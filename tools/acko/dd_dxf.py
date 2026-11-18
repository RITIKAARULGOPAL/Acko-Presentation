# Site due diligence zones from Ritika's DXF (18 Nov, "ACKO_BOUNDARY_site due diligence.dxf": "ill share a dxf for site due diligence.
# rework the slide"): reads the AC_* polygons, maps them onto the deck's plan (plan mm), checks the five kinds the deck already has
# against data/plan-dxf.js (overlays.dd), and writes the list into slides/s-site-dd.html between /*DD:START*/ and /*DD:END*/.
#   python tools/acko/dd_dxf.py "<path to the .dxf>" [slides/s-site-dd.html]
# The DXF is ~150 MB: streamed once (group code / value pairs); the polygons sit in the block the model-space INSERT places.
# Layers: AC_FIRE_EXIT_STAIRCASE stair · AC_AHU ahu · AC_WASHROOM wash · AC_STRENGTHEN_SLAB slab · AC_LIFT_LOBBY lift ·
# AC_OUT_OF_SCOPE oos (new). AC_QUICK_SPRINT (the frame) and AC_ATRIUM (an insert) carry no zone of their own.
# The base (18 Nov, Ritika: "only have what's there in the DXF"): the DXF's own linework, not the shared plan's: its architectural layers
# (BASE below) flattened through every nested INSERT (rotation, scale, mirror) into plan mm, simplified (20 mm grid, runs under 60 mm and
# duplicates dropped) and written as SVG path strings per weight group between /*BASE:START*/ and /*BASE:END*/. The curtain wall (A-GENM,
# ~400,000 pieces) is left out: the slide's glazing line draws the facade.
import sys, re, json, os
KIND = {"AC_FIRE_EXIT_STAIRCASE": "stair", "AC_AHU": "ahu", "AC_WASHROOM": "wash", "AC_STRENGTHEN_SLAB": "slab", "AC_LIFT_LOBBY": "lift", "AC_OUT_OF_SCOPE": "oos"}
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "slides/s-site-dd.html"

def polylines(path):
    ent = None; sect = None; found = []
    def done():
        nonlocal ent
        if ent and ent["t"] == "LWPOLYLINE" and ent.get("l") in KIND and len(ent["pts"]) >= 3: found.append(ent)
        ent = None
    with open(path, encoding="latin-1", errors="replace") as f:
        while True:
            c = f.readline()
            if not c: break
            v = f.readline().rstrip("\r\n").strip(); c = c.strip()
            if c == "0":
                done()
                if v not in ("SECTION", "ENDSEC", "ENDBLK"): ent = {"t": v, "pts": [], "bulge": 0}
            elif c == "2" and ent is None and v in ("HEADER", "CLASSES", "TABLES", "BLOCKS", "ENTITIES", "OBJECTS"): sect = v
            elif ent is not None and ent["t"] == "LWPOLYLINE":
                if c == "8": ent["l"] = v
                elif c == "10": ent["pts"].append([float(v), None])
                elif c == "20" and ent["pts"]: ent["pts"][-1][1] = float(v)
                elif c == "42" and float(v) != 0: ent["bulge"] += 1
    done()
    return found

zones = polylines(src)
assert zones, "no AC_ polygons"
assert not any(z["bulge"] for z in zones), "curved segments: not handled"
# the DXF's frame -> the plan's: CAD's y runs up, the plan's down, so x' = x + DX and y' = K - y; matched on the first lift lobby of the
# current data, then checked on every other shape below
P = open("data/plan-dxf.js", encoding="utf-8").read(); P = json.loads(P[P.index("{"):P.rindex("}") + 1])
cur = P["overlays"]["dd"]
def bbox(pts): xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; return (min(xs), min(ys), max(xs), max(ys))
def curbox(d): n = [list(map(float, m)) for m in re.findall(r"(-?[\d.]+) (-?[\d.]+)", d)]; return bbox(n)
lift0 = next(o for o in cur if o["k"] == "lift"); cb = curbox(lift0["d"])
cand = [bbox(z["pts"]) for z in zones if KIND[z["l"]] == "lift"]
best = None
for b in cand:
    dx, dy = cb[0] - b[0], cb[1] + b[3]
    if abs((b[2] - b[0]) - (cb[2] - cb[0])) < 5 and abs((b[3] - b[1]) - (cb[3] - cb[1])) < 5: best = (dx, dy); break
assert best, "no lift lobby matches the plan's"
DX, K = round(best[0]), round(best[1])
print("x shift", DX, "· y flipped about", K)
def d(pts):
    q = [(p[0] + DX, K - p[1]) for p in pts]
    if q[0] == q[-1]: q = q[:-1]
    return "M" + "L".join("%d %d" % (round(x), round(y)) for x, y in q) + "Z"
area = lambda pts: abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2e6
new = [{"k": KIND[z["l"]], "d": d(z["pts"]), "m2": round(area(z["pts"]), 1)} for z in zones]
# the five kinds the deck had: same counts; report any that sit elsewhere in the new drawing (matched on size, then by distance)
moved = []
for k in ("stair", "ahu", "wash", "slab", "lift"):
    a = [curbox(o["d"]) for o in cur if o["k"] == k]; b = [curbox(o["d"]) for o in new if o["k"] == k]   # from the mapped path
    assert len(a) == len(b), (k, len(a), len(b))
    left = list(b)
    for p in a:
        q = min(left, key=lambda q: abs(q[0] - p[0]) + abs(q[1] - p[1]) + abs((q[2] - q[0]) - (p[2] - p[0])) + abs((q[3] - q[1]) - (p[3] - p[1]))); left.remove(q)
        if any(abs(x - y) > 5 for x, y in zip(p, q)): moved.append((k, round(q[0] - p[0]), round(q[1] - p[1]), round((q[2] - q[0]) * (q[3] - q[1]) / 1e6 - (p[2] - p[0]) * (p[3] - p[1]) / 1e6, 1)))
print("moved or changed against the plan's own data (kind, dx mm, dy mm, d bbox m2):", moved or "none")
print("counts:", {k: sum(1 for o in new if o["k"] == k) for k in ("stair", "ahu", "wash", "slab", "lift", "oos")})
print("areas m2:", {k: round(sum(o["m2"] for o in new if o["k"] == k)) for k in ("stair", "ahu", "wash", "slab", "lift", "oos")})
# ---- the base linework
import math, collections
BASE = {"w": ["A-WALL", "S-COLS", "A-FLOR", "A-FLOR-OTLN"], "d": ["A-DOOR", "A-DOOR-FRAM", "A-DOOR-GLAZ", "A-DOOR-OPNG"], "s": ["S-STRS", "S-STRS-MBND"],
        "f": ["G-IMPT", "P-SANR-FIXT", "Q-SPCQ", "A-DETL", "A-DETL-GENF", "A-DETL-THIN"]}
WANT = {L for ls in BASE.values() for L in ls}
Q, MINL = 20, 60
def scan_blocks(path):
    blocks = {}; sect = None; cur = None; ent = None; model = []
    def done():
        nonlocal ent
        if ent and ent["t"] in ("LINE", "ARC", "LWPOLYLINE", "INSERT"): (cur["ents"] if sect == "BLOCKS" and cur is not None else model).append(ent)
        ent = None
    with open(path, encoding="latin-1", errors="replace") as f:
        while True:
            c = f.readline()
            if not c: break
            v = f.readline().rstrip("\r\n").strip(); c = c.strip()
            if c == "0":
                done()
                if v == "BLOCK": cur = {"ents": [], "base": None}; ent = {"t": "BLOCK"}
                elif v == "ENDBLK": cur = None
                elif v in ("SECTION", "ENDSEC"): pass
                else: ent = {"t": v}
            elif c == "2" and ent is None and v in ("HEADER", "CLASSES", "TABLES", "BLOCKS", "ENTITIES", "OBJECTS"): sect = v
            elif ent is not None:
                t = ent["t"]
                if t == "BLOCK":
                    if c == "2": blocks[v] = cur
                    elif c == "10": cur["base"] = [float(v), 0.0]
                    elif c == "20" and cur["base"]: cur["base"][1] = float(v)
                elif c == "8": ent["l"] = v
                elif t == "LINE":
                    if c in ("10", "20", "11", "21"): ent[{"10": "x1", "20": "y1", "11": "x2", "21": "y2"}[c]] = float(v)
                elif t == "ARC":
                    if c in ("10", "20", "40", "50", "51"): ent[{"10": "cx", "20": "cy", "40": "r", "50": "a0", "51": "a1"}[c]] = float(v)
                elif t == "LWPOLYLINE":
                    if c == "10": ent.setdefault("pts", []).append([float(v), 0.0])
                    elif c == "20" and ent.get("pts"): ent["pts"][-1][1] = float(v)
                    elif c == "70": ent["closed"] = int(v) & 1
                elif t == "INSERT":
                    if c == "2": ent["name"] = v
                    elif c in ("10", "20", "41", "42", "50"): ent[{"10": "x", "20": "y", "41": "sx", "42": "sy", "50": "rot"}[c]] = float(v)
    done()
    return blocks, model
def mat(e):
    sx = 1.0 if e.get("sx") is None else e["sx"]; sy = 1.0 if e.get("sy") is None else e["sy"]
    r = math.radians(e.get("rot") or 0.0); c, s_ = math.cos(r), math.sin(r)
    return (c * sx, -s_ * sy, e.get("x", 0.0), s_ * sx, c * sy, e.get("y", 0.0))
def mul(a, b): return (a[0]*b[0]+a[1]*b[3], a[0]*b[1]+a[1]*b[4], a[0]*b[2]+a[1]*b[5]+a[2], a[3]*b[0]+a[4]*b[3], a[3]*b[1]+a[4]*b[4], a[3]*b[2]+a[4]*b[5]+a[5])
def base_lines(path):
    B, model = scan_blocks(path)
    # model space places baseplan, which places base (the architectural drawing, its families nested inside); the zones' block 1RWYW sits at
    # its own insert: one model frame for both. Plan x' = x_model + (DX - z.x), plan y' = (K + z.y) - y_model
    ins = {e["name"]: e for e in model if e["t"] == "INSERT"}
    bp = [e for e in B["baseplan"]["ents"] if e["t"] == "INSERT" and e["name"] == "base"][0]
    MX, MY = ins["baseplan"]["x"] + bp["x"], ins["baseplan"]["y"] + bp["y"]
    z = ins["1RWYW"]; PX = DX - z["x"]; PY = K + z["y"]
    out = collections.defaultdict(list)
    def arc(e):
        a0, a1 = math.radians(e["a0"]), math.radians(e["a1"])
        if a1 <= a0: a1 += 2 * math.pi
        n = max(2, int((a1 - a0) / math.radians(15)) + 1)
        return [(e["cx"] + e["r"] * math.cos(a0 + (a1 - a0) * i / n), e["cy"] + e["r"] * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    def walk(name, M, layer0, depth):
        for e in B[name]["ents"]:
            t = e["t"]; L = e.get("l") if e.get("l") not in (None, "0") else layer0
            if t == "INSERT":
                if e.get("name") in B and depth < 5:
                    nb = B[e["name"]]["base"] or (0, 0)
                    walk(e["name"], mul(M, mul(mat(e), (1, 0, -nb[0], 0, 1, -nb[1]))), L, depth + 1)
                continue
            if L not in WANT: continue
            if t == "LINE" and "x2" in e: P = [(e["x1"], e["y1"]), (e["x2"], e["y2"])]
            elif t == "ARC" and "a0" in e: P = arc(e)
            elif t == "LWPOLYLINE" and e.get("pts"): P = [tuple(q) for q in e["pts"]] + ([tuple(e["pts"][0])] if e.get("closed") else [])
            else: continue
            out[L].append([(M[0]*x + M[1]*y + M[2] + PX, PY - (M[3]*x + M[4]*y + M[5])) for x, y in P])
    walk("base", (1, 0, MX, 0, 1, MY), "0", 0)
    return out
def pack(lines_by_layer, layers):
    seen = set(); parts = []
    for L in layers:
        for P in lines_by_layer.get(L, []):
            q = []
            for x, y in P:
                p = (round(x / Q) * Q, round(y / Q) * Q)
                if not q or p != q[-1]: q.append(p)
            if len(q) < 2 or sum(math.hypot(q[i+1][0]-q[i][0], q[i+1][1]-q[i][1]) for i in range(len(q)-1)) < MINL: continue
            key = tuple(q) if q[0] <= q[-1] else tuple(reversed(q))
            if key in seen: continue
            seen.add(key); parts.append(q)
    txt = []
    for q in parts:
        t = "M%d %d" % q[0]; px, py = q[0]
        for x, y in q[1:]: t += "l%d %d" % (x - px, y - py); px, py = x, y
        txt.append(t)
    return "".join(txt), len(parts)
lines = base_lines(src)
# the base must sit on the plan: its walls inside the plate (plan x 9,000-257,000, y 14,000-50,000)
xs = [p[0] for P in lines["A-WALL"] for p in P]; ys = [p[1] for P in lines["A-WALL"] for p in P]
assert 8000 < min(xs) and max(xs) < 258000 and 14000 < min(ys) and max(ys) < 50000, ("base off the plan", min(xs), max(xs), min(ys), max(ys))
# ---- the glazing (18 Nov, Ritika: "glazing is not aligning to the layout"): the façade as the DXF's own floor edge (A-FLOR), not a hand-drawn path.
# North: the runs of the edge at the north line (none where the cores are); east; south in runs, each notch up to its inner line; the west
# diagonal and the rounded corner. Every piece is taken from the DXF and the whole must close on itself (checked below).
def facade(L):
    segs = [(P[i], P[i + 1]) for P in L["A-FLOR"] for i in range(len(P) - 1) if math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) > 400]
    H = collections.defaultdict(list); V = collections.defaultdict(list)
    for a, b in segs:
        if abs(a[1] - b[1]) < 30: H[round((a[1] + b[1]) / 100) * 50].append(tuple(sorted((a[0], b[0]))))
        elif abs(a[0] - b[0]) < 30: V[round((a[0] + b[0]) / 100) * 50].append(tuple(sorted((a[1], b[1]))))
    def merge(iv, gap=1600):
        iv = sorted(iv); out = [list(iv[0])]
        for lo, hi in iv[1:]:
            if lo <= out[-1][1] + gap: out[-1][1] = max(out[-1][1], hi)
            else: out.append([lo, hi])
        return out
    long_runs = lambda m, n: [(lo, hi) for lo, hi in m if hi - lo > n]
    yn = min(y for y, iv in H.items() if sum(h - l for l, h in merge(iv)) > 40000)           # the north line
    ys = max(y for y, iv in H.items() if sum(h - l for l, h in merge(iv)) > 40000)           # the south line
    xe = max(x for x, iv in V.items() if sum(h - l for l, h in merge(iv)) > 20000)           # the east line
    north = long_runs(merge(H[yn]), 8000); south = long_runs(merge(H[ys]), 10000)
    inner = [y for y in H if ys - 15000 < y < ys - 5000 and sum(h - l for l, h in merge(H[y])) > 20000]; assert len(inner) >= 1, "notch lines"
    yi = min(inner)
    # the rounded corner: the arc polyline at the west end, from the north line down to the diagonal
    arcs = [P for P in L["A-FLOR"] if len(P) >= 8 and min(p[0] for p in P) < 16000]; assert arcs, "corner arc"
    arc = max(arcs, key=len); arc = arc if arc[0][1] < arc[-1][1] else arc[::-1]
    diag = [(a, b) for a, b in segs if abs(a[0] - b[0]) > 30 and abs(a[1] - b[1]) > 30 and math.hypot(b[0] - a[0], b[1] - a[1]) > 20000]; assert diag, "west diagonal"
    d0, d1 = diag[0]; d0, d1 = (d0, d1) if d0[1] < d1[1] else (d1, d0)                        # d0 the north-west end, d1 the south end
    r = lambda q: (round(q[0] / 10) * 10, round(q[1] / 10) * 10)
    south = sorted(south)
    pts = [(north[0][1], yn)] if False else []
    # the main outline: from the first north run's east end, west along the north edge, round the corner, down the diagonal, east along the
    # south edge with its notches, up the east side, west along the last north run
    path = [r((north[0][1], yn)), r((north[0][0], yn))] + [r(q) for q in arc] + [r(d1)]
    for i, (lo, hi) in enumerate(south):
        if i: path += [r((lo, yi)), r((lo, ys))]
        path += [r((hi, ys))] if i == len(south) - 1 else [r((hi, ys)), r((hi, yi))]
    path += [r((xe, ys)), r((xe, yn)), r((north[-1][0], yn))]
    # note: each notch's inner corners come from the DXF's notch verticals; the pieces between runs are the notch itself
    parts = ["M" + "L".join("%d %d" % q for q in path)]
    for lo, hi in north[1:-1][::-1]: parts.append("M%d %dL%d %d" % (hi, yn, lo, yn))
    # the closing check: the south runs meet the notch verticals' x within 40 mm
    for i in range(len(south) - 1):
        gap = (south[i][1], south[i + 1][0]); vx = [x for x in V if abs(x - gap[0]) < 80 or abs(x - gap[1]) < 80]; assert len(vx) >= 2, ("notch verticals", gap)
    assert abs(arc[0][0] - north[0][0]) < 100 and abs(arc[-1][0] - d0[0]) < 100 and abs(arc[-1][1] - d0[1]) < 100, "corner does not meet the north line and the diagonal"
    assert abs(r(d1)[0] - south[0][0]) < 40, "diagonal does not meet the south edge"
    return "".join(parts)
GLAZE_OUT = facade(lines)
print("glazing", len(GLAZE_OUT), "chars; north runs and notches from the DXF's floor edge")
BASE_OUT = {}
for g, ls in BASE.items():
    BASE_OUT[g], n = pack(lines, ls); print("base", g, n, "polylines,", len(BASE_OUT[g]) // 1024, "KB")
html = open(out, encoding="utf-8").read()
a, b = html.index("/*DD:START*/"), html.index("/*DD:END*/")
html = html[:a] + "/*DD:START*/ const DD_DXF = " + json.dumps(new, separators=(",", ":")) + "; " + html[b:]
a, b = html.index("/*BASE:START*/"), html.index("/*BASE:END*/")
html = html[:a] + "/*BASE:START*/ const DD_BASE = " + json.dumps(BASE_OUT, separators=(",", ":")) + "; " + html[b:]
a, b = html.index("/*GLAZE:START*/"), html.index("/*GLAZE:END*/")
html = html[:a] + "/*GLAZE:START*/ const DD_GLAZE = " + json.dumps(GLAZE_OUT) + "; " + html[b:]
open(out, "w", encoding="utf-8", newline="\n").write(html)
print("ok", out, len(new), "zones")
