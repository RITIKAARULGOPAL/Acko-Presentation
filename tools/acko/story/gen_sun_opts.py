# index-sun.html: the Site due diligence slide alone, with four looks for the sun itself (18 Nov, Ritika picked A, the wall glow and a gradient
# line, then: "sun can flow with the path. show different variations of sun. no need to have the extended dashed line"). A bar at the foot,
# Sun look 1 · 2 · 3 · 4, sets the look (slides/s-site-dd.html: sm-1 .. sm-4) and replays the day; the choice is remembered in this browser.
#   1 orb: a soft glow · 2 rays: a ring of rays that turns · 3 pulse: rings rippling out · 4 beam: a short cone of light the way it travels
#   python tools/acko/story/gen_sun_opts.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

BAR = """<style>/* the sun style bar (index-sun.html only) */
#sn-bar { position: fixed; left: calc(var(--pl) + var(--pw) * .5); bottom: calc(var(--ptop) + var(--ph) * .012); transform: translateX(-50%); z-index: 130; display: flex; align-items: center; gap: 3px;
  padding: 4px 6px 4px 11px; border-radius: 99px; background: rgba(255,255,255,.96); box-shadow: 0 2px 14px rgba(20,10,60,.22); font: 600 12px/1 var(--body); color: #26213a; white-space: nowrap; pointer-events: auto; }
#sn-bar .sn-l { margin-right: 5px; font-size: 9.5px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #c47a00; }
#sn-bar button { height: 23px; padding: 0 9px; border: 1px solid #f1d9a8; border-radius: 99px; background: #fff; color: #b06a00; font: 700 11px/1 var(--body); cursor: pointer; }
#sn-bar button:hover { border-color: #c47a00; }
#sn-bar button.on { background: #e8700c; border-color: #e8700c; color: #fff; }
#sn-bar .sn-now { margin: 0 6px 0 8px; color: #26213a; font-weight: 600; }
</style>
<script>
(() => {
  const KEY = "acko-sun-look", S = [["1", "1", "Orb"], ["2", "2", "Rays"], ["3", "3", "Pulse"], ["4", "4", "Beam"]];
  let cur = "1"; try { const v = localStorage.getItem(KEY); if (v !== null && S.some((x) => x[0] === v)) cur = v; } catch (e) { /* none remembered */ }
  function apply(v) {
    const sc = document.getElementById("s-site-dd"); if (!sc || !sc._sunLook) return false;
    cur = v; sc._sunLook(v);
    document.querySelectorAll("#sn-bar button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    const n = document.querySelector("#sn-bar .sn-now"); if (n) n.textContent = S.find((x) => x[0] === v)[2];
    try { localStorage.setItem(KEY, v); } catch (e) { /* not remembered */ }
    return true;
  }
  function start() {
    const bar = document.createElement("div"); bar.id = "sn-bar";
    bar.innerHTML = '<span class="sn-l">Sun look</span>' + S.map(([v, l, t]) => `<button type="button" data-v="${v}" title="${t}">${l}</button>`).join("") + '<b class="sn-now"></b>';
    bar.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { e.stopPropagation(); apply(b.dataset.v); } });
    document.body.appendChild(bar);
    const t = setInterval(() => { if (apply(cur)) clearInterval(t); }, 100);
  }
  window.__sun = { apply, styles: S };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
</script>
"""
OUT = "index-sun.html"
build.build(["s-site-dd"], OUT)
h = open(OUT, encoding="utf-8").read()
tag = '<script src="assets/js/app.js'
assert tag in h
h = h.replace(tag, BAR + "<script>window.ACKO_WOW = true;</script>\n" + tag, 1)   # the bare shell and the DXF zones draw only with the big-moments switch, as on Story 3
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT)
