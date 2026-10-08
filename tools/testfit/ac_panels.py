# Zones (AC_NEIGH) and egress routes (AC_FIRE_EXIT) drawn in the panels above and below the layout → zones.json.
# Exits 1 when the drawing has no AC_NEIGH layer, so run.sh falls back to the old panel blocks (dxf_blk.py + panels.py).
import sys, json, ezdxf
TOP_DY, BOT_DY = -53268, 55301      # the top panel sits 53.3 m above the layout, the bottom one 55.3 m below
doc = ezdxf.readfile(sys.argv[1]); msp = doc.modelspace()
found = {'AC_NEIGH': [], 'AC_FIRE_EXIT': []}
def visit(ents, depth=0):
    for e in ents:
        if e.dxftype() == 'INSERT' and depth < 3 and e.dxf.name != 'base':
            try: visit(e.virtual_entities(), depth + 1)
            except Exception: pass
        elif e.dxftype() == 'LWPOLYLINE' and e.dxf.layer in found:
            found[e.dxf.layer].append([(x, y) for x, y, *_ in e.get_points()])
visit(msp)
if not found['AC_NEIGH']: sys.exit(1)
zones = [[(x, y + TOP_DY) for x, y in p] for p in found['AC_NEIGH']]
loop = [[(x, y + BOT_DY) for x, y in p] for p in found['AC_FIRE_EXIT']]
json.dump({'zones': zones, 'loop': loop}, open('zones.json', 'w'))
print('AC zones', len(zones), 'routes', len(loop))
