# The sun path on Layout · Due Diligence (Ritika, 9 Nov: "add sun path in site due diligence itself"): s-layout-dd gets a second beat,
# Sun path: the site sun study on the plan. Run after gen_floorflow.py (which writes s-layout-dd afresh): python wow_sundd.py <deck-wow>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
p = "slides/s-layout-dd.html"; s, nl = rd(p)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
if "dd-sun" in s:
    print("already"); sys.exit()
s = sub1(s, 'data-steps="1"', 'data-steps="2"', "steps")
s = sub1(s, 'data-beats="Due diligence"', 'data-beats="Due diligence,Sun path"', "beats")
s = s.replace('data-notes="', 'data-notes="2 · Sun path: the site sun study on the plan, every half hour from 7 am to 6:30 pm (20 Mar / 23 Sep; 21 Jun and 21 Dec on the chips): the sun\'s way round the building, its light across the floor and the sunlit patches. ', 1)
s = sub1(s, '      <div class="dds"></div>\n    </div>\n', '''      <div class="dds"></div>
    </div>
    <!-- 2 · the sun path (9 Nov): the site sun study on the plan -->
    <div class="ly-p dd-sunp ui" data-p="sun">
      <div class="lead"><small>02</small><h2>Sun path</h2>
        <p>The site's sun study on the floor: the sun's way round the building, and where its light falls, <b>half hour by half hour.</b></p></div>
      <div class="dd-clock"><b>07:00</b><span><small></small><i class="dd-days"><button type="button" data-d="0">Mar · Sep</button><button type="button" data-d="1">Jun</button><button type="button" data-d="2">Dec</button></i></span></div>
    </div>
''', "panel")
s = sub1(s, '    <div class="ly-top"></div>\n', '''    <svg class="dd-sun" viewBox="0 0 1920 1080" preserveAspectRatio="none" aria-hidden="true" style="left:0;top:0;width:100%;height:100%"><g class="dd-sun-g">
      <path class="arc"/><g class="ticks"></g>
      <g class="lit" transform="matrix(50 0 0 50 8842 12775)"><g class="a"></g><g class="b"></g></g>
      <line class="ray"/><circle class="halo"/><circle class="sun"/></g></svg>
    <div class="ly-top"></div>
''', "svg")
s = sub1(s, "</style>", '''/* 2 · the sun path (9 Nov): the arc of the day round the floor, the sun on it, its light, the sunlit patches; in plan mm over the plan's view */
#s-layout-dd .dd-sun { pointer-events: none; opacity: 0; transition: opacity .6s var(--ease); }
#s-layout-dd.dd-on .dd-sun { opacity: 1; }
#s-layout-dd .dd-sun .arc { fill: none; stroke: #e89a1c; stroke-width: 2; stroke-dasharray: 6 6; vector-effect: non-scaling-stroke; }
#s-layout-dd .dd-sun .ticks circle { fill: #fff; stroke: #e89a1c; stroke-width: 1.6; vector-effect: non-scaling-stroke; }
#s-layout-dd .dd-sun .ticks text { font-size: 2300px; font-weight: 600; fill: #b06f05; }
#s-layout-dd .dd-sun .lit g { opacity: 0; transition: opacity .45s linear; }
#s-layout-dd .dd-sun .lit g.on { opacity: 1; }
#s-layout-dd .dd-sun .lit path { fill: #ffc23a; fill-opacity: .6; mix-blend-mode: multiply; }
#s-layout-dd .dd-sun .ray { stroke: #f2a72a; stroke-width: 2; stroke-dasharray: 3 7; opacity: .75; vector-effect: non-scaling-stroke; transition: opacity .3s; }
#s-layout-dd .dd-sun .sun { fill: #ffb21f; stroke: #fff; stroke-width: 2.5; vector-effect: non-scaling-stroke; }
#s-layout-dd .dd-sun .halo { fill: #ffc84a; opacity: .28; }
#s-layout-dd.dd-on .ly-p[data-p="7"] { opacity: 0 !important; visibility: hidden !important; }
#s-layout-dd.dd-on .dd-sunp { opacity: 1 !important; visibility: visible !important; transform: none !important; }
#s-layout-dd .dd-clock { display: flex; align-items: center; gap: calc(var(--pt) * 10); }
#s-layout-dd .dd-clock > b { font-family: var(--num, inherit); font-size: calc(var(--pt) * 34); line-height: 1; font-weight: 600; color: #c47a00; font-variant-numeric: tabular-nums; }
#s-layout-dd .dd-clock > span { display: flex; flex-direction: column; gap: calc(var(--pt) * 3); }
#s-layout-dd .dd-clock small { font-size: calc(var(--pt) * 8); color: #555; }
#s-layout-dd .dd-days { display: flex; gap: calc(var(--pt) * 3); font-style: normal; }
#s-layout-dd .dd-days button { border: 1px solid #d6cdf3; background: #fff; color: var(--purple); border-radius: 99px; padding: calc(var(--pt) * 1.2) calc(var(--pt) * 5); font: 500 calc(var(--pt) * 6.5) / 1.2 var(--body, inherit); cursor: pointer; }
#s-layout-dd .dd-days button.on { background: var(--purple); color: #fff; border-color: var(--purple); }
</style>''', "style")
SUN = r'''  // ---- 2 · the sun path (9 Nov, Ritika: "add sun path in site due diligence itself"): the site sun study (ACKO_FLOOR.sun: every half
  // hour, 07:00–18:30, the sun's bearing and height and the floor's sunlit patches, in the plate's units, plan mm = unit × 50 +
  // (8842, 12775)) on the plan. The day's arc round the floor by the sun's bearing (the building's grid turned ACKO_SITE.grid from
  // north), the sun on it with its light falling across the floor, the patches cross-fading; the day on the chips. All in plan mm,
  // over the plan's own view (so a zoom keeps it on the floor)
  const SUN = { t: [], day: 0, raf: 0, c: null };
  const GRID = (window.ACKO_SITE && window.ACKO_SITE.grid) || 11.52;
  function sunGeo() {
    if (SUN.c) return true; const F = window.ACKO_FLOOR; if (!F || !F.sun) return false;
    const xs = F.plate.map((q) => q[0] * 50 + 8842), ys = F.plate.map((q) => q[1] * 50 + 12775);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    SUN.c = [(x0 + x1) / 2, (y0 + y1) / 2]; SUN.rx = ((x1 - x0) / 2) * 0.9; SUN.ry = (y1 - y0) / 2 + 10500;   // the floor fills the page's width: the day's arc tucked inside its ends, swinging out past its long sides
    return true;
  }
  const onArc = (az, k = 1) => { const b = ((az - GRID) * Math.PI) / 180; return [SUN.c[0] + Math.sin(b) * SUN.rx * k, SUN.c[1] - Math.cos(b) * SUN.ry * k]; };
  const svgEl = (tag, at) => { const e = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const k in at) e.setAttribute(k, at[k]); return e; };
  function sunArc(sc) {
    const D = window.ACKO_FLOOR.sun[SUN.day], P = D.frames.map((f) => onArc(f.az));
    $(".dd-sun .arc", sc).setAttribute("d", "M" + P.map((q) => q.map((v) => v.toFixed(0)).join(" ")).join("L"));
    const tk = $(".dd-sun .ticks", sc); tk.innerHTML = "";
    D.frames.forEach((f) => {
      const h = +f.t.slice(0, 2); if (f.t.slice(3) !== "00" || ![7, 9, 12, 15, 18].includes(h)) return;
      const q = onArc(f.az), o = [Math.max(SUN.c[0] - SUN.rx * 1.02, Math.min(SUN.c[0] + SUN.rx * 1.02, q[0])), q[1] + (q[1] >= SUN.c[1] ? 2600 : -1900)];   // the label off the arc, away from the floor
      tk.append(svgEl("circle", { cx: q[0].toFixed(0), cy: q[1].toFixed(0), r: 700 }));
      const t = svgEl("text", { x: o[0].toFixed(0), y: o[1].toFixed(0), "text-anchor": "middle" }); t.textContent = h > 12 ? h - 12 + " pm" : h + (h === 12 ? " noon" : " am"); tk.append(t);
    });
  }
  const compass = (az) => ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][Math.round((((az % 360) + 360) % 360) / 45) % 8];
  function sunFrame(sc, i) {
    const D = window.ACKO_FLOOR.sun[SUN.day], f = D.frames[i]; if (!f) return;
    const on = $(".dd-sun .lit g.on", sc), off = on && on.classList.contains("a") ? $(".dd-sun .lit .b", sc) : $(".dd-sun .lit .a", sc);
    off.innerHTML = f.p.map((d) => `<path d="${d}"/>`).join(""); off.classList.add("on"); if (on) on.classList.remove("on");
    const q = onArc(f.az), up = Math.max(0, Math.min(1, f.alt / 60)), c = SUN.c, k = 0.55, e = [q[0] + (c[0] - q[0]) * k, q[1] + (c[1] - q[1]) * k];
    const sn = $(".dd-sun .sun", sc), hl = $(".dd-sun .halo", sc), ray = $(".dd-sun .ray", sc);
    sn.setAttribute("cx", q[0].toFixed(0)); sn.setAttribute("cy", q[1].toFixed(0)); sn.setAttribute("r", (900 + 500 * up).toFixed(0));
    hl.setAttribute("cx", q[0].toFixed(0)); hl.setAttribute("cy", q[1].toFixed(0)); hl.setAttribute("r", (2200 + 1600 * up).toFixed(0));
    ray.setAttribute("x1", q[0].toFixed(0)); ray.setAttribute("y1", q[1].toFixed(0)); ray.setAttribute("x2", e[0].toFixed(0)); ray.setAttribute("y2", e[1].toFixed(0)); ray.style.opacity = f.alt < 1 ? 0 : 0.75;
    $(".dd-clock > b", sc).textContent = f.t;
    $(".dd-clock small", sc).textContent = f.alt < 1 ? `${D.label} · the sun setting in the ${compass(f.az)}` : `${D.label} · the sun ${Math.round(f.alt)}° up, in the ${compass(f.az)}`;
  }
  function sunStop() { SUN.t.forEach(clearTimeout); SUN.t = []; }
  function sunPlay(sc, wait) {
    sunStop(); sunArc(sc);
    $$(".dd-days button", sc).forEach((b) => b.classList.toggle("on", +b.dataset.d === SUN.day));
    const fr = window.ACKO_FLOOR.sun[SUN.day].frames;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return sunFrame(sc, fr.length - 1);
    fr.forEach((_, i) => SUN.t.push(setTimeout(() => sunFrame(sc, i), (wait || 0) + i * 420)));
  }
  function sunFollow(sc) {                                // the drawing on the plan's current view (plan mm → page px)
    const v = plan.view, g = $(".dd-sun-g", sc);
    if (v) { const kk = Math.max(v[2] / 1920, v[3] / 1080), x0 = v[0] + v[2] / 2 - 960 * kk, y0 = v[1] + v[3] / 2 - 540 * kk;
      g.setAttribute("transform", `matrix(${(1 / kk).toFixed(6)} 0 0 ${(1 / kk).toFixed(6)} ${(-x0 / kk).toFixed(2)} ${(-y0 / kk).toFixed(2)})`); }
    if (sc.classList.contains("dd-on") && document.body.dataset.scene === sc.id) SUN.raf = requestAnimationFrame(() => sunFollow(sc));
  }
  function sunDD(sc, on) {
    if (!on || !sunGeo()) { if (sc.classList.contains("dd-on")) { sc.classList.remove("dd-on"); sunStop(); cancelAnimationFrame(SUN.raf); $$(".dd-sun .lit g", sc).forEach((g) => { g.classList.remove("on"); g.innerHTML = ""; }); } return; }
    if (sc.classList.contains("dd-on")) return;
    sc.classList.add("dd-on");
    $$(".dd-days button", sc).forEach((b) => (b.onclick = () => { b.blur(); SUN.day = +b.dataset.d; sunPlay(sc, 0); }));
    cancelAnimationFrame(SUN.raf); sunFollow(sc); sunPlay(sc, 700);
  }
'''
s = sub1(s, "  return self = {\n", SUN + "  return self = {\n", "sun fns")
s = sub1(s, "      const k = ORDER[n - 1], was = beat;", "      const k = ORDER[Math.min(n, ORDER.length) - 1], was = beat;", "order")
s = sub1(s, "      band(sc); plan.planHome(home(), was ? 700 : 0);        // the plan centred in what this beat's panel leaves it\n",
         "      band(sc); plan.planHome(home(), was ? 700 : 0);        // the plan centred in what this beat's panel leaves it\n"
         "      sunDD(sc, n === 2);                                // 2 · the sun path\n", "hook")
s = sub1(s, "      plan.planOff();\n", "      plan.planOff(); if (sc) sunDD(sc, false);\n", "leave")
wr(p, s, nl)
print("ok sundd")
