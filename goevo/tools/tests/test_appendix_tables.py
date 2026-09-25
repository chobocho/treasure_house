# -*- coding: utf-8 -*-
"""부록(11부)의 생성 표 — deck/gen_tables.appendix_tables 의 시험.

    python3 -m unittest discover -s tools/tests
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BASE, 'deck'))

import gen_tables  # noqa: E402

REL = [{'version': 'go1', 'date': '2012-03-28', 'kind': 'major'},
       {'version': 'go1.0.1', 'date': '2012-04-25', 'kind': 'minor'},
       {'version': 'go1.0.3', 'date': '2012-09-21', 'kind': 'minor'},
       {'version': 'go1.1', 'date': '2013-05-13', 'kind': 'major'}]
API = [{'version': '1.0', 'new-packages': '126', 'new-symbols': '11640',
        'sample-packages': 'archive/tar, bufio', 'syscall-symbols': '5277'},
       {'version': '1.1', 'new-packages': '2', 'new-symbols': '7918',
        'sample-packages': 'go/format', 'syscall-symbols': '6329'}]
GD = [{'setting': 's%02d' % i, 'package': 'p', 'introduced-in': '1.2%d' % (i % 8),
       'default-changed-in': '-', 'old-value': '-'} for i in range(30)]
INDEX = ('<p class="blogtitle">\n  <a href="/blog/a">A</a>, '
         '<span class="date">2 September 2026</span><br>\n'
         '  <span class="author">Vlad Saioc<br></span>\n</p>\n'
         '<p class="blogtitle">\n  <a href="/blog/b">B</a>, '
         '<span class="date">21 May 2026</span><br>\n'
         '  <span class="author">Ethan Lee, Hana Kim, and Vlad Saioc<br>'
         '</span>\n</p>\n'
         '<p class="blogtitle">\n  <a href="/blog/c">C</a>, '
         '<span class="date">19 August 2026</span><br>\n'
         '  <span class="author">Nicholas Husin, on behalf of the Go team'
         '<br></span>\n</p>\n')
FETCHED = ['release.txt', 'relnotes/go1.txt', 'relnotes/go1.1.txt',
           'api/go1.txt', 'blog/a.txt', 'blog/index.txt', 'spec.txt',
           'tags.json']


class Appendix(unittest.TestCase):
    def setUp(self):
        # 세는 규칙을 보는 시험이라 글 한 편인 사람도 싣는다
        self.out = gen_tables.appendix_tables(REL, API, GD, INDEX, FETCHED,
                                              per=14, min_posts=1)

    def test_majors_with_minor_counts(self):
        t = self.out['tbl_app_majors_1.html']
        self.assertIn('<td>go1</td><td>2012-03-28</td><td class="num">2'
                      '</td><td>go1.0.3 (2012-09-21)</td>', t)
        self.assertIn('<td>go1.1</td><td>2013-05-13</td><td class="num">0'
                      '</td><td>—</td>', t)

    def test_api_go1_packages_not_listed(self):
        t = self.out['tbl_app_api_1.html']
        self.assertIn('(Go 1 의 전부)', t)
        self.assertNotIn('archive/tar', t)
        self.assertIn('go/format', t)

    def test_godebug_split_in_chunks(self):
        self.assertIn('tbl_app_godebug_3.html', self.out)
        self.assertNotIn('tbl_app_godebug_4.html', self.out)
        self.assertIn('s29', self.out['tbl_app_godebug_3.html'])

    def test_authors_counted_and_team_line_trimmed(self):
        t = self.out['tbl_app_authors_1.html']
        self.assertIn('<td>Vlad Saioc</td><td class="num">2</td>'
                      '<td>2026-05-21</td><td>2026-09-02</td>', t)
        self.assertIn('<td>Nicholas Husin</td>', t)
        self.assertNotIn('behalf', t)

    def test_team_byline_is_not_a_person(self):
        # 글쓴이 칸이 팀 전체인 글 — 인물 색인에 사람으로 올리지 않는다
        idx = INDEX + ('<p class="blogtitle">\n  <a href="/blog/e">E</a>, '
                       '<span class="date">2 May 2024</span><br>\n'
                       '  <span class="author">The Go Team<br></span>\n</p>\n')
        out = gen_tables.appendix_tables(REL, API, GD, idx, FETCHED,
                                         per=14, min_posts=1)
        self.assertNotIn('Go Team', out['tbl_app_authors_1.html'])

    def test_for_the_team_tail_and_minimum(self):
        idx = INDEX + ('<p class="blogtitle">\n  <a href="/blog/d">D</a>, '
                       '<span class="date">1 May 2024</span><br>\n'
                       '  <span class="author">Todd Kulesza, for the Go team'
                       '<br></span>\n</p>\n')
        out = gen_tables.appendix_tables(REL, API, GD, idx, FETCHED,
                                         per=14, min_posts=2)
        t = out['tbl_app_authors_1.html']
        self.assertNotIn('for the Go team', t)
        self.assertNotIn('Todd Kulesza', t)        # 글 1편 — 기준 아래
        self.assertIn('Vlad Saioc', t)

    def test_sources_by_kind(self):
        t = self.out['tbl_app_sources.html']
        self.assertIn('<td>릴리스 노트</td><td class="num">2</td>', t)
        self.assertIn('<td>블로그 글</td><td class="num">1</td>', t)


if __name__ == '__main__':
    unittest.main()
