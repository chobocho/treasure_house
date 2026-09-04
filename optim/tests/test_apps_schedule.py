# -*- coding: utf-8 -*-
"""스케줄링 — 규칙이 최적임을 검증하고, MILP 가 전수 조사와 일치하는가."""
import random
import unittest

from py.apps import schedule as S


class TestWSPT(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(3)
        for _ in range(30):
            n = rng.randint(2, 7)
            jobs = [('J%d' % i, rng.randint(1, 9), rng.randint(1, 9))
                    for i in range(n)]
            _, got = S.wspt(jobs)
            _, want = S.brute_force_wspt(jobs)
            self.assertAlmostEqual(got, want, places=9)

    def test_equal_weights_is_spt(self):
        jobs = [('A', 5, 1), ('B', 2, 1), ('C', 8, 1)]
        sched, _ = S.wspt(jobs)
        self.assertEqual([s[0] for s in sched], ['B', 'A', 'C'])

    def test_completion_times(self):
        jobs = [('A', 3, 1), ('B', 1, 1)]
        sched, total = S.wspt(jobs)
        self.assertEqual(sched, [('B', 1.0), ('A', 4.0)])
        self.assertAlmostEqual(total, 5.0)

    def test_weight_changes_order(self):
        jobs = [('A', 4, 10), ('B', 1, 1)]
        sched, _ = S.wspt(jobs)
        self.assertEqual(sched[0][0], 'A')       # p/w = 0.4 < 1.0


class TestJobShop(unittest.TestCase):
    def test_two_jobs_two_machines(self):
        jobs = [[(0, 3), (1, 2)], [(1, 2), (0, 4)]]
        res, out = S.jobshop_milp(jobs, 2)
        self.assertEqual(res.status, 'optimal')
        brute = S.jobshop_brute(jobs, 2)
        self.assertAlmostEqual(out['makespan'], brute, places=6)

    def test_three_jobs(self):
        jobs = [[(0, 2), (1, 3)], [(1, 2), (0, 2)], [(0, 1), (1, 1)]]
        res, out = S.jobshop_milp(jobs, 2, maxnodes=60000)
        self.assertEqual(res.status, 'optimal')
        self.assertAlmostEqual(out['makespan'], S.jobshop_brute(jobs, 2), places=6)

    def test_schedule_is_feasible(self):
        jobs = [[(0, 3), (1, 2)], [(1, 2), (0, 4)]]
        _, out = S.jobshop_milp(jobs, 2)
        # 같은 기계에서 겹치지 않는다
        by_m = {}
        for d in out['schedule']:
            by_m.setdefault(d['machine'], []).append(d)
        for m, ds in by_m.items():
            ds.sort(key=lambda d: d['start'])
            for a, b in zip(ds, ds[1:]):
                self.assertLessEqual(a['end'], b['start'] + 1e-6)
        # 작업 안의 공정 순서가 지켜진다
        by_j = {}
        for d in out['schedule']:
            by_j.setdefault(d['job'], []).append(d)
        for j, ds in by_j.items():
            ds.sort(key=lambda d: d['op'])
            for a, b in zip(ds, ds[1:]):
                self.assertLessEqual(a['end'], b['start'] + 1e-6)

    def test_binary_count_grows(self):
        small = S.jobshop_milp([[(0, 1), (1, 1)], [(1, 1), (0, 1)]], 2)[1]
        big = S.jobshop_milp([[(0, 1), (1, 1)], [(1, 1), (0, 1)],
                              [(0, 1), (1, 1)]], 2, maxnodes=60000)[1]
        self.assertLess(small['binaries'], big['binaries'])


if __name__ == '__main__':
    unittest.main()
