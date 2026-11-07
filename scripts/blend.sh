#!/bin/zsh
# 60 fps take -> 30 fps frames with natural motion blur (each output frame = 2 source frames averaged).
#   tools/blend.sh footage/desk footage/desk30
#   tools/blend.sh footage/mob footage/mob30 --crisp    # phone takes: keep every 2nd frame, no blend
# A fast phone scroll moves ~40+ device px per 60 fps frame, so the blend shows text as a double image (ep 2). Use --crisp there.
set -e
rm -rf "$2"; mkdir -p "$2"
VF="tmix=frames=2,select='not(mod(n\,2))'"
[[ "$3" == "--crisp" ]] && VF="select='not(mod(n\,2))'"
ffmpeg -v error -framerate 60 -i "$1/f%05d.jpg" -vf "$VF" -fps_mode passthrough -q:v 2 "$2/f%05d.jpg"
echo "$(ls "$2" | wc -l | tr -d ' ') frames -> $2"
