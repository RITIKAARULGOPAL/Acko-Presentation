"""A small streaming DXF reader (ASCII DXF, any AutoCAD version): blocks and model space as plain geometry, no ezdxf.

  read(path)            -> (blocks, model)
                           blocks: {name: {"base": (x, y), "ents": [ent, ...]}}; model: [ent, ...]
  ent                   {"t": type, "l": layer, ...}:
                             LINE / LWPOLYLINE / POLYLINE / ARC / CIRCLE / ELLIPSE / SPLINE  -> "p": [[(x, y), ...], ...], "c": closed flags
                             HATCH   -> "p": the boundary loops (closed)
                             INSERT  -> "n": block, "m": the 2D affine (a, b, c, d, e, f) from block to parent coordinates
                             TEXT / MTEXT -> "x", "y", "s": the words
  walk(blocks, ents, fn)   every primitive with its world transform and effective layer (layer "0" inside a block takes the
                           insert's layer, as AutoCAD draws it): fn(ent, m, layer, path), path = the inserts it sits in.
Curves are flattened to about 6 degrees an arc step. Entities in a mirrored OCS (extrusion 0, 0, -1) are flipped in x.
"""
import math

ARC_STEP = math.radians(6)


def _arc(cx, cy, r, a0, a1):
    while a1 <= a0: a1 += 2 * math.pi
    n = max(2, int((a1 - a0) / ARC_STEP) + 1)
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _bulge(p, q, b):
    """the points of a bulged segment p -> q (excluding p, including q): the included angle is 4 atan(b), counter-clockwise if b > 0"""
    if abs(b) < 1e-9: return [q]
    d = math.dist(p, q)
    if d < 1e-9: return [q]
    th = 4 * math.atan(b); r = d / (2 * math.sin(th / 2)); h = r * math.cos(th / 2)
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    cx, cy = (p[0] + q[0]) / 2 - uy * h, (p[1] + q[1]) / 2 + ux * h
    a0, R = math.atan2(p[1] - cy, p[0] - cx), abs(r)
    n = max(2, int(abs(th) / ARC_STEP) + 1)
    return [(cx + R * math.cos(a0 + th * i / n), cy + R * math.sin(a0 + th * i / n)) for i in range(1, n)] + [q]


def _poly(verts, closed):
    """[(x, y, bulge)] -> points"""
    if not verts: return []
    out = [(verts[0][0], verts[0][1])]
    n = len(verts)
    for i in range(n if closed else n - 1):
        p, q = verts[i], verts[(i + 1) % n]
        out += _bulge((p[0], p[1]), (q[0], q[1]), p[2])
    return out


def _num(v, d=0.0):
    try: return float(v)
    except ValueError: return d


def _hatch(P):
    """a HATCH's boundary loops from its group codes (in order)"""
    loops, i, n = [], 0, len(P)
    while i < n and P[i][0] != "91": i += 1
    if i >= n: return loops
    count = int(P[i][1]); i += 1
    for _ in range(count):
        while i < n and P[i][0] != "92": i += 1
        if i >= n: break
        flag = int(P[i][1]); i += 1
        if flag & 2:                                    # a polyline path
            has_b = closed = 0; nv = 0
            while i < n and P[i][0] in ("72", "73"):
                if P[i][0] == "72": has_b = int(P[i][1])
                else: closed = int(P[i][1])
                i += 1
            if i < n and P[i][0] == "93": nv = int(P[i][1]); i += 1
            verts = []
            while len(verts) < nv and i < n:
                if P[i][0] == "10":
                    x = _num(P[i][1]); y = _num(P[i + 1][1]) if i + 1 < n and P[i + 1][0] == "20" else 0.0
                    i += 2; b = 0.0
                    if i < n and P[i][0] == "42": b = _num(P[i][1]); i += 1
                    verts.append((x, y, b))
                else:
                    i += 1
            pts = _poly(verts, True)
            if len(pts) > 2: loops.append(pts)
        else:                                           # edges: line, arc, ellipse, spline
            ne = 0
            if i < n and P[i][0] == "93": ne = int(P[i][1]); i += 1
            pts = []
            for _e in range(ne):
                while i < n and P[i][0] != "72": i += 1
                if i >= n: break
                et = int(P[i][1]); i += 1
                vals = {}
                order = []
                while i < n and P[i][0] not in ("72", "97", "92"):
                    c = P[i][0]
                    if et == 4 and c in ("10", "20"):
                        order.append((c, _num(P[i][1])))
                    else:
                        vals.setdefault(c, _num(P[i][1]))
                    i += 1
                    if et in (1, 2, 3) and c == ("21" if et in (1, 3) else "73"):
                        if et == 3 and "73" not in vals: continue
                        break
                if et == 1:
                    seg = [(vals.get("10", 0), vals.get("20", 0)), (vals.get("11", 0), vals.get("21", 0))]
                elif et == 2:
                    a0, a1 = math.radians(vals.get("50", 0)), math.radians(vals.get("51", 360))
                    seg = _arc(vals.get("10", 0), vals.get("20", 0), vals.get("40", 0), a0, a1)
                    if not vals.get("73", 1): seg = [(x, 2 * vals.get("20", 0) - y) for x, y in seg]   # clockwise: the angles mirrored
                elif et == 3:
                    cx, cy, mx, my, k = vals.get("10", 0), vals.get("20", 0), vals.get("11", 0), vals.get("21", 0), vals.get("40", 1)
                    a0, a1 = math.radians(vals.get("50", 0)), math.radians(vals.get("51", 360))
                    while a1 <= a0: a1 += 2 * math.pi
                    R = math.hypot(mx, my); ang = math.atan2(my, mx); nseg = max(4, int((a1 - a0) / ARC_STEP))
                    seg = []
                    for s in range(nseg + 1):
                        t = a0 + (a1 - a0) * s / nseg; x, y = R * math.cos(t), R * k * math.sin(t)
                        seg.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
                else:
                    xs = [v for c, v in order if c == "10"]; ys = [v for c, v in order if c == "20"]
                    seg = list(zip(xs, ys))
                if seg:
                    if pts and math.dist(pts[-1], seg[0]) > math.dist(pts[-1], seg[-1]) and len(seg) > 1 and et != 1:
                        seg = seg[::-1]
                    pts += seg
            if len(pts) > 2: loops.append(pts)
        # source boundary objects: skip their handles
        while i < n and P[i][0] in ("97", "330"): i += 1
    return loops


def _decode(t, P):
    e = {"t": t, "l": "0"}
    first = {}
    for c, v in P:
        if c not in first: first[c] = v
    e["l"] = first.get("8", "0")
    flip = _num(first.get("230", "1"), 1) < 0
    f = lambda pts: [(-x, y) for x, y in pts] if flip else pts
    if t == "LINE":
        e["p"] = [[(_num(first.get("10")), _num(first.get("20"))), (_num(first.get("11")), _num(first.get("21")))]]; e["c"] = [False]   # WCS
    elif t == "LWPOLYLINE":
        verts, closed = [], int(_num(first.get("70", "0"))) & 1
        for c, v in P:
            if c == "10": verts.append([_num(v), 0.0, 0.0])
            elif c == "20" and verts: verts[-1][1] = _num(v)
            elif c == "42" and verts: verts[-1][2] = _num(v)
        e["p"] = [f(_poly([tuple(q) for q in verts], closed))]; e["c"] = [bool(closed)]
    elif t == "ARC":
        e["p"] = [f(_arc(_num(first.get("10")), _num(first.get("20")), _num(first.get("40")), math.radians(_num(first.get("50"))), math.radians(_num(first.get("51")))))]
        e["c"] = [False]
    elif t == "CIRCLE":
        cx, cy, r = _num(first.get("10")), _num(first.get("20")), _num(first.get("40"))
        e["p"] = [f(_arc(cx, cy, r, 0, 2 * math.pi))]; e["c"] = [True]; e["circle"] = (cx * (-1 if flip else 1), cy, r)
    elif t == "ELLIPSE":
        cx, cy, mx, my, k = _num(first.get("10")), _num(first.get("20")), _num(first.get("11")), _num(first.get("21")), _num(first.get("40"), 1)
        a0, a1 = _num(first.get("41"), 0), _num(first.get("42"), 2 * math.pi)
        while a1 <= a0: a1 += 2 * math.pi
        R = math.hypot(mx, my); ang = math.atan2(my, mx); n = max(4, int((a1 - a0) / ARC_STEP))
        pts = []
        for s in range(n + 1):
            u = a0 + (a1 - a0) * s / n; x, y = R * math.cos(u), R * k * math.sin(u)
            pts.append((cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)))
        e["p"] = [pts]; e["c"] = [abs(a1 - a0 - 2 * math.pi) < 1e-3]          # ELLIPSE is WCS
    elif t == "SPLINE":
        cp = [[_num(v), 0.0] for c, v in P if c == "10"]
        ys = [_num(v) for c, v in P if c == "20"]
        for q, y in zip(cp, ys): q[1] = y
        fp = [[_num(v), 0.0] for c, v in P if c == "11"]
        fy = [_num(v) for c, v in P if c == "21"]
        for q, y in zip(fp, fy): q[1] = y
        pts = [tuple(q) for q in (fp if len(fp) >= 2 else cp)]
        e["p"] = [pts]; e["c"] = [bool(int(_num(first.get("70", "0"))) & 1)]
    elif t == "HATCH":
        e["p"] = [f(q) for q in _hatch(P)]; e["c"] = [True] * len(e["p"])
        e["solid"] = first.get("70") == "1"; e["pat"] = first.get("2", "")
    elif t == "INSERT":
        x, y = _num(first.get("10")), _num(first.get("20"))
        sx, sy = _num(first.get("41", "1"), 1), _num(first.get("42", "1"), 1)
        r = math.radians(_num(first.get("50", "0")))
        a, b, c, d = sx * math.cos(r), sx * math.sin(r), -sy * math.sin(r), sy * math.cos(r)
        if flip: a, b, c, d, x = -a, b, -c, d, -x
        e["n"] = first.get("2", ""); e["m"] = (a, b, c, d, x, y)
    elif t in ("TEXT", "MTEXT"):
        x, y = _num(first.get("10")), _num(first.get("20"))
        if flip and t == "TEXT": x = -x
        s = "".join(v for c, v in P if c in ("3", "1"))
        e["x"], e["y"], e["s"] = x, y, s
    else:
        return None
    return e


def read(path, keep=None):
    """blocks and model space; keep(type) -> bool filters entity types (default: all the geometric ones)"""
    blocks, model = {}, []
    sec = blk = None
    cur_t = None; P = []
    poly_t = None; poly_layer = "0"; poly_flags = 0; poly_flip = False; poly_verts = []

    def sink():
        return blocks[blk]["ents"] if blk is not None else (model if sec == "ENTITIES" else None)

    def end_entity():
        nonlocal cur_t, P, poly_t, poly_verts, poly_layer, poly_flags, poly_flip
        if cur_t is None: return
        t, pairs = cur_t, P
        cur_t, P = None, []
        target = sink()
        if target is None: return
        if t == "POLYLINE":
            first = dict(reversed(pairs))
            poly_t = "POLYLINE"; poly_verts = []; poly_layer = first.get("8", "0")
            poly_flags = int(_num(first.get("70", "0"))); poly_flip = _num(first.get("230", "1"), 1) < 0
            return
        if t == "VERTEX" and poly_t:
            first = dict(reversed(pairs))
            if not int(_num(first.get("70", "0"))) & 16:
                poly_verts.append((_num(first.get("10")), _num(first.get("20")), _num(first.get("42", "0"))))
            return
        if t == "SEQEND" and poly_t:
            pts = _poly(poly_verts, poly_flags & 1)
            if poly_flip: pts = [(-x, y) for x, y in pts]
            if len(pts) > 1: target.append({"t": "POLYLINE", "l": poly_layer, "p": [pts], "c": [bool(poly_flags & 1)]})
            poly_t = None; return
        if keep and not keep(t): return
        e = _decode(t, pairs)
        if e: target.append(e)

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        rl = fh.readline
        while True:
            c = rl()
            if not c: break
            v = rl().rstrip("\r\n"); c = c.strip()
            if c == "0":
                end_entity()
                if v == "SECTION": sec = "?"; continue
                if v == "ENDSEC": sec = None; continue
                if sec == "BLOCKS":
                    if v == "BLOCK": blk = "?"; cur_t = "_BLOCK"; continue
                    if v == "ENDBLK": blk = None; continue
                if sec in ("BLOCKS", "ENTITIES"): cur_t = v; P = []
                continue
            if sec == "?" and c == "2": sec = v; continue
            if cur_t == "_BLOCK":
                if c == "2" and blk == "?":
                    blk = v; blocks[blk] = {"base": [0.0, 0.0], "ents": []}
                elif c == "10" and blk not in (None, "?"): blocks[blk]["base"][0] = _num(v)
                elif c == "20" and blk not in (None, "?"): blocks[blk]["base"][1] = _num(v)
                continue
            if cur_t is not None: P.append((c, v))
        end_entity()
    return blocks, model


def mul(m, n):
    """m after n (both 2D affines a, b, c, d, e, f: x' = a x + c y + e, y' = b x + d y + f)"""
    a, b, c, d, e, f = m; A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def tf(m, pts):
    a, b, c, d, e, f = m
    return [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]


def insert_m(blocks, ins):
    """an insert's transform including its block's base point"""
    bx, by = blocks.get(ins["n"], {"base": (0, 0)})["base"]
    return mul(ins["m"], (1, 0, 0, 1, -bx, -by))


def walk(blocks, ents, fn, m=(1, 0, 0, 1, 0, 0), layer=None, path=(), depth=0, enter=None):
    """every primitive under ents with its world transform; enter(ins, m, layer, path) -> False skips an insert's content"""
    for e in ents:
        L = e["l"] if (e["l"] != "0" or layer is None) else layer
        if e["t"] == "INSERT":
            b = blocks.get(e["n"])
            if b is None or depth > 12: continue
            mm = mul(m, insert_m(blocks, e))
            if enter and enter(e, mm, L, path) is False: continue
            walk(blocks, b["ents"], fn, mm, L, path + (e["n"],), depth + 1, enter)
        else:
            fn(e, m, L, path)
