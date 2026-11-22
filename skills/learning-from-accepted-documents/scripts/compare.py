#!/usr/bin/env python3
"""Show what changed between a drafted and an accepted Word or PowerPoint file.

  python compare.py <draft.docx|pptx> <final.docx|pptx> [--max 60]

Prints removed, added and reworded paragraphs and table rows in document order (slide text for a deck).
Needs python-docx for .docx and python-pptx for .pptx.
"""
import argparse
import difflib
import re
import sys
import zipfile



def pptx_lines(path):
    try:
        from pptx import Presentation
    except ImportError:
        sys.exit("python-pptx is missing. Run: pip install python-pptx")
    out = []
    for slide in Presentation(path).slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                out += [p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip()]
            elif shape.has_table:
                out += [" | ".join(c.text.strip() for c in row.cells) for row in shape.table.rows]
    return out


def lines_of(path):
    if str(path).lower().endswith(".pptx"):
        return pptx_lines(path)
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        sys.exit("python-docx is missing. Run: pip install python-docx")
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    if re.search(r"<w:(ins|del) ", xml):
        sys.exit(f"{path} contains tracked changes. Accept all changes first.")
    doc = Document(path)
    out = []
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            text = Paragraph(child, doc).text.strip()
            if text:
                out.append(text)
        elif child.tag.endswith("}tbl"):
            for row in Table(child, doc).rows:
                cells = []
                for cell in row.cells:
                    if cell.text.strip() not in cells:
                        cells.append(cell.text.strip())
                out.append(" | ".join(cells))
    return out


def short(text, n=300):
    return text if len(text) <= n else text[:n] + " ..."


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("final")
    ap.add_argument("--max", type=int, default=60, help="maximum number of changes to print")
    args = ap.parse_args()
    a, b = lines_of(args.draft), lines_of(args.final)
    same = 0
    shown = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            same += i2 - i1
            continue
        if shown >= args.max:
            continue
        shown += 1
        print(f"--- change {shown} ({'reworded' if tag == 'replace' else 'removed' if tag == 'delete' else 'added'})")
        for line in a[i1:i2]:
            print(f"  DRAFT : {short(line)}")
        for line in b[j1:j2]:
            print(f"  FINAL : {short(line)}")
    print(f"\n{same} of {len(a)} draft lines are unchanged in the final ({len(b)} lines in the final).")
    if shown >= args.max:
        print(f"Output stopped after {args.max} changes. Use --max to see more.")


if __name__ == "__main__":
    main()
