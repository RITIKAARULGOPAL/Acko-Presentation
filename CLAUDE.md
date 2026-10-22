# ACKO × SKV presentation: rules for every session

This is SKV's interactive design presentation for ACKO's head office (Regalium, Koramangala; Layout Option 02A; meeting on 20 Oct 2026).
- **Ritika (SKV) presents it in person.**
- **What gets presented:** one self-contained file, `dist/ACKO-The-Loop.html`, built from the slides.
- **Read first:** `README.md` (the journey and the tools) and `SLIDES.md` (how a slide file works).

## The slide file is the unit of work
- **One slide, one file.** Every slide is `slides/<id>.html`: a complete page you can open on its own. Between `<!-- slide:start -->` and `<!-- slide:end -->` it holds:
  - its `<section class="scene" id="<id>">`
  - its `<style>`, every rule prefixed `#<id>`
  - its `<script>`: `ACKO.slide("<id>", (K) => ({ enter, step, leave }))`
- **Its own images** live in `assets/img/<id>/`.
- **Order:** `slides/order.txt`. A slide's section is its `data-part`, not its line.
- **Shared, and not to be changed in a slide session:** `assets/js/app.js` (engine and kit), `assets/css/app.css`, `slides/_shell.html`, `data/`, `tools/`.
  - If a slide truly needs a shared change, keep it minimal and start a commit line with `Shared:`.
- **Generated, never hand-edit:** `index.html`, `preview.html`, `assets/js/shell.js`, `dist/`.

## GitHub
- **Repository:** `RITIKAARULGOPAL/Acko-Presentation` (private), alongside the earlier Acko decks. This presentation lives under its own branch names there, so the repo's `main` is untouched:
  - `main` here pushes to **`the-loop/main`**
  - each `slide/<id>` pushes to **`the-loop/slide/<id>`**
- **How:** the mapping is set in this repo's push config, so a plain `git push` from the main folder pushes `main` and every slide branch to those names.
- **When:** push only when Ritika asks.

## Which slide you are

A session opened in `.claude/worktrees/<id>` (on branch `slide/<id>`) owns that one slide. The main folder on `main` is the merge session.

<!-- worktrees:start (python tools/worktrees.py table) -->
| # | Slide (file) | Deck slides | Title | Branch | Worktree |
|---|---|---|---|---|---|
| 1 | `slides/s-cover.html` | 1 | Cover | `slide/s-cover` | `.claude/worktrees/s-cover` |
| 2 | `slides/s-team.html` | 2 | Meet the team | `slide/s-team` | `.claude/worktrees/s-team` |
| 3 | `slides/s-aspiration.html` | 3 | Workplace aspiration | `slide/s-aspiration` | `.claude/worktrees/s-aspiration` |
| 4 | `slides/s-acko.html` | 4 | What defines ACKO | `slide/s-acko` | `.claude/worktrees/s-acko` |
| 5 | `slides/s-journey.html` | 5 | We respect the journey | `slide/s-journey` | `.claude/worktrees/s-journey` |
| 6 | `slides/s-challenge.html` | 6–7 | The challenge at hand | `slide/s-challenge` | `.claude/worktrees/s-challenge` |
| 7 | `slides/s-memories.html` | 8 | Maybe, we've felt this before | `slide/s-memories` | `.claude/worktrees/s-memories` |
| 8 | `slides/s-whatif.html` | 9 | What if | `slide/s-whatif` | `.claude/worktrees/s-whatif` |
| 9 | `slides/s-mobius.html` | 10 | The Möbius | `slide/s-mobius` | `.claude/worktrees/s-mobius` |
| 10 | `slides/s-loop.html` | 11–12 | The Loop | `slide/s-loop` | `.claude/worktrees/s-loop` |
| 11 | `slides/s-strategy.html` | 13 | Campus strategy | `slide/s-strategy` | `.claude/worktrees/s-strategy` |
| 12 | `slides/s-site.html` | new | The site | `slide/s-site` | `.claude/worktrees/s-site` |
| 13 | `slides/s-challenges.html` | 14 | What's our challenge | `slide/s-challenges` | `.claude/worktrees/s-challenges` |
| 14 | `slides/s-typologies.html` | 15 | Workstation typologies | `slide/s-typologies` | `.claude/worktrees/s-typologies` |
| 15 | `slides/s-palette1.html` | 16–19 | The campus palette 01 | `slide/s-palette1` | `.claude/worktrees/s-palette1` |
| 16 | `slides/s-palette2.html` | 20–23 | The campus palette 02 | `slide/s-palette2` | `.claude/worktrees/s-palette2` |
| 17 | `slides/s-w-board.html` | 24–25 | State Room · Boardroom | `slide/s-w-board` | `.claude/worktrees/s-w-board` |
| 18 | `slides/s-w-dept.html` | 26–27 | Departmental Room | `slide/s-w-dept` | `.claude/worktrees/s-w-dept` |
| 19 | `slides/s-w-sprint.html` | 28–29 | Quick Sprint Room | `slide/s-w-sprint` | `.claude/worktrees/s-w-sprint` |
| 20 | `slides/s-w-arena.html` | 30–31 | Work Arena · Neighbourhood | `slide/s-w-arena` | `.claude/worktrees/s-w-arena` |
| 21 | `slides/s-w-arena2a.html` | 32–33 | Work Arena · Option 2A | `slide/s-w-arena2a` | `.claude/worktrees/s-w-arena2a` |
| 22 | `slides/s-w-library.html` | 34 | Work Arena · Library | `slide/s-w-library` | `.claude/worktrees/s-w-library` |
| 23 | `slides/s-w-garden.html` | 35–36 | The Acker Garden | `slide/s-w-garden` | `.claude/worktrees/s-w-garden` |
| 24 | `slides/s-w-exec.html` | 37 | Executive Room | `slide/s-w-exec` | `.claude/worktrees/s-w-exec` |
| 25 | `slides/s-w-cafe1.html` | 38, 40 | Cafe · View 1 | `slide/s-w-cafe1` | `.claude/worktrees/s-w-cafe1` |
| 26 | `slides/s-w-cafe2.html` | 39, 41 | Cafe · View 2 | `slide/s-w-cafe2` | `.claude/worktrees/s-w-cafe2` |
| 27 | `slides/s-w-coffee.html` | 42 | Coffee Point | `slide/s-w-coffee` | `.claude/worktrees/s-w-coffee` |
| 28 | `slides/s-w-mothers.html` | 43 | Mothers Room | `slide/s-w-mothers` | `.claude/worktrees/s-w-mothers` |
| 29 | `slides/s-w-zen.html` | 44 | Zen Room | `slide/s-w-zen` | `.claude/worktrees/s-w-zen` |
| 30 | `slides/s-w-studio.html` | 45 | Studio Room | `slide/s-w-studio` | `.claude/worktrees/s-w-studio` |
| 31 | `slides/s-engage.html` | 46 | Acker's engagement points | `slide/s-engage` | `.claude/worktrees/s-engage` |
| 32 | `slides/s-material.html` | 47 | Material strategy | `slide/s-material` | `.claude/worktrees/s-material` |
| 33 | `slides/s-acoustic.html` | 48 | Acoustic strategy | `slide/s-acoustic` | `.claude/worktrees/s-acoustic` |
| 34 | `slides/s-wayfinding.html` | 52 | Wayfinding | `slide/s-wayfinding` | `.claude/worktrees/s-wayfinding` |
| 35 | `slides/s-layout.html` | 53–54 | Layout · Option 02A | `slide/s-layout` | `.claude/worktrees/s-layout` |
| 36 | `slides/s-blowup.html` | 55–57 | Blown up X · Y · Z | `slide/s-blowup` | `.claude/worktrees/s-blowup` |
| 37 | `slides/s-axo.html` | 58–60 | Schematic axonometric | `slide/s-axo` | `.claude/worktrees/s-axo` |
| 38 | `slides/s-thanks.html` | — | Thank you | `slide/s-thanks` | `.claude/worktrees/s-thanks` |
| 39 | `slides/s-wellbeing.html` | 49 | Well-being by design | `slide/s-wellbeing` | `.claude/worktrees/s-wellbeing` |
| 40 | `slides/s-di.html` | 50 | Designed for all | `slide/s-di` | `.claude/worktrees/s-di` |
| 41 | `slides/s-esg.html` | 51 | ESG strategy | `slide/s-esg` | `.claude/worktrees/s-esg` |
| 42 | `slides/s-skv.html` | SKV's deck | About SKV | `slide/s-skv` | `.claude/worktrees/s-skv` |
<!-- worktrees:end -->

## Parallel sessions (one per slide), when Ritika asks
- **Setup:** done (16 Oct). `python tools/worktrees.py add` makes any missing worktree: `.claude/worktrees/<id>` on `slide/<id>`, one per slide in `order.txt`.
- **Who has work:** `python tools/worktrees.py status` shows each slide's commits ahead of `main` and any uncommitted changes.
- **In a slide worktree:**
  - Change only `slides/<id>.html` and `assets/img/<id>/`.
  - Commit small and often on `slide/<id>`, and put Ritika's decisions in the message ("Ritika: …").
  - Never push, merge, rebase or switch branches.
- **Before every commit:**
  - `node tools/walk.js --slide <id>`, then look at the screenshots.
  - `node tools/walk.js --page slides/<id>.html` (it runs on its own).
  - Both report 0 errors. puppeteer-core needs `NODE_PATH=C:/Users/Ritika/Mitigata/node_modules`.
- **The merge session (main folder):**
  1. Create `feat/merge` from `main`.
  2. `python tools/worktrees.py merge` merges every `slide/<id>` that has commits, with `--no-ff`, in deck order, and stops at a conflict. Conflicts are rare, because each slide is its own file; `order.txt` is the usual one.
  3. `node tools/walk.js` must report 0 errors.
  4. `python tools/build.py --single`, then `node tools/walk.js --page dist/ACKO-The-Loop.html --single` must report 0 errors and no file requests.
  5. Export `versions/Acko-20min/` and its zip, update the README journey table, then fast-forward `main`.
  6. Remove worktrees only with Ritika's OK (`python tools/worktrees.py remove --yes`). Push only when asked.

## Ritika's standing rules
- **Design system = her PPT** (`20.10.26 _ ACKO Presentation _ Design Deck.pptx`):
  - **Pages:** white; dark, lavender or grey where the PPT has them.
  - **Colour:** purple `#5222D0` / `#4E29BB` on key words, maroon `#980000` for entrances, camera marks and the fire line.
  - **Fonts:** Figtree (with italics), Square Peg for the handwritten lines, Poppins, Lexend.
  - **Chrome:** the header top left, the copyright bottom left, the ACKO | SKV lockup bottom right.
- **The story:**
  - **Order:** the PPT's own.
  - **Palettes:** two chapters.
  - **The walk:** each space shows OP 01 then OP 02.
  - **Length:** about 20 minutes.
  - **Site:** a short site beat before the challenges (the floor's sun and fire beats removed 22 Oct, Ritika).
- **The thread:** the Loop's seven stops (Arrival, Café, Board Room, Meeting Rooms, Collab, Work, Wellness, each with its words).
- **Before editing:** confirm anything big with Ritika, and follow her screenshots and comments literally.
- **Log new patterns** in `PRESENTATION-PATTERNS.md`, and ask which presenter cursor a slide uses while building it.
