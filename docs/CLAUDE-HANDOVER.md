# Handover: Acko neighbourhood-office presentation

This file is for a new Claude session continuing the work. Read it fully before you change anything.

- **Repo:** `RITIKAARULGOPAL/Acko-Presentation`
- **Branch:** work on `main`. `claude/eager-wozniak-85qbdv` holds the same history up to the site analysis and renders.
- **Client:** Acko. **Designer:** Officebanao (the user, Ritika).
- **What we're building:** an interactive presentation of the "neighbourhood office" concept for Acko's floor at Regalium, Koramangala, Bengaluru.

---

## 1. Ground rules the user has set (keep to these)

- **Single-file HTML decks.** Inline CSS and JS, renders embedded as base64, no server. The user opens them straight from Downloads in Chrome.
- **Plain, concise English in captions.** Numbers are computed from the drawing, never typed in.
- **Naming:**
  - Neighbourhoods are **Neighbourhood 01–06**; no place names like Indiranagar.
  - "Town Square" is now **Shared spaces**.
  - The former "atria" are **terraces**.
- **Renders:** a light and a dark image per space type. The viewer is full-bleed, with frosted-glass controls on top and no bottom carousel or slider.
- **Git:** commit with clear messages and push. The user is also building a slide on another branch; that gets merged into `main` later (see section 7).
- **Before pushing**, send the user a preview, i.e. the HTML file.

---

## 2. Files

| Path | What it is |
|---|---|
| `index-testfit.html` | **The current deck** (28 steps, about 2.2 MB). **Generated; never edit it by hand.** Rebuild it with the pipeline. |
| `index.html` | The original sample-data deck. It is also the **engine template** that the test-fit build splices into. |
| `index-v1.html` | An earlier sample version, kept for reference. |
| `tools/testfit/` | The pipeline that turns the test-fit DXF into `index-testfit.html` (section 3). |
| `tools/site/` | Site analysis data: map, wind, climate, due-diligence facts (section 4). |
| `renders/` | Real renders, named `<key>-light.<ext>` / `<key>-dark.<ext>`, or `n03-<key>-…` for one neighbourhood. Currently `reception-*` and `garden-*` (webp). The build embeds them. |
| `docs/` | `Acko-Handover-Spec.pdf`, `Acko-Junior-Guide.pdf` (v1.1, old naming), `Acko-Deliverables.pdf` (naming rules and deliverables list), plus their HTML sources. |
| `README.md`, `tools/testfit/README.md`, `tools/site/README.md` | Documentation, kept up to date. |

---

## 3. The test-fit pipeline (`tools/testfit/run.sh <path/to/layout.dxf>`)

The DXF is **not in the repo** (it is git-ignored and 160 MB). The latest one is `acko-layout-tf03.dxf`; ask the user for it. The pipeline needs `pip install ezdxf shapely`, Python 3, and Playwright/Chromium for the tests. A run takes about 8–10 minutes. It works in a temporary directory, or `WORK=<dir>` if set.

The steps run in this order:
1. `dxf_flat.py` writes `dxf_mid.json`: every layer's paths and texts in the layout panel (y −418000 to −368000 mm).
2. `dxf_blocks.py` writes `dxf_pos.json`: block inserts with positions. That covers desks, microwaves and, from the `base` block, lift shafts and lift doors.
3. `ac_panels.py` writes `zones.json` from `AC_NEIGH` (top panel, offset −53268) and `AC_FIRE_EXIT` (bottom panel, offset +55301). If the drawing has no `AC_NEIGH` layer, it falls back to `dxf_blk.py` + `panels.py`, which read the old `thh`/`gj` panel blocks.
4. `extract.py` (with `geo.py`) writes `realfit.json`, everything the deck draws. Units: 1 unit = 50 mm, `T(x,y)=((x+177000)/50, (−373500−y)/50)`.
   - **Plate:** from `AC_GLAZING`; otherwise the hand-drawn `PLATE` in `geo.py`.
   - **Terraces:** the plate's notches on the south side.
   - **Zones:** `NB_ORDER=[3,7,6,2,1,0]` gives N01–N06, west to east; zones 5 and 6 are receptions R1 and R2.
   - **Café and lobby:** `TW` comes from `AC_CAFETERIA` and `TC` from the east `AC_LIFT_LOBBY`.
   - **Desks**, by block: `rytu`=3, `WS 1500x750mm`(+` 2`)=1, `rhrt`=1, `4PAX WITH PLANTER`=4, for **651 seats** in total.
   - **Rooms:** from the `AC_` layers (table below), each with its exact outline; name and seats come from the `OB-I-ANNO-TEXT` label inside.
   - **Coffee corners:** from `AC_COFFEE_CORNER`.
   - **Also extracted:** stairs, columns, lifts, fire routes, daylight %, `spaces` (the space plan) and `dd` (due diligence).
5. `tools/site/site.py build realfit.json site.json`:
   - fits the plate into Regalium's footprint;
   - works out north (11.5° east of north; the slanted west end lines up with Hosur Road);
   - computes the sun path and the façade sun hours;
   - traces sun patches on the layout for 3 dates × 24 half-hours;
   - computes the sun per area;
   - merges `tools/site/context.json` and `facts.json`.
6. `build_tf.py <index.html> <index-testfit.html>` splices the engine from `index.html` with:
   - `tf_css.css`, `tf_data.js` (+ `realfit.json`) and `tf_site.js` (+ `site.json`);
   - `tf_plan.js`, `tf_steps.js` (the steps and captions) and `tf_tips.js`;
   - the render config (SPACE_NAMES, SCENE_OF, plus the embedded `renders/`);
   - engine edits made with `rep()`, which asserts exact matches.

**Determinism:** a second run of the pipeline must give a byte-identical `index-testfit.html`. Always check with md5sum.

### AC_ layers in acko-layout-tf03.dxf → meaning
| Layer | Used as |
|---|---|
| `AC_GLAZING` | Floor plate (7,606 m², 245 × 34 m). The terraces are its two notches, about 12 m wide each. |
| `AC_NEIGH`, `AC_FIRE_EXIT` | 8 zones and 8 egress routes, in the top and bottom panels. |
| `AC_WS_TYPE01..04` (inside block `AFAFAF`) | Workstations: 74 + 13 singles, 12 four-seat planter tables, 172 three-seat benches. |
| `AC_QUICK_SPIRIT` (37, which includes the 2-pax rooms), `AC_COLLAB_HUDDLE` 13, `AC_DEPARTMENTAL_ROOMS` 6, `AC_BOARD_ROOM`, `AC_THE_HATCHERY`, `AC_VISITOR_HUB` 5, `AC_TRAINING_ROOM`, `AC_THE_STUDIO_ROOM`, `AC_EXECUTIVE_CORNER_CABIN` 3, `AC_PHONE_BOOTH` 42, `AC_ZEN_ROOM` 5, `AC_PRAYER_ROOM`, `AC_MOTHER'S_ROOM`, `AC_HUB_ROOM`, `AC_UPS_SERVER_BATTERY_BMS_ROOM` | Rooms, 117 in total. |
| `AC_COLLAB` 5 | **Acker Garden · Work Arena**, render key `garden`. The NW corner has the punch bag and swing chair. |
| `AC_COFFEE_CORNER` 7 | Coffee corners (render key `pantry`, labelled "Coffee corner"). |
| `AC_WORKHALL`, `AC_CORRIDOR`, `AC_RECEPTION`, `AC_CAFETERIA`, `AC_LIFT_LOBBY`, `AC_OUT_OF_SCOPE`, … | The **space plan**: 8 categories, each m² counted once, in priority order. |
| Numbered markers: 1 `AC_LIFT_LOBBY` (+ `AC_ENTRY` arrows), 2 `AC_WASHROOM`, 3 `AC_FIRE_EXIT_STAIRCASE`, 4 `AC_AHU`, 5 `AC_STRENGTHEN_SLAB`; plus `AC_OUT_OF_SCOPE` and `AC_FIRE_COMPARTMENTALISATION` | The **due-diligence step**, numbered exactly as in the drawing. |

---

## 4. Site analysis (`tools/site/`)

- **Address:** Regalium Building, WJJ7+CQW, Koramangala Industrial Layout, Bengaluru 560095. That is 12.9311° N, 77.6145° E, on the 3rd floor of Machani Group's Regalium.
- **`facts.json`:** typed in by hand from the site visit:
  - areas: SBA 91,000 sq ft, carpet 56,650 sq ft, ~640 headcount;
  - heights and structure: slab 3,700 mm, beam bottom 3,250 mm, PT slab;
  - finishes: full-height glazing from FFL, screed still to be laid;
  - notes: 5 exits, entrance from the lift lobby.
- **`context.json`:** committed. It is built by `site.py prep` from `raw/` (git-ignored, about 25 MB), which `fetch.py` downloads. Sources:
  - **Overture Maps** release 2026-09-23.1 on S3 (OSM data, ODbL): buildings, roads, places, land use. Reading it needs `pip install pyarrow`.
  - **Google Open Buildings** via `gsutil` (cross-check only).
  - **NOAA ISD-lite**, station 432950: wind 2014–2025.
  - **NOAA GHCN** IN009010100: rain and temperature 1991–2020.
  - The OSM, Overpass and Nominatim servers were blocked in the original environment, which is why these copies are used.
- **Results:**
  - **North:** the floor is turned 11.5° east of true north. The cores face north, the terraces south, the slanted SW end faces Hosur Road.
  - **Sun:** the noon sun is north of the building from 26 Apr to 19 Aug.
  - **Wind:** the monsoon wind is SW 53% and W 25%. The monsoon/wind slide was **removed at the user's request**; the wind data is still in `site.json`.

---

## 5. The deck today (28 steps)

1. **Cover and idea:** the city analogy and the loop.
2. **The site:** the map with walking distances, then the "Which way is north" zoom.
3. **The floor:** the shell, then due diligence from the `AC_` markers, with the site-visit facts and a section drawing.
4. **Sun and climate:**
   - the sun-path dome;
   - morning to evening on the layout: sun patches, a time slider, season chips, and three narrative beats with layout takeaways.
5. **Daylight:** the 6 m band; 45% of desks sit inside it.
6. **Fire and egress:** exits with distance rings and the fire compartment line, then the 8 routes measured.
7. **Carving the floor:** the six neighbourhoods and the shared spaces.
8. **The layout:** the full fit-out, then the **space plan** (new), then carved into neighbourhoods.
9. **Shared spaces.**
10. **Sharing out:** a matrix whose Brief column still waits for Acko's numbers.
11. **Axonometric:** the 3D view, then exploded.
12. **Neighbourhoods:** an overview and six deep dives.
13. **By the numbers.**

Click any room or desk to open the render viewer. Real renders exist only for **reception** and **garden**; every other space shows a generated sample visual.

---

## 6. Open decisions to confirm with the user

- The 2-pax rooms are drawn on `AC_QUICK_SPIRIT`, so they count as quick sprints (37). Is that intended?
- The shared-space "Lobby" (`TC`) is the east lift lobby. Because the lobby is cut out of it, the east reception zone R2 is now only about 75 m². Is that fine, or should the receptions come from `AC_RECEPTION`?
- Team names and colours for the neighbourhoods are still placeholders.
- The brief numbers (`BRIEF` in `tf_plan.js`) are missing.
- Fire travel distances still need an NBC check with the fire consultant.
- The handover spec and junior-guide PDFs still use v1.1 naming, and haven't been updated for the AC layers or the new names.

---

## 7. Next steps

1. **Merge:** the user is adding a slide on another branch and will open a PR into `main`.
   - If `tools/testfit/tf_steps.js`, or any other source file, conflicts, resolve it in the **source**.
   - Then rebuild `index-testfit.html` by running the pipeline on the DXF. If the DXF isn't available, re-run only `build_tf.py`, using a work dir that already holds `realfit.json` and `site.json`.
   - Never hand-merge the generated HTML.
2. **New renders:** add `renders/<key>-light.*` and `renders/<key>-dark.*`, then rebuild.
   - The keys are: `desk`, `garden`, `cabin`, `sprint`, `dept`, `huddle`, `hatchery`, `training`, `booth`, `pantry` (coffee corner), `zen`, `prayer`, `mother`, `cafe`, `reception`, `lobby`, `visitor`, `board` and `studio`.
   - Use `n0X-<key>-…` for a render that belongs to one neighbourhood only.
3. **A new DXF revision:** run `tools/testfit/run.sh new.dxf`. Then check:
   - the totals printed in the run log: desks, AC rooms, due diligence, space plan;
   - the deck, stepped through with Playwright in dark, light and phone sizes, with no console errors;
   - the render viewer opens, with real images for the reception and the garden.
4. **Testing pattern used so far:** Node and Playwright scripts that:
   - load `index-testfit.html#<step-id>`, press ArrowRight through all steps, screenshot them and collect console errors;
   - click hits like `#plan3d .hit[data-k="garden"]` and check that `#rv` opens with `#rv-light` and `#rv-dark` loaded (naturalWidth > 0).

---

## 8. History (the short version)

1. Built the brief/loop/zen narrative deck (`index.html`) and kept the previous version as `index-v1.html`.
2. Built `index-testfit.html` from the real test-fit DXF (test fit 02), with zones and fire routes read from the drawing panels.
3. Wrote the deliverables PDF: naming rules and what the user's team must supply.
4. Renamed to Neighbourhood 01–06, Shared spaces and terraces.
5. Added the site analysis from real open data, with north worked out from the building footprint, and the sun on the layout through the day.
6. Added the real reception and Acker Garden renders, made the render viewer full-bleed with glass controls, and removed the monsoon slide.
7. Fixed GitHub access: the Claude GitHub App needed the repo; after that, `main` was created and pushed.
8. Rebuilt everything from `acko-layout-tf03.dxf` and its `AC_` layers: space plan, due diligence from the markers, coffee corners, training room, garden from `AC_COLLAB`. Pushed to `main`.
