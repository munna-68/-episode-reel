#!/usr/bin/env python3
"""Clean and assemble the voiceover.

  python3 tools/clean_vo.py audio/raw audio/vo.wav [--gap 0.2] [--max-pause 0.09] [--report audio/vo_timing.json]

Per line: trims the ends, finds quiet runs inside the line (breaths, dead air: frames more than
REL dB under the line's speech level for at least MIN_RUN s), replaces each with clean silence no longer
than --max-pause, keeping short faded pads so word edges aren't clipped. Then joins the lines with --gap s
of silence, high-passes, and normalizes to -16 LUFS (two-pass loudnorm via ffmpeg).
Writes a timing report (start/end of each line in the final file) for captions and scene cuts.
"""
import sys, json, glob, os, subprocess, tempfile, numpy as np
from scipy.io import wavfile

args = sys.argv[1:]
def opt(name, default, cast=float):
    if name in args:
        i = args.index(name); v = cast(args[i + 1]); del args[i:i + 2]; return v
    return default
GAP = opt('--gap', 0.2); MAXP = opt('--max-pause', 0.09); REPORT = opt('--report', None, str)
REL = opt('--rel', 26.0); MIN_RUN = opt('--min-run', 0.14); PAD = 0.035
src, out = args
files = sorted(glob.glob(os.path.join(src, '[0-9][0-9].wav')))

def load(p):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    if np.abs(x).max() > 1.5: x /= 32768.0
    return sr, x

def frames_db(x, sr, hop=0.01, win=0.03):
    h, w = int(sr * hop), int(sr * win)
    n = max(1, (len(x) - w) // h + 1)
    rms = np.array([np.sqrt(np.mean(x[i * h:i * h + w] ** 2) + 1e-12) for i in range(n)])
    return 20 * np.log10(rms), h

def fade(sig, sr, t_in, t_out):
    s = sig.copy(); a = int(sr * t_in); b = int(sr * t_out)
    if a: s[:a] *= np.linspace(0, 1, a)
    if b: s[-b:] *= np.linspace(1, 0, b)
    return s

def clean(x, sr):
    db, hop = frames_db(x, sr)
    loud = db > np.percentile(db, 90) - REL
    idx = np.where(loud)[0]
    if not len(idx): return x
    pad = int(PAD * sr)
    a = max(0, idx[0] * hop - pad); b = min(len(x), idx[-1] * hop + int(0.03 * sr) + pad)
    runs, i = [], idx[0]
    while i <= idx[-1]:                       # quiet runs between first and last speech frame
        if loud[i]: i += 1; continue
        j = i
        while j <= idx[-1] and not loud[j]: j += 1
        if (j - i) * hop / sr >= MIN_RUN: runs.append((i * hop, j * hop))
        i = j
    out, cur, after_gap = [], a, False
    for s, e in runs:                         # breath/dead air -> short clean silence
        out.append(fade(x[cur:s + pad], sr, PAD if after_gap else 0.005, PAD))
        out.append(np.zeros(int(min((e - s) / sr, MAXP) * sr), np.float32))
        cur, after_gap = e - pad, True
    out.append(fade(x[cur:b], sr, PAD if after_gap else 0.005, 0.02))
    return np.concatenate(out)

sr0 = None; parts = []; timing = []; t = 0.0
for f in files:
    sr, x = load(f); sr0 = sr0 or sr
    y = clean(x, sr)
    if parts:
        parts.append(np.zeros(int(GAP * sr), np.float32)); t += GAP
    timing.append({'line': os.path.basename(f)[:2], 'start': round(t, 3), 'end': round(t + len(y) / sr, 3)})
    parts.append(y); t += len(y) / sr
vo = np.concatenate(parts)
tmp = tempfile.mktemp(suffix='.wav'); wavfile.write(tmp, sr0, (vo * 32767).clip(-32768, 32767).astype(np.int16))

meas = subprocess.run(['ffmpeg', '-hide_banner', '-i', tmp, '-af', 'highpass=f=75,loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json',
                       '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(meas[meas.rindex('{'):meas.rindex('}') + 1])
ln = (f"highpass=f=75,loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', ln, '-ar', '48000', out], check=True)
os.remove(tmp)
if REPORT: json.dump(timing, open(REPORT, 'w'), indent=1)
print(f'{out}: {t:.2f}s, {len(files)} lines')
for r in timing: print(f"  {r['line']}  {r['start']:6.2f} - {r['end']:6.2f}")
