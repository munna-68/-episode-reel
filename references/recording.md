# Recording the takes

## How the recorder works
`tools/rec.mjs` drives Chromium with Playwright on a **fake clock**: `page.clock.install` and `pauseAt` run before the page loads, then `clock.runFor(1000/60)` and one screenshot per frame. Every GSAP, Lenis and rAF animation is therefore frame-exact at 60 fps however slow the screenshots are, and the real-time preloader comes out at true speed. The mouse path and presses are logged to `meta.json`, so the compositor can draw a cursor and click ripple, since headless Chromium has no visible cursor.

```
node tools/rec.mjs shots/desktop.mjs footage/desk                         # 1440x900 @ DPR 1.5 (2160 px wide: sharp at 2x zoom)
node tools/rec.mjs shots/mobile.mjs footage/mob --mobile --w 390 --h 693 --dpr 2.7692   # 1080x1919 phone
add --dry to screenshot only every 30th frame (fast pacing check); add --base http://localhost:3001 for another port
```
A real desktop take of about 50 s takes about 6–8 min to record. Run it in the background and watch for "frames (" in the log.

## Shot-list API (`export default async function (r)`)
| call | does |
|---|---|
| `r.goto(path, {fresh})` | load a route; `fresh: true` lets the preloader play (first load only) |
| `r.hold(sec)` / `r.until(sec)` | let time run / hold until the take reaches `sec` (prints "late by…" if already past) |
| `r.scroll(px, sec, ease)` / `r.scrollTo(sel, offset, sec)` | eased scroll by `window.scrollTo` each frame |
| `r.scrollPath([[t,y],…], [[t,x,y],…])` | **use this for any long scroll**: smooth monotone path through absolute take times, never stops between keys, optionally drifts the cursor along with it |
| `r.move(x,y,sec,ease)` / `r.moveToAbs(sel, sec, ease, i)` | glide the cursor (hover states trigger for real) |
| `r.click()` / `r.tap()` | press at the cursor (desktop / touch) |
| `r.type(text, cps)` | type like a person |
| `r.mark(name)` | name this frame: `edit.json` refers to marks |
| `r.now()`, `r.page`, `r.W`, `r.H` | current take time, the Playwright page, the viewport |
Eases: `sine` (default choice), `io`, `soft`, `out`, `lin`.

Helpers worth copying from `assets/examples/ep1/desktop.mjs`:
- `pressAt(sel, at, glide)`: glide to an element and press exactly at take time `at`.
- `top(sel)`: an element's page-Y position.
- Tag hard-to-select elements first with `page.evaluate(() => el.setAttribute('data-rec', 'x'))`. This marks the DOM in the browser only and never edits the repo.

## Pacing the take to the voice
1. Voice first: you know each line's duration from `audio/timing_tight.json`.
2. Put the beat times in a `T` object at the top of the shot list (when to start scrolling, when to press each button, when to click each nav link).
3. Use `r.until(T.x)` before each beat, so the take is never early. A "late by" warning means the actions take longer than the voice allows: move the beat later or speed up the action.
4. Dry-run, read the marks, adjust, repeat (each dry run is about 2 min).
5. After the real recording, set `audio/starts.json` so each line lands on its action. For example, "land right on the recipe" is said about 1.5 s into its line, so that line starts about 1.5 s before the `click` mark. Keep line gaps at 0.25 s or more and check there's no overlap (`place_vo.py` asserts this).

A page transition by click → `router.push` takes about 2.45 s in ep 1's site (panels in, label, panels out). `r.until(T.navX + 2.45)` before acting on the new page.

## The opening (the hook): get this right
- Preloader at real speed with `fresh: true`. No slow motion.
- Start scrolling the moment the hero has landed (about 4.2 s in ep 1).
- One `scrollPath` through the best sections at roughly 500 px/s, never parking, ending on the section that shows "everything in one place". A quick flick back up to the first click is fine.
- First click (into the first feature) by about 14 s.

## Dry-run contact sheets (look before you record)
```
ffmpeg -v error -y -pattern_type glob -i 'footage/dry/f*.jpg' -vf "scale=240:-1,tile=8x6:padding=4" -frames:v 1 sheet.jpg
```
Read the image, then check:
- the nav is visible before each nav click (it often hides on scroll down; a short `r.scroll(-160, 0.6)` brings it back);
- hover states fire;
- every filter or search result is fully shown;
- nothing sits still for more than about 0.8 s.

## Glitch patterns seen so far (the site's own behaviour, fixed without touching it)
- **Scroll-reveal plus filter (FLIP):** cards below the fold have not faded in yet, a search pulls them up, and they stay invisible. A FLIP with `absolute: true` also briefly collapses the grid, so the footer jumps up over it on every keystroke.
  Fix:
  1. Browse the grid first (scroll down past every card, then back up to the search box).
  2. Zoom tight on the search box (2.0x) while typing, until about 0.8 s after the last key.
  3. Verify by scanning every frame for dark pixels in the window area. A PIL script over `out/frames` for that time range takes seconds.
- **Preloader handoff artifacts:** in ep 1, after the dive through the I, leftover letter-mask pieces slid over the photo for about 0.4 s. Fix: the `stitch` block in `edit.json`. Freeze the last clean dive frame `a`, zoom it about the letter's centre, and dissolve into frames `b0`→`b1` across output frames `k0`→`k1`.
  Find the centre from the frames: bright-pixel runs on the middle row and column. Find the bad range by tiling every 3rd source frame.
- **Nav hide-on-scroll:** scroll up a touch before clicking a nav link.
- **Live widgets** (feeds, countdowns): fine and nice to show, but their numbers are demo data. Label them.

## The phone take
- About 14 s, `goto('/')` without `fresh` (the preloader was already shown on desktop).
- Hold 1.7 s for the hero.
- Scroll through intro → stacking cards → footer with `sine` scrolls. The footer usually ends the video under the CTA.
- No taps needed. If you tap, the compositor draws no touch dot.

## After recording
```
tools/blend.sh footage/desk footage/desk30      # 60 -> 30 fps, 2-frame blend = natural motion blur
tools/blend.sh footage/mob footage/mob30
```
Delete dry-run folders once the real take is in. Keep older takes only while a version is still being compared (each take is about 1–2 GB of JPEGs).
