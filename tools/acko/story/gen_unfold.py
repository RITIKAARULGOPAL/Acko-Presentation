# index-unfold.html: ACKO's logo unfolding like a ribbon into the white Möbius strip, four ways (11 Nov, Ritika: "it's still not seamless.
# ACKO logo can unfold like a ribbon. Also give me multiple options"). In each, the strip that appears IS the deck's photo, revealed along
# the strip's own path (Ritika's line, the slide's .o2-l f1 · bk · f2, photo px) through an SVG mask: a wide, soft stroke drawn along
# that line, so there is never a second picture to cross-fade. The logo sits where the ribbon starts (the twist, top right: its pointed
# tip is its own twist) and becomes the ribbon's head. At the end the masked photo is the slide's photo, which takes over. Beats 2–5
# are s-open's.
#   python tools/acko/story/gen_unfold.py .     writes slides/s-unf-1..4.html (not in order.txt) and index-unfold.html
import sys, os, re, json
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

OPTS = [
    (1, "Peel round", {"mode": "peel", "logo": "twist", "go": 2600}),
    (2, "Both ways", {"mode": "both", "logo": "twist", "go": 2000}),
    (3, "Lavender lead", {"mode": "lead", "logo": "twist", "go": 3000}),
    (4, "Untwist from the centre", {"mode": "peel", "logo": "centre", "go": 2600}),
    (5, "Ribbon logo", {"mode": "ribbon", "logo": "twist", "go": 3000}),   # Ritika's pick (11 Nov): "make the ACKO logo itself in ribbon form and let the ribbon unfold to become the white Möbius strip"
    # more of the ribbon logo (11 Nov, Ritika: "give more variations"), all on tools/acko/story/ribbon_unfold.js
    (6, "Centre stage", {"mode": "ribbon", "logo": "twist", "place": "centre", "go": 3400}),
    (7, "Purple Möbius first", {"mode": "ribbon", "logo": "twist", "tint": "purple", "go": 2800}),
    (8, "Split unwind", {"mode": "ribbon", "logo": "twist", "heads": 2, "go": 2400}),
    (9, "Close-up pull-back", {"mode": "ribbon", "logo": "twist", "cam": 2.6, "go": 3400}),
    (10, "Ribbon to line", {"mode": "ribbon", "logo": "twist", "trail": True, "go": 3000}),
]
PICK = 5            # the deck's opening (slides/s-open.html, and s-open-2.html for index-open.html) is this option
MARK = ('<path class="mk-c" fill="#b098f2" d="M12 34C30 33 44 35 52 38C48.5 55 48.5 74 52 89C40 92 24 93.5 12 92.5C-3 78 -3 50 12 34Z"/>'
        '<path class="mk-a" fill="#9068f0" d="M14 32C40 29 78 38 124 62L166 43.5C168.5 42 168.5 39.5 165.5 37.5C140 21 108 1 80 0C62 0 36 14 14 32Z"/>'
        '<path class="mk-b" fill="#4828ba" d="M169 44.5L104 74C70 89 36 97 13.5 95C32 109 55 127 76 127C104 126 148 102 167 88C169 86 169 85 169 84Z"/>')

JS = r'''  // the unfold (11 Nov): option __N__ · __NAME__. The white strip is the photo itself, shown through a mask along the strip's own
  // path (f1 · bk · f2, from the twist), so it is laid down like a ribbon; the logo sits at the start and becomes the ribbon's head
  const OPT = __OPT__;
  const MS = { raf: 0 };
  const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const sm = (a, b, u) => { const x = Math.min(1, Math.max(0, (u - a) / (b - a))); return x * x * (3 - 2 * x); };
  const TW = [1330, 300], CEN = [768, 512], S_TW = 1.46, S_CEN = 3.14;      // photo px: the twist, the page's middle; the logo's sizes
  const IN = 800, HOLD = 300, PRE = OPT.logo === "centre" ? 1300 : 0, T = IN + HOLD + PRE + OPT.go;
  let LOOP = null;
  function loopPts(sc) {                              // the strip's line, every 3 px, starting at the point nearest the twist
    if (LOOP) return LOOP;
    const pts = []; $$(".o2-l", sc).forEach((p) => { const L = p.getTotalLength(); for (let s = 0; s < L; s += 3) { const q = p.getPointAtLength(s); pts.push([q.x, q.y]); } });
    let i0 = 0, b = Infinity; pts.forEach((q, i) => { const d = (q[0] - TW[0]) ** 2 + (q[1] - TW[1]) ** 2; if (d < b) { b = d; i0 = i; } });
    return (LOOP = pts.slice(i0).concat(pts.slice(0, i0)));
  }
  const dOf = (P) => "M" + P.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1)).join("L");
  let ready = false;
  function setup(sc) {
    if (ready) return; ready = true;
    const P = loopPts(sc), half = Math.floor(P.length / 2), R = $$(".uf-r", sc);
    if (OPT.mode === "both") { R[0].setAttribute("d", dOf(P.slice(0, half + 1))); R[1].setAttribute("d", dOf([P[0]].concat(P.slice(half).reverse()))); }
    else { R[0].setAttribute("d", dOf(P.concat([P[0]]))); R[1].setAttribute("d", "M0 0"); }
    $(".uf-lead", sc).setAttribute("d", dOf(P.concat([P[0]])));
    R.forEach((r) => { const L = r.getTotalLength(); r.style.strokeDasharray = L + " " + (L + 10); });
  }
  function frame(sc, ms) {                            // the whole of beat 1 at time ms
    const lg = $(".uf-logo", sc); let x = TW[0], y = TW[1], s = S_TW, sx = 1, op = 1, dy = 0;
    if (OPT.logo === "centre") { x = CEN[0]; y = CEN[1]; s = S_CEN; }
    if (ms < IN) { op = sm(0, 1, ms / IN); dy = (1 - ease(Math.max(0, ms) / IN)) * 18; }
    const m2 = ms - IN - HOLD;
    if (OPT.logo === "centre" && m2 > 0) {            // it turns edge-on (a line), then drops to the twist
      const a = Math.min(1, m2 / 600), q = sm(0, 1, (m2 - 600) / 700);
      sx = 1 - 0.95 * ease(a); x = CEN[0] + (TW[0] - CEN[0]) * q; y = CEN[1] + (TW[1] - CEN[1]) * q; s = S_CEN + (S_TW - S_CEN) * q;
    }
    const u = ease(Math.min(1, Math.max(0, (m2 - PRE) / OPT.go))), gone = sm(0, 0.25, u);
    const k = s * (1 - 0.7 * gone);
    lg.setAttribute("transform", `translate(${x.toFixed(1)} ${(y + dy).toFixed(1)}) scale(${(k * sx).toFixed(3)} ${k.toFixed(3)}) translate(-84.5 -63.5)`);
    lg.style.opacity = (op * (1 - gone)).toFixed(3);
    if (OPT.mode === "both") { const sp = 70 * sm(0, 0.3, u);   // the two bands part, one each way round
      $(".uf-logo .mk-a", sc).setAttribute("transform", `translate(${(-sp).toFixed(1)} ${(-0.3 * sp).toFixed(1)})`);
      $(".uf-logo .mk-b", sc).setAttribute("transform", `translate(${(0.3 * sp).toFixed(1)} ${sp.toFixed(1)})`); }
    const R = $$(".uf-r", sc), ld = $(".uf-lead", sc);
    if (OPT.mode === "lead") {                        // the lavender runs ahead; the white unrolls behind it
      const L = R[0].getTotalLength(), G = 520, SEG = 420, head = u * (L + G), rv = Math.max(0, head - G);
      R[0].style.strokeDashoffset = (L - rv).toFixed(1);
      ld.style.strokeDasharray = `${SEG} ${L * 3}`; ld.style.strokeDashoffset = (-(head - SEG)).toFixed(1);
      ld.style.opacity = m2 > PRE ? (1 - sm(0.82, 1, u)).toFixed(3) : 0;
    } else R.forEach((r) => { const L = r.getTotalLength(); r.style.strokeDashoffset = (L * (1 - u)).toFixed(1); });
  }
  function start(sc) {                                // the photo hidden, the masked one on, the logo at its start
    setup(sc); const img = $(".o2-art img", sc), sv = $(".uf-svg", sc);
    img.style.transition = "none"; img.style.opacity = 0; sv.style.opacity = 1; frame(sc, 0);
  }
  function finish(sc, now) {                          // the slide's own photo takes over from the identical masked one
    const img = $(".o2-art img", sc), sv = $(".uf-svg", sc);
    img.style.transition = now ? "none" : "opacity .45s"; img.style.opacity = "";
    if (now) sv.style.opacity = 0; else later(() => (sv.style.opacity = 0), 500);
  }
  function play(sc) {
    start(sc); const t0 = performance.now();
    const tick = (now) => { const ms = now - t0; frame(sc, ms); if (ms < T) MS.raf = requestAnimationFrame(tick); else finish(sc); };
    MS.raf = requestAnimationFrame(tick);
  }
  (window.__unfold = window.__unfold || {})["__ID__"] = (t) => { const sc = document.getElementById("__ID__"); cancelAnimationFrame(MS.raf); start(sc); frame(sc, t * T); };   // to check a frame
'''

RJS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ribbon_unfold.js"), encoding="utf-8").read()   # option 5's code

src = open("tools/acko/story/open_base.html", encoding="utf-8").read()   # the opening as it was (11 Nov), the template for every option
a = src.index("  // the morph: each band's points"); b = src.index("\n", src.index("window.__morph")) + 1
assert a < b
LOGO_SVG = '      <svg class="o2-logo-svg" viewBox="0 0 1920 1080" aria-hidden="true"><path class="mk-c"/><path class="mk-a"/><path class="mk-b"/></svg>\n'
assert LOGO_SVG in src
STEP = "      if (k === 1 && !reduced) play(sc); else morph(sc, 1, true);"
assert STEP in src
IMG = '        <img src="assets/img/mobius.webp" alt="">\n'
assert IMG in src

for n, name, opt in OPTS:
    sid = "s-unf-%d" % n
    t = src[:a] + (RJS if opt["mode"] == "ribbon" else JS).replace("__N__", str(n)).replace("__NAME__", name).replace("__OPT__", json.dumps(opt)).replace("__ID__", sid) + src[b:]
    t = t.replace(LOGO_SVG, "")
    t = t.replace(STEP, "      if (k === 1 && !reduced) play(sc); else { setup(sc); finish(sc, true); }")
    mask = ('        <svg class="uf-svg" viewBox="0 0 1536 1024" aria-hidden="true"><defs>'
            '<filter id="uf-b-ID" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="18"/></filter>'
            '<mask id="uf-m-ID" maskUnits="userSpaceOnUse" x="-300" y="-300" width="2136" height="1624"><g filter="url(#uf-b-ID)"><path class="uf-r"/><path class="uf-r"/></g></mask></defs>'
            '<image href="assets/img/mobius.webp" x="0" y="0" width="1536" height="1024" mask="url(#uf-m-ID)" opacity=".9"/>'
            '<path class="uf-lead"/><g class="uf-logo">' + MARK + '</g></svg>\n').replace("ID", sid)
    if opt["mode"] == "ribbon": mask += '        <canvas class="uf-cv"></canvas><canvas class="uf-cv"></canvas>\n'   # the ribbon on the strip · the mark
    t = t.replace(IMG, IMG + mask)
    css = ('#s-open .o2-art svg.uf-svg { opacity: 0; overflow: visible; transition: none; }\n'
           '#s-open .uf-r { fill: none; stroke: #fff; stroke-width: 430; stroke-linecap: butt; stroke-linejoin: round; }\n'
           '#s-open .o2-art canvas.uf-cv { position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; opacity: 0; }\n'
           '#s-open .uf-lead { fill: none; stroke: #c9b3f3; stroke-width: 46; stroke-linecap: round; stroke-linejoin: round; opacity: 0; filter: drop-shadow(0 0 10px rgba(201,179,243,.85)); }\n')
    t = t.replace("#s-open .o2-logo-svg { position", css + "#s-open .o2-logo-svg { position")
    # beat 1's words come once the strip is laid
    base = (800 + (500 if opt.get("cam") else 300) + (1300 if opt["logo"] == "centre" else 0) + opt["go"] + (1600 if opt.get("tint") == "purple" else 0)) / 1000 - 0.2
    for i, d in enumerate(("3s", "3.3s", "3.65s", "4s")):
        t = t.replace(':nth-child(%d) { transition-delay: %s; }' % (i + 1, d), ':nth-child(%d) { transition-delay: %.2fs; }' % (i + 1, base + (0, .3, .65, 1)[i]))
    t = t.replace("s-open", sid).replace("<title>The opening · ACKO slide " + sid, "<title>Unfold · %d · %s · ACKO slide %s" % (n, name, sid))
    t = t.replace("assets/img/" + sid, "assets/img/s-open")   # (no asset folder of its own)
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(t)
    print("ok", sid)
    if n == PICK:                                    # the deck's opening, and option 2 of index-open.html, are this one
        for own, title in (("s-open", "The opening"), ("s-open-2", "Opening · 2 · Into the strip")):
            o = t.replace(sid, own).replace("<title>Unfold · %d · %s · ACKO slide %s" % (n, name, own), "<title>%s · ACKO slide %s" % (title, own))
            open("slides/%s.html" % own, "w", encoding="utf-8", newline="\n").write(o); print("ok", own, "=", sid)

# the comparison page: today's morph (0), the four unfolds, then the Möbius
ORDER = ["s-unf-%d" % n for n, _, _ in OPTS] + ["s-mobius"]
LAB = {}; LAB.update({"s-unf-%d" % n: "Unfold · %d · %s" % (n, name) for n, name, _ in OPTS})
OUT = "index-unfold.html"
build.build(ORDER, OUT)
h = open(OUT, encoding="utf-8").read()
for sid, label in LAB.items():
    i = h.index('id="%s"' % sid); k = h.index('<div class="page">', i) + len('<div class="page">')
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
       'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ORDER))
