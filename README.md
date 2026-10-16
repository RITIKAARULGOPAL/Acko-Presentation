# Mitigata · Living Network: interactive presentation

SKV's concept journey for the Mitigata office at **Sattva Hallmark, Outer Ring Road, Bellandur, Bengaluru, Level 03**.

It opens on the deck's **cover**, then runs as one continuous, roughly 22-minute journey, not a slide deck: brand and values, the concept, then the site, the plans and the design. **About SKV** (~3 min) is a separate deck: click the **SKV logo** at the bottom right to open it, and the **Mitigata logo** to go back to where you were. A single "world" stays on screen and the camera moves through it:
- the satellite map
- the floor plan
- the 3D digital twin
- the renders

It runs fully offline.

## Open it

Double-click **`index.html`**. Use Chrome or Edge, fullscreen, on the meeting screen.

`index.html` is built from the slide files in `slides/` and is not in git. After a pull, run `python tools/build.py` once to write it (or open the deck through `python tools/serve.py`, which rebuilds it on every page load).

## Present it

| Key | Action |
|---|---|
| `→` `Space` `PageDown` (clicker) | Next beat |
| `←` `PageUp` | Previous beat |
| `N` | Speaker notes, with chapter time vs plan |
| `O` | Index of all chapters, grouped by part: the presentation, the **Appendix**, About SKV |
| SKV logo / Mitigata logo (bottom right, as in the deck) | Switch to About SKV / back to where you were in the presentation (also from the Appendix) |
| `1` / `2` | Option 01 · The Arc / Option 02 · The Network |
| `F` | Fullscreen |
| `B` | Blank screen |
| `E` | Explore mode: plan hover everywhere, the sun's season and time controls |
| `C` | Camera editor, on the SOC model views (see below) |

**Timer:** the speaker notes (`N`) show elapsed vs planned time (about **20 min** for the presentation, counting from the first click; the Appendix and About SKV aren't included). Click the time in the notes to reset it. The top bar carries only the breadcrumb; there's no live clock or timer on screen.

**Every beat works with → alone.** The agenda, the site zoom, the board, the network, the sun, the axo, the SOC lighting and the boardroom's dinner light all run by themselves.

**Three decks: the presentation, the Appendix, About SKV:**
- The arrow keys stay inside the deck you're in: the presentation never runs into the Appendix or About SKV.
- The **Appendix** opens from the Index (O) or the "Appendix →" button on the last page; the Mitigata logo brings you back.
- The underline under a top-bar logo shows which deck is on screen.
- The About SKV card in the Index also has a chip for each beat (Numbers, Clients, Team…) to jump straight to one.

**Interaction:**
- In plans, drag to pan and scroll to zoom. The **＋ / − / Reset** buttons appear bottom-right when the pointer is over the plan. Reset (or a double-click) goes back to the chapter's view.
- **SOC model views** (chapter 09, beats 1–2): right-drag to look, right-drag + `W A S D` to fly (`Q`/`E` down/up, `Shift` faster), `Alt`-drag to orbit, scroll to push in, double-click to return to the frame. `C` opens the camera editor: save a frame for the step, toggle the trees, copy the frames to bake into `VIEWS` in `app.js`.
- In the layer chapters, hover a row in the legend to pick out those spaces on the plan.
- In the twin, drag to orbit and scroll to zoom.
- Click the **keyplan** bottom-right in any render to see the whole plan.
- In "Spaces", click the **↗ pins** on the plan to jump into that space.

## The journey

**Cover** (deck slide 1): the Mitigata wordmark, "A Design & Concept Presentation dated 01.10.2026.", the deck's green ASCII band, the copyright line and the Mitigata | SKV lockup.

**About SKV** (its own deck, opened from the SKV logo; deck slides 3–13)

| Beat | What happens |
|---|---|
| 1 | About SKV: "Let us get to know each other better", over a live ASCII data-field (redrawn from the deck's animated pattern) |
| 2 | 17 years of building workplaces that perform: six counters, the Foundation of Excellence, 13 cities |
| 3 | What sets us apart |
| 4 | Our services: Design & Build |
| 5 | What we stand for: Quality · Sustainability · Safety |
| 6 | Brands who trust us: 54 logos |
| 7 | Our factory |
| 8 | Factory capacity and the four workshops |
| 9 | What we create |
| 10 | SKV leadership and design team |
| 11 | Trusted by global leaders: projects and three testimonials |

The presentation follows the PPT's four sections (**Design concept → Space planning → Visual direction → Value engineering**), each opened by a section starter as on the deck's divider pages, and makes **one argument**:

- **The question:** how do you show intelligence without exposing it? **Answer:** visible, never readable.
- **The Living Network** gives three principles, marked ①②③ wherever a design move answers them: **① Intelligence at the heart · ② Trust in layers · ③ People and ideas flow.**
- **Each point has one home:** the sun and daylight on the floor (05), the SOC inside and out (12), trust in layers and biophilia in the Appendix. The detail lives in the Appendix.
- **One highlight per beat.** Fixed colours: SOC mint · guest amber · team blue · secure green · sun amber · visitor route amber dashed.

Each slide has its own mode; there is no Day/Night switch. **Dark** (the deck's divider green): the section starters · The Living Network (the deck's gradient) · the walk (Arrival → Breakout) · in the Appendix: Agenda · Which story? · the Studio · Employee experience. **White:** everything else, including About SKV. To change one, add or remove `data-mode="dark"` on its `<section>` in `slides/<id>.html`.

| # | Chapter | Mode | Beats | What happens |
|---|---|---|---|---|
| — | Cover | white | 1 | Deck slide 1 |
| — | **Design concept** | dark | 1 | Section starter (deck slide 14): "Turning vision into a concept" |
| 01 | What defines Mitigata | white | 2 | Deck slides 15 → 16: the wordmark, one line and the five value photos; then the question, and tile by tile each value turns into its workplace aspiration (Purpose → Distinctive, Resilience → Intelligent, Trust → Immersive, Access → Human-centric, Future → Adaptive) |
| 02 | Conceptual approach | white | 1 | Deck slide 17: cream page, the planted ring, from data flow ● to people flow ● to ideas flow, and the deck's sentence |
| 03 | The Living Network | dark | 1 | Deck slide 18: the deck's gradient, ADAPTIVE · HUMAN-CENTRIC · FUTURE-READY, the paragraph on the green bar; then ①②③ light one by one |
| — | **Space planning** | dark | 1 | Section starter (deck slide 19): "Making every space count" |
| 04 | The site | white | 2 | Satellite zoom to Sattva Hallmark, Level 03 |
| 05 | The floor | white | 2 | The satellite lands on the plan: the fixed core and the red entrance triangle; then the sun runs across the same floor, with 30% of the floor within 6 m of glass |
| 06 | From brief to plan | white | 1 | The brief as bubbles, with their adjacencies |
| 07 | Layout Option 01 | white | 6 | Layer by layer: bubble zoning → the layout → the teams → ① → ② → ③ |
| 08 | Layout Option 02 | white | 6 | The same, for Option 02 |
| 09 | One model, two options | white | 9 | Both layouts in 3D, moving together; then a day at Mitigata |
| — | **Visual direction** | dark | 1 | Section starter (deck slide 27): "Optimising every element of a space" |
| 10 | Space inspiration | white | 1 | Deck slide 28: the mood board, "instagram-worthy", and the material palette |
| 11 | Arrival | dark | 3 | The walk, one slide per space: the key plan (the camera's dot and view cone) → the render → its pins (labels) and the docked key plan |
| 12 | Inside the SOC | dark | 5 | The key plan → the render → back to the site (the model at dusk) → Option 01: the SOC faces the court → Option 02: the SOC turns to the road |
| 13 | Boardroom | dark | 3 | The key plan → the render → meeting at ten, dinner at eight |
| 14 | Meeting room | dark | 3 | The key plan → the render → its pins |
| 15 | Breakout | dark | 3 | The key plan → the render → its pins |
| — | **Value engineering** | dark | 1 | Section starter: "Spending where it matters most" (SKV's line; the PPT has no divider here) |
| 16 | Materials | white | 1 | Deck slide 36: kit of parts by flooring, ceiling, furnishing, wall finishes |
| 17 | Acoustics | white | 1 | Deck slide 37: NRC 0.70–0.90 and the six treatments |
| 18 | Brand experience | white | 1 | Deck slide 38: graphics · people & wellbeing · way-finding |
| — | Thank you | white | 1 | Deck slide 39 |

**57 clicks, ≈26 min.** Chapters 04–09 are being reworked on another branch (12.10) and come in with its merge.

**Appendix** (its own deck): the agenda · the question (value → design move → aspiration board) · trust in layers (Mitigata's mark) · which story? · the studio (On Air) · green zones · the method (5 beats) · space types and areas · teams and seats · the full scorecard · event capacity 50 / 100 / 200 · SOC operational zoning · the next 5–7 years (hard and soft zones) · light, sound and technology · room mix and the studio · what the building decided (due diligence, colour-coded) · employee experience.

**Value → aspiration → design move** (SKV's proposed pairing; edit in the `s-values` section of `index.html`):

| Value | Aspiration | Becomes, in the design |
|---|---|---|
| Purpose | Distinctive | One clear focal point: the SOC at the heart of the floor |
| Resilience | Intelligent | Layers of access: open, guest, team, secure |
| Trust | Immersive | Transparency with confidentiality: visible, never readable |
| Access | Human-centric | A welcoming arrival; guests never cross the work floor |
| Future | Adaptive | Build the hard zones once; keep the rest free to change |

**The earlier layer-by-layer chapters** now live in the Appendix. Teams are named only once the layout exists, and there are no "neighbourhoods": everything is teams.

**Green zones, the method** (from our Acko analysis; numbers in `GZ_DEF` / `GZ_G` in `app.js`):
- **Spaces:** the CAD rooms and team zones. Seats come from the drawing (team seats, room PAX, boardroom 30). The agile workstations (Opt 01 "Agile / Open Discussion" and "Hotdesk", Opt 02 "Collaboration area") count as work at one seat per 2.5 m² (est.).
- **Use:** footfall = occupancy × visits × use; person-hours = footfall × dwell; carbon index = footfall × dwell × activity × services (a relative design index, not a carbon calculation).
- **Priority:** footfall 25 · dwell 25 · carbon index 20 · daylight 15 · social 10 · visibility 5, each half intensity (per m²) and half volume, square-root compressed. The class (very low → very high) sets the plants: one per 12.5 m², ×0.5 to ×1.4.
- **Placement:** free floor only: clear of the glass (0.9 m), walls (0.6 m), desks and chairs (0.9 m), the corridor's walking line (1.2 m either side), the core, support and enclosed rooms (which get table plants instead). Zones sit 6 m apart within a space and 3 m apart across spaces. Types: feature, node, island, edge, threshold, pocket.
- **Score /100:** 40% priority spaces served, 30% desks with green within 8 m, 15% zones in view, 15% plants in daylight.

**Employee experience, where each brief item is** (worked out from the drawing in `exMap()` in `app.js`):

| Brief §10 | On the plan |
|---|---|
| Comfortable touchdown | The agile workstations, plus the team hot desks (13 in Opt 01, 18 in Opt 02) |
| Informal collaboration | The drawn discussion tables |
| Lounges | Opt 02's Lounge (Opt 01: none; its waiting lounge is for visitors) |
| Breakout | Breakout Area rooms, plus Opt 01's breakout in the corridor |
| Quiet / focus | Phone booths, plus Opt 01's nap room and library |
| Café / pantry | The café, 52 covers |
| Social | The café, breakout and lounge together |
| Small spontaneous meetings | Opt 02's 2-person rooms (Opt 01: none) |
| Biophilic elements | The green zones from the Appendix (A1) |

Chapter numbers in the kickers are set automatically from the order (A1, A2 … in the Appendix), so moving a section renumbers everything.


## The look: SKV's presentation

Everything follows the 01.10.2026 deck (`01.10.2026_MITIGATA_DESIGN PROPOSAL.pptx`). New pages should too.
- **Pages:** white (`#FFFFFF`), or the deck's divider green `#0E2A1F` on the slides marked `data-mode="dark"`.
- **Colour:** deck green `#04DB7F`, only on key words and the one highlight. Text `#0D0D0D`, page header `#434343`, subtitles `#666666`, rules `#D9D9D9`.
- **Zoning palette** (deck slides 21–24), used for every plan and the 3D model: SOC `#B5F4D9` · arrival `#FCE7AE` · meet `#C9D3E0` · workhall `#E4ABA5` · collaborate `#E9C8FF` · boardroom `#A0BBEB` · café `#F2C596` · core `#919191`. Main entrance: the red triangle `#CC0000`. Sun: deck yellow `#FBBC04`.
- **Fonts** (all in `assets/fonts/`, OFL): **Poppins** for titles and labels (with Light Italic and ExtraLight), **Figtree** for body text, **Lexend** for the big numerals. No monospace.
- **Layout:** flat and square: no cards, shadows or blur. Each page starts with the deck's header (chapter · section, Poppins SemiBold grey). Hero titles carry the deck's green bar on the left. The ASCII field is the deck's pattern. The footer line is the deck's copyright.
- **Deck pages rebuilt in the presentation:** slides 17 (Living Network), 28 (space inspiration), 34 (the SOC as hero space), 36 (kit of parts), 37 (acoustics), 38 (brand experience).

## Edit the words

All copy is in **`slides/`**: one file per slide, `slides/<id>.html`, holding that slide's `<section>`.
- **Order:** `slides/order.txt` lists the slide ids in order; move a line to move a slide, leave it out to hide it. A slide's chapter is its `data-part`, so change that too when moving a slide to another chapter.
- **The page around the slides** (the world layers, the logos, the scripts) is `slides/_shell.html`.
- **See an edit:** with `python tools/serve.py` running, save and refresh. Otherwise run `python tools/build.py`.
- Speaker notes are in `data-notes`.
- Planned minutes are in `data-mins`.

The About SKV copy is in the `s-skv` section. Its logo names and the ASCII field live in `assets/js/app.js` (`LOGOS`, `ASCII`).

Generated text lives in **`assets/js/app.js`**:
- `DD`: the due-diligence legend (Appendix)
- `STORY`, `compare()`: the two layouts told through ①②③, and the six differences
- `GZ_DEF`, `GZ_G`, `GZ_TYPES`: green-zone assumptions, weights and zone types
- `EX_C`, `exMap()`: the employee-experience layer
- `VIEWS`: the SOC model views (camera frames and copy)
- `STOPS`: the day's three stops
- `MOMENTS`: the three renders in Moments
- `scorecard()`

## Where the numbers and images come from

- **The layouts are the 09.10.2026 test fits** (`Testfit OP1 - 09.10.26.dxf`, `Test Fit op2 09.10.2026.dxf`). They arrive as `data/src/plan-hover-data.js` and are imported by `tools/import_plan_hover.py`:
  - walls, glass, doors and furniture
  - the CAD team's `MI_*` room outlines, which are the zones, the hover rooms and their m²
  - the team zones with seats and PAX: SOC 80 / 78 (of 80), Delivery 71 / 70, Product 50 / 57, Sales 41 / 41, Sales Calling 37 / 31, HR & Finance 20 / 22
  - room counts, from the room labels: Opt 01 has 17 meeting rooms and 9 booths; Opt 02 has 15 meeting rooms and 6 booths
- **Building shell, columns and floor outline:** from the original test-fit DXFs. They're the same building, and the 09.10 drawings line up with them to within 1 mm. The floor plate is ≈1,730 m² and ≈65 m from prow to north façade.
- **Hover:** in Teams, Two layouts, Spaces, Future, the keyplan peek and Explore mode (E), hover a room for its name and m², or a desk for its team. The label sits beside the item, never on it, and plan labels under the hovered item step aside.
- **Everything placed on the plan comes from the 09.10 drawings** (`tools/derive_layout.py`, run by the importer); nothing is hand-placed:
  - **circulation:** the centreline of the floor left between the zones and desks (the line the corridor follows)
  - **routes:** shortest paths over the free floor, preferring the circulation: visitor (front door → boardroom), Opt 02 tour (front door → SOC glass), service (prep or dine store → boardroom)
  - **events:** 50 = the café, staged at its dropdown screen; 100 = the largest team zone on the SOC; 200 = the team zones around it until ≥ 200 m², staged at the SOC glass
  - **SOC glass, signature spots, render viewpoints, the operable wall and the twin's lobby** from the matching CAD rooms
- **Site and orientation:** Ritika marked the site on Google Maps. `tools/site_register.py` matches that screenshot to our satellite still and fits the floor outline to the east wing's roof, which gives `data/site.json`. The fit shows:
  - **North → right**, with the drawing 1.8° off true north.
  - **The atrium** is the glass-roofed court west of the floor, between the two wings.
  - **The entry** is the campus gate off the ORR service road, to the south-east.
- **The SOC concept model** (`assets/js/site.js`, `data/site-data.js`): Sattva Hallmark and its street in the twin — the two blocks traced from the satellite, the court under its space frame, the forecourt, the metro viaduct and the trees, with OpenStreetMap context. The SOC halo sits in each option's SOC zone from today's layout. The model puts Mitigata on the 2nd floor of a G+3 (from SKV's photomontage); the copy says Level 03.
- **Satellite and Street View stills** (`assets/site/`, including the close `site_z20` still under the plan): Imagery ©2026 Google, Airbus, Maxar Technologies. Credited on screen.
- **Atrium night view:** SKV's photomontage from the deck.
- **The "Commons" and "On Air" moments:** use deck mood images, not renders.

## Updating

When the layouts change, rebuild `plan-hover-data.js` from the new DXFs with the CAD pipeline in `tools/plan_hover/` (see its `INTEGRATION.md`). Then:

```bash
python tools/rebuild.py --hover data/src/plan-hover-data.js --deck "01.10.2026_MITIGATA_DESIGN PROPOSAL.pptx"
```

`tools/raster_plan.js` renders the furniture textures in headless Chrome. It needs `npm i puppeteer-core`.

After a layout change, refresh the SOC glazing in the site model with `python tools/build_site.py --soc-only`. The full site build needs `site-context/axo/axo_data.js`, which lives outside this repo. `python tools/serve.py` serves the folder without caching; `tools/site-dev.html` is the model on its own.

To re-place the floor on the satellite from a new marked screenshot, add `--site-mark "<screenshot.svg>" --under "<site_z20.png>"`.

The About SKV images (logos, headshots, photos, icons) are cut from the deck by `tools/extract_skv.py`, which `rebuild.py` also runs:

```bash
python tools/extract_skv.py "01.10.2026_MITIGATA_DESIGN PROPOSAL.pptx"
```

To refresh the site imagery:
- **Street View:** `python tools/capture_site.py`
- **Satellite:** `node tools/capture_sat.js <dir>`. Needs `npm i puppeteer-core`. Then run `capture_site.py --sat <dir>`.

## Folder map

- `slides/`: one file per chapter overlay, `order.txt` (their order) and `_shell.html` (the world layers and everything around the slides)
- `index.html`: built from `slides/` by `tools/build.py`; not in git
- `assets/css/app.css`: light and dark theme tokens, world, chapters
- `assets/js/`:
  - `app.js`: world manager, map zoom, photo zoom-through, chapters, timer
  - `plan2d.js`: SVG plan: layers, hover, overlays and the ＋ / − / Reset canvas controls
  - `twin.js`: three.js digital twin, with themes and the free (Unreal-style) camera
  - `site.js`: the site model (TwinSite): the street, Hallmark, the court, the viaduct, the trees, the façade shader
- `assets/site/`: satellite zoom stack and Street View stills
- `assets/img/`: deck renders, photos, sketches, materials, logos
- `assets/img/skv/`: About SKV images cut from deck slides 3–13
- `assets/vendor/three.min.js`: three.js r147 (MIT)
- `assets/fonts/`: Poppins and IBM Plex Mono (OFL)
- `data/`: geometry generated from the layouts; don't hand-edit it. The source layouts are in `data/src/`, and the site registration is in `site.json`.
- `tools/`: the pipeline
  - `import_plan_hover.py`, `raster_plan.js`: the 09.10 layouts, imported into the presentation's frame
  - `derive_layout.py`: circulation, routes, events, stage points and spots, derived from the 09.10 CAD
  - `build_site.py`: the site model data (`data/site-data.js`); `--soc-only` refreshes the SOC glazing
  - `serve.py`, `site-dev.html`: a no-cache dev server and a model-only harness
  - `plan_hover/`: the CAD pipeline that builds `plan-hover-data.js` from the DXFs
  - `site_register.py`: places the floor on the satellite from the marked screenshot
  - `dxf_to_json.py`
  - `author_zones.py`
  - `zones_from_mx.py`
  - `build_assets.py`
  - `extract_skv.py`
  - `capture_site.py`
  - `capture_sat.js`
  - `rebuild.py`
