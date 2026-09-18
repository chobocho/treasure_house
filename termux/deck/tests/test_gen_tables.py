# -*- coding: utf-8 -*-
"""gen_tables.py 시험 — 거르개(VIEWS 의 넷째 칸).

2부의 연표는 시대(여러 해)마다 한 장이라, 거르개가 값 하나뿐
아니라 값 여럿(튜플)도 받아야 한다. 값 하나는 이전과 똑같이
같음 비교다(7부의 표가 그대로여야 한다).
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import gen_tables                                  # noqa: E402

TSV = ('# 주석\n'
       'year\tevent\tsource\n'
       '2015\t시작\tgit a\n'
       '2016\t둘째\tgit b\n'
       '2017\t셋째\tgit c\n')


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, 't.tsv'), 'w') as f:
            f.write(TSV)
        self.old = gen_tables.DATA, gen_tables.VIEWS
        gen_tables.DATA = self.d

    def tearDown(self):
        gen_tables.DATA, gen_tables.VIEWS = self.old
        shutil.rmtree(self.d)

    def rows(self, filt):
        gen_tables.VIEWS = [('v.html', 't.tsv', ['year', 'event'], filt)]
        text = gen_tables.build()['v.html']
        return text.count('<tr>') - 1          # 머리글 줄 빼고

    def test_single_value_is_equality(self):
        self.assertEqual(self.rows(('year', '2016')), 1)

    def test_tuple_of_values(self):
        self.assertEqual(self.rows(('year', ('2015', '2017'))), 2)

    def test_empty_tuple_gives_no_rows(self):
        self.assertEqual(self.rows(('year', ())), 0)

    def test_no_filter_keeps_all(self):
        self.assertEqual(self.rows(None), 3)

    def test_full_table_still_made(self):
        gen_tables.VIEWS = []
        self.assertIn('tbl_t.html', gen_tables.build())


if __name__ == '__main__':
    unittest.main()
