# index-story3.html: the presentation in Ritika's new structure (18 Nov, "ACKO — Presentation Structure"): eight sections, each slide
# named by its beat in index-story2-numbered.html. Made from the built index-story2.html, so every slide keeps its Story 2 edits;
# gen_story.py is untouched and Story 2 stays as the previous version. Her answers: the agenda lists what is ahead (04–08); a
# divider opens each of 04–08 (the Part card's design, made from s-start); Thank you closes; the Appendix and About SKV stay as side
# tracks; Why a campus beats 2–3, The loop on our floor, The opportunity and the old Part cards are out. Until her material arrives
# ("x: I should give information or it has to be built newly"), the closest existing slide stands in, else a placeholder
# (s-axo-detail, s-recap). Campus strategy keeps its four conceptual beats; its journeys go to the detailed axonometric.
#   python tools/acko/story/gen_story.py .      (Story 2 first)
#   python tools/acko/story/gen_story3.py .
import sys, os, re, json, tempfile, html as _h
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build

SRC, OUT = "index-story2.html", "index-story3.html"
RENDERS = ("s-w-reception s-w-recoffee s-w-cafe1 s-w-cafe2 s-w-deck s-w-coffee s-w-board s-w-exec s-w-dept s-w-sprint s-w-collab "
           "s-w-garden s-w-arena s-w-arena2a s-w-mothers s-w-zen s-w-studio").split()
# (part key, number, name, her line, slides)
SECTIONS = [
    ("cover", "", "Project Vision", "Opening & project introduction", ["s-cover", "s-team"]),
    ("p2", "", "Design Drivers", "Design inputs so far", ["s-heard"]),
    ("p3", "", "Overview", "Presentation roadmap", ["s-overview"]),
    ("p4", "01", "Concept Framework", "Establishing the overarching design vision", ["s-div-1", "s-why-campus", "s-campus-loop"]),
    ("p5", "02", "Design Development", "Translating the concept into a spatial solution",
     ["s-div-2", "s-site", "s-pitch", "s-site-dd", "s-strategy", "s-layout-sp", "s-axo-detail", "s-wayday"]),
    ("p6", "03", "Design Expression", "Materiality, visualisation and spatial experience", ["s-div-3", "s-material", "s-palette2", "s-walkthrough"] + RENDERS),
    ("p7", "04", "Integrated Performance", "Technical performance and added value", ["s-div-4", "s-esg", "s-wf-a6", "s-engage", "s-di"]),
    ("p8", "05", "Project Review", "Revisiting previous discussions and establishing alignment", ["s-div-5", "s-recap"]),
    ("close", "", "Thank you", "", ["s-thanks-w"]),
    ("A", "", "Appendix · Kit of parts", "", ["s-typologies", "s-memories", "s-wellbeing"]),
    ("0", "", "About SKV", "", ["s-skv"]),
]
AHEAD = [s for s in SECTIONS if s[0] in ("p4", "p5", "p6", "p7", "p8")]   # what the agenda and the dividers list: sections 01-05 (18 Nov, Ritika: "section should be numbered from 1 so total is 5")
PART = {sid: key for key, _, _, _, ids in SECTIONS for sid in ids}
LABEL = {key: ("%s · %s" % (num, name) if num else name) for key, num, name, _, _ in SECTIONS}
ORDER = [sid for _, _, _, _, ids in SECTIONS for sid in ids]
OLD_LABELS = ["01 · Belonging", "02 · The Site", "03 · The Plan", "04 · The Feel", "05 · The Day"]
# the bridges (speaker notes) for the new flow
BRIDGE = {
    "s-team": "First, the inputs you gave us.",
    "s-heard": "Here's how today will run.",
    "s-overview": "The concept first. 01 · Concept Framework.",
    "s-why-campus": "Two offices, one floor: so we made it one campus.",
    "s-campus-loop": "Now the floor itself. 02 · Design Development.",
    "s-site": "How big is this floor? Two football pitches.",
    "s-pitch": "And what we found on it: the due diligence.",
    "s-site-dd": "From the campus idea to the floor, in four moves.",
    "s-strategy": "And here's the plan that makes it work.",
    "s-layout-sp": "Now the plan rises into the axonometric.",
    "s-axo-detail": "And over one day in ACKO…",
    "s-wayday": "What it's made of. 03 · Design Expression.",
    "s-material": "And the palette it comes together in.",
    "s-palette2": "Now walk through it.",
    "s-walkthrough": "And every space, one by one.",
    "s-w-studio": "How it performs. 04 · Integrated Performance.",
    "s-esg": "And on a floor this long, finding your way should be effortless.",
    "s-wf-a6": "And at every stop, something for the Acker: their engagement points.",
    "s-engage": "And designed for everyone.",
    "s-di": "Last, back to where we started. 05 · Project Review.",
    "s-recap": "Thank you.",
}
NEW = ["s-div-%d" % int(s[1]) for s in AHEAD] + ["s-overview", "s-site-dd", "s-axo-detail", "s-recap"]

# ---- the dividers: s-start's design (as gen_story.py makes the Part cards), the five sections ahead, this one lit, her line said
st = open("slides/s-start.html", encoding="utf-8").read()
li = re.findall(r'<li style="--i:\d"><i></i><b>[^<]*</b><span class="hand">[^<]*</span></li>', st)
assert len(li) == 6, "start steps"
ln = re.search(r'<div class="st-line"[^>]*>.*?</div>', st).group(0)
for n, (key, num, name, line, _) in enumerate(AHEAD, 1):
    sid = "s-div-%d" % int(num)
    c = st
    c = c.replace(li[5] + "\n", "").replace(li[5], "")
    c = c.replace("grid-template-columns: repeat(6, 1fr)", "grid-template-columns: repeat(5, 1fr)")
    for old, (_, num2, name2, _, _) in zip(li, AHEAD):
        c = c.replace(old, re.sub(r'<b>[^<]*</b><span class="hand">[^<]*</span>', '<b>%s</b><span class="hand">%s</span>' % (num2, name2), old), 1)
    c = c.replace(ln, re.sub(r'<p>.*?</p><span class="hand">.*?</span>', '<p>%s.</p><span class="hand"></span>' % line, ln))
    c = c.replace('<small style="--i:0">Where it starts</small>', '<small style="--i:0">%s · %s</small>' % (num, name))
    c = re.sub(r'data-title="[^"]*"', 'data-title="%s · %s"' % (num, name), c, count=1)
    c = re.sub(r'data-notes="[^"]*"', 'data-notes="Section %s of 05: %s, %s."' % (num, name, line[0].lower() + line[1:]), c, count=1)
    for x, y in (("li:not(:first-child)", "li:not(:nth-child(%d))" % n), ("li:first-child i", "li:nth-child(%d) i" % n),
                 ('$(".ap-steps li i", sc)', '$(".ap-steps li:nth-child(%d) i", sc)' % n),
                 ("#s-start .ap-steps .hand { font-size: calc(var(--pt) * 19); }", "#s-start .ap-steps .hand { font-size: calc(var(--pt) * 15); }   /* the longer names */")):
        assert c.count(x) == 1, (sid, x); c = c.replace(x, y)
    c = c.replace("<!-- slide:start -->\n", "<!-- slide:start -->\n<!-- Divider %s · %s, generated by tools/acko/story/gen_story3.py from s-start (18 Nov, Ritika: a divider "
                  "for each of 01–05); edit the generator, not this file. -->\n" % (num, name), 1)
    c = c.replace("s-start", sid)
    open("slides/%s.html" % sid, "w", encoding="utf-8", newline="\n").write(c)

# ---- the agenda (03 Overview): the divider's design, all five sections at full strength: the dots, the numbers 01-05, the names
# (18 Nov, Ritika: "page 4 should be like page 5"; names only)
c = st
c = c.replace(li[5] + "\n", "").replace(li[5], "")
c = c.replace("grid-template-columns: repeat(6, 1fr)", "grid-template-columns: repeat(5, 1fr)")
for old, (_, num2, name2, _, _) in zip(li, AHEAD):
    c = c.replace(old, re.sub(r'<b>[^<]*</b><span class="hand">[^<]*</span></li>'.replace("</li>", ""), '<b>%s</b><span class="hand">%s</span>' % (num2, name2), old), 1)
c = c.replace(ln + "\n", "").replace(ln, "")
c = c.replace('<small style="--i:0">Where it starts</small>', '<small style="--i:0">Agenda</small>')
c = re.sub(r'data-title="[^"]*"', 'data-title="Agenda"', c, count=1)
c = re.sub(r'data-notes="[^"]*"', 'data-notes="%s"' % _h.escape("The agenda: five sections ahead. " + " ".join(
    "%s %s: %s." % (num, name, line[0].lower() + line[1:]) for _, num, name, line, _ in AHEAD), quote=True), c, count=1)
for x, y in (("    later(() => pg.classList.add(\"lit\"), 1300);\n    later(() => pg.classList.add(\"said\"), 2000);\n", ""),
             ("    if (reduced) { pg.classList.add(\"lit\", \"said\"); return; }\n", ""),
             ("#s-start .ap-steps .hand { font-size: calc(var(--pt) * 19); }", "#s-start .ap-steps .hand { font-size: calc(var(--pt) * 15); }   /* the longer names */")):
    assert c.count(x) == 1, ("overview", x[:50]); c = c.replace(x, y)
c = c.replace("<!-- slide:start -->\n", "<!-- slide:start -->\n<!-- The agenda for index-story3.html, generated by tools/acko/story/gen_story3.py from s-start: the divider's design, "
              "the five sections 01-05 together; edit the generator, not this file. -->\n", 1)
c = c.replace("s-start", "s-overview")
open("slides/s-overview.html", "w", encoding="utf-8", newline="\n").write(c)

# ---- the new slides, built on their own to lift their sections, styles and scripts
tmp = os.path.join(tempfile.gettempdir(), "acko-story3-new.html")
build.build(NEW, tmp)
t = open(tmp, encoding="utf-8").read()
os.remove(tmp)
def blocks(h, tag, sid):
    return re.findall(r'<%s data-slide="%s">.*?</%s>\n' % (tag, re.escape(sid), tag), h, re.S)

# ---- Story 2, re-ordered
h = open(SRC, encoding="utf-8").read()
i = h.index('<main id="stage">') + len('<main id="stage">'); j = h.index("</main>", i); stage = h[i:j]
SEC = {}; LEAD = {}                        # each section, and the comment before it (kept apart: the tag edits below look for the first ">")
prev = 0
for m in re.finditer(r'<section class="scene[^"]*" id="([^"]+)"', stage):
    e = stage.index("</section>", m.start()) + len("</section>")
    lead = stage[prev:m.start()]; lead = lead[lead.find("<!--"):] if "<!--" in lead else ""
    LEAD[m.group(1)] = lead.strip() + "\n" if lead.strip() else ""
    SEC[m.group(1)] = stage[m.start():e]
    prev = e
for sid in NEW:
    a = t.index('id="%s"' % sid); s0 = t.rindex("<section", 0, a); e = t.index("</section>", a) + len("</section>")
    SEC[sid] = t[s0:e]; LEAD[sid] = ""
missing = [s for s in ORDER if s not in SEC]
assert not missing, missing
dropped = [s for s in SEC if s not in ORDER and s not in NEW]

def attr(sec, name, value):                 # set an attribute on the section's opening tag
    k = sec.index(">") + 1; tag = sec[:k]
    tag, n = re.subn(r'(\s%s=")[^"]*(")' % name, lambda m: m.group(1) + value + m.group(2), tag, count=1)
    if not n: tag = tag[:-1] + ' %s="%s">' % (name, value)
    return tag + sec[k:]
def notes_cut(sec, marker):                 # keep the notes up to a beat that no longer shows
    return re.sub(r'(data-notes="[^"]*?) %s[^"]*"' % re.escape(marker), lambda m: m.group(1) + '"', sec, count=1)
def bridge(sec, text):
    text = _h.escape(text, quote=True)
    k = sec.index(">") + 1; tag = sec[:k]
    if "→ Bridge: " in tag: tag = re.sub(r"→ Bridge: [^\"]*", lambda m: "→ Bridge: " + text, tag, count=1)
    else: tag = re.sub(r'(data-notes="[^"]*)"', lambda m: m.group(1) + " → Bridge: " + text + '"', tag, count=1)
    return tag + sec[k:]

out = []
for sid in ORDER:
    s = SEC[sid]
    s = attr(s, "data-part", PART[sid])
    # a header that named an old part names its new section
    s = re.sub(r'(<div class="hdr"><b>[^<]*</b><span>)(%s)(</span></div>)' % "|".join(map(re.escape, OLD_LABELS)),
               lambda m: m.group(1) + LABEL[PART[sid]] + m.group(3), s)
    if sid in BRIDGE: s = bridge(s, BRIDGE[sid])
    out.append(s)
SEC2 = dict(zip(ORDER, out))

# site due diligence (18 Nov, Ritika: one view, the sun path with it): its header names its section
s = SEC2["s-site-dd"]
s = re.sub(r'(<div class="hdr"><b>Site due diligence</b><span>)[^<]*(</span>)', lambda m: m.group(1) + LABEL[PART["s-site-dd"]] + m.group(2), s, count=1)
SEC2["s-site-dd"] = s

# the stand-ins, until her material is in
s = SEC2["s-why-campus"]                    # Two Offices: Why a campus, both beats (Leela and HSR, then the two flowing into one drop, which the next slide turns into the ribbon; 19 Nov: "the merging is not happening")
s = attr(s, "data-title", "Two Offices")
s = s.replace('<div class="hdr"><b>Why a campus</b>', '<div class="hdr"><b>Two Offices</b>', 1)
SEC2["s-why-campus"] = bridge(s, BRIDGE["s-why-campus"])
s = SEC2["s-campus-loop"]                   # The ACKO Campus: Campus + Möbius = The ACKO Loop
SEC2["s-campus-loop"] = attr(s, "data-title", "The ACKO Campus").replace('<div class="hdr"><b>How it ties together</b>', '<div class="hdr"><b>The ACKO Campus</b>', 1)
s = SEC2["s-strategy"]                      # the conceptual axonometries: the first four beats
beats = re.search(r'data-beats="([^"]*)"', s[:s.index(">")])
s = attr(s, "data-steps", "4")
if beats: s = attr(s, "data-beats", ",".join(beats.group(1).split(",")[:4]))
SEC2["s-strategy"] = bridge(notes_cut(s, "5 ·"), BRIDGE["s-strategy"])

h = h[:i] + "\n" + "\n\n".join(LEAD[sid] + SEC2[sid] for sid in ORDER) + "\n" + h[j:]
# the dropped slides' styles and scripts go; the new slides' come in
for sid in dropped:
    h = re.sub(r'<(style|script) data-slide="%s">.*?</\1>\n' % re.escape(sid), "", h, flags=re.S)
st_new = "".join(b for sid in NEW for b in blocks(t, "style", sid))
js_new = "".join(b for sid in NEW for b in blocks(t, "script", sid))
last_style = max(m.end() for m in re.finditer(r'<style data-slide="[^"]+">.*?</style>\n', h, re.S))
h = h[:last_style] + st_new + h[last_style:]
k = h.index("<script>ACKO.start();</script>")
h = h[:k] + js_new + h[k:]
# the page's sections: the menu, the overview's headings, the renders' kicker
names = {key: LABEL[key] for key, *_ in SECTIONS if key != "0"}
main = [[key, name, ""] for key, num, name, _, _ in SECTIONS if key not in ("close", "A", "0")] + [["close", "Thank you", ""]]   # the dropdown: no numbers (18 Nov, Ritika)
h, n = re.subn(r"<script>window\.ACKO_SECTIONS = .*?;</script>", lambda m: "<script>window.ACKO_SECTIONS = %s;</script>" % json.dumps({"names": names, "main": main}, ensure_ascii=False), h, count=1)
assert n == 1, "sections"
open(OUT, "w", encoding="utf-8").write(h)
steps = [int((re.search(r'data-steps="(\d+)"', a) or [0, 1])[1]) for a in re.findall(r'<section class="scene[^"]*" id="[^"]+"([^>]*)>', h)]
print("ok", OUT, len(ORDER), "slides,", sum(steps), "beats; dropped:", " ".join(dropped))
