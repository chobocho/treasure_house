# -*- coding: utf-8 -*-
"""bzip2dec 시험 — SPEC §15.

이 모듈에는 골든 벡터가 없다. 부호기가 없어서다. 대신 진짜 bzip2
만든 파일** 을 푼다 — 우리가 만들지 않은 입력이라 왕복 시험보다 훨씬 센
증거다. 여기서는 파이썬 표준 bz2 로 만든 파일을 쓰고, 진짜 명령줄
bzip2 와의 대조는 interop/ 가 맡는다.
"""
import bz2
import unittest

from compresslib import bzip2dec


class TestCrc(unittest.TestCase):
    """bzip2 의 CRC 는 gzip 의 것과 다르다 — 반사가 없다 (§15.6)."""

    def test_empty(self):
        self.assertEqual(bzip2dec.crc32_bzip2(b''), 0)

    def test_known_vectors(self):
        # 반사 없는 CRC-32/BZIP2 의 표준 시험값
        self.assertEqual(bzip2dec.crc32_bzip2(b'123456789'), 0xFC891918)

    def test_differs_from_gzip_crc(self):
        from compresslib import checksums
        data = b'hello world'
        self.assertNotEqual(bzip2dec.crc32_bzip2(data),
                            checksums.crc32(data))


class TestRle1(unittest.TestCase):

    def test_four_then_count(self):
        # 같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다
        self.assertEqual(bzip2dec.rle1_decode(b'AAAA\x00'), b'AAAA')
        self.assertEqual(bzip2dec.rle1_decode(b'AAAA\x03'), b'AAAAAAA')
        self.assertEqual(bzip2dec.rle1_decode(b'AAAA\xff'), b'A' * 259)

    def test_three_is_not_a_run(self):
        self.assertEqual(bzip2dec.rle1_decode(b'AAAB'), b'AAAB')

    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            bzip2dec.rle1_decode(b'AAAA')


class TestDecode(unittest.TestCase):

    CASES = [b'', b'A', b'AB', b'\x00' * 5000, bytes(range(256)),
             b'hello world ' * 300, b'a' * 300000,
             bytes((i * 37 + 11) & 0xFF for i in range(50000)),
             bytes((i * 251 + 97) & 0xFF for i in range(4096))]

    def test_matches_python_bz2(self):
        for src in self.CASES:
            for level in (1, 9):
                raw = bz2.compress(src, level)
                self.assertEqual(bzip2dec.decode(raw), src,
                                 (level, src[:8]))

    def test_multiple_blocks(self):
        # 레벨 1 은 블록이 100k 라 300k 입력이면 블록이 여럿이다
        src = bytes((i * 37 + 11) & 0xFF for i in range(300000))
        raw = bz2.compress(src, 1)
        self.assertEqual(bzip2dec.decode(raw), src)

    def test_bad_magic_raises(self):
        with self.assertRaises(ValueError):
            bzip2dec.decode(b'XYh9' + b'\x00' * 20)

    def test_bad_level_raises(self):
        with self.assertRaises(ValueError):
            bzip2dec.decode(b'BZh0' + b'\x00' * 20)

    def test_bad_crc_raises(self):
        raw = bytearray(bz2.compress(b'hello world', 9))
        raw[8] ^= 0xFF          # 블록 CRC 의 한 바이트를 뒤집는다
        with self.assertRaises(ValueError):
            bzip2dec.decode(bytes(raw))

    def test_truncated_raises(self):
        raw = bz2.compress(b'hello world ' * 100, 9)
        with self.assertRaises(ValueError):
            bzip2dec.decode(raw[:20])

    def test_beats_our_deflate_on_text(self):
        # bzip2 의 존재 이유 — 텍스트에서 DEFLATE 를 이긴다.
        # 코퍼스는 이 파일에서 상대 경로로 찾는다 — 시험을 어느
        # 디렉터리에서 돌리든 같아야 한다.
        import io as _io
        import os
        from compresslib import deflate
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.abspath(
            os.path.join(here, '..', '..', '..', '..'))
        with _io.open(os.path.join(base, 'corpus', 'english.txt'),
                      'rb') as f:
            src = f.read()
        self.assertLess(len(bz2.compress(src, 9)),
                        len(deflate.encode(src)))
        self.assertEqual(bzip2dec.decode(bz2.compress(src, 9)), src)


if __name__ == '__main__':
    unittest.main()
