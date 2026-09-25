# -*- coding: utf-8 -*-
"""의사거리 넷 이상으로 위치와 시계 오차를 푼다 — 뉴턴 반복 (T26, 5부).

미지수는 넷(x, y, z, b). b 는 수신기 시계 오차에 빛의 속도를 곱한
거리다. ρᵢ = |sᵢ − r| + b 를 한 점 둘레에서 1차로 펴서(테일러) 4×4
연립방정식을 풀고, 그만큼 옮기기를 되풀이한다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import linalg  # noqa: E402

R = 26_560_000.0                      # 궤도 반지름 [m] — 합성 예제용


def sats():
    """하늘에 고르게 흩은 가상 위성 여섯."""
    out = []
    for k, (el, az) in enumerate([(60, 0), (35, 70), (30, 150),
                                  (45, 220), (25, 290), (70, 180)]):
        e, a = math.radians(el), math.radians(az)
        out.append([R * math.cos(e) * math.cos(a),
                    R * math.cos(e) * math.sin(a), R * math.sin(e)])
    return out


def solve(sv, rho, guess=(0.0, 0.0, 0.0, 0.0), steps=8):
    """뉴턴 반복. 매 걸음의 (x, y, z, b) 와 잔차 크기를 돌려준다."""
    x = list(guess)
    hist = []
    for _ in range(steps):
        rows, rhs = [], []
        for s, r in zip(sv, rho):
            d = math.dist(s, x[:3])
            rows.append([(x[i] - s[i]) / d for i in range(3)] + [1.0])
            rhs.append(r - (d + x[3]))
        # 식이 넷보다 많으면 정규방정식 AᵀA dx = Aᵀr
        ata = [[sum(a[i] * a[j] for a in rows) for j in range(4)]
               for i in range(4)]
        atr = [sum(a[i] * b for a, b in zip(rows, rhs))
               for i in range(4)]
        dx = linalg.solve(ata, atr)
        x = [x[i] + dx[i] for i in range(4)]
        hist.append((list(x), math.sqrt(sum(b * b for b in rhs))))
    return x, hist


if __name__ == '__main__':
    truth, bias = [1200.0, -800.0, 300.0], 45_000.0
    sv = sats()
    rho = [math.dist(s, truth) + bias for s in sv]
    x, hist = solve(sv, rho)
    print('참 위치 (1200, -800, 300) m, 시계 오차 45000 m')
    for k, (xk, res) in enumerate(hist, 1):
        print('%d회  x=%12.4f y=%12.4f z=%12.4f b=%12.4f  잔차 %.3e'
              % (k, xk[0], xk[1], xk[2], xk[3], res))
