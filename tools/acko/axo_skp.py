"""A day for a new Acker's live model, straight from the SketchUp model (Ritika, 26 Oct: "build the axo based on this skp file").

Usage:  python -I tools/acko/axo_skp.py "<model>.skp" [--scene "Scene 1"] [--fine 0.035] [--coarse 0.07] [--stats]

The model (acko2A_model.skp, saved by SketchUp 2026) is read through SketchUp 2023's own C library (skp_read.py), headless.
What it holds: 101.7 M faces when every copy is counted, but only ~500 definitions with faces of their own; a whole office chair
is ~45 k faces (×638), the plants ~15 M. So:
  - visibility   the scene's own (--scene; "Scene 1" shows everything, plants included); placements far off the floor (two stray
                 chairs ~7.7 km away) are dropped
  - units        the highest definitions small enough (≤ UNIT_FACES faces counted in full, ≤ UNIT_SIZE m across): a whole chair,
                 a plant, a cluster. Each is flattened into one mesh in its own axes, simplified by vertex clustering, and drawn
                 once per placement (instancing); one used once is merged into the static geometry instead
  - static       everything else (slab, walls, partitions, façade), in world metres, simplified only where a definition is heavy
  - simplifying  two levels, each one cell size for all units (no bigger than a tenth of a unit): fine (3.5 cm, about a pixel
                 in the walk's close-ups; ~4.7 M triangles drawn) and coarse (7 cm, the whole floor; ~1.3 M)
  - kinds        per triangle, for the looks (assets/js/axo-model.js AxoModel.looks): glass (see-through materials), plant
                 (green ones under a plant tag or a plant-like name), wood / soft / hard (furniture, by material name), floor /
                 wall / slab / mullion / top / grass (the rest, by height, slope and material; the terrace's olive floor is grass,
                 kept in its colour); down-facing faces above CEIL m dropped; the zones' floors lifted 4 mm off the base floor
  - colours      each triangle its material's colour (a texture's average colour), the faces painted by their placement inherited
  - registration SketchUp metres onto the DXF's slab (data/axo-dxf.js, plan mm, y down): y flipped (or turned half round),
                 shifted by matching the two footprints at 10 cm; the overlap (IoU) is reported
  - route check  the day's route (slides/s-wayday.html ROUTE) against the walls and glass; a leg that crosses them away from its
                 ends (those are doors) is walked again by A* (the corridor floor preferred; furniture, the terrace's grass and
                 the planters avoided): AXO_SKP.route; the crossings left (the doors) reported, crossings.png and route.png
Writes data/axo-skp.js (window.AXO_SKP) in the world frame AxoModel uses (metres about the DXF slab's centre: x east, y up,
z south), and check pictures in tools/_work/axo-skp/.
"""
import argparse, base64, json, math, os, re, sys, time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skp_read

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "axo-skp")
INCH = skp_read.INCH
UNIT_FACES, UNIT_SIZE, CEIL = 400_000, 8.0, 2.6
FLOOR_BOX = (-10, 260, -10, 50)                               # SketchUp metres: what counts as on the floor
FINE, COARSE = 0.035, 0.07                                     # the two levels' cells (m)
KINDS = ["floor", "slab", "wall", "top", "mullion", "glass", "wood", "soft", "hard", "plant", "grass"]
K = {k: i for i, k in enumerate(KINDS)}
PLANT_TAG = re.compile(r"plant", re.I)
PLANTISH = re.compile(r"leaf|leaves|leav|foliage|plant|palm|banana|grass|fern|ivy|monstera|ficus|tree|bush|shrub|flower|succul|cactus|vase", re.I)
WOOD = re.compile(r"wood|oak|walnut|ply|lamin|madera|veneer|timber|teak|birch|maple|beech|cherry|pine|parquet|formica|bamboo|cork", re.I)
SOFT = re.compile(r"fabric|uphol|tapi|textil|kvadrat|jeans|leather|cushion|seat|sofa|velvet|wool|felt|carpet|rug|cloth|linen|boucle|hermes|clay\b", re.I)
METAL = re.compile(r"metal|chrome|steel|alum|pewter|iron|brass|copper|nickel|zinc|black", re.I)
DEFAULT_RGB = (236, 236, 234)


def log(*a):
    print(*a, flush=True)


# ---------- the plan side: the DXF slab and the day's route ----------
def read_js(path, name):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index(f"window.{name} = ") + len(f"window.{name} = "):].strip().rstrip(";"))


def day_route():
    s = open(os.path.join(ROOT, "slides", "s-wayday.html"), encoding="utf-8").read()
    m = re.search(r"const ROUTE = (\{.*?\});\n", s, re.S)
    return json.loads(m.group(1)) if m else None


# ---------- the model's graph: what is drawn, units, placements ----------
class Graph:
    def __init__(self, m, hidden):
        self.m, self.hidden = m, hidden
        self.E = {}
        for k in m.defs: self.expanded(k)
        self.size = {k: float(np.linalg.norm(d["bbox"][1] - d["bbox"][0])) * INCH for k, d in m.defs.items()}

    def expanded(self, k):
        if k not in self.E:
            d = self.m.defs[k]; self.E[k] = 0
            self.E[k] = len(d["faces"]) + sum(self.expanded(c[0]) for c in d["kids"] if c[5] not in self.hidden)
        return self.E[k]

    def is_unit(self, k):
        return k != "top" and 0 < self.E[k] <= UNIT_FACES and self.size[k] <= UNIT_SIZE

    def walk(self):
        """placements of units: {key: [(world 4x4 inches, tag, painted material ptr or 0, plant)]}; static: [(key, world, tag,
        paint, plant)]"""
        units, static = defaultdict(list), []
        top = self.m.defs["top"]; static.append(("top", np.eye(4), "Layer0", 0, False))

        def go(k, W, tag, paint, plant):
            for (ck, X, ctag, cmat, _hid, cent, cname) in self.m.defs[k]["kids"]:
                if cent in self.hidden: continue
                Wc = W @ X; t = ctag if ctag != "Layer0" else tag; p = cmat.ptr if cmat is not None else paint
                pl = plant or bool(PLANT_TAG.search(t)) or bool(PLANTISH.search(cname))
                if self.is_unit(ck): units[ck].append((Wc, t, p, pl))
                else: static.append((ck, Wc, t, p, pl)); go(ck, Wc, t, p, pl)

        for (ck, X, ctag, cmat, _hid, cent, cname) in top["kids"]:
            if cent in self.hidden: continue
            b = self.m.defs[ck]["bbox"]; c = X @ np.r_[(b[0] + b[1]) / 2, 1.0]; cx, cy = c[0] * INCH, c[1] * INCH
            if not (FLOOR_BOX[0] <= cx <= FLOOR_BOX[1] and FLOOR_BOX[2] <= cy <= FLOOR_BOX[3]): continue   # stray, off the floor
            p = cmat.ptr if cmat is not None else 0; pl = bool(PLANT_TAG.search(ctag)) or bool(PLANTISH.search(cname))
            if self.is_unit(ck): units[ck].append((X, ctag, p, pl))
            else: static.append((ck, X, ctag, p, pl)); go(ck, X, ctag, p, pl)
        return units, static

    def flatten(self, k, X, tag, paint, plant, out):
        """a definition and all under it into one mesh (positions by X), each triangle's material, tag and plant flag"""
        P, T, mat, fidx, fent = self.m.mesh(k)
        if len(T):
            vis = np.array([fe[0] not in self.hidden for fe in fent], dtype=bool)
            keep = vis[fidx]
            if keep.any():
                Tk = T[keep]; used = np.unique(Tk); remap = np.full(len(P), -1, np.int64); remap[used] = np.arange(len(used))
                Pw = (np.c_[P[used], np.ones(len(used))] @ X.T)[:, :3]
                mk = mat[keep].astype(np.uint64); mk[mk == 0] = paint or 0
                out.append((Pw, remap[Tk], mk, tag, plant))
        for (ck, Xc, ctag, cmat, _hid, cent, cname) in self.m.defs[k]["kids"]:
            if cent in self.hidden: continue
            t = ctag if ctag != "Layer0" else tag; p = cmat.ptr if cmat is not None else paint
            self.flatten(ck, X @ Xc, t, p, plant or bool(PLANT_TAG.search(t)) or bool(PLANTISH.search(cname)), out)
        return out


# ---------- meshes: merge, simplify, classify ----------
def merge(pieces):
    """[(P, T, mat, tag, plant)] -> P (n,3), T (m,3), per triangle: mat ptr, plant flag"""
    if not pieces: return np.zeros((0, 3)), np.zeros((0, 3), np.int64), np.zeros(0, np.uint64), np.zeros(0, bool)
    P, T, M, PL, base = [], [], [], [], 0
    for (p, t, mk, tag, pl) in pieces:
        P.append(p); T.append(t + base); M.append(mk); PL.append(pl if isinstance(pl, np.ndarray) else np.full(len(t), pl, bool)); base += len(p)
    return np.concatenate(P), np.concatenate(T), np.concatenate(M), np.concatenate(PL)


def cluster(P, T, c):
    """vertex clustering at cell c (same units as P): representative = the cell's mean; degenerate and repeated triangles
    dropped. Returns P2, T2, and the kept triangles' original indices"""
    if not len(T): return P, T, np.arange(0)
    q = np.floor(P / c).astype(np.int64)
    _, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True); inv = inv.ravel()
    P2 = np.zeros((len(cnt), 3)); np.add.at(P2, inv, P); P2 /= cnt[:, None]
    T2 = inv[T]
    ok = (T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])
    idx = np.nonzero(ok)[0]; s = np.sort(T2[idx], axis=1)
    _, first = np.unique(s, axis=0, return_index=True)
    idx = idx[np.sort(first)]
    return P2, T2[idx], idx


def colours_kinds(m, P, T, mat, plant, static):
    """per triangle: rgb (n,3 uint8), kind index; static ones by height and slope too (P in metres, z up)"""
    n = len(T); rgb = np.empty((n, 3), np.uint8); kind = np.empty(n, np.int16)
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    nrm = np.cross(b - a, c - a); ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1; nz = nrm[:, 2] / ln
    zmin, zmax = np.minimum(np.minimum(a[:, 2], b[:, 2]), c[:, 2]), np.maximum(np.maximum(a[:, 2], b[:, 2]), c[:, 2])
    info = {}
    for ptr in np.unique(mat):
        mm = m.material(skp_read.Ref(int(ptr))) if ptr else None
        info[int(ptr)] = mm if mm else ("", DEFAULT_RGB, 1.0)
    for ptr, (name, col, op) in info.items():
        sel = mat == ptr; rgb[sel] = col
        r, g, bb = col; greenish = g > r + 8 and g > bb + 8
        if op < 0.9: kind[sel] = K["glass"]; continue
        pl = sel & plant
        kind[pl & (greenish or bool(PLANTISH.search(name)))] = K["plant"]
        rest = sel & ~(plant & (greenish or bool(PLANTISH.search(name))))
        if static:
            if METAL.search(name): kind[rest] = K["mullion"]; continue
            flat = np.abs(nz) > 0.9
            olive = g >= r - 4 and g > bb + 20 and max(col) < 200                    # the terrace's grass (the renders' #949474)
            kind[rest & flat & (zmax <= 0.15)] = K["grass"] if olive else K["floor"]
            kind[rest & flat & (zmax > 0.15)] = K["top"]
            kind[rest & ~flat & (zmax <= 0.05)] = K["slab"]
            kind[rest & ~flat & (zmax > 0.05)] = K["wall"]
        else:
            kind[rest] = K["wood"] if WOOD.search(name) else K["soft"] if SOFT.search(name) else K["hard"]
    drop = (nz < -0.9) & (zmin > CEIL) if static else np.zeros(n, bool)          # ceilings would hide the floor
    return rgb, kind, drop


# ---------- registration onto the DXF's slab ----------
def raster(polys, x0, y0, nx, ny, res):
    from PIL import Image, ImageDraw
    im = Image.new("1", (nx, ny), 0); dr = ImageDraw.Draw(im)
    for poly in polys:
        dr.polygon([((x - x0) / res, (y - y0) / res) for x, y in poly], fill=1)
    return np.array(im, dtype=bool)


def register(floor_xy, slab):
    """SketchUp metres (x, y) -> plan mm (x, y down): try y flipped and turned half round, shift by matching footprints"""
    res = 0.1; sl = np.array(slab, float) / 1000.0
    best = None
    for name, A in (("flip y", np.array([[1, 0], [0, -1]])), ("half turn", np.array([[-1, 0], [0, 1]]))):
        tri = floor_xy @ A.T                                                            # (n,3,2) in plan metres (unshifted)
        # coarse: align the boxes' centres, then search shifts ±3 m at 10 cm by FFT correlation
        shift0 = (sl.min(0) + sl.max(0)) / 2 - (tri.reshape(-1, 2).min(0) + tri.reshape(-1, 2).max(0)) / 2
        tri = tri + shift0
        lo = np.minimum(tri.reshape(-1, 2).min(0), sl.min(0)) - 4; hi = np.maximum(tri.reshape(-1, 2).max(0), sl.max(0)) + 4
        nx, ny = int((hi[0] - lo[0]) / res) + 1, int((hi[1] - lo[1]) / res) + 1
        a = raster([t for t in tri], lo[0], lo[1], nx, ny, res).astype(np.float32)
        b = raster([sl], lo[0], lo[1], nx, ny, res).astype(np.float32)
        F = np.fft.irfft2(np.fft.rfft2(b) * np.conj(np.fft.rfft2(a)), s=b.shape)
        win = 30; F2 = np.full_like(F, -1)
        for dy in range(-win, win + 1):
            for dx in range(-win, win + 1): F2[dy % ny, dx % nx] = F[dy % ny, dx % nx]
        iy, ix = np.unravel_index(np.argmax(F2), F2.shape); dy = iy if iy <= ny // 2 else iy - ny; dx = ix if ix <= nx // 2 else ix - nx
        a2 = np.roll(np.roll(a, dy, 0), dx, 1) > 0; iou = (a2 & (b > 0)).sum() / max(1, (a2 | (b > 0)).sum())
        shift = shift0 + np.array([dx, dy]) * res
        if not best or iou > best[0]: best = (iou, name, A, shift)
    iou, name, A, shift = best
    # plan mm = 1000 * (A @ [x, y] + shift)
    return {"iou": round(float(iou), 4), "how": name, "A": A.tolist(), "shift_m": [round(float(v), 3) for v in shift]}


def frame_check(st0, Fm, dxf, CX, CY):
    """tools/_work/axo-skp/frame.png: the model's floor (grey), walls and glass (black) over the DXF's slab (red) and walls (blue)"""
    from PIL import Image, ImageDraw
    SP, ST, rgb, kind = st0; Pw = (np.c_[SP, np.ones(len(SP))] @ Fm.T)[:, :3]
    res = 0.05; lo = np.array([-125.0, -21.0]); nx, ny = int(250 / res), int(42 / res)
    im = Image.new("RGB", (nx, ny), "white"); d = ImageDraw.Draw(im)
    px = lambda x, z: ((x - lo[0]) / res, (z - lo[1]) / res)
    for t in ST[kind == K["floor"]]: d.polygon([px(Pw[i, 0], Pw[i, 2]) for i in t], fill=(225, 225, 225))
    for t in ST[np.isin(kind, [K["wall"], K["glass"]])]: d.line([px(Pw[i, 0], Pw[i, 2]) for i in t] + [px(Pw[t[0], 0], Pw[t[0], 2])], fill=(0, 0, 0), width=1)
    mm = lambda q: px((q[0] - CX) / 1000, (q[1] - CY) / 1000)
    for w in dxf["walls"]:
        for r in w: d.line([mm(q) for q in r] + [mm(r[0])], fill=(40, 90, 230), width=2)
    d.line([mm(q) for q in dxf["slab"]] + [mm(dxf["slab"][0])], fill=(200, 0, 0), width=3)
    im.save(os.path.join(WORK, "frame.png"))


# ---------- packing ----------
def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def pack_part(P, T, rgb, kind, unit, lift=None):
    """one drawable: indexed triangles, vertices keyed by (position, colour); int16 positions over its box; lift: per triangle,
    metres up"""
    if not len(T): return None
    C = P[T.ravel()].copy()
    if lift is not None: C[:, 1] += np.repeat(lift, 3)
    key = np.c_[np.round(C * 1000).astype(np.int64), np.repeat(rgb, 3, axis=0).astype(np.int64)]
    uk, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    V = uk[:, :3] / 1000.0; C3 = uk[:, 3:].astype(np.uint8)
    lo, hi = V.min(0), V.max(0); span = np.maximum(hi - lo, 1e-6)
    q = np.round((V - lo) / span * 65535 - 32768).astype(np.int16)
    I = inv.reshape(-1, 3); big = len(V) > 65535
    return {"k": KINDS[kind], "u": unit, "n": len(V), "t": len(I), "lo": [round(float(v), 4) for v in lo], "hi": [round(float(v), 4) for v in hi],
            "p": b64(q), "c": b64(C3), "i": b64(I.astype(np.uint32 if big else np.uint16)), "i32": bool(big)}


CORRIDOR_RGB = (188, 172, 198)                                   # the renders' corridor lavender (#b9a9c3 in their palette)


def reroute(legs, layers, lo, res, CX, CY, door=3.5):
    """legs (plan mm) that cross the walls or glass away from their ends (a crossing within `door` m of a leg's start or end is a
    door) walked again by A* on a 10 cm grid, start to end: the corridor floor preferred, furniture costly, the terrace's grass
    and the planters avoided, walls impassable but near the leg's ends (its doors), their 0.3 m clearance costly; the path
    string-pulled. A leg whose new way is over 3 times as long is kept as it was. Returns new legs and what changed."""
    import heapq
    from scipy import ndimage
    g = 0.1; f = int(round(g / res)); mask = layers["wall"]
    H, W = mask.shape[0] // f, mask.shape[1] // f
    down = lambda m: m[:H * f, :W * f].reshape(H, f, W, f).any(axis=(1, 3))
    wall = down(mask); yy, xx = np.mgrid[-3:4, -3:4]; disk = xx * xx + yy * yy <= 9
    block = ndimage.binary_dilation(wall, structure=disk)
    furn = ndimage.binary_dilation(down(layers["furn"]), structure=disk[1:-1, 1:-1])
    plant = ndimage.binary_dilation(down(layers["plant"]), structure=disk[1:-1, 1:-1])
    grass, corr = down(layers["grass"]), down(layers["corridor"])
    cost = np.where(corr, 0.8, 1.0); cost[furn] = 6.0; cost[grass] = 8.0; cost[plant] = 30.0; cost[block] = np.maximum(cost[block], 25.0)
    cell = lambda p: (int((p[1] - lo[1]) / g), int((p[0] - lo[0]) / g))                  # (row, col) of a world (x, z)
    world = lambda rc: np.array([lo[0] + (rc[1] + 0.5) * g, lo[1] + (rc[0] + 0.5) * g])
    to_w = lambda q: np.array([(q[0] - CX) / 1000, (q[1] - CY) / 1000]); to_mm = lambda w: [int(round(w[0] * 1000 + CX)), int(round(w[1] * 1000 + CY))]

    def clear(a, b):
        n = max(2, int(np.linalg.norm(b - a) / (g / 2)))
        for t in np.linspace(0, 1, n):
            r, c = cell(a + (b - a) * t)
            if not (0 <= r < H and 0 <= c < W) or block[r, c] or furn[r, c] or plant[r, c] or grass[r, c]: return False
        return True

    def astar(a, b, box):
        r0, c0, r1, c1 = box; s, t = cell(a), cell(b)
        near = lambda v: math.hypot(v[0] - s[0], v[1] - s[1]) * g < door or math.hypot(v[0] - t[0], v[1] - t[1]) * g < door
        D = {s: 0.0}; prev = {}; pq = [(0.0, 0.0, s)]
        steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        while pq:
            _, d, u = heapq.heappop(pq)
            if u == t: break
            if d > D.get(u, 1e18): continue
            for dr, dc, w in steps:
                v = (u[0] + dr, u[1] + dc)
                if not (r0 <= v[0] < r1 and c0 <= v[1] < c1): continue
                if wall[v] and not near(v): continue
                nd = d + w * (60.0 if wall[v] else cost[v])
                if nd < D.get(v, 1e18):
                    D[v] = nd; prev[v] = u; heapq.heappush(pq, (nd + 0.8 * math.hypot(v[0] - t[0], v[1] - t[1]), nd, v))
        if t not in prev: return None
        path = [t]
        while path[-1] != s: path.append(prev[path[-1]])
        pts = [world(rc) for rc in path[::-1]]; pts[0], pts[-1] = a, b
        out = [pts[0]]; i = 0                                                                # string-pulling
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not clear(pts[i], pts[j]): j -= 1
            out.append(pts[j]); i = j
        return out

    new, changes = [], []
    for li, leg in enumerate(legs):
        P = [to_w(q) for q in leg]; cum = [0.0]
        for i in range(1, len(P)): cum.append(cum[-1] + float(np.linalg.norm(P[i] - P[i - 1])))
        L = cum[-1]; hit = False
        for i in range(len(P) - 1):
            for t in np.linspace(0, 1, max(2, int((cum[i + 1] - cum[i]) / 0.05))):
                sd = cum[i] + (cum[i + 1] - cum[i]) * t; r, c = cell(P[i] + (P[i + 1] - P[i]) * t)
                if 0 <= r < H and 0 <= c < W and wall[r, c] and door < sd < L - door: hit = True; break
            if hit: break
        if not hit: new.append(leg); continue
        ps = np.array(P); m_ = int(15 / g); rr = [cell(q) for q in P]
        box = (max(0, min(r for r, c in rr) - m_), max(0, min(c for r, c in rr) - m_), min(H, max(r for r, c in rr) + m_), min(W, max(c for r, c in rr) + m_))
        path = astar(P[0], P[-1], box)
        plen = sum(float(np.linalg.norm(path[i] - path[i - 1])) for i in range(1, len(path))) if path else 0
        if path is None or plen > 3 * L: changes.append({"leg": li, "ok": False, "m": round(L, 1)}); new.append(leg); continue
        changes.append({"leg": li, "ok": True, "was_m": round(L, 1), "m": round(plen, 1)})
        new.append([to_mm(q) for q in path])
    return new, changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skp"); ap.add_argument("--scene", default="Scene 1")
    ap.add_argument("--fine", type=float, default=FINE); ap.add_argument("--coarse", type=float, default=COARSE)
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    t0 = time.time(); m = skp_read.Model(a.skp)
    log(f"opened {os.path.basename(a.skp)} (status {m.status}) in {time.time() - t0:.1f} s: {len(m.defs)} definitions")
    hidden = m.scene_hidden(a.scene); log(f"{a.scene} hides {len(hidden)} entities")
    g = Graph(m, hidden); units, static = g.walk()
    mult = {k: len(v) for k, v in units.items()}
    log(f"units {len(units)} ({sum(mult.values()):,} placements; {sum(1 for v in mult.values() if v == 1)} used once), static definitions {len(static)}")

    # ---- units: flattened in their own axes (metres, z up), simplified at the two cells ----
    A_SKP = np.diag([INCH, INCH, INCH, 1.0]); iA = np.linalg.inv(A_SKP)
    t1 = time.time(); simp = {}
    for k in units:
        P, T, M, PL = merge(g.flatten(k, A_SKP, "Layer0", 0, False, []))
        pl_any = any(p[3] for p in units[k]); lim = max(0.004, g.size[k] / 10)
        simp[k] = []
        for c in (a.fine, a.coarse):
            P2, T2, idx = cluster(P, T, min(c, lim)) if len(T) else (P, T, np.arange(0))
            simp[k].append((P2, T2, M[idx], PL[idx] | pl_any))
    log(f"units simplified in {time.time() - t1:.1f} s")
    for li, name in ((0, "fine"), (1, "coarse")):
        log(f"  {name} ({(a.fine, a.coarse)[li] * 100:.1f} cm): drawn {sum(len(simp[k][li][1]) * mult[k] for k in units):,}, stored {sum(len(simp[k][li][1]) for k in units):,}")
    heavy = sorted(units, key=lambda k: -len(simp[k][0][1]) * mult[k])[:12]
    for k in heavy: log(f"    {len(simp[k][0][1]):>7,} x {mult[k]:>5} = {len(simp[k][0][1]) * mult[k]:>10,}  {m.defs[k]['name'][:60]}")
    if a.stats: m.close(); return

    # ---- static geometry (SketchUp metres, z up): the architecture (both levels), and the units used once (one per level) ----
    t2 = time.time(); pieces = {0: [], 1: [], 2: []}                               # level 0: both; 1 fine; 2 coarse
    for (k, W, tag, paint, pl) in static:
        P, T, mat, fidx, fent = m.mesh(k)
        if not len(T): continue
        vis = np.array([fe[0] not in hidden for fe in fent], dtype=bool); keep = vis[fidx]
        if not keep.any(): continue
        Tk = T[keep]; used = np.unique(Tk); remap = np.full(len(P), -1, np.int64); remap[used] = np.arange(len(used))
        Pw = (np.c_[P[used], np.ones(len(used))] @ (A_SKP @ W).T)[:, :3]; mk = mat[keep].astype(np.uint64); mk[mk == 0] = paint or 0
        Tr = remap[Tk]
        if len(Tr) > 5000:                                                        # a heavy definition: simplified like the units
            for lv, c in ((1, a.fine), (2, a.coarse)):
                P2, T2, idx = cluster(Pw, Tr, c); pieces[lv].append((P2, T2, mk[idx], tag, pl))
        else: pieces[0].append((Pw, Tr, mk, tag, pl))
    for k, pls in units.items():
        if len(pls) != 1: continue
        Wm = A_SKP @ pls[0][0] @ iA
        for lv in (1, 2):
            P2, T2, M2, PL2 = simp[k][lv - 1]
            if len(T2): pieces[lv].append(((np.c_[P2, np.ones(len(P2))] @ Wm.T)[:, :3], T2, M2, pls[0][1], PL2))
    # the light definitions are the architecture (kinds by height and slope); the heavy ones and the units used once are furniture
    stat = {}
    for lv in (0, 1, 2):
        SP, ST, SM, SPL = merge(pieces[lv])
        rgb, kind, drop = colours_kinds(m, SP, ST, SM, SPL, lv == 0) if len(ST) else (np.zeros((0, 3), np.uint8), np.zeros(0, np.int16), np.zeros(0, bool))
        stat[lv] = (SP, ST[~drop], rgb[~drop], kind[~drop])
        log(f"static level {lv}: {len(ST):,} triangles ({int(drop.sum()):,} ceiling dropped); kinds {dict((KINDS[i], int(n)) for i, n in zip(*np.unique(kind[~drop], return_counts=True)))}")
    log(f"  in {time.time() - t2:.1f} s")

    # ---- registration: the floor's footprint onto the DXF slab ----
    SP0, ST0, _, K0 = stat[0]; ftri = SP0[ST0[K0 == K["floor"]]][:, :, :2]
    dxf = read_js(os.path.join(ROOT, "data", "axo-dxf.js"), "AXO_DXF"); slab = dxf["slab"]
    reg = register(ftri, slab); log(f"registration: {reg}")
    xs, ys = [p[0] for p in slab], [p[1] for p in slab]; CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    A2 = np.array(reg["A"], float); sh = np.array(reg["shift_m"])
    # SketchUp metres (x, y, z up) -> world metres (x east, y up, z south): plan mm = 1000 (A2 [x, y] + shift); world = plan / 1000 - centre
    Fm = np.array([[A2[0, 0], A2[0, 1], 0, sh[0] - CX / 1000], [0, 0, 1, 0], [A2[1, 0], A2[1, 1], 0, sh[1] - CY / 1000], [0, 0, 0, 1]])
    Lin = Fm[:3, :3]
    frame_check(stat[0], Fm, dxf, CX, CY)

    # ---- the parts: static by level and kind; each unit used more than once by level and kind, with its placements ----
    parts, unit_out, drawn = [], [], [0, 0]
    for lv in (0, 1, 2):
        SP, ST, rgb, kind = stat[lv]
        if not len(ST): continue
        SPw = (np.c_[SP, np.ones(len(SP))] @ Fm.T)[:, :3]
        # the zones' floors (rooms, corridor, café, terrace) lie in the base floor's plane: lifted 4 mm so they don't flicker
        lift = np.zeros(len(ST)); fl = np.isin(kind, [K["floor"], K["grass"]]) & (np.abs(SPw[ST][:, :, 1].mean(1)) < 0.012)
        if fl.any():
            key = rgb[fl].astype(np.int64) @ np.array([65536, 256, 1]); a_ = SPw[ST[fl]]
            area = np.linalg.norm(np.cross(a_[:, 1] - a_[:, 0], a_[:, 2] - a_[:, 0]), axis=1)
            u, inv = np.unique(key, return_inverse=True); base = u[np.argmax(np.bincount(inv.ravel(), weights=area))]
            lift[np.nonzero(fl)[0][key != base]] = 0.004
        for kk in np.unique(kind):
            sel = kind == kk; pp = pack_part(SPw, ST[sel], rgb[sel], int(kk), -1, lift[sel])
            if pp: pp["lv"] = lv; parts.append(pp)
        for i in (0, 1):
            if lv == 0 or lv == i + 1: drawn[i] += len(ST)
    for k, pls in units.items():
        if len(pls) < 2: continue
        mats = []
        for (W, tag, paint, pl) in pls:
            Wm = Fm @ A_SKP @ W @ iA                                                  # unit metres -> world
            Mw = Wm[:3, :3] @ np.linalg.inv(Lin); mats.append(np.r_[Mw.T.ravel(), Wm[:3, 3]])   # column-major 3x3, then t
        ui = len(unit_out); unit_out.append({"name": m.defs[k]["name"][:60], "n": len(pls), "m": b64(np.array(mats, np.float32))})
        for lv in (1, 2):
            P2, T2, M2, PL2 = simp[k][lv - 1]
            if not len(T2): continue
            rgb, kind, _ = colours_kinds(m, P2, T2, M2, PL2, False)
            G3 = P2 @ Lin.T                                                           # the unit in world axes, about its own origin
            for kk in np.unique(kind):
                sel = kind == kk; pp = pack_part(G3, T2[sel], rgb[sel], int(kk), ui)
                if pp: pp["lv"] = lv; parts.append(pp)
            drawn[lv - 1] += len(T2) * len(pls)
    log(f"parts {len(parts)} ({sum(1 for p in parts if p['u'] < 0)} static, {len(unit_out)} instanced units); drawn fine {drawn[0]:,}, coarse {drawn[1]:,}")

    # ---- the route against the walls and glass (fine level) ----
    R = day_route(); crossings = []
    if R:
        from PIL import Image, ImageDraw
        segs = []
        def add_segs(Pw, T, kind):
            wall = np.isin(kind, [K["wall"], K["glass"], K["mullion"]])
            a_, b_, c_ = Pw[T[wall][:, 0]], Pw[T[wall][:, 1]], Pw[T[wall][:, 2]]
            low = np.minimum(np.minimum(a_[:, 1], b_[:, 1]), c_[:, 1]) < 1.2
            for (p, q) in ((a_, b_), (b_, c_), (c_, a_)): segs.append(np.c_[p[low][:, [0, 2]], q[low][:, [0, 2]]])
        for lv in (0, 1):
            SP, ST, rgb, kind = stat[lv]
            if len(ST): add_segs((np.c_[SP, np.ones(len(SP))] @ Fm.T)[:, :3], ST, kind)
        for k, pls in units.items():
            if len(pls) < 2: continue
            P2, T2, M2, PL2 = simp[k][0]
            if not len(T2): continue
            _, kind, _ = colours_kinds(m, P2, T2, M2, PL2, False)
            if not (kind == K["glass"]).any(): continue
            for (W, tag, paint, pl) in pls:
                Wm = Fm @ A_SKP @ W @ iA; add_segs((np.c_[P2, np.ones(len(P2))] @ Wm.T)[:, :3], T2, kind)
        segs = np.concatenate(segs) if segs else np.zeros((0, 4))
        allp = np.concatenate([(np.c_[stat[lv][0], np.ones(len(stat[lv][0]))] @ Fm.T)[:, [0, 2]] for lv in (0, 1) if len(stat[lv][0])])
        res = 0.05; lo = allp.min(0) - 1; nx, ny = [int(v) + 1 for v in (allp.max(0) - lo + 1) / res]
        im = Image.new("1", (nx, ny), 0); dr = ImageDraw.Draw(im)
        for s in segs:
            if abs(s[0] - s[2]) + abs(s[1] - s[3]) > 0.001: dr.line([((s[0] - lo[0]) / res, (s[1] - lo[1]) / res), ((s[2] - lo[0]) / res, (s[3] - lo[1]) / res)], fill=1)
        mask = np.array(im, bool)
        # the furniture's and the plants' footprints (static triangles; each instanced unit's footprint box, placed), the grass
        # and the corridor's floor
        imf, imp, img_, imc = (Image.new("1", (nx, ny), 0) for _ in range(4)); df, dp_, dg, dc = (ImageDraw.Draw(i) for i in (imf, imp, img_, imc))
        tri2 = lambda Pw, t: [((Pw[i, 0] - lo[0]) / res, (Pw[i, 2] - lo[1]) / res) for i in t]
        SP, ST, rgb, kind = stat[1]
        if len(ST):
            Pw = (np.c_[SP, np.ones(len(SP))] @ Fm.T)[:, :3]
            for t, kk in zip(ST, kind):
                if Pw[t, 1].min() < 1.0 and kk in (K["wood"], K["soft"], K["hard"], K["plant"]): (dp_ if kk == K["plant"] else df).polygon(tri2(Pw, t), fill=1)
        SP, ST, rgb, kind = stat[0]
        if len(ST):
            Pw = (np.c_[SP, np.ones(len(SP))] @ Fm.T)[:, :3]
            for t, kk, cc in zip(ST, kind, rgb):
                if kk == K["grass"]: dg.polygon(tri2(Pw, t), fill=1)
                elif kk == K["floor"] and max(abs(int(cc[i]) - CORRIDOR_RGB[i]) for i in range(3)) < 14: dc.polygon(tri2(Pw, t), fill=1)
        for k, pls in units.items():
            if len(pls) < 2: continue
            P2, T2, M2, PL2 = simp[k][0]
            if not len(P2): continue
            low = P2[P2[:, 2] < 1.0]
            if not len(low): continue
            _, kind, _ = colours_kinds(m, P2, T2, M2, PL2, False); isplant = (kind == K["plant"]).mean() > 0.3
            (x0, y0), (x1, y1) = low[:, :2].min(0), low[:, :2].max(0)
            corners = np.array([[x0, y0, 0, 1], [x1, y0, 0, 1], [x1, y1, 0, 1], [x0, y1, 0, 1]])
            for (W, tag, paint, pl) in pls:
                c4 = corners @ (Fm @ A_SKP @ W @ iA).T
                (dp_ if isplant else df).polygon([((c[0] - lo[0]) / res, (c[2] - lo[1]) / res) for c in c4], fill=1)
        layers = {"wall": mask, "furn": np.array(imf, bool), "plant": np.array(imp, bool), "grass": np.array(img_, bool), "corridor": np.array(imc, bool)}
        np.savez_compressed(os.path.join(WORK, "route.npz"), lo=lo, res=res, CX=CX, CY=CY, legs=json.dumps(R["legs"]), **layers)
        legs, changes = reroute(R["legs"], layers, lo, res, CX, CY)
        log(f"re-routed: {changes}")
        R = {"stops": R["stops"], "legs": legs}
        for li, leg in enumerate(R["legs"]):
            for i in range(len(leg) - 1):
                p = np.array([(leg[i][0] - CX) / 1000, (leg[i][1] - CY) / 1000]); q = np.array([(leg[i + 1][0] - CX) / 1000, (leg[i + 1][1] - CY) / 1000])
                for t in np.linspace(0, 1, max(2, int(np.linalg.norm(q - p) / 0.05))):
                    x = p + (q - p) * t; ix, iy = int((x[0] - lo[0]) / res), int((x[1] - lo[1]) / res)
                    if 0 <= ix < nx and 0 <= iy < ny and mask[iy, ix]:
                        crossings.append({"leg": li, "seg": i, "at_mm": [round(float(x[0] * 1000 + CX)), round(float(x[1] * 1000 + CY))]}); break
        log(f"route crossings with walls and glass: {len(crossings)}", crossings[:12])
        pic = Image.fromarray((~mask).astype(np.uint8) * 255).convert("RGB"); d2 = ImageDraw.Draw(pic)
        for leg in R["legs"]:
            d2.line([(((x - CX) / 1000 - lo[0]) / res, ((y - CY) / 1000 - lo[1]) / res) for x, y in leg], fill=(152, 0, 0), width=3)
        for c in crossings:
            x, y = c["at_mm"]; px, py = ((x - CX) / 1000 - lo[0]) / res, ((y - CY) / 1000 - lo[1]) / res; d2.ellipse([px - 14, py - 14, px + 14, py + 14], outline=(0, 0, 255), width=4)
        pic.save(os.path.join(WORK, "route.png"))
        # each crossing up close (12 x 8 m, 3x): route.png's crops, numbered as listed
        if crossings:
            cw, ch, z = int(12 / res), int(8 / res), 3; cols = 4; rows = (len(crossings) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * cw * z, rows * ch * z), "white"); ds = ImageDraw.Draw(sheet)
            for j, c in enumerate(crossings):
                x, y = c["at_mm"]; px, py = ((x - CX) / 1000 - lo[0]) / res, ((y - CY) / 1000 - lo[1]) / res
                crop = pic.crop((int(px - cw / 2), int(py - ch / 2), int(px + cw / 2), int(py + ch / 2))).resize((cw * z, ch * z), Image.NEAREST)
                sheet.paste(crop, ((j % cols) * cw * z, (j // cols) * ch * z)); ds.text(((j % cols) * cw * z + 8, (j // cols) * ch * z + 6), f"{j}: leg {c['leg']} seg {c['seg']}", fill=(0, 0, 255))
            sheet.save(os.path.join(WORK, "crossings.png"))

    out = {"source": os.path.basename(a.skp), "scene": a.scene, "built": time.strftime("%Y-%m-%d"), "kinds": KINDS, "cells": [a.fine, a.coarse],
           "registration": reg, "drawn": drawn, "parts": parts, "units": unit_out, "crossings": crossings,
           "route": R["legs"] if R else None, "rerouted": changes if R else []}
    js = ("/* A day for a new Acker's model, made by tools/acko/axo_skp.py from the SketchUp model; world metres about the DXF slab's "
          "centre (x east, y up, z south) */\nwindow.AXO_SKP = " + json.dumps(out, separators=(",", ":")) + ";\n")
    with open(os.path.join(ROOT, "data", "axo-skp.js"), "w", encoding="utf-8", newline="\n") as f: f.write(js)
    log(f"data/axo-skp.js: {len(js) / 1e6:.1f} MB in {time.time() - t0:.0f} s")
    m.close()


if __name__ == "__main__":
    main()
