# index-approach.html: the deck in the order of slide 3's six steps, each slide's header, the overview, the sections menu and
# the renders' kicker labelled with its step. The live deck's slides are untouched; app.js only learns to take a page's own
# section names (window.ACKO_SECTIONS), which the live deck doesn't set, so it reads as before.
import sys, os, re, json
sys.path.insert(0, "tools")
os.chdir(sys.argv[1])
import build

# ---- app.js: a page may name its own sections (additive; without ACKO_SECTIONS nothing changes)
p = "assets/js/app.js"
js = open(p, encoding="utf-8", newline="").read()
if "ACKO_SECTIONS" not in js:
    R = [
        ('const PARTS = { cover: "Opening", 1: "Design concept", 2: "Design strategy", 3: "Visual direction", 4: "Value addition", 5: "Layout", 6: "Walkthrough", A: "Appendix", 0: "About SKV" };',
         'const SECT = window.ACKO_SECTIONS || {};   // a page may name its own sections (index-approach.html); the deck itself doesn\'t\n'
         '  const PARTS = Object.assign({ cover: "Opening", 1: "Design concept", 2: "Design strategy", 3: "Visual direction", 4: "Value addition", 5: "Layout", 6: "Walkthrough", A: "Appendix", 0: "About SKV" }, SECT.names || {});'),
        ('const TOPICS = { main: [["1", "Design concept"], ["2", "Design strategy"], ["5", "Layout"], ["3", "Visual direction"], ["4", "Value addition"], ["6", "Walkthrough"]], appendix: [["A", "Appendix"]], skv: [["0", "About SKV"]] };',
         'const TOPICS = { main: SECT.main || [["1", "Design concept"], ["2", "Design strategy"], ["5", "Layout"], ["3", "Visual direction"], ["4", "Value addition"], ["6", "Walkthrough"]], appendix: [["A", "Appendix"]], skv: [["0", "About SKV"]] };'),
        ('$("#wk-kick").textContent = `Visual Direction · ${',
         '$("#wk-kick").textContent = `${(SECT.names && SECT.names[sc.dataset.part]) || "Visual Direction"} · ${'),
    ]
    for a, b in R:
        assert js.count(a) == 1, a[:60]
        js = js.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(js)

STEPS = [("s1", "Belonging"), ("s3", "The Site"),     # 12 Nov (Ritika: "remove the loop in agenda"): five parts; the Loop answers inside Belonging
             # STORY.md (11 Nov): six acts; Belonging first, the question, then the Loop, the answer (Ritika)
         ("s4", "The Plan"), ("s5", "The Feel"), ("s6", "The Day")]
LAB = {k: "%02d · %s" % (i + 1, n) for i, (k, n) in enumerate(STEPS)}
LAB["A"] = "Appendix · Kit of parts"
# the opening: her pick of index-open.html (gen_open.py) once it is slides/s-open.html; until then option 1 stands in
OPEN = "s-open" if os.path.exists("slides/s-open.html") else "s-open-1"
if OPEN != "s-open": print("note: slides/s-open.html isn't there yet, so the deck opens on", OPEN)
# 11 Nov (Ritika): the concept changes and the deck opens on ACKO's own Möbius. The story, in one positive run:
#   01 The Loop: ACKO's mark and what it means (infinite trust, inclusivity, collaboration, always us with you); a loop connects and
#      surrounds us; many lines of business, one loop, like a campus; its bridges hold (security, protection); then the Möbius
#   02 Belonging: 58% come back to the office to belong + the brief, a Modern Indian Institution = a campus; …maybe we've felt
#      this before (the memories, closing on ACKO's promise of protection and one floor in Koramangala)
#   03 The Site: the site, the floor's due diligence and sun, the two pitches, the long floor as an opportunity
#   04 The Plan: the Loop lies down on that floor, the axo rises out of it, the walk, the layout and its neighbourhoods
#   05 The Palette: the campus palette, the materials
#   06 The Experience: the emotions (Acker's engagement points), the renders, the walkthrough, a day in ACKO
#   then Thank you, where the Loop folds back into the Möbius. The kit of parts (acoustic, wayfinding, typologies) goes to the
#   appendix; How we worked, Where it starts and the people's challenge (problem first) leave the order, their files kept
AGENDA_Q = ["why people come in", "where it must happen", "how the floor becomes a campus", "what it feels like", "can we live it"]

# the agenda called back at the start of every section (Ritika, 11 Nov: "call back this with every section start"): s-sec-1..6, made
# from s-start (Where it starts): the six parts, the others step back and this one stays lit, then its line
SECTIONS = [
    ("About <b>651 Ackers</b>, from two offices, onto one floor.", "So we began with them."),
    ("<b>One floor</b> in Koramangala: where it has to happen.", ""),
    ("<b>One loop</b>, seven stops, six neighbourhoods.", ""),
    ("What you <b>touch</b>, hear and find your way by.", ""),
    ("<b>Every stop</b>, built.", "From arrival to evening."),
]
_st = open("slides/s-start.html", encoding="utf-8").read()
_li = re.findall(r'<li style="--i:\d"><i></i><b>[^<]*</b><span class="hand">[^<]*</span></li>', _st)
assert len(_li) == 6, "start steps"
NPARTS = len(STEPS)
_ln = re.search(r'<div class="st-line"[^>]*>.*?</div>', _st).group(0)
for _n, (_line, _hand) in enumerate(SECTIONS, 1):
    _act = STEPS[_n - 1][1]; _id = "s-sec-%d" % _n
    c = _st
    for _old in _li[NPARTS:]: c = c.replace(_old + "\n", "").replace(_old, "")   # five parts now: the spare step goes
    c = c.replace("grid-template-columns: repeat(6, 1fr)", "grid-template-columns: repeat(%d, 1fr)" % NPARTS)
    for _k, (_old, (_, _name)) in enumerate(zip(_li, STEPS), 1):
        c = c.replace(_old, re.sub(r"<b>[^<]*</b><span class=\"hand\">[^<]*</span>", "<b>%02d</b><span class=\"hand\">%s</span>" % (_k, _name), _old), 1)
    c = c.replace(_ln, re.sub(r"<p>.*?</p><span class=\"hand\">.*?</span>", "<p>%s</p><span class=\"hand\">%s</span>" % (_line, _hand), _ln))
    c = c.replace('<small style="--i:0">Where it starts</small>', '<small style="--i:0">Part %02d · %s</small>' % (_n, _act))
    c = re.sub(r'data-title="[^"]*"', 'data-title="Part %02d · %s"' % (_n, _act), c, count=1)
    c = re.sub(r'data-notes="[^"]*"', 'data-notes="Part %02d of six: %s, %s. %s"' % (_n, _act, AGENDA_Q[_n - 1], re.sub("<[^>]+>", "", _line + " " + _hand).strip()), c, count=1)
    for _x, _y in (("li:not(:first-child)", "li:not(:nth-child(%d))" % _n), ("li:first-child i", "li:nth-child(%d) i" % _n), ('$(".ap-steps li i", sc)', '$(".ap-steps li:nth-child(%d) i", sc)' % _n)):
        assert c.count(_x) == 1, _x; c = c.replace(_x, _y)
    c = c.replace("s-start", _id)
    open("slides/%s.html" % _id, "w", encoding="utf-8", newline="\n").write(c)

# the renders in the Loop's order, each named by its stop and feeling (STORY.md, Act 6)
STOPS = [("Arrival", "I feel welcomed", "s-w-reception s-w-recoffee"),
         ("Café", "Hey, we finally meet!", "s-w-cafe1 s-w-cafe2 s-w-deck s-w-coffee"),
         ("Board Room", "This is my big moment", "s-w-board s-w-exec"),
         ("Meeting Rooms", "My impact", "s-w-dept s-w-sprint"),
         ("Collab", "Wow, worth the commute", "s-w-collab s-w-garden"),
         ("Work", "These are my folks!", "s-w-arena s-w-arena2a"),
         ("Wellness", "They thought of me too!", "s-w-mothers s-w-zen s-w-studio")]
GROUPS = [
    ("cover", "s-cover s-team s-agenda"),
    ("s1", "s-sec-1 s-challenge " + OPEN + " s-campus s-memories s-mobius s-loop-stops"),   # the Möbius and the seven stops close Belonging (12 Nov: "remove the loop in agenda")   # 12 Nov, Ritika: "belonging, people's challenge, ackos mark, where both meet, the memories, the loop card, mobius, 7 stops, site"
    ("s3", "s-sec-2 s-site s-layout-dd s-pitch s-challenges"),
    ("s4", "s-sec-3 s-loop-w s-strategy s-walk s-layout-sp"),
    ("s5", "s-sec-4 s-palette2 s-material s-acoustic s-wayfinding s-engage"),
    ("s6", "s-sec-5 " + " ".join(s for _, _, g in STOPS for s in g.split()) + " s-walkthrough s-wayday"),
    ("close", "s-thanks-w"),
    ("A", "s-typologies"),
    (None, "s-wellbeing s-di s-esg s-skv"),
]
# s-loop-stops: the Loop's first two beats (Welcome to the Loop, Where emotions matter), right after the memories; s-loop-w keeps all
# three at the start of 04 The Plan (a quick recap, then the floor)
_lw = open("slides/s-loop-w.html", encoding="utf-8").read().replace("s-loop-w", "s-loop-stops")
_a = 'data-steps="3"'; assert _lw.count(_a) == 1, "loop steps"
_lw = _lw.replace(_a, 'data-steps="2"').replace('data-beats="Welcome to the Loop,Where emotions matter,On the floor"', 'data-beats="Welcome to the Loop,Where emotions matter"')
open("slides/s-loop-stops.html", "w", encoding="utf-8", newline="\n").write(_lw)
GROUPS_10NOV = [
    ("cover", "s-cover s-team s-approach-w"),
    # problem first, then the solution (Ritika, 10 Nov: variation 1 of narrative-options.html, opening on the people's challenge):
    # 1 the people's problem, 2 what people want (the research and the brief meet: a campus; the memories; what if)
    # 02 · map the possibilities: empty (aspiration, brand and journey left out; typologies moved to the end of 06, Ritika, 6 Nov)
    # the six stages renumbered to this order (10 Nov): 01 understand the people … 06 layer the lenses (STEPS above)
    ("s1", "s-start s-challenge"),                 # Where it starts (its own slide, 10 Nov), then the people's challenge
    ("s2", "s-campus s-memories s-whatif"),
    # 3 the building's problem in one run: the site, the layout's due diligence and sun path, the pitches, the floor tilting into the vast floor
    ("s3", "s-site s-layout-dd s-pitch s-challenges"),
    ("s4", "s-mobius s-loop-w"),                      # 4 the idea, answering the vast floor: the Möbius, the Loop, laid on that floor
    ("s5", "s-strategy s-walk s-layout-sp"),          # 5 the proof: the Loop's floor rising into the strategy axo, the walk, flat again: the layout, Spaces on
    # the lenses (10 Nov): acoustics straight on from the Layout's Acoustics; then the two experience lenses; then palette → material
    # → the renders that show them built. Each answers a line of the challenge's promise (LENS below)
    ("s6", "s-acoustic s-wayfinding s-engage s-palette2 s-material"),
    # the renders in the design proposal's order (3 Nov PDF, gen_proposal.py, 10 Nov): the library isn't in it; the reception coffee
    # point, the outdoor deck and collab are new
    ("s6", "s-w-reception s-w-recoffee s-w-deck s-w-board s-w-dept s-w-sprint s-w-arena s-w-arena2a s-w-exec s-w-cafe1 s-w-cafe2 s-w-garden s-w-coffee s-w-collab s-w-mothers s-w-zen s-w-studio s-walkthrough s-typologies s-wayday"),
    ("close", "s-thanks-w"),
    (None, "s-wellbeing s-di s-esg s-skv"),
]
def make(out, swap=None, wi=None, hfix=None, move=None):
  """one page of the re-ordered deck; swap renames (or with None drops) slides, wi marks a What if option page (10 Nov); move puts a
  slide right after another, in that slide's part (12 Nov)"""
  swap = swap or {}; move = move or {}
  ORDER = [swap.get(i, i) for _, g in GROUPS for i in g.split() if swap.get(i, i)]
  _partof = {swap.get(i, i): p for p, g in GROUPS for i in g.split() if swap.get(i, i)}   # each slide's part, by its id on this page
  for _m, _after in move.items():                    # in order; a slide not in the groups is inserted (12 Nov: the wayfinding pair)
      if _m in ORDER: ORDER.remove(_m)
      ORDER.insert(ORDER.index(_after) + 1, _m); _partof[_m] = _partof[_after]
  live = [l.strip() for l in open("slides/order.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
  assert all(os.path.exists(os.path.join("slides", i + ".html")) for i in ORDER) and len(set(ORDER)) == len(ORDER)
  build.build(ORDER, out)

  h = open(out, encoding="utf-8").read()
  # each section's chapter
  for sid in ORDER:
          part = _partof[sid]
          if not part: continue
          h, n = re.subn(r'(<section\b[^>]*?\sid="%s"[^>]*?\sdata-part=")[^"]*(")' % sid, lambda m: m.group(1) + part + m.group(2), h, count=1)
          if not n:
              h, n = re.subn(r'(<section\b[^>]*?\sdata-part=")[^"]*("[^>]*?\sid="%s")' % sid, lambda m: m.group(1) + part + m.group(2), h, count=1)
          assert n, sid
  # each slide's header: its title, then its step (the old section names go)
  HDR = [
      ('<div class="hdr"><b>The Site</b><span>Layout</span></div>', "The Site", "s3"),
      ('<div class="hdr"><b>Design Strategy</b><span>Understanding how we derived a solution.</span></div>', "Workstation Typologies", "A"),
      ('<div class="hdr"><b>Design Strategy</b><span>What\'s our Challenge ?</span></div>', "The Opportunity", "s3"),
      ('<div class="hdr"><b>ESG Strategy</b><span>Value Addition | Kit of parts</span></div>', "Wayfinding", "s5"),
      ('<div class="hdr"><b>Acker’s engagement points</b><span>Value Addition | Kit of parts</span></div>', "Acker’s engagement points", "s5"),
      ('<div class="hdr"><b>The Campus Palette</b><span>Visual Direction</span></div>', "The Campus Palette", "s5"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Material Strategy</span></div>', "Material Strategy", "s5"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Acoustic Strategy</span></div>', "Acoustic Strategy", "s5"),
      ('<div class="hdr"><b>Schematic Axonometric</b><span>Space Planning &nbsp;| Wayfinding</span></div>', "A day in ACKO", "s6"),
  ]
  # the layout's header, once per copy: Due Diligence discovers the site (03), Spaces on shapes the plan (05)
  LY = '<div class="hdr"><b>Layout</b><span>Space Planning - Option 02A &nbsp;| Revised option</span></div>'
  for sid, step in (("s-layout-dd", "s3"), ("s-layout-sp", "s4")):
      i = h.index('id="%s"' % sid); j = h.index(LY, i)
      h = h[:j] + '<div class="hdr"><b>Layout · Option 02A</b><span>%s</span></div>' % LAB[step] + h[j + len(LY):]
  assert LY not in h
  for old, title, step in HDR:
      if old not in h: continue                        # a slide not in this page (index-story2.html)
      assert h.count(old) >= 1, old[:60]                 # the layout's twice (Due Diligence, then Spaces on)
      h = h.replace(old, '<div class="hdr"><b>%s</b><span>%s</span></div>' % (title, LAB[step]))
  # Where both meet opens on the question that bridges from the challenge (wow_campus.py, 10 Nov); its notes say it first
  _n = 'data-notes="Research: 58% of employees'
  assert h.count(_n) == (1 if 'id="s-campus"' in h else 0), "campus notes"   # (index-story2.html has no Where both meet since 17 Nov)
  h = h.replace(_n, 'data-notes="First the question: what makes one place feel like home? We looked at two things. Research: 58% of employees')
  # the page's own section names: the overview's headings, the sections menu, the renders' kicker
  names = dict(LAB); names["close"] = "Thank you"
  SECT = "<script>window.ACKO_WOW = true;   /* the big moments (9 Nov): this page only */</script>\n<script>window.ACKO_SECTIONS = %s;</script>\n" % json.dumps({"names": names, "main": [[k, dict(STEPS)[k], "%02d" % ([q for q, _ in STEPS].index(k) + 1)] for k in dict.fromkeys(k for k, _ in GROUPS) if k in dict(STEPS)] + [["close", "Thank you", ""]]}, ensure_ascii=False)   # the menu in the deck's order
  # How we worked, told the way this deck now runs, lives in its own copy: slides/s-approach-w.html (wow_approach.py, 10 Nov)
  tag = '<script src="assets/js/app.js'
  assert tag in h
  if wi:   # an option page: which one, and a small tag in the corner
      SECT += ('<script>window.ACKO_WI = "%s";</script>\n<div class="wi-tag">What if · %s</div><style>.wi-tag { position: fixed; left: 14px; bottom: 14px; z-index: 90; padding: 6px 10px; border-radius: 3px; background: #5222d0; color: #fff; font: 600 11px/1 var(--body); letter-spacing: .08em; text-transform: uppercase; pointer-events: none; }</style>\n' % (wi, wi.upper()))
  if hfix: h = hfix(h)
  h = h.replace(tag, SECT + tag, 1)
  open(out, "w", encoding="utf-8").write(h)
  print("ok", out, len(ORDER))

# ---- What if, folded into the memories (10 Nov: Ritika picked B, "the narrative is the gap"; wording: ACKO's own promise).
# The memories close on two more beats over the dimmed campus (wow_whatif.py): the feeling and ACKO's promise, then the question and
# where it has to happen; What if's own slide goes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wi_words import close
def fold(h):
    a = 'id="s-memories"'; i = h.index(a); j = h.index(">", i) + 1
    sec = h[h.rindex("<section", 0, i):j]
    new = sec.replace('data-steps="6"', 'data-steps="8"').replace('Study time,The stairs"', 'Study time,The stairs,The promise,What if"')
    new = new.replace("A campus is where we first felt safe among people.",
        "7 · A campus is where we first felt safe among people, and protection is what ACKO promises its customers. "
        "8 · So what if the workplace kept that promise to its own people? The answer was already in your mark.")
    assert new.count('data-steps="8"') == 1 and "The promise,What if" in new and "8 · So what if" in new, "memories head"
    h = h.replace(sec, new, 1)
    k = h.index('<div class="page">', j) + len('<div class="page">')
    return h[:k] + "\n    " + close() + h[k:]
# ---- the lenses keep the challenge's promise (10 Nov): "So we design a place that already feels like home: Teams together · Easy to
# find · Room to explore · Same rhythm". The Layout kept Teams together; each lens says, in the hand under its header, which line it keeps
# 11 Nov: the challenge's promise has left the order and acoustic and wayfinding are in the appendix; the lines that stay say what
# each slide gives in the Loop's own positive words
LENS = [("s-palette2", "A place that already feels like home."), ("s-material", "A place that already feels like home."),
        ("s-acoustic", "Same rhythm."), ("s-wayfinding", "Easy to find."), ("s-engage", "Room to explore.")]
LENS_CSS = ('<style>.scene .page > .lens-cb { left: 1.8%; top: 10%; margin: 0; font-family: var(--hand); font-size: calc(var(--pt) * 13); '
            'line-height: 1; color: var(--purple); white-space: nowrap; }</style>\n')
def lenses(h):
    for sid, line in LENS:
        if 'id="%s"' % sid not in h: continue   # not in this page
        a = 'id="%s"' % sid; i = h.index(a); j = h.index(">", i) + 1
        sec = h[h.rindex("<section", 0, i):j]
        n = re.search(r'data-notes="', sec)
        if n: h = h.replace(sec, sec[:n.end()] + line + " " + sec[n.end():], 1); j = h.index(">", i) + 1
        k = h.index(">", h.index('<div class="page', j)) + 1            # its page, whatever its classes ("page rv")
        h = h[:k] + '\n    <p class="lens-cb">%s</p>' % line + h[k:]
    t = '<script src="assets/js/app.js'
    return h.replace(t, LENS_CSS + t, 1)
# ---- the long floor as an opportunity (11 Nov, Ritika: "make sure the whole narrative is positive"): the same drawing (the uniform
# desks, the long way round, the dead ends), now named as what the plan turns around; draft words, hers to confirm
OPP = [
    ("data-title=\"What's our challenge\"", 'data-title="The opportunity"'),
    ('data-beats="Homogeneity,Distance,Disorientation,A campus that connects"', 'data-beats="Identity,Closeness,Clarity,A campus that connects"'),
    ('One vast floor, a thousand disconnected experiences. 1 · Homogeneity: a repetitive, uninterrupted workstation layout makes a uniform environment with little spatial identity. 2 · Distance: from a desk at the far end, the way to the café is a long walk, along the aisles; the elongated plate weakens the sense of direction, making navigation and wayfinding challenging. 3 · Disorientation: on the way, dead ends and a question; the amenities feel disconnected from the work zones, so distances feel longer and people meet less by chance. 4 · So: a campus that connects, not just accommodates.',
     'One long floor, room for a whole campus. The drawing shows the floor as any plan would fill it; each beat names what our plan turns around. 1 · Identity: instead of one uniform sea of desks, neighbourhoods with a character of their own. 2 · Closeness: from a desk at the far end the café is a long walk today; we bring it, the green and the meeting rooms within easy reach. 3 · Clarity: instead of dead ends and guesswork, one clear path that always tells you where you are. 4 · A campus that connects, not just accommodates.'),
    ('>One vast floor. A thousand disconnected experiences.<', '>One long floor. Room for a whole campus.<'),
    ('>Homogeneity<', '>Identity<'),
    ('>A repetitive, uninterrupted workstation layout creates a uniform environment with limited spatial identity.<', '>From one uniform sea of desks to neighbourhoods, each with a character of its own.<'),
    ('>Distance<', '>Closeness<'),
    ('>The elongated floor plate weakens the sense of direction, making navigation and wayfinding challenging.<', '>From a long walk to a short one: the café, the green and the meeting rooms within easy reach of every desk.<'),
    ('>Disorientation<', '>Clarity<'),
    ('>Amenities feel disconnected from work zones, increasing perceived distances and reducing spontaneous interaction.<', '>From dead ends to one clear path, so everyone always knows where they are, and meets along the way.<'),
]
# ---- STORY.md (11 Nov): the bridge into the next slide, said last (in the notes, N); the renders named by their stop and feeling;
# Where it starts re-labelled to the six acts, with 02 Belonging the one that stays
BRIDGE = {
    "s-team": "And it starts with something you already own.",
    "s-agenda": "Let's begin with the people. Part 1.",
    "s-sec-1": "Moving offices is easy. Moving people isn't.", "s-sec-2": "Regalium, Koramangala.",
    "s-sec-3": "The Loop, laid on the floor.", "s-sec-4": "Starting with the palette.", "s-sec-5": "Arrival first.",
    "s-open": "So what makes one place feel like home? We looked at two things.",
    "s-mobius": "So we gathered those campus moments into seven stops on one loop.",
    "s-mark": "So we gathered those campus moments into seven stops on one loop.",
    "s-challenge": "And the promise already lives in ACKO's own mark…",
    "s-campus": "And most of us have been here before…",
    "s-memories": "The answer was in your own mark.",
    "s-loop-stops": "A loop needs a ground. Part 2.",
    # the concept note's three (17 Nov, index-story2.html only: index-approach.html doesn't have them)
    "s-why-campus": "So how does a floor this long hold together? With something ACKO already stands for.",
    "s-campus-loop": "Here it is on our floor.",
    "s-loop-floor": "Most of us have felt this before…",
    "s-heard": "So we began with the people. Part 1.",
    "s-site": "Here is the floor itself, as we found it.",
    "s-layout-dd": "To feel how big this floor is…",
    "s-pitch": "That length could divide people, or hold a whole campus.",
    "s-challenges": "A campus that connects, not just accommodates. Part 3: how the floor becomes one.",
    "s-loop-w": "Now we build the campus up around it.",
    "s-strategy": "Let's step onto the floor and walk it.",
    "s-walk": "And from above, here's the plan that makes it work.",
    "s-layout-sp": "A plan is a promise on paper. Part 4: what makes it feel like home.",
    "s-palette2": "And how each surface earns its place…",
    "s-material": "Calm needs quiet: the floor's own rhythm.",
    "s-acoustic": "And on a floor this long, finding your way should be effortless.",
    "s-wayfinding": "Materials make it feel like home. People make it feel alive: where emotions matter.",
    "s-engage": "So let's live it. Part 5.",
    "s-w-studio": "That's every stop. Now watch them come alive.",
    "s-walkthrough": "And over one day…",
    "s-wayday": "And at the end of the day, the loop comes back to where it began.",
}
STOP_OF = {s: (n, f) for n, f, g in STOPS for s in g.split()}
START_ACTS = [(k, n) for k, n in STEPS]
def storyfix(h):
    import html as _h
    # bridges, at the end of the notes
    for sid, line in BRIDGE.items():
        if 'id="%s"' % sid not in h: continue   # a slide not in this order
        a = h.index('id="%s"' % sid); i = h.rindex("<section", 0, a); j = h.index(">", a) + 1
        sec = h[i:j]; m = re.search(r'data-notes="([^"]*)"', sec)
        new = sec[:m.end(1)] + " → Bridge: " + _h.escape(line, quote=True) + sec[m.end(1):] if m else sec.replace("<section", '<section data-notes="Bridge: %s"' % _h.escape(line, quote=True), 1)
        h = h[:i] + new + h[j:]
    # the renders: the stop in the small title, its feeling as the quote
    for sid, (stop, feel) in STOP_OF.items():
        a = h.index('id="%s"' % sid); i = h.rindex("<section", 0, a); j = h.index(">", a) + 1
        sec = h[i:j]; m = re.search(r'data-walk="([^"]*)"', sec); assert m, sid
        w = json.loads(_h.unescape(m.group(1)))
        w["sub"] = stop + (" · " + w["sub"] if w.get("sub") else ""); w["q"] = feel
        h = h[:i] + sec[:m.start(1)] + _h.escape(json.dumps(w, ensure_ascii=False), quote=True) + sec[m.end(1):] + h[j:]
    return h

def opportunity(h):
    a = h.index('id="s-challenges"'); i = h.rindex("<section", 0, a); j = h.index("</section>", a)
    sec = h[i:j]
    for x, y in OPP:
        assert sec.count(x) == 1, x[:50]
        sec = sec.replace(x, y)
    return h[:i] + sec + h[j:]
make("index-approach.html", {"s-whatif": None}, hfix=lambda h: storyfix(opportunity(lenses(fold(h)))))

# ---- index-story2.html (12 Nov, Ritika: "spot the places where there's gap in the narrative … do these changes in a new html"): the
# same deck with the review's fixes, on this page only (index-approach.html stays as approved). Text: the mark as ACKO's promise, the
# memories closing on "That promise is a loop", the join said on the way into the seven stops, the agenda's subtitle, the bridges.
# Order: Walk the Loop out ("walk the loop 7 moments can be removed"); the Acoustic strategy slide out, its points folded into the
# layout's Acoustics beat ("retain the layout's acoustic and include the extra information"). The layout's six neighbourhood sheets
# leave the click order: a click on a neighbourhood opens its sheet, → goes on to the next, "Back to layout" / Esc returns
# ("if I click on a neighbourhood the individual boundary and axo page would open …")
def _sec(h, sid):
    a = h.index('id="%s"' % sid); i = h.rindex("<section", 0, a); return i, h.index("</section>", a)
def _in_sec(h, sid, x, y, n=1):
    i, j = _sec(h, sid); s = h[i:j]; assert s.count(x) >= n, (sid, x[:50]); return h[:i] + s.replace(x, y) + h[j:]
def _bridge(h, sid, text):
    i, j = _sec(h, sid); s = h[i:j]; k = s.index(">") + 1; tag = s[:k]
    tag2, c = re.subn(r"→ Bridge: [^\"]*", lambda m: "→ Bridge: " + text.replace("'", "&#x27;"), tag, count=1); assert c, sid
    return h[:i] + tag2 + s[k:] + h[j:]
AC_MORE = ('<ul class="ac-more"><li><b>NRC 0.70–0.90</b> across the floor</li><li>Ceiling treatment in meeting rooms for <b>RT60</b></li>'
           '<li>Absorptive wall panels for speech clarity</li><li>Full-height partitions to the right <b>STC</b></li>'
           '<li>HVAC noise held to zone <b>NC</b> targets</li><li>Sound masking, so focus holds</li><li>Acoustic doors and double glazing</li></ul>'
           '<p class="ac-note">An acoustic consultant can refine the specification.</p>')
SP2_CSS = ('<style>#s-layout-sp .ac-more { margin: calc(var(--pt) * 4) 0 0; padding-left: 1.1em; columns: 2; column-gap: 1.4em; font-size: calc(var(--pt) * 7.6); line-height: 1.4; color: #444; }'
           '#s-layout-sp .ac-more b { color: var(--purple); } #s-layout-sp .ac-note { font-size: calc(var(--pt) * 7); color: #888; font-style: italic; margin-top: calc(var(--pt) * 2) !important; }'
           '#s-layout-sp .sp2-nav { display: none; left: 34%; top: 3.4%; z-index: 7; align-items: center; gap: calc(var(--pt) * 8); }'
           '#s-layout-sp.nb-open .sp2-nav { display: flex; }'
           '#s-layout-sp .sp2-nav button { border: 1px solid #d6cdf3; background: #fff; color: var(--purple); border-radius: 999px; padding: calc(var(--pt) * 2.4) calc(var(--pt) * 9); font: 600 calc(var(--pt) * 8) var(--body); cursor: pointer; }'
           '#s-layout-sp .sp2-nav button:hover { background: #f3effd; } #s-layout-sp .sp2-nav b { font-size: calc(var(--pt) * 8.5); color: #333; }</style>\n')
SP2_JS = '''
  // the sheets on demand (12 Nov): a click opens a neighbourhood's sheet; → / Next goes on to the next; Back / Esc returns to the layout
  let SH = null; const NBS = ["01", "02", "03", "04", "05", "06"];
  function nbOpen(sc, n) { SH = String(n).padStart(2, "0"); closeZone(sc); sheet(sc, SH); sc.classList.add("nb-open"); $(".sp2-nav b", sc).textContent = "Neighbourhood " + SH + " of 06"; }
  function nbClose(sc) { if (!SH) return; SH = null; sc.classList.remove("nb-open"); sheet(sc, null); plan.planHome(home(), 700); }
  function nbStep(sc, d) { const i = NBS.indexOf(SH) + d; if (i < 0 || i >= NBS.length) nbClose(sc); else nbOpen(sc, NBS[i]); }
'''
# Campus strategy, beat 4 "Looping it all Together" (12 Nov): the Loop's ribbon, as The Loop lays it on the floor (its smoothing and
# its hooks, taken from slides/s-loop-w.html), built as a strip on the 3D floor so it turns and zooms with the model, drawing itself
# along its length after the partitions rise; the seven stops called out (the slide's own labels) as the ribbon reaches each
_LWSRC = open("slides/s-loop-w.html", encoding="utf-8").read()
_LWFN = _LWSRC[_LWSRC.index("  function resample(P, n) {"):_LWSRC.index("  function rib(cv, pts, wid) {")]
RIB_JS = _LWFN + r"""
  // the Loop as a path on the floor (12 Nov, Ritika: "loop ribbon is not looking like a path. it is not blending with the axos angle"):
  // the employees' route along the corridors through the seven stops (ACKO_LOOP.sweep, plan mm → model mm as flatten() has it), its
  // corners lightly rounded, lying on the floor in the model (walls overlap it), a deeper tone of the floor's circulation lilac on a
  // paler, wider edge strip; round ends
  const RW = 1.2, RY = 0.06;   // 12 Nov: sleeker; 18 Nov: a little fuller, as a marker stroke
  // 18 Nov (Ritika: "a conceptual loop path, not a defined path, which connects all the spaces"): every point of the Loop (both lanes, the faint
  // lane, the call-outs' points) is moved by one smooth field, so the lanes stay parallel and the ring reads as a loose hand-drawn stroke
  const hd = (p) => [p[0] + 1.2 * Math.sin(p[1] / 8 + 1) + 0.7 * Math.sin(p[0] / 23 + 2), p[1] + 1.2 * Math.sin(p[0] / 9 + 0.4) + 0.7 * Math.sin(p[1] / 25 + 3)];
  const hdMm = (x, y) => { const X0 = M.X(x), Z0 = M.Z(y), q = hd([X0, Z0]); return [x + (q[0] - X0) * 1000, y + (q[1] - Z0) * 1000]; };
  function chaikin(P, it) { for (let k = 0; k < it; k++) { const Q = [P[0]];
    for (let i = 0; i + 1 < P.length; i++) { const a = P[i], b = P[i + 1]; Q.push([0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]], [0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]]); }
    Q.push(P[P.length - 1]); P = Q; } return P; }
  function strip(P, wid, y, col, op, ro, off, flat) {
    const n = P.length, ss = [0]; for (let i = 1; i < n; i++) ss.push(ss[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
    const L = ss[n - 1], R = wid / 2;
    const E = P.map((p, i) => {
      const a = P[Math.max(0, i - 1)], b = P[Math.min(n - 1, i + 1)], dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz) || 1;
      const u = flat ? 1 : Math.min(1, Math.min(ss[i], L - ss[i]) / R), w = R * Math.sqrt(Math.max(0, 1 - (1 - u) * (1 - u)));   // a round end (none on the closed ring)
      return [[p[0] - dz / l * w, p[1] + dx / l * w], [p[0] + dz / l * w, p[1] - dx / l * w]];
    });
    const pos = []; for (let i = 0; i + 1 < n; i++) { const [a, b] = E[i], [c, d] = E[i + 1]; for (const q of [a, b, c, b, d, c]) pos.push(q[0], y, q[1]); }
    const geo = new T.BufferGeometry(); geo.setAttribute("position", new T.Float32BufferAttribute(pos, 3)); geo.setDrawRange(0, 0);
    const m = new T.Mesh(geo, new T.MeshBasicMaterial({ color: col, transparent: true, opacity: op, side: T.DoubleSide, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: off, polygonOffsetUnits: 2 * off }));
    m.renderOrder = ro; m.visible = false; m.frustumCulled = false; return m;
  }
  // 17 Nov (the 16 Nov concept note: "a path with two ends is a corridor with dead ends … redraw the campus strategy route as the same
  // loop"): the ribbon is the Loop as ONE closed ring (ACKO_LOOP.ring), as The loop on our floor draws it: the main street out and back
  // as two lanes (each point set 0.8 m to the ring's left: it runs clockwise, so out east the lane is north of the street, back west
  // south of it), round the meeting island at each end, no ends; the lane 02A has yet to open (ringDash) faint; each stop's call-out on
  // the ring, at its share of the way round
  // 18 Nov (Ritika: "the loop should connect all spaces and look like a loop"; "in the corridor zone, no branching out; the spaces should
  // come in the loop's path"; "first show the arrival arrow and the loop should start from them"): the Loop is the corridor route itself
  // (ACKO_LOOP.ring: the main street out and back, through the seven stops, past the spaces), as ONE closed ring, its two directions parted
  // into lanes 3 m apart so it reads as an oval track, eased, with only a faint hand-drawn tremor. It is split at the two entrances
  // (Arrival 1 and 2, where the maroon arrows stand) into two arcs that draw together, each growing out of its own arrow and meeting at the
  // other. No spurs: each space's dot is the nearest point on the ring, so the spaces sit on the path.
  function ribbon() {
    if (S.rb !== undefined) return S.rb;
    S.rb = null;
    const LP = window.ACKO_LOOP; if (!LP || !LP.ring || !M || typeof spaces !== "function") return null;
    const N = LP.ring.length, LANE = 1500, ARR = (LP.ringStops || []).filter((s) => s.kind === "arrival").map((s) => s.i);
    if (ARR.length < 2) return null;
    const A1 = ARR[0], A2 = ARR[1];
    let C = LP.ring.map((p) => p.slice());
    for (let it = 0; it < 6; it++) C = C.map((p, i) => { const a = C[(i - 1 + N) % N], b = C[(i + 1) % N]; return [0.25 * a[0] + 0.5 * p[0] + 0.25 * b[0], 0.25 * a[1] + 0.5 * p[1] + 0.25 * b[1]]; });
    const OFF = C.map((p, i) => { const a = C[(i - 1 + N) % N], b = C[(i + 1) % N], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      return [p[0] + (dy / l) * LANE, p[1] - (dx / l) * LANE]; });
    const seq = (i0, i1) => { const o = []; for (let i = i0; ; i = (i + 1) % N) { o.push(OFF[i]); if (i === i1) break; } return o; };
    const tremor = (p) => { const h = hd(p); return [p[0] + (h[0] - p[0]) * 0.2, p[1] + (h[1] - p[1]) * 0.2]; };
    const prep = (Q, m) => resample(chaikin(Q.map((q) => [M.X(q[0] - 185842), M.Z(q[1] + 182802)]).filter((p, i, A) => !i || Math.hypot(p[0] - A[i - 1][0], p[1] - A[i - 1][1]) > 0.05), 4), m).map(tremor);
    // the ring's length from Arrival 1 round to each point, to split it into the two arcs
    const cum = [0]; for (let i = 1; i < N; i++) cum.push(cum[i - 1] + Math.hypot(OFF[i][0] - OFF[i - 1][0], OFF[i][1] - OFF[i - 1][1]));
    const L = cum[N - 1] + Math.hypot(OFF[0][0] - OFF[N - 1][0], OFF[0][1] - OFF[N - 1][1]), sOf = (j) => (cum[j] - cum[A1] + L) % L, sA = sOf(A2);
    const nA = Math.max(200, Math.round(1600 * sA / L)), nB = Math.max(200, 1600 - nA);
    const arcs = [prep(seq(A1, A2), nA), prep(seq(A2, A1), nB)].map((P) => ({ P, n: P.length,
      under: strip(P, RW + 0.35, RY - 0.01, 0xd9cbfa, 0.9, 8, -4, true), top: strip(P, RW, RY, 0x8f6cf0, 0.9, 9, -6, true) }));
    arcs.forEach((a) => M.scene.add(a.under, a.top));
    // each place's share of ITS arc (the stroke front growing out of the nearer arrow reaches it then) and its point on the ring (model mm)
    const share = (j) => { const s0 = sOf(j); return s0 <= sA ? s0 / sA : (s0 - sA) / (L - sA); };
    const idx = {};
    (LP.ringStops || []).forEach((s) => { if (s.kind === "stop") idx[s.name] = s.i; });
    const at = M.data.stops.map((s) => (idx[s.name] === undefined ? 1 : Math.min(1, share(idx[s.name]))));
    const pos = M.data.stops.map((s) => (idx[s.name] === undefined ? null : [C[idx[s.name]][0] - 185842, C[idx[s.name]][1] + 182802]));
    const hot = spaces().map((q) => { let j = 0, d0 = 1e18; for (let i = 0; i < N; i++) { const d = (C[i][0] - 185842 - q.x) ** 2 + (C[i][1] + 182802 - q.y) ** 2; if (d < d0) { d0 = d; j = i; } }
      return { at: Math.min(1, share(j)), pos: [C[j][0] - 185842, C[j][1] + 182802] }; });
    // white chevrons say which way each arc runs
    const ar = [];
    arcs.forEach((a, ai) => (ai ? [0.2, 0.5, 0.8] : [0.5]).forEach((f) => {
      const P = a.P, n = a.n, j = Math.round(f * (n - 1)), p0 = P[Math.max(0, j - 6)], p1 = P[Math.min(n - 1, j + 6)], dx = p1[0] - p0[0], dz = p1[1] - p0[1], l = Math.hypot(dx, dz) || 1, ux = dx / l, uz = dz / l, c = P[j], Ln = 1.5, W = 0.95, Y = RY + 0.03;
      const g = new T.BufferGeometry(); g.setAttribute("position", new T.Float32BufferAttribute([c[0] + ux * Ln, Y, c[1] + uz * Ln, c[0] - ux * Ln * 0.5 - uz * W, Y, c[1] - uz * Ln * 0.5 + ux * W, c[0] - ux * Ln * 0.5 + uz * W, Y, c[1] - uz * Ln * 0.5 - ux * W], 3));
      const m = new T.Mesh(g, new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.95, side: T.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -8, polygonOffsetUnits: -16 }));
      m.renderOrder = 10; m.visible = false; m.frustumCulled = false; M.scene.add(m); ar.push({ m, f, ai });
    }));
    const show = (on) => { arcs.forEach((a) => { a.under.visible = on; a.top.visible = on; }); if (!on) ar.forEach((x) => { x.m.visible = false; }); };
    const to = (e) => { arcs.forEach((a) => { const k = Math.max(0, Math.min(a.n - 1, Math.round(e * (a.n - 1)))); a.under.geometry.setDrawRange(0, 6 * k); a.top.geometry.setDrawRange(0, 6 * k); });
      ar.forEach((x) => { x.m.visible = arcs[0].top.visible && e >= x.f + 0.01; }); };
    // a fade of the whole ring and its chevrons (1 = as drawn), for the Detailed axo's glide into A day in ACKO
    const fade = (a) => { arcs.forEach((x) => { x.under.material.opacity = 0.9 * a; x.top.material.opacity = 0.9 * a; }); ar.forEach((x) => { x.m.material.opacity = 0.95 * a; }); };
    return (S.rb = { show, to, fade, at, pos, hot, miss: at.map(() => 0) });
  }
"""
FROM_CSS = ('<style>#s-strategy .st-from { left: 0; top: 1%; width: 89.8%; height: 98.4%; pointer-events: none; opacity: 0;'
            ' background: url(assets/img/challenge-axo.webp) 100% 0 / 111.4% 100% no-repeat; transform-origin: 93.15% 0; transform: scale(.95); }'
            '#s-layout-sp .ly-p[data-p="1"] p:not(.hand), #s-layout-sp .nb-p { display: none; }</style>\n')
def axo_handoff(h):
    # 12 Nov (Ritika: "the transition of these 2 axos can be smooth. now it looks like 2 different slides"): The Opportunity marks the
    # hand-off as it leaves; Campus strategy holds that axo picture over its own floor, the shell already standing, then dissolves it
    h = _in_sec(h, "s-strategy", '<div class="st-3d ui"></div>', '<div class="st-3d ui"></div>\n    <div class="st-from"></div>')
    a = h.index('ACKO.slide("s-challenges"'); b = h.index("</script>", a); js = h[a:b]
    x = "    leave(_, sc) { stop(); S.arr = false;"
    assert js.count(x) == 1, "challenges leave"; h = h[:a] + js.replace(x, '    leave(_, sc) { if (window.ACKO_MORPH) ACKO_MORPH.mark("s-challenges"); stop(); S.arr = false;') + h[b:]
    a = h.index('ACKO.slide("s-strategy"'); b = h.index("</script>", a); js = h[a:b]
    R = [('      const fl = window.ACKO_WOW && window.ACKO_MORPH && !reduced ? window.ACKO_MORPH.take("s-loop-w") : null;',
          '      const fc = window.ACKO_WOW && window.ACKO_MORPH && !reduced ? window.ACKO_MORPH.take("s-challenges", 2500) : null;\n'
          '      const im = $(".st-from", sc); im.style.transition = "none"; im.style.opacity = fc ? 1 : 0; S.fromCh = !!fc;\n'
          '      if (fc) later(() => { im.style.transition = "opacity 1.3s var(--ease)"; im.style.opacity = 0; }, 500);\n'
          '      const fl = window.ACKO_WOW && window.ACKO_MORPH && !reduced ? window.ACKO_MORPH.take("s-loop-w") : null;'),
         ("  function play(k) {\n", "  function play(k) {\n    if (k === 1 && S.fromCh) { S.fromCh = false; show(1); return; }   // from The Opportunity: the shell already stands\n"),
         ("ACKO.slide(\"s-strategy\", ({ $, $$, reduced, plain, reveal, cue, plan }) => {", "ACKO.slide(\"s-strategy\", ({ $, $$, reduced, plain, reveal, cue, plan, later }) => {")]
    for p, q in R:
        assert js.count(p) == 1, ("strategy js 3", p[:60], js.count(p)); js = js.replace(p, q)
    h = h[:a] + js + h[b:]
    t2 = '<script src="assets/js/app.js'
    return h.replace(t2, FROM_CSS + t2, 1)
def strat_loop(h):
    a = h.index('ACKO.slide("s-strategy"'); b = h.index("</script>", a); js = h[a:b]
    R = [("  const DUR = [0, 2.4, 4.4, 6.4, 2.4, 4.2, 7.0];\n", "  const DUR = [0, 2.4, 4.4, 6.4, 7.5, 4.2, 7.0];   // beat 4 longer: the Loop's ribbon draws on after the partitions (12 Nov)\n"),
         ("    S.lit = M.data.stops.map((s) => k === 6 && S.d >= s.d - 0.5);",
          "    const RB = ribbon(), re = k === 4 ? win(t, 1.5, 6.5) : 0;   // 12 Nov: slower, as Ritika asked; 18 Nov: after the arrows have landed\n"
          "    if (RB) { RB.show(k === 4 && re > 0.001); RB.to(re); }\n"
          "    S.lit = M.data.stops.map((s, i) => (k === 6 && S.d >= s.d - 0.5) || (k === 4 && !!RB && re > 0.001 && re >= RB.at[i] - 0.002));"),
         ("  function show(k) {", RIB_JS + "  function show(k) {"),
         ("    leave() { if (window.ACKO_MORPH) ACKO_MORPH.mark(\"s-strategy\");", "    leave() { if (window.ACKO_MORPH) ACKO_MORPH.mark(\"s-strategy\"); if (S.rb) S.rb.show(false);"),
         ("employee: M.routes.employee.geometry.drawRange.count,", "employee: M.routes.employee.geometry.drawRange.count, rb: S.rb ? { at: S.rb.at, miss: S.rb.miss } : null,"),
         # 17 Nov (the concept note): on beat 4 the call-outs sit on the ring itself ("if a node isn't on the loop, it's wrong"); the
         # Arrival an open ring, the commons filled nodes
         ("      const [x, y] = px(o.s.x, o.s.y, 0.6);",
          "      const q = S.k === 4 && S.rb && S.rb.pos && S.rb.pos[i] ? S.rb.pos[i] : [o.s.x, o.s.y]; const [x, y] = px(q[0], q[1], 0.6);"),
         ("g.innerHTML = '<path/><circle r=\"5\"/>'; svg.appendChild(g);",
          "g.innerHTML = '<path/><circle r=\"5\"/>'; if (s.name === \"Arrival\") g.classList.add(\"arr\"); svg.appendChild(g);")]
    for x, y in R:
        assert js.count(x) == 1, ("strategy js", x[:60], js.count(x)); js = js.replace(x, y)
    h = h[:a] + js + h[b:]
    t2 = '<script src="assets/js/app.js'
    h = h.replace(t2, '<style>#s-strategy .st-legs g.arr circle { fill: #fff; stroke: #1a1a2e; stroke-width: 2.4; }</style>\n' + t2, 1)
    return _in_sec(h, "s-strategy", "4 Looping it all together: the floor in colour and the partitions rise.",
                   "4 Looping it all together: conceptual massing, the neighbourhoods as hand-drawn masses, no walls, then the Loop lies down as a loose hand-drawn stroke, one closed ring, the same loop as on our floor: the main street both arrivals open onto, out and back, round the meeting island at each end, no dead ends; its seven stops called out with their words as it reaches each. The faint stretch is the lane 02A has yet to open.")

# Campus strategy (12 Nov): beat 1 is The Shell (the planning has begun on the slide before); beat 5 calls out the client's touchpoints
# where the blue route reaches them (model mm, d m along the route, as data/axo-layers.js has it; named from the plan's rooms there)
CLIENT_JS = """  const CLIENT = [{ name: "Reception", q: "I was expected", x: -97319, y: 216565, d: 10.1 },
    { name: "Visitor Hub · Board Room", q: "A room ready for me", x: -77629, y: 217623, d: 30.3 },
    { name: "Reception · East", q: "Welcome at either door", x: -9798, y: 222950, d: 40.3 },
    { name: "Collab", q: "I see who ACKO is", x: 1914, y: 221390, d: 24.8 }].map((s) => Object.assign(s, { client: true }));
"""
def strat_more(h):
    a = h.index('ACKO.slide("s-strategy"'); b = h.index("</script>", a); js = h[a:b]
    R = [('const NAMES = ["", "How it started",', 'const NAMES = ["", "The Shell",'),
         ('"Every journey begins with a thought. Ours began with reimagining what a workplace could feel like."',
          '"One long floor and two entrances: the ground the Loop is laid on."'),
         ("  const MARKS = {", CLIENT_JS + "  const MARKS = {"),
         ("    S.labs = A.stops.map((s) => {", "    S.labs = A.stops.concat(CLIENT).map((s) => {"),
         ('d.innerHTML = `<b>${s.name}</b><span>${STOPS[s.name] || ""}</span>`;', 'd.innerHTML = `<b>${s.name}</b><span>${s.q || STOPS[s.name] || ""}</span>`; if (s.client) d.classList.add("cl");'),
         ("    S.lit = M.data.stops.map((s, i) => (k === 6 && S.d >= s.d - 0.5) || (k === 4 && !!RB && re > 0.001 && re >= RB.at[i] - 0.002));",
          "    const cd = k === 5 ? cli.userData.max * win(t, 0.3, DUR[5] - 0.2) : 0;\n"
          "    S.lit = S.labs.map((o, i) => o.s.client ? k === 5 && cd >= o.s.d - 0.5 : (k === 6 && S.d >= o.s.d - 0.5) || (k === 4 && !!RB && re > 0.001 && re >= RB.at[i] - 0.002));")]
    for x, y in R:
        assert js.count(x) == 1, ("strategy js 2", x[:60], js.count(x)); js = js.replace(x, y)
    h = h[:a] + js + h[b:]
    i, j = _sec(h, "s-strategy"); s = h[i:j]
    for x, y in [('data-beats="How it started,', 'data-beats="The Shell,'),
                 ("1 How it started: the bare shell", "1 The shell: the bare floor we were given"),
                 ("5 The client's journey: the client's route from the entrance.", "5 The client's journey: the client's route from the entrances, its touchpoints called out: Reception, the Visitor Hub and Board Room, the east Reception, Collab.")]:
        if x not in s: x = x.replace("'", "&#x27;"); y = y.replace("'", "&#x27;")
        assert x in s, ("strategy head", x[:50]); s = s.replace(x, y, 1)
    h = h[:i] + s + h[j:]
    css = '<style>#s-strategy .st-s.cl b { color: #1a2cf0; }</style>\n'
    t2 = '<script src="assets/js/app.js'
    return h.replace(t2, css + t2, 1)

def story2(h):
    # the order: the plan's walk and the separate acoustic slide are out of this page; their neighbours' bridges close the gap
    h = _bridge(h, "s-strategy", "And from above, here's the plan that makes it work.")
    h = _bridge(h, "s-material", "And on a floor this long, finding your way should be effortless.")
    h = _bridge(h, "s-team", "Here's how we'll take you through it.")
    # 17 Nov (the 16 Nov concept note, ACKO_Campus_Concept_Rework_Note.html: "23 slides become 3"): Part 01 is the three new slides,
    # Why a campus → Campus + Möbius = The ACKO Loop → The loop on our floor, then the memories as a pause (their six photos; the
    # promise and What if beats went with fold()). The people's challenge, the Möbius opening, Where both meet, the Möbius and the
    # seven stops leave this page (the make() call below); their patches went with them. Words: belonging, not safety
    h = _in_sec(h, "s-memories", "A campus is where we first felt safe among people.", "A campus is where we first felt we belonged.")
    # (17 Nov, later: the memories moved to the Appendix, so The loop on our floor hands over to Part 02 itself)
    h = _bridge(h, "s-loop-floor", "Here's the floor itself, as we found it. Part 2.")
    h = _bridge(h, "s-memories", "Appendix: the campus moments behind the Loop, kept for questions.")
    h = _in_sec(h, "s-agenda", "01 Belonging: why people come in, and the answer in ACKO's own mark.",
                "01 Belonging: why a campus, and the one loop that ties it together.")
    # 2 · the Loop on the floor, a one-click recap first
    # 2 · (12 Nov, Ritika: "these 2 slides are repetitive … add the loop on the floor slide's loop ribbon and call out to the looping it
    # together slide"): The Loop leaves this page; its ribbon on the floor and the seven call-outs move into Campus strategy, beat 4
    h = strat_loop(h)
    # 12 Nov (Ritika: "this slide in between is hindering the story continuity … How it started can be changed … have call out for
    # client journey as well. move day in acko slide after wayfinding"): the Part 03 card out, the strategy opens on The Shell, the
    # client's touchpoints called out, A day in ACKO in Part 04 after Wayfinding
    h = strat_more(h)
    h = axo_handoff(h)
    h = _bridge(h, "s-challenges", "A campus that connects, not just accommodates. So here's how we plan it: the Loop, laid on the floor.")
    # 12 Nov (Ritika: "swap the wayfinding slide to the one in the given html", index-wayfinding-walk.html; both, the walk then the sketch)
    # (12 Nov: "also remove the wayfinding static slide": the sketch, s-wf-a4, is out; the walk leads into the day)
    for _w, _t, _b in (("s-wf-a6", "Wayfinding", "And here's the floor in use, through one day."),):
        h = _in_sec(h, _w, '<div class="hdr"><b>Wayfinding</b><span>One language, six accents</span></div>', '<div class="hdr"><b>Wayfinding</b><span>%s</span></div>' % LAB["s5"])
        h = re.sub(r'(<section[^>]*\sid="%s"[^>]*?\sdata-title=")[^"]*(")' % _w, lambda m: m.group(1) + _t.replace("'", "&#x27;") + m.group(2), h, count=1)
        h = re.sub(r'(<section[^>]*\sid="%s"[^>]*?\sdata-notes="[^"]*)(")' % _w, lambda m: m.group(1) + " → Bridge: " + _b.replace("'", "&#x27;") + m.group(2), h, count=1, flags=re.S)
    h = _bridge(h, "s-wayday", "And at every stop, something for the Acker: their engagement points.")
    h = _bridge(h, "s-walkthrough", "And at the end of the day, the loop comes back to where it began.")
    h = _in_sec(h, "s-wayday", "<span>05 · The Day</span>", "<span>04 · The Feel</span>")
    # 6 · the agenda's subtitle; 9 · the reception renders say Arrival once
    h = _in_sec(h, "s-agenda", "ACKO’s own promise, “it’s always us with you”, followed from your mark to the floor, and through one day on it.",
                "Why a campus, how one loop ties it together, and how it becomes one floor and one day.")   # campus first (17 Nov)
    # the agenda campus-first (Ritika, 17 Nov, on the slide: "change this based on the new concept slides"; her pick of three
    # headlines): the note's one sentence, every team a home in one campus that one loop ties together
    for x, y in (('One promise, <span>made into a place.</span>', 'Every team a home,<br><span>one campus, one loop.</span>'),   # two whole lines, not "… one / campus"
                 ('<span class="hand">why people come in</span>', '<span class="hand">why a campus</span>'),
                 ('<span class="hand">how it becomes a campus</span>', '<span class="hand">six homes on one loop</span>'),
                 ('The agenda: one promise, made into a place, in five parts.', 'The agenda: every team a home, one campus, one loop, in five parts.'),
                 ('03 The Plan: how it becomes a campus.', '03 The Plan: six homes on one loop.')):
        h = _in_sec(h, "s-agenda", x, y)
    h = _in_sec(h, "s-sec-1", "Part 01 of six: Belonging, why people come in.", "Part 01 of six: Belonging, why a campus.")
    h = _in_sec(h, "s-agenda", "05 The Day: can we live it. Bridge: let's begin with the people.", "05 The Day: can we live it.")
    # the agenda without its copy block (Ritika, 17 Nov, boxing "Today", the headline and its line: "remove the caption from agenda";
    # all of it): the five parts alone, up in the middle, under a small "Agenda" (the slide's own label style; its enter() unchanged).
    # The notes keep "every team a home, one campus, one loop" as the line to say
    i, j = _sec(h, "s-agenda"); s = h[i:j]
    s, n1 = re.subn(r'<div class="ap-copy rv"[^>]*>.*?</div>', '<div class="ap-copy rv" style="left:8%;top:30%;width:62%"><small style="--i:0">Agenda</small></div>', s, count=1, flags=re.S)
    s, n2 = re.subn(r'(<ol class="ap-steps rv" style="left:8%;)top:66%', r'\1top:40%', s, count=1)
    assert n1 == 1 and n2 == 1, ("agenda copy", n1, n2)
    h = h[:i] + s + h[j:]
    h = _bridge(h, "s-agenda", "First, what we heard from you.")   # into We heard you (17 Nov)
    h = h.replace("Arrival · Arrival", "Arrival")
    # the layout: six beats (the sheets on demand), the acoustics fuller, the sheet's nav
    i, j = _sec(h, "s-layout-sp"); s = h[i:j]
    s = re.sub(r'data-steps="12"', 'data-steps="6"', s, count=1)
    s = re.sub(r'data-beats="[^"]*"', 'data-beats="Spaces,Neighbourhoods,Biophilia · the heat,Biophilia · planting,Biophilia · views to green,Acoustics"', s, count=1)
    s = s.replace('<p>The rings show sound: wide and lingering in the open workhall, cut short in the treated rooms.</p></div>',
                  '<p>The rings show sound: wide and lingering in the open workhall, cut short in the treated rooms.</p>' + AC_MORE + '</div>', 1)
    assert "ac-more" in s, "acoustics panel"
    k = s.index('<div class="page">') + len('<div class="page">')
    s = s[:k] + '\n    <div class="sp2-nav ui"><button type="button" class="sp2-back">← Back to layout</button><b></b><button type="button" class="sp2-next">Next neighbourhood →</button></div>' + s[k:]
    h = h[:i] + s + h[j:]
    a = h.index('ACKO.slide("s-layout-sp"'); b = h.index("</script>", a); js = h[a:b]
    R = [('const ORDER = [1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6], SHEET = [null, null, "01", "02", "03", "04", "05", "06", null, null, null, null];',
          'const ORDER = [1, 2, 3, 4, 5, 6], SHEET = [null, null, null, null, null, null];'),
         ('[1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6].indexOf(g) + 1', '[1, 2, 3, 4, 5, 6].indexOf(g) + 1'),
         ('plan.onZoneClick((z) => { if (beat === 2 && NBX.on) { go(sceneIx("s-layout-sp"), 2 + (+z.n)); return; } if (beat === 2) { if (zone && zone.id === z.id) closeZone(sc); else openZone(sc, z); } });',
          'plan.onZoneClick((z) => { if (beat === 2) nbOpen(sc, z.n); });\n      $(".sp2-back", sc).onclick = (e) => { e.stopPropagation(); nbClose(sc); }; $(".sp2-next", sc).onclick = (e) => { e.stopPropagation(); nbStep(sc, 1); };'),
         ('const goTo = (n) => go(sceneIx("s-layout-sp"), 2 + (+n));', 'const goTo = (n) => nbOpen(sc, n);'),
         ('if (NBX.on) go(sceneIx("s-layout-sp"), 2); else closeZone(sc);', 'if (NBX.on) nbClose(sc); else closeZone(sc);'),
         ('        if (e.target.closest && e.target.closest("input, textarea")) return;',
          '        if (e.target.closest && e.target.closest("input, textarea")) return;\n'
          '        if (SH && ["ArrowRight", "PageDown", " "].includes(e.key)) { nbStep(sc, 1); e.stopImmediatePropagation(); e.preventDefault(); return; }\n'
          '        if (SH && ["ArrowLeft", "PageUp"].includes(e.key)) { nbStep(sc, -1); e.stopImmediatePropagation(); e.preventDefault(); return; }\n'
          '        if (SH && e.key === "Escape") { nbClose(sc); e.stopImmediatePropagation(); e.preventDefault(); return; }'),
         ('  function sheet(sc, n) {', SP2_JS + '  function sheet(sc, n) {'),
         ('    step(n, sc) {\n', '    step(n, sc) {\n      if (SH) { SH = null; sc.classList.remove("nb-open"); }\n'),
         ('    leave(_, sc) {\n', '    leave(_, sc) {\n      SH = null; if (sc) sc.classList.remove("nb-open");\n')]
    for x, y in R:
        assert js.count(x) == 1, ("layout js", x[:60], js.count(x)); js = js.replace(x, y)
    h = h[:a] + js + h[b:]
    t = '<script src="assets/js/app.js'
    return h.replace(t, SP2_CSS + t, 1)
# ---- the 16 Nov concept note (ACKO_Campus_Concept_Rework_Note.html, 17 Nov, Ritika: "do these changes to the newly committed file"):
# every diagram labelled as concept, plan or reference ("so the client never mistakes a reference image for the project"), small, by
# the lockup; and no neighbourhood block in a purple ("Loop = the only strong purple line"): 02 Life (lilac) and 03 Health (violet
# blue) take a soft mint and a soft peach, on this page only (Ritika: "Story 2 only"); the plan and the axo both read AXO_LAYERS
TAG = {  # (22 Nov, Ritika: the Concept capsules are gone)
       "s-loop-floor": "Plan", "s-strategy": "Plan", "s-layout-dd": "Plan", "s-layout-sp": "Plan",
       "s-memories": "Reference", "s-site": "Reference"}
TAG_CSS = ('<style>.scene .page > .dg-tag { right: 12.6%; top: 95.1%; margin: 0; padding: .25em .9em; border: 1px solid currentColor; '
           'border-radius: 99px; font-size: calc(var(--pt) * 5); font-weight: 600; letter-spacing: .14em; text-transform: uppercase; '
           'line-height: 1.3; opacity: .5; pointer-events: none; }</style>\n')
NB_FIX = ('<script>/* index-story2.html only (17 Nov, the concept note: "if purple appears on a block, it\'s wrong"): 02 and 03 off the '
          'purples */ (window.AXO_LAYERS && window.AXO_LAYERS.zones || []).forEach(function (z) { if (z.n === "02") z.colour = "#cfe9df"; '
          'if (z.n === "03") z.colour = "#f3dcc4"; });</script>\n')
def concept_note(h):
    for sid, tag in TAG.items():
        if 'id="%s"' % sid not in h: continue
        i, _j = _sec(h, sid); k = h.index(">", h.index('<div class="page', i)) + 1
        h = h[:k] + '\n    <p class="dg-tag">%s</p>' % tag + h[k:]
    d = '<script src="data/axo-layers.js?v=1"></script>\n'
    assert h.count(d) == 1, "axo-layers script"
    h = h.replace(d, d + NB_FIX, 1)
    t = '<script src="assets/js/app.js'
    return h.replace(t, TAG_CSS + t, 1)
# the order (17 Nov, the concept note's "new flow"): cover, team, agenda, Part 01, the three new slides in place of the people's
# challenge, the Möbius opening and Where both meet, the memories as the pause; the Möbius and the seven stops out; fold() out (the
# memories end on their six photos: What if and the promise are what Campus + Möbius now says)
make("index-story2.html", {"s-whatif": None, "s-walk": None, "s-acoustic": None, "s-loop-w": None, "s-sec-3": None, "s-wayfinding": "s-wf-a6",
                           "s-challenge": "s-why-campus", OPEN: "s-campus-loop", "s-campus": "s-loop-floor", "s-mobius": None, "s-loop-stops": None},
     # the memories to the Appendix (Ritika, 17 Nov, on the slide: "move this slide to archive"): out of Part 01, kept beside the typologies
     # We heard you after the agenda (Ritika, 17 Nov: "before the concept slides, a 'we heard you' slide … the meetings mom"; her pick:
     # before the Part 01 card), placeholders until the minutes are in
     move={"s-wayday": "s-wf-a6", "s-memories": "s-typologies", "s-heard": "s-agenda"}, hfix=lambda h: concept_note(story2(storyfix(opportunity(lenses(h))))))
