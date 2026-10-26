"""The layout DXF as vector data, block by block, for the plan viewer (tools/acko/plan_view.html) and later the deck.

The drawing keeps the plan as blocks stacked at one point in model space (the base plan first; outlines, fills,
labels and the rest later). Each block placed in model space becomes its own file, never merged with the others.

Instanced (the default), as Mitigata's instanced.svg: every block definition the file uses is written once, in its own
coordinates, and every placement of it is a reference with its 2D transform. Inside a definition everything AutoCAD
draws is kept in AutoCAD's draw order, as runs of consecutive items sharing a layer, colour, linetype, lineweight and kind:
  s  strokes     lines, arcs, circles, ellipses, splines, polylines (curves flattened to 4 mm)
  f  fills       solid hatches (even-odd over their loops; stale text-box loops dropped), SOLID / TRACE / 3DFACE
  m  wipeouts    painted in the background colour, hiding what was drawn before them
  h  patterns    pattern hatches as their pattern lines, clipped to the hatch's own boundary
  t  text        TEXT / MTEXT / ATTRIB: the words, height, rotation, alignment, width factor, style
  i  inserts     placements of another definition: [definition, a, b, c, d, e, f] (x' = a x + c y + e, y' = b x + d y + f)
A run's layer, colour, linetype and lineweight may inherit, resolved per placement as AutoCAD does:
  layer ""      layer 0: the placement's layer
  colour "L"    BYLAYER on layer 0: the colour of the placement's layer;  "B" BYBLOCK: the placement's colour
  linetype "L" / "B", lineweight -1 / -2: the same
Visibility as AutoCAD: entities on layers that are off or frozen are dropped; layer-0 content follows its placement's
layer; placements on frozen layers are dropped; invisible entities and attributes are dropped.
Coordinates are integers, each run of points as its first point then deltas, in units of 10^-q of the definition's
own units, q chosen per definition so the rounding stays under 0.5 mm on the plan however it's scaled.

--flat writes the previous form instead: every placement exploded into world coordinates (integer mm), as the check.

Writes into <out_dir>:
  layers.json            the blocks (draw order), the frame, every layer (colour, linetype, lineweight, on), linetypes,
                         styles, and a check: every entity type, how many were drawn (in definitions and as placed)
  layers/<block>.json    instanced: {"block", "root", "place", "defs": [{"name", "q", "runs"}]}; flat: {"block", "runs"}

usage: python tools/acko/plan_vector.py <layout.dxf> <out_dir> [--flat]
"""
import sys, os, re, json, math, time, collections
import ezdxf
from ezdxf import path as zpath, colors as zcolors
from ezdxf.render import hatching
from shapely.geometry import Polygon, LineString
from shapely.prepared import prep

SRC, OUT = sys.argv[1], sys.argv[2]
FLAT = "--flat" in sys.argv[3:]
t0 = time.time()
doc = ezdxf.readfile(SRC)
print(f"load {time.time() - t0:.0f}s", flush=True)
msp = doc.modelspace()

LAYERS = {l.dxf.name: l for l in doc.layers}
OFF = {n for n, l in LAYERS.items() if not l.is_on()}
FROZEN = {n for n, l in LAYERS.items() if l.is_frozen()}
LTSCALE = doc.header.get("$LTSCALE", 1.0) or 1.0

def layer_rgb(name):
    l = LAYERS.get(name)
    if l is None: return (0, 0, 0)
    if l.rgb: return l.rgb
    return zcolors.aci2rgb(abs(l.dxf.color) or 7)
def layer_lt(name): return LAYERS[name].dxf.get("linetype", "Continuous") if name in LAYERS else "Continuous"
def layer_lw(name): return LAYERS[name].dxf.get("lineweight", -3) if name in LAYERS else -3

def hexc(rgb):
    rgb = tuple(rgb)
    return "#000000" if rgb == (255, 255, 255) else "#%02x%02x%02x" % rgb     # white draws black on a white page

stats = collections.Counter()
seen = collections.Counter()
drawn = collections.Counter()
failed = collections.defaultdict(list)
ltypes_used, styles_used = set(), collections.Counter()

def enc(pts, q=0):
    """integers in 10^-q units, first point then deltas: [x0, y0, dx1, dy1, ...]"""
    k = 10 ** q
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(pts):
        x, y = round(x * k), round(y * k)
        if i and x == px and y == py: continue
        out += [x, y] if not i else [x - px, y - py]
        px, py = x, y
    return out

class Runs:
    def __init__(self):
        self.runs, self.key = [], None
    def add(self, key, item):
        if key != self.key:
            self.runs.append([*key, []]); self.key = key
        self.runs[-1][-1].append(item)

# ---------------------------------------------------------------- text
PARA = re.compile(r"\\pxq([lrcjd])", re.I)                # MTEXT paragraph alignment
FONT = re.compile(r"\\f([^|;\\]+)", re.I)                   # inline TrueType font
HEIGHT = re.compile(r"\\H(\d+(?:\.\d+)?)(x?);")             # inline height, absolute or relative (x)

def text_rec(e, t, q=0):
    """[x, y, cap height, rotation, align, row, words, style, width factor, line spacing, font]
    (x, y) is where the text's anchor lands, already moved inside an MTEXT box; align is the canvas textAlign
    (left / center / right); row says what y is: 0 the top of the first line's capitals, 1 the middle of the block,
    2 the baseline of the last line, 3 a TEXT's baseline"""
    font = ""
    if t == "MTEXT":
        raw = e.text
        words = e.plain_text()
        h = e.dxf.get("char_height", 0) or 0
        m = HEIGHT.search(raw)
        if m: h = h * float(m.group(1)) if m.group(2) else float(m.group(1))
        rot = e.get_rotation(); wf = 1
        ap = e.dxf.get("attachment_point", 1)
        col, row = (ap - 1) % 3, (ap - 1) // 3
        ls = e.dxf.get("line_spacing_factor", 1) or 1
        width = e.dxf.get("width", 0) or 0
        m = PARA.search(raw)
        para = {"l": 0, "c": 1, "r": 2}.get(m.group(1).lower(), col) if m else col
        m = FONT.search(raw)
        if m: font = m.group(1).strip()
        x, y = e.dxf.insert.x, e.dxf.insert.y
        if width > 0 and para != col:
            # the attachment places the box (its left, middle or right edge on the insertion point); the paragraph
            # alignment then places the words inside the box
            d = width * (para - col) / 2
            a = math.radians(rot)
            x, y = x + d * math.cos(a), y + d * math.sin(a)
        align = ("left", "center", "right")[para]
    else:
        words = e.plain_text() if hasattr(e, "plain_text") else e.dxf.text
        h = e.dxf.get("height", 0) or 0
        rot = e.dxf.get("rotation", 0) or 0
        ha, va = e.dxf.get("halign", 0), e.dxf.get("valign", 0)
        p = e.dxf.align_point if (ha or va) and ha not in (3, 5) and e.dxf.hasattr("align_point") else e.dxf.insert
        x, y = p.x, p.y
        if ha == 4: align, row = "center", 1                                  # "middle": centred both ways
        else:
            align = {1: "center", 2: "right"}.get(ha, "left")                 # 3 aligned, 5 fit: from the insert, left
            row = {3: 0, 2: 1, 1: 2, 0: 3}[va]                                # 1 "bottom" sits close to the baseline
        wf = e.dxf.get("width", 1) or 1; ls = 1
        if e.dxf.hasattr("extrusion") and e.dxf.extrusion.z < 0: stats["text_mirrored"] += 1
    style = e.dxf.get("style", "Standard")
    styles_used[style] += 1
    k = 10 ** q
    return [round(x * k), round(y * k), round(h, 2), round(rot, 2), align, row, words, style, round(wf, 2), round(ls, 2), font]

# ---------------------------------------------------------------- one primitive's geometry
def geometry(e, t, add, q=0):
    """what AutoCAD draws for one primitive: add(kind, item); returns False if it isn't drawn"""
    if t == "LINE":
        a, b = e.dxf.start, e.dxf.end
        add("s", enc([(a.x, a.y), (b.x, b.y)], q))
    elif t in ("LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE"):
        p = zpath.make_path(e)
        if not len(p): stats["empty_" + t] += 1; return False
        tol = 4 / 10 ** q if q else 4
        for sp in p.sub_paths():
            add("s", enc([(v.x, v.y) for v in sp.flattening(tol)], q))
    elif t == "HATCH":
        keep = [bp for bp in e.paths if not bp.path_type_flags & 8]   # text-box loops: AutoCAD doesn't draw them
        if len(keep) != len(e.paths): stats["hatch_textbox_loops_dropped"] += len(e.paths) - len(keep); e.paths.paths = keep
        tol = 4 / 10 ** q if q else 4
        if e.dxf.solid_fill:
            loops = [enc([(v.x, v.y) for v in p.flattening(tol)], q) for p in zpath.from_hatch(e)]
            loops = [l for l in loops if len(l) >= 6]
            if not loops: failed[t].append("solid hatch without loops"); return False
            add("f", loops)
        else:
            # ezdxf can return part of a pattern mirrored across the origin (extrusion 0, 0, -1), so every line is
            # clipped to the hatch's own boundary (even-odd over its loops)
            area = None
            for p in zpath.from_hatch(e):
                pg = Polygon([(v.x, v.y) for v in p.flattening(tol)]).buffer(0)
                area = pg if area is None else area.symmetric_difference(pg)
            n = 0
            if area is not None and not area.is_empty:
                pa = prep(area)
                for ln in hatching.hatch_entity(e):
                    a, b = (ln.start, ln.end) if hasattr(ln, "start") else ln
                    seg = LineString([(a.x, a.y), (b.x, b.y)])
                    if pa.contains(seg): add("h", enc(seg.coords, q)); n += 1; continue
                    if not pa.intersects(seg): stats["pattern_lines_outside"] += 1; continue
                    cut = area.intersection(seg)
                    for g in getattr(cut, "geoms", [cut]):
                        if g.geom_type == "LineString" and g.length > 1 / 10 ** q: add("h", enc(g.coords, q)); n += 1
            if not n: stats["pattern_hatch_without_lines"] += 1
    elif t in ("SOLID", "TRACE", "3DFACE"):
        v = [(p.x, p.y) for p in e.wcs_vertices()]
        if t != "3DFACE" and len(v) == 4: v = [v[0], v[1], v[3], v[2]]     # SOLID's vertex order is a zig-zag
        add("f", [enc(v, q)])
    elif t == "WIPEOUT":
        add("m", enc([(p.x, p.y) for p in e.boundary_path_wcs()], q))
    elif t in ("TEXT", "MTEXT", "ATTRIB"):
        r = text_rec(e, t, q)
        if not str(r[6]).strip(): stats["text_empty"] += 1; return False
        add("t", r)
    elif t in ("POINT", "ATTDEF", "VIEWPORT"):
        stats["not_drawn_" + t] += 1; return False      # AutoCAD doesn't plot these in a plan (PDMODE 0)
    elif t == "REGION":
        stats["not_drawn_REGION"] += 1; return False
    else:
        failed[t].append("type not handled"); return False
    return True

def styled_kind(kind): return kind in ("s", "h")
DIMS = ("DIMENSION", "ARC_DIMENSION", "LARGE_RADIAL_DIMENSION", "LEADER", "MLEADER", "MULTILEADER", "ACAD_TABLE")

# ================================================================ flat: every placement exploded into world mm
def colour_of(e, eff, parent):
    if e.dxf.hasattr("true_color"): return zcolors.int2rgb(e.dxf.true_color)
    c = e.dxf.get("color", 256)
    if c == 256: return layer_rgb(eff)
    if c == 0: return parent["rgb"] if parent else layer_rgb(eff)
    return zcolors.aci2rgb(c)
def ltype_of(e, eff, parent):
    lt = e.dxf.get("linetype", "BYLAYER") or "BYLAYER"
    if lt.upper() == "BYLAYER": return layer_lt(eff)
    if lt.upper() == "BYBLOCK": return parent["lt"] if parent else "Continuous"
    return lt
def lweight_of(e, eff, parent):
    w = e.dxf.get("lineweight", -1)
    if w == -1: w = layer_lw(eff)
    elif w == -2: w = parent["lw"] if parent else -3
    return w if w >= 0 else -3

def flat_draw(e, eff, parent, R):
    t = e.dxftype(); seen[t] += 1
    if eff in OFF or eff in FROZEN: stats["skipped_layer_off"] += 1; return
    rgb, lt, lw = colour_of(e, eff, parent), ltype_of(e, eff, parent), lweight_of(e, eff, parent)
    def add(kind, item):
        R.add((eff, hexc(rgb), lt if kind == "s" else "", lw if styled_kind(kind) else 0, kind), item)
    try:
        if geometry(e, t, add): drawn[t] += 1; ltypes_used.add(lt)
    except Exception as ex:
        failed[t].append(f"{type(ex).__name__}: {ex}"[:120])

def flat_walk(entities, R, parent=None, parent_layer="0"):
    for e in entities:
        lay = e.dxf.get("layer", "0") if e.dxf.is_supported("layer") else "0"
        eff = parent_layer if lay == "0" else lay
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0): stats["invisible"] += 1; continue
        t = e.dxftype()
        if t == "INSERT":
            if eff in FROZEN: stats["insert_frozen"] += 1; continue
            me = {"rgb": colour_of(e, eff, parent), "lt": ltype_of(e, eff, parent), "lw": lweight_of(e, eff, parent)}
            for a in e.attribs:
                if a.is_invisible: stats["attrib_invisible"] += 1; continue
                flat_draw(a, a.dxf.layer if a.dxf.layer != "0" else eff, me, R)
            try:
                for ins in (e.multi_insert() if e.mcount > 1 else [e]):
                    flat_walk(ins.virtual_entities(), R, me, eff)
            except Exception as ex:
                failed["INSERT"].append(f"{e.dxf.name}: {ex}"[:120])
        elif t in DIMS:
            if eff in OFF or eff in FROZEN: stats["skipped_layer_off"] += 1; continue
            try: flat_walk(e.virtual_entities(), R, parent, eff)
            except Exception as ex: failed[t].append(str(ex)[:120])
        else:
            flat_draw(e, eff, parent, R)

# ================================================================ instanced: each definition once, placements by reference
def spec(e, lay):
    """a run's (layer, colour, linetype, lineweight) as stored: resolved now where the entity's own layer decides,
    left to inherit ("" / "L" / "B" / -1 / -2) where its placement decides"""
    own = lay != "0"
    if e.dxf.hasattr("true_color"): col = hexc(zcolors.int2rgb(e.dxf.true_color))
    else:
        c = e.dxf.get("color", 256)
        col = (hexc(layer_rgb(lay)) if own else "L") if c == 256 else "B" if c == 0 else hexc(zcolors.aci2rgb(c))
    lt = e.dxf.get("linetype", "BYLAYER") or "BYLAYER"
    lt = (layer_lt(lay) if own else "L") if lt.upper() == "BYLAYER" else "B" if lt.upper() == "BYBLOCK" else lt
    lw = e.dxf.get("lineweight", -1)
    lw = (layer_lw(lay) if own else -1) if lw == -1 else lw
    if lt not in ("L", "B"): ltypes_used.add(lt)
    return (lay if own else "", col, lt, lw if lw >= -2 else -3)

def affine(m):
    """ezdxf Matrix44 (row vectors) -> canvas setTransform order a, b, c, d, e, f"""
    return [round(m[0, 0], 9), round(m[0, 1], 9), round(m[1, 0], 9), round(m[1, 1], 9), round(m[3, 0], 4), round(m[3, 1], 4)]

DEFS, INDEX, MAXSCALE, USES = [], {}, collections.defaultdict(float), collections.Counter()

def scales(name, k, mult=1):
    """the largest scale each definition is drawn at, and how many times it's placed"""
    MAXSCALE[name] = max(MAXSCALE[name], k); USES[name] += mult
    blk = doc.blocks.get(name)
    if blk is None: return
    kids = collections.Counter()
    for e in blk:
        if e.dxftype() == "INSERT" and not e.dxf.get("invisible", 0):
            kids[(e.dxf.name, max(abs(e.dxf.xscale), abs(e.dxf.yscale)) * max(1, e.mcount))] += 1
    for (child, s), n in kids.items(): scales(child, k * s, mult * n)

def define(name):
    if name in INDEX: return INDEX[name]
    blk = doc.blocks.get(name)
    idx = INDEX[name] = len(DEFS)
    d = {"name": name, "q": max(0, math.ceil(math.log10(max(MAXSCALE[name], 1e-9)))), "runs": None}
    DEFS.append(d)
    R = Runs(); q = d["q"]
    if blk is None: failed["INSERT"].append(f"block {name} missing"); d["runs"] = []; return idx

    def put(e, lay, t):
        seen[t] += 1
        if lay in OFF or lay in FROZEN: stats["skipped_layer_off"] += 1; return
        sp = spec(e, lay)
        def add(kind, item):
            R.add((sp[0], sp[1], sp[2] if kind == "s" else "", sp[3] if styled_kind(kind) else 0, kind), item)
        try:
            if geometry(e, t, add, q): drawn[t] += 1
        except Exception as ex:
            failed[t].append(f"{type(ex).__name__}: {ex}"[:120])

    for e in blk:
        t = e.dxftype()
        lay = e.dxf.get("layer", "0") if e.dxf.is_supported("layer") else "0"
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0): stats["invisible"] += 1; continue
        if t == "INSERT":
            if lay in FROZEN: stats["insert_frozen"] += 1; continue
            sp = spec(e, lay)
            for a in e.attribs:              # attributes live in this definition's coordinates
                if a.is_invisible: stats["attrib_invisible"] += 1; continue
                put(a, a.dxf.layer if a.dxf.layer != "0" else lay, "ATTRIB")
            child = define(e.dxf.name)
            try:
                for ins in (e.multi_insert() if e.mcount > 1 else [e]):
                    R.add((sp[0], sp[1], sp[2], sp[3], "i"), [child, *affine(ins.matrix44())])
            except Exception as ex:
                failed["INSERT"].append(f"{e.dxf.name}: {ex}"[:120])
        elif t in DIMS:
            if lay in OFF or lay in FROZEN: stats["skipped_layer_off"] += 1; continue
            try:
                for v in e.virtual_entities():
                    vl = v.dxf.get("layer", "0")
                    put(v, lay if vl == "0" else vl, v.dxftype())
            except Exception as ex: failed[t].append(str(ex)[:120])
        else:
            put(e, lay, t)
    d["runs"] = R.runs
    return idx

def merge_duplicates(root):
    """dynamic blocks leave identical anonymous copies (*U...): definitions with the same content are kept once"""
    import hashlib
    ident = [None] * len(DEFS)
    for _ in range(12):                       # a definition's identity includes its children's, so iterate to a fixed point
        new = []
        for d in DEFS:
            runs = [r[:5] + [[[ident[it[0]] or it[0], *it[1:]] for it in r[5]]] if r[4] == "i" else r for r in d["runs"]]
            new.append(hashlib.md5(json.dumps([d["q"], runs], separators=(",", ":")).encode()).hexdigest())
        if new == ident: break
        ident = new
    first, keep = {}, []
    for i, h in enumerate(ident):
        if h not in first: first[h] = len(keep); keep.append(i)
    remap = [first[h] for h in ident]
    merged = [DEFS[i] for i in keep]
    for d in merged:
        for r in d["runs"]:
            if r[4] == "i":
                for it in r[5]: it[0] = remap[it[0]]
    stats["definitions_merged"] += len(DEFS) - len(merged)
    names = {d["name"] for d in merged}
    for n in list(USES):
        if n not in names: USES.pop(n)
    DEFS[:] = merged
    return remap[root]

# ================================================================ export each block placed in model space
os.makedirs(os.path.join(OUT, "layers"), exist_ok=True)
manifest, extents = [], []

def runs_pts(runs, M=None, q=0):
    """every point of flat runs (world mm) for the frame"""
    for r in runs:
        kind, items = r[4], r[5]
        for it in items:
            if kind == "t": yield it[0], it[1]; continue
            if kind == "i": continue
            for l in (it if kind == "f" else [it]):
                x, y = l[0], l[1]; yield x, y
                for i in range(2, len(l), 2): x += l[i]; y += l[i + 1]; yield x, y

def expand_pts(di, M, depth=0):
    """every point of an instanced definition, placed by M (for the frame and the check)"""
    d = DEFS[di]; k = 10 ** -d["q"]
    a, b, c, dd, e, f = M
    for r in d["runs"]:
        kind, items = r[4], r[5]
        for it in items:
            if kind == "i":
                ca, cb, cc, cd, ce, cf = it[1:]
                yield from expand_pts(it[0], [a * ca + c * cb, b * ca + dd * cb, a * cc + c * cd, b * cc + dd * cd,
                                              a * ce + c * cf + e, b * ce + dd * cf + f], depth + 1)
                continue
            if kind == "t":
                x, y = it[0] * k, it[1] * k; yield a * x + c * y + e, b * x + dd * y + f; continue
            for l in (it if kind == "f" else [it]):
                x, y = l[0], l[1]
                X, Y = x * k, y * k; yield a * X + c * Y + e, b * X + dd * Y + f
                for i in range(2, len(l), 2):
                    x += l[i]; y += l[i + 1]; X, Y = x * k, y * k; yield a * X + c * Y + e, b * X + dd * Y + f

for e in msp:
    if e.dxftype() != "INSERT":
        seen[e.dxftype()] += 1; stats["modelspace_loose_" + e.dxftype()] += 1      # only the stacked blocks are the plan
        continue
    name = e.dxf.name
    fn = re.sub(r"[^A-Za-z0-9_-]", "_", name) + ".json"
    path = os.path.join(OUT, "layers", fn)
    lay = e.dxf.get("layer", "0")
    if FLAT:
        R = Runs(); flat_walk([e], R)
        json.dump({"block": name, "runs": R.runs}, open(path, "w", encoding="utf-8"), separators=(",", ":"))
        extents.append(list(runs_pts(R.runs)))
        info = {"runs": len(R.runs)}
    else:
        DEFS.clear(); INDEX.clear(); MAXSCALE.clear(); USES.clear()
        scales(name, max(abs(e.dxf.xscale), abs(e.dxf.yscale)))
        placed, shared = sum(USES.values()) - 1, sum(1 for n in USES if USES[n] > 1)
        root = define(name)
        root = merge_duplicates(root)
        place ={"m": affine(e.matrix44()), "spec": list(spec(e, lay))}
        json.dump({"block": name, "root": root, "place": place, "defs": DEFS}, open(path, "w", encoding="utf-8"), separators=(",", ":"))
        extents.append(list(expand_pts(root, place["m"])))
        info = {"defs": len(DEFS), "placements": placed, "placed_more_than_once": shared,
                "merged": stats["definitions_merged"]}
    manifest.append({"block": name, "file": "layers/" + fn, "bytes": os.path.getsize(path), "instanced": not FLAT, **info})
    print(f"  {name}: {os.path.getsize(path) / 1e6:.1f} MB  {info}  {time.time() - t0:.0f}s", flush=True)

# ---------------------------------------------------------------- frame: the extent of what's drawn
xs = sorted(p[0] for E in extents for p in E); ys = sorted(p[1] for E in extents for p in E)
full = [round(xs[0]), round(ys[0]), round(xs[-1]), round(ys[-1])]
qf = lambda a, f: a[int(f * (len(a) - 1))]
X0, X1, Y0, Y1 = qf(xs, .0005), qf(xs, .9995), qf(ys, .0005), qf(ys, .9995)
far = sum(1 for x in xs if x < X0 - 20000 or x > X1 + 20000) + sum(1 for y in ys if y < Y0 - 20000 or y > Y1 + 20000)
if not far: X0, Y0, X1, Y1 = full          # nothing stray: the frame is the whole drawing
X0, Y0, X1, Y1 = map(round, (X0, Y0, X1, Y1))

def lt_pattern(name):
    lt = doc.linetypes.get(name) if name in doc.linetypes else None
    try: pat = list(lt.simplified_line_pattern()) if lt else []
    except Exception: pat = []
    return [round(abs(v), 2) for v in pat]
for n in LAYERS: ltypes_used.add(layer_lt(n))
out = {
    "source": os.path.basename(SRC), "built": time.strftime("%Y-%m-%d %H:%M"), "seconds": round(time.time() - t0),
    "instanced": not FLAT, "frame": [X0, Y0, X1, Y1], "extent_all": full, "points_far_off": far,
    "blocks": manifest,
    "layers": {n: {"colour": hexc(layer_rgb(n)), "lt": layer_lt(n), "lw": layer_lw(n), "off": n in OFF, "frozen": n in FROZEN}
               for n in sorted(LAYERS)},
    "linetypes": {n: lt_pattern(n) for n in sorted(ltypes_used)}, "ltscale": LTSCALE,
    "styles": {s: (doc.styles.get(s).dxf.font if s in doc.styles else "") for s in styles_used},
    "check": {"seen": dict(seen), "drawn": dict(drawn), "failed": {k: [len(v), *sorted(set(v))[:5]] for k, v in failed.items()},
              "stats": dict(stats), "counted": "per definition" if not FLAT else "as placed"},
}
json.dump(out, open(os.path.join(OUT, "layers.json"), "w", encoding="utf-8"), indent=1)
print(f"done {time.time() - t0:.0f}s  frame {(X1 - X0) / 1000:.1f} x {(Y1 - Y0) / 1000:.1f} m, {far} points far off")
print("drawn", dict(drawn)); print("failed", {k: len(v) for k, v in failed.items()}); print("stats", dict(stats))
