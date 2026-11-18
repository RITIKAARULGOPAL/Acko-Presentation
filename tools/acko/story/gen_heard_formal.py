# index-heard-formal.html: five formal ways to open on the MoM (18 Nov, Ritika: "give formal options", the design and the wording
# both). slides/s-heard-f1..f5.html (not in order.txt), each marked with a small chip, in the deck's concept-slide type: a small
# italic label, the headline in Figtree 400 ink with its key words 700 purple, the closing line in Figtree italic. The MoM's twelve
# points are word for word in every one. A wording bar (A … F, tools/acko/story/wordbar.py) sets the headline, label, closing line and
# title on all five at once, so she picks the words and the design together. Her pick goes into slides/s-heard.html.
#   python tools/acko/story/gen_heard_formal.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build
sys.path.insert(0, os.path.join("tools", "acko", "story"))
from wordbar import chips, inject, wordbar

OPTS = [("s-heard-f1", "Formal · 1 · Register"),
        ("s-heard-f2", "Formal · 2 · Cards"),
        ("s-heard-f3", "Formal · 3 · Panel"),
        ("s-heard-f4", "Formal · 4 · Editorial"),
        ("s-heard-f5", "Formal · 5 · Document")]
WORDS = [
    ("A", "Summary of", "your feedback.", "Minutes of our meeting", "The proposal that follows responds to each of these points.", "Summary of feedback"),
    ("B", "Key points from", "our discussion.", "Client feedback", "Each has been considered in the design that follows.", "Key points"),
    ("C", "Your brief,", "as discussed.", "Twelve points from our meeting", "The following pages address each point in turn.", "Your brief"),
    ("D", "Design", "inputs.", "Received from ACKO", "These inputs have shaped the revised proposal.", "Design inputs"),
    ("E", "What", "we heard.", "Meeting outcomes", "Each outcome is addressed in the proposal that follows.", "What we heard"),
    ("F", "Feedback", "received.", "Minutes of meeting", "Our response is set out in the pages that follow.", "Feedback received"),
]
SEL = {"title": ".hdr b", "kick": ".fm-k", "head": ".fm-head", "hand": ".fm-close"}
MAP = {sid: dict(SEL, lines=3 if sid == "s-heard-f3" else 1) for sid, _ in OPTS}   # the panel's headline may take three lines

# the key words' animation (18 Nov, Ritika: "do some animation to highlight the keywords"): three styles in every slide (hl-1 sweep,
# hl-2 underline, hl-3 marker); a Highlight group on the bar picks one for all five, remembered, and replays it on the slide in view
HL = """<style>#hw-bar .hw-sep { width: 1px; height: 16px; margin: 0 6px 0 4px; background: #d6cdf3; }
#hw-bar button.sel { background: #5222d0; border-color: #5222d0; color: #fff; }
.scene .page.kw-quick { --kb: .15s !important; }</style>
<script>
(() => {
  const KEY = "acko-heard-formal-hl", NAMES = ["Sweep", "Underline", "Marker"];
  let hl = 2;   // the underline (Ritika, 18 Nov: "underline is nice")
  try { const v = +localStorage.getItem(KEY); if (v >= 1 && v <= 3) hl = v; } catch (e) { /* no storage: the underline */ }
  function set(n, replay) {
    hl = n;
    document.querySelectorAll(".scene .page").forEach((p) => { p.classList.remove("hl-1", "hl-2", "hl-3"); p.classList.add("hl-" + n); });
    document.querySelectorAll("#hw-bar .hw-hl").forEach((b) => b.classList.toggle("sel", +b.dataset.hl === n));
    try { localStorage.setItem(KEY, String(n)); } catch (e) { /* not remembered, still shown */ }
    const p = replay && document.querySelector(".scene.active .page");
    if (p && p.classList.contains("kw-on")) { p.classList.add("kw-quick"); p.classList.remove("kw-on"); void p.offsetWidth; p.classList.add("kw-on"); }
  }
  function add() {
    const bar = document.getElementById("hw-bar");
    if (!bar) { requestAnimationFrame(add); return; }
    const g = document.createElement("span");
    g.style.display = "contents";
    g.innerHTML = '<i class="hw-sep"></i><span class="hw-l">Highlight</span>' + NAMES.map((n, i) => `<button type="button" class="hw-hl" data-hl="${i + 1}" title="${n}">${i + 1}</button>`).join("");
    bar.insertBefore(g, bar.querySelector(".hw-now"));
    g.addEventListener("click", (e) => { const b = e.target.closest(".hw-hl"); if (b) { e.stopPropagation(); set(+b.dataset.hl, true); } });   // not the wording bar's
    set(hl, false);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", add); else add();
})();
</script>
"""

OUT = "index-heard-formal.html"
build.build([i for i, _ in OPTS], OUT)
h = open(OUT, encoding="utf-8").read()
h = inject(chips(h, OPTS), wordbar(WORDS, MAP, "acko-heard-formal-words", start="D") + HL)   # D first (18 Nov, Ritika: "design inputs so far works")
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(OPTS), "·", len(WORDS), "wordings")
