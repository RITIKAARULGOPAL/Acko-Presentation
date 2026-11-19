# slides/s-axo-detail.html: the Detailed axonometric (18-19 Nov, Ritika's structure: "Detailed axonometric WITH DEFINED BOUNDARIES (the
# proposed layout slide would TRANSFORM into an axonometry where loop, neighborhoods, client and employee journeys would be defined)",
# then "build the detailed axo and let that seamlessly move to A day in ACKO").
# Made from Campus strategy as gen_story.py builds it into index-story2.html, so it is the same live floor (assets/js/axo-layers.js) with
# the same Loop, journeys and call-outs, but with the EXACT boundaries (no hand-drawn massing), in four beats:
#   1 The neighbourhoods  (strategy's beat 2: the six, numbered west to east, ACKO Home ... ACKO Auto, with the atriums, terraces, café)
#   2 The Loop            (beat 4: the floor in colour, the partitions rise, the arrows land, the Loop grows out of them)
#   3 The client's journey, 4 The employees' journey   (beats 5 and 6)
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
head = '<section class="scene" id="%s" data-part="cover" data-title="Detailed axonometric" data-steps="4" data-mins="2.5"\n' \
       '  data-beats="The Neighbourhoods,The Loop,The Client’s journey,The Employees’ journey"\n' \
       '  data-notes="Detailed axonometric, with defined boundaries: the proposed layout transforms into an axonometry where the neighbourhoods, the Loop, and the client’s and employees’ journeys are defined. 1 The neighbourhoods, numbered west to east: 01 ACKO Home, 02 ACKO Drive, 03 ACKO Travel, 04 ACKO Health, 05 ACKO Life, 06 ACKO Auto, with the atriums, terraces and café. 2 The Loop: the floor in colour and the partitions rise, the two arrows land, and the Loop grows out of them through its seven stops. 3 The client’s journey from the entrances, its touchpoints called out. 4 The employees’ journey through the Loop’s seven stops, the furniture in. A click on the floor plays the beat again; drag turns it, scroll zooms, Reset view goes back. It then glides into A day in ACKO.">' % NEW
sec = head + sec[sec.index("\n  <div class=\"page\">"):]
sec = sec.replace('<div class="page">', '<div class="page">\n    <div class="hdr"><b>Detailed axonometric</b><span>02 · Design Development</span></div>', 1)
sec = re.sub(r"<h3 style=\"--i:0\">.*?</h3>", '<h3 style="--i:0">Detailed Axonometric</h3>', sec, count=1, flags=re.S)
sec = re.sub(r"(<p style=\"--i:1\"><span>).*?(</span>)", r"\1With defined boundaries: the proposed layout becomes an axonometry where the neighbourhoods, the Loop, and the client and employee journeys are all defined.\2", sec, count=1, flags=re.S)
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
js = sub(js, "  const S = {", "  const MAP = [0, 2, 4, 5, 6];       // this slide's beats are the strategy's: the neighbourhoods, the Loop, the client's and the employees' journeys\n  const S = {")
k = js.index("const NAMES = ["); k = js.index("];", k) + 2
js = js[:k] + '\n  NAMES[2] = "The Neighbourhoods"; NAMES[4] = "The Loop"; NAMES[6] = "The Employees’ journey";' + js[k:]
# defined boundaries: the floor goes to colour and the partitions rise on the Loop's beat, the neighbourhood masses lift away as they did
js = sub(js, "M.tint(k <= 3 ? 0 : k === 4 ? 0 : 1);", "M.tint(k <= 3 ? 0 : k === 4 ? win(t, 0.3, 1.0) : 1);")
js = sub(js, "grow(G.partitions, k <= 3 ? 0 : k === 4 ? 0 : 1);", "grow(G.partitions, k <= 3 ? 0 : k === 4 ? win(t, 1.0, 2.0) : 1);")
js = sub(js, "      if (k === 4) f = 1 - 0.7 * win(t, 0, 1.0);", "      if (k === 4) { const e = win(t, 0, 0.7); y = 10 * e; f = 1 - e; }")
js = sub(js, "      if (k === 4) f = 1 - 0.5 * win(t, 0, 1.0);\n", "      if (k === 4) f = 1 - win(t, 0, 0.6);\n")
# the hand-over: its last frame and camera, for A day in ACKO to glide from
js = sub(js, "  return {\n    enter(_, s) {", """  // the hand-over to A day in ACKO: this frame (the model drawn once more, copied out) and the camera it was drawn from
  function handoff() {
    try { const c = snap(); if (c && S.state) window.ACKO_AXO_HAND = { st: Object.assign({}, S.state), snap: c, t: performance.now() }; } catch (e) { /* no hand-over: A day in ACKO just opens */ }
  }
  return {
    enter(_, s) {""")
js = sub(js, "    leave() { ", "    leave() { handoff(); ")

# ---------- the file ----------
top = open("slides/s-axo-detail.html", encoding="utf-8").read().split("<!-- slide:start -->")[0]
out = top + "<!-- slide:start -->\n" + sec + "\n<style>\n" + css + "</style>\n<script>" + js + "</script>\n<!-- slide:end -->\n</body>\n</html>\n"
open("slides/s-axo-detail.html", "w", encoding="utf-8", newline="\n").write(out)
print("ok slides/s-axo-detail.html", len(out))
