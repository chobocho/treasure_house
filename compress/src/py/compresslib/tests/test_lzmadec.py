# -*- coding: utf-8 -*-
"""lzmadec 시험 — SPEC §16.

골든 벡터가 없다. 우리가 만들지 않은 파일 — 파이썬 lzma 와 진짜 xz
가 만든 것 — 을 푸는 것이 시험이다. 명령줄 대조는 run_decoders.py
가 맡고, 여기서는 헤더 해석과 거절해야 할 것들을 본다.
"""
import lzma
import unittest

from compresslib import lzmadec


class TestHeader(unittest.TestCase):

    def test_default_properties(self):
        # lc=3, lp=0, pb=2 → (2*5+0)*9+3 = 93 = 0x5D
        raw = lzma.compress(b'hello', format=lzma.FORMAT_ALONE)
        self.assertEqual(raw[0], 0x5D)
        lc, lp, pb, _dict, _size, pos = lzmadec.parse_header(raw)
        self.assertEqual((lc, lp, pb, pos), (3, 0, 2, 13))

    def test_custom_properties(self):
        raw = lzma.compress(
            b'hello world ' * 50, format=lzma.FORMAT_ALONE,
            filters=[{'id': lzma.FILTER_LZMA1, 'lc': 0,
                      'lp': 2, 'pb': 0}])
        lc, lp, pb, _d, _s, _p = lzmadec.parse_header(raw)
        self.assertEqual((lc, lp, pb), (0, 2, 0))
        self.assertEqual(lzmadec.decode(raw), b'hello world ' * 50)

    def test_short_header_raises(self):
        with self.assertRaises(ValueError):
            lzmadec.parse_header(b'\x5d' * 5)

    def test_bad_properties_raises(self):
        bad = bytearray(lzma.compress(b'hi', format=lzma.FORMAT_ALONE))
        bad[0] = 9 * 5 * 5
        with self.assertRaises(ValueError):
            lzmadec.decode(bytes(bad))


class TestDecode(unittest.TestCase):

    CASES = [b'', b'A', b'AB', b'\x00' * 5000, bytes(range(256)),
             b'hello world ' * 300, b'a' * 300000, b'ab' * 20000,
             bytes((i * 37 + 11) & 0xFF for i in range(50000)),
             bytes((i * 251 + 97) & 0xFF for i in range(4096))]

    def test_matches_python_lzma(self):
        for src in self.CASES:
            raw = lzma.compress(src, format=lzma.FORMAT_ALONE)
            self.assertEqual(lzmadec.decode(raw), src, src[:8])

    def test_every_preset(self):
        src = b'the quick brown fox ' * 200
        for preset in (0, 1, 6, 9):
            raw = lzma.compress(src, format=lzma.FORMAT_ALONE,
                                preset=preset)
            self.assertEqual(lzmadec.decode(raw), src, preset)

    def test_unknown_size_falls_back_to_end_marker(self):
        # 크기 칸을 "모름" 으로 바꿔도 풀린다 — liblzma 가 크기를
        # 적으면서
        # 끝 표시도 같이 붙이기 때문이다. 두 가지 끝맺음을 다 받는다는
        # §16.2 의 약속이 여기서 확인된다.
        src = b'hello world ' * 100
        raw = bytearray(lzma.compress(src, format=lzma.FORMAT_ALONE))
        raw[5:13] = b'\xff' * 8
        self.assertEqual(lzmadec.decode(bytes(raw)), src)

    def test_truncated_raises(self):
        raw = lzma.compress(b'hello world ' * 200,
                            format=lzma.FORMAT_ALONE)
        with self.assertRaises(ValueError):
            lzmadec.decode(raw[:30])

    def test_size_mismatch_raises(self):
        raw = bytearray(lzma.compress(b'hello',
                                     format=lzma.FORMAT_ALONE))
        raw[5] = 99
        with self.assertRaises(ValueError):
            lzmadec.decode(bytes(raw))

    def test_beats_deflate_on_structure(self):
        # 지난 거리 넷을 기억하는 값이 여기서 난다 (§16.4)
        import io as _io
        import os
        from compresslib import deflate
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.abspath(
            os.path.join(here, '..', '..', '..', '..'))
        with _io.open(os.path.join(base, 'corpus', 'mixed_1m.bin'),
                      'rb') as f:
            src = f.read()
        raw = lzma.compress(src, format=lzma.FORMAT_ALONE, preset=9)
        self.assertLess(len(raw), len(deflate.encode(src)))
        self.assertEqual(lzmadec.decode(raw), src)


if __name__ == '__main__':
    unittest.main()
