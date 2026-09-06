# -*- coding: utf-8 -*-
"""난수 — SPEC §5.2. 볼랜드 계열 LCG.

   승수 22695477 은 도스 시절 터보 C 의 rand() 가 쓰던 값이다.
   x 를 그냥 곱하면 22695477 * 2^32 ~ 2^57 이라 배정밀도 가수(53비트)를 넘는다.
   그래서 x 를 상·하위 16비트로 쪼개 두 번 곱한다. (정리 5.1)
"""
LCG_A = 22695477
LCG_C = 1
LCG_M = 4294967296              # 2^32


class Rng(object):
    __slots__ = ('s',)

    def __init__(self, seed):
        self.s = seed % LCG_M

    def next(self):
        """상태를 한 걸음 굴리고 15비트 난수를 돌려준다 (0..32767).

           하위 비트는 주기가 짧다 — 최하위 비트는 0,1 을 번갈 뿐이다.
           그래서 도스 시절 rand() 도 비트 30..16 을 꺼내 썼다.
        """
        s = self.s
        sh = s // 65536
        sl = s - sh * 65536
        lo = LCG_A * sl + LCG_C
        hi = LCG_A * sh
        self.s = ((hi % 65536) * 65536 + lo) % LCG_M
        return (self.s // 65536) % 32768

    def below(self, n):
        return self.next() % n

    def roll(self, n, m):
        t = 0
        for _ in range(n):
            t += self.next() % m + 1
        return t
