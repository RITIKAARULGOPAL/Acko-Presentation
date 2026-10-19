# ACKO · The Loop: interactive presentation

SKV's design presentation for **ACKO's head office**:
- **Where:** Regalium, Koramangala, Bengaluru, 3rd floor, one floor of 91,000 sq ft.
- **The layout:** Option 02A, with 651 workstations.
- **When:** the meeting is on 20 Oct 2026.

It's the 20.10.26 design deck (`20.10.26 _ ACKO Presentation _ Design Deck.pptx`) as one continuous, offline HTML journey, in the deck's own order and design, presented from **one self-contained file**. Each slide is its own page, so people can work on slides separately. The engine is forked from the Mitigata presentation.

## Open it

**To present:** double-click **`dist/ACKO-The-Loop.html`** in Chrome or Edge, then press **F** for fullscreen.
- It is the whole presentation in one file (about 46 MB): every image, font, script and the walk music are inside.
- It needs nothing beside it, so it opens from anywhere, from email or a USB stick, offline.
- Build it with `python tools/build.py --single`.

**To work on it:**
- `index.html` is the same deck, linking `assets/` and `data/`. `python tools/build.py` writes it.
- While editing, run `python tools/serve.py`, or use the **acko** preview, which rebuilds it on every page load. `/?only=s-loop,s-site` shows just those slides.

## On GitHub

`RITIKAARULGOPAL/Acko-Presentation` (private):
- **`the-loop/main`:** this presentation.
- **`the-loop/slide/<id>`:** one branch per slide, for working in parallel (see `CLAUDE.md`).

The repo's own `main` holds the earlier Acko decks and is untouched.

## Working on slides separately

Every slide is **its own HTML page**, `slides/<id>.html`:
- **Open it on its own** (double-click, offline) to see and change it.
- **Hand it back:** people work on different slides at the same time, and the build joins them in the order of `slides/order.txt`.
- **Teammates:** see **`SLIDES.md`**.
- **Parallel Claude sessions** (one git worktree per slide): see **`CLAUDE.md`**.
- **A new slide:** start from `slides/_template.html`.

**Inside a slide file**, between `<!-- slide:start -->` and `<!-- slide:end -->`:
- its section
- its `<style>`, prefixed `#<id>`
- its `<script>`: `ACKO.slide(id, (K) => ({ enter, step, leave }))`

`K` is the engine's kit:
- helpers: `reveal`, `countUp`, `typeWords`, `drawPath`
- the world: `plain`, `world`, `shade`, `PHOTO`
- navigation and assets: `go`, `state`, `asset`
- the shared layout plan: `plan`

**Shared classes** need no script:
- walk slides (`class="walk"`, configured by `data-walk`)
- palettes (`class="palette"`, `data-renders`)
- rebuilt deck pages (`class="vpage"`)

## Present it

| Key | Action |
|---|---|
| `→` `Space` `PageDown` (clicker) | Next beat |
| `←` `PageUp` | Previous beat |
| `N` | Speaker notes, with the time per chapter and in total (click the time to reset it) |
| `O` | Index of every chapter and beat |
| `F` | Fullscreen |
| `B` | Blank screen |
| `L` | Laser pointer, with a fading trail |
| SKV logo / ACKO logo (bottom right) | Open About SKV / back to where you were |

**Every beat works with → alone**; the animations run by themselves.

**Three decks.** The arrows stay inside the one on screen:
- **The presentation**
- **The Appendix:** from the index, or from the last page
- **About SKV:** from the SKV logo

**Interaction:**
- **Layout and blow-ups:**
  - Scroll to zoom on the cursor, drag to pan, and double-click to go back to the beat's view.
  - On *Six neighbourhoods*, hover a row to pick out that neighbourhood.
- **The walk:** music on or off, pan mode (drag the render), and keyplan on or off.

## The journey (≈ 20 min, 65 beats)

The PPT's own order. Ritika's choices (16 Oct):
- the palettes are two chapters
- each space shows OP 01, then OP 02
- short site, sun and fire beats come before the challenges

| Deck slides | Chapter | Beats | What happens |
|---|---|---|---|
| 1 | Cover | 1 | The stairs, the ACKO wordmark, the bid facts |
| 2 | Meet the team | 1 | Ten portraits, one after another |
| 3 | Workplace aspiration | 1 | Three cues rise in: acoustic excellence, real nature, an honest palette |
| 4 | What defines ACKO | 1 | Five values open like shutters, then turn to their second picture |
| 5 | We respect the journey | 2 | Why insurance (the collage, on white); then, as the deck's one click plays it, the collage gives way to the road, the founder's words and the 2016 → 2025 timeline flying in |
| 6–7 | The challenge at hand | 2 | The challenge: the four words and the question; then the words turn into the solution's and "One Place One Experience" |
| 8 | Maybe we've felt this before | 1 | A dotted campus path draws; the six memories come up along it |
| 9 | What if | 1 | The question, in the deck's two fonts |
| 10 | The Möbius | 1 | A live 3D Möbius strip, ACKO's own mark, with the copy inside the loop |
| 11–12 | The Loop | 2 | People and trees along a line; then the ribbon writes itself (the deck's GIF) and the seven stops come up with their words as it reaches them |
| 13 | Campus strategy | 1 | The deck's animated axo, keyed out of its green screen |
| new | The site | 1 | A vector map of Koramangala that closes in on Regalium and turns 11.5° to line up with the plans |
| new | The floor | 2 | The bare plate: the sun across an equinox day and the 6 m daylight band; then fire first (exit rings, the eight measured paths, the compartment line) |
| 14 | What's our challenge | 3 | On the axo of the bare floor: a uniform desk grid, the long walk to lunch, then the route draws (245 m) |
| 15 | Workstation typologies | 1 | Types 1–4; the seats add to 648, +3 cabins = 651 |
| 16–19 | Campus palette 01 | 4 | The board builds, then its three renders full bleed |
| 20–23 | Campus palette 02 | 4 | The same, for palette 02 |
| 24–45 | Visual direction: the walk | 22 | One slide per space, OP 01 then OP 02, each with its Loop words and the keyplan's camera mark |
| 46, 47, 48, 52 | Value addition | 4 | Engagement points, materials, acoustics (NRC 0.70–0.90), wayfinding (Nalanda, Sabha, Takshashila) |
| 53–54 | Layout · Option 02A | 2 | The plan and its legend; then the six neighbourhoods draw in and their seats count up |
| 55–57 | Blown up X · Y · Z | 3 | The same plan flies into each blow-up; the fire compartment line draws on Y |
| 58–60 | Schematic axonometric | 3 | West, middle, east, with the leaders drawn out to their spaces |
| 61 | Occupancy chart | 1 | Brief against Option 2A, row by row; shortfalls in maroon, more than asked in purple |
| — | Thank you | 1 | Buttons to the Appendix and About SKV |

**Appendix:** well-being (49), D&I (50) and ESG (51), shown as the deck's own pages.

**About SKV:** SKV's own deck, carried over from the Mitigata presentation.

## The look (from the deck)

- **Pages:** white, with these exceptions:
  - black for the cover, team, memories and walk
  - lavender `#D2C9EB` for the challenge pair
  - grey `#EFEFEF` for the brand page

  Each slide sets its own mode with `data-mode`.
- **Colour:** purple `#5222D0` / `#4E29BB` on key words, lilac `#C9B3F3`, plum `#6F2F9F`, and maroon `#980000` for entrances, camera marks and the fire line.
- **Fonts** (all OFL, in `assets/fonts/`): Figtree with italics, Square Peg (the handwritten lines), Poppins (labels) and Lexend (numerals).
- **Layout:** every slide is a 16:9 page measured in deck points (`--pt`), so positions match the PPT. The chrome is the deck's: the header top left, the copyright bottom left and the ACKO | SKV lockup bottom right.

## Where the content comes from

- **Words and images:** from the 20.10.26 deck.
  - `tools/acko/extract_assets.py` cuts every image out by name (`PICK`), with the deck's crop and rotation, and keys the green-screen animation.
  - `tools/acko/deck_inventory.py`, `deck_text.py`, `deck_layout.py` and `deck_anim.py` read the deck's layout, text, crops and click order.
  - `tools/acko/make_value_slides.py` writes the typology and value-addition pages.
- **The layout, until the DXF arrives:**
  - `tools/acko/deck_plan.py` composes the deck's four plan tiles (slides 53–57) into `assets/img/plan-full.webp`.
  - It also lifts the neighbourhood outlines, the arrival zones, the fire compartment line and the entrances as vectors, into `data/deck-plan.js`.
- **The site and the bare floor:** from the earlier Acko analysis (Acko New 01: test fit 03, the same shell). `tools/acko/site_floor.py` writes `data/site-floor.js`.
  - map: Overture/OSM
  - sun: NOAA formulas
  - exit paths: measured on the drawing (to be confirmed against NBC with the fire consultant)
- **The walk's keyplans:** each render slide's keyplan crop and maroon camera mark, read from the deck, in `data/keyplans.js`.
- **Pages still shown as deck images:** `assets/deck/s49–51.webp` (Appendix).

## What to drop in next (`inputs/`, not committed)

- **`inputs/layout.dxf`:** Option 02A as DXF 2018, with the `AC_*` layers of test fit 03.
  - It replaces the deck plan with the drawing: hover rooms, highlight typologies, true camera positions.
  - Optional: an `AC_CAM` layer, one short line per render pointing where it looks, labelled with the render's file name.
- **`inputs/renders/`:** JPG or PNG, 2400 px or larger, named `<space>-op01.jpg` / `-op02.jpg`.
  - `palette01-1..3` and `palette02-1..3`
  - `boardroom`, `departmental`, `sprint`, `arena`, `arena-2a-1`, `arena-2a-2`
  - `library`, `garden`, `executive`, `cafe-v1`, `cafe-v2`
  - `coffee`, `mothers`, `zen`, `studio`

  Until then, the walk uses the deck's 2048 px renders.

## Check it

`node tools/walk.js` steps every beat from `file://` and reports console errors, failed requests and anything sitting on the logos. It needs `NODE_PATH=C:/Users/Ritika/Mitigata/node_modules` for puppeteer-core.
- `--slide s-loop` screenshots each beat of one slide.
- `--size 1366x768` checks a laptop screen.
- `--page slides/s-loop.html` checks a slide opened on its own.
- `--page dist/ACKO-The-Loop.html --single` checks the single file, and also fails on any request for a file outside it.

## Folder map

- `dist/ACKO-The-Loop.html`: the single file to present (generated; not committed)
- `slides/`:
  - `order.txt`: the order
  - `<id>.html`: one page per slide, holding its section, style and script
  - `_template.html`: a new slide
  - `_shell.html`: the deck's chrome
- `assets/`:
  - `js/app.js`: the engine and kit
  - `js/dev.js`: opens a slide on its own
  - `js/shell.js`: the chrome as a string (generated)
  - `css/app.css`: the shared styles
  - `img/`: deck images; a slide's own images go in `img/<id>/`
  - `deck/`: deck pages
  - `fonts/`, `audio/`, `vendor/`: three.js r147
- `data/`: generated by `tools/acko`; don't hand-edit.
- `tools/`:
  - `build.py`: joins the slides, `--only` for a preview, `--single` for the single file
  - `serve.py`, `walk.js`
  - `acko/`: the deck and data pipeline (including the one-off `split_slides.py`)
  - `raster_plan.js`: kept for the DXF step, with `assets/js/plan2d.js` and `axo.js` (not loaded yet)
