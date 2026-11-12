# index-loopclose.html: "The Loop, on the floor" (s-loop-w beat 3) with its two loose ends closed, two ways (11 Nov, Ritika drew a hook
# at Collab and at Work: "close the loop"; asked how: "build both to compare").
#   1 · s-loopc-1 One closed loop: out west to east as now, a U-turn at Work (down and under, her hook), back just beside itself, a
#       U-turn up into the start at Collab: one ring through all seven stops, no ends, no taper
#   2 · s-loopc-2 Only the end hooks: the one path, each end curling round (as drawn) back into the ribbon
# The slides are s-loop-w with a CLOSE mode: wbuild's floor path B passes through closeLoop(), the Loop's line A is resampled to the
# same count so the morph still runs point for point, and rib() draws a ring without taper. s-loop-w itself is untouched.
#   python tools/acko/story/gen_loopclose.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

HELPER = r'''
  // closing the Loop on the floor (11 Nov, Ritika: "close the loop"): mode "ring" (out, U-turn at Work, back beside itself, U-turn
  // at Collab) or "hooks" (each end curls round, back into the ribbon). Page px in, page px out; the "down" side is the path's left
  // normal, which points down the page as it runs west to east (where her hooks are drawn)
  const CLOSE = "__MODE__";
  function closeLoop(B, mode) {
    const n = B.length, nrm = B.map((p, i) => { const a = B[Math.max(0, i - 1)], b = B[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [-dy / l, dx / l]; });
    const tan = (i) => [nrm[i][1], -nrm[i][0]];
    const smooth = (P, it) => { for (let k = 0; k < it; k++) for (let i = 1; i < P.length - 1; i++) P[i] = [0, 1].map((c) => (P[i - 1][c] + 2 * P[i][c] + P[i + 1][c]) / 4); return P; };
    if (mode === "ring") {
      const OFF = 34;
      const back = smooth(B.map((p, i) => [p[0] + nrm[i][0] * OFF, p[1] + nrm[i][1] * OFF]), 14);
      const uturn = (P, Q, t) => {                      // a half circle from P round to Q, bulging along t
        const c = [(P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2], r = Math.hypot(Q[0] - P[0], Q[1] - P[1]) / 2 || 1, v = [(P[0] - c[0]) / r, (P[1] - c[1]) / r], out = [];
        for (let k = 1; k < 16; k++) { const a = (Math.PI * k) / 16; out.push([c[0] + (v[0] * Math.cos(a) + t[0] * Math.sin(a)) * r, c[1] + (v[1] * Math.cos(a) + t[1] * Math.sin(a)) * r]); }
        return out;
      };
      const t0 = tan(0), tn = tan(n - 1);
      return B.concat(uturn(B[n - 1], back[n - 1], tn), back.slice().reverse(), uturn(back[0], B[0], [-t0[0], -t0[1]]), [B[0].slice()]);
    }
    // hooks, as she drew them: from the end's dot the ribbon drops below itself, swings round inward (toward the rest of the path)
    // and comes back up into the ribbon, a curl of ~300° on a circle beside and under the end
    // then (11 Nov, "blend it together", her red marks): the curl turns back after ~220°, runs into the ribbon along the ribbon's own
    // direction at her mark (back px in from the end), and carries on exactly along the ribbon's points, where its tip tapers out of sight
    const R = 42, hook = (P, back) => {                 // the hook at P's last point
      const m = P.length, E = P[m - 1], d2 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
      const nv = (i) => { const a = P[Math.max(0, i - 1)], b = P[Math.min(m - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; };
      const tE = nv(m - 1), tin = [-tE[0], -tE[1]];
      let dn = [-tE[1], tE[0]]; if (dn[1] < 0) dn = [-dn[0], -dn[1]];     // the side below the ribbon
      const C = [E[0] + tin[0] * R * 0.85 + dn[0] * R * 0.5, E[1] + tin[1] * R * 0.85 + dn[1] * R * 0.5], r = d2(E, C), f0 = Math.atan2(E[1] - C[1], E[0] - C[0]);
      const s = Math.sign(dn[0] * -Math.sin(f0) + dn[1] * Math.cos(f0)) || 1, out = [], SW = 220 * Math.PI / 180;   // leaving the dot downward
      for (let k = 1; k <= 28; k++) { const f = f0 + s * (k / 28) * SW; out.push([C[0] + r * Math.cos(f), C[1] + r * Math.sin(f)]); }
      let j = m - 1, acc = 0; while (j > 2 && acc < back) { acc += d2(P[j], P[j - 1]); j--; }
      const A = out[out.length - 1], fa = f0 + s * SW, ta = [-Math.sin(fa) * s, Math.cos(fa) * s], Q = P[j];
      const tq = (() => { const a = P[j + 1], b = P[j - 1], l = d2(a, b) || 1; return [(b[0] - a[0]) / l, (b[1] - a[1]) / l]; })();   // along the ribbon, back toward its start
      const dd = d2(A, Q) / 2.4, c1 = [A[0] + ta[0] * dd, A[1] + ta[1] * dd], c2 = [Q[0] - tq[0] * dd, Q[1] - tq[1] * dd];
      for (let k = 1; k <= 20; k++) { const t = k / 20, v = 1 - t; out.push([0, 1].map((c) => v * v * v * A[c] + 3 * v * v * t * c1[c] + 3 * v * t * t * c2[c] + t * t * t * Q[c])); }
      for (let i = j - 1, a2 = 0; i > 0 && a2 < 60; i--) { a2 += d2(P[i], P[i + 1]); out.push(P[i].slice()); }
      return out;
    };
    return hook(B.slice().reverse(), 90).reverse().concat(B, hook(B, 70));
  }
'''

src = open("tools/acko/story/loop_w_base.html", encoding="utf-8").read()   # s-loop-w as it was before the hooks went in (11 Nov), the template
A_OLD = "const A = resample(T.pts.slice(Math.ceil(40 / 6), T.pts.length - Math.ceil(40 / 6)), N3), B = resample(window.ACKO_LOOP_SMOOTH(LP).map((q) => P(q[0], q[1])), N3);"
A_NEW = ("const B = resample(closeLoop(resample(window.ACKO_LOOP_SMOOTH(LP).map((q) => P(q[0], q[1])), N3), CLOSE), 640), "
         "A = resample(T.pts.slice(Math.ceil(40 / 6), T.pts.length - Math.ceil(40 / 6)), B.length);")
U_OLD = "const u = Math.min(1, Math.min(ss[i], L - ss[i]) / TAP)"
U_NEW = "const u = CLOSE === \"ring\" ? 1 : Math.min(1, Math.min(ss[i], L - ss[i]) / (CLOSE === \"hooks\" ? 40 : TAP))"   # the hooks keep their width; only their tips taper
H_AT = "  function wbuild(sc) {"
for s, n in ((A_OLD, 1), (U_OLD, 1), (H_AT, 1)):
    assert src.count(s) == n, s[:60]

OPTS = [(1, "ring", "One closed loop"), (2, "hooks", "Only the end hooks")]
PICK = "hooks"
for n, mode, name in OPTS:
    sid = "s-loopc-%d" % n
    t = src.replace(A_OLD, A_NEW).replace(U_OLD, U_NEW).replace(H_AT, HELPER.replace("__MODE__", mode) + H_AT)
    t = t.replace("s-loop-w", sid)
    t = t.replace("assets/img/" + sid, "assets/img/s-loop-w").replace("assets/img/s-loop/", "assets/img/s-loop/")
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(t)
    print("ok", sid)
    if mode == PICK:                                 # the deck's own slide gets the picked closing (Ritika, 11 Nov: hooks, "yes, put it in")
        open("slides/s-loop-w.html", "w", encoding="utf-8", newline="\n").write(t.replace(sid, "s-loop-w")); print("ok s-loop-w =", sid)

ORDER = ["s-loop-w"] + ["s-loopc-%d" % n for n, _, _ in OPTS]
LAB = {"s-loop-w": "0 · In the deck (Close · 2)"}; LAB.update({"s-loopc-%d" % n: "Close · %d · %s" % (n, name) for n, _, name in OPTS})
OUT = "index-loopclose.html"
build.build(ORDER, OUT)
h = open(OUT, encoding="utf-8").read()
for sid, label in LAB.items():
    i = h.index('id="%s"' % sid); k = h.index('<div class="page', i); k = h.index(">", k) + 1
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
       'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ORDER))
