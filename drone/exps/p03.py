# -*- coding: utf-8 -*-
"""3부 — 역사 II. 연표·제품·쇼 기록 표(data/)에서 부의 표를 뽑는다.

출처 칸은 인용 키이거나, 키가 없는 행은 원문 주소의 도메인이다 —
주소 전체는 부록의 연표 표와 data/timeline.tsv 에 있다.
"""
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p01 import rows  # noqa: E402

PER = 12          # 접힌 화면에 드는 행 수 — 일(event) 칸이 두 줄씩 된다


def src(s):
    """'key;https://…' → 'key · 도메인' (여러 출처는 가운뎃점으로)."""
    out = []
    for part in s.split(';'):
        if part.startswith('http'):
            out.append(urlparse(part).netloc.replace('www.', ''))
        else:
            out.append(part)
    return ' · '.join(out)


def timeline(ctx, name, kinds, since='2005', until='2027'):
    got = [r for r in rows('timeline.tsv') if r['kind'] in kinds
           and since <= r['date'] < until]
    body = [[r['date'], r['event(ko)'], src(r['source'])] for r in got]
    for k in range(0, len(body), PER):
        ctx.table('p03_tl_%s_%d' % (name, k // PER + 1),
                  ['날짜', '일', '출처'], body[k:k + PER])
    return len(got)


def makers(ctx):
    """제품 표를 만든 곳마다 — 이 덱이 모은 범위 안에서."""
    by = {}
    for r in rows('products.tsv'):
        by.setdefault(r['maker'], []).append(int(r['year']))
    body = [[m, '%d' % len(ys), '%d–%d' % (min(ys), max(ys))]
            for m, ys in sorted(by.items(),
                                key=lambda kv: (-len(kv[1]), kv[0]))]
    ctx.table('p03_makers', ['만든 곳', '제품 수', '해'], body[:14],
              num=(1,))


def records(ctx):
    """기네스 인증 쇼만 — 대수 기록의 사다리."""
    best, body = 0, []
    for r in sorted(rows('shows.tsv'), key=lambda r: r['date']):
        n = int(r['drone-count'])
        if r['record'] == 'Guinness' and n > best:
            best = n
            body.append([r['date'], r['place'], r['organiser'],
                         '{:,}'.format(n), src(r['source'])])
    head = ['날짜', '곳', '주최', '대수', '출처']
    for k in range(0, len(body), PER):
        ctx.table('p03_records_%d' % (k // PER + 1), head,
                  body[k:k + PER], num=(3,))


def run(ctx):
    for name, kinds, since, until in (
            ('old', ('multirotor',), '1900', '2005'),
            ('fc', ('multirotor',), '2005', '2027'),
            ('consumer1', ('consumer',), '2005', '2016'),
            ('consumer2', ('consumer',), '2016', '2027'),
            ('racing', ('racing',), '2005', '2027'),
            ('delivery', ('delivery',), '2005', '2027'),
            ('law1', ('law',), '2005', '2017'),
            ('law2', ('law',), '2017', '2027'),
            ('industry', ('consumer',), '1985', '2005')):
        timeline(ctx, name, kinds, since, until)
    makers(ctx)
    records(ctx)
