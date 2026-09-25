# -*- coding: utf-8 -*-
"""witness.py 시험 — 정리 id 로 그 증인 시험 하나만 돌린다."""
import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import witness  # noqa: E402


def run(tid):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = witness.main([tid])
    return code, out.getvalue()


class Witness(unittest.TestCase):
    def test_runs_one_test(self):
        code, out = run('M1')
        self.assertEqual(code, 0)
        self.assertIn('test_vec3.Vectors.test_dot_commutes', out)
        self.assertEqual(len(out.strip().split('\n')), 2)

    def test_ex_tests_too(self):
        code, out = run('T26')
        self.assertEqual(code, 0)
        self.assertIn('test_recovers_position', out)

    def test_cited_has_no_witness(self):
        code, out = run('T20')
        self.assertEqual(code, 2)


if __name__ == '__main__':
    unittest.main()
