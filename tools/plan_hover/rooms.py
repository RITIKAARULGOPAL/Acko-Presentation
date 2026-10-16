"""Find the enclosed spaces in a DXF floor plan, for hover fills.

The drawings carry no room outlines or floor hatches, so spaces are derived from the walls:
  1. barrier lines: the building shell block, partition layers, door frames
  2. doors are drawn open, leaving a gap: each door swing arc (r 0.45-1.3 m, ~90 deg) adds the
     leaf in its closed position (and the open one, which the clean-up below absorbs)
  3. free floor = frame - buffered barriers; every piece not touching the frame is a space
  4. clean-up: drop slivers (wall cavities, stair treads), fill small holes (columns, fixtures)
  5. name each space from the room label text inside it

usage: python rooms.py <in.dxf> <out_dir with full.svg>   -> out_dir/rooms.json (+ rooms_debug.png)
"""
import sys, os, re, json, math, collections
import ezdxf
import shapely
from shapely.geometry import LineString, Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
from ezdxf import path as zpath, bbox as zbbox

SRC, OUT = sys.argv[1], sys.argv[2]
head = open(os.path.join(OUT, "full.svg"), encoding="utf-8").read(600)
OX = float(re.search(r'data-ox="(-?[\d.]+)"', head).group(1))
OY = float(re.search(r'data-oy="(-?[\d.]+)"', head).group(1))
W, H = map(float, re.search(r'viewBox="0 0 (\d+) (\d+)"', head).groups())

doc = ezdxf.readfile(SRC)
for blk in doc.blocks:
    for sp in [e for e in blk if e.dxftype() == "SPLINE"]:
        try: sp.construction_tool()
        except Exception: blk.delete_entity(sp)
VIS = {l.dxf.name for l in doc.layers if l.is_on() and not l.is_frozen()}
FROZEN = {l.dxf.name for l in doc.layers if l.is_frozen()}

SHELL_MIN_SIZE = 20000          # a block this big (mm) is the base building drawing
BARRIER_RX = re.compile(r"PART|WALL|GLS|GLASS PARTITION|_PAR_|DOOR|_DOR_|COLS|COLUMN", re.I)
SEAT_RX = re.compile(r"FURN|CHAIR|TABLE|PEOPLE", re.I)

def layer_of(e):
    return e.dxf.get("layer", "0") if e.dxf.is_supported("layer") else "0"

# Each "object" block (the first block below model space, or below a wrapper block that holds the
# whole plan) is classified once:
#   shell     - the base building drawing (> 20 m across)
#   furniture - sits on a wall/door layer but is thousands of pieces (a table with people), not a wall
#   block     - anything else
FURNITURE_MIN_PIECES = 300
WRAPPER_MIN_INSERTS = 20

def is_wrapper(ins):
    blk = doc.blocks.get(ins.dxf.name)
    return blk is not None and sum(1 for x in blk if x.dxftype() == "INSERT") >= WRAPPER_MIN_INSERTS

def count_pieces(ins, limit):
    n, stack = 0, [ins]
    while stack and n <= limit:
        for v in stack.pop().virtual_entities():
            if v.dxftype() == "INSERT": stack.append(v)
            else: n += 1
    return n

SHELL_MIN_PIECES = 1500          # the shell is thousands of pieces; a furniture group with one stray far-off
                                 # piece can also be > 20 m across, so size alone isn't enough
def classify(ins, eff):
    try:
        b = zbbox.extents([ins], fast=True)
        if max(b.size.x, b.size.y) > SHELL_MIN_SIZE and count_pieces(ins, SHELL_MIN_PIECES) > SHELL_MIN_PIECES:
            return "shell"
    except Exception:
        pass
    if BARRIER_RX.search(eff) and count_pieces(ins, FURNITURE_MIN_PIECES) > FURNITURE_MIN_PIECES:
        return "furniture"
    return "block"

stats = collections.Counter()
def walk(ents, parent="0", kind=None):
    """Yields (entity, effective layer, kind); kind is None for loose geometry at plan level."""
    for e in ents:
        lay = layer_of(e); eff = parent if lay == "0" else lay
        if e.dxf.is_supported("invisible") and e.dxf.get("invisible", 0):
            continue
        if e.dxftype() == "INSERT":
            if eff in FROZEN: continue
            if kind is None and is_wrapper(e):
                stats["wrapper_blocks_opened"] += 1
                sub = None                       # look through: its contents are plan level
            else:
                sub = kind if kind is not None else classify(e, eff)
                stats["blocks_" + sub] += kind is None
            try:
                yield from walk(e.virtual_entities(), eff, sub)
            except Exception:
                pass
        else:
            yield e, eff, kind

lines, door_leaves, labels = [], [], []
for e, eff, kind in walk(doc.modelspace()):
    if eff not in VIS:
        continue
    t = e.dxftype()
    if t in ("TEXT", "MTEXT", "ATTRIB"):
        txt = e.plain_text() if t == "MTEXT" else e.dxf.text
        txt = re.sub(r"\s+", " ", txt or "").strip()
        # skip block-name text left on the plan (e.g. "TABLE_MEETING ROOM_RECTANGLE_01")
        if txt and "_" not in txt:
            p = e.dxf.insert
            labels.append((txt, p.x, p.y, e.dxf.get("char_height" if t == "MTEXT" else "height", 0) or 0))
        continue
    in_shell = kind == "shell"
    if kind == "furniture":
        continue
    # walls also get sketched straight onto layer 0 outside any block (e.g. the podcast / server room walls)
    loose_wall = kind is None and eff == "0" and t in ("LINE", "LWPOLYLINE", "POLYLINE")
    is_barrier = in_shell or loose_wall or bool(BARRIER_RX.search(eff))
    # door swing: an arc of door radius sweeping ~90 deg, on a door/partition layer or in the shell
    if t == "ARC" and is_barrier:
        sweep = (e.dxf.end_angle - e.dxf.start_angle) % 360
        if 450 <= e.dxf.radius <= 1300 and 75 <= sweep <= 105:
            c = e.ocs().to_wcs(e.dxf.center)       # mirrored doors store the centre in a flipped OCS
            for q in (e.start_point, e.end_point):  # these two are already in WCS
                door_leaves.append(LineString([(c.x, c.y), (q.x, q.y)]))
            stats["door_arcs"] += 1
            continue
    if not is_barrier:
        continue
    try:
        if t == "HATCH":
            paths = zpath.from_hatch(e)
        else:
            paths = [zpath.make_path(e)]
    except Exception:
        continue
    for p in paths:
        pts = [(v.x, v.y) for v in p.flattening(10)]
        if len(pts) >= 2 and len(set(pts)) > 1:
            ls = LineString(pts)
            if loose_wall and ls.length < 300:
                continue
            lines.append(ls); stats["shell" if in_shell else "loose_layer0" if loose_wall else "partition"] += 1

print("barriers:", dict(stats), "labels:", len(labels))

# ---------- free floor ----------
WALL_HALF = 30                       # buffered line half-width (mm)
barrier = unary_union([shapely.buffer(l, WALL_HALF, quad_segs=2) for l in lines + door_leaves])
# the plan frame from full.svg (already cropped of stray far-off objects)
frame = box(OX, OY - H, OX + W, OY)
free = frame.difference(barrier)
parts = list(free.geoms) if isinstance(free, MultiPolygon) else [free]
outer = frame.exterior.buffer(2000)

spaces = []
for g in parts:
    if g.intersects(outer):          # the outside of the building
        continue
    # close notches left by open door leaves and wall stubs (< 2 x 90 mm wide)
    g = g.buffer(90, quad_segs=2).buffer(-90, quad_segs=2)
    if g.is_empty:
        continue
    g = max(g.geoms, key=lambda h: h.area) if isinstance(g, MultiPolygon) else g
    if g.area < 1.0e6 or g.buffer(-200).is_empty:      # < 1 m2, or thinner than 0.4 m
        stats["dropped_small_or_thin"] += 1
        continue
    holes = [r for r in g.interiors if Polygon(r).area >= 2.0e6]     # keep cores/shafts, fill columns & fixtures
    g = Polygon(g.exterior, holes).simplify(5)
    spaces.append(g)

# furniture drawn as closed shapes (a meeting table on a partition layer) leaves an "island" space inside a
# room, often with the room's "6 PAX" label sitting on it. An island inside a small room (< 50 m2) is
# folded back into that room (its label then names the room). Islands in the big open floor are kept:
# those are phone booths and pods.
# A table pushed against a wall isn't a true island: the room wraps around it. So the test is how much
# of the small space's outline runs along one host room (>= 75%; a real neighbouring room shares one wall).
islands = set()
for i, g in enumerate(spaces):
    if g.area >= 8.0e6:
        continue
    edge = g.exterior
    for j, host in enumerate(spaces):
        if j == i or j in islands or host.area >= 50e6 or g.area > 0.5 * host.area:
            continue
        shared = edge.intersection(host.buffer(160)).length / edge.length
        if shared >= 0.75:
            islands.add(i)
            merged = unary_union([host.buffer(100, quad_segs=2), g.buffer(100, quad_segs=2)]).buffer(-100, quad_segs=2)
            merged = max(merged.geoms, key=lambda h: h.area) if isinstance(merged, MultiPolygon) else merged
            spaces[j] = Polygon(merged.exterior, [r for r in merged.interiors if Polygon(r).area >= 2.0e6]).simplify(5)
            break
stats["furniture_islands_merged"] = len(islands)
spaces = [g for i, g in enumerate(spaces) if i not in islands]

# ---------- names from label text ----------
def label_for(g):
    inside = [(h, t) for t, x, y, h in labels if g.contains(Point(x, y))]
    if not inside:
        return ""
    inside.sort(key=lambda ht: -ht[0])
    seen, out = set(), []
    for h, t in inside:
        if t.upper() not in seen and not re.fullmatch(r"[\d.\s-]+|[A-Z]\d*|P\d+", t, re.I):
            seen.add(t.upper()); out.append(t)
    return " / ".join(out[:3])

def d_of(g):
    def ring(r):
        c = list(r.coords)[:-1]
        return "M" + "L".join(f"{round(x - OX)} {round(OY - y)}" for x, y in c) + "Z"
    return "".join(ring(p.exterior) + "".join(ring(r) for r in p.interiors)
                   for p in (g.geoms if hasattr(g, "geoms") else [g]))

# ---------- MI_ room outlines (the 09.10 space-plan layers) take precedence over wall-derived spaces ----------
# Each MI_ room layer gives a room type; service / collab / boardroom pieces are named from their own label.
# Team zones (MI_DELIVERY, ...) are team hovers, not rooms. Wall-derived spaces are kept only where no MI_
# outline or team zone covers them (e.g. a boardroom or cafe the MI_ layers don't outline).
MI_TEAM = re.compile(r"DELIVERY|PRODUCT|SALES|HR&|_SOC$", re.I)
MI_TYPE = [(r"PB$", "Phone booth"), (r"(\d+)\s*PAX", "Meeting room · {} PAX"), (r"AHU", "AHU room"),
           (r"LIFT", "Lift lobby"), (r"PODCAST", "Podcast room"), (r"RECEPTION", "Reception & waiting lounge"),
           (r"WASHROOM", "Washrooms"), (r"CAFE", "Cafeteria"), (r"CORRIDOR", "Corridor"),
           (r"BOARDROOM", "Boardroom"), (r"COLLAB", "Collaboration area"), (r"SERVICE", "Service room")]
OWN_LABEL = re.compile(r"SERVICE|COLLAB", re.I)      # these are better named by the label written in them
NOISE = re.compile(r"x|y|TV|MHS|ACD|SMR\d+|R\d+|P\.?\s*B\s*-?\s*\d*.*|STORAGE|\d+\s*PAX|.*\d+\s*PAX|[\d.\s-]+", re.I)

def mi_name(layer, g):
    base = next((fmt.format(*re.search(rx, layer, re.I).groups()) for rx, fmt in MI_TYPE if re.search(rx, layer, re.I)),
                layer[3:].replace("_", " ").title())
    own = [t for t, x, y, h in sorted(labels, key=lambda l: -l[3]) if g.contains(Point(x, y)) and not NOISE.fullmatch(t.strip())]
    own = list(dict.fromkeys(re.sub(r"\bPax\b", "PAX", o.title()) if o.isupper() else o for o in own))
    if own and (OWN_LABEL.search(layer) or (base == "Boardroom" and g.area < 20e6)):
        return " / ".join(own[:2])
    return base

mi_rooms, mi_cover, team_zones = [], [], []
for e in doc.modelspace().query("LWPOLYLINE"):
    lay = e.dxf.layer
    if not lay.upper().startswith("MI"):
        continue
    # through ezdxf's path so arc segments (bulges) stay curved; get_points() would turn them into chords
    g = Polygon([(v.x, v.y) for v in zpath.make_path(e).flattening(10)]).buffer(0)
    if g.is_empty or g.area < 0.5e6:
        continue
    g = max(g.geoms, key=lambda h: h.area) if isinstance(g, MultiPolygon) else g
    mi_cover.append(g)
    if MI_TEAM.search(lay):
        team_zones.append(g)
    else:
        mi_rooms.append((lay, g))

# MI_CORRIDOR is drawn loosely: one outline is really the open-plan workspace round the team zones, and the
# others run across desks. Team furniture (from teams.json, when teams.py has run) is cut out of corridors.
teams_json = os.path.join(OUT, "teams.json")
team_furniture = []
if os.path.exists(teams_json):
    for t in json.load(open(teams_json)).get("teams", []):
        for d in t.get("desks", []):
            for part in re.findall(r"M([^Z]+)Z", d):
                pts = [(float(x) + OX, OY - float(y)) for x, y in (p.split() for p in part.split("L"))]
                if len(pts) >= 3:
                    team_furniture.append(Polygon(pts).buffer(0))
teams_area = unary_union(team_zones) if team_zones else None
# cut at the exact furniture edge: a margin (buffer) rounds corners and leaves white bumps along desk ends
corridor_mask = unary_union(team_zones + team_furniture) if (team_zones or team_furniture) else None
# an outer corridor is drawn as a solid outline round the inner one: cut it back to its ring first
corr = [(i, g) for i, (lay, g) in enumerate(mi_rooms) if re.search(r"CORRIDOR", lay, re.I)]
for i, g in corr:
    inner = [h for j, h in corr if j != i and h.area < g.area and h.intersection(g).area >= 0.8 * h.area]
    if inner:
        mi_rooms[i] = (mi_rooms[i][0], g.difference(unary_union(inner)).buffer(-5).buffer(5))
kept = []
for lay, g in mi_rooms:
    if re.search(r"CORRIDOR", lay, re.I) and teams_area is not None:
        if g.intersection(teams_area).area >= 0.3 * g.area:
            stats["corridor_outlines_that_are_workspace"] += 1      # open-plan workspace, not a room
            continue
        if corridor_mask is not None:
            g = g.difference(corridor_mask).buffer(-5).buffer(5)
            if g.is_empty:
                continue
    kept.append((lay, g))
mi_rooms = kept
stats["mi_rooms"] = len(mi_rooms)

def tidy(name):
    """Clean a wall-derived name: drop noise labels, 'N PAX' alone becomes a meeting room, title case."""
    parts = []
    for p in (name.split(" / ") if name else []):
        p = p.strip()
        m = re.fullmatch(r"(\d+)\s*PAX", p, re.I)
        if m:
            parts.append(f"Meeting room · {m.group(1)} PAX")
        elif not re.fullmatch(r"x|y|TV|MHS|ACD|SMR\d+|R\d+|DROPDOWN SCREEN|[\d.\s-]+", p, re.I):
            parts.append(re.sub(r"\bPax\b", "PAX", p.title()) if p.isupper() else p)
    return " / ".join(dict.fromkeys(parts))

entries = []
if mi_rooms:
    covered = unary_union(mi_cover)
    for lay, g in mi_rooms:
        entries.append((g, mi_name(lay, g), "MI", lay))
    for g in spaces:
        if g.intersection(covered).area < 0.3 * g.area:        # a room the MI_ layers don't outline
            entries.append((g, tidy(label_for(g)), "walls", ""))
        else:
            stats["wall_spaces_replaced_by_MI"] += 1
else:
    entries = [(g, tidy(label_for(g)), "walls", "") for g in spaces]

# make spaces disjoint: an outline drawn around smaller ones (the corridor round the open areas, a corridor
# round a collab corner) is cut back so hovering it lights only its own floor
entries.sort(key=lambda en: en[0].area)
taken, carved = None, []
for g, name, source, layer in entries:
    own = g.difference(taken) if taken is not None else g
    own = own.buffer(-5).buffer(5)                   # drop slivers left along shared edges
    if own.is_empty or own.area < 0.3e6:
        stats["swallowed_by_smaller"] += 1
        continue
    if isinstance(own, MultiPolygon):
        own = MultiPolygon([p for p in own.geoms if p.area > 0.3e6]) if any(p.area > 0.3e6 for p in own.geoms) else own
    carved.append((own, name, source, layer))
    taken = g if taken is None else unary_union([taken, g])
entries = carved
entries.sort(key=lambda en: -en[0].area)          # small ones last, so they sit on top for hovering
out = []
for i, (g, name, source, layer) in enumerate(entries):
    c = g.representative_point()
    out.append(dict(id=f"s{i + 1}", name=name, m2=round(g.area / 1e6, 1), source=source, layer=layer,
                    x=round(c.x - OX), y=round(OY - c.y), d=d_of(g)))
json.dump(dict(source=os.path.basename(SRC), count=len(out), spaces=out), open(os.path.join(OUT, "rooms.json"), "w"), indent=0)
# debug picture: barriers grey, spaces coloured with their id
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(24, 13)); ax.set_aspect("equal"); ax.axis("off")
for l in lines + door_leaves:
    x, y = l.xy; ax.plot(x, y, lw=0.3, color="#888")
for l in door_leaves:
    x, y = l.xy; ax.plot(x, y, lw=0.8, color="#06c")
cmap = plt.get_cmap("tab20")
for i, g in enumerate(spaces):
    x, y = g.exterior.xy; ax.fill(x, y, color=cmap(i % 20), alpha=0.55, lw=0)
    c = g.representative_point(); ax.text(c.x, c.y, f"s{i + 1}", fontsize=6, ha="center")
fig.savefig(os.path.join(OUT, "rooms_debug.png"), dpi=110, bbox_inches="tight")
if "--crop" in sys.argv:
    x0, y0, x1, y1 = map(float, sys.argv[sys.argv.index("--crop") + 1].split(","))
    ax.set_xlim(x0 + OX, x1 + OX); ax.set_ylim(OY - y1, OY - y0)
    for t, x, y, h in labels:
        if x0 + OX <= x <= x1 + OX and OY - y1 <= y <= OY - y0:
            ax.text(x, y, t, fontsize=7, color="#c00")
    fig.savefig(os.path.join(OUT, "rooms_debug_crop.png"), dpi=110, bbox_inches="tight")
named = sum(1 for s in out if s["name"])
print(f"{len(out)} spaces ({named} named), total {sum(s['m2'] for s in out):,.0f} m2", dict(stats))
for s in out[:60]:
    print(f"  {s['id']:>4} {s['m2']:8.1f} m2  {s['name'][:60]}")
