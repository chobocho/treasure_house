# -*- coding: utf-8 -*-
"""deck/gen_tables.py 의 C# 표 시험 (PLAN.md §0.3)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)),
                                'deck'))

import gen_tables  # noqa: E402


class GateCounts(unittest.TestCase):
    def test_counts_per_version_in_release_order(self):
        releases = [{'version': '1.0', 'date': '2002-01'},
                    {'version': '1.2', 'date': '2003-04'},
                    {'version': '7.3', 'date': '2018-05'},
                    {'version': '9', 'date': '2020-11'}]
        gates = [{'msgid': 'A', 'feature': 'x', 'required-version': '9'},
                 {'msgid': 'B', 'feature': 'y', 'required-version': '9'},
                 {'msgid': 'C', 'feature': '', 'required-version': '1'},
                 {'msgid': 'D', 'feature': 'z', 'required-version': '7.3'}]
        html = gen_tables.gate_counts(releases, gates)
        rows = [r for r in html.split('\n') if r.startswith('<tr><td>')]
        # 게이트가 없는 버전(1.2)도 0 으로 한 줄 — 빈 칸이 사실이다
        self.assertEqual(rows, [
            '<tr><td>C# 1.0</td><td>2002-01</td><td class="num">1</td></tr>',
            '<tr><td>C# 1.2</td><td>2003-04</td><td class="num">0</td></tr>',
            '<tr><td>C# 7.3</td><td>2018-05</td><td class="num">1</td></tr>',
            '<tr><td>C# 9</td><td>2020-11</td><td class="num">2</td></tr>'])


class ReleaseTables(unittest.TestCase):
    def test_one_table_per_version_with_links_and_gates(self):
        releases = [{'version': '7.3', 'date': '2018-05',
                     'vs': 'Visual Studio 2017 version 15.7', 'framework': ''},
                    {'version': '12', 'date': '2023-11',
                     'vs': 'Visual Studio 2022 version 17.8',
                     'framework': '.NET 8'}]
        feats = [{'version': '12', 'kind': 'lang', 'title': '컬렉션 식',
                  'slide-id': 'p13-coll'},
                 {'version': '12.0', 'kind': 'lang', 'title': '기본 생성자',
                  'slide-id': ''},
                 {'version': '12', 'kind': 'library', 'title': 'A<B>',
                  'slide-id': ''},
                 {'version': '7.3', 'kind': 'lang', 'title': 'x',
                  'slide-id': ''}]
        gates = [{'required-version': '12'}, {'required-version': '12'}]
        out = gen_tables.release_tables(releases, feats, gates)
        self.assertEqual(sorted(out), ['tbl_rel_12.html', 'tbl_rel_7.3.html'])
        t = out['tbl_rel_12.html']
        self.assertIn('<tr><th>나온 달</th><td>2023-11</td></tr>', t)
        self.assertIn('<tr><th>함께 나온 것</th><td>.NET 8 · '
                      'Visual Studio 2022 version 17.8</td></tr>', t)
        # 12 와 12.0 은 같은 버전이다(vnorm)
        self.assertIn('<tr><th>언어</th><td><a href="#p13-coll">컬렉션 식</a>'
                      ' · 기본 생성자</td></tr>', t)
        self.assertIn('<tr><th>라이브러리</th><td>A&lt;B&gt;</td></tr>', t)
        self.assertIn('<tr><th>런타임</th><td>—</td></tr>', t)
        self.assertIn('<tr><th>컴파일러 게이트</th><td>2개</td></tr>', t)
        self.assertIn('<tr><th>함께 나온 것</th><td>Visual Studio 2017 '
                      'version 15.7</td></tr>', out['tbl_rel_7.3.html'])


if __name__ == '__main__':
    unittest.main()
