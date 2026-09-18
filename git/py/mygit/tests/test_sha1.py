# -*- coding: utf-8 -*-
"""sha1 의 시험 — SPEC.md §2 · 부록 A 1단계.

기준은 golden/sha1.tsv 100줄이다. sha1 칸은 coreutils sha1sum 이, blob
칸은 진짜 git hash-object 가 낸 값이다. 표준 라이브러리 hashlib 은
답을 맞춰 보는 두 번째 증인으로만 쓴다 — 구현이 그것을 부르면 이
시험은 아무것도 증명하지 않는다(SPEC.md §2 첫 문단).
"""
import hashlib
import unittest

from mygit import sha1
from mygit.tests import golden

VECTORS = golden.tsv('sha1.tsv')


class TestVectors(unittest.TestCase):
    def test_s2_hundred_vectors_match_sha1sum(self):
        self.assertEqual(len(VECTORS), 100)
        for row in VECTORS:
            data = golden.make(row['recipe'])
            self.assertEqual(len(data), int(row['len']), row['name'])
            self.assertEqual(sha1.sha1_hex(data), row['sha1'],
                             row['name'])

    def test_s2_raw_digest_is_twenty_bytes(self):
        d = sha1.sha1(b'abc')
        self.assertEqual(len(d), 20)
        self.assertEqual(d, hashlib.sha1(b'abc').digest())

    def test_s2_padding_boundaries_agree_with_hashlib(self):
        # 55 바이트까지는 덧붙임이 한 블록에 들어가고 56 부터 넘친다.
        for n in range(0, 200):
            data = bytes((i * 7) % 256 for i in range(n))
            self.assertEqual(sha1.sha1(data),
                             hashlib.sha1(data).digest(), n)


class TestStreaming(unittest.TestCase):
    def test_s2_update_in_odd_chunks_equals_one_shot(self):
        data = golden.make('counter:100000')
        for size in (1, 3, 63, 64, 65, 1000, 99999):
            h = sha1.Sha1()
            for k in range(0, len(data), size):
                h.update(data[k:k + size])
            self.assertEqual(h.digest(), sha1.sha1(data), size)

    def test_s2_digest_twice_is_stable(self):
        h = sha1.Sha1()
        h.update(b'git')
        self.assertEqual(h.digest(), h.digest())


class TestBlobColumn(unittest.TestCase):
    def test_s2_header_plus_body_is_the_blob_name(self):
        # blob 이름 = SHA-1("blob <크기>\0" + 몸) — 머리를 붙이는 일은
        # §4 의 몫이지만, 여기서 숫자가 맞으면 SHA-1 쪽은 끝난 것이다.
        for row in VECTORS:
            data = golden.make(row['recipe'])
            head = b'blob %d\0' % len(data)
            self.assertEqual(sha1.sha1_hex(head + data), row['blob'],
                             row['name'])


if __name__ == '__main__':
    unittest.main()
