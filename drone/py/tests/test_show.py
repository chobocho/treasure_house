# -*- coding: utf-8 -*-
"""show 시험 — 장면 → 할당 → 동기 이동 → 쇼 파일 (SPEC §9)."""
import math
import unittest

from droneshow import collide
from droneshow import formation as F
from droneshow import params
from droneshow import show as SH

D = 1.5


def small_show(n=12, kind='trapezoid'):
    p = params.load()
    scenes = [{'name': 'grid', 'points': F.grid(n, 2 * D, z0=10.0),
               'hold': 2.0, 'rgb': (255, 255, 255)},
              {'name': 'heart', 'points': F.heart(n, 2 * D, z0=10.0),
               'hold': 3.0, 'rgb': (255, 0, 64)},
              {'name': 'circle', 'points': F.circle(n, 2 * D, z0=10.0),
               'hold': 2.0, 'rgb': (0, 200, 255)}]
    return SH.plan(scenes, p, profile={'kind': kind, 'ramp': 0.25},
                   fps=25, seed=7)


class Plan(unittest.TestCase):
    def setUp(self):
        self.s = small_show()

    def test_format(self):
        self.assertEqual(self.s['format'], 'droneshow/1')
        self.assertEqual(len(self.s['drones']), 12)
        self.assertEqual([d['id'] for d in self.s['drones']],
                         list(range(12)))

    def test_keyframes_sorted_and_synchronised(self):
        times = [tuple(k[0] for k in d['keyframes'])
                 for d in self.s['drones']]
        self.assertEqual(len(set(times)), 1)          # 모두 같은 시각
        t = times[0]
        self.assertEqual(list(t), sorted(t))

    def test_transition_respects_limits(self):
        p = params.load()
        for d in self.s['drones'][:4]:
            for t in [k / 50 for k in range(round(self.s['duration']
                                                 * 50))]:
                v = SH.velocity(self.s, d, t)
                a = SH.acceleration(self.s, d, t)
                self.assertLessEqual(math.hypot(*v), p['vmax'] + 1e-9)
                self.assertLessEqual(math.hypot(*a), p['amax'] + 1e-9)

    def test_holds_are_still(self):
        sc = self.s['scenes'][1]
        d = self.s['drones'][3]
        a = SH.position(self.s, d, sc['t0'] + 0.1)
        b = SH.position(self.s, d, sc['t1'] - 0.1)
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=12)

    def test_scene_points_reached(self):
        sc = self.s['scenes'][2]
        pos = sorted(tuple(round(c, 6) for c in
                           SH.position(self.s, d, sc['t0']))
                     for d in self.s['drones'])
        want = sorted(tuple(round(c, 6) for c in q)
                      for q in F.circle(12, 2 * D, z0=10.0))
        self.assertEqual(pos, want)

    def test_min_distance_capt_bound(self):
        # 장면 간격 2d ≥ √2·d 이므로 전환 내내 d 이상 (T31)
        got = SH.min_distance(self.s, step=0.04)
        self.assertGreaterEqual(got[0], D - 1e-9)

    def test_colour_at_hold(self):
        sc = self.s['scenes'][1]
        c = SH.colour(self.s, self.s['drones'][0], sc['t0'] + 0.5)
        self.assertEqual(c, [255, 0, 64])

    def test_deterministic(self):
        self.assertEqual(SH.dumps(small_show()), SH.dumps(small_show()))


class Kinds(unittest.TestCase):
    def test_minsnap_is_smoother(self):
        s = small_show(kind='minsnap')
        d = s['drones'][5]
        # 최소 스냅은 전환의 시작과 끝에서 가속도가 0 에서 시작한다
        t0 = s['scenes'][0]['t1']
        self.assertAlmostEqual(math.hypot(*SH.acceleration(s, d, t0)),
                               0.0, places=9)

    def test_beta_derivatives(self):
        for kind in ('T', 'S', 'J', 'L'):
            h = 1e-6
            for u in (0.1, 0.5, 0.8):
                b0 = SH.beta(kind, u - h, 0.25)[0]
                b1 = SH.beta(kind, u + h, 0.25)[0]
                self.assertAlmostEqual(SH.beta(kind, u, 0.25)[1],
                                       (b1 - b0) / (2 * h), places=5)


class Export(unittest.TestCase):
    def test_csv_rows(self):
        s = small_show()
        rows = SH.csv_rows(s, s['drones'][0])
        self.assertEqual(rows[0], 'Time [msec],x [m],y [m],z [m],'
                                  'Red,Green,Blue')
        self.assertEqual(len(rows) - 1, round(s['duration'] * 25) + 1)
        self.assertTrue(rows[1].startswith('0,'))

    def test_json_roundtrip(self):
        s = small_show()
        self.assertEqual(SH.loads(SH.dumps(s)), SH.loads(SH.dumps(s)))
        self.assertIn('"format": "droneshow/1"', SH.dumps(s))


class Physics(unittest.TestCase):
    def test_physics_mode_tracks_plan(self):
        # 계획이 실제로 날 수 있는가 — 쿼드로터 넷을 물리 모드로
        s = small_show(n=4)
        rows = SH.fly_physics(s, params.load(), ids=[0, 1, 2, 3])
        worst = max(r['max_err'] for r in rows)
        self.assertLess(worst, 0.3)
        self.assertEqual(len(rows), 4)


if __name__ == '__main__':
    unittest.main()
