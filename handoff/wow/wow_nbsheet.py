# Each neighbourhood on its own (Ritika, 10 Nov, from a "Neighbourhoods · 1 of 6" sheet): six beats after the Neighbourhoods overview
# on s-layout-sp, 01 Auto … 06 Home, each its PLAN (the shared plan framed on it, the rest veiled) beside its AXONOMETRIC (the furnished
# SketchUp model clipped to it), its panel below (name, seats, key plan, occupancy, n of 6).
# Run after gen_floorflow.py, wow_sundd.py and wow_people.py: python wow_nbsheet.py <deck-wow checkout>
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
OLD_ROUTE = '[1, 2, 3, 4, 5, 6].indexOf(g) + 1'
NEW_ROUTE = '[1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6].indexOf(g) + 1'      # the layers' first beats, the six sheets after Neighbourhoods
p = "slides/s-layout-dd.html"; s, nl = rd(p)
if OLD_ROUTE in s: s = sub1(s, OLD_ROUTE, NEW_ROUTE, "dd route"); wr(p, s, nl)
p = "slides/s-layout-sp.html"; s, nl = rd(p)
if "nb-sheet" in s:
    print("already"); sys.exit()
s = sub1(s, OLD_ROUTE, NEW_ROUTE, "sp route")
s = sub1(s, 'data-steps="6"', 'data-steps="12"', "steps")
# the neighbourhoods by number only (11 Nov, Ritika: "remove the terms life, auto, drive and only have neighbourhood 01, 02")
s = sub1(s, 'data-beats="Spaces,Neighbourhoods,', 'data-beats="Spaces,Neighbourhoods,Neighbourhood 01,Neighbourhood 02,Neighbourhood 03,Neighbourhood 04,Neighbourhood 05,Neighbourhood 06,', "beats")
s = s.replace('data-notes="', 'data-notes="Neighbourhoods one by one (beats 3–8: neighbourhoods 01 to 06): each its plan with its rooms, beside its model turning slowly, cut to it; its workstations, meeting rooms, phone booths and wellness rooms counted; hover a dot to name a room. ', 1)
s = sub1(s, "const ORDER = [1, 2, 3, 4, 5, 6];", "const ORDER = [1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6], SHEET = [null, null, \"01\", \"02\", \"03\", \"04\", \"05\", \"06\", null, null, null, null];", "order")
s = sub1(s, '    <div class="ly-top"></div>\n', '''    <div class="ly-top"></div>
    <!-- the neighbourhood sheets (10 Nov): its plan (the shared plan, framed on it, left) beside its axonometric (right) -->
    <div class="nb-3d" aria-hidden="true" style="left:50.78%;top:14.54%;width:47.4%;height:47.5%"></div>
    <div class="nb-lab" style="left:1.8%;top:12.2%;width:30%">Plan</div>
    <div class="nb-lab ax" style="left:50.78%;top:12.2%;width:30%">Axonometric</div>
    <!-- template D (10 Nov): the neighbourhood's card under its small plan, the axo large beside -->
    <div class="nb-card" style="left:1.8%;top:43.5%;width:31.5%;height:18.5%"><small class="nbk"></small><h2 class="nbn"></h2><p class="nbs"></p><div class="nbc"></div></div>
    <!-- template E (10 Nov, Ritika's reference sheet): the column, the plan card with its numbered rooms; the axo card is .nb-3d -->
    <div class="nbe" style="left:0;top:0;width:100%;height:100%">
      <div class="nbe-plan" style="left:26.6%;top:12.5%;width:35.4%;height:76%"><b class="nbe-l">Plan</b></div>
      <div class="nbe-pm" style="left:0;top:0;width:100%;height:100%"></div>
      <div class="nbe-col" style="left:1.8%;top:12.5%;width:23.4%;height:76%">
        <small class="nbe-k"></small><div class="nbe-kp"></div><div class="nbe-chips"></div><h2 class="nbe-n"></h2><p class="nbe-s"></p>
        <div class="nbe-cnt"></div><p class="nbe-hint">Hover a dot on the plan or the model to see what it is · scroll the model to zoom</p>
      </div>
    </div>
''', "markup")
# templates B, C (10 Nov): the panel shows four counts in place of the occupancy table
s = sub1(s, '<div class="zone"><div class="kp">', '<div class="zone"><div class="nbc"></div><div class="kp">', "zone counts")
s = sub1(s, "</style>", '''/* the neighbourhood sheets (10 Nov) */
#s-layout-sp .nb-3d { background: #fff; border-left: 1px solid #ece8f6; opacity: 0; visibility: hidden; transition: opacity .6s var(--ease), visibility 0s linear .6s; pointer-events: none; }
#s-layout-sp .nb-3d canvas { display: block; width: 100%; height: 100%; }
#s-layout-sp.nb-sheet .nb-3d { opacity: 1; visibility: visible; transition: opacity .6s var(--ease) .2s, visibility 0s; }
#s-layout-sp .nb-lab { font-size: calc(var(--pt) * 6.5); font-weight: 600; letter-spacing: .2em; text-transform: uppercase; color: #8a83a3; opacity: 0; transition: opacity .5s var(--ease); pointer-events: none; z-index: 3; }
#s-layout-sp.nb-sheet .nb-lab { opacity: 1; }
/* the sheet's templates (10 Nov, Ritika: "the current one is too cluttered"; window.ACKO_NB on the option pages): A as built;
   B the axo across the whole plan area, below it the name, four counts and a small key plan; C plan | axo, below only the name and the
   counts; D the axo large on the right, on the left the neighbourhood's plan small with its card under it */
#s-layout-sp .nbc, #s-layout-sp .nb-card { display: none; }
#s-layout-sp .nbc > div { display: flex; flex-direction: column; }
#s-layout-sp .nbc b { font-family: var(--num); font-weight: 300; font-size: calc(var(--pt) * 24); line-height: 1; color: var(--purple); }
#s-layout-sp .nbc span { margin-top: calc(var(--pt) * 2); font-size: calc(var(--pt) * 6.2); letter-spacing: .03em; color: var(--soft); }
#s-layout-sp.nb-sheet:is([data-nbv="b"], [data-nbv="c"]) .ly-p.zoned .zone { display: flex; align-items: center; gap: 6%; }
#s-layout-sp.nb-sheet:is([data-nbv="b"], [data-nbv="c"]) .ly-p.zoned .occ { display: none; }
#s-layout-sp.nb-sheet:is([data-nbv="b"], [data-nbv="c"]) .ly-p.zoned .nbc { display: flex; gap: calc(var(--pt) * 22); }
#s-layout-sp.nb-sheet[data-nbv="b"] .ly-p.zoned .kp { width: 26%; margin-left: auto; }
#s-layout-sp.nb-sheet[data-nbv="c"] .ly-p.zoned .kp { display: none; }
#s-layout-sp.nb-sheet[data-nbv="b"] .nb-3d { left: 0 !important; width: 100% !important; border-left: 0; }
#s-layout-sp.nb-sheet[data-nbv="b"] .nb-lab { display: none; }
#s-layout-sp.nb-sheet[data-nbv="d"] .nb-3d { left: 35.5% !important; width: 62.7% !important; }
#s-layout-sp.nb-sheet[data-nbv="d"] .nb-lab.ax { left: 35.5% !important; }
#s-layout-sp.nb-sheet[data-nbv="d"] .ly-p[data-p="2"] { opacity: 0 !important; visibility: hidden !important; }
#s-layout-sp.nb-sheet[data-nbv="d"] .nb-card { display: block; z-index: 3; background: #fff; padding-top: calc(var(--pt) * 4); }
#s-layout-sp .nb-card small { display: block; font-family: var(--num); font-weight: 300; font-size: calc(var(--pt) * 7); color: var(--violet); }
#s-layout-sp .nb-card h2 { margin: calc(var(--pt) * 1) 0 calc(var(--pt) * 2); font-size: calc(var(--pt) * 14); font-weight: 600; color: var(--purple-2); }
#s-layout-sp .nb-card p { margin: 0 0 calc(var(--pt) * 5); font-size: calc(var(--pt) * 6.4); color: var(--soft); }
#s-layout-sp .nb-card p b { color: var(--ink); }
#s-layout-sp.nb-sheet[data-nbv="d"] .nb-card .nbc { display: grid; grid-template-columns: repeat(4, auto); justify-content: start; gap: calc(var(--pt) * 14); }
#s-layout-sp .nb-card .nbc b { font-size: calc(var(--pt) * 18); }
/* template E (10 Nov, Ritika's reference: "the template can be like this itself, and the axo can slowly rotate"): a column, a plan card
   with numbered rooms, an axo card turning slowly with numbered pins; the deck's own light page */
#s-layout-sp .nbe, #s-layout-sp .nbe-ap, #s-layout-sp .nbe-axl { display: none; }
#s-layout-sp .nbe > * { position: absolute; }
#s-layout-sp.nb-sheet[data-nbv="e"] .nbe { display: block; z-index: 2; pointer-events: none; }
#s-layout-sp.nb-sheet[data-nbv="e"] :is(.hdr, .ly-tools, .ly-pills) { z-index: 4; }
#s-layout-sp.nb-sheet[data-nbv="e"] :is(.ly-p[data-p="2"], .nb-lab, .ly-north, .ly-bot) { opacity: 0 !important; visibility: hidden !important; }
#s-layout-sp.nb-sheet[data-nbv="e"] .ly-pills { top: 90.6% !important; }
#s-layout-sp .nbe-plan { border: 1px solid #e3def2; border-radius: calc(var(--pt) * 6); box-shadow: 0 0 0 4000px #fff; }
#s-layout-sp .nbe-l, #s-layout-sp .nbe-axl { position: absolute; left: calc(var(--pt) * 8); top: calc(var(--pt) * 7); font-size: calc(var(--pt) * 6); font-weight: 600; letter-spacing: .22em; text-transform: uppercase; color: #8a83a3; }
#s-layout-sp.nb-sheet[data-nbv="e"] .nb-3d { left: 63.6% !important; top: 12.5% !important; width: 34.6% !important; height: 76% !important; z-index: 3;
  border: 1px solid #e3def2 !important; border-radius: calc(var(--pt) * 6); overflow: hidden; }
#s-layout-sp.nb-sheet[data-nbv="e"] :is(.nbe-ap, .nbe-axl) { display: block; }
#s-layout-sp .nbe-ap { position: absolute; inset: 0; pointer-events: none; }
#s-layout-sp .nbe-col { display: flex; flex-direction: column; background: #fff; }
#s-layout-sp .nbe-k { font-family: var(--num); font-size: calc(var(--pt) * 6.4); letter-spacing: .18em; text-transform: uppercase; color: var(--violet); }
#s-layout-sp .nbe-kp { margin: calc(var(--pt) * 5) 0 calc(var(--pt) * 5); width: 92%; }
#s-layout-sp .nbe-kp svg { width: 100%; height: auto; display: block; }
#s-layout-sp .nbe-n { margin: 0; font-size: calc(var(--pt) * 17); line-height: 1.05; white-space: nowrap; font-weight: 700; color: var(--purple); }
#s-layout-sp .nbe-s { margin: calc(var(--pt) * 3) 0 0; font-size: calc(var(--pt) * 6.6); font-weight: 600; color: var(--ink); }
/* 11 Nov ("a lot of text"; "hover to see what it is"; "the axo should be zoomable"; "click and select neighbourhoods"): the big counts,
   the neighbourhoods as chips, the rooms as unnumbered dots that name themselves on hover */
#s-layout-sp .nbe-chips { display: flex; flex-wrap: nowrap; gap: calc(var(--pt) * 2.4); margin: 0 0 calc(var(--pt) * 8); pointer-events: auto; }
#s-layout-sp .nbe-chips button { display: inline-flex; align-items: center; gap: calc(var(--pt) * 2.5); border: 1px solid #ddd6f2; background: #fff; color: var(--ink);
  border-radius: 999px; padding: calc(var(--pt) * 1.8) calc(var(--pt) * 3.8); font: 600 calc(var(--pt) * 6) / 1.1 var(--num, inherit); cursor: pointer; transition: background .2s, color .2s, border-color .2s; }
#s-layout-sp .nbe-chips button::before { content: ""; width: calc(var(--pt) * 4.5); height: calc(var(--pt) * 4.5); border-radius: 50%; background: var(--c); }
#s-layout-sp .nbe-chips button:hover { border-color: var(--purple); }
#s-layout-sp .nbe-chips button.on { background: var(--purple); border-color: var(--purple); color: #fff; }
#s-layout-sp .nbe-kp { pointer-events: auto; }
#s-layout-sp .nbe-kp path { cursor: pointer; }
#s-layout-sp .nbe-cnt { display: grid; grid-template-columns: 1fr 1fr; gap: calc(var(--pt) * 10) calc(var(--pt) * 8); margin-top: calc(var(--pt) * 10); }
#s-layout-sp .nbe-cnt > div { border-top: 2px solid var(--purple); padding-top: calc(var(--pt) * 3); }
#s-layout-sp .nbe-cnt b { display: block; font-family: var(--num); font-weight: 600; font-size: calc(var(--pt) * 24); line-height: 1.05; color: var(--ink); }
#s-layout-sp .nbe-cnt small { display: flex; align-items: center; gap: calc(var(--pt) * 2.5); font-size: calc(var(--pt) * 5.4); letter-spacing: .14em; text-transform: uppercase; color: var(--mute); }
#s-layout-sp .nbe-cnt small::before { content: ""; width: calc(var(--pt) * 4.5); height: calc(var(--pt) * 4.5); border-radius: 50%; background: var(--k); }
#s-layout-sp .nbe-hint { margin: auto 0 0; font-size: calc(var(--pt) * 5.4); color: var(--mute); }
#s-layout-sp :is(.nbe-pm, .nbe-ap) i { display: block; width: calc(var(--pt) * 7); height: calc(var(--pt) * 7); border-radius: 50%; background: var(--k); font-style: normal;
  box-shadow: 0 0 0 calc(var(--pt) * 1.4) #fff, 0 1px 4px rgba(0, 0, 0, .25); pointer-events: auto; cursor: default; position: relative; transition: transform .15s; }
#s-layout-sp .nbe-pm i { position: absolute; transform: translate(-50%, -50%); }
#s-layout-sp .nbe-pm i:hover { transform: translate(-50%, -50%) scale(1.35); z-index: 2; }
#s-layout-sp .nbe-ap .pin i:hover { transform: scale(1.35); z-index: 2; }
#s-layout-sp :is(.nbe-pm, .nbe-ap) i:hover::after { content: attr(data-t); position: absolute; left: 50%; bottom: calc(100% + 6px); transform: translateX(-50%); white-space: nowrap;
  background: #1d1733; color: #fff; font: 500 calc(var(--pt) * 5.6) / 1.2 var(--body, inherit); padding: calc(var(--pt) * 2) calc(var(--pt) * 4); border-radius: calc(var(--pt) * 2); pointer-events: none; }
#s-layout-sp .nbe-pm i:hover::after { transform: translateX(-50%) scale(.74); transform-origin: 50% 100%; }
#s-layout-sp .nbe-ap .pin i:hover::after { transform: translateX(-50%) scale(.74); transform-origin: 50% 100%; }
#s-layout-sp .nbe-ap .pin { position: absolute; display: flex; flex-direction: column; align-items: center; transform: translate(-50%, -100%); }
#s-layout-sp .nbe-ap .pin::after { content: ""; width: 1px; height: calc(var(--pt) * 13); background: var(--k); opacity: .7; }
#s-layout-sp.nb-sheet[data-nbv="e"] .nb-3d { pointer-events: auto; cursor: grab; }
#s-layout-sp.nb-sheet[data-nbv="e"] .nb-3d.drag { cursor: grabbing; }
/* 11 Nov ("don't color the workstations here"): the people's coloured seats stay on Spaces and Neighbourhoods, not on the sheets */
#s-layout-sp.nb-sheet[data-nbv="e"] .ly-ppl { opacity: 0 !important; }
</style>''', "style")
SHEETS = r'''  // ---- the neighbourhood sheets (10 Nov, Ritika: "the axo and layout for neighbourhoods individually in this slide"): beats 3–8, one
  // neighbourhood each. The plan: the shared plan framed on it in the left half (plan.focusZone, the rest veiled; the people stay on its
  // desks). The axo: the furnished SketchUp model (AxoSkp, the plan's own mm frame) cut to the neighbourhood's box by four vertical
  // clipping planes, its purples kept in its outline (AxoSkp.focus), A day in ACKO's angle, framed on the box; from one sheet to the next
  // the camera and the cut ease together. Leaving the sheets clears the cut and the focus (the model is shared)
  // the neighbourhoods by number only on this deck (11 Nov): "Neighbourhood 01" … wherever a slide shows a zone's name
  if (window.ACKO_WOW && window.PLAN_DXF) (window.PLAN_DXF.zones || []).forEach((q) => { q.name = "Neighbourhood " + q.n; });
  const LEFT = [35, 157, 945, 670], NB = { theta: -0.62, phi: 0.92 };
  const NBX = { M: null, cam: null, planes: null, mats: [], cur: null, raf: 0, on: false };
  const nbZone = (n) => (plan.data.zones || []).find((q) => q.n === n);
  function nbBox(z) { const M = NBX.M, b = z.box, pad = 1500; return [M.X(b[0] - pad), M.Z(b[1] - pad), M.X(b[2] + pad), M.Z(b[3] + pad)]; }
  function nbFit(bx, asp) {                                // the box (world m) seen from NB's angle, fitted to the cell
    const T3 = window.THREE, s0 = { theta: NB.theta, phi: NB.phi, t: [0, 0, 0], half: 1 }, B = window.AxoModel.basis(s0), c = new T3.Vector3((bx[0] + bx[2]) / 2, 1.2, (bx[1] + bx[3]) / 2);
    let r0 = 1e9, r1 = -1e9, u0 = 1e9, u1 = -1e9;
    for (const x of [bx[0], bx[2]]) for (const z of [bx[1], bx[3]]) for (const y of [0, 3.6]) {
      const v = new T3.Vector3(x, y, z).sub(c), r = v.dot(B.right), u = v.dot(B.up); r0 = Math.min(r0, r); r1 = Math.max(r1, r); u0 = Math.min(u0, u); u1 = Math.max(u1, u); }
    const t = c.clone().add(B.right.clone().multiplyScalar((r0 + r1) / 2)).add(B.up.clone().multiplyScalar((u0 + u1) / 2));
    return { theta: NB.theta, phi: NB.phi, t: [t.x, t.y, t.z], half: Math.max((u1 - u0) / 2, (r1 - r0) / 2 / asp) * 1.08 };
  }
  function nbClip(on) {                                    // the cut on every material of the model, or off again
    const M = NBX.M, T3 = window.THREE; if (!M) return;
    if (on && !NBX.planes) {
      NBX.planes = [new T3.Plane(new T3.Vector3(1, 0, 0), 0), new T3.Plane(new T3.Vector3(-1, 0, 0), 0), new T3.Plane(new T3.Vector3(0, 0, 1), 0), new T3.Plane(new T3.Vector3(0, 0, -1), 0)];
      NBX.mats = []; M.scene.traverse((o) => { if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { if (!NBX.mats.includes(m)) NBX.mats.push(m); }); });
      NBX.mats.forEach((m) => { m.clippingPlanes = NBX.planes; m.needsUpdate = true; });
      window.AxoModel.renderer().localClippingEnabled = true;
    } else if (!on && NBX.planes) {
      NBX.mats.forEach((m) => { m.clippingPlanes = null; m.needsUpdate = true; }); NBX.planes = null; NBX.mats = [];
    }
  }
  function nbSet(bx) { const P = NBX.planes; if (!P) return; P[0].constant = -bx[0]; P[1].constant = bx[2]; P[2].constant = -bx[1]; P[3].constant = bx[3]; }
  function nbDraw(sc, st, bx) {
    const r = window.AxoModel.renderer(), host = $(".nb-3d", sc);
    if (r.domElement.parentNode !== host) host.appendChild(r.domElement);
    const W = host.clientWidth, H = host.clientHeight; if (!W || !H) return;
    const pr = r.getPixelRatio(); if (r.domElement.width !== Math.round(W * pr) || r.domElement.height !== Math.round(H * pr)) r.setSize(W, H, false);
    nbSet(bx); window.AxoModel.apply(NBX.cam, sc.dataset.nbv === "e" ? nbView(st) : st, W / H); r.render(NBX.M.scene, NBX.cam);
    if (sc.dataset.nbv === "e") { nbPins(sc, W, H); nbMarks(sc); }
  }
  // ---- template E (10 Nov): each occupancy item on its room, numbered in the list, on the plan and on the axo
  const nbIn = (p, r) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const a = r[i], b = r[j];
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
  const GRP = { "Workhall": "Work", "Meeting room": "Meet", "Recreational area / wellness": "Wellness", "Services": "Services" };
  function nbItems(z) {
    const R = rings(z.zone), inZ = (s) => R.filter((r) => nbIn([s.x, s.y], r)).length % 2 === 1;
    const SP = (plan.data.spaces || []).filter(inZ), used = new Set();
    const norm = (t) => t.toLowerCase().replace(/['’]/g, "").replace(/\s+-\s+.*$/, "").replace(/\bthe\b/g, "").replace(/\b(rooms?|cabins?)\b/g, "").replace(/s\b/g, "").trim();
    return (z.occ || []).map(([g, a, n], i) => {
      let at = null;
      if (/workstation/i.test(a)) { const w = SP.find((s) => /workhall/i.test(s.type)); at = w ? [w.x, w.y] : [z.x, z.y]; }
      else {
        const key = norm(a), pax = (a.match(/(\d+)(?:-\d+)?\s*pax/i) || [])[1];
        const cand = SP.filter((s) => !used.has(s) && (() => { const t = norm(s.type || s.name); return t && (t.includes(key) || key.includes(t)); })());
        const best = (pax && cand.find((s) => new RegExp("\\b0?" + +pax + "\\s*PAX", "i").test(s.name))) || cand[0];
        if (best) { used.add(best); at = [best.x, best.y]; }
      }
      return { i: i + 1, g: GRP[g] || g, a: a.replace(/(\d)-(\d)/g, "$1–$2"), n, at };
    });
  }
  const NBKC = { Work: "#5222d0", Meet: "#9a79f2", Wellness: "#2f9e6a", Services: "#8f8a9e" };   // the dots' colours, by kind
  function nbE(sc, z, i) {
    const items = (NBX.items = nbItems(z)), o = z.occ || [], sum = (f) => o.filter(f).reduce((a, r) => a + r[2], 0);
    const meet = sum((r) => r[0] === "Meeting room" && !/phone booth/i.test(r[1])), pb = sum((r) => /phone booth/i.test(r[1])), well = sum((r) => /wellness/i.test(r[0]));
    const goTo = (n) => go(sceneIx("s-layout-sp"), 2 + (+n));
    $(".nbe-k", sc).textContent = `05 · Neighbourhoods · ${i} of 6`;
    const kp = $(".nbe-kp", sc); kp.innerHTML = plan.keyplan(z.id);
    const ZS = plan.data.zones || [], cols = $$("path", kp).map((p) => p.style.getPropertyValue("--c"));
    $$("path", kp).forEach((p, j) => { if (ZS[j]) p.onclick = () => goTo(ZS[j].n); });
    const chips = $(".nbe-chips", sc);
    chips.innerHTML = ZS.map((q, j) => `<button type="button" data-n="${q.n}" class="${q.n === z.n ? "on" : ""}" style="--c:${cols[j] || "#ccc"}">${q.n}</button>`).join("");
    $$("button", chips).forEach((b) => (b.onclick = (e) => { e.stopPropagation(); b.blur(); if (b.dataset.n !== z.n) goTo(b.dataset.n); }));
    $(".nbe-n", sc).textContent = `Neighbourhood ${z.n}`;
    $(".nbe-s", sc).textContent = `${Math.round(z.m2)} m²`;
    $(".nbe-cnt", sc).innerHTML = [[z.seats, "Workstations", NBKC.Work], [meet, "Meeting rooms", NBKC.Meet], [pb, "Phone booths", "#c2b0f6"], [well, "Wellness", NBKC.Wellness]]
      .map(([v, t, k]) => `<div style="--k:${k}"><b>${v}</b><small>${t}</small></div>`).join("");
    const tip = (t) => nbEsc(t.a + (/workstation/i.test(t.a) ? ` · ${t.n}` : t.n > 1 ? ` × ${t.n}` : ""));
    $(".nbe-pm", sc).innerHTML = items.filter((t) => t.at).map((t) => `<i data-i="${t.i}" data-t="${tip(t)}" style="--k:${NBKC[t.g] || NBKC.Services}"></i>`).join("");
    const host = $(".nb-3d", sc);
    if (!$(".nbe-ap", host)) host.insertAdjacentHTML("beforeend", '<b class="nbe-axl">Axonometric</b><div class="nbe-ap"></div>');
    $(".nbe-ap", host).innerHTML = items.filter((t) => t.at).map((t) => `<div class="pin" data-i="${t.i}" style="--k:${NBKC[t.g] || NBKC.Services}"><i data-t="${tip(t)}" style="--k:${NBKC[t.g] || NBKC.Services}"></i></div>`).join("");
    nbZoomWire(sc, host);
  }
  const nbEsc = (s) => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
  // the axo, zoomable (11 Nov): the wheel zooms, a drag pans, a double-click resets; the slow turn carries on
  function nbView(st) {
    const zf = NBX.zf || 1, pn = NBX.pan || [0, 0]; if (zf === 1 && !pn[0] && !pn[1]) return st;
    const B = window.AxoModel.basis(st), t = new window.THREE.Vector3(...st.t).add(B.right.clone().multiplyScalar(pn[0])).add(B.up.clone().multiplyScalar(pn[1]));
    return { ...st, t: [t.x, t.y, t.z], half: st.half / zf };
  }
  function nbZoomWire(sc, host) {
    if (host._nbz) return; host._nbz = true;
    const redraw = () => { if (reduced && NBX.on && NBX.cur) nbDraw(sc, NBX.cur.st, NBX.cur.bx); };
    host.addEventListener("wheel", (e) => { if (sc.dataset.nbv !== "e" || !NBX.on) return; e.preventDefault(); e.stopPropagation();
      NBX.zf = Math.min(2.5, Math.max(0.6, (NBX.zf || 1) * Math.exp(-e.deltaY * 0.0015))); redraw(); }, { passive: false });
    let d = null;
    host.addEventListener("pointerdown", (e) => { if (sc.dataset.nbv !== "e" || !NBX.on || e.button !== 0) return; e.stopPropagation();
      d = { x: e.clientX, y: e.clientY, p: (NBX.pan || [0, 0]).slice() }; host.classList.add("drag"); host.setPointerCapture(e.pointerId); });
    host.addEventListener("pointermove", (e) => { if (!d || !NBX.cur) return; const k = (2 * NBX.cur.st.half / (NBX.zf || 1)) / (host.clientHeight || 1);
      NBX.pan = [d.p[0] - (e.clientX - d.x) * k, d.p[1] + (e.clientY - d.y) * k]; redraw(); });
    const up = () => { d = null; host.classList.remove("drag"); };
    host.addEventListener("pointerup", up); host.addEventListener("pointercancel", up);
    host.addEventListener("click", (e) => e.stopPropagation());
    host.addEventListener("dblclick", (e) => { e.stopPropagation(); NBX.zf = 1; NBX.pan = [0, 0]; redraw(); });
  }
  function nbMarks(sc) {                                     // the plan's numbers, where the plan now shows their rooms
    const v = plan.view, root = plan.root, pg = $(".page", sc).getBoundingClientRect(); if (!v || !root || !NBX.items) return;
    const r = root.getBoundingClientRect(), k = Math.max(v[2] / r.width, v[3] / r.height);
    const map = new Map(NBX.items.map((t) => [String(t.i), t]));
    $$(".nbe-pm i", sc).forEach((e) => { const t = map.get(e.dataset.i); if (!t || !t.at) return;
      const x = r.left + r.width / 2 + (t.at[0] - (v[0] + v[2] / 2)) / k, y = r.top + r.height / 2 + (t.at[1] - (v[1] + v[3] / 2)) / k;
      e.style.left = ((x - pg.left) / pg.width * 100).toFixed(3) + "%"; e.style.top = ((y - pg.top) / pg.height * 100).toFixed(3) + "%"; });
  }
  function nbPins(sc, W, H) {                                // the axo's numbers, on their rooms, turning with the model
    const T3 = window.THREE, M = NBX.M; if (!NBX.items) return;
    const map = new Map(NBX.items.map((t) => [String(t.i), t]));
    $$(".nbe-ap .pin", sc).forEach((e) => { const t = map.get(e.dataset.i); if (!t || !t.at) return;
      const p = new T3.Vector3(M.X(t.at[0]), 1.2, M.Z(t.at[1])).project(NBX.cam);
      e.style.left = ((p.x + 1) / 2 * W).toFixed(1) + "px"; e.style.top = ((1 - p.y) / 2 * H).toFixed(1) + "px"; });
  }
  function nbSpinFit(bx, asp) {                              // a frame that holds the cut at every angle of the turn
    const T3 = window.THREE, c = new T3.Vector3((bx[0] + bx[2]) / 2, 1.8, (bx[1] + bx[3]) / 2); let half = 0;
    for (let a = 0; a < 12; a++) {
      const B = window.AxoModel.basis({ theta: NB.theta + (a / 12) * Math.PI * 2, phi: NB.phi, t: [0, 0, 0], half: 1 }); let r0 = 1e9, r1 = -1e9, u0 = 1e9, u1 = -1e9;
      for (const x of [bx[0], bx[2]]) for (const z of [bx[1], bx[3]]) for (const y of [0, 3.6]) {
        const v = new T3.Vector3(x, y, z).sub(c), r = v.dot(B.right), u = v.dot(B.up); r0 = Math.min(r0, r); r1 = Math.max(r1, r); u0 = Math.min(u0, u); u1 = Math.max(u1, u); }
      half = Math.max(half, (u1 - u0) / 2, (r1 - r0) / 2 / asp);
    }
    return { theta: NB.theta, phi: NB.phi, t: [c.x, c.y, c.z], half: half * 1.12 };
  }
  const SPIN = 90000;                                        // a full turn in 90 s
  function nbPanel(sc, z, i) {
    const p = $('.ly-p[data-p="2"]', sc); p.classList.add("zoned");
    $(".ly-p[data-p=\"2\"] .lead small", sc).textContent = `03 · ${i} of 6`;
    $(".nb-h", sc).textContent = z.name; $(".nb-p", sc).innerHTML = `<b>${z.seats}</b> workstations · <b>${Math.round(z.m2)}</b> m²`;
    $(".kp-in", sc).innerHTML = plan.keyplan(z.id);
    // the four counts (templates B, C, D): the occupancy summed
    const o = z.occ || [], sum = (f) => o.filter(f).reduce((a, r) => a + r[2], 0);
    const C = [[z.seats, "Workstations"], [sum((r) => r[0] === "Meeting room" && !/phone booth/i.test(r[1])), "Meeting rooms"],
      [sum((r) => /phone booth/i.test(r[1])), "Phone booths"], [sum((r) => /wellness/i.test(r[0])), "Wellness"]];
    $$(".nbc", sc).forEach((e) => (e.innerHTML = C.map(([v, t]) => `<div><b>${v}</b><span>${t}</span></div>`).join("")));
    $(".nbk", sc).textContent = `03 · ${i} of 6`; $(".nbn", sc).textContent = z.name;
    $(".nbs", sc).innerHTML = `<b>${z.seats}</b> workstations · <b>${Math.round(z.m2)}</b> m²`;
    let g = ""; $(".occ", sc).innerHTML = (z.occ || []).map(([grp, a, n]) => (grp !== g ? `<div class="g">${(g = grp)}</div>` : "") + `<div><span>${a.replace(/(\d)-(\d)/g, "$1–$2")}</span><span>${n}</span></div>`).join("");
  }
  function sheet(sc, n) {
    const z = n && nbZone(n); NBX.z = z || null;                // the open neighbourhood, for the occupancy chart
    if (!z) {                                             // off: the overview, another layer, or leaving
      if (!NBX.on) return; NBX.on = false; cancelAnimationFrame(NBX.raf);
      sc.classList.remove("nb-sheet"); nbClip(false); if (window.AxoSkp && window.AxoSkp.focus) window.AxoSkp.focus(null);
      $(".ly-p[data-p=\"2\"] .lead small", sc).textContent = "03"; $('.ly-p[data-p="2"]', sc).classList.remove("zoned");
      plan.focusZone(null); return;
    }
    const V = window.ACKO_NB || "a"; sc.dataset.nbv = V;                     // the template (option pages set it)
    plan.focusZone(z.id, V === "d" ? [35, 157, 640, 455] : V === "e" ? [531, 185, 1171, 936] : LEFT); nbPanel(sc, z, +n);
    if (V === "e") { NBX.zf = 1; NBX.pan = [0, 0]; nbE(sc, z, +n); }
    sc.classList.add("nb-sheet");
    if (!(window.AxoSkp && window.AxoSkp.available())) return;
    if (!NBX.M) { NBX.M = window.AxoSkp.get(asset); NBX.cam = new window.THREE.OrthographicCamera(-1, 1, 1, -1, 1, 900); }
    if (!NBX.M) return;
    const host = $(".nb-3d", sc), asp = (host.clientWidth || 910) / (host.clientHeight || 513), bx = nbBox(z), E = V === "e", to = E ? nbSpinFit(bx, asp) : nbFit(bx, asp);
    if (!NBX.on) { NBX.on = true; NBX.M.reset(); window.AxoSkp.look("sketchup"); nbClip(true); NBX.cur = { st: to, bx }; }
    window.AxoSkp.focus(rings(z.zone));
    const from = NBX.cur, t0 = performance.now(), MS = 900, ease = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
    let dth = to.theta - from.st.theta; dth = Math.atan2(Math.sin(dth), Math.cos(dth));   // E: back to the turn's start the short way round
    cancelAnimationFrame(NBX.raf);
    // E: once landed, the model turns slowly (a full turn in SPIN ms), the pins and the plan's numbers following
    const spin = (s0) => (now) => {
      if (!NBX.on || document.body.dataset.scene !== sc.id || sc.dataset.nbv !== "e") return;
      const st = { ...to, theta: to.theta + ((now - s0) / SPIN) * Math.PI * 2 }; NBX.cur = { st, bx }; nbDraw(sc, st, bx);
      NBX.raf = requestAnimationFrame(spin(s0));
    };
    const tick = (now) => {
      if (!NBX.on || document.body.dataset.scene !== sc.id) return;
      const k = Math.min(1, (now - t0) / MS), e = ease(k), L = (a, b) => a + (b - a) * e;
      const st = { theta: E ? from.st.theta + dth * e : to.theta, phi: to.phi, t: from.st.t.map((v, i) => L(v, to.t[i])), half: L(from.st.half, to.half) }, b = from.bx.map((v, i) => L(v, bx[i]));
      NBX.cur = { st, bx: b }; nbDraw(sc, st, b);
      if (k < 1) NBX.raf = requestAnimationFrame(tick);
      else { NBX.M.reset(); if (E && !reduced) NBX.raf = requestAnimationFrame(spin(performance.now())); else later(() => { if (NBX.on) nbDraw(sc, NBX.cur.st, NBX.cur.bx); }, 60); }   // the shadows redrawn with the cut
    };
    NBX.raf = requestAnimationFrame(tick);
    later(() => { if (NBX.on && NBX.cur && !(E && !reduced)) { NBX.cur = { st: to, bx }; nbDraw(sc, to, bx); } }, MS + 200);      // lands even without frames (E turns on)
  }
'''
s = sub1(s, "  return self = {\n", SHEETS + "  return self = {\n", "fns")
# the occupancy chart on a sheet (11 Nov, Ritika: "in occupancy chart, have neighbourhood's occupancy"): that neighbourhood's rows, its
# rooms picked out on the plan; off the sheets, the floor's chart as before
NBCHART = r'''  function nbChart(sc, z) {
    const R = rings(z.zone), inZ = (s) => R.filter((r) => inRing([s.x, s.y], r)).length % 2 === 1;
    const SP = plan.data.spaces.filter((s) => s.type !== "Not in contract" && inZ(s));
    const rows = (z.occ || []).map(([grp, area, n], i) => { const m = MATCH.find(([re]) => re.test(area));
      return { i, grp, area: area.replace(/(\d)-(\d)/g, "$1–$2"), n, ws: /^Workstations/i.test(area), spaces: m ? SP.filter((s) => m[1](s.name, s.type)) : [] }; });
    OCC = rows; sel = -1; sc._nbChart = true;
    const groups = []; rows.forEach((r) => { const g = groups[groups.length - 1]; if (g && g[0] === r.grp) g[1].push(r); else groups.push([r.grp, [r]]); });
    $(".ly-fo-l", sc).innerHTML = `<table class="occ-t"><thead><tr><th>Zone</th><th>Area</th><th>Count</th></tr></thead><tbody>` +
      groups.map(([g, list]) => list.map((r, i) => `<tr data-i="${r.i}" class="${i === 0 ? "g0" : ""}${r.ws ? " ws" : ""}">` + (i === 0 ? `<td class="grp" rowspan="${list.length}">${g}</td>` : "") +
        `<td>${r.area}</td><td class="n">${r.n}</td></tr>`).join("")).join("") + "</tbody></table>";
    const o = z.occ || [], sum = (f) => o.filter(f).reduce((a, r) => a + r[2], 0);
    $(".ly-fo-h b", sc).textContent = `${z.name} · Occupancy`;
    $(".ly-fo-sum", sc).innerHTML = `<b>${z.seats}</b> workstations · <b>${sum((r) => r[0] === "Meeting room" && !/phone booth/i.test(r[1]))}</b> meeting rooms · ` +
      `<b>${sum((r) => /phone booth/i.test(r[1]))}</b> phone booths · <b>${sum((r) => /wellness/i.test(r[0]))}</b> wellness`;
    $(".ly-fo-r", sc).innerHTML = `<p class="occ-key">${z.name}, ${Math.round(z.m2)} m². Click a row to find its rooms on the plan, or a room to find its row.</p>`;
    $$(".ly-fo tr[data-i]", sc).forEach((tr) => (tr.onclick = () => pickRow(sc, +tr.dataset.i)));
  }
'''
s = sub1(s, '  function floorChart(sc) {\n    if ($(".ly-fo .occ-t", sc)) return;\n',
    NBCHART + '  function floorChart(sc) {\n'
    '    if (NBX.on && NBX.z) { nbChart(sc, NBX.z); return; }              // on a sheet: the neighbourhood\'s chart (11 Nov)\n'
    '    if (sc._nbChart) { sc._nbChart = false; $(".ly-fo-l", sc).innerHTML = ""; $(".ly-fo-h b", sc).textContent = "Occupancy"; }\n'
    '    if ($(".ly-fo .occ-t", sc)) return;\n', "floor chart")
# step: after the plan is homed, the sheet for this beat (or none)
s = sub1(s, "      ppl(sc, k === 1 || k === 2, k === 1);", "      sheet(sc, SHEET[n - 1]);                           // beats 3–8: a neighbourhood on its own\n      ppl(sc, k === 1 || k === 2, k === 1);", "step hook")
# a click on a neighbourhood: on a sheet, that neighbourhood's sheet
s = sub1(s, "plan.onZoneClick((z) => { if (beat === 2) {", "plan.onZoneClick((z) => { if (beat === 2 && NBX.on) { go(sceneIx(\"s-layout-sp\"), 2 + (+z.n)); return; } if (beat === 2) {", "zone click")
# the back button: on a sheet, back to the overview
s = sub1(s, '    $(".ly-back", sc).onclick = () => closeZone(sc);', '    $(".ly-back", sc).onclick = () => { if (NBX.on) go(sceneIx("s-layout-sp"), 2); else closeZone(sc); };', "back")
s = sub1(s, "      plan.planOff(); cancelAnimationFrame(PPL.raf);", "      sheet(sc, null); plan.planOff(); cancelAnimationFrame(PPL.raf);", "leave")
# ---- Biophilia · Views to green, four more ways (11 Nov, Ritika: "views to green can come as an illustration instead of showing it on
# layout, can also be a text; show me different variations"): window.ACKO_BIO picks one (the option pages set it); A, the sight
# lines on the plan, stays the deck's until she picks. Each covers the plan area; the figures come live from L.bioStats
BV_SVG = '''<svg class="bv-sec" viewBox="0 0 1200 430" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
          <defs><clipPath id="bv-clip"><rect class="bv-cr" x="0" y="0" width="1200" height="430"/></clipPath></defs>
          <line class="fl" x1="40" y1="360" x2="1160" y2="360"/>
          <g transform="translate(-140 0)"><path class="ln" d="M380 282H580M398 282V360M562 282V360"/><path class="ln" d="M470 282L488 262H540L532 282"/>
          <path class="ln" d="M268 300H338M282 300V360M330 300V360M268 300V240"/>
          <circle class="ln" cx="322" cy="198" r="20"/><path class="ln" d="M318 220L310 296H372L372 360M312 240L378 268"/></g>
          <g transform="translate(-316 0)"><path class="pot" d="M872 300H948L938 360H882Z"/>
          <path class="pl" d="M910 300C900 260 870 240 850 236C872 252 884 276 896 300ZM910 300C912 250 904 214 890 196C918 218 926 262 918 300ZM910 300C928 262 948 246 972 240C952 258 936 280 922 300ZM906 300C892 284 866 280 846 284C866 292 884 298 900 304Z"/></g>
          <g clip-path="url(#bv-clip)"><path class="eye" d="M200 196L594 238"/><circle class="tgt" cx="594" cy="238" r="7"/></g>
          <path class="dim" d="M200 392H594M200 382V402M594 382V402"/><text class="dt" x="397" y="422" text-anchor="middle"><tspan class="bv-med">3.5 m</tspan> · median</text>
          <path class="dim faint" d="M200 66H1100M200 56V76M1100 56V76"/><text class="dt faint" x="650" y="48" text-anchor="middle">8 m · a plant in view within this</text>
        </svg>'''
s = sub1(s, "    <!-- 03 · biophilia: 1 the heat", '''    <!-- Biophilia · Views to green, the variations (11 Nov): B the number, C a section, D 100 seats, E a render -->
    <div class="bv" style="left:1.8%;top:14.5%;width:96.4%;height:47.6%">
      <div class="bv-b"><b class="bv-big"></b><div><p class="bv-l">of the seats have a plant in view within 8&nbsp;m</p><p class="bv-s"></p><p class="bv-h hand">A glance at green, all day.</p></div></div>
      <div class="bv-c">''' + BV_SVG + '''<div class="bv-ct"><b class="bv-pc"></b><span>of the seats see a plant within 8&nbsp;m</span></div></div>
      <div class="bv-d"><div class="bv-grid"></div><div class="bv-dt"><b class="bv-pc"></b><p>of the seats see a plant within 8&nbsp;m: <span class="bv-dn"></span> in every 100</p><p class="bv-s"></p></div></div>
      <div class="bv-e"><div class="bv-et"><p class="bv-eh">From <b class="bv-pc"></b> of the desks, green is a glance away.</p><p class="bv-s"></p></div></div>
    </div>
    <!-- 03 · biophilia: 1 the heat''', "bv markup")
s = sub1(s, "</style>", '''/* Biophilia · Views to green, the variations (11 Nov) */
#s-layout-sp .bv { display: none; background: #fff; z-index: 2; overflow: hidden; }
#s-layout-sp:is([data-bv="b"], [data-bv="c"], [data-bv="d"], [data-bv="e"]) .bv { display: block; }
#s-layout-sp .bv > div { position: absolute; inset: 0; display: none; }
#s-layout-sp[data-bv="b"] .bv-b { display: flex; align-items: center; justify-content: center; gap: calc(var(--pt) * 26); }
#s-layout-sp[data-bv="c"] .bv-c, #s-layout-sp[data-bv="d"] .bv-d { display: flex; align-items: center; justify-content: center; gap: calc(var(--pt) * 26); }
#s-layout-sp[data-bv="e"] .bv-e { display: block; background: url(assets/img/r3-garden.webp) center / cover no-repeat; }
#s-layout-sp .bv-big { font-family: var(--num); font-weight: 300; font-size: calc(var(--pt) * 110); line-height: .9; color: var(--purple); }
#s-layout-sp .bv-l { margin: 0; max-width: calc(var(--pt) * 220); font-size: calc(var(--pt) * 15); line-height: 1.25; color: var(--ink); }
#s-layout-sp .bv-s { margin: calc(var(--pt) * 6) 0 0; font-size: calc(var(--pt) * 7.4); letter-spacing: .02em; color: var(--mute); }
#s-layout-sp .bv-h { margin: calc(var(--pt) * 10) 0 0; font-size: calc(var(--pt) * 20); color: #2f9e6a; }
#s-layout-sp .bv-b > *, #s-layout-sp .bv-ct, #s-layout-sp .bv-dt, #s-layout-sp .bv-et { opacity: 0; transform: translateY(8px); transition: opacity .7s var(--ease), transform .7s var(--ease); }
#s-layout-sp .bv.go .bv-b > *, #s-layout-sp .bv.go :is(.bv-ct, .bv-dt, .bv-et) { opacity: 1; transform: none; }
#s-layout-sp .bv.go .bv-b > div { transition-delay: .25s; }
#s-layout-sp .bv-sec { position: absolute; left: 22%; top: 4%; width: 74%; height: 92%; }
#s-layout-sp .bv-sec .fl { stroke: #d9d2ee; stroke-width: 3; }
#s-layout-sp .bv-sec .ln { fill: none; stroke: #3d2a8a; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; }
#s-layout-sp .bv-sec circle.ln { fill: #fff; }
#s-layout-sp .bv-sec .pot { fill: #d8cbbb; } #s-layout-sp .bv-sec .pl { fill: #3f9a5f; }
#s-layout-sp .bv-sec .eye { fill: none; stroke: #5222d0; stroke-width: 3; stroke-dasharray: 12 9; }
#s-layout-sp .bv-sec .tgt { fill: #5222d0; }
#s-layout-sp .bv-sec .bv-cr { transform-origin: 200px 0; transform: scaleX(0); transition: transform 1.8s cubic-bezier(.65, 0, .35, 1) .3s; }
#s-layout-sp .bv.go .bv-sec .bv-cr { transform: none; }
#s-layout-sp .bv-sec .dim { fill: none; stroke: #5222d0; stroke-width: 2; } #s-layout-sp .bv-sec .dim.faint { stroke: #c9bdf0; }
#s-layout-sp .bv-sec .dt { font: 600 22px var(--body, sans-serif); fill: #3d2a8a; } #s-layout-sp .bv-sec .dt.faint { fill: #9a90b8; font-weight: 500; }
#s-layout-sp .bv-ct { position: absolute; left: 3%; top: 12%; width: 22%; }
#s-layout-sp .bv-ct b, #s-layout-sp .bv-dt b { display: block; font-family: var(--num); font-weight: 300; font-size: calc(var(--pt) * 52); line-height: 1; color: var(--purple); }
#s-layout-sp .bv-ct span, #s-layout-sp .bv-dt p:first-of-type { display: block; margin: calc(var(--pt) * 4) 0 0; font-size: calc(var(--pt) * 10); line-height: 1.3; color: var(--ink); }
#s-layout-sp .bv-grid { display: grid; grid-template-columns: repeat(10, calc(var(--pt) * 12)); gap: calc(var(--pt) * 4); }
#s-layout-sp .bv-grid i { width: calc(var(--pt) * 12); height: calc(var(--pt) * 12); border-radius: 50%; background: #e7e3f0; transition: background .35s var(--ease); transition-delay: calc(var(--d) * 14ms); }
#s-layout-sp .bv.go .bv-grid i.on { background: #3f9a5f; }
#s-layout-sp .bv-dt { max-width: calc(var(--pt) * 200); }
#s-layout-sp .bv-et { position: absolute; left: 0; top: 0; bottom: 0; width: 46%; padding: 0 calc(var(--pt) * 16); display: flex; flex-direction: column; justify-content: center;
  background: linear-gradient(90deg, #fff 58%, rgba(255, 255, 255, 0)); }
#s-layout-sp .bv-eh { margin: 0; max-width: calc(var(--pt) * 190); font-size: calc(var(--pt) * 18); line-height: 1.22; color: var(--ink); }
#s-layout-sp .bv-eh b { color: var(--purple); font-weight: 700; }
#s-layout-sp:is([data-bv="b"], [data-bv="c"], [data-bv="d"], [data-bv="e"]) .bio > div:is(:has(.sw.seat), :has(.sw.view)),
#s-layout-sp:is([data-bv="b"], [data-bv="c"], [data-bv="d"], [data-bv="e"]) .bio-p p.concept[data-b="3"] { display: none; }
</style>''', "bv style")
s = sub1(s, '      if (layer === "bio" && L) {\n', '      sc.dataset.bv = "";                                // Biophilia · Views to green, the variations (11 Nov)\n      if (layer === "bio" && L) {\n', "bv clear")
s = sub1(s, "        $(\".b-vwp\", sc).innerHTML = `of the seats have a plant in view within 8 m · median <b>${st.median.toFixed(1)} m</b>`;\n",
    "        $(\".b-vwp\", sc).innerHTML = `of the seats have a plant in view within 8 m · median <b>${st.median.toFixed(1)} m</b>`;\n"
    "        const BV = window.ACKO_BIO || \"a\";\n"
    "        if (b === 3 && BV !== \"a\") {\n"
    "          const bvo = $(\".bv\", sc), pc = Math.round(st.views), m = st.median.toFixed(1);\n"
    "          sc.dataset.bv = BV; bvo.classList.remove(\"go\");\n"
    "          $(\".bv-big\", sc).textContent = pc + \"%\"; $$(\".bv-pc\", sc).forEach((e) => (e.textContent = pc + \"%\")); $(\".bv-dn\", sc).textContent = pc;\n"
    "          $$(\".bv-s\", sc).forEach((e) => (e.textContent = `median ${m} m · ${st.plants} plants · ${st.seats} seats`)); $(\".bv-med\", sc).textContent = m + \" m\";\n"
    "          $(\".bv-grid\", sc).innerHTML = Array.from({ length: 100 }, (_, i) => `<i class=\"${i < pc ? \"on\" : \"\"}\" style=\"--d:${i}\"></i>`).join(\"\");\n"
    "          void bvo.offsetWidth; later(() => bvo.classList.add(\"go\"), 120);\n"
    "        }\n", "bv fill")
wr(p, s, nl)
print("ok nbsheet")
