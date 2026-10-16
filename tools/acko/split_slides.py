"""One-off migration (16 Oct 2026): make every slide a self-contained page.

Moves each slide's CSS out of assets/css/app.css (and About SKV's from assets/css/skv.css) by the class prefixes each slide
uses, and its behaviour out of the engine into its own <script> (ACKO.slide factories, written out below), then rewrites each
slides/<id>.html as a standalone page:  head (assets/js/dev.js) · <!-- slide:start --> section · style · script <!-- slide:end -->.
Walk slides get their configuration as a data-walk attribute. Run once; afterwards the slide files are the source.

    python tools/acko/split_slides.py
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda *a: os.path.join(ROOT, *a)

# ---------------------------------------------------------------------------------------------------------- CSS
OWNERS = [  # selector pattern -> slide (first match wins); anything else stays in the shared app.css
    (r"#s-cover\b|\.cv-", "s-cover"), (r"\.tm-(photo|h|p)\b", "s-team"), (r"\.asp-", "s-aspiration"), (r"\.val-", "s-acko"),
    (r"#s-journey\b|\.jr-", "s-journey"), (r"\.ch-|\.solved\b", "s-challenge"), (r"\.mem-", "s-memories"), (r"\.wi-", "s-whatif"),
    (r"\.mb-", "s-mobius"), (r"\.lp-", "s-loop"), (r"\.st-", "s-strategy"), (r"\.cl-", "s-challenges"), (r"\.si-|\.vm-", "s-site"),
    (r"\.fl-", "s-floor"), (r"\.ly-", "s-layout"), (r"\.bl-", "s-blowup"), (r"\.ax-", "s-axo"), (r"\.oc\b|\.oc-", "s-occupancy"), (r"\.th-", "s-thanks"),
]


def blocks(css):
    """top-level CSS blocks as (leading comment, prelude, body) — at-rules keep their whole body"""
    out, i, n, pending = [], 0, len(css), ""
    while i < n:
        if css.startswith("/*", i):
            j = css.index("*/", i) + 2; pending += css[i:j] + "\n"; i = j; continue
        if css[i].isspace(): i += 1; continue
        j = css.index("{", i); prelude = css[i:j].strip(); depth, k = 1, j + 1
        while depth:
            if css[k] == "{": depth += 1
            elif css[k] == "}": depth -= 1
            k += 1
        out.append((pending.strip(), prelude, css[j + 1:k - 1])); pending = ""; i = k
    return out


def owner(sel):
    for pat, sid in OWNERS:
        if re.search(pat, sel): return sid
    return None


def fix_urls(t):
    return re.sub(r"url\((['\"]?)\.\./(img|fonts)/", lambda m: f"url({m.group(1)}assets/{m.group(2)}/", t)


core, per = [], {}
for com, pre, body in blocks(open(P("assets", "css", "app.css"), encoding="utf8").read()):
    if pre.startswith("@"):
        core.append((com, pre, body)); continue
    groups = {}
    for sel in [s.strip() for s in pre.split(",")]:
        groups.setdefault(owner(sel), []).append(sel)
    for who, sels in groups.items():
        rule = (com if len(groups) == 1 else "", ", ".join(sels), body)
        (core if who is None else per.setdefault(who, [])).append(rule)
skv = open(P("assets", "css", "skv.css"), encoding="utf8").read()
per["s-skv"] = blocks(skv)

fmt = lambda rules: "\n".join((c + "\n" if c else "") + f"{p} {{{b}}}" for c, p, b in rules)
head = '/* ACKO · The Loop — the shared styles: fonts, tokens, modes, chrome, the world, the page in deck points, reveals, index,\n   notes, cursor, the walk, palettes, deck pages (.dk / .vt), the layout plan. Each slide\'s own styles live in its file (slides/<id>.html). */\n'
open(P("assets", "css", "app.css"), "w", encoding="utf8").write(head + fmt(core) + "\n")
CSS = {k: fix_urls(fmt(v)) for k, v in per.items()}

# ---------------------------------------------------------------------------------------------------------- walk data
WALK = {
    "s-w-board": {"n": "State Room", "sub": "Boardroom · 32 pax", "q": "This is my big moment", "r": ["r-board-op1", "r-board-op2"], "kp": [24, 25]},
    "s-w-dept": {"n": "Departmental Room", "sub": "20 pax meeting room", "q": "My impact", "r": ["r-dept-op1", "r-dept-op2"], "kp": [26, 27]},
    "s-w-sprint": {"n": "Quick Sprint Room", "sub": "4 pax meeting room", "q": "My impact", "r": ["r-sprint-op1", "r-sprint-op2"], "kp": [28, 29]},
    "s-w-arena": {"n": "Work Arena", "sub": "Neighbourhood", "q": "These are my folks!", "r": ["r-arena-op1", "r-arena-op2"], "kp": [30, 31]},
    "s-w-arena2a": {"n": "Work Arena", "sub": "Neighbourhood · Option 2A", "q": "These are my folks!", "r": ["r-arena2a-1", "r-arena2a-2"], "kp": [32, 33], "tags": ["View 1", "View 2"]},
    "s-w-library": {"n": "Work Arena", "sub": "Library", "q": "These are my folks!", "r": ["r-library"], "kp": [34]},
    "s-w-garden": {"n": "The Acker Garden", "sub": "Work arena", "q": "Wow, worth the commute", "r": ["r-garden-op1", "r-garden-op2"], "kp": [35, 36]},
    "s-w-exec": {"n": "Executive Room", "sub": "Executive corner cabin", "r": ["r-exec"], "kp": [37]},
    "s-w-cafe1": {"n": "Cafe", "sub": "View 1", "q": "Hey, we finally meet!", "r": ["r-cafe1-op1", "r-cafe1-op2"], "kp": [38, 40]},
    "s-w-cafe2": {"n": "Cafe", "sub": "View 2", "q": "Hey, we finally meet!", "r": ["r-cafe2-op1", "r-cafe2-op2"], "kp": [39, 41]},
    "s-w-coffee": {"n": "Coffee Point", "sub": "Coffee corner", "q": "Hey, we finally meet!", "r": ["r-coffee"], "kp": [42]},
    "s-w-mothers": {"n": "Mothers Room", "sub": "A space for all moms @ Acko", "q": "They thought of me too!", "p": "Designed with a soothing palette that keeps calm amid a busy day.", "r": ["r-mothers"], "kp": [43]},
    "s-w-zen": {"n": "Zen Room", "sub": "A space to unwind", "q": "They thought of me too!", "p": "A night-sky optic-fibre ceiling in the brand's hues: peace, and a little curiosity.", "r": ["r-zen"], "kp": [44]},
    "s-w-studio": {"n": "Studio Room", "sub": "A space for Acko's voice", "r": ["r-studio"], "kp": [45]},
}

# ---------------------------------------------------------------------------------------------------------- scripts
JS = {}
JS["s-skv"] = r'''
/* About SKV (SKV's own deck, carried over from the Mitigata presentation): the boards come in group by group; the opening beat
   draws the deck's ASCII data-field live */
ACKO.slide("s-skv", ({ $, $$, later, plain, countUp, reduced, asset }) => {
  const LOGOS = ("Google,Amazon,Samsung,PepsiCo,adidas,Godrej,Aramco,Shell,Honeywell,Qualcomm,GlobalLogic,KPMG,H&M,Max Healthcare,Amway,SYSTRA,PwC,Levi's," +
    "McDermott,DLF,DXC Technology,University of Cambridge,M&S,CNH,Perfetti Van Melle,Kia,The Times of India,MetLife,Cadence,Cyril Amarchand Mangaldas,dunnhumby,Airtel," +
    "MG Motor,Hindustan Times,Concentrix,Spark Minda,Vedanta,British Council,Aon,Fortis,Hero MotoCorp,NTT,Amity University,STL,Macquarie,SRF,BIBA,Synopsys,Adani,ReNew," +
    "Muthoot Finance,Grant Thornton,Stryker,Target").split(",");
  const n2 = (i) => String(i + 1).padStart(2, "0");
  if ($("#skv-logos")) $("#skv-logos").innerHTML = LOGOS.map((n, i) => `<div data-in="${1 + Math.floor(i / 9)}"><img src="${asset(`assets/img/skv/logo-${n2(i)}.webp`)}" alt="${n.replace(/&/g, "&amp;")}"></div>`).join("");
  if ($("#skv-caps")) $("#skv-caps").innerHTML = LOGOS.slice(0, 10).map((_, i) => `<div data-in="1" style="background-image:url(${asset(`assets/img/skv/project-${n2(i)}.webp`)})"></div>`).join("");
  const makeAscii = (cv) => ({
    cv, on: false, last: 0, color: null, GLYPHS: " .:-=+itl1I/T7M#",
    start() { if (!this.cv || this.on) return; this.on = true; this.cv.classList.add("on"); this.frame(performance.now()); },
    stop() { if (!this.cv) return; this.on = false; this.cv.classList.remove("on"); cancelAnimationFrame(this.raf); },
    frame(now) {
      if (!this.on) return;
      this.raf = requestAnimationFrame((t) => this.frame(t));
      if (now - this.last < 70) return;
      this.last = now;
      const cv = this.cv, dpr = Math.min(2, devicePixelRatio || 1), W = cv.clientWidth, Hh = cv.clientHeight;
      if (!W || !Hh) return;
      if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(Hh * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr); }
      const g = cv.getContext("2d"), fs = 12, cw = fs * 0.62, ch = fs * 1.18, t = reduced ? 0 : now / 1000;
      if (!this.color) this.color = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#5222d0";
      g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, Hh);
      g.font = `400 ${fs}px "Lexend", sans-serif`; g.fillStyle = this.color; g.textBaseline = "top";
      const cols = Math.ceil(W / cw), rows = Math.ceil(Hh / ch), G = this.GLYPHS, n = G.length - 1;
      for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
        const a = Math.sin(x * 0.11 + t * 0.7) + Math.sin(y * 0.23 - t * 0.5) + Math.sin((x + y * 1.7) * 0.045 + t * 0.35);
        const cloud = Math.sin(x * 0.035 - t * 0.12) * Math.cos(y * 0.09 + t * 0.1);
        const v = Math.max(0, Math.min(1, ((a / 3 + 1) / 2) * 0.9 + cloud * 0.55 - 0.08));
        const c = G[Math.floor(Math.pow(v, 1.35) * n)];
        if (c === " ") continue;
        g.globalAlpha = 0.2 + 0.8 * v; g.fillText(c, x * cw, y * ch);
      }
      g.globalAlpha = 1;
    },
  });
  const ASCII = makeAscii($("#skv-ascii"));
  return {
    enter() { plain(); },
    step(k) {
      const board = $(`#s-skv .skv-board[data-only="${k}"]`), seen = {};
      if (!board) return;
      const delay = (g) => 80 + g * 260;
      $$("[data-in]", board).forEach((e) => {
        e.classList.remove("in");
        const g = +e.dataset.in, n = (seen[g] = (seen[g] || 0) + 1) - 1;
        later(() => e.classList.add("in"), delay(g) + n * (k === 6 ? 26 : 70));
      });
      $$("[data-count]", board).forEach((e) => later(() => countUp(e, 1500), delay(+e.closest("[data-in]").dataset.in)));
      if (k === 1) ASCII.start(); else ASCII.stop();
    },
    leave() { ASCII.stop(); },
  };
});
'''
JS["s-cover"] = r'''
/* the cover (deck slide 1): the facts come up; a thin Möbius line draws itself over the stairs */
ACKO.slide("s-cover", ({ $, plain, reveal }) => {
  // the edge of a Möbius strip (one curve, twice round), seen in perspective
  function mobiusEdge(R, w, tilt, turn) {
    const pts = [];
    for (let i = 0; i <= 720; i++) {
      const u = (i / 720) * 4 * Math.PI, r = R + w * Math.cos(u / 2);
      const x = r * Math.cos(u + turn), y = r * Math.sin(u + turn), z = w * Math.sin(u / 2);
      const y2 = y * Math.cos(tilt) - z * Math.sin(tilt), z2 = y * Math.sin(tilt) + z * Math.cos(tilt), k = 260 / (260 + z2 * 2.2);
      pts.push([(x * k).toFixed(1), (y2 * k).toFixed(1)]);
    }
    return "M" + pts.map((q) => q.join(" ")).join("L");
  }
  return {
    enter(_, sc) {
      plain(); reveal($(".page.rv", sc), 200);
      const p = $(".cv-mobius path", sc);
      if (p && !p.getAttribute("d")) p.setAttribute("d", mobiusEdge(62, 22, 1.08, 0.35));
      if (p) { p.style.animation = "none"; p.style.setProperty("--len", Math.ceil(p.getTotalLength())); void p.getBoundingClientRect(); p.style.animation = ""; }
    },
  };
});
'''
JS["s-team"] = r'''
/* the team (deck slide 2): the portraits come in one after another */
ACKO.slide("s-team", ({ $, plain, reveal }) => ({ enter(_, sc) { plain(); reveal($(".tm-people", sc), 150); } }));
'''
JS["s-aspiration"] = r'''
/* workplace aspiration (deck slide 3): the three tiles rise in, then the handwritten line */
ACKO.slide("s-aspiration", ({ $, plain, reveal }) => ({ enter(_, sc) { plain(); reveal($(".page", sc), 100); } }));
'''
JS["s-acko"] = r'''
/* what defines ACKO (deck slide 4): the five values open like shutters; then, slowly, each strip turns to its second picture
   (the deck's click swaps the first) */
ACKO.slide("s-acko", ({ $, $$, plain, reveal, later }) => ({
  enter(_, sc) {
    plain(); const strips = $$(".val-strip", sc); strips.forEach((s) => s.classList.remove("swap"));
    reveal($(".page", sc), 100);
    strips.forEach((s, i) => later(() => s.classList.add("swap"), 4200 + i * 900));
  },
}));
'''
JS["s-journey"] = r'''
/* the journey (deck slide 5): 1 why an insurance, over five faces of protection; 2 we respect the journey — the timeline draws
   along its line, the milestones come up, then the founder's words */
ACKO.slide("s-journey", ({ $, $$, plain, reveal, later, clearTimers, typeWords }) => ({
  enter() { plain(); },
  step(k, sc) {
    clearTimers();
    sc.classList.toggle("b2", k === 2);
    if (k === 1) { reveal($(".jr-collage", sc), 200); return; }
    const ms = $$(".jr-ms", sc), line = $(".jr-line", sc);
    line.classList.remove("go"); ms.forEach((m) => m.classList.remove("go"));
    later(() => line.classList.add("go"), 500);
    ms.forEach((m, i) => later(() => m.classList.add("go"), 700 + i * 230));
    typeWords($(".jr-quote q", sc), 90, 900 + ms.length * 230);
  },
}));
'''
JS["s-challenge"] = r'''
/* the challenge → the solution (deck slides 6 → 7): the people of two offices, two clusters that drift towards each other (1)
   and then become one loop (2) */
ACKO.slide("s-challenge", ({ $, $$, plain, reveal, raf2 }) => {
  const N = 64;
  function chDots(svg) {
    if (svg.children.length) return;
    let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const out = [];
    for (let i = 0; i < N; i++) {
      const a = i < N / 2 ? [330, 260] : [1530, 250], ang = rnd() * Math.PI * 2, rr = Math.sqrt(rnd()) * 130;
      const from = [a[0] + Math.cos(ang) * rr, a[1] + Math.sin(ang) * rr * 0.62];
      const near = [from[0] + (i < N / 2 ? 260 : -260), from[1]];
      // on the loop: a figure of eight across the middle of the page
      const t = (i / N) * Math.PI * 2, loop = [960 + 520 * Math.sin(t), 270 + 150 * Math.sin(t) * Math.cos(t) * 1.6];
      out.push(`<circle r="${(5 + rnd() * 4).toFixed(1)}" cx="0" cy="0" data-a="${from.map(Math.round)}" data-b="${near.map(Math.round)}" data-c="${loop.map(Math.round)}" style="transform:translate(${from[0]}px,${from[1]}px)"/>`);
    }
    svg.innerHTML = `<g class="ch-people">${out.join("")}</g>` +
      `<text x="330" y="470" text-anchor="middle" class="ch-l a">TWO EXISTING LOCATIONS</text><text x="1530" y="470" text-anchor="middle" class="ch-l a"></text>` +
      `<text x="960" y="520" text-anchor="middle" class="ch-l b">ONE PLACE</text>`;
  }
  function chMove(svg, key, ms) {
    $$("circle", svg).forEach((c, i) => {
      const [x, y] = c.dataset[key].split(",").map(Number);
      c.style.transition = ms ? `transform ${ms}ms cubic-bezier(.45,.05,.3,1) ${Math.round((i % 16) * 25)}ms` : "none";
      c.style.transform = `translate(${x}px,${y}px)`;
    });
  }
  return {
    enter(_, sc) { plain(); chDots($("#ch-dots", sc)); },
    step(k, sc) {
      const pg = $(".page", sc), svg = $("#ch-dots", sc);
      pg.classList.toggle("solved", k === 2);
      if (k === 1) { chMove(svg, "a", 0); raf2(() => chMove(svg, "b", 2800)); }
      else chMove(svg, "c", 2400);
      reveal($(".ch-words", sc), 100);
    },
  };
});
'''
JS["s-memories"] = r'''
/* memories (deck slide 8): a dotted path across the campus; the six moments come up along it */
ACKO.slide("s-memories", ({ $, $$, plain, reveal, later, drawPath }) => ({
  enter(_, sc) {
    plain();
    const stops = $$(".mem-stop", sc); stops.forEach((s) => s.classList.remove("on"));
    drawPath($(".mem-path path", sc), 5200, 400);
    stops.forEach((s, i) => later(() => s.classList.add("on"), 700 + i * 820));
    reveal($(".mem-h", sc), 100);
    $$(".mem-h span", sc).forEach((e, i) => e.style.setProperty("--i", i * 4));
  },
}));
'''
JS["s-whatif"] = r'''
/* what if (deck slide 9): the question, word by word */
ACKO.slide("s-whatif", ({ $, plain, typeWords }) => ({ enter(_, sc) { plain(); typeWords($(".wi-q", sc), 120, 300); } }));
'''
JS["s-mobius"] = r'''
/* the Möbius (deck slide 10): a live white strip, softly lit, swaying slowly — ACKO's own mark, one continuous surface.
   three.js r147 (assets/vendor); its single edge is drawn as a fine lavender line so the strip reads on the white page */
ACKO.slide("s-mobius", ({ $, plain, reveal, reduced }) => {
  const MOB = { r: null };
  function mobius(host) {
    if (MOB.r) { host.appendChild(MOB.r.domElement); return; }
    const THREE = window.THREE; if (!THREE) return;
    const r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    r.setPixelRatio(Math.min(2, devicePixelRatio || 1)); r.setClearColor(0x000000, 0);
    host.appendChild(r.domElement);
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(24, 1, 0.1, 100);
    cam.position.set(0, 6.6, 5.6); cam.lookAt(0, -0.05, 0.1);
    // the strip: u around the loop, v across the band (a flat, wide ribbon as in the deck's render)
    const NU = 360, NV = 24, R = 1.95, Wd = 0.52, T = 0.06;
    const pos = [], idx = [];
    const pt = (u, v, off) => {
      const c = Math.cos(u / 2), s = Math.sin(u / 2);
      const x = (R + v * c) * Math.cos(u), z = (R + v * c) * Math.sin(u), y = v * s;
      const du = [-(R + v * c) * Math.sin(u) - 0.5 * v * s * Math.cos(u), 0.5 * v * c, (R + v * c) * Math.cos(u) - 0.5 * v * s * Math.sin(u)];
      const dv = [c * Math.cos(u), s, c * Math.sin(u)];
      let n = [du[1] * dv[2] - du[2] * dv[1], du[2] * dv[0] - du[0] * dv[2], du[0] * dv[1] - du[1] * dv[0]];
      const l = Math.hypot(...n); n = n.map((q) => q / l);
      return [x + n[0] * off, y + n[1] * off, z + n[2] * off];
    };
    for (let side = 0; side < 2; side++) {
      const base = pos.length / 3, off = side ? -T / 2 : T / 2;
      for (let i = 0; i <= NU; i++) for (let j = 0; j <= NV; j++) pos.push(...pt((i / NU) * Math.PI * 2, -Wd + (2 * Wd * j) / NV, off));
      for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) {
        const a = base + i * (NV + 1) + j, b = a + NV + 1;
        if (side) idx.push(a, a + 1, b, b, a + 1, b + 1); else idx.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({ color: 0xe6e1f0, roughness: 0.55, metalness: 0.0, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(g, mat); scene.add(mesh);
    const ep = [];
    for (let i = 0; i <= 1440; i++) ep.push(...pt((i / 1440) * Math.PI * 4, Wd, 0));
    const eg = new THREE.BufferGeometry(); eg.setAttribute("position", new THREE.Float32BufferAttribute(ep, 3));
    mesh.add(new THREE.Line(eg, new THREE.LineBasicMaterial({ color: 0x8f78dc, transparent: true, opacity: 0.85 })));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x5a5175, 0.7));
    const key = new THREE.DirectionalLight(0xffffff, 0.85); key.position.set(-5, 6, 4); scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 0.25); fill.position.set(5, 2, 6); scene.add(fill);
    const rim = new THREE.DirectionalLight(0xc9b3f3, 0.7); rim.position.set(4, -3, -5); scene.add(rim);
    MOB.r = r; MOB.scene = scene; MOB.cam = cam; MOB.mesh = mesh;
  }
  function run(host) {
    const r = MOB.r; if (!r) return;
    const t0 = performance.now();
    const loop = (now) => {
      if (document.body.dataset.scene !== "s-mobius") return;
      const W = host.clientWidth, Hh = host.clientHeight;
      if (W && Hh && (r.domElement.width !== Math.round(W * r.getPixelRatio()) || r.domElement.height !== Math.round(Hh * r.getPixelRatio()))) { r.setSize(W, Hh, false); MOB.cam.aspect = W / Hh; MOB.cam.updateProjectionMatrix(); }
      const t = reduced ? 0 : (now - t0) / 1000;
      MOB.mesh.rotation.y = -0.6 + 0.28 * Math.sin(t * 0.18);   // a slow sway, so the copy always sits in the loop
      MOB.mesh.rotation.x = 0.06 * Math.sin(t * 0.4);
      r.render(MOB.scene, MOB.cam);
      MOB.raf = requestAnimationFrame(loop);
    };
    cancelAnimationFrame(MOB.raf); MOB.raf = requestAnimationFrame(loop);
  }
  return {
    enter(_, sc) { plain(); const host = $(".mb-stage", sc); mobius(host); run(host); reveal($(".mb-copy", sc), 600); },
    leave() { cancelAnimationFrame(MOB.raf); },
  };
});
'''
JS["s-loop"] = r'''
/* the Loop (deck slides 11–12): 1 welcome to the Loop — people and trees along the line; 2 the lavender ribbon draws from left
   to right and the seven stops come up as it reaches them, each with what it should feel like */
ACKO.slide("s-loop", ({ $, $$, plain, reveal, clearTimers, reduced, state }) => {
  // the seven stops of slide 12: [name, words, dot x/y, label x/y] in % of the page
  const STOPS = [
    ["Arrival", "I feel welcomed", [2.4, 38.9], [6.1, 26]], ["Cafe", "Hey We finally meet !", [17, 46.8], [14, 35.4]],
    ["Board Room", "This is my big moment", [40.3, 43.9], [46.3, 24.5]], ["Meeting Rooms", "My Impact", [55.7, 45.7], [62.7, 23.2]],
    ["Collab", "Wow, worth the commute", [76.1, 45.4], [79.3, 23.2]], ["Work", "These are my folks!", [96.8, 46.8], [93.6, 30.5]],
    ["Wellness", "They thought of me too!", [78.4, 70], [90.2, 66.2]],
  ];
  function build(sc) {
    const host = $(".lp-stops", sc); if (host.children.length) return;
    host.innerHTML = STOPS.map(([n, q, d, l]) => `<div class="lp-stop" style="left:${d[0]}%;top:${d[1]}%"><i></i>` +
      `<div class="lab" style="left:calc(${l[0] - d[0]} * var(--pw) / 100);top:calc(${l[1] - d[1]} * var(--ph) / 100)"><b>${n}</b><q>${q}</q></div></div>`).join("");
    $(".lp-leads", sc).innerHTML = STOPS.map(([, , d, l], i) => {
      const x1 = l[0] * 19.2, y1 = (l[1] + (l[1] < d[1] ? 5 : -0.5)) * 10.8, x2 = d[0] * 19.2, y2 = d[1] * 10.8;
      return `<path data-k="${i}" d="M${x1} ${y1}Q${x1} ${(y1 + y2) / 2} ${x2} ${y2}"/>`;
    }).join("");
  }
  return {
    enter(_, sc) { plain(); build(sc); reveal($(".lp-cuts", sc), 100); },
    step(k, sc) {
      clearTimers();
      const rib = $(".lp-ribbon", sc), stops = $$(".lp-stop", sc);
      $$(".lp-leads path", sc).forEach((l) => l.classList.remove("on"));
      if (k === 1) { rib.style.setProperty("--rv", "0%"); stops.forEach((s) => s.classList.remove("on")); return; }
      const t0 = performance.now(), MS = reduced ? 1 : 4200;
      stops.forEach((s) => s.classList.remove("on"));
      const run = (now) => {
        if (document.body.dataset.scene !== "s-loop" || state.step !== 2) return;
        const e = Math.min(1, (now - t0) / MS), v = (1 - Math.pow(1 - e, 2)) * 106;
        rib.style.setProperty("--rv", v + "%");
        stops.forEach((s, i) => { if (parseFloat(s.style.left) <= v - 2 && !s.classList.contains("on")) { s.classList.add("on"); const l = $(`.lp-leads [data-k="${i}"]`, sc); if (l) l.classList.add("on"); } });
        if (e < 1) requestAnimationFrame(run);
      };
      requestAnimationFrame(run);
    },
  };
});
'''
JS["s-strategy"] = r'''
/* campus strategy (deck slide 13): the deck's animated axo of the floor, keyed out of its green screen */
ACKO.slide("s-strategy", ({ $, plain, reveal }) => ({ enter(_, sc) { plain(); reveal($(".page", sc), 100); } }));
'''
JS["s-site"] = r'''
/* the site: Koramangala as a vector map (Overture/OSM, data/site-floor.js); it closes in on Regalium, then turns 11.5° so the
   building lines up with the plans. Drawn in the world's map layer (#vmap) */
ACKO.slide("s-site", ({ $, $$, later, reveal, countUp, world, shade, reduced }) => {
  const SV = { built: false, vb: [-760, -590, 1520, 1180], rot: 0, raf: 0 };
  function siteMap() {
    if (SV.built || !window.ACKO_SITE) return;
    const S = window.ACKO_SITE, svg = $("#vmap");
    const roads = S.roads.slice().sort((a, b) => b.rank - a.rank);
    const land = S.land ? Object.entries(S.land).map(([k, d]) => `<path class="vm-land ${k}" d="${d}"/>`).join("") : "";
    const water = (S.water || []).map((w) => `<path class="vm-water" d="${w.d}"/>`).join("");
    const rail = (S.rail || []).map((r) => `<path class="vm-rail" d="${r.d}"/>`).join("");
    const hosur = S.hosur.map((seg) => `<path class="vm-hosur" d="M${seg.map((q) => q.join(" ")).join("L")}"/>`).join("");
    const marks = S.marks.slice(0, 5).map((m) => `<g class="vm-mark" transform="translate(${m.x} ${m.y})"><circle r="6"/><text x="10" y="4">${m.n}</text></g>`).join("");
    const labels = S.labels.map((l) => `<text class="vm-lab" transform="translate(${l.x} ${l.y}) rotate(${l.a})" text-anchor="middle">${l.t}</text>`).join("");
    svg.setAttribute("viewBox", SV.vb.join(" ")); svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
    svg.innerHTML = `<g id="vm-root">${land}${water}` +
      roads.map((r) => `<path class="vm-road c" d="${r.d}" style="stroke-width:${r.w + 2.4}"/>`).join("") +
      roads.map((r) => `<path class="vm-road" d="${r.d}" style="stroke-width:${r.w}"/>`).join("") + rail + hosur +
      `<g class="vm-bld">${S.buildings.map((d) => `<path d="${d}"/>`).join("")}</g>` +
      `<path class="vm-foot" d="${S.footprint.d}"/><path class="vm-plate" d="${S.onSite.plate}"/>` +
      `<circle class="vm-gate" cx="${S.gate[0]}" cy="${S.gate[1]}" r="7"/>${labels}${marks}` +
      `<g class="vm-pin" transform="translate(0 10)"><text y="-62" text-anchor="middle">Regalium · 3rd floor</text></g></g>`;
    $("#map-credit").textContent = S.attribution || "© OpenStreetMap contributors, Overture Maps";
    $("#s-site .si-walk").innerHTML = S.marks.slice(0, 5).map((m) => `<li><b>${m.n}</b><span>${m.walk >= 1000 ? (m.walk / 1000).toFixed(1) + " km" : Math.round(m.walk) + " m"} walk</span></li>`).join("");
    SV.built = true;
  }
  function view(vb, rot, ms) {
    cancelAnimationFrame(SV.raf);
    const svg = $("#vmap"), root = $("#vm-root"), from = SV.vb.slice(), r0 = SV.rot, t0 = performance.now();
    if (!root) return;
    const set = (v, r) => { SV.vb = v; SV.rot = r; svg.setAttribute("viewBox", v.map((q) => q.toFixed(1)).join(" ")); root.setAttribute("transform", `rotate(${r.toFixed(2)} 0 10)`); };
    if (!ms || reduced) return set(vb, rot);
    const run = (now) => { const k = Math.min(1, (now - t0) / ms), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      set(from.map((a, i) => a + (vb[i] - a) * e), r0 + (rot - r0) * e); if (k < 1) SV.raf = requestAnimationFrame(run); };
    SV.raf = requestAnimationFrame(run);
  }
  return {
    enter(_, sc) {
      siteMap(); world("map"); shade("left");
      // the whole neighbourhood, then closer, with Regalium right of the copy; then the turn that lines it up with the plans
      view([-1060, -590, 2100, 1180], 0, 0);
      later(() => view([-860, -360, 1300, 731], 0, 3000), 500);
      later(() => view([-713, -315, 1150, 647], -(window.ACKO_SITE ? window.ACKO_SITE.grid : 11.5), 1800), 3700);
      reveal($(".si-copy", sc), 300);
      $$("[data-count]", sc).forEach((e, i) => later(() => countUp(e, 1400), 900 + i * 150));
    },
    leave() { cancelAnimationFrame(SV.raf); },
  };
});
'''
JS["s-floor"] = r'''
/* the floor: the bare plate before any furniture (data/site-floor.js). 1 the sun runs across an equinox day, its patches falling
   through the glass, then the 6 m daylight band; 2 fire first — 15/30/45 m rings at the five stairs, then the eight measured exit
   paths, then the compartment line */
ACKO.slide("s-floor", ({ $, $$, plain, later, clearTimers, countUp, drawPath }) => {
  let built = false;
  function floorSvg(svg) {
    if (built || !window.ACKO_FLOOR) return;
    const F = window.ACKO_FLOOR, P = (a) => "M" + a.map((q) => q.join(" ")).join("L") + "Z", L = (a) => "M" + a.map((q) => q.join(" ")).join("L");
    const plate = P(F.plate);
    svg.innerHTML = `<defs><clipPath id="fl-clip"><path d="${plate}"/></clipPath></defs>` +
      `<path class="fl-plate" d="${plate}"/>` +
      `<g clip-path="url(#fl-clip)"><path class="fl-band" d="${plate}"/><g class="fl-sun"></g></g>` +
      F.terraces.map((t) => `<path class="fl-terr" d="${P(t)}"/>`).join("") +
      F.cores.map((c) => `<path class="fl-core" d="${P(c)}"/>`).join("") +
      F.cols.map((c) => `<rect class="fl-col" x="${c[0] - c[2] / 2}" y="${c[1] - c[3] / 2}" width="${c[2]}" height="${c[3]}"/>`).join("") +
      F.stairs.map((s) => `<g class="fl-stair"><rect x="${s.x}" y="${s.y}" width="${s.w}" height="${s.h}"/><text x="${s.x + s.w / 2}" y="${s.y + s.h / 2 + 22}">${s.id}</text></g>`).join("") +
      `<g class="fl-rings">${F.stairs.map((s) => [900, 600, 300].map((r) => `<circle cx="${s.x + s.w / 2}" cy="${s.y + s.h / 2}" r="${r}"/>`).join("")).join("")}</g>` +
      `<g class="fl-routes">${F.routes.map((r) => `<path d="${L(r.pts)}"/>`).join("")}</g>` +
      `<g class="fl-rlab">${F.routes.map((r) => { const q = r.pts[0]; return `<text x="${q[0]}" y="${q[1] - 18}">${Math.round(r.m)} m</text>`; }).join("")}</g>` +
      `<g class="fl-comp">${(F.comp || []).map((c) => `<path d="${L(c)}"/>`).join("")}</g>` +
      `<g class="fl-entry">${(F.entries || []).map((e) => `<path d="${P(e)}"/>`).join("")}</g>` +
      `<g class="fl-sunpos"><circle r="46"/></g><text class="fl-n" x="4960" y="-150">N</text>`;
    built = true;
  }
  function sunRun(svg, day) {
    const F = window.ACKO_FLOOR, frames = F.sun.find((d) => d.k === day) || F.sun[0], g = $(".fl-sun", svg), pos = $(".fl-sunpos", svg);
    const cx = 2460, cy = 380, R = 2600, up = 11.5;
    let i = 0;
    $("#fl-d").textContent = frames.label;
    const show = () => {
      const f = frames.frames[i];
      g.innerHTML = f.p.map((d) => `<path d="${d}"/>`).join("");
      $("#fl-t").textContent = f.t;
      const a = ((f.az - up) * Math.PI) / 180, x = cx + R * Math.sin(a), y = cy - R * 0.36 * Math.cos(a);
      pos.setAttribute("transform", `translate(${x.toFixed(0)} ${y.toFixed(0)})`); pos.style.opacity = f.alt > 0 ? 1 : 0;
      i++;
      if (i < frames.frames.length) later(show, 300); else later(() => svg.classList.add("band"), 400);
    };
    show();
  }
  return {
    enter(_, sc) { plain(); floorSvg($("#fl-svg", sc)); },
    step(k, sc) {
      clearTimers();
      const svg = $("#fl-svg", sc);
      if (!window.ACKO_FLOOR) return;
      svg.classList.remove("band", "fire1", "fire2", "fire3");
      if (k === 1) { svg.classList.add("sunny"); sunRun(svg, "mar"); $$("[data-only='1'] [data-count]", sc).forEach((e) => countUp(e, 1500)); return; }
      svg.classList.remove("sunny"); $(".fl-sun", svg).innerHTML = "";
      svg.classList.add("fire1");
      later(() => { svg.classList.add("fire2"); $$(".fl-routes path", svg).forEach((q, i) => drawPath(q, 1400, i * 160)); }, 1500);
      later(() => svg.classList.add("fire3"), 3600);
    },
  };
});
'''
JS["s-challenges"] = r'''
/* what's our challenge (deck slide 14), on the deck's axo of the bare floor: 1 homogeneity — one uniform grid of desks floods the
   plate; 2 disorientation — a desk at the far end is a long walk from the café and the arrivals; 3 distance — the route the deck
   draws, end to end, 245 m */
ACKO.slide("s-challenges", ({ $, plain, later, countUp, drawPath, inPoly }) => {
  function clDesks(g) {
    if (g.childElementCount) return;
    const A = [39, 1029], U = [1359, -1014], V = [206, 130], core = [[300, 842], [1095, 241], [1190, 303], [399, 916]];
    const terr = [[[556, 856], [628, 801], [680, 841], [608, 896]], [[1079, 466], [1154, 407], [1206, 448], [1130, 505]]];
    const out = [], NU = 104, NV = 8;
    for (let i = 0; i <= NU; i++) for (let j = 0; j < NV; j++) {
      const ii = i / NU, jj = (j + 0.5) / NV, x = A[0] + U[0] * ii + V[0] * jj, y = A[1] + U[1] * ii + V[1] * jj;
      if (inPoly([x, y], core) || terr.some((t) => inPoly([x, y], t))) continue;
      const a = 0.62 / NU, b = 0.36 / NV;
      out.push(`<path style="--d:${Math.round(ii * 1400)}ms" d="M${x.toFixed(1)} ${y.toFixed(1)}l${(U[0] * a).toFixed(1)} ${(U[1] * a).toFixed(1)}l${(V[0] * b).toFixed(1)} ${(V[1] * b).toFixed(1)}l${(-U[0] * a).toFixed(1)} ${(-U[1] * a).toFixed(1)}Z"/>`);
    }
    g.innerHTML = out.join("");
  }
  return {
    enter(_, sc) { plain(); clDesks($(".cl-desks", sc)); },
    step(k, sc) {
      const svg = $(".cl-svg", sc);
      ["b1", "b2", "b3"].forEach((c, i) => svg.classList.toggle(c, k === i + 1));
      if (k === 3) { drawPath($(".cl-route", sc), 3200, 300); later(() => countUp($(".cl-len [data-count]", sc), 2600), 500); }
      if (k === 2) drawPath($(".cl-walk", sc), 2200, 400);
    },
  };
});
'''
JS["s-thanks"] = r'''
/* thank you: the Appendix and About SKV from here */
ACKO.slide("s-thanks", ({ $, plain, reveal, go, trackIdx, sceneIx }) => ({
  enter(_, sc) {
    plain(); reveal($(".page", sc), 100);
    $("#to-appendix").onclick = () => go(trackIdx("appendix")[0], 1);
    $("#to-skv").onclick = () => go(sceneIx("s-skv"), 1);
  },
}));
'''
JS["s-axo"] = r'''
/* the schematic axonometrics (deck slides 58–60): west, middle, east; the leaders draw out to their spaces */
ACKO.slide("s-axo", ({ $$, plain }) => ({
  enter() { plain(); },
  step(k, sc) { $$(".ax-keys span", sc).forEach((b) => b.classList.toggle("on", +b.dataset.k === k)); },
}));
'''
JS["s-occupancy"] = r'''
/* the occupancy chart (deck slide 61): the rows come in one after another; shortfalls in maroon, more than asked in purple */
ACKO.slide("s-occupancy", ({ $, $$, plain, reveal, later, countUp }) => ({
  enter(_, sc) {
    plain();
    const rows = $$(".oc tbody tr", sc); rows.forEach((r) => r.classList.remove("in"));
    rows.forEach((r, i) => later(() => { r.classList.add("in"); $$("[data-count]", r).forEach((e) => countUp(e, 700)); }, 200 + i * 70));
    reveal($(".page", sc), 100);
    later(() => countUp($(".oc-big [data-count]", sc), 1600), 400 + rows.length * 70);
  },
}));
'''
JS["s-layout"] = r'''
/* layout Option 02A (deck slides 53–54) on the shared plan (K.plan): 1 the plan and its legend; 2 the six neighbourhoods draw in,
   their seats count up, and hovering a row picks out its outline */
ACKO.slide("s-layout", ({ $, $$, later, countUp, plan }) => ({
  enter(_, sc) { plan.deckPlan(); plan.nbHover($(".ly-nbs", sc)); },
  step(k, sc) {
    plan.planOn(sc, { nb: k === 2, lab: k === 2, entry: true, blow: k === 1, view: [0, 0, 1920, 1080], ms: 0 });
    if (k === 2) {
      $$(".dp-nb polygon", plan.svg).forEach((p, i) => { p.style.setProperty("--len", Math.ceil(p.getTotalLength())); p.style.animationDelay = i * 0.22 + "s"; });
      $$("[data-count]", sc).forEach((e, i) => later(() => countUp(e, 1400), 300 + i * 180));
    }
  },
  leave() { plan.planOff(); },
}));
'''
JS["s-blowup"] = r'''
/* the blow-ups (deck slides 55–57): the same plan flies into X, Y and Z; the fire compartment line draws on Y */
ACKO.slide("s-blowup", ({ $, $$, plan }) => {
  const DISP = [38, 150, 1882, 880];
  return {
    step(k, sc) {
      const key = ["X", "Y", "Z"][k - 1], P = window.DECK_PLAN;
      plan.planOn(sc, { fire: key === "Y", entry: true, blow: false, view: plan.vbFor(P.blow[key], DISP), ms: 1100 });
      $(".bl-sub", sc).textContent = `Space Planning - Option 02A | Blown Up ${key}`;
      $$(".bl-keys span", sc).forEach((b) => b.classList.toggle("on", b.dataset.k === key));
    },
    leave() { plan.planOff(); },
  };
});
'''

# ---------------------------------------------------------------------------------------------------------- the pages
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · ACKO slide {sid}</title>
<!-- Open this file on its own to see and work on the slide (offline, no server). dev.js loads the deck's styles, data, chrome and
     engine around it. The build (tools/build.py) takes only what sits between the two markers below. -->
<base href="../">
<script src="assets/js/dev.js"></script>
</head>
<body>
<!-- slide:start -->
{section}
{style}{script}<!-- slide:end -->
</body>
</html>
"""
n = 0
for f in sorted(os.listdir(P("slides"))):
    if not f.endswith(".html") or f.startswith("_"): continue
    sid = f[:-5]
    text = open(P("slides", f), encoding="utf8").read()
    if "<!-- slide:start -->" in text:
        print("already split:", sid); continue
    section = text.strip()
    if sid in WALK and "data-walk=" not in section:
        section = section.replace(f'id="{sid}"', f'id="{sid}" data-walk="{html.escape(json.dumps(WALK[sid], ensure_ascii=False), quote=True)}"', 1)
    title = html.unescape(re.search(r'data-title="([^"]*)"', section).group(1))
    style = f"<style>\n{CSS[sid]}\n</style>\n" if sid in CSS else ""
    script = f"<script>{JS[sid].rstrip()}\n</script>\n" if sid in JS else ""
    open(P("slides", f), "w", encoding="utf8").write(PAGE.format(title=html.escape(title), sid=sid, section=section, style=style, script=script))
    n += 1
missing = sorted(set(CSS) - {f[:-5] for f in os.listdir(P("slides"))})
print(f"{n} slides written; CSS moved for {len(CSS)} slides; JS for {len(JS)}; CSS for slides not found: {missing}")
print("core rules left in app.css:", len(core))
