#!/usr/bin/env python3
"""Check every skill against the authoring rules. Run:  python tools/lint_skills.py

Rules (from Anthropic's skill authoring guidance):
  - SKILL.md exists, with a name and a description in the frontmatter
  - name: lowercase letters, digits and hyphens, at most 64 characters, same as the folder name
  - description: at most 1024 characters, says what the skill does AND when to use it ("Use when"),
    written in the third person
  - SKILL.md body under 500 lines (put detail in other files and point to them)
Warnings (do not fail): descriptions that overlap, long descriptions, long lessons.md files.
Token numbers are rough estimates (about 4 characters per token).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
problems = []


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
if not skills:
    problems.append("no skills found")
for folder in skills:
    skill_md = folder / "SKILL.md"
    if not skill_md.exists():
        problems.append(f"{folder.name}: SKILL.md is missing (the file name must be exactly SKILL.md)")
        continue
    text = skill_md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None or "name" not in fm or "description" not in fm:
        problems.append(f"{folder.name}: frontmatter needs both 'name' and 'description'")
        continue
    name, desc = fm["name"], fm["description"]
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        problems.append(f"{folder.name}: name '{name}' must be lowercase letters, digits and hyphens, max 64 characters")
    if name != folder.name:
        problems.append(f"{folder.name}: name '{name}' must be the same as the folder name (chat upload fails otherwise)")
    if len(desc) > 1024:
        problems.append(f"{folder.name}: description is {len(desc)} characters, the limit is 1024")
    if "use when" not in desc.lower():
        problems.append(f"{folder.name}: description should say when to use the skill ('Use when ...')")
    if re.match(r"(?i)^(i |you |use |draft |prepare |help )", desc):
        problems.append(f"{folder.name}: write the description in the third person ('Drafts ...', not 'Draft ...')")
    lines = text.count("\n") + 1
    if lines > 500:
        problems.append(f"{folder.name}: SKILL.md has {lines} lines, keep it under 500 and move detail to other files")
    print(f"{folder.name}: description {len(desc)} chars, SKILL.md {lines} lines")

# ---- warnings and the token picture ----
STOP = set("the and for with that from this when user users file files use used using their them then are not any all its into over about also can has have will been being such these those only".split())
words = {}
for folder in skills:
    fm = frontmatter((folder / "SKILL.md").read_text(encoding="utf-8")) or {}
    words[folder.name] = {w for w in re.findall(r"[a-z]{4,}", fm.get("description", "").lower()) if w not in STOP}
names = list(words)
warnings = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = words[names[i]], words[names[j]]
        score = len(a & b) / max(1, len(a | b))
        if score > 0.30:
            warnings.append(f"descriptions of {names[i]} and {names[j]} overlap ({score:.0%}); they may fire together. Narrow them.")
tokens = lambda t: round(len(t) / 4)
always = 0
for folder in skills:
    fm = re.match(r"^---\n(.*?)\n---\n", (folder / "SKILL.md").read_text(encoding="utf-8"), re.S)
    if fm:
        if "disable-model-invocation: true" not in fm.group(1):  # loads only when invoked by name
            always += tokens(fm.group(1))
        if len(fm.group(1)) > 600:
            warnings.append(f"{folder.name}: name and description are about {tokens(fm.group(1))} tokens and load every session. Shorten them.")
for lessons in (ROOT / "skills").rglob("lessons.md"):
    n = lessons.read_text(encoding="utf-8").count("\n")
    if n > 40:
        warnings.append(f"{lessons.relative_to(ROOT)} has {n} lines and is read on every run. Merge repeats into rules.md and delete old lessons.")
print(f"\nAlways loaded (names and descriptions of all skills): about {always} tokens")
for folder in skills:
    base = folder / "doctypes"
    if not base.is_dir():
        continue
    shared = [folder / "SKILL.md"] + sorted((folder / "shared").glob("*.md"))
    for dt in sorted(p for p in base.iterdir() if p.is_dir()):
        read = shared + [dt / n for n in ("rules.md", "lessons.md", "fields.json", "example-draft.json") if (dt / n).exists()]
        total = sum(tokens(f.read_text(encoding="utf-8")) for f in read)
        print(f"{folder.name} / {dt.name}: one run reads about {total} tokens")
        if total > 8000:
            warnings.append(f"a {dt.name} run reads about {total} tokens. Trim rules, examples or lessons.")
for w in warnings:
    print(f"Warning: {w}")

if problems:
    print("\nProblems:")
    for p in problems:
        print(f"  - {p}")
    sys.exit(1)
print("Skill lint: OK")
