# D · the building assembles: s-strategy beat 1, only on a page with window.ACKO_WOW (the re-ordered deck); the live deck as before
# run: python wow_build.py <deck-wow checkout>     (idempotent)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
os.chdir(sys.argv[1])
p = "slides/s-strategy.html"; s, nl = rd(p)
def sub1(s, a, b, what):
    assert s.count(a) == 1, (what, s.count(a)); return s.replace(a, b)
if "WAVE" not in s:
    s = sub1(s, 'ACKO.slide("s-strategy", ({ $, $$, reduced, plain, reveal }) => {', 'ACKO.slide("s-strategy", ({ $, $$, reduced, plain, reveal, cue }) => {', "factory")
    s = sub1(s, "  const DUR = [0, 2.4, 4.4, 6.4, 2.4, 4.2, 7.0];",
        "  const DUR = [0, 2.4, 4.4, 6.4, 2.4, 4.2, 7.0];\n"
        "  // the building assembles (9 Nov, the re-ordered deck only, window.ACKO_WOW): on beat 1 the core and columns come up in a wave from\n"
        "  // the west end to the east, the façade following them, then the entrances drop in: a clipping plane on each group's materials\n"
        "  // sweeping along x (world m, the slab −122.5…122.5), set far off (nothing cut) on every other beat and on leaving\n"
        "  const WAVE = !!window.ACKO_WOW, W_MASS = [0.1, 1.9], W_FAC = [0.7, 2.7], W_ENT = [2.6, 3.2];\n"
        "  if (WAVE) DUR[1] = 3.4;\n"
        "  let CLIP = null;\n"
        "  function clip(sxM, sxF) {                         // keep x ≤ sx (world m); 1e6: keep all\n"
        "    if (!WAVE) return;\n"
        "    if (!CLIP) {\n"
        "      const T3 = window.THREE; CLIP = { m: new T3.Plane(new T3.Vector3(-1, 0, 0), 1e6), f: new T3.Plane(new T3.Vector3(-1, 0, 0), 1e6) };\n"
        "      const put = (g, pl) => g.traverse((o) => { if (!o.material) return; (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.clippingPlanes = [pl]; m.needsUpdate = true; }); });\n"
        "      put(M.groups.mass, CLIP.m); put(M.groups.facade, CLIP.f);\n"
        "      r.localClippingEnabled = true;\n"
        "    }\n"
        "    CLIP.m.constant = sxM; CLIP.f.constant = sxF;\n"
        "  }\n"
        "  const sweep = (t, w) => { const e = win(t, w[0], w[1]); return e >= 1 ? 1e6 : -126 + 252 * e; };", "consts")
    s = sub1(s, "    for (const g of SHELL) grow(G[g], k === 1 ? win(t, 0.1, 1.5) : 1);",
        "    for (const g of SHELL) grow(G[g], k === 1 && !WAVE ? win(t, 0.1, 1.5) : 1);\n"
        "    if (WAVE) clip(k === 1 ? sweep(t, W_MASS) : 1e6, k === 1 ? sweep(t, W_FAC) : 1e6);", "pose shell")
    s = sub1(s, "    S.ent = k === 1 ? win(t, 1.4, 2.0) : 1;", "    S.ent = k === 1 ? (WAVE ? win(t, W_ENT[0], W_ENT[1]) : win(t, 1.4, 2.0)) : 1;", "pose ent")
    s = sub1(s, "  function play(k) {\n", "  function play(k) {\n    if (WAVE && k === 1 && !reduced) cue(\"swell\");\n", "play cue")
    s = sub1(s, "      cancelAnimationFrame(S.raf); S.raf = 0; S.playing = false;\n", "      cancelAnimationFrame(S.raf); S.raf = 0; S.playing = false; if (CLIP) clip(1e6, 1e6);\n", "leave")
    wr(p, s, nl)
print("ok build")
