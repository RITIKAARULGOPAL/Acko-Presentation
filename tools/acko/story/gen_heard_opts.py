# index-heard.html: five immersive ways to open on "We heard you" (17 Nov, Ritika: "give variations in this slide. make it immersive so
# it catches client's attention since its the very 1st slide"), after the slide as it is now, each marked with a small chip. The
# twelve points are the MoM's, word for word, in every one; only the staging changes. The options are slides/s-heard-1..5.html (not
# in order.txt); her pick goes into slides/s-heard.html.
# The words (17 Nov, Ritika: "instead of what you told us and we heard you, give different texts. give multiple variations. ill pick
# one"): a wording bar at the foot of the page (Now, A … H) sets the headline, the label, the hand line and the slide's title on all
# six at once, so she picks the words and the design together; the choice is remembered in this browser. A headline is shrunk to its
# line limit if a wording runs long. The slides themselves keep "We heard you."; her pick is written into s-heard.html.
#   python tools/acko/story/gen_heard_opts.py .
import sys, os
os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, "tools")
import build
sys.path.insert(0, os.path.join("tools", "acko", "story"))
from wordbar import chips, inject, wordbar

OPTS = [("s-heard", "We heard you · As now"),
        ("s-heard-1", "We heard you · 1 · Twelve voices"),
        ("s-heard-2", "We heard you · 2 · On your floor"),
        ("s-heard-3", "We heard you · 3 · Twelve windows"),
        ("s-heard-4", "We heard you · 4 · The minutes"),
        ("s-heard-5", "We heard you · 5 · One loop")]

# each wording: the headline in two parts (b is the accent: violet in 1 and 3, its own line in 3), the label, the hand line, the title
WORDS = [
    ("Now", "We heard", "you.", "What you told us", "Everything that follows is built on what you told us.", "We heard you"),
    ("A", "You spoke.", "We listened.", "From our last meeting", "Each of these shaped what you’ll see today.", "You spoke, we listened"),
    ("B", "Your words,", "our brief.", "Twelve points from our meeting", "Everything that follows answers these twelve.", "Your words, our brief"),
    ("C", "You asked.", "We answered.", "What you asked of us", "Every one of them is in this design.", "You asked, we answered"),
    ("D", "It starts", "with you.", "What we took away", "This is where today’s design begins.", "It starts with you"),
    ("E", "Noted.", "Every word.", "The minutes of our meeting", "Now let us show you what we did with them.", "Noted"),
    ("F", "Straight from", "the room.", "Our last meeting, in twelve points", "Each one is answered in the pages ahead.", "Straight from the room"),
    ("G", "First,", "your words.", "Before our ideas", "Then, what we made of them.", "First, your words"),
    ("H", "Back to", "your brief.", "Twelve points we carried forward", "Every page ahead began here.", "Back to your brief"),
]
# where each slide keeps its words, and how many lines its headline may take
MAP = {
    "s-heard":   {"title": ".hdr b", "kick": ".hd-cols b", "head": ".hd-copy h2", "hand": ".hd-close", "lines": 1},
    "s-heard-1": {"title": ".hdr b", "kick": None, "head": ".vc-head", "hand": ".vc-close", "lines": 1},
    "s-heard-2": {"title": ".hdr b", "kick": None, "head": ".fl-copy h2", "hand": ".fl-close", "lines": 1},
    "s-heard-3": {"title": ".hdr b", "kick": ".wn-k", "head": ".wn-side h2", "hand": ".wn-side .hand", "lines": 2},
    "s-heard-4": {"title": ".hdr b", "kick": ".mn-k", "head": ".mn-head", "hand": ".mn-close", "lines": 1},
    "s-heard-5": {"title": ".hdr b", "kick": ".lp-k", "head": ".lp-mid h2", "hand": ".lp-mid .hand", "lines": 1},
}
OUT = "index-heard.html"
build.build([i for i, _ in OPTS], OUT)
h = open(OUT, encoding="utf-8").read()
h = inject(chips(h, OPTS), wordbar(WORDS, MAP, "acko-heard-words"))   # tools/acko/story/wordbar.py
open(OUT, "w", encoding="utf-8").write(h)
print("ok", OUT, len(OPTS), "·", len(WORDS), "wordings")
