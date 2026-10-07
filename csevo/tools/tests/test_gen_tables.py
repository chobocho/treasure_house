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


REL = [{'version': '1.0', 'date': '2002-01', 'vs': 'Visual Studio .NET 2002',
        'framework': ''},
       {'version': '7.3', 'date': '2018-05',
        'vs': 'Visual Studio 2017 version 15.7', 'framework': ''},
       {'version': '8.0', 'date': '2019-09',
        'vs': 'Visual Studio 2019 version 16.3', 'framework': '.NET Core 3.0'},
       {'version': '13', 'date': '2024-11',
        'vs': 'Visual Studio 2022 version 17.12', 'framework': '.NET 9'}]


def trs(html):
    return [r for r in html.split('\n') if r.startswith('<tr><td')]


class P16Parts(unittest.TestCase):
    def test_part_of_each_version_comes_from_the_feature_file(self):
        feats = [{'version': '1.0', '_file': 'data/features/p02.tsv'},
                 {'version': '1.2', '_file': 'data/features/p02b.tsv'},
                 {'version': '8.0', '_file': 'data/features/p09c.tsv'},
                 {'version': '8', '_file': 'data/features/p09.tsv'}]
        self.assertEqual(gen_tables.version_parts(feats),
                         {'1': 2, '1.2': 2, '8': 9})


class P16Timeline(unittest.TestCase):
    def test_split_where_the_dotnet_pairing_starts_with_gaps_and_links(self):
        out = gen_tables.p16_timeline(REL, {'1': 2, '7.3': 8, '8': 9})
        self.assertEqual(sorted(out), ['tbl_p16_rel_1.html',
                                       'tbl_p16_rel_2.html'])
        one = trs(out['tbl_p16_rel_1.html'])
        # 첫 버전은 앞 버전이 없다 — 간격 칸은 '—'
        self.assertEqual(one[0], '<tr><td>C# 1.0</td><td>2002-01</td>'
                         '<td class="num">—</td><td>VS .NET 2002</td>'
                         '<td><a href="#p2">2부</a></td></tr>')
        # 2002-01 → 2018-05 = 196달. 'version' 낱말은 뺀다
        self.assertEqual(one[1], '<tr><td>C# 7.3</td><td>2018-05</td>'
                         '<td class="num">196</td><td>VS 2017 15.7</td>'
                         '<td><a href="#p8">8부</a></td></tr>')
        two = trs(out['tbl_p16_rel_2.html'])
        self.assertEqual(two[0], '<tr><td>C# 8.0</td><td>2019-09</td>'
                         '<td class="num">16</td><td>.NET Core 3.0</td>'
                         '<td>VS 2019 16.3</td>'
                         '<td><a href="#p9">9부</a></td></tr>')
        # 부를 모르는 버전은 링크 없이 '—'
        self.assertIn('<td>VS 2022 17.12</td><td>—</td></tr>', two[1])


class P16Cadence(unittest.TestCase):
    def test_gap_statistics_per_era(self):
        html = gen_tables.p16_cadence(REL)
        rows = trs(html)
        # VS 시대: 1.0→7.3 한 간격 196. .NET 시대: 8.0→13 한 간격 62.
        # 시대를 넘는 7.3→8.0(16)은 '전체' 에만 들어간다
        self.assertEqual(rows[0], '<tr><td>C# 1.0–7.3 (Visual Studio 와 함께)'
                         '</td><td class="num">2</td><td class="num">196</td>'
                         '<td class="num">196</td><td class="num">196.0</td>'
                         '</tr>')
        self.assertEqual(rows[1], '<tr><td>C# 8.0–13 (.NET 과 함께)</td>'
                         '<td class="num">2</td><td class="num">62</td>'
                         '<td class="num">62</td><td class="num">62.0</td>'
                         '</tr>')
        self.assertEqual(rows[2], '<tr><td>전체</td><td class="num">4</td>'
                         '<td class="num">16</td><td class="num">196</td>'
                         '<td class="num">91.3</td></tr>')


class P16Pairs(unittest.TestCase):
    def test_every_dotnet_release_with_its_csharp_and_month_gap(self):
        dotnet = [{'product': '.NET Core', 'version': '2.2',
                   'date': '2018-12-04'},
                  {'product': '.NET Core', 'version': '3.0',
                   'date': '2019-09-23'},
                  {'product': '.NET', 'version': '9', 'date': '2024-12-03'}]
        rows = trs(gen_tables.p16_pairs(REL, dotnet))
        self.assertEqual(rows, [
            '<tr><td>.NET Core 2.2</td><td>2018-12-04</td><td>—</td>'
            '<td>—</td><td class="num">—</td></tr>',
            '<tr><td>.NET Core 3.0</td><td>2019-09-23</td><td>C# 8.0</td>'
            '<td>2019-09</td><td class="num">0</td></tr>',
            # 버전 기록의 달(2024-11)과 releases JSON 의 9.0.0 날짜가 한 달 다르다
            '<tr><td>.NET 9</td><td>2024-12-03</td><td>C# 13</td>'
            '<td>2024-11</td><td class="num">1</td></tr>'])


class P16FeatGates(unittest.TestCase):
    def test_rows_gated_rows_distinct_gates_and_all_gates(self):
        feats = [{'version': '8.0', 'msgid': 'A'},
                 {'version': '8', 'msgid': 'A'},
                 {'version': '8', 'msgid': ''},
                 {'version': '13', 'msgid': 'C'}]
        gates = [{'msgid': 'A', 'required-version': '8'},
                 {'msgid': 'B', 'required-version': '8'},
                 {'msgid': 'C', 'required-version': '13'}]
        rows = trs(gen_tables.p16_featgates(REL, feats, gates))
        self.assertEqual(rows[0], '<tr><td>C# 1.0</td><td class="num">0</td>'
                         '<td class="num">0</td><td class="num">0</td>'
                         '<td class="num">0</td></tr>')
        # 8.0: 행 셋, 게이트가 적힌 행 둘, 그 게이트는 하나(A), 컴파일러 게이트 둘
        self.assertEqual(rows[2], '<tr><td>C# 8.0</td><td class="num">3</td>'
                         '<td class="num">2</td><td class="num">1</td>'
                         '<td class="num">2</td></tr>')
        self.assertEqual(rows[3], '<tr><td>C# 13</td><td class="num">1</td>'
                         '<td class="num">1</td><td class="num">1</td>'
                         '<td class="num">1</td></tr>')
        # 마지막 줄은 합
        self.assertEqual(rows[4], '<tr><td>합</td><td class="num">4</td>'
                         '<td class="num">3</td><td class="num">2</td>'
                         '<td class="num">3</td></tr>')


class P16Kinds(unittest.TestCase):
    def test_kind_counts_per_part_with_links(self):
        feats = [{'version': '1.0', 'kind': 'lang', '_file': 'data/features/p02.tsv'},
                 {'version': '1.2', 'kind': 'runtime', '_file': 'data/features/p02b.tsv'},
                 {'version': '8.0', 'kind': 'ecosystem', '_file': 'data/features/p09.tsv'},
                 {'version': '8.0', 'kind': 'platform', '_file': 'data/features/p09b.tsv'},
                 {'version': '8.0', 'kind': 'library', '_file': 'data/features/p09c.tsv'}]
        rows = trs(gen_tables.p16_kinds(feats))
        self.assertEqual(rows, [
            '<tr><td><a href="#p2">2부</a></td><td>1.0 · 1.2</td>'
            '<td class="num">1</td><td class="num">1</td><td class="num">0</td>'
            '<td class="num">0</td><td class="num">0</td><td class="num">2</td>'
            '</tr>',
            # 생태계와 플랫폼은 '그 밖' 한 칸으로
            '<tr><td><a href="#p9">9부</a></td><td>8.0</td>'
            '<td class="num">0</td><td class="num">0</td><td class="num">0</td>'
            '<td class="num">1</td><td class="num">2</td><td class="num">3</td>'
            '</tr>',
            '<tr><td>합</td><td></td>'
            '<td class="num">1</td><td class="num">1</td><td class="num">0</td>'
            '<td class="num">1</td><td class="num">2</td><td class="num">5</td>'
            '</tr>'])


class P16Standard(unittest.TestCase):
    def test_ecma_table_joined_with_release_months(self):
        with open(os.path.join(HERE, 'fixtures', 'ecma-334-table.txt'),
                  encoding='utf-8') as f:
            text = f.read()
        rel = [{'version': '1.0', 'date': '2002-01'},
               {'version': '1.2', 'date': '2003-04'},
               {'version': '3.0', 'date': '2007-11'},
               {'version': '7.0', 'date': '2017-03'},
               {'version': '7.3', 'date': '2018-05'}]
        rows = trs(gen_tables.p16_standard(rel, text))
        # V1 은 C# 1.0 의 해와 비교한다. 괄호 속 설명은 뗀다
        self.assertEqual(rows[0], '<tr><td>V1</td><td>2002-01</td>'
                         '<td>ECMA-334:2003</td><td>ISO/IEC 23270:2003</td>'
                         '<td class="num">1</td></tr>')
        self.assertEqual(rows[2], '<tr><td>V3</td><td>2007-11</td>'
                         '<td>none</td><td>none</td><td class="num">—</td></tr>')
        # releases.tsv 에 없는 버전(V2·V5·V6)은 나온 달이 '—', 늦음도 '—'
        self.assertEqual(rows[1], '<tr><td>V2</td><td>—</td>'
                         '<td>ECMA-334:2006</td><td>ISO/IEC 23270:2006</td>'
                         '<td class="num">—</td></tr>')
        self.assertEqual(rows[6], '<tr><td>V7</td><td>2017-03</td>'
                         '<td>ECMA-334:2023</td><td>ISO/IEC 20619:2023</td>'
                         '<td class="num">6</td></tr>')
        self.assertEqual(len(rows), 7)


if __name__ == '__main__':
    unittest.main()
