"""Fetch the site imagery used in the presentation (Imagery (c) Google).

Usage: python tools/capture_site.py [--sat <dir with sat_zNN.png from capture_sat.js>]

* Street View stills come from Google's public thumbnail endpoint (1024x512).
* Satellite stills are captured with tools/capture_sat.js (needs Node and
  `npm i puppeteer-core`, drives the installed Chrome) and converted here.
"""
import os, io, sys, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "site")
os.makedirs(OUT, exist_ok=True)

# name: (panorama id, heading, pitch) - pitch is negative to look up
STREET = {
    "sv-across": ("jfA3SHxyA_VAmL-ID_XKDQ", 320, -12),   # across the ORR, under the metro
    "sv-road": ("NoDoVm0PKk-0q_7mWK7xrw", 310, -18),     # ORR service road, façade behind trees
    "sv-road-2": ("NoDoVm0PKk-0q_7mWK7xrw", 280, -15),
    "sv-gate": ("fQBLIydBSkkQZpf-pWtIdw", 230, -12),     # the entry gate
    "sv-entry": ("fQBLIydBSkkQZpf-pWtIdw", 320, -15),    # entry forecourt, glazed façade in view
}
for name, (pid, yaw, pitch) in STREET.items():
    url = (f"https://streetviewpixels-pa.clients6.google.com/v1/thumbnail?cb_client=maps_sv.tactile"
           f"&w=1024&h=512&pitch={pitch}&panoid={pid}&yaw={yaw}")
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    Image.open(io.BytesIO(data)).convert("RGB").save(os.path.join(OUT, name + ".webp"), "WEBP", quality=86)
    print("street view", name)

if "--sat" in sys.argv:
    src = sys.argv[sys.argv.index("--sat") + 1]
    for f in sorted(os.listdir(src)):
        if f.startswith("sat_z") and f.endswith(".png"):
            Image.open(os.path.join(src, f)).convert("RGB").save(os.path.join(OUT, f.replace(".png", ".webp")), "WEBP", quality=82)
            print("satellite", f)
