# -*- coding: utf-8 -*-
"""성능 분석과 자원 배치 — 로그에서 잰 값이 실제와 맞는가."""
import math
import unittest

from py.pm import allocate as AL
from py.pm import log as L
from py.pm import perf


class TestActivityStats(unittest.TestCase):
    def setUp(self):
        self.log = L.generate(n_cases=400, seed=71)

    def test_counts_match_log(self):
        st = perf.activity_stats(self.log)
        total = sum(v['count'] for v in st.values())
        self.assertEqual(total, sum(len(t) for t in self.log))

    def test_receive_is_longest(self):
        # 생성기에서 Receive 의 평균 처리시간이 48시간으로 가장 길다
        st = perf.activity_stats(self.log)
        slowest = max(st, key=lambda a: st[a]['mean_duration'])
        self.assertEqual(slowest, 'Receive')
        self.assertGreater(st['Receive']['mean_duration'], 40.0)
        self.assertLess(st['Receive']['mean_duration'], 56.0)

    def test_case_duration_positive(self):
        cs = perf.case_stats(self.log)
        self.assertGreater(cs['mean'], 0)
        self.assertLessEqual(cs['median'], cs['p90'])
        self.assertLessEqual(cs['p90'], cs['max'])


class TestBottleneck(unittest.TestCase):
    def test_shares_sum_to_one(self):
        lg = L.generate(n_cases=300, seed=72)
        bt = perf.bottlenecks(lg)
        self.assertAlmostEqual(sum(r['wait_share'] for r in bt), 1.0, places=9)
        self.assertAlmostEqual(sum(r['dur_share'] for r in bt), 1.0, places=9)

    def test_sorted_by_total_waiting(self):
        lg = L.generate(n_cases=300, seed=73)
        bt = perf.bottlenecks(lg)
        for i in range(len(bt) - 1):
            self.assertGreaterEqual(bt[i]['total_waiting'], bt[i + 1]['total_waiting'])

    def test_frequent_activity_dominates(self):
        # Request 는 반려 때문에 가장 자주 실행된다 → 총 대기가 크다
        lg = L.generate(n_cases=400, seed=74, reject_prob=0.5)
        bt = perf.bottlenecks(lg)
        top = {r['activity'] for r in bt[:3]}
        self.assertIn('Request', top)


class TestResources(unittest.TestCase):
    def test_slow_resource_detected(self):
        lg = L.generate(n_cases=400, seed=75, slow_resource='ware1')
        rs = perf.resource_stats(lg)
        self.assertIn('ware1', rs)
        self.assertGreater(rs['ware1']['mean_duration'],
                           rs['ware2']['mean_duration'] * 2.0)

    def test_handover_network(self):
        lg = L.generate(n_cases=200, seed=76)
        h = perf.handover_network(lg)
        self.assertGreater(len(h), 5)
        total = sum(h.values())
        self.assertEqual(total, sum(max(0, len(t) - 1) for t in lg))

    def test_rework_counts_reject_loop(self):
        lg = L.generate(n_cases=300, seed=77, reject_prob=0.4)
        rw = perf.rework(lg)
        self.assertIn('Request', rw)
        self.assertIn('Approve', rw)
        self.assertNotIn('Pay', rw)          # Pay 는 한 번뿐


class TestQueueing(unittest.TestCase):
    def test_littles_law_consistent(self):
        lg = L.generate(n_cases=500, seed=78)
        r = perf.littles_law(lg)
        self.assertGreater(r['L_predicted'], 0)
        rel = abs(r['L_predicted'] - r['L_observed']) / r['L_observed']
        self.assertLess(rel, 0.15)           # 예측과 관측이 15% 안에서 일치

    def test_mm1_blows_up_near_capacity(self):
        w50 = perf.mm1_waiting(0.5, 1.0)
        w90 = perf.mm1_waiting(0.9, 1.0)
        w99 = perf.mm1_waiting(0.99, 1.0)
        self.assertLess(w50, w90)
        self.assertLess(w90, w99)
        self.assertGreater(w99 / w90, 5.0)   # 가동률 90 -> 99% 에서 5배 이상
        self.assertEqual(perf.mm1_waiting(1.0, 1.0), float('inf'))


class TestAllocation(unittest.TestCase):
    def test_cost_matrix_shape(self):
        lg = L.generate(n_cases=200, seed=79)
        acts, res, M = AL.cost_matrix(lg)
        self.assertEqual(len(M), len(acts))
        self.assertEqual(len(M[0]), len(res))
        for row in M:
            for v in row:
                self.assertGreater(v, 0)

    def test_assignment_is_one_to_one(self):
        lg = L.generate(n_cases=200, seed=80)
        out, total = AL.assign_resources(lg)
        acts = [a for a, _, _ in out]
        rs = [r for _, r, _ in out]
        self.assertEqual(len(set(acts)), len(acts))
        self.assertEqual(len(set(rs)), len(rs))
        self.assertGreater(total, 0)

    def test_assignment_beats_random(self):
        import random
        lg = L.generate(n_cases=200, seed=81)
        acts, res, M = AL.cost_matrix(lg)
        out, total = AL.assign_resources(lg)
        rng = random.Random(0)
        worse = 0
        for _ in range(200):
            perm = list(range(len(res)))
            rng.shuffle(perm)
            c = sum(M[i][perm[i]] for i in range(len(acts)) if perm[i] < len(res))
            if c >= total - 1e-9:
                worse += 1
        self.assertGreater(worse, 150)       # 대부분의 무작위 배치보다 낫다

    def test_capacity_plan_respects_budget(self):
        lg = L.generate(n_cases=300, seed=82)
        p = AL.capacity_plan(lg, budget=3)
        self.assertLessEqual(p['spent'], 3)
        self.assertGreater(p['saved'], 0)
        self.assertLessEqual(len(p['chosen']), 3)

    def test_bigger_budget_saves_more(self):
        lg = L.generate(n_cases=300, seed=83)
        a = AL.capacity_plan(lg, budget=2)
        b = AL.capacity_plan(lg, budget=5)
        self.assertGreaterEqual(b['saved'], a['saved'])


if __name__ == '__main__':
    unittest.main()


class TestDemoUsesOneLog(unittest.TestCase):
    """12부 데모의 병목 표(§2)와 배낭 표(§6)는 같은 로그에서 나와야 한다 —
       그래야 "예산 1 의 절감 = 1위 병목의 총 대기 절반"이 표끼리 맞아떨어진다."""

    def test_knapsack_matches_bottleneck_table(self):
        from py import demo_pm_perf
        lg = demo_pm_perf.base_log()
        top = perf.bottlenecks(lg)[0]
        plan = AL.capacity_plan(lg, budget=1)
        self.assertEqual(plan['chosen'], [top['activity']])
        self.assertEqual(plan['saved'], int(round(0.5 * top['total_waiting'])))
