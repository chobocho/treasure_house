#!/usr/bin/env python3
"""용어집을 만든다 — 그리고 가리키는 자리가 실재하는지 검사한다.

    python3 deck/gen_glossary.py           # 슬라이드 조각을 찍는다
    python3 deck/gen_glossary.py --check   # 검사만 한다

원본은 deck/glossary.txt 한 파일이다. 한 줄에 하나:

    낱말 | 한 줄 뜻 | 처음 나온 슬라이드 id

세 번째 칸이 이 도구의 요점이다. **그 id 가 실재하지 않으면
덱이 만들어지지 않는다.** 용어집은 시간이 지나면 본문과 어긋나기
마련인데, 적어도 "어디를 보라" 는 화살표만은 어긋나지 않게 한다.

§8 12단계 이탈(기록): PLAN 은 슬라이드의 data-term 속성을 긁어
만들라고 했다. 그렇게 하면 낱말 예순 개의 뜻이 열두 파일에 흩어져
한눈에 볼 수 없고, 고르는 기준도 안 보인다. 한 파일에 모으고
**화살표만 기계가 검사**하는 쪽을 골랐다.
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = os.path.join(HERE, 'sections')
SRC = os.path.join(HERE, 'glossary.txt')
PER_SLIDE = 9   # 한 장에 몇 낱말. 접힌 화면에서 안 잘리는 수


def slide_ids():
    ids = set()
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        with open(os.path.join(SECTIONS, name), encoding='utf-8') as f:
            ids |= set(re.findall(r'id="([^"]+)"', f.read()))
    return ids


def entries():
    out = []
    with open(SRC, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            line = line.split('#')[0].strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) != 3:
                sys.exit('%s:%d 칸이 %d개 — 셋이어야 한다'
                         % (SRC, n, len(parts)))
            out.append(tuple(parts))
    return out


def check(rows, ids):
    """어긋난 곳을 사람이 읽을 문장으로 돌려준다.

    조립기도 이 목록을 그대로 자기 오류 목록에 붙인다.
    """
    bad = ['%s → %s 라는 슬라이드가 없다' % (t, w)
           for t, _, w in rows if w not in ids]
    dup = {}
    for t, _, _ in rows:
        dup[t] = dup.get(t, 0) + 1
    for t, n in sorted(dup.items()):
        if n > 1:
            bad.append('%s 가 %d번 적혔다' % (t, n))
    return bad


def render(rows):
    parts = []
    rows = sorted(rows, key=lambda r: r[0].lower())
    for i in range(0, len(rows), PER_SLIDE):
        chunk = rows[i:i + PER_SLIDE]
        num = i // PER_SLIDE + 1
        body = ['<article class="card" id="wr-gl-%d">' % num,
                '<h3>용어집 %d — %s ~ %s</h3>'
                % (num, html.escape(chunk[0][0]),
                   html.escape(chunk[-1][0])),
                '<div class="tblwrap">', '<table class="kv">',
                '<tr><th>낱말</th><th>뜻</th><th>어디</th></tr>']
        for term, meaning, where in chunk:
            body.append('<tr><td><b>%s</b></td><td>%s</td>'
                        '<td><a href="#%s">보기</a></td></tr>'
                        % (html.escape(term), meaning, where))
        body += ['</table>', '</div>', '</article>']
        parts.append('\n'.join(body))
    return '\n\n'.join(parts)


def main(argv):
    rows = entries()
    bad = check(rows, slide_ids())
    if bad:
        for line in bad:
            print('  ' + line)
        sys.exit('용어집: 어긋남 %d건' % len(bad))
    if '--check' in argv:
        print('  용어 %d개 · 가리키는 자리 전부 실재' % len(rows))
        return
    print(render(rows))


if __name__ == '__main__':
    main(sys.argv[1:])
