"""Each space onto the drawing's own walls: the room outlines the hover and the Spaces colours use.

Usage:  python tools/acko/snap_spaces.py "<toolkit>/viewer/out/op2a"

The deck's spaces (data/plan-dxf.js) are traced from the PPT's slide-53 legend colours: pixel traces, stair-stepped, about
0.3 m off the DXF. Mitigata's hover used the CAD team's own room outlines; ACKO's DXF has none, so this takes them from the
drawing itself (the DXF plan toolkit's full.svg, never the DXF): the partition linework (walls, glass, doors with their swing
arcs, the shell, the planters, and the façade's long rails, which the toolkit classes as furniture) gives the faces it
encloses (breaks of a few centimetres bridged; each doorway shut along its door's closed position, from the swing arc's
hinge to its ends), and each space becomes the union of the faces lying mostly inside its
trace. Its edge then runs along the walls' inner faces, as a CAD room outline would. The traces have notches wherever the
slide's furniture sat on the colour, so a room's face counts when it lies mostly inside the trace or holds a good share of
it without being much bigger.
  snapped    the faces cover 75%+ of the trace (50%+ for a booth-sized room, whose trace spills out of its door) and are at
             most 4x its area (2.5x past 60 m2); small holes (a table in the shell) filled
  clipped    else (a doorway left open, the room's face running on): the trace with its notches closed (0.8 m), clipped to
             the floor (the enclosed faces: the walls excluded), so it stops at the walls it has
  kept       else: the trace as it was
Rewrites data/plan-dxf.js in place (idempotent: run again, nothing changes); m2 from the new shape; names, types, label
points kept. Report: counts per type, the outline-to-wall distance before and after, a check picture tools/_work/snap/check.png.
"""
import json, math, os, re, statistics, sys, time
from collections import Counter, defaultdict

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOK = re.compile(r"[MLC]|-?\d+(?:\.\d+)?(?:e-?\d+)?")
PARTITION = {"s wall", "f wall", "m wall", "s glass", "s door", "f door", "s base", "f base", "s shade", "f shade"}
LONG_FURN = 2500      # furniture lines longer than this (mm) are the façade's rails and long counters: they close rooms too


def subpaths(d, tol=60.0):
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
                pts.append((a ** 3 * x0 + 3 * a * a * u * x1 + 3 * a * u * u * x2 + u ** 3 * x, a ** 3 * y0 + 3 * a * a * u * y1 + 3 * a * u * u * y2 + u ** 3 * y))
        else:
            i += 1
    if pts and len(pts) > 1: out.append(pts)
    return out


def door_closers(pts):
    """a door's swing arc closes its doorway: the lines from the arc's centre (the hinge) to both its ends are the leaf at
    either end of its swing, so the doorway is shut as if the door were closed. None if the points aren't an arc."""
    if len(pts) < 6: return []
    (ax, ay), (bx, by), (cx, cy) = pts[0], pts[len(pts) // 2], pts[-1]
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-6: return []
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    if not 450 <= r <= 1400: return []
    if any(abs(math.hypot(x - ux, y - uy) - r) > 0.06 * r for x, y in pts): return []
    return [LineString([(ux, uy), pts[0]]), LineString([(ux, uy), pts[-1]])]


def rings_of_d(d):
    out = []
    for part in re.findall(r"M([^M]+)", d):
        nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", part)))
        pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
        if len(pts) > 2: out.append(pts)
    return out


def poly_of(d):
    """a space's path (rings, even-odd) as one polygon"""
    g = None
    for r in rings_of_d(d):
        p = Polygon(r).buffer(0)
        if p.is_empty: continue
        g = p if g is None else g.symmetric_difference(p)
    return g


def d_of(g):
    parts = g.geoms if isinstance(g, MultiPolygon) else [g]
    out = []
    for p in parts:
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            out.append("M" + "L".join(f"{round(x)} {round(y)}" for x, y in c) + "Z")
    return "".join(out)


def cap(f):
    """how much bigger than its trace a room's face may be: the traces of small rooms are notched to a third of the room by the
    slide's furniture; a big open area keeps a tighter cap, so a trace in it never takes the whole open floor"""
    return 4.0 if f.area <= 60e6 else 2.5


def fill_holes(g, max_area):
    parts = g.geoms if isinstance(g, MultiPolygon) else [g]
    out = [Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > max_area]) for p in parts]
    return unary_union(out)


def main(out_dir):
    t0 = time.time()
    svg = open(os.path.join(out_dir, "full.svg"), encoding="utf-8").read()
    lines, closers = [], []
    for cls, d in re.findall(r'<path class="([^"]+)" d="([^"]*)"', svg):
        if cls in PARTITION or cls == "s furn":
            for p in subpaths(d):
                if len(p) < 2: continue
                l = LineString(p)
                if cls in PARTITION or l.length > LONG_FURN: lines.append(l)
                if cls == "s door": closers.extend(door_closers(p))
    print(f"partition lines: {len(lines)}, doorways closed: {len(closers) // 2}")
    lines += closers
    # the faces: the regions the linework encloses, bridging the breaks where a wall stops short of a glass frame or a door:
    # every line thickened by GAP, the enclosed holes taken, and grown back by GAP (square corners kept). A small GAP keeps
    # the narrow rooms (phone booths); a larger one closes rooms whose walls stop further short. Each space tries them in turn.
    LEVELS = []
    for GAP in (45, 120, 160):
        U = unary_union([l.buffer(GAP, 4) for l in lines])
        holes = [Polygon(h) for q in (U.geoms if hasattr(U, "geoms") else [U]) for h in q.interiors]
        fs = [h.buffer(GAP, join_style=2) for h in holes if h.area > 2e3]
        LEVELS.append((GAP, fs, STRtree(fs)))
        print(f"faces at {GAP} mm: {len(fs)} ({time.time() - t0:.0f}s)")
    faces = LEVELS[0][1]
    ltree = STRtree(lines)
    floor = unary_union(faces).buffer(0)          # the walls are the thickened lines, so the faces are already the floor

    path = os.path.join(ROOT, "data", "plan-dxf.js")
    js = open(path, encoding="utf-8").read()
    head = js[:js.index("window.PLAN_DXF")]
    P = json.loads(js[js.index("{"):js.rindex("}") + 1])

    def wall_dist(g):
        """the median and p90 distance (mm) from an outline's vertices to the nearest partition line"""
        ds = []
        for p in (g.geoms if isinstance(g, MultiPolygon) else [g]):
            for x, y in list(p.exterior.coords)[::2]:
                pt = Point(x, y); near = ltree.query(pt.buffer(1500))
                ds.append(min((lines[i].distance(pt) for i in near), default=1500))
        return ds

    stats, before, after = Counter(), [], []
    per_type = defaultdict(Counter)
    for sp in P["spaces"]:
        g = poly_of(sp["d"])
        if g is None or g.is_empty:
            stats["kept"] += 1; per_type[sp["type"]]["kept"] += 1; continue
        before += wall_dist(g)
        res, how = None, "kept"
        for GAP, fs, tr in LEVELS:
            sel = []
            for f in (fs[i] for i in tr.query(g)):
                a = f.intersection(g).area
                if a >= 0.5 * f.area or (a >= 0.3 * g.area and f.area <= cap(f) * g.area): sel.append(f)
            if not sel: continue
            u = fill_holes(unary_union(sel).buffer(0), 6e6)
            cover = u.intersection(g).area / g.area
            if u.area <= cap(u) * g.area and (cover >= 0.75 or (u.area <= 6e6 and cover >= 0.5)):
                res, how = u, "snapped"; break
        if res is None:
            c = fill_holes(g.buffer(800, join_style=2).buffer(-800, join_style=2), 6e6).intersection(floor).buffer(0)
            if not c.is_empty and c.area >= 0.6 * g.area:
                res, how = c, "clipped"
        if res is None: res = g
        res = res.simplify(10)
        if isinstance(res, MultiPolygon):     # a sliver beside the room: keep the room
            big = max(res.geoms, key=lambda q: q.area)
            res = big if big.area > 0.9 * res.area else res
        stats[how] += 1; per_type[sp["type"]][how] += 1
        after += wall_dist(res)
        sp["d"] = d_of(res)
        sp["m2"] = round(res.area / 1e6, 1)
    q = lambda a, f: (statistics.median(a) if f == 0.5 else sorted(a)[int(len(a) * f)]) if a else 0
    print(f"spaces: {dict(stats)}")
    for t, c in sorted(per_type.items()): print(f"  {t:24s} {dict(c)}")
    print(f"outline to the nearest wall line: median {q(before, .5):.0f} -> {q(after, .5):.0f} mm, p90 {q(before, .9):.0f} -> {q(after, .9):.0f} mm")
    P["spaces_snapped"] = time.strftime("%Y-%m-%d %H:%M")
    open(path, "w", encoding="utf-8").write(head + "window.PLAN_DXF = " + json.dumps(P, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"wrote {path} in {time.time() - t0:.0f}s")
    check(P, lines, js)


def check(P, lines, old_js):
    """the old traces (red) and the new outlines (green) over the drawing: the whole floor and two crops"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    O = json.loads(old_js[old_js.index("{"):old_js.rindex("}") + 1])
    old = {s["id"]: s["d"] for s in O["spaces"]}
    os.makedirs(os.path.join(ROOT, "tools", "_work", "snap"), exist_ok=True)
    for name, box in [("check", None), ("check_06", (14000, 14500, 60000, 45000)), ("check_core", (100000, 14500, 140000, 40000))]:
        vx, vy, vw, vh = P["viewBox"]
        x0, y0, x1, y1 = box or (vx, vy, vx + vw, vy + vh)
        fig = plt.figure(figsize=((x1 - x0) / (2500 if box else 7000), (y1 - y0) / (2500 if box else 7000)), dpi=110)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal"); ax.axis("off")
        for l in lines:
            b = l.bounds
            if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1: continue
            ax.plot(*l.xy, color="#999", lw=.35)
        for s in P["spaces"]:
            for r in rings_of_d(old.get(s["id"], "")): ax.fill(*zip(*r), fc="none", ec="#d22", lw=.7)
            for r in rings_of_d(s["d"]): ax.fill(*zip(*r), fc="#2a2", alpha=.18, ec="#1a1", lw=.9)
        fig.savefig(os.path.join(ROOT, "tools", "_work", "snap", name + ".png")); plt.close(fig)
    print("check pictures: tools/_work/snap/check*.png")


if __name__ == "__main__":
    main(sys.argv[1])
