"""The layout plan from the DXF, for s-layout and s-blowup: pictures of the plan, its spaces, neighbourhoods and fire egress.

    python tools/acko/plan_dxf.py "<toolkit>/viewer/out/tf2110" "<the test fit .dxf>"

Reads the DXF plan toolkit's output for the drawing (full.svg, labels.json, teams.json, rooms.json: run the toolkit first,
with projects/acko.json) and the DXF itself (its fire egress layers), and writes:
  assets/img/plan-dxf-12.webp, -24.webp, -48.webp   the plan drawn at 12 / 24 / 48 px per metre (transparent), so the
                                                     deck can show it sharp at every zoom (the full vector plan is too
                                                     heavy to fly smoothly)
  data/plan-dxf.js (window.PLAN_DXF), in the toolkit's plan frame (mm, y down):
    viewBox   the plan's crop [x, y, w, h]
    levels    the pictures and their px per metre
    spaces    the rooms as the drawing encloses them: each room label (labels.json, layer OB-I-ANNO-TEXT) takes the room
              face its walls enclose (tools/acko/faces.py), labels sharing a face share it; typed by the label, coloured
              by the deck's legend (slide 53). Open-plan labels with no enclosing face keep the previous build's outline of
              the same name. The not-in-contract area (ak_zone_Nic) from rooms.json
    zones     the neighbourhoods (the drawing's ak_zone outlines, seats from its workstation counts), from teams.json
    egress    the fire egress paths (ak_Ep layers): band "lt50" (< 50 m) or "50-60", and length in m
    overlays  from data/deck-plan.js, mapped onto the DXF: the Blown up X / Y / Z boxes, the fire compartment line,
              the entrances, the arrival zones
Needs NODE_PATH=C:/Users/Ritika/Mitigata/node_modules (puppeteer-core) for the pictures.
"""
import io, json, os, re, subprocess, sys, zipfile, collections, time
import numpy as np, cv2, ezdxf
from ezdxf import path as zpath
from PIL import Image
from shapely.geometry import Polygon, Point, MultiPolygon, LineString
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "plan")
LEVELS = (12, 24, 48)
FW, FH = 1920, 1080
TILES = ["image206.png", "image212.png", "image208.png", "image209.png"]   # slide 53's plan tiles (X in two, Y, Z)

# the deck's slide-53 plan -> the DXF, measured by overlaying the composed tiles on the DXF plan (within ~0.3 m):
# frame px -> composed image px -> a 24 px/m render of the toolkit's first full.svg -> world mm (DXF coordinates)
_SX, _SY = (5928 - 35) / (6462 - 6), (876 - 36) / (932 - 0)
_OX1, _OY1, _CX1, _CY1 = -185842, -360727, 7672, 12623


def frame_to_world(fx, fy):
    u = (fx - 32.6) * 6467 / 1850.9; v = (fy - 175) * 936 / 267.8
    rx, ry = 35 + (u - 6) * _SX, 36 + v * _SY
    return _CX1 + rx / 0.024 + _OX1, _OY1 - (_CY1 + ry / 0.024)


LEGEND = [("Reception", "EAE6DF"), ("Departmental room", "DDDBD4"), ("Visitor hub", "C3CBBC"), ("Collaboration huddle", "C2BFBB"),
          ("Quick sprint", "CED2CF"), ("Cafeteria", "CEDED1"), ("Training room", "B6AFAF"), ("The Hatchery", "DFE4DE"),
          ("Studio", "E5DEDE"), ("Phone booth", "D5CEED"), ("Collab", "A5B0AB"), ("Executive corner cabin", "D3D9C5"),
          ("Prayer room", "A19DAD"), ("Coffee corner", "BAB0C1"), ("Hub room", "F0EFF5"), ("Mother's room", "E0DFDD"),
          ("Zen room", "F4F3EF"), ("Server, UPS & battery", "929292")]
BY_LABEL = [("Boardroom", r"BOARD"), ("Departmental room", r"DEPARTMENTAL"), ("Collaboration huddle", r"HUDDLE"),
            ("Quick sprint", r"SPRINT|^\d+ PAX"), ("Visitor hub", r"VISITOR"), ("Phone booth", r"^PB\b"), ("Zen room", r"ZEN"),
            ("Hub room", r"HUB ROOM"), ("Mother's room", r"MOTHER"), ("Prayer room", r"PRAYER"), ("Studio", r"STUDIO"),
            ("The Hatchery", r"HATCHERY"), ("Executive corner cabin", r"EXECUTIVE"), ("Training room", r"TRAINING"),
            ("Pantry", r"DISHWASH|PLATE DROP"), ("Cafeteria", r"CAFE|PANTRY|HEATING|WASTE"), ("Reception", r"RECEPTION"), ("Coffee corner", r"COFFEE"),
            ("Server, UPS & battery", r"SERVER|UPS|BATTERY|ELECTRICAL|BMS"), ("Mail room", r"MAIL"), ("Medical room", r"MEDICAL"),
            ("Nap room", r"\bNAP\b"), ("Store room", r"STORE|RAIN COAT|UMBRELLA"), ("Collab", r"COLLAB")]
# rooms without walls all round: their outline can't come from the drawing alone
OPEN_PLAN = {"Reception", "Cafeteria", "Visitor hub", "Collab", "Coffee corner", "The Hatchery"}
# the largest each kind of room is (m2): a face bigger than this around its label has leaked through a gap in the walls
TYPE_CAP = {"Phone booth": 4, "Quick sprint": 30, "Collaboration huddle": 45, "Departmental room": 60, "Boardroom": 90, "Visitor hub": 40,
            "Executive corner cabin": 40, "Zen room": 20, "Mother's room": 20, "Prayer room": 25, "Hub room": 20, "Studio": 45, "The Hatchery": 45,
            "Training room": 90, "Medical room": 25, "Nap room": 25, "Mail room": 25, "Store room": 40, "Server, UPS & battery": 40,
            "Coffee corner": 60, "Reception": 120, "Cafeteria": 420, "Collab": 150, "Pantry": 30}
# the smallest each kind of room is (m2): a face smaller than this round its label is a table or a desk inside the room
TYPE_MIN = {"Phone booth": 0.8, "Quick sprint": 2.4, "Collaboration huddle": 12, "Departmental room": 22, "Boardroom": 40, "Visitor hub": 4,
            "Executive corner cabin": 10, "Zen room": 4, "Mother's room": 5, "Prayer room": 5, "Hub room": 4, "Studio": 15, "The Hatchery": 10,
            "Training room": 30, "Medical room": 3, "Nap room": 3, "Mail room": 2.5, "Store room": 3, "Server, UPS & battery": 3,
            "Coffee corner": 4, "Reception": 8, "Cafeteria": 50, "Collab": 10, "Pantry": 2}
# the legend's colours for what it doesn't list (slide 53 predates these rooms)
EXTRA_COLOURS = [("Boardroom", "D2CCE2"), ("Medical room", "D6E4E6"), ("Nap room", "E3DEEE"), ("Mail room", "E2DED6"),
                 ("Store room", "E2DED6"), ("Not in contract", "D4D4D4"), ("Room", "E4E2DD"),
                 # the named-layer drawing's floors (22.10.26): the open floor, its corridors, entries, lobbies, terrace, washrooms
                 ("Workhall", "E9E9E8"), ("Corridor", "EFEEEB"), ("Entry", "EAE6DF"), ("Lift lobby", "E6E3EE"),
                 ("Terrace", "D2E3C8"), ("Washroom", "DEDEDE")]
NOISE = r"[\d\s.-]+|DT|SMR\d+|MHS|ACD|FHS|PUNCH BAG|SWING CHAIR|DIGITAL SCREEN|COMMUNITY TABLE|1500MM WIDE CORRIDOR|ACD CAN BE PROVIDED HERE|SEATING AND SWING"


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.int16)


def legend_type(col):
    c = hexrgb(col); best = min(LEGEND, key=lambda t: int(np.abs(hexrgb(t[1]) - c).max()))
    return best[0] if int(np.abs(hexrgb(best[1]) - c).max()) <= 4 else None


def title(t):
    """"MOTHER'S ROOM" -> "Mother's Room" (str.title() would give "Mother'S"); PAX and PB stay capitals"""
    t = re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", lambda m: m.group(0).capitalize(), t)
    return re.sub(r"\bPax\b", "PAX", re.sub(r"\bPb\b", "PB", t))


# the deck's occupancy chart (slide 61): its groups and rows, in its order. Each row: (group, area, test on a space name)
OCC_ROWS = [
    ("Workhall", "Executive cabin", r"EXECUTIVE"),
    ("Meeting room", "Board room", r"BOARD"),
    ("Meeting room", "Focus room - 2 pax", r"^2 PAX\b"),
    ("Meeting room", "Visitor Hub", r"VISITOR HUB \d"),
    ("Meeting room", "Dealer Room - 4 pax", r"DEALER"),
    ("Meeting room", "Quick Sprint Room - 3 pax", r"SPRINT 3 PAX"),
    ("Meeting room", "Quick Sprint Room - 4 pax", r"SPRINT 4 PAX"),
    ("Meeting room", "Quick Sprint Room - 6 pax", r"SPRINT 6 PAX"),
    ("Meeting room", "Quick Sprint Room - 8 pax", r"SPRINT 8 PAX"),
    ("Meeting room", "Quick Sprint Room - 10 pax", r"SPRINT 10 PAX"),
    ("Meeting room", "Collaboration huddles - 10-12 pax", r"HUDDLE"),
    ("Meeting room", "Departmental Room - 18-20 pax", r"DEPARTMENTAL"),
    ("Meeting room", "Hatchery - 08 pax", r"HATCHERY"),
    ("Meeting room", "Studio", r"STUDIO"),
    ("Meeting room", "Phone booth", r"(^| / )PB \d"),
    ("Training room", "Training Room - 40 pax", r"TRAINING"),
    ("Recreational area / wellness", "Cafeteria", r"CAFE|HEATING STATION"),
    ("Recreational area / wellness", "Mother's Room", r"MOTHER"),
    ("Recreational area / wellness", "Zen Room", r"ZEN"),
    ("Recreational area / wellness", "Nap Room", r"\bNAP\b"),
    ("Recreational area / wellness", "Medical Room", r"MEDICAL"),
    ("Recreational area / wellness", "Prayer Room", r"PRAYER"),
    ("Recreational area / wellness", "Coffee corner", r"COFFEE"),
    ("Services", "UPS / Electrical", r"UPS|ELECTRICAL"),
    ("Services", "Battery", r"BATTERY"),
    ("Services", "Hub Room", r"HUB ROOM"),
    ("Services", "Server Room", r"SERVER"),
]


def occupancy(z, zone_poly, spaces):
    """the occupancy rows for one neighbourhood: its workstations, then a count of each kind of space inside it (by the
    space's label point; a space named for several labels, e.g. "PB 10 / PB 11", counts each of them)"""
    rows = [("Workhall", "Workstations", z["seats"])]
    inside = [sp for sp in spaces if zone_poly.contains(Point(sp["x"], sp["y"])) and sp["name"] != sp["type"]]
    for grp, area, rx in OCC_ROWS:
        n = 0
        for sp in inside:
            parts = sp["name"].split(" / ")
            n += sum(1 for part in parts if re.search(rx, part, re.I)) if area in ("Phone booth", "Focus room - 2 pax") else int(bool(re.search(rx, sp["name"], re.I)))
        if n:
            rows.append((grp, area, n))
    return rows


def d_of(poly):
    out = []
    for g in (poly.geoms if hasattr(poly, "geoms") else [poly]):
        for r in [g.exterior] + list(g.interiors):
            pts = list(r.coords)[:-1]
            out.append("M" + "L".join(f"{round(x)} {round(y)}" for x, y in pts) + "Z")
    return "".join(out)


def check_spaces(lines, spaces, crop):
    """the spaces over the partition lines: the whole floor and two close-ups (tools/_work/plan/spaces*.png)"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for name, box, k in [("spaces", None, 7000), ("spaces_west", (14000, 14500, 60000, 45000), 2500), ("spaces_mid", (95000, 14500, 140000, 48000), 2500)]:
        x0, y0, x1, y1 = box or (crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3])
        fig = plt.figure(figsize=((x1 - x0) / k, (y1 - y0) / k), dpi=110)
        ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal"); ax.axis("off")
        for l in lines:
            bb = l.bounds
            if bb[2] < x0 or bb[0] > x1 or bb[3] < y0 or bb[1] > y1: continue
            ax.plot(*l.xy, color="#999", lw=.35)
        for sp in spaces:
            for part in re.findall(r"M([^Z]+)Z", sp["d"]):
                pts = [tuple(map(float, q.split())) for q in part.split("L")]
                ax.fill(*zip(*pts), fc=sp["colour"], alpha=.75, ec="#5222d0", lw=.6)
            if box: ax.text(sp["x"], sp["y"], sp["name"][:22], fontsize=4, ha="center", color="#222")
        fig.savefig(os.path.join(WORK, name + ".png")); plt.close(fig)
    print("check pictures: tools/_work/plan/spaces*.png")


def main(tk, dxf_path):
    t0 = time.time()
    os.makedirs(WORK, exist_ok=True)
    full = os.path.join(tk, "full.svg")
    head = open(full, encoding="utf-8").read(600)
    OX = float(re.search(r'data-ox="(-?[\d.]+)"', head).group(1)); OY = float(re.search(r'data-oy="(-?[\d.]+)"', head).group(1))
    W, H = map(float, re.search(r'viewBox="0 0 (\d+) (\d+)"', head).groups())
    world_to_svg = lambda wx, wy: (wx - OX, OY - wy)
    node = lambda *a: subprocess.run(["node", os.path.join(ROOT, "tools", "acko", "plan_raster.js"), full, WORK, *map(str, a)],
                                     check=True, capture_output=True, text=True).stdout.strip()

    # ---- the crop: what the plan actually covers, plus 1.5 m ----
    skip = os.environ.get("PLAN_DXF_SKIP_RENDER") == "1"    # re-use the pictures in tools/_work/plan (while tuning spaces)
    if not skip:
        node(0, 0, int(W), int(H), 4)
    a = np.array(Image.open(os.path.join(WORK, "plan-4.png")))[..., 3]
    ys, xs = np.where(a > 40)
    cx0, cy0 = xs.min() / 4 * 1000 - 1500, ys.min() / 4 * 1000 - 1500
    cw, ch = (xs.max() - xs.min() + 1) / 4 * 1000 + 3000, (ys.max() - ys.min() + 1) / 4 * 1000 + 3000
    crop = [round(cx0), round(cy0), round(cw), round(ch)]
    print("crop", crop, f"({cw / 1000:.1f} x {ch / 1000:.1f} m)")

    # ---- the pictures ----
    if not skip:
        print(node(*crop, ",".join(map(str, LEVELS))))
    for ppm in (() if skip else LEVELS):
        im = Image.open(os.path.join(WORK, f"plan-{ppm}.png"))
        dst = os.path.join(ROOT, "assets", "img", f"plan-dxf-{ppm}.webp")
        im.save(dst, "WEBP", quality=84, method=6)
        print(f"  plan-dxf-{ppm}.webp {im.size[0]}x{im.size[1]} {os.path.getsize(dst) / 1e6:.2f} MB")

    # ---- room labels (the toolkit's labels.json: each text's drawn box) and the egress paths (the DXF) ----
    labels = []
    for L in json.load(open(os.path.join(tk, "labels.json"), encoding="utf-8"))["labels"]:
        if L["layer"] != "OB-I-ANNO-TEXT" or not L["text"] or re.fullmatch(NOISE, L["text"], re.I):
            continue
        b = L.get("box")
        at = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (L["x"], L["y"])
        labels.append((L["text"], at[0], at[1], (L["x"], L["y"])))
    doc = ezdxf.readfile(dxf_path); msp = doc.modelspace()
    egress = []
    ep_blocks = {b.name for b in doc.blocks if any(x.dxf.layer.lower().startswith("ak_ep") for x in b)}
    def walk(ents, d=0):
        for e in ents:
            if e.dxftype() == "INSERT" and d < 3 and e.dxf.name in ep_blocks:
                walk(e.virtual_entities(), d + 1)
            elif e.dxf.layer.lower().startswith("ak_ep") and e.dxftype() in ("LWPOLYLINE", "POLYLINE", "LINE"):
                pts = [world_to_svg(v.x, v.y) for v in zpath.make_path(e).flattening(50)]
                if len(pts) > 1:
                    band = "lt50" if "less" in e.dxf.layer.lower() else "50-60"
                    egress.append(dict(band=band, m=round(LineString(pts).length / 1000, 1),
                                       d="M" + "L".join(f"{round(x)} {round(y)}" for x, y in pts)))
    walk(msp)
    print(f"egress paths: {len(egress)}", collections.Counter(e["band"] for e in egress))

    # ---- a drawing with its spaces on named layers (AC_*: the 22.10.26 drawing): the spaces, neighbourhoods and workstation
    # types come straight from the layers (tools/acko/named_layers.py); otherwise each room label is snapped into its walls ----
    import named_layers as NL
    named = any(str(sp.get("layer", "")).startswith("AC_") for sp in json.load(open(os.path.join(tk, "rooms.json"), encoding="utf-8"))["spaces"])
    prev_tk = os.path.join(os.path.dirname(tk), "tf2110")          # the previous drawing: its neighbourhood numbers and egress paths
    shift, types = (0.0, 0.0, 1.0), []
    COL = dict(LEGEND + EXTRA_COLOURS)
    COL.setdefault("Pantry", COL.get("Cafeteria", "E4E2DD"))         # the cafeteria's back of house, in its colour
    if named:
        shift = NL.frame_shift(tk, prev_tk) if os.path.exists(os.path.join(prev_tk, "full.svg")) else (0.0, 0.0, 0.0)
        print(f"frame check against the previous drawing: shift {shift[0]:.0f}, {shift[1]:.0f} mm (response {shift[2]:.2f})")
        out_spaces = NL.spaces(tk, labels, COL, TYPE_CAP)
        print(f"spaces: {len(out_spaces)}", collections.Counter(sp["type"] for sp in out_spaces).most_common())
        types = NL.types(tk)
        print("workstation types:", [(t["name"], len(t["uses"])) for t in types])
        import faces as FC
        check_spaces(FC.partition_lines(open(full, encoding="utf-8").read())[0], out_spaces, crop)
    else:
        # ---- spaces: each room label in the room its walls enclose ----
        import faces as FC
        from shapely.strtree import STRtree
        svg = open(full, encoding="utf-8").read()
        rings_of = lambda d: [pts for part in re.findall(r"M([^M]+)", d)
                              for nums in [list(map(float, re.findall(r"-?\d+(?:\.\d+)?", part)))]
                              for pts in [[(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]] if len(pts) > 2]
        zone_polys = [Polygon(r).buffer(0) for t in json.load(open(os.path.join(tk, "teams.json")))["teams"] for r in rings_of(t["zone"])]
        room_polys = [Polygon(r).buffer(0) for sp in json.load(open(os.path.join(tk, "rooms.json"), encoding="utf-8"))["spaces"]
                      if sp["name"] != "Not in contract" for r in rings_of(sp["d"])]
        plate = FC.floor_plate(zone_polys, room_polys)                    # the neighbourhoods and the toolkit's rooms: the floor
        lines, ndoors = FC.partition_lines(svg, plate)                    # its outline as the outside wall
        LV = FC.levels(lines)
        ltree = STRtree(lines)
        print(f"partition lines {len(lines)} ({ndoors} doorways shut, the floor plate {plate.area / 1e6:.0f} m2 as the outside wall); "
              "faces " + ", ".join(f"{g} mm: {len(fs)}" for g, fs, _ in LV))
        # the previous drawing's spaces (Option 02A, snapped to its walls), kept once in tools/_work/plan/prev-spaces.json so re-runs
        # compare against the same reference: their areas cap a leaky face, their outlines stand in for open-plan labels with none
        prev, keep = {}, os.path.join(WORK, "prev-spaces.json")
        try:
            if not os.path.exists(keep):
                pj = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
                json.dump(json.loads(pj[pj.index("{"):pj.rindex("}") + 1])["spaces"], open(keep, "w", encoding="utf-8"))
            for sp in json.load(open(keep, encoding="utf-8")):
                prev.setdefault(sp["name"].upper(), []).append(sp)
        except Exception:
            pass
        rooms, unplaced, carried = {}, [], []
        for t, x, y, ins in labels:
            typ = next((n for n, rx in BY_LABEL if re.search(rx, t, re.I)), None)
            # the largest a room of its kind can be (m2), and no more than 1.6x what the same room measured in the previous build: a
            # face bigger than that has leaked through a gap, so the next (wider-bridging) level is tried, else the previous outline
            hi = TYPE_CAP.get(typ, 200) * 1e6
            same = prev.get(re.sub(r"\s*-\s*", " - ", title(t)).upper(), [])
            old = min(same, key=lambda q: (q["x"] - x) ** 2 + (q["y"] - y) ** 2) if same else None   # the same-named room nearest this label
            if old is not None and ((old["x"] - x) ** 2 + (old["y"] - y) ** 2) > 15000 ** 2: old = None
            if old is not None and old.get("m2", 0) >= TYPE_MIN.get(typ, 0.8): hi = min(hi, max(old["m2"] * 1.6, old["m2"] + 4) * 1e6)
            pax = re.search(r"(\d+)\s*PAX", t, re.I)
            lo = max(TYPE_MIN.get(typ, 0.8), 0.9 * int(pax.group(1)) if pax else 0) * 1e6     # a table is never the room
            poly = gap = None
            for pt in ((x, y), ins):
                poly, gap = FC.room_at(pt, LV, lo=lo, hi=max(hi, lo * 1.5))
                if poly is not None: break
            if poly is None:
                if old is not None:
                    rings = [[tuple(map(float, q.split())) for q in part.split("L")] for part in re.findall(r"M([^Z]+)Z", old["d"])]
                    poly = unary_union([Polygon(r).buffer(0) for r in rings if len(r) > 2]); gap = "prev"
                    if not poly.buffer(300).contains(Point(x, y)):     # the same name somewhere else in the old plan: not this room
                        unplaced.append(f"{t} (previous outline elsewhere)"); continue
                    # how well the carried outline sits on the new drawing's walls: its vertices' median distance to a partition line
                    ds = sorted(min((lines[j].distance(Point(c)) for j in ltree.query(Point(c).buffer(1500))), default=1500)
                                for g_ in (poly.geoms if hasattr(poly, "geoms") else [poly]) for c in list(g_.exterior.coords)[::2])
                    # an open-plan room has open sides with no wall near them: half its edge on the new walls is enough; less, and
                    # that part of the plan changed (no outline beats a wrong one)
                    on = sum(1 for v in ds if v <= 250) / max(len(ds), 1)
                    if typ in OPEN_PLAN and on < 0.5:     # an open-plan area: its old outline, trimmed to the open floor it's in
                        big = [fs[i] for g_, fs, tr_ in LV[:1] for i in tr_.query(Point(x, y)) if fs[i].contains(Point(x, y))]
                        if big:
                            poly = poly.intersection(big[0]).buffer(0); on = 1.0
                    if on < 0.5:
                        unplaced.append(f"{t} (previous outline: {on:.0%} of it on the new walls)"); continue
                    carried.append(f"{t} ({on:.0%} on the walls)")
            if poly is None:
                unplaced.append(t); continue
            key = (round(poly.area), round(poly.bounds[0]), round(poly.bounds[1]))
            r = rooms.setdefault(key, dict(poly=poly, labels=[], gap=gap))
            r["labels"].append((t, x, y))
        for rj in json.load(open(os.path.join(tk, "rooms.json"), encoding="utf-8"))["spaces"]:
            if rj["name"] == "Not in contract":
                for part in re.findall(r"M([^M]+)", rj["d"]):
                    nums = list(map(float, re.findall(r"-?\d+(?:\.\d+)?", part)))
                    pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
                    if len(pts) > 2:
                        g = Polygon(pts).buffer(0)
                        rooms[("nic", round(g.area))] = dict(poly=g, labels=[], gap="nic", typ="Not in contract")
        out_spaces = []
        for i, r in enumerate(sorted(rooms.values(), key=lambda r: (r["poly"].centroid.x, r["poly"].centroid.y))):
            names = list(dict.fromkeys(re.sub(r"\s*-\s*", " - ", title(t)) for t, x, y in r["labels"]))
            typ = r.get("typ") or next((n for n, rx in BY_LABEL for t, x, y in r["labels"] if re.search(rx, t, re.I)), None) or "Room"
            if typ == "Cafeteria" and not any(re.search(r"CAFE", t, re.I) for t, x, y in r["labels"]):
                names = ["Cafeteria"]          # the dining floor, labelled only by its counters (heating station, waste disposal)
            at = (r["labels"][0][1], r["labels"][0][2]) if r["labels"] else r["poly"].representative_point().coords[0]
            if not r["poly"].buffer(300).contains(Point(at)): at = r["poly"].representative_point().coords[0]
            g = r["poly"].simplify(10)
            out_spaces.append(dict(id=f"r{i + 1}", type=typ, name=" / ".join(names) or typ, colour="#" + COL.get(typ, "E4E2DD"),
                                   m2=round(g.area / 1e6, 1), x=round(at[0]), y=round(at[1]), d=d_of(g)))
        print(f"spaces: {len(out_spaces)}", collections.Counter(s["type"] for s in out_spaces).most_common())
        print(f"by gap: {collections.Counter(str(r['gap']) for r in rooms.values())}; carried from the previous build: {carried}")
        print("labels not placed:", unplaced)
        check_spaces(lines, out_spaces, crop)

    if named:
        zones = NL.zones(tk, prev_tk, shift, (OX, OY))
        for z in zones:
            g = NL.poly_of(z["zone"])
            z["box"] = [round(v) for v in g.bounds]
            z["occ"] = occupancy(z, g, out_spaces)
            print(f"  {z['name']} (overlap with the old zone {z['overlap']:.0%}): {z['seats']} seats · " + ", ".join(f"{a} {n}" for grp, a, n in z["occ"][1:]))
        print("zones total", sum(z["seats"] for z in zones))
    else:
        # ---- neighbourhoods ----
        tj = json.load(open(os.path.join(tk, "teams.json")))
        zones = [dict(id=t["id"], n=re.sub(r"\D", "", t["name"]) or t["name"], name=t["name"], seats=t["seats"], m2=t["m2"],
                      x=t["x"], y=t["y"], zone=t["zone"], desks=t["desks"]) for t in tj["teams"]]
        zones.sort(key=lambda z: z["n"])
        print("zones:", [(z["n"], z["seats"]) for z in zones], "total", sum(z["seats"] for z in zones))
        # each neighbourhood's box (for the zoom) and its occupancy chart: the deck's slide-61 rows, for what lies inside it
        for z in zones:
            rings = [[tuple(map(float, q.split())) for q in part.split("L")] for part in re.findall(r"M([^Z]+)Z", z["zone"])]
            g = unary_union([Polygon(r).buffer(0) for r in rings if len(r) > 2])
            z["box"] = [round(v) for v in g.bounds]
            z["occ"] = occupancy(z, g, out_spaces)
            print(f"  {z['name']}: " + ", ".join(f"{a} {n}" for grp, a, n in z["occ"]))

    # ---- the deck's own marks, onto the DXF ----
    dp = open(os.path.join(ROOT, "data", "deck-plan.js"), encoding="utf-8").read()
    D = json.loads(dp[dp.index("{"):dp.rindex("}") + 1])
    f2s = lambda fx, fy: (lambda w: tuple(round(v) for v in world_to_svg(w[0] + shift[0], w[1] + shift[1])))(frame_to_world(fx, fy))
    blow = {}
    for k, (x0, y0, x1, y1) in D["blow"].items():
        (ax, ay), (bx, by) = f2s(x0, y0), f2s(x1, y1)
        blow[k] = [ax, ay, bx - ax, by - ay]
    overlays = dict(blow=blow,
                    # the compartment line only: segments on the plan (the slide's legend sample sits below it)
                    fire=[f for f in ([*f2s(*s[0]), *f2s(*s[1])] for s in D["fire"])
                          if all(crop[0] <= f[i] <= crop[0] + crop[2] and crop[1] <= f[i + 1] <= crop[1] + crop[3] for i in (0, 2))],
                    entry=[list(f2s(*e)) for e in D["entry"]],
                    arrival=["M" + "L".join(f"{x} {y}" for x, y in (f2s(*p) for p in n["pts"])) + "Z" for n in D["nb"] if n["c"].upper() == "#0000FF"])

    if named:
        # no egress layer in this drawing: the previous drawing's paths (kept once in world coordinates), when the frames line
        # up (a clear wall match); the arrival zones are the drawing's own lift lobbies
        keep = os.path.join(WORK, "prev-egress-world.json")
        if not os.path.exists(keep):
            pj = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
            old = json.loads(pj[pj.index("{"):pj.rindex("}") + 1])
            head0 = open(os.path.join(prev_tk, "full.svg"), encoding="utf-8").read(600)
            pox = float(re.search(r'data-ox="(-?[\d.]+)"', head0).group(1)); poy = float(re.search(r'data-oy="(-?[\d.]+)"', head0).group(1))
            json.dump([dict(band=e["band"], m=e["m"], pts=[(x + pox, poy - y) for x, y in (tuple(map(float, q.split())) for q in e["d"][1:].split("L"))])
                       for e in old.get("egress", [])], open(keep, "w"))
        if not egress and shift[2] > 0.3:                  # a clear wall match: the two drawings line up (a CAD move is fine)
            for e in json.load(open(keep)):
                pts = [world_to_svg(x + shift[0], y + shift[1]) for x, y in e["pts"]]
                egress.append(dict(band=e["band"], m=e["m"], d="M" + "L".join(f"{round(x)} {round(y)}" for x, y in pts)))
            print(f"egress: {len(egress)} paths carried over from the previous drawing (shifted {shift[0]:.0f}, {shift[1]:.0f} mm)")
        elif not egress:
            print("egress: none (no egress layer, and the previous drawing doesn't line up)")
        lobbies = [sp["d"] for sp in out_spaces if sp["type"] == "Lift lobby"]
        if lobbies:
            overlays["arrival"] = lobbies
    data = dict(source=os.path.basename(dxf_path), built=time.strftime("%Y-%m-%d %H:%M"), viewBox=crop,
                levels=[dict(ppm=p, src=f"assets/img/plan-dxf-{p}.webp") for p in LEVELS], floor=None,
                spaces=out_spaces, zones=zones, egress=egress, overlays=overlays, types=types)
    with open(os.path.join(ROOT, "data", "plan-dxf.js"), "w", encoding="utf-8") as f:
        f.write(f"/* generated by tools/acko/plan_dxf.py from the DXF plan toolkit's output for {os.path.basename(dxf_path)}: don't hand-edit */\n")
        f.write("window.PLAN_DXF = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"data/plan-dxf.js {os.path.getsize(os.path.join(ROOT, 'data', 'plan-dxf.js')) / 1e6:.2f} MB  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(*sys.argv[1:3])
