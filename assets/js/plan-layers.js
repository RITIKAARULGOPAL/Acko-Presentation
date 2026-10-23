/* PlanLayers: the layout's value-addition layers on the deck plan (the PlanHover mounted by app.js deckPlan()): the
   workstation types, biophilia (1 heat, 2 planting, 3 views to green), acoustics (four levels, sound rings) and a measure /
   area tool. Mounted once by the kit (plan.layers()); s-layout drives it. Data: window.PLAN_DXF (spaces, zones, types,
   egress, overlays) and window.AXO_DXF (the blocks behind the desks and chairs, the plants). Plan mm, y down.
   What shows is set on the plan host: data-pl = "spaces" | "nb" | "bio" | "ac" (none: off), data-pb = the biophilia step. */
(function () {
  "use strict";
  const rings = (d) => (d.match(/M[^Z]+/g) || []).map((r) => r.slice(1).split("L").map((q) => q.trim().split(/\s+/).map(Number)));
  const inPoly = (p, ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) { const [xi, yi] = ring[i], [xj, yj] = ring[j]; if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) c = !c; } return c; };
  const inside = (p, d) => rings(d).filter((r) => inPoly(p, r)).length % 2 === 1;
  const dpath = (pts, close) => "M" + pts.map((q) => q[0].toFixed(0) + " " + q[1].toFixed(0)).join("L") + (close ? "Z" : "");
  const place = (u, q) => [u[1] * q[0] + u[3] * q[1] + u[5], u[2] * q[0] + u[4] * q[1] + u[6]];
  const PPT = { T1: 73, T2: 14, T3: 36, T4: 525 };                       // the PPT legend's seats per type (slide 53)
  const CAT = { "Quick sprint": 2, "Collaboration huddle": 2, "Visitor hub": 2, "The Hatchery": 2, "Departmental room": 3, "Boardroom": 3, "Phone booth": 4, "Studio": 4 };
  const PEOPLE = { "Cafeteria": 178, "Reception": 18, "Coffee corner": 10, "Visitor hub": 4, "Collaboration huddle": 6, "Departmental room": 10, "Boardroom": 16, "The Hatchery": 8, "Pantry": 4, "Training room": 20 };

  function mount(o) {
    const { ph, host, P, A } = o, $ = (s) => host.querySelector(s), $$ = (s) => [...host.querySelectorAll(s)];
    const [vx, vy, vw, vh] = P.viewBox;
    const spaces = P.spaces.filter((s) => s.type !== "Not in contract");

    // ---- workstation types: each typed insert's block (desks and chairs), placed; seats = the block's chairs ----
    const desks = [], seats = [], types = [];
    const tyLayer = (P.types || []).map((T) => {
      let s = "", n = 0;
      for (const u of T.uses) {
        const sh = A.blocks[u[0]] || [], all = [];
        for (const [kind, ring] of sh) {
          const pts = ring.map((q) => place(u, q)); all.push(...pts); s += `<path d="${dpath(pts, true)}"/>`;
          if (kind === "chair") { n++; seats.push([pts.reduce((a, q) => a + q[0], 0) / pts.length, pts.reduce((a, q) => a + q[1], 0) / pts.length]); }
        }
        if (all.length) { const xs = all.map((p) => p[0]), ys = all.map((p) => p[1]); desks.push([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2, Math.max(1, sh.filter((q) => q[0] === "chair").length)]); }
      }
      types.push({ t: T.t, name: T.name, seats: n, ppt: PPT[T.t] });
      return `<g class="pl-ty" data-t="${T.t}">${s}</g>`;
    }).join("");

    // ---- the layers ----
    const CATF = { 1: "#efe9fd", 2: "#cdb9f5", 3: "#9a79f2", 4: "#5222d0" };
    const work = spaces.filter((s) => s.type === "Workhall");
    const acFill = (work.length ? work.map((s) => `<path data-c="1" d="${s.d}" style="fill:${CATF[1]}"/>`) : P.zones.map((z) => `<path data-c="1" d="${z.zone}" style="fill:${CATF[1]}"/>`)).join("") +
      spaces.filter((s) => CAT[s.type]).map((s) => `<path data-c="${CAT[s.type]}" d="${s.d}" style="fill:${CATF[CAT[s.type]]}"/>`).join("");
    ph.addLayer("pl-under", `<g class="pl-ac">${acFill}</g><g class="pl-heatg"><image class="pl-heat" x="${vx}" y="${vy}" preserveAspectRatio="none" opacity=".85"/><image class="pl-glow" x="${vx}" y="${vy}" preserveAspectRatio="none"/></g>`, { below: true });
    ph.addLayer("pl-types", tyLayer);
    ph.addLayer("pl-bio", `<g class="pl-views"></g><g class="pl-plants"></g>`);
    const waves = ph.addLayer("pl-waves", "");
    const measureSvg = ph.addLayer("pl-measure", "");

    // ---- biophilia: the heat field (where people breathe out), the planting softening it (conceptual), views to green ----
    const BIO = { built: false, raf: 0, show: null, stats: {} };
    function buildBio() {
      if (BIO.built) return; BIO.built = true;
      const S = 200, W = Math.ceil(vw / S), H = Math.ceil(vh / S);
      const c = document.createElement("canvas"); c.width = W; c.height = H; const g = c.getContext("2d"); g.globalCompositeOperation = "lighter";
      const blob = (x, y, r, a) => { const px = (x - vx) / S, py = (y - vy) / S, pr = r / S, gr = g.createRadialGradient(px, py, 0, px, py, pr);
        gr.addColorStop(0, `rgba(255,255,255,${Math.min(1, a)})`); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(px - pr, py - pr, pr * 2, pr * 2); };
      desks.forEach(([x, y, n]) => blob(x, y, 3600, 0.09 * n));
      const spread = (d, people, r = 3000) => { const R = rings(d), xs = R.flat().map((q) => q[0]), ys = R.flat().map((q) => q[1]), pts = [];
        for (let x = Math.min(...xs) + 1200; x < Math.max(...xs); x += 2400) for (let y = Math.min(...ys) + 1200; y < Math.max(...ys); y += 2400) if (inside([x, y], d)) pts.push([x, y]);
        if (!pts.length) pts.push([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2]);
        pts.forEach(([x, y]) => blob(x, y, r, (0.09 * people) / pts.length * 2.2)); };
      spaces.forEach((s) => { if (PEOPLE[s.type]) spread(s.d, PEOPLE[s.type]); else if (s.type === "Quick sprint") spread(s.d, (+(s.name.match(/(\d+)\s*PAX/i) || [0, 4])[1]) * 0.6); });
      (P.overlays.arrival || []).forEach((d) => spread(d, 30, 3600));
      const id = g.getImageData(0, 0, W, H); let mx = 0; for (let i = 3; i < id.data.length; i += 4) mx = Math.max(mx, id.data[i]);
      const raw = new Float32Array(W * H); for (let i = 0; i < W * H; i++) raw[i] = id.data[i * 4 + 3] / (mx || 1);
      const out = g.createImageData(W, H), ramp = [[0, [255, 236, 170]], [0.5, [251, 146, 60]], [1, [220, 38, 38]]];
      const heatImg = $(".pl-heat"), glowImg = $(".pl-glow");
      [heatImg, glowImg].forEach((im) => { im.setAttribute("width", W * S); im.setAttribute("height", H * S); });
      const paint = (f) => {
        for (let i = 0; i < W * H; i++) {
          const v = f[i], q = i * 4; if (v < 0.07) { out.data[q + 3] = 0; continue; }
          let k = 0; while (k < ramp.length - 2 && v > ramp[k + 1][0]) k++;
          const [a, ca] = ramp[k], [b, cb] = ramp[k + 1], t = Math.min(1, (v - a) / (b - a));
          out.data[q] = ca[0] + (cb[0] - ca[0]) * t; out.data[q + 1] = ca[1] + (cb[1] - ca[1]) * t; out.data[q + 2] = ca[2] + (cb[2] - ca[2]) * t; out.data[q + 3] = Math.min(190, 40 + v * 200);
        }
        g.putImageData(out, 0, 0); heatImg.setAttribute("href", c.toDataURL());
      };
      // the planting, busiest spots first; each plant softens the heat within 3 m (a Gaussian dip, up to 45%: conceptual)
      const at = (x, y) => raw[Math.min(H - 1, Math.max(0, Math.floor((y - vy) / S))) * W + Math.min(W - 1, Math.max(0, Math.floor((x - vx) / S)))];
      const order = A.plants.map((p, i) => [at(p[0], p[1]), i]).sort((a, b) => b[0] - a[0]).map((q) => A.plants[q[1]]);
      const dips = order.map(([x, y]) => { const ci = (x - vx) / S, cj = (y - vy) / S, R = 3000 / S, cells = [], f = [];
        for (let j = Math.max(0, Math.floor(cj - R)); j <= Math.min(H - 1, Math.ceil(cj + R)); j++) for (let i = Math.max(0, Math.floor(ci - R)); i <= Math.min(W - 1, Math.ceil(ci + R)); i++) {
          const d = Math.hypot(i + 0.5 - ci, j + 0.5 - cj) * S; if (d > 3000) continue; cells.push(j * W + i); f.push(1 - 0.45 * Math.exp(-(d * d) / (2 * 1500 * 1500))); }
        return [cells, f]; });
      // the busiest floor (cells at 40%+ of the peak) and, for each, the first plant (in planting order) within 3 m
      const hot = [], first = [], cz = 3000, grid = new Map();
      order.forEach((p, k) => { const key = Math.floor(p[0] / cz) + "," + Math.floor(p[1] / cz); (grid.get(key) || grid.set(key, []).get(key)).push([p, k]); });
      for (let i = 0; i < W * H; i++) if (raw[i] >= 0.4) {
        const x = vx + (i % W + 0.5) * S, y = vy + (Math.floor(i / W) + 0.5) * S, cx = Math.floor(x / cz), cy = Math.floor(y / cz); let best = Infinity;
        for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (const [q, k] of grid.get(cx + a + "," + (cy + b)) || []) if (k < best && Math.hypot(q[0] - x, q[1] - y) <= 3000) best = k;
        hot.push(i); first.push(best);
      }
      const covAt = (n) => (hot.length ? Math.round((100 * first.filter((k) => k < n).length) / hot.length) : 0);
      const gc = document.createElement("canvas"); gc.width = W; gc.height = H; const gg = gc.getContext("2d");
      const glow = (n) => { gg.clearRect(0, 0, W, H); for (let k = 0; k < n; k++) { const [x, y, r] = order[k], px = (x - vx) / S, py = (y - vy) / S, pr = (r + 2600) / S, gr = gg.createRadialGradient(px, py, 0, px, py, pr);
        gr.addColorStop(0, "rgba(63,143,58,.38)"); gr.addColorStop(1, "rgba(63,143,58,0)"); gg.fillStyle = gr; gg.fillRect(px - pr, py - pr, pr * 2, pr * 2); } glowImg.setAttribute("href", gc.toDataURL()); };
      $(".pl-plants").innerHTML = spaces.filter((s) => /Server|UPS/.test(s.type)).map((s) => `<path class="pl-svc" d="${s.d}"/>`).join("") +
        order.map(([x, y, r], k) => `<circle class="pl-pl" data-k="${k}" cx="${x}" cy="${y}" r="${Math.max(r, 380)}"/>`).join("");
      const plEls = $$(".pl-pl"), cool = new Float32Array(raw);
      let planted = 0;
      const plantTo = (n) => {
        if (n < planted) { cool.set(raw); planted = 0; }
        for (; planted < n; planted++) { const [cells, f] = dips[planted]; for (let q = 0; q < cells.length; q++) cool[cells[q]] *= f[q]; }
        plEls.forEach((e, k) => e.classList.toggle("in", k < n));
      };
      BIO.show = (b, animate, onCov) => {
        cancelAnimationFrame(BIO.raf);
        if (b === 1) { plantTo(0); paint(raw); glow(0); onCov && onCov(0); return; }
        if (b === 3 || !animate) { plantTo(order.length); paint(cool); glow(order.length); onCov && onCov(covAt(order.length)); return; }
        plantTo(0); paint(raw); glow(0);
        const t0 = performance.now(), DUR = 3200; let last = 0;
        const run = (now) => {
          const k = Math.min(1, (now - t0) / DUR), e = 1 - Math.pow(1 - k, 2), n = Math.round(order.length * e);
          if (now - last > 60 || k >= 1) { last = now; plantTo(n); paint(cool); glow(n); onCov && onCov(covAt(n)); }
          if (k < 1) BIO.raf = requestAnimationFrame(run);
        };
        BIO.raf = requestAnimationFrame(run);
      };
      // views to green: every seat to its nearest plant within 8 m, the sight line not through a room's outline
      const EB = 4000, edges = new Map();
      spaces.filter((s) => !/Workhall|Corridor|Entry|Lift lobby|Terrace|Collab$/.test(s.type)).forEach((sp) => rings(sp.d).forEach((r) => r.forEach((a, i) => {
        const b = r[(i + 1) % r.length], seg = [a, b];
        for (let x = Math.floor(Math.min(a[0], b[0]) / EB); x <= Math.floor(Math.max(a[0], b[0]) / EB); x++)
          for (let y = Math.floor(Math.min(a[1], b[1]) / EB); y <= Math.floor(Math.max(a[1], b[1]) / EB); y++) { const k = x + "," + y; (edges.get(k) || edges.set(k, []).get(k)).push(seg); }
      })));
      const cross = (p, q, a, b) => { const d = (u, v, w) => (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0]); const d1 = d(a, b, p), d2 = d(a, b, q), d3 = d(p, q, a), d4 = d(p, q, b); return (d1 > 0) !== (d2 > 0) && (d3 > 0) !== (d4 > 0); };
      const clear = (p, q) => { const seen = new Set();
        for (let x = Math.floor(Math.min(p[0], q[0]) / EB); x <= Math.floor(Math.max(p[0], q[0]) / EB); x++) for (let y = Math.floor(Math.min(p[1], q[1]) / EB); y <= Math.floor(Math.max(p[1], q[1]) / EB); y++)
          for (const e of edges.get(x + "," + y) || []) { if (seen.has(e)) continue; seen.add(e); if (cross(p, q, e[0], e[1])) return false; }
        return true; };
      const PB = 8000, pg = new Map(); A.plants.forEach((p) => { const k = Math.floor(p[0] / PB) + "," + Math.floor(p[1] / PB); (pg.get(k) || pg.set(k, []).get(k)).push(p); });
      let lines = "", dots = "", seen = 0; const dist = [];
      for (const s_ of seats) {
        const cx = Math.floor(s_[0] / PB), cy = Math.floor(s_[1] / PB), cand = [];
        for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) for (const q of pg.get(cx + a + "," + (cy + b)) || []) { const d = Math.hypot(q[0] - s_[0], q[1] - s_[1]); if (d <= 8000) cand.push([d, q]); }
        cand.sort((a, b) => a[0] - b[0]);
        const hit = cand.find(([, q]) => clear(s_, q));
        if (hit) { seen++; dist.push(hit[0]); lines += `<line class="pl-vw" x1="${s_[0].toFixed(0)}" y1="${s_[1].toFixed(0)}" x2="${hit[1][0]}" y2="${hit[1][1]}"/>`; }
        dots += `<circle class="pl-st${hit ? "" : " no"}" cx="${s_[0].toFixed(0)}" cy="${s_[1].toFixed(0)}" r="260"/>`;
      }
      $(".pl-views").innerHTML = lines + dots;
      dist.sort((a, b) => a - b);
      BIO.stats = { plants: A.plants.length, seats: seats.length, seen, views: seats.length ? Math.round((100 * seen) / seats.length) : 0,
        median: dist.length ? dist[Math.floor(dist.length / 2)] / 1000 : 0, cover: covAt(order.length) };
    }

    // ---- acoustics: sound rings, wide and lingering from the loud places, cut short in the treated rooms ----
    let wavesBuilt = false;
    function buildWaves() {
      if (wavesBuilt) return; wavesBuilt = true;
      const ring = (x, y, R, dur, n, cls, op) => Array.from({ length: n }, (_, i) => `<circle class="pl-wv ${cls}" cx="${x}" cy="${y}" r="0"><animate attributeName="r" values="0;${R}" dur="${dur}s" begin="${-(i * dur) / n}s" repeatCount="indefinite"/><animate attributeName="opacity" values="${op};0" dur="${dur}s" begin="${-(i * dur) / n}s" repeatCount="indefinite"/></circle>`).join("");
      const loud = [...spaces.filter((s) => /Cafeteria|Reception|Coffee/.test(s.type)).map((s) => [s.x, s.y]), ...P.zones.map((z) => [z.x, z.y])];
      const quiet = spaces.filter((s) => /Departmental|Boardroom|Studio/.test(s.type) || (s.type === "Phone booth" && +s.id.slice(1) % 6 === 0));
      waves.innerHTML = loud.map(([x, y]) => ring(x, y, 15000, 3.6, 3, "", 0.9)).join("") +
        quiet.map((s) => { const R = rings(s.d)[0], w = Math.max(...R.map((q) => q[0])) - Math.min(...R.map((q) => q[0])), h = Math.max(...R.map((q) => q[1])) - Math.min(...R.map((q) => q[1])); return ring(s.x, s.y, Math.min(w, h) * 0.42, 1.3, 2, "d", 0.6); }).join("");
    }

    // ---- measure / area: points snap to the spaces' corners; lengths in m, areas in m² ----
    const kOf = () => { const r = host.getBoundingClientRect(), v = ph.view; return Math.max(v[2] / r.width, v[3] / r.height); };
    const toPlan = (e) => { const r = host.getBoundingClientRect(), v = ph.view, k = kOf(); return [v[0] + v[2] / 2 - (r.width * k) / 2 + (e.clientX - r.left) * k, v[1] + v[3] / 2 - (r.height * k) / 2 + (e.clientY - r.top) * k, k]; };
    const VERTS = spaces.flatMap((s) => rings(s.d).flat());
    const MS = { mode: null, shapes: [], cur: null, live: null, down: null, read: null, lastView: "" };
    const snap = (p, k) => { let best = null, bd = 12 * k; for (const q of VERTS) { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < bd) { bd = d; best = q; } } return best ? [best[0], best[1], 1] : [p[0], p[1], 0]; };
    const len = (p) => p.slice(1).reduce((a, q, i) => a + Math.hypot(q[0] - p[i][0], q[1] - p[i][1]), 0);
    const area = (p) => Math.abs(p.reduce((a, q, i) => { const r = p[(i + 1) % p.length]; return a + q[0] * r[1] - r[0] * q[1]; }, 0)) / 2;
    const fm = (mm) => (mm / 1000).toFixed(2) + " m", fa = (mm2) => (mm2 / 1e6).toFixed(1) + " m²";
    function drawMeasure() {
      if (!MS.mode) { measureSvg.innerHTML = ""; MS.read && MS.read(""); return; }
      const k = kOf(), lab = (p, t) => `<text class="pl-m-lab" x="${p[0]}" y="${p[1]}" font-size="${11.5 * k}" stroke-width="${3.2 * k}">${t}</text>`;
      let s = ""; const all = MS.shapes.concat(MS.cur ? [{ mode: MS.cur.mode, pts: MS.cur.pts.concat(MS.live ? [[MS.live[0], MS.live[1]]] : []), live: true }] : []);
      for (const sh of all) {
        const p = sh.pts; if (!p.length) continue;
        if (sh.mode === "area" && p.length > 2) { s += `<path class="pl-m-area" d="${dpath(p, true)}"/>`; s += lab([p.reduce((a, q) => a + q[0], 0) / p.length, p.reduce((a, q) => a + q[1], 0) / p.length], fa(area(p))); }
        s += `<path class="pl-m-line${sh.live ? " live" : ""}" d="${dpath(p, sh.mode === "area" && !sh.live && p.length > 2)}"/>`;
        if (sh.mode === "dist") for (let i = 1; i < p.length; i++) { const a = p[i - 1], b = p[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L > 1) s += lab([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 8 * k], fm(L)); }
        p.forEach((q) => (s += `<circle class="pl-m-pt" cx="${q[0]}" cy="${q[1]}" r="${3 * k}"/>`));
      }
      if (MS.live && MS.live[2]) s += `<rect class="pl-m-snap" x="${MS.live[0] - 4.5 * k}" y="${MS.live[1] - 4.5 * k}" width="${9 * k}" height="${9 * k}"/>`;
      measureSvg.innerHTML = s;
      const c = MS.cur, p = c ? c.pts.concat(MS.live ? [[MS.live[0], MS.live[1]]] : []) : null, last = MS.shapes[MS.shapes.length - 1];
      MS.read && MS.read(c && p.length > 1 ? (c.mode === "dist" ? `${fm(len(p))} · click on, double-click to finish` : `${fa(area(p))} · perimeter ${fm(len(p.concat([p[0]])))}`)
        : last ? (last.mode === "dist" ? `${fm(len(last.pts))} measured · Esc clears` : `${fa(area(last.pts))} · perimeter ${fm(len(last.pts.concat([last.pts[0]])))} · Esc clears`)
        : MS.mode === "dist" ? "Click two points (snaps to room corners) · double-click to finish · Esc" : "Click the corners · click the first again to close · Esc");
    }
    function finish() { const c = MS.cur; MS.cur = null; MS.live = null; if (c) { c.pts = c.pts.filter((q, i) => !i || Math.hypot(q[0] - c.pts[i - 1][0], q[1] - c.pts[i - 1][1]) > 1); if (c.pts.length >= (c.mode === "area" ? 3 : 2)) MS.shapes.push(c); } drawMeasure(); }
    host.addEventListener("pointerdown", (e) => { MS.down = [e.clientX, e.clientY]; }, true);
    host.addEventListener("click", (e) => {
      if (!MS.mode) return;
      e.stopPropagation();                                   // no neighbourhood opens while measuring
      if (MS.down && Math.hypot(e.clientX - MS.down[0], e.clientY - MS.down[1]) > 3) return;
      const [x, y, k] = toPlan(e), s = snap([x, y], k);
      if (!MS.cur) MS.cur = { mode: MS.mode, pts: [] };
      if (MS.cur.mode === "area" && MS.cur.pts.length > 2 && Math.hypot(s[0] - MS.cur.pts[0][0], s[1] - MS.cur.pts[0][1]) < 12 * k) return finish();
      MS.cur.pts.push([s[0], s[1]]); drawMeasure();
    }, true);
    host.addEventListener("dblclick", (e) => { if (!MS.mode) return; e.stopPropagation(); e.preventDefault(); finish(); }, true);
    host.addEventListener("contextmenu", (e) => { if (!MS.mode) return; e.preventDefault(); finish(); });
    host.addEventListener("pointermove", (e) => { if (!MS.mode || !MS.cur) return; const [x, y, k] = toPlan(e); MS.live = snap([x, y], k); drawMeasure(); });
    // labels keep their screen size: redraw when the view changes (a zoom, a pan, a flight)
    const watch = () => { if (MS.mode && (MS.shapes.length || MS.cur)) { const v = ph.view.join(","); if (v !== MS.lastView) { MS.lastView = v; drawMeasure(); } } requestAnimationFrame(watch); };
    requestAnimationFrame(watch);

    const api = {
      types,
      desks, seats,
      set(layer) { host.dataset.pl = layer || ""; if (layer === "ac") buildWaves(); if (layer === "bio") buildBio(); if (layer !== "bio") cancelAnimationFrame(BIO.raf); },
      type(t) { ["T1", "T2", "T3", "T4"].forEach((x) => host.classList.toggle("pl-t-" + x, x === t)); },
      bio(step, animate, onCov) { buildBio(); host.dataset.pb = step || ""; BIO.show(step, animate, onCov); },
      get bioStats() { buildBio(); return BIO.stats; },
      acHi(c) { [1, 2, 3, 4].forEach((x) => host.classList.toggle("pl-ac-" + x, +c === x)); $$(".pl-ac path").forEach((p) => p.classList.toggle("hi", +p.dataset.c === +c)); },
      measure: {
        get mode() { return MS.mode; },
        set(m, onRead) { MS.mode = MS.mode === m ? null : m; MS.cur = null; MS.live = null; if (!MS.mode) MS.shapes = []; if (onRead) MS.read = onRead; host.classList.toggle("measuring", !!MS.mode); ph.clear(); drawMeasure(); return MS.mode; },
        esc() { if (!MS.mode) return false; if (MS.cur) { MS.cur = null; MS.live = null; } else if (MS.shapes.length) MS.shapes = []; else { MS.mode = null; host.classList.remove("measuring"); } drawMeasure(); return true; },
        off() { MS.mode = null; MS.shapes = []; MS.cur = null; MS.live = null; host.classList.remove("measuring"); drawMeasure(); },
      },
      off() { api.set(""); api.type(null); api.acHi(null); api.measure.off(); host.dataset.pb = ""; },
    };
    return api;
  }
  window.PlanLayers = { mount };
})();
