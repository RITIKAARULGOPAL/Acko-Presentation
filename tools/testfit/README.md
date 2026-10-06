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
| `A-FLOR` outline | Floor plate, the two south atria |
| Top panel (`thh` block), shifted onto the plan | Zones: 6 neighbourhoods and 2 receptions |
| Bottom panel (`gj` block), shifted onto the plan | Fire egress routes, measured in metres |
| `OB-I-ANNO-TEXT` labels | Rooms: quick sprints, huddles, departmental rooms, 2-pax rooms, booths (PB), zen rooms, cabins and more |
| Blocks `rytu` (3 desks), `WS 1500x750mm`, `rhrt`, `4PAX WITH PLANTER` (4 seats) | Workstations: 651, matching the counts written on the drawing |
| Microwave tags | Pantry points |

## Assumptions to revisit when the drawing changes

These are set for test fit 02 and live in the scripts:

- **Panel offsets** in `panels.py` (the top and bottom panels sit 53.3 m above and 55.3 m below the layout).
- **Zone order** in `extract.py` (`NB_ORDER`): the drawing's zones 4, 8, 7, 3, 2, 1 become N1 to N6 from west to east. Zones 5 and 6 are the receptions.
- **Town Square areas** in `extract.py`: the café and dining box (west) and the lobby box around the central cut-out are drawn by coordinates, since the drawing doesn't outline them.
- **Plate outline and atria** in `geo.py` (`PLATE`) and `extract.py` (`atria`).
- **Names, teams and colours** are placeholders in `tf_data.js` (`NBS`, `SHARED`).
- **Brief numbers** go in `BRIEF` in `tf_plan.js`. They show in the "Sharing out" table.
