# -*- coding: utf-8 -*-
"""deflate 시험 — SPEC §10.

이 모듈만 우리가 만든 형식이 아니다. 그래서 시험도 두 갈래다.
  · 우리끼리의 왕복 — 골든 벡터가 걸리는 자리
  · **진짜 도구와의 상호운용** — 이쪽이 훨씬 강한 증거다.
    파이썬 표준 zlib 이 우리 스트림을 풀어야 하고, 우리 inflate 는
    zlib 이 레벨 0~9 로 만든 스트림을 전부 풀어야 한다.

바이트가 같아지는지는 보지 않는다. 우리 부호기는 zlib 보다 단순한 선택을
하므로 같아질 수 없고, 같다고 주장하는 순간 거짓말이 된다 (§10.9).
"""
import unittest
import zlib

from compresslib import checksums, containers, deflate


class TestChecksums(unittest.TestCase):

    def test_adler32_matches_zlib(self):
        for src in (b'', b'a', b'hello world', bytes(range(256)) * 40):
            self.assertEqual(checksums.adler32(src),
                             zlib.adler32(src), src[:8])

    def test_crc32_matches_zlib(self):
        for src in (b'', b'a', b'hello world', bytes(range(256)) * 40):
            self.assertEqual(checksums.crc32(src),
                             zlib.crc32(src), src[:8])

    def test_adler32_modulus_over_5552_bytes(self):
        src = b'\xff' * 100000
        self.assertEqual(checksums.adler32(src), zlib.adler32(src))


class TestRawDeflate(unittest.TestCase):

    def test_empty_is_03_00(self):
        self.assertEqual(deflate.deflate_raw(b''), b'\x03\x00')

    def test_empty_round_trip(self):
        self.assertEqual(deflate.inflate_raw(b'\x03\x00'), b'')

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'\x00' * 100000,
                 bytes(range(256)), b'hello world ' * 2000,
                 bytes((i * 37 + 11) & 0xFF for i in range(50000)),
                 b'ab' * 40000]
        for src in cases:
            got = deflate.inflate_raw(deflate.deflate_raw(src))
            self.assertEqual(got, src, src[:8])

    def test_stored_block_for_incompressible(self):
        # 난수 같은 입력에서는 stored 가 이긴다 — 그때는 원본보다
        # 다섯 바이트쯤만 커진다
        src = bytes((i * 251 + 97) & 0xFF for i in range(4096))
        out = deflate.deflate_raw(src)
        self.assertLess(len(out), len(src) + 16)
        self.assertEqual(deflate.inflate_raw(out), src)

    def test_shrinks_repetitive(self):
        src = b'the quick brown fox ' * 3000
        self.assertLess(len(deflate.deflate_raw(src)), len(src) // 50)

    def test_crosses_block_boundary(self):
        for n in (65535, 65536, 65537, 200000):
            src = bytes((i * 37 + 11) & 0xFF for i in range(n))
            self.assertEqual(
                deflate.inflate_raw(deflate.deflate_raw(src)), src, n)


class TestInterop(unittest.TestCase):
    """진짜 zlib 과 양방향. 이게 이 모듈의 진짜 시험이다."""

    CASES = [b'', b'A', b'hello world ' * 500, b'\x00' * 100000,
             bytes((i * 37 + 11) & 0xFF for i in range(50000))]

    def test_zlib_reads_ours(self):
        for src in self.CASES:
            raw = deflate.deflate_raw(src)
            self.assertEqual(zlib.decompress(raw, -15), src, src[:8])

    def test_we_read_zlib_at_every_level(self):
        for level in range(10):
            for src in self.CASES:
                co = zlib.compressobj(level, zlib.DEFLATED, -15)
                raw = co.compress(src) + co.flush()
                self.assertEqual(deflate.inflate_raw(raw), src,
                                 (level, src[:8]))

    def test_zlib_container_both_ways(self):
        for src in self.CASES:
            ours = containers.zlib_compress(src)
            self.assertEqual(zlib.decompress(ours), src)
            self.assertEqual(containers.zlib_decompress(
                zlib.compress(src, 9)), src)

    def test_gzip_container_both_ways(self):
        import gzip as gz
        for src in self.CASES:
            ours = containers.gzip_compress(src)
            self.assertEqual(gz.decompress(ours), src)
            self.assertEqual(containers.gzip_decompress(
                gz.compress(src, 9, mtime=0)), src)

    def test_gzip_header_is_reproducible(self):
        # MTIME 0, OS 255 — 두 번 돌려 같은 바이트여야 make record 가
        # 산다
        a = containers.gzip_compress(b'hello')
        b = containers.gzip_compress(b'hello')
        self.assertEqual(a, b)
        self.assertEqual(a[:10],
                         b'\x1f\x8b\x08\x00' + b'\x00' * 5 + b'\xff')


class TestErrors(unittest.TestCase):

    def test_btype_11_raises(self):
        with self.assertRaises(ValueError):
            deflate.inflate_raw(b'\x07\x00')

    def test_nlen_mismatch_raises(self):
        # BFINAL=1, BTYPE=00, 정렬, LEN=1, NLEN 틀림, 바이트 하나
        bad = bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x41])
        with self.assertRaises(ValueError):
            deflate.inflate_raw(bad)

    def test_distance_too_far_raises(self):
        # 고정 블록에서 길이 3, 거리 100 을 첫 토큰으로
        from compresslib import bitio
        w = bitio.LsbWriter()
        w.write_bits(1, 1)
        w.write_bits(1, 2)
        w.write_code(1, 7)                   # 257 — 고정표에서 7비트
        w.write_code(11, 5)                  # 거리 부호 11 → 49..64
        w.write_bits(0, 4)
        w.write_code(0, 7)                   # EOB
        w.flush()
        with self.assertRaises(ValueError):
            deflate.inflate_raw(w.bytes())

    def test_truncated_raises(self):
        raw = deflate.deflate_raw(b'hello world ' * 200)
        with self.assertRaises(ValueError):
            deflate.inflate_raw(raw[:5])

    def test_bad_zlib_header_raises(self):
        with self.assertRaises(ValueError):
            containers.zlib_decompress(b'\x00\x00\x03\x00')

    def test_bad_adler_raises(self):
        good = bytearray(containers.zlib_compress(b'hello'))
        good[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            containers.zlib_decompress(bytes(good))

    def test_bad_gzip_crc_raises(self):
        good = bytearray(containers.gzip_compress(b'hello'))
        good[-5] ^= 0xFF
        with self.assertRaises(ValueError):
            containers.gzip_decompress(bytes(good))


class TestGoldenCodec(unittest.TestCase):

    def test_encode_is_raw_deflate(self):
        src = b'hello world ' * 100
        self.assertEqual(deflate.encode(src), deflate.deflate_raw(src))

    def test_round_trip(self):
        for src in (b'', b'A', b'\x00' * 5000, bytes(range(256))):
            self.assertEqual(deflate.decode(deflate.encode(src)), src)


if __name__ == '__main__':
    unittest.main()
