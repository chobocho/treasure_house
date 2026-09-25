# -*- coding: utf-8 -*-
"""1부 — 드론이란 무엇인가. 자료 표(data/)를 세어 쓰임새 지도를 만든다."""
import io
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASS = {'consumer': '소비자(촬영)', 'prosumer': '준전문가', 'enterprise':
         '산업·점검', 'agri': '농업(방제)', 'delivery': '배송',
         'racing': '레이싱·FPV', 'show': '드론쇼', 'autopilot':
         '비행 제어기', 'component': '부품', 'kit': '조립 키트',
         'passenger': '사람 수송'}


def rows(name):
    out, head = [], None
    with io.open(os.path.join(HERE, 'data', name), encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            cols = line.split('\t')
            if head is None:
                head = cols
            else:
                out.append(dict(zip(head, cols)))
    return out


def products(ctx):
    """제품 표의 갈래마다 수와 처음·마지막 해."""
    by = {}
    for r in rows('products.tsv'):
        by.setdefault(r['class'], []).append(int(r['year']))
    table = []
    for k, ys in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        table.append([CLASS.get(k, k), '%d' % len(ys), '%d' % min(ys),
                      '%d' % max(ys)])
    ctx.table('p01_products', ['쓰임새', '제품 수', '처음', '마지막'],
              table, num=(1, 2, 3))


def run(ctx):
    products(ctx)
