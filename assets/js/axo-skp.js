/* AxoSkp: A day for a new Acker's live model, from the SketchUp model (Ritika, 26 Oct: "build the axo based on this skp file").
   Built once from data/axo-skp.js (tools/acko/axo_skp.py: acko2A_model.skp read through SketchUp's own library, every chair,
   desk and plant simplified and drawn once per placement), in AxoModel's world frame (the DXF slab's centre; x east, y up,
   z south), so the day's route, pins and walker sit where they did. Same shape as AxoModel.get(): { scene, groups, X, Z, CX, CY,
   slab, reset }, on the same renderer (AxoModel.renderer()) and camera helpers (AxoModel.apply / basis / frame). Layers:
     base       the slab, the floors, grass   walls      walls, partitions, the band's mass, tops
     glass      see-through surfaces          facade     metal (mullions, frames)
     furniture  wood, soft, hard              plants     the plants, in their own green
     marks      the entrances (red triangles)
   Two levels of detail: fine (3.5 cm) in the walk's close-ups, coarse (7 cm) when the view is wider than LOD_HALF m. Looks as
   AxoModel's (AxoModel.looks): "ppt" (as built: SketchUp's colours, no cast shadows), "sketchup" (SketchUp's colours with sun
   and shadows), "clay", "clay-tex", "crisp", "warm". The shadow map is drawn once per look (the floor stands still; the walker
   keeps its ring), not every frame. three.js r147. */
(function () {
  const AS = {}, LOD_HALF = 32;
  const GROUP_OF = { floor: "base", slab: "base", wall: "walls", top: "walls", glass: "glass", mullion: "facade", wood: "furniture",
    soft: "furniture", hard: "furniture", plant: "plants", grass: "base" };
  let T, M = null, REG = null, LOOK = "ppt", shadowDue = true;

  AS.available = () => !!(window.THREE && window.AXO_SKP && window.AXO_DXF && window.AxoModel);
  const bytes = (b64) => { const s = atob(b64), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer; };

  AS.get = function (asset) {
    if (M) return M;
    T = window.THREE;
    const D = window.AXO_SKP, A = window.AXO_DXF, P = window.PLAN_DXF;
    const xs = A.slab.map((q) => q[0]), ys = A.slab.map((q) => q[1]);
    const CX = (Math.min(...xs) + Math.max(...xs)) / 2, CY = (Math.min(...ys) + Math.max(...ys)) / 2;
    const X = (x) => (x - CX) / 1000, Z = (y) => (y - CY) / 1000;
    REG = { mats: [], meshes: [], pts: [] };
    const reg = (m, kind, vc) => { m.userData.kind = kind; m.userData.vc = !!vc; m.userData.ppt = { color: m.color.getHex(), opacity: m.opacity }; REG.mats.push(m); return m; };

    const scene = new T.Scene(), G = {};
    for (const k of ["base", "walls", "glass", "facade", "furniture", "plants", "marks"]) { G[k] = new T.Group(); G[k].name = k; scene.add(G[k]); }
    // the soft shadow under the slab, as AxoModel's (it grounds the floor in the looks without a sun)
    {
      const [x0, x1, y0, y1] = [Math.min(...xs) - 6000, Math.max(...xs) + 6000, Math.min(...ys) - 6000, Math.max(...ys) + 6000];
      const k = 2048 / (x1 - x0), cv = document.createElement("canvas"); cv.width = 2048; cv.height = Math.round((y1 - y0) * k);
      const c = cv.getContext("2d"); c.filter = "blur(10px)"; c.fillStyle = "rgba(60,55,70,.55)"; c.beginPath();
      A.slab.forEach(([x, y], i) => c[i ? "lineTo" : "moveTo"]((x - x0) * k, (y - y0) * k)); c.closePath(); c.fill();
      const pl = new T.Mesh(new T.PlaneGeometry((x1 - x0) / 1000, (y1 - y0) / 1000), reg(new T.MeshBasicMaterial({ map: new T.CanvasTexture(cv), transparent: true, opacity: 0.5, depthWrite: false }), "softshadow"));
      pl.rotation.x = -Math.PI / 2; pl.position.set(X((x0 + x1) / 2) + 1.6, -0.6, Z((y0 + y1) / 2) + 2.4); G.base.add(pl);
    }
    // one material per kind, white over the vertices' SketchUp colours (a look recolours it); flat-shaded, both sides
    const mats = {};
    const matOf = (k) => mats[k] || (mats[k] = reg(k === "glass"
      ? new T.MeshLambertMaterial({ color: 0xffffff, vertexColors: true, flatShading: true, transparent: true, opacity: 0.35, depthWrite: false, side: T.DoubleSide })
      : new T.MeshLambertMaterial({ color: 0xffffff, vertexColors: true, flatShading: true, side: T.DoubleSide,
          polygonOffset: k === "floor" || k === "slab" || k === "grass", polygonOffsetFactor: 1, polygonOffsetUnits: 2 }), k, true));
    // a part's geometry: int16 positions over its box, RGB per vertex, indices; UVs box-mapped in metres (for the looks' textures)
    function geometry(p) {
      const q = new Int16Array(bytes(p.p)), pos = new Float32Array(q.length);
      for (let i = 0; i < q.length; i += 3) for (let a = 0; a < 3; a++) pos[i + a] = p.lo[a] + ((q[i + a] + 32768) / 65535) * (p.hi[a] - p.lo[a]);
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.BufferAttribute(pos, 3));
      g.setAttribute("color", new T.BufferAttribute(new Uint8Array(bytes(p.c)), 3, true));
      g.setIndex(new T.BufferAttribute(p.i32 ? new Uint32Array(bytes(p.i)) : new Uint16Array(bytes(p.i)), 1));
      g.computeVertexNormals();
      const n = g.getAttribute("normal").array, uv = new Float32Array((pos.length / 3) * 2);
      for (let i = 0, j = 0; i < pos.length; i += 3, j += 2) {
        const nx = Math.abs(n[i]), ny = Math.abs(n[i + 1]), nz = Math.abs(n[i + 2]);
        if (ny >= nx && ny >= nz) { uv[j] = pos[i]; uv[j + 1] = pos[i + 2]; } else if (nx >= nz) { uv[j] = pos[i + 2]; uv[j + 1] = pos[i + 1]; } else { uv[j] = pos[i]; uv[j + 1] = pos[i + 1]; }
      }
      g.setAttribute("uv", new T.BufferAttribute(uv, 2));            // (the normals stay: the shadow lookup's normal bias needs them)
      g.computeBoundingSphere();
      return g;
    }
    const placements = D.units.map((u) => {
      const f = new Float32Array(bytes(u.m)), out = [];
      for (let i = 0; i < u.n; i++) { const m = f.subarray(i * 12, i * 12 + 12);
        out.push(new T.Matrix4().set(m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10], m[2], m[5], m[8], m[11], 0, 0, 0, 1)); }
      return out;
    });
    const fine = [], coarse = [], lo = new T.Vector3(1e9, 1e9, 1e9), hi = new T.Vector3(-1e9, -1e9, -1e9), ink = [];
    for (const p of D.parts) {
      const g = geometry(p), mat = matOf(p.k);
      let mesh;
      if (p.u >= 0) {
        const ms = placements[p.u]; mesh = new T.InstancedMesh(g, mat, ms.length);
        ms.forEach((m4, i) => mesh.setMatrixAt(i, m4)); mesh.instanceMatrix.needsUpdate = true;
        mesh.frustumCulled = false;                                             // r147 culls instances by the base geometry
      } else {
        mesh = new T.Mesh(g, mat);
        lo.min(new T.Vector3(...p.lo)); hi.max(new T.Vector3(...p.hi));
        if (p.lv === 0 && p.k !== "floor" && p.k !== "grass" && p.k !== "plant") ink.push(new T.EdgesGeometry(g, 30));
      }
      if (p.k === "glass") mesh.renderOrder = 2;
      G[GROUP_OF[p.k] || "furniture"].add(mesh); REG.meshes.push([mesh, p.k]);
      if (p.lv === 1) fine.push(mesh); else if (p.lv === 2) coarse.push(mesh);
    }
    // the architecture's edges, thin, in the looks' ink
    if (ink.length) {
      const arr = []; for (const e of ink) arr.push(...e.getAttribute("position").array);
      const lg = new T.BufferGeometry(); lg.setAttribute("position", new T.Float32BufferAttribute(arr, 3));
      const lm = reg(new T.LineBasicMaterial({ color: 0x2a2a2a, transparent: true, opacity: 0.55 }), "ink");
      G.walls.add(new T.LineSegments(lg, lm));
    }
    // the entrances: red triangles, as the deck marks them, on the floor at each
    {
      const tri = [], top = 0.06;
      for (const [ex, ey] of (P && P.overlays && P.overlays.entry) || []) {
        const r = [[ex - 1300, ey - 900], [ex + 1300, ey - 900], [ex, ey + 1300]].map(([x, y]) => [X(x), Z(y)]);
        tri.push(r[0][0], top, r[0][1], r[1][0], top, r[1][1], r[2][0], top, r[2][1]);
      }
      if (tri.length) { const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(tri, 3)); G.marks.add(new T.Mesh(g, new T.MeshBasicMaterial({ color: 0xc40000, side: T.DoubleSide }))); }
    }
    const hemi = new T.HemisphereLight(0xffffff, 0xb9b4c6, 0.78); scene.add(hemi);
    const key = new T.DirectionalLight(0xffffff, 0.5); key.position.set(-40, 90, 60); scene.add(key, key.target);
    REG.hemi = hemi; REG.key = key;
    for (const x of [lo.x, hi.x]) for (const y of [lo.y, hi.y]) for (const z of [lo.z, hi.z]) REG.pts.push(new T.Vector3(x, y, z));

    // each frame: the level of detail by the view's size; the shadow map drawn only when due (with the fine level showing)
    scene.onBeforeRender = (r, s, cam) => {
      const far = cam.top > LOD_HALF && !(shadowDue && REG.key.castShadow);
      for (const m of fine) m.visible = !far; for (const m of coarse) m.visible = far;
      r.shadowMap.autoUpdate = false;
      if (shadowDue) { r.shadowMap.needsUpdate = true; shadowDue = false; }
    };
    M = { scene, groups: G, X, Z, CX, CY, slab: A.slab, source: D.source };
    M.reset = () => { for (const k in G) { G[k].visible = true; G[k].scale.set(1, 1, 1); } shadowDue = true; };
    window.AxoModel.looks.apply(REG, LOOK);
    return M;
  };
  // the model's look: AxoSkp.look() gives it, AxoSkp.look(name) sets it ("ppt" or one of AxoModel.LOOKS); the shadows redrawn
  AS.look = function (name) {
    if (name === undefined) return LOOK;
    LOOK = window.AxoModel.LOOKS.includes(name) ? name : "ppt";
    if (M) { window.AxoModel.looks.apply(REG, LOOK); shadowDue = true; }
    return LOOK;
  };
  // the day's route as walked on this model (legs re-routed round what the SketchUp model has in the way), or the slide's own
  AS.route = (legs) => (window.AXO_SKP && window.AXO_SKP.route) || legs;
  window.AxoSkp = AS;
})();
