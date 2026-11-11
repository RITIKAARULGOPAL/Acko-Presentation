# ACKO "The Loop" pitch deck — hand-off

This file lets another Claude session continue the deck work without the original chat. Read it all before changing anything.

> **Update (11 Nov, merged from the "Plan content preview" session into `claude/new-changes`):**
> - **Generator:** `index-approach.html` is now built in-repo by `python tools/acko/story/gen_story.py .`.
> - **Order:** the brand-first order (01 The Loop · 02 Belonging · 03 The Site · 04 The Plan · 05 The Palette · 06 The Experience), opening on ACKO's Möbius in `slides/s-open.html`.
> - **Opening options:** `index-open.html` and `index-unfold.html` (`gen_open.py`, `gen_unfold.py`; `PICK` sets the opening).
> - **The old generators:** `handoff/wow/` keeps the generators of the earlier problem-first order, for reference. Their wow patches are already committed in the slide files.
> - **Paths below:** they describe the deck-wow worktree as it was. In this branch the files are at the repo root.

---

## 1 · The project

- **What it is.** An HTML pitch deck for **ACKO's new office** (one floor at Regalium, Koramangala, Bengaluru, about 640 people).
  - It's presented by **SKV / Studiokon** in a slot of about 20 minutes.
  - The big idea is **"The Loop"**: a campus-like circulation route with seven stops (Arrival → Café → Board Room → Meeting Rooms → Collab → Work → Wellness). It's drawn from ACKO's Möbius logo.
- **Who you're working with.** **Ritika**, the designer.
  - She reviews everything in the in-app browser preview and points at slides with screenshots.
  - She iterates fast, in short messages ("there's a gap", "too cluttered", "show in preview").
- **Two decks live in one checkout:**
  - **`index.html`**: the **live deck**, built from `slides/order.txt` by `python tools/build.py`. It has **45 slides** now. Its behaviour must not change unless Ritika asks; the one time she did was "Both decks" for the 3 Nov proposal.
  - **`index-approach.html`**: the **re-ordered deck**, with the "wow" moments and the problem-first narrative. It has **45 slides**, since the walk slide was removed. It's built by `handoff/wow/gen_approach.py`, which sets `window.ACKO_WOW = true` and `window.ACKO_SECTIONS`. All wow behaviour is guarded by `ACKO_WOW`, so the live deck never runs it.

## 2 · Where things are

| What | Where |
|---|---|
| Repo root (main checkout) | `C:\Users\Ritika\Acko 1610` |
| **Current work** (worktree, branch **`deck/wow`**) | `C:\Users\Ritika\Acko 1610\.claude\worktrees\deck-wow` |
| Earlier re-order (branch `deck/reordered`, commit 8be4cc5) | `C:\Users\Ritika\Acko 1610\.claude\worktrees\plan-content-920e251` (preview port 8771) |
| The generators for the re-ordered deck (copied out of the old session's scratchpad) | `C:\Users\Ritika\Acko 1610\.claude\worktrees\eager-lumiere-ebac53\handoff\wow\` |
| The 3 Nov design proposal (source of renders, palette, materials) | `C:\Users\Ritika\Downloads\Copy of 03.11.26 _ ACKO_Design Proposal.pdf` (32 pages) |
| Notes per change (long, dated) | `deck-wow\README.md` (bottom sections, 9–10 Nov) |

- **Commits on `deck/wow`:** `3e3663b` "Big moments and a problem-first narrative" sits on `8be4cc5`. **Everything after that is uncommitted** (see §7).
- **Preview:** `python "<deck-wow>/tools/serve.py"` on **port 8791**. The launch config is called `the-loop-wow`.
  - Open `http://localhost:8791/index-approach.html#<slide-id>/<beat>`, for example `#s-layout-dd/1`.
  - The live deck is `http://localhost:8791/index.html`.

## 3 · How the deck engine works (enough to edit it safely)

- **Slides:** each slide is `slides/<id>.html`. It contains a `<section class="scene" id="…" data-part data-title data-steps data-beats data-mins data-notes>`, its own `<style>`, and `ACKO.slide(id, kit => ({ enter(_, sc), step(k, sc), leave(_, sc) }))`.
  - Only the part between `<!-- slide:start -->` and `<!-- slide:end -->` goes into the build.
  - `go()` calls the old slide's `leave()` **before** the new slide's `enter()`.
  - Beats use `data-step="n"` / `data-only` elements, or the slide's own `step(k)`.
- **The build:** `tools/build.py` exposes `build.build(ids, out)`. Always run `python tools/build.py` after building another page.
- **The kit** (`assets/js/app.js`): `$`, `$$`, `plain`, `reveal`, `later`, `countUp`, `world("map"|"plan"|"photo"|"none")`, `shade`, `reduced`, `cue(name)`.
  - `cue(name)` plays WebAudio sounds; they're on only with `ACKO_WOW`, and Shift+S mutes them.
  - `kit.plan` is the floor plan: `deckPlan`, `planOn`, `planOff`, `planView`, `vbFor`, `focusZone`, `planBare`, `layers`, `keyplan`…
  - In the browser, `ACKO.kit.plan.planBare(...)` works too.
- **Hand-offs between slides:** `window.ACKO_MORPH` is defined in `slides/s-challenges.html`.
  - `mark(id, data)` is called in the outgoing slide's `leave`, and `take(id)` in the next slide's `enter`. A mark is valid for 1.5 s.
  - Temporary transition layers are inserted **first in `#stage`**, so they sit under both slides during the 0.7 s cross-fade.
- **The floor plan:** `PlanCanvas` (`assets/js/plan-canvas.js`) draws `PLAN_BASE`, the CAD layers, on a canvas shared by every Layout slide. The SVG layers come from `PlanHover`, `plan-layers.js` and `app.js` `deckPlan()`.
  - `bare(on, re)` keeps only the shell layers (walls, columns, cores, stairs, lifts, toilets, façade). `.bare` on `#world-plan` hides the fit-out SVG layers.
- **3D:** one shared three.js renderer, `AxoModel.renderer()`. It's used by `AxoLayers` (the strategy axo) and `AxoSkp` (the SketchUp model; A day in ACKO; the walk).
- **Walk (render) slides:** `class="scene walk"` with `data-walk='{"n","sub","q","p","r":[image ids],"kp":[keyplan slide nos],"tags"}'`.
  - The images are `assets/img/<id>.webp`.
  - Keyplans come from `data/keyplans.js` (`ACKO_KP`), keyed by the old PPT slide number.

## 4 · How to rebuild

```bash
sh "C:/Users/Ritika/Acko 1610/.claude/worktrees/eager-lumiere-ebac53/handoff/wow/run_wow.sh"
```

- It prints `ok …` per step, then `ok index-approach.html 45`, the three `index-nb-*` pages, `ok nb-options` and `index: 45 slides`.
- **The order matters.** `gen_floorflow.py` **regenerates** `slides/s-layout-dd.html` and `s-layout-sp.html` from `s-layout.html` on every run, and the `wow_*.py` patches run after it. So never hand-edit those two slides: change the script that patches them.
- The other `wow_*.py` patches are idempotent. Each checks a marker string before patching.
  - If you change one, you may need to `git checkout -- slides/<that slide>.html` first so it re-applies. That was done for `s-campus`, `s-memories` and `s-site`.
- **`gen_proposal.py`** runs on its own, only when the proposal PDF changes. It needs PyMuPDF (`fitz`) and Pillow.
  ```bash
  python handoff/wow/gen_proposal.py "<proposal.pdf>" "<deck-wow>"
  ```
  Run `run_wow.sh` again after it.
- **Helpers:**
  - `eol.py`: `rd`/`wr` keep each file's CRLF/LF.
  - `wi_words.py`: the word-by-word markup for the memories' close.
  - `walk_body.js`: used by `wow_walk.py`.
  - `gen_narrative_opts.py`: built `narrative-options.html`, the narrative comparison page.

| Script | What it does |
|---|---|
| `gen_floorflow.py` | Splits the Layout into `s-layout-dd` (Due Diligence + sun path) and `s-layout-sp` (Spaces → Neighbourhoods → 6 neighbourhood sheets → Biophilia ×3 → Acoustics), and adds the floor hand-offs (Site → DD → pitches → vast floor; strategy axo → Spaces). |
| `wow_loop.py` | `s-loop-w`: the Möbius ribbon becomes the Loop on the real floor (`data/loop-path.js`). |
| `wow_sundd.py` | Sun path beat on Due Diligence. |
| `wow_ddshell.py` | Due Diligence on the **bare shell**, drawn as the **core & shell layout** (see §6). |
| `wow_build.py` / `wow_rise.py` | Strategy axo assembles with a clipping wave, and rises from the Loop's floor. |
| `wow_people.py` | 640 people walk to their desks on Spaces, in neighbourhood colours; they stay on Neighbourhoods. |
| `wow_nbsheet.py` | Six neighbourhood sheets (plan + clipped SketchUp axo) on `s-layout-sp` beats 3–8. |
| `wow_approach.py` | `s-approach-w` (How we worked, this deck's six stages) and `s-start` (Where it starts), plus the lavender circle sweep into `s-challenge`. |
| `wow_campus.py` | Challenge → Where both meet: the question line and the seam glide. |
| `wow_whatif.py` | What if folded into the memories (beats 7–8). |
| `wow_thanks.py` | `s-thanks-w`: the Loop closes into the Möbius. |
| `wow_walk.py` | `s-walk`: walk the Loop at eye level on the SketchUp model. |
| `gen_approach.py` | Builds `index-approach.html`: GROUPS, section labels, headers, notes inserts, the lens callbacks, the memories fold, ACKO_WOW, ACKO_SECTIONS. |
| `gen_proposal.py` | 3 Nov proposal: renders → `r3-*.webp` plus the walk slides and order; palette → `pal3-*`; materials → `mat3-*`. |

## 5 · The re-ordered deck now (`index-approach.html`, 45 slides)

The stages are named on "How we worked" and in the sections menu: **01 Understand the people · 02 Spot the opportunity · 03 Discover the site · 04 Frame the idea · 05 Shape the plan · 06 Layer the lenses.**

| Stage | Slides |
|---|---|
| Opening | Cover · Meet the team · How we worked (`s-approach-w`) |
| 01 | **Where it starts** (`s-start`) · The challenge at hand (3 beats) |
| 02 | Where both meet (3) · Maybe, we've felt this before (**8 beats**: 6 memories, then the close) |
| 03 | The site · Layout · Due Diligence (2: DD, sun path) · One floor, two football pitches (2) · What's our challenge (vast floor, 4) |
| 04 | The Möbius · The Loop (`s-loop-w`, 3) |
| 05 | Campus strategy (6) · Layout · Spaces (12) |
| 06 | Acoustic strategy · Wayfinding · Acker's engagement points (4) · Campus palette · Material strategy · **17 render slides** · Walkthrough · Workstation typologies · A day in ACKO (7) |
| Close | Thank you (`s-thanks-w`) |
| Appendix | Well-being by design · Designed for all (D&I) · ESG strategy · About SKV |

**The story thread:**
1. **The people's problem.** It's not a move: moving people isn't easy. "So we design a place that already feels like home: *Teams together · Easy to find · Room to explore · Same rhythm*. One Place. One Experience."
2. **What people want.** 58% come back to belong, and the brief asks for a Modern Indian Institution, so a campus. Then the memories.
3. **The memories' close:**
   - "A campus is where we first felt safe among people. **Protection** is what ACKO promises its customers."
   - "What if the workplace kept that promise **to its own people?** So we started where it has to happen: one floor in Koramangala."
4. **The building's problem** (the site … the vast floor).
5. **The idea** (the Möbius, the Loop) and **the proof** (strategy, walk, Spaces). The Layout's neighbourhoods keep *Teams together*.
6. **The lenses keep the rest of the promise.** Each one has a line in the hand under its header: Acoustic "Same rhythm.", Wayfinding "Easy to find.", Engagement "Room to explore.", Palette and Material "A place that already feels like home."
7. **The renders show it built**, in the 3 Nov proposal's order.

**Hand-offs that must stay smooth** (Ritika: "make sure the transition from one slide to another is smooth"):
- How we worked → Where it starts → the challenge: its lavender grows as a circle from the "Understand" dot.
- Challenge → Where both meet: lavender stays under both pages, and the challenge's vertical line becomes the seam and glides to the centre.
- Where both meet → memories: black to black.
- Site → Due Diligence: the map zooms into the plate.
- DD → pitches → vast floor: the floor glides, then tilts into the axo.
- The Loop lies on the floor → the strategy rises.
- Campus strategy → Spaces: the axo flattens exactly onto the plan.

## 6 · What was built in this chat (9–10 Nov), in order

Each entry gives Ritika's ask, what was built, and her verdict where she gave one.

1. **Re-ordered building chapter, with smooth floor hand-offs** (earlier, on `deck/reordered`). Her correction: "the axo to layout transition should be entire axo turning into spaces layout": the 3D model flattens itself, with no empty layout in between.
2. **Wow moments** (her picks):
   - the Möbius becomes the floor;
   - walk the Loop;
   - 640 people find their seats;
   - the sun across the floor (the sun path lives on Due Diligence, per "add sun path in site due diligence itself");
   - the Loop closes at the end;
   - sound cues;
   - the building assembles.

   Also: the neighbourhood colours on the Neighbourhoods beat; and the neighbourhood sheets, "axo and layout for neighbourhoods individually", six beats.
3. **Problem first, then solution.** `narrative-options.html` offered four variations. She chose **variation 1** ("start with this": the people's challenge). Committed as 3e3663b on `deck/wow`.
4. **How we worked's stages.** Re-ordered to the deck's order. "We didn't talk with the people", so it says **"Understand · the people"** (from the brief and the research). Headline: "We began with what people need, let the site set the terms, and the concept followed."
5. **Gap between How we worked and the challenge.** She said it was both a story gap and a visual one.
   - First built as a second click on How we worked.
   - "This is nice but can come in a different slide, since this whole slide is too cluttered", so it became its own slide, **"Where it starts"** (`s-start`).
6. **Gap between the challenge and Where both meet:** the question line "What makes one place feel like home? We looked at two things.", plus the seam glide.
7. **What if** ("this slide oddly stays"):
   - All three options were built on a comparison page. She picked **B: fold into the memories**.
   - Then "the narrative is the gap": "Safety & Protection" had lost its set-up when the ACKO brand slide dropped out of the order. She chose the wording **"ACKO's own promise"**.
   - Then "the background and text are clashing": the scrim became `rgba(8,8,8,.93)` with a 10 px backdrop blur.
8. **Due Diligence:**
   - "furniture and partitions should not be there, only empty bare shell": the plan now draws only the CAD shell layers.
   - Then her **core & shell layout** as the reference: flat core fills; a cyan **External glazing** line drawn to the reference (the CAD has no glazing layer; `A-WALL-EL3` turned out to be column casings); red entries; matching card swatches; a key line "External glazing / Entry ×2".
   - The green hatch: **"Keep slab areas"**. It marks the "Slab to be strengthened" shapes, not the south voids that her drawing hatches.
9. **The lenses** ("are these slides sitting well, is the narrative right?"):
   - re-ordered so Acoustic strategy follows the Layout's Acoustics, and Material leads into the renders;
   - each lens got its callback line.
10. **The 3 Nov design proposal PDF** ("make sure the contents of these slides are there"). She chose **replace the renders** and **both decks**.
    - **Renders:** all 24 renders, cut as each page crops them, into the walk in the proposal's order and option pairs.
      - Three spaces are new: **Reception Coffee Point** (`s-w-recoffee`), **Outdoor Deck** (`s-w-deck`), **Collab** (`s-w-collab`).
      - **Library** was removed from both orders; its slide file is kept.
    - **Palette and Material:** the campus palette (page 1) and Material strategy (page 27) were rebuilt tile by tile from the PDF.
    - **Already matching:** engagement, acoustic, well-being, D&I, ESG and wayfinding.

11. **The Loop, the walk slide, the neighbourhood sheets** (10 Nov, later):
    - **"Make the loop look smooth."** `window.ACKO_LOOP_SMOOTH(LP)` (in `wow_loop.py`) turns the corridor route into one smooth spline.
      - It keeps every stop exactly (via `sweepStops`) and uses one route point every 30 m between stops, as a centripetal Catmull-Rom, then eases the result.
      - It's used on The Loop beat 3 and on Thank you.
    - **"Remove walk the loop slides."** `s-walk` is out of the 05 group. Campus strategy flattens straight into Spaces again. The re-ordered deck now has **45 slides**.
    - **"Suggest more templates for neighbourhoods slide – current one is too cluttered."** `window.ACKO_NB` switches the sheet's template (`wow_nbsheet.py`):
      - **A**: as built.
      - **B · Axo hero**: the axo full width; below, the name, four counts and a small key plan.
      - **C · Quiet split**: plan | axo; below, the name and four counts.
      - **D · Axo-led**: the axo is large on the right; the small plan and the card are on the left.

      The four counts are workstations, meeting rooms (without phone booths), phone booths and wellness, summed from `z.occ`. There's a page per template (`index-nb-a/b/c/d.html`) and a comparison page, **`nb-options.html`**.
12. **Template E, the deck's sheet now.** Ritika shared a reference (an officebanao tool page, dark, three columns) and said: "the template can be like this itself, and the axo can slowly rotate". `gen_approach.py` `nb_e()` sets `window.ACKO_NB = "e"` in `index-approach.html`. E has three columns, on the deck's light page:
    - **Left column:** "05 · Neighbourhoods · n of 6", the key plan, the name, a line, the stats (desks · area · meeting rooms), and a numbered list of every room type with its count.
    - **Middle, the PLAN card:** the plan framed on the neighbourhood, with the same numbers on the rooms. `nbItems()` matches each `occ` row to a room in `PLAN_DXF.spaces` by type and pax. The numbers follow the live plan view (`nbMarks`).
    - **Right, the AXONOMETRIC card:** the SketchUp cut turns slowly, a full turn every 90 s (`SPIN`, `nbSpinFit`). Its pins on leader lines are projected through the camera every frame (`nbPins`).
    - The white outside the plan card is the card's `box-shadow`; the header, tools, pills and axo sit above it by z-index. The pills move to the foot of the page.
    - If she wants the reference's dark look, it's one CSS block on `[data-nbv="e"]`.
13. **E, lighter** (11 Nov). Her notes: "a lot of text", "no need for the 1, 2, 3, 4 legend, hover to see what it is", "major counts on screen", "the axo should be zoomable", "click and select neighbourhoods", and "no Auto / Life / Drive, only neighbourhood 01, 02".
    - **Left column:** the kicker, the key plan (clickable), six neighbourhood chips (01–06, each in its colour, the current one filled; they jump to that sheet), "Neighbourhood 01", its m², then four big counts (workstations · meeting rooms · phone booths · wellness), and a one-line hint. No paragraph, stats row or list.
    - **Plan and axo:** unnumbered dots coloured by kind (`NBKC`: work, meet, wellness, services). Hovering one shows its name (`data-t`, a CSS tooltip).
    - **The axo is zoomable:** the wheel zooms (`NBX.zf`), a drag pans (`NBX.pan`), a double-click resets (`nbView`, `nbZoomWire`); the slow turn carries on.
    - **Numbers, not names:**
      - `PLAN_DXF.zones[].name` is rewritten to "Neighbourhood nn" at load in s-layout-sp (guarded by `ACKO_WOW`);
      - the beat labels read "Neighbourhood 01" …;
      - Campus strategy's floating labels are patched in `wow_rise.py` (`NB_NUM`).
    - The live deck keeps its names.

## 7 · State right now

- **Uncommitted on `deck/wow`:** everything in §6 from item 4 on. That's the slide changes, the new slides (`s-approach-w`, `s-start`, `s-w-recoffee`, `s-w-deck`, `s-w-collab`), the new images (`r3-*`, `pal3-*`, `mat3-*`), `assets/js/app.js` (`planBare`), `assets/js/plan-canvas.js` (`bare`), `slides/order.txt`, `index-approach.html` and the README. **Commit only when Ritika says so**; she usually says "Yes, commit". Never push or merge.
- **Open points, raised with her but not acted on:**
  - The three new render slides have **no keyplan**: the deck has no camera marks for them.
  - Material strategy has a lot of empty space above its columns.
  - Workstation typologies sits late in 06; she placed it there on 6 Nov.
  - The old `r-*` render images are still on disk, unused.

## 8 · How Ritika likes to work

- **"For different ways, build every option working on one comparison page."** She picks, then iterates.
- When she reports a "gap", ask whether it's **story, visual or both**. It has usually been both.
- **Keep slides uncluttered.** If a slide gets busy, move the extra onto its own slide.
- **Don't overclaim.** The team didn't interview people: say "from the brief and the research".
- **Smooth transitions** are a standing requirement.
- **Show proof:** check in the preview at **1920×1080** and send a screenshot. Then reset the viewport to "desktop".
- **Short answers, then act.** Ask with options when it's her design call.

## 9 · Gotchas

- **Windows + Git Bash heredocs mangle `\n` and `\'`** inside Python string literals. Edit scripts with the editor tool, not heredocs.
- **Many repo files are CRLF.** Use `eol.rd`/`eol.wr`.
- **Background preview tabs throttle `requestAnimationFrame` and timers.** Front the tab and set 1920×1080 before judging animation.
  - Key presses need the page focused: run `document.body.focus()`, or click first.
- **The browser caches pages.** Add `?r=N` to the URL after a rebuild.
- **The "negative viewBox" console error** appears only when the preview resizes. It was already there before this work.
- **Harness hook:** a session running in one worktree may be blocked from writing another worktree's files with the editor tools. Work in the `deck-wow` worktree directly, or run the generators there.
