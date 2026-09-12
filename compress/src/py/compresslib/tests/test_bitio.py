# -*- coding: utf-8 -*-
"""bitio 시험 — SPEC §1.

여기서 볼 것은 "돌아가는가" 가 아니라 **다섯 언어가 같은 바이트를
내는가** 다. 그래서 왕복만 보지 않고, 나온 바이트를 손으로 적은
기댓값과 견준다. 왕복만 보면 채움을 1로 채우는 구현도 그냥 통과한다.
"""
import unittest

from compresslib import bitio


class TestMsbWriter(unittest.TestCase):

    def test_empty_flush_emits_nothing(self):
        w = bitio.MsbWriter()
        w.flush()
        self.assertEqual(w.bytes(), b'')

    def test_single_one_bit_is_0x80(self):
        # 첫 비트는 첫 바이트의 7번 비트에 앉는다
        w = bitio.MsbWriter()
        w.write_bit(1)
        w.flush()
        self.assertEqual(w.bytes(), b'\x80')

    def test_flush_pads_with_zero_bits(self):
        # 채움은 0 이다. 1로 채우면 0xFF 가 나오고 다섯 언어가 갈라진다.
        w = bitio.MsbWriter()
        w.write_bits(0b111, 3)
        w.flush()
        self.assertEqual(w.bytes(), b'\xe0')

    def test_write_bits_is_msb_first(self):
        w = bitio.MsbWriter()
        w.write_bits(0x41, 8)
        w.flush()
        self.assertEqual(w.bytes(), b'A')

    def test_crosses_byte_boundary(self):
        # 3비트 뒤에 0xFF 를 쓰면 0x1F 0xE0 이 되어야 한다
        w = bitio.MsbWriter()
        w.write_bits(0, 3)
        w.write_bits(0xFF, 8)
        w.flush()
        self.assertEqual(w.bytes(), b'\x1f\xe0')

    def test_wide_value(self):
        w = bitio.MsbWriter()
        w.write_bits(0x0123456789ABCDEF, 64)
        w.flush()
        self.assertEqual(w.bytes(),
                         bytes.fromhex('0123456789abcdef'))

    def test_zero_width_writes_nothing(self):
        w = bitio.MsbWriter()
        w.write_bits(0xFF, 0)
        w.flush()
        self.assertEqual(w.bytes(), b'')


class TestMsbReader(unittest.TestCase):

    def test_reads_back_what_was_written(self):
        w = bitio.MsbWriter()
        for v, n in ((1, 1), (0, 3), (0x2A, 6), (0xFFFF, 16)):
            w.write_bits(v, n)
        w.flush()
        r = bitio.MsbReader(w.bytes())
        self.assertEqual(r.read_bits(1), 1)
        self.assertEqual(r.read_bits(3), 0)
        self.assertEqual(r.read_bits(6), 0x2A)
        self.assertEqual(r.read_bits(16), 0xFFFF)

    def test_exhausted_raises(self):
        r = bitio.MsbReader(b'\x00')
        r.read_bits(8)
        with self.assertRaises(ValueError):
            r.read_bit()


class TestLsbWriter(unittest.TestCase):

    def test_single_one_bit_is_0x01(self):
        w = bitio.LsbWriter()
        w.write_bit(1)
        w.flush()
        self.assertEqual(w.bytes(), b'\x01')

    def test_write_bits_is_lsb_first(self):
        # 값은 낮은 비트부터 들어간다 — DEFLATE 의 헤더 칸이 이렇다
        w = bitio.LsbWriter()
        w.write_bits(0b101, 3)
        w.flush()
        self.assertEqual(w.bytes(), b'\x05')

    def test_deflate_empty_block_bits(self):
        # SPEC §10.6 의 빈 DEFLATE 스트림: BFINAL=1, BTYPE=01, 부호 256
        w = bitio.LsbWriter()
        w.write_bits(1, 1)          # BFINAL
        w.write_bits(1, 2)          # BTYPE = 01
        w.write_code(0, 7)          # 고정표의 256번 — MSB 먼저
        w.flush()
        self.assertEqual(w.bytes(), b'\x03\x00')

    def test_round_trip(self):
        w = bitio.LsbWriter()
        w.write_bits(0x5, 3)
        w.write_bits(0xABCD, 16)
        w.flush()
        r = bitio.LsbReader(w.bytes())
        self.assertEqual(r.read_bits(3), 0x5)
        self.assertEqual(r.read_bits(16), 0xABCD)


class TestGoldenCodec(unittest.TestCase):

    def test_empty_is_two_zero_bytes(self):
        # SPEC §0.3 의 예외. 몸통이 채움 비트 셋으로 시작하니 빈
        # 입력에도 바이트 하나가 더 나온다. n == 0 일 때만 채움을 빼면
        # 형식 안에 조건문이 생기는데, 그게 두 바이트보다 나쁘다.
        self.assertEqual(bitio.encode(b''), b'\x00\x00')

    def test_size_formula(self):
        # SPEC §1.4 — varint(n) + ceil((3 + 8n) / 8)
        for n in (0, 1, 2, 127, 128, 1000):
            src = bytes((i * 7) & 0xFF for i in range(n))
            out = bitio.encode(src)
            head = 1 if n < 128 else 2
            self.assertEqual(len(out), head + (3 + 8 * n + 7) // 8)

    def test_round_trip(self):
        for src in (b'', b'A', b'\x00' * 100, bytes(range(256))):
            self.assertEqual(bitio.decode(bitio.encode(src)), src)

    def test_truncated_raises(self):
        out = bitio.encode(b'hello world')
        with self.assertRaises(ValueError):
            bitio.decode(out[:3])


if __name__ == '__main__':
    unittest.main()
