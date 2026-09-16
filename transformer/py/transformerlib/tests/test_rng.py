# -*- coding: utf-8 -*-
"""rng 의 증인 시험 — SPEC.md §1.

여기 박은 상수는 SPEC.md §1.4 와 c/tests/test_rng.c 에 똑같이 적힌다.
파이썬과 C 가 같은 씨앗에서 같은 수열을 내야 가중치 초기화와 배치
뽑기가 같아지고, 그래야 두 구현을 한 스텝씩 맞대어 볼 수 있다.
"""
import math
import unittest

from transformerlib import rng

SEED42_STATE = [0xbdd732262feb6e95, 0x28efe333b266f103,
                0x47526757130f9f52, 0x581ce1ff0e4ae394]
SEED42_NEXT = [0x15780b2e0c2ec716, 0x6104d9866d113a7e,
               0xae17533239e499a1, 0xecb8ad4703b360a1,
               0xfde6dc7fe2ec5e64, 0xc50da53101795238,
               0xb82154855a65ddb2, 0xd99a2743ebe60087]
SEED42_UNIFORM = [0.08386297105988216, 0.3789802506626686,
                  0.6800434110281394, 0.9246929453253876]
SEED42_NORMAL = [-0.303263064678738, 1.3438117634372806,
                 0.3834617912676943, 0.9369624250258953]


class TestPinned(unittest.TestCase):
    def test_splitmix_expansion(self):
        self.assertEqual(rng.Rng(42).s, SEED42_STATE)

    def test_first_eight_outputs(self):
        r = rng.Rng(42)
        self.assertEqual([r.next() for _ in range(8)], SEED42_NEXT)

    def test_uniform(self):
        r = rng.Rng(42)
        # 비트까지 같아야 한다 — 허용 오차 0 (SPEC §9)
        self.assertEqual([r.uniform() for _ in range(4)],
                         SEED42_UNIFORM)

    def test_normal(self):
        r = rng.Rng(42)
        self.assertEqual([r.normal() for _ in range(4)], SEED42_NORMAL)

    def test_outputs_stay_in_64_bits(self):
        r = rng.Rng(2 ** 64 - 1)
        for _ in range(1000):
            v = r.next()
            self.assertTrue(0 <= v < 2 ** 64)


class TestDistributions(unittest.TestCase):
    def test_uniform_range(self):
        r = rng.Rng(7)
        xs = [r.uniform() for _ in range(20000)]
        self.assertTrue(all(0.0 <= x < 1.0 for x in xs))
        self.assertLess(abs(sum(xs) / len(xs) - 0.5), 0.01)

    def test_normal_moments(self):
        """평균 0 · 분산 1 — 2만 개에서 2 % 안 (PLAN.md §3.1)."""
        r = rng.Rng(42)
        xs = [r.normal() for _ in range(20000)]
        m = sum(xs) / len(xs)
        v = sum((x - m) ** 2 for x in xs) / len(xs)
        self.assertLess(abs(m), 0.02)
        self.assertLess(abs(v - 1.0), 0.02)

    def test_randint_bounds_and_coverage(self):
        r = rng.Rng(3)
        seen = [0] * 7
        for _ in range(7000):
            k = r.randint(7)
            seen[k] += 1
        self.assertTrue(all(800 < c < 1200 for c in seen))

    def test_randint_rejects_empty(self):
        with self.assertRaises(ValueError):
            rng.Rng(1).randint(0)

    def test_permutation(self):
        p = rng.Rng(5).permutation(50)
        self.assertEqual(sorted(p), list(range(50)))
        self.assertEqual(p, rng.Rng(5).permutation(50))
        self.assertNotEqual(p, list(range(50)))

    def test_permutation_edges(self):
        self.assertEqual(rng.Rng(5).permutation(0), [])
        self.assertEqual(rng.Rng(5).permutation(1), [0])

    def test_same_seed_same_stream_different_seed_differs(self):
        a = [rng.Rng(10).next() for _ in range(3)]
        b = [rng.Rng(10).next() for _ in range(3)]
        c = [rng.Rng(11).next() for _ in range(3)]
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_normal_never_takes_log_of_zero(self):
        """u1 = 1 − uniform() 이라 u1 은 (0, 1] — ln 0 이 없다."""
        r = rng.Rng(0)
        for _ in range(5000):
            self.assertTrue(math.isfinite(r.normal()))


if __name__ == '__main__':
    unittest.main()
