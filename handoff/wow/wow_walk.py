# E · walk the Loop: slides/s-walk.html (new, the re-ordered deck only), plus the strategy's last-frame snapshot (_snap)
# run: python wow_walk.py <deck-wow checkout>   (s-walk written afresh each run; the s-strategy patch once)
import os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from eol import rd, wr
os.chdir(sys.argv[1])
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

# ---- what the walk borrows from A day in ACKO: the people (data and code), the ring test
wd, _ = rd("slides/s-wayday.html")
people_data = re.search(r"\n  const PEOPLE = (\{.*?\});\n", wd).group(0).strip("\n")
inring = re.search(r"\n  const inRing = [^\n]*\n", wd).group(0).strip("\n")
a = wd.index("  // the people: one low-poly figure per pose"); b = wd.index("\n  function build() {")
people_code = wd[a:b].rstrip() + "\n"
body = open(os.path.join(here, "walk_body.js"), encoding="utf-8").read()
body = body.replace("  /*@PEOPLE@*/", people_data).replace("  /*@INRING@*/", inring).replace("  /*@PEOPLECODE@*/\n", people_code)
assert "/*@" not in body

head, _ = rd("slides/s-thanks.html")
pre = head[: head.index("<!-- slide:start -->")].replace("Thank you · ACKO slide s-thanks", "Walk the Loop · ACKO slide s-walk")
html = pre + '''<!-- slide:start -->
<section class="scene" id="s-walk" data-part="6" data-title="Walk the Loop" data-steps="8" data-mins="1.5" data-beats="Into the floor,Café,Board Room,Meeting Rooms,Collab,Work,Wellness,Back to the plan"
  data-notes="Walk the Loop: from the strategy's axo the camera sinks to eye level and walks the Loop on the furnished model, a click a stop: Arrival (I feel welcomed), Café (Hey, we finally meet!), Board Room (This is my big moment), Meeting Rooms (My impact), Collab (Wow, worth the commute), Work (These are my folks!), Wellness (They thought of me too!). On the long legs it lifts and flies low over the floor. The last click rises straight up over the plan, and the next slide's Spaces plan takes over from it.">
  <div class="page">
    <div class="wl-3d" style="left:0;top:0;width:100%;height:100%"></div>
    <div class="wl-head rv" style="left:3.4%;top:6.5%;width:60%"><small style="--i:0">Walk the Loop</small><h2 style="--i:1">One path, <b>seven moments.</b></h2></div>
    <div class="wl-card" style="left:3.4%;top:70%;width:34%"><i class="wl-n"></i><b class="wl-name"></b><q class="wl-q"></q></div>
    <div class="wl-dots" style="left:3.4%;top:89.5%;width:30%"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
    <p class="wl-end hand" style="left:3.4%;top:78%;width:60%">…and back to the plan it all sits on.</p>
    <p class="wl-fb" style="left:3.4%;top:40%;width:60%">The walk needs the furnished model (WebGL); the stops: Arrival, Café, Board Room, Meeting Rooms, Collab, Work, Wellness.</p>
  </div>
</section>
<style>
/* ---------- walk the Loop (9 Nov, the re-ordered deck) ---------- */
#s-walk .wl-3d { pointer-events: none; }
#s-walk .wl-3d canvas { display: block; width: 100%; height: 100%; }
#s-walk .wl-head small { display: block; font-size: calc(var(--pt) * 8.5); font-weight: 600; letter-spacing: .16em; text-transform: uppercase; color: var(--purple-2); text-shadow: 0 0 calc(var(--pt) * 6) #fff, 0 0 calc(var(--pt) * 3) #fff; }
#s-walk .wl-head h2 { margin: calc(var(--pt) * 3) 0 0; font-size: calc(var(--pt) * 24); font-weight: 400; color: #111; text-shadow: 0 0 calc(var(--pt) * 8) #fff, 0 0 calc(var(--pt) * 4) #fff; }
#s-walk .wl-head h2 b { font-weight: 700; color: var(--purple-2); }
#s-walk .wl-card { display: flex; flex-direction: column; gap: calc(var(--pt) * 2); padding: calc(var(--pt) * 8) calc(var(--pt) * 11); border-radius: calc(var(--pt) * 7); background: rgba(255,255,255,.86); box-shadow: 0 calc(var(--pt) * 3) calc(var(--pt) * 14) rgba(40,20,90,.14); backdrop-filter: blur(6px);
  opacity: 0; transform: translateY(calc(var(--pt) * 5)); transition: opacity .5s var(--ease), transform .5s var(--ease); box-sizing: border-box; }
#s-walk .wl-card.on { opacity: 1; transform: none; }
#s-walk .wl-n { font-style: normal; font-family: var(--num, inherit); font-size: calc(var(--pt) * 7); letter-spacing: .12em; color: #888; }
#s-walk .wl-name { font-size: calc(var(--pt) * 20); font-weight: 700; color: var(--purple-2); }
#s-walk .wl-q { quotes: none; font-size: calc(var(--pt) * 11); font-style: italic; font-weight: 600; color: var(--plum, #5a3d73); }
#s-walk .wl-q::before { content: "\\201C"; } #s-walk .wl-q::after { content: "\\201D"; }
#s-walk .wl-dots { display: flex; gap: calc(var(--pt) * 4); align-items: center; }
#s-walk .wl-dots i { width: calc(var(--pt) * 5); height: calc(var(--pt) * 5); border-radius: 50%; border: 1.5px solid var(--purple-2); background: rgba(255,255,255,.8); transition: background .4s, transform .4s; }
#s-walk .wl-dots i.on { background: var(--purple-2); }
#s-walk .wl-dots i.now { transform: scale(1.35); }
#s-walk .wl-end { margin: 0; font-size: calc(var(--pt) * 18); color: var(--purple-2); opacity: 0; transition: opacity .8s var(--ease) .4s; text-shadow: 0 0 calc(var(--pt) * 5) #fff; }
#s-walk .wl-end.on { opacity: 1; }
#s-walk .wl-fb { display: none; margin: 0; font-size: calc(var(--pt) * 12); color: #555; }
#s-walk.wl-fallback .wl-fb { display: block; }
#s-walk.wl-fallback .wl-card { opacity: 1; transform: none; }
</style>
<script>
''' + body + '''</script>
<!-- slide:end -->
</body>
</html>
'''
wr("slides/s-walk.html", html, "\r\n")

# ---- the strategy: its last frame on demand, for the walk to open on
p = "slides/s-strategy.html"; s, nl = rd(p)
if "_snap" not in s:
    s = sub1(s, "  function flatten(vb, ms, done) {\n", '''  // the walk (s-walk, 9 Nov), opening on this view: the model drawn once more as it was and copied out, in the same task (the
  // drawing buffer is only readable until it is shown)
  function snap() {
    if (!M || !r || !cam) return null;
    window.AxoModel.apply(cam, S.state, asp); r.render(M.scene, cam);
    const c = document.createElement("canvas"); c.width = r.domElement.width; c.height = r.domElement.height; c.getContext("2d").drawImage(r.domElement, 0, 0);
    return c;
  }
  function flatten(vb, ms, done) {
''', "snap")
    s = sub1(s, "sc = s; sc._flatten = flatten;", "sc = s; sc._flatten = flatten; sc._snap = snap;", "snap expose")
    wr(p, s, nl)
print("ok walk")
