// One-off: assets/img/ty-type2.webp, a white-background 3D view of one Type 2 workstation (two desks back to back, a chair on
// each side) made from the deck's SketchUp model, for the typologies' cards (beside ty-type1/3/4.webp).
//
//   NODE_PATH=C:/Users/Ritika/Mitigata/node_modules node tools/acko/render_ws_type.js        (Git Bash)
//   options: --at 131340,46651.3  a T2 placement's origin (plan mm, PLAN_DXF.types T2 uses; its desk spans x-600..x, y..y+1500)
//            --shift 450,224      the model minus the plan there (mm; measured: the model's desk top at that placement)
//            --view -0.8,0.97     the camera {theta, phi}, as AxoModel.basis   --size 1400x756   --out assets/img/ty-type2.webp
//
// Why built, not just cut: the plan's 2-seat T2 placements (and the model's) are two desks end to end with both chairs on one
// side; the back-to-back pair (the icon, and the plan's 6-seat T2 at 48015,38511) is not in the model. So: one desk with its
// chair is cut out of the model at --at (clipping planes), and drawn again mirrored about the desk's back edge.
// How: a page in the OS temp dir loads the deck's three.js and the model's data and code (as slides/_shell.html), builds
// AxoSkp.get() (world m: x east, y up, z south; plan mm -> M.X(x), M.Z(y), as slides/s-layout-sp.html), keeps the furniture,
// recolours the cut to the other renders' palette (white tops, lilac screens, dark mesh chairs, black legs), lights it with a
// tight soft sun over a white shadow-catcher floor, renders at 2x, screenshots; Python PIL downsizes and writes the webp.
// Needs Chrome (CHROME env var, else the default path) and puppeteer-core.
const path = require("path"), fs = require("fs"), os = require("os"), { execFileSync } = require("child_process");
const puppeteer = require("puppeteer-core");

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const nums = (k, d) => arg(k, d).split(",").map(Number);
const ROOT = path.resolve(__dirname, "..", ".."), url = (p) => "file:///" + path.join(ROOT, p).split(path.sep).join("/");
const AT = nums("--at", "131340,46651.3"), SHIFT = nums("--shift", "450,224"), VIEW = nums("--view", "-0.8,0.97");
const [W, H] = arg("--size", "1400x756").split("x").map(Number), OUT = path.resolve(ROOT, arg("--out", "assets/img/ty-type2.webp"));
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe", SS = 2;   // rendered at 2x, downsized

const LIBS = ["assets/vendor/three.min.js", "data/plan-dxf.js", "data/plan-base.js", "data/axo-dxf.js", "assets/js/axo-model.js", "data/axo-skp.js", "assets/js/axo-skp.js"];
const PAGE = `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;overflow:hidden;background:linear-gradient(#fefefe 35%,#f1f1f1)}canvas{display:block}</style>
${LIBS.map((p) => `<script src="${url(p)}"></script>`).join("\n")}
<script>
window.renderType2 = function (at, shift, view) {
  const T = THREE, M = AxoSkp.get((p) => p), r = AxoModel.renderer();
  document.body.appendChild(r.domElement); r.setSize(innerWidth, innerHeight);
  M.reset(); AxoSkp.look("sketchup");
  for (const k in M.groups) M.groups[k].visible = k === "furniture";
  M.scene.updateMatrixWorld(true);
  // the cut (model m): the desk east of the chair, from its back edge xe to past the chair, one desk long (the south one); the
  // chair (SketchUp has it pushed in, its arms through the top) pulled PULL m back from the desk, as the other renders have them
  const PULL = 0.22, xe = M.X(at[0] + shift[0]), z0 = M.Z(at[1] + shift[1]) - 0.002, z1 = z0 + 1.56, x0 = xe - 1.25 - PULL, LID = 1.6;
  const cut = (a, b) => [new T.Plane(new T.Vector3(1, 0, 0), -a), new T.Plane(new T.Vector3(-1, 0, 0), b), new T.Plane(new T.Vector3(0, 0, 1), -z0),
    new T.Plane(new T.Vector3(0, 0, -1), z1), new T.Plane(new T.Vector3(0, 1, 0), -0.003), new T.Plane(new T.Vector3(0, -1, 0), LID)];
  // the meshes in the cut (any instance's box touching it)
  const box = new T.Box3(new T.Vector3(x0 + PULL, 0, z0), new T.Vector3(xe, LID, z1)), inCut = [], at4 = new Map(), m4 = new T.Matrix4();
  M.groups.furniture.traverse((o) => {
    if (!o.isMesh) return; const g = o.geometry; if (!g.boundingBox) g.computeBoundingBox();
    const n = o.isInstancedMesh ? o.count : 1;
    for (let i = 0; i < n; i++) { if (o.isInstancedMesh) { o.getMatrixAt(i, m4); m4.premultiply(o.matrixWorld); } else m4.copy(o.matrixWorld);
      if (Math.abs(m4.determinant()) > 1e-12 && g.boundingBox.clone().applyMatrix4(m4).intersectsBox(box)) { inCut.push(o); at4.set(o, m4.clone()); break; } }
  });
  // the fine level of detail only (the model's own switch, run once for a close view, then off), and only what is in the cut
  M.scene.onBeforeRender(r, M.scene, { top: 1 }); M.scene.onBeforeRender = () => {};
  M.groups.furniture.traverse((o) => { if (o.isMesh || o.isLine) o.visible = o.visible && inCut.includes(o); });
  inCut.splice(0, inCut.length, ...inCut.filter((o) => o.visible));
  // the palette of ty-type1/3/4 over SketchUp's colours (by colour; the chairs' grey split at the seat: mesh above, base below);
  // the chair's vertices (its greys, its soft part) moved PULL m west, in the component's own frame
  const RE = { "193,170,147": [246, 246, 244], "169,169,169": [162, 139, 156], "86,86,86": [38, 38, 40], "122,122,122": [62, 62, 66], "193,193,193": [70, 70, 74] };
  const done = new Set();
  for (const o of inCut) {
    const g = o.geometry, c = g.getAttribute("color"), p = g.getAttribute("position"); if (!c || done.has(g)) continue; done.add(g);
    const y0 = g.boundingBox.min.y, soft = o.material.userData.kind === "soft";
    const back = new T.Vector3(-PULL, 0, 0).applyMatrix3(new T.Matrix3().setFromMatrix4(at4.get(o).clone().invert()));
    for (let i = 0; i < c.count; i++) {
      const key = [c.getX(i), c.getY(i), c.getZ(i)].map((q) => Math.round(q * 255)).join(",");
      if (soft || key === "147,147,147" || key === "122,122,122") p.setXYZ(i, p.getX(i) + back.x, p.getY(i) + back.y, p.getZ(i) + back.z);
      let to = RE[key];
      if (key === "147,147,147") to = p.getY(i) - y0 < 0.33 ? [150, 150, 155] : [84, 84, 88];
      if (to) c.setXYZ(i, to[0] / 255, to[1] / 255, to[2] / 255);
    }
    c.needsUpdate = p.needsUpdate = true; g.computeBoundingBox(); g.computeBoundingSphere();
  }
  // the clip on the cut's own materials; then each mesh again, mirrored about x = xe (the desks' shared back edge), on a copy
  // of its material clipped to the mirrored box
  const planes = cut(x0, xe), mats = new Map(), mir = new T.Matrix4().makeTranslation(2 * xe, 0, 0).multiply(new T.Matrix4().makeScale(-1, 1, 1));
  for (const o of inCut) {
    const m = o.material; m.clippingPlanes = planes; m.clipShadows = true; m.needsUpdate = true;
    if (!mats.has(m)) { const mm = m.clone(); mm.clippingPlanes = cut(xe, 2 * xe - x0); mm.clipShadows = true; mats.set(m, mm); }
    const twin = o.clone(); twin.material = mats.get(m); twin.matrixAutoUpdate = false; twin.matrix.copy(mir).multiply(o.matrixWorld);
    twin.castShadow = o.castShadow = true; twin.receiveShadow = o.receiveShadow = true; M.scene.add(twin);
  }
  r.localClippingEnabled = true;
  // a floor that only catches the shadows (the clear is transparent: the page's near-white gradient is the ground, as the others')
  const cx = xe, cz = (z0 + z1) / 2, floor = new T.Mesh(new T.PlaneGeometry(40, 40), new T.ShadowMaterial({ opacity: 0.13 }));
  floor.rotation.x = -Math.PI / 2; floor.position.set(cx, 0.001, cz); floor.receiveShadow = true; M.scene.add(floor);
  // the light: the look's sky, brighter; its sun high in the north-west, its soft (VSM) shadow camera tight round the desks
  let sun = null, hemi = null; M.scene.traverse((o) => { if (o.isDirectionalLight) sun = o; if (o.isHemisphereLight) hemi = o; });
  const d = new T.Vector3(-0.35, 2.2, -0.25).normalize();
  sun.target.position.set(cx, 0, cz); sun.target.updateMatrixWorld(); sun.position.set(cx + d.x * 30, d.y * 30, cz + d.z * 30);
  sun.intensity = 0.5; sun.castShadow = true; hemi.intensity = 0.98; hemi.color.setHex(0xffffff); hemi.groundColor.setHex(0xdedde4);
  const sc = sun.shadow.camera; sc.left = sc.bottom = -3.5; sc.right = sc.top = 3.5; sc.near = 1; sc.far = 80; sc.updateProjectionMatrix();
  sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 14; sun.shadow.blurSamples = 24; sun.shadow.bias = -0.0002; sun.shadow.normalBias = 0.008;
  if (sun.shadow.map) { sun.shadow.map.dispose(); sun.shadow.map = null; }
  r.shadowMap.type = T.VSMShadowMap; r.shadowMap.needsUpdate = true;
  // the camera: an orthographic axo at {theta, phi}, framed on both desks and chairs (floor to the screens' tops), centred
  const cam = new T.OrthographicCamera(-1, 1, 1, -1, 1, 900), asp = innerWidth / innerHeight, c = new T.Vector3(cx, 0.55, cz);
  const st = { theta: view[0], phi: view[1], t: [c.x, c.y, c.z], half: 1 }, B = AxoModel.basis(st);
  let r0 = 1e9, r1 = -1e9, u0 = 1e9, u1 = -1e9;
  for (const x of [x0, 2 * xe - x0]) for (const z of [z0, z1]) for (const y of [0, 1.14]) {
    const v = new T.Vector3(x, y, z).sub(c), a = v.dot(B.right), b = v.dot(B.up);
    r0 = Math.min(r0, a); r1 = Math.max(r1, a); u0 = Math.min(u0, b); u1 = Math.max(u1, b); }
  c.add(B.right.clone().multiplyScalar((r0 + r1) / 2)).add(B.up.clone().multiplyScalar((u0 + u1) / 2));
  st.t = [c.x, c.y, c.z]; st.half = Math.max((u1 - u0) / 2 / 1.12, (r1 - r0) / 2 / asp);   // (the box corners overshoot the desks: ~80% of the height, as ty-type3)
  AxoModel.apply(cam, st, asp);
  r.setClearColor(0xffffff, 0); r.render(M.scene, cam);
  return inCut.length;
};
</script>`;

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "acko-ws-")), html = path.join(dir, "page.html"), png = path.join(dir, "shot.png");
  fs.writeFileSync(html, PAGE);
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--allow-file-access-from-files"], defaultViewport: { width: W, height: H, deviceScaleFactor: SS } });
  const page = await browser.newPage();
  page.on("pageerror", (e) => console.error("page:", e.message));
  page.on("console", (m) => { if (m.type() === "error") console.error("console:", m.text()); });
  await page.goto("file:///" + html.split(path.sep).join("/"), { waitUntil: "load", timeout: 300000 });
  console.log("meshes in the cut:", await page.evaluate((a, s, v) => window.renderType2(a, s, v), AT, SHIFT, VIEW));
  await page.screenshot({ path: png });
  await browser.close();
  execFileSync(process.env.PYTHON || "python", ["-c", "import sys; from PIL import Image; im = Image.open(sys.argv[1]).convert('RGB'); " +
    "im.resize((int(sys.argv[3]), int(sys.argv[4])), Image.LANCZOS).save(sys.argv[2], 'WEBP', quality=85, method=6)", png, OUT, String(W), String(H)], { stdio: "inherit" });
  fs.rmSync(dir, { recursive: true, force: true });
  console.log("wrote", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
