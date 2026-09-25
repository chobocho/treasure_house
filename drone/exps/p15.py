# -*- coding: utf-8 -*-
"""15부 — 자바스크립트 판: node 시험, 재생기용 쇼, 데모 요약의 파이썬 판.

데모(js/demo.js)가 화면에 쓰는 요약 한 줄 한 줄을 파이썬 판으로 같은
입력에서 계산해 out/p15_demo_*.txt 에 남긴다. check_deck.js 는 DOM
스텁에서 데모를 돌려 그 글이 이 캡처의 줄과 같은지 본다 — 두 판이
같은 수를 낸다는 것을 덱 조립 때마다 다시 확인한다.
"""
import math

from droneshow import assign as AS
from droneshow import attitude as A
from droneshow import collide, formation as F, params, profile, sim
from droneshow import quat as Q
from droneshow import rigidbody as RB
from droneshow import show as SH


def player(ctx):
    """재생기용 쇼 — 65 대: 격자 → 하트 → 지구본 → SHOW → 3·2·1 → 하트."""
    p = params.load()
    d = p['dmin'] * math.sqrt(2)          # 전환 중에도 dmin 을 지키게(T31)
    n = 65
    park = [[x - 12 * d / 2 + 0.0, 12.0, 5.0 + z * d]
            for z in range(5) for x in [k * d for k in range(13)]][:n]

    scenes = [{'name': 'grid', 'points': F.grid(n, d, z0=20.0), 'hold': 2.0,
               'rgb': (255, 255, 255)},
              {'name': 'heart', 'points': F.heart(n, d, 20.0), 'hold': 3.0,
               'rgb': (255, 40, 90)},
              {'name': 'globe', 'points': F.globe(n, d, z0=20.0),
               'hold': 3.0, 'rgb': (80, 200, 255)},
              {'name': 'SHOW', 'points': F.text('SHOW', d, 20.0),
               'hold': 3.0, 'rgb': (255, 220, 120)}]
    for k in ('3', '2', '1'):
        dig = F.digit(int(k), d, 20.0)
        pts = dig + park[:n - len(dig)]
        rgb = [(255, 255, 255)] * len(dig) + [(0, 0, 0)] * (n - len(dig))
        scenes.append({'name': k, 'points': pts, 'hold': 1.0, 'rgb': rgb})
    scenes.append({'name': 'heart2', 'points': F.heart(n, d, 20.0),
                   'hold': 3.0, 'rgb': (255, 40, 90)})
    s = SH.plan(scenes, p)
    ctx.show('p15_player', s)
    return s


def demos(ctx, show):
    p = params.load()
    ctx.text('p15_demo_showplayer', '드론 %d대 · %.2f / %.2f초 · %s'
             % (len(show['drones']), 0.0, show['duration'],
                show['scenes'][0]['name']))
    # 실시간 물리 — 기본값
    rows = sim.fly(p, lambda t: {'p': [1, 0, 5]}, 4.0, start=[0, 0, 5])

    def tilt(s):
        z = Q.rotate(s[6:10], [0, 0, 1])
        return math.degrees(math.acos(max(-1.0, min(1.0, z[2]))))
    xs = [r['s'][0] for r in rows]
    ctx.text('p15_demo_physics', '최대 기울기 %.1f° · x 최댓값 %.3f m · '
             '4초 뒤 x %.3f m' % (max(tilt(r['s']) for r in rows), max(xs),
                                 xs[-1]))
    # 자세 놀이터 — 롤 30°, 피치 20°, 요 60°, k = 3
    qd = Q.from_euler(math.radians(30), math.radians(20), math.radians(60))
    axis, th0 = Q.to_axis_angle(qd)
    q, k, ths = [1.0, 0.0, 0.0, 0.0], 3.0, [th0]
    f = lambda x: Q.qdot(x, A.att_law(x, qd, [k, k, k], 1.0))
    for n in range(2000):
        q = Q.normalize(RB.rk4(f, q, 0.001))
        if (n + 1) % 20 == 0:
            ths.append(Q.to_axis_angle(Q.mul(Q.conj(q), qd))[1])
    closed = 4 * math.atan(math.tan(th0 / 4) * math.exp(-k * 1.0))
    qe = Q.canonical(qd)
    ctx.text('p15_demo_attitude',
             'q_e = (%s)\n축 (%s) · 각 %.2f°\n1초 뒤 %.4f° · 닫힌 해 %.4f°'
             % (', '.join('%.4f' % v for v in qe),
                ', '.join('%.3f' % v for v in axis), math.degrees(th0),
                math.degrees(ths[50]), math.degrees(closed)))
    # 편대 실험실 — HI, d = 1.5, 두 비용
    lines = []
    for sq in (True, False):
        d = 1.5
        b = F.text('HI', d * math.sqrt(2), 10.0)
        a = F.grid(len(b), d * math.sqrt(2), 'xz', 10.0)
        perm, total, _o = AS.hungarian(AS.cost_matrix(a, b, sq))
        dmin = collide.check_transition(a, b, perm, lambda u: u, 100)[0]
        lines.append('%s 합 최소 · %d대 · 합 %.3f\n엇갈린 쌍 %d · 이동 중 최소 간격 '
                     '%.3f m (한계 δ/√2 = %.3f m)'
                     % ('제곱 거리' if sq else '그냥 거리', len(b), total,
                        collide.crossings(a, b, perm), dmin, d))
    ctx.text('p15_demo_formation', '\n'.join(lines))
    # 궤적 실험실 — 12 m, 3 m/s, 2 m/s²
    pr = profile.trapezoid(12.0, 3.0, 2.0)
    s1, s2 = SH.limits('S', 0.25)
    ts = max(12.0 * s1 / 3.0, math.sqrt(12.0 * s2 / 2.0))
    ctx.text('p15_demo_trajectory', '사다리꼴 T %.3f초 (%s) · 최소 스냅 T '
             '%.3f초 · 비 %.3f' % (pr['T'], '삼각' if pr['triangular']
                                  else '사다리꼴', ts, ts / pr['T']))
    # PID 튜너 — kp 4, kd 0.8
    kp, kd = 4.0, 0.8
    f = lambda x: [x[1], kp * (1 - x[0]) - kd * x[1]]
    s, top = [0.0, 0.0], 0.0
    for _ in range(20000):
        s = RB.rk4(f, s, 1e-3)
        top = max(top, s[0])
    wn, z = math.sqrt(kp), kd / (2 * math.sqrt(kp))
    disc = kd * kd - 4 * kp
    ctx.text('p15_demo_pidtune', 'ζ = %.3f · ωn = %.3f\n초과량 측정 %.5f · 공식 '
             '%.5f\n극 %.3f ± %.3fi'
             % (z, wn, max(0.0, top - 1),
                math.exp(-math.pi * z / math.sqrt(1 - z * z)), -kd / 2,
                math.sqrt(-disc) / 2))


def run(ctx):
    ctx.cmd('p15_node_test', ['node', '--test', 'js/test/parity.test.js'],
            strip_timing=True)
    s = player(ctx)
    demos(ctx, s)
