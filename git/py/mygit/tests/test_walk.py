# -*- coding: utf-8 -*-
"""역사 걷기·merge-base·branch -d 의 시험 — SPEC.md §9.1 · §9.2 · §10,
7단계 "log · DAG 순회 · merge-base".

golden/dag/<역사>/git 은 진짜 git 이 만든 .git 이고, expect.txt 는 그
저장소에서 git 이 찍은 log·merge-base 출력이다. equal 은 모든 커밋의
날짜가 같아(§10.1 의 "먼저 온 것이 먼저" 규칙이 차례를 전부 정한다),
dated 는 날짜가 모두 다르고, criss 는 가장 좋은 공통 조상이 둘이다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, refs, walk
from mygit.tests import golden

HISTORIES = ('equal', 'dated', 'criss')


def expectations(name):
    """expect.txt → [(인자 목록, 기대 stdout, 기대 코드)]."""
    text = golden.read('dag', name, 'expect.txt').decode()
    out = []
    for block in text.split('$ git ')[1:]:
        cmd, _, rest = block.partition('\n')
        body, _, code = rest.rpartition('= ')
        out.append((cmd.split(' '), body, int(code.strip())))
    return out


class Dag(unittest.TestCase):
    name = 'equal'

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'w')
        self.gitdir = os.path.join(self.root, '.git')
        src = golden.path('dag', self.name, 'git')
        shutil.copytree(src, self.gitdir)
        for d in ('objects/pack', 'refs/tags'):
            os.makedirs(os.path.join(self.gitdir, d), exist_ok=True)
        self.env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp,
                        GIT_COMMITTER_NAME='C O Mitter',
                        GIT_COMMITTER_EMAIL='committer@example.com',
                        GIT_COMMITTER_DATE='1700000000 +0900')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def mygit(self, *args):
        return cli.run(list(args), cwd=self.root, env=self.env)


class TestAgainstGit(unittest.TestCase):
    def test_s10_log_and_merge_base_match_git(self):
        n = 0
        for name in HISTORIES:
            d = Dag('run')
            d.name = name
            d.setUp()
            try:
                for args, body, code in expectations(name):
                    got = d.mygit(*args)
                    self.assertEqual((got[0], got[1].decode()),
                                     (code, body),
                                     '%s: %s' % (name, ' '.join(args)))
                    n += 1
            finally:
                d.tearDown()
        self.assertGreaterEqual(n, 14)


class TestWalk(Dag):
    def test_s10_1_equal_dates_first_in_first_out(self):
        # SPEC.md §10.1 의 예: I M2 G H M1 F D E C B A
        head = refs.rev_parse(self.gitdir, 'HEAD')
        order = walk.walk_log(self.gitdir, [head])
        self.assertEqual(len(order), 11)
        self.assertEqual(order[0], head)

    def test_s10_2_is_ancestor(self):
        head = refs.rev_parse(self.gitdir, 'HEAD')
        t = refs.rev_parse(self.gitdir, 't')
        self.assertTrue(walk.is_ancestor(self.gitdir, t, head))
        self.assertFalse(walk.is_ancestor(self.gitdir, head, t))
        self.assertTrue(walk.is_ancestor(self.gitdir, head, head))


class TestBranchDelete(Dag):
    def test_s9_2_delete_merged_branch(self):
        t = refs.rev_parse(self.gitdir, 't')
        code, out, err = self.mygit('branch', '-d', 't')
        self.assertEqual((code, out, err),
                         (0, ('Deleted branch t (was %s).\n'
                              % t[:7]).encode(), b''))
        self.assertIsNone(refs.resolve_ref(self.gitdir, 'refs/heads/t'))

    def test_s9_2_refuses_unmerged_branch(self):
        self.mygit('branch', 'old', 'HEAD~1')
        # HEAD 를 뒤로 돌려 old 가 HEAD 에서 닿지 않게 한다
        base = refs.rev_parse(self.gitdir, 'HEAD~2')
        refs.set_head(self.gitdir, base)
        code, out, err = self.mygit('branch', '-d', 'old')
        self.assertEqual((code, err),
                         (1, b"error: the branch 'old' is not fully "
                             b"merged\n"))

    def test_s9_2_refuses_current_branch(self):
        code, _, err = self.mygit('branch', '-d', 'main')
        want = ("error: cannot delete branch 'main' used by worktree "
                "at '%s'\n" % self.root)
        self.assertEqual((code, err.decode()), (1, want))


class TestLogErrors(Dag):
    def test_s1_4_unknown_revision(self):
        code, _, err = self.mygit('log', 'nope')
        self.assertEqual(code, 128)
        self.assertEqual(err.decode().split('\n')[0],
                         "fatal: ambiguous argument 'nope': unknown "
                         "revision or path not in the working tree.")

    def test_s9_1_limit(self):
        code, out, _ = self.mygit('log', '--oneline', '-n', '3')
        self.assertEqual(len(out.split(b'\n')), 4)


if __name__ == '__main__':
    unittest.main()
