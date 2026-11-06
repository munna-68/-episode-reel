#!/usr/bin/env python3
"""Music checkpoint: the real voice over 2-3 candidate beds, mixed at the series balance, as short mp3s to send.

  python3 tools/music_preview.py [--secs 24] [--opts deep:104,warm:96,pluck:118]

Needs audio/vo.wav + audio/timing.json (placed voice, tools/place_vo.py). Writes music/preview/<style>-<bpm>.mp3.
Episode 1's approved pick was deep:104 (always offer it first, as the series default).
"""
import json, os, subprocess, sys
TOOLS = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
def opt(k, d):
    if k in a: i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
secs = float(opt('--secs', 24)); opts = [o.split(':') for o in opt('--opts', 'deep:104,warm:96,pluck:118').split(',')]
os.makedirs('music/preview', exist_ok=True)
timing = [r for r in json.load(open('audio/timing.json')) if r['start'] < secs]
json.dump(timing, open('music/preview/timing.json', 'w'))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'audio/vo.wav', '-t', f'{secs}', 'music/preview/vo.wav'], check=True)
for style, bpm in opts:
    bed = f'music/preview/{style}-{bpm}.wav'; out = f'music/preview/{style}-{bpm}.mp3'
    subprocess.run(['python3', f'{TOOLS}/synth_bed.py', '--style', style, '--bpm', bpm, '--dur', f'{secs + 0.5}', '--drop-beat', '1',
                    '--end-beat', str(int((secs - 1.3) / (60 / float(bpm)))), '--out', bed], check=True, capture_output=True)
    subprocess.run(['python3', f'{TOOLS}/mix.py', 'music/preview/vo.wav', bed, 'music/preview/timing.json', out,
                    '--under', '4', '--lift', '2', '--lowpass', '9000', '--vo-offset', '0', '--tail', '0.5'], check=True, capture_output=True)
    print(out)
