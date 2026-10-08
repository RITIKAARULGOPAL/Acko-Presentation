#!/usr/bin/env bash
# Rebuild index-testfit.html from a test-fit DXF.
# Usage: tools/testfit/run.sh path/to/ACKO_Testfit.dxf
# Needs: python3 with ezdxf and shapely (pip install ezdxf shapely). Takes a few minutes for a 160 MB DXF.
# The site data (tools/site/context.json) is committed; tools/site/fetch.py + site.py prep refresh it.
set -euo pipefail
DXF=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/../.." && pwd)
WORK=${WORK:-$(mktemp -d)}; mkdir -p "$WORK"
cp "$HERE"/*.py "$HERE"/tf_* "$WORK"/
cd "$WORK"
python3 dxf_flat.py "$DXF" dxf_mid.json -418000 -368000   # layout panel only (y range in mm)
python3 dxf_blocks.py "$DXF" dxf_pos.json                 # every block insert with its position
python3 ac_panels.py "$DXF" || { python3 dxf_blk.py "$DXF" dxf_blk.pkl && python3 panels.py; }   # zones and egress routes (AC_ layers, else the old panel blocks)
python3 extract.py                                        # → realfit.json
python3 gz_extract.py                                     # green zone analysis input: spaces, keep-clear mask, free floor, candidate spots → realfit.json gz
python3 "$HERE/../site/site.py" build realfit.json site.json   # the plan on the site, the sun on the layout → site.json
python3 build_tf.py "$ROOT/index.html" "$ROOT/index-testfit.html"
echo "Built $ROOT/index-testfit.html (work files in $WORK)"
