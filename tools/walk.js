// Headless check of the presentation in this checkout, from file:// (as it is presented: double-clicked, offline).
//
//   node tools/walk.js                    every beat of every slide: console errors, failed requests, anything on the logo lockup;
//                                         exits 1 on any error
//   node tools/walk.js --slide s-loop     one slide: each beat screenshotted (to --out), plus its errors
//   node tools/walk.js --page dist/ACKO-The-Loop.html --single    the single file: also fails on ANY request for a file (it must need nothing)
//   node tools/walk.js --page slides/s-loop.html                  one slide file opened on its own
//   options: --out <dir>  --size 1366x768
//
// Needs node, puppeteer-core (set NODE_PATH=C:/Users/Ritika/Mitigata/node_modules) and Chrome.
const path = require("path"), fs = require("fs"), os = require("os");
const puppeteer = require("puppeteer-core");

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const SLIDE = arg("--slide"), [W, H] = arg("--size", "1600x900").split("x").map(Number);
const OUT = arg("--out", path.join(os.tmpdir(), "acko-walk", SLIDE || "all"));
// index.html is built from slides/ (tools/build.py): build it first so the walk sees the current slides (unless --page names a file)
const PAGEFILE = arg("--page");
if (!PAGEFILE) require("child_process").execFileSync(process.env.PYTHON || "python", [path.join(__dirname, "build.py")], { stdio: "inherit" });
const PAGE = "file:///" + path.resolve(PAGEFILE || path.join(__dirname, "..", "index.html")).replace(/\\/g, "/");
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
// slides whose beats animate for a while before they settle
const WAIT = { "s-cover": 2600, "s-team": 1800, "s-aspiration": 2600, "s-acko": 2400, "s-journey": 6200, "s-challenge": 3600, "s-memories": 6800,
  "s-whatif": 3600, "s-mobius": 2400, "s-loop": 5200, "s-strategy": 1800, "s-site": 6200, "s-floor": 8200, "s-challenges": 4200, "s-typologies": 2600,
  "s-palette1": 1800, "s-palette2": 1800, "s-engage": 2600, "s-material": 2600, "s-acoustic": 2600, "s-wayfinding": 2600, "s-layout": 3200,
  "s-blowup": 1600, "s-axo": 2600, "s-occupancy": 3800, "s-thanks": 1200, "s-skv": 1800 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--allow-file-access-from-files"], defaultViewport: { width: W, height: H } });
  const page = await browser.newPage();
  const errors = [];
  let at = "load";
  page.on("pageerror", (e) => errors.push(`${at}: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${at}: ${m.text()}`); });
  // a paused audio stream has its open download dropped by Chrome (net::ERR_ABORTED): normal, not an error
  const mediaAbort = (r) => (/\.(mp3|m4a|ogg|mp4|webm)$/i.test(r.url()) || r.resourceType() === "media") && (r.failure() || {}).errorText === "net::ERR_ABORTED";
  page.on("requestfailed", (r) => { if (!mediaAbort(r)) errors.push(`${at}: FAILED ${r.url()} (${r.resourceType()}, ${(r.failure() || {}).errorText})`); });
  // the single file must not reach for anything beside itself
  if (PAGEFILE && process.argv.includes("--single")) page.on("request", (r) => { const u = r.url(); if (!/^(blob:|data:|about:)/.test(u) && decodeURI(u.split("#")[0]) !== PAGE) errors.push(`${at}: REQUEST ${u}`); });
  await page.goto(PAGE, { waitUntil: "load", timeout: 120000 });
  await page.waitForFunction(() => window.ACKO && window.ACKO.state && window.ACKO.state.idx >= 0, { timeout: 120000 });
  await sleep(1500);
  const list = await page.evaluate(() => [...document.querySelectorAll(".scene")].map((s, i) => ({ i, id: s.id, n: +s.dataset.steps || 1 })));
  await page.evaluate(() => {   // anything visible sitting on the bottom-right logo lockup
    window.__lockHits = () => {
      const L = document.querySelector(".lockup"); if (!L) return [];
      const lr = L.getBoundingClientRect(), pad = 4, big = innerWidth * innerHeight * 0.2, out = [];
      const hit = (r) => r.right > lr.left - pad && r.left < lr.right + pad && r.bottom > lr.top - pad && r.top < lr.bottom + pad;
      const shown = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement) { const cs = getComputedStyle(n); if (cs.display === "none" || cs.visibility === "hidden" || +cs.opacity < 0.05) return false; } return true; };
      const root = document.querySelector(".scene.active");
      for (const e of root.querySelectorAll("*")) {
        const r = e.getBoundingClientRect();
        if (!r.width || !r.height || r.width * r.height > big || !hit(r) || !shown(e)) continue;
        if (e.children.length && !["BUTTON", "svg", "IMG"].includes(e.tagName)) continue;
        if (e.closest("svg") && e.tagName !== "svg") continue;
        out.push((e.id ? "#" + e.id : "") + (typeof e.className === "string" && e.className ? "." + e.className.trim().split(/\s+/)[0] : e.tagName.toLowerCase()));
      }
      return out;
    };
  });
  const report = { beats: 0, lockup: {}, shots: [] };
  const slides = SLIDE ? list.filter((x) => x.id === SLIDE) : list;
  if (SLIDE && !slides.length) { console.error(`No slide "${SLIDE}". Slides: ${list.map((x) => x.id).join(" ")}`); process.exit(2); }
  if (SLIDE) fs.mkdirSync(OUT, { recursive: true });
  for (const s of slides) for (let k = 1; k <= s.n; k++) {
    at = `${s.id}/${k}`;
    await page.evaluate((i, k) => window.ACKO.go(i, k), s.i, k);
    await sleep(SLIDE ? WAIT[s.id] || 1500 : Math.min(WAIT[s.id] || 900, 2200));
    report.beats++;
    const hits = await page.evaluate(() => window.__lockHits());
    if (hits.length) report.lockup[at] = hits;
    if (SLIDE) { const file = path.join(OUT, `${s.id}_${k}_${W}x${H}.png`); await page.screenshot({ path: file }); report.shots.push(file); }
  }
  await browser.close();
  const lock = Object.entries(report.lockup);
  console.log(`${PAGE} at ${W}x${H}: ${report.beats} beats, ${errors.length} errors`);
  errors.forEach((e) => console.log("  ERROR " + e));
  lock.forEach(([k, v]) => console.log(`  ON THE LOGOS ${k}: ${v.join(", ")}`));
  if (report.shots.length) console.log(`  screenshots: ${OUT}`);
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
