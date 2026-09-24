# -*- coding: utf-8 -*-
"""deck/gen_figs.py 의 시험 — 그림이 자료의 행 수만큼 점·막대를 그리는가.

    python3 -m unittest discover -s tools/tests
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BASE, 'deck'))

import gen_figs  # noqa: E402


class Helpers(unittest.TestCase):
    def test_year_frac(self):
        self.assertAlmostEqual(gen_figs.year_frac('2012-03-28'),
                               2012 + 87 / 366.0, places=3)
        self.assertAlmostEqual(gen_figs.year_frac('2027-02'),
                               2027 + 31 / 365.0, places=3)

    def test_need_stops(self):
        with self.assertRaises(SystemExit):
            gen_figs.need(False, 'x')


class Figures(unittest.TestCase):
    def test_cadence_one_dot_per_major_plus_draft(self):
        svg = gen_figs.FIGURES['cadence']().render()
        majors = [r for r in gen_figs.tsv('releases.tsv')
                  if r['kind'] == 'major']
        self.assertEqual(svg.count('class="dot"'), len(majors))
        self.assertEqual(svg.count('class="dotn"'), 1)     # 1.28 초안
        self.assertIn('viewBox="0 0 340 ', svg)

    def test_api_growth_one_bar_per_version_after_go1(self):
        svg = gen_figs.FIGURES['api_growth']().render()
        rows = gen_figs.tsv('api_added.tsv')
        self.assertEqual(svg.count('class="bar"'), len(rows) - 1)
        # syscall 이 낀 판마다 전체 높이를 점으로 — 봉우리의 정체를 가른다
        with_sys = [r for r in rows[1:] if int(r['syscall-symbols']) > 0]
        self.assertEqual(svg.count('class="dot5"'), len(with_sys))


if __name__ == '__main__':
    unittest.main()
