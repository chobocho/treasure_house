# -*- coding: utf-8 -*-
"""cascade 시험 — 위치→속도→자세→각속도 캐스케이드가 실제로 난다.

물리 모드(SPEC §4)와 제어기(SPEC §5)를 한 대로 묶어 돌린다.
시간이 드는 시험이라 걸음 수를 아낀다(합계 수십 초).
"""
import math
import unittest

from droneshow import params
from droneshow import quat as Q
from droneshow import sim
from droneshow import vec3 as V


def hold(x, y, z, yaw=0.0):
    return lambda t: {'p': [x, y, z], 'yaw': yaw}


def circle(r=2.0, w=0.8, z=5.0, ff=True):
    def ref(t):
        c, s = math.cos(w * t), math.sin(w * t)
        out = {'p': [r * c, r * s, z], 'yaw': 0.0}
        if ff:
            out['v'] = [-r * w * s, r * w * c, 0.0]
            out['a'] = [-r * w * w * c, -r * w * w * s, 0.0]
        return out
    return ref


def tilt(s):
    z = Q.rotate(s[6:10], [0.0, 0.0, 1.0])
    return math.degrees(math.acos(max(-1.0, min(1.0, z[2]))))


class Hover(unittest.TestCase):
    def test_hover_stays_put(self):
        p = params.load()
        rows = sim.fly(p, hold(0, 0, 5), 2.0, start=[0, 0, 5])
        self.assertLess(V.dist(rows[-1]['s'][0:3], [0, 0, 5]), 1e-6)


class Steps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = params.load()
        cls.x = sim.fly(cls.p, hold(1, 0, 5), 8.0, start=[0, 0, 5])

    def test_reaches_and_settles(self):
        s = self.x[-1]['s']
        self.assertLess(V.dist(s[0:3], [1, 0, 5]), 0.02)

    def test_overshoot_small(self):
        top = max(r['s'][0] for r in self.x)
        self.assertLess(top - 1.0, 0.2)

    def test_tilt_limit_respected(self):
        self.assertLess(max(tilt(r['s']) for r in self.x),
                        self.p['tilt_max_deg'] + 1.0)

    def test_altitude_step(self):
        rows = sim.fly(self.p, hold(0, 0, 6), 6.0, start=[0, 0, 5])
        self.assertLess(abs(rows[-1]['s'][2] - 6.0), 0.02)

    def test_yaw_step(self):
        rows = sim.fly(self.p, hold(0, 0, 5, math.pi / 2), 4.0,
                       start=[0, 0, 5])
        yaw = Q.to_euler(rows[-1]['s'][6:10])[2]
        self.assertLess(abs(math.degrees(yaw) - 90.0), 2.0)
        drift = max(V.dist(r['s'][0:3], [0, 0, 5]) for r in rows)
        self.assertLess(drift, 0.05)


class TimeScale(unittest.TestCase):
    """T17 — 안쪽(각속도) 루프가 바깥(자세)보다 느리면 무너진다.

    '느리다' 는 표본 주기가 아니라 대역폭(이득)의 이야기다 — 각속도
    루프를 50 Hz 로 내려도 멀쩡하지만, 이득을 자세 이득의 4분의 1 로
    내리면 한 걸음 명령에 크게 기울고 제자리에 서지 못한다."""

    def fly_step(self, cfg=None):
        p = params.load()
        return sim.fly(p, hold(1, 0, 5), 4.0, start=[0, 0, 5], cfg=cfg)

    def test_sample_rate_alone_does_not_break(self):
        good = self.fly_step()
        slow = self.fly_step({'rate_hz': 50, 'att_hz': 50})
        g = max(tilt(r['s']) for r in good)
        self.assertLess(max(tilt(r['s']) for r in slow), 1.1 * g)

    def test_slow_inner_bandwidth_breaks(self):
        good = self.fly_step()
        bad = self.fly_step({'kp_rate': 2.0, 'ki_rate': 0.0,
                             'kd_rate': 0.0})
        g = max(tilt(r['s']) for r in good)
        self.assertGreater(max(tilt(r['s']) for r in bad), 2 * g)
        self.assertGreater(abs(bad[-1]['s'][0] - 1.0), 0.5)


class Disturbance(unittest.TestCase):
    """T15 — 일정한 바람을 적분항이 지운다."""

    def test_integral_cancels_wind(self):
        p = params.load()
        wind = lambda t: [0.3, 0.0, 0.0]
        with_i = sim.fly(p, hold(0, 0, 5), 20.0, start=[0, 0, 5],
                         wind=wind)
        no_i = sim.fly(p, hold(0, 0, 5), 20.0, start=[0, 0, 5],
                       wind=wind, cfg={'ki_vel': 0.0})
        e1 = V.dist(with_i[-1]['s'][0:3], [0, 0, 5])
        e0 = V.dist(no_i[-1]['s'][0:3], [0, 0, 5])
        self.assertLess(e1, 0.01)
        self.assertGreater(e0, 0.05)


class FeedForward(unittest.TestCase):
    """T12 — 평탄 출력의 속도·가속도를 앞먹임하면 원을 따라간다."""

    def err(self, ff):
        p = params.load()
        ref = circle(ff=ff)
        rows = sim.fly(p, ref, 12.0, start=[2, 0, 5])
        return max(V.dist(r['s'][0:3], ref(r['t'])['p'])
                   for r in rows if r['t'] > 4.0)

    def test_feedforward_tracks_circle(self):
        with_ff, without = self.err(True), self.err(False)
        self.assertLess(with_ff, 0.1)
        self.assertGreater(without, 10 * with_ff)


if __name__ == '__main__':
    unittest.main()
