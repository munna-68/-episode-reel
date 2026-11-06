#!/usr/bin/env python3
"""Transcribe every voiced line and compare it with the script, word by word.

  python3 tools/check_lines.py audio/lines.json audio/raw [--only 2,3]

Prints OK or MISMATCH per line. Numbers transcribe as digits and names can vary in spelling
("Rachael" -> "Rachel"), so read every MISMATCH yourself before re-voicing. Re-voice only real slips
(a dropped or inserted word). The voice model sometimes adds a stray word, and that has to be caught here.
"""
import json, base64, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_rpc import session, call
a = sys.argv[1:]
only = None
if '--only' in a: i = a.index('--only'); only = {int(x) for x in a[i + 1].split(',')}; del a[i:i + 2]
lines, raw = a
norm = lambda s: re.sub(r"[^a-z0-9' ]", ' ', s.lower()).split()
sid = session(); bad = 0
for n, text in enumerate(json.load(open(lines)), 1):
    if only and n not in only: continue
    b = base64.b64encode(open(os.path.join(raw, f'{n:02d}.wav'), 'rb').read()).decode()
    got = call(sid, 'transcribe', {'audio_base64': b, 'language': 'English'}).get('text', '')
    ok = norm(got) == norm(text); bad += not ok
    print(f"{n:02d} {'OK      ' if ok else 'MISMATCH'} {got}")
print(f'{bad} line(s) to review')
