# index-why-campus.html: twelve ways to depict "Why a campus" (17 Nov, Ritika: "give multiple variations in depicting this slide";
# then "give more options": 7-9 take option 6's campus map further, 10-12 are new).
# The words, the footer and the three beats are the same in every option; only the picture changes. The options are
# slides/s-wc-1..12.html (not in order.txt): 1 is the slide as it was on 17 Nov, 2-12 are written by hand. Her pick, option 3,
# the merge, went into slides/s-why-campus.html on 18 Nov ("we can go with this option"), and Story 2 was rebuilt.
# index-why-merge.html: the merge and six variants of it (18 Nov, Ritika: "give me more variants keeping this as base"), slides
# s-wm-1..6.html (not in order.txt), each option 3 with only its picture changed. Her pick, 3.2 two drops, went into s-why-campus.html
# on 18 Nov. index-campus-loop.html: the next slide's three Möbius versions (below).
#   python tools/acko/story/gen_why_opts.py .
import sys, os, re
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

# index-campus-loop.html (18 Nov, Ritika: "the circle fill of the merged circle would move like a ribbon to next slide … the same ribbon
# would continue as mobius strip after '+' showing acko's mobius strip"; asked to see all three): Why a campus, then How it ties
# together three ways, differing only after "+". Version 1 is the deck's own slides/s-campus-loop.html (MOB = 1, the deck's render);
# 2 and 3 are copies of it made here (MOB = 2, the ribbon becomes the strip; MOB = 3, ACKO's mark), not in order.txt. Her pick
# becomes the deck slide's MOB.
MOBS = [(1, "the deck's render"), (2, "the ribbon becomes the strip"), (3, "ACKO's mark")]
src = open("slides/s-campus-loop.html", encoding="utf-8").read()
assert src.count("const MOB = 1;") == 1
DECK = int(re.search(r"const LAYOUT = (\d+);", src).group(1))      # the deck slide's zoning (5, Courtyards, since 18 Nov)
def copy(sid, mob=1, layout=None, title=""):                # a copy of the deck slide under its own id (and filter id)
    s = src.replace("s-campus-loop", sid).replace("cpl-goo", sid.replace("s-", "") + "-goo")
    s = s.replace("const MOB = 1;", "const MOB = %d;" % mob)
    s = re.sub(r"const LAYOUT = \d+;", "const LAYOUT = %d;" % (layout or DECK), s)
    s = s.replace("<title>How campus and loop tie together · ACKO slide", "<title>How it ties together, %s · ACKO slide" % title)
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(s)
for n, _ in MOBS[1:]: copy("s-cl-%d" % n, mob=n, title="Möbius version %d" % n)
# Why a campus before each version (18 Nov, Ritika: "the transition between both slides should be smooth"), so every version opens
# from its drop: copies of the deck slide, s-wcx-2 and s-wcx-3, not in order.txt
why = open("slides/s-why-campus.html", encoding="utf-8").read()
for n, _ in MOBS[1:]:
    s = why.replace("s-why-campus", "s-wcx-%d" % n).replace("wc-goo", "wcx%d-goo" % n)
    open("slides/s-wcx-%d.html" % n, "w", encoding="utf-8", newline="\n").write(s)
page("index-campus-loop.html", sum([[("s-why-campus" if n == 1 else "s-wcx-%d" % n, "Why a campus · before Möbius %d" % n),
     ("s-campus-loop" if n == 1 else "s-cl-%d" % n, "How it ties together · Möbius %d · %s" % (n, label))] for n, label in MOBS], []))

# index-campus-zoning.html (18 Nov, Ritika: "give variations for the layout zoning and loop"): How it ties together six ways, differing
# only in the zoning on the floor and the loop through it (clicks 3–6). Layout 1 is the deck's own slide (LAYOUT = 1, Islands); 2–6
# are copies, s-cz-2 … s-cz-6, not in order.txt. Her pick becomes the deck slide's LAYOUT.
ZONINGS = [(1, "Islands"), (2, "Beads"), (3, "Bubbles"), (4, "Spine"), (5, "Courtyards"), (6, "Staggered"), (7, "Scribble")]
for n, label in ZONINGS:
    if n != DECK: copy("s-cz-%d" % n, layout=n, title="zoning %d · %s" % (n, label))
page("index-campus-zoning.html", [("s-campus-loop" if n == DECK else "s-cz-%d" % n, "The ACKO Loop · zoning %d · %s" % (n, label)) for n, label in ZONINGS])

# index-campus-people.html (18 Nov, Ritika: "instead of dots give variations to show humans"): Why a campus and How it ties together
# for each of five ways to draw a person (PEOPLE in both deck slides; 1 is the deck's until she picks). Copies s-wcp-n and s-cp-n,
# not in order.txt, made from the deck slides with PEOPLE set; her pick becomes PEOPLE in both.
PEOPLEV = [(6, "Mixed heights"), (7, "Dressed"), (8, "Walking"), (9, "Pairs"), (10, "Outline"), (11, "Inclusive"),
           (1, "Pawns"), (2, "Standing figures"), (3, "Heads and shoulders"), (4, "Top view"), (5, "Sketched")]   # the new six first (18 Nov, "give variations for humans")
items = []
for n, label in PEOPLEV:
    w = why.replace("s-why-campus", "s-wcp-%d" % n).replace("wc-goo", "wcp%d-goo" % n)
    w = re.sub(r"const PEOPLE = \d+;", "const PEOPLE = %d;" % n, w)
    open("slides/s-wcp-%d.html" % n, "w", encoding="utf-8", newline="\n").write(w)
    c = src.replace("s-campus-loop", "s-cp-%d" % n).replace("cpl-goo", "cp%d-goo" % n)
    c = re.sub(r"const PEOPLE = \d+;", "const PEOPLE = %d;" % n, c)
    c = c.replace("<title>How campus and loop tie together · ACKO slide", "<title>How it ties together, people %d · ACKO slide" % n)
    open("slides/s-cp-%d.html" % n, "w", encoding="utf-8", newline="\n").write(c)
    items += [("s-wcp-%d" % n, "People %d · %s · Why a campus" % (n, label)), ("s-cp-%d" % n, "People %d · %s · How it ties together" % (n, label))]
page("index-campus-people.html", items)
