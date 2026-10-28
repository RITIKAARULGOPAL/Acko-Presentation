"""The schematic axonometric's model (deck slides 58-60), from the DXF plan toolkit's classed SVG.

Usage:  python tools/acko/axo_dxf.py "<toolkit>/viewer/out/op2a"

Reads the toolkit's output, never the DXF itself (the toolkit's rule):
  instanced.svg  every block written once and placed by <use transform="matrix(...)">, plus loose geometry; every path
                 classed: wall, glass, door, furn, green, base, shade, anno (s = stroke, f = fill, m = mask, h = hatch)
  rooms.json     the terrace (a space-plan layer)
and the deck's own data/plan-dxf.js (the spaces as the legend colours them, the neighbourhoods).

Writes data/axo-dxf.js (window.AXO_DXF) and a check picture, tools/_work/axo/check.png. Everything is in plan mm in the
toolkit's frame (y down), the same frame as data/plan-dxf.js:
  slab      the floor plate outline (the union of the walls, glass and shell, closed and filled)
  walls     solid walls, as polygons (filled walls, and the thin strips between double wall lines)
  columns   the shell's small filled shapes
  glass     glazing lines (polylines)
  floors    the deck's spaces: [type, ring]; terrace: rings
  blocks    furniture per block, in block coordinates: {id: [[kind, ring], ...]}; uses: [[id, a, b, c, d, e, f], ...]
  loose     furniture drawn outside blocks: [[kind, ring], ...]
  plants    [x, y, r]
  beats     the West / Middle / East thirds: [x0, x1]; labels: per beat [[name, x, y], ...]
Furniture kinds, from each closed outline's size and shape: chair, desk (desks and tables), store (low units along walls).
"""
import json, math, os, re, sys, time
from collections import Counter, defaultdict

from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union
from shapely.strtree import STRtree

# the legend's enclosed rooms: glass in the axo
GLASS_ROOMS = {"Phone booth", "Quick sprint", "Collaboration huddle", "Departmental room", "Boardroom", "Visitor hub", "The Hatchery",
               "Studio", "Zen room", "Mother's room", "Prayer room", "Executive corner cabin", "Training room"}
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOK = re.compile(r"[MLC]|-?\d*\.?\d+(?:e-?\d+)?")


def subpaths(d, tol=50.0):
    """a path's subpaths as point lists; cubic curves flattened to about tol mm (the toolkit writes only M, L and C)"""
    out, pts, cmd, t, i = [], None, None, TOK.findall(d), 0
    while i < len(t):
        k = t[i]
        if k in ("M", "L", "C"):
            cmd = k; i += 1; continue
        if cmd == "M":
            if pts and len(pts) > 1: out.append(pts)
            pts = [(float(t[i]), float(t[i + 1]))]; i += 2; cmd = "L"
        elif cmd == "L":
            pts.append((float(t[i]), float(t[i + 1]))); i += 2
        elif cmd == "C":
            x1, y1, x2, y2, x, y = map(float, t[i:i + 6]); i += 6
            x0, y0 = pts[-1]
            L = math.hypot(x1 - x0, y1 - y0) + math.hypot(x2 - x1, y2 - y1) + math.hypot(x - x2, y - y2)
            n = max(2, min(24, int(L / tol) + 1))
            for j in range(1, n + 1):
                u = j / n; a = 1 - u
                pts.append((a ** 3 * x0 + 3 * a * a * u * x1 + 3 * a * u * u * x2 + u ** 3 * x,
                            a ** 3 * y0 + 3 * a * a * u * y1 + 3 * a * u * u * y2 + u ** 3 * y))
        else:
            i += 1
    if pts and len(pts) > 1: out.append(pts)
    return out


def tf(m, pts):
    a, b, c, d, e, f = m
    return [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]


def closed(p):
    return len(p) >= 4 and math.dist(p[0], p[-1]) < 5


def valid(ring):
    try:
        g = Polygon(ring).buffer(0)
    except Exception:
        return []
    if g.is_empty: return []
    return [q for q in (g.geoms if isinstance(g, MultiPolygon) else [g]) if q.area > 1e3]


def sides(poly):
    """the short and long side (m) of a shape's minimum rotated rectangle"""
    c = list(poly.minimum_rotated_rectangle.exterior.coords)
    a, b = math.dist(c[0], c[1]) / 1000, math.dist(c[1], c[2]) / 1000
    return min(a, b), max(a, b)


def kind_of(poly):
    """chair / desk / store from an outline's size and shape (None: a detail, a rug, a room outline)"""
    A = poly.area / 1e6
    if A < 0.1: return None
    w, L = sides(poly)
    if w < 0.28: return None                                   # monitors, edges, thin trims
    if A <= 0.6 and L <= 0.95: return "chair"
    if w <= 0.52 and 0.8 <= L <= 6: return "store"             # credenzas, low storage along walls
    if w <= 1.7 and L <= 7.5 and A >= 0.35: return "desk"      # desks and tables
    if A <= 12 and w <= 3.5: return "desk"                     # large tables (boardroom, café)
    return None


def outermost(polys):
    """drop shapes that lie (90%+) inside a larger kept one: a seat inside its chair, a top inside its desk"""
    polys = sorted(polys, key=lambda q: -q.area)
    kept = []
    tree_items = []
    for q in polys:
        inside = False
        for k in tree_items:
            if k.bounds[0] <= q.bounds[0] and k.bounds[1] <= q.bounds[1] and k.bounds[2] >= q.bounds[2] and k.bounds[3] >= q.bounds[3]:
                if k.intersection(q).area >= 0.9 * q.area:
                    inside = True; break
        if not inside:
            kept.append(q); tree_items.append(q)
    return kept


def closed_faces(lines, gap):
    """the regions a set of lines encloses, bridging breaks up to 2 x gap mm (CAD hides a desk's edge where a chair sits on it)"""
    if not lines: return []
    u = unary_union([LineString(p).buffer(gap, 2) for p in lines if len(p) > 1])
    return [q for g in (u.geoms if isinstance(u, MultiPolygon) else [u]) for h in g.interiors for q in valid(list(Polygon(h).buffer(gap, 2).exterior.coords))]


def furniture(subs, fills, tops=()):
    """the furniture shapes in a set of linework: closed outlines as they are, open lines polygonized face by face, and
    desk tops (a pod's "base" lines) closed across the breaks its chairs leave"""
    polys = closed_faces(list(tops), 110)
    for p in fills: polys += valid(p)
    opens = []
    for p in subs:
        if closed(p): polys += valid(p)
        else: opens.append(p)
    if opens:
        # each face of the open linework on its own: merging them would fuse a table with the chairs drawn across it
        try:
            polys += [f for f in polygonize(unary_union([LineString(p) for p in opens if len(p) > 1])) if f.area > 1e3]
        except Exception:
            pass
    # classify first: a rug or a cluster outline (no kind) must not hide the desks inside it
    typed = [(kind_of(q), q) for q in polys]
    keep = outermost([q for k, q in typed if k])
    out = []
    for q in keep:
        s = q.simplify(8)
        if not s.is_empty and s.geom_type == "Polygon": out.append((kind_of(q), s))
    return [(k, q) for k, q in out if k]


def ring_out(poly, ndp=0):
    return [[round(x), round(y)] for x, y in list(poly.exterior.coords)[:-1]]


def poly_out(poly):
    """a polygon with its holes: [exterior, hole, ...]"""
    return [ring_out(poly)] + [[[round(x), round(y)] for x, y in list(h.coords)[:-1]] for h in poly.interiors]


def rings_of_d(d):
    out = []
    for part in re.findall(r"M([^M]+)", d):
        nums = list(map(float, re.findall(r"-?\d*\.?\d+", part)))
        pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
        if len(pts) > 2: out.append(pts)
    return out


def main(out_dir):
    t0 = time.time()
    svg = open(os.path.join(out_dir, "instanced.svg"), encoding="utf-8").read()
    cut = svg.index("</defs>")
    defs, body = svg[:cut], svg[cut:]
    raw = re.findall(r'<g id="(b\d+)">(.*?)</g>', defs, re.S)
    assert len(raw) == defs.count("<g "), "blocks with nested groups: the parser needs a real XML walk"
    blocks = {bid: re.findall(r'<path class="([^"]+)" d="([^"]*)"', inner) for bid, inner in raw}
    uses = [(bid, tuple(map(float, m.replace(",", " ").split()))) for bid, m in re.findall(r'<use href="#(b\d+)" transform="matrix\(([^)]*)\)"', body)]
    loose = re.findall(r'<path class="([^"]+)" d="([^"]*)"', body)
    print(f"blocks {len(blocks)}, uses {len(uses)}, loose paths {len(loose)}")

    # world geometry per class (walls, glass, shell, plants), and furniture per block in its own coordinates
    W = defaultdict(list)                       # (kind, cat) -> list of world point lists
    bsub = {}                                   # block -> its parsed subpaths per (kind, cat)
    for bid, paths in blocks.items():
        g = defaultdict(list)
        for cls, d in paths:
            k = cls.split()
            if len(k) < 2: continue
            g[(k[0], k[1])] += subpaths(d)
        bsub[bid] = g
    plants = []
    for bid, m in uses:
        g = bsub[bid]
        for key, subs in g.items():
            if key[1] in ("wall", "glass", "base") or key == ("f", "green"):
                W[key] += [tf(m, p) for p in subs]
        green = g.get(("s", "green"), []) + g.get(("f", "green"), [])
        if green and not g.get(("s", "furn")):
            pts = [q for p in green for q in tf(m, p)]
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            plants.append([round((max(xs) + min(xs)) / 2), round((max(ys) + min(ys)) / 2), round(min(max(r, 250), 1200))])
    loose_furn_s, loose_furn_f = [], []
    for cls, d in loose:
        k = cls.split()
        if len(k) < 2: continue
        subs = subpaths(d)
        if k[1] == "furn":
            (loose_furn_f if k[0] == "f" else loose_furn_s).extend(subs)
        elif k[1] in ("wall", "glass", "base") or (k[0], k[1]) == ("f", "green"):
            W[(k[0], k[1])] += subs
    print(f"parsed in {time.time() - t0:.0f}s; plants {len(plants)}")

    # walls: filled walls, and the thin strips between double wall lines; the shell's small fills are columns
    fills = [q for p in W[("f", "wall")] for q in valid(p)]
    lines = [LineString(p) for p in W[("s", "wall")] if len(p) > 1]
    faces = list(polygonize(unary_union(lines))) if lines else []
    strips = [f for f in faces if f.area > 1e4 and 2 * f.area / f.length < 350]
    columns, shell_walls = [], []
    for p in W[("f", "base")]:
        for q in valid(p):
            w, L = sides(q)
            (columns if (q.area < 2.5e6 and w > 0.2) else shell_walls).append(q)
    blines = [LineString(p) for p in W[("s", "base")] if len(p) > 1]
    bfaces = list(polygonize(unary_union(blines))) if blines else []
    shell_walls += [f for f in bfaces if f.area > 1e4 and 2 * f.area / f.length < 450]
    walls = unary_union(fills + strips + shell_walls).simplify(10)
    walls = [q for q in (walls.geoms if isinstance(walls, MultiPolygon) else [walls]) if q.area > 2e4]
    print(f"walls {len(walls)} (fills {len(fills)}, strips {len(strips)} of {len(faces)} faces, shell {len(shell_walls)}), columns {len(columns)}")

    # glazing lines, merged
    glines = [LineString(p) for p in W[("s", "glass")] if len(p) > 1]
    gm = linemerge(unary_union(glines)) if glines else None
    glass = [g.simplify(20) for g in (gm.geoms if hasattr(gm, "geoms") else [gm])] if gm else []
    glass = [g for g in glass if g.length > 300]

    # the slab: the floor ACKO occupies (the neighbourhoods, the deck's spaces, the toolkit's rooms: cores, common areas,
    # terrace), closed up and filled; the rest of the building's floor (the hotel rooms' band) becomes plain grey masses
    rooms = json.load(open(os.path.join(out_dir, "rooms.json"), encoding="utf-8"))["spaces"]
    # a drawing with named layers (AC_*): its out-of-scope band is "not in contract", and an outline bigger than the floor is a
    # block's frame on a layer, not a space
    nic = lambda sp: sp["name"] in ("Not in contract", "Out Of Scope") or sp.get("layer") == "AC_OUT_OF_SCOPE"
    named = any(str(sp.get("layer", "")).startswith("AC_") for sp in rooms)
    rooms = [sp for sp in rooms if sp.get("m2", 0) < 6000 and not (named and str(sp.get("layer", "")).startswith("AC_") and sp["name"] != "Terrace")]
    terrace = [q for s in rooms if s["name"] == "Terrace" for r in rings_of_d(s["d"]) for q in valid(r)]
    js = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
    P = json.loads(js[js.index("{"):js.rindex("}") + 1])
    occ = [q for z in P["zones"] for r in rings_of_d(z["zone"]) for q in valid(r)]
    occ += [q for sp in rooms if not nic(sp) for r in rings_of_d(sp["d"]) for q in valid(r)]
    occ += [q for sp in P["spaces"] if sp["type"] != "Not in contract" for r in rings_of_d(sp["d"]) for q in valid(r)]
    u = unary_union([q.buffer(1500) for q in occ]).buffer(-1500)
    used = [q for z in P["zones"] for r in rings_of_d(z["zone"]) for q in valid(r)]
    used += [q for sp in P["spaces"] if sp["type"] != "Not in contract" for r in rings_of_d(sp["d"]) for q in valid(r)]
    used += [q for sp in rooms if sp["name"] in ("Common area", "Terrace") for r in rings_of_d(sp["d"]) for q in valid(r)]
    used = unary_union([q.buffer(300) for q in used])           # not the cores (toilets, shafts, lifts): their fixtures aren't furniture
    slab = max((u.geoms if isinstance(u, MultiPolygon) else [u]), key=lambda q: q.area)
    slab = Polygon(slab.exterior).buffer(150).simplify(40)          # out to the façade line
    struct = walls + [g.buffer(60) for g in glass] + [l.buffer(60) for l in blines]
    b = unary_union([q.buffer(2000) for q in struct + [slab]]).buffer(-2000)
    building = max((b.geoms if isinstance(b, MultiPolygon) else [b]), key=lambda q: q.area)
    rest = Polygon(building.exterior).difference(slab.buffer(100))
    # the thin rim left between the shell and the slab is no mass: drawn by its outline it would roof the whole floor
    rest = rest.buffer(-1500).buffer(1500)
    context = [Polygon(q.exterior).simplify(60) for q in (rest.geoms if isinstance(rest, MultiPolygon) else [rest]) if q.area > 40e6 and not q.interiors]
    near = slab.buffer(300)
    walls = [w for w in (near.intersection(q) for q in walls) for w in (w.geoms if hasattr(w, "geoms") else [w]) if w.geom_type == "Polygon" and w.area > 2e4]
    glass = [g for g in glass if g.intersects(slab)]
    plants = [p for p in plants if slab.contains(Point(p[0], p[1]))]
    print(f"slab {slab.area / 1e6:.0f} m2, bounds {[round(v) for v in slab.bounds]}; context masses {len(context)} ({sum(q.area for q in context) / 1e6:.0f} m2); walls {len(walls)}")

    # furniture: per block once (placed by its uses), and the loose linework tile by tile
    bshapes, kinds = {}, Counter()
    for bid, g in bsub.items():
        subs, fl = g.get(("s", "furn"), []), g.get(("f", "furn"), [])
        if not subs and not fl: continue
        tops = g.get(("s", "base"), [])                  # in a furniture block, "base" lines are its desk tops (the pods)
        fl = fl + g.get(("f", "base"), [])
        sh = furniture(subs, fl, tops)
        if sh: bshapes[bid] = sh
    def placed_in(bid, m):
        xs = [q for _, sh in bshapes[bid] for q in tf(m, list(sh.exterior.coords))]
        return used.contains(Point(sum(x for x, _ in xs) / len(xs), sum(y for _, y in xs) / len(xs)))
    uses = [(bid, m) for bid, m in uses if bid not in bshapes or placed_in(bid, m)]
    buses = [[bid] + [round(v, 4) if i < 4 else round(v, 1) for i, v in enumerate(m)] for bid, m in uses if bid in bshapes]
    for bid, m in uses:
        for k, _ in bshapes.get(bid, []): kinds[k] += 1
    TILE = 12000
    tiles = defaultdict(lambda: ([], []))
    for p in loose_furn_s: tiles[(int(p[0][0] // TILE), int(p[0][1] // TILE))][0].append(p)
    for p in loose_furn_f: tiles[(int(p[0][0] // TILE), int(p[0][1] // TILE))][1].append(p)
    lshapes = []
    for key, (subs, fl) in tiles.items():
        lshapes += [(k, q) for k, q in furniture(subs, fl) if used.contains(q.representative_point())]
    for k, _ in lshapes: kinds[k] += 1
    # placed block furniture also at world coordinates for the check picture and the report
    print(f"furniture: {dict(kinds)} ({len(bshapes)} blocks, {len(buses)} placements, {len(lshapes)} loose) in {time.time() - t0:.0f}s")

    # floors: the deck's spaces, as the legend colours them
    floors = []
    for s in [s for s in P["spaces"] if s["type"] != "Not in contract"]:      # the hotel band: grey masses already
        rs = [q for r in rings_of_d(s["d"]) for q in valid(r)]
        # a space's holes (its furniture, cut out for hover) are not floors of their own: its outer rings only
        for q in rs:
            if not any(o is not q and o.area > q.area and o.contains(q.representative_point()) for o in rs):
                floors.append([s["type"], ring_out(q.simplify(20))])

    # walls that border the legend's glass rooms are those rooms' partitions: the axo shows them as the rooms' purple glass
    # (as the deck's axo does), so only the rest stand solid (cores, services, the shell)
    rooms_u = unary_union([Polygon(r).buffer(250) for t, r in floors if t in GLASS_ROOMS])
    solid, parts = [], []
    for q in walls: (parts if q.intersection(rooms_u).area > 0.5 * q.area else solid).append(q)
    print(f"walls: {len(solid)} solid, {len(parts)} room partitions (shown as glass)")

    # the beats: the floor in three, west to east; the labels the deck's axo calls out, found in each third
    x0, _, x1, _ = slab.bounds
    third = (x1 - x0) / 3
    beats = {"west": [round(x0), round(x0 + third * 1.08)], "middle": [round(x0 + third * 0.96), round(x0 + third * 2.04)],
             "east": [round(x0 + third * 1.92), round(x1)]}
    NAME = {"Reception": "Reception", "Boardroom": "Board Room", "Cafeteria": "Café", "Training room": "Training Room",
            "The Hatchery": "The Hatchery", "Departmental room": "Departmental Room", "Collaboration huddle": "Collaboration Huddle",
            "Executive corner cabin": "Executive Cabin", "Quick sprint": "Quick Sprint Room", "Studio": "Studio", "Zen room": "Zen Room",
            "Visitor hub": "Visitor Hub", "Coffee corner": "Coffee Corner"}
    ORDER = list(NAME)
    labels = {}
    for b, (a, c) in beats.items():
        lo, hi = a + third * 0.06, c - third * 0.06            # not on the very edge of the frame
        got = []
        for t in ORDER:
            cand = [s for s in P["spaces"] if s["type"] == t and lo <= s["x"] <= hi]
            if cand:
                s = max(cand, key=lambda s: s["m2"]); got.append([NAME[t], round(s["x"]), round(s["y"])])
        tps = [tp for tp in terrace if lo <= tp.representative_point().x <= hi]
        if tps:                                                # one call-out per terrace in view (a terrace drawn as several outlines)
            c_ = max(tps, key=lambda q: q.area).representative_point(); got.insert(1, ["Terrace", round(c_.x), round(c_.y)])
        for z in P["zones"]:
            if lo <= z["x"] <= hi: got.append([f"Workhall · {z['name']}", round(z["x"]), round(z["y"])])
        labels[b] = got[:9]

    data = {
        "source": "DXF plan toolkit: instanced.svg + rooms.json (ACKO.dxf, Option 02A); spaces from data/plan-dxf.js",
        "built": time.strftime("%Y-%m-%d"),
        "slab": ring_out(slab),
        "context": [ring_out(q) for q in context],
        "walls": [poly_out(q) for q in solid],
        "columns": [ring_out(q.simplify(10)) for q in columns],
        "glass": [[[round(x), round(y)] for x, y in g.coords] for g in glass],
        "floors": floors,
        "terrace": [ring_out(t.simplify(30)) for t in terrace],
        "greens": [ring_out(q.simplify(30)) for p in W[("f", "green")] for q in valid(p) if q.area > 5e5],
        "blocks": {bid: [[k, ring_out(q)] for k, q in sh] for bid, sh in bshapes.items()},
        "uses": buses,
        "loose": [[k, ring_out(q)] for k, q in lshapes],
        "plants": plants,
        "beats": beats,
        "labels": labels,
    }
    out = os.path.join(ROOT, "data", "axo-dxf.js")
    txt = "/* the axo's model, made by tools/acko/axo_dxf.py from the DXF plan toolkit's output; plan mm, y down */\nwindow.AXO_DXF = " + json.dumps(data, separators=(",", ":")) + ";\n"
    open(out, "w", encoding="utf-8").write(txt)
    print(f"wrote {out}: {len(txt) / 1e6:.2f} MB in {time.time() - t0:.0f}s")
    print("labels:", json.dumps(labels, ensure_ascii=False))
    check(data, slab, walls, columns, glass, bshapes, uses, lshapes, plants)


def check(data, slab, walls, columns, glass, bshapes, uses, lshapes, plants):
    """the model on the plan, each class in its colour"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    x0, y0, x1, y1 = slab.bounds
    fig = plt.figure(figsize=((x1 - x0) / 6000, (y1 - y0) / 6000 + 0.4), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0 - 2000, x1 + 2000); ax.set_ylim(y1 + 2000, y0 - 2000); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(MP(list(slab.exterior.coords), fc="#ececec", ec="#888", lw=.6))
    for r in data["context"]: ax.add_patch(MP(r, fc="#bdbdbd", ec="#666", lw=.4))
    COL = {"Phone booth": "#d5ceed", "Quick sprint": "#cfc5ea", "Collaboration huddle": "#c9bde8", "Departmental room": "#c2b4e4", "Boardroom": "#b9a8e0",
           "Cafeteria": "#f3ead2", "Reception": "#efe6da", "Training room": "#d9d0e8"}
    for t, r in data["floors"]: ax.add_patch(MP(r, fc=COL.get(t, "#dcdcdc"), ec="none"))
    for r in data["terrace"] + data["greens"]: ax.add_patch(MP(r, fc="#b9d7a8", ec="none"))
    for q in walls: ax.add_patch(MP(list(q.exterior.coords), fc="#222", ec="none"))
    for q in columns: ax.add_patch(MP(list(q.exterior.coords), fc="#777", ec="none"))
    for g in glass: ax.plot(*zip(*g.coords), color="#3a7bbf", lw=.5)
    FC = {"chair": "#555", "desk": "#d6b48a", "store": "#ffffff"}
    for bid, m in uses:
        for k, q in bshapes.get(bid, []):
            ax.add_patch(MP(tf(m, list(q.exterior.coords)), fc=FC[k], ec="#333", lw=.15))
    for k, q in lshapes: ax.add_patch(MP(list(q.exterior.coords), fc=FC[k], ec="#333", lw=.15))
    for x, y, r in plants: ax.add_patch(plt.Circle((x, y), r, color="#4c8a46"))
    for b, L in data["labels"].items():
        for n, x, y in L: ax.plot(x, y, "o", color="#980000", ms=2); ax.text(x, y - 600, n, fontsize=3, color="#980000", ha="center")
    os.makedirs(os.path.join(ROOT, "tools", "_work", "axo"), exist_ok=True)
    p = os.path.join(ROOT, "tools", "_work", "axo", "check.png"); fig.savefig(p); print("check:", p)


if __name__ == "__main__":
    main(sys.argv[1])
