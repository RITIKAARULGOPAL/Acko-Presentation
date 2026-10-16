"""Print a slide's pictures as HTML, placed and cropped exactly as on the deck page: each picture becomes an <i class="dk">
at its box (% of the page) with the deck's crop as background-size / background-position. Pictures are named through
extract_assets.PICK (media → asset); pictures not picked are listed as comments so nothing is missed.

    python tools/acko/deck_layout.py 16            # after deck_inventory.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INV = json.load(open(os.path.join(ROOT, "tools", "_media", "inventory.json")))
import importlib.util
spec = importlib.util.spec_from_file_location("ea", os.path.join(os.path.dirname(os.path.abspath(__file__)), "extract_assets.py"))
src = open(spec.origin, encoding="utf8").read()
PICK = {}
exec(src[src.index("PICK = {"):src.index("\n}\n", src.index("PICK = {")) + 3], {}, locals_ := {})
PICK = locals_["PICK"]
BY_MEDIA = {}
for name, p in PICK.items():
    BY_MEDIA.setdefault(p[0], name)


def css(box, crop):
    l, t, r, b = [max(0.0, v) / 100 for v in crop]
    sw, sh = 100 / max(0.01, 1 - l - r), 100 / max(0.01, 1 - t - b)
    px = 0 if l + r == 0 else l / (l + r) * 100
    py = 0 if t + b == 0 else t / (t + b) * 100
    return (f"left:{box[0]}%;top:{box[1]}%;width:{box[2]}%;height:{box[3]}%;"
            f"background-size:{sw:.1f}% {sh:.1f}%;background-position:{px:.1f}% {py:.1f}%")


for s in sys.argv[1:]:
    print(f"<!-- slide {s} -->")
    for i, r in enumerate(INV[s]):
        name = BY_MEDIA.get(r["media"])
        if not name:
            print(f"<!-- unpicked {r['media']} {r['px']} box {r['box']} crop {r['crop']} -->")
            continue
        print(f'<i class="dk" style="--i:{i};{css(r["box"], r["crop"])};background-image:url(assets/img/{name}.webp)"></i>')
