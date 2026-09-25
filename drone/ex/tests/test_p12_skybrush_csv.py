# -*- coding: utf-8 -*-
"""12부 — ex/skybrush_csv.py: 우리 쇼 파일 → 드론별 CSV 묶음(zip)."""
import io
import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))
import skybrush_csv as K  # noqa: E402
from droneshow import render as R  # noqa: E402

KF0 = [[0.0, 0, 0, 0, 255, 128, 0, 'L'], [0.08, 0, 0, 0, 255, 128, 0]]
KF7 = [[0.0, 1, 2, 3, 0, 0, 0, 'L'], [0.08, 1, 2, 3, 0, 0, 0]]
SHOW = {'fps': 25, 'duration': 0.08,
        'profile': {'kind': 'trapezoid', 'ramp': 0.25},
        'drones': [{'id': 0, 'keyframes': KF0},
                   {'id': 7, 'keyframes': KF7}]}


class Csv(unittest.TestCase):
    def test_header_order_matches_the_doc(self):
        # Studio 문서의 줄 형식:
        # Time_msec, x_m, y_m, z_m, Red, Green, Blue
        self.assertEqual(K.HEADER,
                         'Time_msec,x_m,y_m,z_m,Red,Green,Blue')

    def test_one_line_per_frame_plus_header(self):
        lines = K.rows(SHOW, SHOW['drones'][0])
        self.assertEqual(lines[0], K.HEADER)
        self.assertEqual(len(lines), 1 + 3)        # 0, 40, 80 ms

    def test_colours_are_linearised(self):
        # 부호 128 은 빛의 22 % — 선형 0–255 로는 56
        line = K.rows(SHOW, SHOW['drones'][0])[1]
        self.assertEqual(line.split(',')[4:], ['255', '56', '0'])
        self.assertEqual(K.linear(128), round(255 * R.decode(128)))

    def test_linear_boundaries(self):
        self.assertEqual(K.linear(0), 0)
        self.assertEqual(K.linear(255), 255)
        for v in range(256):
            self.assertLessEqual(K.linear(v), v)

    def test_zip_has_one_file_per_drone(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'show.zip')
            K.write_zip(SHOW, p)
            with zipfile.ZipFile(p) as z:
                self.assertEqual(sorted(z.namelist()),
                                 ['drone_000.csv', 'drone_007.csv'])
                text = z.read('drone_007.csv').decode('utf-8')
            self.assertTrue(text.startswith(K.HEADER + '\n'))
            self.assertIn('\n0,1.000,2.000,3.000,0,0,0\n', text)

    def test_zip_is_byte_for_byte_reproducible(self):
        # 파일 시각을 고정하지 않으면 같은 쇼도 zip 이 매번 달라진다
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, 'a.zip')
            b = os.path.join(tmp, 'b.zip')
            K.write_zip(SHOW, a)
            K.write_zip(SHOW, b)
            with open(a, 'rb') as fa, open(b, 'rb') as fb:
                self.assertEqual(fa.read(), fb.read())
            with zipfile.ZipFile(a) as z:
                self.assertEqual(z.infolist()[0].date_time,
                                 (1980, 1, 1, 0, 0, 0))

    def test_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, 's.json')
            with io.open(src, 'w', encoding='utf-8') as f:
                import json
                json.dump(SHOW, f)
            out = os.path.join(tmp, 'o.zip')
            buf = io.StringIO()
            sys_stdout, sys.stdout = sys.stdout, buf
            try:
                self.assertEqual(K.main([src, out]), 0)
            finally:
                sys.stdout = sys_stdout
            self.assertIn('2개', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
