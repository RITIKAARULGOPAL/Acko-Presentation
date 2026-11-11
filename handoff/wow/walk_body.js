/* walk the Loop (9 Nov, the re-ordered deck): after the Employees Journey the camera leaves the strategy's axo, sinks to eye level and
   walks the Loop on the furnished model (the SketchUp model, people as on A day in ACKO), stop by stop, a click each: Arrival, Café,
   Board Room, Meeting Rooms, Collab, Work, Wellness, along ACKO_LOOP's path (the employees' route through the stops, PLAN_DXF mm);
   on the long legs it lifts and flies low over the floor. The last click rises straight up until it looks down on the plan, where the
   Layout's Spaces plan takes over (ACKO_MORPH, _flatten). It opens on the strategy's last frame (its _snap), cross-fading into this
   model from the same angle (a far, narrow perspective standing in for the strategy's orthographic view). */
ACKO.slide("s-walk", ({ $, $$, plain, reveal, later, reduced, asset, plan, cue }) => {
  const STOPS = [["Arrival", "I feel welcomed"], ["Café", "Hey, we finally meet!"], ["Board Room", "This is my big moment"], ["Meeting Rooms", "My impact"],
    ["Collab", "Wow, worth the commute"], ["Work", "These are my folks!"], ["Wellness", "They thought of me too!"]];
  /*@PEOPLE@*/
  const SKP = !!(window.AxoSkp && window.AxoSkp.available());
  /*@INRING@*/
  const S = { raf: 0, k: 0, cur: null, anim: null, built: false, flat: false, asp: 16 / 9 };
  let T, M, W, group, crowd, walkers = [], cam, r, host, sc, CV = null;
  const KEEP_H = 1.65, LOOK_Y = 1.2, FOV = 62;
  const GREY = 0x4a4a4a;                                // the people's grey (as on A day in ACKO)
  /*@PEOPLECODE@*/

  // ---------- the Loop on this model: ACKO_LOOP.path in world metres, every 0.5 m, smoothed over about 4 m; each stop's place on it
  function curve() {
    if (CV) return CV;
    const LP = window.ACKO_LOOP, raw = LP.path.map(([x, y]) => [M.X(x), M.Z(y)]);
    const ss = [0]; for (let i = 1; i < raw.length; i++) ss.push(ss[i - 1] + Math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]));
    const L = ss[ss.length - 1], n = Math.ceil(L / 0.5), P = []; let j = 0;
    for (let k = 0; k <= n; k++) { const s = (k / n) * L; while (j < ss.length - 2 && ss[j + 1] < s) j++; const f = ss[j + 1] > ss[j] ? (s - ss[j]) / (ss[j + 1] - ss[j]) : 0; P.push([raw[j][0] + (raw[j + 1][0] - raw[j][0]) * f, raw[j][1] + (raw[j + 1][1] - raw[j][1]) * f]); }
    const Q = P.map((p, i) => { const a = Math.max(0, i - 4), b = Math.min(P.length - 1, i + 4); let x = 0, z = 0; for (let q = a; q <= b; q++) { x += P[q][0]; z += P[q][1]; } return [x / (b - a + 1), z / (b - a + 1)]; });
    const cs = [0]; for (let i = 1; i < Q.length; i++) cs.push(cs[i - 1] + Math.hypot(Q[i][0] - Q[i - 1][0], Q[i][1] - Q[i - 1][1]));
    const stopS = LP.stops.map((o) => { const t = [M.X(LP.path[o.i][0]), M.Z(LP.path[o.i][1])]; let bi = 0, bd = 1e9; Q.forEach((q, i) => { const d = Math.hypot(q[0] - t[0], q[1] - t[1]); if (d < bd) { bd = d; bi = i; } }); return cs[bi]; });
    return (CV = { Q, cs, L: cs[cs.length - 1], stopS });
  }
  function pt(s) {
    const { Q, cs, L } = CV; s = Math.max(0, Math.min(L, s));
    let a = 0, b = cs.length - 1; while (b - a > 1) { const m = (a + b) >> 1; if (cs[m] < s) a = m; else b = m; }
    const f = cs[b] > cs[a] ? (s - cs[a]) / (cs[b] - cs[a]) : 0; return [Q[a][0] + (Q[b][0] - Q[a][0]) * f, Q[a][1] + (Q[b][1] - Q[a][1]) * f];
  }
  // ---------- a view: where it looks (tgt), from which way (dir, unit, target to eye), how far (dist), how much it sees (h: half the
  // height seen at the target, m); its field of view follows (2·atan(h / dist)), so a far, narrow view and a near, wide one ease into each other
  const norm = (v) => { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; };
  const fromEye = (c, tg, fov) => { const d = [c[0] - tg[0], c[1] - tg[1], c[2] - tg[2]], dist = Math.hypot(...d); return { tgt: tg, dir: norm(d), dist, h: dist * Math.tan((fov * Math.PI) / 360) }; };
  function eyeAt(s, lift) {                                // on the Loop at s, lift m above eye height, looking ahead along it (and down, when lifted)
    const o = pt(s), u = norm([pt(s + 1)[0] - pt(s - 1)[0], 0, pt(s + 1)[1] - pt(s - 1)[1]]);
    const p = [o[0] - u[0] * 3.5, o[1] - u[2] * 3.5], la = 7 + lift * 1.3, q = pt(s + la);   // a few steps back from the spot (past the path's start too), so the stop is in view, not underfoot
    return fromEye([p[0], KEEP_H + lift, p[1]], [q[0], LOOK_Y, q[1]], FOV);
  }
  function topState(vb) {                                  // straight down on the plan's home view (vb, plan mm): the Layout's own framing
    const cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2, e = 0.002;
    return { tgt: [(cx - M.CX) / 1000, 0, (cy - M.CY) / 1000], dir: [0, Math.cos(e), Math.sin(e)], dist: 1500, h: vb[3] / 2000 };
  }
  function axoState(st) {                                  // the strategy's orthographic view, in this model's frame (the AxoLayers floor is the plan + (185842, −182802) mm)
    const AL = window.AxoLayers && window.AxoLayers.get(), dx = (185842 + (AL ? AL.CX : -54000) - M.CX) / 1000, dz = (-182802 + (AL ? AL.CY : 214489.5) - M.CY) / 1000;
    const th = st.theta, ph = st.phi;
    return { tgt: [st.t[0] + dx, st.t[1], st.t[2] + dz], dir: [Math.sin(ph) * Math.sin(th), Math.cos(ph), Math.sin(ph) * Math.cos(th)], dist: 1500, h: st.half };
  }
  const homeVb = () => { const [x, y, w, h] = plan.data.viewBox; return plan.vbFor([x, y, x + w, y + h], [35, 157, 1885, 670]); };
  const lerpV = (a, b, e) => ({ tgt: a.tgt.map((v, i) => v + (b.tgt[i] - v) * e), dir: norm(a.dir.map((v, i) => v + (b.dir[i] - v) * e)),
    dist: Math.exp(Math.log(a.dist) + (Math.log(b.dist) - Math.log(a.dist)) * e), h: Math.exp(Math.log(a.h) + (Math.log(b.h) - Math.log(a.h)) * e) });
  function apply(v) {
    cam.position.set(v.tgt[0] + v.dir[0] * v.dist, v.tgt[1] + v.dir[1] * v.dist, v.tgt[2] + v.dir[2] * v.dist);
    cam.up.set(0, 1, 0); cam.lookAt(v.tgt[0], v.tgt[1], v.tgt[2]);
    cam.fov = (2 * Math.atan(v.h / v.dist) * 180) / Math.PI; cam.aspect = S.asp;
    cam.near = Math.max(0.05, v.dist * 0.02); cam.far = v.dist + 700; cam.top = v.h;   // top: the model's level of detail reads it
    cam.updateProjectionMatrix();
  }
  const ease = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const easeIO = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u));

  // ---------- the moves: a flight along the Loop from stop i to stop j; any other change, an eased blend of two views
  function legMove(i, j) {
    const s0 = CV.stopS[i], s1 = CV.stopS[j], L = Math.abs(s1 - s0), lift = Math.min(16, L * 0.08), ms = 2200 + 3300 * Math.sqrt(L / 330);
    return { ms, at: (u) => { const e = easeIO(u); return eyeAt(s0 + (s1 - s0) * e, lift * Math.sin(Math.PI * e)); } };
  }
  const blend = (a, b, ms) => ({ ms, at: (u) => lerpV(a, b, ease(u)) });
  function target(k) { return k >= 8 ? topState(homeVb()) : eyeAt(CV.stopS[k - 1], 0); }
  function card(k, on) {
    const c = $(".wl-card", sc);
    if (k >= 1 && k <= 7) { const [n, q] = STOPS[k - 1]; $(".wl-n", c).textContent = String(k).padStart(2, "0") + " / 07"; $(".wl-name", c).textContent = n; $(".wl-q", c).textContent = q; }
    c.classList.toggle("on", !!on && k >= 1 && k <= 7);
    $$(".wl-dots i", sc).forEach((d, i) => { d.classList.toggle("on", i < k && k <= 7); d.classList.toggle("now", i === k - 1); });
    $(".wl-end", sc).classList.toggle("on", !!on && k === 8);
  }
  function go(k) {
    const from = S.k; S.k = k;
    const mv = k >= 2 && k <= 7 && from === k - 1 ? legMove(k - 2, k - 1) : k === 1 && from === 0 ? blend(S.cur, target(1), 4200) : blend(S.cur, target(k), k === 8 ? 3200 : 1500);
    card(k, false);
    if (reduced) { S.cur = target(k); S.anim = null; card(k, true); return; }
    S.anim = { mv, t0: performance.now(), k };
  }

  // ---------- the model, the people, the frames
  function build() {
    if (S.built) return true;
    if (!SKP || !window.ACKO_LOOP) return false;
    T = window.THREE; M = window.AxoSkp.get(asset); if (!M) return false;
    W = (p) => new T.Vector3(M.X(p[0]), 0, M.Z(p[1]));
    group = new T.Group(); group.name = "walk";
    try { people(); } catch (e) { console.warn("s-walk: no people", e); }
    cam = new T.PerspectiveCamera(FOV, 16 / 9, 0.05, 2000);
    curve();
    return (S.built = true);
  }
  function size() {
    const Wd = host.clientWidth, Hd = host.clientHeight; if (!Wd || !Hd) return false;
    const pr = r.getPixelRatio(); if (r.domElement.width !== Math.round(Wd * pr) || r.domElement.height !== Math.round(Hd * pr)) r.setSize(Wd, Hd, false);
    S.asp = Wd / Hd; return true;
  }
  function frame(now) {
    S.raf = 0;
    if (document.body.dataset.scene !== "s-walk" || !r) return;
    if (r.domElement.parentNode !== host) host.appendChild(r.domElement);
    if (!size()) { S.raf = requestAnimationFrame(frame); return; }
    if (S.anim) {
      const a = S.anim, u = Math.min(1, (now - a.t0) / a.mv.ms); S.cur = a.mv.at(u);
      if (u >= 1) { S.anim = null; card(a.k, true); if (a.k <= 7) cue("chime"); }
    }
    apply(S.cur);
    if (walkers.length) walk(now);
    r.render(M.scene, cam);
    S.raf = requestAnimationFrame(frame);
  }
  // the strategy's last frame, held under both pages while this model takes over from the same angle, then let go
  function snapIn(st) {
    const c = st && st._snap ? st._snap() : null; if (!c) return;
    const stage = document.getElementById("stage"), h = document.createElement("div");
    h.style.cssText = "position:fixed;left:var(--pl);top:var(--ptop);width:var(--pw);height:var(--ph);pointer-events:none;z-index:0;transition:opacity 1s ease-in-out";
    c.style.cssText = "width:100%;height:100%;display:block"; h.appendChild(c); stage.insertBefore(h, stage.firstChild);
    setTimeout(() => (h.style.opacity = "0"), 450); setTimeout(() => h.remove(), 1600);
  }
  // Layout · Spaces, arriving from here: lends the canvas to a host under both pages and eases to the plan's view (it is there already
  // after the last click), its own frames; done(host) on landing; the people leave the model once the plan has taken over
  function flatten(vb, ms, done) {
    if (!S.built || !r || !cam) return false;
    const stage = document.getElementById("stage"); if (!stage) return false;
    const h = document.createElement("div"); h.className = "st-flat-host";
    h.style.cssText = "position:fixed;left:var(--pl);top:var(--ptop);width:var(--pw);height:var(--ph);pointer-events:none;z-index:0";
    stage.insertBefore(h, stage.firstChild);
    const cv = r.domElement; h.appendChild(cv); cv.style.width = "100%"; cv.style.height = "100%"; cv.style.display = "block";
    cancelAnimationFrame(S.raf); S.raf = 0; S.flat = true;
    const from = S.cur, to = topState(vb), there = S.k === 8 && !S.anim, MS = there ? 250 : ms;
    let t0 = 0, end = false;
    const paint = (e) => { S.cur = lerpV(from, to, e); apply(S.cur); r.render(M.scene, cam); };
    const fin = () => { if (end) return; end = true; paint(1); if (done) done(h); setTimeout(() => { S.flat = false; if (document.body.dataset.scene !== "s-walk" && group) M.scene.remove(group); }, 2200); };
    const tick = (now) => { if (end) return; if (!t0) t0 = now; const k = Math.min(1, (now - t0) / MS); paint(ease(k)); if (k < 1) requestAnimationFrame(tick); else fin(); };
    paint(0); requestAnimationFrame(tick); setTimeout(fin, MS + 500);
    return true;
  }
  return {
    enter(_, s) {
      sc = s; plain(); reveal($(".wl-head", sc), 80); sc._flatten = flatten;
      const ok = build(); sc.classList.toggle("wl-fallback", !ok);
      if (!ok) return;
      r = window.AxoModel.renderer(); host = $(".wl-3d", sc);
      const fromSt = window.ACKO_MORPH ? window.ACKO_MORPH.take("s-strategy") : null, st = document.getElementById("s-strategy");
      const stState = st && st._strategy ? st._strategy().state : null;
      if (fromSt && stState) snapIn(st);                  // before this model takes the renderer
      M.reset(); if (!group.parent) M.scene.add(group); window.AxoSkp.look("sketchup");
      host.appendChild(r.domElement); r.domElement.style.width = "100%"; r.domElement.style.height = "100%"; r.domElement.style.display = "block";
      S.k = 0; S.anim = null;
      S.cur = stState ? axoState(stState) : axoState({ theta: -0.7848, phi: 0.7344, t: [0, 0, 0], half: 70 });
      cancelAnimationFrame(S.raf); S.raf = requestAnimationFrame(frame);
    },
    step(k) {
      if (!S.built || !sc || sc.classList.contains("wl-fallback")) { if (sc) card(k, true); return; }
      go(k);
      if (!S.raf) S.raf = requestAnimationFrame(frame);
    },
    leave() {
      cancelAnimationFrame(S.raf); S.raf = 0;
      if (window.ACKO_MORPH) window.ACKO_MORPH.mark("s-walk");   // Layout · Spaces takes the floor from here
      setTimeout(() => { if (!S.flat && document.body.dataset.scene !== "s-walk" && group && group.parent) M.scene.remove(group); }, 400);
    },
  };
});
