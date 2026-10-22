/* Shared engine for the engagement-points comparison pages (index-engage.html, index-engage-groups.html):
   the seven photos, the slide's text, the PPT collage, and the shell: options, beats, keys, lightbox, full screen.
   A page builds its views' generated parts first, then calls ENGAGE.start(V) with one entry per view:
   { n: beats, cap: the bar's caption, hook(k, view)?: called on every beat (k = 0 while a view is cleared) }. */
window.ENGAGE = (() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const IMG = (k) => `engage/img/eng-${k}.webp`;
  const esc = (s) => s.replace(/&/g, "&amp;");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // the seven points, in the PPT's reading order; pos is the crop used wherever a tile is not the PPT's own
  const P = {
    g: { label: "Mood Check-In", pos: "40% 50%" },
    d: { label: "Pause & Play", pos: "50% 38%" },
    f: { label: "Happy conversations", pos: "30% 30%" },
    a: { label: "Interactive Gaming", pos: "62% 55%" },
    b: { label: "Come nerd it out", pos: "50% 42%" },
    e: { label: "To Express out", pos: "45% 45%" },
    c: { label: "For the frustrated Ackers", pos: "56% 40%" },   // keeps "PUBLIC PUNCHING BAG" in narrow tiles
  };
  const ORDER = ["g", "d", "f", "a", "b", "e", "c"];

  // the slide's text, as in the PPT
  const TEXT = {
    loop: `<img src="engage/img/acko-ink.webp" alt="ACKO"><span>Loop , where Emotions Matter!</span>`,
    tag: "Designed for Interaction. Built for Engagement.",
    body: "From <b>conversation and connection</b> to <b>games, self-expression and opportunities to pause or unwind</b>, these elements make the workplace feel more human and approachable. The interventions also add a sense of <b>discovery and personality</b>, creating spaces where employees can interact, recharge and have moments of fun throughout the day.",
    note: "Acker’s engagement points explore how the workplace can go beyond functionality to create moments of interaction, play and emotional engagement.",
  };

  /* ---------- the PPT collage (deck slide 46) ---------- */
  // tiles: [point, left top width height (% of the page), background-size, background-position], the crops of slides/s-engage.html
  const TILES = [
    ["a", "34.2 51.6 13.2 20.5", "106.6% 183.5%", "100% 53.2%"],
    ["b", "47.9 51.6 11.1 20.5", "100% 128%", "0% 100%"],
    ["c", "69.8 45.7 9.1 26.3", "146.8% 120.3%", "65.5% 18.3%"],
    ["d", "69.8 22 9.1 22.8", "100% 100%", "0% 0%"],
    ["e", "59.4 22 9.9 50.1", "160.8% 100%", "43.9% 0%"],
    ["f", "79.4 22 18.9 27.6", "117.9% 167.8%", "0% 22.8%"],
    ["g", "47.9 34.1 11.1 16.5", "100% 221.7%", "0% 46.4%"],
  ];
  // labels where the PPT has them (% of the page), and the arrows photo → label, as hand-drawn there (1920×1080 page units)
  const LABELS = [
    ["g", 45.1, 15.6, "M931 362 C910 318 914 262 958 234"],
    ["d", 63.8, 12.9, "M1410 238 C1420 206 1404 182 1376 170"],
    ["f", 84.8, 12.9, "M1580 238 C1556 206 1582 184 1660 190"],
    ["a", 35.4, 77.4, "M740 790 C734 806 746 818 741 832"],
    ["b", 47.2, 83, "M1026 790 C1030 840 1082 850 1067 826 C1052 802 1016 846 1022 890"],
    ["e", 66.5, 75.8, "M1200 790 C1196 826 1222 836 1264 834"],
    ["c", 77, 81.2, "M1450 790 C1478 812 1494 838 1487 866"],
  ];
  // the collage into a view: tiles from beat `beat`, arrows and labels from `drawBeat`; every part carries data-k (its point)
  function collage(sec, { beat = 1, drawBeat = 2 } = {}) {
    const id = sec.dataset.v;
    sec.insertAdjacentHTML("afterbegin", TILES.map(([k, box, size, pos], i) => {
      const [l, t, w, h] = box.split(" ");
      return `<div class="ph b" data-b="${beat}" data-p="${k}" data-k="${k}" style="--i:${i};left:${l}%;top:${t}%;width:${w}%;height:${h}%;` +
        `background-size:${size};background-position:${pos};background-image:url(${IMG(k)})"></div>`;
    }).join(""));
    sec.insertAdjacentHTML("beforeend",
      `<svg class="arrows" data-b="${drawBeat}" viewBox="0 0 1920 1080" aria-hidden="true">` +
      `<marker id="ah${id}" viewBox="-12 -8 14 16" refX="0" refY="0" markerWidth="14" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto">` +
      `<path d="M-10 -6 L0 0 L-10 6" fill="none" stroke="#8d8d8d" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></marker>` +
      LABELS.map(([k, , , d], i) =>
        `<mask id="am${id}-${i}" maskUnits="userSpaceOnUse" x="-20" y="-20" width="1960" height="1120"><path class="mk" pathLength="1" style="--i:${i}" d="${d}"/></mask>` +
        `<path class="vis" data-k="${k}" mask="url(#am${id}-${i})" marker-end="url(#ah${id})" d="${d}"/>`).join("") +
      `</svg>` +
      LABELS.map(([k, l, t], i) => `<div class="hand c-lab" data-b="${drawBeat}" data-k="${k}" style="--i:${i};left:${l}%;top:${t}%">${esc(P[k].label)}</div>`).join(""));
  }

  /* ---------- the shell ---------- */
  function start(V, { first = 1 } = {}) {
    $$("[data-t]").forEach((el) => { el.innerHTML = TEXT[el.dataset.t]; });
    // every tile that does not carry the PPT's own crop gets its photo and crop from the table
    $$(".ph[data-p]").forEach((el) => {
      const k = el.dataset.p;
      if (!el.style.backgroundImage) { el.style.backgroundImage = `url(${IMG(k)})`; el.style.backgroundPosition = el.dataset.pos || P[k].pos; }
      el.title = P[k].label;
    });
    const page = $("#page"), views = $$(".view", page), pills = $$("#pills button"), beatEl = $("#beat"), capEl = $("#cap");
    if ($("#kmax")) $("#kmax").textContent = V.length - 1;
    let v = first, k = 1;

    function apply() {
      const view = views[v];
      $$("[data-b]", view).forEach((el) => el.classList.toggle("on", k >= +el.dataset.b));
      if (V[v].hook) V[v].hook(k, view);
      beatEl.textContent = `${Math.max(k, 1)} / ${V[v].n}`;
    }
    function show(nv, at = 1) {
      v = nv;
      views.forEach((el, i) => el.classList.toggle("cur", i === v));
      page.dataset.v = v;
      pills.forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.v === v)));
      capEl.textContent = V[v].cap;
      history.replaceState(null, "", "#" + v);
      // clear the view, let the browser take in its cleared state, then play it in: the beats' transitions run from there
      k = 0; apply(); void page.offsetWidth;
      k = at; apply();
    }
    const go = (nk) => { k = Math.max(1, Math.min(V[v].n, nk)); apply(); };
    const next = () => { if (k < V[v].n) go(k + 1); else if (v < V.length - 1) show(v + 1); };
    const prev = () => { if (k > 1) go(k - 1); else if (v > 0) show(v - 1, V[v - 1].n); };
    const replay = () => show(v);

    const lb = $("#lb");
    const openLB = (key) => { $("img", lb).src = IMG(key); $(".hand", lb).textContent = P[key].label; lb.classList.add("on"); };
    lb.addEventListener("click", () => lb.classList.remove("on"));

    // a click on the slide: data-go jumps to that beat, a photo opens large, anything else moves the beat on
    page.addEventListener("click", (e) => {
      const to = e.target.closest("[data-go]");
      if (to) { go(+to.dataset.go); return; }
      const ph = e.target.closest("[data-lb],[data-p]");
      if (ph && (ph.dataset.lb || ph.dataset.p)) { openLB(ph.dataset.lb || ph.dataset.p); return; }
      next();
    });
    pills.forEach((b) => b.addEventListener("click", () => { show(+b.dataset.v); b.blur(); }));
    $("#next").addEventListener("click", (e) => { next(); e.currentTarget.blur(); });
    $("#prev").addEventListener("click", (e) => { prev(); e.currentTarget.blur(); });
    $("#replay").addEventListener("click", (e) => { replay(); e.currentTarget.blur(); });

    const toggleFS = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.());
    addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (lb.classList.contains("on")) { if (["Escape", " ", "Enter"].includes(e.key)) { e.preventDefault(); lb.classList.remove("on"); } return; }
      if (/^[0-9]$/.test(e.key) && +e.key < V.length) show(+e.key);
      else if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(e.key)) { e.preventDefault(); next(); }
      else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(e.key)) { e.preventDefault(); prev(); }
      else if (e.key === "r" || e.key === "R") replay();
      else if (e.key === "f" || e.key === "F") toggleFS();
    });

    // the page fits the window under the bar (none in full screen)
    const bar = $("#bar");
    const fit = () => document.body.style.setProperty("--bar", (document.body.classList.contains("fs") ? 0 : bar.offsetHeight) + "px");
    document.addEventListener("fullscreenchange", () => { document.body.classList.toggle("fs", !!document.fullscreenElement); fit(); });
    new ResizeObserver(fit).observe(bar);
    fit();

    const h = parseInt(location.hash.slice(1), 10);
    show(h >= 0 && h < V.length ? h : first);
    return { get v() { return v; }, get k() { return k; }, go };
  }

  return { $, $$, IMG, esc, P, ORDER, TEXT, reduced, collage, start };
})();
