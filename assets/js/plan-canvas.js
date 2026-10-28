/* plan-canvas.js - the floor plan's own drawing (data/plan-base.js, window.PLAN_BASE) as vector on a <canvas>, at every zoom.
   The data is plan_vector.py's instanced export: each block definition once, placements by reference. It is walked once,
   placed into the deck's plan frame (x - origin[0], origin[1] - y, mm) and kept as Path2D batches in 10 m tiles; a draw
   strokes what is in view. Colours and line weights are the deck's plan theme (plan-hover.css, --ph-*), by what a layer
   draws: walls, glass, doors, furniture, plants, shading, annotation, the rest; fills light, pattern lines faint.

   PlanCanvas.mount(stage, data, { before }) -> { el, draw([x, y, w, h]) }
     stage   the element the canvas fills (PlanHover's .ph-stage); before: the child it goes in front of
     draw    the viewBox in plan mm, fitted as the SVGs above it fit theirs (xMidYMid meet) */
(function () {
  const TILE = 10000, FINE = 250;
  const GLASS = /GLASS|GLSS|GLS|GLAZ|_IN_GL\b/i, GREEN = /PLANT|PLNT|GRASS|LANDSCAP|TREE|SHRUB|VEG/i;
  const DOOR = /DOOR|_DOR_|DOR-/i, WALL = /WALL|PART|PRTN|COLS|S-COL|CORE|STRU/i;
  const FURN = /FURN|\bFUR\b|_FUR_|CHAIR|TABLE|SEAT|SOFA|STORAGE|TV UNIT|^AC_WS_|EQPM|MLWK|FIXT|PLBG|ELEV/i;
  const SHADE = /SHADE|PATT|HATCH/i, ANNO = /ANNO|TEXT|DIM|TAG|IDEN/i;
  // class -> [colour variable, line width in CSS px]
  const STROKE = { wall: ["--ph-wall", 1.4], glass: ["--ph-glass", 1], door: ["--ph-door", 0.7], furn: ["--ph-furniture", 0.6],
                   green: ["--ph-plant", 0.5], shade: ["--ph-shade", 0.4], anno: ["--ph-door", 0.5], base: ["--ph-line", 0.9] };
  const cls = (layer, group, veg) => veg || group === "vegetation" || GREEN.test(layer) ? "green" : GLASS.test(layer) ? "glass"
    : DOOR.test(layer) ? "door" : WALL.test(layer) ? "wall" : FURN.test(layer) ? "furn" : SHADE.test(layer) ? "shade"
    : ANNO.test(layer) ? "anno" : "base";
  const FONT = (name) => /gothic/i.test(name) ? `"Century Gothic", "Futura", "Avenir", sans-serif`
    : /romans|txt|standard/i.test(name) ? `"Arial Narrow", Arial, sans-serif` : `Arial, Helvetica, sans-serif`;

  function build(data) {
    const L = data.layers, [ox, oy] = data.origin, parts = [], texts = [];
    let order = 0;
    const ingest = (c, kind, lt, items) => {
      const tiles = new Map(), o = ++order;
      for (const P of items) {
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (const p of P) for (let i = 0; i < p.length; i += 2) { const x = p[i], y = p[i + 1]; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
        const key = Math.floor(x0 / TILE) + "," + Math.floor(y0 / TILE), fine = Math.max(x1 - x0, y1 - y0) < FINE;
        let t = tiles.get(key); if (!t) tiles.set(key, (t = { c: [], f: [] }));
        (fine ? t.f : t.c).push({ P, b: [x0, y0, x1, y1] });
      }
      for (const t of tiles.values()) for (const [list, fine] of [[t.c, false], [t.f, true]]) {
        if (!list.length) continue;
        let b = [Infinity, Infinity, -Infinity, -Infinity]; const path = new Path2D();
        for (const { P, b: ib } of list) {
          b = [Math.min(b[0], ib[0]), Math.min(b[1], ib[1]), Math.max(b[2], ib[2]), Math.max(b[3], ib[3])];
          for (const p of P) {
            path.moveTo(p[0], p[1]); for (let i = 2; i < p.length; i += 2) path.lineTo(p[i], p[i + 1]);
            if (kind === "f" || kind === "m") path.closePath();
          }
        }
        parts.push({ c, kind, lt, order: o, fine, b, path });
      }
    };
    for (const blk of data.blocks) {
      const D = blk.data, defs = D.defs, group = blk.group;
      const resolve = (spec, ctx) => {
        const layer = spec[0] || ctx.layer;
        const lt = spec[2] === "L" ? L[layer]?.lt : spec[2] === "B" ? ctx.lt : spec[2];
        return { layer, lt, veg: ctx.veg };
      };
      const off = (l) => L[l] && (L[l].off || L[l].frozen);
      let pend = null;
      const flush = () => { if (pend) { ingest(pend.c, pend.kind, pend.lt, pend.items); pend = null; } };
      const push = (st, kind, item) => {
        const c = cls(st.layer, group, st.veg), lt = kind === "s" ? st.lt : "";
        if (!pend || pend.c !== c || pend.kind !== kind || pend.lt !== lt) { flush(); pend = { c, kind, lt, items: [] }; }
        pend.items.push(item);
      };
      const root = { layer: "0", lt: L["0"]?.lt || "Continuous", veg: false };
      (function walk(di, M, ctx) {
        const d = defs[di], k = Math.pow(10, -d.q);
        if (d.veg && !ctx.veg) ctx = { ...ctx, veg: true };
        const [a, b, c, e, f, g] = M;
        const place = (arr) => {
          const o = new Array(arr.length); let x = arr[0], y = arr[1];
          for (let i = 0; i < arr.length; i += 2) {
            if (i) { x += arr[i]; y += arr[i + 1]; }
            const X = x * k, Y = y * k;
            o[i] = a * X + c * Y + f - ox; o[i + 1] = oy - (b * X + e * Y + g);
          }
          return o;
        };
        for (const [l, col, lt, lw, kind, items] of d.runs) {
          const st = resolve([l, col, lt, lw], ctx);
          if (kind === "i") {
            if (L[st.layer]?.frozen) continue;
            for (const [ci, ca, cb, cc, cd, ce, cf] of items)
              walk(ci, [a * ca + c * cb, b * ca + e * cb, a * cc + c * cd, b * cc + e * cd, a * ce + c * cf + f, b * ce + e * cf + g], st);
            continue;
          }
          if (off(st.layer)) continue;
          if (kind === "t") {
            flush();
            const det = a * e - b * c, sx = Math.hypot(a, b), sy = Math.abs(det) / (sx || 1);
            for (const t of items) {
              const X = t[0] * k, Y = t[1] * k;
              texts.push({ t, x: a * X + c * Y + f - ox, y: oy - (b * X + e * Y + g), ang: Math.atan2(b, a) * 180 / Math.PI, k: sy, m: det < 0 ? -1 : 1 });
            }
            continue;
          }
          for (const it of items) push(st, kind, (kind === "f" ? it : [it]).map(place));
        }
      })(D.root, D.place.m, resolve(D.place.spec, root));
      flush();
    }
    parts.sort((p, q) => p.order - q.order);
    return { parts, texts, lt: data.linetypes || {}, ltscale: data.ltscale || 1 };
  }

  function mount(stage, data, opts) {
    const M = build(data), cv = document.createElement("canvas"), ctx = cv.getContext("2d");
    cv.className = "ph-layer pc-plan";
    cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none";
    stage.insertBefore(cv, (opts && opts.before) || null);
    let vb = null, raf = 0, theme = null;
    const colours = () => {
      const cs = getComputedStyle(cv), v = (n) => cs.getPropertyValue(n).trim();
      const o = {}; for (const k in STROKE) o[k] = v(STROKE[k][0]);
      Object.assign(o, { paper: v("--ph-paper"), fill: v("--ph-fill"), fillGreen: v("--ph-fill-green"), fillGlass: v("--ph-fill-glass"),
                         hatch: v("--ph-hatch"), text: v("--ph-text") });
      return o;
    };
    function paint() {
      raf = 0; if (!vb) return;
      const r = cv.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
      if (!r.width || !r.height) return;
      const W = Math.round(r.width * dpr), H = Math.round(r.height * dpr);
      if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
      theme = theme || colours();
      const kk = Math.max(vb[2] / r.width, vb[3] / r.height), x0 = vb[0] + vb[2] / 2 - (r.width * kk) / 2, y0 = vb[1] + vb[3] / 2 - (r.height * kk) / 2;
      const s = dpr / kk, hair = 1 / s, vx1 = x0 + r.width * kk, vy1 = y0 + r.height * kk, skipFine = FINE * s < 1.2;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
      ctx.setTransform(s, 0, 0, s, -x0 * s, -y0 * s);
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (const p of M.parts) {
        if (p.fine && skipFine) continue;
        if (p.b[2] < x0 || p.b[0] > vx1 || p.b[3] < y0 || p.b[1] > vy1) continue;
        if (p.kind === "f") { ctx.fillStyle = p.c === "green" ? theme.fillGreen : p.c === "glass" ? theme.fillGlass : theme.fill; ctx.fill(p.path, "evenodd"); continue; }
        if (p.kind === "m") { ctx.fillStyle = theme.paper; ctx.fill(p.path, "nonzero"); continue; }
        if (p.kind === "h") { ctx.globalAlpha = p.c === "green" ? 0.6 : 1; ctx.strokeStyle = p.c === "green" ? theme.green : theme.hatch; ctx.lineWidth = 0.3 * dpr * hair; ctx.setLineDash([]); ctx.stroke(p.path); ctx.globalAlpha = 1; continue; }
        const [, w] = STROKE[p.c];
        ctx.strokeStyle = theme[p.c]; ctx.lineWidth = w * dpr * hair;
        const dash = p.lt ? M.lt[p.lt] : null;
        if (dash && dash.length && dash.some((v) => v > 0) && Math.max(...dash) * M.ltscale * s > 2) ctx.setLineDash(dash.map((v) => Math.max(v, 0.5 / s / M.ltscale) * M.ltscale));
        else ctx.setLineDash([]);
        ctx.stroke(p.path);
      }
      ctx.setLineDash([]);
      ctx.fillStyle = theme.text;
      for (const T of M.texts) {
        const [, , h0, rot, align, row, words, style, wf, ls, font] = T.t, h = h0 * (T.k || 1), fs = h / 0.716;
        if (fs * s < 3 * dpr || T.x < x0 - 20000 || T.x > vx1 + 20000 || T.y < y0 - 20000 || T.y > vy1 + 20000) continue;
        ctx.save(); ctx.translate(T.x, T.y); ctx.rotate(-(T.ang || 0) * Math.PI / 180); if (T.m < 0) ctx.scale(1, -1);
        ctx.rotate(-rot * Math.PI / 180); ctx.scale(wf || 1, 1);
        ctx.font = `${fs}px ${FONT(font || style)}`; ctx.textAlign = align; ctx.textBaseline = "alphabetic";
        const lines = String(words).split("\n"), lh = (h * 5) / 3 * (ls || 1), block = (lines.length - 1) * lh + h;
        let base = row === 0 ? h : row === 1 ? h - block / 2 : row === 2 ? -(lines.length - 1) * lh : 0;
        for (const l of lines) { ctx.fillText(l, 0, base); base += lh; }
        ctx.restore();
      }
    }
    const draw = (v) => { vb = v.slice(); if (!raf) raf = requestAnimationFrame(paint); };
    // a theme switch (Day / Night) changes the colours
    new MutationObserver(() => { theme = null; if (vb) draw(vb); }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
    addEventListener("resize", () => vb && draw(vb));
    return { el: cv, draw, model: M };
  }

  window.PlanCanvas = { mount, build };
})();
