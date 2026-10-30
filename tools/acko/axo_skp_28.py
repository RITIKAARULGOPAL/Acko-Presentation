"""The SketchUp model's furniture brought up to the 28.10 plan in the areas that drawing set marks as changed (Ritika, 30 Oct:
"this entire portion is wrong.. not as per the latest plan", then "Rebuild from 28.10", the café as basePlan.dxf has it: "Café
tables", not training room.dxf's townhall rows).

Usage:  python -I tools/acko/axo_skp_28.py "<28.10 folder with basePlan.dxf and changes.dxf>"
        (after tools/acko/axo_skp.py: it adds the key "changes" to data/axo-skp.js, which that tool's rebuild drops)

  frame   basePlan.dxf's A-WALL lines matched onto AXO_DXF's walls (tools/acko/wayday_marks.register): the slide's plan frame;
          then its walls and partitions onto the SketchUp model's own (they sit a little off AXO_DXF's: 0.3, 0.2 m on 28.10)
  areas   changes.dxf's outlines (plan mm, y down): in them the model's furniture goes (data/axo-skp.js stays as built; the
          loader, assets/js/axo-skp.js, leaves out what is in an area) and the 28.10 furniture comes in
  pieces  every furniture-layer block the plan places in an area, a group of them taken apart (a block over 6 m); each drawn
          with one of the model's own components (a plain table, TABLES, as [x, y, w, d, turn] for the loader to draw: the
          model's long tables are booths): its own where the model has a component of that name (Traning room seating,
          SE_CF_04_0900_01, SE_CF_04_1200X0750_01, es), else the nearest kind (SUBST), scaled on plan to the block's size; turned
          to whichever quarter of the block's rotation lays the component's footprint best on the block's lines (or as TURN says)
  seats   the chairs of the café's sets and of the long tables (the blocks' own chairs), facing their table; people for them as
          PEOPLE.sit has them ([x, y, a (centiradians), h]); the slide drops its people in the areas and takes these
Writes "changes": {source, areas, place: [{u, m (12 floats, as the units' m)}], seats} into data/axo-skp.js and
tools/_work/axo-skp-28/check.png (the pieces' lines, red, over the components' footprints, grey).
"""
import argparse, base64, json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axo_skp
import axo_skp_28_walls as WALLS28
import dxf_read as D
import wayday_marks

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "axo-skp-28")
FURN = {"OB-I-FURN-MFUR", "OB_Furniture", "OB-I-FURN-LFUR", "AC_WS_TYPE03", "AC_WS_TYPE04", "I-FUR INT", "N-FURN-LOOSE FURNITURE",
        "Furniture_UC", "AVA-FURNITURE", "I-FURN", "N-FURN-BOUGHT", "A-SYM-FURN", "I-CHAIR", "AI-FURN-HTCH"}
# the 28.10 blocks the model has no component for: the component (by name, without its "#n") drawn in its place
SUBST = {"Chair_Cafe-Generic - CH-23-V289": "*U734", "chair-flat9": "*U734", "*U738": "*U734", "*U1159": "*U734",
         "Bench - Day Dinning-V295": "CoalesseViccarbe_Common_180L",
         "*U834": "SE_CF_04_0900_", "CH_CA_LO_01": "rhrt", "zw$5B81-flat-1": "rhrt", "ferfer": "rhrt", "fvtb": "rhrt",
         "rgr": "A$C3BB14C"}
# by unit id where the model's name is empty or shared: a stool (0.45 m) for the counter's stools, a table (2.94 x 1.35 m) for the
# the 2.6 m table and chairs (*U#69) for the meeting table, a light chair for the loose chairs
SUBST_ID = {"A$C1AF9623F": 10, "ratghag": 54, "Chair_Cafe-Generic - CH-23-V289": 36, "chair-flat9": 36, "*U738": 36, "*U1159": 36}
CHAIRS = ("CH_CF_PC_01", "Chair_Cafe-Generic - CH-23-V289", "chair-flat9", "*U738", "*U1159", "CH_MR_TA_01", "chair",
          "A$C1AF9623F", "Bench - Day Dinning-V295")
SETS = ("SE_CF_04_0900_01", "SE_CF_04_1200X0750_01", "es", "*U834", "ratghag")
SEAT_H = {"A$C1AF9623F": 650}
# the drawing's walls and partitions (the frame's fine fit onto the model's own)
WALLS = {"A-WALL", "I-PART-GYP-100MM", "I-PART-GYP", "OB-I-PART-GYP", "OB-I-PART-GLS", "I_PAR_PA_IN_GL", "I-PART-GLSS", "SKV_GLASS PARTITION"}
TABLES = ("zw$3543",)                                             # plain tables: the model has none, so the loader draws them
# a component whose front its footprint can't tell (a chair): turned by the block's rotation plus this, as all the model's own
# placements of it are (30 Oct: "the training room chairs are wrong"; the model's 42 training chairs: the block's turn + 180)
TURN = {"Traning room seating": 180}                                      # a stool's seat (mm); the rest sit at chair height (0)


def log(*a): print(*a, flush=True)


def inring(p, r):
    x, y = p; c = False
    for i in range(len(r)):
        (x1, y1), (x2, y2) = r[i], r[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c


def b64(s, dt): return np.frombuffer(base64.b64decode(s), dtype=dt)


def unit_shapes(S):
    """per component: its fine parts' triangles in its own frame (x, z, top y), its box"""
    out = {}
    for p in S["parts"]:
        if p["u"] < 0 or p["lv"] == 2: continue
        q = b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3)
        lo, hi = np.array(p["lo"]), np.array(p["hi"]); v = lo + (q + 32768) / 65535 * (hi - lo)
        idx = b64(p["i"], np.uint32 if p.get("i32") else np.uint16).reshape(-1, 3)
        u = out.setdefault(p["u"], {"tri": [], "lo": np.full(3, 1e9), "hi": np.full(3, -1e9), "kinds": set()})
        u["tri"].append(v[idx]); u["lo"] = np.minimum(u["lo"], v.min(0)); u["hi"] = np.maximum(u["hi"], v.max(0)); u["kinds"].add(p["k"])
    for u in out.values(): u["tri"] = np.concatenate(u["tri"])
    return out


def read_plan(folder, off):
    """the change areas and the furniture pieces in them (plan mm, y down)"""
    def pt(x, y): return [x + off[0], -y + off[1]]
    cb, cm = D.read(os.path.join(folder, "changes.dxf"))
    areas = []
    D.walk(cb, cm, lambda e, m, L, p: areas.extend([[pt(x, y) for x, y in D.tf(m, r)] for r in e.get("p", [])]))
    blocks, model = D.read(os.path.join(folder, "basePlan.dxf"))
    top = model[0]; m0 = D.insert_m(blocks, top)
    pieces = []

    def lines(ents, m, layer, keep=None):
        rings, kids = [], []
        def fn(e, mm, L, path):
            if L in FURN and e["t"] not in ("TEXT", "MTEXT"):
                for r in e.get("p", []): rings.append([pt(x, y) for x, y in D.tf(mm, r)])
        def enter(e, mm, L, path):
            if keep is not None and len(path) == 0: kids.append((e, mm, L))
        D.walk(blocks, ents, fn, m, layer, enter=enter)
        return rings, kids

    def visit(e, m, layer, depth):
        b = blocks.get(e["n"])
        if b is None: return
        mm = D.mul(m, D.insert_m(blocks, e)); L = e["l"] if e["l"] != "0" else layer
        rings, kids = lines(b["ents"], mm, L, keep=True)
        if not rings: return
        P = np.array([p for r in rings for p in r]); c = (P.min(0) + P.max(0)) / 2; w, h = P.max(0) - P.min(0)
        if w > 6000 or h > 6000:                                     # a group: its own blocks
            if depth < 4:
                for s in b["ents"]:
                    if s["t"] == "INSERT": visit(s, mm, L, depth + 1)
            return
        if not any(inring(c, a) for a in areas): return
        a_, b_, c_, d_, _, _ = mm
        chairs = []
        for k, km, kl in kids:                                       # its own chairs, for the seats
            if k["n"] in CHAIRS or "chair" in k["n"].lower():
                kr, _ = lines(blocks[k["n"]]["ents"], km, kl)
                if kr: Q = np.array([p for r in kr for p in r]); chairs.append(((Q.min(0) + Q.max(0)) / 2).tolist())
        pieces.append({"n": e["n"], "rings": rings, "c": c.tolist(), "rot": math.atan2(-b_, a_), "chairs": chairs})

    for e in blocks[top["n"]]["ents"]:
        if e["t"] == "INSERT": visit(e, m0, top["l"], 1)
    walls = []
    def fn(e, m, L, p):
        if L in WALLS and e["t"] != "HATCH":
            for r in e.get("p", []): walls.append([(x, -y) for x, y in D.tf(m, r)])
    D.walk(blocks, model, fn)
    return areas, pieces, walls, (blocks, model)


def onto_model(S, walls, off, CX, CY, reach=1500, res=50.0):
    """the small shift (plan mm, within reach) that lays the drawing's walls and partitions on the model's own walls and glass
    (their faces over 1.8 m, top view), and the share of the lines on them after and before"""
    from scipy import ndimage
    P = np.array([p for r in walls for p in r], float) + off; x0, y0 = P.min(0) - reach - 500; x1, y1 = P.max(0) + reach + 500
    W, H = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    tgt = Image.new("L", (W, H), 0); dt = ImageDraw.Draw(tgt)
    units = [b64(u["m"], np.float32).reshape(-1, 12) for u in S["units"]]
    for p in S["parts"]:
        if p["lv"] == 2 or p["k"] not in ("wall", "top", "mass", "hard", "glass", "mullion"): continue
        q = b64(p["p"], np.int16).astype(np.float64).reshape(-1, 3); lo, hi = np.array(p["lo"]), np.array(p["hi"]); v = lo + (q + 32768) / 65535 * (hi - lo)
        idx = b64(p["i"], np.uint32 if p.get("i32") else np.uint16).reshape(-1, 3)
        for m in (units[p["u"]] if p["u"] >= 0 else [None]):
            vv = v if m is None else v @ np.array([[m[0], m[3], m[6]], [m[1], m[4], m[7]], [m[2], m[5], m[8]]]).T + m[9:12]
            T3 = vv[idx]; keep = (T3[:, :, 1].max(1) > 1.8) & (np.ptp(T3[:, :, 1], 1) > 0.3)
            for t in T3[keep]: dt.polygon([((a[0] * 1000 + CX - x0) / res, (a[2] * 1000 + CY - y0) / res) for a in t], fill=255, outline=255)
    tgt = ndimage.binary_dilation(np.asarray(tgt) > 0, iterations=3).astype(np.float32)
    src = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(src)
    for r in walls:
        q = [((x + off[0] - x0) / res, (y + off[1] - y0) / res) for x, y in r]
        if len(q) > 1: ds.line(q, fill=255)
    a = np.asarray(src, np.float32) / 255
    F = np.fft.irfft2(np.fft.rfft2(tgt) * np.conj(np.fft.rfft2(a)), s=tgt.shape); win = int(reach / res); best = (-1.0, 0, 0)
    for dy in range(-win, win + 1):
        for dx in range(-win, win + 1):
            if F[dy % H, dx % W] > best[0]: best = (F[dy % H, dx % W], dx, dy)
    return np.array([best[1], best[2]], float) * res, best[0] / max(1, a.sum()), float((a * tgt).sum() / max(1, a.sum()))


def fit(piece, U, uid, scale, CX, CY, turn=None):
    """the component's placement for a piece: turned to the quarter of the block's rotation whose footprint lies best on the
    block's lines, centred on them; scaled on plan to the block's size when it stands in for another block"""
    u = U[uid]; lc = (u["lo"] + u["hi"]) / 2; ext = (u["hi"] - u["lo"])[[0, 2]]
    P = np.array([p for r in piece["rings"] for p in r], float) / 1000.0
    best = None
    for k in (range(4) if turn is None else [None]):
        al = piece["rot"] + (k * math.pi / 2 if turn is None else math.radians(turn)); ca, sa = math.cos(al), math.sin(al)
        loc = (P - P.mean(0)) @ np.array([[ca, -sa], [sa, ca]])                      # the lines in the turned frame
        lo, hi = loc.min(0), loc.max(0); size = hi - lo; cl = (lo + hi) / 2
        sx, sz = (size / np.maximum(ext, 1e-3)) if scale else (1.0, 1.0)
        centre = P.mean(0) + np.array([[ca, -sa], [sa, ca]]) @ cl
        # the footprint's triangles on plan, rasterised against the lines (5 cm)
        T3 = u["tri"]; T3 = T3[T3[:, :, 1].max(1) > 0.05]
        tx = (T3[:, :, 0] - lc[0]) * sx; tz = (T3[:, :, 2] - lc[2]) * sz
        wx = centre[0] + tx * ca - tz * sa; wz = centre[1] + tx * sa + tz * ca
        x0, z0 = P.min(0) - 0.3; W_, H_ = (((P.max(0) + 0.3) - (x0, z0)) / 0.05).astype(int) + 1
        a = Image.new("L", (W_, H_), 0); da = ImageDraw.Draw(a)
        for i in range(len(wx)): da.polygon([((wx[i, j] - x0) / 0.05, (wz[i, j] - z0) / 0.05) for j in range(3)], fill=255)
        b = Image.new("L", (W_, H_), 0); db = ImageDraw.Draw(b)
        for r in piece["rings"]:
            q = [((x / 1000 - x0) / 0.05, (y / 1000 - z0) / 0.05) for x, y in r]
            if len(q) > 1: db.line(q, fill=255, width=2)
        A_, B_ = np.asarray(a) > 0, np.asarray(b) > 0
        score = (A_ & B_).sum() / max(1, B_.sum())
        if best is None or score > best[0]: best = (score, al, sx, sz, centre)
    _, al, sx, sz, centre = best
    ca, sa = math.cos(al), math.sin(al)
    c0 = np.array([sx * ca, 0, sx * sa]); c1 = np.array([0, 1.0, 0]); c2 = np.array([-sz * sa, 0, sz * ca])
    world = np.array([centre[0] - CX / 1000, 0, centre[1] - CY / 1000])
    t = world - (c0 * lc[0] + c2 * lc[2]); t[1] = 0.0
    return [round(float(v), 5) for v in (*c0, *c1, *c2, *t)], best[0]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("folder"); a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    path = os.path.join(ROOT, "data", "axo-skp.js")
    S = axo_skp.read_js(path, "AXO_SKP"); A = axo_skp.read_js(os.path.join(ROOT, "data", "axo-dxf.js"), "AXO_DXF")
    xs = [q[0] for q in A["slab"]]; ys = [q[1] for q in A["slab"]]; CX, CY = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    # the frame: basePlan's walls onto AXO_DXF's
    _, _, walls, _ = read_plan(a.folder, (0.0, 0.0))
    aw = [w for w in walls]                                          # (all its wall layers; the coarse match uses them too)
    off, share = wayday_marks.register(aw, A)
    log(f"frame: shift {[round(v) for v in off]} mm ({share:.0%} of basePlan's walls on AXO_DXF's within 10 cm)")
    d, after, before = onto_model(S, walls, off, CX, CY); off = off + d
    log(f"  then onto the SketchUp model's own walls: {[round(v) for v in d]} mm more ({before:.0%} -> {after:.0%} of the lines on them)")
    areas, pieces, _, (blocks, model) = read_plan(a.folder, (float(off[0]), float(off[1])))
    WR = WALLS28.rebuild(S, blocks, model, lambda x, y: (x + off[0], -y + off[1]), A["slab"], CX, CY, log)
    log(f"{len(areas)} change areas, {len(pieces)} furniture blocks in them")
    U = unit_shapes(S); names = {i: (u.get("name") or "").rsplit("#", 1)[0] for i, u in enumerate(S["units"])}
    byname = {}
    for i, n in names.items():
        if n and i in U: byname.setdefault(n, i)
    place, seats, report = [], [], {}
    tables = []
    for pc in pieces:
        n = pc["n"]
        if n in TABLES:                                              # its top's middle, size and turn (plan mm, degrees)
            P = np.array([p for r in pc["rings"] for p in r], float); al = pc["rot"]; ca, sa = math.cos(al), math.sin(al)
            loc = (P - P.mean(0)) @ np.array([[ca, -sa], [sa, ca]]); lo, hi = loc.min(0), loc.max(0)
            c = P.mean(0) + np.array([[ca, -sa], [sa, ca]]) @ ((lo + hi) / 2)
            tables.append([round(c[0]), round(c[1]), round(hi[0] - lo[0]), round(hi[1] - lo[1]), round(math.degrees(al), 2)])
            report.setdefault(n, ["(a plain table)", 0])[1] += 1; continue
        own = next((i for nm, i in byname.items() if nm and (n == nm or (n.startswith(nm) and len(nm) > 4))), None)
        uid = own if own is not None else (SUBST_ID.get(n) if n in SUBST_ID else byname.get(SUBST.get(n, "\0")))
        if uid is None: report.setdefault(n, ["-", 0])[1] += 1; continue
        m, score = fit(pc, U, uid, own is None, CX, CY, TURN.get(n))
        place.append({"u": uid, "m": m}); r = report.setdefault(n, [names[uid] or f"u{uid}", 0]); r[1] += 1
        # seats: a set's chairs face its middle; a loose chair or bench faces the nearest set or table within 1.6 m
        if n in SETS:
            for ch in pc["chairs"]:
                seats.append([round(ch[0]), round(ch[1]), round(100 * math.atan2(pc["c"][1] - ch[1], pc["c"][0] - ch[0])), SEAT_H.get(n, 0)])
        elif n in CHAIRS or n in SUBST and SUBST[n] == "*U734" or n in ("Bench - Day Dinning-V295", "A$C1AF9623F"):
            tabs = [q for q in pieces if q["n"] in SETS + ("zw$3543",)]
            near = min(tabs, key=lambda q: math.dist(q["c"], pc["c"])) if tabs else None
            if near and math.dist(near["c"], pc["c"]) < 1600:
                c = pc["c"]
                if n == "Bench - Day Dinning-V295":                  # a bench: two along it, facing the table
                    P = np.array([p for r in pc["rings"] for p in r]); w, h = P.max(0) - P.min(0)
                    along = np.array([1.0, 0]) * w if w > h else np.array([0, 1.0]) * h
                    for f in (-0.25, 0.25):
                        q = np.array(c) + along * f; seats.append([round(q[0]), round(q[1]), round(100 * math.atan2(near["c"][1] - q[1], near["c"][0] - q[0])), 0])
                else:
                    seats.append([round(c[0]), round(c[1]), round(100 * math.atan2(near["c"][1] - c[1], near["c"][0] - c[0])), SEAT_H.get(n, 0)])
    for n, (u, k) in sorted(report.items(), key=lambda kv: -kv[1][1]): log(f"  {k:4d}  {n[:40]:40s} -> {u}")
    log(f"{len(place)} placements, {len(seats)} seats")
    out = {"source": f"{os.path.basename(a.folder.rstrip('/\\'))}: basePlan.dxf in changes.dxf's areas", "areas": [[[round(x), round(y)] for x, y in r] for r in areas],
           "place": place, "tables": tables, "seats": seats, "walls": WR["walls"], "heights": WR["heights"], "drop": WR["drop"], "hide": WR["hide"]}
    # into data/axo-skp.js as its last key (the rest of the file as built)
    s = open(path, encoding="utf-8").read(); body = s.rstrip().rstrip(";")
    cut = body.rfind(',"changes":')
    if cut > 0: body = body[:cut] + "}"
    assert body.endswith("}")
    s2 = body[:-1] + ',"changes":' + json.dumps(out, separators=(",", ":")) + "};\n"
    open(path, "w", encoding="utf-8", newline="\n").write(s2)
    log(f"data/axo-skp.js: {len(s2) / 1e6:.2f} MB")
    # the check picture: the pieces' lines (red) over the components' footprints as placed (grey), the areas (blue)
    allp = np.array([p for r in areas for p in r]); x0, y0 = allp.min(0) - 1000; x1, y1 = allp.max(0) + 1000; k = 0.04
    im = Image.new("RGB", (int((x1 - x0) * k), int((y1 - y0) * k)), "white"); dr = ImageDraw.Draw(im)
    for pl in place:
        m = pl["m"]; u = U[pl["u"]]; T3 = u["tri"][u["tri"][:, :, 1].max(1) > 0.05]
        wx = m[0] * T3[:, :, 0] + m[6] * T3[:, :, 2] + m[9]; wz = m[2] * T3[:, :, 0] + m[8] * T3[:, :, 2] + m[11]
        for i in range(len(wx)): dr.polygon([((wx[i, j] * 1000 + CX - x0) * k, (wz[i, j] * 1000 + CY - y0) * k) for j in range(3)], fill=(190, 190, 190))
    for pc in pieces:
        for r in pc["rings"]: dr.line([((x - x0) * k, (y - y0) * k) for x, y in r], fill=(220, 30, 30), width=1)
    for s_ in seats: dr.ellipse([(s_[0] - x0) * k - 3, (s_[1] - y0) * k - 3, (s_[0] - x0) * k + 3, (s_[1] - y0) * k + 3], outline=(0, 120, 0))
    for r in areas: dr.line([((x - x0) * k, (y - y0) * k) for x, y in r] + [((r[0][0] - x0) * k, (r[0][1] - y0) * k)], fill=(0, 70, 255), width=2)
    im.save(os.path.join(WORK, "check.png")); log("tools/_work/axo-skp-28/check.png")
    # the walls' check, in strips west to east: the 28.10 bodies (solid grey, glass light blue), the model's walls kept (green)
    # and gone (red), the walls added (outlined: solid black, glass blue)
    x0, y0, x1, y1 = WR["box"]; k = 0.05; im = Image.new("RGB", (int((x1 - x0) * k), int((y1 - y0) * k)), "white"); dr = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * k, (y - y0) * k)
    for g, c in ((WR["solid"], (200, 200, 200)), (WR["glass"], (190, 220, 250))):
        for q in getattr(g, "geoms", [g]):
            if hasattr(q, "exterior") and not q.is_empty: dr.polygon([P(*xy) for xy in q.exterior.coords], fill=c)
    for pc in WR["pieces"]:
        if not len(pc["pts"]) or pc["ty"] == "core": continue
        col = (220, 30, 30) if pc.get("gone") else (40, 160, 60)
        for x, y in pc["pts"][::3]: dr.point(P(x, y), fill=col)
    for ty, col in (("wall", (90, 0, 0)), ("solid", (0, 0, 0)), ("glass", (30, 90, 230))):
        for poly in WR["walls"][ty]:
            for r in poly: dr.line([P(*xy) for xy in r] + [P(*r[0])], fill=col, width=1)
    n = 4; w = im.size[0] // n + 1
    for i in range(n): im.crop((i * w, 0, min(im.size[0], (i + 1) * w), im.size[1])).save(os.path.join(WORK, f"walls-{i}.png"))
    log("tools/_work/axo-skp-28/walls-0..3.png")


if __name__ == "__main__":
    main()
