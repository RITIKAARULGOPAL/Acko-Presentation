# Presentation patterns (ACKO · The Loop)

Patterns built for this deck, logged as they were made, with enough of the code, values and gotchas to lift into another deck or into Presenta.

## 1. The page in deck points
**What:** every slide is a 16:9 page measured in the PPT's own points, so positions and sizes read straight off the deck.

```css
:root { --pw: min(100vw, 177.7778vh); --ph: calc(var(--pw) * .5625);
        --pl: calc((100vw - var(--pw)) / 2); --ptop: calc((100vh - var(--ph)) / 2);
        --pt: calc(var(--pw) / 720); }                 /* a 10" deck is 720 pt wide */
.page { position: absolute; left: var(--pl); top: var(--ptop); width: var(--pw); height: var(--ph); }
.page > * { position: absolute; }                     /* children placed in % of the page */
```

- **Placement:** an element at the deck's `[x, y, w, h]` (% of the slide) gets exactly `left/top/width/height` in %. Type uses `calc(var(--pt) * 18)` for 18 pt.
- **Fixed chrome:** the copyright and lockup use the same variables, e.g. `left: calc(var(--pl) + var(--pw) * .018)`, so they sit on the page, not on the window.
- **Gotcha:** nested groups (`<div>` covering the page with children inside) need `position: absolute` on the children too. `.page > *` only reaches one level.

## 2. Reading the deck, not retyping it
**Tools** (`tools/acko/`):
- `deck_inventory.py`: every picture, with its media file, pixel size, box (% of the slide) and crop. It walks groups through `chOff` / `chExt`.
- `deck_text.py`: the text boxes, with box, point size, font and colour.
- `deck_anim.py`: the click order (`p:timing` main sequence: click → entr/exit + target).
- `deck_layout.py`: prints `<i class="dk">` for every picture on a slide, with the deck's crop as CSS:
  `background-size: 100/(1-l-r)% 100/(1-t-b)%; background-position: l/(l+r)% t/(t+b)%`.

**Gotchas:**
- **Shapes with a picture fill:** a portrait can be a `p:sp` with a `blipFill`, not a `p:pic`; python-pptx won't list it as a picture.
- **Rotated pictures:** read `<a:xfrm rot="-5400000">` and turn the cut image to match.
- **Render the deck with PowerPoint itself** (COM `Slide.Export(path, "PNG", 1920, 1080)`) for checking and stand-ins. LibreOffice isn't needed.

## 3. Green-screen animations from the deck
**What:** the deck's "GIFs" are chroma-key clips that PowerPoint makes transparent: a green screen for the campus axo, black for the loop ribbon.

**How:** key them out per frame and save as an animated WebP.

```python
green = g - max(r, b);  alpha = clip(1 - (green - 25) / 70, 0, 1);  g = max(r, b) + min(green, 8)  # despill
frames[0].save(p, "WEBP", save_all=True, append_images=frames[1:], duration=durs, loop=0, quality=74)
```

13 MB GIF → 1.6 MB animated WebP.

**If a static version exists, prefer it.** The ribbon is drawn crisper from the deck's 2007 px still with a moving mask:
`mask-image: linear-gradient(90deg, #000 0, #000 var(--rv), transparent calc(var(--rv) + 6%))`, with `--rv` driven 0 → 106% by rAF.

**Update (19 Oct):** Ritika preferred the deck's own GIF writing the ribbon, so the Loop now plays it frame by frame (§11). The wipe was a straight line; the GIF follows the ribbon's path.

## 4. Stops that come up as a line reaches them (the Loop)
- **Stops:** each is `[name, words, dot x/y, label x/y]` in % of the page. The label's offset from the dot is `calc(dx * var(--pw) / 100)`.
- **Timing:** each stop turns `.on` when the ribbon's reveal `--rv` passes its x.
- **Leaders:** dotted quadratic paths in a 1920 × 1080 SVG with `preserveAspectRatio="none"`. Each fades in with its stop.
- **The thread:** the same seven quotes come back as the walk's quote on each render. One idea, carried through.

## 5. Two clusters → one loop (the challenge → the solution)
**Setup:** 64 dots, each with three positions stored on it:
- `data-a`: its office cluster
- `data-b`: drifted towards the other office
- `data-c`: on a figure of eight, `x = 960 + 520 sin t`, `y = 270 + 240 sin t cos t`

**Motion:**
- Beat 1 animates a → b over 2.8 s; beat 2 animates → c over 2.4 s.
- Each dot is staggered by `(i % 16) * 25ms`.
- CSS `transform: translate()` with a cubic-bezier transition.

**Status:** removed from the ACKO deck on 19 Oct at Ritika's request (the deck leaves this space empty); kept here as a pattern. The code is in git history before the commit "Challenge: no dots animation".

## 6. A live Möbius strip (three.js r147, no textures)
**Geometry:** a parametric strip, `x = (R + v cos(u/2)) cos u`, `z = (R + v cos(u/2)) sin u`, `y = v sin(u/2)`, with `R = 1.95` and `v ∈ ±0.52`.
- Two offset sheets (±T/2 along the normal) give it thickness.
- `MeshStandardMaterial(#e6e1f0, roughness .55, DoubleSide)`.

**Gotcha:** white on a white page vanishes where it's lit. What fixed it:
- a darker hemisphere ground (`#5a5175`)
- a lavender rim light
- its single edge (`u` over 0 → 4π at `v = W`) drawn as a 1 px `THREE.Line` in `#8f78dc`

**Framing:** fov 24, camera `(0, 6.6, 5.6)`, so the hole frames the copy. A slow sway `rotation.y = -0.6 + 0.28 sin(0.18 t)` keeps the copy inside the loop. Don't spin it fully.

**Status:** replaced on 21 Oct 2026 by §18 (Ritika: the deck's own photo, with her path drawn on it). The three.js strip is in git history before that change; `three.min.js` stays for `s-challenges` and the axo.

## 7. One plan in the world, flown between slides
**What:** the layout is an SVG in the persistent world layer (`#world-plan`). Successive slides retarget its viewBox, so the layout flies into blow-ups X / Y / Z without a cut.
- `vbFor(box, display)` returns the viewBox that shows a frame-px box inside a frame-px display rectangle.
- The tween uses easeInOutCubic.
- **Interaction:** wheel zooms about the cursor (`w *= exp(deltaY * .0015)`), drag pans, double-click returns to `DP.home`.
- **Overlays** are classes on the SVG: `show-nb`, `show-fire`, `show-lab`. The outlines draw with `stroke-dasharray: var(--len)` and a per-path delay.
- **Hover:** a legend row hovered sets `.focus` on the SVG plus `.hi` on its polygon. The others dim to .2.

## 8. Keyplan from the deck's own crop
**What:** a render slide's keyplan is a crop of one of four keyplan images, plus a maroon V shape.

**Reading it:**
- `extract_assets.keyplans()` reads the V's centre and rotation from the slide XML.
- It maps that through the picture's box and crop into % of the keyplan image.

**Showing it:** the walk frames the image around that point at 1.5× the deck's crop width, clamped to the image edges. A pulsing ring marks the camera.

**Later:** replaced by the DXF's `AC_CAM` cameras.

## 9. Small beats that read well
- **A deck's one-click sequence, in its own timing** (the journey, slide 5). One click in the PPT runs a chain of "after previous" effects. Here one beat class (`.b2`) plays it as CSS transitions with delays:
  - the collage fades out (1 s); the road, heading and quote fade in (1.2 s, from 1 s)
  - the years and labels appear (`opacity 0s 2.2s`)
  - the timeline flies in from the left, one page width, linear (`translateX(-100%) → none`, 2.5 s, from 2.2 s), clipped to the page
  - the wordmarks appear (`opacity 0s 4.7s`)
  
  **Replay:** going forward, remove `.b2`, force a reflow, add it. Going back, or arriving from the next slide, add `.rm` (`transition: none`) so it switches without playing. Read the timings with `deck_anim.py` and the slide's `p:timing` (`nodeType`, `dur`, `cond delay`, `ppt_x`).
- **Homogeneity:** a lattice of desk parallelograms along the axo's two axes, clipped to the floor polygon, minus the core and terraces. They appear sweeping along the length (`--d = i/N * 1400ms`), then dim to .28 for the next beat.
- **The sun on the bare plate:** 24 half-hour frames of sun patches, 300 ms apart, with a sun dot on an ellipse at the frame's azimuth (corrected 11.5° for the plan's north). Then the 6 m daylight band appears: the plate outline stroked 12 m wide and clipped to the plate.
- **Exit rings:** `transform-box: fill-box; transform-origin: center; scale(.2 → 1)` on SVG circles.

## 10. One page per slide, joined into one file
**The idea:** every slide is a complete HTML page that runs on its own, and the build joins them into the deck. People and parallel sessions work on separate files, with no merge fights.

**The slide file:**
- Markers `<!-- slide:start -->` … `<!-- slide:end -->` wrap its section, `<style>` and `<script>`. The build takes only that part.
- The head has `<base href="../">` and `<script src="assets/js/dev.js">`. `dev.js` `document.write`s the stylesheet, the data, `shell.js` and the engine, then calls `ACKO.start()` on DOMContentLoaded.
- **Gotcha:** the `<base>` must be static in the file. Written from JS, the browser's preload scanner has already fetched body images against the wrong base, and you get 404s.

**The engine:**
- It does nothing until `ACKO.start()`. Slides register factories: `ACKO.slide(id, (K) => hooks)`.
- At start: `H[id] = factory(kit)`. Slides with no script get the shared hook of their class (`walk` / `palette` / `vpage`).
- **The chrome when a slide is alone:** `start()` injects `window.ACKO_SHELL` (`_shell.html`'s body as a string, generated by `build.py`) when there's no `#stage`, and moves the sections in.
- **Gotcha:** with a `<base>`, `location.replace("#s-x/1")` resolves against the base and leaves the page. Use `location.href.split("#")[0] + hash`.

**The single file** (`build.py --single`):
- **Payload:** one JSON in `<script type="application/json">` holding `{css, body, scripts[], assets{path: [mime, base64]}}`, with `</` escaped as `<\/`.
- **Loader:** decodes each asset to a Blob URL, then regex-swaps `assets/…` paths in the CSS, markup and scripts. It injects the style and body, and runs the scripts in order by appending `<script>` elements with `textContent`.
- **Dynamic paths** go through `ACKO.asset(p)`, i.e. `window.ASSET_URLS[p] || p`.
- **What gets embedded:**
  - every literal `assets/…` path
  - files named by key anywhere in the text (`r-board-op1`)
  - files under a `${`-template prefix (`assets/img/skv/logo-${n}`)
- **Never** build a path from just `assets/img/${key}`: the bundler can't tell what's needed.
- **Result:** 46 MB, ready in about 0.6–0.8 s. `walk.js --single` fails on any non-blob request, which proves the file needs nothing beside it.

## 11. A deck GIF played once, frame by frame on a canvas (the Loop)
**What:** the deck's loop GIF (slide 11) writes "loop", holds it, then clears it and repeats. On the stops beat it should write once and stay.

**Why not an `<img>`:**
- It loops forever, so the ribbon would clear itself under the stops.
- It can't be restarted reliably on each visit to the beat.
- It can't tell the stops when to appear.

**How** (`tools/acko/loop_frames.py "<deck.pptx>"`):
- **Frames:** keep only the writing, up to the first frame where the ribbon is complete (79 frames at 40 ms ≈ 3.2 s). Apply the deck's srcRect crop and save each frame as `assets/img/s-loop/draw-NN.webp` (1600 px, 2.2 MB in all).
- **Fit the box:** place the finished ribbon on the slide-12 still, where the stops were placed, by matching their alpha bounding boxes. The deck's two boxes differ by a few px.
- **Reach array:** per frame, the cumulative rightmost drawn column, mapped to % of the page. A stop turns on when the ribbon's reach passes its x.
- **Player:** preload every frame on `enter`, through `asset(`…`draw-${nn}.webp`)` so the single file embeds them by prefix. A rAF loop draws `floor(elapsed / 40)` and holds the last frame.
  - The clock starts only once every frame has loaded (or failed), so a slow load never skips the writing.
  - It draws a frame only once it has loaded, so the canvas never blinks empty.
  - A run id stops an old loop when the beat changes.
  - `ctx.globalAlpha` is the deck's 75%.
- **Layering:** as on slide 12, the canvas sits in front of the trees and people, which read through it; the Work figures stay on top. The cut-outs' white backgrounds vanish under the ribbon.

**Status:** on 21 Oct 2026 the writing was retired in favour of §19. The ribbon is in place as the Loop opens, and the Möbius line runs along it.
- Only the GIF's last frame (`draw-78.webp`) is used, by its literal path, so the single file embeds one frame.
- The frame files stay on disk.
- The player above is in git history.

## 12. The DXF plan in the world (PlanHover, pictures at three sharpnesses)
**What:** the layout and its blow-ups use the DXF plan (via the DXF plan toolkit). Hover a space for its name and m², or a neighbourhood for its seats. The plan still lives in the world layer, so the layout flies into X / Y / Z without a cut (§7).

**Why pictures:** the toolkit's vector plan (16.5 MB, half a million line pieces) animates at about 5 fps, too slow for a fly-in. So the plan is rendered from its `full.svg` (puppeteer, transparent) at 12, 24 and 48 px per m: 0.5, 1.1 and 2.6 MB.
- They sit as three `<image>`s in the component's plan SVG. The coarse one always shows.
- A sharper one turns visible when the zoom needs it: screen px per m × devicePixelRatio, against each level's px per m.
- The sharper ones are decoded ahead (`new Image().decode()`), so the first zoom doesn't stall.
- **Result:** fly-ins and wheel zoom at 60 fps.

**Layers through `addLayer`** (toolkit component 1.1):
- **Beneath:** fills, the floor tint and the spaces in their legend colours.
- **Above:** marks, with `pointer-events: none` and lines `vector-effect: non-scaling-stroke`. The marks are the neighbourhood outlines and numbers, the egress paths, the fire line, the entrances, the arrival zones and the blow-up labels.
- **Hovers per beat:** set by classes on the root, `.dxplan:not(.show-rooms) .ph-room { pointer-events: none }`.
- **Legend rows:** call `highlight("team", id)`.
- **Fly-ins:** a tween calls `zoomTo` from `view`.

**Gotchas:**
- Text and fill sizes in the marks are in plan mm (for example `font-size: 2600px`), so they scale with the plan. Only strokes stay constant on screen.
- A full-page `.ui` overlay on a slide (`.scene.active .ui { pointer-events: auto }`) blocks the plan's hovers underneath. Keep `ui` on the controls, not on page-sized wrappers.

## 13. Spaces from a slide's legend colours, placed on the DXF
**What:** the deck's layout slide colours every space by its legend. Those colours become the space boundaries on the DXF plan; walls alone gave boundaries that didn't match the design.

**How** (`tools/acko/plan_dxf.py`):
- **Fill patches:** in each of the slide's plan tiles (lossless PNGs, read at their own resolution), the flat fill colours are every distinct colour with ≥ 300 px.
  - Skipped: white, black and the workhall floor.
  - Shades within 2 levels are merged.
  - Each colour is masked, closed 3×3 (bridging furniture lines but not thin walls), and traced with `cv2.findContours`.
- **Onto the DXF:**
  - **Global fit:** an affine from the slide's frame px to DXF mm. It was measured by overlaying the composed tiles on a render of the DXF and is good to about 0.3 m.
  - **Per tile:** a small `cv2.phaseCorrelate` shift of the tile's ink against the render's lines.
- **Names:** the DXF room label inside each patch. A pod's label often sits just outside it, so the nearest label within 1.2 m is taken.
- **Type:** from the name (BOARD, HUDDLE, SPRINT, PB …), or failing that from the nearest legend colour (within 4 levels).
- **Small pods:** phone booths are lilac pods of only 0.3 m² of colour, so they get their own size threshold and are grown 150 mm to make them hoverable.
- **Seams:** patches cut by a tile seam (same type, touching) are merged.
- **The floor tint:** warped into the plan frame as one picture.

**Result:** 136 spaces, including 42 phone booths, on the DXF walls, each keeping its slide colour.

## 14. Click a neighbourhood: zoom, key plan, occupancy chart
**What:** on the layout's *Six neighbourhoods* beat, a click on a neighbourhood (on the plan, or its row) flies the plan into it on the left of the page; a white panel on the right shows a small key plan of the floor (that one filled), its name, workstations and area, and its occupancy chart in the occupancy slide's table style.

**How:**
- **Data** (`tools/acko/plan_dxf.py`): each zone gets `box` and `occ`. `occ` is the occupancy slide's rows, limited to the spaces whose label point lies inside the zone's outline; a space named for several labels (`PB 10 / PB 11`) counts each one.
- **Engine** (kit `plan`):
  - `onZoneClick(fn)`: a click anywhere inside an outline (point-in-polygon in plan mm, through the plan's own viewBox mapping), so the gaps between desks count. A press that moves more than 4 px is a pan, not a click. Cleared by `planOff`.
  - `focusZone(id, disp)` flies to the zone's box (1.5 m margin) inside a display rect in frame px, adds `focus-zone` (the others dim, its rooms take the hover), and makes that view the double-click home. `focusZone(null)` flies back.
  - `keyplan(id)`: markup for the key plan (the 12 px/m picture, faint, with the six outlines).
- **Slide:** the panel and a white top and bottom band (behind the header and footer) fade in on `zp-open`, and the rows fade out. Esc is caught in the capture phase while one is open, so it doesn't reach the deck's overview key. A beat change or leaving the slide closes it.
- **Watch:** a function named like one already in `app.js` (the walk has a `keyplan`) is silently overridden by the later declaration; give engine helpers distinct names.
- **The tools** (top right on the layout and the blow-ups, a `ui` flex group of `.ly-tool` pills):
  - **Neighbourhoods:** `plan.planNb(on, labels)` switches `show-nb`, `show-teams` and (unless `labels === false`) `show-lab` together. The blow-ups pass `false`: at their zoom the big numbers would be 4–5× larger, and the hover names each one. On the layout, opening a neighbourhood follows this button, on any beat; switching it off closes one.
  - **Reset zoom:** `plan.planReset()` flies to `DP.cur`, the framing in force: `planOn` sets it to the beat's view, `focusZone` to the zone's (and back on close).
  - While one is open, every beat's lower panel (legend, rows, egress legend) and the plan's blow-up captions step aside.
- **The plan takes the page** (Ritika: the legend and chart collapsible, the layout filling the canvas):
  - **Two framings:** the floor centred at full width (`vbFor(viewBox, [24, 130, 1896, 950])`, the default), or the deck's top band (`planView()`) while the beat's key drawer is open beneath it. `plan.planHome(v)` switches the beat's framing (and flies there unless a neighbourhood is open), so Reset and closing a neighbourhood follow it.
  - **The key drawer:** one tab, bottom left, labelled for the beat; `dr-open` on the section shows that beat's panel (overriding `[data-only].shown`). Every beat arrives with it shut.
  - **An open neighbourhood:** with its chart tucked away (the default) it fills the page above a bar (key plan, name, workstations, area, Occupancy chart, All neighbourhoods); `occ-open` brings back the right-hand panel and refits it into the left. Switching keeps the chart's state; closing resets it.
  - **Testing a click on a neighbourhood:** pick the point by the engine's own rule (the first outline that contains it). A desk of one neighbourhood can lie inside another's outline.

## 15. A live axo from the toolkit's classed SVG
**What:** the deck's schematic axonometric (slides 58–60), rebuilt as a live three.js model of the DXF in the deck's axo look:
- a pale slab on a soft shadow
- the rooms in translucent purple glass with dark frames
- wood desks, grey chairs, green plants
- black mullions round the façade
- grey masses for the rest of the building's floor
- thin ink edges
- the faint plan drawing on the floor, clipped to the slab

West, Middle and East fly an orthographic camera along it.

**Data** (`tools/acko/axo_dxf.py` → `data/axo-dxf.js`, 0.3 MB):
- **Source:** the toolkit's `instanced.svg`. Every path is already classed (wall, glass, furn, green, base…), and every block is drawn once and placed by `<use transform="matrix(...)">`. The DXF isn't read again.
- **Furniture:** closed outlines, plus the faces of the open linework (polygonized face by face; merging them fuses a table with the chairs drawn across it). Each is classified first (chair, desk, store, or nothing), and only then are nested shapes dropped, so a rug or cluster outline can't hide the desks inside it.
- **Pod desk tops:** they're the block's `base` lines, broken where CAD hid them under the chairs. They're closed by thickening the lines 110 mm and taking the enclosed holes.
- **Furniture is stored:** per block once, plus the placements.
- **Slab:** the occupied floor (neighbourhoods, spaces, the toolkit's rooms), closed and filled. Walls are clipped to it, and furniture is kept only in the spaces people use (not the cores' fixtures).

**Slide** (`slides/s-axo.html`):
- **Geometry:** flat-shaded prisms gathered per material into a few meshes, and one LineSegments per pen. Faces sit behind their lines (polygon offset); glass and panes draw last without writing depth.
- **Drawing:** on demand only, while a tween or a drag runs.
- **Beat cameras:** each third is fitted by projecting its slab points on the camera's right/up axes.
- **Labels:** projected each frame. Each side's names sit in one column so the leaders run level; one with no room on its side goes the other way, beside its space.
- **Fallback:** if the WebGL context fails, the section takes `ax-fallback` and shows the deck's three axo pictures with their leaders.
- **Tests:** `sc._axo()` exposes the camera state and a projection, read-only, for the tests (WebGL canvases can't be read back without `preserveDrawingBuffer`).
- **Hover on / off** (Ritika, as in Mitigata): one deck-wide state in the engine.
  - **Engine:** `HOVER`, with `plan.planHover(on)` and `plan.hoverOn`. `no-hover` on the plan root hides the label and turns off the hover targets with `!important`, which beats the open neighbourhood's room hovers. It survives `planOn` / `planOff`, so it stays as set across the layout, the blow-ups and the axo.
  - **Slides:** each one's pill syncs from `plan.hoverOn` on enter.
  - **The axo's own hover:** the cursor is taken to a plane at 0.4 m (desk height, less parallax than the floor) and tested against the deck's spaces, smallest first, then the neighbourhoods. The hit space gets a purple floor fill and outline, and a label in the plan's style above its label point at 2.6 m.
- **The floor's occupancy chart on the layout:** a second tab beside the Legend; one drawer at a time.
  - **Source:** the brief's table, kept in the layout slide itself (`<template class="ly-oc-src">`), read on first open and split at "Training room" into two columns. (It was the occupancy slide's table until that slide, deck 61, was folded into this panel on 22 Oct: Ritika, "its there in layout page already".)
  - **Standalone:** the table travels with the slide, so the tab works when the layout slide is opened on its own too.
- **Gotcha:** a slide that draws over the world (the axo) must call `plain()` on enter. Otherwise the layout's flat plan, left in the world by the blow-ups, shows through its transparent canvas.
- **The occupancy charts in Mitigata's look** (Ritika: "take reference from mitigata presentation"):
  - **Builder:** one `occTable(rows, req)` gives Mitigata's `occ-t`: Zone | Area (| Requirement) | count. The zone cell spans its rows in small purple capitals, the rows are hairlines with no fills, and each count gets a mark.
  - **Floor chart:** it reads slide 61's rows, carrying the zone down from each rowspan cell. Each cell's class becomes a state: `short` → ▼ (maroon), `up` → ▲, `up` with nothing asked → +, otherwise ✓. It sits in a white card with a summary line computed from the rows.
  - **Expand:** ⤢ centres the card larger over a flat white 72% scrim. ✕, Esc (caught before the neighbourhood's Esc) or a click on the scrim closes it.
  - **Neighbourhood chart:** the same builder without the requirement column.
- **As sharp as the viewer when zoomed in** (Ritika: "not as clear as" the toolkit viewer). Past the zoom the pictures are made for, their baked lines go soft and heavy.
  - **Tiles:** `tools/acko/plan_vec.py` cuts the toolkit's `full.svg` into 12 m tiles, each with the bbox of all it holds. Each subpath goes to the tile of its first point; the paint order is kept so wipeouts still mask; coordinates are relative. 24 → 13 MB.
  - **Layer:** `deckPlan` adds one `ph-plan dx-vec` layer (the component's own viewer styles: non-scaling strokes) just above the picture and under the hovers and marks.
  - **Switching:** `level()` turns it on past 16 device px/m (`vec-on`). Tiles in view (plus 15%) are built on first sight, a few per 12 ms frame (`vecBuild`), and the picture steps aside only once they're all there.
  - **Moving:** flights (`vec-fly`), and drags and wheel-zooms when more than 20 tiles are in view (`vec-heavy` with `ph-dragging` / `vec-wheel`), show the picture, so they stay at 60 fps. It sharpens as they rest.
- **Hover on the real room boundaries, tinted under the drawing** (Ritika: "follow how it is in mitigata"). Mitigata's rooms were the CAD team's polylines, drawn in a "hoverfloor" group under the furniture.
  - **Outlines:** ACKO's legend traces are notched wherever the slide's furniture sat, and about 0.3 m off, so `tools/acko/snap_spaces.py` snaps them to the faces of the drawing's partition linework:
    - **Lines used:** walls, glass, doors and the shell; planters (`shade`); the façade rails, which the toolkit classes as furniture, so `furn` lines over 2.5 m count.
    - **Doorways:** each one is shut along the door's closed position (from the swing arc's hinge to its ends).
    - **Breaks:** bridged by thickening the lines, taking the enclosed holes and growing them back. Each space tries 45, 120 and 160 mm (the small gap keeps the booths).
    - **Choosing faces:** a face counts if it's mostly inside the trace, or holds 30%+ of it and is at most 4× the trace (2.5× past 60 m², so a trace never takes the open floor).
    - **Accepting:** at 75% coverage (50% for booth-sized rooms, whose traces spill out of their doors). Otherwise the trace is notch-closed and clipped to the walls.
  - **Layering:** the component's `.ph-rooms` layer moves under the picture and the vector (they take no pointer events), so the tint sits under the linework. The teams stay on top.

## 16. One live model for two slides: the axo and the campus strategy
**What:** the floor's three.js model is now a shared module, `assets/js/axo-model.js` (`window.AxoModel`), used by the schematic axonometric (`s-axo`) and the campus strategy (`s-strategy`).
- **One renderer:** a single WebGL renderer, whose canvas moves into whichever slide is showing (one GPU context).
- **One model:** built once, in layers (`base`, `walls`, `glass`, `facade`, `furniture`, `plants`) that a slide can hide or grow. `M.reset()` puts them back as built, and each slide calls it on entering or leaving.
- **Camera helpers:** `AxoModel.basis / apply / frame(m, view, x0, x1, fit, asp)`, so each slide keeps its own camera state.
- **Redraws:** async work (the floor drawing) notifies the showing slide through `AxoModel.listeners`.

**The strategy slide plays once on arriving**, as the PPT's GIF did:
- **How it started:** each layer's `scale.y` grows 0 → 1 in turn.
- **Looping it all together:** the Loop is a flat band whose index draw range grows.
  - **Path:** two lanes along the floor, a quarter of the way in from the slab's edges at every 2 m of its length, joined at the ends. A Catmull-Rom through stops alone left the building where the floor narrows, and pulling waypoints inside made it zigzag.
  - **Stops:** found on the plan by type: the reception nearest the first entrance, the café, the boardroom, the quick sprint nearest the middle, collab, the biggest neighbourhood, a wellness room.
  - **Lighting:** each stop lights when the band reaches its nearest point on the loop.
- **The client's journey:** a maroon band, with a dot walking it.

**Interaction:** a click (not a drag) replays it, drag turns, the wheel zooms, Reset view goes back.
**Labels:** they step up to avoid each other, and hang left near the page's edge.

## 17. Spaces straight from the drawing: labels in the rooms their walls enclose
**When:** a new test fit (21.10.26) arrived after the PPT, so the PPT's legend colours (slide 53) no longer described the plan.

**How:**
- **Labels:** each room label comes from the toolkit's `labels.json`, at the centre of the drawn text's box.
- **Faces:** the label takes the room face the partition linework encloses (`tools/acko/faces.py`, the builder from the snapping step, now shared; `snap_spaces.py` retired).
- **Size limits per type:** each room type has a minimum and a maximum (m²).
  - **Minimum:** a table under the label makes a small face of its own. The room face still holds it unless the table touches the walls.
  - **Maximum:** a room leaking through a gap makes a face far too big, so the next bridging level is tried.
- **Furniture joined to a wall:** a desk against a wall makes the label sit in the desk's own face, cut off from the room. The room-sized face touching it most closely is taken, with the piece included.
- **Fallback:** open-plan or open-sided labels keep the previous build's outline of the same name.
  - **Which one:** the same-named room nearest the label (names repeat, such as two "Executive Corner Cabin 02"s).
  - **Checked:** only if that outline sits within 200 mm of the new walls. Otherwise there's no outline, which is better than a wrong one.
  - **Reference:** the previous spaces are kept once in `tools/_work/plan/prev-spaces.json`, so re-runs compare against the same set.
- **Not in contract:** the area (`ak_zone_Nic`) is a space with its own grey, and kept out of the axo's slab and floors.
- **Text at its CAD size:** fixed in the toolkit (`text_outline.py`). Every text is drawn as its glyph outlines in its style's font with its width factor and MTEXT formatting, so a label never outgrows its room. Rooms read the drawn box from `labels.json`.

**Addendum (21 Oct, Ritika: "include the door area also"; "all the spaces are not rendered"):**
- **Doors:** a swing door's leaf and arc were walls, so each swing became a small sector of its own, left white beside its room. Now only the closed position (the arc's hinge to both its ends) shuts the doorway. The leaf dangles and splits nothing, so the swing area is part of the room. Folding and sliding doors still close a room as walls do.
- **No furniture:** tables and desks never bound a room (a Quick Sprint took only its table). Only furniture lines over 2.5 m that are open or thin (the façade's rails) are used, and the furniture-against-a-wall rule is retired.
- **The floor plate as the outside wall:** the façade's mullion units are short furniture pieces, so rooms along it leaked outside. The plate (neighbourhood zones plus the toolkit's rooms, closed by 1.5 m, out 150 mm) is added as a line.
- **Minimum by PAX:** a meeting room's minimum is at least 0.9 m² per PAX in its label.
- **A 0.5 m bridging level** comes last, for doorways drawn without a door (Collaboration Huddle 01, Store Room, Dishwash).
- **Carried outlines** only where they hold the label (within 0.3 m) and at least half their vertices lie within 250 mm of the new walls; open-plan areas (Reception) are trimmed to the open floor they're in.
- **Names:** the dining floor is labelled only by its counters (Heating Station, Waste Disposal), so it is named "Cafeteria"; Dishwash and Plate Drop are its back of house, in the cafeteria's colour.

## 18. A hand-drawn path on a photo, drawn in one stroke (the Möbius)
**Status:** replaced in the deck on 22 Oct by §20 (Ritika: "replace these slides"); the drawn-path version is in git history.
**What:** deck slide 10's own Möbius photo, with Ritika's path along the strip drawn on in a single stroke (6.5 s, after the copy).
- The path runs twice round the strip before it meets itself.
- In front of the strip it is purple. Behind it, it is lilac, and it runs under the front where they cross.
- Ritika chose this over a light that flows along the path, marching dashes, a lane with a centre line, a travelling trail and a felt-tip look (21 Oct).

**The photo:** `assets/img/mobius.webp`, where the deck puts it (x 7.8%, 84.4% × 100%: the photo's own 3:2).
- **Opacity 35%:** the PPTX picture has `alphaModFix amt="35000"`. Without it the strip looks much darker than the deck. Check a picture's `alphaModFix` before matching tones.
- The SVG's viewBox is the photo's 1536 × 1024, so the path is written in photo pixels.

**The path:** she drew it as a red polyline in a layer over a deck screenshot (`Downloads/Screenshot 2026-10-21 131243.svg`): bright where it runs in front, light where it runs behind. Traced in a scratch script:
- **Register** the screenshot to the photo with `cv2.findTransformECC`, starting from the slide layout.
  - The warp it returns maps the template (the photo, at 35% on white) into the input (the screenshot); invert it for screenshot → photo.
  - It agreed with the plain layout to within about 7 px.
- **Trace** the line with a small tracker on the red pixels: a circle of samples ahead, the run nearest straight on.
  - Where two strokes cross at a shallow angle, prefer the colour it is already on. Otherwise it turns onto the other stroke and closes early.
  - Two colour switches with no crossing are the front/behind ends.
- **Smooth** with a periodic smoothing spline (`splprep(per=1)`, 6 px rms).
  - This rounds her polyline's corners while staying near her line: 4 px on average, at most 18 px, at the sharp tip.
  - A small Gaussian (σ 12 px) kept her corners.
- **Pieces:** front 1 → behind → front 2, as Catmull-Rom cubics. In the SVG the behind piece comes first, so the front lies on top at the crossings.

**The draw:** the three pieces are drawn as one line, with one progress and one easing over their joint length.
- `data-i` gives their order along the path.
- The engine's `drawPath` eases each path on its own, so a chain of them would stutter.
- Each piece stays `visibility: hidden` until the line reaches it, or a round cap shows as a dot before it arrives.

**Gotchas:**
- On Windows, a Python `print` with "→" fails under the console's code page. Run with `python -X utf8`; `-I` ignores `PYTHONIOENCODING`.
- Headless Chrome on SwiftShader leaves stray, rectangle-clipped smudges around animated SVG blur filters and blend modes. The real browser draws them cleanly. Check motion like that in the real browser before chasing it.

## 19. A line that carries on from one slide onto the next (the Möbius → the Loop)
**Status:** replaced in the deck on 22 Oct by §20; in git history.
**What (Ritika, 22 Oct):** the purple line of the Möbius slide carries on onto the Loop's ribbon.
1. **The opening frame:** the Loop opens on the Möbius slide's last frame: the deck's photo at 35% and her path drawn, placed exactly as `s-mobius` places them. So the engine's cross-fade only fades the Möbius words.
2. **Beat 1:** the photo and path fade as the ribbon (the deck's artwork, `draw-78.webp` at 75%) comes in. A stretch of the path, the arc round its start that she marked, about 480 page px, stays, then glides onto the ribbon's start by Arrival and waits there. Then the people, trees and welcome words come in.
3. **Beat 2:** the stretch runs the whole ribbon left to right, through every loop, and slides off its right end. Each stop and its leader come up as the line reaches it.

**How (`s-loop.html`):**
- **One full-page SVG (`.lp-run`, viewBox 1920 × 1080).**
  - **`.lp-line`:** the ribbon's centre line, also the visible stretch. One dash, `stroke-dasharray: LS (L + 2·LS)` and `stroke-dashoffset: LS − s`, so the dash covers [s − LS, s].
  - **`.lp-glide`:** a 40-point polyline for the glide.
  - **Hidden** (`visibility`) whenever not in use, so a round cap never shows as a dot.
- **No stored geometry for the glide:**
  - **The arc:** read at runtime from the `.lp-mob` path pieces with `getPointAtLength`: the end of front piece 2 and the start of front piece 1, which meet at the path's start. Mapped photo px → page px as `s-mobius` places the photo (x = 149.76 + 1.055·x, y = 1.0547·y).
  - **The landing:** the first LS of the centre line.
  - **The motion:** each point eases from one to the other (cubic in-out, 1.2 s). At the end, `.lp-line` takes over at s = LS: the same geometry, so nothing visibly changes.
- **Stops:** each stop's trigger is the first arc length where the centre line comes within 1.2 × its nearest approach to the stop's dot, because the ribbon passes some stops twice. The run (5.5 s, sine in-out) turns each stop on as s passes it.
- **Other entries:**
  - **Back to beat 1:** the line waits at Arrival, with no replay.
  - **Entering at beat 2 (going backwards):** every stop on and no line.
  - **Reduced motion:** each beat's end at once.

**The ribbon's centre line** (scratch scripts, the session scratchpad):
- **The route:**
  - **A tracker failed:** on this coil ("loop" in cursive), going straight through crossings skips each ring.
  - **The writing order:** for each pixel, the first frame of the deck's GIF that paints it, plus the centre of each frame's new paint, gave the order.
  - **96 points placed by hand** in that order (centripetal Catmull-Rom).
- **The snap:** at every 4 px, measure the band across the path (along its normal) and move the point to that cross-section's centre.
  - **Skipped where** the run is too wide (two bands overlapping at a crossing); there the neighbours' offsets carry across.
  - **Offsets** are smoothed along the path; three passes.
  - **Result:** every point on the ribbon (100%, up from about 85%).
- **Where the deck's own GIF does the same:** the route laps each ring and passes over its top twice, and dips through the crossing between the first two rings.

**Tried and replaced:** a 2D band morphing the Möbius strip itself into the ribbon (edge curves, staggered lerp, offscreen composite). Ritika: the line should move, not the strip. It is in git history (21 Oct).

**Gotchas:**
- **The cut-outs:** the slide's own `.lp-cut { opacity }` overrides the reveal's hidden state. Hold them with a container opacity (`#s-loop.lp-wait .lp-cuts`) instead.
- **Testing:** headless SwiftShader is too slow to film canvas or rAF motion in real time, and screenshots lag too. Film it on a virtual clock instead: replace `requestAnimationFrame` and `performance.now` before load, and step 16 ms at a time between screenshots.

## 20. A ribbon that slides off one slide and reveals the deck's artwork on the next (ribbon version: Möbius → Loop)
**Status:** in the deck since 22 Oct as `s-mobius` → `s-loop` (Ritika: "replace these slides"); the pieces now live in `assets/img/s-loop/ribbon-01..10.webp`. Mentions of `s-mobius-ribbon` / `s-loop-ribbon` below are their earlier names.
**What (Ritika, 22 Oct):** another version of §18–19, in `s-mobius-ribbon` → `s-loop-ribbon`, not in `order.txt` (see them at `/?only=s-mobius-ribbon,s-loop-ribbon`).
- **On the Möbius:** a lavender ribbon (60 px), not a line, runs along her path from its left-most point, twice round, and back to it.
  - Narrow at both ends.
  - Softly lighter where it passes behind.
- **On the Loop, beat 1:** the ribbon slides along itself, off that point and out of the left edge, its tail following it twice round the strip. As the tail leaves, the head comes back in at Arrival and **reveals the deck's own ribbon** along the Loop's line, so the Loop is the artwork from the first pixel.
- **Her notes that shaped it:**
  - "Ending also should be narrow."
  - "The strip should be gradient."
  - "This whole animation is very chaotic." Round 2 swung the whole strip round the page.
  - "Both loop animations are not aligning." Round 2's vector Loop ≠ the deck's artwork.

**No click between them (Ritika: "without click, let it start animating the loop"):**
- The Möbius slide calls the kit's `next()` 0.15 s after its draw ends (a `later()`, so any slide change first cancels it), and the Loop starts moving 0.3 s in, inside the 0.7 s cross-fade (Ritika: "start the Loop sooner"). The Loop opens on the Möbius's exact last frame and the motion starts slowly, so nothing doubles.
- **Only going forward:** a `MutationObserver` on `body[data-scene]` (`attributeOldValue`) records the slide it was entered from; coming back from a later slide (`sceneIx`), it stays.
  - The engine's `enter` doesn't say where it came from, and the record arrives after `enter`, so the check runs in the timer.
- **The words** (both Möbius versions) sit in the PPT's own text boxes: each line placed at its box's x, y and width, padded by the box inset (7.2 pt; 7.6 pt for the kicker, centred in its box), with the body's 12 pt space before.
  - Checked against PowerPoint's own export of slide 10 (COM `Slide.Export`, 1920 × 1080): each line within 1–4 px. PowerPoint draws it in Arial here because Figtree isn't installed for it, so compare positions, not glyphs.

**Round 4 (Ritika: "after the ending, again let it follow the path and move to next page… remove the unwravelling step with the mobius image in the background and directly draw the loop - when drawing the loop the text should slide and move in"):**
- **The Möbius:** after the draw, the ribbon slides on as one piece along her path, round to its right-most point (the behind pass down the strip's right side), and out down-right off the right edge along her green line (`mb3/bridge4.py`, `.mr-exit`), over 4 s.
  - It speeds up, then runs steadily out; it doesn't slow at the end, so it leaves moving.
  - As its tail leaves, the slide calls `next()`. Forward only, as before; back from the Loop it draws and stays.
- **The Loop page has no Möbius on it** (no photo, no strip, no left exit). It opens empty and reveals the deck's ribbon from Arrival at once, entering at speed, 4 s, slowing at the end.
  - **The words:** the title and paragraph slide in from the left once the head is 300 px in; the welcome line slides in from the right at mid-way. Classes `lr-hold-a` / `lr-hold-b` hold them off to the sides, and the frame loop removes them.
  - The words' hide transition keeps a delayed `visibility`, so they still fade out on beat 2.
  - The people and trees come in at the end.
- **Generator:** `mb/make_ribbon4.py` (the Möbius part spliced from `mob4_section.py`, the Loop part from `loop4_section.py`).
- **Round 5 (Ritika: "the ribbon should unwrap and go to next slide without beat"):**
  - **No stop at the close:** one frame loop runs the draw (the head speeds up, then steadily round) and the unwrap. At the close the head carries on at the same speed, up over the top and down the strip's right side, then out flat at y≈560, the Loop's start height on the next page, along her second line (`mb3/bridge5.py`, leaving her path at 1608, 396).
  - **The tail** unwraps from rest, faster than the head, and leaves last; then `next()` at once.
  - **The Loop draw** starts at 0 ms (3.3 s), entering at about the tail's speed.
  - **Always onward:** the forward-only check is gone (her choice), so coming back to the Möbius replays it and moves on again.
- **Made smooth (Ritika: "make it smooth"):** the exit is now one cubic Bézier plus a straight run (`mb3/bridge6.py`, leaving her path at 1612.6, 405.4). The leave point and control lengths come from a small search: even bend, smallest radius 240 px, within 7 px of her trace.
  - A Catmull-Rom through hand points had bent down to 45 px just after the join, which pinched a 30 px half-width ribbon. Measure the radius along any path a wide ribbon follows.
- The two paragraphs below describe round 3, where the strip still ran on the Loop page; the strip renderer is now on the Möbius slide only.

**How: the strip** (a canvas renderer, in both files):
- **One route, one polyline:** the Möbius pieces re-cut at the left-most point (found as the point of the behind piece nearest a fixed page point, so both slides cut alike), then the exit, in page px every 6 px.
- **Both ends taper:** half-width = W · (0.08 + 0.92 · smoothstep(min(s − tail, head − s) / 220)).
- **Front-ness F per sample:** 1 in front, 0 behind, smoothstep over ±90 px of each switch.
  - The exit's `lead` keeps the last part's side for 90 px into it, so the Möbius slide's last frame and the Loop's first frame match.
- **Two offscreen layers,** composited at 35% (behind, filled) and 75% (front, filled and edged in white). Each layer's share is 1 − F or F.
  - **Where a share is full:** one polygon per stretch.
  - **Where it is partial:** two-step pieces starting at every sample, each at 1 − √(1 − share), so every stretch lies under exactly two and comes to the share without seams.
  - An alpha gradient or one-piece-per-step leaves seams.
- **The pace:** the strip moves as one piece (tail = head − Möbius length). The turn off the page is as long as the ribbon, so the head comes back in exactly as the tail goes out. Trapezoid speed (15% up, 22% down) over 6.5 s (Ritika: "a little faster"; it was 8.5 s). The Möbius draw takes 5 s.

**How: the reveal** (no pixel reads, so it works from `file://`):
- **The artwork in pieces:** the deck's ribbon frame (`draw-78`) is cut into 10 pieces in `assets/img/s-loop-ribbon/` (lossless webp, cropped).
  - Each pixel is placed along the Loop's centre line: the earliest strand whose band it lies in (the band's half-width measured where the ribbon is single), else the nearest. The boundaries are median-smoothed.
  - Pieces are cut wherever a wide mask on one strand would uncover the same piece's pixels on another strand early (ring passes, crossings, the Wellness hook). The cuts come from interval stabbing.
- **Each frame,** each piece is drawn through a mask along its stretch of the line onto `.lp-draw` itself (1600 × 671, the ribbon's own canvas), `source-in`, at 75%.
  - **The mask:** one quad per step, all turned the same way so they join under nonzero.
  - **Its width:** a point at the head, the band's width 220 px behind it, then 100 px wide for the widest twist.
  - **Once the mask has passed a piece,** the piece is drawn whole.
- **At the end it is the artwork exactly,** and `lay()` redraws it.

**Gotchas:**
- **OpenCV `fillPoly` with many polygons in one call XORs where they overlap,** which left speckled holes in the simulation. Fill each quad on its own.
- **The GIF's first-paint map is blocky** (8-px codec blocks), so assigning crossing pixels by it gives stair-stepped edges. Assign them by geometry instead.
- **Small notches** still show for a moment where the inner pass of a ring meets the lap. They are gone once the head passes.
- **Scripts** (scratchpad `mb3/`):
  - `frames.py`: the GIF's paint history
  - `assign.py`, `assign2.py`: pixels → line
  - `pieces.py`: cuts, piece files, simulation
  - `bridge3.py`: the exit
  - `mb/make_ribbon3.py`: writes both slides

## 21. A lens on a collage (Engagement points)
**What (Ritika, 21–22 Oct):** her PPT collage stays whole; each beat lights one group and dims the rest (Feel it, Play it, Share it, then All last). Picked from the comparison pages (`index-engage.html`).

**How:**
- **Grouping:** every part of a point (tile, label, arrow) carries `data-k`. `step(k)` toggles `.lens` on the section and `.lit` on the group's `data-k`.
- **Dimming:** unlit tiles get `filter: grayscale(1) opacity(.25)`, with a per-property transition so the entrance stagger is kept.
- **Arrows:** each label's dashed arrow draws through a mask whose path animates `stroke-dashoffset` (`pathLength` 1), so the visible stroke stays dashed.
- **Chips** jump to a beat; photos open in the lightbox.
- **Matching the PPT page:** screenshot headless Chrome at 1376×774 (`--virtual-time-budget=30000`), then compare ink boxes per region against her PPT screenshot (within 0.2%).
- **Gotcha:** `tools/acko/make_value_slides.py` writes `slides/s-engage.html`; don't re-run it for s-engage.

