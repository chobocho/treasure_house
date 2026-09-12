# -*- coding: utf-8 -*-
"""ppm 시험 — SPEC §17.

PPM 의 고전 버그는 **모두 배제된 문맥** 이다. 탈출이 확실하니 비트가 0인데,
부호기가 탈출을 적고 복호기는 안 읽으면 그 자리에서 어긋난다. 작은 입력
으로는 그 상황이 안 생기므로, 그 상황을 일부러 만드는 입력을 넣어 둔다.
"""
import unittest

from compresslib import ppm, rangecoder


class TestFrequencyCoder(unittest.TestCase):
    """PPM 이 쓰려고 레인지 코더에 붙인 두 입구 (SPEC §17.2)."""

    def test_round_trip(self):
        freqs = [5, 3, 2, 1, 1]
        tot = sum(freqs)
        cum = [sum(freqs[:i]) for i in range(len(freqs))]
        syms = [(i * 7 + 3) % 5 for i in range(3000)]
        enc = rangecoder.Encoder()
        for s in syms:
            enc.encode_freq(cum[s], freqs[s], tot)
        enc.flush()
        dec = rangecoder.Decoder(enc.bytes(), 0)
        got = []
        for _ in syms:
            v = dec.decode_freq(tot)
            s = max(i for i in range(len(freqs)) if cum[i] <= v)
            dec.decode_update(cum[s], freqs[s], tot)
            got.append(s)
        self.assertEqual(got, syms)

    def test_mixes_with_the_bit_coder(self):
        # 같은 스트림에 비트와 빈도를 섞어 써도 된다 (§17.2)
        probs = [rangecoder.PROB_INIT]
        enc = rangecoder.Encoder()
        enc.encode_bit(probs, 0, 1)
        enc.encode_freq(2, 3, 10)
        enc.encode_bit(probs, 0, 0)
        enc.flush()
        probs2 = [rangecoder.PROB_INIT]
        dec = rangecoder.Decoder(enc.bytes(), 0)
        self.assertEqual(dec.decode_bit(probs2, 0), 1)
        self.assertEqual(dec.decode_freq(10) // 1, 2)
        dec.decode_update(2, 3, 10)
        self.assertEqual(dec.decode_bit(probs2, 0), 0)


class TestModel(unittest.TestCase):

    def test_rescale_keeps_counts_positive(self):
        m = ppm.Model()
        for _ in range(ppm.MAX_TOTAL + 100):
            m.update((), 65)
        table = m.counts(())
        self.assertTrue(all(v >= 1 for v in table.values()))
        self.assertLess(sum(table.values()), ppm.MAX_TOTAL)

    def test_context_keys_shrink_with_history(self):
        self.assertEqual(ppm._context_keys([]), [()])
        self.assertEqual(ppm._context_keys([1]), [(1,), ()])
        self.assertEqual(ppm._context_keys([1, 2]), [(1, 2), (2,), ()])


class TestCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(ppm.encode(b''), b'\x00')

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'\x00' * 5000, bytes(range(256)),
                 b'hello world ' * 300, b'ab' * 2000,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000)),
                 bytes((i * 251 + 97) & 0xFF for i in range(4096))]
        for src in cases:
            self.assertEqual(ppm.decode(ppm.encode(src)), src, src[:8])

    def test_all_excluded_context(self):
        # 2차가 알던 기호가 1차에도 전부 있는 자리를 만든다 — 1차는
        # 그때 아무 정보도 못 주므로 건너뛰어야 한다 (§17.3).
        src = (b'abcabcabc' * 50 + b'abab' * 50 + b'aaaa' * 50
               + bytes(range(256)))
        self.assertEqual(ppm.decode(ppm.encode(src)), src)

    def test_beats_order0(self):
        # 문맥을 보는 값이 여기서 난다
        from compresslib import rangecoder as rc
        src = b'the quick brown fox jumps over the lazy dog ' * 200
        self.assertLess(len(ppm.encode(src)), len(rc.encode(src)) // 2)

    def test_sees_through_a_linear_sequence(self):
        # (i*251+97) & 0xFF 은 다른 코덱들에게는 난수처럼 보인다. PPM 은
        # 앞 두 바이트로 다음을 완전히 맞힌다 — 4096바이트가 400바이트
        # 아래로 간다. "난수처럼 보인다" 와 "난수다" 의 차이가 이것이다.
        src = bytes((i * 251 + 97) & 0xFF for i in range(4096))
        self.assertLess(len(ppm.encode(src)), 500)

    def test_grows_on_real_random(self):
        # 진짜 난수(코퍼스의 xorshift)에서는 커진다. 그게 정상이다.
        import io as _io
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.abspath(os.path.join(here, '..', '..', '..', '..'))
        with _io.open(os.path.join(base, 'corpus', 'random_64k.bin'),
                      'rb') as f:
            src = f.read()
        self.assertGreater(len(ppm.encode(src)), len(src))

    def test_truncated_raises(self):
        out = ppm.encode(b'hello world ' * 50)
        with self.assertRaises(ValueError):
            ppm.decode(out[:6])


if __name__ == '__main__':
    unittest.main()
