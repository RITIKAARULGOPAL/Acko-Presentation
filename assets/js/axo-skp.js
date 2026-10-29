/* AxoSkp: A day for a new Acker's live model, from the SketchUp model (Ritika, 26 Oct: "build the axo based on this skp file").
   Built once from data/axo-skp.js (tools/acko/axo_skp.py: acko2A_model.skp read through SketchUp's own library, every chair,
   desk and plant simplified and drawn once per placement), in AxoModel's world frame (the DXF slab's centre; x east, y up,
   z south), so the day's route, pins and walker sit where they did. Same shape as AxoModel.get(): { scene, groups, X, Z, CX, CY,
   slab, reset }, on the same renderer (AxoModel.renderer()) and camera helpers (AxoModel.apply / basis / frame). Layers:
     base       the slab, the floors, grass   walls      walls, partitions, tops, the band "Not in contract" (a solid mass)
     glass      see-through surfaces          facade     metal (mullions, frames)
     furniture  wood, soft, hard              plants     the plants, in their own green
     marks      the entrances (red triangles)
   Two levels of detail: fine (3.5 cm) in the walk's close-ups, coarse (7 cm) when the view is wider than LOD_HALF m. Looks as
   AxoModel's (AxoModel.looks): "ppt" (as built: SketchUp's colours, no cast shadows), "sketchup" (SketchUp's colours with sun
   and shadows), "clay", "clay-tex", "crisp", "warm". The shadow map is drawn once per look (the floor stands still; the walker
   keeps its ring), not every frame. AxoSkp.focus(rings) keeps the purples in one space and greys them elsewhere. three.js r147. */
(function () {
  const AS = {}, LOD_HALF = 32;
  const GROUP_OF = { floor: "base", slab: "base", wall: "walls", top: "walls", glass: "glass", mullion: "facade", wood: "furniture",
    soft: "furniture", hard: "furniture", plant: "plants", grass: "base", mass: "walls" };
  let T, M = null, REG = null, LOOK = "ppt", shadowDue = true;
  const FOCUS = { u: { uFocusMap: { value: null }, uFocusBox: { value: null }, uFocusOn: { value: 0 } }, cv: null, box: null };

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
    // the focus (AS.focus): a mask over the slab, white in the space in focus; outside it the model's purples go grey
    {
      const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      const cv = document.createElement("canvas"); cv.width = 2048; cv.height = Math.max(64, Math.round(((y1 - y0) / (x1 - x0)) * 2048));
      FOCUS.cv = cv; FOCUS.box = [x0, y0, x1, y1];
      FOCUS.u.uFocusMap.value = new T.CanvasTexture(cv); FOCUS.u.uFocusMap.value.flipY = false;     // row 0 is the plan's least y
      FOCUS.u.uFocusBox.value = new T.Vector4(X(x0), Z(y0), 1000 / (x1 - x0), 1000 / (y1 - y0));
    }
    // the walls, their tops, the glass and the frames grey their purples everywhere while a focus is on, in it too (29 Oct, on
    // the neighbourhood's lavender walls: walls and glass grey, only the floor and the wayfinding marks purple); "hard" too, as
    // SketchUp has the rooms' full-height panels in it (29 Oct: "still few walls are getting highlighted")
    const FLAT = ["wall", "top", "glass", "mullion", "mass", "hard"];
    const focusable = (m, k) => {
      if (FLAT.includes(k)) m.defines = { ...(m.defines || {}), FOCUS_GREY: "" };
      m.onBeforeCompile = (sh) => {
        Object.assign(sh.uniforms, FOCUS.u);
        sh.vertexShader = "varying vec2 vFocusXZ;\n" + sh.vertexShader.replace("#include <project_vertex>", `#include <project_vertex>
          vec4 fcW = vec4(transformed, 1.0);
          #ifdef USE_INSTANCING
            fcW = instanceMatrix * fcW;
          #endif
          vFocusXZ = (modelMatrix * fcW).xz;`);
        sh.fragmentShader = "uniform sampler2D uFocusMap;\nuniform vec4 uFocusBox;\nuniform float uFocusOn;\nvarying vec2 vFocusXZ;\n" + sh.fragmentShader.replace("#include <color_fragment>", `#include <color_fragment>
          if (uFocusOn > 0.5) {                                     // a purple (blue over green, red not under it) outside the focus goes grey
            vec3 c = diffuseColor.rgb;
            float purple = smoothstep(0.015, 0.06, c.b - c.g) * smoothstep(-0.04, 0.0, c.r - c.g);
            float inside = texture2D(uFocusMap, (vFocusXZ - uFocusBox.xy) * uFocusBox.zw).r;
            #ifdef FOCUS_GREY
            inside = 0.0;
            #endif
            float l = mix(dot(c, vec3(0.299, 0.587, 0.114)), max(c.r, max(c.g, c.b)), 0.4);
            diffuseColor.rgb = mix(c, vec3(l), purple * (1.0 - inside));
          }`);
      };
      return m;
    };
    // one material per kind, white over the vertices' SketchUp colours (a look recolours it); flat-shaded, both sides
    const mats = {};
    const matOf = (k) => mats[k] || (mats[k] = reg(focusable(k === "glass"
      ? new T.MeshLambertMaterial({ color: 0xffffff, vertexColors: true, flatShading: true, transparent: true, opacity: 0.35, depthWrite: false, side: T.DoubleSide })
      : new T.MeshLambertMaterial({ color: 0xffffff, vertexColors: true, flatShading: true, side: T.DoubleSide,
          polygonOffset: k === "floor" || k === "slab" || k === "grass", polygonOffsetFactor: 1, polygonOffsetUnits: 2 }), k), k, true));
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
    // the terraces' open edges are parapets, not glazing (29 Oct: "the marked walls should be parapets"): the facade's glass
    // panels and fins on a terrace's south edge and its two sides are taken out (scaled to nothing), and each edge gets one
    // solid parapet, PARAPET m high, along the panels' line (drawn after the parts, below)
    const PARAPET = 1.1, edges = {};
    {
      const ringOf = (d) => d.split("M")[1].replace(/Z/g, "").split("L").map((t) => t.trim().split(/\s+/).map(Number));
      const decks = ((P && P.spaces) || []).filter((s) => s.type === "Terrace").map((s) => {
        const r = ringOf(s.d).map(([x, y]) => [X(x), Z(y)]), xs = r.map((q) => q[0]), zs = r.map((q) => q[1]);
        return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)];
      });
      const zero = new T.Matrix4().makeScale(0, 0, 0), done = new Set(), v = new T.Vector3();
      for (const p of D.parts) {
        if (p.k !== "glass" || p.u < 0 || done.has(p.u)) continue;
        done.add(p.u);
        placements[p.u].forEach((m4, i) => {
          const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
          for (const a of [p.lo[0], p.hi[0]]) for (const b of [p.lo[1], p.hi[1]]) for (const c of [p.lo[2], p.hi[2]]) {
            v.set(a, b, c).applyMatrix4(m4); [v.x, v.y, v.z].forEach((w, k) => { lo[k] = Math.min(lo[k], w); hi[k] = Math.max(hi[k], w); });
          }
          if (hi[1] < 2) return;
          const dx = hi[0] - lo[0], dz = hi[2] - lo[2], cx = (lo[0] + hi[0]) / 2;
          decks.forEach(([x0, z0, x1, z1], d) => {
            let side = null;
            if (lo[2] > z1 - 0.2 && cx > x0 - 0.8 && cx < x1 + 0.8) side = dx > 0.3 && dz < 0.3 ? "S" : "fin";
            else if (dx < 0.3 && dz > 0.3 && lo[2] > z0 - 0.2 && hi[2] < z1 + 1) side = Math.abs(cx - x0) < 0.8 ? "W" : Math.abs(cx - x1) < 0.8 ? "E" : null;
            if (!side) return;
            placements[p.u][i] = zero;
            if (side === "fin") return;
            const e = edges[d + side] || (edges[d + side] = { side, lo: [1e9, 1e9], hi: [-1e9, -1e9], at: [] });
            e.lo = [Math.min(e.lo[0], lo[0]), Math.min(e.lo[1], lo[2])]; e.hi = [Math.max(e.hi[0], hi[0]), Math.max(e.hi[1], hi[2])];
            e.at.push(side === "S" ? (lo[2] + hi[2]) / 2 : cx);
          });
        });
      }
    }
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
    // the terraces' parapets: one solid wall, 0.2 m thick, the length of each edge's panels, in a wall's white
    for (const k in edges) {
      const e = edges[k], at = e.at.reduce((s, a) => s + a, 0) / e.at.length, t = 0.1;
      const g = e.side === "S" ? new T.BoxGeometry(e.hi[0] - e.lo[0], PARAPET, 2 * t) : new T.BoxGeometry(2 * t, PARAPET, e.hi[1] - e.lo[1]);
      g.translate(e.side === "S" ? (e.lo[0] + e.hi[0]) / 2 : at, PARAPET / 2, e.side === "S" ? at : (e.lo[1] + e.hi[1]) / 2);
      g.setAttribute("color", new T.BufferAttribute(new Uint8Array(g.getAttribute("position").count * 3).fill(236), 3, true));
      const mesh = new T.Mesh(g, matOf("wall"));
      G.walls.add(mesh); REG.meshes.push([mesh, "wall"]); ink.push(new T.EdgesGeometry(g, 30));
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
  // the focus: AxoSkp.focus(rings) keeps the model's purples in those outlines (plan mm, y down; holes by even-odd) and turns the
  // rest of them grey (29 Oct: "the only purple theme elements in this axo should be highlighted at each time interval");
  // AxoSkp.focus(null) gives every purple back
  AS.focus = function (rings) {
    if (!M) return;
    FOCUS.u.uFocusOn.value = rings && rings.length ? 1 : 0;
    if (!FOCUS.u.uFocusOn.value) return;
    const cv = FOCUS.cv, c = cv.getContext("2d"), [x0, y0, x1, y1] = FOCUS.box, kx = cv.width / (x1 - x0), ky = cv.height / (y1 - y0);
    c.clearRect(0, 0, cv.width, cv.height); c.fillStyle = "#000"; c.fillRect(0, 0, cv.width, cv.height);
    c.filter = "blur(2px)"; c.fillStyle = "#fff"; c.beginPath();
    for (const r of rings) r.forEach(([x, y], i) => c[i ? "lineTo" : "moveTo"]((x - x0) * kx, (y - y0) * ky));
    c.fill("evenodd"); c.filter = "none";
    FOCUS.u.uFocusMap.value.needsUpdate = true;
  };
  // the day's route as walked on this model (legs re-routed round what the SketchUp model has in the way), or the slide's own
  AS.route = (legs) => (window.AXO_SKP && window.AXO_SKP.route) || legs;
  window.AxoSkp = AS;
})();
