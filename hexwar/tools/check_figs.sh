#!/bin/sh
# 도해를 눈으로 확인하기 위해 PNG 로 렌더한다.
# 덱의 CSS 를 SVG 안에 임시로 심고, 원본 viewBox 를 그대로 쓴다.
set -e
OUT=${1:-/tmp/figs}
mkdir -p "$OUT"
STYLE='<style>text{font-family:"Nanum Gothic",sans-serif;font-size:11px;fill:#23301c}.hx{fill:#dfe6cd;stroke:#4a6b34;stroke-width:1.2}.hx.on{fill:#f4d98a}.hx.hot{fill:#e8a37a}.hx.dim{fill:#cfd4c2}.lbl{font-size:9px;fill:#5d6b4e}.ax{stroke:#b04a2a;stroke-width:1.4;fill:none}</style><rect width="100%" height="100%" fill="#f4f6ec"/>'
for f in deck/figs/*.svg; do
  n=$(basename "$f" .svg)
  sed -e 's|<svg class="diag" |<svg xmlns="http://www.w3.org/2000/svg" class="diag" |' \
      -e "s|<title>|$STYLE<title>|" "$f" > "$OUT/$n.wrap.svg"
  rsvg-convert -w 900 -o "$OUT/$n.png" "$OUT/$n.wrap.svg"
done
echo "렌더 완료: $OUT"
