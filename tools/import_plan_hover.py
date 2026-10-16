"""Bring the 09.10.2026 test-fit layouts into the presentation's data.

The layouts arrive as `plan-hover-data.js` (built from the DXFs by tools/plan_hover/build_plan_hover.py):
per option a full plan SVG, the CAD team's MI_* room outlines and the team zones with their seats.
This rewrites, in the presentation's own frame (mm, shell lower-left = 0,0, y up, north = +x):

  data/opt{1,2}.json   vec.partition / glass / door, texts, plants   (shell, columns, size kept)
  data/zones.json      zones from the CAD rooms + teams, hover data, true floor outline
  tools/_raster/opt{1,2}.svg   furniture layer for tools/raster_plan.js -> assets/plans/opt{1,2}_furn.png

Usage (from the project folder):
  python tools/import_plan_hover.py data/src/plan-hover-data.js [--debug out_dir]
"""
import json, math, os, re, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import author_zones  # noqa: E402  (the programme type list)
import derive_layout  # noqa: E402  (events, routes, cameras, signature… derived from the CAD)

NS = "{http://www.w3.org/2000/svg}"
# new SVG frame (y down) -> presentation frame (y up): x = x' + DX, y = Y0 - y'.  Fitted on ~40 shared labels (<1 mm).
FRAME = {"opt1": ("op1", 5635.0, 35956.0), "opt2": ("op2", 5194.0, 36160.0), "opt3": ("op3", 4427.0, 36057.0)}
# Option 03 (14.10) is drawn 387 734.1 / 509 912.0 mm from Option 02 (the AHUs and lift lobby match to the mm); its
# frame above is fitted on the core's labels. Its shell, columns and size are Option 02's: the same building.
SHIFT = {"opt3": ("opt2", 387734.1, 509912.0)}
VECTOR = {"wall": "partition", "glass": "glass", "door": "door"}

# CAD space name -> programme type (first match wins); corridors are circulation, not a zone
ROOM_TYPES = [
    (r"corridor", None),
    (r"meeting|think tank", "meet"), (r"phone booth", "quiet"), (r"board", "board"),
    (r"^cafe|cafeteria", "cafe"), (r"reception|entrance", "arrive"), (r"podcast", "studio"),
    (r"agile|collaboration area|hotdesk", "focus"),          # agile workstations: part of the workhall, not a team
    (r"breakout|collab|lounge", "collab"),
    (r"server|ups|electrical", "secure"), (r"service|store|prep|dine", "service"),
    (r"ahu|lift|washroom", "core"), (r"^$", "core"),
]


def load(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def subpaths(d):
    """M/L/C path -> list of point lists (cubics flattened to 8 segments)."""
    out, cur = [], None
    for cmd, args in re.findall(r"([MLCZ])([^MLCZ]*)", d):
        a = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", args)]
        if cmd == "M":
            cur = [(a[0], a[1])]; out.append(cur)
            for i in range(2, len(a), 2):
                cur.append((a[i], a[i + 1]))
        elif cmd == "L":
            for i in range(0, len(a), 2):
                cur.append((a[i], a[i + 1]))
        elif cmd == "C":
            for i in range(0, len(a), 6):
                p0 = cur[-1]; c1, c2, p3 = (a[i], a[i + 1]), (a[i + 2], a[i + 3]), (a[i + 4], a[i + 5])
                for k in range(1, 9):
                    t = k / 8; u = 1 - t
                    cur.append((u**3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p3[0],
                                u**3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p3[1]))
        elif cmd == "Z" and cur:
            cur.append(cur[0])
    return out


def matrix(tr):
    m = re.match(r"matrix\(([^)]*)\)", tr or "")
    if not m:
        return (1, 0, 0, 1, 0, 0)
    return tuple(float(v) for v in re.split(r"[\s,]+", m.group(1).strip()))


def apply(m, pts):
    a, b, c, d, e, f = m
    return [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]


def flatten(svg):
    """-> [(classes, [polylines]) ...], texts, block instances (for plants), all in the SVG's own frame."""
    root = ET.fromstring(svg)
    defs = {g.get("id"): g for g in root.find(NS + "defs")}
    prims, texts, uses = [], [], []

    def emit(el, m, block=None):
        cls = el.get("class", "")
        prims.append((cls, [apply(m, p) for p in subpaths(el.get("d", ""))], block))

    for el in root:
        if el.tag == NS + "g" and el.get("class") == "labels":
            for t in el.iter(NS + "text"):
                txt = " ".join(" ".join(t.itertext()).split())        # tspans are separate lines: keep a space between them
                if txt:
                    texts.append((txt, float(t.get("x")), float(t.get("y")), float(t.get("font-size", 200))))
        elif el.tag == NS + "g":
            for p in el.iter(NS + "path"):
                emit(p, (1, 0, 0, 1, 0, 0))
        elif el.tag == NS + "path":
            emit(el, (1, 0, 0, 1, 0, 0))
        elif el.tag == NS + "use":
            bid = el.get("href", "")[1:]; m = matrix(el.get("transform"))
            uses.append((bid, m))
            for p in defs[bid].iter(NS + "path"):
                emit(p, m, bid)
    return prims, texts, uses, defs


def length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def misfiled_glass_blocks(defs):
    """Blocks drawn on a glass layer that are really furniture (e.g. a table with chairs): many small glass pieces."""
    out = set()
    for bid, g in defs.items():
        pieces = [sp for p in g.iter(NS + "path") if "glass" in (p.get("class") or "") for sp in subpaths(p.get("d", ""))]
        if len(pieces) > 40 and sum(1 for sp in pieces if length(sp) < 300) > 0.6 * len(pieces):
            out.add(bid)
    return out


def to_frame(pts, dx, y0):
    return [(round(x + dx), round(y0 - y)) for x, y in pts]


def area_signed(pts):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])) / 2


def area(pts):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def centroid(pts):
    a = cx = cy = 0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        k = x1 * y2 - x2 * y1; a += k; cx += (x1 + x2) * k; cy += (y1 + y2) * k
    return (cx / (3 * a), cy / (3 * a)) if a else pts[0]


def path_d(polys):
    return "".join("M" + "L".join(f"{x} {y}" for x, y in p) + "Z" for p in polys)


def near_shell(shell, tol=120, cell=500):
    grid = {}
    for pl in shell:
        pts = list(zip(pl[0::2], pl[1::2]))
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            n = max(1, int(math.dist((x1, y1), (x2, y2)) // 100))
            for i in range(n + 1):
                x, y = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
                grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y))

    def on_shell(p):
        gx, gy = int(p[0] // cell), int(p[1] // cell)
        return any(abs(q[0] - p[0]) < tol and abs(q[1] - p[1]) < tol
                   for i in (-1, 0, 1) for j in (-1, 0, 1) for q in grid.get((gx + i, gy + j), ()))
    return on_shell


def room_type(name):
    n = (name or "").strip().lower()
    for pat, t in ROOM_TYPES:
        if re.search(pat, n):
            return t
    return "service"


CORRIDOR_M2 = 100   # an unnamed space this large is the floor left between the rooms (the 14.10 drawing outlines no corridors)


def room_name(name, m2):
    """The 14.10 drawing's room names, tidied: a label drawn just outside its own room lands in the café next door
    ("Cafeteria 52 PAX / Meeting Room 6 PAX": the café keeps its own); "Tinktank" is the founder's think tank."""
    parts = (name or "").split(" / ")
    cafe = next((p for p in parts if re.search(r"^cafe|cafeteria", p, re.I)), None)
    if cafe and len(parts) > 1:
        name = cafe
    name = re.sub(r"^tinktank$", "Think tank", name or "", flags=re.I)
    if not name and m2 >= CORRIDOR_M2:
        name = "Corridor"
    return name


def on_plate(polys, plate):
    """Rings (each closed: last point = first) clipped to the floor plate: a space the walls leave open to the sheet's
    edge (Option 03's corridor, outlined round the whole sheet) stops at the façades."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    g = None
    for p in polys:
        q = Polygon(p).buffer(0)
        g = q if g is None else g.symmetric_difference(q)        # even-odd, as the plan fills them
    g = g.intersection(plate)
    out = []
    for q in getattr(g, "geoms", [g]):
        if q.geom_type == "Polygon" and q.area > 1e4:
            for ring in [q.exterior] + list(q.interiors):
                pts = [(round(x), round(y)) for x, y in ring.coords]
                out.append(pts)
    return out or polys


def import_option(key, src, old, plate=None):
    sk, dx, y0 = FRAME[key]
    o = src["options"][sk]
    prims, texts, uses, defs = flatten(o["svg"])
    on_shell = near_shell(old["vec"]["shell"])

    vec = {"partition": [], "glass": [], "door": []}
    dropped = 0
    furniture = misfiled_glass_blocks(defs)
    for cls, polys, block in prims:
        kind = next((VECTOR[c] for c in cls.split() if c in VECTOR), None) if cls.startswith("s ") else None
        if not kind or (kind == "glass" and block in furniture):
            continue
        for p in polys:
            q = to_frame(p, dx, y0)
            if len(q) < 2:
                continue
            # long runs on a door layer are glass partitions (e.g. the curved SOC screen), not door swings
            if kind == "door" and length(q) > 3200:
                vec["glass"].append([v for pt in q for v in pt])
                continue
            if kind == "partition":
                hits = sum(on_shell(pt) for pt in q[:: max(1, len(q) // 12)])
                if hits >= 0.9 * len(q[:: max(1, len(q) // 12)]):
                    dropped += 1
                    continue
            vec[kind].append([v for pt in q for v in pt])

    # plants: every instance of a block drawn in the green (planting) class
    green = {bid for bid, g in defs.items() if any("green" in (p.get("class") or "") for p in g.iter(NS + "path"))}
    plants = []
    for bid, m in uses:
        if bid not in green:
            continue
        pts = [pt for p in defs[bid].iter(NS + "path") for sp in subpaths(p.get("d", "")) for pt in apply(m, sp)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = to_frame([((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)], dx, y0)[0]
        plants.append([cx, cy, round(max(max(xs) - min(xs), max(ys) - min(ys)) / 2)])

    txt = [dict(t=t, x=round(x + dx), y=round(y0 - y), h=round(h)) for t, x, y, h in texts]

    # zones from the CAD room outlines (MI_* layers) and the team zones
    zones, hover_rooms, hover_teams, rooms_frame, desk_frame, unnamed = [], [], [], [], [], set()
    for r in o["rooms"]:
        r = dict(r, name=room_name(r["name"], float(r["m2"])))
        polys = [to_frame(p, dx, y0) for p in subpaths(r["d"])]
        if plate is not None:
            polys = on_plate(polys, plate)
        hover_rooms.append(dict(id=r["id"], name=r["name"] or "Space", m2=float(r["m2"]),
                                at=to_frame([(float(r["x"]), float(r["y"]))], dx, y0)[0], d=path_d([p[:-1] for p in polys])))
        t = room_type(r["name"])
        rooms_frame.append((r["name"] or "", [p[:-1] for p in polys]))
        if t:
            outer = max(polys, key=lambda p: area(p[:-1]))[:-1]
            z = dict(type=t, name=r["name"] or "Shaft / riser", poly=[list(p) for p in outer], area=round(float(r["m2"]), 1))
            if t == "focus":
                z["agile"] = True
            if not r["name"]:
                unnamed.add(id(z))
            zones.append(z)
    # a riser sits with the core: an unnamed room wholly west of the named core rooms is not one
    # (Opt 01's leftover nook at the south-west glass). It keeps its hover; it just isn't a zone.
    core_x0 = min((p[0] for z in zones if z["type"] == "core" and id(z) not in unnamed for p in z["poly"]), default=None)
    if core_x0 is not None:
        zones = [z for z in zones if not (id(z) in unnamed and max(p[0] for p in z["poly"]) < core_x0 - 1000)]
    for tm in o["teams"]:
        zp = max((p[:-1] for p in (to_frame(sp, dx, y0) for sp in subpaths(tm["zone"]))), key=area)
        desks = [to_frame(sp, dx, y0) for d in tm["desks"] for sp in subpaths(d)]
        if "SOC" not in tm["name"].upper():
            desk_frame.extend(p[:-1] for p in desks)
        name = tm["name"].replace("SOC ROOM", "SOC").title().replace("Hr,", "HR &").replace("Soc", "SOC")
        name = re.sub(r"^Sales & Marketing$", "Sales", name)   # the 14.10 drawing's name for Sales (the chart says Sales)
        typ = "soc" if "SOC" in tm["name"].upper() else "focus"
        zones.append(dict(type=typ, name=name, poly=[list(p) for p in zp], area=round(area(zp) / 1e6, 1),
                          pax=int(tm["pax"]), seats=int(tm["seats"]), hot=int(tm["hot_desks"])))
        hover_teams.append(dict(id=tm["id"], name=name, pax=int(tm["pax"]), seats=int(tm["seats"]), hot=int(tm["hot_desks"]),
                                at=to_frame([(float(tm["x"]), float(tm["y"]))], dx, y0)[0],
                                zone=path_d([zp]), desks=path_d([p[:-1] for p in desks])))
    # SOC first so zonesOf(opt, "soc")[0] is the room itself
    zones.sort(key=lambda z: (z["type"] != "soc", -z["area"]))

    opt = dict(old, vec=dict(old["vec"], **vec), plants=plants, texts=txt, source=o["source"])
    stats = dict(walls=len(vec["partition"]), glass=len(vec["glass"]), doors=len(vec["door"]), dropped_on_shell=dropped,
                 plants=len(plants), texts=len(txt), zones=len(zones), rooms=len(hover_rooms), teams=len(hover_teams))
    return opt, zones, dict(rooms=hover_rooms, teams=hover_teams), stats, (sk, dx, y0, o), rooms_frame, desk_frame


def shell_outline(opt):
    """Tenant floor outline from the base-building shell: prow tip, the two long glass lines (the longest
    horizontal runs), and the north façade (the longest vertical run; shafts beyond it are the building's)."""
    pts = [(x, y) for pl in opt["vec"]["shell"] for x, y in zip(pl[0::2], pl[1::2]) if not (x < 100 and y > opt["size"][1] - 100)]
    tip = min(pts, key=lambda p: p[0])
    runs_h, runs_v = {}, {}
    for pl in opt["vec"]["shell"]:
        q = list(zip(pl[0::2], pl[1::2]))
        for (x1, y1), (x2, y2) in zip(q, q[1:]):
            if abs(y1 - y2) < 30 and min(x1, x2) > 25000:
                runs_h[round(y1 / 50) * 50] = runs_h.get(round(y1 / 50) * 50, 0) + abs(x2 - x1)
            if abs(x1 - x2) < 30 and x1 > 60000:
                runs_v[round(x1 / 50) * 50] = runs_v.get(round(x1 / 50) * 50, 0) + abs(y2 - y1)
    # outermost of the strong façade lines on each side (the glass line, not the inner sill)
    top = {y: l for y, l in runs_h.items() if y > tip[1]}; bot = {y: l for y, l in runs_h.items() if y < tip[1]}
    yhi = max(y for y, l in top.items() if l > 0.6 * max(top.values()))
    ylo = min(y for y, l in bot.items() if l > 0.6 * max(bot.values()))
    xn = max(runs_v, key=runs_v.get)
    tx, ty = tip
    # the prow sides run at 45 degrees from the tip to the long façades
    return [[round(tx), round(ty)], [round(tx + yhi - ty), yhi], [xn, yhi], [xn, ylo], [round(tx + ty - ylo), ylo]]


RASTER_CSS = """
svg{background:#000}
path{fill:none;stroke:#fff;stroke-width:1.05px;vector-effect:non-scaling-stroke;stroke-linecap:round;stroke-linejoin:round}
.s.wall,.t,text{display:none}.s.glass,.s.door{stroke-opacity:.6}
.s.shade{stroke-opacity:.55}.h{stroke-opacity:.4;stroke-width:.6px}.s.anno{stroke-opacity:.7}
.f{fill:#fff;stroke:none;fill-opacity:.16}.m{fill:#000;stroke:none}
"""


def offset_convex(poly, d):
    """Grow a convex polygon (CCW or CW) by d: shift every edge outwards, intersect neighbours."""
    n = len(poly); sgn = 1 if sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1])) > 0 else -1
    lines = []
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        L = math.hypot(x2 - x1, y2 - y1); nx, ny = sgn * (y2 - y1) / L, -sgn * (x2 - x1) / L
        lines.append(((x1 + nx * d, y1 + ny * d), (x2 - x1, y2 - y1)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i - 1], lines[i]
        t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / (r[0] * s[1] - r[1] * s[0])
        out.append((p[0] + r[0] * t, p[1] + r[1] * t))
    return out


def raster_svg(sk, dx, y0, o, opt, outline, path):
    """The plan's furniture layer placed on the raster's pixel grid (80 px/m, top-left = (0, H)),
    clipped to the floor plate so the drawing sheet's frame and the building beyond stay out."""
    r = opt["raster"]; s = r["px_per_m"] / 1000; H = opt["size"][1]
    inner = re.sub(r"^<svg[^>]*>|</svg>$", "", o["svg"]).replace("<style>", "<style data-x>").split("</style>", 1)[1]
    clip = " ".join(f"{x * s:.1f},{(H - y) * s:.1f}" for x, y in offset_convex([tuple(p) for p in outline], 900))
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{r["w"]}" height="{r["h"]}" viewBox="0 0 {r["w"]} {r["h"]}">'
           f'<style>{RASTER_CSS}</style><clipPath id="plate"><polygon points="{clip}"/></clipPath>'
           f'<g clip-path="url(#plate)"><g transform="scale({s}) translate({dx} {H - y0})">{inner}</g></g></svg>')
    open(path, "w", encoding="utf-8").write(doc)


def plate(outline):
    """the floor plate, with the façade line itself (600 mm out, where the glass and its mullions are drawn)"""
    from shapely.geometry import Polygon
    return Polygon(outline).buffer(600, join_style=2)


def main():
    src = load(sys.argv[1])
    keys = [k for k in FRAME if FRAME[k][0] in src["options"]]
    old = {}
    for k in keys:
        p = os.path.join(ROOT, "data", f"{k}.json")
        if not os.path.exists(p) and k in SHIFT:     # a new option: start from its base option's building
            base, tx, ty = SHIFT[k]
            b = json.load(open(os.path.join(ROOT, "data", f"{base}.json"), encoding="utf-8"))
            p = None; old[k] = dict(b, origin_dxf=[b["origin_dxf"][0] - tx, b["origin_dxf"][1] - ty],
                                    raster=dict(b["raster"], file=f"{k}_furn.png"))
        if p:
            old[k] = json.load(open(p, encoding="utf-8"))
    zones_json = dict(types={k: dict(label=v[0], tier=v[1]) for k, v in author_zones.TYPES.items()},
                      opt1=author_zones.build(author_zones.OPT1), opt2=author_zones.build(author_zones.OPT2),
                      annot=dict(author_zones.ANNOT))
    os.makedirs(os.path.join(HERE, "_raster"), exist_ok=True)
    outline = shell_outline(old["opt1"])
    glazed = [(outline[0], outline[1]), (outline[1], outline[2]), (outline[4], outline[0])]   # SW, W, SE glass
    labels = None
    for key in keys:
        opt, zones, hover, stats, raw, rooms_frame, desk_frame = import_option(key, src, old[key], plate(outline) if key in SHIFT else None)
        json.dump(opt, open(os.path.join(ROOT, "data", f"{key}.json"), "w"), separators=(",", ":"))
        derived, lab = derive_layout.derive(key, zones, rooms_frame, opt["texts"], outline, glazed, desk_frame)
        zones_json[key] = dict(zones=zones, hover=hover, **derived)
        labels = labels or lab
        raster_svg(*raw, opt, outline, os.path.join(HERE, "_raster", f"{key}.svg"))
        print(key, raw[3]["source"], stats, {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in derived.items()},
              "events m2", {k: e["area"] for k, e in derived["events"].items()}, "routes m", {k: r["m"] for k, r in derived["routes"].items()})
    # façade labels at the middle of each glass edge, pushed 1.6 m outside
    def fac_label(a, b, text, rot):
        (x1, y1), (x2, y2) = a, b; L = math.hypot(x2 - x1, y2 - y1); cw = area_signed(outline) < 0
        n = (-(y2 - y1) / L, (x2 - x1) / L) if cw else ((y2 - y1) / L, -(x2 - x1) / L)
        return dict(t=text, at=[round((x1 + x2) / 2 + n[0] * 1600), round((y1 + y2) / 2 + n[1] * 1600)], kind="facade", rot=rot)
    o = outline
    labels += [fac_label(o[1], o[2], f"West façade · {round(math.dist(o[1], o[2]) / 1000)} m of glass", 0),
               fac_label(o[0], o[1], "South-west façade", -45), fac_label(o[4], o[0], "South-east façade", 45),
               fac_label(o[3], o[4], "East façade (core side)", 0)]
    zones_json["annot"]["labels"] = labels
    zones_json["annot"]["outline"] = outline
    zones_json["floor_area"] = round(area([tuple(p) for p in outline]) / 1e6)
    zones_json["source"] = {k: src["options"][FRAME[k][0]]["source"] for k in keys}
    json.dump(zones_json, open(os.path.join(ROOT, "data", "zones.json"), "w"), separators=(",", ":"))
    print("outline", outline, "floor area m2", zones_json["floor_area"])
    print("next: node tools/raster_plan.js  (renders tools/_raster/*.svg -> assets/plans/opt*_furn.png)")


if __name__ == "__main__":
    main()
