# -*- coding: utf-8 -*-
"""check_width 시험 — 예제 파일의 모든 줄은 접힌 폰 화면 폭(72칸) 안이다.
한글은 2칸, 탭은 4칸으로 센다(조립기와 같은 셈)."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_width  # noqa: E402


class Width(unittest.TestCase):
    def test_korean_counts_two_and_tab_four(self):
        self.assertEqual(check_width.width('가a\tb'), 2 + 1 + 4 + 1)

    def test_reports_file_line_and_width_only_over_72(self):
        d = tempfile.mkdtemp(prefix='width-')
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, 'x.py')
        with open(p, 'w', encoding='utf-8') as f:
            f.write('a' * 72 + '\n' + '가' * 37 + '\n\tok\n')
        self.assertEqual(check_width.over([p]), [(p, 2, 74)])

    def test_main_exit_code(self):
        d = tempfile.mkdtemp(prefix='width-')
        self.addCleanup(shutil.rmtree, d, True)
        good = os.path.join(d, 'g.go')
        with open(good, 'w', encoding='utf-8') as f:
            f.write('package g\n')
        self.assertEqual(check_width.main([good]), 0)
        with open(good, 'a', encoding='utf-8') as f:
            f.write('// ' + '나' * 40 + '\n')
        self.assertEqual(check_width.main([good]), 1)


if __name__ == '__main__':
    unittest.main()
