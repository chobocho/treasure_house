# -*- coding: utf-8 -*-
"""attitude — 원하는 자세 만들기와 쿼터니언 자세 제어.

SPEC §5.3–5.4, 정리 T12(미분 평탄성), T18(P 법칙), T19(요 가중치).
"""
import math

from . import quat as Q
from . import vec3 as V


def _axes(f, yaw):
    """추력 방향 f 와 요 → 몸체 축 셋 (x_B, y_B, z_B)."""
    z = V.normalize(f)
    xc = [math.cos(yaw), math.sin(yaw), 0.0]
    y = V.normalize(V.cross(z, xc))
    x = V.cross(y, z)
    return x, y, z


def desired_attitude(f, yaw):
    """z_B = f/|f|, 요는 x_B 를 수평면에 내린 방향 (SPEC §5.3)."""
    x, y, z = _axes(f, yaw)
    return Q.from_matrix(V.from_cols(x, y, z))


def flat_thrust(m, a, g):
    """평탄 출력의 가속도 a → 총추력 F = m·|a + g·e3|."""
    return m * V.norm([a[0], a[1], a[2] + g])


def flat_rates(a, j, yaw, yaw_rate, g):
    """가속도 a, 가가속도 j, 요와 그 변화율 → 몸체 각속도 [p, q, r].

    ż_B = ω × z_B = q·x_B − p·y_B 이고, ż_B 는 f/|f| 를 미분한
    h = (j − (z_B·j) z_B)/|f| 다. 그래서 p = −h·y_B, q = h·x_B.
    r 은 y_B ⊥ x_C 를 미분해 얻는다(x_C = 요 방향의 수평 단위벡터):
    r = (β p + ψ̇ (y_B·y_C)) / α, α = x_C·x_B, β = x_C·z_B (T12)."""
    f = [a[0], a[1], a[2] + g]
    x, y, z = _axes(f, yaw)
    h = V.scale(V.sub(j, V.scale(z, V.dot(z, j))), 1.0 / V.norm(f))
    p, q = -V.dot(h, y), V.dot(h, x)
    xc = [math.cos(yaw), math.sin(yaw), 0.0]
    yc = [-math.sin(yaw), math.cos(yaw), 0.0]
    alpha, beta = V.dot(xc, x), V.dot(xc, z)
    r = (beta * p + yaw_rate * V.dot(y, yc)) / alpha
    return [p, q, r]


def att_law(q, qd, k, yaw_w):
    """PX4 식 자세 P 법칙 → 원하는 몸체 각속도 (SPEC §5.4).

    1) 기울기만 맞추는 가장 짧은 회전 q_red 를 먼저 만들고, 2) 남은
    요 회전을 yaw_w 만큼만 섞는다. 3) 오차 q_e = q⁻¹ ⊗ q_d 의 벡터부의
    두 배에 이득을 곱한다. yaw_w = 1 이면 ω = 2k·sign(w)·q_e,xyz
    (T18)."""
    ez = Q.rotate(q, [0.0, 0.0, 1.0])
    ezd = Q.rotate(qd, [0.0, 0.0, 1.0])
    if V.dot(ez, ezd) < -1.0 + 1e-5:
        # 정반대 — 기울기만 따로 못 푼다
        qred = list(qd)
    else:
        qred = Q.mul(Q.from_two_vectors(ez, ezd), q)
    qmix = Q.canonical(Q.mul(Q.conj(qred), qd))
    w0 = max(-1.0, min(1.0, qmix[0]))
    z0 = max(-1.0, min(1.0, qmix[3]))
    qd2 = Q.mul(qred, [math.cos(yaw_w * math.acos(w0)), 0.0, 0.0,
                       math.sin(yaw_w * math.asin(z0))])
    qe = Q.canonical(Q.mul(Q.conj(q), qd2))
    return [2.0 * k[i] * qe[i + 1] for i in range(3)]
