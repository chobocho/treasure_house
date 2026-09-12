# -*- coding: utf-8 -*-
"""rle 시험 — SPEC §3. PackBits 와 0런 부호.

런 부호는 "몇 개나 이어지면 묶을 것인가" 하나로 출력이 완전히 달라진다.
문턱 3, 상한 128 이 그 답이고, 시험은 그 경계 바로 앞뒤만 본다.
"""
import unittest

from compresslib import rle


class TestPackBits(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(rle.encode(b''), b'\x00')

    def test_run_of_three(self):
        # 제어 257-3 = 254 = 0xfe, 그 뒤에 반복할 바이트 하나
        self.assertEqual(rle.encode(b'AAA'), b'\x03\xfeA')

    def test_run_of_two_is_literal(self):
        # 문턱이 3 이라 2 는 리터럴이다. 제어는 개수-1 = 1.
        self.assertEqual(rle.encode(b'AB'), b'\x02\x01AB')
        self.assertEqual(rle.encode(b'AA'), b'\x02\x01AA')

    def test_run_cap_128(self):
        self.assertEqual(rle.encode(b'A' * 128), b'\x80\x01\x81A')

    def test_run_129_splits(self):
        # 128 짜리 런 하나 + 남은 한 바이트는 리터럴
        self.assertEqual(rle.encode(b'A' * 129),
                         b'\x81\x01\x81A\x00A')

    def test_literal_then_run(self):
        self.assertEqual(rle.encode(b'AABBB'),
                         b'\x05\x01AA\xfeB')

    def test_literal_cap_128(self):
        src = bytes((i * 37 + 11) & 0xFF for i in range(200))
        out = rle.encode(src)
        # 리터럴 묶음은 128 을 못 넘는다 — 128 + 72 로 갈린다
        body = out[2:]
        self.assertEqual(body[0], 127)
        self.assertEqual(body[1 + 128], 71)

    def test_round_trip(self):
        cases = [b'', b'A', b'AA', b'AAA', b'A' * 1000,
                 bytes(range(256)), b'ab' * 500,
                 b'\x00' * 300 + b'\xff' * 3 + b'xyz']
        for src in cases:
            self.assertEqual(rle.decode(rle.encode(src)), src)

    def test_control_128_raises(self):
        with self.assertRaises(ValueError):
            rle.decode(b'\x03\x80AAA')

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            rle.decode(b'\x05\xfeA')

    def test_trailing_garbage_raises(self):
        good = rle.encode(b'AAA')
        with self.assertRaises(ValueError):
            rle.decode(good + b'\x00B')


class TestZeroRle(unittest.TestCase):
    """bzip2 의 RUNA/RUNB — 이진법의 자릿수 하나가 0 하나가 아니다."""

    TABLE = [(1, [0]), (2, [1]), (3, [0, 0]), (4, [1, 0]),
             (5, [0, 1]), (6, [1, 1]), (7, [0, 0, 0])]

    def test_run_table(self):
        for length, want in self.TABLE:
            self.assertEqual(rle.zero_run_encode([0] * length), want,
                             length)

    def test_nonzero_shifts_by_one(self):
        # 기호 0·1 을 RUNA·RUNB 가 가져갔으므로 나머지는 한 칸씩 밀린다
        self.assertEqual(rle.zero_run_encode([5, 0, 7]), [6, 0, 8])

    def test_round_trip(self):
        cases = [[], [0], [0] * 100, [3, 3, 3], [0, 1, 0, 2, 0, 0, 0],
                 [0] * 1000 + [255] + [0] * 7]
        for syms in cases:
            got = rle.zero_run_decode(rle.zero_run_encode(syms))
            self.assertEqual(got, syms)


if __name__ == '__main__':
    unittest.main()
