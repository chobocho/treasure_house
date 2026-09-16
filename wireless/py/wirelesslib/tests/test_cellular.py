# -*- coding: utf-8 -*-
"""cellular 모듈의 증인 시험.

셀룰러의 착상은 하나다. "멀리 떨어지면 같은 주파수를 다시 써도 된다."
그 착상을 숫자로 만든 것이 재사용 거리와 SIR 이고, 그 셀에 회선을
몇 개 둘지를 정하는 것이 얼랑 식이다.

  · 클러스터 크기가 N = i² + ij + j² 꼴만 나오는가
  · 재사용 거리비가 √(3N) 인가, N=7·γ=4 의 SIR 이 18.7 dB 인가
  · 얼랑 B(A=10, N=15) 가 표의 값 0.0365 와 맞는가
  · 얼랑 C 가 얼랑 B 보다 큰가 (기다릴 수 있으면 막히는 일이 는다)
  · 회선을 한 통에 모으면 효율이 오르는가 (트렁킹 이득)
  · 히스테리시스가 핑퐁 핸드오프를 줄이는가
"""
import math
import unittest

from wirelesslib import cellular


class TestReuse(unittest.TestCase):
    def test_cluster_sizes(self):
        """N = i²+ij+j² — 1·3·4·7·9·12·13·16·19·21 …"""
        got = cellular.cluster_sizes(4)
        for n in (1, 3, 4, 7, 9, 12, 13, 16, 19, 21):
            self.assertIn(n, got)
        for n in (2, 5, 6, 8, 10, 11, 14, 15):
            self.assertNotIn(n, got)

    def test_reuse_distance_ratio(self):
        for n in (3, 4, 7, 12):
            self.assertAlmostEqual(cellular.reuse_ratio(n),
                                   math.sqrt(3.0 * n), places=12)

    def test_sir_for_n7_gamma4(self):
        """가장 많이 인용되는 값 — N=7, γ=4 에서 약 18.7 dB."""
        self.assertAlmostEqual(cellular.sir_db(7, 4.0), 18.66,
                               places=2)

    def test_bigger_cluster_is_cleaner(self):
        prev = -99.0
        for n in (3, 4, 7, 12, 19):
            v = cellular.sir_db(n, 4.0)
            self.assertGreater(v, prev)
            prev = v

    def test_sectoring_raises_sir(self):
        """섹터 안테나가 간섭원 수를 줄인다 — 3섹터면 6 → 2."""
        omni = cellular.sir_db(7, 4.0, interferers=6)
        three = cellular.sir_db(7, 4.0, interferers=2)
        self.assertAlmostEqual(three - omni,
                               10 * math.log10(3.0), places=9)

    def test_capacity_per_cell_falls_with_cluster(self):
        """클러스터가 크면 깨끗한 대신 셀마다 쓸 채널이 줄어든다."""
        a = cellular.channels_per_cell(395, 3)
        b = cellular.channels_per_cell(395, 7)
        self.assertGreater(a, b)

    def test_rejects_invalid_cluster(self):
        with self.assertRaises(ValueError):
            cellular.sir_db(5, 4.0)


class TestErlang(unittest.TestCase):
    def test_erlang_b_table_value(self):
        """A=10 얼랑, 회선 15개 → 차단률 0.0365 (표준 표)."""
        self.assertAlmostEqual(cellular.erlang_b(10.0, 15), 0.0365,
                               places=4)

    def test_erlang_b_more_values(self):
        self.assertAlmostEqual(cellular.erlang_b(1.0, 1), 0.5,
                               places=9)
        self.assertAlmostEqual(cellular.erlang_b(2.0, 2), 0.4,
                               places=9)
        self.assertAlmostEqual(cellular.erlang_b(0.0, 5), 0.0,
                               places=12)

    def test_erlang_b_falls_with_channels(self):
        prev = 1.1
        for n in range(1, 30):
            v = cellular.erlang_b(10.0, n)
            self.assertLess(v, prev)
            prev = v

    def test_erlang_b_rises_with_load(self):
        prev = -1.0
        for a in (1.0, 5.0, 10.0, 20.0):
            v = cellular.erlang_b(a, 15)
            self.assertGreater(v, prev)
            prev = v

    def test_erlang_c_exceeds_b(self):
        """기다릴 수 있으면 '막힘' 의 뜻이 달라진다 — C 가 더 크다."""
        for a, n in ((5.0, 8), (10.0, 15), (20.0, 25)):
            self.assertGreater(cellular.erlang_c(a, n),
                               cellular.erlang_b(a, n))

    def test_erlang_c_needs_stable_queue(self):
        with self.assertRaises(ValueError):
            cellular.erlang_c(20.0, 15)      # A ≥ N 이면 큐가 터진다

    def test_offered_load_for_gos(self):
        a = cellular.offered_load(15, 0.02)
        self.assertAlmostEqual(cellular.erlang_b(a, 15), 0.02,
                               places=6)

    def test_trunking_gain(self):
        """회선을 한 통에 모을수록 회선당 실어 나르는 양이 는다."""
        small = cellular.offered_load(10, 0.02) / 10.0
        big = cellular.offered_load(100, 0.02) / 100.0
        self.assertGreater(big, small)
        self.assertLess(big, 1.0)


class TestHandoff(unittest.TestCase):
    def test_hysteresis_reduces_ping_pong(self):
        a = cellular.ping_pong_count(hysteresis_db=0.0, seed=3)
        b = cellular.ping_pong_count(hysteresis_db=6.0, seed=3)
        self.assertLess(b, a)

    def test_no_handoff_when_always_stronger(self):
        self.assertEqual(
            cellular.ping_pong_count(hysteresis_db=3.0, seed=5,
                                     bias_db=40.0), 0)


class TestBreathing(unittest.TestCase):
    def test_radius_shrinks_with_load(self):
        """CDMA 셀은 사람이 늘면 작아진다 — 셀 호흡."""
        prev = 1e9
        for load in (0.1, 0.3, 0.5, 0.7):
            r = cellular.breathing_radius(load, gamma=4.0)
            self.assertLess(r, prev)
            prev = r

    def test_empty_cell_is_full_size(self):
        self.assertAlmostEqual(cellular.breathing_radius(0.0, 4.0),
                               1.0, places=12)

    def test_full_load_collapses(self):
        self.assertAlmostEqual(cellular.breathing_radius(1.0, 4.0),
                               0.0, places=12)


if __name__ == '__main__':
    unittest.main()
