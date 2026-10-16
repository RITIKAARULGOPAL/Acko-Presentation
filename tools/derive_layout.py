"""Everything the presentation places on the plan, derived from the 09.10 CAD (no hand-placed coordinates).

Called by import_plan_hover.py for each option, in the presentation's frame (mm, y up, north = +x):
  circulation  centreline of the floor left between zones and desks (raster skeleton → polylines)
  routes       visitor (front door → boardroom), tour (Opt 02: front door → SOC glass), service (prep / dine store → boardroom)
               shortest paths over the free floor, preferring the corridors
  events       50 = the café · 100 = the largest team zone on the SOC · 200 = the team zones on the SOC until ≥ 200 m²
  stage        where each event faces: the café's dropdown screen, or the SOC glass
  socGlass     the SOC's interior edge (not on the façade), longest run
  signature    arrival · watchwall · commons · on air · lantern
  cameras      render viewpoints at their CAD rooms (directions kept from the renders)
  walls        operable wall between the café and a team zone, where they meet
  lobby        the front door (where people arrive in the 3D twin)
"""
import heapq, math, re
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import nearest_points, unary_union

RES = 200.0                                  # raster cell, mm

ENCLOSED = {"meet", "quiet", "board", "studio", "secure", "service", "core", "soc"}
CAM_DIRS = {"reception": [0, -1], "breakout": [0.866, 0.5], "meeting6": [-1, 0], "boardroom": [-1, 0], "soc": [-0.618, 0.786]}
HOW = {
    "opt1": {"50": "Tables fold and nest; the dropdown screen and the pantry counter become stage and bar.",
             "100": "Mobile benches roll back to the SOC glass; the SOC wall becomes the backdrop.",
             "200": "Furniture moves out to the storage spine; the full hall faces the SOC as a live stage."},
    "opt2": {"50": "By day a café, at four a training room: tables stack, the dropdown screen lowers.",
             "100": "Desks are mobile; the hall turns to face the SOC display wall.",
             "200": "The central hall opens end to end; the SOC display wall is the stage."},
}


def P(poly):
    g = Polygon(poly)
    return g if g.is_valid else g.buffer(0)


def biggest(g):
    if isinstance(g, MultiPolygon):
        return max(g.geoms, key=lambda q: q.area)
    return g


def coords(line):
    return [[round(x), round(y)] for x, y in line.coords]


def zhang_suen(img):
    """Thin a boolean raster to a one-pixel skeleton."""
    img = img.copy().astype(np.uint8)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = np.pad(img, 1)
            P2, P3, P4, P5 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:]
            P6, P7, P8, P9 = p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]
            nb = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(n.astype(int) for n in nb)
            A = sum(((nb[i] == 0) & (nb[(i + 1) % 8] == 1)).astype(int) for i in range(8))
            if step == 0:
                c = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                c = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            m = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                img[m] = 0
                changed = True
    return img.astype(bool)


class Grid:
    def __init__(self, outline):
        self.plate = P(outline)
        x0, y0, x1, y1 = self.plate.bounds
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
        xs = x0 + (np.arange(self.nx) + 0.5) * RES
        ys = y0 + (np.arange(self.ny) + 0.5) * RES
        self.X, self.Y = np.meshgrid(xs, ys)          # [row = y, col = x]

    def rasterize(self, geoms):
        out = np.zeros(self.X.shape, bool)
        pts = np.c_[self.X.ravel(), self.Y.ravel()]
        for g in geoms:
            if g.is_empty:
                continue
            for q in (g.geoms if isinstance(g, MultiPolygon) else [g]):
                bx0, by0, bx1, by1 = q.bounds
                sel = (pts[:, 0] >= bx0) & (pts[:, 0] <= bx1) & (pts[:, 1] >= by0) & (pts[:, 1] <= by1)
                idx = np.nonzero(sel)[0]
                if not len(idx):
                    continue
                inside = _contains(q, pts[idx])
                out.ravel()[idx[inside]] = True
        return out

    def cell(self, x, y):
        return int(np.clip((y - self.y0) / RES, 0, self.ny - 1)), int(np.clip((x - self.x0) / RES, 0, self.nx - 1))

    def xy(self, r, c):
        return [self.x0 + (c + 0.5) * RES, self.y0 + (r + 0.5) * RES]


def _contains(poly, pts):
    """Vectorised point-in-polygon (exterior minus holes)."""
    def ring_in(ring, P_):
        xy = np.asarray(ring.coords)
        x, y = P_[:, 0], P_[:, 1]
        inside = np.zeros(len(P_), bool)
        j = len(xy) - 1
        for i in range(len(xy)):
            xi, yi = xy[i]; xj, yj = xy[j]
            cross = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi)
            inside ^= cross
            j = i
        return inside
    res = ring_in(poly.exterior, pts)
    for h in poly.interiors:
        res &= ~ring_in(h, pts)
    return res


def trace(skel, grid, min_len=1500):
    """Skeleton pixels → polylines (walk between junctions and ends)."""
    pts = set(zip(*np.nonzero(skel)))
    nbrs = lambda p: [(p[0] + dr, p[1] + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and (p[0] + dr, p[1] + dc) in pts]
    deg = {p: len(nbrs(p)) for p in pts}
    seen_edges, lines = set(), []
    starts = [p for p in pts if deg[p] != 2] or list(pts)[:1]
    for s in starts:
        for n in nbrs(s):
            if (s, n) in seen_edges:
                continue
            path = [s, n]; seen_edges.add((s, n)); seen_edges.add((n, s))
            prev, cur = s, n
            while deg.get(cur) == 2:
                nxt = [q for q in nbrs(cur) if q != prev]
                if not nxt or (cur, nxt[0]) in seen_edges:
                    break
                seen_edges.add((cur, nxt[0])); seen_edges.add((nxt[0], cur))
                prev, cur = cur, nxt[0]; path.append(cur)
            ln = LineString([grid.xy(r, c) for r, c in path])
            dead_end = deg[path[0]] == 1 or deg.get(path[-1], 0) == 1
            if ln.length >= (min_len if dead_end else 400):
                lines.append(ln.simplify(180))
    return lines


def derive(key, zones, rooms, texts, outline, glazed, desks):
    """zones: presentation zones · rooms: [(name, [polys])] in frame · texts: drawing labels · glazed: [(P, Q)] façade edges."""
    grid = Grid(outline)
    plate = grid.plate
    byname = lambda rx: [z for z in zones if re.search(rx, z.get("name") or "", re.I)]
    room_geoms = [(n, unary_union([P(p) for p in ps if len(p) > 2])) for n, ps in rooms]
    soc = biggest(unary_union([P(z["poly"]) for z in zones if z["type"] == "soc"]))
    teams = [z for z in zones if z["type"] in ("focus", "soc") and z.get("pax") is not None and z["type"] != "soc"]
    one = lambda rx: next((biggest(g) for n, g in sorted(room_geoms, key=lambda t: -t[1].area) if re.search(rx, n, re.I)), None)
    entrance, reception, boardroom = one(r"main / entrance"), one(r"reception"), one(r"board")
    cafe, podcast, prep = one(r"^cafe|cafeteria"), one(r"podcast"), one(r"preparation|dine store")
    lifts = one(r"lift lobby")

    # ---- circulation: centreline of the floor left between the zones and desks ----
    corr = unary_union([g for n, g in room_geoms if re.search(r"corridor", n, re.I)])
    # unnamed rooms are enclosed too, even the ones that are not zones (Opt 01's south-west nook)
    taken = grid.rasterize([P(z["poly"]) for z in zones] + [g for n, g in room_geoms if not n] + [P(d) for d in desks if len(d) > 2])
    left = grid.rasterize([plate.buffer(-600)]) & ~taken
    # (the CAD "Corridor" outlines also cover the workhall aisles, so they are not used here)
    corr_m = ndimage.binary_opening(left, iterations=2)
    corr_m = ndimage.binary_closing(corr_m, iterations=1) & grid.rasterize([plate])
    skel = zhang_suen(corr_m)
    # drop the skeleton's small loops and stubs: keep the largest connected network
    lab, n = ndimage.label(skel, structure=np.ones((3, 3)))
    if n > 1:
        sizes = ndimage.sum(skel, lab, range(1, n + 1))
        skel = np.isin(lab, [i + 1 for i, sz in enumerate(sizes) if sz >= 0.08 * sizes.max()])
    lines = trace(skel, grid, min_len=2600)
    # drop isolated bits: groups of touching lines shorter than 4 m in all
    groups = []
    for ln in lines:
        hit = [g for g in groups if any(ln.distance(o) < 450 for o in g)]
        merged = [ln] + [o for g in hit for o in g]
        groups = [g for g in groups if g not in hit] + [merged]
    circulation = [coords(l) for g in groups if sum(o.length for o in g) >= 4000 for l in g]

    # ---- free floor for routes: the plate minus enclosed rooms and desks; corridors are cheapest ----
    obstacles = [P(z["poly"]) for z in zones if z["type"] in ENCLOSED] + [P(d) for d in desks if len(d) > 2]
    free = grid.rasterize([plate]) & ~grid.rasterize(obstacles)
    team_m = grid.rasterize([P(t["poly"]) for t in teams] + [P(z["poly"]) for z in zones if z.get("agile")])
    cost = np.where(corr_m, 1.0, np.where(team_m, 8.0, 3.0))

    def route(src_geom, dst_geom, dst_point=None):
        if src_geom is None or dst_geom is None:
            return None
        allow = free | grid.rasterize([src_geom.buffer(300), dst_geom.buffer(300)])
        idx = -np.ones(allow.shape, int); ids = np.argwhere(allow); idx[tuple(ids.T)] = np.arange(len(ids))
        rows, cols, w = [], [], []
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            a = ids; b = ids + [dr, dc]
            ok = (b[:, 0] >= 0) & (b[:, 0] < allow.shape[0]) & (b[:, 1] >= 0) & (b[:, 1] < allow.shape[1])
            a, b = a[ok], b[ok]; ok = allow[b[:, 0], b[:, 1]]; a, b = a[ok], b[ok]
            step = math.hypot(dr, dc) * RES
            ww = step * 0.5 * (cost[a[:, 0], a[:, 1]] + cost[b[:, 0], b[:, 1]])
            rows += list(idx[a[:, 0], a[:, 1]]); cols += list(idx[b[:, 0], b[:, 1]]); w += list(ww)
        G = coo_matrix((w + w, (rows + cols, cols + rows)), shape=(len(ids), len(ids))).tocsr()
        sp = src_geom.representative_point() if not src_geom.contains(src_geom.centroid) else src_geom.centroid
        tp = Point(dst_point) if dst_point else (dst_geom.centroid if dst_geom.contains(dst_geom.centroid) else dst_geom.representative_point())
        def near(pt):
            d = np.hypot(grid.X[tuple(ids.T)] - pt.x, grid.Y[tuple(ids.T)] - pt.y); return int(np.argmin(d))
        s, t = near(sp), near(tp)
        dist, pred = dijkstra(G, indices=s, return_predecessors=True)
        if not np.isfinite(dist[t]):
            return None
        path, cur = [], t
        while cur != s and cur >= 0:
            path.append(cur); cur = pred[cur]
        path.append(s)
        line = LineString([grid.xy(*ids[i]) for i in reversed(path)]).simplify(300)
        return dict(pts=coords(line), m=round(line.length / 1000, 1))

    # ---- SOC glass: interior edges of the SOC, longest contiguous run ----
    ext = list(soc.exterior.coords)[:-1]
    edge_in = [plate.exterior.distance(LineString([ext[i], ext[(i + 1) % len(ext)]]).interpolate(0.5, normalized=True)) > 1200 for i in range(len(ext))]
    runs, cur = [], []
    for i in range(len(ext) * 2):                 # wrap around so a run can cross the start
        j = i % len(ext)
        if edge_in[j]:
            cur.append(j)
        else:
            if cur: runs.append(cur); cur = []
    if cur: runs.append(cur)
    runs = [r[: len(ext)] for r in runs]
    best = max(runs, key=lambda r: sum(LineString([ext[k], ext[(k + 1) % len(ext)]]).length for k in r)) if runs else []
    soc_glass = LineString([ext[k] for k in best] + [ext[(best[-1] + 1) % len(ext)]]) if best else LineString(ext[:2])
    glass_mid = soc_glass.interpolate(0.5, normalized=True)

    # ---- events: café · largest team on the SOC · teams on the SOC until ≥ 200 m² ----
    on_soc = sorted([t for t in teams if P(t["poly"]).distance(soc) <= 2000], key=lambda t: -t["area"])
    others = sorted([t for t in teams if t not in on_soc], key=lambda t: P(t["poly"]).distance(soc))
    ev = {}
    if cafe is not None:
        dd = next((t for t in texts if re.search(r"DROPDOWN", t["t"], re.I)), None)
        st = [dd["x"], dd["y"]] if dd and cafe.buffer(1500).contains(Point(dd["x"], dd["y"])) else list(cafe.centroid.coords[0])
        ev["50"] = dict(polys=[coords(cafe.exterior)], where="Café", how=HOW.get(key, {}).get("50", ""), stage=[round(v) for v in st])
    pick = on_soc[:1] if on_soc else others[:1]
    sel, acc = list(pick), sum(t["area"] for t in pick)
    while acc < 200:
        hall = unary_union([P(t["poly"]) for t in sel])
        nxt = [t for t in teams if t not in sel and P(t["poly"]).distance(hall) <= 3000]
        if not nxt:
            break
        t = max(nxt, key=lambda t: (P(t["poly"]).distance(soc) <= 2000, t["area"]))
        sel.append(t); acc += t["area"]
    for lvl, ts in (("100", pick), ("200", sel)):
        if not ts: continue
        g = unary_union([P(t["poly"]) for t in ts])
        near_pt = nearest_points(g, glass_mid)[0]
        c = g.centroid
        v = np.array([c.x - near_pt.x, c.y - near_pt.y]); v = v / (np.linalg.norm(v) or 1)
        st = [near_pt.x + v[0] * 1500, near_pt.y + v[1] * 1500]
        polys = [coords(q.exterior) for q in (g.geoms if isinstance(g, MultiPolygon) else [g])]
        ev[lvl] = dict(polys=polys, where=" + ".join(t["name"] for t in ts) + " workhall", how=HOW.get(key, {}).get(lvl, ""), stage=[round(v) for v in st])
    for k, e in ev.items():
        areas = [P(p).area for p in e["polys"]]
        e["poly"] = e["polys"][int(np.argmax(areas))]
        e["area"] = round(sum(areas) / 1e6)

    # ---- routes ----
    routes = {}
    r = route(entrance or reception, boardroom)
    if r: routes["visitor"] = r
    if key == "opt2":
        r = route(entrance or reception, glass_mid.buffer(400), dst_point=list(glass_mid.coords[0]))
        if r: routes["tour"] = r
    r = route(prep, boardroom)
    if r: routes["service"] = r

    # ---- signature spots, cameras, operable wall, lobby ----
    c = lambda g: [round(v) for v in g.centroid.coords[0]] if g is not None else None
    soc_c = soc.centroid
    gm = np.array(glass_mid.coords[0]); away = gm - np.array(soc_c.coords[0]); away = away / (np.linalg.norm(away) or 1)
    glz = unary_union([LineString([a, b]) for a, b in glazed])
    fp = nearest_points(soc.exterior, glz)[0]
    to_c = np.array(soc_c.coords[0]) - np.array(fp.coords[0]); to_c = to_c / (np.linalg.norm(to_c) or 1)
    signature = {
        "arrival": c(reception), "watchwall": [round(v) for v in gm + away * 1500], "commons": c(cafe),
        "onair": c(podcast), "lantern": [round(v) for v in np.array(fp.coords[0]) + to_c * 2500],
    }
    signature = {k: v for k, v in signature.items() if v}
    cams = {}
    if key == "opt1":
        six = one(r"meeting room . 6 pax")
        for name, g in (("reception", reception), ("breakout", one(r"breakout")), ("meeting6", six), ("boardroom", boardroom), ("soc", soc)):
            if g is not None:
                cams[name] = dict(at=c(g), dir=CAM_DIRS[name])
    walls = []
    if key == "opt2" and cafe is not None:
        tz = unary_union([P(t["poly"]) for t in teams])
        shared = cafe.exterior.intersection(tz.buffer(800))
        segs = [g for g in getattr(shared, "geoms", [shared]) if isinstance(g, LineString) and g.length > 2000]
        if segs:
            walls.append(coords(max(segs, key=lambda g: g.length)))
    lobby = c(entrance or reception)

    # ---- floor labels at their CAD rooms and façades ----
    labels = []
    if entrance is not None: labels.append(dict(t="Main entrance", at=c(entrance), kind="entry"))
    if lifts is not None: labels.append(dict(t="Lifts · fire stair · toilets", at=c(lifts), kind="core"))
    for g in sorted([g for n, g in room_geoms if re.search(r"ahu", n, re.I)], key=lambda g: g.centroid.x):
        labels.append(dict(t="AHU", at=c(g), kind="core"))
    return dict(events=ev, walls=walls, routes=routes, cameras=cams, signature=signature,
                socGlass=coords(soc_glass), lobby=lobby, circulation=circulation), labels
