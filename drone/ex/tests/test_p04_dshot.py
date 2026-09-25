# -*- coding: utf-8 -*-
"""ex/dshot_packet.py 시험 — Betaflight 의 DShot 프레임 틀."""
import itertools
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import dshot_packet as D  # noqa: E402


class Packet(unittest.TestCase):
    def test_hand_example(self):
        # 1046 → 12비트 0x82C, 니블 8^2^C = 6 → 0x82C6
        self.assertEqual(D.packet(1046), 0x82C6)

    def test_telemetry_bit(self):
        self.assertEqual(D.packet(1046, telemetry=True) >> 4, 0x82D)

    def test_inverted_checksum(self):
        a, b = D.packet(1046), D.packet(1046, inverted=True)
        self.assertEqual(a >> 4, b >> 4)
        self.assertEqual((a ^ b) & 0xF, 0xF)

    def test_throttle_range(self):
        self.assertEqual((D.MIN_THROTTLE, D.MAX_THROTTLE), (48, 2047))

    def test_roundtrip_all_values(self):
        for v in range(2048):
            for t in (False, True):
                f = D.packet(v, telemetry=t)
                self.assertTrue(D.check(f))
                self.assertEqual(D.unpack(f), (v, t))

    def test_value_out_of_range(self):
        with self.assertRaises(ValueError):
            D.packet(2048)
        with self.assertRaises(ValueError):
            D.packet(-1)

    def test_every_single_flip_is_caught(self):
        f = D.packet(1046)
        self.assertEqual(D.flips_caught(f, 1), (16, 16))

    def test_double_flips_in_one_column_slip(self):
        # 같은 자리(니블 안 위치)의 두 비트가 뒤집히면 XOR 가 그대로다
        f = D.packet(1046)
        self.assertEqual(D.flips_caught(f, 2), (96, 120))
        n = sum(1 for a, b in itertools.combinations(range(16), 2)
                if a % 4 == b % 4)
        self.assertEqual(n, 24)

    def test_frame_time(self):
        self.assertAlmostEqual(D.frame_us(600), 16 / 0.6, places=9)
        self.assertAlmostEqual(D.frame_us(150), 16 / 0.15, places=9)


if __name__ == '__main__':
    unittest.main()
