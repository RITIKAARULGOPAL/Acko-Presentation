# How we worked → the people's challenge, bridged in story and on screen (Ritika, 10 Nov).
# slides/s-approach-w.html: this deck's How we worked (people first, the six stages in the deck's order), one click.
# slides/s-start.html (new): "Where it starts", its own slide ("this whole slide is too cluttered"): the six stages, larger; the rest step
# back and Understand · the people stays; then the move, said: about 640 Ackers, from two offices, onto one floor. So we began with them.
# s-challenge (guarded by window.ACKO_WOW): arriving from s-start, its lavender grows as a circle out of the Understand dot.
# run: python wow_approach.py <deck-wow checkout>
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

OLD_STRIP = '''<li style="--i:3"><i></i><b>Discover</b><span class="hand">the site</span></li>
      <li style="--i:4"><i></i><b>Map</b><span class="hand">the possibilities</span></li>
      <li style="--i:5"><i></i><b>Spot</b><span class="hand">the opportunity</span></li>
      <li style="--i:6"><i></i><b>Frame</b><span class="hand">the idea</span></li>
      <li style="--i:7"><i></i><b>Layer</b><span class="hand">the lenses</span></li>
      <li style="--i:8"><i></i><b>Shape</b><span class="hand">the plan</span></li>'''
NEW_STRIP = '''<li style="--i:3"><i></i><b>Understand</b><span class="hand">the people</span></li>
      <li style="--i:4"><i></i><b>Spot</b><span class="hand">the opportunity</span></li>
      <li style="--i:5"><i></i><b>Discover</b><span class="hand">the site</span></li>
      <li style="--i:6"><i></i><b>Frame</b><span class="hand">the idea</span></li>
      <li style="--i:7"><i></i><b>Shape</b><span class="hand">the plan</span></li>
      <li style="--i:8"><i></i><b>Layer</b><span class="hand">the lenses</span></li>'''

# ---- How we worked, this deck's way: one click
src, nl = rd("slides/s-approach.html")
s = re.sub(r"(?<![/\w-])s-approach\b", "s-approach-w", src)
s = sub1(s, "How we worked: we let the site lead, and the concept followed. Every decision grew from the site itself: we explored its potential, embraced its character, and let the layout take shape naturally. Six steps: discover the site, map the possibilities, spot the opportunity, frame the idea, layer the lenses, shape the plan.",
         "How we worked: we began with what people need, from the brief and the research, let the site set the terms, and the concept followed. Six stages, in the order of this deck: understand the people, spot the opportunity, discover the site, frame the idea, shape the plan, layer the lenses.", "notes")
s = sub1(s, '<h2 style="--i:1">We let the site lead, <span>and the concept followed.</span></h2>',
         '<h2 style="--i:1">We began with what people need, <span>let the site set the terms, and the concept followed.</span></h2>', "h2")
s = sub1(s, '<p style="--i:2">Every decision grew from the site itself. We explored its potential, embraced its character, and let the layout take shape naturally.</p>',
         '<p style="--i:2">Every decision began with what the brief and the research say people need, then grew from the site itself.</p>', "p")
s = sub1(s, OLD_STRIP, NEW_STRIP, "strip")
wr("slides/s-approach-w.html", s, nl)

# ---- Where it starts: its own slide, built from How we worked's frame (head, foot, the strip's look)
head = src[: src.index("<!-- slide:start -->")].replace("How we worked · ACKO slide s-approach", "Where it starts · ACKO slide s-start")
foot = src[src.index("<!-- slide:end -->"):]
strip_css = re.findall(r"#s-approach \.ap-steps[^\n]*\n", src)
strip_css = "".join(l.replace("#s-approach ", "#s-start ") for l in strip_css)
html = head + '''<!-- slide:start -->
<section class="scene" id="s-start" data-part="cover" data-title="Where it starts" data-steps="1" data-mins="0.3"
  data-notes="Where it starts: of the six stages, the first, understand the people. About 640 Ackers, from two offices, onto one floor. So we began with them.">
  <div class="page">
    <div class="st-k rv" style="left:8%;top:21%;width:60%"><small style="--i:0">Where it starts</small></div>
    <ol class="ap-steps rv" style="left:8%;top:35%;width:84%">
      ''' + NEW_STRIP + '''
    </ol>
    <div class="st-line" style="left:8%;top:62%;width:84%"><p>About <b>640 Ackers</b>, from two offices, onto one floor.</p><span class="hand">So we began with them.</span></div>
  </div>
</section>
<style>
/* where it starts (10 Nov): the six stages, larger; the rest step back and Understand · the people stays; then the move, said */
#s-start .st-k small { display: block; font-size: calc(var(--pt) * 9); font-style: italic; color: #555; }
''' + strip_css + '''#s-start .ap-steps li { padding-top: calc(var(--pt) * 28); transition: opacity .7s var(--ease); }
#s-start .ap-steps i { width: calc(var(--pt) * 13); height: calc(var(--pt) * 13); transition: transform .7s var(--ease), box-shadow .7s var(--ease); }
#s-start .ap-steps li::before { top: calc(var(--pt) * 6.5); }
#s-start .ap-steps b { font-size: calc(var(--pt) * 15); }
#s-start .ap-steps .hand { font-size: calc(var(--pt) * 19); }
#s-start .page.lit .ap-steps li:not(:first-child) { opacity: .26 !important; }
#s-start .page.lit .ap-steps li:first-child i { transform: scale(1.45); box-shadow: 0 0 0 calc(var(--pt) * 5) rgba(82, 34, 208, .14); }
#s-start .st-line { opacity: 0; transform: translateY(calc(var(--pt) * 5)); transition: opacity .8s var(--ease), transform .8s var(--ease); }
#s-start .page.said .st-line { opacity: 1; transform: none; }
#s-start .st-line p { margin: 0; font-size: calc(var(--pt) * 22); line-height: 1.2; color: var(--purple-2); }
#s-start .st-line b { font-weight: 700; color: var(--purple); }
#s-start .st-line .hand { display: block; margin-top: calc(var(--pt) * 8); font-size: calc(var(--pt) * 20); color: var(--hand-ink); }
</style>
<script>
/* where it starts: the six stages as How we worked left them, then the rest step back and the first stays; then the move, said.
   Leaving, it hands the Understand dot's place to the people's challenge, whose lavender grows out of it */
ACKO.slide("s-start", ({ $, plain, reveal, later, reduced }) => ({
  enter(_, sc) {
    plain(); const pg = $(".page", sc); pg.classList.remove("lit", "said"); void pg.offsetWidth;
    reveal($(".st-k", sc), 80); reveal($(".ap-steps", sc), 90);
    if (reduced) { pg.classList.add("lit", "said"); return; }
    later(() => pg.classList.add("lit"), 1300);
    later(() => pg.classList.add("said"), 2000);
  },
  leave(_, sc) {
    if (!sc || !window.ACKO_MORPH) return;
    const pg = $(".page", sc).getBoundingClientRect(), d = $(".ap-steps li i", sc).getBoundingClientRect();
    window.ACKO_MORPH.mark("s-approach", { x: (d.left + d.width / 2 - pg.left) / pg.width, y: (d.top + d.height / 2 - pg.top) / pg.height });
  },
}));
</script>
''' + foot
wr("slides/s-start.html", html, nl)

# ---- s-challenge: its lavender grows out of the Understand dot (only with ACKO_WOW, and only arriving from s-start)
p = "slides/s-challenge.html"; s, nl = rd(p)
if 'take("s-approach")' not in s:
    s = sub1(s, '  enter(_, sc) { plain(); sc.querySelectorAll(".rv").forEach((e) => reveal(e, 120)); },',
        '''  enter(_, sc) {
    plain(); sc.querySelectorAll(".rv").forEach((e) => reveal(e, 120));
    // from Where it starts (10 Nov, the re-ordered deck): the lavender grows as a circle out of the Understand dot, on a white
    // ground, both under the pages (first in #stage), gone once the world has turned lavender itself
    const f = window.ACKO_WOW && window.ACKO_MORPH && !matchMedia("(prefers-reduced-motion: reduce)").matches ? window.ACKO_MORPH.take("s-approach") : null;
    const stage = document.getElementById("stage");
    if (f && stage) {
      const box = "position:fixed;left:var(--pl);top:var(--ptop);width:var(--pw);height:var(--ph);pointer-events:none;z-index:0";
      const white = document.createElement("div"), lav = document.createElement("div");
      white.style.cssText = box + ";background:#fff";
      lav.style.cssText = box + ";background:" + (getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() || "#d2c9eb");
      const at = `${(f.x * 100).toFixed(2)}% ${(f.y * 100).toFixed(2)}%`;
      lav.style.clipPath = `circle(0% at ${at})`;
      stage.insertBefore(lav, stage.firstChild); stage.insertBefore(white, lav);
      void lav.offsetWidth;
      lav.style.transition = "clip-path 1s cubic-bezier(.65, 0, .35, 1)"; lav.style.clipPath = `circle(150% at ${at})`;
      setTimeout(() => { white.remove(); lav.remove(); }, 1300);
    }
  },''', "challenge enter")
    wr(p, s, nl)
print("ok approach")
