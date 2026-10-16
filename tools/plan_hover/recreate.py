"""Recreate a DXF floor plan as SVG and measure how faithful the recreation is.

Writes two SVGs in the same millimetre frame so they overlay exactly:
  full.svg  - every visible primitive, true curves (SVG Bezier), 1 mm rounding,
              screen-constant line weights, wipeouts, hatches and text kept.
  acko.svg  - the Acko test-fit pipeline settings (20 mm flattening, short pieces
              dropped, Douglas-Peucker simplify, 50 mm grid, thick mm strokes).
and metrics.json comparing both against the source geometry.

usage: python recreate.py <in.dxf> <out_dir> [precision_mm=1]
"""
import sys, os, re, json, gzip, math, time, collections
import numpy as np
import ezdxf
import shapely
from ezdxf import path as zpath
from ezdxf.path import Command
from ezdxf.math import Vec3
from shapely.geometry import LineString

SRC, OUT = sys.argv[1], sys.argv[2]
PREC = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
os.makedirs(OUT, exist_ok=True)
t0 = time.time()

doc = ezdxf.readfile(SRC)
# a malformed SPLINE inside a block breaks path conversion; drop those
for blk in doc.blocks:
    for sp in [e for e in blk if e.dxftype() == "SPLINE"]:
        try:
            sp.construction_tool()
        except Exception:
            blk.delete_entity(sp)
VISIBLE = {l.dxf.name for l in doc.layers if l.is_on() and not l.is_frozen()}
FROZEN = {l.dxf.name for l in doc.layers if l.is_frozen()}
print(f"load {time.time() - t0:.1f}s")

# ---------- layer -> drawing category ----------
RULES = [
    ("anno", r"ANNO|TEXT|TAGS|DIM"),
    ("glass", r"GLS|GLAZ|GLASS|IN_GL"),
    ("door", r"DOOR|_DOR_|DOORWIN"),
    ("wall", r"WALL|PART|PRTN|GYP"),
    ("green", r"PLANT|LANDSCAPE|TREE"),
    ("shade", r"SHADE|ELEV|HATCH|MLWK"),
]
BASE = {"0", "1", "None", "WWW.DWGAUTOCAD.COM"}
_cat = {}
def cat(layer):
    if layer not in _cat:
        c = next((c for c, rx in RULES if re.search(rx, layer.upper())), None)
        _cat[layer] = c or ("base" if layer in BASE else "furn")
    return _cat[layer]

# ---------- explode blocks, resolving layer-0 inheritance and visibility ----------
def layer_of(e):
    return e.dxf.get("layer", "0") if e.dxf.is_supported("layer") else "0"

def walk(entities, parent="0"):
    for e in entities:
        lay = layer_of(e)
        eff = parent if lay == "0" else lay
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0):
            continue
        t = e.dxftype()
        if t == "INSERT":
            if eff in FROZEN:
                continue
            for a in e.attribs:
                if not a.dxf.get("invisible", 0) and not a.is_invisible:
                    yield a, eff
            subs = e.multi_insert() if e.mcount > 1 else [e]
            for ins in subs:
                try:
                    yield from walk(ins.virtual_entities(), eff)
                except Exception:
                    stats["err_insert"] += 1
        elif t in ("DIMENSION", "ARC_DIMENSION", "LEADER", "MLEADER"):
            try:
                yield from walk(e.virtual_entities(), eff)
            except Exception:
                stats["err_" + t] += 1
        else:
            yield e, eff

stats = collections.Counter()
items = []   # draw order: dict(kind, cat, layer, path, truth)
texts = []

def truth_pts(e, p):
    """Densely flattened source geometry, straight from the entity where possible."""
    t = e.dxftype()
    try:
        if t in ("ARC", "CIRCLE"):
            return [(v.x, v.y) for v in e.flattening(0.05)]
        if t in ("ELLIPSE", "SPLINE"):
            return [(v.x, v.y) for v in e.flattening(0.05)]
    except Exception:
        pass
    return [(v.x, v.y) for v in p.flattening(0.05)]

TEXT_T = ("TEXT", "ATTRIB", "MTEXT")
SKIP_T = ("POINT", "ARCALIGNEDTEXT", "VIEWPORT", "IMAGE", "OLE2FRAME", "3DSOLID", "REGION", "BODY", "MESH")

def to_items(e, eff, count=True):
    """Drawable items for one exploded, visible, non-text entity."""
    t = e.dxftype()
    c = cat(eff)
    tally = stats if count else collections.Counter()
    if t in SKIP_T:
        tally["skip_" + t] += 1
        return []
    out = []
    try:
        if t == "HATCH":
            if e.dxf.solid_fill:
                for p in zpath.from_hatch(e):
                    out.append(dict(kind="fill", cat=c, layer=eff, path=p, ent=e))
            else:
                from ezdxf.render import hatching
                for ln in hatching.hatch_entity(e):
                    p = zpath.Path(ln.start); p.line_to(ln.end)
                    out.append(dict(kind="hatch", cat=c, layer=eff, path=p, ent=None))
            return out
        p = zpath.make_path(e)
    except Exception:
        tally["nopath_" + t] += 1
        return []
    if len(p) == 0:
        tally["empty_" + t] += 1
        return []
    kind = "mask" if t == "WIPEOUT" else "fill" if t in ("SOLID", "TRACE", "3DFACE") else "stroke"
    return [dict(kind=kind, cat=c, layer=eff, path=p, ent=e)]

for e, eff in walk(doc.modelspace()):
    if eff not in VISIBLE:
        stats["hidden_layer"] += 1
        continue
    if e.dxftype() in TEXT_T:
        # partition-type tags ("P1" on every gypsum partition block) are construction notes, not plan labels
        if e.dxftype() == "ATTRIB" and (e.dxf.get("tag", "").upper() == "PARTITIONTYPE" or eff.upper() == "I-PART-TEXT"):
            stats["partition_tags_hidden"] += 1
            continue
        texts.append((e, eff))
        continue
    items.extend(to_items(e, eff))
print(f"explode {time.time() - t0:.1f}s  items={len(items)} texts={len(texts)}", dict(stats))

# ---------- frame: crop stray far-off objects ----------
def pbox(p):
    vs = list(p.control_vertices())
    xs = [v.x for v in vs]; ys = [v.y for v in vs]
    return min(xs), min(ys), max(xs), max(ys)
for it in items:
    it["bb"] = pbox(it["path"])
cx = np.array([(b[0] + b[2]) / 2 for b in (it["bb"] for it in items)])
cy = np.array([(b[1] + b[3]) / 2 for b in (it["bb"] for it in items)])
x0, x1 = np.percentile(cx, [0.2, 99.8]); y0, y1 = np.percentile(cy, [0.2, 99.8])
pad = 0.06 * max(x1 - x0, y1 - y0)
X0, X1, Y0, Y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
before = len(items)
items = [it for it in items if it["bb"][2] >= X0 and it["bb"][0] <= X1 and it["bb"][3] >= Y0 and it["bb"][1] <= Y1]
stats["cropped_outside"] = before - len(items)
OX, OY = math.floor(X0), math.ceil(Y1)      # svg origin: top-left, y down
W, H = math.ceil(X1 - X0), math.ceil(Y1 - Y0)

# ---------- full-fidelity SVG ----------
def q(v):
    return round(v / PREC) * PREC
def num(v):
    v = q(v)
    return str(int(v)) if float(v).is_integer() else f"{v:g}"
def pt(v):
    return f"{num(v.x - OX)} {num(OY - v.y)}"

def d_of(p):
    s = ["M" + pt(p.start)]
    for c in p.commands():
        if c.type == Command.LINE_TO:
            s.append("L" + pt(c.end))
        elif c.type == Command.CURVE4_TO:
            s.append("C" + pt(c.ctrl1) + " " + pt(c.ctrl2) + " " + pt(c.end))
        elif c.type == Command.CURVE3_TO:
            s.append("Q" + pt(c.ctrl) + " " + pt(c.end))
        elif c.type == Command.MOVE_TO:
            s.append("M" + pt(c.end))
    return "".join(s)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def text_svg(e, eff):
    t = e.dxftype()
    lines, h, rot = [], 0, 0
    anchor, base = "start", "alphabetic"
    if t == "MTEXT":
        lines = [l for l in e.plain_text().split("\n")]
        h = e.dxf.get("char_height", 250) or 250
        rot = e.get_rotation()
        ap = e.dxf.get("attachment_point", 1)
        anchor = ("start", "middle", "end")[(ap - 1) % 3]
        row = (ap - 1) // 3                     # 0 top, 1 middle, 2 bottom
        lh = h * 5 / 3 * (e.dxf.get("line_spacing_factor", 1) or 1)
        n = len(lines)
        ins = e.dxf.insert
        if row == 0:
            first = -h
        elif row == 1:
            first = (h + (n - 1) * lh) / 2 - h
        else:
            first = (n - 1) * lh
        offs = [first - i * lh for i in range(n)]   # baseline offsets along local y (up)
    else:
        txt = e.plain_text() if hasattr(e, "plain_text") else e.dxf.text
        lines = [txt]
        h = e.dxf.get("height", 250) or 250
        rot = e.dxf.get("rotation", 0) or 0
        ha, va = e.dxf.get("halign", 0), e.dxf.get("valign", 0)
        ins = e.dxf.align_point if (ha or va) and e.dxf.hasattr("align_point") and ha not in (3, 5) else e.dxf.insert
        anchor = {1: "middle", 2: "end", 4: "middle"}.get(ha, "start")
        offs = [{2: -h / 2, 3: -h}.get(va, 0) if ha != 4 else -h / 2]
    if not any(l.strip() for l in lines):
        return ""
    x, y = ins.x - OX, OY - ins.y
    fs = h / 0.716    # cap height -> em size (Arial)
    out = [f'<text class="t" x="{x:.0f}" y="{y:.0f}" font-size="{fs:.0f}" text-anchor="{anchor}"'
           + (f' transform="rotate({-rot:.2f} {x:.0f} {y:.0f})"' if abs(rot) > 0.01 else "") + ">"]
    for l, o in zip(lines, offs):
        out.append(f'<tspan x="{x:.0f}" y="{y - o:.0f}">{esc(l)}</tspan>')
    out.append("</text>")
    return "".join(out)

STYLE_FULL = """
.pf{background:var(--paper,#fbfaf7)}
.pf path{vector-effect:non-scaling-stroke;stroke-linecap:round;stroke-linejoin:round}
.s{fill:none}
.s.base{stroke:#2a2a2a;stroke-width:.9}.s.wall{stroke:#1a1a1a;stroke-width:1.4}
.s.glass{stroke:#3a7bbf;stroke-width:1}.s.door{stroke:#555;stroke-width:.7}
.s.furn{stroke:#5d5d5d;stroke-width:.6}.s.green{stroke:#4c8a46;stroke-width:.5}
.s.shade{stroke:#a3a3a3;stroke-width:.4}.s.anno{stroke:#444;stroke-width:.5}
.h{fill:none;stroke-width:.3}.h.green{stroke:#7fb07a}.h:not(.green){stroke:#c4c4c4}
.f{fill-rule:evenodd;stroke:none}.f.green{fill:#cfe3cb}.f.glass{fill:#d6e6f5}.f:not(.green):not(.glass){fill:#e8e6e1}
.m{fill:var(--paper,#fbfaf7);stroke:none}
.t{font-family:Arial,Helvetica,sans-serif;fill:#2b2b2b}
"""
CLS = {"stroke": "s", "fill": "f", "mask": "m", "hatch": "h"}

def write_full(path):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" class="pf" viewBox="0 0 {W} {H}" data-ox="{OX}" data-oy="{OY}">',
             f"<style>{STYLE_FULL}</style>"]
    run_key, run = None, []
    def flush():
        if run:
            kind, c = run_key
            parts.append(f'<path class="{CLS[kind]} {c}" d="{"".join(run)}"/>')
    for it in items:
        k = (it["kind"], it["cat"])
        if k != run_key:
            flush(); run_key, run = k, []
        run.append(d_of(it["path"]))
    flush()
    parts.append('<g class="labels">')
    for e, eff in texts:
        try:
            s = text_svg(e, eff)
        except Exception:
            stats["text_err"] += 1; s = ""
        if s:
            parts.append(s); stats["texts_drawn"] += 1
    parts.append("</g></svg>")
    data = "".join(parts).encode()
    open(path, "wb").write(data)
    return len(data), len(gzip.compress(data, 6))

full_size = write_full(os.path.join(OUT, "full.svg"))
print(f"full.svg {full_size[0]/1e6:.2f} MB ({full_size[1]/1e6:.2f} MB gz)  {time.time() - t0:.1f}s")

# ---------- Acko pipeline reproduction ----------
ACKO_SKIP = {'A-GENM','A-FLOR','A-FLOR-OTLN','A-FLOR-OVHD','A-DETL','A-DETL-GENF','A-DETL-THIN','OB-I-BLK-TAGS','Defpoints',
             'AI-ANNO-DIM','A-ANNO-NOTE','G-ANNO-TEXT','I-PART-TEXT','A-AREA-IDEN','A-DOOR-IDEN','A-GENM-IDEN','Q-SPCQ','None',
             'HATCH-PLINES','N-HATCH','Lag 1','OB-I-SHADE60','OB-I-SHADE40','OB-I-ELEV-1','OB-I-MLWK-HIDN','OB-I-MLWK-OVHD',
             'A-SYM-FURN','h','HATCH','pline','TEXT1','RAILING'}
ACKO_TOL = {"furn": 30, "green": 60, "part": 15}
GRID = 50.0
def acko_group(c):
    return "part" if c in ("wall", "glass", "base") else "green" if c == "green" else "furn"

def acko_line(p, g):
    """Returns grid-snapped polyline in mm, or (None, reason)."""
    P = [(round(v.x), round(v.y)) for v in p.flattening(distance=20)]
    if len(P) < 2:
        return None, "degenerate"
    xs = [a for a, _ in P]; ys = [b for _, b in P]
    ext = max(max(xs) - min(xs), max(ys) - min(ys))
    if g in ("furn", "green") and ext < 120:
        return None, "short<120mm"
    if ext > 150000:
        return None, "frame"
    if g == "part" and ext < 60:
        return None, "short<60mm"
    ls = LineString(P).simplify(ACKO_TOL[g])
    Q = []
    for x, y in ls.coords:
        gx = round((x - OX) / GRID) * GRID + OX
        gy = round((y - OY) / GRID) * GRID + OY
        if not Q or Q[-1] != (gx, gy):
            Q.append((gx, gy))
    if len(Q) < 2:
        return None, "collapsed_by_grid"
    return Q, None

# ---------- accuracy measurement ----------
def measure():
    full_pairs, acko_pairs, rows = [], [], []
    for it in items:
        if it["kind"] != "stroke":
            continue
        e, p = it["ent"], it["path"]
        try:
            T = truth_pts(e, p)
        except Exception:
            continue
        if len(T) < 2:
            continue
        truth = LineString(T)
        L = truth.length
        if L < 1e-6:
            continue
        # full: rebuild the path from rounded control points, exactly as written to the svg
        rv = lambda v: Vec3(q(v.x - OX) + OX, OY - q(OY - v.y), 0)
        qp = zpath.Path(rv(p.start))
        for c in p.commands():
            if c.type == Command.LINE_TO: qp.line_to(rv(c.end))
            elif c.type == Command.CURVE4_TO: qp.curve4_to(rv(c.end), rv(c.ctrl1), rv(c.ctrl2))
            elif c.type == Command.CURVE3_TO: qp.curve3_to(rv(c.end), rv(c.ctrl))
            elif c.type == Command.MOVE_TO: qp.move_to(rv(c.end))
        F = [(v.x, v.y) for v in qp.flattening(0.05)]
        g = acko_group(it["cat"])
        in_acko = it["layer"] not in ACKO_SKIP
        A, why = acko_line(p, g) if in_acko else (None, "layer_skipped")
        rows.append(dict(cat=it["cat"], layer=it["layer"], L=L, why=why, acko=A))
        full_pairs.append((truth, LineString(F) if len(F) > 1 else None))
        acko_pairs.append((truth, LineString(A) if A else None))
    def dev(pairs):
        tr = [a for a, b in pairs if b is not None]
        ot = [b for a, b in pairs if b is not None]
        return shapely.hausdorff_distance(np.array(tr), np.array(ot), densify=0.25)
    dfull = dev(full_pairs)
    keep = [i for i, (a, b) in enumerate(acko_pairs) if b is not None]
    dacko = dev(acko_pairs)
    return rows, dfull, dacko, keep

rows, dfull, dacko, keep = measure()
print(f"measured {len(rows)} strokes  {time.time() - t0:.1f}s")

def pct(a, ps=(50, 95, 99, 100)):
    return {f"p{p}": round(float(np.percentile(a, p)), 2) for p in ps} if len(a) else {}

L = np.array([r["L"] for r in rows])
dropped = collections.Counter()
dropped_len = collections.Counter()
for r in rows:
    if r["acko"] is None:
        dropped[r["why"]] += 1; dropped_len[r["why"]] += r["L"]
by_cat = {}
for c in sorted({r["cat"] for r in rows}):
    idx = [i for i, r in enumerate(rows) if r["cat"] == c]
    kidx = [i for i in idx if rows[i]["acko"] is not None]
    kpos = {i: n for n, i in enumerate(keep)}
    by_cat[c] = dict(
        strokes=len(idx), length_m=round(float(L[idx].sum()) / 1000, 1),
        full_dev_mm=pct(dfull[idx]),
        acko_kept_pct=round(100 * len(kidx) / len(idx), 1),
        acko_kept_length_pct=round(100 * float(L[kidx].sum()) / max(float(L[idx].sum()), 1e-9), 1),
        acko_dev_mm=pct(np.array([dacko[kpos[i]] for i in kidx])),
    )

# ---------- acko SVG (same frame, mm) ----------
STYLE_ACKO = """
.pa{background:var(--paper,#fbfaf7)}
.pa path{fill:none;stroke-linecap:round;stroke-linejoin:round}
.pa .part{stroke:#1d1d1d;stroke-width:180}.pa .furn{stroke:#6a6a6a;stroke-width:85}.pa .green{stroke:#4c8a46;stroke-width:85}
"""
groups = collections.defaultdict(list)
for r in rows:
    if r["acko"]:
        Q = r["acko"]
        groups[acko_group(r["cat"])].append("M" + "L".join(f"{x - OX:.0f} {OY - y:.0f}" for x, y in Q))
acko_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="pa" viewBox="0 0 {W} {H}"><style>{STYLE_ACKO}</style>'
            + "".join(f'<path class="{g}" d="{"".join(v)}"/>' for g, v in groups.items()) + "</svg>").encode()
open(os.path.join(OUT, "acko.svg"), "wb").write(acko_svg)
print(f"acko.svg  {time.time() - t0:.1f}s")

# ---------- instanced SVG: each block written once in <defs>, placed with <use>. Every shape is
#            written exactly as in full.svg; only repeated blocks are shared. ----------
from ezdxf import bbox as zbbox

def fnum(v, dec):
    s = f"{v:.{dec}f}".rstrip("0").rstrip(".") if dec else str(round(v))
    return "0" if s in ("-0", "") else s

def qd_of(p, dec, ox=0.0, oy=0.0):
    """SVG path data of p in (x - ox, oy - y), rounded to `dec` decimals."""
    pt = lambda v: f"{fnum(v.x - ox, dec)} {fnum(oy - v.y, dec)}"
    s = ["M" + pt(p.start)]
    for c in p.commands():
        if c.type == Command.LINE_TO: s.append("L" + pt(c.end))
        elif c.type == Command.CURVE4_TO: s.append("C" + pt(c.ctrl1) + " " + pt(c.ctrl2) + " " + pt(c.end))
        elif c.type == Command.CURVE3_TO: s.append("Q" + pt(c.ctrl) + " " + pt(c.end))
        elif c.type == Command.MOVE_TO: s.append("M" + pt(c.end))
    return "".join(s)

def quantized(p, dec):
    """The path as it is written: every control point rounded to `dec` decimals (for measuring)."""
    rv = lambda v: Vec3(round(v.x, dec), round(v.y, dec), 0)
    qp = zpath.Path(rv(p.start))
    for c in p.commands():
        if c.type == Command.LINE_TO: qp.line_to(rv(c.end))
        elif c.type == Command.CURVE4_TO: qp.curve4_to(rv(c.end), rv(c.ctrl1), rv(c.ctrl2))
        elif c.type == Command.CURVE3_TO: qp.curve3_to(rv(c.end), rv(c.ctrl))
        elif c.type == Command.MOVE_TO: qp.move_to(rv(c.end))
    return qp

def runs_of(its, dec, ox=0.0, oy=0.0):
    """Items in draw order -> [(kind, cat, d)], consecutive same-style items sharing one <path>."""
    runs = []
    for it in its:
        d = qd_of(it["path"], dec, ox, oy)
        k = (it["kind"], it["cat"])
        if runs and runs[-1][:2] == k:
            runs[-1] = (*k, runs[-1][2] + d)
        else:
            runs.append((*k, d))
    return runs

def runs_svg(runs):
    return "".join(f'<path class="{CLS[k]} {c}" d="{d}"/>' for k, c, d in runs)

def drawable(entities, parent):
    for e, eff in walk(entities, parent):
        if eff in VISIBLE and e.dxftype() not in TEXT_T:
            yield from to_items(e, eff, count=False)

def svg_matrix(ins):
    m = ins.matrix44()
    o = m.transform((0, 0, 0)); ux = m.transform((1, 0, 0)) - o; uy = m.transform((0, 1, 0)) - o
    # block-local (x, -y)  ->  svg (X - OX, OY - Y)
    return (ux.x, -ux.y, -uy.x, uy.y, o.x - OX, OY - o.y)

def inside_frame(e):
    try:
        b = zbbox.extents([e], fast=True)
        return b.has_data and b.extmax.x >= X0 and b.extmin.x <= X1 and b.extmax.y >= Y0 and b.extmin.y <= Y1
    except Exception:
        return True

syms = {}        # (block name, layer it inherits) -> dict(id, items, max_scale)
seq = []         # draw order: ("use", key, matrix) | ("loose", items)
loose, placement_err, worst_place = [], [], []
def flush_loose():
    if loose:
        seq.append(("loose", loose[:])); loose.clear()

WRAPPER_MIN_INSERTS = 20
def is_wrapper(ins):
    """A block that holds the whole plan (furniture, rooms, shell all nested in it) rather than one object."""
    blk = doc.blocks.get(ins.dxf.name)
    return blk is not None and sum(1 for x in blk if x.dxftype() == "INSERT") >= WRAPPER_MIN_INSERTS

def top_level(entities, parent="0"):
    """Model space entities with their effective layer, looking through wrapper blocks so that the
    chairs, desks and plants inside them are what gets instanced."""
    for e in entities:
        lay = layer_of(e)
        eff = parent if lay == "0" else lay
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0):
            continue
        if e.dxftype() == "INSERT" and eff not in FROZEN and e.mcount <= 1 and is_wrapper(e):
            cstats["wrappers_opened"] += 1
            yield from top_level(e.virtual_entities(), eff)
        else:
            yield e, eff

cstats = collections.Counter()
for e, lay in top_level(doc.modelspace()):
    if e.dxftype() != "INSERT":
        for it in drawable([e], lay):
            b = pbox(it["path"])
            if b[2] >= X0 and b[0] <= X1 and b[3] >= Y0 and b[1] <= Y1:
                loose.append(it)
        continue
    if lay in FROZEN or not inside_frame(e):
        continue
    for ins in (e.multi_insert() if e.mcount > 1 else [e]):
        key = (ins.dxf.name, lay)
        if key not in syms:
            syms[key] = dict(id=f"b{len(syms)}", items=list(drawable(doc.blocks.get(ins.dxf.name), lay)), max_scale=0)
        s = syms[key]
        if not s["items"]:
            continue
        flush_loose()
        mtx = svg_matrix(ins)
        s["max_scale"] = max(s["max_scale"], math.sqrt(abs(mtx[0] * mtx[3] - mtx[1] * mtx[2])))
        seq.append(("use", key, mtx))
        # placement check: the block's first shape placed by the <use> matrix vs. the exploded original
        world = next(drawable(ins.virtual_entities(), lay), None)
        if world is not None:
            a, b, c, d, ee, f = mtx
            k = math.sqrt(abs(a * d - b * c)) or 1      # flatten finely enough in local units for this scale
            placed = [(a * v.x + c * -v.y + ee, b * v.x + d * -v.y + f) for v in s["items"][0]["path"].flattening(0.2 / max(k, 1))]
            orig = [(v.x - OX, OY - v.y) for v in world["path"].flattening(0.2)]
            placed, orig = placed * (2 if len(placed) == 1 else 1), orig * (2 if len(orig) == 1 else 1)
            placement_err.append(float(shapely.hausdorff_distance(LineString(placed), LineString(orig), densify=0.25)))
            if placement_err[-1] > 1:
                worst_place.append((round(placement_err[-1], 1), ins.dxf.name))
flush_loose()

# a block placed at scale k turns 1 local unit into k mm, so round its local coordinates finely enough
# that the error on the plan stays at the full.svg level (<= PREC)
for s in syms.values():
    s["dec"] = max(0, math.ceil(math.log10(s["max_scale"] / PREC))) if s["max_scale"] > PREC else 0

# accuracy: every stroke as written (rounded) vs. its exact geometry, scaled to plan mm
inst_dev = []
def measure_items(its, dec, scale):
    exact, written = [], []
    for it in its:
        if it["kind"] != "stroke":
            continue
        A = [(v.x, v.y) for v in it["path"].flattening(0.05)]
        B = [(v.x, v.y) for v in quantized(it["path"], dec).flattening(0.05)]
        if len(A) > 1 and len(B) > 1:
            exact.append(LineString(A)); written.append(LineString(B))
    if exact:
        inst_dev.extend((shapely.hausdorff_distance(np.array(exact), np.array(written), densify=0.25) * scale).tolist())
used = {k for kind, k, *_ in seq if kind == "use"}
n_uses = sum(1 for kind, *_ in seq if kind == "use")
for k in used:
    measure_items(syms[k]["items"], syms[k]["dec"], syms[k]["max_scale"])
n_loose = 0
for kind, *rest in seq:
    if kind == "loose":
        measure_items(rest[0], 0, 1.0); n_loose += len(rest[0])

def instanced_style():
    """STYLE_FULL scoped to .pc for viewing the file on its own. Browsers ignore
    vector-effect:non-scaling-stroke inside <use>, so here line weights come from --mpp (plan mm per
    screen px) and --k (1 / the <use> scale). The viewer instead expands each <use> into a plain copy
    and uses full.svg's styles, which is faster and exact."""
    css = STYLE_FULL.replace("vector-effect:non-scaling-stroke;", "")
    css = re.sub(r"stroke-width:([\d.]+)",
                 lambda m: f"stroke-width:calc({m.group(1)}px * var(--mpp, 20) * var(--k, 1))", css)
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        sels = [s.strip() for s in sel.split(",")]
        out.append(",".join(".pc" + s[3:] if s.startswith(".pf") else ".pc " + s for s in sels) + "{" + body + "}")
    return "".join(out)

fmtm = lambda v: f"{v:.6f}".rstrip("0").rstrip(".") if abs(v) < 100 else f"{v:.1f}"
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" class="pc" viewBox="0 0 {W} {H}">'
         f"<style>{instanced_style()}</style><defs>"]
for k in sorted(used, key=lambda k: int(syms[k]["id"][1:])):
    s = syms[k]
    parts.append(f'<g id="{s["id"]}">{runs_svg(runs_of(s["items"], s["dec"]))}</g>')
parts.append("</defs>")
for kind, *rest in seq:
    if kind == "use":
        key, mtx = rest
        scale = math.sqrt(abs(mtx[0] * mtx[3] - mtx[1] * mtx[2])) or 1
        kk = f' style="--k:{1 / scale:.5g}"' if abs(scale - 1) > 1e-3 else ""
        parts.append(f'<use href="#{syms[key]["id"]}" transform="matrix({" ".join(fmtm(v) for v in mtx)})"{kk}/>')
    else:
        # loose geometry goes straight into plan coordinates, exactly as in full.svg
        parts.append(f"<g>{runs_svg(runs_of(rest[0], 0, OX, OY))}</g>")
parts.append('<g class="labels">')
for e, eff in texts:
    try:
        parts.append(text_svg(e, eff))
    except Exception:
        pass
parts.append("</g></svg>")
inst_svg = "".join(parts).encode()
open(os.path.join(OUT, "instanced.svg"), "wb").write(inst_svg)
print(f"instanced.svg {len(inst_svg)/1e6:.2f} MB  blocks={len(used)} uses={n_uses} loose={n_loose} wrappers_opened={cstats['wrappers_opened']}  {time.time() - t0:.1f}s")

metrics = dict(
    source=os.path.basename(SRC), precision_mm=PREC, frame_mm=[W, H],
    counts=dict(items=len(items), strokes_measured=len(rows), texts=len(texts),
                **{k: v for k, v in stats.items()}),
    full=dict(size_mb=round(full_size[0] / 1e6, 2), gzip_mb=round(full_size[1] / 1e6, 2),
              kept_pct=100.0, dev_mm=pct(dfull)),
    acko=dict(size_mb=round(len(acko_svg) / 1e6, 2), gzip_mb=round(len(gzip.compress(acko_svg, 6)) / 1e6, 2),
              kept_pct=round(100 * len(keep) / len(rows), 1),
              kept_length_pct=round(100 * float(L[keep].sum()) / float(L.sum()), 1),
              dropped={k: dict(n=n, length_m=round(dropped_len[k] / 1000, 1)) for k, n in dropped.most_common()},
              dev_mm=pct(dacko)),
    instanced=dict(size_mb=round(len(inst_svg) / 1e6, 2), gzip_mb=round(len(gzip.compress(inst_svg, 6)) / 1e6, 2),
                   kept_pct=100.0, symbols=len(used), uses=n_uses, loose_items=n_loose,
                   wrapper_blocks_opened=cstats["wrappers_opened"],
                   dev_mm=pct(np.array(inst_dev)),
                   placement_err_mm=pct(np.array(placement_err)) if placement_err else {},
                   worst_placement=sorted(worst_place, reverse=True)[:8]),
    by_category=by_cat,
    seconds=round(time.time() - t0, 1),
)
json.dump(metrics, open(os.path.join(OUT, "metrics.json"), "w"), indent=1)
print(json.dumps(metrics, indent=1))
