# -*- coding: utf-8 -*-
"""blob — hash-object · cat-file 의 시험. SPEC.md §1 · §9, 3단계.

오라클은 golden/objects/ 의 blob 들(진짜 git 이 쓴 파일)과
golden/errors.tsv 의 오류 문장이다. 명령은 cli.run 으로 과정 안에서
부른다 — 새 파이썬을 띄우지 않아 빠르고, 출력 바이트를 그대로 본다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, zlib
from mygit.tests import golden

OBJS = golden.tsv('objects', 'objects.tsv')
ERRORS = {r['command']: r for r in golden.tsv('errors.tsv')}


def body_of(oid):
    raw = zlib.decompress(golden.read('objects', oid))
    return raw.partition(b'\0')[2]


class Sandbox(unittest.TestCase):
    """임시 디렉터리. with_repo 면 .git 뼈대를 손으로 만든다(init 은
    5단계의 일이라 여기서는 쓰지 않는다)."""

    with_repo = True

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'w')
        os.makedirs(self.root)
        if self.with_repo:
            g = os.path.join(self.root, '.git')
            for d in ('objects/pack', 'refs/heads', 'refs/tags'):
                os.makedirs(os.path.join(g, d))
            with open(os.path.join(g, 'HEAD'), 'w') as f:
                f.write('ref: refs/heads/main\n')
        # 위로 올라가다 이 덱의 저장소를 찾지 않게 (SPEC.md §1.1)
        self.env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp)

    def tearDown(self):
        for root, _d, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        shutil.rmtree(self.tmp)

    def mygit(self, *args, stdin=b''):
        return cli.run(list(args), cwd=self.root, env=self.env,
                       stdin=stdin)

    def put(self, name, data):
        with open(os.path.join(self.root, name), 'wb') as f:
            f.write(data)


class TestHashObject(Sandbox):
    def test_s9_every_golden_blob_has_its_git_name(self):
        n = 0
        for row in OBJS:
            if row['type'] != 'blob':
                continue
            self.put('f', body_of(row['id']))
            code, out, err = self.mygit('hash-object', 'f')
            self.assertEqual((code, out, err),
                             (0, row['id'].encode() + b'\n', b''))
            n += 1
        self.assertGreaterEqual(n, 3)

    def test_s9_stdin(self):
        code, out, _ = self.mygit('hash-object', '--stdin',
                                  stdin=b'hello\n')
        self.assertEqual(out, b'ce013625030ba8dba906f756967f9e9c'
                              b'a394464a\n')

    def test_s9_type_option(self):
        _, out, _ = self.mygit('hash-object', '-t', 'tree', '--stdin')
        self.assertEqual(out, b'4b825dc642cb6eb9a060e54bf8d69288'
                              b'fbee4904\n')

    def test_s9_write_then_read_back(self):
        data = golden.make('counter:5000')
        self.put('f', data)
        _, out, _ = self.mygit('hash-object', '-w', 'f')
        oid = out.strip().decode()
        self.assertEqual(self.mygit('cat-file', '-t', oid),
                         (0, b'blob\n', b''))
        self.assertEqual(self.mygit('cat-file', '-s', oid),
                         (0, b'5000\n', b''))
        self.assertEqual(self.mygit('cat-file', '-p', oid),
                         (0, data, b''))
        # 앞부분 7글자로도 찾는다
        self.assertEqual(self.mygit('cat-file', '-p', oid[:7])[1], data)

    def test_s1_4_missing_file(self):
        row = ERRORS['hash-object nope']
        code, out, err = self.mygit('hash-object', 'nope')
        self.assertEqual(err.decode().split('\n')[0],
                         row['stderr-first-line'])
        self.assertEqual(code, int(row['exit']))


class TestCatFile(Sandbox):
    def plant(self, oid):
        d = os.path.join(self.root, '.git', 'objects', oid[:2])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, oid[2:]), 'wb') as f:
            f.write(golden.read('objects', oid))

    def test_s9_commit_and_tag_print_their_bodies(self):
        for row in OBJS:
            if row['type'] not in ('commit', 'tag', 'blob'):
                continue
            self.plant(row['id'])
            code, out, _ = self.mygit('cat-file', '-p', row['id'])
            self.assertEqual((code, out), (0, body_of(row['id'])))
            self.assertEqual(self.mygit('cat-file', '-t', row['id'])[1],
                             row['type'].encode() + b'\n')

    def test_s1_4_not_a_valid_object_name(self):
        row = ERRORS['cat-file -p nope']
        code, _, err = self.mygit('cat-file', '-p', 'nope')
        self.assertEqual((code, err.decode().split('\n')[0]),
                         (int(row['exit']), row['stderr-first-line']))


class TestOutsideRepo(Sandbox):
    with_repo = False

    def test_s1_4_not_a_repository(self):
        row = ERRORS['status']
        code, _, err = self.mygit('cat-file', '-t', 'abcd')
        self.assertEqual((code, err.decode().split('\n')[0]),
                         (int(row['exit']), row['stderr-first-line']))

    def test_s1_1_hash_object_needs_no_repo(self):
        self.put('f', b'hello\n')
        self.assertEqual(self.mygit('hash-object', 'f')[0], 0)

    def test_s1_4_unknown_command(self):
        code, _, err = self.mygit('frobnicate')
        self.assertEqual(code, 1)
        self.assertEqual(err, b"mygit: 'frobnicate' is not a mygit"
                              b" command.\n")


if __name__ == '__main__':
    unittest.main()
