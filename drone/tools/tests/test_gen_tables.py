# -*- coding: utf-8 -*-
"""gen_tables 시험 — 표의 이스케이프·쪼개기·정리 자리 찾기."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'deck'))
import gen_tables as G  # noqa: E402


class Render(unittest.TestCase):
    def test_escape_but_raw_column_kept(self):
        t = G.render(['a', 'b'], [['<x>', '<i>y</i>']], raw=(1,))
        self.assertIn('<td>&lt;x&gt;</td><td><i>y</i></td>', t)

    def test_num_column(self):
        t = G.render(['a', 'n'], [['p', '3']], num=(1,))
        self.assertIn('<th class="num">n</th>', t)
        self.assertIn('<td class="num">3</td>', t)

    def test_chunks(self):
        self.assertEqual([len(c) for c in G.chunks(list(range(30)))],
                         [14, 14, 2])
        self.assertEqual(G.chunks([]), [[]])


class Places(unittest.TestCase):
    def test_first_slide_of_each_theorem(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, '07_a.html'), 'w', encoding='utf-8') as f:
            f.write('<article class="card" id="p7-x"><!--THM id=M1-->'
                    '</article>\n<article class="card" id="p7-y">'
                    '<!--THM id=M1 cont--><!--THM id=M2--></article>')
        saved, G.SECTIONS = G.SECTIONS, d
        try:
            self.assertEqual(G.thm_places(), {'M1': 'p7-x', 'M2': 'p7-y'})
        finally:
            G.SECTIONS = saved


if __name__ == '__main__':
    unittest.main()
