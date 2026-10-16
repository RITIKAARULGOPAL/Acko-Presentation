// Capture label-free satellite stills of Sattva Hallmark at several zoom levels.
// Usage: node capture_sat.js <outdir> [--at lat,lng] [--zooms 20] [--name site]
//   default: the zoom stack centred on the place pin (sat_z12 ... sat_z19)
//   --at / --zooms / --name: e.g. the close still of the floor plate (site_z20) used under the plan
const puppeteer = require("puppeteer-core");
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const [LAT, LNG] = arg("--at", "12.9366189,77.6916687").split(",").map(Number);
const ZOOMS = arg("--zooms", "12,14,16,18,19").split(",").map(Number);
const NAME = arg("--name", "sat");
const out = process.argv[2];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: "new", args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--window-size=1920,1080"],
    defaultViewport: { width: 1920, height: 1080 },
  });
  const page = await browser.newPage();
  for (const z of ZOOMS) {
    await page.goto(`https://www.google.com/maps/@${LAT},${LNG},${z}z/data=!3m1!1e3`, { waitUntil: "networkidle2", timeout: 90000 });
    await sleep(3500);
    // labels off (control lives in the layers widget; click it programmatically)
    const toggled = await page.evaluate(() => {
      const el = [...document.querySelectorAll("button, [role=button], [role=menuitemcheckbox], [role=checkbox], label")]
        .find((e) => ((e.getAttribute("aria-label") || e.textContent || "").trim()) === "Labels");
      if (!el) return "no-labels-control";
      const on = el.getAttribute("aria-checked");
      if (on !== "false") el.click();
      return "clicked:" + on;
    });
    await sleep(3500);
    // hide every overlay that isn't the map canvas or one of its ancestors
    await page.evaluate(() => {
      const canvas = [...document.querySelectorAll("canvas")].sort((a, b) => b.width * b.height - a.width * a.height)[0];
      document.querySelectorAll("body *").forEach((e) => {
        if (e === canvas || e.contains(canvas) || canvas.contains(e)) return;
        e.style.visibility = "hidden";
      });
    });
    await sleep(1500);
    await page.screenshot({ path: `${out}/${NAME}_z${z}.png` });
    console.log("z", z, toggled);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
