/* Mitigata · Living Network — one continuous journey.
   A persistent WORLD (satellite map · shared plan · digital twin · photographs)
   lives behind the chapters; each chapter is a copy overlay that steers it.
   Keys: → / PageDown / Space next beat · ← / PageUp previous · T day/night ·
   O index · N notes · F fullscreen · B blank · E explore · 1 / 2 option · L laser ·
   M measure / A area on the plan (Esc finishes, then clears). */
(function () {
  const D = window.MX_DATA, Z = D.zones;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const fmt = (n) => Math.round(n).toLocaleString("en-IN");
  const sqft = (m2, unit) => window.Plan2D.sqft(m2, unit);          // every area in the deck, in sq ft
  const scenes = $$(".scene");
  const sceneIx = (id) => scenes.findIndex((s) => s.id === id);
  const state = { idx: -1, step: 1, opt: "opt1", explore: false, t0: null, chapterT0: null, track: "mitigata", mitigataAt: { idx: 0, step: 1 } };
  // two decks: the Mitigata presentation (cover → journey) and About SKV, opened from the SKV logo
  const trackOf = (s) => (s.dataset.part === "0" ? "skv" : s.dataset.part === "A" ? "appendix" : "mitigata");
  const trackIdx = (t) => scenes.map((s, i) => (trackOf(s) === t ? i : -1)).filter((i) => i >= 0);
  const OPTNAME = { opt1: "Layout Option 01", opt2: "Layout Option 02", opt3: "Layout Option 03" };   // Ritika: the layouts go by number only
  let timers = [];
  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const clearTimers = () => { timers.forEach(clearTimeout); timers = []; };
  const zonesOf = (opt, type) => Z[opt].zones.filter((z) => z.type === type);
  const areaOf = (opt, types) => Z[opt].zones.filter((z) => types.includes(z.type)).reduce((a, z) => a + z.area, 0);
  const bboxOfType = (opt, type, pad) => window.Plan2D.bboxOf(zonesOf(opt, type).map((z) => z.poly), pad);
  const centroidOf = (opt, type) => window.Plan2D.centroid(zonesOf(opt, type).sort((a, b) => b.area - a.area)[0].poly);

  /* ======================= theme ======================= */
  const theme = () => document.documentElement.dataset.theme || "light";
  // no Day/Night switch: each slide has its own mode — data-mode="dark" is the deck's divider green, otherwise its white pages
  function setTheme(t) {
    if (document.documentElement.dataset.theme === t) return;
    document.documentElement.dataset.theme = t;
    if (twin) twin.setTheme(t);
  }
  const applyMode = (sc) => setTheme(sc.dataset.mode || "light");

  /* ======================= world ======================= */
  const LAYERS = { map: $("#w-map"), plan: $("#w-plan"), twin: $("#w-twin"), photo: $("#w-photo") };
  let twin = null, planA = null, planB = null;
  function getTwin() {
    if (!twin) {
      twin = new window.Twin(); twin.attach($("#world-twin")); twin.setTheme(theme()); twin.visible = false;
      if (window.TwinSite) twin.attachSite(new window.TwinSite(twin));   // Sattva Hallmark in its street (assets/js/site.js)
      try { if (twin.site && localStorage.getItem("mx-trees") === "0") twin.site.setTrees(false); } catch (e) { /* storage blocked */ }
    }
    return twin;
  }
  function getPlanA() {
    if (!planA) planA = new window.Plan2D($("#world-plan"), { interactive: true, layers: { furn: false, parts: false, labels: false } });
    return planA;
  }
  function getPlanB() {
    if (!planB) planB = new window.Plan2D($("#world-plan-b"), { interactive: true, option: "opt2", layers: { furn: true, zones: true, labels: true } });
    return planB;
  }
  function world(name, under) {
    for (const k in LAYERS) {
      LAYERS[k].classList.toggle("on", k === name);
      LAYERS[k].classList.toggle("under", k === under && k !== name);
    }
    if (twin) twin.visible = name === "twin" || under === "twin";
    world.cur = name;
  }
  const shade = (k) => { $("#shade").className = k || ""; };

  /* plan frames: right (copy on the left) · full · split · dock (keyplan) */
  const FA = $("#frame-a"), FB = $("#frame-b");
  function frames(mode, tag) {
    FA.className = "plan-frame" + ({ full: " full", split: " split-a", dock: " dock" }[mode] || "");
    FB.className = "plan-frame " + (mode === "split" ? "split-b" : "hidden-b");
    LAYERS.plan.classList.toggle("docked", mode === "dock");
    $("#tag-a").style.display = tag ? "" : "none";
    if (tag) $("#tag-a").textContent = tag;
    frames.mode = mode;
  }
  // docked keyplan: click to peek at the whole plan, click again to go back
  FA.addEventListener("click", (e) => {
    if (frames.mode !== "dock") return;
    e.stopPropagation();
    frames("full", $("#tag-a").textContent); FA.classList.add("peek"); LAYERS.plan.classList.add("on"); getPlanA().setLayers({ hover: true });   // peek: the keyplan, larger, still light
    const b = document.createElement("button"); b.className = "chip on peek-close"; b.textContent = "✕ Back to the view";
    b.onclick = () => { b.remove(); LAYERS.plan.classList.remove("on"); frames("dock", $("#tag-a").textContent); getPlanA().setLayers({ hover: false }); getPlanA().fit(frames.dockView, 0); };
    document.body.appendChild(b);
  }, true);

  /* ---------- satellite zoom stack ---------- */
  const MAP = {
    Z: 12, imgs: $$("#mapstack img"), labels: $$(".map-label"), site: D.site ? $("#map-site") : null,
    render(z) {
      this.Z = z;
      this.imgs.forEach((im, i) => {
        const zi = +im.dataset.z, s = Math.pow(2, z - zi);
        im.style.transform = `translate(-50%,-50%) scale(${s})`;
        // each finer still fades in over the second half of the zoom gap below it
        const start = i === 0 ? 0 : zi - (zi - +this.imgs[i - 1].dataset.z) * 0.5;
        im.style.opacity = i === 0 ? 1 : clamp((z - start) / (zi - start), 0, 1);
      });
      this.labels.forEach((l) => l.classList.toggle("on", Math.abs(z - +l.dataset.zl) < 0.9));
      $("#map-pin").style.opacity = z > 17.6 ? 1 : 0;
      if (this.site) {   // the floor plate, registered on the z19 still: scales with it
        this.site.style.transform = `translate(-50%,-50%) scale(${Math.pow(2, z - D.site.zoom)})`;
        this.site.style.opacity = z > 17.6 ? 1 : 0;
        this.placePin();
      }
    },
    // still px of the plate (z19) -> px inside #w-map
    toLayer(px) {
      const m = this.site.getScreenCTM(); if (!m) return null;
      const pt = this.site.createSVGPoint(); pt.x = px[0]; pt.y = px[1];
      const q = pt.matrixTransform(m), r = LAYERS.map.getBoundingClientRect();
      return [q.x - r.left, q.y - r.top];
    },
    placePin() {
      const c = this.toLayer(this.pinPx); if (!c) return;
      const pin = $("#map-pin"); pin.style.left = c[0] + "px"; pin.style.top = c[1] + "px";
    },
    zoomTo(z, ms) {
      cancelAnimationFrame(this.raf);
      const from = this.Z, t0 = performance.now();
      if (!ms) return this.render(z);
      const step = (now) => {
        const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        this.render(from + (z - from) * e);
        if (k < 1) this.raf = requestAnimationFrame(step);
      };
      this.raf = requestAnimationFrame(step);
    },
  };
  if (MAP.site) {
    const o = D.site.outline_px;
    MAP.site.querySelector("path").setAttribute("d", "M" + o.map((p) => p.join(" ")).join("L") + "Z");
    MAP.pinPx = [o.reduce((a, p) => a + p[0], 0) / o.length, o.reduce((a, p) => a + p[1], 0) / o.length];
  }
  const mmToPx = (mm) => { const m = D.site.mm_to_px; return [m[0] * mm[0] + m[2] * mm[1] + m[4], m[1] * mm[0] + m[3] * mm[1] + m[5]]; };
  /* turn + zoom the satellite so the plate's roof lands exactly on the plan in frame A (north -> right) */
  function turnMapOntoPlan(p) {
    const st = $("#mapstack"), wm = LAYERS.map.getBoundingClientRect(), hr = p.host.getBoundingClientRect();
    st.classList.remove("turn"); st.style.transform = "";
    const o = Z.annot.outline, A = [o[0], o[2]].map((mm) => MAP.toLayer(mmToPx(mm)));
    const B = [o[0], o[2]].map((mm) => { const s = p.toScreen(mm); return [hr.left - wm.left + s[0], hr.top - wm.top + s[1]]; });
    if (!A[0] || !A[1]) return;
    const ax = A[1][0] - A[0][0], ay = A[1][1] - A[0][1], bx = B[1][0] - B[0][0], by = B[1][1] - B[0][1], d = ax * ax + ay * ay;
    const re = (bx * ax + by * ay) / d, im = (by * ax - bx * ay) / d;          // B = (re + i·im)·A + t
    const tx = B[0][0] - (re * A[0][0] - im * A[0][1]), ty = B[0][1] - (im * A[0][0] + re * A[0][1]);
    void st.offsetWidth; st.classList.add("turn");
    st.style.transform = `matrix(${re}, ${im}, ${-im}, ${re}, ${tx}, ${ty}) translateX(var(--mx))`;
  }
  function untwistMap() { const st = $("#mapstack"); st.classList.remove("turn"); st.style.transform = ""; LAYERS.map.classList.remove("turned"); }
  MAP.render(12);

  /* ---------- photographs ---------- */
  const AR = { reception: 2.314, soc: 2.358, breakout: 2.358, boardroom: 1.792, "boardroom-dinner": 1.792, "boardroom-present": 1.792, "soc-night": 2.188, meeting6: 2.0, "human-centric": 1.5, immersive: 1.048 };
  const PHOTO = {
    stack: $("#photo-stack"), cur: null,
    src(key) { return key.startsWith("sv-") ? `assets/site/${key}.webp` : `assets/img/${key}.webp`; },
    // key "" is an empty (black) frame; o.kb drifts the whole frame, o.pins adds a scrim and a pin layer that drift with it
    show(key, o) {
      o = o || {};
      const src = key ? this.src(key) : "";
      $("#photo-credit").textContent = o.credit || (key.startsWith("sv-") ? "Street View · Imagery ©2026 Google" : key === "soc-night" ? "SKV photomontage · atrium" : "");
      if (this.cur && this.cur.dataset.src === src) return this.cur;
      const f = document.createElement("div"); f.className = "shot-frame"; f.dataset.src = src;
      const ar = AR[key] || (key.startsWith("sv-") ? 2 : 1.778), kb = o.kb ? " kb" : "";
      f.innerHTML = `<div class="cover${kb}" data-ar="${ar}">${src ? `<div class="shot" style="background-image:url(${src})"></div>` : ""}<div class="grade"></div></div>` +
        (o.pins ? `<div class="scrim"></div><div class="cover pins${kb}" data-ar="${ar}"></div>` : "");
      f.style.opacity = 0;
      if (o.from) { f.style.transformOrigin = `${o.from[0]}px ${o.from[1]}px`; f.style.transform = "scale(.28)"; }
      this.stack.appendChild(f); layoutCovers();
      requestAnimationFrame(() => requestAnimationFrame(() => { f.style.opacity = 1; f.style.transform = "none"; }));
      const old = this.cur; this.cur = f;
      if (old) setTimeout(() => old.remove(), 1100);
      return f;
    },
    shot() { return this.cur && this.cur.querySelector(".shot"); },
    grade() { return this.cur && this.cur.querySelector(".grade"); },
  };
  /* zoom from a camera point on the plan into its render, then dock the plan as a keyplan */
  function enterPhoto(key, cam, opt, show) {
    const p = getPlanA(); opt = opt || "opt1";
    const tag = "Keyplan · " + OPTNAME[opt];
    const fromPhoto = world.cur === "photo";
    p.setOption(opt); p.setLayers({ cams: true, furn: true, parts: true, zones: false, evo: false, labels: false, tiers: false, routes: [], events: null, sig: false, sat: false, hover: false });
    p.setOverlay([]); p.setNotes([]); p.setLinks([]); p.host.dataset.fac = "";
    const c = cam && Z[opt].cameras[cam];
    p.setCam(cam || null);
    const around = c ? [c.at[0] - 9000, c.at[1] - 6000, c.at[0] + 9000, c.at[1] + 6000] : null;
    frames.dockView = c ? [c.at[0] - 26000, c.at[1] - 15000, c.at[0] + 26000, c.at[1] + 15000] : null;
    if (fromPhoto || !c) {
      PHOTO.show(key, show); world("photo"); frames("dock", tag); p.fit(frames.dockView, 0);
      return;
    }
    if (frames.mode === "dock" || frames.mode === "split") frames("full");
    world("plan");
    p.fit(around, 900);
    later(() => {
      const r = p.host.getBoundingClientRect(), s = p.toScreen(c.at);
      PHOTO.show(key, Object.assign({ from: [r.left + s[0], r.top + s[1]] }, show));
      world("photo");
      later(() => { frames("dock", tag); p.fit(frames.dockView, 0); }, 700);
    }, 820);
  }

  /* cover-fit frames: keep render-relative hotspots glued to the image */
  function layoutCovers() {
    const W = window.innerWidth, H = window.innerHeight;
    $$(".cover").forEach((c) => {
      const ar = +c.dataset.ar; let w = W, h = W / ar; if (h < H) { h = H; w = H * ar; }
      Object.assign(c.style, { position: "absolute", width: w + "px", height: h + "px", left: (W - w) / 2 + "px", top: (H - h) / 2 + "px" });
    });
  }
  window.addEventListener("resize", layoutCovers);

  /* ======================= chrome ======================= */
  const ov = $("#overview-grid");
  const PARTS = { cover: "Cover", 0: "About SKV", 1: "Part 1 · Design concept", 2: "Part 2 · Space planning", 3: "Part 3 · Visual direction", 4: "Part 4 · Value engineering", A: "Appendix" };
  // the cover and About SKV sit ahead of the journey, so journey chapters keep their numbers (Opening = 00)
  const front = (s) => s.dataset.part === "cover" || s.dataset.part === "0";
  // section starters and the closing page carry no chapter number (data-nonum), so the chapters count on without gaps
  const nonum = (s) => s.hasAttribute("data-nonum");
  const journey = scenes.filter((s) => !front(s) && !nonum(s) && s.dataset.part !== "A" && s.dataset.part !== "0");
  const appx = scenes.filter((s) => s.dataset.part === "A");
  const chNum = (i) => (nonum(scenes[i]) ? "—" : { cover: "COVER", 0: "SKV" }[scenes[i].dataset.part] || (scenes[i].dataset.part === "A" ? "A" + (appx.indexOf(scenes[i]) + 1) : String(journey.indexOf(scenes[i]) + 1).padStart(2, "0")));
  let part = null, grid = null;
  scenes.forEach((s, i) => {
    if (s.dataset.part !== part) {
      part = s.dataset.part;
      const label = PARTS[part];
      const h = document.createElement("h4"); h.textContent = label; ov.appendChild(h);
      grid = document.createElement("div"); grid.className = "grid"; ov.appendChild(grid);
    }
    const o = document.createElement("button");
    const beats = s.dataset.beats ? s.dataset.beats.split(",") : null;
    o.innerHTML = `<span class="n">${s.dataset.part === "cover" || nonum(s) ? "" : chNum(i) + " · "}${s.dataset.mins} min</span><b>${s.dataset.title}</b>` +
      (beats ? `<span class="beats">${beats.map((t, k) => `<span data-beat="${k + 1}">${t}</span>`).join("")}</span>` : `<span>${(s.dataset.notes || "").slice(0, 92)}…</span>`);
    o.onclick = (e) => {
      const beat = e.target.closest("[data-beat]");
      toggleOverview(false); go(i, beat ? +beat.dataset.beat : 1);
    };
    grid.appendChild(o);
  });
  scenes.forEach((s, i) => {
    if (front(s) || nonum(s)) return;
    $$(".kicker", s).forEach((k) => { if (!k.closest(".storycol")) k.textContent = k.textContent.replace(/^\d\d(?= · )/, chNum(i)); });
  });
  /* the topic mark (Ritika): Mitigata's arc, one ring per topic of the deck, inner to outer; past charcoal, now green, next pale.
     It sits before the breadcrumb, on the slides' left line; hover lists the topics, a click opens a topic's first slide */
  // the four sections of the deck (Ritika, 12.10: Value engineering is the fourth; the cover sits before the arc)
  const TOPICS = { mitigata: [["1", "Design concept"], ["2", "Space planning"], ["3", "Visual direction"], ["4", "Value engineering"]], appendix: [["A", "Appendix"]], skv: [["0", "About SKV"]] };
  const RINGS = { 4: [[0.28, 0.42], [0.47, 0.61], [0.66, 0.8], [0.85, 1]], 1: [[0.555, 1]] };
  const arcPt = (r, a) => [17 + r * 24 * Math.cos((a * Math.PI) / 180), 25 - r * 24 * Math.sin((a * Math.PI) / 180)].map((v) => v.toFixed(2));
  const ringD = ([r0, r1]) => { const A = arcPt(r1, 135), B = arcPt(r1, 45), Cc = arcPt(r0, 45), Dd = arcPt(r0, 135);
    return `M${A}A${r1 * 24} ${r1 * 24} 0 0 1 ${B}L${Cc}A${r0 * 24} ${r0 * 24} 0 0 0 ${Dd}Z`; };
  const firstOf = (part) => scenes.findIndex((s) => s.dataset.part === part);
  function topicMark(track) {
    const tp = TOPICS[track] || TOPICS.mitigata, rings = RINGS[tp.length] || RINGS[4];
    $("#topic-mark svg").innerHTML = tp.map(([p], k) => `<path class="tm-ring" data-part="${p}" d="${ringD(rings[k])}"/>`).join("");
    // the presentation's list opens with the cover (Ritika, 14.10): Mitigata's arc in place of a number, no ring in the mark,
    // so 01–04 stay the deck's sections
    const arc = `<svg class="tm-arc" viewBox="0 0 34 21" aria-hidden="true"><path d="${ringD(RINGS[1][0])}"/></svg>`;
    $("#tm-list").innerHTML = (track === "mitigata" ? `<button type="button" data-part="cover"><b>${arc}</b>Cover page</button>` : "") +
      tp.map(([p, n], k) => `<button type="button" data-part="${p}"><b>${tp.length > 1 ? String(k + 1).padStart(2, "0") : ""}</b>${n}</button>`).join("");
    $$("#topic-mark [data-part]").forEach((el) => (el.onclick = (e) => {
      e.stopPropagation(); if (document.activeElement) document.activeElement.blur();
      if (el.dataset.part === "cover") state.t0 = null;     // the cover starts the presentation again
      go(firstOf(el.dataset.part), 1);
    }));
    topicMark.track = track;
  }
  function topicState(sc) {
    if (topicMark.track !== state.track) topicMark(state.track);
    const order = (TOPICS[state.track] || TOPICS.mitigata).map(([p]) => p), now = order.indexOf(sc.dataset.part);
    $$("#topic-mark [data-part]").forEach((el) => { const k = order.indexOf(el.dataset.part); el.dataset.state = k < now ? "past" : k === now ? "now" : "next"; });
  }
  const PLANNED = scenes.filter((s) => trackOf(s) === "mitigata").reduce((a, s) => a + +s.dataset.mins, 0) * 60;
  const mmss = (s) => String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(Math.floor(s % 60)).padStart(2, "0");
  function tick() {
    const now = Date.now(), el = state.t0 ? (now - state.t0) / 1000 : 0;
    const sc = scenes[state.idx];
    if (sc) {
      const ch = state.chapterT0 ? (now - state.chapterT0) / 1000 : 0;
      $("#notes-time").textContent = `CH ${chNum(state.idx)} · ${mmss(ch)} / ${mmss(+sc.dataset.mins * 60)} · TOTAL ${mmss(el)} / ${mmss(PLANNED)}`;
    }
  }
  setInterval(tick, 1000);
  // the time lives in the speaker notes (N); click it to reset
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
    $$("[data-optseg] button").forEach((b) => b.classList.toggle("on", b.dataset.opt === state.opt));
    if (front(sc)) {
      const beat = (sc.dataset.beats || "").split(",")[state.step - 1];
      $("#crumb").innerHTML = beat ? `${sc.dataset.crumb} › <b>${beat}</b>` : `<b>${sc.dataset.crumb}</b>`;
      return;
    }
    if (nonum(sc)) { $("#crumb").innerHTML = `<b>${sc.dataset.crumb}</b>`; return; }
    if (sc.dataset.part === "1") { $("#crumb").innerHTML = `Mitigata › <b>${sc.dataset.crumb}</b>`; return; }
    if (sc.dataset.part === "4") { $("#crumb").innerHTML = `Value engineering › <b>${sc.dataset.crumb}</b>`; return; }
    if (sc.dataset.part === "A") { $("#crumb").innerHTML = `Appendix › <b>${sc.dataset.title}</b>`; return; }
    const parts = ["Bengaluru"].concat(state.idx >= sceneIx("s-site") ? ["Sattva Hallmark", "Level 03"] : []);
    const last = ((sc.dataset.crumbs || "").split(",")[state.step - 1] || sc.dataset.crumb).split(" › ").pop();   // data-crumbs: one per beat
    if (!parts.includes(last) && last !== "Bengaluru") parts.push(last);
    if (+sc.dataset.part >= 2 && state.idx > sceneIx("s-twin")) parts.splice(3, 0, OPTNAME[sc.dataset.opt || state.opt]);   // data-opt: a chapter drawn for one option only
    $("#crumb").innerHTML = parts.map((p, i) => (i === parts.length - 1 ? `<b>${p}</b>` : p)).join(" › ");
  }
  const toggleOverview = (on) => $("#overview").classList.toggle("on", on === undefined ? !$("#overview").classList.contains("on") : on);
  function fullscreen() { if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }
  function setExplore(on) { state.explore = on; document.body.classList.toggle("explore", on); if (planA) planA.setLayers({ hover: on || !!hoverScene[scenes[state.idx].id] }); }
  // chapters where the plan is the main view and the room is listening: hover rooms / teams
  const hoverScene = { "s-teams": 1, "s-arc": 1, "s-net": 1, "s-opt3": 1, "s-flex": 1 };

  /* ======================= navigation ======================= */
  function go(i, step) {
    i = clamp(i, 0, scenes.length - 1);
    const prev = scenes[state.idx], next = scenes[i];
    if (prev !== next) {
      clearTimers();
      if (planA) planA.measureMode(null);                  // measurements belong to the slide they were taken on
      $$(".peek-close").forEach((b) => b.remove());
      if (prev) { prev.classList.remove("active"); hook(prev, "leave"); }
      if (prev && trackOf(prev) === "mitigata" && trackOf(next) !== "mitigata") state.mitigataAt = { idx: state.idx, step: state.step };
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
    layoutCovers();
    hook(sc, "step", state.step);
    updateChrome();
    // the address follows the deck: a hash change (not replaceState), so browsers that only watch navigations, as the Claude
    // browser pane, show it too; our own change is skipped below, so nothing runs twice (Sathwick)
    const h = "#" + sc.id + "/" + state.step;
    if (location.hash !== h) { try { location.replace(h); } catch (e) { /* file:// */ } }
  }
  const steps = (i) => +scenes[i].dataset.steps || 1;
  function next() {
    if (!state.t0 && state.track === "mitigata") state.t0 = Date.now();
    const tr = trackIdx(state.track), at = tr.indexOf(state.idx);
    if (state.step < steps(state.idx)) setStep(state.step + 1); else if (at < tr.length - 1) go(tr[at + 1], 1);
  }
  function prev() {
    const tr = trackIdx(state.track), at = tr.indexOf(state.idx);
    if (state.step > 1) setStep(state.step - 1); else if (at > 0) go(tr[at - 1], steps(tr[at - 1]));
  }
  // the logos: SKV opens About SKV; Mitigata returns to the slide and beat the presentation was left on (Ritika, 14.10:
  // not the cover; the cover is first in the topics list)
  $("#brand-skv").onclick = () => { if (state.track !== "skv") go(sceneIx("s-skv"), 1); };
  $("#brand-mitigata").onclick = () => { if (state.track !== "mitigata") go(state.mitigataAt.idx, state.mitigataAt.step); };
  function setOpt(o) { if (o === state.opt) return; state.opt = o; updateChrome(); hook(scenes[state.idx], "opt", o); }
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-optseg] button"); if (b) setOpt(b.dataset.opt); });
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea")) return;
    const k = e.key;
    if (["ArrowRight", "PageDown", " ", "Enter"].includes(k)) { e.preventDefault(); next(); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(k)) { e.preventDefault(); prev(); }
    else if (k === "Home") go(trackIdx(state.track)[0], 1);
    else if (k === "End") go(trackIdx(state.track).slice(-1)[0], 1);
    else if (k === "f" || k === "F") fullscreen();
    else if (k === "b" || k === "B" || k === ".") $("#blank").classList.toggle("on");
    else if (["m", "M", "a", "A"].includes(k) && planA && world.cur === "plan" && planA.L.ctl && frames.mode !== "dock" && !document.body.classList.contains("wk-key")) {   // measure on the plan in view (not the walk's key plan)
      const m = k.toLowerCase() === "m" ? "dist" : "area"; planA.measureMode(planA.meas && planA.meas.mode === m ? null : m);
    }
    else if (k === "Escape" && planA && planA.measureEsc()) { /* finished or cleared a measurement */ }
    else if (k === "o" || k === "O" || k === "Escape") toggleOverview(k === "Escape" ? false : undefined);
    else if (k === "n" || k === "N") $("#notes").classList.toggle("on");
    else if (k === "e" || k === "E") setExplore(!state.explore);
    else if (k === "1") setOpt("opt1");
    else if (k === "2") setOpt("opt2");
    else if (k === "l" || k === "L") $("#cur").classList.toggle("laser");
  });
  $("#blank").onclick = () => $("#blank").classList.remove("on");

  /* ======================= presenter cursor =======================
     A green dot on the mouse with a ring easing behind it: the ring grows on anything clickable and
     dashes over a pannable plan. It fades after 2 s still; L swaps in a red laser that stays put and leaves an ink trail
     that fades in 1.6 s (Ritika, 12.10). */
  (function cursor() {
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;   // touch and pen keep the browser's own
    const cur = $("#cur"), ring = $(".cur-ring", cur), dot = $(".cur-dot", cur), laser = $(".cur-laser", cur);
    const CLICK = "button, a[href], [role=button], label, select, summary, .plan .link, .hv-room, .hv-seats, .story, .tl-stop, .plan-frame.dock, #notes-time";
    const PAN = ".plan.pannable svg";
    const ease = matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : 0.22;
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
    // the laser's ink trail: the pointer's last 1.6 s as a red line, thinner and fainter with age; drawn only while it has points
    const cv = $(".cur-trail", cur), cx = cv.getContext("2d"), LIFE = 1600, still = ease === 1;
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
      if (cur.classList.contains("out")) { p.rx = p.x; p.ry = p.y; at(ring, p.x, p.y); }   // back in the window: no swoop from the edge
      const t = e.target instanceof Element ? e.target : null;
      cur.classList.remove("out", "idle");
      cur.classList.toggle("text", !!(t && t.closest("input, textarea")));
      cur.classList.toggle("click", !!(t && t.closest(CLICK)));
      cur.classList.toggle("pan", !!(t && t.closest(PAN)));
      cur.classList.toggle("meas", !!(t && t.closest(".plan.measuring")));   // the crosshair takes over
      at(dot, p.x, p.y); at(laser, p.x, p.y);
      if (!raf) raf = requestAnimationFrame(tick);
      if (!still && cur.classList.contains("laser")) { ink.push({ x: p.x, y: p.y, t: performance.now() }); if (!inkRaf) inkRaf = requestAnimationFrame(inkTick); }
    }, { capture: true, passive: true });
    document.addEventListener("pointerdown", (e) => { if (e.pointerType === "mouse") cur.classList.add("down"); }, true);
    document.addEventListener("pointerup", () => cur.classList.remove("down"), true);
    document.addEventListener("mouseout", (e) => { if (!e.relatedTarget) { cur.classList.add("out"); inkClear(); } });
    setInterval(() => { if (!cur.classList.contains("laser") && Date.now() - moved > 2000) cur.classList.add("idle"); }, 200);
  })();

  /* ======================= camera editor (C) =======================
     Fly the 3D camera freely and save a frame for the current step:
     WASD move · Q/E down/up · Shift faster · drag look · right-drag orbit · wheel forward.
     Frames are kept in this browser (localStorage) and override the step's built-in view;
     "Copy all" gives the JSON to bake into the code. */
  const CAMKEY = "mx-cam-frames";
  const camFrames = (() => { try { return JSON.parse(localStorage.getItem(CAMKEY)) || {}; } catch (e) { return {}; } })();
  const stepKey = () => `${scenes[state.idx].id}/${state.step}`;
  function saveFrames() { try { localStorage.setItem(CAMKEY, JSON.stringify(camFrames)); } catch (e) { /* storage blocked */ } }
  // 11.10: "Back to the site" became the SOC chapter's first step, so frames saved for its two street views move up one
  try {
    if (localStorage.getItem("mx-cam-v") !== "2") {
      const a = camFrames["s-soc/1"], b = camFrames["s-soc/2"];
      delete camFrames["s-soc/1"]; delete camFrames["s-soc/2"];
      if (a) camFrames["s-soc/2"] = a; if (b) camFrames["s-soc/3"] = b;
      saveFrames(); localStorage.setItem("mx-cam-v", "2");
    }
    // 12.10: "The SOC, seen" became the last three steps of Inside the SOC (then s-w-soc 3–5), so its frames move there
    if (localStorage.getItem("mx-cam-v") === "2") {
      [1, 2, 3].forEach((k) => { const f = camFrames[`s-soc/${k}`]; if (f) { camFrames[`s-w-soc/${k + 2}`] = f; delete camFrames[`s-soc/${k}`]; } });
      saveFrames(); localStorage.setItem("mx-cam-v", "3");
    }
    // 12.10: the SOC render gained a Details beat (its pins), so the building's frames move one step on (s-w-soc 4–6)
    if (localStorage.getItem("mx-cam-v") === "3") {
      [5, 4, 3].forEach((k) => { const f = camFrames[`s-w-soc/${k}`]; if (f) { camFrames[`s-w-soc/${k + 1}`] = f; delete camFrames[`s-w-soc/${k}`]; } });
      saveFrames(); localStorage.setItem("mx-cam-v", "4");
    }
  } catch (e) { /* storage blocked */ }
  const CAM = { on: false, el: null };
  function camPanel() {
    if (CAM.el) return CAM.el;
    const el = document.createElement("div");
    el.id = "cam-editor";
    el.style.cssText = "position:fixed;right:16px;top:76px;z-index:60;width:300px;padding:12px 14px;border-radius:10px;background:var(--panel);border:1px solid var(--accent);font:12px/1.5 var(--body);color:var(--ink);backdrop-filter:blur(8px);pointer-events:auto";
    el.innerHTML = `<b style="font-family:var(--display);font-size:13px">Camera editor</b> <span class="mute" style="float:right">C to close</span>
      <div class="mute" style="margin:4px 0 8px">Unreal-style · RMB drag look · RMB+WASD/QE fly (Shift fast)<br>RMB+wheel speed · RMB+Z/C lens · LMB drag look<br>MMB or LMB+RMB pan · Alt+LMB orbit · Alt+RMB dolly · wheel push</div>
      <div id="cam-step"></div><pre id="cam-read" style="margin:6px 0 2px;white-space:pre-wrap"></pre><div id="cam-speed" class="mute" style="margin-bottom:6px"></div>
      <label>Lens <span id="cam-fov-v"></span>°<input id="cam-fov" type="range" min="15" max="100" step="1" style="width:100%"></label>
      <label>Rise (shift lens) <span id="cam-rise-v"></span><input id="cam-rise" type="range" min="-0.6" max="0.9" step="0.005" style="width:100%"></label>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">
        <button class="chip" id="cam-trees">Trees: on</button><button class="chip" id="cam-save">Save for this step</button><button class="chip" id="cam-reset">Reset step</button><button class="chip" id="cam-copy">Copy all</button>
      </div><div id="cam-msg" class="mute" style="margin-top:6px"></div>`;
    document.body.appendChild(el);
    const t = () => getTwin();
    $("#cam-fov", el).oninput = (e) => { t().camera.fov = +e.target.value; t().camera.updateProjectionMatrix(); };
    $("#cam-rise", el).oninput = (e) => t().setRise(+e.target.value);
    // hand the keyboard back to the 3D view after using a slider or button
    el.addEventListener("pointerup", () => setTimeout(() => document.activeElement && document.activeElement.blur(), 0));
    $("#cam-save", el).onclick = () => {
      const tw = t(), p = tw.camera.position, R = tw.rig;
      camFrames[stepKey()] = { cam: [p.x, p.y, p.z].map((v) => +v.toFixed(2)), at: [R.tx, R.ty, R.tz].map((v) => +v.toFixed(2)), fov: Math.round(tw.camera.fov), rise: +tw.rise.toFixed(3) };
      saveFrames(); tw.home = lookFrom(camFrames[stepKey()].cam, camFrames[stepKey()].at);
      if (tw.site && scenes[state.idx].id === "s-w-soc") tw.site.keepClear(clearViews());   // re-clear the trees for the new frame
      $("#cam-msg", el).textContent = `Saved ${stepKey()}.`;
    };
    const treesBtn = $("#cam-trees", el);
    const setTrees = (on) => { if (getTwin().site) getTwin().site.setTrees(on); treesBtn.textContent = "Trees: " + (on ? "on" : "off"); treesBtn.classList.toggle("on", on); try { localStorage.setItem("mx-trees", on ? "1" : "0"); } catch (e) { /* storage blocked */ } };
    treesBtn.onclick = () => setTrees(!(getTwin().site && getTwin().site.treesOn !== false));
    setTrees((() => { try { return localStorage.getItem("mx-trees") !== "0"; } catch (e) { return true; } })());
    $("#cam-reset", el).onclick = () => { delete camFrames[stepKey()]; saveFrames(); $("#cam-msg", el).textContent = `Cleared ${stepKey()}; the built-in view returns next time.`; };
    $("#cam-copy", el).onclick = async () => {
      const txt = JSON.stringify(camFrames, null, 1);
      try { await navigator.clipboard.writeText(txt); $("#cam-msg", el).textContent = `Copied ${Object.keys(camFrames).length} frame(s).`; }
      catch (e) { window.prompt("Copy the frames:", txt); }
    };
    return (CAM.el = el);
  }
  function camReadout() {
    if (!CAM.on) return;
    const tw = getTwin(), p = tw.camera.position, el = CAM.el;
    $("#cam-step", el).textContent = `Step ${stepKey()}${camFrames[stepKey()] ? " · saved frame" : ""}`;
    $("#cam-read", el).textContent = `eye  ${p.x.toFixed(1)}, ${p.y.toFixed(1)}, ${p.z.toFixed(1)}\nlook ${tw.rig.tx.toFixed(1)}, ${tw.rig.ty.toFixed(1)}, ${tw.rig.tz.toFixed(1)}`;
    $("#cam-fov-v", el).textContent = Math.round(tw.camera.fov); $("#cam-rise-v", el).textContent = tw.rise.toFixed(3);
    $("#cam-speed", el).textContent = `speed ×${(tw.flySpeed || 1).toFixed(2)}`;
    if (document.activeElement !== $("#cam-fov", el)) $("#cam-fov", el).value = tw.camera.fov;
    if (document.activeElement !== $("#cam-rise", el)) $("#cam-rise", el).value = tw.rise;
    requestAnimationFrame(camReadout);
  }
  function toggleCam(on) {
    if (world.cur !== "twin" && on !== false) return;
    CAM.on = on === undefined ? !CAM.on : on;
    const tw = getTwin(), el = camPanel();
    el.style.display = CAM.on ? "" : "none";
    tw.keys = {};
    if (CAM.on) { CAM.prev = tw.control; tw.stopFly(); if (tw.control !== "free") tw.setControl("free"); camReadout(); }
    else if (CAM.prev && CAM.prev !== "free") tw.setControl(CAM.prev);
  }
  const FLYKEYS = { w: "w", a: "a", s: "s", d: "d", q: "q", e: "e" };
  // the Unreal-style camera is live on any 3D view that uses it (the site views), editor open or not
  const freeCam = () => twin && world.cur === "twin" && twin.control === "free";
  // capture phase: camera keys never reach the presentation's shortcuts
  const typing = (t) => t && t.closest && t.closest("textarea, input:not([type=range])");
  window.addEventListener("keydown", (e) => {
    if (typing(e.target)) return;
    const rmb = twin && twin.mouseButtons & 2;
    if ((e.key === "c" || e.key === "C") && !(freeCam() && rmb)) { e.stopPropagation(); toggleCam(); return; }
    if (!freeCam()) return;
    if (e.key === "Alt") e.preventDefault();               // Alt is for orbit/dolly, not the browser menu
    const tw = twin;
    tw.keys = tw.keys || {};
    if (e.key === "Shift") tw.keys.fast = true;
    if ((e.key === "z" || e.key === "Z" || e.key === "c" || e.key === "C") && rmb) {
      // RMB + Z/C: lens out / in, as in Unreal
      e.stopPropagation(); e.preventDefault();
      tw.camera.fov = Math.min(100, Math.max(10, tw.camera.fov + (e.key.toLowerCase() === "z" ? 2 : -2))); tw.camera.updateProjectionMatrix();
      return;
    }
    const k = FLYKEYS[e.key.toLowerCase()];
    // as in Unreal: WASD/QE fly while the right button is held; with the editor open they always fly
    if (k && (rmb || CAM.on)) {
      e.stopPropagation(); e.preventDefault();
      // a tap moves at once (0.4 m, 1.6 m with Shift); holding keeps moving every frame
      if (!e.repeat && !tw.keys[k]) { const m = e.shiftKey ? 1.6 : 0.4; tw.flyBy(((k === "d") - (k === "a")) * m, ((k === "e") - (k === "q")) * m, ((k === "w") - (k === "s")) * m); }
      tw.keys[k] = true;
    }
  }, true);
  window.addEventListener("keyup", (e) => {
    if (!twin || !twin.keys) return;                         // always release, whatever the mouse is doing now
    const k = FLYKEYS[e.key.toLowerCase()];
    if (k) twin.keys[k] = false;
    if (e.key === "Shift") twin.keys.fast = false;
  }, true);
  window.addEventListener("blur", () => { if (twin) twin.keys = {}; });   // no stuck keys after alt-tab

  /* ======================= chapters ======================= */
  const H = {};
  function hook(sc, ev, arg) { const h = sc && H[sc.id]; if (h && h[ev]) h[ev](arg, sc); }

  /* ---- About SKV (deck slides 3–13): its own chapter ahead of the journey ---- */
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const LOGOS = ("Google,Amazon,Samsung,PepsiCo,adidas,Godrej,Aramco,Shell,Honeywell,Qualcomm,GlobalLogic,KPMG,H&M,Max Healthcare,Amway,SYSTRA,PwC,Levi's," +
    "McDermott,DLF,DXC Technology,University of Cambridge,M&S,CNH,Perfetti Van Melle,Kia,The Times of India,MetLife,Cadence,Cyril Amarchand Mangaldas,dunnhumby,Airtel," +
    "MG Motor,Hindustan Times,Concentrix,Spark Minda,Vedanta,British Council,Aon,Fortis,Hero MotoCorp,NTT,Amity University,STL,Macquarie,SRF,BIBA,Synopsys,Adani,ReNew," +
    "Muthoot Finance,Grant Thornton,Stryker,Target").split(",");
  const n2 = (i) => String(i + 1).padStart(2, "0");
  $("#skv-logos").innerHTML = LOGOS.map((n, i) => `<div data-in="${1 + Math.floor(i / 9)}"><img src="assets/img/skv/logo-${n2(i)}.webp" alt="${n.replace(/&/g, "&amp;")}"></div>`).join("");
  $("#skv-caps").innerHTML = LOGOS.slice(0, 10).map((_, i) => `<div data-in="1" style="background-image:url(assets/img/skv/project-${n2(i)}.webp)"></div>`).join("");

  function countUp(el, ms) {
    const to = +el.dataset.count, dec = +(el.dataset.dec || 0), pre = el.dataset.pre || "";
    const show = (v) => (el.textContent = pre + (dec ? v.toFixed(dec) : Math.round(v).toLocaleString("en-IN")));
    if (reduced) return show(to);
    const t0 = performance.now();
    const step = (now) => {
      const k = Math.min(1, (now - t0) / ms);
      show(to * (1 - Math.pow(1 - k, 3)));
      if (k < 1 && document.body.dataset.scene === "s-skv") requestAnimationFrame(step); else show(to);
    };
    show(0); requestAnimationFrame(step);
  }

  /* the deck's animated ASCII data-field (slides 1 and 3), redrawn live so it stays sharp and themed */
  const makeAscii = (cv) => ({
    cv, on: false, last: 0, color: null,
    GLYPHS: " .:-=+itl1I/T7M#",
    start() { if (this.on) return; this.on = true; this.cv.classList.add("on"); this.frame(performance.now()); },
    stop() { this.on = false; this.cv.classList.remove("on"); cancelAnimationFrame(this.raf); },
    frame(now) {
      if (!this.on) return;
      this.raf = requestAnimationFrame((t) => this.frame(t));
      if (now - this.last < 70) return;   // ~14 fps is plenty for a drifting field
      this.last = now;
      const cv = this.cv, dpr = Math.min(2, window.devicePixelRatio || 1), W = cv.clientWidth, H = cv.clientHeight;
      if (!W || !H) return;
      if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
      const g = cv.getContext("2d"), fs = 12, cw = fs * 0.62, ch = fs * 1.18, t = reduced ? 0 : now / 1000;
      if (!this.color) this.color = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#04db7e";
      g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
      g.font = `400 ${fs}px "Lexend", "Poppins", sans-serif`; g.fillStyle = this.color; g.textBaseline = "top";
      const cols = Math.ceil(W / cw), rows = Math.ceil(H / ch), G = this.GLYPHS, n = G.length - 1;
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          // drifting interference of a few waves, carved by slow "clouds" so the field has holes like the deck's
          const a = Math.sin(x * 0.11 + t * 0.7) + Math.sin(y * 0.23 - t * 0.5) + Math.sin((x + y * 1.7) * 0.045 + t * 0.35);
          const cloud = Math.sin(x * 0.035 - t * 0.12) * Math.cos(y * 0.09 + t * 0.1);
          const v = Math.max(0, Math.min(1, (a / 3 + 1) / 2 * 0.9 + cloud * 0.55 - 0.08));
          const c = G[Math.floor(Math.pow(v, 1.35) * n)];
          if (c === " ") continue;
          g.globalAlpha = 0.2 + 0.8 * v;
          g.fillText(c, x * cw, y * ch);
        }
      }
      g.globalAlpha = 1;
      if (reduced) cancelAnimationFrame(this.raf);
    },
  });
  const ASCII = makeAscii($("#skv-ascii")), COVER_ASCII = makeAscii($("#cover-ascii"));

  /* ---- cover (deck slide 1) ---- */
  H["s-cover"] = {
    enter() { world("none"); shade(""); COVER_ASCII.start(); },
    theme() { COVER_ASCII.color = null; },
    leave() { COVER_ASCII.stop(); },
  };
  /* ---- thank you (deck slide 39): the cover's band again ---- */
  const THANKS_ASCII = makeAscii($("#thanks-ascii"));
  H["s-thanks"] = {
    enter() { world("none"); shade(""); THANKS_ASCII.color = null; THANKS_ASCII.start(); },
    theme() { THANKS_ASCII.color = null; },
    leave() { THANKS_ASCII.stop(); },
  };

  /* ---- the deck's agenda (slide 2) and part dividers (slides 14, 19, 27) ---- */
  const AGENDA_ASCII = makeAscii($("#agenda-ascii"));
  H["s-agenda"] = {
    enter() {
      world("none"); shade(""); AGENDA_ASCII.start();
      // the six stages draw in one after another, joined by the green line; each opens its chapter
      const g = $("#glimpse"), st = $$("#glimpse .gl");
      st.forEach((b) => { b.classList.remove("in"); b.onclick = () => go(sceneIx(b.dataset.to), 1); });
      st.forEach((b, i) => later(() => b.classList.add("in"), 300 + i * 380));
    },
    theme() { AGENDA_ASCII.color = null; },
    leave() { AGENDA_ASCII.stop(); },
  };
  // the section starters (Ritika, 12.10): one per part, as the deck's dividers — the ASCII field drifts top right
  $$(".scene.divider").forEach((sc) => {
    const A = makeAscii($(".divider-ascii", sc));
    H[sc.id] = {
      enter() { world("none"); shade(""); A.color = null; A.start(); },
      theme() { A.color = null; },
      leave() { A.stop(); },
    };
  });

  H["s-skv"] = {
    enter() { world("none"); shade(""); },
    step(k) {
      const board = $(`#s-skv .skv-board[data-only="${k}"]`), seen = {};
      const delay = (g) => 80 + g * 260;
      $$("[data-in]", board).forEach((e) => {
        e.classList.remove("in");
        const g = +e.dataset.in, n = (seen[g] = (seen[g] || 0) + 1) - 1;
        later(() => e.classList.add("in"), delay(g) + n * (k === 6 ? 26 : 70));
      });
      $$("[data-count]", board).forEach((e) => later(() => countUp(e, 1500), delay(+e.closest("[data-in]").dataset.in)));
      if (k === 1) ASCII.start(); else ASCII.stop();
    },
    theme() { ASCII.color = null; },
    leave() { ASCII.stop(); },
  };

  /* ---- 04 the site: Bengaluru → Sattva Hallmark, zooming by itself ---- */
  H["s-open"] = {
    enter() { untwistMap(); world("map"); shade(""); },   // the satellite full bleed, no white band (Sathwick)
    step(k) {
      MAP.zoomTo([0, 16.1, 19][k], [0, 4200, 3200][k]);
      // at Level 03 the floor plate draws itself on the east wing's roof
      if (MAP.site) { MAP.site.classList.remove("on"); if (k === 2) later(() => MAP.site.classList.add("on"), 2600); }
    },
  };

  /* ---- 01 understanding Mitigata (deck images) ---- */
  // 1) the five values come in; 2) tile by tile each turns into its workplace aspiration (deck slides 15 → 16, Ritika 12.10)
  H["s-mitigata"] = {
    enter() { world("none"); shade(""); $$("#s-mitigata .values-mosaic .tile").forEach((t) => t.classList.remove("in", "asp")); },
    step(k) {
      const tiles = $$("#s-mitigata .values-mosaic .tile"), fresh = !tiles[0].classList.contains("in");
      if (k === 1) {
        if (fresh) tiles.forEach((t, i) => later(() => t.classList.add("in"), 120 + i * 160));
        else tiles.forEach((t) => t.classList.remove("asp"));   // back from the aspirations
        return;
      }
      tiles.forEach((t) => t.classList.add("in"));
      tiles.forEach((t, i) => later(() => t.classList.add("asp"), (fresh ? 700 : 300) + i * 240));
    },
  };

  /* ---- 02 the question: the board builds itself (value → design move → aspiration), then the answer ---- */
  H["s-values"] = {
    enter() { world("none"); shade(""); },
    step() {
      const sc = $("#s-values"), rows = $$("#s-values .vb-row"), t = 450;
      sc.classList.remove("principles"); rows.forEach((r) => r.classList.remove("linked"));
      rows.forEach((r, i) => later(() => r.classList.add("linked"), 500 + i * t));
      later(() => sc.classList.add("principles"), 800 + rows.length * t);
    },
  };

  // site facts, measured from the drawing's shell and the satellite registration
  (function siteFacts() {
    const o = Z.annot.outline, dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]) / 1000;
    $("#fact-area").textContent = `≈${sqft(Z.floor_area)}`;
    $("#fact-len").textContent = `≈${Math.round((o[2][0] - o[0][0]) / 1000)} × ${Math.round((o[1][1] - o[3][1]) / 1000)} m`;
    if (D.site && $("#site-north")) $("#site-north").textContent = `North → right, ${Math.abs(D.site.north_deg).toFixed(1)}° off true north (checked against the satellite).`;
  })();

  /* ---- sun & light: the sun moving across the empty floor (NOAA solar position, ASHRAE clear sky) ---- */
  const SOLAR = (() => {
    const LAT = 12.9366189, LNG = 77.6917687, TZ = 5.5, R = Math.PI / 180;
    // ASHRAE clear-sky coefficients by month: A (W/m²), B (optical depth)
    const AB = [[1230, .142], [1215, .144], [1186, .156], [1136, .18], [1104, .196], [1088, .205], [1085, .207], [1107, .201], [1151, .177], [1192, .16], [1221, .149], [1233, .142]];
    const SEASONS = [
      { k: "mar", label: "20 Mar · 23 Sep", doy: 79, m: 2 },
      { k: "jun", label: "21 Jun", doy: 172, m: 5 },
      { k: "dec", label: "21 Dec", doy: 355, m: 11 },
    ];
    // NOAA "general solar position" equations
    function sun(doy, minutes) {
      const g = (2 * Math.PI / 365) * (doy - 1 + (minutes / 60 - 12) / 24);
      const eqt = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
      const dec = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
      const ha = ((minutes + eqt + 4 * LNG - 60 * TZ) / 4 - 180) * R, lat = LAT * R;
      const cz = Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(ha);
      const alt = 90 - Math.acos(Math.max(-1, Math.min(1, cz))) / R;
      const az = (Math.atan2(Math.sin(ha), Math.cos(ha) * Math.sin(lat) - Math.tan(dec) * Math.cos(lat)) / R + 180 + 360) % 360;
      return { az, alt, eqt, dec };
    }
    function riseSet(doy) {
      const { eqt, dec } = sun(doy, 720), lat = LAT * R;
      const h = Math.acos(Math.cos(90.833 * R) / (Math.cos(lat) * Math.cos(dec)) - Math.tan(lat) * Math.tan(dec)) / R;
      const hm = (m) => String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(Math.round(m % 60)).padStart(2, "0");
      return { rise: hm(720 - 4 * (LNG + h) - eqt + TZ * 60), set: hm(720 - 4 * (LNG - h) - eqt + TZ * 60) };
    }
    const dni = (m, alt) => (alt <= 0 ? 0 : AB[m][0] * Math.exp(-AB[m][1] / Math.sin(alt * R)));
    return { sun, riseSet, dni, SEASONS };
  })();

  // glazed façades from the floor outline (outward normal → compass bearing, using true north from the site registration)
  const SUNF = (() => {
    const o = Z.annot.outline, north = (D.site && D.site.north_deg) || 0;
    const area = o.reduce((a, p, i) => { const q = o[(i + 1) % o.length]; return a + p[0] * q[1] - q[0] * p[1]; }, 0);
    const face = (k, name, a, b, shaded) => {
      const P = Array.isArray(a) ? a : o[a], Q = Array.isArray(b) ? b : o[b], dx = Q[0] - P[0], dy = Q[1] - P[1], L = Math.hypot(dx, dy);
      const n = area < 0 ? [-dy / L, dx / L] : [dy / L, -dx / L];
      const brg = ((north - Math.atan2(n[1], n[0]) / (Math.PI / 180)) % 360 + 360) % 360;
      return { k, name, P, Q, n, brg, len: L / 1000, shaded: !!shaded };
    };
    // the glass is the prow and the long sides' first bays only (Sathwick, 12.10): the west side to x ≈ 37.4 m, the east to ≈ 35.5 m;
    // past them the long sides are solid
    const GLASS_W = 37400, GLASS_E = 35500;
    // the west glass and the upper prow face look onto the atrium, under its space-frame roof and across from the west block
    // (15.2 m, ≈22 m away): daylight, and only the sun the space frame lets through, softened (Sathwick)
    return { north, list: [face("SW", "south-west façade", 0, 1, true), face("W", "west façade", 1, [GLASS_W, o[1][1]], true),
      face("E", "east façade", [GLASS_E, o[4][1]], 4), face("SE", "south-east façade", 4, 0)] };
  })();
  const SUN_HEAD = 3000;                       // glass head height, mm (assumed)
  // the atrium's glass: the space-frame roof lets through about a third of the sun, dappled, and only once the sun clears
  // the west block: Level 03 is the top floor (slab at 11.4 m), so the block's 15.2 m roof stands only ≈2.3 m above the
  // glass's mid-height, ≈22 m across: it takes the sun below ≈6°
  const SHADE_T = 0.3, SHADE_ALT = 6;
  const COMP8 = (b) => ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][Math.round(((b % 360) + 360) % 360 / 45) % 8];
  // clip a polygon to the (convex) floor outline: Sutherland–Hodgman
  function clipToPlate(poly) {
    const o = Z.annot.outline, ccw = o.reduce((a, p, i) => { const q = o[(i + 1) % o.length]; return a + p[0] * q[1] - q[0] * p[1]; }, 0) > 0;
    let out = poly;
    for (let i = 0; i < o.length && out.length; i++) {
      const A = o[i], B = o[(i + 1) % o.length], inside = (p) => ((B[0] - A[0]) * (p[1] - A[1]) - (B[1] - A[1]) * (p[0] - A[0])) * (ccw ? 1 : -1) >= 0;
      const inp = out; out = [];
      inp.forEach((P, j) => {
        const Q = inp[(j + 1) % inp.length], pi = inside(P), qi = inside(Q);
        if (pi) out.push(P);
        if (pi !== qi) {
          const d1 = (B[0] - A[0]) * (P[1] - A[1]) - (B[1] - A[1]) * (P[0] - A[0]), d2 = (B[0] - A[0]) * (Q[1] - A[1]) - (B[1] - A[1]) * (Q[0] - A[0]);
          const t = d1 / (d1 - d2); out.push([P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t]);
        }
      });
    }
    return out;
  }
  const DAY0 = 7 * 60, DAY1 = 18 * 60 + 30;   // the run: 07:00 to 18:30
  const hhmm = (m) => String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(Math.floor(m % 60)).padStart(2, "0");
  // one moment of the day, at any minute: the sun, and the direct sun through each glazed face (c: how square the sun is to it)
  function sunAt(S, m) {
    const R = Math.PI / 180, { az, alt } = SOLAR.sun(S.doy, m), t = hhmm(Math.round(m / 5) * 5);
    if (alt <= 0) return { m, t, az, alt, dni: 0, p: [] };
    const dni = Math.round(SOLAR.dni(S.m, alt)), th = (SUNF.north - az) * R, s = [Math.cos(th), Math.sin(th)];
    const reach = Math.min(30000, SUN_HEAD / Math.tan(alt * R));
    const p = [];
    SUNF.list.forEach((F) => {
      const c = Math.cos((az - F.brg) * R);
      if (c <= 0.02) return;                                         // the sun is behind this glass
      // the atrium's glass: the west block takes the low sun, eased in and out over 10° so nothing pops
      const k = F.shaded ? clamp01((alt - SHADE_ALT + 5) / 10) : 1;
      if (k <= 0) return;
      const w = Math.round(dni * Math.cos(alt * R) * c * (F.shaded ? SHADE_T * k : 1)), v = [-s[0] * reach, -s[1] * reach];
      const poly = clipToPlate([F.P, F.Q, [F.Q[0] + v[0], F.Q[1] + v[1]], [F.P[0] + v[0], F.P[1] + v[1]]]);
      if (poly.length > 2) p.push({ f: F.k, w, c, depth: Math.min(30, (reach * c) / 1000), poly, filt: F.shaded, k: F.shaded ? 0.5 * k : 1 });
    });
    return { m, t, az, alt, dni, p, s, reach, low: alt < 15 };
  }
  // the day for one season, every half hour: for the written summary
  function sunDay(season) {
    const S = SOLAR.SEASONS.find((s) => s.k === season), rs = SOLAR.riseSet(S.doy), frames = [];
    for (let m = DAY0; m <= DAY1; m += 30) frames.push(sunAt(S, m));
    return { S, rise: rs.rise, set: rs.set, frames };
  }
  // the sun's path: a rounded rectangle 3.5 m clear of the plate; hit() runs from a point inside, along a direction, to the path
  const SUN_PATH = (() => {
    const o = Z.annot.outline, xs = o.map((q) => q[0]), ys = o.map((q) => q[1]), r = 3500;
    const IN = 2200;                    // the prow side runs only 1.3 m out, so the sun never crosses the column beside the plan
    const cx = (Math.min(...xs) + IN + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    const bx = (Math.max(...xs) - Math.min(...xs) - IN) / 2, by = (Math.max(...ys) - Math.min(...ys)) / 2;
    const sd = (x, y) => { const qx = Math.abs(x - cx) - bx, qy = Math.abs(y - cy) - by; return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r; };
    const hit = (gx, gy, dx, dy) => { let lo = 0, hi = 120000; for (let i = 0; i < 32; i++) { const k = (lo + hi) / 2; if (sd(gx + dx * k, gy + dy * k) < 0) lo = k; else hi = k; } return [gx + dx * hi, gy + dy * hi]; };
    return { cx, cy, hit };
  })();

  const SUNS = { season: "mar", m: DAY0, raf: null, day: null };
  const onSun = () => scenes[state.idx].id === "s-site";              // the sun runs on the floor, over its core (one beat, Sathwick)
  const sunColor = () => "#fbbc04";
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const sunTint = (a) => `rgb(${Math.round(255 - 4 * a)},${Math.round(255 - 67 * a)},${Math.round(255 - 251 * a)})`;   // white → deck yellow
  const sunFade = (fr) => clamp01((fr.alt - 8) / 12);                   // low sun fades in and out
  // how strongly one patch of sun shows: by how hard it falls on the glass, and how square the sun is to it
  function sunStrength(q, fr) {
    const f = sunFade(fr), x = Math.min(1, q.w / 1000);
    return (q.k ?? 1) * clamp01(fr.alt / 4) * clamp01(q.c / 0.2) * ((0.06 + 0.3 * x) * (1 - f) + (0.14 + 0.55 * x) * f);   // k: the atrium's softening
  }
  // how far in the west sun reaches by 4 pm: the edge the rooms along the west glass take in both layouts
  // the deepest the direct sun gets in, over the day, through the glass the atrium doesn't shade
  // (sun under 15° left out: trees and the buildings across the road usually take it)
  function sunEdge(S) { let d = 0; for (let m = DAY0; m <= DAY1; m += 15) { const f = sunAt(S, m); if (!f.low) f.p.forEach((q) => { if (q.c > 0.2 && !q.filt) d = Math.max(d, q.depth); }); } return d; }
  // how far a ray from a point just inside the glass runs across the floor before it leaves the plate (the plate is convex)
  function plateRun(x, y, dx, dy, max) {
    const o = Z.annot.outline, at = (k) => inPoly(x + dx * k, y + dy * k, o);
    if (!at(10)) return 0;
    if (at(max)) return max;
    let lo = 10, hi = max;
    for (let i = 0; i < 24; i++) { const k = (lo + hi) / 2; if (at(k)) lo = k; else hi = k; }
    return lo;
  }
  // the sun's sweep for a day: its bearing on the plan at sunrise, noon and sunset, unwrapped so it passes the noon side
  // (south in March and December, north in June)
  const SWEEP = {};
  function sunSweep(doy) {
    if (SWEEP[doy]) return SWEEP[doy];
    const th = (m) => (SUNF.north - SOLAR.sun(doy, m).az) * Math.PI / 180, wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
    let mR = 300, mS = 1260, mN = 720, top = -90;
    for (let m = 300; m <= 1260; m++) { const a = SOLAR.sun(doy, m).alt; if (a > 0 && mR === 300) mR = m; if (a > 0) mS = m; if (a > top) { top = a; mN = m; } }   // mN: noon, the side it passes
    const tR = th(mR), sweep = wrap(th(mN) - tR) + wrap(th(mS) - th(mN));
    // the path from the sunrise point to the sunset point, sampled, with the distance run so far
    const pts = [], run = [0];
    for (let i = 0; i <= 600; i++) { const a = tR + sweep * i / 600; pts.push(SUN_PATH.hit(SUN_PATH.cx, SUN_PATH.cy, Math.cos(a), Math.sin(a))); }
    for (let i = 1; i < pts.length; i++) run.push(run[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    return (SWEEP[doy] = { mR, mS, pts, run });
  }
  // the sun: on its path from the sunrise point to the sunset point, the distance along it even with the clock, so it glides
  // at one pace when played or dragged (its true bearing swings fast near noon). The light on the floor follows the true sun
  function sunPlace(fr) {
    if (fr.alt <= 0) return null;
    const th = (SUNF.north - fr.az) * Math.PI / 180, dx = Math.cos(th), dy = Math.sin(th);
    const W = sunSweep(SUNS.day.S.doy), L = W.run[W.run.length - 1] * clamp01((fr.m - W.mR) / (W.mS - W.mR));
    let i = 1; while (i < W.run.length - 1 && W.run[i] < L) i++;
    const t = clamp01((L - W.run[i - 1]) / ((W.run[i] - W.run[i - 1]) || 1)), A = W.pts[i - 1], B = W.pts[i];
    const lit = fr.p.map((q) => { const F = SUNF.list.find((g) => g.k === q.f); return { q, F, wt: q.w * F.len * clamp01(q.c / 0.2) }; });
    const sx = A[0] + (B[0] - A[0]) * t, sy = A[1] + (B[1] - A[1]) * t;
    return { sx, sy, dx, dy, lit };
  }
  // pacing: half by the clock, half by how far the sun travels on the plan, so it glides evenly
  // (around noon it swings past the prow quickly, and the clock slows a little there)
  function sunPace(S) {
    const ms = [], P = [];
    let arc = 0, prev = null;
    for (let m = DAY0; m <= DAY1; m += 2) {
      const at = sunPlace(sunAt(S, m));
      if (at && prev) arc += Math.hypot(at.sx - prev.sx, at.sy - prev.sy);
      prev = at; ms.push(m); P.push(arc);
    }
    return { ms, P: P.map((a, i) => 0.5 * (ms[i] - DAY0) / (DAY1 - DAY0) + 0.5 * (arc ? a / arc : (ms[i] - DAY0) / (DAY1 - DAY0))) };
  }
  const paceAt = (m) => { const { ms, P } = SUNS.pace, i = Math.min(ms.length - 2, Math.max(0, Math.floor((m - DAY0) / 2))); return P[i] + (P[i + 1] - P[i]) * clamp01((m - ms[i]) / 2); };
  const paceTo = (u) => { const { ms, P } = SUNS.pace; let lo = 0, hi = P.length - 1; while (hi - lo > 1) { const k = (lo + hi) >> 1; if (P[k] <= u) lo = k; else hi = k; } return ms[lo] + (ms[hi] - ms[lo]) * clamp01((u - P[lo]) / ((P[hi] - P[lo]) || 1)); };
  // the sun's foot on one glass: where the light from the sun meets that face (clamped to it)
  function sunFoot(F, sx, sy, dx, dy) {
    const ex = F.Q[0] - F.P[0], ey = F.Q[1] - F.P[1], rx = sx - F.P[0], ry = sy - F.P[1], det = dx * ey - dy * ex;
    const u = Math.abs(det) > 1e-6 ? (dx * ry - dy * rx) / det : (rx * ex + ry * ey) / (ex * ex + ey * ey);
    const k = Math.max(0, Math.min(1, u));
    return [F.P[0] + ex * k, F.P[1] + ey * k];
  }
  // the intensity follows the sun: each lit patch is brightest at the sun's foot on its glass and eases off along the glass and
  // into the floor. One radial gradient per face, kept in the plan's own <defs> (rebuilt with the plan, so made again if missing)
  const SUN_GLOW_R = 20000;
  function sunGlow(p, F, foot, a, dark) {
    const NS = "http://www.w3.org/2000/svg", id = `sun-glow-${F.k}-${p.host.id}`, defs = p.svg.querySelector("defs");
    let g = defs.querySelector("#" + id);
    if (!g) {
      g = document.createElementNS(NS, "radialGradient"); g.id = id; g.setAttribute("gradientUnits", "userSpaceOnUse");
      [0, 0.45, 1].forEach((o) => { const s = document.createElementNS(NS, "stop"); s.setAttribute("offset", o); g.appendChild(s); });
      defs.appendChild(g);
    }
    g.setAttribute("cx", Math.round(foot[0])); g.setAttribute("cy", Math.round(foot[1])); g.setAttribute("r", SUN_GLOW_R);
    [1, 0.6, 0.2].forEach((k, i) => {
      const s = g.children[i];
      if (dark) { s.setAttribute("stop-color", sunColor()); s.setAttribute("stop-opacity", (a * k).toFixed(3)); }
      else { s.setAttribute("stop-color", sunTint(a * k)); s.setAttribute("stop-opacity", 1); }
    });
    return `url(#${id})`;
  }
  // the 6 m daylight band: a strip in from each glass face, clipped to the plate
  const dayBand = () => SUNF.list.map((F) => clipToPlate([F.P, F.Q, [F.Q[0] - F.n[0] * DAYLIGHT, F.Q[1] - F.n[1] * DAYLIGHT], [F.P[0] - F.n[0] * DAYLIGHT, F.P[1] - F.n[1] * DAYLIGHT]]));
  function drawSunFrame() {
    const p = getPlanA(), fr = sunAt(SUNS.day.S, SUNS.m), col = sunColor(), dark = theme() === "dark";
    const band = [], patches = [], light = [], at = sunPlace(fr);
    // when the day is done, the daylight band fades in: drawn solid and darkened together, so where two strips meet it doesn't double
    // while the sun is up, every glass (the atrium's too) lets daylight in: a soft strip that brightens and fades with the sky,
    // so by dusk it is gone. The 6 m daylight band is a measure, not light: it shows only while its row is hovered (Sathwick)
    const sky = sunFade(fr);
    if (SUNS.band || SUNS.end) dayBand().forEach((q) => band.push({ kind: "poly", pts: q, fill: "#fce7ae", stroke: "none", fo: dark ? 0.35 : 1, cls: "day-band" + (dark ? "" : " sun-patch") }));
    else if (sky > 0.01) dayBand().forEach((q) => band.push({ kind: "poly", pts: q, fill: sunTint(0.07 * sky), stroke: "none", fo: dark ? 0.16 * sky : 1, cls: "day-band" + (dark ? "" : " sun-patch") }));
    // the sun on the floor now, brightest under the sun; on a light page drawn solid and darkened together, so overlaps show the stronger
    fr.p.forEach((q) => {
      const F = SUNF.list.find((g) => g.k === q.f), a = Math.min(0.92, sunStrength(q, fr) * (dark ? 1.35 : 1));
      const fill = at ? sunGlow(p, F, sunFoot(F, at.sx, at.sy, at.dx, at.dy), a, dark) : (dark ? col : sunTint(a));
      patches.push({ kind: "poly", pts: q.poly, fill, stroke: "none", fo: 1, cls: dark ? "" : "sun-patch" });
    });
    // the light comes in only through the glass: the lit glass glows, and the rays run in across the floor as far as the sun reaches
    fr.p.forEach((q) => {
      const F = SUNF.list.find((g) => g.k === q.f), a = sunStrength(q, fr), n = Math.max(1, Math.round(F.len / 12));
      light.push({ kind: "line", pts: [F.P, F.Q], stroke: dark ? col : sunTint(clamp01(0.35 * (q.k ?? 1) * clamp01(q.c / 0.2) + a)), sw: 5, cls: "sun-glass" });
      for (let j = 0; j < n; j++) {
        const t = (j + 0.5) / n, ex = F.P[0] + (F.Q[0] - F.P[0]) * t - F.n[0] * 250, ey = F.P[1] + (F.Q[1] - F.P[1]) * t - F.n[1] * 250;
        const L = plateRun(ex, ey, -fr.s[0], -fr.s[1], fr.reach);
        if (L > 1200) light.push({ kind: "line", pts: [[ex, ey], [ex - fr.s[0] * L, ey - fr.s[1] * L]], stroke: dark ? col : sunTint(clamp01(a / 0.45)), sw: 2.5, cls: "sun-ray" });
      }
    });
    // from 4 pm: the line the west sun has reached by then, the edge the rooms along the west glass take
    const Wf = SUNF.list.find((g) => g.k === "W");
    if (SUNS.m >= 16 * 60 && SUNS.edge && Wf && !Wf.shaded) {
      const W = Wf, d = SUNS.edge * 1000;
      light.push({ kind: "line", pts: [[W.P[0] - W.n[0] * d, W.P[1] - W.n[1] * d], [W.Q[0] - W.n[0] * d, W.Q[1] - W.n[1] * d]], stroke: dark ? col : "#d99a00", sw: 1.5, cls: "sun-edge" });
    }
    // the sun itself stays outside, beyond the glass it lights
    if (at) {
      const { sx, sy } = at, f = sunFade(fr);
      const circ = (r) => Array.from({ length: 28 }, (_, j) => [sx + r * Math.cos(j / 28 * 6.2832), sy + r * Math.sin(j / 28 * 6.2832)]);
      light.push({ kind: "poly", pts: circ(750), fill: col, stroke: "none", fo: clamp01(fr.alt / 4) * (0.55 + 0.45 * f), cls: "sun-disc" });
      for (let j = 0; j < 8; j++) { const b = j * Math.PI / 4; light.push({ kind: "line", pts: [[sx + Math.cos(b) * 1050, sy + Math.sin(b) * 1050], [sx + Math.cos(b) * 1450, sy + Math.sin(b) * 1450]], stroke: `rgba(251,188,4,${clamp01(fr.alt / 4).toFixed(2)})`, sw: 3 }); }
    }
    p.setOverlay(band.concat(coreParts(SUNS.coreFocus), patches, light));  // the core, part by part, stays under the sun
    // readout
    const top = fr.p.slice().sort((a, b) => b.w - a.w)[0], F = top && SUNF.list.find((g) => g.k === top.f);
    $("#sun-t").textContent = fr.t; if (!SUNS.glide) $("#sun-range").value = Math.round(SUNS.m);   // not under a dragging thumb
    $("#sun-read").innerHTML = fr.alt <= 0 ? `<b>${fr.t}</b> · the sun is down.` :
      `<b>${fr.t}</b> · sun in the ${COMP8(fr.az)} (${Math.round(fr.az)}°), ${Math.round(fr.alt)}° up · ${fr.dni} W/m² direct in a clear sky.` +
      (top ? ` Strongest on the ${F.name}: <b class="sun-w">${top.w} W/m²</b> on the glass, reaching ${top.depth.toFixed(1)} m in.` : " No direct sun on the glass.") +
      (fr.low ? ' <span class="sun-low">Very low sun: trees and buildings across the road will often block it.</span>' : "");
  }
  // the day runs continuously: 07:00–18:30 takes about 8 s
  const SUN_RUN = 8000;
  function sunStop() { cancelAnimationFrame(SUNS.raf); SUNS.raf = null; cancelAnimationFrame(SUNS.glide); SUNS.glide = null; $("#sun-play").classList.remove("on"); }
  // when the day has played to its end, the whole 6 m daylight band comes in as its summary (Sathwick); any change clears it
  function sunEnd(on) { SUNS.end = on; $("#s-site").classList.toggle("daylit", on); }
  function sunPlay() {
    sunStop(); sunEnd(false); $("#sun-play").classList.add("on");
    if (SUNS.m >= DAY1) SUNS.m = DAY0;
    drawSunFrame();
    let last = performance.now(), drawn = last, u = paceAt(SUNS.m);
    const tick = (now) => {
      u = Math.min(1, u + (now - last) / SUN_RUN); last = now;
      SUNS.m = u >= 1 ? DAY1 : paceTo(u);
      if (now - drawn >= 33 || SUNS.m >= DAY1) { drawn = now; drawSunFrame(); }
      if (SUNS.m >= DAY1) { sunStop(); later(() => { if (onSun() && !SUNS.raf && SUNS.m >= DAY1) { sunEnd(true); drawSunFrame(); } }, 700); return; }
      SUNS.raf = requestAnimationFrame(tick);
    };
    SUNS.raf = requestAnimationFrame(tick);
  }
  // the day in three beats, written from the numbers for the chosen season
  function sunBeats() {
    const D2 = SUNS.day, F = D2.frames.filter((f) => f.alt > 0 && f.p.length), win = (a, b) => F.filter((f) => f.t >= a && f.t <= b);
    const peak = (fs) => fs.reduce((b, f) => { f.p.forEach((q) => { if (!b || q.w > b.w) b = { ...q, t: f.t }; }); return b; }, null);
    const fname = (k) => SUNF.list.find((f) => f.k === k).name;
    const am = win("07:00", "10:30"), md = win("11:00", "13:30"), pm = win("14:00", "18:30");
    const mk = peak(am), pk = peak(pm), noon = D2.frames.reduce((b, f) => (f.alt > b.alt ? f : b), D2.frames[0]);
    const north = noon.az < 90 || noon.az > 270, mdDepth = Math.max(0, ...md.flatMap((f) => f.p.map((q) => q.depth)));
    return {
      peak: pk || mk,
      html: [
        ["Morning", `From sunrise at ${D2.rise} the sun comes in low from the ${COMP8(am[0] ? am[0].az : 90)}${mk ? ` onto the ${fname(mk.f)}: up to ${mk.w} W/m² on the glass by ${mk.t}, reaching ${mk.depth.toFixed(1)} m in` : ", but none of the glass faces it"}.`],
        ["Midday", `At noon the sun is ${Math.round(noon.alt)}° up, ${north ? "to the north" : "to the south"}. Direct sun shrinks to ${mdDepth.toFixed(1)} m or less inside the glass.`],
        ["Afternoon", pk ? `From 2 pm the sun swings ${COMP8(pm[0].az)} and drops: the ${fname(pk.f)} takes the hardest sun, ${pk.w} W/m² at ${pk.t}, reaching ${pk.depth.toFixed(0)} m in. Sunset ${D2.set}.` : `The afternoon sun stays off the glass. Sunset ${D2.set}.`],
      ].map(([h, t]) => `<p class="beat"><b>${h}.</b> ${t}</p>`).join(""),
    };
  }
  function sunSeason(k) {
    SUNS.season = k; SUNS.day = sunDay(k); SUNS.pace = sunPace(SUNS.day.S);
    SUNS.edge = sunEdge(SUNS.day.S);
    $("#sun-edge").textContent = `≈${Math.round(SUNS.edge * 2) / 2} m`;
    $$("#sun-season button").forEach((b) => b.classList.toggle("on", b.dataset.season === k));
    $("#sun-beats").innerHTML = sunBeats().html;
    if (onSun()) drawSunFrame();                             // otherwise just ready for the sun beat
  }

  /* ======================= Part 2 · the floor, one layer at a time (like the Acko deck) =======================
     The floor (what the building decided, then the sun across it) → carving → layout → types → teams → green → employee experience.
     Teams are named only once the layout exists; labels live in the legends, so nothing sits on a highlighted space. */
  const ptsOf = (d) => d.split("M").filter((s) => s.trim()).map((sp) => {
    const n = sp.replace(/[LZ]/g, " ").trim().split(/[\s,]+/).map(Number), out = [];
    for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], n[i + 1]]);
    return out;
  });
  const inPoly = (x, y, p) => { let c = false; for (let i = 0, j = p.length - 1; i < p.length; j = i++) { const [xi, yi] = p[i], [xj, yj] = p[j]; if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return c; };
  const bboxP = (p) => p.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [1e9, 1e9, -1e9, -1e9]);
  const segDist = (x, y, A, B) => { const dx = B[0] - A[0], dy = B[1] - A[1], t = Math.max(0, Math.min(1, ((x - A[0]) * dx + (y - A[1]) * dy) / (dx * dx + dy * dy || 1))); return Math.hypot(x - A[0] - t * dx, y - A[1] - t * dy); };
  const edgeDist = (x, y, p) => Math.min(...p.map((q, i) => segDist(x, y, q, p[(i + 1) % p.length])));
  const polyDist = (x, y, p) => (inPoly(x, y, p) ? 0 : edgeDist(x, y, p));
  const glassDist = (x, y) => Math.min(...SUNF.list.map((F) => segDist(x, y, F.P, F.Q)));
  const samples = (p, step) => { const [x0, y0, x1, y1] = bboxP(p), out = []; for (let x = x0 + step / 2; x < x1; x += step) for (let y = y0 + step / 2; y < y1; y += step) if (inPoly(x, y, p)) out.push([x, y]); return out; };
  const centroidP = (p) => window.Plan2D.centroid(p);
  const areaP = (p) => Math.abs(p.reduce((a, q, i) => { const r = p[(i + 1) % p.length]; return a + q[0] * r[1] - r[0] * q[1]; }, 0)) / 2e6;
  const circleP = (c, r, n) => Array.from({ length: n || 24 }, (_, i) => [c[0] + r * Math.cos((i / (n || 24)) * 6.2832), c[1] + r * Math.sin((i / (n || 24)) * 6.2832)]);
  const DAYLIGHT = 6000;                       // useful daylight ≈ 2 × the 3 m glass head
  const PLATE_PTS = samples(Z.annot.outline, 500);
  const PLATE_DAY = PLATE_PTS.filter(([x, y]) => glassDist(x, y) <= DAYLIGHT).length / PLATE_PTS.length;
  const zoneNamed = (o, re) => Z[o].zones.filter((z) => re.test(z.name || ""));
  // teams carry a PAX from the drawing; the agile workstations (no PAX) are not teams
  const teamsOf = (o) => Z[o].zones.filter((z) => (z.type === "soc" || z.type === "focus") && z.pax != null);
  const agileOf = (o) => Z[o].zones.filter((z) => z.agile);
  const TEAMC = ["#b5f4d9", "#a0bbeb", "#f2c596", "#e9c8ff", "#e4aba5", "#fce7ae", "#c9d3e0"];   // the deck's zoning palette
  // desk outlines per team (the CAD team hatches); the SOC has no hatch, its zone stands in
  const deskPolys = (o, withSoc) => Z[o].hover.teams.filter((t) => withSoc || !/SOC/i.test(t.name)).flatMap((t) => ptsOf(t.desks).filter((p) => p.length > 2));
  const deskPts = {};
  const deskSamples = (o) => deskPts[o] || (deskPts[o] = deskPolys(o, true).flatMap((p) => samples(p, 600)));
  const legendRow = (c, name, val, k) => `<li${k !== undefined ? ` data-k="${k}"` : ""}><i class="sw" style="background:${c}"></i><b>${name}</b><span>${val}</span></li>`;
  // hovering a legend row picks out its spaces on the plan
  function legendHover(list, on) {
    list.dataset.cur = "";
    list.onmouseover = (e) => { const li = e.target.closest("li[data-k]"); if (li && li.dataset.k !== list.dataset.cur) { list.dataset.cur = li.dataset.k; on(li.dataset.k); } };
    list.onmouseleave = () => { list.dataset.cur = ""; on(null); };
  }
  function layerPlan(o, layers) {
    const p = getPlanA();
    p.setOption(o); p.setOverlay([]); p.setNotes([]); p.setLinks([]); p.highlight(null); p.setCam(null); p.host.dataset.fac = ""; p.host.dataset.furn = "";
    p.setLayers(Object.assign({ furn: false, parts: false, walls: true, zones: false, labels: false, evo: false, tiers: false, facades: false, north: true, cams: false, routes: [],
      events: null, sig: false, hard: false, socglass: false, sat: false, hover: false, circ: false, ctl: true, render: false, entry: false, slab: true, names: false }, layers || {}));
    return p;
  }
  const layerScene = () => { frames("right"); world("plan", "map"); shade("left"); };

  // due diligence: what the base building has already fixed, colour-coded (no numbers, no labels on the plan)
  const DD = (() => {
    const zs = (re) => zoneNamed("opt1", re).map((z) => z.poly);
    const fire = D.opt1.texts.find((t) => /FIRE EXIT/i.test(t.t)), ent = zoneNamed("opt1", /main \/ entrance/i)[0];
    return [
      { k: "lift", c: "#a0bbeb", t: "Lifts and lift lobby", d: "In the core, on the east edge", polys: zs(/lift lobby/i) },
      { k: "fire", c: "#cc0000", t: "Fire stair", d: "Beside the lifts", polys: fire ? [circleP([fire.x, fire.y], 1100)] : [] },
      { k: "wc", c: "#b5f4d9", t: "Toilets", d: "In the core, north of the lifts", polys: zs(/washroom/i) },
      { k: "ahu", c: "#f2c596", t: "Two AHU rooms", d: "East edge: south of the core and at the north end", polys: zs(/ahu/i) },
      { k: "shaft", c: "#e9c8ff", t: "Shafts and risers", d: "In the core, and one in the south-east", polys: zs(/shaft|riser/i) },
      { k: "door", c: "#cc0000", t: "One front door", d: "The north-west corner", polys: ent ? [circleP(centroidP(ent.poly), 1300)] : [] },
    ];
  })();
  function drawDD(focus) {
    const items = [];
    DD.forEach((d) => d.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: d.c, stroke: d.c, fo: !focus || focus === d.k ? 0.85 : 0.1, sw: focus === d.k ? 2.5 : 1.5 })));
    getPlanA().setOverlay(items);
  }
  /* ---- 05 the floor: what the building decided (the core, the front door), then the sun across it ---- */
  // the core, part by part, from the 09.10 drawing (the same in both options). The spiral stair is the unnamed pieces east of the
  // lift lobby that the importer calls "Shaft / riser"; the real shafts are the two strips along the east wall below them
  const CORE_PARTS = (() => {
    const zs = Z.opt1.zones.filter((z) => z.type === "core"), top = (z) => Math.max(...z.poly.map((q) => q[1]));
    const part = (k, c, t, f) => { const ps = zs.filter(f); return { k, c, t, polys: ps.map((z) => z.poly), m2: Math.round(ps.reduce((a, z) => a + z.area, 0)) }; };
    return [
      part("lift", "#a0bbeb", "Lifts and lift lobby", (z) => /lift lobby/i.test(z.name)),
      part("stair", "#e4aba5", "Fire stair", (z) => /shaft|riser/i.test(z.name) && top(z) >= 5000),
      part("wc", "#b5f4d9", "Toilets", (z) => /washroom/i.test(z.name)),
      part("ahu", "#f2c596", "AHU rooms", (z) => /ahu/i.test(z.name)),
      part("shaft", "#e9c8ff", "Shafts and risers", (z) => /shaft|riser/i.test(z.name) && top(z) < 5000),
    ];
  })();
  // the red triangle, outside the main door (clear of its swing) and pointing in
  function entryTri(fo) {
    const e = Z.annot.labels.find((l) => l.kind === "entry");
    if (!e) return [];
    const [x, y] = e.at, tip = y + 1500, top = y + 3300;
    return [{ kind: "poly", pts: [[x - 900, top], [x + 900, top], [x, tip]], fill: "#cc0000", stroke: "#cc0000", fo, sw: 1 }];
  }
  // the deck's grey core and the entrance triangle; the sun beat keeps them under the sun
  function coreItems() {
    const cc = "#919191";
    return Z.opt1.zones.filter((z) => z.type === "core").map((z) => ({ kind: "poly", pts: z.poly, fill: cc, stroke: cc, fo: 0.75, sw: 1.5 })).concat(entryTri(1));
  }
  // its label sits just above the triangle, off the highlight
  const entryNote = () => { const e = Z.annot.labels.find((l) => l.kind === "entry"); return e ? [{ at: [e.at[0], e.at[1] + 3700], text: "Main entrance", kind: "entry" }] : []; };
  // the plate's length and depth from the outline: dimension lines outside the floor, their labels beside them (not on the plan)
  const DIMS = (() => {
    const o = Z.annot.outline, xs = o.map((q) => q[0]), ys = o.map((q) => q[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys), prow = o.find((q) => q[0] === x0);
    const ly = y0 - 2600, lx = 78400, ink = "#434343", ext = "#a6a6a6";   // lx: just past the east annex, inside the page's margin
    const tick = (x, y) => ({ kind: "line", pts: [[x - 450, y - 450], [x + 450, y + 450]], stroke: ink, sw: 1.6 });
    const ln = (a, b, c, w) => ({ kind: "line", pts: [a, b], stroke: c, sw: w });
    return {
      items: [
        ln([x0, prow[1] - 1500], [x0, ly - 700], ext, 0.8), ln([x1, y0 - 700], [x1, ly - 700], ext, 0.8), ln([x0, ly], [x1, ly], ink, 1.2), tick(x0, ly), tick(x1, ly),
        ln([78200, y1], [lx + 700, y1], ext, 0.8), ln([78200, y0], [lx + 700, y0], ext, 0.8), ln([lx, y0], [lx, y1], ink, 1.2), tick(lx, y0), tick(lx, y1),
      ],
      notes: [
        { at: [(x0 + x1) / 2, ly], text: `≈${Math.round((x1 - x0) / 1000)} m`, kind: "dim" },
        { at: [lx, (y0 + y1) / 2], text: `≈${Math.round((y1 - y0) / 1000)} m`, kind: "dim", rot: -90 },   // along the line, beside it
      ],
    };
  })();
  // beat 1: the core part by part (a legend row picks its part out), the entrance and the plate's size
  /* the core toilets against the code (NBCS 2026, SP 7, Part E Section 2 Table 1 Office Buildings; the ratios as IS 1172 and
     NBC 2016; men and women half each by its note 3, so 50:50 first): what the 09.10 drawing
     provides against what each option's seats need, for a chosen men : women split (Sathwick) */
  // the people: each option's seats (workstations and the SOC) in Mitigata's occupancy chart (Sathwick, 13.10)
  const NBC = { open: false, split: 50, have: { wc: 9, ur: 5, wb: 7, acc: 1 } };
  const nbcNeed = (n, split) => {
    const M = Math.round((n * split) / 100), F = n - M, up = Math.ceil;
    const ur = M <= 6 ? 0 : M <= 20 ? 1 : M <= 45 ? 2 : M <= 70 ? 3 : M <= 100 ? 4 : M <= 200 ? 4 + up((M - 100) * 0.03) : 7 + up((M - 200) * 0.025);
    return { M, F, wc: up(M / 25) + up(F / 15), wcM: up(M / 25), wcF: up(F / 15), ur, wb: up(M / 25) + up(F / 25), dw: Math.max(1, up(n / 100)) };
  };
  function nbcDraw() {
    const opts = ["opt1", "opt2"], h = NBC.have, mark = (a, b) => (a >= b ? '<i class="ok">✓</i>' : '<i class="dn">▼</i>');
    const qs = opts.map((o) => nbcNeed(occSum(o).seats, NBC.split));
    $("#nbc-head").innerHTML = `<th></th><th>Provided</th>${opts.map((o) => `<th>Option ${o === "opt2" ? "02" : "01"} · ${occSum(o).seats}</th>`).join("")}`;
    $("#nbc-body").innerHTML = [
      ["WCs", `${h.wc} <small>incl. 1 accessible</small>`, (q) => [h.wc >= q.wc, `${q.wc} <small>${q.wcM} men · ${q.wcF} women</small>`]],
      ["Urinals", `${h.ur}`, (q) => [h.ur >= q.ur, `${q.ur}`]],
      ["Wash basins", `${h.wb}`, (q) => [h.wb >= q.wb, `${q.wb}`]],
      ["Accessible WC", `${h.acc}`, () => [h.acc >= 1, "1"]],
    ].map(([a, b, f]) => `<tr><td>${a}</td><td>${b}</td>${qs.map((q) => { const [ok, t] = f(q); return `<td>${ok === null ? "" : ok ? mark(1, 0) : mark(0, 1)}${t}</td>`; }).join("")}</tr>`).join("");
    $$("#nbc-split button").forEach((b) => b.classList.toggle("on", +b.dataset.s === NBC.split));
  }
  function nbcWire(list, redraw) {
    const btn = $('#s-site [data-tool="nbc"]'), panel = $("#nbc-panel");   // the button bottom left, as the layout slides' (Sathwick)
    const set = (on) => { NBC.open = on; panel.classList.toggle("open", on); btn.classList.toggle("on", on); SUNS.coreFocus = on ? "wc" : null; if (on) nbcDraw(); redraw(); };
    btn.onclick = (e) => { e.currentTarget.blur(); set(!NBC.open); };
    $(".nbc-x", panel).onclick = (e) => { e.currentTarget.blur(); set(false); };
    $$("#nbc-split button").forEach((b) => (b.onclick = () => { b.blur(); NBC.split = +b.dataset.s; nbcDraw(); }));
    NBC.close = () => set(false);
  }
  function coreParts(focus) {
    const items = [];
    CORE_PARTS.forEach((d) => d.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: d.c, stroke: d.c, fo: !focus || focus === d.k ? 0.85 : 0.12, sw: focus === d.k ? 2.5 : 1.5 })));
    return items.concat(entryTri(!focus || focus === "door" ? 1 : 0.25), DIMS.items);
  }
  function drawCore(focus) { getPlanA().setOverlay(coreParts(focus)); }
  H["s-site"] = {
    enter() {
      const fromMap = world.cur === "map" || world.cur === "none";
      if (Math.abs(MAP.Z - 19) > 0.05) MAP.zoomTo(19, 0);
      FA.style.transition = "none"; frames("right"); void FA.offsetWidth;      // final frame size now, for the hand-off
      const p = layerPlan("opt1", { ctl: false, north: false });     // the north point is in the top bar
      p.fit(layView(p, $("#s-site")).view, 0); FA.style.transition = ""; ctlNorth(p);   // the layout slides' plan size (Sathwick)
      // the time of day joins the top bar, ahead of the north point (Sathwick)
      const row = $("#s-site .sunrow");
      if (row && !$(".ctl-sun", p.ctl)) { const w = document.createElement("span"); w.className = "ctl-sun"; w.appendChild(row); p.ctl.insertBefore(w, p.ctl.firstChild); }
      shade("");                                                        // the column no longer sits on the plan; a plain white page, no satellite under it (Sathwick)
      this.landing = fromMap && !!MAP.site;
      if (this.landing) {
        // the satellite turns (north -> right) and zooms until the roof sits on the plan, then the plan takes over
        // the plan (with its own still) fades in over the turned map, and only then does the map go, unseen under it
        world("map"); MAP.site.classList.add("on"); LAYERS.map.classList.add("turned"); $("#s-site").classList.add("landing");
        turnMapOntoPlan(p);
        later(() => { if (onSun()) { LAYERS.plan.classList.add("on"); p.setLayers({ ctl: true }); } }, 1600);
        later(() => { if (onSun()) world("plan"); }, 2500);
      } else { world("plan"); p.setLayers({ ctl: true }); }
      if (!SUNS.wired) {
        SUNS.wired = true;
        $$("#sun-season button").forEach((b) => (b.onclick = () => { b.blur(); sunSeason(b.dataset.season); if (onSun()) sunPlay(); }));
        $("#sun-play").onclick = (e) => { e.currentTarget.blur(); SUNS.raf ? sunStop() : sunPlay(); };
        const r = $("#sun-range");
        // dragging: the day glides to the thumb, frame by frame like the play, instead of snapping a step per event
        r.oninput = () => {
          if (SUNS.raf) sunStop();
          if (SUNS.end) sunEnd(false);
          SUNS.to = +r.value;
          if (SUNS.glide) return;
          const go = () => {
            const d = SUNS.to - SUNS.m;
            SUNS.m = Math.abs(d) < 0.5 ? SUNS.to : SUNS.m + d * 0.22;
            drawSunFrame();
            SUNS.glide = SUNS.m === SUNS.to || !onSun() ? null : requestAnimationFrame(go);
          };
          SUNS.glide = requestAnimationFrame(go);
        };
        r.onchange = r.onpointerup = () => r.blur();             // give the arrow keys back to the deck
      }
      sunSeason(SUNS.season);
      $("#dl-share").textContent = `${Math.round(PLATE_DAY * 100)}%`;
      $("#fact-glass").textContent = `≈${Math.round(SUNF.list.reduce((a, F) => a + F.len, 0))} m`;   // the glazed runs only
      const list = $("#core-list");
      if (!list.children.length) list.innerHTML = CORE_PARTS.map((d) => legendRow(d.c, d.t, sqft(d.m2), d.k)).join("") +
        `<li data-k="door"><i class="sw sw-tri"></i><b>Main entrance</b><span>north-west corner</span></li>`;
      legendHover(list, (k) => { SUNS.coreFocus = k || (NBC.open ? "wc" : null); if (!this.landing && !SUNS.raf) drawSunFrame(); });   // the sun's frame redraws the core
      nbcWire(list, () => { if (!this.landing && !SUNS.raf) drawSunFrame(); });
      const dl = $("#s-site .dl-fact");
      dl.onmouseenter = () => { SUNS.band = true; if (!this.landing && !SUNS.raf) drawSunFrame(); };
      dl.onmouseleave = () => { SUNS.band = false; if (!this.landing && !SUNS.raf) drawSunFrame(); };
    },
    step(k) {
      const p = getPlanA();
      sunStop(); sunEnd(false); p.setNotes([]); SUNS.band = false;
      // what the building decides: the core, part by part, the one front door and the plate's size; then the sun runs its day
      // across the same floor, half hour by half hour (the two beats fused, Sathwick)
      SUNS.coreFocus = null;
      const draw = () => {
        const landed = this.landing;
        this.landing = false; p.setLayers({ sat: false }); p.host.style.removeProperty("--sat-op");
        drawCore(null); p.setNotes(entryNote().concat(DIMS.notes));
        if (landed) { p.gOver.classList.remove("fade-in"); void p.gOver.getBoundingClientRect(); p.gOver.classList.add("fade-in"); }   // the core fades in, no pop
        later(() => { if (onSun()) { SUNS.m = DAY0; sunPlay(); } }, 1400);
      };
      if (this.landing) {   // the roof lands first; its still fades to the white page with the column, then the core
        p.setLayers({ sat: true }); p.setOverlay([]); p.host.style.setProperty("--sat-op", ".85");
        later(() => { if (onSun()) { p.host.style.setProperty("--sat-op", "0"); $("#s-site").classList.remove("landing"); } }, 2700);
        later(() => { if (onSun()) draw(); }, 3500);
      } else draw();
      p.fit(layView(p, $("#s-site")).view, 900);
      later(() => { if (onSun()) keyToFloor(p, $("#s-site .core-key")); }, 950);   // the core's key, level with the floor
    },
    theme() { if (onSun()) drawSunFrame(); else if (!this.landing) drawCore(null); },
    leave() { sunStop(); if (NBC.close) NBC.close(); $("#s-site").classList.remove("landing"); SUNS.band = false; sunEnd(false); getPlanA().host.style.removeProperty("--sat-op"); const p = getPlanA(); p.setOverlay([]); p.setNotes([]); p.setLayers({ sat: false }); untwistMap(); },
  };

  /* ======================= from brief to plan (Ritika, 11.10) =======================
     06 the brief as bubbles, with their adjacencies → each option in turn: bubble zoning on the floor → the zoning becomes the layout
     (coloured to the same outlines hover uses, the building core included: not in contract; furniture on top) → ①②③, one highlight each
     → the two options against the brief → the two options in 3D. Colours and legends: the deck's zoning (slide 21).
     Every plan beat carries the north point and the entry arrow. */
  const P2 = () => window.Plan2D;
  const planScene = () => { frames("right"); world("plan"); shade("left"); };   // white pages: no satellite under the plans here
  const OPTLBL = OPTNAME;
  const LAY_BOX = [5600, -200, 79200, 38200];                      // the floor, its north point and its entry arrow
  /* the layout slides: the plan frame runs the page's width and every step frames the floor the same way, right of
     the column (so the plan never changes size); on the brief, the squares fill the column under the layer list */
  function layView(p, S) {
    const fe = p.host.parentNode, tr = fe.style.transition;           // the frame's final size, not mid-transition
    fe.style.transition = "none"; void fe.offsetWidth;
    const fr = p.host.getBoundingClientRect(), cr = ($(".lay-copy", S) || $(".copy", S)).getBoundingClientRect();
    fe.style.transition = tr;
    const off = Math.max(0, cr.right + 24 - fr.left), W = Math.max(100, fr.width - off), H = fr.height;   // the plan as large as the page allows; the squares fit the column (Sathwick)
    const [x0, y0, x1, y1] = LAY_BOX, s = Math.max((x1 - x0) / W, (y1 - y0) / H), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const vx0 = cx - (W / 2 + off) * s, vy1 = cy + (H / 2) * s;
    return { view: [vx0, vy1 - H * s, vx0 + fr.width * s, vy1], s, vx0, vy1, fr, off };
  }
  // the brief's bar: the text column, from under the kicker (the headline is gone, Ritika 14.10) to just above the timeline's row
  // (call once the view is applied)
  function layTileBox(p, S) {
    const hr = p.host.getBoundingClientRect(), cr = $(".lay-copy", S).getBoundingClientRect(), tb = $(".lay-copy .kicker", S).getBoundingClientRect();
    const [x0, y1] = p.fromScreen(cr.left - hr.left, tb.bottom + 76 - hr.top), [x1, y0] = p.fromScreen(cr.right - hr.left, hr.height - 66);
    return [x0, y0, x1, y1];
  }
  const DZ_ORDER = ["arrival", "meet", "focus", "collab", "soc", "board", "cafe", "support", "nic"];
  const dzName = (k) => (k === "nic" ? "Not in contract" : P2().DZ[k].n);
  const dzSw = (k, pal) => `<i class="sw${k === "nic" && !(pal && pal.hatch === "none") ? " sw-nic" : ""}" style="background-color:${(pal && pal[k]) || P2().DZ[k].c}"></i>`;
  // the layout slides' own palette (Sathwick, 13.10), nine colours from the two reference boards and the logo's green
  // (café, collaborate, arrival and boardroom softened 35% towards white: the full colours read too harsh; the SOC in the
  // 3D views' pale mint; the café in softened terracotta, apart from it);
  // the other slides keep the deck's zoning pastels
  const LAY_PAL = { soc: "#B5F4D9", cafe: "#D88E83", meet: "#D8F6EE", focus: "#EFE2D1", arrival: "#F2CA9C", collab: "#B6B9FF",
    support: "#55634A", board: "#5A8B85", nic: "#758386", hatch: "none" };   // the core plain (the hatch read too busy), in the shade the zoning shows it (Sathwick)
  // the teams (Sathwick, 13.10): from the layout's palette, at its tone; each team apart from the others and the grey
  const LAY_TEAM = { soc: "#B5F4D9", delivery: "#B6B9FF", product: "#F2CA9C", sales: "#D88E83", "sales calling": "#5A8B85", "hr & finance": "#909A89" };
  const LAY_AGILE = "#ececec";   // the agile desks: grey with the rest, they're no team's (Sathwick)
  const NAMES = { focus: "Workhall", soc: "SOC", secure: "Server · UPS", collab: "Breakout", quiet: "Booths", meet: "Meeting rooms", arrive: "Arrival",
    board: "Boardroom", cafe: "Café", studio: "Podcast studio", service: "Stores" };
  const SHORTN = (t) => NAMES[t] || P2().SHORT[t] || t;
  const ADJ_KIND = { next: "Next to", near: "Near", seen: "Seen, never entered" };
  // the brief lists no adjacencies: these are SKV's, for Ritika to check
  const ADJ_WHY = {
    "arrive|board": "Guests reach the boardroom without crossing team space.",
    "arrive|meet": "Client meetings stay at the front of the floor.",
    "arrive|cafe": "Arrivals and events spill into the café.",
    "arrive|soc": "Guests see the SOC, but never enter it.",
    "soc|secure": "The server room and the SOC share one secure line.",
    "soc|focus": "The teams the SOC works with sit around it.",
    "soc|collab": "Huddles happen beside the SOC, not inside it.",
    "focus|collab": "Teams break out without leaving their workhall.",
    "focus|quiet": "A booth for calls within each workhall.",
    "focus|meet": "Every team is a few steps from a meeting room.",
    "cafe|studio": "Content and events share the social end.",
    "board|service": "The prep counter serves the boardroom's dinners.",
  };
  const ADJ_KEY = ["arrive|soc", "arrive|board", "soc|secure", "focus|collab"];   // the four that shape the plan
  const adjOf = (key) => P2().ADJ.find(([a, b]) => a + "|" + b === key);
  // why each zone sits where it does: the deck's own zoning copy (slides 21 and 23), with what the site decided
  const WHY_ALL = {
    arrival: "A warm, secure arrival with turnstiles, at the one front door.",
    focus: "A flexible mix of dedicated and agile desks that turns into event space.",
    collab: "Breakouts that spark spontaneous collaboration.",
    support: "Server, UPS and stores, off the main path.",
    nic: "The building core, fixed on the east edge: not in contract.",
  };
  const ZONE_WHY = {
    opt1: Object.assign({}, WHY_ALL, {
      soc: "Visible by design, secure by its position: a glass arc to the atrium.",
      meet: "Perimeter rooms: a daylight buffer for the workhall.",
      board: "Boardroom and dining in one, at the far end.",
      cafe: "A space to pause, connect and recharge, beside the studio.",
    }),
    opt2: Object.assign({}, WHY_ALL, {
      soc: "Visible by design, secure by its placement: at the prow, towards the gate.",
      meet: "Seamless meeting access from every workhall.",
      board: "Boardroom and dining in one, a short walk from arrival.",
      cafe: "One space, two modes: café by day, training room when needed.",
    }),
  };
  // what the plan says when a bubble or a link is hovered (the label sits beside it)
  const bubbleTip = (o) => (kind, key, dz, s) => {
    if (kind === "link") { const l = adjOf(key), [a, b] = key.split("|"); return `<b>${SHORTN(a)} – ${SHORTN(b)}</b><span>${ADJ_KIND[l[2]]} · ${ADJ_WHY[key]}</span>`; }
    if (s < 0.5) {         // a brief bubble: what it sits with
      const by = {}; P2().ADJ.forEach(([a, b, k]) => { if (a === key || b === key) (by[k] = by[k] || []).push(SHORTN(a === key ? b : a)); });
      const parts = [by.next && `next to ${by.next.join(", ")}`, by.near && `near ${by.near.join(", ")}`, by.seen && (key === "soc" ? `seen from ${by.seen.join(", ")}, never entered` : `sees the ${by.seen.join(", ")}, never enters`)].filter(Boolean);
      return `<b>${P2().BRIEF[key] || SHORTN(key)}</b><span>${dzName(dz)} · ${parts.join(" · ")}</span>`;
    }
    return `<b>${dzName(dz)} · ${SHORTN(key)}</b><span>${ZONE_WHY[o][dz] || ""}</span>`;
  };

  /* ---- 06 the brief, as bubbles ---- */
  H["s-carve"] = {
    enter() {
      planScene();
      $("#adj-zones").innerHTML = DZ_ORDER.filter((k) => k !== "nic").map((k) => `<li>${dzSw(k)}<b>${dzName(k)}</b></li>`).join("");
      $("#adj-why").innerHTML = ADJ_KEY.map((key) => { const [a, b] = key.split("|"); return `<li><i class="sw-adj ${adjOf(key)[2]}"></i><b>${SHORTN(a)} – ${SHORTN(b)}</b><span>${ADJ_WHY[key]}</span></li>`; }).join("");
    },
    step() {
      const p = getPlanA(), glide = p.opt === "opt1" && p.L.evo;    // back from Option 01's bubble zoning: the bubbles lift off the floor
      layerPlan("opt1", { evo: true, walls: false, slab: false, north: false });
      p.evoTip = bubbleTip("opt1"); p.setEvoStart("adj");
      p.setEvo(0, glide ? 1400 : 0);
      p.fit(p.evoBox(2400), glide ? 1200 : 700);
    },
    leave() { getPlanA().setLayers({ slab: true }); },
  };

  /* ---- 07 / 08 each option: bubble zoning → the layout → ①②③ ---- */
  const GUEST = ["arrival", "meet", "board"];
  const cafePax = (o) => paxIn(o, /CAF.*\d+\s*PAX/i, 52);
  const PR = {
    opt1: [
      "A curved glass SOC on the main path, facing the atrium: seen from the court, never entered.",
      "Every visitor walks past the SOC to the boardroom at the far end.",
      "Chance meetings in the breakouts between the teams; the café and the studio share the north end, and for a town hall the workhall faces the SOC as a 200-person stage.",
    ],
    opt2: [
      "The SOC holds the prow, with a display wall on the central corridor: seen from the road side.",
      "Arrival, boardroom and meeting rooms stay by the front door: guests never cross the floor.",
      "Chance meetings at the breakout and lounge on the central hub; the café turns into a training room, and the central hall opens end to end for 200, the SOC display wall as the stage.",
    ],
  };
  // one highlight per beat: which zones keep their colour, and what is drawn over them
  const PR_HL = [
    { keep: ["soc"], soc: true },
    { keep: GUEST, route: true },
    { keep: ["collab", "cafe"], events: "200" },
  ];
  const PR_FACTS = [
    (o) => { const z = zonesOf(o, "soc")[0], s = teamSeats(o, z); return [[`${s.seats}${s.seats < s.pax ? ` <small>of ${s.pax}</small>` : ""}`, "SOC seats"], [`≈${sqft(z.area)}`, "of SOC"]]; },
    (o) => [[`${Z[o].routes.visitor.m} m`, "front door to boardroom"], [`${sqft(areaOf(o, ["arrive", "board", "meet"]))}`, "of guest spaces"]],
    (o) => [[`${zonesOf(o, "collab").length}`, "breakouts and lounges"], [`${sqft(Z[o].events["200"].area)}`, "a 200-person stage"]],
  ];
  const PR_LGD = [
    () => `<li>${dzSw("soc")}<b>SOC</b><span>outlined in green</span></li>`,
    () => GUEST.map((k) => `<li>${dzSw(k)}<b>${dzName(k)}</b><span>guest</span></li>`).join("") + `<li><i class="sw-route solid"></i><b>The visitor's walk</b><span>front door → boardroom</span></li>`,
    () => `<li>${dzSw("collab")}<b>${dzName("collab")}</b><span>chance meetings</span></li><li>${dzSw("cafe")}<b>${dzName("cafe")}</b><span>a shared stage</span></li>` +
      `<li><i class="sw sw-evt"></i><b>The event hall</b><span>200 people</span></li>`,
  ];
  // the short line each layer keeps once the next one arrives
  const PR_SHORT = {
    opt1: () => ["each zone where it works best", "exact outlines, walls and furniture", teamsLine("opt1"), "a curved glass SOC facing the atrium",
      `${Z.opt1.routes.visitor.m} m past the SOC to the boardroom`, "chance meetings; a 200-person stage"],
    opt2: () => ["each zone where it works best", "exact outlines, walls and furniture", teamsLine("opt2"), "the SOC holds the prow",
      `${Z.opt2.routes.visitor.m} m from the front door to the boardroom`, "a hub for chance meetings; café by day, training room by four"],
  };
  // the teams layer (Ritika): every other space grey, the shared agile desks too, each team in its colour (Sathwick's
  // mapping, 13.10); in A3's order (SOC first, then by seats)
  const teamTones = (o) => {
    const rows = Z[o].hover.teams.map((t) => teamSeats(o, t)).sort((a, b) => /SOC/i.test(b.name) - /SOC/i.test(a.name) || b.seats - a.seats), map = {};
    rows.forEach((t, i) => (map[t.id] = LAY_TEAM[t.name.toLowerCase()] || TEAMC[i % TEAMC.length]));
    return { map, rows };
  };
  const teamsLine = (o) => { const t = Z[o].hover.teams.map((x) => teamSeats(o, x)); return `${t.length} teams, ${t.reduce((a, x) => a + x.seats, 0)} seats`; };
  function layoutCopy(o, S) {
    const why = ZONE_WHY[o] || {}, present = new Set(Z[o].zones.map((z) => P2().dzOf(z.type, z.name)));
    if ($('[data-lg="why"]', S)) $('[data-lg="why"]', S).innerHTML = DZ_ORDER.filter((k) => present.has(k)).map((k) => `<li data-k="${k}">${dzSw(k, LAY_PAL)}<b>${dzName(k)}</b><span>${why[k] || ""}</span></li>`).join("");
    const m2 = {}; Z[o].zones.forEach((z) => { const k = P2().dzOf(z.type, z.name); m2[k] = (m2[k] || 0) + z.area; });
    const corr = Z[o].hover.rooms.filter((r) => P2().roomType(r.name) === "circ").reduce((a, r) => a + r.m2, 0);
    $('[data-lg="zones"]', S).innerHTML = DZ_ORDER.filter((k) => m2[k]).map((k) => `<li data-k="${k}">${dzSw(k, LAY_PAL)}<b>${dzName(k)}</b><span>${sqft(m2[k])}</span></li>`).join("") +
      `<li data-k="circ"><i class="sw sw-circ" style="background-color:${P2().CIRC_COL}"></i><b>Circulation</b><span>${sqft(corr)}</span></li>` +
      `<li><i class="sw sw-tri"></i><b>Main entrance</b><span></span></li>`;
    (PR[o] || []).forEach((t, i) => {
      if (!$(`[data-pr="${i + 1}"]`, S)) return;                       // Option 01 dropped its ①②③ layers (Sathwick)
      $(`[data-pr="${i + 1}"]`, S).textContent = t;
      $(`[data-facts="${i + 1}"]`, S).innerHTML = PR_FACTS[i](o).map(([b, s]) => `<div class="fact"><b>${b}</b><span>${s}</span></div>`).join("");
      $(`[data-lg="${i + 1}"]`, S).innerHTML = PR_LGD[i]();
    });
    const q = occSum(o), det = $(".occ", S);
    $("summary", det).innerHTML = `<span>Occupancy</span><b>${q.seats} seats · ${q.rooms} meeting rooms</b>`;
    $(".occ-body", det).innerHTML = occTable([o]);
    const op = det.closest(".lay-panel");
    if (op) op.dataset.opt = o;
    if (op && !$(".occ-xp", op)) {   // the expand button (Ritika, 14.10)
      const xp = document.createElement("button"); xp.type = "button"; xp.className = "occ-xp";
      xp.onclick = (e) => { e.stopPropagation(); xp.blur(); occBig(op, !op.classList.contains("big")); };   // the arrow keys stay with the deck
      op.insertBefore(xp, op.firstChild); occBig(op, false);
    }
    $("summary", det).onclick = (e) => { const s = e.currentTarget; setTimeout(() => s.blur(), 0); };   // the arrow keys stay with the deck
    if ($('[data-lg="why"]', S)) legendHover($('[data-lg="why"]', S), (k) => getPlanA().evoFocus(k));
    legendHover($('[data-lg="zones"]', S), (k) => getPlanA().renderFocus(k ? [k] : null));
    (PR_SHORT[o] ? PR_SHORT[o]() : []).forEach((t, i) => { const e = $(`[data-short="${i + 1}"]`, S); if (e) e.textContent = t; });
    const tt = teamTones(o), agile = agileOf(o);
    $('[data-lg="teams"]', S).innerHTML = tt.rows.map((t) => `<li data-k="${t.id}"><i class="sw" style="background-color:${tt.map[t.id]}"></i><b>${t.name}</b><span>${t.seats} seats</span></li>`).join("") +
      (agile.length ? `<li><i class="sw" style="background-color:${LAY_AGILE}"></i><b>Agile desks</b><span>shared · ≈${Math.round(sumOf(agile, (z) => z.area) / 2.5)}</span></li>` : "");
    $('[data-facts="teams"]', S).textContent = `${tt.rows.length} teams, ${tt.rows.reduce((a, t) => a + t.seats, 0)} seats with the SOC; agile desks shared. Every team has its own TV screen.`;
    legendHover($('[data-lg="teams"]', S), (k) => getPlanA().renderFocus(k ? [k] : null));
  }
  // the plan's toolbar starts with the north point (true north, from the satellite registration); shown on the layout slides
  function ctlNorth(p) {
    if ($(".ctl-north", p.ctl)) return;
    const a = ((D.site && D.site.north_deg) || 0) * Math.PI / 180, x = 13 + 9 * Math.cos(a), y = 13 - 9 * Math.sin(a);
    p.ctl.insertAdjacentHTML("afterbegin", `<span class="ctl-north" title="North (${Math.abs(((D.site && D.site.north_deg) || 0)).toFixed(1)}° off the drawing)">` +
      `<svg viewBox="0 0 26 26" aria-hidden="true"><circle cx="13" cy="13" r="10"/><line x1="13" y1="13" x2="${x.toFixed(2)}" y2="${y.toFixed(2)}"/></svg><b>N</b></span>`);
  }
  /* the layout slides' tools (bottom left): one base plan; "layout" or "teams" lays its colours over it (one at a time, or
     neither), each with its legend; "occ" opens the occupancy; on step 1 "zones" opens the bubbles' reasons (Sathwick) */
  const LAY = { col: null, panel: null, hover: true };   // col: the colours on the plan (their legend in the column); panel: occupancy
  // hover on / off (Ritika, 14.10): a button after Area in the plan's toolbar, on the layout slides only; it stays as set
  function ctlHover(p, on) {
    let b = $(".ctl-hover", p.ctl);
    if (!on) { if (b) b.remove(); p.host.classList.remove("no-hover"); return; }
    if (!b) {
      b = document.createElement("button"); b.type = "button"; b.className = "ctl-hover"; b.textContent = "Hover"; b.title = "Room names on hover: on / off";
      b.onclick = () => { b.blur(); LAY.hover = !LAY.hover; ctlHover(p, true); };   // the arrow keys stay with the deck
      p.ctl.insertBefore(b, $(".m-read", p.ctl));
    }
    b.classList.toggle("on", LAY.hover); p.host.classList.toggle("no-hover", !LAY.hover);
  }
  // the occupancy panel, expanded (centred and larger) or back in its place
  // expanded, the table shows the three options side by side (Sathwick, 15.10); back in its place, this slide's option
  function occBig(op, on) {
    if (!op) return;
    if (op.dataset.opt && op.classList.contains("big") !== on) $(".occ-body", op).innerHTML = occTable(on ? ["opt1", "opt2", "opt3"] : [op.dataset.opt]);
    op.classList.toggle("big", on);
    const xp = $(".occ-xp", op); if (xp) { xp.textContent = on ? "✕" : "⤢"; xp.title = on ? "Close" : "Expand"; xp.setAttribute("aria-label", on ? "Close the occupancy" : "Expand the occupancy"); }
  }
  document.addEventListener("keydown", (e) => { const b = $(".lay-panel.big"); if (e.key === "Escape" && b) { occBig(b, false); e.stopImmediatePropagation(); } }, true);
  document.addEventListener("pointerdown", (e) => { const b = $(".lay-panel.big"); if (b && !b.contains(e.target)) occBig(b, false); }, true);
  const layStep = (S) => +S.dataset.steps;   // the layout: the last step (Options 01, 02: after the brief and the zoning; 03: the only one)
  function layApply(S, o) {
    const p = getPlanA(), c = LAY.col;
    // layout: the zoning colours; teams: each team's area in its colour, the rest grey; neither: the floor all grey
    p.setLayers({ render: true }); p.renderFocus(null);
    p.renderMono(c !== "layout"); p.teamColours(c === "teams" ? teamTones(o).map : null); p.setNameTeams(c === "teams");
    if (p.g.render) p.g.render.classList.toggle("bare", !c);
    $$(".lay-btns button[data-tool]", S).forEach((b) => b.classList.toggle("on", b.dataset.tool === c || b.dataset.tool === LAY.panel));
    $$(".lay-panel", S).forEach((x) => { x.classList.toggle("open", x.dataset.panel === LAY.panel); if (x.dataset.panel !== LAY.panel) occBig(x, false); });
    layKey(S);
  }
  // the legend of the colours on the plan, in the column, its bottom level with the floor's (like the zoning's key)
  function layKey(S) {
    $$(".col-key", S).forEach((k) => { k.hidden = state.step !== layStep(S) || k.dataset.key !== LAY.col; if (!k.hidden) keyToFloor(getPlanA(), k); });
  }
  function layTools(S, o, k) {
    const t = $(".lay-tools", S); if (!t) return false;
    $$(".layer-list li", S).forEach((li) => li.onclick = () => { if (+li.dataset.step !== state.step) setStep(+li.dataset.step); });   // the steps, clickable
    LAY.col = k === layStep(S) ? "layout" : null; LAY.panel = null;   // the layout opens on its colours
    $$(".col-key", S).forEach((x) => (x.hidden = true));     // until the layout has come in
    $$(".lay-btns button", t).forEach((b) => b.onclick = () => {
      b.blur(); const k2 = b.dataset.tool;                                      // the arrow keys stay with the deck
      if (k2 === "layout" || k2 === "teams" || k2 === "acoustics") {           // the colours on or off (one at a time), their legend with them;
                                                                                // acoustics: the bare plan until Ritika's layout comes
        LAY.col = LAY.col === k2 ? null : k2;
        if (state.step >= layStep(S)) layApply(S, o);
      }
      else { LAY.panel = LAY.panel === k2 ? null : k2; if (state.step < layStep(S)) { $$(".lay-panel", S).forEach((x) => x.classList.toggle("open", x.dataset.panel === LAY.panel)); b.classList.toggle("on", LAY.panel === k2); } else layApply(S, o); }
    });
    $$(".lay-btns button", t).forEach((b) => b.classList.remove("on", "open")); $$(".lay-panel", t).forEach((x) => { x.classList.remove("open"); occBig(x, false); });
    return true;
  }
  // a slide's key sits with its bottom level with the floor's bottom edge (the layout slides' zoning key, the floor's core key)
  function keyToFloor(p, key) {
    const hr = p.host.getBoundingClientRect(), fb = hr.top + p.toScreen([LAY_BOX[0], 2150])[1], kr = key.getBoundingClientRect();
    key.style.marginTop = Math.max(18, parseFloat(key.style.marginTop || 18) + fb - kr.bottom) + "px";
  }
  function layoutHook(o) {
    const sec = () => $({ opt1: "#s-arc", opt2: "#s-net", opt3: "#s-opt3" }[o]), here = (k) => scenes[state.idx] === sec() && state.step === k;
    const base = { walls: true, slab: true, north: false, entry: true };   // the north point is in the toolbar
    return {
      enter() { planScene(); shade(""); getPlanA().setPalette(LAY_PAL); layoutCopy(o, sec()); ctlNorth(getPlanA()); ctlHover(getPlanA(), true); },   // no white wash: the column no longer sits on the plan
      step(k) {
        const p = getPlanA();
        frames("right", OPTLBL[o]); p.evoTip = bubbleTip(o);
        $$(".layer-list li", sec()).forEach((li) => li.classList.toggle("now", +li.dataset.step === k));   // the layer on screen is open ("now": .cur is the presenter cursor's)
        const tools = layTools(sec(), o, k);
        if (layStep(sec()) === 1) {   // Option 03: no brief, no zoning; the layout straight away (Sathwick, 15.10)
          layerPlan(o, Object.assign({ evo: false, parts: false }, base));
          p.renderFocus(null); p.evoFocus(null);
          p.fit(layView(p, sec()).view, 0);
          p.setLayers({ render: true, furn: true, parts: true, hover: true, names: true }); p.teamColours(null); p.renderMono(false);
          if (tools) layApply(sec(), o);
          later(() => { if (here(1)) layKey(sec()); }, 750);   // once the view has settled, level with the floor
        } else if (k === 1) {        // the brief: one square per space, area-proportional, under the empty floor (Sathwick)
          const back = p.opt === o && p.L.evo && p.evoStart === "tiles";
          layerPlan(o, Object.assign({ evo: true, parts: false }, base));
          p.renderFocus(null); p.evoFocus(null); p.renderMono(false); p.teamColours(null);
          p.fit(layView(p, sec()).view, 0); p.setTileBox(layTileBox(p, sec())); p.setEvoStart("tiles");
          p.setEvo(0, back ? 1500 : 0);
        } else if (k === 2) { // zoning: the squares move onto the floor and take each zone's exact outline (or back from the layout)
          const fromBrief = p.opt === o && p.L.evo && p.evoStart === "tiles" && p.evoS < 1;
          layerPlan(o, Object.assign({ evo: true, parts: false }, base));
          p.renderFocus(null); p.evoFocus(null); p.renderMono(false); p.teamColours(null);
          const lv = layView(p, sec()).view;
          if (p.evoStart !== "tiles") { p.fit(lv, 0); p.setTileBox(layTileBox(p, sec())); p.setEvoStart("tiles"); p.setEvo(0, 0); }
          else p.fit(lv, fromBrief ? 0 : 900);
          p.setEvo(2, fromBrief ? 2600 : 1200);
          // the zones' key comes in once the bar has landed as the zoning, its bottom level with the floor's
          const key = $(".zone-key", sec());
          if (key) {
            key.classList.add("wait");
            later(() => {
              if (!here(2)) return;
              keyToFloor(p, key); key.classList.remove("wait");
            }, fromBrief ? 2600 : 1200);
          }
        } else if (k === 3) { // the zoning becomes the layout: walls, glass, furniture and the colours
          const fromZoning = p.opt === o && p.L.evo;
          layerPlan(o, Object.assign({ evo: true, parts: false }, base));
          p.renderFocus(null); p.evoFocus(null); p.renderMono(false); p.teamColours(null);
          if (!fromZoning) p.setEvo(2, 0);
          p.setEvo(2, 400);
          p.fit(layView(p, sec()).view, 900);
          // a cross-fade: the layout, its walls and furniture come in under the zoning, which then fades away (Sathwick)
          later(() => {
            if (!here(3)) return;
            p.setLayers({ evo: true, render: true, furn: true, parts: true, hover: true, names: true }); p.teamColours(null); p.renderMono(false);   // every space named (Sathwick: the PDF has no hover)
            if (tools) layApply(sec(), o);
            later(() => { if (here(3)) layKey(sec()); }, 750);   // once the view has settled, level with the floor again
            const ge = p.evoGroup; ge.style.transition = "opacity .9s ease"; ge.style.opacity = "0";
            later(() => { ge.style.transition = ""; ge.style.opacity = ""; if (here(3)) p.setLayers({ evo: false }); }, 950);
          }, 200);
        }
      },
      leave() {
        const p = getPlanA(); p.setLayers({ render: false, entry: false, evo: false, routes: [], circ: false, hover: false, events: null, names: false }); p.setPalette(null); p.setNameTeams(false);
        ctlHover(p, false); occBig($('.lay-panel[data-panel="occ"]', sec()), false);
        p.renderFocus(null); p.evoFocus(null); p.setOverlay([]); p.teamColours(null); p.renderMono(false);
        if (p.g.render) p.g.render.classList.remove("bare");
        if (!$(".lay-tools", sec())) $(".occ", sec()).open = false;
      },
    };
  }
  H["s-arc"] = layoutHook("opt1");
  H["s-net"] = layoutHook("opt2");
  H["s-opt3"] = layoutHook("opt3");

  /* ---- occupancy: each option against the brief, as Mitigata's occupancy chart (Sathwick, 13.10) ---- */
  const sumOf = (a, f) => a.reduce((s, x) => s + (f(x) || 0), 0);
  function paxIn(o, re, d) { const t = D[o].texts.find((x) => re.test(x.t)), m = t && t.t.match(/(\d+)\s*PAX/i); return m ? +m[1] : d; }
  // [zone, area, requirement, Option 01, Option 02, low, high, sub]: low/high the requirement as numbers (none: the brief
  // doesn't count it); sub rows sit under the row above them (the teams under the workstations, the meeting rooms' sizes,
  // which the chart lists before their total)
  const OCC = [
    ["Public zone", "Reception", "1", 1, 1, 1, 1],
    ["Public zone", "Waiting lounge", "—", 1, 1],
    ["Work zone", "Workstations <small>1050 × 600</small>", "210", 219, 221, 210, 210],
    ["Work zone", "HR & Finance", "20", 20, 22, 20, 20, 1],
    ["Work zone", "Delivery", "70", 71, 70, 70, 70, 1],
    ["Work zone", "Product", "50", 50, 57, 50, 50, 1],
    ["Work zone", "Sales", "40", 41, 41, 40, 40, 1],
    ["Work zone", "Sales Calling", "30", 37, 31, 30, 30, 1],
    ["Work zone", "SOC", "80", 80, 84, 80, 80],
    ["Work zone", "Meeting rooms", "16–17", 17, 15, 16, 17],   // the brief 16–17 (Sathwick, 13.10; the chart says 17–18)
    ["Work zone", "2 pax", "—", "—", 3, null, null, 1],
    ["Work zone", "4 pax", "—", 11, 5, null, null, 1],
    ["Work zone", "5 pax", "—", "—", 1, null, null, 1],
    ["Work zone", "6 pax", "—", 5, 3, null, null, 1],
    ["Work zone", "8 pax", "—", "—", 1, null, null, 1],
    ["Work zone", "10 pax", "—", 1, 1, null, null, 1],
    ["Work zone", "14 pax", "—", "—", 1, null, null, 1],
    ["Work zone", "Boardroom", "1 · 30 pax", "1 · 30 pax", "1 · 30 pax", 1, 1],
    ["Work zone", "Founder's think tank", "1", "—", "—", 1, 1, 0, 1],   // Option 03's chart only (8: shown where an option has it)
    ["Work zone", "Phone booths", "6–7", 9, 6, 6, 7],
    ["Collaboration area", "Podcast room", "1", 1, 1, 1, 1],
    ["Collaboration area", "Collab", "Yes", "Yes", "Yes"],
    ["Collaboration area", "Cafeteria", "1", 1, 1, 1, 1],
    ["Collaboration area", "Repro", "—", 2, 2],
    ["Service zone", "Nap room", "—", 1, "—"],
    ["Service zone", "Store room", "1", 1, 1, 1, 1],
    ["Service zone", "Server room", "1", 1, 1, 1, 1],
    ["Service zone", "UPS & battery room", "1", 1, 1, 1, 1],
  ];
  const occOf = (o) => (o === "opt2" ? 4 : 3), WS = "Workstations <small>1050 × 600</small>";
  // Option 03 (14.10), from Mitigata's chart "Revised Option 03" (Sathwick, 15.10); a space it doesn't list is "—"
  const OCC3 = { "Reception": 1, "Waiting lounge": 1, [WS]: 219, "HR & Finance": 21, "Delivery": 74, "Product": 53, "Sales": 41,
    "Sales Calling": 30, "SOC": 80, "Meeting rooms": 16, "4 pax": 9, "6 pax": 7, "Boardroom": "1 · 30 pax", "Founder's think tank": 1,
    "Phone booths": 6, "Podcast room": 1, "Collab": "Yes", "Cafeteria": 1, "Repro": 2, "Server room": 1, "UPS & battery room": 1 };
  const occV = (o, r) => (o === "opt3" ? (r[1] in OCC3 ? OCC3[r[1]] : "—") : r[occOf(o)]);
  const occRow = (name) => OCC.find((r) => r[1] === name);
  const occN = (o, name) => { const v = occV(o, occRow(name)); return typeof v === "number" ? v : parseInt(v, 10) || 0; };
  // the occupancy's headline numbers: the seats (workstations and the SOC) and the meeting rooms
  const occSum = (o) => ({ seats: occN(o, WS) + occN(o, "SOC"), rooms: occN(o, "Meeting rooms") });
  // a team's seats as the chart has them (and its brief), wherever a slide shows seats: the drawings' own counts can differ
  // (Option 02's SOC is drawn with 78; the chart has 84) (Sathwick, 13.10)
  const teamSeats = (o, t) => { const r = OCC.find((x) => x[1] === t.name); return r ? Object.assign({}, t, { seats: occV(o, r), pax: r[5] }) : t; };
  const mark = (n, lo, hi) => (typeof n !== "number" || lo == null ? ["", ""] : n < lo ? ["dn", "▼"] : n > hi ? ["up", "▲"] : ["ok", "✓"]);
  function occTable(opts) {
    const groups = [];
    // a room size no shown option has is left out
    OCC.filter((r) => !(r[7] || r[8]) || opts.some((o) => occV(o, r) !== "—")).forEach((r) => { const g = groups[groups.length - 1]; if (g && g[0] === r[0]) g[1].push(r); else groups.push([r[0], [r]]); });
    const rows = groups.map(([g, list]) => list.map((r, i) => { const [, name, brief, , , lo, hi, sub] = r;
      return `<tr class="${i === 0 ? "g0" : ""}${sub ? " sub" : ""}">` +
        (i === 0 ? `<td class="grp" rowspan="${list.length}">${g}</td>` : "") + `<td class="sp">${name}</td><td class="br">${brief}</td>` +
        opts.map((o) => { const v = occV(o, r), [c, m] = mark(v, lo, hi); return `<td class="${c}"><i>${m}</i>${v}</td>`; }).join("") + "</tr>"; }).join("")).join("");
    return `<table class="occ-t"><tr><th>Zone</th><th>Area</th><th>Brief</th>${opts.map((o) => `<th>${OPTLBL[o]}</th>`).join("")}</tr>${rows}</table>` +
      `<p class="occ-key"><i class="ok">✓</i> meets the brief <i class="up">▲</i> above <i class="dn">▼</i> below · from Mitigata's occupancy chart</p>`;
  }
  // the chart, read: a few lines, from the same numbers
  function occWhy() {
    const n = occN, ws = WS, L = [
      `<b>SOC</b> ${n("opt1", "SOC")} in Option 01 and ${n("opt2", "SOC")} in Option 02, against 80.`,
      `<b>Workstations</b> ${n("opt1", ws)} and ${n("opt2", ws)}, against 210: every team seated, ${n("opt1", "Sales Calling") > 30 ? `Option 01 with ${n("opt1", "Sales Calling") - 30} more for Sales Calling` : ""}${n("opt2", "Product") > 50 ? `, Option 02 with ${n("opt2", "Product") - 50} more for Product` : ""}.`,
      `<b>Meeting rooms</b> ${n("opt1", "Meeting rooms")} in Option 01 (4 to 10 pax) and ${n("opt2", "Meeting rooms")} in Option 02 (2 to 14 pax, the wider mix), against 16–17.`,
      `<b>Phone booths</b> ${n("opt1", "Phone booths")} and ${n("opt2", "Phone booths")}, against 6–7.`,
      `<b>Beyond the brief</b> A waiting lounge and two repro rooms in both; a nap room in Option 01.`,
    ];
    return L.map((l) => `<li>${l}</li>`).join("");
  }

  /* ---- 09 the two options against the brief, side by side ---- */
  H["s-stories"] = {
    enter() {
      $("#occ-cmp").innerHTML = `<div class="panel-h"><span>Occupancy against the brief</span></div>${occTable(["opt1", "opt2"])}`;
      $("#occ-why").innerHTML = occWhy();
      world("plan"); shade("left");
      const lay = { render: true, furn: false, parts: true, walls: true, slab: true, north: true, entry: true, ctl: false, hover: false };
      const a = layerPlan("opt1", lay), b = getPlanB();
      b.setOption("opt2"); b.setOverlay([]);
      b.setLayers(Object.assign({ zones: false, labels: false, evo: false, tiers: false, routes: [], circ: false, events: null, sat: false, cams: false, sig: false }, lay));
      frames("split", OPTLBL.opt1); $("#tag-b").textContent = OPTLBL.opt2;
      a.fit(LAY_BOX, 0); b.fit(LAY_BOX, 0);
    },
    leave() { frames("right"); $("#tag-b").textContent = OPTNAME.opt2; getPlanA().setLayers({ render: false, entry: false }); },
  };

  /* ---- 10 one model, two options: both axos, one volume per beat (assets/js/axo.js) ---- */
  let axo = null;
  // straight-line metres from the front door to a space (the largest of its type)
  const doorTo = (o, t) => { const e = Z.annot.labels.find((l) => l.kind === "entry").at, c = centroidOf(o, t); return Math.round(Math.hypot(c[0] - e[0], c[1] - e[1]) / 1000); };
  // the three options, two on view: Option 01 above and Option 03 below to begin with, each view's tag a dropdown (Sathwick, 15.10);
  // a change re-runs the beat on the drawing that comes in
  const getAxo = () => axo || ((axo = new window.Axo($("#axo-host"), { opts: ["opt1", "opt2", "opt3"], slots: ["opt1", "opt3"] })),
    axo.setEvents(TWIN_EV), axo.setPodium(TWIN_POD), axo.setStudioWalk(TWIN_STUDIO),
    (axo.onSlot = () => { if (scenes[state.idx] && scenes[state.idx].id === "s-twin") H["s-twin"].step(state.step); }), axo);
  // each option's line on the beats (Options 01 and 02 as Ritika wrote them; Option 03 from the 14.10 drawing)
  const AXO_CAP = {
    zones: { opt1: "SOC on the atrium edge · boardroom at the far end", opt2: "SOC at the prow · boardroom by arrival", opt3: "SOC at the prow · boardroom beside it" },
    soc: { opt1: "seen from the atrium court", opt2: "seen from the road side", opt3: "at the prow, behind curved glass" },
    board: { opt1: "at the far end", opt2: "close to arrival", opt3: "at the prow, beside the SOC" },
    walk: { opt1: "a tour past the SOC", opt2: "never crosses the floor", opt3: "the length of the floor to the prow" },
  };
  const axoZones = () => DZ_ORDER.map((k) => `<li>${dzSw(k)}<b>${dzName(k)}</b><span></span></li>`).join("");   // one per line, as the layout slides' key (Ritika)
  const mixSizes = (o) => Object.keys(MIX[o].mix).map(Number).sort((a, b) => a - b);
  const AXO = [
    { set: { soc: 0, guest: 0, route: 0, meet: 0, mono: 0 }, legend: () => axoZones() + `<li><i class="sw sw-tri"></i><b>Main entrance</b><span></span></li>`,
      labels: () => [[], []], caps: (os) => os.map((o) => `<b>${OPTLBL[o]}</b> ${AXO_CAP.zones[o]}`) },
    { set: { soc: 1, guest: 0, route: 0, meet: 0, mono: 1 }, legend: () => `<li><i class="sw sw-vol" style="--c:#04db7f"></i><b>The SOC</b><span>standing up</span></li>`,
      labels: (os) => os.map((o) => { const s = teamSeats(o, zonesOf(o, "soc")[0]); return [{ at: "soc", text: `SOC · ${s.seats}${s.seats < s.pax ? ` of ${s.pax}` : ""} seats` }]; }),
      caps: (os) => os.map((o) => `<b>${OPTLBL[o]}</b> ${AXO_CAP.soc[o]}`) },
    { set: { soc: 0, guest: 1, route: 0, meet: 0, mono: 1 }, legend: () => `<li><i class="sw sw-vol" style="--c:#fbbc04"></i><b>Arrival, boardroom and studio</b><span></span></li>`,
      labels: (os) => os.map((o) => [{ at: "guest", text: `Boardroom · ${paxIn(o, /BOARD.*PAX/i, 30)} pax` }, { at: "studio", text: "Podcast studio", dx: 70 }, { at: "arrive", text: "Arrival · reception", dx: 70 }]),
      caps: (os) => os.map((o) => `<b>${OPTLBL[o]}</b> boardroom ≈${doorTo(o, "board")} m from the front door, ${AXO_CAP.board[o]}`) },
    // the walk past everything the earlier beats stood up (Ritika); no length on it
    { set: { soc: 1, guest: 1, route: 1, meet: 0, mono: 1 }, legend: () => `<li><i class="sw-route solid"></i><b>The visitor's walk</b><span>to the boardroom · studio</span></li><li><i class="sw sw-tri"></i><b>Main entrance</b><span></span></li>` +
        `<li><i class="sw sw-vol" style="--c:#04db7f"></i><b>SOC</b><span></span></li><li><i class="sw sw-vol" style="--c:#fbbc04"></i><b>Arrival, boardroom and studio</b><span></span></li>`,
      labels: () => [[], []],
      caps: (os) => os.map((o) => `<b>${OPTLBL[o]}</b> ${AXO_CAP.walk[o]}`) },
  ];
  // then a day at Mitigata on the same drawings, one option at a time (Ritika): the brief's 50 / 100 / 200 events among the hours
  const DAY = [
    { t: "09:30", n: "Workday", scen: "workday", ev: null, h: "A normal workday.", p: "The SOC around the clock; everyone else across the workhalls, the rooms and the café." },
    { t: "11:00", n: "Workshop", scen: "e50", ev: "50", h: "A workshop for 50." },                       // no lunch; workshop, then showcase (Ritika)
    { t: "16:00", n: "Product showcase", scen: "e100", ev: "100", h: "A product showcase for 100." },
    { t: "18:30", n: "Town hall", scen: "e200", ev: "200", h: "A town hall for 200." },
  ];
  // where each event stands on the axo: Ritika's own marks (OPTION 1.svg / OPTION 2.svg, 12.10: 50 red, 100 green, 200 blue),
  // traced off her plan screenshots into drawing mm; the axo's day only (A5 and the scorecard keep the drawings' areas).
  // In Option 02 the larger café-end area is the 100's and the smaller one the 50's (Ritika, 12.10)
  const TWIN_EV = {"opt1":{"200":[[26760,7660],[35430,7660],[35480,15700],[70210,15700],[70210,26720],[62350,24640],[60720,28530],[37280,28530],[36650,23330],[33260,19630],[27480,15650],[26760,15610]],"50":[[62580,15610],[62580,7300],[60500,7250],[60500,2560],[60050,2200],[63570,2200],[63610,3280],[65060,3280],[65100,8470],[71430,8470],[71470,5940],[72900,5940],[72900,10100],[70120,10140],[70120,15610]],"100":[[27120,15930],[53540,15840],[53540,28660],[37240,28660],[36650,23690],[33670,19990]]},"opt2":{"50":[[59730,13920],[61090,12370],[61090,6970],[65500,6970],[65550,8380],[71820,8380],[71860,5690],[72900,5690],[72900,14150],[61680,14010],[60730,14960]],"100":[[64140,21010],[64140,18370],[59590,14010],[59590,13690],[61140,12330],[61140,7060],[65320,7060],[65360,8420],[71820,8420],[71860,5970],[72900,5970],[72900,21010]],"200":[[19510,29010],[19510,28640],[20290,28190],[34600,13870],[58140,13870],[46370,25640],[33960,25640],[33920,32000],[22830,32000]]},
    // Option 03: the CAD team's own outlines (layers 50 / 100 / 200 of "Testfit -14.10.26 (2).dxf", drawn on the copy of the floor
    // 44 924 mm below the layout), in drawing mm
    "opt3":{"50":[[69561,15631],[61833,15631],[61833,8631],[69561,8631]],"100":[[25884,16610],[26554,19536],[26554,22477],[41595,22477],[41595,8631],[35897,8631],[34692,10607],[33867,11707],[32949,12717],[31944,13633],[30860,14448],[29705,15159],[28485,15759],[27209,16245]],"200":[[25884,16610],[26554,19536],[26554,28523],[47667,28523],[47667,15780],[41595,15780],[41595,8631],[35897,8631],[34692,10607],[33867,11707],[32949,12717],[31944,13633],[30860,14448],[29705,15159],[28485,15759],[27209,16245]]}};
  // the town hall's podium, 450 mm high, along the SOC: Ritika's outlines (PODIUM OP1.svg / PODIUM OP2.svg, 13.10), traced the same way
  const TWIN_POD = {"opt1":[[35020,25730],[33080,22880],[31230,21120],[29420,19950],[27480,19130],[27930,17870],[28250,17870],[31730,19990],[33990,22070],[35020,23330]],"opt2":[[23510,22690],[22740,21640],[30650,13690],[30920,13690],[31690,14650],[31690,15060],[24240,22690]]};
  // the visitor's walk on from reception to the podcast studio (Ritika, 14.10), drawing mm along the floor's corridor centrelines
  // (D.zones[o].circulation), ending in the studio
  const TWIN_STUDIO = {
    opt1: [[65176, 28965], [66218, 25050], [67218, 25450], [68618, 25650], [69018, 25050], [69018, 20450], [68818, 20250], [68818, 16450], [70200, 14400]],
    opt2: [[65313, 29073], [59418, 29650], [55818, 29650], [55818, 27650], [62218, 21250], [62218, 18450], [59418, 15650], [58218, 15050], [57618, 13650], [56618, 13050],
      [49818, 13050], [38018, 13250], [37018, 12650], [34818, 12650], [33400, 12500], [32300, 10900]],
  };
  const twinEv = (o, lvl) => { const p = TWIN_EV[o] && TWIN_EV[o][lvl], e = Z[o].events[lvl] || {}; return p ? { poly: p, area: polyA(p) / 1e6, how: e.how } : e; };
  const dayLegend = (d) => `<li><i class="sw sw-person"></i><b>A person</b><span></span></li>` + (d && d.ev ? `<li><i class="sw sw-person ev"></i><b>At the event</b><span></span></li>` : "") +
    (d && d.ev === "200" ? `<li><i class="sw sw-person" style="background:#cc0000"></i><b>Speaker at the podium</b><span>by the SOC</span></li>` : "");
  // the hour in the column: its time and headline (the counts go in each option's caption)
  function dayHead(i) { const s = DAY[i]; $("#day-head").innerHTML = `<span class="t">${s.t}</span><b>${s.h}</b>`; }
  function dayAxo(i) {
    const ax = getAxo(), d = DAY[i];
    $("#s-twin").classList.add("day");
    $$("#timeline .tl-stop").forEach((b, j) => b.classList.toggle("on", j === i));
    $("#tl-fill").style.height = (i / (DAY.length - 1)) * 100 + "%";   // the timeline runs down the column
    ax.set({ soc: 0, guest: 0, route: 0, meet: 0, mono: 0 }); ax.setOne(null); ax.setColours(false); ax.setFurniture(false);   // a clean white floor: people and the event read (Ritika)
    ax.setHome({ fw: 0, zoom: 1 }, true);                   // both options at once, the whole floor, as the beats before (Ritika)
    const labs = [], caps = [];
    ax.shownOpts().forEach((o, j) => {
      ax.showEvent(j, d.ev);
      const n = ax.setDay(j, d.scen, occSum(o).seats), ev = d.ev && twinEv(o, d.ev);   // the option's people (299 / 305)
      labs.push(ev ? [{ at: P2c(ev).concat(2.4), text: `${d.n} · ${d.ev}` }] : []);
      caps.push(`<b>${OPTLBL[o]}</b> ${n} people` + (ev ? ` · ${sqft(ev.area)} · ${Math.floor(ev.area / 0.75)} theatre seats` : " on the floor"));
    });
    ax.setTexts(labs, caps);
    $("#axo-lgd").innerHTML = dayLegend(d); ax.setLegend(dayLegend(d));
    dayHead(i);
  }
  // an event's label sits over the middle of its largest part
  const polyA = (p) => Math.abs(p.reduce((a, q, i) => { const r = p[(i + 1) % p.length]; return a + q[0] * r[1] - r[0] * q[1]; }, 0)) / 2;
  const P2c = (ev) => window.Plan2D.centroid((ev.polys || [ev.poly]).slice().sort((a, b) => polyA(b) - polyA(a))[0]);
  /* the occupancy on One model, two options: the layout slides' chart, filled from Ritika's occupancy chart
     (Mitigata_Occupancy Chart - Sheet1, 12.10): her brief and both options' counts, as given; Option 03 from its own
     chart (Revised Option 03, Sathwick 15.10) */
  const TWIN_OCC = [
    ["Public", "Reception and waiting", "1", 1, 1, [1, "1"], [1, "1"], [1, "1"]],
    ["Work", "Workstations", "210", 210, 210, [219, "219"], [221, "221"], [219, "219"]],
    ["Work", "HR &amp; Finance", "20", 20, 20, [20, "20"], [22, "22"], [21, "21"]],
    ["Work", "Delivery", "70", 70, 70, [71, "71"], [70, "70"], [74, "74"]],
    ["Work", "Product", "50", 50, 50, [50, "50"], [57, "57"], [53, "53"]],
    ["Work", "Sales", "40", 40, 40, [41, "41"], [41, "41"], [41, "41"]],
    ["Work", "Sales calling", "30", 30, 30, [37, "37"], [31, "31"], [30, "30"]],
    ["Work", "SOC seats", "80", 80, 80, [80, "80"], [84, "84"], [80, "80"]],
    ["Work", "Meeting rooms", "16–17", 16, 17, [17, "17 <small>4–10 pax</small>"], [15, "15 <small>2–14 pax</small>"], [16, "16 <small>4–6 pax</small>"]],
    ["Work", "Boardroom", "1 · 30 pax", 1, 1, [1, "1 <small>30 pax</small>"], [1, "1 <small>30 pax</small>"], [1, "1 <small>30 pax</small>"]],
    ["Work", "Founder's think tank", "1", 1, 1, [null, "—"], [null, "—"], [1, "1"]],   // Option 03's chart only
    ["Work", "Phone booths", "6–7", 6, 7, [9, "9"], [6, "6"], [6, "6"]],
    ["Collaboration", "Podcast studio", "1", 1, 1, [1, "1"], [1, "1"], [1, "1"]],
    ["Collaboration", "Breakouts and lounges", "Yes", 1, 99, [1, "Yes"], [1, "Yes"], [1, "Yes"]],
    ["Collaboration", "Café", "1", 1, 1, [1, "1"], [1, "1"], [1, "1"]],
    ["Collaboration", "Repro", "—", null, null, [2, "2"], [2, "2"], [2, "2"]],
    ["Service", "Server and UPS", "1", 1, 1, [1, "1"], [1, "1"], [1, "1"]],
    ["Service", "Store room", "1", 1, 1, [1, "1"], [1, "1"], [null, "—"]],
    ["Service", "Nap room", "—", null, null, [1, "1"], [0, "—"], [0, "—"]],
    ["Total", "Seats, desks and SOC", "290", 290, 290, [299, "299"], [305, "305"], [299, "299"]],
  ];
  function twinOccTable() {
    const groups = [];
    TWIN_OCC.forEach((r) => { const g = groups[groups.length - 1]; if (g && g[0] === r[0]) g[1].push(r); else groups.push([r[0], [r]]); });
    const rows = groups.map(([g, list]) => list.map(([, name, brief, lo, hi, a, b, c], i) => `<tr${i === 0 ? ' class="g0"' : ""}>` +
      (i === 0 ? `<td class="grp" rowspan="${list.length}">${g}</td>` : "") + `<td class="sp">${name}</td><td class="br">${brief}</td>` +
      [a, b, c].map(([n, h]) => { const [k, m] = mark(n, lo, hi); return `<td class="${k}"><i>${m}</i>${h}</td>`; }).join("") + "</tr>").join("")).join("");
    return `<table class="occ-t"><tr><th>Zone</th><th>Space</th><th>Brief</th><th>${OPTLBL.opt1}</th><th>${OPTLBL.opt2}</th><th>${OPTLBL.opt3}</th></tr>${rows}</table>` +
      `<p class="occ-key"><i class="ok">✓</i> meets the brief <i class="up">▲</i> above <i class="dn">▼</i> below <i class="x">+</i> beyond it · from the occupancy charts (12.10; Option 03, 15.10)</p>`;
  }
  function twinOcc(on) {
    const oc = $("#s-twin .twin-occ"); if (!oc) return;
    oc.classList.toggle("open", on); $(".lay-btns button", oc).classList.toggle("on", on);
  }
  H["s-twin"] = {
    enter() {
      frames("right"); world("none"); shade("");
      const bar = $("#axo-bar");   // the one toolbar: zoom and reset move both options together
      if (!bar.dataset.on) { bar.dataset.on = 1; bar.addEventListener("click", (e) => {
        const b = e.target.closest("button"), ax = getAxo(); if (!b) return; b.blur();
        if (b.dataset.z === "reset") ax.home(); else ax.set({ zoom: Math.min(4, Math.max(0.8, ax.t.zoom * (b.dataset.z === "in" ? 1.4 : 1 / 1.4))) });
      }); }
      const tl = $("#timeline");
      if (!tl.querySelector(".tl-stop")) DAY.forEach((s, i) => {
        const b = document.createElement("button"); b.className = "tl-stop"; b.style.top = (i / (DAY.length - 1)) * 100 + "%";
        b.innerHTML = `<div class="t">${s.t}</div><i></i><div class="n">${s.n}${s.ev ? ` · ${s.ev}` : ""}</div>`; b.onclick = () => setStep(AXO.length + i + 1); tl.appendChild(b);
      });
      const ax = getAxo(); ax.setSolo(null); ax.intro(); ax.start(); ax.home();
      const oc = $("#s-twin .twin-occ"), ob = $(".lay-btns button", oc);   // Occupancy opens Ritika's chart in the middle of the page
      if (!oc.dataset.on) {
        oc.dataset.on = 1; $(".occ-body", oc).innerHTML = twinOccTable();
        ob.onclick = () => { ob.blur(); twinOcc(!oc.classList.contains("open")); };   // the arrow keys stay with the deck
        $(".occ-x", oc).onclick = () => twinOcc(false); $(".occ-scrim", oc).onclick = () => twinOcc(false);
        document.addEventListener("keydown", (e) => { if (e.key === "Escape" && oc.classList.contains("open")) { e.stopPropagation(); twinOcc(false); } }, true);
      }
    },
    step(k) {
      const ax = getAxo();
      if (k > AXO.length) return dayAxo(k - AXO.length - 1);
      // the four planning beats: both drawings, nobody on the floor yet
      $("#s-twin").classList.remove("day"); ax.setOne(null); ax.setColours(true); ax.setFurniture(true);
      ax.setHome({}, ax.t.fw > 0.01);   // back from the day: the whole floor again (a turn made on beats 1–4 still carries over)
      ax.views.forEach((v, j) => { if (v.headcount) ax.setDay(j, null); ax.showEvent(j, null); });
      const b = AXO[k - 1], os = ax.shownOpts(); ax.set(b.set); ax.setTexts(b.labels(os), b.caps(os)); $("#axo-lgd").innerHTML = b.legend(); ax.setLegend(b.legend());
    },
    // the axo keeps its last frame: going on, "Back to the site" dissolves it into the model at the same angle
    leave() { twinOcc(false); if (axo) { if (axo.solo !== null) axo.setSolo(null); axo.stop(); } },
  };

  /* ---- Appendix: the meeting rooms, none identical, by size on both axos (Ritika: moved here from One model, two options) ---- */
  let axoM = null;
  const meetLegend = () => `<li><i class="sw sw-vol" style="--c:#6f8fc9"></i><b>Non-identical meeting rooms</b><span>${MIX.opt1.total} · ${MIX.opt2.total}</span></li>` +
    [...new Set(mixSizes("opt1").concat(mixSizes("opt2")))].sort((a, b) => a - b).map((k) => `<li><i class="sw" style="background-color:#${(window.Axo.MEET_C[k] || 0x6f8fc9).toString(16).padStart(6, "0")}"></i><b>${k} pax</b><span>${MIX.opt1.mix[k] || "–"} · ${MIX.opt2.mix[k] || "–"}</span></li>`).join("");
  H["s-meetaxo"] = {
    enter() {
      frames("right"); world("none"); shade("");
      const ax = axoM || (axoM = new window.Axo($("#axo-host-meet")));
      ax.setSolo(null); ax.intro(); ax.start(); ax.home();
      ax.set({ soc: 0, guest: 0, route: 0, meet: 1, mono: 1 });
      ax.setTexts([[], []], ["opt1", "opt2"].map((o) => { const s = mixSizes(o); return `<b>${OPTLBL[o]}</b> ${MIX[o].total} meeting rooms · ${s.length} sizes, ${s[0]}–${s[s.length - 1]} pax`; }));
      $("#meet-lgd").innerHTML = meetLegend(); ax.setLegend(meetLegend());
    },
    leave() { if (axoM) { if (axoM.solo !== null) axoM.setSolo(null); axoM.stop(); } },
  };

  /* ---- 10 every space, by what it is for ---- */
  const TYPE_ORDER = ["focus", "soc", "meet", "quiet", "collab", "cafe", "arrive", "board", "studio", "secure", "service", "core"];
  function drawTypes() {
    const o = state.opt; layerPlan(o, { furn: true, parts: true, zones: true });
    const by = {}; Z[o].zones.forEach((z) => (by[z.type] = (by[z.type] || 0) + z.area));
    const tot = Object.values(by).reduce((a, b) => a + b, 0);
    $("#types-list").innerHTML = TYPE_ORDER.filter((t) => by[t]).map((t) => legendRow(window.Plan2D.ZCOL[t], t === "focus" ? "Workhall · teams and agile workstations" : D.zones.types[t].label, `${sqft(by[t])} · ${((by[t] / tot) * 100).toFixed(0)}%`, t)).join("");
  }
  H["s-types"] = {
    enter() { layerScene(); drawTypes(); legendHover($("#types-list"), (t) => getPlanA().highlight(t)); getPlanA().fit(null, 800); },
    opt() { drawTypes(); },
    leave() { getPlanA().highlight(null); },
  };

  /* ---- 11 then, the teams move in (after the layout): colours, seats against PAX, hover on ---- */
  const teamOrder = (o) => teamsOf(o).map((t) => teamSeats(o, t)).sort((a, b) => (b.type === "soc") - (a.type === "soc") || b.seats - a.seats);
  function drawTeams(focus) {
    const o = state.opt, teams = teamOrder(o);
    getPlanA().setOverlay(teams.map((t, i) => ({ kind: "poly", pts: t.poly, fill: TEAMC[i % TEAMC.length], stroke: TEAMC[i % TEAMC.length], fo: !focus || focus === String(i) ? 0.8 : 0.1, sw: focus === String(i) ? 2.5 : 1.5 })));
  }
  function teamsPanel() {
    const o = state.opt, teams = teamOrder(o), max = Math.max(...teams.map((t) => Math.max(t.pax || 0, t.seats)));
    $("#teams-list").innerHTML = teams.map((t, i) => `<li data-k="${i}"><i class="sw" style="background:${TEAMC[i % TEAMC.length]}"></i><b>${t.name}</b><span class="tb"><em style="width:${(100 * t.seats) / max}%"></em></span><span>${t.seats}${t.seats < t.pax ? ` of ${t.pax}` : ""} seats${t.hot ? ` · ${t.hot} hot` : ""}</span></li>`).join("") +
      `<li class="tot"><b>Total</b><span></span><span>${teams.reduce((a, t) => a + t.seats, 0)} seats · ${teams.reduce((a, t) => a + t.pax, 0)} in the brief</span></li>`;
  }
  H["s-teams"] = {
    enter() { layerPlan(state.opt, { furn: true, parts: true, hover: true }); layerScene(); drawTeams(); teamsPanel(); legendHover($("#teams-list"), drawTeams); getPlanA().fit(null, 800); },
    opt() { layerPlan(state.opt, { furn: true, parts: true, hover: true }); drawTeams(); teamsPanel(); },
    leave() { getPlanA().setOverlay([]); getPlanA().setLayers({ hover: false }); },
  };

  /* ======================= 12 green zones: biophilic analysis (the Acko method, presented) ======================= */
  // per space type: who uses it and how. Planning estimates (Acko's defaults; SOC, boardroom and studio added for this floor)
  const GZ_DEF = {
    open:      { n: "Open workstations",  occ: "seats",  visits: 2,   util: .70, dwell: 180, act: 1.0, int: 1.0, soc: 35 },
    soc:       { n: "SOC (24 × 7)",       occ: "seats",  visits: 1.5, util: .90, dwell: 240, act: 1.1, int: 1.4, soc: 25 },
    booth:     { n: "Phone booth",        occ: "seats",  visits: 4,   util: .50, dwell: 20,  act: .8,  int: 1.0, soc: 5 },
    meeting:   { n: "Meeting room",       occ: "seats",  visits: 3,   util: .55, dwell: 50,  act: 1.2, int: 1.2, soc: 55 },
    board:     { n: "Boardroom",          occ: "seats",  visits: 1,   util: .40, dwell: 75,  act: 1.2, int: 1.2, soc: 70 },
    studio:    { n: "Podcast studio",     occ: "seats",  visits: 1,   util: .40, dwell: 60,  act: 1.1, int: 1.3, soc: 40 },
    collab:    { n: "Breakout and lounge", occ: "seats", visits: 3,   util: .60, dwell: 40,  act: 1.1, int: 1.0, soc: 90 },
    cafe:      { n: "Café and dining",    occ: "all",    visits: 1.2, util: .70, dwell: 30,  act: 1.3, int: 1.3, soc: 100 },
    reception: { n: "Reception",          occ: "arrive", visits: 1.3, util: .85, dwell: 4,   act: 1.0, int: 1.0, soc: 75 },
    lobby:     { n: "Lift lobby",         occ: "arrive", visits: 2.5, util: .85, dwell: 1.5, act: .9,  int: .9,  soc: 40 },
    corridor:  { n: "Main circulation",   occ: "all",    visits: 12,  util: .70, dwell: .6,  act: .8,  int: .8,  soc: 30 },
    support:   { n: "Server, store, services", occ: "none", visits: 0, util: 0, dwell: 0, act: 0, int: 0, soc: 0 },
  };
  const GZ_G = { density: 12.5, visitors: .05, wF: 25, wD: 25, wC: 20, wL: 15, wS: 10, wV: 5, mVL: .5, mL: .75, mM: 1, mH: 1.2, mVH: 1.4, reach: 8 };
  const GZ_CATS = { work: ["Work", "#e4aba5"], collab: ["Collaboration", "#e9c8ff"], social: ["Social", "#f2c596"], arrival: ["Arrival", "#fce7ae"], move: ["Movement", "#c9d3e0"], support: ["Support", "#c8c8c8"] };
  const GZ_CLASSES = [[25, "Very low", "mVL"], [40, "Low", "mL"], [60, "Moderate", "mM"], [80, "High", "mH"], [101, "Very high", "mVH"]];
  const GZ_CLASS_C = { "Very low": "#e8efe9", Low: "#c6e3cf", Moderate: "#8fd0a6", High: "#3fb878", "Very high": "#0a8f57" };
  const GZ_TYPES = {
    feature: { n: "Green feature", d: "High visibility, high design importance", cap: [3, 7], foot: .9 },
    node: { n: "Green node", d: "High footfall and visibility", cap: [3, 8], foot: .55 },
    island: { n: "Green island", d: "Long stays in a social or team space", cap: [4, 12], foot: .4 },
    edge: { n: "Green edge", d: "Along a desk or team boundary", cap: [4, 12], foot: .3 },
    threshold: { n: "Green threshold", d: "Between two kinds of space", cap: [3, 8], foot: .35 },
    pocket: { n: "Green pocket", d: "Residual or under-used floor", cap: [2, 5], foot: .2 },
  };
  const GZ_ORDER = ["feature", "node", "island", "edge", "threshold", "pocket"];
  const gzClass = (p) => GZ_CLASSES.find((c) => Math.round(p) <= c[0]) || GZ_CLASSES[4];
  const GZ_ENCLOSED = new Set(["booth", "meeting", "board", "studio", "soc"]);
  function gzKind(name) {
    const n = (name || "").toLowerCase();
    if (/agile|hotdesk|collaboration area/.test(n)) return "open";          // the agile workstations are work
    if (/meeting/.test(n)) return "meeting"; if (/phone booth/.test(n)) return "booth"; if (/board/.test(n)) return "board";
    if (/^cafe|cafeteria/.test(n)) return "cafe"; if (/reception|entrance/.test(n)) return "reception"; if (/lift lobby/.test(n)) return "lobby";
    if (/corridor/.test(n)) return "corridor"; if (/breakout|collab|lounge/.test(n)) return "collab"; if (/podcast/.test(n)) return "studio";
    return "support";
  }
  const gzName = (n) => (/^corridor/i.test(n) ? "Main circulation" : /^board ?room/i.test(n) ? "Boardroom" : /^cafe|cafeteria/i.test(n) ? "Café" : n.replace(/\s*-\s*\d+\s*PAX.*$/i, ""));
  const gzCat = (k) => ({ open: "work", soc: "work", booth: "collab", meeting: "collab", board: "collab", studio: "collab", collab: "collab", cafe: "social", reception: "arrival", lobby: "arrival", corridor: "move" }[k] || "support");
  const GZ = {};
  function gzRun(o) {
    if (GZ[o]) return GZ[o];
    const g = GZ_G, teams = teamsOf(o), head = teams.reduce((a, t) => a + (t.seats || 0), 0);
    const rows = [];
    teams.forEach((t) => rows.push({ id: "t" + rows.length, name: t.name, k: t.type === "soc" ? "soc" : "open", poly: t.poly, polys: [t.poly], m2: t.area, seats: t.seats, src: "dwg" }));
    Z[o].hover.rooms.forEach((r) => {
      const k = gzKind(r.name), polys = ptsOf(r.d).filter((p) => p.length > 2 && areaP(p) > 0.2).sort((a, b) => areaP(b) - areaP(a)); if (!polys.length) return;
      const pax = +((r.name.match(/(\d+)\s*PAX/i) || [])[1] || 0);
      const seats = k === "booth" ? 1 : k === "board" ? 30 : k === "meeting" ? pax : k === "studio" ? 3 : k === "open" || k === "collab" ? Math.max(2, Math.round(r.m2 / 2.5)) : 0;
      const same = k === "corridor" && rows.find((q) => q.k === "corridor");
      if (same) { same.polys.push(...polys); same.m2 += r.m2; return; }
      rows.push({ id: r.id, name: gzName(r.name), k, poly: polys[0], polys, m2: r.m2, seats, src: ["collab", "studio", "open"].includes(k) ? "est." : seats ? "dwg" : "est." });
    });
    const corr = rows.filter((r) => r.k === "corridor").flatMap((r) => r.polys);
    // the walking line stays clear: no planting within 1.2 m of the circulation centreline
    const circ = (Z[o].circulation || []).flatMap((l) => l.slice(1).map((q, i) => [l[i], q]));
    const circDist = (x, y) => (circ.length ? Math.min(...circ.map(([a, b]) => segDist(x, y, a, b))) : 1e9);
    const minDist = (x, y, polys) => Math.min(...polys.map((q) => polyDist(x, y, q)));
    const nodes = rows.filter((r) => ["reception", "lobby", "cafe"].includes(r.k)).map((r) => ({ at: centroidP(r.poly), k: r.k }));
    const arrM2 = rows.filter((r) => r.k === "reception" || r.k === "lobby").reduce((a, r) => a + r.m2, 0) || 1;
    rows.forEach((r) => {
      const d = GZ_DEF[r.k]; r.d = d; r.c = gzCat(r.k); r.sup = d.occ === "none"; r.at = centroidP(r.poly);
      r.occ = d.occ === "seats" ? r.seats : d.occ === "all" ? head : d.occ === "arrive" ? Math.round(head * (1 + g.visitors) * (r.m2 / arrM2)) : 0;
      if (d.occ !== "seats" && !r.sup) r.src = "est.";
      r.foot = r.occ * d.visits * d.util; r.hrs = (r.foot * d.dwell) / 60; r.ciiRaw = r.foot * (d.dwell / 60) * d.act * d.int;
      const pts = r.polys.flatMap((q) => samples(q, 700)); r.day = pts.length ? pts.filter(([x, y]) => glassDist(x, y) <= DAYLIGHT).length / pts.length : 0;
      const dc = r.k === "corridor" ? 0 : corr.length ? minDist(r.at[0], r.at[1], corr) : 6000;
      r.vis = (GZ_ENCLOSED.has(r.k) ? 0.35 : 1) * (0.5 + 0.5 / (1 + dc / 6000)) + (r.c === "arrival" ? 0.2 : 0);
    });
    // priority: six normalised factors, half intensity (per m², min 25 m²) and half volume, square-root compressed (Acko)
    const live = rows.filter((r) => !r.sup && r.m2 > 0), A = (r) => Math.max(25, r.m2), mx = (f) => Math.max(...live.map(f)) || 1;
    const blend = (vol) => { const iv = (r) => vol(r) / A(r), mi = mx(iv), mv = mx(vol); return (r) => 50 * Math.sqrt(iv(r) / mi) + 50 * Math.sqrt(vol(r) / mv); };
    const bF = blend((r) => r.foot), bD = blend((r) => r.hrs), bC = blend((r) => r.ciiRaw), rv = mx((r) => r.vis), W = g.wF + g.wD + g.wC + g.wL + g.wS + g.wV;
    rows.forEach((r) => {
      if (r.sup) { Object.assign(r, { nF: 0, nD: 0, cii: 0, nL: 0, nS: 0, nV: 0, raw: 0 }); return; }
      r.nF = bF(r); r.nD = bD(r); r.cii = bC(r); r.nL = Math.min(100, r.day * 100); r.nS = r.d.soc; r.nV = 100 * Math.sqrt(r.vis / rv);
      r.raw = (g.wF * r.nF + g.wD * r.nD + g.wC * r.cii + g.wL * r.nL + g.wS * r.nS + g.wV * r.nV) / W;
    });
    const top = Math.max(...rows.map((r) => r.raw)) || 1;
    rows.forEach((r) => { r.prio = r.sup ? 0 : (100 * r.raw) / top; r.cls = r.sup ? null : gzClass(r.prio); r.target = r.sup ? 0 : Math.round((r.m2 / g.density) * g[r.cls[2]]); });
    // candidate spots: free floor only — off the glass line, clear of walls and doors, desks, the corridors, the core and the enclosed rooms
    const desks = deskPolys(o, false), deskS = deskSamples(o);
    const closed = rows.filter((r) => r.sup || GZ_ENCLOSED.has(r.k)).flatMap((r) => r.polys).concat(Z[o].zones.filter((z) => z.type === "core").map((z) => z.poly));
    const hostOf = (x, y) => rows.find((r) => !r.sup && !GZ_ENCLOSED.has(r.k) && r.polys.some((q) => inPoly(x, y, q)));
    const cands = [];
    const [x0, y0, x1, y1] = bboxP(Z.annot.outline);
    for (let x = x0 + 900; x < x1; x += 1500) for (let y = y0 + 900; y < y1; y += 1500) {
      if (!inPoly(x, y, Z.annot.outline) || edgeDist(x, y, Z.annot.outline) < 900) continue;
      if (closed.some((p) => polyDist(x, y, p) < 700) || desks.some((p) => inPoly(x, y, p)) || circDist(x, y) < 1200) continue;
      const host = hostOf(x, y), hp = host && host.polys.find((q) => inPoly(x, y, q)); if (!host || edgeDist(x, y, hp) < 600) continue;
      let fd = 1e9, nx = x, ny = y; deskS.forEach(([a, b]) => { const dd = Math.hypot(a - x, b - y); if (dd < fd) { fd = dd; nx = a; ny = b; } });
      if (fd < 900) continue;                                         // keep the chair zone free
      const nd = nodes.length ? Math.min(...nodes.map((n) => Math.hypot(n.at[0] - x, n.at[1] - y))) / 1000 : 99;
      const near = rows.filter((r) => r !== host && !r.sup && minDist(x, y, r.polys) < 2200).map((r) => r.c);
      const trans = near.some((c) => c !== host.c);
      cands.push({ x, y, host, fd: fd / 1000, node: nd, trans, ang: Math.atan2(ny - y, nx - x) + Math.PI / 2, day: glassDist(x, y) <= DAYLIGHT, vis: host.vis * (1 + Math.max(0, 1 - nd / 10)) });
    }
    const rvC = Math.max(...cands.map((c) => c.vis)) || 1;
    cands.forEach((c) => {
      const h = c.host, hc = h.c; c.vnorm = (100 * c.vis) / rvC;
      c.t = c.vnorm >= 70 && h.prio >= 55 && ["arrival", "social", "collab"].includes(hc) ? "feature"
        : c.node <= 5 && h.nF >= 55 && ["arrival", "social", "collab", "move"].includes(hc) ? "node"
        : hc === "move" && h.nF >= 55 ? "node"
        : c.trans && c.node <= 8 ? "threshold"
        : hc === "work" && c.fd <= 2.4 ? "edge"
        : ["social", "collab", "work", "arrival"].includes(hc) && h.nD >= 40 ? "island" : "pocket";
      const nodeB = Math.max(0, 100 - c.node * 15), maint = (c.day ? 0 : 1) * 10;
      c.score = 0.45 * h.prio + 0.2 * c.vnorm + 0.15 * Math.min(100, (1 - Math.min(1, c.fd / 12)) * 100) + 0.1 * nodeB + 0.05 * (c.t === "pocket" ? 100 : 0) + (c.t === "feature" ? 6 : 0) - maint;
      if (h.cls[1] === "Very low" && c.t !== "pocket") c.score = -1;
    });
    // best spot first; never crowd (6 m apart in one space, 3 m otherwise); stop when a space has its plants
    const zones = [], far = (c) => zones.every((z) => Math.hypot(z.x - c.x, z.y - c.y) >= (z.host === c.host ? 6000 : 3000));
    let features = 0;
    cands.filter((c) => c.score > 0).sort((a, b) => b.score - a.score).forEach((c) => {
      const h = c.host, have = zones.filter((z) => z.host === h), left = h.target - have.reduce((a, z) => a + z.n, 0);
      if (left <= 0 || have.length >= Math.max(1, Math.round(h.m2 / 90)) || !far(c)) return;
      if (c.t === "feature" && features >= 2) c.t = "node";
      const T = GZ_TYPES[c.t], n = Math.min(T.cap[1], Math.max(T.cap[0], left));
      if (c.t === "feature") features++;
      zones.push({ x: c.x, y: c.y, t: c.t, n, host: h, day: c.day, vnorm: c.vnorm, c });
    });
    // enclosed rooms get table plants instead of floor planting
    const table = rows.filter((r) => GZ_ENCLOSED.has(r.k) && r.k !== "soc" && r.cls && r.cls[1] !== "Very low").reduce((a, r) => a + Math.max(1, Math.min(4, r.target)), 0);
    const placed = zones.reduce((a, z) => a + z.n, 0);
    // biophilic workplace score: impact, not plant count (40 / 30 / 15 / 15)
    const hiRows = rows.filter((r) => r.cls && r.prio > 60 && !GZ_ENCLOSED.has(r.k) && r.k !== "corridor");
    const served = hiRows.length ? hiRows.filter((r) => zones.some((z) => z.host === r)).reduce((a, r) => a + r.prio, 0) / hiRows.reduce((a, r) => a + r.prio, 0) : 0;
    const reachN = deskS.filter(([a, b]) => zones.some((z) => Math.hypot(z.x - a, z.y - b) <= g.reach * 1000)).length / (deskS.length || 1);
    const visZ = zones.length ? zones.reduce((a, z) => a + z.vnorm, 0) / zones.length / 100 : 0;
    const dayZ = placed ? zones.filter((z) => z.day).reduce((a, z) => a + z.n, 0) / placed : 0;
    const usable = Z.floor_area - Z[o].zones.filter((z) => z.type === "core").reduce((a, z) => a + z.area, 0);
    const cov = (100 * zones.reduce((a, z) => a + z.n * GZ_TYPES[z.t].foot, 0)) / usable;
    return (GZ[o] = { rows, zones, placed, table, head, usable, cov, sub: { served, reachN, visZ, dayZ }, score: 40 * served + 30 * reachN + 15 * visZ + 15 * dayZ });
  }
  const gzTop = (G, key, n) => G.rows.filter((r) => !r.sup).sort((a, b) => b[key] - a[key]).slice(0, n);
  // zone glyphs drawn in plan millimetres
  function gzGlyph(z, col) {
    const { x, y } = z, star = (r) => Array.from({ length: 10 }, (_, i) => { const a = (i * Math.PI) / 5 - Math.PI / 2, rr = i % 2 ? r * 0.45 : r; return [x + rr * Math.cos(a), y - rr * Math.sin(a)]; });
    const fo = 0.9;
    if (z.t === "feature") return [{ kind: "poly", pts: star(1400), fill: col, stroke: "none", fo }];
    if (z.t === "node") return [{ kind: "poly", pts: circleP([x, y], 1050, 20), fill: col, stroke: "none", fo }, { kind: "poly", pts: circleP([x, y], 1500, 20), fill: "none", stroke: col, sw: 1.5, fo: 0 }];
    if (z.t === "island") return [{ kind: "poly", pts: Array.from({ length: 20 }, (_, i) => [x + 1300 * Math.cos((i / 20) * 6.283), y + 750 * Math.sin((i / 20) * 6.283)]), fill: col, stroke: "none", fo }];
    if (z.t === "pocket") return [{ kind: "poly", pts: [[x, y + 800], [x + 800, y], [x, y - 800], [x - 800, y]], fill: col, stroke: "none", fo }];
    // edge / threshold: a short line along the nearest desk or boundary
    const L = z.t === "edge" ? 1800 : 1300, ang = z.c.ang, dx = L * Math.cos(ang), dy = L * Math.sin(ang);
    const out = [{ kind: "line", pts: [[x - dx, y - dy], [x + dx, y + dy]], stroke: col, sw: z.t === "edge" ? 7 : 5 }];
    if (z.t === "threshold") [-0.6, -0.2, 0.2, 0.6].forEach((f) => out.push({ kind: "line", pts: [[x + dx * f - dy * 0.35, y + dy * f + dx * 0.35], [x + dx * f + dy * 0.35, y + dy * f - dx * 0.35]], stroke: col, sw: 2 }));
    return out;
  }
  const gzGreen = () => "#04db7f";
  const GZ_METRIC = {
    foot: ["foot", "Footfall", "How many visits a space gets in a day. Arrival, the café and the main circulation lead.", (r) => `${fmt(r.foot)} visits a day`],
    dwell: ["hrs", "Dwell", "How long people stay: person-hours a day. Desks and the SOC lead: few trips, long stays.", (r) => `${fmt(r.hrs)} person-hours`],
    carbon: ["ciiRaw", "Carbon index", "Footfall × dwell × activity × services: where people and equipment work hardest.", (r) => `index ${fmt(r.ciiRaw)}`],
  };
  const GZS = { metric: "foot" };
  // beat → what the plan shows: 1 the outcome · 2 who uses each space · 3 how busy, how long · 4 priority · 5 the zones
  function gzDraw(k) {
    const o = state.opt, G = gzRun(o), items = [], light = theme() === "light";
    const green = gzGreen(), ramp = "#04db7f";
    const heat = (key) => { const live = G.rows.filter((r) => !r.sup), vals = live.map((r) => r[key] / Math.max(25, r.m2)), m = Math.max(...vals) || 1;
      live.forEach((r, i) => r.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: ramp, stroke: ramp, fo: 0.06 + 0.7 * Math.sqrt(vals[i] / m), sw: 0.6 }))); };
    if (k === 2) G.rows.forEach((r) => r.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: GZ_CATS[r.c][1], stroke: GZ_CATS[r.c][1], fo: 0.45, sw: 0.6 })));
    else if (k === 3) heat(GZ_METRIC[GZS.metric][0]);
    else {
      G.rows.filter((r) => !r.sup).forEach((r) => r.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: GZ_CLASS_C[r.cls[1]], stroke: "none", fo: k === 4 ? 0.75 : 0.3 })));
      if (k !== 4) G.zones.forEach((z) => items.push(...gzGlyph(z, green)));
    }
    getPlanA().setOverlay(items);
    gzPanel(G);
  }
  function gzPanel(G) {
    const cats = {}; G.rows.forEach((r) => { (cats[r.c] = cats[r.c] || [0, 0]); cats[r.c][0]++; cats[r.c][1] += r.m2; });
    $("#gz-cats").innerHTML = Object.keys(GZ_CATS).filter((k) => cats[k]).map((k) => legendRow(GZ_CATS[k][1], GZ_CATS[k][0], `${cats[k][0]} space${cats[k][0] > 1 ? "s" : ""} · ${sqft(cats[k][1])}`)).join("");
    const M = GZ_METRIC[GZS.metric];
    $$("#gz-metric button").forEach((b) => b.classList.toggle("on", b.dataset.m === GZS.metric));
    $("#gz-mdesc").textContent = M[2];
    $("#gz-top").innerHTML = gzTop(G, M[0], 3).map((r) => `<li><b>${r.name}</b><span>${M[3](r)}</span></li>`).join("");
    $("#gz-w").innerHTML = [["Footfall", GZ_G.wF], ["Dwell time", GZ_G.wD], ["Carbon index", GZ_G.wC], ["Daylight", GZ_G.wL], ["Social importance", GZ_G.wS], ["Visibility", GZ_G.wV]]
      .map(([n, w]) => `<li><span>${n}</span><i style="--w:${w * 4}%"></i><b>${w}%</b></li>`).join("");
    $("#gz-cls").innerHTML = GZ_CLASSES.slice().reverse().map((c) => `<li><i class="sw" style="background:${GZ_CLASS_C[c[1]]}"></i><b>${c[1]}</b><span>×${GZ_G[c[2]]} plants</span></li>`).join("");
    $("#gz-prio").innerHTML = gzTop(G, "prio", 4).map((r) => `<li><b>${r.name}</b><span>${Math.round(r.prio)} · ${r.cls[1].toLowerCase()}</span></li>`).join("");
    const nT = {}; G.zones.forEach((z) => (nT[z.t] = (nT[z.t] || 0) + 1));
    $("#gz-types").innerHTML = GZ_ORDER.map((t) => `<li title="${GZ_TYPES[t].d}"><i class="gz-g gz-${t}"></i><b>${GZ_TYPES[t].n}</b><span>${nT[t] || 0}</span></li>`).join("");
    $("#gz-kpi").innerHTML = `<div class="fact"><b>${Math.round(G.score)}<small>/100</small></b><span>biophilic score</span></div><div class="fact"><b>${fmt(G.placed + G.table)}</b><span>plants · ${G.zones.length} zones</span></div><div class="fact"><b>${G.cov.toFixed(1)}%</b><span>green coverage</span></div><div class="fact"><b>${G.table}</b><span>table plants in rooms</span></div>`;
    $("#gz-sub").innerHTML = [["Priority spaces served", G.sub.served, 40], [`Desks with green within ${GZ_G.reach} m`, G.sub.reachN, 30], ["Zones in view", G.sub.visZ, 15], ["Plants in daylight", G.sub.dayZ, 15]]
      .map(([n, v, w]) => `<li><span>${n} <small>${w}%</small></span><i style="--w:${Math.round(v * 100)}%"></i><b>${Math.round(v * 100)}%</b></li>`).join("");
    $("#gz-assume").innerHTML = `<tr><th>Space type</th><th>Visits / day</th><th>In use</th><th>Stay</th><th>Activity</th><th>Services</th><th>Social</th></tr>` +
      Object.values(GZ_DEF).filter((d) => d.occ !== "none").map((d) => `<tr><td>${d.n}</td><td>${d.visits}</td><td>${Math.round(d.util * 100)}%</td><td>${d.dwell} min</td><td>${d.act}</td><td>${d.int}</td><td>${d.soc}</td></tr>`).join("");
    $("#gz-note").textContent = `${OPTNAME[state.opt]}: ${G.zones.length} green zones and ${fmt(G.placed + G.table)} plants on ${sqft(G.usable)} of usable floor, for ${G.head} people.`;
  }
  const GZ_H = ["", "Planting is not decoration.", "Who uses each space?", "How busy, and for how long?", "Where green matters most.", "Where the plants go."];
  H["s-green"] = {
    enter() {
      layerPlan(state.opt, { furn: true, parts: true }); layerScene(); getPlanA().fit(null, 800);
      if (!GZS.wired) {
        GZS.wired = true;
        $$("#gz-metric button").forEach((b) => (b.onclick = () => { b.blur(); GZS.metric = b.dataset.m; gzDraw(state.step); }));
        $("#gz-assume-btn").onclick = (e) => { e.currentTarget.blur(); $("#gz-pop").classList.toggle("on"); };
        $("#gz-pop-x").onclick = (e) => { e.currentTarget.blur(); $("#gz-pop").classList.remove("on"); };
      }
    },
    step(k) { $("#gz-h").textContent = GZ_H[k]; if (k !== 5) $("#gz-pop").classList.remove("on"); gzDraw(k); },
    opt() { layerPlan(state.opt, { furn: true, parts: true }); gzDraw(state.step); },
    theme() { gzDraw(state.step); },
    leave() { getPlanA().setOverlay([]); $("#gz-pop").classList.remove("on"); },
  };

  /* ======================= 13 employee experience: the brief's §10 spaces, scooped out of the layout ======================= */
  const EX_C = { touch: "#e4aba5", collab: "#d9c5c6", lounge: "#fce7ae", breakout: "#e9c8ff", quiet: "#b5f4d9", cafe: "#f2c596", social: "#f2c596", meet: "#a0bbeb", green: "#04db7f" };   // the deck's palette
  const EX_SW = { social: "linear-gradient(135deg, #f2c596 0 33%, #e9c8ff 33% 66%, #fce7ae 66%)" };
  const EX = {};
  function exMap(o) {
    if (EX[o]) return EX[o];
    const zs = (f) => Z[o].zones.filter(f), T = D[o].texts, spot = (re) => T.filter((t) => re.test(t.t)).map((t) => [t.x, t.y]);
    const area = (a) => a.reduce((s, z) => s + z.area, 0), hot = teamsOf(o).reduce((a, t) => a + (t.hot || 0), 0);
    const agile = agileOf(o), lounge = zs((z) => /^lounge$/i.test(z.name || "")), breakout = zs((z) => /breakout/i.test(z.name || ""));
    const booths = zs((z) => z.type === "quiet"), cafe = zs((z) => z.type === "cafe"), small = zs((z) => z.type === "meet" && /· 2 PAX/i.test(z.name || ""));
    const inside = (p, list) => list.some((z) => inPoly(p[0], p[1], z.poly));
    const bSpots = spot(/^BREAKOUT AREA$/i).filter((p) => !inside(p, breakout)), quietSpots = spot(/NAP ROOM|LIBRARY/i), discuss = spot(/DISCUSSION TABLE/i);
    const G = gzRun(o), plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
    const rows = [
      { k: "touch", t: "Comfortable touchdown spaces", polys: agile.map((z) => z.poly), spots: [],
        where: agile.length ? `${agile.map((z) => z.name).join(" + ")} · plus ${hot} hot desks in the teams` : `${hot} hot desks in the teams`, n: plural(agile.length, "agile area") + ` · ${hot} hot desks`, m2: area(agile) },
      { k: "collab", t: "Informal collaboration spaces", polys: [], spots: discuss, where: discuss.length ? "Discussion tables drawn in the workhall" : "—", n: discuss.length ? plural(discuss.length, "discussion table") : "—", m2: 0 },
      { k: "lounge", t: "Lounges", polys: lounge.map((z) => z.poly), spots: [], where: lounge.length ? "Lounge" : "—", n: lounge.length ? plural(lounge.length, "lounge") : "—", m2: area(lounge) },
      { k: "breakout", t: "Breakout areas", polys: breakout.map((z) => z.poly), spots: bSpots, where: `Breakout Area${breakout.length > 1 ? " ×" + breakout.length : ""}${bSpots.length ? " + one in the corridor" : ""}`, n: plural(breakout.length + bSpots.length, "breakout"), m2: area(breakout) },
      { k: "quiet", t: "Quiet / focus spaces", polys: booths.map((z) => z.poly), spots: quietSpots, where: `Phone booths${quietSpots.length ? " + nap room and library" : ""}`, n: plural(booths.length, "booth") + (quietSpots.length ? ` · ${quietSpots.length} quiet corners` : ""), m2: area(booths) },
      { k: "cafe", t: "Café / pantry experience", polys: cafe.map((z) => z.poly), spots: [], where: cafe.map((z) => gzName(z.name)).join(", "), n: "52 covers", m2: area(cafe) },
      { k: "social", t: "Social spaces", polys: [], spots: [], where: "The café, breakout" + (lounge.length ? " and lounge" : "") + " together", n: "café + breakout" + (lounge.length ? " + lounge" : ""), m2: area(cafe) + area(breakout) + area(lounge), note: true },
      { k: "meet", t: "Small spontaneous meeting areas", polys: small.map((z) => z.poly), spots: [], where: small.length ? "2-person rooms" : "—", n: small.length ? plural(small.length, "2-pax room") : "—", m2: area(small) },
      { k: "green", t: "Biophilic elements", polys: [], spots: [], zones: G.zones, where: "The green zones on the plan", n: `${G.zones.length} zones · ${fmt(G.placed + G.table)} plants`, m2: 0 },
    ];
    return (EX[o] = rows);
  }
  function exDraw(focus) {
    const o = state.opt, rows = exMap(o), items = [], green = gzGreen();
    const holes = rows.filter((r) => !r.note).flatMap((r) => r.polys);
    // the rest of the floor steps back: one mask with the experience spaces cut out
    items.push({ kind: "poly", rings: [Z.annot.outline].concat(holes), cls: "ex-mask", fill: "#000", stroke: "none", fo: 0.62 });
    rows.forEach((r) => {
      const on = !focus || focus === r.k || (focus === "social" && ["cafe", "breakout", "lounge"].includes(r.k)), c = EX_C[r.k];
      r.polys.forEach((q) => items.push({ kind: "poly", pts: q, fill: c, stroke: c, fo: on ? 0.85 : 0.1, sw: on ? 2 : 1 }));
      r.spots.forEach((s) => items.push({ kind: "poly", pts: circleP(s, 1200, 20), fill: c, stroke: c, fo: on ? 0.75 : 0.1, sw: 1.5 }));
      if (r.zones) r.zones.forEach((z) => gzGlyph(z, green).forEach((g) => items.push(Object.assign(g, on ? {} : { fo: 0.15 }))));
    });
    getPlanA().setOverlay(items);
  }
  function exList(sel) {
    const rows = exMap(state.opt), list = $(sel);
    list.innerHTML = rows.map((r) => `<li data-k="${r.k}"${r.n === "—" ? ' class="none"' : ""}><i class="sw" style="background:${EX_SW[r.k] || EX_C[r.k]}"></i><b>${r.t}</b><span>${r.n}</span></li>`).join("");
  }
  function exGreen() {
    const G = gzRun(state.opt);
    $("#ex-green").textContent = `Biophilia: ${G.zones.length} green zones and ${fmt(G.placed + G.table)} plants, placed where people stay and pass · score ${Math.round(G.score)}/100 (method in the Appendix).`;
  }
  H["s-ex"] = {
    enter() {
      layerPlan(state.opt, { furn: true, parts: true }); layerScene(); frames("right", OPTNAME[state.opt]);
      exList("#ex-list"); exDraw(); exGreen(); exCards(); legendHover($("#ex-list"), exDraw); getPlanA().fit(null, 800);
    },
    step(k) {
      shade(k === 2 ? "" : "left");
      $("#w-plan").style.filter = k === 2 ? "blur(3px)" : "";
      $$("#exc-board .exc").forEach((c, i) => { c.classList.remove("in"); if (k === 2) later(() => c.classList.add("in"), 80 + i * 90); });
    },
    opt() { layerPlan(state.opt, { furn: true, parts: true }); frames("right", OPTNAME[state.opt]); exList("#ex-list"); exDraw(); exGreen(); exCards(); },
    theme() { exDraw(); },
    leave() { $("#w-plan").style.filter = ""; getPlanA().setOverlay([]); frames("right"); },
  };

  /* ---- Part 3 · employee experience, the concept: the scooped-out spaces and their furniture ---- */
  function exCards() {
    const rows = exMap(state.opt);
    $$("#exc-board .exc").forEach((c) => {
      const r = rows.find((x) => x.k === c.dataset.k); if (!r) return;
      c.style.setProperty("--c", EX_C[r.k]);
      const w = c.querySelector(".exc-where"); if (w) w.textContent = `${OPTNAME[state.opt]}: ${r.where === "—" ? "not in this option" : r.where}`;
    });
  }
  /* ---- 03 the concept: the Living Network, abstract (no plan, no map) ---- */
  // trust in layers, drawn as Mitigata's mark: nested bands that touch, the logo's 90° sweep, ends cut along the radius,
  // the green band innermost and thickest (logo radii 108 / 87 / 60: outer edge, seam, hole)
  const TIERS = [
    { k: "Open", c: "#c9cecb", w: 46, t: "Forecourt and atrium" },
    { k: "Guest", c: "#f2c596", w: 46, t: "Reception, boardroom, café" },
    { k: "Team", c: "#a0bbeb", w: 46, t: "Workhalls, rooms, booths" },
    { k: "Secure", c: "#04db7f", w: 62, t: "SOC, server", key: true },
  ];
  const SVGNS = "http://www.w3.org/2000/svg";
  function sv(parent, tag, attrs, text) {
    const e = document.createElementNS(SVGNS, tag);
    for (const a in attrs || {}) e.setAttribute(a, attrs[a]);
    if (text !== undefined) e.textContent = text;
    parent.appendChild(e); return e;
  }
  // a line that draws itself (stroke-dashoffset), after a delay
  function drawIn(path, ms) {
    const L = path.getTotalLength(); path.style.strokeDasharray = L; path.style.strokeDashoffset = L; path.classList.add("tl-draw");
    later(() => (path.style.strokeDashoffset = 0), ms);
  }
  // viewBox 900 × 318: the mark on the left (outer radius 400, hole 200), one label column off its right-hand cut face
  function trustMark(svg) {
    const cx = 287, cy = 406, c45 = Math.SQRT1_2, XE = cx + 400 * c45 + 24, XL = 652;
    let r = 400;
    TIERS.forEach((T, i) => {
      const rm = r - T.w / 2, x0 = cx - rm * c45, x1 = cx + rm * c45, y = cy - rm * c45, ly = 107 + i * 60;
      r -= T.w;
      // a butt-capped stroke along the band's mid-radius: its square ends fall exactly on the radius, as on the logo
      const band = sv(svg, "path", { d: `M${x0} ${y} A ${rm} ${rm} 0 0 1 ${x1} ${y}`, class: "tl-band", stroke: T.c, "stroke-width": T.w + 1 });
      drawIn(band, 250 + i * 520);
      // the leader leaves the middle of the band's cut face, runs clear of the mark, then fans out to its row
      const g = sv(svg, "g", { class: "tl-lab" });
      sv(g, "path", { d: `M${x1} ${y} H ${XE} L ${XL - 16} ${ly - 7.5} H ${XL - 6}`, class: "tl-lead" });
      sv(g, "circle", { cx: x1, cy: y, r: 3, class: "tl-dot" });
      sv(g, "rect", { x: XL, y: ly - 14.5, width: 14, height: 14, fill: T.c });
      sv(g, "text", { x: XL + 24, y: ly, class: "tl-name" + (T.key ? " key" : "") }, T.k);
      sv(g, "text", { x: XL + 24, y: ly + 22, class: "tl-sub" }, T.t);
      later(() => g.classList.add("on"), 900 + i * 520);
    });
  }
  // deck slide 17: from data flow, to people flow, to ideas flow, one after another
  H["s-idea"] = {
    enter() { world("none"); shade(""); },
    step() {
      $$("#ln-flows span").forEach((x) => x.classList.remove("on"));
      $$("#ln-flows span").forEach((x, i) => later(() => x.classList.add("on"), 500 + i * 1100));
    },
  };
  // deck slide 18: its words come in, then the three principles light one by one (Ritika, 12.10)
  H["s-living"] = {
    enter() { world("none"); shade(""); },
    step() {
      const ins = $$("#s-living .lnet-in"), prs = $$("#s-living .ln-principles li");
      ins.concat(prs).forEach((x) => x.classList.remove("on"));
      ins.forEach((x, i) => later(() => x.classList.add("on"), 200 + i * 450));
      prs.forEach((x, i) => later(() => x.classList.add("on"), 1700 + i * 700));
    },
  };
  // the Appendix: trust in layers, drawn as Mitigata's mark
  H["s-layers"] = {
    enter() { world("none"); shade(""); },
    step() { const svg = $("#tl-svg"); svg.innerHTML = ""; trustMark(svg); },
  };

  /* ---- 05 two stories (side by side, no swipe) + scorecard ---- */
  const MIX = { opt1: roomMix("opt1"), opt2: roomMix("opt2") };
  function roomMix(opt) {
    const mix = {}; let pb = 0;
    D[opt].texts.forEach(({ t }) => {
      const u = t.toUpperCase().replace(/\s+/g, " ").trim();
      if (/^P\.?\s?B\b|PB\s*-\s*1/.test(u)) { pb++; return; }
      // meeting-room tags only ("MEETING ROOM 4 PAX" / "4 PAX"): team, café, SOC and boardroom labels also carry a PAX
      const m = u.match(/^(?:MEETING ROOM )?(\d+) ?PAX$/); if (m) mix[+m[1]] = (mix[+m[1]] || 0) + 1;
    });
    return { mix, pb, total: Object.values(mix).reduce((a, b) => a + b, 0) };
  }
  // the scorecard's rows: A4 in full, and compact on One model, two options (beat 1)
  function scoreRows() {
    const a = MIX.opt1, b = MIX.opt2, r1 = Z.opt1.routes, r2 = Z.opt2.routes;
    const sizes = (m) => Object.keys(m.mix).map(Number).sort((x, y) => x - y).join(" · ");
    const studio = (o) => Math.round(areaOf(o, ["studio"]));
    const rows = [
      ["Meeting rooms · target ≈16–17", `<span class="ok">${a.total}</span>`, `<span class="warn">${b.total}<span class="tagx">−1 to −2</span></span>`],
      ["Room sizes offered", `<span class="warn">${sizes(a)} pax</span><br><small class="mute">${a.mix[4]} identical 4-pax rooms</small>`, `<span class="ok">${sizes(b)} pax</span>`],
      ["Single-person booths · 6–7", `${a.pb}`, `${b.pb}`],
      ["SOC · seats / area", ...["opt1", "opt2"].map((o) => { const s = zonesOf(o, "soc")[0]; return `${s.seats}${s.seats < s.pax ? ` <small class="mute">of ${s.pax}</small>` : ""} · ≈${sqft(s.area)}`; })],
      ["SOC is seen from", VIEWS[0].seen, VIEWS[1].seen],
      ["SOC from inside", "A curved glass arc on the main path", "A display wall along the central corridor"],
      ["Visitor → boardroom", `${r1.visitor.m} m · a tour past the SOC`, `${r2.visitor.m} m · never crosses the floor`],
      ["Boardroom sits", "Far end, beside the prep counter", "By arrival, with a dine store"],
      ["Podcast studio", `<span class="ok">≈${sqft(studio("opt1"))}</span> · by the café`, `<span class="warn">≈${sqft(studio("opt2"))}</span> · by the SOC (tight)`],
      ["200-person footprint", sqft(Z.opt1.events["200"].area), sqft(Z.opt2.events["200"].area)],
      ["Night-shift recovery", '<span class="ok">Nap room</span>', "—"],
    ];
    return rows;
  }
  const scoreTable = (rows) => `<table class="score"><tr><th></th><th>${OPTNAME.opt1}</th><th>${OPTNAME.opt2}</th></tr>${rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")}</table>`;
  function scorecard() {
    const rows = scoreRows();
    return `<div class="panel-h"><span>Scorecard · measured from the test-fit CAD</span><span class="green">● same brief, two answers</span></div>
      <table class="score"><tr><th></th><th>${OPTNAME.opt1}</th><th>${OPTNAME.opt2}</th></tr>${rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")}</table>`;
  }
  /* ---- 10 the SOC, seen: the concept model (Sattva Hallmark in its street), then inside ---- */
  // where each option's SOC is seen: one view per layout option, framed in the camera editor
  // (absolute twin coordinates; eye ~3.5-4.5 m above the ground, long lenses, shift-lens rise)
  const VIEWS = [
    { opt: "opt1", inset: "soc-night", insetLabel: "SKV photomontage · Option 01", seen: "The atrium court",
      h: "Layout Option 01: the SOC faces the court.", p: "Everyone crossing the atrium court looks straight at it. At night it becomes a lantern.",
      cam: [-69.48, -3.92, -28.22], at: [-40.62, -7.36, -20.81], fov: 25, rise: 0.334 },
    { opt: "opt2", seen: "The road side",
      h: "Layout Option 02: the SOC turns to the road.", p: "At the prow, towards the gate and the service road: the first thing you see arriving.",
      cam: [-38.81, -3.17, 44.02], at: [-33.83, -5.73, 14.55], fov: 26, rise: 0.334 },
  ];
  // the views as eye points for TwinSite.keepClear: trees in a view's line of sight to its SOC move aside
  const clearViews = () => VIEWS.map((v, i) => { const f = camFrames[`s-w-soc/${i + 5}`]; return { eye: (f || v).cam, opt: v.opt }; });   // steps 5 and 6 of Inside the SOC
  // the lens, eased (the twin's fly() moves the rig, not the field of view)
  function tweenFov(t, to, ms) {
    cancelAnimationFrame(tweenFov.raf);
    const from = t.camera.fov, t0 = performance.now();
    const run = (now) => {
      const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      t.camera.fov = from + (to - from) * e; t.camera.updateProjectionMatrix();
      if (k < 1) tweenFov.raf = requestAnimationFrame(run);
    };
    tweenFov.raf = requestAnimationFrame(run);
  }
  // twin rig that puts the eye at cam looking at `at`
  function lookFrom(cam, at) {
    const dx = cam[0] - at[0], dy = cam[1] - at[1], dz = cam[2] - at[2], r = Math.hypot(dx, dy, dz);
    return { r, phi: Math.acos(dy / r), theta: Math.atan2(dx, dz), tx: at[0], ty: at[1], tz: at[2] };
  }
  function siteView(v) {
    const t = getTwin();
    if (t.site) t.site.keepClear(clearViews());
    const saved = camFrames[stepKey()];
    if (saved) v = Object.assign({}, v, saved);           // a frame set in the camera editor wins
    siteRise(t, 1, t.site && t.site.group.scale.y < 1 ? 600 : 0);
    t.setOption(v.opt || "opt1");
    t.setLayers({ site: true, cut: false, furn: true, walls: true, zones: false, tiers: false, routes: false, people: false });
    t.showEvent(null); t.setLabels([]); t.setShift(0); t.explode(0, 10); t.setSway(0, 0);
    t.setNight(theme() === "dark" ? 1 : 0, 1400);           // the theme is day / night here (T)
    t.setControl("free");                                  // Unreal-style camera: RMB look, RMB+WASD fly, Alt orbit
    t.keys = {};
    if (v.fov) {   // flying in from the site the lens eases; arriving cold it is set
      if (world.cur === "twin") tweenFov(t, v.fov, 2400);
      else { cancelAnimationFrame(tweenFov.raf); t.camera.fov = v.fov; t.camera.updateProjectionMatrix(); }
    }
    t.setRise(v.rise || 0, 1200);                          // a shift lens, as in the photomontage
    if (world.cur !== "twin") { t.fly(Object.assign(lookFrom(v.cam, v.at), { r: lookFrom(v.cam, v.at).r * 1.6 }), 10); }
    world("twin"); shade("bottom");
    t.home = lookFrom(v.cam, v.at);
    t.fly(t.home, 2400);
  }
  function siteOff() { cancelAnimationFrame(tweenFov.raf); if (twin) { siteRise(twin, 1); twin.setLayers({ site: false }); twin.setNight(0, 10); twin.setControl("orbit"); twin.setRise(0); twin.setShift(0); twin.home = null; } }
  // a render opens as an overlay (Ritika): ✕, Esc, a click beside it, or moving on closes it
  const LB = $("#lightbox");
  function lightbox(src, cap) { $("img", LB).src = src; $("figcaption", LB).textContent = cap || ""; LB.hidden = false; requestAnimationFrame(() => LB.classList.add("on")); }
  function lightboxOff() { if (LB.hidden) return false; LB.classList.remove("on"); setTimeout(() => { if (!LB.classList.contains("on")) LB.hidden = true; }, 300); return true; }
  LB.addEventListener("click", (e) => { if (!e.target.closest("img")) lightboxOff(); });
  document.addEventListener("keydown", (e) => {   // capture: Esc only closes the overlay; the arrows close it and carry on
    if (LB.hidden) return;
    if (e.key === "Escape") { lightboxOff(); e.stopImmediatePropagation(); e.preventDefault(); }
    else if (["ArrowRight", "ArrowLeft", "PageDown", "PageUp", " ", "Enter", "Backspace", "Home", "End"].includes(e.key)) lightboxOff();
  }, true);
  // the views are the slide's last beats (Ritika's Details beat moved them on one): counted from its end
  $("#soc-vinset").addEventListener("click", () => { const n = +$("#s-w-soc").dataset.steps, v = VIEWS[state.step - (n - VIEWS.length) - 1]; if (v && v.inset) lightbox(PHOTO.src(v.inset), v.insetLabel); });
  // "Back to the site" (Ritika): from Layout Option 01's axo the drawing dissolves into the model at the same angle, then the
  // camera pulls back until Sattva Hallmark stands in its street at dusk, the east wing cut open above Level 03
  const SITE_WIDE = { theta: -1.3, phi: 1.0, r: 250, tx: -16, ty: -4, tz: -8 };
  // the street grows up from the ground around the floor (which stays put), so the drawing hands over to the floor alone
  function siteRise(t, to, ms) {
    const g = t.site && t.site.group; if (!g) return;
    const G0 = -((window.MX_SITE && window.MX_SITE.slabZ) || 11.4);
    const l3 = t.site.l3;   // Level 03's ceiling and SOC halo belong to the floor: they stay at its height while the rest rises
    const set = (v) => {
      v = Math.max(0.001, v); g.scale.y = v; g.position.y = G0 * (1 - v);
      if (l3) { l3.scale.y = 1 / v; l3.position.y = (-G0 * (1 - v)) / v; }
    };
    cancelAnimationFrame(siteRise.raf);
    if (!ms) return set(to);
    const from = g.scale.y, t0 = performance.now();
    const run = (now) => { const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3); set(from + (to - from) * e); if (k < 1) siteRise.raf = requestAnimationFrame(run); };
    siteRise.raf = requestAnimationFrame(run);
  }
  function siteFromAxo() {
    const t = getTwin(), saved = camFrames[stepKey()], fromAxo = world.cur !== "twin" && world.cur !== "photo" && axo && axo.fr;   // from the SOC render (slide 16) it is never the axo
    if (t.site) t.site.keepClear(clearViews());
    const shown = fromAxo && axo.one === 1 ? "opt2" : "opt1";   // the drawing on screen hands over; the court view is Option 01's
    t.setOption(shown);
    t.setLayers({ site: true, cut: true, furn: true, walls: true, zones: false, tiers: false, routes: false, people: false });
    t.showEvent(null); t.setLabels([]); t.explode(0, 10); t.setSway(0, 0);
    t.setControl("free"); t.keys = {};
    if (fromAxo) {
      // the model's camera where the drawing's was: same angles, a long lens sized so the floor fills the same frame
      const p = axo.pose(), W = innerWidth, H = innerHeight, F = 12;
      const r = (p.halfH * H / p.rect[3]) / Math.tan((F * Math.PI) / 360);
      cancelAnimationFrame(tweenFov.raf); t.camera.fov = F;
      t.setShift((p.rect[0] + p.rect[2] / 2 - W / 2) / W); t.setRise((p.rect[1] + p.rect[3] / 2 - H / 2) / H);
      t.fly({ theta: p.theta, phi: p.phi, r, tx: p.center[0], ty: p.center[1], tz: p.center[2] }, 10);
      t.setNight(0, 10); siteRise(t, 0);
    } else siteRise(t, 1, 600);
    world("twin"); shade("bottom");
    const wide = saved ? lookFrom(saved.cam, saved.at) : SITE_WIDE;
    t.home = wide;
    later(() => {
      t.fly(wide, 3400); t.setShift(0, 2600); t.setRise(0, 2600); t.setNight(0.6, 3000); siteRise(t, 1, 3200);
      tweenFov(t, (saved && saved.fov) || 30, 3000);
      if (shown !== "opt1") later(() => t.setOption("opt1"), 3600);   // swapped far away, where it is quiet
    }, fromAxo ? 900 : 0);
  }
  function fillTicker() {
    const tk = $("#soc-ticker div"); if (tk.innerHTML) return;
    const items = ["SOC · LIVE", "DETECT · COMPLY · INSURE · RESPOND", "50+ THREAT ANALYSTS", "1M+ ENDPOINTS MONITORED", "MEAN TIME TO DETECT 4.2 MIN", "60-MIN BREACH RESPONSE", "INDIA'S OWN CYBER RESILIENCE PLATFORM"];
    tk.innerHTML = items.concat(items).map((t) => `<em><span>●</span> ${t}</em>`).join("");
  }
  H["s-soc"] = {
    enter() { fillTicker(); },
    // 1 back to the site (from the axo) · 2–3 where each option's SOC is seen (inside the SOC opens the walk, Ritika)
    step(k) {
      clearTimers(); $("#soc-ticker").classList.remove("on"); lightboxOff();
      const site = window.TwinSite && window.MX_SITE;
      if (k === 1) {
        frames("right"); LAYERS.plan.classList.remove("docked");
        if (site) siteFromAxo(); else { PHOTO.show("soc-night", { kb: true }); world("photo"); shade("photo"); }
      } else if (k <= VIEWS.length + 1) {
        const v = VIEWS[k - 2];
        frames("right"); LAYERS.plan.classList.remove("docked");
        $("#soc-vinset").style.display = v.inset ? "" : "none";
        if (v.inset) { $("#soc-vinset").style.backgroundImage = `url(${PHOTO.src(v.inset)})`; $("#soc-vinset span").textContent = v.insetLabel || ""; }
        if (site) siteView(v);
        else { PHOTO.show(v.inset || "soc-night", { kb: true }); world("photo"); shade("photo"); }
        $("#soc-vh").textContent = v.h; $("#soc-vp").textContent = v.p;
      }
    },
    leave() { if (CAM.on) toggleCam(false); siteOff(); $("#soc-ticker").classList.remove("on"); lightboxOff(); },
  };

  /* ---- event densities (Appendix: event capacity) ---- */
  const DENS = [["Theatre", 0.75], ["Standing", 0.8], ["Cabaret", 1.4], ["Workshop", 2.0]];
  /* ---- 10 spaces & signature moments ---- */
  const REC = [[2, 3], [4, 5], [6, 4], [8, 2], [12, 1], [16, 1]];
  // the Option 01 podcast room as drawn in Testfit OP1 · 09.10.26 (its furniture layer, "Podcast room", 17.7 m²): the walls and door,
  // the two cameras, the round set with a table and two rounds, the lounge chair, the curved sofa and the planting.
  // Plan coordinates, north to the right as on every plan; the room's inner corner is (64026, 20281), 3204 × 5518 mm.
  const STUDIO_O1 = {
    wall: "<path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M0 -50L5517 -50L5517 50L0 50L0 -50M100 -50L0 -50L0 50L100 50L100 -50M1000 -50L5517 -50L5517 50L1000 50L1000 -50\"/><path class=\"s\" transform=\"matrix(-1 -0 -0 -1 67230.3 20215.1)\" d=\"M0 -66L3304 -66L3304 66L0 66L0 -66M3304 -66L0 -66L0 66L3304 66L3304 -66\"/><path class=\"f\" transform=\"matrix(-1 -0 -0 -1 67230.3 20215.1)\" d=\"M0 66L3304 66L3304 -66L0 -66L0 66\"/><path class=\"s\" transform=\"matrix(-1 -0 -0 1 67230.3 25848.6)\" d=\"M0 -50L3304 -50L3304 50L0 50L0 -50M3304 -50L0 -50L0 50L3304 50L3304 -50\"/><path class=\"f\" transform=\"matrix(-1 -0 -0 1 67230.3 25848.6)\" d=\"M0 50L3304 50L3304 -50L0 -50L0 50\"/>",
    door: "<path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M962 25L962 -25L967 -25L967 -20L975 -20L975 -50L1000 -50L1000 50L975 50L975 25L967 25L967 30L952 30L952 25L962 25M100 50L125 50L125 25L133 25L132 30L148 30L148 25L138 25L138 -25L132 -25L133 -20L125 -20L125 -50L100 -50L100 50\"/><path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M962 -20C962 -239 875 -448 721 -603C566 -757 357 -844 138 -844M138 -20L138 -844\"/><path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M142 22L142 -22L957 -22L957 22L142 22\"/><path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M1000 0L100 0\"/><path class=\"s\" transform=\"matrix(0 1 -1 0 63976.4 20281.1)\" d=\"M812 93C812 98 815 102 819 104C823 107 827 107 831 104C835 102 837 98 837 93M812 93L812 22L837 22L837 93M837 -94C837 -98 835 -102 831 -104C827 -107 823 -107 819 -104C815 -102 812 -98 812 -94M812 -94L812 -23L837 -23L837 -94\"/>",
    furn: "<path class=\"s\" d=\"M67230 20281L64026 20281L64026 25799L67230 25799L67230 20281\"/><path class=\"s\" d=\"M65753 23942C65753 24108 65618 24242 65453 24242C65287 24242 65153 24108 65153 23942C65153 23776 65287 23642 65453 23642C65618 23642 65753 23776 65753 23942M65956 23623C65956 23706 65889 23773 65806 23773C65723 23773 65656 23706 65656 23623C65656 23540 65723 23473 65806 23473C65889 23473 65956 23540 65956 23623M66193 23951C66193 24062 66104 24151 65993 24151C65883 24151 65793 24062 65793 23951C65793 23841 65883 23751 65993 23751C66104 23751 66193 23841 66193 23951\"/><path class=\"s\" d=\"M67050 24128C67050 24840 66473 25417 65762 25417C65050 25417 64474 24840 64474 24128C64474 23417 65050 22840 65762 22840C66473 22840 67050 23417 67050 24128\"/><path class=\"s\" transform=\"matrix(0.32591 -0.945401 0.945401 0.32591 -2816879.4 -790885.8)\" d=\"M169220.4 2989113.2C169235.6 2989113.4 169250.9 2989113.6 169266.2 2989114.4C169297.4 2989116 169328.9 2989120 169358 2989131.1C169381.1 2989140 169402.7 2989153.3 169421.2 2989169.7C169436.8 2989183.5 169450.2 2989199.6 169462.6 2989216.3C169477.2 2989236.3 169490.4 2989257.4 169502.9 2989278.8C169517.8 2989304.4 169531.8 2989330.6 169545 2989357.3C169573.2 2989414.4 169597.5 2989473.5 169620.6 2989532.9C169629.5 2989555.9 169638.2 2989578.9 169646.8 2989601.9C169652.3 2989616.9 169657.8 2989631.8 169663.3 2989646.8C169670.9 2989667.9 169678.4 2989689.1 169685.9 2989710.1C169689.5 2989720.3 169693.2 2989730.5 169696.3 2989741C169697.5 2989745 169698.6 2989749 169699.4 2989752.9C169699.7 2989754.5 169700 2989756 169699.8 2989757.8C169699.7 2989758.2 169699.7 2989758.5 169699.5 2989758.7C169699.3 2989758.9 169699 2989759 169698.7 2989759.1M169220.2 2989341.8C169223.5 2989341.8 169226.8 2989341.8 169230.1 2989341.9C169236.7 2989342 169243.4 2989342.4 169250 2989342.9C169263.3 2989343.9 169276.6 2989345.5 169289.7 2989347.9C169311.9 2989351.8 169333.7 2989357.8 169354.7 2989366.4C169372.4 2989373.6 169389.5 2989382.8 169403.7 2989395.1C169418.1 2989407.6 169429.6 2989423.3 169440.8 2989438.9C169452.5 2989455.3 169463.8 2989471.7 169475.4 2989487.9C169488.4 2989506.2 169501.8 2989524.3 169515.3 2989542.2C169531.1 2989563.3 169547.2 2989584.2 169563.6 2989604.8C169577.1 2989621.6 169590.8 2989638.3 169604.5 2989654.9C169614.4 2989667 169624.4 2989679.1 169634.4 2989691.2C169641.9 2989700.2 169649.4 2989709.3 169656.4 2989718.6C169661.6 2989725.4 169666.6 2989732.3 169671.7 2989739.1C169673.8 2989741.9 169675.9 2989744.6 169678.1 2989747.1C169679.7 2989749 169681.4 2989750.8 169683.3 2989752.5C169684.9 2989753.9 169686.5 2989755.2 169688.4 2989756.2C169689.6 2989756.9 169690.9 2989757.5 169692.2 2989757.9C169693.3 2989758.3 169694.4 2989758.7 169695.5 2989758.9C169696.6 2989759 169697.6 2989759 169698.7 2989759.1M169220.4 2989857.9C169242.3 2989857.6 169264.3 2989857.4 169286.2 2989856.6C169316.4 2989855.5 169346.6 2989853.3 169376.7 2989850C169414.5 2989845.9 169452.2 2989840.1 169489.4 2989832.1C169516.9 2989826.2 169544.2 2989819.1 169571 2989810.7C169607.6 2989799.2 169643.5 2989785.2 169678.2 2989768.9C169685.3 2989765.6 169692.4 2989762.1 169699.5 2989758.7M169220.4 2989113.2C169205.1 2989113.4 169189.9 2989113.6 169174.6 2989114.4C169143.4 2989116 169111.9 2989120 169082.8 2989131.1C169059.7 2989140 169038 2989153.3 169019.5 2989169.7C169003.9 2989183.5 168990.5 2989199.6 168978.2 2989216.3C168963.5 2989236.3 168950.4 2989257.4 168937.9 2989278.8C168922.9 2989304.4 168908.9 2989330.6 168895.8 2989357.3C168867.5 2989414.4 168843.3 2989473.5 168820.2 2989532.9C168811.3 2989555.9 168802.6 2989578.9 168794 2989601.9C168788.4 2989616.9 168782.9 2989631.8 168777.5 2989646.8C168769.9 2989667.9 168762.4 2989689.1 168754.9 2989710.1C168751.2 2989720.3 168747.6 2989730.5 168744.4 2989741C168743.3 2989745 168742.1 2989749 168741.4 2989752.9C168741 2989754.5 168740.8 2989756 168741 2989757.8C168741 2989758.2 168741.1 2989758.5 168741.3 2989758.7C168741.5 2989758.9 168741.8 2989759 168742.1 2989759.1M169220.5 2989341.8C169217.3 2989341.8 169214 2989341.8 169210.7 2989341.9C169204 2989342 169197.4 2989342.4 169190.8 2989342.9C169177.5 2989343.9 169164.2 2989345.5 169151 2989347.9C169128.9 2989351.8 169107.1 2989357.8 169086.1 2989366.4C169068.4 2989373.6 169051.3 2989382.8 169037 2989395.1C169022.6 2989407.6 169011.1 2989423.3 168999.9 2989438.9C168988.3 2989455.3 168976.9 2989471.7 168965.3 2989487.9C168952.3 2989506.2 168939 2989524.3 168925.5 2989542.2C168909.6 2989563.3 168893.6 2989584.2 168877.1 2989604.8C168863.7 2989621.6 168850 2989638.3 168836.3 2989654.9C168826.3 2989667 168816.3 2989679.1 168806.3 2989691.2C168798.9 2989700.2 168791.4 2989709.3 168784.3 2989718.6C168779.1 2989725.4 168774.2 2989732.3 168769 2989739.1C168767 2989741.9 168764.9 2989744.6 168762.7 2989747.1C168761 2989749 168759.3 2989750.8 168757.5 2989752.5C168755.9 2989753.9 168754.2 2989755.2 168752.4 2989756.2C168751.2 2989756.9 168749.9 2989757.5 168748.6 2989757.9C168747.5 2989758.3 168746.4 2989758.7 168745.2 2989758.9C168744.2 2989759 168743.1 2989759 168742.1 2989759.1M169220.4 2989857.9C169198.4 2989857.6 169176.5 2989857.4 169154.6 2989856.6C169124.4 2989855.5 169094.2 2989853.3 169064.1 2989850C169026.3 2989845.9 168988.6 2989840.1 168951.4 2989832.1C168923.9 2989826.2 168896.6 2989819.1 168869.7 2989810.7C168833.1 2989799.2 168797.3 2989785.2 168762.6 2989768.9C168755.5 2989765.6 168748.4 2989762.1 168741.3 2989758.7\"/><path class=\"s\" transform=\"matrix(-994.2 82.802184 -82.802184 -994.2 60592.7 22320.1)\" d=\"M-6.199 -3.396L-5.907 -3.572C-5.869 -3.59 -5.828 -3.602 -5.787 -3.609L-5.262 -3.678L-4.662 -3.696C-4.626 -3.69 -4.59 -3.681 -4.555 -3.668L-4.17 -3.505L-3.894 -3.361C-3.856 -3.322 -3.843 -3.265 -3.862 -3.213L-4.056 -2.778C-4.1 -2.736 -4.159 -2.714 -4.219 -2.718L-4.849 -2.885L-5.863 -2.875C-5.932 -2.858 -6.004 -2.89 -6.037 -2.953C-6.093 -3.06 -6.155 -3.164 -6.222 -3.264C-6.233 -3.28 -6.237 -3.299 -6.235 -3.318C-6.233 -3.329 -6.231 -3.341 -6.229 -3.353C-6.225 -3.371 -6.214 -3.386 -6.199 -3.396M-4.171 -3.223L-4.222 -3.237L-4.31 -3.264L-4.426 -3.302L-4.552 -3.343L-4.696 -3.375L-4.764 -3.379L-4.867 -3.385L-5.043 -3.384L-5.205 -3.383L-5.353 -3.384L-5.398 -3.385L-5.489 -3.387L-5.593 -3.391L-5.642 -3.393L-5.672 -3.394L-5.716 -3.396L-5.763 -3.41L-5.799 -3.449L-5.817 -3.494L-5.81 -3.528L-5.793 -3.547L-5.789 -3.552L-5.789 -3.552L-5.766 -3.568L-5.766 -3.568L-5.74 -3.578L-5.711 -3.585L-5.647 -3.594L-5.522 -3.61L-5.363 -3.627L-5.202 -3.642L-5.028 -3.654L-4.834 -3.661L-4.643 -3.649L-4.643 -3.649L-4.643 -3.649L-4.522 -3.613L-4.478 -3.601L-4.478 -3.601L-4.339 -3.538L-4.223 -3.482L-4.155 -3.447L-4.135 -3.437L-4.09 -3.413L-4.09 -3.413L-4.069 -3.4L-4.049 -3.384L-4.049 -3.384L-4.033 -3.364L-4.033 -3.364L-4.024 -3.337L-4.021 -3.307L-4.021 -3.307L-4.025 -3.285L-4.025 -3.286L-4.036 -3.266L-4.036 -3.267L-4.054 -3.248L-4.079 -3.232L-4.112 -3.223L-4.11 -3.224L-4.11 -3.224L-4.139 -3.22L-4.158 -3.221L-4.171 -3.223\"/>",
    cam: "<path class=\"s\" d=\"M66533 21887L67085 22266L66941 22476L66389 22098L66533 21887M66233 22355L66665 22287M66757 22714L66665 22287\"/><path class=\"s\" d=\"M65095 20937L65764 20924L65769 21179L65100 21192L65095 20937M65123 21493L65435 21186M65758 21480L65435 21186\"/>",
    green: "<path class=\"s\" transform=\"matrix(-0.025132 0.613819 0.613819 0.025132 64525.6 25306.3)\" d=\"M184 -160L300 -216L466 -211L305 -259L231 -252M165 74L178 100L258 219L148 134L31 81M-60 80L-167 277L-177 413L-133 288L-82 205M-262 211L-349 311L-384 461L-292 325L-138 194L-59 79M-621 227L-442 220L-194 87M-162 -215L-208 -362L-295 -481M-32 -50L-67 -162L-92 -323M73 -127L171 -316L301 -450L332 -520M164 -155L297 -190L434 -183L595 -239L480 -141L371 -99L171 -75L90 -71M146 24L336 34L529 59L606 69M38 136L94 230L129 377M-18 115L-36 272L-29 427L3 560M595 -239L483 -113L357 -61L82 -11M-134 -236L-180 -390L-365 -593L-309 -457L-288 -341L-157 -155M-151 -78L-358 -127L-569 -120L-677 -26L-544 -61L-337 -47L-199 8M-106 -106L-232 -225L-404 -267L-628 -257L-418 -215L-236 -117L0 0M0 0L-22 -197L-88 -397L-78 -628L-127 -404L-134 -176L-74 -50L0 0M0 0L34 -190L122 -351L304 -520L353 -611L343 -488L276 -344L178 -187L0 0M332 83L406 136L476 255L490 311L409 244L262 136L132 59M0 0L266 -36L448 -8L613 48L690 52L578 94L371 90L196 76L94 48L0 0M-11 20L132 195L164 458L39 300M0 0L-173 160L-376 276L-562 276L-674 220L-509 185L-327 24L-155 3L0 0M0 0L0 171L41 307L59 490L13 661M-11 20C-129 220 -119 471 13 661M87 -286L153 -492L234 -537L118 -516L52 -383L39 -199\"/><path class=\"s\" transform=\"matrix(-3.746069 -0.977109 -0.977109 3.746069 64252.1 25094.8)\" d=\"M-4.6 -66.5L-7.6 -55.3L-12.6 -57.7L-17.2 -54.8L-22.1 -55.3L-29.4 -50.9L-36.6 -50.4L-41.6 -46L-41.6 -42.1L-45.4 -37.7L-52.3 -36.7L-60.7 -36.7L-54.9 -33.7L-51.1 -27.4L-54.5 -21L-58.4 -17.1L-57.6 -11.2L-58.7 -5.4L-63.7 -2.4L-59.1 0L-56.8 6.8L-58.4 13.2L-56.5 20.5L-52.3 23.5L-51.1 27.4L-51.1 32.3L-45 35.2L-42 39.1L-42.7 47.9L-45.4 54.3L-40.4 49.4L-35.5 46L-31.7 46.9L-27.1 51.8L-21.4 56.2L-16 56.7L-3.4 60.1L0 71.9L1.5 60.1L3.1 58.2L8.4 56.2L14.1 56.7L22.5 54.3L27.5 50.4L33.9 49.4L37 45L42.7 39.6L43.1 35.7L45 34.7L51.9 36.2L46.2 29.3L51.9 28.4L53.8 25.9L56.1 21.5L57.6 20.5L55.7 18.1L57.2 5.9L59.9 2.9L58.7 -3.4L60.3 -7.8L67.1 -11.2L74.8 -14.2L67.9 -13.7L58.4 -13.7L54.9 -16.6L54.2 -27.9L50.4 -32.3L43.9 -39.1L42.7 -42.5L43.1 -47.4L35.5 -49.9L31.7 -47.9L27.1 -50.9L14.5 -61.1L9.2 -59.7L2.3 -56.7L-3.1 -57.7L-4.6 -66.5M-11 -56.5L-9.2 -58.4L-10.1 -63.5L-8.9 -67L-3.4 -69.8L2.7 -72.1L-2.8 -71.7L-10.4 -71.7L-13.2 -74.1L-13.8 -83.1L-16.9 -86.6L-22 -92.1L-23 -94.8L-22.7 -98.7L-28.8 -100.7L-31.8 -99.1L-35.5 -101.5L-45.5 -109.7L-49.8 -108.5L-55.3 -106.2L-59.6 -106.9L-60.8 -114L-63.2 -105L-67.2 -106.9L-70.9 -104.6L-74.8 -105L-80.6 -101.5L-86.4 -101.1L-90.4 -97.5L-90.4 -94.4L-93.5 -90.9L-98.9 -90.1L-105.7 -90.1L-101.1 -87.8L-98 -82.7L-100.8 -77.6L-103.8 -74.5L-103.2 -69.8L-104.1 -65.1L-108.1 -62.7L-104.4 -60.8L-102.6 -55.3L-103.8 -50.2L-102.3 -44.3L-98.9 -42L-98 -38.9L-98 -35L-93.1 -32.6L-90.7 -29.5L-91.3 -22.4L-93.5 -17.3L-89.5 -21.3L-85.5 -24L-82.5 -23.2L-78.8 -19.3L-74.2 -15.8L-70 -15.4L-59.9 -12.7L-58.3 -7.1M59.4 -5.3L60.9 -4.9L62.7 1L63.4 -4.9L64.2 -5.8L66.8 -6.8L69.7 -6.6L73.9 -7.8L76.4 -9.7L79.6 -10.2L81.2 -12.4L84 -15.1L84.2 -17.1L85.2 -17.6L88.6 -16.8L85.7 -20.3L88.6 -20.8L89.5 -22L90.7 -24.2L91.5 -24.7L90.5 -25.9L91.3 -32L92.6 -33.5L92 -36.6L92.8 -38.8L96.2 -40.6L100 -42L96.6 -41.8L91.8 -41.8L90.1 -43.2L89.7 -48.9L87.8 -51.1L84.6 -54.5L84 -56.2L84.2 -58.7L80.4 -59.9L78.5 -58.9L76.2 -60.4L69.9 -65.5L67.2 -64.8L63.8 -63.3L61.1 -63.8L60.4 -68.2L58.8 -62.6L56.4 -63.8L54.1 -62.3L51.6 -62.6L48 -60.4L44.3 -60.1L41.9 -57.9L41.9 -56L40 -53.8L36.5 -53.3L32.3 -53.3L35.2 -51.8L36.6 -49.4M-58.1 -61.9L-59 -60.8L-57.1 -60.8L-58.1 -61.9M-1.1 -1.5L-2.3 0L0 0L-1.1 -1.5M62.1 -35.7L61.5 -34.9L62.7 -34.9L62.1 -35.7\"/>",
  };
  // used by the walk (dark stage) and Appendix A9 (white page): the drawing is currentColor, our concept is in colour
  function drawStudio(svg) {
    const C = STUDIO_O1, W = 3204, H = 5518;
    // a camera's view, opened along its own V
    const cone = (a, p, q, len) => {
      const out = (v) => { const l = Math.hypot(v[0] - a[0], v[1] - a[1]); return [a[0] + ((v[0] - a[0]) / l) * len, a[1] + ((v[1] - a[1]) / l) * len]; };
      const P = out(p), Q = out(q);
      return `<path class="sd-cone" d="M${a[0]} ${a[1]}L${P[0]} ${P[1]}L${Q[0]} ${Q[1]}Z"/>`;
    };
    // a label in a side column with a thin leader to what it names, so no label sits on the drawing
    const lab = (t, y, at, right, cls) => {
      const x = right ? 3820 : -620;
      return (at ? `<path class="sd-lead" d="M${at[0]} ${at[1]}L${x + (right ? -70 : 70)} ${y - 55}"/>` : "") +
        `<text class="sd-lbl${cls ? " " + cls : ""}" x="${x}" y="${y}" text-anchor="${right ? "start" : "end"}">${t}</text>`;
    };
    svg.setAttribute("viewBox", "-2900 -900 8600 7500");
    svg.innerHTML =
      `<rect class="sd-room" width="${W}" height="${H}"/>` +
      cone([1409, 905], [1097, 1212], [1732, 1199], 1900) + cone([2639, 2006], [2207, 2074], [2731, 2433], 1900) +
      `<g class="sd-cad" transform="translate(-64026 -20281)"><g class="sd-wall">${C.wall}</g><g class="sd-door">${C.door}</g>` +
      `<g class="sd-furn">${C.furn}</g><g class="sd-green">${C.green}</g><g class="sd-cam">${C.cam}</g></g>` +
      // our concept on the drawing: a box-in-box shell, a pixel wall behind the sofa, ON AIR by the door
      `<rect class="sd-bxb" x="120" y="120" width="${W - 240}" height="${H - 240}"/>` +
      `<path class="sd-pix" d="M520 ${H - 70}L2880 ${H - 70}"/>` +
      `<g class="sd-onair"><rect x="-560" y="1090" width="420" height="170"/><text x="-350" y="1218" text-anchor="middle">ON AIR</text></g>` +
      `<path class="sd-dim" d="M0 -380L${W} -380M0 -450L0 -310M${W} -450L${W} -310"/><text class="sd-num" x="${W / 2}" y="-470" text-anchor="middle">3.2 m</text>` +
      `<path class="sd-dim" d="M3420 0L3420 ${H}M3350 0L3490 0M3350 ${H}L3490 ${H}"/><text class="sd-num" x="3570" y="1250" text-anchor="middle" transform="rotate(90 3570 1250)">5.5 m</text>` +
      `<path class="sd-dim" d="M-2600 -560L-2150 -560M-2260 -620L-2150 -560L-2260 -500"/><text class="sd-num" x="-2080" y="-505">N</text>` +
      lab("Door from the café", 520, [-100, 550]) + lab("ON AIR signal", 1218) + lab("Box-in-box · NR 25", 2250, [120, 2250]) +
      lab("Lounge chair", 3150, [200, 3150]) + lab("Planting", 4520, [150, 4650]) +
      lab("CAM A", 830, [1743, 777], true, "cam") + lab("CAM B", 1830, [3040, 1900], true, "cam") + lab("Round set · Ø 2.6 m", 2800, [2647, 2936], true) +
      lab("Table · Ø 600", 3560, [1727, 3661], true) + lab("Curved sofa", 4480, [3010, 4620], true) + lab("Network pixel wall", 5420, [2880, H - 70], true, "pix") +
      `<text class="sd-foot" x="${W / 2}" y="6150" text-anchor="middle">Podcast room · Option 01 · 3.2 × 5.5 m · ≈${sqft(18)}</text>` +
      `<text class="sd-note" x="${W / 2}" y="6420" text-anchor="middle">As drawn in the 09.10 layout; in colour, our studio concept</text>`;
  }
  /* ---- the walk: every space, a moment — Sidvin's gallery: a slow drift, music, pan mode, keyplan on / off ---- */
  // every render is of Option 01. Pins: [kind, image, label, x %, y % of the render, "l" = label on the left]; the kinds are the kit of
  // parts, acoustics and brand, as labels on the render (Ritika, 12.10: they don't jump to those pages).
  const WALK = [
    { id: "s-w-soc", n: "Inside the SOC", img: "soc", cam: "soc", soc: true,
      p: "80 analysts facing one command wall, under an arc of light.",
      pins: [["b", "soc-wall", "Command wall · video wall", 36, 45], ["k", "mat-metal-mesh", "Arc ceiling · lit cove + mesh", 31, 12],
        ["b", "soc-ticker", "Live ticker · threat feed", 73.6, 41.5, "l"], ["k", "soc-desk", "Analyst desks · curved rows", 62, 74]] },
    { id: "s-w-arrival", n: "Arrival", img: "reception", cam: "reception",
      p: "A warm, secure arrival. Mitigata's arc becomes a lit canopy; turnstiles hide in the joinery, and guests wait on the guest side.",
      pins: [["k", "mat-metal-mesh", "Canopy · Mitigata's arc in metal mesh", 50, 22], ["k", "ar-turnstile", "Turnstiles", 31, 53], ["b", "mat-biophilia", "Planted desk · biophilia", 57, 55], ["k", "mat-acrylic", "Desk · fluted acrylic", 61, 71],
        ["k", "mat-oak", "Wall · wooden panel", 82, 50, "l"], ["b", "brand-inlay", "Floor inlay · way-finding", 70, 87, "l"]] },
    { id: "s-w-breakout", n: "Breakout", img: "breakout", cam: "breakout",
      p: "Spaces that spark spontaneous collaboration: tiered seats along the glass, a live screen overhead, and soft seats on the green island.",
      pins: [["k", "mat-metal-mesh", "Arc tray · metal mesh", 62.3, 33.3, "l"], ["b", "bo-screen", "Screen · business narratives", 43, 32],
        ["k", "mat-fabric", "Lounge chairs · fabric", 66, 64], ["k", "mat-carpet", "Island · carpet", 73, 85, "l"], ["b", "mat-biophilia", "Planters · biophilia", 80, 52, "l"]] },
    { id: "s-w-meeting", n: "Meeting room · 6 pax", img: "meeting6", cam: "meeting6",
      p: "Rooms that fit the meeting: 16–17 in a real mix of sizes, every one VC-ready — felt, baffles and rated glass keep every word in the room.",
      pins: [["a", "acou-ceiling", "Suspended baffle · RT60 control", 55, 15], ["a", "acou-wall", "Felt wall panels · speech clarity", 36, 30, "l"], ["a", "acou-glazing", "Glass door · acoustic-rated", 16, 52],
        ["k", "mat-acoustic-felt", "Mint felt · acoustic panelling", 73, 50, "l"], ["k", "mat-fabric", "Chairs · fabric", 64, 76]] },
    { id: "s-w-boardroom", n: "Boardroom", img: "boardroom", cam: "boardroom", dinner: "boardroom-dinner",
      present: "boardroom-present",   // the presentation render (Ritika, 15.10)
      p: "One room, two lives: a board meeting at ten, a hosted dinner at eight — the same table, two renders.",
      // the meeting and the dinner renders share the camera, so the pins hold for both (Ritika, 12.10)
      pins: [["a", "acou-ceiling", "Acoustic ceiling · felt panels", 30, 14], ["k", "mat-oak", "Wall · wooden panel", 60, 43], ["a", "acou-glazing", "Glass wall", 85, 45, "l"],
        ["k", "br-bench", "Bench seating · storage below", 21, 66], ["k", "br-chair", "Leather chairs · wipe-clean", 73, 63, "l"], ["k", "br-lvt", "LVT flooring · spill-proof for dining", 80.4, 93.5, "l"], ["k", "mat-carpet", "Carpet · soft underfoot for long sittings", 46, 86]] },
    { id: "s-w-studio", n: "Studio · On Air", studio: true,
      p: "As drawn: two cameras on a round set, a lounge chair and a curved sofa, in a box-in-box shell with ON AIR by the door. The render follows." },
  ];
  // Ritika, 12.10: one slide per space (s-w-<space>, in order.txt). The walk's controls — music, pan, keyplan, the name block and the
  // index — are one set (in _shell.html), moved into whichever walk slide is open
  const WKUI = $$("#walk-ui > *"), PHL = LAYERS.photo;
  let WK = null;
  const isWalk = (s) => !!s && s.classList.contains("walk");

  // music: fades in on the walk, out when you leave; a browser only plays after a click or key, so it retries on the next one
  const AUD = {
    el: $("#wk-audio"), muted: false, want: false, fadeT: null, level: 0.35,   // level: the slider's volume (Ritika, 15.10)
    fade(to, ms, then) {
      const a = this.el, from = a.volume, n = 16; let i = 0;
      clearInterval(this.fadeT);
      this.fadeT = setInterval(() => { a.volume = clamp(from + (to - from) * (++i / n), 0, 1); if (i >= n) { clearInterval(this.fadeT); if (then) then(); } }, ms / n);
    },
    play() {
      this.want = true;
      if (this.muted) return;
      const a = this.el;
      if (!a.paused) { this.fade(this.level, 600); return; }
      a.volume = 0;
      a.play().then(() => this.fade(this.level, 800)).catch(() => { /* not allowed yet: retried on the next click or key */ });
    },
    silence() { if (!this.el.paused) this.fade(0, 500, () => this.el.pause()); },
    stop() { this.want = false; this.silence(); },
  };
  ["keydown", "pointerdown"].forEach((ev) => document.addEventListener(ev, () => { if (AUD.want && !AUD.muted && AUD.el.paused) AUD.play(); }));
  $("#wk-mute").onclick = () => {
    AUD.muted = !AUD.muted; $("#wk-mute").classList.toggle("muted", AUD.muted);
    if (AUD.muted) AUD.silence(); else AUD.play();
  };
  // the volume slider beside it: sets the level at once; turning it up unmutes, at 0 it reads as muted; the arrow keys go back to the deck
  const LVL = $("#wk-level");
  LVL.addEventListener("input", () => {
    AUD.level = LVL.value / 100;
    if (AUD.level > 0 && AUD.muted) { AUD.muted = false; AUD.play(); }
    $("#wk-mute").classList.toggle("muted", AUD.muted || AUD.level === 0);
    if (!AUD.el.paused && !AUD.muted) { clearInterval(AUD.fadeT); AUD.el.volume = AUD.level; }
  });
  ["change", "pointerup"].forEach((ev) => LVL.addEventListener(ev, () => LVL.blur()));

  // pan mode: the render grows to 1.35× and follows the mouse, never past its edges
  const PAN = { on: false, x: 0, y: 0, drag: null, s: 1.35 };
  function panTo(x, y) {
    const c = PHOTO.cur && $(".cover", PHOTO.cur);
    if (c) {
      const w = c.offsetWidth * PAN.s, h = c.offsetHeight * PAN.s;
      const mx = Math.max(0, ((w - innerWidth) / 2 / w) * 100), my = Math.max(0, ((h - innerHeight) / 2 / h) * 100);
      x = clamp(x, -mx, mx); y = clamp(y, -my, my);
    }
    PAN.x = x; PAN.y = y;
    PHL.style.setProperty("--px", x + "%"); PHL.style.setProperty("--py", y + "%");
  }
  function setPan(on) { PAN.on = on; PHL.classList.toggle("pan", on); $("#wk-pan").classList.toggle("on", on); panTo(0, 0); }
  $("#wk-pan").onclick = () => setPan(!PAN.on);
  PHL.addEventListener("pointerdown", (e) => {
    if (!PAN.on || e.button !== 0 || e.target.closest(".mpin")) return;
    const c = PHOTO.cur && $(".cover", PHOTO.cur); if (!c) return;
    e.preventDefault();
    PAN.drag = { x0: e.clientX, y0: e.clientY, px: PAN.x, py: PAN.y, w: c.offsetWidth * PAN.s, h: c.offsetHeight * PAN.s };
    PHL.classList.add("dragging");
  });
  window.addEventListener("pointermove", (e) => { const d = PAN.drag; if (d) panTo(d.px + ((e.clientX - d.x0) / d.w) * 100, d.py + ((e.clientY - d.y0) / d.h) * 100); });
  window.addEventListener("pointerup", () => { if (PAN.drag) { PAN.drag = null; PHL.classList.remove("dragging"); } });

  // keyplan on / off
  let kpOn = true;
  $("#wk-kp").onclick = () => { kpOn = !kpOn; $("#wk-kp").classList.toggle("on", kpOn); document.body.classList.toggle("kp-off", !kpOn); pinFit(); };

  // pins: built on the render's own layer, so they drift and pan with it; a pin that would sit under the copy, the list,
  // the buttons or the keyplan, or off screen, steps aside
  function walkPins(s) {
    const host = PHOTO.cur && $(".cover.pins", PHOTO.cur);
    if (!host || PHOTO.cur.dataset.src !== PHOTO.src(imgOf(s))) return;
    host.innerHTML = s.pins.map(([k, img, label, x, y, side]) =>
      `<span class="mpin ${k}${side === "l" ? " l" : ""}" style="left:${x}%;top:${y}%">` +
      `<i style="background-image:url(assets/img/${img}.webp)"></i><span>${label}</span></span>`).join("");
    $$(".mpin", host).forEach((m, i) => later(() => { m.classList.add("on"); pinFit(); }, i * 320));
  }
  function pinFit() {
    const host = PHOTO.cur && $(".cover.pins", PHOTO.cur);
    if (!host || !document.body.classList.contains("in-walk")) return;
    const W = innerWidth, Hh = innerHeight;
    const block = [".wk-name", ".wk-nav", ".walk-ctl"].map((q) => $(q, WK).getBoundingClientRect());
    if (kpOn && frames.mode === "dock") block.push(FA.getBoundingClientRect());
    $$(".mpin", host).forEach((m) => {
      const a = m.getBoundingClientRect(), b = $("span", m).getBoundingClientRect();
      const r = { l: Math.min(a.left, b.left), r: Math.max(a.right, b.right), t: Math.min(a.top, b.top), b: Math.max(a.bottom, b.bottom) };
      const out = r.l < 12 || r.r > W - 12 || r.t < 70 || r.b > Hh - 36 || block.some((q) => r.l < q.right && r.r > q.left && r.t < q.bottom && r.b > q.top);
      m.classList.toggle("off", out);
    });
  }
  window.addEventListener("resize", () => later(pinFit, 50));

  // the studio has no render yet: its plan diagram on the deck's green, no keyplan (Ritika)
  function walkStudio() {
    const svg = $("#wk-studio-svg"); if (!svg.children.length) drawStudio(svg);
  }

  // each space is its own slide (Ritika, 12.10): it opens on its key plan; → opens the render alone with its name (no laser or glow:
  // Ritika, 12.10); → brings everything on it. The SOC goes on to the building from outside (s-w-soc); the studio has no render: one beat
  const walkBeats = (s) => (s.studio ? ["studio"] : ["key", "bare", "full"]);
  // the boardroom's renders, meeting · presentation · dinner (Ritika, 12.10 / 14.10): its toggle picks one, the render the walk shows
  let brMode = "meet";
  const imgOf = (s) => (brMode === "meet" ? s.img : s[brMode] || s.img);
  function walkBare(on) { if (WK) WK.classList.toggle("bare", on); document.body.classList.toggle("wk-bare", on); }
  // the key plan: Option 01 around the space's camera, its dot and view cone; the render then zooms out of that dot (enterPhoto)
  function keyplanView(s) {
    const p = getPlanA(), c = Z.opt1.cameras[s.cam];
    p.setOption("opt1"); p.setLayers({ cams: true, furn: true, parts: true, zones: false, evo: false, labels: false, tiers: false, routes: [], events: null, sig: false, sat: false, hover: false });
    p.setOverlay([]); p.setNotes([]); p.setLinks([]); p.host.dataset.fac = ""; p.setCam(s.cam);
    frames("right"); world("plan"); shade("");
    p.fit([c.at[0] - 9000, c.at[1] - 6000, c.at[0] + 9000, c.at[1] + 6000], 900);
  }
  function walkStep(s, beat) {
    clearTimers();
    const p = getPlanA();
    walkBare(beat !== "full"); panTo(0, 0); p.highlight(null);
    document.body.classList.toggle("wk-key", beat === "key");
    if (beat === "key") { keyplanView(s); return; }
    if (beat === "studio") { enterPhoto("", null, "opt1", { kb: true }); walkStudio(); return; }
    const img = imgOf(s), first = world.cur !== "photo", fresh = first || !PHOTO.cur || PHOTO.cur.dataset.src !== PHOTO.src(img);
    enterPhoto(img, s.cam, "opt1", { kb: true, pins: true });
    if (AUD.want && AUD.el.paused) AUD.play();   // a render never opens silent, unless the music is muted
    if (beat === "bare") return;
    const t = first ? 1500 : fresh ? 650 : 150;
    later(() => walkPins(s), t);
    later(pinFit, t + 1400);
  }
  // Meeting / Presentation / Dinner: cross-fades to that render of the same view; its pins follow
  function brShow(mode) {
    const s = WALK.find((w) => w.id === "s-w-boardroom");
    brMode = mode;
    $$("#wk-br button").forEach((b) => b.classList.toggle("on", b.dataset.br === mode));
    if (world.cur !== "photo" || !WK || WK.id !== s.id) return;
    PHOTO.show(imgOf(s), { kb: true, pins: true });
    if (!WK.classList.contains("bare")) later(() => { walkPins(s); later(pinFit, 1400); }, 150);
  }
  $$("#wk-br button").forEach((b) => (b.onclick = (e) => { e.stopPropagation(); b.blur(); brShow(b.dataset.br); }));
  function walkHook(id) {
    const s = WALK.find((w) => w.id === id), beats = walkBeats(s);
    return {
      enter(_, sc) {
        WK = sc; WKUI.forEach((n) => sc.appendChild(n));
        document.body.classList.add("in-walk");
        // the index lists the walk's spaces in the deck, in their order; a space in the Appendix stands alone
        const deck = scenes.filter((x) => isWalk(x) && trackOf(x) === trackOf(sc)), at = deck.indexOf(sc), many = deck.length > 1;
        $("#wk-nav").innerHTML = many ? deck.map((x, i) => `<button type="button" data-to="${x.id}"${x === sc ? ' class="on"' : ""}><b>0${i + 1}</b>${x.dataset.title}</button>`).join("") : "";
        $$("#wk-nav button").forEach((b) => (b.onclick = () => go(sceneIx(b.dataset.to), 1)));
        $("#wk-ix").textContent = many ? `0${at + 1} / 0${deck.length}` : "";
        $("#wk-n").textContent = s.n; $("#wk-p").textContent = s.p;
        $(".wk-name .kicker", sc).textContent = `${chNum(sceneIx(sc.id))} · Visual direction · Layout Option 01`;
        sc.classList.toggle("is-studio", !!s.studio); sc.classList.toggle("is-soc", !!s.soc); sc.classList.toggle("is-board", !!s.dinner);
        if (s.dinner) { brMode = "meet"; $$("#wk-br button").forEach((b) => b.classList.toggle("on", b.dataset.br === "meet")); } document.body.classList.toggle("wk-studio", !!s.studio);
        AUD.play();
      },
      step(k) { walkStep(s, beats[k - 1]); },
      leave() {
        setPan(false); walkBare(false); document.body.classList.remove("wk-studio", "wk-key", "in-walk");
        const p = getPlanA(); p.highlight(null); p.setCam(null); p.setLayers({ zones: false }); p.setOption(state.opt);
        setTimeout(() => { if (!isWalk(scenes[state.idx])) AUD.stop(); }, 0);   // the music carries on from one space to the next
      },
    };
  }
  WALK.forEach((s) => (H[s.id] = walkHook(s.id)));
  // slide 16 (Ritika, 12.10): Inside the SOC — its key plan and render — then the building from outside: back to the site, and where
  // each option's SOC is seen (the beats of "The SOC, seen"). The walk's music fades while the model is on
  const SOC_IN = H["s-w-soc"], SOC_OUT = H["s-soc"];
  H["s-w-soc"] = {
    enter(_, sc) { SOC_IN.enter(_, sc); fillTicker(); },
    step(k) {
      const model = k > 3, sc = $("#s-w-soc"), was = sc.classList.contains("model");
      sc.classList.toggle("model", model);
      if (model) {
        if (!was) { AUD.stop(); setPan(false); walkBare(false); document.body.classList.remove("wk-key"); }
        SOC_OUT.step(k - 3);
        return;
      }
      if (was) { siteOff(); lightboxOff(); if (PHOTO.cur && k === 3) world("photo"); AUD.play(); }   // back inside: straight to the render
      SOC_IN.step(k);
    },
    leave() { $("#s-w-soc").classList.remove("model"); SOC_IN.leave(); SOC_OUT.leave(); },
  };

  /* ---- A · room mix and the studio ---- */
  H["s-rooms"] = {
    enter() {
      const host = $("#mix");
      if (!host.children.length) {
        const sizes = [2, 4, 5, 6, 8, 10, 14];
        const sq = (n, cls) => Array.from({ length: n || 0 }, () => `<i${cls ? ` class="${cls}"` : ""}></i>`).join("") || '<span class="mute">—</span>';
        host.innerHTML = sizes.map((s) => `<div class="mixrow"><span class="lab">${s} pax</span><span class="mixbar">${sq(MIX.opt1.mix[s])}</span><span class="mixbar">${sq(MIX.opt2.mix[s])}</span></div>`).join("") +
          `<div class="mixrow"><span class="lab">booths</span><span class="mixbar">${sq(MIX.opt1.pb, "rec")}</span><span class="mixbar">${sq(MIX.opt2.pb, "rec")}</span></div>` +
          `<div class="mixtotal"><span>Rooms</span><span class="green">${MIX.opt1.total} · low variety</span><span style="color:var(--amber)">${MIX.opt2.total} · 1–2 short</span></div>`;
        $("#mix-rec").innerHTML = REC.map(([s, n]) => `<div class="mixrow" style="grid-template-columns:90px 1fr"><span class="lab">${s === 16 ? "14–16 flex" : s === 12 ? "10–12 conf." : s + " pax"}</span><span class="mixbar">${sq(n)}</span></div>`).join("");
        const s1 = Math.round(areaOf("opt1", ["studio"])), s2 = Math.round(areaOf("opt2", ["studio"]));
        $("#studio-note").textContent = `Option 01's podcast room as drawn (3.2 × 5.5 m, ≈${sqft(s1)}): two cameras on a round set, a lounge chair and a curved sofa, in a box-in-box shell with an ON AIR signal by the door. Option 02's ≈${sqft(s2)} is tight — we'd grow it to ≈${sqft(20)}.`;
        drawStudio($("#studio-svg"));
      }
    },
    step(k) {
      const o = state.opt, p = layerPlan(o, { furn: true, parts: true, zones: true, hover: true });
      p.highlight(k === 1 ? "meet" : "studio"); layerScene(); frames("right", OPTNAME[o]);
      p.fit(k === 1 ? null : bboxOfType(o, "studio", 9000), 900);
    },
    opt() { this.step(state.step); },
    leave() { const p = getPlanA(); p.highlight(null); p.setLayers({ zones: false, hover: false }); frames("right"); },
  };

  /* ---- 11 kit of parts ---- */
  // [image, label, spans two rows?] per column, as on the slide
  const KIT = [
    ["Flooring.", [["mat-tile", "Tiles"], ["mat-carpet", "Carpet", true], ["mat-oak-chevron", "Wooden LVT"]]],
    ["Ceiling.", [["mat-gypsum", "Perforated gypsum"], ["mat-spray-acoustic", "Spray-applied treatment"], ["mat-metal-mesh", "Metal mesh"], ["mat-baffles", "Suspended acoustic"]]],
    ["Furnishing.", [["mat-acrylic", "Acrylics"], ["ex-lounge", "Blinds", true], ["mat-fabric", "Fabrics"]]],
    ["Wall finishes.", [["mat-acoustic-felt", "Acoustic panelling"], ["mat-stone-dark", "Wall paint"], ["mat-oak", "Wooden panel"], ["ex-cafe", "Graphics"]]],
  ];
  H["s-kit"] = {
    enter() {
      const g = $("#kit-cols");
      if (!g.children.length) g.innerHTML = KIT.map(([h, items]) => `<div class="kc"><h3>${h}</h3><div class="kc-tiles">${items.map(([f, n, tall]) =>
        `<figure${tall ? ' class="tall"' : ""} style="background-image:url(assets/img/${f}.webp)"><figcaption>${n}</figcaption></figure>`).join("")}</div></div>`).join("");
      LAYERS.plan.classList.remove("docked"); frames("right"); world("none"); shade("");
    },
  };
  H["s-acoustic"] = { enter() { LAYERS.plan.classList.remove("docked"); frames("right"); world("none"); shade(""); } };
  H["s-brand"] = { enter() { LAYERS.plan.classList.remove("docked"); frames("right"); world("none"); shade(""); } };
  // slide 28's pendant hangs just right of the kicker: on a narrow screen it moves over (and shrinks) so its cords never cross it
  function fitPendant() {
    const pd = $(".insp-pendant"), k = $("#s-inspire .insp-kicker"), tag = $("#s-inspire .insp-tag");
    pd.style.left = pd.style.width = "";
    const W = innerWidth, kr = k.getBoundingClientRect().right + 14, tl = tag.getBoundingClientRect().left - 8;
    const IN = 0.192, OUT = 0.836;   // the image's first and last visible cord, as a share of its width
    let w = 0.225 * W, left = Math.max(0.226 * W, kr - IN * w);
    if (left + OUT * w > tl) { w = Math.max(0.1 * W, (tl - kr) / (OUT - IN)); left = Math.max(0.226 * W, kr - IN * w); }
    pd.style.left = left + "px"; pd.style.width = w + "px";
  }
  window.addEventListener("resize", () => { if (document.body.dataset.scene === "s-inspire") fitPendant(); });
  // the Lantern: the SOC as the hero space (deck slide 34), right after the material palette (Ritika)
  H["s-inspire"] = {
    enter() {
      LAYERS.plan.classList.remove("docked"); frames("right"); world("none"); shade("");
      fitPendant();
      document.fonts.ready.then(() => { if (document.body.dataset.scene === "s-inspire") fitPendant(); });   // the kicker's width depends on Poppins
    },
  };
  H["s-kitmore"] = {
    enter() { LAYERS.plan.classList.remove("docked"); frames("right"); world("none", "plan"); shade("veil"); },
    step(k) { $("#kit-h").textContent = ["Light and sound, as one strategy.", "Technology you feel, not see."][k - 1]; },
  };

  /* ---- 12 future + next ---- */
  H["s-future"] = {
    enter() {
      LAYERS.plan.classList.remove("docked"); frames("full"); world("none", "plan"); shade("veil");
      $$("#s-future .story").forEach((s) => (s.onclick = () => go(sceneIx(s.dataset.goto), +s.dataset.to)));
      $("#to-appendix").onclick = () => go(trackIdx("appendix")[0], 1);
    },
  };

  /* ---- A · the next 5–7 years: hard zones once, the rest loose-fit ---- */
  H["s-flex"] = {
    render() {
      const o = state.opt, p = getPlanA();
      p.setOption(o); p.setOverlay([]); p.setNotes([]); p.setLinks([]); p.highlight(null); p.setCam(null);
      p.setLayers({ furn: false, parts: true, zones: false, labels: false, hard: true, sig: false, cams: false, tiers: false, circ: false, hover: true });
      const hard = areaOf(o, ["soc", "secure", "board", "studio"]), soft = areaOf(o, ["focus", "meet", "collab", "cafe", "quiet", "arrive", "service"]);
      $("#future-facts").innerHTML = `<div class="fact"><b>≈${sqft(hard)}</b><span>hard · ${Math.round((hard / (hard + soft)) * 100)}% of fit-out</span></div>
        <div class="fact"><b>≈${sqft(soft)}</b><span>soft · ${Math.round((soft / (hard + soft)) * 100)}% loose-fit</span></div>`;
      const desks = zonesOf(o, "focus").reduce((a, z) => a + (z.seats || 0), 0);   // workhall desks (SOC seats excluded)
      if (desks) $("#fut-desks").textContent = `the same ${desks} workhall desks support ≈${Math.round(desks * 1.2)} people`;
    },
    enter() { LAYERS.plan.classList.remove("docked"); frames("right", OPTNAME[state.opt]); world("plan"); shade("left"); this.render(); getPlanA().fit(null, 800); },
    opt() { this.render(); frames("right", OPTNAME[state.opt]); },
    leave() { getPlanA().setLayers({ hard: false, hover: false }); frames("right"); },
  };

  /* ---- A · the full scorecard ---- */
  H["s-score"] = {
    enter() { $("#scorecard").innerHTML = scorecard(); LAYERS.plan.classList.remove("docked"); frames("right"); world("plan"); shade("left"); $("#w-plan").style.filter = "blur(3px)"; },
    leave() { $("#w-plan").style.filter = ""; },
  };

  /* ---- A · event capacity: 50 / 100 / 200 on the plan ---- */
  const EVN = ["50", "100", "200"], EVNAME = { "50": "50 · workshop and training.", "100": "100 · panel and product launch.", "200": "200 · town hall." };
  function evDossier(o, lvl) {
    const ev = Z[o].events[lvl], target = +lvl;
    return `<div class="h"><span>${OPTNAME[o]}</span><span class="green">● ${lvl} people</span></div><p>${ev.where} · ${ev.how}</p><div class="kv"><span>Event footprint</span><b>${sqft(ev.area)}</b></div>` +
      `<div class="capbars">${DENS.map(([n, d]) => { const cap = Math.floor(ev.area / d), w = Math.min(100, (cap / (target * 2)) * 100); return `<div class="capbar"><span>${n} <small class="mute" style="white-space:nowrap">${sqft(d)}</small></span><span class="track"><i style="width:${w}%"></i><u style="left:50%"></u></span><b style="color:${cap >= target ? "var(--accent)" : "var(--amber)"}">${cap}</b></div>`; }).join("")}</div>` +
      `<div class="axo-inset"><img src="assets/img/axo-${o === "opt1" ? "o1" : "o2"}-${lvl}.webp" alt=""><span>From our concept deck · ${lvl}-person mode</span></div>`;
  }
  H["s-events"] = {
    enter() { LAYERS.plan.classList.remove("docked"); layerScene(); },
    step(k) {
      const o = state.opt, lvl = EVN[k - 1], ev = Z[o].events[lvl], p = layerPlan(o, { furn: true, parts: true, events: lvl });
      frames("right", OPTNAME[o]);
      $("#evx-h").textContent = EVNAME[lvl]; $("#evx-dossier").innerHTML = evDossier(o, lvl);
      p.fit(window.Plan2D.bboxOf(ev.polys || [ev.poly], 9000), 900);
    },
    opt() { this.step(state.step); },
    leave() { getPlanA().setLayers({ events: null }); frames("right"); },
  };

  /* ---- A · SOC operational zoning ---- */
  H["s-socops"] = {
    enter() {
      if (!$("#soc-zoning").children.length) $("#soc-zoning").innerHTML = [
        ["Command wall · curved, front", "In plan"], ["Analyst tiers L1 → L3 on a stepped floor", "Add"], ["Viewing edge for visitors", "In plan"],
        ["Shift-lead dais, centre-rear", "Add"], ["Incident-response room · 8 seats, direct door", "Add"], ["Secure airlock · card + biometric", "Add"], ["Night-shift recovery room", "Opt 01"],
      ].map(([a, b]) => `<span>${a}</span><b class="${b === "Add" ? "warn" : "ok"}">${b}</b>`).join("");
      this.opt();
    },
    opt() {
      const o = state.opt, p = layerPlan(o, { furn: true, parts: true, zones: true, socglass: true });
      p.highlight("soc"); layerScene(); frames("right", OPTNAME[o]);
      p.fit(bboxOfType(o, "soc", 3500), 900);
    },
    leave() { const p = getPlanA(); p.highlight(null); p.setLayers({ zones: false, socglass: false }); frames("right"); },
  };

  /* ---- A · what the building decided (due diligence, colour-coded) ---- */
  H["s-dd"] = {
    enter() {
      layerPlan("opt1"); layerScene();
      if (!$("#dd-list").children.length) $("#dd-list").innerHTML = DD.map((d) => legendRow(d.c, d.t, d.d, d.k)).join("");
      legendHover($("#dd-list"), (k) => drawDD(k));
      drawDD(null); getPlanA().fit(null, 800);
    },
    leave() { getPlanA().setOverlay([]); },
  };

  /* ======================= boot ======================= */
  const fromHash = () => {
    const m = (location.hash || "").match(/^#([\w-]+)\/(\d+)/);
    go(m ? Math.max(0, sceneIx(m[1])) : 0, m ? +m[2] : 1);
  };
  // a hash typed or linked moves the deck; the deck's own address updates (setStep) are where it already is: skipped
  window.addEventListener("hashchange", () => { if (location.hash !== "#" + scenes[state.idx].id + "/" + state.step) fromHash(); });
  fromHash();
  tick();
  window.MX = { go, setStep, setOpt, setTheme, state };
})();
