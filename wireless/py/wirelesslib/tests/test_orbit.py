# -*- coding: utf-8 -*-
"""orbit 모듈의 증인 시험.

위성 이야기의 숫자는 전부 케플러에서 나온다. 높이를 정하면 주기·속도·
지연·도플러·발자국이 줄줄이 따라 나오고, 그 값들이 곧 NTN 규격이 왜
그렇게 생겼는지를 설명한다.

  · 정지궤도의 주기가 **항성일**(23시간 56분 4초)인가 — 24시간이 아니다
  · 그 조건에서 고도가 35,786 km 인가
  · 케플러 제3법칙 T² ∝ a³ 이 성립하는가
  · 550 km 궤도의 주기가 약 95.6분, 속도가 약 7.59 km/s 인가
  · 천정 통과 때 편도 지연이 h/c 이고, 낮은 앙각에서 늘어나는가
  · 2 GHz 에서 550 km 저궤도의 최대 도플러가 ±47 kHz 쯤인가
"""
import math
import unittest

from wirelesslib import orbit


class TestKepler(unittest.TestCase):
    def test_geo_period_is_a_sidereal_day(self):
        """정지궤도의 주기는 항성일이다 — 24시간이 아니라 23h56m4s."""
        # 정지궤도 고도는 적도 반지름 위의 값이다. 평균 반지름을
        # 섞어 쓰면 22초가 어긋난다 — 그래서 기준을 같이 넘긴다.
        t = orbit.period_s(orbit.geo_altitude_km(),
                           orbit.EARTH_EQ_R_KM)
        self.assertAlmostEqual(t, orbit.SIDEREAL_DAY_S, delta=1.0)
        h = int(t // 3600)
        m = int((t - h * 3600) // 60)
        self.assertEqual((h, m), (23, 56))

    def test_geo_altitude(self):
        self.assertAlmostEqual(orbit.geo_altitude_km(), 35786.0,
                               delta=2.0)

    def test_keplers_third_law(self):
        """T² / a³ 은 높이에 상관없이 같은 값이다."""
        vals = []
        for h in (200.0, 550.0, 1200.0, 8000.0, 35786.0):
            a = orbit.EARTH_R_KM + h
            vals.append(orbit.period_s(h) ** 2 / a ** 3)
        for v in vals[1:]:
            self.assertAlmostEqual(v / vals[0], 1.0, places=9)

    def test_leo_period_and_speed(self):
        self.assertAlmostEqual(orbit.period_s(550.0) / 60.0, 95.6,
                               delta=0.2)
        self.assertAlmostEqual(orbit.speed_ms(550.0) / 1000.0, 7.59,
                               delta=0.02)

    def test_higher_is_slower(self):
        prev = 1e9
        for h in (300.0, 550.0, 1200.0, 20200.0, 35786.0):
            v = orbit.speed_ms(h)
            self.assertLess(v, prev)
            prev = v

    def test_negative_altitude_rejected(self):
        with self.assertRaises(ValueError):
            orbit.period_s(-10.0)


class TestGeometry(unittest.TestCase):
    def test_zenith_slant_range_is_the_altitude(self):
        for h in (550.0, 1200.0, 35786.0):
            self.assertAlmostEqual(orbit.slant_range_km(h, 90.0), h,
                                   places=6)

    def test_slant_range_grows_as_elevation_falls(self):
        prev = 0.0
        for el in (90.0, 60.0, 40.0, 25.0, 10.0, 5.0):
            d = orbit.slant_range_km(550.0, el)
            self.assertGreater(d, prev)
            prev = d

    def test_starlink_like_delay_window(self):
        """550 km 궤도의 편도 지연은 천정 1.8 ms, 25° 에서 3.7 ms 쯤."""
        self.assertAlmostEqual(orbit.one_way_delay_ms(550.0, 90.0),
                               1.83, places=2)
        self.assertAlmostEqual(orbit.one_way_delay_ms(550.0, 25.0),
                               3.74, delta=0.05)

    def test_geo_delay(self):
        """정지궤도 편도 119 ms.

        왕복 238 ms 가 위성 통화의 어색함을 만든다.
        """
        self.assertAlmostEqual(orbit.one_way_delay_ms(35786.0, 90.0),
                               119.4, delta=0.2)

    def test_footprint_grows_with_altitude(self):
        prev = 0.0
        for h in (550.0, 1200.0, 20200.0, 35786.0):
            r = orbit.footprint_radius_km(h, 10.0)
            self.assertGreater(r, prev)
            prev = r

    def test_central_angle_consistency(self):
        """중심각·앙각·슬랜트 거리는 한 삼각형의 세 요소다."""
        h, el = 550.0, 30.0
        d = orbit.slant_range_km(h, el)
        g = orbit.central_angle_deg(h, el)
        r = orbit.EARTH_R_KM
        # 코사인 법칙으로 되짚어 같은 거리가 나와야 한다
        back = math.sqrt(r ** 2 + (r + h) ** 2 - 2 * r * (r + h)
                         * math.cos(math.radians(g)))
        self.assertAlmostEqual(d, back, places=6)

    def test_elevation_out_of_range(self):
        with self.assertRaises(ValueError):
            orbit.slant_range_km(550.0, 95.0)


class TestDoppler(unittest.TestCase):
    def test_zero_at_closest_approach(self):
        self.assertAlmostEqual(orbit.doppler_hz(550.0, 2.0e9, 0.0),
                               0.0, places=6)

    def test_max_doppler_for_leo(self):
        """2 GHz·550 km 천정 통과에서 최대 ±47 kHz 쯤.

        NTN 이 궤도력을 내려보내 미리 보정하게 하는 값이다.
        """
        d = orbit.max_doppler_hz(550.0, 2.0e9)
        self.assertAlmostEqual(d / 1000.0, 46.6, delta=1.0)

    def test_doppler_scales_with_frequency(self):
        a = orbit.max_doppler_hz(550.0, 2.0e9)
        b = orbit.max_doppler_hz(550.0, 20.0e9)
        self.assertAlmostEqual(b / a, 10.0, places=6)

    def test_geo_doppler_vanishes_with_earth_rotation(self):
        """정지궤도는 지구와 함께 돈다.

        상대 각속도가 0 이라 도플러도 0 이다.

        자전을 빼지 않은 모형에서는 3 kHz 쯤이 남는다. 그 차이가
        '정지궤도' 라는 말의 뜻이다.
        """
        h = orbit.geo_altitude_km()
        self.assertLess(
            orbit.max_doppler_hz(h, 2.0e9, earth_rotation=True), 1.0)
        self.assertGreater(orbit.max_doppler_hz(h, 2.0e9), 1000.0)

    def test_pass_is_antisymmetric(self):
        for th in (5.0, 12.0, 20.0):
            a = orbit.doppler_hz(550.0, 2.0e9, th)
            b = orbit.doppler_hz(550.0, 2.0e9, -th)
            self.assertAlmostEqual(a, -b, places=6)


class TestNTN(unittest.TestCase):
    def test_timing_advance_window(self):
        """빔 안에서 왕복 지연이 얼마나 벌어지는가.

        그 폭이 곧 타이밍 어드밴스의 범위다.
        """
        lo, hi = orbit.ta_window_ms(550.0, 25.0, 90.0)
        self.assertLess(lo, hi)
        self.assertAlmostEqual(lo, 2 * orbit.one_way_delay_ms(550.0,
                                                              90.0),
                               places=6)

    def test_geo_needs_much_bigger_window(self):
        leo = orbit.ta_window_ms(550.0, 10.0, 90.0)
        geo = orbit.ta_window_ms(35786.0, 10.0, 90.0)
        self.assertGreater(geo[1] - geo[0], leo[1] - leo[0])

    def test_visibility_time(self):
        """한 위성이 보이는 시간.

        저궤도에서는 몇 분뿐이라 자주 넘겨야 한다.
        """
        t = orbit.visibility_s(550.0, 25.0)
        self.assertGreater(t, 60.0)
        self.assertLess(t, 600.0)


if __name__ == '__main__':
    unittest.main()
