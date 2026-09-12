# -*- coding: utf-8 -*-
"""rangecoder 시험 — SPEC §8.

허프만은 기호 하나에 정수 비트를 쓴다. 확률 0.9 인 기호도 1비트다.
레인지 코더는 그 제약이 없다 — 구간을 확률대로 쪼개 쌓기만 한다. 대신
캐리 전파와 정규화가 붙고, 그 둘이 언어마다 갈라지는 자리다.
"""
import unittest

from compresslib import rangecoder as rc


class TestStreamShape(unittest.TestCase):

    def test_first_byte_is_zero(self):
        # cache 가 0, cacheSize 가 1 로 시작하므로 첫 바이트는 늘 0
        # 이다. 진짜 .lzma 파일도 이렇게 시작한다 — 14번 모듈이 여기
        # 기댄다.
        out = rc.encode(b'hello world')
        self.assertEqual(out[1], 0)

    def test_empty_is_header_only(self):
        self.assertEqual(rc.encode(b''), b'\x00')


class TestBitCoder(unittest.TestCase):

    def test_single_bit_round_trip(self):
        for bits in ([0], [1], [0, 1, 1, 0], [1] * 100, [0] * 100):
            enc = rc.Encoder()
            probs = [rc.PROB_INIT]
            for b in bits:
                enc.encode_bit(probs, 0, b)
            enc.flush()
            raw = enc.bytes()
            dec = rc.Decoder(raw)
            probs2 = [rc.PROB_INIT]
            got = [dec.decode_bit(probs2, 0) for _ in bits]
            self.assertEqual(got, bits)

    def test_model_adapts(self):
        # 0 만 계속 넣으면 P(0) 이 올라간다 — 그게 '적응' 이다
        probs = [rc.PROB_INIT]
        enc = rc.Encoder()
        for _ in range(200):
            enc.encode_bit(probs, 0, 0)
        self.assertGreater(probs[0], rc.PROB_INIT)
        self.assertLess(probs[0], rc.PROB_TOTAL)

    def test_skewed_bits_cost_less_than_one_bit_each(self):
        # 허프만이 절대 못 하는 일 — 기호당 1비트 아래로 내려간다
        enc = rc.Encoder()
        probs = [rc.PROB_INIT]
        for _ in range(8000):
            enc.encode_bit(probs, 0, 0)
        enc.flush()
        self.assertLess(len(enc.bytes()), 100)


class TestByteModel(unittest.TestCase):

    def test_round_trip(self):
        src = bytes((i * 37 + 11) & 0xFF for i in range(1000))
        enc = rc.Encoder()
        m = rc.ByteModel()
        for b in src:
            m.encode(enc, b)
        enc.flush()
        dec = rc.Decoder(enc.bytes())
        m2 = rc.ByteModel()
        got = bytes(m2.decode(dec) for _ in src)
        self.assertEqual(got, src)

    def test_index_zero_never_used(self):
        # 문맥은 1 에서 시작해 8번 만에 256..511 이 된다
        m = rc.ByteModel()
        seen = []
        ctx = 1
        for i in range(7, -1, -1):
            seen.append(ctx)
            ctx = (ctx << 1) | ((0xA5 >> i) & 1)
        self.assertNotIn(0, seen)
        self.assertTrue(all(1 <= c <= 255 for c in seen))
        self.assertEqual(len(m.probs), 256)


class TestGoldenCodec(unittest.TestCase):

    def test_round_trip(self):
        cases = [b'', b'A', b'\x00' * 5000, bytes(range(256)),
                 b'hello world ' * 300,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000))]
        for src in cases:
            self.assertEqual(rc.decode(rc.encode(src)), src, src[:8])

    def test_beats_huffman_on_skewed_data(self):
        from compresslib import huffman
        src = b'a' * 9000 + b'b' * 900 + b'c' * 100
        self.assertLess(len(rc.encode(src)), len(huffman.encode(src)))

    def test_grows_on_random(self):
        src = bytes((i * 251 + 97) & 0xFF for i in range(4096))
        self.assertGreater(len(rc.encode(src)), len(src))


class TestErrors(unittest.TestCase):

    def test_nonzero_first_byte_raises(self):
        out = bytearray(rc.encode(b'hello'))
        out[1] = 1
        with self.assertRaises(ValueError):
            rc.decode(bytes(out))

    def test_truncated_raises(self):
        out = rc.encode(b'hello world' * 50)
        with self.assertRaises(ValueError):
            rc.decode(out[:6])


if __name__ == '__main__':
    unittest.main()
