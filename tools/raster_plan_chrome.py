"""raster_plan.js without puppeteer: the same furniture texture (assets/plans/<opt>_furn.png, 80 px/m, white on
transparent) from tools/_raster/<opt>.svg (written by import_plan_hover.py), rendered by headless Chrome's own
--screenshot. As raster_plan.js: every <use> is expanded into a plain group first (browsers ignore non-scaling strokes
inside <use>), drawn white on black, then alpha = brightness.

usage: python tools/raster_plan_chrome.py opt3 [out.png]
"""
import os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

opt = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets", "plans", f"{opt}_furn.png")
svg = open(os.path.join(HERE, "_raster", f"{opt}.svg"), encoding="utf-8").read()
W, H = (int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', svg[:300]).groups())
page = f"""<!doctype html><html><head><style>html,body{{margin:0;background:#000;overflow:hidden}}svg{{display:block}}</style></head>
<body>{svg}<script>
const svg = document.querySelector("svg"), NS = "http://www.w3.org/2000/svg";
const defs = new Map([...svg.querySelectorAll("defs > g[id]")].map((g) => [g.id, g]));
svg.querySelectorAll("use").forEach((u) => {{
  const src = defs.get((u.getAttribute("href") || "").slice(1)), g = document.createElementNS(NS, "g");
  g.setAttribute("transform", u.getAttribute("transform") || "");
  if (src) for (const ch of src.children) g.appendChild(ch.cloneNode(true));
  u.replaceWith(g);
}});
svg.querySelector("defs")?.remove();
</script></body></html>"""
tmp = tempfile.mkdtemp(prefix="raster_")
html, shot = os.path.join(tmp, "page.html"), os.path.join(tmp, "shot.png")
open(html, "w", encoding="utf-8").write(page)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={W},{H}", "--virtual-time-budget=20000", f"--screenshot={shot}", "file:///" + html.replace(os.sep, "/")],
               check=True, capture_output=True)
im = Image.open(shot).convert("RGB").crop((0, 0, W, H))
alpha = Image.fromarray(np.asarray(im).max(axis=2))              # white lines on black -> white on transparent, alpha = brightness
res = Image.new("RGBA", (W, H), (255, 255, 255, 0)); res.putalpha(alpha)
res.save(out)
print(opt, "->", out, f"{W}x{H}", os.path.getsize(out) // 1024, "KB")
