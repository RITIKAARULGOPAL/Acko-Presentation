# The memories' close (10 Nov): lines written word by word; each word its own <span class="w" style="--w:n">, each run keeping its font
import re
def words(runs):
    """runs: [("h"|"b"|"t", text)]; h = the hand (.wi-h), b = Figtree bold, t = plain text of the line's own font"""
    n, out = 0, []
    for kind, txt in runs:
        seg = ""
        for p in re.split(r"(\s+)", txt):
            if not p: continue
            if p.isspace(): seg += p
            else: seg += '<span class="w" style="--w:%d">%s</span>' % (n, p); n += 1
        out.append('<span class="wi-h">%s</span>' % seg if kind == "h" else "<b>%s</b>" % seg if kind == "b" else seg)
    return "".join(out)

def close():
    """the campus feeling, ACKO's promise (beat 7); the question, and where it has to happen (beat 8)"""
    return ('<div class="mem-wi"><div class="mw-col">'
            '<p class="mw-l1">' + words([("h", "A campus is where we first felt safe among people.")]) + '</p>'
            '<p class="mw-l2"><b>Protection</b> is what ACKO promises its customers.</p>'
            '<p class="wi-q mw-q">' + words([("h", "What if the workplace kept that promise"), ("b", " to its own people?")]) + '</p>'
            '<p class="mw-l4">So we started where it has to happen: one floor in Koramangala.</p>'
            '</div></div>')
