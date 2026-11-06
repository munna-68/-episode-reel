#!/usr/bin/env python3
"""Edit data for comp/one.html: one continuous desktop take, one crossfade into the phone take.

  python3 tools/build_edit.py            (run from the episode folder) -> comp/one.js

Inputs (standard episode layout):
  edit.json                     what the edit adds on top of the takes (zooms, cards, graphic, CTA, theme, sfx)
  footage/desk/meta.json        60 fps desktop take (marks + cursor log from tools/rec.mjs)
  footage/mob/meta.json         60 fps phone take
  audio/timing.json, audio/words.json   placed voice lines + caption chunks

Output time == take time. Nothing is time-remapped (no slow motion). Output frame k shows desk30/f{k+1}.jpg,
i.e. source frames 2k-1 and 2k blended (tools/blend.sh), which gives natural motion blur on scrolls.

Time expressions in edit.json (strings):
  "4.2"            absolute seconds
  "hover-0.2"      a mark from the desktop take (shot list r.mark('hover')), plus/minus seconds
  "line:04+0.3"    start of voice line 04;  "lineend:04" its end
  "cut", "mob0", "dur"   desktop end, phone start (= cut - xf), video end
Camera: zoom is 1 except inside "zooms" windows; it eases in/out (smootherstep, RAMP s) and centres on the
cursor path smoothed with a Gaussian, so the frame drifts with the mouse instead of jumping.
"""
import json, math, re, os

FPS = 30
C = json.load(open('edit.json'))
D = json.load(open('footage/desk/meta.json')); M = json.load(open('footage/mob/meta.json'))
W = json.load(open('audio/words.json')); L = {r['line']: r for r in json.load(open('audio/timing.json'))}
XF = C.get('xf', 0.4); RAMP = C.get('zoom_ramp', 0.8)
CUT = D['frames'] / 60
MOB0 = CUT - XF
DUR = round(MOB0 + M['frames'] / 60 - C.get('trim_end', 0.2), 2)
FR = int(DUR * FPS)
marks = {k: v / 60 for k, v in D['marks'].items()}

import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeexpr import resolver
T = resolver(marks, list(L.values()), {'cut': CUT, 'mob0': MOB0, 'dur': DUR})

ss = lambda u: (lambda v: v * v * v * (v * (v * 6 - 15) + 10))(min(1, max(0, u)))
ZOOMS = [(T(z['from']), T(z['to']), z['zoom']) for z in C.get('zooms', [])]
def zoom_at(t):
    z = 1.0
    for a, b, zz in ZOOMS:
        env = min(ss((t - a) / RAMP), 1 - ss((t - (b - RAMP)) / RAMP))
        z = max(z, 1 + (zz - 1) * env)
    return z

cur = D['cursor']; n = len(cur); sig = C.get('cursor_smooth', 0.28) * 60; R = int(3 * sig)
gk = [math.exp(-(i * i) / (2 * sig * sig)) for i in range(-R, R + 1)]
def smooth(i, key):
    s = w = 0
    for j, g in zip(range(i - R, i + R + 1), gk):
        s += cur[min(n - 1, max(0, j))][key] * g; w += g
    return s / w

SW, SH = D['w'], D['h']
cam = []
for k in range(FR):
    t = k / FPS
    if t >= CUT: break
    i = min(n - 1, 2 * k); z = zoom_at(t); vw, vh = SW / z, SH / z
    fx = min(SW - vw / 2, max(vw / 2, smooth(i, 'x'))); fy = min(SH - vh / 2, max(vh / 2, smooth(i, 'y')))
    since = next((i - b for b in range(i, max(-1, i - 36), -1) if cur[b]['down'] and (b == 0 or not cur[b - 1]['down'])), 99)
    cam.append([round(z, 4), round(fx - vw / 2, 2), round(fy - vh / 2, 2), round(cur[i]['x'], 1), round(cur[i]['y'], 1), since])

sc = C.get('scatter')
EDIT = {
    'fps': FPS, 'frames': FR, 'dur': DUR, 'cut': round(CUT, 3), 'xf': XF, 'mob0': round(MOB0, 3),
    'desk': {'w': SW, 'h': SH, 'frames': len(cam)}, 'mob': {'w': M['w'], 'h': M['h'], 'frames': M['frames'] // 2},
    'cam': cam, 'chunks': W['chunks'],
    'cards': [[round(T(c['from']), 2), round(T(c['to']), 2), c['chip'], c.get('sub', '')] for c in C.get('cards', [])],
    'scatter': sc and {'t0': round(T(sc['from']), 2), 'merge': round(T(sc['merge']), 2), 'lock': sc.get('lock') and round(T(sc['lock']['at']), 2),
                       'lockText': (sc.get('lock') or {}).get('text', ''), 'pill': sc.get('pill', ''), 'tiles': sc['tiles'], 'small': sc.get('small', '')},
    'cta': C.get('cta') and {'t': round(T(C['cta']['at']), 2), 'html': C['cta']['html']},
    'domain': C.get('domain', ''), 'urls': [[0 if m == 0 else round(T(m) - 0.2, 2), u] for m, u in C.get('urls', [[0, '']])],
    'stitch': C.get('stitch'), 'theme': C.get('theme', {}), 'marks': {k: round(v, 2) for k, v in marks.items()},
}
os.makedirs('comp', exist_ok=True)
open('comp/one.js', 'w').write('const EDIT = ' + json.dumps(EDIT, separators=(',', ':'), ensure_ascii=False) + ';\n')
print(f'{FR} frames, {DUR}s, desktop {CUT:.2f}s + phone; zooms: ' + (', '.join(f'{a:.1f}-{b:.1f} x{z}' for a, b, z in ZOOMS) or 'none'))
