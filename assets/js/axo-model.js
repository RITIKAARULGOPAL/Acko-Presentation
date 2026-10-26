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
     marks      the entrances (red triangles)
   Plan mm, y down; the model's metres: x east, y up, z south (X(), Z()). three.js r147. */
(function () {
  const AM = {};
  const H = { wall: 2.4, glass: 2.4, top: 2.7, chair: 0.45, desk: 0.75, store: 1.0, floor: 0.02, sill: 0.32 };
  const GLASS = new Set(["Phone booth", "Quick sprint", "Collaboration huddle", "Departmental room", "Boardroom", "Visitor hub", "The Hatchery",
    "Studio", "Zen room", "Mother's room", "Prayer room", "Executive corner cabin", "Training room", "Medical room", "Nap room"]);
  const SERVICE = new Set(["Server, UPS & battery", "Store room", "Mail room", "Hub room", "Not in contract"]);
  // the floors by zone, as the PPT's schematic axo has them (Ritika, 22 Oct: "take the schematic axo in ppt as reference"): a dark
  // corridor band, the workhall pale, the café cream, the terrace grass, the rooms lavender, the services grey
  const FLOOR = (t) => GLASS.has(t) ? 0xd6c9ef : t === "Corridor" ? 0x5a5a60 : t === "Cafeteria" || t === "Coffee corner" || t === "Pantry" ? 0xf2e7c6
    : t === "Reception" || t === "Entry" ? 0xefe4d2 : t === "Terrace" ? 0x9dc27c : t === "Lift lobby" ? 0xdddce2 : t === "Washroom" ? 0xd6d6d6
    : t === "Collab" ? 0xe4dff0 : SERVICE.has(t) ? 0xbdbdbd : 0xebebe9;
  let T, M = null, R = null, REG = null, LOOK = "ppt";
  // each floor's kind, for the looks (the rooms', the corridor, the café's, …; the terrace is grass and stays green)
  const floorKind = (t) => GLASS.has(t) ? "roomfloor" : t === "Corridor" ? "corridor" : t === "Cafeteria" || t === "Coffee corner" || t === "Pantry" ? "cafe"
    : t === "Reception" || t === "Entry" ? "reception" : t === "Terrace" ? "green" : t === "Lift lobby" ? "lobby" : t === "Washroom" ? "wash"
    : t === "Collab" ? "collab" : SERVICE.has(t) ? "servfloor" : "floor";

  AM.H = H; AM.GLASS = GLASS; AM.SERVICE = SERVICE;
  // the one renderer (null without WebGL)
  AM.renderer = function () {
    if (R !== null) return R || null;
    T = window.THREE;
    try {
      R = new T.WebGLRenderer({ antialias: true, alpha: true }); R.setPixelRatio(Math.min(2, devicePixelRatio || 1)); R.setClearColor(0xffffff, 0);
      R.shadowMap.enabled = true; R.shadowMap.type = T.PCFSoftShadowMap;       // only a light that casts (the white looks' sun) costs anything
    }
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
    // the looks' registry: every material with a kind (its PPT colour kept) and every mesh made with one
    REG = { mats: [], meshes: [] };
    const reg = (m, kind) => { if (kind) { m.userData.kind = kind; m.userData.ppt = { color: m.color.getHex(), opacity: m.opacity }; REG.mats.push(m); } return m; };

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
    // a mesh, with UVs box-mapped in metres from each face's normal (tops x/z, sides x/y or z/y), so a look's textures tile at real
    // scale; a material with a kind (lam(color, o, kind)) is the look's to recolour
    function mesh(a, mat) {
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(a.p, 3)); g.setAttribute("normal", new T.Float32BufferAttribute(a.n, 3));
      const uv = new Float32Array((a.p.length / 3) * 2);
      for (let i = 0, j = 0; i < a.p.length; i += 3, j += 2) {
        const nx = Math.abs(a.n[i]), ny = Math.abs(a.n[i + 1]), nz = Math.abs(a.n[i + 2]);
        if (ny >= nx && ny >= nz) { uv[j] = a.p[i]; uv[j + 1] = a.p[i + 2]; } else if (nx >= nz) { uv[j] = a.p[i + 2]; uv[j + 1] = a.p[i + 1]; } else { uv[j] = a.p[i]; uv[j + 1] = a.p[i + 1]; }
      }
      g.setAttribute("uv", new T.BufferAttribute(uv, 2));
      const m = new T.Mesh(g, mat); if (mat.userData.kind) REG.meshes.push([m, mat.userData.kind]);
      return m;
    }
    function lines(l, color, opacity, kind) {
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(l, 3));
      return new T.LineSegments(g, reg(new T.LineBasicMaterial({ color, transparent: true, opacity }), kind));
    }
    const lam = (color, o, kind) => reg(new T.MeshLambertMaterial(Object.assign({ color, side: T.DoubleSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 2 }, o || {})), kind);
    const segDist = (x, y, a, b) => { const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy, t = L ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L)) : 0;
      return Math.hypot(x - a[0] - t * dx, y - a[1] - t * dy); };

    const scene = new T.Scene(), G = {};
    for (const k of ["base", "walls", "glass", "facade", "furniture", "plants", "marks"]) { G[k] = new T.Group(); G[k].name = k; scene.add(G[k]); }
    // the soft shadow under the slab (a blurred silhouette, down and to the right as in the deck's axo)
    {
      const [x0, x1, y0, y1] = [Math.min(...xs) - 6000, Math.max(...xs) + 6000, Math.min(...ys) - 6000, Math.max(...ys) + 6000];
      const k = 2048 / (x1 - x0), cv = document.createElement("canvas"); cv.width = 2048; cv.height = Math.round((y1 - y0) * k);
      const c = cv.getContext("2d"); c.filter = "blur(10px)"; c.fillStyle = "rgba(60,55,70,.55)"; c.beginPath();
      A.slab.forEach(([x, y], i) => c[i ? "lineTo" : "moveTo"]((x - x0) * k, (y - y0) * k)); c.closePath(); c.fill();
      const pl = new T.Mesh(new T.PlaneGeometry((x1 - x0) / 1000, (y1 - y0) / 1000), reg(new T.MeshBasicMaterial({ map: new T.CanvasTexture(cv), transparent: true, opacity: 0.5, depthWrite: false }), "softshadow"));
      pl.rotation.x = -Math.PI / 2; pl.position.set(X((x0 + x1) / 2) + 1.6, -0.6, Z((y0 + y1) / 2) + 2.4); G.base.add(pl);
    }
    const INK_B = [], INK_W = [], INK_F = [], INK2 = [], GINK = [];
    // the slab, and the floors the legend colours
    const slab = acc(); prism(slab, A.slab, -0.18, 0, INK_B, { base: true, corners: true });
    G.base.add(mesh(slab, lam(0xe9e8e6, null, "slab")));
    const fl = {}, kindOf = {};
    for (const [t, r] of A.floors) { const c = FLOOR(t); kindOf[c] = floorKind(t); prism(fl[c] || (fl[c] = acc()), r, 0, H.floor, null, { sides: false }); }
    const green = acc(); for (const r of A.terrace.concat(A.greens)) prism(green, r, 0, H.floor + 0.005, null, { sides: false });
    for (const c in fl) G.base.add(mesh(fl[c], lam(+c, { polygonOffsetFactor: -1, polygonOffsetUnits: -2 }, kindOf[c])));
    G.base.add(mesh(green, lam(0x9dc27c, { polygonOffsetFactor: -2, polygonOffsetUnits: -4 }, "green")));
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
      const mat = new T.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.3, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -8 });
      const pl = new T.Mesh(new T.PlaneGeometry(vw / 1000, vh / 1000), mat);
      pl.rotation.x = -Math.PI / 2; pl.position.set(X(vx + vw / 2), H.floor + 0.01, Z(vy + vh / 2)); G.base.add(pl);
      AM.drawingMaterial = mat;
    }
    // solid walls (cores, services, the shell) and the grey masses of the rest of the building's floor
    const walls = acc(); for (const w of A.walls) prism(walls, w[0], 0, H.wall, INK_W, { holes: w.slice(1), corners: true });
    G.walls.add(mesh(walls, lam(0xf3f2f0, null, "wall")));
    const mass = acc(); for (const r of A.context) prism(mass, r, 0, H.top, INK_W, { corners: true });
    const serv = acc(); for (const [t, r] of A.floors) if (SERVICE.has(t)) prism(serv, r, 0, H.wall, INK_W, { corners: true });
    G.walls.add(mesh(mass, lam(0xcfcfcf, null, "mass"))); G.walls.add(mesh(serv, lam(0x9a9a9a, null, "service")));
    // the rooms: purple glass along their outlines over a solid deeper-purple base (as in the PPT's axo), dark frames
    const glass = acc(), sill = acc();
    for (const [t, r] of A.floors) if (GLASS.has(t)) {
      const pts = r.map(([x, y]) => [X(x), Z(y)]);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i], q = pts[(i + 1) % pts.length]; quad(glass, p, q, H.sill, H.glass); quad(sill, p, q, H.floor, H.sill);
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
    G.furniture.add(mesh(fu.desk, lam(0xd8b78c, null, "desk"))); G.furniture.add(mesh(fu.chair, lam(0x5d5c62, null, "chair"))); G.furniture.add(mesh(fu.store, lam(0xf2f0eb, null, "store")));
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
    G.facade.add(mesh(mull, lam(0x262626, null, "mullion"))); G.walls.add(mesh(solidEdge, lam(0xdcdcdc, null, "edge")));
    // the see-through layers last, without writing depth, so what's behind them still shows
    const gm = mesh(glass, reg(new T.MeshLambertMaterial({ color: 0x7d5fd2, transparent: true, opacity: 0.32, depthWrite: false, side: T.DoubleSide }), "glass")); gm.renderOrder = 2; G.glass.add(gm);
    G.glass.add(mesh(sill, lam(0x6a4cb4, null, "sill")));
    const pm = mesh(pane, reg(new T.MeshLambertMaterial({ color: 0xdfe9ef, transparent: true, opacity: 0.16, depthWrite: false, side: T.DoubleSide }), "pane")); pm.renderOrder = 3; G.facade.add(pm);
    if (A.plants.length) {
      const im = new T.InstancedMesh(new T.IcosahedronGeometry(1, 1), new T.MeshLambertMaterial({ color: 0x4f8f3a, flatShading: true }), A.plants.length);
      const m4 = new T.Matrix4(), q4 = new T.Quaternion(), s3 = new T.Vector3(), p3 = new T.Vector3();
      A.plants.forEach(([x, y, r], i) => { const Rr = Math.min(0.9, r / 1000) * 0.85; im.setMatrixAt(i, m4.compose(p3.set(X(x), 0.35 + Rr * 0.9, Z(y)), q4, s3.set(Rr, Rr * 0.9, Rr))); });
      G.plants.add(im); REG.meshes.push([im, "plant"]);
    }
    // the entrances: red triangles, as the deck marks them (on the core's cap, pointing in)
    const tri3 = acc();
    for (const [ex, ey] of (P.overlays && P.overlays.entry) || []) prism(tri3, [[ex - 1300, ey - 900], [ex + 1300, ey - 900], [ex, ey + 1300]], H.top + 0.02, H.top + 0.06, null);
    G.marks.add(mesh(tri3, new T.MeshBasicMaterial({ color: 0xc40000, side: T.DoubleSide })));
    G.base.add(lines(INK_B, 0x2a2a2a, 0.75, "ink")); G.walls.add(lines(INK_W, 0x2a2a2a, 0.75, "ink")); G.facade.add(lines(INK_F, 0x2a2a2a, 0.75, "ink"));
    G.furniture.add(lines(INK2, 0x6b5a45, 0.45, "inkf"));
    const gl = lines(GINK, 0x45367a, 0.7, "inkg"); gl.renderOrder = 4; G.glass.add(gl);
    const hemi = new T.HemisphereLight(0xffffff, 0xb9b4c6, 0.78); scene.add(hemi);
    const key = new T.DirectionalLight(0xffffff, 0.5); key.position.set(-40, 90, 60); scene.add(key, key.target);
    REG.hemi = hemi; REG.key = key; REG.slab = A.slab; REG.X = X; REG.Z = Z;

    M = { scene, groups: G, X, Z, CX, CY, acc, quad, prism, mesh, lines, lam, segDist, slab: A.slab };
    // everything as built: every layer shown and full height (a slide that animates them puts them back on leaving)
    M.reset = () => { for (const k in G) { G[k].visible = true; G[k].scale.set(1, 1, 1); } if (AM.drawingMaterial) AM.drawingMaterial.opacity = LOOKS[LOOK] ? LOOKS[LOOK].drawing : 0.38; };
    applyLook();
    return M;
  };

  // ---------- looks: the PPT's colours ("ppt", as built), or a white model with cast shadows and near-white textures ----------
  // (Ritika, 26 Oct: "make this axo completely plain white with shadows and depth and textures"; both axos; the day's story, the
  // plants and the grass keep their colour). A look recolours the materials by kind; the textures are drawn here, no files.
  const W = (o) => Object.assign({
    tex: 0, slab: 0xefefed, floor: 0xf7f7f5, cafe: 0xf6f5f2, wall: 0xfbfbfa, mass: 0xf1f1ef, service: 0xe8e8e6, sill: 0xf3f3f1,
    desk: 0xfcfcfa, chair: 0xeeeeec, store: 0xf8f8f6, mullion: 0xdadad8, glass: [0xffffff, 0.4], pane: [0xf6f9fb, 0.18],
    ink: [0xa6a6a4, 0.5], inkf: [0xbdbdbb, 0.4], inkg: [0xb2b2b2, 0.55], soft: 0.3, drawing: 0.12,
    // the sun 50° to the left of the deck's view (azimuth θ ≈ -0.61), 52° up: shadows fall to the right where they show, not
    // behind what casts them; left faces lit, fronts half, right faces in shade
    sun: [-100, 128, 9], sunColor: 0xffffff, sunI: 0.95, sky: 0xffffff, ground: 0xd8d8dd, skyI: 0.55,
  }, o);
  const LOOKS = {
    clay: W({}),
    "clay-tex": W({ tex: 1 }),
    crisp: W({ tex: 1.8, mullion: 0xb2b2b0, glass: [0xf4f4f4, 0.55], ink: [0x6a6a68, 0.72], inkf: [0x8c8c8a, 0.55], inkg: [0x777777, 0.7],
      sunI: 1.05, skyI: 0.42, drawing: 0.16 }),
    warm: W({ tex: 1, slab: 0xf2eee7, floor: 0xfbf8f2, cafe: 0xfaf6ef, wall: 0xfdfbf7, mass: 0xf4f0e9, service: 0xeee9e1, sill: 0xf6f3ec,
      desk: 0xfefbf5, chair: 0xf1ede5, store: 0xfbf8f2, mullion: 0xe0dbd0, glass: [0xfffcf6, 0.4], pane: [0xfdfaf4, 0.18],
      ink: [0xb3ab9c, 0.5], inkf: [0xc6beb0, 0.4], inkg: [0xbfb7a9, 0.55], sun: [-99, 78, -17], sunColor: 0xfff2e2, sunI: 1.0,
      sky: 0xfffbf4, ground: 0xdcd6cc, skyI: 0.52 }),
  };
  AM.LOOKS = Object.keys(LOOKS);
  // each kind's colour key, texture and tile (m); the kinds that keep their PPT colour in every look
  const GROUP = { slab: "slab", floor: "floor", roomfloor: "floor", corridor: "floor", lobby: "floor", wash: "floor", collab: "floor",
    servfloor: "floor", cafe: "cafe", reception: "cafe", wall: "wall", edge: "wall", mass: "mass", service: "service", sill: "sill",
    desk: "desk", chair: "chair", store: "store", mullion: "mullion", glass: "glass", pane: "pane", ink: "ink", inkf: "inkf", inkg: "inkg" };
  const TEX = { slab: ["concrete", 4], floor: ["concrete", 4], cafe: ["terrazzo", 2], wall: ["plaster", 3], mass: ["concrete", 4],
    service: ["plaster", 3], sill: ["plaster", 3], desk: ["wood", 1.6], chair: ["fabric", 0.4], store: ["plaster", 2] };
  const CAST = new Set(["wall", "mass", "service", "sill", "desk", "chair", "store", "mullion", "plant"]);
  const SEE = new Set(["glass", "pane"]);
  // near-white textures, drawn once per kind and strength: concrete grain, terrazzo chips, plaster, wood grain, fabric weave
  const texCache = {};
  function texture(name, k) {
    const key = name + "@" + k; if (texCache[key]) return texCache[key];
    const N = 512, cv = document.createElement("canvas"); cv.width = cv.height = N;
    const c = cv.getContext("2d"); c.fillStyle = "#fff"; c.fillRect(0, 0, N, N);
    let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const dot = (x, y, r, col) => { c.fillStyle = col; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill(); };
    if (name === "concrete" || name === "plaster") {
      const n = name === "concrete" ? 9000 : 5000, a = (name === "concrete" ? 0.07 : 0.045) * k;
      for (let i = 0; i < 40; i++) { const x = rnd() * N, y = rnd() * N, r = 30 + rnd() * 90, g = c.createRadialGradient(x, y, 0, x, y, r);
        g.addColorStop(0, `rgba(120,120,118,${0.035 * k})`); g.addColorStop(1, "rgba(120,120,118,0)"); c.fillStyle = g; c.fillRect(x - r, y - r, 2 * r, 2 * r); }
      for (let i = 0; i < n; i++) dot(rnd() * N, rnd() * N, 0.4 + rnd() * (name === "concrete" ? 1.2 : 0.7), `rgba(${110 + rnd() * 60 | 0},${110 + rnd() * 60 | 0},${108 + rnd() * 60 | 0},${a})`);
    } else if (name === "terrazzo") {
      for (let i = 0; i < 1400; i++) { const r = 1 + rnd() * 3.2, t = rnd(); dot(rnd() * N, rnd() * N, r, t < 0.5 ? `rgba(150,150,148,${0.2 * k})` : t < 0.8 ? `rgba(196,182,160,${0.22 * k})` : `rgba(90,90,92,${0.16 * k})`); }
    } else if (name === "wood") {
      for (let i = 0; i < 150; i++) {
        const y0 = rnd() * N, amp = 2 + rnd() * 6, f = 0.004 + rnd() * 0.01, ph = rnd() * 6.28;
        c.strokeStyle = `rgba(176,150,112,${(0.07 + rnd() * 0.08) * k})`; c.lineWidth = 0.6 + rnd() * 1.4; c.beginPath();
        for (let x = 0; x <= N; x += 8) { const y = y0 + Math.sin(x * f + ph) * amp; x ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
      }
    } else if (name === "fabric") {
      c.strokeStyle = `rgba(120,120,124,${0.09 * k})`; c.lineWidth = 1;
      for (let i = 0; i < N; i += 3) { c.beginPath(); c.moveTo(i, 0); c.lineTo(i, N); c.stroke(); c.beginPath(); c.moveTo(0, i + 1.5); c.lineTo(N, i + 1.5); c.stroke(); }
      for (let i = 0; i < 2500; i++) dot(rnd() * N, rnd() * N, 0.5, `rgba(90,90,96,${0.06 * k})`);
    }
    const t = new T.CanvasTexture(cv); t.wrapS = t.wrapT = T.RepeatWrapping; t.anisotropy = 8;
    return (texCache[key] = t);
  }
  // the sun's shadow camera, fitted round the floor as the sun sees it
  function fitSun(key) {
    const d = key.position.clone().normalize(), up = Math.abs(d.y) > 0.99 ? new T.Vector3(0, 0, 1) : new T.Vector3(0, 1, 0);
    const right = new T.Vector3().crossVectors(up, d).normalize(), top = new T.Vector3().crossVectors(d, right).normalize();
    let a0 = 1e9, a1 = -1e9, b0 = 1e9, b1 = -1e9;
    for (const [x, y] of REG.slab) for (const h of [0, H.top]) {
      const v = new T.Vector3(REG.X(x), h, REG.Z(y)), a = v.dot(right), b = v.dot(top);
      a0 = Math.min(a0, a); a1 = Math.max(a1, a); b0 = Math.min(b0, b); b1 = Math.max(b1, b);
    }
    key.position.copy(d.multiplyScalar(200)); key.target.position.set(0, 0, 0); key.target.updateMatrixWorld();
    const cam = key.shadow.camera; cam.left = a0 - 2; cam.right = a1 + 2; cam.bottom = b0 - 2; cam.top = b1 + 2; cam.near = 1; cam.far = 420;
    cam.updateProjectionMatrix(); key.shadow.mapSize.set(4096, 4096); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.03;
    if (key.shadow.map) { key.shadow.map.dispose(); key.shadow.map = null; }
  }
  function applyLook() {
    if (!REG) return;
    const L = LOOKS[LOOK];
    for (const m of REG.mats) {
      const kind = m.userData.kind, g = GROUP[kind], p = m.userData.ppt;
      if (!L || !g) { m.color.setHex(p.color); m.opacity = kind === "softshadow" && L ? L.soft : p.opacity; if (m.map && TEX[g]) m.map = null; m.needsUpdate = true; continue; }
      const v = L[g];
      if (Array.isArray(v)) { m.color.setHex(v[0]); m.opacity = v[1]; } else m.color.setHex(v);
      const tx = TEX[g];
      m.map = L.tex && tx ? texture(tx[0], L.tex) : null;
      if (m.map) m.map.repeat.set(1 / tx[1], 1 / tx[1]);
      m.needsUpdate = true;
    }
    for (const [mesh, kind] of REG.meshes) { const g = GROUP[kind] || kind; mesh.castShadow = !!L && CAST.has(g); mesh.receiveShadow = !!L && !SEE.has(g); }
    const { hemi, key } = REG;
    if (L) {
      hemi.color.setHex(L.sky); hemi.groundColor.setHex(L.ground); hemi.intensity = L.skyI;
      key.color.setHex(L.sunColor); key.intensity = L.sunI; key.position.set(...L.sun); key.castShadow = true; fitSun(key);
    } else {
      hemi.color.setHex(0xffffff); hemi.groundColor.setHex(0xb9b4c6); hemi.intensity = 0.78;
      key.color.setHex(0xffffff); key.intensity = 0.5; key.position.set(-40, 90, 60); key.castShadow = false;
    }
    if (AM.drawingMaterial) AM.drawingMaterial.opacity = L ? L.drawing : 0.38;
  }
  // the model's look: AxoModel.look() gives it, AxoModel.look(name) sets it ("ppt" or one of AxoModel.LOOKS) and redraws
  AM.look = function (name) {
    if (name === undefined) return LOOK;
    LOOK = LOOKS[name] ? name : "ppt"; T = T || window.THREE;
    if (M) { applyLook(); changed(); }
    return LOOK;
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
