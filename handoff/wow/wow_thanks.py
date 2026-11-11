# G · the Loop closes: slides/s-thanks-w.html, a copy of s-thanks for the re-ordered deck: the Loop on the floor (the route that ran
# through the deck) traces itself, then folds into ACKO's Möbius and closes, and only then "Thank you"
# run: python wow_thanks.py <deck-wow checkout>
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
s, nl = rd("slides/s-thanks.html")
mob, _ = rd("slides/s-mobius.html")
geo = re.findall(r'<path class="mr-geo (f1|bk|f2)" d="([^"]+)"', mob)
assert len(geo) == 3, geo
s = re.sub(r"(?<![/\w-])s-thanks\b", "s-thanks-w", s)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
s = s.replace('data-notes="Thank you.', 'data-notes="The route that ran through the deck traces itself once more, then folds back into ACKO\'s Möbius and closes: where it began. Thank you.', 1)
s = sub1(s, '  <div class="page">\n', '''  <div class="page">
    <!-- the Loop closes (9 Nov): the floor's Loop, then the Möbius (s-mobius's centre line, photo px), drawn on a canvas -->
    <svg class="tw-geo" viewBox="0 0 1536 1024" aria-hidden="true" style="left:0;top:0;width:0;height:0;overflow:hidden">''' +
    "".join('<path class="g-%s" d="%s"/>' % (k, d) for k, d in geo) + '''</svg>
    <canvas class="tw-rib" aria-hidden="true" style="left:0;top:0;width:100%;height:100%"></canvas>
''', "markup")
s = sub1(s, "</style>", '''/* the Loop closes (9 Nov): the words wait for the ribbon */
#s-thanks-w .tw-rib { pointer-events: none; }
#s-thanks-w.tw-wait .th-h, #s-thanks-w.tw-wait .th-p, #s-thanks-w.tw-wait .th-btns { opacity: 0 !important; transform: translateY(10px) !important; }
#s-thanks-w .th-h, #s-thanks-w .th-p, #s-thanks-w .th-btns { transition: opacity .9s var(--ease), transform .9s var(--ease); }
#s-thanks-w .th-p { transition-delay: .35s; }
#s-thanks-w .th-btns { transition-delay: .7s; }
</style>''', "style")
JS = r'''<script>
/* thank you: the Appendix and About SKV from here. The re-ordered deck (9 Nov): first the Loop closes. The route on the floor (ACKO_LOOP's
   west-to-east sweep, as it lay on the Loop slide and the plans) traces itself across the page, then folds point by point into ACKO's
   Möbius (s-mobius's centre line: behind, front, front, behind, from her left-most point) and closes; then the words */
ACKO.slide("s-thanks-w", ({ $, plain, reveal, go, trackIdx, sceneIx, later, reduced, cue }) => {
  const N = 520, LAV = "rgb(190,164,245)", R = { raf: 0, A: null, B: null };
  const ease = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  function resample(P, n) {
    const ss = [0]; for (let i = 1; i < P.length; i++) ss.push(ss[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const L = ss[ss.length - 1], out = []; let j = 0;
    for (let k = 0; k < n; k++) { const s = (k / (n - 1)) * L; while (j < ss.length - 2 && ss[j + 1] < s) j++; const f = ss[j + 1] > ss[j] ? (s - ss[j]) / (ss[j + 1] - ss[j]) : 0; out.push([P[j][0] + (P[j + 1][0] - P[j][0]) * f, P[j][1] + (P[j + 1][1] - P[j][1]) * f]); }
    return out;
  }
  const fit = (P, box) => {                              // P scaled into box [x0, y0, x1, y1], centred, keeping its shape
    const xs = P.map((p) => p[0]), ys = P.map((p) => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const k = Math.min((box[2] - box[0]) / (x1 - x0), (box[3] - box[1]) / (y1 - y0)), cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2;
    return P.map(([x, y]) => [cx + (x - (x0 + x1) / 2) * k, cy + (y - (y0 + y1) / 2) * k]);
  };
  function build(sc) {
    if (R.A) return true;
    const LP = window.ACKO_LOOP; if (!LP) return false;
    const toPage = (p) => [149.76 + 1.055 * p.x, 1.0547 * p.y];
    const smp = (el, a, b) => { const out = [], L = el.getTotalLength(); a = a || 0; b = b == null ? L : b; const n = Math.max(2, Math.ceil((b - a) / 6)); for (let i = 0; i <= n; i++) out.push(toPage(el.getPointAtLength(a + ((b - a) * i) / n))); return out; };
    const f1 = $(".g-f1", sc), bk = $(".g-bk", sc), f2 = $(".g-f2", sc);
    // her left-most point on the behind part: where the strip starts and closes (s-mobius CUT)
    const CUT = [344.19, 543.99], Lb = bk.getTotalLength(); let c = 0, best = 1e9;
    for (let l = 0; l <= Lb; l += 3) { const p = toPage(bk.getPointAtLength(l)), d = Math.hypot(p[0] - CUT[0], p[1] - CUT[1]); if (d < best) { best = d; c = l; } }
    const mob = smp(bk, c).concat(smp(f2), smp(f1), smp(bk, 0, c));
    R.B = resample(fit(mob, [660, 80, 1260, 410]), N);
    R.A = resample(fit(window.ACKO_LOOP_SMOOTH ? window.ACKO_LOOP_SMOOTH(LP) : LP.sweep, [180, 150, 1740, 300]), N);   // the smooth Loop (10 Nov)
    return true;
  }
  function rib(cv, pts, wid, head) {                     // the ribbon along pts up to share head of its length, ends tapering
    const r = Math.min(2, devicePixelRatio || 1), W = Math.round(cv.clientWidth * r), H = Math.round(cv.clientHeight * r);
    if (!W || !H) return; if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const k = W / 1920, x = cv.getContext("2d"); x.clearRect(0, 0, W, H);
    if (!pts) return;
    const m = Math.max(2, Math.round(pts.length * head)), P = pts.slice(0, m), n = P.length, ss = [0];
    for (let i = 1; i < n; i++) ss.push(ss[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const L = ss[n - 1], TAP = Math.min(160, L * 0.1);
    const E = P.map((p, i) => {
      const a = P[Math.max(0, i - 1)], b = P[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const u = Math.min(1, Math.min(ss[i], L - ss[i]) / TAP), e = u * u * (3 - 2 * u), w = wid * (0.1 + 0.9 * e) / 2;
      return [[(p[0] - dy / l * w) * k, (p[1] + dx / l * w) * k], [(p[0] + dy / l * w) * k, (p[1] - dx / l * w) * k]];
    });
    x.globalAlpha = 0.85; x.fillStyle = LAV; x.beginPath(); E.forEach((e) => x.lineTo(e[0][0], e[0][1])); for (let i = n - 1; i >= 0; i--) x.lineTo(E[i][1][0], E[i][1][1]); x.closePath(); x.fill();
    x.globalAlpha = 0.9; x.strokeStyle = "rgba(255,255,255,.8)"; x.lineWidth = 1.3 * k; x.lineJoin = "round";
    [0, 1].forEach((j) => { x.beginPath(); E.forEach((e) => x.lineTo(e[j][0], e[j][1])); x.stroke(); });
    x.globalAlpha = 1;
  }
  const at = (e) => R.A.map((a, i) => [a[0] + (R.B[i][0] - a[0]) * e, a[1] + (R.B[i][1] - a[1]) * e]);
  const words = (sc) => sc.classList.remove("tw-wait");
  return {
    enter(_, sc) {
      plain(); reveal($(".page", sc), 100);
      $("#to-appendix").onclick = () => go(trackIdx("appendix")[0], 1);
      $("#to-skv").onclick = () => go(sceneIx("s-skv"), 1);
      cancelAnimationFrame(R.raf);
      const cv = $(".tw-rib", sc);
      if (!build(sc)) return;
      if (reduced) { rib(cv, R.B, 30, 1); return; }
      sc.classList.add("tw-wait"); rib(cv, null);
      // 0.3–1.6 s the floor's Loop traces itself; 1.9–4.1 s it folds into the Möbius, widening; closed, then the words
      const t0 = performance.now(); let shut = false;
      const close = () => { if (shut) return; shut = true; rib(cv, R.B, 30, 1); cue("close"); later(() => words(sc), 350); };
      const frame = (now) => {
        if (document.body.dataset.scene !== sc.id || shut) return;
        const t = (now - t0) / 1000;
        if (t < 1.9) rib(cv, R.A, 12, ease(Math.min(1, Math.max(0, (t - 0.3) / 1.3))));
        else { const e = ease(Math.min(1, (t - 1.9) / 2.2)); rib(cv, at(e), 12 + 18 * e, 1); if (e >= 1) return close(); }
        R.raf = requestAnimationFrame(frame);
      };
      R.raf = requestAnimationFrame(frame); later(close, 4600);
    },
    leave(_, sc) { cancelAnimationFrame(R.raf); if (sc) sc.classList.remove("tw-wait"); },
  };
});
</script>'''
s = re.sub(r"<script>\n/\* thank you:.*?</script>", lambda m: JS, s, count=1, flags=re.S)
assert 'ACKO.slide("s-thanks-w", ({ $, plain, reveal, go, trackIdx, sceneIx, later' in s
wr("slides/s-thanks-w.html", s, nl)
print("ok thanks")
