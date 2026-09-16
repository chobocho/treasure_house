# -*- coding: utf-8 -*-
"""harq 모듈의 증인 시험.

재전송은 '또 보내면 좋아진다' 로 넘어가기 쉬운 자리다. 무엇이 좋아지고
왜 좋아지는지를 숫자로 붙잡는다.

  · 부블록 인터리버가 순열인가, 열 차례가 5비트 역순인가
  · 순환 버퍼의 길이가 3·Kπ 인가, RV0 이 계통 비트부터 시작하는가
  · 네 RV 를 모두 보내면 버퍼의 모든 자리가 한 번은 나가는가
  · **체이스 결합** — 같은 것을 두 번 받으면 LLR 이 두 배가 되어
    3 dB 를 번다
  · **증분 잉여(IR)** — 같은 횟수라면 IR 이 체이스보다 낫다
  · 처리율이 용량을 넘지 않는다
"""
import math
import unittest

from wirelesslib import harq, info


class TestSubblock(unittest.TestCase):
    def test_column_order_is_bit_reversal(self):
        """LTE 의 32열 치환은 5비트 역순과 같다.

        외울 표가 아니라 규칙이다.
        """
        want = [int('{:05b}'.format(j)[::-1], 2) for j in range(32)]
        self.assertEqual(harq.COL_PERM, want)

    def test_is_a_permutation(self):
        for n in (44, 100, 333):
            perm = harq.subblock_perm(n)
            self.assertEqual(sorted(x for x in perm if x is not None),
                             list(range(n)))

    def test_length_is_padded_to_32_columns(self):
        for n in (44, 100, 333):
            perm = harq.subblock_perm(n)
            self.assertEqual(len(perm) % 32, 0)
            self.assertGreaterEqual(len(perm), n)


class TestCircularBuffer(unittest.TestCase):
    def setUp(self):
        self.k = 40
        self.d = harq.streams(self.k, f1=3, f2=10, seed=1)

    def test_buffer_length(self):
        buf = harq.circular_buffer(self.d)
        kpi = len(harq.subblock_perm(len(self.d[0])))
        self.assertEqual(len(buf), 3 * kpi)

    def test_rv0_is_mostly_systematic(self):
        """RV0 은 혼자서도 복호가 되어야 한다 — 계통 비트가 주로 나간다.

        버퍼 안의 계통 스트림은 이미 부블록 인터리버를 지난 뒤라
        '앞에서부터 그대로' 는 아니다. 보아야 할 것은 차례가 아니라
        **어느 스트림에서 왔는가** 다.
        """
        pos = harq.rate_match_positions(self.d, 48, rv=0)
        buf = harq.circular_buffer(self.d)
        froms = [buf[p][0] for p in pos]
        self.assertGreater(froms.count(0) / float(len(froms)), 0.6)

    def test_rv2_is_mostly_parity(self):
        pos = harq.rate_match_positions(self.d, 48, rv=2)
        buf = harq.circular_buffer(self.d)
        froms = [buf[p][0] for p in pos]
        self.assertLess(froms.count(0) / float(len(froms)), 0.4)

    def test_four_rvs_cover_the_buffer(self):
        seen = set()
        buf = harq.circular_buffer(self.d)
        live = sum(1 for v in buf if v is not None)
        for rv in range(4):
            seen |= set(harq.rate_match_positions(self.d, live // 3,
                                                  rv))
        self.assertEqual(len(seen), live)

    def test_rate_match_length(self):
        for e in (30, 132, 400):
            self.assertEqual(len(harq.rate_match(self.d, e, rv=0)), e)


class TestCombining(unittest.TestCase):
    def test_chase_doubles_the_llr(self):
        """같은 자리를 두 번 받으면 연판정 값이 더해진다.

        그 덧셈이 곧 3 dB 다.
        """
        d = harq.streams(40, 3, 10, seed=2)
        a = harq.soft_buffer(d, [(0, [1.0] * 60)])
        b = harq.soft_buffer(d, [(0, [1.0] * 60), (0, [1.0] * 60)])
        pairs = [(x, y) for x, y in zip(a, b) if x]
        self.assertTrue(pairs)
        for x, y in pairs:
            self.assertAlmostEqual(y, 2.0 * x, places=9)

    def test_ir_is_not_worse_than_chase(self):
        cc = harq.bler(1.0, transmissions=2, frames=40, k=40,
                       elen=72, seed=5, mode='chase')
        ir = harq.bler(1.0, transmissions=2, frames=40, k=40,
                       elen=72, seed=5, mode='ir')
        self.assertLessEqual(ir, cc)

    def test_more_transmissions_help(self):
        prev = 1.1
        for t in (1, 2, 3):
            v = harq.bler(0.0, transmissions=t, frames=30, k=40,
                          elen=72, seed=7, mode='ir')
            self.assertLessEqual(v, prev)
            prev = v

    def test_throughput_never_exceeds_capacity(self):
        """처리율은 그 SNR 의 섀넌 용량을 넘을 수 없다."""
        for ebn0 in (0.0, 2.0, 5.0):
            k, elen = 40, 72
            th = harq.throughput(ebn0, transmissions=3, frames=30,
                                 k=k, elen=elen, seed=9)
            rate = float(k) / elen
            esn0 = ebn0 + 10.0 * math.log10(rate)
            self.assertLessEqual(th, info.capacity_awgn(esn0) + 1e-9)

    def test_unknown_mode(self):
        with self.assertRaises(ValueError):
            harq.bler(1.0, 2, 5, 40, 72, seed=1, mode='magic')


if __name__ == '__main__':
    unittest.main()
