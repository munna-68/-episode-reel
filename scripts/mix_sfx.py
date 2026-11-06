#!/usr/bin/env python3
"""Lay synthesized sound effects over the chosen music bed from a cue sheet, write a pre-master.

  python3 mix_sfx.py cues.json premaster.wav

cues.json:
{
  "bed": "audio/bed.wav",          # chosen track, already cut/stretched to the grid (48 kHz)
  "dur": 40.74,                     # seconds (match the bed)
  "bed_gain": 0.85,
  "cues": [
    {"type": "whoosh",  "t": 5.77},                 # PEAKS at t (put one on every hard cut)
    {"type": "boom",    "t": 5.80},                 # soft sub thump (the drop / a reveal)
    {"type": "ping",    "t": 0.47, "pan": -0.3},    # notification ping
    {"type": "tap",     "t": 10.4},                 # finger tap on glass
    {"type": "click",   "t": 2.33},                 # mouse click
    {"type": "thock",   "t": 11.0},                 # small object lands (item into cart/box, card into slot)
    {"type": "chime",   "t": 19.7},                 # success / payment confirmed
    {"type": "hit",     "t": 22.7},                 # transition hit / data lands
    {"type": "ticks",   "t": 29.3, "n": 12, "gap": 0.06},   # counter ticking up
    {"type": "keys",    "t": 4.04, "n": 20, "gap": 0.032},  # quiet key ticks while typing
    {"type": "shimmer", "t": 38.7}                  # end card sparkle
  ]
}
Optional per cue: "gain" (multiplies the default), "pan" (-1..1).
"""
import sys, json, math, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, sosfilt_zi

cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
SR = 48000; DUR = float(cfg['dur']); N = int(SR * DUR)
sr, bed = wavfile.read(cfg['bed']); assert sr == SR, f'bed must be 48 kHz (got {sr})'
bed = bed.astype(np.float64)
if bed.dtype.kind == 'i' or np.abs(bed).max() > 2: bed /= 32768.0
if bed.ndim == 1: bed = np.stack([bed, bed], 1)
bed = bed[:N] if len(bed) >= N else np.pad(bed, ((0, N - len(bed)), (0, 0)))
sfx = np.zeros((N, 2))

def lp(x, fc, o=2): return sosfilt(butter(o, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, o=2): return sosfilt(butter(o, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def place(sig, t, gain=1.0, pan=0.0):
    if sig.ndim == 1:
        a = (pan + 1) * math.pi / 4; sig = np.stack([sig * math.cos(a), sig * math.sin(a)], 1)
    i = int(round(t * SR)); s = max(0, -i); e = min(len(sig), N - i)
    if e > s: sfx[i + s:i + e] += sig[s:e] * gain
def reverb(x, secs=1.2, seed=1, damp=6000):
    r = np.random.default_rng(seed); n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (SR * secs / 6)); ir = lp(ir, damp); ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n; return np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L))[:len(x) + n]
def sweep_bp(x, f_of_u, q=1.2, block=256):
    y = np.zeros_like(x); zi = None; n = len(x)
    for i in range(0, n, block):
        fc = float(np.clip(f_of_u(i / n), 80, SR * .4)); lo, hi = fc / (1 + 1 / (2 * q)), fc * (1 + 1 / (2 * q))
        sos = butter(2, [lo, hi], 'band', fs=SR, output='sos')
        if zi is None: zi = sosfilt_zi(sos) * 0
        y[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return y

def whoosh(seed, pre=.46, post=.16, f0=260, f1=3600):
    r = np.random.default_rng(seed); n = int((pre + post) * SR); t = np.arange(n) / SR; nz = r.standard_normal(n)
    env = np.where(t < pre, (t / pre) ** 2.2, np.exp(-(t - pre) / (post / 3.5)))
    s = (sweep_bp(nz, lambda q: f0 * (f1 / f0) ** min(1, q * (pre + post) / pre), q=.9) + hp(nz, 5000) * .25) * env
    a = (np.clip((t - pre) / (pre + post) * 2.2, -1, 1) + 1) * math.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)], 1), pre
def boom():
    n = int(.9 * SR); t = np.arange(n) / SR; f = 40 + 70 * np.exp(-t / .06)
    return np.tanh(1.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .35))
def ping(i):
    n = int(.35 * SR); t = np.arange(n) / SR
    p = np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t / .07) * (t < .09) + np.sin(2 * np.pi * 1975.5 * (t - .075)) * np.exp(-np.maximum(0, t - .075) / .12) * (t >= .075)
    return p + .3 * np.sin(2 * np.pi * 3951 * t) * np.exp(-t / .02)
def click(seed, bright=1.):
    r = np.random.default_rng(seed); n = int(.06 * SR); t = np.arange(n) / SR
    return bp(r.standard_normal(n), 1800 * bright, 9000) * np.exp(-t / .004) + np.sin(2 * np.pi * 1300 * bright * t) * np.exp(-t / .008) * .5
def thock(i):
    r = np.random.default_rng(300 + i); n = int(.18 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (520 + 40 * (i % 6)) * t) * np.exp(-t / .035) + bp(r.standard_normal(n), 800, 3000) * np.exp(-t / .01) * .5
def chime():
    out = np.zeros(int(1.2 * SR))
    for j, m in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        n = int(.9 * SR); t = np.arange(n) / SR; o = int(j * .055 * SR)
        out[o:o + n] += (np.sin(2 * np.pi * m * t) + .3 * np.sin(4 * np.pi * m * t)) * np.exp(-t / .35) * np.minimum(1, t / .004)
    return out
def hit(seed):
    r = np.random.default_rng(seed); n = int(.5 * SR); t = np.arange(n) / SR; f = 62 + 110 * np.exp(-t / .03)
    dry = np.tanh(1.6 * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .16) + bp(r.standard_normal(n), 1200, 7000) * np.exp(-t / .018) * .7))
    return dry + reverb(dry, 1.0, seed)[:n] * .35
def tick(seed):
    n = int(.02 * SR); t = np.arange(n) / SR
    return hp(np.random.default_rng(seed).standard_normal(n), 3000) * np.exp(-t / .004)
def key(seed):
    r = np.random.default_rng(seed); n = int(.03 * SR); t = np.arange(n) / SR
    return hp(r.standard_normal(n), 2500 + 900 * r.random()) * np.exp(-t / .006) + np.sin(2 * np.pi * (900 + 200 * r.random()) * t) * np.exp(-t / .005) * .4
def shimmer():
    n = int(2.4 * SR); t = np.arange(n) / SR; sh = np.zeros(n)
    for i, fq in enumerate([1568, 2093, 2637, 3136, 4186, 5274]): sh += np.sin(2 * np.pi * fq * (1 + .0015 * (i - 2.5)) * t + i) * (.9 ** i)
    sh *= np.minimum(1, t / .02) * np.exp(-t / .6) * (1 + .25 * np.sin(2 * np.pi * 7 * t))
    return np.stack([sh * .5 + reverb(sh, 1.6, 21)[:n] * .6, sh * .5 + reverb(sh, 1.6, 22)[:n] * .6], 1)

DEF = {'whoosh': .26, 'boom': .35, 'ping': .10, 'tap': .30, 'click': .30, 'thock': .20, 'chime': .07, 'hit': .30, 'ticks': .06, 'keys': .075, 'shimmer': .10}
counts = {}
for c in sorted(cfg['cues'], key=lambda c: c['t']):
    ty = c['type']; t = float(c['t']); g = DEF[ty] * c.get('gain', 1.0); pan = c.get('pan', 0.0)
    k = counts[ty] = counts.get(ty, -1) + 1
    if ty == 'whoosh': w, pre = whoosh(10 + k); place(w, t - pre, g)
    elif ty == 'boom': place(boom(), t, g, pan)
    elif ty == 'ping': place(ping(k), t, g * max(.5, 1 - .03 * k), pan if 'pan' in c else -.5 + ((k * 37) % 10) / 10)
    elif ty == 'tap': place(lp(click(50 + k, .75), 5200), t, g, pan or .15)
    elif ty == 'click': place(click(70 + k), t, g, pan)
    elif ty == 'thock': place(thock(k), t, g, pan or .25)
    elif ty == 'chime': place(chime(), t, g, pan or .2)
    elif ty == 'hit': place(hit(5 + k), t, g, pan)
    elif ty == 'ticks':
        for j in range(int(c.get('n', 12))): place(tick(500 + 31 * k + j), t + j * float(c.get('gap', .06)), g, pan or .1)
    elif ty == 'keys':
        r = np.random.default_rng(100 + k)
        for j in range(int(c.get('n', 20))): place(key(1000 + 50 * k + j), t + j * float(c.get('gap', .032)), g * (.8 + .4 * r.random()), -.2 + .4 * r.random())
    elif ty == 'shimmer': place(shimmer(), t, g)
    else: print('unknown cue type', ty)
mix = bed * float(cfg.get('bed_gain', .85)) + sfx
mix /= max(1e-9, np.abs(mix).max()) / .89
ne = int(.06 * SR); mix[-ne:] *= np.linspace(1, 0, ne)[:, None]
wavfile.write(out, SR, mix.astype(np.float32))
print('wrote', out, {k: v + 1 for k, v in counts.items()})
