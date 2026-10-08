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



# ---------------------------------------------------------------- 부록(17부)
class AppWhere(unittest.TestCase):
    def test_version_to_cover_overview_badges_and_gates(self):
        ids = {'p2-v1', 'p2-v1-overview', 'p8-v7_3', 'p9-v8',
               'p9-v8-overview', 'p1-intro'}
        feats = [{'version': '1.0', 'slide-id': 'p2-v1-a'},
                 {'version': '1.0', 'slide-id': 'p2-v1-a'},
                 {'version': '1.0', 'slide-id': 'p2-v1-b'},
                 {'version': '1.0', 'slide-id': ''},
                 {'version': '8', 'slide-id': 'p9-v8-x'}]
        gates = [{'required-version': '8'}, {'required-version': '8.0'},
                 {'required-version': '1'}]
        rows = trs(gen_tables.app_where(REL, feats, gates, ids))
        # 배지 단 장은 서로 다른 slide-id 의 수(빈 칸은 세지 않는다)
        self.assertEqual(rows[0], '<tr><td><a href="#p2-v1">C# 1.0</a></td>'
                         '<td>2002-01</td><td><a href="#p2">2부</a></td>'
                         '<td><a href="#p2-v1-overview">개관</a></td>'
                         '<td class="num">2</td><td class="num">1</td></tr>')
        # 표지는 있는데 개관 장이 없으면 '—'
        self.assertEqual(rows[1], '<tr><td><a href="#p8-v7_3">C# 7.3</a></td>'
                         '<td>2018-05</td><td><a href="#p8">8부</a></td>'
                         '<td>—</td><td class="num">0</td>'
                         '<td class="num">0</td></tr>')
        self.assertEqual(rows[2], '<tr><td><a href="#p9-v8">C# 8.0</a></td>'
                         '<td>2019-09</td><td><a href="#p9">9부</a></td>'
                         '<td><a href="#p9-v8-overview">개관</a></td>'
                         '<td class="num">1</td><td class="num">2</td></tr>')
        # 표지가 없는 버전은 링크 없이
        self.assertEqual(rows[3], '<tr><td>C# 13</td><td>2024-11</td>'
                         '<td>—</td><td>—</td><td class="num">0</td>'
                         '<td class="num">0</td></tr>')

    def test_cover_in_the_smallest_part_wins(self):
        ids = {'p9-v8', 'p3-v8'}
        rows = trs(gen_tables.app_where(REL[2:3], [], [], ids))
        self.assertIn('<a href="#p3-v8">C# 8.0</a>', rows[0])


class AppReleases(unittest.TestCase):
    def test_full_vs_name_and_dotnet_ga_date(self):
        dotnet = [{'product': '.NET Core', 'version': '3.0',
                   'date': '2019-09-23'},
                  {'product': '.NET', 'version': '9', 'date': '2024-12-03'}]
        rows = trs(gen_tables.app_releases(REL, dotnet))
        self.assertEqual(rows[0], '<tr><td>C# 1.0</td><td>2002-01</td>'
                         '<td>Visual Studio .NET 2002</td><td>—</td>'
                         '<td>—</td></tr>')
        self.assertEqual(rows[2], '<tr><td>C# 8.0</td><td>2019-09</td>'
                         '<td>Visual Studio 2019 version 16.3</td>'
                         '<td>.NET Core 3.0</td><td>2019-09-23</td></tr>')
        self.assertEqual(rows[3], '<tr><td>C# 13</td><td>2024-11</td>'
                         '<td>Visual Studio 2022 version 17.12</td>'
                         '<td>.NET 9</td><td>2024-12-03</td></tr>')


GATES = [{'msgid': 'IDS_FeatureA', 'feature': 'feature a',
          'required-version': '7.3'},
         {'msgid': 'IDS_FeatureB', 'feature': 'feature b',
          'required-version': '7.3'},
         {'msgid': 'IDS_FeatureC', 'feature': '', 'required-version': '7.3'},
         {'msgid': 'IDS_AwaitX', 'feature': 'await <x>',
          'required-version': '8'},
         {'msgid': 'IDS_FeatureE', 'feature': 'feature e',
          'required-version': '8'}]
GFEATS = [
    {'_file': 'data/features/p08c.tsv', 'msgid': 'IDS_FeatureA',
     'slide-id': 'p8-v7_3-a', 'title': '에이', 'cite-key': 'k',
     'cite-sec': 'S', 'version': '7.3'},
    # 같은 인용(k, S)의 앞 행이 장을 가졌다 — 그 장을 나눠 쓴다
    {'_file': 'data/features/p08c.tsv', 'msgid': 'IDS_FeatureB',
     'slide-id': '', 'title': '비', 'cite-key': 'k', 'cite-sec': 'S',
     'version': '7.3'},
    # 인용이 다르면 나눠 쓴 것이 아니다 — MessageID 를 인용한 장으로
    {'_file': 'data/features/p08c.tsv', 'msgid': 'IDS_FeatureC',
     'slide-id': '', 'title': '씨', 'cite-key': 'k2', 'cite-sec': 'T',
     'version': '7.3'},
    # 장도 인용도 없으면 버전 개관으로
    {'_file': 'data/features/p09.tsv', 'msgid': 'IDS_AwaitX',
     'slide-id': '', 'title': '어웨이트', 'cite-key': 'k', 'cite-sec': 'S',
     'version': '8'}]


class AppGateLinks(unittest.TestCase):
    def test_row_shared_cite_overview_and_none(self):
        ids = {'p8-v7_3-overview', 'p9-v8-overview', 'p8-v7_3-a'}
        cites_ = {'IDS_FeatureC': ['p6-x', 'p7-y']}
        links = gen_tables.gate_links(GATES, GFEATS, cites_, ids)
        self.assertEqual(links['IDS_FeatureA'], ('row', [('p8-v7_3-a', '에이')]))
        self.assertEqual(links['IDS_FeatureB'],
                         ('shared', [('p8-v7_3-a', '비')]))
        self.assertEqual(links['IDS_FeatureC'], ('cite', [('p6-x', '씨')]))
        # 파일이 바뀌면 앞 행을 보지 않는다
        self.assertEqual(links['IDS_AwaitX'],
                         ('overview', [('p9-v8-overview', '어웨이트 (개관)')]))
        self.assertEqual(links['IDS_FeatureE'], ('none', []))


class AppGateTables(unittest.TestCase):
    def test_versions_packed_with_header_rows_and_split_when_long(self):
        links = {'IDS_FeatureA': ('row', [('p8-v7_3-a', '에이')]),
                 'IDS_FeatureB': ('shared', [('p8-v7_3-a', '비')]),
                 'IDS_FeatureC': ('cite', [('p6-x', '씨')]),
                 'IDS_AwaitX': ('overview', [('p9-v8-overview', '어')]),
                 'IDS_FeatureE': ('none', [])}
        out = gen_tables.app_gates(REL, GATES, links, per=5)
        self.assertEqual(sorted(out), ['tbl_app_gates_1.html',
                                       'tbl_app_gates_2.html'])
        one = out['tbl_app_gates_1.html'].split('\n')
        self.assertEqual(one[1], '<tr><th>Roslyn 의 기능 이름</th>'
                         '<th>이 덱에서</th></tr>')
        self.assertEqual(one[2], '<tr><th colspan="2">C# 7.3 · 게이트 3개'
                         '</th></tr>')
        self.assertEqual(one[3], '<tr><td>feature a</td><td>'
                         '<a href="#p8-v7_3-a">에이</a></td></tr>')
        # 자원 파일에 이름이 없는 게이트는 MessageID 를 줄여 보인다
        self.assertEqual(one[5], '<tr><td><code>C</code> (이름 없음)</td><td>'
                         '<a href="#p6-x">씨</a></td></tr>')
        # 7.3(머리+3) 뒤에 8(머리+2)은 다섯 줄에 안 든다 — 다음 장으로
        two = out['tbl_app_gates_2.html'].split('\n')
        self.assertEqual(two[2], '<tr><th colspan="2">C# 8.0 · 게이트 2개'
                         '</th></tr>')
        self.assertEqual(two[3], '<tr><td>await &lt;x&gt;</td><td>'
                         '<a href="#p9-v8-overview">어</a></td></tr>')
        self.assertEqual(two[4], '<tr><td>feature e</td><td>—</td></tr>')

    def test_a_version_longer_than_a_slide_continues(self):
        gates = [{'msgid': 'IDS_Feature%d' % i, 'feature': 'f%d' % i,
                  'required-version': '8'} for i in range(5)]
        links = dict((g['msgid'], ('none', [])) for g in gates)
        out = gen_tables.app_gates(REL, gates, links, per=4)
        self.assertEqual(len(out), 2)
        two = out['tbl_app_gates_2.html'].split('\n')
        self.assertEqual(two[2], '<tr><th colspan="2">C# 8.0 · 게이트 5개 '
                         '(이어서)</th></tr>')
        self.assertEqual(len(trs(out['tbl_app_gates_1.html'])), 3)
        self.assertEqual(len(trs(out['tbl_app_gates_2.html'])), 2)

    def test_how_counts_with_total(self):
        links = {'a': ('row', []), 'b': ('row', []), 'c': ('cite', []),
                 'd': ('none', [])}
        rows = trs(gen_tables.app_gates_how(links))
        self.assertEqual(rows, [
            '<tr><td>기능 행의 장</td><td class="num">2</td></tr>',
            '<tr><td>앞 행과 같은 장(같은 인용)</td><td class="num">0</td></tr>',
            '<tr><td>MessageID 줄을 인용한 장</td><td class="num">1</td></tr>',
            '<tr><td>버전 개관만</td><td class="num">0</td></tr>',
            '<tr><td>덱에 없음</td><td class="num">1</td></tr>',
            '<tr><td>합</td><td class="num">4</td></tr>'])


class AppGlossaryIndex(unittest.TestCase):
    def test_initials_point_at_the_glossary_slides(self):
        terms = ['ㅎ', 'Zeta', '<Main>$', 'alpha', 'Beta', 'beta2', '가',
                 '까치', '나', '하나', '깃']
        rows = [(t, 'x', 'p1') for t in terms]
        html = gen_tables.app_glossary_index(rows, per=3)
        got = trs(html)
        # 차례: <Main>$ alpha Beta | beta2 Zeta ㅎ | 가 깃 까치 | 나 하나
        # (낱자 ㅎ 은 U+314E 라 완성 글자 '가'(U+AC00) 보다 앞에 선다)
        self.assertEqual(got[0], '<tr><td>기호·숫자</td><td>'
                         '<a href="#p17-gl-1">1</a></td></tr>')
        self.assertEqual(got[1], '<tr><td>로마자</td><td>'
                         '<a href="#p17-gl-1">A</a> · '
                         '<a href="#p17-gl-1">B</a> · '
                         '<a href="#p17-gl-2">Z</a></td></tr>')
        # 된소리(ㄲ)는 ㄱ 에 묶는다 — 가나다 차례에서 바로 뒤에 온다
        self.assertEqual(got[2], '<tr><td>ㄱ</td><td>'
                         '<a href="#p17-gl-3">3</a></td></tr>')
        self.assertEqual(got[3], '<tr><td>ㄴ</td><td>'
                         '<a href="#p17-gl-4">4</a></td></tr>')
        # 낱자(ㅎ)도 그 자음의 줄로 — 줄의 차례는 자음 차례이고 장은 수 차례
        self.assertEqual(got[4], '<tr><td>ㅎ</td><td>'
                         '<a href="#p17-gl-2">2</a> · '
                         '<a href="#p17-gl-4">4</a></td></tr>')
        self.assertEqual(len(got), 5)

    def test_same_slide_numbers_as_the_glossary_renderer(self):
        import gen_glossary
        terms = ['b', 'A', '다', '가', 'c', '나', 'Ä', '라', '1']
        rows = [(t, 'x', 'p1') for t in terms]
        rendered = gen_glossary.render(rows)
        html = gen_tables.app_glossary_index(rows, per=gen_glossary.PER_SLIDE)
        # 어느 장에 있다고 했으면 그 장의 제목 범위에 정말 그 낱말이 있다
        import re
        for sid, text in re.findall(r'href="#(p17-gl-\d+)">([^<]+)<', html):
            self.assertIn('id="%s"' % sid, rendered)


class AppCiteTally(unittest.TestCase):
    def test_slides_per_key_and_messageid_lines(self):
        files = [('02_cs1.html',
                  '<article class="card" id="p2-a">x <!--CITE key=history '
                  'sec="C# version 1.0"--> <!--CITE key=history--></article>\n'
                  '<article class="card" id="p2-b"><!--CITE key=msgid '
                  'sec="case MessageID.IDS_FeatureX: // c"--></article>'),
                 ('03_cs2.html',
                  '<article class="card" id="p3-a"><!--CITE key=lvh sec="x"-->'
                  '<!--CITE key=history sec="y"--></article>')]
        keys, msg = gen_tables.cite_tally(files)
        self.assertEqual(keys, {'history': ['p2-a', 'p3-a'],
                                'msgid': ['p2-b'], 'lvh': ['p3-a']})
        self.assertEqual(msg, {'IDS_FeatureX': ['p2-b']})


KEYS = [{'key': 'history', 'name': 'C# 버전 기록',
         'file': 'whatsnew/csharp-version-history.txt'},
        {'key': 'prop-9-records', 'name': 'C# 9 기능 명세 records',
         'file': 'csharplang/proposals/csharp-9.0/records.txt'},
        {'key': 'prop-10-x', 'name': 'C# 10 기능 명세 x',
         'file': 'csharplang/proposals/csharp-10.0/x.txt'},
        {'key': 'prop-9-a', 'name': 'C# 9 기능 명세 a',
         'file': 'csharplang/proposals/csharp-9.0/a.txt'},
        {'key': 'blog-x', 'name': 'devblogs “X”', 'file': 'blog/x.txt'},
        {'key': 'odd', 'name': 'odd', 'file': 'misc/odd.txt'}]
TALLY = {'history': ['p2-a', 'p3-a'], 'prop-9-records': ['p10-r'],
         'blog-x': ['p9-b']}


class AppSources(unittest.TestCase):
    def test_kinds_with_cited_documents_and_distinct_slides(self):
        rows = trs(gen_tables.app_src_kinds(KEYS, TALLY))
        self.assertEqual(rows[0], '<tr><td>버전 기록·새 기능</td>'
                         '<td class="num">1</td><td class="num">1</td>'
                         '<td class="num">2</td></tr>')
        self.assertEqual(rows[1], '<tr><td>기능 명세(csharplang 제안)</td>'
                         '<td class="num">3</td><td class="num">1</td>'
                         '<td class="num">1</td></tr>')
        # 문서가 없는 갈래는 줄을 내지 않는다. 모르는 경로는 '그 밖'
        self.assertEqual(rows[2], '<tr><td>블로그(devblogs)</td>'
                         '<td class="num">1</td><td class="num">1</td>'
                         '<td class="num">1</td></tr>')
        self.assertEqual(rows[3], '<tr><td>그 밖</td><td class="num">1</td>'
                         '<td class="num">0</td><td class="num">0</td></tr>')
        # 합의 장 수는 겹치지 않게 센다(p2-a, p3-a, p10-r, p9-b)
        self.assertEqual(rows[4], '<tr><td>합</td><td class="num">6</td>'
                         '<td class="num">3</td><td class="num">4</td></tr>')

    def test_lists_grouped_with_urls_counts_and_first_slide(self):
        urls = {'whatsnew/csharp-version-history.txt': 'https://e/h.md',
                'csharplang/proposals/csharp-9.0/records.txt': 'https://e/r'}
        out = gen_tables.app_src_lists(KEYS, TALLY, urls, per=4)
        self.assertEqual(sorted(out), ['tbl_app_src_1.html',
                                       'tbl_app_src_2.html',
                                       'tbl_app_src_3.html'])
        one = out['tbl_app_src_1.html'].split('\n')
        self.assertEqual(one[1], '<tr><th>문서</th><th class="num">장</th>'
                         '<th>처음</th></tr>')
        self.assertEqual(one[2], '<tr><th colspan="3">버전 기록·새 기능 · 1개'
                         '</th></tr>')
        self.assertEqual(one[3], '<tr><td><a href="https://e/h.md">C# 버전 '
                         '기록</a></td><td class="num">2</td><td>'
                         '<a href="#p2-a">2부</a></td></tr>')
        # 제안은 버전마다 머리 줄. 9 가 10 보다 앞(수로 견준다), 이름의
        # 'C# 9 기능 명세 ' 는 머리 줄이 말하므로 뗀다
        self.assertEqual(one[4], '<tr><th colspan="3">기능 명세 C# 9 · 2개'
                         '</th></tr>')
        self.assertEqual(one[5], '<tr><td>a</td><td class="num">0</td>'
                         '<td>—</td></tr>')
        two = out['tbl_app_src_2.html'].split('\n')
        self.assertEqual(two[2], '<tr><th colspan="3">기능 명세 C# 9 · 2개 '
                         '(이어서)</th></tr>')
        self.assertEqual(two[3], '<tr><td><a href="https://e/r">records</a>'
                         '</td><td class="num">1</td><td>'
                         '<a href="#p10-r">10부</a></td></tr>')
        self.assertEqual(two[4], '<tr><th colspan="3">기능 명세 C# 10 · 1개'
                         '</th></tr>')

    def test_pins_group_files_by_repository_and_commit(self):
        fetched = [
            {'path': 'a.txt', 'url': 'https://raw.githubusercontent.com/dotnet/'
             'docs/91cc9093b4a0158adc/docs/a.md', 'date': '2026-10-01'},
            {'path': 'b.txt', 'url': 'https://raw.githubusercontent.com/dotnet/'
             'docs/91cc9093b4a0158adc/docs/b.md', 'date': '2026-10-02'},
            {'path': 't.json', 'url': 'https://api.github.com/repos/dotnet/'
             'csharplang/git/trees/93d55a09e48c?recursive=1',
             'date': '2026-10-01'},
            {'path': 'blog/x.txt', 'url': 'https://devblogs.microsoft.com/x/',
             'date': '2026-10-01'}]
        rows = trs(gen_tables.app_src_pins(fetched))
        self.assertEqual(rows, [
            '<tr><td>devblogs.microsoft.com</td><td>—</td>'
            '<td class="num">1</td><td>2026-10-01</td></tr>',
            '<tr><td>dotnet/csharplang</td><td><code>93d55a0</code></td>'
            '<td class="num">1</td><td>2026-10-01</td></tr>',
            '<tr><td>dotnet/docs</td><td><code>91cc909</code></td>'
            '<td class="num">2</td><td>2026-10-01 · 2026-10-02</td></tr>'])


class AppExamples(unittest.TestCase):
    def test_per_part_counts_with_total(self):
        parts = {2: {'ex': 3, 'files': 4, 'lines': 100, 'fail': 1,
                     'caps': 7},
                 0: {'ex': 1, 'files': 1, 'lines': 9, 'fail': 0, 'caps': 2}}
        rows = trs(gen_tables.app_examples(parts))
        self.assertEqual(rows, [
            '<tr><td><a href="#p0">0부</a></td><td class="num">1</td>'
            '<td class="num">1</td><td class="num">9</td>'
            '<td class="num">0</td><td class="num">2</td></tr>',
            '<tr><td><a href="#p2">2부</a></td><td class="num">3</td>'
            '<td class="num">4</td><td class="num">100</td>'
            '<td class="num">1</td><td class="num">7</td></tr>',
            '<tr><td>합</td><td class="num">4</td><td class="num">5</td>'
            '<td class="num">109</td><td class="num">1</td>'
            '<td class="num">9</td></tr>'])



class AppSectionUsesEveryTable(unittest.TestCase):
    """여러 장으로 나뉘는 표(게이트·출처)는 장 수가 자료에 따라 달라진다.
    인용 키가 늘어 표가 한 장 더 생기면 조각 파일에 그 장을 더해야 한다 —
    안 더하면 표가 조용히 덱에서 빠진다. 지금 자료로 만든 부록 표가 전부
    17_appendix.html 에 실렸는지, 없는 표를 가리키지 않는지 본다."""

    def test_every_appendix_table_is_on_a_slide(self):
        # 예제 수 표(tbl_app_ex)는 한 장짜리라 장 수가 안 바뀐다 — 느려서 뺀다
        made = set(gen_tables.appendix_tables(examples=False))
        made.add('tbl_app_ex.html')
        path = os.path.join(gen_tables.HERE, 'sections', '17_appendix.html')
        with open(path, encoding='utf-8') as f:
            text = f.read()
        import re
        used = set(re.findall(r'<!--TABLE file=out/(tbl_app_[^ >-]+\.html)',
                              text))
        self.assertEqual(sorted(set(made) - used), [])
        self.assertEqual(sorted(used - set(made)), [])


if __name__ == '__main__':
    unittest.main()
