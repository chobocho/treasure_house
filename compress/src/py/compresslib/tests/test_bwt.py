# -*- coding: utf-8 -*-
"""bwt 시험 — SPEC §9.

BWT 는 한 바이트도 줄이지 않는다. 자리만 바꾼다. 그런데 그 자리 바꾸기가
"같은 글자를 몰아 놓는" 성질을 가져서, 뒤에 MTF·0런·허프만을 붙이면
bzip2 가 된다. 10부가 통째로 이 이야기다.

시험이 볼 것 둘: 교과서 예제(banana)의 L 열과 primary 가 정확한가,
그리고 모든 회전이 똑같은 입력(zeros)에서 동점 규칙이 안 흔들리는가.
"""
import unittest

from compresslib import bwt


class TestForward(unittest.TestCase):

    def test_banana(self):
        # 회전을 사전순으로 세우면
        #   abanan / anaban / ananab / banana / nabana / nanaba
        # 마지막 글자를 모은 것이 L, 원래 문장이 선 자리가 primary
        L, primary = bwt.transform_block(b'banana')
        self.assertEqual(L, b'nnbaaa')
        self.assertEqual(primary, 3)

    def test_single_byte(self):
        L, primary = bwt.transform_block(b'A')
        self.assertEqual((L, primary), (b'A', 0))

    def test_all_equal_rotations(self):
        # 모든 회전이 같아 배가 늘리기로는 절대 안 갈린다.
        # 동점은 시작 위치 오름차순 — 그래서 primary 가 0 이다.
        L, primary = bwt.transform_block(b'\x00' * 64)
        self.assertEqual(L, b'\x00' * 64)
        self.assertEqual(primary, 0)

    def test_groups_equal_bytes(self):
        # BWT 의 존재 이유: 같은 글자가 몰린다
        src = b'the quick brown fox ' * 50
        L, _ = bwt.transform_block(src)
        runs = sum(1 for i in range(1, len(L)) if L[i] != L[i - 1])
        plain = sum(1 for i in range(1, len(src))
                    if src[i] != src[i - 1])
        self.assertLess(runs, plain // 4)


class TestInverse(unittest.TestCase):

    def test_banana(self):
        self.assertEqual(bwt.inverse_block(b'nnbaaa', 3), b'banana')

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'banana', b'\x00' * 1000,
                 bytes(range(256)), b'ab' * 1000,
                 bytes((i * 37 + 11) & 0xFF for i in range(5000))]
        for src in cases:
            L, p = bwt.transform_block(src)
            self.assertEqual(bwt.inverse_block(L, p), src, src[:8])

    def test_bad_primary_raises(self):
        with self.assertRaises(ValueError):
            bwt.inverse_block(b'nnbaaa', 99)


class TestGoldenCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(bwt.encode(b''), b'\x00')

    def test_size_is_length_plus_four_per_block(self):
        for n, blocks in ((1, 1), (65536, 1), (65537, 2), (200000, 4)):
            src = bytes((i * 13) & 0xFF for i in range(n))
            out = bwt.encode(src)
            from compresslib import varint
            head = len(varint.put(n))
            self.assertEqual(len(out), head + n + 4 * blocks, n)

    def test_round_trip_across_block_boundary(self):
        for n in (65535, 65536, 65537, 131072, 131073):
            src = bytes((i * 37 + 11) & 0xFF for i in range(n))
            self.assertEqual(bwt.decode(bwt.encode(src)), src, n)

    def test_truncated_raises(self):
        out = bwt.encode(b'hello world' * 10)
        with self.assertRaises(ValueError):
            bwt.decode(out[:8])


class TestPipeline(unittest.TestCase):
    """BWT → MTF → 0런 → 허프만. bzip2 의 뼈대다."""

    def test_bwt_helps_mtf_and_huffman(self):
        from compresslib import huffman, mtf
        src = b'the quick brown fox jumps over the lazy dog ' * 100
        plain = len(huffman.encode(mtf.transform(src)))
        L, _p = bwt.transform_block(src)
        through_bwt = len(huffman.encode(mtf.transform(L)))
        self.assertLess(through_bwt, plain // 2)


if __name__ == '__main__':
    unittest.main()
