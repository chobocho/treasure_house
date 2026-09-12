# -*- coding: utf-8 -*-
"""lossy 시험 — SPEC §19.

이 모듈에서 왕복하는 것은 PNG 쪽 하나뿐이다. 나머지는 일부러 버리므로
"같은가" 를 물을 수 없고 **얼마나 다른가** 를 물어야 한다. 그래서 PSNR·SNR
이 시험에 들어간다 — 품질을 올렸는데 PSNR 이 안 오르면 그건 버그다.
실제로 그렇게 잡았다(품질 100 에서 EOB 바이트를 안 먹던 버그).
"""
import math
import unittest

from compresslib import lossy


def _test_image(w=64, h=64):
    px = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            v = (x * 3 + y * 2) % 256
            if (x - w // 2) ** 2 + (y - h // 2) ** 2 < 400:
                v = (v + 128) % 256
            px[y * w + x] = v
    return bytes(px)


def psnr(a, b):
    mse = sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)
    return 99.0 if mse == 0 else 10 * math.log10(255 * 255 / mse)


class TestQuantise(unittest.TestCase):

    def test_uniform_rounds_half_away(self):
        self.assertEqual(lossy.quantise(5, 2), 3)
        self.assertEqual(lossy.quantise(-5, 2), -3)
        self.assertEqual(lossy.quantise(4, 2), 2)
        self.assertEqual(lossy.quantise(1, 4), 0)

    def test_dead_zone_truncates_toward_zero(self):
        # (-q, q) 가 통째로 0 이 된다 — 그림이 원하는 모양이다
        for v in range(-3, 4):
            self.assertEqual(lossy.quantise(v, 4, dead_zone=True), 0)
        self.assertEqual(lossy.quantise(4, 4, dead_zone=True), 1)
        self.assertEqual(lossy.quantise(-4, 4, dead_zone=True), -1)

    def test_dequantise(self):
        self.assertEqual(lossy.dequantise(3, 7), 21)


class TestDct(unittest.TestCase):

    def test_round_trip_error_is_at_most_two(self):
        # DCT 자체는 손실이 아니다. 정수 근사의 반올림만 남는다 (§19.2).
        worst = 0
        for seed in range(50):
            block = [((i * 37 + seed * 11) % 256) - 128 for i in range(64)]
            back = lossy.idct8(lossy.fdct8(block))
            worst = max(worst, max(abs(back[i] - block[i])
                                   for i in range(64)))
        self.assertLessEqual(worst, 2)

    def test_flat_block_has_only_dc(self):
        block = [50] * 64
        coef = lossy.fdct8(block)
        self.assertNotEqual(coef[0], 0)
        self.assertTrue(all(c == 0 for c in coef[1:]))

    def test_zigzag_is_the_jpeg_order(self):
        self.assertEqual(lossy.ZIGZAG[:10],
                         [0, 1, 8, 16, 9, 2, 3, 10, 17, 24])
        self.assertEqual(sorted(lossy.ZIGZAG), list(range(64)))


class TestJpegLite(unittest.TestCase):

    def test_quality_raises_psnr(self):
        # 품질을 올렸는데 PSNR 이 안 오르면 버그다. 품질 100 에서 EOB
        # 바이트를 안 먹던 버그가 바로 이 시험에서 잡혔다.
        src = _test_image()
        last = -1.0
        for q in (10, 30, 50, 75, 90, 100):
            enc = lossy.jpeglite_encode(src, 64, 64, q)
            got, w, h = lossy.jpeglite_decode(enc)
            self.assertEqual((w, h), (64, 64))
            value = psnr(src, got)
            self.assertGreater(value, last, q)
            last = value
        self.assertGreater(last, 45.0)

    def test_quality_raises_size(self):
        src = _test_image()
        sizes = [len(lossy.jpeglite_encode(src, 64, 64, q))
                 for q in (10, 50, 90)]
        self.assertLess(sizes[0], sizes[1])
        self.assertLess(sizes[1], sizes[2])

    def test_non_multiple_of_eight(self):
        # 가장자리는 복제로 채운다 (§19.4)
        src = _test_image(37, 21)
        enc = lossy.jpeglite_encode(src, 37, 21, 80)
        got, w, h = lossy.jpeglite_decode(enc)
        self.assertEqual((w, h, len(got)), (37, 21, 37 * 21))
        self.assertGreater(psnr(src, got), 25.0)

    def test_bad_magic_raises(self):
        with self.assertRaises(ValueError):
            lossy.jpeglite_decode(b'XXX' + b'\x00' * 10)

    def test_bad_quality_raises(self):
        with self.assertRaises(ValueError):
            lossy.jpeglite_encode(_test_image(8, 8), 8, 8, 0)


class TestPngFilters(unittest.TestCase):

    def test_paeth(self):
        # p = a + b - c 에 가장 가까운 것을 고른다. 동점은 a, 그다음 b.
        self.assertEqual(lossy.paeth(10, 20, 15), 15)   # p=15, c 가 정확
        self.assertEqual(lossy.paeth(10, 20, 30), 10)   # p=0, a 가 가깝다
        self.assertEqual(lossy.paeth(1, 2, 0), 2)       # p=3, b 가 가깝다
        self.assertEqual(lossy.paeth(5, 5, 5), 5)
        self.assertEqual(lossy.paeth(0, 0, 0), 0)

    def test_filter_round_trip(self):
        for width in (1, 3, 16, 256):
            data = bytes((i * 37 + 11) & 0xFF for i in range(1000))
            got = lossy.png_unfilter(lossy.png_filter(data, width), width)
            self.assertEqual(got, data, width)

    def test_up_filter_flattens_repeated_rows(self):
        # 같은 줄이 되풀이되면 Up 필터가 전부 0 으로 만든다
        row = bytes(range(64))
        data = row * 10
        filtered = lossy.png_filter(data, 64)
        self.assertTrue(all(b == 0 for b in filtered[65 + 1:129]))

    def test_unknown_filter_raises(self):
        with self.assertRaises(ValueError):
            lossy.png_unfilter(b'\x09' + b'\x00' * 8, 8)


class TestGoldenCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(lossy.encode(b''), b'\x00')

    def test_round_trip_is_exact(self):
        # PNG 는 손실 형식이 아니다 — 이 모듈에서 유일하게 왕복한다.
        cases = [b'', b'A', bytes(range(256)) * 3, b'\x00' * 5000,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000))]
        for src in cases:
            self.assertEqual(lossy.decode(lossy.encode(src)), src,
                             len(src))

    def test_truncated_raises(self):
        out = lossy.encode(b'hello world ' * 50)
        with self.assertRaises(ValueError):
            lossy.decode(out[:5])


class TestAdpcm(unittest.TestCase):

    def test_four_to_one(self):
        samples = [int(12000 * math.sin(2 * math.pi * 440 * t / 8000))
                   for t in range(8000)]
        enc = lossy.adpcm_encode(samples)
        self.assertEqual(len(enc), 4000)        # 16비트 → 4비트

    def test_snr_on_a_tone(self):
        samples = [int(12000 * math.sin(2 * math.pi * 440 * t / 8000))
                   for t in range(8000)]
        dec = lossy.adpcm_decode(lossy.adpcm_encode(samples), len(samples))
        sig = sum(v * v for v in samples)
        noise = sum((a - b) ** 2 for a, b in zip(samples, dec))
        self.assertGreater(10 * math.log10(sig / noise), 20.0)

    def test_odd_sample_count(self):
        samples = [100, -200, 300]
        enc = lossy.adpcm_encode(samples)
        self.assertEqual(len(enc), 2)
        self.assertEqual(len(lossy.adpcm_decode(enc, 3)), 3)

    def test_silence_stays_silent(self):
        dec = lossy.adpcm_decode(lossy.adpcm_encode([0] * 100), 100)
        self.assertTrue(all(abs(v) < 20 for v in dec))


if __name__ == '__main__':
    unittest.main()
