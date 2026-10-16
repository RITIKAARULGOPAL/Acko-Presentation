/* Plan2D.Measure — distances (chained) and areas on the plan, snapped to the CAD lines.
   The walls are the DXF's own lines at true scale (millimetres, y up, only shifted and flipped),
   so straight walls read to the millimetre. Shift keeps the line straight, Ctrl places a point freely. */
(function () {
  const D = window.MX_DATA, NS = "http://www.w3.org/2000/svg";
  const H = D.opt1.size[1], sy = (y) => H - y;
  const SNAP_PX = 12, CLICK_PX = 3;
  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  };
  const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);
  const nf = (v, d) => v.toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d });
  // 4.25 m · 13′ 11″ (to the nearest inch, so 11′ 11.7″ reads 12′ 0″)
  const ftIn = (mm) => { const i = Math.round(mm / 25.4), f = Math.floor(i / 12); return `${f}′ ${i - f * 12}″`; };
  const fmtLen = (mm) => `${nf(mm / 1000, 2)} m · ${ftIn(mm)}`;
  const fmtArea = (mm2) => window.Plan2D.sqft(mm2 / 1e6);     // the deck's areas are in sq ft
  const pathLen = (pts, close) => { let s = 0; for (let i = 1; i < pts.length; i++) s += dist(pts[i - 1], pts[i]); return close && pts.length > 2 ? s + dist(pts[pts.length - 1], pts[0]) : s; };
  const polyArea = (p) => { let a = 0; for (let i = 0; i < p.length; i++) { const [x1, y1] = p[i], [x2, y2] = p[(i + 1) % p.length]; a += x1 * y2 - x2 * y1; } return Math.abs(a / 2); };
  const rings = (d) => d.split("M").filter(Boolean).map((s) => { const n = s.match(/-?\d+(\.\d+)?/g).map(Number), r = []; for (let i = 0; i + 1 < n.length; i += 2) r.push([n[i], n[i + 1]]); return r; });
  /* the CAD room outlines round their corners in 1 mm steps: put the sharp corner back where the straight
     sides meet (a run of short steps under 60 mm is a fillet; anything longer, e.g. a curve, stays as drawn) */
  function sharpen(ring) {
    const r = ring.filter((p, i) => !i || dist(p, ring[i - 1]) > 0), n = r.length;
    if (n > 1 && !dist(r[0], r[n - 1])) r.pop();
    const m = r.length, len = (i) => dist(r[i], r[(i + 1) % m]), long = [];
    for (let i = 0; i < m; i++) if (len(i) >= 50) long.push(i);
    if (long.length < 2) return r;
    const out = [];
    long.forEach((k, j) => {
      const k2 = long[(j + 1) % long.length], a = r[k], b = r[(k + 1) % m], c = r[k2], e = r[(k2 + 1) % m];
      let run = 0; for (let i = (k + 1) % m; i !== k2; i = (i + 1) % m) run += len(i);
      const ux = b[0] - a[0], uy = b[1] - a[1], vx = e[0] - c[0], vy = e[1] - c[1], cr = ux * vy - uy * vx;
      if (run < 60 && Math.abs(cr) > 1e-3 * Math.hypot(ux, uy) * Math.hypot(vx, vy)) {
        const t = ((c[0] - a[0]) * vy - (c[1] - a[1]) * vx) / cr, p = [a[0] + ux * t, a[1] + uy * t];
        if (dist(p, b) < 100) { out.push(p); return; }
      }
      for (let i = (k + 1) % m; ; i = (i + 1) % m) { out.push(r[i]); if (i === k2) break; }
    });
    return out;
  }

  class Measure {
    constructor(plan) {
      this.p = plan; this.mode = null; this.items = []; this.cur = null; this.at = null; this.ev = null;
      this.read = plan.ctl.querySelector(".m-read");
      const svg = plan.svg;
      let down = null;
      svg.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY]; });
      svg.addEventListener("pointermove", (e) => {
        if (!this.mode) return;
        this.ev = e;
        if (!this._raf) this._raf = requestAnimationFrame(() => { this._raf = 0; this.track(); });
      });
      svg.addEventListener("pointerleave", () => { if (this.mode) { this.ev = null; this.at = null; this.render(); } });
      svg.addEventListener("click", (e) => {
        if (!this.mode || !down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) >= CLICK_PX) return;   // a pan, not a click
        e.stopPropagation(); this.ev = e; this.track(); this.add();
      });
      svg.addEventListener("dblclick", (e) => { if (this.mode) { e.stopPropagation(); this.finish(); } });
      svg.addEventListener("contextmenu", (e) => { if (this.mode) { e.preventDefault(); this.finish(); } });
      // Shift / Ctrl change the snap without moving the mouse
      const mod = (e) => { if (this.mode && this.ev && (e.key === "Shift" || e.key === "Control")) { this.ev = { clientX: this.ev.clientX, clientY: this.ev.clientY, shiftKey: e.shiftKey, ctrlKey: e.ctrlKey }; this.track(); } };
      window.addEventListener("keydown", mod); window.addEventListener("keyup", mod);
    }

    /* "dist" | "area" | null; off clears everything */
    setMode(m) {
      m = m || null;
      const p = this.p;
      if (m !== this.mode) {
        if (this.cur) this.finish();
        this.mode = m;
        if (!m) { this.items = []; this.cur = null; this.at = null; this.ev = null; }
      }
      p.host.classList.toggle("measuring", !!m); p.ctl.classList.toggle("measuring", !!m);
      p.ctl.querySelectorAll("[data-m]").forEach((b) => b.classList.toggle("on", b.dataset.m === m));
      if (m) {   // the room / team hover steps aside while measuring
        p.host.querySelectorAll(".g-hover .on, .g-hoverfloor .on").forEach((n) => n.classList.remove("on"));
        p.hvAt = null; p.hvEl = null; p.placeHover(); p.hideTip();
        if (p.onHover) p.onHover(null);
      }
      this.render();
      return !!m;
    }
    /* Esc: finish what is being drawn, else clear, else stop measuring */
    esc() {
      if (!this.mode) return false;
      if (this.cur) this.finish();
      else if (this.items.length) { this.items = []; this.render(); }
      else this.setMode(null);
      return true;
    }
    /* the plan was rebuilt (option switch): the walls differ, so start again */
    reset() { this.items = []; this.cur = null; this.at = null; this.segKey = null; this.g = null; this.render(); }

    /* ---------- snapping ---------- */
    // every visible CAD line as flat segments [ax, ay, bx, by, ...]: shell, columns, and with the layout shown
    // its partitions, glass, doors and the CAD room outlines (MI_ layer; their corners, where a partition stops short of a column)
    segs() {
      const p = this.p, L = p.L, d = D[p.opt], parts = L.parts !== false, key = p.opt + (L.walls ? "w" : "") + (parts ? "p" : "");
      if (this.segKey === key) return this._segs;
      const s = [];
      const add = (q, close) => {
        for (let i = 0; i + 3 < q.length; i += 2) s.push(q[i], q[i + 1], q[i + 2], q[i + 3]);
        if (close && q.length > 4) s.push(q[q.length - 2], q[q.length - 1], q[0], q[1]);
      };
      if (L.walls) {
        d.vec.shell.forEach((q) => add(q));
        d.fills.forEach((q) => add(q, true));
        if (parts) {
          [d.vec.partition, d.vec.glass, d.vec.door].forEach((l) => l.forEach((q) => add(q)));
          const hv = D.zones[p.opt].hover;
          (hv ? hv.rooms : []).forEach((rm) => rings(rm.d).forEach((g) => add(sharpen(g).flat(), true)));
        }
      }
      this._segs = new Float64Array(s); this.segKey = key;
      return this._segs;
    }
    world(e) {   // pointer -> data mm
      const r = this.p.svg.getBoundingClientRect(), [vx, vy, w, h] = this.p.vb;
      return [vx + ((e.clientX - r.left) / r.width) * w, sy(vy + ((e.clientY - r.top) / r.height) * h)];
    }
    snap(c, e) {
      const S = this.segs(), R = SNAP_PX * this.p.mmPerPx, pts = this.cur ? this.cur.pts : [], a = pts.length ? pts[pts.length - 1] : null;
      if (a && e.shiftKey) {
        // straight: along the plan's axes (the building's), then onto the wall that line crosses near the cursor
        const hor = Math.abs(c[0] - a[0]) >= Math.abs(c[1] - a[1]), q = hor ? [c[0], a[1]] : [a[0], c[1]];
        if (e.ctrlKey) return { pt: q, kind: "free" };
        const u = hor ? 1 : 0, v = 1 - u, k = a[u];   // u: the locked coordinate (y when horizontal)
        let best = null, bd = R;
        for (let i = 0; i < S.length; i += 4) {
          const p0 = S[i + u], p1 = S[i + 2 + u];
          if (p0 === p1 || (p0 - k) * (p1 - k) > 0) continue;
          const t = (k - p0) / (p1 - p0), x = S[i + v] + (S[i + 2 + v] - S[i + v]) * t, dd = Math.abs(x - q[v]);
          if (dd < bd) { bd = dd; best = hor ? [x, k] : [k, x]; }
        }
        return best ? { pt: best, kind: "edge" } : { pt: q, kind: "free" };
      }
      if (e.ctrlKey) return { pt: c, kind: "free" };
      if (this.mode === "area" && pts.length >= 3 && dist(c, pts[0]) < R) return { pt: pts[0], kind: "close" };
      // 1. a corner
      let best = null, bd = R;
      for (let i = 0; i < S.length; i += 2) {
        const dd = Math.hypot(S[i] - c[0], S[i + 1] - c[1]);
        if (dd < bd) { bd = dd; best = [S[i], S[i + 1]]; }
      }
      if (best) return { pt: best, kind: "vertex" };
      // 2. square off a wall from the last point (clear widths); 3. anywhere on a line
      let perp = null, pd = R, edge = null, ed = R;
      for (let i = 0; i < S.length; i += 4) {
        const ax = S[i], ay = S[i + 1], dx = S[i + 2] - ax, dy = S[i + 3] - ay, L2 = dx * dx + dy * dy;
        if (!L2) continue;
        if (Math.min(ax, ax + dx) - R > c[0] || Math.max(ax, ax + dx) + R < c[0] || Math.min(ay, ay + dy) - R > c[1] || Math.max(ay, ay + dy) + R < c[1]) continue;
        if (a && this.mode === "dist") {
          const t = ((a[0] - ax) * dx + (a[1] - ay) * dy) / L2;
          if (t >= 0 && t <= 1) { const f = [ax + dx * t, ay + dy * t], dd = dist(f, c); if (dd < pd && dist(f, a) > 1) { pd = dd; perp = f; } }
        }
        const t = Math.max(0, Math.min(1, ((c[0] - ax) * dx + (c[1] - ay) * dy) / L2)), f = [ax + dx * t, ay + dy * t], dd = dist(f, c);
        if (dd < ed) { ed = dd; edge = f; }
      }
      if (perp) return { pt: perp, kind: "perp" };
      if (edge) return { pt: edge, kind: "edge" };
      return { pt: c, kind: "free" };
    }

    /* ---------- drawing a measurement ---------- */
    track() {
      if (!this.mode || !this.ev || !this.p.vb || this.p.dragging) { this.at = null; this.render(); return; }
      this.at = this.snap(this.world(this.ev), this.ev);
      this.render();
    }
    add() {
      if (!this.at) return;
      const pt = this.at.pt;
      if (!this.cur) { this.cur = { kind: this.mode, pts: [pt] }; this.render(); return; }
      const pts = this.cur.pts;
      if (this.at.kind === "close") return this.finish();
      if (dist(pts[pts.length - 1], pt) < 1) return;          // the second click of a double-click
      pts.push(pt); this.render();
    }
    finish() {
      const c = this.cur; this.cur = null;
      if (c && c.pts.length >= (c.kind === "area" ? 3 : 2)) this.items.push(c);
      this.render();
    }

    /* ---------- render: everything in data mm, sized in screen px ---------- */
    render() {
      const p = this.p, svg = p.svg;
      if (!this.g || this.g.parentNode !== svg) this.g = el("g", { class: "g-measure" }, svg);
      else if (svg.lastChild !== this.g) svg.appendChild(this.g);
      const g = this.g; g.innerHTML = "";
      this.readout();
      if (!this.mode || !p.vb) return;
      const s = p.mmPerPx, fs = 11.5 * s;
      const live = this.cur ? { kind: this.cur.kind, pts: this.at && this.at.kind !== "close" ? this.cur.pts.concat([this.at.pt]) : this.cur.pts.slice(), live: true } : null;
      this.items.concat(live ? [live] : []).forEach((it) => (it.kind === "area" ? this.drawArea(g, it, s, fs) : this.drawDist(g, it, s, fs)));
      if (this.at && this.at.kind !== "free") this.drawSnap(g, this.at, s);
    }
    drawDist(g, it, s, fs) {
      const P = it.pts.map((q) => [q[0], sy(q[1])]);
      el("path", { class: "m-line" + (it.live ? " live" : ""), d: "M" + P.map((q) => q[0] + " " + q[1]).join("L"), "vector-effect": "non-scaling-stroke" }, g);
      P.forEach((q, i) => {
        // 45° ticks, as on a CAD dimension
        const o = P[i ? i - 1 : 1]; if (!o) return;
        const L = dist(o, q) || 1, ux = (q[0] - o[0]) / L, uy = (q[1] - o[1]) / L, k = 5 * s;
        el("line", { class: "m-tick", x1: q[0] - (ux - uy) * k, y1: q[1] - (uy + ux) * k, x2: q[0] + (ux - uy) * k, y2: q[1] + (uy + ux) * k, "vector-effect": "non-scaling-stroke" }, g);
      });
      for (let i = 1; i < P.length; i++) {
        const a = P[i - 1], b = P[i], L = dist(a, b);
        if (L < 2 * s) continue;
        let ang = Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI;
        if (ang > 90) ang -= 180; else if (ang <= -90) ang += 180;   // read it left to right
        const r = ang * Math.PI / 180, off = 5 * s, mx = (a[0] + b[0]) / 2 + Math.sin(r) * off, my = (a[1] + b[1]) / 2 - Math.cos(r) * off;
        // the length sits beside its line, never on it
        const t = el("text", { class: "m-lbl", x: mx, y: my, "font-size": fs, "text-anchor": "middle", transform: `rotate(${ang} ${mx} ${my})` }, g);
        t.textContent = fmtLen(dist(it.pts[i - 1], it.pts[i]));
      }
    }
    drawArea(g, it, s, fs) {
      const P = it.pts.map((q) => [q[0], sy(q[1])]);
      el("path", { class: "m-area" + (it.live ? " live" : ""), d: "M" + P.map((q) => q[0] + " " + q[1]).join("L") + (P.length > 2 ? "Z" : ""), "vector-effect": "non-scaling-stroke" }, g);
      if (it.pts.length < 3) return;
      // the area sits just outside the shape: above it, or below when there's no room above
      const xs = P.map((q) => q[0]), ys = P.map((q) => q[1]), [, vy, , vh] = this.p.vb, gap = 8 * s;
      const cx = (Math.min(...xs) + Math.max(...xs)) / 2, top = Math.min(...ys), bot = Math.max(...ys);
      const above = top - gap - fs > vy, t = el("text", { class: "m-lbl", x: cx, y: above ? top - gap : Math.min(bot + gap + fs, vy + vh - gap), "font-size": fs, "text-anchor": "middle" }, g);
      t.textContent = fmtArea(polyArea(it.pts));
    }
    drawSnap(g, at, s) {
      const [x, y] = [at.pt[0], sy(at.pt[1])], k = 5 * s, ns = { "vector-effect": "non-scaling-stroke" };
      if (at.kind === "vertex" || at.kind === "close") el("rect", Object.assign({ class: "m-snap" + (at.kind === "close" ? " fill" : ""), x: x - k, y: y - k, width: 2 * k, height: 2 * k }, ns), g);
      else if (at.kind === "perp") el("path", Object.assign({ class: "m-snap", d: `M${x - k} ${y + k}H${x + k}M${x} ${y + k}V${y - k}` }, ns), g);
      else el("path", Object.assign({ class: "m-snap", d: `M${x} ${y - k}L${x + k} ${y}L${x} ${y + k}L${x - k} ${y}Z` }, ns), g);
    }
    /* the toolbar reads the measurement being drawn, else the last one */
    readout() {
      if (!this.read) return;
      if (!this.mode) { this.read.textContent = ""; return; }
      const it = this.cur ? { kind: this.cur.kind, pts: this.at && this.at.kind !== "close" ? this.cur.pts.concat([this.at.pt]) : this.cur.pts } : this.items[this.items.length - 1];
      let txt;
      if (!it || it.kind !== this.mode) txt = this.mode === "area" ? "Click round a space · Shift straight · Ctrl free" : "Click two points · Shift straight · Ctrl free";
      else if (it.kind === "area") txt = it.pts.length < 3 ? "Click round a space" : `${fmtArea(polyArea(it.pts))} · perimeter ${nf(pathLen(it.pts, true) / 1000, 2)} m`;
      else {
        const n = it.pts.length;
        txt = n < 2 ? "Click the next point" : fmtLen(dist(it.pts[n - 2], it.pts[n - 1])) + (n > 2 ? ` · total ${fmtLen(pathLen(it.pts))}` : "");
      }
      this.read.textContent = txt;
    }
  }

  Measure.fmtLen = fmtLen; Measure.fmtArea = fmtArea;
  window.Plan2D.Measure = Measure;
})();
