// Conceptual axo of the Acko test fit, built in three.js from axo.json (see extract_axo.py).
// Bundled by esbuild into dist/axo.bundle.js (global AckoAxo), used both by render.mjs for the stills
// and inline in index-testfit.html for the interactive step.
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

// plan boxes [x0, x1, y0, y1] in metres (x east, y south); the stills and the presets frame these
export const VIEWS = {
  floor:  { name: 'Whole floor', box: [0, 246, 1.5, 36.5] },
  west:   { name: 'West',        box: [0, 112, 1.5, 36.5] },
  middle: { name: 'Middle',      box: [78, 192, 1.5, 36.5] },
  east:   { name: 'East',        box: [166, 246, 1.5, 36.5] },
};
export const NAMES = {
  booth: 'Phone booth', sprint: 'Quick sprint room', huddle: 'Collaboration huddle', dept: 'Departmental room',
  cabin: 'Executive corner cabin', zen: 'Zen room', prayer: 'Prayer room', mother: "Mother's room", board: 'Boardroom',
  hatchery: 'The Hatchery', studio: 'The Studio', visitor: 'Visitor hub', hub: 'Hub room', training: 'Training room',
  cafe: 'Cafeteria', coffee: 'Coffee corner', collab: 'Collaboration zone', reception: 'Reception', entry: 'Entry',
  work: 'Work hall', corridor: 'The loop', lift: 'Lift lobby', washroom: 'Washrooms', ahu: 'AHU room',
  ups: 'UPS, server and BMS', stair: 'Fire exit stair', out: 'Base building (out of scope)',
};
const NB_COLOR = { N01: '#ff7a59', N02: '#f0b43a', N03: '#2ec4b6', N04: '#58a9ff', N05: '#ef72b2', N06: '#a3d977', R1: '#7c5cff', R2: '#7c5cff' };
const NB_NAME = { N01: 'Neighbourhood 01', N02: 'Neighbourhood 02', N03: 'Neighbourhood 03', N04: 'Neighbourhood 04', N05: 'Neighbourhood 05', N06: 'Neighbourhood 06', R1: 'West reception', R2: 'East reception' };

const H = { slab: 0.3, wall: 2.4, core: 3.2, facade: 3.0, rail: 1.1, deskTop: 0.75, desk: 0.05, seat: 0.48, seatH: 0.2 };
const C = {   // the reference look
  slabTop: '#e6e7e8', slabSide: '#c4c6c9', work: '#dcdddf', corridor: '#5b5d63', collab: '#e4e0d8', coffee: '#e6e0d6',
  cafe: '#efe7b4', training: '#efe7b4', reception: '#e6e4df', entry: '#d9d4ff', terrace: '#9fae80',
  roomFloor: '#cdbde6', glass: '#7c5cb8', glassEdge: '#4b3480', core: '#b9b9bb', coreEdge: '#77777b', wall: '#a593cc',
  wallEdge: '#9a9a9a', column: '#d4d3d0', desk: '#d7ab7c', deskEdge: '#9b7350', chair: '#5b5b66', leaf: '#5f9444', leaf2: '#4c7d36',
  pot: '#dad7d0', facadeGlass: '#cfe3ea', mullion: '#9da3a8',
};

// ---------- geometry helpers ----------
function shapeOf(rings) {
  const toV = r => r.map(([x, y]) => new THREE.Vector2(x, -y));
  const s = new THREE.Shape(toV(rings[0]));
  for (const h of rings.slice(1)) s.holes.push(new THREE.Path(toV(h)));
  return s;
}
const asRings = p => (Array.isArray(p[0][0]) ? p : [p]);
function prism(rings, y0, y1) {
  const g = new THREE.ExtrudeGeometry(shapeOf(asRings(rings)), { depth: y1 - y0, bevelEnabled: false, curveSegments: 4 });
  g.rotateX(-Math.PI / 2); g.translate(0, y0, 0);
  return g;
}
function flat(rings, y) {
  const g = new THREE.ShapeGeometry(shapeOf(asRings(rings)), 4).toNonIndexed();
  g.rotateX(-Math.PI / 2); g.translate(0, y, 0);
  return g;
}
function bar(a, b, y0, y1, th) {      // a thin upright panel from plan point a to b
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
  const g = new THREE.BoxGeometry(L, y1 - y0, th).toNonIndexed();
  g.rotateY(-Math.atan2(dy, dx));
  g.translate((a[0] + b[0]) / 2, (y0 + y1) / 2, (a[1] + b[1]) / 2);
  return g;
}
function merge(list) {
  const gs = list.filter(Boolean).map(g => { g.deleteAttribute('uv'); return g.index ? g.toNonIndexed() : g; });
  return gs.length ? mergeGeometries(gs, false) : null;
}
function edgesOf(rings) {                                  // plan polygon edges as [a, b] pairs
  const out = [];
  for (const r of asRings(rings)) for (let i = 0; i < r.length; i++) out.push([r[i], r[(i + 1) % r.length]]);
  return out;
}
const mat = (c, o = {}) => new THREE.MeshLambertMaterial({ color: c, ...o });
function mesh(g, m, { shadow = true, receive = true } = {}) {
  if (!g) return null;
  const x = new THREE.Mesh(g, m); x.castShadow = shadow; x.receiveShadow = receive; return x;
}
function lines(g, color, opacity = 1, angle = 25) {
  if (!g) return null;
  return new THREE.LineSegments(new THREE.EdgesGeometry(g, angle), new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity }));
}
function inside(pt, ring) {
  let c = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}
const centroid = r => { let x = 0, y = 0; for (const p of r) { x += p[0]; y += p[1]; } return [x / r.length, y / r.length]; };

// ---------- the model ----------
function buildShell(A) {     // slab, terraces, façade, cores, columns
  const g = new THREE.Group();
  const add = o => o && g.add(o);
  // slab and terraces
  add(mesh(prism(A.slab, -H.slab, 0), [mat(C.slabTop), mat(C.slabSide)], { shadow: false }));
  add(mesh(merge(A.terraces.map(t => prism(t, -H.slab, 0))), mat(C.terrace), { shadow: false }));
  // façade: glass, mullions every ~1.5 m, a head rail; glass railing on the terraces' open edge
  const glass = [], mull = [], rail = [];
  const fac = A.facade;
  for (let i = 0; i < fac.length; i++) {
    const a = fac[i], b = fac[(i + 1) % fac.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    glass.push(bar(a, b, 0, H.facade, 0.03));
    rail.push(bar(a, b, H.facade - 0.12, H.facade, 0.1), bar(a, b, 0, 0.1, 0.1));
    const n = Math.max(1, Math.round(L / 1.5));
    for (let k = 0; k <= n; k++) {
      const t = k / n, p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
      const q = [p[0] + (b[0] - a[0]) / L * 0.07, p[1] + (b[1] - a[1]) / L * 0.07];
      mull.push(bar(p, q, 0, H.facade, 0.07));
    }
  }
  const south = Math.max(...A.slab.map(p => p[1]));
  for (const t of A.terraces) for (const [a, b] of edgesOf(t)) {
    if (Math.abs(a[1] - south) < 0.05 && Math.abs(b[1] - south) < 0.05) {
      glass.push(bar(a, b, 0, H.rail, 0.03)); rail.push(bar(a, b, H.rail - 0.05, H.rail, 0.06));
    }
  }
  add(mesh(merge(glass), new THREE.MeshLambertMaterial({ color: C.facadeGlass, transparent: true, opacity: 0.16, depthWrite: false }), { shadow: false, receive: false }));
  add(mesh(merge(mull.concat(rail)), mat(C.mullion), { receive: false }));
  // cores, columns, solid walls
  const cores = merge(A.cores.map(r => prism(r, 0, H.core)));
  add(mesh(cores, mat(C.core, { transparent: true, opacity: 0.9 })));
  add(lines(cores, C.coreEdge, 0.8));
  add(mesh(merge(A.columns.map(r => prism(r, 0, H.core))), mat(C.column)));
  return g;
}

function buildFit(A) {       // partitions, furniture, plants
  const g = new THREE.Group();
  const add = o => o && g.add(o);
  // solid partitions read like the reference: a denser, frosted version of the room glass
  const walls = merge(A.walls.solid.map(r => prism(r, 0, H.wall)));
  add(mesh(walls, new THREE.MeshLambertMaterial({ color: C.wall, transparent: true, opacity: 0.62 }), { receive: false }));
  add(lines(walls, C.glassEdge, 0.7));
  // furniture
  const desks = merge(A.furn.table.map(r => prism(r, H.deskTop - H.desk, H.deskTop)));
  add(mesh(desks, mat(C.desk)));
  add(lines(desks, C.deskEdge, 0.35));
  add(mesh(merge(A.furn.chair.map(r => prism(r, H.seat - H.seatH, H.seat))), mat(C.chair)));
  // plants: a pot and a few leafy blobs each, instanced
  const blob = new THREE.IcosahedronGeometry(1, 1), pot = new THREE.CylinderGeometry(0.5, 0.42, 1, 10);
  const leaves = new THREE.InstancedMesh(blob, mat(C.leaf, { flatShading: true }), A.plants.length * 3);
  const pots = new THREE.InstancedMesh(pot, mat(C.pot), A.plants.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), v = new THREE.Vector3();
  const tint = [new THREE.Color(C.leaf), new THREE.Color(C.leaf2), new THREE.Color('#6fa24f')];
  let rnd = 7; const rand = () => (rnd = (rnd * 16807) % 2147483647) / 2147483647;
  A.plants.forEach(([x, y, r], i) => {
    const rr = Math.min(0.9, r);
    pots.setMatrixAt(i, m4.compose(v.set(x, 0.22, y), q.identity(), s.set(rr * 0.7, 0.44, rr * 0.7)));
    for (let k = 0; k < 3; k++) {
      const a = rand() * Math.PI * 2, d = rr * 0.35 * rand();
      const sz = rr * (0.55 + 0.25 * rand());
      leaves.setMatrixAt(i * 3 + k, m4.compose(v.set(x + Math.cos(a) * d, 0.55 + rr * (0.35 + 0.5 * k / 2), y + Math.sin(a) * d), q.identity(), s.set(sz, sz * 0.9, sz)));
      leaves.setColorAt(i * 3 + k, tint[(i + k) % 3]);
    }
  });
  leaves.castShadow = pots.castShadow = true; leaves.receiveShadow = pots.receiveShadow = true;
  g.add(pots, leaves);
  return g;
}

function nbOf(A, pt) { for (const [k, r] of Object.entries(A.neigh)) if (inside(pt, r)) return k; return null; }

// the neighbourhoods as thin coloured plates, with the loop on top: the middle layer of the exploded view
function buildNbLayer(A) {
  const g = new THREE.Group();
  const add = o => o && g.add(o);
  for (const [k, r] of Object.entries(A.neigh)) {
    const geo = prism(r, 0, 0.12);
    add(mesh(geo, mat(new THREE.Color(NB_COLOR[k]).lerp(new THREE.Color('#ffffff'), 0.25), { transparent: true, opacity: 0.85 }), { shadow: false }));
    add(lines(geo, new THREE.Color(NB_COLOR[k]).multiplyScalar(0.7), 0.9));
  }
  add(mesh(merge(A.spaces.filter(s => s.k === 'corridor').map(s => prism(s.p, 0.12, 0.2))), mat(C.corridor), { shadow: false }));
  g.add(outline(A, '#8a8c93'));
  return g;
}
function outline(A, color) {     // the floor's edge as a line, so a floating layer still reads as the floor
  const ring = asRings(A.slab)[0].map(([x, y]) => new THREE.Vector3(x, 0, y));
  return new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(ring), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.7 }));
}

function buildStyle(A, style, { zones = true } = {}) {
  const g = new THREE.Group();
  const add = o => o && g.add(o);
  const nbTint = style === 'nb';
  const zoneY = { work: 0.004, collab: 0.008, coffee: 0.008, cafe: 0.008, reception: 0.008, entry: 0.02, corridor: 0.012 };
  const byColor = new Map();
  const put = (c, geo) => { if (!byColor.has(c)) byColor.set(c, []); byColor.get(c).push(geo); };
  if (zones) for (const s of A.spaces) if (s.g === 'zone') put(C[s.k] || C.work, flat(s.p, zoneY[s.k] || 0.006));
  if (nbTint) for (const [k, r] of Object.entries(A.neigh)) put('nb:' + k, flat(r, 0.009));
  // rooms: lavender floor and purple glass walls on the outline (neighbourhood colour in the colour view)
  const glassBy = new Map();
  for (const s of A.spaces) if (s.g === 'room') {
    const nb = nbTint ? nbOf(A, centroid(s.p)) : null;
    const key = nb || 'ref';
    put(nb ? 'room:' + nb : C.roomFloor, flat(s.p, 0.016));
    if (!glassBy.has(key)) glassBy.set(key, []);
    for (const [a, b] of edgesOf(s.p)) glassBy.get(key).push(bar(a, b, 0, H.wall, 0.05));
  }
  for (const [c, list] of byColor) {
    let m;
    if (c.startsWith('nb:')) m = new THREE.MeshLambertMaterial({ color: NB_COLOR[c.slice(3)], transparent: true, opacity: 0.38, depthWrite: false });
    else if (c.startsWith('room:')) m = mat(new THREE.Color(NB_COLOR[c.slice(5)]).lerp(new THREE.Color('#ffffff'), 0.45));
    else m = mat(c);
    add(mesh(merge(list), m, { shadow: false }));
  }
  for (const [k, list] of glassBy) {
    const geo = merge(list);
    const col = k === 'ref' ? C.glass : NB_COLOR[k];
    add(mesh(geo, new THREE.MeshLambertMaterial({ color: col, transparent: true, opacity: 0.42, depthWrite: false }), { shadow: false }));
    add(lines(geo, k === 'ref' ? C.glassEdge : new THREE.Color(col).multiplyScalar(0.6), 0.9));
  }
  return g;
}

// ---------- viewer ----------
export function createAxo(canvas, A, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: !!opts.still });
  renderer.setPixelRatio(opts.pixelRatio || Math.min(2, window.devicePixelRatio || 1));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd0d3d8, 1.75));   // three's lights are physical: these give a bright floor with soft shadows
  const sun = new THREE.DirectionalLight(0xffffff, 1.9);
  sun.castShadow = true; sun.shadow.mapSize.set(opts.shadowMap || 4096, opts.shadowMap || 4096);
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  scene.add(sun, sun.target);
  // exploded: shell and core at the base, the neighbourhoods above, the fit-out on top
  const EX = opts.exploded ? { shell: 0, nb: 15, fit: 30 } : null;
  const TOP = EX ? EX.fit + H.core : H.core;
  if (EX) {
    scene.add(buildShell(A));
    const nb = buildNbLayer(A); nb.position.y = EX.nb; scene.add(nb);
    const fit = new THREE.Group(); fit.add(buildFit(A), buildStyle(A, 'ref', { zones: false }), outline(A, '#8a8c93')); fit.position.y = EX.fit; scene.add(fit);
    for (const layer of [nb, fit]) layer.traverse(o => { o.castShadow = false; });   // no shadows thrown across the gaps
  } else scene.add(buildShell(A), buildFit(A));
  const styles = {}; let style = null;
  function setStyle(s) {
    if (EX) { style = s; return; }
    if (!styles[s]) { styles[s] = buildStyle(A, s); scene.add(styles[s]); }
    for (const k in styles) styles[k].visible = k === s;
    style = s; render();
  }
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 2000);
  const AZ = THREE.MathUtils.degToRad(opts.azimuth ?? (EX ? 16 : 45)), EL = THREE.MathUtils.degToRad(opts.elevation ?? (EX ? 26 : 35.264));   // exploded: more frontal, so the layers separate
  const DIR = new THREE.Vector3(-Math.sin(AZ) * Math.cos(EL), Math.sin(EL), Math.cos(AZ) * Math.cos(EL));
  let controls = null;
  if (opts.interactive) {
    controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true; controls.dampingFactor = 0.12; controls.screenSpacePanning = true;
    controls.rotateSpeed = 0.35; controls.minPolarAngle = THREE.MathUtils.degToRad(12); controls.maxPolarAngle = THREE.MathUtils.degToRad(72);
    controls.minZoom = 0.5; controls.maxZoom = 12;
    controls.addEventListener('change', () => { placeSun(); render(); });
  }
  function size() { const r = canvas.getBoundingClientRect(); return [Math.max(1, opts.width || r.width), Math.max(1, opts.height || r.height)]; }
  function placeSun() {
    const t = controls ? controls.target : camera.userData.target || new THREE.Vector3();
    sun.position.copy(t).add(new THREE.Vector3(-70, 110, 22));   // high, from the west: shadows fall east, behind things sun.target.position.copy(t);
    const span = (camera.right - camera.left) / camera.zoom * 0.62 + 10;
    Object.assign(sun.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 1, far: 400 });
    sun.shadow.camera.updateProjectionMatrix();
  }
  function setView(key, animate) {
    const [x0, x1, y0, y1] = (VIEWS[key] || VIEWS.floor).box;
    const [w, h] = size(); const aspect = w / h;
    const c = new THREE.Vector3((x0 + x1) / 2, 1, (y0 + y1) / 2);
    camera.position.copy(c).addScaledVector(DIR, 600); camera.up.set(0, 1, 0); camera.lookAt(c); camera.updateMatrixWorld();
    // fit the box's corners (floor to core height) in view space
    const inv = camera.matrixWorldInverse, P = new THREE.Vector3();
    let a = Infinity, b = -Infinity, d = Infinity, e = -Infinity;
    for (const x of [x0, x1]) for (const z of [y0, y1]) for (const y of [0, TOP]) {
      P.set(x, y, z).applyMatrix4(inv); a = Math.min(a, P.x); b = Math.max(b, P.x); d = Math.min(d, P.y); e = Math.max(e, P.y);
    }
    const m = opts.margin ?? 1.04;
    let hw = (b - a) / 2 * m, hh = (e - d) / 2 * m;
    if (hw / hh > aspect) hh = hw / aspect; else hw = hh * aspect;
    // slide the camera so the box's centre in view space sits in the middle of the frame
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0), upv = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    const target = c.clone().addScaledVector(right, (a + b) / 2).addScaledVector(upv, (d + e) / 2);
    camera.position.copy(target).addScaledVector(DIR, 600); camera.lookAt(target);
    Object.assign(camera, { left: -hw, right: hw, top: hh, bottom: -hh, zoom: 1 });
    camera.userData.target = target; camera.updateProjectionMatrix();
    if (controls) { controls.target.copy(target); controls.update(); }
    placeSun(); render();
  }
  function resize() {
    const [w, h] = size();
    renderer.setSize(w, h, false);
    const hh = (camera.top - camera.bottom) / 2;
    camera.left = -hh * w / h; camera.right = hh * w / h; camera.updateProjectionMatrix();
    render();
  }
  let raf = 0;
  function render() { if (raf) return; raf = requestAnimationFrame(() => { raf = 0; renderer.render(scene, camera); if (controls && controls.update()) render(); }); }
  function renderNow() { renderer.render(scene, camera); }
  // what is under the pointer: the space outline on the floor plane
  const ray = new THREE.Raycaster(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), hit = new THREE.Vector3();
  function pick(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2((clientX - r.left) / r.width * 2 - 1, -(clientY - r.top) / r.height * 2 + 1), camera);
    if (!ray.ray.intersectPlane(plane, hit)) return null;
    const pt = [hit.x, hit.z];
    const order = ['room', 'core', 'zone'];
    for (const g of order) {
      const cand = A.spaces.filter(s => s.g === g && s.k !== 'work' && inside(pt, s.p)).sort((p, q) => p.m2 - q.m2)[0];
      if (cand) return { kind: cand.k, name: NAMES[cand.k] || cand.k, m2: cand.m2, nb: NB_NAME[nbOf(A, pt)] || '' };
    }
    const nb = nbOf(A, pt);
    return nb ? { kind: 'work', name: NAMES.work, nb: NB_NAME[nb] } : null;
  }
  // where the exploded view's labels go, in canvas pixels: each layer at the floor's west tip, each neighbourhood at its centre
  function anchors() {
    if (!EX) return [];
    const [w, h] = size(), P = new THREE.Vector3();
    const px = (x, y, z) => { P.set(x, y, z).project(camera); return [(P.x + 1) / 2 * w, (1 - P.y) / 2 * h]; };
    const tip = asRings(A.slab)[0].reduce((m, p) => (px(p[0], 0, p[1])[0] < px(m[0], 0, m[1])[0] ? p : m));
    const out = [['fit', 'Fit-out'], ['nb', 'Neighbourhoods'], ['shell', 'Shell and core']].map(([k, t]) => ({ k, t, at: px(tip[0], EX[k], tip[1]) }));
    for (const [k, r] of Object.entries(A.neigh)) { const c = centroid(r); out.push({ k: 'nb:' + k, t: NB_NAME[k], at: px(c[0], EX.nb + 0.2, c[1]) }); }
    return out;
  }
  resize(); setStyle(opts.style || 'ref'); setView(opts.view || 'floor');
  return { setStyle, setView, resize, render, renderNow, pick, anchors, scene, camera, renderer, sun, get style() { return style; }, dispose: () => { controls && controls.dispose(); renderer.dispose(); } };
}
