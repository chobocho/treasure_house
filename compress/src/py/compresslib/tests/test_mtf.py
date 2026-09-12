# -*- coding: utf-8 -*-
"""mtf 시험 — SPEC §4.

요점은 하나다. 앞으로 **옮기는** 것이지 **바꿔치는** 것이 아니다.
바꿔치기도 자기들끼리는 왕복이 되므로 시험이 없으면 안 드러난다.
"""
import unittest

from compresslib import mtf


class TestTransform(unittest.TestCase):

    def test_identity_start(self):
        # 표가 0..255 로 시작하므로 첫 바이트는 자기 값이 그대로 나온다
        self.assertEqual(mtf.transform(b'\x00'), b'\x00')
        self.assertEqual(mtf.transform(b'\x41'), b'\x41')

    def test_repeat_becomes_zero(self):
        self.assertEqual(mtf.transform(b'AAAA'), b'\x41\x00\x00\x00')

    def test_is_move_not_swap(self):
        # 'C','B','A' 를 넣으면 표는 C,B,A,... 가 되어야 한다.
        # 바꿔치기였다면 세 번째 결과가 2 가 아니라 0 이 된다.
        self.assertEqual(mtf.transform(b'CBA'), b'\x43\x43\x43')
        self.assertEqual(mtf.transform(b'CBAA'), b'\x43\x43\x43\x00')
        self.assertEqual(mtf.transform(b'CBAB'), b'\x43\x43\x43\x01')

    def test_round_trip(self):
        cases = [b'', b'A', b'AAAA', bytes(range(256)),
                 bytes(reversed(range(256))), b'ab' * 500,
                 bytes((i * 31 + 7) & 0xFF for i in range(5000))]
        for src in cases:
            self.assertEqual(mtf.inverse(mtf.transform(src)), src)

    def test_length_is_preserved(self):
        src = bytes(range(256)) * 3
        self.assertEqual(len(mtf.transform(src)), len(src))


class TestGoldenCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(mtf.encode(b''), b'\x00')

    def test_size_is_length_plus_header(self):
        for n in (1, 127, 128, 5000):
            src = bytes((i * 13) & 0xFF for i in range(n))
            head = 1 if n < 128 else (2 if n < 16384 else 3)
            self.assertEqual(len(mtf.encode(src)), head + n)

    def test_round_trip(self):
        for src in (b'', b'A', b'\x00' * 100, bytes(range(256))):
            self.assertEqual(mtf.decode(mtf.encode(src)), src)

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            mtf.decode(mtf.encode(b'hello')[:3])


if __name__ == '__main__':
    unittest.main()
