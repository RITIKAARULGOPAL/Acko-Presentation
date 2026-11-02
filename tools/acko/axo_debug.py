"""The axo's walls, one object at a time, for tools/acko/axo_debug.html (Ritika, 30 Oct: "remove all walls apart from the core
walls of sketchup.. i want the debug to be like the plan hover debug wher i can selecct each object", then "now extrude all
columns alone.. have a separate layer", "now the external glazing", then "these walls are getting selected as one.. i want to select individual segments so i
can say which is glass and which are doors").
Usage:  python -I tools/acko/axo_debug.py   (then python tools/serve.py 8774, /tools/acko/axo_debug.html)
Writes tools/_work/axo-debug/debug.json (plan mm, y down, in the model's frame):
  pieces  every wall piece the axo extrudes (tools/acko/axo_skp_28_walls.rebuild's bodies, clipped and kept as it keeps them),
          each joined run split into its segments (at the plan's own lines across it and at its inside corners: see segments;
          "run" names the run, "key" is a segment's place, stable while the plan is), each with its type, height, area, mean width, rings and the floor plan lines it was made from (those running in it,
          longest first); the pieces rebuild leaves out too, with why ("cut": too small, too thick); and the floor plan's
          columns (S-COLS: its outlines and fills closed into faces, each column whole), type "column", to COLUMN_H, not
          clipped or tested as the walls are (the axo doesn't draw them: the model keeps its own); and the external glazing
          (type "facade"): the façade's glazing blocks (Revit's curtain walls, windows, glazed doors, mullions and fins: FT1,
          FT3, FT7, FT9, FT12...; not its louvres, railings, cladding or opaque fins) on the slab or within FACADE_OUT of it,
          each block's lines closed into its plan strip, one piece per run, to FACADE_H (the axo keeps the model's façade)
  lines   the floor plan's wall, partition, glass and door lines (layer, kind, block path, length; i: its place in
          plan_base_lines, which the page's own walk of data/plan-base.js follows, so its plan finds them)
  core    the SketchUp core's footprint boxes (the model's "mass" part, "Not in contract")"""
import json, math, os, re, sys
from collections import defaultdict

import numpy as np
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.prepared import prep
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axo_skp, axo_skp_28, axo_skp_28_walls as W

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "tools", "_work", "axo-debug")
LAYERS = W.WALL_FILLS | W.WALL_LINES | W.SOLID_LINES | W.SOLID_FILLS | W.GLASS_LINES | axo_skp_28.WALLS
NEAR = 30.0                                                         # a line this near a piece is one of its sources (mm)
FEEDS = {"wall": sorted(W.WALL_FILLS | W.WALL_LINES), "solid": sorted(W.SOLID_LINES | W.SOLID_FILLS | W.WALL_FILLS | W.WALL_LINES),
         "glass": sorted(W.GLASS_LINES), "column": sorted({"S-COLS"})}  # the layers each type is built from
GAP_MIN, GAP_MAX, GAP_DOOR = 450.0, 2000.0, 150.0                   # a door's opening (mm) and its door lines in it (mm at least)
BOOTH_BLOCK, BOOTH_MATCH, BOOTH_KEEP = "dfvfg", 150.0, 500.0       # (a model booth this near a plan seat (mm): kept)
CORE_NEAR, CORE_REACH = 1500.0, 800.0                               # the slab's edge this near the core isn't façade; walls reach the core
TIP_ZONE, TIP_SPLIT, TIP_REACH = 2000.0, 15500.0, 4000.0                               # the west tip's glazing: this far past the slab's west end; north of y
BOOTH_OWN = 700.0                                                   # a booth's own outline: its lines this near its seat (mm)
BOOTH_BLOCK_ = None                          # the plan's phone booth block; a booth on its seat (mm)
BOOTH_H, BOOTH_W = 1.8, 1800.0                                      # a phone booth: taller than this (m), under this across (mm)
COLUMN_H = 2.4                                                      # the columns cut where the walls are (m)
FACADE = re.compile(r"^FT\s*\d|Curtain|glazing|Facade|Window|Mullion|Fin\b", re.I)   # a block of the façade's glazing
NOT_GLASS = re.compile(r"Louver|Railing|Cladding|Opaque", re.I)     # (the façade's, but not glass)
FACADE_OUT, FACADE_H, FACADE_CLOSE = 1500.0, 2.4, 100.0             # mm beyond the slab's edge; its height (m); gaps closed (mm)
RAIL, RAIL_H = re.compile(r"Landscape Deck Railing", re.I), 1.1      # the terraces' railings (the plan's, A-FLOR-HRAL), glass to this (m)
RAIL_OFF, RAIL_MIN = 400.0, 600.0                                   # none this near the façade's glazing (mm); a run this long at least (mm)
RAIL_DEEP = 1500.0                                                  # the glazing on a deck's south edge (this shallow, mm) is its handrail
FACADE_REACH, FACADE_TOUCH = 3500.0, 300.0                         # a block wholly this near (mm), touching kept glazing this near


def facade_runs(PL, pt, slab):
    """the external glazing's lines by the outermost glazing block they sit in: {block path: [index in PL]}. The plan draws other
    parts of the building's façade round this floor too, and at the west tip it runs past the axo's slab (30 Oct: "this portion
    glazing is missing"), so: a block with most of its lines on the slab or within FACADE_OUT of its edge, whole; a block wholly
    within FACADE_REACH that touches one of those (within FACADE_TOUCH), whole; of the rest, only their lines within FACADE_OUT
    (a terrace's fins and the façades further out stay out). West of the slab's west end (the tip, past the axo's slab) every
    glazing line counts, and so do OB's own façade modules there (OB-I-ELEV-1, loose in the plan: the tip has no Revit façade
    block; elsewhere that layer doubles the Revit façade or draws a terrace's railing)"""
    near, reach = prep(slab.buffer(FACADE_OUT)), prep(slab.buffer(FACADE_REACH)); blk = defaultdict(list)
    west = slab.bounds[0]
    for i, (L, k, q, p) in enumerate(PL):
        if len(q) < 2: continue
        g = LineString([pt(x, y) for x, y in q]); m = g.interpolate(0.5, normalized=True)
        if L == "OB-I-ELEV-1" and tuple(n for n in p if n) == ("base",):
            if m.x < west: blk[("OB-I-ELEV-1 façade modules (the west tip)",)].append((i, g, True, True))
            continue
        ix = next((j for j, n in enumerate(p) if n and FACADE.search(n)), None)
        if ix is None or NOT_GLASS.search(p[ix]): continue
        blk[p[:ix + 1]].append((i, g, near.contains(m) or m.x < west, reach.contains(m) or m.x < west))
    out = {k: [i for i, *_ in v] for k, v in blk.items() if 2 * sum(a for _, _, a, _ in v) >= len(v)}
    kept = [g for k in out for _, g, _, _ in blk[k]]; tree = STRtree(kept)
    touch = lambda g: any(kept[j].distance(g) <= FACADE_TOUCH for j in tree.query(g.buffer(FACADE_TOUCH)))
    for k, v in blk.items():
        if k in out: continue
        if all(r for *_, r in v) and any(touch(g) for _, g, _, _ in v): out[k] = [i for i, *_ in v]; print("  glazing, touching:", k[-1])
        elif any(a for _, _, a, _ in v): out[k] = [i for i, _, a, _ in v if a]
    return out


def strips(qs):
    """a façade block's lines as its plan strip: each line widened 25 mm, the gaps under 2 x FACADE_CLOSE closed (glass and its
    mullions one solid); its runs"""
    u = unary_union([LineString(q).buffer(25) for q in qs]).buffer(FACADE_CLOSE).buffer(-FACADE_CLOSE)
    return [g for g in getattr(u, "geoms", [u]) if isinstance(g, Polygon) and g.area > 1e4]


RAY = 450.0                                                         # an inside corner's cut across its wall, at most (mm)
SEG_W, SEG_A = 60.0, 2e4                                            # a cut-off thinner (mm) or smaller (mm2) is a sliver
CORNER, ARC_TURN, ARC_MIN = 30.0, 1.0, 3                            # a corner turns this far (deg); a curve's facets: 1-30 deg, 3+


DOOR_MIN, DOOR_IN, DOOR_JOIN = 500.0, 0.8, 100.0                    # a door's opening line: this long (mm), this much in the wall,
                                                                    # its lines this near one another one door


def door_spans(g, doors):
    """the floor plan's doors in a run of walls: its door lines (a door block's opening, its leaves) lying in the wall along it
    (DOOR_MIN mm long or more, DOOR_IN of them inside), those near one another one door; each door's two jambs (the ends of its
    lines, along the longest) and its direction"""
    gz = g.buffer(30)
    ok = [d for d in doors if d.length >= DOOR_MIN and d.intersection(gz).length >= DOOR_IN * d.length]
    grp = list(range(len(ok)))
    def root(i):
        while grp[i] != i: grp[i] = grp[grp[i]]; i = grp[i]
        return i
    for i in range(len(ok)):
        for j in range(i + 1, len(ok)):
            if ok[i].distance(ok[j]) < DOOR_JOIN: grp[root(i)] = root(j)
    out = defaultdict(list)
    for i, d in enumerate(ok): out[root(i)].append(d)
    for ds in out.values():
        c = [q for d in ds for q in zip(d.coords[:-1], d.coords[1:])]          # (along its longest edge: a door drawn closed has no ends)
        (x0, y0), (x1, y1) = max(c, key=lambda e: math.dist(*e)); ln = math.hypot(x1 - x0, y1 - y0)
        if ln < 1: continue
        u = ((x1 - x0) / ln, (y1 - y0) / ln); ss = [(x - x0) * u[0] + (y - y0) * u[1] for d in ds for x, y in d.coords]
        yield [(x0 + u[0] * a, y0 + u[1] * a) for a in (min(ss), max(ss))], u


def segments(g, cutters, doors=()):
    """a joined run of walls (one polygon) as its segments: cut along the floor plan's own lines across it (a partition's end, a
    jamb) and, at each inside corner (where a wall meets another, the body bending round), along the corner's two edges carried
    on across the wall (RAY mm at most); a sliver (under SEG_W mm across or SEG_A mm2) joined to the segment it shares the most
    edge with. A cut runs across a wall, face to face, never along it (3 Nov: "still there are ovelapped walls": a glass line
    down a partition's middle had split it into two skins side by side). A door the plan draws in the wall (door_spans) is cut
    out at its jambs, its own segment (3 Nov: "thse are all door.. but they are included in the wall"). [(segment, is a door)]"""
    gb = g.buffer(1); rays = []; edge = g.boundary
    across = lambda part: isinstance(part, LineString) and 1 < part.length <= RAY and all(edge.distance(Point(e)) < 3 for e in (part.coords[0], part.coords[-1]))
    parts = lambda geom: [q for q in getattr(geom, "geoms", [geom]) if across(q)]
    def cut(b, dx, dy):                                              # a cut from b on the boundary, this way, across the body
        ln = math.hypot(dx, dy)
        if ln < 1e-9: return
        ray = LineString([b, (b[0] + dx / ln * RAY, b[1] + dy / ln * RAY)]).intersection(gb)
        rays.extend(part for part in parts(ray) if part.distance(Point(b)) < 2)
    for r, outer in [(g.exterior, True), *[(h, False) for h in g.interiors]]:   # (the body on the left: ccw outside, cw holes)
        q = list(r.coords)[:-1]; n = len(q); ccw = r.is_ccw if outer else not r.is_ccw
        turn = []                                                    # each corner's turn (degrees; + bends round the body)
        for i in range(n):
            a, b, c = q[i - 1], q[i], q[(i + 1) % n]
            u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1])
            t = math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
            turn.append(-t if ccw else t)
        for i in range(n):                                           # an inside corner where walls meet (a facet of a curve isn't)
            if turn[i] < CORNER: continue
            a, b, c = q[i - 1], q[i], q[(i + 1) % n]
            cut(b, b[0] - a[0], b[1] - a[1]); cut(b, b[0] - c[0], b[1] - c[1])
        # a curve (ARC_MIN facets or more in a row, each turning under CORNER, the same way): one segment, cut square across at
        # both its ends (3 Nov: "cureved wall portions should be one chunk")
        bent = [ARC_TURN <= abs(t) < CORNER for t in turn]
        if all(bent): continue
        s0 = next(i for i in range(n) if not bent[i])
        i = 0
        while i < n:
            j = (s0 + i) % n
            if not bent[j]: i += 1; continue
            run = [j]
            while i + len(run) < n and bent[(s0 + i + len(run)) % n] and (turn[(s0 + i + len(run)) % n] > 0) == (turn[j] > 0): run.append((s0 + i + len(run)) % n)
            if len(run) >= ARC_MIN:
                for k in (run[0], run[-1]):
                    a, b, c = q[k - 1], q[k], q[(k + 1) % n]
                    tx, ty = c[0] - a[0], c[1] - a[1]                # (the curve's tangent there; the body on its left if ccw)
                    cut(b, -ty, tx) if ccw else cut(b, ty, -tx)
            i += len(run)
    zones = []
    for (a, b), u in door_spans(g, doors):
        n = (-u[1], u[0])
        for e in (a, b): rays.extend(parts(LineString([(e[0] - n[0] * RAY, e[1] - n[1] * RAY), (e[0] + n[0] * RAY, e[1] + n[1] * RAY)]).intersection(gb)))
        zones.append((math.dist(a, b), Polygon([(a[0] - n[0] * RAY, a[1] - n[1] * RAY), (b[0] - n[0] * RAY, b[1] - n[1] * RAY), (b[0] + n[0] * RAY, b[1] + n[1] * RAY), (a[0] + n[0] * RAY, a[1] + n[1] * RAY)])))
    net = unary_union([edge] + [q for c in cutters for q in parts(c.intersection(gb))] + rays)
    faces = [f for f in polygonize(net) if g.contains(f.representative_point())]
    ok = lambda f: f.area >= SEG_A and 2 * f.area / f.length >= SEG_W
    big, small = [f for f in faces if ok(f)], [f for f in faces if not ok(f)]
    def is_door(f):                                                 # (most of it in a door's span, and most of the span's length)
        if not zones: return False
        r = f.minimum_rotated_rectangle.exterior.coords; long = max(math.dist(r[0], r[1]), math.dist(r[1], r[2]))
        return any(f.intersection(z).area >= 0.7 * f.area and long >= 0.6 * w for w, z in zones)
    if not big: return [(g, is_door(g))]
    for _ in range(3):
        rest = []
        for f in small:
            m, j = max((b.buffer(2).intersection(f.boundary).length, j) for j, b in enumerate(big))
            joined = unary_union([big[j], f]).buffer(1, join_style=2).buffer(-1, join_style=2) if m > 1 else None
            if isinstance(joined, Polygon): big[j] = joined                # (a merge that leaves it in parts doesn't happen)
            else: rest.append(f)
        small = rest
        if not small: break
    return [(q, is_door(q)) for f in big + small for q in getattr(f, "geoms", [f]) if isinstance(q, Polygon) and q.area > 1]   # (none lost: 3 Nov, a toilet wall)


CURVE_LAYER, CURVE_GAP, CURVE_TURN, CURVE_REACH, CURVE_ALONG = "OUTLINE", 400.0, 20.0, 150.0, 200.0   # see outline_curves


def outline_curves(PL, pt, walls):
    """curved walls the plan draws on its OUTLINE layer, which the axo's wall rules don't read (3 Nov: "cureved wall issing
    here"): two curved lines (turning CURVE_TURN deg or more in all) side by side, CURVE_GAP mm apart at most, the region between
    them a wall (WALL_W mm across at most) whose both ends meet the walls (within CURVE_REACH mm). Drawn along the middle of the
    two lines at the thickness of the walls it joins (3 Nov: "but teh thickness is different": the lines are ~90 mm apart, the
    partitions ~200). [polygon]"""
    comps = [c for c in getattr(walls, "geoms", [walls]) if isinstance(c, Polygon)]
    def curved(q):
        t = 0.0
        for a, b, c in zip(q, q[1:], q[2:]):
            u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - b[0], c[1] - b[1]); t += abs(math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])))
        return len(q) >= 5 and t >= CURVE_TURN
    arcs = [LineString(q) for L, k, raw, p in PL if L == CURVE_LAYER and k == "s" for q in [[pt(x, y) for x, y in raw]] if curved(q)]
    out = []
    for i in range(len(arcs)):
        for j in range(i + 1, len(arcs)):
            A, B = arcs[i], arcs[j]
            if A.distance(B) > CURVE_GAP or A.hausdorff_distance(B) > CURVE_GAP: continue
            qa, qb = list(A.coords), list(B.coords)
            if math.dist(qa[0], qb[0]) + math.dist(qa[-1], qb[-1]) > math.dist(qa[0], qb[-1]) + math.dist(qa[-1], qb[0]): qb = qb[::-1]
            g = Polygon(qa + qb[::-1]).buffer(0)
            if not isinstance(g, Polygon) or g.is_empty or 2 * g.area / max(g.length, 1) > W.WALL_W: continue
            if not all(walls.distance(Point(e)) < CURVE_REACH for e in (qa[0], qa[-1])): continue
            n = max(len(qa), len(qb), 24); A2, B2 = LineString(qa), LineString(qb)
            mid = [((a.x + b.x) / 2, (a.y + b.y) / 2) for k in range(n + 1) for a, b in [(A2.interpolate(k / n, normalized=True), B2.interpolate(k / n, normalized=True))]]
            ml = LineString(mid)                                    # (one along the walls already there, its middle (not the ends
            from shapely.ops import substring                       # that meet them), is their outline, not a wall: 3 Nov, "duplicate walls here")
            core_ = substring(ml, 500, ml.length - 500) if ml.length > 1200 else None
            if core_ is not None and core_.length > 1 and core_.difference(walls.buffer(CURVE_ALONG)).length < 0.5 * core_.length: continue
            ws = [2 * c.area / max(c.length, 1) for e in (mid[0], mid[-1]) for c in comps if c.distance(Point(e)) < CURVE_REACH]
            w = sorted(ws)[len(ws) // 2] if ws else 2 * g.area / max(g.length, 1)
            out.append(LineString(mid).buffer(w / 2, cap_style=2, join_style=1))
    return out


def core_footprint(S, CX, CY):
    """the SketchUp core's plan footprint (plan mm, the model's frame): its "mass" parts' triangles seen from above, joined"""
    tris = []
    for p in S["parts"]:
        if p["k"] != "mass" or p["lv"] == 2: continue
        q = W.b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3); lo, hi = np.array(p["lo"]), np.array(p["hi"]); v = lo + (q + 32768) / 65535 * (hi - lo)
        idx = W.b64(p["i"], np.uint32 if p.get("i32") else np.uint16).reshape(-1, 3)
        for t in v[idx]:
            g = Polygon([(a[0] * 1000 + CX, a[2] * 1000 + CY) for a in t])
            if g.area > 100: tris.append(g)
    return unary_union(tris).buffer(20).buffer(-20) if tris else Polygon()


# the plan's furniture the model hasn't (3 Nov: "thse workstations are missing", "add all these missing plants as well"): each rule
# a plan block or blocks, the model's component for them, and the block its frame is learned from (its pairs with the model's own
# placements, the nearest within MISS_NEAR mm); with too few pairs (MISS_PAIRS), the component centred on the block's insert point.
# A block gets one where no model piece of the rule's kinds stands within MISS_NEAR mm, on the slab
MISS_NEAR, MISS_PAIRS = 1500.0, 5
MISSING = [
    {"blocks": ["WS 1500x750mm 2"], "learn": "WS 1500x750mm", "unit": "WS 1500x750mm", "kinds": None, "near": 1500.0},   # (None: that component's own)
    {"blocks": ["A$C396F796F"], "learn": "A$C396F796F", "unit": "A$C396F796F", "kinds": ["plant"], "near": 900.0, "apart": 400},
    {"blocks": ["TREE12"], "learn": "TREE12", "unit": "TREE12", "kinds": ["plant"], "near": 900.0, "apart": 400},
    {"blocks": ["Clump of Trees or Bushes - plan", "TREE_P03", "A$C143125F4", "tree 26"], "learn": None, "unit": "A$C396F796F", "kinds": ["plant"], "near": 900.0, "apart": 400},
]


def missing_from_plan(root, S, sx, sy, CX, CY, slab):
    """placements for the plan's blocks the model has no piece for (MISSING): [{"u", "m"}] for AXO_SKP.changes.place"""
    import base64
    from shapely.prepared import prep as _prep
    s = open(os.path.join(root, "data", "plan-base.js"), encoding="utf-8").read(); PB = json.loads(s[s.index("window.PLAN_BASE = ") + 19:].strip().rstrip(";"))
    ox, oy = PB["origin"]; L = PB["layers"]; inst = defaultdict(list)
    want = {b for r in MISSING for b in r["blocks"] + ([r["learn"]] if r["learn"] else [])}
    for blk in PB["blocks"]:                                         # (every group: the plants are in "vegetation")
        Dd = blk["data"]; defs = Dd["defs"]; lay = lambda l, ctx: ctx if l in ("", "0") else l
        def walk(di, M, ctx):
            a, b, c, e, f, g = M
            for l, col, lt, lw, kind, items in defs[di]["runs"]:
                st = lay(l, ctx)
                if kind != "i" or L.get(st, {}).get("frozen"): continue
                for ci, ca, cb, cc, cd, ce, cf in items:
                    M2 = [a * ca + c * cb, b * ca + e * cb, a * cc + c * cd, b * cc + e * cd, a * ce + c * cf + f, b * ce + e * cf + g]
                    if defs[ci]["name"] in want:                      # (the block's frame in the plan's, mm, y down)
                        inst[defs[ci]["name"]].append((np.array([[M2[0], M2[2]], [-M2[1], -M2[3]]]), np.array([M2[4] - ox + sx, oy - M2[5] + sy])))
                    walk(ci, M2, st)
        walk(Dd["root"], Dd["place"]["m"], lay(Dd["place"]["spec"][0], "0"))
    on_slab = _prep(Polygon(slab)); byname = {}
    for i, x in enumerate(S["units"]): byname.setdefault((x.get("name") or "").rsplit("#", 1)[0], i)
    kinds_of = defaultdict(set)
    for p_ in S["parts"]:
        if p_["u"] >= 0: kinds_of[p_["u"]].add(p_["k"])
    place = {i: np.frombuffer(base64.b64decode(x["m"]), np.float32).reshape(-1, 12) for i, x in enumerate(S["units"])}
    out, report = [], []
    for r in MISSING:
        u = byname.get(r["unit"])
        if u is None: continue
        have = np.array([[f[9] * 1000 + CX, f[11] * 1000 + CY] for i, F in place.items() if (i == u if r["kinds"] is None else kinds_of[i] & set(r["kinds"])) for f in F] or [[1e12, 1e12]])
        placed = [np.array([q["m"][9] * 1000 + CX, q["m"][11] * 1000 + CY]) for q in out]    # (and apart from the ones placed: r["apart"] mm)
        mod = [(np.array([[f[0], f[6]], [f[2], f[8]]]) * 1000, np.array([f[9] * 1000 + CX, f[11] * 1000 + CY])) for f in place[u]]
        Km, kt = [], []
        for Mp, tp in (inst[r["learn"]] if r["learn"] else []):
            Mm, tm = min(mod, key=lambda q: np.linalg.norm(q[1] - tp))
            if np.linalg.norm(tm - tp) > MISS_NEAR or np.sign(np.linalg.det(Mm)) != np.sign(np.linalg.det(Mp)) or abs(np.linalg.det(Mm)) < 1e-9: continue
            Km.append(np.linalg.inv(Mm) @ Mp); kt.append(np.linalg.inv(Mm) @ (tp - tm))
        learned = len(Km) >= MISS_PAIRS
        if learned: Km, kt = np.median(Km, 0), np.median(kt, 0)
        ref = place[u][0]; R0 = np.array([[ref[0], ref[6]], [ref[2], ref[8]]]); n0 = len(out)
        # (unlearned: the component's own local box centre set on the insert point, as its own first placement is turned and sized)
        lo = np.min([p_["lo"] for p_ in S["parts"] if p_["u"] == u and p_["lv"] != 2], 0); hi = np.max([p_["hi"] for p_ in S["parts"] if p_["u"] == u and p_["lv"] != 2], 0); lc = np.array([(lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2])
        for nm in r["blocks"]:
            for Mp, tp in inst[nm]:
                if not on_slab.contains(Point(*tp)) or np.min(np.linalg.norm(have - tp, axis=1)) < r["near"] or any(np.linalg.norm(q - tp) < r.get("apart", 200) for q in placed): continue
                if learned: Mm = Mp @ np.linalg.inv(Km); tm = tp - Mm @ kt; A = Mm / 1000
                else: A = R0; tm = tp - (A @ lc) * 1000
                out.append({"u": u, "m": [float(v) for v in (A[0, 0], 0, A[1, 0], ref[3], ref[4], ref[5], A[0, 1], 0, A[1, 1], (tm[0] - CX) / 1000, ref[10], (tm[1] - CY) / 1000)]})
                placed.append(tp)
        report.append(f"{len(out) - n0} {r['unit']} on {', '.join(r['blocks'])}" + ("" if learned else " (centred)"))
    print("  the plan's furniture the model hasn't, placed: " + "; ".join(report))
    return out


def columns(PL, pt):
    """the floor plan's columns: its S-COLS lines and fills noded and closed into faces, the faces that touch joined (a column
    and its hatch, a column's parts): one polygon each"""
    ls = []
    for L, k, q, p in PL:
        if L not in FEEDS["column"] or len(q) < 2: continue
        r = [pt(x, y) for x, y in q]
        ls.append(LineString(r + [r[0]] if k == "f" and math.dist(r[0], r[-1]) > 1 else r))
    u = unary_union(list(polygonize(unary_union(ls)))) if ls else Polygon()
    return [g for g in getattr(u, "geoms", [u]) if isinstance(g, Polygon) and g.area > 1e3]


def layer_colours(names):
    """each layer's colour in the floor plan (data/plan-base.js)"""
    s = open(os.path.join(ROOT, "data", "plan-base.js"), encoding="utf-8").read(); PB = json.loads(s[s.index("window.PLAN_BASE = ") + 19:].strip().rstrip(";"))
    return {n: PB["layers"].get(n, {}).get("colour", "#000000") for n in sorted(names)}


def main():
    os.makedirs(OUT, exist_ok=True)
    S = axo_skp.read_js(os.path.join(ROOT, "data", "axo-skp.js"), "AXO_SKP"); A = axo_skp.read_js(os.path.join(ROOT, "data", "axo-dxf.js"), "AXO_DXF")
    xs = [q[0] for q in A["slab"]]; ys = [q[1] for q in A["slab"]]; CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    PL = W.plan_base_lines(ROOT, paths=True)
    pw = [q for L, k, q, p in PL if L in axo_skp_28.WALLS and k == "s" and len(q) > 1]
    d, after, before = axo_skp_28.onto_model(S, pw, np.zeros(2), CX, CY)          # the axo's own fit
    print(f"the floor plan onto the model: {[round(v) for v in d]} mm ({before:.0%} -> {after:.0%} of its wall lines on the model's)")
    pt = lambda x, y: (x + d[0], y + d[1])
    bodies = W.plan_bodies([(L, k, q) for L, k, q, p in PL], pt)
    axo_bodies = dict(bodies)                                       # (the axo's own, for the count it is checked against)
    curves = outline_curves(PL, pt, unary_union(list(bodies.values()))); curve_u = unary_union(curves) if curves else Polygon()
    if curves: bodies["solid"] = bodies["solid"].union(curve_u).difference(bodies["wall"])
    print(f"  {len(curves)} curved walls on {CURVE_LAYER} added as solid partitions (the axo doesn't extrude them yet)")

    # the zone rebuild clips to: the slab less EDGE, less the core (its pieces' boxes)
    model = W.model_pieces(S, CX, CY)
    core = [pc["box"] for pc in model if pc["ty"] == "core"]
    core_box = unary_union([Polygon([(a, b), (c, b), (c, e), (a, e)]) for a, b, c, e in core])
    zone_axo = Polygon(A["slab"]).buffer(-W.EDGE).difference(core_box)   # (the axo's: the core as its box)
    # the core as it stands: its plan footprint, the model's "mass" triangles seen from above (3 Nov: "no walls generated
    # here?": the rooms along the core, inside its box, had been clipped away)
    coreg = core_footprint(S, CX, CY)
    # the façade's edge kept clear (EDGE mm), not the core's: the slab's outline stops short of the core's walls (~0.3 m) and the
    # walls run up to the core (3 Nov: "there is a gap here")
    slab_p = Polygon(A["slab"]); facade_edge = slab_p.exterior.difference(coreg.buffer(CORE_NEAR))
    zone = slab_p.union(coreg.buffer(CORE_REACH)).difference(facade_edge.buffer(W.EDGE)).difference(coreg)
    print(f"  the core: {coreg.area / 1e6:.0f} m2 as it stands, {core_box.area / 1e6:.0f} m2 as its box (the axo's)")

    runs = facade_runs(PL, pt, Polygon(A["slab"])); on_facade = {i for v in runs.values() for i in v}
    lines, line_of = [], {}
    for i, (L, k, q, path) in enumerate(PL):
        if (L in LAYERS or L in FEEDS["column"] or W.DOOR.search(L) or i in on_facade or any(n and RAIL.search(n) for n in path)) and len(q) > 1:
            line_of[i] = len(lines)
            qq = [pt(x, y) for x, y in q]
            if k == "f" and math.dist(qq[0], qq[-1]) > 1: qq = qq + [qq[0]]
            lines.append({"i": i, "L": L, "k": k, "path": " > ".join(p for p in path if p) or "(the plan itself)",
                          "pts": [[round(x), round(y)] for x, y in qq], "m": round(sum(math.dist(qq[i], qq[i + 1]) for i in range(len(qq) - 1)) / 1000, 2)})
    geoms = [LineString(l["pts"]) for l in lines]; tree = STRtree(geoms)

    def sources(g):
        near = g.buffer(NEAR); src = []
        for i in tree.query(near):
            inside = geoms[i].intersection(near).length
            if inside > 1: src.append((int(i), round(inside / 1000, 2)))
        return sorted(src, key=lambda s: -s[1])
    ring = lambda g: [[[round(x), round(y)] for x, y in g.exterior.coords[:-1]]] + [[[round(x), round(y)] for x, y in h.coords[:-1]] for h in g.interiors]

    cut_ix = [j for j, l in enumerate(lines) if l["L"] in LAYERS]; cut_tree = STRtree([geoms[j] for j in cut_ix])
    door_ix = [j for j, l in enumerate(lines) if W.DOOR.search(l["L"])]; door_tree = STRtree([geoms[j] for j in door_ix])
    pieces, runs_n = [], 0
    cols = columns(PL, pt); col_u = unary_union(cols)                 # (a wall stops at a column standing in it)
    for ty, body in bodies.items():
        add = body.intersection(zone)
        for g in getattr(add, "geoms", [add]):
            if not isinstance(g, Polygon) or g.is_empty or g.area < 1e3: continue
            width = 2 * g.area / max(g.length, 1)
            cut = [] if g.area > 4e4 else ["small"]                   # rebuild's own tests
            if g.length <= 1200: cut.append("short")
            if width >= (W.GLASS_THICK if ty == "glass" else W.THICK): cut.append("thick")
            if not cut: g = g.simplify(10)                              # (as the axo draws it)
            runs_n += 1
            own = [c.intersection(g).buffer(0) for c in curves if not cut and c.intersects(g) and c.intersection(g).area > SEG_A]   # (an OUTLINE curve: whole)
            rest = g.difference(unary_union(own)).buffer(0) if own else g
            segs = [(q, dr) for part in getattr(rest, "geoms", [rest]) if isinstance(part, Polygon) and part.area > SEG_A
                    for q, dr in segments(part, [geoms[cut_ix[j]] for j in cut_tree.query(part)], [geoms[door_ix[j]] for j in door_tree.query(part.buffer(50))])] if not cut else [(g, False)]
            segs += [(q, False) for c in own for q in getattr(c, "geoms", [c]) if isinstance(q, Polygon)]
            if not cut and col_u.intersects(g):
                segs = [(q, dr) for s, dr in segs for d_ in [s.buffer(0).difference(col_u)] for q in getattr(d_, "geoms", [d_]) if isinstance(q, Polygon) and q.area >= SEG_A]
            for s, dr in segs:
                c = s.representative_point()
                pieces.append({"ty": ty, "h": W.HEIGHT[ty], "area": round(s.area / 1e6, 3), "width": round(2 * s.area / max(s.length, 1)),
                               "rings": ring(s), "src": sources(s), "box": [round(v) for v in s.bounds], "key": f"{ty}:{round(c.x)},{round(c.y)}",
                               "run": runs_n, "run_n": len(segs), "run_area": round(g.area / 1e6, 3), **({"cut": cut} if cut else {}), **({"door": True} if dr else {}),
                               **({"outline": True} if curves and s.intersection(curve_u).area >= 0.5 * s.area else {}),
                               **({"core_box": True} if s.intersection(core_box).area >= 0.5 * s.area else {})})
    # the phone booths: where the plan draws them (3 Nov: "add in the phone booths", then "these phone booths are placed
    # wrong": the model's stand off the 28.10 plan in places, and some the plan has it hasn't). The plan's booth is its BOOTH_BLOCK
    # block, the same name as the model's booth component: a seat each (A-SYM-FURN, its own small block of lines) and the
    # glass front nearest it (A-DOORWIN). Each is the model's own booth component, turned and moved so its seat and its front
    # land on the plan's: where the seat and the front sit in the component, the median over the model's booths that already
    # stand on a plan seat (within BOOTH_MATCH mm)
    hidden = {tuple(h) for h in S.get("changes", {}).get("hide", [])}
    booths = [pc for pc in model if "unit" in pc and pc["kind"] & {"wood", "soft"} and pc["h"] > BOOTH_H and len(pc["segs"])
              and max(pc["box"][2] - pc["box"][0], pc["box"][3] - pc["box"][1]) < BOOTH_W and tuple(pc["unit"]) not in hidden]
    toM = lambda f: np.array([[f[0], f[3], f[6], f[9]], [f[1], f[4], f[7], f[10]], [f[2], f[5], f[8], f[11]], [0, 0, 0, 1.0]])
    P3 = lambda x, y: np.array([(x - CX) / 1000, 0.0, (y - CY) / 1000, 1.0])
    bl = [(L, LineString([pt(x, y) for x, y in q])) for L, k, q, p in PL if len(q) > 1 and BOOTH_BLOCK in p]
    seats_u = unary_union([g.buffer(75) for L, g in bl if L == "A-SYM-FURN"]) if bl else Polygon()   # (a seat's parts, one seat)
    seats = [c.convex_hull.centroid for c in getattr(seats_u, "geoms", [seats_u]) if isinstance(c, Polygon) and 0.1e6 < c.convex_hull.area < 0.8e6]
    fronts = [g for L, g in bl if L == "A-DOORWIN"]
    outl = [g for L, g in bl if L == "A-WALL-EL3"]; outl_tree = STRtree(outl) if outl else None
    plan_b = []
    for s_ in seats:
        f = min(fronts, key=lambda g: g.distance(s_), default=None)
        if f is None or f.distance(s_) >= 1500: continue
        m_ = f.interpolate(0.5, normalized=True); ang = math.atan2(m_.y - s_.y, m_.x - s_.x)
        # its facing, square to its own outline (the nearest front can be the next booth's): the outline's axis nearest to it
        own = [outl[k] for k in outl_tree.query(s_.buffer(BOOTH_OWN))] if outl_tree is not None else []
        r = unary_union(own).minimum_rotated_rectangle if own else None
        if isinstance(r, Polygon):
            (x0_, y0_), (x1_, y1_) = list(r.exterior.coords)[:2]; phi = math.atan2(y1_ - y0_, x1_ - x0_)
            ang = min((phi + k * math.pi / 2 for k in range(4)), key=lambda t: abs(math.atan2(math.sin(t - ang), math.cos(t - ang))))
        plan_b.append(((s_.x, s_.y), (s_.x + math.cos(ang) * 1000, s_.y + math.sin(ang) * 1000)))
    ref, ls_, ld_ = None, [], []
    for pc in booths:
        u, i = (int(v) for v in pc["unit"]); M = toM(W.b64(S["units"][u]["m"], np.float32).reshape(-1, 12)[i]); c0 = ((pc["box"][0] + pc["box"][2]) / 2, (pc["box"][1] + pc["box"][3]) / 2)
        hit = min(plan_b, key=lambda b: math.dist(b[0], c0), default=None)
        if hit is None: continue
        l_s, l_d = np.linalg.inv(M) @ P3(*hit[0]), np.linalg.inv(M) @ P3(*hit[1])
        if math.dist(hit[0], c0) < BOOTH_MATCH * 3: ls_.append(l_s); ld_.append(l_d); ref = ref or (u, M)
    placed = []
    if ref and plan_b:
        u, Mr = ref; l_s, l_d = np.median(ls_, 0), np.median(ld_, 0)
        verts = []                                                  # (the component's own footprint, its parts seen from above)
        for p in S["parts"]:
            if p["u"] != u or p["lv"] == 2: continue
            q = W.b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3); lo, hi = np.array(p["lo"]), np.array(p["hi"]); verts.append(lo + (q + 32768) / 65535 * (hi - lo))
        V = np.concatenate(verts); hull = list(MultiPoint([(x, z) for x, _, z in V]).convex_hull.exterior.coords)[:-1]
        Ar = Mr[:3, :3]; vr = Ar @ (l_d - l_s)[:3]; a_ref = math.atan2(vr[2], vr[0])
        mods = []                                                   # (the model's booths, its own placement and footprint)
        for pc in booths:
            uu, ii = (int(v) for v in pc["unit"]); f = W.b64(S["units"][uu]["m"], np.float32).reshape(-1, 12)[ii]
            mods.append(((pc["box"][0] + pc["box"][2]) / 2, (pc["box"][1] + pc["box"][3]) / 2, MultiPoint([tuple(q) for q in pc["segs"].reshape(-1, 2)]).convex_hull, [float(v) for v in f], uu))
        for s_, d_ in plan_b:
            near = min(mods, key=lambda m: math.dist(m[:2], s_), default=None)
            if near is not None and math.dist(near[:2], s_) < BOOTH_KEEP:   # (one the model has on this seat: kept as it is)
                placed.append((near[2], near[3], near[4])); continue
            vn = P3(*d_) - P3(*s_); th = a_ref - math.atan2(vn[2], vn[0]); c, sn = math.cos(th), math.sin(th)
            Ry = np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]]); An = Ry @ Ar; t = P3(*s_)[:3] - An @ l_s[:3]
            g = Polygon([((An @ [x, 0, z] + t)[0] * 1000 + CX, (An @ [x, 0, z] + t)[2] * 1000 + CY) for x, z in hull])
            M = np.eye(4); M[:3, :3] = An; M[:3, 3] = t
            placed.append((g, [float(v) for v in (M[0, 0], M[1, 0], M[2, 0], M[0, 1], M[1, 1], M[2, 1], M[0, 2], M[1, 2], M[2, 2], M[0, 3], M[1, 3], M[2, 3])], u))
    model_c = [((pc["box"][0] + pc["box"][2]) / 2, (pc["box"][1] + pc["box"][3]) / 2) for pc in booths]
    for g, m16, u in placed:
        c0 = g.centroid; off = min((math.dist((c0.x, c0.y), c) for c in model_c), default=1e9)
        note = "as the model has it" if off < BOOTH_MATCH else f"the model's {off / 1000:.2f} m off" if off < 2500 else "the model has none here"
        pieces.append({"ty": "booth", "h": round(booths[0]["h"], 2) if booths else 2.2, "unit": [u, -1], "m": [round(v, 5) for v in m16], "area": round(g.area / 1e6, 3),
                       "width": round(2 * g.area / max(g.length, 1)), "rings": ring(g.simplify(5)), "src": sources(g), "box": [round(v) for v in g.bounds],
                       "name": "phone booth", "block": f"the plan's {BOOTH_BLOCK} (its seat and front); SketchUp's booth placed on it: {note}",
                       "key": "booth:%d,%d" % tuple(round(v) for v in g.representative_point().coords[0]), **({"moved": round(off)} if off >= BOOTH_MATCH else {})})
    pc_c = [g.centroid for g, _, _ in placed]
    dropped = sum(1 for c in model_c if min((math.dist(c, (q.x, q.y)) for q in pc_c), default=1e9) > 2500)
    print(f"  {len(placed)} phone booths where the plan draws them ({sum(1 for g, _, _ in placed if True)} placed; the model has {len(booths)}, {dropped} of them where the plan has none)")
    for g in cols:
        pieces.append({"ty": "column", "h": COLUMN_H, "key": "column:%d,%d" % tuple(round(v) for v in g.representative_point().coords[0]), "area": round(g.area / 1e6, 3), "width": round(2 * g.area / max(g.length, 1)), "rings": ring(g),
                       "src": sources(g), "box": [round(v) for v in g.bounds], **({"core": True} if g.intersects(coreg) else {})})
    # the doors in the walls' openings (3 Nov: "add doors herer"): from a wall's free end, straight on along it, another wall
    # GAP_MIN to GAP_MAX mm away (end on or side on), the plan's door lines in the gap (its leaf, its swing): a door, the wall's
    # thickness, filling it; an opening with no door drawn stays open
    walls_ = [(q, Polygon(q["rings"][0], q["rings"][1:]).buffer(0)) for q in pieces if q["ty"] in ("wall", "solid", "glass", "column") and not q.get("cut")]
    wall_tree = STRtree([g for _, g in walls_]); gaps = []
    door_geoms = [geoms[j] for j in door_ix]; door_tree2 = STRtree(door_geoms)
    for q, g in walls_:
        if q["ty"] == "column": continue
        r = g.minimum_rotated_rectangle
        if not isinstance(r, Polygon) or g.area < 0.8 * r.area: continue
        c = list(r.exterior.coords)[:4]
        if len(c) < 4: continue
        e = [(c[k], c[(k + 1) % 4]) for k in range(4)]
        short = sorted(e, key=lambda ab: math.dist(*ab))[:2]
        if math.dist(*sorted(e, key=lambda ab: math.dist(*ab))[-1]) < max(2 * math.dist(*short[0]), 300): continue   # (a post has no clear way on)
        for (a_, b_) in short:
            m = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2); ctr = g.centroid
            u = (m[0] - ctr.x, m[1] - ctr.y); ln = math.hypot(*u)
            if ln < 1: continue
            u = (u[0] / ln, u[1] / ln); wd = math.dist(a_, b_)
            if wd > W.WALL_W + 50: continue                                   # (a wall's end, not its side)
            start = Point(m[0] + u[0] * 5, m[1] + u[1] * 5)
            if any(g2 is not g and g2.distance(start) < 3 for g2 in (walls_[k][1] for k in wall_tree.query(start.buffer(5)))): continue   # (not free)
            ray = LineString([(m[0] + u[0] * 5, m[1] + u[1] * 5), (m[0] + u[0] * GAP_MAX, m[1] + u[1] * GAP_MAX)])
            gd = min((Point(m).distance(ray.intersection(g2)) for k in wall_tree.query(ray) for g2 in [walls_[k][1]] if g2 is not g and ray.intersects(g2)), default=None)
            if gd is None or not GAP_MIN <= gd <= GAP_MAX: continue
            gap = Polygon([a_, b_, (b_[0] + u[0] * gd, b_[1] + u[1] * gd), (a_[0] + u[0] * gd, a_[1] + u[1] * gd)])
            if sum(gap.intersection(walls_[k][1]).area for k in wall_tree.query(gap)) > 0.1 * gap.area: continue
            # open on both sides: no wall along either of its long sides (3 Nov: "whya re these glass wlls added right next to
            # solid walls.. remove them": a wall's flank had been taken for an opening)
            n_ = (-u[1], u[0]); side = False
            for e0, sg in ((a_, 1 if (a_[0] - b_[0]) * n_[0] + (a_[1] - b_[1]) * n_[1] > 0 else -1), (b_, 1 if (b_[0] - a_[0]) * n_[0] + (b_[1] - a_[1]) * n_[1] > 0 else -1)):
                o = (e0[0] + n_[0] * sg * 60, e0[1] + n_[1] * sg * 60)
                strip = LineString([(o[0] + u[0] * 80, o[1] + u[1] * 80), (o[0] + u[0] * (gd - 80), o[1] + u[1] * (gd - 80))]).buffer(30, cap_style=2)
                if sum(strip.intersection(walls_[k][1]).area for k in wall_tree.query(strip)) > 0.2 * strip.area: side = True
            if side: continue
            near = gap.buffer(60)
            if sum(door_geoms[k].intersection(near).length for k in door_tree2.query(near)) < GAP_DOOR: continue
            if any(gap.intersection(o).area > 0.5 * min(gap.area, o.area) for o in gaps): continue   # (two ends facing: one door)
            gaps.append(gap); c2 = gap.representative_point()
            pieces.append({"ty": q["ty"], "h": q["h"], "area": round(gap.area / 1e6, 3), "width": round(2 * gap.area / max(gap.length, 1)), "rings": ring(gap),
                           "src": sources(gap), "box": [round(v) for v in gap.bounds], "key": f"{q['ty']}:{round(c2.x)},{round(c2.y)}", "run": q.get("run"),
                           "run_n": q.get("run_n"), "run_area": q.get("run_area"), "door": True, "opening": True, **({"core_box": True} if q.get("core_box") else {})})
    print(f"  {len(gaps)} doors in the walls' openings")
    feeds_f, drawn = set(), []                                     # (a module two façade blocks draw: once, the first's)
    solid_pcs = [Polygon(q["rings"][0], q["rings"][1:]) for q in pieces if not q.get("cut")]; solid_tree = STRtree(solid_pcs)
    for path, ix in runs.items():
        js = [line_of[i] for i in ix]; feeds_f |= {lines[j]["L"] for j in js}
        name = re.sub(r"-(V\d+-)?\d*-?Third Floor Plan$", "", path[-1]).strip()
        for g0 in strips([lines[j]["pts"] for j in js]):
            twin = next((q for q, gg in drawn if gg.intersects(g0) and gg.intersection(g0).area > 0.6 * min(g0.area, gg.area)), None)
            if twin is not None: twin.setdefault("twins", []).append(" > ".join(n for n in path if n)); continue
            # what the walls, the columns and the modules before it already fill, taken off (a shared mullion, a partition's end)
            over = [gg for _, gg in drawn if gg.intersects(g0)] + [solid_pcs[k] for k in solid_tree.query(g0)]
            rest = g0.difference(unary_union(over)) if over else g0
            parts_ = [q for q in getattr(rest, "geoms", [rest]) if isinstance(q, Polygon) and q.area > 1e4]
            if not parts_: continue
            g = max(parts_, key=lambda q: q.area)
            near = g.buffer(NEAR); src = []
            for j in js:
                inside = geoms[j].intersection(near).length
                if inside > 1: src.append((j, round(inside / 1000, 2)))
            pieces.append({"ty": "facade", "h": FACADE_H, "area": round(g.area / 1e6, 3), "width": round(2 * g.area / max(g.length, 1)),
                           "rings": ring(g.simplify(5)), "src": sorted(src, key=lambda s: -s[1]), "box": [round(v) for v in g.bounds],
                           "name": name, "block": " > ".join(n for n in path if n),
                           "key": "facade:%d,%d" % tuple(round(v) for v in g.representative_point().coords[0])})
            drawn.append((pieces[-1], g))
    # the west tip closed in its point (3 Nov: "this is still open", then "still the building has a triangular ending"): the plan
    # draws no glass round it, so the north glazing's line and the diagonal glazing's line carried on from their ends till they
    # meet, in glass; the triangle and its post inside
    west = Polygon(A["slab"]).bounds[0]
    tipf = [q for q in pieces if q["ty"] == "facade" and q["box"][0] < west + TIP_ZONE]
    nq = [q for q in tipf if q["box"][3] < TIP_SPLIT]; dq = [q for q in tipf if q["box"][1] > TIP_SPLIT]
    def axis(qs):                                                    # (the longest piece's long direction)
        r = Polygon(max(qs, key=lambda q: q["area"])["rings"][0]).minimum_rotated_rectangle; c = list(r.exterior.coords)
        e = max(((c[k], c[k + 1]) for k in range(2)), key=lambda ab: math.dist(*ab)); ln = math.dist(*e)
        return ((e[1][0] - e[0][0]) / ln, (e[1][1] - e[0][1]) / ln)
    if nq and dq:
        a_ = min((v for q in nq for v in q["rings"][0]), key=lambda v: v[0]); b_ = min((v for q in dq for v in q["rings"][0]), key=lambda v: v[1])
        (ux, uy), (vx, vy) = axis(nq), axis(dq); den = ux * vy - uy * vx
        if abs(den) > 1e-3:
            t = ((b_[0] - a_[0]) * vy - (b_[1] - a_[1]) * vx) / den; p_ = (a_[0] + ux * t, a_[1] + uy * t)   # (where the two lines meet)
            if math.dist(a_, p_) < TIP_REACH and math.dist(b_, p_) < TIP_REACH:
                for e0, e1 in ((a_, p_), (p_, b_)):
                    g = LineString([e0, e1]).buffer(60, cap_style=2).union(Point(p_).buffer(60, quad_segs=2))
                    pieces.append({"ty": "facade", "h": FACADE_H, "area": round(g.area / 1e6, 3), "width": 120, "rings": ring(g), "src": sources(g),
                                   "box": [round(v) for v in g.bounds], "name": "glass round the west tip", "block": "(none: the plan draws no glass here)",
                                   "key": "facade:%d,%d" % tuple(round(v) for v in g.representative_point().coords[0])})
                print(f"  the west tip closed in its point at {[round(v) for v in p_]}: {(math.dist(a_, p_) + math.dist(p_, b_)) / 1000:.2f} m of glass")
    FEEDS["facade"] = sorted(feeds_f)
    # the terraces' glass handrails (Ritika, 2 Nov: "these 2 portions should have glass handrails for terrace"): the plan's deck
    # railings (RAIL, its A-FLOR-HRAL lines): it draws only their ends and posts, at the deck's corners, so each railing is the
    # deck's south, east and west edges through them (its lines' box), less where the façade's glazing already stands (RAIL_OFF
    # mm of it), each run left one piece, glass to RAIL_H. The south edge is handrail all along: the façade's glazing the plan
    # draws on it goes (2 Nov: "this is also handrail")
    rail_ix = [j for j, l in enumerate(lines) if RAIL.search(l["path"])]
    decks_r = []
    for blk in sorted({lines[j]["path"] for j in rail_ix}):
        xs = [x for j in rail_ix if lines[j]["path"] == blk for x, _ in lines[j]["pts"]]; ys = [y for j in rail_ix if lines[j]["path"] == blk for _, y in lines[j]["pts"]]
        decks_r.append((min(xs) + 20, min(ys), max(xs) - 20, max(ys) - 20))
    south = unary_union([LineString([(x0, y1), (x1, y1)]) for x0, y0, x1, y1 in decks_r])
    on_south = [q for q in pieces if q["ty"] == "facade" and q["box"][3] - q["box"][1] < RAIL_DEEP and Polygon(q["rings"][0]).distance(south) < RAIL_OFF]
    pieces[:] = [q for q in pieces if not any(q is o for o in on_south)]
    print(f"  {len(on_south)} façade glazing runs on the terraces' south edges made handrail")
    fac_u = unary_union([Polygon(q["rings"][0]) for q in pieces if q["ty"] == "facade"]).buffer(RAIL_OFF)
    runs_r = []
    for x0, y0, x1, y1 in decks_r:
        for e in (LineString([(x0, y1), (x1, y1)]), LineString([(x1, y0), (x1, y1)]), LineString([(x0, y0), (x0, y1)])):
            rest = e.difference(fac_u)
            runs_r += [s for s in getattr(rest, "geoms", [rest]) if s.length > RAIL_MIN]
    for g in getattr(unary_union([s.buffer(40, cap_style=2, join_style=2) for s in runs_r]), "geoms", []) or [unary_union([s.buffer(40, cap_style=2, join_style=2) for s in runs_r])]:
        if g.is_empty: continue
        pieces.append({"ty": "rail", "h": RAIL_H, "area": round(g.area / 1e6, 3), "width": round(2 * g.area / max(g.length, 1)),
                       "rings": ring(g.simplify(5)), "src": sources(g), "box": [round(v) for v in g.bounds], "name": "the terrace's handrail",
                       "block": "Landscape Deck Railing", "key": "rail:%d,%d" % tuple(round(v) for v in g.representative_point().coords[0])})
    FEEDS["rail"] = sorted({lines[j]["L"] for j in rail_ix})
    print(f"  {sum(p['ty'] == 'rail' for p in pieces)} terrace handrail runs from {len(rail_ix)} railing lines")
    seen = defaultdict(int)                                        # (two façade blocks drawing one module: their keys apart)
    for p in pieces:
        seen[p["key"]] += 1
        if seen[p["key"]] > 1: p["key"] += "#%d" % seen[p["key"]]
    pieces.sort(key=lambda p: -p["area"])
    for i, p in enumerate(pieces): p["id"] = i
    add_place = missing_from_plan(ROOT, S, d[0], d[1], CX, CY, A["slab"])
    kept = {ty: sum(1 for g in getattr(b.intersection(zone_axo), "geoms", [b.intersection(zone_axo)]) if isinstance(g, Polygon) and g.area > 4e4 and g.length > 1200
                    and 2 * g.area / g.length < (W.GLASS_THICK if ty == "glass" else W.THICK)) for ty, b in axo_bodies.items()}   # (as rebuild keeps them)
    axo = {ty: len(v) for ty, v in S.get("changes", {}).get("walls", {}).items()}
    print(f"{len(pieces)} pieces: kept runs {kept} (data/axo-skp.js has {axo}), {sum('cut' in p for p in pieces)} cut; {sum(1 for p in pieces if p["ty"] in kept and "cut" not in p)} wall segments ({sum(1 for p in pieces if p.get("door"))} the plan's doors); {len(cols)} columns ({sum(1 for p in pieces if p.get("core"))} in the core); {len(placed)} phone booths; {sum(p["ty"] == "facade" for p in pieces)} glazing runs from {len(runs)} façade blocks; {len(lines)} plan lines")
    out = {"CX": CX, "CY": CY, "shift": [round(v) for v in d], "slab": A["slab"], "core": [[round(v) for v in b] for b in core],
           "heights": {**W.HEIGHT, "column": COLUMN_H, "facade": FACADE_H}, "axo": axo, "axo_runs": kept, "add_place": add_place, "feeds": FEEDS, "colours": layer_colours({l["L"] for l in lines}), "pieces": pieces, "lines": lines}
    with open(os.path.join(OUT, "debug.json"), "w") as f: json.dump(out, f, separators=(",", ":"))
    print("wrote", os.path.relpath(os.path.join(OUT, "debug.json"), ROOT))


if __name__ == "__main__": main()
