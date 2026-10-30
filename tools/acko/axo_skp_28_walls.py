"""The SketchUp model's fit-out walls rebuilt from the 28.10 plan (Ritika, 30 Oct: "check all walls and wall types as per the
latest plan", "Rebuild from 28.10", then "wall terminations are not fine// also z fighting is happening": so none of the model's
fit-out walls are kept beside the plan's, and the plan's own bodies meet at their corners); used by tools/acko/axo_skp_28.py,
which writes the result into data/axo-skp.js (AXO_SKP.changes).

  plan    basePlan.dxf's walls and partitions as bodies (plan mm, y down), by type, each one union (so they join cleanly):
            wall   the walls' own fill (A-WALL-PATT) and the other wall lines (widened 55 mm a side), to 3.7 m
            solid  the gypsum partitions' outlines (closed) and face lines (widened 55 mm a side, a pair of faces filling
                   between them), less the walls, to 2.4 m; and the OB-I-PART-GYP outlines where no glass runs along them (in
                   the glass rooms they trace the glass system: 30 Oct, the departmental room)
            glass  the glass partitions' lines (widened 30 mm a side), less the walls and gypsum partitions, to 2.4 m
          clipped to the slab less EDGE mm (the façade stays the model's) and less the core (the model's solid block, "Not in
          contract"), so they run up to both; under THICK mm across on average (a wall, not a filled shaft)
  model   the model's walls, partitions and glass as pieces (a merged part's triangles joined where they share a corner; a
          component's placement); its fit-out ones go: every wall, top, glass and frame piece rising past 1.8 m, and the hard
          ones that stand along the plan's walls (its full-height panels; a cabinet or a screen in a room stays). The core,
          the façade (most of a piece within FACADE mm of the slab's edge) and the columns stay
Returns {walls: {wall|solid|glass: [[ring, hole...]]}, heights, drop: {part: [[t0, t1], ...]}, hide: [[unit, i], ...]} and
what the check picture needs.
"""
import base64, math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, sparse
from scipy.sparse.csgraph import connected_components
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

import dxf_read as D

WALL_FILLS = {"A-WALL-PATT"}                                        # hatches: the walls' own fill
WALL_LINES = {"OB-A-WALL", "I_WALL_WA_CS_BR_100"}
SOLID_LINES = {"I-PART-GYP-100MM", "I-PART-GYP"}                 # the gypsum partitions
SOLID_FILLS = {"I-PART-GYP", "I-PART-GYP-100MM"}                  # (closed outlines)
WEAK = {"OB-I-PART-GYP"}                                           # outlines that also run along the glass systems: solid only off the glass
GLASS_LINES = {"OB-I-PART-GLS", "I_PAR_PA_IN_GL", "I-PART-GLSS", "SKV_GLASS PARTITION"}
HEIGHT = {"wall": 3.7, "solid": 2.4, "glass": 2.4}
FACADE, EDGE, NEAR, RES, THICK = 800.0, 250.0, 150.0, 25.0, 450.0


def b64(s, dt): return np.frombuffer(base64.b64decode(s), dtype=dt)


def plan_bodies(blocks, model, pt):
    """basePlan's wall bodies by type, in the slide's plan frame (pt maps drawing x, y to plan mm)"""
    B = {"wall": [], "solid": [], "weak": [], "glass": []}
    def fn(e, m, L, p):
        if e["t"] in ("TEXT", "MTEXT"): return
        C = e.get("c") or []
        for i, r in enumerate(e.get("p", [])):
            q = [pt(x, y) for x, y in D.tf(m, r)]
            if len(q) < 2: continue
            closed = e["t"] == "HATCH" or (C[i] if i < len(C) else False)
            if L in WALL_FILLS and closed and len(q) >= 3: B["wall"].append(Polygon(q).buffer(0)); continue
            if (L in SOLID_FILLS or L in WEAK) and closed and len(q) >= 3:
                pg = Polygon(q).buffer(0)
                if pg.area > 2e4: B["weak" if L in WEAK else "solid"].append(pg); continue
            line = LineString(q + ([q[0]] if closed else []))
            if L in WALL_LINES: B["wall"].append(line.buffer(55, cap_style=2, join_style=2))
            elif L in SOLID_LINES: B["solid"].append(line.buffer(55, cap_style=2, join_style=2))
            elif L in WEAK: B["weak"].append(line.buffer(55, cap_style=2, join_style=2))
            elif L in GLASS_LINES: B["glass"].append(line.buffer(30, cap_style=2, join_style=2))
    D.walk(blocks, model, fn)
    clean = lambda g: unary_union(g).buffer(10, join_style=2).buffer(-10, join_style=2)
    # which wins where they overlap: the walls, the gypsum partitions, the glass, then the weak outlines (off the glass)
    wall = clean(B["wall"]); solid = clean(B["solid"]).difference(wall); glass = clean(B["glass"]).difference(wall.union(solid))
    solid = solid.union(clean(B["weak"]).difference(wall.union(glass.buffer(80))))
    return {"wall": wall, "solid": solid, "glass": glass}


def model_pieces(S, CX, CY):
    """the model's walls and glass as pieces: {ty, pts (plan mm, its tall faces' middles), h, part|unit}"""
    out = []
    units = [b64(u["m"], np.float32).reshape(-1, 12) for u in S["units"]]
    KIND = {"wall": "solid", "top": "solid", "hard": "solid", "mass": "core", "glass": "glass", "mullion": "glass"}
    seen_units = {}
    for pi, p in enumerate(S["parts"]):
        if p["k"] not in KIND or p["lv"] == 2: continue
        q = b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3); lo, hi = np.array(p["lo"]), np.array(p["hi"]); v = lo + (q + 32768) / 65535 * (hi - lo)
        idx = b64(p["i"], np.uint32 if p.get("i32") else np.uint16).reshape(-1, 3).astype(np.int64)
        if p["u"] >= 0:                                              # a component: one piece per placement (its parts together)
            for i, m in enumerate(units[p["u"]]):
                vv = v @ np.array([[m[0], m[3], m[6]], [m[1], m[4], m[7]], [m[2], m[5], m[8]]]).T + m[9:12]
                key = (p["u"], i); T3 = vv[idx]
                pc = seen_units.setdefault(key, {"ty": None, "tris": [], "unit": key, "kind": set()}); pc["kind"].add(p["k"])
                pc["tris"].append(T3); pc["ty"] = "glass" if KIND[p["k"]] == "glass" or pc["ty"] == "glass" else KIND[p["k"]]
            continue
        # a merged part: its triangles joined where they share a corner (5 mm)
        key = np.round(v * 200).astype(np.int64); _, vid = np.unique(key, axis=0, return_inverse=True); vid = vid.ravel()
        n = len(idx); nv = vid.max() + 1
        rows = np.repeat(np.arange(n), 3); cols = n + vid[idx].ravel()
        G = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n + nv, n + nv))
        _, lab = connected_components(G, directed=False); lab = lab[:n]
        T3 = v[idx]
        for c in np.unique(lab):
            sel = np.nonzero(lab == c)[0]
            out.append({"ty": KIND[p["k"]], "T": T3[sel], "part": pi, "tris": sel, "kind": {p["k"]}})
    for key, pc in seen_units.items():
        out.append({"ty": pc["ty"], "T": np.concatenate(pc["tris"]), "unit": key, "kind": pc["kind"]})
    for pc in out:
        T = pc["T"]; ymax = T[:, :, 1].max(1); vert = np.ptp(T[:, :, 1], 1) > 0.3
        tall = vert & (ymax > 1.8); pc["h"] = float(T[:, :, 1].max())
        mid = T[tall].mean(1) if tall.any() else np.zeros((0, 3))
        pc["pts"] = np.stack([mid[:, 0] * 1000 + CX, mid[:, 2] * 1000 + CY], 1) if len(mid) else np.zeros((0, 2))
        xz = T.reshape(-1, 3)[:, [0, 2]] * 1000 + (CX, CY); pc["box"] = (*xz.min(0), *xz.max(0))
        del pc["T"]
    return out


def raster(geom, box, res=RES):
    x0, y0, x1, y1 = box; W, H = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty: continue
        d.polygon([((x - x0) / res, (y - y0) / res) for x, y in g.exterior.coords], fill=255)
        for h in g.interiors: d.polygon([((x - x0) / res, (y - y0) / res) for x, y in h.coords], fill=0)
    return np.asarray(im) > 0


def rebuild(S, blocks, model, pt, slab, CX, CY, log):
    bodies = plan_bodies(blocks, model, pt)
    log("28.10 bodies: " + ", ".join(f"{k} {g.area / 1e6:.0f} m2" for k, g in bodies.items()))
    pieces = model_pieces(S, CX, CY)
    core = unary_union([Polygon([(pc["box"][0], pc["box"][1]), (pc["box"][2], pc["box"][1]), (pc["box"][2], pc["box"][3]), (pc["box"][0], pc["box"][3])])
                        for pc in pieces if pc["ty"] == "core"])
    slabp = Polygon(slab); facade = prep(slabp.buffer(-FACADE)); near_core = prep(core.buffer(300))
    box = (min(x for x, _ in slab) - 2000, min(y for _, y in slab) - 2000, max(x for x, _ in slab) + 2000, max(y for _, y in slab) + 2000)
    anyw = ndimage.binary_dilation(raster(unary_union(list(bodies.values())), box), iterations=int(NEAR / RES)); x0, y0 = box[0], box[1]
    def along(pts):
        ij = ((pts - (x0, y0)) / RES).astype(int); H, W = anyw.shape
        ok = (ij[:, 0] >= 0) & (ij[:, 1] >= 0) & (ij[:, 0] < W) & (ij[:, 1] < H)
        hit = np.zeros(len(pts), bool); hit[ok] = anyw[ij[ok, 1], ij[ok, 0]]
        return hit.mean() if len(pts) else 0.0
    drop, hide = {}, []; stats = {"gone": 0, "stays": 0}
    for pc in pieces:
        pts = pc["pts"]
        if pc["ty"] == "core" or not len(pts): stats["stays"] += 1; continue
        smp = pts[:: max(1, len(pts) // 16)]
        at_facade = np.mean([not facade.contains(Point(x, y)) for x, y in smp]) > 0.5
        at_core = np.mean([near_core.contains(Point(x, y)) for x, y in smp]) > 0.5
        bx = pc["box"]; column = bx[2] - bx[0] < 1500 and bx[3] - bx[1] < 1500 and pc["h"] > 3.0
        loose = pc["kind"] <= {"hard"} and along(pts) < 0.5                 # a cabinet, a screen: not a wall
        if at_facade or at_core or column or loose: stats["stays"] += 1; continue
        stats["gone"] += 1; pc["gone"] = True
        if "unit" in pc: hide.append([int(pc["unit"][0]), int(pc["unit"][1])])
        else:
            t = np.sort(pc["tris"]); br = np.nonzero(np.diff(t) > 1)[0]
            starts = np.r_[t[0], t[br + 1]]; ends = np.r_[t[br], t[-1]]
            drop.setdefault(str(pc["part"]), []).extend([[int(a), int(b) + 1] for a, b in zip(starts, ends)])
    log(f"model fit-out walls: {stats['gone']} gone; {stats['stays']} pieces stay (core, facade, columns, cabinets, low pieces)")
    zone = slabp.buffer(-EDGE).difference(core)
    walls = {}
    for ty, body in bodies.items():
        add = body.intersection(zone)
        polys = [g for g in getattr(add, "geoms", [add]) if isinstance(g, Polygon) and g.area > 4e4 and g.length > 1200 and 2 * g.area / g.length < THICK]
        walls[ty] = [[[[round(x), round(y)] for x, y in g.simplify(10).exterior.coords[:-1]]] +
                     [[[round(x), round(y)] for x, y in h.coords[:-1]] for h in g.interiors] for g in polys]
        log(f"  {ty}: {len(polys)} pieces, {sum(g.area for g in polys) / 1e6:.1f} m2, to {HEIGHT[ty]} m")
    return {"walls": walls, "heights": HEIGHT, "drop": drop, "hide": hide, "solid": bodies["solid"].union(bodies["wall"]),
            "glass": bodies["glass"], "pieces": pieces, "box": box}
