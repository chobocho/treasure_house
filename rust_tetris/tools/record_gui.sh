#!/bin/sh
# GUI 를 가상 X 서버(Xvfb)에서 실제로 띄우고, xdotool 로 키를 보내고,
# xwd 로 창을 찍어 ImageMagick 으로 PNG 로 바꾼다. → out/gui_{start,play,pause}.png
set -eu
cd "$(dirname "$0")/.."
BIN=target/release/tetris-gui
MAGICK=${MAGICK:-/data/data/com.termux/files/usr/bin/magick}
D=:77
Xvfb $D -screen 0 640x700x24 -nolisten tcp >/dev/null 2>&1 &
XPID=$!
trap 'kill $GPID 2>/dev/null; kill $XPID 2>/dev/null; wait $XPID 2>/dev/null' EXIT   # 고아 Xvfb 방지
sleep 1.5
DISPLAY=$D $BIN --seed 7 &
GPID=$!
shot() { DISPLAY=$D xwd -silent -id "$WID" > out/gui_$1.xwd; $MAGICK out/gui_$1.xwd out/gui_$1.png; rm out/gui_$1.xwd; }
sleep 2
WID=$(DISPLAY=$D xdotool search --name "Rust" | head -1)
DISPLAY=$D xdotool windowfocus --sync "$WID" 2>/dev/null || true   # 창 관리자가 없어 포커스를 직접 준다
shot start
for k in Left Left Left Left space Right Right Right Right space Up space z Left space c space x space; do
  DISPLAY=$D xdotool key "$k"; sleep 0.2
done
sleep 0.5
shot play
DISPLAY=$D xdotool key p; sleep 0.4
shot pause
DISPLAY=$D xdotool key q; sleep 0.5
if kill -0 $GPID 2>/dev/null; then echo "Q 로 안 끝났다"; exit 1; fi
echo "GUI 녹화 완료"
