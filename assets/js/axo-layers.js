/* AxoLayers: the campus strategy's floor (deck slide 13) as a live three.js model in the layers the 3D renders build it in
   (axo_update/acko2A_model*.png), from data/axo-layers.js (tools/acko/axo_layers.py: the 22.10.26 layout DXF and the renders).
   Each layer is a THREE.Group a slide can show, grow (scale.y) or fade:
     base      the slab and its floors in the renders' colours (render 01): grey floor, lavender corridors, purple rooms,
               pale yellow café, olive terraces
     mass      the columns and the building's middle band (grey blocks)
     partitions  the rooms' purple glass (render 02)    rooms     the furniture in the rooms (render 02)
     cafe      the café's and training room's furniture (03)       terrace   the terraces' furniture (04)
     work      the workstations and the open floor's furniture (05) plants    the plants (06)
     facade    mullions, rails and pale glass round the floor (07)
     zones     the six neighbourhoods 01-06 as translucent volumes with their numbers, the atriums, the terraces and the café's
               zone (-01, 00; the boundaries from ACKO_NEI.dxf)
     routes    the employee's journey (red dashes, 08) and the client's (blue, 09), drawn on from the entrances
   M.tint(k) takes the whole model from the white model (k = 0, render -02) to the renders' colours (k = 1).
   Plan mm, y down; the model's metres: x east, y up, z south (X(), Z()). It shares AxoModel's renderer and camera helpers. */
(function () {
  const AL = {};
  let T, M = null;
  AL.available = () => !!(window.THREE && window.AXO_LAYERS && window.AxoModel);

  AL.get = function () {
    if (M) return M;
    T = window.THREE;
    const A = window.AXO_LAYERS, H = A.heights;
    const xs = A.slab.map((q) => q[0]), ys = A.slab.map((q) => q[1]);
    const CX = (Math.min(...xs) + Math.max(...xs)) / 2, CY = (Math.min(...ys) + Math.max(...ys)) / 2;
    const X = (x) => (x - CX) / 1000, Z = (y) => (y - CY) / 1000;

    // ---------- geometry: flat-shaded prisms gathered per material, ink lines per pen ----------
    const acc = () => ({ p: [], n: [] });
    function tri(a, P0, B, C) {
      const ux = B[0] - P0[0], uy = B[1] - P0[1], uz = B[2] - P0[2], vx = C[0] - P0[0], vy = C[1] - P0[1], vz = C[2] - P0[2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const l = Math.hypot(nx, ny, nz) || 1;
      a.p.push(P0[0], P0[1], P0[2], B[0], B[1], B[2], C[0], C[1], C[2]);
      for (let i = 0; i < 3; i++) a.n.push(nx / l, ny / l, nz / l);
    }
    function quad(a, p, q, y0, y1) { tri(a, [p[0], y0, p[1]], [q[0], y0, q[1]], [q[0], y1, q[1]]); tri(a, [p[0], y0, p[1]], [q[0], y1, q[1]], [p[0], y1, p[1]]); }
    // a ring (plan mm) stood up from y0 to y1 (m): its top, its sides, its ink (the top outline; corners and base on request)
    function prism(a, ring, y0, y1, ink, o) {
      o = o || {};
      const pts = ring.map(([x, y]) => [X(x), Z(y)]); if (pts.length < 3) return;
      let tris = [];
      try { tris = T.ShapeUtils.triangulateShape(pts.map(([x, z]) => new T.Vector2(x, z)), []); } catch (e) { /* a broken ring: no top */ }
      for (const [i, j, k] of tris) {
        const P0 = pts[i], B = pts[j], C = pts[k], up = (B[1] - P0[1]) * (C[0] - P0[0]) - (B[0] - P0[0]) * (C[1] - P0[1]) >= 0;
        tri(a, [P0[0], y1, P0[1]], up ? [B[0], y1, B[1]] : [C[0], y1, C[1]], up ? [C[0], y1, C[1]] : [B[0], y1, B[1]]);
      }
      if (o.sides !== false) for (let i = 0; i < pts.length; i++) quad(a, pts[i], pts[(i + 1) % pts.length], y0, y1);
      if (!ink) return;
      for (let i = 0; i < pts.length; i++) {
        const P0 = pts[i], B = pts[(i + 1) % pts.length];
        ink.push(P0[0], y1, P0[1], B[0], y1, B[1]);
        if (o.base) ink.push(P0[0], y0, P0[1], B[0], y0, B[1]);
        if (o.corners) {
          const Q = pts[(i - 1 + pts.length) % pts.length], t1 = Math.atan2(P0[1] - Q[1], P0[0] - Q[0]), t2 = Math.atan2(B[1] - P0[1], B[0] - P0[0]);
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
    // materials that tint between the white model and the renders' colours
    const tinted = [];
    function lam(col, white, o) {
      const m = new T.MeshLambertMaterial(Object.assign({ color: col, side: T.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 2 }, o || {}));
      m.userData.col = new T.Color(col); m.userData.white = new T.Color(white); tinted.push(m); return m;
    }
    function lines(l, col, white, opacity) {
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(l, 3));
      const m = new T.LineBasicMaterial({ color: col, transparent: true, opacity });
      m.userData.col = new T.Color(col); m.userData.white = new T.Color(white); tinted.push(m);
      return new T.LineSegments(g, m);
    }

    const scene = new T.Scene(), G = {};
    for (const k of ["base", "mass", "partitions", "rooms", "cafe", "terrace", "work", "plants", "facade", "zones", "routes"]) { G[k] = new T.Group(); G[k].name = k; scene.add(G[k]); }
    const C = A.colours, WHITE = 0xfbfbfa;

    // ---------- the slab and its floors (render 01) ----------
    const INK_B = [];
    const slab = acc(); prism(slab, A.slab, -0.3, 0, INK_B, { base: true, corners: true });
    G.base.add(mesh(slab, lam(C.floor, WHITE)));
    const ORDER = ["floor", "corridor", "cafe", "terrace", "room"], fl = {};
    for (const [t, r, f] of A.floors) prism(fl[f] || (fl[f] = acc()), r, 0, 0.02, null, { sides: false });
    ORDER.forEach((f, i) => { if (fl[f]) G.base.add(mesh(fl[f], lam(C[f], WHITE, { polygonOffsetFactor: -1 - i, polygonOffsetUnits: -2 - 2 * i }))); });
    G.base.add(lines(INK_B, 0x2a2a2a, 0x9a9a9a, 0.7));

    // ---------- the columns and the middle band's grey blocks ----------
    const INK_M = [], mass = acc(), cols = acc();
    for (const r of A.mass) prism(mass, r, 0, H.mass, INK_M, { corners: true });
    for (const r of A.columns) prism(cols, r, 0, H.column, INK_M, { corners: true });
    // the band a little see-through, as in render 01 (a column shows through it)
    const bandMat = lam(0xc8c8c8, 0xf2f2f0, { transparent: true, opacity: 0.88, depthWrite: false }), band = mesh(mass, bandMat); band.renderOrder = 1;
    G.mass.add(band, mesh(cols, lam(0xbdbdbd, 0xececea)), lines(INK_M, 0x3a3a3a, 0xa6a6a6, 0.6));

    // ---------- the rooms' glass (render 02) ----------
    const walled = new Set(A.walled), glass = acc(), GINK = [];
    for (const [t, r] of A.floors) if (walled.has(t)) {
      const pts = r.map(([x, y]) => [X(x), Z(y)]);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i], q = pts[(i + 1) % pts.length]; quad(glass, p, q, 0.02, H.wall);
        GINK.push(p[0], H.wall, p[1], q[0], H.wall, q[1], p[0], 0.02, p[1], q[0], 0.02, q[1]);
        const o = pts[(i - 1 + pts.length) % pts.length], t1 = Math.atan2(p[1] - o[1], p[0] - o[0]), t2 = Math.atan2(q[1] - p[1], q[0] - p[0]);
        let d = Math.abs(t1 - t2); d = Math.min(d, 2 * Math.PI - d); if (d > 0.45) GINK.push(p[0], 0.02, p[1], p[0], H.wall, p[1]);
      }
    }
    const gmat = new T.MeshLambertMaterial({ color: 0x6f5d85, transparent: true, opacity: 0.42, depthWrite: false, side: T.DoubleSide });
    gmat.userData.col = new T.Color(0x6f5d85); gmat.userData.white = new T.Color(0xd9d9d9); gmat.userData.op = [0.22, 0.42]; tinted.push(gmat);
    const gm = new T.Mesh(new T.BufferGeometry(), gmat);
    gm.geometry.setAttribute("position", new T.Float32BufferAttribute(glass.p, 3)); gm.geometry.setAttribute("normal", new T.Float32BufferAttribute(glass.n, 3));
    gm.renderOrder = 3; G.partitions.add(gm);
    const gl = lines(GINK, 0x2d2340, 0x8f8f8f, 0.75); gl.renderOrder = 4; G.partitions.add(gl);

    // ---------- furniture by group: each block's shapes once, placed by its uses; the loose ones as drawn ----------
    const KIND = { desk: [0xdcc6a4, 0xf3f3f1], chair: [0x77767c, 0xdedede], store: [0xeeebe4, 0xf6f6f4], sofa: [0x9a999e, 0xe6e6e6] };
    const fu = {}, FINK = {};
    const place = (g, k, ring) => { const a = (fu[g] || (fu[g] = {}))[k] || (fu[g][k] = acc()); prism(a, ring, 0, H[k], k === "chair" ? null : (FINK[g] || (FINK[g] = []))); };
    for (const u of A.uses) {
      const [id, a, b, c, d, e, f, g] = u;
      for (const [k, r] of A.blocks[id] || []) place(g, k, r.map(([x, y]) => [a * x + c * y + e, b * x + d * y + f]));
    }
    for (const [k, r, g] of A.loose) place(g, k, r);
    for (const g in fu) {
      for (const k in fu[g]) G[g].add(mesh(fu[g][k], lam(KIND[k][0], KIND[k][1])));
      if (FINK[g]) G[g].add(lines(FINK[g], 0x5a4a38, 0xb0b0b0, 0.45));
    }

    // ---------- plants (render 06): rounded crowns ----------
    if (A.plants.length) {
      const pm = new T.MeshLambertMaterial({ color: 0x5f9845, flatShading: true });
      const im = new T.InstancedMesh(new T.IcosahedronGeometry(1, 1), pm, A.plants.length);
      const m4 = new T.Matrix4(), q4 = new T.Quaternion(), s3 = new T.Vector3(), p3 = new T.Vector3();
      A.plants.forEach(([x, y, r], i) => { const R = Math.min(0.9, r / 1000) * 0.85; im.setMatrixAt(i, m4.compose(p3.set(X(x), 0.35 + R * 0.9, Z(y)), q4, s3.set(R, R * 1.1, R))); });
      G.plants.add(im);
    }

    // ---------- the façade (render 07): mullions about every 1.5 m, rails, pale glass ----------
    const mull = acc(), pane = acc(), INK_F = [];
    for (let i = 0; i < A.slab.length; i++) {
      const p = A.slab[i], q = A.slab[(i + 1) % A.slab.length], L = Math.hypot(q[0] - p[0], q[1] - p[1]); if (L < 200) continue;
      const P0 = [X(p[0]), Z(p[1])], Q0 = [X(q[0]), Z(q[1])];
      quad(pane, P0, Q0, 0.05, H.facade);
      const n = Math.max(1, Math.round(L / 1500));
      for (let j = 0; j <= n; j++) {
        const t = j / n, x = P0[0] + (Q0[0] - P0[0]) * t, z = P0[1] + (Q0[1] - P0[1]) * t, w = 0.04;
        prism(mull, [[x - w, z - w], [x + w, z - w], [x + w, z + w], [x - w, z + w]].map(([a, b]) => [a * 1000 + CX, b * 1000 + CY]), 0, H.facade, null);
      }
      for (const h of [0.05, 1.1, H.facade]) INK_F.push(P0[0], h, P0[1], Q0[0], h, Q0[1]);
    }
    G.facade.add(mesh(mull, lam(0xa9a9a9, 0xcfcfcf)), lines(INK_F, 0x6d6d6d, 0xb4b4b4, 0.8));
    const pmat = new T.MeshLambertMaterial({ color: 0xdfe9ef, transparent: true, opacity: 0.14, depthWrite: false, side: T.DoubleSide });
    const pn = mesh(pane, pmat); pn.renderOrder = 5; G.facade.add(pn);

    // ---------- the neighbourhoods (renders -01 and 00): translucent volumes, their numbers on top ----------
    function numberTex(txt, col) {
      const cv = document.createElement("canvas"); cv.width = 512; cv.height = 320;
      const draw = () => {
        const c = cv.getContext("2d"); c.clearRect(0, 0, 512, 320);
        c.font = "700 250px Figtree, Poppins, Arial, sans-serif"; c.textAlign = "center"; c.textBaseline = "middle";
        c.shadowColor = "rgba(0,0,0,.22)"; c.shadowBlur = 8; c.shadowOffsetY = 3; c.fillStyle = col; c.fillText(txt, 256, 168);
        c.shadowColor = "transparent"; c.lineWidth = 3; c.strokeStyle = "rgba(90,90,90,.45)"; c.strokeText(txt, 256, 168);
        tex.needsUpdate = true; if (M) changed();
      };
      const tex = new T.CanvasTexture(cv); tex.anisotropy = 4; draw();
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
      return tex;
    }
    const ring2 = (r) => { let a = 0, cx = 0, cy = 0; for (let i = 0; i < r.length; i++) { const [x0, y0] = r[i], [x1, y1] = r[(i + 1) % r.length], f = x0 * y1 - x1 * y0; a += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f; } return [cx / (3 * a), cy / (3 * a)]; };
    function volume(ring, col, op, h, number, numCol) {
      const grp = new T.Group(), a = acc(), ink = [];
      prism(a, ring, 0.03, h, ink, { corners: true });
      const mat = new T.MeshLambertMaterial({ color: col, transparent: true, opacity: op, depthWrite: false, side: T.DoubleSide });
      const m = mesh(a, mat); m.renderOrder = 6; grp.add(m);
      const lm = new T.LineBasicMaterial({ color: new T.Color(col).multiplyScalar(0.7), transparent: true, opacity: 0.7 }), ln = new T.LineSegments(new T.BufferGeometry(), lm);
      ln.geometry.setAttribute("position", new T.Float32BufferAttribute(ink, 3)); ln.renderOrder = 7; grp.add(ln);
      grp.userData.mats = [[mat, op], [lm, 0.7]];
      if (number) {
        const ys_ = ring.map((q) => q[1]), span = (Math.max(...ys_) - Math.min(...ys_)) / 1000, hgt = Math.max(7, Math.min(15, span * 0.5));
        const [cx, cy] = ring2(ring), nm = new T.MeshBasicMaterial({ map: numberTex(number, numCol || "#ffffff"), transparent: true, depthWrite: false, depthTest: false });
        const pl = new T.Mesh(new T.PlaneGeometry(hgt * 1.6, hgt), nm); pl.rotation.x = -Math.PI / 2; pl.position.set(X(cx), h + 0.03, Z(cy)); pl.renderOrder = 12;      // on top, as the deck's numbers are
        grp.add(pl); grp.userData.mats.push([nm, 1]); grp.userData.num = pl; grp.userData.numH = hgt;
        grp.userData.at = [X(cx), h, Z(cy)];
      }
      return grp;
    }
    const zones = A.zones.map((z) => { const v = volume(z.ring, z.colour, z.n === "03" ? 0.78 : 0.62, H.zone, z.n, "#ffffff"); v.userData.zone = z; return v; });
    const atrium = A.atrium.map((r) => volume(r, "#929292", 0.85, H.zone * 0.5));
    const terr = A.terrace.map((r) => volume(r, "#8f8f6a", 0.55, H.zone * 0.5));
    const cafe = (A.cafezone || []).map((r) => volume(r, "#efe7a6", 0.8, H.zone * 0.5));     // the café's own zone (ACKO_NEI.dxf), in the renders' cream
    zones.concat(atrium, terr, cafe).forEach((v) => G.zones.add(v));

    // ---------- the routes (renders 08 and 09): dashes on the floor, drawn on in order of their distance from the entrances ----------
    function dashes(runs, col) {
      const P = 1.7, D = 1.05, W = 0.42, Y = 0.08, quads = [];
      for (const run of runs) {
        const pts = run.map(([x, y, d]) => [X(x), Z(y), d]);
        for (let i = 0; i + 1 < pts.length; i++) {
          const [ax, az, ad] = pts[i], [bx, bz, bd] = pts[i + 1], L = Math.hypot(bx - ax, bz - az); if (L < 1e-3 || bd <= ad) continue;
          // the parts of this segment that fall on a dash (by route distance, so dashes keep their rhythm across segments)
          for (let k = Math.floor(ad / P); k * P < bd; k++) {
            const s0 = Math.max(ad, k * P), s1 = Math.min(bd, k * P + D); if (s1 <= s0) continue;
            const t0 = (s0 - ad) / (bd - ad), t1 = (s1 - ad) / (bd - ad), nx = -(bz - az) / L * W / 2, nz = (bx - ax) / L * W / 2;
            const p0 = [ax + (bx - ax) * t0, az + (bz - az) * t0], p1 = [ax + (bx - ax) * t1, az + (bz - az) * t1];
            quads.push({ d: s0, v: [p0[0] + nx, Y, p0[1] + nz, p0[0] - nx, Y, p0[1] - nz, p1[0] - nx, Y, p1[1] - nz, p1[0] + nx, Y, p1[1] + nz] });
          }
        }
      }
      quads.sort((a, b) => a.d - b.d);
      const pos = [], idx = [];
      quads.forEach((q, i) => { pos.push(...q.v); const k = 4 * i; idx.push(k, k + 1, k + 2, k, k + 2, k + 3); });
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.setDrawRange(0, 0);
      const mat = new T.MeshBasicMaterial({ color: col, transparent: true, opacity: 1, side: T.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -12 });
      const m = new T.Mesh(g, mat); m.renderOrder = 9;
      m.userData.ds = quads.map((q) => q.d); m.userData.max = quads.length ? quads[quads.length - 1].d : 0;
      // drawn up to distance d (m) from the entrances
      m.userData.to = (d) => { const ds = m.userData.ds; let lo = 0, hi = ds.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (ds[mid] <= d) lo = mid + 1; else hi = mid; } g.setDrawRange(0, lo * 6); };
      return m;
    }
    const routes = { employee: dashes(A.routes.employee, 0xe0141e), client: dashes(A.routes.client, 0x1a2cf0) };
    G.routes.add(routes.employee, routes.client);

    // soft light from above and the south-west: the faces we see stay close to the tops, as in the renders
    scene.add(new T.HemisphereLight(0xffffff, 0xd0ccd8, 0.7));
    const key = new T.DirectionalLight(0xffffff, 0.35); key.position.set(-50, 80, 50); scene.add(key);

    M = { scene, groups: G, X, Z, CX, CY, slab: A.slab, zones, atrium, terrace: terr, cafe, routes, data: A };
    // the white model (0) to the renders' colours (1)
    M.tint = (k) => { for (const m of tinted) { m.color.lerpColors(m.userData.white, m.userData.col, k); if (m.userData.op) m.opacity = m.userData.op[0] + (m.userData.op[1] - m.userData.op[0]) * k; } };
    // a volume's fade (0..1)
    M.fade = (v, k) => { v.visible = k > 0.002; for (const [m, op] of v.userData.mats) m.opacity = op * k; };
    M.tint(1);
    return M;
  };
  // the camera {theta, phi, t, half} (AxoModel's) that fits the floor, façade height included, into fit [l, t, r, b] (page fractions)
  AL.frame = function (m, view, fit, asp) {
    const s = { theta: view.theta, phi: view.phi, t: [0, 0, 0], half: 1 }, { right, up } = window.AxoModel.basis(s), v = new T.Vector3();
    let mnx = 1e9, mxx = -1e9, mny = 1e9, mxy = -1e9;
    for (const [x, y] of m.slab) for (const h of [-0.3, m.data.heights.facade]) {
      v.set(m.X(x), h, m.Z(y)); const a = v.dot(right), b = v.dot(up);
      mnx = Math.min(mnx, a); mxx = Math.max(mxx, a); mny = Math.min(mny, b); mxy = Math.max(mxy, b);
    }
    const fw = fit[2] - fit[0], fh = fit[3] - fit[1];
    s.half = Math.max((mxy - mny) / (2 * fh), (mxx - mnx) / (2 * fw * asp));
    const ox = ((fit[0] + fit[2]) - 1) * s.half * asp, oy = (1 - (fit[1] + fit[3])) * s.half;
    const c = right.clone().multiplyScalar((mnx + mxx) / 2 - ox).add(up.clone().multiplyScalar((mny + mxy) / 2 - oy));
    s.t = [c.x, c.y, c.z];
    return s;
  };
  // listeners called when something async (the numbers' font) lands, so the showing slide redraws
  AL.listeners = new Set();
  const changed = () => AL.listeners.forEach((f) => f());
  window.AxoLayers = AL;
})();
