# -*- coding: utf-8 -*-
"""센서 보정 — 자이로 바이어스·가속도계 6면·자력계 구·전류 보상 (5부).

PX4 와 ArduPilot 의 보정 화면이 하는 일을 작게 다시 만든다. 모두
"알려진 참값과 어긋난 만큼" 을 최소제곱으로 푸는 일이다. 좌표는 이
덱의 몸체 좌표(x 앞, y 왼쪽, z 위)다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import linalg  # noqa: E402
from droneshow import quat as Q  # noqa: E402


def lstsq(rows, rhs):
    """식이 미지수보다 많은 A x ≈ y 를 정규방정식 AᵀA x = Aᵀy 로.

    n 개 식, m 개 미지수에 O(n·m² + m³). A 의 계수가 m 이 아니면
    AᵀA 가 특이해 linalg.solve 가 ValueError 를 낸다."""
    m = len(rows[0])
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(m)]
           for i in range(m)]
    aty = [sum(r[i] * y for r, y in zip(rows, rhs)) for i in range(m)]
    return linalg.solve(ata, aty)


def gyro_bias(samples):
    """가만히 둔 자이로의 평균 = 바이어스. 참 각속도가 0 이니까."""
    if not samples:
        raise ValueError('표본이 없다')
    n = len(samples)
    return [sum(s[i] for s in samples) / n for i in range(3)]


def accel_six(up, down, g):
    """축 i 를 위로(up[i]), 아래로(down[i]) 두고 잰 값 → 영점·배율.

    읽은 값 = 배율·참값 + 영점 이라 두면 위는 s·g + o, 아래는
    −s·g + o. 더하면 영점, 빼면 배율이 나온다(축마다 따로)."""
    off = [(up[i][i] + down[i][i]) / 2 for i in range(3)]
    scl = [(up[i][i] - down[i][i]) / (2 * g) for i in range(3)]
    return off, scl


def apply(v, offset, scale):
    """보정: (읽은 값 − 영점) / 배율."""
    return [(v[i] - offset[i]) / scale[i] for i in range(3)]


def fit_sphere(points):
    """자력계 점들이 놓인 구의 중심(하드 아이언)과 반지름.

    |m − c|² = r² 를 펼치면 2c·m + (r² − |c|²) = |m|² — c 와
    k = r² − |c|² 에 대해 1차식이라 최소제곱 한 번이면 된다."""
    if len(points) < 4:
        raise ValueError('점이 넷은 있어야 한다')
    rows = [[2 * p[0], 2 * p[1], 2 * p[2], 1.0] for p in points]
    rhs = [p[0] * p[0] + p[1] * p[1] + p[2] * p[2] for p in points]
    cx, cy, cz, k = lstsq(rows, rhs)
    return [cx, cy, cz], math.sqrt(k + cx * cx + cy * cy + cz * cz)


def fit_axes(points):
    """축마다 늘어난 타원체 — 중심과 축마다의 반지름(배율).

    a x² + b y² + c z² + d x + e y + f z = 1 이 여섯 미지수의
    1차식이다. 완전제곱으로 중심 −d/(2a) 와 반지름을 읽는다."""
    if len(points) < 6:
        raise ValueError('점이 여섯은 있어야 한다')
    rows = [[p[0] * p[0], p[1] * p[1], p[2] * p[2], p[0], p[1], p[2]]
            for p in points]
    a = lstsq(rows, [1.0] * len(points))
    c = [-a[3 + i] / (2 * a[i]) for i in range(3)]
    s = 1 + sum(a[i] * c[i] * c[i] for i in range(3))
    return c, [math.sqrt(s / a[i]) for i in range(3)]


def fit_line(xs, ys):
    """y ≈ k·x + b — CompassMot 처럼 전류 x 에 비례하는 간섭 k."""
    if max(xs) == min(xs):
        raise ValueError('x 가 한 값뿐이면 기울기를 알 수 없다')
    k, b = lstsq([[x, 1.0] for x in xs], ys)
    return k, b


def heading(m, roll, pitch):
    """몸체 자기장 m → 요(라디안). 롤·피치를 먼저 되돌린다.

    수평으로 되돌린 벡터가 (B_h cos ψ, −B_h sin ψ, ·) 꼴이므로
    ψ = atan2(−y, x). 기울기를 모르면 수직 성분이 섞여 틀린다."""
    q = Q.from_euler(roll, pitch, 0.0)
    lv = Q.rotate(q, m)
    return math.atan2(-lv[1], lv[0])


if __name__ == '__main__':
    g = 9.81
    ofs, scl = [0.12, -0.3, 0.05], [1.02, 0.97, 1.01]
    up, down = [], []
    for i in range(3):
        e = [0.0, 0.0, 0.0]
        e[i] = g
        up.append([scl[j] * e[j] + ofs[j] for j in range(3)])
        e[i] = -g
        down.append([scl[j] * e[j] + ofs[j] for j in range(3)])
    o, s = accel_six(up, down, g)
    print('가속도계 영점 ', ' '.join('%+.4f' % x for x in o))
    print('가속도계 배율 ', ' '.join('%.4f' % x for x in s))
    pts = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        for z in (-0.6, 0.0, 0.6):
            r = math.sqrt(1 - z * z)
            pts.append([0.3 + 0.5 * r * math.cos(a),
                        -0.2 + 0.5 * r * math.sin(a), 0.1 + 0.5 * z])
    c, r = fit_sphere(pts)
    print('자력계 중심   ', ' '.join('%+.4f' % x for x in c),
          ' 반지름 %.4f' % r)
