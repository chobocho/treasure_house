# -*- coding: utf-8 -*-
"""params 시험 — data/params.tsv 를 읽는다.

SPEC.md §3 의 표와 어긋나지 않는지도 본다."""
import os
import re
import unittest

from droneshow import params

SPEC = os.path.join(os.path.dirname(__file__), '..', '..', 'SPEC.md')


class Load(unittest.TestCase):
    def test_numbers_are_floats(self):
        p = params.load()
        self.assertEqual(p['m'], 0.5)
        self.assertEqual(p['omega_max'], 2000.0)

    def test_derived(self):
        p = params.load()
        d = params.derived(p)
        self.assertAlmostEqual(d['a'], 0.12 / 2 ** 0.5, places=15)
        self.assertAlmostEqual(d["c"], 1.24e-8 / 1.2e-6, places=15)
        self.assertAlmostEqual(d['T_hover'], 0.5 * 9.81 / 4, places=15)
        # why 칸의 '약 1000 rad/s' 가 거짓이 아닌지
        self.assertAlmostEqual(d['omega_hover'], 1011, delta=1)

    def test_spec_table_agrees(self):
        # SPEC §3 의 표에 적힌 값이 params.tsv 와 같아야 한다
        p = params.load()
        text = open(SPEC, encoding='utf-8').read()
        sec = text.split('## 3.')[1].split('## 4.')[0]
        n = 0
        pat = r'^\| `([^|]+)` \| ([^|]+) \|'
        for row in re.findall(pat, sec, re.M):
            names = re.findall(r'[A-Za-z_]+', row[0].replace('`', ''))
            vals = [float(v) for v in row[1].split(',')]
            for k, v in zip(names, vals):
                self.assertEqual(p[k], v, k)
                n += 1
        self.assertGreater(n, 20)


if __name__ == '__main__':
    unittest.main()
