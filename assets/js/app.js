/* ACKO · The Loop — the presentation engine (forked from the Mitigata presentation).
   A persistent WORLD (vector map · plan · photographs) lives behind the slides; each slide is a 16:9 page in deck points.
   Keys: → / PageDown / Space next beat · ← / PageUp previous · O index · N notes · F fullscreen · B blank · L laser.

   Every slide is its own file (slides/<id>.html): its section, its <style> and its script. A slide's script registers itself:
       ACKO.slide("s-id", (K) => ({ enter(_, sc) {…}, step(k, sc) {…}, leave(_, sc) {…} }));
   K is the kit below (helpers, the world, navigation, the shared layout plan). Nothing here runs until ACKO.start(): the
   joined deck calls it after all the slides' scripts; a slide opened on its own calls it from assets/js/dev.js. */
(function () {
  const FACTORIES = {};
  let booted = false;
  const asset = (p) => (window.ASSET_URLS && window.ASSET_URLS[p]) || p;   // an embedded copy in the single file, else the path
  window.ACKO = {
    slide(id, factory) { FACTORIES[id] = factory; },
    start() { if (!booted) { booted = true; boot(); } },
    asset,
  };

  function boot() {
  /* a slide opened on its own: wrap the deck's chrome (assets/js/shell.js) around its section */
  if (!document.getElementById("stage") && window.ACKO_SHELL) {
    const secs = Array.from(document.querySelectorAll("section.scene"));
    const holder = document.createElement("div"); holder.innerHTML = window.ACKO_SHELL;
    document.body.prepend(...holder.childNodes);
    const stage = document.getElementById("stage"); secs.forEach((s) => stage.appendChild(s));
    document.documentElement.classList.add("standalone");
  }
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const scenes = $$(".scene");
  const sceneIx = (id) => scenes.findIndex((s) => s.id === id);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { idx: -1, step: 1, t0: null, chapterT0: null, track: "main", mainAt: { idx: 0, step: 1 } };
  // three decks: the ACKO presentation, the Appendix and About SKV (opened from the SKV logo); the arrows stay inside the one on screen
  const trackOf = (s) => (s.dataset.part === "0" ? "skv" : s.dataset.part === "A" ? "appendix" : "main");
  const trackIdx = (t) => scenes.map((s, i) => (trackOf(s) === t ? i : -1)).filter((i) => i >= 0);
  let timers = [];
  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const clearTimers = () => { timers.forEach(clearTimeout); timers = []; };
  const raf2 = (fn) => requestAnimationFrame(() => requestAnimationFrame(fn));
  if (!scenes.length) return;

  /* ======================= mode ======================= */
  // each slide has its own mode: data-mode = dark (black) · lavender · grey; otherwise the deck's white pages
  function setTheme(t) { if (document.documentElement.dataset.theme !== t) document.documentElement.dataset.theme = t; }
  const applyMode = (sc) => setTheme(sc.dataset.mode || "light");

  /* ======================= world ======================= */
  const LAYERS = { map: $("#w-map"), plan: $("#w-plan"), photo: $("#w-photo") };
  function world(name, under) {
    for (const k in LAYERS) {
      LAYERS[k].classList.toggle("on", k === name);
      LAYERS[k].classList.toggle("under", k === under && k !== name);
    }
    world.cur = name;
    document.body.classList.toggle("on-photo", name === "photo");
  }
  const shade = (k) => { $("#shade").className = k || ""; };

  /* ---------- photographs ---------- */
  const PHOTO = {
    stack: $("#photo-stack"), cur: null,
    src(key) { return asset(/[./]/.test(key) ? key : "assets/img/" + key + ".webp"); },
    // o.kb drifts the frame slowly; o.ar is the image's aspect (cover fit keeps the whole frame filled)
    show(key, o) {
      o = o || {};
      const src = key ? this.src(key) : "";
      $("#photo-credit").textContent = o.credit || "";
      if (this.cur && this.cur.dataset.src === src) return this.cur;
      const f = document.createElement("div"); f.className = "shot-frame"; f.dataset.src = src;
      f.innerHTML = `<div class="cover${o.kb ? " kb" : ""}" data-ar="${o.ar || 2.0}">${src ? `<div class="shot" style="background-image:url('${src}')"></div>` : ""}</div>`;
      f.style.opacity = 0;
      this.stack.appendChild(f); layoutCovers();
      raf2(() => { f.style.opacity = 1; });
      const old = this.cur; this.cur = f;
      if (old) setTimeout(() => old.remove(), 1100);
      return f;
    },
  };
  // cover-fit frames: the image always fills the window, whatever its shape
  function layoutCovers() {
    const W = innerWidth, H = innerHeight;
    $$(".cover").forEach((c) => {
      const ar = +c.dataset.ar; let w = W, h = W / ar; if (h < H) { h = H; w = H * ar; }
      Object.assign(c.style, { position: "absolute", width: w + "px", height: h + "px", left: (W - w) / 2 + "px", top: (H - h) / 2 + "px" });
    });
  }
  addEventListener("resize", layoutCovers);

  /* ======================= chrome ======================= */
  const ov = $("#overview-grid");
  // the deck's sections, in the PPT's order
  const PARTS = { cover: "Opening", 1: "Design concept", 2: "Design strategy", 3: "Visual direction", 4: "Value addition", 5: "Space planning", A: "Appendix", 0: "About SKV" };
  const front = (s) => s.dataset.part === "cover" || s.dataset.part === "0";
  const nonum = (s) => s.hasAttribute("data-nonum");
  const journey = scenes.filter((s) => !front(s) && !nonum(s) && s.dataset.part !== "A");
  const appx = scenes.filter((s) => s.dataset.part === "A");
  const chNum = (i) => (nonum(scenes[i]) ? "—" : { cover: "—", 0: "SKV" }[scenes[i].dataset.part] || (scenes[i].dataset.part === "A" ? "A" + (appx.indexOf(scenes[i]) + 1) : String(journey.indexOf(scenes[i]) + 1).padStart(2, "0")));
  let part = null, grid = null;
  scenes.forEach((s, i) => {
    if (s.dataset.part !== part) {
      part = s.dataset.part;
      const h = document.createElement("h4"); h.textContent = PARTS[part] || ""; ov.appendChild(h);
      grid = document.createElement("div"); grid.className = "grid"; ov.appendChild(grid);
    }
    const o = document.createElement("button");
    const beats = s.dataset.beats ? s.dataset.beats.split(",") : null;
    o.innerHTML = `<span class="n">${front(s) || nonum(s) ? "" : chNum(i) + " · "}${s.dataset.mins} min</span><b>${s.dataset.title}</b>` +
      (beats ? `<span class="beats">${beats.map((t, k) => `<span data-beat="${k + 1}">${t}</span>`).join("")}</span>` : `<span>${(s.dataset.notes || "").slice(0, 92)}…</span>`);
    o.onclick = (e) => { const beat = e.target.closest("[data-beat]"); toggleOverview(false); go(i, beat ? +beat.dataset.beat : 1); };
    grid.appendChild(o);
  });
  /* the sections list behind the ACKO symbol (top right): hover lists the deck's five sections — past ink, now purple,
     next pale — and a click opens one */
  const TOPICS = { main: [["1", "Design concept"], ["2", "Design strategy"], ["3", "Visual direction"], ["4", "Value addition"], ["5", "Space planning"]], appendix: [["A", "Appendix"]], skv: [["0", "About SKV"]] };
  const firstOf = (p) => scenes.findIndex((s) => s.dataset.part === p);
  function topicMark(track) {
    const tp = TOPICS[track] || TOPICS.main, n = tp.length;
    $("#tm-list").innerHTML = (track === "main" ? `<button type="button" data-part="cover"><b>—</b>Cover</button>` : "") +
      tp.map(([p, nm], k) => `<button type="button" data-part="${p}"><b>${n > 1 ? String(k + 1).padStart(2, "0") : ""}</b>${nm}</button>`).join("");
    $$("#topic-mark [data-part]").forEach((el) => (el.onclick = (e) => {
      e.stopPropagation(); if (document.activeElement) document.activeElement.blur();
      if (el.dataset.part === "cover") state.t0 = null;
      const i = firstOf(el.dataset.part); if (i >= 0) go(i, 1);
    }));
    topicMark.track = track;
  }
  function topicState(sc) {
    if (topicMark.track !== state.track) topicMark(state.track);
    const order = (TOPICS[state.track] || TOPICS.main).map(([p]) => p), now = order.indexOf(sc.dataset.part);
    $$("#topic-mark [data-part]").forEach((el) => { const k = order.indexOf(el.dataset.part); el.dataset.state = k < now ? "past" : k === now ? "now" : "next"; });
  }
  const PLANNED = scenes.filter((s) => trackOf(s) === "main").reduce((a, s) => a + +s.dataset.mins, 0) * 60;
  const mmss = (s) => String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(Math.floor(s % 60)).padStart(2, "0");
  function tick() {
    const now = Date.now(), el = state.t0 ? (now - state.t0) / 1000 : 0, sc = scenes[state.idx];
    if (sc) $("#notes-time").textContent = `CH ${chNum(state.idx)} · ${mmss(state.chapterT0 ? (now - state.chapterT0) / 1000 : 0)} / ${mmss(+sc.dataset.mins * 60)} · TOTAL ${mmss(el)} / ${mmss(PLANNED)}`;
  }
  setInterval(tick, 1000);
  $("#notes-time").title = "Click to reset the timer";
  $("#notes-time").onclick = () => { state.t0 = null; tick(); };
  function updateChrome() {
    const sc = scenes[state.idx], n = +sc.dataset.steps || 1;
    topicState(sc);
    $$("#overview-grid button").forEach((b, i) => b.classList.toggle("on", i === state.idx));
    const tr = trackIdx(state.track);
    $("#progress").style.width = ((tr.indexOf(state.idx) + state.step / n) / tr.length) * 100 + "%";
    $$(".brand-btn").forEach((b) => b.classList.toggle("on", b.dataset.track === state.track));
    $("#notes-text").textContent = sc.dataset.notes || "";
  }
  const toggleOverview = (on) => $("#overview").classList.toggle("on", on === undefined ? !$("#overview").classList.contains("on") : on);
  function fullscreen() { if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }

  /* ======================= navigation ======================= */
  function go(i, step) {
    if (i === undefined || i < 0 || Number.isNaN(i)) return;      // a slide that isn't in this deck (e.g. a slide opened on its own)
    i = clamp(i, 0, scenes.length - 1);
    const prev = scenes[state.idx], next = scenes[i];
    if (prev !== next) {
      clearTimers();
      if (prev) { prev.classList.remove("active"); hook(prev, "leave"); }
      if (prev && trackOf(prev) === "main" && trackOf(next) !== "main") state.mainAt = { idx: state.idx, step: state.step };
      state.track = trackOf(next); document.body.dataset.track = state.track;
      state.idx = i; state.chapterT0 = Date.now();
      applyMode(next);
      next.classList.add("active"); document.body.dataset.scene = next.id;
      layoutCovers();
      hook(next, "enter");
    }
    setStep(step || 1);
  }
  function setStep(k) {
    const sc = scenes[state.idx], n = +sc.dataset.steps || 1;
    state.step = clamp(k, 1, n);
    $$("[data-step]", sc).forEach((e) => e.classList.toggle("shown", +e.dataset.step <= state.step));
    $$("[data-only]", sc).forEach((e) => e.classList.toggle("shown", e.dataset.only.split(",").map(Number).includes(state.step)));
    hook(sc, "step", state.step);
    updateChrome();
    // the address follows the beat; absolute, because a slide opened on its own has a <base> pointing at the project root
    const h = "#" + sc.id + "/" + state.step;
    if (location.hash !== h) { try { location.replace(location.href.split("#")[0] + h); } catch (e) { /* file:// */ } }
  }
  const steps = (i) => +scenes[i].dataset.steps || 1;
  function next() {
    if (!state.t0 && state.track === "main") state.t0 = Date.now();
    const tr = trackIdx(state.track), at = tr.indexOf(state.idx);
    if (state.step < steps(state.idx)) setStep(state.step + 1); else if (at < tr.length - 1) go(tr[at + 1], 1);
  }
  function prev() {
    const tr = trackIdx(state.track), at = tr.indexOf(state.idx);
    if (state.step > 1) setStep(state.step - 1); else if (at > 0) go(tr[at - 1], steps(tr[at - 1]));
  }
  // the logos: SKV opens About SKV; ACKO returns to the slide and beat the presentation was left on
  $("#brand-skv").onclick = () => { if (state.track !== "skv") go(sceneIx("s-skv"), 1); };
  $("#brand-main").onclick = () => { if (state.track !== "main") go(state.mainAt.idx, state.mainAt.step); };
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    const k = e.key;
    if (["ArrowRight", "PageDown", " ", "Enter"].includes(k)) { e.preventDefault(); next(); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(k)) { e.preventDefault(); prev(); }
    else if (k === "Home") go(trackIdx(state.track)[0], 1);
    else if (k === "End") go(trackIdx(state.track).slice(-1)[0], 1);
    else if (k === "f" || k === "F") fullscreen();
    else if (k === "b" || k === "B" || k === ".") $("#blank").classList.toggle("on");
    else if (k === "o" || k === "O" || k === "Escape") toggleOverview(k === "Escape" ? false : undefined);
    else if (k === "n" || k === "N") $("#notes").classList.toggle("on");
    else if (k === "l" || k === "L") $("#cur").classList.toggle("laser");
  });
  $("#blank").onclick = () => $("#blank").classList.remove("on");

  /* ======================= presenter cursor =======================
     A purple dot with a ring easing behind it: the ring grows on anything clickable. It fades after 2 s still;
     L swaps in a red laser that leaves an ink trail fading in 1.6 s. */
  (function cursor() {
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    const cur = $("#cur"), ring = $(".cur-ring", cur), dot = $(".cur-dot", cur), laser = $(".cur-laser", cur);
    const CLICK = "button, a[href], [role=button], label, select, summary, .click, #notes-time";
    const ease = reduced ? 1 : 0.22;
    const p = { x: 0, y: 0, rx: 0, ry: 0 };
    let moved = 0, raf = 0;
    const at = (el, x, y) => { el.style.transform = `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%)`; };
    const tick = () => {
      p.rx += (p.x - p.rx) * ease; p.ry += (p.y - p.ry) * ease;
      const settled = Math.abs(p.x - p.rx) + Math.abs(p.y - p.ry) < 0.3;
      if (settled) { p.rx = p.x; p.ry = p.y; }
      at(ring, p.rx, p.ry);
      raf = settled ? 0 : requestAnimationFrame(tick);
    };
    const cv = $(".cur-trail", cur), cx = cv.getContext("2d"), LIFE = 1600;
    let ink = [], inkRaf = 0;
    const inkClear = () => { ink = []; cx.clearRect(0, 0, cv.width, cv.height); };
    const inkPass = (w, a) => {
      for (let i = 1; i < ink.length; i++) {
        const f = ink[i].f;
        cx.globalAlpha = a * f; cx.lineWidth = w * (0.25 + 0.75 * f);
        cx.beginPath(); cx.moveTo(ink[i - 1].x, ink[i - 1].y); cx.lineTo(ink[i].x, ink[i].y); cx.stroke();
      }
    };
    const inkTick = (now) => {
      const d = devicePixelRatio || 1, W = innerWidth, H = innerHeight;
      if (cv.width !== Math.round(W * d) || cv.height !== Math.round(H * d)) { cv.width = Math.round(W * d); cv.height = Math.round(H * d); }
      cx.setTransform(d, 0, 0, d, 0, 0); cx.clearRect(0, 0, W, H);
      ink = ink.filter((q) => now - q.t < LIFE); ink.forEach((q) => (q.f = 1 - (now - q.t) / LIFE));
      cx.lineCap = cx.lineJoin = "round"; cx.strokeStyle = "#cc0000";
      inkPass(8, 0.18); inkPass(3, 0.95); cx.globalAlpha = 1;
      inkRaf = ink.length ? requestAnimationFrame(inkTick) : 0;
    };
    new MutationObserver(() => { if (!cur.classList.contains("laser")) inkClear(); }).observe(cur, { attributes: true, attributeFilter: ["class"] });
    addEventListener("hashchange", inkClear);
    document.documentElement.classList.add("cx");
    cur.classList.add("out");
    document.addEventListener("pointermove", (e) => {
      if (e.pointerType !== "mouse") return;
      p.x = e.clientX; p.y = e.clientY; moved = Date.now();
      if (cur.classList.contains("out")) { p.rx = p.x; p.ry = p.y; at(ring, p.x, p.y); }
      const t = e.target instanceof Element ? e.target : null;
      cur.classList.remove("out", "idle");
      cur.classList.toggle("text", !!(t && t.closest("input, textarea")));
      cur.classList.toggle("click", !!(t && t.closest(CLICK)));
      cur.classList.toggle("pan", !!(t && t.closest(".pannable")));
      at(dot, p.x, p.y); at(laser, p.x, p.y);
      if (!raf) raf = requestAnimationFrame(tick);
      if (!reduced && cur.classList.contains("laser")) { ink.push({ x: p.x, y: p.y, t: performance.now() }); if (!inkRaf) inkRaf = requestAnimationFrame(inkTick); }
    }, { capture: true, passive: true });
    document.addEventListener("pointerdown", (e) => { if (e.pointerType === "mouse") cur.classList.add("down"); }, true);
    document.addEventListener("pointerup", () => cur.classList.remove("down"), true);
    document.addEventListener("mouseout", (e) => { if (!e.relatedTarget) { cur.classList.add("out"); inkClear(); } });
    setInterval(() => { if (!cur.classList.contains("laser") && Date.now() - moved > 2000) cur.classList.add("idle"); }, 200);
  })();

  /* ======================= lightbox ======================= */
  const LB = $("#lightbox");
  function lightbox(src, cap) { $("img", LB).src = src; $("figcaption", LB).textContent = cap || ""; LB.hidden = false; requestAnimationFrame(() => LB.classList.add("on")); }
  function lightboxOff() { if (LB.hidden) return false; LB.classList.remove("on"); setTimeout(() => { if (!LB.classList.contains("on")) LB.hidden = true; }, 300); return true; }
  LB.addEventListener("click", (e) => { if (!e.target.closest("img")) lightboxOff(); });
  document.addEventListener("keydown", (e) => {
    if (LB.hidden) return;
    if (e.key === "Escape") { lightboxOff(); e.stopImmediatePropagation(); e.preventDefault(); }
    else if (["ArrowRight", "ArrowLeft", "PageDown", "PageUp", " ", "Enter", "Backspace", "Home", "End"].includes(e.key)) lightboxOff();
  }, true);

  /* ======================= helpers the slides use ======================= */
  const H = {};
  function hook(sc, ev, arg) { const h = sc && H[sc.id]; if (h && h[ev]) { try { h[ev](arg, sc); } catch (e) { console.error(`${sc.id} ${ev}:`, e); } } }
  // a page with no world behind it: the slide is the whole picture
  const plain = () => { world("none"); shade(""); };
  // .rv / .rv-i children come in one after another; restart by removing and re-adding .go
  function reveal(el, delay) { if (!el) return; el.classList.remove("go"); void el.offsetWidth; later(() => el.classList.add("go"), delay || 60); }
  function countUp(el, ms) {
    if (!el) return;
    const to = +el.dataset.count, dec = +(el.dataset.dec || 0), pre = el.dataset.pre || "", post = el.dataset.post || "";
    const show = (v) => (el.textContent = pre + (dec ? v.toFixed(dec) : Math.round(v).toLocaleString("en-IN")) + post);
    if (reduced) return show(to);
    const t0 = performance.now(), sc = document.body.dataset.scene;
    const step = (now) => { const k = Math.min(1, (now - t0) / ms); show(to * (1 - Math.pow(1 - k, 3))); if (k < 1 && document.body.dataset.scene === sc) requestAnimationFrame(step); else show(to); };
    show(0); requestAnimationFrame(step);
  }
  // type a line in, word by word (each word a span, shown in turn)
  function typeWords(el, ms, delay) {
    if (!el.dataset.words) { el.dataset.words = "1"; el.innerHTML = el.textContent.trim().split(/\s+/).map((w) => `<span>${w} </span>`).join(""); }
    const w = $$("span", el); w.forEach((s) => s.classList.remove("on"));
    w.forEach((s, i) => later(() => s.classList.add("on"), (delay || 0) + i * (ms || 70)));
  }
  // an SVG path drawn by its own length
  function drawPath(path, ms, delay) {
    const L = path.getTotalLength(); path.style.transition = "none"; path.style.strokeDasharray = L; path.style.strokeDashoffset = L;
    void path.getBoundingClientRect();
    later(() => { path.style.transition = `stroke-dashoffset ${ms}ms cubic-bezier(.45,.05,.3,1)`; path.style.strokeDashoffset = 0; }, delay || 0);
  }
  const inPoly = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j];
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0]) c = !c; } return c; };

  /* ======================= the layout as one plan (deck slides 53–57) =======================
     The DXF plan (data/plan-dxf.js, made by tools/acko/plan_dxf.py from the DXF plan toolkit's output), mounted once with
     PlanHover (assets/js/plan-hover.js) in the world, so the layout flies into its blow-ups without a cut. The plan is a
     picture at three sharpnesses (12 / 24 / 48 px per m; the one the zoom needs shows over the coarser ones). Beneath it,
     the spaces in the colours the deck's legend gives them; on it, hovers for the spaces (name, m²) and the six
     neighbourhoods (seats), the neighbourhood outlines, the fire egress paths and the deck's own marks (blow-up boxes, fire
     compartment line, entrances, arrival zones). Wheel zooms on the cursor, drag pans, a double-click returns to the beat's
     view. Used by s-layout and s-blowup. */
  const NB_COL = { "01": "#B45F06", "02": "#274E13", "03": "#45818E", "04": "#4A86E8", "05": "#9900FF", "06": "#FF00FF" };
  let HOVER = true;                                   // the Hover pill's state, deck-wide (planHover)
  const DP = { ph: null, root: null, raf: 0, lvRaf: 0, home: null, cur: null, P: null, onZone: null, zone: null };   // home: the beat's view; cur: what Reset returns to
  function deckPlan() {
    if (DP.ph) return DP;
    const P = (DP.P = window.PLAN_DXF), host = $("#world-plan"), [vx, vy, vw, vh] = P.viewBox, vb = P.viewBox.join(" ");
    // with the plan's own drawing (data/plan-base.js) it is drawn as vector on a canvas (below); the pictures are the fallback
    const BASE = window.PLAN_BASE && window.PlanCanvas;
    const imgs = BASE ? "" : P.levels.map((l) => `<image class="lv lv-${l.ppm}" href="${asset(l.src)}" x="${vx}" y="${vy}" width="${vw}" height="${vh}" preserveAspectRatio="none"/>`).join("");
    const data = { options: { plan: { label: "Layout", viewBox: vb, svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb}">${imgs}</svg>`,
      rooms: P.spaces.map((r) => ({ id: r.id, name: r.name, m2: r.m2, x: r.x, y: r.y, d: r.d })),
      teams: P.zones.map((z) => ({ id: z.id, name: z.name, pax: null, seats: z.seats, hot_desks: 0, x: z.x, y: z.y, zone: z.zone, desks: z.desks })) } } };
    host.classList.add("dxplan");
    host.classList.toggle("no-hover", !HOVER);
    DP.root = host;
    DP.ph = PlanHover.mount(host, { data, labelPlacement: "above" });     // the label above a space, never on it
    DP.ph.addLayer("dx-fill", (P.floor ? `<image href="${asset(P.floor)}" x="${vx}" y="${vy}" width="${vw}" height="${vh}" preserveAspectRatio="none"/>` : "") +
      P.spaces.map((r) => `<path d="${r.d}" style="fill:${r.colour}"/>`).join(""), { below: true });
    const O = P.overlays, tri = (x, y) => `M${x - 900} ${y - 600}L${x + 900} ${y - 600}L${x} ${y + 900}Z`;
    DP.ph.addLayer("dx-marks",
      `<g class="dx-arrival">${O.arrival.map((d) => `<path d="${d}"/>`).join("")}</g>` +
      `<g class="dx-nb">${P.zones.map((z) => `<path data-nb="${z.n}" d="${z.zone}" style="--c:${NB_COL[z.n] || "#888"}"/>`).join("")}</g>` +
      `<g class="dx-egress">${P.egress.map((e) => `<path class="${e.band === "lt50" ? "b50" : "b60"}" d="${e.d}"/>`).join("")}</g>` +
      `<g class="dx-fire">${O.fire.map((f) => `<line x1="${f[0]}" y1="${f[1]}" x2="${f[2]}" y2="${f[3]}"/>`).join("")}</g>` +
      `<g class="dx-entry">${O.entry.map((e) => `<path d="${tri(e[0], e[1])}"/>`).join("")}</g>` +
      `<g class="dx-blow">${Object.entries(O.blow).map(([k, r]) => `<text x="${r[0] + r[2] / 2}" y="${r[1] + r[3] + 2600}">Blown Up ${k}</text>`).join("")}</g>` +
      `<g class="dx-lab">${P.zones.map((z) => `<text data-nb="${z.n}" x="${z.x}" y="${z.y}"><tspan class="n">${z.n}</tspan><tspan class="s" dx="500" dy="-1500">${z.seats}</tspan>${z.title ? `<tspan class="t" x="${z.x}" dy="4200">${z.title}</tspan>` : ""}</text>`).join("")}</g>`);
    // the picture sharp enough for the zoom (screen px per metre, times the device's pixel ratio)
    // the DXF's own linework (data/plan-vec.js) as vector tiles, just above the picture and under the hovers and marks: drawn
    // as the toolkit's viewer draws it (.ph-plan: non-scaling strokes, its colours) once the zoom is past the sharpest picture
    // a hovered room tints its floor under the drawing, as in Mitigata (its "hoverfloor"): the component's rooms layer goes
    // beneath the picture and the vector, which take no pointer events, so the hover still reaches it; teams stay on top
    { const st = host.querySelector(".ph-stage"); st.insertBefore(st.querySelector(".ph-rooms"), st.querySelector(".ph-plan")); }
    if (BASE) {
      // the plan's drawing on a canvas where the picture was (over the fills and the rooms' hover tint, under the rest),
      // redrawn whenever the plan's view moves (every SVG layer shares one viewBox)
      const st = host.querySelector(".ph-stage"), rooms = st.querySelector(".ph-rooms");
      DP.base = PlanCanvas.mount(st, window.PLAN_BASE, { before: st.querySelector(".ph-plan") });
      new MutationObserver(() => DP.base.draw(DP.ph.view)).observe(rooms, { attributes: true, attributeFilter: ["viewBox"] });
      DP.base.draw(DP.ph.view);
    } else if (window.PLAN_VEC) {
      const svg = DP.ph.addLayer("ph-plan dx-vec", ""), st = host.querySelector(".ph-stage");
      st.insertBefore(svg, st.querySelector(".ph-teams"));
      DP.vec = { svg, g: [] };
      // a wheel-zoom in progress (cleared once it rests): with many tiles in view the picture carries it, as it does a drag
      let wt = 0; host.addEventListener("wheel", () => { host.classList.add("vec-wheel"); clearTimeout(wt); wt = setTimeout(() => host.classList.remove("vec-wheel"), 180); }, { passive: true });
    }
    const level = () => {
      const r = host.getBoundingClientRect(), v = DP.ph.view; if (!r.width) return;
      const need = (r.width / (v[2] / 1000)) * (window.devicePixelRatio || 1);
      P.levels.forEach((l, i) => host.classList.toggle("lv-" + l.ppm, i === 0 || P.levels[i - 1].ppm < need * 0.85));
      vecLevel(r, v, need);
    };
    DP.level = () => { cancelAnimationFrame(DP.lvRaf); DP.lvRaf = requestAnimationFrame(level); };
    ["wheel", "pointermove", "pointerup"].forEach((ev) => host.addEventListener(ev, DP.level, { passive: true }));
    addEventListener("resize", DP.level);
    level();
    // a click (not a drag) anywhere inside a neighbourhood's outline: the point is taken into plan mm the way the plan
    // draws it (viewBox, xMidYMid meet), so it works between the desks too and while the plan holds the pointer
    const rings = P.zones.map((z) => (z.zone.match(/M[^Z]+/g) || []).map((r) => r.slice(1).split("L").map((q) => q.trim().split(/\s+/).map(Number))));
    let down = null;
    host.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
    host.addEventListener("click", (e) => {
      if (!DP.onZone || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
      const r = host.getBoundingClientRect(), v = DP.ph.view, k = Math.max(v[2] / r.width, v[3] / r.height);
      const pt = [v[0] + v[2] / 2 - (r.width * k) / 2 + (e.clientX - r.left) * k, v[1] + v[3] / 2 - (r.height * k) / 2 + (e.clientY - r.top) * k];
      const i = rings.findIndex((rs) => rs.filter((ring) => inPoly(pt, ring)).length % 2 === 1);
      if (i >= 0) DP.onZone(P.zones[i]);
    });
    // decode the sharper pictures ahead, so the first zoom into them doesn't stall
    P.levels.slice(1).forEach((l) => { const im = new Image(); im.src = asset(l.src); if (im.decode) im.decode().catch(() => {}); });
    return DP;
  }
  // zoomed in (past 16 device px per m: a neighbourhood, a blow-up, a wheel-zoom) the vector tiles take over from the picture.
  // Tiles in view (and a margin) are built on first sight, a few per frame so a landing never stalls; the picture stays up
  // until the view's tiles are all there, then steps aside (vec-on). Once on, tiles panned into view join as they're built.
  const VEC_NEED = 16;                                 // device px per m on screen (the blow-ups are about 17 on a plain screen)
  function vecLevel(r, v, need) {
    const V = window.PLAN_VEC, X = DP.vec; if (!V || !X) return;
    if (need <= VEC_NEED) { DP.root.classList.remove("vec-on"); X.pending = []; return; }
    const k = Math.max(v[2] / r.width, v[3] / r.height), cx = v[0] + v[2] / 2, cy = v[1] + v[3] / 2;
    const hw = (r.width * k * 1.15) / 2, hh = (r.height * k * 1.15) / 2, vis = [];
    V.tiles.forEach((t, i) => {
      const on = t.b[0] < cx + hw && t.b[2] > cx - hw && t.b[1] < cy + hh && t.b[3] > cy - hh;
      if (on) vis.push(i);
      if (X.g[i]) X.g[i].style.display = on ? "" : "none";
    });
    DP.root.classList.toggle("vec-heavy", vis.length > 20);          // many tiles in view: the picture carries drags and wheel-zooms
    X.pending = vis.filter((i) => !X.g[i]);
    if (!X.pending.length) { DP.root.classList.add("vec-on"); return; }
    if (!X.busy) { X.busy = true; requestAnimationFrame(vecBuild); }
  }
  function vecBuild() {
    const X = DP.vec, V = window.PLAN_VEC, t0 = performance.now();
    while (X.pending.length && performance.now() - t0 < 12) {
      const i = X.pending.shift(); if (X.g[i]) continue;
      const g = (X.g[i] = document.createElementNS("http://www.w3.org/2000/svg", "g")); g.innerHTML = V.tiles[i].s; X.svg.appendChild(g);
    }
    if (X.pending.length) requestAnimationFrame(vecBuild); else { X.busy = false; DP.level(); }
  }
  // a flight: the picture carries the move (vec-fly), the vector comes back as it lands
  function fitVb(v, ms) {
    cancelAnimationFrame(DP.raf);
    const from = DP.ph.view, t0 = performance.now();
    if (!ms || reduced) { DP.root.classList.remove("vec-fly"); DP.ph.zoomTo(...v); return DP.level(); }
    DP.root.classList.add("vec-fly");
    const run = (now) => { const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      DP.ph.zoomTo(...from.map((a, i) => a + (v[i] - a) * e));
      if (k < 1) DP.raf = requestAnimationFrame(run); else { DP.root.classList.remove("vec-fly"); DP.level(); } };
    DP.raf = requestAnimationFrame(run);
  }
  // the viewBox (plan mm) that shows box [x0, y0, x1, y1] (plan mm) inside the display rect disp (frame px of the 1920 × 1080 page)
  function vbFor(box, disp) {
    const bw = box[2] - box[0], bh = box[3] - box[1], dw = disp[2] - disp[0], dh = disp[3] - disp[1], s = Math.min(dw / bw, dh / bh);
    const cx = (box[0] + box[2]) / 2, cy = (box[1] + box[3]) / 2, dcx = (disp[0] + disp[2]) / 2, dcy = (disp[1] + disp[3]) / 2;
    return [cx - dcx / s, cy - dcy / s, 1920 / s, 1080 / s];
  }
  // the whole plan where the deck's slide 53 has it (frame px [32.6, 175] – [1883.5, 442.8])
  const planView = () => { const [x, y, w, h] = DP.P.viewBox; return vbFor([x, y, x + w, y + h], [32.6, 175, 1883.5, 442.8]); };
  const PLAN_LAYERS = ["rooms", "teams", "nb", "fire", "blow", "lab", "entry", "egress", "fill"];
  function planOn(sc, opts) {
    deckPlan(); world("plan"); shade("");
    document.body.classList.add("dp-on");
    PLAN_LAYERS.forEach((k) => DP.root.classList.toggle("show-" + k, !!opts[k]));
    DP.ph.clear();
    const v = opts.view || planView();
    DP.home = DP.cur = v; DP.ph.setHome(...v); fitVb(v, opts.ms === undefined ? 900 : opts.ms);
  }
  function planOff() {
    document.body.classList.remove("dp-on"); DP.onZone = null;
    if (DP.root) { PLAN_LAYERS.forEach((k) => DP.root.classList.remove("show-" + k)); markZone(null); DP.root.classList.remove("focus"); DP.ph.clear(); }
    if (DP.layers) DP.layers.off();
  }
  // the layout's value-addition layers (assets/js/plan-layers.js), mounted on the deck plan the first time a slide asks
  function planLayers() { deckPlan(); return DP.layers || (DP.layers = window.PlanLayers ? window.PlanLayers.mount({ ph: DP.ph, host: DP.root, P: DP.P, A: window.AXO_DXF || { blocks: {}, plants: [] } }) : null); }
  // one neighbourhood picked out: the plan flies to it (inside disp, frame px), the others dim, its rooms can be hovered;
  // focusZone(null) flies back to the beat's view
  function markZone(z) {
    DP.zone = z;
    DP.root.classList.remove("focus"); $$(".dx-marks .hi", DP.root).forEach((p) => p.classList.remove("hi"));   // a row's hover, done with
    DP.root.classList.toggle("focus-zone", !!z);
    $$(".dx-nb [data-nb], .dx-lab [data-nb]", DP.root).forEach((e) => e.classList.toggle("sel", !!z && e.dataset.nb === z.n));
    $$(".ph-team", DP.root).forEach((g) => g.classList.toggle("sel", !!z && g.dataset.id === z.id));
  }
  function focusZone(id, disp) {
    deckPlan(); DP.ph.clear();
    const z = id ? DP.P.zones.find((q) => q.id === id) : null;
    markZone(z);
    if (!z) { DP.cur = DP.home; DP.ph.setHome(...DP.home); fitVb(DP.home, 900); return null; }
    const pad = 1500, b = z.box, v = vbFor([b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad], disp || [38, 120, 1230, 880]);
    DP.cur = v; DP.ph.setHome(...v); fitVb(v, 900);
    return z;
  }
  // a small key plan of the whole floor (markup), the neighbourhood id filled in its colour (kit: plan.keyplan)
  function zoneKey(id) {
    const P = window.PLAN_DXF, [x, y, w, h] = P.viewBox, l = P.levels[0];
    const sel = P.zones.find((q) => q.id === id);
    return `<svg class="dx-key" viewBox="${x} ${y} ${w} ${h}" preserveAspectRatio="xMidYMid meet">` +
      `<image href="${asset(l.src)}" x="${x}" y="${y}" width="${w}" height="${h}" preserveAspectRatio="none" opacity=".5"/>` +
      P.zones.map((z) => `<path class="${z.id === id ? "sel" : ""}" d="${z.zone}" style="--c:${NB_COL[z.n] || "#888"}"/>`).join("") +
      (sel ? `<text x="${sel.x}" y="${sel.y}" style="fill:${NB_COL[sel.n] || "#555"}">${sel.n}</text>` : "") + `</svg>`;
  }
  // the fire egress layer, switched by a button on the slide (on top of whatever the beat shows)
  function planEgress(on) { deckPlan(); return DP.root.classList.toggle("show-egress", on); }
  // the spaces in their legend colours (and the workhall floor tint): off, the plan is the DXF's plain linework, as the toolkit's viewer draws it
  function planFill(on) { deckPlan(); return DP.root.classList.toggle("show-fill", on); }
  // hover on / off (Ritika, as in Mitigata): names on hover across the layout, the blow-ups and the axo; it stays as set
  function planHover(on) { HOVER = on === undefined ? !HOVER : !!on; if (DP.root) { DP.root.classList.toggle("no-hover", !HOVER); if (!HOVER) DP.ph.clear(); } return HOVER; }
  // the neighbourhoods, switched the same way: outlines and arrival zones, their seat hover, and their numbers (unless labels is false)
  function planNb(on, labels) {
    deckPlan();
    const v = DP.root.classList.toggle("show-nb", on);
    DP.root.classList.toggle("show-teams", v); DP.root.classList.toggle("show-lab", v && labels !== false);
    return v;
  }
  // back to the beat's view, or the open neighbourhood's (flown; a double-click jumps there)
  function planReset(ms) { deckPlan(); DP.ph.clear(); if (DP.cur) fitVb(DP.cur, ms === undefined ? 700 : ms); }
  // a new framing for the beat (e.g. a panel opened beneath the plan), flown to unless a neighbourhood is open (closing it returns here)
  function planHome(v, ms) {
    deckPlan(); DP.home = v;
    if (!DP.zone) { DP.cur = v; DP.ph.setHome(...v); fitVb(v, ms === undefined ? 700 : ms); }
  }
  // a list of [data-nb] rows: hover one to pick out its neighbourhood on the plan (outline, seats)
  function nbHover(list) {
    deckPlan();
    $$("[data-nb]", list).forEach((row) => {
      const z = DP.P.zones.find((q) => q.n === row.dataset.nb);
      row.onmouseenter = () => { DP.root.classList.add("focus"); $$(`.dx-nb [data-nb="${row.dataset.nb}"], .dx-lab [data-nb="${row.dataset.nb}"]`, DP.root).forEach((p) => p.classList.add("hi")); if (z) DP.ph.highlight("team", z.id); };
      row.onmouseleave = () => { DP.root.classList.remove("focus"); $$(".dx-marks .hi", DP.root).forEach((p) => p.classList.remove("hi")); DP.ph.clear(); };
    });
  }

  /* ======================= the walk: every space, OP 01 then OP 02 =======================
     One slide per space (class "walk"); its configuration is its own data-walk attribute:
       {"n": name, "sub": subtitle, "q": the Loop's words, "p": a line, "r": [render per beat], "kp": [deck slide of each keyplan], "tags": [...]}.
     The render fills the window with a slow drift; the name block, the words, the OP tag and the keyplan (the deck's plan with its
     maroon camera mark) sit on it. */
  const AR = {};   // render aspect ratios, read once loaded
  const WKUI = $$("#walk-ui > *"), PHL = LAYERS.photo;
  const isWalk = (s) => !!s && s.classList.contains("walk");
  // music: fades in on the walk, out when you leave; a browser only plays after a click or key, so it retries on the next one
  const AUD = {
    el: $("#wk-audio"), muted: false, want: false, fadeT: null, level: 0.35,
    fade(to, ms, then) {
      const a = this.el, from = a.volume, n = 16; let i = 0;
      clearInterval(this.fadeT);
      this.fadeT = setInterval(() => { a.volume = clamp(from + (to - from) * (++i / n), 0, 1); if (i >= n) { clearInterval(this.fadeT); if (then) then(); } }, ms / n);
    },
    play() {
      this.want = true; if (this.muted) return;
      const a = this.el;
      if (!a.paused) { this.fade(this.level, 600); return; }
      a.volume = 0; a.play().then(() => this.fade(this.level, 800)).catch(() => { /* not allowed yet */ });
    },
    silence() { if (!this.el.paused) this.fade(0, 500, () => this.el.pause()); },
    stop() { this.want = false; this.silence(); },
  };
  ["keydown", "pointerdown"].forEach((ev) => document.addEventListener(ev, () => { if (AUD.want && !AUD.muted && AUD.el.paused) AUD.play(); }));
  $("#wk-mute").onclick = () => { AUD.muted = !AUD.muted; $("#wk-mute").classList.toggle("muted", AUD.muted); if (AUD.muted) AUD.silence(); else AUD.play(); };
  const LVL = $("#wk-level");
  LVL.addEventListener("input", () => {
    AUD.level = LVL.value / 100;
    if (AUD.level > 0 && AUD.muted) { AUD.muted = false; AUD.play(); }
    $("#wk-mute").classList.toggle("muted", AUD.muted || AUD.level === 0);
    if (!AUD.el.paused && !AUD.muted) { clearInterval(AUD.fadeT); AUD.el.volume = AUD.level; }
  });
  ["change", "pointerup"].forEach((ev) => LVL.addEventListener(ev, () => LVL.blur()));
  // pan mode: the render grows and follows a drag, never past its edges
  const PAN = { on: false, x: 0, y: 0, drag: null, s: 1.35 };
  function panTo(x, y) {
    const c = PHOTO.cur && $(".cover", PHOTO.cur);
    if (c) { const w = c.offsetWidth * PAN.s, h = c.offsetHeight * PAN.s, mx = Math.max(0, (w - innerWidth) / 2), my = Math.max(0, (h - innerHeight) / 2); x = clamp(x, -mx, mx); y = clamp(y, -my, my); }
    PAN.x = x; PAN.y = y; PHL.style.setProperty("--px", x + "px"); PHL.style.setProperty("--py", y + "px");
  }
  function setPan(on) { PAN.on = on; PHL.classList.toggle("pan", on); $("#wk-pan").classList.toggle("on", on); panTo(0, 0); }
  $("#wk-pan").onclick = () => setPan(!PAN.on);
  PHL.addEventListener("pointerdown", (e) => { if (!PAN.on || e.button !== 0) return; e.preventDefault(); PAN.drag = { x0: e.clientX, y0: e.clientY, px: PAN.x, py: PAN.y }; PHL.classList.add("dragging"); });
  addEventListener("pointermove", (e) => { const d = PAN.drag; if (d) panTo(d.px + (e.clientX - d.x0), d.py + (e.clientY - d.y0)); });
  addEventListener("pointerup", () => { if (PAN.drag) { PAN.drag = null; PHL.classList.remove("dragging"); } });
  let kpOn = true;
  $("#wk-kp").onclick = () => { kpOn = !kpOn; $("#wk-kp").classList.toggle("on", kpOn); document.body.classList.toggle("kp-off", !kpOn); };
  // the keyplan: the deck's keyplan image, framed around its camera mark (a little wider than the deck's crop)
  function keyplan(slideNo) {
    const k = (window.ACKO_KP || {})[slideNo], box = $("#wk-kpimg"), inner = $(".wk-kp-in", box), img = $("img", inner), cam = $(".wk-cam", inner);
    if (!k) { box.style.display = "none"; return; }
    box.style.display = "";
    const place = () => {
      const W = box.clientWidth, Hh = box.clientHeight, iw = img.naturalWidth, ih = img.naturalHeight;
      if (!W || !iw) return;
      const vw = ((k.view[2] - k.view[0]) / 100) * iw, vh = ((k.view[3] - k.view[1]) / 100) * ih;
      const s = Math.min(W / (vw * 1.5), Hh / (vh * 1.5)), w = iw * s, h = ih * s;
      const cx = (k.x / 100) * w, cy = (k.y / 100) * h;
      const tx = clamp(W / 2 - cx, W - w, 0), ty = clamp(Hh / 2 - cy, Hh - h, 0);
      inner.style.width = w + "px"; inner.style.transform = `translate(${tx}px, ${ty}px)`;
      cam.style.left = cx + "px"; cam.style.top = cy + "px"; cam.style.setProperty("--rot", k.rot + "deg");
    };
    if (img.dataset.key !== k.img) { img.dataset.key = k.img; img.onload = place; img.src = asset("assets/img/" + k.img + ".webp"); } else place();
  }
  function walkShow(s, k) {
    const key = s.r[k - 1];
    const f = PHOTO.show(key, { kb: true, ar: AR[key] || 2.1 });
    if (!AR[key]) { const im = new Image(); im.onload = () => { AR[key] = im.naturalWidth / im.naturalHeight; $$(".cover", f).forEach((c) => (c.dataset.ar = AR[key])); layoutCovers(); }; im.src = PHOTO.src(key); }
    world("photo"); shade("photo");
    $$("#wk-opt span").forEach((b, i) => b.classList.toggle("on", i === k - 1));
    keyplan((s.kp || [])[k - 1]);
    if (AUD.want && AUD.el.paused) AUD.play();
  }
  function walkHook(sc) {
    let s = {};
    try { s = JSON.parse(sc.dataset.walk || "{}"); } catch (e) { console.error(`${sc.id}: data-walk is not valid JSON`, e); }
    s.r = s.r || [];
    return {
      enter() {
        WKUI.forEach((n) => sc.appendChild(n));
        document.body.classList.add("in-walk");
        const deck = scenes.filter((x) => isWalk(x) && trackOf(x) === trackOf(sc)), at = deck.indexOf(sc);
        $("#wk-nav").innerHTML = deck.length > 1 ? deck.map((x, i) => `<button type="button" data-to="${x.id}"${x === sc ? ' class="on"' : ""}><b>${String(i + 1).padStart(2, "0")}</b>${x.dataset.title}</button>`).join("") : "";
        $$("#wk-nav button").forEach((b) => (b.onclick = () => go(sceneIx(b.dataset.to), 1)));
        $("#wk-n").innerHTML = `${s.n || sc.dataset.title}<small>${s.sub || ""}</small>`;
        $("#wk-q").textContent = s.q || ""; $("#wk-p").textContent = s.p || "";
        $("#wk-opt").innerHTML = s.r.length > 1 ? (s.tags || ["OP 01", "OP 02"]).map((t) => `<span>${t}</span>`).join("") : "";
        $("#wk-kick").textContent = `Visual Direction · ${String(at + 1).padStart(2, "0")} / ${String(deck.length).padStart(2, "0")}`;
        AUD.play();
      },
      step(k) { if (s.r[k - 1]) walkShow(s, k); },
      leave() {
        setPan(false); document.body.classList.remove("in-walk");
        setTimeout(() => { if (!isWalk(scenes[state.idx])) AUD.stop(); }, 0);
      },
    };
  }
  /* campus palettes (class "palette", data-renders="a,b,c"): 1 the board builds tile by tile; 2–4 the renders, full bleed */
  function paletteHook(sc) {
    const renders = (sc.dataset.renders || "").split(",").filter(Boolean);
    return {
      enter() { plain(); },
      step(k) {
        if (k === 1 || !renders[k - 2]) { world("none"); shade(""); reveal($(".pl-board", sc), 80); sc.classList.remove("rendered"); return; }
        sc.classList.add("rendered");
        PHOTO.show(renders[k - 2], { kb: true, ar: 2.357 }); world("photo"); shade("photo");
      },
    };
  }
  /* deck pages rebuilt as HTML (class "vpage"): pictures, then words, one after another; [data-count] numbers count up */
  function vpageHook(sc) {
    return { enter() { plain(); reveal($(".page", sc), 80); $$("[data-count]", sc).forEach((e, i) => later(() => countUp(e, 1500), 1100 + i * 120)); } };
  }

  /* ======================= the slides' own scripts ======================= */
  const kit = {
    $, $$, clamp, later, clearTimers, raf2, reduced, asset,
    reveal, countUp, typeWords, drawPath, inPoly,
    plain, world, shade, PHOTO, layoutCovers, lightbox, lightboxOff,
    go, next, prev, setStep, state, scenes, sceneIx, trackIdx,
    plan: { deckPlan, planOn, planOff, planEgress, planView, vbFor, fitVb, nbHover, focusZone, planNb, planFill, planHover, planReset, planHome, layers: planLayers, keyplan: zoneKey, onZoneClick: (fn) => { deckPlan(); DP.onZone = fn || null; },
            get zone() { return DP.zone; }, get view() { return DP.ph ? DP.ph.view : null; }, get hoverOn() { return HOVER; }, get root() { return DP.root; }, get data() { return window.PLAN_DXF; } },
  };
  for (const id in FACTORIES) {
    if (!document.getElementById(id)) continue;
    try { H[id] = FACTORIES[id](kit) || {}; } catch (e) { console.error(`${id}: its script failed to start`, e); }
  }
  // slides with no script of their own: the shared behaviour of their class
  scenes.forEach((sc) => {
    if (H[sc.id]) return;
    if (sc.classList.contains("walk")) H[sc.id] = walkHook(sc);
    else if (sc.classList.contains("palette")) H[sc.id] = paletteHook(sc);
    else if (sc.classList.contains("vpage")) H[sc.id] = vpageHook(sc);
    else H[sc.id] = { enter() { plain(); } };
  });

  /* ======================= start ======================= */
  const fromHash = () => {
    const m = (location.hash || "").match(/^#([\w-]+)\/(\d+)/), i = m ? sceneIx(m[1]) : -1;
    go(i >= 0 ? i : 0, i >= 0 ? +m[2] : 1);
  };
  addEventListener("hashchange", () => { if (location.hash !== "#" + scenes[state.idx].id + "/" + state.step) fromHash(); });
  fromHash();
  tick();
  Object.assign(window.ACKO, { go, setStep, setTheme, state, H, kit });
  }
})();
