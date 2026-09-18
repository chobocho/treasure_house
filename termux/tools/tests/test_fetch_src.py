# -*- coding: utf-8 -*-
"""fetch_src.sh 시험 — upstream 을 핀 커밋으로 받아 두는 일.

네트워크는 쓰지 않는다. 임시 디렉터리에 file:// 원격 저장소를 만들고
(커밋 둘, 태그 하나, 디렉터리 둘), data/repos.tsv 를 그것으로 채운 뒤
fetch_src.sh 가 핀 커밋에 서는지 본다. GitHub 이 허락하는 두 가지
(부분 복제 필터, SHA 로 직접 받기)를 원격에 켜 둔다.
"""
import io
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'fetch_src.sh')
HEAD = ('repo\turl\tpinned-sha\tpinned-date\tlicense\thistory\tpaths'
        '\twhy-pinned\n')
ENV = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
           GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')


def git(cwd, *args):
    return subprocess.run(('git',) + args, cwd=cwd, env=ENV, check=True,
                          capture_output=True, text=True).stdout.strip()


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        work = os.path.join(self.tmp, 'work')
        os.makedirs(os.path.join(work, 'a'))
        os.makedirs(os.path.join(work, 'b'))
        git(work, 'init', '-q', '-b', 'main')
        self.put(work, 'a/x.txt', 'one\n')
        self.put(work, 'b/y.txt', 'two\n')
        self.put(work, 'README.md', 'r\n')
        git(work, 'add', '.')
        git(work, 'commit', '-qm', 'first')
        git(work, 'tag', 'v1')
        self.c1 = git(work, 'rev-parse', 'HEAD')
        self.put(work, 'a/x.txt', 'ONE\n')
        git(work, 'commit', '-qam', 'second')
        self.c2 = git(work, 'rev-parse', 'HEAD')
        self.origin = os.path.join(self.tmp, 'origin.git')
        git(self.tmp, 'clone', '-q', '--bare', work, self.origin)
        git(self.origin, 'config', 'uploadpack.allowFilter', 'true')
        git(self.origin, 'config', 'uploadpack.allowAnySHA1InWant',
            'true')
        self.base = os.path.join(self.tmp, 'base')
        os.makedirs(os.path.join(self.base, 'data'))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def put(self, d, rel, text):
        io.open(os.path.join(d, rel), 'w', encoding='utf-8',
                newline='\n').write(text)

    def table(self, *rows):
        self.put(self.base, 'data/repos.tsv', HEAD + ''.join(
            '%s\tfile://%s\t%s\t-\tMIT\t%s\t%s\ttest\n'
            % (name, self.origin, sha, hist, paths)
            for name, sha, hist, paths in rows))

    def run_it(self, *args):
        env = dict(ENV, FETCH_BASE=self.base)
        return subprocess.run(['sh', SCRIPT] + list(args), env=env,
                              capture_output=True, text=True)

    def src(self, name):
        return os.path.join(self.base, 'sources', name)

    def head(self, name):
        return git(self.src(name), 'rev-parse', 'HEAD')

    def has(self, name, *rel):
        return os.path.exists(os.path.join(self.src(name), *rel))

    def test_full_history_at_pin(self):
        self.table(('r', self.c1, 'full', '-'))
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.head('r'), self.c1)
        # 전체 기록이면 핀 뒤의 커밋과 태그도 있다 (연표·태그 날짜용)
        git(self.src('r'), 'cat-file', '-e', self.c2 + '^{commit}')
        self.assertIn('v1', git(self.src('r'), 'tag'))
        self.assertEqual(io.open(os.path.join(self.src('r'), 'a',
                                              'x.txt')).read(), 'one\n')

    def test_shallow_has_one_commit(self):
        self.table(('s', self.c1, 'shallow', '-'))
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.head('s'), self.c1)
        self.assertEqual(git(self.src('s'), 'rev-list', '--count',
                             'HEAD'), '1')

    def test_sparse_paths(self):
        self.table(('p', self.c2, 'shallow', 'a'))
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.has('p', 'a', 'x.txt'))
        self.assertFalse(self.has('p', 'b'))
        # 희소 체크아웃이어도 git show 로는 핀 커밋의 모든 파일을 읽는다
        self.assertEqual(git(self.src('p'), 'show',
                             self.c2 + ':b/y.txt'), 'two')

    def test_rerun_is_idempotent_and_moves_pin(self):
        self.table(('r', self.c1, 'full', '-'))
        self.assertEqual(self.run_it().returncode, 0)
        self.table(('r', self.c2, 'full', '-'))
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.head('r'), self.c2)

    def test_unknown_sha_fails(self):
        self.table(('r', 'f' * 40, 'shallow', '-'))
        r = self.run_it()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('r', r.stderr)

    def test_only_one_repo(self):
        self.table(('r', self.c1, 'full', '-'),
                   ('s', self.c1, 'shallow', '-'))
        r = self.run_it('--only', 's')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(self.src('r')))
        self.assertTrue(os.path.exists(self.src('s')))

    def test_head_mode_lists_remote_head(self):
        self.table(('r', self.c1, 'full', '-'))
        r = self.run_it('--head')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('r\t' + self.c2, r.stdout)
        self.assertFalse(os.path.exists(self.src('r')))

    def test_empty_table(self):
        self.put(self.base, 'data/repos.tsv', HEAD)
        self.assertEqual(self.run_it().returncode, 0)


if __name__ == '__main__':
    unittest.main()
