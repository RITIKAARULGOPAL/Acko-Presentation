# Acko · A city of neighbourhoods

An interactive, single-file presentation of the Acko workplace concept. It tells how a bare floor plate became six self-sustaining neighbourhoods around one shared Town Square.

> **Draft.** The floor plate, neighbourhood names, teams and every number are sample data. They stand in until the real drawings and area statement arrive.

## Open it

Double-click `index.html`. The earlier version of the story (23 steps: escape routes become Main Street, without the brief, the loop or the shared zen rooms) is kept as `index-v1.html` and works the same way.

**`index-testfit.html` is built on the real test fit** (ACKO_Testfit_02_5.10.26): the floor, cores, stairs, partitions, furniture, rooms, workstations, egress routes and zones are all read from that DXF. See [Test fit](#test-fit) below.

All three run in any modern browser (Chrome or Edge recommended for presenting) with no install and no server, and work offline. Without internet the web fonts fall back to system fonts, and the final version will embed the fonts.

## Present it

| Key | Action |
|---|---|
| `→` `Space` `PgDn` | Next step |
| `←` `PgUp` | Previous step |
| `Home` / `End` | First / last step |
| `F` | Fullscreen |
| `T` | Light / dark |
| `B` | Blank the screen (any key returns) |
| `?` | Shortcuts |

**In the render viewer**

| Key | Action |
|---|---|
| `→` `←` (or the clicker) | Next / previous space. Stepping past the last space closes the viewer |
| `L` `C` `D` | Light, compare, dark |
| `Esc` | Close |

Presentation clickers work, since they send `PgUp` / `PgDn`. For self-browsing, the client can scroll or swipe through the same steps or jump with the progress bar. Each step has its own link (for example `index.html#town-square`).

## The story (14 chapters, 29 steps)

1. **The idea**: an office that works like a city (city → floor, the loop → circulation, Town Square → shared amenities, neighbourhood → team zone, home → desk). Then **the loop**, taken from Acko's logo: a ring stretches into one endless corridor around the core, with the Town Square inside and the neighbourhoods outside
2. **The brief**: six neighbourhoods and one floor-wide total for every space type, grouped by how each was shared out
3. **Bare shell**: the floor plate draws itself in
4. **Site understanding**: light and orientation, then views, noise, arrival and the structural grid
5. **Due diligence**: numbered findings pinned to the plan
6. **Fire and egress**: exits with 15 / 30 / 45 m rings, then every escape route traced and measured
7. **Deriving the plan**: the escape corridors join at both ends and close into the loop (no dead ends, two ways to every stair), and the parcels left between the loop and the lanes become six neighbourhoods plus the Town Square
8. **Sharing out the brief**: one table, two steps. First every total is divided by six, with the leftovers set aside. Then the leftovers go to the neighbourhoods that had room, and the three zen rooms become one per pair of neighbours facing each other across the loop
9. **The layout**: the full fit-out, then the same layout carved into coloured neighbourhoods (hover for details, click to open), then the three shared zen rooms with links to the pair that shares each one
10. **Brief vs plan**: the same table showing what the plan achieved. Shortfalls are marked in red, with the reason for each
11. **Town Square**: what is shared, highlighted on the plan
12. **Axonometric**: the plan tilts into 3D in the same colours, then explodes into shell, loop and lanes, neighbourhoods and fit-out
13. **Neighbourhoods**: an overview of all six, then **six deep dives**. Each shows plan and axo side by side, its share of the brief (with extras and shortfalls), a numbered kit (workstations, lead cabin, touchdown, focus pods, phone booths, meeting rooms, huddle, pantry, lockers, planter, shared zen room) and a self-sustaining checklist. Hovering a kit item lights it up in both views.
14. **By the numbers**: totals and the area split

All counts, areas, daylight percentages, route lengths, the loop length and the brief comparison are computed from the drawing, so they stay consistent when the layout changes.

### How the brief is shared out

Each entry in `BRIEF` has a `rule`:

- `split`: the total is divided by six. The remainder goes to the neighbourhoods listed in `extra` (for example `extra:{N2:1, N4:1}`).
- `shared`: fewer than six are asked for, so each pair in `PAIRS` shares one (zen rooms: 3 for 6).
- `square`: one for everyone, in the Town Square.

Add `why` to any entry the plan can't meet. The "Brief vs plan" step compares the plan's counts with each neighbourhood's share and lists every shortfall with its reason.

## Renders on click

Click any space to open its renders. This works in the layout steps, the Town Square step, both 3D views, and every neighbourhood deep dive (plan, axo, numbered markers and kit rows with a camera icon). Each space has two renders, **light** and **dark**:

- **Light / Compare / Dark** toggle at the top right
- **Slider**: drag across the image, or use the bar below it, to wipe between the two versions
- **Filmstrip** of the other spaces in the same neighbourhood (or the Town Square), with ‹ › arrows on the image

Until the real renders arrive, every space shows a generated sample interior in the neighbourhood's colour, marked "Sample visual".

**Adding the real renders.** Put the images in a `renders/` folder next to `index.html` and list them in `RENDERS` at the top of the RENDERS section of the script:

```js
const RENDERS={
  meeting:{light:'renders/meeting-light.jpg', dark:'renders/meeting-dark.jpg'},
  huddle:{light:'renders/huddle-light.jpg', dark:'renders/huddle-dark.jpg'},
  'N1:huddle':{light:'renders/n1-huddle-light.jpg', dark:'renders/n1-huddle-dark.jpg'}, // only Indiranagar
};
```

A shared entry (`meeting`) is used by every neighbourhood. A neighbourhood-specific entry (`N1:meeting`) wins over it. Space keys: `desk` (workstations), `cabin`, `touch` (touchdown bench), `focus`, `booth`, `meeting`, `huddle`, `pantry`, the shared `zen` room, plus the Town Square's `reception`, `townhall`, `board` and `cafe`.

Render both versions of a space **from the same camera, at the same size**, so the slider lines up. JPG about 2400 px wide works well, in 16:10 or 16:9.

## What we need to replace the sample data

**Drawings.** Export everything from the same CAD file at the same scale, crop and sheet size. Vector (PDF or SVG) is best; otherwise PNG at least 3000 px wide.

- [ ] Bare shell plan
- [ ] Fire escape plan: exits, stairs, travel distances, routes
- [ ] Final furniture layout
- [ ] Neighbourhood and common-area demarcation (a rough colour mark-up is fine)
- [ ] Axo render of the full floor, plus the same camera with each neighbourhood highlighted (or a colour-ID / mask pass)
- [ ] Axo close-up of **each of the six neighbourhoods** (isolated or exploded is ideal)
- [ ] Site understanding and due-diligence mark-ups, or just bullet points
- [ ] Site photos for the due-diligence pins (optional)
- [ ] **Light and dark render of each space type**, same camera for both: workstations, lead cabin, touchdown, focus pod, phone booth, meeting room, huddle, pantry, zen room, reception, town hall, boardroom, café. Add per-neighbourhood versions wherever a neighbourhood looks different

**Content.**

- [ ] Acko colour palette, typefaces and logo, plus the Officebanao logo
- [ ] Location, floor, carpet area, headcount and seat count
- [ ] **The brief**: every space type Acko asked for with its total, how it was shared out (÷ 6, 1 per 2, or Town Square), which neighbourhoods got the extras, and the reason for any count the plan can't meet
- [ ] The concept note in your words
- [ ] Neighbourhood names, the team in each, and their colours
- [ ] Area statement: seats and area per neighbourhood, and a breakdown of the common area
- [ ] For **each** neighbourhood: every component with its count (workstations, cabins, meeting rooms and seats, phone booths, focus pods, huddle, pantry, lockers, print, planters, and anything else)
- [ ] Due-diligence findings and fire-planning notes as short bullets

## Where things live

Everything is in `index.html`:

- **Theme tokens** (brand, neutrals, neighbourhood colours) are at the top of the `<style>` block. Acko's palette goes there.
- **Project content** (`PROJECT`, `NBS`, `BRIEF`, `PAIRS`, `DD`) is at the top of the `<script>` block.
- **Geometry** (plate, loop and lanes, stairs, routes, zen rooms and the furniture layout for each neighbourhood) follows it.

## Test fit

`index-testfit.html` tells the story on the real floor from test fit 03 (`acko-layout-tf03.dxf`): the 3rd floor of Regalium, Koramangala, a 245 × 34 m plate (7,606 m²) with five fire stairs along the north cores and two terraces on the south façade. Neighbourhoods are numbered Neighbourhood 01 to 06 from west to east, and what everyone uses is called the shared spaces. It has 40 steps:

1. **The idea**: the city analogy and the loop (schematic)
2. **The site**: a map of Regalium on Hosur Road, with landmarks, walking distances and the metro. It then zooms to the block and turns until the floor lines up with the drawing. The floor sits 11.5° east of true north (see below)
3. **The floor**: outline, cores, columns, stairs and terraces, with dimensions and the real façade orientations. Then the **due diligence** from the site visit: lift lobbies and entrances, slab and beam heights (with a section), glazing, screed, structure, the five exits, and super built-up, carpet and headcount
4. **Sun and climate**:
   - the sun path over the floor, with hours of sun on each façade
   - **morning to evening on the layout**, an animated day (21 Mar/Sep, 21 Jun, 21 Dec) showing the sun patches on the furniture plan, with what it means for each neighbourhood
5. **Daylight**: the 6 m band along the façade, including the glass facing the terraces (45% of workstations sit in it)
6. **Fire and egress**: five stairs with 15 / 30 / 45 m rings, then the eight egress routes from the drawing, measured (43 to 61 m)
7. **Carving the floor**: Neighbourhood 01 to 06 plus the shared spaces (café and dining, two receptions, lobby)
8. **The layout**: the full fit-out; the **space plan**, with every space from the drawing's `AC_` layers coloured by type and measured; then carved into neighbourhoods (hover for details, click to open)
9. **Shared spaces**: café and dining, both receptions and the lobby, highlighted
10. **Sharing out**: every space type counted per neighbourhood, with a Brief column waiting for Acko's numbers
11. **Axonometric**: the drawing in 3D. Then the **conceptual axo**: exploded into shell and core, neighbourhoods with the loop, and fit-out; rendered stills (whole floor, west, middle, east; reference colours or neighbourhood colours), then the same model live in 3D to orbit, zoom and hover
12. **Neighbourhoods**: an overview and six deep dives with plan, axo, numbered kit and walking distances
13. **Green zones**: a carbon-responsive green zone analyzer on the real layout (10 steps, see [Green zones](#green-zones) below)
14. **By the numbers**: 651 workstations, 48 meeting and collaboration rooms, 58 phone booths and 2-pax rooms, area split

Click any desk cluster, room, pantry or shared area for its light and dark renders. For the test fit, drop the images into `renders/` named `<key>-light` and `<key>-dark` (`.jpg`, `.png` or `.webp`). The build embeds them in `index-testfit.html`, so it stays one self-contained file. Real renders so far: the reception (`renders/reception-*.webp`) and the Acker Garden · Work Arena (`renders/garden-*.webp`). The garden isn't labelled in the drawing; it is placed at the curved north-west corner of Neighbourhood 01, by its coffee point, in `PLACES` in `tools/testfit/tf_data.js`. The keys are: `garden`, `desk`, `sprint`, `dept`, `huddle`, `hatchery`, `duo`, `booth`, `pantry`, `zen`, `cabin`, `board`, `studio`, `prayer`, `mother`, `cafe`, `reception`, `lobby`, `visitor`. A render for one neighbourhood only uses its two-digit id: `'N03:huddle':{light:'renders/n03-huddle-light.jpg', dark:'renders/n03-huddle-dark.jpg'}`.

### Green zones

The Green zones chapter works out **where planting should go and why**, from how each space is used. It does not spread plants evenly by area. *Planting is not decoration: it is spatial infrastructure responding to how people use the workplace.*

Layout → space classification → occupancy → footfall → dwell time → relative carbon impact → biophilic priority → green zone identification → plant quantity → plant type → placement → green score.

1. **The idea**: the philosophy and the workflow, over the final proposal
2. **Spaces**: the 167 spaces from the drawing's `AC_` layers, each a record (type, category, area, occupancy, dwell, visits, footfall, daylight, circulation, privacy, existing planting). Click one to see it or override its numbers
3. **Footfall**: occupancy × visits per person per day × utilisation
4. **Dwell**: footfall × average dwell gives occupancy hours. This separates high-footfall/short-dwell (reception), high/high (café) and low-movement/long-dwell (work arenas)
5. **Carbon index**: footfall × dwell × activity factor × services intensity, scaled 0–100 across the floor. **It is a relative design-planning index, not measured emissions or a carbon offset**, and every surface that shows it says so
6. **Priority**: 25% footfall, 25% dwell, 20% carbon index, 15% daylight, 10% social importance, 5% visibility, scaled 0–100 and classed Very Low to Very High
7. **Green zones**: the proposal on the plan, as Green Node, Island, Edge, Threshold, Pocket and Feature. Click a zone for its card (footfall, dwell, carbon index, priority, type, plants, mix, planter length, height, density, light, maintenance and the reason). Drag to move, **+ Add zone** to place one, and delete, retype or resize from the card. A zone moved into the keep-clear zone is flagged and costs score
8. **Dashboard**: floor summary, the green zone table, plant mix and 5–10 generated design recommendations, with CSV and JSON export
9. **Space database**: the full table, highest priority first
10. **Assumptions**: every default by space type (visits, utilisation, dwell, activity, services intensity, social importance), the priority weights, density (1 plant per 12.5 m²), class multipliers (0.75 / 1.0 / 1.2 / 1.4, and 0.5 for very low) and plant spacing. Edits recompute everything, stay in the browser, and export or import as JSON

The toolbar switches layers at any step (Spaces · Footfall · Dwell · Carbon index · Priority · Green zones) and overlays the keep-clear zone, the free floor, the escape routes and the existing plants.

**From the drawing:** space outlines and types, 651 workstations and 544 room and café seats, 228 existing plants, doors, partitions (glass counts as see-through for visibility), escape routes, cores, columns, and the drawing's "1500MM WIDE CORRIDOR" note, which sets the clear width. **Estimates, labelled `est.`:** visits, utilisation, dwell and activity factors, and the users of coffee corners, receptions, lobbies and the corridor (from the headcount). Nothing is presented as a measured occupancy or carbon figure.

**Nothing is planted** on furniture and its 0.6 m use zone, 1.2 m in front of doors, escape routes ± 1.0 m, corridor width below 1.5 m clear + 0.6 m planter, junction sight lines (1.5 m), lifts, stairs and entrances (1.5 m), columns, cores, or support rooms. That leaves 358 m² of the 5,434 m² usable floor, cut into 164 candidate spots. The selection then **maximises impact, not plant count**. It ranks spots by their space's priority, visibility, daylight and footfall, keeps zones apart (3 m, 6 m within one space), and puts the work-arena remainder on desks. The **biophilic workplace score** is 40% priority spaces served, 30% desks within 8 m of greenery, 15% zone visibility and 15% plants in daylight, minus clearance conflicts. So a few well-placed plants outscore many scattered ones.

**Conceptual axo (test fit 03).** The exploded step and the two axo steps after it come from `acko-layout-tf03.dxf`, like the rest of the deck, through their own pipeline in `tools/axo/`. Rooms, cores, corridors and zones come from its `AC_*` outline layers, and desks, chairs, tables and plants from the fit-out blocks. The stills are `renders/axo-<view>-<style>.webp` and `renders/axo-exploded-layers.webp`, whose label positions are in `renders/axo-exploded-layers.json`. To rebuild them or the model, see `tools/axo/README.md`.

**Still placeholders in the test fit:** teams and colours; the brief numbers; the loop (the drawing has no loop line yet). The fire travel distances still need checking against NBC with the fire consultant.

### Site analysis: sources and assumptions

- **Location:** plus code 7J4VWJJ7+CQW (12.9311° N, 77.6145° E).
- **North:** the drawing has no north point, so the floor plate is fitted into Regalium's footprint (Wings A–C in OpenStreetMap). Of the two ways round, only one puts the plate's slanted end beside Hosur Road. That gives a plan-up bearing of 11.5°: the cores face north and the terraces face south. Worth checking with a compass on site.
- **Map:** buildings, roads, landmarks and bus stops come from Overture Maps (release 2026-09-23.1, OpenStreetMap data, ODbL). Walking distances follow the road network from the site gate.
- **Sun:** NOAA solar-position formulas and the ASHRAE clear-sky model. Glazing is full height to 3.25 m (the beam bottom from the due diligence). The floor's own recesses and cores cast shade; neighbours and fins are not modelled.
- **Wind:** NOAA ISD 3-hourly observations at IMD Bangalore (WMO 43295), 2014–2025.
- **Rain and temperature:** NOAA GHCN-daily, Bangalore, 1991–2020 averages.
- **Due diligence:** typed into `tools/site/facts.json` from the site-visit report: heights, glazing, screed, structure, exits, entrance, super built-up 91,000 sq ft, carpet 56,650 sq ft, about 640 headcount. Edit that file and rebuild if anything changes.

To refresh the open data, run `python3 tools/site/fetch.py && python3 tools/site/site.py prep`. Download the raw data first; it is about 25 MB and is not committed. Then rebuild as usual.

To rebuild after the drawing changes, run `tools/testfit/run.sh` on the new DXF (see `tools/testfit/README.md`).
