# Working on a slide

Every slide of the ACKO presentation is **its own HTML file**, `slides/<id>.html` (for example `slides/s-loop.html`). You can open it, change it and send it back without touching anyone else's work. One build then joins all the slides into the single file we present.

## See your slide
**Double-click your file** (`slides/s-loop.html`). It opens in Chrome or Edge with the deck around it:
- **Keys:** the arrows step through its beats, `N` shows the speaker notes and timer, `O` the index.
- **Offline:** no internet and no server needed. Keep the project folder together: the file needs `assets/` and `data/` beside it.

## Change your slide
Open the file in any text editor. Everything you work on sits between two markers:

```html
<!-- slide:start -->
<section class="scene" id="s-loop" …> … the slide … </section>
<style> … this slide's styles … </style>
<script> ACKO.slide("s-loop", (K) => ({ … what happens on each beat … })); </script>
<!-- slide:end -->
```

**The section:**
- Its attributes set the slide:
  - `data-title`, `data-steps` (number of clicks), `data-beats` (their names)
  - `data-mins` (planned minutes), `data-notes` (what to say)
  - `data-mode` (`dark`, `lavender` or `grey`; leave it out for white)
- **Placement:** the page is 16:9. Place things in % of it, the way the PPT places them (`style="left:5%;top:30%;width:40%"`).
- **Type:** in deck points, so `calc(var(--pt) * 16)` is 16 pt.
- **Beats:**
  - `data-step="2"`: shows from beat 2 on
  - `data-only="1"`: shows only on beat 1
  - `class="rv"`: its children come in one after another (`style="--i:0"`, `--i:1` …)

**The styles:** start every rule with your slide's id (`#s-loop .my-thing { … }`), so nothing spills into other slides. The deck's colours and fonts are ready to use:
- **Colours:** `var(--purple)`, `var(--purple-2)`, `var(--lilac)`, `var(--plum)`, `var(--maroon)`
- **The handwritten line:** `class="hand"`
- **The page header:** `<div class="hdr"><b>Title</b><span>Section</span></div>`

**The script** is optional; many slides don't need one. The kit `K` gives you the deck's helpers. The comments in `slides/_template.html` list them.

**Images:**
- Put new ones in `assets/img/<your slide id>/` (for example `assets/img/s-loop/sketch.webp`).
- Write them from the project root, as `assets/img/s-loop/sketch.webp`, never `../assets/…`.
- WebP or JPG, 2400 px wide at most.

## Start a new slide
1. Copy `slides/_template.html` to `slides/s-<name>.html`.
2. Replace `s-new` with `s-<name>` everywhere in the file.
3. Double-click it to check it.

## Hand it back
Send your slide file, plus your image folder if you added images. Whoever joins the deck:
1. drops the file into `slides/` and the images into `assets/img/`
2. adds the slide's id to `slides/order.txt`, on the line where it belongs (that file is the order of the deck)
3. runs `python tools/build.py --single`

That writes **`dist/ACKO-The-Loop.html`: the whole presentation in one file**, with every image, font and the music inside. It opens by double-clicking, from anywhere, offline.

A slide listed in `order.txt` whose file isn't back yet is skipped, with a note, so the deck still builds.

## Please don't
- Edit `assets/js/app.js`, `assets/css/app.css`, `slides/_shell.html` or someone else's slide. If your slide needs something shared, ask.
- Rename your slide's id once others link to it.
