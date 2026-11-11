  // the unfold (11 Nov): option __N__ · __NAME__ (Ritika: "make the ACKO logo itself in ribbon form and let the ribbon unfold to
  // become the white Möbius strip"; then "give more variations"). ACKO's mark (its own three shapes, exactly) is shown only where a
  // ribbon's window lies on it, so it draws itself in along the ribbon, then winds off itself as the ribbon's tail runs round it. Each
  // ribbon is one route: a stretch of the mark's centreline ending at its tip, [a bridge to the strip's twist,] then the strip's own line.
  // On the strip the white is the photo itself, shown through a soft mask along the same line; the slide's photo then takes over.
  // OPT: place (twist | centre), tint (white | purple: a purple Möbius forms first, then washes white), heads (1 | 2: the mark's two
  // bands unwind opposite ways), cam (a close-up that pulls back), trail (the head narrows into the lilac line, which stays for beat 2)
  const OPT = Object.assign({ place: "twist", tint: "white", heads: 1, cam: 0, trail: false }, __OPT__);
  const MS = { raf: 0 };
  const ease = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const sm = (a, b, u) => { const x = Math.min(1, Math.max(0, (u - a) / (b - a))); return x * x * (3 - 2 * x); };
  const cl = (u) => Math.min(1, Math.max(0, u));
  const TW = [1330, 300], CEN = [768, 512];                      // photo px: the strip's twist, the page's middle
  const S = OPT.place === "centre" ? 3.4 : 1.9;                  // photo px per mark unit
  const IN = 800, HOLD = OPT.cam ? 500 : 300, WASH = OPT.tint === "purple" ? 1600 : 0, T = IN + HOLD + OPT.go + WASH;
  // the mark's centreline in its own units (169 × 127), from its right tip: [x, y, band width, part 0 top · 1 left wedge · 2 bottom]
  const K = [[166, 52, 8, 0], [140, 38, 40, 0], [110, 30, 46, 0], [78, 24, 46, 0], [46, 26, 40, 0], [22, 33, 28, 0], [23, 47, 30, 1], [25, 64, 34, 1],
    [23, 81, 30, 1], [32, 97, 34, 2], [62, 106, 44, 2], [94, 102, 48, 2], [124, 88, 46, 2], [150, 70, 36, 2]];
  const COL = [[144, 104, 240], [176, 152, 242], [72, 40, 184]], WHITE = [242, 242, 246], HEADC = [146, 111, 243], LILAC = [201, 179, 243];
  // ACKO's mark, its own three shapes (as s-open-1), in its 169 × 127 units
  const MARK = [["M12 34C30 33 44 35 52 38C48.5 55 48.5 74 52 89C40 92 24 93.5 12 92.5C-3 78 -3 50 12 34Z", "#b098f2"],
    ["M14 32C40 29 78 38 124 62L166 43.5C168.5 42 168.5 39.5 165.5 37.5C140 21 108 1 80 0C62 0 36 14 14 32Z", "#9068f0"],
    ["M169 44.5L104 74C70 89 36 97 13.5 95C32 109 55 127 76 127C104 126 148 102 167 88C169 86 169 85 169 84Z", "#4828ba"]];
  let R = null;
  function cr(P, n) {                                 // a closed Catmull-Rom through P (x, y, w, colour index), n samples a span
    const out = [], m = P.length;
    for (let i = 0; i < m; i++) {
      const p0 = P[(i - 1 + m) % m], p1 = P[i], p2 = P[(i + 1) % m], p3 = P[(i + 2) % m];
      for (let j = 0; j < n; j++) {
        const t = j / n, t2 = t * t, t3 = t2 * t, f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
        const c1 = COL[p1[3]], c2 = COL[p2[3]];
        out.push({ x: f(p0[0], p1[0], p2[0], p3[0]), y: f(p0[1], p1[1], p2[1], p3[1]), w: p1[2] + (p2[2] - p1[2]) * t, c: c1.map((v, q) => v + (c2[q] - v) * t) });
      }
    }
    out.push(Object.assign({}, out[0])); return out;
  }
  function route(logo, bridge, strip, frac) {         // one ribbon: logo [x, y, w] → bridge [x, y] → strip [x, y]; part 0 · 2 · 1
    const X = [], Y = [], W = [], part = [];
    logo.forEach((q) => { X.push(q[0]); Y.push(q[1]); W.push(q[2]); part.push(0); });
    bridge.forEach((q) => { X.push(q[0]); Y.push(q[1]); W.push(0); part.push(2); });
    strip.forEach((q) => { X.push(q[0]); Y.push(q[1]); W.push(0); part.push(1); });
    const ss = [0]; for (let i = 1; i < X.length; i++) ss.push(ss[i - 1] + Math.hypot(X[i] - X[i - 1], Y[i] - Y[i - 1]));
    const nn = X.map((_, i) => { const a = Math.max(0, i - 1), c = Math.min(X.length - 1, i + 1), dx = X[c] - X[a], dy = Y[c] - Y[a], l = Math.hypot(dx, dy) || 1; return [-dy / l, dx / l]; });
    const first = (p) => { const i = part.indexOf(p); return i < 0 ? -1 : ss[i]; };
    const LL = first(1), LG = bridge.length ? first(2) : LL, LS = (ss[ss.length - 1] - LL) * frac;
    return { X, Y, W, part, ss, nn, LG, LL, LS };
  }
  function rbuild(sc) {
    if (R) return R;
    const pts = []; $$(".o2-l", sc).forEach((p) => { const L = p.getTotalLength(); for (let s = 0; s < L; s += 3) { const q = p.getPointAtLength(s); pts.push([q.x, q.y]); } });
    let i0 = 0, b = Infinity; pts.forEach((q, i) => { const d = (q[0] - TW[0]) ** 2 + (q[1] - TW[1]) ** 2; if (d < b) { b = d; i0 = i; } });
    const line = pts.slice(i0).concat(pts.slice(0, i0)); line.push(line[0]);
    const P0 = line[0];
    const org = OPT.place === "centre" ? [CEN[0] - S * 84.5, CEN[1] - S * 63.5] : [P0[0] - S * K[0][0], P0[1] - S * K[0][1]];
    const L = cr(K, 14).map((q) => [org[0] + S * q.x, org[1] + S * q.y, S * q.w]);   // tip → top → wedge → bottom → tip
    let bridge = [];
    if (OPT.place === "centre") {                     // from the mark's tip, out and round to the twist, arriving along the strip
      const tip = L[L.length - 1], pv = L[L.length - 4], d0 = [tip[0] - pv[0], tip[1] - pv[1]], l0 = Math.hypot(...d0);
      const d1 = [line[3][0] - P0[0], line[3][1] - P0[1]], l1 = Math.hypot(...d1);
      const c1 = [tip[0] + (d0[0] / l0) * 380, tip[1] + (d0[1] / l0) * 380], c2 = [P0[0] - (d1[0] / l1) * 380, P0[1] - (d1[1] / l1) * 380];
      for (let j = 1; j < 80; j++) { const t = j / 80, v = 1 - t; bridge.push([v * v * v * tip[0] + 3 * v * v * t * c1[0] + 3 * v * t * t * c2[0] + t * t * t * P0[0], v * v * v * tip[1] + 3 * v * v * t * c1[1] + 3 * v * t * t * c2[1] + t * t * t * P0[1]]); }
    }
    const RR = $$(".uf-r", sc), dOf = (P) => "M" + P.map((p) => p[0].toFixed(1) + " " + p[1].toFixed(1)).join("L");
    let routes;
    if (OPT.heads === 2) {                            // the top band out one way, the bottom band the other, each from the tip
      const h = Math.floor(L.length / 2), back = line.slice().reverse();
      routes = [route(L.slice(0, h + 1).reverse(), bridge, line, 0.5), route(L.slice(h), bridge, back, 0.5)];
      const n = Math.floor(line.length / 2);
      RR[0].setAttribute("d", dOf(line.slice(0, n + 1))); RR[1].setAttribute("d", dOf(back.slice(0, n + 1)));
    } else {
      routes = [route(L, bridge, line, 1)];
      RR[0].setAttribute("d", dOf(line)); RR[1].setAttribute("d", "M0 0");
    }
    RR.forEach((r) => { const l = r.getTotalLength(); r.style.strokeDasharray = l + " " + (l + 10); });
    return (R = { routes, org, RR });
  }
  function band(cx, k, Rt, idx, wOf, cOf) {           // a ribbon over the samples idx of route Rt, quad by quad, each in its own colour
    for (let j = 0; j + 1 < idx.length; j++) {
      const i = idx[j], h = idx[j + 1], wi = wOf(i) / 2, wh = wOf(h) / 2, ci = cOf(i);
      if (!ci || ci[3] <= 0.004) continue;
      const a = [Rt.X[i] + Rt.nn[i][0] * wi, Rt.Y[i] + Rt.nn[i][1] * wi], b = [Rt.X[h] + Rt.nn[h][0] * wh, Rt.Y[h] + Rt.nn[h][1] * wh];
      const c = [Rt.X[h] - Rt.nn[h][0] * wh, Rt.Y[h] - Rt.nn[h][1] * wh], d = [Rt.X[i] - Rt.nn[i][0] * wi, Rt.Y[i] - Rt.nn[i][1] * wi];
      const col = `rgba(${ci[0] | 0},${ci[1] | 0},${ci[2] | 0},${ci[3].toFixed(3)})`;
      cx.fillStyle = col; cx.strokeStyle = col; cx.lineWidth = 1.2 * k;
      cx.beginPath(); cx.moveTo(a[0] * k, a[1] * k); cx.lineTo(b[0] * k, b[1] * k); cx.lineTo(c[0] * k, c[1] * k); cx.lineTo(d[0] * k, d[1] * k); cx.closePath(); cx.fill(); cx.stroke();
    }
  }
  function layers(Wc, Hc, k, img) {                   // the whole mark, and the photo tinted purple (option tint), on their own canvases
    if (R.mk && R.mk.width === Wc && R.mk.height === Hc) return;
    R.mk = document.createElement("canvas"); R.mk.width = Wc; R.mk.height = Hc;
    const m = R.mk.getContext("2d"); m.setTransform(k * S, 0, 0, k * S, k * R.org[0], k * R.org[1]);
    MARK.forEach(([d, c]) => { m.fillStyle = c; m.fill(new Path2D(d)); });
    if (OPT.tint === "purple" && img.complete && img.naturalWidth) {
      R.pp = document.createElement("canvas"); R.pp.width = Wc; R.pp.height = Hc; const p = R.pp.getContext("2d");
      p.drawImage(img, 0, 0, Wc, Hc); p.globalCompositeOperation = "multiply"; p.fillStyle = "rgb(144,104,240)"; p.fillRect(0, 0, Wc, Hc);
      p.globalCompositeOperation = "destination-in"; p.drawImage(img, 0, 0, Wc, Hc);
    }
  }
  function frame(sc, ms) {
    rbuild(sc);
    const cvs = $$(".uf-cv", sc), img = $(".o2-art img", sc), dpr = Math.min(2, devicePixelRatio || 1);
    const Wc = Math.round(cvs[0].clientWidth * dpr), Hc = Math.round(cvs[0].clientHeight * dpr);
    cvs.forEach((c) => { if (c.width !== Wc || c.height !== Hc) { c.width = Wc; c.height = Hc; } c.getContext("2d").clearRect(0, 0, Wc, Hc); });
    if (!Wc) return;
    const k = Wc / 1536; layers(Wc, Hc, k, img);
    const m2 = ms - IN - HOLD, u = ease(cl(m2 / OPT.go)), w = WASH ? ease(cl((m2 - OPT.go) / WASH)) : 0;
    const fadeLogo = 1 - sm(0.9, 1, u), fadeAll = WASH ? 1 : fadeLogo;
    if (OPT.cam) {                                    // a close-up on the mark that pulls back as the ribbon runs
      const cam = $(".o2-cam", sc), z = 1 + (OPT.cam - 1) * (1 - ease(cl(m2 / (OPT.go * 0.85))));
      cam.style.transition = "none"; cam.style.transformOrigin = `${((149.76 + 1.055 * TW[0]) / 19.2).toFixed(2)}% ${(1.0547 * TW[1] / 10.8).toFixed(2)}%`;
      cam.style.transform = `scale(${z.toFixed(4)})`;
    }
    const lx = cvs[1].getContext("2d"), sx = cvs[0].getContext("2d");
    const win = R.routes.map((Rt) => {
      let tail = 0, head = Rt.LG * ease(cl(ms / IN));
      if (m2 > 0) { tail = u * Rt.LL; head = Rt.LG + u * (Rt.LL - Rt.LG + Rt.LS); }
      const i0 = [], i1 = [], i2 = [];
      Rt.ss.forEach((s, i) => { if (s >= tail - 3 && s <= head + 3) [i0, i1, i2][Rt.part[i]].push(i); });
      const lastOf = (a) => a[a.length - 1];
      if (i2.length && i0.length) i2.unshift(lastOf(i0));
      if (i1.length) { const pre = i2.length ? lastOf(i2) : lastOf(i0); if (pre !== undefined) i1.unshift(pre); }
      return { Rt, tail, head, i0, i1, i2 };
    });
    // the mark itself, only where a ribbon's window lies on it
    win.forEach(({ Rt, i0 }) => band(lx, k, Rt, i0, (i) => Rt.W[i] * 1.7 + 14 * S, () => [255, 255, 255, 1]));
    lx.globalCompositeOperation = "source-in"; lx.drawImage(R.mk, 0, 0); lx.globalCompositeOperation = "source-over";
    if (fadeLogo < 1) { lx.globalCompositeOperation = "destination-in"; lx.fillStyle = `rgba(0,0,0,${fadeLogo})`; lx.fillRect(0, 0, Wc, Hc); lx.globalCompositeOperation = "source-over"; }
    // the bridge (centre stage): a narrow purple ribbon over the dark, from the mark's tip to the twist
    win.forEach(({ Rt, i2 }) => band(lx, k, Rt, i2, () => 12 * S / (OPT.place === "centre" ? 1.6 : 1), () => HEADC.concat(1)));
    // on the strip
    win.forEach(({ Rt, i1, head }) => {
      const behind = (i) => head - Rt.ss[i];
      if (OPT.tint === "purple") {                    // full width, purple, staying; the wash then clears it from the twist round
        const front = w * (Rt.LS + 500);
        band(sx, k, Rt, i1, (i) => 30 + 360 * sm(0, 260, behind(i)), (i) => [255, 255, 255, 1 - sm(0, 420, front - (Rt.ss[i] - Rt.LL))]);
      } else band(sx, k, Rt, i1, (i) => (OPT.trail ? 7 : 12 * S) + 330 * sm(0, 700, behind(i)),
        (i) => { const d = behind(i), q = sm(0, 520, d); return HEADC.map((v, j) => v + (WHITE[j] - v) * q).concat((1 - sm(380, 760, d)) * fadeAll); });
      if (OPT.trail) band(lx, k, Rt, i1, () => 7, () => LILAC.concat(1));   // the lilac line left on the strip
    });
    if (OPT.tint === "purple") { if (R.pp) { sx.globalCompositeOperation = "source-in"; sx.drawImage(R.pp, 0, 0); } }
    else if (img.complete && img.naturalWidth) { sx.globalCompositeOperation = "destination-in"; sx.drawImage(img, 0, 0, Wc, Hc); }
    sx.globalCompositeOperation = "source-over";
    // the photo behind the head (or behind the wash)
    win.forEach(({ Rt, head }, j) => {
      const r = R.RR[j], Lm = r.getTotalLength();
      const rv = OPT.tint === "purple" ? w * (Rt.LS + 500) - 120 : head - Rt.LL - 140;
      r.style.strokeDashoffset = (Lm - Math.min(Lm, Math.max(0, rv) * (Lm / Rt.LS))).toFixed(1);
    });
  }
  function setup(sc) { rbuild(sc); }
  function lineSvg(sc) { return $(".o2-art svg:not(.uf-svg)", sc); }
  function start(sc) {
    rbuild(sc); const img = $(".o2-art img", sc), sv = $(".uf-svg", sc);
    img.style.transition = "none"; img.style.opacity = 0; sv.style.opacity = 1; $(".uf-logo", sc).style.opacity = 0;
    $$(".uf-cv", sc).forEach((c) => (c.style.opacity = 1));
    if (OPT.trail) { lineSvg(sc).style.opacity = ""; $$(".o2-l", sc).forEach((p) => { p.style.strokeDasharray = ""; p.style.strokeDashoffset = ""; }); }
    frame(sc, 0);
  }
  function finish(sc, now) {
    const img = $(".o2-art img", sc), sv = $(".uf-svg", sc);
    img.style.transition = now ? "none" : "opacity .45s"; img.style.opacity = "";
    if (OPT.cam) { const cam = $(".o2-cam", sc); cam.style.transform = ""; cam.style.transformOrigin = ""; later(() => (cam.style.transition = ""), 50); }
    if (OPT.trail) {                                  // the line stays: beat 2 goes on from it rather than drawing it again
      $$(".o2-l", sc).forEach((p) => { p.style.transition = "none"; p.style.strokeDasharray = "none"; });
      const ls = lineSvg(sc); ls.style.transition = "none"; ls.style.opacity = 1; last = Math.max(last, 2);
    }
    $$(".uf-cv", sc).forEach((c) => (c.style.opacity = 0));
    if (now) sv.style.opacity = 0; else later(() => (sv.style.opacity = 0), 500);
  }
  function play(sc) {
    start(sc); const t0 = performance.now();
    const tick = (now) => { const ms = now - t0; frame(sc, ms); if (ms < T) MS.raf = requestAnimationFrame(tick); else finish(sc); };
    MS.raf = requestAnimationFrame(tick);
  }
  (window.__unfold = window.__unfold || {})["__ID__"] = (t) => { const sc = document.getElementById("__ID__"); cancelAnimationFrame(MS.raf); start(sc); frame(sc, t * T); };   // to check a frame
