# Acko · A city of neighbourhoods

An interactive, single-file presentation of the Acko workplace concept. It tells how a bare floor plate became six self-sustaining neighbourhoods around one shared Town Square.

> **Draft.** The floor plate, neighbourhood names, teams and every number are sample data. They stand in until the real drawings and area statement arrive.

## Open it

Double-click `index.html`. It runs in any modern browser (Chrome or Edge recommended for presenting) with no install and no server. It also works offline. Without internet the web fonts fall back to system fonts, and the final version will embed the fonts.

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

Presentation clickers work, since they send `PgUp` / `PgDn`. For self-browsing, the client can scroll or swipe through the same steps or jump with the progress bar. Each step has its own link (for example `index.html#town-square`).

## The story (11 chapters, 23 steps)

1. **The idea**: an office that works like a city (city → floor, Main Street → circulation, Town Square → shared amenities, neighbourhood → team zone, home → desk)
2. **Bare shell**: the floor plate draws itself in
3. **Site understanding**: light and orientation, then views, noise, arrival and the structural grid
4. **Due diligence**: numbered findings pinned to the plan
5. **Fire and egress**: exits with 15 / 30 / 45 m rings, then every escape route traced and measured
6. **Deriving the plan**: escape routes become Main Street and lanes, and the parcels left between them become six neighbourhoods plus the Town Square
7. **The layout**: the full fit-out, then the same layout carved into coloured neighbourhoods (hover for details, click to open)
8. **Town Square**: what is shared, highlighted on the plan
9. **Axonometric**: the plan tilts into 3D in the same colours, then explodes into shell, streets, neighbourhoods and fit-out
10. **Neighbourhoods**: an overview of all six, then **six deep dives**. Each shows plan and axo side by side, with a numbered kit (workstations, lead cabin, touchdown, focus pods, phone booths, meeting rooms, huddle, pantry, lockers, planter) and a self-sustaining checklist. Hovering a kit item lights it up in both views.
11. **By the numbers**: totals and the area split

All counts, areas, daylight percentages and route lengths are computed from the drawing, so they stay consistent when the layout changes.

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

**Content.**

- [ ] Acko colour palette, typefaces and logo, plus the Officebanao logo
- [ ] Location, floor, carpet area, headcount and seat count
- [ ] The concept note in your words
- [ ] Neighbourhood names, the team in each, and their colours
- [ ] Area statement: seats and area per neighbourhood, and a breakdown of the common area
- [ ] For **each** neighbourhood: every component with its count (workstations, cabins, meeting rooms and seats, phone booths, focus pods, huddle, pantry, lockers, print, planters, and anything else)
- [ ] Due-diligence findings and fire-planning notes as short bullets

## Where things live

Everything is in `index.html`:

- **Theme tokens** (brand, neutrals, neighbourhood colours) are at the top of the `<style>` block. Acko's palette goes there.
- **Project content** (`PROJECT`, `NBS`, `VARIANTS`, `DD`) is at the top of the `<script>` block.
- **Geometry** (plate, streets, stairs, routes and the furniture layout for each neighbourhood) follows it.
