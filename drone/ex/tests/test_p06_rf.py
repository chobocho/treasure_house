# -*- coding: utf-8 -*-
"""ex/rf_link.py 시험 — 자유 공간 손실 모델과 주파수 도약 장난감."""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))

import rf_link as RF  # noqa: E402


class Link(unittest.TestCase):
    def test_dbm(self):
        self.assertAlmostEqual(RF.dbm(100.0), 20.0, places=12)
        self.assertAlmostEqual(RF.dbm(1.0), 0.0, places=12)

    def test_fspl_distance_doubling_is_6db(self):
        f = 2.44e9
        d = RF.fspl_db(2000.0, f) - RF.fspl_db(1000.0, f)
        self.assertAlmostEqual(d, 20 * math.log10(2), places=12)

    def test_fspl_matches_definition(self):
        d, f = 1234.5, 915e6
        want = (4 * math.pi * d * f / RF.C) ** 2
        self.assertAlmostEqual(RF.fspl_db(d, f), 10 * math.log10(want),
                               places=9)

    def test_range_inverts_fspl(self):
        for d in (1.0, 500.0, 40000.0):
            self.assertAlmostEqual(
                RF.range_m(RF.fspl_db(d, 2.44e9), 2.44e9) / d, 1.0,
                places=12)

    def test_budget(self):
        self.assertEqual(RF.budget(20, 2, 2, -108), 132)

    def test_wavelength(self):
        self.assertAlmostEqual(RF.wavelength(RF.C), 1.0, places=15)


class Hop(unittest.TestCase):
    def test_every_channel_once_per_cycle(self):
        seq = RF.hops(b'phrase', 40, 4)
        for c in range(4):
            self.assertEqual(sorted(seq[40 * c:40 * c + 40]),
                             list(range(40)))

    def test_same_phrase_same_pattern(self):
        self.assertEqual(RF.hops(b'abc', 20, 3), RF.hops(b'abc', 20, 3))
        self.assertNotEqual(RF.hops(b'abc', 20, 3),
                            RF.hops(b'abd', 20, 3))

    def test_blocked_channels_lose_k_over_n(self):
        seq = RF.hops(b'x', 40, 10)
        self.assertEqual(RF.lost(seq, set(range(6))), 6 / 40)

    def test_two_links_collide_about_1_over_n(self):
        a = RF.hops(b'one', 40, 500)
        b = RF.hops(b'two', 40, 500)
        self.assertAlmostEqual(RF.collide(a, b), 1 / 40, delta=0.004)


if __name__ == '__main__':
    unittest.main()
