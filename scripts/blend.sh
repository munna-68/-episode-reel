#!/bin/zsh
# 60 fps take -> 30 fps frames with natural motion blur (each output frame = 2 source frames averaged).
#   tools/blend.sh footage/desk footage/desk30
set -e
rm -rf "$2"; mkdir -p "$2"
ffmpeg -v error -framerate 60 -i "$1/f%05d.jpg" -vf "tmix=frames=2,select='not(mod(n\,2))'" -fps_mode passthrough -q:v 2 "$2/f%05d.jpg"
echo "$(ls "$2" | wc -l | tr -d ' ') frames -> $2"
