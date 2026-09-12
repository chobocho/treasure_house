# -*- coding: utf-8 -*-
"""lzw 시험 — SPEC §7.

가장 잘 틀리는 자리가 딱 하나 있다. **복호기는 부호기보다 항목 하나
뒤처진다.** 그래서 폭을 늘리는 조건이 한 칸 어긋나고, 그 어긋남은 사전에
항목이 254개쯤 쌓일 때까지 드러나지 않는다. 작은 시험만 있으면 통과한다.
"""
import unittest

from compresslib import lzw


class TestStream(unittest.TestCase):

    def test_empty_is_header_plus_eof(self):
        # EOF(257) 하나만 9비트로 나가고 채워진다
        self.assertEqual(lzw.encode(b''), b'\x00\x80\x80')

    def test_single_byte(self):
        # 65 = 001000001, EOF = 100000001, 6비트 채움
        self.assertEqual(lzw.encode(b'A'), b'\x01\x20\xc0\x40')

    def test_repeat_uses_dictionary(self):
        # 'ABAB' → A, B, 258(AB), EOF. 넷 × 9비트 = 36비트 = 5바이트
        out = lzw.encode(b'ABAB')
        self.assertEqual(len(out), 1 + 5)


class TestKwKwK(unittest.TestCase):
    """부호기가 방금 만든 항목을 복호기가 아직 모르는 그 한 순간."""

    def test_ababab(self):
        for n in (3, 4, 5, 6, 20, 4096):
            src = (b'ab' * (n // 2 + 1))[:n]
            self.assertEqual(lzw.decode(lzw.encode(src)), src, n)

    def test_aaaa(self):
        for n in range(1, 60):
            src = b'a' * n
            self.assertEqual(lzw.decode(lzw.encode(src)), src, n)

    def test_code_from_the_future_raises(self):
        # 첫 부호 뒤에 아직 만들어지지 않은 부호를 넣는다
        bad = b'\x02' + bytes([0b00100000, 0b11000000,
                               0b01000000, 0b10000000])
        with self.assertRaises(ValueError):
            lzw.decode(bad)


class TestWidthGrowth(unittest.TestCase):
    """폭이 9 → 10 → 11 → 12 로 커지는 자리를 실제로 넘어가는 시험."""

    def test_crosses_512(self):
        # 사전 항목이 512개를 넘으려면 서로 다른 쌍이 254개 넘게
        # 필요하다
        src = bytes((i * 7 + 3) & 0xFF for i in range(3000))
        self.assertEqual(lzw.decode(lzw.encode(src)), src)

    def test_crosses_all_widths_and_clears(self):
        # 4096 을 넘겨 CLEAR 가 최소 한 번 나오게 한다
        src = bytes((i * 31 + 17) & 0xFF for i in range(60000))
        out = lzw.encode(src)
        self.assertEqual(lzw.decode(out), src)

    def test_clear_resets_width(self):
        src = bytes((i * 131 + 7) & 0xFF for i in range(200000))
        self.assertEqual(lzw.decode(lzw.encode(src)), src)


class TestRoundTrip(unittest.TestCase):

    def test_various(self):
        cases = [b'', b'A', b'AA', b'\x00' * 5000, bytes(range(256)),
                 b'the quick brown fox ' * 300,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000))]
        for src in cases:
            self.assertEqual(lzw.decode(lzw.encode(src)), src, src[:8])

    def test_shrinks_repetitive_input(self):
        src = b'the quick brown fox ' * 500
        self.assertLess(len(lzw.encode(src)), len(src) // 3)


class TestErrors(unittest.TestCase):

    def test_truncated_raises(self):
        out = lzw.encode(b'hello world' * 20)
        with self.assertRaises(ValueError):
            lzw.decode(out[:6])

    def test_length_mismatch_raises(self):
        # 헤더의 길이와 EOF 가 어긋나면 거절한다 (§7.4 의 이중 검사)
        out = bytearray(lzw.encode(b'hello'))
        out[0] = 4
        with self.assertRaises(ValueError):
            lzw.decode(bytes(out))


if __name__ == '__main__':
    unittest.main()
