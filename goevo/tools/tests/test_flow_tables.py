# -*- coding: utf-8 -*-
"""10부(흐름으로 다시 읽기)의 생성 표 — deck/gen_tables.flow_tables 의 시험.

    python3 -m unittest discover -s tools/tests
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BASE, 'deck'))

import gen_tables  # noqa: E402

TIMELINE = [{'date': '2007-09-21', 'event': '화이트보드 <목표>'},
            {'date': '2009-11-10', 'event': '공개'},
            {'date': '2012-03-28', 'event': 'Go 1 릴리스'}]
GD = [{'setting': 'a', 'introduced-in': '1.21', 'default-changed-in': '1.21'},
      {'setting': 'b', 'introduced-in': '1.21', 'default-changed-in': '-'},
      {'setting': 'c', 'introduced-in': '1.22', 'default-changed-in': '1.23'},
      {'setting': 'd', 'introduced-in': '-', 'default-changed-in': '-'}]
FEATS = [{'version': '1.1', 'kind': 'lang', '_file': 'data/features/p03.tsv'},
         {'version': '1.2', 'kind': 'lang', '_file': 'data/features/p03.tsv'},
         {'version': '1.2', 'kind': 'stdlib', '_file': 'data/features/p03.tsv'},
         {'version': '1.22', 'kind': 'runtime', '_file': 'data/features/p07.tsv'},
         # 8부는 파일 셋(p08·p08b·p08c)으로 나뉜다 — 한 부로 더해야 한다
         {'version': '1.25', 'kind': 'lang', '_file': 'data/features/p08.tsv'},
         {'version': '1.26', 'kind': 'lang', '_file': 'data/features/p08b.tsv'},
         {'version': '1.27', 'kind': 'lang', '_file': 'data/features/p08c.tsv'}]


class Flow(unittest.TestCase):
    def setUp(self):
        self.out = gen_tables.flow_tables(TIMELINE, GD, FEATS, per=2)

    def test_timeline_chunks_escape(self):
        self.assertIn('tbl_flow_timeline_2.html', self.out)
        t = self.out['tbl_flow_timeline_1.html']
        self.assertIn('<td>2007-09-21</td><td>화이트보드 &lt;목표&gt;</td>', t)

    def test_godebug_by_version(self):
        t = self.out['tbl_flow_godebug.html']
        self.assertIn('<td>1.21</td><td class="num">2</td><td class="num">1</td>',
                      t)
        self.assertIn('<td>1.23</td><td class="num">0</td><td class="num">1</td>',
                      t)
        self.assertNotIn('<td>-</td>', t)

    def test_kinds_by_part(self):
        t = self.out['tbl_flow_kinds.html']
        self.assertIn('<td>3부</td><td class="num">2</td>', t)
        self.assertIn('<td>7부</td><td class="num">0</td><td class="num">0</td>'
                      '<td class="num">1</td>', t)
        self.assertIn('<td>8부</td><td class="num">3</td>', t)
        self.assertEqual(t.count('<td>8부</td>'), 1)


class FlowKinds(unittest.TestCase):
    # 네 갈래 표: 갈래마다 판 순서로, 한 판의 기능은 한 줄에 · 로 잇는다.
    # 전용 장이 있으면 그리로 가는 링크. 판은 문자열 순이 아니라 수 순.
    ROWS = [
        {'version': '1.10', 'kind': 'lang', 'title': '열', 'slide-id': 'p4-v110-a',
         '_file': 'data/features/p04.tsv'},
        {'version': '1.9', 'kind': 'lang', 'title': '아홉 <b>', 'slide-id': '',
         '_file': 'data/features/p04.tsv'},
        {'version': '1.9', 'kind': 'lang', 'title': '아홉 둘', 'slide-id': 'p4-v19-b',
         '_file': 'data/features/p04.tsv'},
        {'version': '1.9', 'kind': 'runtime', 'title': 'gc', 'slide-id': '',
         '_file': 'data/features/p04.tsv'},
        {'version': '1.26', 'kind': 'lang', 'title': 'new', 'slide-id': 'p8-v126-new',
         '_file': 'data/features/p08b.tsv'},
    ]

    def test_rows_per_version_in_numeric_order(self):
        out = gen_tables.flow_kind_tables(self.ROWS, per={'lang': 2})
        t1 = out['tbl_flow_lang_1.html']
        self.assertIn('<td>1.9</td><td>아홉 &lt;b&gt; · '
                      '<a href="#p4-v19-b">아홉 둘</a></td>', t1)
        self.assertLess(t1.index('1.9'), t1.index('1.10'))
        self.assertIn('<a href="#p8-v126-new">new</a>',
                      out['tbl_flow_lang_2.html'])
        self.assertNotIn('tbl_flow_lang_3.html', out)

    def test_every_kind_separately(self):
        out = gen_tables.flow_kind_tables(self.ROWS)
        self.assertIn('tbl_flow_runtime_1.html', out)
        self.assertNotIn('gc', out['tbl_flow_lang_1.html'])
        self.assertNotIn('tbl_flow_platform_1.html', out)   # 행이 없으면 표도 없다


if __name__ == '__main__':
    unittest.main()
