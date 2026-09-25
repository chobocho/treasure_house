# -*- coding: utf-8 -*-
"""16부 실습 — 쇼 파일을 날리기 전에 규칙 다섯 가지를 잰다.

    python3 ex/lab_check.py out/show_p16_60.json [--zmax 120]

최소 간격 · 최고 속도 · 최고 가속도 · 고도 · 비행시간. 하나라도
어기면 종료 코드 1 이다. 손으로 고친 쇼 파일이나 다른 도구가 만든
쇼를 받았을 때 쓰는 문지기다 — 우리 계획기(show.plan)는 앞의 셋을
지키도록 짜지만, 파일은 믿지 말고 잰다.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import motor, params  # noqa: E402
from droneshow import show as SH  # noqa: E402
from droneshow import vec3 as V  # noqa: E402

EPS = 1e-9


def peak_rates(show):
    """(최고 속도, 최고 가속도) — 표본을 뜨지 않고 구간마다 정확히.

    한 구간은 직선 위를 β(u) 로 가므로 속도 = 거리·β'/구간 시간,
    가속도 = 거리·β''/구간 시간² 이고, β' 와 |β''| 의 최댓값은
    모양마다 정해져 있다(SH.limits). 키프레임 수 K 에 대해 O(K)."""
    ramp = show['profile']['ramp']
    vmax = amax = 0.0
    for d in show['drones']:
        kf = d['keyframes']
        for a, b in zip(kf, kf[1:]):
            span = b[0] - a[0]
            dist = V.dist(a[1:4], b[1:4])
            if span <= 0.0 or dist == 0.0:
                continue
            d1, d2 = SH.limits(SH._kind(show, a), ramp)
            vmax = max(vmax, dist * d1 / span)
            amax = max(amax, dist * d2 / span ** 2)
    return vmax, amax


def check(show, p, zmax=120.0):
    """[(이름, 통과?, 잰 값, 한계)] — 글은 출력용으로 다듬어 둔다."""
    dmin = SH.min_distance(show)[0]
    v, a = peak_rates(show)
    # 구간은 직선이므로 높이의 극값은 키프레임에 있다
    zs = [k[3] for d in show['drones'] for k in d['keyframes']]
    ft = motor.flight_time(p)
    return [
        ('최소 간격', dmin >= p['dmin'] - EPS, '%.3f m' % dmin,
         '≥ %.3f m' % p['dmin']),
        ('최고 속도', v <= p['vmax'] + EPS, '%.3f m/s' % v,
         '≤ %.3f m/s' % p['vmax']),
        ('최고 가속도', a <= p['amax'] + EPS, '%.3f m/s²' % a,
         '≤ %.3f m/s²' % p['amax']),
        ('고도', min(zs) >= -EPS and max(zs) <= zmax + EPS,
         '%.1f–%.1f m' % (min(zs), max(zs)), '0–%.1f m' % zmax),
        ('비행시간', show['duration'] <= ft + EPS,
         '%.1f s' % show['duration'], '≤ %.1f s' % ft),
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(prog='lab_check')
    ap.add_argument('show')
    ap.add_argument('--zmax', type=float, default=120.0)
    a = ap.parse_args(argv)
    with open(a.show, encoding='utf-8') as f:
        s = SH.loads(f.read())
    rows = check(s, params.load(), a.zmax)
    print('드론 %d대 · %.2f초' % (len(s['drones']), s['duration']))
    for name, ok, val, lim in rows:
        print('  %s  %-6s %14s  (%s)' % ('통과' if ok else '실패', name,
                                        val, lim))
    bad = sum(1 for r in rows if not r[1])
    print('실패 %d건' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
