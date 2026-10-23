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
- **Layout and blow-ups** (the DXF plan):
  - On the layout the plan takes the page: the whole floor, centred. **The beat's key** (Legend, Six neighbourhoods, Fire egress key) is a tab at the bottom left: click it to open it beneath the plan, which moves up; click again to tuck it away. Every beat starts with it tucked away.
  - Scroll to zoom on the cursor, drag to pan, and double-click to go back to the beat's view.
  - Hover a space for its name and area. On *Six neighbourhoods*, hover a neighbourhood, or its row, to pick it out with its seats.
  - On *Six neighbourhoods* (or any layout beat with Neighbourhoods on), **click a neighbourhood** (on the plan, or its row): it fills the page, with a bar along the bottom (its key plan, workstations, area). **Occupancy chart** opens its chart on the right (workstations and the rooms inside it); **Hide chart** tucks it away. Hover its rooms; click another to switch; **All neighbourhoods**, a click on the same one, or Esc goes back.
  - **The plan** is the DXF's plain linework, as the toolkit's viewer draws it.
  - **The tools** (top right, on the layout and the blow-ups, any beat):
    - **Spaces** shows the spaces in their legend colours (opening the layout's Legend does too).
    - **Neighbourhoods** switches the six on or off. On the layout, when they show, a click on one opens it; on the blow-ups, outlines and seat hover only.
    - **Fire egress** switches the exit-path layer on or off.
    - **Hover** switches the names on hover on or off. It's one setting for the layout, the blow-ups and the axo, and it stays as set (as in Mitigata). A neighbourhood still opens on a click with Hover off.
    - **Reset zoom** flies back to the beat's view, or to the open neighbourhood's.
  - **Occupancy** (bottom left, beside the Legend tab) opens the floor's occupancy chart beneath the plan, the plan moving up. It shows the brief against Option 2A (deck slide 61, which is no longer a slide of its own: its table lives in the layout slide) in Mitigata's chart look: hairlines, the zones in small purple capitals, a mark before each count (✓ meets, ▲ above, + not asked, ▼ short) and a summary line. ⤢ opens it centred and larger; ✕, Esc or a click outside closes it. Each neighbourhood's chart has the same look.
- **The axo:** with Hover on, the space under the cursor lights up with its name and area. Drag to turn it, scroll to zoom on the cursor, right-drag (or Shift-drag) to pan; **Reset view** (or a double-click) goes back to the beat. Without WebGL, it shows the deck's own axo pictures.
- **The walk:** music on or off, pan mode (drag the render), and keyplan on or off.

## The journey (≈ 20 min, 66 beats)

The PPT's own order. Ritika's choices (16 Oct):
- one palette, the campus palette (palette 01 removed on 22 Oct)
- each space shows one render (OP 02); Reception alone shows OP 01, then OP 02
- the site sits in the Appendix, first (22 Oct); the floor's sun and fire beats were removed the same day

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
| 10 | The Möbius | 1 | The deck's own Möbius photo (at 35%); a lavender ribbon draws along Ritika's path, narrow at both ends, then slides on along it and out off the right edge, and the Loop follows without a click |
| 11–12 | The Loop | 2 | The deck's ribbon is drawn straight away from Arrival, the title and words sliding in as it passes, then the people and trees; then the seven stops come up, left to right |
| 13 | Campus strategy | 5 | The live model of the 22.10.26 layout, built up in the 3D renders' layers and the deck's five captions: How it started (the white model, the entrances); Planning Acko's Neighbourhood (01–06, the café, atriums, terraces; the boundaries from `ACKO_NEI.dxf`, 23 Oct); Looping it all together (the floor in colour, then rooms, café, terraces, workstations, plants, façade); The Employee's Journey (the red route, the Loop's seven stops named as it reaches them); The Client's Journey (the blue route). Copy at the PPT's boxes, word for word. A click replays the beat; drag turns; without WebGL, the deck's GIF |
| 14 | What's our challenge | 4 | On the axo of the bare floor, the PPT's three challenges: Homogeneity (a uniform desk grid), Disorientation (a dashed maze route drawn on, Ritika's pick of six), Distance (the long walk to lunch); then the PPT's "A campus that connects…" line. Laid out on the PPT's boxes, its words only |
| 15 | Workstation typologies | 1 | Types 1–4; the seats add to 648, +3 cabins = 651 |
| 20 | The campus palette | 1 | The board builds |
| 24–45 | Visual direction: the walk | 17 | One slide per space, one render each (OP 02), each with its Loop words and the keyplan's camera mark; Reception first, in OP 01 then OP 02 |
| 46, 47, 48, 52 | Value addition | 7 | Engagement points, a lens on the PPT collage over four beats (Feel it, Play it, Share it, then All; chips jump, photos open large); materials, acoustics (NRC 0.70–0.90), wayfinding (Nalanda, Sabha, Takshashila) |
| 53–54, 61 | Layout · Option 02A | 6 | The plan in four layers, a beat each (pills jump between them): **Spaces** (hover a workstation type: its desks light up; counts from the drawing, flagged against the PPT); **Neighbourhoods** (outlines only; a click zooms in with its key plan and occupancy; vastness, dealt with); **Biophilia** in three (the CO₂ heat; the planting softening it, conceptual; views to green from the seats); **Acoustics** (four levels of treatment, sound rings). Tools: Measure, Area (M, A, Esc), zoom, Reset, Hover, Egress, Occupancy (the brief against Option 2A) |
| 55–57 | Blown up X · Y · Z | 3 | The same DXF plan flies into each blow-up (hover a space); the fire compartment line draws on Y; the layout's tool row (Measure, Area, zoom, Reset, Hover, Spaces, Neighbourhoods, Egress) |
| 58–60 | Schematic axonometric | 3 | A live 3D model from the DXF in the PPT's schematic-axo look (floors by zone: dark corridors, pale workhall, cream café, grass terrace, lavender rooms in purple glass on a purple base; the entrance in red); West, Middle, East fly along it, with leaders (a dot at both ends) and a key plan bottom right showing the section (drag to turn, scroll to zoom, Reset view) |
| new | A day for a new Acker | 9 | Wayfinding on the live axo: a figure walks the day's route along the corridors, a stop a click (arrival, reception, their neighbourhood, the desk, first meeting, lunch, coffee, a pause, home time); at each marked spot a signage card opens (placeholders for Ritika's concept sketches); Whole floor shows the route; the strip along the bottom jumps to a stop |
| — | Thank you | 1 | Buttons to the Appendix and About SKV |

**Appendix:** the site (A1: a vector map of Koramangala that closes in on Regalium and turns 11.5° to line up with the plans), then well-being (49), D&I (50) and ESG (51), shown as the deck's own pages.

**Comparison pages (outside the deck):** `index-engage.html` (five ways to light the slide-46 collage) and `index-engage-groups.html` (grouping variations), self-contained in `engage/`. `index-disorient.html`: six ways (and today's) to show Disorientation, beat 2 of slide 14, on the axo; one-beat slides `slides/s-dis-0` … `s-dis-6` (not in `order.txt`), built with the deck's own `build()`. `index-lost.html`: six variations on the chosen way's route (Lost loop: zig-zag, knot, wrong turns, back and forth, meander, maze), slides `s-lost-1` … `s-lost-6`. Picked: path 6 · Maze, now slide 14's beat 2.

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
- **The layout and blow-ups: the DXF** (`Downloads/ACKO_Testfit_21.10.26 (3).dxf`, the 21.10.26 test fit; the toolkit plan `tf2110`), in three steps:
  1. **The DXF plan toolkit** (`Downloads/dxf-plan-toolkit-v1.0/dxf-plan-toolkit`, its `projects/acko.json`): `python tools/build.py --config projects/acko.json --only tf2110` (about 30 min).
     - **Conversion:** the drawing at 0.49 mm median accuracy (0.81 mm worst), with every text as the outlines of its own glyphs (its style's font, width factor and MTEXT formatting), so labels keep their CAD size.
     - **Neighbourhoods:** `ak_zone_*`, with seats from the drawing's workstation counts: 140 / 137 / 65 / 82 / 104 / 123 = 651.
     - **Not in contract:** `ak_zone_Nic`, the hotel band.
     - **Output:** `viewer/out/tf2110/`. Check it in its viewer.
  2. **`tools/acko/plan_dxf.py "<toolkit>/viewer/out/tf2110" "<the .dxf>"`** (needs `NODE_PATH` for puppeteer):
     - **Pictures:** the plan at 12 / 24 / 48 px per m (`assets/img/plan-dxf-*.webp`, rendered by `plan_raster.js`).
     - **Spaces from the drawing:** each room label (the toolkit's `labels.json`) takes the room its walls enclose (`tools/acko/faces.py`):
       - **Lines used:** walls, glass, the shell, planters and the façade's rails; folding and sliding doors as walls; each swing door shut along its closed position, so its swing area belongs to its room. Tables and desks are never used. The floor plate's outline is the outside wall. Small breaks are bridged at 45 / 120 / 160 mm, and doorways drawn without a door at 0.5 m.
       - **Size limits:** per room type there's a minimum, raised to 0.9 m² per PAX in the label (so a table under the label is never taken for the room), and a maximum (so a room that leaks through a gap is caught).
       - **Result:** 137 spaces. 131 come from the new walls; 4 keep the previous build's outline (only where it holds the label and at least half of it lies on the new walls; open-plan areas trimmed to their open floor); 2 are not in contract. One label (a second "Rain coat" tag in the corridor) gets no outline of its own.
     - **Colours:** the deck's legend (slide 53), plus colours for the rooms it predates (medical, nap, mail and store, not in contract).
     - **The rest:** the neighbourhoods (with boxes and occupancy rows), the fire egress (`ak_Ep_*`), and the deck's marks (blow-up boxes, fire line, entrances, arrival zones). The new drawing shares the old one's frame, so the marks map unchanged.
     - **Output:** all into `data/plan-dxf.js`.
  3. **The component** is the toolkit's `component/assets/js/plan-hover.js` and `.css`, copied into `assets/`. The engine mounts it once in the world (`plan` in the kit).
- **Sharp when zoomed in:** `python tools/acko/plan_vec.py "<toolkit>/viewer/out/tf2110"` writes `data/plan-vec.js` (13.5 MB): the toolkit's `full.svg` as 81 vector tiles of 12 m, in relative coordinates and the drawing's paint order. Past 16 device px per metre (a neighbourhood, a blow-up, a wheel-zoom), the deck draws the tiles in view exactly as the toolkit's viewer does (non-scaling lines, its colours) in place of the picture. The picture still carries the whole floor and the flights, and drags and wheel-zooms when more than 20 tiles are in view.
- **The axo's model:** `python tools/acko/axo_dxf.py "<toolkit>/viewer/out/tf2110"` writes `data/axo-dxf.js` (and a check picture, `tools/_work/axo/check.png`) from the toolkit's classed `instanced.svg` and `rooms.json`, and the deck's `data/plan-dxf.js`. It never reads the DXF itself. The slab is the floor ACKO occupies, and the solid walls exclude the legend rooms' partitions, which the axo shows as purple glass. Furniture comes from each closed outline's size: chairs, desks and tables, storage. A pod's desk tops are its `base` lines, closed across the breaks its chairs leave. Plants are the `green` blocks.
- **The campus strategy's layered axo (slide 13):** `python tools/acko/axo_layers.py "<layout>.dxf" --renders "<axo_update folder>"` writes `data/axo-layers.js` (and check pictures in `tools/_work/axo-layers/`) straight from the layout DXF (`ACKO_BOUNDARY_HATCH_ALL_22_10_26.dxf`), read by `tools/acko/dxf_read.py` (no ezdxf, about 7 s). The DXF's placed blocks are found by what they hold: the neighbourhoods (`AC_AUTO` … `AC_HOME`, `AC_ATRIUM`, `AC_TERRACE`), one outline per space (`AC_<TYPE>`, `AC_GLAZING` the façade, `AC_ENTRY`), `AC_OUT_OF_SCOPE` (the grey band), the layout (furniture, `S-COLS` columns) and the plants. The renders (`acko2A_model*.png`) give the two routes: their red and blue dashes, traced and mapped back to the plan through the floor's affine (fitted to render 01's silhouette, the renders' camera: 45°, 48° up). Without `--renders` the last routes are kept. `--zones "<ACKO_NEI.dxf>"` takes the neighbourhoods, atriums, terraces and the café's zone from Ritika's neighbourhood drawing instead: its zone block has the layout's block frame, so it is placed by the layout's own zone insert (the two drawings were moved apart in CAD). Loaded by `assets/js/axo-layers.js` (`window.AxoLayers`), which shares AxoModel's renderer and camera.
- **The old deck plan:** `tools/acko/deck_plan.py` made `plan-full.webp` and `data/deck-plan.js` from the deck's plan tiles. They're no longer loaded; `plan_dxf.py` still reads the marks from `deck-plan.js`.
- **The site and the bare floor:** from the earlier Acko analysis (Acko New 01: test fit 03, the same shell). `tools/acko/site_floor.py` writes `data/site-floor.js`.
  - map: Overture/OSM
  - sun: NOAA formulas
  - exit paths: measured on the drawing (to be confirmed against NBC with the fire consultant)
- **The walk's keyplans:** each render slide's keyplan crop and maroon camera mark, read from the deck, in `data/keyplans.js`.
- **Pages still shown as deck images:** `assets/deck/s49–51.webp` (Appendix).

## What to drop in next (`inputs/`, not committed)

- **A new DXF of the layout:** re-run the toolkit and `plan_dxf.py` (see above). Optional for later: an `AC_CAM` layer (one short line per render pointing where it looks, labelled with the render's file name) for true camera positions in the walk.
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
  - `acko/plan_dxf.py` and `acko/plan_raster.js`: the layout plan from the DXF (see above)
  - `raster_plan.js`, with `assets/js/plan2d.js` and `axo.js`: from Mitigata, not loaded
