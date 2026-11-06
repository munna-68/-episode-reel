// Episode 1 v2 mobile: one continuous take on a phone viewport, home hero -> intro -> stacking cards -> footer.
export default async function (r) {
  const p = r.page;
  const sy = () => p.evaluate(() => scrollY);
  const top = sel => p.evaluate(s => document.querySelector(s).getBoundingClientRect().top + scrollY, sel);
  await r.goto('/');
  r.mark('hero');
  await r.hold(1.7);                                             // hero letters rise
  r.mark('scroll');
  await r.scroll(await top('.intro-text') - 150 - await sy(), 2.2, 'sine');
  await r.hold(0.2);
  const cards = await p.evaluate(() => { const a = [...document.querySelectorAll('a')].find(a => /Browse recipes|See the guides|Visit the shop/.test(a.textContent)); return a.closest('section').getBoundingClientRect().top + scrollY; });
  await r.scroll(cards - await sy(), 2.4, 'sine');
  r.mark('cards');
  await r.scroll(r.H * 2.4, 3.6, 'sine');                         // cards stack and sink back
  r.mark('footer');
  const end = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
  await r.scroll(end - await sy(), 2.6, 'sine');                   // wordmark rises out of the bottom
  await r.hold(1.6);
  r.mark('end');
}
