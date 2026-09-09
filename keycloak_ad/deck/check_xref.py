#!/usr/bin/env python3
"""상호참조 검사 — "N부 M장" 이라고 적힌 것이 진짜 그 자리인가.

    python3 deck/check_xref.py

덱은 앞뒤로 계속 서로를 가리킨다("1부 6장에서 본 그 쿠키다"). 그 화살표는
글로만 적혀 있어서, 장을 하나 끼워 넣으면 **아무 소리 없이 전부 한 칸씩
어긋난다.** 14단계 전수 리뷰에서 이런 것을 다섯 건 찾았다. 그래서 도구로 옮겼다.

두 가지를 본다.

  1. `<a href="#id">N부 M장</a>` — 링크가 가리키는 슬라이드가 실제로
     그 부 그 장에 있는가. (id 가 실재하는지는 check_deck.js 가 본다.)
  2. 링크 없이 글로만 적은 "N부 M장" — 그 부에 그 장이 있기는 한가.

뜻이 맞는지(그 장이 정말 그 이야기를 하는지)는 기계가 못 본다. 사람이 본다.
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = os.path.join(HERE, 'sections')
ART = re.compile(r'<article[^>]*id="([^"]+)"[^>]*>(.*?)</article>', re.S)
CHNUM = re.compile(r'<p class="chnum">([^<]+)</p>')


def scan():
    """슬라이드 id → (부, 장). 부·장 표지가 나올 때마다 갈아 끼운다."""
    where, chaps = {}, {}
    for f in sorted(glob.glob(os.path.join(SECTIONS, '*.html'))):
        part = chap = None
        for m in ART.finditer(io.open(f, encoding='utf-8').read()):
            cm = CHNUM.search(m.group(2))
            if cm:
                v = cm.group(1).strip()
                if v.endswith('부'):
                    part, chap = v[:-1], None
                elif v.endswith('장'):
                    chap = v[:-1]
                    if part:
                        chaps[part] = max(chaps.get(part, 0), int(chap))
            where[m.group(1)] = (part, chap)
    return where, chaps


def main():
    where, chaps = scan()
    bad, n_link, n_text = [], 0, 0
    for f in sorted(glob.glob(os.path.join(SECTIONS, '*.html'))):
        name = os.path.basename(f)
        text = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r'<a href="#([^"]+)">([^<]*)</a>', text):
            aid, label = m.group(1), m.group(2)
            pm = re.search(r'(\d+)부', label)
            cm = re.search(r'(\d+)(?:·\d+)*장', label)
            if not (pm or cm):
                continue
            n_link += 1
            p, c = where.get(aid, (None, None))
            if pm and p and p != pm.group(1):
                bad.append('%s: #%s 는 %s부인데 "%s" 라고 적혀 있다'
                           % (name, aid, p, label))
            elif cm and c and cm.group(1) != c:
                bad.append('%s: #%s 는 %s장인데 "%s" 라고 적혀 있다'
                           % (name, aid, c, label))
        for m in re.finditer(r'(\d+)부\s*(\d+)장', text):
            p, c = m.group(1), int(m.group(2))
            n_text += 1
            if p in chaps and c > chaps[p]:
                bad.append('%s: "%s" — %s부는 %d장까지다'
                           % (name, m.group(0), p, chaps[p]))
    for line in bad:
        print('  ' + line)
    print('상호참조: 링크 %d개 · 글로 적은 것 %d개 — 어긋남 %d건'
          % (n_link, n_text, len(bad)))
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
