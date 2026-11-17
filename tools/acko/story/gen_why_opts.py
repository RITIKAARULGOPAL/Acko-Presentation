# index-why-campus.html: six ways to depict "Why a campus" (17 Nov, Ritika: "give multiple variations in depicting this slide").
# The words, the footer and the three beats are the same in every option; only the picture changes. The options are
# slides/s-wc-1..6.html (not in order.txt): 1 is the slide as it is (copied here from slides/s-why-campus.html), 2-6 are written
# by hand. Her pick goes into slides/s-why-campus.html (its ids renamed back), then Story 2 is rebuilt.
#   python tools/acko/story/gen_why_opts.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

OPTS = [
    (1, "As now"),
    (2, "Before | after"),
    (3, "The merge"),
    (4, "Two lines, one loop"),
    (5, "By the numbers"),
    (6, "Campus map"),
]

# option 1: the slide as it is, under its own id
src = open("slides/s-why-campus.html", encoding="utf-8").read()
assert src.count('ACKO.slide("s-why-campus"') == 1
t = src.replace("s-why-campus", "s-wc-1").replace("<title>Why a campus · ACKO slide", "<title>Why a campus, option 1 · ACKO slide")
open("slides/s-wc-1.html", "w", encoding="utf-8", newline="\n").write(t)

ids = []
for n, label in OPTS:
    sid = "s-wc-%d" % n
    if not os.path.exists("slides/%s.html" % sid):
        print("  skip %s (not written yet)" % sid); continue
    ids.append((sid, "Why a campus · %d · %s" % (n, label)))

OUT = "index-why-campus.html"
shell = os.path.join("assets", "js", "shell.js")
keep = open(shell, "rb").read()                      # build() rewrites the chrome; keep the committed bytes
try:
    build.build([i for i, _ in ids], OUT)
finally:
    open(shell, "wb").write(keep)
h = open(OUT, encoding="utf-8").read()
for sid, label in ids:
    a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 50%; top: 3.2%; transform: translateX(-50%); z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); '
       'border-radius: 99px; background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; '
       'white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
assert tag in h
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ids))
