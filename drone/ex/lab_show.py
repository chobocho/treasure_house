# -*- coding: utf-8 -*-
"""16부 실습 — 쇼 한 편을 12·60·300 대로 짠다.

    python3 ex/lab_show.py 60 -o scratch/lab60.json
    python3 ex/lab_show.py 60 --tight -o scratch/bad60.json
    python3 ex/lab_show.py 300 --layers 1 -o scratch/flat300.json

대수마다 이야기가 다르다. 12 대로는 글자를 못 쓴다(숫자 3 한 자에
점 14 개) — 원과 하트로 끝낸다. 60 대는 숫자까지, 300 대라야
"TREASURE"(점 131 개)를 쓴다. 점이 모자란 장면에서는 남는 드론이
그림 뒤에서 불을 끄고 기다린다(13부 '불 끄고 이동').

모양 간격은 √2·dmin 이다. 제곱 거리 할당으로 모두 같은 β 를 따라
직선으로 옮기면, 장면 간격이 δ 일 때 전환 중 거리는 δ/√2 아래로
내려가지 않는다(T31) — 그래서 δ = √2·dmin 이면 전환 내내 dmin 이다.
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import formation as F  # noqa: E402
from droneshow import params  # noqa: E402
from droneshow import show as SH  # noqa: E402

VERSIONS = (12, 60, 300)
Z0 = 20.0                         # 그림의 아래 끝 높이[m]
WHITE, DARK = (255, 255, 255), (0, 0, 0)
RED, BLUE, GOLD = (255, 40, 90), (80, 200, 255), (255, 220, 120)


def spacing(p, tight=False):
    """모양 간격. tight 는 일부러 dmin 그대로 — T31 의 바닥을 보려고."""
    return p['dmin'] if tight else p['dmin'] * math.sqrt(2)


def park(m, d):
    """쉬는 드론 m 대의 자리 — 그림 뒤 y = 2d 의 세로 격자.

    그림(글자·숫자)은 y = 0 평면에 있으므로 2d 뒤면 켜진 점과도
    d 이상 떨어진다."""
    return [[x, 2 * d, z] for x, _y, z in F.grid(m, d, z0=Z0)]


def with_dark(name, lit_pts, n, d, rgb, hold):
    """켜진 점 + 불 끈 대기 점으로 n 을 채운 장면."""
    m = n - len(lit_pts)
    if m < 0:
        raise ValueError('%s: 점 %d개에 드론 %d대'
                         % (name, len(lit_pts), n))
    pts = lit_pts + (park(m, d) if m else [])
    return {'name': name, 'points': pts, 'hold': hold,
            'rgb': [rgb] * len(lit_pts) + [DARK] * m}


def countdown(n, d):
    return [with_dark(k, F.digit(int(k), d, Z0), n, d, WHITE, 1.0)
            for k in ('3', '2', '1')]


def scenes(n, d, layers=None):
    """대수별 장면 목록. 모든 장면의 점 수는 n — 드론은 사라지지
    않는다.

    layers 는 하트의 겹 수. 윤곽선 모양은 둘레가 대수에 비례하므로
    300 대를 한 겹에 실으면 꼭대기가 120 m 를 넘는다 — 300 대 판의
    기본은 3겹이다."""
    if n not in VERSIONS:
        raise ValueError('준비된 판은 12·60·300 대뿐이다: %r' % (n,))
    if layers is None:
        layers = 3 if n == 300 else 1
    ground = {'name': 'grid', 'points': F.grid(n, d, plane='xy'),
              'hold': 2.0, 'rgb': WHITE}
    heart = {'name': 'heart', 'points': F.heart(n, d, Z0, layers),
             'hold': 3.0, 'rgb': RED}
    if n == 12:
        return [ground,
                {'name': 'circle', 'points': F.circle(n, d, Z0),
                 'hold': 3.0, 'rgb': BLUE},
                heart,
                {'name': 'land', 'points': F.grid(n, d, plane='xy'),
                 'hold': 1.0, 'rgb': WHITE}]
    out = [ground]
    if n == 300:
        word = F.text('TREASURE', d, Z0)
        out.append(with_dark('TREASURE', word, n, d, GOLD, 4.0))
    out.append(heart)
    out.append({'name': 'globe', 'points': F.globe(n, d, z0=Z0),
                'hold': 3.0, 'rgb': BLUE})
    out += countdown(n, d)
    out.append(dict(heart, name='heart2'))
    return out


def build(n, p, tight=False, layers=None):
    return SH.plan(scenes(n, spacing(p, tight), layers), p)


def main(argv=None):
    ap = argparse.ArgumentParser(prog='lab_show')
    ap.add_argument('n', type=int)
    ap.add_argument('-o', required=True)
    ap.add_argument('--tight', action='store_true',
                    help='간격을 √2·dmin 대신 dmin 으로(일부러 틀리게)')
    ap.add_argument('--layers', type=int, default=None,
                    help='하트의 겹 수(기본: 300 대만 3)')
    a = ap.parse_args(argv)
    s = build(a.n, params.load(), a.tight, a.layers)
    with open(a.o, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SH.dumps(s))
    print('%s — 드론 %d대 · 장면 %d개 · %.2f초'
          % (a.o, len(s['drones']), len(s['scenes']), s['duration']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
