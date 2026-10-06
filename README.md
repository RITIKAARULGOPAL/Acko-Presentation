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
