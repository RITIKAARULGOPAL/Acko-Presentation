# Turn the flattened test-fit DXF (dxf_dump.py → dump.pkl) into axo.json: plan-space shapes in metres,
# each tagged with how it is built in 3D (floor tint, glass room, core mass, wall, furniture, plant, façade).
# Usage: python3 extract_axo.py dump.pkl axo.json
import sys, json, math, pickle, collections
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep

D = pickle.load(open(sys.argv[1], 'rb'))
OUT = sys.argv[2]
XO, YO = -177000, -373500                       # same origin as tools/testfit/extract.py
def M(p, dy=0): return ((p[0]-XO)/1000, (YO-(p[1]+dy))/1000)   # mm → plan metres, y down
NEIGH_DY = -53268                               # AC_NEIGH panel sits above the layout (checked against the plate below)
EXIT_DY = 55301                                 # AC_FIRE_EXIT panel sits below it

def r2(v): return round(v, 2)
def ring(g):
    g = g.simplify(0.02)
    return [[r2(x), r2(y)] for x, y in list(g.exterior.coords)[:-1]]
def rings(g):
    """Exterior first, then holes: walls that close around a room stay hollow."""
    g = g.simplify(0.02)
    return [[[r2(x), r2(y)] for x, y in list(r.coords)[:-1]] for r in [g.exterior, *g.interiors]]
def polys(g):
    if g.is_empty: return []
    return [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.geom_type == 'Polygon' and not p.is_empty]
def closed(pts):
    P = Polygon(pts)
    if not P.is_valid: P = P.buffer(0)
    return P

paths = D['paths']; inserts = D['inserts']
INS = {i[0]: i for i in inserts}

# ---------- space outlines (AC_* layers in model space) ----------
ROOM = {'AC_PHONE_BOOTH':'booth','AC_QUICK_SPIRIT':'sprint','AC_COLLAB_HUDDLE':'huddle','AC_DEPARTMENTAL_ROOMS':'dept',
        'AC_EXECUTIVE_CORNER_CABIN':'cabin','AC_ZEN_ROOM':'zen','AC_PRAYER_ROOM':'prayer',"AC_MOTHER'S_ROOM":'mother',
        'AC_BOARD_ROOM':'board','AC_THE_HATCHERY':'hatchery','AC_THE_STUDIO_ROOM':'studio','AC_VISITOR_HUB':'visitor',
        'AC_HUB_ROOM':'hub','AC_TRAINING_ROOM':'training'}
CORE = {'AC_OUT_OF_SCOPE':'out','AC_WASHROOM':'washroom','AC_AHU':'ahu','AC_UPS_SERVER_BATTERY_BMS_ROOM':'ups',
        'AC_FIRE_EXIT_STAIRCASE':'stair','AC_LIFT_LOBBY':'lift'}
ZONE = {'AC_WORKHALL':'work','AC_CORRIDOR':'corridor','AC_COLLAB':'collab','AC_COFFEE_CORNER':'coffee',
        'AC_CAFETERIA':'cafe','AC_RECEPTION':'reception','AC_ENTRY':'entry'}
spaces = collections.defaultdict(list); neigh = []; exits = []; glazing = None
for lay, t, ch, pts in paths:
    if ch or not lay.startswith('AC_') or len(pts) < 3: continue
    if lay == 'AC_NEIGH': neigh.append(closed([M(p, NEIGH_DY) for p in pts])); continue
    if lay == 'AC_FIRE_EXIT': exits.append([[r2(a), r2(b)] for a, b in (M(p, EXIT_DY) for p in pts)]); continue
    if lay == 'AC_GLAZING': glazing = closed([M(p) for p in pts]); continue
    kind = ROOM.get(lay) or CORE.get(lay) or ZONE.get(lay)
    if not kind: continue
    for P in polys(closed([M(p) for p in pts])):
        if P.area > 0.5: spaces[(('room' if lay in ROOM else 'core' if lay in CORE else 'zone'), kind)].append(P)
print('spaces', {f'{a}:{b}': len(v) for (a, b), v in sorted(spaces.items())})

# ---------- the slab, terraces, façade ----------
slab = glazing
# terraces: the notches cut into the south edge of the glazing line, closed off along the façade line
south = max(y for x, y in glazing.exterior.coords)
notches = polys(box(*glazing.bounds).difference(glazing).intersection(box(glazing.bounds[0], south-12, glazing.bounds[2], south)))
terraces = [n for n in notches if n.area > 50 and abs(n.bounds[3]-south) < 0.05 and n.area > 0.95*box(*n.bounds).area]   # rectangular notches only, not the slanted west end
print('terraces', [[r2(v) for v in t.bounds] for t in terraces])
assert neigh and abs(max(p.bounds[1] for p in neigh) - max(p.bounds[1] for p in [slab])) < 40, 'AC_NEIGH shift looks wrong'

# neighbourhood ids: same parcels as test fit 02 (N01–N06 west→east, R1/R2 the two receptions)
neigh.sort(key=lambda p: p.area, reverse=True)
small = sorted(neigh[-2:], key=lambda p: p.centroid.x)                  # the two reception parcels
big = sorted(neigh[:-2], key=lambda p: p.centroid.x)
NB = {f'N{i+1:02d}': p for i, p in enumerate(big)}; NB['R1'], NB['R2'] = small
print('neighbourhoods', {k: round(p.area, 1) for k, p in NB.items()})

# ---------- fit-out geometry by group ----------
SKIP_LAYERS = {'OB-I-SHADE60','OB-I-SHADE40','OB-I-ELEV-1','A-ELEV 5','N-HATCH','HATCH-PLINES','AI-ANNO-DIM','I-PART-TEXT',
               'OB-I-ANNO-TEXT','I-FLOR','Defpoints','I-DT-METL','pline','h','RAILING','A-SYM-FURN','Lag 1'}
def is_part(l): return any(s in l for s in ('PART', 'WALL', 'GLASS')) or l == 'I_PAR_PA_IN_GL'
def is_glass(l): return any(s in l for s in ('GLS', 'GLSS', 'GLASS', '_GL'))
def is_plant(l, names): return any(s in l for s in ('Plant', 'PLNT', 'PLANT')) or any(n.startswith(('TREE', 'Clump')) for n in names)
PLANT_BLOCKS = {'A$C396F796F', 'A$C143125F4'}
walls_g = []; walls_s = []; furn = collections.defaultdict(list); plant = collections.defaultdict(list)
cols = []
for lay, t, ch, pts in paths:
    if not ch or len(ch) < 1 or ch[0][1] != 'AFAFAF': continue
    if 'DOOR' in lay or lay.startswith('I_DOR') or lay in SKIP_LAYERS or lay.endswith(('LENGTH', 'WIDTH', 'POSITION')): continue
    names = [n for _, n in ch[1:]]
    Q = [M(p) for p in pts]
    if names and names[0] == 'base':
        if lay == 'S-COLS': cols.append(Q)
        continue
    if is_part(lay): (walls_g if is_glass(lay) else walls_s).append(Q); continue
    gid = ch[1][0] if len(ch) > 1 else None
    if is_plant(lay, names) or (names and names[0] in PLANT_BLOCKS): plant[gid if gid is not None else ('loose',)].append(Q); continue
    furn[gid if gid is not None else 'loose'].append(Q)

def wall_strips(lines, th):
    U = unary_union([LineString(q).buffer(th/2, cap_style=2, join_style=2) for q in lines if len(q) > 1 and LineString(q).length > 0.25])
    return [rings(p) for p in polys(U) if p.area > 0.03]
walls = {'glass': wall_strips(walls_g, 0.06), 'solid': wall_strips(walls_s, 0.1)}
print('walls', {k: len(v) for k, v in walls.items()})

# columns: closed rectangles in S-COLS
cu = unary_union([LineString(q).buffer(0.02) for q in cols if len(q) > 1])
colp = [Polygon(h) for p in polys(cu) for h in p.interiors] + [Polygon(p.exterior) for p in polys(cu)]
colp = [c for c in unary_union([c.buffer(0.02) for c in colp if 0.1 < c.area < 4]).geoms] if colp else []
print('columns', len(colp))

def pieces(lines, gap=0.03):
    """Closed furniture outlines → solid footprints. Lines are fattened by `gap` so near-misses close."""
    ls = [LineString(q) for q in lines if len(q) > 1 and LineString(q).length > 0.05]
    if not ls: return []
    U = unary_union([l.buffer(gap, join_style=2) for l in ls])
    out = []
    for p in polys(U):
        for h in p.interiors:                               # every enclosed outline is one piece: a desk top, a chair, a table
            out += polys(Polygon(h).buffer(gap*0.5, join_style=2))
    # chairs are often drawn as open arcs or as a seated figure: a small cluster of strokes left outside
    # every piece becomes a seat, centred on the part of the cluster that is not over a table
    out = [p for p in out if p.area > 0.06]               # drop the little closed loops inside figures (heads, hands)
    tables = [p for p in out if p.area > 0.3]
    solid = unary_union(tables).buffer(0.04) if tables else Polygon()
    rest = [l for l in ls if solid.is_empty or not solid.contains(l.representative_point())]
    for c in polys(unary_union([l.buffer(0.12) for l in rest])) if rest else []:   # a seat's arcs and figure join into one cluster
        x0, y0, x1, y1 = c.bounds
        if 0.4 < math.hypot(x1-x0, y1-y0) < 1.7:
            free = c.convex_hull.difference(solid)
            if free.area > 0.06 and not any(p.contains(free.centroid) for p in out):
                out.append(free.centroid.buffer(0.25, resolution=2))
    return out

def classify(P):
    a = P.area; r = P.minimum_rotated_rectangle
    xs = [math.dist(r.exterior.coords[i], r.exterior.coords[i+1]) for i in range(2)]
    w = min(xs)
    if a < 0.06 or w < 0.18 or a > 16 or w > 2.6: return None    # big or wide outlines are rugs and zones, not furniture
    if a < 0.42 and max(xs) < 0.9: return 'chair'
    return 'table'
F = collections.defaultdict(list)
groups = list(furn.items())
for gid, lines in groups:
    if gid == 'loose':
        # loose strokes in the fit-out block: work cluster by cluster
        cl = unary_union([LineString(q).buffer(0.25) for q in lines if len(q) > 1])
        bucket = collections.defaultdict(list)
        cps = [(prep(c), c) for c in polys(cl)]
        for q in lines:
            if len(q) < 2: continue
            p0 = Point(q[0])
            for i, (pp, c) in enumerate(cps):
                if pp.contains(p0): bucket[i].append(q); break
        parts = [pc for b in bucket.values() for pc in pieces(b)]
    else:
        parts = pieces(lines)
    for P in parts:
        k = classify(P)
        if k: F[k].append(P)
# drop pieces that sit inside a bigger piece (inner outlines of the same table)
for k in F:
    F[k].sort(key=lambda p: -p.area)
    keep = []
    for P in F[k]:
        c = P.representative_point()
        if any(Q.contains(c) for Q in keep[-400:] if Q.bounds[0] <= c.x <= Q.bounds[2] and Q.bounds[1] <= c.y <= Q.bounds[3]): continue
        keep.append(P)
    F[k] = keep
print('furniture', {k: len(v) for k, v in F.items()})

# desks, from the workstation blocks themselves (a desk is a table piece inside a WS block)
WS = {'rytu': 3, 'WS 1500x750mm': 1, 'WS 1500x750mm 2': 1, 'rhrt': 1, '4PAX WITH PLANTER': 4}
seats = collections.Counter(); deskpos = []
for iid, n, l, ch, x, y, rot, sx, sy in inserts:
    if n in WS and len(ch) == 1:
        seats[n] += WS[n]; deskpos.append([r2(v) for v in M((x, y))] + [WS[n], round(rot, 1)])
print('workstation seats', dict(seats), 'total', sum(seats.values()))

# plants: one shrub per plant block or per cluster of loose plant strokes
shrubs = []
for gid, lines in plant.items():
    pts = [p for q in lines for p in q]
    if not pts: continue
    if gid == ('loose',):
        cl = unary_union([LineString(q).buffer(0.15) if len(q) > 1 else Point(q[0]).buffer(0.15) for q in lines])
        for c in polys(cl):
            (x0, y0, x1, y1) = c.bounds; shrubs.append([r2((x0+x1)/2), r2((y0+y1)/2), r2(min(1.4, max(0.25, (x1-x0+y1-y0)/4)))])
    else:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        shrubs.append([r2((min(xs)+max(xs))/2), r2((min(ys)+max(ys))/2), r2(min(1.4, max(0.25, (max(xs)-min(xs)+max(ys)-min(ys))/4)))])
print('plants', len(shrubs))

# façade: the glazing line, split into straight runs
fac = [[r2(x), r2(y)] for x, y in list(glazing.exterior.coords)[:-1]]

out = {
  'units': 'm', 'origin_mm': [XO, YO], 'source': 'acko-layout-tf03.dxf',
  'slab': ring(slab), 'facade': fac, 'terraces': [ring(t) for t in terraces],
  'neigh': {k: ring(p) for k, p in NB.items()},
  'spaces': [{'g': g, 'k': k, 'p': ring(P), 'm2': round(P.area, 1)} for (g, k), L in sorted(spaces.items()) for P in L],
  'cores': [rings(p) for p in polys(unary_union([P.buffer(0) for (g, k), L in spaces.items() if g == 'core' for P in L]))],
  'walls': walls,
  'columns': [ring(c) for c in colp],
  'furn': {k: [ring(p) for p in v] for k, v in F.items()},
  'plants': shrubs, 'desks': deskpos, 'exits': exits,
  'counts': {'seats': sum(seats.values()), 'rooms': collections.Counter(k for (g, k), L in spaces.items() if g == 'room' for _ in L)},
}
json.dump(out, open(OUT, 'w'), separators=(',', ':'))
import os; print('written', OUT, os.path.getsize(OUT), 'bytes')
