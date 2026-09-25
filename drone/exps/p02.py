# -*- coding: utf-8 -*-
"""2부 — 역사 I. 연표(data/timeline.tsv)의 2004년까지를 10년
단위로 센다."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p01 import rows  # noqa: E402

KINDS = [('military', '군용'), ('hobby', 'RC 취미'),
         ('multirotor', '멀티로터'), ('consumer', '민간·산업')]


def decades(ctx):
    """1840년대 … 2000년대 초 — 갈래마다 행 수. 빈 10년은 뺀다."""
    count = {}
    for r in rows('timeline.tsv'):
        y = int(r['date'][:4])
        if y >= 2005:
            continue
        d = y // 10 * 10
        count.setdefault(d, {})
        count[d][r['kind']] = count[d].get(r['kind'], 0) + 1
    table = []
    for d in sorted(count):
        c = count[d]
        cells = ['%d' % c.get(k, 0) for k, _ in KINDS]
        table.append(['%d년대' % d] + cells + ['%d' % sum(c.values())])
    ctx.table('p02_decades', ['10년'] + [n for _, n in KINDS] + ['합'],
              table, num=(1, 2, 3, 4, 5))


def run(ctx):
    decades(ctx)
