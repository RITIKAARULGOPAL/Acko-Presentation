"""Check the room hatches the deck hovers on, against the plan's other layers, from plan_vector.py's export.

The rooms DXF (group "rooms") holds one solid hatch per room type (AC_<TYPE>), each with a loop per room. For hover every
room must be its own clean shape, so each hatch is split into rooms (even-odd over its loops; furniture islands are
holes in a CAD fill, so a room's hover shape is its outer edge) and every room is checked:
  shape        a valid polygon of a sensible size
  overlap      no other room's hover shape covers part of it (the cursor would light two rooms)
  outline      the zoneBoundaries group has an outline of the same type that matches it (intersection over union);
               outlines with no hatch are listed too
  label        a label from the text group sits inside it, and its words fit the type
  neighbourhood  which of the six it lies in (the neighbourhoods group), for the occupancy panels
Writes <dir>/rooms.json: every room (type, colour, area, label, neighbourhood, outline match, its shape in world mm) and
every issue with its position, which plan_view.html draws as a hover layer and an issue list.

usage: python tools/acko/plan_rooms.py <export dir, e.g. tools/_work/plan> [--only=25,40]
"""
import sys, os, re, json, math, collections
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import explain_validity

DIR = sys.argv[1]
# --only 25,40: rebuild just these shapes' hover; every other shape keeps its hover from the last run (fast, for one fix)
ONLY = next((set(int(v) for v in a.split("=", 1)[1].split(",")) for a in sys.argv[2:] if a.startswith("--only=")), None)
meta = json.load(open(os.path.join(DIR, "layers.json"), encoding="utf-8"))
L = meta["layers"]

def decode(a, k):
    pts, x, y = [(a[0] * k, a[1] * k)], a[0], a[1]
    for i in range(2, len(a), 2):
        x += a[i]; y += a[i + 1]; pts.append((x * k, y * k))
    return pts

def expand(group):
    """every placed item of a group in world mm: (layer, colour, kind, item) with item = loops / points / text"""
    out = []
    for b in meta["blocks"]:
        if b["group"] != group: continue
        data = json.load(open(os.path.join(DIR, b["file"]), encoding="utf-8"))
        defs = data["defs"]
        def resolve(spec, ctx):
            layer = spec[0] or ctx[0]
            col = (L.get(layer, {}).get("colour", "#000000") if spec[1] == "L" else ctx[1] if spec[1] == "B" else spec[1])
            return layer, col
        root = ("0", L.get("0", {}).get("colour", "#000000"))
        def walk(di, M, ctx):
            d = defs[di]; k = 10 ** -d["q"]; a, b_, c, e, f, g = M
            T = lambda p: (a * p[0] + c * p[1] + f, b_ * p[0] + e * p[1] + g)
            for r in d["runs"]:
                layer, col = resolve(r[:4], ctx); kind = r[4]
                for it in r[5]:
                    if kind == "i":
                        ci, ca, cb, cc, cd, ce, cf = it
                        walk(ci, [a * ca + c * cb, b_ * ca + e * cb, a * cc + c * cd, b_ * cc + e * cd, a * ce + c * cf + f, b_ * ce + e * cf + g], (layer, col))
                    elif kind == "t":
                        out.append((layer, col, "t", (T((it[0] * k, it[1] * k)), it[6], it[2])))
                    elif kind == "f":
                        out.append((layer, col, "f", [[T(p) for p in decode(l, k)] for l in it]))
                    else:
                        out.append((layer, col, kind, [T(p) for p in decode(it, k)]))
        walk(data["root"], data["place"]["m"], resolve(data["place"]["spec"], root))
    return out

issues = []
def issue(kind, layer, pt, what, level="issue", **kw):
    """level: "issue" needs a look in CAD; "note" is expected but worth knowing (it shows in the hover)"""
    issues.append({"kind": kind, "level": level, "layer": layer, "x": round(pt[0]), "y": round(pt[1]), "what": what, **kw})

def clean(pts):
    pg = Polygon(pts)
    return pg if pg.is_valid else pg.buffer(0)
def parts(g): return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and not p.is_empty]

TYPE_WORDS = {   # words a room's label should carry, by type (beyond its own layer name's words)
    "AC_COLLAB_HUDDLE": ["COLLABORATION", "HUDDLE"], "AC_QUICK_SPRINT": ["SPRINT", "PAX"], "AC_PHONE_BOOTH": ["PHONE", "BOOTH", "PAX"],
    "AC_DEPARTMENTAL_ROOMS": ["DEPARTMENTAL"], "AC_UPS_SERVER_BATTERY_BMS_ROOM": ["UPS", "SERVER", "BATTERY", "BMS", "ELECTRICAL"],
    "AC_EXECUTIVE_CORNER_CABIN": ["EXECUTIVE", "CABIN"], "AC_THE_STUDIO_ROOM": ["STUDIO"], "AC_THE_HATCHERY": ["HATCHERY"],
    "AC_BOARD_ROOM": ["BOARD"], "AC_COFFEE_CORNER": ["COFFEE"], "AC_WORKHALL": ["WORK"], "AC_CORRIDOR": ["CORRIDOR"],
}
DEV_MM = 400            # mm a hover shape may stray from its outline (a wall's thickness and a little)
OPEN = {"AC_WORKHALL", "AC_CORRIDOR", "AC_OUT_OF_ZONE", "AC_OUT_OF_SCOPE", "AC_TERRACE", "AC_ENTRY"}
ZONES = ["AC_AUTO", "AC_LIFE", "AC_HEALTH", "AC_DRIVE", "AC_TRAVEL", "AC_HOME"]

# ---------------------------------------------------------------- the room hatches, split into rooms
rooms = []
for layer, col, kind, it in expand("rooms"):
    if kind != "f":
        continue
    g = None
    for loop in it:                                # even-odd over the hatch's loops, as AutoCAD fills it
        pg = clean(loop)
        if pg.is_empty: continue
        g = pg if g is None else g.symmetric_difference(pg)
    if g is None: continue
    for p in parts(g):
        shell = Polygon(p.exterior)                # furniture islands are holes in the fill, not gaps in the room
        if shell.area < 2e5: continue              # under 0.2 m2: a sliver between loops, not a room
        rooms.append({"type": layer, "colour": col, "poly": shell, "fill": p, "islands": len(p.interiors)})
# a filled loop inside a furniture island (a table's inlay, a planter) is drawn as its own piece; for hover it is part of
# the room around it
rooms.sort(key=lambda r: -r["poly"].area)
kept = []
for r in rooms:
    host = next((k for k in kept if k["type"] == r["type"] and k["poly"].contains(r["poly"].representative_point())
                 and k["poly"].intersection(r["poly"]).area > 0.95 * r["poly"].area), None)
    if host: host["nested"] = host.get("nested", 0) + 1
    else: kept.append(r)
nested = len(rooms) - len(kept); rooms = kept
# an open area's hatch can come as loops that only share an edge (a corridor in pieces): touching pieces of one open
# type are one hover shape
joined = 0
for t in sorted({r["type"] for r in rooms if r["type"] in OPEN}):
    group = [r for r in rooms if r["type"] == t]
    while True:
        pair = next(((a, b) for i, a in enumerate(group) for b in group[i + 1:] if a["poly"].distance(b["poly"]) < 50), None)
        if not pair: break
        a, b = pair
        fill = unary_union([a["fill"].buffer(5), b["fill"].buffer(5)]).buffer(-5)
        fill = max(parts(fill), key=lambda p: p.area)
        a.update(poly=Polygon(fill.exterior), fill=fill, islands=len(fill.interiors), joined=a.get("joined", 0) + 1 + b.get("joined", 0))
        group.remove(b); rooms.remove(b); joined += 1
# a corner cut off a room where furniture meets its wall comes out as a sliver of its own: a piece under 2 m2 with no
# label, touching a room of its type, is part of that room
def merge_into(a, b):
    fill = unary_union([a["fill"].buffer(5), b["fill"].buffer(5)]).buffer(-5)
    fill = max(parts(fill), key=lambda p: p.area)
    a.update(poly=Polygon(fill.exterior), fill=fill, islands=len(fill.interiors), merged=a.get("merged", 0) + 1)
    rooms.remove(b)
label_at = [Point(it[0]) for layer, col, kind, it in expand("text") if kind == "t" and it[1].strip()]
slivers = 0
for b in sorted([r for r in rooms if r["type"] not in OPEN], key=lambda r: r["poly"].area):
    if b["poly"].area >= 2e6 or any(b["poly"].contains(q) for q in label_at): continue
    host = min((a for a in rooms if a is not b and a["type"] == b["type"] and a["poly"].distance(b["poly"]) < 50),
               key=lambda a: a["poly"].distance(b["poly"]), default=None)
    if host: merge_into(host, b); slivers += 1
print(f"{len(rooms)} rooms from {sum(1 for x in expand('rooms') if x[2] == 'f')} hatches ({nested} nested pieces folded into their rooms, "
      f"{joined} touching open-area pieces joined, {slivers} slivers merged into their rooms)")

# stable numbers: a shape keeps the number it had in the last run (the checklist and the viewer's fine list use them);
# matched by type and overlap, new shapes numbered after the highest
prev_path = os.path.join(DIR, "rooms.json")
CHECKED_PRE = json.load(open(os.path.join(DIR, "checked.json"), encoding="utf-8")) if os.path.exists(os.path.join(DIR, "checked.json")) else {}
prev = json.load(open(prev_path, encoding="utf-8"))["rooms"] if os.path.exists(prev_path) else []
taken, nxt = set(), max([p["id"] for p in prev] + [CHECKED_PRE.get("next_id", 0) - 1], default=-1) + 1   # numbers are never reused
for r in sorted(rooms, key=lambda r: -r["poly"].area):
    best, bid = 0.5, None
    for p in prev:
        if p["type"] != r["type"] or p["id"] in taken: continue
        pp = Polygon(p["shape"])
        if not pp.is_valid: pp = pp.buffer(0)
        if not pp.intersects(r["poly"]): continue
        iou = pp.intersection(r["poly"]).area / pp.union(r["poly"]).area
        if iou > best: best, bid = iou, p["id"]
    if bid is None: bid = nxt; nxt += 1
    r["id"] = bid; taken.add(bid)
gone = sorted({p["id"] for p in prev} - taken)
if gone: print("shapes no longer there (merged or removed):", gone)

# ---------------------------------------------------------------- the other layers
outlines = []
for layer, col, kind, pts in expand("zoneBoundaries"):
    if kind == "s" and layer.startswith("AC_") and len(pts) >= 4 and math.dist(pts[0], pts[-1]) < 1000:
        outlines.append({"type": layer, "poly": clean(pts), "open": math.dist(pts[0], pts[-1]) > 1})
labels = [{"layer": layer, "pt": it[0], "words": it[1].replace("\n", " ").strip(), "h": it[2]}
          for layer, col, kind, it in expand("text") if kind == "t" and it[1].strip()]
zones = []
for layer, col, kind, pts in expand("neighbourhoods"):
    if layer in ZONES and kind == "s" and len(pts) >= 4:
        zones.append({"name": layer[3:].title(), "poly": clean(pts + [pts[0]])})
print(f"{len(outlines)} outlines, {len(labels)} labels, {len(zones)} neighbourhoods")

# ---------------------------------------------------------------- checks
for i, r in enumerate(rooms):
    p, c = r["poly"], r["poly"].representative_point().coords[0]
    r["m2"], r["x"], r["y"] = round(p.area / 1e6, 2), round(c[0]), round(c[1])
    # shape
    raw = Polygon(r["poly"].exterior.coords)
    if not raw.is_valid: issue("shape", r["type"], c, f"hover shape self-crosses: {explain_validity(raw)}", room=r["id"])
    # outline of the same type
    best, bi = 0, None
    for j, o in enumerate(outlines):
        if o["type"] != r["type"] or not o["poly"].intersects(p): continue
        iou = o["poly"].intersection(p).area / o["poly"].union(p).area
        if iou > best: best, bi = iou, j
    r["outline_iou"] = round(best, 3)
    if bi is not None:
        outlines[bi].setdefault("rooms", []).append(i)
        if best >= 0.5: r["outline_poly"] = outlines[bi]["poly"]
        # how far the hover shape strays from its outline: a fill stops at the wall's inner face, so up to a wall's
        # thickness is expected
        o = outlines[bi]["poly"]
        dev, ratio = p.hausdorff_distance(o), p.area / o.area
        r["outline_dev_mm"], r["outline_area_ratio"] = round(dev), round(ratio, 3)
        if dev > DEV_MM and r["type"] not in OPEN:
            # furniture islands that touch a wall notch the fill's edge: a smaller area than the outline but in its bounds
            ok = 0.8 <= ratio <= 1.05
            issue("outline", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²): the hatch is {ratio:.0%} of its outline's area, "
                  f"its edge up to {dev / 1000:.2f} m off" + (" (furniture notches)" if ok else ""), level="note" if ok else "issue", room=r["id"])
    if r.get("outline_poly") is None:
        # a hatch that only half fills its room (furniture against the walls) still lies within its outline: take the
        # same-type outline that holds nearly all of it, if it isn't many times bigger
        cand = [o for o in outlines if o["type"] == r["type"] and o["poly"].intersects(p)]
        cand = [o for o in cand if o["poly"].intersection(p).area > 0.85 * p.area and o["poly"].area < 3 * p.area]
        if cand: r["outline_poly"] = min(cand, key=lambda o: o["poly"].area)["poly"]
    if best < 0.5:
        issue("outline", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²) has no matching outline in zoneBoundaries" + (f" (best overlap {best:.0%})" if best else ""), room=r["id"])
    # labels
    inside = [l for l in labels if p.contains(Point(l["pt"]))]
    r["labels"] = [l["words"] for l in inside][:6]
    if r["type"] not in OPEN:
        if not inside:
            issue("label", r["type"], c, f"{r['type'][3:]} ({r['m2']} m²) has no label inside", room=r["id"])
    # neighbourhood
    z = max(zones, key=lambda z: z["poly"].intersection(p).area, default=None)
    r["zone"] = z["name"] if z and z["poly"].intersection(p).area > 0.5 * p.area else None

# overlaps between hover shapes: the cursor would light two rooms
for i in range(len(rooms)):
    for j in range(i + 1, len(rooms)):
        a, b = rooms[i], rooms[j]
        if not a["poly"].intersects(b["poly"]): continue
        ov = a["poly"].intersection(b["poly"]).area
        if ov < 5e5: continue                       # under 0.5 m2: a shared wall line
        small = min(a["poly"].area, b["poly"].area)
        inner = a if a["poly"].area < b["poly"].area else b
        outer = b if inner is a else a
        if ov > 0.95 * small and outer["type"] in OPEN:
            continue                                # a room drawn over an open area (the room wins on top): fine for hover if drawn last
        c = a["poly"].intersection(b["poly"]).representative_point().coords[0]
        issue("overlap", a["type"], c, f"{a['type'][3:]} ({a['m2']} m²) and {b['type'][3:]} ({b['m2']} m²) overlap by {ov / 1e6:.1f} m² ({ov / small:.0%} of the smaller)", room=a["id"], other=b["id"])

# rooms lying inside an open-area hatch: hover needs the room on top
for r in rooms:
    if r["type"] in OPEN: continue
    for o in rooms:
        if o["type"] in OPEN and o["poly"].intersection(r["poly"]).area > 0.95 * r["poly"].area:
            r["inside_open"] = o["type"]; break

# outlines with no room hatch
for o in outlines:
    if o["type"] in ("AC_GLAZING", "AC_FIRE_COMPARTMENTALISATION"): continue
    if not o.get("rooms"):
        c = o["poly"].representative_point().coords[0]
        issue("outline", o["type"], c, f"outline {o['type'][3:]} ({o['poly'].area / 1e6:.1f} m²) has no room hatch" + (" (not closed in CAD)" if o["open"] else ""))

# labels in no room
union = unary_union([r["poly"] for r in rooms])
for l in labels:
    if l["layer"] == "OB-I-ANNO-TEXT" and not union.contains(Point(l["pt"])):
        issue("label", l["layer"], l["pt"], f"label {l['words'][:40]!r} sits in no room hatch")

# ---------------------------------------------------------------- write
def ring(p): return [[round(x), round(y)] for x, y in p.exterior.coords]

# the hover shape: the room with its furniture cut out, as the hatch's islands have it. A hole that only keeps the fill
# clear of a label is filled back (the cursor on a room's name should light the room), and specks under 0.02 m2 are dropped.
label_pts = [Point(l["pt"]) for l in labels]
room_pts = [(r, r["poly"].representative_point()) for r in rooms]
# shapes already confirmed fine keep the shape that was checked
_ck = os.path.join(DIR, "checked.json")
CHECKED = json.load(open(_ck, encoding="utf-8")) if os.path.exists(_ck) else {"fine": [], "shapes": {}}
APPROVED = set(CHECKED.get("fine", []))
HATCH_EDGE = set(CHECKED.get("hatch_edge", []))      # shapes that keep their hatch's edge (outline runs over an unmarked wall)
FROZEN = {int(k): v for k, v in CHECKED.get("shapes", {}).items()}       # approved shapes, exactly as they were seen

# the furniture's footprint, from the base plan's furniture linework (desks, chairs and the figures in them, loose
# pieces): its lines are noded and polygonized into faces, and the faces, closed over small gaps, are the footprint
from shapely.geometry import LineString
from shapely.ops import polygonize
from shapely.strtree import STRtree
FURN = re.compile(r"FURN|\bFUR\b|_FUR_|CHAIR|TABLE|SEAT|SOFA|STORAGE|TV UNIT|^AC_WS_|OUTLINE (3 SEATER|CHAIR)|EQPM|MLWK-SURF", re.I)      # EQPM: pantry and kitchen equipment; MLWK-SURF: counters (not overhead or hidden millwork)
flines = [LineString(pts) for layer, col, kind, pts in expand("base") if kind == "s" and FURN.search(layer) and len(pts) >= 2]
ftree = STRtree(flines)
olines = [LineString(pts) for layer, col, kind, pts in expand("base") if kind == "s" and layer.upper() == "OUTLINE"
          and 3 <= len(pts) <= 12 and LineString(pts).length < 4000]
otree = STRtree(olines)
WALL = re.compile(r"WALL|PART|PRTN|GLS|GLASS|GLAZ|_PAR_|DOOR-FRAM|_DOR_|COLS|OUTLINE", re.I)
wlines = [LineString(pts) for layer, col, kind, pts in expand("base") if kind == "s" and WALL.search(layer) and len(pts) >= 2
          and not (layer.upper() == "OUTLINE" and LineString(pts).length < 4000)]   # small OUTLINE shapes are details, not walls
wtree = STRtree(wlines)
flor = [LineString(pts) for layer, col, kind, pts in expand("base") if kind == "s" and re.search(r"FLOR", layer, re.I) and len(pts) >= 2]
ftree2 = STRtree(flor)      # the slab edge along the façade: a console can stand against it
# structural columns (their solid fills): never floor
cols = [Polygon(it[0]).buffer(0) for layer, col, kind, it in expand("base") if kind == "f" and re.search(r"COLS|COLUMN", layer, re.I)]
ctree = STRtree(cols)
print(f"{len(flines)} furniture lines in the base plan")
EXTRA_LINES = {}       # per room, lines on layers that hold its furniture only there (a punch bag drawn on an elevation layer)
for _rid, _lays in CHECKED.get("furniture_layers", {}).items():
    EXTRA_LINES[int(_rid)] = set(_lays)
_extra_cache = {}
def extra_lines(lays):
    key = tuple(sorted(lays))
    if key not in _extra_cache:
        _extra_cache[key] = [L for L in (LineString(pts) for layer, col, kind, pts in expand("base")
                                         if kind == "s" and layer in lays and len(pts) >= 2) if L.length < 6000]   # pieces, not the building outline
    return _extra_cache[key]
def furniture_in(area, desk_ends=False, extra=()):
    """desk tops and chairs rarely close exactly (segments overlap or stop a few mm short), so the lines are thickened
    by 25 mm, which closes such gaps, and everything they enclose is filled: a piece's whole outline, or for a long run
    of furniture over 20 m2 the pockets inside it; then shrunk back by the 25 mm"""
    near = [flines[i] for i in ftree.query(area)] + [l for l in extra if l.intersects(area)]
    # a closed outline on a furniture layer that takes in most of the room is the room traced, not a piece in it
    near = [l for l in near if not (len(l.coords) >= 4 and math.dist(l.coords[0], l.coords[-1]) < 50
                                    and Polygon(l.coords).buffer(0).area > 0.7 * area.area)]
    if not near: return None
    # short shapes on OUTLINE that finish a piece (the pointed end of a desk drawn open as a U) join the furniture
    fl_tree = STRtree(near)
    if desk_ends: near += [o for o in (olines[i] for i in otree.query(area)) if len(fl_tree.query(o.buffer(20)))]
    mass = unary_union([l.buffer(25, 4) for l in near])
    out = []
    for p in parts(mass):
        whole = Polygon(p.exterior)
        out.append(whole if whole.area < 2e7 else Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > 2e7]))
    # a single outline drawn open (a table as one polyline whose ends don't meet) is closed if its gap is short for it
    ends = [olines[i] for i in otree.query(area)] if desk_ends else []      # short open shapes on OUTLINE (a desk's pointed end)
    for l in near + ends:
        c = list(l.coords)
        if len(c) < 3: continue
        gap = LineString([c[0], c[-1]])
        # ... or along another piece of furniture (the V of a desk's end, open where it meets the desk)
        touch = [flines[i].buffer(80) for i in ftree.query(gap.buffer(80)) if flines[i] is not l]
        if gap.length > 300 and touch and gap.intersection(unary_union(touch)).length > 0.8 * gap.length:
            pg = Polygon(c).buffer(0)
            if 1e4 < pg.area < 2e7: out.append(pg.buffer(25, 4)); continue
        # ... or if its open side runs along a wall (a console drawn as a U against the wall)
        along_wall = gap.length > 300 and any(w.buffer(80).contains(gap) for w in (wlines[i] for i in wtree.query(gap.buffer(80))))
        if len(c) >= 4 and (math.dist(c[0], c[-1]) < max(300, 0.15 * l.length) or along_wall):
            pg = Polygon(c).buffer(0)
            if 1e5 < pg.area < 2e7: out.append(pg.buffer(25, 4))
    # a console or counter against a wall is often drawn as its front edge alone: a straight furniture line over 1 m,
    # parallel to a wall 15-70 cm away, and the strip between them is the piece
    for l in near:
        c = list(l.coords)
        if len(c) != 2 or l.length < 1000: continue
        ang = math.atan2(c[1][1] - c[0][1], c[1][0] - c[0][0])
        best = None
        for w in [wlines[i] for i in wtree.query(l.buffer(700))] + [flor[i] for i in ftree2.query(l.buffer(700))] + [o for o in near if o is not l]:
            wc = list(w.coords)
            for a, b in zip(wc, wc[1:]):
                if math.dist(a, b) < 500: continue
                d_ang = abs((math.atan2(b[1] - a[1], b[0] - a[0]) - ang + math.pi / 2) % math.pi - math.pi / 2)
                seg = LineString([a, b]); dist = seg.distance(LineString(c))
                # truly parallel: the same gap at both ends of the line (a narrow V's arms converge), and not touching
                ends = [seg.distance(Point(c[0])), seg.distance(Point(c[1]))]
                if abs(ends[0] - ends[1]) > 60 or w.distance(l) < 100: continue
                if d_ang < math.radians(4) and 150 < dist < 700 and (best is None or dist < best[0]):
                    best = (dist, seg)
        if best:
            d, seg = best
            for side in (d, -d):
                strip = l.offset_curve(side)
                if not strip.is_empty and strip.distance(seg) < 30:
                    out.append(Polygon(list(c) + list(strip.coords)[::-1]).buffer(0).buffer(25, 4)); break
    # and back by the same 25 mm once filled: the cut-out follows the drawn line, not the thickened one
    return make_valid(unary_union(out).buffer(-25, 4)) if out else None
from shapely.validation import make_valid
def safe_diff(a, b):
    """a minus b; shapes this intricate can trip GEOS's noding, so retry on cleaned copies, then at a 1 mm grid"""
    try: return a.difference(b)
    except Exception:
        try: return make_valid(a.buffer(0)).difference(make_valid(b.buffer(0)))
        except Exception: return shapely.set_precision(a, 1).difference(shapely.set_precision(b, 1))
import shapely
def text_hole(hp):
    """is this hole the box AutoCAD keeps clear around a label's text?"""
    inside = [l for l in labels if hp.contains(Point(l["pt"]))]
    if not inside: return False
    if hp.area / hp.minimum_rotated_rectangle.area < 0.9: return False          # a box, not a round or angled object
    box = sum(len(max(l["words"].split("  ") or [""], key=len)) * 0.75 * l["h"] * (l["words"].count("  ") + 1) * 1.8 * l["h"] for l in inside)
    return hp.area < 4 * max(box, 1)                                             # no bigger than its words, give or take
DROP = set(CHECKED.get("drop", []))       # shapes that aren't in the design (a booth drawn twice): no hover at all
_drop_at = [(Point(q[0], q[1]), q[2]) for q in CHECKED.get("drop_at", [])]   # remembered by place and type, so a renumbered shape stays dropped
DROP |= {r["id"] for r in rooms if any(r["type"] == t and r["poly"].contains(q) for q, t in _drop_at)}
dropped = [r["poly"] for r in rooms if r["id"] in DROP]      # ... but still not the open area's floor around them
rooms = [r for r in rooms if r["id"] not in DROP]
solid = unary_union([r["poly"] for r in rooms if r["type"] not in OPEN])     # every enclosed room's footprint (a dropped shape's spot is the open area's floor)
def rings_of(g):
    """a (multi)polygon as [[exterior, hole, ...], ...] in whole mm. Holes too small to matter are dropped, and so is a hole
    lying inside another hole: the viewer fills even-odd, so a hole in a hole would show as floor again"""
    rd = lambda c: [[round(x), round(y)] for x, y in c]
    out = []
    for p in parts(make_valid(g) if not g.is_valid else g):
        if p.area <= 2e4: continue
        hs = [Polygon(h) for h in p.interiors if Polygon(h).area >= 2e4]
        hs = [h for h in hs if not any(o is not h and o.area > h.area and o.contains(h.representative_point()) for o in hs)]
        out.append([rd(p.exterior.coords)] + [rd(h.exterior.coords) for h in hs])
    return out
prev_by_id = {p["id"]: p for p in prev}
for r in rooms:
    if ONLY is not None and r["id"] not in ONLY and r["id"] in prev_by_id:
        old = prev_by_id[r["id"]]
        for k in ("rings", "holes", "hover_m2", "label_holes_refilled", "from_outline", "frozen"):
            if k in old: r[k] = old[k]
        if r["id"] in APPROVED and r["id"] not in FROZEN:     # just approved: freeze exactly what was on screen
            FROZEN[r["id"]] = {"rings": old["rings"], "hover_m2": old["hover_m2"]}; r["frozen"] = True
        continue
    holes, refilled = [], 0
    for h in r["fill"].interiors:
        hp = Polygon(h)
        if hp.area < 2e4: continue
        # a hole that only keeps the fill clear of a label: a rectangle about the size of the label's words, with no room
        # in it. A labelled piece of furniture (a punch bag, a swing chair) is a hole of its own shape and stays cut out.
        if text_hole(hp) and not any(o is not r and hp.contains(q) for o, q in room_pts):
            refilled += 1; continue
        # in an open area the hatch's small islands are furniture (often lumping a desk with what stands beside it):
        # the furniture is cut from the base plan instead, rooms are subtracted below; big holes (cores) stay
        if r["type"] in OPEN and hp.area < 2e7: continue
        if r["id"] in HATCH_EDGE: continue     # its furniture comes from the base plan; the hatch's islands (a table's slot) aren't trusted
        holes.append(hp)
    hover = Polygon(r["poly"].exterior.coords, [h.exterior.coords for h in holes]).buffer(0)
    if (r["type"] not in OPEN or r["type"] == "AC_WORKHALL") and r.get("outline_poly") is not None and r["id"] not in FROZEN             and r["id"] not in HATCH_EDGE:
        # the hatch stops at the walls' inner face, the outline runs outside them. Keep the hatch's edge, add back the
        # parts of the outline it missed that are wider than a wall (a corner behind a door, a notch where furniture
        # meets the wall) and drop its holes: text boxes stay in, the furniture is cut from the base plan below
        missed = safe_diff(r["outline_poly"], r["poly"])
        # never floor another room or open area already holds (a corridor along the façade inside a workhall's outline)
        _others = [o["poly"] for o in rooms if o is not r and o["poly"].intersects(missed)]
        if _others: missed = safe_diff(missed, unary_union(_others).buffer(5))
        # never past a wall: cut the missed parts along the base plan's walls, partitions and glass, and keep only the
        # pieces that touch the room directly. A wall's body lies behind its own line, so it never touches the room,
        # however thick; a strip beyond a partition doesn't either; slivers under 10 cm wide are dropped
        walls = [wlines[i] for i in wtree.query(missed)]
        if walls: missed = safe_diff(missed, unary_union([w.buffer(15, 2) for w in walls]))
        missed = missed.buffer(-50).buffer(50)
        keep = [q for q in parts(missed) if q.area > 2e4 and q.distance(r["poly"]) < 5]
        hover = unary_union([r["poly"], *[q.buffer(20).intersection(r["outline_poly"]) for q in keep]]).buffer(0)
        r["from_outline"] = True; refilled = 0
    if r["type"] == "AC_WORKHALL" and r["id"] not in FROZEN:
        # a workhall's hatch (and its outline) can stop short of the wall, leaving a strip that is nobody's floor: grow up
        # to 60 cm into floor no other room or open area holds, keeping only the pieces that run up to a wall line
        others = unary_union([o["poly"] for o in rooms if o is not r and o["poly"].distance(r["poly"]) < 700])
        grow = safe_diff(safe_diff(r["poly"].buffer(600, join_style=2), r["poly"]), others.buffer(5))
        walls = [wlines[i] for i in wtree.query(grow)]
        if walls:
            cut = safe_diff(grow, unary_union([w.buffer(15, 2) for w in walls]))
            wall_zone = unary_union([w.buffer(40, 2) for w in walls])
            def along_wall(q):
                """a real gap to a wall: a wall runs along the strip's far side for most of the length it shares with
                the workhall (a piece that merely grew 60 cm into open floor doesn't qualify)"""
                shared = q.boundary.intersection(r["poly"].buffer(25)).length
                walled = q.boundary.intersection(wall_zone).difference(r["poly"].buffer(25)).length
                return shared > 0 and walled >= 0.7 * shared
            strips = [q for q in parts(cut) if q.area > 1e5 and q.distance(r["poly"]) < 5 and along_wall(q)]
            if strips: hover = unary_union([hover] + [q.buffer(16, 2).intersection(grow) for q in strips]).buffer(0)
    fp = furniture_in(hover if r.get("from_outline") else r["poly"], desk_ends=r["type"] == "AC_WORKHALL",
                      extra=extra_lines(EXTRA_LINES[r["id"]]) if r["id"] in EXTRA_LINES else ())
    if fp is not None and r["id"] in HATCH_EDGE:
        # here a closed piece of the furniture that holds the room's own label is floor (a table's slot), not furniture
        lp = [q for q in label_pts if r["poly"].contains(q)]
        fl = [flines[i] for i in ftree.query(r["poly"])]
        slots = [f for f in polygonize(unary_union(fl)) if f.area < 4e6 and any(f.contains(q) for q in lp)] if lp else []
        if slots: fp = safe_diff(fp, unary_union(slots).buffer(-20))
    if fp is not None: hover = safe_diff(hover, fp)     # every desk, chair and loose piece, hatch islands or not
    cc = [cols[i] for i in ctree.query(hover)]
    if cc: hover = safe_diff(hover, unary_union(cc))
    if r["id"] not in FROZEN:
        # a wall's body (the thin face between its two lines, a curved one too) when a hatch runs over it
        # cut along every wall line: a wall's body (a curved one, or one open at its ends) falls away as a thin piece of
        # its own; keep the pieces wider than 30 cm and give back the cut
        wl = [wlines[i] for i in wtree.query(hover)]
        if wl:
            cut = safe_diff(hover, unary_union([w.buffer(15, 2) for w in wl]))
            wide = [q for q in parts(cut) if not q.buffer(-150).is_empty]
            if wide: hover = unary_union(wide).buffer(16, 2).intersection(hover)
        # and the loose bits a cut leaves behind
        hover = unary_union([q for q in parts(hover) if q.area >= 1e5]) if parts(hover) else hover
    if r["type"] in OPEN:
        hover = safe_diff(hover, solid)          # an open area never lights over a room, even where their hatches overlap
    if str(r["id"]) in CHECKED.get("add", {}):        # manual: floor the drawing can't tell apart (a slot drawn inside a table top)
        hover = unary_union([hover] + [Polygon(q).buffer(0) for q in CHECKED["add"][str(r["id"])]]).buffer(0)
    if str(r["id"]) in CHECKED.get("remove", {}):     # manual: area that isn't this room's floor
        hover = safe_diff(hover, unary_union([Polygon(q).buffer(0) for q in CHECKED["remove"][str(r["id"])]]))
    r["rings"] = rings_of(hover)
    if r["id"] in FROZEN:                         # approved: keep the shape that was checked
        r["rings"], r["frozen"] = FROZEN[r["id"]]["rings"], True
        hover = unary_union([Polygon(q[0], q[1:]).buffer(0) for q in r["rings"]])
    elif r["id"] in APPROVED:                     # approved but not yet frozen: freeze this shape
        FROZEN[r["id"]] = {"rings": r["rings"], "hover_m2": round(hover.area / 1e6, 2)}; r["frozen"] = True
    r["holes"] = [[[round(x), round(y)] for x, y in h.exterior.coords] for h in holes]
    r["hover_m2"] = round(hover.area / 1e6, 2)
    r["label_holes_refilled"] = refilled
out = {
    "rooms": [{k: v for k, v in r.items() if k not in ("poly", "fill", "outline_poly")} | {"shape": ring(r["poly"])} for r in rooms],
    "issues": issues,
    "summary": {"rooms": len(rooms), "by_type": dict(collections.Counter(r["type"] for r in rooms).most_common()),
                "outlines": len(outlines), "labels": len(labels), "issues": dict(collections.Counter(i["kind"] for i in issues))},
}
json.dump(out, open(os.path.join(DIR, "rooms.json"), "w", encoding="utf-8"), separators=(",", ":"))
CHECKED["shapes"] = {str(k): v for k, v in sorted(FROZEN.items())}
json.dump(CHECKED, open(_ck, "w", encoding="utf-8"), separators=(",", ":"))
out["summary"]["levels"] = dict(collections.Counter(i["kind"] + ":" + i["level"] for i in issues))
json.dump(out, open(os.path.join(DIR, "rooms.json"), "w", encoding="utf-8"), separators=(",", ":"))
print("issues", out["summary"]["levels"])
for i in issues:
    if i["level"] == "issue": print(f"  {i['kind']:8s} {i['layer'][:28]:28s} ({i['x']}, {i['y']})  {i['what']}")
