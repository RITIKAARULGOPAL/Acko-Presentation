# index-agenda.html: six ways to word the agenda (12 Nov, Ritika: "can we have different captions and text to begin with. give me
# variations il pick"). Same layout and the same five parts; the label, headline, subtitle and the five hand captions change.
# The options are slides/s-ag-1..6.html (not in order.txt); her pick goes into slides/s-agenda.html.
#   python tools/acko/story/gen_agenda_opts.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

PARTS = ["Belonging", "The Site", "The Plan", "The Feel", "The Day"]
OPTS = [
    ("1 · As now", "Today", "One promise,", "made into a place.",
     "Why people come in, the answer in ACKO’s own promise, and how it becomes one floor and one day.",
     ["why people come in", "where it must happen", "how it becomes a campus", "what it feels like", "can we live it?"]),
    ("2 · From belonging to campus", "Today", "From belonging", "to a campus.",
     "How 651 Ackers, two offices and one long floor become one place.",
     ["why we come in", "one floor, 245 m long", "one loop, six neighbourhoods", "warm, quiet, easy to find", "arrival to evening"]),
    ("3 · Five questions", "Five questions", "Five questions,", "one answer.",
     "Each part asks one thing. The answer is always the Loop.",
     ["why come in?", "where?", "how?", "how does it feel?", "can we live it?"]),
    ("4 · The promise", "ACKO’s promise", "Always us with you,", "<br>made into a place.",
     "ACKO’s promise, followed from its people to its floor.",
     ["the people and the promise", "the floor we were given", "the loop that plans it", "the materials that hold it", "the day that proves it"]),
    ("5 · A walk", "Today’s walk", "Walk it", "the way an Acker would.",
     "We’ll take you round the Loop, from the first hello to the last coffee.",
     ["meet the people", "see the ground", "follow the plan", "touch the materials", "live the day"]),
    ("6 · Few words", "The Loop", "The Loop,", "ACKO Campus.", None,
     ["people", "place", "plan", "feel", "day"]),
]

src = open("slides/s-agenda.html", encoding="utf-8").read()
H2 = "<h2 style=\"--i:1\">One promise, <span>made into a place.</span></h2>"
P = '<p style="--i:2">ACKO’s own promise, “it’s always us with you”, followed from your mark to the floor, and through one day on it.</p>'
OLDQ = ["why people come in", "where it must happen", "how it becomes a campus", "what it feels like", "can we live it?"]
assert H2 in src and P in src and '<small style="--i:0">Today</small>' in src
ids = []
for n, (chip, label, bold, rest, sub, caps) in enumerate(OPTS, 1):
    sid = "s-ag-%d" % n; ids.append((sid, "Agenda · " + chip))
    t = src.replace("s-agenda", sid)
    t = t.replace('<small style="--i:0">Today</small>', '<small style="--i:0">%s</small>' % label)
    t = t.replace(H2, '<h2 style="--i:1">%s <span>%s</span></h2>' % (bold, rest))
    t = t.replace(P, '<p style="--i:2">%s</p>' % sub if sub else "")
    for old, new in zip(OLDQ, caps):
        k = '<span class="hand">%s</span>' % old; assert k in t, k; t = t.replace(k, '<span class="hand">%s</span>' % new, 1)
    notes = "The agenda: %s %s %s Five parts. " % (bold, rest.replace("<br>", ""), sub or "") + " ".join(
        "%02d %s: %s." % (i, p, c.rstrip("?.")) for i, (p, c) in enumerate(zip(PARTS, caps), 1)) + " Bridge: let's begin with the people."
    t = __import__("re").sub(r'data-notes="[^"]*"', lambda m: 'data-notes="%s"' % notes.replace('"', "&quot;"), t, count=1)
    t = t.replace("<title>The agenda · ACKO slide %s</title>" % sid, "<title>Agenda option %d · ACKO slide %s</title>" % (n, sid))
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(t)

OUT = "index-agenda.html"
build.build([i for i, _ in ids], OUT)
h = open(OUT, encoding="utf-8").read()
for sid, label in ids:
    a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
       'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
assert tag in h
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ids))
