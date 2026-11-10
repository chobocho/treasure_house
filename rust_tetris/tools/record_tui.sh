#!/bin/sh
# TUI 를 tmux 안에서 실제로 돌리고 키를 보내 화면을 캡처한다.
#   tools/record_tui.sh            → out/tui_*.ansi, out/tui_*.txt
# 중력이 실제 시간으로 흐르므로 조각이 한두 줄 다르게 찍힐 수 있다.
set -eu
cd "$(dirname "$0")/.."
BIN=target/release/tetris-tui
T="tmux -L rt -f /dev/null"
$T kill-server 2>/dev/null || true
$T new-session -d -s rt -x 44 -y 24 "$BIN --seed 7; sleep 30"
snap() { $T capture-pane -t rt -e -p > "out/tui_$1.ansi"; $T capture-pane -t rt -p > "out/tui_$1.txt"; }
sleep 1
snap start
# 몇 조각 쌓기: 왼쪽 끝, 오른쪽 끝, 회전 후 가운데
for k in Left Left Left Left Space  Right Right Right Right Space  Up Space  z Left Space  c Space; do
  $T send-keys -t rt "$k"; sleep 0.15
done
sleep 0.3
snap play
$T send-keys -t rt p; sleep 0.3
snap pause
$T send-keys -t rt p
$T send-keys -t rt q; sleep 0.5
$T capture-pane -t rt -p > out/tui_after_quit.txt
$T kill-server 2>/dev/null || true
echo "녹화 완료: $(ls out/tui_*.ansi | wc -l)장"
