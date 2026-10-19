"""The layout plan from the DXF, for s-layout and s-blowup: pictures of the plan, its spaces, neighbourhoods and fire egress.

    python tools/acko/plan_dxf.py "<toolkit>/viewer/out/op2a" "<ACKO.dxf>" "<deck.pptx>"

Reads the DXF plan toolkit's output for the drawing (full.svg, teams.json: run the toolkit first, with
projects/acko.json), the DXF itself and the design deck, and writes:
  assets/img/plan-dxf-12.webp, -24.webp, -48.webp   the plan drawn at 12 / 24 / 48 px per metre (transparent), so the
                                                     deck can show it sharp at every zoom (the full vector plan is too
                                                     heavy to fly smoothly)
  data/plan-dxf.js (window.PLAN_DXF), in the toolkit's plan frame (mm, y down):
    viewBox   the plan's crop [x, y, w, h]
    levels    the pictures and their px per metre
    spaces    the spaces as the deck's layout slide (53) colours them by its legend: every flat fill patch of the slide's
              plan tiles, registered onto the DXF plan, named by the DXF room label inside it and typed by that name or by
              the legend colour; each keeps its slide colour
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
          ("Quick sprint", "CED2CF"), ("Cafeteria", "CEDED1"), ("Training room", "B6AFAF"), ("The Hatchery", "CCD5CB"),
          ("Studio", "E5DEDE"), ("Phone booth", "D5CEED"), ("Collab", "A5B0AB"), ("Executive corner cabin", "D3D9C5"),
          ("Prayer room", "A19DAD"), ("Coffee corner", "BAB0C1"), ("Hub room", "EAE8F1"), ("Mother's room", "E0DFDD"),
          ("Zen room", "F4F3EF"), ("Server, UPS & battery", "929292")]
BY_LABEL = [("Boardroom", r"BOARD"), ("Departmental room", r"DEPARTMENTAL"), ("Collaboration huddle", r"HUDDLE"),
            ("Quick sprint", r"SPRINT|^\d+ PAX"), ("Visitor hub", r"VISITOR"), ("Phone booth", r"^PB\b"), ("Zen room", r"ZEN"),
            ("Hub room", r"HUB ROOM"), ("Mother's room", r"MOTHER"), ("Prayer room", r"PRAYER"), ("Studio", r"STUDIO"),
            ("The Hatchery", r"HATCHERY"), ("Executive corner cabin", r"EXECUTIVE"), ("Training room", r"TRAINING"),
            ("Cafeteria", r"CAFE|PANTRY|HEATING|DISHWASH|PLATE DROP|WASTE"), ("Reception", r"RECEPTION"), ("Coffee corner", r"COFFEE"),
            ("Server, UPS & battery", r"SERVER|UPS|BATTERY|ELECTRICAL|BMS"), ("Mail room", r"MAIL"), ("Store room", r"STORE")]
NOISE = r"[\d\s.-]+|DT|SMR\d+|MHS|ACD|FHS|PUNCH BAG|SWING CHAIR|DIGITAL SCREEN|COMMUNITY TABLE|1500MM WIDE CORRIDOR|ACD CAN BE PROVIDED HERE|SEATING AND SWING"


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.int16)


def legend_type(col):
    c = hexrgb(col); best = min(LEGEND, key=lambda t: int(np.abs(hexrgb(t[1]) - c).max()))
    return best[0] if int(np.abs(hexrgb(best[1]) - c).max()) <= 4 else None


def d_of(poly):
    out = []
    for g in (poly.geoms if hasattr(poly, "geoms") else [poly]):
        for r in [g.exterior] + list(g.interiors):
            pts = list(r.coords)[:-1]
            out.append("M" + "L".join(f"{round(x)} {round(y)}" for x, y in pts) + "Z")
    return "".join(out)


def main(tk, dxf_path, deck):
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

    # ---- the DXF: room labels and the egress paths ----
    doc = ezdxf.readfile(dxf_path); msp = doc.modelspace()
    labels = []
    for e in msp.query("MTEXT TEXT"):
        if e.dxf.layer != "OB-I-ANNO-TEXT":
            continue
        t = re.sub(r"\s+", " ", e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).strip()
        if t and not re.fullmatch(NOISE, t, re.I):
            labels.append((t, *world_to_svg(e.dxf.insert.x, e.dxf.insert.y)))
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

    # ---- spaces from the slide's legend colours ----
    PPM = 24
    ref = np.array(Image.open(os.path.join(WORK, "plan-24.png")))
    ref_ink = (ref[..., 3] > 100).astype(np.float32)
    svg_to_ref = lambda x, y: ((x - crop[0]) / 1000 * PPM, (y - crop[1]) / 1000 * PPM)
    def frame_to_ref(fx, fy):
        return svg_to_ref(*world_to_svg(*frame_to_world(fx, fy)))
    z = zipfile.ZipFile(deck)
    inv = json.load(open(os.path.join(ROOT, "tools", "_media", "inventory.json")))
    boxes = {r["media"]: [r["box"][0] / 100 * FW, r["box"][1] / 100 * FH, r["box"][2] / 100 * FW, r["box"][3] / 100 * FH] for r in inv["53"] if r["media"] in TILES}
    patches = []
    floor = np.zeros(ref_ink.shape, np.uint8)        # the workhall floor (the slide's grey), as a picture beneath the spaces
    for ti, m in enumerate(TILES):
        rgb = np.array(Image.open(io.BytesIO(z.read("ppt/media/" + m))).convert("RGB"))
        th, tw = rgb.shape[:2]; bx, by, bw, bh = boxes[m]
        (ax, ay), (bx2, by2) = frame_to_ref(bx, by), frame_to_ref(bx + bw, by + bh)
        A = np.array([[(bx2 - ax) / tw, 0, ax], [0, (by2 - ay) / th, ay]], np.float64)
        # a small shift onto the DXF lines: phase correlation of the two ink images over the tile's footprint
        ink = (rgb.max(2) < 110).astype(np.float32)
        warped = cv2.warpAffine(ink, A.astype(np.float32), (ref_ink.shape[1], ref_ink.shape[0]))
        foot = cv2.warpAffine(np.ones_like(ink), A.astype(np.float32), (ref_ink.shape[1], ref_ink.shape[0])) > .5
        fy_, fx_ = np.where(foot); x0, x1, y0, y1 = fx_.min(), fx_.max(), fy_.min(), fy_.max()
        ra, rb = cv2.GaussianBlur(ref_ink[y0:y1, x0:x1], (0, 0), 2), cv2.GaussianBlur(warped[y0:y1, x0:x1], (0, 0), 2)
        (dx, dy), _ = cv2.phaseCorrelate(rb, ra, cv2.createHanningWindow((ra.shape[1], ra.shape[0]), cv2.CV_32F))
        if abs(dx) < 40 and abs(dy) < 40:
            A[0, 2] += dx; A[1, 2] += dy
        print(f"  {m}: shift ({dx:+.1f}, {dy:+.1f}) px")
        fm = (np.abs(rgb.astype(int) - (0xE2, 0xE2, 0xE1)).max(2) <= 2).astype(np.uint8)
        fm = cv2.morphologyEx(fm, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        floor = np.maximum(floor, cv2.warpAffine(fm, A.astype(np.float32), (floor.shape[1], floor.shape[0]), flags=cv2.INTER_NEAREST))
        # flat fill colours (not white, black or the workhall floor), near shades merged
        cols, counts = np.unique(rgb.reshape(-1, 3), axis=0, return_counts=True)
        groups = []
        for c, n in sorted(zip(map(tuple, cols.astype(int)), counts), key=lambda t: -t[1]):
            if n < 300 or min(c) > 246 or max(c) < 120 or max(abs(c[i] - (0xE2, 0xE2, 0xE1)[i]) for i in range(3)) <= 3 \
                    or (max(c) - min(c) < 3 and min(c) > 238):
                continue
            g = next((g for g in groups if max(abs(c[i] - g["c"][i]) for i in range(3)) <= 2), None)
            if g: g["cols"].append(c)
            else: groups.append(dict(c=c, cols=[c]))
        for g in groups:
            mask = np.zeros((th, tw), np.uint8)
            for c in g["cols"]:
                mask |= np.all(np.abs(rgb.astype(int) - c) <= 1, axis=2).astype(np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            booth = legend_type("%02X%02X%02X" % g["c"]) == "Phone booth" or (g["c"][2] > g["c"][0] + 20 and g["c"][2] > g["c"][1] + 20)
            for c in cnts:
                if cv2.contourArea(c) < (30 if booth else 120):
                    continue
                c = cv2.approxPolyDP(c, 1.0, True).reshape(-1, 2).astype(np.float64)
                if len(c) < 3:
                    continue
                P = (A[:, :2] @ c.T).T + A[:, 2]
                poly = Polygon([(crop[0] + x / PPM * 1000, crop[1] + y / PPM * 1000) for x, y in P]).buffer(0)
                if isinstance(poly, MultiPolygon):
                    poly = max(poly.geoms, key=lambda h: h.area)
                if booth and poly.area >= 0.2e6:             # phone booths: small lilac pods, grown a little to hover
                    patches.append(dict(tile=ti, colour="%02X%02X%02X" % g["c"], poly=poly.buffer(150, join_style=2), booth=True))
                elif poly.area >= 0.9e6:
                    patches.append(dict(tile=ti, colour="%02X%02X%02X" % g["c"], poly=poly))
    fl = np.zeros((*floor.shape, 4), np.uint8); fl[floor > 0] = (0xE2, 0xE2, 0xE1, 255)
    Image.fromarray(fl).save(os.path.join(ROOT, "assets", "img", "plan-dxf-floor.webp"), "WEBP", quality=80, method=6)
    print(f"  plan-dxf-floor.webp {os.path.getsize(os.path.join(ROOT, 'assets', 'img', 'plan-dxf-floor.webp')) / 1e3:.0f} KB")
    # names: the label inside; a pod's label often sits just outside it (nearest within 1.2 m)
    for p in patches:
        p["labels"] = [l for l in labels if p["poly"].contains(Point(l[1], l[2]))]
    used = {id(l) for p in patches for l in p["labels"]}
    for l in labels:
        if id(l) in used:
            continue
        q = Point(l[1], l[2])
        near = sorted((p["poly"].distance(q), i) for i, p in enumerate(patches) if not p["labels"] and p["poly"].distance(q) <= 1200)
        if near:
            patches[near[0][1]]["labels"].append(l); used.add(id(l))
    spaces = []
    for p in patches:
        names = list(dict.fromkeys(re.sub(r"\s*-\s*", " - ", t.title().replace("Pax", "PAX").replace("Pb ", "PB ")) for t, x, y in p["labels"]))
        typ = next((n for n, rx in BY_LABEL for t, x, y in p["labels"] if re.search(rx, t, re.I)), None) or legend_type(p["colour"])               or ("Phone booth" if p.get("booth") else None)
        if not typ or (not names and p["poly"].area < 4e6 and not p.get("booth")):
            continue
        spaces.append(dict(tile=p["tile"], type=typ, name=" / ".join(names) or typ, colour=p["colour"], poly=p["poly"],
                           at=(p["labels"][0][1], p["labels"][0][2]) if p["labels"] else None))
    # one space cut by a tile edge: same type, touching across the seam
    merged = True
    while merged:
        merged = False
        for i in range(len(spaces)):
            for j in range(i + 1, len(spaces)):
                a, b = spaces[i], spaces[j]
                if a["tile"] != b["tile"] and a["type"] == b["type"] and a["poly"].buffer(400).intersects(b["poly"]) and \
                        (a["name"] == a["type"] or b["name"] == b["type"] or a["name"] == b["name"]):
                    g = unary_union([a["poly"].buffer(450), b["poly"].buffer(450)]).buffer(-450)
                    a["poly"] = max(g.geoms, key=lambda h: h.area) if isinstance(g, MultiPolygon) else g
                    if a["name"] == a["type"]: a["name"], a["at"] = b["name"], b["at"]
                    del spaces[j]; merged = True; break
            if merged: break
    out_spaces = []
    for i, s in enumerate(sorted(spaces, key=lambda s: (s["poly"].centroid.x, s["poly"].centroid.y))):
        at = s["at"] or s["poly"].representative_point().coords[0]
        if not s["poly"].buffer(300).contains(Point(at)):
            at = s["poly"].representative_point().coords[0]
        out_spaces.append(dict(id=f"r{i + 1}", type=s["type"], name=s["name"], colour="#" + s["colour"], m2=round(s["poly"].area / 1e6, 1),
                               x=round(at[0]), y=round(at[1]), d=d_of(s["poly"].simplify(40))))
    print(f"spaces: {len(out_spaces)}", collections.Counter(s["type"] for s in out_spaces).most_common())
    print("labels without a space:", sorted({t for t, x, y in labels if not any(t == l[0] for p in patches for l in p["labels"])}))

    # ---- neighbourhoods ----
    tj = json.load(open(os.path.join(tk, "teams.json")))
    zones = [dict(id=t["id"], n=re.sub(r"\D", "", t["name"]) or t["name"], name=t["name"], seats=t["seats"], m2=t["m2"],
                  x=t["x"], y=t["y"], zone=t["zone"], desks=t["desks"]) for t in tj["teams"]]
    zones.sort(key=lambda z: z["n"])
    print("zones:", [(z["n"], z["seats"]) for z in zones], "total", sum(z["seats"] for z in zones))

    # ---- the deck's own marks, onto the DXF ----
    dp = open(os.path.join(ROOT, "data", "deck-plan.js"), encoding="utf-8").read()
    D = json.loads(dp[dp.index("{"):dp.rindex("}") + 1])
    f2s = lambda fx, fy: tuple(round(v) for v in world_to_svg(*frame_to_world(fx, fy)))
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

    data = dict(source=os.path.basename(dxf_path), built=time.strftime("%Y-%m-%d %H:%M"), viewBox=crop,
                levels=[dict(ppm=p, src=f"assets/img/plan-dxf-{p}.webp") for p in LEVELS], floor="assets/img/plan-dxf-floor.webp",
                spaces=out_spaces, zones=zones, egress=egress, overlays=overlays)
    with open(os.path.join(ROOT, "data", "plan-dxf.js"), "w", encoding="utf-8") as f:
        f.write("/* generated by tools/acko/plan_dxf.py from the DXF plan toolkit's output for ACKO.dxf: don't hand-edit */\n")
        f.write("window.PLAN_DXF = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(f"data/plan-dxf.js {os.path.getsize(os.path.join(ROOT, 'data', 'plan-dxf.js')) / 1e6:.2f} MB  ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
