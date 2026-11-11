# index-open.html: the three ways to open the deck on ACKO's Möbius (11 Nov, Ritika: "start it with acko's mobius strip"), one after
# another, each marked with a small chip, then the Möbius and Where both meet as they follow in the re-ordered deck, so the hand-off
# can be judged too. The options are slides/s-open-1..3.html (not in order.txt); her pick becomes slides/s-open.html.
#   python tools/acko/story/gen_open.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

OPTS = [("s-open-1", "Opening · 1 · Logo unfurls"), ("s-open-2", "Opening · 2 · Into the strip"), ("s-open-3", "Opening · 3 · Loop to campus")]
ORDER = [i for i, _ in OPTS] + ["s-mobius", "s-campus"]
OUT = "index-open.html"
build.build(ORDER, OUT)
h = open(OUT, encoding="utf-8").read()
for sid, label in OPTS:
    a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
       'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
assert tag in h
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ORDER))
