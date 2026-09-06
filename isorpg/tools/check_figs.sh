#!/bin/sh
# 도해를 눈으로 확인하기 위해 PNG 로 렌더한다.
# 덱의 CSS 를 SVG 안에 임시로 심고, 원본 viewBox 를 그대로 쓴다.
set -e
OUT=${1:-/tmp/figs}
mkdir -p "$OUT"
STYLE='<style>text{font-family:"Nanum Gothic",sans-serif;font-size:11px;fill:#2a2118}.tl{fill:#e6dcc6;stroke:#8a5a2b;stroke-width:1.2}.tl.on{fill:#f4d98a}.tl.hot{fill:#e8a37a}.tl.dim{fill:#d6cdb8}.tl.cool{fill:#b9cbdc}.tl.none{fill:none;stroke-dasharray:4 3}.gd{stroke:rgba(138,90,43,.35);stroke-width:.8;fill:none}.lbl{font-size:9px;fill:#6b5b46}.ax{stroke:#b04a2a;stroke-width:1.4;fill:none}</style><rect width="100%" height="100%" fill="#f6f1e6"/>'
for f in deck/figs/*.svg; do
  n=$(basename "$f" .svg)
  sed -e 's|<svg class="diag" |<svg xmlns="http://www.w3.org/2000/svg" class="diag" |' \
      -e "s|<title>|$STYLE<title>|" "$f" > "$OUT/$n.wrap.svg"
  rsvg-convert -w 900 -o "$OUT/$n.png" "$OUT/$n.wrap.svg"
done
echo "렌더 완료: $OUT"
