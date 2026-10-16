/* Plan2D — interactive SVG floor plan built from the DXF-derived data.
   Data space: millimetres, y up, origin = base-building shell lower-left.
   Geometry sits in a y-flipped group; labels/markers sit in an unflipped
   group so text reads correctly and keeps a constant screen size.
   Also hosts the "evolution" morph: brief tiles -> bubbles -> zones. */
(function () {
  const D = window.MX_DATA, TEX = window.MX_TEX, FURN = window.MX_FURN;
  const NS = "http://www.w3.org/2000/svg";
  /* the furniture as vector linework (data/plan-furn.js). Thousands of paths are too slow to repaint on every hover
     and zoom frame, so the plan shows them as a bitmap rendered from the vector for the current view (sharp at the
     screen's resolution) and renders it again once the view settles; between renders the bitmap just scales. */
  const FURN_SRC = {};
  const furnSvg = (opt, [x, y, w, h], pw, ph, mpp, c) => {
    const f = FURN[opt];
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${pw}" height="${ph}" viewBox="${x} ${y} ${w} ${h}" ` +
      `style="--fi:${c.fi};--ff:${c.ff};--fg:${c.fg};--mpp:${mpp};fill:none;stroke:var(--fi);stroke-width:calc(var(--mpp) * .75px);stroke-linecap:round;stroke-linejoin:round">` +
      `<defs>${f.defs}<clipPath id="fc"><polygon points="${f.clip}"/></clipPath></defs>` +
      `<g clip-path="url(#fc)"><g transform="${f.tr}">${f.body}</g></g></svg>`;
  };
  const H = D.opt1.size[1];
  const PRINT = /[?&]pdf(&|=|$)/.test(location.search) || document.documentElement.classList.contains("pdf");
  // the deck's zoning palette (slides 21–24) and the trust tiers in the same family
  const ZCOL = { soc: "#b5f4d9", secure: "#9ed9c0", arrive: "#fce7ae", board: "#a0bbeb", focus: "#e4aba5", meet: "#c9d3e0",
    collab: "#e9c8ff", cafe: "#f2c596", studio: "#e8b4c8", quiet: "#c6e8da", service: "#c8c8c8", core: "#919191" };
  const TCOL = ["#919191", "#f2c596", "#a0bbeb", "#b5f4d9"];
  const TIER = ["Building core", "Guest", "Team", "Secure"];
  const SHORT = { soc: "SOC", secure: "Secure", arrive: "Arrival", board: "Boardroom", focus: "Workhall", meet: "Meeting",
    collab: "Collab", cafe: "Café", studio: "Studio", quiet: "Booths", service: "Service" };
  const FLOOR_VIEW = [6200, 600, 78200, 34600];
  // the deck's zoning (slide 21): Arrival · Meet · Focus · Collaborate, plus the SOC, boardroom and café it also keys;
  // support rooms, and the building core, which is not in SKV's contract (Ritika, 11.10)
  const DZ = {
    arrival: { n: "Arrival", c: "#fce7ae", types: ["arrive"] },
    meet: { n: "Meet", c: "#c9d3e0", types: ["meet"] },
    focus: { n: "Focus", c: "#e4aba5", types: ["focus", "quiet"] },
    collab: { n: "Collaborate", c: "#e9c8ff", types: ["collab", "studio"] },
    soc: { n: "SOC", c: "#b5f4d9", types: ["soc"] },
    board: { n: "Boardroom", c: "#a0bbeb", types: ["board"] },
    cafe: { n: "Café", c: "#f2c596", types: ["cafe"] },
    support: { n: "Support", c: "#d9d9d9", types: ["secure", "service"] },
    nic: { n: "Not in contract · building core", c: "#a6a6a6", types: ["core"] },
  };
  const CIRC_COL = "#efefef";
  const DZ_OF = {}; for (const k in DZ) DZ[k].types.forEach((t) => (DZ_OF[t] = k));
  // the electrical room comes with the building: not in contract either
  const dzOf = (type, name) => (/electrical/i.test(name || "") ? "nic" : DZ_OF[type] || "nic");
  // a CAD space name -> programme type (as tools/import_plan_hover.py reads them); corridors are circulation
  const ROOM_TYPES = [[/corridor/i, "circ"], [/meeting|think tank/i, "meet"], [/phone booth/i, "quiet"], [/board/i, "board"], [/^cafe|cafeteria/i, "cafe"],
    [/reception|entrance/i, "arrive"], [/podcast/i, "studio"], [/agile|collaboration area|hotdesk/i, "focus"], [/breakout|collab|lounge/i, "collab"],
    [/server|ups|electrical/i, "secure"], [/service|store|prep|dine/i, "service"]];
  // rooms the 09.10 CAD leaves as "Space" that are meeting rooms by their furniture (Sathwick)
  const ROOM_NAMES = { opt1: { s22: "Meeting room · 4 PAX" } };
  for (const o in ROOM_NAMES) ((D.zones[o] || {}).hover || { rooms: [] }).rooms.forEach((r) => { if (ROOM_NAMES[o][r.id]) r.name = ROOM_NAMES[o][r.id]; });
  const roomType = (name) => { for (const [re, t] of ROOM_TYPES) if (re.test(name || "")) return t; return "core"; };
  // the brief, one bubble per space type
  const BRIEF = { focus: "Workhall · 235 seats", soc: "SOC · 80 seats", meet: "Meeting rooms · 16–17", collab: "Breakout", cafe: "Café · 52",
    arrive: "Arrival", board: "Boardroom · 30", secure: "Server · UPS", studio: "Podcast studio", service: "Store · service", quiet: "Booths · 6–7" };
  // adjacency (SKV's, the brief has none): next to · near · seen, never entered
  const ADJ = [["arrive", "board", "next"], ["arrive", "meet", "next"], ["arrive", "cafe", "near"], ["arrive", "soc", "seen"],
    ["soc", "secure", "next"], ["soc", "focus", "next"], ["soc", "collab", "near"], ["focus", "collab", "next"], ["focus", "quiet", "next"],
    ["focus", "meet", "near"], ["cafe", "studio", "near"], ["board", "service", "next"]];
  // where each bubble sits (mm, plan frame: the front door is top right); laid out so "seen" runs clear over the workhall
  const ADJ_AT = { focus: [38000, 10500], soc: [17000, 18000], secure: [7500, 10500], collab: [31000, 25000], quiet: [27500, -1400],
    meet: [59000, 15000], arrive: [61000, 27000], board: [69800, 28200], service: [76200, 31500], cafe: [71500, 8500], studio: [76500, 17500] };
  const EVO_VIEW = [5200, -15500, 79200, 35000];
  // the brief as squares under the floor, area-proportional, in this order (the layout slides start from them, Sathwick)
  const TILE_ORDER = ["focus", "soc", "meet", "collab", "cafe", "arrive", "board", "secure", "studio", "service", "quiet"];
  // the brief's bar is by zone, as the zoning's key (Sathwick, 13.10): booths in Focus, the studio in Collaborate, secure and
  // service rooms in Support; the core isn't in the brief
  const BAR_ORDER = ["focus", "soc", "meet", "collab", "cafe", "arrival", "board", "support"];
  const NPTS = 72;

  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  const flatD = (list) => {
    let s = "";
    for (const p of list) { s += "M" + p[0] + " " + p[1]; for (let i = 2; i < p.length; i += 2) s += "L" + p[i] + " " + p[i + 1]; }
    return s;
  };
  const ptsD = (pts, close) => "M" + pts.map((p) => Math.round(p[0]) + " " + Math.round(p[1])).join("L") + (close ? "Z" : "");
  const sy = (y) => H - y;

  /* ---------- geometry helpers for the morph ---------- */
  function polyArea(p) { let a = 0; for (let i = 0; i < p.length; i++) { const [x1, y1] = p[i], [x2, y2] = p[(i + 1) % p.length]; a += x1 * y2 - x2 * y1; } return a / 2; }
  function centroid(poly) {
    let a = 0, cx = 0, cy = 0;
    for (let i = 0; i < poly.length; i++) {
      const [x1, y1] = poly[i], [x2, y2] = poly[(i + 1) % poly.length];
      const f = x1 * y2 - x2 * y1; a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f;
    }
    a /= 2; return a ? [cx / (6 * a), cy / (6 * a)] : poly[0];
  }
  function resample(poly, n) {
    let p = poly.slice(); if (polyArea(p) < 0) p.reverse();          // counter-clockwise
    const loop = p.concat([p[0]]), seg = [];
    let L = 0;
    for (let i = 0; i < loop.length - 1; i++) { const d = Math.hypot(loop[i + 1][0] - loop[i][0], loop[i + 1][1] - loop[i][1]); seg.push(d); L += d; }
    const out = []; let i = 0, acc = 0;
    for (let k = 0; k < n; k++) {
      const t = (k / n) * L;
      while (i < seg.length - 1 && acc + seg[i] < t) { acc += seg[i]; i++; }
      const f = seg[i] ? (t - acc) / seg[i] : 0;
      out.push([loop[i][0] + (loop[i + 1][0] - loop[i][0]) * f, loop[i][1] + (loop[i + 1][1] - loop[i][1]) * f]);
    }
    const c = centroid(p); let best = 0, bd = 1e9;      // start nearest angle 0 so shapes don't twist
    out.forEach((q, j) => { const d = Math.abs(Math.atan2(q[1] - c[1], q[0] - c[0])); if (d < bd) { bd = d; best = j; } });
    return out.slice(best).concat(out.slice(0, best));
  }
  const circlePts = (c, r, n) => Array.from({ length: n }, (_, i) => { const a = (2 * Math.PI * i) / n; return [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)]; });
  // an ellipse (semi-axes a, b, turned by rot), counter-clockwise, starting nearest angle 0 like resample()
  const ellipsePts = (c, a, b, rot, n) => {
    const cs = Math.cos(rot), sn = Math.sin(rot);
    const out = Array.from({ length: n }, (_, i) => { const t = (2 * Math.PI * i) / n, x = a * Math.cos(t), y = b * Math.sin(t); return [c[0] + x * cs - y * sn, c[1] + x * sn + y * cs]; });
    let best = 0, bd = 1e9;
    out.forEach((q, j) => { const d = Math.abs(Math.atan2(q[1] - c[1], q[0] - c[0])); if (d < bd) { bd = d; best = j; } });
    return out.slice(best).concat(out.slice(0, best));
  };
  const lerpPts = (A, B, t) => A.map((p, i) => [p[0] + (B[i][0] - p[0]) * t, p[1] + (B[i][1] - p[1]) * t]);
  const ease = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const bboxOf = (p) => p.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [1e9, 1e9, -1e9, -1e9]);

  /* ---------- bubbles: one per space type, sized by area (the mean of both options), kept clear of each other ---------- */
  const typeArea = (t) => ["opt1", "opt2"].reduce((a, o) => a + D.zones[o].zones.filter((z) => z.type === t).reduce((s, z) => s + z.area, 0), 0) / 2;
  const ADJ_BUBBLES = (() => {
    const R = {}, P = {};
    for (const t in ADJ_AT) { R[t] = Math.max(2100, Math.sqrt(typeArea(t) / Math.PI) * 1000 * 0.82); P[t] = ADJ_AT[t].slice(); }
    const ks = Object.keys(P);
    for (let it = 0; it < 120; it++) for (let i = 0; i < ks.length; i++) for (let j = i + 1; j < ks.length; j++) {
      const a = ks[i], b = ks[j], dx = P[b][0] - P[a][0], dy = P[b][1] - P[a][1], d = Math.hypot(dx, dy) || 1, m = R[a] + R[b] + 1400;
      if (d < m) { const f = (m - d) / d / 2; P[a][0] -= dx * f; P[a][1] -= dy * f; P[b][0] += dx * f; P[b][1] += dy * f; }
    }
    return ks.reduce((o, t) => ((o[t] = { c: P[t], r: R[t] }), o), {});
  })();
  /* bubble zoning: the zones of a type that sit together (≤ 3 m apart) make one bubble, an ellipse along their long axis */
  function clusters(zs) {
    const n = zs.length, up = zs.map((_, i) => i), find = (i) => (up[i] === i ? i : (up[i] = find(up[i])));
    const bb = zs.map((z) => bboxOf(z.poly));
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
      const gx = Math.max(0, Math.max(bb[i][0], bb[j][0]) - Math.min(bb[i][2], bb[j][2])), gy = Math.max(0, Math.max(bb[i][1], bb[j][1]) - Math.min(bb[i][3], bb[j][3]));
      if (Math.hypot(gx, gy) < 3000) up[find(i)] = find(j);
    }
    const g = {}; zs.forEach((z, i) => (g[find(i)] = g[find(i)] || []).push(z));
    return Object.values(g).map((list) => {
      let A = 0, cx = 0, cy = 0; const pts = [];
      list.forEach((z) => { const c = centroid(z.poly); A += z.area; cx += c[0] * z.area; cy += c[1] * z.area; pts.push(...z.poly); });
      const c = [cx / A, cy / A];
      let sxx = 0, syy = 0, sxy = 0; pts.forEach(([x, y]) => { sxx += (x - c[0]) ** 2; syy += (y - c[1]) ** 2; sxy += (x - c[0]) * (y - c[1]); });
      const rot = 0.5 * Math.atan2(2 * sxy, sxx - syy), tr = sxx + syy, det = sxx * syy - sxy * sxy, l1 = tr / 2 + Math.sqrt(Math.max(0, tr * tr / 4 - det)), l2 = Math.max(1, tr - l1);
      const k = Math.min(3.4, Math.max(1, Math.sqrt(l1 / l2))), a = Math.sqrt((A * 1e6 * 1.05 / Math.PI) * k);
      return { zones: list, c, a, b: Math.max(1300, a / k), rot, area: A };
    });
  }

  class Plan2D {
    constructor(host, opts) {
      opts = opts || {};
      this.host = host;
      this.opt = opts.option || "opt1";
      this.L = Object.assign({ furn: true, walls: true, parts: true, zones: false, tiers: false, events: null, routes: [], cams: false,
        sig: false, labels: false, names: false, facades: false, north: false, socglass: false, opwalls: false, slab: true, hard: false, evo: false,
        sat: false, hover: false, circ: false, ctl: false, render: false, entry: false }, opts.layers || {});
      this.interactive = !!opts.interactive;
      this.onZone = opts.onZone || null;
      this.labelPx = opts.labelPx || 11;
      this.view = FLOOR_VIEW.slice();
      this.evoS = 2;
      host.classList.add("plan");
      if (this.interactive) host.classList.add("pannable");
      this.svg = el("svg", { preserveAspectRatio: "xMidYMid meet" }, host);
      this.tip = document.createElement("div"); this.tip.className = "plan-tip"; host.appendChild(this.tip);
      this.hvLabel = document.createElement("div"); this.hvLabel.className = "hv-label"; host.appendChild(this.hvLabel);
      // canvas controls: zoom in / out and back to the chapter's view; measure distances and areas (plan-measure.js)
      this.ctl = document.createElement("div"); this.ctl.className = "plan-ctl ui";
      this.ctl.innerHTML = '<button type="button" data-z="in" aria-label="Zoom in">+</button><button type="button" data-z="out" aria-label="Zoom out">−</button><button type="button" data-z="reset">Reset</button>' +
        '<button type="button" data-m="dist" title="Measure (M)">Measure</button><button type="button" data-m="area" title="Area (A)">Area</button><span class="m-read"></span>';
      this.ctl.addEventListener("click", (e) => {
        const b = e.target.closest("button"); if (!b || !(b.dataset.z || b.dataset.m)) return;   // other controls may join the bar
        e.stopPropagation(); b.blur();                          // give the arrow keys back to the deck
        if (b.dataset.m) this.measureMode(this.meas && this.meas.mode === b.dataset.m ? null : b.dataset.m);
        else if (b.dataset.z === "reset") this.resetView(); else this.zoomBy(b.dataset.z === "in" ? 0.7 : 1 / 0.7);
      });
      host.appendChild(this.ctl);
      this.home = FLOOR_VIEW.slice();
      this.build();
      this.applyView(this.view);
      if (this.interactive) this.bindPanZoom();
      new ResizeObserver(() => this.applyView(this.view)).observe(host);
    }

    /* ---------- build ---------- */
    build() {
      const svg = this.svg; svg.innerHTML = "";
      const d = D[this.opt], z = D.zones[this.opt];
      this.g = {};
      const defs = el("defs", {}, svg);
      // the visitor's walk ends in an arrowhead, as on the axo (used by the layout slides' CSS)
      const mk = el("marker", { id: "route-arrow-" + (this.host.id || ""), viewBox: "0 0 10 10", refX: 6, refY: 5, markerWidth: 4, markerHeight: 4, orient: "auto-start-reverse", markerUnits: "strokeWidth" }, defs);
      el("path", { d: "M0 0L10 5L0 10Z", fill: "#cc0000" }, mk);
      const pat = el("pattern", { id: "hatch-" + this.opt + (this.host.id || ""), width: 900, height: 900, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
      this.hatchLine = el("line", { x1: 0, y1: 0, x2: 0, y2: 900, class: "hard-hatch", "stroke-width": 140, opacity: .35 }, pat);
      this.paintHatch();
      // satellite still under the plan, registered on the floor plate (data/site.json: mm -> still px)
      if (D.site) {
        const U = D.site.under || D.site;                                          // the close (z20) still when there is one
        const [a, b, c, dd, e, f] = U.mm_to_px, det = a * dd - b * c;
        const ia = dd / det, ib = -b / det, ic = -c / det, id = a / det;          // inverse: still px -> mm
        const m = [ia, ib, ic, id, -(ia * e + ic * f), -(ib * e + id * f)].map((v) => +v.toFixed(7)).join(" ");
        const gs = (this.g.sat = el("g", { class: "g-sat", transform: `translate(0 ${H}) scale(1 -1) matrix(${m})` }, svg));
        el("image", { href: U.still, x: 0, y: 0, width: U.size[0], height: U.size[1], preserveAspectRatio: "none" }, gs);
      }
      const gf = (this.g.furn = el("g", { class: "g-furn" }, svg));
      const fv = !!(FURN && FURN[this.opt]);
      if (!fv) el("image", { href: TEX[this.opt], x: 0, y: 0, width: d.raster.w * 1000 / d.raster.px_per_m, height: d.raster.h * 1000 / d.raster.px_per_m, preserveAspectRatio: "none", class: "furn" }, gf);
      const flip = el("g", { transform: `translate(0 ${H}) scale(1 -1)` }, svg);
      const G = (name, parent) => (this.g[name] = el("g", { class: "g-" + name }, parent || flip));
      el("path", { class: "slab", d: ptsD(D.zones.annot.outline, true) }, G("slab"));
      const gt = G("tiers"), gz = G("zones"), gh = G("hard");
      this.zoneEls = [];
      z.zones.forEach((zz) => {
        const t = D.zones.types[zz.type];
        el("path", { class: "tier", d: ptsD(zz.poly, true), fill: TCOL[t.tier], stroke: TCOL[t.tier] }, gt);
        const p = el("path", { class: "zone", d: ptsD(zz.poly, true), fill: ZCOL[zz.type], stroke: ZCOL[zz.type], "data-type": zz.type }, gz);
        p.addEventListener("mousemove", (e) => this.showTip(e, zz));
        p.addEventListener("mouseleave", () => this.hideTip());
        p.addEventListener("click", () => this.onZone && this.onZone(zz));
        this.zoneEls.push(p);
        const hard = ["soc", "secure", "core", "board", "studio"].includes(zz.type);
        el("path", { d: ptsD(zz.poly, true), fill: hard ? "#04db7e" : `url(#${pat.id})`, "fill-opacity": hard ? .45 : 1, stroke: hard ? "#04db7e" : "currentColor", "stroke-opacity": .35, "stroke-width": 1, "vector-effect": "non-scaling-stroke" }, gh);
      });
      // the layout, coloured: every space filled to the same outline hover uses, the core (not in contract) included
      this.buildRender(G("render"), pat.id, z);
      // furniture above the colours (on the white pages the slab would veil it): only with the render
      const gf2 = G("furn2");
      // printing (index.html?pdf, the client PDF): the furniture as real linework, so it stays sharp when the PDF is zoomed
      // (Sathwick, 13.10); live, the bitmap below (thousands of paths are too slow to repaint)
      this.furnVec = fv && PRINT ? this.furnVector(gf2) : null;
      this.furnImg = fv && !PRINT ? el("image", { class: "furn furnv", preserveAspectRatio: "none", transform: `translate(0 ${H}) scale(1 -1)` }, gf2) : null;
      this.furnKey = "";
      if (!fv) el("image", { href: TEX[this.opt], x: 0, y: 0, width: d.raster.w * 1000 / d.raster.px_per_m, height: d.raster.h * 1000 / d.raster.px_per_m, preserveAspectRatio: "none", class: "furn", transform: `translate(0 ${H}) scale(1 -1)` }, gf2);
      const gevo = G("evo");
      this.evoGroup = gevo;
      const gw = G("walls");
      const ns = { "vector-effect": "non-scaling-stroke" };
      this.partEls = [
        el("path", Object.assign({ class: "w-door", d: flatD(d.vec.door) }, ns), gw),
        el("path", Object.assign({ class: "w-part", d: flatD(d.vec.partition) }, ns), gw),
        el("path", Object.assign({ class: "w-glass", d: flatD(d.vec.glass) }, ns), gw),
      ];
      this.shellEl = el("path", Object.assign({ class: "w-shell", d: flatD(d.vec.shell) }, ns), gw);
      el("path", { class: "w-fill", d: d.fills.map((p) => flatD([p]) + "Z").join("") }, gw);
      const go = G("opwalls");
      (z.walls || []).forEach((w) => el("path", Object.assign({ class: "opwall", d: ptsD(w) }, ns), go));
      el("path", Object.assign({ class: "socglass", d: ptsD(z.socGlass) }, ns), G("socglass"));
      const ge = G("events"); this.evEls = {};
      for (const k in z.events) this.evEls[k] = el("path", Object.assign({ class: "evt", d: (z.events[k].polys || [z.events[k].poly]).map((q) => ptsD(q, true)).join(""), style: "display:none" }, ns), ge);
      // circulation: the line the corridor will follow (derived from the 09.10 drawing)
      el("path", Object.assign({ class: "circ", d: (z.circulation || []).map((l) => ptsD(l)).join("") }, ns), G("circ"));
      const gr = G("routes"); this.routeEls = {};
      for (const k in z.routes) this.routeEls[k] = el("path", Object.assign({ class: "route " + k, d: ptsD(z.routes[k].pts), style: "display:none" }, ns), gr);
      const gfac = G("facades"); const o = D.zones.annot.outline;
      [[0, 1, "sw"], [1, 2, "w"], [4, 0, "se"]].forEach(([a, b, c]) => el("path", Object.assign({ class: "facade fac-" + c, d: ptsD([o[a], o[b]]) }, ns), gfac));
      this.gOver = G("over");
      // the main entrance: the deck's red triangle, pointing in, just off the door swing (as on 05 · The floor)
      const ent = D.zones.annot.labels.find((l) => l.kind === "entry");
      if (ent) { const [x, y] = ent.at; el("path", { class: "entry-tri", d: ptsD([[x - 900, y + 3300], [x + 900, y + 3300], [x, y + 1500]], true) }, G("entry")); }
      // a hovered room tints its floor, under the furniture; a hovered team lights its desks, above it
      const ghf = G("hoverfloor"); if (FURN && FURN[this.opt]) ghf.parentNode.insertBefore(ghf, gf2);
      this.buildHover(G("hover"), ghf);

      const top = el("g", { class: "g-top" }, svg);
      this.gNames = el("g", { class: "g-names" }, top); this.buildNames();
      this.gLabels = el("g", {}, top); this.gCams = el("g", {}, top); this.gSig = el("g", {}, top);
      this.gNorth = el("g", { class: "north" }, top); this.gNotes = el("g", { class: "plan-notes" }, top);
      this.gLinks = el("g", {}, top); this.gEvoLbl = el("g", {}, top);
      this.buildMarkers();
      this.evoBuilt = false;
      if (this.notes) this.setNotes(this.notes);
      if (this.links) this.setLinks(this.links);
      if (this.overlay) this.setOverlay(this.overlay);
      if (this.meas) this.meas.reset();                      // another option's walls: measurements start again
      this.update();
    }

    /* one fill per hover item (CAD room or team zone), in the deck zone colours; corridors pale, the core grey and hatched */
    buildRender(g, hatch, z) {
      this.renderEls = [];
      const hv = z.hover; if (!hv) return;
      const add = (d, dz, type, team, room) => {
        const p = el("path", { class: "rd", d, fill: this.dzc(dz), "data-dz": dz, "data-type": type, "data-team": team || "", "data-room": room || "" }, g);
        this.renderEls.push(p);
        if (dz === "nic") this.renderEls.push(el("path", { class: "rd rd-hatch", d, fill: `url(#${hatch})`, "data-dz": dz, "data-type": type }, g));
      };
      hv.rooms.filter((r) => roomType(r.name) === "circ").forEach((r) => add(r.d, "circ", "circ"));
      hv.teams.forEach((t) => add(t.zone, /SOC/i.test(t.name) ? "soc" : "focus", /SOC/i.test(t.name) ? "soc" : "focus", t.id));
      hv.rooms.forEach((r) => { const t = roomType(r.name); if (t !== "circ") add(r.d, dzOf(t, r.name), t, "", r.name); });
      // core spaces the CAD has no room for (risers): from the zones
      z.zones.filter((zz) => zz.type === "core").forEach((zz) => add(ptsD(zz.poly, true), "nic", "core"));
    }
    /* keep some zones in colour, fade the rest (null: all in colour) */
    renderFocus(keys) {
      const set = keys ? new Set([].concat(keys)) : null;
      (this.renderEls || []).forEach((p) => p.classList.toggle("dim", !!set && !set.has(p.dataset.dz) && !set.has(p.dataset.type) && !set.has(p.dataset.team)));
    }
    /* each team's workstations in its own colour (map: team id -> colour), or back to the zone colour (null) */
    /* the teams view: every space that is not a team in grey (the not-in-contract hatch stays) */
    renderMono(on) { if (this.g.render) this.g.render.classList.toggle("mono", !!on); }
    // (map keys "room:<name>" colour a CAD room, e.g. the shared agile desks)
    teamColours(map) {
      (this.renderEls || []).forEach((p) => {
        const t = p.dataset.team, r = p.dataset.room && "room:" + p.dataset.room;
        if (t) p.style.fill = (map && map[t]) || "";
        else if (r) p.style.fill = (map && map[r]) || "";
      });
    }
    /* a palette for this plan's zone colours (key -> colour, "hatch" for the core's hatch lines), or the deck's (null):
       the layout slides take their own (Sathwick, 13.10) */
    dzc(k) { return (this.pal && this.pal[k]) || (k === "circ" ? CIRC_COL : DZ[k].c); }
    paintHatch() {
      if (this.hatchLine) { const h = this.pal && this.pal.hatch; this.hatchLine.style.stroke = h || ""; this.hatchLine.style.opacity = h ? ".55" : ""; }
      this.host.classList.toggle("no-core-hatch", !!(this.pal && this.pal.hatch === "none"));   // the core plain, no hatch
    }
    setPalette(pal) {
      if (pal === this.pal) return;
      this.pal = pal; this.paintHatch();
      (this.renderEls || []).forEach((p) => { if (!p.classList.contains("rd-hatch")) p.setAttribute("fill", this.dzc(p.dataset.dz)); });
      (this.evoCore || []).forEach((p) => p.setAttribute("fill", this.dzc("nic")));
      (this.evoShapes || []).forEach((e) => { const k = e.path.dataset.dz; e.path.setAttribute("fill", this.dzc(k)); e.path.setAttribute("stroke", this.dzc(k)); });
    }

    buildMarkers() {
      const z = D.zones[this.opt];
      this.gLabels.innerHTML = "";
      const best = {};
      z.zones.forEach((zz) => { if (zz.type !== "core" && (!best[zz.type] || zz.area > best[zz.type].area)) best[zz.type] = zz; });
      this.labelEls = [];
      for (const t in best) {
        const c = centroid(best[t].poly);
        const tx = el("text", { class: "lbl big", x: c[0], y: sy(c[1]), "text-anchor": "middle", "dominant-baseline": "middle" }, this.gLabels);
        tx.textContent = SHORT[t] || t;
        this.labelEls.push(tx);
      }
      this.gCams.innerHTML = ""; this.camEls = {};
      for (const k in z.cameras) { const g = el("g", { class: "cam" }, this.gCams); this.camEls[k] = g; }
      this.gSig.innerHTML = ""; this.sigEls = {};
      let n = 1;
      for (const k in z.signature) {
        const p = z.signature[k]; const g = el("g", { class: "sig" }, this.gSig);
        el("circle", { class: "o", cx: p[0], cy: sy(p[1]), r: 900 }, g);
        el("circle", { class: "c", cx: p[0], cy: sy(p[1]), r: 520 }, g);
        const t = el("text", { x: p[0], y: sy(p[1]), "text-anchor": "middle", "dominant-baseline": "central", "font-family": "Poppins", "font-size": 600, fill: "#0e2a1f", "font-weight": 600 }, g);
        t.textContent = "0" + n++;
        this.sigEls[k] = g;
      }
      this.gNorth.innerHTML = "";
      // true north, from the satellite registration (a couple of degrees off the drawing's +x)
      const nx = 74500, ny = sy(36200), na = ((D.site && D.site.north_deg) || 0) * Math.PI / 180;
      el("circle", { cx: nx, cy: ny, r: 1100, fill: "none", stroke: "currentColor", class: "nc", "stroke-width": 1, "vector-effect": "non-scaling-stroke" }, this.gNorth);
      el("line", { x1: nx, y1: ny, x2: nx + 1100 * Math.cos(na), y2: ny - 1100 * Math.sin(na), "vector-effect": "non-scaling-stroke" }, this.gNorth);
      const nt = el("text", { x: nx + 1600 * Math.cos(na), y: ny - 1600 * Math.sin(na), "dominant-baseline": "central", "font-size": 900 }, this.gNorth); nt.textContent = "N";
    }

    /* ---------- hover: CAD rooms (name · area) and teams (seats light up) ---------- */
    /* the drawing's own texts (data/plan-names.js, tools/build_names.py): every name as the 09.10 DXF writes it, its lines,
       height, rotation and anchor, in drawing mm, so it scales with the plan as on paper (Sathwick, 13.10); the teams' labels
       only with the team colours on (setNameTeams) */
    buildNames() {
      const N = window.MX_NAMES && window.MX_NAMES[this.opt]; if (!N || !this.gNames) return;
      N.forEach((q) => {
        const g = el("g", { class: "nm" + (q.k ? " nm-team" : "") }, this.gNames);
        q.l.forEach(([s, x, y]) => {
          const t = el("text", Object.assign({ x, y: sy(y), "font-size": q.f, "text-anchor": q.a }, q.r ? { transform: `rotate(${-q.r} ${x} ${sy(y)})` } : {}), g);
          t.textContent = s;
        });
      });
      this.setNameTeams(this.nameTeams);
    }
    setNameTeams(on) { this.nameTeams = !!on; if (this.gNames) this.gNames.classList.toggle("teams", this.nameTeams); }
    buildHover(g, gRooms) {
      const hv = D.zones[this.opt].hover; this.hvAt = null;
      if (!hv) return;
      const rooms = new Map(hv.rooms.map((r) => [r.id, r])), teams = new Map(hv.teams.map((t) => [t.id, t]));
      hv.rooms.forEach((r) => el("path", { class: "hv-room", d: r.d, "data-id": r.id }, gRooms || g));
      hv.teams.forEach((t) => {
        const tg = el("g", { class: "hv-team", "data-id": t.id }, g);
        el("path", { class: "hv-zone", d: t.zone, "vector-effect": "non-scaling-stroke" }, tg);
        el("path", { class: "hv-seats", d: t.desks }, tg);
      });
      const n = (v) => Number(v).toLocaleString("en-IN", { maximumFractionDigits: 1 });
      [g, gRooms].filter(Boolean).forEach((gg) => gg.addEventListener("pointerover", (e) => {
        if (this.dragging) return;
        const tg = e.target.closest(".hv-team"), t = tg && teams.get(tg.dataset.id), r = !t && rooms.get(e.target.dataset.id);
        if (!t && !r) return;
        (tg || e.target).classList.add("on"); this.hvEl = tg || e.target; this.hvLabel.classList.remove("wrap");
        this.hvLabel.innerHTML = t
          ? `<b>${t.name}</b><span>${t.pax} PAX · ${t.seats} seats${t.hot ? ` (incl. ${t.hot} hot desk${t.hot > 1 ? "s" : ""})` : ""}</span>`
          : `<b>${r.name}</b><span>${Plan2D.sqft(r.m2)}</span>`;
        this.hvAt = (t || r).at; this.placeHover();
        if (this.onHover) this.onHover(t ? { kind: "team", item: t } : { kind: "room", item: r });
      }));
      [g, gRooms].filter(Boolean).forEach((gg) => gg.addEventListener("pointerout", (e) => {
        const tg = e.target.closest(".hv-team");
        (tg || e.target).classList.remove("on"); this.hvAt = null; this.hvEl = null; this.placeHover();
        if (this.onHover) this.onHover(null);
      }));
    }
    /* the label sits just outside the hovered item (above, else below, else beside), never on it;
       plan labels that fall on the hovered item step aside while it is hovered */
    placeHover() {
      const hidden = this.host.querySelectorAll(".hv-hide");
      hidden.forEach((n) => n.classList.remove("hv-hide"));
      if (!this.hvAt || !this.hvEl || !(this.L.hover || this.L.evo) || !this.vb) { this.hvLabel.classList.remove("on"); return; }
      const h = this.host.getBoundingClientRect(), r = this.hvEl.getBoundingClientRect();
      const b = { l: r.left - h.left, t: r.top - h.top, r: r.right - h.left, b: r.bottom - h.top };
      this.hvLabel.classList.add("on");
      const lw = this.hvLabel.offsetWidth, lh = this.hvLabel.offsetHeight, W = h.width, Hh = h.height, gap = 8, m = 6;
      const cx = (b.l + b.r) / 2, cy = (b.t + b.b) / 2, clampX = (x) => Math.max(m, Math.min(W - lw - m, x)), clampY = (y) => Math.max(m, Math.min(Hh - lh - m, y));
      let x, y;
      if (b.t - gap - lh >= m) { x = clampX(cx - lw / 2); y = b.t - gap - lh; }
      else if (b.b + gap + lh <= Hh - m) { x = clampX(cx - lw / 2); y = b.b + gap; }
      else if (b.r + gap + lw <= W - m) { x = b.r + gap; y = clampY(cy - lh / 2); }
      else { x = Math.max(m, b.l - gap - lw); y = clampY(cy - lh / 2); }
      this.hvLabel.style.left = x + "px"; this.hvLabel.style.top = y + "px";
      const pad = 2, hit = (q) => q.right > r.left + pad && q.left < r.right - pad && q.bottom > r.top + pad && q.top < r.bottom - pad;
      [this.gLabels, this.gNames, this.gNotes, this.gLinks, this.gSig].forEach((grp) => grp && Array.from(grp.children).forEach((n) => { if (hit(n.getBoundingClientRect())) n.classList.add("hv-hide"); }));
      this.host.querySelectorAll(".plan-callout").forEach((n) => { if (hit(n.getBoundingClientRect())) n.classList.add("hv-hide"); });
    }

    /* ---------- evolution morph: s = 0 adjacency bubbles (the brief, no floor) → 1 bubble zoning on the floor → 2 the exact spaces ---------- */
    buildEvo() {
      const z = D.zones[this.opt];
      this.evoGroup.innerHTML = ""; this.gEvoLbl.innerHTML = "";
      const AB = ADJ_BUBBLES;
      // the building core is there from the bubble zoning on: fixed, grey, not in contract
      // (with the electrical room: not in contract either, it isn't in the brief, so it never comes out of the bar)
      this.evoCore = z.zones.filter((zz) => zz.type === "core" || dzOf(zz.type, zz.name) === "nic").map((zz) => el("path", { class: "evo-core", d: ptsD(zz.poly, true), fill: this.dzc("nic") }, this.evoGroup));
      const gl = el("g", { class: "adj-links" }, this.evoGroup);
      const tiles = this.evoStart === "tiles" ? this.evoTiles(z) : null;   // start from the brief's squares, not the adjacency bubbles
      if (tiles) gl.style.display = "none";
      this.evoLinks = ADJ.map(([a, b, k]) => {
        const A = AB[a], B = AB[b], dx = B.c[0] - A.c[0], dy = B.c[1] - A.c[1], d = Math.hypot(dx, dy), ux = dx / d, uy = dy / d;
        const p = [[A.c[0] + ux * A.r, A.c[1] + uy * A.r], [B.c[0] - ux * B.r, B.c[1] - uy * B.r]];
        const g = el("g", { class: "adj adj-" + k, "data-a": a, "data-b": b }, gl);
        el("path", { class: "adj-line", d: ptsD(p), "vector-effect": "non-scaling-stroke" }, g);
        el("path", { class: "adj-hit", d: ptsD(p), "vector-effect": "non-scaling-stroke" }, g);
        g.addEventListener("pointerover", () => this.evoHover(g, "link", a + "|" + b));
        g.addEventListener("pointerout", () => this.evoHover(null));
        return g;
      });
      this.evoShapes = [];
      const types = {};
      z.zones.forEach((zz) => { if (zz.type !== "core" && dzOf(zz.type, zz.name) !== "nic") (types[zz.type] = types[zz.type] || []).push(zz); });
      const byZone = tiles && tiles._byZone; if (tiles) delete tiles._byZone;
      for (const t in types) {
        const T = tiles && !byZone && tiles[t] ? resample(tiles[t].rect, NPTS) : !tiles ? circlePts(AB[t].c, AB[t].r, NPTS) : null, dz = dzOf(t, "");
        clusters(types[t]).forEach((cl, ci) => {
          const B = ellipsePts(cl.c, cl.a, cl.b, cl.rot, NPTS);
          cl.zones.forEach((zz, zi) => {
            const zdz = dzOf(t, zz.name), P = resample(zz.poly, NPTS);
            const seg = tiles && tiles[zdz], T0 = T || (seg ? resample(seg.rect, NPTS) : P);   // by zone: from its segment
            const path = el("path", { class: "morph", fill: this.dzc(zdz), stroke: this.dzc(zdz), "data-type": t, "data-dz": zdz, "vector-effect": "non-scaling-stroke" }, this.evoGroup);
            // one shape per bubble while the bubbles are whole: the others appear as they split
            this.evoShapes.push({ T: T0, B, P, path, t, lead: ci === 0 && zi === 0 ? 2 : zi === 0 ? 1 : 0 });
            path.addEventListener("pointerover", () => this.evoHover(path, "type", t, zdz));
            path.addEventListener("pointerout", () => this.evoHover(null));
          });
        });
        if (tiles) continue;                                              // the squares' labels go under them (below)
        // brief labels sit beside each adjacency bubble, never on it: on the side its links leave free
        const { c, r } = AB[t], dirs = ADJ.filter((l) => l[0] === t || l[1] === t).map((l) => { const o = AB[l[0] === t ? l[1] : l[0]].c, d = Math.hypot(o[0] - c[0], o[1] - c[1]) || 1; return [(o[0] - c[0]) / d, (o[1] - c[1]) / d]; });
        const side = [[0, -1, 0], [0, 1, 0.15], [1, 0, 0.6], [-1, 0, 0.6]].map(([x, y, pen]) => ({ x, y, s: Math.max(-1, ...dirs.map((v) => v[0] * x + v[1] * y)) + pen })).sort((a, b) => a.s - b.s)[0];
        const L = el("text", side.y ? { class: "tile-lbl", x: c[0], y: sy(c[1] + side.y * r) + (side.y < 0 ? 450 : -450), "text-anchor": "middle", "dominant-baseline": side.y < 0 ? "hanging" : "auto", "data-dz": dz }
          : { class: "tile-lbl", x: c[0] + side.x * (r + 500), y: sy(c[1]), "text-anchor": side.x > 0 ? "start" : "end", "dominant-baseline": "middle", "data-dz": dz }, this.gEvoLbl);
        L.textContent = BRIEF[t] || SHORT[t];
      }
      if (tiles) {
        let small = 0;
        if (tiles._total) {
          const T0 = tiles._total, tx = el("text", { class: "tile-lbl tile-total", x: T0.x, y: sy(T0.y), "text-anchor": "start", "dominant-baseline": "auto" }, this.gEvoLbl);
          tx.textContent = T0.text; delete tiles._total;
        }
        for (const t in tiles) {
          const q = tiles[t];
          if (q.lbl) {                                                    // the bar: the label beside its segment, a leader if it moved
            const L = q.lbl, m = this.mmPerPx || 60;
            // a leader for every label: out of its segment, then (if the label moved) a bend to it
            el("path", { class: "tile-lbl tile-lead", d: `M${L.from[0]} ${sy(L.from[1])}L${L.from[0] + 10 * m} ${sy(L.from[1])}L${L.x - 12 * m} ${sy(L.y)}L${L.x - 5 * m} ${sy(L.y)}`, "vector-effect": "non-scaling-stroke" }, this.gEvoLbl);
            const tx = el("text", { class: "tile-lbl", x: L.x, y: sy(L.y), "text-anchor": "start", "dominant-baseline": "middle", "data-dz": byZone ? t : dzOf(t, "") }, this.gEvoLbl);
            tx.textContent = L.text;
            continue;
          }
          const stagger = q.s < 5200 ? (small++ % 2) * 2300 : 0;          // in a row, small squares alternate label rows
          const L = el("text", { class: "tile-lbl", x: q.cx, y: sy(q.rect[0][1]) + (q.gap || 900) + stagger, "text-anchor": "middle", "dominant-baseline": "hanging", "data-dz": dzOf(t, "") }, this.gEvoLbl);
          L.textContent = BRIEF[t] || SHORT[t];
        }
      }
      this.evoBuilt = true;
      this.renderEvo(this.evoS);
      if (this.vb) this.applyView(this.view);                         // size the new labels (text scales with the view)
    }
    evoTiles(z) {
      const types = {};
      z.zones.forEach((zz) => { if (zz.type !== "core") types[zz.type] = (types[zz.type] || 0) + zz.area; });
      if (this.tileBox) {
        const zs = {};
        z.zones.forEach((zz) => { const k = dzOf(zz.type, zz.name); if (zz.type !== "core" && k !== "nic") zs[k] = (zs[k] || 0) + zz.area; });
        return Object.assign(this.packTiles(zs, this.tileBox, BAR_ORDER, (k) => DZ[k].n), { _byZone: true });
      }
      const k = 0.56, gap = 1300, yTop = -2600, out = {}; let x = 7600;
      TILE_ORDER.forEach((t) => {
        if (!types[t]) return;
        const s = Math.sqrt(types[t]) * 1000 * k;
        out[t] = { rect: [[x, yTop - s], [x + s, yTop - s], [x + s, yTop], [x, yTop]], cx: x + s / 2, s };
        x += s + gap;
      });
      return out;
    }
    /* the brief as one bar down a box (mm, y up: the page's left column on the layout slides), split by each space's share
       of the area, its name and share beside it; labels that would collide step apart, with a leader line (Sathwick) */
    packTiles(types, [bx0, by0, bx1, by1], order, name) {
      const mpp = this.mmPerPx || 60, barW = Math.min(30 * mpp, (bx1 - bx0) * 0.2), gap = 1.5 * mpp, lh = 17 * mpp;
      const items = (order || TILE_ORDER).filter((t) => types[t]), tot = items.reduce((a, t) => a + types[t], 0), H = by1 - by0, out = {};
      let y = by1;
      items.forEach((t) => {
        const h = (H * types[t]) / tot, top = y, bot = y - h + Math.min(gap, h * 0.3);
        out[t] = { rect: [[bx0, bot], [bx0 + barW, bot], [bx0 + barW, top], [bx0, top]], cx: bx0 + barW / 2, s: barW, mid: (top + bot) / 2,
          pct: Math.round((types[t] / tot) * 100) };
        y -= h;
      });
      // labels at their segments' middles, pushed apart top-down, then back up if they ran off the bottom
      const ys = items.map((t) => out[t].mid);
      for (let i = 1; i < ys.length; i++) ys[i] = Math.min(ys[i], ys[i - 1] - lh);
      if (ys.length && ys[ys.length - 1] < by0 + lh / 2) { ys[ys.length - 1] = by0 + lh / 2; for (let i = ys.length - 2; i >= 0; i--) ys[i] = Math.max(ys[i], ys[i + 1] + lh); }
      const lx = bx0 + barW + 34 * mpp;                                 // room for the leaders between bar and labels
      items.forEach((t, i) => { out[t].lbl = { x: lx, y: ys[i], text: `${name ? name(t) : SHORT[t]} · ${Plan2D.sqft(types[t])} · ${out[t].pct || "<1"}%`, from: [bx0 + barW + 2 * mpp, out[t].mid] }; });
      out._total = { x: bx0, y: by1 + 10 * mpp, text: `Total · ${Plan2D.sqft(tot)}` };   // above the bar
      return out;
    }
    setTileBox(b) {
      const key = b ? b.map((v) => Math.round(v / 50)).join(",") : "";
      if (key === (this._tileKey || "")) return;
      this._tileKey = key; this.tileBox = b; if (this.evoStart === "tiles") { this.evoBuilt = false; if (this.L.evo) this.buildEvo(); }
    }
    /* where the morph starts: "adj" the adjacency bubbles (from brief to plan), "tiles" the brief's squares under the floor */
    setEvoStart(m) { if ((this.evoStart || "adj") === m) return; this.evoStart = m; this.evoBuilt = false; if (this.L.evo) this.buildEvo(); }
    renderEvo(s) {
      this.evoS = s;
      this.evoShapes.forEach((o) => {
        const direct = this.evoStart === "tiles";                        // the brief's bar goes straight to the zones (Sathwick)
        const pts = direct ? lerpPts(o.T, o.P, clamp01(s / 2)) : s <= 1 ? lerpPts(o.T, o.B, s) : lerpPts(o.B, o.P, s - 1);
        o.path.setAttribute("d", ptsD(pts, true));
        o.path.style.opacity = direct || o.lead === 2 ? 1 : o.lead === 1 ? clamp01(s * 4) : clamp01((s - 1) * 4);
      });
      this.evoLinks.forEach((l) => (l.style.opacity = clamp01(1 - s * 2.2)));
      this.gEvoLbl.querySelectorAll(".tile-lbl").forEach((t) => (t.style.opacity = clamp01(1 - s * 2.5)));
      this.evoCore.forEach((p) => (p.style.opacity = clamp01(s * 1.5)));
      this.evoGroup.classList.toggle("zoned", s > 1.5);
    }
    /* the adjacency bubbles' extent (for fitting the view on them) */
    evoBox(pad) {
      let b = [1e9, 1e9, -1e9, -1e9];
      for (const t in ADJ_BUBBLES) { const { c, r } = ADJ_BUBBLES[t]; b = [Math.min(b[0], c[0] - r - 1500), Math.min(b[1], c[1] - r - 2400), Math.max(b[2], c[0] + r + 1500), Math.max(b[3], c[1] + r + 2400)]; }
      pad = pad || 0; return [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad];
    }
    /* hover on a bubble or a link: the app says what to show (evoTip), the label sits beside it */
    evoHover(elx, kind, key, dz) {
      if (!elx || !this.evoTip || this.dragging) { this.hvAt = null; this.hvEl = null; this.placeHover(); return; }
      const html = this.evoTip(kind, key, dz, this.evoS);
      if (!html) return;
      this.hvLabel.innerHTML = html; this.hvLabel.classList.add("wrap"); this.hvEl = elx; this.hvAt = true; this.placeHover();
    }
    /* keep one deck zone's bubbles in colour, fade the rest (null: all) */
    evoFocus(dz) { (this.evoShapes || []).forEach((o) => o.path.classList.toggle("dim", !!dz && o.path.dataset.dz !== dz)); }
    setEvo(s, ms) {
      if (!this.evoBuilt) this.buildEvo();
      const from = this.evoS, t0 = performance.now(); ms = ms === undefined ? 1600 : ms;
      cancelAnimationFrame(this._evoRaf);
      if (!ms) return this.renderEvo(s);
      const step = (now) => { const k = Math.min(1, (now - t0) / ms); this.renderEvo(from + (s - from) * ease(k)); if (k < 1) this._evoRaf = requestAnimationFrame(step); };
      this._evoRaf = requestAnimationFrame(step);
    }
    drawIn() {   // walls draw themselves
      this.partEls.concat([this.shellEl]).forEach((p) => {
        p.classList.remove("drawin"); void p.getBoundingClientRect();
        p.style.setProperty("--len", 60000); p.classList.add("drawin");
      });
    }

    /* ---------- annotations ---------- */
    setNotes(list) {
      this.notes = list; this.gNotes.innerHTML = "";
      (list || []).forEach((n) => {
        const g = el("g", { class: "note-" + (n.kind || "x") }, this.gNotes);
        el("circle", { cx: n.at[0], cy: sy(n.at[1]), r: 260, fill: n.kind === "entry" ? "#cc0000" : n.kind === "view" ? "#04db7f" : n.kind === "facade" ? "#ffb547" : n.kind === "entryside" ? "#8fb7ff" : "currentColor" }, g);
        const t = el("text", { class: "lbl", x: n.at[0], y: sy(n.at[1]), "text-anchor": n.anchor || "middle" }, g);
        if (n.rot) t.setAttribute("transform", `rotate(${n.rot} ${n.at[0]} ${sy(n.at[1])})`);   // e.g. a vertical dimension's label, along its line
        t.textContent = n.text;
      });
      this.applyView(this.view);
    }
    setLinks(list) {   // clickable "enter this space" pins
      this.links = list; this.gLinks.innerHTML = "";
      (list || []).forEach((l) => {
        const g = el("g", { class: "link" }, this.gLinks);
        el("circle", { cx: l.at[0], cy: sy(l.at[1]), r: 500 }, g);
        const t = el("text", { class: "lbl", x: l.at[0], y: sy(l.at[1]), "text-anchor": "start" }, g); t.textContent = "↗ " + l.label;
        g.addEventListener("click", (e) => { e.stopPropagation(); l.onClick && l.onClick(); });
      });
      this.applyView(this.view);
    }
    /* generic overlay: [{kind:'poly'|'cone'|'line', pts|from,to,spread,len, cls, fill, stroke, label, labelAt}] */
    setOverlay(list) {
      this.overlay = list; this.gOver.innerHTML = "";
      (list || []).forEach((o) => {
        let pts = o.pts;
        if (o.kind === "cone") {
          const a = Math.atan2(o.to[1] - o.from[1], o.to[0] - o.from[0]), L = o.len || Math.hypot(o.to[0] - o.from[0], o.to[1] - o.from[1]), s = o.spread || 0.35;
          pts = [o.from, [o.from[0] + L * Math.cos(a - s), o.from[1] + L * Math.sin(a - s)], [o.from[0] + L * Math.cos(a + s), o.from[1] + L * Math.sin(a + s)]];
        }
        // rings: one shape with holes (even-odd), e.g. a mask with the highlighted spaces cut out
        const d = o.rings ? o.rings.map((r) => ptsD(r, true)).join("") : ptsD(pts, o.kind !== "line");
        el("path", { d, class: o.cls || "", fill: o.fill || "none", stroke: o.stroke || "none", "stroke-width": o.sw || 2, "fill-opacity": o.fo === undefined ? .35 : o.fo, "fill-rule": "evenodd", "vector-effect": "non-scaling-stroke" }, this.gOver);
      });
    }

    /* ---------- layers ---------- */
    setLayers(patch) { Object.assign(this.L, patch); this.update(); }
    setOption(opt) { if (opt === this.opt) return; this.opt = opt; this.build(); this.applyView(this.view); }
    /* the furniture as vector, in the plan itself (print): FURN's blocks and body, under the floor's flip, clipped to the plate */
    furnVector(parent) {
      const f = FURN[this.opt], cs = getComputedStyle(this.host), id = `fc-${this.opt}-${this.host.id || "p"}`;
      const c = { fi: cs.getPropertyValue("--plan-furn-ink").trim() || "#5a5a5a", ff: cs.getPropertyValue("--plan-furn-fill").trim() || "#fff", fg: cs.getPropertyValue("--plan-furn-green").trim() || "#7c9a6e" };
      this.svg.querySelector("defs").insertAdjacentHTML("beforeend", `<clipPath id="${id}"><polygon points="${f.clip}"/></clipPath>`);
      // furnv: no invert filter (the old raster texture's), as the bitmap
      const g = el("g", { class: "furn furnv furnvec", transform: `translate(0 ${H}) scale(1 -1)`, "clip-path": `url(#${id})`,
        style: `--fi:${c.fi};--ff:${c.ff};--fg:${c.fg};--mpp:60;fill:none;stroke:var(--fi);stroke-width:calc(var(--mpp) * .75px);stroke-linecap:round;stroke-linejoin:round` }, parent);
      // the blocks' own definitions inside the group, so they take its colours
      if (!this.svg.querySelector(`[id^="fb-${this.opt}-"]`)) el("defs", {}, g).innerHTML = f.defs;
      el("g", { transform: f.tr }, g).innerHTML = f.body;
      return g;
    }
    /* the furniture bitmap: rendered for the view plus a margin, at the screen's resolution, once the view settles */
    furnLater(ms) {
      if (!this.furnImg) return;
      clearTimeout(this.furnT);
      this.furnT = setTimeout(() => this.furnRender(), ms === undefined ? 140 : ms);
    }
    furnRender() {
      const img = this.furnImg, vb = this.vb;
      if (!img || !vb || !this.L.furn || this.g.furn2.style.display === "none") return;
      const cs = getComputedStyle(this.host), c = { fi: cs.getPropertyValue("--plan-furn-ink").trim() || "#5a5a5a",
        ff: cs.getPropertyValue("--plan-furn-fill").trim() || "#fff", fg: cs.getPropertyValue("--plan-furn-green").trim() || "#7c9a6e" };
      const [x, y, w, h, W, Hh] = vb, dpr = Math.min(window.devicePixelRatio || 1, 2);
      const m = 0.35, rect = [x - w * m, y - h * m, w * (1 + 2 * m), h * (1 + 2 * m)];
      let k = (W * (1 + 2 * m) * dpr) / rect[2];                       // output px per mm
      k = Math.min(k, 7000 / rect[2], 7000 / rect[3]);                  // keep the canvas within limits
      const pw = Math.round(rect[2] * k), ph = Math.round(rect[3] * k), mpp = (1 / k) * dpr;
      const key = [this.opt, rect.map((v) => Math.round(v)).join(","), pw, ph, c.fi, c.ff].join("|");
      if (key === this.furnKey) return;
      this.furnKey = key;
      const ticket = (this.furnTicket = (this.furnTicket || 0) + 1);
      const src = new Image();
      src.onload = () => {
        if (ticket !== this.furnTicket) return;
        const cv = document.createElement("canvas"); cv.width = pw; cv.height = ph;
        cv.getContext("2d").drawImage(src, 0, 0);
        URL.revokeObjectURL(src.src);
        cv.toBlob((b) => {
          if (ticket !== this.furnTicket || !b) return;
          const old = this.furnUrl; this.furnUrl = URL.createObjectURL(b);
          img.setAttribute("href", this.furnUrl);
          img.setAttribute("x", rect[0]); img.setAttribute("y", rect[1]); img.setAttribute("width", rect[2]); img.setAttribute("height", rect[3]);
          if (old) setTimeout(() => URL.revokeObjectURL(old), 500);
        });
      };
      src.src = URL.createObjectURL(new Blob([furnSvg(this.opt, rect, pw, ph, mpp.toFixed(3), c)], { type: "image/svg+xml" }));
    }
    update() {
      const L = this.L, show = (g, on) => g && (g.style.display = on ? "" : "none");
      // vector furniture always sits above the floor colours (furn2); the texture only did with the render
      show(this.g.furn, L.furn && !L.render && !FURN); show(this.g.furn2, L.furn && (L.render || !!FURN)); show(this.g.render, L.render); show(this.g.entry, L.entry);
      show(this.g.walls, L.walls); show(this.g.zones, L.zones && !L.evo); show(this.g.tiers, L.tiers);
      show(this.g.slab, L.slab); show(this.g.facades, L.facades); show(this.g.socglass, L.socglass); show(this.g.opwalls, L.opwalls);
      show(this.g.hard, L.hard); show(this.g.evo, L.evo); show(this.gEvoLbl, L.evo);
      show(this.g.sat, L.sat); show(this.g.hover, L.hover && !L.evo); show(this.g.hoverfloor, L.hover && !L.evo); if (!L.hover) { this.hvAt = null; this.hvEl = null; this.placeHover(); }
      show(this.g.circ, L.circ); this.ctl.classList.toggle("on", !!L.ctl);
      if (this.meas) { if (!L.ctl) this.meas.setMode(null); else this.meas.render(); }   // the snap follows the lines shown
      if (L.evo && !this.evoBuilt) this.buildEvo();
      this.partEls.forEach((p) => show(p, L.parts !== false));
      show(this.gLabels, L.labels && !L.evo); show(this.gNames, L.names); show(this.gCams, L.cams); show(this.gSig, L.sig); show(this.gNorth, L.north);
      for (const k in this.evEls) this.evEls[k].style.display = L.events === k ? "" : "none";
      for (const k in this.routeEls) this.routeEls[k].style.display = L.routes.includes(k) ? "" : "none";
      this.drawCams();
      this.furnLater(0);
    }
    highlight(types) {
      const set = types ? new Set([].concat(types)) : null;
      this.zoneEls.forEach((p) => { p.classList.toggle("dim", !!set && !set.has(p.dataset.type)); p.classList.toggle("hi", !!set && set.has(p.dataset.type)); });
    }
    focusSig(k) { for (const s in this.sigEls) this.sigEls[s].style.opacity = !k || s === k ? 1 : .3; }

    /* ---------- view ---------- */
    applyView(v) {
      this.view = v;
      const r = this.host.getBoundingClientRect();
      const W = Math.max(1, r.width), Hh = Math.max(1, r.height);
      let [x0, y0, x1, y1] = v;
      let w = x1 - x0, h = y1 - y0;
      const ar = W / Hh;
      if (w / h > ar) { const nh = w / ar; y0 -= (nh - h) / 2; h = nh; } else { const nw = h * ar; x0 -= (nw - w) / 2; w = nw; }
      this.vb = [x0, sy(y0 + h), w, h, W, Hh];
      this.svg.setAttribute("viewBox", `${x0} ${sy(y0 + h)} ${w} ${h}`);
      this.mmPerPx = w / W;
      if (this.furnVec) this.furnVec.style.setProperty("--mpp", this.mmPerPx.toFixed(3));
      this.furnLater();
      const fs = this.labelPx * this.mmPerPx;
      this.labelEls && this.labelEls.forEach((t) => t.setAttribute("font-size", fs * 1.25));
      this.gEvoLbl && this.gEvoLbl.querySelectorAll("text").forEach((t) => t.setAttribute("font-size", t.classList.contains("big") ? fs * 1.2 : fs * 1.15));

      this.gNotes && this.gNotes.querySelectorAll("g").forEach((g) => {
        const t = g.querySelector("text"), c = g.querySelector("circle");
        t.setAttribute("font-size", fs); t.setAttribute("dy", -fs * 0.9); c.setAttribute("r", 3.5 * this.mmPerPx);
      });
      this.gLinks && this.gLinks.querySelectorAll("g").forEach((g) => {
        const t = g.querySelector("text"), c = g.querySelector("circle");
        t.setAttribute("font-size", fs * 1.05); t.setAttribute("dx", 9 * this.mmPerPx); t.setAttribute("dy", fs * 0.35); c.setAttribute("r", 6 * this.mmPerPx);
      });
      this.drawCams();
      this.placeHover();
      if (this.meas) this.meas.render();
      if (this.onView) this.onView(v);
    }
    /* a chapter's view: also what Reset returns to */
    fit(bbox, ms) { this.home = (bbox || FLOOR_VIEW).slice(); this.tweenView(this.home, ms); }
    resetView() { this.tweenView(this.home || FLOOR_VIEW, 600); }
    /* zooming out stops at the chapter's view (what each step opens on and Reset returns to): past it, back to it (Sathwick) */
    scaleOf([x0, y0, x1, y1]) { const r = this.host.getBoundingClientRect(); return Math.max((x1 - x0) / Math.max(1, r.width), (y1 - y0) / Math.max(1, r.height)); }
    pastHome(v) { const h = this.home || FLOOR_VIEW; return this.scaleOf(v) > this.scaleOf(h) * 1.001; }
    zoomBy(f) {
      const [x0, y0, x1, y1] = this.view, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      const w = Math.min(120000, Math.max(5000, (x1 - x0) * f)), h = (y1 - y0) * (w / (x1 - x0));
      const v = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
      this.tweenView(f > 1 && this.pastHome(v) ? (this.home || FLOOR_VIEW) : v, 350);
    }
    tweenView(target, ms) {
      const from = this.view.slice(), to = target.slice();
      cancelAnimationFrame(this._raf);
      if (!ms) return this.applyView(to);
      const t0 = performance.now();
      const step = (now) => {
        const k = Math.max(0, Math.min(1, (now - t0) / ms)), e = 1 - Math.pow(1 - k, 3);   // rAF time can trail the start on a slow frame
        this.applyView(from.map((f, i) => f + (to[i] - f) * e));
        if (k < 1) this._raf = requestAnimationFrame(step);
      };
      this._raf = requestAnimationFrame(step);
    }
    /* px inside the host -> data mm (y up) */
    fromScreen(px, py) {
      const [vx, vy, w, h, W, Hh] = this.vb;
      return [vx + (px / W) * w, sy(vy + (py / Hh) * h)];
    }
    /* data mm -> px inside the host */
    toScreen(p) {
      const [vx, vy, w, h, W, Hh] = this.vb;
      return [((p[0] - vx) / w) * W, ((sy(p[1]) - vy) / h) * Hh];
    }
    drawCams() {
      if (!this.camEls || !this.L.cams) return;
      const z = D.zones[this.opt], s = this.mmPerPx || 60;
      for (const k in this.camEls) {
        const c = z.cameras[k], g = this.camEls[k]; g.innerHTML = "";
        const x = c.at[0], y = sy(c.at[1]); const a = Math.atan2(-c.dir[1], c.dir[0]);
        const R = 60 * s, sp = 0.45;
        g.style.opacity = !this.activeCam || this.activeCam === k ? 1 : .2;
        el("path", { d: `M${x} ${y}L${x + R * Math.cos(a - sp)} ${y + R * Math.sin(a - sp)}A${R} ${R} 0 0 1 ${x + R * Math.cos(a + sp)} ${y + R * Math.sin(a + sp)}Z` }, g);
        el("circle", { cx: x, cy: y, r: 6 * s }, g);
      }
    }
    setCam(k) { this.activeCam = k; this.drawCams(); }

    bindPanZoom() {
      const svg = this.svg; let drag = null;
      svg.addEventListener("wheel", (e) => {
        e.preventDefault();
        const r = svg.getBoundingClientRect(); const [x0, y0, x1, y1] = this.view;
        const fx = (e.clientX - r.left) / r.width, fy = 1 - (e.clientY - r.top) / r.height;
        const k = Math.exp(e.deltaY * 0.0012);
        const cx = x0 + (x1 - x0) * fx, cy = y0 + (y1 - y0) * fy;
        const w = Math.min(120000, Math.max(5000, (x1 - x0) * k)), h = (y1 - y0) * (w / (x1 - x0));
        const v = [cx - w * fx, cy - h * fy, cx - w * fx + w, cy - h * fy + h];
        if (k > 1 && this.pastHome(v)) { if (!this._homing) { this._homing = true; this.tweenView(this.home || FLOOR_VIEW, 250); setTimeout(() => (this._homing = false), 260); } return; }
        this.applyView(v);
      }, { passive: false });
      svg.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, y: e.clientY, v: this.view.slice() }; svg.setPointerCapture(e.pointerId); });
      svg.addEventListener("pointermove", (e) => {
        if (!drag) return;
        if (!this.dragging && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 3) return;   // a click, not a drag yet
        this.dragging = true; this.hvAt = null;
        const s = this.mmPerPx; const dx = (e.clientX - drag.x) * s, dy = (e.clientY - drag.y) * s;
        this.applyView([drag.v[0] - dx, drag.v[1] + dy, drag.v[2] - dx, drag.v[3] + dy]);
      });
      svg.addEventListener("pointerup", () => { drag = null; this.dragging = false; });
      svg.addEventListener("dblclick", () => { if (!this.measuring()) this.resetView(); });
    }
    /* measure: "dist" | "area" | null (off clears); Esc finishes, then clears, then stops */
    measureMode(m) {
      if (!this.meas && m && Plan2D.Measure) this.meas = new Plan2D.Measure(this);
      return this.meas ? this.meas.setMode(m) : false;
    }
    measuring() { return !!(this.meas && this.meas.mode); }
    measureEsc() { return !!(this.meas && this.meas.esc()); }

    showTip(e, zz) {
      const t = D.zones.types[zz.type];
      this.tip.innerHTML = `<div class="h"><span>${zz.type.toUpperCase()}</span><span>${TIER[t.tier]} tier</span></div><b>${t.label}</b>≈ ${Plan2D.sqft(zz.area)}`;
      const r = this.host.getBoundingClientRect();
      this.tip.style.left = Math.min(r.width - 290, e.clientX - r.left + 16) + "px";
      this.tip.style.top = (e.clientY - r.top + 16) + "px";
      this.tip.classList.add("on");
    }
    hideTip() { this.tip.classList.remove("on"); }
  }

  Plan2D.FLOOR_VIEW = FLOOR_VIEW; Plan2D.EVO_VIEW = EVO_VIEW;
  Plan2D.ZCOL = ZCOL; Plan2D.TCOL = TCOL; Plan2D.TIER = TIER; Plan2D.SHORT = SHORT;
  /* areas, everywhere in the deck, in square feet (Sathwick): 1 m² = 10.7639 sq ft; to 0.1 below 10, to 1 below
     1,000, to 10 above */
  const SQFT = 10.7639;
  Plan2D.sqft = (m2, unit = true) => {
    const v = m2 * SQFT, r = v < 10 ? Math.round(v * 10) / 10 : v < 1000 ? Math.round(v) : Math.round(v / 10) * 10;
    return r.toLocaleString("en-IN", { maximumFractionDigits: 1 }) + (unit ? " sq ft" : "");
  };
  Plan2D.DZ = DZ; Plan2D.dzOf = dzOf; Plan2D.roomType = roomType; Plan2D.CIRC_COL = CIRC_COL; Plan2D.ADJ = ADJ; Plan2D.BRIEF = BRIEF;
  Plan2D.centroid = centroid;
  Plan2D.bboxOf = (polys, pad) => {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    polys.forEach((p) => p.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }));
    pad = pad || 0; return [x0 - pad, y0 - pad, x1 + pad, y1 + pad];
  };
  window.Plan2D = Plan2D;
})();
