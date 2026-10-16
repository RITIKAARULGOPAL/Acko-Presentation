"""Option 03's drawing, from the CAD team's two 15.10 files of the 14.10 test fit (the same drawing, same coordinates):
  (2) the base: its new SOC, BOARDROOM and RECEPTION outlines go onto MI_ layers (MI_SOC closed along the prow
      façade, where it is left open; MI_RECEPTION replaces the two open reception pieces); a second copy of the
      floor drawn below the plan is dropped
  (1) adds what (2) lacks: the MI_PRODUCT and MI_SALES CALLING outlines and every MI_ desk hatch (teams.py's seats);
      (1) wraps the drawing in two blocks, exploded first
MI_ outlines whose ends meet within 50 mm are closed.

usage: python tools/plan_hover/combine_1410.py "Testfit -14.10.26 (1).dxf" "Testfit -14.10.26 (2).dxf" "Testfit -14.10.26 combined.dxf"
"""
import math, sys
import ezdxf
from ezdxf.addons import Importer

one, two, out = sys.argv[1:4]
src = ezdxf.readfile(one)
for ins in list(src.modelspace().query("INSERT")):
    ins.explode()
doc = ezdxf.readfile(two)
msp = doc.modelspace()

# (2) carries a second copy of the floor (shell, columns, core) below the plan: keep only what lies on (1)'s plan
from ezdxf import bbox
ext = bbox.extents([e for e in src.modelspace() if e.dxf.hasattr("layer")], fast=True)
x0, y0, x1, y1 = ext.extmin.x - 2000, ext.extmin.y - 2000, ext.extmax.x + 2000, ext.extmax.y + 2000
dropped = 0
for e in list(msp):
    if not e.dxf.hasattr("layer"):
        continue
    b = bbox.extents([e], fast=True)
    if b.has_data and not (x0 <= (b.extmin.x + b.extmax.x) / 2 <= x1 and y0 <= (b.extmin.y + b.extmax.y) / 2 <= y1):
        msp.delete_entity(e); dropped += 1
print(f"from (2): dropped {dropped} entities off the plan (the second copy of the floor)")

take = [e for e in src.modelspace() if e.dxf.hasattr("layer") and
        (e.dxf.layer in ("MI_PRODUCT", "MI_SALES CALLING") or (e.dxftype() == "HATCH" and e.dxf.layer.startswith("MI")))]
imp = Importer(src, doc); imp.import_entities(take, msp); imp.finalize()
print(f"from (1): {len(take)} entities (Product and Sales Calling outlines, desk hatches)")

for e in list(msp.query('LWPOLYLINE[layer=="MI_RECEPTION"]')):
    if not e.closed:
        msp.delete_entity(e)
for old, new in (("SOC", "MI_SOC"), ("BOARDROOM", "MI_BOARDROOM"), ("RECEPTION", "MI_RECEPTION")):
    for e in msp.query(f'LWPOLYLINE[layer=="{old}"]'):
        e.dxf.layer = new
        if not e.closed:
            e.close(True); print(f"  {new}: closed (it was open)")
        print(f"  {old} -> {new}")
for e in msp.query("LWPOLYLINE"):
    if e.dxf.layer.upper().startswith("MI") and not e.closed:
        p = e.get_points()
        if math.dist(p[0][:2], p[-1][:2]) < 50:
            e.close(True)
for name in ("MI_SOC", "MI_BOARDROOM"):
    if name not in doc.layers:
        doc.layers.add(name)
doc.saveas(out)
print("wrote", out)
