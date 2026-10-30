/* plan-hover.js - interactive floor plan with room and team hovers.
 *
 *   <link rel="stylesheet" href="assets/css/plan-hover.css">
 *   <script src="data/plan-hover-data.js"></script>      (window.PLAN_HOVER, built from the DXFs)
 *   <script src="assets/js/plan-hover.js"></script>
 *
 *   const plan = PlanHover.mount(document.getElementById("plan"), { option: "op1" });
 *   plan.setOption("op2");  plan.fit();  plan.destroy();
 *
 * Works from file:// (no fetch). No dependencies. See INTEGRATION.md.
 */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";

  const DEFAULTS = {
    option: null,           // a key of PLAN_HOVER.options (from project.json); default: the first plan
    data: null,             // defaults to window.PLAN_HOVER
    rooms: true,            // room hovers
    teams: true,            // team hovers (workstation seats, by team)
    interactive: true,      // wheel zoom, drag pan, double-click to fit
    labels: true,           // name label on hover
    labelPlacement: "centre", // "centre": on the hovered room / team; "above": just above it (below if no room), clear of it
    onHover: null,          // callback({ kind: "room"|"team", item }) / callback(null)
  };

  function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }
  function fmt(n, d = 1) { return Number(n).toLocaleString(undefined, { maximumFractionDigits: d }); }

  // The plan SVG writes every repeated block once (<defs>) and places it with <use>. Browsers ignore
  // vector-effect:non-scaling-stroke inside <use>, so each <use> is expanded into a plain <g> copy:
  // the file stays small and lines stay crisp at every zoom.
  function inflate(svg) {
    const defs = new Map([...svg.querySelectorAll("defs > g[id]")].map(g => [g.id, g]));
    svg.querySelectorAll("use").forEach(u => {
      const src = defs.get((u.getAttribute("href") || "").slice(1));
      const g = document.createElementNS(NS, "g");
      g.setAttribute("transform", u.getAttribute("transform"));
      if (src) for (const ch of src.children) g.appendChild(ch.cloneNode(true));
      u.replaceWith(g);
    });
    svg.querySelector("defs")?.remove();
    svg.querySelector("style")?.remove();
    svg.removeAttribute("class");
    svg.classList.add("ph-plan");
  }

  function mount(el, options) {
    const o = Object.assign({}, DEFAULTS, options || {});
    const data = o.data || window.PLAN_HOVER;
    if (!data || !data.options) throw new Error("PlanHover: PLAN_HOVER data not loaded (include data/plan-hover-data.js first)");

    el.classList.add("ph-root");
    el.innerHTML = '<div class="ph-stage"></div><div class="ph-label" aria-live="polite"></div>';
    const stage = el.querySelector(".ph-stage");
    const label = el.querySelector(".ph-label");
    let vb, home, maxW = Infinity, svgs = [], current = null, labelAt = null, labelEl = null, drag = null;
    const extras = [];                      // layers added with addLayer(): kept across setOption()

    function load(key) {
      const opt = data.options[key];
      if (!opt) throw new Error("PlanHover: unknown option " + key);
      current = key;
      const rooms = o.rooms ? opt.rooms.map(s => `<path class="ph-room" data-id="${s.id}" d="${s.d}"/>`).join("") : "";
      const teams = o.teams ? opt.teams.map(t =>
        `<g class="ph-team" data-id="${t.id}"><path class="ph-zone" d="${t.zone}"/><path class="ph-seats" d="${t.desks.join("")}"/></g>`).join("") : "";
      stage.innerHTML = opt.svg +
        `<svg xmlns="${NS}" class="ph-layer ph-rooms" viewBox="${opt.viewBox}">${rooms}</svg>` +
        `<svg xmlns="${NS}" class="ph-layer ph-teams" viewBox="${opt.viewBox}">${teams}</svg>`;
      svgs = [...stage.querySelectorAll(":scope > svg")];
      inflate(svgs[0]);
      for (const x of extras) placeExtra(x, opt.viewBox);
      svgs.forEach(s => s.setAttribute("preserveAspectRatio", "xMidYMid meet"));
      home = opt.viewBox.split(/\s+/).map(Number);
      vb = home.slice();
      hideLabel(); apply();
      wire(opt);
    }

    function apply() {
      const s = vb.join(" ");
      svgs.forEach(x => x.setAttribute("viewBox", s));
      placeLabel();
    }
    function scale() {
      const r = stage.getBoundingClientRect();
      return Math.max(vb[2] / r.width, vb[3] / r.height);
    }
    function toPlan(cx, cy) {
      const r = stage.getBoundingClientRect(), k = scale();
      return [vb[0] + vb[2] / 2 - (r.width * k) / 2 + (cx - r.left) * k, vb[1] + vb[3] / 2 - (r.height * k) / 2 + (cy - r.top) * k];
    }
    function toScreen(x, y) {
      const r = stage.getBoundingClientRect(), k = scale();
      return [(x - (vb[0] + vb[2] / 2 - (r.width * k) / 2)) / k, (y - (vb[1] + vb[3] / 2 - (r.height * k) / 2)) / k];
    }

    function placeLabel() {
      if (!labelAt) { label.style.display = "none"; return; }
      label.style.display = "block";
      if (o.labelPlacement === "above" && labelEl) {
        // above the hovered shape's on-screen box, centred on it; below it when there is no room above
        const st = stage.getBoundingClientRect(), r = labelEl.getBoundingClientRect(), w = label.offsetWidth, h = label.offsetHeight, gap = 8;
        const x = Math.max(w / 2 + 4, Math.min(st.width - w / 2 - 4, r.left + r.width / 2 - st.left));
        const below = r.top - st.top - gap - h < 0;
        label.classList.toggle("ph-above", !below); label.classList.toggle("ph-below", below);
        label.style.left = x + "px"; label.style.top = (below ? r.bottom - st.top + gap : r.top - st.top - gap) + "px";
        return;
      }
      label.classList.remove("ph-above", "ph-below");
      const [x, y] = toScreen(labelAt[0], labelAt[1]);
      label.style.left = x + "px"; label.style.top = y + "px";
    }
    function showLabel(x, y, title, sub, el) {
      if (!o.labels) return;
      label.innerHTML = `<b>${esc(title)}</b><span>${esc(sub)}</span>`;
      labelAt = [x, y]; labelEl = el || null; placeLabel();
    }
    function hideLabel() { labelAt = null; labelEl = null; placeLabel(); }

    function wire(opt) {
      const rooms = new Map(opt.rooms.map(s => [s.id, s]));
      const teams = new Map(opt.teams.map(t => [t.id, t]));
      const roomLayer = stage.querySelector(".ph-rooms"), teamLayer = stage.querySelector(".ph-teams");
      roomLayer.addEventListener("pointerover", e => {
        const s = rooms.get(e.target.dataset.id);
        if (!s || drag) return;
        e.target.classList.add("ph-on");
        showLabel(s.x, s.y, s.name || "Space", `${fmt(s.m2)} m²`, e.target);
        o.onHover && o.onHover({ kind: "room", item: s });
      });
      roomLayer.addEventListener("pointerout", e => {
        if (!rooms.has(e.target.dataset.id)) return;
        e.target.classList.remove("ph-on"); hideLabel(); o.onHover && o.onHover(null);
      });
      teamLayer.addEventListener("pointerover", e => {
        const g = e.target.closest(".ph-team"), t = g && teams.get(g.dataset.id);
        if (!t || drag) return;
        g.classList.add("ph-on");
        const pax = t.pax != null ? `${t.pax} PAX · ` : "";
        const hot = t.hot_desks ? ` (incl. ${t.hot_desks} hot desk)` : "";
        showLabel(t.x, t.y, t.name, `${pax}${t.seats} seats${hot}`, g.querySelector(".ph-seats") || g);
        o.onHover && o.onHover({ kind: "team", item: t });
      });
      teamLayer.addEventListener("pointerout", e => {
        const g = e.target.closest(".ph-team");
        if (g) { g.classList.remove("ph-on"); hideLabel(); o.onHover && o.onHover(null); }
      });
    }

    // ---- pan / zoom ----
    const onWheel = e => {
      e.preventDefault();
      const f = Math.min(Math.exp(e.deltaY * 0.0015), maxW / vb[2]), [px, py] = toPlan(e.clientX, e.clientY);   // no wider than maxW
      vb = [px - (px - vb[0]) * f, py - (py - vb[1]) * f, vb[2] * f, vb[3] * f]; apply();
    };
    const onDown = e => { drag = [e.clientX, e.clientY, false]; stage.setPointerCapture(e.pointerId); };
    const onMove = e => {
      if (!drag) return;
      const dx = e.clientX - drag[0], dy = e.clientY - drag[1];
      if (!drag[2] && Math.hypot(dx, dy) < 3) return;        // a click, not a drag yet
      if (!drag[2]) { drag[2] = true; el.classList.add("ph-dragging"); hideLabel(); }
      const k = scale(); vb[0] -= dx * k; vb[1] -= dy * k; drag[0] = e.clientX; drag[1] = e.clientY; apply();
    };
    const onUp = () => { drag = null; el.classList.remove("ph-dragging"); };
    const onDbl = () => fit();
    const onResize = () => vb && apply();
    if (o.interactive) {
      stage.addEventListener("wheel", onWheel, { passive: false });
      stage.addEventListener("pointerdown", onDown);
      stage.addEventListener("pointermove", onMove);
      stage.addEventListener("pointerup", onUp);
      stage.addEventListener("pointercancel", onUp);
      stage.addEventListener("dblclick", onDbl);
    }
    window.addEventListener("resize", onResize);

    function fit() { vb = home.slice(); apply(); }
    function zoomTo(x, y, w, h) { vb = [x, y, w, h]; apply(); }

    // ---- extra layers (e.g. coloured rooms beneath the plan, annotations above it); they follow the view ----
    function placeExtra(x, viewBox) {
      x.svg.setAttribute("viewBox", viewBox);
      x.svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      if (x.below) stage.insertBefore(x.svg, stage.firstChild); else stage.appendChild(x.svg);
      if (!svgs.includes(x.svg)) svgs.push(x.svg);
    }
    function addLayer(cls, inner, opts) {
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("class", "ph-layer ph-extra " + (cls || ""));
      svg.innerHTML = inner || "";
      const x = { svg, below: !!(opts && opts.below) };
      extras.push(x); placeExtra(x, data.options[current].viewBox); apply();
      return svg;
    }
    // ---- programmatic hover, e.g. from a legend row ----
    function clearOn() { stage.querySelectorAll(".ph-on").forEach((e) => e.classList.remove("ph-on")); hideLabel(); }
    function highlight(kind, id) {
      clearOn();
      const opt = data.options[current];
      if (kind === "team") {
        const g = stage.querySelector(`.ph-team[data-id="${id}"]`), t = opt.teams.find((q) => q.id === id);
        if (!g || !t) return;
        g.classList.add("ph-on");
        showLabel(t.x, t.y, t.name, `${t.pax != null ? t.pax + " PAX · " : ""}${t.seats} seats`, g.querySelector(".ph-seats") || g);
      } else {
        const p = stage.querySelector(`.ph-room[data-id="${id}"]`), r = opt.rooms.find((q) => q.id === id);
        if (!p || !r) return;
        p.classList.add("ph-on"); showLabel(r.x, r.y, r.name || "Space", `${fmt(r.m2)} m²`, p);
      }
    }

    load(o.option || Object.keys(data.options)[0]);
    return {
      el,
      get option() { return current; },
      setOption: key => load(key),
      fit,
      zoomTo,                                   // plan units are mm in the SVG frame
      get view() { return vb.slice(); },        // the current viewBox [x, y, w, h]
      setHome(x, y, w, h) { home = [x, y, w, h]; },   // where fit() and a double-click return to
      setMaxWidth(w) { maxW = w || Infinity; },        // the widest view (plan mm) the wheel zooms out to
      addLayer,                                 // addLayer(cls, svgInner, { below }) -> the layer's <svg>
      highlight,                                // highlight("room"|"team", id): as if hovered
      clear: clearOn,
      teams: () => data.options[current].teams.map(({ desks, zone, ...t }) => t),
      rooms: () => data.options[current].rooms.map(({ d, ...s }) => s),
      destroy() {
        window.removeEventListener("resize", onResize);
        el.innerHTML = ""; el.classList.remove("ph-root", "ph-dragging");
      },
    };
  }

  window.PlanHover = { mount, version: "1.2" };
})();
