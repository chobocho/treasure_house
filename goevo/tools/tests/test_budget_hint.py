# -*- coding: utf-8 -*-
"""tools/budget_hint.py 의 시험 — 부 예산을 릴리스 노트 길이에 비례해 나눈다.

    python3 -m unittest discover -s tools/tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import budget_hint  # noqa: E402


class Split(unittest.TestCase):
    def test_proportional_and_sums_to_budget(self):
        got = budget_hint.split(55, [('1.1', 26607), ('1.2', 23565),
                                     ('1.3', 16782), ('1.4', 24440)])
        self.assertEqual(sum(n for _, n in got), 55 - 2 - 3 * 4)
        self.assertEqual([v for v, _ in got], ['1.1', '1.2', '1.3', '1.4'])
        d = dict(got)
        # 긴 노트가 짧은 노트보다 적게 받는 일은 없다(끝수 때문에 같을 수는 있다)
        self.assertTrue(d['1.1'] >= d['1.4'] >= d['1.2'] >= d['1.3'])
        self.assertTrue(d['1.1'] > d['1.3'])

    def test_weight_doubles(self):
        # 41 - 2 - 6 = 33 장 → 1:2 로 11·22 (나누어떨어지는 예산을 고른다)
        got = dict(budget_hint.split(41, [('1.24', 1000), ('1.25', 1000)],
                                     weights={'1.25': 2}))
        self.assertEqual(got['1.25'], 2 * got['1.24'])

    def test_largest_remainder_is_deterministic(self):
        a = budget_hint.split(20, [('a', 1), ('b', 1), ('c', 1)])
        self.assertEqual(a, budget_hint.split(20, [('a', 1), ('b', 1),
                                                   ('c', 1)]))
        self.assertEqual(sum(n for _, n in a), 20 - 2 - 9)


if __name__ == '__main__':
    unittest.main()
