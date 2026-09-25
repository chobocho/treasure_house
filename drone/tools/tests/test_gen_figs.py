# -*- coding: utf-8 -*-
"""deck/gen_figs.py 의 시험 — 그림이 자료의 행 수만큼 점을 그리는가.

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
    def test_year_frac_partial_dates(self):
        # 연표의 날짜는 연도만·연월만·연월일 세 꼴이 섞여 있다
        self.assertEqual(gen_figs.year_frac('1935'), 1935.0)
        self.assertAlmostEqual(gen_figs.year_frac('2012-09'),
                               2012 + 244 / 366.0, places=6)
        self.assertAlmostEqual(gen_figs.year_frac('1849-07-15'),
                               1849 + 195 / 365.0, places=6)

    def test_timeline_scale_break(self):
        # 2000 에서 두 토막이 이어져야 한다(점이 건너뛰지 않게)
        self.assertAlmostEqual(gen_figs.tl_x(2000), gen_figs.TL_BRK)
        self.assertAlmostEqual(gen_figs.tl_x(1849), gen_figs.TL_X0)
        self.assertLess(gen_figs.tl_x(1999.99), gen_figs.tl_x(2000.01))

    def test_need_stops(self):
        with self.assertRaises(SystemExit):
            gen_figs.need(False, 'x')


class Figures(unittest.TestCase):
    def test_every_figure_is_340_wide(self):
        for name, fn in gen_figs.FIGURES.items():
            self.assertIn('viewBox="0 0 340 ', fn().render(), name)

    def test_timeline_one_dot_per_row(self):
        svg = gen_figs.FIGURES['timeline']().render()
        rows = gen_figs.tsv('timeline.tsv')
        dots = sum(svg.count('class="dotg%d"' % i) for i in range(1, 9))
        self.assertEqual(dots, len(rows))
        # 갈래마다 제 색 — 드론쇼(7번째)는 dotg7
        shows = sum(1 for r in rows if r['kind'] == 'show')
        self.assertEqual(svg.count('class="dotg7"'), shows)

    def test_show_sizes_one_dot_per_show(self):
        svg = gen_figs.FIGURES['show_sizes']().render()
        rows = gen_figs.tsv('shows.tsv')
        n = {k: sum(1 for r in rows if r['record'] == k)
             for k in gen_figs.RECORD_CLS}
        # 범례의 견본 점이 종류마다 하나씩 더 있다
        self.assertEqual(svg.count('class="dot"'), n['Guinness'] + 1)
        self.assertEqual(svg.count('class="dot2"'), n['claimed'] + 1)
        self.assertEqual(svg.count('class="dotn"'), n['none'] + 1)

    def test_frames_rotor_count(self):
        # +4, X4, 6, 8, 동축 4(링 두 겹), H4 → 촉은 4+4+6+8+4+4 = 30
        svg = gen_figs.FIGURES['frames']().render()
        self.assertEqual(svg.count('class="ah"'), 30)

    def test_curves_read_out(self):
        rows = gen_figs.out_tsv('step')
        self.assertEqual(len(rows), 301)          # 0…6 s, 20 ms
        self.assertEqual(rows[0]['zeta=1'], 0.0)


if __name__ == '__main__':
    unittest.main()
