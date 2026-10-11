#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""역검증 — 다 만든 덱을 다시 읽어, 실린 코드·출력이 원본과 같은지 본다.

   조립기를 믿지 않기 위한 도구다. 덱의 모든 <pre> 는 data-src(원본 파일)와
   data-lines(줄 범위)를 달고 있어야 하고, 그 글자가 원본의 그 줄과 같아야
   한다. 원본이 예제면 캡처가 낡지 않았는지도(rsrun 장부) 다시 본다.
   덱을 손으로 고쳤거나, 조립 뒤에 예제를 고치고 다시 안 돌렸으면 여기서 걸린다.
"""
import html
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)
import build_deck  # noqa: E402
import rsrun  # noqa: E402

PRE = re.compile(r'<pre\b([^>]*)>(.*?)</pre>', re.S)


def _text(inner):
    """<pre> 안쪽 → 원본 글자. 태그를 걷고 엔티티를 푼다."""
    return html.unescape(re.sub(r'<[^>]+>', '', inner))


def verify(root, deck_html):
    """문제의 목록을 돌려준다. 비었으면 덱과 원본이 같다."""
    bad = []
    main = deck_html.split('<main', 1)[-1].split('</main>', 1)[0]
    manifest = rsrun.manifest_load(root)
    n = 0
    for m in PRE.finditer(main):
        attrs, inner = m.group(1), m.group(2)
        if re.search(r'class="fig"', attrs):
            continue
        n += 1
        src = re.search(r'data-src="([^"]+)"', attrs)
        rng = re.search(r'data-lines="(\d+)-(\d+)"', attrs)
        if not src or not rng:
            bad.append('원본 표시가 없는 <pre>: %s' % _text(inner)[:40].replace('\n', '⏎'))
            continue
        rel, lo, hi = src.group(1), int(rng.group(1)), int(rng.group(2))
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            bad.append('원본이 없다: %s' % rel)
            continue
        text = build_deck.read(p)
        if rel.startswith('ex/') and rel.endswith('.rs'):
            text, _ = rsrun.parse_directives(text)
        lines = text.split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        want = '\n'.join(lines[lo - 1:hi]) + '\n'
        if _text(inner) != want:
            bad.append('덱과 원본이 다르다: %s %d-%d' % (rel, lo, hi))
        if rel.startswith('out/'):
            ex = 'ex/' + rel[4:-4]
            if os.path.isfile(os.path.join(root, ex + '.rs')):
                ex += '.rs'
            why = rsrun.stale(root, ex, manifest)
            if why:
                bad.append('캡처가 낡았다: %s (%s)' % (rel, why))
    verify.count = n
    return bad


def main():
    target = os.path.join(os.path.dirname(ROOT), build_deck.TARGET_NAME)
    with io.open(target, encoding='utf-8') as f:
        deck = f.read()
    bad = verify(ROOT, deck)
    for b in bad:
        print('  ✗ ' + b)
    slides = len(re.findall(r'<article\b', deck.split('<main', 1)[-1].split('</main>', 1)[0]))
    print('  역검증 — 슬라이드 %d장, 코드·출력 블록 %d개, 어긋남 %d건' % (slides, verify.count, len(bad)))
    if slides > build_deck.HARD_CAP:
        print('  ✗ %d장 — 상한 %d장을 넘었다' % (slides, build_deck.HARD_CAP))
        return 1
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
