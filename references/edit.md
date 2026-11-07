# The edit (`edit.json` → `tools/build_edit.py` → `comp/one.js` → `comp/one.html`)

The compositor is frame-pure: `seek(k)` draws output frame k. Output time equals take time, with no remapping.

## Layout (1080x1920; the layout is fixed across the series, the colours and fonts are per client)
- **Desktop window:** left 20, top 560, 1040 wide. A 34 px browser bar with a fake address (`domain` + the slug for the current page), then a 650 px view. It never moves or resizes, and nothing animates in on cuts.
- **Top zone (y 220–540):** one chip plus a script subtitle at a time (cards), or the problem graphic, or the CTA.
- **Captions:** top 1290, Archivo wide caps 66 px, the active word in the accent colour, max 4 words per chunk. Over the phone they get a dark band.
- **Phone:** full bleed (1080x1919), crossfades in over `xf` s. Its chips get a dark gradient band so they stay readable.
- **Instagram safe zone:** top 220, bottom 420, right 140. `node tools/check_safe.mjs` must report 0.

## Time expressions
A number (`4.2`), a take mark (`"hover-0.2"`, `"navShop+1.0"`), a voice line (`"line:04"`, `"lineend:04+0.2"`), or `cut` (end of the desktop take), `mob0` (phone start = cut − xf), `dur`.

## `edit.json` keys
```jsonc
{
  "domain": "valleygirlkitchen.com",                 // shown in the address bar
  "urls": [[0, ""], ["recipe", "/recipes/x"]],       // [mark, slug]: the slug shows from 0.2 s before that mark
  "xf": 0.4,                                         // desktop -> phone crossfade (s)
  "zooms": [{"from": "hover-0.2", "to": "click+0.55", "zoom": 1.55}],
  "cards": [{"from": 0.25, "to": "line:03-0.3", "chip": "EPISODE 1", "sub": "Valley Girl Kitchen"}],
  "scatter": {"from": "line:03", "merge": "line:04", "pill": "🔗 one link in bio",
              "tiles": ["Recipes", "Drops", "Shop"], "small": "another platform",
              "lock": {"at": "line:03+2.5", "text": "🔒 make an account"}},   // lock is optional
  "cta": {"at": "line:12", "html": "Drop a business <em>below</em><br>for episode 3 👇"},
  "stitch": {"k0": 70, "k1": 83, "a": 69, "b0": 81, "b1": 83, "ox": 330, "oy": 458, "zmax": 12},  // optional
  "theme": {...},                                    // per-client look (required); {} = ep 1 espresso look
  "music": {"style": "deep", "bpm": 104},
  "sfx": {"transitions": ["click", "navShop"], "boom": 2.3, "keys": [{"at": "type+0.02", "n": 5}],
          "thock": ["add+0.05"], "ticks": [{"at": "navDash+1.5", "n": 16}]}
}
```
Optional tuning: `zoom_ramp` (0.8 s), `cursor_smooth` (Gaussian sigma, 0.28 s), `trim_end` (0.2 s).

### Zooms
Use them only around an interaction: hovering and pressing a button, typing, a product hover, the batch buttons. Start about 0.2 s before the cursor arrives and end before the next page transition. Levels: 1.45–1.7, or 2.0 to frame out a glitch. The camera follows the smoothed cursor, so make the shot list's cursor sit on the thing being shown.

### Cards (top-zone chips)
- Use one per section, named by the page or benefit ("THE RECIPE / no app, no login", "SHOP & DROPS / one tap from any recipe", "DASHBOARD / demo numbers", "ON A PHONE / same site, same feel").
- The first card is "EPISODE N / <Business>".
- Chip text is short caps; the subtitle is a 2–5 word script phrase. Don't repeat the caption word for word.
- Leave the top zone empty under the scatter graphic and the CTA.

### Stitch
To cover a short glitch in the take, use output frame numbers (30 fps). Desk30 frame index k corresponds to source frames 2k−1 and 2k.
- `a`: the last clean frame, frozen and zoomed by up to `zmax` about (`ox`, `oy`) in site CSS px.
- `b0`→`b1`: the frames it dissolves into.
- Keep `k1 − k0` around 13 frames (0.43 s) so real time barely shifts.

### Theme (every episode: built from the client's site)
Keys, with the defaults shown in `comp/one.html`:
- `fonts` (a Google Fonts CSS URL, `display=block`)
- `bgInner`, `bgMid`, `bgOuter` (the radial studio background: keep it dark so the light site window pops)
- `accent`, `accentInk` (chip fill and text, active caption word, script subtitle, click ripple)
- `capFont`, `capStretch`, `capWeight`, `capSize` (66px), `capInk` (caption words), `capOn` (active word; defaults to `accent`), `scriptFont`, `subSize` (60px; use about 38px for a mono font)
- `tile`, `tileInk`, `tileSmall`, `lock`
- `bar`, `barDots`, `urlBg`, `urlInk`, `viewBg`

- `chipSize` (28px), `ctaSize` (58px)

How to derive each key from the client's site is in SKILL.md → step 5, "Design this episode's look". Never reuse another episode's theme. Contrast check: captions, the spoken word and the subtitle must read at phone size over `bgMid`. Example: `assets/examples/ep2/edit.json`.

## Building and checking
```
python3 tools/build_edit.py                  # prints frames, duration, zoom windows (bad marks fail loudly)
node tools/render.mjs stills 15 300 600 ...   # PNGs in out/stills (frame = seconds x 30)
node tools/check_safe.mjs
```
Tile stills into a sheet for the user, for example:
```
ffmpeg -pattern_type glob -i 'out/stills/s*.png' -vf "scale=360:-1,tile=6x1:padding=6" sheet.jpg
```

## Audio
`python3 tools/make_audio.py` does three things:
- builds the bed for the full length, with a fill into the phone and a ring-out at the end;
- mixes the placed voice at the locked balance;
- adds SFX: a click on every real mouse press, a whoosh 0.62 s after each mark in `transitions`, a whoosh into the phone, and a shimmer under the CTA.

`tools/finish.sh` masters to −14 LUFS (true peak about −1 to −1.5), muxes H.264 crf 17 + AAC 256k, then prints the probe, loudness, silent gaps (target 0) and black frames (target 0).
