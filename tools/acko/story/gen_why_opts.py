# index-why-campus.html: twelve ways to depict "Why a campus" (17 Nov, Ritika: "give multiple variations in depicting this slide";
# then "give more options": 7-9 take option 6's campus map further, 10-12 are new).
# The words, the footer and the three beats are the same in every option; only the picture changes. The options are
# slides/s-wc-1..12.html (not in order.txt): 1 is the slide as it was on 17 Nov, 2-12 are written by hand. Her pick, option 3,
# the merge, went into slides/s-why-campus.html on 18 Nov ("we can go with this option"), and Story 2 was rebuilt.
# index-why-merge.html: the merge and six variants of it (18 Nov, Ritika: "give me more variants keeping this as base"), slides
# s-wm-1..6.html (not in order.txt), each option 3 with only its picture changed. Her pick of these goes into s-why-campus.html.
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
    (7, "Map · by headcount"),
    (8, "Map · night"),
    (9, "Map · warmth"),
    (10, "A village of homes"),
    (11, "Around one table"),
    (12, "Two streams"),
]
MERGE = [
    (1, "They meet"),
    (2, "Two drops"),
    (3, "∞ becomes O"),
    (4, "Bloom"),
    (5, "Soft neighbourhoods"),
    (6, "Through the arrivals"),
]

CSS = ('<style>.scene .page > .op-chip { left: 50%; top: 3.2%; transform: translateX(-50%); z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); '
       'border-radius: 99px; background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; '
       'white-space: nowrap; pointer-events: none; }</style>\n')

# one options page: the slides in this order, each with its purple chip naming it
def page(OUT, items):
    ids = []
    for sid, label in items:
        if not os.path.exists("slides/%s.html" % sid):
            print("  skip %s (not written yet)" % sid); continue
        ids.append((sid, label))
    shell = os.path.join("assets", "js", "shell.js")
    keep = open(shell, "rb").read()                  # build() rewrites the chrome; keep the committed bytes
    try:
        build.build([i for i, _ in ids], OUT)
    finally:
        open(shell, "wb").write(keep)
    h = open(OUT, encoding="utf-8").read()
    for sid, label in ids:
        a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
        h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
    tag = '<script src="assets/js/app.js'
    assert tag in h
    h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
    open(OUT, "w", encoding="utf-8").write(h)
    print("ok", OUT, len(ids))

page("index-why-campus.html", [("s-wc-%d" % n, "Why a campus · %d · %s" % (n, label)) for n, label in OPTS])
page("index-why-merge.html", [("s-wc-3", "The merge · 3 · as chosen")] +
     [("s-wm-%d" % n, "The merge · 3.%d · %s" % (n, label)) for n, label in MERGE])
