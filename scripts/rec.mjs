// Frame-perfect screen recording of the running site.
// Playwright's fake clock drives every animation (GSAP, Lenis, rAF), so each frame is exactly 1/FPS s
// apart no matter how slow the screenshot is. Mouse moves are logged so a cursor can be drawn in the edit.
//
//   node tools/rec.mjs <shotlist.mjs> <outDir> [--fps 60] [--w 1440 --h 900 --dpr 1.5] [--mobile]
//
// The shot list module exports `default async function (r)` and uses the recorder API:
//   r.goto(path, {fresh})   load a route (fresh = preloader plays)      r.hold(sec)        let time run
//   r.scroll(px, sec, ease)  wheel-free smooth scroll via window.scrollTo r.move(x, y, sec)  glide the cursor
//   r.click()                click at the cursor                         r.mark(name)       name this frame
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const [shotFile, out] = a;
const FPS = +opt('--fps', 60), W = +opt('--w', 1440), H = +opt('--h', 900), DPR = +opt('--dpr', 1.5);
const MOBILE = a.includes('--mobile'), DRY = a.includes('--dry');
const BASE = opt('--base', 'http://localhost:3000');
fs.mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DPR, isMobile: MOBILE, hasTouch: MOBILE });
await ctx.addInitScript(() => document.addEventListener('DOMContentLoaded', () => {
  const s = document.createElement('style'); s.textContent = 'nextjs-portal{display:none!important}'; document.head.append(s);
}));
const page = await ctx.newPage();
let n = 0, mx = W / 2, my = H / 2, down = 0;
const log = [], marks = {};
const dt = 1000 / FPS;
const ease = { io: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2, lin: t => t, out: t => 1 - Math.pow(1 - t, 3), sine: t => -(Math.cos(Math.PI * t) - 1) / 2, soft: t => t * t * t * (t * (6 * t - 15) + 10) };

async function frame() {
  await page.clock.runFor(dt);
  if (!DRY || n % 30 === 0) await page.screenshot({ path: path.join(out, `f${String(n).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 92 });
  log.push({ n, x: mx, y: my, down: down > 0 ? 1 : 0 }); if (down > 0) down--;
  n++;
}
const r = {
  page, W, H,
  async goto(p, { fresh = false } = {}) {
    if (!fresh) await ctx.addInitScript(() => { try { sessionStorage.setItem('vgk-preloaded', '1'); } catch {} });
    await page.clock.install({ time: new Date('2026-11-07T10:00:00') });
    await page.clock.pauseAt(new Date('2026-11-07T10:00:01'));
    await page.goto(BASE + p, { waitUntil: 'commit' });
    await page.waitForLoadState('domcontentloaded');
    // let fonts/images arrive in real time while the fake clock is paused, so frame 1 is fully painted
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.evaluate(() => document.fonts.ready);
  },
  async hold(sec) { for (let i = 0; i < Math.round(sec * FPS); i++) await frame(); },
  async scroll(px, sec, e = 'io') {
    const y0 = await page.evaluate(() => scrollY), f = Math.round(sec * FPS);
    for (let i = 1; i <= f; i++) { const y = y0 + px * ease[e](i / f); await page.evaluate(y => scrollTo(0, y), y); await frame(); }
  },
  async scrollTo(sel, offset, sec, e = 'io') {
    const y = await page.evaluate(([s, o]) => document.querySelector(s).getBoundingClientRect().top + scrollY + o, [sel, offset]);
    await r.scroll(y - await page.evaluate(() => scrollY), sec, e);
  },
  async move(x, y, sec, e = 'io') {
    const x0 = mx, y0 = my, f = Math.max(1, Math.round(sec * FPS));
    for (let i = 1; i <= f; i++) { const t = ease[e](i / f); mx = x0 + (x - x0) * t; my = y0 + (y - y0) * t; await page.mouse.move(mx, my); await frame(); }
  },
  async click() { down = Math.round(0.12 * FPS); await page.mouse.down(); await frame(); await page.mouse.up(); },
  async tap() { await page.touchscreen.tap(mx, my); down = Math.round(0.15 * FPS); },
  async center(sel, i = 0) { return page.evaluate(([s, i]) => { const e = document.querySelectorAll(s)[i]; const b = e.getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2]; }, [sel, i]); },
  async moveTo(sel, sec, i = 0, dx = 0, dy = 0) { const [x, y] = await r.center(sel, i); await r.move(x + dx, y + dy, sec); },
  async waitFor(fn, maxSec = 6) { for (let i = 0; i < maxSec * FPS; i++) { if (await page.evaluate(fn)) return; await frame(); } },
  // hold until the take reaches `sec` (keeps a continuous take in sync with the voice); never cuts time
  async until(sec) { const f = Math.round(sec * FPS) - n; if (f < 0) console.log(`  late by ${(-f / FPS).toFixed(2)}s before mark at ${sec}s`); for (let i = 0; i < f; i++) await frame(); },
  now() { return n / FPS; },
  // type like a person: one key every 1/cps s
  async type(text, cps = 9) { for (const ch of text) { await page.keyboard.type(ch); await r.hold(1 / cps); } },
  async moveToAbs(sel, sec, e = 'io', i = 0) { const [x, y] = await r.center(sel, i); await r.move(x, y, sec, e); },
  // scroll along a smooth path of absolute [takeSec, scrollY] keys (monotone cubic, zero speed at both ends),
  // optionally drifting the cursor along [takeSec, x, y] keys at the same time. Never stops between keys.
  async scrollPath(keys, cur = null) {
    const mono = (K, t, j) => {
      const n = K.length; if (t <= K[0][0]) return K[0][j]; if (t >= K[n - 1][0]) return K[n - 1][j];
      const d = [], m = [];
      for (let i = 0; i < n - 1; i++) d.push((K[i + 1][j] - K[i][j]) / (K[i + 1][0] - K[i][0]));
      m.push(0); for (let i = 1; i < n - 1; i++) m.push(d[i - 1] * d[i] <= 0 ? 0 : 2 / (1 / d[i - 1] + 1 / d[i])); m.push(0);
      let i = 0; while (t > K[i + 1][0]) i++;
      const h = K[i + 1][0] - K[i][0], u = (t - K[i][0]) / h, u2 = u * u, u3 = u2 * u;
      return (2 * u3 - 3 * u2 + 1) * K[i][j] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * K[i + 1][j] + (u3 - u2) * h * m[i + 1];
    };
    const end = keys[keys.length - 1][0];
    while (n / FPS < end - 1e-6) {
      const t = (n + 1) / FPS;
      await page.evaluate(y => scrollTo(0, y), mono(keys, t, 1));
      if (cur) { mx = mono(cur, t, 1); my = mono(cur, t, 2); await page.mouse.move(mx, my); }
      await frame();
    }
  },
  mark(name) { marks[name] = n; console.log(`mark ${name} @ frame ${n} (${(n / FPS).toFixed(2)}s)`); },
};
const shots = (await import(pathToFileURL(path.resolve(shotFile)).href)).default;
await shots(r);
fs.writeFileSync(path.join(out, 'meta.json'), JSON.stringify({ fps: FPS, w: W, h: H, dpr: DPR, frames: n, marks, cursor: log }));
console.log(`${n} frames (${(n / FPS).toFixed(2)}s) -> ${out}`);
await browser.close();
