# -*- coding: utf-8 -*-
"""이벤트 로그 — 자료 구조와 기본 통계가 맞는가."""
import unittest

from py.pm import log as L


class TestTrace(unittest.TestCase):
    def test_sort_and_activities(self):
        t = L.Trace(1, [L.Event(1, 'B', 5.0), L.Event(1, 'A', 1.0)])
        t.sort()
        self.assertEqual(t.activities, ('A', 'B'))
        self.assertAlmostEqual(t.duration, 4.0)

    def test_empty_trace(self):
        t = L.Trace(1)
        self.assertEqual(len(t), 0)
        self.assertEqual(t.duration, 0.0)


class TestEventLog(unittest.TestCase):
    def setUp(self):
        self.log = L.EventLog.from_variants({
            ('A', 'B', 'C'): 3,
            ('A', 'C', 'B'): 2,
            ('A', 'B', 'B', 'C'): 1,
        })

    def test_counts(self):
        s = self.log.summary()
        self.assertEqual(s['cases'], 6)
        self.assertEqual(s['events'], 3 * 3 + 2 * 3 + 4)
        self.assertEqual(s['activities'], 3)
        self.assertEqual(s['variants'], 3)

    def test_start_end(self):
        self.assertEqual(self.log.start_activities(), {'A': 6})
        self.assertEqual(self.log.end_activities(), {'C': 4, 'B': 2})

    def test_dfg(self):
        d = self.log.dfg()
        self.assertEqual(d[('A', 'B')], 4)      # 3 + 1
        self.assertEqual(d[('A', 'C')], 2)
        self.assertEqual(d[('B', 'B')], 1)
        self.assertNotIn(('C', 'A'), d)

    def test_filter_variants(self):
        f = self.log.filter_variants(2)
        self.assertEqual(len(f), 5)
        self.assertEqual(len(f.variants()), 2)

    def test_from_events_groups_by_case(self):
        evs = [L.Event(1, 'A', 0), L.Event(2, 'A', 1), L.Event(1, 'B', 2)]
        lg = L.EventLog.from_events(evs)
        self.assertEqual(len(lg), 2)
        self.assertEqual(lg.traces[0].activities, ('A', 'B'))


class TestGenerator(unittest.TestCase):
    def test_deterministic(self):
        a = L.generate(n_cases=50, seed=1)
        b = L.generate(n_cases=50, seed=1)
        self.assertEqual(a.variants(), b.variants())

    def test_structure(self):
        lg = L.generate(n_cases=300, seed=2)
        for t in lg:
            acts = t.activities
            self.assertEqual(acts[0], 'Request')
            self.assertEqual(acts[-1], 'Pay')
            self.assertEqual(acts.count('Receive'), 1)
            # 반려가 있으면 그 뒤에 반드시 재요청이 온다
            for i, a in enumerate(acts):
                if a == 'Reject':
                    self.assertEqual(acts[i + 1], 'Request')

    def test_reject_probability(self):
        lg = L.generate(n_cases=2000, seed=3, reject_prob=0.3)
        rej = sum(1 for t in lg if 'Reject' in t.activities)
        self.assertGreater(rej / 2000.0, 0.2)      # 최소 한 번 반려될 확률 ≈ 0.3
        self.assertLess(rej / 2000.0, 0.45)

    def test_parallel_produces_two_orders(self):
        lg = L.generate(n_cases=400, seed=4, parallel_prob=1.0)
        for t in lg:
            self.assertIn('Check', t.activities)
        orders = {t.activities.index('Order') < t.activities.index('Check')
                  for t in lg}
        self.assertEqual(orders, {True, False})    # 두 순서가 모두 나타난다

    def test_noise_changes_log(self):
        clean = L.generate(n_cases=200, seed=5, noise=0.0)
        noisy = L.generate(n_cases=200, seed=5, noise=0.3)
        self.assertNotEqual(clean.variants(), noisy.variants())
        self.assertGreater(len(noisy.variants()), len(clean.variants()))

    def test_resources_recorded(self):
        lg = L.generate(n_cases=50, seed=6)
        self.assertGreater(len(lg.resources()), 3)
        for t in lg:
            for e in t:
                self.assertIsNotNone(e.resource)
                self.assertIn('duration', e.attrs)


if __name__ == '__main__':
    unittest.main()
