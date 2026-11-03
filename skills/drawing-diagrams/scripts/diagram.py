#!/usr/bin/env python3
"""Turn a small diagram spec (JSON) into a draw.io file, with automatic layout.

  python diagram.py build <spec.json> <out.drawio> [--png preview.png] [--allow-detail]
  python diagram.py check <spec.json> [--allow-detail]

The spec format is in spec-format.md. Open the .drawio file at app.diagrams.net or in the
draw.io desktop app; arrows are routed by draw.io itself when it opens the file.
The .png is a rough preview drawn here, not what draw.io will draw. Needs Pillow only for --png.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ID = re.compile(r"^[a-z][a-z0-9_-]{0,39}$")
LEVELS = {"summary", "detailed"}
DIRECTIONS = {"LR", "TB"}
NODE_W, NODE_H, ICON = 140, 60, 60
GAP_MAIN, GAP_CROSS = 60, 30
PAD, HEADER, MARGIN = 20, 34, 30
MAX_SUMMARY_NODES = 15

NODE_KINDS = {  # kind: (style, fill colour for the preview)
    "service": ("rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;", "#ffe6cc"),
    "compute": ("rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;", "#dae8fc"),
    "database": ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#d5e8d4;strokeColor=#82b366;", "#d5e8d4"),
    "storage": ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=12;fillColor=#e1d5e7;strokeColor=#9673a6;", "#e1d5e7"),
    "network": ("rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;", "#f5f5f5"),
    "security": ("rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;", "#f8cecc"),
    "actor": ("ellipse;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;", "#fff2cc"),
    "external": ("rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#ffffff;strokeColor=#666666;", "#ffffff"),
}
GROUP_BASE = "rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=none;verticalAlign=top;align=left;spacingLeft=10;fontStyle=1;container=1;collapsible=0;recursiveResize=0;"
GROUP_KINDS = {  # kind: stroke colour
    "environment": "#666666",
    "cloud": "#ED7100",
    "network": "#248814",
    "onprem": "#7F7F7F",
}
ICON_STYLE = ("sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;"
              "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;aspect=fixed;"
              "shape=mxgraph.aws4.resourceIcon;resIcon={icon};")

DETAIL_PATTERNS = [  # not allowed at level "summary"
    ("an instance type", r"\b(?:db\.)?[a-z]\d[a-z]{0,2}\.(?:nano|micro|small|medium|large|\d*xlarge|metal)\b"),
    ("an IP address or network range", r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ("a resource count such as '2 x EC2'", r"\b\d+\s*x\s*(?:ec2|rds|instances?|servers?|nodes?|vms?)\b"),
    ("a cloud account number", r"(?<!\d)\d{12}(?!\d)"),
    ("network internals", r"\b(?:subnets?|availability zones?|security groups?|nacls?|route tables?)\b"),
]


# ---------- spec checking ----------

def check_spec(spec, allow_detail):
    problems = []
    if not isinstance(spec, dict):
        return ["the spec must be a JSON object"]
    for key in spec:
        if key not in {"title", "level", "direction", "groups", "nodes", "edges"}:
            problems.append(f"unknown key '{key}'")
    level = spec.get("level", "summary")
    if level not in LEVELS:
        problems.append(f"level must be one of {sorted(LEVELS)}")
    if spec.get("direction", "LR") not in DIRECTIONS:
        problems.append(f"direction must be one of {sorted(DIRECTIONS)}")
    groups, nodes, edges = spec.get("groups", []), spec.get("nodes", []), spec.get("edges", [])
    if not nodes:
        problems.append("the diagram needs at least one node")
    ids = {}
    for kind, items in (("group", groups), ("node", nodes)):
        for item in items:
            i = item.get("id", "")
            if not ID.match(str(i)):
                problems.append(f"{kind} id '{i}' must be lowercase letters, digits, - or _, starting with a letter")
            elif i in ids:
                problems.append(f"id '{i}' is used twice")
            ids[i] = kind
            label = item.get("label", "")
            if not isinstance(label, str) or not label.strip():
                problems.append(f"{kind} '{i}' needs a label")
            elif len(label) > 80:
                problems.append(f"{kind} '{i}': label is longer than 80 characters. Keep labels short.")
    for g in groups:
        if g.get("kind", "environment") not in GROUP_KINDS:
            problems.append(f"group '{g.get('id')}': kind must be one of {sorted(GROUP_KINDS)}")
        parent = g.get("parent")
        if parent is not None and ids.get(parent) != "group":
            problems.append(f"group '{g.get('id')}': parent '{parent}' is not a group")
    for g in groups:  # cycles
        seen, cur = set(), g.get("id")
        parents = {x.get("id"): x.get("parent") for x in groups}
        while cur is not None and cur in parents:
            if cur in seen:
                problems.append(f"group '{g.get('id')}' is inside itself")
                break
            seen.add(cur)
            cur = parents[cur]
    for n in nodes:
        if n.get("kind", "service") not in NODE_KINDS:
            problems.append(f"node '{n.get('id')}': kind must be one of {sorted(NODE_KINDS)}")
        grp = n.get("group")
        if grp is not None and ids.get(grp) != "group":
            problems.append(f"node '{n.get('id')}': group '{grp}' does not exist")
        icon = n.get("icon")
        if icon is not None and not str(icon).startswith("mxgraph."):
            problems.append(f"node '{n.get('id')}': icon must be a draw.io shape name such as mxgraph.aws4.ec2")
    for e in edges:
        for end in ("from", "to"):
            if e.get(end) not in ids:
                problems.append(f"edge {e.get('from')}->{e.get('to')}: '{e.get(end)}' does not exist")
        if e.get("from") == e.get("to"):
            problems.append(f"edge from '{e.get('from')}' to itself")
    if level == "summary" and not allow_detail:
        texts = [(f"node '{n.get('id')}'", n.get("label", "")) for n in nodes]
        texts += [(f"group '{g.get('id')}'", g.get("label", "")) for g in groups]
        texts += [(f"edge {e.get('from')}->{e.get('to')}", e.get("label", "")) for e in edges]
        for where, text in texts:
            for name, rx in DETAIL_PATTERNS:
                m = re.search(rx, str(text), re.IGNORECASE)
                if m:
                    problems.append(f"too much detail at summary level in {where}: {name} ('{m.group(0)}'). "
                                    f"Use business wording, or set level to detailed.")
        if len(nodes) > MAX_SUMMARY_NODES:
            problems.append(f"a summary diagram has {len(nodes)} nodes. Keep it to about {MAX_SUMMARY_NODES} "
                            f"or fewer, or use level detailed.")
    return problems


# ---------- layout ----------

def build_layout(spec):
    """Return {id: (x, y, w, h)} with x, y relative to the parent, plus parent map and order."""
    nodes = {n["id"]: n for n in spec["nodes"]}
    groups = {g["id"]: g for g in spec.get("groups", [])}
    tb = spec.get("direction", "LR") == "TB"
    parent = {i: n.get("group") for i, n in nodes.items()}
    parent.update({i: g.get("parent") for i, g in groups.items()})

    members = {None: []}
    members.update({g: [] for g in groups})
    for i in list(groups) + list(nodes):
        members[parent[i]].append(i)

    def member_of(i, container):
        """The direct member of `container` that holds item i, or None if i is not inside it."""
        cur = i
        while cur is not None:
            if parent.get(cur) == container:
                return cur
            cur = parent.get(cur)
        return None

    def level_ranks(container):
        """Rank the members of one container by the arrows between them (arrows are lifted to this level)."""
        kids = members[container]
        out = {k: [] for k in kids}
        for e in spec.get("edges", []):
            a, b = member_of(e["from"], container), member_of(e["to"], container)
            if a is not None and b is not None and a != b:
                out[a].append(b)
        state, forward = {}, []

        def visit(a):
            state[a] = 1
            for b in out[a]:
                if state.get(b) == 1:  # back edge: ignore, it would make a loop
                    continue
                forward.append((a, b))
                if b not in state:
                    visit(b)
            state[a] = 2

        for k in kids:
            if k not in state:
                visit(k)
        rank = {k: 0 for k in kids}
        for _ in range(len(kids)):
            for a, b in forward:
                if rank[b] < rank[a] + 1:
                    rank[b] = rank[a] + 1
        return rank

    geom, size = {}, {}

    def item_size(i):
        if i in size:
            return size[i]
        if i in nodes:
            size[i] = (ICON, ICON + 30) if nodes[i].get("icon") else (NODE_W, NODE_H)
        else:
            lay = arrange(i)
            size[i] = lay
        return size[i]

    def arrange(container):
        kids = members[container]
        ranks = level_ranks(container)
        cols = {}
        for k in kids:
            cols.setdefault(ranks[k], []).append(k)
        order = [cols[r] for r in sorted(cols)]
        # main axis = columns (LR) or rows (TB)
        dims = [[item_size(k) for k in col] for col in order]
        if tb:
            dims = [[(h, w) for (w, h) in col] for col in dims]
        col_main = [max((d[0] for d in col), default=0) for col in dims]
        col_cross = [sum(d[1] for d in col) + GAP_CROSS * (len(col) - 1) for col in dims]
        total_cross = max(col_cross, default=0)
        total_main = sum(col_main) + GAP_MAIN * (len(col_main) - 1)
        pad = 0 if container is None else PAD
        head = 0 if container is None else HEADER
        if container is None:
            main_pos = cross_start = MARGIN
        elif tb:  # the header sits at the top, which is the main axis in top-to-bottom layouts
            main_pos, cross_start = head + pad, pad
        else:
            main_pos, cross_start = pad, head + pad
        for ci, col in enumerate(order):
            cross = cross_start + (total_cross - col_cross[ci]) // 2
            for ki, k in enumerate(col):
                m, c = dims[ci][ki]
                x, y = (cross, main_pos) if tb else (main_pos, cross)
                w, h = (c, m) if tb else (m, c)
                geom[k] = (x, y, w, h)
                cross += c + GAP_CROSS
            main_pos += col_main[ci] + GAP_MAIN
        if tb:
            width, height = total_cross + 2 * pad, total_main + 2 * pad + head
        else:
            width, height = total_main + 2 * pad, total_cross + 2 * pad + head
        return (width, height)

    for i in list(nodes) + list(groups):
        item_size(i)
    arrange(None)  # top level: fills geom for top-level items (overwrites sizes with positions)
    # item_size recorded sizes; rebuild geometry with the final sizes for every item
    for i in geom:
        x, y, _, _ = geom[i]
        w, h = size[i]
        geom[i] = (x, y, w, h)
    return geom, parent


# ---------- output ----------

def label_html(text):
    return escape(text, {'"': "&quot;"}).replace("\n", "&lt;br&gt;")


def to_drawio(spec, geom, parent):
    nodes = {n["id"]: n for n in spec["nodes"]}
    groups = {g["id"]: g for g in spec.get("groups", [])}
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']

    def emit(i):
        x, y, w, h = geom[i]
        p = parent.get(i) or "1"
        if i in groups:
            g = groups[i]
            style = GROUP_BASE + f"strokeColor={GROUP_KINDS[g.get('kind', 'environment')]};"
            label = g["label"]
        else:
            n = nodes[i]
            if n.get("icon"):
                style = ICON_STYLE.format(icon=n["icon"])
            else:
                style = NODE_KINDS[n.get("kind", "service")][0]
            label = n["label"]
        cells.append(f'<mxCell id="{i}" value="{label_html(label)}" style="{style}" vertex="1" parent="{p}">'
                     f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def walk(container):  # parents before children
        for i in list(groups) + list(nodes):
            if (parent.get(i) or None) == container:
                emit(i)
                if i in groups:
                    walk(i)

    walk(None)
    for n, e in enumerate(spec.get("edges", []), 1):
        value = label_html(e.get("label", ""))
        cells.append(f'<mxCell id="edge{n}" value="{value}" '
                     'style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;" '
                     f'edge="1" parent="1" source="{e["from"]}" target="{e["to"]}">'
                     '<mxGeometry relative="1" as="geometry"/></mxCell>')
    name = escape(spec.get("title", "Diagram"), {'"': "&quot;"})
    body = "\n        ".join(cells)
    return (f'<mxfile host="app.diagrams.net">\n  <diagram id="diagram1" name="{name}">\n'
            '    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
            'arrows="1" fold="1" page="1" pageScale="1" pageWidth="1600" pageHeight="1000" math="0" shadow="0">\n'
            f'      <root>\n        {body}\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')


def absolute(geom, parent):
    result = {}

    def pos(i):
        if i in result:
            return result[i]
        x, y, w, h = geom[i]
        p = parent.get(i)
        if p:
            px, py, _, _ = pos(p)
            x, y = x + px, y + py
        result[i] = (x, y, w, h)
        return result[i]

    for i in geom:
        pos(i)
    return result


def draw_preview(spec, geom, parent, path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is not installed, so no preview image was made (pip install pillow).")
        return
    ab = absolute(geom, parent)
    nodes = {n["id"]: n for n in spec["nodes"]}
    groups = {g["id"]: g for g in spec.get("groups", [])}
    width = int(max(x + w for x, y, w, h in ab.values()) + MARGIN)
    height = int(max(y + h for x, y, w, h in ab.values()) + MARGIN)
    scale = 2
    img = Image.new("RGB", (width * scale, height * scale), "white")
    d = ImageDraw.Draw(img)
    font = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(f).exists():
            font = ImageFont.truetype(f, 12 * scale)
            bold = ImageFont.truetype(f.replace("Regular", "Bold").replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"), 12 * scale) \
                if Path(f.replace("Regular", "Bold").replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")).exists() else font
            break
    if font is None:
        font = bold = ImageFont.load_default()

    def rect(box, fill, outline, radius=8, dashed=False):
        x, y, w, h = [v * scale for v in box]
        d.rounded_rectangle([x, y, x + w, y + h], radius=radius * scale, fill=fill, outline=outline, width=2)

    def wrapped(text, maxw, fnt):
        lines, line = [], ""
        for word in text.replace("\n", " \n ").split(" "):
            if word == "\n":
                lines.append(line); line = ""; continue
            trial = (line + " " + word).strip()
            if d.textlength(trial, font=fnt) <= maxw * scale or not line:
                line = trial
            else:
                lines.append(line); line = word
        lines.append(line)
        return lines

    for gid, g in groups.items():
        rect(ab[gid], None, GROUP_KINDS[g.get("kind", "environment")])
    for gid, g in groups.items():
        x, y, w, h = ab[gid]
        d.text(((x + 10) * scale, (y + 8) * scale), g["label"], fill="#333333", font=bold)

    def anchor(src, dst):
        sx, sy, sw, sh = ab[src]
        tx, ty, tw, th = ab[dst]
        if tx >= sx + sw:
            return (sx + sw, sy + sh / 2), (tx, ty + th / 2)
        if tx + tw <= sx:
            return (sx, sy + sh / 2), (tx + tw, ty + th / 2)
        if ty >= sy + sh:
            return (sx + sw / 2, sy + sh), (tx + tw / 2, ty)
        return (sx + sw / 2, sy), (tx + tw / 2, ty + th)

    for e in spec.get("edges", []):
        (x1, y1), (x2, y2) = anchor(e["from"], e["to"])
        d.line([x1 * scale, y1 * scale, x2 * scale, y2 * scale], fill="#444444", width=2)
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        for da in (2.6, -2.6):
            d.line([x2 * scale, y2 * scale, (x2 + 10 * math.cos(ang + da)) * scale, (y2 + 10 * math.sin(ang + da)) * scale],
                   fill="#444444", width=2)
        if e.get("label"):
            d.text((((x1 + x2) / 2 + 4) * scale, ((y1 + y2) / 2 - 16) * scale), e["label"], fill="#444444", font=font)
    for nid, n in nodes.items():
        x, y, w, h = ab[nid]
        fill = NODE_KINDS[n.get("kind", "service")][1]
        box_h = h if not n.get("icon") else ICON
        rect((x, y, w, box_h), "#ED7100" if n.get("icon") else fill, "#555555")
        lines = wrapped(n["label"], w - 12, font)
        lh = 15 * scale
        if n.get("icon"):
            ty = (y + box_h + 4) * scale
        else:
            ty = (y + box_h / 2) * scale - lh * len(lines) / 2
        for k, line in enumerate(lines):
            tw = d.textlength(line, font=font)
            d.text(((x + w / 2) * scale - tw / 2, ty + k * lh), line, fill="#111111", font=font)
    img.save(path)


# ---------- commands ----------

def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"cannot read {path}: {exc}"]


def report(title, problems):
    print(f"{title}:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


def cmd_check(args):
    spec, problems = load(args.spec)
    problems = problems or check_spec(spec, args.allow_detail)
    if problems:
        return report("The diagram spec needs fixing", problems)
    print(f"OK: {len(spec['nodes'])} nodes, {len(spec.get('groups', []))} groups, "
          f"{len(spec.get('edges', []))} arrows, level {spec.get('level', 'summary')}")
    return 0


def cmd_build(args):
    spec, problems = load(args.spec)
    problems = problems or check_spec(spec, args.allow_detail)
    if problems:
        return report("The diagram spec needs fixing", problems)
    geom, parent = build_layout(spec)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_drawio(spec, geom, parent), encoding="utf-8")
    print(f"OK: wrote {out} (open it at app.diagrams.net or in the draw.io desktop app)")
    if args.png:
        draw_preview(spec, geom, parent, args.png)
        print(f"Preview (approximate, not how draw.io draws it): {args.png}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write a .drawio file from a spec")
    b.add_argument("spec"); b.add_argument("out")
    b.add_argument("--png", help="also write a rough preview image")
    b.add_argument("--allow-detail", action="store_true", help="skip the summary-level detail check")
    b.set_defaults(func=cmd_build)
    c = sub.add_parser("check", help="check a spec without writing anything")
    c.add_argument("spec")
    c.add_argument("--allow-detail", action="store_true")
    c.set_defaults(func=cmd_check)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
