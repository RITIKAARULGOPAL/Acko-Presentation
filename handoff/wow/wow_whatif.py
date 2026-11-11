# What if, folded into the memories (Ritika, 10 Nov: "B is fine, but the narrative is the gap"; wording: ACKO's own promise).
# slides/s-memories.html gets two closing beats, over the dimmed campus, when the slide carries .mem-wi (gen_approach.py's fold(),
# index-approach.html only; the live deck has no .mem-wi and behaves as before):
#   7 · "A campus is where we first felt safe among people." / "Protection is what ACKO promises its customers."
#   8 · "What if the workplace kept that promise to its own people?" / "So we started where it has to happen: one floor in Koramangala."
# run before gen_approach.py: python wow_whatif.py <deck-wow checkout>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

p = "slides/s-memories.html"; s, nl = rd(p)
if "mem-wi" not in s:
    s = sub1(s, "    step(k) { beat(k); },",
        "    // the close, folded in (10 Nov, the re-ordered deck, where the slide has .mem-wi and 8 beats): the campus dims, then the feeling\n"
        "    // and ACKO's promise (7), the question and where it has to happen (8); the memories stay as beat 6 left them, so stepping\n"
        "    // 6 → 7 → 6 doesn't replay the sixth\n"
        "    step(k, sc) {\n"
        "      const w = sc && sc.querySelector(\".mem-wi\"), b = Math.min(k, 6);\n"
        "      if (!(w && b === 6 && sc.dataset.mb === \"6\")) beat(b);\n"
        "      if (sc) sc.dataset.mb = String(b);\n"
        "      if (w) { w.classList.toggle(\"on\", k >= 7); w.classList.toggle(\"on2\", k >= 8); }\n"
        "    },", "step")
    s = sub1(s, "      plain();\n      if (!S) S = build", "      plain(); sc.dataset.mb = \"\";\n      if (!S) S = build", "enter")
    W = "#s-memories .mem-wi"
    s = sub1(s, "</style>",
        "/* the close, folded in (10 Nov, the re-ordered deck only): a scrim over the campus; the lines written in, word by word */\n"
        f"{W} {{ left: 0; top: 0; width: 100%; height: 100%; z-index: 6; display: flex; align-items: center; box-sizing: border-box;\n"
        "  padding: 0 calc(var(--pw) * .017 + var(--pt) * 7.2); background: rgba(8, 8, 8, 0); pointer-events: none;\n"
        "  -webkit-backdrop-filter: blur(0px); backdrop-filter: blur(0px); transition: background .9s var(--ease), backdrop-filter .9s var(--ease), -webkit-backdrop-filter .9s var(--ease); }\n"
        "/* nearly opaque, and what's behind blurred: the campus a soft dark ghost, no label or photo edge reading through the lines (10 Nov) */\n"
        f"{W}.on {{ background: rgba(8, 8, 8, .93); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px); }}\n"
        f"{W} .mw-col {{ display: flex; flex-direction: column; gap: calc(var(--pt) * 10); }}\n"
        f"{W} p {{ margin: 0; text-align: left; transition: opacity .8s var(--ease), transform .8s var(--ease); }}\n"
        f"{W} .wi-h {{ font-family: var(--hand); font-weight: 400; color: #fff; }}\n"
        f"{W} .mw-l1 .wi-h {{ font-size: calc(var(--pt) * 22); }}\n"
        f"{W} .mw-l2 {{ font-size: calc(var(--pt) * 16); color: rgba(255,255,255,.85); opacity: 0; transform: translateY(6px); }}\n"
        f"{W} .mw-l2 b {{ color: var(--lilac, #c9b3f3); }}\n"
        f"{W}.on .mw-l2 {{ opacity: 1; transform: none; transition-delay: 1.9s; }}\n"
        f"{W} .mw-q {{ margin-top: calc(var(--pt) * 14); line-height: 1.15; }}\n"
        f"{W} .mw-q .wi-h {{ font-size: calc(var(--pt) * 30); }}\n"
        f"{W} .mw-q b {{ font-family: var(--body); font-weight: 700; font-size: calc(var(--pt) * 28); color: var(--lilac, #c9b3f3); }}\n"
        f"{W} .mw-l4 {{ font-style: italic; font-size: calc(var(--pt) * 11); color: rgba(255,255,255,.62); opacity: 0; transform: translateY(6px); }}\n"
        f"{W}.on2 .mw-l4 {{ opacity: 1; transform: none; transition-delay: 2.6s; }}\n"
        f"{W}.on2 :is(.mw-l1, .mw-l2) {{ opacity: .45; transition-delay: 0s; }}\n"
        f"{W} .w {{ display: inline-block; opacity: 0; filter: blur(5px); transform: translateY(.12em); transition: opacity .6s var(--ease), filter .6s var(--ease), transform .6s var(--ease); }}\n"
        f"{W}.on .mw-l1 .w {{ opacity: 1; filter: none; transform: none; transition-delay: calc(.5s + var(--w) * 90ms); }}\n"
        f"{W}.on2 .mw-q .w {{ opacity: 1; filter: none; transform: none; transition-delay: calc(.4s + var(--w) * 90ms); }}\n"
        "/* stepping back: what goes, goes at once */\n"
        f"{W}:not(.on) :is(p, .w), {W}:not(.on2) :is(.mw-q .w, .mw-l4) {{ transition-delay: 0s !important; }}\n"
        "</style>", "css")
    wr(p, s, nl)
print("ok whatif")
