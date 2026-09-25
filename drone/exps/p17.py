# -*- coding: utf-8 -*-
"""17부 — 미래와 진로. 법령 표(data/law.tsv)에서 원격 ID·조종 자격·
교통 관리 조문을 골라 표로 만든다."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p01 import rows  # noqa: E402

PICK = {
    'rid': [('US', '§89.105'), ('US', '§89.110'), ('US', '§89.115'),
            ('US', '§89.305'), ('US', '§89.205')],
    'pilot': [('KR', '제125조'), ('KR', '제306조'), ('US', '§107.12'),
              ('US', '§107.61'), ('US', '§107.65'), ('EU', 'Article 9')],
    'future': [('KR', '제10조'), ('KR', '제17조'), ('EU', 'Article 6')],
}


def pick(pairs):
    law = rows('law.tsv')
    out = []
    for jur, art in pairs:
        hit = [r for r in law if r['jurisdiction'] == jur
               and r['article'] == art]
        if not hit:
            raise RuntimeError('law.tsv 에 %s %s 가 없다' % (jur, art))
        out += hit
    return out


def run(ctx):
    for name, pairs in sorted(PICK.items()):
        got = pick(pairs)
        body = [[r['jurisdiction'], r['article'], r['requirement(ko)']]
                for r in got]
        for k in range(0, len(body), 8):
            ctx.table('p17_%s_%d' % (name, k // 8 + 1),
                      ['관할', '조문', '요지'], body[k:k + 8])
