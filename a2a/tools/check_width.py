#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_width — 예제 파일의 모든 줄이 72칸 안인지 본다.

   조립기는 슬라이드에 실리는 부분만 잰다. 그러면 실리지 않는 줄은
   넓어져도 아무도 모르고, 나중에 region 을 옮겨 싣는 순간 덱이
   깨진다. 그래서 make lint 가 파일 전체를 잰다. 한글(동아시아 넓은
   글자)은 2칸, 탭은 4칸 — 조립기와 같은 셈이다.

     python3 tools/check_width.py FILE…     넘는 줄을 찍고 종료 코드 1
"""
import io
import sys
import unicodedata

LIMIT = 72


def width(s):
    """화면에서 차지하는 칸 수. O(글자 수)."""
    s = s.replace('\t', '    ')
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1
               for c in s)


def over(paths):
    """[(경로, 줄 번호, 칸 수)] — LIMIT 을 넘는 줄만."""
    out = []
    for p in paths:
        with io.open(p, encoding='utf-8') as f:
            for no, line in enumerate(f, 1):
                w = width(line.rstrip('\n'))
                if w > LIMIT:
                    out.append((p, no, w))
    return out


def main(argv=None):
    paths = sys.argv[1:] if argv is None else argv
    bad = over(paths)
    for p, no, w in bad:
        print('  %s:%d — %d칸 (한도 %d)' % (p, no, w, LIMIT))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
