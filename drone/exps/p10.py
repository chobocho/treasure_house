# -*- coding: utf-8 -*-
"""10부 — 궤적·편대·할당. 최소 스냅, 사다리꼴, 헝가리안, 교차와 간격."""
import math

from droneshow import assign as AS
from droneshow import collide, formation as F, params, poly, profile, rng
from droneshow import show as SH


def betas(ctx):
    rows = []
    for u in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0):
        row = ['%.2f' % u]
        for k in ('T', 'J', 'S'):
            b = SH.beta(k, u, 0.25)
            z = [round(x, 4) + 0.0 for x in b]      # −0 을 0 으로
            row.append('%.4f / %.3f / %.2f' % (z[0], z[1], z[2]))
        rows.append(row)
    ctx.table('p10_beta', ['u', '사다리꼴 β/β′/β″', '최소 저크',
                           '최소 스냅'], rows)
    rows = []
    for k, name in (('T', '사다리꼴 (r = ¼)'), ('J', '최소 저크 (5차)'),
                    ('S', '최소 스냅 (7차)')):
        d1, d2 = SH.limits(k, 0.25)
        rows.append([name, '%.4f' % d1, '%.4f' % d2])
    ctx.table('p10_limits', ['모양', 'max β′', 'max |β″|'], rows,
              num=(1, 2))


def snapcost(ctx):
    """T27 — 섭동을 더하면 비용은 늘기만 한다."""
    big_t = 2.0
    c = [a / big_t ** k for k, a in enumerate(poly.rest_to_rest(4))]
    j0 = poly.snap_cost(c, big_t)
    g = rng.Rng(6)
    rows, worst = [], math.inf
    for trial in range(1, 201):
        h = poly.bump_poly(big_t, [g.normal() for _ in range(4)])
        eps = 0.1 * g.normal()
        j = poly.snap_cost(poly.add(c, [eps * x for x in h]), big_t)
        worst = min(worst, j - j0)
        if trial in (1, 2, 3, 50, 200):
            rows.append(['%d' % trial, '%.6f' % j,
                         '%.3e' % (j - j0)])
    rows.append(['200번 중 최소 증가', '', '%.3e' % worst])
    ctx.table('p10_snapcost', ['섭동', 'J(x + εh)', 'J − J(x)'], rows,
              num=(1, 2))
    ctx.text('p10_snapcost_j0', '# 최소 스냅 x(t) = β(t/2), T = 2 s\n'
             'J(x) = %.6f\n' % j0)


def multiseg(ctx):
    wp, times = [0.0, 2.0, 1.0, 4.0], [1.5, 1.0, 2.0]
    segs = poly.min_snap(wp, times)
    rows = []
    for k in range(len(segs) - 1):
        jumps = []
        for d in range(0, 8):
            a = poly.val(poly.deriv(segs[k], d), times[k])
            b = poly.val(poly.deriv(segs[k + 1], d), 0.0)
            jumps.append('%.1e' % abs(a - b))
        rows.append(['%d–%d' % (k + 1, k + 2)] + jumps)
    ctx.table('p10_multiseg', ['경유점', '위치', '1계', '2계', '3계', '4계',
                               '5계', '6계', '7계'], rows,
              num=(1, 2, 3, 4, 5, 6, 7, 8))


def profiles(ctx):
    rows = []
    for d in (0.5, 4.5, 12.0, 30.0):
        pr = profile.trapezoid(d, 3.0, 2.0)
        ts = profile.feasible_time(d, 3.0, 2.0, poly.rest_to_rest(4))
        tj = profile.feasible_time(d, 3.0, 2.0, poly.rest_to_rest(3))
        rows.append(['%g' % d, '%.3f' % pr['T'], '%.3f' % pr['v_peak'],
                     '삼각' if pr['triangular'] else '사다리꼴',
                     '%.3f' % tj, '%.3f' % ts])
    ctx.table('p10_profile', ['거리[m]', '사다리꼴 T[s]', '최고 속도',
                              '모양', '최소 저크 T', '최소 스냅 T'],
              rows, num=(0, 1, 2, 4, 5))


def hungarian(ctx):
    g = rng.Rng(12)
    rows = []
    for n in (5, 10, 20, 40, 80):
        a = [[g.uniform() * 30, 0.0, g.uniform() * 30] for _ in range(n)]
        b = [[g.uniform() * 30, 0.0, g.uniform() * 30] for _ in range(n)]
        perm, tot, ops = AS.hungarian(AS.cost_matrix(a, b))
        rows.append(['%d' % n, '{:,}'.format(ops), '%.3f' % (ops / n ** 3),
                     '%.2f' % tot])
    ctx.table('p10_hungarian', ['n', '완화 횟수', '÷ n³', '제곱 거리 합'],
              rows, num=(0, 1, 2, 3))
    g = rng.Rng(9)
    same = 0
    for n in range(1, 8):
        for _ in range(10):
            c = [[g.uniform() for _ in range(n)] for _ in range(n)]
            if abs(AS.hungarian(c)[1] - AS.brute(c)[1]) < 1e-12:
                same += 1
    ctx.text('p10_brute', '# n = 1..7, 무작위 비용 행렬 70개\n'
             '헝가리안 = 모든 순열: %d / 70\n' % same)


def crossing(ctx):
    """T30·T31·L23·L24 — 그냥 거리와 제곱 거리의 할당을 비교."""
    g = rng.Rng(33)
    stats = {True: [0, 1e9], False: [0, 1e9]}
    for _ in range(300):
        a = [[g.uniform() * 12, 0.0, g.uniform() * 12] for _ in range(6)]
        b = [[g.uniform() * 12, 0.0, g.uniform() * 12] for _ in range(6)]
        delta = min(collide.min_distance(a)[0], collide.min_distance(b)[0])
        for sq in (True, False):
            perm, _t, _o = AS.hungarian(AS.cost_matrix(a, b, sq))
            stats[sq][0] += collide.crossings(a, b, perm)
            d = collide.check_transition(a, b, perm, lambda u: u, 100)[0]
            stats[sq][1] = min(stats[sq][1], d / delta)
    rows = [['제곱 거리 합', '%d' % stats[True][0],
             '%.4f' % stats[True][1]],
            ['그냥 거리 합', '%d' % stats[False][0],
             '%.4f' % stats[False][1]]]
    ctx.table('p10_crossing', ['최소로 한 것', '엇갈린 경로 쌍(300판)',
                               '이동 중 최소 거리 ÷ δ'], rows, num=(1, 2))


def counterexample(ctx):
    c = 0.9
    u, w = [1.0, 0.0], [c, math.sqrt(1 - c * c)]
    a1, b1 = [-u[0], -u[1]], [10 * u[0], 10 * u[1]]
    a2, b2 = [-10 * w[0], -10 * w[1]], [w[0], w[1]]
    d2 = lambda p, q: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    lines = ['# 교차점 X = 원점, u·w = 0.9',
             'a1 = X − u,  b1 = X + 10u,  a2 = X − 10w,  b2 = X + w',
             '제곱 거리 합  그대로 %.4f  맞바꿈 %.4f'
             % (d2(a1, b1) + d2(a2, b2), d2(a1, b2) + d2(a2, b1)),
             '그냥 거리 합  그대로 %.4f  맞바꿈 %.4f'
             % (math.sqrt(d2(a1, b1)) + math.sqrt(d2(a2, b2)),
                math.sqrt(d2(a1, b2)) + math.sqrt(d2(a2, b1)))]
    ctx.text('p10_counter', '\n'.join(lines))


def spacing(ctx):
    rows = []
    for n in (50, 100, 200, 400, 800):
        m = F.fibonacci_unit_min(n)
        rows.append(['%d' % n, '%.5f' % m, '%.4f' % (m * math.sqrt(n)),
                     '%.3f' % (1.5 / m)])
    ctx.table('p10_fibonacci', ['n', '단위 구의 최소 간격 m₁', 'm₁·√n',
                                'dmin 1.5 m 의 반지름'], rows,
              num=(0, 1, 2, 3))
    rows = []
    for r in (2.0, 1.5, 1.0):
        pts = F.poisson_disk(lambda x, z: True, 20.0, 10.0, r, rng.Rng(4),
                             tries=3000)
        d = collide.min_distance([[x, 0.0, z] for x, z in pts])[0]
        rows.append(['%g' % r, '%d' % len(pts), '%.4f' % d])
    ctx.table('p10_poisson', ['r[m]', '받아들인 점', '최소 거리[m]'], rows,
              num=(0, 1, 2))


def shapes(ctx):
    p = params.load()
    d = p['dmin']
    for name, pts, rgb in (
            ('heart', F.heart(60, d, 20.0), (255, 40, 90)),
            ('sphere', F.sphere(100, d, 20.0), (80, 200, 255)),
            ('globe', F.globe(120, d, z0=20.0), (120, 220, 255)),
            ('text', F.text('DRONE', d, 20.0), (255, 220, 120)),
            ('rings', F.rings(60, d, 3, 20.0), (180, 120, 255))):
        ctx.show('p10_' + name, SH.plan([{'name': name, 'points': pts,
                                          'hold': 1.0, 'rgb': rgb}], p))


def run(ctx):
    ctx.py('p10_exercises', 'ex/exercises10.py')
    betas(ctx)
    snapcost(ctx)
    multiseg(ctx)
    profiles(ctx)
    hungarian(ctx)
    crossing(ctx)
    counterexample(ctx)
    spacing(ctx)
    shapes(ctx)
