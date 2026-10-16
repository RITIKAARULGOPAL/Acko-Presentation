"""The layout as the deck draws it (slides 53–57), as one zoomable plan until the DXF arrives.

  * assets/img/plan-full.webp: the four plan tiles of slide 53 (Blown up X in two parts, Y, Z) set side by side at their
    slide positions, at the tiles' own resolution
  * data/deck-plan.js (window.DECK_PLAN): in slide-53 pixels (1920 × 1080 frame):
      img   where plan-full.webp sits
      nb    the six neighbourhood outlines of slide 54 (vector, with the deck's colours) and their seat labels
      blow  the Blown up X / Y / Z boxes (the dashed dividers of slide 53)
      fire  the fire compartment line of slide 56, mapped back from the Y blow-up onto the whole floor
      entry the two arrival triangles

    python tools/acko/deck_plan.py "<deck.pptx>"
"""
import io, json, os, re, sys, zipfile
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMU_W, EMU_H, FW, FH = 9144000, 5143500, 1920, 1080
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def px(x, y):
    return (x / EMU_W * FW, y / EMU_H * FH)


def xfrm(s):
    o = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"', s)
    return [int(v) for v in o.groups()]


def cust_paths(s):
    """custGeom → list of point lists in frame px (no rotation used on these shapes)"""
    X, Y, W, H = xfrm(s)
    out = []
    for pm in re.finditer(r'<a:path[^>]*h="(\d+)"[^>]*w="(\d+)"[^>]*>(.*?)</a:path>', s, re.S):
        ph, pw, body = int(pm.group(1)), int(pm.group(2)), pm.group(3)
        pts = [(X + int(a) / pw * W, Y + int(b) / ph * H) for a, b in re.findall(r'<a:pt x="(-?\d+)" y="(-?\d+)"/>', body)]
        out.append({"pts": [tuple(round(v, 1) for v in px(*p)) for p in pts], "closed": "<a:close/>" in body})
    return out


def main():
    deck = sys.argv[1]
    z = zipfile.ZipFile(deck)
    inv = json.load(open(os.path.join(ROOT, "tools", "_media", "inventory.json")))

    # 1 · the tiles, composed at the finest tile's scale (source px per frame px)
    tiles = {"image206.png": None, "image212.png": None, "image208.png": None, "image209.png": None}
    for r in inv["53"]:
        if r["media"] in tiles:
            tiles[r["media"]] = r["box"]
    boxes = {m: [b[0] / 100 * FW, b[1] / 100 * FH, b[2] / 100 * FW, b[3] / 100 * FH] for m, b in tiles.items()}
    ims = {m: Image.open(io.BytesIO(z.read("ppt/media/" + m))).convert("RGBA") for m in tiles}
    k = max(ims[m].width / boxes[m][2] for m in tiles)
    x0 = min(b[0] for b in boxes.values()); y0 = min(b[1] for b in boxes.values())
    x1 = max(b[0] + b[2] for b in boxes.values()); y1 = max(b[1] + b[3] for b in boxes.values())
    canvas = Image.new("RGBA", (round((x1 - x0) * k), round((y1 - y0) * k)), (255, 255, 255, 0))
    for m, b in boxes.items():
        im = ims[m].resize((round(b[2] * k), round(b[3] * k)), Image.LANCZOS)
        canvas.alpha_composite(im, (round((b[0] - x0) * k), round((b[1] - y0) * k)))
    bg = Image.new("RGB", canvas.size, (255, 255, 255)); bg.paste(canvas, mask=canvas.split()[3])
    bg.save(os.path.join(ROOT, "assets", "img", "plan-full.webp"), "WEBP", quality=88, method=6)
    print("plan-full.webp", bg.size, os.path.getsize(os.path.join(ROOT, "assets", "img", "plan-full.webp")) // 1024, "KB")

    # 2 · the neighbourhood outlines (slide 54) and their labels
    x54 = z.read("ppt/slides/slide54.xml").decode("utf8")
    nb = []
    for s in re.findall(r"<p:sp>.*?</p:sp>", x54, re.S):
        if "custGeom" not in s:
            continue
        ln = re.search(r"<a:ln[^>]*>(.*?)</a:ln>", s, re.S)
        col = re.findall(r'srgbClr val="(\w+)"', ln.group(1)) if ln else []
        if not col:
            continue
        w = re.search(r'<a:ln[^>]*w="(\d+)"', s)
        for p in cust_paths(s):
            nb.append({"c": "#" + col[0], "w": round(int(w.group(1)) / 12700, 2) if w else 1.5, **p})
    labels = []
    for s in re.findall(r"<p:sp>.*?</p:sp>", x54, re.S):
        t = "".join(re.findall(r"<a:t>([^<]*)</a:t>", s)).strip()
        m = re.fullmatch(r"(0[1-6])\s*(\d+)", t)
        if m:
            X, Y, W, H = xfrm(s)
            labels.append({"n": m.group(1), "seats": int(m.group(2)), "at": [round(v, 1) for v in px(X, Y)], "wh": [round(W / EMU_W * FW, 1), round(H / EMU_H * FH, 1)]})

    # 3 · the blow-up dividers (dashed connectors on slide 53) → three boxes over the plan
    x53 = z.read("ppt/slides/slide53.xml").decode("utf8")
    cuts = sorted({round(px(xfrm(s)[0], 0)[0], 1) for s in re.findall(r"<p:cxnSp>.*?</p:cxnSp>", x53, re.S)})
    blow = {"X": [x0, y0, cuts[0], y1], "Y": [cuts[0], y0, cuts[1], y1], "Z": [cuts[1], y0, x1, y1]} if len(cuts) == 2 else {}

    # 4 · the fire compartment line (slide 56, in the Y blow-up) mapped back onto the floor: Y sits at its slide-53 box
    yb53 = boxes["image208.png"]
    yb56 = next(r["box"] for r in inv["56"] if r["media"] == "image208.png" and r["box"][2] > 50)
    yb56 = [yb56[0] / 100 * FW, yb56[1] / 100 * FH, yb56[2] / 100 * FW, yb56[3] / 100 * FH]
    to53 = lambda p: (round(yb53[0] + (p[0] - yb56[0]) / yb56[2] * yb53[2], 1), round(yb53[1] + (p[1] - yb56[1]) / yb56[3] * yb53[3], 1))
    x56 = z.read("ppt/slides/slide56.xml").decode("utf8")
    fire = []
    for r in inv["56"]:                                    # the red dashed picture pieces: vertical runs
        if r["media"] == "image223.png":
            bx, by, bw, bh = (r["box"][0] / 100 * FW, r["box"][1] / 100 * FH, r["box"][2] / 100 * FW, r["box"][3] / 100 * FH)
            fire.append([to53((bx + bw / 2, by)), to53((bx + bw / 2, by + bh))])
    for s in re.findall(r"<p:(?:sp|cxnSp)>.*?</p:(?:sp|cxnSp)>", x56, re.S):   # and the maroon line shapes between them
        if "980000" in s and ("Connector" in s or "line" in s):
            X, Y, W, H = xfrm(s)
            flipV = 'flipV="1"' in s
            a, b = px(X, Y + (H if flipV else 0)), px(X + W, Y + (0 if flipV else H))
            fire.append([to53(a), to53(b)])

    # 5 · the arrival triangles (image214 on slide 53)
    entry = [[round(r["box"][0] / 100 * FW + r["box"][2] / 200 * FW, 1), round(r["box"][1] / 100 * FH + r["box"][3] / 200 * FH, 1)] for r in inv["53"] if r["media"] == "image214.png"]

    data = {"frame": [FW, FH], "img": {"src": "assets/img/plan-full.webp", "box": [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]},
            "nb": nb, "labels": labels, "blow": {k2: [round(v, 1) for v in b] for k2, b in blow.items()}, "fire": fire, "entry": entry}
    with open(os.path.join(ROOT, "data", "deck-plan.js"), "w") as f:
        f.write("/* generated by tools/acko/deck_plan.py from the design deck's layout slides (53–57): slide-53 pixels, 1920 × 1080 */\n")
        f.write("window.DECK_PLAN = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"{len(nb)} outline paths, labels {[(l['n'], l['seats']) for l in labels]}, blow-ups {list(blow)}, fire pieces {len(fire)}, entries {len(entry)}")


if __name__ == "__main__":
    main()
