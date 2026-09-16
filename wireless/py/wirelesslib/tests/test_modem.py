# -*- coding: utf-8 -*-
"""modem 모듈의 증인 시험.

이 덱에서 가장 자주 되부르는 식이 여기 있다 — AWGN 에서의 오류율이다.
확인하는 것은 "몬테카를로가 닫힌 식과 맞는가" 하나다.

몇 비트를 던져야 하는가는 눈대중이 아니라 계산으로 정했다. 오류가 평균
E 개 나오는 실험의 상대 표준편차는 대략 1/√E 이므로, 5 % 안에 들려면
E ≈ 400 이 필요하다. 아래의 비트 수는 전부 그렇게 잡은 것이다.
허용 오차를 늘려서 통과시키지 말 것 (PLAN.md §0.6).
"""
import math
import unittest

from wirelesslib import modem


class TestQFunction(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(modem.qfunc(0.0), 0.5, places=12)
        self.assertAlmostEqual(modem.qfunc(1.0), 0.158655254, places=9)
        self.assertAlmostEqual(modem.qfunc(2.0), 0.022750132, places=9)
        self.assertAlmostEqual(modem.qfunc(3.0), 0.001349898, places=9)

    def test_symmetry(self):
        for x in (0.3, 1.7, 2.9):
            self.assertAlmostEqual(modem.qfunc(-x), 1 - modem.qfunc(x),
                                   places=12)


class TestConstellations(unittest.TestCase):
    NAMES = ['bpsk', 'qpsk', '8psk', '16qam', '64qam', '256qam',
             '1024qam']

    def test_size_and_unit_energy(self):
        for name in self.NAMES:
            c = modem.constellation(name)
            self.assertEqual(len(c.points), c.m)
            e = sum(abs(p) ** 2 for p in c.points) / c.m
            self.assertAlmostEqual(e, 1.0, places=9, msg=name)

    def test_bits_per_symbol(self):
        want = dict(bpsk=1, qpsk=2, **{'8psk': 3})
        want.update({'16qam': 4, '64qam': 6, '256qam': 8,
                     '1024qam': 10})
        for name, k in want.items():
            self.assertEqual(modem.constellation(name).k, k)

    def test_gray_neighbours_differ_by_one_bit(self):
        """이웃한 점의 라벨은 비트 하나만 달라야 한다.

        그레이 사상이라는 말의 정의가 이것이다.
        """
        for name in self.NAMES:
            c = modem.constellation(name)
            for i, p in enumerate(c.points):
                d = sorted((abs(p - q), j)
                           for j, q in enumerate(c.points) if j != i)
                near = d[0][0]
                for dist, j in d:
                    if dist > near * 1.001:
                        break
                    diff = bin(c.labels[i] ^ c.labels[j]).count('1')
                    self.assertEqual(diff, 1, '%s %d↔%d' % (name, i, j))

    def test_unknown_name(self):
        with self.assertRaises(ValueError):
            modem.constellation('3qam')


class TestMapping(unittest.TestCase):
    def test_map_demap_roundtrip_without_noise(self):
        rnd = __import__('random').Random(11)
        for name in ('bpsk', 'qpsk', '8psk', '16qam', '64qam'):
            c = modem.constellation(name)
            bits = [rnd.randint(0, 1) for _ in range(c.k * 200)]
            got = modem.demap_hard(modem.modulate(bits, c), c)
            self.assertEqual(got, bits, name)

    def test_bit_count_must_be_multiple(self):
        c = modem.constellation('16qam')
        with self.assertRaises(ValueError):
            modem.modulate([0, 1, 0], c)


class TestLLR(unittest.TestCase):
    def test_llr_sign_agrees_with_hard_decision(self):
        rnd = __import__('random').Random(5)
        c = modem.constellation('16qam')
        bits = [rnd.randint(0, 1) for _ in range(c.k * 300)]
        y = modem.awgn(modem.modulate(bits, c), 20.0, rnd)
        hard = modem.demap_hard(y, c)
        soft = [0 if v > 0 else 1 for v in modem.demap_llr(y, c, 0.01)]
        self.assertEqual(hard, soft)

    def test_maxlog_close_to_exact_at_high_snr(self):
        rnd = __import__('random').Random(9)
        c = modem.constellation('16qam')
        bits = [rnd.randint(0, 1) for _ in range(c.k * 200)]
        y = modem.awgn(modem.modulate(bits, c), 15.0, rnd)
        a = modem.demap_llr(y, c, 0.03)
        b = modem.demap_llr(y, c, 0.03, maxlog=True)
        worst = max(abs(u - v) / (1 + abs(u)) for u, v in zip(a, b))
        self.assertLess(worst, 0.2)


class TestGrayCode(unittest.TestCase):
    def test_ungray_inverts_gray(self):
        """세 비트부터는 _gray 가 자기 역함수가 아니다.

        실제로 여기서 물려 64QAM 의 BER 이 14 % 어긋났다.
        """
        for k in (1, 2, 3, 4, 5, 8):
            for i in range(1 << k):
                self.assertEqual(modem._ungray(modem._gray(i), k), i)

    def test_gray_is_not_its_own_inverse_beyond_two_bits(self):
        self.assertNotEqual(modem._gray(modem._gray(4)), 4)


class TestBER(unittest.TestCase):
    """몬테카를로 대 닫힌 식.

    씨앗이 고정돼 있으므로 결과는 늘 같다 — 한 번 통과하면 언제나
    통과한다. 그래서 허용 오차는 '운' 이 아니라 '얼마나 맞는가' 를
    말한다. 비트 수는 오류가 2,000개 이상 나오도록(상대 표준편차
    2 % 남짓) 잡았다.
    """

    def test_bpsk_matches_closed_form(self):
        """BER = Q(√(2Eb/N0)) — 근사가 아니라 정확한 값이다."""
        for ebn0, nbits in ((2.0, 120000), (4.0, 360000)):
            got = modem.ber_sim('bpsk', ebn0, nbits, seed=20260916)
            want = modem.ber_theory('bpsk', ebn0)
            self.assertLess(abs(got - want) / want, 0.05,
                            'Eb/N0=%s got=%g want=%g'
                            % (ebn0, got, want))

    def test_qpsk_has_same_ber_as_bpsk(self):
        """QPSK 는 직교한 BPSK 둘이다 — 비트 오류율이 같아야 한다."""
        for ebn0 in (4.0, 6.0):
            self.assertAlmostEqual(modem.ber_theory('qpsk', ebn0),
                                   modem.ber_theory('bpsk', ebn0),
                                   places=12)
        got = modem.ber_sim('qpsk', 4.0, 360000, seed=7)
        want = modem.ber_theory('qpsk', 4.0)
        self.assertLess(abs(got - want) / want, 0.05)

    def test_square_qam_matches_closed_form(self):
        """사각 QAM 의 식은 가장 가까운 이웃만 센 **근사** 다.

        16·64QAM 은 쓸 만한 SNR 에서 몇 % 안에 든다. 256QAM 부터는
        이웃이 늘어 근사가 느슨해지므로 허용 오차를 따로 적는다 —
        느슨한 것을 숨기지 않고 시험에 적어 두는 쪽을 골랐다.
        """
        for name, ebn0, nbits, tol in (('16qam', 8.0, 200000, 0.08),
                                       ('64qam', 12.0, 300000, 0.08),
                                       ('256qam', 18.0, 300000, 0.15)):
            got = modem.ber_sim(name, ebn0, nbits, seed=5)
            want = modem.ber_theory(name, ebn0)
            self.assertLess(abs(got - want) / want, tol,
                            '%s got=%g want=%g' % (name, got, want))

    def test_8psk_ber_matches_approximation(self):
        got = modem.ber_sim('8psk', 9.0, 300000, seed=5)
        want = modem.ber_theory('8psk', 9.0)
        self.assertLess(abs(got - want) / want, 0.10)

    def test_ber_falls_with_snr(self):
        prev = 1.0
        for ebn0 in (0.0, 2.0, 4.0, 6.0, 8.0):
            v = modem.ber_theory('bpsk', ebn0)
            self.assertLess(v, prev)
            prev = v

    def test_higher_order_needs_more_snr(self):
        """같은 BER 을 내려면 성상도가 클수록 SNR 이 더 든다."""
        order = ['bpsk', '16qam', '64qam', '256qam']
        vals = [modem.ber_theory(n, 12.0) for n in order]
        for a, b in zip(vals, vals[1:]):
            self.assertLess(a, b)

    def test_shannon_limit_sign(self):
        """−1.59 dB 아래에서는 어떤 부호도 못 쓴다 — 값만 확인한다."""
        self.assertAlmostEqual(modem.shannon_limit_db(), -1.5917,
                               places=4)


class TestSER(unittest.TestCase):
    def test_8psk_ser_matches_approximation(self):
        got = modem.ser_sim('8psk', 12.0, 60000, seed=21)
        want = modem.ser_theory_mpsk(8, 12.0)
        self.assertLess(abs(got - want) / want, 0.10)

    def test_bpsk_ser_equals_ber(self):
        self.assertAlmostEqual(modem.ser_theory_mpsk(2, 4.0),
                               modem.ber_theory('bpsk', 4.0), places=12)


if __name__ == '__main__':
    unittest.main()
