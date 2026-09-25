# -*- coding: utf-8 -*-
"""데모 자료 생성기 deck/gen_demos.py 의 시험 (PLAN.md §3.6, §5 8단계).

데모는 자바스크립트지만 자료는 data/ 와 out/ 의 표에서 온다. 생성기는
표를 JSON 으로 옮겨 demos_src.js 앞에 붙인다 — 손으로 옮기면 표와
데모가 어긋난다.

    python3 -m unittest discover -s tools/tests
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BASE, 'deck'))

import gen_demos  # noqa: E402

RELEASES = [{'version': 'go1', 'date': '2012-03-28', 'kind': 'major'},
            {'version': 'go1.0.1', 'date': '2012-04-25', 'kind': 'minor'},
            {'version': 'go1.21.0', 'date': '2023-08-08', 'kind': 'major'},
            {'version': 'go1.22.0', 'date': '2024-02-06', 'kind': 'major'}]
TIMELINE = [{'date': '2009-11-10', 'event': '공개', 'source': 'x'}]
FEATURES = [{'id': 'rangeint', 'version': '1.22', 'kind': 'lang',
             'title': '정수 range', 'slide-id': 'p7-v122-rangeint',
             '_file': 'data/features/p07.tsv'},
            {'id': 'x', 'version': '1.28', 'kind': 'stdlib', 'title': '초안',
             'slide-id': '', '_file': 'data/features/p09.tsv'}]
LADDER = [('rangeint', '1.22', '정수 range')]
GODEBUG = [{'setting': 'panicnil', 'package': 'runtime', 'introduced-in': '1.21',
            'default-changed-in': '1.21', 'old-value': '1'}]
API = [{'version': '1.21', 'new-packages': '4', 'new-symbols': '1000',
        'syscall-symbols': '0',
        'sample-packages': ', '.join('p%d' % i for i in range(20))}]


class Data(unittest.TestCase):
    def setUp(self):
        self.d = gen_demos.build_data(RELEASES, TIMELINE, FEATURES, LADDER,
                                      GODEBUG, API)

    def test_majors_only_with_short_version(self):
        self.assertEqual(self.d['rel'], [['1.0', '2012-03-28'],
                                         ['1.21', '2023-08-08'],
                                         ['1.22', '2024-02-06']])

    def test_features_keep_what_the_demos_need(self):
        self.assertEqual(self.d['feat'][0],
                         ['rangeint', '1.22', '정수 range', 'p7-v122-rangeint'])

    def test_quiz_skips_draft_versions(self):
        # 1.28 은 아직 나오지 않았다 — '어느 판에서 왔나' 카드로 내지 않는다
        self.assertEqual([f[0] for f in self.d['feat']], ['rangeint'])

    def test_ladder_godebug_api(self):
        self.assertEqual(self.d['ladder'], [['rangeint', '1.22', '정수 range']])
        self.assertEqual(self.d['godebug'][0],
                         ['panicnil', 'runtime', '1.21', '1.21', '1'])
        api = self.d['api'][0]
        self.assertEqual(api[:4], ['1.21', 4, 1000, 0])
        self.assertEqual(len(api[4]), 12)   # 표본 패키지는 열두 개까지

    def test_timeline(self):
        self.assertEqual(self.d['tl'], [['2009-11-10', '공개']])


class Render(unittest.TestCase):
    def test_data_line_then_source(self):
        js = gen_demos.render({'a': [1]}, '__demo("x", function(){});\n')
        head, rest = js.split('var DATA = ', 1)
        self.assertIn('생성', head)                 # 손으로 고치지 말라는 머리말
        line, src = rest.split('\n', 1)
        self.assertEqual(json.loads(line.rstrip(';')), {'a': [1]})
        self.assertEqual(src, '__demo("x", function(){});\n')

    def test_non_ascii_stays_readable(self):
        js = gen_demos.render({'t': '정수'}, '')
        self.assertIn('정수', js)


if __name__ == '__main__':
    unittest.main()
