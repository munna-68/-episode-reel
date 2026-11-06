#!/usr/bin/env python3
"""Place each cleaned voice line at an absolute time (continuous-take edit: the voice follows the picture).

  python3 tools/place_vo.py vo_tight.wav timing_tight.json starts.json out.wav out_timing.json [--dur 75]
starts.json: [t1, t2, ...] seconds, one per line.
"""
import sys, json, numpy as np
from scipy.io import wavfile
a = sys.argv[1:]; dur = None
if '--dur' in a: i = a.index('--dur'); dur = float(a[i + 1]); del a[i:i + 2]
src, tim, st, out, otim = a
sr, x = wavfile.read(src); spans = json.load(open(tim)); starts = json.load(open(st))
n = int(sr * (dur or (starts[-1] + spans[-1]['end'] - spans[-1]['start'] + 0.5)))
y = np.zeros((n,) + x.shape[1:], x.dtype); rep = []
for s, t in zip(spans, starts):
    seg = x[int(s['start'] * sr):int(s['end'] * sr)]; i = int(t * sr)
    assert not rep or t >= rep[-1]['end'] - 1e-3, f"line {s['line']} overlaps"
    y[i:i + len(seg)] = seg[:max(0, n - i)]
    rep.append({'line': s['line'], 'start': round(t, 3), 'end': round(t + len(seg) / sr, 3)})
wavfile.write(out, sr, y); json.dump(rep, open(otim, 'w'))
for r in rep: print(r)
