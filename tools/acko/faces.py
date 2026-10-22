"""Rooms as the drawing encloses them: the faces of the partition linework in the DXF plan toolkit's full.svg.

Used by plan_dxf.py to give each room label the room it sits in. The lines that bound a room:
  walls, glass, the shell, planters (shade); doors without their swing arcs (folding and sliding doors and frames close a room
  as walls do), each swing replaced by its doorway shut along the door's closed position (from the arc's hinge to its two ends:
  the leaf, without its arc, dangles inside the room and splits nothing), so a door's swing belongs to its room, not to a
  sector of its own as when the arc was a wall; furniture lines over 2.5 m that are open or thin (the facade's
  rails), never tables or desks; and, when given, the floor plate's outline as the outside wall (the facade's mullion units are
  short furniture pieces, so rooms along it would otherwise leak out of the building).
Breaks where a wall stops short of a glass frame or a door are bridged by thickening every line by GAP, taking the enclosed
holes and growing them back by GAP (square corners kept). A small GAP keeps narrow rooms (phone booths); larger ones close
rooms whose walls stop further short, the largest (0.5 m) doorways drawn without a door: levels(lines) builds all four, and
room_at() tries them in turn.
"""
import math, re
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

TOK = re.compile(r"[MLCQ]|-?\d+(?:\.\d+)?(?:e-?\d+)?")
PARTITION = {"s wall", "f wall", "m wall", "s glass", "s base", "f base", "s shade", "f shade"}
LONG_FURN = 2500
GAPS = (45, 120, 160, 500)


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


def _thin(p):
    g = Polygon(p).buffer(0)
    return g.is_empty or 2 * g.area / max(g.length, 1) <= 200


def partition_lines(svg, plate=None):
    """the lines that bound rooms, from full.svg's classed paths (and the floor plate's outline, when given)"""
    lines, closers = [], []
    for cls, d in re.findall(r'<path class="([^"]+)" d="([^"]*)"', svg):
        if cls not in PARTITION and cls not in ("s door", "s furn"): continue
        for p in subpaths(d):
            if len(p) < 2: continue
            if cls in PARTITION:
                lines.append(LineString(p))
            elif cls == "s door":
                c = door_closers(p)
                if c: closers.extend(c)                # a swing: the door shut instead (its leaf then dangles, splitting nothing)
                else: lines.append(LineString(p))     # folding and sliding doors, frames: they close a room as walls do
            elif LineString(p).length > LONG_FURN and (math.dist(p[0], p[-1]) > 20 or len(p) < 4 or _thin(p)):
                lines.append(LineString(p))          # a facade rail, not a table
    if plate is not None:
        for g in (plate.geoms if hasattr(plate, "geoms") else [plate]):
            lines.append(LineString(g.exterior.coords))
    return lines + closers, len(closers) // 2


def floor_plate(zones, rooms, extra=()):
    """the floor the client occupies: the neighbourhood zones, the rooms and any extra faces, closed by 1.5 m, its largest
    part, out by 150 mm to the facade line"""
    occ = [g for g in list(zones) + list(rooms) + list(extra) if g is not None and not g.is_empty]
    U = unary_union([g.buffer(1500) for g in occ]).buffer(-1500)
    big = max((U.geoms if hasattr(U, "geoms") else [U]), key=lambda g: g.area)
    return Polygon(big.exterior).buffer(150, join_style=2)


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
    """the room round pt: the smallest room-sized face containing it, at the first gap level that has one -> (polygon, gap),
    or (None, None)"""
    p = Point(pt)
    for gap, fs, tr in lv:
        cand = [fs[i] for i in tr.query(p) if fs[i].contains(p) and lo <= fs[i].area <= hi and not is_strip(fs[i])]
        if cand:
            return fill_holes(min(cand, key=lambda f: f.area), 6e6), gap
    return None, None
