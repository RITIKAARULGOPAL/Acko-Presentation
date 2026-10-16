# Plan hover: integration guide

An interactive floor plan for the Mitigata presentation: hover a **room** to highlight it, or hover a **workstation** to highlight its whole **team**. A label with the name and figures appears in the middle of the room or team. It covers both test-fit options (09.10.2026 DXFs), works offline, and has no dependencies.

**Try it first:** double-click `demo.html` (Chrome or Edge). Use Option 01 / 02, Day / Night, and hover anything.

---

## What's in the zip

| Path | What it is |
|---|---|
| `demo.html` | Stand-alone demo, double-click to open (works from `file://`) |
| `assets/js/plan-hover.js` | The component (vanilla JS, ~10 KB, no dependencies) |
| `assets/css/plan-hover.css` | Its styles. Every colour is a CSS variable; night theme included |
| `data/plan-hover-data.js` | Both options' plan, rooms and teams, generated from the DXFs (~3 MB). Don't hand-edit |
| `tools/plan_hover/` | The pipeline that rebuilds the data file from the DXFs |

The data file is a plain `<script>` (it sets `window.PLAN_HOVER`), so it loads from `file://` like the rest of the deck. No `fetch`, no server.

---

## Add it to the deck

### 1. Copy the files

Copy `assets/js/plan-hover.js`, `assets/css/plan-hover.css` and `data/plan-hover-data.js` into the same folders of `mitigata-presentation`. The folder names already match the deck's layout. Keep `tools/plan_hover/` next to the other tools.

### 2. Include them in `index.html`

```html
<link rel="stylesheet" href="assets/css/plan-hover.css">
<!-- before app.js -->
<script src="data/plan-hover-data.js"></script>
<script src="assets/js/plan-hover.js"></script>
```

### 3. Give it a container and mount it

The plan fills its container, so the container needs a size:

```html
<div id="plan-hover" style="position:absolute; inset:0"></div>
```

```js
const plan = PlanHover.mount(document.getElementById("plan-hover"), { option: "op1" });
```

Mount it when its chapter opens. If the container is hidden (`display:none`) at mount time, call `plan.fit()` once it becomes visible.

### 4. Hook it to the deck

- **Option keys `1` / `2`:** call `plan.setOption("op1")` / `plan.setOption("op2")`.
- **Day / Night:** nothing to do. The night colours apply automatically under `html[data-theme="dark"]`, which is what the deck's toggle sets.
- **Double-click to reset:** built in, matching the deck's other plans.

### API

```js
const plan = PlanHover.mount(element, {
  option: "op1",        // "op1" | "op2"
  rooms: true,          // room hovers
  teams: true,          // team hovers
  interactive: true,    // wheel zoom, drag pan, double-click to fit
  labels: true,         // centred name label on hover
  onHover: info => {},  // { kind: "room" | "team", item } on enter, null on leave
});

plan.setOption("op2");           // switch option
plan.fit();                      // whole floor
plan.zoomTo(x, y, w, h);         // plan coordinates (mm, SVG frame)
plan.teams();                    // [{ id, name, pax, seats, hot_desks, x, y }]
plan.rooms();                    // [{ id, name, m2, x, y }]
plan.destroy();
```

`onHover` lets the deck react to a hover, for example by showing a team's details in a side panel.

### Colours

Override any variable on `.ph-root` (or an ancestor) in the deck's CSS:

```css
#plan-hover { --ph-hover: rgba(255, 64, 64, .5); --ph-paper: transparent; }
```

The hover colour is coral red at 50% opacity (`--ph-hover`). The full list of variables is at the top of `plan-hover.css`.

---

## Rebuild the data when the drawings change

```bash
pip install -r tools/plan_hover/requirements.txt
python tools/plan_hover/build_plan_hover.py --op1 "Testfit OP1 - 09.10.26.dxf" --op2 "Test Fit op2 09.10.2026.dxf" --out data/plan-hover-data.js
```

It takes a few minutes. Add `--keep work` to keep the intermediate files: the full and instanced SVGs, `rooms.json`, `teams.json` and debug PNGs. `rooms_debug.png` shows every detected space with its id, which is useful for checking a new drawing.

For each option it runs four steps:
1. `recreate.py` writes the plan as SVG.
2. `rooms.py` builds the room outlines.
3. `teams.py` assigns seats to teams.
4. `rooms.py` runs again, so corridors are cut back around team furniture.

---

## Where the data comes from

### The plan

Every visible line, arc, hatch, wipeout and label from the DXF is kept. Curves stay true curves. Repeated blocks (chairs, desks, plants) are written once and reused, which keeps the file small.

Accuracy: every line is within **0.7 mm** of the DXF. Partition-type tags (`P1` on the gypsum partition blocks) and layers switched off in the DWG are left out.

### Rooms

- **From the drawing:** the `MI_*` room outlines in the 09.10 DXFs: meeting rooms, phone booths, boardroom, cafe, reception, podcast, collab areas, service rooms, AHUs, washrooms, lift lobby and corridors. Arcs in these outlines are kept as arcs.
- **Names:**
  - Most come from the layer: `MI_4PAX` becomes "Meeting room · 4 PAX", `MI_PB` becomes "Phone booth".
  - Service and collab areas use the label written in them: "Server Room / UPS & Battery Room", "Breakout Area", "Hotdesk".
- **Fallback:** rooms with no `MI_` outline come from the walls. In Option 02 that's the boardroom, cafe, 14-, 5- and 6-PAX rooms and the stores. Doors are closed using their swing arcs, and each enclosed area becomes a room named from the label inside it.
- **Corridors:**
  - The inner `MI_CORRIDOR` outlines are really the open-plan workspace around the teams, so they aren't rooms.
  - The outer corridor is cut back to its ring, and around team desks and chairs.
- **No overlaps:** spaces don't overlap, and smaller ones sit on top.

### Teams

- **Zones and labels:** each team has an `MI_*` zone (`MI_DELIVERY`, `MI_PRODUCT`, `MI_SALES`, `MI_SALES CALLING`, `MI_HR&FINANCE`, `MI_SOC`) and a "*TEAM n PAX*" label.
- **Hatched teams:** the hatches on each team's `MI_` layer are the designer's allocation. A team's seats are everything its hatch covers:
  - chairs at desks and pod chairs
  - stools, and blocks named with a headcount ("4PAX WITH PLANTER" = 4)
  - chairs drawn as loose lines (an exploded chair block, or chairs drawn inside a table block)
  - a hatched bench with no chairs drawn: one seat per 1.05 m of length, both sides if 1 m or more deep
- **Hot desks:** seats a hatch claims that aren't a standard desk or pod chair are counted as hot desks.
- **The SOC (no hatch):**
  - Its seats are the SOC chairs in its zone, plus the nearest same-type chairs up to its PAX, never from another team's zone.
  - It highlights as a room: the zone plus its seats.

**Counts (seats / PAX):**

| Team | Option 01 | Option 02 |
|---|---|---|
| SOC | 80 / 80 | 78 / 80 |
| Delivery | 71 / 71 | 70 / 70 |
| Product | 50 / 50 | 57 / 57 |
| Sales | 41 / 41 | 41 / 41 |
| Sales Calling | 37 / 37 | 31 / 31 |
| HR, Finance | 20 / 20 | 22 / 22 |

Option 02's SOC has 78 SOC seats drawn.

---

## Notes for the CAD layer spec

`CAD-LAYER-SPEC.md` asks for `MX-PROG-*` layers. The CAD team delivered the same information as `MI_*` layers, which this pipeline reads:

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
| `MI_SOC`, team zones | `MX-PROG-SOC`, `MX-PROG-WORK` |

To make the next revision cleaner, the CAD team could:
- Draw corridors as corridors only. The inner `MI_CORRIDOR` outlines currently cover the workspace.
- Give the SOC a team hatch, like the other teams.
- Add `MI_` outlines for Option 02's boardroom, cafe and wing rooms.
- Move block `fgbg` (a table with chairs) off the glass-door layer `I_DOR_OP_IN_GL`. The spec already lists this.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Blank plan | Check the container has a size. Make sure `plan-hover-data.js` loads before `plan-hover.js`. |
| Plan squashed after a chapter becomes visible | Call `plan.fit()` once the container is shown. |
| Hover doesn't react | Another element is on top of the plan: give it `pointer-events: none`. |
| Lines look too heavy or light | Adjust the `stroke-width` rules in `plan-hover.css`. They are screen pixels, constant at any zoom. |
