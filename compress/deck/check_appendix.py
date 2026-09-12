#!/usr/bin/env python3
"""부록의 '소스 전문' 이 정말 전문인지 검사한다.

    python3 deck/check_appendix.py

왜 따로 필요한가: 조립기의 커버리지는 "그 줄이 **덱 어딘가에** 실렸는가"
만 본다. 본문 인용이 메워 준 줄이 있으면 부록에 구멍이 나도 100 % 가
나온다. 부록의 약속은 그것보다 세다 — **파일마다 1..N 이 끊김 없이
이어진다.** 그 약속을 여기서 본다. 3차 리뷰에서 쓰던 검사를 옮겨 왔다.

보는 것:
  A1  파일의 첫 조각이 1줄에서 시작하는가
  A2  마지막 조각이 파일 끝 줄에서 끝나는가
  A3  조각과 조각 사이에 빈 구간이나 겹침이 없는가
  A4  '몇 번째 / 전체 몇' 표시가 1..N 과 맞는가
  A5  조각 제목에 적힌 이름이 그 조각 코드 안에 있는가
      (여러 이름은 · 로 나뉜다. '머리말'·'이어서' 는 이름이 아니다)

조각 자체는 조립기(build_deck.py + chunks.py)가 만든다. 그러니 여기서
거르는 것은 "조립기가 바뀌었거나, FULLSRC 목록이 손으로 망가졌을 때"다.
시간은 덱 한 번 읽기 O(덱 크기).
"""
import html
import io
import os
import re
import sys

DECK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DECK)
TARGET = os.path.join(os.path.dirname(BASE), '압축_대백과사전.html')
SECTIONS = os.path.join(DECK, 'sections')

ART = re.compile(r'<article[^>]*id="([a-z]+-\d+)-(\d+)"[^>]*>(.*?)</article>',
                 re.S)
LN = re.compile(r'<span class="ln">(\d+)[–-](\d+)</span>')
TAG = re.compile(r'(\d+)/(\d+)</span>')
NOTE = re.compile(r'<span class="ln">[^<]*</span><span>([^<]*)</span>')
CODE = re.compile(r'<code[^>]*>(.*?)</code>', re.S)
# 이름이 아니라 자리 설명인 제목. 코드 안에서 찾으면 안 된다.
GENERIC = ('머리말', '이어서', '')


def read(path):
    return io.open(path, encoding='utf-8').read()


def listed():
    """부록에 전문을 싣기로 한 파일들 — 조각 파일의 <!--FULLSRC-->."""
    out = {}
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        for path, prefix in re.findall(
                r'^<!--FULLSRC file=(\S+) prefix=(\S+) title=',
                read(os.path.join(SECTIONS, name)), re.M):
            out[prefix] = path
    return out


def main():
    if not os.path.exists(TARGET):
        print('덱이 없다 — make deck 먼저')
        return 2
    files = listed()
    doc = read(TARGET)

    spans, tags, titles = {}, {}, []
    for prefix, _n, inner in ART.findall(doc):
        if prefix not in files:
            continue
        ln, tg = LN.search(inner), TAG.search(inner)
        if ln:
            spans.setdefault(prefix, []).append(
                (int(ln.group(1)), int(ln.group(2))))
        if tg:
            tags.setdefault(prefix, []).append(
                (int(tg.group(1)), int(tg.group(2))))
        note, code = NOTE.search(inner), CODE.search(inner)
        if note and code:
            titles.append((prefix, html.unescape(note.group(1)).strip(),
                           html.unescape(code.group(1))))

    errs = []
    for prefix, path in sorted(files.items()):
        rows = sorted(spans.get(prefix, []))
        if not rows:
            errs.append('%s: 부록에 조각이 하나도 없다' % path)
            continue
        n = len(read(os.path.join(BASE, path)).rstrip('\n').split('\n'))
        if rows[0][0] != 1:                                       # A1
            errs.append('%s: 첫 조각이 %d줄부터' % (path, rows[0][0]))
        if rows[-1][1] != n:                                      # A2
            errs.append('%s: 마지막 조각이 %d줄까지 (파일은 %d줄)'
                        % (path, rows[-1][1], n))
        for (a, b), (c, d) in zip(rows, rows[1:]):                # A3
            if c != b + 1:
                errs.append('%s: %d–%d 다음이 %d–%d' % (path, a, b, c, d))
        want = [(i + 1, len(rows)) for i in range(len(rows))]
        if sorted(tags.get(prefix, [])) != want:                  # A4
            errs.append('%s: 조각 번호 표시가 1..%d 와 다르다'
                        % (path, len(rows)))

    n_title = 0
    for prefix, title, code in titles:                            # A5
        if title in GENERIC:
            continue
        n_title += 1
        miss = [x.strip() for x in title.split('·')
                if x.strip() and x.strip() not in code]
        if miss:
            errs.append('%s: 조각 제목의 %s 가 그 코드에 없다'
                        % (files[prefix], ', '.join(miss)))

    for e in errs:
        print('  ✗ ' + e)
    print('부록 파일 %d개 · 조각 제목 %d개 — 어긋남 %d건'
          % (len(files), n_title, len(errs)))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
