# -*- coding: utf-8 -*-
"""tricks — 13부의 드론쇼 트릭을 함수로 (SPEC §9.3).

트릭마다 '무엇을 바꾸고 무엇을 그대로 두는가' 가 분명해야 한다.
빛만 바꾸는 트릭은 lights 트랙만 고치고 움직임(keyframes)은 그대로
둔다 — 그래야 충돌 검사를 다시 할 필요가 없다.
"""
import copy
import math

from . import assign as AS
from . import show as SH


def _track(show, d):
    """드론 한 대의 빛 트랙 — 없으면 키프레임의 색으로 만든다."""
    return d.get('lights') or [[k[0]] + list(k[4:7])
                               for k in d['keyframes']]


def dark_move(show, fade=0.3):
    """움직이는 동안 불을 끈다 — 관객에게는 모양이 '바뀌어' 보인다.

    멈춤이 끝나면 fade 초 동안 꺼지고, 다음 멈춤 fade 초 전부터 켜진다.
    전환이 2·fade 보다 짧으면 그 전환은 건드리지 않는다."""
    s = copy.deepcopy(show)
    sc = s['scenes']
    for d in s['drones']:
        light = []
        for k, cur in enumerate(sc):
            c = SH.colour(show, d, cur['t0'])
            light += [[cur['t0']] + c, [cur['t1']] + c]
            if k + 1 < len(sc):
                a, b = cur['t1'], sc[k + 1]['t0']
                if b - a > 2 * fade:
                    light += [[SH.r9(a + fade), 0, 0, 0],
                              [SH.r9(b - fade), 0, 0, 0]]
        d['lights'] = light
    return s


def under_count(pts, r, h):
    """(위, 아래) 쌍의 수 — 수평 거리 < r, 0 < 높이 차 < h.

    아래 드론은 위 드론이 내리미는 공기(다운워시) 속에 있다."""
    n = 0
    for i, a in enumerate(pts):
        for j, b in enumerate(pts):
            if i != j and math.hypot(a[0] - b[0], a[1] - b[1]) < r \
                    and 0 < a[2] - b[2] < h:
                n += 1
    return n


def takeoff(show, ground, p, delay=0.0):
    """땅의 격자에서 첫 장면으로 이륙 — delay 초씩 엇갈려(스태거링).

    목표 높이가 높은 줄부터 먼저 뜬다. 늦게 뜬 드론이 먼저 뜬 드론의
    아래를 지나갈 일이 줄어든다(다운워시). delay = 0 이면 모두 함께
    — 그때는 동기 직선 이동이라 T31 의 보장이 그대로 선다."""
    s = copy.deepcopy(show)
    first = [d['keyframes'][0][1:4] for d in s['drones']]
    perm, _t, _o = AS.hungarian(AS.cost_matrix(first, ground, True))
    dmax = max(math.dist(first[i], ground[perm[i]])
               for i in range(len(first)))
    d1, d2 = SH.limits('T', s['profile']['ramp'])
    up = max(dmax * d1 / p['vmax'], math.sqrt(dmax * d2 / p['amax']))
    up = math.ceil(up * s['fps'] - 1e-9) / s['fps']
    heights = sorted({round(q[2], 6) for q in first}, reverse=True)
    rank = {h: k for k, h in enumerate(heights)}
    t_all = SH.r9((len(heights) - 1) * delay + up)
    for i, d in enumerate(s['drones']):
        g = ground[perm[i]]
        start = SH.r9(rank[round(first[i][2], 6)] * delay)
        c = list(d['keyframes'][0][4:7])
        head = [[0.0] + g + [0, 0, 0, 'L'],
                [start] + g + [0, 0, 0, 'T'],
                [SH.r9(start + up)] + first[i] + c + ['L']]
        rest = [[SH.r9(k[0] + t_all)] + k[1:] for k in d['keyframes']]
        d['keyframes'] = head + rest
        if 'lights' in d:
            d['lights'] = [[SH.r9(x[0] + t_all)] + x[1:]
                           for x in d['lights']]
    for sc in s['scenes']:
        sc['t0'], sc['t1'] = SH.r9(sc['t0'] + t_all), SH.r9(
            sc['t1'] + t_all)
    s['duration'] = SH.r9(s['duration'] + t_all)
    s['takeoff'] = {'t0': 0.0, 't1': t_all, 'delay': delay}
    return s


def layered_depth(pts, depth):
    """체스판 무늬로 한 칸 걸러 뒤로 depth 만큼 — 앞에서 보면 그대로.

    관객은 깊이를 거의 못 느낀다(T33). 앞에서 본 간격은 좁게 두고
    3차원 간격만 넓혀 같은 넓이에 더 많은 점을 세운다."""
    from . import collide
    s = collide.min_distance(pts)[0]
    x0 = min(q[0] for q in pts)
    z0 = min(q[2] for q in pts)
    out = []
    for q in pts:
        par = (SH.rnd((q[0] - x0) / s) + SH.rnd((q[2] - z0) / s)) % 2
        out.append([q[0], q[1] + depth * par, q[2]])
    return out


def centroid(pts):
    n = len(pts)
    return [sum(q[k] for q in pts) / n for k in range(3)]


def rotate_volume(pts, angle, steps):
    """중심을 지나는 수직축 둘레로 angle 만큼, steps 등분한 자리들."""
    c = centroid(pts)
    out = []
    for k in range(steps + 1):
        a = angle * k / steps
        ca, sa = math.cos(a), math.sin(a)
        out.append([[c[0] + ca * (q[0] - c[0]) - sa * (q[1] - c[1]),
                     c[1] + sa * (q[0] - c[0]) + ca * (q[1] - c[1]),
                     q[2]] for q in pts])
    return out


def wave(pts, amp, lam, period, t):
    """z 에 진폭 amp 의 파동 — 위상이 x 를 따라 λ 마다 한 바퀴."""
    return [[q[0], q[1], q[2] + amp * math.sin(
        2 * math.pi * (q[0] / lam - t / period))] for q in pts]


def led_only_motion(show, speed=2.0, width=2.0, dim=0.25, dt=0.2):
    """드론은 멈춰 있고 밝은 띠만 x 쪽으로 흐른다 — 빛만의 움직임."""
    s = copy.deepcopy(show)
    xs = [k[1] for d in s['drones'] for k in d['keyframes']]
    x0 = min(xs)
    for d in s['drones']:
        light = []
        for sc in s['scenes']:
            n = max(1, round((sc['t1'] - sc['t0']) / dt))
            for k in range(n + 1):
                t = sc['t0'] + (sc['t1'] - sc['t0']) * k / n
                x = SH.position(show, d, t)[0]
                band = x0 + speed * (t - sc['t0'])
                b = 1.0 if abs(x - band) < width / 2 else dim
                c = SH.colour(show, d, t)
                light.append([SH.r9(t)] + [SH.rnd(b * v) for v in c])
        d['lights'] = light
    return s


def dither(values, levels):
    """값 [0,1] 을 levels 단계로 — 오차를 다음 값에 넘긴다(오차 확산).

    반올림만 하면 부드러운 그러데이션이 계단 몇 개로 뭉친다. 버린
    오차를 옆 드론에 넘기면 몇 대씩 묶어 본 평균이 원래 값에 붙는다."""
    step = 1.0 / (levels - 1)
    out, err = [], 0.0
    for v in values:
        want = v + err
        q = min(1.0, max(0.0, math.floor(want / step + 0.5) * step))
        out.append(q)
        err = want - q
    return out
