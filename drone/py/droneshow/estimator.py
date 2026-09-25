# -*- coding: utf-8 -*-
"""estimator — 센서 값에서 상태를 거꾸로 짐작한다 (SPEC §6, T23–T25).

자이로는 빠르고 매끄럽지만 바이어스 때문에 적분하면 표류한다.
가속도계·GNSS 는 표류하지 않지만 떨린다. 추정기는 둘을 섞는다 —
섞는 비율을 손으로 정하면 상보 필터, 분산으로 정하면 칼만 필터다.
"""
import math

from . import quat as Q
from . import vec3 as V


def complementary_1d(theta, gyro, acc_angle, alpha, dt):
    """한 축 상보 필터: α(θ + ω dt) + (1−α)·가속도계 각 (T23)."""
    return alpha * (theta + gyro * dt) + (1.0 - alpha) * acc_angle


def kalman_1d_gain(p, r):
    """예측 분산 P, 측정 분산 R → 이득 K = P/(P+R) (T24)."""
    if p + r == 0.0:
        return 0.0
    return p / (p + r)


def posterior_var(p, r, k):
    """이득 K 로 섞은 추정의 분산 (1−K)²P + K²R."""
    return (1.0 - k) ** 2 * p + k * k * r


class Kalman1D:
    """상태 [위치, 속도], 모델 x' = v, v' = 흰 잡음(세기 q).

    예측: x ← F x, P ← F P Fᵀ + Q. 갱신: y = z − x₀, S = P₀₀ + R,
    K = P[:,0]/S, x ← x + K y, P ← (I − K H) P. 2×2 라 손으로 풀었다."""

    def __init__(self, q, r, x0=(0.0, 0.0), p0=(1.0, 1.0)):
        self.q, self.r = q, r
        self.x = list(x0)
        self.p = [[p0[0], 0.0], [0.0, p0[1]]]

    def predict(self, dt, acc=0.0):
        x, v = self.x
        self.x = [x + v * dt + 0.5 * acc * dt * dt, v + acc * dt]
        p = self.p
        # F = [[1, dt], [0, 1]], Q = q·[[dt³/3, dt²/2], [dt²/2, dt]]
        a = p[0][0] + dt * (p[1][0] + p[0][1]) + dt * dt * p[1][1]
        b = p[0][1] + dt * p[1][1]
        c = p[1][0] + dt * p[1][1]
        q = self.q
        self.p = [[a + q * dt ** 3 / 3, b + q * dt * dt / 2],
                  [c + q * dt * dt / 2, p[1][1] + q * dt]]

    def update(self, z):
        """위치 측정 z 로 갱신. (혁신 y, 혁신 분산 S) 를 돌려준다."""
        p = self.p
        y = z - self.x[0]
        s = p[0][0] + self.r
        k0, k1 = p[0][0] / s, p[1][0] / s
        self.x = [self.x[0] + k0 * y, self.x[1] + k1 * y]
        self.p = [[(1 - k0) * p[0][0], (1 - k0) * p[0][1]],
                  [p[1][0] - k1 * p[0][0], p[1][1] - k1 * p[0][1]]]
        return y, s


class Complementary:
    """쿼터니언 상보 필터 — 자이로를 적분하고 기울기를 중력으로 당긴다.

    가속도계가 재는 비력의 방향 â 와, 지금 추정한 자세에서 본 '위'
    방향 R(q)ᵀe3 의 외적이 기울기 오차 축이다. 그 축으로 k_c 만큼
    각속도를 더해 적분한다(요는 중력으로 알 수 없어 그대로 둔다)."""

    def __init__(self, k_c=1.0, q0=(1.0, 0.0, 0.0, 0.0)):
        self.k_c = k_c
        self.q = list(q0)

    def update(self, gyro, acc, dt):
        up = Q.rotate(Q.conj(self.q), [0.0, 0.0, 1.0])
        e = V.cross(V.normalize(acc), up)
        w = [gyro[i] + self.k_c * e[i] for i in range(3)]
        n = V.norm(w)
        if n > 0:
            self.q = Q.normalize(Q.mul(self.q,
                                       Q.from_axis_angle(w, n * dt)))
        return self.q
