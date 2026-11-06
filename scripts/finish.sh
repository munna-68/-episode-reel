#!/bin/zsh
# Mux out/frames + audio/mix/premaster.wav into final.mp4 (1080x1920, H.264 30 fps, AAC 48 kHz, -14 LUFS, ~-1 dBTP), then verify.
#   tools/finish.sh [name.mp4]      (run from the episode folder; default final.mp4)
set -e
OUTF=${1:-final.mp4}
J=$(ffmpeg -hide_banner -i audio/mix/premaster.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1'])"; }
LN="loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
ffmpeg -v error -y -framerate 30 -i out/frames/f%05d.jpg -i audio/mix/premaster.wav \
  -af "$LN,aresample=48000" -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -level 4.2 -r 30 \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$OUTF"
echo "== probe"; ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -show_entries format=duration,size -of compact "$OUTF"
echo "== loudness"; ffmpeg -hide_banner -i "$OUTF" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | tr -s ' '
echo "== silent gaps > 0.4 s (at -50 dB)"; ffmpeg -hide_banner -i "$OUTF" -vn -af silencedetect=n=-50dB:d=0.4 -f null - 2>&1 | grep -c silence_end || true
echo "== black frames"; ffmpeg -hide_banner -i "$OUTF" -an -vf blackdetect=d=0.05:pix_th=0.06 -f null - 2>&1 | grep -c black_start || true
