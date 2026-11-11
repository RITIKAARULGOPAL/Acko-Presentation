# The opening's morph (11 Nov, Ritika: "the transition and merging of the white Möbius strip is not seamless"): ACKO's mark, its three
# bands, changes shape into the white strip of the deck's Möbius photo, so the photo comes up on an outline that is already there.
#   python tools/acko/story/mark_morph.py .            writes the point lists into slides/s-open.html and s-open-2.html
# The strip's silhouette is its alpha (outer edge and opening), in page px as s-mobius places the photo (x' = 149.76 + 1.055 x,
# y' = 1.0547 y). The ring is cut by three rays from the opening's centre, at the twist (top right) and either side of the left
# crossing, into three bands that sit where the mark's bands sit: top run, lower run, left fold. Each mark band (its SVG path at the
# logo's pose) and its target are resampled to N points by length, the target's start and direction chosen to match the source in
# normalised box coordinates, so no point travels across the shape.
import sys, os, re, json, math
import numpy as np, cv2
from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
N = 180
POSE = (681.0, 330.0, 3.3)          # the logo's pose in page px: translate, scale (as the slide's CSS)
MARK = {
    "a": "M14 32C40 29 78 38 124 62L166 43.5C168.5 42 168.5 39.5 165.5 37.5C140 21 108 1 80 0C62 0 36 14 14 32Z",
    "b": "M169 44.5L104 74C70 89 36 97 13.5 95C32 109 55 127 76 127C104 126 148 102 167 88C169 86 169 85 169 84Z",
    "c": "M12 34C30 33 44 35 52 38C48.5 55 48.5 74 52 89C40 92 24 93.5 12 92.5C-3 78 -3 50 12 34Z",
}

def path_pts(d, step=0.25):
    toks = re.findall(r"[MLCZ]|-?\d*\.?\d+", d); i = 0; cur = None; out = []; cmd = None
    while i < len(toks):
        t = toks[i]
        if t in "MLCZ": cmd = t; i += 1
        if cmd == "Z": break
        if cmd in "ML":
            p = (float(toks[i]), float(toks[i + 1])); i += 2
            if cmd == "L" and cur:
                n = max(2, int(math.dist(cur, p) / step)); out += [(cur[0] + (p[0] - cur[0]) * k / n, cur[1] + (p[1] - cur[1]) * k / n) for k in range(1, n + 1)]
            else: out.append(p)
            cur = p; cmd = "L" if cmd == "M" else cmd
        elif cmd == "C":
            c1 = (float(toks[i]), float(toks[i + 1])); c2 = (float(toks[i + 2]), float(toks[i + 3])); p = (float(toks[i + 4]), float(toks[i + 5])); i += 6
            for k in range(1, 61):
                u = k / 60; v = 1 - u
                out.append((v**3 * cur[0] + 3 * v * v * u * c1[0] + 3 * v * u * u * c2[0] + u**3 * p[0], v**3 * cur[1] + 3 * v * v * u * c1[1] + 3 * v * u * u * c2[1] + u**3 * p[1]))
            cur = p
    tx, ty, s = POSE
    return np.array([(tx + x * s, ty + y * s) for x, y in out])

def resample(P, n):
    P = np.vstack([P, P[:1]]); seg = np.hypot(*np.diff(P, axis=0).T); L = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, L[-1], n, endpoint=False)
    return np.stack([np.interp(t, L, P[:, 0]), np.interp(t, L, P[:, 1])], 1)

def area(P): x, y = P[:, 0], P[:, 1]; return 0.5 * (x @ np.roll(y, -1) - y @ np.roll(x, -1))

def match(src, dst):
    """dst rotated (and reversed if needed) so its points line up with src's, judged in each shape's own normalised box"""
    if np.sign(area(src)) != np.sign(area(dst)): dst = dst[::-1]
    nrm = lambda P: (P - P.min(0)) / np.maximum(np.ptp(P, 0), 1e-6)
    a, b = nrm(src), nrm(dst)
    best = min(range(len(dst)), key=lambda k: ((a - np.roll(b, -k, 0)) ** 2).sum())
    return np.roll(dst, -best, 0)

im = np.array(Image.open(os.path.join(ROOT, "assets/img/mobius.webp")).convert("RGBA"))
alpha = (im[:, :, 3] > 40).astype(np.uint8) * 255
alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cs, hier = cv2.findContours(alpha, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
order = sorted(range(len(cs)), key=lambda i: -cv2.contourArea(cs[i]))
outer = cs[order[0]][:, 0, :].astype(float)
holes = [cs[i][:, 0, :].astype(float) for i in order[1:] if hier[0][i][3] == order[0]]
hole = max(holes, key=lambda h: cv2.contourArea(h.astype(np.int32)))
page = lambda P: np.stack([149.76 + 1.055 * P[:, 0], 1.0547 * P[:, 1]], 1)
O, H = page(outer), page(hole)
C = H.mean(0)

# the cuts (angles from the opening's centre, screen y down): the twist at the top right, and the left crossing's two sides
def ang_of(photo_xy): p = np.array([149.76 + 1.055 * photo_xy[0], 1.0547 * photo_xy[1]]); return math.atan2(p[1] - C[1], p[0] - C[0])
CUT = {"twist": ang_of((1330, 300)), "lt": ang_of((330, 330)), "lb": ang_of((330, 760))}

def band(a0, a1):
    """the ring between angles a0 → a1 (clockwise on screen): the outer edge forward, the opening's edge back"""
    span = (a1 - a0) % (2 * math.pi)
    inr = lambda P: [p for p in P if ((math.atan2(p[1] - C[1], p[0] - C[0]) - a0) % (2 * math.pi)) <= span]
    def ordered(P):
        q = inr(P); q.sort(key=lambda p: (math.atan2(p[1] - C[1], p[0] - C[0]) - a0) % (2 * math.pi)); return q
    o, h = ordered(O), ordered(H)
    return np.array(o + h[::-1])

TARGET = {"a": band(CUT["lt"], CUT["twist"]),       # top run: left crossing (upper side) → over the top → the twist
          "b": band(CUT["twist"], CUT["lb"]),       # lower run: the twist → round the bottom → the crossing (lower side)
          "c": band(CUT["lb"], CUT["lt"])}          # the left fold, between the crossing's two sides
rgb = im[:, :, :3].astype(float); ys, xs = np.nonzero(im[:, :, 3] > 200)
out = {}
for k in "abc":
    src = resample(path_pts(MARK[k]), N)
    dst = match(src, resample(TARGET[k], N))
    # the band's tone in the photo: mean colour of opaque photo px inside the target band
    poly = np.stack([(dst[:, 0] - 149.76) / 1.055, dst[:, 1] / 1.0547], 1).astype(np.int32)
    m = np.zeros(alpha.shape, np.uint8); cv2.fillPoly(m, [poly], 1); sel = (m > 0) & (im[:, :, 3] > 200)
    tone = rgb[sel].mean(0) if sel.any() else np.array([235, 235, 238])
    out[k] = {"from": [round(v, 1) for v in src.ravel().tolist()], "to": [round(v, 1) for v in dst.ravel().tolist()],
              "tone": "#%02x%02x%02x" % tuple(int(min(255, c * 1.04)) for c in tone)}
    print(k, "tone", out[k]["tone"], "target px", len(TARGET[k]))
if "--preview" in sys.argv:          # a picture of the cuts over the photo, in page px, then stop
    pv = Image.new("RGB", (1920, 1080), (20, 18, 30)); ph = Image.open(os.path.join(ROOT, "assets/img/mobius.webp")).convert("RGBA")
    pv.paste(ph.resize((round(1536 * 1.055), round(1024 * 1.0547))), (150, 0), ph.resize((round(1536 * 1.055), round(1024 * 1.0547))))
    a = np.array(pv); col = {"a": (144, 104, 240), "b": (72, 40, 186), "c": (176, 152, 242)}
    for k in "abc":
        ov = a.copy(); cv2.fillPoly(ov, [np.array(out[k]["to"]).reshape(-1, 2).astype(np.int32)], col[k]); a = (a * .45 + ov * .55).astype(np.uint8)
        cv2.polylines(a, [np.array(out[k]["from"]).reshape(-1, 2).astype(np.int32)], True, col[k], 3)
        f = np.array(out[k]["from"]).reshape(-1, 2); t = np.array(out[k]["to"]).reshape(-1, 2)
        for i in range(0, N, 15): cv2.line(a, tuple(f[i].astype(int)), tuple(t[i].astype(int)), (255, 200, 0), 1)
    Image.fromarray(a).save(sys.argv[sys.argv.index("--preview") + 1]); print("preview"); sys.exit()
blob = "/*MORPH*/" + json.dumps(out, separators=(",", ":")) + "/*END*/"
for f in ("tools/acko/story/open_base.html",):          # the opening's template (gen_unfold.py builds the slides from it)
    p = os.path.join(ROOT, f); t = open(p, encoding="utf-8").read()
    t2, n = re.subn(r"/\*MORPH\*/.*?/\*END\*/", lambda _: blob, t, flags=re.S)
    assert n == 1, f + ": no /*MORPH*/ placeholder"
    open(p, "w", encoding="utf-8", newline="\n").write(t2); print("ok", f)
