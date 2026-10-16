"""Joins the slides into the presentation.

Every slide is its own HTML page, slides/<id>.html (open it on its own to work on it). Between <!-- slide:start --> and
<!-- slide:end --> it holds its <section class="scene" id="<id>">, its <style> and its <script>; the build takes only that part
and joins the slides in slides/order.txt into the deck shell (slides/_shell.html): the styles into the head, the sections into
the stage, the scripts after the engine, then ACKO.start().

usage:
  python tools/build.py                  index.html — the joined deck, linking assets/ and data/ (for editing; serve.py rebuilds it)
  python tools/build.py --only s-loop,s-site     preview.html — just those slides, joined
  python tools/build.py --single         dist/ACKO-The-Loop.html — ONE self-contained file: every image, font, script and the music
                                         embedded once; opens from anywhere, offline (this is the file to present)
It also writes assets/js/shell.js (the deck's chrome, for a slide opened on its own).
"""
import base64, json, os, posixpath, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES = os.path.join(ROOT, "slides")
START, END = "<!-- slide:start -->", "<!-- slide:end -->"
MARK = {k: re.compile(r"^[ \t]*<!-- @%s\b.*?-->[ \t]*\n" % k, re.M) for k in ("slides", "styles", "scripts")}
SINGLE_NAME = "ACKO-The-Loop.html"


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def order():
    ids = [l.strip() for l in read("slides", "order.txt").splitlines()]
    return [i for i in ids if i and not i.startswith("#")]


def parse_slide(sid):
    """the slide's section, styles and scripts (between the markers); old-style files without markers are all section"""
    text = read("slides", sid + ".html")
    if START in text:
        if END not in text:
            raise SystemExit(f"slides/{sid}.html has {START} but no {END}")
        text = text.split(START, 1)[1].split(END, 1)[0]
    styles = re.findall(r"<style\b[^>]*>(.*?)</style>", text, re.S)
    scripts = re.findall(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)
    body = re.sub(r"<style\b[^>]*>.*?</style>|<script\b[^>]*>.*?</script>", "", text, flags=re.S).strip()
    if len(re.findall(r"<section\b", body)) != 1:
        raise SystemExit(f"slides/{sid}.html: expected exactly one <section> between the markers")
    if not re.search(r'<section\b[^>]*\bid="%s"' % re.escape(sid), body):
        raise SystemExit(f'slides/{sid}.html: its <section> needs id="{sid}"')
    for css in styles:      # a slide's CSS should only reach its own slide
        for sel in re.findall(r"(?:^|})\s*([^{}@]+?)\s*{", css):
            for one in sel.split(","):
                one = one.strip()
                if re.match(r"^(html|body|\*|h[1-6]|p|img|button|section|svg|div|span|\.page|\.hdr|\.scene)\b", one):
                    print(f"  note: slides/{sid}.html styles '{one}' for the whole deck — prefix it with #{sid}", file=sys.stderr)
    return body, styles, scripts


def shell_chrome(shell):
    """the deck's chrome (body without scripts, the stage left empty) as a string for assets/js/shell.js"""
    body = shell.split("<body>", 1)[1].split("<script", 1)[0]
    return MARK["slides"].sub("", body).strip()


def compose(ids):
    problems, seen, present = [], set(), []
    for i in ids:
        if i in seen: problems.append(f"{i} is listed twice in order.txt")
        seen.add(i)
        # a slide still out with someone: the deck builds without it
        if os.path.exists(os.path.join(SLIDES, i + ".html")): present.append(i)
        else: print(f"  skipped: {i} is in order.txt but slides/{i}.html isn't here (yet)", file=sys.stderr)
    if problems: raise SystemExit("slides: " + "; ".join(problems))
    ids = present
    parts = [parse_slide(i) for i in ids]
    shell = read("slides", "_shell.html")
    for k, m in MARK.items():
        if len(m.findall(shell)) != 1: raise SystemExit(f"slides/_shell.html needs exactly one <!-- @{k} --> line")
    styles = "".join(f"<style data-slide=\"{i}\">{s}</style>\n" for i, (_, ss, _) in zip(ids, parts) for s in ss)
    sections = "\n".join(b for b, _, _ in parts) + "\n"
    scripts = "".join(f"<script data-slide=\"{i}\">{s}</script>\n" for i, (_, _, js) in zip(ids, parts) for s in js)
    html = MARK["styles"].sub(lambda m: styles, shell)
    html = MARK["slides"].sub(lambda m: sections, html)
    html = MARK["scripts"].sub(lambda m: scripts + "<script>ACKO.start();</script>\n", html)
    return html, shell


def write(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    try:
        with open(p, encoding="utf-8", newline="") as f:
            if f.read() == text: return
    except FileNotFoundError:
        pass
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def unused_warning(ids):
    listed = set(ids)
    unused = sorted(f[:-5] for f in os.listdir(SLIDES) if f.endswith(".html") and not f.startswith("_") and f[:-5] not in listed)
    if unused: print("in slides/ but not in order.txt (not in the deck):", ", ".join(unused), file=sys.stderr)


def build(ids=None, out="index.html"):
    ids = ids or order()
    html, shell = compose(ids)
    write(os.path.join("assets", "js", "shell.js"), "/* generated by tools/build.py from slides/_shell.html: the deck's chrome, for a slide opened on its own */\n"
          "window.ACKO_SHELL = " + json.dumps(shell_chrome(shell)) + ";\n")
    write(out, html)
    return html


# ------------------------------------------------------------------------------------------------ the single file
ASSET = re.compile(r"assets/(?:img|deck|fonts|audio)/[A-Za-z0-9_./-]+?\.(?:webp|png|jpe?g|gif|svg|woff2|mp3)")
MIME = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml", "woff2": "font/woff2", "mp3": "audio/mpeg"}
LOADER = r"""(function () {
  var veil = document.getElementById("acko-veil");
  setTimeout(function () {
    var P = JSON.parse(document.getElementById("acko-payload").textContent), urls = {};
    for (var p in P.assets) {
      var a = P.assets[p], bin = atob(a[1]), n = bin.length, u = new Uint8Array(n);
      for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
      urls[p] = URL.createObjectURL(new Blob([u], { type: a[0] }));
    }
    window.ASSET_URLS = urls;
    var RE = /assets\/(?:img|deck|fonts|audio)\/[A-Za-z0-9_.\/-]+?\.(?:webp|png|jpe?g|gif|svg|woff2|mp3)/g;
    var swap = function (t) { return t.replace(RE, function (m) { return urls[m] || m; }); };
    var st = document.createElement("style"); st.textContent = swap(P.css); document.head.appendChild(st);
    document.body.insertAdjacentHTML("afterbegin", swap(P.body));
    P.scripts.forEach(function (js) { var s = document.createElement("script"); s.textContent = swap(js); document.body.appendChild(s); });
    if (veil) veil.remove();
  }, 30);
})();"""


def single():
    html = build()
    head, body = html.split("<body>", 1)
    body = body.rsplit("</body>", 1)[0]
    # the styles: linked stylesheets (their url()s made root-relative) and the slides' <style> blocks, in order
    css = []
    for m in re.finditer(r'<link rel="stylesheet" href="([^"?]+)[^"]*">|<style\b[^>]*>(.*?)</style>', head, re.S):
        if m.group(1):
            base = posixpath.dirname(m.group(1))
            text = read(*m.group(1).split("/"))
            text = re.sub(r"url\((['\"]?)(?!data:|https?:|/)([^)'\"]+)\1\)", lambda u: "url(%s)" % posixpath.normpath(posixpath.join(base, u.group(2))), text)
            css.append(text)
        else:
            css.append(m.group(2))
    # the markup (everything before the first script) and the scripts, in order (linked ones inlined)
    markup, scripts = body.split("<script", 1)[0], []
    for m in re.finditer(r'<script src="([^"?]+)[^"]*"></script>|<script\b[^>]*>(.*?)</script>', body, re.S):
        scripts.append(read(*m.group(1).split("/")) if m.group(1) else m.group(2))
    alltext = "\n".join(css) + markup + "\n".join(scripts)
    # what to embed: every literal asset path; files named by key (renders, keyplans: "r-board-op1"); and paths built from a prefix
    want = set(ASSET.findall(alltext))
    for d in ("img", "deck"):
        for f in os.listdir(os.path.join(ROOT, "assets", d)):
            stem = os.path.splitext(f)[0]
            if os.path.isfile(os.path.join(ROOT, "assets", d, f)) and re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(stem), alltext):
                want.add(f"assets/{d}/{f}")
    for pre in set(re.findall(r"(assets/[A-Za-z0-9_./-]*)\$\{", alltext)):
        if pre.rstrip("/") in ("assets/img", "assets/deck", "assets"):
            print(f"  warning: a path is built from just '{pre}' — use ACKO.asset('assets/img/' + key + '.webp') with a known key", file=sys.stderr)
            continue
        d, stem = posixpath.split(pre)
        for f in os.listdir(os.path.join(ROOT, *d.split("/"))):
            if f.startswith(stem): want.add(posixpath.join(d, f))
    assets, missing, total = {}, [], 0
    for p in sorted(want):
        fp = os.path.join(ROOT, *p.split("/"))
        if not os.path.isfile(fp): missing.append(p); continue
        raw = open(fp, "rb").read(); total += len(raw)
        assets[p] = [MIME[p.rsplit(".", 1)[1].lower()], base64.b64encode(raw).decode("ascii")]
    if missing: print("  missing assets (left as paths):", ", ".join(missing), file=sys.stderr)
    payload = json.dumps({"css": "\n".join(css), "body": markup, "scripts": scripts, "assets": assets}, separators=(",", ":")).replace("</", "<\\/")
    title = re.search(r"<title>.*?</title>", head, re.S).group(0)
    html1 = ("<!doctype html>\n<html lang=\"en\" data-theme=\"light\">\n<head>\n<meta charset=\"utf-8\">\n"
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + title + "\n"
             "<style>html,body{margin:0;height:100%;background:#fff}#acko-veil{position:fixed;inset:0;display:grid;place-items:center;"
             "font:500 15px/1.4 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#5222d0;background:#fff;z-index:999}</style>\n"
             "</head>\n<body>\n<div id=\"acko-veil\">ACKO · The Loop · loading…</div>\n"
             "<script id=\"acko-payload\" type=\"application/json\">" + payload + "</script>\n"
             "<script>" + LOADER + "</script>\n</body>\n</html>\n")
    write(os.path.join("dist", SINGLE_NAME), html1)
    print(f"dist/{SINGLE_NAME}: {len(re.findall(r'<section class=.scene', markup))} slides, {len(assets)} files embedded ({total / 1e6:.1f} MB), {len(html1.encode('utf-8')) / 1e6:.1f} MB in all")


if __name__ == "__main__":
    if "--single" in sys.argv:
        unused_warning(order()); single()
    elif "--only" in sys.argv:
        ids = sys.argv[sys.argv.index("--only") + 1].split(",")
        build(ids, "preview.html"); print(f"preview.html: {', '.join(ids)}")
    else:
        unused_warning(order()); html = build(); print(f"index.html: {len(re.findall(r'<section class=.scene', html))} slides")
