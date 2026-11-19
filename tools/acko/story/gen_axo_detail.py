# slides/s-axo-detail.html: the Detailed axonometric (18-19 Nov, Ritika's structure: "Detailed axonometric WITH DEFINED BOUNDARIES (the
# proposed layout slide would TRANSFORM into an axonometry where loop, neighborhoods, client and employee journeys would be defined)",
# then "build the detailed axo and let that seamlessly move to A day in ACKO").
# Made from Campus strategy as gen_story.py builds it into index-story2.html, so it is the same live floor (assets/js/axo-layers.js) with
# the same Loop, journeys and call-outs, but with the EXACT boundaries (no hand-drawn massing), in four beats:
#   1 The neighbourhoods  (strategy's beat 2: the six, numbered west to east, ACKO Home ... ACKO Auto, with the atriums, terraces, café)
#   2 The Loop            (beat 4: the floor in colour, the partitions rise, the arrows land, the Loop grows out of them)
#   (the client's and employees' journeys are not on this slide: Ritika, 19 Nov)
#   3 A day in ACKO        the camera glides (3.2 s) to the day's Arrival view, the Loop and the words fading; then a cut with no slide fade to
#                          A day in ACKO on the identical frame (window.ACKO_AXO_HAND, day: true; body.ax-hand)
# It is drawn on the furnished SketchUp model A day in ACKO uses (AxoSkp), the Layers volumes, Loop and routes over it (two passes: the
# model first, then the Layers scene with the depth cleared, its camera shifted by the plan offset).
# On leaving it keeps its last frame and camera (window.ACKO_AXO_HAND) for A day in ACKO, which glides from that view and dissolves the
# frame away (slides/s-wayday.html).
#   python tools/acko/story/gen_story.py .      (first: it builds index-story2.html)
#   python tools/acko/story/gen_axo_detail.py .
#   python tools/acko/story/gen_story3.py .
import sys, os, re
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")

H = open("index-story2.html", encoding="utf-8").read()
ID, NEW = "s-strategy", "s-axo-detail"

i = H.index('<section class="scene" id="%s"' % ID); j = H.index("</section>", i) + len("</section>")
sec = H[i:j]
a = H.index('<style data-slide="%s">' % ID); b = H.index("</style>", a)
css = H[a + len('<style data-slide="%s">' % ID):b]
a = H.index('<script data-slide="%s">' % ID); b = H.index("</script>", a)
js = H[a + len('<script data-slide="%s">' % ID):b]
# the generator's own rules for this slide, which sit outside its style block in index-story2.html
extra = "".join(m.group(1) + "\n" for m in re.finditer(r"<style>(#s-strategy \.st-(?:legs g\.arr|s\.cl)[^<]*)</style>", H))

def sub(s, old, new, n=1):
    assert s.count(old) == n, ("not found / not unique", old[:70], s.count(old))
    return s.replace(old, new)

# ---------- the section: its own words ----------
head = '<section class="scene" id="%s" data-part="cover" data-title="Detailed axonometric" data-steps="3" data-mins="2"\n' \
       '  data-beats="The Neighbourhoods,The Loop,A day in ACKO"\n' \
       '  data-notes="Detailed axonometric, with defined boundaries: the proposed layout transforms into an axonometry where the neighbourhoods and the Loop are defined. 1 The neighbourhoods, numbered west to east: 01 ACKO Home, 02 ACKO Drive, 03 ACKO Travel, 04 ACKO Health, 05 ACKO Life, 06 ACKO Auto, with the atriums, terraces and café. 2 The Loop: the floor in colour and the partitions rise, the two arrows land, and the Loop grows out of them through its seven stops. 3 A day in ACKO: the camera glides in, the Loop and the words fade away, and A day in ACKO takes over on the same frame. A click on the floor plays the beat again; drag turns it, scroll zooms, Reset view goes back. It is drawn on the furnished model of A day in ACKO and then glides into it.">' % NEW
sec = head + sec[sec.index("\n  <div class=\"page\">"):]
sec = sec.replace('<div class="page">', '<div class="page">\n    <div class="hdr"><b>Detailed axonometric</b><span>02 · Design Development</span></div>', 1)
sec = re.sub(r"<h3 style=\"--i:0\">.*?</h3>", '<h3 style="--i:0">Detailed Axonometric</h3>', sec, count=1, flags=re.S)
sec = re.sub(r"(<p style=\"--i:1\"><span>).*?(</span>)", r"\1With defined boundaries: the proposed layout becomes an axonometry where the neighbourhoods and the Loop are both defined.\2", sec, count=1, flags=re.S)
sec = sec.replace(ID, NEW)

# ---------- the style ----------
css = css.replace(ID, NEW) + extra.replace(ID, NEW)

# ---------- the script ----------
js = js.replace(ID, NEW)
js = sub(js, "M = Object.assign({}, S.base, S.base.sketch);", "M = S.base;")
js = sub(js, "      S.base.useSketch(true);", "")
for old, new in [('window.ACKO_MORPH.take("s-challenges", 2500)', "null"), ('window.ACKO_MORPH.take("s-loop-w")', "null")]:
    js = sub(js, old, new)
# the four beats are strategy's 2, 4, 5 and 6
js = re.sub(r"play\(k\);(\s*)// every beat plays", r"play(MAP[k]);\1// every beat plays", js, count=1)
assert "play(MAP[k])" in js
js = sub(js, "  const S = {", "  const MAP = [0, 2, 4];       // this slide's beats are the strategy's: the neighbourhoods, the Loop (the journeys are out, Ritika 19 Nov)\n  const S = {")
k = js.index("const NAMES = ["); k = js.index("];", k) + 2
js = js[:k] + '\n  NAMES[2] = "The Neighbourhoods"; NAMES[4] = "The Loop"; NAMES[6] = "The Employees’ journey";' + js[k:]
# defined boundaries: the floor goes to colour and the partitions rise on the Loop's beat, the neighbourhood masses lift away as they did
js = sub(js, "M.tint(k <= 3 ? 0 : k === 4 ? 0 : 1);", "M.tint(k <= 3 ? 0 : k === 4 ? win(t, 0.3, 1.0) : 1);")
js = sub(js, "grow(G.partitions, k <= 3 ? 0 : k === 4 ? 0 : 1);", "grow(G.partitions, k <= 3 ? 0 : k === 4 ? win(t, 1.0, 2.0) : 1);")
js = sub(js, "      if (k === 4) f = 1 - 0.7 * win(t, 0, 1.0);", "      if (k === 4) { const e = win(t, 0, 0.7); y = 10 * e; f = 1 - e; }")
js = sub(js, "      if (k === 4) f = 1 - 0.5 * win(t, 0, 1.0);\n", "      if (k === 4) f = 1 - win(t, 0, 0.6);\n")
# the furnished model underneath (the one A day in ACKO uses), the Layers scene over it
js = sub(js, "ACKO.slide(\"%s\", ({ $, $$, reduced, plain, reveal, cue, plan, later }) => {" % NEW, "ACKO.slide(\"%s\", ({ $, $$, reduced, plain, reveal, cue, plan, later, asset }) => {" % NEW)
js = sub(js, "  let T, M, cam, r, asp = 16 / 9, host, sc, view;", "  let T, M, cam, r, asp = 16 / 9, host, sc, view, SK = null, camS = null;")
js = sub(js, "view = S.base.data.view;", "view = { theta: -0.62, phi: 0.92 };      // A day in ACKO's angle, so the hand-over is a zoom and a pan (Ritika, 19 Nov)")
js = sub(js, "window.AxoModel.apply(cam, window.AxoLayers.frame(M, view, FIT_MARKS, asp), asp);", "window.AxoModel.apply(cam, window.AxoLayers.frame(M, M.data.view, FIT_MARKS, asp), asp);")
js = sub(js, "  const FIT = FIT14.map((v, i) => AT[i % 2] + SHRINK * (v - AT[i % 2])), FIT_MARKS", "  const FIT = [0.30, 0.07, 0.99, 0.71], FIT_MARKS")
js = sub(js, "M = S.base;", "M = S.base; SK = window.AxoSkp && window.AxoSkp.available() ? window.AxoSkp.get(asset) : null; camS = new T.OrthographicCamera(-1, 1, 1, -1, 1, 900);")
js = sub(js, "      if (!ok) return;\n", "      if (!ok) return;\n      if (SK) { window.AxoSkp.look(\"sketchup\"); SK.reset(); }\n")
js = sub(js, "v.position.y = y; M.fade(v, f);", "v.position.y = y; M.fade(v, f * (SK ? 0.55 : 1)); if (SK && v.userData.mats[2]) v.userData.mats[2][0].opacity = f;     // the mass at 55%, its number solid")
js = sub(js, "    r.render(M.scene, cam);\n    overlay();", "    paint();\n    overlay();")
js = sub(js, "window.AxoModel.apply(cam, S.state, asp); r.render(M.scene, cam);", "window.AxoModel.apply(cam, S.state, asp); paint();")
js = sub(js, "  function draw(now) {", """  // two passes: the furnished model (its own frame: the plan, the Layers floor is the plan + (185842, -182802) mm), then the Layers scene over
  // it with the depth cleared, so the neighbourhoods, the Loop and the journeys always show on the furniture. The Layers floor itself is hidden
  const OWN = ["base", "mass", "partitions", "rooms", "cafe", "terrace", "work", "plants", "facade"];
  function paint() {
    if (!SK) { r.render(M.scene, cam); return; }
    OWN.forEach((g) => { if (M.groups[g]) M.groups[g].visible = false; });
    const dx = (185842 + M.CX - SK.CX) / 1000, dz = (-182802 + M.CY - SK.CY) / 1000, st = S.state;
    window.AxoModel.apply(camS, { theta: st.theta, phi: st.phi, half: st.half, t: [st.t[0] + dx, st.t[1], st.t[2] + dz] }, asp); camS.updateMatrixWorld();
    const ac = r.autoClear; r.autoClear = false; r.clear(); r.render(SK.scene, camS); r.clearDepth(); r.render(M.scene, cam); r.autoClear = ac;
  }
  function draw(now) {""")

# the hand-over: its last frame and camera, for A day in ACKO to glide from
js = sub(js, "  return {\n    enter(_, s) {", """  // the hand-over to A day in ACKO: this frame (the model drawn once more, copied out) and the camera it was drawn from
  function handoff() {
    try { const c = snap(); if (c && S.state) window.ACKO_AXO_HAND = { st: Object.assign({}, S.state), snap: c, t: performance.now() }; } catch (e) { /* no hand-over: A day in ACKO just opens */ }
  }
  return {
    enter(_, s) {""")
js = sub(js, "    leave() { ", "    leave() { handoff(); S.day = false; ")

# the third beat: the camera glides to A day in ACKO's first view (its beatView(0), in this slide's frame), the ring and the words fading
js = js.replace("play(MAP[k]);", "if (k === 3) toDay(); else { clearDay(); play(MAP[k]); }", 1)
js = sub(js, "      S.fresh = true; S.k = 0;", "      S.fresh = true; S.k = 0; S.day = false; S.dayT = 0; sc.classList.remove(\"ax-day\"); if (S.rb) S.rb.fade(1);")
js = sub(js, "    if (S.tween) {\n      const tw = S.tween,", "    if (S.dayT && S.rb) S.rb.fade(Math.max(0, 1 - (now - S.dayT) / 1200));\n    if (S.tween) {\n      const tw = S.tween,")
js = sub(js, "  // the hand-over to A day in ACKO: this frame", """  // A day in ACKO's first camera (s-wayday: Arrival at plan (85500, 31500) mm, half 14, its offset), in this slide's frame
  function dayView() {
    const v = { theta: -0.62, phi: 0.92 }, h = 14, { right, up } = window.AxoModel.basis(v);
    const off = right.clone().multiplyScalar(-h * asp * 0.18).add(up.clone().multiplyScalar(h * 0.05));
    const dx = (185842 + M.CX - SK.CX) / 1000, dz = (-182802 + M.CY - SK.CY) / 1000;
    return { theta: v.theta, phi: v.phi, half: h, t: [SK.X(85500) + off.x - dx, 0.8 + off.y, SK.Z(31500) + off.z - dz] };
  }
  function toDay() {
    if (!SK) return;
    S.day = true; S.dayT = performance.now(); S.playing = false; S.moved = true; sc.classList.add("ax-day");
    S.tween = { from: Object.assign({}, S.state), to: dayView(), t0: S.dayT, ms: 3200 }; need();
  }
  function clearDay() {                                  // back from the day to the Loop: the ring and the words return, the camera goes home
    if (!S.day) return;
    S.day = false; S.dayT = 0; sc.classList.remove("ax-day"); if (S.rb) S.rb.fade(1); home();
  }
  // the hand-over to A day in ACKO: this frame""")
js = sub(js, "    try { const c = snap(); if (c && S.state) window.ACKO_AXO_HAND = { st: Object.assign({}, S.state), snap: c, t: performance.now() }; } catch (e) { /* no hand-over: A day in ACKO just opens */ }",
  "    try {\n      if (!S.state) return;\n      window.ACKO_AXO_HAND = { st: Object.assign({}, S.state), snap: S.day ? null : snap(), day: !!S.day, t: performance.now() };\n      if (S.day) { document.body.classList.add(\"ax-hand\"); setTimeout(() => document.body.classList.remove(\"ax-hand\"), 2600); }   // a cut, not a fade, into the day\n    } catch (e) { /* no hand-over: A day in ACKO just opens */ }")
css += """/* the third beat: the words and the ring fade as the camera glides in; then A day in ACKO takes over with no slide fade */
#%s.ax-day .st-t, #%s.ax-day .st-cap, #%s.ax-day .st-ov, #%s.ax-day .st-tools, #%s.ax-day .hdr { opacity: 0 !important; transition: opacity 1.2s ease !important; }
body.ax-hand .scene { transition: none !important; }
""" % ((NEW,) * 5)


# ---------- the file ----------
top = open("slides/s-axo-detail.html", encoding="utf-8").read().split("<!-- slide:start -->")[0]
out = top + "<!-- slide:start -->\n" + sec + "\n<style>\n" + css + "</style>\n<script>" + js + "</script>\n<!-- slide:end -->\n</body>\n</html>\n"
open("slides/s-axo-detail.html", "w", encoding="utf-8", newline="\n").write(out)
print("ok slides/s-axo-detail.html", len(out))
