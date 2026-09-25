# -*- coding: utf-8 -*-
"""sensors — 자이로·가속도계·기압계·GNSS 의 모델 (SPEC §6).

잡음은 모두 씨앗을 준 rng 에서 온다 — 같은 씨앗이면 같은 잡음이다.
자이로 바이어스는 한 번 뽑아 고정한다(실제 칩의 켤 때마다 다른
바이어스를 흉내 낸다).
"""
from . import quat as Q


class Sensors:
    def __init__(self, p, g):
        self.p, self.g = p, g
        self.bias = [p['sigma_bg'] * g.normal() for _ in range(3)]

    def _n(self, sigma):
        return sigma * self.g.normal() if sigma else 0.0

    def gyro(self, s):
        """몸체 각속도 + 바이어스 + 잡음."""
        return [s[10 + i] + self.bias[i] + self._n(self.p['sigma_g'])
                for i in range(3)]

    def accel(self, s, d):
        """비력(specific force) Rᵀ(v̇ + g·e3) — 중력은 못 잰다.

        d 는 quadrotor.deriv 의 결과(가속도가 d[3:6]). 떠 있으면 +g,
        자유낙하면 0 이다 — 가속도계가 재는 것은 '중력을 뺀 것'이다."""
        a = [d[3], d[4], d[5] + self.p['g']]
        b = Q.rotate(Q.conj(s[6:10]), a)
        return [b[i] + self._n(self.p['sigma_a']) for i in range(3)]

    def baro(self, s):
        """고도 + 잡음."""
        return s[2] + self._n(self.p['sigma_b'])

    def gnss(self, s):
        """위치 + 축마다 잡음."""
        return [s[i] + self._n(self.p['sigma_p']) for i in range(3)]
