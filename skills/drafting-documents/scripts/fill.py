#!/usr/bin/env python3
"""Fill a Word template from a draft.json, and check a document type folder.

  python fill.py build <doctype-dir> <draft.json> <out.docx> [--allow-detail]
  python fill.py check <doctype-dir>

Placeholders in template.docx:
  {{name}}            a text field
  {{list:name}}       a paragraph that is repeated once per item of a list field
  {{table.column}}    cells of ONE template row, repeated once per row of a table field
Needs only python-docx.
"""
import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

try:
    from docx import Document
    from docx.text.paragraph import Paragraph
except ImportError:
    sys.exit("python-docx is missing. Run: pip install python-docx")

PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
LIST_MARK = re.compile(r"^\s*\{\{\s*list:([a-z][a-z0-9_]*)\s*\}\}\s*$")
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
TYPES = {"text", "list", "table"}


# ---------- document type definition ----------

def load_definition(doctype_dir: Path):
    path = doctype_dir / "fields.json"
    if not path.exists():
        return None, [f"{path} not found"]
    try:
        defn = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"fields.json is not valid JSON: {exc}"]
    return defn, check_definition(defn)


def check_definition(defn: dict) -> list:
    problems = []
    fields = defn.get("fields")
    if not isinstance(fields, dict) or not fields:
        return ["fields.json needs a non-empty 'fields' object"]
    for name, spec in fields.items():
        if not NAME.match(name):
            problems.append(f"field name '{name}' must be lowercase letters, digits and underscores")
        if not isinstance(spec, dict) or spec.get("type") not in TYPES:
            problems.append(f"field '{name}': type must be one of {sorted(TYPES)}")
            continue
        if spec["type"] == "table":
            cols = spec.get("columns")
            if not cols or not all(isinstance(c, str) and NAME.match(c) for c in cols):
                problems.append(f"field '{name}': table needs 'columns' (lowercase names)")
    for item in defn.get("forbidden_patterns", []):
        try:
            re.compile(item["regex"])
        except (KeyError, re.error, TypeError) as exc:
            problems.append(f"forbidden_patterns entry {item!r} is not valid: {exc}")
    return problems


# ---------- draft validation ----------

def check_draft(defn: dict, draft: dict, allow_detail: bool) -> list:
    problems = []
    fields = defn["fields"]
    for key in draft:
        if key not in fields:
            problems.append(f"draft has a field the document type does not know: '{key}'")
    for name, spec in fields.items():
        if name not in draft:
            if spec.get("required", True):
                problems.append(f"missing field: '{name}'")
            continue
        value, kind = draft[name], spec["type"]
        if kind == "text":
            if not isinstance(value, str):
                problems.append(f"'{name}' must be text")
            elif spec.get("required", True) and not value.strip():
                problems.append(f"'{name}' is empty")
        elif kind == "list":
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                problems.append(f"'{name}' must be a list of text items")
        elif kind == "table":
            cols = spec["columns"]
            if not isinstance(value, list):
                problems.append(f"'{name}' must be a list of rows")
                continue
            for i, row in enumerate(value, 1):
                if not isinstance(row, dict) or sorted(row) != sorted(cols):
                    problems.append(f"'{name}' row {i} must have exactly these columns: {cols}")
                elif not all(isinstance(v, str) for v in row.values()):
                    problems.append(f"'{name}' row {i}: every value must be text")
    if not allow_detail:
        problems += detail_problems(defn, draft)
    return problems


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from strings_in(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings_in(v)


def detail_problems(defn: dict, draft: dict) -> list:
    problems = []
    for item in defn.get("forbidden_patterns", []):
        rx = re.compile(item["regex"], re.IGNORECASE)
        for name, value in draft.items():
            for text in strings_in(value):
                m = rx.search(text)
                if m:
                    problems.append(
                        f"too much detail in '{name}': {item['name']} found ('{m.group(0)}'). "
                        f"Rewrite at business level, or use --allow-detail if this is intended."
                    )
    return problems


# ---------- reading and editing the Word file ----------

def containers(doc):
    yield doc
    for section in doc.sections:
        for part in (section.header, section.footer, section.first_page_header,
                     section.first_page_footer, section.even_page_header, section.even_page_footer):
            if not part.is_linked_to_previous:
                yield part


def all_paragraphs(container, seen=None):
    seen = set() if seen is None else seen
    for p in container.paragraphs:
        if p._p not in seen:
            seen.add(p._p)
            yield p
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from all_paragraphs(cell, seen)


def document_paragraphs(doc):
    seen = set()
    for c in containers(doc):
        yield from all_paragraphs(c, seen)


def replace_in_paragraph(p, resolver):
    """Replace {{...}} using resolver(name) -> str or None (None keeps the placeholder)."""
    if "{{" not in p.text:
        return

    def sub(m):
        value = resolver(m.group(1))
        return m.group(0) if value is None else value

    expected = PLACEHOLDER.sub(sub, p.text)
    for run in p.runs:
        if "{{" in run.text:
            run.text = PLACEHOLDER.sub(sub, run.text)
    if p.text != expected and p.runs:
        # a placeholder was split over several runs: keep the text, lose inline formatting
        p.runs[0].text = expected
        for run in p.runs[1:]:
            run.text = ""


def set_text(p, text):
    if p.runs:
        p.runs[0].text = text
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.add_run(text)


def template_placeholders(doc):
    found = set()
    for p in document_paragraphs(doc):
        for m in PLACEHOLDER.finditer(p.text):
            found.add(m.group(1).strip())
    return found


def classify(name, fields):
    """Return (field, kind, column) for a placeholder name, or None if it does not fit."""
    if name.startswith("list:"):
        f = name[5:]
        return (f, "list", None) if fields.get(f, {}).get("type") == "list" else None
    if "." in name:
        f, col = name.split(".", 1)
        spec = fields.get(f, {})
        return (f, "table", col) if spec.get("type") == "table" and col in spec["columns"] else None
    return (name, "text", None) if fields.get(name, {}).get("type") == "text" else None


def fill_tables(doc, fields, draft):
    for table in doc.tables:
        for row in list(table.rows):
            text = " ".join(c.text for c in row.cells)
            names = {classify(m.group(1).strip(), fields) for m in PLACEHOLDER.finditer(text)}
            tables = {n[0] for n in names if n and n[1] == "table"}
            if not tables:
                continue
            field = tables.pop()
            items = draft.get(field, [])

            def make_resolver(item):
                def resolver(name):
                    c = classify(name, fields)
                    if c and c[0] == field and c[1] == "table":
                        return item[c[2]] if item else "-"
                    return None
                return resolver

            for item in (items or [None]):
                new_tr = copy.deepcopy(row._tr)
                row._tr.addprevious(new_tr)
                from docx.table import _Row
                new_row = _Row(new_tr, table)
                for cell in new_row.cells:
                    for p in cell.paragraphs:
                        replace_in_paragraph(p, make_resolver(item))
            row._tr.getparent().remove(row._tr)


def fill_lists(doc, draft):
    for p in list(all_paragraphs(doc)):
        m = LIST_MARK.match(p.text)
        if not m:
            continue
        items = draft.get(m.group(1), []) or ["-"]
        for item in items:
            new_p = copy.deepcopy(p._p)
            p._p.addprevious(new_p)
            set_text(Paragraph(new_p, p._parent), item)
        p._p.getparent().remove(p._p)


def build_document(doctype_dir: Path, defn: dict, draft: dict, out: Path) -> list:
    template = doctype_dir / "template.docx"
    if not template.exists():
        return [f"{template} not found"]
    doc = Document(str(template))
    fields = defn["fields"]
    fill_tables(doc, fields, draft)
    fill_lists(doc, draft)

    def resolver(name):
        c = classify(name.strip(), fields)
        return draft.get(c[0], "") if c and c[1] == "text" else None

    for p in document_paragraphs(doc):
        replace_in_paragraph(p, resolver)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    left = [p.text.strip() for p in document_paragraphs(Document(str(out))) if "{{" in p.text or "}}" in p.text]
    return [f"leftover placeholder in the Word file: {t[:80]}" for t in left]


# ---------- commands ----------

def cmd_build(args) -> int:
    doctype_dir = Path(args.doctype)
    defn, problems = load_definition(doctype_dir)
    if problems:
        return report("The document type has problems", problems)
    try:
        draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return report("Cannot read the draft", [str(exc)])
    problems = check_draft(defn, draft, args.allow_detail)
    if problems:
        return report("The draft needs fixing before it can be filled in", problems)
    problems = build_document(doctype_dir, defn, draft, Path(args.out))
    if problems:
        return report("The Word file was written but has problems", problems)
    print(f"OK: wrote {args.out}")
    questions = draft.get("open_questions")
    if questions:
        print(f"\nOpen questions ({len(questions)}):")
        for q in questions:
            print(f"  {q.get('id', '?'):<4} {q.get('impact', ''):<9} {q.get('question', '')}")
    return 0


def cmd_check(args) -> int:
    doctype_dir = Path(args.doctype)
    defn, problems = load_definition(doctype_dir)
    if defn is None or problems:
        return report("Document type check failed", problems)
    fields = defn["fields"]
    if defn.get("name") != doctype_dir.name:
        problems.append(f"fields.json says name '{defn.get('name')}' but the folder is called '{doctype_dir.name}'. Make them the same.")
    template = doctype_dir / "template.docx"
    if not template.exists():
        return report("Document type check failed", [f"{template} not found"])
    used_fields = set()
    for name in sorted(template_placeholders(Document(str(template)))):
        c = classify(name, fields)
        if c is None:
            problems.append(f"template placeholder '{{{{{name}}}}}' does not match any field in fields.json")
        else:
            used_fields.add(c[0])
    for name in fields:
        if name not in used_fields:
            problems.append(f"field '{name}' is in fields.json but not used in template.docx")
    for needed in ("rules.md", "example-draft.json"):
        if not (doctype_dir / needed).exists():
            problems.append(f"{needed} is missing")
    example = doctype_dir / "example-draft.json"
    if example.exists() and not problems:
        draft = json.loads(example.read_text(encoding="utf-8"))
        problems += check_draft(defn, draft, allow_detail=False)
        if not problems:
            with tempfile.TemporaryDirectory() as tmp:
                problems += build_document(doctype_dir, defn, draft, Path(tmp) / "example.docx")
    if problems:
        return report("Document type check failed", problems)
    print(f"OK: '{defn.get('name', doctype_dir.name)}' is consistent "
          f"({len(fields)} fields, template, example and rules all match).")
    return 0


def report(title, problems) -> int:
    print(f"{title}:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="fill the template from a draft.json")
    b.add_argument("doctype")
    b.add_argument("draft")
    b.add_argument("out")
    b.add_argument("--allow-detail", action="store_true", help="skip the too-much-detail check")
    b.set_defaults(func=cmd_build)
    c = sub.add_parser("check", help="check that a document type folder is consistent")
    c.add_argument("doctype")
    c.set_defaults(func=cmd_check)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
