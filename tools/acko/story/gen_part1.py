# index-part1.html: Part 01's two slides (the mark · the loop around us) three ways, with fewer words and the tags carried by the loop
# itself (11 Nov, Ritika: "the text seems too cluttered … the idea … is not conveyed well. All the tags are not feeling continuous").
# Every way: at most one headline and one hand line a click; the values (slide a) and the lines of business (slide b) written ALONG the
# strip's own line (SVG textPath on f1 · bk · f2, photo px), never in boxes.
#   1 · words on the loop: the lettering slides slowly round the strip, one continuous band
#   2 · the loop in lengths: the line divided into lengths, one per value / line of business, each tinted and named along itself, a
#       dashed length for what's next; on "it holds" arcs bridge across between them
#   3 · one sentence: a single line along the foot builds across the clicks; the lettering rides the loop as in 1
# Made from the deck's own s-open (the ribbon logo, PICK in gen_unfold.py) and s-loopmean; the deck is untouched until she picks.
#   python tools/acko/story/gen_part1.py .
import sys, os, re
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

A0 = open("slides/s-open.html", encoding="utf-8").read()
B0 = open("slides/s-loopmean.html", encoding="utf-8").read()
VALUES = ["infinite trust", "inclusivity", "collaboration"]
LOB = ["car", "two-wheeler", "health", "travel", "life"]

def line_d(src):
    ds = [re.search(r'class="o2-l %s" d="([^"]+)"' % k, src).group(1) for k in ("f1", "bk", "f2")]
    return ds[0] + " " + " ".join(re.sub(r"^M[\d.\s-]+", "", d) for d in ds[1:])   # one path: f1, then bk and f2 without their moves

WORDS = {   # (slide a: [(beat, headline, hand)], slide b: [...]); option 3 is a sentence instead
    "a": [(1, "One continuous <b>loop.</b>", ""), (2, "Always <b>us with you.</b>", "it’s never us versus you")],
    "b": [(1, "A loop <b>connects.</b>", "and surrounds"), (2, "<b>One loop</b>, every line of business.", "and room for what’s next"), (3, "Where it bridges, <b>it holds.</b>", "one continuous journey")],
}
SENTENCE = {"a": [(1, "One continuous loop,"), (2, "<b>always us with you.</b>")],
            "b": [(1, "A loop that connects,"), (2, "holds <b>every line of business</b>,"), (3, "and <b>keeps them safe.</b>")]}

CSS = '''/* Part 01, fewer words (11 Nov): one headline and one hand line a click; the tags ride the strip's own line */
#ID .o2-lob { display: none; }
#ID .o2-art svg.p1 { opacity: 1; overflow: visible; }
#ID .p1-wrap { position: absolute; left: 0; top: 0; width: 100%; height: 100%; }
#ID .p1-wrap.ad[data-step] { transition-delay: 3.4s; }
#ID .p1 .p1-txt { font-family: var(--body); font-size: 32px; font-weight: 600; letter-spacing: .04em; fill: #4e29bb; }
#ID .p1 .p1-txt.next { fill: #926ff3; font-style: italic; }
#ID .p1 .p1-seg { fill: none; stroke-width: 9; stroke-linecap: butt; }
#ID .p1 .p1-seg.next { stroke-dasharray: 14 10; }
#ID .p1 .p1-br { fill: none; stroke: #5222d0; stroke-width: 4; opacity: 0; transition: opacity .8s var(--ease); }
#ID .b3 .p1 .p1-br { opacity: .7; }
#ID .pw { display: flex; flex-direction: column; gap: calc(var(--pt) * 6); }
#ID .pw h2 { margin: 0; font-size: calc(var(--pt) * 34); font-weight: 400; line-height: 1.08; color: #111; }
#ID .pw h2 b { font-weight: 700; color: var(--purple); }
#ID .pw p.hand { margin: 0; font-family: var(--hand); font-size: calc(var(--pt) * 22); line-height: 1; color: var(--purple); }
#ID .pw-a { left: 5%; top: 40%; width: 33%; }
#ID .pw-b { left: 64%; top: 40%; width: 32%; }
#ID .pw-a[data-only="1"] { transition-delay: 3.2s; }
#ID .ps { left: 5%; top: 70%; width: 60%; margin: 0; font-size: calc(var(--pt) * 20); line-height: 1.25; font-weight: 400; color: #111; }
#ID .ps.ps-b { left: 63%; top: 38%; width: 33%; font-size: calc(var(--pt) * 24); }
#ID .ps:not(.ps-b) { left: 5%; top: 40%; width: 32%; font-size: calc(var(--pt) * 28); }
#ID .ps b { font-weight: 700; color: var(--purple); }
#ID .ps span { display: inline-block; margin-right: .3em; }
#ID .ps span[data-step="1"].ad { transition-delay: 3.2s; }
'''

def words(slide, opt):
    if opt == 3:
        sp = "".join('<span data-step="%d"%s>%s</span>' % (k, ' class="ad"' if slide == "a" and k == 1 else "", w) for k, w in SENTENCE[slide])
        return '    <p class="ps%s">%s</p>\n' % ("" if slide == "a" else " ps-b", sp)   # the side the strip leaves free
    cl = "pw pw-a" if slide == "a" else "pw pw-b"
    return "".join('    <div class="%s" data-only="%d"><h2>%s</h2>%s</div>\n' % (cl, k, h, '<p class="hand">%s</p>' % hd if hd else "") for k, h, hd in WORDS[slide])

def ride(slide, opt, sid):
    """the svg laid over the strip: the joined line, and the tags on it (flowing text, or lengths with their names)"""
    d = line_d(A0)
    items = VALUES if slide == "a" else LOB
    step = 1 if slide == "a" else 2
    pid = "p1l-" + sid
    head = '<div class="p1-wrap%s" data-step="%d"><svg class="p1" viewBox="0 0 1536 1024" aria-hidden="true"><defs><path id="%s" d="%s"/></defs>' % (" ad" if slide == "a" else "", step, pid, d)
    if opt in (1, 3):
        band = "  ·  ".join(items) + ("  ·  what’s next…" if slide == "b" else "") + "  ·  "
        txt = band * 10
        body = ('<text class="p1-txt" dy="-16"><textPath href="#%s" startOffset="0">%s'
                '<animate attributeName="startOffset" from="-1200" to="0" dur="26s" repeatCount="indefinite"/></textPath></text>') % (pid, txt)
    else:   # lengths: the line in tinted lengths, each named along itself; the arcs (bridges) laid out by the script
        names = items + (["what’s next…"] if slide == "b" else [])
        tints = ["#5222d0", "#7a52e6", "#9068f0", "#4828ba", "#6a40d8", "#926ff3"]
        body = "".join('<use class="p1-seg%s" href="#%s" data-k="%d" style="stroke:%s"/>' % (" next" if n.startswith("what") else "", pid, k, tints[k % len(tints)]) for k, n in enumerate(names))
        body += "".join('<text class="p1-txt%s" dy="-16"><textPath href="#%s" data-k="%d" text-anchor="middle">%s</textPath></text>' % (" next" if n.startswith("what") else "", pid, k, n) for k, n in enumerate(names))
        if slide == "b": body += '<path class="p1-br"/><path class="p1-br"/><path class="p1-br"/>'
    return head + body + "</svg></div>\n"

JS = r'''
  // Part 01, the loop in lengths (option 2): each named length set along the line by arc length, and the bridges laid across
  let p1done = false;
  function p1setup(sc) {
    if (p1done) return; const pth = sc.querySelector(".p1 defs path"); if (!pth) return; p1done = true;
    const L = pth.getTotalLength(), segs = sc.querySelectorAll(".p1 .p1-seg"), n = segs.length; if (!n) return;
    const gap = 26, len = L / n;
    segs.forEach((u, k) => { u.style.strokeDasharray = u.classList.contains("next") ? "14 10" : `0 ${k * len + gap / 2} ${len - gap} ${L}`;
      if (u.classList.contains("next")) { u.style.strokeDashoffset = -(k * len + gap / 2); u.setAttribute("stroke-dasharray", "14 10"); u.style.clipPath = ""; } });
    sc.querySelectorAll(".p1 textPath[data-k]").forEach((tp) => tp.setAttribute("startOffset", (+tp.dataset.k + 0.5) * len));
    const nx = sc.querySelector(".p1 .p1-seg.next");
    if (nx) { const k = +nx.dataset.k; nx.style.strokeDasharray = ""; nx.setAttribute("stroke-dasharray", `0 ${k * len + gap / 2} ` + Array.from({ length: Math.floor((len - gap) / 24) }, () => "14 10").join(" ") + ` ${L}`); }
    const br = sc.querySelectorAll(".p1 .p1-br"), at = (s) => pth.getPointAtLength(((s % L) + L) % L);
    br.forEach((b, i) => { const p = at((i * 2 + 0.5) * len), q = at((i * 2 + 3.5) * len), c = [(p.x + q.x) / 2 * 0.6 + 768 * 0.4, (p.y + q.y) / 2 * 0.6 + 512 * 0.4];
      b.setAttribute("d", `M${p.x.toFixed(1)} ${p.y.toFixed(1)}Q${c[0].toFixed(1)} ${c[1].toFixed(1)} ${q.x.toFixed(1)} ${q.y.toFixed(1)}`); });
  }
'''

def variant(src, slide, opt, sid, old_id):
    t = src.replace(old_id, sid)
    if slide == "a":
        i, j = t.index("    <!--words-->"), t.index("    <!--/words-->") + len("    <!--/words-->\n")
    else:
        i = t.index('    <div class="lm">'); j = t.index("</div>\n    </div>\n", i) + len("</div>\n    </div>\n")
    t = t[:i] + words(slide, opt) + t[j:]
    a = t.index('        <div class="o2-lob"></div>\n'); t = t[:a] + "        " + ride(slide, opt, sid) + t[a:]
    t = t.replace("</style>", CSS.replace("#ID", "#" + sid) + "</style>", 1)
    t = t.replace("  let built = false, last = 0;", JS + "  let built = false, last = 0;", 1)
    e = "    enter(_, sc) { plain(); build(sc);"
    assert t.count(e) == 1, "enter"
    t = t.replace(e, "    enter(_, sc) { plain(); build(sc); p1setup(sc);", 1)
    title = {"a": "The mark", "b": "The loop around us"}[slide]
    t = re.sub(r"<title>[^<]*</title>", "<title>Part 01 · %d%s · %s · ACKO slide %s</title>" % (opt, slide, title, sid), t, count=1)
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(t)
    print("ok", sid)

NAMES = {1: "Words on the loop", 2: "The loop in lengths", 3: "One sentence"}
ORDER, LAB = [], {}
for n in (1, 2, 3):
    for slide, src, old in (("a", A0, "s-open"), ("b", B0, "s-loopmean")):
        sid = "s-p1-%d%s" % (n, slide)
        variant(src, slide, n, sid, old)
        ORDER.append(sid); LAB[sid] = "Part 01 · %d · %s%s" % (n, NAMES[n], "" if slide == "a" else " (2/2)")

OUT = "index-part1.html"
build.build(ORDER, OUT)
h = open(OUT, encoding="utf-8").read()
for sid, label in LAB.items():
    i = h.index('id="%s"' % sid); k = h.index('<div class="page', i); k = h.index(">", k) + 1
    h = h[:k] + '\n    <div class="op-chip">%s</div>' % label + h[k:]
CSS2 = ('<style>.scene .page > .op-chip { right: 6%; top: 3.2%; z-index: 9; padding: calc(var(--pt) * 3) calc(var(--pt) * 9); border-radius: 99px; '
        'background: #5222d0; color: #fff; font-size: calc(var(--pt) * 8); font-weight: 700; letter-spacing: .04em; white-space: nowrap; pointer-events: none; }</style>\n')
tag = '<script src="assets/js/app.js'
h = h.replace(tag, CSS2 + '<script>window.ACKO_WOW = true;</script>\n' + tag, 1)
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(ORDER))
