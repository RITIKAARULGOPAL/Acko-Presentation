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
    // the 28.10 changes' own components (the café chair) and their parts, as the model's own
    if (D.changes && D.changes.units && !D.changes.merged) { D.units.push(...D.changes.units); D.parts.push(...D.changes.parts); D.changes.merged = true; }
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
    // the 28.10 plan in the areas its drawings mark as changed (D.changes, tools/acko/axo_skp_28.py; 30 Oct: "this entire portion
    // is wrong.. not as per the latest plan"): the model's furniture in them left out (a component's placements scaled to nothing,
    // a merged part's low pieces cut from its triangles; plants, glass and anything taller than LOW m stay), and the 28.10 pieces
    // added as placements of the model's own components
    const CHG = D.changes, LOW = 1.3, FURN = ["wood", "soft", "hard"];
    const areas = CHG ? CHG.areas.map((r) => r.map(([x, y]) => [X(x), Z(y)])) : [];
    const inArea = (x, z) => areas.some((r) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const [x1, z1] = r[i], [x2, z2] = r[j]; if ((z1 > z) !== (z2 > z) && x < ((x2 - x1) * (z - z1)) / (z2 - z1) + x1) c = !c; } return c; });
    if (CHG) {
      const box = {}, kinds = {};
      for (const p of D.parts) if (p.u >= 0) {
        const b = box[p.u] || (box[p.u] = [[1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]]); (kinds[p.u] = kinds[p.u] || new Set()).add(p.k);
        for (let a = 0; a < 3; a++) { b[0][a] = Math.min(b[0][a], p.lo[a]); b[1][a] = Math.max(b[1][a], p.hi[a]); }
      }
      const zero = new T.Matrix4().makeScale(0, 0, 0), v = new T.Vector3();
      for (const u in box) {
        const ks = [...kinds[u]], [blo, bhi] = box[u];
        if (!ks.every((k) => FURN.includes(k)) || bhi[1] - blo[1] > LOW + 0.3) continue;
        placements[u].forEach((m4, i) => { v.set((blo[0] + bhi[0]) / 2, 0, (blo[2] + bhi[2]) / 2).applyMatrix4(m4); if (inArea(v.x, v.z)) placements[u][i] = zero; });
      }
      for (const [u, i] of CHG.hide || []) placements[u][i] = zero;                 // walls 28.10 doesn't have
      for (const { u, m } of CHG.place) placements[u].push(new T.Matrix4().set(m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10], m[2], m[5], m[8], m[11], 0, 0, 0, 1));
    }
    // a merged part's furniture in the areas: its pieces (triangles joined where they share a corner) that stay under LOW m, have
    // their middle in one and are under BIG m across; a longer one is millwork (the café's counter) and stays
    const BIG = 3.2;
    const cut = (g) => {
      const pos = g.getAttribute("position").array, ix = g.getIndex().array, n = ix.length / 3, cand = [], up = new Int32Array(n).fill(-1);
      const find = (a) => { while (up[a] >= 0 && up[up[a]] >= 0) { up[a] = up[up[a]]; a = up[a]; } return up[a] >= 0 ? up[a] : a; };
      const at = new Map(), key = (v) => Math.round(pos[v] * 200) + "," + Math.round(pos[v + 1] * 200) + "," + Math.round(pos[v + 2] * 200);
      for (let t = 0; t < n; t++) {
        const a = ix[3 * t] * 3, b = ix[3 * t + 1] * 3, c = ix[3 * t + 2] * 3;
        if (Math.max(pos[a + 1], pos[b + 1], pos[c + 1]) >= LOW) continue;
        if (!inArea((pos[a] + pos[b] + pos[c]) / 3, (pos[a + 2] + pos[b + 2] + pos[c + 2]) / 3)) continue;
        cand.push(t);
        for (const v of [a, b, c]) { const k = key(v), o = at.get(k); if (o === undefined) at.set(k, t); else { const r1 = find(o), r2 = find(t); if (r1 !== r2) up[r2] = r1; } }
      }
      const box = new Map();
      for (const t of cand) { const r = find(t), b = box.get(r) || [1e9, 1e9, -1e9, -1e9];
        for (let j = 0; j < 3; j++) { const v = ix[3 * t + j] * 3; b[0] = Math.min(b[0], pos[v]); b[1] = Math.min(b[1], pos[v + 2]); b[2] = Math.max(b[2], pos[v]); b[3] = Math.max(b[3], pos[v + 2]); }
        box.set(r, b); }
      const drop = new Uint8Array(n);
      for (const t of cand) { const b = box.get(find(t)); if (Math.max(b[2] - b[0], b[3] - b[1]) < BIG) drop[t] = 1; }
      const keep = []; for (let t = 0; t < n; t++) if (!drop[t]) keep.push(ix[3 * t], ix[3 * t + 1], ix[3 * t + 2]);
      if (keep.length < ix.length) g.setIndex(new T.BufferAttribute(new ix.constructor(keep), 1));
    };
    const fine = [], coarse = [], lo = new T.Vector3(1e9, 1e9, 1e9), hi = new T.Vector3(-1e9, -1e9, -1e9), ink = [];
    for (const [pi, p] of D.parts.entries()) {
      const g = geometry(p), mat = matOf(p.k);
      if (CHG && p.u < 0 && FURN.includes(p.k)) cut(g);
      if (CHG && p.u < 0 && CHG.drop && CHG.drop[pi]) {                        // walls 28.10 doesn't have
        const ix = g.getIndex().array, out = new Uint8Array(ix.length / 3); for (const [t0, t1] of CHG.drop[pi]) out.fill(1, t0, t1);
        const keep = []; for (let t = 0; t < out.length; t++) if (!out[t]) keep.push(ix[3 * t], ix[3 * t + 1], ix[3 * t + 2]);
        g.setIndex(new T.BufferAttribute(new ix.constructor(keep), 1));
      }
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
    // the 28.10 plan's plain tables (CHG.tables: the model has none): a 40 mm top at 0.75 m on four legs, white
    if (CHG && CHG.tables && CHG.tables.length) {
      const pos = [], m4 = new T.Matrix4(), q = new T.Quaternion(), Y = new T.Vector3(0, 1, 0);
      const box = (w, h, d, x, y, z, M4) => { const b = new T.BoxGeometry(w, h, d).toNonIndexed(); b.translate(x, y, z); b.applyMatrix4(M4); pos.push(...b.getAttribute("position").array); };
      for (const [x, y, w, d, a] of CHG.tables) {
        const W_ = w / 1000, D_ = d / 1000; m4.compose(new T.Vector3(X(x), 0, Z(y)), q.setFromAxisAngle(Y, -a * Math.PI / 180), new T.Vector3(1, 1, 1));
        box(W_, 0.04, D_, 0, 0.73, 0, m4);
        for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(0.05, 0.71, 0.05, sx * (W_ / 2 - 0.06), 0.355, sz * (D_ / 2 - 0.06), m4);
      }
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
      g.setAttribute("color", new T.BufferAttribute(new Uint8Array(pos.length).fill(240), 3, true)); g.computeVertexNormals();
      const uv = new Float32Array((pos.length / 3) * 2); for (let i = 0, j = 0; i < pos.length; i += 3, j += 2) { uv[j] = pos[i]; uv[j + 1] = pos[i + 2]; }
      g.setAttribute("uv", new T.BufferAttribute(uv, 2));
      const mesh = new T.Mesh(g, matOf("wood")); G.furniture.add(mesh); REG.meshes.push([mesh, "wood"]);
    }
    // the 28.10 plan's fit-out walls, in place of the model's (CHG.walls, plan mm: outlines with their holes; 30 Oct: "wall
    // terminations are not fine// also z fighting is happening"): walls and partitions in a wall's white, glass in the model's
    // glass, each to its height (CHG.heights), edged in the ink
    if (CHG && CHG.walls) {
      const HT = CHG.heights || { wall: 3.7, solid: 2.4, glass: 2.4 };
      for (const [ty, rgb] of [["wall", [232, 230, 226]], ["solid", [232, 230, 226]], ["glass", [95, 78, 107]]]) {
        const h = HT[ty];
        const geos = [];
        for (const poly of CHG.walls[ty] || []) {
          const sh = new T.Shape(poly[0].map(([x, y]) => new T.Vector2(X(x), -Z(y))));
          for (const hole of poly.slice(1)) sh.holes.push(new T.Path(hole.map(([x, y]) => new T.Vector2(X(x), -Z(y)))));
          const e = new T.ExtrudeGeometry(sh, { depth: h, bevelEnabled: false }); e.rotateX(-Math.PI / 2); geos.push(e);
        }
        if (!geos.length) continue;
        const pos = []; for (const e of geos) { const q = e.index ? e.toNonIndexed() : e; pos.push(...q.getAttribute("position").array); }
        const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3)); g.computeVertexNormals();
        const col = new Uint8Array(pos.length); for (let i = 0; i < col.length; i += 3) col.set(rgb, i);
        g.setAttribute("color", new T.BufferAttribute(col, 3, true));
        const uv = new Float32Array((pos.length / 3) * 2); for (let i = 0, j = 0; i < pos.length; i += 3, j += 2) { uv[j] = pos[i]; uv[j + 1] = pos[i + 1]; }
        g.setAttribute("uv", new T.BufferAttribute(uv, 2));
        // their own material, as the kind's, casting from the back faces only: closed solids, so the faces the sun meets don't
        // shade themselves (30 Oct: the stripes on the new walls)
        const kind = ty === "glass" ? "glass" : "wall";
        const own = mats[kind + "28"] || (mats[kind + "28"] = reg(focusable(new T.MeshLambertMaterial(kind === "glass"
          ? { color: 0xffffff, vertexColors: true, flatShading: true, transparent: true, opacity: 0.35, depthWrite: false, side: T.DoubleSide, shadowSide: T.BackSide }
          : { color: 0xffffff, vertexColors: true, flatShading: true, side: T.DoubleSide, shadowSide: T.BackSide }), kind), kind, true));
        const mesh = new T.Mesh(g, own); if (ty === "glass") mesh.renderOrder = 2;
        (ty === "glass" ? G.glass : G.walls).add(mesh); REG.meshes.push([mesh, ty === "glass" ? "glass" : "wall"]); ink.push(new T.EdgesGeometry(g, 30));
      }
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
