# ACKO "The Loop": hand-off, 11 Nov 2026

This file is for a Claude session on another account that hasn't seen the work. Read it all before changing anything. Its companions in the repo are:
- `CLAUDE.md`: house rules
- `HANDOFF.md`: the earlier hand-off, with deeper engine notes
- `README.md`: the long change log
- `SLIDES.md`: the slide-file format
- `PRESENTATION-PATTERNS.md`: methods and gotchas

---

## 1 · The project

- **What:** SKV (Studiokon) is pitching to **ACKO** for its head office: one floor at Regalium, Koramangala, Bengaluru (about 91,000 sq ft, ~640 people). The pitch is an **interactive HTML deck**, presented in person by **Ritika** (SKV's designer), about **20 minutes**.
- **The idea, "The Loop":** ACKO's logo is a Möbius strip. The workplace is a campus joined by one continuous loop, with seven stops: Arrival → Café → Board Room → Meeting Rooms → Collab → Work → Wellness.
- **Design system (her PPT):**
  - **Colour:** white pages, with dark, lavender or grey where the PPT has them; purple `#5222D0` / `#4E29BB`, lilac `#C9B3F3`
  - **Fonts:** Figtree; Square Peg for the handwritten lines
  - **Chrome:** the ACKO | SKV lockup bottom right, the header top left

## 2 · Getting the code

- **Repo:** `RITIKAARULGOPAL/Acko-Presentation` (private on GitHub).
- **Branch to continue from:** **`the-loop/claude/new-changes`**.
  - Tip: `2e213ae`, plus this file's commit.
  - It sits on the 11 Nov re-ordered deck, `206b6d9`.
- **Branch naming:** this presentation's branches are named `the-loop/*`. The repo's own `main` is an earlier deck; leave it alone.
  - `the-loop/main` is the live deck as of 27 Oct. Nothing here has been merged into it yet.

```bash
git clone https://github.com/RITIKAARULGOPAL/Acko-Presentation.git
```
```bash
cd Acko-Presentation && git checkout -b new-changes origin/the-loop/claude/new-changes
```

- **Images and data are in git** (`assets/`, `data/`).
- **Generated files, not in git:** `index.html` (the live deck, built by `python tools/build.py`), `dist/` and `versions/`.
- **Generated files, committed:** `index-approach.html`, `index-open.html` and `index-unfold.html`. Regenerate them with the commands in §5.

## 3 · Run, preview, test

- **Serve the checkout:** `python tools/serve.py [port]`. It rebuilds `index.html` on every load.
  - Restart it after changing `tools/build.py`.
  - Browsers cache these pages hard, so add `?v=<n>` to the URL after regenerating.
- **Pages:**

| URL | What |
|---|---|
| `/index-approach.html` | **The deck to present: the re-ordered deck** (44 slides). `#<slide-id>/<beat>` jumps, for example `#s-open/1` |
| `/index.html` | The live deck, in the PPT's own order (`slides/order.txt`) |
| `/index-unfold.html` | Comparison page: 10 ways the ACKO logo becomes the white Möbius strip (`s-unf-1 … s-unf-10`) |
| `/index-open.html` | Comparison page: the three openings (`s-open-1 … 3`) |
| `/?only=a,b` | Just those slides, joined |

- **Keys:** → / Space next; ← back; F fullscreen; N notes; O overview. Shift+S mutes the deck's sound cues.
- **Test:**
  - `node tools/walk.js --page index-approach.html` needs `puppeteer-core`. On Ritika's machine: `NODE_PATH=C:/Users/Ritika/Mitigata/node_modules`.
  - **Expected:** exactly **17 errors, all `s-layout-sp/9`** (an SVG viewBox going negative), present before 11 Nov. Anything else is new.

## 4 · How a slide works (short)

- **One slide is one file:** `slides/<id>.html`. Only the part between `<!-- slide:start -->` and `<!-- slide:end -->` is used. It holds:
  - the `<section class="scene" id data-part data-title data-steps data-beats data-mins data-notes>`
  - a `<style>` with every rule prefixed `#<id>`
  - `ACKO.slide(id, kit => ({ enter(_, sc), step(k, sc), leave() }))`
- **Beats:** `data-step="n"` (shown from beat n) and `data-only="n"` (only on beat n), or the slide's own `step(k)`.
- **The kit:** `$`, `$$`, `plain`, `reveal`, `later` (timers cleared on leave), `drawPath`, `reduced`, …
- **Build:** `tools/build.py` → `build.build(ids, out)` joins slides into a page.
- **Re-ordered deck only:**
  - `window.ACKO_WOW = true` switches on the "big moments", and `window.ACKO_SECTIONS` names the six sections.
  - Slide-to-slide hand-offs go through `window.ACKO_MORPH`: `mark` in `leave()`, `take` in `enter()`.
- **Gotcha:** a slide's whole `<script>` is one scope. A helper you inject with the same name as one already there (e.g. `build`) silently replaces it.

## 5 · What changed on 11 Nov (this branch), with Ritika's decisions

### 5.1 The story re-ordered: brand first, positive throughout
Her brief: open on ACKO's Möbius and what it means. Then:
- the loop connects and surrounds us
- many lines of business on one loop, like a campus
- the bridges stand for security and protection
- 58% of employees come back to belong, and the brief (a Modern Indian Institution) points to a campus
- "maybe, we've felt this before"
- the site, then the layout and axo
- the material palette, then the emotions (Acker's engagement points), then the renders

The tone must be positive and immersive, with no seams between slides.

**`index-approach.html`, built by `python tools/acko/story/gen_story.py .`:**

| # | Section | Slides |
|---|---|---|
| — | Opening | `s-cover s-team` |
| 01 | The Loop | `s-open` (the opening), `s-mobius` |
| 02 | Belonging | `s-campus` (58% + the brief = a campus → …maybe we've felt this before), `s-memories` |
| 03 | The Site | `s-site s-layout-dd s-pitch s-challenges` |
| 04 | The Plan | `s-loop-w s-strategy s-walk s-layout-sp` |
| 05 | The Palette | `s-palette2 s-material` |
| 06 | The Experience | `s-engage`, the renders `s-w-*`, `s-walkthrough s-wayday` |
| — | Close | `s-thanks-w` (the Loop folds back into the Möbius) |
| — | Appendix | `s-acoustic s-wayfinding s-typologies s-wellbeing s-di s-esg s-skv` |

- **Out of the order** (files kept): `s-approach-w`, `s-start`, `s-challenge`. They told the story problem-first.
- **`s-challenges` reworded as "The Opportunity"**, on this page only (the `OPP` list in `gen_story.py`). This is **draft copy, still to confirm with her**:
  - headline: "One long floor. Room for a whole campus."
  - the three points: Identity / Closeness / Clarity, each written as "from … to …"
- **Lens hand lines:** `LENS` in `gen_story.py`.
- **Source for the brand story:** Social Samosa, 29 Jan 2025, "ACKO rebrands with a logo inspired by the Möbius strip". It gives trust, inclusivity and collaboration, and the line "it's never us versus you; it's always us with you". Credited on screen as "ACKO brand identity, 2025". The lines of business come from `s-journey`.

### 5.2 The opening: ACKO's logo becomes the white Möbius strip
How it got here, in her words:
1. She chose **opening 2, "Into the strip"**: dark and cinematic, the deck's Möbius photo on near-black, the camera leaning into the twist, a lilac line running the strip, the lines of business along it, the twist glowing.
2. "make the logo animate to the mobius white strip and continue." **v1** scaled the logo up and faded it out, and she said "not seamless". **v2** morphed points from the logo to the strip's outline, and she said "still not seamless".
3. "ACKO logo can unfold like a ribbon. Also give me multiple options." **Unfold 1–4**: the strip that appears *is the photo*, revealed along its own line through a soft SVG mask, so there is no second picture to cross-fade.
4. "unfold 1 is fine, but make the ACKO logo itself in ribbon form." **Option 5**. Her next note, "not looking like the logo", led to the **exact mark** (its three original shapes and purples), shown only where the ribbon lies on it. It draws in along the ribbon, then winds off itself while the ribbon runs round the strip.
5. "give more variations." **Options 6–10.**

**The options on `index-unfold.html`:**

| # | Name | What it does |
|---|---|---|
| 1 | Peel round | Flat logo at the twist; one white ribbon peels round the strip |
| 2 | Both ways | The logo's bands part; the strip unrolls both ways |
| 3 | Lavender lead | A lavender ribbon leads, the white strip unrolls behind |
| 4 | Untwist from the centre | The logo, centred, turns edge-on, drops to the twist, then unrolls |
| **5** | **Ribbon logo** (**current opening**, `PICK = 5`) | The exact logo unwinds as a ribbon; a narrow purple head runs round, widening into white |
| 6 | Centre stage | Big centred logo; the ribbon sweeps out to the twist, then round |
| 7 | Purple Möbius first | A full purple Möbius forms (the photo tinted), then washes white |
| 8 | Split unwind | The two bands unwind opposite ways round the strip |
| 9 | Close-up pull-back | The camera starts at 2.6× on the logo and pulls back. Soft at full zoom; raise the canvas resolution for the zoom if she picks it |
| 10 | Ribbon to line | The head narrows into the lilac line, which stays, so beat 2 continues from it |

Beats 2–5 of the opening are the same in all of them:
2. "It's never us versus you; it's always us with you."
3. A loop connects, a loop surrounds.
4. Many lines of business, one loop.
5. Where it bridges, it holds.

**Files** (all in `tools/acko/story/`):
- `gen_unfold.py`: writes `slides/s-unf-1..10.html` and `index-unfold.html`. It **also writes `slides/s-open.html` and `s-open-2.html` from option `PICK`.** To change the deck's opening, set `PICK`, then rebuild (below).
- `ribbon_unfold.js`: the code for options 5–10, injected into the slide. `OPT` holds `place` (twist | centre), `tint` (white | purple), `heads` (1 | 2), `cam` (zoom), `trail`. It draws a route (the mark's centreline → [bridge] → the strip's line) as quads on two canvases:
  - the mark canvas: the exact logo, cut by the ribbon's window
  - the strip canvas: clipped to the photo's alpha by `destination-in`
- `open_base.html`: the frozen template every option is generated from. **Don't delete it.**
- `gen_open.py`: writes `index-open.html`.
- `gen_story.py`: writes `index-approach.html`.
- `mark_morph.py`: the v2 point morph, kept for reference. It writes into `open_base.html`.
- **Frame checks:** `window.__unfold["s-unf-N"](t)` draws any moment, t from 0 to 1.

**Rebuild everything:**
```bash
python tools/acko/story/gen_unfold.py .
```
```bash
python tools/acko/story/gen_story.py .
```
```bash
python tools/acko/story/gen_open.py .
```
```bash
git checkout -- assets/js/shell.js
```
The generators run `build.build`, which rewrites `assets/js/shell.js` with only line-ending changes, so revert it each time.

**Gotchas met here:**
- **Canvas compositing:** `source-in` with several shapes drawn one at a time clears the earlier shapes. Draw the whole logo onto its own canvas first, then composite once.
- **Mask strokes need `butt` caps.** A round cap shows a disc at the start of the path before anything has been revealed.
- **Fills on SVG paths:** a CSS rule like `path { fill: none }` beats a path's `fill="…"` attribute.
- **Writes can fail:** a page can be briefly locked while a walk test runs (`OSError: [Errno 22]`). Run the command again.

### 5.3 Also on this branch
- `HANDOFF.md` and `handoff/wow/`: the earlier hand-off and the generators of the previous, problem-first order, merged in from another session. Kept for reference; their changes are already committed in the slide files.
- `README.md` and `PRESENTATION-PATTERNS.md` (§29) describe all of this in more detail.

## 6 · Open items
1. **Her pick among unfold 5–10.** Set `PICK` in `gen_unfold.py` and rebuild. If she picks 9, sharpen the close-up.
2. **Confirm the draft copy:** The Opportunity (`OPP`) and the lens lines (`LENS`) in `gen_story.py`.
3. **Not rebuilt since 11 Nov:** `dist/` (`python tools/build.py --single` makes the self-contained `dist/ACKO-The-Loop.html`) and `versions/`. The single file is built from `order.txt`, the live deck. To present the re-ordered deck offline, it needs its own single-file build; ask her first.
4. **Nothing merged into `the-loop/main`.** Do it only if she asks.
5. **The 17 known walk-test errors** on `s-layout-sp/9`, from before 11 Nov.

## 7 · Working with Ritika
- **How she reviews:** in the app's preview pane, often pointing with screenshots, in short messages ("not seamless", "show in preview", "give more variations"). Follow her words literally.
- **When she asks for ways or variations:** build every option, working, on one comparison page (with a chip naming each), and let her pick. Don't describe options in text.
- **When she's using the preview tab:** check your work in a background tab.
- **Commits and pushes:** confirm anything big first, and push only when she asks.
  - Pushes go to the `the-loop/` names. This branch was pushed with: `git push origin refs/heads/claude/new-changes:refs/heads/the-loop/claude/new-changes`
  - The repo's push config also maps `main` → `the-loop/main` and `slide/*` → `the-loop/slide/*`.
- **New methods:** log them in `PRESENTATION-PATTERNS.md`.

*Paths like `C:\Users\Ritika\…` in the other notes are on Ritika's machine. In a fresh clone, read them relative to the repo root.*
