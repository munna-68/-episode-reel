#!/usr/bin/env python3
"""Word-level timings for burned-in captions, without a forced aligner.

  python3 tools/word_times.py audio/v5/vo.wav audio/v5/timing.json audio/v5/lines.json audio/v5/words.json [--offset 0.3]

For each line (span from clean_vo's timing report): find the pauses inside the span, snap the
punctuation breaks (, . : ? !) to the longest pauses in order, then spread the words of each phrase
across its speech by a syllable-ish weight. Also groups words into caption chunks (max 4 words,
break on punctuation or a pause).
"""
import sys, json, re, numpy as np
from scipy.io import wavfile

a = sys.argv[1:]
OFF = 0.0
if '--offset' in a: i = a.index('--offset'); OFF = float(a[i + 1]); del a[i:i + 2]
wav, tim, lines_p, out = a
sr, x = wavfile.read(wav); x = x.astype(np.float32); x = x.mean(1) if x.ndim > 1 else x
x /= (np.abs(x).max() + 1e-9)
hop = int(sr * 0.01); win = int(sr * 0.025)
db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9) for i in range(0, len(x) - win, hop)])
lines = json.load(open(lines_p)); spans = json.load(open(tim))

def weight(w):
    w = re.sub(r'[^a-z]', '', w.lower()) or 'x'
    syl = max(1, len(re.findall(r'[aeiouy]+', w)) - (1 if w.endswith('e') and len(w) > 3 else 0))
    return syl + 0.15 * len(w)

words_out = []
for text, sp in zip(lines, spans):
    s0, s1 = sp['start'], sp['end']
    f0, f1 = int(s0 / 0.01), min(len(db), int(s1 / 0.01))
    seg = db[f0:f1]; thr = np.percentile(seg, 90) - 22
    quiet = seg < thr
    pauses = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if j - i >= 5 and i > 3 and j < len(quiet) - 3: pauses.append(((f0 + i) * 0.01, (f0 + j) * 0.01))
            i = j
        else: i += 1
    toks = text.split()
    breaks = [k for k, w in enumerate(toks[:-1]) if re.search(r'[,.:;?!]$', w)]
    # choose the longest pauses, one per punctuation break, kept in time order
    chosen = sorted(sorted(pauses, key=lambda p: p[1] - p[0], reverse=True)[:len(breaks)])
    if len(chosen) < len(breaks):  # fewer pauses than commas: drop the latest breaks
        breaks = breaks[:len(chosen)]
    bounds = [s0] + [v for p in chosen for v in p] + [s1]
    phrases, k0 = [], 0
    for b in breaks + [len(toks) - 1]: phrases.append(toks[k0:b + 1]); k0 = b + 1
    for pi, ph in enumerate(phrases):
        a0, a1 = bounds[2 * pi], bounds[2 * pi + 1]
        W = [weight(w) for w in ph]; tot = sum(W); t = a0
        for w, wt in zip(ph, W):
            d = (a1 - a0) * wt / tot
            words_out.append({'w': w, 't0': round(t + OFF, 3), 't1': round(t + d + OFF, 3), 'line': sp['line']})
            t += d

# caption chunks
chunks, cur = [], []
for i, w in enumerate(words_out):
    cur.append(w)
    nxt = words_out[i + 1] if i + 1 < len(words_out) else None
    end = (len(cur) >= 4 or re.search(r'[,.:;?!]$', w['w']) or not nxt or nxt['line'] != w['line']
           or (nxt and nxt['t0'] - w['t1'] > 0.18) or (len(cur) >= 3 and len(''.join(c['w'] for c in cur)) > 16))
    if end:
        chunks.append({'t0': cur[0]['t0'] - 0.04, 't1': (nxt['t0'] - 0.04) if nxt and nxt['t0'] - w['t1'] < 0.45 else w['t1'] + 0.25,
                       'words': [{'w': c['w'], 't0': c['t0'], 't1': c['t1']} for c in cur]})
        cur = []
json.dump({'words': words_out, 'chunks': chunks}, open(out, 'w'), indent=1)
print(f'{len(words_out)} words, {len(chunks)} chunks -> {out}')
