"""A day for a new Acker's stops, from Ritika's marked wayfinding blocks (27 Oct: "I've marked certain blocks as Wayfinding-Signage,
Wayfinding-Graphics, Wayfinding-Artwork, Wayfinding-Collab, Wayfinding-Workhall; these are the spots I want to show in this slide
instead of the route you have shown ... it should still sound like a day for a new Acker").

Usage:  python -I tools/acko/wayday_marks.py "<ACKO_BOUNDARY_HATCH_ALL_22_10_26 (5)>.dxf"
        (after tools/acko/axo_skp.py, whose route check leaves the floor's walking layers in tools/_work/axo-skp/route.npz)

  marks   every INSERT of a Wayfinding-* block in model space, as plan mm: Signage and Artwork (bars: standing and wall panels),
          Graphics (a polyline: a wall wrap, 3 cm off its wall), Collab and Workhall (hatches: floor areas)
  frame   the drawing's model space with y negated, shifted onto the slide's frame (data/axo-dxf.js, the DXF plan toolkit's) by
          matching the layout block's A-WALL lines to AXO_DXF's walls (FFT at 50 mm; it stops if under 30% land within 10 cm),
          then onto the SketchUp model's own walls, which sit a little off AXO_DXF's (a shift of up to 1.5 m)
  stops   her day (27 Oct), in order: the Reception sign (the Signage in Reception), the corridor sign (the other), the graphic, the
          workhall (a free spot by a desk, 40% of the way on from the graphic to the Collab), the Collab (a free spot inside),
          the art wall (its middle artwork);
          a mark on a wall is visited 1.2 m in front of it, on the free side (if both are: a sign from its own space, an artwork
          or the graphic from the corridor)
  floors  the Collab's and the workhall's hatches as one even area each (30 Oct: "Fill it, no cut-outs"): the hatch's furniture
          cut-outs are the 22.10 layout's, off the SketchUp model's desks, so its outlines are merged and the cut-outs and the
          notches walled in on most of their edge filled (solid); the gaps between its patches (a corridor) stay open
  legs    walked on the SketchUp model (axo_skp.Walker: the corridor floor preferred; furniture, grass and planters avoided)
Writes the `const WAY = {...};` line in slides/s-wayday.html (plan mm, y down: stops, legs, marks [{k, stop, shape, rings | line,
h}]) and tools/_work/wayday/way.png to check.
"""
import argparse, json, os, re, sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axo_skp
import dxf_read as D

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "_work", "wayday")
SLIDE = os.path.join(ROOT, "slides", "s-wayday.html")
# how each kind of mark stands up: shape and heights (m)
SHAPES = {"Signage": ("panel", [0.0, 2.2]), "Artwork": ("wall", [0.9, 2.1]), "Graphics": ("wrap", [0.0, 2.4]),
          "Collab": ("floor", None), "Workhall": ("floor", None)}
ORDER = ["Signage@Reception", "Signage", "Graphics", "Workhall", "Collab", "Artwork"]       # her day


def log(*a):
    print(*a, flush=True)


def read_marks(path):
    """the Wayfinding-* inserts (rings: (points, closed)) and the layout block's A-WALL lines, model space with y negated"""
    blocks, model = D.read(path)
    ins = [e for e in model if e["t"] == "INSERT"]
    lay = max((e for e in ins if not e["n"].startswith("Wayfinding")), key=lambda e: len(blocks.get(e["n"], {}).get("ents", [])))
    walls = []

    def fn(ent, m, layer, pth):
        if layer == "A-WALL":
            for r in ent.get("p", []): walls.append([(x, -y) for x, y in D.tf(m, r)])
    D.walk(blocks, [lay], fn)
    marks = []
    for e in ins:
        if not e["n"].startswith("Wayfinding-"): continue
        rings = []
        for be in blocks[e["n"]]["ents"]:
            P, C = be.get("p", []), be.get("c", [])
            for i, r in enumerate(P):
                rings.append(([(x, -y) for x, y in D.tf(e["m"], r)], be["t"] == "HATCH" or (C[i] if i < len(C) else True), be["t"]))
        marks.append({"k": e["n"].split("-", 1)[1], "rings": rings})
    log(f"read {os.path.basename(path)}: layout block {lay['n']} ({len(walls)} A-WALL lines), {len(marks)} marks:",
        dict((k, sum(1 for m in marks if m["k"] == k)) for k in sorted({m["k"] for m in marks})))
    return marks, walls


def register(walls, A):
    """the shift (plan mm) that lays the drawing's walls on AXO_DXF's, and the share of them that land within 10 cm"""
    from scipy import ndimage
    tgt = [[tuple(p) for p in ring] for w in A["walls"] for ring in w] + [[tuple(p) for p in r] for r in A["context"]]
    T = np.array([p for r in tgt for p in r], float); P = np.array([p for r in walls for p in r], float)
    d0 = (T.min(0) + T.max(0)) / 2 - (P.min(0) + P.max(0)) / 2
    res = 50.0; lo = T.min(0) - 25000; hi = T.max(0) + 25000; nx, ny = [int(v) for v in (hi - lo) / res + 1]

    def draw(rings, off):
        im = Image.new("L", (nx, ny), 0); dr = ImageDraw.Draw(im)
        for r in rings:
            q = [((x + off[0] - lo[0]) / res, (y + off[1] - lo[1]) / res) for x, y in r]
            if len(q) > 1: dr.line(q, fill=255, width=1)
        return np.asarray(im, np.float32) / 255
    a = draw(walls, d0); b = ndimage.binary_dilation(draw(tgt, (0, 0)) > 0, iterations=2).astype(np.float32)
    F = np.fft.irfft2(np.fft.rfft2(b) * np.conj(np.fft.rfft2(a)), s=b.shape)
    win = int(20000 / res); best = (-1.0, 0, 0)
    for dy in range(-win, win + 1):
        for dx in range(-win, win + 1):
            v = F[dy % ny, dx % nx]
            if v > best[0]: best = (v, dx, dy)
    off = d0 + np.array([best[1], best[2]]) * res
    share = float((draw(walls, off) * b).sum() / max(1, a.sum()))
    return off, share


def refine(walls, off, z, reach=1500):
    """the SketchUp model is registered onto AXO_DXF by its floor's footprint, so its walls can sit a little off AXO_DXF's: the
    small shift (plan mm, within reach) that lays the drawing's walls on the model's own (route.npz's wall layer, 5 cm), and the
    share of them within 10 cm after and before"""
    from scipy import ndimage
    res, lo, CX, CY = float(z["res"]), z["lo"], float(z["CX"]), float(z["CY"])
    H, W = z["wall"].shape; tgt = ndimage.binary_dilation(z["wall"], iterations=2).astype(np.float32)

    def draw(d):
        im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
        for r in walls:
            q = [(((x + off[0] + d[0] - CX) / 1000 - lo[0]) / res, ((y + off[1] + d[1] - CY) / 1000 - lo[1]) / res) for x, y in r]
            if len(q) > 1: dr.line(q, fill=255, width=1)
        return np.asarray(im, np.float32) / 255
    a = draw((0, 0)); share = lambda img: float((img * tgt).sum() / max(1, img.sum()))
    F = np.fft.irfft2(np.fft.rfft2(tgt) * np.conj(np.fft.rfft2(a)), s=tgt.shape)
    win = int(reach / 1000 / res); best = (-1.0, 0, 0)
    for dy in range(-win, win + 1):
        for dx in range(-win, win + 1):
            v = F[dy % H, dx % W]
            if v > best[0]: best = (v, dx, dy)
    d = np.array([best[1], best[2]], float) * res * 1000
    return d, share(draw(d)), share(a)


def solid(rings, R=1500, rim=0.85, keep=15e6):
    """a floor mark's rings (plan mm) as one even area: merged (60 mm closes the seams between patches), the furniture cut-outs
    and holes under keep mm2 dropped, and the notches a closing of R would fill added where the area walls in more than rim of
    their edge (a desk cut into the hatch's edge; not a corridor between two patches)"""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    u = unary_union([Polygon(r).buffer(0) for r in rings if len(r) >= 3]).buffer(60, join_style=2).buffer(-60, join_style=2)
    gap = u.buffer(R, join_style=2).buffer(-R, join_style=2).difference(u); edge = u.buffer(30)
    add = [g for g in getattr(gap, "geoms", [gap]) if g.area > 0 and g.boundary.intersection(edge).length > rim * g.length]
    u = unary_union([u] + add).buffer(30, join_style=2).buffer(-30, join_style=2)
    out = []
    for p in getattr(u, "geoms", [u]):
        if p.area < 1e6: continue
        out += [p.exterior] + [h for h in p.interiors if Polygon(h).area > keep]
    return [[[int(round(x)), int(round(y))] for x, y in r.simplify(20).coords[:-1]] for r in out]


def spaces_at():
    """(x, y) plan mm -> the PLAN_DXF space it is in ("Reception", ...), for the report and the Reception sign"""
    s = open(os.path.join(ROOT, "data", "plan-dxf.js"), encoding="utf-8").read()
    j = json.loads(s[s.index("window.PLAN_DXF = ") + 18:].strip().rstrip(";"))
    sp = [(q["type"], q["name"], [[tuple(map(float, p.strip().split())) for p in m[1:].rstrip("Z").split("L")] for m in re.findall(r"M[^MZ]+Z?", q["d"])]) for q in j["spaces"]]

    def inring(p, ring):
        c = False
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i], ring[i - 1]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1: c = not c
        return c
    return lambda p: next((f"{t} ({n})" if n != t else t for t, n, rings in sp if sum(inring(p, r) for r in rings) % 2), "-")


def clean(ring, closed):
    """mm-rounded points without repeats (and without the closing repeat of a closed ring)"""
    out = []
    for x, y in ring:
        q = [int(round(x)), int(round(y))]
        if not out or abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) > 5: out.append(q)
    if closed and len(out) > 2 and abs(out[0][0] - out[-1][0]) + abs(out[0][1] - out[-1][1]) <= 5: out.pop()
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("dxf"); a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    A = axo_skp.read_js(os.path.join(ROOT, "data", "axo-dxf.js"), "AXO_DXF")
    raw, walls = read_marks(a.dxf)
    off, share = register(walls, A)
    log(f"registration: shift {[round(v) for v in off]} mm, {share:.0%} of the layout's walls on the slide's (within 10 cm)")
    if share < 0.3: sys.exit("the walls don't match: the marks can't be placed")
    space = spaces_at()
    z = np.load(os.path.join(ROOT, "tools", "_work", "axo-skp", "route.npz"))
    d, share2, share1 = refine(walls, off, z)
    off = off + d
    log(f"  then onto the SketchUp model's own walls: {[round(v) for v in d]} mm more ({share1:.0%} -> {share2:.0%} of the walls within 10 cm)")
    wk = axo_skp.Walker({k: z[k] for k in ("wall", "furn", "plant", "grass", "corridor")}, z["lo"], float(z["res"]), float(z["CX"]), float(z["CY"]))
    from scipy import ndimage
    near_desk = ndimage.binary_dilation(wk.furn, iterations=6) & ~wk.furn                   # within 0.6 m of furniture

    # the marks in plan mm
    marks = []
    for m in raw:
        rings = [(clean([(x + off[0], y + off[1]) for x, y in r], closed), closed, t) for r, closed, t in m["rings"]]
        shape, h = SHAPES[m["k"]]
        if shape in ("panel", "wall"): rings = [next((r for r in rings if r[2] == "HATCH"), rings[0])]   # the bar, once
        pts = np.array([p for r, _, _ in rings for p in r], float)
        marks.append({"k": m["k"], "shape": shape, "h": h, "rings": rings, "c": (pts.min(0) + pts.max(0)) / 2})

    def front(m):
        """a wall mark's standing point: in front of it (1.2 m first, along the wall if furniture is in the way), on the right
        side: a sign is read from the space it stands in (the Reception sign from Reception), an artwork or a graphic from the
        corridor"""
        r = np.array(m["rings"][0][0], float)
        if m["shape"] == "wrap":
            seg = max(range(len(r) - 1), key=lambda i: np.linalg.norm(r[i + 1] - r[i])); c = (r[seg] + r[seg + 1]) / 2; u = r[seg + 1] - r[seg]
        else:
            c = m["c"]; e = [r[(i + 1) % len(r)] - r[i] for i in range(len(r))]; u = max(e, key=np.linalg.norm)
        u = u / np.linalg.norm(u); n = np.array([-u[1], u[0]])
        # every free spot 0.9-3 m in front and up to 2.4 m along the wall (furniture can stand right in front, as Reception's
        # lounge does), on either side: the right side first, then the nearest
        own = space(m["c"]).split(" (")[0]
        side_score = lambda q: (2 if m["k"] == "Signage" and space(q).split(" (")[0] == own else 0) + int(wk.corr[wk.cell(wk.to_w(q))])
        ok = [(side_score(q), -(abs(t) + d / 2), sg, q) for d in (1200, 1500, 1900, 2400, 900, 3000) for t in (0, 800, -800, 1600, -1600, 2400, -2400)
              for sg in (1, -1) for q in [c + n * sg * d + u * t] if wk.free(wk.cell(wk.to_w(q)))]
        if ok:
            _, _, sg, p = max(ok, key=lambda o: (o[0], o[1]))
            return p, n * sg
        raise SystemExit(f"no free spot in front of the {m['k']} at {m['c'].round()}")

    def inside(m, by_desk=False, toward=None):
        """an area mark's standing point: the free cell inside it (by a desk, for the workhall) nearest its area's middle, or
        nearest `toward` (plan mm) if given"""
        im = Image.new("1", (wk.W, wk.H), 0); dr = ImageDraw.Draw(im)
        for r, _, _ in m["rings"]: dr.polygon([tuple(wk.cell(wk.to_w(p))[::-1]) for p in r], fill=1)
        ins = np.array(im, bool)
        ok = ins & ~(wk.block | wk.furn | wk.plant | wk.grass) & (near_desk if by_desk else True)
        rr, cc = np.nonzero(ok)
        if not len(rr): raise SystemExit(f"no free spot inside the {m['k']}")
        # its middle: the rings' area-weighted centre (the workhall's 17 patches span a triangle; their box's middle is a corridor)
        A_ = cx = cy = 0.0
        for r, _, _ in m["rings"]:
            q = np.array(r, float); x, y = q[:, 0], q[:, 1]; x2, y2 = np.roll(x, -1), np.roll(y, -1); cr_ = x * y2 - x2 * y
            a_ = cr_.sum() / 2; A_ += abs(a_)
            if a_: cx += abs(a_) * ((x + x2) * cr_).sum() / (6 * a_); cy += abs(a_) * ((y + y2) * cr_).sum() / (6 * a_)
        mid = np.array([cx / A_, cy / A_]) if A_ else m["c"]
        cr, ccol = wk.cell(wk.to_w(mid if toward is None else toward))
        i = int(np.argmin((rr - cr) ** 2 + (cc - ccol) ** 2))
        return np.array(wk.to_mm(wk.world((rr[i], cc[i]))), float)

    # the stops, in her order
    sig = [m for m in marks if m["k"] == "Signage"]
    rec = [m for m in sig if space(m["c"]).startswith("Reception")] or sorted(sig, key=lambda m: -m["c"][0])[:1]
    pick = {"Signage@Reception": rec[0], "Signage": next(m for m in sig if m is not rec[0])}
    for k in ("Graphics", "Workhall", "Collab"): pick[k] = next(m for m in marks if m["k"] == k)
    art = sorted([m for m in marks if m["k"] == "Artwork"], key=lambda m: m["c"][0]); pick["Artwork"] = art[len(art) // 2]
    # where each is visited; the desk last: the workhall's patches lie either side of the diagonal corridor (their middle is the
    # corridor by the graphic), so the desk is the one by a desk nearest 40% of the way from the graphic on to the Collab
    at = {}
    for key in ORDER:
        m = pick[key]
        if key == "Workhall": continue
        if m["shape"] == "floor": at[key] = inside(m)
        else:
            at[key], n = front(m)
            if m["shape"] == "wrap": m["n"] = n                                                # the wrap's visible side
    at["Workhall"] = inside(pick["Workhall"], by_desk=True, toward=at["Graphics"] + 0.4 * (at["Collab"] - at["Graphics"]))
    stops = []
    for i, key in enumerate(ORDER):
        m = pick[key]; p = at[key]
        stops.append(p)
        for mm in ([x for x in art] if key == "Artwork" else [m]): mm["stop"] = i
        log(f"  stop {i + 1} {key:18s} at {[int(v) for v in p]}  in {space(p)}  (mark in {space(m['c'])})")
    # the legs, walked on the SketchUp model
    legs = []
    for i in range(len(stops) - 1):
        path = wk.astar(wk.to_w(stops[i]), wk.to_w(stops[i + 1]))
        if path is None: raise SystemExit(f"no way from stop {i + 1} to {i + 2}")
        legs.append([wk.to_mm(q) for q in path])
        L = sum(float(np.linalg.norm(path[j] - path[j - 1])) for j in range(1, len(path)))
        log(f"  leg {i + 1}->{i + 2}: {L:.1f} m, {len(path)} points")
    # what the slide draws
    out_marks = []
    for m in marks:
        o = {"k": m["k"], "stop": m["stop"], "shape": m["shape"]}
        if m["shape"] == "wrap":
            r = np.array(m["rings"][0][0], float) + m["n"] * 30; o["line"] = [[int(round(x)), int(round(y))] for x, y in r]; o["h"] = m["h"]
        else:
            o["rings"] = [r for r, closed, _ in m["rings"] if closed and len(r) >= 3]
            if m["shape"] == "floor": o["rings"] = solid(o["rings"])
            if m["h"]: o["h"] = m["h"]
        out_marks.append(o)
    out_marks.sort(key=lambda o: o["stop"])
    way = {"stops": [[int(round(v)) for v in p] for p in stops], "legs": legs, "marks": out_marks}
    s = open(SLIDE, encoding="utf-8").read()
    s2, n = re.subn(r"^  const WAY = .*;$", lambda _: "  const WAY = " + json.dumps(way, separators=(",", ":")) + ";", s, count=1, flags=re.M)
    if n != 1: sys.exit("no `const WAY = ...;` line in slides/s-wayday.html")
    with open(SLIDE, "w", encoding="utf-8", newline="") as f: f.write(s2)
    log(f"slides/s-wayday.html: WAY with {len(stops)} stops, {len(legs)} legs, {len(out_marks)} marks")

    # the check picture: the floor's walking layers round the marks, the marks (purple), the legs (red), the stops (numbered)
    res = float(z["res"]); lo = z["lo"]; pts = np.array([p for o in out_marks for r in (o.get("rings") or [o["line"]]) for p in r] + [p for L in legs for p in L], float)
    w0 = (pts.min(0) - 8000 - np.array([z["CX"], z["CY"]])) / 1000; w1 = (pts.max(0) + 8000 - np.array([z["CX"], z["CY"]])) / 1000
    Hh, Ww = z["wall"].shape
    c0, r0 = [max(0, int((w0[i] - lo[i]) / res)) for i in (0, 1)]; c1, r1 = min(Ww, int((w1[0] - lo[0]) / res)), min(Hh, int((w1[1] - lo[1]) / res))
    img = np.full((r1 - r0, c1 - c0, 3), 255, np.uint8)
    for k, col in (("corridor", (232, 222, 245)), ("grass", (205, 225, 180)), ("furn", (205, 220, 240)), ("plant", (140, 190, 120)), ("wall", (0, 0, 0))):
        img[z[k][r0:r1, c0:c1]] = col
    im = Image.fromarray(img).resize(((c1 - c0) * 2, (r1 - r0) * 2), Image.NEAREST); dr = ImageDraw.Draw(im)
    px = lambda p: (((p[0] - z["CX"]) / 1000 - lo[0]) / res * 2 - c0 * 2, ((p[1] - z["CY"]) / 1000 - lo[1]) / res * 2 - r0 * 2)
    for o in out_marks:
        for r in (o.get("rings") or []): dr.polygon([px(p) for p in r], outline=(82, 34, 208), fill=(82, 34, 208) if o["shape"] != "floor" else None)
        if o.get("line"): dr.line([px(p) for p in o["line"]], fill=(82, 34, 208), width=6)
    for L in legs: dr.line([px(p) for p in L], fill=(200, 0, 0), width=4)
    for i, p in enumerate(way["stops"]):
        x, y = px(p); dr.ellipse([x - 14, y - 14, x + 14, y + 14], outline=(152, 0, 0), width=4); dr.text((x + 16, y - 20), str(i + 1), fill=(152, 0, 0))
    im.save(os.path.join(WORK, "way.png")); log(f"check picture: tools/_work/wayday/way.png ({im.size[0]} x {im.size[1]})")


if __name__ == "__main__":
    main()
