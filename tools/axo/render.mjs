// Render the axo stills: every view × style, transparent background, as WebP.
// Usage: node render.mjs [outDir=../../renders] [width=2400]
// Needs `npm install` and `npm run bundle` (→ axo.bundle.js) first. Uses Playwright's Chromium with software WebGL.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(process.argv[2] || path.join(HERE, '../../renders'));
const W = +(process.argv[3] || 2400);
const VIEWS = { floor: [W, Math.round(W * 0.5)], west: [W, Math.round(W * 0.5)], middle: [W, Math.round(W * 0.5)], east: [W, Math.round(W * 0.5)] };
const STYLES = ['ref', 'nb'];

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
for (const [view, [w, h]] of Object.entries(VIEWS)) for (const style of STYLES) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('pageerror', e => console.error('page error', e.message));
  await page.goto(`${base}/axo.html?view=${view}&style=${style}&w=${w}&h=${h}`);
  await page.waitForFunction(() => document.title === 'ready' || document.title.startsWith('error'), null, { timeout: 300000 });
  const title = await page.title();
  if (title !== 'ready') throw new Error(title);
  // trim the empty transparent margin (the whole-floor view is a long diagonal), keep a small border
  const url = await page.evaluate(() => {
    const src = document.getElementById('c'), w = src.width, h = src.height;
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d'); x.drawImage(src, 0, 0);
    const a = x.getImageData(0, 0, w, h).data;
    let x0 = w, y0 = h, x1 = 0, y1 = 0;
    for (let y = 0; y < h; y++) for (let i = 0; i < w; i++) if (a[(y * w + i) * 4 + 3] > 8) { if (i < x0) x0 = i; if (i > x1) x1 = i; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    const p = Math.round(w * 0.01); x0 = Math.max(0, x0 - p); y0 = Math.max(0, y0 - p); x1 = Math.min(w - 1, x1 + p); y1 = Math.min(h - 1, y1 + p);
    const o = document.createElement('canvas'); o.width = x1 - x0 + 1; o.height = y1 - y0 + 1;
    o.getContext('2d').drawImage(c, x0, y0, o.width, o.height, 0, 0, o.width, o.height);
    return o.toDataURL('image/webp', 0.9);
  });
  const file = path.join(OUT, `axo-${view}-${style}.webp`);
  fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
  console.log(file, Math.round(fs.statSync(file).size / 1024) + ' KB');
  await page.close();
}
await browser.close(); server.close();
