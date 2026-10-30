"""The SketchUp model's fit-out walls rebuilt from the 28.10 plan (Ritika, 30 Oct: "check all walls and wall types as per the
latest plan", "Rebuild from 28.10", then "wall terminations are not fine// also z fighting is happening": so none of the model's
fit-out walls are kept beside the plan's, and the plan's own bodies meet at their corners); used by tools/acko/axo_skp_28.py,
which writes the result into data/axo-skp.js (AXO_SKP.changes).

  plan    the deck's floor plan's walls and partitions (data/plan-base.js, as it draws: hidden blocks left out) as bodies (plan mm,
          y down), by type, each one union (so they join cleanly):
            wall   the walls' own fill (A-WALL-PATT) and the other wall lines (widened 55 mm a side), to 2.4 m
            solid  the solid partitions' outlines (closed) and face lines (widened 55 mm a side, a pair of faces filling
                   between them): I-PART-GYP(-100MM), OB-I-PART-GYP, OB-I-PART-SOF, SKV_GLASS PARTITION; less the walls, to
                   2.4 m
            glass  OB-I-PART-GLS and I-PART-GLSS lines (widened 30 mm a side), less the walls and wherever a solid outline
                   runs within GLASS_WINS mm, to 2.4 m
          the floor plan alone decides each wall and its type (30 Oct: "instead of using sketchup walls,... can you extrute
          the walls based on the floor plan?")
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
# the plan's layers, as Ritika reads them (30 Oct: glass is "OB-I-PART-GLS, I-PART-GLSS"; the rest of the partitions solid)
SOLID_LINES = {"I-PART-GYP-100MM", "I-PART-GYP", "OB-I-PART-GYP", "OB-I-PART-SOF", "SKV_GLASS PARTITION"}
SOLID_FILLS = SOLID_LINES                                          # (their closed outlines)
WEAK = set()
GLASS_LINES = {"OB-I-PART-GLS", "I-PART-GLSS"}                    # (I_PAR_PA_IN_GL: a line inside the solid outlines, not a wall)
HEIGHT = {"wall": 2.4, "solid": 2.4, "glass": 2.4}                # one cut height (the walls left in the fit-out are partitions
                                                                   # by now: the core and the facade stay the model's)
FACADE, EDGE, NEAR, RES, THICK = 800.0, 250.0, 150.0, 25.0, 450.0
WALL_W = 350.0                                                     # a region between face lines this narrow on average is a wall (mm)
FILL_W = 300.0                                                     # a closed outline this wide on average is a wall's body (mm)
JOIN = 80.0                                                        # two outlines of one wall, closed into one (mm)
DOOR_NEAR = 300.0                                                  # a model piece this near the plan's door lines is that door (mm)
OPEN = 60.0                                                        # a face line's strip is 110 mm: opened away
GLASS_THICK = 300.0                                                # glass: its frame lines at most 250 mm apart
GLASS_WINS = 150.0                                                 # a glass line this near a solid outline is in that wall (mm)


def b64(s, dt): return np.frombuffer(base64.b64decode(s), dtype=dt)


DOOR = __import__("re").compile(r"DOOR|_DOR_|DOR-", __import__("re").I)


def plan_base_lines(root):
    """the deck's floor plan as it draws (data/plan-base.js, its "base" group walked as assets/js/plan-canvas.js walks it: an
    insert on a frozen layer and anything on an off layer left out), in the deck's plan frame: [(layer, kind, points)],
    kind "s" a line, "f" a fill (30 Oct: "the outlines of the nested blocks are causing conflicts": the drawing's hidden
    blocks carried walls the floor plan doesn't show)"""
    import json, os
    s = open(os.path.join(root, "data", "plan-base.js"), encoding="utf-8").read(); PB = json.loads(s[s.index("window.PLAN_BASE = ") + 19:].strip().rstrip(";"))
    ox, oy = PB["origin"]; L = PB["layers"]; out = []
    lay = lambda l, ctx: ctx if l in ("", "0") else l
    for blk in PB["blocks"]:
        if blk["group"] != "base": continue
        Dd = blk["data"]; defs = Dd["defs"]
        def walk(di, M, ctx):
            d = defs[di]; k = 10 ** (-d["q"]); a, b, c, e, f, g = M
            for l, col, lt, lw, kind, items in d["runs"]:
                st = lay(l, ctx)
                if kind == "i":
                    if L.get(st, {}).get("frozen"): continue
                    for ci, ca, cb, cc, cd, ce, cf in items:
                        walk(ci, [a * ca + c * cb, b * ca + e * cb, a * cc + c * cd, b * cc + e * cd, a * ce + c * cf + f, b * ce + e * cf + g], st)
                    continue
                if kind == "t" or L.get(st, {}).get("off") or L.get(st, {}).get("frozen"): continue
                for it in items:
                    for arr in (it if kind == "f" else [it]):
                        x, y = arr[0], arr[1]; pts = []
                        for i in range(0, len(arr), 2):
                            if i: x += arr[i]; y += arr[i + 1]
                            X, Y = x * k, y * k; pts.append((a * X + c * Y + f - ox, oy - (b * X + e * Y + g)))
                        out.append((st, "f" if kind == "f" else "s", pts))
        walk(Dd["root"], Dd["place"]["m"], lay(Dd["place"]["spec"][0], "0"))
    return out


def plan_bodies(lines, pt):
    """the floor plan's wall bodies by type, in the slide's frame (pt maps the plan's mm onto the model's). The walls and solid
    partitions are the floor plan's own regions between their face lines: every line of those layers noded into one network,
    the plan cut into the faces it bounds, and the narrow ones kept (WALL_W mm across at most, on average): a wall's body
    between its two faces, a thick one whole, a room never, a stray line never (30 Oct: "also there are overlapps in these
    places": hollow 300 mm walls, a line through a room's table). Glass from its own lines (widened 30 mm a side), less the
    walls and solid partitions and wherever a solid face runs within GLASS_WINS mm"""
    from shapely.ops import polygonize
    W_, S_, G_ = [], [], []
    for L, kind, raw in lines:
        q = [pt(x, y) for x, y in raw]
        if len(q) < 2: continue
        ring = q + [q[0]] if kind == "f" and math.dist(q[0], q[-1]) > 1 else q
        if L in WALL_FILLS or L in WALL_LINES: W_.append(LineString(ring))
        elif L in SOLID_LINES or L in SOLID_FILLS: S_.append(LineString(ring))
        elif L in GLASS_LINES and kind != "f": G_.append(LineString(q).buffer(30, cap_style=2, join_style=2))
    def bodies(ls):
        if not ls: return Polygon()
        net = unary_union(ls)                                        # noded where lines cross
        keep = [g for g in polygonize(net) if g.area > 1e4 and 2 * g.area / max(g.length, 1) <= WALL_W]
        return unary_union(keep).buffer(5, join_style=2).buffer(-5, join_style=2) if keep else Polygon()
    def strips(ls):                                                  # face pairs left open at their ends: each line widened 55 mm
        if not ls: return Polygon()            # a side, a pair's two strips joined (gaps under 2 x JOIN), lone strips opened away
        g = unary_union([l.buffer(55, cap_style=2, join_style=2) for l in ls]).buffer(JOIN, join_style=2).buffer(-JOIN, join_style=2)
        return g.buffer(-OPEN, join_style=2).buffer(OPEN, join_style=2).intersection(g)
    wall = bodies(W_).union(strips(W_))
    solid = bodies(S_ + W_).union(strips(S_)).difference(wall)        # (a partition's faces may close on a wall's)
    glass = unary_union(G_).buffer(10, join_style=2).buffer(-10, join_style=2).difference(wall.union(solid.buffer(GLASS_WINS, join_style=2))) if G_ else Polygon()
    only = lambda g: unary_union([q for q in getattr(g, "geoms", [g]) if isinstance(q, Polygon)] or [Polygon()])
    return {"wall": only(wall), "solid": only(solid), "glass": only(glass)}


def model_pieces(S, CX, CY):
    """the model's walls and glass as pieces: {ty, pts (plan mm, its tall faces' middles), h, part|unit}"""
    out = []
    units = [b64(u["m"], np.float32).reshape(-1, 12) for u in S["units"]]
    KIND = {"wall": "solid", "top": "solid", "hard": "solid", "mass": "core", "glass": "glass", "mullion": "glass"}
    FURN_K = {"wood", "soft"}                                           # (a component with these is furniture: kept whole)
    seen_units = {}
    for pi, p in enumerate(S["parts"]):
        if p["lv"] == 2 or (p["k"] not in KIND and not (p["u"] >= 0 and p["k"] in FURN_K)): continue
        q = b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3); lo, hi = np.array(p["lo"]), np.array(p["hi"]); v = lo + (q + 32768) / 65535 * (hi - lo)
        idx = b64(p["i"], np.uint32 if p.get("i32") else np.uint16).reshape(-1, 3).astype(np.int64)
        if p["u"] >= 0:                                              # a component: one piece per placement (its parts together)
            for i, m in enumerate(units[p["u"]]):
                vv = v @ np.array([[m[0], m[3], m[6]], [m[1], m[4], m[7]], [m[2], m[5], m[8]]]).T + m[9:12]
                key = (p["u"], i); T3 = vv[idx]
                pc = seen_units.setdefault(key, {"ty": None, "tris": [], "unit": key, "kind": set()}); pc["kind"].add(p["k"])
                pc["tris"].append(T3); kk = KIND.get(p["k"], "solid"); pc["ty"] = "glass" if kk == "glass" or pc["ty"] == "glass" else (pc["ty"] or kk)
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
        Tt = T[tall]
        if len(Tt):                                                  # each tall face on plan: its two farthest corners
            xz = Tt[:, :, [0, 2]] * 1000 + (CX, CY); d = [np.linalg.norm(xz[:, a] - xz[:, b], axis=1) for a, b in ((0, 1), (1, 2), (0, 2))]
            k = np.argmax(np.stack(d, 1), 1); pair = np.array([(0, 1), (1, 2), (0, 2)])[k]
            pc["segs"] = np.stack([xz[np.arange(len(xz)), pair[:, 0]], xz[np.arange(len(xz)), pair[:, 1]]], 1)
        else: pc["segs"] = np.zeros((0, 2, 2))
        del pc["T"]
    return out


def raster(geom, box, res=RES):
    x0, y0, x1, y1 = box; W, H = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or not hasattr(g, "exterior"): continue
        d.polygon([((x - x0) / res, (y - y0) / res) for x, y in g.exterior.coords], fill=255)
        for h in g.interiors: d.polygon([((x - x0) / res, (y - y0) / res) for x, y in h.coords], fill=0)
    return np.asarray(im) > 0


def rebuild(S, lines, pt, slab, CX, CY, log):
    bodies = plan_bodies(lines, pt)
    doors = unary_union([LineString([pt(x, y) for x, y in q]).buffer(DOOR_NEAR) for L, k, q in lines if DOOR.search(L) and len(q) > 1])
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
    drop, hide = {}, []; stats = {"gone": 0, "stays": 0, "doors": 0}; at_door = prep(doors)
    on_wall = prep(unary_union([bodies["wall"], bodies["solid"], bodies["glass"]]).buffer(40))
    for pc in pieces:
        pts = pc["pts"]
        if pc["ty"] == "core" or not len(pts): stats["stays"] += 1; continue
        smp = pts[:: max(1, len(pts) // 16)]
        at_facade = np.mean([not facade.contains(Point(x, y)) for x, y in smp]) > 0.5
        at_core = np.mean([near_core.contains(Point(x, y)) for x, y in smp]) > 0.5
        bx = pc["box"]; column = bx[2] - bx[0] < 1500 and bx[3] - bx[1] < 1500 and pc["h"] > 3.0
        thin = min(bx[2] - bx[0], bx[3] - bx[1]) <= 150 and pc["h"] > 1.8    # a full-height panel: a wall's piece
        loose = pc["kind"] <= {"hard"} and along(pts) < 0.5 and not thin    # a cabinet, a screen: not a wall
        pod = bool(pc["kind"] & {"wood", "soft"})                           # a phone booth: furniture (30 Oct: "what happened to the phone booth")
        # the model's door where the plan has one, in an opening of the extruded walls (30 Oct: "use the sketchup as referece for
        # door", then "skp door and your extrusion doors are overlapping": a panel on an extruded wall is not the door)
        door = np.mean([at_door.contains(Point(x, y)) for x, y in smp]) > 0.5 and np.mean([on_wall.contains(Point(x, y)) for x, y in smp]) < 0.3
        if at_facade or at_core or column or loose or pod or door: stats["stays"] += 1; stats["doors"] += door; continue
        stats["gone"] += 1; pc["gone"] = True
        if "unit" in pc: hide.append([int(pc["unit"][0]), int(pc["unit"][1])])
        else:
            t = np.sort(pc["tris"]); br = np.nonzero(np.diff(t) > 1)[0]
            starts = np.r_[t[0], t[br + 1]]; ends = np.r_[t[br], t[-1]]
            drop.setdefault(str(pc["part"]), []).extend([[int(a), int(b) + 1] for a, b in zip(starts, ends)])
    log(f"model fit-out walls: {stats['gone']} gone; {stats['stays']} pieces stay (core, facade, columns, cabinets, low pieces), {stats['doors']} of them doors")
    zone = slabp.buffer(-EDGE).difference(core)
    walls = {}
    for ty, body in bodies.items():
        add = body.intersection(zone)
        polys = [g for g in getattr(add, "geoms", [add]) if isinstance(g, Polygon) and g.area > 4e4 and g.length > 1200 and 2 * g.area / g.length < (GLASS_THICK if ty == "glass" else THICK)]
        walls[ty] = [[[[round(x), round(y)] for x, y in g.simplify(10).exterior.coords[:-1]]] +
                     [[[round(x), round(y)] for x, y in h.coords[:-1]] for h in g.interiors] for g in polys]
        log(f"  {ty}: {len(polys)} pieces, {sum(g.area for g in polys) / 1e6:.1f} m2, to {HEIGHT[ty]} m")
    return {"walls": walls, "heights": HEIGHT, "drop": drop, "hide": hide, "solid": bodies["solid"].union(bodies["wall"]),
            "glass": bodies["glass"], "pieces": pieces, "box": box}
