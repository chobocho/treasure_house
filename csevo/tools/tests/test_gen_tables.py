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


if __name__ == '__main__':
    unittest.main()
