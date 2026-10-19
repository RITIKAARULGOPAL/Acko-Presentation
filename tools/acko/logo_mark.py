"""The ACKO symbol on its own (no letters), cut from the two wordmarks, for the mark at the top right of every slide.

    python tools/acko/logo_mark.py      writes assets/img/acko-mark.webp (purple) and acko-mark-white.webp

The symbol is everything left of the first fully transparent column of the wordmark, trimmed to its alpha box.
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG = os.path.join(ROOT, "assets", "img")

for src, out in (("acko-ink", "acko-mark"), ("acko-white", "acko-mark-white")):
    im = Image.open(os.path.join(IMG, src + ".webp")).convert("RGBA")
    alpha = im.getchannel("A")
    w, h = im.size
    x = 0
    while x < w and not alpha.crop((x, 0, x + 1, h)).getbbox():     # skip any blank columns before the symbol
        x += 1
    while x < w and alpha.crop((x, 0, x + 1, h)).getbbox():         # then run to the gap before the "A"
        x += 1
    mark = im.crop((0, 0, x, h))
    mark = mark.crop(mark.getchannel("A").getbbox())
    mark.save(os.path.join(IMG, out + ".webp"), "WEBP", lossless=True)
    print(f"{out}.webp  {mark.size[0]}x{mark.size[1]}  (from {src}.webp, {w}x{h})")
