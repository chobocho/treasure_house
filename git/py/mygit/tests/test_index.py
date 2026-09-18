# -*- coding: utf-8 -*-
"""인덱스의 시험 — SPEC.md §7, 6단계 "인덱스 — 스테이징의 실체".

golden/index/ 의 세 파일은 진짜 git 이 쓴 인덱스다: 확장 없음(git add
직후), TREE 확장(git commit 뒤), 판 3(skip-worktree 가 켜진 항목).
plain.bin 은 plain.raw 의 stat 칸을 §7.3 으로 지운 것이다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import index
from mygit.tests import golden


def ls_stage():
    """golden/index/ls-stage.txt → [(모드, 이름, 단계, 경로 바이트)]."""
    out = []
    text = golden.read('index', 'ls-stage.txt').decode()
    for line in text.split('\n'):
        if not line:
            continue
        meta, path = line.split('\t', 1)
        mode, oid, stage = meta.split(' ')
        p = path.encode()
        if path.startswith('"'):
            p = golden.unescape_c(path[1:-1])
        out.append((int(mode, 8), oid, int(stage), p))
    return out


def summary(entries):
    return [(e.mode, e.oid, e.stage, e.path) for e in entries]


class TestReadGit(unittest.TestCase):
    def test_s7_1_plain(self):
        ents = index.parse_index(golden.read('index', 'plain.raw'))
        self.assertEqual(summary(ents), ls_stage())

    def test_s7_5_tree_extension_is_skipped(self):
        ents = index.parse_index(golden.read('index', 'tree-ext.raw'))
        self.assertEqual(summary(ents), ls_stage())

    def test_s7_1_version_3(self):
        ents = index.parse_index(golden.read('index', 'v3.raw'))
        self.assertEqual(summary(ents), ls_stage())
        skip = [e.path for e in ents if e.skip_worktree]
        self.assertEqual(skip, [b'run.sh'])

    def test_s7_5_bad_checksum(self):
        raw = bytearray(golden.read('index', 'plain.raw'))
        raw[-1] ^= 1
        golden.assert_git_error(self, index.parse_index, bytes(raw))


class TestWrite(unittest.TestCase):
    def test_s7_2_round_trip_is_byte_identical(self):
        raw = golden.read('index', 'plain.raw')
        self.assertEqual(index.serialize_index(index.parse_index(raw)),
                         raw)

    def test_s7_3_normalized_equals_golden(self):
        ents = index.parse_index(golden.read('index', 'plain.raw'))
        for e in ents:
            e.ctime_s = e.ctime_ns = e.mtime_s = e.mtime_ns = 0
            e.dev = e.ino = e.uid = e.gid = 0
        self.assertEqual(index.serialize_index(ents),
                         golden.read('index', 'plain.bin'))

    def test_s7_2_version_3_is_written_as_version_2(self):
        ents = index.parse_index(golden.read('index', 'v3.raw'))
        data = index.serialize_index(ents)
        self.assertEqual(data[4:8], b'\0\0\0\2')

    def test_s7_2_long_path_and_padding(self):
        for n in (1, 2, 7, 8, 9, 100, 4094, 4095, 4096, 5000):
            e = index.IndexEntry(b'd/' + b'x' * n, '1' * 40, 0o100644)
            data = index.serialize_index([e])
            # 항목 길이는 8의 배수, NUL 은 1‥8 개
            body = len(data) - 12 - 20
            self.assertEqual(body % 8, 0, n)
            self.assertTrue(1 <= body - 62 - len(e.path) <= 8, n)
            back = index.parse_index(data)
            self.assertEqual(back[0].path, e.path, n)

    def test_s7_1_sorted_by_path_bytes_then_stage(self):
        ents = [index.IndexEntry(p, '1' * 40, 0o100644, stage=s)
                for p, s in ((b'b', 0), (b'a/x', 0), (b'a-b', 0),
                             (b'c', 3), (b'c', 1), (b'c', 2))]
        back = index.parse_index(index.serialize_index(ents))
        self.assertEqual([(e.path, e.stage) for e in back],
                         [(b'a-b', 0), (b'a/x', 0), (b'b', 0),
                          (b'c', 1), (b'c', 2), (b'c', 3)])


class TestStat(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_s7_2_exec_bit_and_size(self):
        p = os.path.join(self.tmp, 'run.sh')
        with open(p, 'wb') as f:
            f.write(b'#!/bin/sh\n')
        os.chmod(p, 0o755)
        e = index.entry_from_stat(b'run.sh', p, '2' * 40)
        self.assertEqual((e.mode, e.size), (0o100755, 10))
        os.chmod(p, 0o644)
        e = index.entry_from_stat(b'run.sh', p, '2' * 40)
        self.assertEqual(e.mode, 0o100644)
        st = os.stat(p)
        self.assertEqual((e.mtime_s, e.mtime_ns),
                         (st.st_mtime_ns // 10 ** 9,
                          st.st_mtime_ns % 10 ** 9))

    def test_s7_4_write_and_read_back(self):
        g = os.path.join(self.tmp, '.git')
        os.makedirs(g)
        self.assertEqual(index.read_index(g), [])
        e = index.IndexEntry(b'a', '3' * 40, 0o100644)
        index.write_index(g, [e])
        self.assertEqual(summary(index.read_index(g)),
                         [(0o100644, '3' * 40, 0, b'a')])
        self.assertFalse(os.path.exists(os.path.join(g, 'index.lock')))


if __name__ == '__main__':
    unittest.main()
