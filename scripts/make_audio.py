#!/usr/bin/env python3
"""Soundtrack: the approved music bed, the placed voice on top (series balance), and light SFX taken from
the real take (every mouse press, page-transition whooshes, typing, etc. from edit.json "sfx").

  python3 tools/make_audio.py        (run from the episode folder, after build_edit.py) -> audio/mix/premaster.wav

edit.json "music": {"style": "deep", "bpm": 104}   style: deep | warm | pluck (tools/synth_bed.py), the one the user picked.
Series mix (user-approved, do not change without asking): music 4 LU under the voice, +2 dB in the gaps, 9 kHz high-cut.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeexpr import resolver
TOOLS = os.path.dirname(os.path.abspath(__file__))
E = json.loads(open('comp/one.js').read()[len('const EDIT = '):].rstrip().rstrip(';\n'))
C = json.load(open('edit.json')); MU = C.get('music', {}); SX = C.get('sfx', {})
timing = json.load(open('audio/timing.json'))
T = resolver(E['marks'], timing, {'cut': E['cut'], 'mob0': E['mob0'], 'dur': E['dur'], 'cta': (E.get('cta') or {}).get('t', E['dur'])})
dur = E['dur']
run = lambda *a: subprocess.run(a, check=True)
os.makedirs('audio/mix', exist_ok=True); os.makedirs('music', exist_ok=True)

bpm = MU.get('bpm', 104); beat = lambda t: (t - 0.048) / (60 / bpm)
run('python3', f'{TOOLS}/synth_bed.py', '--style', MU.get('style', 'deep'), '--bpm', str(bpm), '--dur', f'{dur + 0.5:.2f}',
    '--drop-beat', str(MU.get('drop_beat', 1)), '--fills', f'{int(beat(E["mob0"])) - 2}-{int(beat(E["mob0"]))}',
    '--end-beat', str(int(beat(dur - 1.3))), '--out', 'music/bed.wav')
vo_len = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', 'audio/vo.wav'],
                              capture_output=True, text=True).stdout)
run('python3', f'{TOOLS}/mix.py', 'audio/vo.wav', 'music/bed.wav', 'audio/timing.json', 'audio/mix/vo_bed.wav',
    '--under', str(MU.get('under', 4)), '--lift', str(MU.get('lift', 2)), '--lowpass', str(MU.get('lowpass', 9000)),
    '--vo-offset', '0', '--tail', f'{max(0.1, dur - vo_len):.2f}')

cues = []
cur = json.load(open('footage/desk/meta.json'))['cursor']; prev = 0
for c in cur:                                              # every real mouse press in the take
    if c['down'] and not prev: cues.append({'type': 'click', 't': c['n'] / 60, 'gain': 0.8})
    prev = c['down']
for m in SX.get('transitions', []):                        # the site's own page-transition panels
    cues.append({'type': 'whoosh', 't': T(m) + 0.62, 'gain': 0.32})
for k, g in (('boom', 0.7), ('thock', 0.6), ('chime', 0.6), ('ping', 0.8), ('hit', 0.6)):
    for at in ([SX[k]] if isinstance(SX.get(k), (str, int, float)) else SX.get(k, [])):
        cues.append({'type': k, 't': T(at), 'gain': g})
for kk in SX.get('keys', []):
    cues.append({'type': 'keys', 't': T(kk['at']), 'n': kk['n'], 'gap': kk.get('gap', 1 / 7), 'gain': 0.8})
for tk in SX.get('ticks', []):
    cues.append({'type': 'ticks', 't': T(tk['at']), 'n': tk.get('n', 16), 'gap': tk.get('gap', 0.07), 'gain': 0.7})
cues.append({'type': 'whoosh', 't': E['mob0'] + 0.25, 'gain': 0.5})          # into the phone
if E.get('cta'): cues.append({'type': 'shimmer', 't': E['cta']['t'] + 0.3, 'gain': 0.9})
cfg = {'bed': 'audio/mix/vo_bed.wav', 'dur': dur, 'bed_gain': 1.0, 'cues': sorted(cues, key=lambda c: c['t'])}
json.dump(cfg, open('audio/mix/cues.json', 'w'), indent=1)
run('python3', f'{TOOLS}/mix_sfx.py', 'audio/mix/cues.json', 'audio/mix/premaster.wav')
print(f'{len(cues)} cues -> audio/mix/premaster.wav')
