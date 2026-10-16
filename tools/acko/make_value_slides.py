"""Write the value-addition and typology slides (deck 15, 46, 47, 48, 52) as HTML: every picture placed and cropped as on its
deck page (deck_layout.py), the words as on the page, and everything coming in one after another.

    python tools/acko/make_value_slides.py
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "acko", "deck_layout.py"), "15", "46", "47", "48", "52"],
                     capture_output=True, text=True, cwd=ROOT).stdout
parts = re.split(r"<!-- slide (\d+) -->\n", out)
PICS = {parts[i]: [l for l in parts[i + 1].splitlines() if l.startswith("<i")] for i in range(1, len(parts), 2)}


def pics(n, skip=()):
    return "\n".join("      " + l for l in PICS[n] if not any(s in l for s in skip))


def T(x, y, w, cls, html, extra=""):
    return f'    <div class="vt {cls}" style="left:{x}%;top:{y}%;width:{w}%;{extra}">{html}</div>'


SLIDES = {}

# 15 · workstation typologies
SLIDES["s-typologies"] = dict(part="2", title="Workstation typologies", mins=0.75, hdr=("Design Strategy", "Understanding how we derived a solution."),
  notes="Workstation typologies: instead of rows, non-linear clusters that give the plan a more dynamic rhythm. Type 1, 73 pax; Type 3, 36 pax; Type 4, the main cluster, 525 pax; with Type 2, 14 pax, that is 648 seats — and the three executive cabins make 651.",
  body=pics("15") + "\n" + "\n".join([
    T(1.8, 27, 48.3, "h-p", "Let’s understand the Workstation Typologies"),
    T(50.2, 27, 48.3, "p-g", "So here the main idea is that we explore different non linear workstation typologies that gives a more dynamic approach in space planning."),
    T(8.5, 72.4, 22, "ty-n", '<b>Type 1</b><span data-count="73">73</span> pax'),
    T(39.5, 72.4, 22, "ty-n", '<b>Type 3</b><span data-count="36">36</span> pax'),
    T(71.6, 72.4, 22, "ty-n", '<b>Type 4</b><span data-count="525">525</span> pax'),
    T(1.9, 84, 96, "ty-sum", 'Type 1 <b>73</b> + Type 2 <b>14</b> + Type 3 <b>36</b> + Type 4 <b>525</b> = <b data-count="648">648</b> seats &nbsp;·&nbsp; + 3 executive cabins = <b>651</b>'),
  ]))

# 46 · Acker's engagement points
SLIDES["s-engage"] = dict(part="4", title="Acker's engagement points", mins=0.75, hdr=("Acker’s engagement points", "Value Addition | Kit of parts"),
  notes="Acker's engagement points: the workplace beyond function — moments of interaction, play and emotional engagement. A mood check-in, interactive gaming, a place to nerd out, a wall to express, pause and play, a punch bag for the frustrated Ackers, happy conversations.",
  body=pics("46", ("acko-ink",)) + "\n" + "\n".join([
    T(3.1, 39.2, 44.3, "h-loop", '<img src="assets/img/acko-ink.webp" alt="ACKO"><span>Loop , where Emotions Matter!</span>'),
    T(1.7, 44.2, 42.5, "hand h-hand", "Designed for Interaction. Built for Engagement."),
    T(1.7, 52.6, 30, "p-g", "From conversation and connection to games, self-expression and opportunities to pause or unwind, these elements make the workplace feel more human and approachable. The interventions also add a sense of discovery and personality, creating spaces where employees can interact, recharge and have moments of fun throughout the day."),
    T(79.4, 52, 18.9, "p-g it", "Acker’s engagement points explore how the workplace can go beyond functionality to create moments of interaction, play and emotional engagement."),
    T(43.8, 14.5, 14.7, "hand lab", "Mood Check-In"), T(62.7, 12.4, 14.7, "hand lab", "Pause &amp; Play"), T(83.7, 12.4, 14.7, "hand lab", "Happy conversations"),
    T(34.2, 74.8, 14.7, "hand lab", "Interactive Gaming"), T(46.0, 80.9, 14.7, "hand lab", "Come nerd it out"), T(65.4, 74.2, 14.7, "hand lab", "To Express out"),
    T(75.8, 79, 14.7, "hand lab", "For the frustrated Ackers"),
  ]))

# 47 · material strategy
lab = lambda x, y, t, dark=False: T(x, y, 9.5, "tile-lab" + (" dark" if dark else ""), t)
SLIDES["s-material"] = dict(part="4", title="Material strategy", mins=0.75, hdr=("Value Addition", "Kit of parts | Material Strategy"),
  notes="The kit of parts, by surface. Flooring: tiles, wooden LVT, carpet. Ceiling: perforated gypsum, spray-applied acoustic treatment, gypsum with track lights, acoustic baffles. Furnishing: rugs, fabrics, blinds. Wall finishes: acoustic panelling, wooden panel, stone. Material intelligence matters.",
  body=pics("47") + "\n" + "\n".join([
    T(1.3, 25.9, 20.3, "col-h", "Flooring."), T(27.5, 25.9, 17.5, "col-h", "Ceiling."), T(52.9, 25.9, 20.3, "col-h", "Furnishing."), T(78.7, 25.9, 20.3, "col-h", "Wall Finishes."),
    lab(1.9, 31.4, "Tiles"), lab(1.8, 62.5, "Wooden LVT"), lab(11.7, 62.3, "Carpet"), lab(27.2, 31.5, "Perforated Gypsum", True), lab(37.2, 31.4, "Spray-applied treatment"),
    lab(27.1, 60.3, "Gypsum ceiling with track lights"), lab(37.2, 60.2, "Acoustic baffles"), lab(53.0, 31.4, "Rugs"), lab(52.9, 62.4, "Fabrics"), lab(62.8, 62.5, "Blinds"),
    lab(78.7, 31.4, "Acoustic Paneling"), lab(78.7, 62.4, "Wooden Panel"), lab(88.7, 31.4, "Stone Finish"),
    T(52.9, 68.2, 45.6, "hand h-hand", "Material Intelligence matters…"),
  ]))

# 48 · acoustic strategy
ac = [("Ceiling Treatment", "Absorptive ceiling systems with acoustic tiles or spray treatment; dedicated ceiling treatment in meeting rooms for RT60 control.", 4.2),
      ("Wall Treatment", "Absorptive wall panels in meeting spaces enhance speech clarity and reduce echo, with feature walls combining acoustic and aesthetic performance.", 18.9),
      ("Partition Design", "Full-height acoustic partitions with appropriate STC ratings ensure privacy based on room function and adjacency.", 34.4),
      ("HVAC Noise Control", "Control duct-borne and breakout noise through HVAC design, with terminal devices meeting zone NC targets.", 50.2),
      ("Sound Masking", "Background sound masking evens out the floor’s noise, so speech carries less and focus holds.", 65.8),
      ("Door &amp; Glazing Spec", "Acoustic-rated doors and double glazing assemblies complement partition STC performance for meeting spaces.", 81.5)]
SLIDES["s-acoustic"] = dict(part="4", title="Acoustic strategy", mins=0.75, hdr=("Value Addition", "Kit of parts | Acoustic Strategy"),
  notes="Acoustic excellence: spaces designed for NRC 0.70–0.90, so focus, privacy and comfort hold on a floor of 651. Ceiling treatment for RT60 in meeting rooms, absorptive wall panels, full-height partitions to the right STC, HVAC noise control to NC targets, sound masking, acoustic doors and double glazing. An acoustic consultant can refine the specification.",
  body=pics("48") + "\n" + "\n".join([
    T(3.5, 16.3, 56.4, "p-k", 'Thoughtful acoustic planning enhances focus, privacy, and workplace comfort. Spaces are designed with optimal <b>NRC values (<span data-count="0.70" data-dec="2">0.70</span>–<span data-count="0.90" data-dec="2">0.90</span>)</b> to reduce noise, minimize reverberation, and improve speech privacy.'),
  ] + [T(x, 59.7, 14.6, "ac-c", f"<b>{h}</b><p>{p}</p>") for h, p, x in ac] + [
    T(4.1, 82.6, 31.3, "hand h-hand", "Acoustic excellence…"),
    T(50.3, 84.6, 47, "p-g r", "An acoustic consultant can be onboarded to further refine technical specifications, material selection, and performance benchmarks."),
  ]))

# 52 · wayfinding
SLIDES["s-wayfinding"] = dict(part="4", title="Wayfinding", mins=0.75, hdr=("ESG Strategy", "Value Addition | Kit of parts"),
  notes="Wayfinding of a modern Indian institution: meeting rooms as study chambers, named Nalanda, Sabha, Takshashila. Meeting-room signs with braille for inclusive design; bespoke privacy films drawn from the brand; consistent wayfinding for meeting rooms, work areas and reception. A subtle recall that respects the brand and its glocal identity.",
  body=pics("52") + "\n" + "\n".join([
    '      <i class="dk" style="--i:7;left:90.2%;top:34.7%;width:8.2%;height:26.3%;background-size:641.0% 223.2%;background-position:81.8% 51.0%;background-image:url(assets/img/wf-corner.webp)"></i>',
    '      <i class="dk" style="--i:8;left:44.7%;top:52.3%;width:9.8%;height:8.6%;background-size:117.6% 100%;background-position:72.7% 0;background-image:url(assets/img/wf-film.webp)"></i>',
    '      <i class="dk" style="--i:9;left:62.7%;top:52.3%;width:9.8%;height:8.6%;background-size:117.6% 100%;background-position:72.7% 0;background-image:url(assets/img/wf-film.webp)"></i>',
    '      <i class="dk" style="--i:10;left:80.7%;top:52.5%;width:9.8%;height:8.6%;background-size:117.6% 100%;background-position:72.7% 0;background-image:url(assets/img/wf-film.webp)"></i>',
    T(44.5, 44.3, 5.5, "wf-name", "Nalanda"), T(62.5, 44.3, 5.5, "wf-name", "Sabha"), T(80.6, 44.2, 6.5, "wf-name", "Takshashila"),
    T(50.4, 23.2, 23.2, "p-k", "Meeting room Signages, with braille signage; considering Inclusive Design"),
    T(76.3, 23.1, 14, "p-k", "Consistent Wayfinding"), T(78.1, 63.6, 18.6, "p-k", "Bespoke Privacy Films, inspired from the branding"),
    T(1.8, 48.3, 23.9, "col-h", "04 Wayfinding"),
    T(2.3, 52.8, 12.1, "p-g sm", "This is done keeping in mind the ethos of a Modern Indian Institution. Meeting Rooms are study and chambers."),
    T(2.3, 71.1, 32.7, "p-m", "If Incorporating Wayfinding of A Modern Indian Institution in workplace, what would it be ?"),
    T(2.3, 80.9, 36, "p-l", "Subtle Recall that respects the Brand &amp; Glocal Identity."),
  ]))

for sid, d in SLIDES.items():
    html = f'''<section class="scene vpage" id="{sid}" data-part="{d["part"]}" data-title="{d["title"]}" data-steps="1" data-mins="{d["mins"]}"
  data-notes="{d["notes"]}">
  <div class="page rv">
    <div class="hdr"><b>{d["hdr"][0]}</b><span>{d["hdr"][1]}</span></div>
{d["body"]}
  </div>
</section>
'''
    # number the reveal order: pictures first (their --i), then the words after them
    k = [0]
    def num(m):
        k[0] += 1
        return f'<div class="vt{m.group(1)}" style="--i:{8 + k[0]};'
    html = re.sub(r'<div class="vt([^"]*)" style="', num, html)
    open(os.path.join(ROOT, "slides", sid + ".html"), "w", encoding="utf8").write(html)
    print(sid)
