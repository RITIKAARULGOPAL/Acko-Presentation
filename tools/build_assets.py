"""Copy deck media into assets/img, make logo variants, and bundle data as JS.

The presentation must open by double-clicking index.html (file://), so data is
shipped as classic <script> files (no fetch) and the furniture textures are
embedded as data URIs (WebGL refuses file:// images as cross-origin).

Usage: python build_assets.py <deck_media_dir>     (deck images + data)
       python build_assets.py --data-only     (just re-bundle data/*.json and the plan textures)
"""
import sys, os, json, base64, io, shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ONLY = sys.argv[1] == "--data-only"

if not DATA_ONLY:
    media = sys.argv[1]
    IMG = os.path.join(ROOT, "assets", "img")
    os.makedirs(IMG, exist_ok=True)

    PICK = {
        "s29_00": "reception", "s30_00": "breakout", "s31_00": "meeting6", "s32_00": "boardroom",
        "s33_00": "soc", "s34_01": "soc-night", "s28_03": "moodboard", "s17_00": "living-ring",
        "s16_01": "human-centric", "s15_01": "purpose", "s15_00": "access", "s15_05": "future",
        "s15_06": "trust", "s16_02": "intelligent", "s16_03": "adaptive", "s16_04": "immersive", "s16_00": "distinctive",   # Sathwick 15.10: the three were rotated
        "s18_00": "network-gradient", "s21_00": "zoning-o1", "s23_00": "zoning-o2", "s22_00": "plan-o1", "s24_00": "plan-o2",
        "s35_00": "axo-o1-50", "s35_01": "axo-o1-100", "s35_02": "axo-o1-200",
        "s35_03": "axo-o2-50", "s35_04": "axo-o2-100", "s35_05": "axo-o2-200",
        # kits of parts
        "s36_11": "mat-oak-chevron", "s36_07": "mat-oak", "s36_06": "mat-acoustic-felt", "s36_02": "mat-stone-dark",
        "s36_10": "mat-tile", "s36_05": "mat-metal-mesh", "s36_03": "mat-baffles", "s36_12": "mat-spray-acoustic",
        "s36_08": "mat-fabric", "s38_02": "mat-biophilia", "s36_04": "mat-gypsum",
        # employee experience: furniture concepts
        "s38_07": "ex-touchdown", "s38_03": "ex-collab", "s36_01": "ex-lounge", "s38_01": "ex-focus",
        "s36_13": "ex-cafe", "s38_06": "ex-meet",
        "s28_00": "insp-slats-green",
        "s28_01": "insp-slats-black",
        "s28_02": "insp-perforated",
        "s28_05": "insp-plant",
        "s28_06": "insp-fabrics",
        "s28_07": "insp-pendant",
        "s28_08": "insp-chair",
        "s36_09": "mat-carpet",
        "s36_00": "mat-acrylic",
        "s37_01": "acou-ceiling",
        "s37_00": "acou-wall",
        "s37_02": "acou-partition",
        "s37_03": "acou-hvac",
        "s37_05": "acou-masking",
        "s37_04": "acou-glazing",
        "s38_00": "brand-narratives",
        "s38_05": "brand-tech",
        "s38_04": "brand-inclusive",
        "s38_08": "brand-inlay",
        "s38_09": "brand-corners",
        "s38_10": "brand-sign",
    }
    for src, dst in PICK.items():
        shutil.copyfile(os.path.join(media, src + ".webp"), os.path.join(IMG, dst + ".webp"))
    # slide 17 shows the planted ring cropped (l 8.296 %, r 25.228 %) and turned 90° clockwise: the same band for the Living Network
    ring = Image.open(os.path.join(IMG, "living-ring.webp")).convert("RGB"); rw, rh = ring.size
    ring.crop((round(rw * 0.08296), 0, round(rw * (1 - 0.25228)), rh)).rotate(-90, expand=True).save(os.path.join(IMG, "living-ring-band.webp"), quality=84)

    # logos -----------------------------------------------------------------
    def knockout(im, invert_dark):
        """White background -> transparent; optionally turn black ink white (for dark UI)."""
        im = im.convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                light = min(r, g, b)
                greenish = g - max(r, b) > 40
                if greenish:
                    px[x, y] = (r, g, b, a)
                    continue
                alpha = int((255 - light) * a / 255)        # dark ink -> opaque
                ink = 245 if invert_dark else 20
                px[x, y] = (ink, ink, ink, alpha)
        return im

    logo = Image.open(os.path.join(media, "s01_02.webp"))
    knockout(logo, False).save(os.path.join(IMG, "mitigata-ink.png"))
    knockout(logo, True).save(os.path.join(IMG, "mitigata-light.png"))
    # cover wordmark without the "FULL STACK CYBER RESILIENCE" tagline, as on the deck's cover (slide 1)
    for v in ("ink", "light"):
        im = Image.open(os.path.join(IMG, f"mitigata-{v}.png"))
        im.crop((0, 0, im.width, round(im.height * 0.74))).save(os.path.join(IMG, f"mitigata-cover-{v}.png"))
    skv = Image.open(os.path.join(media, "s01_00.webp")).convert("RGBA")
    px = skv.load()
    for y in range(skv.height):
        for x in range(skv.width):
            r, g, b, a = px[x, y]
            if a and max(r, g, b) < 90:
                px[x, y] = (240, 240, 240, a)
    skv.save(os.path.join(IMG, "skv-light.png"))
    shutil.copyfile(os.path.join(media, "s01_00.webp"), os.path.join(IMG, "skv-ink.webp"))

    # logo green (most saturated green pixels)
    g = [p for p in Image.open(os.path.join(media, "s01_02.webp")).convert("RGB").getdata() if p[1] - max(p[0], p[2]) > 80]
    g.sort(key=lambda p: p[1]); mid = g[len(g) // 2]
    print("logo green", "#%02x%02x%02x" % mid)

# data bundle -----------------------------------------------------------
DATA = os.path.join(ROOT, "data")
def furn_uri(name):
    im = Image.open(os.path.join(ROOT, "assets", "plans", name))
    buf = io.BytesIO(); im.save(buf, "WEBP", lossless=False, quality=88, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()

OPTS = [o for o in ("opt1", "opt2", "opt3") if os.path.exists(os.path.join(DATA, o + ".json"))]   # opt3: the 14.10 test fit
bundle = {o: json.load(open(os.path.join(DATA, o + ".json"))) for o in OPTS}
bundle["zones"] = json.load(open(os.path.join(DATA, "zones.json")))
if os.path.exists(os.path.join(DATA, "site.json")):          # floor plate registered on the satellite (tools/site_register.py)
    bundle["site"] = json.load(open(os.path.join(DATA, "site.json")))
with open(os.path.join(DATA, "plan-data.js"), "w") as f:
    f.write("/* generated by tools/build_assets.py from the test-fit DXFs - do not edit */\n")
    f.write("window.MX_DATA=" + json.dumps(bundle, separators=(",", ":")) + ";\n")
with open(os.path.join(DATA, "plan-textures.js"), "w") as f:
    f.write("/* furniture + planting linework, rasterised from the DXFs */\n")
    f.write("window.MX_TEX=" + json.dumps({"opt1": furn_uri("opt1_furn.png"), "opt2": furn_uri("opt2_furn.png")}) + ";\n")
for n in ("plan-data.js", "plan-textures.js"):
    print(n, os.path.getsize(os.path.join(DATA, n)) // 1024, "KB")
