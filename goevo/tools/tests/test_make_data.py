# -*- coding: utf-8 -*-
"""tools/make_data.py 의 시험 (PLAN.md §3.2).

생성 표 셋(releases·api_added·godebug)과 인용 키 표, features.tsv 검사.
픽스처는 받아 둔 진짜 문서의 발췌다 — release.html·godebug.html·
godebugs_table.go·blog_index.html. API 목록은 go1.txt·go1.1.txt 의 진짜
줄 몇 개를 여기 적었다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.dirname(HERE))

import html_text  # noqa: E402
import make_data  # noqa: E402


def fixture(name):
    with io.open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class Releases(unittest.TestCase):
    def setUp(self):
        self.rows = make_data.releases(
            html_text.convert(fixture('release.html')))
        self.by = dict((r[0], r) for r in self.rows)

    def test_go1_major(self):
        self.assertEqual(self.by['go1'],
                         ('go1', '2012-03-28', 'major', 'relnotes-1.0'))

    def test_dot_zero_major(self):
        self.assertEqual(self.by['go1.22.0'],
                         ('go1.22.0', '2024-02-06', 'major', 'relnotes-1.22'))

    def test_minors(self):
        self.assertEqual(self.by['go1.22.1'],
                         ('go1.22.1', '2024-03-05', 'minor', ''))
        self.assertEqual(self.by['go1.0.2'][1], '2012-06-13')

    def test_sorted_by_version(self):
        names = [r[0] for r in self.rows]
        self.assertEqual(names, ['go1', 'go1.0.1', 'go1.0.2', 'go1.22.0',
                                 'go1.22.1', 'go1.27.0'])


GO1 = '''pkg archive/tar, const TypeBlock ideal-char
pkg log/syslog (darwin-386), const LOG_ALERT Priority
pkg log/syslog (darwin-amd64), const LOG_ALERT Priority
pkg log/syslog (darwin-386), const LOG_CRIT Priority
'''
GO11 = '''# comment line
pkg archive/tar, const TypeBlock = 52
pkg go/format, func Node(io.Writer, *token.FileSet, interface{}) error
pkg go/format, func Source([]uint8) ([]uint8, error)
pkg log/syslog (linux-386), const LOG_ALERT = 1
pkg archive/tar, func NewReader //deprecated
'''


class ApiAdded(unittest.TestCase):
    def test_pkg_of_strips_platform(self):
        self.assertEqual(make_data.pkg_of(
            'pkg log/syslog (darwin-386), const LOG_ALERT Priority'),
            ('log/syslog', 'const LOG_ALERT Priority'))
        self.assertIsNone(make_data.pkg_of('# CL 1 x'))

    def test_counts_and_first_packages(self):
        rows = make_data.api_added([('1', GO1), ('1.1', GO11)])
        self.assertEqual(rows[0], ('1.0', '2', '3', 'archive/tar, log/syslog'))
        # 1.1: 기호 넷(주석·//deprecated 제외), 새 패키지는 go/format 하나
        self.assertEqual(rows[1], ('1.1', '1', '4', 'go/format'))


class Godebug(unittest.TestCase):
    def setUp(self):
        self.rows = make_data.godebug_rows(
            fixture('godebugs_table.go'),
            html_text.convert(fixture('godebug.html')))
        self.by = dict((r[0], r) for r in self.rows)

    def test_changed_default_and_first_mention(self):
        self.assertEqual(self.by['httplaxcontentlength'],
                         ('httplaxcontentlength', 'net/http', '1.22', '1.22',
                          '1'))

    def test_never_changed(self):
        self.assertEqual(self.by['tlsmaxrsasize'],
                         ('tlsmaxrsasize', 'crypto/tls', '1.22', '-', '-'))

    def test_not_in_history_excerpt(self):
        self.assertEqual(self.by['panicnil'][2:], ('-', '1.21', '1'))

    def test_commented_out_entry_skipped(self):
        self.assertNotIn('multipartfiles', self.by)
        self.assertEqual(len(self.rows), 6)


class CiteKeys(unittest.TestCase):
    def test_blog_titles(self):
        t = make_data.blog_titles(fixture('blog_index.html'))
        self.assertEqual(t['goroutine-leak-profiles'],
                         ('Goroutine Leak Profiles', '2 September 2026'))

    def test_rows(self):
        rows = make_data.cite_keys(
            ['spec.txt', 'godebug.txt', 'relnotes/go1.28-draft.txt',
             'relnotes/go1.22.txt', 'api/go1.22.txt',
             'blog/goroutine-leak-profiles.txt', 'blog/index.txt',
             'tags.json'],
            {'goroutine-leak-profiles': ('Goroutine Leak Profiles',
                                         '2 September 2026')})
        by = dict((r[0], r) for r in rows)
        self.assertEqual(by['spec'][2], 'spec.txt')
        self.assertEqual(by['relnotes-1.28'][2], 'relnotes/go1.28-draft.txt')
        self.assertIn('초안', by['relnotes-1.28'][1])
        self.assertEqual(by['blog-goroutine-leak-profiles'][1],
                         'Go 블로그 “Goroutine Leak Profiles” (2 September 2026)')
        self.assertNotIn('relnotes-1.22', by)    # releases.tsv 가 맡는다
        self.assertNotIn('api-1.22', by)
        self.assertNotIn('tags', by)             # 인용할 글이 아니다


class Features(unittest.TestCase):
    """features.tsv 검사 — 기억으로 적은 버전이 여기서 걸려야 한다."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='goevo-md-')

        def w(rel, text):
            p = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
        w('data/releases.tsv', 'version\tdate\tkind\trelnotes-key\n'
          'go1.21.0\t2023-08-08\tmajor\trelnotes-1.21\n'
          'go1.22.0\t2024-02-06\tmajor\trelnotes-1.22\n')
        w('data/cite_keys.tsv', 'key\tname\tfile\n')
        w('docs/relnotes/go1.22.txt', '§\tChanges to the language\n')
        w('docs/relnotes/go1.21.txt', '§\tChanges to the language\n')
        w('docs/api/go1.21.txt', 'pkg slices, func Max[$0 cmp.Ordered]($0, ...$0) $0 #1\n')
        w('docs/api/go1.22.txt', 'pkg slices, func Concat x #2\n')
        self.head = ['id', 'version', 'kind', 'title', 'cite-key',
                     'cite-sec', 'slide-id']

    def tearDown(self):
        shutil.rmtree(self.root)

    def check(self, *rows):
        return make_data.check_features(
            self.root, [dict(zip(self.head, r)) for r in rows])

    def test_good_rows(self):
        self.assertEqual(self.check(
            ('loopvar', '1.22', 'lang', '루프 변수', 'relnotes-1.22',
             'Changes to the language', 'p7-loopvar'),
            ('slices-max', '1.21', 'stdlib', 'slices.Max', 'api-1.21',
             'pkg slices, func Max[$0 cmp.Ordered]($0, ...$0) $0 #1',
             'p7-slices')), [])

    def test_wrong_version_is_caught(self):
        bad = self.check(('slices-max', '1.22', 'stdlib', 'slices.Max',
                          'api-1.21', 'pkg slices, func Max[$0 cmp.Ordered]'
                          '($0, ...$0) $0 #1', 'p7-slices'))
        self.assertTrue(any('1.21' in b and '1.22' in b for b in bad), bad)

    def test_unknown_version_kind_and_missing_section(self):
        bad = self.check(('x', '1.99', 'lang', 'x', 'relnotes-1.22',
                          'Changes to the language', 'p7-x'),
                         ('y', '1.22', 'magic', 'y', 'relnotes-1.22',
                          'Changes to the language', 'p7-y'),
                         ('z', '1.22', 'lang', 'z', 'relnotes-1.22',
                          'Nope', 'p7-z'))
        # 행마다 적어도 한 번씩 걸려야 한다. x 는 '없는 버전' 과 '인용과
        # 다른 버전' 두 가지로 걸린다 — 둘 다 참이다.
        for rid in ('x', 'y', 'z'):
            self.assertTrue(any(b.startswith('features.tsv %s:' % rid)
                                for b in bad), (rid, bad))
        self.assertEqual(len(bad), 4, bad)

    def test_stdlib_needs_versioned_cite(self):
        bad = self.check(('s', '1.22', 'stdlib', 's', 'godebug', '', 'p7-s'))
        self.assertTrue(bad)

    def test_duplicates(self):
        row = ('a', '1.22', 'lang', 'a', 'relnotes-1.22',
               'Changes to the language', 'p7-a')
        bad = self.check(row, row)
        self.assertEqual(len(bad), 2, bad)       # id 와 slide-id 둘 다


if __name__ == '__main__':
    unittest.main()
