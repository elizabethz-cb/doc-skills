#!/usr/bin/env python3
"""Smoke test for the whole pack. Run:  python tests/smoke.py   (needs python-docx)"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILL = ROOT / "skills/drafting-documents/scripts/fill.py"
REDACT = ROOT / "skills/redacting-customer-files/scripts/redact.py"
DOCTYPES = ROOT / "skills/drafting-documents/doctypes"
failures = []


def run(*cmd, env=None):
    return subprocess.run([sys.executable, *map(str, cmd)], capture_output=True, text=True, env=env)


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


# 0. skills follow the authoring rules
r = run(ROOT / "tools/lint_skills.py")
check("skill lint (names, descriptions, size)", r.returncode == 0, r.stdout[-400:])

# 1. every document type is consistent and its example builds
for d in sorted(p for p in DOCTYPES.iterdir() if p.is_dir()):
    r = run(FILL, "check", d)
    check(f"doctype '{d.name}' check", r.returncode == 0, r.stderr.strip())

# 2. the detail guard blocks low-level content in a SOW
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    draft = json.loads((DOCTYPES / "sow/example-draft.json").read_text())
    draft["scope_in"].append("Use 2 x m5.large servers in 10.0.0.0/16.")
    (tmp / "bad.json").write_text(json.dumps(draft))
    r = run(FILL, "build", DOCTYPES / "sow", tmp / "bad.json", tmp / "bad.docx")
    check("SOW detail guard blocks instance types and IPs", r.returncode == 1 and "too much detail" in r.stderr)
    r = run(FILL, "build", DOCTYPES / "sow", tmp / "bad.json", tmp / "ok.docx", "--allow-detail")
    check("--allow-detail lets it through", r.returncode == 0)

# 3. redaction: text file, docx, restore round trip
PLANTED = [
    "Example Corp", "Examplecorp", "Project Lighthouse", "Yoav", "Dana Levi", "Lior Barak",
    "examplecorp.example", "10.40.0.0/16", "10.40.1.11", "203.0.113.25", "111122223333",
    "arn:aws:iam::111122223333", "dana.levi@", "+972-50-555-0142", "AKIAIOSFODNN7EXAMPLE",
    "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "ex-web01", "ex-app02",
]
STAY = ["eu-central-1", "PostgreSQL 14.9", "USD 9,000", "2026-11-20", "2027-01-05"]

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    env = dict(os.environ, DOCS_SKILLS_HOME=str(tmp / "home"))
    src = tmp / "originals"
    src.mkdir()
    original = (ROOT / "examples/original-notes-FICTIONAL.md").read_text()
    (src / "notes.md").write_text(original)

    from docx import Document
    doc = Document()
    doc.core_properties.author = "Dana Levi"
    doc.sections[0].header.paragraphs[0].text = "Example Corp confidential"
    doc.add_paragraph("Servers at 10.40.1.11 belong to Example Corp Ltd.")
    t = doc.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text = "Contact"
    t.rows[0].cells[1].text = "dana.levi@examplecorp.example"
    doc.save(str(src / "plan.docx"))
    (src / "slide.pptx").write_bytes(b"not supported")

    out = tmp / "redacted"
    r = run(REDACT, "run", src, "--engagement", "t", "--names", ROOT / "examples/names.txt", "--out", out, env=env)
    r0 = r
    check("redact skips unsupported file types and says so (exit code 2)", r.returncode == 2 and "slide.pptx" in r.stdout, r.stdout[-300:])
    check("unsupported file is not copied to the output", not (out / "slide.pptx").exists())

    text = (out / "notes.md").read_text()
    leaked = [v for v in PLANTED if v.lower() in text.lower()]
    check("no planted value left in the redacted text file", not leaked, str(leaked))
    check("harmless values stay in the text file", all(v in text for v in STAY), str([v for v in STAY if v not in text]))

    docx_text = "\n".join(p.text for p in Document(str(out / "plan.docx")).paragraphs)
    rd = Document(str(out / "plan.docx"))
    docx_all = docx_text + "\n" + rd.sections[0].header.paragraphs[0].text + "\n" + rd.tables[0].rows[0].cells[1].text
    leaked = [v for v in ("Example Corp", "10.40.1.11", "dana.levi", "examplecorp") if v.lower() in docx_all.lower()]
    check("no planted value left in the docx (body, table, header)", not leaked, str(leaked))
    check("docx author property is cleared", rd.core_properties.author == "")

    r = run(REDACT, "restore", out, "--engagement", "t", "--out", tmp / "restored", env=env)
    restored = (tmp / "restored" / "notes.md").read_text()
    check("restore brings back key values", "111122223333" in restored and "203.0.113.25" in restored and r.returncode == 0)
    import re as _re
    check("restore leaves no placeholder behind", not _re.search(r"\b[A-Z]{3,9}_\d{3}\b", restored), _re.findall(r"\b[A-Z]{3,9}_\d{3}\b", restored)[:5])
    check("restore brings back host names", "ex-app01" in restored and "ex-web01.corp.examplecorp.example" in restored)
    check("review hint lists a place name that was not redacted", "Haifa" in r0.stdout, r0.stdout[-400:])
    mapping = tmp / "home/mappings/t.json"
    check("mapping is stored outside the output folder", mapping.exists() and not list(out.rglob("*.json")))

    # docx with comments must be refused
    import zipfile
    with_comments = src / "commented.docx"
    with zipfile.ZipFile(src / "plan.docx") as zin, zipfile.ZipFile(with_comments, "w") as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("word/comments.xml", "<comments/>")
    out2 = tmp / "redacted2"
    r = run(REDACT, "run", with_comments, "--engagement", "t", "--out", out2, env=env)
    check("docx with comments is refused", r.returncode == 2 and not (out2 / "commented.docx").exists())

# 4. redaction refuses Word files with tracked changes (text the editor cannot reach)
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    env = dict(os.environ, DOCS_SKILLS_HOME=str(tmp / "home"))
    d = Document()
    para = d.add_paragraph("Contact: ")
    ins = OxmlElement("w:ins")
    for k, v in (("w:id", "1"), ("w:author", "x"), ("w:date", "2026-01-01T00:00:00Z")):
        ins.set(qn(k), v)
    xml_run, t = OxmlElement("w:r"), OxmlElement("w:t")
    t.text = "bob@acme.example from 10.1.2.3"
    xml_run.append(t)
    ins.append(xml_run)
    para._p.append(ins)
    d.save(str(tmp / "tracked.docx"))
    r = subprocess.run([sys.executable, str(REDACT), "run", str(tmp / "tracked.docx"), "--engagement", "t", "--out", str(tmp / "out")],
                       capture_output=True, text=True, env=env)
    check("Word file with tracked changes is refused, not passed through",
          r.returncode == 2 and not (tmp / "out" / "tracked.docx").exists(), r.stdout[-300:])

# 5. compare.py shows what changed between a draft and an accepted final
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    from docx import Document
    draft = DOCTYPES / "sow/example-output.docx"
    final = Document(str(draft))
    paras = [p for p in final.paragraphs if p.text.strip()]
    removed_text = paras[3].text
    paras[3]._p.getparent().remove(paras[3]._p)
    paras[5].runs[0].text = "A sentence that people wrote in the final version."
    for r_ in paras[5].runs[1:]:
        r_.text = ""
    final.save(str(tmp / "final.docx"))
    cmp_script = ROOT / "skills/learning-from-accepted-documents/scripts/compare.py"
    r = run(cmp_script, draft, tmp / "final.docx")
    check("compare shows the removed and the new text",
          r.returncode == 0 and removed_text[:30] in r.stdout and "A sentence that people wrote" in r.stdout, r.stdout[-300:])

# 6. lessons must not contain customer-looking values (they are shared with colleagues)
import importlib.util
import re as _re2
spec = importlib.util.spec_from_file_location("redact", REDACT)
redact_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(redact_mod)
for lessons in sorted(ROOT.glob("skills/**/lessons.md")):
    text = lessons.read_text(encoding="utf-8")
    found = [v for _, _, _, v in redact_mod.find_spans(text, [])] + _re2.findall(r"\b[A-Z]{3,9}_\d{3}\b", text)
    check(f"{lessons.relative_to(ROOT)} has no customer-looking values", not found, str(found))
with tempfile.TemporaryDirectory() as tmp:
    bad = Path(tmp) / "lessons.md"
    bad.write_text("- 2026-11-03: Dana at dana@acme.example said CUSTOMER_001 uses 10.1.2.3\n")
    leaked = [v for _, _, _, v in redact_mod.find_spans(bad.read_text(), [])]
    check("the lessons check catches an email and an IP address", len(leaked) >= 2, str(leaked))

# 7. diagrams: structure of the .drawio file, layout sanity, and the summary-level guard
DIAGRAM = ROOT / "skills/drawing-diagrams/scripts/diagram.py"
EXAMPLE_SPEC = ROOT / "skills/drawing-diagrams/example-spec.json"
import xml.etree.ElementTree as ET


def drawio_problems(path):
    """Return structural problems in a .drawio file."""
    problems = []
    root = ET.parse(path).getroot()
    cells = {c.get("id"): c for c in root.iter("mxCell")}
    ids = [c.get("id") for c in root.iter("mxCell")]
    if len(ids) != len(set(ids)):
        problems.append("duplicate cell ids")
    geo = {}
    for cid, c in cells.items():
        if c.get("vertex") == "1":
            g = c.find("mxGeometry")
            geo[cid] = (float(g.get("x")), float(g.get("y")), float(g.get("width")), float(g.get("height")), c.get("parent"))
        if c.get("edge") == "1":
            for end in ("source", "target"):
                if c.get(end) not in cells:
                    problems.append(f"edge {cid} points at a missing cell")
        parent = c.get("parent")
        if parent is not None and parent not in cells:
            problems.append(f"{cid} has a missing parent")
    for cid, (x, y, w, h, parent) in geo.items():
        if parent in geo:
            px, py, pw, ph, _ = geo[parent]
            if x < 0 or y < 0 or x + w > pw or y + h > ph:
                problems.append(f"{cid} sticks out of its group")
    by_parent = {}
    for cid, g in geo.items():
        by_parent.setdefault(g[4], []).append((cid, g))
    for siblings in by_parent.values():
        for i in range(len(siblings)):
            for j in range(i + 1, len(siblings)):
                (a, (ax, ay, aw, ah, _)), (b, (bx, by, bw, bh, _)) = siblings[i], siblings[j]
                if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                    problems.append(f"{a} and {b} overlap")
    return problems


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    r = run(DIAGRAM, "build", EXAMPLE_SPEC, tmp / "ex.drawio", "--png", tmp / "ex.png")
    check("diagram example builds", r.returncode == 0, r.stderr.strip())
    check("diagram file is valid, with no broken links, escapes or overlaps", not drawio_problems(tmp / "ex.drawio"), str(drawio_problems(tmp / "ex.drawio")))
    check("diagram preview image is written", (tmp / "ex.png").exists() and (tmp / "ex.png").stat().st_size > 1000)
    committed = ROOT / "skills/drawing-diagrams/example.drawio"
    check("committed example.drawio is up to date", committed.read_text() == (tmp / "ex.drawio").read_text())

    spec = json.loads(EXAMPLE_SPEC.read_text())

    def with_changes(**changes):
        d = json.loads(json.dumps(spec))
        for k, v in changes.items():
            d[k] = v
        path = tmp / "variant.json"
        path.write_text(json.dumps(d))
        return path

    bad = json.loads(json.dumps(spec))
    bad["nodes"][2]["label"] = "2 x m5.large web servers"
    bad["groups"][1]["label"] = "VPC 10.0.0.0/16 private subnet"
    (tmp / "bad.json").write_text(json.dumps(bad))
    r = run(DIAGRAM, "build", tmp / "bad.json", tmp / "bad.drawio")
    check("summary level blocks instance types, IP ranges and subnets",
          r.returncode == 1 and r.stderr.count("too much detail") >= 3 and not (tmp / "bad.drawio").exists(), r.stderr[-300:])
    r = run(DIAGRAM, "build", tmp / "bad.json", tmp / "bad2.drawio", "--allow-detail")
    check("--allow-detail lets detailed labels through", r.returncode == 0)
    d = json.loads(json.dumps(spec)); d["level"] = "detailed"; d["nodes"][2]["label"] = "2 x m5.large web servers"
    (tmp / "detailed.json").write_text(json.dumps(d))
    check("detailed level allows detail", run(DIAGRAM, "check", tmp / "detailed.json").returncode == 0)

    many = json.loads(json.dumps(spec))
    many["nodes"] += [{"id": f"x{i}", "label": f"Part {i}"} for i in range(10)]
    (tmp / "many.json").write_text(json.dumps(many))
    r = run(DIAGRAM, "check", tmp / "many.json")
    check("summary level rejects an overcrowded diagram", r.returncode == 1 and "nodes" in r.stderr)

    broken = json.loads(json.dumps(spec))
    broken["nodes"][0]["group"] = "nope"
    broken["edges"].append({"from": "web", "to": "ghost"})
    broken["nodes"].append({"id": "web", "label": "Duplicate"})
    (tmp / "broken.json").write_text(json.dumps(broken))
    r = run(DIAGRAM, "check", tmp / "broken.json")
    check("unknown group, missing edge target and duplicate id are all reported",
          r.returncode == 1 and "nope" in r.stderr and "ghost" in r.stderr and "used twice" in r.stderr, r.stderr)

    tb = json.loads(json.dumps(spec)); tb["direction"] = "TB"
    (tmp / "tb.json").write_text(json.dumps(tb))
    r = run(DIAGRAM, "build", tmp / "tb.json", tmp / "tb.drawio")
    check("top-to-bottom layout is valid too", r.returncode == 0 and not drawio_problems(tmp / "tb.drawio"), str(drawio_problems(tmp / "tb.drawio")) if r.returncode == 0 else r.stderr)

    ic = json.loads(json.dumps(spec)); ic["nodes"][2]["icon"] = "mxgraph.aws4.ec2"; ic["nodes"][3]["label"] = "R&D <app> \"tier\""
    (tmp / "icon.json").write_text(json.dumps(ic))
    r = run(DIAGRAM, "build", tmp / "icon.json", tmp / "icon.drawio")
    check("icons pass through and special characters are escaped",
          r.returncode == 0 and "resIcon=mxgraph.aws4.ec2" in (tmp / "icon.drawio").read_text() and not drawio_problems(tmp / "icon.drawio"), r.stderr)

# 5. engagement workflows (the lint in check 0 already covers their names and descriptions)
import re

skill_names = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
readme = (ROOT / "README.md").read_text(encoding="utf-8")
for w in ("draft", "update", "learn"):
    f = ROOT / "skills" / w / "SKILL.md"
    check(f"workflow '{w}' exists", f.exists())
    if not f.exists():
        continue
    text = f.read_text(encoding="utf-8")
    named = set(re.findall(r"`([a-z-]+)` skill", text))
    check(f"workflow '{w}' names only skills that exist", bool(named) and named <= skill_names, str(named - skill_names))
    check(f"workflow '{w}' reads the shared folder rules and runs only when invoked",
          "shared/folder-rules.md" in text and "disable-model-invocation: true" in text)
    check(f"README documents /docs-skills:{w}", f"/docs-skills:{w}" in readme)
for w in ("apply-lessons", "add-doctype", "update-template"):
    f = ROOT / "skills" / w / "SKILL.md"
    check(f"workflow '{w}' exists, runs only when invoked and documents itself in the README",
          f.exists() and "disable-model-invocation: true" in f.read_text(encoding="utf-8") and f"/docs-skills:{w}" in readme)
rule_lines = ["Never edit, move, rename or delete anything in input/", "Write only inside output/", "Do not send, upload or share anything"]
texts = {p: p.read_text(encoding="utf-8", errors="ignore") for p in ROOT.rglob("*.md") if ".git" not in p.parts}
for line in rule_lines:
    where = [p.name for p, t in texts.items() if line in t]
    check(f"folder rule '{line[:30]}...' is written in exactly one file", where == ["folder-rules.md"], str(where))

print()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("All checks passed")
