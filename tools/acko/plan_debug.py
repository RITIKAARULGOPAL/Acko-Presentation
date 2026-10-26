"""Audit a layout DXF before it goes into the deck: are the boundaries, fills and text all coming through?

Walks model space with every block exploded (layer 0 and BYBLOCK inherit from the insert, as AutoCAD draws it),
resolves each entity's true colour, and checks the three things the plan needs:
  boundaries  closed outlines on the AC_* layers (one per space, the façade, the out-of-scope band); open ones,
              self-crossing ones and duplicates are flagged
  fills       every HATCH: solid or pattern, its colour, transparency and loops; loops that fail to convert,
              invalid or zero-area polygons, and hatches on hidden layers are flagged
  text        every TEXT / MTEXT / ATTRIB: the words, style, font, height and rotation; empty text, unresolved
              MTEXT codes, fonts that aren't installed and mirrored text are flagged
The DXF keeps the plan as blocks stacked at one point (base plan, space outlines, fills, labels, neighbourhoods,
core, plants, egress), so everything is kept per block and per layer, never merged.
Writes, into <out_dir>:
  report.json   counts per layer, every issue with its position, the space list (AC_ fill + label inside it)
  layers.json   the blocks in draw order, each with its role and layers (colour, counts)
  layers/<block>.json   one file per block: per layer and colour, its strokes, fills, wipeouts, hatch-pattern lines,
                and its text; integer mm, each run as its first point then deltas
  report.md     the summary, to read
  ref.svg       with --ref: ezdxf's own drawing of the DXF (true colours, hatch patterns, text as glyphs), the
                reference the extraction is checked against (about 1 min more)
View it all in tools/acko/plan_debug.html (serve the repo: python tools/serve.py, then /tools/acko/plan_debug.html).

usage: python tools/acko/plan_debug.py <layout.dxf> <out_dir> [--ref]
"""
import sys, os, re, json, math, time, collections
import ezdxf
from ezdxf import path as zpath, colors as zcolors
from ezdxf.fonts import fonts as zfonts
from shapely.geometry import Polygon, Point
from shapely.validation import explain_validity

SRC, OUT = sys.argv[1], sys.argv[2]
REF = "--ref" in sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
doc = ezdxf.readfile(SRC)
print(f"load {time.time() - t0:.0f}s", flush=True)

LAYERS = {l.dxf.name: l for l in doc.layers}
HIDDEN = {n for n, l in LAYERS.items() if not l.is_on() or l.is_frozen()}

def layer_rgb(name):
    l = LAYERS.get(name)
    if l is None: return (255, 255, 255)
    if l.rgb: return l.rgb
    return zcolors.aci2rgb(abs(l.dxf.color) or 7)

def rgb_of(e, eff, parent_rgb):
    """true colour: entity true colour > ACI > BYLAYER (effective layer) > BYBLOCK (insert's colour)"""
    if e.dxf.hasattr("true_color"): return zcolors.int2rgb(e.dxf.true_color)
    c = e.dxf.get("color", 256)
    if c == 256: return layer_rgb(eff)
    if c == 0: return parent_rgb or layer_rgb(eff)
    return zcolors.aci2rgb(c)

def hexc(rgb):
    r, g, b = rgb
    return "#%02x%02x%02x" % (r, g, b)

stats = collections.Counter()
per_layer = collections.defaultdict(collections.Counter)
issues = []      # dict(kind, layer, x, y, what)
fills, outlines, texts = [], [], []

def issue(kind, layer, x, y, what):
    issues.append(dict(kind=kind, layer=layer, x=round(x), y=round(y), what=what))

TOP = None
def walk(entities, parent="0", parent_rgb=None, depth=0):
    for e in entities:
        lay = e.dxf.get("layer", "0") if e.dxf.is_supported("layer") else "0"
        eff = parent if lay == "0" else lay
        t = e.dxftype()
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0):
            stats["invisible"] += 1; continue
        if t == "INSERT":
            global TOP
            if depth == 0: TOP = e.dxf.name       # the plan's layer blocks: base, outlines, fills, labels, ...
            ins_rgb = rgb_of(e, eff, parent_rgb)
            if eff in HIDDEN and LAYERS[eff].is_frozen():
                stats["insert_frozen"] += 1; continue
            for a in e.attribs:
                yield a, (a.dxf.layer if a.dxf.layer != "0" else eff), ins_rgb
            try:
                for ins in (e.multi_insert() if e.mcount > 1 else [e]):
                    yield from walk(ins.virtual_entities(), eff, ins_rgb, depth + 1)
            except Exception as ex:
                stats["insert_explode_error"] += 1
                p = e.dxf.insert; issue("block", eff, p.x, p.y, f"block {e.dxf.name} could not be exploded: {ex}")
        elif t in ("DIMENSION", "ARC_DIMENSION", "LEADER", "MLEADER"):
            if eff in HIDDEN: stats["dim_hidden"] += 1; continue
            try: yield from walk(e.virtual_entities(), eff, parent_rgb, depth + 1)
            except Exception: stats["dim_explode_error"] += 1
        else:
            yield e, eff, parent_rgb

def poly_of(p):
    pts = [(v.x, v.y) for v in p.flattening(5)]
    return pts

# ---------------------------------------------------------------- per-block, per-layer drawing store
def enc(pts):
    """integer mm, first point then deltas: [x0, y0, dx1, dy1, ...]"""
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(pts):
        x, y = round(x), round(y)
        if i and x == px and y == py: continue
        out += [x, y] if not i else [x - px, y - py]
        px, py = x, y
    return out

DRAW = {}      # (block, layer) -> {"c": {rgb: {"s": strokes, "f": fills, "m": wipeouts, "h": pattern lines}}, "t": texts}
def bucket(block, layer, rgb):
    L = DRAW.setdefault((block, layer), {"c": {}, "t": [], "n": collections.Counter()})
    return L, L["c"].setdefault(hexc(rgb), {"s": [], "f": [], "m": [], "h": []})

def draw_entity(e, eff, prgb):
    """what AutoCAD draws for one exploded primitive, into its block's layer (hatches and text are stored by their branches)"""
    t = e.dxftype()
    if t in ("HATCH", "TEXT", "MTEXT", "ATTRIB", "ATTDEF"): return
    L, B = bucket(TOP, eff, rgb_of(e, eff, prgb))
    L["n"][t] += 1
    try:
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end; B["s"].append(enc([(a.x, a.y), (b.x, b.y)]))
        elif t in ("LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE"):
            p = zpath.make_path(e)
            if len(p): B["s"].append(enc([(v.x, v.y) for v in p.flattening(8)]))
        elif t in ("SOLID", "TRACE", "3DFACE"):
            v = [(q.x, q.y) for q in e.wcs_vertices()]
            if len(v) >= 3: B["f"].append([enc(v)])
        elif t == "WIPEOUT":
            v = [(q.x, q.y) for q in e.boundary_path_wcs()]
            if len(v) >= 3: B["m"].append(enc(v))
        else:
            stats["not_drawn_" + t] += 1
    except Exception:
        stats["draw_error_" + t] += 1

# ---------------------------------------------------------------- walk
FONT_OK = {}
def font_ok(style):
    if style in FONT_OK: return FONT_OK[style]
    st = doc.styles.get(style) if style in doc.styles else None
    f = (st.dxf.font if st else "") or ""
    ok = True; note = ""
    if f.lower().endswith(".shx") or f.lower() == "txt" or f == "":
        ok, note = False, f"SHX font '{f or 'txt'}' (AutoCAD-only), needs a TTF stand-in"
    else:
        try:
            face = zfonts.font_manager.get_font_face(f)
            found = face and face.filename and os.path.basename(face.filename).lower().split(".")[0] == f.lower().split(".")[0]
            if not found: ok, note = False, f"font '{f}' not installed, falls back to {face.filename if face else '?'}"
        except Exception as ex:
            ok, note = False, f"font '{f}' lookup failed: {ex}"
    FONT_OK[style] = (ok, f, note)
    return FONT_OK[style]

MTEXT_CODE = re.compile(r"\\[A-Za-z][^;\\]*;|\\[PpLlOoKkNX~]|[{}]")
for e, eff, prgb in walk(doc.modelspace()):
    t = e.dxftype()
    stats[t] += 1; per_layer[eff][t] += 1
    hidden = eff in HIDDEN
    if hidden:
        stats["on_hidden_layer"] += 1; continue
    draw_entity(e, eff, prgb)
    if t == "HATCH":
        rgb = rgb_of(e, eff, prgb)
        solid = bool(e.dxf.solid_fill)
        tr = e.transparency if hasattr(e, "transparency") else 0
        # text-box loops (flag 8) only keep the fill clear of text; AutoCAD doesn't draw them as boundaries, and here
        # they are stale copies far off the floor
        tb = [bp for bp in e.paths if bp.path_type_flags & 8]
        if tb:
            stats["hatch_textbox_loops_dropped"] += len(tb); stats["hatches_with_textbox_loops"] += 1
            e.paths.paths = [bp for bp in e.paths if not bp.path_type_flags & 8]
        try:
            paths = list(zpath.from_hatch(e))
        except Exception as ex:
            paths = []
            stats["hatch_path_error"] += 1
        loops = []
        for p in paths:
            pts = poly_of(p)
            if len(pts) >= 3: loops.append(pts)
        if not loops:
            stats["hatch_no_boundary"] += 1
            sp = e.seeds[0] if e.seeds else (0, 0)
            issue("fill", eff, sp[0], sp[1], f"{'solid' if solid else e.dxf.pattern_name} hatch has no usable boundary ({len(e.paths)} loops in the DXF)")
            continue
        # outer loops vs holes: evenodd over all loops, as AutoCAD's normal style draws
        polys = [Polygon(l) for l in loops]
        bad = [explain_validity(pg) for pg in polys if not pg.is_valid]
        area = sum(pg.buffer(0).area for pg in polys) / 1e6
        cx, cy = polys[0].representative_point().coords[0] if polys[0].is_valid else loops[0][0]
        if bad:      # touching loops are normal in a multi-loop hatch; a space's fill is checked against its outline below
            stats["hatch_loops_self_touching"] += 1
        if area < 0.0005 and eff.startswith("AC_"):
            stats["hatch_zero_area"] += 1
            issue("fill", eff, cx, cy, "hatch with ~zero area")
        if hidden: stats["hatch_on_hidden_layer"] += 1
        L, B = bucket(TOP, eff, rgb); L["n"]["HATCH"] += 1
        if solid:
            B["f"].append([enc(l) for l in loops])
        else:
            try:
                from ezdxf.render import hatching
                B["h"] += [enc([(ln.start.x, ln.start.y), (ln.end.x, ln.end.y)]) for ln in hatching.hatch_entity(e)]
            except Exception:
                stats["hatch_pattern_error"] += 1; B["s"] += [enc(l + l[:1]) for l in loops]
        fills.append(dict(top=TOP, layer=eff, solid=solid, pattern=None if solid else e.dxf.pattern_name, rgb=hexc(rgb),
                          alpha=round(1 - (tr or 0), 2), m2=round(area, 2), loops=loops, hidden=hidden, x=cx, y=cy))
    elif t in ("TEXT", "MTEXT", "ATTRIB", "ATTDEF"):
        if t == "ATTDEF": stats["attdef_skipped"] += 1; continue
        if t == "ATTRIB" and (e.is_invisible or e.dxf.get("tag", "").upper() == "PARTITIONTYPE"):
            stats["attrib_hidden"] += 1; continue
        raw = e.text if t == "MTEXT" else e.dxf.text
        plain = e.plain_text() if t == "MTEXT" else (e.plain_text() if hasattr(e, "plain_text") else raw)
        style = e.dxf.get("style", "Standard")
        h = e.dxf.get("char_height" if t == "MTEXT" else "height", 0) or 0
        rot = e.get_rotation() if t == "MTEXT" else (e.dxf.get("rotation", 0) or 0)
        ins = e.dxf.insert
        ok, font, fnote = font_ok(style)
        rec = dict(top=TOP, t=t, layer=eff, style=style, font=font, h=round(h, 1), rot=round(rot, 1), x=round(ins.x), y=round(ins.y),
                   raw=raw, text=plain, hidden=hidden, rgb=hexc(rgb_of(e, eff, prgb)))
        if t == "MTEXT":
            rec["ap"] = e.dxf.get("attachment_point", 1); rec["w"] = round(e.dxf.get("width", 0) or 0)
            left = MTEXT_CODE.sub("", plain)
            if left != plain: issue("text", eff, ins.x, ins.y, f"MTEXT codes left in the plain text: {plain[:60]!r}")
        if t != "MTEXT" and e.dxf.hasattr("extrusion") and e.dxf.extrusion.z < 0:
            issue("text", eff, ins.x, ins.y, f"mirrored text (extrusion z<0): {plain[:40]!r}")
        if not plain.strip():
            stats["text_empty"] += 1
        elif not hidden:
            if not ok: stats["text_font_fallback"] += 1
            if h <= 0: issue("text", eff, ins.x, ins.y, f"text height 0: {plain[:40]!r}")
        texts.append(rec)
        if plain.strip():
            L, _ = bucket(TOP, eff, rgb_of(e, eff, prgb)); L["n"][t] += 1
            if t == "MTEXT":
                ap, wf = rec["ap"], 1
            else:     # TEXT alignment onto MTEXT's 1..9 grid (1 top-left .. 9 bottom-right); the baseline counts as bottom
                ha, va = e.dxf.get("halign", 0), e.dxf.get("valign", 0)
                if (ha or va) and ha not in (3, 5) and e.dxf.hasattr("align_point"): ins = e.dxf.align_point
                ap = {3: 0, 2: 3, 1: 6, 0: 6}[va if ha != 4 else 2] + {0: 1, 1: 2, 2: 3, 4: 2}.get(ha, 1)
                wf = round(e.dxf.get("width", 1) or 1, 2)
            L["t"].append([round(ins.x), round(ins.y), round(h, 1), round(rot, 2), ap, plain, rec["rgb"], wf])
    elif t in ("LWPOLYLINE", "POLYLINE") and eff.upper().startswith("AC") and not eff.upper().startswith("AC_WS_"):
        # (AC_WS_* is the workstation blocks' own linework, not a boundary)
        try: pts = poly_of(zpath.make_path(e))
        except Exception: stats["outline_path_error"] += 1; continue
        closed = e.closed if t == "LWPOLYLINE" else e.is_closed
        if not closed and len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1: closed = True
        elif not closed and len(pts) > 3 and math.dist(pts[0], pts[-1]) < 1000:
            issue("boundary", eff, pts[-1][0], pts[-1][1], f"outline not closed (gap {math.dist(pts[0], pts[-1]):.0f} mm): closed for the check, close it in CAD")
            closed = True; pts = pts + [pts[0]]
        rec = dict(top=TOP, layer=eff, closed=closed, pts=pts, hidden=hidden, rgb=hexc(rgb_of(e, eff, prgb)))
        if closed and len(pts) >= 3:
            pg = Polygon(pts); rec["m2"] = round(abs(pg.area) / 1e6, 2)
        elif not closed:
            issue("boundary", eff, pts[0][0], pts[0][1], f"stray line on a boundary layer ({math.dist(pts[0], pts[-1]) / 1000:.1f} m)" if len(pts) == 2
                  else f"open outline ({len(pts)} pts, gap {math.dist(pts[0], pts[-1]):.0f} mm)")
        outlines.append(rec)
print(f"walk {time.time() - t0:.0f}s", dict(stats), flush=True)

# ---------------------------------------------------------------- spaces: one closed outline per space (the outlines block),
# checked against its type's fill (one multi-loop hatch per type) and the room labels
from shapely.ops import unary_union
OPEN_PLAN = {"AC_WORKHALL", "AC_CORRIDOR", "AC_GLAZING", "AC_ENTRY", "AC_OUT_OF_SCOPE", "AC_OUT_OF_ZONE", "AC_TERRACE",
             "AC_FIRE_COMPARTMENTALISATION", "AC_STRENGTHEN_SLAB"}
ZONES = {"AC_AUTO", "AC_LIFE", "AC_HEALTH", "AC_DRIVE", "AC_TRAVEL", "AC_HOME", "AC_ATRIUM"}
labels = [x for x in texts if x["text"].strip() and (x["layer"] in ("OB-I-ANNO-TEXT", "A-AREA-IDEN") or x["layer"].startswith("AC_"))]
def clean(pts):
    pg = Polygon(pts)
    return pg if pg.is_valid else pg.buffer(0)
fill_geom = {}
for f in fills:
    if f["layer"].startswith("AC_") and f["solid"]:
        g = None
        for l in f["loops"]:                       # even-odd over the loops, as the hatch draws
            pg = clean(l)
            if pg.is_empty: continue
            g = pg if g is None else g.symmetric_difference(pg)
        if g is None: continue
        # the fill's outer edge: furniture islands are holes in a CAD fill, not gaps in the space
        g = unary_union([Polygon(part.exterior) for part in getattr(g, "geoms", [g]) if part.area > 0])
        fill_geom[f["layer"]] = g if f["layer"] not in fill_geom else fill_geom[f["layer"]].union(g)
spaces = []
for o in outlines:
    lay = o["layer"]
    if not o["closed"] or len(o["pts"]) < 3: continue
    raw = Polygon(o["pts"]); pg = clean(o["pts"])
    if pg.is_empty or pg.area < 1e5: continue      # under 0.1 m2: a tick, not a space
    c = pg.representative_point()
    sp = dict(top=o["top"], layer=lay, m2=round(pg.area / 1e6, 2), x=round(c.x), y=round(c.y), pts=o["pts"])
    if not raw.is_valid and abs(abs(raw.area) - pg.area) / pg.area > 0.01:
        issue("boundary", lay, c.x, c.y, f"outline self-crosses and loses {abs(abs(raw.area) - pg.area) / 1e6:.1f} m² when cleaned")
    if lay in ZONES:
        sp["kind"] = "zone"
    else:
        sp["kind"] = "open" if lay in OPEN_PLAN else "room"
        fg = fill_geom.get(lay)
        cov = fg.intersection(pg).area / pg.area if fg is not None else 0
        sp["fill_cover"] = round(cov, 3)
        if lay not in ("AC_GLAZING", "AC_FIRE_COMPARTMENTALISATION") and cov < 0.9:
            issue("fill", lay, c.x, c.y, f"{lay} outline ({sp['m2']} m²) only {cov:.0%} covered by its fill" if fg is not None else f"{lay} has no fill at all")
        inside = [l for l in labels if pg.contains(Point(l["x"], l["y"]))]
        sp["labels"] = [l["text"].replace("\n", " ").strip() for l in inside][:4]
        if sp["kind"] == "room" and not inside:
            issue("label", lay, c.x, c.y, f"{lay} ({sp['m2']} m²) has no label inside")
    spaces.append(sp)
# fill loops with no outline of the same type under them
for lay, g in fill_geom.items():
    if lay in ZONES: continue
    covered = unary_union([clean(s["pts"]) for s in spaces if s["layer"] == lay]) if any(s["layer"] == lay for s in spaces) else None
    for part in getattr(g, "geoms", [g]):
        if part.area < 2e5: continue
        if covered is None or covered.intersection(part).area / part.area < 0.5:
            c = part.representative_point(); issue("boundary", lay, c.x, c.y, f"{lay} fill ({part.area / 1e6:.1f} m²) has no outline")
# outlines drawn twice, or a room drawn over another room (open-plan areas, the façade and the slab marks are containers)
CONTAINERS = OPEN_PLAN | ZONES
rooms = [(s, clean(s["pts"])) for s in spaces if s["layer"] not in CONTAINERS]
for i, (a, pa) in enumerate(rooms):
    for b, pb in rooms[i + 1:]:
        if not pa.intersects(pb): continue
        ov = pa.intersection(pb).area / min(pa.area, pb.area)
        if ov > 0.3:
            c = pa.intersection(pb).representative_point()
            what = (f"{a['layer']} drawn twice ({a['m2']} and {b['m2']} m², {ov:.0%} overlap)" if a["layer"] == b["layer"]
                    else f"{a['layer']} ({a['m2']} m²) and {b['layer']} ({b['m2']} m²) overlap {ov:.0%}")
            issue("boundary", a["layer"], c.x, c.y, what)
for s in spaces:       # an open-plan outline lying over rooms: the room is drawn on top in CAD, but the area double counts
    if s["layer"] not in OPEN_PLAN - {"AC_GLAZING"}: continue
    ps = clean(s["pts"]); under = [r for r, pr in rooms if ps.intersection(pr).area > 0.5 * pr.area]
    if len(under) >= 3 and ps.area < 2e8:
        c = ps.representative_point()
        issue("boundary", s["layer"], c.x, c.y, f"{s['layer']} outline ({s['m2']} m²) lies over {len(under)} rooms: {', '.join(sorted({r['layer'][3:] for r in under}))}")
# labels that sit in no space at all
room_union = unary_union([clean(s["pts"]) for s in spaces if s["kind"] != "zone"])
for l in labels:
    if l["layer"] == "OB-I-ANNO-TEXT" and not room_union.contains(Point(l["x"], l["y"])):
        issue("label", l["layer"], l["x"], l["y"], f"label {l['text'][:40]!r} sits in no outlined space")
# AC_ layers that exist but carry no fill / no outline
ac_layers = [n for n in LAYERS if n.upper().startswith("AC")]
fill_layers = collections.Counter(f["layer"] for f in fills)
out_layers = collections.Counter(o["layer"] for o in outlines)

# ---------------------------------------------------------------- frame and layer files
xs = sorted([p[0] for f in fills for l in f["loops"] for p in l] + [p[0] for o in outlines for p in o["pts"]])
ys = sorted([p[1] for f in fills for l in f["loops"] for p in l] + [p[1] for o in outlines for p in o["pts"]])
cut = lambda a, q: a[int(q * (len(a) - 1))]
X0, X1, Y0, Y1 = cut(xs, .002), cut(xs, .998), cut(ys, .002), cut(ys, .998)
pad = 0.03 * (X1 - X0); X0 -= pad; X1 += pad; Y0 -= pad; Y1 += pad
OX, OY, W, H = math.floor(X0), math.ceil(Y1), math.ceil(X1 - X0), math.ceil(Y1 - Y0)

def role(block):
    """what one of the stacked blocks holds, from its contents"""
    n = collections.Counter()
    for (b, lay), L in DRAW.items():
        if b == block: n[lay] += sum(L["n"].values())
    tot = sum(n.values()) or 1
    share = lambda f: sum(v for k, v in n.items() if f(k)) / tot
    hatch = sum(L["n"]["HATCH"] for (b, _), L in DRAW.items() if b == block) / tot
    if share(lambda k: k.startswith("ak_Ep")) > .5: return "Fire egress"
    if share(lambda k: k in ZONES or k in ("AC_TERRACE", "AC_OUT_OF_ZONE", "AC_CAFETERIA")) > .5: return "Neighbourhoods"
    if share(lambda k: k in ("AC_FIRE_EXIT_STAIRCASE", "AC_AHU", "AC_WASHROOM", "AC_LIFT_LOBBY", "AC_STRENGTHEN_SLAB")) > .5: return "Core"
    if share(lambda k: "ANNO" in k or "TEXT" in k) > .5: return "Labels"
    if share(lambda k: "PLANT" in k.upper() or "PLNT" in k.upper()) > .3: return "Plants"
    if hatch > .5: return "Fills"
    if share(lambda k: k.startswith("AC_")) > .5: return "Space outlines"
    return "Base plan"
ORDER = ["Fills", "Base plan", "Plants", "Core", "Space outlines", "Neighbourhoods", "Fire egress", "Labels"]
ROLE = {b: role(b) for b in {b for b, _ in DRAW}}
blocks = sorted(ROLE, key=lambda b: (ORDER.index(ROLE[b]) if ROLE[b] in ORDER else 99, str(b)))
os.makedirs(os.path.join(OUT, "layers"), exist_ok=True)
manifest = []
for b in blocks:
    data, lays = {"block": b, "role": ROLE[b], "layers": []}, []
    for (bb, lay), L in sorted(DRAW.items(), key=lambda kv: kv[0][1]):
        if bb != b: continue
        weight = lambda kv: sum(len(v) for v in kv[1].values())
        main = max(L["c"].items(), key=weight)[0] if L["c"] else (L["t"][0][6] if L["t"] else "#000000")
        data["layers"].append({"name": lay, "colour": main, "c": L["c"], "t": L["t"]})
        lays.append({"name": lay, "colour": main, "counts": dict(L["n"])})
    fn = re.sub(r"[^A-Za-z0-9_-]", "_", str(b)) + ".json"
    path = os.path.join(OUT, "layers", fn)
    json.dump(data, open(path, "w", encoding="utf-8"), separators=(",", ":"))
    manifest.append({"block": b, "role": ROLE[b], "file": "layers/" + fn, "bytes": os.path.getsize(path), "layers": lays})
    print(f"  {ROLE[b]:15s} {str(b):10s} {len(lays):3d} layers  {manifest[-1]['bytes'] / 1e6:5.1f} MB", flush=True)
if os.path.exists(os.path.join(OUT, "audit.svg")): os.remove(os.path.join(OUT, "audit.svg"))

# ---------------------------------------------------------------- reference render
ref_extents = None
if REF:
    # vector, like everything else here; ~60 MB, so the viewer loads it only when asked
    from ezdxf.addons.drawing import Frontend, RenderContext, svg as dsvg, layout as dlayout, config as dconfig
    backend = dsvg.SVGBackend()
    cfg = dconfig.Configuration(background_policy=dconfig.BackgroundPolicy.WHITE, color_policy=dconfig.ColorPolicy.COLOR_SWAP_BW,
                                lineweight_policy=dconfig.LineweightPolicy.RELATIVE, text_policy=dconfig.TextPolicy.FILLING)
    Frontend(RenderContext(doc), backend, config=cfg).draw_layout(doc.modelspace(), finalize=True)
    box = backend.player().bbox()
    ref_extents = [round(box.extmin.x, 1), round(box.extmin.y, 1), round(box.extmax.x, 1), round(box.extmax.y, 1)]
    page = dlayout.Page(0, 0, dlayout.Units.mm, margins=dlayout.Margins.all(0))
    open(os.path.join(OUT, "ref.svg"), "w", encoding="utf-8").write(backend.get_string(page, render_box=box,
        settings=dlayout.Settings(output_coordinate_space=1_000_000, max_stroke_width=0.0005, min_stroke_width=0.0001)))
    print(f"ref.svg {time.time() - t0:.0f}s", flush=True)
elif os.path.exists(os.path.join(OUT, "report.json")):    # keep the last reference render's extents
    ref_extents = json.load(open(os.path.join(OUT, "report.json"), encoding="utf-8")).get("ref_extents")

# ---------------------------------------------------------------- report
fonts = sorted({(x["style"], x["font"], *font_ok(x["style"])[::2]) for x in texts if not x["hidden"] and x["text"].strip()})
rep = dict(source=os.path.basename(SRC), seconds=round(time.time() - t0), frame=[OX, OY, W, H], ref_extents=ref_extents, stats=stats,
           hidden_layers=sorted(HIDDEN),
           fills=dict(total=len(fills), solid=sum(f["solid"] for f in fills), pattern=sum(not f["solid"] for f in fills),
                      on_hidden=sum(f["hidden"] for f in fills), by_layer=dict(fill_layers.most_common())),
           outlines=dict(total=len(outlines), open=sum(not o["closed"] for o in outlines), by_layer=dict(out_layers.most_common())),
           ac_layers={n: dict(fills=fill_layers.get(n, 0), outlines=out_layers.get(n, 0), texts=sum(x["layer"] == n for x in texts),
                              colour=hexc(layer_rgb(n)), hidden=n in HIDDEN) for n in ac_layers},
           text=dict(total=len(texts), shown=sum(not x["hidden"] and bool(x["text"].strip()) for x in texts),
                     by_layer=dict(collections.Counter(x["layer"] for x in texts if not x["hidden"]).most_common()),
                     fonts=[dict(style=s, file=f, ok=ok, note=n) for s, f, ok, n in fonts]),
           issues_by_kind=dict(collections.Counter(i["kind"] for i in issues)), issues=issues, spaces=spaces,
           labels=[dict(layer=x["layer"], text=x["text"], x=x["x"], y=x["y"], h=x["h"], style=x["style"]) for x in labels])
json.dump(rep, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), indent=1, default=int)
json.dump(dict(source=rep["source"], frame=[OX, OY, W, H], ref_extents=ref_extents, ref="ref.svg", blocks=manifest),
          open(os.path.join(OUT, "layers.json"), "w", encoding="utf-8"), indent=1)

md = [f"# Plan audit: {rep['source']}", "", f"{rep['seconds']} s. Frame {W/1000:.1f} × {H/1000:.1f} m.", "",
      "## Fills", f"{len(fills)} hatches: {rep['fills']['solid']} solid, {rep['fills']['pattern']} pattern, {rep['fills']['on_hidden']} on hidden layers.", "",
      "## Boundaries (AC_ polylines)", f"{len(outlines)} outlines, {rep['outlines']['open']} open.", "",
      "## AC_ layers", "| layer | colour | fills | outlines | texts |", "|---|---|---|---|---|"]
md += [f"| {n} | {v['colour']} | {v['fills']} | {v['outlines']} | {v['texts']} |" for n, v in rep["ac_layers"].items()]
md += ["", "## Text", f"{rep['text']['shown']} shown of {len(texts)}.", "", "| style | font file | ok | note |", "|---|---|---|---|"]
md += [f"| {f['style']} | {f['file']} | {'yes' if f['ok'] else 'no'} | {f['note']} |" for f in rep["text"]["fonts"]]
md += ["", "## Issues", ", ".join(f"{k}: {v}" for k, v in rep["issues_by_kind"].items()) or "none", ""]
md += [f"- **{i['kind']}** `{i['layer']}` at ({i['x']}, {i['y']}): {i['what']}" for i in issues[:300]]
open(os.path.join(OUT, "report.md"), "w", encoding="utf-8").write("\n".join(md))
print(f"done {time.time() - t0:.0f}s  fills={len(fills)} outlines={len(outlines)} texts={len(texts)} issues={len(issues)}", dict(rep["issues_by_kind"]))
