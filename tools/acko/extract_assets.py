"""Cut the presentation's images out of the Acko design deck (20.10.26) into assets/img/*.webp.

Every image in PICK is named by what it shows, so the slides never refer to the deck's own image numbers.
A pick can apply the crop the deck gives that picture on a slide (crop=slide number), cap its width, and keep
transparency (PNG cut-outs stay transparent in WebP). Animated GIFs become animated WebP.

Also writes data/keyplans.js: for every render slide, where its keyplan's camera mark sits on the keyplan image
(the deck draws the mark as a maroon V over a cropped keyplan), so the walk can show the same keyplan.

    python tools/acko/extract_assets.py "<deck.pptx>"            # everything
    python tools/acko/extract_assets.py "<deck.pptx>" team- kp-   # only names starting with these
Needs tools/_media/inventory.json from deck_inventory.py (crops and boxes).
"""
import io, json, math, os, re, sys, zipfile
from PIL import Image, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "img")
INV = json.load(open(os.path.join(ROOT, "tools", "_media", "inventory.json")))

# name: (media, crop-from-slide or None, max width[, degrees to turn counter-clockwise, as the slide turns it])
PICK = {
    # cover (1) and the logos
    "cover-stair": ("image17.png", 1, 2000),
    "acko-white": ("image22.png", None, 800),            # the cover's white ACKO wordmark
    "acko-ink": ("image1.png", None, 528),               # the purple wordmark used on the slides
    # team (2), by name; crops as on the slide
    "team-tushar": ("image12.png", 2, 500), "team-jegan": ("image11.png", 2, 500), "team-bisa": ("image60.png", 2, 500),
    "team-nabeela": ("image19.png", 2, 500), "team-sai": ("image7.png", 2, 500), "team-ashish": ("image25.png", 2, 500),
    "team-rishabh": ("image15.png", 2, 500), "team-umar": ("image13.png", None, 500), "team-deepak": ("image16.png", 2, 500),
    "team-sudeeti": ("image20.png", 2, 500), "team-dark": ("image18.png", 2, 1200),
    # workplace aspiration (3)
    "asp-protection": ("image23.jpg", None, 1100), "asp-nature": ("image31.png", None, 1100), "asp-palette": ("image21.png", None, 1600),
    # what defines ACKO (4): the strip shown, then the one beneath it
    "val-confidence": ("image24.jpg", None, 900), "val-trust": ("image29.jpg", None, 900), "val-protection": ("image28.jpg", None, 900),
    "val-assurance": ("image30.png", None, 900), "val-empowerment": ("image45.jpg", None, 900),
    "val-confidence-2": ("image27.jpg", None, 900), "val-trust-2": ("image38.jpg", None, 900), "val-protection-2": ("image26.jpg", None, 900),
    "val-assurance-2": ("image34.jpg", None, 900), "val-empowerment-2": ("image36.png", None, 900),
    # the journey (5)
    "jr-loop": ("image39.png", 5, 1600, 90), "jr-confidence": ("image35.jpg", None, 700), "jr-assurance": ("image37.png", None, 700),
    "jr-trust": ("image43.png", None, 700), "jr-empowerment": ("image56.png", None, 700), "jr-protection": ("image40.png", None, 700),
    # the challenge (6) and the solution (7): the four icons each
    "ch-disoriented": ("image41.png", None, 300), "ch-unsettled": ("image44.png", None, 300), "ch-displaced": ("image50.png", None, 300),
    "ch-disconnected": ("image42.png", None, 300), "ch-familiar": ("image47.png", None, 300), "ch-comfort": ("image48.png", None, 300),
    "ch-spatial": ("image49.png", None, 300), "ch-dynamics": ("image46.png", None, 300),
    # memories (8): the dark campus, the photos, the cut-outs
    "mem-campus": ("image51.png", 8, 2000), "mem-path": ("image86.png", None, 900), "mem-stairs": ("image88.png", None, 900),
    "mem-study": ("image68.png", None, 800), "mem-friends": ("image101.png", None, 900), "mem-cafe": ("image71.png", None, 800),
    "mem-court": ("image62.png", None, 700), "mem-trees": ("image54.png", None, 1536), "mem-people": ("image52.png", None, 1252),
    "mem-people-2": ("image53.png", None, 626),
    # the Möbius (10)
    "mobius": ("image84.png", None, 1536),
    # the loop (11, 12): the ribbon, the people and the animation
    "loop-ribbon": ("image65.png", None, 2007), "loop-people-1": ("image55.jpg", None, 612), "loop-people-2": ("image57.png", None, 783),
    "loop-people-3": ("image58.png", None, 453), "loop-people-4": ("image59.png", None, 2048), "loop-people-5": ("image63.png", None, 1218),
    "loop-people-6": ("image64.png", None, 2048),
    # campus strategy (13): the animated axo of the floor, shot on green (the deck keys the green out; so do we)
    "strategy-anim": ("image75.gif", None, 960, 0, "green"),
    # the challenges (14) and the typologies (15)
    "challenge-axo": ("image61.png", None, 2048),
    "chl-grid": ("image70.png", 14, 400), "chl-compass": ("image90.jpg", 14, 300), "chl-coffee": ("image66.jpg", 14, 300),
    "chl-walk": ("image91.png", 14, 300), "chl-people": ("image69.jpg", 14, 300), "chl-crowd": ("image67.png", 14, 300), "ty-type1": ("image74.png", None, 1400), "ty-type3": ("image72.png", None, 1400),
    "ty-type4": ("image76.png", None, 1400), "ty-icon1": ("image108.png", None, 500), "ty-icon3": ("image120.png", None, 500),
    "ty-icon4": ("image115.png", None, 500),
    # campus palette 01 (16) and its renders (17–19)
    "p1-a": ("image98.jpg", None, 1000), "p1-b": ("image78.png", None, 1000), "p1-c": ("image79.jpg", None, 700), "p1-d": ("image77.jpg", None, 700),
    "p1-e": ("image82.jpg", None, 640), "p1-f": ("image83.jpg", None, 800), "p1-g": ("image80.png", None, 366), "p1-h": ("image85.jpg", None, 853),
    "p1-i": ("image81.png", None, 700), "p1-j": ("image87.png", None, 736), "p1-k": ("image89.jpg", None, 1000), "p1-l": ("image92.jpg", None, 1000),
    "p1-m": ("image95.jpg", None, 1000), "p1-n": ("image94.png", None, 500),
    "p1-render-1": ("image99.png", None, 2048), "p1-render-2": ("image103.jpg", None, 2048), "p1-render-3": ("image96.png", None, 2048),
    # campus palette 02 (20) and its renders (21–23)
    "p2-a": ("image104.jpg", None, 1000), "p2-b": ("image97.png", None, 520), "p2-c": ("image100.png", None, 768), "p2-d": ("image110.png", None, 736),
    "p2-e": ("image107.png", None, 600), "p2-f": ("image113.png", None, 1103), "p2-g": ("image169.png", None, 994), "p2-h": ("image106.png", None, 500),
    "p2-k": ("image116.jpg", None, 736), "p2-l": ("image102.png", None, 614), "p2-m": ("image114.png", None, 736), "p2-n": ("image105.png", None, 432),
    "p2-render-1": ("image112.png", None, 2048), "p2-render-2": ("image118.png", None, 2048), "p2-render-3": ("image121.png", None, 2048),
    # visual direction (24–45): the renders, OP 01 / OP 02
    "r-board-op1": ("image111.png", None, 2048), "r-board-op2": ("image122.png", None, 2048),
    "r-dept-op1": ("image117.png", None, 2048), "r-dept-op2": ("image132.jpg", None, 2048),
    "r-sprint-op1": ("image123.jpg", None, 2048), "r-sprint-op2": ("image127.jpg", None, 2048),
    "r-arena-op1": ("image129.jpg", None, 2048), "r-arena-op2": ("image133.png", None, 2048),
    "r-arena2a-1": ("image143.jpg", None, 2048), "r-arena2a-2": ("image147.jpg", None, 2048),
    "r-library": ("image142.jpg", None, 2048), "r-garden-op1": ("image128.png", None, 2048), "r-garden-op2": ("image137.png", None, 2048),
    "r-exec": ("image124.png", None, 2048), "r-cafe1-op1": ("image130.png", None, 2048), "r-cafe2-op1": ("image134.png", None, 2048),
    "r-cafe1-op2": ("image146.jpg", None, 2048), "r-cafe2-op2": ("image136.png", None, 2048), "r-coffee": ("image166.jpg", None, 2048),
    "r-mothers": ("image160.png", None, 2048), "r-zen": ("image150.png", None, 1514), "r-studio": ("image149.png", None, 2048),
    # the keyplans the renders are marked on (each render crops one of these)
    "kp-119": ("image119.png", None, 2048), "kp-125": ("image125.png", None, 2048), "kp-131": ("image131.png", None, 2048), "kp-135": ("image135.png", None, 2048),
    # value addition (46–52)
    "eng-a": ("image138.png", None, 736), "eng-b": ("image145.png", None, 900), "eng-c": ("image144.png", None, 750), "eng-d": ("image141.png", None, 379),
    "eng-e": ("image140.png", None, 736), "eng-f": ("image148.png", None, 958), "eng-g": ("image151.png", None, 752),
    "mat-tiles": ("image162.jpg", None, 375), "mat-lvt": ("image155.jpg", None, 694), "mat-carpet": ("image156.jpg", None, 1200),
    "mat-gypsum": ("image157.jpg", None, 736), "mat-track": ("image159.jpg", None, 564), "mat-spray": ("image158.jpg", None, 400),
    "mat-baffles": ("image154.jpg", None, 1003), "mat-rugs": ("image165.png", None, 1000), "mat-fabrics": ("image213.png", None, 1024),
    "mat-blinds": ("image153.jpg", None, 480), "mat-acoustic": ("image167.jpg", None, 700), "mat-wood": ("image173.jpg", None, 1025),
    "mat-stone": ("image152.jpg", None, 736),
    "ac-ceiling": ("image161.png", None, 238), "ac-wall": ("image177.png", None, 1200), "ac-partition": ("image164.png", None, 1200),
    "ac-hvac": ("image174.png", None, 1200), "ac-masking": ("image229.gif", None, 800), "ac-door": ("image163.png", None, 1064),
    "wb-daylight": ("image170.jpg", None, 900), "wb-air": ("image222.jpg", None, 1200), "wb-biophilic": ("image178.png", None, 1197),
    "wb-health": ("image189.jpg", None, 736),
    "di-access": ("image182.png", None, 1049), "di-braille": ("image171.png", None, 930), "di-quiet": ("image176.png", None, 768),
    "di-mothers": ("image188.png", None, 1199), "di-gender": ("image175.png", None, 736), "di-alarm": ("image179.png", None, 360),
    "di-zen": ("image196.jpg", None, 600), "di-access-2": ("image172.png", None, 586), "di-braille-2": ("image190.png", None, 532),
    "di-quiet-2": ("image180.png", None, 323), "di-mothers-2": ("image181.png", None, 932),
    "esg-narratives": ("image187.png", None, 1200), "esg-urban": ("image191.png", None, 768), "esg-films": ("image215.jpg", None, 1024),
    "esg-sign": ("image185.png", None, 564), "esg-community": ("image186.png", None, 1055), "esg-wellness": ("image207.jpg", None, 736),
    "esg-ergonomics": ("image183.png", None, 650), "esg-biophilia": ("image184.png", None, 564), "esg-inclusive": ("image193.png", None, 1200),
    "esg-scale": ("image211.jpg", None, 2048),
    "wf-corridor": ("image228.png", None, 2048), "wf-baked": ("image204.png", None, 921), "wf-room": ("image192.png", None, 1080),
    "wf-sign": ("image199.png", None, 864), "wf-tall": ("image194.png", None, 375), "wf-umbrella": ("image195.png", None, 580),
    "wf-car": ("image197.png", None, 740), "wf-corner": ("image205.jpg", None, 2041), "wf-person": ("image198.png", None, 564),
    "wf-sign2": ("image220.png", None, 626), "wf-film": ("image200.png", None, 2048),
    # the layout (53–57): the four plan tiles that make the floor, the type icons, the north point
    "plan-x1": ("image206.png", None, 1449), "plan-x2": ("image212.png", None, 838), "plan-y": ("image208.png", None, 1918),
    "plan-z": ("image209.png", None, 1869), "north": ("image210.png", None, 200),
    "ty-icon2": ("image218.png", None, 500),
    # the schematic axonometrics (58–60)
    "axo-west": ("image224.png", None, 1935), "axo-middle": ("image226.png", None, 1935), "axo-east": ("image227.png", None, 1935),
}


def crop_of(slide, media):
    """the deck's crop (left, top, right, bottom, in %) for that picture on that slide"""
    for r in INV.get(str(slide), []):
        if r["media"] == media:
            return r["crop"]
    raise SystemExit(f"{media} is not on slide {slide}")


def apply_crop(im, c):
    l, t, r, b = c
    W, H = im.size
    box = (round(W * max(0, l) / 100), round(H * max(0, t) / 100), round(W * (1 - max(0, r) / 100)), round(H * (1 - max(0, b) / 100)))
    return im.crop(box)


def fit(im, maxw):
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    return im


def save(im, path):
    alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if alpha else "RGB")
    if alpha and im.getextrema()[3][0] == 255:
        im = im.convert("RGB")
    im.save(path, "WEBP", quality=86 if im.width > 1200 else 88, method=6)


def key_green(im):
    """green screen → transparent, with soft edges and the green spill taken out of what stays"""
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = g - np.maximum(r, b)
    alpha = np.clip(1 - (green - 25) / 70, 0, 1)
    g2 = np.where(green > 0, np.maximum(r, b) + np.minimum(green, 8), g)          # despill
    out = np.dstack([r, g2, b, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def save_anim(blob, path, maxw, key=None):
    src = Image.open(io.BytesIO(blob))
    frames, durs = [], []
    for fr in ImageSequence.Iterator(src):
        f = fr.convert("RGBA")
        if key == "green":
            f = key_green(f)
        frames.append(fit(f, maxw))
        durs.append(fr.info.get("duration", 40))
    frames[0].save(path, "WEBP", save_all=True, append_images=frames[1:], duration=durs, loop=0, quality=74, method=4, lossless=False, allow_mixed=False)


def keyplans(z):
    """camera marks on the keyplans of the render slides (24–45), in % of the keyplan image"""
    W, H = 9144000, 5143500
    out = {}
    for i in range(24, 46):
        x = z.read(f"ppt/slides/slide{i}.xml").decode("utf8")
        kp = [r for r in INV[str(i)] if r["media"] in ("image119.png", "image125.png", "image131.png", "image135.png")]
        mk = None
        for m in re.finditer(r"<p:sp>.*?</p:sp>", x, re.S):
            s = m.group(0)
            if "980000" in s and "custGeom" in s:
                o = re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"', s)
                rot = re.search(r'<a:xfrm[^>]*rot="(-?\d+)"', s)
                X, Y, w, h = (int(v) for v in o.groups())
                mk = ((X + w / 2) / W * 100, (Y + h / 2) / H * 100, int(rot.group(1)) / 60000 if rot else 0)
        if not kp or not mk:
            continue
        k = kp[0]
        bx, by, bw, bh = k["box"]
        l, t, r, b = k["crop"]
        # slide % -> share of the visible (cropped) picture -> share of the whole keyplan image
        u, v = (mk[0] - bx) / bw, (mk[1] - by) / bh
        ix = (l + u * (100 - l - r)) / 100
        iy = (t + v * (100 - t - b)) / 100
        out[i] = {"img": "kp-" + re.sub(r"\D", "", k["media"]), "x": round(ix * 100, 2), "y": round(iy * 100, 2), "rot": round(mk[2], 1),
                  "view": [round(l, 1), round(t, 1), round(100 - r, 1), round(100 - b, 1)]}
    return out


def main():
    deck = sys.argv[1]
    only = sys.argv[2:]
    z = zipfile.ZipFile(deck)
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for name, pick in PICK.items():
        media, crop, maxw = pick[:3]
        turn = pick[3] if len(pick) > 3 else 0
        key = pick[4] if len(pick) > 4 else None
        if only and not any(name.startswith(o) for o in only):
            continue
        blob = z.read("ppt/media/" + media)
        path = os.path.join(OUT, name + ".webp")
        if media.endswith(".gif"):
            save_anim(blob, path, maxw, key)
        else:
            im = Image.open(io.BytesIO(blob))
            im.load()
            if crop:
                im = apply_crop(im, crop_of(crop, media))
            if turn:
                im = im.rotate(turn, expand=True)
            save(fit(im, maxw), path)
        n += 1
        print(f"{name:<22} <- {media:<14} {os.path.getsize(path) // 1024:>6} KB")
    if not only or any(o.startswith("kp") for o in only):
        kp = keyplans(z)
        with open(os.path.join(ROOT, "data", "keyplans.js"), "w", encoding="utf-8") as f:
            f.write("/* generated by tools/acko/extract_assets.py: the camera mark of each render slide on its keyplan image (% of the image) */\n")
            f.write("window.ACKO_KP = " + json.dumps(kp, indent=0).replace("\n", "") + ";\n")
        print(f"keyplans: {len(kp)} render slides")
    print(f"{n} images")


if __name__ == "__main__":
    main()
