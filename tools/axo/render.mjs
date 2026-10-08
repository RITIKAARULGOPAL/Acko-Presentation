// Render the axo stills: every view × style, transparent background, as WebP.
// Usage: node render.mjs [outDir=../../renders] [width=2400] [only=<part of a name>]
// Needs `npm install` and `npm run bundle` (→ axo.bundle.js) first. Uses Playwright's Chromium with software WebGL.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(process.argv[2] || path.join(HERE, '../../renders'));
const W = +(process.argv[3] || 2400);
// every still: the four views in both styles, then the exploded layers (with room on the left for the layer labels)
const JOBS = [];
for (const view of ['floor', 'west', 'middle', 'east']) for (const style of ['ref', 'nb'])
  JOBS.push({ name: `axo-${view}-${style}`, q: `view=${view}&style=${style}`, w: W, h: Math.round(W * 0.5), padLeft: 0.01 });
JOBS.push({ name: 'axo-exploded-layers', q: 'view=floor&exploded=1', w: W, h: Math.round(W * 0.6), padLeft: 0.14, labels: true });

// Playwright: the project's own copy if present, else the global install
const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require(path.join(process.env.NPM_GLOBAL || '/usr/local/lib/node_modules', 'playwright')); }

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(HERE, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await pw.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
fs.mkdirSync(OUT, { recursive: true });
const ONLY = process.argv[4];   // optional: render only the stills whose name contains this
for (const job of JOBS.filter(j => !ONLY || j.name.includes(ONLY))) {
  const { w, h } = job;
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('pageerror', e => console.error('page error', e.message));
  await page.goto(`${base}/axo.html?${job.q}&w=${w}&h=${h}`);
  await page.waitForFunction(() => document.title === 'ready' || document.title.startsWith('error'), null, { timeout: 300000 });
  const title = await page.title();
  if (title !== 'ready') throw new Error(title);
  // trim the empty transparent margin (the whole-floor view is a long diagonal), keep a small border
  const res = await page.evaluate(padLeft => {
    const src = document.getElementById('c'), w = src.width, h = src.height;
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d'); x.drawImage(src, 0, 0);
    const a = x.getImageData(0, 0, w, h).data;
    let x0 = w, y0 = h, x1 = 0, y1 = 0;
    for (let y = 0; y < h; y++) for (let i = 0; i < w; i++) if (a[(y * w + i) * 4 + 3] > 8) { if (i < x0) x0 = i; if (i > x1) x1 = i; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    const p = Math.round(w * 0.01), pl = Math.round(w * padLeft);
    x0 = x0 - pl; y0 = Math.max(0, y0 - p); x1 = Math.min(w - 1, x1 + p); y1 = Math.min(h - 1, y1 + p);
    const o = document.createElement('canvas'); o.width = x1 - x0 + 1; o.height = y1 - y0 + 1;
    o.getContext('2d').drawImage(c, 0, 0, w, h, -x0, -y0, w, h);
    const labels = window.ax.anchors().map(l => ({ k: l.k, t: l.t, x: Math.round(l.at[0] - x0), y: Math.round(l.at[1] - y0) }));
    return { url: o.toDataURL('image/webp', 0.9), w: o.width, h: o.height, labels };
  }, job.padLeft);
  const file = path.join(OUT, job.name + '.webp');
  fs.writeFileSync(file, Buffer.from(res.url.split(',')[1], 'base64'));
  if (job.labels) fs.writeFileSync(path.join(OUT, job.name + '.json'), JSON.stringify({ w: res.w, h: res.h, labels: res.labels }) + '\n');
  console.log(file, Math.round(fs.statSync(file).size / 1024) + ' KB');
  await page.close();
}
await browser.close(); server.close();
