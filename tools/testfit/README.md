# Test-fit pipeline

Turns the test-fit DXF into `index-testfit.html`. Every plan, count, area and route in that file comes from the drawing.

```bash
pip install ezdxf shapely
tools/testfit/run.sh ~/Downloads/ACKO_Testfit_02_5.10.26.dxf
```

It takes a few minutes for the 160 MB file. The DXF itself is not stored in the repo.

## What it reads

| From the drawing | Used for |
|---|---|
| Middle panel (`base` block and fit-out layers) | Plan, cores, columns, stairs, partitions, furniture |
| `A-FLOR` outline | Floor plate, the two south terraces |
| Top panel (`thh` block), shifted onto the plan | Zones: 6 neighbourhoods and 2 receptions |
| Bottom panel (`gj` block), shifted onto the plan | Fire egress routes, measured in metres |
| `OB-I-ANNO-TEXT` labels | Rooms: quick sprints, huddles, departmental rooms, 2-pax rooms, booths (PB), zen rooms, cabins and more |
| Blocks `rytu` (3 desks), `WS 1500x750mm`, `rhrt`, `4PAX WITH PLANTER` (4 seats) | Workstations: 651, matching the counts written on the drawing |
| Microwave tags | Pantry points |
| Lift shaft and lift door blocks inside `base` | The two lift lobbies (7 passenger lifts each), the arrival points |

## Assumptions to revisit when the drawing changes

These are set for test fit 02 and live in the scripts:

- **Panel offsets** in `panels.py` (the top and bottom panels sit 53.3 m above and 55.3 m below the layout).
- **Zone order** in `extract.py` (`NB_ORDER`): the drawing's zones 4, 8, 7, 3, 2, 1 become Neighbourhood 01 to 06 (ids `N01`–`N06`) from west to east. Zones 5 and 6 are the receptions, part of the shared spaces.
- **Shared spaces** in `extract.py`: the café and dining box (west) and the lobby box by the lifts are drawn by coordinates, since the drawing doesn't outline them.
- **Plate outline and terraces** in `geo.py` (`PLATE`) and `extract.py` (`terraces`).
- **Teams and colours** are placeholders in `tf_data.js` (`NBS`). Neighbourhood names are numbers (Neighbourhood 01 to 06).
- **Brief numbers** go in `BRIEF` in `tf_plan.js`. They show in the "Sharing out" table.

## Site analysis

`run.sh` also runs `tools/site/site.py build`. That step takes the committed site data in `tools/site/context.json` (map, wind, climate) and `tools/site/facts.json` (due diligence and areas). It places the plan on the site and works out the sun on the layout, writing `site.json`. `build_tf.py` then splices `site.json` and `tf_site.js` into the page.

- **North** is found again on every build. The plate is fitted into the footprint both ways round, and the way that puts the slanted end beside Hosur Road wins. `run.sh` prints the result.
- **Sun patches**: for 3 dates × 24 half-hours, each façade is sampled every 0.5 m. Glass shaded by the floor's own recesses is skipped. The light is traced inwards to 3.25 m ÷ tan(sun altitude), stopping at core walls.
- **Refreshing the open data**: `python3 tools/site/fetch.py` (needs `pip install pyarrow` and network access to the Overture and NOAA S3 buckets), then `python3 tools/site/site.py prep`.

## AC_ layers (layout tf03 onwards)

When the drawing has the `AC_` layers, they take over from the guesses above:

| Layer | Used for |
|---|---|
| `AC_GLAZING` | The floor plate. The terraces are its notches on the south side. |
| `AC_NEIGH` (top panel), `AC_FIRE_EXIT` (bottom panel) | The 8 zones (Neighbourhood 01–06, 2 receptions) and the egress routes. Read by `ac_panels.py`. |
| `AC_WS_TYPE01`–`04` | Workstation blocks. They are still counted by block name, which gives 651 seats. |
| `AC_QUICK_SPIRIT`, `AC_COLLAB_HUDDLE`, `AC_DEPARTMENTAL_ROOMS`, `AC_BOARD_ROOM`, `AC_THE_HATCHERY`, `AC_VISITOR_HUB`, `AC_TRAINING_ROOM`, `AC_THE_STUDIO_ROOM`, `AC_EXECUTIVE_CORNER_CABIN`, `AC_PHONE_BOOTH`, `AC_ZEN_ROOM`, `AC_PRAYER_ROOM`, `AC_MOTHER'S_ROOM`, `AC_HUB_ROOM`, `AC_UPS_SERVER_BATTERY_BMS_ROOM` | Rooms with exact outlines. Name and seats come from the room label inside each. |
| `AC_COLLAB` | The Acker Garden · Work Arena spaces (renders `garden`). |
| `AC_COFFEE_CORNER` | Coffee corners. They replace the microwave-based pantry points. |
| `AC_CAFETERIA`, `AC_LIFT_LOBBY` (east) | The café and the lobby among the shared spaces. |
| `AC_WORKHALL`, `AC_CORRIDOR`, `AC_RECEPTION`, `AC_OUT_OF_SCOPE`, … | The space plan: area per category, each m² counted once. |
| `AC_LIFT_LOBBY` 1, `AC_WASHROOM` 2, `AC_FIRE_EXIT_STAIRCASE` 3, `AC_AHU` 4, `AC_STRENGTHEN_SLAB` 5 (numbered marker circles), `AC_ENTRY`, `AC_OUT_OF_SCOPE`, `AC_FIRE_COMPARTMENTALISATION` | The due-diligence step, numbered as on the drawing. |
