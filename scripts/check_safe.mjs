// Measure captions, chips, the problem graphic and the CTA against the Instagram Reels safe zone
// (top 220 px, bottom 420 px, right 140 px; captions may use the full width). Run from the episode folder.
import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto(`file://${encodeURI(process.cwd())}/comp/one.html`); await p.evaluate(() => document.fonts.ready);
const res = await p.evaluate(async () => {
  const bad = [], probes = EDIT.chunks.map(c => Math.round((c.t0 + c.t1) / 2 * EDIT.fps));
  EDIT.cards.forEach(c => probes.push(Math.round((c[0] + 0.5) * EDIT.fps)));
  if (EDIT.scatter) probes.push(Math.round((EDIT.scatter.merge - 0.3) * EDIT.fps));
  if (EDIT.cta) probes.push(Math.round((EDIT.cta.t + 1) * EDIT.fps));
  probes.push(EDIT.frames - 1);
  const box = el => { if (el.classList.contains('s') || el.classList.contains('cta')) { const g = document.createRange(); g.selectNodeContents(el); return g.getBoundingClientRect(); } return el.getBoundingClientRect(); };
  for (const f of probes) {
    await seek(f);
    for (const el of document.querySelectorAll('#cap span, #cap, .card b, .card .s, .tile, .pill, .lock, .cta')) {
      const r = box(el); if (!r.width || getComputedStyle(el).display === 'none') continue;
      if (r.top < 219 || r.bottom > 1501 || r.left < 39 || (el.id !== 'cap' && r.right > 941))
        bad.push(`f${f} ${el.className || el.id} [${r.left | 0},${r.top | 0} -> ${r.right | 0},${r.bottom | 0}]`);
    }
  }
  return { n: probes.length, bad };
});
console.log(`${res.n} frames probed, ${res.bad.length} out-of-zone`); res.bad.slice(0, 20).forEach(x => console.log('  ' + x));
await b.close();
