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


class Appendix(unittest.TestCase):
    """부록의 자료 표 — 행 수만큼, 14행씩 쪼개서."""

    @classmethod
    def setUpClass(cls):
        cls.made = G.tables()
        cls.base = os.path.join(HERE, '..', '..')

    def rows(self, name):
        import cites
        return cites.rows(self.base, name)

    def count(self, prefix):
        return sorted(k for k in self.made if k.startswith(prefix))

    def test_timeline_split_and_kinds_in_korean(self):
        n = len(self.rows('timeline.tsv'))
        names = self.count('tbl_d_timeline_')
        self.assertEqual(len(names), -(-n // 14))
        body = ''.join(self.made[k] for k in names)
        self.assertEqual(body.count('<tr>') - len(names), n)
        self.assertIn('<td>드론쇼</td>', body)
        self.assertNotIn('<td>show</td>', body)

    def test_shows_law_tools_firmware(self):
        for tsv, prefix in (('shows.tsv', 'tbl_d_shows_'),
                            ('law.tsv', 'tbl_d_law_'),
                            ('tools_show.tsv', 'tbl_d_tools_'),
                            ('firmware.tsv', 'tbl_d_firmware_')):
            n = len(self.rows(tsv))
            names = self.count(prefix)
            self.assertEqual(len(names), -(-n // 14), prefix)
            body = ''.join(self.made[k] for k in names)
            self.assertEqual(body.count('<tr>') - len(names), n, prefix)

    def test_sources_link_every_key(self):
        keys = self.rows('cite_keys.tsv')
        body = ''.join(self.made[k] for k in self.count('tbl_d_sources_'))
        for r in keys:
            self.assertIn('<td>%s</td>' % r['key'], body)
        # 주소는 글자로 늘어놓지 않고 링크 하나로 — 폴드 폭 때문
        self.assertEqual(body.count('<a href="http'), len(keys))


if __name__ == '__main__':
    unittest.main()
