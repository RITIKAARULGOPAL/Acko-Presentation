/* ACKO · The Loop — SKV's design presentation as one continuous journey (engine forked from the Mitigata presentation).
   A persistent WORLD (vector map · plan · photographs) lives behind the slides; each slide is a 16:9 page in deck points.
   Keys: → / PageDown / Space next beat · ← / PageUp previous · O index · N notes · F fullscreen · B blank · L laser. */
(function () {
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
    src(key) { return /[./]/.test(key) ? key : `assets/img/${key}.webp`; },
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
  /* the section mark (top right): the deck's five sections as beads along one loop — past ink, now purple, next pale;
     hover lists them, a click opens a section */
  const TOPICS = { main: [["1", "Design concept"], ["2", "Design strategy"], ["3", "Visual direction"], ["4", "Value addition"], ["5", "Space planning"]], appendix: [["A", "Appendix"]], skv: [["0", "About SKV"]] };
  const firstOf = (p) => scenes.findIndex((s) => s.dataset.part === p);
  function topicMark(track) {
    const tp = TOPICS[track] || TOPICS.main, n = tp.length;
    const xs = tp.map((_, k) => (n === 1 ? 30 : 6 + (48 * k) / (n - 1)));
    $("#topic-mark svg").innerHTML = `<path class="tm-loop" d="M6 8C6 1 18 1 30 8S54 15 54 8 42 1 30 8 6 15 6 8"/>` +
      tp.map(([p], k) => `<circle class="tm-bead" data-part="${p}" cx="${xs[k]}" cy="8" r="3.4"/>`).join("");
    $("#tm-list").innerHTML = (track === "main" ? `<button type="button" data-part="cover"><b>—</b>Cover</button>` : "") +
      tp.map(([p, nm], k) => `<button type="button" data-part="${p}"><b>${n > 1 ? String(k + 1).padStart(2, "0") : ""}</b>${nm}</button>`).join("");
    $$("#topic-mark [data-part]").forEach((el) => (el.onclick = (e) => {
      e.stopPropagation(); if (document.activeElement) document.activeElement.blur();
      if (el.dataset.part === "cover") state.t0 = null;
      go(firstOf(el.dataset.part), 1);
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
    const h = "#" + sc.id + "/" + state.step;
    if (location.hash !== h) { try { location.replace(h); } catch (e) { /* file:// */ } }
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

  /* ======================= chapters ======================= */
  const H = {};
  function hook(sc, ev, arg) { const h = sc && H[sc.id]; if (h && h[ev]) h[ev](arg, sc); }
  // a page with no world behind it: the slide is the whole picture
  const plain = () => { world("none"); shade(""); };
  // .rv / .rv-i children come in one after another; restart by removing and re-adding .go
  function reveal(el, delay) { if (!el) return; el.classList.remove("go"); void el.offsetWidth; later(() => el.classList.add("go"), delay || 60); }
  function countUp(el, ms) {
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

  /* ---- About SKV (SKV's own deck, unchanged from the Mitigata presentation) ---- */
  const LOGOS = ("Google,Amazon,Samsung,PepsiCo,adidas,Godrej,Aramco,Shell,Honeywell,Qualcomm,GlobalLogic,KPMG,H&M,Max Healthcare,Amway,SYSTRA,PwC,Levi's," +
    "McDermott,DLF,DXC Technology,University of Cambridge,M&S,CNH,Perfetti Van Melle,Kia,The Times of India,MetLife,Cadence,Cyril Amarchand Mangaldas,dunnhumby,Airtel," +
    "MG Motor,Hindustan Times,Concentrix,Spark Minda,Vedanta,British Council,Aon,Fortis,Hero MotoCorp,NTT,Amity University,STL,Macquarie,SRF,BIBA,Synopsys,Adani,ReNew," +
    "Muthoot Finance,Grant Thornton,Stryker,Target").split(",");
  const n2 = (i) => String(i + 1).padStart(2, "0");
  if ($("#skv-logos")) $("#skv-logos").innerHTML = LOGOS.map((n, i) => `<div data-in="${1 + Math.floor(i / 9)}"><img src="assets/img/skv/logo-${n2(i)}.webp" alt="${n.replace(/&/g, "&amp;")}"></div>`).join("");
  if ($("#skv-caps")) $("#skv-caps").innerHTML = LOGOS.slice(0, 10).map((_, i) => `<div data-in="1" style="background-image:url(assets/img/skv/project-${n2(i)}.webp)"></div>`).join("");
  // the deck's animated ASCII data-field, redrawn live (About SKV's opening beat)
  const makeAscii = (cv) => ({
    cv, on: false, last: 0, color: null, GLYPHS: " .:-=+itl1I/T7M#",
    start() { if (!this.cv || this.on) return; this.on = true; this.cv.classList.add("on"); this.frame(performance.now()); },
    stop() { if (!this.cv) return; this.on = false; this.cv.classList.remove("on"); cancelAnimationFrame(this.raf); },
    frame(now) {
      if (!this.on) return;
      this.raf = requestAnimationFrame((t) => this.frame(t));
      if (now - this.last < 70) return;
      this.last = now;
      const cv = this.cv, dpr = Math.min(2, devicePixelRatio || 1), W = cv.clientWidth, Hh = cv.clientHeight;
      if (!W || !Hh) return;
      if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(Hh * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr); }
      const g = cv.getContext("2d"), fs = 12, cw = fs * 0.62, ch = fs * 1.18, t = reduced ? 0 : now / 1000;
      if (!this.color) this.color = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#5222d0";
      g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, Hh);
      g.font = `400 ${fs}px "Lexend", sans-serif`; g.fillStyle = this.color; g.textBaseline = "top";
      const cols = Math.ceil(W / cw), rows = Math.ceil(Hh / ch), G = this.GLYPHS, n = G.length - 1;
      for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
        const a = Math.sin(x * 0.11 + t * 0.7) + Math.sin(y * 0.23 - t * 0.5) + Math.sin((x + y * 1.7) * 0.045 + t * 0.35);
        const cloud = Math.sin(x * 0.035 - t * 0.12) * Math.cos(y * 0.09 + t * 0.1);
        const v = Math.max(0, Math.min(1, ((a / 3 + 1) / 2) * 0.9 + cloud * 0.55 - 0.08));
        const c = G[Math.floor(Math.pow(v, 1.35) * n)];
        if (c === " ") continue;
        g.globalAlpha = 0.2 + 0.8 * v; g.fillText(c, x * cw, y * ch);
      }
      g.globalAlpha = 1;
    },
  });
  const ASCII = makeAscii($("#skv-ascii"));
  H["s-skv"] = {
    enter() { plain(); },
    step(k) {
      const board = $(`#s-skv .skv-board[data-only="${k}"]`), seen = {};
      if (!board) return;
      const delay = (g) => 80 + g * 260;
      $$("[data-in]", board).forEach((e) => {
        e.classList.remove("in");
        const g = +e.dataset.in, n = (seen[g] = (seen[g] || 0) + 1) - 1;
        later(() => e.classList.add("in"), delay(g) + n * (k === 6 ? 26 : 70));
      });
      $$("[data-count]", board).forEach((e) => later(() => countUp(e, 1500), delay(+e.closest("[data-in]").dataset.in)));
      if (k === 1) ASCII.start(); else ASCII.stop();
    },
    leave() { ASCII.stop(); },
  };

  /* ---- cover (slide 1): the facts come up; a thin Möbius line draws itself over the stairs ---- */
  // the edge of a Möbius strip (one curve, twice round), seen in perspective
  function mobiusEdge(R, w, tilt, turn) {
    const pts = [];
    for (let i = 0; i <= 720; i++) {
      const u = (i / 720) * 4 * Math.PI, r = R + w * Math.cos(u / 2);
      let x = r * Math.cos(u + turn), y = r * Math.sin(u + turn), z = w * Math.sin(u / 2);
      const y2 = y * Math.cos(tilt) - z * Math.sin(tilt), z2 = y * Math.sin(tilt) + z * Math.cos(tilt), k = 260 / (260 + z2 * 2.2);
      pts.push([(x * k).toFixed(1), (y2 * k).toFixed(1)]);
    }
    return "M" + pts.map((q) => q.join(" ")).join("L");
  }
  H["s-cover"] = {
    enter(_, sc) {
      plain(); reveal($(".page.rv", sc), 200);
      const p = $(".cv-mobius path", sc);
      if (p && !p.getAttribute("d")) p.setAttribute("d", mobiusEdge(62, 22, 1.08, 0.35));
      if (p) { p.style.animation = "none"; p.style.setProperty("--len", Math.ceil(p.getTotalLength())); void p.getBoundingClientRect(); p.style.animation = ""; }
    },
  };
  /* ---- team (slide 2) ---- */
  H["s-team"] = { enter(_, sc) { plain(); reveal($(".tm-people", sc), 150); } };
  /* ---- workplace aspiration (slide 3): the three tiles rise in, then the handwritten line ---- */
  H["s-aspiration"] = { enter(_, sc) { plain(); reveal($(".page", sc), 100); } };
  /* ---- what defines ACKO (slide 4): the five values open like shutters; then, slowly, each strip turns to its second picture
     (the deck's click swaps the first) ---- */
  H["s-acko"] = {
    enter(_, sc) {
      plain(); const strips = $$(".val-strip", sc); strips.forEach((s) => s.classList.remove("swap"));
      reveal($(".page", sc), 100);
      strips.forEach((s, i) => later(() => s.classList.add("swap"), 4200 + i * 900));
    },
  };
  /* ---- the journey (slide 5): ① why an insurance, over five faces of protection; ② we respect the journey — the timeline
     draws along its line, the milestones come up, then the founder's words ---- */
  H["s-journey"] = {
    enter() { plain(); },
    step(k, sc) {
      clearTimers();
      sc.classList.toggle("b2", k === 2);
      if (k === 1) { reveal($(".jr-collage", sc), 200); return; }
      const ms = $$(".jr-ms", sc), line = $(".jr-line", sc);
      line.classList.remove("go"); ms.forEach((m) => m.classList.remove("go"));
      later(() => line.classList.add("go"), 500);
      ms.forEach((m, i) => later(() => m.classList.add("go"), 700 + i * 230));
      typeWords($(".jr-quote q", sc), 90, 900 + ms.length * 230);
    },
  };
  /* ---- the challenge → the solution (slides 6 → 7) ---- */
  // the people of two offices: two clusters that drift towards each other (1) and then become one loop (2)
  const CH = { n: 64 };
  function chDots(svg) {
    if (svg.children.length) return;
    let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const out = [];
    for (let i = 0; i < CH.n; i++) {
      const a = i < CH.n / 2 ? [330, 260] : [1530, 250], ang = rnd() * Math.PI * 2, rr = Math.sqrt(rnd()) * 130;
      const from = [a[0] + Math.cos(ang) * rr, a[1] + Math.sin(ang) * rr * 0.62];
      const near = [from[0] + (i < CH.n / 2 ? 260 : -260), from[1]];
      // on the loop: a figure of eight across the middle of the page
      const t = (i / CH.n) * Math.PI * 2, loop = [960 + 520 * Math.sin(t), 270 + 150 * Math.sin(t) * Math.cos(t) * 1.6];
      out.push(`<circle r="${(5 + rnd() * 4).toFixed(1)}" cx="0" cy="0" data-a="${from.map(Math.round)}" data-b="${near.map(Math.round)}" data-c="${loop.map(Math.round)}" style="transform:translate(${from[0]}px,${from[1]}px)"/>`);
    }
    svg.innerHTML = `<g class="ch-people">${out.join("")}</g>` +
      `<text x="330" y="470" text-anchor="middle" class="ch-l a">TWO EXISTING LOCATIONS</text><text x="1530" y="470" text-anchor="middle" class="ch-l a"></text>` +
      `<text x="960" y="520" text-anchor="middle" class="ch-l b">ONE PLACE</text>`;
  }
  function chMove(svg, key, ms) {
    $$("circle", svg).forEach((c, i) => {
      const [x, y] = c.dataset[key].split(",").map(Number);
      c.style.transition = ms ? `transform ${ms}ms cubic-bezier(.45,.05,.3,1) ${Math.round((i % 16) * 25)}ms` : "none";
      c.style.transform = `translate(${x}px,${y}px)`;
    });
  }
  H["s-challenge"] = {
    enter(_, sc) { plain(); chDots($("#ch-dots", sc)); },
    step(k, sc) {
      const pg = $(".page", sc), svg = $("#ch-dots", sc);
      pg.classList.toggle("solved", k === 2);
      if (k === 1) { chMove(svg, "a", 0); raf2(() => chMove(svg, "b", 2800)); }
      else chMove(svg, "c", 2400);
      reveal($(".ch-words", sc), 100);
    },
  };
  /* ---- memories (slide 8): a dotted path across the campus; the six moments come up along it ---- */
  H["s-memories"] = {
    enter(_, sc) {
      plain();
      const stops = $$(".mem-stop", sc); stops.forEach((s) => s.classList.remove("on"));
      const path = $(".mem-path path", sc); drawPath(path, 5200, 400);
      stops.forEach((s, i) => later(() => s.classList.add("on"), 700 + i * 820));
      reveal($(".mem-h", sc), 100);
      $$(".mem-h span", sc).forEach((e, i) => e.style.setProperty("--i", i * 4));
    },
  };
  /* ---- what if (slide 9): the question, word by word ---- */
  H["s-whatif"] = { enter(_, sc) { plain(); typeWords($(".wi-q", sc), 120, 300); } };

  /* ---- the Möbius (slide 10): a live white strip, softly lit, turning slowly — Acko's own mark, one continuous surface ---- */
  const MOB = { r: null };
  function mobius(host) {
    if (MOB.r) { host.appendChild(MOB.r.domElement); return; }
    const THREE = window.THREE; if (!THREE) return;
    const r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    r.setPixelRatio(Math.min(2, devicePixelRatio || 1)); r.setClearColor(0x000000, 0);
    host.appendChild(r.domElement);
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(24, 1, 0.1, 100);
    cam.position.set(0, 6.6, 5.6); cam.lookAt(0, -0.05, 0.1);
    // the strip: u around the loop, v across the band (a flat, wide ribbon as in the deck's render)
    const NU = 360, NV = 24, R = 1.95, Wd = 0.52, T = 0.06;
    const pos = [], idx = [];
    const pt = (u, v, off) => {
      const c = Math.cos(u / 2), s = Math.sin(u / 2);
      const x = (R + v * c) * Math.cos(u), z = (R + v * c) * Math.sin(u), y = v * s;
      // the surface normal, for the thickness: d/du × d/dv
      const du = [-(R + v * c) * Math.sin(u) - 0.5 * v * s * Math.cos(u), 0.5 * v * c, (R + v * c) * Math.cos(u) - 0.5 * v * s * Math.sin(u)];
      const dv = [c * Math.cos(u), s, c * Math.sin(u)];
      let n = [du[1] * dv[2] - du[2] * dv[1], du[2] * dv[0] - du[0] * dv[2], du[0] * dv[1] - du[1] * dv[0]];
      const l = Math.hypot(...n); n = n.map((q) => q / l);
      return [x + n[0] * off, y + n[1] * off, z + n[2] * off];
    };
    for (let side = 0; side < 2; side++) {
      const base = pos.length / 3, off = side ? -T / 2 : T / 2;
      for (let i = 0; i <= NU; i++) for (let j = 0; j <= NV; j++) pos.push(...pt((i / NU) * Math.PI * 2, -Wd + (2 * Wd * j) / NV, off));
      for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) {
        const a = base + i * (NV + 1) + j, b = a + NV + 1;
        if (side) idx.push(a, a + 1, b, b, a + 1, b + 1); else idx.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: 0xe6e1f0, roughness: 0.55, metalness: 0.0, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(g, mat); scene.add(mesh);
    // its one edge (twice round), drawn as a fine lavender line so the strip reads on the white page
    const ep = [];
    for (let i = 0; i <= 1440; i++) ep.push(...pt((i / 1440) * Math.PI * 4, Wd, 0));
    const eg = new THREE.BufferGeometry(); eg.setAttribute("position", new THREE.Float32BufferAttribute(ep, 3));
    mesh.add(new THREE.Line(eg, new THREE.LineBasicMaterial({ color: 0x8f78dc, transparent: true, opacity: 0.85 })));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x5a5175, 0.7));
    const key = new THREE.DirectionalLight(0xffffff, 0.85); key.position.set(-5, 6, 4); scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 0.25); fill.position.set(5, 2, 6); scene.add(fill);
    const rim = new THREE.DirectionalLight(0xc9b3f3, 0.7); rim.position.set(4, -3, -5); scene.add(rim);
    MOB.r = r; MOB.scene = scene; MOB.cam = cam; MOB.mesh = mesh;
  }
  function mobiusRun(host) {
    const r = MOB.r; if (!r) return;
    const t0 = performance.now();
    const loop = (now) => {
      if (document.body.dataset.scene !== "s-mobius") return;
      const W = host.clientWidth, Hh = host.clientHeight;
      if (W && Hh && (r.domElement.width !== Math.round(W * r.getPixelRatio()) || r.domElement.height !== Math.round(Hh * r.getPixelRatio()))) { r.setSize(W, Hh, false); MOB.cam.aspect = W / Hh; MOB.cam.updateProjectionMatrix(); }
      const t = reduced ? 0 : (now - t0) / 1000;
      MOB.mesh.rotation.y = -0.6 + 0.28 * Math.sin(t * 0.18);   // a slow sway, so the copy always sits in the loop
      MOB.mesh.rotation.x = 0.06 * Math.sin(t * 0.4);
      r.render(MOB.scene, MOB.cam);
      MOB.raf = requestAnimationFrame(loop);
    };
    cancelAnimationFrame(MOB.raf); MOB.raf = requestAnimationFrame(loop);
  }
  H["s-mobius"] = {
    enter(_, sc) { plain(); const host = $(".mb-stage", sc); mobius(host); mobiusRun(host); reveal($(".mb-copy", sc), 600); },
    leave() { cancelAnimationFrame(MOB.raf); },
  };

  /* ---- the Loop (slides 11–12): ① welcome to the Loop — people and trees along the line; ② the lavender ribbon draws from left
     to right and the seven stops come up as it reaches them, each with what it should feel like ---- */
  // the seven stops of slide 12: [name, words, dot x/y, label x/y] in % of the page
  const LOOP_STOPS = [
    ["Arrival", "I feel welcomed", [2.4, 38.9], [6.1, 26]], ["Cafe", "Hey We finally meet !", [17, 46.8], [14, 35.4]],
    ["Board Room", "This is my big moment", [40.3, 43.9], [46.3, 24.5]], ["Meeting Rooms", "My Impact", [55.7, 45.7], [62.7, 23.2]],
    ["Collab", "Wow, worth the commute", [76.1, 45.4], [79.3, 23.2]], ["Work", "These are my folks!", [96.8, 46.8], [93.6, 30.5]],
    ["Wellness", "They thought of me too!", [78.4, 70], [90.2, 66.2]],
  ];
  function loopStops(sc) {
    const host = $(".lp-stops", sc); if (host.children.length) return;
    host.innerHTML = LOOP_STOPS.map(([n, q, d, l]) => `<div class="lp-stop" style="left:${d[0]}%;top:${d[1]}%"><i></i>` +
      `<div class="lab" style="left:calc(${l[0] - d[0]} * var(--pw) / 100);top:calc(${l[1] - d[1]} * var(--ph) / 100)"><b>${n}</b><q>${q}</q></div></div>`).join("");
    // a dotted leader from each label to its dot
    $(".lp-leads", sc).innerHTML = LOOP_STOPS.map(([, , d, l], i) => {
      const x1 = l[0] * 19.2, y1 = (l[1] + (l[1] < d[1] ? 5 : -0.5)) * 10.8, x2 = d[0] * 19.2, y2 = d[1] * 10.8;
      return `<path data-k="${i}" d="M${x1} ${y1}Q${x1} ${(y1 + y2) / 2} ${x2} ${y2}"/>`;
    }).join("");
  }
  H["s-loop"] = {
    enter(_, sc) { plain(); loopStops(sc); reveal($(".lp-cuts", sc), 100); },
    step(k, sc) {
      clearTimers();
      const rib = $(".lp-ribbon", sc), stops = $$(".lp-stop", sc);
      $$(".lp-leads path", sc).forEach((l) => l.classList.remove("on"));
      if (k === 1) { rib.style.setProperty("--rv", "0%"); stops.forEach((s) => s.classList.remove("on")); return; }
      const t0 = performance.now(), MS = reduced ? 1 : 4200;
      stops.forEach((s) => s.classList.remove("on"));
      const run = (now) => {
        if (document.body.dataset.scene !== "s-loop" || state.step !== 2) return;
        const e = Math.min(1, (now - t0) / MS), v = (1 - Math.pow(1 - e, 2)) * 106;
        rib.style.setProperty("--rv", v + "%");
        stops.forEach((s, i) => { if (parseFloat(s.style.left) <= v - 2 && !s.classList.contains("on")) { s.classList.add("on"); const l = $(`.lp-leads [data-k="${i}"]`, sc); if (l) l.classList.add("on"); } });
        if (e < 1) requestAnimationFrame(run);
      };
      requestAnimationFrame(run);
    },
  };
  /* ---- campus strategy (slide 13): the deck's animated axo of the floor (replaced by the DXF's axo when it arrives) ---- */
  H["s-strategy"] = { enter(_, sc) { plain(); reveal($(".page", sc), 100); } };

  /* ---- thank you: the Appendix and About SKV from here ---- */
  H["s-thanks"] = {
    enter(_, sc) {
      plain(); reveal($(".page", sc), 100);
      $("#to-appendix").onclick = () => go(trackIdx("appendix")[0], 1);
      $("#to-skv").onclick = () => go(sceneIx("s-skv"), 1);
    },
  };

  /* ---- a deck page as it is, until its slide is rebuilt ---- */
  $$(".scene.deck").forEach((sc) => { if (!H[sc.id]) H[sc.id] = { enter() { plain(); } }; });

  /* ======================= the walk: every space, OP 01 then OP 02 =======================
     One slide per space (s-w-*); its beats are its renders. The render fills the window with a slow drift; the name block,
     the Loop's words for the space, the OP tag and the keyplan (the deck's plan with its maroon camera mark) sit on it. */
  const WALK = {
    "s-w-board": { n: "State Room", sub: "Boardroom · 32 pax", q: "This is my big moment", r: ["r-board-op1", "r-board-op2"], kp: [24, 25] },
    "s-w-dept": { n: "Departmental Room", sub: "20 pax meeting room", q: "My impact", r: ["r-dept-op1", "r-dept-op2"], kp: [26, 27] },
    "s-w-sprint": { n: "Quick Sprint Room", sub: "4 pax meeting room", q: "My impact", r: ["r-sprint-op1", "r-sprint-op2"], kp: [28, 29] },
    "s-w-arena": { n: "Work Arena", sub: "Neighbourhood", q: "These are my folks!", r: ["r-arena-op1", "r-arena-op2"], kp: [30, 31] },
    "s-w-arena2a": { n: "Work Arena", sub: "Neighbourhood · Option 2A", q: "These are my folks!", r: ["r-arena2a-1", "r-arena2a-2"], kp: [32, 33], tags: ["View 1", "View 2"] },
    "s-w-library": { n: "Work Arena", sub: "Library", q: "These are my folks!", r: ["r-library"], kp: [34] },
    "s-w-garden": { n: "The Acker Garden", sub: "Work arena", q: "Wow, worth the commute", r: ["r-garden-op1", "r-garden-op2"], kp: [35, 36] },
    "s-w-exec": { n: "Executive Room", sub: "Executive corner cabin", r: ["r-exec"], kp: [37] },
    "s-w-cafe1": { n: "Cafe", sub: "View 1", q: "Hey, we finally meet!", r: ["r-cafe1-op1", "r-cafe1-op2"], kp: [38, 40] },
    "s-w-cafe2": { n: "Cafe", sub: "View 2", q: "Hey, we finally meet!", r: ["r-cafe2-op1", "r-cafe2-op2"], kp: [39, 41] },
    "s-w-coffee": { n: "Coffee Point", sub: "Coffee corner", q: "Hey, we finally meet!", r: ["r-coffee"], kp: [42] },
    "s-w-mothers": { n: "Mothers Room", sub: "A space for all moms @ Acko", q: "They thought of me too!", p: "Designed with a soothing palette that keeps calm amid a busy day.", r: ["r-mothers"], kp: [43] },
    "s-w-zen": { n: "Zen Room", sub: "A space to unwind", q: "They thought of me too!", p: "A night-sky optic-fibre ceiling in the brand's hues: peace, and a little curiosity.", r: ["r-zen"], kp: [44] },
    "s-w-studio": { n: "Studio Room", sub: "A space for Acko's voice", r: ["r-studio"], kp: [45] },
  };
  const AR = {};   // render aspect ratios, read once loaded
  const WKUI = $$("#walk-ui > *"), PHL = LAYERS.photo;
  let WK = null;
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
      const vw = (k.view[2] - k.view[0]) / 100 * iw, vh = (k.view[3] - k.view[1]) / 100 * ih;
      const s = Math.min(W / (vw * 1.5), Hh / (vh * 1.5)), w = iw * s, h = ih * s;
      const cx = (k.x / 100) * w, cy = (k.y / 100) * h;
      const tx = clamp(W / 2 - cx, W - w, 0), ty = clamp(Hh / 2 - cy, Hh - h, 0);
      inner.style.width = w + "px"; inner.style.transform = `translate(${tx}px, ${ty}px)`;
      cam.style.left = cx + "px"; cam.style.top = cy + "px"; cam.style.setProperty("--rot", k.rot + "deg");
    };
    if (img.getAttribute("src") !== `assets/img/${k.img}.webp`) { img.onload = place; img.src = `assets/img/${k.img}.webp`; } else place();
  }
  function walkShow(s, k) {
    const key = s.r[k - 1];
    const f = PHOTO.show(key, { kb: true, ar: AR[key] || 2.1 });
    if (!AR[key]) { const im = new Image(); im.onload = () => { AR[key] = im.naturalWidth / im.naturalHeight; $$(".cover", f).forEach((c) => (c.dataset.ar = AR[key])); layoutCovers(); }; im.src = PHOTO.src(key); }
    world("photo"); shade("photo");
    $$("#wk-opt span").forEach((b, i) => b.classList.toggle("on", i === k - 1));
    keyplan(s.kp[k - 1]);
    if (AUD.want && AUD.el.paused) AUD.play();
  }
  function walkHook(id) {
    const s = WALK[id];
    return {
      enter(_, sc) {
        WK = sc; WKUI.forEach((n) => sc.appendChild(n));
        document.body.classList.add("in-walk");
        const deck = scenes.filter((x) => isWalk(x) && trackOf(x) === trackOf(sc)), at = deck.indexOf(sc);
        $("#wk-nav").innerHTML = deck.map((x, i) => `<button type="button" data-to="${x.id}"${x === sc ? ' class="on"' : ""}><b>${String(i + 1).padStart(2, "0")}</b>${x.dataset.title}</button>`).join("");
        $$("#wk-nav button").forEach((b) => (b.onclick = () => go(sceneIx(b.dataset.to), 1)));
        $("#wk-n").innerHTML = `${s.n}<small>${s.sub || ""}</small>`;
        $("#wk-q").textContent = s.q || ""; $("#wk-p").textContent = s.p || "";
        $("#wk-opt").innerHTML = s.r.length > 1 ? (s.tags || ["OP 01", "OP 02"]).map((t) => `<span>${t}</span>`).join("") : "";
        $("#wk-kick").textContent = `Visual Direction · ${String(at + 1).padStart(2, "0")} / ${String(deck.length).padStart(2, "0")}`;
        AUD.play();
      },
      step(k) { walkShow(s, k); },
      leave() {
        setPan(false); document.body.classList.remove("in-walk");
        setTimeout(() => { if (!isWalk(scenes[state.idx])) AUD.stop(); }, 0);
      },
    };
  }
  Object.keys(WALK).forEach((id) => { if ($("#" + id)) H[id] = walkHook(id); });

  /* ---- campus palettes (slides 16–23): ① the board builds tile by tile; ②–④ the three renders, full bleed ---- */
  $$(".scene.palette").forEach((sc) => {
    const renders = sc.dataset.renders.split(",");
    H[sc.id] = {
      enter() { plain(); },
      step(k) {
        if (k === 1) { world("none"); shade(""); reveal($(".pl-board", sc), 80); sc.classList.remove("rendered"); return; }
        sc.classList.add("rendered");
        PHOTO.show(renders[k - 2], { kb: true, ar: 2.357 }); world("photo"); shade("photo");
      },
    };
  });

  /* ======================= boot ======================= */
  const fromHash = () => {
    const m = (location.hash || "").match(/^#([\w-]+)\/(\d+)/);
    go(m ? Math.max(0, sceneIx(m[1])) : 0, m ? +m[2] : 1);
  };
  addEventListener("hashchange", () => { if (location.hash !== "#" + scenes[state.idx].id + "/" + state.step) fromHash(); });
  fromHash();
  tick();
  window.ACKO = { go, setStep, setTheme, state, H, lightbox, countUp };
})();
