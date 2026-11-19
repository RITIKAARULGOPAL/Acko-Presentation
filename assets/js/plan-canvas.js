/* plan-canvas.js - the floor plan's own drawing (data/plan-base.js, window.PLAN_BASE) as vector on a <canvas>, at every zoom.
   The data is plan_vector.py's instanced export: each block definition once, placements by reference. It is walked once,
   placed into the deck's plan frame (x - origin[0], origin[1] - y, mm) and kept as Path2D batches in 10 m tiles; a draw
   strokes what is in view. Colours and line weights are the deck's plan theme (plan-hover.css, --ph-*), by what a layer
   draws: walls, glass, doors, furniture, plants, shading, annotation, the rest; fills light (the columns dark grey), pattern lines faint.

   PlanCanvas.mount(stage, data, { before }) -> { el, draw([x, y, w, h], sync), prepare(view, done), warm(view, done), bare(on, re) }
     stage   the element the canvas fills (PlanHover's .ph-stage); before: the child it goes in front of
     draw    the viewBox in plan mm, fitted as the SVGs above it fit theirs (xMidYMid meet)
     prepare a picture of a view made off the page, in a worker (19 Nov); warm: the same at idle, kept for when the view comes back */
(function () {
  // the core: what turns the plan's data into paths and paints a slice of a picture. It names nothing outside itself, so the same text runs in the
  // page and in the worker
  function makeCore() {
  const TILE = 10000, FINE = 250;
  const GLASS = /GLASS|GLSS|GLS|GLAZ|_IN_GL\b/i, GREEN = /PLANT|PLNT|GRASS|LANDSCAP|TREE|SHRUB|VEG/i;
  // strokes of 0.9 CSS px or less (furniture, doors, planting, hatch, notes, the rest): butt ends and bevelled joins are indistinguishable from
  // round ones at that width and cost the GPU about half (19 Nov, "lag while zooming": one overview paint 700 ms -> 350 ms at 2x density);
  // walls, columns and glass keep round ends and joins
  const THIN = { furn: 1, door: 1, anno: 1, green: 1, shade: 1, base: 1 };
  const DOOR = /DOOR|_DOR_|DOR-/i, COL = /COLS|S-COL/i, WALL = /WALL|PART|PRTN|COLS|S-COL|CORE|STRU/i;
  const FURN = /FURN|\bFUR\b|_FUR_|CHAIR|TABLE|SEAT|SOFA|STORAGE|TV UNIT|^AC_WS_|EQPM|MLWK|FIXT|PLBG|ELEV/i;
  const SHADE = /SHADE|PATT|HATCH/i, ANNO = /ANNO|TEXT|DIM|TAG|IDEN/i;
  // class -> [colour variable, line width in CSS px]
  const STROKE = { wall: ["--ph-wall", 1.4], col: ["--ph-wall", 1.4], glass: ["--ph-glass", 1], door: ["--ph-door", 0.7], furn: ["--ph-furniture", 0.6],
                   green: ["--ph-plant", 0.5], shade: ["--ph-shade", 0.4], anno: ["--ph-door", 0.5], base: ["--ph-line", 0.9] };
  const cls = (layer, group, veg) => veg || group === "vegetation" || GREEN.test(layer) ? "green" : GLASS.test(layer) ? "glass"
    : DOOR.test(layer) ? "door" : COL.test(layer) ? "col" : WALL.test(layer) ? "wall" : FURN.test(layer) ? "furn" : SHADE.test(layer) ? "shade"
    : ANNO.test(layer) ? "anno" : "base";
  const FONT = (name) => /gothic/i.test(name) ? `"Century Gothic", "Futura", "Avenir", sans-serif`
    : /romans|txt|standard/i.test(name) ? `"Arial Narrow", Arial, sans-serif` : `Arial, Helvetica, sans-serif`;

  function build(data) {
    const L = data.layers, [ox, oy] = data.origin, parts = [], texts = [];
    let order = 0;
    const ingest = (c, kind, lt, items, ly) => {
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
        parts.push({ c, kind, lt, order: o, fine, b, path, ly });
      }
    };
    for (const blk of data.blocks) {
      const D = blk.data, defs = D.defs, group = blk.group;
      const resolve = (spec, ctx) => {
        const layer = spec[0] || ctx.layer;
        const lt = spec[2] === "L" ? L[layer]?.lt : spec[2] === "B" ? ctx.lt : spec[2];
        // host: the layer that owns it for the bare shell (planBare): an entity on layer 0 takes its insert's, as CAD does
        return { layer, lt, veg: ctx.veg, host: layer && layer !== "0" ? layer : ctx.host || layer };
      };
      const off = (l) => L[l] && (L[l].off || L[l].frozen);
      let pend = null;
      const flush = () => { if (pend) { ingest(pend.c, pend.kind, pend.lt, pend.items, pend.ly); pend = null; } };
      const push = (st, kind, item) => {
        const c = cls(st.layer, group, st.veg), lt = kind === "s" ? st.lt : "", ly = group === "base" ? st.host : "";   // vegetation and text are never shell
        if (!pend || pend.c !== c || pend.kind !== kind || pend.lt !== lt || pend.ly !== ly) { flush(); pend = { c, kind, lt, items: [], ly }; }
        pend.items.push(item);
      };
      const root = { layer: "0", lt: L["0"]?.lt || "Continuous", veg: false, host: "0" };
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
    // paint the device columns [d0, d1) of picture g into context c (all of it when d0 is undefined): what a slice, or the whole canvas, is made of.
    // g: { dpr, W, H, x0, y0, s, hair, vy1 } (x0, y0: the plan point at the picture's top left; s: device px per mm); theme: the colours;
    // bare: a RegExp (only the building's own layers) or null
    function makeRender(M) {
      const shellOf = new Map(); let shellFor = null;
      return function render(c, g, d0, d1, theme, bare) {
        if (bare !== shellFor) { shellOf.clear(); shellFor = bare; }
        const isShell = (ly) => { if (!shellOf.has(ly)) shellOf.set(ly, !!ly && bare.test(ly)); return shellOf.get(ly); };
        const { dpr, W, H, s, hair } = g, skipFine = FINE * s < 1.2, whole = d0 === undefined;
        if (whole) { d0 = 0; d1 = W; }
        const px0 = g.x0 + d0 / s, px1 = g.x0 + d1 / s, y0 = g.y0, vy1 = g.vy1;             // the plan columns being painted
        c.setTransform(1, 0, 0, 1, 0, 0);
        if (!whole) { c.save(); c.beginPath(); c.rect(d0, 0, d1 - d0, H); c.clip(); }
        c.clearRect(d0, 0, d1 - d0, H);
        c.setTransform(s, 0, 0, s, -g.x0 * s, -y0 * s);
        let round = true; c.lineCap = "round"; c.lineJoin = "round";
        const ends = (thin) => { if (thin === round) { round = !thin; c.lineCap = thin ? "butt" : "round"; c.lineJoin = thin ? "bevel" : "round"; } };
        const cols = [];                                // the columns, last: solid over whatever line runs into them
        for (const p of M.parts) {
          if (p.fine && skipFine) continue;
          if (bare && !isShell(p.ly)) continue;
          if (p.b[2] < px0 || p.b[0] > px1 || p.b[3] < y0 || p.b[1] > vy1) continue;
          if (p.c === "col") { cols.push(p); continue; }
          if (p.kind === "f") { c.fillStyle = p.c === "green" ? theme.fillGreen : p.c === "glass" ? theme.fillGlass : theme.fill; c.fill(p.path, "evenodd"); continue; }
          if (p.kind === "m") { c.fillStyle = theme.paper; c.fill(p.path, "nonzero"); continue; }
          if (p.kind === "h") { ends(true); c.globalAlpha = p.c === "green" ? 0.6 : 1; c.strokeStyle = p.c === "green" ? theme.green : theme.hatch; c.lineWidth = 0.3 * dpr * hair; c.setLineDash([]); c.stroke(p.path); c.globalAlpha = 1; continue; }
          const [, w] = STROKE[p.c];
          ends(!!THIN[p.c]);
          c.strokeStyle = theme[p.c]; c.lineWidth = w * dpr * hair;
          const dash = p.lt ? M.lt[p.lt] : null;
          if (dash && dash.length && dash.some((v) => v > 0) && Math.max(...dash) * M.ltscale * s > 2) c.setLineDash(dash.map((v) => Math.max(v, 0.5 / s / M.ltscale) * M.ltscale));
          else c.setLineDash([]);
          c.stroke(p.path);
        }
        c.setLineDash([]);
        c.fillStyle = theme.fillCol;
        for (const p of cols) if (p.kind === "f") c.fill(p.path, "evenodd");
        ends(false); c.strokeStyle = theme.col; c.lineWidth = STROKE.col[1] * dpr * hair;
        for (const p of cols) if (p.kind === "s") c.stroke(p.path);
        c.fillStyle = theme.text;
        for (const T of bare ? [] : M.texts) {
          const [, , h0, rot, align, row, words, style, wf, ls, font] = T.t, h = h0 * (T.k || 1), fs = h / 0.716;
          if (fs * s < 3 * dpr || T.x < px0 - 20000 || T.x > px1 + 20000 || T.y < y0 - 20000 || T.y > vy1 + 20000) continue;
          c.save(); c.translate(T.x, T.y); c.rotate(-(T.ang || 0) * Math.PI / 180); if (T.m < 0) c.scale(1, -1);
          c.rotate(-rot * Math.PI / 180); c.scale(wf || 1, 1);
          c.font = `${fs}px ${FONT(font || style)}`; c.textAlign = align; c.textBaseline = "alphabetic";
          const lines = String(words).split("\n"), lh = (h * 5) / 3 * (ls || 1), block = (lines.length - 1) * lh + h;
          let base = row === 0 ? h : row === 1 ? h - block / 2 : row === 2 ? -(lines.length - 1) * lh : 0;
          for (const l of lines) { c.fillText(l, 0, base); base += lh; }
          c.restore();
        }
        if (!whole) c.restore();
      };
    }
    return { build, makeRender, STROKE };
  }
  const CORE = makeCore(), STROKE = CORE.STROKE;

  // the worker (19 Nov, "lag while zooming"): a canvas only records its drawing, and anything that needs the result makes the page wait for the GPU
  // to finish it: 0.4-1.6 s for one overview paint at 2x density, however it is sliced. Here the waiting is done off the page: the worker builds the
  // same paths from the same data, paints pictures of views on an OffscreenCanvas a slice at a time, and hands back bitmaps; the page only copies
  // one. Its source is makeCore's own text plus this function, so there is no second copy to keep in step. Interactive jobs go before warm ones,
  // between slices (a cancel, or a more urgent job, is heard then)
  function workerMain() {
    const core = makeCore(); let render = null; const jobs = [], dead = new Set(); let busy = false;
    self.onmessage = (e) => {
      const m = e.data;
      if (m.t === "init") { render = core.makeRender(core.build(m.data)); postMessage({ t: "ready" }); pump(); }
      else if (m.t === "job") { jobs.push(m); pump(); }
      else if (m.t === "cancel") dead.add(m.id);
    };
    async function pump() {
      if (busy || !render) return; busy = true;
      while (jobs.length) {
        jobs.sort((a, b) => b.prio - a.prio);
        const j = jobs[0];
        if (dead.has(j.id)) { jobs.shift(); dead.delete(j.id); continue; }
        if (!j.oc) { j.oc = new OffscreenCanvas(j.g.W, j.g.H); j.c = j.oc.getContext("2d"); j.i = 0; j.re = j.bare ? new RegExp(j.bare[0], j.bare[1]) : null; }
        const k = j.order[j.i++];
        try { render(j.c, j.g, k * j.w, Math.min(j.g.W, (k + 1) * j.w), j.theme, j.re); } catch (err) { jobs.shift(); postMessage({ t: "fail", id: j.id }); continue; }
        if (j.i >= j.order.length) { jobs.shift(); j.c.getImageData(0, 0, 1, 1); const bm = j.oc.transferToImageBitmap();      // the readback makes the GPU finish here, in the worker, not when the page first uses the bitmap
          postMessage({ t: "done", id: j.id, bitmap: bm }, [bm]); }
        await new Promise((r) => setTimeout(r, 0));
      }
      busy = false;
    }
  }

  function mount(stage, data, opts) {
    const cv = document.createElement("canvas"), ctx = cv.getContext("2d");
    cv.className = "ph-layer pc-plan";
    cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none";
    stage.insertBefore(cv, (opts && opts.before) || null);
    // the stage can carry a CSS transform (PlanHover's fastZoom scales the drawn layers while a zoom is under way): geometry is read from its
    // parent, which never does, not from the canvas
    const host = stage.parentNode;
    let vb = null, raf = 0, theme = null, themeV = 0, bare = null;
    // the page's own paths and painter: built only when needed (no worker, or a picture wanted at once); the worker builds its own
    let M = null, rend = null;
    const local = () => { if (!rend) { M = CORE.build(data); rend = CORE.makeRender(M); } return rend; };
    const colours = () => {
      const cs = getComputedStyle(cv), v = (n) => cs.getPropertyValue(n).trim();
      const o = {}; for (const k in STROKE) o[k] = v(STROKE[k][0]);
      Object.assign(o, { paper: v("--ph-paper"), fill: v("--ph-fill"), fillGreen: v("--ph-fill-green"), fillGlass: v("--ph-fill-glass"), fillCol: v("--ph-fill-col"),
                         hatch: v("--ph-hatch"), text: v("--ph-text") });
      return o;
    };
    // ---- one picture of a view: the canvas' size, the scale, where the plan falls; key names the picture (size, view, mode, colours) ----
    const geom = (view, bb) => {
      const r = host.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
      if (!r.width || !r.height) return null;
      const kk = Math.max(view[2] / r.width, view[3] / r.height), x0 = view[0] + view[2] / 2 - (r.width * kk) / 2, y0 = view[1] + view[3] / 2 - (r.height * kk) / 2, s = dpr / kk;
      const W = Math.round(r.width * dpr), H = Math.round(r.height * dpr);
      return { dpr, W, H, x0, y0, s, hair: 1 / s, vy1: y0 + r.height * kk, key: W + "x" + H + "|" + view.join(",") + "|" + String(bb === undefined ? bare : bb) + "|" + themeV };
    };
    // ---- pictures: a view's drawing made ahead (a bitmap from the worker, or an offscreen canvas painted in slices when there is no worker); showing
    // one is a copy. Pinned pictures (the overview, warmed at idle) are kept for views that come back (Reset view, the next click); the newest other
    // one waits for its commit ----
    const pool = [];
    const grab = (W, H) => { let b = pool.pop(); if (!b) { const o = document.createElement("canvas"); b = { cv: o, c: o.getContext("2d") }; } if (b.cv.width !== W || b.cv.height !== H) { b.cv.width = W; b.cv.height = H; } return b; };
    const release = (b) => { if (b && pool.length < 2) pool.push(b); };
    const drop = (rec) => { if (!rec) return; if (rec.bm) rec.bm.close(); else release(rec.b); };
    const pinned = new Map(); let lastDone = null;
    const ready = (key) => pinned.get(key) || (lastDone && lastDone.key === key ? lastDone : null);
    const keep = (rec, pin) => {
      if (pin) { pinned.set(rec.key, rec); while (pinned.size > 2) { const k0 = pinned.keys().next().value; drop(pinned.get(k0)); pinned.delete(k0); } }
      else { drop(lastDone); lastDone = rec; }
    };
    // the worker: made at the first need; null where workers or offscreen canvases aren't (or it failed): then the page paints
    let wk = null, wkFail = false, nextId = 1; const pend = new Map();
    function worker() {
      if (wk || wkFail) return wk;
      try {
        if (!window.Worker || !window.OffscreenCanvas || !window.createImageBitmap) throw new Error("no worker");
        const src = "const makeCore = " + makeCore.toString() + ";\n(" + workerMain.toString() + ")();";
        wk = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })));
        // any failure turns the worker off for good: what was waiting is told, and the page paints from then on
        const fail = () => { wkFail = true; const w = wk, fs = [...pend.values()]; wk = null; pend.clear(); try { w && w.terminate(); } catch (e) {} fs.forEach((f) => f(null)); };
        wk.onmessage = (e) => { const m = e.data; if (m.t === "fail") return fail(); const f = pend.get(m.id); if (f) { pend.delete(m.id); f(m.t === "done" ? m.bitmap : null); } };
        wk.onerror = fail;
        wk.postMessage({ t: "init", data });                      // the data is copied once (about 120 ms)
      } catch (e) { wkFail = true; wk = null; }
      return wk;
    }
    function job(view, pin, done) {                // a picture of view, made without stalling the page; done() when it can be shown (at once if it can already)
      theme = theme || colours();
      const bb = pin ? null : bare;                  // warmed pictures are always the full drawing, whatever mode a slide has the plan in now
      const g = geom(view, bb); if (!g) { done(); return null; }
      if (ready(g.key)) { done(); return null; }
      const N = Math.max(4, Math.min(10, Math.round(g.W / 480))), w = Math.ceil(g.W / N);
      const order = Array.from({ length: N }, (_, i) => i); if (!pin) order.sort((p, q) => Math.abs(p - (N - 1) / 2) - Math.abs(q - (N - 1) / 2));      // a zoom: the middle first
      const W = worker();
      if (W) {
        const id = nextId++; let dead = false;
        pend.set(id, (bm) => {
          if (dead) { if (bm) bm.close(); return; }
          if (!bm) { done(); return; }
          keep({ bm, key: g.key }, pin); done();
        });
        W.postMessage({ t: "job", id, prio: pin ? 0 : 1, g: { dpr: g.dpr, W: g.W, H: g.H, x0: g.x0, y0: g.y0, s: g.s, hair: g.hair, vy1: g.vy1 }, theme, bare: bb ? [bb.source, bb.flags] : null, order, w });
        return () => { dead = true; pend.delete(id); W.postMessage({ t: "cancel", id }); };
      }
      // no worker: slices on the page, a few ms of script per task (the GPU still makes the page wait when the picture is copied)
      const b = grab(g.W, g.H), render = local(); let i = 0, dead = false, tm = 0; const idle = pin && window.requestIdleCallback;
      const sched = (f) => { tm = idle ? requestIdleCallback(f, { timeout: 800 }) : setTimeout(f, 0); };
      const step = () => {
        if (dead) return;
        const t0 = performance.now();
        do { const k = order[i++]; render(b.c, g, k * w, Math.min(g.W, (k + 1) * w), theme, bb); } while (i < N && performance.now() - t0 < 10);
        if (i < N) return sched(step);
        keep({ b, key: g.key }, pin); done();
      };
      sched(step);
      return () => { dead = true; if (idle) cancelIdleCallback(tm); else clearTimeout(tm); release(b); };
    }
    let lastKey = "", fb = null;                  // what the canvas shows now (the same again is not painted again); a picture being made for it
    function paint() {
      raf = 0; if (!vb) return; clearTimeout(later);
      theme = theme || colours();
      const g = geom(vb); if (!g || g.key === lastKey) return;
      const pic = ready(g.key);
      if (!pic && worker()) {                       // the worker makes it; the canvas keeps what it shows until then
        if (!fb || fb.key !== g.key) {
          if (fb && fb.cancel) fb.cancel();
          const key = g.key; fb = { key, cancel: null };
          fb.cancel = job(vb.slice(), false, () => { if (fb && fb.key === key) fb = null; draw(vb, true); });
        }
        return;
      }
      if (cv.width !== g.W || cv.height !== g.H) { cv.width = g.W; cv.height = g.H; }
      if (pic) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, g.W, g.H); ctx.drawImage(pic.bm || pic.b.cv, 0, 0); }      // prepared: one copy
      else local()(ctx, g, undefined, undefined, theme, bare);
      lastKey = g.key;
    }
    // sync: paint now (PlanHover's fastZoom commits the layers' new view and clears its transform in the same frame: the canvas must not
    // show its old drawing under the new view for even one frame)
    const draw = (v, sync) => { vb = v.slice(); if (sync) { cancelAnimationFrame(raf); paint(); } else if (!raf) raf = requestAnimationFrame(paint); };
    // a theme switch (Day / Night) changes the colours: nothing painted before it is any use
    new MutationObserver(() => { theme = null; themeV++; lastKey = ""; pinned.forEach(drop); pinned.clear(); drop(lastDone); lastDone = null; if (vb) draw(vb); }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
    addEventListener("resize", () => vb && draw(vb));
    const SHELL = /^(A-(WALL|FLOR|DOOR|ELEV)|OB-A-WALL|S-(COLS|STRS)|RAILING|P-SANR|OUTLINE)/;
    // switched off (leaving the slide), the full drawing comes back at once for any slide that draws next; otherwise quietly, after the
    // cross-fade, so the hand-off doesn't stall on a whole repaint
    let later = 0;
    const setBare = (on, re) => { const nb = on ? re || SHELL : null; if (String(nb) === String(bare)) return; bare = nb; clearTimeout(later);
      if (!vb) return; if (on) draw(vb); else later = setTimeout(() => draw(vb), 900); };
    // prepare(view, done) -> cancel: a picture of `view` made without stalling; done() when it can be shown (at once if it already can: draw(view, true) then copies it)
    // warm(view, done): the same, at idle, kept for when the view comes back
    return { el: cv, draw, get model() { local(); return M; }, bare: setBare, prepare: (view, done) => job(view, false, done), warm: (view, done) => job(view, true, done || (() => {})) };
  }

  window.PlanCanvas = { mount, build: CORE.build };
})();
