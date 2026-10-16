/* Twin — the floor as a live "digital twin" (three.js r147, classic build).
   Walls / glass / partitions are extruded from the DXF polylines, furniture is a
   floor texture, programme + security tiers + events are translucent volumes,
   and ~315 people move between scenarios (workday -> events -> dinner). */
(function () {
  const D = window.MX_DATA, TEX = window.MX_TEX, T = window.THREE;
  const CX = 42000, CY = 17500;
  const mx = (x) => (x - CX) / 1000, mz = (y) => -(y - CY) / 1000;
  // the deck's zoning palette and trust tiers (see plan2d.js)
  const ZCOL = { soc: 0xb5f4d9, secure: 0x9ed9c0, arrive: 0xfce7ae, board: 0xa0bbeb, focus: 0xe4aba5, meet: 0xc9d3e0,
    collab: 0xe9c8ff, cafe: 0xf2c596, studio: 0xe8b4c8, quiet: 0xc6e8da, service: 0xc8c8c8, core: 0x919191 };
  const TCOL = [0x919191, 0xf2c596, 0xa0bbeb, 0x04db7f];
  const MINT = 0x04db7f;
  // [colour, face opacity, edge opacity]
  const PALETTE = {
    dark: { bg: 0x0e2a1f, bgNight: 0x07170f, slab: 0x12352a, slabEdge: MINT, slabEdgeOp: 0.4, grid: [0x1f4a3a, 0x173d2f],
      shell: [0xdfe8e3, 0.032, 0.34], part: [0xc49a6c, 0.10, 0.62], glass: [0x9fe9ff, 0.05, 0.45], cols: [0xdfe8e3, 0.55], furn: [0xcfe9dc, 0.55],
      people: { base: 0xf2f5f3, night: 0xfce7ae, soc: 0xb5f4d9, event: 0x04db7f, board: 0xfbbc04 } },
    light: { bg: 0xffffff, bgNight: 0xd9dee3, slab: 0xfafcfa, slabEdge: MINT, slabEdgeOp: 0.7, grid: [0xe3e6e3, 0xeef0ee],
      shell: [0x0d0d0d, 0.028, 0.5], part: [0x434343, 0.12, 0.7], glass: [0x7f8c96, 0.07, 0.6], cols: [0x434343, 0.42], furn: [0x434343, 0.5],
      people: { base: 0x434343, night: 0x6b4a1a, soc: 0x03b86a, event: 0x04db7f, board: 0xd99e00 } },
  };

  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  function inPoly(x, y, poly) {
    let c = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xi, yi] = poly[i], [xj, yj] = poly[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  }
  function bbox(poly) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    poly.forEach(([x, y]) => { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); });
    return [x0, y0, x1, y1];
  }
  /* scatter n points in polygons with a minimum spacing (mm) */
  function scatter(polys, n, seed, gap) {
    const r = rng(seed), out = [];
    if (!polys.length || n <= 0) return out;
    const areas = polys.map((p) => Math.max(1, polyArea(p)));
    const tot = areas.reduce((a, b) => a + b, 0);
    let tries = 0; gap = gap || 1100;
    while (out.length < n && tries < n * 400) {
      tries++;
      let k = r() * tot, i = 0; while (k > areas[i] && i < areas.length - 1) k -= areas[i++];
      const b = bbox(polys[i]); const x = b[0] + r() * (b[2] - b[0]), y = b[1] + r() * (b[3] - b[1]);
      if (!inPoly(x, y, polys[i])) continue;
      const g = tries > n * 200 ? gap * 0.6 : gap;
      if (out.some((p) => (p[0] - x) ** 2 + (p[1] - y) ** 2 < g * g)) continue;
      out.push([x, y]);
    }
    return out;
  }
  /* theatre rows: grid points inside the event's polygons, nearest to the stage first */
  function seats(polys, n, stage) {
    const pts = [];
    polys.forEach((poly) => {
      const b = bbox(poly);
      for (let x = b[0] + 500; x < b[2]; x += 850) for (let y = b[1] + 500; y < b[3]; y += 950) if (inPoly(x, y, poly)) pts.push([x, y]);
    });
    pts.sort((a, c) => Math.hypot(a[0] - stage[0], a[1] - stage[1]) - Math.hypot(c[0] - stage[0], c[1] - stage[1]));
    const keep = pts.filter((p) => Math.hypot(p[0] - stage[0], p[1] - stage[1]) > 2200);
    return keep.slice(0, n);
  }
  function polyArea(p) { let a = 0; for (let i = 0; i < p.length; i++) { const [x1, y1] = p[i], [x2, y2] = p[(i + 1) % p.length]; a += x1 * y2 - x2 * y1; } return Math.abs(a) / 2; }

  /* stage points and the lobby come from the 09.10 drawing (tools/derive_layout.py) */
  const evPolys = (ev) => ev.polys || [ev.poly];

  /* scenarios: who is where (counts by zone type, or event seats) */
  const SCEN = {
    workday: { soc: 72, focus: 190, meet: 38, collab: 10, cafe: 5 },
    lunch: { soc: 60, focus: 118, cafe: 52, collab: 40, meet: 22 },
    e50: { soc: 70, focus: 150, meet: 30, collab: 15, event: ["50", 50] },
    e100: { soc: 60, focus: 70, meet: 10, collab: 15, cafe: 10, event: ["100", 100] },
    e200: { soc: 50, cafe: 18, collab: 12, event: ["200", 200] },
    dinner: { soc: 40, focus: 12, collab: 6, board: 30 },
  };
  const NPEOPLE = 320;

  class Twin {
    constructor() {
      this.renderer = new T.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
      this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      this.canvas = this.renderer.domElement;
      this.scene = new T.Scene();
      this.bg = new T.Color(0x0a0f0d); this.scene.background = this.bg;
      this.scene.fog = new T.Fog(0x0a0f0d, 120, 260);
      this.camera = new T.PerspectiveCamera(30, 16 / 9, 0.5, 600);
      this.rig = { theta: -0.55, phi: 0.92, r: 108, tx: 0, ty: 0, tz: 1.5 };
      this.labels = document.createElement("div"); this.labels.className = "twin-labels";
      this.opt = "opt1"; this.layers = {}; this.cache = {}; this.theme = "dark"; this.shift = 0; this.rise = 0;
      this.explodeT = 0; this.night = 0; this.eventLevel = null; this.eventK = 0; this.rMax = 220;
      this.labelDefs = [];
      this.buildCommon();
      this.setOption("opt1");
      this.buildPeople();
      this.bindControls();
      this.clock = new T.Clock();
      const loop = () => { requestAnimationFrame(loop); if (this.host && this.visible) this.frame(); };
      loop();
    }

    attach(host) {
      this.host = host; host.appendChild(this.canvas); host.appendChild(this.labels);
      this.visible = true; this.resize();
      if (!this._ro) { this._ro = new ResizeObserver(() => this.resize()); }
      this._ro.disconnect(); this._ro.observe(host);
    }
    detach() { this.visible = false; }
    resize() {
      if (!this.host) return;
      const r = this.host.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      this.renderer.setSize(r.width, r.height, false);
      this.camera.aspect = r.width / r.height;
      // shift: slide the model sideways on screen; rise: a shift lens (keeps verticals straight while framing high)
      if (this.shift || this.rise) this.camera.setViewOffset(r.width, r.height, -this.shift * r.width, -this.rise * r.height, r.width, r.height);
      else this.camera.clearViewOffset();
      this.camera.updateProjectionMatrix();
    }
    /* push the model sideways on screen (fraction of width) so it clears overlay copy */
    setRise(f, ms) { if (!ms) { this.rise = f || 0; return this.resize(); } this.tween("rise", f || 0, ms, () => this.resize()); }
    setShift(f, ms) { if (!ms) { this.shift = f || 0; return this.resize(); } this.tween("shift", f || 0, ms, () => this.resize()); }

    /* ---------- geometry ---------- */
    buildCommon() {
      const a = D.zones.annot.outline;
      const shape = new T.Shape(a.map(([x, y]) => new T.Vector2(mx(x), (y - CY) / 1000)));
      const slab = new T.Mesh(new T.ExtrudeGeometry(shape, { depth: 0.45, bevelEnabled: false }),
        new T.MeshBasicMaterial({ color: 0x0f1714 }));
      slab.rotation.x = -Math.PI / 2; slab.position.y = -0.45;
      const edge = new T.LineSegments(new T.EdgesGeometry(slab.geometry), new T.LineBasicMaterial({ color: MINT, transparent: true, opacity: 0.35 }));
      edge.rotation.copy(slab.rotation); edge.position.copy(slab.position);
      this.base = new T.Group(); this.base.add(slab, edge); this.scene.add(this.base);
      this.baseC = a.reduce((acc, [x, y]) => [acc[0] + mx(x) / a.length, acc[1] + mz(y) / a.length], [0, 0]);
      this.slabMat = slab.material; this.slabEdgeMat = edge.material;
      // grid "ground"
      const grid = new T.GridHelper(260, 52, 0x1d2925, 0x141d1a); grid.position.y = -0.47; grid.material.transparent = true; grid.material.opacity = 0.6;
      this.scene.add(grid); this.grid = grid;
      // stage marker
      this.stage = new T.Mesh(new T.BoxGeometry(3.2, 0.5, 1.4), new T.MeshBasicMaterial({ color: MINT, transparent: true, opacity: 0.9 }));
      this.stage.visible = false; this.scene.add(this.stage);
    }

    wallGeo(lines, h, minLen) {
      const pos = [], top = [];
      for (const p of lines) {
        for (let i = 2; i < p.length; i += 2) {
          const x1 = p[i - 2], y1 = p[i - 1], x2 = p[i], y2 = p[i + 1];
          if (Math.hypot(x2 - x1, y2 - y1) < (minLen || 40)) continue;
          const ax = mx(x1), az = mz(y1), bx = mx(x2), bz = mz(y2);
          pos.push(ax, 0, az, bx, 0, bz, bx, h, bz, ax, 0, az, bx, h, bz, ax, h, az);
          top.push(ax, h, az, bx, h, bz);
        }
      }
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
      const e = new T.BufferGeometry(); e.setAttribute("position", new T.Float32BufferAttribute(top, 3));
      return [g, e];
    }
    polyMesh(poly, color, opacity, height, y) {
      const s = new T.Shape(poly.map(([x, yy]) => new T.Vector2(mx(x), (yy - CY) / 1000)));
      const geo = height ? new T.ExtrudeGeometry(s, { depth: height, bevelEnabled: false }) : new T.ShapeGeometry(s);
      const m = new T.Mesh(geo, new T.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: T.DoubleSide }));
      m.rotation.x = -Math.PI / 2; m.position.y = y || 0;
      return m;
    }

    buildOption(opt) {
      if (this.cache[opt]) return this.cache[opt];
      const d = D[opt], z = D.zones[opt], o = {};
      // furniture floor texture
      const tex = new T.TextureLoader().load(TEX[opt]);
      tex.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
      const rw = d.raster.w / d.raster.px_per_m, rh = d.raster.h / d.raster.px_per_m;
      const plane = new T.Mesh(new T.PlaneGeometry(rw, rh), new T.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0.55, color: 0xcfe9dc, depthWrite: false }));
      plane.rotation.x = -Math.PI / 2; plane.position.set(mx(rw * 500), 0.02, mz(d.size[1] - rh * 500));
      o.furn = new T.Group(); o.furn.add(plane);
      o.mats = { furn: plane.material };
      // walls
      o.walls = new T.Group();
      const add = (key, lines, h) => {
        const [g, e] = this.wallGeo(lines, h);
        const mm = new T.MeshBasicMaterial({ transparent: true, side: T.DoubleSide, depthWrite: false });
        const em = new T.LineBasicMaterial({ transparent: true });
        o.walls.add(new T.Mesh(g, mm)); o.walls.add(new T.LineSegments(e, em));
        o.mats[key] = [mm, em];
      };
      add("shell", d.vec.shell, 3.1);
      add("part", d.vec.partition, 2.7);
      add("glass", d.vec.glass, 2.7);
      // columns / solid fills (one shared material)
      const cols = new T.Group();
      o.mats.cols = new T.MeshBasicMaterial({ transparent: true, depthWrite: false, side: T.DoubleSide });
      d.fills.forEach((p) => {
        const pts = []; for (let i = 0; i < p.length; i += 2) pts.push([p[i], p[i + 1]]);
        if (polyArea(pts) < 0.05e6) return;
        const m = this.polyMesh(pts, 0xdfe8e3, 0.55, 3.1, 0); m.material = o.mats.cols; cols.add(m);
      });
      o.walls.add(cols);
      // zones (flat, coloured) + tiers (volumes by tier height)
      o.zones = new T.Group(); o.tiers = new T.Group();
      z.zones.forEach((zz) => {
        const tier = D.zones.types[zz.type].tier;
        o.zones.add(this.polyMesh(zz.poly, ZCOL[zz.type], zz.type === "core" ? 0.25 : 0.4, 0, 0.06));
        if (tier > 0) o.tiers.add(this.polyMesh(zz.poly, TCOL[tier], 0.16 + tier * 0.05, 0.3 + tier * 0.9, 0.05));
      });
      // events
      o.events = {};
      for (const k in z.events) {
        const g = new T.Group();
        evPolys(z.events[k]).forEach((poly) => {
          const m = this.polyMesh(poly, MINT, 0.16, 2.6, 0.04);
          const e = new T.LineSegments(new T.EdgesGeometry(m.geometry, 30), new T.LineBasicMaterial({ color: MINT, transparent: true, opacity: 0.9 }));
          e.rotation.copy(m.rotation); e.position.copy(m.position);
          g.add(m, e);
        });
        g.scale.y = 0.001; g.visible = false; o.events[k] = g;
      }
      o.eventsGroup = new T.Group(); Object.values(o.events).forEach((g) => o.eventsGroup.add(g));
      // routes as glowing tubes
      o.routes = new T.Group();
      for (const k in z.routes) {
        const pts = z.routes[k].pts.map(([x, y]) => new T.Vector3(mx(x), 0.25, mz(y)));
        const curve = new T.CatmullRomCurve3(pts, false, "catmullrom", 0.05);
        const col = k === "visitor" ? 0xfbbc04 : k === "tour" ? MINT : 0xa0bbeb;
        o.routes.add(new T.Mesh(new T.TubeGeometry(curve, Math.max(20, pts.length * 12), 0.12, 6, false), new T.MeshBasicMaterial({ color: col })));
      }
      // operable walls
      (z.walls || []).forEach((w) => {
        const flat = []; w.forEach(([x, y]) => flat.push(x, y));
        const [g, e] = this.wallGeo([flat], 2.7);
        o.walls.add(new T.Mesh(g, new T.MeshBasicMaterial({ color: 0xff5a4e, transparent: true, opacity: 0.25, side: T.DoubleSide, depthWrite: false })));
      });
      this.cache[opt] = o;
      this.paintOption(o);
      return o;
    }

    /* ---------- themes ---------- */
    setTheme(t) {
      this.theme = t === "light" ? "light" : "dark";
      const P = PALETTE[this.theme];
      this.slabMat.color.setHex(P.slab); this.slabEdgeMat.color.setHex(P.slabEdge); this.slabEdgeMat.opacity = P.slabEdgeOp;
      this.scene.remove(this.grid);
      this.grid = new T.GridHelper(260, 52, P.grid[0], P.grid[1]); this.grid.position.y = -0.47;
      this.grid.material.transparent = true; this.grid.material.opacity = 0.6; this.scene.add(this.grid);
      this.grid.visible = !(this.site && this.layers.site);
      Object.values(this.cache).forEach((o) => this.paintOption(o));
      this.applyNight();
      if (this.people) this.updatePeople(Math.min(1, this.pT));
      if (this.site) this.site.setTheme(this.theme);
    }
    paintOption(o) {
      const P = PALETTE[this.theme || "dark"];
      for (const k of ["shell", "part", "glass"]) {
        const [mm, em] = o.mats[k], [col, op, eop] = P[k];
        mm.color.setHex(col); mm.opacity = op; em.color.setHex(col); em.opacity = eop;
      }
      o.mats.cols.color.setHex(P.cols[0]); o.mats.cols.opacity = P.cols[1];
      o.mats.furn.color.setHex(P.furn[0]); o.mats.furn.opacity = P.furn[1];
    }
    applyNight() {
      const P = PALETTE[this.theme || "dark"], n = this.night;
      const a = new T.Color(P.bg), b = new T.Color(P.bgNight);
      this.bg.copy(a).lerp(b, n); this.scene.fog.color.copy(this.bg);
      Object.values(this.cache).forEach((o) => (o.mats.furn.opacity = P.furn[1] - 0.2 * n));
      if (this.site) this.site.setNight(n);
    }
    /* straight-down view framed like the 2D plan (for the plan -> 3D handoff) */
    topView(r) { this.stopFly(); Object.assign(this.rig, { theta: 0, phi: 0.0015, r: r || 78, tx: mx(42200), ty: 0, tz: mz(17600) }); }

    setOption(opt) {
      const old = this.cache[this.opt];
      if (old) ["furn", "walls", "zones", "tiers", "eventsGroup", "routes"].forEach((k) => this.scene.remove(old[k]));
      this.opt = opt;
      if (this.site) this.site.setOption(opt);
      const o = this.buildOption(opt);
      ["furn", "walls", "zones", "tiers", "eventsGroup", "routes"].forEach((k) => this.scene.add(o[k]));
      this.applyLayers();
      if (this.site) this.applySite();
      if (this.people) this.setScenario(this.scenario || "workday", true);
    }
    setLayers(patch) { Object.assign(this.layers, patch); this.applyLayers(); if ("site" in patch || "cut" in patch) this.applySite(); }

    /* ---------- site context (assets/js/site.js) ---------- */
    attachSite(site) { this.site = site; site.setTheme(this.theme); site.setNight(this.night); site.setOption(this.opt); this.applySite(); }
    applySite() {
      const on = !!(this.site && this.layers.site);
      if (this.site) { this.site.setVisible(on); this.site.setCut(this.layers.cut !== false); }
      this.grid.visible = !on;
      // inside the building the slab sits just behind the glass (its edge lies on the façade line at the prow)
      const k = on ? 0.992 : 1;
      this.base.scale.set(k, 1, k); this.base.position.set(this.baseC[0] * (1 - k), 0, this.baseC[1] * (1 - k));
      // the street needs a deeper view than the floor on its own
      this.scene.fog.near = on ? 260 : 120; this.scene.fog.far = on ? 760 : 260;
      this.camera.far = on ? 2500 : 600; this.camera.updateProjectionMatrix();
      this.rMax = on ? 620 : 220;
      // seen from the street, the floor's walls need more body than in the plan-like views
      const o = this.cache[this.opt];
      if (o) {
        this.paintOption(o);
        // the shell includes the curtain-wall line right behind the glass: keep it faint, give the partitions body
        if (on) for (const [k, f, e] of [["shell", 0.08, 0.5], ["part", 0.62, 0.9], ["glass", 0.12, 0.6]]) {
          o.mats[k][0].opacity = f; o.mats[k][1].opacity = e;
        }
      }
    }
    applyLayers() {
      const o = this.cache[this.opt], L = this.layers;
      o.furn.visible = L.furn !== false; o.walls.visible = L.walls !== false;
      o.zones.visible = !!L.zones; o.tiers.visible = !!L.tiers; o.routes.visible = !!L.routes;
      if (this.people) this.people.visible = !!L.people;
      this.applyExplode();
    }
    explode(t, ms) { this.tween("explodeT", t, ms || 1200, () => this.applyExplode()); }
    applyExplode() {
      const o = this.cache[this.opt], t = this.explodeT;
      o.furn.position.y = 0; o.walls.position.y = t * 5;
      o.zones.position.y = t * 11; o.tiers.position.y = t * 15.5; o.routes.position.y = t * 21;
      o.eventsGroup.position.y = 0;
    }

    /* ---------- events ---------- */
    showEvent(level) {
      const o = this.cache[this.opt];
      for (const k in o.events) {
        const g = o.events[k];
        if (k === level) { g.visible = true; this.tweenObj(g.scale, "y", 1, 1100); }
        else if (g.visible) { this.tweenObj(g.scale, "y", 0.001, 500, () => (g.visible = false)); }
      }
      this.eventLevel = level;
      const ev = level && D.zones[this.opt].events[level], st = ev && ev.stage;
      this.stage.visible = !!st;
      if (st) this.stage.position.set(mx(st[0]), 0.25, mz(st[1]));
    }

    /* ---------- people ---------- */
    buildPeople() {
      const geo = new T.CylinderGeometry(0.17, 0.17, 1.15, 8); geo.translate(0, 0.58, 0);
      const mat = new T.MeshBasicMaterial({ color: 0xffffff });
      this.people = new T.InstancedMesh(geo, mat, NPEOPLE);
      this.people.instanceMatrix.setUsage(T.DynamicDrawUsage);
      this.pFrom = new Float32Array(NPEOPLE * 2); this.pTo = new Float32Array(NPEOPLE * 2);
      this.pVis = new Float32Array(NPEOPLE); this.pVisTo = new Float32Array(NPEOPLE); this.pDelay = new Float32Array(NPEOPLE);
      this.pRole = new Array(NPEOPLE).fill("x");
      const r = rng(7);
      const lob = this.lobby();
      for (let i = 0; i < NPEOPLE; i++) { this.pFrom[i * 2] = lob[0]; this.pFrom[i * 2 + 1] = lob[1]; this.pDelay[i] = r() * 0.6; }
      this.pT = 1; this.people.visible = false;
      this.scene.add(this.people);
      this.dummy = new T.Object3D(); this.col = new T.Color();
      this.setScenario("workday", true);
    }
    setScenario(name, instant) {
      this.scenario = name;
      const sc = SCEN[name], z = D.zones[this.opt], targets = [];
      const zonesOf = (t) => z.zones.filter((zz) => zz.type === t).map((zz) => zz.poly);
      let seed = 11;
      for (const t in sc) {
        if (t === "event") continue;
        scatter(zonesOf(t), sc[t], seed++ * 31, t === "soc" ? 1300 : 1050).forEach((p) => targets.push([p[0], p[1], t]));
      }
      if (sc.event) {
        const [lvl, n] = sc.event, ev = z.events[lvl];
        seats(evPolys(ev), n, ev.stage || window.Plan2D.centroid(ev.poly)).forEach((p) => targets.push([p[0], p[1], "event"]));
      }
      // keep identity stable: current positions continue from where they are
      const lob = this.lobby();
      for (let i = 0; i < NPEOPLE; i++) {
        const cur = this.currentPos(i);
        this.pFrom[i * 2] = cur[0]; this.pFrom[i * 2 + 1] = cur[1];
        if (i < targets.length) {
          this.pTo[i * 2] = targets[i][0]; this.pTo[i * 2 + 1] = targets[i][1]; this.pRole[i] = targets[i][2]; this.pVisTo[i] = 1;
        } else {
          this.pTo[i * 2] = lob[0]; this.pTo[i * 2 + 1] = lob[1]; this.pRole[i] = "out"; this.pVisTo[i] = 0;
        }
      }
      this.headcount = targets.length;
      this.pT = instant ? 1 : 0; this.pStart = performance.now();
      if (instant) for (let i = 0; i < NPEOPLE; i++) this.pVis[i] = this.pVisTo[i];
      this.updatePeople(instant ? 1 : 0);
      return targets.length;
    }
    lobby() { const z = D.zones[this.opt || "opt1"]; return (z && z.lobby) || D.zones.opt1.lobby; }
    currentPos(i) {
      if (!this._lastPos) return [this.pFrom[i * 2], this.pFrom[i * 2 + 1]];
      return [this._lastPos[i * 2], this._lastPos[i * 2 + 1]];
    }
    updatePeople(t) {
      if (!this._lastPos) this._lastPos = new Float32Array(NPEOPLE * 2);
      const night = this.night;
      for (let i = 0; i < NPEOPLE; i++) {
        let k = Math.min(1, Math.max(0, (t * 1.6 - this.pDelay[i]) / 1));
        k = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        const x = this.pFrom[i * 2] + (this.pTo[i * 2] - this.pFrom[i * 2]) * k;
        const y = this.pFrom[i * 2 + 1] + (this.pTo[i * 2 + 1] - this.pFrom[i * 2 + 1]) * k;
        this._lastPos[i * 2] = x; this._lastPos[i * 2 + 1] = y;
        const vis = this.pVisTo[i] ? Math.max(this.pVis[i], k) : (1 - k) * this.pVis[i];
        this.dummy.position.set(mx(x), 0.05, mz(y));
        const s = Math.max(0.0001, vis); this.dummy.scale.set(s, s, s);
        this.dummy.updateMatrix(); this.people.setMatrixAt(i, this.dummy.matrix);
        const role = this.pRole[i], PP = PALETTE[this.theme || "dark"].people;
        this.col.setHex(role === "event" ? PP.event : role === "soc" ? PP.soc : role === "board" ? PP.board : night > 0.5 ? PP.night : PP.base);
        this.people.setColorAt(i, this.col);
      }
      if (t >= 1) for (let i = 0; i < NPEOPLE; i++) this.pVis[i] = this.pVisTo[i];
      this.people.instanceMatrix.needsUpdate = true;
      if (this.people.instanceColor) this.people.instanceColor.needsUpdate = true;
    }

    setNight(v, ms) { this.tween("night", v, ms || 1200, () => this.applyNight()); }

    /* ---------- camera ---------- */
    /* "orbit" turns the model around its target; "look" stands still and turns the head (street-level views) */
    setControl(mode) {
      this.fc = null;                                              // the free camera re-reads the rig next frame
      if (mode === "free") { this.control = "free"; return; }   // free: keep the lens as it is (the camera editor sets it)
      this.control = mode === "look" ? "look" : "orbit";
      // a wider lens at eye level (closer to how Street View feels); the twin's own 30 deg otherwise
      this.camera.fov = this.control === "look" ? 55 : 30; this.camera.updateProjectionMatrix();
    }
    // move the eye and the target together (look mode), keeping the eye where it is relative to the target
    shiftRig(dx, dz, from) { this.rig.tx = from.tx + dx; this.rig.tz = from.tz + dz; }
    bindControls() {
      const c = this.canvas; let drag = null;
      this.control = "orbit";
      c.addEventListener("pointerdown", (e) => {
        this.mouseButtons = e.buttons;
        if (this.control === "free") { e.preventDefault(); try { c.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ } this.stopFly(); this.ueDown(e); return; }
        drag = { x: e.clientX, y: e.clientY, r: Object.assign({}, this.rig), pan: e.shiftKey || e.button === 2, eye: this.camera.position.clone() };
        c.setPointerCapture(e.pointerId); this.stopFly();
      });
      c.addEventListener("mousedown", (e) => { if (e.button === 1) e.preventDefault(); });   // no autoscroll on middle-drag
      c.addEventListener("pointermove", (e) => {
        this.mouseButtons = e.buttons;
        if (this.control === "free") { this.ueMove(e); return; }
        if (!drag) return;
        const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        if (this.control === "look") {
          const R = this.rig, th0 = drag.r.theta, fx = -Math.sin(th0), fz = -Math.cos(th0);   // forward on the ground
          if (drag.pan) {
            // step sideways / forward, like walking: the scene follows the hand
            const s = 0.06;
            this.shiftRig(fz * dx * s + fx * dy * s, -fx * dx * s + fz * dy * s, drag.r);
            return;
          }
          // turn the head about the eye: drag right turns left, drag down looks up (as in Street View)
          R.theta = drag.r.theta + dx * 0.0035;
          R.phi = Math.min(3.05, Math.max(0.1, drag.r.phi + dy * 0.0035));
          const sp = Math.sin(R.phi);
          R.tx = drag.eye.x - R.r * sp * Math.sin(R.theta); R.ty = drag.eye.y - R.r * Math.cos(R.phi); R.tz = drag.eye.z - R.r * sp * Math.cos(R.theta);
          return;
        }
        if (drag.pan) {
          const s = this.rig.r / 900, th = this.rig.theta;   // grab-pan along the ground plane
          this.rig.tx = drag.r.tx - Math.cos(th) * dx * s - Math.sin(th) * dy * s;
          this.rig.tz = drag.r.tz + Math.sin(th) * dx * s - Math.cos(th) * dy * s;
        } else {
          this.rig.theta = drag.r.theta - dx * 0.005;
          this.rig.phi = Math.min(1.45, Math.max(0.05, drag.r.phi - dy * 0.004));
        }
      });
      c.addEventListener("pointerup", (e) => { drag = null; this.mouseButtons = e.buttons; this.ue = null; });
      c.addEventListener("contextmenu", (e) => e.preventDefault());
      // double-click: back to where this view started (set by the chapter as this.home)
      c.addEventListener("dblclick", () => { if (this.home) this.fly(this.home, 900); });
      c.addEventListener("wheel", (e) => {
        e.preventDefault(); this.stopFly();
        if (this.control === "free") { this.ueWheel(e); return; }
        if (this.control === "look") {
          // walk forward / back along the ground
          const th = this.rig.theta, d = -e.deltaY * 0.03;
          this.shiftRig(-Math.sin(th) * d, -Math.cos(th) * d, this.rig);
          return;
        }
        this.rig.r = Math.min(this.rMax, Math.max(14, this.rig.r * Math.exp(e.deltaY * 0.001)));
      }, { passive: false });
    }
    /* ---------- free camera (the camera editor), with Unreal Engine viewport controls ----------
       State fc = { E: eye, th, ph: rig angles, r: distance to the rig target }; fcGoal is where the hand
       has put it and fc eases toward it every frame. With a pivot (Alt-orbit / dolly) the eye rides
       on a sphere around the pivot; otherwise the target is derived from the eye.
       LMB or RMB drag look · MMB or LMB+RMB pan · Alt+LMB orbit · Alt+RMB dolly ·
       Alt+MMB pan · wheel forward/back · RMB+wheel speed · WASD/QE fly (keys set by the editor). */
    sdir(th, ph) { const sp = Math.sin(ph); return new T.Vector3(sp * Math.sin(th), Math.cos(ph), sp * Math.cos(th)); }
    fcInit() {
      const R = this.rig, E = new T.Vector3(R.tx, R.ty, R.tz).addScaledVector(this.sdir(R.theta, R.phi), R.r);
      this.fc = { E, th: R.theta, ph: R.phi, r: R.r, pivot: null };
      this.fcGoal = { E: E.clone(), th: R.theta, ph: R.phi, r: R.r };
      this.flySpeed = this.flySpeed || 1;
    }
    fcPivot() {
      // orbit about whatever is on the optical axis (or 30 m ahead): the view doesn't jump when the pivot is set
      const dir = new T.Vector3(); this.camera.getWorldDirection(dir);
      const ray = new T.Raycaster(this.camera.position.clone(), dir, 0.5, 2000);
      ray.params.Line.threshold = 0.01; ray.params.Points.threshold = 0.01;
      const shown = (o) => { for (; o; o = o.parent) if (!o.visible) return false; return true; };
      const hit = ray.intersectObjects(this.scene.children, true).find((h) => shown(h.object));
      const P = hit ? hit.point : this.camera.position.clone().addScaledVector(dir, 30);
      const d = this.camera.position.distanceTo(P);
      this.fc.pivot = P; this.fc.r = this.fcGoal.r = d;
      this.fcGoal.E = this.fc.E.clone();
    }
    fcDropPivot() {
      if (!this.fc || !this.fc.pivot) return;
      this.fc.pivot = null; this.fcGoal.E = this.fc.E.clone(); this.fcGoal.th = this.fc.th; this.fcGoal.ph = this.fc.ph;
    }
    ueDown(e) {
      if (!this.fc) this.fcInit();
      this.ue = { x: e.clientX, y: e.clientY };
      if (e.altKey && (e.button === 0 || e.button === 2)) this.fcPivot(); else this.fcDropPivot();
    }
    ueMove(e) {
      if (!this.ue || !this.fc) return;
      const dx = e.clientX - this.ue.x, dy = e.clientY - this.ue.y; this.ue.x = e.clientX; this.ue.y = e.clientY;
      const b = e.buttons, G = this.fcGoal, v = this.flySpeed, clampPh = (p) => Math.min(Math.PI - 0.02, Math.max(0.02, p));
      const right = new T.Vector3(Math.cos(G.th), 0, -Math.sin(G.th));
      if (e.altKey && this.fc.pivot) {
        if (b & 1) { G.th -= dx * 0.008; G.ph = clampPh(G.ph + dy * 0.006); }                           // orbit
        else if (b & 2) { G.r = Math.max(0.5, G.r * Math.exp((dy - dx) * 0.004)); }                     // dolly
        if (b & 3) { G.E = this.fc.pivot.clone().addScaledVector(this.sdir(G.th, G.ph), G.r); return; }
      }
      if (b & 4 || (b & 1 && b & 2) || (e.altKey && b & 4)) {                                           // pan
        this.fcDropPivot();
        G.E.addScaledVector(right, dx * 0.03 * v).add(new T.Vector3(0, -dy * 0.03 * v, 0));   // the camera follows the mouse
      } else if (b & 3) {                                                                              // look (LMB or RMB)
        this.fcDropPivot();
        G.th -= dx * 0.0035; G.ph = clampPh(G.ph - dy * 0.0035);
      }
    }
    ueWheel(e) {
      if (!this.fc) this.fcInit();
      if (e.buttons & 2) { this.flySpeed = Math.min(20, Math.max(0.05, this.flySpeed * Math.exp(-e.deltaY * 0.0015))); return; }
      this.fcDropPivot();
      this.fcGoal.E.addScaledVector(this.sdir(this.fcGoal.th, this.fcGoal.ph), e.deltaY * 0.02 * this.flySpeed);
    }
    /* move the camera -- right, up (world), forward (along the view) in metres */
    flyBy(right, up, fwd) {
      if (this.control === "free") {
        if (!this.fc) this.fcInit();
        this.fcDropPivot();
        const G = this.fcGoal, f = this.sdir(G.th, G.ph).negate(), rt = new T.Vector3(Math.cos(G.th), 0, -Math.sin(G.th));
        const d = f.multiplyScalar(fwd).addScaledVector(rt, right).add(new T.Vector3(0, up, 0));
        this.fc.E.add(d); G.E.add(d);
        return;
      }
      const R = this.rig, sp = Math.sin(R.phi);
      const f = new T.Vector3(-sp * Math.sin(R.theta), -Math.cos(R.phi), -sp * Math.cos(R.theta));
      const rt = new T.Vector3(Math.cos(R.theta), 0, -Math.sin(R.theta));
      R.tx += f.x * fwd + rt.x * right; R.ty += f.y * fwd + up; R.tz += f.z * fwd + rt.z * right;
    }
    fcStep(dt) {
      if (!this.fc) this.fcInit();
      const fc = this.fc, G = this.fcGoal, k = 1 - Math.exp(-dt * 16);
      // WASD / QE: W flies along the view, as in Unreal; Shift x4; speed from RMB+wheel
      if (this.keys) {
        const K = this.keys, v = (K.fast ? 24 : 6) * this.flySpeed * Math.min(dt, 0.25);
        const fw = (K.w ? 1 : 0) - (K.s ? 1 : 0), rt = (K.d ? 1 : 0) - (K.a ? 1 : 0), up = (K.e ? 1 : 0) - (K.q ? 1 : 0);
        if (fw || rt || up) this.flyBy(rt * v, up * v, fw * v);
      }
      fc.th += (G.th - fc.th) * k; fc.ph += (G.ph - fc.ph) * k; fc.r += (G.r - fc.r) * k;
      if (fc.pivot) fc.E.copy(fc.pivot).addScaledVector(this.sdir(fc.th, fc.ph), fc.r);
      else fc.E.lerp(G.E, k);
      const R = this.rig, T0 = fc.E.clone().addScaledVector(this.sdir(fc.th, fc.ph), -fc.r);
      R.theta = fc.th; R.phi = fc.ph; R.r = fc.r; R.tx = T0.x; R.ty = T0.y; R.tz = T0.z;
    }
    fly(to, ms) {
      const from = Object.assign({}, this.rig), t0 = performance.now(); ms = ms || 1800;
      let dth = (to.theta !== undefined ? to.theta : from.theta) - from.theta;
      this._fly = (now) => {
        const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        for (const key of ["phi", "r", "tx", "ty", "tz"]) if (to[key] !== undefined) this.rig[key] = from[key] + (to[key] - from[key]) * e;
        this.rig.theta = from.theta + dth * e;
        if (k >= 1) this._fly = null;
      };
    }
    stopFly() { this._fly = null; this.autoOrbit = 0; this.sway = null; }
    setSway(base, amp) { this.sway = amp ? { base, amp, t0: performance.now() } : null; }
    lookAtPlan(x, y, r, phi, theta) { this.fly({ tx: mx(x), tz: mz(y), r: r || 40, phi: phi === undefined ? 0.9 : phi, theta: theta === undefined ? this.rig.theta : theta }); }

    /* ---------- labels ---------- */
    setLabels(defs) {   // [{text, x, y, h, cls}] in plan mm + height m
      this.labelDefs = defs || [];
      this.labels.innerHTML = "";
      this.labelDefs.forEach((d) => { const n = document.createElement("div"); n.textContent = d.text; if (d.cls) n.className = d.cls; this.labels.appendChild(n); d.el = n; });
    }
    drawLabels() {
      if (!this.labelDefs.length || !this.host) return;
      const r = this.host.getBoundingClientRect(), v = new T.Vector3();
      this.labelDefs.forEach((d) => {
        const yOff = d.layer ? this.layerY(d.layer) : 0;
        v.set(mx(d.x), (d.h || 0) + yOff, mz(d.y)).project(this.camera);
        const on = v.z < 1 && Math.abs(v.x) < 1.1 && Math.abs(v.y) < 1.1 && (d.show ? d.show() : true);
        d.el.style.opacity = on ? 1 : 0;
        d.el.style.left = ((v.x + 1) / 2) * r.width + "px"; d.el.style.top = ((1 - v.y) / 2) * r.height + "px";
      });
    }
    layerY(name) {
      const o = this.cache[this.opt]; return o[name] ? o[name].position.y : 0;
    }

    /* ---------- tweening + frame ---------- */
    tween(key, to, ms, onStep) {
      const from = this[key], t0 = performance.now();
      this._tw = this._tw || {};
      this._tw[key] = (now) => {
        const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3);
        this[key] = from + (to - from) * e; onStep && onStep();
        if (k >= 1) delete this._tw[key];
      };
    }
    tweenObj(obj, key, to, ms, done) {
      const from = obj[key], t0 = performance.now(); this._two = this._two || [];
      this._two.push((now) => {
        const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3);
        obj[key] = from + (to - from) * e;
        if (k >= 1) { done && done(); return true; }
      });
    }
    frame() {
      const now = performance.now(), dt = this.clock.getDelta();
      if (this._fly) this._fly(now);
      // the editor's free camera (a fly in progress owns the rig; the free camera re-reads it afterwards)
      if (this.control === "free") { if (this._fly) this.fc = null; else this.fcStep(dt); }
      if (this.autoOrbit) this.rig.theta += dt * this.autoOrbit;
      if (this.sway && !this._fly) this.rig.theta = this.sway.base + this.sway.amp * Math.sin((now - this.sway.t0) / 5200);
      for (const k in this._tw || {}) this._tw[k](now);
      if (this._two) this._two = this._two.filter((f) => !f(now));
      if (this.pT < 1) { this.pT = Math.min(1, (now - this.pStart) / 2600); this.updatePeople(this.pT); }
      if (this.stage.visible) this.stage.material.opacity = 0.6 + 0.3 * Math.sin(now / 300);
      const R = this.rig, cp = Math.cos(R.phi), sp = Math.sin(R.phi);
      this.camera.position.set(R.tx + R.r * sp * Math.sin(R.theta), R.ty + R.r * cp, R.tz + R.r * sp * Math.cos(R.theta));
      this.camera.lookAt(R.tx, R.ty, R.tz);
      if (this.site) this.site.frame(this.camera);
      this.renderer.render(this.scene, this.camera);
      this.drawLabels();
    }
  }

  Twin.SCEN = SCEN;
  Twin.mm = { mx, mz };
  window.Twin = Twin;
})();
