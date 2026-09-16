# -*- coding: utf-8 -*-
"""난수 — splitmix64 로 씨앗을 펴고 xoshiro256** 로 뽑는다 (SPEC.md §1).

파이썬의 random 모듈을 쓰지 않는 까닭: C 가 같은 수열을 내야 한다.
random 의 메르센 트위스터는 C 로 옮길 수는 있지만, 씨앗을 펴는 방식과
정규분포를 뽑는 방식(가우스 캐시)까지 맞추기가 번거롭다. 짧고 전부
적어 둘 수 있는 생성기를 골랐다. 한 번 뽑기는 O(1) 시간·O(1) 공간.

파이썬 정수는 넘치지 않으므로 64비트 넘침을 & MASK 로 흉내 낸다.
"""
import math

MASK = (1 << 64) - 1
INV53 = 1.0 / 9007199254740992.0          # 2⁻⁵³


def _rotl(x, k):
    return ((x << k) | (x >> (64 - k))) & MASK


def splitmix64(x):
    """(다음 상태, 출력). 씨앗 하나를 64비트 넷으로 펴는 데 쓴다."""
    x = (x + 0x9E3779B97F4A7C15) & MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return x, z ^ (z >> 31)


class Rng(object):
    """xoshiro256** 생성기 하나. 쓰임마다 따로 만든다(SPEC §1.5)."""

    def __init__(self, seed):
        x = seed & MASK
        self.s = []
        for _ in range(4):
            x, z = splitmix64(x)
            self.s.append(z)

    def next(self):
        """64비트 정수 하나 (SPEC §1.2)."""
        s = self.s
        result = (_rotl((s[1] * 5) & MASK, 7) * 9) & MASK
        t = (s[1] << 17) & MASK
        s[2] ^= s[0]
        s[3] ^= s[1]
        s[1] ^= s[2]
        s[0] ^= s[3]
        s[2] ^= t
        s[3] = _rotl(s[3], 45)
        return result

    def uniform(self):
        """[0, 1) — 위 53비트만 쓴다. double 이 정확히 담는 폭이다."""
        return (self.next() >> 11) * INV53

    def normal(self):
        """표준정규 하나 — Box–Muller 의 코사인 쪽만.

        사인 쪽을 남겨 다음에 주면 한 번에 둘을 얻지만, 그 캐시가
        C 와 "몇 번째 호출인가" 를 맞춰야 하는 짐이 된다. 버린다.
        """
        u1 = 1.0 - self.uniform()          # (0, 1] — ln 0 을 피한다
        u2 = self.uniform()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi
                                                          * u2)

    def randint(self, n):
        """0 ≤ r < n. ⌊uniform·n⌋ — 치우침은 2⁻⁵³·n 수준이라 무시."""
        if n <= 0:
            raise ValueError('randint(%d): n 은 양수여야 한다' % n)
        return int(self.uniform() * n)

    def permutation(self, n):
        """피셔–예이츠. O(n) 시간·O(n) 공간."""
        p = list(range(n))
        for i in range(n - 1, 0, -1):
            j = self.randint(i + 1)
            p[i], p[j] = p[j], p[i]
        return p
