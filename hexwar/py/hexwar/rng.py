# -*- coding: utf-8 -*-
"""난수와 해시 — SPEC §5, §10.4.

   도스 게임의 난수는 대부분 32비트 선형 합동 생성기(LCG)였다. 곱셈 한 번,
   덧셈 한 번, 자르기 한 번이면 끝이라 8086 에서도 수십 사이클이면 나온다.
   여기서는 Numerical Recipes 의 상수를 쓴다 — 세 언어가 같은 수열을 내야
   전투 판정이 재현되므로, 상수와 32비트 자르기 방식이 규격의 일부다.

   주의: LCG 는 하위 비트의 주기가 짧다. state & 7 로 방향을 뽑으면 8칸마다
   같은 패턴이 돈다. 그래서 주사위는 상위 비트(>> 16)에서 꺼낸다.
"""

M32 = 0xFFFFFFFF
MUL = 1664525
ADD = 1013904223


class Rng(object):
    __slots__ = ('state',)

    def __init__(self, seed):
        self.state = seed & M32

    def next(self):
        """다음 상태를 만들고 그 값을 돌려준다. O(1)."""
        self.state = (self.state * MUL + ADD) & M32
        return self.state

    def d6(self):
        """1..6. 상위 비트에서 뽑는다 — 하위 비트는 주기가 짧다."""
        return ((self.next() >> 16) % 6) + 1

    def below(self, n):
        """0..n-1. 나머지 편향은 n 이 작아 무시할 수준(도스 게임도 그랬다)."""
        return (self.next() >> 16) % n

    def save(self):
        return self.state

    def restore(self, s):
        """언두가 난수 상태를 되돌릴 때 쓴다 — SPEC §11.3."""
        self.state = s & M32


def fnv1a(data):
    """FNV-1a 32비트. SPEC §10.4.

       세 언어에 다 있는 32비트 곱셈만으로 되고, 표도 필요 없어 골든 벡터의
       요약값으로 쓴다. 암호학용이 아니다 — 여기서는 '두 실행이 같은 바이트를
       만들었는가'만 판정한다.
    """
    h = 2166136261
    for b in data:
        h = ((h ^ b) * 16777619) & M32
    return h


def fnv1a_str(s):
    return fnv1a(s.encode('utf-8'))
