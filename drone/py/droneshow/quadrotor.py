# -*- coding: utf-8 -*-
"""quadrotor — 쿼드로터 한 대의 6자유도 모델 (SPEC §4.3, 8부).

상태 17개: 위치 p(3) · 속도 v(3) · 자세 q(4) · 각속도 ω(3) · 모터 Ω(4).
    ṗ = v
    v̇ = (R(q)·(0,0,ΣTᵢ) − c·v + f_바람)/m − g·e3
    q̇ = ½ q ⊗ (0, ω)
    ω̇ = J⁻¹(τ − ω × Jω)
    Ω̇ᵢ = (Ω_명령,ᵢ − Ωᵢ)/τ_m
"""
from . import mixer
from . import params as P
from . import quat as Q
from . import rigidbody as RB


def pos(s):
    return s[0:3]


def vel(s):
    return s[3:6]


def att(s):
    return s[6:10]


def rates(s):
    return s[10:13]


def motors(s):
    return s[13:17]


def hover_state(p, where):
    """그 자리에 멈춰 떠 있는 상태 — 모터는 호버 회전수."""
    oh = P.derived(p)['omega_hover']
    return (list(map(float, where)) + [0.0] * 3 + [1.0, 0.0, 0.0, 0.0]
            + [0.0] * 3 + [oh] * 4)


def deriv(p, s, cmd, wind=(0.0, 0.0, 0.0)):
    """상태의 시간 미분. cmd 는 모터 회전수 명령 넷(이미 한계 안)."""
    m, g = p['m'], p['g']
    thrust = [p['kT'] * w * w for w in motors(s)]
    u = mixer.forward(p, thrust)
    q = att(s)
    f_body = Q.rotate(q, [0.0, 0.0, u[0]])
    v = vel(s)
    acc = [(f_body[i] - p['c_drag'] * v[i] + wind[i]) / m
           for i in range(3)]
    acc[2] -= g
    wdot = RB.omega_dot([p['Jxx'], p['Jyy'], p['Jzz']], rates(s), u[1:])
    mdot = [(cmd[i] - s[13 + i]) / p['tau_m'] for i in range(4)]
    return list(v) + acc + Q.qdot(q, rates(s)) + wdot + mdot


def step(p, s, cmd, dt, wind=(0.0, 0.0, 0.0)):
    """RK4 한 걸음 뒤 쿼터니언을 정규화한다(T7 — 표류를 지운다)."""
    n = RB.rk4(lambda x: deriv(p, x, cmd, wind), s, dt)
    n[6:10] = Q.normalize(n[6:10])
    return n


def accel_tilted(p, roll, pitch):
    """추력을 mg 로 두고 몸체만 기울였을 때의 정확한 가속도."""
    z = Q.rotate(Q.from_euler(roll, pitch, 0.0), [0.0, 0.0, 1.0])
    g = p['g']
    return [g * z[0], g * z[1], g * z[2] - g]


def accel_small_angle(p, roll, pitch):
    """호버 선형화 x'' ≈ gθ, y'' ≈ −gφ, z'' ≈ 0 (T11)."""
    g = p['g']
    return [g * pitch, -g * roll, 0.0]
