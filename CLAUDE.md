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

## Parallel sessions (one per slide), when Ritika asks
- **Setup** (from the main folder, on `main`):
  ```bash
  git worktree add .claude/worktrees/<id> -b slide/<id>
  ```
  One per slide.
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
  2. Merge every `slide/<id>` that has commits, with `--no-ff`, in deck order. Conflicts are rare, because each slide is its own file; `order.txt` is the usual one.
  3. `node tools/walk.js` must report 0 errors.
  4. `python tools/build.py --single`, then `node tools/walk.js --page dist/ACKO-The-Loop.html --single` must report 0 errors and no file requests.
  5. Export `versions/Acko-20min/` and its zip, update the README journey table, then fast-forward `main`.
  6. Remove worktrees only with Ritika's OK. Push only when asked.

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
  - **Site:** short site, sun and fire beats before the challenges.
- **The thread:** the Loop's seven stops (Arrival, Café, Board Room, Meeting Rooms, Collab, Work, Wellness, each with its words).
- **Before editing:** confirm anything big with Ritika, and follow her screenshots and comments literally.
- **Log new patterns** in `PRESENTATION-PATTERNS.md`, and ask which presenter cursor a slide uses while building it.
