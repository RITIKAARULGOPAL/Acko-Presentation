"""The deck's loop GIF (slide 11, image73.gif) as frames for the Loop slide's stops beat: the ribbon writes itself once.

    python tools/acko/loop_frames.py "<deck.pptx>"

The GIF writes "loop", holds it, then clears it and repeats; only the writing is kept, from the first frame to the first
one where the ribbon is complete. Each frame gets the deck's slide-11 crop and is saved as assets/img/s-loop/draw-NN.webp.

Prints what the slide needs (paste into slides/s-loop.html):
  box    where the frames sit on the page (% of the page), fitted so the finished ribbon lands on the slide-12 still
         (loop-ribbon.webp in its deck box), where the stops were placed
  reach  per frame, how far right the ribbon has got (% of the page), to bring each stop up as the ribbon reaches it
  alpha  the opacity that gives the still's colour on white
"""
import io, json, os, sys, zipfile
from PIL import Image, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "img", "s-loop")
CROP = (0.03225, 0.15321, 0.0357, 0.15321)          # srcRect l, t, r, b on slide 11
STILL_BOX = (0, 9.1, 100, 69.4)                      # loop-ribbon.webp on slide 12, % of the page
WIDTH = 1600                                         # the frames' width in pixels
PW, PH = 1920, 1080                                  # a page to measure on


def solid(im):
    return im.getchannel("A").point(lambda v: 255 if v > 128 else 0)


def main(deck):
    gif = Image.open(io.BytesIO(zipfile.ZipFile(deck).read("ppt/media/image73.gif")))
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(gif)]
    w, h = frames[0].size
    l, t, r, b = CROP
    box_px = (round(l * w), round(t * h), round(w * (1 - r)), round(h * (1 - b)))
    crops = [f.crop(box_px) for f in frames]
    cw, ch = crops[0].size

    # the writing: up to the first frame where the ribbon is (all but) complete
    cover = [sum(1 for v in solid(c.resize((cw // 10, ch // 10))).getdata() if v) for c in crops]
    last = next(i for i, c in enumerate(cover) if c >= 0.995 * max(cover))

    # fit the frames' box so the finished ribbon lands on the still ribbon of slide 12
    sx, sy, sw, sh = STILL_BOX
    still = Image.open(os.path.join(ROOT, "assets", "img", "loop-ribbon.webp")).convert("RGBA")
    s0 = solid(still).getbbox()
    sb = [sx + s0[0] / still.width * sw, sy + s0[1] / still.height * sh, sx + s0[2] / still.width * sw, sy + s0[3] / still.height * sh]
    g0 = solid(crops[last]).getbbox()
    kx, ky = (sb[2] - sb[0]) / ((g0[2] - g0[0]) / cw), (sb[3] - sb[1]) / ((g0[3] - g0[1]) / ch)
    box = [sb[0] - g0[0] / cw * kx, sb[1] - g0[1] / ch * ky, kx, ky]

    # how far right the ribbon has got, frame by frame (cumulative, % of the page)
    reach, far = [], 0
    for c in crops[: last + 1]:
        bb = solid(c).getbbox()
        if bb:
            far = max(far, bb[2])
        reach.append(round(box[0] + far / cw * box[2], 1))

    # the still's colour on white, and the opacity that gives it from the GIF's colour
    def ribbon_rgb(im):
        px = [p for p in im.resize((im.width // 8, im.height // 8)).getdata() if p[3] == 255]
        return [sorted(p[k] for p in px)[len(px) // 2] for k in range(3)]
    srgb, grgb = ribbon_rgb(still), ribbon_rgb(crops[last])
    alpha = sum((255 - s) / max(1, 255 - g) for s, g in zip(srgb, grgb)) / 3

    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.startswith("draw-") and old.endswith(".webp"):
            os.remove(os.path.join(OUT, old))
    hh = round(ch * WIDTH / cw)
    total = 0
    for i, c in enumerate(crops[: last + 1]):
        p = os.path.join(OUT, f"draw-{i:02d}.webp")
        c.resize((WIDTH, hh), Image.LANCZOS).save(p, "WEBP", quality=82, method=6)
        total += os.path.getsize(p)
    print(f"{last + 1} frames ({gif.info.get('duration', 40)} ms each), {WIDTH}x{hh}, {total / 1e6:.2f} MB -> assets/img/s-loop/draw-NN.webp")
    print(json.dumps({"frames": last + 1, "size": [WIDTH, hh], "box": [round(v, 2) for v in box], "alpha": round(alpha, 2),
                      "still_rgb": srgb, "gif_rgb": grgb, "reach": reach}))


if __name__ == "__main__":
    main(sys.argv[1])
