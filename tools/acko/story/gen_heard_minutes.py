# index-heard-minutes.html: five ways to stage "The minutes" (17 Nov, Ritika, picking s-heard-4 with wording G from index-heard.html:
# "this style and wording is fine. show variations taking this as base"). First the base as she picked it (s-heard-4 with wording G
# put into this page), then slides/s-heard-4a..4e.html (not in order.txt), each marked with a small chip. Every one keeps the MoM's
# twelve points word for word and wording G: "First, your words." / "Before our ideas" / "Then, what we made of them." Her pick
# goes into slides/s-heard.html.
#   python tools/acko/story/gen_heard_minutes.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

OPTS = [("s-heard-4", "Minutes · As picked"),
        ("s-heard-4a", "Minutes · A · Notepad"),
        ("s-heard-4b", "Minutes · B · Sticky notes"),
        ("s-heard-4c", "Minutes · C · Notebook"),
        ("s-heard-4d", "Minutes · D · Annotated"),
        ("s-heard-4e", "Minutes · E · Pen")]
# wording G into the base (its own file keeps "We heard you."), only inside its section
G = [('<div class="hdr"><b>We heard you</b>', '<div class="hdr"><b>First, your words</b>'),
     ('<h2 class="mn-head">We heard you.</h2>', '<h2 class="mn-head">First, your words.</h2>'),
     ('<b class="hand mn-k">What you told us</b>', '<b class="hand mn-k">Before our ideas</b>'),
     ('<p class="hand mn-close">Everything that follows is built on what you told us.</p>', '<p class="hand mn-close">Then, what we made of them.</p>')]

OUT = "index-heard-minutes.html"
build.build([i for i, _ in OPTS], OUT)
h = open(OUT, encoding="utf-8").read()
a = h.index('id="s-heard-4"'); z = h.index("</section>", a)
sec = h[a:z]
for old, new in G:
    assert sec.count(old) == 1, old
    sec = sec.replace(old, new)
h = h[:a] + sec + h[z:]
for sid, label in OPTS:
    a = h.index('id="%s"' % sid); k = h.index('<div class="page">', a) + len('<div class="page">')
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS = ('<style>.scene .page > .op-chip { left: 2.2%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
       'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
assert tag in h
h = h.replace(tag, CSS + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(OPTS))
