# -*- coding: utf-8 -*-
"""16부 — 실습: 쇼 한 편을 12·60·300 대로 짜고, 재고, 날리고, 내보낸다.

명령은 독자가 그대로 따라 칠 수 있게 ex/lab_show.py·ex/lab_check.py 와
droneshow CLI 로만 부른다. 물리 모드는 느리므로(한 대 × 쇼 1초 ≈
0.06초) 12 대는 전부, 60·300 대는 가장 멀리 나는 몇 대만 날린다.
"""
import json
import math
import os

ENV = {'PYTHONPATH': 'py'}
SHOWS = [('12', []), ('60', []), ('300', []),
         ('300_flat', ['--layers', '1']), ('60_tight', ['--tight'])]


def load(name):
    with open('out/show_p16_%s.json' % name, encoding='utf-8') as f:
        return json.load(f)


def path_len(d):
    kf = d['keyframes']
    return sum(math.dist(a[1:4], b[1:4]) for a, b in zip(kf, kf[1:]))


def longest(show, k):
    """이동 거리가 가장 긴 드론 k 대의 id — 물리 모드에서 가장
    힘든 것."""
    ds = sorted(show['drones'], key=lambda d: (-path_len(d), d['id']))
    return sorted(d['id'] for d in ds[:k])


def plans(ctx):
    for name, extra in SHOWS:
        n = name.split('_')[0]
        ctx.py('p16_plan%s' % name, 'ex/lab_show.py', n, *extra,
               '-o', 'out/show_p16_%s.json' % name)
        ctx.adopt('show_p16_%s.json' % name)
    for n in ('60', '300'):
        ctx.py('p16_info' + n, '-m', 'droneshow', 'info',
               'out/show_p16_%s.json' % n, env=ENV)


def checks(ctx):
    for name, _extra in SHOWS:
        bad = name in ('300_flat', '60_tight')
        ctx.py('p16_check%s' % name, 'ex/lab_check.py',
               'out/show_p16_%s.json' % name, expect=1 if bad else 0)


def extent(pts, k):
    return max(p[k] for p in pts) - min(p[k] for p in pts)


def scale(ctx):
    """판마다 그림 크기와 시간 — 윤곽선 모양은 대수에 비례해 커진다."""
    rows = []
    for name, _extra in SHOWS[:4]:
        s = load(name)
        sc = {m['name']: m for m in s['scenes']}
        t_heart = sc['heart']['t0'] + 0.5
        pts = [position(s, d, t_heart) for d in s['drones']]
        hold = sum(m['t1'] - m['t0'] for m in s['scenes'])
        top = max(p[2] for p in pts)
        rows.append([name.replace('_flat', ' (한 겹)'),
                     '%d' % len(s['drones']),
                     '%.1f' % extent(pts, 0), '%.1f' % top,
                     '%.1f' % (s['duration'] - hold),
                     '%.1f' % s['duration']])
    head = ['판', '대수', '하트 폭[m]', '하트 꼭대기[m]', '전환 합[s]',
            '쇼 길이[s]']
    ctx.table('p16_scale', head, rows, num=(1, 2, 3, 4, 5))


def position(show, d, t):
    from droneshow import show as SH
    return SH.position(show, d, t)


def transitions(ctx):
    """300 대 판의 전환마다 — 가장 먼 드론의 거리가 시간을 정한다."""
    s = load('300')
    rows, prev = [], s['scenes'][0]
    for m in s['scenes'][1:]:
        a = [position(s, d, prev['t1']) for d in s['drones']]
        b = [position(s, d, m['t0']) for d in s['drones']]
        far = max(math.dist(p, q) for p, q in zip(a, b))
        rows.append(['%s → %s' % (prev['name'], m['name']),
                     '%.1f' % far, '%.2f' % (m['t0'] - prev['t1'])])
        prev = m
    head = ['전환', '가장 먼 드론[m]', '전환 시간[s]']
    ctx.table('p16_trans300', head, rows, num=(1, 2))


def fly(ctx):
    ids12 = ','.join(str(i) for i in range(12))
    ctx.py('p16_fly12', '-m', 'droneshow', 'fly',
           'out/show_p16_12.json', '--mode', 'physics', '--ids', ids12,
           env=ENV)
    for name, k in (('60', 4), ('300', 3)):
        ids = ','.join(str(i) for i in longest(load(name), k))
        ctx.py('p16_fly%s' % name, '-m', 'droneshow', 'fly',
               'out/show_p16_%s.json' % name, '--mode', 'physics',
               '--ids', ids, env=ENV)


def export(ctx):
    os.makedirs('scratch/p16csv', exist_ok=True)
    ctx.py('p16_csv', '-m', 'droneshow', 'csv', 'out/show_p16_60.json',
           'scratch/p16csv', env=ENV)
    ctx.cmd('p16_csvhead', ['head', '-4', 'scratch/p16csv/drone_0.csv'])
    ctx.cmd('p16_csvwc', ['wc', '-l', 'scratch/p16csv/drone_0.csv'])


def run(ctx):
    plans(ctx)
    checks(ctx)
    scale(ctx)
    transitions(ctx)
    fly(ctx)
    export(ctx)
