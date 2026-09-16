# -*- coding: utf-8 -*-
"""link 모듈의 증인 시험.

링크 버짓은 이 책에서 가장 실무에 가까운 계산이다. dB 를 더하고 빼는
것뿐이지만, 항을 하나 빠뜨리거나 부호를 뒤집으면 셀 반지름이 두 배로
틀린다. 그래서 손으로 계산한 표와 0.1 dB 안에서 맞대어 본다.

  · 290 K 의 열잡음 밀도가 −173.98 dBm/Hz 인가
  · 10 MHz·NF 3 dB 의 잡음 바닥이 −101 dBm 인가
  · EIRP·경로손실·수신 이득을 더한 값이 손 계산과 맞는가
  · 여유(margin)가 요구 SNR 을 넘긴 만큼인가
  · 요구 SNR 을 BER 목표에서 거꾸로 구할 수 있는가
"""
import math
import unittest

from wirelesslib import channel, link, modem


class TestNoise(unittest.TestCase):
    def test_thermal_density_at_290k(self):
        """kT = −173.98 dBm/Hz — 이 책에서 가장 자주 쓰는 상수."""
        self.assertAlmostEqual(link.thermal_noise_dbm(1.0, 290.0),
                               -173.98, places=2)

    def test_bandwidth_adds_ten_log(self):
        a = link.thermal_noise_dbm(1.0)
        b = link.thermal_noise_dbm(1.0e7)
        self.assertAlmostEqual(b - a, 70.0, places=9)

    def test_noise_floor_with_nf(self):
        self.assertAlmostEqual(link.noise_floor_dbm(1.0e7, 3.0),
                               -100.98, places=2)

    def test_colder_is_quieter(self):
        self.assertLess(link.thermal_noise_dbm(1.0, 100.0),
                        link.thermal_noise_dbm(1.0, 290.0))

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            link.thermal_noise_dbm(0.0)


class TestTerms(unittest.TestCase):
    def test_eirp(self):
        self.assertAlmostEqual(link.eirp_dbm(43.0, 17.0, 2.0), 58.0,
                               places=9)

    def test_gt(self):
        """G/T — 안테나 이득을 시스템 잡음온도로 나눈 것.

        위성 지구국의 성능을 한 수로 말할 때 쓴다.
        """
        self.assertAlmostEqual(link.gt_db(30.0, 100.0),
                               30.0 - 10 * math.log10(100.0),
                               places=9)

    def test_noise_temp_from_figure(self):
        """NF 3 dB → 잡음온도 약 289 K (290 K 기준)."""
        self.assertAlmostEqual(link.noise_temp_k(3.0), 288.6,
                               delta=1.0)
        self.assertAlmostEqual(link.noise_temp_k(0.0), 0.0, places=9)

    def test_figure_and_temp_are_inverse(self):
        for nf in (0.5, 2.0, 5.0, 10.0):
            t = link.noise_temp_k(nf)
            self.assertAlmostEqual(link.noise_figure_db(t), nf,
                                   places=9)


class TestBudget(unittest.TestCase):
    def test_hand_computed_case(self):
        """손으로 계산한 표와 0.1 dB 안에서 맞아야 한다.

        Ptx 23 dBm · Gtx 0 dBi · 1 km·2 GHz 자유공간 · Grx 18 dBi ·
        NF 3 dB · 10 MHz →  Prx = 23 − 98.47 + 18 = −57.47 dBm,
        잡음 바닥 −100.98 dBm, SNR 43.5 dB.
        """
        b = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=18.0,
                        path_loss_db=channel.fspl_db(1000.0, 2.0e9),
                        bw_hz=1.0e7, nf_db=3.0, required_snr_db=10.0)
        self.assertAlmostEqual(b['eirp_dbm'], 23.0, places=6)
        self.assertAlmostEqual(b['prx_dbm'], -57.47, delta=0.05)
        self.assertAlmostEqual(b['noise_dbm'], -100.98, delta=0.05)
        self.assertAlmostEqual(b['snr_db'], 43.51, delta=0.05)
        self.assertAlmostEqual(b['margin_db'], 33.51, delta=0.05)

    def test_margin_is_snr_minus_required(self):
        b = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=0.0,
                        path_loss_db=120.0, bw_hz=1.0e6, nf_db=5.0,
                        required_snr_db=7.0)
        self.assertAlmostEqual(b['margin_db'],
                               b['snr_db'] - 7.0, places=9)

    def test_losses_subtract(self):
        a = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=0.0,
                        path_loss_db=120.0, bw_hz=1.0e6, nf_db=5.0,
                        required_snr_db=7.0)
        b = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=0.0,
                        path_loss_db=120.0, bw_hz=1.0e6, nf_db=5.0,
                        required_snr_db=7.0, other_loss_db=6.0)
        self.assertAlmostEqual(a['margin_db'] - b['margin_db'], 6.0,
                               places=9)

    def test_max_range_solves_the_budget(self):
        """여유가 0 이 되는 거리 — 그 거리가 곧 셀 반지름이다."""
        d = link.max_range_m(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=18.0,
                             f_hz=2.0e9, bw_hz=1.0e7, nf_db=3.0,
                             required_snr_db=10.0)
        b = link.budget(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=18.0,
                        path_loss_db=channel.fspl_db(d, 2.0e9),
                        bw_hz=1.0e7, nf_db=3.0, required_snr_db=10.0)
        self.assertAlmostEqual(b['margin_db'], 0.0, places=6)

    def test_presets_exist_and_close(self):
        for name in link.PRESETS:
            b = link.preset_budget(name)
            self.assertIn('margin_db', b)
            self.assertIsInstance(b['margin_db'], float)

    def test_satellite_needs_more_gain(self):
        """정지궤도는 경로손실이 200 dB 대다.

        안테나 이득으로 메울 수밖에 없다.
        """
        geo = link.preset_budget('geo_downlink')
        self.assertGreater(geo['path_loss_db'], 190.0)


class TestSensitivity(unittest.TestCase):
    def test_sensitivity_is_noise_plus_required_snr(self):
        s = link.sensitivity_dbm(1.0e7, 3.0, 10.0)
        self.assertAlmostEqual(s, link.noise_floor_dbm(1.0e7, 3.0)
                               + 10.0, places=9)

    def test_required_snr_for_ber(self):
        """BER 목표에서 요구 SNR 을 거꾸로 구한다."""
        for name, ber in (('bpsk', 1e-3), ('qpsk', 1e-4),
                          ('16qam', 1e-3)):
            snr = link.required_ebn0_db(name, ber)
            self.assertAlmostEqual(modem.ber_theory(name, snr), ber,
                                   delta=ber * 0.01)

    def test_higher_order_needs_more(self):
        a = link.required_ebn0_db('qpsk', 1e-4)
        b = link.required_ebn0_db('16qam', 1e-4)
        c = link.required_ebn0_db('64qam', 1e-4)
        self.assertLess(a, b)
        self.assertLess(b, c)

    def test_unreachable_ber(self):
        with self.assertRaises(ValueError):
            link.required_ebn0_db('bpsk', 0.6)


if __name__ == '__main__':
    unittest.main()
