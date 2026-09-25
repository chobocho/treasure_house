# -*- coding: utf-8 -*-
"""16부 실습 — ex/lab_show.py 가 12·60·300 대 쇼를 규칙대로 짜는가."""
import io
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))
import lab_show as L  # noqa: E402
from droneshow import collide, params  # noqa: E402
from droneshow import show as SH  # noqa: E402

DARK = (0, 0, 0)


def lit(sc):
    rgb = sc['rgb']
    if isinstance(rgb, tuple):
        return len(sc['points'])
    return sum(1 for c in rgb if tuple(c) != DARK)


class Scenes(unittest.TestCase):
    def setUp(self):
        self.d = L.spacing(params.load())

    def test_spacing_is_sqrt2_dmin(self):
        # T31: 전환 중 거리는 δ/√2 아래로 안 내려간다
        # → 모양 간격을 √2·dmin 으로 둔다
        self.assertAlmostEqual(self.d, 1.5 * math.sqrt(2), places=12)
        self.assertEqual(L.spacing(params.load(), tight=True), 1.5)

    def test_every_scene_has_n_points(self):
        for n in L.VERSIONS:
            for sc in L.scenes(n, self.d):
                self.assertEqual(len(sc['points']), n, (n, sc['name']))

    def test_scene_names(self):
        names = lambda n: [sc['name'] for sc in L.scenes(n, self.d)]
        self.assertEqual(names(12), ['grid', 'circle', 'heart', 'land'])
        self.assertEqual(names(60), ['grid', 'heart', 'globe', '3', '2',
                                     '1', 'heart2'])
        self.assertEqual(names(300), ['grid', 'TREASURE', 'heart',
                                      'globe', '3', '2', '1', 'heart2'])

    def test_lit_counts_follow_the_glyphs(self):
        sc = {s['name']: s for s in L.scenes(300, self.d)}
        self.assertEqual(lit(sc['TREASURE']), 131)   # 5×7 글꼴의 # 수
        self.assertEqual(lit(sc['3']), 14)
        self.assertEqual(lit(sc['1']), 10)
        self.assertEqual(lit(sc['heart']), 300)

    def test_every_scene_keeps_spacing(self):
        # 켜진 점도, 불 끄고 쉬는 점도 서로 d 이상 — 경계값 d 는 허용
        for n in L.VERSIONS:
            for sc in L.scenes(n, self.d):
                dd = collide.min_distance(sc['points'])[0]
                self.assertGreaterEqual(dd, self.d - 1e-9,
                                        (n, sc['name']))

    def test_parking_is_behind_the_picture(self):
        # 쉬는 드론은 그림 뒤(y > 0)에서 불을 끈다 — 관객 쪽(y < 0) 금지
        sc = {s['name']: s for s in L.scenes(60, self.d)}['1']
        for pt, c in zip(sc['points'], sc['rgb']):
            if tuple(c) == DARK:
                self.assertGreater(pt[1], 0.0)

    def test_every_version_fits_under_120m(self):
        # 300 대 하트를 한 겹으로 그리면 꼭대기가 120 m 를 넘는다 —
        # 그래서 300 대 판은 겹 하트(3겹)가 기본이다
        for n in L.VERSIONS:
            top = max(p[2] for sc in L.scenes(n, self.d)
                      for p in sc['points'])
            self.assertLessEqual(top, 120.0, n)
        flat = L.scenes(300, self.d, layers=1)
        top = max(p[2] for sc in flat for p in sc['points'])
        self.assertGreater(top, 120.0)

    def test_unknown_size_is_refused(self):
        for n in (0, 11, 13, 301):
            with self.assertRaises(ValueError):
                L.scenes(n, self.d)


class Build(unittest.TestCase):
    def test_small_show_keeps_dmin(self):
        p = params.load()
        s = L.build(12, p)
        self.assertEqual(len(s['drones']), 12)
        self.assertGreaterEqual(SH.min_distance(s)[0], p['dmin'] - 1e-9)

    def test_tight_spacing_reaches_the_t31_floor(self):
        # 간격을 dmin 그대로 두면 전환 중 dmin/√2 까지 가까워진다(T31)
        p = params.load()
        s = SH.plan(L.scenes(12, L.spacing(p, tight=True)), p)
        dd = SH.min_distance(s)[0]
        self.assertLess(dd, p['dmin'])
        self.assertGreaterEqual(dd, p['dmin'] / math.sqrt(2) - 1e-9)

    def test_main_writes_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'lab.json')
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = L.main(['12', '-o', path])
            self.assertEqual(code, 0)
            self.assertIn('드론 12대', buf.getvalue())
            with io.open(path, encoding='utf-8') as f:
                s = SH.loads(f.read())
            self.assertEqual([sc['name'] for sc in s['scenes']],
                             ['grid', 'circle', 'heart', 'land'])

    def test_main_tight_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'lab.json')
            with redirect_stdout(io.StringIO()):
                L.main(['12', '--tight', '-o', path])
            with io.open(path, encoding='utf-8') as f:
                s = SH.loads(f.read())
            self.assertLess(SH.min_distance(s)[0], 1.5)


if __name__ == '__main__':
    unittest.main()
