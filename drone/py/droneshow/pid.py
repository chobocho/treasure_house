# -*- coding: utf-8 -*-
"""pid — PID 제어기와 그것을 읽는 공식들 (SPEC §5.1, T14–T17, T22).

u = kp·e + ki·∫e + kd·D. D 는 오차가 아니라 **측정값**을 미분한다 —
목표를 바꿀 때마다 D 가 튀어 모터를 걷어차는 것(derivative kick)을
막기 위해서다. 미분은 잡음을 키우므로 1차 저역 통과로 누른다(T22).
"""
import math


class PID:
    def __init__(self, kp, ki, kd, i_max=math.inf, tau_d=0.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.i_max, self.tau_d = i_max, tau_d
        self.reset()

    def reset(self):
        self.i = 0.0
        self.d = 0.0
        self.y_prev = None

    def update(self, ref, y, dt):
        """목표 ref, 측정 y, 걸음 dt → 출력 u."""
        e = ref - y
        self.i = max(-self.i_max, min(self.i_max, self.i + e * dt))
        if self.y_prev is None:
            raw = 0.0                    # 첫 호출 — 앞 측정이 없다
        else:
            raw = -(y - self.y_prev) / dt
        self.y_prev = y
        # 1차 저역 통과: D_f += (D − D_f)·dt/(τ + dt). τ = 0 이면 그대로
        self.d += (raw - self.d) * dt / (self.tau_d + dt)
        return self.kp * e + self.ki * self.i + self.kd * self.d


class VecPID:
    """축마다 스칼라 PID 하나씩."""

    def __init__(self, kp, ki, kd, i_max=math.inf, tau_d=0.0):
        self.axes = [PID(kp[k], ki[k], kd[k], i_max, tau_d)
                     for k in range(3)]

    def reset(self):
        for a in self.axes:
            a.reset()

    def update(self, ref, y, dt):
        return [self.axes[k].update(ref[k], y[k], dt) for k in range(3)]


# ------------------------------------------------ 해석 공식 (7·9부)
def second_order(kp, kd):
    """x'' + kd x' + kp x = kp r → (ζ, ωn). ωn = √kp, ζ = kd/(2√kp)."""
    wn = math.sqrt(kp)
    return kd / (2.0 * wn), wn


def overshoot(zeta):
    """계단 응답의 최대 초과량 e^(−πζ/√(1−ζ²)). ζ ≥ 1 이면 0 (T14)."""
    if zeta >= 1.0:
        return 0.0
    return math.exp(-math.pi * zeta / math.sqrt(1.0 - zeta * zeta))


def routh3(a2, a1, a0):
    """s³ + a2 s² + a1 s + a0 의 근이 모두 왼쪽 반평면에 있나 (T16)."""
    return a2 > 0 and a1 > 0 and a0 > 0 and a2 * a1 > a0


def cascade_poles(k, b):
    """안쪽 1차 루프(빠르기 b)와 바깥 P(이득 k) — s² + b s + b k 의 근.

    근이 실수일 때(b ≥ 4k)만 [빠른 근, 느린 근] 을 돌려준다. b ≫ k 이면
    느린 근이 −k 에 붙어 바깥 루프가 안쪽을 1 로 본 것과
    같아진다(T17)."""
    disc = b * b - 4.0 * b * k
    if disc < 0:
        raise ValueError('복소수 근 — b < 4k')
    r = math.sqrt(disc)
    return [(-b - r) / 2.0, (-b + r) / 2.0]


def derivative_gain(w):
    """sin(ωt) 를 미분하면 진폭이 ω 배 — D항이 잡음을 키우는 까닭."""
    return w


def lowpass_gain(w, tau):
    """1차 저역 통과의 진폭비 1/√(1 + (ωτ)²) (T22)."""
    return 1.0 / math.sqrt(1.0 + (w * tau) ** 2)
