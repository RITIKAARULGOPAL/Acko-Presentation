"""Place the floor plate on the satellite stills.

Input: a Google Maps screenshot saved as SVG (from a vector editor) whose layers are the screenshot and
a boundary drawn over the site (the most saturated green layer is taken as the site), plus our own
satellite still assets/site/sat_z19.webp.

1. The screenshot is matched to the still (SIFT + RANSAC similarity) - both are Google imagery.
2. The drawing's floor outline (data/zones.json annot.outline, mm, north = +x, west = +y) is fitted to the
   marked boundary at the still's true scale (Web Mercator, zoom 19), anchored on the prow, then snapped
   to the roof edges visible in the still.
3. Writes data/site.json: the mm -> still-px affine, the outline in still px, and the atrium / entry points.

Usage: python tools/site_register.py "<screenshot.svg>" [--debug out.png]
"""
import base64, io, json, math, os, re, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STILL = os.path.join(ROOT, "assets", "site", "sat_z19.webp")
LAT, ZOOM = 12.9366189, 19                       # the stills are centred on the Sattva Hallmark place pin
S = 256 * 2 ** ZOOM / (40075016.686 * math.cos(math.radians(LAT))) / 1000   # still px per mm


def layers(svg_path):
    s = open(svg_path, encoding="utf-8").read()
    imgs = {i: Image.open(io.BytesIO(base64.b64decode(b))) for _, _, i, b in
            re.findall(r'<image\s+width="(\d+)" height="(\d+)" id="(\w+)" href="data:image/png;base64,([^"]+)"', s)}
    uses = re.findall(r'<use id="([^"]*)"[^>]*href="#(\w+)" x="([\d.]+)" y="([\d.]+)"', s)
    bg = next(imgs[i] for name, i, x, y in uses if name == "Background").convert("RGB")
    marks = [(imgs[i].convert("RGBA"), float(x), float(y)) for name, i, x, y in uses if name != "Background"]
    # the site layer: the overlay whose opaque pixels are greenest
    def greenness(im):
        a = np.array(im); m = a[:, :, 3] > 100
        return (a[:, :, 1][m].astype(float) - np.maximum(a[:, :, 0], a[:, :, 2])[m]).mean() if m.any() else -1e9
    site = max(marks, key=lambda t: greenness(t[0]))
    return bg, site


def register(bg):
    shot = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2GRAY)
    still = cv2.cvtColor(np.array(Image.open(STILL).convert("RGB")), cv2.COLOR_RGB2GRAY)
    mask = np.zeros_like(shot); mask[90:shot.shape[0] - 80, :] = 255     # map canvas only, no browser chrome / taskbar
    sift = cv2.SIFT_create(6000)
    k1, d1 = sift.detectAndCompute(shot, mask); k2, d2 = sift.detectAndCompute(still, None)
    good = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    M, inl = cv2.estimateAffinePartial2D(np.float32([k1[g.queryIdx].pt for g in good]), np.float32([k2[g.trainIdx].pt for g in good]),
                                         method=cv2.RANSAC, ransacReprojThreshold=4)
    return M, int(inl.sum()), still


def corners(mark, ox, oy):
    """Prow tip, prow corners and the two far corners of a hand-drawn prow-shaped boundary (screenshot px)."""
    a = np.array(mark)[:, :, 3] > 100
    rows = [(y, np.nonzero(a[y])[0]) for y in range(a.shape[0]) if a[y].any()]
    widths = np.array([r[-1] - r[0] for _, r in rows]); full = np.median(widths)
    prow_i = max(i for i, w in enumerate(widths) if w > 0.9 * full)          # last full-width row
    y_p, r_p = rows[prow_i]; y_t, r_t = rows[-1]; y_0, r_0 = rows[0]
    P = lambda x, y: (x + ox, y + oy)
    return dict(tip=P(r_t.mean(), y_t), left=P(r_p[0], y_p), right=P(r_p[-1], y_p), top_left=P(r_0[0], y_0), top_right=P(r_0[-1], y_0))


def model(outline, rot, c):
    """mm -> still px: north (+x) up, west (+y) left, rotated by rot (deg, clockwise on screen) about the origin."""
    th = math.radians(rot); R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    A = R @ (S * np.array([[0, -1], [-1, 0]]))
    return (np.asarray(outline, float) @ A.T) + c, A


def fit(outline, marked):
    """Rotation + translation (scale fixed) on prow tip and prow corners."""
    src = np.array([outline[0], outline[1], outline[4]], float)      # tip, west prow corner, east prow corner
    dst = np.array([marked["tip"], marked["left"], marked["right"]], float)
    best = None
    for rot in np.arange(-10, 10.001, 0.05):
        q, _ = model(src, rot, np.zeros(2)); c = (dst - q).mean(0); e = np.linalg.norm(q + c - dst, axis=1).mean()
        if best is None or e < best[0]:
            best = (e, rot, c)
    return best


def snap(outline, rot, c, still):
    """Nudge rotation / offset so the outline's prow and long sides sit on the strongest roof edges."""
    g = cv2.GaussianBlur(still, (3, 3), 0).astype(np.float32)
    mag = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    # sample the prow sides and the southern 30 m of both long sides (the north end is hidden by other roofs)
    o = np.asarray(outline, float)
    segs = [(o[0], o[1]), (o[0], o[4]), (o[1], o[1] + [30000, 0]), (o[4], o[4] + [30000, 0])]
    pts = np.array([a + (b - a) * t for a, b in segs for t in np.linspace(0, 1, 60)])

    def score(r, cc):
        q, _ = model(pts, r, cc); x, y = q[:, 0].round().astype(int), q[:, 1].round().astype(int)
        ok = (x >= 0) & (x < mag.shape[1]) & (y >= 0) & (y < mag.shape[0])
        return mag[y[ok], x[ok]].mean()
    best = (score(rot, c), rot, c)
    for r in np.arange(rot - 3, rot + 3.001, 0.1):
        for dx in range(-8, 9):
            for dy in range(-8, 9):
                s = score(r, c + [dx, dy])
                if s > best[0]:
                    best = (s, r, c + [dx, dy])
    return best


def main():
    shot_svg = sys.argv[1]
    bg, (mark, ox, oy) = layers(shot_svg)
    M, inliers, still = register(bg)
    sc = math.hypot(M[0, 0], M[1, 0]); rot_shot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
    to_still = lambda p: tuple(M[:, :2] @ np.array(p, float) + M[:, 2])
    marked = {k: to_still(v) for k, v in corners(mark, ox, oy).items()}
    Z = json.load(open(os.path.join(ROOT, "data", "zones.json"), encoding="utf-8"))
    outline = Z["annot"]["outline"]
    err, rot0, c0 = fit(outline, marked)
    sc_edge, rot, c = snap(outline, rot0, c0, still)
    poly, A = model(outline, rot, c)
    inv = np.linalg.inv(A)
    to_mm = lambda p: [round(v) for v in inv @ (np.array(p, float) - c)]
    # atrium: the glass-roofed court between the two wings, where Google's Sattva Hallmark pin sits (still centre);
    # entry: the campus gate / drop-off off the ORR service road, south-east of the east wing's prow
    pin_px = (960.0, 540.0)
    entry_px = tuple(np.array(model([outline[4]], rot, c)[0][0]) + np.array([66.0, 44.0]))
    site = dict(
        still="assets/site/sat_z19.webp", size=[1920, 1080], zoom=ZOOM, px_per_m=round(S * 1000, 4),
        mm_to_px=[A[0, 0], A[1, 0], A[0, 1], A[1, 1], c[0], c[1]],              # SVG matrix(a b c d e f): px = A.mm + c
        north_deg=round(rot, 2),                       # true north, in degrees counter-clockwise from the drawing's +x
        outline_px=[[round(x, 1), round(y, 1)] for x, y in poly],
        points=dict(atrium=to_mm(pin_px), entry=to_mm(entry_px), pin=to_mm(pin_px)),
        registration=dict(shot=os.path.basename(shot_svg), inliers=inliers, shot_scale=round(sc, 4), shot_rot_deg=round(rot_shot, 2),
                          mark_fit_err_m=round(err / S / 1000, 2), edge_score=round(float(sc_edge), 2)),
    )
    # optional close still (e.g. site_z20 from capture_sat.js) for the satellite underlay in the plan:
    # matched to the z19 still, so its mm -> px transform is the z19 one carried across
    if "--under" in sys.argv:
        src = sys.argv[sys.argv.index("--under") + 1]
        name = os.path.splitext(os.path.basename(src))[0]
        im = Image.open(src).convert("RGB"); im.save(os.path.join(ROOT, "assets", "site", name + ".webp"), "WEBP", quality=84)
        g = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create(8000)
        k1, d1 = sift.detectAndCompute(still, None); k2, d2 = sift.detectAndCompute(g, None)
        good = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
        H, inl = cv2.estimateAffinePartial2D(np.float32([k1[m.queryIdx].pt for m in good]), np.float32([k2[m.trainIdx].pt for m in good]),
                                             method=cv2.RANSAC, ransacReprojThreshold=3)
        A2 = H[:, :2] @ A; c2 = H[:, :2] @ c + H[:, 2]
        site["under"] = dict(still=f"assets/site/{name}.webp", size=list(im.size), mm_to_px=[A2[0, 0], A2[1, 0], A2[0, 1], A2[1, 1], c2[0], c2[1]],
                             inliers=int(inl.sum()), scale_vs_z19=round(math.hypot(H[0, 0], H[1, 0]), 4))
        print("underlay", name, site["under"]["inliers"], "inliers, scale", site["under"]["scale_vs_z19"])
    json.dump(site, open(os.path.join(ROOT, "data", "site.json"), "w"), indent=1)
    print(json.dumps({k: site[k] for k in ("north_deg", "points", "registration")}, indent=1))
    if "--debug" in sys.argv:
        im = Image.open(STILL).convert("RGB"); d = ImageDraw.Draw(im)
        for k in ("tip", "left", "right"):
            x, y = marked[k]; d.ellipse((x - 4, y - 4, x + 4, y + 4), outline=(0, 255, 60), width=2)
        d.polygon([tuple(p) for p in poly], outline=(255, 255, 255))
        for k, p in (("atrium", pin_px), ("entry", entry_px)):
            d.ellipse((p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5), outline=(255, 180, 0), width=2); d.text((p[0] + 8, p[1] - 6), k, fill=(255, 180, 0))
        im.crop((760, 330, 1160, 700)).resize((800, 740), Image.LANCZOS).save(sys.argv[sys.argv.index("--debug") + 1])


if __name__ == "__main__":
    main()
