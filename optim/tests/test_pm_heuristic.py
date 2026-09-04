# -*- coding: utf-8 -*-
"""휴리스틱 마이너 — 빈도 기반 필터가 잡음을 걸러내는가."""
import unittest

from py.pm import heuristic as H
from py.pm import log as L


class TestDependency(unittest.TestCase):
    def test_pure_sequence_is_near_one(self):
        lg = L.EventLog.from_variants({('a', 'b'): 100})
        d = H.dependency(lg)
        self.assertGreater(d[('a', 'b')], 0.98)
        self.assertLess(d[('b', 'a')], -0.98)

    def test_parallel_is_near_zero(self):
        lg = L.EventLog.from_variants({('a', 'b'): 50, ('b', 'a'): 50})
        d = H.dependency(lg)
        self.assertLess(abs(d[('a', 'b')]), 0.02)

    def test_small_counts_are_cautious(self):
        # 한 번만 관측된 관계는 확신하지 않는다
        lg = L.EventLog.from_variants({('a', 'b'): 1})
        d = H.dependency(lg)
        self.assertAlmostEqual(d[('a', 'b')], 0.5, places=9)

    def test_self_loop(self):
        lg = L.EventLog.from_variants({('a', 'a', 'a'): 10})
        d = H.dependency(lg)
        self.assertGreater(d[('a', 'a')], 0.9)


class TestGraphFiltering(unittest.TestCase):
    def test_noise_edges_removed(self):
        lg = L.generate(n_cases=500, seed=31, noise=0.35)
        all_edges = len(lg.dfg())
        g = H.dependency_graph(lg, dep_threshold=0.9, freq_threshold=10)
        self.assertLess(len(g), all_edges)
        st = H.graph_stats(lg, g)
        # 남긴 간선이 관측 빈도의 상당 부분을 덮는다. 1 에 가깝지 않은 것은
        # 병렬 쌍(Order ‖ Check)의 의존도가 0 근처라 함께 잘려 나가기 때문이다 —
        # 그래서 완전한 휴리스틱 마이너는 AND-분기를 따로 판정한다.
        self.assertGreater(st['coverage'], 0.6)
        self.assertLess(st['coverage'], 0.95)

    def test_threshold_monotone(self):
        lg = L.generate(n_cases=400, seed=32, noise=0.3)
        sizes = [len(H.dependency_graph(lg, dep_threshold=t, freq_threshold=5,
                                        all_tasks_connected=False))
                 for t in (0.0, 0.5, 0.9, 0.99)]
        for i in range(len(sizes) - 1):
            self.assertGreaterEqual(sizes[i], sizes[i + 1])

    def test_all_tasks_connected(self):
        lg = L.generate(n_cases=300, seed=33)
        g = H.dependency_graph(lg, dep_threshold=0.999, freq_threshold=1)
        touched = set()
        for (a, b) in g:
            touched.add(a)
            touched.add(b)
        self.assertEqual(touched, lg.activities())   # 고립된 활동이 없다


if __name__ == '__main__':
    unittest.main()
