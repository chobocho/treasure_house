# -*- coding: utf-8 -*-
"""width.py — 덱에 실릴 소스 파일이 폴더블 폭을 넘지 않는지 본다.

왜 글자 수가 아니라 칸 수인가: 고정폭 글꼴에서 한글은 정확히 두 칸이다.
한글 주석 40글자는 80칸이고, 갤럭시 폴드 접힘(374px)에서 <pre> 는 약
72칸에서 잘린다. 글자 수로 세면 "짧아 보이는데 잘리는" 줄을 못 잡는다.

조립기(deck/build_deck.py)가 완성된 덱에서 같은 검사를 한다. 이 도구는
덱을 만들기 전에 소스 쪽에서 먼저 잡으려고 있다 — 조립 뒤에 알면
어느 줄을 고쳐야 하는지 되짚어야 한다.

    python3 tools/width.py web/**/*.go        # 넘는 줄만 보여 준다
    python3 tools/width.py --max 72 web/01_hello/main.go
"""
import io
import os
import sys
import unicodedata

TABSTOP = 4          # 덱 CSS 의 tab-size 와 같아야 한다
DEFAULT_MAX = 72


def cells(s):
    """화면 칸 수. 한글·CJK(W/F)만 두 칸. O(글자 수)."""
    n = 0
    for ch in s:
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def check(path, limit=DEFAULT_MAX):
    """(줄번호, 칸수, 줄) 목록. 비어 있으면 통과."""
    out = []
    text = io.open(path, encoding='utf-8').read()
    for i, line in enumerate(text.split('\n'), 1):
        w = cells(line.expandtabs(TABSTOP))
        if w > limit:
            out.append((i, w, line))
    return out


def main(argv):
    limit = DEFAULT_MAX
    if '--max' in argv:
        k = argv.index('--max')
        limit = int(argv[k + 1])
        del argv[k:k + 2]
    paths = [p for p in argv if not p.startswith('--')]
    if not paths:
        sys.stderr.write(__doc__)
        return 2
    total = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        bad = check(p, limit)
        total += len(bad)
        for i, w, line in bad:
            print('  %s:%d  %d칸  %s' % (p, i, w, line.expandtabs(TABSTOP)[:60]))
    if total:
        print('%d칸을 넘는 줄 %d개' % (limit, total))
        return 1
    print('%d개 파일 — %d칸을 넘는 줄 없음' % (len(paths), limit))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
