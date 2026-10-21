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
  - **Source:** the occupancy slide's table (`#s-occupancy .oc`), cloned on first open and split at "Training room" into two columns. One source for both slides.
  - **Standalone:** opened on its own, the layout slide has no slide 61, so the tab hides (`no-fo`).
- **Gotcha:** a slide that draws over the world (the axo) must call `plain()` on enter. Otherwise the layout's flat plan, left in the world by the blow-ups, shows through its transparent canvas.

