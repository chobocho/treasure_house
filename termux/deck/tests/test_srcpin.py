# -*- coding: utf-8 -*-
"""srcpin 시험 — 핀 고정한 upstream 소스를 SHA 로 읽는 일.

덱의 원리 장은 upstream 소스의 줄을 보여 준다. 그 줄이 "지금 작업
트리" 가 아니라 "data/repos.tsv 에 적은 커밋" 의 것이어야 독자가
같은 커밋을 열어 같은 줄을 본다. 그래서 임시 git 저장소를 만들어
커밋 두 개를 쌓고, 핀이 가리키는 쪽의 내용이 나오는지를 본다.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import srcpin                                                  # noqa: E402

HEAD = ('repo\turl\tpinned-sha\tpinned-date\tlicense\twhy-pinned\n')


def git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t',
               GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t')
    return subprocess.run(('git',) + args, cwd=cwd, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


class SrcPinTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        repo = os.path.join(self.base, 'sources', 'demo')
        os.makedirs(os.path.join(repo, 'src'))
        git(repo, 'init', '-q')
        self.write(repo, 'src/a.c', 'one\ntwo\nthree\n')
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'first')
        self.sha1 = git(repo, 'rev-parse', 'HEAD')
        # 두 번째 커밋이 줄을 바꾼다 — 핀은 첫 커밋에 있다
        self.write(repo, 'src/a.c', 'ONE\ntwo\n')
        git(repo, 'commit', '-qam', 'second')
        self.sha2 = git(repo, 'rev-parse', 'HEAD')
        os.makedirs(os.path.join(self.base, 'data'))
        self.write(self.base, 'data/repos.tsv',
                   HEAD + 'demo\thttps://example.invalid/demo\t%s\t'
                   '2026-09-18\tGPL-3.0\ttest\n' % self.sha1)
        self.pin = srcpin.Pins(self.base)

    def tearDown(self):
        shutil.rmtree(self.base)

    def write(self, d, rel, text):
        io.open(os.path.join(d, rel), 'w', encoding='utf-8',
                newline='\n').write(text)

    # ── 정상 ──────────────────────────────────────────────────────
    def test_reads_pinned_commit_not_worktree(self):
        self.assertEqual(self.pin.lines('sources/demo/src/a.c'),
                         ['one', 'two', 'three'])

    def test_split_path(self):
        self.assertEqual(srcpin.split('sources/demo/src/a.c'),
                         ('demo', 'src/a.c'))
        self.assertIsNone(srcpin.split('py/elf.py'))

    def test_pinned_sha_and_short_prefix(self):
        self.assertEqual(self.pin.sha('demo'), self.sha1)
        self.assertIsNone(self.pin.check('demo', self.sha1))
        self.assertIsNone(self.pin.check('demo', self.sha1[:7]))

    def test_exists_at_pin(self):
        self.assertTrue(self.pin.exists('sources/demo/src/a.c'))

    # ── 가장자리 ──────────────────────────────────────────────────
    def test_sha_mismatch_is_error(self):
        msg = self.pin.check('demo', self.sha2)
        self.assertIn('핀', msg)

    def test_short_prefix_below_seven_is_error(self):
        self.assertIsNotNone(self.pin.check('demo', self.sha1[:6]))

    def test_unknown_repo_is_error(self):
        self.assertIn('repos.tsv', self.pin.check('nope', self.sha1))

    def test_empty_sha_is_error(self):
        self.assertIsNotNone(self.pin.check('demo', ''))
        self.assertIsNotNone(self.pin.check('demo', None))

    def test_missing_file_at_pin(self):
        self.assertFalse(self.pin.exists('sources/demo/src/nope.c'))
        self.assertIsNone(self.pin.lines('sources/demo/src/nope.c'))

    def test_missing_checkout(self):
        shutil.rmtree(os.path.join(self.base, 'sources', 'demo'))
        p = srcpin.Pins(self.base)
        self.assertIsNone(p.lines('sources/demo/src/a.c'))

    def test_no_repos_tsv(self):
        os.remove(os.path.join(self.base, 'data', 'repos.tsv'))
        p = srcpin.Pins(self.base)
        self.assertIsNotNone(p.check('demo', self.sha1))

    def test_header_only_tsv(self):
        self.write(self.base, 'data/repos.tsv', HEAD)
        p = srcpin.Pins(self.base)
        self.assertEqual(p.repos(), {})

    def test_last_line_without_newline_kept(self):
        repo = os.path.join(self.base, 'sources', 'demo')
        self.write(repo, 'src/b.c', 'x\ny')
        git(repo, 'add', '.')
        git(repo, 'commit', '-qm', 'third')
        sha3 = git(repo, 'rev-parse', 'HEAD')
        self.write(self.base, 'data/repos.tsv',
                   HEAD + 'demo\tu\t%s\td\tl\tw\n' % sha3)
        p = srcpin.Pins(self.base)
        self.assertEqual(p.lines('sources/demo/src/b.c'), ['x', 'y'])

    # ── grep: 핀 커밋의 파일에서 패턴을 찾는다(캡처용) ─────────────
    def test_grep_prints_line_and_match(self):
        got = self.pin.grep('demo:src/a.c', r't[a-z]+')
        self.assertEqual(got, ['2:two', '3:three'])

    def test_grep_reads_pin_not_worktree(self):
        # 작업 트리의 a.c 는 'ONE\ntwo' 이지만 핀은 'one…three' 다
        self.assertEqual(self.pin.grep('demo:src/a.c', r'^one$'),
                         ['1:one'])

    def test_grep_missing_file_raises(self):
        with self.assertRaises(LookupError):
            self.pin.grep('demo:src/none.c', 'x')

    # ── sources-check: 핀 커밋이 체크아웃에 들어 있는가 ─────────────
    def test_missing_commits_all_present(self):
        self.assertEqual(self.pin.missing(), [])

    def test_missing_commits_reports_absent_sha(self):
        self.write(self.base, 'data/repos.tsv',
                   HEAD + 'demo\tu\t%s\td\tl\tw\n' % ('0' * 40))
        got = srcpin.Pins(self.base).missing()
        self.assertEqual(len(got), 1)
        self.assertIn('demo', got[0])

    def test_missing_commits_reports_absent_checkout(self):
        shutil.rmtree(os.path.join(self.base, 'sources', 'demo'))
        got = srcpin.Pins(self.base).missing()
        self.assertEqual(len(got), 1)
        self.assertIn('make sources', got[0])

    def test_missing_commits_empty_table(self):
        self.write(self.base, 'data/repos.tsv', HEAD)
        self.assertEqual(srcpin.Pins(self.base).missing(), [])


if __name__ == '__main__':
    unittest.main()
