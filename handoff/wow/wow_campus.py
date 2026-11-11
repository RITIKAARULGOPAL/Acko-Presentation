# The people's challenge → Where both meet, without the gap (Ritika, 10 Nov: "these 2 slides have a gap"). Only with window.ACKO_WOW.
# Story: one small question on Where both meet's first beat: "What makes one place feel like home? We looked at two things."
# Visual: arriving from the challenge, its lavender stays under both pages (no black mid-fade), Where both meet's panels start in
# that lavender with their seam on the challenge's vertical line (44.7%), then the seam glides to the centre and the panels warm to lilac.
# run after wow_approach.py: python wow_campus.py <deck-wow checkout>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

# ---- the challenge: leaving, it hands over its lavender
p = "slides/s-challenge.html"; s, nl = rd(p)
if 'mark("s-challenge"' not in s:
    s = sub1(s, '  step(k, sc) { const pg = $(".page", sc); pg.classList.toggle("b2", k >= 2); pg.classList.toggle("b3", k >= 3); },\n}));',
        '  step(k, sc) { const pg = $(".page", sc); pg.classList.toggle("b2", k >= 2); pg.classList.toggle("b3", k >= 3); },\n'
        '  // to Where both meet (10 Nov, the re-ordered deck): its lavender, which that slide\'s panels start in\n'
        '  leave() { if (window.ACKO_WOW && window.ACKO_MORPH) window.ACKO_MORPH.mark("s-challenge", { bg: getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() || "#d2c9eb" }); },\n'
        '}));', "challenge leave")
    wr(p, s, nl)

# ---- Where both meet: the question, and the seam carried over
p = "slides/s-campus.html"; s, nl = rd(p)
if "cp-q" not in s:
    s = sub1(s, '    <div class="col cl rv"',
        '    <p class="cp-q">What makes one place feel like home? We looked at two things.</p>\n    <div class="col cl rv"', "kicker")
    s = sub1(s, "#s-campus .meet { text-align: center; }",
        "/* the re-ordered deck only (ACKO_WOW, 10 Nov): the question on beat 1, and the panels carried over from the challenge's lavender */\n"
        "#s-campus .cp-q { display: none; left: 50%; top: 13%; transform: translateX(-50%); white-space: nowrap; margin: 0; padding: calc(var(--pt) * 3) calc(var(--pt) * 10); background: var(--lilac, #c9b3f3); text-align: center; font-style: italic; font-size: calc(var(--pt) * 11); color: rgba(0,0,0,.62); }\n"
        "#s-campus .cp-wow .cp-q { display: block; opacity: 0; transition: opacity .5s var(--ease); }\n"
        "#s-campus .cp-wow.drawn:not(.b2) .cp-q { opacity: 1; transition: opacity .8s var(--ease) .9s; }\n"
        "#s-campus .cp-wow .pn { transition: transform 1.1s var(--ease), background-color 1.1s var(--ease), box-shadow 1.1s var(--ease); }\n"
        "#s-campus .cp-from .pn { background: var(--cp-from, #d2c9eb); transition: none; }\n"
        "#s-campus .cp-from .pl { transform: translateX(-10.6%); box-shadow: inset -1px 0 0 rgba(255,255,255,.55); }\n"
        "#s-campus .cp-from .pr { transform: translateX(-10.6%); }\n"
        "#s-campus .meet { text-align: center; }", "css")
    s = sub1(s, "    plain(); const pg = $(\".page\", sc); pg.classList.remove(\"drawn\"); void pg.offsetWidth;\n",
        "    plain(); const pg = $(\".page\", sc); pg.classList.remove(\"drawn\", \"cp-from\"); void pg.offsetWidth;\n"
        "    // from the people's challenge (10 Nov, the re-ordered deck): its lavender stays under both pages while they cross, and the\n"
        "    // panels start in it with their seam where the challenge's line stood (44.7%), then glide to the centre and warm to lilac\n"
        "    pg.classList.toggle(\"cp-wow\", !!window.ACKO_WOW);\n"
        "    const f = window.ACKO_WOW && window.ACKO_MORPH && !reduced ? window.ACKO_MORPH.take(\"s-challenge\") : null;\n"
        "    const stage = document.getElementById(\"stage\");\n"
        "    if (f && stage) {\n"
        "      const under = document.createElement(\"div\");\n"
        "      under.style.cssText = \"position:fixed;left:var(--pl);top:var(--ptop);width:var(--pw);height:var(--ph);pointer-events:none;z-index:0;background:\" + f.bg;\n"
        "      stage.insertBefore(under, stage.firstChild);\n"
        "      pg.style.setProperty(\"--cp-from\", f.bg); pg.classList.add(\"cp-from\"); void pg.offsetWidth;\n"
        "      setTimeout(() => pg.classList.remove(\"cp-from\"), 250);\n"
        "      setTimeout(() => under.remove(), 1500);\n"
        "    }\n", "enter")
    wr(p, s, nl)
print("ok campus")
