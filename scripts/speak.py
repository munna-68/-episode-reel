#!/usr/bin/env python3
"""Voice the script line by line in the series voice.

  python3 tools/speak.py audio/lines.json audio/raw [--only 3,5] [--steps 16] [--voice 3a02464e]

lines.json: ["sentence 1", ...] -> audio/raw/01.wav, 02.wav, ...
Default voice: "ep1 D sample-locked" (3a02464e), the voice approved for the series. Do not swap it unless the user asks.
"""
import json, base64, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_rpc import session, call

a = sys.argv[1:]
def opt(k, d):
    if k in a: i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
VOICE = opt('--voice', '3a02464e'); STEPS = int(opt('--steps', 16)); only = opt('--only', None)
only = {int(x) for x in only.split(',')} if only else None
lines_file, out_dir = a
os.makedirs(out_dir, exist_ok=True)
sid = session()
for n, text in enumerate(json.load(open(lines_file)), 1):
    if only and n not in only: continue
    t0 = time.time()
    out = call(sid, 'generate_speech', {"text": text, "profile_id": VOICE, "language": "English", "steps": STEPS, "speed": 1.0, "format": "wav"})
    p = os.path.join(out_dir, f"{n:02d}.wav"); open(p, "wb").write(base64.b64decode(out["wav_base64"]))
    print(f"{p}  {out['audio_duration_s']:.2f}s  ({time.time() - t0:.0f}s)  {text}", flush=True)
