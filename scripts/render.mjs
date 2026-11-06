// Render the reel frame by frame from comp/one.html + comp/one.js (run from the episode folder).
//   node tools/render.mjs stills 15 300 900 ...   -> out/stills/sNNNNN.png   (output frame numbers, 30 fps)
//   node tools/render.mjs film [from] [to]        -> out/frames/fNNNNN.jpg   (~1 min per 1000 frames)
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const [mode, ...rest] = process.argv.slice(2);
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto(`file://${encodeURI(root)}/comp/one.html`);
await p.evaluate(() => document.fonts.ready);
const total = await p.evaluate(() => EDIT.frames);
let frames;
if (mode === 'stills') frames = rest.map(Number);
else { const a = +(rest[0] ?? 0), z = +(rest[1] ?? total - 1); frames = []; for (let i = a; i <= z; i++) frames.push(i); }
const dir = path.join(root, 'out', mode === 'stills' ? 'stills' : 'frames'); fs.mkdirSync(dir, { recursive: true });
const t0 = Date.now();
for (const f of frames) {
  await p.evaluate(f => seek(f), f);
  const file = path.join(dir, `${mode === 'stills' ? 's' : 'f'}${String(f).padStart(5, '0')}.${mode === 'stills' ? 'png' : 'jpg'}`);
  await p.screenshot(mode === 'stills' ? { path: file } : { path: file, type: 'jpeg', quality: 93 });
  if (mode !== 'stills' && f % 300 === 0) console.log(`frame ${f}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}
console.log(`${frames.length} frames -> ${dir}`);
await b.close();
