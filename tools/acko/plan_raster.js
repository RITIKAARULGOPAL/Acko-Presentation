// The DXF plan as pictures: renders the toolkit's full.svg (a crop of it, in its mm frame) at each px-per-metre level
// into <out_dir>/plan-<ppm>.png, transparent. Called by tools/acko/plan_dxf.py.
//
//   node tools/acko/plan_raster.js <full.svg> <out_dir> <x0> <y0> <w> <h> <ppm>[,<ppm>...]
// needs puppeteer-core: NODE_PATH=C:/Users/Ritika/Mitigata/node_modules
const fs = require("fs"), path = require("path"), puppeteer = require("puppeteer-core");
(async () => {
  const [src, outDir, x0, y0, w, h, levels] = process.argv.slice(2);
  const raw = fs.readFileSync(src, "utf8");
  const b = await puppeteer.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: "new",
    args: ["--allow-file-access-from-files", "--force-device-scale-factor=1"] });
  for (const ppm of levels.split(",").map(Number)) {
    const W = Math.round((+w / 1000) * ppm), H = Math.round((+h / 1000) * ppm);
    const svg = raw.replace(/viewBox="[^"]*"/, `viewBox="${x0} ${y0} ${w} ${h}" width="${W}" height="${H}"`);
    // transparent paper, so coloured rooms can sit beneath; wipeouts stay white
    const html = `<!doctype html><html><head><style>html,body{margin:0;background:transparent}svg{display:block}
      .pf{background:transparent!important}.m{fill:#fff!important}</style></head><body>${svg}</body></html>`;
    const tmp = path.join(outDir, `_plan-${ppm}.html`); fs.writeFileSync(tmp, html);
    const p = await b.newPage(); await p.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
    await p.goto("file:///" + tmp.split("\\").join("/"), { waitUntil: "load", timeout: 300000 });
    await p.screenshot({ path: path.join(outDir, `plan-${ppm}.png`), omitBackground: true, clip: { x: 0, y: 0, width: W, height: H } });
    await p.close(); fs.unlinkSync(tmp);
    console.log(`plan-${ppm}.png ${W}x${H}`);
  }
  await b.close();
})();
