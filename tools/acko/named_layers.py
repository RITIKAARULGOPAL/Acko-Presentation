"""The plan's spaces, neighbourhoods and workstation types from a drawing whose spaces are drawn on named layers (one AC_*
layer per kind of space, its outlines and hatches; AC_AUTO … AC_TRAVEL the six neighbourhoods; AC_WS_TYPE01–04 the
workstation types as block inserts). Used by plan_dxf.py when the toolkit's rooms.json comes from AC_ layers (the 22.10.26
drawing): no snapping to walls, the drawing says what each space is.

    spaces(tk, labels, colours)        -> [space]   typed by layer, named by the room labels inside, coloured by the legend
    zones(tk, prev_tk, shift)          -> [zone]    "01 · Travel": numbered by overlap with the previous drawing's ak_zone_01–06
    types(tk)                          -> [type]    each AC_WS_TYPE insert matched to its <use> in instanced.svg
    frame_shift(tk, prev_tk)           -> (dx, dy, response)  the previous drawing's world coordinates -> this one's (walls)
"""
import json, os, re, collections
import numpy as np, cv2
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

# the layer -> the deck's type of space
LAYER_TYPE = {
    "BOARD_ROOM": "Boardroom", "CAFETERIA": "Cafeteria", "COFFEE_CORNER": "Coffee corner", "COLLAB": "Collab",
    "COLLAB_HUDDLE": "Collaboration huddle", "CORRIDOR": "Corridor", "DEPARTMENTAL_ROOMS": "Departmental room", "ENTRY": "Entry",
    "EXECUTIVE_CORNER_CABIN": "Executive corner cabin", "HUB_ROOM": "Hub room", "LIFT_LOBBY": "Lift lobby", "MAIL_ROOM": "Mail room",
    "MEDICAL_ROOM": "Medical room", "MOTHER'S_ROOM": "Mother's room", "NAP_ROOM": "Nap room", "OUT_OF_SCOPE": "Not in contract",
    "PHONE_BOOTH": "Phone booth", "PRAYER_ROOM": "Prayer room", "QUICK_SPRINT": "Quick sprint", "RECEPTION": "Reception",
    "TERRACE": "Terrace", "THE_HATCHERY": "The Hatchery", "THE_STUDIO_ROOM": "Studio", "TRAINING_ROOM": "Training room",
    "UPS_SERVER_BATTERY_BMS_ROOM": "Server, UPS & battery", "VISITOR_HUB": "Visitor hub", "WASHROOM": "Washroom",
    "WORKHALL": "Workhall", "ZEN_ROOM": "Zen room",
}
# kinds of space named by their own label (one room each); the rest are named by their type
NAMED = {"Boardroom", "Collaboration huddle", "Departmental room", "Executive corner cabin", "Hub room", "Phone booth",
         "Quick sprint", "Visitor hub", "Zen room", "Server, UPS & battery", "The Hatchery", "Training room", "Studio",
         "Mail room", "Medical room", "Nap room", "Prayer room", "Mother's room"}
NEIGHBOURHOODS = ("AUTO", "DRIVE", "HEALTH", "HOME", "LIFE", "TRAVEL")

rings_of = lambda d: [[tuple(map(float, q.split())) for q in part.split("L")] for part in re.findall(r"M([^Z]+)Z", d)]


def poly_of(d):
    """an SVG path's rings as one shape, even-odd (a ring inside another is a hole: the corridor round the rooms)"""
    g = Polygon()
    for r in rings_of(d):
        if len(r) > 2: g = g.symmetric_difference(Polygon(r).buffer(0))
    return g.buffer(0)


def title(t):
    t = re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", lambda m: m.group(0).capitalize(), t)
    return re.sub(r"\s*-\s*", " - ", re.sub(r"\bPax\b", "PAX", re.sub(r"\bPb\b", "PB", t)))


def d_of(poly):
    out = []
    for g in (poly.geoms if hasattr(poly, "geoms") else [poly]):
        for r in [g.exterior] + list(g.interiors):
            out.append("M" + "L".join(f"{round(x)} {round(y)}" for x, y in list(r.coords)[:-1]) + "Z")
    return "".join(out)


def spaces(tk, labels, colours, caps=None):
    """the toolkit's space-plan outlines (rooms.json, source MI) as the deck's spaces. caps: the largest each kind of room is
    (m2); an outline over three times that, or over 6,000 m2 (more than the floor), is a block's frame on the layer, not a room"""
    caps = caps or {}
    R = json.load(open(os.path.join(tk, "rooms.json"), encoding="utf-8"))["spaces"]
    out, untyped, unnamed = [], collections.Counter(), []
    for sp in R:
        lay = sp.get("layer") or ""
        if sp.get("source") != "MI" or not lay.startswith("AC_"):
            continue
        typ = LAYER_TYPE.get(lay[3:])
        if not typ:
            untyped[lay] += 1; continue
        g = poly_of(sp["d"])
        if g.is_empty:
            continue
        if g.area > 6000e6 or (typ in caps and g.area > 3 * caps[typ] * 1e6):
            untyped[f"{lay} (oversized, {g.area / 1e6:.0f} m2)"] += 1; continue
        inside = [(t, x, y) for t, x, y, _ in labels if g.buffer(150).contains(Point(x, y))]
        names = list(dict.fromkeys(title(t) for t, x, y in inside))
        if typ in NAMED and names:
            name = " / ".join(names[:3])
        else:
            name = typ
            if typ in NAMED: unnamed.append(f"{typ} ({sp['m2']} m2)")
        at = (inside[0][1], inside[0][2]) if inside and typ in NAMED else g.representative_point().coords[0]
        gg = g.simplify(10)
        out.append(dict(type=typ, name=name, colour="#" + colours.get(typ, "E4E2DD"), m2=round(gg.area / 1e6, 1),
                        x=round(at[0]), y=round(at[1]), d=d_of(gg)))
    out.sort(key=lambda s: (s["x"], s["y"]))
    for i, s in enumerate(out):
        s["id"] = f"r{i + 1}"
    if untyped: print("  AC_ layers with no deck type (left out):", dict(untyped))
    if unnamed: print(f"  {len(unnamed)} named-kind spaces with no label inside:", unnamed[:12])
    return out


def _walls(tk):
    """the wall linework of a toolkit output in its SVG frame (mm, y down), and the frame's origin (data-ox, data-oy)"""
    import faces as FC
    svg = open(os.path.join(tk, "full.svg"), encoding="utf-8").read()
    head = svg[:600]
    ox = float(re.search(r'data-ox="(-?[\d.]+)"', head).group(1)); oy = float(re.search(r'data-oy="(-?[\d.]+)"', head).group(1))
    out = [p for cls, d in re.findall(r'<path class="([^"]+)" d="([^"]*)"', svg) if cls.split()[-1] in ("wall", "glass") for p in FC.subpaths(d)]
    return out, (ox, oy)


def frame_shift(tk, prev_tk, px=200.0):
    """the translation (mm) that puts the previous drawing's world coordinates onto this drawing's. The walls of both are
    drawn in their SVG frames at 0.2 m a pixel, padded (phase correlation wraps round), and correlated; a drawing moved in
    CAD moves its frame with it, so the frames' origins carry the rest. -> (dx, dy, response 0..1)"""
    a, (aox, aoy) = _walls(prev_tk); b, (box_, boy) = _walls(tk)
    xs = [x for p in a + b for x, y in p]; ys = [y for p in a + b for x, y in p]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    W, H = 2 * (int((x1 - x0) / px) + 2), 2 * (int((y1 - y0) / px) + 2)
    def raster(paths):
        im = np.zeros((H, W), np.float32)
        for p in paths:
            pts = np.array([[(x - x0) / px, (y - y0) / px] for x, y in p], np.int32)
            cv2.polylines(im, [pts], False, 1.0, 1)
        return cv2.GaussianBlur(im, (5, 5), 0)
    (sx, sy), resp = cv2.phaseCorrelate(raster(a), raster(b))
    dsx, dsy = sx * px, sy * px                       # the shift in the SVG frames (y down)
    return dsx + box_ - aox, (boy - aoy) - dsy, resp


def zones(tk, prev_tk, shift, frame):
    """the six neighbourhoods (teams.json), each numbered by the previous drawing's ak_zone it overlaps most"""
    ox, oy = frame
    tj = json.load(open(os.path.join(tk, "teams.json")))["teams"]
    prev = []
    if prev_tk and os.path.exists(os.path.join(prev_tk, "teams.json")):
        head = open(os.path.join(prev_tk, "full.svg"), encoding="utf-8").read(600)
        pox = float(re.search(r'data-ox="(-?[\d.]+)"', head).group(1)); poy = float(re.search(r'data-oy="(-?[\d.]+)"', head).group(1))
        for t in json.load(open(os.path.join(prev_tk, "teams.json")))["teams"]:
            n = re.sub(r"\D", "", t["name"])
            # previous svg -> world -> this world (shift) -> this svg
            rs = [Polygon([(x + pox + shift[0] - ox, oy - (poy - y + shift[1])) for x, y in r]).buffer(0) for r in rings_of(t["zone"]) if len(r) > 2]
            prev.append((n, unary_union(rs)))
    out, used = [], set()
    for t in tj:
        g = poly_of(t["zone"])
        best = max(prev, key=lambda q: q[1].intersection(g).area / max(g.area, 1)) if prev else None
        share = best[1].intersection(g).area / max(g.area, 1) if best else 0
        n = best[0] if best and share > 0.3 and best[0] not in used else None
        if n: used.add(n)
        nm = t["name"].strip().title()
        out.append(dict(id=t["id"], n=n, title=nm, seats=t["seats"], m2=t["m2"], x=t["x"], y=t["y"], zone=t["zone"], desks=t["desks"], overlap=round(share, 2)))
    free = iter(sorted({f"{i:02d}" for i in range(1, 7)} - used))
    for z in out:
        if not z["n"]: z["n"] = next(free, "?")
        z["name"] = f"{z['n']} · {z['title']}"
    out.sort(key=lambda z: z["n"])
    return out


def types(tk):
    """the workstation types: each AC_WS_TYPE insert (inserts.json) matched to its <use> in instanced.svg by its placement"""
    p = os.path.join(tk, "inserts.json")
    if not os.path.exists(p):
        return []
    ins = json.load(open(p))["inserts"]
    svg = open(os.path.join(tk, "instanced.svg"), encoding="utf-8").read()
    uses = [(bid, tuple(map(float, m.replace(",", " ").split()))) for bid, m in re.findall(r'<use href="#(b\d+)" transform="matrix\(([^)]*)\)"', svg)]
    grid = collections.defaultdict(list)
    for bid, m in uses:
        grid[(round(m[4] / 500), round(m[5] / 500))].append((bid, m))
    by = collections.defaultdict(list); missed = collections.Counter()
    for i in ins:
        e, f = i["m"][4], i["m"][5]
        cand = [u for dx in (-1, 0, 1) for dy in (-1, 0, 1) for u in grid[(round(e / 500) + dx, round(f / 500) + dy)]]
        hit = min(cand, key=lambda u: abs(u[1][4] - e) + abs(u[1][5] - f)) if cand else None
        if hit and abs(hit[1][4] - e) + abs(hit[1][5] - f) < 30:
            by[i["layer"]].append([hit[0]] + [round(v, 4) if k < 4 else round(v, 1) for k, v in enumerate(hit[1])])
        else:
            missed[i["layer"]] += 1
    out = []
    for lay in sorted(by):
        k = re.search(r"(\d+)$", lay).group(1).lstrip("0")
        out.append(dict(t=f"T{k}", name=f"Type {k}", layer=lay, uses=by[lay]))
    if missed: print("  inserts with no matching <use>:", dict(missed))
    return out
