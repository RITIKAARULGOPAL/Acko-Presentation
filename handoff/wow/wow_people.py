# F · 640 people find their seats: s-layout-sp's Spaces beat, only with window.ACKO_WOW (the re-ordered deck)
# run after gen_floorflow.py (which writes s-layout-sp afresh): python wow_people.py <deck-wow checkout>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
p = "slides/s-layout-sp.html"; s, nl = rd(p)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
if "ly-ppl" in s:
    print("already"); sys.exit()
s = sub1(s, '    <div class="ly-top"></div>\n', '''    <!-- the people (9 Nov, the re-ordered deck): 640 come in at the two entrances and walk the Loop to their desks -->
    <canvas class="ly-ppl" aria-hidden="true" style="left:0;top:0;width:100%;height:100%"></canvas>
    <div class="ly-ppl-n" style="left:3%;top:18.6%;width:50%"><b>0</b><span>people, one floor: each to their own desk</span></div>
    <div class="ly-top"></div>
''', "markup")
s = sub1(s, "</style>", '''/* the people (9 Nov): dots in their neighbourhood's colour, walking in from the entrances along the Loop; only on Spaces */
#s-layout-sp .ly-ppl { pointer-events: none; opacity: 0; transition: opacity .6s var(--ease); }
#s-layout-sp.ppl-on .ly-ppl { opacity: 1; }
#s-layout-sp .ly-ppl-n { display: flex; align-items: baseline; gap: calc(var(--pt) * 4); opacity: 0; transition: opacity .6s var(--ease); pointer-events: none; }
#s-layout-sp.ppl-on .ly-ppl-n { opacity: 1; }
#s-layout-sp.ppl-nb .ly-ppl-n { opacity: 0; }
#s-layout-sp .ly-ppl-n b { font-family: var(--num, inherit); font-size: calc(var(--pt) * 22); line-height: 1; font-weight: 600; color: var(--purple-2); font-variant-numeric: tabular-nums; }
#s-layout-sp .ly-ppl-n span { font-size: calc(var(--pt) * 8.5); color: #555; }
</style>''', "style")
s = sub1(s, 'ACKO.slide("s-layout-sp", ({ $, $$, later, go, sceneIx, plan, asset, world }) => {',
         'ACKO.slide("s-layout-sp", ({ $, $$, later, go, sceneIx, plan, asset, world, cue, reduced }) => {', "factory")
PPL = r'''  // ---- the people (9 Nov, the re-ordered deck only: window.ACKO_WOW): 640 of the plan's 646 desks (L.seats, the chairs in the drawing)
  // filled by people who come in at the two entrances (PLAN_DXF.overlays.entry) and walk the employees' route (ACKO_LOOP's graph: the
  // shortest way from the nearer entrance to the route point nearest their desk), then step to it; each in their neighbourhood's
  // colour (the seat tested against the zones' outlines), deepened to show on the plan. Drawn on a canvas over the plan through the
  // plan's own view (so a zoom keeps them on their desks); once per visit, on Spaces
  const PPL = { raf: 0, P: null, t0: 0, on: false };
  const DEEP = { "01": "#2f8fb0", "02": "#7a5cc9", "03": "#46589f", "04": "#a5605f", "05": "#8c8e2e", "06": "#c0577f" };
  function pplBuild() {
    if (PPL.P) return PPL.P;
    const LP = window.ACKO_LOOP, D = plan.data; if (!LP || !L || !L.seats || !D) return null;
    const N = LP.nodes, adj = N.map(() => []);
    LP.edges.forEach(([a, b]) => { const d = Math.hypot(N[a][0] - N[b][0], N[a][1] - N[b][1]); adj[a].push([b, d]); adj[b].push([a, d]); });
    const near = (q) => { let bi = 0, bd = 1e18; N.forEach((n, i) => { const d = (n[0] - q[0]) ** 2 + (n[1] - q[1]) ** 2; if (d < bd) { bd = d; bi = i; } }); return bi; };
    const dij = (src) => {                                // distances and the way back, from one entrance's route point
      const dist = new Float64Array(N.length).fill(Infinity), prev = new Int32Array(N.length).fill(-1), done = new Uint8Array(N.length); dist[src] = 0;
      for (;;) { let u = -1, m = Infinity; for (let i = 0; i < N.length; i++) if (!done[i] && dist[i] < m) { m = dist[i]; u = i; } if (u < 0) break; done[u] = 1;
        for (const [v, d] of adj[u]) if (dist[u] + d < dist[v]) { dist[v] = dist[u] + d; prev[v] = u; } }
      return { dist, prev };
    };
    const E = (D.overlays && D.overlays.entry) || LP.entries, EN = E.map((e) => near(e)), T = EN.map(dij);
    const zones = D.zones.map((z) => ({ n: z.n, R: rings(z.zone) }));
    const inP = (q, ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const [xi, yi] = ring[i], [xj, yj] = ring[j]; if ((yi > q[1]) !== (yj > q[1]) && q[0] < ((xj - xi) * (q[1] - yi)) / (yj - yi) + xi) c = !c; } return c; };
    const seats = L.seats.filter((_, i) => i % 108 !== 107).slice(0, 640);          // 640 people, 646 desks: 6 left free
    const P = seats.map((q, i) => {
      const z = zones.find((z) => z.R.some((r) => inP(q, r))), sn = near(q);
      const e = T[0].dist[sn] <= T[1].dist[sn] ? 0 : 1, way = []; for (let u = sn; u >= 0; u = T[e].prev[u]) way.push(N[u]);
      way.reverse(); const pts = [E[e]].concat(way, [q]);
      const ss = [0]; for (let k = 1; k < pts.length; k++) ss.push(ss[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
      return { pts, ss, len: ss[ss.length - 1], col: DEEP[z ? z.n : "02"] || "#7a5cc9", go: 0 };
    });
    // released in a steady stream over 2.8 s, the two entrances interleaved, in a fixed shuffled order
    const ord = P.map((_, i) => i).sort((a, b) => ((a * 7919) % 640) - ((b * 7919) % 640));
    ord.forEach((i, k) => (P[i].go = (k / P.length) * 2800));
    return (PPL.P = P);
  }
  const SPEED = 42;                                       // m/s on the plan: the far desks reached in about 3 s
  function pplDraw(sc, now) {
    const cv = $(".ly-ppl", sc), v = plan.view; if (!v || !PPL.P) return 0;
    const r = Math.min(2, devicePixelRatio || 1), W = Math.round(cv.clientWidth * r), H = Math.round(cv.clientHeight * r); if (!W || !H) return 0;
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
    const kk = Math.max(v[2] / W, v[3] / H), x0 = v[0] + v[2] / 2 - (W * kk) / 2, y0 = v[1] + v[3] / 2 - (H * kk) / 2;   // the plan's own fit (xMidYMid meet)
    const x = cv.getContext("2d"); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H);
    const rad = 3.4 * W / 1920;                            // 3.4 page px
    let seated = 0; const t = now - PPL.t0;
    for (const o of PPL.P) {
      const d = (t - o.go) / 1000 * SPEED * 1000; if (d <= 0) continue;
      let q; if (d >= o.len) { q = o.pts[o.pts.length - 1]; seated++; }
      else { let a = 0, b = o.ss.length - 1; while (b - a > 1) { const m = (a + b) >> 1; if (o.ss[m] < d) a = m; else b = m; } const f = (d - o.ss[a]) / (o.ss[b] - o.ss[a] || 1); q = [o.pts[a][0] + (o.pts[b][0] - o.pts[a][0]) * f, o.pts[a][1] + (o.pts[b][1] - o.pts[a][1]) * f]; }
      x.beginPath(); x.arc((q[0] - x0) / kk, (q[1] - y0) / kk, rad, 0, 6.2832); x.fillStyle = o.col; x.fill();
      x.lineWidth = 0.9 * r; x.strokeStyle = "rgba(255,255,255,.9)"; x.stroke();
    }
    return seated;
  }
  function ppl(sc, on, play) {
    if (!window.ACKO_WOW) return;
    sc.classList.toggle("ppl-on", !!on); sc.classList.toggle("ppl-nb", !!on && !play);   // ppl-nb: Neighbourhoods, the colours without the count
    if (!on) return;
    if (!pplBuild()) return;
    if (!PPL.on && !play) { PPL.on = true; PPL.t0 = -1e9; $(".ly-ppl-n b", sc).textContent = PPL.P.length; }   // straight to Neighbourhoods: already at their desks
    if (!PPL.on) {                                       // once per visit: the walk in; after it, the dots stay drawn
      PPL.on = true; PPL.t0 = performance.now() + 300; let ticks = 0, end = false;
      const n = $(".ly-ppl-n b", sc);
      if (reduced) PPL.t0 = -1e9;
      const frame = (now) => {
        if (document.body.dataset.scene !== sc.id || !sc.classList.contains("ppl-on")) return;
        const k = pplDraw(sc, now); n.textContent = k;
        if (k >= (ticks + 1) * 80) { ticks++; cue("tick"); }
        if (k < PPL.P.length || !end) { if (k >= PPL.P.length) end = true; PPL.raf = requestAnimationFrame(frame); }
        else { const keep = () => { if (document.body.dataset.scene !== sc.id || !sc.classList.contains("ppl-on")) return; pplDraw(sc, now); PPL.raf = requestAnimationFrame(keep); }; PPL.raf = requestAnimationFrame(keep); }
      };
      cancelAnimationFrame(PPL.raf); PPL.raf = requestAnimationFrame(frame);
      later(() => { n.textContent = PPL.P.length; }, 300 + 2800 + 4200);           // the count lands even without frames
    } else {
      cancelAnimationFrame(PPL.raf);
      const keep = (now) => { if (document.body.dataset.scene !== sc.id || !sc.classList.contains("ppl-on")) return; pplDraw(sc, now); PPL.raf = requestAnimationFrame(keep); };
      PPL.raf = requestAnimationFrame(keep);
    }
  }
'''
s = sub1(s, "  return self = {\n", PPL + "  return self = {\n", "ppl fns")
s = sub1(s, "      band(sc); plan.planHome(home(), was ? 700 : 0);        // the plan centred in what this beat's panel leaves it\n",
         "      band(sc); plan.planHome(home(), was ? 700 : 0);        // the plan centred in what this beat's panel leaves it\n"
         "      ppl(sc, k === 1 || k === 2, k === 1);              // Spaces: the people come in; Neighbourhoods: they stay, in their colours (10 Nov)\n", "step hook")
s = sub1(s, '      arriving = document.body.classList.contains("si-left"); pend = 0;\n',
         '      arriving = document.body.classList.contains("si-left"); pend = 0; PPL.on = false; sc.classList.remove("ppl-on");\n', "enter reset")
s = sub1(s, "      plan.planOff();\n", "      plan.planOff(); cancelAnimationFrame(PPL.raf); if (sc) sc.classList.remove(\"ppl-on\");\n", "leave")
wr(p, s, nl)
print("ok people")
