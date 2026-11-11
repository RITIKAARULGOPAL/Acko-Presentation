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

STEPS = [("s1", "The Loop"), ("s2", "Belonging"), ("s3", "The Site"),     # this deck's order (11 Nov, the brand first)
         ("s4", "The Plan"), ("s5", "The Palette"), ("s6", "The Experience")]
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
GROUPS = [
    ("cover", "s-cover s-team"),
    ("s1", OPEN + " s-mobius"),
    ("s2", "s-campus s-memories"),
    ("s3", "s-site s-layout-dd s-pitch s-challenges"),
    ("s4", "s-loop-w s-strategy s-walk s-layout-sp"),
    ("s5", "s-palette2 s-material"),
    ("s6", "s-engage s-w-reception s-w-recoffee s-w-deck s-w-board s-w-dept s-w-sprint s-w-arena s-w-arena2a s-w-exec s-w-cafe1 s-w-cafe2 s-w-garden s-w-coffee s-w-collab s-w-mothers s-w-zen s-w-studio s-walkthrough s-wayday"),
    ("close", "s-thanks-w"),
    ("A", "s-acoustic s-wayfinding s-typologies"),
    (None, "s-wellbeing s-di s-esg s-skv"),
]
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
def make(out, swap=None, wi=None, hfix=None):
  """one page of the re-ordered deck; swap renames (or with None drops) slides, wi marks a What if option page (10 Nov)"""
  swap = swap or {}
  ORDER = [swap.get(i, i) for _, g in GROUPS for i in g.split() if swap.get(i, i)]
  live = [l.strip() for l in open("slides/order.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
  assert all(os.path.exists(os.path.join("slides", i + ".html")) for i in ORDER) and len(set(ORDER)) == len(ORDER)
  build.build(ORDER, out)

  h = open(out, encoding="utf-8").read()
  # each section's chapter
  for part, g in GROUPS:
      if not part: continue
      for sid in g.split():
          sid = swap.get(sid, sid)
          if not sid: continue
          h, n = re.subn(r'(<section\b[^>]*?\sid="%s"[^>]*?\sdata-part=")[^"]*(")' % sid, lambda m: m.group(1) + part + m.group(2), h, count=1)
          if not n:
              h, n = re.subn(r'(<section\b[^>]*?\sdata-part=")[^"]*("[^>]*?\sid="%s")' % sid, lambda m: m.group(1) + part + m.group(2), h, count=1)
          assert n, sid
  # each slide's header: its title, then its step (the old section names go)
  HDR = [
      ('<div class="hdr"><b>The Site</b><span>Layout</span></div>', "The Site", "s3"),
      ('<div class="hdr"><b>Design Strategy</b><span>Understanding how we derived a solution.</span></div>', "Workstation Typologies", "A"),
      ('<div class="hdr"><b>Design Strategy</b><span>What\'s our Challenge ?</span></div>', "The Opportunity", "s3"),
      ('<div class="hdr"><b>ESG Strategy</b><span>Value Addition | Kit of parts</span></div>', "Wayfinding", "A"),
      ('<div class="hdr"><b>Acker’s engagement points</b><span>Value Addition | Kit of parts</span></div>', "Acker’s engagement points", "s6"),
      ('<div class="hdr"><b>The Campus Palette</b><span>Visual Direction</span></div>', "The Campus Palette", "s5"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Material Strategy</span></div>', "Material Strategy", "s5"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Acoustic Strategy</span></div>', "Acoustic Strategy", "A"),
      ('<div class="hdr"><b>Schematic Axonometric</b><span>Space Planning &nbsp;| Wayfinding</span></div>', "A day in ACKO", "s6"),
  ]
  # the layout's header, once per copy: Due Diligence discovers the site (03), Spaces on shapes the plan (05)
  LY = '<div class="hdr"><b>Layout</b><span>Space Planning - Option 02A &nbsp;| Revised option</span></div>'
  for sid, step in (("s-layout-dd", "s3"), ("s-layout-sp", "s4")):
      i = h.index('id="%s"' % sid); j = h.index(LY, i)
      h = h[:j] + '<div class="hdr"><b>Layout · Option 02A</b><span>%s</span></div>' % LAB[step] + h[j + len(LY):]
  assert LY not in h
  for old, title, step in HDR:
      assert h.count(old) >= 1, old[:60]                 # the layout's twice (Due Diligence, then Spaces on)
      h = h.replace(old, '<div class="hdr"><b>%s</b><span>%s</span></div>' % (title, LAB[step]))
  # Where both meet opens on the question that bridges from the challenge (wow_campus.py, 10 Nov); its notes say it first
  _n = 'data-notes="Research: 58% of employees'
  assert h.count(_n) == 1, "campus notes"
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
        "8 · So what if the workplace kept that promise to its own people? We started where it has to happen: one floor in Koramangala.")
    assert new.count('data-steps="8"') == 1 and "The promise,What if" in new and "8 · So what if" in new, "memories head"
    h = h.replace(sec, new, 1)
    k = h.index('<div class="page">', j) + len('<div class="page">')
    return h[:k] + "\n    " + close() + h[k:]
# ---- the lenses keep the challenge's promise (10 Nov): "So we design a place that already feels like home: Teams together · Easy to
# find · Room to explore · Same rhythm". The Layout kept Teams together; each lens says, in the hand under its header, which line it keeps
# 11 Nov: the challenge's promise has left the order and acoustic and wayfinding are in the appendix; the lines that stay say what
# each slide gives in the Loop's own positive words
LENS = [("s-palette2", "A place that already feels like home."), ("s-material", "A place that already feels like home."),
        ("s-engage", "Room to explore.")]
LENS_CSS = ('<style>.scene .page > .lens-cb { left: 1.8%; top: 10%; margin: 0; font-family: var(--hand); font-size: calc(var(--pt) * 13); '
            'line-height: 1; color: var(--purple); white-space: nowrap; }</style>\n')
def lenses(h):
    for sid, line in LENS:
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
def opportunity(h):
    a = h.index('id="s-challenges"'); i = h.rindex("<section", 0, a); j = h.index("</section>", a)
    sec = h[i:j]
    for x, y in OPP:
        assert sec.count(x) == 1, x[:50]
        sec = sec.replace(x, y)
    return h[:i] + sec + h[j:]
make("index-approach.html", {"s-whatif": None}, hfix=lambda h: opportunity(lenses(fold(h))))
