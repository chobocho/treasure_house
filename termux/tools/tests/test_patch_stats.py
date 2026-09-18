# -*- coding: utf-8 -*-
"""patch_stats.sh 시험 — termux-packages 의 패치를 센다(8부).

임시 git 저장소에 packages/ 를 지어 답이 정해진 상태를 만든다.
  a — 패치 둘(.patch), b — 패치 하나 + build.sh, c — build.sh 만,
  d — 이름에 .patch 가 들어가도 끝이 아닌 파일(.patch32)만.
두 번째 커밋에서 a 에 패치를 하나 더 넣어, 판(REV)을 고르면 그
판의 트리를 센다는 것을 본다. 작업 트리가 아니라 커밋을 센다.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'patch_stats.sh')


def git(d, *args):
    return subprocess.run(['git', '-C', d] + list(args), check=True,
                          capture_output=True, text=True).stdout.strip()


def put(d, rel, text='x\n'):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(text)


@unittest.skipUnless(shutil.which('git'), 'git 이 없다')
class PatchStatsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        git(self.d, 'init', '-q')
        git(self.d, 'config', 'user.email', 't@example.com')
        git(self.d, 'config', 'user.name', 't')
        for rel in ('packages/a/one.patch', 'packages/a/two.patch',
                    'packages/b/fix.patch', 'packages/b/build.sh',
                    'packages/c/build.sh', 'packages/d/x.patch32',
                    'README.md'):
            put(self.d, rel)
        git(self.d, 'add', '-A')
        git(self.d, 'commit', '-qm', 'one')
        self.first = git(self.d, 'rev-parse', '--short', 'HEAD')
        put(self.d, 'packages/a/three.patch')
        git(self.d, 'add', '-A')
        git(self.d, 'commit', '-qm', 'two')

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_it(self, *args):
        return subprocess.run(['sh', SCRIPT] + list(args),
                              capture_output=True, text=True)

    def test_counts_at_rev(self):
        r = self.run_it(self.d, self.first)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout,
                         'packages 4\n'
                         'patches 3\n'
                         'patched-packages 2\n'
                         '      2 a\n'
                         '      1 b\n')

    def test_head_by_default_and_top(self):
        r = self.run_it(self.d, 'HEAD', '1')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines()[:3],
                         ['packages 4', 'patches 4',
                          'patched-packages 2'])
        # 위에서 하나만
        self.assertEqual(r.stdout.splitlines()[3:], ['      3 a'])

    def test_worktree_changes_do_not_count(self):
        put(self.d, 'packages/c/new.patch')
        r = self.run_it(self.d, 'HEAD')
        self.assertIn('patches 4\n', r.stdout)

    def test_bad_rev_fails(self):
        r = self.run_it(self.d, 'nosuchrev')
        self.assertNotEqual(r.returncode, 0)

    def test_no_args_is_usage(self):
        r = self.run_it()
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
