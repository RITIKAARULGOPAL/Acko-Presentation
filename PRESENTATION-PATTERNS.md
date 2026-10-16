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
- **The founder's words** type in word by word (each word a span, `.on` every 90 ms) after the timeline's milestones (`.jr-ms`, 230 ms apart) come in along a line that scales from the left (`transform: scaleX(0 → 1)`, 2.6 s).
- **Homogeneity:** a lattice of desk parallelograms along the axo's two axes, clipped to the floor polygon, minus the core and terraces. They appear sweeping along the length (`--d = i/N * 1400ms`), then dim to .28 for the next beat.
- **The sun on the bare plate:** 24 half-hour frames of sun patches, 300 ms apart, with a sun dot on an ellipse at the frame's azimuth (corrected 11.5° for the plan's north). Then the 6 m daylight band appears: the plate outline stroked 12 m wide and clipped to the plate.
- **Exit rings:** `transform-box: fill-box; transform-origin: center; scale(.2 → 1)` on SVG circles.
