/* TwinSite — Sattva Hallmark in its street, inside the twin.
   Context massing (OSM), the two Hallmark blocks, the glazed atrium and the
   entrance canopy, the metro viaduct and street trees. Every façade is dark
   grey reflective glass except Mitigata's Level 03, which is clear: through it
   you see the twin's own floor (the real layout), under a lit ceiling, with
   the SOC's halo hung over the SOC zone. Geometry comes in twin coordinates
   from data/site-data.js (Level 03 slab top at y = 0).
   Attach with twin.attachSite(new TwinSite(twin)). */
(function () {
  const S = window.MX_SITE, D = window.MX_DATA, T = window.THREE;
  if (!S || !D || !T) return;
  const CX = 42000, CY = 17500, mx = (x) => (x - CX) / 1000, mz = (y) => -(y - CY) / 1000;
  const G0 = -S.slabZ;                       // ground level in twin y

  const PAL = {
    dark: { ground: "#0e1513", road: "#1f2b27", roadMajor: "#26342f", path: "#18221e", green: "#132419", water: "#10202a",
      mass: 0x2b3934, massEdge: 0x4f8a72, massEdgeOp: 0.6, roof: 0x1c2522, spandrel: [0.09, 0.11, 0.105],
      sky: [[0.09, 0.1, 0.12], [0.3, 0.33, 0.38]],
      tree: 0x5d7a6a, leaf: 0x4f6e5c, rail: 0x6f8a80,
      court: { frame: 0x8f9a96, panel: 0x4a5652, panelOp: 0.6, column: 0x9ea9a5, paving: 0x242c29, planter: 0x3a4440, shrub: 0x2b4c34, water: 0x1f3a46, bridge: 0x57534b },
      glassBody: [0.15, 0.16, 0.18], frame: [0.25, 0.26, 0.28], ceiling: 0x9a978f },
    light: { ground: "#ecebe8", road: "#dedcd8", roadMajor: "#d5d3cf", path: "#e5e3df", green: "#e1e6dc", water: "#dde6ea",
      mass: 0xfbfbfa, massEdge: 0x8e8f8b, massEdgeOp: 0.6, roof: 0xf4f4f2, spandrel: [0.62, 0.66, 0.68],
      sky: [[0.62, 0.72, 0.8], [0.88, 0.9, 0.9]],
      tree: 0xffffff, leaf: 0xe6ecdf, rail: 0x5a5d5f,
      court: { frame: 0xf2f2f0, panel: 0xffffff, panelOp: 0.62, column: 0xeeeeec, paving: 0xd8d7d3, planter: 0xb9b7b1, shrub: 0x3f6236, water: 0x9cc2ce, bridge: 0xe4dac4 },
      glassBody: [0.16, 0.175, 0.19], frame: [0.27, 0.285, 0.3], ceiling: 0xd8d4ca },
  };

  /* ---------------- façade shader ----------------
     Dark grey reflective glass with mullions and floor bands; Level 03's vision
     glass is clear so the real floor behind it shows. */
  const FACADE_VS = `
    attribute vec3 aN;
    varying vec3 vWorld; varying vec2 vUv; varying vec3 vN;
    void main() {
      vUv = uv; vN = aN;
      vec4 w = modelMatrix * vec4(position, 1.0); vWorld = w.xyz;
      gl_Position = projectionMatrix * viewMatrix * w;
    }`;
  const FACADE_FS = `
    uniform vec3 camPos; uniform float ftf; uniform float ourRow; uniform float cutV; uniform float ceilV;
    uniform vec3 skyLo; uniform vec3 skyHi; uniform vec3 glassBody; uniform vec3 frame;
    uniform float fogNear; uniform float fogFar; uniform vec3 fogColor;
    varying vec3 vWorld; varying vec2 vUv; varying vec3 vN;
    float hash(float n) { return fract(sin(n) * 43758.5453); }
    void main() {
      if (vUv.y > cutV) discard;
      float row = floor(vUv.y / ftf), fv = vUv.y - row * ftf;
      vec3 V = normalize(vWorld - camPos), N = normalize(vN);
      float F = 0.04 + 0.96 * pow(1.0 - abs(dot(V, N)), 5.0);
      vec3 R = reflect(V, N);
      vec3 sky = mix(skyLo, skyHi, clamp(R.y * 1.4 + 0.4, 0.0, 1.0));
      // floor band (slab edge + upstand), mullions every 1.5 m
      float band = step(fv, 0.75);
      float mul = step(fract(vUv.x / 1.5), 0.03);
      bool ours = abs(row - ourRow) < 0.5;
      // our floor's glass stops at its suspended ceiling; above it, up to the next slab, an opaque spandrel
      if (ours && fv > ceilV) band = 1.0;
      vec3 col; float alpha = 1.0;
      if (band > 0.5) { col = frame * (ours ? 1.25 : 0.85); }
      else if (ours) {
        // Level 03: clear glass, a little sky at grazing angles, mullions as fine lines
        col = mix(sky, frame, mul); alpha = max(mul * 0.85, 0.05 + min(F, 0.5) * 0.3);   // stays see-through even at grazing angles
      } else {
        // each 1.5 m panel reflects a little differently, as real curtain-wall glass does
        float pv = hash(floor(vUv.x / 1.5) * 12.9898 + row * 78.233);
        col = mix(glassBody * (0.9 + 0.2 * pv), sky, 0.18 + F * 0.7);
        col = mix(col, frame, mul * 0.85);
      }
      float fd = smoothstep(fogNear, fogFar, length(vWorld - camPos));
      gl_FragColor = vec4(mix(col, fogColor, fd), alpha);
    }`;

  class TwinSite {
    constructor(twin) {
      this.twin = twin;
      this.group = new T.Group(); this.group.visible = false;
      this.theme = "dark"; this.night = 0; this.opt = "opt1";
      this.mats = { mass: [], edges: [] };
      this.buildGround(); this.buildContext(); this.buildViaduct(); this.buildHallmark(); this.buildTrees();
      twin.scene.add(this.group);
    }

    /* ---------- helpers ---------- */
    shape(rings) {
      // twin (x, z) -> shape (x, -z) so that rotating -90 deg about x lands it back on (x, z)
      const s = new T.Shape(rings[0].map(([x, z]) => new T.Vector2(x, -z)));
      for (const h of rings.slice(1)) s.holes.push(new T.Path(h.map(([x, z]) => new T.Vector2(x, -z))));
      return s;
    }
    prism(rings, y0, h) {
      const g = new T.ExtrudeGeometry(this.shape(rings), { depth: h, bevelEnabled: false });
      g.rotateX(-Math.PI / 2); g.translate(0, y0, 0);
      return g;
    }
    // flat-shaded massing: bake a soft directional shade into vertex colours, tint by material colour
    shaded(g) {
      g = g.toNonIndexed(); g.computeVertexNormals();
      const n = g.getAttribute("normal"), c = [];
      const L = new T.Vector3(-0.45, 0.8, 0.4).normalize();
      for (let i = 0; i < n.count; i++) {
        const k = 0.72 + 0.28 * Math.max(0, n.getX(i) * L.x + n.getY(i) * L.y + n.getZ(i) * L.z);
        c.push(k, k, k);
      }
      g.setAttribute("color", new T.Float32BufferAttribute(c, 3));
      return g;
    }
    massMesh(g, opacity) {
      const m = new T.Mesh(this.shaded(g), new T.MeshBasicMaterial({ vertexColors: true, transparent: opacity < 1, opacity }));
      this.mats.mass.push(m.material);
      const e = new T.LineSegments(new T.EdgesGeometry(g, 25), new T.LineBasicMaterial({ transparent: true, opacity: 0.5 }));
      e.userData.op = opacity; this.mats.edges.push(e.material);
      return [m, e];
    }

    /* ---------- ground: roads / green / water painted on one canvas ---------- */
    buildGround() {
      const R = S.R, N = 4096;
      this.groundCanvas = document.createElement("canvas"); this.groundCanvas.width = this.groundCanvas.height = N;
      this.groundTex = new T.CanvasTexture(this.groundCanvas); this.groundTex.anisotropy = 8;
      const [cx, cz] = S.centre;
      const m = new T.Mesh(new T.CircleGeometry(R, 128), new T.MeshBasicMaterial({ map: this.groundTex, transparent: true }));
      m.rotation.x = -Math.PI / 2; m.position.set(cx, G0, cz);
      // the disc's local +y maps to world -z; the canvas is painted in that frame
      m.material.onBeforeCompile = (sh) => {
        sh.fragmentShader = sh.fragmentShader.replace("#include <dithering_fragment>",
          "#include <dithering_fragment>\n float rr = length(vUv - 0.5) * 2.0; gl_FragColor.a *= 1.0 - smoothstep(0.8, 1.0, rr);");
      };
      this.ground = m; this.group.add(m);
    }
    paintGround() {
      const P = PAL[this.theme], N = this.groundCanvas.width, g = this.groundCanvas.getContext("2d"), R = S.R;
      const [cx, cz] = S.centre, s = N / (2 * R);
      // disc rotated -90 deg about x: local +y = world -z; with flipY off, canvas row 0 = uv v 0 = local -y
      const X = (x) => (x - cx + R) * s, Y = (z) => (cz - z + R) * s;
      g.fillStyle = P.ground; g.fillRect(0, 0, N, N);
      const fill = (polys, col) => {
        g.fillStyle = col;
        for (const rings of polys) {
          g.beginPath();
          for (const r of rings) { r.forEach(([x, z], i) => (i ? g.lineTo : g.moveTo).call(g, X(x), Y(z))); g.closePath(); }
          g.fill("evenodd");
        }
      };
      fill(S.green, P.green); fill(S.water, P.water);
      fill(S.roads.path, P.path); fill(S.roads.minor, P.road); fill(S.roads.major, P.roadMajor);
      this.groundTex.flipY = false; this.groundTex.needsUpdate = true;
    }

    /* ---------- context ---------- */
    buildContext() {
      this.context = new T.Group(); this.group.add(this.context);
      const [cx, cz] = S.centre;
      for (const b of S.buildings) {
        const c = b.r.reduce((a, p) => [a[0] + p[0] / b.r.length, a[1] + p[1] / b.r.length], [0, 0]);
        const fade = Math.min(1, Math.max(0, (Math.hypot(c[0] - cx, c[1] - cz) - S.R * 0.5) / (S.R * 0.45)));
        const [m, e] = this.massMesh(this.prism([b.r], G0, b.h), 1 - fade * 0.8);
        this.context.add(m, e);
      }
    }
    buildViaduct() {
      const V = S.viaduct; this.metro = new T.Group(); this.group.add(this.metro);
      for (const rings of V.deck) {
        const [m, e] = this.massMesh(this.prism(rings, G0 + V.deck_bottom, V.deck_top - V.deck_bottom + V.parapet), 1);
        this.metro.add(m, e);
      }
      for (const [x, z, a] of V.piers) {
        const grp = new T.Group();
        const pier = new T.Mesh(this.shaded(new T.CylinderGeometry(V.pier_r, V.pier_r * 1.1, V.deck_bottom, 16).translate(0, V.deck_bottom / 2, 0)), new T.MeshBasicMaterial({ vertexColors: true }));
        const cap = new T.Mesh(this.shaded(new T.BoxGeometry(2.4, 1.4, V.half_width * 2 + 2.6).translate(0, V.deck_bottom - 0.7, 0)), new T.MeshBasicMaterial({ vertexColors: true }));
        this.mats.mass.push(pier.material, cap.material);
        grp.add(pier, cap); grp.position.set(x, G0, z); grp.rotation.y = a;
        this.metro.add(grp);
      }
    }

    /* ---------- street trees (traced from the satellite still) ---------- */
    // merge geometries (each with a flat colour or its own vertex colours) into one non-indexed geometry
    merge(parts) {
      const pos = [], col = [];
      for (const [g0, c] of parts) {
        const g = g0.index ? g0.toNonIndexed() : g0;
        const P = g.getAttribute("position"), C = g.getAttribute("color");
        for (let i = 0; i < P.count; i++) {
          pos.push(P.getX(i), P.getY(i), P.getZ(i));
          if (C) col.push(C.getX(i), C.getY(i), C.getZ(i)); else col.push(c[0], c[1], c[2]);
        }
      }
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
      g.setAttribute("color", new T.Float32BufferAttribute(col, 3));
      g.computeVertexNormals();
      return g;
    }
    // shade a geometry's faces from above (lighter tops, darker undersides) in a base colour
    lit(g, base, lo = 0.62, hi = 1.12) {
      g = g.toNonIndexed(); g.computeVertexNormals();
      const n = g.getAttribute("normal"), c = [];
      for (let i = 0; i < n.count; i++) { const k = lo + (hi - lo) * (0.5 + 0.5 * n.getY(i)); c.push(base[0] * k, base[1] * k, base[2] * k); }
      g.setAttribute("color", new T.Float32BufferAttribute(c, 3));
      return g;
    }
    // a limb from a to b (unit tree space)
    limb(a, b, r0, r1) {
      const d = new T.Vector3().subVectors(b, a), L = d.length();
      const g = new T.CylinderGeometry(r1, r0, L, 5).translate(0, L / 2, 0);
      g.applyQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize()));
      return g.translate(a.x, a.y, a.z);
    }
    /* a leaf-cluster sprite (alpha-cut): many small leaves in mixed greens, drawn once on a canvas */
    leafTexture() {
      const N = 256, cv = document.createElement("canvas"); cv.width = cv.height = N;
      const g = cv.getContext("2d");
      let s = 97; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      const greens = ["#2f5a26", "#3d6b2c", "#4a7a33", "#5a8a3a", "#6f9a45", "#86ab55", "#9bb862"];
      for (let i = 0; i < 9; i++) {                                   // a few twigs under the leaves
        g.strokeStyle = "rgba(80,62,44,0.9)"; g.lineWidth = 2;
        g.beginPath(); g.moveTo(N / 2, N / 2); g.lineTo(N / 2 + (rnd() - 0.5) * N * 0.8, N / 2 + (rnd() - 0.5) * N * 0.8); g.stroke();
      }
      for (let i = 0; i < 150; i++) {
        const a = rnd() * Math.PI * 2, d = Math.sqrt(rnd()) * N * 0.42;
        const x = N / 2 + Math.cos(a) * d, y = N / 2 + Math.sin(a) * d;
        g.save(); g.translate(x, y); g.rotate(rnd() * Math.PI);
        g.fillStyle = greens[Math.floor(rnd() * greens.length)];
        g.beginPath(); g.ellipse(0, 0, 8 + rnd() * 9, 3.5 + rnd() * 4, 0, 0, Math.PI * 2); g.fill();
        g.restore();
      }
      const t = new T.CanvasTexture(cv); t.anisotropy = 4;
      return t;
    }
    /* merge cards (position, uv, colour) into one geometry */
    mergeCards(cards) {
      const pos = [], uv = [], col = [];
      for (const [g0, c] of cards) {
        const g = g0.index ? g0.toNonIndexed() : g0, P = g.getAttribute("position"), U = g.getAttribute("uv");
        for (let i = 0; i < P.count; i++) { pos.push(P.getX(i), P.getY(i), P.getZ(i)); uv.push(U.getX(i), U.getY(i)); col.push(c[0], c[1], c[2]); }
      }
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
      g.setAttribute("uv", new T.Float32BufferAttribute(uv, 2));
      g.setAttribute("color", new T.Float32BufferAttribute(col, 3));
      return g;
    }
    /* a crown of leaf cards packed into a few overlapping lobes; shaded lighter at the top and the outside */
    crownCards(rnd, lobes, n, size, base) {
      const cards = [], up = new T.Vector3(), e = new T.Euler(), qr = new T.Quaternion();
      let ymin = 1e9, ymax = -1e9;
      lobes.forEach((l) => { ymin = Math.min(ymin, l.c.y - l.ry); ymax = Math.max(ymax, l.c.y + l.ry); });
      for (let i = 0; i < n; i++) {
        const l = lobes[Math.floor(rnd() * lobes.length)];
        up.set(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1).normalize();
        const f = 0.5 + 0.5 * Math.sqrt(rnd());                     // mostly towards the lobe's surface
        const x = l.c.x + up.x * l.rx * f, y = l.c.y + up.y * l.ry * f, z = l.c.z + up.z * l.rx * f;
        const sz = size * (0.75 + rnd() * 0.5);
        const g = new T.PlaneGeometry(sz, sz);
        g.applyQuaternion(qr.setFromEuler(e.set(rnd() * Math.PI, rnd() * Math.PI, rnd() * Math.PI)));
        g.translate(x, y, z);
        const hgt = (y - ymin) / (ymax - ymin || 1), out = f;
        const k = 0.55 + 0.4 * hgt + 0.2 * out, j = (rnd() - 0.5) * 0.12;
        cards.push([g, [base[0] * k + j * 0.6, base[1] * k + j, base[2] * k]]);
      }
      return this.mergeCards(cards);
    }
    /* broadleaf street tree in metres (scaled evenly per tree): trunk, limbs and a crown of leaf cards.
       R0/H0: crown radius and height of this variant; n: cards (density). As in Street View on the
       service road: rain-tree / copper-pod canopies, broad and irregular, trunk clear for the first third. */
    broadleaf(seed, R0, H0, n) {
      let s = seed; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      const BARK = [0.36, 0.32, 0.27], wood = [];
      const fork = new T.Vector3((rnd() - 0.5) * 0.4, H0 * (0.36 + rnd() * 0.08), (rnd() - 0.5) * 0.4);
      wood.push([this.lit(this.limb(new T.Vector3(0, 0, 0), fork, 0.3 * R0 / 5, 0.22 * R0 / 5), BARK, 0.7, 1.0), null]);
      const nb = 4 + Math.floor(rnd() * 3), lobes = [];
      for (let i = 0; i < nb; i++) {
        const a = (i / nb) * Math.PI * 2 + rnd() * 0.7, rr = R0 * (0.35 + rnd() * 0.3);
        const tip = new T.Vector3(fork.x + Math.cos(a) * rr, H0 * (0.58 + rnd() * 0.14), fork.z + Math.sin(a) * rr);
        wood.push([this.lit(this.limb(fork, tip, 0.15 * R0 / 5, 0.06 * R0 / 5), BARK, 0.7, 1.0), null]);
        lobes.push({ c: tip.clone().add(new T.Vector3(0, H0 * 0.08, 0)), rx: R0 * (0.45 + rnd() * 0.15), ry: H0 * (0.16 + rnd() * 0.06) });
      }
      lobes.push({ c: new T.Vector3(fork.x, H0 * 0.8, fork.z), rx: R0 * 0.55, ry: H0 * 0.17 });   // the crown's top
      const t = rnd() * 0.08;
      return { wood: this.merge(wood), leaves: this.crownCards(rnd, lobes, n, 1.9 * R0 / 5, [0.72 + t, 0.86, 0.62]), R0, H0 };
    }
    /* a shrub: a small ball of leaf cards (boundary hedge, understorey) */
    bush(seed) {
      let s = seed; const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      const lobes = [{ c: new T.Vector3(0, 0.75, 0), rx: 0.9, ry: 0.7 }, { c: new T.Vector3(0.4, 0.6, 0.2), rx: 0.6, ry: 0.55 }];
      return this.crownCards(rnd, lobes, 30, 0.85, [0.7, 0.88, 0.6]);
    }
    /* fan palm (Washingtonia, as on the island and the ORR separator), in two parts so the crown keeps its
       shape: a trunk in unit height (instances stretch it to the palm's height) and a crown of radius ~1
       around the origin (instances scale it evenly and lift it to the top of the trunk) */
    palm() {
      const trunk = this.merge([[new T.CylinderGeometry(0.09, 0.12, 1, 8).translate(0, 0.5, 0), [0.42, 0.37, 0.31]]]);
      const parts = [[this.lit(new T.CylinderGeometry(0.32, 0.2, 0.7, 10).translate(0, -0.35, 0), [0.45, 0.38, 0.26]), null]];  // skirt of dead fronds
      for (let i = 0; i < 22; i++) {
        const a = (i / 22) * Math.PI * 2 + (i % 2) * 0.14, droop = -0.15 - (i % 4) * 0.2;
        const g = new T.CircleGeometry(0.85, 10, -0.7, 1.4);        // a fan: a sector of a disc
        g.rotateZ(-Math.PI / 2); g.rotateX(-Math.PI / 2 + 0.05); g.rotateZ(droop);
        g.translate(0.12, 0.05, 0); g.rotateY(a);
        parts.push([this.lit(g, [0.24, 0.42, 0.22], 0.75, 1.1), null]);
      }
      return { trunk, crown: this.merge(parts) };
    }
    buildTrees() {
      this.trees = new T.Group(); this.group.add(this.trees);   // root of everything "Trees" hides
      this.treeMat = new T.MeshBasicMaterial({ vertexColors: true, side: T.DoubleSide });            // wood, palms
      this.leafMat = new T.MeshBasicMaterial({ vertexColors: true, side: T.DoubleSide, map: this.leafTexture(), alphaTest: 0.45 });
      this.treeGeo = {
        variants: [this.broadleaf(11, 5.0, 11.0, 170), this.broadleaf(23, 4.2, 9.5, 120), this.broadleaf(37, 4.6, 10.5, 150), this.broadleaf(51, 3.8, 9.0, 100)],
        palm: this.palm(),
      };
      this.treeMeshes = new T.Group(); this.trees.add(this.treeMeshes);
      if (this.courtPalms && !this._courtPalmsAdded) { S.trees.push(...this.courtPalms); this._courtPalmsAdded = true; }
      this.placeTrees(S.trees.map((t, i) => [...t, i]));
      this.buildForecourt();
    }
    /* a broadleaf tree's even scale and crown, from its crown radius on the satellite */
    treeScale(t) { const v = this.treeGeo.variants[t[5] % this.treeGeo.variants.length]; return { v, k: Math.max(2.6, Math.min(6.5, t[2])) / v.R0 }; }
    /* trees as [x, z, crown radius, height, palm?, original index] */
    placeTrees(list) {
      for (const o of [...this.treeMeshes.children]) { this.treeMeshes.remove(o); o.dispose(); }
      const V = this.treeGeo.variants, buckets = V.map(() => []), palms = [];
      list.forEach((t) => (t[4] ? palms : buckets[t[5] % V.length]).push(t));    // variant follows the tree, wherever it stands
      const m = new T.Matrix4(), q = new T.Quaternion(), sc = new T.Vector3(), p = new T.Vector3(), up = new T.Vector3(0, 1, 0), c = new T.Color();
      const add = (im) => { im.userData.veg = true; im.visible = this.treesOn !== false; this.treeMeshes.add(im); };
      V.forEach((v, vi) => {
        const items = buckets[vi]; if (!items.length) return;
        const wood = new T.InstancedMesh(v.wood, this.treeMat, items.length), leaves = new T.InstancedMesh(v.leaves, this.leafMat, items.length);
        items.forEach((t, i) => {
          const [x, z, , , , idx] = t, { k } = this.treeScale(t), j = ((idx * 0.618034) % 1 + 1) % 1;   // stable per-tree jitter
          q.setFromAxisAngle(up, j * Math.PI * 2);
          m.compose(p.set(x, G0, z), q, sc.set(k, k * (0.92 + j * 0.16), k));
          wood.setMatrixAt(i, m); leaves.setMatrixAt(i, m);
          // every instanced mesh on these materials carries instance colours (else the shader reads black)
          wood.setColorAt(i, c.setRGB(1, 1, 1)); leaves.setColorAt(i, c.setRGB(0.9 + j * 0.18, 0.92 + j * 0.12, 0.88 + j * 0.06));
        });
        add(wood); add(leaves);
      });
      // palms: trunk stretched to height, crown scaled evenly on top
      if (palms.length) {
        const tr = new T.InstancedMesh(this.treeGeo.palm.trunk, this.treeMat, palms.length), cr = new T.InstancedMesh(this.treeGeo.palm.crown, this.treeMat, palms.length);
        palms.forEach(([x, z, r, h, , idx], i) => {
          const j = ((idx * 0.618034) % 1 + 1) % 1;
          q.setFromAxisAngle(up, j * Math.PI * 2);
          m.compose(p.set(x, G0, z), q, sc.set(r * 0.9, h, r * 0.9)); tr.setMatrixAt(i, m); tr.setColorAt(i, c.setRGB(1, 1, 1));
          m.compose(p.set(x, G0 + h, z), q, sc.set(r * 0.9, r * 0.9, r * 0.9)); cr.setMatrixAt(i, m);
          cr.setColorAt(i, c.setRGB(0.9 + j * 0.15, 0.9 + j * 0.12, 0.88));
        });
        add(tr); add(cr);
      }
    }
    /* keep the chapter's views clear: any tree whose crown sits in a view's line of sight to that option's
       SOC glazing slides sideways out of the sight cone to the nearest free spot (not on a road, a building,
       the atrium or the canopy; palms stay on the forecourt island) -- or goes, if there is none.
       views: [{eye: [x, y, z], opt}] in twin coordinates. */
    keepClear(views) {
      const key = JSON.stringify(views);
      if (key === this._clearKey) return this.clearStats;
      this._clearKey = key;
      const east = S.blocks.find((b) => b.mitigata);
      const sight = views.map(({ eye, opt }) => {
        const segs = [];
        for (const run of S.soc[opt] || []) {
          const fa = east.facades[run.edge], L = fa.len, tx = (fa.b[0] - fa.a[0]) / L, tz = (fa.b[1] - fa.a[1]) / L;
          const n = Math.max(3, Math.ceil((run.u1 - run.u0) / 2.5));
          for (let i = 0; i <= n; i++) {
            const u = run.u0 + ((run.u1 - run.u0) * i) / n;
            for (const y of [1.0, 2.2, 3.4]) segs.push([eye, [fa.a[0] + tx * u + fa.n[0] * 0.3, y, fa.a[1] + tz * u + fa.n[1] * 0.3]]);
          }
        }
        // the cone's axis in plan, for the sideways push
        const cx = segs.reduce((a, s_) => a + s_[1][0], 0) / segs.length, cz = segs.reduce((a, s_) => a + s_[1][2], 0) / segs.length;
        const ax = cx - eye[0], az = cz - eye[2], al = Math.hypot(ax, az) || 1;
        return { segs, perp: [-az / al, ax / al] };
      });
      // does a crown at (x, z) sit in a sight line? crown = a cylinder of radius rc between heights yb and yt
      // crown = a cylinder of radius rc between heights yb and yt, as the tree is drawn
      const crown = (t) => {
        const [, , r, h, palm] = t;
        if (palm) return [r * 0.85, G0 + h - 0.75 * r, G0 + h + 0.35 * r];
        const { v, k } = this.treeScale(t);
        return [v.R0 * k * 1.15, G0 + v.H0 * k * 0.4, G0 + v.H0 * k * 1.02];
      };
      const blocks = (x, z, t) => {
        const [rc, yb, yt] = crown(t), R = rc + 0.4;
        for (let v = 0; v < sight.length; v++) for (const [E, P] of sight[v].segs) {
          const dx = P[0] - E[0], dz = P[2] - E[2], fx = E[0] - x, fz = E[2] - z;
          const a = dx * dx + dz * dz, b = 2 * (fx * dx + fz * dz), c = fx * fx + fz * fz - R * R, disc = b * b - 4 * a * c;
          if (disc < 0 || a < 1e-9) continue;
          const sq = Math.sqrt(disc), t0 = Math.max(0, (-b - sq) / (2 * a)), t1 = Math.min(1, (-b + sq) / (2 * a));
          if (t0 > t1) continue;
          const y0 = E[1] + t0 * (P[1] - E[1]), y1 = E[1] + t1 * (P[1] - E[1]);
          if (Math.max(y0, y1) >= yb - 0.3 && Math.min(y0, y1) <= yt + 0.3) return v;
        }
        return -1;
      };
      const inRing = (x, z, r) => {
        let c = false;
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const [xi, zi] = r[i], [xj, zj] = r[j];
          if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c;
        }
        return c;
      };
      const solids = [...S.blocks.map((b) => b.ring), ...S.buildings.map((b) => b.r), S.atrium.ring, S.canopy.ring];
      const roads = [...(S.roads.major || []), ...(S.roads.minor || [])];
      const island = S.gate && S.gate.island;
      const free = (x, z, r, palm) => {
        if (palm) return island && Math.hypot(x - island[0], z - island[1]) < 7;
        for (const [ox, oz] of [[0, 0], [r * 0.6, 0], [-r * 0.6, 0], [0, r * 0.6], [0, -r * 0.6]])
          if (solids.some((ring) => inRing(x + ox, z + oz, ring))) return false;
        return !roads.some((poly) => inRing(x, z, poly[0]) && !poly.slice(1).some((hole) => inRing(x, z, hole)));
      };
      let moved = 0, removed = 0;
      const out = [];
      S.trees.forEach((t, idx) => {
        const [x, z, r, h, palm] = t;
        const v = blocks(x, z, [...t, idx]);
        if (v < 0) { out.push([...t, idx]); return; }
        const [px, pz] = sight[v].perp;
        for (let d = 1; d <= 24; d += 0.75) for (const sgn of [1, -1]) {
          const nx = x + px * d * sgn, nz = z + pz * d * sgn;
          if (free(nx, nz, r, palm) && blocks(nx, nz, [nx, nz, r, h, palm, idx]) < 0) { out.push([nx, nz, r, h, palm, idx]); moved++; return; }
        }
        removed++;
      });
      this.placeTrees(out);
      return (this.clearStats = { moved, removed, kept: out.length - moved });
    }
    /* the forecourt at the gate: planter island + signage totem, security kiosk, boom barrier, boundary hedge + railing */
    buildForecourt() {
      const F = S.gate; if (!F) return;
      const grp = new T.Group(); this.trees.add(grp);
      this.fcMats = { solid: new T.MeshBasicMaterial({ vertexColors: true }), rail: new T.LineBasicMaterial({ transparent: true, opacity: 0.8 }) };
      const solid = (g, col) => { const m = new T.Mesh(this.lit(g, col, 0.7, 1.05), this.fcMats.solid); grp.add(m); return m; };
      const [ix, iz] = F.island;
      solid(new T.CylinderGeometry(4.6, 4.8, 0.45, 28).scale(1.4, 1, 0.8).translate(ix, G0 + 0.22, iz), [0.55, 0.53, 0.5]);
      solid(new T.CylinderGeometry(4.3, 4.3, 0.5, 28).scale(1.4, 1, 0.8).translate(ix, G0 + 0.3, iz), [0.25, 0.4, 0.2]);
      solid(new T.BoxGeometry(1.1, 5.2, 0.5).translate(ix, G0 + 2.6, iz), [0.2, 0.21, 0.22]);           // totem
      const [kx, kz] = F.kiosk;
      solid(new T.BoxGeometry(3.2, 2.7, 2.4).translate(kx, G0 + 1.35, kz), [0.72, 0.72, 0.7]);           // kiosk
      solid(new T.BoxGeometry(3.8, 0.25, 3.0).translate(kx, G0 + 2.8, kz), [0.45, 0.46, 0.47]);
      // boom barrier: red and white bands
      const [b0, b1] = F.barrier, bl = Math.hypot(b1[0] - b0[0], b1[1] - b0[1]), seg = 6;
      for (let i = 0; i < seg; i++) {
        const t0 = i / seg, t1 = (i + 1) / seg;
        const a = new T.Vector3(b0[0] + (b1[0] - b0[0]) * t0, G0 + 1.0, b0[1] + (b1[1] - b0[1]) * t0);
        const b = new T.Vector3(b0[0] + (b1[0] - b0[0]) * t1, G0 + 1.0, b0[1] + (b1[1] - b0[1]) * t1);
        grp.add(new T.Mesh(this.limb(a, b, 0.06, 0.06), new T.MeshBasicMaterial({ color: i % 2 ? 0xf2f2f2 : 0xd23a2a })));
      }
      solid(new T.BoxGeometry(0.5, 1.1, 0.5).translate(b0[0], G0 + 0.55, b0[1]), [0.8, 0.78, 0.2]);
      // boundary hedge (clumps) behind a metal railing
      const hedge = [], rail = [];
      for (const line of F.hedge) {
        for (let i = 0; i + 1 < line.length; i++) {
          const [x0, z0] = line[i], [x1, z1] = line[i + 1], L = Math.hypot(x1 - x0, z1 - z0);
          for (let d = 0; d < L; d += 1.1) {
            const t = d / L, jx = Math.sin(d * 12.9) * 0.3, jz = Math.cos(d * 7.3) * 0.3;
            hedge.push([x0 + (x1 - x0) * t + jx, z0 + (z1 - z0) * t + jz, 0.75 + Math.abs(Math.sin(d * 3.1)) * 0.35]);
          }
          const nx = -(z1 - z0) / L, nz = (x1 - x0) / L;            // the railing a metre out from the hedge
          for (const y of [0.15, 1.1]) rail.push(x0 + nx, G0 + y, z0 + nz, x1 + nx, G0 + y, z1 + nz);
          for (let d = 0; d <= L; d += 2.4) { const t = d / L, x = x0 + (x1 - x0) * t + nx, z = z0 + (z1 - z0) * t + nz; rail.push(x, G0, z, x, G0 + 1.1, z); }
        }
      }
      const hm = new T.InstancedMesh(this.bush(71), this.leafMat, hedge.length), m = new T.Matrix4(), q = new T.Quaternion(), sc = new T.Vector3(), p = new T.Vector3();
      const hc = new T.Color();
      hedge.forEach(([x, z, r], i) => {
        q.setFromAxisAngle(new T.Vector3(0, 1, 0), i * 2.39996);
        m.compose(p.set(x, G0, z), q, sc.set(r * 1.1, r * 1.25, r * 1.1)); hm.setMatrixAt(i, m);
        hm.setColorAt(i, hc.setRGB(0.9 + (i % 5) * 0.03, 0.92 + (i % 3) * 0.03, 0.9));   // instance colours, as on all treeMat meshes
      });
      hm.userData.veg = true;
      grp.add(hm);
      const rg = new T.BufferGeometry(); rg.setAttribute("position", new T.Float32BufferAttribute(rail, 3));
      grp.add(new T.LineSegments(rg, this.fcMats.rail));
    }

    /* ---------- Sattva Hallmark ---------- */
    buildHallmark() {
      this.hallmark = new T.Group(); this.group.add(this.hallmark);
      this.facadeMat = new T.ShaderMaterial({
        vertexShader: FACADE_VS, fragmentShader: FACADE_FS, transparent: true, side: T.FrontSide,
        uniforms: {
          camPos: { value: new T.Vector3() }, ftf: { value: S.ftf }, ourRow: { value: -1 }, cutV: { value: 1e4 },
          ceilV: { value: S.ftf - 0.45 },                  // height of the lit floor's ceiling above its slab (buildLevel03)
          skyLo: { value: new T.Vector3() }, skyHi: { value: new T.Vector3() },
          glassBody: { value: new T.Vector3() }, frame: { value: new T.Vector3() },
          fogNear: { value: 1e4 }, fogFar: { value: 2e4 }, fogColor: { value: new T.Color() },
        },
      });
      this.blocks = {};
      for (const bl of S.blocks) {
        const grp = new T.Group();
        const top = Math.max(...bl.parts.map((p) => p.h));
        const f = this.facadeMesh(bl, top);
        if (bl.mitigata) f.userData.ours = true;
        grp.add(f);
        for (const p of bl.parts) {
          const roof = this.prism([p.ring], G0 + p.h - 0.3, 0.3);
          const [m, e] = this.massMesh(roof, 1);
          grp.add(m, e);
          grp.userData.roofs = (grp.userData.roofs || []).concat([m, e]);
        }
        this.blocks[bl.name] = grp; this.hallmark.add(grp);
      }
      this.buildCourt();
      this.buildLevel03();
    }
    /* the atrium and the forecourt, per site photos: an open paved court under a white steel space-frame
       roof with fabric panels in every bay (the checkered roof on the satellite), carried on tall white
       column pairs along the façades; planters with conical shrubs and foxtail palms, a water feature,
       a bridge across the far end */
    buildCourt() {
      const court = new T.Group(); this.hallmark.add(court); this.court = court;
      const M = this.courtMats = {};
      for (const k of ["frame", "column", "paving", "planter", "shrub", "water", "bridge"]) M[k] = new T.MeshBasicMaterial();
      M.panel = new T.MeshBasicMaterial({ transparent: true, side: T.DoubleSide, depthWrite: false });
      const rings = [S.atrium.ring, S.canopy.ring];
      const inRing = (x, z, r) => {
        let c = false;
        for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
          const [xi, zi] = r[i], [xj, zj] = r[j];
          if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c;
        }
        return c;
      };
      const inside = (x, z) => rings.some((r) => inRing(x, z, r));
      // ---- space frame: a 3 m grid, bottom chord just above the roofs, top chord 1.4 m higher ----
      const SP = 3.0, yb = G0 + S.canopy.z, yt = yb + 1.4;
      let x0 = 1e9, z0 = 1e9, x1 = -1e9, z1 = -1e9;
      rings.flat().forEach(([x, z]) => { x0 = Math.min(x0, x); z0 = Math.min(z0, z); x1 = Math.max(x1, x); z1 = Math.max(z1, z); });
      const ni = Math.ceil((x1 - x0) / SP), nj = Math.ceil((z1 - z0) / SP);
      const node = (i, j) => [x0 + i * SP, z0 + j * SP];
      const bin = (i, j) => { const [x, z] = node(i, j); return inside(x, z); };
      const members = [], panels = [];
      const V3 = (x, y, z) => new T.Vector3(x, y, z);
      for (let i = 0; i <= ni; i++) for (let j = 0; j <= nj; j++) {
        if (!bin(i, j)) continue;
        const [x, z] = node(i, j);
        if (bin(i + 1, j)) members.push([V3(x, yb, z), V3(x + SP, yb, z), 0.09]);
        if (bin(i, j + 1)) members.push([V3(x, yb, z), V3(x, yb, z + SP), 0.09]);
        if (bin(i + 1, j) && bin(i, j + 1) && bin(i + 1, j + 1)) {
          // a bay: the top-chord node over its centre, diagonals to its four corners, a fabric panel under it
          const cx = x + SP / 2, cz = z + SP / 2, top = V3(cx, yt, cz);
          for (const [dx, dz] of [[0, 0], [SP, 0], [0, SP], [SP, SP]]) members.push([top, V3(x + dx, yb, z + dz), 0.05]);
          if (bin(i + 2, j) && bin(i + 2, j + 1) && bin(i + 1, j + 1)) members.push([top, V3(cx + SP, yt, cz), 0.07]);
          if (bin(i, j + 2) && bin(i + 1, j + 2) && bin(i + 1, j + 1)) members.push([top, V3(cx, yt, cz + SP), 0.07]);
          const pg = new T.PlaneGeometry(SP * 0.74, SP * 0.74);   // sky shows between the fabric panels
          pg.rotateX(-Math.PI / 2); pg.translate(cx, yb - 0.25, cz);
          panels.push(pg);
        }
      }
      const tube = new T.CylinderGeometry(1, 1, 1, 6).translate(0, 0.5, 0);
      const im = new T.InstancedMesh(tube, M.frame, members.length), m = new T.Matrix4(), q = new T.Quaternion(), sc = new T.Vector3(), up = new T.Vector3(0, 1, 0);
      members.forEach(([a, b, r], i) => {
        const d = new T.Vector3().subVectors(b, a), L = d.length();
        q.setFromUnitVectors(up, d.normalize()); m.compose(a, q, sc.set(r, L, r)); im.setMatrixAt(i, m);
      });
      court.add(im);
      if (panels.length) {
        const pos = []; panels.forEach((g) => { const P = g.toNonIndexed().getAttribute("position"); for (let i = 0; i < P.count; i++) pos.push(P.getX(i), P.getY(i), P.getZ(i)); });
        const pg = new T.BufferGeometry(); pg.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
        const pm = new T.Mesh(pg, M.panel); pm.renderOrder = 3; court.add(pm);
      }
      // ---- columns: white pairs 1.2 m off both atrium façades and along the forecourt edge, every ~10.8 m ----
      const cols = [], [a0, a1, a2, a3] = S.atrium.ring;      // west face a0->a1, east face a3->a2
      const along = (p, q2, inset, other) => {
        const L = Math.hypot(q2[0] - p[0], q2[1] - p[1]), ux = (q2[0] - p[0]) / L, uz = (q2[1] - p[1]) / L;
        let nx = -uz, nz = ux;                                  // turn the inset towards the court
        if ((other[0] - p[0]) * nx + (other[1] - p[1]) * nz < 0) { nx = -nx; nz = -nz; }
        for (let d = 3; d < L - 2; d += 10.8) for (const off of [0, 0.8]) cols.push([p[0] + ux * (d + off) + nx * inset, p[1] + uz * (d + off) + nz * inset]);
      };
      along(a0, a1, 1.2, a3); along(a3, a2, 1.2, a0);
      // the forecourt edge: only its two corners (a full row stood between the views and the SOC)
      const cr = S.canopy.ring;
      for (const [p, q2] of [[cr[0], cr[1]], [cr[1], cr[0]]]) {
        const L = Math.hypot(q2[0] - p[0], q2[1] - p[1]), ux = (q2[0] - p[0]) / L, uz = (q2[1] - p[1]) / L;
        cols.push([p[0] + ux * 1.5, p[1] + uz * 1.5]);
      }
      const cm = new T.InstancedMesh(new T.CylinderGeometry(0.2, 0.2, 1, 10).translate(0, 0.5, 0), M.column, cols.length);
      cols.forEach(([x, z], i) => { m.compose(V3(x, G0, z), q.identity(), sc.set(1, yb - G0, 1)); cm.setMatrixAt(i, m); });
      court.add(cm);
      // ---- paving ----
      for (const r of rings) {
        const g = new T.ShapeGeometry(this.shape([r])); g.rotateX(-Math.PI / 2); g.translate(0, G0 + 0.03, 0);
        court.add(new T.Mesh(g, M.paving));
      }
      // ---- planters down the atrium: conical shrubs, and every other one a foxtail palm ----
      const mid = (p, q2) => [(p[0] + q2[0]) / 2, (p[1] + q2[1]) / 2];
      const s0 = mid(a0, a3), s1 = mid(a1, a2), LL = Math.hypot(s1[0] - s0[0], s1[1] - s0[1]);
      this.courtPalms = [];
      const box = (w, h, d, x, y, z, mat) => { const b = new T.Mesh(new T.BoxGeometry(w, h, d).translate(x, y, z), mat); court.add(b); return b; };
      for (let d = 10, k = 0; d < LL - 8; d += 13, k++) {
        const x = s0[0] + ((s1[0] - s0[0]) * d) / LL, z = s0[1] + ((s1[1] - s0[1]) * d) / LL + (k % 2 ? 3.5 : -3.5);
        box(3.2, 0.55, 1.6, x, G0 + 0.275, z, M.planter);
        if (k % 2) this.courtPalms.push([x, z, 2.6, 8.5 + (k % 3), 1]);
        else for (const ox of [-0.9, 0, 0.9]) court.add(new T.Mesh(new T.ConeGeometry(0.45, 1.8, 8).translate(x + ox, G0 + 0.55 + 0.9, z), M.shrub));
      }
      // water feature near the forecourt end, and the bridge across the far end
      const wx = s0[0] + ((s1[0] - s0[0]) * 6) / LL, wz = s0[1] + ((s1[1] - s0[1]) * 6) / LL;
      box(6, 0.6, 3, wx, G0 + 0.3, wz, M.planter); box(5.4, 0.05, 2.4, wx, G0 + 0.62, wz, M.water);
      const bx = s0[0] + ((s1[0] - s0[0]) * 0.72), bz = s0[1] + ((s1[1] - s0[1]) * 0.72);
      box(3.5, 1.2, Math.abs(a3[1] - a0[1]) + 0.4, bx, G0 + 4.8, bz, M.bridge);
    }
    /* Level 03 seen from outside: a lit ceiling over the floor plate, and the SOC's halo over the SOC zone */
    buildLevel03() {
      this.l3 = new T.Group(); this.group.add(this.l3);
      const out = D.zones.annot.outline, ceilY = S.ftf - 0.45;
      const sh = new T.Shape(out.map(([x, y]) => new T.Vector2(mx(x), -mz(y))));
      const cg = new T.ShapeGeometry(sh); cg.rotateX(-Math.PI / 2); cg.translate(0, ceilY, 0);
      this.ceilingMat = new T.MeshBasicMaterial({ side: T.DoubleSide });
      this.l3.add(new T.Mesh(cg, this.ceilingMat));
      this.halo = new T.Group(); this.l3.add(this.halo);
      this.buildHalo();
    }
    /* the SOC's ceiling, as in the interior render: Mitigata's logo arcs over the desks, a wide white lit arc with the green
       perforated arc inside it, both centred on the command wall and swept as far as the SOC allows (ends cut square, like the
       logo's); a small ring pendant hangs between them and the wall (Sathwick) */
    buildHalo() {
      this.halo.clear();
      const z = D.zones[this.opt].zones.filter((q) => q.type === "soc").sort((a, b) => b.area - a.area)[0];
      if (!z) return;
      const P = z.poly.map(([x, y]) => [mx(x), mz(y)]);
      const inside = (x, y) => {
        let c = false;
        for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
          const [xi, yi] = P[i], [xj, yj] = P[j];
          if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
        }
        return c;
      };
      const edgeDist = (x, y) => {
        let d = 1e9;
        for (let i = 0, j = P.length - 1; i < P.length; j = i++) {
          const [ax, ay] = P[j], [bx, by] = P[i], vx = bx - ax, vy = by - ay, L = vx * vx + vy * vy || 1e-9;
          const t = Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / L));
          d = Math.min(d, Math.hypot(x - ax - t * vx, y - ay - t * vy));
        }
        return d;
      };
      const ok = (x, y) => inside(x, y) && edgeDist(x, y) >= 0.6;           // a ceiling feature: it never crosses the glass
      // the command wall the desks face (09.10 test fits): Option 01's curved wall on the west façade, at the centre of its fan
      // of desks, the arcs swept to fit the SOC; Option 02's display wall in the SOC's south-east corner, where Sathwick drew
      // them (12.10): 5.6 m out, facing north-west (plan degrees), in Option 01's proportions (its 124° sweep); moved ≈2.9 m
      // towards the road view's centre so the whole arc is in its frame, still 0.6 m clear of the glass (Sathwick, 13.10)
      const SPEC = {
        opt1: { c: [22700, 31850] },
        opt2: { c: [25600, 8200], R: 5.6, a: [149 - 62, 149 + 62] },
      }[this.opt];
      if (!SPEC) return;
      const cx = mx(SPEC.c[0]), cz = mz(SPEC.c[1]);
      // which way the desks lie: towards the SOC's deepest point
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      P.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); });
      let dx = 0, dz = 0, best = -1;
      for (let i = 0; i <= 60; i++) for (let j = 0; j <= 60; j++) {
        const x = x0 + ((x1 - x0) * i) / 60, y = y0 + ((y1 - y0) * j) / 60;
        if (!inside(x, y)) continue;
        const d = edgeDist(x, y);
        if (d > best) { best = d; dx = x; dz = y; }
      }
      // the axis, in the ring geometry's angle (x, -z: plan degrees): the middle of a drawn sweep, or towards the deepest point
      const ax = SPEC.a ? ((SPEC.a[0] + SPEC.a[1]) / 2) * Math.PI / 180 : Math.atan2(-(dz - cz), dx - cx);
      const at = (r, a) => [cx + Math.cos(a) * r, cz - Math.sin(a) * r];
      // the white arc's outer edge: well into the desks, about two thirds of the way along the axis to the SOC's far edge
      let far = 0; while (far < 40 && inside(...at(far + 0.25, ax))) far += 0.25;
      // the outer radius; the white and green bands and the pendant keep Option 01's proportions (1.5 m and 0.8 m bands at 9 m)
      const R = SPEC.R || Math.max(4, Math.min(far - 1.5, far * 0.68)), W = (R * 1.5) / 9, G = (R * 0.8) / 9;
      // the sweep: as drawn, or from the axis both ways while both edges of the arcs stay inside the SOC (at most 210°)
      const fits = (a) => ok(...at(R, a)) && ok(...at(R - W - G, a));
      let lo = 0, hi = 0; const step = Math.PI / 180;
      if (SPEC.a) { const [a0, a1] = SPEC.a.map((d) => (d * Math.PI) / 180); lo = ax - a0; hi = a1 - ax; }
      else {
        while (lo < Math.PI * 0.58 && fits(ax - lo - step)) lo += step;
        while (hi < Math.PI * 0.58 && fits(ax + hi + step)) hi += step;
      }
      if (lo + hi < Math.PI / 6) return;
      const arc = (r0, r1, a0, a1, color, y) => {
        const g = new T.RingGeometry(r0, r1, 96, 1, a0, a1 - a0); g.rotateX(-Math.PI / 2);
        const m = new T.Mesh(g, new T.MeshBasicMaterial({ color, side: T.DoubleSide }));
        m.position.set(cx, y, cz); this.halo.add(m);
      };
      const y = S.ftf - 0.55, trim = 0.08 * (lo + hi);                       // the green arc a little shorter at each end
      arc(R - W, R, ax - lo, ax + hi, 0xffffff, y);                          // the lit arc
      arc(R - W - G, R - W, ax - lo + trim, ax + hi - trim, 0x0a8f57, y - 0.12);   // the green perforated arc, just below it
      // the pendant: a ring of light between the arcs and the wall
      const [px, pz] = at((R - W - G) * 0.45, ax), pr = (R * 1.4) / 9;
      const pg = new T.RingGeometry(pr - (pr * 0.15) / 1.4, pr, 64); pg.rotateX(-Math.PI / 2);
      const pm = new T.Mesh(pg, new T.MeshBasicMaterial({ color: 0xffffff, side: T.DoubleSide }));
      pm.position.set(px, y - 0.55, pz); this.halo.add(pm);
    }
    facadeMesh(bl, top) {
      const pos = [], uv = [], an = [];
      for (const fa of bl.facades) {
        const L = fa.len, tx = (fa.b[0] - fa.a[0]) / L, tz = (fa.b[1] - fa.a[1]) / L;
        // front faces outward: (a,0)->(b,0)->(b,top) faces (-tz, 0, tx)
        let v = [[fa.a, 0, 0], [fa.b, 0, L], [fa.b, top, L], [fa.a, 0, 0], [fa.b, top, L], [fa.a, top, 0]];
        if (-tz * fa.n[0] + tx * fa.n[1] < 0) v = [v[0], v[2], v[1], v[3], v[5], v[4]];
        for (const [[x, z], y, u] of v) { pos.push(x, G0 + y, z); uv.push(u, y); an.push(fa.n[0], 0, fa.n[1]); }
      }
      const g = new T.BufferGeometry();
      g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
      g.setAttribute("uv", new T.Float32BufferAttribute(uv, 2));
      g.setAttribute("aN", new T.Float32BufferAttribute(an, 3));
      // Mitigata's block gets its own material instance so only its Level 03 goes clear
      const mat = bl.mitigata ? this.facadeMat : this.otherMat || (this.otherMat = this.facadeMat.clone());
      const m = new T.Mesh(g, mat); m.renderOrder = 2;
      return m;
    }

    /* ---------- public ---------- */
    setOption(opt) {
      if (opt === this.opt) return;
      this.opt = opt; this.buildHalo();
    }
    setTheme(t) {
      this.theme = t === "light" ? "light" : "dark";
      const P = PAL[this.theme];
      this.mats.mass.forEach((m) => m.color.setHex(P.mass));
      this.mats.edges.forEach((m) => { m.color.setHex(P.massEdge); });
      this.treeMat.color.setHex(P.tree); this.leafMat.color.setHex(P.leaf);
      if (this.fcMats) { this.fcMats.solid.color.setHex(P.tree); this.fcMats.rail.color.setHex(P.rail); }
      const C = P.court, M = this.courtMats;
      for (const k of ["frame", "column", "paving", "planter", "shrub", "water", "bridge", "panel"]) M[k].color.setHex(C[k]);
      M.panel.opacity = C.panelOp;
      this.ceilingMat.color.setHex(P.ceiling);
      this.paintGround();
      this.applyLook();
    }
    setNight(n) { this.night = n; this.applyLook(); }
    applyLook() {
      const P = PAL[this.theme], n = this.night;
      const lerp3 = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k);
      const N = PAL.dark, k = this.theme === "light" ? n : 0;    // the dark theme is already the night look
      for (const mat of [this.facadeMat, this.otherMat]) {
        if (!mat) continue;
        const u = mat.uniforms;
        u.skyLo.value.fromArray(lerp3(P.sky[0], N.sky[0], k)); u.skyHi.value.fromArray(lerp3(P.sky[1], N.sky[1], k));
        u.glassBody.value.fromArray(lerp3(P.glassBody, N.glassBody, k)); u.frame.value.fromArray(lerp3(P.frame, N.frame, k));
      }
      this.facadeMat.uniforms.ourRow.value = S.level;
    }
    /* cut the Mitigata block open above Level 03, to look down into the real floor */
    setCut(on) {
      const east = S.blocks.find((b) => b.mitigata), grp = this.blocks[east.name];
      this.facadeMat.uniforms.cutV.value = on ? (S.level + 1) * S.ftf : 1e4;
      (grp.userData.roofs || []).forEach((o) => (o.visible = !on));
      this.ceilingMat.visible = !on;
    }
    setVisible(v) { this.group.visible = v; }
    /* trees, palms and the hedge (the forecourt's island, kiosk and barrier stay) */
    setTrees(on) { this.treesOn = on; this.trees.traverse((o) => { if (o.userData.veg) o.visible = on; }); }
    frame(camera) {
      if (!this.group.visible) return;
      const f = this.twin.scene.fog;
      for (const mat of [this.facadeMat, this.otherMat]) {
        if (!mat) continue;
        const u = mat.uniforms; u.camPos.value.copy(camera.position);
        if (f) { u.fogNear.value = f.near; u.fogFar.value = f.far; u.fogColor.value.copy(f.color); }
      }
    }
  }
  window.TwinSite = TwinSite;
})();
