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

**Online (Cloudflare):** `python tools/deploy.py` builds `dist/site/` and uploads it as the `acko-the-loop` Worker (static assets; Cloudflare's successor to Pages). Settings: `wrangler.jsonc`.
- `dist/site/` holds `index.html` and only the files it uses. The single file can't go up: Cloudflare takes no file over 25 MiB.
- Once per machine: `npx wrangler@4 login`. `--dry-run` checks the upload without sending it.
- **Magic links:** nothing is served without one (`worker/index.js`). `python tools/links.py new "<who>" [--days N]` makes a link, `list` shows the live ones, `revoke "<who>"` switches one off: whoever opened it is shut out on their next load, within about a minute.
- Locally: `npx wrangler@4 dev --local`, with links from `python tools/links.py new "<who>" --local`. The **site** preview serves `dist/site/` without the gate.

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
- **The axo:** with Hover on, the space under the cursor lights up with its name and area. Drag to pan, scroll to zoom on the cursor, right-drag (or Shift-drag) to turn it (the same on every axo); **Reset view** (or a double-click) goes back to the beat. Without WebGL, it shows the deck's own axo pictures.
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
| new | How we worked | 1 | "We let the site lead, and the concept followed." and its line; then six steps one after another: discover the site → map the possibilities → spot the opportunity → frame the idea → layer the lenses → shape the plan |
| 3 | Workplace aspiration | 1 | Three cues rise in: acoustic excellence, real nature, an honest palette |
| 4 | What defines ACKO | 1 | Five values open like shutters, then turn to their second picture |
| 5 | We respect the journey | 2 | Why insurance (the collage, on white); then, as the deck's one click plays it, the collage gives way to the road, the founder's words and the 2016 → 2025 timeline flying in |
| 6–7 | The challenge at hand | 3 | One slide in two bands, People first: the worry ("Where do I go?" … over their drawings, "Moving offices is easy. Moving people isn't."); the answer comes in below it, the worry staying on; then "One Place. One Experience." |
| 8 | Maybe we've felt this before | 1 | A dotted campus path draws; the six memories come up along it |
| 9 | What if | 1 | The question, in the deck's two fonts |
| 10 | The Möbius | 1 | The deck's own Möbius photo (at 35%); a lavender ribbon draws along Ritika's path, narrow at both ends, then slides on along it and out off the right edge, and the Loop follows without a click |
| 11–12 | The Loop | 2 | The deck's ribbon is drawn straight away from Arrival, the title and words sliding in as it passes, then the people and trees; then the seven stops come up, left to right |
| 13 | Campus strategy | 6 | The live model of the 22.10.26 layout as "a complete evolution of planning and massing" (Ritika, 26 Oct), from the bare shell to the furnished floor, the floor framed exactly where slide 14's axo has it (her note, 26 Oct: "size of axo should be same in both the slides"; both at 95% about the top-right so the copyright line clears them, her pick): How it started (the bare shell as a white model: slab, core band, columns, façade; the entrances); Planning Acko's Neighbourhood (01–06, the café, atriums, terraces; the boundaries from `ACKO_NEI.dxf`, 23 Oct); Configuring the Neighbourhoods (any neighbourhood can take any department, by its occupancy and the proximity it needs: said, not written; each department, name and colour, steps one zone along the floor twice and steps back (the carousel, her pick), then two clicks on names swap them live; the numbers stay with the zones); Looping it all Together (the floor in colour, the partitions rise); The Client's Journey (the blue route on it); The Employee's Journey (the furniture rises: rooms, café, terraces, workstations, plants; the red route, the Loop's seven stops named as it reaches them). Copy at the PPT's boxes, word for word, the title and paragraph moved up off the axo (her note, 26 Oct). A click replays the beat; drag turns; without WebGL, the deck's GIF |
| 14 | What's our challenge | 4 | On the axo of the bare floor (the picture and its overlay at 95% about the top-right, so the copyright line clears it; slide 13's axo matches it), the PPT's three challenges: Homogeneity (a uniform desk grid); Distance, 02 (from a far desk the dashed way to the café draws like a maze, Ritika's pick of six; Distance comes when it ends, in the bottom box, laid out as the PPT's bottom box with "02" first and the icons after it, moved right off the axo, her note); Disorientation, 03 (the dead ends pop, then the "?", and Disorientation comes after it, in the right box, laid out as the PPT's right box with "03" above the title; her note, 26 Oct: "keep disorientation as 3 and distance as 2"); then the PPT's "A campus that connects…" line, under the headline (her note, 26 Oct: "move the text"); the headline, the closing line and Homogeneity aligned with the header (her note). Laid out on the PPT's boxes, its words only |
| 15 | Workstation typologies | 1 | Types 1–4; the seats add to 648, +3 cabins = 651 |
| 20 | The campus palette | 1 | The board builds |
| 24–45 | Visual direction: the walk | 17 | One slide per space, one render each (OP 02), each with its Loop words and the keyplan's camera mark; Reception first, in OP 01 then OP 02 |
| 46, 47, 48, 52 | Value addition | 7 | Engagement points, a lens on the PPT collage over four beats (Feel it, Play it, Share it, then All; chips jump, photos open large); materials, acoustics (NRC 0.70–0.90), wayfinding (Nalanda, Sabha, Takshashila) |
| 53–54, 61 | Layout · Option 02A | 6 | The plan in four layers, a beat each (pills jump between them): **Spaces** (hover a workstation type: its desks light up; counts from the drawing, flagged against the PPT); **Neighbourhoods** (outlines only; a click zooms in with its key plan and occupancy; vastness, dealt with); **Biophilia** in three (the CO₂ heat; the planting softening it, conceptual; views to green from the seats); **Acoustics** (four levels of treatment, sound rings). Tools: Measure, Area (M, A, Esc), zoom, Reset, Hover, Egress, Occupancy (the brief against Option 2A) |
| 55–57 | Blown up X · Y · Z | 3 | The same DXF plan flies into each blow-up (hover a space); the fire compartment line draws on Y; the layout's tool row (Measure, Area, zoom, Reset, Hover, Spaces, Neighbourhoods, Egress) |
| 58–60 | Schematic axonometric | 3 | A live 3D model from the DXF in the PPT's schematic-axo look (floors by zone: dark corridors, pale workhall, cream café, grass terrace, lavender rooms in purple glass on a purple base; the entrance in red); West, Middle, East fly along it, with leaders (a dot at both ends) and a key plan bottom right showing the section (drag to turn, scroll to zoom, Reset view) |
| new | A day in ACKO | 7 | The campus in use through a day, on the SketchUp model (acko2A_model, in its own colours under a soft sun): the Loop's seven stops by the clock (Arrival 09:00, Work, Meeting Rooms, Collab, Café, Board Room, Wellness 17:00), each beat easing to its space, where small dark grey people sit at the layout's chairs, present, huddle, talk and walk the corridors (`tools/acko/wayday_people.py`). Wayfinding hotspots are amber light columns at the spots Ritika marked in the boundary DXF (`tools/acko/wayday_marks.py`); a click opens a spot's pop-up (signage concept to come). Turns all the way round, pans, zooms; Whole floor. Hotspot samples: `index-pins.html` (her pick, 5). |
| — | Thank you | 1 | Buttons to the Appendix and About SKV |

**Appendix:** the site (A1: a vector map of Koramangala that closes in on Regalium and turns 11.5° to line up with the plans), then well-being (49), D&I (50) and ESG (51), shown as the deck's own pages.

**Comparison pages (outside the deck):** `index-engage.html` (five ways to light the slide-46 collage) and `index-engage-groups.html` (grouping variations), self-contained in `engage/`. `index-disorient.html`: six ways (and today's) to show Disorientation, beat 2 of slide 14, on the axo; one-beat slides `slides/s-dis-0` … `s-dis-6` (not in `order.txt`), built with the deck's own `build()`. `index-lost.html`: six variations on the chosen way's route (Lost loop: zig-zag, knot, wrong turns, back and forth, meander, maze), slides `s-lost-1` … `s-lost-6`. Picked: path 6 · Maze, now slide 14's beat 2. `index-configure.html`: six ways to animate slide 13's beat 3, Configuring the Neighbourhoods (swap arcs, which is today's; carousel; split-flap; blank & fill; cards; lift & drop), one-beat slides `slides/s-cfg-1` … `s-cfg-6` (not in `order.txt`), each made from `s-strategy.html` with its own play. Picked: 2 · Carousel, now slide 13's beat 3. `index-challenge.html`: six ways (and today's) to put slide 6's challenge and its solution on one slide, both staying on after the click (two bands, four pairs, before | after, crossed out, question → answer, bridge), two-beat slides `slides/s-chx-0` … `s-chx-6` (not in `order.txt`), each made from `s-challenge.html`. `index-challenge-styles.html`: six more, each a look with its own story (two become one, manifesto, voices, untangled, ledger, into the space), slides `s-chy-1` … `s-chy-6`; the Voices bubbles and the Ledger's middle column are draft lines. `index-challenge-copy.html`: four rewrites of slide 6's narrative in today's layout (tight, question → answer, people first, three-word beats), slides `s-chz-0` … `s-chz-4`; all draft copy. Picked: copy 3 · People first, set on way 1 · Two bands, now slide 6 in three beats (the worry, the answer, One Place. One Experience.). `index-narrative.html`: the deck re-ordered so the concept leads (the brief, a Modern Indian Institution, named up front; ACKO's Möbius planted on the brand slide; a new slide `s-nv-threads`, institution + Möbius = the Loop; strategy after the site and the floor's challenge; the renders in the Loop's order, each marked with its stop), changed slides `s-nv-*` (not in `order.txt`). The renders' Loop marker is a small ring of the seven stops. `index-narrative-words.html`: each new line three ways (A as built, B shorter, C with more Indian cues), slides `s-nw-<line>-<a|b|c>`. Picked: all B (shorter), now in `index-narrative.html`. `index-approach.html`: the whole deck re-ordered, from the six steps on slide 3, How we worked, then by Ritika (6 Nov): the concept first (frame the idea: the Möbius, the Loop); discover the site: the site, then `s-pitch`, the bare floor (core and shell, `ACKO_FLOOR`) on football pitches, to scale, its top edge on their touchline: two end to end (245 m), then its width beside a pitch's (34 m against 68 m: half a pitch wide); map the possibilities: left empty (aspiration, brand and journey left out); spot the opportunity: the floor's challenge, the people's challenge, then `s-institution` (the brief, a Modern Indian Institution: not a building, a campus; a campus plan draws itself on black), memories, what if; layer the lenses: wayfinding, engagement, palette, material, acoustic; shape the plan: the renders, walkthrough, workstation typologies, then the layout and axo slides last (campus strategy, layout, a day in ACKO). every slide as it is, but labelled by its step: each header names its slide and its step ("05 · Layer the lenses"), and the overview, the sections menu behind the ACKO symbol and the renders' kicker use the six steps; the page sets them with `window.ACKO_SECTIONS`, which `app.js` reads if a page gives it (the deck itself doesn't). Then by Ritika (9 Nov): the people first (the people's challenge, Where both meet, memories, what if), then the building in one run: the site → Layout · Due Diligence (`s-layout-dd`, a one-beat copy of `s-layout`) → the football pitches → the vast-floor axo (`s-challenges`) → the campus strategy axo to the employees' journey (`s-strategy`) → Layout · Spaces on (`s-layout-sp`, the other six beats; the pills jump across the two copies). The bare floor is carried from slide to slide (`window.ACKO_MORPH`, in `s-challenges`' script): a slide's leave() marks where it lay, the next slide's enter() picks it up if it follows that one: from Due Diligence it glides from the plan's plate to the touchline; from the pitches it tilts from plan into the axo (one 2D matrix: plan metres → the desks' axo frame at 95%), then the picture takes over; from the employees' journey the furnished 3D model itself (route and all) turns straight down until it lies on the Spaces plan (`s-strategy`'s `_flatten`: its canvas lent to a host under both pages, the camera eased to θ 0, φ ≈ 0 and the plan's home view; the 3D floor and the plan differ by a translation in mm), then the 2D plan fades in under it and the model fades off. Any other way in (the menu, going back, the live deck, which has no pitch slide) is the usual cross-fade. `s-layout` itself is untouched (the live deck uses it). `index-institution.html`: the Modern Indian Institution slide six ways (0 as built; 1 belonging → campus: 58% of employees in India come back to the office to belong (Cisco, From Mandate to Magnet, Nov 2023), the brief, so a campus; 2 three principles; 3 a line of campuses; 4 a campus on one floor; 5 into the map), slides `s-ins-0` … `s-ins-5`; all draft copy. `index-belonging.html`: option 1 (belonging → campus) six ways (0 as built; 1 58 in 100, a grid of people; 2 why we come in, three bars: collaborate 80%, belong 58%, ideate 53%; 3 the equation, 58% + the brief = a campus; 4 one word, "to belong."; 5 where both meet, the research and the brief with a campus between; and three with less text: 6 three words, belong · institution · campus; 7 the number, then "→ a campus."; 8 the 58 lit dots gather into a ring, a campus), slides `s-bel-0` … `s-bel-8`; `index-belonging-lite.html`: the same, with almost no words, on white (1 a ring fills to 58% then closes, campus; 2 dots gather into a courtyard ring; 3 one word at a time, belong · institution · campus; 4 three icons, people · a portico · a courtyard; 5 the courtyard plan with 58% then campus in it), slides `s-blw-1` … `s-blw-5`; `index-belonging-all.html`: all three rounds on one page (A · Institution 0–5, B · Belonging 0–8, C · Belonging · white 1–5, each chip prefixed with its round in that page only); `index-meet.html`: the picked way, B · 5 · Where both meet (research and brief side by side, a campus where they meet), six more ways (0 as picked; 1 Venn, the overlap fills; 2 converging lines; 3 two half-arcs close into a ring; 4 the equation, card by card; 5 split panels part and a lilac seam opens; 6 the campus plan draws itself beneath, a campus in its courtyard), slides `s-meet-0` … `s-meet-6`. Picked: 5 · Split, then seam, now `slides/s-campus.html` (no chip), in `index-approach.html` in place of `s-institution`, with its colours inverted (lilac panels, black type; the seam is the page's black) and a third beat: the panels open off the page, the black fills it with …maybe, we've felt this before, and the memories come up out of the same black (the chrome turns ink on the lilac via `body.cp-lil`); figures from Cisco, From Mandate to Magnet, Nov 2023.

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
  - `build.py`: joins the slides, `--only` for a preview, `--single` for the single file, `--site` for hosting
  - `deploy.py`: uploads `dist/site/` to Cloudflare; `links.py`: its magic links
  - `serve.py`, `walk.js`
  - `acko/`: the deck and data pipeline (including the one-off `split_slides.py`)
  - `acko/plan_dxf.py` and `acko/plan_raster.js`: the layout plan from the DXF (see above)
  - `raster_plan.js`, with `assets/js/plan2d.js` and `axo.js`: from Mitigata, not loaded

**The big moments (branch `deck/wow`, 9 Nov; `index-approach.html` only, which sets `window.ACKO_WOW`; the live deck reads as before):** `data/loop-path.js` (`window.ACKO_LOOP`, by `tools/acko/loop_path.py`): the employees' route as one path through the seven stops in the Loop's order, its west-to-east sweep, and the route as a graph, in PLAN_DXF mm. 1 · the Möbius becomes the floor: `s-loop-w` (a copy of s-loop) has a third beat, On the floor: the ribbon lies down on the real floor, where the Layout's plan sits, and the seven stops land on their spots. 2 · the sun path: `s-layout-dd` beat 2, Sun path (Ritika: "add sun path in site due diligence itself"; moved there from the pitch slide): the site sun study on the plan, every half hour 07:00–18:30: the day's arc round the floor by the sun's bearing (the grid turned ACKO_SITE.grid from north), the sun on it with its light across the floor, the sunlit patches; Mar · Sep, Jun, Dec on the chips. 3 · the building assembles: `s-strategy` beat 1 (with ACKO_WOW): a clipping plane sweeps the core, columns and façade up west to east, then the entrances drop in. 4 · walk the Loop: `s-walk` (new, after the strategy): from the strategy's last frame (`_snap`) the camera sinks to eye level on the SketchUp model with A day in ACKO's people and walks the Loop, a click a stop (it lifts and flies low on the long legs), then rises straight up over the plan; Layout · Spaces takes over from it (`_flatten`). 5 · 640 people: on Layout · Spaces 640 of the 646 desks fill as dots walk in from the entrances along the route, each in its neighbourhood's colour, the count rising to 640. 5b · each neighbourhood on its own (10 Nov): `s-layout-sp` beats 3–8 (01 Auto … 06 Home) after the Neighbourhoods overview: its plan in the left half (plan.focusZone, the rest veiled, the people on its desks), its axonometric in the right half (the furnished SketchUp model cut to its box by four clipping planes, its purples kept by AxoSkp.focus, A day in ACKO's angle), its panel below (name, seats, area, key plan, occupancy, n of 6); the camera and the cut ease from one to the next; a click on another neighbourhood opens its sheet; the cut is cleared on leaving. The pills map layers to beats by ORDER [1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6] (wow_nbsheet.py). 6 · the Loop closes: `s-thanks-w` (a copy of s-thanks): the floor's Loop folds into the Möbius and closes, then Thank you. Sound: `kit.cue(name)` in app.js, soft synthesised cues (whoosh, chime, swell, tick, close) only with ACKO_WOW; S (shift+s) mutes them. Built from the scratchpad generators (run_wow.sh: gen_floorflow, wow_loop, wow_sundd, wow_build, wow_people, wow_nbsheet, wow_thanks, wow_walk, gen_approach).

**Problem first (branch `deck/wow`, 10 Nov; Ritika picked variation 1 of `narrative-options.html`):** `index-approach.html` now runs cover · team · How we worked (reworded on this page only: "We started with the people, let the site set the terms, and the concept followed.") → 1 the people's problem (the challenge at hand) → 2 what people want (Where both meet, the memories, what if) → 3 the building's problem (site, Layout · Due Diligence and sun path, two pitches, the vast floor) → 4 the idea (the Möbius, the Loop, laid on the floor) → 5 the proof (Campus strategy, walk the Loop, Layout · Spaces on) → 6 the experience (the lenses, the renders, walkthrough, typologies, A day in ACKO) → Thank you. New hand-off: from the Loop on the floor the strategy's model starts straight down on the plan's footprint and rises into its axo (`wow_rise.py`; s-loop-w marks it on leave). `narrative-options.html` holds the four variations, their scoring and the slide-by-slide talk track (`gen_narrative_opts.py`).

**The brand first (branch `claude/new-changes`, 11 Nov, Ritika: "we'll start it with ACKO's Möbius strip"; the whole run positive):** `index-approach.html` is now built from the repo, `python tools/acko/story/gen_story.py .` (it was `gen_approach.py` in a session scratchpad; `wi_words.py` beside it), and runs cover · team → **01 The Loop** (the opening, then the Möbius) → **02 Belonging** (Where both meet: 58% + the brief = a campus; …maybe we've felt this before) → **03 The Site** (site, Layout · Due Diligence and sun, two pitches, the long floor) → **04 The Plan** (the Loop on the floor, the strategy axo rising out of it, walk the Loop, Layout · Spaces on with the neighbourhood sheets) → **05 The Palette** (campus palette, materials) → **06 The Experience** (Acker's engagement points, the renders, walkthrough, A day in ACKO) → Thank you (the Loop folds back into the Möbius). Acoustic, wayfinding and typologies are in the appendix (Appendix · Kit of parts); How we worked, Where it starts and the people's challenge leave the order (files kept). The long floor is now **The Opportunity** (on this page only, `OPP` in the generator; draft words): One long floor. Room for a whole campus. · Identity · Closeness · Clarity, each "from … to …" over the same drawing. The palette, material and engagement keep their hand lines; the acoustic and wayfinding ones went with them to the appendix.
**The opening, three ways (11 Nov):** `index-open.html` (`python tools/acko/story/gen_open.py .`): `s-open-1` Logo unfurls (ACKO's mark, band by band, untwists into the lavender figure of eight, opens round the page, the lines of business land on it, bridges arch between them), `s-open-2` Into the strip (dark: the deck's Möbius photo with Ritika's path from `s-mobius`, the camera leaning in to the twist, the lines of business along the strip, the twist and crossing glowing), `s-open-3` Loop to campus (the mark drawn as a line, one ring from above, the lines of business as buildings round a shared green with a plot left for what's next, bridges and a ring of protection). Each in five clicks: the mark (infinite trust, inclusivity, collaboration) → "it's never us versus you; it's always us with you" → a loop connects and surrounds → many lines of business, one loop, like a campus → where it bridges, it holds. Source: ACKO's 2025 brand identity (Social Samosa, 29 Jan 2025); the lines of business are `s-journey`'s. **Picked (11 Nov): 2 · Into the strip**, now `slides/s-open.html` (the deck opens on it), with one change she asked for: beat 1 starts on ACKO's logo, which grows onto the strip's outline, turns white and dissolves into the white Möbius strip as the photo comes up; then the beats carry on as before. `s-open-2.html` stays for the comparison page. **Then (11 Nov, after "not seamless" twice):** the logo becomes a ribbon. `index-unfold.html` (`python tools/acko/story/gen_unfold.py .`) compares five ways of laying the white strip down as a ribbon out of the logo, the strip being the photo itself, revealed along its own line through a soft mask: 1 Peel round, 2 Both ways, 3 Lavender lead, 4 Untwist from the centre, 5 Ribbon logo. **Ritika's pick: Unfold 1, with the logo itself as a ribbon**, which is option 5. ACKO's mark is drawn as one band (`tools/acko/story/ribbon_unfold.js`) with its tip on the strip's twist. It unwinds: its head runs round the strip, narrow and purple, widening and whitening behind it, clipped to the photo's outline, and the photo comes up behind it. The generator writes it into `slides/s-open.html` and `s-open-2.html` (`PICK`), from the template `tools/acko/story/open_base.html`.

**How we worked → Where it starts → the people (10 Nov):** `slides/s-approach-w.html` (wow_approach.py), this deck's How we worked, one click: "We began with what people need, let the site set the terms, and the concept followed" (from the brief and the research; Ritika: we didn't talk with the people), its six stages in the deck's order (Understand the people · Spot the opportunity · Discover the site · Frame the idea · Shape the plan · Layer the lenses; the section labels and menu follow them, 01–06). Then `slides/s-start.html`, Where it starts, its own slide (Ritika: the bridge made How we worked too cluttered): the six stages larger, the other five step back and Understand · the people stays, then "About 640 Ackers, from two offices, onto one floor. So we began with them." Leaving it, the people's challenge grows its lavender as a circle out of the Understand dot (guarded patch in `s-challenge`, only with ACKO_WOW and only arriving from s-start).

**The people's challenge → Where both meet (10 Nov):** `wow_campus.py`, only with ACKO_WOW. Where both meet opens on one question, "What makes one place feel like home? We looked at two things." (it leaves with the panels on beat 2; the notes say it first). Arriving from the challenge, its lavender stays under both pages while they cross (no black mid-fade), and the two panels start in that lavender with their seam on the challenge's vertical line (44.7%), then glide to the centre and warm to lilac. Any other way in is the normal fade.

**What if, folded into the memories (10 Nov; Ritika picked B of three, then: "the narrative is the gap"; `wow_whatif.py`, `wi_words.py`, `gen_approach.py`'s `fold()`):** `index-approach.html` has no What if slide. The memories close on two more beats over the dimmed campus, written in word by word: 7 · "A campus is where we first felt safe among people." / "Protection is what ACKO promises its customers." (the brand slide that set up Safety & Protection isn't in this order); 8 · "What if the workplace kept that promise to its own people?" / "So we started where it has to happen: one floor in Koramangala." Then the Site. The live deck's memories have no `.mem-wi` and play as before.

**Layout · Due Diligence on the bare shell (10 Nov, Ritika: "furniture and partitions should not be there, only empty bare shell"; `wow_ddshell.py`):** `PlanCanvas.mount()` returns `bare(on, re)`: while on, the plan's drawing keeps only the building's own CAD layers (`A-WALL|A-FLOR|A-DOOR|A-ELEV`, `OB-A-WALL`, `S-COLS|S-STRS`, `RAILING`, `P-SANR`, `OUTLINE`; an entity on layer 0 takes its insert's layer) and no text; vegetation and text blocks are never shell. `plan.planBare(on)` (app.js) switches it and puts `.bare` on `#world-plan`, which hides the fit-out's SVG layers (room fills `.dx-fill`, rooms, teams, furniture cut-outs, neighbourhood fills and numbers). Only `s-layout-dd` turns it on (after its plan is built, so the Site's zoom still lands smoothly) and off on leaving; the full drawing returns at once for whatever draws next, or quietly 0.9 s later. The live deck never calls it. Then drawn as Ritika's core & shell layout (10 Nov, same patch, `ddShell()` in s-layout-dd): the due diligence shapes filled flat in that drawing's colours (lift lobbies #cfcfcf, fire exit stairs #8e8e8e, washrooms #cfe0f6, AHU #b5d1e4; slabs to strengthen green and cross-hatched, `#dd-hatch`), the external glazing a cyan line (`.dd-glaze`: the slab edge from A-FLOR, read against the drawing: the whole façade but the north edge where the cores sit, wrapping the two south voids), the entries red; the cards' swatches match, and a key line adds External glazing and Entry ×2.

**06 · Layer the lenses, re-ordered and tied to the promise (10 Nov, Ritika: "are these slides sitting well, is the narrative right?"; `gen_approach.py` GROUPS and `lenses()`):** Acoustic strategy now follows the Layout's own Acoustics beat directly, then Wayfinding, Acker's engagement points, the Campus palette and Material strategy, which leads into the renders that show those materials built. Each lens carries, in the hand under its header, the line of the challenge's promise it keeps ("So we design a place that already feels like home: Teams together · Easy to find · Room to explore · Same rhythm"): Acoustic "Same rhythm.", Wayfinding "Easy to find.", Engagement "Room to explore.", Palette and Material "A place that already feels like home." (the Layout's neighbourhoods kept "Teams together"). Inserted into index-approach.html only, with their notes; the slide files are the live deck's.

**The design proposal of 3 Nov, in both decks (10 Nov, Ritika: "make sure the contents of these slides are there"; she chose to replace the renders, in both decks; scratchpad `gen_proposal.py`, reading `Copy of 03.11.26 _ ACKO_Design Proposal.pdf` with PyMuPDF):** every render page's picture cut as the page shows it (its clip path) into `assets/img/r3-*.webp`; the walk takes them in the proposal's order and option pairs: Reception (OP 01/02), Reception Coffee Point (new, `s-w-recoffee`, OP 01/02), Outdoor Deck (new, `s-w-deck`), State Room · Boardroom (OP 01/02), Departmental, Quick Sprint, Work Area · Neighbourhood ×2 (OP 01/02 each), Executive Room (OP 01/02), Cafe ×2, The Acker Garden, Coffee Point, Collab (new, `s-w-collab`), Mother's Room, Zen Room, Studio (OP 01/02). The library, not in the proposal, leaves both orders (its slide file stays); the old `r-*` renders stay on disk, unused. The campus palette (page 1: TEXTURED · CONTRAST · WARMTH · REFINED · LAYERED, light wood and accent stone; `pal3-*`) and Material strategy (page 27: stretch fabric, wallpaper, acoustic panel; `mat3-*`) are rebuilt from their pages, each tile as the page crops it, the words where the page sets them. Engagement points, acoustic, well-being, D&I, ESG and wayfinding already matched the proposal. The live deck is now 45 slides, the re-ordered one 46.
