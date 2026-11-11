# The floor as one continuous drawing through the re-ordered deck's building chapter (Ritika, 9 Nov):
#   Layout · Due Diligence (s-layout-dd) → football pitches: the bare floor starts where the plan's plate lay and glides to the touchline
#   pitches → vast-floor axo (s-challenges): the floor tilts from plan into the axo, then the picture takes over
#   Employees Journey (s-strategy) → Layout · Spaces (s-layout-sp): the axo flattens back into the plan
# Writes slides/s-layout-dd.html and slides/s-layout-sp.html (copies of s-layout, which the live deck keeps), and adds the hand-offs
# to s-pitch and s-challenges (they only play when the slide before is the one named, so the live deck reads as before).
# run: python gen_floorflow.py <plan-content checkout>   (idempotent: re-run safe)
import os, re, sys
os.chdir(sys.argv[1])
NL = "\r\n"                                   # the slide files are CRLF; edited as LF, written back CRLF
rd = lambda p: open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
def wr(p, s): open(p, "w", encoding="utf-8", newline="").write(s.replace("\r\n", "\n").replace("\n", NL))
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

# ------------------------------------------------------------------ the shared helper (in s-challenges' script)
# the plate's plan (metres, ACKO_FLOOR) → the challenges axo on the page: the desks' own frame (A, U, V over the plate's box), then
# the axo's 95% about page (1606.08, 10.8)
X0, X1, Y0, Y1 = 0.47, 245.53, 1.79, 36.03
A, U, V = (39, 1029), (1359, -1014), (206, 130)
a, b = U[0] / (X1 - X0), U[1] / (X1 - X0)
c, d = V[0] / (Y1 - Y0), V[1] / (Y1 - Y0)
e, f = A[0] - a * X0 - c * Y0, A[1] - b * X0 - d * Y0
O = (1606.08, 10.8)
AXO = [.95 * a, .95 * b, .95 * c, .95 * d, .95 * e + .05 * O[0], .95 * f + .05 * O[1]]
HOME = [48, 284, 1872, 542]          # the plan's plate on the Layout's home view (page px; s-site's intoView lands it there)

HELPER = '''
/* the floor carried from slide to slide (9 Nov, the re-ordered deck): a slide's leave() marks where the bare floor lay (page px, a
   2D matrix from ACKO_FLOOR's metres), the next slide's enter() takes it if it's the one it follows, and draws the floor from there */
window.ACKO_MORPH = window.ACKO_MORPH || (() => {
  const M = {
    from: null,
    AXO: %s,                                    // plan (m) → the challenges axo on the page
    HOME: %s,                                   // the Layout's plate on the page (px)
    BOX: [%s, %s, %s, %s],                      // the plate's box (m)
    mark(id, data) { M.from = Object.assign({ id, t: performance.now() }, data || {}); },
    take(id, ms) { const f = M.from; if (!f || f.id !== id || performance.now() - f.t > (ms || 1500)) return null; M.from = null; return f; },
    mul: (P, Q) => [P[0] * Q[0] + P[2] * Q[1], P[1] * Q[0] + P[3] * Q[1], P[0] * Q[2] + P[2] * Q[3], P[1] * Q[2] + P[3] * Q[3], P[0] * Q[4] + P[2] * Q[5] + P[4], P[1] * Q[4] + P[3] * Q[5] + P[5]],
    inv(P) { const D = P[0] * P[3] - P[1] * P[2]; return [P[3] / D, -P[1] / D, -P[2] / D, P[0] / D, (P[2] * P[5] - P[3] * P[4]) / D, (P[1] * P[4] - P[0] * P[5]) / D]; },
    rect(r) { const [x0, y0, x1, y1] = M.BOX, sx = (r[2] - r[0]) / (x1 - x0), sy = (r[3] - r[1]) / (y1 - y0); return [sx, 0, 0, sy, r[0] - sx * x0, r[1] - sy * y0]; },
    // an element's user space → page px (the page frame is 1920 wide on every slide)
    page(el, pg) { const m = el.getScreenCTM(), r = pg.getBoundingClientRect(), s = r.width / 1920; return [m.a / s, m.b / s, m.c / s, m.d / s, (m.e - r.left) / s, (m.f - r.top) / s]; },
    // the bare floor, in metres, into a <g>
    draw(g) {
      if (g.childElementCount) return;
      const F = window.ACKO_FLOOR; if (!F) return;
      const k = F.unit, P = (pts) => pts.map(([x, y]) => `${(x * k).toFixed(2)} ${(y * k).toFixed(2)}`).join("L"), ns = 'vector-effect="non-scaling-stroke"';
      g.innerHTML = (F.terraces || []).map((t) => `<path d="M${P(t)}Z" fill="#e3efd9" stroke="#8a83a3" stroke-width="1" ${ns}/>`).join("") +
        `<path d="M${P(F.plate)}Z" fill="#f4f0ff" stroke="#5222d0" stroke-width="2.4" stroke-linejoin="round" ${ns}/>` +
        (F.cores || []).map((q) => `<path d="M${P(q)}Z" fill="#dcd7e8" stroke="#8a83a3" stroke-width="1" ${ns}/>`).join("");
    },
    // a <g>'s matrix from P to Q over ms (eased); the end state is set by a timer too, so it lands even without frames
    anim(g, P, Q, ms, done, wait) {
      const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2), set = (u) => g.setAttribute("transform", `matrix(${P.map((v, i) => (v + (Q[i] - v) * ease(u)).toFixed(4)).join(" ")})`);
      let end = false, t0 = 0; set(0);
      const fin = () => { if (end) return; end = true; set(1); if (done) done(); };
      const tick = (now) => { if (end) return; const u = Math.min(1, (now - t0) / ms); set(u); if (u < 1) requestAnimationFrame(tick); else fin(); };
      setTimeout(() => { t0 = performance.now(); requestAnimationFrame(tick); setTimeout(fin, ms + 150); }, wait == null ? 450 : wait);   // after the slides' cross-fade has begun
    },
  };
  return M;
})();
''' % ("[" + ", ".join("%.5f" % v for v in AXO) + "]", str(HOME), X0, Y0, X1, Y1)

# ------------------------------------------------------------------ s-challenges: arriving from the pitches, the floor tilts into the axo
p = "slides/s-challenges.html"; s = rd(p)
if "ACKO_MORPH" not in s:
    s = sub1(s, '<div class="cl-axo"', '<svg class="cl-morph" viewBox="0 0 1920 1080" preserveAspectRatio="none" aria-hidden="true" style="left:0;top:0;width:100%;height:100%"><g></g></svg>\n    <div class="cl-axo"', "morph svg")
    s = sub1(s, "</style>", '''/* arriving from the football pitches (9 Nov, the re-ordered deck): the bare floor tilts from plan into this axo, then the picture,
   the header and the headline come in over it and the drawing goes */
#s-challenges .cl-morph { pointer-events: none; opacity: 0; transition: opacity .6s var(--ease); }
#s-challenges .page.cl-arrive .cl-morph, #s-challenges .page.cl-land .cl-morph { opacity: 1; transition: none; }
#s-challenges .page.cl-land .cl-morph { opacity: 0; transition: opacity .7s var(--ease) .25s; }
#s-challenges .cl-axo, #s-challenges .cl-svg, #s-challenges .cl-h, #s-challenges .hdr { transition: opacity .7s var(--ease); }
#s-challenges .page.cl-arrive :is(.cl-axo, .cl-svg, .cl-h, .hdr, [data-step]) { opacity: 0 !important; transition: none !important; }
</style>''', "style")
    s = sub1(s, '<script>\n/* what\'s our challenge', '<script>\n' + HELPER.strip("\n") + '\n/* what\'s our challenge', "helper") if '<script>\n/* what' in s else sub1(s, "<script>\r\n/* what's our challenge", "<script>\r\n" + HELPER.strip("\n") + "\r\n/* what's our challenge", "helper")
    s = sub1(s, 'enter(_, sc) { plain(); clDesks($(".cl-desks", sc)); S.k = 0; },',
        '''enter(_, sc) {
      plain(); clDesks($(".cl-desks", sc)); S.k = 0; S.pend = 0;
      // the campus strategy's 3D model, built ahead while this page is up, so it comes in without a wait (9 Nov)
      setTimeout(() => { try { if (window.AxoLayers && AxoLayers.available()) AxoLayers.get(); } catch (e) { /* the picture stays */ } }, 1200);   // not in S.t: step() clears those
      const pg = $(".page", sc), f = window.ACKO_MORPH && ACKO_MORPH.take("s-pitch");
      pg.classList.remove("cl-arrive", "cl-land"); S.arr = !!(f && f.m && !reduced);
      if (S.arr) {                                     // from the pitches: the floor where it lay there, tilting into the axo
        const g = $(".cl-morph g", sc); ACKO_MORPH.draw(g); pg.classList.add("cl-arrive");
        ACKO_MORPH.anim(g, f.m, ACKO_MORPH.AXO, 1700, () => {
          if (document.body.dataset.scene !== sc.id) return;
          S.arr = false; pg.classList.remove("cl-arrive"); pg.classList.add("cl-land");
          S.t.push(setTimeout(() => api.step(S.pend || 1, sc), 350));
        });
      }
    },''', "enter")
    s = sub1(s, "    step(k, sc) {\n      const svg", "    step(k, sc) {\n      if (S.arr) { S.pend = k; return; }             // the floor still tilting in: this beat once it has landed\n      const svg", "step") if "    step(k, sc) {\n      const svg" in s else sub1(s, "    step(k, sc) {\r\n      const svg", "    step(k, sc) {\r\n      if (S.arr) { S.pend = k; return; }             // the floor still tilting in: this beat once it has landed\r\n      const svg", "step")
    s = sub1(s, "  return {\n    enter(_, sc) {\n      plain(); clDesks", "  const api = {\n    enter(_, sc) {\n      plain(); clDesks", "api open")
    s = sub1(s, "    leave() { stop(); },\n  };\n});", "    leave() { stop(); },\n  };\n  return api;\n});", "api close")
    s = sub1(s, "leave() { stop(); },",'leave(_, sc) { stop(); S.arr = false; if (sc) $(".page", sc).classList.remove("cl-arrive", "cl-land"); },', "leave")
    wr(p, s)

# ------------------------------------------------------------------ s-pitch: from Due Diligence the floor glides in; leaving, it marks where it lay
p = "slides/s-pitch.html"; s = rd(p)
if "ACKO_MORPH" not in s:
    s = sub1(s, "</style>", '''/* arriving from Layout · Due Diligence (9 Nov): the bare floor starts on the plan's plate and glides to the touchline; the pitches and
   the words come in round it */
#s-pitch .pp-pitches, #s-pitch .pp-len, #s-pitch .pp-lab, #s-pitch .pp-head, #s-pitch .pp-w { transition: opacity .8s var(--ease); }
#s-pitch .page.pp-arrive :is(.pp-pitches, .pp-len, .pp-lab, .pp-head, .pp-w, [data-only], [data-step]) { opacity: 0 !important; transition: none !important; }
</style>''', "pitch style")
    s = sub1(s, "    step(k, sc) {\n      if (sc._fresh) {", "    step(k, sc) {\n      if (sc._fresh && sc._from) { sc._fresh = false; return glide(sc, k); }\n      if (sc._fresh) {", "pitch step") if "    step(k, sc) {\n      if (sc._fresh) {" in s else sub1(s, "    step(k, sc) {\r\n      if (sc._fresh) {", "    step(k, sc) {\r\n      if (sc._fresh && sc._from) { sc._fresh = false; return glide(sc, k); }\r\n      if (sc._fresh) {", "pitch step")
    s = sub1(s, "      sc._fresh = true;\n", "      sc._fresh = true; sc._from = !reduced && window.ACKO_MORPH ? ACKO_MORPH.take(\"s-layout-dd\") : null;\n", "pitch enter") if "      sc._fresh = true;\n" in s else sub1(s, "      sc._fresh = true;\r\n", "      sc._fresh = true; sc._from = !reduced && window.ACKO_MORPH ? ACKO_MORPH.take(\"s-layout-dd\") : null;\r\n", "pitch enter")
    s = sub1(s, "    leave() { cancelAnimationFrame(raf); },",
        '''    leave(_, sc) {
      cancelAnimationFrame(raf);
      if (sc && window.ACKO_MORPH) { const pg = $(".page", sc), sh = $(".pp-shell", sc); pg.classList.remove("pp-arrive"); sh.removeAttribute("transform"); ACKO_MORPH.mark("s-pitch", { m: ACKO_MORPH.page(sh, pg) }); }
    },''', "pitch leave")
    s = sub1(s, "  return {\n    enter(_, sc) {\n      plain();", '''  // from Due Diligence: the floor laid on the plan's plate (its place on the Layout), gliding to its place here; then the rest
  function glide(sc, k) {
    cancelAnimationFrame(raf); draw(sc, k >= 2 ? 1 : 0);
    const pg = $(".page", sc), sh = $(".pp-shell", sc), M = ACKO_MORPH;
    const from = M.mul(M.inv(M.page($(".pp-svg", sc), pg)), M.rect(M.HOME));
    pg.classList.add("pp-arrive");
    M.anim(sh, from, [1, 0, 0, 1, 0, 0], 1500, () => {
      sh.removeAttribute("transform"); pg.classList.remove("pp-arrive");
      if (k < 2) $$(".pp-stats[data-only='1'] [data-count]", sc).forEach((e, i) => later(() => countUp(e, 1400), 300 + i * 120));
    });
  }
  return {
    enter(_, sc) {
      plain();''', "pitch glide") if "  return {\n    enter(_, sc) {\n      plain();" in s else sub1(s, "  return {\r\n    enter(_, sc) {\r\n      plain();", '''  // from Due Diligence: the floor laid on the plan's plate (its place on the Layout), gliding to its place here; then the rest
  function glide(sc, k) {
    cancelAnimationFrame(raf); draw(sc, k >= 2 ? 1 : 0);
    const pg = $(".page", sc), sh = $(".pp-shell", sc), M = ACKO_MORPH;
    const from = M.mul(M.inv(M.page($(".pp-svg", sc), pg)), M.rect(M.HOME));
    pg.classList.add("pp-arrive");
    M.anim(sh, from, [1, 0, 0, 1, 0, 0], 1500, () => {
      sh.removeAttribute("transform"); pg.classList.remove("pp-arrive");
      if (k < 2) $$(".pp-stats[data-only='1'] [data-count]", sc).forEach((e, i) => later(() => countUp(e, 1400), 300 + i * 120));
    });
  }
  return {
    enter(_, sc) {
      plain();''', "pitch glide")
    wr(p, s)

# ------------------------------------------------------------------ the Layout, split in two
src = rd("slides/s-layout.html")
ROUTE = '{ const g = +b.dataset.go; if (g === 7) go(sceneIx("s-layout-dd"), 1); else go(sceneIx("s-layout-sp"), [1, 2, 3, 4, 5, 6].indexOf(g) + 1); }'
def copy(nid, steps, beats, order, mins):
    s = re.sub(r"(?<![/\w-])s-layout\b", nid, src)
    s = sub1(s, 'data-steps="7"', 'data-steps="%d"' % steps, nid + " steps")
    s = sub1(s, 'data-mins="3"', 'data-mins="%s"' % mins, nid + " mins")
    s = sub1(s, 'data-beats="Due diligence,Spaces,Neighbourhoods,Biophilia · the heat,Biophilia · planting,Biophilia · views to green,Acoustics"', 'data-beats="%s"' % beats, nid + " beats")
    s = sub1(s, "const ORDER = [7, 1, 2, 3, 4, 5, 6];", "const ORDER = %s;          // the re-ordered deck (9 Nov): Due Diligence on its own, the rest after the axos" % order, nid + " order")
    s = sub1(s, 'go(sceneIx("%s"), ORDER.indexOf(+b.dataset.go) + 1);' % nid, ROUTE, nid + " pills")
    return s
dd = copy("s-layout-dd", 1, "Due diligence", "[7]", "0.6")
dd = sub1(dd, "      plan.planOff();\n    },", "      plan.planOff();\n      if (window.ACKO_MORPH) ACKO_MORPH.mark(\"s-layout-dd\");   // the pitches pick the floor up from here\n    },", "dd leave") if "      plan.planOff();\n    }," in dd else sub1(dd, "      plan.planOff();\r\n    },", "      plan.planOff();\r\n      if (window.ACKO_MORPH) ACKO_MORPH.mark(\"s-layout-dd\");   // the pitches pick the floor up from here\r\n    },", "dd leave")
sp = copy("s-layout-sp", 6, "Spaces,Neighbourhoods,Biophilia · the heat,Biophilia · planting,Biophilia · views to green,Acoustics", "[1, 2, 3, 4, 5, 6]", "2.4")
# Spaces: from the Employees Journey the furnished 3D model itself turns straight down onto the plan (s-strategy's _flatten), and the
# 2D plan takes over from it (Ritika, 9 Nov: "entire axo turning into spaces layout - in between empty layout shouldnt be there")
old = '      arriving = document.body.classList.contains("si-left"); pend = 0;\n      if (arriving) {'
new = '''      arriving = document.body.classList.contains("si-left"); pend = 0;
      const ax = !arriving && window.ACKO_MORPH && !matchMedia("(prefers-reduced-motion: reduce)").matches ? (ACKO_MORPH.take("s-strategy") || ACKO_MORPH.take("s-walk")) : null;
      const st = ax && document.getElementById(ax.id);          // the strategy's axo, or the walk's view from above
      if (st && st._flatten) {                          // from the Employees Journey: the model turns down onto the plan, then the plan
        arriving = true; document.body.classList.add("ly-arrive"); sc.classList.add("ly-arrive");
        const ok = st._flatten(home(), 1700, (h) => {
          if (document.body.dataset.scene !== sc.id) { h.remove(); return; }
          arriving = false; build(sc); self.step(pend || 1, sc);          // planOn: the 2D plan fades in under the model
          sc._h3 = h; h.style.transition = "opacity 1.1s ease-in-out";
          later(() => { h.style.opacity = "0"; }, 300);                   // the model fades off the plan it now lies on
          later(() => { h.remove(); sc._h3 = null; }, 1600);
          later(() => sc.classList.remove("ly-arrive"), 1100);
          later(() => document.body.classList.remove("ly-arrive"), 1800);
        });
        if (!ok) { arriving = false; document.body.classList.remove("ly-arrive"); sc.classList.remove("ly-arrive"); build(sc); }
      } else if (arriving) {'''
sp = sub1(sp, old, new, "sp enter")
sp = sub1(sp, "      plan.planOff();\n    },", "      plan.planOff();\n      if (sc && sc._h3) { sc._h3.remove(); sc._h3 = null; }   // left mid-turn: the model's host goes\n    },", "sp leave host")
sp = sub1(sp, 'document.body.classList.remove("ly-arrive", "si-into"); if (sc) sc.classList.remove("ly-arrive");', 'document.body.classList.remove("ly-arrive", "si-into"); if (sc) sc.classList.remove("ly-arrive");', "sp leave")
wr("slides/s-layout-dd.html", dd); wr("slides/s-layout-sp.html", sp)

# ------------------------------------------------------------------ s-strategy: leaving, it marks the axo (the camera is fitted to the same footprint)
p = "slides/s-strategy.html"; s = rd(p)
if "ACKO_MORPH" not in s:
    m = re.search(r"\n    leave\(([^)]*)\) \{", s)
    assert m, "strategy leave"
    s = s[:m.end()] + ' if (window.ACKO_MORPH) ACKO_MORPH.mark("s-strategy");   // Layout · Spaces flattens the floor from here (9 Nov)' + s[m.end():]
    wr(p, s)

# ------------------------------------------------------------------ s-strategy: _flatten, the furnished model turning straight down onto the plan
p = "slides/s-strategy.html"; s = rd(p)
if "_flatten" not in s:
    FL = '''  // Layout · Spaces, arriving from here (9 Nov, the re-ordered deck): the furnished model, route and all, turns straight down until it
  // lies on the plan's home view (vb, plan mm). The 3D floor and the plan differ by a translation in mm: world x = (plan x − 185842 −
  // M.CX)/1000, z = (plan y + 182802 − M.CY)/1000; φ from vertical, so straight down is φ ≈ 0 (exactly 0 is degenerate), θ 0 is north up.
  // The canvas goes into a host of its own, first in #stage under both pages, so it never blinks in the slides' cross-fade; its own
  // frames (this slide's draw() stops once it isn't the scene); the names and leaders go at once; done(host) when it lands
  function flatten(vb, ms, done) {
    if (!M || !r || !cam) return false;
    const stage = document.getElementById("stage"); if (!stage) return false;
    const h = document.createElement("div"); h.className = "st-flat-host";
    h.style.cssText = "position:fixed;left:var(--pl);top:var(--ptop);width:var(--pw);height:var(--ph);pointer-events:none;z-index:0";
    stage.insertBefore(h, stage.firstChild);
    const cv = r.domElement; h.appendChild(cv); cv.style.width = "100%"; cv.style.height = "100%"; cv.style.display = "block";
    sc.classList.add("st-flat");
    cancelAnimationFrame(S.raf); S.raf = 0; S.playing = false; S.tween = null;
    const from = { theta: S.state.theta, phi: S.state.phi, half: S.state.half, t: S.state.t.slice() }, d0 = S.dim || 0;
    const to = { theta: 0, phi: 1e-4, half: vb[3] / 2000, t: [(vb[0] + vb[2] / 2 - 185842 - M.CX) / 1000, 0, (vb[1] + vb[3] / 2 + 182802 - M.CY) / 1000] };
    const paint = (e) => {
      const L = (a, b) => a + (b - a) * e;
      S.state = { theta: L(from.theta, to.theta), phi: L(from.phi, to.phi), half: L(from.half, to.half), t: from.t.map((x, i) => L(x, to.t[i])) };
      S.dim = d0 * (1 - e);                            // the veil lifts: the furniture at full strength, as the plan's
      window.AxoModel.apply(cam, S.state, asp);
      S.veil.visible = S.dim > 0.001; S.veil.material.opacity = S.dim;
      if (S.veil.visible) { cam.updateMatrixWorld(); S.veil.quaternion.copy(cam.quaternion); S.veil.position.copy(cam.position).add(cam.getWorldDirection(v3()).multiplyScalar(5)); S.veil.scale.set(4 * S.state.half * asp, 4 * S.state.half, 1); }
      r.render(M.scene, cam);
    };
    let t0 = 0, end = false;
    const fin = () => { if (end) return; end = true; paint(1); sc.classList.remove("st-flat"); if (done) done(h); };
    const tick = (now) => { if (end) return; if (!t0) t0 = now; const k = Math.min(1, (now - t0) / ms); paint(ease(k)); if (k < 1) requestAnimationFrame(tick); else fin(); };
    paint(0); requestAnimationFrame(tick); setTimeout(fin, ms + 500);
    return true;
  }

'''
    s = sub1(s, "  return {\n    enter(_, s) {\n      sc = s;", FL + "  return {\n    enter(_, s) {\n      sc = s; sc._flatten = flatten;", "strategy flatten")
    s = sub1(s, "</style>", "#s-strategy.st-flat .st-ov, #s-strategy.st-flat .st-cap { opacity: 0; transition: opacity .3s; }   /* turning onto the plan: the names go at once */\n</style>", "strategy style")
    wr(p, s)
print("ok")
