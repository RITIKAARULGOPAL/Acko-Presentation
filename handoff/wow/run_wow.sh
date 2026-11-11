#!/bin/sh
# The re-ordered deck (index-approach.html) with its big moments, and the live deck (index.html), rebuilt from these generators
# into the deck-wow checkout (branch deck/wow).
#   sh handoff/wow/run_wow.sh                      # the deck-wow worktree at its usual place
#   sh handoff/wow/run_wow.sh "<deck checkout>"    # or another checkout of deck/wow
# Order matters: gen_floorflow.py regenerates slides/s-layout-dd.html and s-layout-sp.html from slides/s-layout.html, and the
# wow_*.py patches after it change those copies (and a few shared slides, each guarded by window.ACKO_WOW); gen_approach.py then
# builds index-approach.html, and tools/build.py the live index.html from slides/order.txt.
S="$(cd "$(dirname "$0")" && pwd)"
B="${1:-C:/Users/Ritika/Acko 1610/.claude/worktrees/deck-wow}"
set -e
python "$S/gen_floorflow.py" "$B" >/dev/null
python "$S/wow_loop.py" "$B"
python "$S/wow_sundd.py" "$B"
python "$S/wow_ddshell.py" "$B"
python "$S/wow_build.py" "$B"
python "$S/wow_rise.py" "$B"
python "$S/wow_people.py" "$B"
python "$S/wow_nbsheet.py" "$B"
python "$S/wow_approach.py" "$B"
python "$S/wow_campus.py" "$B"
python "$S/wow_whatif.py" "$B"
python "$S/wow_thanks.py" "$B"
python "$S/wow_walk.py" "$B"
cd "$B" && python "$S/gen_approach.py" "$B" 2>&1 | grep -v note: ; python tools/build.py >/dev/null 2>&1
echo "index: $(grep -o 'class="scene[^"]*" id="[^"]*"' index.html | wc -l) slides"
# gen_proposal.py (the 3 Nov design proposal PDF: renders, palette, materials) runs on its own, only when the PDF changes:
#   python handoff/wow/gen_proposal.py "<proposal.pdf>" "<deck checkout>"   (PyMuPDF + Pillow), then this script again
