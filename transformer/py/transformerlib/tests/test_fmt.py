# -*- coding: utf-8 -*-
"""표 출력 도우미 — 한글이 섞인 표가 어긋나지 않아야 한다.
(optim/tests/test_fmt.py 에서 물려받았다)"""
import unittest

from transformerlib import fmt


class TestWidth(unittest.TestCase):
    def test_wlen(self):
        self.assertEqual(fmt.wlen('abc'), 3)
        self.assertEqual(fmt.wlen('가나'), 4)      # 한글은 두 칸
        self.assertEqual(fmt.wlen('κ₂'), 2)        # 그리스 글자도 한 칸
        self.assertEqual(fmt.wlen(''), 0)
        self.assertEqual(fmt.wlen('x̂'), 1)  # 결합 곡절부호는 0 칸

    def test_pad(self):
        self.assertEqual(fmt.pad('가', 5), '가   ')  # 2칸 + 3칸
        # 넘치면 자르지 않는다
        self.assertEqual(fmt.pad('abcdef', 3), 'abcdef')
        self.assertEqual(fmt.rpad('가', 5), '   가')

    def test_table_alignment(self):
        rows = [['이름', '값'], ['가나다', '1'], ['ab', '22']]
        out = fmt.table(rows, align='ll').split('\n')
        self.assertEqual(len(out), 4)       # 머리 + 구분선 + 2행
        # 폭이 전부 같다
        self.assertEqual(len(set(fmt.wlen(r) for r in out)), 1)

    def test_table_right_align(self):
        out = fmt.table([['a', 'b'], ['x', '1'], ['y', '22']],
                        align='lr')
        self.assertTrue(out.split('\n')[2].endswith(' 1'))

    def test_num(self):
        self.assertEqual(fmt.num(0.5, 3), '0.500')
        self.assertEqual(fmt.num(1e-6, 4), '1.0e-06')
        self.assertEqual(fmt.num(float('nan')), 'nan')


if __name__ == '__main__':
    unittest.main()
