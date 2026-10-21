"""Rooms as the drawing encloses them: the faces of the partition linework in the DXF plan toolkit's full.svg.

Used by plan_dxf.py to give each room label the room it sits in. The linework:
  walls, glass, doors, the shell, planters (shade), and furniture lines longer than 2.5 m (the facade's rails and long
  counters, which the toolkit classes as furniture; tables too, whose own small faces room_at's minimum size skips); each doorway shut along its door's closed position (from the swing
  arc's hinge to its two ends)
Breaks where a wall stops short of a glass frame or a door are bridged by thickening every line by GAP, taking the enclosed
holes and growing them back by GAP (square corners kept). A small GAP keeps narrow rooms (phone booths); larger ones close
rooms whose walls stop further short: levels(lines) builds all three, and room_at() tries them in turn.
"""
import math, re
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

TOK = re.compile(r"[MLCQ]|-?\d+(?:\.\d+)?(?:e-?\d+)?")
PARTITION = {"s wall", "f wall", "m wall", "s glass", "s door", "f door", "s base", "f base", "s shade", "f shade"}
LONG_FURN = 2500
GAPS = (45, 120, 160)


def subpaths(d, tol=60.0):
    """an SVG path (M, L, C, Q) as point lists, curves flattened to about tol mm"""
    out, pts, cmd, t, i = [], None, None, TOK.findall(d), 0
    while i < len(t):
        k = t[i]
        if k in ("M", "L", "C", "Q"):
            cmd = k; i += 1; continue
        if cmd == "M":
            if pts and len(pts) > 1: out.append(pts)
            pts = [(float(t[i]), float(t[i + 1]))]; i += 2; cmd = "L"
        elif cmd == "L":
            pts.append((float(t[i]), float(t[i + 1]))); i += 2
        elif cmd in ("C", "Q"):
            n6 = 6 if cmd == "C" else 4
            v = list(map(float, t[i:i + n6])); i += n6
            x0, y0 = pts[-1]
            ctrl = [(v[0], v[1]), (v[2], v[3])] + ([(v[4], v[5])] if cmd == "C" else [])
            L = sum(math.dist(a, b) for a, b in zip([(x0, y0)] + ctrl[:-1], ctrl))
            n = max(2, min(24, int(L / tol) + 1))
            for j in range(1, n + 1):
                u = j / n; a = 1 - u
                if cmd == "C":
                    (x1, y1), (x2, y2), (x, y) = ctrl
                    pts.append((a ** 3 * x0 + 3 * a * a * u * x1 + 3 * a * u * u * x2 + u ** 3 * x, a ** 3 * y0 + 3 * a * a * u * y1 + 3 * a * u * u * y2 + u ** 3 * y))
                else:
                    (x1, y1), (x, y) = ctrl
                    pts.append((a * a * x0 + 2 * a * u * x1 + u * u * x, a * a * y0 + 2 * a * u * y1 + u * u * y))
        else:
            i += 1
    if pts and len(pts) > 1: out.append(pts)
    return out


def door_closers(pts):
    """a door's swing arc shuts its doorway: the lines from the arc's centre (the hinge) to both its ends"""
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


def partition_lines(svg):
    """the lines that bound rooms, from full.svg's classed paths"""
    lines, closers = [], []
    for cls, d in re.findall(r'<path class="([^"]+)" d="([^"]*)"', svg):
        if cls not in PARTITION and cls != "s furn": continue
        for p in subpaths(d):
            if len(p) < 2: continue
            l = LineString(p)
            if cls in PARTITION or l.length > LONG_FURN: lines.append(l)   # tables too: a room's face still holds them (room_at's lo skips their own)
            if cls == "s door": closers.extend(door_closers(p))
    return lines + closers, len(closers) // 2


def levels(lines, gaps=GAPS):
    """[(gap, faces, tree)] for each bridging gap"""
    out = []
    for gap in gaps:
        U = unary_union([l.buffer(gap, 4) for l in lines])
        holes = [Polygon(h) for q in (U.geoms if hasattr(U, "geoms") else [U]) for h in q.interiors]
        fs = [h.buffer(gap, join_style=2) for h in holes if h.area > 2e3]
        out.append((gap, fs, STRtree(fs)))
    return out


def fill_holes(g, max_area):
    parts = g.geoms if isinstance(g, MultiPolygon) else [g]
    return unary_union([Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > max_area]) for p in parts])


def is_strip(f):
    """a wall's own interior (between its two lines): thin"""
    return 2 * f.area / max(f.length, 1) < 260


def room_at(pt, lv, lo=0.8e6, hi=200e6):
    """the room round pt, at the first gap level that has one: (polygon, gap) or (None, None). The smallest room-sized face
    containing pt; or, when pt sits on a piece of furniture whose outline joins the walls (a desk against the wall, a table
    touching a partition: a face of its own), the room-sized face that touches that piece along most of its edge, with the
    piece included"""
    p = Point(pt)
    for gap, fs, tr in lv:
        under = [fs[i] for i in tr.query(p) if fs[i].contains(p)]
        cand = [f for f in under if lo <= f.area <= hi and not is_strip(f)]
        if cand:
            return fill_holes(min(cand, key=lambda f: f.area), 6e6), gap
        small = [f for f in under if f.area < lo]
        if small:
            piece = min(small, key=lambda f: f.area)
            ring = piece.buffer(gap + 40)
            near = [fs[i] for i in tr.query(ring) if fs[i] is not piece and lo <= fs[i].area <= hi and not is_strip(fs[i])]
            near = [(ring.intersection(f).area, f) for f in near]
            near = [(a, f) for a, f in near if a > 0]
            if near:
                a, f = max(near, key=lambda t: t[0])
                return fill_holes(unary_union([f, piece.buffer(gap + 40).intersection(f.buffer(gap + 40)), piece]).buffer(0), 6e6), gap
    return None, None
