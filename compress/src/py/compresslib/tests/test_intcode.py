# -*- coding: utf-8 -*-
"""intcode 시험 — SPEC §2.

정수 부호는 표로 외우는 것이 아니라 규칙이 있다. 그래서 시험도 표를
그대로 적어 두고 견준다 — 규칙을 틀리게 옮겼을 때 어느 값에서 갈라지는지
바로 보이기 때문이다.
"""
import unittest

from compresslib import bitio, intcode


def bits(fn, *args):
    """부호 하나를 써서 비트 문자열로 돌려준다 (채움은 빼고)."""
    w = bitio.MsbWriter()
    n = fn(w, *args)
    return n


class Recorder:
    """MsbWriter 흉내 — 쓴 비트를 문자열로 모은다."""

    def __init__(self):
        self.s = ''

    def write_bit(self, b):
        self.s += '1' if b else '0'

    def write_bits(self, v, n):
        for i in range(n - 1, -1, -1):
            self.write_bit((v >> i) & 1)


def rec(fn, *args):
    r = Recorder()
    fn(r, *args)
    return r.s


class TestVarint(unittest.TestCase):

    TABLE = [(0, '00'), (1, '01'), (127, '7f'), (128, '8001'),
             (300, 'ac02'), (16383, 'ff7f'), (16384, '808001')]

    def test_table(self):
        for v, hexs in self.TABLE:
            self.assertEqual(intcode.put_varint(v).hex(), hexs, v)

    def test_round_trip(self):
        for v, _ in self.TABLE:
            self.assertEqual(intcode.get_varint(intcode.put_varint(v)),
                             (v, len(intcode.put_varint(v))))

    def test_max_u64(self):
        v = (1 << 64) - 1
        raw = intcode.put_varint(v)
        self.assertEqual(len(raw), 10)
        self.assertEqual(intcode.get_varint(raw)[0], v)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            intcode.put_varint(-1)

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            intcode.get_varint(b'\x80')

    def test_too_long_raises(self):
        with self.assertRaises(ValueError):
            intcode.get_varint(b'\x80' * 11)


class TestZigzag(unittest.TestCase):

    TABLE = [(0, 0), (-1, 1), (1, 2), (-2, 3), (2, 4),
             (-3, 5), (2147483647, 4294967294),
             (-2147483648, 4294967295)]

    def test_table(self):
        for n, u in self.TABLE:
            self.assertEqual(intcode.zigzag(n), u, n)
            self.assertEqual(intcode.unzigzag(u), n, u)

    def test_extremes(self):
        lo, hi = -(1 << 63), (1 << 63) - 1
        for n in (lo, hi, lo + 1, hi - 1):
            self.assertEqual(intcode.unzigzag(intcode.zigzag(n)), n)


class TestEliasGamma(unittest.TestCase):

    TABLE = [(1, '1'), (2, '010'), (3, '011'), (4, '00100'),
             (5, '00101'), (6, '00110'), (7, '00111'),
             (8, '0001000'), (255, '000000011111111')]

    def test_table(self):
        for v, s in self.TABLE:
            self.assertEqual(rec(intcode.put_gamma, v), s, v)

    def test_zero_raises(self):
        with self.assertRaises(ValueError):
            rec(intcode.put_gamma, 0)

    def test_round_trip(self):
        w = bitio.MsbWriter()
        for v in range(1, 500):
            intcode.put_gamma(w, v)
        w.flush()
        r = bitio.MsbReader(w.bytes())
        for v in range(1, 500):
            self.assertEqual(intcode.get_gamma(r), v)


class TestEliasDelta(unittest.TestCase):

    TABLE = [(1, '1'), (2, '0100'), (3, '0101'), (4, '01100'),
             (5, '01101'), (8, '00100000'), (16, '001010000')]

    def test_table(self):
        for v, s in self.TABLE:
            self.assertEqual(rec(intcode.put_delta, v), s, v)

    def test_round_trip(self):
        w = bitio.MsbWriter()
        for v in range(1, 500):
            intcode.put_delta(w, v)
        w.flush()
        r = bitio.MsbReader(w.bytes())
        for v in range(1, 500):
            self.assertEqual(intcode.get_delta(r), v)

    def test_delta_is_shorter_than_gamma_for_large(self):
        # 델타가 감마보다 나은 지점이 있다는 것이 이 부호의 존재 이유다
        big = 1 << 20
        self.assertLess(len(rec(intcode.put_delta, big)),
                        len(rec(intcode.put_gamma, big)))


class TestRice(unittest.TestCase):

    # (k, n, 비트) — 단항은 1을 q개 쓰고 0 하나로 닫는다
    TABLE = [(2, 0, '000'), (2, 1, '001'), (2, 3, '011'),
             (2, 4, '1000'), (2, 5, '1001'), (2, 9, '11001'),
             (0, 0, '0'), (0, 3, '1110'),
             (4, 16, '100000'), (4, 15, '01111'),
             (0, 100, '1' * 100 + '0')]

    def test_table(self):
        for k, n, s in self.TABLE:
            self.assertEqual(rec(intcode.put_rice, n, k), s, (k, n))

    def test_round_trip(self):
        for k in (0, 1, 3, 8):
            w = bitio.MsbWriter()
            for v in range(0, 300):
                intcode.put_rice(w, v, k)
            w.flush()
            r = bitio.MsbReader(w.bytes())
            for v in range(0, 300):
                self.assertEqual(intcode.get_rice(r, k), v, (k, v))

    def test_huge_quotient_raises(self):
        w = bitio.MsbWriter()
        with self.assertRaises(ValueError):
            intcode.put_rice(w, 1 << 40, 0)


class TestGoldenCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(intcode.encode(b''), b'\x00')

    def test_round_trip(self):
        for src in (b'', b'A', b'\x00' * 100, bytes(range(256)),
                    b'\xff' * 1000):
            self.assertEqual(intcode.decode(intcode.encode(src)), src)

    def test_zeros_shrink_eightfold(self):
        # 0 바이트는 gamma(1) = 비트 하나다
        out = intcode.encode(b'\x00' * 800)
        self.assertEqual(len(out), 2 + 100)

    def test_high_bytes_grow(self):
        # 0xff 는 gamma(256) = 17비트다. 커지는 것이 정상이다.
        out = intcode.encode(b'\xff' * 800)
        self.assertGreater(len(out), 800)

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            intcode.decode(intcode.encode(b'hello world')[:3])


if __name__ == '__main__':
    unittest.main()
