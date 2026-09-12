# -*- coding: utf-8 -*-
"""huffman 시험 — SPEC §5.

트리를 만들지 않고 **길이 벡터** 를 바로 구한다. 트리를 만들면 우선순위
큐의 동점 처리가 언어마다 달라 최적 길이가 여러 벌 나오고, 다섯 언어가
사이좋게 서로 다른 파일을 낸다. 그래서 시험도 트리 모양이 아니라
길이 벡터와 그 길이에서 나온 부호를 본다.
"""
import unittest

from compresslib import huffman


def freqs_of(data):
    f = [0] * 256
    for b in data:
        f[b] += 1
    return f


def kraft(lengths):
    """길이 벡터의 크래프트 합 × 2^15. 접두 부호면 32768 이하다."""
    return sum(1 << (15 - l) for l in lengths if l)


class TestCodeLengths(unittest.TestCase):

    def test_single_symbol_gets_length_one(self):
        f = [0] * 256
        f[65] = 1000
        lens = huffman.code_lengths(f)
        self.assertEqual(lens[65], 1)
        self.assertEqual(sum(1 for l in lens if l), 1)

    def test_two_symbols(self):
        f = [0] * 256
        f[0], f[1] = 3, 5
        self.assertEqual(huffman.code_lengths(f)[:2], [1, 1])

    def test_classic_three(self):
        # 5,2,1 → 1,2,2 (크래프트 합이 정확히 1)
        f = [0] * 256
        f[0], f[1], f[2] = 5, 2, 1
        lens = huffman.code_lengths(f)
        self.assertEqual(lens[:3], [1, 2, 2])
        self.assertEqual(kraft(lens), 1 << 15)

    def test_kraft_equality_on_real_data(self):
        data = bytes((i * 37 + 11) & 0xFF for i in range(5000))
        lens = huffman.code_lengths(freqs_of(data))
        self.assertEqual(kraft(lens), 1 << 15)

    def test_length_limit_is_respected(self):
        # 피보나치 빈도는 길이를 제한 없이 늘린다 — 20기호면 19비트까지
        f = [0] * 256
        a, b = 1, 1
        for i in range(24):
            f[i] = a
            a, b = b, a + b
        lens = huffman.code_lengths(f, limit=15)
        self.assertLessEqual(max(lens), 15)
        self.assertEqual(kraft(lens), 1 << 15)

    def test_is_optimal_for_small_case(self):
        # 가중 평균 길이가 이론상 최적과 같아야 한다
        f = [0] * 256
        for i, v in enumerate((8, 4, 2, 1, 1)):
            f[i] = v
        lens = huffman.code_lengths(f)
        cost = sum(f[i] * lens[i] for i in range(256))
        self.assertEqual(cost, 8 * 1 + 4 * 2 + 2 * 3 + 1 * 4 + 1 * 4)

    def test_deterministic_tie_breaking(self):
        # 같은 빈도가 잔뜩이면 동점 처리가 전부다. 같은 입력 → 같은
        # 길이.
        f = [0] * 256
        for i in range(7):
            f[i] = 1
        lens = huffman.code_lengths(f)
        # 기호 일곱이 모두 같은 빈도면 하나만 2비트, 나머지 여섯이
        # 3비트다 (5개가 3비트고 2개가 2비트면 크래프트 합이 1.125 라
        # 부호가 안 된다). 어느 하나가 짧아지는지는 순전히 동점 규칙이
        # 정한다.
        self.assertEqual(lens[:7], [3, 3, 3, 3, 3, 3, 2])
        self.assertEqual(kraft(lens), 1 << 15)
        self.assertEqual(huffman.code_lengths(f), lens)

    def test_too_many_symbols_for_limit(self):
        f = [1] * 256
        with self.assertRaises(ValueError):
            huffman.code_lengths(f, limit=7)


class TestCanonicalCodes(unittest.TestCase):

    def test_rfc1951_example(self):
        # RFC 1951 §3.2.2 의 예: 기호 A..H 의 길이 3,3,3,3,3,2,4,4
        lens = [3, 3, 3, 3, 3, 2, 4, 4] + [0] * 248
        codes = huffman.canonical_codes(lens)
        want = {0: 0b010, 1: 0b011, 2: 0b100, 3: 0b101, 4: 0b110,
                5: 0b00, 6: 0b1110, 7: 0b1111}
        for sym, code in want.items():
            self.assertEqual(codes[sym], code, sym)

    def test_ordered_by_length_then_symbol(self):
        lens = [0] * 256
        lens[9], lens[3], lens[200] = 2, 2, 1
        codes = huffman.canonical_codes(lens)
        self.assertEqual(codes[200], 0b0)
        self.assertEqual(codes[3], 0b10)
        self.assertEqual(codes[9], 0b11)


class TestGoldenCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(huffman.encode(b''), b'\x00')

    def test_header_is_128_bytes_of_nibbles(self):
        out = huffman.encode(b'A' * 16)
        self.assertEqual(out[0], 16)
        table = out[1:129]
        self.assertEqual(len(table), 128)
        # 65 = 0x41 은 홀수이므로 낮은 니블에 들어간다
        self.assertEqual(table[65 // 2] & 0x0F, 1)
        self.assertEqual(sum(1 for i in range(256)
                             if huffman.nibble(table, i)), 1)

    def test_single_symbol_body_is_n_zero_bits(self):
        out = huffman.encode(b'\x00' * 64)
        self.assertEqual(len(out), 1 + 128 + 8)
        self.assertEqual(out[129:], b'\x00' * 8)

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'\x00' * 1000, bytes(range(256)),
                 b'hello world' * 100,
                 bytes((i * 37 + 11) & 0xFF for i in range(5000))]
        for src in cases:
            self.assertEqual(huffman.decode(huffman.encode(src)), src,
                             src[:8])

    def test_beats_raw_on_skewed_data(self):
        src = b'a' * 900 + b'b' * 90 + b'c' * 10
        self.assertLess(len(huffman.encode(src)), len(src))

    def test_truncated_raises(self):
        out = huffman.encode(b'hello world' * 10)
        with self.assertRaises(ValueError):
            huffman.decode(out[:100])

    def test_oversubscribed_table_raises(self):
        # 길이 1 짜리 기호 셋 — 크래프트 합이 1 을 넘는다
        table = bytearray(128)
        for sym in (0, 1, 2):
            hi = sym % 2 == 0
            i = sym // 2
            table[i] |= (1 << 4) if hi else 1
        bad = b'\x04' + bytes(table) + b'\x00'
        with self.assertRaises(ValueError):
            huffman.decode(bad)


if __name__ == '__main__':
    unittest.main()
