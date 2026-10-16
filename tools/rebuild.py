"""Rebuild every generated file from the source drawings and the deck.

Usage (from the project folder):
  python tools/rebuild.py --hover data/src/plan-hover-data.js --deck "<proposal.pptx>"      (current: 09.10 layouts)
  python tools/rebuild.py --op1 "<OP1.dxf>" --op2 "<OP2.dxf>" --deck "<proposal.pptx>" [--mx]  (straight from DXFs)

--hover      the 09.10.2026 test fits, as plan-hover-data.js (built from the DXFs by tools/plan_hover/build_plan_hover.py):
             plan, walls, furniture, the CAD team's MI_* rooms and the team zones. Needs node + puppeteer-core.
--mx         with DXFs: read zones / events / routes / cameras from MX-* layers (see CAD-LAYER-SPEC.md).
--site-mark  a Maps screenshot (SVG) with the site boundary drawn in green: re-register the floor on the satellite.
--under      with --site-mark: a close satellite still (tools/capture_sat.js --zooms 20 --name site) for under the plan.
--site       re-fetch the Street View stills.
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
py = [sys.executable, "-P", "-E"]

ap = argparse.ArgumentParser()
ap.add_argument("--hover"); ap.add_argument("--op1"); ap.add_argument("--op2")
ap.add_argument("--deck", required=True); ap.add_argument("--mx", action="store_true")
ap.add_argument("--site-mark"); ap.add_argument("--under")
ap.add_argument("--site", action="store_true", help="re-fetch the Street View stills (satellite: run tools/capture_sat.js first)")
a = ap.parse_args()
if not a.hover and not (a.op1 and a.op2):
    ap.error("give --hover <plan-hover-data.js> or --op1/--op2 DXFs")


def run(*args):
    print(">", " ".join(os.path.basename(x) if os.sep in x or "/" in x else x for x in args))
    subprocess.run(list(args), check=True, cwd=ROOT)


media = os.path.join(HERE, "_media")
run(*py, os.path.join(HERE, "extract_pptx_media.py"), a.deck, media)
if a.op1 and a.op2:     # the base-building shell and columns always come from the DXFs when they are given
    for n, src in (("1", a.op1), ("2", a.op2)):
        run(*py, os.path.join(HERE, "dxf_to_json.py"), src, os.path.join(ROOT, "data", f"opt{n}.json"), os.path.join(ROOT, "assets", "plans", f"opt{n}_furn.png"))
if a.hover:
    run(*py, os.path.join(HERE, "import_plan_hover.py"), a.hover)
    run("node", os.path.join(HERE, "raster_plan.js"))
elif a.mx:
    run(*py, os.path.join(HERE, "zones_from_mx.py"), a.op1, a.op2, os.path.join(ROOT, "data", "zones.json"))
else:
    run(*py, os.path.join(HERE, "author_zones.py"), os.path.join(ROOT, "data", "zones.json"))
if a.site_mark:
    run(*py, os.path.join(HERE, "site_register.py"), a.site_mark, *(["--under", a.under] if a.under else []))
run(*py, os.path.join(HERE, "build_assets.py"), media)
run(*py, os.path.join(HERE, "extract_skv.py"), a.deck)
if a.site:
    run(*py, os.path.join(HERE, "capture_site.py"))
print("done - open index.html")
