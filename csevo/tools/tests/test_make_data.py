# -*- coding: utf-8 -*-
"""make_data.py 의 시험 (PLAN.md §0.7, §4 3단계).

픽스처는 받은 진짜 문서의 발췌다 — MessageID.cs 는 설치된 SDK 와 같은
커밋의 RequiredVersion() 스위치, CSharpResources.resx 는 그 <data> 몇 개,
releases json 은 dotnet/core 의 것. 이 표들이 "C# N 에 들어왔다" 를
기계가 대조하는 바닥이다.

    python3 -m unittest discover -s tools/tests
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
FIX = os.path.join(HERE, 'fixtures')

import make_data   # noqa: E402


def fixture(name):
    with io.open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


class LangGates(unittest.TestCase):
    def setUp(self):
        self.rows = make_data.langgates(fixture('MessageID.cs'),
                                        fixture('CSharpResources.resx'))
        self.by = dict((r[0], r) for r in self.rows)

    def test_return_value_wins_over_the_comment(self):
        # 소스 주석은 C# 14 묶음 위에도 "C# 13.0 features" 라고 적혀 있다.
        # 컴파일러가 실제로 쓰는 것은 return 줄이다.
        self.assertEqual(self.by['IDS_FeatureFieldKeyword'][2], '14')
        self.assertEqual(self.by['IDS_FeatureLockObject'][2], '13')

    def test_records_and_names_from_resources(self):
        self.assertEqual(self.by['IDS_FeatureRecords'],
                         ('IDS_FeatureRecords', 'records', '9'))
        self.assertEqual(self.by['IDS_TopLevelStatements'][1],
                         'top-level statements')

    def test_csharp1_and_missing_name(self):
        self.assertEqual(self.by['IDS_FeatureModuleAttrLoc'][2], '1')
        self.assertEqual(self.by['IDS_FeatureModuleAttrLoc'][1], '')

    def test_commented_preview_return_is_ignored(self):
        self.assertFalse(any(r[2] == 'Preview' for r in self.rows))

    def test_version_order_then_name(self):
        keys = [(make_data.vkey(r[2]), r[0]) for r in self.rows]
        self.assertEqual(keys, sorted(keys))

    def test_enum_to_version(self):
        e = make_data.enum_version
        self.assertEqual(e('CSharp7_3'), '7.3')
        self.assertEqual(e('CSharp7'), '7')
        self.assertEqual(e('CSharp14'), '14')
        self.assertEqual(e('CSharp1'), '1')


HIST = ('§\tThe history of C#\n§\tC# version 14\n\n*Released November 2025*\n'
        '§\tC# version 7.3\n\n*Released May 2018*\n'
        '§\tC# version 1.0\n\n*Released January 2002*\n')
LVH = ('§\tFeatures Added in C# Language Versions\n'
       '§\tC# 15.0 - .NET 11 and Visual Studio 2026 version 18.8\n'
       '§\tC# 14.0 - .NET 10 and Visual Studio 2026 version 18.0\n'
       '§\tC# 7.3 - Visual Studio 2017 version 15.7\n'
       '§\tC# 1.0 - Visual Studio .NET 2002\n')


class Releases(unittest.TestCase):
    # 진짜 문서의 제목 줄들(docs/whatsnew/csharp-version-history.txt,
    # docs/csharplang/Language-Version-History.txt)을 옮긴 것
    def test_rows_from_history_and_lvh(self):
        rows = make_data.releases_rows(HIST, LVH)
        self.assertEqual(rows, [
            ('1.0', '2002-01', 'Visual Studio .NET 2002', '', 'history·lvh'),
            ('7.3', '2018-05', 'Visual Studio 2017 version 15.7', '',
             'history·lvh'),
            ('14', '2025-11', 'Visual Studio 2026 version 18.0', '.NET 10',
             'history·lvh')])

    def test_unreleased_version_in_lvh_only_is_left_out(self):
        rows = make_data.releases_rows(HIST, LVH)
        self.assertNotIn('15', [r[0] for r in rows])


class DotnetRows(unittest.TestCase):
    def test_ga_date_is_the_x_0_0_release(self):
        ch = {'releases': [
            {'release-version': '8.0.1', 'release-date': '2024-01-09'},
            {'release-version': '8.0.0', 'release-date': '2023-11-14'},
            {'release-version': '8.0.0-rc.2', 'release-date': '2023-10-10'}]}
        self.assertEqual(make_data.ga_row('8.0', ch, 'releases/8.0.json'),
                         ('.NET', '8', '2023-11-14', 'releases/8.0.json'))

    def test_product_name_by_era(self):
        p = make_data.product_name
        self.assertEqual(p('3.1'), ('.NET Core', '3.1'))
        self.assertEqual(p('5.0'), ('.NET', '5'))
        self.assertEqual(p('1.0'), ('.NET Core', '1.0'))

    def test_unreleased_channel_has_no_row(self):
        ch = {'releases': [{'release-version': '11.0.0-rc.1',
                            'release-date': '2026-09-08'}]}
        self.assertIsNone(make_data.ga_row('11.0', ch, 'releases/11.0.json'))


class CiteKeys(unittest.TestCase):
    def test_keys_from_paths(self):
        paths = ['whatsnew/csharp-12.txt', 'whatsnew/csharp-version-history.txt',
                 'csharplang/Language-Version-History.txt',
                 'csharplang/proposals/csharp-14.0/field-keyword.txt',
                 'roslyn/MessageID.cs', 'roslyn/Language-Feature-Status.txt',
                 'blog/introducing-csharp-14.txt', 'releases/8.0.json',
                 'raw/csharplang-tree.json', 'ecma-334.txt']
        rows = dict((k, (n, f)) for k, n, f in
                    make_data.cite_keys(paths, {'introducing-csharp-14':
                                                'Introducing C# 14'}))
        self.assertEqual(rows['whatsnew-12'][1], 'whatsnew/csharp-12.txt')
        self.assertEqual(rows['history'][1],
                         'whatsnew/csharp-version-history.txt')
        self.assertEqual(rows['lvh'][1],
                         'csharplang/Language-Version-History.txt')
        self.assertEqual(rows['prop-14-field-keyword'][1],
                         'csharplang/proposals/csharp-14.0/field-keyword.txt')
        self.assertEqual(rows['msgid'][1], 'roslyn/MessageID.cs')
        self.assertEqual(rows['blog-introducing-csharp-14'][0],
                         'devblogs “Introducing C# 14”')
        self.assertEqual(rows['rel-8.0'][1], 'releases/8.0.json')
        self.assertNotIn('raw/csharplang-tree', ''.join(rows))


FEATURES = ('id\tversion\tkind\ttitle\tcite-key\tcite-sec\tslide-id\tmsgid\n'
            'rec\t9\tlang\trecord\twhatsnew-9\tRecord types\tp10-rec\tIDS_FeatureRecords\n'
            'bad\t8.0\tlang\t기억 오류\twhatsnew-9\tRecord types\t\tIDS_FeatureRecords\n'
            'nogate\t7.0\tlang\t게이트 없음\twhatsnew-9\tRecord types\t\tIDS_Nope\n'
            'kind\t9.0\tweird\t종류\twhatsnew-9\tNo such heading\tp10-rec\t\n')


class CheckFeatures(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='csevo-md-')
        def w(rel, text):
            p = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            io.open(p, 'w', encoding='utf-8').write(text)
        w('data/releases.tsv', 'version\tdate\tvs\tframework\tsource\n'
          '7.0\t2017-03\tx\tx\tx\n8.0\t2019-09\tx\tx\tx\n9\t2020-11\tx\tx\tx\n')
        w('data/cite_keys.tsv', 'key\tname\tfile\nwhatsnew-9\tW9\tw9.txt\n')
        w('docs/w9.txt', '§\tRecord types\n')
        w('data/langgates.tsv', 'msgid\tfeature\trequired-version\n'
          'IDS_FeatureRecords\trecords\t9\n')
        w('data/features/p10.tsv', FEATURES)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_all_rules(self):
        import cites
        bad = make_data.check_features(self.root,
                                       cites.feature_rows(self.root))
        text = '\n'.join(bad)
        self.assertNotIn(' rec:', text)
        self.assertIn('bad:', text)           # 게이트는 9 인데 8.0 이라 적었다
        self.assertIn('nogate:', text)        # 그런 MessageID 가 없다
        self.assertIn('weird', text)          # kind
        self.assertIn('No such heading', text)  # 인용 절이 없다
        self.assertIn('p10-rec', text)        # slide-id 가 겹친다
        self.assertEqual(len(bad), 5, bad)


if __name__ == '__main__':
    unittest.main()
