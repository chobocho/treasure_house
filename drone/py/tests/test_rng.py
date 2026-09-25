# -*- coding: utf-8 -*-
"""rng 시험 — SPEC §2 의 xorshift128 (두 언어가 같은 수를 뽑는다)."""
import unittest

from droneshow import rng


class Stream(unittest.TestCase):
    def test_same_seed_same_stream(self):
        a, b = rng.Rng(7), rng.Rng(7)
        self.assertEqual([a.next() for _ in range(50)],
                         [b.next() for _ in range(50)])

    def test_seeds_differ(self):
        a, b = rng.Rng(1), rng.Rng(2)
        self.assertNotEqual([a.next() for _ in range(5)],
                            [b.next() for _ in range(5)])

    def test_recurrence(self):
        # 스펙의 식을 여기서 한 번 더 손으로 돌린다 — 구현이
        # 식을 바꿔 적어도 두 쪽이 같이 틀릴 수는 없게.
        g = rng.Rng(0)
        x, y, z, w = g.s
        t = (x ^ (x << 11)) & 0xffffffff
        want = (w ^ (w >> 19) ^ t ^ (t >> 8)) & 0xffffffff
        self.assertEqual(g.next(), want)

    def test_words_stay_32bit(self):
        g = rng.Rng(2026)
        for _ in range(1000):
            self.assertTrue(0 <= g.next() <= 0xffffffff)


class Distribution(unittest.TestCase):
    def test_uniform_range_and_mean(self):
        g = rng.Rng(7)
        u = [g.uniform() for _ in range(20000)]
        self.assertTrue(all(0.0 <= x < 1.0 for x in u))
        self.assertAlmostEqual(sum(u) / len(u), 0.5, delta=0.01)

    def test_normal_moments(self):
        g = rng.Rng(7)
        n = [g.normal() for _ in range(20000)]
        m = sum(n) / len(n)
        var = sum((x - m) ** 2 for x in n) / len(n)
        self.assertAlmostEqual(m, 0.0, delta=0.03)
        self.assertAlmostEqual(var, 1.0, delta=0.04)


if __name__ == '__main__':
    unittest.main()
