"""Builds index.html from slides/: the page shell (slides/_shell.html) with every slide in slides/order.txt, in that order.

usage: python tools/build.py             writes index.html (the file you double-click to present, offline)
tools/serve.py runs this on every page load, so while editing just save a slide and refresh.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLIDES = os.path.join(ROOT, "slides")
MARK = re.compile(r"^<!-- @slides\b.*?-->\n", re.M)


def read(*p):
    with open(os.path.join(SLIDES, *p), encoding="utf-8") as f:
        return f.read()


def order():
    ids = [l.strip() for l in read("order.txt").splitlines()]
    return [i for i in ids if i and not i.startswith("#")]


def build():
    ids, problems = order(), []
    seen = set()
    for i in ids:
        if i in seen: problems.append(f"{i} is listed twice in order.txt")
        seen.add(i)
        if not os.path.exists(os.path.join(SLIDES, i + ".html")): problems.append(f"{i} is in order.txt but slides/{i}.html is missing")
        elif f'id="{i}"' not in read(i + ".html"): problems.append(f'slides/{i}.html has no section with id="{i}"')
    if problems: raise SystemExit("slides: " + "; ".join(problems))
    unused = sorted(f[:-5] for f in os.listdir(SLIDES) if f.endswith(".html") and not f.startswith("_") and f[:-5] not in seen)
    if unused: print("not in order.txt (hidden):", ", ".join(unused), file=sys.stderr)
    shell = read("_shell.html")
    if len(MARK.findall(shell)) != 1: raise SystemExit("slides/_shell.html needs exactly one <!-- @slides --> line")
    body = "\n".join(read(i + ".html").rstrip("\n") + "\n" for i in ids)
    return MARK.sub(lambda m: body, shell)


def write():
    html = build()
    p = os.path.join(ROOT, "index.html")
    try:
        with open(p, encoding="utf-8", newline="") as f:
            if f.read() == html: return html
    except FileNotFoundError:
        pass
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    return html


if __name__ == "__main__":
    write()
    print(f"index.html: {len(order())} slides")
