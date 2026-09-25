#!/bin/sh
# pdf_text.sh — PDF 한 편을 인용할 수 있는 글로 (절 제목은 '§' 줄).
#
#   sh tools/pdf_text.sh 글.pdf > 글.txt
#
# pdftotext(poppler-utils, §9 결정 7)의 -layout 으로 먼저 뽑는다.
# 한 단 보고서는 이것이 가장 원문에 가깝다(줄머리 번호 제목·식의
# 자리가 산다). 두 단 논문은 -layout 이 두 단을 한 줄에 섞어 문장을
# 인용할 수 없게 되므로, pdf_sections.py --columns 가 2 를 내면
# 읽기 차례(-layout 없이)로 다시 뽑는다. 제목 찾기는 pdf_sections.py.
set -eu
here=$(dirname "$0")
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
pdftotext -layout -enc UTF-8 "$1" "$tmp"
if [ "$(python3 "$here/pdf_sections.py" --columns "$tmp")" = 2 ]; then
  pdftotext -enc UTF-8 "$1" "$tmp"
fi
python3 "$here/pdf_sections.py" "$tmp"
