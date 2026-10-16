"""One git worktree per slide, for working on slides in parallel (see CLAUDE.md), and the merge that joins them again.

    python tools/worktrees.py add        a worktree .claude/worktrees/<id> on branch slide/<id> for every slide in order.txt
                                          (from main; existing ones are left alone)
    python tools/worktrees.py status     per slide: commits ahead of main, uncommitted changes in its worktree
    python tools/worktrees.py merge      merge every slide branch that has commits into the current branch (--no-ff, deck order);
                                          stops at the first conflict
    python tools/worktrees.py table      rewrite the branch table in CLAUDE.md (between its worktrees markers)
    python tools/worktrees.py remove --yes      remove all slide worktrees and delete their branches (asks for --yes)
Run from the main folder (C:\\Users\\Ritika\\Acko 1610), not from inside a worktree.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WT = os.path.join(ROOT, ".claude", "worktrees")
BASE = "main"
# where each slide comes from in the 20.10.26 design deck
DECK = {"s-cover": "1", "s-team": "2", "s-aspiration": "3", "s-acko": "4", "s-journey": "5", "s-challenge": "6–7", "s-memories": "8",
        "s-whatif": "9", "s-mobius": "10", "s-loop": "11–12", "s-strategy": "13", "s-site": "new", "s-floor": "new", "s-challenges": "14",
        "s-typologies": "15", "s-palette1": "16–19", "s-palette2": "20–23", "s-w-board": "24–25", "s-w-dept": "26–27", "s-w-sprint": "28–29",
        "s-w-arena": "30–31", "s-w-arena2a": "32–33", "s-w-library": "34", "s-w-garden": "35–36", "s-w-exec": "37", "s-w-cafe1": "38, 40",
        "s-w-cafe2": "39, 41", "s-w-coffee": "42", "s-w-mothers": "43", "s-w-zen": "44", "s-w-studio": "45", "s-engage": "46",
        "s-material": "47", "s-acoustic": "48", "s-wayfinding": "52", "s-layout": "53–54", "s-blowup": "55–57", "s-axo": "58–60",
        "s-occupancy": "61", "s-thanks": "—", "s-wellbeing": "49", "s-di": "50", "s-esg": "51", "s-skv": "SKV's deck"}


def git(*args, cwd=ROOT, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def slides():
    with open(os.path.join(ROOT, "slides", "order.txt"), encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def title(sid):
    try:
        text = open(os.path.join(ROOT, "slides", sid + ".html"), encoding="utf-8").read()
        return re.search(r'data-title="([^"]*)"', text).group(1).replace("&amp;", "&")
    except (OSError, AttributeError):
        return ""


def branches():
    return set(git("branch", "--format=%(refname:short)").splitlines())


def add():
    have, made = branches(), 0
    os.makedirs(WT, exist_ok=True)
    for sid in slides():
        path, br = os.path.join(WT, sid), f"slide/{sid}"
        if os.path.isdir(path):
            continue
        if br in have:
            git("worktree", "add", path, br)
        else:
            git("worktree", "add", path, "-b", br, BASE)
        made += 1
        print(f"  {br:<22} .claude/worktrees/{sid}")
    print(f"{made} worktrees made; {len(slides())} slides in all")


def status():
    have = branches()
    print(f"{'slide':<16} {'ahead':>5}  {'changes':<8} title")
    for sid in slides():
        br = f"slide/{sid}"
        if br not in have:
            print(f"{sid:<16} {'—':>5}  {'no branch':<8}"); continue
        ahead = git("rev-list", "--count", f"{BASE}..{br}")
        path = os.path.join(WT, sid)
        dirty = (git("status", "--porcelain", cwd=path) if os.path.isdir(path) else "")
        print(f"{sid:<16} {ahead:>5}  {'yes' if dirty else '':<8} {title(sid)}")


def merge():
    if git("status", "--porcelain"):
        raise SystemExit("the current folder has uncommitted changes: commit or stash them first")
    here, have, done = git("rev-parse", "--abbrev-ref", "HEAD"), branches(), 0
    for sid in slides():
        br = f"slide/{sid}"
        if br not in have or git("rev-list", "--count", f"{here}..{br}") == "0":
            continue
        r = subprocess.run(["git", "merge", "--no-ff", "-m", f"Merge {br}", br], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print(f"conflict merging {br}: resolve it (keep both sides' intent), commit, then run merge again\n{r.stdout}{r.stderr}")
            sys.exit(1)
        done += 1
        print(f"  merged {br}")
    print(f"{done} slide branches merged into {here}. Next: node tools/walk.js, then python tools/build.py --single")


def table():
    rows = ["| # | Slide (file) | Deck slides | Title | Branch | Worktree |", "|---|---|---|---|---|---|"]
    for n, sid in enumerate(slides(), 1):
        rows.append(f"| {n} | `slides/{sid}.html` | {DECK.get(sid, '')} | {title(sid)} | `slide/{sid}` | `.claude/worktrees/{sid}` |")
    p = os.path.join(ROOT, "CLAUDE.md")
    text = open(p, encoding="utf-8").read()
    block = "<!-- worktrees:start (python tools/worktrees.py table) -->\n" + "\n".join(rows) + "\n<!-- worktrees:end -->"
    if "<!-- worktrees:start" in text:
        text = re.sub(r"<!-- worktrees:start.*?<!-- worktrees:end -->", lambda m: block, text, flags=re.S)
    else:
        text = text.replace("## Parallel sessions (one per slide), when Ritika asks", "## Which slide you are\n\n"
                            "A session opened in `.claude/worktrees/<id>` (on branch `slide/<id>`) owns that one slide. The main folder on `main` is the merge session.\n\n"
                            + block + "\n\n## Parallel sessions (one per slide), when Ritika asks")
    open(p, "w", encoding="utf-8").write(text)
    print(f"CLAUDE.md: table of {len(rows) - 2} slides")


def remove():
    if "--yes" not in sys.argv:
        raise SystemExit("this removes every slide worktree and deletes its branch, with any uncommitted work: add --yes to go ahead")
    for sid in slides():
        path, br = os.path.join(WT, sid), f"slide/{sid}"
        if os.path.isdir(path):
            git("worktree", "remove", "--force", path)
        if br in branches():
            git("branch", "-D", br)
        print(f"  removed {br}")
    git("worktree", "prune")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"add": add, "status": status, "merge": merge, "table": table, "remove": remove}.get(cmd, lambda: print(__doc__))()
