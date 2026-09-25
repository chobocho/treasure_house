# -*- coding: utf-8 -*-
"""rng — 두 언어가 똑같이 뽑는 난수 (SPEC §2).

파이썬의 random 모듈을 쓰지 않는 까닭: 자바스크립트 판이 같은 수열을
만들 수 없기 때문이다. 마사글리아의 xorshift128 은 32비트 정수의
시프트와 XOR 만 쓰므로 두 언어에서 비트까지 같게 옮길 수 있다.
"""
import math

M32 = 0xffffffff


class Rng:
    """xorshift128 (Marsaglia 2003). 상태는 32비트 낱말 넷."""

    def __init__(self, seed=0):
        self.s = [123456789, 362436069, 521288629, 88675123]
        self.s[0] ^= seed & M32
        # 씨앗을 섞은 첫 몇 개는 서로 닮았다 — 16개를 버린다
        for _ in range(16):
            self.next()

    def next(self):
        """다음 32비트 부호 없는 정수."""
        x, y, z, w = self.s
        t = (x ^ (x << 11)) & M32
        nw = (w ^ (w >> 19) ^ t ^ (t >> 8)) & M32
        self.s = [y, z, w, nw]
        return nw

    def uniform(self):
        """[0, 1) 의 실수."""
        return self.next() / 4294967296.0

    def normal(self):
        """표준정규분포 — 박스-뮬러. 한 번에 두 개를 쓴다."""
        u1 = 1.0 - self.uniform()          # (0, 1] — log(0) 을 피한다
        u2 = self.uniform()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(
            2.0 * math.pi * u2)
