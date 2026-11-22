#!/usr/bin/env python3
"""Build a PowerPoint deck from a deck.json using a deck type's template, and check a deck type folder.

  python fill_deck.py build <decktype-dir> <deck.json> <out.pptx>
  python fill_deck.py check <decktype-dir>

Slide kinds: title, agenda, section, bullets, two_column, cards, process, stats, table, cases, timeline, closing.
Any text wrapped in [brackets], or inside an element marked "todo": true, gets a red highlight.
Needs only python-pptx.
"""
import argparse
import calendar
import copy
import json
import math
import re
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.dml import MSO_LINE, MSO_THEME_COLOR
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE, PP_PLACEHOLDER
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Pt
except ImportError:
    sys.exit("python-pptx is missing. Run: pip install python-pptx")

IN = 914400
TODO_RED = "FF0000"
BRACKETED = re.compile(r"(\[[^\[\]]+\])")
THEME = {"bg1": MSO_THEME_COLOR.BACKGROUND_1, "bg2": MSO_THEME_COLOR.BACKGROUND_2, "tx1": MSO_THEME_COLOR.TEXT_1,
         "tx2": MSO_THEME_COLOR.TEXT_2, "accent1": MSO_THEME_COLOR.ACCENT_1, "accent3": MSO_THEME_COLOR.ACCENT_3,
         "accent4": MSO_THEME_COLOR.ACCENT_4}
ANCHOR = {"t": MSO_ANCHOR.TOP, "ctr": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}
LAYOUT_KEYS = ("title", "section", "bullets", "two_column", "component", "closing")
# kind: (layout key, allowed keys besides kind/notes/todo, show slide number)
KINDS = {
    "title": ("title", {"title", "subtitle", "aws"}, False),
    "agenda": ("component", {"title", "items"}, True),
    "section": ("section", {"kicker", "title"}, True),
    "bullets": ("bullets", {"title", "bullets"}, True),
    "two_column": ("two_column", {"title", "left", "right"}, True),
    "cards": ("component", {"title", "cards"}, True),
    "process": ("component", {"title", "steps"}, True),
    "stats": ("component", {"title", "stats", "detail"}, True),
    "table": ("component", {"title", "columns", "rows", "bold_columns", "footnotes"}, True),
    "cases": ("component", {"title", "cases"}, True),
    "timeline": ("component", {"title", "programme", "start", "months", "phases", "milestones"}, True),
    "closing": ("closing", {"title", "subtitle"}, False),
}
TIMELINE_X, TIMELINE_W = 2.8, 9.9
AWS_ARROW = "amazon_arrow.png"  # in the deck type's icons/, supplied by the user: never drawn here


# ---------- small helpers ----------

def inch(v):
    return Emu(int(round(v * IN)))


def text_of(item):
    """A list item is a string or {"text": ..., "todo": true}. Returns (text, todo)."""
    if isinstance(item, dict):
        return str(item.get("text", "")), bool(item.get("todo"))
    return str(item), False


def parse_month(value, with_day=False):
    m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", str(value))
    if not m or not 1 <= int(m.group(2)) <= 12 or (m.group(3) and not with_day):
        raise ValueError(value)
    year, month = int(m.group(1)), int(m.group(2))
    if with_day:
        day = int(m.group(3)) if m.group(3) else None
        return year, month, day
    return year, month


def month_index(start, ym):
    return (ym[0] - start[0]) * 12 + (ym[1] - start[1])


def estimate_lines(text, width, pt, bold=False):
    per_line = max(1, int(width * 72 / (pt * (0.58 if bold else 0.52))))
    return sum(max(1, math.ceil(len(part) / per_line)) for part in str(text).split("\n"))


# ---------- template ----------

def title_of(slide):
    """The title placeholder, found by type: python-pptx's slide.shapes.title needs idx 0, which this template does not use."""
    return next((p for p in slide.placeholders if p.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)), None)


def open_template(path: Path):
    try:
        return Presentation(str(path))
    except ValueError:  # python-pptx refuses .potx: make it a normal presentation in a temp copy
        with tempfile.TemporaryDirectory() as tmp:
            copy_path = Path(tmp) / "template.pptx"
            with zipfile.ZipFile(path) as zin, zipfile.ZipFile(copy_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "[Content_Types].xml":
                        data = data.replace(b"presentationml.template.main+xml", b"presentationml.presentation.main+xml")
                    zout.writestr(item, data)
            return Presentation(str(copy_path))


def load_definition(deck_dir: Path):
    path = deck_dir / "fields.json"
    if not path.exists():
        return None, [f"{path} not found"]
    try:
        defn = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path} is not valid JSON: {exc}"]
    problems = []
    if defn.get("name") != deck_dir.name:
        problems.append(f"'name' in fields.json must be '{deck_dir.name}', the folder name")
    missing = [k for k in LAYOUT_KEYS if k not in defn.get("layouts", {})]
    if missing:
        problems.append(f"fields.json 'layouts' needs: {', '.join(missing)}")
    for icon, fname in defn.get("icons", {}).items():
        if not (deck_dir / "icons" / fname).exists():
            problems.append(f"icon '{icon}': icons/{fname} not found")
    if not (deck_dir / "template.potx").exists():
        problems.append("template.potx not found")
    return defn, problems


# ---------- checking a deck.json ----------

def check_deck(defn: dict, deck: dict) -> list:
    problems = []
    for key in deck:
        if key not in ("title", "customer", "slides"):
            problems.append(f"deck has a field it does not know: '{key}'")
    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        return problems + ["'slides' must be a non-empty list"]
    for n, s in enumerate(slides, 1):
        where = f"slide {n}"
        kind = s.get("kind")
        if kind not in KINDS:
            problems.append(f"{where}: kind must be one of {sorted(KINDS)}")
            continue
        for key in s:
            if key not in KINDS[kind][1] | {"kind", "notes", "todo"}:
                problems.append(f"{where} ({kind}): unknown field '{key}'")
        if "aws" in s and not isinstance(s["aws"], bool):
            problems.append(f"{where}: 'aws' must be true or false")
        need = {"title"} if kind not in ("section",) else {"title", "kicker"}
        for key in need:
            if not isinstance(s.get(key), str) or not s[key].strip():
                problems.append(f"{where} ({kind}): '{key}' must be text")
        problems += CHECKS.get(kind, lambda s, where, defn: [])(s, where, defn)
    return problems


def need_list(s, key, where, lo, hi):
    items = s.get(key)
    if not isinstance(items, list) or not lo <= len(items) <= hi:
        return [f"{where}: '{key}' must be a list of {lo} to {hi}"]
    return []


def check_agenda(s, where, defn):
    return need_list(s, "items", where, 1, 5)


def check_bullets(s, where, defn):
    return need_list(s, "bullets", where, 1, 8)


def check_two_column(s, where, defn):
    return need_list(s, "left", where, 1, 8) + need_list(s, "right", where, 1, 8)


def check_cards(s, where, defn):
    problems = need_list(s, "cards", where, 2, 3)
    for i, c in enumerate(s.get("cards") or [], 1):
        if c.get("icon") not in defn.get("icons", {}):
            problems.append(f"{where} card {i}: icon must be one of {sorted(defn.get('icons', {}))}")
        if not c.get("heading"):
            problems.append(f"{where} card {i}: needs a heading")
        problems += need_list(c, "items", f"{where} card {i}", 1, 6)
    return problems


def check_process(s, where, defn):
    problems = need_list(s, "steps", where, 1, 3)
    for i, st in enumerate(s.get("steps") or [], 1):
        if not st.get("activity"):
            problems.append(f"{where} step {i}: needs an activity")
        problems += need_list(st, "outputs", f"{where} step {i}", 1, 3)
    return problems


def check_stats(s, where, defn):
    problems = need_list(s, "stats", where, 2, 3)
    for i, st in enumerate(s.get("stats") or [], 1):
        if not st.get("value") or not st.get("label"):
            problems.append(f"{where} stat {i}: needs a value and a label")
    return problems


def check_cases(s, where, defn):
    problems = need_list(s, "cases", where, 2, 3)
    for i, c in enumerate(s.get("cases") or [], 1):
        for key in ("customer", "challenge", "solution", "outcome"):
            if not c.get(key):
                problems.append(f"{where} case {i}: needs '{key}'")
    return problems


def check_timeline(s, where, defn):
    problems = need_list(s, "phases", where, 1, 6)
    try:
        start = parse_month(s.get("start"))
    except ValueError:
        return problems + [f"{where}: 'start' must be a month like 2027-01"]
    months = s.get("months", 24)
    if start[1] not in (1, 4, 7, 10):
        problems.append(f"{where}: 'start' must be the first month of a quarter (Jan, Apr, Jul or Oct)")
    if not isinstance(months, int) or months % 3 or not 3 <= months <= 36:
        problems.append(f"{where}: 'months' must be a multiple of 3 from 3 to 36")
        return problems
    for i, p in enumerate(s.get("phases") or [], 1):
        try:
            a, b = month_index(start, parse_month(p.get("start"))), month_index(start, parse_month(p.get("end")))
        except ValueError:
            problems.append(f"{where} phase {i}: 'start' and 'end' must be months like 2027-03")
            continue
        if not p.get("name"):
            problems.append(f"{where} phase {i}: needs a name")
        if b < a or a < 0 or b >= months:
            problems.append(f"{where} phase {i}: runs outside the {months}-month grid, or ends before it starts")
    ms = s.get("milestones", [])
    if not isinstance(ms, list) or len(ms) > 3:
        problems.append(f"{where}: 'milestones' must be a list of at most 3")
        return problems
    for i, m in enumerate(ms, 1):
        try:
            y, mo, _ = parse_month(m.get("date"), with_day=True)
        except ValueError:
            problems.append(f"{where} milestone {i}: 'date' must be like 2027-04 or 2027-04-15")
            continue
        if not m.get("label") or not 0 <= month_index(start, (y, mo)) < months:
            problems.append(f"{where} milestone {i}: needs a label and a date inside the grid")
    return problems


def check_table(s, where, defn):
    problems = need_list(s, "columns", where, 2, 7) + need_list(s, "rows", where, 1, 7)
    cols = s.get("columns") if isinstance(s.get("columns"), list) else []
    for name in s.get("bold_columns", []):
        if name not in cols:
            problems.append(f"{where}: bold_columns names '{name}', which is not a column")
    for i, row in enumerate(s.get("rows") if isinstance(s.get("rows"), list) else [], 1):
        cells = row.get("cells") if isinstance(row, dict) else row
        if not isinstance(cells, list) or len(cells) != len(cols):
            problems.append(f"{where} row {i}: needs {len(cols)} cells, one per column")
        if isinstance(row, dict) and row.get("total") and row.get("extra"):
            problems.append(f"{where} row {i}: cannot be both a total and an extra row")
    notes = s.get("footnotes", [])
    if not isinstance(notes, list) or len(notes) > 3:
        problems.append(f"{where}: 'footnotes' must be a list of at most 3")
    return problems


CHECKS = {"table": check_table, "agenda": check_agenda, "bullets": check_bullets, "two_column": check_two_column, "cards": check_cards,
          "process": check_process, "stats": check_stats, "cases": check_cases, "timeline": check_timeline}


# ---------- building ----------

class Deck:
    def __init__(self, prs, defn, deck_dir):
        self.prs, self.defn, self.deck_dir = prs, defn, deck_dir
        self.layouts = {l.name: l for l in prs.slide_layouts}
        self.warnings, self.todos, self.n = [], [], 0

    # -- text and shapes --

    def fit(self, what, text, width, height, pt, bold=False, spacing=0.0):
        lines = estimate_lines(text, width, pt, bold)
        if lines * pt * 1.2 / 72 + spacing > height + 0.02:
            self.warnings.append(f"slide {self.n}: {what} may not fit its box ({lines} lines at {pt} pt)")

    def runs(self, par, text, whole_todo, **fmt):
        segments = [(text, True)] if whole_todo else [(s, bool(BRACKETED.fullmatch(s))) for s in BRACKETED.split(text) if s]
        for seg, todo in segments:
            run = par.add_run()
            run.text = seg
            font = run.font
            if fmt.get("size"):
                font.size = Pt(fmt["size"])
            if fmt.get("bold") is not None:
                font.bold = fmt["bold"]
            if fmt.get("color"):
                font.color.theme_color = THEME[fmt["color"]]
            rpr = run._r.get_or_add_rPr()
            rpr.set("lang", "en-US")
            if fmt.get("spc"):
                rpr.set("spc", str(fmt["spc"]))
                rpr.set("kern", "0")
            if todo:
                hl = rpr.makeelement(qn("a:highlight"), {})
                hl.append(hl.makeelement(qn("a:srgbClr"), {"val": TODO_RED}))
                rpr.append(hl)
                self.todos.append((self.n, seg))

    @staticmethod
    def no_bullet(par, align=None, after=None):
        if align:
            par.alignment = align
        if after:
            par.space_after = Pt(after)
        ppr = par._p.get_or_add_pPr()
        ppr.set("marL", "0")
        ppr.set("indent", "0")
        ppr.append(ppr.makeelement(qn("a:buNone"), {}))

    def textbox(self, slide, x, y, w, h, paras, anchor="ctr", align=None, after=None, name=None, todo=False):
        """paras: list of paragraphs; a paragraph is a list of (text, format) runs."""
        box = slide.shapes.add_textbox(inch(x), inch(y), inch(w), inch(h))
        if name:
            box.name = name
        tf = box.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = ANCHOR[anchor]
        for i, par_runs in enumerate(paras):
            par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            self.no_bullet(par, align, after)
            for text, fmt in par_runs:
                self.runs(par, text, bool(todo or fmt.get("todo")), **fmt)
        return box

    @staticmethod
    def flat(shape, color, name=None):
        style = shape._element.find(qn("p:style"))
        if style is not None:
            shape._element.remove(style)
        shape.fill.solid()
        shape.fill.fore_color.theme_color = THEME[color]
        shape.line.fill.background()
        if name:
            shape.name = name

    def card(self, slide, x, y, w, h, name, color="tx2", radius=0.08, kind=MSO_SHAPE.ROUNDED_RECTANGLE):
        shape = slide.shapes.add_shape(kind, inch(x), inch(y), inch(w), inch(h))
        if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
            shape.adjustments[0] = min(0.5, radius / min(w, h))
        self.flat(shape, color, name)
        return shape

    @staticmethod
    def line(slide, x1, y1, x2, y2, color, width_pt, name, dash=False):
        conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, inch(x1), inch(y1), inch(x2), inch(y2))
        style = conn._element.find(qn("p:style"))
        if style is not None:
            conn._element.remove(style)
        conn.line.color.theme_color = THEME[color]
        conn.line.width = Pt(width_pt)
        if dash:
            conn.line.dash_style = MSO_LINE.DASH
        conn.name = name

    # -- placeholders and slide plumbing --

    def new_slide(self, s):
        key = KINDS[s["kind"]][0]
        slide = self.prs.slides.add_slide(self.layouts[self.defn["layouts"][key]])
        self.n += 1
        if KINDS[s["kind"]][2]:
            self.slide_number(slide)
        return slide

    def slide_number(self, slide):
        for ph in slide.slide_layout.placeholders:
            if ph.placeholder_format.type == PP_PLACEHOLDER.SLIDE_NUMBER:
                el = copy.deepcopy(ph._element)
                ids = [int(i) for i in slide.shapes._spTree.xpath("//p:cNvPr/@id")]
                el.xpath(".//p:cNvPr")[0].set("id", str(max(ids) + 1))
                for t in el.xpath(".//a:fld/a:t"):
                    t.text = str(self.n)
                slide.shapes._spTree.append(el)
                return

    def fill(self, slide, s, bodies=(), bullets=False):
        """Fill the title and the other placeholders (in idx order), formatted like the template's example slides."""
        key = KINDS[s["kind"]][0]
        title_anchor, body_anchor = {"title": ("b", "t"), "closing": ("b", "t"), "section": ("t", None)}.get(key, ("ctr", "t"))
        phs = [p for p in slide.placeholders if p.placeholder_format.type != PP_PLACEHOLDER.SLIDE_NUMBER]
        titles = [p for p in phs if p.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)]
        rest = sorted((p for p in phs if p not in titles), key=lambda p: p.placeholder_format.idx)
        targets = [(titles[0], [s["title"]], title_anchor)] if titles else []
        targets += [(ph, lines, body_anchor) for ph, lines in zip(rest, bodies)]
        for ph, lines, anchor in targets:
            tf = ph.text_frame
            tf.clear()
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            if anchor:
                tf.vertical_anchor = ANCHOR[anchor]
            for i, line in enumerate(lines):
                text, item_todo = text_of(line)
                opts = line if isinstance(line, dict) else {}
                heading = bool(opts.get("heading"))  # a group heading: bold, no bullet
                par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                if bullets and ph not in titles and not heading:
                    self.bullet(par)
                else:
                    self.no_bullet(par, PP_ALIGN.LEFT, after=8 if heading else None)
                    if heading and i:
                        par.space_before = Pt(10)
                self.runs(par, text, bool(s.get("todo")) or item_todo, **({"bold": True} if heading or opts.get("bold") else {}))

    @staticmethod
    def bullet(par):
        par.space_after = Pt(8)
        ppr = par._p.get_or_add_pPr()
        ppr.set("algn", "l")
        ppr.set("marL", "342900")
        ppr.set("indent", "-342900")
        ppr.append(ppr.makeelement(qn("a:buSzPct"), {"val": "100000"}))
        ppr.append(ppr.makeelement(qn("a:buChar"), {"char": "•"}))

    @staticmethod
    def notes(slide, s):
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]

    def heading(self, slide, s):
        self.fit("the title", s["title"], 10.1, 0.85, 32, bold=True)
        self.fill(slide, s)

    # -- slide kinds --

    def build_slide(self, s):
        slide = self.new_slide(s)
        getattr(self, "kind_" + s["kind"])(slide, s)
        self.notes(slide, s)

    def kind_title(self, slide, s):
        self.fill(slide, s, bodies=[[s.get("subtitle", "")]])
        if s.get("aws"):
            self.aws_arrow(slide)

    def aws_arrow(self, slide):
        """The Amazon arrow under the title, left-aligned with it, at its own aspect ratio."""
        pic = slide.shapes.add_picture(str(self.deck_dir / "icons" / AWS_ARROW), inch(0.62), inch(4.6), width=inch(1.9))
        pic.name = "AWS arrow"
        pic._element.xpath(".//p:cNvPr")[0].set("descr", "Amazon arrow")
        subtitle = [p for p in slide.placeholders if p.placeholder_format.type == PP_PLACEHOLDER.SUBTITLE or
                    (p.placeholder_format.type == PP_PLACEHOLDER.BODY and p.top > pic.top)]
        if subtitle and pic.top + pic.height > min(p.top for p in subtitle) - inch(0.05):
            self.warnings.append(f"slide {self.n}: the AWS arrow may overlap the subtitle (the image is taller than expected)")

    kind_closing = kind_title

    def kind_section(self, slide, s):
        self.fill(slide, s, bodies=[[s["kicker"]]])
        self.clear_of_art(slide, s)

    def clear_of_art(self, slide, s):
        """Narrow the title so it stops before the layout's cloud picture (the slide only; the layout is untouched)."""
        art = [sh for sh in slide.slide_layout.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.width > inch(4)]
        title = title_of(slide)
        if not art or title is None:
            return
        left, top, height = title.left, title.top, title.height
        width = max(inch(2), min(title.width, min(a.left for a in art) - inch(0.2) - left))
        title.left, title.top, title.width, title.height = left, top, width, height
        self.fit("the section title", s["title"], width / IN, 1.35, 40, bold=True)  # two lines at the template's 40 pt

    def kind_bullets(self, slide, s):
        self.fill(slide, s, bodies=[s["bullets"]], bullets=True)

    def kind_two_column(self, slide, s):
        self.fill(slide, s, bodies=[s["left"], s["right"]], bullets=True)

    def kind_agenda(self, slide, s):
        self.heading(slide, s)
        for i, item in enumerate(s["items"]):
            text, todo = text_of(item)
            y = 1.65 + i * 1.0
            self.card(slide, 0.6, y, 12.1, 0.8, f"Agenda row {i + 1}")
            self.textbox(slide, 0.9, y, 0.8, 0.8, [[(f"{i + 1:02d}", dict(size=22, bold=True, color="accent1"))]], name=f"Agenda number {i + 1}")
            self.fit(f"agenda item {i + 1}", text, 10.5, 0.8, 18)
            self.textbox(slide, 1.8, y, 10.5, 0.8, [[(text, dict(size=18, color="bg1"))]], name=f"Agenda item {i + 1}", todo=todo or s.get("todo"))

    @staticmethod
    def columns(n):
        w = (12.1 - 0.2 * (n - 1)) / n
        return [(0.6 + i * (w + 0.2), w) for i in range(n)]

    def kind_cards(self, slide, s):
        self.heading(slide, s)
        for i, (c, (x, w)) in enumerate(zip(s["cards"], self.columns(len(s["cards"]))), 1):
            todo = bool(c.get("todo") or s.get("todo"))
            self.card(slide, x, 1.55, w, 5.2, f"Card {i}", radius=0.08)
            self.card(slide, x + 0.3, 1.8, 0.75, 0.75, f"Icon circle {i}", color="accent1", kind=MSO_SHAPE.OVAL)
            pic = slide.shapes.add_picture(str(self.deck_dir / "icons" / self.defn["icons"][c["icon"]]),
                                           inch(x + 0.42), inch(1.92), inch(0.51), inch(0.51))
            pic.name = f"Icon {i}"
            pic._element.xpath(".//p:cNvPr")[0].set("descr", f"{c['icon']} icon")
            self.fit(f"card {i} heading", c["heading"], w - 1.5, 0.75, 20, bold=True)
            self.textbox(slide, x + 1.25, 1.8, w - 1.5, 0.75, [[(c["heading"], dict(size=20, bold=True, color="bg1"))]], name=f"Heading {i}", todo=todo)
            paras, total = [], 0.0
            for item in c["items"]:
                label, text = (item.get("label"), item.get("text", "")) if isinstance(item, dict) else (None, str(item))
                runs = ([(f"{label}:", dict(size=13, bold=True, color="accent1")), (f" {text}", dict(size=13, color="bg1"))]
                        if label else [(text, dict(size=13, color="bg1"))])
                paras.append(runs)
                total += estimate_lines(f"{label}: {text}" if label else text, w - 0.6, 13) * 13 * 1.2 / 72 + 9 / 72
            if total > 3.8:
                self.warnings.append(f"slide {self.n}: card {i} text may not fit its box")
            self.textbox(slide, x + 0.3, 2.8, w - 0.6, 3.8, paras, anchor="t", after=9, name=f"Items {i}", todo=todo)

    def kind_process(self, slide, s):
        self.heading(slide, s)
        head = dict(size=11, bold=True, color="bg2", spc=200)
        self.textbox(slide, 0.6, 1.5, 5.6, 0.3, [[("ACTIVITY", head)]], name="Activity header")
        self.textbox(slide, 6.95, 1.5, 5.75, 0.3, [[("OUTPUTS", head)]], name="Outputs header")
        for i, st in enumerate(s["steps"]):
            y, todo = 1.95 + i * 1.6, bool(st.get("todo") or s.get("todo"))
            self.card(slide, 0.6, y, 5.6, 1.35, f"Activity {i + 1}")
            self.card(slide, 0.9, y + 0.38, 0.6, 0.6, f"Step {i + 1} circle", color="accent1", kind=MSO_SHAPE.OVAL)
            self.textbox(slide, 0.9, y + 0.38, 0.6, 0.6, [[(str(i + 1), dict(size=18, bold=True, color="tx1"))]], align=PP_ALIGN.CENTER, name=f"Step {i + 1} number")
            self.fit(f"step {i + 1} activity", st["activity"], 4.25, 1.35, 16)
            self.textbox(slide, 1.75, y, 4.25, 1.35, [[(st["activity"], dict(size=16, color="bg1"))]], name=f"Activity text {i + 1}", todo=todo)
            self.card(slide, 6.35, y + 0.5, 0.45, 0.35, f"Arrow {i + 1}", color="accent1", kind=MSO_SHAPE.RIGHT_ARROW)
            self.card(slide, 6.95, y, 5.75, 1.35, f"Outputs {i + 1}")
            outputs = [text_of(o) for o in st["outputs"]]
            self.fit(f"step {i + 1} outputs", "\n".join(text for text, _ in outputs), 5.25, 1.35, 16)
            self.textbox(slide, 7.25, y, 5.25, 1.35, [[(text, dict(size=16, color="bg1", todo=item_todo))] for text, item_todo in outputs],
                         name=f"Outputs text {i + 1}", todo=todo)

    def kind_stats(self, slide, s):
        self.heading(slide, s)
        for i, (st, (x, w)) in enumerate(zip(s["stats"], self.columns(len(s["stats"]))), 1):
            todo = bool(st.get("todo") or s.get("todo"))  # the value only; the label is marked only by the slide's todo
            self.card(slide, x, 1.55, w, 2.0, f"Stat {i}", radius=0.08)
            self.fit(f"stat {i} value", st["value"], w - 0.6, 1.0, 44, bold=True)
            self.textbox(slide, x + 0.3, 1.75, w - 0.6, 1.0, [[(st["value"], dict(size=44, bold=True, color="bg1"))]], name=f"Stat value {i}", todo=todo)
            self.fit(f"stat {i} label", st["label"], w - 0.6, 0.5, 14)
            self.textbox(slide, x + 0.3, 2.8, w - 0.6, 0.5, [[(st["label"], dict(size=14, color="bg2"))]], name=f"Stat label {i}", todo=bool(s.get("todo")))
        detail = s.get("detail")
        if detail:
            lines = [detail] if isinstance(detail, str) else detail
            self.card(slide, 0.6, 3.8, 12.1, 2.95, "Detail area", radius=0.08)
            self.fit("the detail text", "\n".join(text_of(l)[0] for l in lines), 11.5, 2.45, 16, spacing=0.15 * len(lines))
            self.textbox(slide, 0.9, 4.05, 11.5, 2.45, [[(text_of(l)[0], dict(size=16, color="bg1"))] for l in lines],
                         anchor="t", after=8, name="Detail text", todo=s.get("todo"))

    def kind_table(self, slide, s):
        self.heading(slide, s)
        cols = s["columns"]
        rows = [r if isinstance(r, dict) else {"cells": r} for r in s["rows"]]
        first = 12.1 / 2 if len(cols) == 2 else 12.1 * 0.32
        widths = [first] + [(12.1 - first) / (len(cols) - 1)] * (len(cols) - 1)
        bold = {cols.index(c) for c in s.get("bold_columns", [])}
        y = self.table(slide, 1.55, widths, [{"cells": cols, "kind": "header"}] + [r for r in rows if not r.get("extra")], bold, "Table", s)
        extra = [{**r, "kind": "extra"} for r in rows if r.get("extra")]
        if extra:  # extra charges sit apart from the table, with a gap
            self.table(slide, y + 0.2, widths, extra, bold, "Extra charges", s)
        notes = s.get("footnotes", [])
        if notes:
            self.textbox(slide, 0.6, 6.15, 12.1, 0.75, [[(text_of(n)[0], dict(size=11, color="bg2", todo=text_of(n)[1]))] for n in notes],
                         anchor="t", after=3, name="Footnotes", todo=s.get("todo"))

    def table(self, slide, y, widths, rows, bold, name, s):
        """Draw a real PowerPoint table with no table style; return the y where it ends."""
        height = 0.5
        frame = slide.shapes.add_table(len(rows), len(widths), inch(0.6), inch(y), inch(sum(widths)), inch(height * len(rows)))
        frame.name = name
        tbl = frame.table
        props = tbl._tbl.tblPr
        for attr in ("firstRow", "bandRow"):
            props.attrib.pop(attr, None)
        style = props.find(qn("a:tableStyleId"))
        if style is not None:
            props.remove(style)
        for c, w in enumerate(widths):
            tbl.columns[c].width = inch(w)
        for r, row in enumerate(rows):
            tbl.rows[r].height = inch(height)
            kind = row.get("kind") or ("total" if row.get("total") else "body")
            for c, item in enumerate(row["cells"]):
                text, todo = text_of(item)
                bold_cell = kind in ("header", "total") or c in bold
                fmt = {"header": dict(size=12, bold=True, color="accent1"), "extra": dict(size=14, color="bg2")}.get(kind, dict(size=14, color="bg1"))
                fmt = {**fmt, "bold": bold_cell or fmt.get("bold")}
                if estimate_lines(text, widths[c] - 0.3, fmt["size"], bool(fmt["bold"])) > 1:
                    self.warnings.append(f"slide {self.n}: table cell '{text[:30]}' may wrap, which makes its row taller")
                cell = tbl.cell(r, c)
                cell.margin_left = cell.margin_right = inch(0.15)
                cell.margin_top = cell.margin_bottom = inch(0.05)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                par = cell.text_frame.paragraphs[0]
                self.no_bullet(par, PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT)
                self.runs(par, text, bool(todo or row.get("todo") or s.get("todo")), **fmt)
                if kind in ("header", "extra", "total"):
                    cell.fill.solid()
                    cell.fill.fore_color.theme_color = THEME["tx2" if kind != "total" else "accent4"]
                else:
                    cell.fill.background()
                self.borders(cell, "accent4" if kind == "body" else None)
        return y + height * len(rows)

    @staticmethod
    def borders(cell, bottom_color):
        """No outline on any side, except a thin line under body rows (no table style, so nothing else is drawn)."""
        props = cell._tc.get_or_add_tcPr()
        for pos, side in enumerate(("L", "R", "T", "B")):
            line = props.makeelement(qn(f"a:ln{side}"), {"w": "9525", "cap": "flat", "cmpd": "sng", "algn": "ctr"})
            if side == "B" and bottom_color:
                fill = line.makeelement(qn("a:solidFill"), {})
                fill.append(fill.makeelement(qn("a:schemeClr"), {"val": bottom_color}))
                line.append(fill)
            else:
                line.append(line.makeelement(qn("a:noFill"), {}))
            props.insert(pos, line)  # border lines come first in a cell's properties, before its fill

    def kind_cases(self, slide, s):
        self.heading(slide, s)
        for i, (c, (x, w)) in enumerate(zip(s["cases"], self.columns(len(s["cases"]))), 1):
            todo = bool(c.get("todo") or s.get("todo"))
            self.card(slide, x, 1.55, w, 5.2, f"Customer card {i}", radius=0.08)
            self.fit(f"case {i} customer name", c["customer"], w - 0.6, 0.5, 20, bold=True)
            self.textbox(slide, x + 0.3, 1.8, w - 0.6, 0.5, [[(c["customer"], dict(size=20, bold=True, color="bg1"))]], name=f"Customer {i}", todo=todo)
            for j, key in enumerate(("challenge", "solution", "outcome")):
                y = 2.6 + j * 1.35
                self.textbox(slide, x + 0.3, y, w - 0.6, 0.3, [[(key.upper(), dict(size=11, bold=True, color="accent1", spc=200))]], name=f"{key.title()} label {i}")
                self.fit(f"case {i} {key}", c[key], w - 0.6, 0.8, 14)
                self.textbox(slide, x + 0.3, y + 0.32, w - 0.6, 0.8, [[(c[key], dict(size=14, color="bg2"))]], anchor="t", name=f"{key.title()} text {i}", todo=todo)

    def kind_timeline(self, slide, s):
        self.heading(slide, s)
        start, months = parse_month(s["start"]), s.get("months", 24)
        mw, qw = TIMELINE_W / months, TIMELINE_W / (months // 3)
        if s.get("programme"):
            self.textbox(slide, 0.6, 1.35, 4.0, 0.35, [[(s["programme"], dict(size=14, bold=True, color="accent1"))]], name="Programme name")
        for q in range(months // 3):
            year, month = start[0] + (start[1] - 1 + 3 * q) // 12, (start[1] - 1 + 3 * q) % 12 + 1
            label = f"Q{(month - 1) // 3 + 1}/{year % 100:02d}"
            self.textbox(slide, TIMELINE_X + q * qw, 6.43, qw, 0.35, [[(label, dict(size=11, color="bg2"))]], align=PP_ALIGN.CENTER, name=f"Quarter {q + 1}")
            if q:
                self.line(slide, TIMELINE_X + q * qw, 2.45, TIMELINE_X + q * qw, 6.38, "accent4", 0.75, f"Grid {q}")
        self.line(slide, TIMELINE_X, 6.38, TIMELINE_X + TIMELINE_W, 6.38, "bg2", 1.0, "Axis")
        xs = []
        for i, m in enumerate(s.get("milestones", []), 1):
            y, mo, day = parse_month(m["date"], with_day=True)
            frac = 0.5 if day is None else (day - 1) / calendar.monthrange(y, mo)[1]
            x = TIMELINE_X + (month_index(start, (y, mo)) + frac) * mw
            xs.append(x)
            if len(xs) > 1 and abs(xs[-1] - xs[-2]) < 1.9:
                self.warnings.append(f"slide {self.n}: milestones {i - 1} and {i} are close, their labels may overlap")
            self.line(slide, x, 2.25, x, 6.38, "accent3", 1.25, f"Milestone {i} line", dash=True)
            self.card(slide, x - 0.11, 2.14, 0.22, 0.22, f"Milestone {i} dot", color="accent3", kind=MSO_SHAPE.OVAL)
            left = x + 0.2 + 1.6 > TIMELINE_X + TIMELINE_W
            self.textbox(slide, x - 1.8 if left else x + 0.2, 1.70, 1.6, 0.55,
                         [[(m["label"], dict(size=11, bold=True, color="bg1"))], [(self.milestone_date(m["date"]), dict(size=11, color="accent3"))]],
                         align=PP_ALIGN.RIGHT if left else None, name=f"Milestone {i} label", todo=m.get("todo") or s.get("todo"))
        for j, p in enumerate(s["phases"]):
            todo = bool(p.get("todo") or s.get("todo"))
            a, b = month_index(start, parse_month(p["start"])), month_index(start, parse_month(p["end"])) + 1
            x, w = TIMELINE_X + a * mw + 0.03, (b - a) * mw - 0.06
            self.fit(f"phase {j + 1} name", p["name"], 2.0, 0.5, 15, bold=True)
            self.textbox(slide, 0.6, 2.6 + 0.63 * j, 2.0, 0.5, [[(p["name"], dict(size=15, bold=True, color="bg1"))]], name=f"Phase {j + 1} name", todo=todo)
            self.card(slide, x, 2.64 + 0.63 * j, w, 0.42, f"Phase {j + 1} bar", color="accent1", radius=0.06)
            label = p.get("label") or self.date_label(parse_month(p["start"]), parse_month(p["end"]))
            label_w = len(label) * 11 * 0.6 / 72
            y_bar = 2.64 + 0.63 * j
            if w >= label_w + 0.2:
                self.textbox(slide, x, y_bar, w, 0.42, [[(label, dict(size=11, bold=True, color="tx1"))]], align=PP_ALIGN.CENTER, name=f"Phase {j + 1} dates", todo=todo)
            elif x + w + 0.1 + label_w <= TIMELINE_X + TIMELINE_W:
                self.textbox(slide, x + w + 0.1, y_bar, label_w + 0.3, 0.42, [[(label, dict(size=11, bold=True, color="bg1"))]], name=f"Phase {j + 1} dates", todo=todo)
            else:  # no room to the right at the end of the grid: beside the bar on its left
                self.textbox(slide, x - 0.1 - label_w - 0.3, y_bar, label_w + 0.3, 0.42, [[(label, dict(size=11, bold=True, color="bg1"))]],
                             align=PP_ALIGN.RIGHT, name=f"Phase {j + 1} dates", todo=todo)

    @staticmethod
    def milestone_date(value):
        y, mo, day = parse_month(value, with_day=True)
        return f"{day} {calendar.month_abbr[mo]} {y}" if day else f"{calendar.month_abbr[mo]} {y}"

    @staticmethod
    def date_label(a, b):
        name = lambda ym: calendar.month_abbr[ym[1]]
        if a == b:
            return name(a)
        return f"{name(a)} – {name(b)}" if a[0] == b[0] else f"{name(a)} {a[0] % 100:02d} – {name(b)} {b[0] % 100:02d}"


def build_deck(deck_dir: Path, defn: dict, deck: dict, out: Path):
    prs = open_template(deck_dir / "template.potx")
    missing = [n for n in defn["layouts"].values() if n not in {l.name for l in prs.slide_layouts}]
    if missing:
        return [], [], [f"the template has no layout named: {', '.join(missing)}"]
    sld_ids = prs.slides._sldIdLst
    for sld_id in list(sld_ids):  # drop the template's example slides
        prs.part.drop_rel(sld_id.rId)
        sld_ids.remove(sld_id)
    builder = Deck(prs, defn, deck_dir)
    for s in deck["slides"]:
        builder.build_slide(s)
    if deck.get("title"):
        prs.core_properties.title = deck["title"]
    prs.save(str(out))
    return builder.warnings, builder.todos, []


# ---------- commands ----------

def report(title, problems):
    print(f"{title}:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


def cmd_build(args) -> int:
    deck_dir, out = Path(args.decktype), Path(args.out)
    defn, problems = load_definition(deck_dir)
    if problems:
        return report("The deck type has problems", problems)
    try:
        deck = json.loads(Path(args.deck).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return report("Cannot read the deck", [str(exc)])
    problems = check_deck(defn, deck)
    if any(s.get("aws") for s in deck.get("slides", [])) and not (deck_dir / "icons" / AWS_ARROW).exists():
        problems.append(f"a title slide has \"aws\": true, but icons/{AWS_ARROW} is not in the deck type: add the Amazon arrow image you were given")
    if problems:
        return report("The deck needs fixing before it can be built", problems)
    if out.exists():
        return report("Not overwriting an existing file", [f"{out} exists: use the next version number"])
    warnings, todos, problems = build_deck(deck_dir, defn, deck, out)
    if problems:
        return report("The deck was not built", problems)
    print(f"OK: wrote {out} ({len(deck['slides'])} slides)")
    for w in warnings:
        print(f"Warning: {w}")
    if todos:
        print(f"\nTo-dos highlighted in red ({len(todos)}):")
        for n, text in todos:
            print(f"  slide {n}: {text}")
    return 0


def cmd_check(args) -> int:
    deck_dir = Path(args.decktype)
    defn, problems = load_definition(deck_dir)
    if not problems:
        prs = open_template(deck_dir / "template.potx")
        names = {l.name for l in prs.slide_layouts}
        problems = [f"layout '{n}' is not in the template (it has: {', '.join(sorted(names))})"
                    for n in defn["layouts"].values() if n not in names]
    if problems:
        return report("The deck type has problems", problems)
    print(f"OK: deck type '{defn['name']}' is consistent ({len(defn['icons'])} icons)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build a .pptx from a deck.json")
    b.add_argument("decktype")
    b.add_argument("deck")
    b.add_argument("out")
    b.set_defaults(func=cmd_build)
    c = sub.add_parser("check", help="check that a deck type folder is consistent")
    c.add_argument("decktype")
    c.set_defaults(func=cmd_check)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
