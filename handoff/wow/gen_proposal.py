# The design proposal of 3 Nov ("Copy of 03.11.26 _ ACKO_Design Proposal.pdf", Ritika, 10 Nov: "make sure the contents of these slides
# are there"; she chose: replace the renders with the PDF's, in both decks).
#  1 · renders: each render page's picture, cut as the page shows it (its clip), into assets/img/r3-*.webp; the walk slides take them,
#      with the PDF's option pairs and names; three spaces the deck didn't have are added (reception coffee point, outdoor deck, collab);
#      the library, not in the proposal, leaves the order (its slide file stays)
#  2 · the campus palette (page 1) and material strategy (page 27): their boards rebuilt from the page, every tile as the page crops it,
#      the words where the page sets them
# run: python gen_proposal.py <pdf> <deck checkout>          (then tools/build.py, and run_wow.sh for the re-ordered deck)
import io, json, os, re, sys, html as H
import fitz
from PIL import Image
PDF, DECK = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eol import rd, wr
doc = fitz.open(PDF)
IMG = os.path.join(DECK, "assets", "img")
PW, PH = 720.0, 405.0

def placed(pn):
    """the page's pictures in drawing order: (xref, image bbox, visible rect, transform)"""
    pg = doc[pn - 1]
    info = pg.get_image_info(xrefs=True)
    log = pg.get_bboxlog()
    out, k = [], 0
    for n, (kind, r) in enumerate(log):
        if kind != "fill-image": continue
        inf = info[k]; k += 1
        b = fitz.Rect(inf["bbox"]); vis = fitz.Rect(b)
        if n and log[n - 1][0] == "fill-path":                      # the shape it is cut to, drawn just before it
            c = fitz.Rect(log[n - 1][1])
            if c.width > 2 and c.height > 2 and (c & b).get_area() > 0.2 * c.get_area(): vis = c & b
        vis = vis & fitz.Rect(0, 0, PW, PH)
        out.append((inf["xref"], b, vis, inf["transform"]))
    return out

def picture(xref, b, vis, tr, maxw=2400):
    """the picture as the page shows it: mirrored as placed, cut to the visible rect, alpha kept"""
    pix = fitz.Pixmap(doc, xref)
    sm = doc.extract_image(xref).get("smask") or 0
    if sm:
        try: pix = fitz.Pixmap(pix, fitz.Pixmap(doc, sm))
        except Exception: pass
    if pix.colorspace and pix.colorspace.n not in (1, 3): pix = fitz.Pixmap(fitz.csRGB, pix)
    mode = "RGBA" if pix.alpha else ("L" if pix.n == 1 else "RGB")
    im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    if tr[0] < 0: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if tr[3] < 0: im = im.transpose(Image.FLIP_TOP_BOTTOM)
    W, Hh = im.size
    box = (round((vis.x0 - b.x0) / b.width * W), round((vis.y0 - b.y0) / b.height * Hh),
           round((vis.x1 - b.x0) / b.width * W), round((vis.y1 - b.y0) / b.height * Hh))
    im = im.crop(box)
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    return im

def save(im, name, q=86):
    if im.mode not in ("RGB", "RGBA"): im = im.convert("RGB")
    p = os.path.join(IMG, name + ".webp"); im.save(p, "WEBP", quality=q, method=6); return p

# ---------------------------------------------------------------- 1 · renders
R = {2: "r3-reception-op1", 3: "r3-reception-op2", 4: "r3-recoffee-op1", 5: "r3-recoffee-op2", 6: "r3-deck",
     7: "r3-board-op1", 8: "r3-board-op2", 9: "r3-dept", 10: "r3-sprint", 11: "r3-work1-op1", 12: "r3-work1-op2",
     13: "r3-work2-op1", 14: "r3-work2-op2", 15: "r3-exec-op1", 16: "r3-exec-op2", 17: "r3-cafe1", 18: "r3-cafe2",
     19: "r3-garden", 20: "r3-coffee", 21: "r3-collab", 22: "r3-mothers", 23: "r3-zen", 24: "r3-studio-op1", 25: "r3-studio-op2"}
for pn, name in R.items():
    big = max(placed(pn), key=lambda t: t[2].get_area())
    im = picture(*big); save(im, name, 88); print("render", pn, name, im.size)

OP = "OP 01,OP 02"
# slide: (pages, name, sub, Loop words, line, keyplans, title, notes)
WALK = {
    "s-w-reception": ([2, 3], "Reception", "Arrival", "I feel welcomed", None, [], "Reception",
                      "Reception, where the Loop begins: I feel welcomed. Option 01 and Option 02."),
    "s-w-recoffee":  ([4, 5], "Reception Coffee Point", "Arrival", "I feel welcomed", None, [], "Reception Coffee Point",
                      "The coffee point at reception: a first coffee as you arrive. Option 01 and Option 02."),
    "s-w-deck":      ([6], "Outdoor Deck", "Out in the open", "They thought of me too!", None, [], "Outdoor Deck",
                      "The outdoor deck: a pause in the open air, under the canopies."),
    "s-w-board":     ([7, 8], "State Room", "Boardroom · 32 pax", "This is my big moment", None, [25, 25], "State Room · Boardroom",
                      "The State Room, the 32-pax boardroom: ACKO's big moment. Option 01 and Option 02."),
    "s-w-dept":      ([9], "State Room", "Departmental rooms", "My impact", None, [27], "Departmental Room",
                      "The departmental room: a department meets as one."),
    "s-w-sprint":    ([10], "Quick Sprint Room", "04 pax meeting room", "My impact", None, [29], "Quick Sprint Room",
                      "Quick sprint rooms, 4 pax: the everyday meeting."),
    "s-w-arena":     ([11, 12], "Work Area", "Neighbourhood", "These are my folks!", None, [31, 31], "Work Area · Neighbourhood",
                      "A work area in a neighbourhood: these are my folks. Option 01 and Option 02."),
    "s-w-arena2a":   ([13, 14], "Work Area", "Neighbourhood · another view", "These are my folks!", None, [33, 33], "Work Area · Neighbourhood · View 2",
                      "The neighbourhood from another corner. Option 01 and Option 02."),
    "s-w-exec":      ([15, 16], "Executive Room", "Executive corner cabin", None, None, [37, 37], "Executive Room",
                      "The executive room: a desk, a meeting table and a lounge corner by the glass. Option 01 and Option 02."),
    "s-w-cafe1":     ([17], "Cafe", "View 1", "Hey, we finally meet!", None, [40], "Cafe · View 1",
                      "The café: hey, we finally meet. View 1."),
    "s-w-cafe2":     ([18], "Cafe", "View 2", "Hey, we finally meet!", None, [41], "Cafe · View 2",
                      "The café: hey, we finally meet. View 2."),
    "s-w-garden":    ([19], "The Acker Garden", "Work area", "Wow, worth the commute", None, [36], "The Acker Garden",
                      "The Acker Garden: a work area in the planting. Wow, worth the commute."),
    "s-w-coffee":    ([20], "Coffee Point", "Coffee corner", "Hey, we finally meet!", None, [42], "Coffee Point",
                      "A coffee point: hey, we finally meet."),
    "s-w-collab":    ([21], "Collab", "Come together", "Wow, worth the commute", None, [], "Collab",
                      "Collab: a space to come together around ideas. Worth the commute."),
    "s-w-mothers":   ([22], "Mother's Room", "A space for all Moms @ Acko", "They thought of me too!",
                      "Designed with a soothing palette that ensures calm amongst a busy day, to relax.", [43], "Mother's Room",
                      "The mother's room: a soothing palette that keeps calm amongst a busy day. A space for all moms at ACKO."),
    "s-w-zen":       ([23], "Zen Room", "A space to unwind", "They thought of me too!",
                      "To unwind, relax and keep the mind creative: a night-sky optic-fibre ceiling in the brand's hues, for peace and curiosity.", [44], "Zen Room",
                      "The zen room: a space to unwind, relax and keep the mind creative, under a night-sky optic-fibre ceiling in the brand's hues."),
    "s-w-studio":    ([24, 25], "Studio Room", "A space for Acko's voice", None, None, [45, 45], "Studio Room",
                      "The studio: a space for ACKO's voice, the podcast set. Option 01 and Option 02."),
}
tpl, nl = rd(os.path.join(DECK, "slides", "s-w-coffee.html"))
for sid, (pages, n, sub, q, line, kp, title, notes) in WALK.items():
    path = os.path.join(DECK, "slides", sid + ".html")
    s, snl = rd(path) if os.path.exists(path) else (re.sub(r"(?<![/\w-])s-w-coffee\b", sid, tpl).replace("<title>Coffee Point ·", "<title>" + title + " ·"), nl)
    w = {"n": n, "sub": sub}
    if q: w["q"] = q
    if line: w["p"] = line
    w["r"] = [R[p] for p in pages]; w["kp"] = kp[:len(pages)]
    steps = len(pages)
    s = re.sub(r'data-walk="[^"]*"', 'data-walk="%s"' % H.escape(json.dumps(w, ensure_ascii=False), quote=True), s, count=1)
    s = re.sub(r'data-title="[^"]*"', 'data-title="%s"' % H.escape(title, quote=True), s, count=1)
    s = re.sub(r'data-steps="\d+"', 'data-steps="%d"' % steps, s, count=1)
    s = re.sub(r'data-beats="[^"]*"', 'data-beats="%s"' % (OP if steps == 2 else "Render"), s, count=1)
    s = re.sub(r'data-notes="[^"]*"', 'data-notes="%s"' % H.escape(notes, quote=True), s, count=1)
    wr(path, s, snl); print("walk", sid, w["r"])

# the order: the proposal's
WALK_ORDER = list(WALK)
p = os.path.join(DECK, "slides", "order.txt"); s, onl = rd(p)
lines = s.split("\n"); ids = [l.strip() for l in lines]
first = min(i for i, l in enumerate(ids) if l.startswith("s-w-")); last = max(i for i, l in enumerate(ids) if l.startswith("s-w-"))
assert all(ids[i].startswith("s-w-") or not ids[i] or ids[i].startswith("#") for i in range(first, last + 1)), ids[first:last + 1]
lines = lines[:first] + WALK_ORDER + lines[last + 1:]
wr(p, "\n".join(lines), onl); print("order.txt: walk", len(WALK_ORDER))
json.dump(WALK_ORDER, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "walk_order.json"), "w"))
print("ok renders")

# ---------------------------------------------------------------- 2 · the palette and the materials, from their pages
X = lambda v: "%.1f%%" % (v / PW * 100)
Y = lambda v: "%.1f%%" % (v / PH * 100)
def tiles(pn, prefix):
    """every picture on the page but the footer's logos, cut as shown, placed where the page places it (in drawing order)"""
    out = []
    for n, (xref, b, vis, tr) in enumerate(t for t in placed(pn) if t[2].y0 < 370 and t[2].width > 8):
        name = "%s-%02d" % (prefix, n + 1); save(picture(xref, b, vis, tr, 1400), name, 84)
        out.append('      <i class="dk" style="--i:%d;left:%s;top:%s;width:%s;height:%s;background-size:100%% 100%%;background-image:url(assets/img/%s.webp)"></i>'
                   % (n, X(vis.x0), Y(vis.y0), X(vis.width), Y(vis.height), name))
    return out
def spans(pn):
    d = doc[pn - 1].get_text("dict"); out = []
    for b in d["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["text"].strip(): out.append((fitz.Rect(s["bbox"]), s["text"].strip(), s["color"], s["size"]))
    return out

# the campus palette (page 1)
LAB = ["Timeless", "Serene", "Soothing", "Organic", "Sleek", "Expressive", "Tactile", "Understated", "Artisanal", "Accent"]
board = tiles(1, "pal3")
labs = []
for r, t, c, sz in spans(1):
    if t in LAB:
        labs.append('      <span class="pl-lab" style="left:%s;top:%s%s">%s</span>' % (X(r.x0 - 4), Y(r.y0 - 2), ";color:#111;text-shadow:none" if c < 0x808080 else "", t))
PAL = ('    <div class="pl-board rv" style="left:0;top:0;width:100%;height:100%">\n' + "\n".join(board + labs) + "\n    </div>\n"
       '    <div class="pl-words" style="left:2.7%;top:16%">TEXTURED · CONTRAST · WARMTH · REFINED · LAYERED</div>\n'
       '    <div class="pl-title hand" style="left:2.3%;top:68.6%">The Campus Palette</div>\n'
       '    <p class="pl-p" style="left:31.1%;top:71.6%;width:50%">A sophisticated blend of <b>light wood, Accent stone,</b> soft neutrals and lush greenery for a <b>grounded and contemporary workplace.</b></p>\n')
p = os.path.join(DECK, "slides", "s-palette2.html"); s, snl = rd(p)
a = s.index('    <div class="pl-board'); z = s.index("</p>", s.index('<p class="pl-p"')) + len("</p>\n")
s = s[:a] + PAL + s[z:]
s = re.sub(r'data-notes="[^"]*"', 'data-notes="The campus palette: textured, contrast, warmth, refined, layered. A sophisticated blend of light wood, accent stone, soft neutrals and lush greenery for a grounded and contemporary workplace. Timeless, serene, soothing, organic, sleek, expressive, tactile, understated, artisanal, accent."', s, count=1)
wr(p, s, snl); print("palette", len(board), "tiles", len(labs), "labels")

# material strategy (page 27)
mat = tiles(27, "mat3")
sp = [t for t in spans(27) if t[3] < 7 and 120 < t[0].y0 < 370]          # the tiles' labels (not the footer)
groups = []                                                   # a label's lines, joined (same left edge, the next line straight under)
for r, t, c, sz in sorted(sp, key=lambda q: (round(q[0].x0), q[0].y0)):
    g = groups[-1] if groups else None
    if g and abs(g[0].x0 - r.x0) < 1.5 and 0 <= r.y0 - g[0].y1 < 2: g[0] |= r; g[1].append(t)
    else: groups.append([fitz.Rect(r), [t], c])
labs = ['    <div class="vt tile-lab%s" style="--i:%d;left:%s;top:%s;width:9.5%%;">%s</div>' % (" dark" if c < 0x808080 else "", 13 + i, X(r.x0 - 3), Y(r.y0 - 2),
        " ".join(ts).replace("Wooden Lvt", "Wooden LVT").replace("spray-applied treatment", "Spray-applied treatment"))
        for i, (r, ts, c) in enumerate(groups)]
heads = ['    <div class="vt col-h" style="--i:%d;left:%s;top:%s;width:20%%;">%s</div>' % (9 + i, X(r.x0 - 1), Y(r.y0 - 1), t)
         for i, (r, t, c, sz) in enumerate(q for q in spans(27) if q[1] in ("Flooring.", "Ceiling.", "Furnishing.", "Wall Finishes."))]
seps = ['    <i class="mat-sep" style="left:%s;top:%s;height:%s"></i>' % (X(x), Y(135.1), Y(130)) for x in (176.3, 363.1, 547.8)]
MAT = ("\n".join(mat) + "\n" + "\n".join(seps + heads + labs) + "\n"
       '    <div class="vt hand h-hand" style="--i:30;left:53.9%;top:67.8%;width:45%;">Material Intelligence matters…</div>\n'
       '    <style>#s-material .mat-sep { border-left: 1px dashed #c9c9c9; }</style>\n')
p = os.path.join(DECK, "slides", "s-material.html"); s, snl = rd(p)
a = s.index("\n", s.index('<div class="hdr">')) + 1; z = s.index("  </div>\n</section>")
s = s[:a] + MAT + s[z:]
s = re.sub(r'data-notes="[^"]*"', 'data-notes="The kit of parts, by surface. Flooring: tiles, wooden LVT, carpet. Ceiling: stretch fabric, spray-applied treatment, gypsum ceiling with track lights, acoustic baffles. Furnishing: rugs, fabrics, blinds. Wall finishes: wallpaper, acoustic panel, wooden panel. Material intelligence matters."', s, count=1)
wr(p, s, snl); print("material", len(mat), "tiles", len(groups), "labels", len(heads), "heads")
