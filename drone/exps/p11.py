# -*- coding: utf-8 -*-
"""11부 — 드론쇼 I. 관객의 눈(원근·감마), 쇼 관련 조문, 쇼 기록의 주최."""
import math
import os
import sys

from droneshow import render as R

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p01 import rows  # noqa: E402



def perspective(ctx):
    """T33 — 보이는 각 2·atan(W/2D) 와 어림 W/D."""
    body = []
    for w in (20.0, 60.0, 120.0):
        for d in (100.0, 300.0):
            a = R.apparent_size(w, d)
            body.append(['%g' % w, '%g' % d, '%.3f' % math.degrees(a),
                         '%.3f' % math.degrees(w / d),
                         '%.2f' % (100 * (w / d - a) / a)])
    head = ['너비 W[m]', '거리 D[m]', '보이는 각[°]', 'W/D[°]',
            '어림의 오차[%]']
    ctx.table('p11_angle', head, body, num=(0, 1, 2, 3, 4))
    body = []
    base = R.apparent_size(40.0, 200.0)
    for dd in (-20.0, -10.0, -5.0, 0.0, 5.0, 10.0, 20.0):
        a = R.apparent_size(40.0, 200.0 + dd)
        body.append(['%+g' % dd, '%.3f' % math.degrees(a),
                     '%+.2f' % (100 * (a - base) / base)])
    ctx.table('p11_depth', ['깊이 변화[m]', '보이는 각[°]', '크기 변화[%]'],
              body, num=(0, 1, 2))


def gamma(ctx):
    """L22·T34 — 부호 값과 빛의 양, 두 가지 섞기."""
    body = [['%d' % v, '%.4f' % (v / 255), '%.4f' % R.decode(v),
             '%d' % R.encode(R.decode(v))]
            for v in (0, 32, 64, 128, 186, 255)]
    ctx.table('p11_gamma', ['부호 값 v', 'v/255', '빛의 양', '되돌린 값'],
              body, num=(0, 1, 2, 3))
    red, green = [255, 0, 0], [0, 255, 0]
    lines = ['빨강 (255,0,0) 과 초록 (0,255,0) 을 반반 섞기']
    for name, lin in (('부호 값 평균', False), ('빛의 양 평균', True)):
        c = R.mix_codes(red, green, 0.5, lin)
        light = sum(R.decode(x) for x in c)
        lines.append('  %-8s → (%d,%d,%d) · 빛의 양 합 %.3f'
                     % (name, c[0], c[1], c[2], light))
    ctx.text('p11_mix', '\n'.join(lines))


# 쇼와 직접 이어지는 조문 — data/law.tsv 의 (관할, 조문) 과 요지의 앞머리
SHOW_LAW = [('KR', '제310조', '일몰 후부터'),
            ('KR', '제310조', '무인비행장치 조종자는 기체를'),
            ('KR', '제310조', '인구 밀집'),
            ('KR', '제129조', '무인비행장치 조종자는 야간'),
            ('KR', '제312조의2', '야간 비행이나'),
            ('KR', '제312조의2', '지방항공청장은'),
            ('US', '§107.29', ''), ('US', '§107.31', ''), ('US', '§107.35', ''),
            ('US', '§107.39', ''), ('US', '§107.200', ''), ('US', '§107.205', ''),
            ('EU', 'Article 5', ''), ('EU', 'UAS.SPEC.020', '')]


def law(ctx):
    got = []
    for jur, art, head in SHOW_LAW:
        hit = [r for r in rows('law.tsv') if r['jurisdiction'] == jur
               and r['article'] == art
               and r['requirement(ko)'].startswith(head)]
        if len(hit) != 1:
            raise RuntimeError('law.tsv 에서 %s %s %r 이 %d 행'
                               % (jur, art, head, len(hit)))
        got.append(hit[0])
    for tag, part in (('kr', got[:6]), ('us_eu', got[6:])):
        body = [[r['jurisdiction'], r['article'], r['requirement(ko)']]
                for r in part]
        ctx.table('p11_law_' + tag, ['관할', '조문', '요지'], body)


# 같은 회사를 표가 두 이름으로 적은 경우 — 한 줄로 센다
ALIAS = {'유비파이': 'UVify'}


def organisers(ctx):
    """쇼 기록 표의 나라·주최 — 산업 지도의 한 조각."""
    by_c, by_o = {}, {}
    for r in rows('shows.tsv'):
        c = r['place'].split()[0].split('(')[0]
        by_c[c] = by_c.get(c, 0) + 1
        for o in r['organiser'].replace(' 외', '').split('·'):
            o = ALIAS.get(o.strip(), o.strip())
            by_o[o] = by_o.get(o, 0) + 1
    body = [[c, '%d' % n] for c, n in
            sorted(by_c.items(), key=lambda kv: (-kv[1], kv[0]))][:10]
    ctx.table('p11_countries', ['나라', '쇼 기록 행'], body, num=(1,))
    body = [[o, '%d' % n] for o, n in
            sorted(by_o.items(), key=lambda kv: (-kv[1], kv[0]))][:12]
    ctx.table('p11_organisers', ['주최·제작', '쇼 기록 행'], body, num=(1,))


def run(ctx):
    perspective(ctx)
    gamma(ctx)
    law(ctx)
    organisers(ctx)
