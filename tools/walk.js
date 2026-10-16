// Headless check of the presentation in this checkout (main folder or any worktree), from file://.
//
//   node tools/walk.js                         every beat of every slide, both options: console errors, failed requests,
//                                              anything sitting on the logo lockup; exits 1 on any error
//   node tools/walk.js --slide s-site          one slide: each beat screenshotted (to --out), plus its errors and copy overflow
//   options: --out <dir>  --size 1366x768  --opt opt2
//
// Needs node and puppeteer-core (C:\Users\Ritika\Mitigata\node_modules; worktrees inside the repo find it) and Chrome.
const path = require("path"), fs = require("fs"), os = require("os");
const puppeteer = require("puppeteer-core");

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const SLIDE = arg("--slide"), [W, H] = arg("--size", "1600x900").split("x").map(Number), OPT = arg("--opt", "opt1");
const OUT = arg("--out", path.join(os.tmpdir(), "mitigata-walk", SLIDE || "all"));
// index.html is built from slides/ (tools/build.py): build it first so the walk sees the current slides
require("child_process").execFileSync(process.env.PYTHON || "python", [path.join(__dirname, "build.py")], { stdio: "inherit" });
const PAGE = "file:///" + path.resolve(__dirname, "..", "index.html").replace(/\\/g, "/");
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
// slides whose beats animate for a while before they settle
const WAIT = { "s-open": 4600, "s-site": 2800, "s-values": 4800, "s-idea": 5600, "s-twin": 3600, "s-soc": 4600, "s-lantern": 900, "s-spaces": 5200, "s-ex": 2400, "s-stories": 1800,
  "s-carve": 1600, "s-arc": 3800, "s-net": 3800, "s-mitigata": 2600, "s-part1": 900, "s-part2": 900, "s-part3": 900, "s-part4": 900, "s-thanks": 900, "s-living": 4200, "s-layers": 3400,
  "s-w-arrival": 5200, "s-w-soc": 5200, "s-w-boardroom": 5200, "s-w-meeting": 5200, "s-w-breakout": 5200, "s-w-studio": 2400 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--allow-file-access-from-files"], defaultViewport: { width: W, height: H } });
  const page = await browser.newPage();
  const errors = [];
  let at = "load";
  page.on("pageerror", (e) => errors.push(`${at}: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${at}: ${m.text()}`); });
  // a paused audio / video stream has its open download dropped by Chrome (net::ERR_ABORTED): normal, not an error
  const mediaAbort = (r) => /\.(mp3|m4a|ogg|mp4|webm)$/i.test(r.url()) && (r.failure() || {}).errorText === "net::ERR_ABORTED";
  page.on("requestfailed", (r) => { if (!mediaAbort(r)) errors.push(`${at}: FAILED ${r.url()}`); });
  await page.goto(PAGE, { waitUntil: "load" });
  await sleep(1500);
  const list = await page.evaluate(() => [...document.querySelectorAll(".scene")].map((s, i) => ({ i, id: s.id, n: +s.dataset.steps || 1, title: s.dataset.title })));
  await page.evaluate(() => {   // anything visible sitting on the bottom-right logo lockup
    window.__lockHits = () => {
      const L = document.querySelector(".lockup"); if (!L) return [];
      const lr = L.getBoundingClientRect(), pad = 4, big = innerWidth * innerHeight * 0.2, out = [];
      const hit = (r) => r.right > lr.left - pad && r.left < lr.right + pad && r.bottom > lr.top - pad && r.top < lr.bottom + pad;
      const shown = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement) { const cs = getComputedStyle(n); if (cs.display === "none" || cs.visibility === "hidden" || +cs.opacity < 0.05) return false; } return true; };
      for (const root of [document.querySelector(".scene.active"), document.getElementById("world")])
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
  const report = { page: PAGE, size: `${W}x${H}`, beats: 0, lockup: {}, overflow: [], shots: [] };

  if (SLIDE) {
    const s = list.find((x) => x.id === SLIDE);
    if (!s) { console.error(`No slide "${SLIDE}". Slides: ${list.map((x) => x.id).join(" ")}`); process.exit(2); }
    fs.mkdirSync(OUT, { recursive: true });
    await page.evaluate((o) => window.MX.setOpt(o), OPT);
    for (let k = 1; k <= s.n; k++) {
      at = `${s.id}/${k}`;
      await page.evaluate((i, k) => window.MX.go(i, k), s.i, k);
      await sleep(WAIT[s.id] || 1500);
      report.beats++;
      const info = await page.evaluate(() => {
        const sc = document.querySelector(".scene.active"), copy = sc.querySelector(".copy");
        return { bottom: copy ? Math.round(copy.getBoundingClientRect().bottom) : 0, lock: window.__lockHits() };
      });
      if (info.bottom > H - 40) report.overflow.push(`${at}: copy ends at ${info.bottom}px`);
      if (info.lock.length) report.lockup[at] = info.lock;
      const file = path.join(OUT, `${s.id}_${k}_${W}x${H}.png`);
      await page.screenshot({ path: file }); report.shots.push(file);
    }
  } else {
    for (const opt of ["opt1", "opt2"]) {
      await page.evaluate((o) => window.MX.setOpt(o), opt);
      for (const s of list) for (let k = 1; k <= s.n; k++) {
        at = `${s.id}/${k} (${opt})`;
        await page.evaluate((i, k) => window.MX.go(i, k), s.i, k);
        await sleep(opt === "opt1" ? (WAIT[s.id] || 900) : 250);
        report.beats++;
        if (opt === "opt1") { const hits = await page.evaluate(() => window.__lockHits()); if (hits.length) report.lockup[`${s.id}/${k}`] = hits; }
      }
    }
  }
  await browser.close();

  const lock = Object.entries(report.lockup);
  console.log(`${report.page} at ${report.size}: ${report.beats} beats, ${errors.length} errors`);
  errors.forEach((e) => console.log("  ERROR " + e));
  report.overflow.forEach((o) => console.log("  OVERFLOW " + o));
  lock.forEach(([k, v]) => console.log(`  ON THE LOGOS ${k}: ${v.join(", ")}`));
  if (report.shots.length) console.log(`  screenshots: ${OUT}`);
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
