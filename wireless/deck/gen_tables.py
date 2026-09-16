#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/*.tsv (+ out/manifest.json) → 덱이 싣는 HTML 표를 만든다.

    python3 deck/gen_tables.py           # out/tbl_*.html 을 다시 만든다
    python3 deck/gen_tables.py --check   # 지금 것과 같은지 대조만 한다

왜 표를 손으로 안 쓰는가: 이 덱의 표는 대부분 "연도·규격 번호·대역 번호"
같은 사실의 나열이다. 그런 표는 한 칸만 틀려도 티가 안 나고, 본문과 표가
어긋나면 어느 쪽이 맞는지 아무도 모른다. 사실은 data/*.tsv 한 곳에만 적고
(행마다 출처 칸이 있다), 표는 거기서 만든다. 그러면 고칠 곳이 늘 한 곳이다.

새 표가 필요하면 VIEWS 에 한 줄 더한다. TSV 전체를 그대로 싣는 표는
따로 적지 않아도 tbl_<이름>.html 로 언제나 만들어진다.

시간·공간 모두 O(행 수).
"""
import html
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data')
OUT = os.path.join(BASE, 'out')

# 잘라 보는 표. (내보낼 이름, 원본 tsv, 실을 칸 이름들, 거르개)
# 거르개는 (칸 이름, 값) — 그 칸이 그 값인 행만 싣는다. 없으면 전부.
VIEWS = [
    # PLAN.md §5 8단계에서 부를 쓸 때마다 한 줄씩 는다.
    ('gen_glance.html', 'generations.tsv',
     ['generation', 'standard', 'access', 'bandwidth', 'peak_rate',
      'first_launch'], None),
    ('releases_short.html', 'releases.tsv',
     ['release', 'freeze', 'features'], None),
]

# 이 칸은 표에 글자로 싣지 않고 '출처' 링크로 바꾼다.
LINKCOLS = ('source', 'url')


def read(p):
    return io.open(p, encoding='utf-8').read()


def rows_of(name):
    """TSV 를 (칸 이름 목록, 행 목록) 으로. 첫 줄이 칸 이름, #은 주석."""
    text = read(os.path.join(DATA, name))
    head, body = None, []
    for line in text.split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('\t')]
        if head is None:
            head = cols
        else:
            # 칸이 모자라면 빈 칸으로 채운다 — 줄이 어긋나는 것보다 낫다
            cols += [''] * (len(head) - len(cols))
            body.append(cols[:len(head)])
    return head or [], body


def is_num(v):
    try:
        float(v.replace(',', ''))
        return True
    except ValueError:
        return False


def render(head, body, cols=None):
    """<table> 한 덩어리. 칸 이름은 그대로 머리글이 된다."""
    idx = [head.index(c) for c in cols] if cols else list(range(len(head)))
    numeric = [all(is_num(r[i]) for r in body) if body else False for i in idx]
    out = ['<table>']
    out.append('<tr>' + ''.join(
        '<th%s>%s</th>' % (' class="num"' if numeric[k] else '',
                           html.escape(head[i]))
        for k, i in enumerate(idx)) + '</tr>')
    for r in body:
        tds = []
        for k, i in enumerate(idx):
            v = r[i]
            if head[i] in LINKCOLS and v.startswith('http'):
                cell = '<a href="%s">출처</a>' % html.escape(v, quote=True)
            else:
                cell = html.escape(v)
            tds.append('<td%s>%s</td>'
                       % (' class="num"' if numeric[k] else '', cell))
        out.append('<tr>' + ''.join(tds) + '</tr>')
    out.append('</table>')
    return '\n'.join(out) + '\n'


def build():
    """{내보낼 파일 이름: 내용}. 파일로 쓰기 전의 순수한 계산이다."""
    made = {}
    if not os.path.isdir(DATA):
        return made
    for name in sorted(os.listdir(DATA)):
        if not name.endswith('.tsv'):
            continue
        head, body = rows_of(name)
        if not head:
            continue
        made['tbl_%s.html' % name[:-4]] = render(head, body)
    for out_name, tsv, cols, filt in VIEWS:
        head, body = rows_of(tsv)
        if filt:
            col, want = filt
            body = [r for r in body if r[head.index(col)] == want]
        made[out_name] = render(head, body, cols)
    return made


def manifest_note():
    """out/manifest.json 이 있으면 몇 개의 캡처가 표에 쓰였는지 한 줄로."""
    p = os.path.join(OUT, 'manifest.json')
    if not os.path.exists(p):
        return '  (out/manifest.json 아직 없다 — make run 먼저)'
    return '  out/manifest.json 의 캡처 %d개' % len(json.loads(read(p)))


def main(argv):
    made = build()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(OUT, name)
            if not os.path.exists(p):
                bad.append('%s 가 없다' % name)
            elif read(p) != want:
                bad.append('%s 가 data/ 와 어긋난다' % name)
        for line in bad:
            print('  ✗ ' + line)
        print('생성 표 %d개 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, text in sorted(made.items()):
        io.open(os.path.join(OUT, name), 'w',
                encoding='utf-8', newline='\n').write(text)
    print('생성 표 %d개 → out/' % len(made))
    print(manifest_note())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
