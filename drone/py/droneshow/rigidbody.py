# -*- coding: utf-8 -*-
"""rigidbody — 적분기와 뉴턴-오일러 회전 방정식.

SPEC §4.3–4.4, 정리 T8·T21.

상태는 실수의 리스트다. 적분기는 무엇을 적분하는지 모른다 — 그래서
같은 rk4 로 x' = −x 도, 드론 한 대의 17개 수도 푼다.
"""
from . import quat as Q
from . import vec3 as V


def euler(f, x, dt):
    """오일러 한 걸음: x + dt·f(x). 전역 오차 O(dt)."""
    d = f(x)
    return [x[i] + dt * d[i] for i in range(len(x))]


def rk4(f, x, dt):
    """고전 룽게-쿠타 4단. 전역 오차 O(dt⁴) (T21)."""
    n = len(x)
    k1 = f(x)
    k2 = f([x[i] + 0.5 * dt * k1[i] for i in range(n)])
    k3 = f([x[i] + 0.5 * dt * k2[i] for i in range(n)])
    k4 = f([x[i] + dt * k3[i] for i in range(n)])
    return [x[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
            for i in range(n)]


def omega_dot(j, w, tau):
    """J ω̇ = τ − ω × (J ω). J 는 대각 성분 셋 [Jxx, Jyy, Jzz].

    ω × Jω 는 회전하는 몸체 좌표에서 미분했기 때문에 생기는 항이다
    (자이로 항, T8). 주축 둘레로만 돌면 ω 와 Jω 가 나란해 0 이 된다."""
    jw = [j[0] * w[0], j[1] * w[1], j[2] * w[2]]
    g = V.cross(w, jw)
    return [(tau[0] - g[0]) / j[0], (tau[1] - g[1]) / j[1],
            (tau[2] - g[2]) / j[2]]


def attitude_deriv(j, s, tau):
    """[q(4), ω(3)] 의 미분 — 회전만 다루는 시험·실험용."""
    return Q.qdot(s[:4], s[4:7]) + omega_dot(j, s[4:7], tau)


def rot_energy(j, w):
    """회전 운동에너지 ½ ωᵀ J ω."""
    return 0.5 * (j[0] * w[0] ** 2 + j[1] * w[1] ** 2
                  + j[2] * w[2] ** 2)


def ang_momentum(j, w):
    """몸체 좌표의 각운동량 J ω."""
    return [j[0] * w[0], j[1] * w[1], j[2] * w[2]]
