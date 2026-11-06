#!/usr/bin/env python3
"""Mix voice over the music bed with precise ducking, then master.

  python3 tools/mix.py audio/vo.wav music/full/D-raw.wav audio/vo_timing.json out.mp3 \
      [--under 18] [--lift 4] [--vo-offset 0.25] [--tail 1.6] [--lowpass 5500] [--lufs -14]

--under  how many LU the music sits below the voice while you speak
--lift   how much the music rises in the gaps between lines (dB)
The bed is high-cut (--lowpass) so it stays out of the voice range, trimmed to the voice
length plus --tail, faded out, ducked by a smooth gain curve built from the line timings,
summed with the voice and two-pass loudnorm'd to --lufs (true peak -1 dBTP).
"""
import sys, json, subprocess, tempfile, os, numpy as np
from scipy.io import wavfile

args = sys.argv[1:]
def opt(n, d, c=float):
    if n in args: i = args.index(n); v = c(args[i + 1]); del args[i:i + 2]; return v
    return d
UNDER = opt('--under', 18); LIFT = opt('--lift', 4); OFF = opt('--vo-offset', 0.25)
TAIL = opt('--tail', 1.6); LP = opt('--lowpass', 5500); LUFS = opt('--lufs', -14)
vo_p, bed_p, tim_p, out = args
SR = 48000

def ff(*a): subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)
def read(p):
    sr, x = wavfile.read(p); x = x.astype(np.float32)
    if np.abs(x).max() > 1.5: x /= 32768.0
    if x.ndim == 1: x = np.stack([x, x], 1)
    return x
def loud(p):
    e = subprocess.run(['ffmpeg', '-hide_banner', '-i', p, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(e[e.rindex('I:'):].split()[1])

tmp = tempfile.mkdtemp()
vo_w = os.path.join(tmp, 'vo.wav'); bed_w = os.path.join(tmp, 'bed.wav')
ff('-i', vo_p, '-ar', str(SR), '-ac', '2', vo_w)
vo_l = loud(vo_w)
dur = OFF + read(vo_w).shape[0] / SR + TAIL
# bed: high-cut, trim, fade, set so it sits UNDER LU below the voice
ff('-i', bed_p, '-af', f'lowpass=f={LP},atrim=0:{dur:.3f},afade=t=out:st={dur - 1.4:.3f}:d=1.4', '-ar', str(SR), '-ac', '2', bed_w)
bed = read(bed_w); bed *= 10 ** ((vo_l - UNDER - loud(bed_w)) / 20)
vo = read(vo_w); n = bed.shape[0]
voice = np.zeros_like(bed); o = int(OFF * SR); voice[o:o + vo.shape[0]] = vo[:n - o]

# gain curve: 0 dB under speech, +LIFT dB in gaps longer than 0.35 s, 120 ms ramps
tim = json.load(open(tim_p)); g = np.full(n, LIFT, np.float32)
for r in tim:
    a = int((OFF + r['start'] - 0.08) * SR); b = int((OFF + r['end'] + 0.05) * SR); g[max(0, a):b] = 0
k = int(0.12 * SR); g = np.convolve(g, np.ones(k) / k, mode='same')
bed *= (10 ** (g / 20))[:, None]

mix = os.path.join(tmp, 'mix.wav'); wavfile.write(mix, SR, (voice + bed).astype(np.float32))
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', mix, '-af', f'loudnorm=I={LUFS}:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
ln = (f"loudnorm=I={LUFS}:TP=-1:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
      f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
args_out = ['-b:a', '256k'] if out.endswith('.mp3') else []
ff('-i', mix, '-af', ln, '-ar', str(SR), *args_out, out)
print(f'{out}: {dur:.2f}s, music {UNDER} LU under voice (+{LIFT} dB in gaps), final {loud(out):.1f} LUFS')
