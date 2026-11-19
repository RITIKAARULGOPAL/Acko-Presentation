"""Rebuild pages of the 03.11.26 Design Proposal PDF as native HTML slides (3 Nov deck, Ritika, 19 Nov):

    pages 1-4   Value Addition: Material strategy, the Campus palette, ESG strategy, D&I strategy
                  -> slides/s-material.html, s-palette2.html, s-esg.html, s-di.html (rewritten in place, same ids)
    page 5      "A quick Recap .."                         -> slides/s-recap.html
    pages 6-29  "A quick recap | <space> | <option>"        -> slides/s-recap-<space>.html, one per page

Every picture is cropped from the page as it shows (text taken off first, so the PDF's labels are HTML text, not pixels), the
words keep their font, size, colour and place (deck points, so the slide's --pt unit reads straight off the PDF), and the
slide reveals left to right.

    python tools/acko/make_proposal_slides.py ["path/to/Design Proposal.pdf"]       (needs pypdfium2, pdfplumber, numpy, scipy, Pillow)
    python tools/acko/make_proposal_slides.py PDF --debug DIR                       (also writes each page's detected boxes to DIR)

It prints the recap slide ids in page order; tools/acko/story/gen_story3.py lists them for Story 3 (RECAP).
"""
import html, os, re, sys

import numpy as np
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PDF = r"C:\Users\Ritika\Downloads\Copy of 03.11.26 _ ACKO_Design Proposal (1).pdf"
W, H = 720.0, 405.0
FOOT = 372            # below this line: the copyright and the ACKO | SKV lockup, which the deck draws itself
VALUE = {1: ("s-material", "img/mat4"), 2: ("s-palette2", "img/pal4"), 3: ("s-esg", "img/esg4"), 4: ("s-di", "img/di4")}

FONT = {"Figtree": "var(--body)", "SquarePeg": "var(--hand)", "Outfit": "var(--label)", "Poppins": "var(--label)", "Lexend": "var(--num)"}
WEIGHT = {"Thin": 100, "Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}


def clean_render(pdf, i, scale):
    """the page without its text, as an RGB image"""
    page = pdf[i]
    for o in [o for o in page.get_objects() if o.type == 1]:
        page.remove_obj(o)
    page.gen_content()
    return page.render(scale=scale).to_pil().convert("RGB")


def boxes(img, scale):
    """the pictures and flat blocks on a page, as (x0, y0, x1, y1) in deck points, outermost only"""
    a = np.asarray(img).astype(int)
    mask = np.abs(a - 255).max(axis=2) > 10
    mask[int(FOOT * scale):] = False
    mask = ndimage.binary_dilation(mask, iterations=1)
    lab, _ = ndimage.label(mask)
    out = []
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        b = (x0 + 1, y0 + 1, x1 - 1, y1 - 1)
        if min(b[2] - b[0], b[3] - b[1]) >= 14 * scale:      # at least 14 pt in each direction
            out.append(tuple(v / scale for v in b))
    out = [b for b in out if min(b[2] - b[0], b[3] - b[1]) >= 8]
    keep = [b for b in out if not any(o is not b and o[0] <= b[0] + 1 and o[1] <= b[1] + 1 and o[2] >= b[2] - 1 and o[3] >= b[3] - 1 for o in out)]
    return sorted(keep, key=lambda b: (round(b[0] / 4), b[1]))


def pct(v, total):
    return f"{v / total * 100:.2f}".rstrip("0").rstrip(".") + "%"


def tile_html(img, scale, b, name, i, outdir, quality=82, maxw=None):
    x0, y0, x1, y1 = b
    crop = img.crop((round(x0 * scale), round(y0 * scale), round(x1 * scale), round(y1 * scale)))
    arr = np.asarray(crop).astype(int)
    pos = f"--i:{i};left:{pct(x0, W)};top:{pct(y0, H)};width:{pct(x1 - x0, W)};height:{pct(y1 - y0, H)}"
    if arr.reshape(-1, 3).std(axis=0).max() < 3.5:                         # a flat block: a colour, not a picture
        r, g, bl = (int(v) for v in np.median(arr.reshape(-1, 3), axis=0))
        if min(r, g, bl) >= 238 and max(r, g, bl) - min(r, g, bl) < 6: return None   # the page's own white, not a swatch
        return f'      <i class="dk" style="{pos};background:#{r:02x}{g:02x}{bl:02x}"></i>'
    if maxw and crop.width > maxw:
        crop = crop.resize((maxw, round(crop.height * maxw / crop.width)), Image.LANCZOS)
    os.makedirs(os.path.join(ROOT, "assets", os.path.dirname(name)), exist_ok=True)
    crop.save(os.path.join(ROOT, "assets", name + ".webp"), "WEBP", quality=quality, method=6)
    return f'      <i class="dk" style="{pos};background-size:100% 100%;background-image:url(assets/{name}.webp)"></i>'


def style_of(fontname, size, color):
    fam, _, st = fontname.split("+")[-1].partition("-")
    return dict(fam=fam, weight=next((WEIGHT[k] for k in WEIGHT if st.startswith(k)), 400), italic="Italic" in st, size=round(size, 1), color=color_css(color))


def lines(page):
    """the words on a page as paragraphs: dicts of html (runs of other weight or colour as spans), x0, top, size, pitch, style, footer left out"""
    words = page.extract_words(extra_attrs=["fontname", "size", "non_stroking_color"], keep_blank_chars=False, use_text_flow=False)
    words = [dict(w, st=style_of(w["fontname"], w["size"], w["non_stroking_color"])) for w in words if w["top"] < FOOT]
    words.sort(key=lambda w: (round(w["top"] / 2), w["x0"]))
    rows = []
    for w in words:                                                      # words into lines: same height, the next word close by
        for r in rows:
            if abs(r["top"] - w["top"]) < w["size"] * 0.45 and 0 <= w["x0"] - r["x1"] < w["size"] * 1.1 and abs(r["st"]["size"] - w["st"]["size"]) < 1.5:
                r["words"].append(w); r["x1"] = w["x1"]; break
        else:
            rows.append(dict(words=[w], x0=w["x0"], x1=w["x1"], top=w["top"], bottom=w["bottom"], st=w["st"]))
    for r in rows:                                                       # the line's own style = its longest run's; other runs get spans
        tally = {}
        for w in r["words"]: tally[str(w["st"])] = tally.get(str(w["st"]), 0) + len(w["text"])
        main = max(r["words"], key=lambda w: tally[str(w["st"])])["st"]
        out, prev = [], None
        for w in r["words"]:
            diff = {k: w["st"][k] for k in ("weight", "italic", "color") if w["st"][k] != main[k]}
            t = html.escape(w["text"])
            if diff != prev:
                if prev: out.append("</span>")
                if out: out.append(" ")
                if diff: out.append('<span style="' + ";".join({"weight": f"font-weight:{diff.get('weight')}", "italic": "font-style:" + ("italic" if diff.get("italic") else "normal"),
                                                                "color": f"color:{diff.get('color')}"}[k] for k in diff) + '">')
                prev = diff
            else:
                out.append(" ")
            out.append(t)
        if prev: out.append("</span>")
        r["html"] = "".join(out); r["st"] = main
    rows.sort(key=lambda r: (r["st"]["fam"], r["st"]["size"], r["st"]["color"], round(r["x0"]), r["top"]))
    paras = []
    for r in rows:                                                       # stack the lines of one paragraph
        for p in paras:
            if p["st"] == r["st"] and abs(p["x0"] - r["x0"]) < 1.5 and 0 < r["top"] - p["last"] < r["st"]["size"] * 1.9                     and (p["pitch"] is None or abs(r["top"] - p["last"] - p["pitch"]) < 1.2):
                p["pitch"] = r["top"] - p["last"]; p["html"] += "<br>" + r["html"]; p["last"] = r["top"]; break
        else:
            paras.append(dict(r, last=r["top"], pitch=None))
    return paras


def color_css(c):
    if c is None: return "#000"
    if not isinstance(c, (list, tuple)): c = (c,)
    if len(c) == 1: c = (c[0],) * 3
    if len(c) == 4:                                                          # CMYK
        k = c[3]; c = tuple((1 - v) * (1 - k) for v in c[:3])
    return "#%02x%02x%02x" % tuple(round(v * 255) for v in c[:3])


def text_html(p):
    st = p["st"]
    lh = (p["pitch"] / st["size"]) if p["pitch"] else 1.0
    css = f"left:{pct(p['x0'], W)};top:{pct(p['top'], H)};font-family:{FONT.get(st['fam'], 'var(--body)')};font-size:calc(var(--pt) * {st['size']:.2f});"           f"line-height:{lh:.3f};color:{st['color']};font-weight:{st['weight']};white-space:nowrap"
    if st["italic"]: css += ";font-style:italic"
    if st["color"] in ("#ffffff", "#eeeeee"): css += ";text-shadow:0 1px 4px rgba(0,0,0,.4)"
    return css


def page_body(pdf, plum, i, scale, name_prefix, quality=82, maxw=None, debug=None):
    """(pictures html, words html) of page i (0-based)"""
    img = clean_render(pdf, i, scale)
    bx = boxes(img, scale)
    if debug:
        d = img.copy(); dr = ImageDraw.Draw(d)
        for k, b in enumerate(bx):
            dr.rectangle([v * scale for v in b], outline=(255, 0, 0), width=3); dr.text((b[0] * scale + 6, b[1] * scale + 6), str(k + 1), fill=(255, 0, 0))
        os.makedirs(debug, exist_ok=True); d.resize((d.width // 2, d.height // 2)).save(os.path.join(debug, "p%02d.png" % (i + 1)))
    pics = [tile_html(img, scale, b, f"{name_prefix}-{k + 1:02d}", int(((b[0] + b[2]) / 2) / W * 8), None, quality, maxw) for k, b in enumerate(bx)]
    pics = [t for t in pics if t]
    words = [f'    <div class="vt" style="--i:{int(p["x0"] / W * 8) + 1};{text_html(p)}">{p["html"]}</div>' for p in lines(plum.pages[i])]
    return pics, words


def section(sid, part, title, steps, mins, notes, pics, words, extra_css=""):
    css = f"\n<style>\n#{sid} .page {{ background: #fff; }}\n{extra_css}</style>"
    return f'''<section class="scene vpage" id="{sid}" data-part="{part}" data-title="{html.escape(title)}" data-steps="{steps}" data-mins="{mins}"
  data-notes="{html.escape(notes, quote=True)}">
  <div class="page rv">
{chr(10).join(pics)}
{chr(10).join(words)}
  </div>
</section>{css}
'''


def write_slide(sid, sec, head_from=None):
    path = os.path.join(ROOT, "slides", sid + ".html")
    src = open(head_from or path, encoding="utf8").read()
    head = src.split("<!-- slide:start -->")[0]
    head = re.sub(r"<title>.*?</title>", f"<title>{html.escape(sid)} · ACKO slide {sid}</title>", head, flags=re.S)
    open(path, "w", encoding="utf8").write(head + "<!-- slide:start -->\n" + sec + "<!-- slide:end -->\n</body>\n</html>\n")


def old_attrs(sid):
    """data-part, title, steps, mins, notes of a slide that already exists"""
    s = open(os.path.join(ROOT, "slides", sid + ".html"), encoding="utf8").read()
    g = lambda k: html.unescape(re.search(rf'data-{k}="(.*?)"', s, re.S).group(1))
    return g("part"), g("title"), g("steps"), g("mins"), g("notes")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    args = [a for a in sys.argv[1:] if a != "--debug"]
    debug = sys.argv[sys.argv.index("--debug") + 1] if "--debug" in sys.argv else None
    if debug: args.remove(debug)
    path = args[0] if args else DEFAULT_PDF
    pdf, plum = pdfium.PdfDocument(path), pdfplumber.open(path)

    for n, (sid, prefix) in VALUE.items():
        pics, words = page_body(pdf, plum, n - 1, 4, prefix, 86, None, debug)
        part, title, steps, mins, notes = old_attrs(sid)
        write_slide(sid, section(sid, part, title, 1, mins, notes, pics, words))
        print(sid, len(pics), "pictures,", len(words), "text blocks")

    # page 5: the divider
    pics, words = page_body(pdf, plum, 4, 2, "img/recap-0", 80, None, debug)
    write_slide("s-recap", section("s-recap", "cover", "A quick recap", 1, "0.1",
                                   "A quick recap: the spaces we have already seen, one render each.", pics, words))
    print("s-recap")

    ids, seen = [], {}
    for n in range(6, 30):
        i = n - 1
        text = [p for p in lines(plum.pages[i])]
        sub = re.sub(r"<[^>]+>", " ", sorted(text, key=lambda p: p["top"])[1]["html"])      # the first line is "A quick recap"
        base = "s-recap-" + slug(re.sub(r"\s*\|\s*", " ", html.unescape(sub)))[:48]
        seen[base] = seen.get(base, 0) + 1
        sid = base if seen[base] == 1 else f"{base}-{seen[base]}"
        pics, words = page_body(pdf, plum, i, 2.667, f"recap/{sid}", 80, 1920, debug)
        title = "A quick recap · " + html.unescape(sub)
        sec = section(sid, "cover", title, 1, "0.2", f"A quick recap: {html.unescape(sub)}. The render as shown at the last meeting.", pics, words)
        write_slide(sid, sec, head_from=os.path.join(ROOT, "slides", "s-recap.html"))
        ids.append(sid)
    print("RECAP =", ids)


if __name__ == "__main__":
    main()
