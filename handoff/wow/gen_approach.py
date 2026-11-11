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

STEPS = [("s1", "Understand the people"), ("s2", "Spot the opportunity"), ("s3", "Discover the site"),     # this deck's order (10 Nov)
         ("s4", "Frame the idea"), ("s5", "Shape the plan"), ("s6", "Layer the lenses")]
LAB = {k: "%02d · %s" % (i + 1, n) for i, (k, n) in enumerate(STEPS)}
GROUPS = [
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
    ("s5", "s-strategy s-layout-sp"),          # 5 the proof: the Loop's floor rising into the strategy axo, the walk, flat again: the layout, Spaces on
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
      ('<div class="hdr"><b>Design Strategy</b><span>Understanding how we derived a solution.</span></div>', "Workstation Typologies", "s6"),
      ('<div class="hdr"><b>Design Strategy</b><span>What\'s our Challenge ?</span></div>', "What's our Challenge?", "s3"),
      ('<div class="hdr"><b>ESG Strategy</b><span>Value Addition | Kit of parts</span></div>', "Wayfinding", "s6"),
      ('<div class="hdr"><b>Acker’s engagement points</b><span>Value Addition | Kit of parts</span></div>', "Acker’s engagement points", "s6"),
      ('<div class="hdr"><b>The Campus Palette</b><span>Visual Direction</span></div>', "The Campus Palette", "s6"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Material Strategy</span></div>', "Material Strategy", "s6"),
      ('<div class="hdr"><b>Value Addition</b><span>Kit of parts | Acoustic Strategy</span></div>', "Acoustic Strategy", "s6"),
      ('<div class="hdr"><b>Schematic Axonometric</b><span>Space Planning &nbsp;| Wayfinding</span></div>', "A day in ACKO", "s6"),
  ]
  # the layout's header, once per copy: Due Diligence discovers the site (03), Spaces on shapes the plan (05)
  LY = '<div class="hdr"><b>Layout</b><span>Space Planning - Option 02A &nbsp;| Revised option</span></div>'
  for sid, step in (("s-layout-dd", "s3"), ("s-layout-sp", "s5")):
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
LENS = [("s-acoustic", "Same rhythm."), ("s-wayfinding", "Easy to find."), ("s-engage", "Room to explore."),
        ("s-palette2", "A place that already feels like home."), ("s-material", "A place that already feels like home.")]
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
def nb_e(h):
    """the deck's own neighbourhood sheet: template E, Ritika's reference (10 Nov)"""
    t = '<script src="assets/js/app.js'
    return h.replace(t, '<script>window.ACKO_NB = window.ACKO_NB || "e";   /* the neighbourhood sheets as in Ritika\'s reference (10 Nov) */</script>\n' + t, 1)
make("index-approach.html", {"s-whatif": None}, hfix=lambda h: nb_e(lenses(fold(h))))

# ---- the neighbourhood sheet, three more templates (10 Nov, Ritika: "suggest more templates for neighbourhoods slide - current one is
# too cluttered"; wow_nbsheet.py): a page each, and one page to compare them. index-approach.html keeps A until she picks
NBT = [("e", "As in your reference", "index-approach.html", ["The deck's sheet now.", "A column: key plan, the name, a line, desks · area · meeting rooms, and every room numbered.", "The plan card with the same numbers on the rooms; the axo card turning slowly, its pins on the rooms."]),
       ("a", "As built", "index-nb-a.html", ["Plan beside axo, labelled.", "Below: the name, seats and area, a key plan and the full occupancy table."]),
       ("b", "Axo hero", "index-nb-b.html", ["The furnished axo across the whole plan area.", "Below: the name, four big counts (workstations, meeting rooms, phone booths, wellness) and a small key plan.", "No table."]),
       ("c", "Quiet split", "index-nb-c.html", ["Plan beside axo, as now.", "Below: only the name and the four big counts.", "No table, no key plan."]),
       ("d", "Axo-led", "index-nb-d.html", ["The axo large on the right.", "On the left: the neighbourhood's plan, small, and its card under it: name, seats and area, the four counts.", "Nothing else below but the pills."])]
def nbopt(v):
    def f(h):
        t = '<script src="assets/js/app.js'
        tag = ('<script>window.ACKO_NB = "%s";</script>\n<div class="nb-tag">Neighbourhoods · %s</div><style>.nb-tag { position: fixed; left: 14px; bottom: 14px; z-index: 90; '
               'padding: 6px 10px; border-radius: 3px; background: #5222d0; color: #fff; font: 600 11px/1 var(--body); letter-spacing: .08em; text-transform: uppercase; pointer-events: none; }</style>\n') % (v, v.upper())
        return h.replace(t, tag + t, 1)
    return f
for v, _, out, _ in NBT[1:]:
    make(out, {"s-whatif": None}, hfix=lambda h, v=v: nbopt(v)(lenses(fold(h))))
cards = "".join('<article><div class="k">%s%s</div><h2>%s</h2><ul>%s</ul><a href="%s#s-layout-sp/3">Open the sheets →</a></article>'
                % (v.upper(), " · the deck's" if v == "e" else "", t, "".join("<li>%s</li>" % l for l in ls), out) for v, t, out, ls in NBT)
open("nb-options.html", "w", encoding="utf-8").write('''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neighbourhood sheets · four ways</title>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root { --ink: #16131f; --mute: #5b5570; --line: #e3def2; --purple: #5222d0; --bg: #faf9fd; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: Figtree, system-ui, sans-serif; }
main { max-width: 1240px; margin: 0 auto; padding: 48px 24px 64px; }
h1 { margin: 0 0 6px; font-size: 30px; } .lead { margin: 0 0 32px; color: var(--mute); max-width: 780px; line-height: 1.5; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; }
article { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 22px; display: flex; flex-direction: column; }
.k { font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--purple); }
h2 { margin: 8px 0 12px; font-size: 22px; } ul { margin: 0 0 20px; padding-left: 18px; color: var(--mute); line-height: 1.5; flex: 1; }
li + li { margin-top: 6px; }
a { align-self: flex-start; padding: 10px 14px; border-radius: 6px; background: var(--purple); color: #fff; font-weight: 600; text-decoration: none; }
a:hover { background: #3e17a8; }
</style></head><body><main>
<h1>Neighbourhood sheets · four ways</h1>
<p class="lead">Layout · Spaces, beats 3–8: one neighbourhood at a time. Each way below is the whole re-ordered deck, opening on the first sheet (01 · Auto); press → for the next neighbourhood.</p>
<div class="grid">''' + cards + '''</div>
</main></body></html>
''')
print("ok nb-options")

# ---- Biophilia · Views to green, four more ways (11 Nov, Ritika: "can come as an illustration instead of showing it on layout, can
# also be a text; show me different variations, I'll pick"; wow_nbsheet.py): a page each, one page to compare
BVT = [("a", "On the plan", "index-approach.html", ["As now: every seat's sight line to its nearest plant, drawn on the layout."]),
       ("b", "The number", "index-bio-b.html", ["Text only: a very large 96%, “of the seats have a plant in view within 8 m”.", "Small: the median distance, the plants, the seats.", "In the hand: “A glance at green, all day.”"]),
       ("c", "A section", "index-bio-c.html", ["An illustration, side on: a person at a desk, the eye-line drawing itself to a plant 3.5 m away (the median).", "A lighter bracket for “within 8 m”, and the 96% beside it."]),
       ("d", "100 seats", "index-bio-d.html", ["An infographic: 100 seats, 96 of them filling green one by one.", "“96 in every 100 seats see a plant within 8 m”, with the median."]),
       ("e", "A render", "index-bio-e.html", ["The Acker Garden render across the layout's place.", "On a soft white fade: “From 96% of the desks, green is a glance away.”"])]
def bioopt(v):
    def f(h):
        t = '<script src="assets/js/app.js'
        tag = ('<script>window.ACKO_BIO = "%s";</script>\n<div class="bv-tag">Views to green · %s</div><style>.bv-tag { position: fixed; left: 14px; bottom: 14px; z-index: 90; '
               'padding: 6px 10px; border-radius: 3px; background: #2f7a4f; color: #fff; font: 600 11px/1 var(--body); letter-spacing: .08em; text-transform: uppercase; pointer-events: none; }</style>\n') % (v, v.upper())
        return h.replace(t, tag + t, 1)
    return f
for v, _, out, _ in BVT[1:]:
    make(out, {"s-whatif": None}, hfix=lambda h, v=v: bioopt(v)(nb_e(lenses(fold(h)))))
cards = "".join('<article><div class="k">%s%s</div><h2>%s</h2><ul>%s</ul><a href="%s#s-layout-sp/11">Open it →</a></article>'
                % (v.upper(), " · now" if v == "a" else "", t, "".join("<li>%s</li>" % l for l in ls), out) for v, t, out, ls in BVT)
open("bio-options.html", "w", encoding="utf-8").write(open("nb-options.html", encoding="utf-8").read()
    .replace("<title>Neighbourhood sheets · four ways</title>", "<title>Views to green · five ways</title>")
    .replace(open("nb-options.html", encoding="utf-8").read().split('<main>')[1].split('</main>')[0],
             '\n<h1>Views to green · five ways</h1>\n<p class="lead">Layout · Biophilia, step 3. Each way below is the whole re-ordered deck, opening on that step; ← goes back to Planting.</p>\n<div class="grid">' + cards + '</div>\n'))
print("ok bio-options")
