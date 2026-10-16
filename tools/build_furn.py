"""The plans' furniture as vector linework: data/plan-furn.js (window.MX_FURN), from the 09.10 test-fit SVGs.

Replaces the 80 px/m furniture texture on the 2D plans (data/plan-textures.js stays for the 3D twin), so the
furniture stays sharp at any zoom and can be filled white over the floor colours. Same layers and clip as the
texture (tools/import_plan_hover.py raster_svg): everything but walls and text, clipped to the floor plate.
The CAD blocks stay blocks (<use>), so line widths come from --mpp (mm per screen px), which the plan sets on zoom.

usage: python tools/build_furn.py [data/src/plan-hover-data.js]
"""
import json, os, re, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.modules.setdefault("derive_layout", type(sys)("derive_layout"))   # only the frame helpers are needed (no scipy)
from import_plan_hover import FRAME, load, offset_convex, shell_outline, subpaths  # noqa: E402
from shapely.geometry import LineString, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.affinity import affine_transform  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
DROP = re.compile(r"^(s|f|m) wall$|^t$|^labels$")


def num(m):
    v = float(m.group(0))
    return str(round(v)) if abs(v) >= 100 else f"{v:.1f}".rstrip("0").rstrip(".")


def short(d):
    return re.sub(r"-?\d+\.\d+(?:e-?\d+)?", num, d)


FILL_MIN, FILL_MAX = 2e4, 16e6   # mm²: regions this size (a chair's seat to the boardroom table) are filled; rooms are not
GAP = 15                         # mm: drafting gaps up to twice this still close a region


def room_polys(key, dx, y0):
    """The CAD rooms (data/zones.json hover outlines), in the source drawing's frame (x' = x - dx, y' = y0 - y)."""
    zones = json.load(open(os.path.join(ROOT, "data", "zones.json"), encoding="utf-8"))
    out = []
    for r in zones[key]["hover"]["rooms"]:
        for q in subpaths(r["d"].replace("Z", "")):
            if len(q) >= 3:
                pg = Polygon([(x - dx, y0 - y) for x, y in q]).buffer(0)
                if pg.area > 0: out.append(pg)
    return out


def core_polys(key, dx, y0):
    """The building core (not in contract: its grey and hatch must show), in the source drawing's frame."""
    zones = json.load(open(os.path.join(ROOT, "data", "zones.json"), encoding="utf-8"))
    return [Polygon([(x - dx, y0 - y) for x, y in z["poly"]]).buffer(0) for z in zones[key]["zones"] if z["type"] == "core"]


CORE = []                                  # set per option in main()


def in_core(face):
    return any(c.intersects(face) and c.intersection(face).area > 0.5 * face.area for c in CORE)


def is_room(face, rooms):
    """A region that is essentially one of the rooms (its walls drawn in the furniture linework), not a piece."""
    for r in rooms:
        if r.intersects(face):
            inter = r.intersection(face).area
            if inter > 0.6 * face.area and inter > 0.45 * r.area:     # most of a room (a table is ~20-30% of one)
                return True
    return False


def faces(ds):
    """The regions enclosed by a group of furniture lines, as polygons (see regions)."""
    lines = []
    for d in ds:
        for q in subpaths(d):
            if len(q) >= 2:
                lines.append(LineString(q))
    if not lines:
        return []
    merged = unary_union([l.buffer(GAP, quad_segs=2) for l in lines])
    out = []
    for poly in getattr(merged, "geoms", [merged]):
        for ring in poly.interiors:
            face = Polygon(ring).buffer(GAP, quad_segs=2, join_style=2)
            if FILL_MIN < face.area < FILL_MAX:
                out.append(face)
    return out


def path_of(polys):
    return "".join("M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in list(f.exterior.coords)[:-1]) + "Z" for f in polys)


def regions(ds, rooms=()):
    """The regions enclosed by a group of furniture lines (each path's data in ds), as one path's data.
    The lines are thickened by GAP and merged, so pieces drawn as separate open strokes (a curved desk, a chair's
    seat and back) still enclose their area; each hole of the merge, grown back by GAP, is one region."""
    lines = []
    for d in ds:
        for q in subpaths(d):
            if len(q) >= 2:
                lines.append(LineString(q))
    if not lines:
        return ""
    merged = unary_union([l.buffer(GAP, quad_segs=2) for l in lines])
    out = []
    for poly in getattr(merged, "geoms", [merged]):
        for ring in poly.interiors:
            face = Polygon(ring).buffer(GAP, quad_segs=2, join_style=2)
            if FILL_MIN < face.area < FILL_MAX and not in_core(face) and not (rooms and face.area > 4e6 and is_room(face, rooms)):
                xy = list(face.exterior.coords)[:-1]
                out.append("M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in xy) + "Z")
    return "".join(out)


# paths sit in <use> shadow trees, where the page's CSS does not reach: they inherit fill/stroke from the plan's
# <use> (assets/css/app.css .furnv) and the few that differ carry an inline style, themed by custom properties
FILLED = ("s furn", "s shade", "s base")
PRE = {}                                   # block id -> its regions' path data, rooms already taken out   # the line classes whose enclosed regions are pieces of furniture
STYLE = {"k": "fill:var(--ff);stroke:none", "f": "fill:var(--fi);fill-opacity:.12;stroke:none", "m": "fill:var(--ff);stroke:none",
         "shade": "stroke-opacity:.45", "door": "stroke-opacity:.6", "glass": "stroke-opacity:.6", "green": "stroke:var(--fg)"}


def style(cls):
    c = cls.split()
    if c[0] == "m" and c[1:] != ["furn"]:          # wipeouts the drafter drew to hide hatching: floor, not a piece
        return ' style="fill:none;stroke:none"'
    st = STYLE.get(c[0]) if c[0] in ("f", "m", "k") else next((STYLE[x] for x in c[1:] if x in STYLE), None)
    return f' style="{st}"' if st else ""


def emit(el, key, out, fill=True, fill_core=True):
    tag = el.tag.replace(SVG, "")
    cls = el.get("class", "")
    if tag in ("text", "style", "defs") or DROP.match(cls):
        return
    if tag == "use":
        ref = (el.get("href") or el.get("{http://www.w3.org/1999/xlink}href") or "")[1:]
        # a scaled insert (e.g. a hatch drawn at ×213) carries --k: its lines are drawn 1/scale as wide
        k = re.search(r"--k:\s*([\d.e-]+)", el.get("style", ""))
        st = f' style="stroke-width:calc(var(--mpp, 20) * {float(k.group(1)):.6g} * .75px)"' if k else ""
        out.append(f'<use href="#fb-{key}-{ref}" transform="{el.get("transform", "")}"{st}/>')
    elif tag == "path":
        d = el.get("d", "")
        if cls.startswith("f "):
            # the CAD's solid fills: furniture-sized ones are pieces (white, like the rest), larger ones are floor finishes
            polys = [Polygon(q).buffer(0) for q in subpaths(d.replace("Z", "")) if len(q) >= 3]
            piece = polys and max(p.area for p in polys) < FILL_MAX and not (fill_core and any(in_core(p) for p in polys))
            out.append(f'<path{style("k") if piece else ' style="fill:none;stroke:none"'} d="{short(d)}"/>')
            return
        out.append(f'<path{style(cls)} d="{short(d)}"/>')
    elif tag == "g":
        inner = []
        if fill and el.get("id") in PRE:
            fd = PRE[el.get("id")]
            if fd:
                inner.append(f'<path{style("k")} d="{fd}"/>')
        elif fill:
            fd = regions([p.get("d", "") for p in el if p.tag == SVG + "path" and p.get("class", "") in FILLED])
            if fd:
                inner.append(f'<path{style("k")} d="{fd}"/>')
        for ch in el:
            emit(ch, key, inner, fill, fill_core)
        if inner or el.get("id"):
            attrs = "".join(f' {k}="{v}"' for k, v in (("id", el.get("id") and f"fb-{key}-{el.get('id')}"), ("transform", el.get("transform"))) if v)
            out.append(f"<g{attrs}>"); out.extend(inner); out.append("</g>")


def main():
    src = load(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "src", "plan-hover-data.js"))
    opt1 = json.load(open(os.path.join(ROOT, "data", "opt1.json"), encoding="utf-8"))
    outline = shell_outline(opt1)
    res = {}
    for key, (sk, dx, y0) in FRAME.items():
        H = json.load(open(os.path.join(ROOT, "data", f"{key}.json"), encoding="utf-8"))["size"][1]
        root = ET.fromstring(src["options"][sk]["svg"])
        defs, out = [], []
        # blocks inserted at a large scale are hatches and site symbols, not furniture: no fills there
        scaled = {u.get("href", "")[1:] for u in root.iter(SVG + "use")
                  if (m := re.search(r"--k:\s*([\d.e-]+)", u.get("style", ""))) and float(m.group(1)) < 0.67}
        # a block's regions, less any that is a room wherever the block is placed (a meeting room drawn as a block)
        rooms = room_polys(key, dx, y0)
        CORE[:] = core_polys(key, dx, y0)
        blocks = {g.get("id"): g for d in root.iter(SVG + "defs") for g in d}
        PRE.clear()
        bf = {i: faces([p.get("d", "") for p in g if p.tag == SVG + "path" and p.get("class", "") in FILLED])
              for i, g in blocks.items() if i not in scaled}
        drop = {i: set() for i in bf}
        for u in root.iter(SVG + "use"):
            i = (u.get("href") or "")[1:]
            m = re.match(r"matrix\(([^)]*)\)", u.get("transform", ""))
            if i not in bf or not m:
                continue
            a, b, c, d_, e, f = [float(v) for v in re.split(r"[ ,]+", m.group(1).strip())]
            for n, face in enumerate(bf[i]):
                g = affine_transform(face, [a, c, b, d_, e, f])
                if in_core(g) or (face.area * abs(a * d_ - b * c) > 4e6 and is_room(g, rooms)):
                    drop[i].add(n)
        for i, fs in bf.items():
            PRE[i] = path_of([fc for n, fc in enumerate(fs) if n not in drop[i]])
        for d in root.iter(SVG + "defs"):
            for g in d:
                emit(g, key, defs, g.get("id") not in scaled, False)   # (block coordinates: the core is tested where blocks sit)
        # the drawing's own linework (outside blocks): one piece is often split across groups (a curved desk row's arc
        # in one, its dividers in another), so its regions are found over all of it together, under everything
        loose = []
        def gather(el):
            for ch in el:
                t = ch.tag.replace(SVG, "")
                if t == "path" and ch.get("class", "") in FILLED: loose.append(ch.get("d", ""))
                elif t == "g" and not ch.get("transform"): gather(ch)
        gather(root)
        fd = regions(loose, rooms)
        if fd:
            out.append(f'<path{style("k")} d="{fd}"/>')
        for ch in root:
            emit(ch, key, out, False)
        clip = " ".join(f"{x:.0f},{H - y:.0f}" for x, y in offset_convex([tuple(p) for p in outline], 900))
        res[key] = dict(tr=f"translate({dx} {H - y0})", clip=clip, defs="".join(defs), body="".join(out))
        print(key, f"{(len(res[key]['defs']) + len(res[key]['body'])) / 1e6:.2f} MB")
    with open(os.path.join(ROOT, "data", "plan-furn.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* the plans' furniture as vector linework, from the 09.10 test fits: generated by tools/build_furn.py */\n")
        f.write("window.MX_FURN=" + json.dumps(res, separators=(",", ":")) + ";\n")


if __name__ == "__main__":
    main()
