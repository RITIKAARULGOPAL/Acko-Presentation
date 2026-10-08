# Conceptual axo

Builds the 3D axonometric of the test fit from the DXF. The deck uses it twice, after the "Exploded" step:

- **The floor, rendered** (`#axo-render`): eight stills in `renders/axo-<view>-<style>.webp`. There are four views (`floor`, `west`, `middle`, `east`) in two styles: `ref`, the reference look (grey floor, dark loop, purple glass rooms, wood desks), and `nb`, tinted in the neighbourhood colours.
- **Walk around the model** (`#axo-model`): the same scene live in three.js. Drag to orbit, right-drag to pan, scroll or pinch to zoom, and hover for the space's name.

Source drawing: `acko-layout-tf03.dxf` (test fit 03). It is about 160 MB, so it is not committed. `axo.json` is committed, so the stills and the model can be rebuilt without it.

## Rebuild

```bash
pip install ezdxf shapely
cd tools/axo
python3 dxf_dump.py ~/Downloads/acko-layout-tf03.dxf /tmp/dump.pkl   # ~2 min: flattens every block to world lines
python3 extract_axo.py /tmp/dump.pkl axo.json                        # ~20 s: prints counts to check against the drawing
npm install && npm run bundle                                         # three.js scene → axo.bundle.js
node render.mjs                                                       # → ../../renders/axo-*.webp (needs Playwright)
```

Then rebuild the deck with `tools/testfit/build_tf.py`. It embeds `axo.bundle.js`, `axo.json` and the stills into `index-testfit.html`, so the file stays self-contained and works offline.

`axo.html` is the harness `render.mjs` opens. Open it through any local web server to look at a view, for example `axo.html?view=east&style=nb`.

## What is read from the drawing

| From the DXF | Becomes |
|---|---|
| `AC_GLAZING` | Slab edge and glass façade (mullions every ~1.5 m). The notches in it on the south side are the two terraces |
| Room layers: `AC_PHONE_BOOTH`, `AC_QUICK_SPIRIT`, `AC_COLLAB_HUDDLE`, `AC_DEPARTMENTAL_ROOMS`, `AC_EXECUTIVE_CORNER_CABIN`, `AC_ZEN_ROOM`, `AC_BOARD_ROOM`, `AC_TRAINING_ROOM`, … | Glass rooms: a tinted floor with purple glass walls on the outline |
| `AC_OUT_OF_SCOPE`, `AC_WASHROOM`, `AC_AHU`, `AC_UPS_…`, `AC_FIRE_EXIT_STAIRCASE`, `AC_LIFT_LOBBY` | Solid core masses, 3.2 m |
| `AC_CORRIDOR` | The dark loop path |
| `AC_WORKHALL`, `AC_COLLAB`, `AC_COFFEE_CORNER`, `AC_CAFETERIA`, `AC_RECEPTION` | Floor tints |
| `AC_NEIGH` (panel above the plan, shifted 53.268 m) | Neighbourhoods 01–06 and the two receptions, for the colour style and the hover |
| Partition layers in the fit-out block (`I-PART-*`, `OB-I-PART-*`, `A-WALL-EL3`, …) | Walls, 2.4 m |
| `S-COLS` in the base building | Columns |
| Furniture blocks and linework | Every closed outline becomes a desk top or table (0.75 m) or a chair (0.48 m). A seated figure or chair arcs next to a desk becomes a chair |
| `rytu`, `WS 1500x750mm`, `rhrt`, `4PAX WITH PLANTER` | Workstation count (651) |
| Plant blocks and plant layers | Shrubs in pots |

Heights are conceptual, not from the drawing: slab 0.3 m, partitions 2.4 m, cores 3.2 m, façade 3 m.

Coordinates are in metres from the same origin as `tools/testfit/extract.py`, so the axo lines up with the test-fit-02 plans.
