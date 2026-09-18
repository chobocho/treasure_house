# -*- coding: utf-8 -*-
"""작업 트리 바꾸기의 시험 — SPEC.md §9.3, 9단계 "checkout · switch".

큰 오라클은 golden/scen/checkout.scn(진짜 git 의 switch·checkout 출력과
reflog)이다. 여기서는 장면이 직접 보지 않는 두 가지 — 파일이 없어져
비게 된 디렉터리가 지워지는가, 실행 비트가 작업 트리에 살아나는가 —
를 본다. git 도 둘 다 그렇게 한다(SPEC.md §9.3 끝 문단).
"""
import os
import shutil
import stat
import tempfile
import unittest

from mygit import cli

ENV = {'GIT_AUTHOR_NAME': 'A', 'GIT_AUTHOR_EMAIL': 'a@x',
       'GIT_AUTHOR_DATE': '1700000000 +0900',
       'GIT_COMMITTER_NAME': 'C', 'GIT_COMMITTER_EMAIL': 'c@x',
       'GIT_COMMITTER_DATE': '1700000000 +0900'}


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'w')
        os.makedirs(self.root)
        self.env = dict(os.environ, **ENV)
        self.env['GIT_CEILING_DIRECTORIES'] = self.tmp
        self.ok('init')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def ok(self, *args):
        code, out, err = cli.run(list(args), cwd=self.root,
                                 env=self.env)
        self.assertEqual(code, 0, (args, out, err))
        return out, err

    def put(self, rel, data, mode=0o644):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data)
        os.chmod(p, mode)


class TestTwoWay(Repo):
    def test_s9_3_emptied_directories_are_removed(self):
        self.put('keep', b'k\n')
        self.ok('add', '.')
        self.ok('commit', '-m', 'base')
        self.ok('switch', '-c', 'deep')
        self.put('a/b/c.txt', b'c\n')
        self.ok('add', '.')
        self.ok('commit', '-m', 'deep')
        self.ok('switch', 'main')
        self.assertFalse(os.path.exists(os.path.join(self.root, 'a')))
        self.ok('switch', 'deep')
        path = os.path.join(self.root, 'a', 'b', 'c.txt')
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), b'c\n')

    def test_s9_3_exec_bit_is_written(self):
        self.put('run', b'#!/bin/sh\n', 0o755)
        self.ok('add', '.')
        self.ok('commit', '-m', 'x')
        self.ok('switch', '-c', 'side')
        os.remove(os.path.join(self.root, 'run'))
        self.ok('add', '.')
        self.ok('commit', '-m', 'gone')
        self.ok('switch', 'main')
        mode = os.stat(os.path.join(self.root, 'run')).st_mode
        self.assertTrue(mode & stat.S_IXUSR)

    def test_s9_3_status_is_clean_after_switch(self):
        self.put('f', b'1\n')
        self.ok('add', '.')
        self.ok('commit', '-m', 'one')
        self.ok('switch', '-c', 'b2')
        self.put('f', b'2\n')
        self.put('g/h', b'h\n')
        self.ok('add', '.')
        self.ok('commit', '-m', 'two')
        for name in ('main', 'b2', 'main'):
            self.ok('switch', name)
            self.assertEqual(self.ok('status')[0], b'')


if __name__ == '__main__':
    unittest.main()
