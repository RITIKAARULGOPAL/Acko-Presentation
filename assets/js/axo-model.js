/* AxoModel: the floor as a live three.js model, shared by the schematic axonometric (s-axo) and the campus strategy (s-strategy).
   Built once from data/axo-dxf.js (tools/acko/axo_dxf.py: the DXF plan toolkit's classed SVG) and data/plan-dxf.js, in the
   deck's axo look: a pale slab on a soft shadow, rooms in translucent purple glass, wood desks, grey chairs, green plants, black
   mullions round the façade, thin ink edges, the plan drawing faint on the floor. One WebGL renderer, moved between the slides
   (one GPU context). The model is in layers (THREE.Groups) that a slide can show, hide or grow:
     base       the shadow, the slab, the floors, the terraces, the drawing on the floor
     walls      solid walls, services, the rest of the building's floor
     glass      the rooms' purple glass and its frames
     facade     mullions, rails and the pale glass band
     furniture  desks, chairs, storage
     plants     rounded crowns
   Plan mm, y down; the model's metres: x east, y up, z south (X(), Z()). three.js r147. */
(function () {
  const AM = {};
  const H = { wall: 2.4, glass: 2.4, top: 2.7, chair: 0.45, desk: 0.75, store: 1.0, floor: 0.02 };
  const GLASS = new Set(["Phone booth", "Quick sprint", "Collaboration huddle", "Departmental room", "Boardroom", "Visitor hub", "The Hatchery",
    "Studio", "Zen room", "Mother's room", "Prayer room", "Executive corner cabin", "Training room", "Medical room", "Nap room"]);
  const SERVICE = new Set(["Server, UPS & battery", "Store room", "Mail room", "Hub room", "Not in contract"]);
  const FLOOR = (t) => GLASS.has(t) ? 0xe2daf2 : t === "Cafeteria" || t === "Coffee corner" ? 0xf3e9d0 : t === "Reception" ? 0xeee4d6 : SERVICE.has(t) ? 0xbdbdbd : 0xe8e8e6;
  let T, M = null, R = null;

  AM.H = H; AM.GLASS = GLASS; AM.SERVICE = SERVICE;
  // the one renderer (null without WebGL)
  AM.renderer = function () {
    if (R !== null) return R || null;
    T = window.THREE;
    try { R = new T.WebGLRenderer({ antialias: true, alpha: true }); R.setPixelRatio(Math.min(2, devicePixelRatio || 1)); R.setClearColor(0xffffff, 0); }
    catch (e) { R = false; }
    return R || null;
  };
  AM.available = () => !!(window.THREE && window.AXO_DXF && window.PLAN_DXF);
  // listeners called when something async (the floor drawing) lands, so the showing slide redraws
  AM.listeners = new Set();
  const changed = () => AM.listeners.forEach((f) => f());

  AM.get = function (asset) {
    if (M) return M;
    T = window.THREE;
    const A = window.AXO_DXF, P = window.PLAN_DXF;
    const xs = A.slab.map((q) => q[0]), ys = A.slab.map((q) => q[1]);
    const CX = (Math.min(...xs) + Math.max(...xs)) / 2, CY = (Math.min(...ys) + Math.max(...ys)) / 2;
    const X = (x) => (x - CX) / 1000, Z = (y) => (y - CY) / 1000;

    // ---------- geometry: flat-shaded prisms and quads gathered per material, ink lines per pen ----------
    const acc = () => ({ p: [], n: [] });
    function tri(a, A_, B, C) {
      const ux = B[0] - A_[0], uy = B[1] - A_[1], uz = B[2] - A_[2], vx = C[0] - A_[0], vy = C[1] - A_[1], vz = C[2] - A_[2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const l = Math.hypot(nx, ny, nz) || 1;
      a.p.push(A_[0], A_[1], A_[2], B[0], B[1], B[2], C[0], C[1], C[2]);
      for (let i = 0; i < 3; i++) a.n.push(nx / l, ny / l, nz / l);
    }
    function quad(a, p, q, y0, y1) { tri(a, [p[0], y0, p[1]], [q[0], y0, q[1]], [q[0], y1, q[1]]); tri(a, [p[0], y0, p[1]], [q[0], y1, q[1]], [p[0], y1, p[1]]); }
    // a ring (plan mm) stood up from y0 to y1 (m): its top, its sides, its ink (the top outline; corners and base on request)
    function prism(a, ring, y0, y1, ink, o) {
      o = o || {};
      const pts = ring.map(([x, y]) => [X(x), Z(y)]); if (pts.length < 3) return;
      const holes = (o.holes || []).map((h) => h.map(([x, y]) => [X(x), Z(y)]));
      let tris = [];
      try { tris = T.ShapeUtils.triangulateShape(pts.map(([x, z]) => new T.Vector2(x, z)), holes.map((h) => h.map(([x, z]) => new T.Vector2(x, z)))); } catch (e) { /* a broken ring: no top */ }
      const all = pts.concat(...holes);
      for (const [i, j, k] of tris) {
        const P0 = all[i], B = all[j], C = all[k], up = (B[1] - P0[1]) * (C[0] - P0[0]) - (B[0] - P0[0]) * (C[1] - P0[1]) >= 0;
        tri(a, [P0[0], y1, P0[1]], up ? [B[0], y1, B[1]] : [C[0], y1, C[1]], up ? [C[0], y1, C[1]] : [B[0], y1, B[1]]);
      }
      if (o.sides !== false) for (const r of [pts, ...holes]) for (let i = 0; i < r.length; i++) quad(a, r[i], r[(i + 1) % r.length], y0, y1);
      if (!ink) return;
      for (const r of [pts, ...holes]) for (let i = 0; i < r.length; i++) {
        const P0 = r[i], B = r[(i + 1) % r.length];
        ink.push(P0[0], y1, P0[1], B[0], y1, B[1]);
        if (o.base) ink.push(P0[0], y0, P0[1], B[0], y0, B[1]);
        if (o.corners) {
          const Q = r[(i - 1 + r.length) % r.length], t1 = Math.atan2(P0[1] - Q[1], P0[0] - Q[0]), t2 = Math.atan2(B[1] - P0[1], B[0] - P0[0]);
          let d = Math.abs(t1 - t2); d = Math.min(d, 2 * Math.PI - d);
          if (d > 0.45) ink.push(P0[0], y0, P0[1], P0[0], y1, P0[1]);
        }
      }
    }
    function mesh(a, mat) {
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(a.p, 3)); g.setAttribute("normal", new T.Float32BufferAttribute(a.n, 3));
      return new T.Mesh(g, mat);
    }
    function lines(l, color, opacity) {
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(l, 3));
      return new T.LineSegments(g, new T.LineBasicMaterial({ color, transparent: opacity < 1, opacity }));
    }
    const lam = (color, o) => new T.MeshLambertMaterial(Object.assign({ color, side: T.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 2 }, o || {}));
    const segDist = (x, y, a, b) => { const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L)) : 0;
      return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy); };

    const scene = new T.Scene(), G = {};
    for (const k of ["base", "walls", "glass", "facade", "furniture", "plants"]) { G[k] = new T.Group(); G[k].name = k; scene.add(G[k]); }
    // the soft shadow under the slab (a blurred silhouette, down and to the right as in the deck's axo)
    {
      const [x0, x1, y0, y1] = [Math.min(...xs) - 6000, Math.max(...xs) + 6000, Math.min(...ys) - 6000, Math.max(...ys) + 6000];
      const k = 2048 / (x1 - x0), cv = document.createElement("canvas"); cv.width = 2048; cv.height = Math.round((y1 - y0) * k);
      const c = cv.getContext("2d"); c.filter = "blur(10px)"; c.fillStyle = "rgba(60,55,70,.55)"; c.beginPath();
      A.slab.forEach(([x, y], i) => c[i ? "lineTo" : "moveTo"]((x - x0) * k, (y - y0) * k)); c.closePath(); c.fill();
      const pl = new T.Mesh(new T.PlaneGeometry((x1 - x0) / 1000, (y1 - y0) / 1000), new T.MeshBasicMaterial({ map: new T.CanvasTexture(cv), transparent: true, opacity: 0.5, depthWrite: false }));
      pl.rotation.x = -Math.PI / 2; pl.position.set(X((x0 + x1) / 2) + 1.6, -0.6, Z((y0 + y1) / 2) + 2.4); G.base.add(pl);
    }
    const INK_B = [], INK_W = [], INK_F = [], INK2 = [], GINK = [];
    // the slab, and the floors the legend colours
    const slab = acc(); prism(slab, A.slab, -0.18, 0, INK_B, { base: true, corners: true });
    G.base.add(mesh(slab, lam(0xe9e8e6)));
    const fl = {};
    for (const [t, r] of A.floors) { const c = FLOOR(t); prism(fl[c] || (fl[c] = acc()), r, 0, H.floor, null, { sides: false }); }
    const green = acc(); for (const r of A.terrace.concat(A.greens)) prism(green, r, 0, H.floor + 0.005, null, { sides: false });
    for (const c in fl) G.base.add(mesh(fl[c], lam(+c, { polygonOffsetFactor: -1, polygonOffsetUnits: -2 })));
    G.base.add(mesh(green, lam(0xb7d3a2, { polygonOffsetFactor: -2, polygonOffsetUnits: -4 })));
    // the plan drawing laid faintly on the floor (clipped to the slab): every piece of furniture reads, even where not stood up
    {
      const lv = P.levels[1] || P.levels[0], [vx, vy, vw, vh] = P.viewBox;
      const cv = document.createElement("canvas"), tex = new T.CanvasTexture(cv), img = new Image();
      img.onload = () => {
        const max = Math.min((R && R.capabilities.maxTextureSize) || 8192, 8192), k = Math.min(1, max / img.width);
        cv.width = Math.round(img.width * k); cv.height = Math.round(img.height * k);
        const c = cv.getContext("2d"), sx = cv.width / vw, sy = cv.height / vh;
        c.drawImage(img, 0, 0, cv.width, cv.height);
        c.globalCompositeOperation = "destination-in"; c.beginPath();
        A.slab.forEach(([x, y], i) => c[i ? "lineTo" : "moveTo"]((x - vx) * sx, (y - vy) * sy)); c.closePath(); c.fill();
        tex.needsUpdate = true; changed();
      };
      img.src = asset(lv.src); tex.anisotropy = 4;
      const mat = new T.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.38, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8 });
      const pl = new T.Mesh(new T.PlaneGeometry(vw / 1000, vh / 1000), mat);
      pl.rotation.x = -Math.PI / 2; pl.position.set(X(vx + vw / 2), H.floor + 0.01, Z(vy + vh / 2)); G.base.add(pl);
      AM.drawingMaterial = mat;
    }
    // solid walls (cores, services, the shell) and the grey masses of the rest of the building's floor
    const walls = acc(); for (const w of A.walls) prism(walls, w[0], 0, H.wall, INK_W, { holes: w.slice(1), corners: true });
    G.walls.add(mesh(walls, lam(0xf3f2f0)));
    const mass = acc(); for (const r of A.context) prism(mass, r, 0, H.top, INK_W, { corners: true });
    const serv = acc(); for (const [t, r] of A.floors) if (SERVICE.has(t)) prism(serv, r, 0, H.wall, INK_W, { corners: true });
    G.walls.add(mesh(mass, lam(0xcfcfcf))); G.walls.add(mesh(serv, lam(0x9a9a9a)));
    // the rooms: purple glass along their outlines, dark frames
    const glass = acc();
    for (const [t, r] of A.floors) if (GLASS.has(t)) {
      const pts = r.map(([x, y]) => [X(x), Z(y)]);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i], q = pts[(i + 1) % pts.length]; quad(glass, p, q, H.floor, H.glass);
        GINK.push(p[0], H.glass, p[1], q[0], H.glass, q[1], p[0], H.floor, p[1], q[0], H.floor, q[1]);
        const o = pts[(i - 1 + pts.length) % pts.length], t1 = Math.atan2(p[1] - o[1], p[0] - o[0]), t2 = Math.atan2(q[1] - p[1], q[0] - p[0]);
        let d = Math.abs(t1 - t2); d = Math.min(d, 2 * Math.PI - d); if (d > 0.45) GINK.push(p[0], H.floor, p[1], p[0], H.glass, p[1]);
      }
    }
    // furniture: each block's shapes once, placed by its uses; the loose ones as drawn
    const fu = { chair: acc(), desk: acc(), store: acc() };
    const place = (k, ring) => prism(fu[k], ring, 0, H[k], k === "chair" ? null : INK2);
    for (const u of A.uses) {
      const [id, a, b, c, d, e, f] = u;
      for (const [k, r] of A.blocks[id] || []) place(k, r.map(([x, y]) => [a * x + c * y + e, b * x + d * y + f]));
    }
    for (const [k, r] of A.loose) place(k, r);
    G.furniture.add(mesh(fu.desk, lam(0xd8b78c))); G.furniture.add(mesh(fu.chair, lam(0x5d5c62))); G.furniture.add(mesh(fu.store, lam(0xf2f0eb)));
    // the façade: black mullions about every 1.5 m along the slab's edge, rails, a pale glass band; a plain wall where the edge
    // meets the rest of the building
    const mull = acc(), pane = acc(), solidEdge = acc();
    const nearMass = (x, y) => A.context.some((r) => r.some((q, i) => segDist(x, y, q, r[(i + 1) % r.length]) < 900));
    for (let i = 0; i < A.slab.length; i++) {
      const p = A.slab[i], q = A.slab[(i + 1) % A.slab.length], L = Math.hypot(q[0] - p[0], q[1] - p[1]); if (L < 200) continue;
      const P0 = [X(p[0]), Z(p[1])], Q0 = [X(q[0]), Z(q[1])];
      if (nearMass((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)) { quad(solidEdge, P0, Q0, 0, H.top); INK_W.push(P0[0], H.top, P0[1], Q0[0], H.top, Q0[1]); continue; }
      quad(pane, P0, Q0, 0.08, H.top - 0.06);
      const n = Math.max(1, Math.round(L / 1500));
      for (let j = 0; j <= n; j++) {
        const t = j / n, x = P0[0] + (Q0[0] - P0[0]) * t, z = P0[1] + (Q0[1] - P0[1]) * t, w = 0.045;
        prism(mull, [[x - w, z - w], [x + w, z - w], [x + w, z + w], [x - w, z + w]].map(([a, b]) => [a * 1000 + CX, b * 1000 + CY]), 0, H.top, null);
      }
      INK_F.push(P0[0], H.top, P0[1], Q0[0], H.top, Q0[1], P0[0], 0.08, P0[1], Q0[0], 0.08, Q0[1]);
    }
    G.facade.add(mesh(mull, lam(0x262626))); G.walls.add(mesh(solidEdge, lam(0xdcdcdc)));
    // the see-through layers last, without writing depth, so what's behind them still shows
    const gm = mesh(glass, new T.MeshLambertMaterial({ color: 0x8a6cd0, transparent: true, opacity: 0.26, depthWrite: false, side: T.DoubleSide })); gm.renderOrder = 2; G.glass.add(gm);
    const pm = mesh(pane, new T.MeshLambertMaterial({ color: 0xdfe9ef, transparent: true, opacity: 0.16, depthWrite: false, side: T.DoubleSide })); pm.renderOrder = 3; G.facade.add(pm);
    if (A.plants.length) {
      const im = new T.InstancedMesh(new T.IcosahedronGeometry(1, 1), new T.MeshLambertMaterial({ color: 0x5f9845, flatShading: true }), A.plants.length);
      const m4 = new T.Matrix4(), q4 = new T.Quaternion(), s3 = new T.Vector3(), p3 = new T.Vector3();
      A.plants.forEach(([x, y, r], i) => { const Rr = Math.min(0.9, r / 1000) * 0.85; im.setMatrixAt(i, m4.compose(p3.set(X(x), 0.35 + Rr * 0.9, Z(y)), q4, s3.set(Rr, Rr * 0.9, Rr))); });
      G.plants.add(im);
    }
    G.base.add(lines(INK_B, 0x2a2a2a, 0.75)); G.walls.add(lines(INK_W, 0x2a2a2a, 0.75)); G.facade.add(lines(INK_F, 0x2a2a2a, 0.75));
    G.furniture.add(lines(INK2, 0x6b5a45, 0.45));
    const gl = lines(GINK, 0x45367a, 0.7); gl.renderOrder = 4; G.glass.add(gl);
    scene.add(new T.HemisphereLight(0xffffff, 0xb9b4c6, 0.78));
    const key = new T.DirectionalLight(0xffffff, 0.5); key.position.set(-40, 90, 60); scene.add(key);

    M = { scene, groups: G, X, Z, CX, CY, acc, quad, prism, mesh, lines, lam, segDist, slab: A.slab };
    // everything as built: every layer shown and full height (a slide that animates them puts them back on leaving)
    M.reset = () => { for (const k in G) { G[k].visible = true; G[k].scale.set(1, 1, 1); } if (AM.drawingMaterial) AM.drawingMaterial.opacity = 0.38; };
    return M;
  };

  // ---------- camera: an orthographic axo, a state {theta, phi, t, half} ----------
  AM.basis = function (s) {
    T = window.THREE;
    const d = new T.Vector3(Math.sin(s.phi) * Math.sin(s.theta), Math.cos(s.phi), Math.sin(s.phi) * Math.cos(s.theta));
    const f = d.clone().negate(), right = new T.Vector3(-f.z, 0, f.x).normalize(), up = new T.Vector3().crossVectors(right, f).normalize();
    return { d, f, right, up };
  };
  AM.apply = function (cam, s, asp) {
    const { d } = AM.basis(s);
    cam.position.set(s.t[0] + d.x * 300, s.t[1] + d.y * 300, s.t[2] + d.z * 300); cam.up.set(0, 1, 0); cam.lookAt(s.t[0], s.t[1], s.t[2]);
    cam.top = s.half; cam.bottom = -s.half; cam.left = -s.half * asp; cam.right = s.half * asp; cam.near = 1; cam.far = 900; cam.updateProjectionMatrix();
  };
  // the camera {theta, phi} that fits the slab between plan x0..x1 (mm) into fit [l, t, r, b] (page fractions)
  AM.frame = function (m, view, x0, x1, fit, asp) {
    T = window.THREE;
    const s = { theta: view.theta, phi: view.phi, t: [0, 0, 0], half: 1 }, { right, up } = AM.basis(s);
    let mnx = 1e9, mxx = -1e9, mny = 1e9, mxy = -1e9;
    for (const [x, y] of m.slab) {
      const px = m.X(Math.max(x0, Math.min(x1, x))), pz = m.Z(y);
      for (const h of [0, H.top]) {
        const v = new T.Vector3(px, h, pz), a = v.dot(right), b = v.dot(up);
        mnx = Math.min(mnx, a); mxx = Math.max(mxx, a); mny = Math.min(mny, b); mxy = Math.max(mxy, b);
      }
    }
    const fw = fit[2] - fit[0], fh = fit[3] - fit[1];
    s.half = Math.max((mxy - mny) / (2 * fh), (mxx - mnx) / (2 * fw * asp));
    const ox = ((fit[0] + fit[2]) - 1) * s.half * asp, oy = (1 - (fit[1] + fit[3])) * s.half;
    const c = right.clone().multiplyScalar((mnx + mxx) / 2 - ox).add(up.clone().multiplyScalar((mny + mxy) / 2 - oy));
    s.t = [c.x, c.y, c.z];
    return s;
  };
  window.AxoModel = AM;
})();
