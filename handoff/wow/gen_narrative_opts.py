# narrative-options.html (deck-wow checkout): problem first, then solution, opening on the people's challenge (Ritika, 10 Nov).
# Four variations, the analysis, the final narrative with a line to say per slide. Slide titles, clicks and minutes are read from the
# re-ordered deck itself (index-approach.html), so the timings are the deck's own.  run: python gen_narrative_opts.py <deck-wow>
import html, os, re, sys
os.chdir(sys.argv[1])
H = open("index-approach.html", encoding="utf-8").read()
META = {}
for m in re.finditer(r'<section class="scene[^"]*" id="([^"]+)"([^>]*)>', H):
    a = m.group(2); g = lambda k: html.unescape((re.search(k + r'="([^"]*)"', a) or [None, ""])[1])
    META[m.group(1)] = {"title": g("data-title"), "mins": float(g("data-mins") or 0), "steps": int(g("data-steps") or 1)}
TITLE = {"s-layout-dd": "Layout · Due Diligence + sun path", "s-layout-sp": "Layout · Spaces, the six neighbourhoods, Biophilia, Acoustics",
         "s-challenge": "The challenge at hand (the people)", "s-challenges": "One vast floor (the building)", "s-campus": "Where both meet",
         "s-loop-w": "The Loop (welcome · emotions · on the floor)", "s-strategy": "Campus strategy (to the Employees Journey)"}
t = lambda i: TITLE.get(i, META[i]["title"])

OPEN = ["s-cover", "s-team", "s-approach"]
PEOPLE = ["s-challenge"]
INSIGHT = ["s-campus", "s-memories", "s-whatif"]
BUILDING = ["s-site", "s-layout-dd", "s-pitch", "s-challenges"]
IDEA = ["s-mobius", "s-loop-w"]
PROOF = ["s-strategy", "s-walk", "s-layout-sp"]
RENDERS = [i for i in META if i.startswith("s-w-")]
EXP = ["s-wayfinding", "s-engage", "s-palette2", "s-material", "s-acoustic"] + RENDERS + ["s-walkthrough", "s-typologies", "s-wayday"]
CLOSE = ["s-thanks-w"]
TODAY = [("Opening", OPEN), ("The idea", IDEA), ("The people", PEOPLE + INSIGHT), ("The building", BUILDING), ("The plan", PROOF), ("The experience", EXP), ("Close", CLOSE)]

V = [
    {"n": 1, "name": "People → what they want → the building → the idea", "tag": "Recommended",
     "acts": [("Opening", OPEN), ("1 · The people's problem", PEOPLE), ("2 · What people want", INSIGHT), ("3 · The building's problem", BUILDING),
              ("4 · The idea", IDEA), ("5 · The proof", PROOF), ("6 · The experience", EXP), ("Close", CLOSE)],
     "why": "Feeling, then reality, then the answer. The last problem on screen is the vast floor's “a thousand disconnected experiences”; the very next thing is ACKO's own Möbius turning into one Loop. The Loop then lies down on that same floor."},
    {"n": 2, "name": "People → the building → what they want → the idea", "tag": "",
     "acts": [("Opening", OPEN), ("1 · The people's problem", PEOPLE), ("2 · The building's problem", BUILDING), ("3 · What people want", INSIGHT),
              ("4 · The idea", IDEA), ("5 · The proof", PROOF), ("6 · The experience", EXP), ("Close", CLOSE)],
     "why": "Both problems first, then the longing, then the answer. The Loop follows “What if…”, so it answers the feeling well, but the floor's problem is four slides back by then."},
    {"n": 3, "name": "People → the building → the idea → why it works", "tag": "",
     "acts": [("Opening", OPEN), ("1 · The people's problem", PEOPLE), ("2 · The building's problem", BUILDING), ("3 · The idea", IDEA),
              ("4 · Why it works", INSIGHT), ("5 · The proof", PROOF), ("6 · The experience", EXP), ("Close", CLOSE)],
     "why": "The Loop arrives earliest, straight after the vast floor. But the research, the brief and the memories then come after the answer, as a justification; the room has seen the idea before it has felt the need."},
    {"n": 4, "name": "People and the brief → the building → the idea → the feeling, before the walk", "tag": "",
     "acts": [("Opening", OPEN), ("1 · The people and the brief", PEOPLE + ["s-campus"]), ("2 · The building's problem", BUILDING), ("3 · The idea", IDEA),
              ("4 · The proof", ["s-strategy", "s-memories", "s-whatif", "s-walk", "s-layout-sp"]), ("5 · The experience", EXP), ("Close", CLOSE)],
     "why": "The research and the brief stay with the people up front; the memories wait until just before the walk, as the feeling the walk delivers. Strong in parts, but it splits the insight in two and breaks Where both meet's black opening into the memories."},
]
# the analysis: per variation, 1–5 and the reason
CRIT = ["The Loop answers the problem just shown", "Fact and feeling in a good order", "Hand-offs between slides kept", "Matches “How we worked”", "Opening pace"]
SCORES = {
    1: [(5, "Vast floor → Möbius → Loop: problem, then answer, back to back"), (5, "The worry, the longing, then the hard facts, then the answer"),
        (5, "All kept: the black into the memories; site → plan → pitches → axo"), (4, "With its line reworded: people first, site next, concept followed"), (4, "Opens on the people's own questions: quick and human")],
    2: [(3, "The Loop follows “What if”; the floor problem is four slides back"), (4, "Facts first, feeling last: logical, a little cool"),
        (5, "All kept"), (5, "Closest to today's wording: the site leads"), (3, "Site data comes right after the opening: a slower first five minutes")],
    3: [(5, "Vast floor → Loop, back to back"), (2, "The why (58%, the brief, the memories) comes after the answer"),
        (3, "The black into the memories kept; the Loop no longer leads into the strategy"), (3, "The idea before the opportunity"), (4, "Fast: the Loop at about 4¾ min")],
    4: [(5, "Vast floor → Loop, back to back"), (4, "Research and brief up front; the feeling saved for the walk"),
        (2, "Where both meet no longer opens into the memories; the strategy → walk hand-off is split"), (4, "Close, with its line reworded"), (4, "Brisk")],
}

def mins(ids): return sum(META[i]["mins"] for i in ids)
def loop_at(acts):
    t = 0.0
    for _, ids in acts:
        for i in ids:
            if i == "s-mobius": return t
            t += META[i]["mins"]
    return t
def chip(i, cls=""):
    m = META[i]; k = m["steps"]
    return f'<li class="{cls}"><span>{html.escape(t(i))}</span><em>{m["mins"]:g}′{" · " + str(k) + " clicks" if k > 1 else ""}</em></li>'
def strip(acts, compact=False):
    out = []
    for name, ids in acts:
        if compact and name in ("The experience", "6 · The experience", "5 · The experience"):
            body = f'<li><span>Lenses · {len(RENDERS)} renders · walkthrough · typologies · A day in ACKO</span><em>{mins(ids):.1f}′</em></li>'
        else:
            body = "".join(chip(i, "idea" if i in IDEA else "prob" if i in PEOPLE + BUILDING else "") for i in ids)
        out.append(f'<div class="act"><h4>{html.escape(name)}<small>{mins(ids):.1f} min</small></h4><ul>{body}</ul></div>')
    return '<div class="strip">' + "".join(out) + "</div>"

# the final narrative: what to say, slide by slide
SAY = {
    "s-cover": "ACKO · The Loop: a campus for about 640 Ackers on one floor at Regalium.",
    "s-team": "The people behind it.",
    "s-approach": "How we worked: we started with the people, let the site set the terms, and the concept followed, in six steps.",
    "s-challenge": "It's not a move: moving offices is easy, moving people isn't. Where do I go, will I fit, where's my desk, where's my team? So the brief for us: one place, one experience.",
    "s-campus": "Two things we were given: the research (58% of people in India come to the office to feel they belong) and the brief (a Modern Indian Institution). Where both meet: a campus.",
    "s-memories": "Maybe we've felt this before: the court, the pathways, friends, the café, study time, the stairs.",
    "s-whatif": "So what if the workplace carried that same feeling of safety and belonging?",
    "s-site": "Now the building we were given: Regalium, Koramangala, the 3rd floor, 56,650 sq ft carpet for about 640 people.",
    "s-layout-dd": "What the building brings, and the layout has to work around; and where the sun falls through the day.",
    "s-pitch": "One floor, longer than two football pitches end to end, and only half a pitch wide.",
    "s-challenges": "One vast floor, a thousand disconnected experiences: homogeneity, distance, disorientation. What it needs is a campus that connects, not just accommodates.",
    "s-mobius": "The answer was already in ACKO's own mark: the Möbius, one continuous surface.",
    "s-loop-w": "Opened out, it becomes the Loop, where emotions matter; and laid on the floor, it is one path through all seven moments.",
    "s-strategy": "How the Loop shapes the floor: the neighbourhoods planned, configured and looped together, the client's journey and the employees'.",
    "s-walk": "Walk it: arrival, café, board room, meeting rooms, collab, work, wellness.",
    "s-layout-sp": "And the plan it all sits on: 640 people at their desks, six neighbourhoods one by one, the planting and the acoustics.",
    "s-wayfinding": "How people find their way round the Loop.",
    "s-engage": "Where Ackers feel it, play it and share it.",
    "s-palette2": "The campus palette.", "s-material": "The materials, and why.", "s-acoustic": "Keeping the open floor calm.",
    "s-walkthrough": "The walkthrough.", "s-typologies": "The workstation types behind the 640 desks.",
    "s-wayday": "A day in ACKO, by the clock, stop by stop.",
    "s-thanks-w": "And the Loop closes where it began, in ACKO's Möbius. Thank you.",
}
FINAL = V[0]["acts"]
rows = []
for name, ids in FINAL:
    rows.append(f'<tr class="ah"><th colspan="3">{html.escape(name)}<small>{mins(ids):.1f} min</small></th></tr>')
    for i in ids:
        if i in RENDERS:
            if i == RENDERS[0]:
                rows.append(f'<tr><td>The renders ({len(RENDERS)})</td><td>{mins(RENDERS):.1f}′</td><td>Each space as it will be, in the Loop\'s order.</td></tr>')
            continue
        rows.append(f'<tr class="{"idea" if i in IDEA else "prob" if i in PEOPLE + BUILDING else ""}"><td>{html.escape(t(i))}</td><td>{META[i]["mins"]:g}′</td><td>{html.escape(SAY.get(i, ""))}</td></tr>')

total = mins([i for _, ids in FINAL for i in ids])
cards = []
for v in V:
    sc = SCORES[v["n"]]; tot = sum(s for s, _ in sc)
    cards.append(f'''<section class="card{" rec" if v["tag"] else ""}"><header><b>{v["n"]}</b><div><h3>{html.escape(v["name"])}</h3>
<p>{html.escape(v["why"])}</p></div><aside>{('<i>' + v["tag"] + '</i>') if v["tag"] else ""}<span>Loop at <b>{loop_at(v["acts"]):.1f} min</b></span><span>Score <b>{tot}/25</b></span></aside></header>{strip(v["acts"], True)}</section>''')
table = "<table class='an'><thead><tr><th></th>" + "".join(f"<th>{v['n']}</th>" for v in V) + "</tr></thead><tbody>" + "".join(
    "<tr><th>" + html.escape(c) + "</th>" + "".join(f"<td><span class='dots'>{'●' * SCORES[v['n']][k][0]}{'○' * (5 - SCORES[v['n']][k][0])}</span>{html.escape(SCORES[v['n']][k][1])}</td>" for v in V) + "</tr>"
    for k, c in enumerate(CRIT)) + "<tr class='tot'><th>Total</th>" + "".join(f"<td><b>{sum(s for s, _ in SCORES[v['n']])}</b> / 25</td>" for v in V) + "</tr></tbody></table>"

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ACKO · Problem first</title>
<style>
:root {{ --ink:#16131f; --soft:#5d5870; --line:#e7e3f1; --purple:#5222d0; --lilac:#c9b3f3; --wash:#f6f3ff; --warm:#c45b2f; }}
* {{ box-sizing: border-box; }} body {{ margin: 0; background: #fff; color: var(--ink); font: 15px/1.5 "Figtree", "Segoe UI", system-ui, sans-serif; }}
main {{ max-width: 1480px; margin: 0 auto; padding: 48px 40px 80px; }}
h1 {{ font-size: 40px; line-height: 1.1; margin: 0 0 8px; }} h1 b {{ color: var(--purple); }}
h2 {{ font-size: 24px; margin: 56px 0 14px; }} h2 small {{ font-size: 14px; font-weight: 500; color: var(--soft); margin-left: 10px; }}
.lede {{ font-size: 17px; color: var(--soft); max-width: 70ch; margin: 0 0 6px; }}
.note {{ display: inline-block; margin-top: 10px; padding: 6px 12px; border-radius: 99px; background: var(--wash); color: var(--purple); font-weight: 600; font-size: 13px; }}
.card {{ border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px; margin: 16px 0; }}
.card.rec {{ border-color: var(--purple); box-shadow: 0 0 0 3px rgba(82,34,208,.08); }}
.card header {{ display: grid; grid-template-columns: 44px 1fr 220px; gap: 16px; align-items: start; }}
.card header > b {{ font-size: 30px; color: var(--purple); line-height: 1; }}
.card h3 {{ margin: 0 0 4px; font-size: 19px; }} .card p {{ margin: 0; color: var(--soft); }}
.card aside {{ display: flex; flex-direction: column; gap: 4px; align-items: flex-end; font-size: 13px; color: var(--soft); }}
.card aside i {{ font-style: normal; background: var(--purple); color: #fff; border-radius: 99px; padding: 3px 10px; font-weight: 600; }}
.card aside b {{ color: var(--ink); }}
.strip {{ display: flex; gap: 10px; margin-top: 16px; overflow-x: auto; padding-bottom: 4px; }}
.act {{ flex: 1 0 150px; background: #fbfaff; border: 1px solid var(--line); border-radius: 10px; padding: 10px; }}
.act h4 {{ margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--soft); display: flex; justify-content: space-between; gap: 8px; }}
.act h4 small {{ font-weight: 500; text-transform: none; letter-spacing: 0; }}
.act ul, .final ul {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 5px; }}
.act li {{ background: #fff; border: 1px solid var(--line); border-radius: 7px; padding: 5px 8px; font-size: 12.5px; display: flex; justify-content: space-between; gap: 8px; }}
.act li em {{ font-style: normal; color: var(--soft); white-space: nowrap; }}
li.prob {{ border-color: #f0c9b6; background: #fff7f2; }} li.idea {{ border-color: var(--lilac); background: var(--wash); font-weight: 600; }}
.an {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }} .an th, .an td {{ border-bottom: 1px solid var(--line); padding: 10px; text-align: left; vertical-align: top; }}
.an thead th {{ font-size: 20px; color: var(--purple); }} .an tbody th {{ width: 220px; }}
.dots {{ display: block; color: var(--purple); letter-spacing: 2px; font-size: 13px; }} .an .tot td {{ font-size: 16px; }}
.verdict {{ background: var(--wash); border-radius: 14px; padding: 18px 22px; margin-top: 18px; }} .verdict p {{ margin: 6px 0; }}
.fin {{ width: 100%; border-collapse: collapse; font-size: 14px; }} .fin td {{ border-bottom: 1px solid var(--line); padding: 8px 10px; vertical-align: top; }}
.fin td:first-child {{ width: 290px; font-weight: 600; }} .fin td:nth-child(2) {{ width: 60px; color: var(--soft); }}
.fin tr.ah th {{ text-align: left; padding: 22px 10px 8px; font-size: 15px; color: var(--purple); border-bottom: 2px solid var(--purple); }}
.fin tr.ah small {{ font-weight: 500; color: var(--soft); margin-left: 10px; }}
.fin tr.prob td:first-child::before {{ content: "PROBLEM"; display: block; font-size: 10px; letter-spacing: .12em; color: var(--warm); }}
.fin tr.idea td:first-child::before {{ content: "THE IDEA"; display: block; font-size: 10px; letter-spacing: .12em; color: var(--purple); }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }} .cols ul {{ margin: 6px 0; padding-left: 20px; }}
@media (max-width: 900px) {{ main {{ padding: 24px 16px; }} .card header {{ grid-template-columns: 1fr; }} .card aside {{ align-items: flex-start; }} .cols {{ grid-template-columns: 1fr; }} }}
</style></head><body><main>
<h1>Problem first, <b>then the Loop.</b></h1>
<p class="lede">Today the deck opens on the Möbius and the Loop, before anyone has heard the problem. Below: four ways to tell it the other way round, all opening on the people's challenge, each scored; then the final narrative, slide by slide, with a line to say.</p>
<span class="note">Opens on the people's challenge · {total:.1f} min of slides in all · minutes and clicks read from the deck</span>

<h2>Today <small>the idea first: the Loop at {loop_at(TODAY):.1f} min, before any problem</small></h2>
<section class="card">{strip(TODAY, True)}</section>

<h2>Four variations <small>orange: a problem · lilac: the idea</small></h2>
{"".join(cards)}

<h2>Analysis</h2>
{table}
<div class="verdict"><p><b>Recommended: variation 1.</b> It is the only one where every hand-off survives and the answer follows straight on from the problem. The people's worry and their longing (58% to belong, a campus, the memories) build the need; the building then shows why the need is hard to meet on this floor; and the Loop answers both at once, landing on that same floor.</p>
<p>Variation 3 reaches the Loop about a minute sooner, but asks the room to accept the idea before it has felt the need, which works against the client's note that the concept must carry the weight. Variation 2 is the most logical and the least moving.</p></div>

<h2>The final narrative <small>variation 1 · {total:.1f} min of slides</small></h2>
<table class="fin"><tbody>{"".join(rows)}</tbody></table>

<h2>When you say go</h2>
<div class="cols"><div><b>Kept as they are</b><ul>
<li>Where both meet's black opening into the memories</li><li>Site → Due Diligence → two pitches → the vast floor (the floor carried, the sun path)</li>
<li>Campus strategy → walk the Loop → Layout · Spaces</li><li>The Loop closing into the Möbius on Thank you</li></ul></div>
<div><b>New or changed</b><ul>
<li>The vast floor → the Möbius: the axo's floor fades as the ribbon draws</li>
<li>The Loop on the floor rising into the Campus strategy axo (the vast floor no longer sits next to it)</li>
<li>“How we worked”: “we started with the people, let the site set the terms, and the concept followed”</li>
<li>The section labels and menu follow the new order</li></ul></div></div>
</main></body></html>'''
open("narrative-options.html", "w", encoding="utf-8", newline="\n").write(page)
print("ok", round(total, 2), [round(loop_at(v["acts"]), 2) for v in V], round(loop_at(TODAY), 2))
