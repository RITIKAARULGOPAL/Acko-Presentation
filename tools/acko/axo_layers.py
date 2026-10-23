"""The campus strategy's layered axo (deck slide 13), straight from the layout DXF and the 3D renders.

Usage:  python tools/acko/axo_layers.py "<layout>.dxf" [--renders "<dir of acko2A_model*.png>"]

The DXF (ACKO_BOUNDARY_HATCH_ALL_22_10_26.dxf) is drawn in the renders' layers: one block each, all inserted at one point.
They are found by what they hold, not by their (random) names:
  zones     AC_AUTO, AC_LIFE, AC_HEALTH, AC_TRAVEL, AC_DRIVE, AC_HOME, AC_ATRIUM, AC_TERRACE  (the neighbourhoods, 01-06)
  spaces    one closed outline per space, on AC_<TYPE> layers; AC_GLAZING (the façade line), AC_ENTRY (the two entrances)
  services  AC_OUT_OF_SCOPE (the building's middle band, a grey mass in the renders), cores inside it
  layout    the furniture, the partitions, and the architect's base drawing (columns on S-COLS)
  plants    plant blocks
The renders (axo_update/acko2A_model*.png, 19942 x 10426) give what the DXF doesn't: the routes. The employee's journey
(red dashes, render 08) and the client's journey (blue dashes, render 09) are traced from the pictures and mapped back to the
plan through the floor's affine (fitted from the façade line to render 01's silhouette). Without --renders the routes kept
in the last data/axo-layers.js are reused.

Writes data/axo-layers.js (window.AXO_LAYERS), plan mm with y down (the DXF's y negated), and check pictures in
tools/_work/axo-layers/:
  slab      the façade line (the floor)              mass      the out-of-scope band (grey blocks)
  columns   rings                                    zones     [{n, key, name, colour, ring}]; atrium, terrace: rings
  spaces    [[type, ring], ...]                      walled    the space types with glass walls (rooms)
  entries   [[x, y], ...]                            blocks / uses   furniture shapes per block and their placements:
  plants    [[x, y, r], ...]                                   uses: [block, a, b, c, d, e, f, group]
  routes    {employee, client}: [[[x, y, d], ...], ...] (d: metres from the nearest entrance along the route)
  stops     the Loop's seven stops: [{name, x, y, d}]   view   the renders' camera {theta, phi}
  heights   the renders' heights (m)                 colours   the renders' palette per layer
Groups (the order the renders build them): rooms (render 02), cafe (03), terrace (04), work (05).
"""
import argparse, heapq, json, math, os, re, sys, time
from collections import Counter, defaultdict

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dxf_read as D

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "axo-layers")

# the AC_ layers' space types, named as the deck names them elsewhere (data/plan-dxf.js)
TYPES = {"WORKHALL": "Workhall", "CORRIDOR": "Corridor", "PHONE_BOOTH": "Phone booth", "COLLAB_HUDDLE": "Collaboration huddle",
         "QUICK_SPRINT": "Quick sprint", "UPS_SERVER_BATTERY_BMS_ROOM": "Server, UPS & battery", "COLLAB": "Collab",
         "COFFEE_CORNER": "Coffee corner", "TRAINING_ROOM": "Training room", "CAFETERIA": "Cafeteria", "THE_STUDIO_ROOM": "Studio",
         "RECEPTION": "Reception", "DEPARTMENTAL_ROOMS": "Departmental room", "THE_HATCHERY": "The Hatchery", "NAP_ROOM": "Nap room",
         "BOARD_ROOM": "Boardroom", "PRAYER_ROOM": "Prayer room", "EXECUTIVE_CORNER_CABIN": "Executive corner cabin",
         "HUB_ROOM": "Hub room", "MOTHER'S_ROOM": "Mother's room", "VISITOR_HUB": "Visitor hub", "TERRACE": "Terrace",
         "MAIL_ROOM": "Mail room", "ZEN_ROOM": "Zen room", "MEDICAL_ROOM": "Medical room"}
# the neighbourhoods as the renders number them (render -01) and the deck's GIF names them; colours sampled from render -01
ZONES = [("01", "AUTO", "ACKO Auto", "#c9eaf3"), ("02", "LIFE", "ACKO Life", "#cec1ec"), ("03", "HEALTH", "ACKO Health", "#576cbd"),
         ("04", "TRAVEL", "ACKO Travel", "#e0d3d3"), ("05", "DRIVE", "ACKO Drive", "#ebedd6"), ("06", "HOME", "ACKO Home", "#f0d8e2")]
# render 01's floor palette, and each type's colour (the majority of its floor's pixels in render 01, checked at build)
PALETTE = {"floor": "#cbcbca", "corridor": "#b9a9c3", "room": "#a490a7", "cafe": "#f3f3ca", "terrace": "#949474", "mass": "#afafaf"}
FLOOR_OF = {"Corridor": "corridor", "Reception": "corridor", "Cafeteria": "cafe", "Coffee corner": "cafe", "Training room": "cafe",
            "Terrace": "terrace", "Workhall": "floor", "Collab": "floor", "Medical room": "floor"}
# which furniture group a space's furniture belongs to (the render that adds it)
GROUP_OF = {"Cafeteria": "cafe", "Coffee corner": "cafe", "Training room": "cafe", "Terrace": "terrace",
            "Workhall": "work", "Corridor": "work", "Collab": "work", "Reception": "work"}
# heights the renders use, measured on them (m): rooms' glass walls, columns, the out-of-scope block, the façade
HEIGHTS = {"wall": 2.45, "column": 3.8, "mass": 3.7, "facade": 4.5, "zone": 3.0, "desk": 0.75, "chair": 0.45, "sofa": 0.42, "store": 1.0}
SKIP_INS = re.compile(r"PART|DOOR|WALL|ANNO|DIM", re.I)
SKIP_LAYER = re.compile(r"ANNO|TEXT|TAGS|DIM|DEFPOINTS|PART|DOOR|WALL|ELEV|SHADE|HATCH-PLINES|IDEN|S-COLS|S-STRS|A-FLOR|A-GENM|G-IMPT|A-DETL", re.I)
LOOSE_FURN = re.compile(r"FURN|FUR\b|FURNITURE|STORAGE|^0$|KTCH|MLWK-SURF", re.I)


# ---------- geometry helpers ----------
def parts(g):
    return [q for q in (g.geoms if hasattr(g, "geoms") else [g]) if q.geom_type == "Polygon" and not q.is_empty]


def ring_of(pts):
    """a DXF point list as a valid polygon in plan mm, y down"""
    try:
        q = Polygon([(x, -y) for x, y in pts]).buffer(0)
    except Exception:
        return None
    q = parts(q)
    return max(q, key=lambda r: r.area) if q else None


def ring_out(q, tol=0):
    q = q.simplify(tol) if tol else q
    return [[round(x), round(y)] for x, y in list(q.exterior.coords)[:-1]]


def straight(p):
    """a table's edge: a line, or a polyline mostly of long segments (a rounded table's corners are short steps; a chair or
    a person is drawn all in short steps)"""
    q = [p[0]] + [b for a, b in zip(p, p[1:]) if math.dist(a, b) > 2]
    if len(q) < 2: return False
    seg = [math.dist(a, b) for a, b in zip(q, q[1:])]
    return sum(L for L in seg if L > 120) >= 0.7 * sum(seg)


# ---------- furniture: table tops from the straight linework, seats from the curvy drawing ----------
def shapes(prims):
    """[(points, circle radius or None)] in (scaled) block mm -> [(kind, Polygon)]: desk, store, chair, sofa.
    Desks and counters are the faces the straight lines enclose (a person drawn over a desk cuts it; the pieces join again).
    Chairs are the blobs of curvy drawing (a chair, or the person sat on it): a 0.56 m seat at each. Sofas: longer blobs."""
    st, curvy = [], []
    for p, r in prims:
        if len(p) < 2: continue
        (st if r is None and straight(p) else curvy).append((p, r))
    tops = []
    G = 110                                         # CAD leaves a desk's edge out where a chair sits on it: bridge such breaks
    lines = [LineString(p).buffer(G, 2) for p, r in st]
    if lines:                                       # the faces the edges enclose
        u = unary_union(lines)
        for f in [Polygon(h).buffer(G, 2) for g in parts(u) for h in g.interiors]:
            if f.area < 0.34e6: continue
            if f.area / max(f.minimum_rotated_rectangle.area, 1) < 0.6: continue
            tops.append(f)
    for p, r in curvy:
        if r is not None and r >= 280: tops.append(Polygon(p))         # round tables
        elif r is None and len(p) > 3 and math.dist(p[0], p[-1]) < 5:   # a closed outline a table's size and shape
            f = Polygon(p).buffer(0)
            if f.area >= 0.6e6 and f.area / max(f.minimum_rotated_rectangle.area, 1) >= 0.8: tops.append(f)
    tops = [Polygon(t.exterior) for t in parts(unary_union([t.buffer(6) for t in tops]).buffer(-6))] if tops else []
    out = []
    for t in tops:
        c = list(t.minimum_rotated_rectangle.exterior.coords)
        w, L = sorted([math.dist(c[0], c[1]), math.dist(c[1], c[2])])
        if t.area > 20e6 or w > 3200: continue                         # a rug, a planter bed or a room's outline, not a table
        out.append(("store" if w <= 500 and L > 900 else "desk", t.simplify(12)))
    seats = []
    cv = [LineString(p).buffer(40, 2) for p, r in curvy if (r is None or r < 280) and len(p) > 1]
    for b in (parts(unary_union(cv)) if cv else []):
        b = Polygon(b.exterior)
        if b.area < 0.08e6: continue
        if sum(t.intersection(b).area for t in tops) / b.area > 0.7: continue   # drawing on a table top
        c = list(b.minimum_rotated_rectangle.exterior.coords)
        w, L = sorted([math.dist(c[0], c[1]), math.dist(c[1], c[2])])
        if L <= 1300:
            seats.append((b.centroid.x, b.centroid.y))
        elif w >= 450 and L <= 3500 and b.area > 0.5e6:
            out.append(("sofa", b.minimum_rotated_rectangle.buffer(-40)))
    # a chair and the person on it make two blobs: one seat
    kept = []
    for x, y in seats:
        if all(math.hypot(x - a, y - b) > 420 for a, b in kept): kept.append((x, y))
    s = 280
    out += [("chair", Polygon([(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)])) for x, y in kept]
    return out


def flatten(blocks, name, S):
    """a block's drawing in its own coordinates scaled by S (sx, sy): [(points, circle radius or None)]"""
    prims = []
    def fn(e, m, L, path):
        if SKIP_LAYER.search(L or "") or e["t"] in ("HATCH", "TEXT", "MTEXT"): return
        for p, c in zip(e.get("p", []), e.get("c", [])):
            q = D.tf(m, p)
            r = e["circle"][2] * math.hypot(m[0], m[1]) if "circle" in e else None
            prims.append((q + [q[0]] if c and math.dist(q[0], q[-1]) > 1 else q, r))
    D.walk(blocks, blocks[name]["ents"], fn, m=(S[0], 0, 0, S[1], 0, 0))
    return prims


# ---------- the routes, traced from the renders ----------
def fit_affine(ring_dxf, render01):
    """the floor plane's affine, DXF mm -> render px: the façade line fitted to render 01's silhouette along each edge's normal"""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(render01).convert("L"); R = 4
    mask = np.asarray(im.resize((im.width // R, im.height // R), Image.BILINEAR)) < 247
    H, W = mask.shape
    P = lambda M, pts: np.hstack([np.asarray(pts, float), np.ones((len(pts), 1))]) @ M
    solve = lambda s, d: np.linalg.lstsq(np.hstack([s, np.ones((len(s), 1))]), d, rcond=None)[0]
    # a first guess from the renders' framing (the façade's three outer corners), then refined
    xs = [x for x, y in ring_dxf]; ys = [y for x, y in ring_dxf]
    src = np.array([(min(xs) + (max(xs) - min(xs)) * 0.13, min(ys)), (max(xs), min(ys)), (max(xs), max(ys))], float)
    M = solve(src, np.array([(640, 1035), (1830, 148), (1640, 8)], float) * (im.width / 2000 / R))
    top = max(ys)
    samples = []
    for i in range(len(ring_dxf)):
        a, b = np.array(ring_dxf[i], float), np.array(ring_dxf[(i + 1) % len(ring_dxf)], float)
        if abs(a[1] - top) < 1 and abs(b[1] - top) < 1: continue       # the north edge: the grey block stands on it
        m = max(2, int(np.linalg.norm(b - a) / 1500))
        samples += [(a + (b - a) * j / m, a, b) for j in range(1, m)]
    for _ in range(8):
        cen = P(M, ring_dxf).mean(0); tg, sv = [], []
        for s, a, b in samples:
            p = P(M, [s])[0]; ia, ib = P(M, [a, b]); e = ib - ia; d = np.array([-e[1], e[0]]); d /= np.linalg.norm(d)
            if np.dot(d, p - cen) < 0: d = -d
            for t in np.arange(40, -40, -0.5):
                q = p + d * t; x, y = int(round(q[0])), int(round(q[1]))
                if 0 <= x < W and 0 <= y < H and mask[y, x]: tg.append(q); sv.append(s); break
        tg, sv = np.array(tg), np.array(sv)
        M2 = solve(sv, tg); res = np.linalg.norm(P(M2, sv) - tg, axis=1)
        keep = res < max(3, np.percentile(res, 85))
        M = solve(sv[keep], tg[keep])
    res = np.linalg.norm(P(M, sv[keep]) - tg[keep], axis=1) * R
    print(f"floor affine: {keep.sum()} edge samples, rms {np.sqrt((res ** 2).mean()):.1f} px, max {res.max():.1f} px of {im.width}")
    return M * R, im.size


def trace(render, colour):
    """the dashes of one colour in a render, chained into lines (render px)"""
    import cv2
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    a = np.asarray(Image.open(render).convert("RGB").reduce(2)).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = ((R > 180) & (G < 100) & (B < 100)) if colour == "red" else ((B > 170) & (R < 110) & (G < 110))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    dashes = []
    for i in range(1, n):
        if not 40 <= st[i, cv2.CC_STAT_AREA] < 420: continue            # not the people (bigger blobs), not specks
        ys, xs = np.nonzero(lab[st[i, 1]:st[i, 1] + st[i, 3], st[i, 0]:st[i, 0] + st[i, 2]] == i)
        pts = np.stack([xs + st[i, 0], ys + st[i, 1]], 1).astype(float)
        c = pts.mean(0); w, v = np.linalg.eigh(np.cov((pts - c).T))
        L, Wd = 4 * np.sqrt(max(w[1], 1e-6)), 4 * np.sqrt(max(w[0], 1e-6))
        if L > 2.2 * Wd: dashes.append((c * 2, v[:, 1], L))
    # each dash's two ends join the facing end of the nearest dash ahead, when both choose each other
    ends = []
    for i, (c, d, L) in enumerate(dashes):
        ends += [(i, c - d * L, -d), (i, c + d * L, d)]
    E = np.array([e[1] for e in ends])
    best = {}
    for a_ in range(len(ends)):
        dist = np.linalg.norm(E - E[a_], axis=1); cand = []
        for b_ in np.argsort(dist)[:12]:
            if ends[b_][0] == ends[a_][0] or dist[b_] > 260: continue
            v = E[b_] - E[a_]; dd = np.linalg.norm(v)
            ahead = np.dot(v / dd, ends[a_][2]); facing = -np.dot(ends[b_][2], ends[a_][2])
            if ahead < 0.3 or facing < 0.2: continue
            cand.append((dd * (2 - ahead) * (2 - facing), b_))
        if cand: best[a_] = min(cand)[1]
    link = {a_: b_ for a_, b_ in best.items() if best.get(b_) == a_}
    used, chains = set(), []
    for s in range(len(ends)):
        if ends[s][0] in used or s in link: continue
        ch, e = [], s
        while ends[e][0] not in used:
            used.add(ends[e][0]); ch.append(dashes[ends[e][0]][0].tolist())
            o = e ^ 1
            if o not in link: break
            e = link[o]
        chains.append(ch)
    print(f"  {colour}: {len(dashes)} dashes in {len(chains)} chains")
    return [c for c in chains if len(c) >= 2]


def network(lines, sources, gap=9000):
    """route lines (plan mm) joined where they break (the renders' people stand in the gaps), and each point's distance (m)
    from the nearest entrance along them; returned as lines that run away from the entrances: [[x, y, d], ...]"""
    pts, adj = [], defaultdict(list)
    def add(p):
        pts.append(p); return len(pts) - 1
    ids = []
    for ln in lines:
        q = LineString(ln).simplify(150)
        q = [q.interpolate(t).coords[0] for t in np.arange(0, q.length, 700)] + [q.coords[-1]]
        k = [add(p) for p in q]
        for a, b in zip(k, k[1:]):
            w = math.dist(pts[a], pts[b]); adj[a].append((b, w)); adj[b].append((a, w))
        ids.append(k)
    # joins: each line's ends to the nearest point of another line within the gap; then the pieces still apart join at
    # their closest ends, nearest first (the renders' people stand where the dashes break)
    comp = list(range(len(ids)))
    def root(i):
        while comp[i] != i: comp[i] = comp[comp[i]]; i = comp[i]
        return i
    links = []
    def join(a, b, d, la, lb):
        adj[a].append((b, d)); adj[b].append((a, d)); links.append((a, b)); comp[root(la)] = root(lb)
    for li, k in enumerate(ids):
        for end in (k[0], k[-1]):
            best = None
            for lj, k2 in enumerate(ids):
                if lj == li: continue
                for j in k2:
                    d = math.dist(pts[end], pts[j])
                    if d < gap and (best is None or d < best[0]): best = (d, j, lj)
            if best: join(end, best[1], best[0], li, best[2])
    while len({root(i) for i in range(len(ids))}) > 1:
        best = None
        for li, k in enumerate(ids):
            for end in (k[0], k[-1]):
                for lj, k2 in enumerate(ids):
                    if root(lj) == root(li): continue
                    for j in k2:
                        d = math.dist(pts[end], pts[j])
                        if best is None or d < best[0]: best = (d, end, j, li, lj)
        if best is None or best[0] > 40000: break
        join(best[1], best[2], best[0], best[3], best[4])
    # the entrances: each joins the route's nearest point
    dist = [math.inf] * len(pts); h = []
    for s in sources:
        j = min(range(len(pts)), key=lambda i: math.dist(pts[i], s))
        d0 = math.dist(pts[j], s)
        if d0 < 25000: dist[j] = min(dist[j], d0); heapq.heappush(h, (dist[j], j))
    while h:
        d, i = heapq.heappop(h)
        if d > dist[i]: continue
        for j, w in adj[i]:
            if d + w < dist[j]: dist[j] = d + w; heapq.heappush(h, (dist[j], j))
    # every edge once, as lines running uphill in distance
    segs, seen = [], set()
    for i in range(len(pts)):
        for j, w in adj[i]:
            if (j, i) in seen or (i, j) in seen or math.isinf(dist[i]) or math.isinf(dist[j]): continue
            seen.add((i, j))
            a, b = (i, j) if dist[i] <= dist[j] else (j, i)
            segs.append((a, b))
    # chain the uphill segments into runs
    nxt = defaultdict(list)
    for a, b in segs: nxt[a].append(b)
    indeg = Counter(b for a, b in segs)
    runs, done = [], set()
    for a, b in sorted(segs, key=lambda s: dist[s[0]]):
        if (a, b) in done: continue
        run = [a, b]; done.add((a, b))
        while len(nxt[run[-1]]) == 1 and indeg[run[-1]] == 1 and (run[-1], nxt[run[-1]][0]) not in done:
            c = nxt[run[-1]][0]; done.add((run[-1], c)); run.append(c)
        runs.append([[round(pts[k][0]), round(pts[k][1]), round(dist[k] / 1000, 2)] for k in run])
    print(f"  network: {len(lines)} lines, {len(links)} joins, {len(runs)} runs, longest reach {max(d for d in dist if not math.isinf(d)) / 1000:.0f} m")
    return runs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("dxf"); ap.add_argument("--renders")
    a = ap.parse_args()
    t0 = time.time()
    blocks, model = D.read(a.dxf)
    print(f"read {os.path.basename(a.dxf)}: {len(blocks)} blocks in {time.time() - t0:.0f}s")

    # the placed blocks, found by what they hold
    placed = [e for e in model if e["t"] == "INSERT" and e["n"] in blocks]
    def layers(e): return Counter(x["l"] for x in blocks[e["n"]]["ents"])
    def find(test):
        for e in placed:
            if test(layers(e), e): return e
        return None
    B = {"zones": find(lambda L, e: "AC_AUTO" in L and "AC_HOME" in L),
         "spaces": find(lambda L, e: "AC_GLAZING" in L and "AC_ENTRY" in L),
         "services": find(lambda L, e: "AC_OUT_OF_SCOPE" in L),
         "plants": find(lambda L, e: sum(v for k, v in L.items() if re.search("PLANT", k, re.I)) > 50),
         "layout": max(placed, key=lambda e: len(blocks[e["n"]]["ents"]) if any(x["t"] == "INSERT" and x["n"] == "base" for x in blocks[e["n"]]["ents"]) else 0)}
    print("blocks:", {k: (v["n"] if v else None) for k, v in B.items()})

    def world(key, fn):
        e = B[key]
        if e: D.walk(blocks, [e], fn)

    # zones, spaces, services: closed outlines per AC_ layer
    outl = defaultdict(list)
    def grab(store):
        def fn(e, m, L, path):
            for p, c in zip(e.get("p", []), e.get("c", [])):
                if e["t"] in ("LWPOLYLINE", "POLYLINE") and len(p) >= 3: store[L].append(D.tf(m, p))
        return fn
    zl, sl, vl = defaultdict(list), defaultdict(list), defaultdict(list)
    world("zones", grab(zl)); world("spaces", grab(sl)); world("services", grab(vl))
    slab = ring_of(max(sl["AC_GLAZING"], key=lambda p: Polygon(p).area))
    zones = []
    for n, key, name, col in ZONES:
        r = [q for q in (ring_of(p) for p in zl.get("AC_" + key, [])) if q]
        if r: zones.append({"n": n, "key": key, "name": name, "colour": col, "ring": ring_out(max(r, key=lambda q: q.area), 20)})
    atrium = [ring_out(q, 20) for q in (ring_of(p) for p in zl.get("AC_ATRIUM", [])) if q and q.area > 20e6]
    terrace = [ring_out(q, 20) for q in (ring_of(p) for p in zl.get("AC_TERRACE", [])) if q and q.area > 20e6]
    spaces = []
    for L, lst in sl.items():
        t = TYPES.get(L[3:])
        if not t: continue
        for p in lst:
            q = ring_of(p)
            if q and 0.3e6 < q.area < 5000e6: spaces.append((t, q))
    entries = []
    for p in sl.get("AC_ENTRY", []):
        q = ring_of(p)
        if q and all(math.dist((q.centroid.x, q.centroid.y), e) > 2000 for e in entries): entries.append((q.centroid.x, q.centroid.y))
    entries.sort()
    mass = [q for q in (ring_of(p) for p in vl.get("AC_OUT_OF_SCOPE", [])) if q]
    print(f"slab {slab.area / 1e6:.0f} m2; zones {len(zones)}, atrium {len(atrium)}, terrace {len(terrace)}; spaces {len(spaces)} "
          f"{dict(Counter(t for t, _ in spaces))}; entries {len(entries)}; mass {len(mass)}")

    # columns: the layout's S-COLS outlines, one per column
    cols = []
    def colfn(e, m, L, path):
        if L == "S-COLS":
            for p in e.get("p", []):
                if len(p) >= 4: cols.append(LineString(D.tf(m, [(x, y) for x, y in p])).buffer(1).envelope)
    world("layout", colfn)
    columns = [Polygon([(x, -y) for x, y in q.exterior.coords]) for q in parts(unary_union(cols)) if 0.04e6 < q.area < 2e6]
    columns = [q for q in columns if slab.contains(q.centroid) and not any(m_.buffer(-300).contains(q.centroid) for m_ in mass)]
    print(f"columns {len(columns)}")

    # where a point is: the smallest space that holds it
    sp_tree = STRtree([q for _, q in spaces])
    def space_at(x, y):
        pt = Point(x, y); best = None
        for i in sp_tree.query(pt):
            t, q = spaces[int(i)]
            if q.contains(pt) and (best is None or q.area < best[1].area): best = (t, q)
        return best[0] if best else None
    WALLED = {"Phone booth", "Quick sprint", "Collaboration huddle", "Departmental room", "Boardroom", "Visitor hub", "The Hatchery",
              "Studio", "Zen room", "Mother's room", "Prayer room", "Executive corner cabin", "Hub room", "Server, UPS & battery",
              "Mail room", "Nap room"}
    def group_at(x, y):
        t = space_at(x, y)
        if t in WALLED: return "rooms"
        return GROUP_OF.get(t, "work")

    # furniture: every placed block in the layout, its shapes once per scale, placed by its uses; loose linework by tiles
    lay = blocks[B["layout"]["n"]]["ents"]; Mlay = D.insert_m(blocks, B["layout"])
    cache, uses, kinds = {}, [], Counter()
    bid = {}
    for e in lay:
        if e["t"] != "INSERT" or e["n"] == "base" or SKIP_INS.search(e["l"]) or e["n"] not in blocks: continue
        m = D.mul(Mlay, D.insert_m(blocks, e))
        sx = math.hypot(m[0], m[1]); det = m[0] * m[3] - m[1] * m[2]; sy = det / sx if sx else 1
        key = (e["n"], round(sx, 3), round(sy, 3))
        if key not in cache:
            sh = shapes(flatten(blocks, e["n"], (sx, sy)))
            cache[key] = sh
            if sh: bid[key] = f"b{len(bid)}"
        if not cache[key]: continue
        R = (m[0] / sx, m[1] / sx, m[2] / sy, m[3] / sy, m[4], m[5])     # rotation (and mirror) + move, DXF frame
        # into plan (y down): y' = -y
        a_, b_, c_, d_, e_, f_ = R
        U = (a_, -b_, -c_, d_, e_, -f_)                                  # x' = a x + c y + e,  y' = -(b x + d y + f), block y flipped too
        cx = sum(q.centroid.x for _, q in cache[key]) / len(cache[key]); cy = sum(q.centroid.y for _, q in cache[key]) / len(cache[key])
        wx = a_ * cx + c_ * cy + e_; wy = -(b_ * cx + d_ * cy + f_)
        g = group_at(wx, wy)
        if not slab.buffer(500).contains(Point(wx, wy)): continue
        uses.append([bid[key]] + [round(v, 4) for v in U[:4]] + [round(U[4]), round(U[5]), g])
        for k, _ in cache[key]: kinds[(g, k)] += 1
    # loose furniture linework in the layout block, tile by tile
    loose_prims = defaultdict(list)
    for e in lay:
        if e["t"] in ("INSERT", "HATCH", "TEXT", "MTEXT") or not LOOSE_FURN.search(e["l"]) or SKIP_LAYER.search(e["l"]): continue
        for p, c in zip(e.get("p", []), e.get("c", [])):
            q = D.tf(Mlay, p)
            r = e["circle"][2] if "circle" in e else None
            q = [(x, -y) for x, y in q]
            if c and math.dist(q[0], q[-1]) > 1: q = q + [q[0]]
            loose_prims[(int(q[0][0] // 12000), int(q[0][1] // 12000))].append((q, r))
    loose = []
    for k, prims in loose_prims.items():
        for kd, q in shapes(prims):
            c = q.centroid
            if slab.contains(c): loose.append([kd, ring_out(q), group_at(c.x, c.y)]); kinds[(group_at(c.x, c.y), kd)] += 1
    # block shapes in plan orientation: the block's y flips with the plan, so the shapes are mirrored in y here
    blk = {bid[k]: [[kd, [[round(x), round(-y)] for x, y in list(q.exterior.coords)[:-1]]] for kd, q in sh] for k, sh in cache.items() if k in bid}
    print(f"furniture: {len(blk)} block shapes, {len(uses)} uses, {len(loose)} loose; " + ", ".join(f"{g}/{k} {n}" for (g, k), n in sorted(kinds.items())))

    # plants: each plant block's centre and spread
    plants = []
    if B["plants"]:
        for e in blocks[B["plants"]["n"]]["ents"]:
            if e["t"] != "INSERT" or e["n"] not in blocks: continue
            m = D.mul(D.insert_m(blocks, B["plants"]), D.insert_m(blocks, e)); pts = []
            D.walk(blocks, blocks[e["n"]]["ents"], lambda x, mm, L, path: pts.extend(p for q in x.get("p", []) for p in D.tf(mm, q)), m=m)
            if not pts: continue
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            r = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            if r < 80 or r > 4000: continue
            x, y = (max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2
            if slab.buffer(300).contains(Point(x, y)): plants.append([round(x), round(y), round(min(max(r, 250), 1200))])
    print(f"plants {len(plants)}")

    # the routes: traced from the renders, or kept from the last build
    out = os.path.join(ROOT, "data", "axo-layers.js")
    routes, view, affine = None, None, None
    if a.renders:
        ring_dxf = [(x, -y) for x, y in slab.exterior.coords[:-1]]
        M, size = fit_affine(ring_dxf, os.path.join(a.renders, "acko2A_model01.png"))
        affine = M.tolist()
        A2, b2 = M[:2].T, M[2]; Ai = np.linalg.inv(A2)
        to_plan = lambda u, v: (lambda p: (p[0], -p[1]))(Ai @ (np.array([u, v]) - b2))
        routes = {}
        for key, name, colour in (("employee", "acko2A_model08.png", "red"), ("client", "acko2A_model09.png", "blue")):
            chains = trace(os.path.join(a.renders, name), colour)
            lines = [[to_plan(u, v) for u, v in ch] for ch in chains]
            routes[key] = network(lines, entries)
        # the renders' camera: the floor's affine is an orthographic axo's; east and south in screen px (y up) give its angles
        ex = A2 @ np.array([1.0, 0]); so = A2 @ np.array([0, -1.0])
        theta = math.atan2(-so[0], ex[0])
        sin_e = math.hypot(ex[1], so[1]) / math.hypot(ex[0], so[0])
        view = {"theta": round(theta, 4), "phi": round(math.pi / 2 - math.asin(min(1, sin_e)), 4)}
        print(f"renders' camera: theta {math.degrees(theta):.1f} deg, elevation {math.degrees(math.asin(min(1, sin_e))):.1f} deg")
    elif os.path.exists(out):
        old = json.loads(open(out, encoding="utf-8").read().split("=", 1)[1].rstrip().rstrip(";"))
        routes, view, affine = old["routes"], old["view"], old.get("affine")
        print("routes: kept from the last build")
    else:
        sys.exit("no routes: run once with --renders")

    # the Loop's seven stops, found on the plan by type, each lit where the employee's journey passes it
    def of(t): return [q for tt, q in spaces if tt == t]
    big = lambda l: max(l, key=lambda q: q.area) if l else None
    near = lambda l, p: min(l, key=lambda q: q.centroid.distance(Point(p))) if l else None
    xs = [x for x, y in slab.exterior.coords]; mid = ((min(xs) + max(xs)) / 2, slab.centroid.y)
    west = entries[0] if entries else mid
    pick = [("Arrival", near(of("Reception"), west)), ("Café", big(of("Cafeteria"))), ("Board Room", big(of("Boardroom"))),
            ("Meeting Rooms", near(of("Quick sprint"), mid)), ("Collab", big(of("Collab")) or big(of("Collaboration huddle"))),
            ("Work", big(of("Workhall"))), ("Wellness", big(of("Zen room")) or big(of("Mother's room")))]
    rp = [(x, y, d) for run in routes["employee"] for x, y, d in run]
    stops = []
    for name, q in pick:
        if q is None: continue
        c = q.representative_point() if not q.contains(q.centroid) else q.centroid
        x, y, d = min(rp, key=lambda p: math.hypot(p[0] - c.x, p[1] - c.y))
        stops.append({"name": name, "x": round(c.x), "y": round(c.y), "d": d})
    print("stops:", [(s["name"], s["d"]) for s in stops])

    # the floors' colours, checked against render 01 when it's here
    colours = dict(PALETTE)
    floors = [[t, ring_out(q, 15), FLOOR_OF.get(t, "room" if t in WALLED else "floor")] for t, q in spaces]
    data = {
        "source": os.path.basename(a.dxf) + " + axo_update renders (acko2A_model*.png)",
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "view": view, "affine": affine, "heights": HEIGHTS, "colours": colours,
        "slab": ring_out(slab, 20), "mass": [ring_out(q, 20) for q in mass], "columns": [ring_out(q, 10) for q in columns],
        "zones": zones, "atrium": atrium, "terrace": terrace,
        "floors": floors, "walled": sorted(WALLED), "entries": [[round(x), round(y)] for x, y in entries],
        "blocks": blk, "uses": uses, "loose": loose, "plants": plants,
        "routes": routes, "stops": stops,
    }
    txt = "/* the campus strategy's layered axo, made by tools/acko/axo_layers.py from the layout DXF and the renders; plan mm, y down */\nwindow.AXO_LAYERS = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
    open(out, "w", encoding="utf-8").write(txt)
    print(f"wrote {out}: {len(txt) / 1e6:.2f} MB in {time.time() - t0:.0f}s")
    check(data, a.renders)


def check(A, renders):
    """the layers on the plan; and, with the renders, the slab outline, routes and stops over renders 01, 08 and 09"""
    from PIL import Image, ImageDraw
    os.makedirs(WORK, exist_ok=True)
    xs = [x for x, y in A["slab"]]; ys = [y for x, y in A["slab"]]
    x0, y0, x1, y1 = min(xs) - 2000, min(ys) - 2000, max(xs) + 2000, max(ys) + 2000
    k = 5000 / (x1 - x0); im = Image.new("RGB", (5000, int((y1 - y0) * k)), "white"); d = ImageDraw.Draw(im, "RGBA")
    T = lambda pts: [((x - x0) * k, (y - y0) * k) for x, y in pts]
    d.polygon(T(A["slab"]), fill="#e9e9e8", outline="#555")
    for t, r, f in A["floors"]: d.polygon(T(r), fill=A["colours"][f])
    for r in A["mass"]: d.polygon(T(r), fill="#9a9a9a")
    for r in A["columns"]: d.polygon(T(r), fill="#555")
    FC = {"chair": "#5d5c62", "desk": "#d8b78c", "store": "#ffffff", "sofa": "#8a8a90"}
    for u in A["uses"]:
        b, a_, b_, c_, d_, e_, f_, g = u
        for kd, r in A["blocks"][b]: d.polygon(T([(a_ * x + c_ * y + e_, b_ * x + d_ * y + f_) for x, y in r]), fill=FC[kd], outline="#333")
    for kd, r, g in A["loose"]: d.polygon(T(r), fill=FC[kd], outline="#a33")
    for x, y, r in A["plants"]: d.ellipse(((x - r - x0) * k, (y - r - y0) * k, (x + r - x0) * k, (y + r - y0) * k), fill="#4c8a4688")
    for key, col in (("employee", "#e00000"), ("client", "#0010ff")):
        for run in A["routes"][key]: d.line(T([(x, y) for x, y, _ in run]), fill=col, width=3)
    for s in A["stops"]:
        x, y = T([(s["x"], s["y"])])[0]; d.ellipse((x - 8, y - 8, x + 8, y + 8), fill="#5222d0"); d.text((x + 10, y - 8), f"{s['name']} {s['d']}m", fill="#5222d0")
    for x, y in A["entries"]:
        p = T([(x, y)])[0]; d.polygon([(p[0] - 12, p[1] - 14), (p[0] + 12, p[1] - 14), (p[0], p[1] + 6)], fill="#980000")
    im.save(os.path.join(WORK, "plan.png")); print("check:", os.path.join(WORK, "plan.png"))
    if not (renders and A.get("affine")): return
    Image.MAX_IMAGE_PIXELS = None
    M = np.array(A["affine"])
    P = lambda pts: [tuple((np.array([x, -y, 1.0]) @ M) / 8) for x, y in pts]
    for name in ("01", "08", "09"):
        r = Image.open(os.path.join(renders, f"acko2A_model{name}.png")).convert("RGB").reduce(8); d = ImageDraw.Draw(r)
        d.line(P(A["slab"] + A["slab"][:1]), fill=(0, 200, 0), width=2)
        for key, col in (("employee", (0, 160, 0)), ("client", (255, 140, 0))):
            for run in A["routes"][key]: d.line(P([(x, y) for x, y, _ in run]), fill=col, width=2)
        for s in A["stops"]:
            u, v = P([(s["x"], s["y"])])[0]; d.ellipse((u - 5, v - 5, u + 5, v + 5), fill=(82, 34, 208))
        r.save(os.path.join(WORK, f"over{name}.png"))


if __name__ == "__main__":
    main()
