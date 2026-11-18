# index-story2-numbered.html: Story 2 with every beat numbered (18 Nov, Ritika, before re-ordering the deck: "number each beat, so I
# can use it to mark the changes"). A copy of the built index-story2.html with a small purple badge, top centre: the beat's number
# through the whole deck (counted through each slide's data-steps in page order, as the deck counts), the slide's title, and for a
# slide of several beats which one it is and its name. It follows the address (#slide/beat). H hides or shows it (N is the notes).
# The real deck is untouched; run this again after the deck is rebuilt.
#   python tools/acko/story/gen_story2_numbered.py .
import sys, os, re
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
SRC = sys.argv[2] if len(sys.argv) > 2 else "index-story2.html"          # e.g. index-story3.html: its copy is index-story3-numbered.html
OUT = SRC.replace(".html", "-numbered.html")

BADGE = """<style>/* the beat number (index-story2-numbered.html only) */
#beat-no { position: fixed; left: 50%; top: calc(var(--ptop) + var(--ph) * .022); transform: translateX(-50%); z-index: 140; display: flex; align-items: center; gap: 8px;
  max-width: 56vw; padding: 5px 13px 5px 6px; border-radius: 99px; background: rgba(82, 34, 208, .94); color: #fff; font: 600 12px/1.2 var(--body);
  box-shadow: 0 2px 12px rgba(20, 10, 60, .3); pointer-events: none; white-space: nowrap; }
#beat-no b { min-width: 30px; padding: 4px 7px; border-radius: 99px; background: #fff; color: #5222d0; font: 700 13px/1 var(--num); text-align: center; }
#beat-no span { overflow: hidden; text-overflow: ellipsis; }
#beat-no i { font-style: normal; opacity: .78; }
#beat-no.off { display: none; }
</style>
<script>
(() => {
  let starts = null, total = 0, badge = null, last = "";
  function index() {
    starts = {}; total = 0;
    document.querySelectorAll("section.scene").forEach((s) => { starts[s.id] = total; total += +s.dataset.steps || 1; });
  }
  function show() {
    if (!badge) return;
    const m = (location.hash || "").match(/^#([\\w-]+)\\/(\\d+)/);
    const sc = (m && document.getElementById(m[1])) || document.querySelector("section.scene.active");
    if (!sc || !(sc.id in starts)) return;
    const steps = +sc.dataset.steps || 1, k = Math.min(Math.max(m && m[1] === sc.id ? +m[2] : 1, 1), steps);
    const names = (sc.dataset.beats || "").split(",").map((x) => x.trim()), no = starts[sc.id] + k;
    const key = no + "|" + sc.id;
    if (key === last) return;
    last = key;
    const esc = (t) => t.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
    badge.dataset.no = no;
    badge.innerHTML = `<b>${no}</b><span>${esc(sc.dataset.title || sc.id)}` + (steps > 1 ? ` <i>· ${k}/${steps}${names[k - 1] ? " " + esc(names[k - 1]) : ""}</i>` : "") + "</span>";
  }
  function start() {
    index();
    badge = document.createElement("div"); badge.id = "beat-no"; badge.setAttribute("aria-hidden", "true");
    document.body.appendChild(badge);
    show();
    addEventListener("hashchange", show);
    setInterval(show, 250);
    document.addEventListener("keydown", (e) => { if ((e.key === "h" || e.key === "H") && !(e.target.closest && e.target.closest("input, textarea"))) badge.classList.toggle("off"); });
    window.__beats = { total: () => total, starts: () => starts };
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
</script>
"""

h = open(SRC, encoding="utf-8").read()
tag = '<script src="assets/js/app.js'
assert h.count(tag) == 1, "engine tag"
h = h.replace(tag, BADGE + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
steps = [int((re.search(r'data-steps="(\d+)"', a) or [0, 1])[1]) for a in re.findall(r'<section class="scene[^"]*" id="[^"]+"([^>]*)>', h)]
print("ok", OUT, len(steps), "slides,", sum(steps), "beats")
