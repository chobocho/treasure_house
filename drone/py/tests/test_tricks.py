# -*- coding: utf-8 -*-
"""tricks 시험 — 13부의 트릭마다 그 트릭이 약속하는 성질 하나씩."""
import math
import unittest

from droneshow import collide
from droneshow import formation as F
from droneshow import params
from droneshow import show as SH
from droneshow import tricks as TR

D = 1.5


def base_show():
    p = params.load()
    return SH.plan([
        {'name': 'a', 'points': F.grid(9, 2 * D, z0=10.0), 'hold': 2.0,
         'rgb': (255, 255, 255)},
        {'name': 'b', 'points': F.circle(9, 2 * D, z0=10.0),
         'hold': 2.0, 'rgb': (255, 0, 0)}], p)


class DarkMove(unittest.TestCase):
    def test_dark_in_the_middle_of_transitions(self):
        s = TR.dark_move(base_show(), fade=0.3)
        a, b = s['scenes'][0]['t1'], s['scenes'][1]['t0']
        for d in s['drones']:
            self.assertEqual(SH.colour(s, d, (a + b) / 2), [0, 0, 0])
            self.assertEqual(SH.colour(s, d, b + 0.5), [255, 0, 0])
            self.assertEqual(SH.colour(s, d, a - 0.5), [255, 255, 255])

    def test_motion_unchanged(self):
        s0 = base_show()
        s1 = TR.dark_move(base_show(), fade=0.3)
        for d0, d1 in zip(s0['drones'], s1['drones']):
            self.assertEqual(d0['keyframes'], d1['keyframes'])


class Takeoff(unittest.TestCase):
    def test_stagger_starts_differ_and_arrive(self):
        p = params.load()
        s = base_show()
        ground = F.grid(9, 2 * D, plane='xy', z0=0.0)
        a = TR.takeoff(s, ground, p, delay=0.0)
        b = TR.takeoff(s, ground, p, delay=1.0)
        starts = sorted({d['keyframes'][1][0] for d in b['drones']})
        self.assertGreater(len(starts), 1)
        for x in (a, b):
            first = x['scenes'][0]
            got = sorted(tuple(round(c, 6) for c in
                               SH.position(x, d, first['t0']))
                         for d in x['drones'])
            want = sorted(tuple(round(c, 6) for c in q)
                          for q in F.grid(9, 2 * D, z0=10.0))
            self.assertEqual(got, want)

    def test_downwash_exposure_metric(self):
        # 한 대가 다른 한 대의 바로 위(반지름 r, 높이 h 안)에 있는 시간
        pts = [[0.0, 0.0, 5.0], [0.3, 0.0, 3.0], [5.0, 0.0, 3.0]]
        self.assertEqual(TR.under_count(pts, 1.0, 3.0), 1)


class Depth(unittest.TestCase):
    def test_layers_keep_front_view_and_add_spacing(self):
        pts = F.grid(16, 1.0, z0=10.0)          # 앞에서 1 m 간격
        deep = TR.layered_depth(pts, 1.5)
        for a, b in zip(pts, deep):
            self.assertEqual((a[0], a[2]), (b[0], b[2]))
        self.assertLess(collide.min_distance(pts)[0], D)
        self.assertGreater(collide.min_distance(deep)[0],
                           collide.min_distance(pts)[0])


class Rotate(unittest.TestCase):
    def test_rotation_keeps_radius(self):
        pts = F.sphere(30, D, z0=10.0)
        seq = TR.rotate_volume(pts, math.pi / 2, 4)
        self.assertEqual(len(seq), 5)
        c = TR.centroid(pts)
        for a, b in zip(seq[0], seq[-1]):
            ra = math.hypot(a[0] - c[0], a[1] - c[1])
            rb = math.hypot(b[0] - c[0], b[1] - c[1])
            self.assertAlmostEqual(ra, rb, places=9)
            self.assertAlmostEqual(a[2], b[2], places=12)


class Wave(unittest.TestCase):
    def test_phase_travels_with_x(self):
        pts = [[x * 2.0, 0.0, 10.0] for x in range(8)]
        w0 = TR.wave(pts, 1.0, 8.0, 1.0, 0.0)
        self.assertAlmostEqual(w0[0][2], 10.0, places=12)
        self.assertAlmostEqual(w0[1][2], 11.0, places=12)   # λ/4 = 2
        # 한 주기 뒤에는 제자리
        w1 = TR.wave(pts, 1.0, 8.0, 1.0, 1.0)
        for a, b in zip(w0, w1):
            self.assertAlmostEqual(a[2], b[2], places=9)


class Lights(unittest.TestCase):
    def test_led_only_motion_moves_light_not_drones(self):
        s0 = base_show()
        s1 = TR.led_only_motion(base_show(), speed=2.0, width=2.0)
        t = s1['scenes'][1]['t0'] + 0.5
        for d0, d1 in zip(s0['drones'], s1['drones']):
            self.assertEqual(SH.position(s0, d0, t),
                             SH.position(s1, d1, t))
        cols = {tuple(SH.colour(s1, d, t)) for d in s1['drones']}
        self.assertGreater(len(cols), 1)

    def test_dither_mean_closer_than_rounding(self):
        n = 40
        want = [i / (n - 1) for i in range(n)]
        d = TR.dither(want, levels=3)
        r = [round(v * 2) / 2 for v in want]
        def block_err(q):
            return sum(abs(sum(q[k:k + 8]) - sum(want[k:k + 8]))
                       for k in range(0, n, 8))
        self.assertLess(block_err(d), block_err(r))
        self.assertTrue(all(v in (0.0, 0.5, 1.0) for v in d))


if __name__ == '__main__':
    unittest.main()
