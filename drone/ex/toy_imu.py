# -*- coding: utf-8 -*-
"""5부 9장 — 완구 드론 펌웨어의 자세 추정과 헤드리스 모드를 파이썬으로.

오픈소스 H8 mini 펌웨어(silver13/h8mini-dual, MIT)의 imu.c·control.c
를 이 덱의 좌표(FLU)로 옮겼다. 센서는 6축(자이로 + 가속도계)뿐이다.

상보 필터: 몸체에서 본 '위' 벡터(가속도계가 가만히 있을 때 재는
비력)를 들고 다닌다. 걸음마다
  1) 자이로로 돌린다 — 세계에 고정된 벡터를 도는 몸체에서 보면
     u̇ = −ω × u. 펌웨어는 축마다 작은 각 근사(sin≈각, cos≈1)로
     세 번 돌리는데, 1차까지 같은 식이다.
  2) 가속도의 크기가 0.7–1.3 g 안이면, 1 g 로 정규화한 가속도 쪽으로
     계수 exp(−dt/T) 의 저역 통과로 끌어당긴다(T = 2 초).
그래서 롤·피치는 가속도계가 붙잡아 흐르지 않지만, 요에는 붙잡을
기준이 없다 — 헤드리스 모드의 요 각은 자이로 z 의 적분뿐이다.
걸음당 O(1).
"""
import math


def coeff(dt, filtertime):
    """펌웨어 lpfcalc: exp(−dt/T). dt ≤ 0 이면 0, T ≤ 0 이면 1."""
    if dt <= 0:
        return 0.0
    if filtertime <= 0:
        return 1.0
    return min(1.0, math.exp(-dt / filtertime))


class ToyIMU:
    """6축 상보 필터 — est 는 몸체 좌표의 '위' 벡터(단위 m/s²)."""

    def __init__(self, filtertime=2.0, acc_min=0.7, acc_max=1.3,
                 g=9.81):
        self.T, self.g = filtertime, g
        self.lo, self.hi = acc_min, acc_max
        self.est = [0.0, 0.0, g]

    def update(self, gyro, acc, dt):
        e, w = self.est, gyro
        # 1) 자이로로 돌리기: e ← e − (ω × e)·dt
        cx = w[1] * e[2] - w[2] * e[1]
        cy = w[2] * e[0] - w[0] * e[2]
        cz = w[0] * e[1] - w[1] * e[0]
        e = [e[0] - cx * dt, e[1] - cy * dt, e[2] - cz * dt]
        # 2) 가속도가 1 g 근처일 때만 끌어당기기(창은 양쪽 모두 제외)
        mag = math.sqrt(acc[0] ** 2 + acc[1] ** 2 + acc[2] ** 2)
        if self.lo * self.g < mag < self.hi * self.g:
            k = coeff(dt, self.T)
            e = [e[i] * k + acc[i] * (self.g / mag) * (1 - k)
                 for i in range(3)]
        self.est = e
        return e

    def tilt(self):
        """추정한 '위' 와 몸체 z 축 사이의 각 [rad]."""
        e = self.est
        n = math.sqrt(e[0] ** 2 + e[1] ** 2 + e[2] ** 2)
        return math.acos(max(-1.0, min(1.0, e[2] / n)))

    def roll_pitch(self):
        e = self.est
        return (math.atan2(e[1], e[2]),
                math.atan2(-e[0], math.hypot(e[1], e[2])))


class Headless:
    """헤드리스 모드: 켤 때의 앞을 기준으로 스틱을 돌린다.

    기준 방향은 자이로 z 를 적분한 요 각 하나뿐 — 자력계가 없으니
    바이어스 b 만큼 1 초에 b rad 씩 틀어진다."""

    def __init__(self):
        self.yaw = 0.0

    def reset(self):
        self.yaw = 0.0

    def update(self, gyro_z, dt):
        self.yaw += gyro_z * dt
        while self.yaw < -math.pi:
            self.yaw += 2 * math.pi
        while self.yaw > math.pi:
            self.yaw -= 2 * math.pi
        return self.yaw

    def rotate(self, x, y):
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return x * c - y * s, y * c + x * s
