# -*- coding: utf-8 -*-
"""motor — 로터 한 개: 모멘텀 이론, 비행시간, 1차 지연 (T1, T2, T13).

로터를 '공기를 아래로 미는 원판' 으로 본다. 원판이 공기에 준 운동량이
곧 추력이고, 공기에 준 운동에너지가 곧 드는 일률이다(T1).
"""
import math

from . import params as P


def induced_velocity(t, rho, area):
    """원판을 지나는 공기의 속도 v = √(T / (2ρA))."""
    return math.sqrt(t / (2.0 * rho * area))


def ideal_power(t, rho, area):
    """이상적인 호버 일률 P = T^(3/2) / √(2ρA) = T·v (T1)."""
    return t ** 1.5 / math.sqrt(2.0 * rho * area)


def hover_power(p):
    """네 로터의 전기 일률 — 이상값 ÷ (성능 지수 × 전기 효율)."""
    d = P.derived(p)
    one = ideal_power(d['T_hover'], p['rho'], d['area'])
    return 4.0 * one / (p['fm'] * p['eta_e'])


def flight_time(p):
    """호버 비행시간[s] = 쓸 수 있는 에너지 / (호버 + LED 일률) (T2)."""
    energy = p['batt_Ah'] * 3600.0 * p['batt_V'] * p['batt_use']
    return energy / (hover_power(p) + p['led_W'])


def lag_exact(w, w_cmd, tau, dt):
    """τ Ω' = Ω_cmd − Ω 를 dt 동안 정확히 푼 값 (명령이 일정할 때).

    해는 Ω(t) = Ω_cmd + (Ω₀ − Ω_cmd)·e^(−t/τ) — 7부의 1차 선형
    미분방정식이다. 시뮬레이터 본체는 이 식 대신 RK4 로 함께
    적분한다."""
    return w_cmd + (w - w_cmd) * math.exp(-dt / tau)


def clamp_omega(w, p):
    return min(p['omega_max'], max(p['omega_min'], w))


def omega_for_thrust(t, p):
    """T = kT Ω² 를 거꾸로. 음수 추력은 0 으로 본다."""
    return math.sqrt(max(t, 0.0) / p['kT'])
