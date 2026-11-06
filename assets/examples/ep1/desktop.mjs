// Episode 1 v2: ONE continuous real-time desktop take, paced to the voice.
// home (real-speed preloader) -> scroll -> recipe of the week -> open recipe -> 2x batch
// -> nav Recipes -> search "pumpkin" -> nav Shop -> add to bag -> nav Dashboard.
// Beat times (seconds into the take) live in T below, paced to the voice (optional overrides: shots/beats.json).
import fs from 'node:fs';
const B = fs.existsSync('shots/beats.json') ? JSON.parse(fs.readFileSync('shots/beats.json')) : {};   // optional overrides
const T = Object.assign({ scroll1: 4.2, down: 11.6, open: 14.0, x2: 18.7, navRecipes: 23.0, navShop: 32.2, add: 40.0, navDash: 43.0, end: 49.4 }, B);

export default async function (r) {
  const p = r.page;
  const sy = () => p.evaluate(() => scrollY);
  const top = (sel, i = 0) => p.evaluate(([s, i]) => { const e = document.querySelectorAll(s)[i]; return e.getBoundingClientRect().top + scrollY; }, [sel, i]);
  const navLink = href => `header nav a[href="${href}"]`;
  // glide to an element and press it exactly at take time `at`
  const pressAt = async (sel, at, glide = 0.9, i = 0) => { await r.until(at - glide - 0.2); await r.moveToAbs(sel, glide, 'sine', i); await r.until(at); await r.click(); };

  await r.goto('/', { fresh: true });
  r.mark('pre');
  await r.move(r.W * 0.62, r.H * 0.6, 0.01);
  // Hook: preloader at real speed, then ONE fast continuous scroll (~500 px/s) that never parks:
  // hero -> intro -> numbers -> recipe of the week opening -> stacking Recipes/Guides/Shop cards -> quick flick back up.
  const rotw = await top('#rotw');
  const cards = await p.evaluate(() => [...document.querySelectorAll('a')].find(a => /Browse recipes/.test(a.textContent)).closest('section').getBoundingClientRect().top + scrollY);
  await r.until(T.scroll1);
  r.mark('scroll1');
  const s1 = T.scroll1;
  await r.scrollPath([[s1, 0], [s1 + 1.4, 700], [s1 + 2.8, 1200], [s1 + 4.2, rotw + 150], [s1 + 6.0, cards + 500], [T.down, cards + 1150]],
    [[s1, r.W * 0.62, r.H * 0.6], [T.down, r.W * 0.7, r.H * 0.5]]);
  r.mark('rotw');
  await r.scrollPath([[T.down, cards + 1150], [T.down + 1.3, rotw - 40]], [[T.down, r.W * 0.7, r.H * 0.5], [T.down + 1.3, r.W * 0.6, r.H * 0.62]]);
  // L6 comment recipe -> land on the recipe
  r.mark('hover');
  await r.moveToAbs('#rotw .btn', 0.7, 'sine', 0);                 // label rolls on hover
  await r.until(T.open); r.mark('click'); await r.click();
  await r.until(T.open + 2.45);                                    // the real page transition
  r.mark('recipe');
  // L7 bigger batch
  const ing = await p.evaluate(() => { const h = [...document.querySelectorAll('h2')].find(e => /ingredients/i.test(e.textContent)); return h.getBoundingClientRect().top + scrollY - 110; });
  await r.scroll(ing - await sy(), 1.5, 'sine');
  await p.evaluate(() => { const b = s => [...document.querySelectorAll('button')].find(b => b.textContent.trim() === s); b('2×').setAttribute('data-rec', 'x2'); b('3×').setAttribute('data-rec', 'x3'); });
  r.mark('scale');
  await pressAt('[data-rec="x2"]', T.x2, 0.7);
  await pressAt('[data-rec="x3"]', T.x2 + 1.3, 0.45);
  // L8 searchable: scroll up a touch so the nav slides back in, then Recipes
  await r.hold(0.7);
  await r.scroll(-160, 0.6, 'sine');
  r.mark('navRecipes');
  await pressAt(navLink('/recipes'), T.navRecipes, 0.8);
  await r.until(T.navRecipes + 2.45);
  r.mark('library');
  const search = await top('input[aria-label="Search recipes"]');
  const t0 = r.now();                                              // browse the box (every card fades in), then back to search
  await r.scrollPath([[t0, await sy()], [t0 + 1.7, search + 740], [t0 + 2.9, search - 250]], [[t0, r.W * 0.5, r.H * 0.5], [t0 + 2.9, r.W * 0.3, r.H * 0.45]]);
  await r.moveToAbs('input[aria-label="Search recipes"]', 0.5, 'sine');
  await r.click(); await r.hold(0.15);
  r.mark('type'); await r.type('maple', 7);
  // L9 drop + shop
  await pressAt(navLink('/shop'), T.navShop, 0.8);
  r.mark('navShop');
  await r.until(T.navShop + 2.45);
  r.mark('shop');
  const drop = await top('#drop');
  await r.scroll(drop - 120 - await sy(), 1.4, 'sine');           // countdown ticking
  await r.hold(1.0);
  const card = await p.evaluate(() => { const b = [...document.querySelectorAll('button')].find(b => /Add to bag/.test(b.textContent)); return b.getBoundingClientRect().top + scrollY; });
  await r.scroll(card - 640 - await sy(), 1.4, 'sine');
  await p.evaluate(() => { const b = [...document.querySelectorAll('button')].find(b => /Add to bag/.test(b.textContent)); b.setAttribute('data-rec', 'add'); b.closest('.group').querySelector('img')?.setAttribute('data-rec', 'img'); });
  r.mark('hoverImg');
  await r.moveToAbs('[data-rec="img"]', 0.8, 'sine');               // photo eases in on hover
  await pressAt('[data-rec="add"]', T.add, 0.5);
  r.mark('add');
  // L10 dashboard
  await r.hold(1.2);
  await r.scroll(-160, 0.6, 'sine');
  await pressAt('header a[href="/dashboard"]', T.navDash, 0.9);
  r.mark('navDash');
  await r.until(T.navDash + 2.4);
  r.mark('dash');
  await r.move(r.W * 0.58, r.H * 0.64, 1.6, 'sine');
  await r.until(T.end);
  r.mark('end');
}
