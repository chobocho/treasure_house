# -*- coding: utf-8 -*-
"""16부 실습 — ex/lab_check.py 가 쇼 파일의 규칙 위반을 잡는가."""
import copy
import io
import math
import os
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'py'))
import lab_check as C  # noqa: E402
import lab_show as L  # noqa: E402
from droneshow import motor, params  # noqa: E402
from droneshow import show as SH  # noqa: E402

P = params.load()
GOOD = L.build(12, P)
TIGHT = SH.plan(L.scenes(12, L.spacing(P, tight=True)), P)


def by_name(rows):
    return {r[0]: r for r in rows}


class Checks(unittest.TestCase):
    def test_names_in_order(self):
        self.assertEqual([r[0] for r in C.check(GOOD, P)],
                         ['최소 간격', '최고 속도', '최고 가속도',
                          '고도', '비행시간'])

    def test_planned_show_passes(self):
        for name, ok, _v, _lim in C.check(GOOD, P):
            self.assertTrue(ok, name)

    def test_tight_show_fails_spacing_only(self):
        r = by_name(C.check(TIGHT, P))
        self.assertFalse(r['최소 간격'][1])
        self.assertTrue(r['최고 속도'][1])

    def test_speed_is_exact_per_segment(self):
        # 계획은 가장 먼 드론이 v_max 에 닿게 시간을 정한다 — 최고
        # 속도는 v_max 에 (1/fps 올림만큼) 조금 못 미친다
        v = C.peak_rates(GOOD)[0]
        self.assertLessEqual(v, P['vmax'] + 1e-9)
        self.assertGreater(v, 0.9 * P['vmax'])

    def test_twice_as_fast_breaks_speed_and_accel(self):
        fast = copy.deepcopy(GOOD)
        for d in fast['drones']:
            for k in d['keyframes']:
                k[0] = k[0] / 2
        fast['duration'] /= 2
        r = by_name(C.check(fast, P))
        self.assertFalse(r['최고 속도'][1])
        self.assertFalse(r['최고 가속도'][1])

    def test_altitude_limit(self):
        r = by_name(C.check(GOOD, P, zmax=10.0))
        self.assertFalse(r['고도'][1])
        high = max(k[3] for d in GOOD['drones'] for k in d['keyframes'])
        self.assertTrue(by_name(C.check(GOOD, P, zmax=high))['고도'][1])

    def test_below_ground_fails(self):
        low = copy.deepcopy(GOOD)
        low['drones'][0]['keyframes'][0][3] = -0.5
        self.assertFalse(by_name(C.check(low, P))['고도'][1])

    def test_flight_time_boundary(self):
        # 경계: 쇼 길이 == 비행시간 이면 통과, 넘으면 실패
        ft = motor.flight_time(P)
        edge = dict(GOOD, duration=ft)
        self.assertTrue(by_name(C.check(edge, P))['비행시간'][1])
        over = dict(GOOD, duration=ft + 0.01)
        self.assertFalse(by_name(C.check(over, P))['비행시간'][1])

    def test_main_exit_code(self):
        path = os.path.join(HERE, '..', '..', 'scratch',
                            'p16_check.json')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for show, want in ((GOOD, 0), (TIGHT, 1)):
            with io.open(path, 'w', encoding='utf-8') as f:
                f.write(SH.dumps(show))
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(C.main([path]), want)
            self.assertIn('최소 간격', buf.getvalue())
        os.remove(path)


if __name__ == '__main__':
    unittest.main()
