# B · the Möbius becomes the floor: slides/s-loop-w.html, a copy of s-loop with a third beat, "On the floor" (the re-ordered deck only)
# run: python wow_loop.py <deck-wow checkout>
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
s, nl = rd("slides/s-loop.html")
s = re.sub(r"(?<![/\w-])s-loop\b", "s-loop-w", s)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)

s = sub1(s, 'data-steps="2" data-mins="1" data-beats="Welcome to the Loop,Where emotions matter"',
         'data-steps="3" data-mins="1.2" data-beats="Welcome to the Loop,Where emotions matter,On the floor"', "beats")
s = s.replace('data-notes="1 · The Loop draws', 'data-notes="3 · On the floor: the ribbon leaves the page and lies down on the real floor as the Loop, one path through all seven stops, Arrival to Wellness: the concept is the plan. 1 · The Loop draws', 1)
s = sub1(s, "  </div>\n</section>", '''    <!-- 3 · on the floor (9 Nov): the ribbon lies down on the real floor, the Loop through all seven stops -->
    <svg class="lw-floor" viewBox="0 0 1920 1080" preserveAspectRatio="none" aria-hidden="true" style="left:0;top:0;width:100%;height:100%"></svg>
    <canvas class="lw-rib" style="left:0;top:0;width:100%;height:100%"></canvas>
    <div class="lw-stops" style="left:0;top:0;width:100%;height:100%"></div>
    <h2 class="lw-h" data-only="3" style="left:3.4%;top:12%;width:80%">The Loop, <b>on the floor.</b></h2>
    <p class="lw-p hand" data-only="3" style="left:3.4%;top:74%;width:60%">one path through all seven stops: the concept is the plan</p>
  </div>
</section>''', "markup")
s = sub1(s, "</style>", '''/* 3 · on the floor (9 Nov): the picture ribbon, the people and the words give way; the vector ribbon lies down on the floor */
#s-loop-w .lp-draw, #s-loop-w .lp-cuts { transition: opacity .6s var(--ease); }
#s-loop-w.lw-on .lp-draw, #s-loop-w.lw-on .lp-cuts { opacity: 0 !important; }
#s-loop-w .lw-rib { pointer-events: none; }
#s-loop-w .lw-floor { opacity: 0; transition: opacity .3s; }
#s-loop-w.lw-on .lw-floor { opacity: 1; transition: opacity 1s var(--ease) .9s; }
#s-loop-w .lw-floor .plate { fill: #f6f3ff; stroke: var(--purple-2, #5222d0); stroke-width: 1.6; stroke-linejoin: round; }
#s-loop-w .lw-floor .core { fill: #e4e0ee; stroke: #a49cc0; stroke-width: .8; }
#s-loop-w .lw-floor .lead { fill: none; stroke: var(--purple); stroke-width: 1; stroke-dasharray: 2 4; opacity: 0; transition: opacity .5s; }
#s-loop-w .lw-floor .lead.on { opacity: .9; }
#s-loop-w .lw-stop { position: absolute; width: 0; height: 0; opacity: 0; transition: opacity .5s var(--ease); }
#s-loop-w .lw-stop.on { opacity: 1; }
#s-loop-w .lw-stop i { position: absolute; width: calc(var(--pt) * 6); height: calc(var(--pt) * 6); margin: calc(var(--pt) * -3) 0 0 calc(var(--pt) * -3); border-radius: 50%; background: var(--purple); box-shadow: 0 0 0 calc(var(--pt) * 2) rgba(255,255,255,.9); }
#s-loop-w .lw-stop.on i { animation: pulseP 2.2s infinite; }
#s-loop-w .lw-stop .lab { position: absolute; transform: translate(-50%, -50%); text-align: center; white-space: nowrap; line-height: 1.25; }
#s-loop-w .lw-stop .lab b { display: block; font-size: calc(var(--pt) * 7.5); font-weight: 700; color: #000; }
#s-loop-w .lw-stop .lab q { display: block; quotes: none; font-size: calc(var(--pt) * 6.5); font-style: italic; font-weight: 600; color: var(--plum); }
#s-loop-w .lw-stop .lab q::before { content: "\\201C "; }
#s-loop-w .lw-stop .lab q::after { content: " \\201D"; }
#s-loop-w .lw-h { margin: 0; font-size: calc(var(--pt) * 24); font-weight: 400; color: #000; }
#s-loop-w .lw-h b { font-weight: 700; color: var(--purple-2, #5222d0); }
#s-loop-w .lw-p { margin: 0; font-size: calc(var(--pt) * 16); color: var(--purple-2, #5222d0); }
#s-loop-w [data-only="3"] { transition-delay: 2.4s; }
#s-loop-w .page:not(.lw-b3) [data-only="3"] { transition-delay: 0s; }
</style>''', "style")

# the script: the factory gets the plan kit and the cues; beat 3 lies the ribbon down on the floor
s = sub1(s, 'ACKO.slide("s-loop-w", ({ $, $$, plain, reveal, later, clearTimers, reduced, asset }) => {',
         'ACKO.slide("s-loop-w", ({ $, $$, plain, reveal, later, clearTimers, reduced, asset, plan, cue }) => {', "factory")
FLOOR = r'''  // ---- 3 · on the floor (9 Nov): the Loop's line, resampled, eases point by point onto the Loop on the real floor (ACKO_LOOP.sweep,
  // the employees' route west to east through the stops as they lie), the ribbon narrowing as it lands; the bare floor comes up under
  // it (ACKO_FLOOR: plan mm = unit × 50 + (8842, 12775)), then the seven stops on their real spots. Both drawn where the Layout's
  // plan will sit (its home view), so the floor met later is this one.
  const N3 = 420, W3 = { raf: 0 };
  const LAV = "rgb(190,164,245)";
  function resample(P, n) {
    const ss = [0]; for (let i = 1; i < P.length; i++) ss.push(ss[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const L = ss[ss.length - 1], out = []; let j = 0;
    for (let k = 0; k < n; k++) { const s = (k / (n - 1)) * L; while (j < ss.length - 2 && ss[j + 1] < s) j++; const f = ss[j + 1] > ss[j] ? (s - ss[j]) / (ss[j + 1] - ss[j]) : 0; out.push([P[j][0] + (P[j + 1][0] - P[j][0]) * f, P[j][1] + (P[j + 1][1] - P[j][1]) * f]); }
    return out;
  }
  // the Loop, smooth (10 Nov, Ritika: "make the loop look smooth"): the route's corridor zig-zags gone, its course kept. Through every
  // stop exactly (the sweep passes them at sweepStops), with a few of the route's own points between (one every 30 m, none near a stop),
  // a centripetal Catmull-Rom spline, then eased a few times with the stops held. Plan mm in, plan mm out; also for the Thank-you slide
  window.ACKO_LOOP_SMOOTH = window.ACKO_LOOP_SMOOTH || function (LP) {
    const S = LP.sweep, idx = (LP.sweepStops || []).map((o) => o.i).sort((a, b) => a - b);
    if (!S || idx.length < 2) return S;
    const keys = [], pin = [], d = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    for (let s = 0; s < idx.length - 1; s++) {
      const a = idx[s], b = idx[s + 1], arc = [0];
      for (let i = a + 1; i <= b; i++) arc.push(arc[arc.length - 1] + d(S[i], S[i - 1]));
      keys.push(S[a]); pin.push(true);
      const L = arc[arc.length - 1], n = Math.floor(L / 30000);
      for (let k = 1; k <= n; k++) { const at = (k * L) / (n + 1); if (at < 12000 || L - at < 12000) continue;
        let j = 1; while (j < arc.length - 1 && arc[j] < at) j++; keys.push(S[a + j]); pin.push(false); }
    }
    keys.push(S[idx[idx.length - 1]]); pin.push(true);
    const out = [], hold = [], SEG = 16;                      // centripetal Catmull-Rom through the keys
    for (let i = 0; i < keys.length - 1; i++) {
      const p0 = keys[Math.max(0, i - 1)], p1 = keys[i], p2 = keys[i + 1], p3 = keys[Math.min(keys.length - 1, i + 2)];
      const t1 = Math.sqrt(d(p0, p1)) || 1, t2 = t1 + (Math.sqrt(d(p1, p2)) || 1), t3 = t2 + (Math.sqrt(d(p2, p3)) || 1);
      for (let k = 0; k < SEG; k++) {
        const t = t1 + ((t2 - t1) * k) / SEG, L = (A, B, ta, tb) => [0, 1].map((c) => (tb - t) / (tb - ta) * A[c] + (t - ta) / (tb - ta) * B[c]);
        const A1 = L(p0, p1, 0, t1), A2 = L(p1, p2, t1, t2), A3 = L(p2, p3, t2, t3), B1 = L(A1, A2, 0, t2), B2 = L(A2, A3, t1, t3);
        out.push(k === 0 ? p1.slice() : L(B1, B2, t1, t2)); hold.push(k === 0 && pin[i]);
      }
    }
    out.push(keys[keys.length - 1].slice()); hold.push(true);
    for (let it = 0; it < 4; it++) for (let i = 1; i < out.length - 1; i++) if (!hold[i])   // eased, the stops held
      out[i] = [0, 1].map((c) => (out[i - 1][c] + 2 * out[i][c] + out[i + 1][c]) / 4);
    return out;
  };
  function wbuild(sc) {
    if (sc._lw) return sc._lw;
    const LP = window.ACKO_LOOP, F = window.ACKO_FLOOR, D = window.PLAN_DXF; if (!LP || !F || !D) return null;
    const [vx, vy, vw, vh] = D.viewBox, vb = plan.vbFor([vx, vy, vx + vw, vy + vh], [35, 157, 1885, 670]), k = 1920 / vb[2], P = (x, y) => [(x - vb[0]) * k, (y - vb[1]) * k];
    const FP = (q) => P(q[0] * 50 + 8842, q[1] * 50 + 12775), d = (pts) => "M" + pts.map((q) => FP(q).map((v) => v.toFixed(1)).join(" ")).join("L") + "Z";
    const T = track(sc);
    const A = resample(T.pts.slice(Math.ceil(40 / 6), T.pts.length - Math.ceil(40 / 6)), N3), B = resample(window.ACKO_LOOP_SMOOTH(LP).map((q) => P(q[0], q[1])), N3);
    // the stops: on their spots, the labels above or below the floor, alternately west to east, clear of each other
    const top = Math.min(...F.plate.map((q) => FP(q)[1])), bot = Math.max(...F.plate.map((q) => FP(q)[1]));
    const QUOTE = { "Arrival": "I feel welcomed", "Café": "Hey We finally meet !", "Board Room": "This is my big moment", "Meeting Rooms": "My Impact", "Collab": "Wow, worth the commute", "Work": "These are my folks!", "Wellness": "They thought of me too!" };
    const st = LP.stops.map((o) => ({ name: o.name, q: QUOTE[o.name] || "", p: P(o.x, o.y) })).sort((a, b) => a.p[0] - b.p[0]);
    st.forEach((o, i) => { o.up = i % 2 === 0; o.l = [Math.max(110, Math.min(1810, o.p[0])), o.up ? top - 58 : bot + 58]; });
    const svg = $(".lw-floor", sc);
    svg.innerHTML = `<path class="plate" d="${d(F.plate)}"/>` + (F.cores || []).map((c) => `<path class="core" d="${d(c)}"/>`).join("") +
      st.map((o, i) => `<path class="lead" data-k="${i}" d="M${o.p[0].toFixed(1)} ${o.p[1].toFixed(1)}L${o.l[0].toFixed(1)} ${(o.l[1] + (o.up ? 22 : -22)).toFixed(1)}"/>`).join("");
    $(".lw-stops", sc).innerHTML = st.map((o) => `<div class="lw-stop" style="left:${(o.p[0] / 19.2).toFixed(3)}%;top:${(o.p[1] / 10.8).toFixed(3)}%"><i></i>` +
      `<div class="lab" style="left:calc(${((o.l[0] - o.p[0]) / 19.2).toFixed(3)} * var(--pw) / 100);top:calc(${((o.l[1] - o.p[1]) / 10.8).toFixed(3)} * var(--ph) / 100)"><b>${o.name}</b><q>${o.q}</q></div></div>`).join("");
    return (sc._lw = { A, B, st });
  }
  function rib(cv, pts, wid) {                             // a ribbon along pts (page px): filled lilac, white edges, its ends tapering
    const r = Math.min(2, devicePixelRatio || 1), W = Math.round(cv.clientWidth * r), H = Math.round(cv.clientHeight * r);
    if (!W || !H) return; if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const k = W / 1920, x = cv.getContext("2d"); x.clearRect(0, 0, W, H);
    if (!pts) return;
    const n = pts.length, ss = [0]; for (let i = 1; i < n; i++) ss.push(ss[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const L = ss[n - 1], TAP = Math.min(220, L * 0.12);
    const E = pts.map((p, i) => {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const u = Math.min(1, Math.min(ss[i], L - ss[i]) / TAP), e = u * u * (3 - 2 * u), w = wid * (0.08 + 0.92 * e) / 2;
      return [[(p[0] - dy / l * w) * k, (p[1] + dx / l * w) * k], [(p[0] + dy / l * w) * k, (p[1] - dx / l * w) * k]];
    });
    x.globalAlpha = 0.8; x.fillStyle = LAV; x.beginPath(); E.forEach((e) => x.lineTo(e[0][0], e[0][1])); for (let i = n - 1; i >= 0; i--) x.lineTo(E[i][1][0], E[i][1][1]); x.closePath(); x.fill();
    x.globalAlpha = 1; x.strokeStyle = "#fff"; x.lineWidth = 1.4 * k; x.lineJoin = "round";
    [0, 1].forEach((j) => { x.beginPath(); E.forEach((e) => x.lineTo(e[j][0], e[j][1])); x.stroke(); });
  }
  const ease3 = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  function lwAt(sc, e) {                                   // the ribbon at share e of the way from the Loop's line to the floor
    const G = sc._lw; if (!G) return;
    rib($(".lw-rib", sc), G.A.map((a, i) => [a[0] + (G.B[i][0] - a[0]) * e, a[1] + (G.B[i][1] - a[1]) * e]), 60 + (13 - 60) * e);
  }
  function lwStops(sc, on, play) {
    $$(".lw-stop", sc).forEach((n, i) => { const f = () => { n.classList.toggle("on", on); const l = $(`.lw-floor .lead[data-k="${i}"]`, sc); if (l) l.classList.toggle("on", on); };
      if (on && play) later(f, 120 * i); else f(); });
  }
  function onFloor(sc, play) {
    cancelAnimationFrame(W3.raf);
    if (!wbuild(sc)) return;
    sc.classList.add("lw-on"); $(".page", sc).classList.add("lw-b3");
    if (!play || reduced) { lwAt(sc, 1); lwStops(sc, true, false); return; }
    cue("whoosh"); lwAt(sc, 0);
    const t0 = performance.now(), MS = 2300, WAIT = 250;
    let done = false;
    const land = () => { if (done) return; done = true; lwAt(sc, 1); lwStops(sc, true, true); cue("chime"); };
    const frame = (now) => {
      if (document.body.dataset.scene !== sc.id || done) return;
      const u = Math.min(1, Math.max(0, (now - t0 - WAIT) / MS)); lwAt(sc, ease3(u));
      if (u < 1) W3.raf = requestAnimationFrame(frame); else land();
    };
    W3.raf = requestAnimationFrame(frame); later(land, WAIT + MS + 400);
  }
  function offFloor(sc) {
    cancelAnimationFrame(W3.raf); sc.classList.remove("lw-on"); $(".page", sc).classList.remove("lw-b3");
    rib($(".lw-rib", sc), null, 0); if (sc._lw) lwStops(sc, false, false);
  }
'''
s = sub1(s, "  return {\n    enter(_, sc) { plain(); build(sc);", FLOOR + "  return {\n    enter(_, sc) { plain(); build(sc);", "floor fns")
s = sub1(s, "      const fresh = S.fresh; S.fresh = false;\n",
         "      const fresh = S.fresh; S.fresh = false;\n"
         "      if (k === 3) { if (fresh) laid(sc); onFloor(sc, !fresh); return; }   // 3 · on the floor (fresh: come back to it, laid at once)\n"
         "      offFloor(sc);\n", "step")
s = sub1(s, "    leave() { cancelAnimationFrame(S.raf); S.fresh = false; },", "    leave(_, sc) { cancelAnimationFrame(S.raf); cancelAnimationFrame(W3.raf); S.fresh = false; if (sc && sc.classList.contains(\"lw-on\") && window.ACKO_MORPH) ACKO_MORPH.mark(\"s-loop-w\"); if (sc) offFloor(sc); },   // on the floor: the strategy rises out of it (10 Nov)", "leave")
wr("slides/s-loop-w.html", s, nl)
print("ok s-loop-w")
