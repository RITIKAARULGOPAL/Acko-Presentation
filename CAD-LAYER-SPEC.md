# CAD layer spec: Mitigata interactive presentation

**For:** SKV CAD team  
**Files:** `Mitigata OP1.dxf` and `Mitigata OP2.dxf` (2D, DXF R2018, units mm)

The interactive presentation is built directly from the test-fit DXFs.

**What already works:** walls, glass, furniture and room labels come out of the current files automatically.

**What these layers fix:** zones, events, routes and camera points are currently traced by hand from the deck plans, accurate to about ±0.3 m. With these layers they become exact, and stay correct whenever the plan changes.

## Before adding layers

1. **Same base point in both files.** Move both drawings so the main-entrance door corner is at 0,0.
   - Today OP1 sits around (−391 000, −566 000) and OP2 around (0, −99 000).
   - The presentation re-aligns them on the shell block for now, so this matters most for future revisions.
2. **Explode the base-building block `zw$DF8`**, so walls, columns and the core sit on their own layers. Then PURGE.
3. **Delete junk layers.** Examples: `WWW.DWGAUTOCAD.COM`, unused `OB-*` and `I_*` layers.
4. **Fix mislabelled furniture.** In OP2, block `fgbg` (workstations) sits on the glass-door layer `I_DOR_OP_IN_GL`. Move it to a furniture layer.

## Layers to add (identical names in OP1 and OP2)

| Layer | Geometry | What it drives |
|---|---|---|
| `MX-FLOOR` | 1 closed polyline | Floor-plate outline and area |
| `MX-PROG-SOC` | closed polylines | SOC zone |
| `MX-PROG-WORK` | closed polylines | Workhalls |
| `MX-PROG-MEET` | closed polylines | Meeting rooms (one per room is ideal) |
| `MX-PROG-BOARD` | closed polyline | Boardroom |
| `MX-PROG-ARRIVE` | closed polylines | Reception + waiting lounge |
| `MX-PROG-COLLAB` | closed polylines | Breakout / agile / hot-desk |
| `MX-PROG-CAFE` | closed polylines | Café / pantry |
| `MX-PROG-STUDIO` | closed polyline | Podcast studio |
| `MX-PROG-QUIET` | closed polylines | Phone booths, nap room |
| `MX-PROG-SERVICE` | closed polylines | Stores, prep counter, dine store |
| `MX-PROG-SECURE` | closed polylines | Server, UPS & battery |
| `MX-PROG-CORE` | closed polylines | Lifts, stair, toilets, AHU, electrical |
| `MX-EVT-50` / `MX-EVT-100` / `MX-EVT-200` | 1 closed polyline each | Event footprints. Area and seat capacities are calculated from these |
| `MX-WALL-OPERABLE` | open polylines | Folding / operable walls, drawn in the closed position |
| `MX-GLASS-SOC` | open polyline | The SOC viewing glass |
| `MX-PATH-VISITOR` | open polyline | Main entrance → reception → boardroom |
| `MX-PATH-TOUR` | open polyline | Optional SOC tour route |
| `MX-PATH-SERVICE` | open polyline | Pantry → event zones (F&B) |
| `MX-CAM-RECEPTION`, `MX-CAM-SOC`, `MX-CAM-BOARDROOM`, `MX-CAM-BREAKOUT`, `MX-CAM-MEETING6` | 1 LINE each, from the eye point toward the view | Render viewpoints for the keyplans |
| `MX-SIG-ARRIVAL`, `MX-SIG-WATCHWALL`, `MX-SIG-LANTERN`, `MX-SIG-COMMONS`, `MX-SIG-ONAIR` | POINT or CIRCLE | Signature-moment markers |

**Rules:**
- Closed polylines must really be closed (the Closed property, or end point = start point).
- Polygons of one type may touch but shouldn't overlap.
- Security tiers (guest / team / secure) are derived from the `MX-PROG-*` type, so no separate layer is needed.

## Also useful

Send a small **heights table** (a text note is fine). It replaces the defaults used for the 3D extrusion:
- full-height partitions
- glass partitions
- false ceiling heights by zone
- the SOC raised floor (+200 mm is noted in OP1)
- the SOC and boardroom ceiling features

## How it's used

Ask Claude, or run:

```bash
python tools/rebuild.py --op1 "Mitigata OP1.dxf" --op2 "Mitigata OP2.dxf" --deck "01.10.2026_MITIGATA_DESIGN PROPOSAL.pptx" --mx
```

**Fallback:** any layer that's missing keeps its provisional traced version, and the script prints which ones.

## Update 10.10.2026: what the CAD team delivered

The 09.10 test fits carry the same information on `MI_*` layers instead of `MX-PROG-*`. The presentation now reads them through `tools/plan_hover/` and `tools/import_plan_hover.py`:

| Delivered (`MI_`) | Spec (`MX-`) |
|---|---|
| `MI_4PAX`, `MI-6PAX`, `MI_8 PAX`, `MI_10 PAX`, `MI_2 PAX` | `MX-PROG-MEET` |
| `MI_BOARDROOM` | `MX-PROG-BOARD` |
| `MI_RECEPTION` | `MX-PROG-ARRIVE` |
| `MI_COLLAB` | `MX-PROG-COLLAB` |
| `MI_CAFE` | `MX-PROG-CAFE` |
| `MI_PODCAST` | `MX-PROG-STUDIO` |
| `MI_PB` | `MX-PROG-QUIET` |
| `MI_SERVICE` | `MX-PROG-SERVICE` / `MX-PROG-SECURE` |
| `MI_AHU`, `MI_LIFT_LOBBY`, `MI_WASHROOM` | `MX-PROG-CORE` |
| `MI_SOC`, team zones (`MI_DELIVERY`, `MI_PRODUCT`, …) | `MX-PROG-SOC`, `MX-PROG-WORK` |

**For the next revision:**
- Draw corridors as corridors only. The inner `MI_CORRIDOR` outlines currently cover the open workspace.
- Give the SOC a team hatch, like the other teams.
- Add `MI_` outlines for Option 02's boardroom, café and wing rooms.
- Add an outline for Option 01's 4-pax meeting room that has none, and move P.B 06 / 08 / 09 off `MI_SERVICE`.
- Move the curved SOC glass screen (Opt 01) off the door layer. The table-with-chairs block `fgbg` (Opt 02) is drawn on a glass layer. The importer works around both, but the layers should be fixed.
- Events, routes, render viewpoints and signature spots are still placed by hand. `MX-EVT-*`, `MX-PATH-*`, `MX-CAM-*` and `MX-SIG-*` would still help.
