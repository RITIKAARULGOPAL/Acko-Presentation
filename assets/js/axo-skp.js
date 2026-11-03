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

  // ---------- the axo debug page's fit (tools/acko/axo_debug.html: walkPlan, oriented, loungeGroups, fixPlace, loungeSeats,
  // terraceFurniture, partition, door and its furniture trims), as the page has them, here on the slide's model ----------
  function fitting({ T, D, P: PD, X, Z, CX, CY, shift }) {
    const SOFA = { SEAT: 0.42, BACK: 0.8, BACK_D: 0.22, ARM: 0.6, ARM_W: 0.16 }, DESK_SET = /^rhrt(#|$)/, ARMCHAIRS = ["ferfer", "CH_CA_LO_01", "fvtb"];
    const SOFA_BLOCKS = ["rgr"], ARMCHAIR_BLOCKS = ["fvtb"], TABLE_BLOCKS = ["FGFGDG"], LOUNGE_CHAIR = /^A\$C3BB14C(#|$)/;
    const TURN_CHAIR = "chair-flat9", STRETCH = 1.5, CAFE_CHAIR = /^cafe chair/i, CABIN_CHAIR = "*U738", TASK_CHAIR = /^\*U730(#|$)/, FURN_L = /FUR|CHAIR|LOOSE/i;
    // the floor plan: data/plan-base.js walked as the page walks it (an insert on a frozen layer, anything on an off one, left
    // out), plan mm shifted onto the model: each item's points, layer, kind (1 a fill), block path and box; a grid of the boxes.
    // Only the items the fit reads (a furniture layer's, or in one of the blocks it looks for): the rest it never asks about
    const PB = window.PLAN_BASE, LY = PB.layers, [ox, oy] = PB.origin, [sx, sy] = shift;
    const NEED = new Set([...SOFA_BLOCKS, ...ARMCHAIR_BLOCKS, ...TABLE_BLOCKS, ...ARMCHAIRS]), furnL = new Map();
    const needed = (st, tail) => NEED.has(tail) || tail.endsWith(CABIN_CHAIR) || tail.endsWith(TURN_CHAIR) || (furnL.get(st) ?? furnL.set(st, FURN_L.test(st)).get(st));
    const pts = [], start = [], cnt = [], lay = [], kind = [], path = [], names = [], nameIx = new Map(), paths = [], pathIx = new Map();
    const id = (map, list, s) => { let i = map.get(s); if (i === undefined) { i = list.length; map.set(s, i); list.push(s); } return i; };
    for (const blk of PB.blocks) {
      const Dd = blk.data, defs = Dd.defs, lay_ = (l, ctx) => (l === "" || l === "0" ? ctx : l);
      const walk = (di, M4, ctx, pth, tail) => {
        const d = defs[di], k = Math.pow(10, -d.q), [a, b, c, e, f, g] = M4; let pid = -1;
        for (const [l, , , , kd, items] of d.runs) {
          const st = lay_(l, ctx);
          if (kd === "i") {
            if (LY[st] && LY[st].frozen) continue;
            for (const [ci, ca, cb, cc, cd, ce, cf] of items) { const nm = defs[ci].name;
              walk(ci, [a * ca + c * cb, b * ca + e * cb, a * cc + c * cd, b * cc + e * cd, a * ce + c * cf + f, b * ce + e * cf + g], st, nm ? (pth ? pth + " > " + nm : nm) : pth, nm || tail); }
            continue;
          }
          if (kd === "t" || (LY[st] && (LY[st].off || LY[st].frozen)) || !needed(st, tail)) continue;
          if (pid < 0) pid = id(pathIx, paths, pth || "(the plan itself)");
          const li = id(nameIx, names, st);
          for (const item of items) for (const arr of kd === "f" ? item : [item]) {
            start.push(pts.length / 2); let x = arr[0], y = arr[1];
            for (let i = 0; i < arr.length; i += 2) { if (i) { x += arr[i]; y += arr[i + 1]; } const XX = x * k, YY = y * k; pts.push(a * XX + c * YY + f - ox + sx, oy - (b * XX + e * YY + g) + sy); }
            cnt.push(arr.length / 2); lay.push(li); kind.push(kd === "f" ? 1 : 0); path.push(pid);
          }
        }
      };
      walk(Dd.root, Dd.place.m, lay_(Dd.place.spec[0], "0"), "", "(the plan itself)");
    }
    const N = start.length, CELL = 2000, box = new Float64Array(N * 4), grid = new Map();
    for (let i = 0; i < N; i++) {
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity; const s = start[i] * 2;
      for (let j = 0; j < cnt[i]; j++) { const x = pts[s + 2 * j], y = pts[s + 2 * j + 1]; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
      box.set([x0, y0, x1, y1], i * 4);
      for (let cx = Math.floor(x0 / CELL); cx <= Math.floor(x1 / CELL); cx++) for (let cy = Math.floor(y0 / CELL); cy <= Math.floor(y1 / CELL); cy++) {
        const key = cx * 100000 + cy, cl = grid.get(key); if (cl) cl.push(i); else grid.set(key, [i]);
      }
    }
    const tails = paths.map((p) => p.split(" > ").pop());
    const ptsOf = (i) => { const s = start[i] * 2, out = []; for (let j = 0; j < cnt[i]; j++) out.push([pts[s + 2 * j], pts[s + 2 * j + 1]]); return out; };
    const near = (x, y, r, fn) => { for (let cx = Math.floor((x - r) / CELL); cx <= Math.floor((x + r) / CELL); cx++) for (let cy = Math.floor((y - r) / CELL); cy <= Math.floor((y + r) / CELL); cy++) for (const i of grid.get(cx * 100000 + cy) || []) fn(i); };
    const mid = (i) => [(box[4 * i] + box[4 * i + 2]) / 2, (box[4 * i + 1] + box[4 * i + 3]) / 2];
    const bytes_ = (b64) => { const s = atob(b64), a = new Uint8Array(s.length); for (let k = 0; k < s.length; k++) a[k] = s.charCodeAt(k); return a.buffer; };
    const ubox = new Map();                                              // (a component's local box, its fine parts')
    for (const p of D.parts) if (p.u >= 0 && p.lv !== 2) { const b = ubox.get(p.u) || [[1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]];
      for (let k = 0; k < 3; k++) { b[0][k] = Math.min(b[0][k], p.lo[k]); b[1][k] = Math.max(b[1][k], p.hi[k]); } ubox.set(p.u, b); }
    const boxOf = (u) => ubox.get(u) || [[1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]];
    // a set of triangles (positions, indices) in pieces joined where they share a corner: find(t) gives its piece
    const pieces_ = (pos, ix) => {
      const n = ix.length / 3, up = new Int32Array(n).fill(-1), at = new Map();
      const find = (a) => { while (up[a] >= 0 && up[up[a]] >= 0) { up[a] = up[up[a]]; a = up[a]; } return up[a] >= 0 ? up[a] : a; };
      // (a corner's key: its place to 5 mm, as one number; the model is well within ±200 m)
      for (let t = 0; t < n; t++) for (let j = 0; j < 3; j++) { const v = ix[3 * t + j] * 3, key = ((Math.round(pos[v] * 200) + 40000) * 80000 + Math.round(pos[v + 1] * 200) + 40000) * 80000 + Math.round(pos[v + 2] * 200) + 40000, o = at.get(key);
        if (o === undefined) at.set(key, t); else { const r1 = find(o), r2 = find(t); if (r1 !== r2) up[r2] = r1; } }
      return { n, find };
    };
    const keepOnly = (g, ix, n, drop) => { const keep = []; for (let t = 0; t < n; t++) if (!drop(t)) keep.push(ix[3 * t], ix[3 * t + 1], ix[3 * t + 2]); if (keep.length < ix.length) g.setIndex(new T.BufferAttribute(new ix.constructor(keep), 1)); };

    // a ring's smallest rectangle round it (plan mm): its centre c, its long direction u, its length L and width W, and how much
    // of it the ring fills
    function oriented(ring) {
      const p = ring.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
      const lo = [], hi = []; for (const q of p) { while (lo.length > 1 && cr(lo.at(-2), lo.at(-1), q) <= 0) lo.pop(); lo.push(q); }
      for (const q of p.reverse()) { while (hi.length > 1 && cr(hi.at(-2), hi.at(-1), q) <= 0) hi.pop(); hi.push(q); }
      const hull = lo.slice(0, -1).concat(hi.slice(0, -1)); if (hull.length < 3) return null;
      let best = null;
      for (let i = 0; i < hull.length; i++) {
        const a = hull[i], b = hull[(i + 1) % hull.length], l = Math.hypot(b[0] - a[0], b[1] - a[1]); if (l < 1) continue;
        const u = [(b[0] - a[0]) / l, (b[1] - a[1]) / l], v = [-u[1], u[0]]; let s0 = 1e18, s1 = -1e18, t0 = 1e18, t1 = -1e18;
        for (const q of hull) { const s = q[0] * u[0] + q[1] * u[1], t = q[0] * v[0] + q[1] * v[1]; s0 = Math.min(s0, s); s1 = Math.max(s1, s); t0 = Math.min(t0, t); t1 = Math.max(t1, t); }
        const A = (s1 - s0) * (t1 - t0);
        if (!best || A < best.A) { const sm = (s0 + s1) / 2, tm = (t0 + t1) / 2; best = { A, s: s1 - s0, t: t1 - t0, u, v, c: [u[0] * sm + v[0] * tm, u[1] * sm + v[1] * tm] }; }
      }
      if (!best) return null;
      const long = best.s >= best.t, area = Math.abs(ring.reduce((s, q, i) => { const n = ring[(i + 1) % ring.length]; return s + q[0] * n[1] - n[0] * q[1]; }, 0)) / 2;
      return { c: best.c, u: long ? best.u : best.v, L: long ? best.s : best.t, W: long ? best.t : best.s, fill: area / best.A };
    }
    const hull2 = (pp0) => { const pp = pp0.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]), lo = [], hi = [];
      for (const q of pp) { while (lo.length > 1 && cr(lo.at(-2), lo.at(-1), q) <= 0) lo.pop(); lo.push(q); } for (const q of pp.reverse()) { while (hi.length > 1 && cr(hi.at(-2), hi.at(-1), q) <= 0) hi.pop(); hi.push(q); }
      return lo.slice(0, -1).concat(hi.slice(0, -1)); };

    // solids drawn here, gathered per material: their triangles (non-indexed) and a colour per corner
    const bucket = () => ({ pos: [], col: [] });
    const put = (b, geo, rgb) => { const g = geo.index ? geo.toNonIndexed() : geo, a = g.getAttribute("position").array; for (let i = 0; i < a.length; i += 3) { b.pos.push(a[i], a[i + 1], a[i + 2]); b.col.push(rgb[0], rgb[1], rgb[2]); } };
    const UNIT = new T.BoxGeometry(1, 1, 1).toNonIndexed().getAttribute("position").array;   // (a box: the unit one sized, turned, moved)
    const boxAt = (b, rgb, w, h, d, x, y, z, ang) => { const c = Math.cos(ang || 0), s = Math.sin(ang || 0);
      for (let i = 0; i < UNIT.length; i += 3) { const px = UNIT[i] * w, pz = UNIT[i + 2] * d; b.pos.push(px * c + pz * s + x, UNIT[i + 1] * h + y, -px * s + pz * c + z); b.col.push(rgb[0], rgb[1], rgb[2]); } };
    const shapeOf = (rings) => { const sh = new T.Shape(rings[0].map(([x, y]) => new T.Vector2(X(x), -Z(y)))); for (const h of rings.slice(1)) sh.holes.push(new T.Path(h.map(([x, y]) => new T.Vector2(X(x), -Z(y))))); return sh; };
    const slabOf = (b, rgb, sh, y0, y1) => { const g = new T.ExtrudeGeometry(sh, { depth: y1 - y0, bevelEnabled: false }); g.rotateX(-Math.PI / 2); g.translate(0, y0, 0); put(b, g, rgb); };
    // a geometry of those triangles: its colours, its normals, UVs box-mapped in metres as the parts' (for the looks' textures)
    const solid = (pos, col) => {
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute(pos, 3)); g.setAttribute("color", new T.BufferAttribute(Uint8Array.from(col), 3, true));
      g.computeVertexNormals();
      const n = g.getAttribute("normal").array, uv = new Float32Array((pos.length / 3) * 2);
      for (let i = 0, j = 0; i < pos.length; i += 3, j += 2) { const nx = Math.abs(n[i]), ny = Math.abs(n[i + 1]), nz = Math.abs(n[i + 2]);
        if (ny >= nx && ny >= nz) { uv[j] = pos[i]; uv[j + 1] = pos[i + 2]; } else if (nx >= nz) { uv[j] = pos[i + 2]; uv[j + 1] = pos[i + 1]; } else { uv[j] = pos[i]; uv[j + 1] = pos[i + 1]; } }
      g.setAttribute("uv", new T.BufferAttribute(uv, 2)); g.computeBoundingSphere(); return g;
    };

    // ---- the pieces: walls solid; a glass partition a 12 mm pane in an aluminium frame (rails top and bottom, posts at its ends
    // and every PANEL m or less) on a straight piece, a curved or odd one its own shape in glass between rails of its shape; a
    // door a glass door, full height (a jamb each side, rails, a leaf, a pull on each face by its free edge)
    const WALL_RGB = [232, 230, 226], PANE_RGB = [95, 78, 107], FPANE_RGB = [223, 233, 239], FRAME_RGB = [74, 77, 82], PULL_RGB = [201, 201, 201];
    const GLZ = { PANE: 0.012, RAIL: 0.05, POST: 0.05 }, PANEL = { glass: 1.2, rail: 1.2, facade: 1.5 }, JAMB = 0.05, PULL = 0.6;
    function pieces(list) {
      const B = { wall: bucket(), pane: bucket(), fpane: bucket(), frame: bucket() };
      for (const [ty, h, rings] of list) {
        if (ty === "booth") continue;
        if (ty === "wall" || ty === "solid" || ty === "column") { slabOf(B.wall, WALL_RGB, shapeOf(rings), 0, h); continue; }
        const r = oriented(rings[0]), R = GLZ.RAIL, straight = r && r.fill > 0.8 && rings.length === 1;
        const [pb, prgb] = ty === "facade" ? [B.fpane, FPANE_RGB] : [B.pane, PANE_RGB];   // (the external glazing's own, paler glass)
        if (!straight) { const sh = shapeOf(rings); slabOf(pb, prgb, sh, R, h - R); slabOf(B.frame, FRAME_RGB, sh, 0, R); slabOf(B.frame, FRAME_RGB, sh, h - R, h); continue; }
        const L = r.L / 1000, W = r.W / 1000, x = X(r.c[0]), z = Z(r.c[1]), ang = -Math.atan2(r.u[1], r.u[0]), d = Math.min(W, 0.06);
        const at = (s, n = 0) => [x + Math.cos(ang) * s + Math.sin(ang) * n, z - Math.sin(ang) * s + Math.cos(ang) * n];   // (along it, across it)
        boxAt(B.frame, FRAME_RGB, L, R, d, x, R / 2, z, ang); boxAt(B.frame, FRAME_RGB, L, R, d, x, h - R / 2, z, ang);
        if (ty === "door") {
          const leafL = Math.max(0.1, L - 2 * JAMB);
          for (const s of [-L / 2 + JAMB / 2, L / 2 - JAMB / 2]) { const [px, pz] = at(s); boxAt(B.frame, FRAME_RGB, JAMB, h, d, px, h / 2, pz, ang); }
          boxAt(B.pane, PANE_RGB, leafL, h - 2 * R, GLZ.PANE, x, h / 2, z, ang);
          for (const side of [-1, 1]) { const [px, pz] = at(leafL / 2 - 0.1, side * (GLZ.PANE / 2 + 0.03)); boxAt(B.frame, PULL_RGB, 0.025, PULL, 0.025, px, 1.05, pz, ang); }
          continue;
        }
        boxAt(pb, prgb, L, h - 2 * R, GLZ.PANE, x, h / 2, z, ang);
        const n = Math.max(1, Math.ceil(L / (PANEL[ty] || 1.2)));
        for (let k = 0; k <= n; k++) { const [px, pz] = at(-L / 2 + GLZ.POST / 2 + (k / n) * (L - GLZ.POST)); boxAt(B.frame, FRAME_RGB, GLZ.POST, h, d, px, h / 2, pz, ang); }
      }
      return B;
    }

    // ---- the plan's lounge: its sofas (SOFA_BLOCKS) and armchairs (ARMCHAIR_BLOCKS), each a group of the block's lines (within
    // 400 mm), and the lounge's middle (its coffee tables, TABLE_BLOCKS); a sofa drawn on its outline, an armchair the model's
    // lounge armchair (LOUNGE_CHAIR, its ottoman left off), each facing the middle; the axo's own soft pieces on them go (fixPlace)
    function loungeGroups() {
      const by = (nms) => {
        const gs = [];
        for (let i = 0; i < N; i++) {
          if (!nms.includes(tails[path[i]])) continue;
          const b = [box[4 * i], box[4 * i + 1], box[4 * i + 2], box[4 * i + 3]];
          let g = gs.find((q) => b[0] < q.b[2] + 400 && q.b[0] < b[2] + 400 && b[1] < q.b[3] + 400 && q.b[1] < b[3] + 400);
          if (!g) gs.push(g = { b: b.slice(), pts: [] }); else g.b = [Math.min(g.b[0], b[0]), Math.min(g.b[1], b[1]), Math.max(g.b[2], b[2]), Math.max(g.b[3], b[3])];
          g.pts.push(...ptsOf(i));
        }
        return gs;
      };
      const sofas = by(SOFA_BLOCKS), arms = by(ARMCHAIR_BLOCKS), tabs = by(TABLE_BLOCKS);
      const gm = (g) => [(g.b[0] + g.b[2]) / 2, (g.b[1] + g.b[3]) / 2];
      const centre = (g) => { const t = tabs.map(gm).sort((a, b) => Math.hypot(a[0] - gm(g)[0], a[1] - gm(g)[1]) - Math.hypot(b[0] - gm(g)[0], b[1] - gm(g)[1]))[0];
        return t && Math.hypot(t[0] - gm(g)[0], t[1] - gm(g)[1]) < 5000 ? t : gm(g); };
      return { sofas: sofas.map((g) => ({ ...g, c: centre(g) })), arms: arms.map((g) => ({ ...g, c: centre(g) })) };
    }
    const armSpots = (a) => { const cl = []; for (const p of a.pts) { let g = cl.find((q) => Math.hypot(q.x / q.n - p[0], q.y / q.n - p[1]) < 900); if (!g) cl.push(g = { x: 0, y: 0, n: 0 }); g.x += p[0]; g.y += p[1]; g.n++; } return cl.map((g) => [g.x / g.n, g.y / g.n]); };

    // ---- the 28.10 plan's furniture as the axo places it, put right: none on the lounge's seats; the desks the axo set on the
    // plan's armchairs made armchairs; a café chair turned as the plan draws its chair (TURN_CHAIR) and, at the plan's desks
    // (CABIN_CHAIR), the workstation chair (TASK_CHAIR); a placement stretched STRETCH times or more split into that many copies
    function fixPlace(place, lg) {
      const midOf = (pl) => { const b = boxOf(pl.u), c = b[0].map((v, k) => (v + b[1][k]) / 2), m = pl.m;
        return [(m[0] * c[0] + m[3] * c[1] + m[6] * c[2] + m[9]) * 1000 + CX, (m[2] * c[0] + m[5] * c[1] + m[8] * c[2] + m[11]) * 1000 + CY]; };
      const armAt = []; for (const a of lg.arms) armAt.push(...armSpots(a));
      const onSeat = ([x, y]) => lg.sofas.some((g) => x > g.b[0] && x < g.b[2] && y > g.b[1] && y < g.b[3]) || armAt.some(([ax, ay]) => Math.hypot(ax - x, ay - y) < 700);
      place = place.filter((pl) => !onSeat(midOf(pl)));
      const spots = [];
      place = place.filter((pl) => {
        if (!DESK_SET.test((D.units[pl.u] && D.units[pl.u].name) || "")) return true;
        const [x, y] = midOf(pl), n = {}, at = {};
        near(x, y, 700, (i) => { const nm = tails[path[i]], [mx, my] = mid(i);
          if (nm === "(the plan itself)" || DESK_SET.test(nm) || Math.hypot(mx - x, my - y) > 700) return; n[nm] = (n[nm] || 0) + 1; (at[nm] = at[nm] || []).push([mx, my]); });
        const nm = Object.keys(n).filter((k) => ARMCHAIRS.includes(k)).sort((a, b) => n[b] - n[a])[0];
        if (!nm) return true;
        const c = at[nm].reduce((s, p) => [s[0] + p[0], s[1] + p[1]], [0, 0]).map((v) => v / at[nm].length), m = pl.m;
        spots.push({ x: c[0], y: c[1], fx: m[6], fy: m[8] }); return false;
      });
      for (const s of spots) {
        const nb = spots.filter((o) => o !== s && Math.hypot(o.x - s.x, o.y - s.y) < 3500);
        if (nb.length) { const all = [s, ...nb], mx = all.reduce((a, o) => a + o.x, 0) / all.length, my = all.reduce((a, o) => a + o.y, 0) / all.length; s.fx = mx - s.x; s.fy = my - s.y; }
      }
      lg.extra = spots;
      const task = D.units.findIndex((u) => TASK_CHAIR.test(u.name || "")), cafeU = D.units.findIndex((u) => CAFE_CHAIR.test(u.name || ""));
      let taskC = null, taskF = null;                                    // (the workstation chair's centre on the floor, its front)
      if (task >= 0) {
        const [lo, hi] = boxOf(task); taskC = new T.Vector3((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2); let bx = 0, bz = 0, n = 0;
        for (const p of D.parts) { if (p.u !== task || p.lv === 2) continue; const q = new Int16Array(bytes_(p.p));
          for (let i = 0; i < q.length; i += 3) { const y = p.lo[1] + ((q[i + 1] + 32768) / 65535) * (p.hi[1] - p.lo[1]); if (y < 0.75) continue;
            bx += p.lo[0] + ((q[i] + 32768) / 65535) * (p.hi[0] - p.lo[0]); bz += p.lo[2] + ((q[i + 2] + 32768) / 65535) * (p.hi[2] - p.lo[2]); n++; } }
        if (n) { taskF = new T.Vector3(taskC.x - bx / n, 0, taskC.z - bz / n); if (taskF.length() < 1e-3) taskF = null; else taskF.normalize(); }
      }
      const onCabin = (x, y) => { let hit = false; near(x, y, 450, (i) => { if (!hit && paths[path[i]].endsWith(CABIN_CHAIR)) { const [mx, my] = mid(i); if (Math.hypot(mx - x, my - y) < 450) hit = true; } }); return hit; };
      const facing = (x, y) => {
        const its = new Set(); near(x, y, 450, (i) => { if (!paths[path[i]].endsWith(TURN_CHAIR)) return; const [mx, my] = mid(i); if (Math.hypot(mx - x, my - y) < 450) its.add(i); });
        if (!its.size) return null;
        let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, sx_ = 0, sy_ = 0, n = 0;
        for (const i of its) { const q = ptsOf(i); for (let k = 1; k < q.length; k++) { sx_ += (q[k][0] + q[k - 1][0]) / 2; sy_ += (q[k][1] + q[k - 1][1]) / 2; n++; }
          for (const p of q) { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); } }
        if (!n) return null;
        const a = Math.round(Math.atan2((y0 + y1) / 2 - sy_ / n, (x0 + x1) / 2 - sx_ / n) / (Math.PI / 2)) * (Math.PI / 2);
        return [Math.cos(a), Math.sin(a)];
      };
      const out = [];
      for (const pl0 of place) {
        let pl = pl0;
        if (pl.u === cafeU) { const f = facing(pl.m[9] * 1000 + CX, pl.m[11] * 1000 + CY); if (f) pl = { u: pl.u, m: [f[1], 0, -f[0], 0, 1, 0, f[0], 0, f[1], pl.m[9], pl.m[10], pl.m[11]] }; }
        const m = pl.m, ax = [new T.Vector3(m[0], m[1], m[2]), new T.Vector3(m[3], m[4], m[5]), new T.Vector3(m[6], m[7], m[8])], t = new T.Vector3(m[9], m[10], m[11]);
        if (pl.u === cafeU && task >= 0 && taskF && onCabin(t.x * 1000 + CX, t.z * 1000 + CY)) {
          const A = new T.Matrix4().makeBasis(ax[0], ax[1], ax[2]), q = new T.Quaternion().setFromUnitVectors(taskF, new T.Vector3(0, 0, 1));
          const R = A.clone().multiply(new T.Matrix4().makeRotationFromQuaternion(q)), c = taskC.clone().applyMatrix4(R), e = R.elements;
          out.push({ u: task, m: [e[0], e[1], e[2], e[4], e[5], e[6], e[8], e[9], e[10], t.x - c.x, t.y - c.y, t.z - c.z] }); continue;
        }
        const k = [0, 2].find((a) => ax[a].length() >= STRETCH);
        if (k === undefined) { out.push(pl); continue; }
        const s = ax[k].length(), n = Math.round(s), [lo, hi] = boxOf(pl.u), span = hi[k] - lo[k], dir = ax[k].clone().normalize();
        for (let j = 0; j < n; j++) {
          const a2 = ax.map((v) => v.clone()); a2[k].multiplyScalar(1 / n);
          const sh = dir.clone().multiplyScalar(s * span * (j - (n - 1) / 2) / n + (s - s / n) * (lo[k] + span / 2));
          out.push({ u: pl.u, m: [a2[0].x, a2[0].y, a2[0].z, a2[1].x, a2[1].y, a2[1].z, a2[2].x, a2[2].y, a2[2].z, t.x + sh.x, t.y + sh.y, t.z + sh.z] });
        }
      }
      return out;
    }
    // the lounge's seats: [geometry, matrix, kind] (geometry: the slide's own part decoder)
    function loungeSeats(lg, geometry) {
      const out = [], u = D.units.findIndex((q) => LOUNGE_CHAIR.test(q.name || ""));
      if (u < 0 || (!lg.sofas.length && !lg.arms.length)) return out;
      const geos = [], all = [], low = [];                               // (the chair alone: its low pieces, its ottoman, left off)
      for (const p of D.parts.filter((q) => q.u === u && q.lv !== 2)) {
        const g = geometry(p), pos = g.getAttribute("position").array, ix = g.getIndex().array, { n, find } = pieces_(pos, ix);
        const top = new Map(); for (let t = 0; t < n; t++) { const r = find(t); for (let j = 0; j < 3; j++) top.set(r, Math.max(top.get(r) ?? -1e9, pos[ix[3 * t + j] * 3 + 1])); }
        for (let t = 0; t < n; t++) { const dest = top.get(find(t)) < 0.55 ? low : all; for (let j = 0; j < 3; j++) { const v = ix[3 * t + j] * 3; dest.push([pos[v], pos[v + 2]]); } }
        keepOnly(g, ix, n, (t) => top.get(find(t)) < 0.55); geos.push([g, p.k]);
      }
      if (!all.length || !low.length) return out;
      const xs = all.map((v) => v[0]), zs = all.map((v) => v[1]), c = new T.Vector3((Math.min(...xs) + Math.max(...xs)) / 2, 0, (Math.min(...zs) + Math.max(...zs)) / 2);
      const oc = low.reduce((s, v) => [s[0] + v[0], s[1] + v[1]], [0, 0]).map((v) => v / low.length), front = new T.Vector3(oc[0] - c.x, 0, oc[1] - c.z).normalize();
      const seat = (x, y, fx, fy) => {
        const q = new T.Quaternion().setFromUnitVectors(front, new T.Vector3(fx, 0, fy).normalize()), m4 = new T.Matrix4().makeRotationFromQuaternion(q);
        const cc = c.clone().applyMatrix4(m4); m4.setPosition(X(x) - cc.x, 0, Z(y) - cc.z);
        for (const [g, k] of geos) out.push([g, m4, k]);
      };
      // a sofa: its seat the plan's sofa (its lines' hull) SOFA.SEAT m up, a back along its back (away from the lounge's middle) and
      // an arm at each end, in the armchairs' own upholstery (the colour most of the chair's faces have)
      const up = (() => { const n = {}; for (const [g] of geos) { const c2 = g.getAttribute("color"); for (let i = 0; i < c2.count; i += 7) { const k = [c2.getX(i), c2.getY(i), c2.getZ(i)].map((v) => Math.round(v * 255 / 16) * 16).join(","); n[k] = (n[k] || 0) + 1; } }
        return Object.entries(n).sort((a, b) => b[1] - a[1])[0][0].split(",").map((v) => Math.min(255, Number(v))); })();
      const sb = bucket();
      for (const s of lg.sofas) {
        let best = null; for (let a = 0; a < 180; a += 2) { const r = a * Math.PI / 180, d = [Math.cos(r), Math.sin(r)], pr = s.pts.map((p) => p[0] * d[0] + p[1] * d[1]); const L = Math.max(...pr) - Math.min(...pr); if (!best || L > best.L) best = { d, L, lo: Math.min(...pr) }; }
        const nrm = [-best.d[1], best.d[0]], ps = s.pts.map((p) => p[0] * nrm[0] + p[1] * nrm[1]), D_ = Math.max(...ps) - Math.min(...ps), mn = (Math.min(...ps) + Math.max(...ps)) / 2;
        const ctr = [best.d[0] * (best.lo + best.L / 2) + nrm[0] * mn, best.d[1] * (best.lo + best.L / 2) + nrm[1] * mn];
        const toC = [s.c[0] - ctr[0], s.c[1] - ctr[1]], f = toC[0] * nrm[0] + toC[1] * nrm[1] >= 0 ? nrm : [-nrm[0], -nrm[1]];
        slabOf(sb, up, shapeOf([hull2(s.pts)]), 0, SOFA.SEAT);
        const L = best.L / 1000, Dm = D_ / 1000, ang = -Math.atan2(best.d[1], best.d[0]);
        const block = (w, h, d, along, across, y0) => { const x = ctr[0] + best.d[0] * along * 1000 - f[0] * across * 1000, y = ctr[1] + best.d[1] * along * 1000 - f[1] * across * 1000; boxAt(sb, up, w, h, d, X(x), y0 + h / 2, Z(y), ang); };
        block(L - 0.1, SOFA.BACK - SOFA.SEAT, SOFA.BACK_D, 0, Dm / 2 - SOFA.BACK_D / 2 - 0.02, SOFA.SEAT);
        for (const e of [-1, 1]) block(SOFA.ARM_W, SOFA.ARM - SOFA.SEAT, Dm - 0.1, e * (L / 2 - SOFA.ARM_W / 2 - 0.08), 0, SOFA.SEAT);
      }
      if (sb.pos.length) out.push([solid(sb.pos, sb.col), new T.Matrix4(), "soft"]);
      for (const a of lg.arms) for (const [x, y] of armSpots(a)) seat(x, y, a.c[0] - x, a.c[1] - y);
      for (const s of lg.extra || []) seat(s.x, s.y, s.fx, s.fy);
      return out;
    }

    // ---- the terraces' furniture as the plan draws it: on each deck (PLAN_DXF's Terrace spaces) the model's furniture goes (the
    // deck an area of the changes; the 28.10 pieces placed there too; plants stay) and the plan's goes in: its round and oval
    // tables (the model's round table, TERRACE.TABLE, sized to them), café chairs facing them, the communal tables the low stools
    // flank and the carrom table (as the plain tables), and, drawn here, its stools, bar ledges, fixed seating, planters, screens
    const TERRACE = { PAD: 150, TABLE: /^reht(#|$)/, LO: 0.45, HI: 0.75, LEDGE: 1.05, SEAT: 0.42, BACK: 0.78, PLANTER: 0.45, SCREEN: 1.8, MODULE: 950,
      COL: { ledge: [[192, 168, 144], "wood"], seat: [[85, 85, 91], "hard"], leg: [[154, 154, 160], "hard"], cushion: [[233, 226, 210], "soft"], back: [[214, 204, 184], "soft"],
        planter: [[201, 196, 187], "hard"], screen: [[217, 214, 207], "hard"] } };
    function terraceFurniture() {
      const out = { areas: [], place: [], tables: [], decks: [], prims: {}, clears: () => false };
      const decks = ((PD && PD.spaces) || []).filter((s) => s.type === "Terrace").map((s) => {
        const r = s.d.split("M")[1].replace(/Z/g, "").split("L").map((t) => t.trim().split(/\s+/).map(Number)), xs = r.map((q) => q[0]), ys = r.map((q) => q[1]);
        return [Math.min(...xs) + TERRACE.PAD, Math.min(...ys) + TERRACE.PAD, Math.max(...xs) - TERRACE.PAD, Math.max(...ys) - TERRACE.PAD]; });
      if (!decks.length) return out;
      const inDeck = (x, y) => decks.some(([a, b, c, d]) => x > a && x < c && y > b && y < d);
      out.decks = decks; out.areas = decks.map(([a, b, c, d]) => [[a, b], [c, b], [c, d], [a, d]]);
      const plants = new Set(D.parts.filter((p) => p.k === "plant").map((p) => p.u));
      out.clears = (pl) => !plants.has(pl.u) && inDeck(pl.m[9] * 1000 + CX, pl.m[11] * 1000 + CY);
      const furn = names.map((L) => /FUR|CHAIR|LOOSE/i.test(L)), circles = [], shapes = [], blocks = {};
      for (let i = 0; i < N; i++) {
        if (!furn[lay[i]]) continue;
        const q = ptsOf(i); if (q.length < 2) continue;
        const cx = q.reduce((s, p) => s + p[0], 0) / q.length, cy = q.reduce((s, p) => s + p[1], 0) / q.length;
        if (!inDeck(cx, cy)) continue;
        const tail = tails[path[i]], L = names[lay[i]];
        if (tail !== "(the plan itself)" && !/ISLAND SEATING|zw\$DAD8/.test(tail)) { const b = blocks[tail] || (blocks[tail] = []); b.push(...q); }
        const closed = q.length > 3 && (Math.hypot(q[0][0] - q.at(-1)[0], q[0][1] - q.at(-1)[1]) < 20 || kind[i] === 1); if (!closed) continue;
        const rs = q.map((p) => Math.hypot(p[0] - cx, p[1] - cy)), r = rs.reduce((a, b) => a + b) / rs.length, sd = Math.sqrt(rs.reduce((a, b) => a + (b - r) ** 2, 0) / rs.length);
        if (q.length >= 8 && sd < 0.06 * r) circles.push({ x: cx, y: cy, d: 2 * r, L, tail });
        else if (tail === "(the plan itself)") { const o = oriented(q); if (o) shapes.push({ ...o, lay: L }); }
      }
      const cluster = (ps, nr) => { const cl = []; for (const p of ps) { const g = cl.find((c) => Math.abs(c.cx / c.n - p[0]) < nr && Math.abs(c.cy / c.n - p[1]) < nr); if (g) { g.pts.push(p); g.cx += p[0]; g.cy += p[1]; g.n++; } else cl.push({ pts: [p], cx: p[0], cy: p[1], n: 1 }); } return cl.map((c) => oriented(c.pts)).filter(Boolean); };
      const blk = (re, nr = 1500) => Object.entries(blocks).filter(([k]) => re.test(k)).flatMap(([, v]) => cluster(v, nr));
      const tabs = circles.filter((c) => c.tail === "(the plan itself)" && /I-FURN|N-FURN/.test(c.L) && c.d >= 595).map((c) => ({ x: c.x, y: c.y, a: c.d, b: c.d, ang: 0 }));
      for (const s of shapes) if (s.lay === "AVA-FURNITURE" && s.fill > 0.7 && s.fill < 0.85 && s.W > 1000) tabs.push({ x: s.c[0], y: s.c[1], a: s.L, b: s.W, ang: Math.atan2(s.u[1], s.u[0]) });
      const tu = D.units.findIndex((q) => TERRACE.TABLE.test(q.name || ""));
      if (tu >= 0) {
        const f = new Float32Array(bytes_(D.units[tu].m)).subarray(0, 12), [lo, hi] = boxOf(tu);
        const Mref = new T.Matrix4().set(f[0], f[3], f[6], 0, f[1], f[4], f[7], 0, f[2], f[5], f[8], 0, 0, 0, 0, 1);
        const lc = new T.Vector3((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2);
        const wbox = new T.Box3().setFromPoints([0, 1].flatMap((i) => [0, 1].flatMap((j) => [0, 1].map((k) => new T.Vector3(i ? hi[0] : lo[0], j ? hi[1] : lo[1], k ? hi[2] : lo[2]).applyMatrix4(Mref)))));
        const dx = wbox.max.x - wbox.min.x, dz = wbox.max.z - wbox.min.z;
        for (const t of tabs) {
          const Lm = new T.Matrix4().makeRotationY(-t.ang).multiply(new T.Matrix4().makeScale(t.a / 1000 / dx, 1, t.b / 1000 / dz)).multiply(Mref);
          const c = lc.clone().applyMatrix4(Lm), e = Lm.elements;
          out.place.push({ u: tu, m: [e[0], e[1], e[2], e[4], e[5], e[6], e[8], e[9], e[10], X(t.x) - c.x, f[10], Z(t.y) - c.z] });
        }
      }
      const cafeU = D.units.findIndex((u) => CAFE_CHAIR.test(u.name || "")), y0 = ((D.changes && D.changes.place) || []).find((pl) => pl.u === cafeU)?.m[10] ?? 0;
      const chairs = circles.filter((c) => /zw\$DAD8/.test(c.tail) || (c.tail === "(the plan itself)" && /N-FURN/.test(c.L) && c.d > 500 && c.d < 595)).map((c) => [c.x, c.y])
        .concat(blk(/R18\$0\$A\$C3A641C51/, 450).map((o) => o.c));
      if (cafeU >= 0) for (const [x, y] of chairs) {
        const t = tabs.slice().sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y))[0]; if (!t) continue;
        const fx = t.x - x, fy = t.y - y, n = Math.hypot(fx, fy) || 1, f = [fx / n, fy / n];
        out.place.push({ u: cafeU, m: [f[1], 0, -f[0], 0, 1, 0, f[0], 0, f[1], X(x), y0, Z(y)] });
      }
      const P_ = out.prims, pb = (k) => P_[TERRACE.COL[k][1]] || (P_[TERRACE.COL[k][1]] = bucket());
      const bx = (w, h, d, x, y, ang, yy, k) => boxAt(pb(k), TERRACE.COL[k][0], w, h, d, X(x), yy + h / 2, Z(y), -ang);
      const cyl = (r, h, x, yy, y, seg, k) => { const g = new T.CylinderGeometry(r, r, h, seg); g.translate(X(x), yy, Z(y)); put(pb(k), g, TERRACE.COL[k][0]); };
      const stool = (x, y, d, h) => { cyl(d / 2000, 0.05, x, h - 0.025, y, 20, "seat"); cyl(0.02, h - 0.05, x, (h - 0.05) / 2, y, 8, "leg"); cyl(d / 2600, 0.02, x, 0.01, y, 16, "leg"); };
      for (const s of shapes.filter((s) => /OB-I-FURN-MFUR/.test(s.lay) && s.W >= 300 && s.W <= 600 && s.L >= 3000)) bx(s.L / 1000, TERRACE.LEDGE, s.W / 1000, s.c[0], s.c[1], Math.atan2(s.u[1], s.u[0]), 0, "ledge");
      for (const c of circles.filter((c) => /ISLAND SEATING/.test(c.tail))) stool(c.x, c.y, c.d, TERRACE.HI);
      const low = circles.filter((c) => c.tail === "(the plan itself)" && c.d >= 420 && c.d <= 480 && /MFUR|AVA/.test(c.L));
      for (const c of low) stool(c.x, c.y, c.d, TERRACE.LO);
      for (const o of blk(/Stool_ CH-10/, 450)) stool(o.c[0], o.c[1], 440, TERRACE.LO);
      const seen = new Set();
      for (const c of low) {
        if (seen.has(c)) continue; const g = [c]; seen.add(c);
        for (let k = 0; k < g.length; k++) for (const o of low) if (!seen.has(o) && Math.hypot(o.x - g[k].x, o.y - g[k].y) < 1700) { seen.add(o); g.push(o); }
        if (g.length < 4) continue;
        const o = oriented(g.map((p) => [p.x, p.y])); if (!o) continue;
        out.tables.push([o.c[0], o.c[1], o.L + 450, Math.max(700, o.W - 650), Math.atan2(o.u[1], o.u[0]) * 180 / Math.PI]);
      }
      for (const o of blk(/^Carrom Table/)) out.tables.push([o.c[0], o.c[1], 850, 850, Math.atan2(o.u[1], o.u[0]) * 180 / Math.PI]);
      for (const o of blk(/^fixed seating/)) {
        const ang = Math.atan2(o.u[1], o.u[0]), at = (s) => [o.c[0] + o.u[0] * s, o.c[1] + o.u[1] * s];
        for (const s of [-TERRACE.MODULE, 0, TERRACE.MODULE]) { const [x, y] = at(s); bx(0.8, TERRACE.SEAT, o.W / 1000 - 0.08, x, y, ang, 0, "cushion"); }
        for (const e of [-1, 1]) { const [x, y] = at(e * (o.L / 2 - 60)); bx(0.12, TERRACE.BACK, o.W / 1000 - 0.08, x, y, ang, 0, "back"); }
      }
      for (const s of shapes.filter((s) => /OB-I-FURN-MFUR/.test(s.lay) && s.W >= 900 && s.W <= 1300 && s.L >= 1500 && s.L <= 2100)) bx(s.L / 1000, TERRACE.PLANTER, s.W / 1000, s.c[0], s.c[1], Math.atan2(s.u[1], s.u[0]), 0, "planter");
      for (const o of blk(/^mobil partition/)) bx(o.L / 1000, TERRACE.SCREEN, 0.06, o.c[0], o.c[1], Math.atan2(o.u[1], o.u[0]), 0, "screen");
      return out;
    }
    const terraceMeshes = (tf) => Object.entries(tf.prims || {}).map(([k, b]) => [solid(b.pos, b.col), k]);

    // ---- the tables the plan draws as an outline of its own (on OB_Furniture, no block) that neither the model nor the 28.10
    // tables have (Ritika: "this table is missing", then "it should be in this shape": the boardroom's 8.6 m table, its slot open
    // at one end): the outline itself as its top, PLAN_TABLE.TOP m up, a pedestal under each arm at a quarter of its length from
    // each end (none in the slot), in the tables' beige
    const PLAN_TABLE = { LAYER: "OB_Furniture", MIN_L: 3000, W: [900, 3200], PTS: 20, NEAR: 1000, TOP: 0.75, SLAB: 0.04, PED: [0.5, 0.6], RGB: [192, 168, 144] };
    function planTables(tables) {
      const b = bucket(), have = tables.map((t) => [t[0], t[1]]), H = PLAN_TABLE.TOP - PLAN_TABLE.SLAB;
      for (let i = 0; i < N; i++) {
        if (names[lay[i]] !== PLAN_TABLE.LAYER || paths[path[i]] !== "(the plan itself)") continue;
        const q = ptsOf(i); if (q.length < PLAN_TABLE.PTS) continue;
        const o = oriented(q); if (!o || o.L < PLAN_TABLE.MIN_L || o.W < PLAN_TABLE.W[0] || o.W > PLAN_TABLE.W[1]) continue;
        if (have.some(([x, y]) => Math.hypot(x - o.c[0], y - o.c[1]) < PLAN_TABLE.NEAR)) continue;   // (the 28.10 plan's own: drawn already)
        slabOf(b, PLAN_TABLE.RGB, shapeOf([q]), H, PLAN_TABLE.TOP);
        const inside = (x, y) => { let c = false; for (let a = 0, e = q.length - 1; a < q.length; e = a++) { const [x1, y1] = q[a], [x2, y2] = q[e];
          if ((y1 > y) !== (y2 > y) && x < ((x2 - x1) * (y - y1)) / (y2 - y1) + x1) c = !c; } return c; };
        const ang = Math.atan2(o.u[1], o.u[0]), v = [-o.u[1], o.u[0]];
        for (const s of [-1, 1]) {
          const ax = o.c[0] + o.u[0] * s * o.L / 4, ay = o.c[1] + o.u[1] * s * o.L / 4, runs = []; let run = null;
          for (let t = -o.W / 2; t <= o.W / 2; t += 20) { const on = inside(ax + v[0] * t, ay + v[1] * t);
            if (on && run === null) run = t; if ((!on || t + 20 > o.W / 2) && run !== null) { runs.push([run, t]); run = null; } }
          for (const [t0, t1] of runs.filter(([t0, t1]) => t1 - t0 > 250)) {
            const w = Math.min(PLAN_TABLE.PED[0], (t1 - t0) / 1000 * 0.6), t = (t0 + t1) / 2, x = ax + v[0] * t, y = ay + v[1] * t;
            boxAt(b, PLAN_TABLE.RGB, PLAN_TABLE.PED[1], H, w, X(x), H / 2, Z(y), -ang);
          }
        }
      }
      return b.pos.length ? [solid(b.pos, b.col)] : [];
    }

    // ---- the furniture put right, as the page puts it (skip: meshes left alone, the phone booths): the model's partitions' and
    // doors' frames (its hard pieces up over TALL m standing TALL_SPAN m or more, or wholly above TALL m: the plan's walls, glass
    // and doors stand there now); its old tables under a new one (CHANGES.tables: a piece with its top at a table's height,
    // OLD_TOP m, over a third of a new one, and its legs); its pieces on the decks under DECK_LOW m; every table one beige
    function trim(grp, tables, decks, skip) {
      const TALL = 1.9, TALL_SPAN = 1.5, OLD_TOP = [0.65, 1.0], DECK_LOW = 1.3, BEIGE = [192 / 255, 168 / 255, 144 / 255], TOP = [0.55, 0.9];
      // (the page's three passes in one: each takes whole pieces out, so the pieces the next one sees are the same; a frame is up
      // over TALL m, a table's top or legs and a deck's piece under it, so none is taken for another's)
      const each = (fn) => grp.traverse((m) => { if (m.isMesh && !skip.has(m)) fn(m); });
      const plain = (m) => { const cc = m.geometry.getAttribute("color"); return cc && cc.count && [...Array(Math.min(cc.count, 64)).keys()].every((i) => Math.abs(cc.getX(i) - 240 / 255) < 0.01 && Math.abs(cc.getY(i) - 240 / 255) < 0.01); };
      const newT = tables.map(([x, y, w, d]) => [x - w / 2, y - d / 2, x + w / 2, y + d / 2]);
      const onDeck = (x, z) => decks.some(([a, b, c, d]) => x > a && x < c && z > b && z < d);
      each((m) => {
        const g = m.geometry, hard = !!(m.material && m.material.userData && m.material.userData.kind === "hard");
        if (m.isInstancedMesh) { if (hard) { g.computeBoundingBox(); const b = g.boundingBox; if (b.max.y > TALL && b.max.y - b.min.y >= TALL_SPAN) m.count = 0; } return; }
        if (!g.getIndex()) return;
        const rest = !plain(m) && (newT.length || decks.length);
        if (!hard && !rest) return;
        const pos = g.getAttribute("position").array, ix = g.getIndex().array, { n, find } = pieces_(pos, ix), bb = new Map();
        for (let t = 0; t < n; t++) { const r = find(t); let b = bb.get(r); if (!b) bb.set(r, b = [1e9, 1e9, 1e9, -1e9, -1e9, -1e9]);
          for (let j = 0; j < 3; j++) { const v = ix[3 * t + j] * 3; b[0] = Math.min(b[0], pos[v]); b[1] = Math.min(b[1], pos[v + 1]); b[2] = Math.min(b[2], pos[v + 2]); b[3] = Math.max(b[3], pos[v]); b[4] = Math.max(b[4], pos[v + 1]); b[5] = Math.max(b[5], pos[v + 2]); } }
        const gone = new Set(), tops = [];
        for (const [r, b] of bb) {
          if (hard && ((b[4] > TALL && b[4] - b[1] >= TALL_SPAN) || b[1] > TALL)) { gone.add(r); continue; }        // (a frame)
          if (!rest) continue;
          if (decks.length && b[4] < DECK_LOW && onDeck((b[0] + b[3]) / 2 * 1000 + CX, (b[2] + b[5]) / 2 * 1000 + CY)) gone.add(r);   // (on a deck)
          if (b[4] < OLD_TOP[0] || b[4] > OLD_TOP[1]) continue;
          const px = [b[0] * 1000 + CX, b[2] * 1000 + CY, b[3] * 1000 + CX, b[5] * 1000 + CY];
          if (newT.some((q) => { const w = Math.min(px[2], q[2]) - Math.max(px[0], q[0]), h = Math.min(px[3], q[3]) - Math.max(px[1], q[1]); return w > 0 && h > 0 && w * h >= 0.33 * (q[2] - q[0]) * (q[3] - q[1]); })) { gone.add(r); tops.push(b); }   // (an old table's top)
        }
        if (tops.length) for (const [r, b] of bb) if (tops.some((t) => b[0] >= t[0] - 0.05 && b[3] <= t[3] + 0.05 && b[2] >= t[2] - 0.05 && b[5] <= t[5] + 0.05 && b[4] <= t[4] + 0.02)) gone.add(r);   // (its legs)
        if (gone.size) keepOnly(g, ix, n, (t) => gone.has(find(t)));
      });
      const white = (c, i) => Math.min(c.getX(i), c.getY(i), c.getZ(i)) > 0.85 && Math.max(c.getX(i), c.getY(i), c.getZ(i)) - Math.min(c.getX(i), c.getY(i), c.getZ(i)) < 0.08;
      each((m) => {
        const g = m.geometry, c = g.getAttribute("color"); if (!c) return;
        const pos = g.getAttribute("position"), ix = g.getIndex() ? g.getIndex().array : null, n = ix ? ix.length / 3 : pos.count / 3, paint = new Set();
        let all = true; for (let i = 0; i < c.count && all; i++) if (Math.abs(c.getX(i) - 240 / 255) > 0.01 || Math.abs(c.getY(i) - 240 / 255) > 0.01) all = false;
        const M4 = new T.Matrix4(), vv = new T.Vector3();
        if (m.isInstancedMesh) for (let i = 0; i < m.count; i++) { m.getMatrixAt(i, M4); if (Math.abs(M4.determinant()) > 1e-6) break; }
        const wy = (i) => (m.isInstancedMesh ? vv.fromBufferAttribute(pos, i).applyMatrix4(M4).y : pos.getY(i));
        if (all) for (let i = 0; i < c.count; i++) paint.add(i);
        else for (let t = 0; t < n; t++) { const v = [0, 1, 2].map((j) => (ix ? ix[3 * t + j] : 3 * t + j)); if (v.every((i) => { const y = wy(i); return y >= TOP[0] && y <= TOP[1] && white(c, i); })) v.forEach((i) => paint.add(i)); }
        for (const i of paint) c.setXYZ(i, ...BEIGE);
        if (paint.size) c.needsUpdate = true;
      });
    }
    // ---- the open seating by the coffee bar (Ritika: "the open seating area by the coffee bar is empty.. furnish it like the
    // reference render"): the plan draws no planter, bench or café tables there, only four 460 mm circles (N-FURN-LOOSE
    // FURNITURE, no block), so as the render has it, at the plan's scale: a long low white planter with rounded ends along the
    // façade, from the column to the glass partition, its bed behind (the model's plants along the glass stand in it, raised
    // to its soil) and a bench along its room side, a dark seat pad on the white base; at its near end, in front of the column,
    // two pedestal café tables (the tables' beige, dark stems) with a café chair at each; the plan's circles as sage poufs
    const NOOK = { X: [91600, 97400], Y: [37500, 38800], BED: 37980, R: 350, SEAT: 0.42, PAD: 0.05, RIM: 0.55, SOIL: 0.53,
      TABLES: [[90250, 37150], [91300, 36450]], CHAIRS: [[89700, 37150], [91300, 35900]], TABLE: { D: 600, H: 0.72, STEM: 0.06, FOOT: 450 },
      POUF: { D: 460, H: 0.42, IN: [87500, 33500, 96000, 37000] },
      RGB: { base: [236, 234, 230], soil: [96, 82, 68], pad: [84, 74, 68], top: [192, 168, 144], stem: [62, 60, 60], pouf: [176, 190, 160] } };
    const rounded = (x0, y0, x1, y1, r, n = 6) => { const q = [];
      for (const [cx, cy, a0] of [[x1 - r, y0 + r, -Math.PI / 2], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, Math.PI / 2], [x0 + r, y0 + r, Math.PI]])
        for (let k = 0; k <= n; k++) { const a = a0 + (k / n) * Math.PI / 2; q.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
      return q; };
    function coffeeNook() {
      const out = { place: [], prims: {}, bed: [NOOK.X[0], NOOK.BED, NOOK.X[1], NOOK.Y[1]], soil: NOOK.SOIL };
      const pb = (k) => out.prims[k] || (out.prims[k] = bucket()), C = NOOK.RGB;
      const cyl = (k, rgb, r, y0, y1, x, y, seg = 24) => { const g = new T.CylinderGeometry(r, r, y1 - y0, seg); g.translate(X(x), (y0 + y1) / 2, Z(y)); put(pb(k), g, rgb); };
      const [x0, x1] = NOOK.X, [y0, y1] = NOOK.Y;
      slabOf(pb("hard"), C.base, shapeOf([rounded(x0, y0, x1, y1, NOOK.R)]), 0, NOOK.SEAT);                       // (the planter's base)
      slabOf(pb("hard"), C.base, shapeOf([rounded(x0, NOOK.BED, x1, y1, NOOK.R)]), NOOK.SEAT, NOOK.RIM);           // (its bed's rim)
      slabOf(pb("hard"), C.soil, shapeOf([rounded(x0 + 60, NOOK.BED + 60, x1 - 60, y1 - 60, NOOK.R - 60)]), NOOK.RIM, NOOK.RIM + 0.004);   // (its soil)
      slabOf(pb("soft"), C.pad, shapeOf([rounded(x0 + 250, y0 + 40, x1 - 250, NOOK.BED - 20, 80)]), NOOK.SEAT, NOOK.SEAT + NOOK.PAD);   // (the bench's pad)
      const t = NOOK.TABLE;
      for (const [x, y] of NOOK.TABLES) {
        cyl("wood", C.top, t.D / 2000, t.H - 0.03, t.H, x, y); cyl("hard", C.stem, t.STEM / 2, 0.02, t.H - 0.03, x, y, 12); cyl("hard", C.stem, t.FOOT / 2000, 0, 0.02, x, y);
      }
      const cafeU = D.units.findIndex((u) => CAFE_CHAIR.test(u.name || "")), y0c = ((D.changes && D.changes.place) || []).find((pl) => pl.u === cafeU)?.m[10] ?? 0;
      if (cafeU >= 0) NOOK.CHAIRS.forEach(([x, y], i) => {                                                        // (each facing its table)
        const [tx, ty] = NOOK.TABLES[i], n = Math.hypot(tx - x, ty - y) || 1, f = [(tx - x) / n, (ty - y) / n];
        out.place.push({ u: cafeU, m: [f[1], 0, -f[0], 0, 1, 0, f[0], 0, f[1], X(x), y0c, Z(y)] });
      });
      const [a, b, c, d] = NOOK.POUF.IN;                                                                          // (the plan's circles)
      for (let i = 0; i < N; i++) {
        if (names[lay[i]] !== "N-FURN-LOOSE FURNITURE" || paths[path[i]] !== "(the plan itself)") continue;
        const q = ptsOf(i); if (q.length < 8) continue;
        const [bx0, by0, bx1, by1] = [box[4 * i], box[4 * i + 1], box[4 * i + 2], box[4 * i + 3]];          // (its box: its points bunch unevenly)
        const cx = (bx0 + bx1) / 2, cy = (by0 + by1) / 2, r = Math.max(bx1 - bx0, by1 - by0) / 2;
        if (cx < a || cx > c || cy < b || cy > d || Math.abs(2 * r - NOOK.POUF.D) > 60) continue;
        cyl("soft", C.pouf, r / 1000, 0, NOOK.POUF.H, cx, cy);
      }
      return out;
    }
    // (the model's plants in the planter's bed stood up on its soil)
    const raise = (placements, nook) => { const plants = new Set(D.parts.filter((p) => p.k === "plant" && p.u >= 0).map((p) => p.u)), [a, b, c, d] = nook.bed;
      for (const u of plants) for (const m4 of placements[u]) { const e = m4.elements, x = e[12] * 1000 + CX, y = e[14] * 1000 + CY;
        if (Math.abs(m4.determinant()) > 1e-12 && x > a && x < c && y > b && y < d) e[13] += nook.soil; } };
    const nookMeshes = (nook) => Object.entries(nook.prims).map(([k, b]) => [solid(b.pos, b.col), k]);

    return { pieces, solid, loungeGroups, fixPlace, loungeSeats, terraceFurniture, terraceMeshes, planTables, coffeeNook, raise, nookMeshes, trim };
  }

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
    // the axo debug page's model (tools/acko/axo_debug.html, baked into AXO_SKP.changes.fit by tools/acko/axo_skp_fit.py; Ritika:
    // "now the axo model is updated in tis branch.. bring in the model changes.. retain the style as it is here"): the floor
    // plan's walls, glass, doors, columns, façade glazing, the terraces' handrails and the phone booths in place of the model's
    // walls, glass and façade (its core stays), and its furniture fitted to the plan as the page fits it; in this slide's
    // materials. (The page builds the model through here after its own fit, its flags on the changes: then none of this.)
    const CHG = D.changes, FIT = CHG && CHG.fit && !CHG.debugFixed ? CHG.fit : null, ARCH = ["wall", "top", "glass", "mullion"];
    let place = CHG ? CHG.place : [], areasP = CHG ? CHG.areas : [], tables = CHG ? CHG.tables || [] : [];
    const FT = FIT ? fitting({ T, D, P, X, Z, CX, CY, shift: FIT.shift }) : null, booths = new Map();
    let lg = null, tf = null, nook = null;
    if (FIT) {
      for (const [ty, , , u, m] of FIT.pieces) if (ty === "booth") (booths.get(u) || booths.set(u, []).get(u)).push(m);
      place = place.concat(FIT.place);
      lg = FT.loungeGroups(); place = FT.fixPlace(place, lg);
      tf = FT.terraceFurniture(); areasP = areasP.concat(tf.areas); tables = tables.concat(tf.tables);
      place = place.filter((pl) => !tf.clears(pl)).concat(tf.place);
      nook = FT.coffeeNook(); place = place.concat(nook.place);
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
    if (!FIT) {                                                         // (the fit has the plan's glass handrails there)
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
    const LOW = 1.3, FURN = ["wood", "soft", "hard"];
    const areas = areasP.map((r) => r.map(([x, y]) => [X(x), Z(y)]));
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
      for (const { u, m } of place) placements[u].push(new T.Matrix4().set(m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10], m[2], m[5], m[8], m[11], 0, 0, 0, 1));
      // the phone booths where the plan draws them, the model's own booth component on each (its own placements gone)
      for (const [u, ms] of booths) placements[u] = ms.map((m) => new T.Matrix4().set(m[0], m[3], m[6], m[9], m[1], m[4], m[7], m[10], m[2], m[5], m[8], m[11], 0, 0, 0, 1));
    }
    if (nook) FT.raise(placements, nook);
    // a merged part's furniture in the areas: its pieces (triangles joined where they share a corner) that stay under LOW m, have
    // their middle in one and are under BIG m across; a longer one is millwork (the café's counter) and stays
    const BIG = 3.2;
    const cut = (g) => {
      const pos = g.getAttribute("position").array, ix = g.getIndex().array, n = ix.length / 3, cand = [], up = new Int32Array(n).fill(-1);
      const find = (a) => { while (up[a] >= 0 && up[up[a]] >= 0) { up[a] = up[up[a]]; a = up[a]; } return up[a] >= 0 ? up[a] : a; };
      const at = new Map(), key = (v) => ((Math.round(pos[v] * 200) + 40000) * 80000 + Math.round(pos[v + 1] * 200) + 40000) * 80000 + Math.round(pos[v + 2] * 200) + 40000;
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
    const fine = [], coarse = [], lo = new T.Vector3(1e9, 1e9, 1e9), hi = new T.Vector3(-1e9, -1e9, -1e9), ink = [], boothMesh = new Set();
    for (const [pi, p] of D.parts.entries()) {
      if (FIT && ARCH.includes(p.k) && !booths.has(p.u)) continue;          // (the plan's walls, glass and façade instead)
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
      if (booths.has(p.u)) boothMesh.add(mesh);
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
    if (tables.length) {
      const pos = [], m4 = new T.Matrix4(), q = new T.Quaternion(), Y = new T.Vector3(0, 1, 0);
      const box = (w, h, d, x, y, z, M4) => { const b = new T.BoxGeometry(w, h, d).toNonIndexed(); b.translate(x, y, z); b.applyMatrix4(M4); pos.push(...b.getAttribute("position").array); };
      for (const [x, y, w, d, a] of tables) {
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
    if (CHG && CHG.walls && !FIT) {
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
    // the fit's pieces (FIT.pieces): walls, partitions and columns solid in a wall's white, edged in the ink; glass partitions, the
    // façade's glazing and the terraces' handrails as the page draws a glass partition (a pane between rails, posts along it),
    // doors as its glass doors (jambs, rails, a leaf, pulls); the panes in the model's glass, the frames in its metal; the
    // external glazing toned down (Ritika: "tone down the external glazing glass"): the pale pane glass of the deck's own axo
    // (AxoModel's façade: #dfe9ef at 16%)
    if (FIT) {
      const B = FT.pieces(FIT.pieces), SEE_K = { glass: 0.35, pane: 0.16 };
      const own = (kind) => mats[kind + "28"] || (mats[kind + "28"] = reg(focusable(new T.MeshLambertMaterial(SEE_K[kind]
        ? { color: 0xffffff, vertexColors: true, flatShading: true, transparent: true, opacity: SEE_K[kind], depthWrite: false, side: T.DoubleSide, shadowSide: T.BackSide }
        : { color: 0xffffff, vertexColors: true, flatShading: true, side: T.DoubleSide, shadowSide: T.BackSide }), kind), kind, true));
      for (const [b, kind, grp, edged] of [[B.wall, "wall", G.walls, true], [B.pane, "glass", G.glass, false], [B.fpane, "pane", G.glass, false], [B.frame, "mullion", G.facade, false]]) {
        if (!b.pos.length) continue;
        const g = FT.solid(b.pos, b.col), mesh = new T.Mesh(g, own(kind));
        if (SEE_K[kind]) mesh.renderOrder = 2;
        grp.add(mesh); REG.meshes.push([mesh, kind]); if (edged) ink.push(new T.EdgesGeometry(g, 30));
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
    // the furniture as the page puts it right (FT.trim: the model's frames, its old tables under the new, its pieces on the decks,
    // every table one beige), then the plan's lounge seats and the terraces' own furniture
    if (FIT) {
      FT.trim(G.furniture, tables, tf.decks || [], boothMesh);
      for (const [g, m4, k] of FT.loungeSeats(lg, geometry)) { const m = new T.Mesh(g, matOf(k)); m.applyMatrix4(m4); G.furniture.add(m); REG.meshes.push([m, k]); }
      for (const [g, k] of FT.terraceMeshes(tf)) { const m = new T.Mesh(g, matOf(k)); G.furniture.add(m); REG.meshes.push([m, k]); }
      for (const [g, k] of FT.nookMeshes(nook)) { const m = new T.Mesh(g, matOf(k)); G.furniture.add(m); REG.meshes.push([m, k]); }
      for (const g of FT.planTables(tables)) { const m = new T.Mesh(g, matOf("wood")); G.furniture.add(m); REG.meshes.push([m, "wood"]); }
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
    M = { scene, groups: G, X, Z, CX, CY, slab: A.slab, source: D.source, areas: areasP };   // (areas: where the furniture is the plan's)
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
