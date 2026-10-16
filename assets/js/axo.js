/* Axo — the two layout options as clean axonometric drawings, one above the other, moving in step ("One model, two options").
   Ritika (11.10): the old 3D view read as a white film, cluttered, and its idea didn't come across. This uses the deck's own axo
   language instead: a crisp line plan with its furniture, the floor coloured by the deck's zones, walls cut low so the plan reads
   through them, and ONE volume standing up per beat. Orthographic camera, opaque materials, no fog, no site.
   Both drawings share one camera, so they turn, tilt and zoom together; either can fill the screen (⤢).
   A day at Mitigata plays on them too, one option at a time: people (a round head on a triangular body, at human scale,
   scattered, never in rows) take their places for each hour, and an event's volume rises with its crowd in green.
   No flicker while it moves (Ritika): faces sit behind their lines (polygon offset), every floor fill has its own height,
   and the see-through layers draw in a fixed order. */
(function () {
  const D = window.MX_DATA, TEX = window.MX_TEX, T = window.THREE, P2 = window.Plan2D;
  if (!T || !P2) return;
  const CX = 42000, CY = 17500;
  const mx = (x) => (x - CX) / 1000, mz = (y) => -(y - CY) / 1000;

  const OPTS = ["opt1", "opt2"];             // what an axo shows unless told otherwise (the appendix's meeting rooms)
  const optName = (o) => "Layout Option " + o.replace("opt", "").padStart(2, "0");
  const HOME = { theta: -0.36, phi: 0.98, zoom: 1 };
  const TOP = { theta: 0, phi: 0.04, zoom: 1 };
  // what has to fit in the frame: the floor plate and the strip east of it (lift lobby side)
  const FIT = D.zones.annot.outline.concat([[77500, 1300], [77500, 34300], [63000, 37300]]);   // the last: the entrance triangle

  const ptsOf = (d) => d.split("M").filter((s) => s.trim()).map((sp) => {
    const n = sp.replace(/[LZ]/g, " ").trim().split(/[\s,]+/).map(Number), out = [];
    for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], n[i + 1]]);
    return out;
  }).filter((p) => p.length > 2);
  const area = (p) => Math.abs(p.reduce((a, q, i) => { const r = p[(i + 1) % p.length]; return a + q[0] * r[1] - r[0] * q[1]; }, 0)) / 2;
  const shapeOf = (poly) => new T.Shape(poly.map(([x, y]) => new T.Vector2(mx(x), (y - CY) / 1000)));
  // the plan render's colours: the zone pastel at 72% on white
  const tint = (hex, a) => { const c = new T.Color(hex), w = new T.Color(0xffffff); return w.lerp(c, a === undefined ? 0.72 : a); };
  // faces step back in depth so the lines drawn on their edges always win; where faces coincide (a column traced by
  // the shell, a partition over the shell) a fixed priority decides: columns, then glass, then partitions, then the shell
  const behind = (m, k) => Object.assign(m, { polygonOffset: true, polygonOffsetFactor: k === undefined ? 1 : k, polygonOffsetUnits: 2 * (k === undefined ? 1 : k) });
  const LIFT = 0.01;                         // lines sit 1 cm above the faces they trace
  const STAGE = 0xffffff;                    // a white page, as in Ritika's reference axo (12.10): bold outlines and grey faces make it read
  const WALL = 2.1;                          // walls stand to door height: rooms read as boxes, the floor behind stays in view (Ritika)
  const INK = 0x111111;                      // the outlines
  // meeting rooms by size: a blue ramp, light for the small rooms, deep for the large (Ritika: each size called out)
  const MEET_C = { 2: 0xc9d8f2, 4: 0xa6bfeb, 5: 0x86a6e0, 6: 0x6a8fd4, 8: 0x4f77c2, 10: 0x3a61ab, 14: 0x264a8f };
  const G0 = -((window.MX_SITE && window.MX_SITE.slabZ) || 7.6);   // the street, 7.6 m under Level 03: the floor floats above it
  // a flat band along a line, a pen weight in metres: [ax, az, bx, bz] segments at height y, w wide
  function bands(segs, y, w) {
    const pos = [];
    for (const [ax, az, bx, bz] of segs) {
      const dx = bx - ax, dz = bz - az, L = Math.hypot(dx, dz); if (L < 1e-4) continue;
      const nx = (-dz / L) * w / 2, nz = (dx / L) * w / 2, ex = (dx / L) * w / 2, ez = (dz / L) * w / 2;   // a little past each end, so corners close
      const a1 = [ax - ex + nx, az - ez + nz], a2 = [ax - ex - nx, az - ez - nz], b1 = [bx + ex + nx, bz + ez + nz], b2 = [bx + ex - nx, bz + ez - nz];
      pos.push(a1[0], y, a1[1], a2[0], y, a2[1], b2[0], y, b2[1], a1[0], y, a1[1], b2[0], y, b2[1], b1[0], y, b1[1]);
    }
    const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3)); return g;
  }
  // people: four standing figures, drawn once as white silhouettes (tinted per person), feet at the bottom (64 x 192 px = 0.62 x 1.86 m)
  const FIGS = [
    (c) => { c.arc(32, 17, 10.5, 0, 7); c.moveTo(14, 34); c.quadraticCurveTo(32, 26, 50, 34); c.lineTo(54, 98); c.lineTo(47, 99); c.lineTo(45, 58); c.lineTo(43, 104);
      c.lineTo(42, 188); c.lineTo(34, 188); c.lineTo(32, 112); c.lineTo(30, 188); c.lineTo(22, 188); c.lineTo(21, 104); c.lineTo(19, 58); c.lineTo(17, 99); c.lineTo(10, 98); c.closePath(); },
    (c) => { c.arc(32, 18, 10, 0, 7); c.moveTo(17, 35); c.quadraticCurveTo(32, 28, 47, 35); c.lineTo(51, 92); c.lineTo(45, 93); c.lineTo(43, 62); c.lineTo(42, 76); c.lineTo(50, 138);
      c.lineTo(37, 138); c.lineTo(37, 188); c.lineTo(32, 188); c.lineTo(31, 140); c.lineTo(30, 188); c.lineTo(25, 188); c.lineTo(26, 138); c.lineTo(14, 138); c.lineTo(22, 76); c.lineTo(21, 62); c.lineTo(19, 93); c.lineTo(13, 92); c.closePath(); },
    (c) => { c.arc(33, 17, 10.5, 0, 7); c.moveTo(16, 34); c.quadraticCurveTo(33, 26, 50, 34); c.lineTo(58, 92); c.lineTo(52, 95); c.lineTo(45, 62); c.lineTo(44, 104);
      c.lineTo(56, 186); c.lineTo(48, 188); c.lineTo(33, 118); c.lineTo(20, 188); c.lineTo(11, 186); c.lineTo(22, 104); c.lineTo(20, 62); c.lineTo(12, 94); c.lineTo(6, 91); c.closePath(); },
    (c) => { c.arc(31, 18, 10, 0, 7); c.moveTo(16, 35); c.quadraticCurveTo(31, 28, 46, 35); c.lineTo(52, 90); c.lineTo(58, 90); c.lineTo(60, 122); c.lineTo(44, 122); c.lineTo(45, 92);
      c.lineTo(42, 66); c.lineTo(41, 110); c.lineTo(40, 188); c.lineTo(33, 188); c.lineTo(31, 118); c.lineTo(29, 188); c.lineTo(22, 188); c.lineTo(21, 110); c.lineTo(20, 66); c.lineTo(18, 94); c.lineTo(12, 93); c.closePath(); },
  ];
  let FIGTEX = null;
  const figTex = () => FIGTEX || (FIGTEX = FIGS.map((draw) => {
    const cv = document.createElement("canvas"); cv.width = 64; cv.height = 192;
    const c = cv.getContext("2d"); c.fillStyle = "#fff"; c.beginPath(); draw(c); c.fill();
    const t = new T.CanvasTexture(cv); t.anisotropy = 4; return t;
  }));

  /* ---------- a day on the floor: people as a round head on a triangular body, at human scale (Ritika) ----------
     who is where, by zone type (the twin's scenarios, twin.js SCEN), or at an event: never in rows — scattered */
  const SCEN = {
    workday: { soc: 72, focus: 190, meet: 38, collab: 10, cafe: 5 },
    lunch: { soc: 60, focus: 118, cafe: 52, collab: 40, meet: 22 },
    e50: { soc: 70, focus: 150, meet: 30, collab: 15, event: ["50", 50] },
    e100: { soc: 60, focus: 70, meet: 10, collab: 15, cafe: 10, event: ["100", 100] },
    e200: { soc: 50, cafe: 18, collab: 12, event: ["200", 200] },
  };
  const PODIUM = "200", PODIUM_H = 0.45, SPEAKER = 0xcc0000;   // the speaker in the deck's red (Ritika)   // the town hall has a podium (450 mm, Ritika) and a speaker on it
  const NP = 332, PERSON = 0x8c8c8c, GUEST = 0x04db7f;   // grey figures (Ritika); event people in the deck green
  const rng = (seed) => { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
  const inPoly = (x, y, p) => { let c = false; for (let i = 0, j = p.length - 1; i < p.length; j = i++) { const [xi, yi] = p[i], [xj, yj] = p[j]; if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return c; };
  const bboxP = (p) => p.reduce((b, [x, y]) => [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)], [1e9, 1e9, -1e9, -1e9]);
  // the floor's occupied spots, hashed in 1.3 m cells, so a crowd of 200 places quickly
  const CELL = 1300, cellOf = (x, y) => Math.floor(x / CELL) + "," + Math.floor(y / CELL);
  const floorTaken = () => ({ g: new Map() });
  const near = (tk, x, y, g) => {
    const cx = Math.floor(x / CELL), cy = Math.floor(y / CELL);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (const q of tk.g.get(cx + i + "," + (cy + j)) || []) if ((q[0] - x) ** 2 + (q[1] - y) ** 2 < g * g) return true;
    return false;
  };
  const take = (tk, x, y) => { const k = cellOf(x, y); (tk.g.get(k) || tk.g.set(k, []).get(k)).push([x, y]); };
  // n people standing about in small groups (1–5, 0.5–1.1 m around a spot), the groups loose across the area (Ritika)
  function groups(polys, n, seed, tk, keepOff) {
    const r = rng(seed * 3 + 1), out = [], centres = scatter(polys, Math.ceil(n / 2.6), seed, 1800, floorTaken(), keepOff);
    let tries = 0;
    for (let ci = 0; out.length < n && tries < n * 600; ci = (ci + 1) % Math.max(1, centres.length)) {
      const c = centres[ci]; if (!c) break;
      const size = 1 + Math.floor(r() * 5);
      for (let j = 0; j < size && out.length < n; j++) {
        tries++;
        const a = r() * 6.283, d = j ? 500 + r() * 600 : r() * 250, x = c[0] + Math.cos(a) * d, y = c[1] + Math.sin(a) * d;
        if (!polys.some((p) => inPoly(x, y, p)) || (keepOff && keepOff(x, y)) || near(tk, x, y, 520)) continue;
        out.push([x, y]); take(tk, x, y);
      }
    }
    if (out.length < n) scatter(polys, n - out.length, seed + 5, 600, tk, keepOff).forEach((p) => out.push(p));   // a tight room: fill the rest loosely
    return out;
  }
  // n points spread over the polygons by area, each at least `gap` mm from every spot already taken: never in rows
  function scatter(polys, n, seed, gap, tk, keepOff) {
    const r = rng(seed), out = [], areas = polys.map((p) => Math.max(1, area(p))), tot = areas.reduce((a, b) => a + b, 0);
    if (!polys.length) return out;
    let tries = 0;
    while (out.length < n && tries < n * 400) {
      tries++;
      let u = r() * tot, i = 0; while (u > areas[i] && i < areas.length - 1) u -= areas[i++];
      const b = bboxP(polys[i]), x = b[0] + r() * (b[2] - b[0]), y = b[1] + r() * (b[3] - b[1]);
      if (!inPoly(x, y, polys[i]) || (keepOff && keepOff(x, y))) continue;
      if (near(tk, x, y, tries > n * 200 ? gap * 0.7 : gap)) continue;
      out.push([x, y]); take(tk, x, y);
    }
    return out;
  }

  class Axo {
    /* cfg.opts: every option it can show (the views are built once each, as they are first shown); cfg.slots: the two on
       view, top and bottom. With more options than slots, each view's tag is a dropdown (One model, Sathwick 15.10) */
    constructor(host, cfg) {
      this.host = host;
      this.opts = (cfg && cfg.opts) || OPTS;
      this.cache = {};
      this.renderer = new T.WebGLRenderer({ antialias: true, alpha: false });
      this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
      this.renderer.setClearColor(0xffffff, 1);
      this.renderer.setScissorTest(true);
      this.evOver = null;   // event areas a slide hands in (setEvents), before the drawings' own
      this.podOver = null;  // the town hall's podium outline a slide hands in (setPodium)
      host.appendChild(this.renderer.domElement);
      this.over = document.createElement("div"); this.over.className = "axo-over"; host.appendChild(this.over);
      this.camera = new T.OrthographicCamera(-1, 1, 1, -1, 0.5, 900);
      this.dummy = new T.Object3D(); this.col = new T.Color(); this.one = null;
      this.views = ((cfg && cfg.slots) || this.opts.slice(0, 2)).map((o) => this.viewOf(o));
      // colours: the deck's zone pastels (1) or a white floor (0) · fx, fy, fw: a point to frame (plan mm) and how far toward it
      const base = { soc: 0, guest: 0, route: 0, meet: 0, mono: 0, colours: 1, furn: 1, fx: 40300, fy: 17200, fw: 0, px: 0, py: 0 };   // px, py: a drag's pan, in view units
      this.s = Object.assign({}, base, TOP);    // what is drawn now
      this.t = Object.assign({}, base, HOME);   // where it is heading
      this.homeT = Object.assign({}, HOME, { fw: 0, px: 0, py: 0 });   // the beat's own view: what Reset and double-click return to
      this.colAt = 1;
      this.texts = { labels: [[], []], captions: ["", ""] }; this.solo = null;
      this.clock = new T.Clock();
      this.bind();
      document.addEventListener("keydown", (e) => { if (e.key === "Escape" && this.solo !== null) this.setSolo(null); });
      new ResizeObserver(() => this.resize()).observe(host);
      this.resize();
    }

    /* ---------- one option as a drawing ---------- */
    buildView(opt) {
      const d = D[opt], z = D.zones[opt], scene = new T.Scene(), v = { opt, scene, fills: [] };
      // light that gives the reference's faces: tops flat white, one face family white, the other a soft grey (about #d9d9d9)
      scene.add(new T.AmbientLight(0xffffff, 0.78));
      // a low light from behind the floor: the two wall faces read apart, white and grey (no shadows: Ritika, 13.10)
      const sun = new T.DirectionalLight(0xffffff, 0.3); sun.position.set(-26, 34, -22); sun.target.position.set(0, 0, 0); scene.add(sun, sun.target);
      const OUT = D.zones.annot.outline;
      // the street under the floor: a subtle square grid (Ritika), the two Hallmark blocks in pale grey, dashed drop lines from the slab
      const grid = [], E = 160, gx = mx(40300), gz = mz(17200), GS = 3;
      for (let i = -E; i <= E; i += GS) grid.push(gx + i, G0, gz - E, gx + i, G0, gz + E, gx - E, G0, gz + i, gx + E, G0, gz + i);
      const gg = new T.BufferGeometry(); gg.setAttribute("position", new T.Float32BufferAttribute(grid, 3));
      scene.add(new T.LineSegments(gg, new T.LineBasicMaterial({ color: 0xe6e6e6 })));
      (window.MX_SITE ? window.MX_SITE.blocks : []).forEach((bl) => {
        const m = new T.Mesh(new T.ShapeGeometry(new T.Shape(bl.ring.map(([x, zz]) => new T.Vector2(x, -zz)))), new T.MeshBasicMaterial({ color: 0xf2f2f2, side: T.DoubleSide }));
        m.rotation.x = -Math.PI / 2; m.position.y = G0 + 0.02; scene.add(m);
      });
      const drops = []; OUT.forEach(([x, y]) => drops.push(mx(x), -0.5, mz(y), mx(x), G0, mz(y)));
      const dl = new T.BufferGeometry(); dl.setAttribute("position", new T.Float32BufferAttribute(drops, 3));
      const dline = new T.LineSegments(dl, new T.LineDashedMaterial({ color: 0x666666, dashSize: 0.6, gapSize: 0.45 })); dline.computeLineDistances(); scene.add(dline);
      // the slab: a thick white plate, its edge in a bold pen
      const slab = new T.Mesh(new T.ExtrudeGeometry(shapeOf(OUT), { depth: 0.5, bevelEnabled: false }),
        [behind(new T.MeshBasicMaterial({ color: 0xffffff })), behind(new T.MeshLambertMaterial({ color: 0xf4f4f4 }))]);
      slab.rotation.x = -Math.PI / 2; slab.position.y = -0.5; scene.add(slab);
      const se = new T.LineSegments(new T.EdgesGeometry(slab.geometry, 20), new T.LineBasicMaterial({ color: INK }));
      se.rotation.copy(slab.rotation); se.position.copy(slab.position); scene.add(se);
      const ring = (pts) => pts.map((q, i) => { const r = pts[(i + 1) % pts.length]; return [mx(q[0]), mz(q[1]), mx(r[0]), mz(r[1])]; });
      const slabPen = new T.Mesh(bands(ring(OUT), 0.09, 0.16), new T.MeshBasicMaterial({ color: INK, side: T.DoubleSide })); slabPen.renderOrder = 9; scene.add(slabPen);
      // the floor coloured to every space's outline, as on the plan (the core, not in contract, in grey)
      // each fill on its own plane: corridor, then team zones, then the core, then rooms, each a little above the last
      let nth = 0;
      const DZ = P2.DZ, flat = (polys, col, y) => polys.forEach((p) => {
        const m = new T.Mesh(new T.ShapeGeometry(shapeOf(p)), new T.MeshBasicMaterial({ color: col, side: T.DoubleSide }));
        m.rotation.x = -Math.PI / 2; m.position.y = y + (nth++) * 0.0006; scene.add(m);
        v.fills.push([m.material, m.material.color.clone()]);
      });
      const hv = z.hover;
      hv.rooms.filter((r) => P2.roomType(r.name) === "circ").forEach((r) => flat(ptsOf(r.d), tint(P2.CIRC_COL, 1), 0.01));
      hv.teams.forEach((t) => flat(ptsOf(t.zone), tint(DZ[/SOC/i.test(t.name) ? "soc" : "focus"].c), 0.03));
      flat(z.zones.filter((zz) => zz.type === "core").map((zz) => zz.poly), tint(DZ.nic.c, 0.9), 0.05);
      hv.rooms.forEach((r) => { const ty = P2.roomType(r.name); if (ty !== "circ") flat(ptsOf(r.d), tint(DZ[P2.dzOf(ty, r.name)].c, ty === "core" ? 0.9 : 0.72), 0.07); });
      // furniture: the plan's linework, dark, on top of the colours
      const tex = new T.TextureLoader().load(TEX[opt]);
      tex.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
      const rw = d.raster.w / d.raster.px_per_m, rh = d.raster.h / d.raster.px_per_m;
      const furn = new T.Mesh(new T.PlaneGeometry(rw, rh), new T.MeshBasicMaterial({ map: tex, color: 0x1e1e1e, transparent: true, opacity: 0.9, depthWrite: false }));
      furn.rotation.x = -Math.PI / 2; furn.position.set(mx(rw * 500), 0.14, mz(d.size[1] - rh * 500)); furn.renderOrder = 10; scene.add(furn);
      v.furn = furn;
      // walls as white massing at door height (Ritika's reference): closed outlines become solids with flat white tops, open lines
      // become thin walls; the curtain wall at the edge of the floor stays glass; every top is traced in a bold pen
      const toXZ = (p) => { const o = []; for (let i = 0; i < p.length; i += 2) o.push([p[i], p[i + 1]]); return o; };
      const closed = (p) => p.length >= 8 && p[0] === p[p.length - 2] && p[1] === p[p.length - 1];
      const segD = (px, py, ax, ay, bx, by) => { const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy || 1, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L)); return Math.hypot(px - ax - t * dx, py - ay - t * dy); };
      const edgeOf = (x, y) => OUT.some((q, i) => { const r = OUT[(i + 1) % OUT.length]; return segD(x, y, q[0], q[1], r[0], r[1]) < 650; });
      const onEdge = (p) => toXZ(p).every(([x, y]) => edgeOf(x, y));
      const caps = [], sides = [], glassQ = [], pens = [], lines = [];
      const side = (arr, ax, az, bx, bz, h) => arr.push(ax, 0, az, bx, 0, bz, bx, h, bz, ax, 0, az, bx, h, bz, ax, h, az);
      const addPoly = (pts, h, solid) => {       // pts: plan mm, open, or closed without the repeated last point
        const n = pts.length, P = pts.map(([x, y]) => [mx(x), mz(y)]);
        for (let i = 0; i < (solid ? n : n - 1); i++) {
          const a0 = P[i], b0 = P[(i + 1) % n];
          if (Math.hypot(b0[0] - a0[0], b0[1] - a0[1]) < 0.04) continue;
          side(sides, a0[0], a0[1], b0[0], b0[1], h);
          pens.push([a0[0], a0[1], b0[0], b0[1]]);
          lines.push(a0[0], h + 2 * LIFT, a0[1], b0[0], h + 2 * LIFT, b0[1]);
        }
        if (solid && n >= 3) T.ShapeUtils.triangulateShape(P.map(([x, zz]) => new T.Vector2(x, zz)), []).forEach((f) => f.forEach((k) => caps.push(P[k][0], h, P[k][1])));
      };
      const glassLine = (p, pen) => { const P = toXZ(p); for (let i = 1; i < P.length; i++) {
        const ax = mx(P[i - 1][0]), az = mz(P[i - 1][1]), bx = mx(P[i][0]), bz = mz(P[i][1]);
        side(glassQ, ax, az, bx, bz, WALL);
        if (pen) pens.push([ax, az, bx, bz]); else lines.push(ax, WALL + 2 * LIFT, az, bx, WALL + 2 * LIFT, bz);
      } };
      // the long south façade (y 2150, from the boardroom's end to the east corner) is solid wall, not glazing (Ritika)
      const southWall = (p) => toXZ(p).every(([x, y]) => x >= 22400 && Math.abs(y - 2150) < 650);
      d.vec.shell.forEach((p) => { if (onEdge(p) && southWall(p)) addPoly(toXZ(p), WALL, false); else if (onEdge(p)) glassLine(p, true); else if (closed(p)) addPoly(toXZ(p).slice(0, -1), WALL, true); else addPoly(toXZ(p), WALL, false); });
      d.vec.partition.forEach((p) => { if (closed(p)) addPoly(toXZ(p).slice(0, -1), WALL, true); else addPoly(toXZ(p), WALL, false); });
      d.fills.forEach((f) => {
        let pts = toXZ(f); if (area(pts) < 0.05e6) return;
        if (pts[0][0] === pts[pts.length - 1][0] && pts[0][1] === pts[pts.length - 1][1]) pts = pts.slice(0, -1);
        addPoly(pts, WALL, true);
      });
      d.vec.glass.forEach((p) => glassLine(p, false));
      const geo = (arr) => { const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(arr, 3)); g.computeVertexNormals(); return g; };
      scene.add(new T.Mesh(geo(sides), behind(new T.MeshLambertMaterial({ color: 0xffffff, side: T.DoubleSide }), 2)));
      scene.add(new T.Mesh(geo(caps), behind(new T.MeshBasicMaterial({ color: INK, side: T.DoubleSide }), 2)));   // the cut: walls and columns in black poché (Ritika)
      const gl = new T.Mesh(geo(glassQ), behind(new T.MeshBasicMaterial({ color: 0xcfe3ec, transparent: true, opacity: 0.3, side: T.DoubleSide, depthWrite: false }), 1));
      gl.renderOrder = 11; scene.add(gl);
      scene.add(new T.Mesh(bands(pens, WALL + LIFT, 0.14), new T.MeshBasicMaterial({ color: INK, side: T.DoubleSide })));   // single-line walls cut as a filled black band
      scene.add(new T.LineSegments(geo(lines), new T.LineBasicMaterial({ color: INK })));
      // planting from the drawing: olive bushes, as in the reference
      const pl = d.plants || [];
      if (pl.length) {
        const bush = new T.InstancedMesh(new T.IcosahedronGeometry(1, 1), new T.MeshLambertMaterial({ color: 0xffffff }), pl.length * 3);
        const bd = new T.Object3D(), bc = new T.Color(), br = rng(31 + this.opts.indexOf(opt));
        pl.forEach(([x, y, r], i) => {
          const R = Math.max(0.2, r / 1000) * 0.8;
          for (let j = 0; j < 3; j++) {
            const a0 = br() * 6.28, o = j ? R * 0.55 : 0;
            bd.position.set(mx(x) + Math.cos(a0) * o, R * (0.9 + br() * 0.35), mz(y) + Math.sin(a0) * o);
            bd.scale.setScalar(R * (j ? 0.75 : 1)); bd.updateMatrix(); bush.setMatrixAt(i * 3 + j, bd.matrix);
            bush.setColorAt(i * 3 + j, bc.setHex(j ? 0xb7b97c : 0xcfcf95));
          }
        });
        scene.add(bush);
      }
      // the main entrance: the deck's red triangle, pointing in
      const ent = D.zones.annot.labels.find((l) => l.kind === "entry");
      if (ent) {
        const [x, y] = ent.at, tri = new T.Mesh(new T.ShapeGeometry(shapeOf([[x - 1800, y + 4700], [x + 1800, y + 4700], [x, y + 1500]])), new T.MeshBasicMaterial({ color: 0xcc0000, side: T.DoubleSide }));
        tri.rotation.x = -Math.PI / 2; tri.position.y = 0.16; scene.add(tri);
        v.entry = [x, y];
      }
      // the one volume of each beat
      const vol = (polys, h, face, edge, op) => {
        const g = new T.Group();
        polys.forEach((p) => {
          const m = new T.Mesh(new T.ExtrudeGeometry(shapeOf(p), { depth: h, bevelEnabled: false }), new T.MeshBasicMaterial({ color: face, transparent: true, opacity: op === undefined ? 0.3 : op, depthWrite: false, side: T.DoubleSide }));
          m.rotation.x = -Math.PI / 2; m.renderOrder = 12;
          const e = new T.LineSegments(new T.EdgesGeometry(m.geometry, 25), new T.LineBasicMaterial({ color: edge }));
          e.rotation.copy(m.rotation); e.renderOrder = 13;
          g.add(m, e);
        });
        g.scale.y = 0.001; g.visible = false; scene.add(g);
        return g;
      };
      const zs = (types) => z.zones.filter((zz) => types.includes(zz.type));
      const top = (list, h) => { let A = 0, cx = 0, cy = 0; list.forEach((zz) => { const c = P2.centroid(zz.poly); A += zz.area; cx += c[0] * zz.area; cy += c[1] * zz.area; }); return [cx / A, cy / A, h]; };
      v.soc = vol(zs(["soc"]).map((zz) => zz.poly), 3.2, 0x04db7f, 0x03a862);
      v.socAt = top(zs(["soc"]), 3.2);
      v.podAt = {};   // the town hall's podium, by event level: [x, y, toward-x, toward-y], found on first use
      v.guest = vol(zs(["arrive", "board"]).map((zz) => zz.poly), 3.2, 0xfbbc04, 0xc98a00);
      v.guestAt = top(zs(["board"]), 3.2);
      v.studio = vol(zs(["studio"]).map((zz) => zz.poly), 3.2, 0xfbbc04, 0xc98a00);   // the podcast studio stands up with the guests (Ritika)
      v.studioAt = top(zs(["studio"]), 3.2);
      v.arriveAt = top(zs(["arrive"]), 3.2);   // reception, for its callout (Ritika, 14.10)
      // the meeting rooms, one shade per size, so the sizes read apart (Ritika); the size from each room's tag ("Meeting room · 6 PAX")
      v.meet = new T.Group(); v.meet.visible = false; scene.add(v.meet);
      const bySize = {}; zs(["meet"]).forEach((zz) => { const m = /(\d+)\s*PAX/i.exec(zz.name || ""), k = m ? +m[1] : 0; (bySize[k] = bySize[k] || []).push(zz.poly); });
      Object.keys(bySize).forEach((k) => { const c = MEET_C[k] || 0x6f8fc9, g = vol(bySize[k], 3.2, c, 0x2f4f80, 0.45); scene.remove(g); g.visible = true; g.scale.y = 1; v.meet.add(g); });
      v.meet.scale.y = 0.001;
      // the visitor's walk, from the front door; and on from reception to the podcast studio, if the slide hands one in (Ritika, 14.10)
      const walk = (pts, over) => {
        // a bold red line on the floor, drawn from its start, with an arrowhead at its end (Ritika's reference)
        const curve = new T.CatmullRomCurve3(pts.map(([x, y]) => new T.Vector3(mx(x), 0.2, mz(y))), false, "catmullrom", 0.05);
        const L = curve.getLength(), HEAD = 1.5, n = Math.max(60, Math.round(L * 3)), segs = [];
        let prev = curve.getPointAt(0);
        for (let i = 1; i <= n; i++) { const q = curve.getPointAt(((L - HEAD * 0.9) / L) * (i / n)); segs.push([prev.x, prev.z, q.x, q.z]); prev = q; }
        const rg = bands(segs, 0.2, 0.45), line = new T.Mesh(rg, new T.MeshBasicMaterial({ color: 0xcc0000, side: T.DoubleSide }));
        const N = rg.getAttribute("position").count; rg.setDrawRange(0, 0); line.renderOrder = 14; scene.add(line);
        if (over) [line.material].forEach((m) => (m.depthTest = false));   // drawn over the walls: in Option 02 the corridor runs behind the core
        const tip = curve.getPointAt(1), back = curve.getPointAt((L - HEAD) / L), hx = tip.x - back.x, hz = tip.z - back.z, hl = Math.hypot(hx, hz) || 1;
        const px = (-hz / hl) * 0.65, pz = (hx / hl) * 0.65, hg = new T.BufferGeometry();
        hg.setAttribute("position", new T.Float32BufferAttribute([back.x + px, 0.21, back.z + pz, back.x - px, 0.21, back.z - pz, tip.x, 0.21, tip.z], 3));
        const end = new T.Mesh(hg, new T.MeshBasicMaterial({ color: 0xcc0000, side: T.DoubleSide }));
        end.renderOrder = 14; end.visible = false; scene.add(end);
        if (over) { end.material.depthTest = false; line.renderOrder = end.renderOrder = 16; }
        return { line, N, end };
      };
      const rt = z.routes && z.routes.visitor;
      if (rt) {
        const w = walk(rt.pts); v.route = w.line; v.routeN = w.N; v.routeEnd = w.end;
        const end = rt.pts[rt.pts.length - 1];
        v.routeAt = [end[0], end[1], 0.6];
      }
      v.walkOf = walk;   // the studio leg is handed in later (setStudioWalk)
      // a day: people as grey standing figures (four poses), 5.5 ft tall (1.68 m, Ritika), each turning to face the camera like a cut-out
      const fg = new T.PlaneGeometry(0.57, 1.71); fg.translate(0, 0.855, 0);   // the figure fills 188 of the 192 px: 1.71 x 188/192 = 1.68 m
      v.pFig = figTex().map((tex) => {
        const m = new T.InstancedMesh(fg, new T.MeshBasicMaterial({ map: tex, alphaTest: 0.5, side: T.DoubleSide, color: 0xffffff }), Math.ceil(NP / FIGS.length));
        m.instanceMatrix.setUsage(T.DynamicDrawUsage); m.renderOrder = 15; m.frustumCulled = false; scene.add(m);
        return m;
      });
      v.lobby = z.lobby || D.zones.opt1.lobby;
      const P = (v.p = { from: new Float32Array(NP * 2), to: new Float32Array(NP * 2), now: new Float32Array(NP * 2), vis: new Float32Array(NP), visTo: new Float32Array(NP), delay: new Float32Array(NP), green: new Uint8Array(NP), look: new Float32Array(NP * 2).fill(NaN), lift: new Float32Array(NP), t: 1, t0: 0 });
      const rd = rng(7 + this.opts.indexOf(opt));
      for (let k = 0; k < NP; k++) { P.now[k * 2] = P.to[k * 2] = v.lobby[0]; P.now[k * 2 + 1] = P.to[k * 2 + 1] = v.lobby[1]; P.delay[k] = rd() * 0.6; }
      this.drawPeople(v, 1);
      v.vol = vol; v.ev = {}; v.evS = {}; v.evOn = null; v.headcount = 0;
      // overlay: tag, labels, caption, north
      v.el = document.createElement("div"); v.el.className = "axo-view";
      const pick = this.opts.length > 2 ? `<label class="frame-tag axo-pick"><select aria-label="Layout option">${this.opts.map((o) => `<option value="${o}"${o === opt ? " selected" : ""}>${optName(o)}</option>`).join("")}</select></label>` : `<span class="frame-tag">${optName(opt)}</span>`;
      v.el.innerHTML = `${pick}<svg class="axo-lines"></svg><div class="axo-lbls"></div><p class="axo-cap"></p><div class="axo-north"><i></i><b>N</b></div>` +
        `<ul class="lgd axo-solo-lgd"></ul><div class="axo-ctl"><button type="button" data-z="in" aria-label="Zoom in">+</button><button type="button" data-z="out" aria-label="Zoom out">−</button><button type="button" data-z="reset" title="Back to this beat's view">Reset</button></div><button type="button" class="axo-fs" title="Full screen" aria-label="Show this option full screen">⤢</button>`;
      v.el.querySelector(".axo-fs").addEventListener("click", (e) => { e.currentTarget.blur(); const i = this.views.indexOf(v); this.setSolo(this.solo === i ? null : i); });   // the arrow keys stay with the deck
      const sel = v.el.querySelector(".axo-pick select");
      if (sel) sel.addEventListener("change", () => { sel.blur(); this.setSlot(this.views.indexOf(v), sel.value); });
      v.el.querySelector(".axo-ctl").addEventListener("click", (e) => {
        const b = e.target.closest("button"); if (!b) return; b.blur();
        if (b.dataset.z === "reset") this.home(); else this.set({ zoom: Math.min(4, Math.max(0.8, this.t.zoom * (b.dataset.z === "in" ? 1.4 : 1 / 1.4))) });
      });
      this.over.appendChild(v.el);
      return v;
    }

    /* each option's drawing, built the first time it is shown; the slide's podium and studio walk go on it too */
    viewOf(opt) {
      if (this.cache[opt]) return this.cache[opt];
      const v = (this.cache[opt] = this.buildView(opt));
      this.podiumBase(v); this.studioWalk(v);
      return v;
    }
    /* view i (0 top, 1 bottom) shows another option; picking the one the other view shows swaps them. The slide is told
       (onSlot), so it can put this beat's labels, captions, people and event on the new drawing */
    setSlot(i, opt) {
      if (!this.views[i] || this.views[i].opt === opt) return;
      const j = this.views.findIndex((v) => v.opt === opt);
      if (j >= 0) [this.views[i], this.views[j]] = [this.views[j], this.views[i]];
      else this.views[i] = this.viewOf(opt);
      this.views.forEach((v) => { const sel = v.el.querySelector(".axo-pick select"); if (sel) sel.value = v.opt; });
      this.colAt = NaN;                         // the drawing coming in takes the colours on now
      this.layout();
      if (this.onSlot) this.onSlot();
      this.wake();
    }
    shownOpts() { return this.views.map((v) => v.opt); }

    /* ---------- state: each beat sets what stands up; the frame moves toward it ---------- */
    set(target) { Object.assign(this.t, target); this.wake(); }
    setTexts(labels, captions) {
      this.texts = { labels: labels || [[], []], captions: captions || ["", ""] };
      this.views.forEach((v, i) => {
        v.el.querySelector(".axo-cap").innerHTML = this.texts.captions[i] || "";
        v.el.querySelector(".axo-lbls").innerHTML = (this.texts.labels[i] || []).map((l) => `<div class="axo-lbl">${l.text}</div>`).join("");
      });
      this.wake();
    }
    setLegend(html) { this.views.forEach((v) => (v.el.querySelector(".axo-solo-lgd").innerHTML = html || "")); }
    /* one option fills the screen (i), or both stacked (null) */
    setSolo(i) {
      this.solo = i === undefined ? null : i;
      this.host.classList.toggle("solo", this.solo !== null);
      this.layout();
    }
    /* one option in the slide's own frame (the day: one at a time), or both (null); ⤢ still takes it full screen */
    setOne(i) { this.one = i === undefined ? null : i; this.layout(); }
    layout() {
      const shown = this.solo !== null ? this.solo : this.one;
      Object.values(this.cache).forEach((v) => (v.el.style.display = this.views.includes(v) ? "" : "none"));   // a drawing not on view keeps its overlay hidden
      this.views.forEach((v, j) => {
        v.el.classList.toggle("off", shown !== null && j !== shown);
        v.el.classList.toggle("top", j === 0); v.el.classList.toggle("bottom", j === 1 && shown === null);   // (the overlays' order in the page is the order they were built)
        const b = v.el.querySelector(".axo-fs"); b.textContent = this.solo === j ? "✕" : "⤢"; b.title = this.solo === j ? (this.one !== null ? "Back (Esc)" : "Back to both options (Esc)") : "Full screen";
      });
      this.resize();
    }

    /* ---------- a day on view i: people take their places for a scenario (null: everyone leaves) ---------- */
    // people: the option's headcount (Mitigata's occupancy chart: 299 and 305, Sathwick 13.10); the scenarios are written for
    // 315, so each hour's count scales to it, the event's own crowd staying the brief's 50 / 100 / 200 and the floor taking the rest
    setDay(i, name, people) {
      const v = this.views[i], z = D.zones[v.opt], P = v.p, targets = [], tk = floorTaken();
      let sc = name ? SCEN[name] : null;
      if (sc && people) {
        const k = people / 315, keys = Object.keys(sc).filter((t) => t !== "event"), flo = keys.reduce((a, t) => a + sc[t], 0);
        const evN = sc.event ? sc.event[1] : 0, want = Math.max(0, Math.round((flo + evN) * k) - evN);   // the hour's whole count scales
        const raw = keys.map((t) => (sc[t] * want) / (flo || 1)), out = raw.map(Math.floor);
        let left = want - out.reduce((a, x) => a + x, 0);
        raw.map((x, j) => [x - Math.floor(x), j]).sort((a, b) => b[0] - a[0]).forEach(([, j]) => { if (left > 0) { out[j]++; left--; } });
        sc = Object.assign({}, sc); keys.forEach((t, j) => (sc[t] = out[j]));
      }
      let evPolys = null, podPoly = null;
      if (sc) {
        // the event first, so its crowd has the room; a ring kept clear in front of the stage
        if (sc.event) {
          const [lvl, n] = sc.event, ev = this.eventOf(v.opt, lvl);
          if (ev) {
            evPolys = ev.polys || [ev.poly];
            const pd = lvl === PODIUM ? this.podium(v, lvl, evPolys) : null, st = pd || ev.stage;
            const pp = pd && pd[4], off = st ? (x, y) => (pp && inPoly(x, y, pp)) || (x - st[0]) ** 2 + (y - st[1]) ** 2 < (pd ? (pp ? 1800 : 2800) : 2200) ** 2 : null;
            if (pp) podPoly = pp;
            // the town hall: the speaker on the stage with the mic, facing the room; everyone turned to him (Ritika)
            if (pd) { targets.push([pd[0], pd[1], 2]); take(tk, pd[0], pd[1]); }   // he faces the camera, so he reads; the room turns to him
            groups(evPolys, pd ? n - 1 : n, 97 + n, tk, off).forEach((p) => targets.push(pd ? [p[0], p[1], 1, pd[0], pd[1]] : [p[0], p[1], 1]));   // standing about in small groups, never in rows (Ritika)
          }
        }
        const outside = evPolys ? (x, y) => evPolys.some((p) => inPoly(x, y, p)) || (podPoly && inPoly(x, y, podPoly)) : null;   // no grey figure inside the event's area or on the podium (Ritika)
        let seed = 11;
        for (const t in sc) {
          if (t === "event") continue;
          scatter(z.zones.filter((zz) => zz.type === t).map((zz) => zz.poly), sc[t], seed++ * 31, t === "soc" ? 1300 : 1050, tk, outside).forEach((p) => targets.push([p[0], p[1], 0]));
        }
      }
      // everyone continues from where they stand; the rest walk out to the lobby and fade
      for (let k = 0; k < NP; k++) {
        P.from[k * 2] = P.now[k * 2]; P.from[k * 2 + 1] = P.now[k * 2 + 1];
        const tg = targets[k];
        if (tg) { P.to[k * 2] = tg[0]; P.to[k * 2 + 1] = tg[1]; P.green[k] = tg[2]; P.visTo[k] = 1; }
        else { P.to[k * 2] = v.lobby[0]; P.to[k * 2 + 1] = v.lobby[1]; P.visTo[k] = 0; }
        P.look[k * 2] = tg && tg[3] !== undefined ? tg[3] : NaN; P.look[k * 2 + 1] = tg && tg[4] !== undefined ? tg[4] : NaN;
        P.lift[k] = tg && tg[2] === 2 ? (podPoly ? PODIUM_H : 0.3) : 0;
      }
      P.t = 0; P.t0 = performance.now(); v.headcount = targets.length;
      this.wake();
      return targets.length;
    }
    /* event areas a slide hands in, { opt: { "50": poly, ... } }: they replace the drawings' own on this axo */
    setEvents(map) { this.evOver = map; Object.values(this.cache).forEach((v) => { v.ev = {}; v.evS = {}; }); }
    eventOf(opt, lvl) {
      const o = this.evOver && this.evOver[opt] && this.evOver[opt][lvl];
      return o ? { poly: o } : (D.zones[opt].events && D.zones[opt].events[lvl]) || null;
    }
    /* the event's volume on view i rises (level "50" | "100" | "200") or sinks (null) */
    showEvent(i, lvl) {
      const v = this.views[i], ev = lvl && this.eventOf(v.opt, lvl);
      if (ev && !v.ev[lvl]) {
        v.ev[lvl] = v.vol(ev.polys || [ev.poly], 3.2, 0x04db7f, 0x03a862, 0.13); v.evS[lvl] = 0;
        if (lvl === PODIUM) v.ev[lvl].add(this.podiumMesh(this.podium(v, lvl, ev.polys || [ev.poly])));
      }
      v.evOn = ev ? lvl : null;
      this.wake();
    }
    /* the town hall's podium: on the edge of its area nearest the SOC, 1.6 m in; [x, y, look-x, look-y] (plan mm) */
    podium(v, lvl, polys) {
      if (v.podAt[lvl]) return v.podAt[lvl];
      const pp = this.podOver && this.podOver[v.opt];
      if (pp) {   // Ritika's podium (450 mm): the speaker at its middle, the lectern toward the room's centre
        const big = polys.slice().sort((a, b) => area(b) - area(a))[0], c = P2.centroid(big), pc = P2.centroid(pp), b = bboxP(pp);
        let sp = null, sd = 1e18;
        for (let x = b[0]; x <= b[2]; x += 150) for (let y = b[1]; y <= b[3]; y += 150) {
          if (!inPoly(x, y, pp)) continue;
          if ((x - pc[0]) ** 2 + (y - pc[1]) ** 2 > 1500 * 1500) continue;            // near the podium's middle...
          const d = (x - c[0]) ** 2 + (y - c[1]) ** 2; if (d < sd) { sd = d; sp = [x, y]; }   // ...on its side toward the room
        }
        return (v.podAt[lvl] = [sp[0], sp[1], c[0], c[1], pp]);
      }
      const s = v.socAt, poly = polys.slice().sort((a, b) => area(b) - area(a))[0], c = P2.centroid(poly);
      let best = null, bd = 1e18;
      poly.forEach((q, i) => {
        const r = poly[(i + 1) % poly.length], dx = r[0] - q[0], dy = r[1] - q[1], L = dx * dx + dy * dy || 1;
        const t = Math.max(0, Math.min(1, ((s[0] - q[0]) * dx + (s[1] - q[1]) * dy) / L)), px = q[0] + t * dx, py = q[1] + t * dy, d = (px - s[0]) ** 2 + (py - s[1]) ** 2;
        if (d < bd) { bd = d; best = [px, py]; }
      });
      const ux = c[0] - best[0], uy = c[1] - best[1], ul = Math.hypot(ux, uy) || 1;
      let p = [best[0] + (ux / ul) * 1600, best[1] + (uy / ul) * 1600];
      for (let k = 0; k < 20 && !inPoly(p[0], p[1], poly); k++) p = [p[0] + (ux / ul) * 400, p[1] + (uy / ul) * 400];
      return (v.podAt[lvl] = [p[0], p[1], c[0], c[1]]);
    }
    // a low stage, a lectern toward the room and the speaker's mic (Ritika)
    podiumMesh(pd) {
      const out = new T.Group(), g = new T.Group(), W = new T.MeshLambertMaterial({ color: 0xffffff }), K = new T.MeshBasicMaterial({ color: INK });
      const H = pd[4] ? PODIUM_H : 0.3;
      const box = (w, h, d, x, y, z, m) => { const b = new T.Mesh(new T.BoxGeometry(w, h, d), m || W); b.position.set(x, y, z); g.add(b);
        const e = new T.LineSegments(new T.EdgesGeometry(b.geometry), new T.LineBasicMaterial({ color: INK })); e.position.copy(b.position); g.add(e); return b; };
      if (!pd[4]) box(3.0, H, 2.0, 0, H / 2, 0);                                         // no outline handed in: a small stage (Ritika's podium stands throughout)
      box(0.6, 1.1, 0.45, 0, H + 0.55, 0.75);                                            // the lectern, between him and the room
      const st = new T.Mesh(new T.CylinderGeometry(0.012, 0.012, 0.45, 6), K); st.position.set(0.18, H + 1.1 + 0.2, 0.62); st.rotation.x = -0.5; g.add(st);
      const hd = new T.Mesh(new T.SphereGeometry(0.05, 10, 8), K); hd.position.set(0.18, H + 1.42, 0.5); g.add(hd);   // the mic, at his mouth
      // the speaker's spot, turned to the room (the group's +z toward the room)
      g.position.set(mx(pd[0]), 0, mz(pd[1])); g.rotation.y = Math.atan2(mx(pd[2]) - mx(pd[0]), mz(pd[3]) - mz(pd[1]));
      out.add(g);
      return out;
    }
    // the visitor's walk on from reception to the podcast studio, per option (drawing mm): drawn after the boardroom walk
    setStudioWalk(map) { this.studioMap = map; Object.values(this.cache).forEach((v) => this.studioWalk(v)); this.wake(); }
    studioWalk(v) {
      if (v.walk2) { v.scene.remove(v.walk2.line, v.walk2.end); v.walk2 = null; }
      const pts = this.studioMap && this.studioMap[v.opt]; if (pts && pts.length > 1) v.walk2 = v.walkOf(pts, true);
    }
    // Ritika's podium outline per option, 450 mm high, white with a bold edge: on the floor throughout, every beat (13.10)
    setPodium(map) { this.podOver = map; Object.values(this.cache).forEach((v) => this.podiumBase(v)); this.wake(); }
    podiumBase(v) {
      v.podAt = {}; v.ev = {}; v.evS = {};
      if (v.podBase) { v.scene.remove(v.podBase); v.podBase = null; }
      const pp = this.podOver && this.podOver[v.opt]; if (!pp) return;
      const g = (v.podBase = new T.Group()), m = new T.Mesh(new T.ExtrudeGeometry(shapeOf(pp), { depth: PODIUM_H, bevelEnabled: false }), behind(new T.MeshLambertMaterial({ color: 0xffffff }), 1));
      m.rotation.x = -Math.PI / 2; g.add(m);
      const e = new T.LineSegments(new T.EdgesGeometry(m.geometry, 25), new T.LineBasicMaterial({ color: INK })); e.rotation.copy(m.rotation); g.add(e);
      v.scene.add(g);
    }
    drawPeople(v, t) {
      const P = v.p, d = this.dummy, F = FIGS.length;
      const th = this.s ? this.s.theta : HOME.theta;                     // (built before the camera state exists)
      d.rotation.set(0, th, 0); v.pTheta = th;                           // every figure faces the camera
      for (let k = 0; k < NP; k++) {
        let e = Math.min(1, Math.max(0, t * 1.6 - P.delay[k]));
        e = e < 0.5 ? 2 * e * e : 1 - Math.pow(-2 * e + 2, 2) / 2;
        const x = P.from[k * 2] + (P.to[k * 2] - P.from[k * 2]) * e, y = P.from[k * 2 + 1] + (P.to[k * 2 + 1] - P.from[k * 2 + 1]) * e;
        P.now[k * 2] = x; P.now[k * 2 + 1] = y;
        const vis = P.visTo[k] ? Math.max(P.vis[k], e) : (1 - e) * P.vis[k], s = Math.max(0.0001, vis);
        const jt = 0.94 + ((k * 7919) % 13) / 100, fl = (k * 2654435761 >>> 0) % 2 ? -1 : 1;   // each figure its own size (±6 %) and side: no ranks
        const lx = P.look[k * 2], ly = P.look[k * 2 + 1];
        let ry = th;
        if (!isNaN(lx)) { let da = Math.atan2(mx(lx) - mx(x), mz(ly) - mz(y)) - th; da = Math.atan2(Math.sin(da), Math.cos(da)); ry = th + Math.max(-0.8, Math.min(0.8, da)); }
        d.rotation.set(0, ry, 0);   // facing the camera, or turned toward the speaker, at most 45° so each still reads (Ritika)
        d.position.set(mx(x), 0.02 + P.lift[k] * e, mz(y)); d.scale.set(s * jt * fl, s * jt, s * jt); d.updateMatrix();
        const m = v.pFig[k % F], j = Math.floor(k / F);
        m.setMatrixAt(j, d.matrix); m.setColorAt(j, this.col.setHex(P.green[k] === 2 && P.visTo[k] ? SPEAKER : P.green[k] && P.visTo[k] ? GUEST : PERSON));   // the speaker in black
      }
      if (t >= 1) for (let k = 0; k < NP; k++) P.vis[k] = P.visTo[k];
      v.pFig.forEach((m) => { m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true; });
    }
    /* where the visible drawing is looking, for a hand-over to the twin (app.js: the site from the axo) */
    pose() {
      const i = this.solo !== null ? this.solo : this.one !== null ? this.one : 0, R = this.rects && this.rects[i], h = this.host.getBoundingClientRect();
      return { theta: this.s.theta, phi: this.s.phi, zoom: this.s.zoom, center: this.fr ? this.fr.center.toArray() : null, halfH: this.fr ? this.fr.hh : 30,
        rect: R ? [h.left + R[0], h.top + R[1], R[2], R[3]] : [h.left, h.top, h.width, h.height] };
    }
    intro() { Object.assign(this.s, TOP, { soc: 0, guest: 0, route: 0, meet: 0, mono: 0 }); this.wake(); }
    home() { Object.assign(this.t, this.homeT); this.wake(); }
    /* the beat's own view (angles, zoom, focus): Reset returns to it; apply moves there now */
    setHome(view, apply) { this.homeT = Object.assign({}, HOME, { fw: 0, px: 0, py: 0 }, view); if (apply) this.home(); }
    setColours(on) { this.set({ colours: on ? 1 : 0 }); }
    setFurniture(on) { this.set({ furn: on ? 1 : 0 }); }
    start() { this.running = true; this.resize(); this.wake(); }
    stop() { this.running = false; }
    wake() { if (!this.raf && this.running) this.raf = requestAnimationFrame(() => this.frame()); }

    resize() {
      const r = this.host.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      this.W = r.width; this.H = r.height;
      this.renderer.setSize(r.width, r.height, false);
      this.renderer.domElement.style.width = r.width + "px"; this.renderer.domElement.style.height = r.height + "px";
      const gap = 18, h = (r.height - gap) / 2, shown = this.solo !== null ? this.solo : this.one;
      this.rects = shown !== null ? this.views.map((v, i) => (i === shown ? [0, 0, r.width, r.height] : null)) : [[0, 0, r.width, h], [0, h + gap, r.width, h]];
      this.views.forEach((v, i) => { const R = this.rects[i]; if (R) Object.assign(v.el.style, { left: R[0] + "px", top: R[1] + "px", width: R[2] + "px", height: R[3] + "px" }); });
      this.wake();
    }

    bind() {
      // drag pans, as on the floor plans; Shift+drag or a right-drag turns the model (Ritika, 14.10)
      const c = this.renderer.domElement; let drag = null;
      c.addEventListener("contextmenu", (e) => e.preventDefault());
      c.addEventListener("pointerdown", (e) => {
        const r = (this.rects || []).find(Boolean);
        drag = { x: e.clientX, y: e.clientY, th: this.t.theta, ph: this.t.phi, px: this.t.px, py: this.t.py, turn: e.shiftKey || e.button === 2,
          k: this.fr && r ? (this.fr.hh * 2) / r[3] : 0 };   // view units per screen pixel
        c.setPointerCapture(e.pointerId); c.classList.add("dragging");
      });
      c.addEventListener("pointermove", (e) => {
        if (!drag) return;
        const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
        if (drag.turn) {
          this.t.theta = drag.th - dx * 0.006;
          this.t.phi = Math.min(1.35, Math.max(0.04, drag.ph - dy * 0.004));
        } else { this.t.px = drag.px + dx * drag.k; this.t.py = drag.py - dy * drag.k; this.s.px = this.t.px; this.s.py = this.t.py; }   // the drawing stays under the cursor
        this.wake();
      });
      c.addEventListener("pointerup", () => { drag = null; c.classList.remove("dragging"); });
      c.addEventListener("dblclick", () => this.home());
      c.addEventListener("wheel", (e) => { e.preventDefault(); this.t.zoom = Math.min(4, Math.max(0.8, this.t.zoom * Math.exp(-e.deltaY * 0.0012))); this.wake(); }, { passive: false });
    }

    /* ---------- frame ---------- */
    frame() {
      this.raf = null;
      if (!this.running || !this.rects) return;
      // the page's white between the stages, then each view clears to its grey stage as it renders (scissored)
      const R0 = this.renderer; R0.setScissorTest(false); R0.setClearColor(0xffffff, 1); R0.clear(); R0.setScissorTest(true); R0.setClearColor(STAGE, 1);
      const dt = Math.min(0.05, this.clock.getDelta()), k = 1 - Math.exp(-dt * 3.4);
      let moving = false;
      for (const key in this.t) { const dd = this.t[key] - this.s[key]; if (Math.abs(dd) > 1e-4) { this.s[key] += dd * k; moving = true; } else this.s[key] = this.t[key]; }
      const S = this.s, cam = this.camera, tgt = new T.Vector3(mx(40300), 0, mz(17200));
      const sp = Math.sin(S.phi), dir = new T.Vector3(sp * Math.sin(S.theta), Math.cos(S.phi), sp * Math.cos(S.theta));
      cam.position.copy(tgt).addScaledVector(dir, 300); cam.up.set(0, 1, 0); cam.lookAt(tgt); cam.updateMatrixWorld();
      // fit the floor (and what stands on it) into one view; both views use the same frame
      const inv = cam.matrixWorldInverse, b = [1e9, 1e9, -1e9, -1e9], q = new T.Vector3();
      FIT.forEach(([x, y]) => [0, 3.4].forEach((h) => { q.set(mx(x), h, mz(y)).applyMatrix4(inv); b[0] = Math.min(b[0], q.x); b[1] = Math.min(b[1], q.y); b[2] = Math.max(b[2], q.x); b[3] = Math.max(b[3], q.y); }));
      const [, , vw, vh] = this.rects.find(Boolean), ar = vw / vh, pad = 1.08;
      let hw = ((b[2] - b[0]) / 2) * pad, hh = ((b[3] - b[1]) / 2) * pad;
      if (hw / hh > ar) hh = hw / ar; else hw = hh * ar;
      hw /= S.zoom; hh /= S.zoom;
      let cx = (b[0] + b[2]) / 2 - S.px, cy = (b[1] + b[3]) / 2 - S.py;
      if (S.fw > 1e-3) { q.set(mx(S.fx), 0, mz(S.fy)).applyMatrix4(inv); cx += (q.x - cx) * S.fw; cy += (q.y - cy) * S.fw; }   // toward a space
      // the floor: its zone colours, grey beyond the highlight (mono, Ritika), or white (colours 0)
      const ck = S.colours + 7 * S.mono, ct = this.t.colours + 7 * this.t.mono;
      if (Math.abs(ck - this.colAt) > 1e-4 || (ck !== this.colAt && ck === ct)) {
        const W = new T.Color(0xffffff), G = new T.Color(0xe3e3e3), c2 = new T.Color();
        this.views.forEach((vv) => vv.fills.forEach(([m, c]) => m.color.copy(W).lerp(c2.copy(c).lerp(G, S.mono), S.colours)));
        this.colAt = ck;
      }
      Object.assign(cam, { left: cx - hw, right: cx + hw, top: cy + hh, bottom: cy - hh, near: 150, far: 450 }); cam.updateProjectionMatrix();
      this.fr = { hh, center: cam.localToWorld(new T.Vector3(cx, cy, -300)) };   // the world point at the middle of the view
      const now = performance.now();
      this.views.forEach((v, i) => {
        if (!this.rects[i]) return;
        v.soc.visible = S.soc > 0.01; v.soc.scale.y = Math.max(0.001, S.soc);
        v.guest.visible = S.guest > 0.01; v.guest.scale.y = Math.max(0.001, S.guest);
        v.studio.visible = S.guest > 0.01; v.studio.scale.y = Math.max(0.001, S.guest);
        v.meet.visible = S.meet > 0.01; v.meet.scale.y = Math.max(0.001, S.meet);
        if (v.route) { v.route.geometry.setDrawRange(0, Math.floor(v.routeN * S.route / 6) * 6); v.routeEnd.visible = S.route > 0.98; }
        if (v.walk2) {   // the studio leg draws once the boardroom walk is nearly in
          const k = Math.max(0, Math.min(1, (S.route - 0.55) / 0.45));
          v.walk2.line.geometry.setDrawRange(0, Math.floor(v.walk2.N * k / 6) * 6); v.walk2.end.visible = k > 0.98;
        }
        if (v.p.t >= 1 && Math.abs(S.theta - v.pTheta) > 1e-4) this.drawPeople(v, 1);   // the figures turn with the drawing
        v.furn.material.opacity = 0.9 * S.furn; v.furn.visible = S.furn > 0.01;
        // the day: people walk to their places; an event's volume rises or sinks
        if (v.p.t < 1) { v.p.t = Math.min(1, (now - v.p.t0) / 2600); this.drawPeople(v, v.p.t); moving = true; }
        for (const lvl in v.ev) {
          const to = v.evOn === lvl ? 1 : 0, dd = to - v.evS[lvl];
          if (Math.abs(dd) > 1e-3) { v.evS[lvl] += dd * k; moving = true; } else v.evS[lvl] = to;
          v.ev[lvl].visible = v.evS[lvl] > 0.01; v.ev[lvl].scale.y = Math.max(0.001, v.evS[lvl]);
        }
        const [x, y, w, h] = this.rects[i], by = this.H - y - h;
        this.renderer.setViewport(x, by, w, h); this.renderer.setScissor(x, by, w, h);
        this.renderer.render(v.scene, cam);
        this.drawOver(v, i);
      });
      if (moving) this.wake();
    }
    /* data mm (+ height m) -> px inside view i */
    toView(i, p) {
      const [, , w, h] = this.rects[i], q = new T.Vector3(mx(p[0]), p[2] || 0, mz(p[1])).project(this.camera);
      return [((q.x + 1) / 2) * w, ((1 - q.y) / 2) * h];
    }
    drawOver(v, i) {
      const [, , w, h] = this.rects[i], S = this.s;
      // north: the drawing's +x, as it falls on screen now
      const o = this.toView(i, [40000, 17000, 0]), n = this.toView(i, [41000, 17000, 0]), a = Math.atan2(n[1] - o[1], n[0] - o[0]);
      v.el.querySelector(".axo-north i").style.transform = `rotate(${a}rad)`;
      v.el.querySelector(".axo-north b").style.transform = `translate(${Math.cos(a) * 27}px, ${Math.sin(a) * 27}px)`;
      const bar = i === 0 && document.querySelector("#axo-bar .ctl-north line");   // the slide's one toolbar, if it has one
      if (bar) { bar.setAttribute("x2", (13 + 9 * Math.cos(a)).toFixed(2)); bar.setAttribute("y2", (13 + 9 * Math.sin(a)).toFixed(2)); }
      // labels beside what they name, with a leader line; never on the volume
      const svg = v.el.querySelector(".axo-lines"), lbls = v.el.querySelectorAll(".axo-lbl"), list = this.texts.labels[i] || [];
      svg.setAttribute("viewBox", `0 0 ${w} ${h}`); let lines = "";
      list.forEach((l, j) => {
        const el = lbls[j]; if (!el) return;
        const at = l.at === "soc" ? [v.socAt[0], v.socAt[1], v.socAt[2] * S.soc] : l.at === "guest" ? [v.guestAt[0], v.guestAt[1], v.guestAt[2] * S.guest] : l.at === "studio" ? [v.studioAt[0], v.studioAt[1], v.studioAt[2] * S.guest] : l.at === "arrive" ? [v.arriveAt[0], v.arriveAt[1], v.arriveAt[2] * S.guest] : l.at === "route" ? v.routeAt : l.at;
        const shown = (l.at === "soc" ? S.soc : l.at === "guest" || l.at === "studio" || l.at === "arrive" ? S.guest : l.at === "route" ? S.route : 1) > 0.6;
        const p = this.toView(i, at), lw = el.offsetWidth, lh = el.offsetHeight;
        const dx = l.dx === undefined ? -70 : l.dx, dy = l.dy === undefined ? -64 : l.dy;
        const lx = Math.max(4, Math.min(w - lw - 4, p[0] + dx - (dx < 0 ? lw : 0))), ly = Math.max(30, Math.min(h - lh - 30, p[1] + dy - lh / 2));
        el.style.left = lx + "px"; el.style.top = ly + "px"; el.style.opacity = shown ? 1 : 0;
        const ex = dx < 0 ? lx + lw : lx, ey = ly + lh / 2;
        if (shown) lines += `<line x1="${ex}" y1="${ey}" x2="${p[0]}" y2="${p[1]}"/><circle cx="${p[0]}" cy="${p[1]}" r="3"/>`;
      });
      svg.innerHTML = lines;
    }
  }
  window.Axo = Axo;
  Axo.MEET_C = MEET_C;   // the meeting rooms' shades by size, for the slide's legend
})();
