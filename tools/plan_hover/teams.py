"""Teams and their workstation seats, for team-wise hover.

The 09.10 drawings carry a space-plan layer set (MI_*). Team zones are the MI_ outlines that are not
rooms or services (MI_DELIVERY, MI_PRODUCT, MI_SALES, MI_SALES CALLING, MI_HR&FINANCE, MI_SOC); each
has a "<TEAM> <n> PAX" label inside it.

Seats: a workstation seat is a chair at a desk -
  desk block    a block holding one desk top and its chair (tuyu, zw$9964): 1 seat
  pod           a block holding a shared table with chairs nested in it (egrd, htd): 1 seat per chair
  chair block   a small chair block (dgb, zw$F9BB) within 0.7 m of a desk top, e.g. at the SOC desk rows
Chairs inside rooms (MI_ room outlines: meeting rooms, cafe, collab, ...) or away from any desk are not
workstation seats.

Assignment: seats inside a team zone go to that team; teams still short of their PAX headcount then take
the nearest unassigned seats (up to 12 m from the zone) until the headcount is met.

Highlight shape: the seat's real outline (chair, and the desk for desk blocks), plus the desk top, pod
table or desk-row segment it uses. Outlines are traced from the drawing's linework.

usage: python teams.py <in.dxf> <out_dir with full.svg>   -> out_dir/teams.json
"""
import sys, os, re, json, collections
import ezdxf
from ezdxf import path as zpath, bbox as zbbox
from shapely.geometry import Polygon, MultiPolygon, Point, LineString
from shapely.ops import polygonize, unary_union
from shapely import affinity, STRtree

SRC, OUT = sys.argv[1], sys.argv[2]
head = open(os.path.join(OUT, "full.svg"), encoding="utf-8").read(600)
OX = float(re.search(r'data-ox="(-?[\d.]+)"', head).group(1))
OY = float(re.search(r'data-oy="(-?[\d.]+)"', head).group(1))

doc = ezdxf.readfile(SRC)
for blk in doc.blocks:
    for sp in [e for e in blk if e.dxftype() == "SPLINE"]:
        try: sp.construction_tool()
        except Exception: blk.delete_entity(sp)
msp = doc.modelspace()
FROZEN = {l.dxf.name for l in doc.layers if l.is_frozen()}

NOT_TEAM = re.compile(r"PAX|_PB$|BOARD|CAFE|COLLAB|RECEPTION|SERVICE|WASHROOM|LIFT|AHU|PODCAST|CORRIDOR", re.I)
ROOM = re.compile(r"PAX|_PB$|BOARD|CAFE|COLLAB|RECEPTION|PODCAST|SERVICE|AHU|WASHROOM|LIFT", re.I)
NOT_WORKSTATION = re.compile(r"PLANT|TREE|PALM|LANDSCAPE|PART|WALL|DOOR|_DOR_|GLS|GLASS|ANNO|TAG|STOOL|LOOSE|POUF|SOFA|LOUNGE|OTTOMAN", re.I)
MIN_CHAIR_REPEATS = 5    # a loose chair type must recur to be a workstation seat (one-off chairs are not)
CHAIR_MAX = 800          # blocks up to this size are chairs
SEAT_TO_DESK = 700       # a chair this close to a desk top is a workstation seat
ASSIGN_REACH = 12000     # how far from its zone a short team may take seats
SKIP_T = ("TEXT", "MTEXT", "ATTDEF", "ATTRIB", "HATCH", "POINT", "WIPEOUT")
stats = collections.Counter()

def ring(e):
    # through ezdxf's path so arc segments (bulges) stay curved; get_points() would turn them into chords
    return Polygon([(v.x, v.y) for v in zpath.make_path(e).flattening(10)]).buffer(0)

zones, rooms = {}, []
for e in msp.query("LWPOLYLINE"):
    lay = e.dxf.layer
    if not lay.upper().startswith("MI"):
        continue
    g = ring(e)
    if not NOT_TEAM.search(lay):
        if g.area > 5e6:
            zones[lay] = zones[lay].union(g) if lay in zones else g
    elif ROOM.search(lay) and g.area > 0.5e6:
        rooms.append(g)
if not zones:
    print("no MI_ team zones in this drawing"); json.dump(dict(teams=[]), open(os.path.join(OUT, "teams.json"), "w")); sys.exit()
# enclosed rooms found from the walls (rooms.py) also count, for rooms the MI_ layers don't outline;
# only real rooms (< 150 m2), not the big open floor areas
def svg_poly(d):
    rings = [[(float(x) + OX, OY - float(y)) for x, y in (p.split() for p in part.split("L"))]
             for part in re.findall(r"M([^Z]+)Z", d)]
    return Polygon(rings[0], rings[1:]) if rings and len(rings[0]) >= 3 else None
rooms_json = os.path.join(OUT, "rooms.json")
if os.path.exists(rooms_json):
    for s in json.load(open(rooms_json))["spaces"]:
        if s.get("source", "walls") == "walls" and s["m2"] < 150 and s["name"]:     # named rooms only: an unnamed closed outline round a desk cluster is not a room
            g = svg_poly(s["d"])
            if g is not None and g.is_valid:
                rooms.append(g)
in_room = STRtree(rooms) if rooms else None
def inside_room(p):
    return in_room is not None and any(rooms[i].contains(p) for i in in_room.query(p))

# ---------- labels: "<TEAM> <n> PAX" ----------
labels = []
def all_entities(ents, depth=0):
    for e in ents:
        if e.dxftype() == "INSERT":
            if depth < 4:
                try: yield from all_entities(e.virtual_entities(), depth + 1)
                except Exception: pass
        else:
            yield e
for e in all_entities(msp):
    if e.dxftype() in ("TEXT", "MTEXT"):
        t = re.sub(r"\s+", " ", e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).strip()
        m = re.fullmatch(r"(.+?)\s*(\d+)\s*PAX", t, re.I)
        if m:
            labels.append((m.group(1).strip(" ,-"), int(m.group(2)), e.dxf.insert.x, e.dxf.insert.y))

# ---------- geometry helpers ----------
def is_wrapper(ins):
    blk = doc.blocks.get(ins.dxf.name)
    return blk is not None and sum(1 for x in blk if x.dxftype() == "INSERT") >= 20

def object_inserts(ents, parent="0"):
    for e in ents:
        if e.dxftype() != "INSERT":
            continue
        lay = e.dxf.layer; eff = parent if lay == "0" else lay
        if eff in FROZEN:
            continue
        if is_wrapper(e):
            yield from object_inserts(e.virtual_entities(), eff)
        else:
            yield e, eff

def size_of(e):
    b = zbbox.extents([e], fast=True)
    return max(b.size.x, b.size.y), b

def lines_of(entities, skip_chairs):
    out = []
    for e in entities:
        t = e.dxftype()
        if t == "INSERT":
            try:
                if not skip_chairs or size_of(e)[0] > CHAIR_MAX:
                    out += lines_of(e.virtual_entities(), skip_chairs)
            except Exception:
                pass
            continue
        if t in SKIP_T:
            continue
        try:
            # snapped to 1 mm so lines and arcs that should meet actually close
            pts = [(round(v.x), round(v.y)) for v in zpath.make_path(e).flattening(5)]
        except Exception:
            continue
        if len(pts) > 1 and len(set(pts)) > 1:
            out.append(LineString(pts))
    return out

def desk_like(g, max_depth, min_depth=450, min_len=900, min_area=0.3e6):
    """Bounding rectangle for near-rectangular shapes; for curved strips the rectangle with the same area
    and perimeter (exact for an annular sector, impossible for round shapes, which are rejected)."""
    if g.area < min_area:
        return False
    r = g.minimum_rotated_rectangle
    if g.area / r.area >= 0.8:
        c = list(r.exterior.coords)
        a, b = LineString(c[0:2]).length, LineString(c[1:3]).length
        lo, hi = min(a, b), max(a, b)
    else:
        half_p = g.length / 2
        disc = half_p * half_p - 4 * g.area
        if disc < 0:
            return False
        lo = (half_p - disc ** 0.5) / 2
        hi = half_p - lo
    return min_depth <= lo <= max_depth and hi >= min_len

def silhouette(lines):
    """Outer outline of a piece of furniture: its strokes thickened slightly, merged, holes filled."""
    if not lines:
        return None
    g = unary_union([l.buffer(15, quad_segs=2) for l in lines])
    parts = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    filled = unary_union([Polygon(p.exterior) for p in parts if p.area > 2e3])
    return filled.simplify(8) if not filled.is_empty else None

_desks, _sil, _kind = {}, {}, {}
def block_desks(name):
    if name not in _desks:
        blk = doc.blocks.get(name)
        faces = list(polygonize(unary_union(lines_of(blk, True)))) if blk is not None else []
        _desks[name] = [f for f in faces if desk_like(f, 2500)]
    return _desks[name]
def block_silhouette(name):
    if name not in _sil:
        blk = doc.blocks.get(name)
        _sil[name] = silhouette(lines_of(blk, False)) if blk is not None else None
    return _sil[name]
def block_kind(name, size):
    if name not in _kind:
        blk = doc.blocks.get(name)
        nested_chairs = 0
        for e in blk:
            if e.dxftype() == "INSERT":
                try:
                    if size_of(e)[0] <= CHAIR_MAX: nested_chairs += 1
                except Exception: pass
        if nested_chairs and block_desks(name):
            _kind[name] = "pod"
        elif block_desks(name) and size <= 1600:
            _kind[name] = "desk"
        elif size <= CHAIR_MAX:
            _kind[name] = "chair"
        else:
            _kind[name] = None
    return _kind[name]

def place(g, ins):
    m = ins.matrix44()
    o = m.transform((0, 0, 0)); ux = m.transform((1, 0, 0)) - o; uy = m.transform((0, 1, 0)) - o
    return affinity.affine_transform(g, [ux.x, uy.x, ux.y, uy.y, o.x, o.y])

# ---------- desk tops drawn loose at plan level (SOC rows, loose desks) ----------
def plan_entities(ents, parent="0"):
    for e in ents:
        if e.dxftype() == "INSERT":
            if is_wrapper(e):
                yield from plan_entities(e.virtual_entities(), e.dxf.layer)
            continue
        if not e.dxf.hasattr("layer"):   # proxy entities (the 14.10 drawing's arc-aligned text) carry no layer
            continue
        lay = e.dxf.layer
        yield e, parent if lay == "0" else lay
loose = [e for e, lay in plan_entities(msp) if not lay.upper().startswith("MI") and not NOT_WORKSTATION.search(lay)]
shared = []              # desk tops / pod tables / row segments that seats use
for f in polygonize(unary_union(lines_of(loose, True))):
    if desk_like(f, 700, 550, min_len=600, min_area=0.25e6):
        shared.append(f); stats["loose_desk_tops"] += 1

# ---------- seats ----------
seats = []               # dict(p=Point, shape=Polygon, shared=index into `shared` or None, src=name)
chair_candidates = []
extra = []               # chairs / headcount blocks that are only seats where a team hatch covers them
for ins, eff in object_inserts(msp):
    name = ins.dxf.name
    headcount_block = re.search(r"\d+\s*PAX", name, re.I) is not None    # "4PAX WITH PLANTER" is a table, not a plant
    if not headcount_block and (NOT_WORKSTATION.search(eff) or NOT_WORKSTATION.search(name)):
        # stools and loose seats are not workstations, but count where a team hatch covers them (hot desks)
        if re.search(r"STOOL|LOOSE|POUF", eff + " " + name, re.I):
            try:
                size, b = size_of(ins)
                sil = block_silhouette(name)
                if size <= CHAIR_MAX and sil is not None:
                    extra.append(dict(p=Point(b.center.x, b.center.y), shape=place(sil, ins), shared=None, src=name))
            except Exception:
                pass
        continue
    try:
        size, b = size_of(ins)
    except Exception:
        continue
    if not (300 <= size <= 5000):
        continue
    if headcount_block:
        # a block named with its headcount ("4PAX WITH PLANTER") seats exactly that many
        sil = block_silhouette(name)
        if sil is not None:
            extra.append(dict(p=Point(b.center.x, b.center.y), shape=place(sil, ins), shared=None, src=name,
                              n=int(re.search(r"(\d+)\s*PAX", name, re.I).group(1))))
        continue
    kind = block_kind(name, size)
    if kind == "desk":
        sil = block_silhouette(name)
        p = Point(b.center.x, b.center.y)
        if sil is not None and not inside_room(p):
            seats.append(dict(p=p, shape=place(sil, ins), shared=None, src=name))
    elif kind == "pod":
        tables = [place(f, ins) for f in block_desks(name)]
        first = len(shared); shared.extend(tables)
        for v in ins.virtual_entities():
            if v.dxftype() != "INSERT":
                continue
            try:
                vs, vb = size_of(v)
            except Exception:
                continue
            if vs <= CHAIR_MAX and block_silhouette(v.dxf.name) is not None:
                p = Point(vb.center.x, vb.center.y)
                if not inside_room(p):
                    near = min(range(first, len(shared)), key=lambda i: shared[i].distance(p)) if tables else None
                    seats.append(dict(p=p, shape=place(block_silhouette(v.dxf.name), v), shared=near, src=name))
    elif kind == "chair":
        chair_candidates.append((ins, b))
    else:
        # other furniture: only counted where a team hatch covers it (hot desks). A block named with a
        # headcount ("4PAX WITH PLANTER") seats that many; otherwise its nested chairs are the seats.
        m = re.search(r"(\d+)\s*PAX", name, re.I)
        sil = block_silhouette(name)
        if m and sil is not None:
            extra.append(dict(p=Point(b.center.x, b.center.y), shape=place(sil, ins), shared=None, src=name, n=int(m.group(1))))
        else:
            for v in ins.virtual_entities():
                if v.dxftype() != "INSERT":
                    continue
                try:
                    vs, vb = size_of(v)
                except Exception:
                    continue
                if vs <= CHAIR_MAX and block_silhouette(v.dxf.name) is not None:
                    extra.append(dict(p=Point(vb.center.x, vb.center.y), shape=place(block_silhouette(v.dxf.name), v),
                                      shared=None, src=name))

# a chair block is a workstation seat only next to a desk top (SOC rows, pods, desks), and not in a room;
# any other chair is kept aside in case a team hatch covers it (a hot desk)
tree = STRtree(shared) if shared else None
for ins, b in chair_candidates:
    p = Point(b.center.x, b.center.y)
    sil = block_silhouette(ins.dxf.name)
    if sil is None:
        continue
    seat = dict(p=p, shape=place(sil, ins), shared=None, src=ins.dxf.name)
    if not inside_room(p) and tree is not None:
        i = tree.nearest(p)
        if shared[i].distance(p) <= SEAT_TO_DESK:
            seat["shared"] = int(i); seats.append(seat); continue
    stats["chairs_not_at_desk"] += 1
    extra.append(seat)
# one-off chair types (a few chairs round a table) are not workstation seats, unless a hatch says so
chair_types = collections.Counter(s["src"] for s in seats if block_kind(s["src"], 0) == "chair")
extra += [s for s in seats if block_kind(s["src"], 0) == "chair" and chair_types[s["src"]] < MIN_CHAIR_REPEATS]
seats = [s for s in seats if block_kind(s["src"], 0) != "chair" or chair_types[s["src"]] >= MIN_CHAIR_REPEATS]
stats["one_off_chairs_dropped"] = sum(n for t, n in chair_types.items() if n < MIN_CHAIR_REPEATS)
for s in seats:
    s.setdefault("n", 1); s["hot"] = False
for s in extra:
    s.setdefault("n", 1); s["hot"] = True
stats["seats"] = len(seats)

# ---------- team hatches: the designer's own allocation (desks, chairs and hot-desk spots) ----------
# solid hatches on a team's MI_ layer, or a coloured (non-grey) hatch on layer 0 lying inside a team zone
hatch = collections.defaultdict(list)
for e, lay in plan_entities(msp):
    if e.dxftype() != "HATCH":
        continue
    color = e.dxf.get("true_color") or e.dxf.get("color", 256)
    try:
        polys = [Polygon([(v.x, v.y) for v in p.flattening(20)]).buffer(0) for p in zpath.from_hatch(e)]
    except Exception:
        continue
    g = unary_union([p for p in polys if p.area > 0])
    if g.is_empty or g.area < 1e6:
        continue
    team = lay if lay in zones else None
    if team is None and lay == "0" and color not in (7, 8, 9, 250, 251, 252, 253, 254, 255, 256):
        team = next((z for z, zg in zones.items() if zg.contains(g.representative_point())), None)
    if team:
        hatch[team].append(g)
hatch = {t: unary_union(gs) for t, gs in hatch.items()}
stats["hatched_teams"] = len(hatch)

HATCH_REACH = 450       # a chair pulled up to a hatched desk sits about this far from the desk edge
def hatch_for(seat):
    """The hatch covering most of the seat's outline (>= 20%); failing that, the nearest hatch within reach."""
    s = seat["shape"]
    best, frac = None, 0.2
    for lay, h in hatch.items():
        f = s.intersection(h).area / s.area if s.area > 0 else 0
        if f >= frac:
            best, frac = lay, f
    if best is None:
        near = [(h.distance(seat["p"]), lay) for lay, h in hatch.items()]
        d, lay = min(near) if near else (None, None)
        if d is not None and d <= HATCH_REACH:
            best = lay
    return best

# ---------- assign seats to teams ----------
order = sorted(zones, key=lambda l: -zones[l].area)
info = {}
for lay in order:
    z = zones[lay]
    inside = [l for l in labels if z.contains(Point(l[2], l[3]))]
    name, pax, lx, ly = inside[0] if inside else (lay[3:].replace("&", " & ").title(), None, *z.representative_point().coords[0])
    info[lay] = dict(name=name, pax=pax, x=lx, y=ly)
# stools drawn as plain circles (e.g. round a hatched high table), loose or inside a table block, are seats
# where a hatch claims them; circles that are part of a seat already counted (chair, person) are skipped
from ezdxf.disassemble import recursive_decompose
counted = STRtree([s["shape"] for s in seats + extra]) if seats or extra else None
near_hatch = unary_union([h.buffer(1000) for h in hatch.values()]) if hatch else None
def stool_circles():
    for e, lay in plan_entities(msp):
        if e.dxftype() == "CIRCLE" and not lay.upper().startswith("MI"):
            yield e
    for ins, eff in object_inserts(msp):
        try:
            size, b = size_of(ins)
        except Exception:
            continue
        if size < 5000 and near_hatch is not None and near_hatch.contains(Point(b.center.x, b.center.y)):
            for v in recursive_decompose([ins]):
                if v.dxftype() == "CIRCLE":
                    yield v
for e in stool_circles():
    if not 125 <= e.dxf.radius <= 350:
        continue
    c = e.ocs().to_wcs(e.dxf.center); p = Point(c.x, c.y)
    if near_hatch is None or not near_hatch.contains(p):
        continue
    if counted is not None and any(seats_extra.contains(p) for seats_extra in
                                   (( seats + extra)[i]["shape"] for i in counted.query(p))):
        continue
    extra.append(dict(p=p, shape=p.buffer(e.dxf.radius, quad_segs=8), shared=None, src="(stool)", n=1, hot=True))
    stats["stools"] += 1

# chairs exploded into loose lines (a chair block someone exploded in the DWG) next to a team hatch:
# drop long lines (desk edges), group the short pieces that touch, and keep chair-sized groups
def chair_blobs(pieces, src):
    """Group short pieces that touch; chair-sized groups (0.4-0.9 m, >= 15 pieces) are chairs."""
    if not pieces:
        return
    blobs = unary_union([l.buffer(40, quad_segs=2) for l in pieces])
    singles, multis = [], []
    for blob in (blobs.geoms if hasattr(blobs, "geoms") else [blobs]):
        r = blob.minimum_rotated_rectangle; c = list(r.exterior.coords)
        ext = max(LineString(c[0:2]).length, LineString(c[1:3]).length)
        n_pieces = sum(1 for l in pieces if blob.contains(l))
        if n_pieces < 15 or any(s["shape"].contains(blob.centroid) for s in seats + extra):
            continue
        if 400 <= ext <= 900:
            singles.append(blob)
        elif 900 < ext <= 2000:
            multis.append(blob)          # neighbouring chairs drawn touching each other
    # a merged group counts as as many chairs as its area holds, judged against the single chairs found here
    unit = sorted(b.area for b in singles)[len(singles) // 2] if singles else None
    for blob in singles:
        extra.append(dict(p=blob.centroid, shape=Polygon(blob.exterior).simplify(8), shared=None, src=src, n=1, hot=False))
        stats["exploded_chairs"] += 1
    for blob in multis:
        if unit:
            n = max(1, round(blob.area / unit))
            extra.append(dict(p=blob.centroid, shape=Polygon(blob.exterior).simplify(8), shared=None, src=src, n=n, hot=False))
            stats["exploded_chairs"] += n

def short_pieces(entities):
    out = []
    for e in entities:
        if e.dxftype() in SKIP_T or e.dxftype() == "INSERT":
            continue
        try:
            ls = LineString([(v.x, v.y) for v in zpath.make_path(e).flattening(10)])
        except Exception:
            continue
        if 0 < ls.length < 700:          # long lines are desk / table edges
            out.append(ls)
    return out

if near_hatch is not None:
    # loose furniture lines at plan level
    loose_furn = [e for e, lay in plan_entities(msp)
                  if not lay.upper().startswith("MI") and re.search(r"FURN", lay, re.I)]
    chair_blobs([l for l in short_pieces(loose_furn) if near_hatch.intersects(l)], "(exploded chair)")
    # chairs drawn as lines inside a furniture block a hatch covers (e.g. a table drawn with its chairs and
    # people, sitting on a glass layer): blocks not already giving seats, and not plants or partitions
    seat_sources = {s["src"] for s in seats + extra}
    for ins, eff in object_inserts(msp):
        name = ins.dxf.name
        if name in seat_sources or re.search(r"PLANT|TREE|PALM|PART|WALL", eff + " " + name, re.I):
            continue
        try:
            size, b = size_of(ins)
        except Exception:
            continue
        if 900 < size <= 5000 and near_hatch.contains(Point(b.center.x, b.center.y)):
            chair_blobs(short_pieces(recursive_decompose([ins])), f"(chairs drawn in {name})")

pool = seats + extra
owner = [None] * len(pool)
# 1. hatched teams: every seat its hatch covers, including hot desks
for k, s in enumerate(pool):
    owner[k] = hatch_for(s)
# 2. teams without a hatch (the SOC): workstation seats in the zone, then the nearest free ones up to PAX
count = collections.Counter()
for k, o in enumerate(owner):
    if o: count[o] += pool[k]["n"]
for k, s in enumerate(seats):
    if owner[k] is None:
        for lay in order:
            if lay not in hatch and zones[lay].contains(s["p"]):
                owner[k] = lay; count[lay] += s["n"]; break
in_zone = dict(count)
# top up to PAX from the nearest free seats: workstation seats, or chairs of a type the team already uses
# (SOC chairs just outside a zone outline that misses some rows), never a seat inside another team's zone
own_types = collections.defaultdict(set)
for k, o in enumerate(owner):
    if o and o not in hatch:
        own_types[o].add(pool[k]["src"])
other_area = {lay: unary_union([g for l2, g in zones.items() if l2 != lay] + [h for l2, h in hatch.items() if l2 != lay])
              for lay in order if lay not in hatch}
pairs = []
for k, s in enumerate(pool):
    if owner[k] is None:
        for lay in order:
            if lay in hatch or not info[lay]["pax"] or count[lay] >= info[lay]["pax"]:
                continue
            if k >= len(seats) and s["src"] not in own_types[lay]:
                continue
            if other_area[lay].contains(s["p"]):
                continue
            d = zones[lay].distance(s["p"])
            if d <= ASSIGN_REACH:
                pairs.append((d, k, lay))
for d, k, lay in sorted(pairs):
    if owner[k] is None and count[lay] < info[lay]["pax"]:
        owner[k] = lay; count[lay] += pool[k]["n"]
        pool[k]["hot"] = False                       # a regular seat of that team, just outside its outline
stats["unassigned_workstation_seats"] = sum(1 for k in range(len(seats)) if owner[k] is None)

# a hatched desk or bench with no chairs drawn: estimate its seats from its size
# (one per 1.05 m of length, both sides when it is 1 m or more deep)
SEAT_PITCH = 1050
for lay, h in hatch.items():
    mine = [pool[k]["p"] for k, o in enumerate(owner) if o == lay]
    for part in (h.geoms if hasattr(h, "geoms") else [h]):
        if part.area < 1e6 or any(part.buffer(HATCH_REACH).contains(p) for p in mine):
            continue
        r = part.minimum_rotated_rectangle; c = list(r.exterior.coords)
        a, b = LineString(c[0:2]).length, LineString(c[1:3]).length
        length, depth = max(a, b), min(a, b)
        n = int(length // SEAT_PITCH) * (2 if depth >= 1000 else 1)
        if n:
            pool.append(dict(p=part.representative_point(), shape=part, shared=None, src="(hatched bench, no chairs drawn)", n=n, hot=True))
            owner.append(lay); stats["estimated_bench_seats"] += n

def d_of(g):
    def r(coords):
        c = list(coords)[:-1]
        return "M" + "L".join(f"{round(x - OX)} {round(OY - y)}" for x, y in c) + "Z"
    gs = list(g.geoms) if hasattr(g, "geoms") else [g]
    return "".join(r(h.exterior.coords) + "".join(r(i.coords) for i in h.interiors) for h in gs if h.area > 0)

teams = []
for i, lay in enumerate(order):
    mine = [k for k, o in enumerate(owner) if o == lay]
    shapes = [pool[k]["shape"] for k in mine]
    shapes += [shared[j] for j in sorted({pool[k]["shared"] for k in mine if pool[k]["shared"] is not None})]
    if lay in hatch:
        shapes.append(hatch[lay])            # the hatch is the designer's outline of the team's furniture
    else:
        shapes.append(zones[lay])            # a team without a hatch (the SOC) is a room: highlight the room
    union = unary_union(shapes).simplify(5) if shapes else None
    t = info[lay]
    n_seats = sum(pool[k]["n"] for k in mine)
    n_hot = sum(pool[k]["n"] for k in mine if pool[k]["hot"])
    teams.append(dict(id=f"t{i + 1}", layer=lay, name=t["name"], pax=t["pax"], seats=n_seats, hot_desks=n_hot,
                      method="hatch" if lay in hatch else "zone",
                      sources=dict(collections.Counter(pool[k]["src"] for k in mine)),
                      m2=round(zones[lay].area / 1e6, 1), x=round(t["x"] - OX), y=round(OY - t["y"]),
                      zone=d_of(zones[lay]), desks=[d_of(union)] if union is not None else []))
json.dump(dict(source=os.path.basename(SRC), seats_total=len(seats), teams=teams), open(os.path.join(OUT, "teams.json"), "w"))
for t in teams:
    print(f"  {t['name']:16s} {str(t['pax']):>4} PAX | {t['seats']:3d} seats incl. {t['hot_desks']} hot desk [{t['method']}] {t['sources']}")
print(dict(stats))

# debugging aid: TEAM_DEBUG=<MI_ layer> lists every seat candidate within 1.5 m of that team's hatch
dbg = os.environ.get("TEAM_DEBUG")
if dbg and dbg in hatch:
    h = hatch[dbg]
    for k, s in enumerate(pool):
        d = h.distance(s["p"])
        if d <= 1500:
            cov = s["shape"].intersection(h).area / s["shape"].area if s["shape"].area else 0
            print(f"   seat {k:4d} {s['src']:28s} owner={owner[k]!s:18s} dist={d:5.0f} cover={cov:.2f} "
                  f"in_zone={zones[dbg].contains(s['p'])} at=({s['p'].x - OX:.0f},{OY - s['p'].y:.0f})")
