#!/usr/bin/env python3
"""Original, royalty-free house bed locked to the video's beat grid. Deterministic (seeded).

  python3 synth_bed.py --style pluck --dur 40.74 --drop-beat 12 --fills 10-12,66-68 \
      --lead 44-60,68-76 --breakdown 76-80 --end-beat 80 --out bed.wav

styles:
  pluck  bright 16th-note plucks, airy supersaw pads, punchy kick (Am F C G)  - product-launch energy
  warm   Rhodes chords, shuffled hats, round kick (Dm9 G13 Cmaj9 Am9)       - cosy, premium
  deep   darker minor groove, sub bass, sparse stabs (Fm Db Ab Eb)           - techy, serious
Beats: beat k sits at OFFSET + k*60/BPM seconds (defaults 0.048 s, 124 BPM).
Before --drop-beat: filtered intro (8ths only, soft offbeat ticks) with a riser into the drop.
--fills a-b      snare roll from beat a to b (kick drops for the last beat) - put one ending on the drop
--lead a-b       bell motif on top for those beats (lift the second half)
--breakdown a-b  kick out, filter closes (calm moment before the end card)
--end-beat k     big hit + chord ring-out at beat k; groove stops there
"""
import argparse, numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi
from scipy.io import wavfile

ap = argparse.ArgumentParser()
ap.add_argument('--style', default='pluck', choices=['pluck', 'warm', 'deep'])
ap.add_argument('--dur', type=float, required=True)
ap.add_argument('--bpm', type=float, default=124)
ap.add_argument('--offset', type=float, default=0.048)
ap.add_argument('--drop-beat', type=float, default=12)
ap.add_argument('--fills', default='')
ap.add_argument('--lead', default='')
ap.add_argument('--breakdown', default='')
ap.add_argument('--end-beat', type=float, default=None)
ap.add_argument('--seed', type=int, default=124)
ap.add_argument('--out', required=True)
A = ap.parse_args()
ranges = lambda s: [tuple(float(v) for v in r.split('-')) for r in s.split(',') if r.strip()]
FILLS, LEADS, BREAKS = ranges(A.fills), ranges(A.lead), ranges(A.breakdown)
inr = lambda k, R: any(a <= k < b for a, b in R)

SR = 48000; DUR = A.dur; N = int(SR * DUR); BEAT = 60 / A.bpm; DROP = A.drop_beat
END = A.end_beat if A.end_beat is not None else 1e9
bt = lambda k: A.offset + BEAT * k
NB = int((DUR - A.offset) / BEAT) + 2
rng = np.random.default_rng(A.seed)
STYLE = A.style

def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def place(buf, sig, t):
    i = int(round(t * SR))
    if i >= len(buf) or i + len(sig) <= 0: return
    s = max(0, -i); e = min(len(sig), len(buf) - i); buf[i + s:i + e] += sig[s:e]
def lp(x, fc, o=2): return sosfilt(butter(o, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def sweep_lp(x, f_of_t, block=512):
    y = np.zeros_like(x); zi = None
    for i in range(0, len(x), block):
        sos = butter(2, float(np.clip(f_of_t(i / SR), 60, SR * .45)), 'low', fs=SR, output='sos')
        if zi is None: zi = sosfilt_zi(sos) * 0
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return y
def reverb(x, secs=1.8, seed=1, damp=5000):
    r = np.random.default_rng(seed); n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (SR * secs / 6)); ir = lp(ir, damp); ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L))[:len(x)]

def groove(k):
    if k < DROP or k >= END or inr(k, BREAKS): return False
    for a, b in FILLS:
        if b - 1 <= k < b and b > DROP + 1: return False      # kick drops on the last beat of a mid-song fill
    return True

# ---------- drums ----------
kick = np.zeros(N); clap = np.zeros(N); hat = np.zeros(N); pump = np.ones(N); roll = np.zeros(N)
def mk_kick():
    n = int(.42 * SR); t = np.arange(n) / SR
    top = {'pluck': 140, 'warm': 115, 'deep': 100}[STYLE]; dec = {'pluck': .26, 'warm': .32, 'deep': .36}[STYLE]
    f = 45 + top * np.exp(-t / .035)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec) + .25 * rng.standard_normal(n) * np.exp(-t / .003)
    return np.tanh(1.6 * s)
K = mk_kick()
for kk in range(NB):
    k = kk
    if groove(k):
        place(kick, K, bt(k))
        i = int(bt(k) * SR); n = int(BEAT * SR); t = np.arange(n) / SR
        e = 1 - .55 * np.exp(-t / .11); j = min(N, i + n)
        if i < N: pump[i:j] = np.minimum(pump[i:j], e[:j - i])
        if (k - DROP) % 2 == 1:
            n = int(.25 * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n); e = np.zeros(n)
            for o in (0, .009, .019): e += np.exp(-np.maximum(0, t - o) / .012) * (t >= o)
            e += .6 * np.exp(-t / .09)
            place(clap, bp(nz * e, 900, 5200) * (.5 if STYLE != 'deep' else .35), bt(k))
for h in range(NB * 4):
    k = h / 4; tm = bt(k) + (.022 if STYLE == 'warm' and h % 2 == 1 else 0)
    n = int(.08 * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n)
    s = hp(nz, 7000) * np.exp(-t / .035) * .55 if h % 4 == 2 else hp(nz, 9000) * np.exp(-t / .012) * (.22 if h % 2 else .3)
    if k < DROP: s = s * (0 if (h % 4 != 2 or k < min(4, DROP / 3)) else .3 * k / DROP)
    elif k >= END: s = s * 0
    elif inr(k, BREAKS): s = s * (.35 if h % 4 == 2 else 0)
    place(hat, s, tm)
for a, b in FILLS:
    k = a
    while k < b - 1e-6:
        n = int(.12 * SR); t = np.arange(n) / SR
        place(roll, bp(rng.standard_normal(n), 1500, 6500) * np.exp(-t / .03) * (.18 + .4 * (k - a) / (b - a)), bt(k))
        k += .25 if (k - a) < (b - a) / 2 else .125

# ---------- harmony ----------
PROG = {'pluck': [[45, 52, 57, 60, 64], [41, 52, 57, 60, 65], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]],
        'warm': [[50, 57, 60, 64, 65], [43, 53, 57, 59, 64], [48, 55, 59, 62, 64], [45, 55, 60, 64, 67]],
        'deep': [[41, 56, 60, 63, 67], [37, 56, 60, 65, 68], [44, 56, 60, 63, 67], [39, 55, 58, 63, 67]]}[STYLE]
chord_at = lambda bar_start: PROG[int(((bar_start - DROP) // 4) % 4)]
def supersaw(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for d in (-.12, -.05, 0, .06, .13): s += 2 * ((mtof(m) * 2 ** (d / 12) * t + rng.random()) % 1) - 1
    return s * np.minimum(1, t / .25) * np.minimum(1, np.maximum(0, (dur - t) / .2)) / 5
def pluck(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = (2 * ((f * t) % 1) - 1) + .5 * np.sign(np.sin(2 * np.pi * f * 1.005 * t))
    return (lp(s, 1800) * .6 + lp(s, 5000) * .4 * np.exp(-t / .05)) * np.exp(-t / .16)
def rhodes(m, dur, v=1.):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    s = np.sin(2 * np.pi * f * t + 2.2 * np.exp(-t / .25) * v * np.sin(2 * np.pi * f * t)) + .15 * np.sin(4 * np.pi * f * t) * np.exp(-t / .1)
    a = np.exp(-t / .9); a[:int(.004 * SR)] *= np.linspace(0, 1, int(.004 * SR)); a[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
    return s * a * v
def bell(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    return np.sin(2 * np.pi * f * t + 1.5 * np.exp(-t / .2) * np.sin(2 * np.pi * f * 3.5 * t)) * np.exp(-t / .5)
lead = np.zeros(N); pad = np.zeros(N); bass = np.zeros(N); bells = np.zeros(N)
first = DROP - 4 * int(np.ceil(DROP / 4))
b0 = first
while bt(b0) < DUR:
    t0 = bt(b0); t1 = min(bt(b0 + 4), DUR); ch = chord_at(b0)
    if b0 < END:
        if STYLE == 'pluck':
            arp = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[3] + 12, ch[2] + 24, ch[4] + 12, ch[1] + 24]
            for s16 in range(16):
                k = b0 + s16 / 4
                if k < 0 or bt(k) >= DUR or k >= END + 1: continue
                if k < DROP and s16 % 2: continue
                place(lead, pluck(arp[s16 % 8], .4) * .11 * (.9 if s16 % 4 == 0 else .6), bt(k))
        elif STYLE == 'warm':
            for off, v in ((0, 1.), (1.5, .7), (3, .55), (3.5, .4)):
                k = b0 + off
                if k < 0 or bt(k) >= DUR or (k < DROP and off > 0): continue
                for m in ch[1:]: place(lead, rhodes(m + 12, min(1.6, DUR - bt(k) + .01), v) * .16, bt(k) + .004 * rng.random())
        else:
            for off in (0, .75, 2.5):
                k = b0 + off
                if k < 0 or bt(k) >= DUR: continue
                for m in ch[2:]: place(lead, pluck(m + 12, .3) * .09, bt(k))
    if b0 + 4 > 0:
        for m in ch[1:4]: place(pad, supersaw(m + 12, max(.05, t1 - max(0, t0) + .15)) * .07, max(0, t0))
    if DROP <= b0 < END and not inr(b0, BREAKS):
        root = ch[0] - 12 if ch[0] >= 48 else ch[0]
        pat = ((.5, .4), (1.5, .35), (2.5, .4), (3.25, .2), (3.5, .3)) if STYLE == 'warm' else ((0, .3), (.75, .2), (2, .3), (2.75, .2)) if STYLE == 'deep' else ((.5, .35), (1.5, .35), (2.5, .35), (3.5, .35))
        for off, d in pat:
            if bt(b0 + off) >= DUR: continue
            n = int(d * SR); t = np.arange(n) / SR; f = mtof(root)
            s = np.sin(2 * np.pi * f * t) + (.3 if STYLE != 'deep' else .1) * np.sin(4 * np.pi * f * t)
            place(bass, np.tanh(1.8 * s * np.minimum(1, t / .005) * np.minimum(1, (d - t) / .02)) * (.32 if STYLE != 'deep' else .4), bt(b0 + off))
    if inr(b0, LEADS):
        mel = [ch[4] + 24, ch[3] + 24, ch[2] + 24, ch[3] + 24]
        for i, off in enumerate((0, 1.5, 2.5, 3)):
            if bt(b0 + off) < DUR: place(bells, bell(mel[i], .9) * .05, bt(b0 + off))
    b0 += 4

end = np.zeros(N)
if A.end_beat is not None and bt(END) < DUR:
    n = int(3.5 * SR); t = np.arange(n) / SR; f = 40 + 90 * np.exp(-t / .05)
    place(end, np.tanh(1.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .5)) * .8 + hp(rng.standard_normal(n), 4000) * np.exp(-t / .9) * .18, bt(END))
    for m in [c + 12 for c in chord_at(END)[1:]] + [chord_at(END)[1] + 24]: place(end, supersaw(m, 3.) * .06, bt(END))

def mel_f(s):
    if s < bt(DROP): return 450 + 3000 * (s / bt(DROP)) ** 2
    for a, b in BREAKS:
        if bt(a) <= s < bt(b): return 9000 - 7600 * (s - bt(a)) / (bt(b) - bt(a))
    return 12000
lead = sweep_lp(lead, mel_f); pad = sweep_lp(pad, mel_f)
riser = np.zeros(N); n = int(1.9 * SR); t = np.arange(n) / SR
rs = sweep_lp(rng.standard_normal(n), lambda s: 600 + 7000 * (s / 1.9) ** 2) * (t / 1.9) ** 2 * .12
place(riser, rs, bt(DROP) - 1.9)
for a, b in FILLS:
    if b > DROP + 1: place(riser, rs * .9, bt(b) - 1.9)
air = hp(rng.standard_normal(N), 3000) * .003
mel = (lead + pad + bells + bass) * pump
src = lead + pad * .6 + bells * 1.5 + clap * .5 + end * .6
dry = kick * .9 + clap * .55 + hat * .6 + roll + mel + riser + air + end
st = np.stack([dry + reverb(src, 1.8, 7) * .22, dry + reverb(src, 1.8, 11) * .22], 1)
st /= np.abs(st).max() / .9
ne = int(.06 * SR); st[-ne:] *= np.linspace(1, 0, ne)[:, None]
wavfile.write(A.out, SR, (st * 32767).astype(np.int16))
print(f'wrote {A.out}  style={STYLE} dur={DUR}s drop=beat {DROP} ({bt(DROP):.3f}s)')
