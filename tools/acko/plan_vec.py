"""The plan's own linework, as vector tiles, for when the layout is zoomed in past its sharpest picture.

Usage:  python tools/acko/plan_vec.py "<toolkit>/viewer/out/op2a"

Reads the DXF plan toolkit's full.svg (the drawing the toolkit's viewer shows: every path classed s/f/m/h + wall, glass,
door, furn, green, base, shade, anno; the room labels as text) and writes data/plan-vec.js (window.PLAN_VEC):
  tile    the grid (mm); frame: the deck's plan frame (data/plan-dxf.js viewBox)
  tiles   [{b: [x0, y0, x1, y1] (everything in it, mm), s: its markup}]
Each subpath goes to the tile of its first point; a tile keeps the drawing's paint order (a wipeout still masks what was
drawn before it), its consecutive same-class paths merged, coordinates relative after each subpath's first point.
The deck draws a tile with the plan component's .ph-plan styles (non-scaling strokes, the viewer's colours) once the zoom
needs more than the 48 px/m picture holds (app.js, deckPlan / level).
"""
import json, math, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOK = re.compile(r"[MLC]|-?\d+(?:\.\d+)?(?:e-?\d+)?")
TILE = 12000


def pairs(nums):
    """a run of relative numbers, written as SVG packs them (no space before a minus)"""
    out = ""
    for n in nums:
        s = str(n)
        out += s if (not out or s.startswith("-") or out.endswith(("l", "c"))) else " " + s
    return out


def subpaths(d):
    """[(points, relative d)] for each subpath; the toolkit writes only M, L and C"""
    res, t, i, cmd = [], TOK.findall(d), 0, None
    pts, enc, cx, cy, last = None, None, 0, 0, None
    while i < len(t):
        k = t[i]
        if k in ("M", "L", "C"):
            cmd = k; i += 1; continue
        if cmd == "M":
            if pts: res.append((pts, enc))
            x, y = round(float(t[i])), round(float(t[i + 1])); i += 2
            pts, enc, cx, cy, last, cmd = [(x, y)], f"M{x} {y}", x, y, None, "L"
        elif cmd == "L":
            x, y = round(float(t[i])), round(float(t[i + 1])); i += 2
            enc = (enc + "l" + pairs([x - cx, y - cy])) if last != "l" else pairs_join(enc, [x - cx, y - cy])
            pts.append((x, y)); cx, cy, last = x, y, "l"
        elif cmd == "C":
            v = [round(float(q)) for q in t[i:i + 6]]; i += 6
            rel = [v[0] - cx, v[1] - cy, v[2] - cx, v[3] - cy, v[4] - cx, v[5] - cy]
            enc = (enc + "c" + pairs(rel)) if last != "c" else pairs_join(enc, rel)
            pts += [(v[0], v[1]), (v[2], v[3]), (v[4], v[5])]; cx, cy, last = v[4], v[5], "c"
        else:
            i += 1
    if pts: res.append((pts, enc))
    return res


def pairs_join(enc, nums):
    """append more numbers to the current l / c run"""
    for n in nums:
        s = str(n)
        enc += s if s.startswith("-") else " " + s
    return enc


def main(out_dir):
    t0 = time.time()
    svg = open(os.path.join(out_dir, "full.svg"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
    P = json.loads(js[js.index("{"):js.rindex("}") + 1])
    vx, vy, vw, vh = P["viewBox"]
    cx0, cy0, cx1, cy1 = vx - 2000, vy - 2000, vx + vw + 2000, vy + vh + 2000
    nx, ny = math.ceil((cx1 - cx0) / TILE), math.ceil((cy1 - cy0) / TILE)
    tiles = [{"els": [], "b": [math.inf, math.inf, -math.inf, -math.inf]} for _ in range(nx * ny)]
    tix = lambda x, y: min(nx - 1, max(0, int((x - cx0) // TILE))) + nx * min(ny - 1, max(0, int((y - cy0) // TILE)))
    classes, kept, dropped = set(), 0, 0
    for m in re.finditer(r'<path class="([^"]+)" d="([^"]*)"\s*/?>', svg):
        cls, d = m.group(1), m.group(2)
        per = {}
        for pts, enc in subpaths(d):
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if max(xs) < cx0 or min(xs) > cx1 or max(ys) < cy0 or min(ys) > cy1:
                dropped += 1; continue
            k = tix(*pts[0]); per.setdefault(k, []).append(enc); kept += 1
            b = tiles[k]["b"]; b[0] = min(b[0], min(xs)); b[1] = min(b[1], min(ys)); b[2] = max(b[2], max(xs)); b[3] = max(b[3], max(ys))
        for k, encs in per.items():
            els = tiles[k]["els"]
            if els and els[-1][0] == cls: els[-1][1].extend(encs)       # the same class right after: one path
            else: els.append([cls, encs])
        classes.add(cls)
    texts = 0
    for m in re.finditer(r"<text\b[^>]*>.*?</text>", svg, re.S):
        el = m.group(0)
        x, y = float(re.search(r'\bx="([-\d.]+)"', el).group(1)), float(re.search(r'\by="([-\d.]+)"', el).group(1))
        if not (cx0 <= x <= cx1 and cy0 <= y <= cy1): continue
        k = tix(x, y); tiles[k]["els"].append(["#text", re.sub(r'="([^"]*)"', r"='\1'", el)]); texts += 1
        b = tiles[k]["b"]; b[0] = min(b[0], x - 3000); b[1] = min(b[1], y - 600); b[2] = max(b[2], x + 3000); b[3] = max(b[3], y + 600)
    out = []
    for t in tiles:
        if not t["els"]: continue
        paths = [e for e in t["els"] if e[0] != "#text"]; txt = [e for e in t["els"] if e[0] == "#text"]
        s = "".join(f"<path class='{c}' d='{''.join(encs)}'/>" for c, encs in paths) + "".join(e[1] for e in txt)
        out.append({"b": [round(v) for v in t["b"]], "s": s})
    data = {"source": "DXF plan toolkit: full.svg (ACKO.dxf, Option 02A)", "built": time.strftime("%Y-%m-%d"), "tile": TILE,
            "frame": [cx0, cy0, cx1, cy1], "tiles": out}
    txt = ("/* the plan's own linework as vector tiles, made by tools/acko/plan_vec.py from the toolkit's full.svg; drawn when the "
           "layout is zoomed in past its sharpest picture */\nwindow.PLAN_VEC = " + json.dumps(data, separators=(",", ":")) + ";\n")
    dst = os.path.join(ROOT, "data", "plan-vec.js")
    open(dst, "w", encoding="utf-8").write(txt)
    sizes = sorted(len(t["s"]) for t in out)
    print(f"{len(out)} tiles of {nx} x {ny} ({TILE / 1000:.0f} m), {kept} subpaths kept, {dropped} outside the frame, {texts} labels")
    print(f"classes: {sorted(classes)}")
    print(f"wrote {dst}: {len(txt) / 1e6:.2f} MB; tiles median {sizes[len(sizes) // 2] / 1e3:.0f} KB, largest {sizes[-1] / 1e3:.0f} KB; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1])
