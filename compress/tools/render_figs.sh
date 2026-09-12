#!/bin/sh
# render_figs.sh — 도해를 PNG 로 떠서 **눈으로 본다.**
#
#   sh tools/render_figs.sh            # build/figs/*.png
#   sh tools/render_figs.sh kraft      # 한 장만
#
# 덱에 실리는 SVG 는 색을 CSS 변수로 쓴다(head.html 의 팔레트를 따라
# 가야 하므로). rsvg-convert 는 그 변수를 모르기 때문에, 여기서 임시
# 복사본을 만들어 변수를 그때의 literal 색으로 바꿔 넣는다. **원본은
# 건드리지 않는다** — 덱에 실리는 것은 변수 쪽이다.
set -eu
cd "$(dirname "$0")/.."

SRC=deck/figs
TMP=build/figs_lit
OUTD=build/figs
mkdir -p "$TMP" "$OUTD"

only="${1:-}"

for f in "$SRC"/*.svg; do
  name=$(basename "$f" .svg)
  [ -z "$only" ] || [ "$only" = "$name" ] || continue
  sed -e 's/var(--border)/#9fb4d0/g' \
      -e 's/var(--accent2)/#23375c/g' \
      -e 's/var(--accent)/#3a5c96/g' \
      -e 's/var(--special)/#7c3aed/g' \
      -e 's/var(--muted)/#55708f/g' \
      -e 's/var(--text)/#16283d/g' \
      -e 's/var(--panel)/#ffffff/g' \
      -e 's/var(--ok)/#2e9e5b/g' \
      -e 's/var(--warn)/#d97706/g' \
      -e 's/var(--bad)/#cb2c2c/g' \
      -e 's/var(--net)/#7b8794/g' \
      -e 's/class="diag"/class="diag" style="background:#fff"/' \
      "$f" >"$TMP/$name.svg"
  # 클래스 규칙은 head.html 에 있다. 렌더용 복사본에는 그 규칙만
  # 최소로 넣어 준다 — 안 넣으면 상자가 전부 검게 칠해진다.
  python3 - "$TMP/$name.svg" <<'PY'
import io, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read()
css = ('<style>text{font-family:sans-serif;font-size:12px;fill:#16283d}'
       '.lbl{font-size:11px;fill:#55708f}'
       '.box{fill:#fff;stroke:#9fb4d0;stroke-width:1.4;rx:8px}'
       '.box.off{fill:none;stroke-dasharray:4 3}'
       '.arw{stroke:#7b8794;stroke-width:1.6;fill:none;'
       'marker-end:url(#ah)}'
       'marker path{fill:#7b8794;stroke:none}</style>')
s = s.replace('>', '>' + css, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
PY
  rsvg-convert -w 680 -b '#ffffff' -o "$OUTD/$name.png" "$TMP/$name.svg"
done

echo "  build/figs/ 에 PNG 를 떴다 — 눈으로 볼 것"
