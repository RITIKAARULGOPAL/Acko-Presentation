// Render the furniture layer written by import_plan_hover.py (tools/_raster/opt{1,2}.svg) into the
// white-on-transparent textures the plan and the 3D twin use: assets/plans/opt{1,2}_furn.png (80 px/m).
// Usage (from the project folder):  node tools/raster_plan.js        (needs: npm i puppeteer-core)
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");
const ROOT = path.join(__dirname, "..");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: "new", args: ["--allow-file-access-from-files"],
  });
  const page = await browser.newPage();
  for (const opt of ["opt1", "opt2"]) {
    const svg = fs.readFileSync(path.join(__dirname, "_raster", `${opt}.svg`), "utf8");
    await page.setContent(`<!doctype html><body style="margin:0;background:#000">${svg}</body>`);
    const b64 = await page.evaluate(async () => {
      const svg = document.querySelector("svg"), NS = "http://www.w3.org/2000/svg";
      // browsers ignore non-scaling strokes inside <use>: expand every instance into a plain group first
      const defs = new Map([...svg.querySelectorAll("defs > g[id]")].map((g) => [g.id, g]));
      svg.querySelectorAll("use").forEach((u) => {
        const src = defs.get((u.getAttribute("href") || "").slice(1)), g = document.createElementNS(NS, "g");
        g.setAttribute("transform", u.getAttribute("transform") || "");
        if (src) for (const ch of src.children) g.appendChild(ch.cloneNode(true));
        u.replaceWith(g);
      });
      svg.querySelector("defs")?.remove();
      const W = +svg.getAttribute("width"), H = +svg.getAttribute("height");
      const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: "image/svg+xml" }));
      const img = new Image(); img.src = url; await img.decode();
      const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
      const g = cv.getContext("2d"); g.drawImage(img, 0, 0, W, H);
      // white lines on black -> white on transparent (alpha = brightness), like the DXF rasteriser
      const im = g.getImageData(0, 0, W, H), d = im.data;
      for (let i = 0; i < d.length; i += 4) { const a = Math.max(d[i], d[i + 1], d[i + 2]); d[i] = d[i + 1] = d[i + 2] = 255; d[i + 3] = a; }
      g.putImageData(im, 0, 0);
      return cv.toDataURL("image/png").split(",")[1];
    });
    const out = path.join(ROOT, "assets", "plans", `${opt}_furn.png`);
    fs.writeFileSync(out, Buffer.from(b64, "base64"));
    console.log(opt, "->", path.relative(ROOT, out), Math.round(fs.statSync(out).size / 1024), "KB");
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
