# Problem first (Ritika, 10 Nov): the Loop now comes straight before the Campus strategy. Arriving from the Loop lying on the floor
# (s-loop-w beat 3, drawn where the Layout's plan sits), the strategy's model starts looking straight down on that same footprint and
# rises into its axo while the building assembles. Only with window.ACKO_WOW. run after wow_build.py: python wow_rise.py <deck-wow>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
p = "slides/s-strategy.html"; s, nl = rd(p)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
if 'take("s-loop-w")' not in s:
    s = sub1(s, 'ACKO.slide("s-strategy", ({ $, $$, reduced, plain, reveal, cue }) => {', 'ACKO.slide("s-strategy", ({ $, $$, reduced, plain, reveal, cue, plan }) => {', "factory")
    s = sub1(s, "      const ok = start();\n      sc.classList.toggle(\"st-fallback\", !ok);\n      if (!ok) return;\n",
        "      const ok = start();\n      sc.classList.toggle(\"st-fallback\", !ok);\n      if (!ok) return;\n"
        "      // from the Loop lying on the floor (10 Nov, problem first): straight down on the plan's footprint, rising into the axo\n"
        "      const fl = window.ACKO_WOW && window.ACKO_MORPH && !reduced ? window.ACKO_MORPH.take(\"s-loop-w\") : null;\n"
        "      if (fl && plan && plan.data) {\n"
        "        const [x, y, w, h] = plan.data.viewBox, vb = plan.vbFor([x, y, x + w, y + h], [35, 157, 1885, 670]);\n"
        "        const top = { theta: 0, phi: 1e-4, half: vb[3] / 2000, t: [(vb[0] + vb[2] / 2 - 185842 - M.CX) / 1000, 0, (vb[1] + vb[3] / 2 + 182802 - M.CY) / 1000] };\n"
        "        S.state = top; S.tween = { from: top, to: S.home, t0: performance.now(), ms: 2400 }; need();\n"
        "      }\n", "enter")
    wr(p, s, nl)
# the neighbourhoods by number only on this deck (11 Nov, Ritika: "remove the terms life, auto, drive and only have neighbourhood 01, 02")
s, nl = rd(p)
if "NB_NUM" not in s:
    s = sub1(s, '["ACKO Café", "cafezone", "S", "#8f8a5c", 2]];\n' if '["ACKO Café"' in s else '["Café", "cafezone", "S", "#8f8a5c", 2]];\n',
        ('["ACKO Café", "cafezone", "S", "#8f8a5c", 2]];\n' if '["ACKO Café"' in s else '["Café", "cafezone", "S", "#8f8a5c", 2]];\n') +
        "  if (window.ACKO_WOW) LABELS.slice(0, 6).forEach((l, i) => { l[0] = \"Neighbourhood \" + String(i + 1).padStart(2, \"0\"); });   // NB_NUM: by number, on the re-ordered deck\n", "labels")
    wr(p, s, nl)
print("ok rise")
