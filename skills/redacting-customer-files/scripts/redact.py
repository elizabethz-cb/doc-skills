#!/usr/bin/env python3
"""Replace sensitive values in customer files with consistent placeholders.

RUN THIS YOURSELF in a terminal. Do not let an AI tool run it on original files.

  python redact.py run <file-or-folder> --engagement acme --names names.txt --out redacted/
  python redact.py restore <file-or-folder> --engagement acme --out restored/

names.txt (one group per line, aliases share one placeholder, a trailing * means "every word starting with this"):
  customer: Example Corp Ltd | Example Corp | Example
  person: Dana Levi | Dana
  project: Project Lighthouse
  term: ex-*          (every word starting with ex-, each gets its own placeholder)

Handles text files (.txt .md .csv .eml .json .yaml .yml .log .tsv) and .docx.
Anything else is skipped and listed (it fails closed). A .docx is re-scanned after redaction,
including tracked changes, text boxes, footnotes and file properties, and is refused if anything
sensitive-looking is left. Needs python-docx for .docx.
The mapping that allows restoring real values is stored OUTSIDE the project, in
~/.docs-skills/mappings/<engagement>.json (set DOCS_SKILLS_HOME to change the folder).
"""
import argparse
import html
import json
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

TEXT_EXT = {".txt", ".md", ".csv", ".eml", ".json", ".yaml", ".yml", ".log", ".tsv"}
SKIP_TLDS = {"md", "txt", "csv", "json", "yaml", "yml", "docx", "xlsx", "pptx", "pdf", "py", "js",
             "ts", "png", "jpg", "jpeg", "gif", "svg", "html", "htm", "log", "zip", "sh", "eml", "tsv",
             "dotm", "dotx", "docm", "xlsm", "xltx", "pptm", "potx", "xml", "rels", "bin", "emf", "wmf",
             "tiff", "bmp", "ini", "cfg", "css"}
KINDS = {"customer": "CUSTOMER", "person": "PERSON", "project": "PROJECT", "term": "TERM"}


# ---------- mapping (kept outside the project) ----------

class Mapping:
    def __init__(self, engagement: str):
        base = Path(os.environ.get("DOCS_SKILLS_HOME", Path.home() / ".docs-skills"))
        self.path = base / "mappings" / f"{engagement}.json"
        self.data = {"tokens": {}, "originals": {}, "counters": {}}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def token(self, label: str, original: str) -> str:
        key = f"{label}|{original.lower()}"
        tokens = self.data["tokens"]
        if key not in tokens:
            n = self.data["counters"].get(label, 0) + 1
            self.data["counters"][label] = n
            tokens[key] = f"{label}_{n:03d}"
            self.data["originals"][tokens[key]] = original
        return tokens[key]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass


# ---------- detectors ----------

def valid_ip(text):
    parts = text.split(".")
    return len(parts) == 4 and all(p.isdigit() and int(p) <= 255 for p in parts)


DETECTORS = [
    # (label, regex, group, validator)
    ("SECRET", re.compile(r"(?i)aws_secret_access_key\s*[=:]\s*([A-Za-z0-9/+=]{40})"), 1, None),
    ("KEY", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), 0, None),
    ("ARN", re.compile(r"arn:aws[a-z-]*:[a-z0-9-]*:[a-z0-9-]*:\d{0,12}:[^\s\"'<>,;)]+"), 0, None),
    ("ACCOUNT", re.compile(r"(?<!\d)\d{12}(?!\d)"), 0, None),
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), 0, None),
    ("CIDR", re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}(?!\d)"), 0,
     lambda t: valid_ip(t.split("/")[0]) and int(t.split("/")[1]) <= 32),
    ("IP", re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.]*\d)"), 0, valid_ip),
    ("PHONE", re.compile(r"(?<![\w+])\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,4}){2,4}"), 0,
     lambda t: 8 <= sum(c.isdigit() for c in t) <= 15),
    ("DOMAIN", re.compile(
        r"(?<![\w@.-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}(?![\w-])"), 0,
     lambda t: t.rsplit(".", 1)[1].lower() not in SKIP_TLDS),
]


def load_names(path):
    patterns = []  # (label, canonical, regex)
    if not path:
        return patterns
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        kind, rest = line.split(":", 1)
        label = KINDS.get(kind.strip().lower())
        if not label:
            sys.exit(f"names.txt: unknown type '{kind.strip()}'. Use one of {sorted(KINDS)}")
        aliases = [a.strip() for a in rest.split("|") if a.strip()]
        if not aliases:
            continue
        canonical = aliases[0].rstrip("*")
        for alias in aliases:
            prefix = alias.endswith("*")
            body = re.escape(alias.rstrip("*"))
            if prefix:  # the whole word that starts with this text, e.g. ex-* matches ex-app01
                rx = re.compile(r"(?<!\w)" + body + r"[\w-]*", re.IGNORECASE)
            else:
                rx = re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)
            patterns.append((label, None if prefix else canonical, rx))
    return patterns


def find_spans(text, names):
    spans = []
    for label, rx, group, check in DETECTORS:
        for m in rx.finditer(text):
            s, e = m.span(group)
            if check is None or check(text[s:e]):
                spans.append((s, e, label, text[s:e]))
    for label, canonical, rx in names:
        for m in rx.finditer(text):
            spans.append((m.start(), m.end(), label, canonical or m.group(0)))
    spans.sort(key=lambda t: (-(t[1] - t[0]), t[0]))
    chosen, taken = [], []
    for s, e, label, value in spans:
        if all(e <= ts or s >= te for ts, te in taken):
            taken.append((s, e))
            chosen.append((s, e, label, value))
    return sorted(chosen)


def redact_text(text, names, mapping, counts):
    out, last = [], 0
    for s, e, label, value in find_spans(text, names):
        out.append(text[last:s])
        out.append(mapping.token(label, value))
        counts[label] += 1
        last = e
    out.append(text[last:])
    return "".join(out)


# ---------- docx ----------

def docx_paragraphs(container, seen):
    for p in container.paragraphs:
        if p._p not in seen:
            seen.add(p._p)
            yield p
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from docx_paragraphs(cell, seen)


def docx_all(doc):
    seen = set()
    parts = [doc]
    for s in doc.sections:
        for part in (s.header, s.footer, s.first_page_header, s.first_page_footer,
                     s.even_page_header, s.even_page_footer):
            if not part.is_linked_to_previous:
                parts.append(part)
    for part in parts:
        yield from docx_paragraphs(part, seen)


def rewrite_paragraph(p, new_text):
    if p.runs:
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(new_text)


def docx_problem(path, allow_images):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
    if "word/comments.xml" in names:
        return "contains Word comments, which are not redacted. Remove the comments first."
    if any(n.startswith("word/media/") for n in names) and not allow_images:
        return "contains images, which are not checked. Remove them, or use --allow-images."
    return None


def docx_texts(path):
    """Text of every part of a Word file, including parts the editor above does not touch
    (tracked changes, text boxes, footnotes, file properties)."""
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml = z.read(name).decode("utf-8", "ignore")
                for para in xml.split("</w:p>"):
                    chunks = re.findall(r"<w:(?:t|delText)(?: [^>]*)?>(.*?)</w:(?:t|delText)>", para, re.S)
                    if chunks:
                        yield name, html.unescape("".join(chunks))
            elif name in ("docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"):
                xml = z.read(name).decode("utf-8", "ignore")
                yield name, html.unescape(re.sub(r"<[^>]+>", " ", xml))


def verify_docx(path, names):
    """Return the parts of a finished Word file that still hold sensitive-looking text."""
    bad = set()
    for part, text in docx_texts(path):
        if find_spans(text, names):
            bad.add(part)
    return sorted(bad)


def process_docx(src, dst, transform):
    from docx import Document
    doc = Document(str(src))
    for p in docx_all(doc):
        if p.text:
            new = transform(p.text)
            if new != p.text:
                rewrite_paragraph(p, new)
    props = doc.core_properties
    for attr in ("author", "last_modified_by", "title", "subject", "comments", "keywords"):
        setattr(props, attr, "")
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dst))


# ---------- commands ----------

def files_in(target: Path):
    if target.is_file():
        return [(target, Path(target.name))]
    return [(p, p.relative_to(target)) for p in sorted(target.rglob("*")) if p.is_file()]


def cmd_run(args) -> int:
    names = load_names(args.names)
    mapping = Mapping(args.engagement)
    out_root = Path(args.out)
    counts, done, skipped = Counter(), [], []
    leftover = Counter()
    for src, rel in files_in(Path(args.input)):
        ext = src.suffix.lower()
        dst = out_root / rel
        try:
            if ext in TEXT_EXT:
                text = src.read_text(encoding="utf-8")
                new = redact_text(text, names, mapping, counts)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(new, encoding="utf-8")
                collect_candidates(new, leftover)
            elif ext == ".docx":
                problem = docx_problem(src, args.allow_images)
                if problem:
                    skipped.append((str(rel), problem))
                    continue
                texts = []

                def transform(t, texts=texts):
                    new = redact_text(t, names, mapping, counts)
                    texts.append(new)
                    return new

                process_docx(src, dst, transform)
                leaks = verify_docx(dst, names)
                if leaks:
                    dst.unlink()
                    skipped.append((str(rel), "still holds sensitive-looking text in " + ", ".join(leaks)
                                    + " (tracked changes, text boxes, footnotes or file properties). "
                                    "Accept all changes, remove text boxes and footnotes, or redact it by hand."))
                    continue
                collect_candidates("\n".join(texts), leftover)
            else:
                skipped.append((str(rel), f"file type '{ext or 'none'}' is not supported"))
                continue
            done.append(str(rel))
        except (UnicodeDecodeError, OSError, zipfile.BadZipFile) as exc:
            skipped.append((str(rel), f"could not be processed ({exc.__class__.__name__})"))
    mapping.save()
    write_report(out_root, done, skipped, counts)
    print(f"Redacted {len(done)} file(s) into {out_root}")
    for label, n in sorted(counts.items()):
        print(f"  {label:<9} {n}")
    for name, why in skipped:
        print(f"SKIPPED {name}: {why}")
    top = [(w, n) for w, n in leftover.most_common(15)]
    if top:
        print("\nCapitalised words still in the text. Check for names, places or products, add them to names.txt and run again:")
        for w, n in top:
            print(f"  {w}  (x{n})")
    print(f"\nMapping saved outside the project: {mapping.path}")
    print("Read the redacted files yourself before sharing them with any AI tool.")
    return 2 if skipped else 0


def collect_candidates(text, counter):
    # multi-word capitalised phrases, and single capitalised words in the middle of a sentence
    for m in re.finditer(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+\b", text):
        counter[m.group(0)] += 1
    for m in re.finditer(r"(?<=[a-z,;] )[A-Z][a-z]{3,}\b", text):
        counter[m.group(0)] += 1


def write_report(out_root, done, skipped, counts):
    out_root.mkdir(parents=True, exist_ok=True)
    lines = ["REDACTION REPORT (counts only, no original values)", ""]
    lines += [f"{label}: {n}" for label, n in sorted(counts.items())]
    lines += ["", "Files redacted:"] + [f"  {d}" for d in done]
    lines += ["", "Files skipped:"] + [f"  {n}: {w}" for n, w in skipped]
    (out_root / "REDACTION-REPORT.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_restore(args) -> int:
    mapping = Mapping(args.engagement)
    originals = mapping.data["originals"]
    if not originals:
        print(f"No mapping found at {mapping.path}", file=sys.stderr)
        return 1
    tokens = sorted(originals, key=len, reverse=True)
    rx = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(map(re.escape, tokens)) + r")(?![A-Za-z0-9_])")
    restore = lambda t: rx.sub(lambda m: originals[m.group(0)], t)
    out_root = Path(args.out)
    n = 0
    for src, rel in files_in(Path(args.input)):
        dst = out_root / rel
        ext = src.suffix.lower()
        if ext in TEXT_EXT:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(restore(src.read_text(encoding="utf-8")), encoding="utf-8")
        elif ext == ".docx":
            process_docx(src, dst, restore)
        else:
            print(f"SKIPPED {rel}: file type not supported")
            continue
        n += 1
    print(f"Restored {n} file(s) into {out_root}. These contain real values: keep them out of AI tools.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="redact a file or folder")
    r.add_argument("input")
    r.add_argument("--engagement", required=True)
    r.add_argument("--names")
    r.add_argument("--out", required=True)
    r.add_argument("--allow-images", action="store_true")
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("restore", help="put the real values back into a finished document")
    s.add_argument("input")
    s.add_argument("--engagement", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_restore)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
