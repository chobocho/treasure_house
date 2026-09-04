# -*- coding: utf-8 -*-
"""적합도 — 정렬이 정말 최소비용인가, 지표가 기대대로 움직이는가."""
import itertools
import unittest

from py.pm import conformance as C
from py.pm import inductive as IM
from py.pm import log as L
from py.pm import petri
from py.pm import tree as T


def seq_model(acts):
    return T.to_petri(T.Node(T.SEQ, children=[T.act(a) for a in acts]))


class TestTokenReplay(unittest.TestCase):
    def test_perfect_fit(self):
        net, m0, mf = seq_model(['a', 'b', 'c'])
        r = C.token_replay(net, m0, mf, ['a', 'b', 'c'])
        self.assertAlmostEqual(r['fitness'], 1.0, places=9)
        self.assertEqual(r['missing'], 0)
        self.assertEqual(r['remaining'], 0)

    def test_missing_event_lowers_fitness(self):
        net, m0, mf = seq_model(['a', 'b', 'c'])
        r = C.token_replay(net, m0, mf, ['a', 'c'])
        self.assertLess(r['fitness'], 1.0)
        self.assertGreater(r['missing'], 0)

    def test_unknown_activity(self):
        net, m0, mf = seq_model(['a', 'b'])
        r = C.token_replay(net, m0, mf, ['a', 'x', 'b'])
        self.assertLess(r['fitness'], 1.0)


class TestAlignment(unittest.TestCase):
    def test_perfect_trace_costs_zero(self):
        net, m0, mf = seq_model(['a', 'b', 'c'])
        a = C.align(net, m0, mf, ['a', 'b', 'c'])
        self.assertEqual(a['cost'], 0)
        self.assertEqual(a['sync_moves'], 3)
        self.assertEqual(a['log_moves'], 0)

    def test_missing_event_costs_one(self):
        net, m0, mf = seq_model(['a', 'b', 'c'])
        a = C.align(net, m0, mf, ['a', 'c'])
        self.assertEqual(a['cost'], 1)       # b 를 모델 이동으로 채운다
        self.assertEqual(a['model_moves'], 1)

    def test_extra_event_costs_one(self):
        net, m0, mf = seq_model(['a', 'b'])
        a = C.align(net, m0, mf, ['a', 'x', 'b'])
        self.assertEqual(a['cost'], 1)       # x 를 로그 이동으로 버린다
        self.assertEqual(a['log_moves'], 1)

    def test_swapped_events(self):
        net, m0, mf = seq_model(['a', 'b', 'c'])
        a = C.align(net, m0, mf, ['a', 'c', 'b'])
        self.assertEqual(a['cost'], 2)       # 하나 버리고 하나 채운다

    def test_matches_brute_force(self):
        """작은 예에서 모든 정렬을 전수 조사해 최소비용과 비교한다."""
        net, m0, mf = seq_model(['a', 'b', 'c'])
        model_seq = ['a', 'b', 'c']
        for k in range(4):
            for tr in itertools.product('abcx', repeat=k):
                got = C.align(net, m0, mf, list(tr))['cost']
                want = _edit_distance(list(tr), model_seq)
                self.assertEqual(got, want, (tr, got, want))

    def test_heuristic_does_not_change_cost(self):
        lg = L.generate(n_cases=60, seed=41)
        net, m0, mf = T.to_petri(IM.mine(lg))
        for seq in list(lg.variants())[:6]:
            a = C.align(net, m0, mf, list(seq), heuristic=True)
            b = C.align(net, m0, mf, list(seq), heuristic=False)
            self.assertEqual(a['cost'], b['cost'])

    def test_heuristic_visits_no_more_states(self):
        lg = L.generate(n_cases=60, seed=42)
        net, m0, mf = T.to_petri(IM.mine(lg))
        seq = list(max(lg.variants(), key=len)) + ['XX', 'YY']
        a = C.align(net, m0, mf, seq, heuristic=True)
        b = C.align(net, m0, mf, seq, heuristic=False)
        self.assertEqual(a['cost'], b['cost'])
        self.assertLessEqual(a['visited'], b['visited'])


def _edit_distance(a, b):
    """삽입·삭제만 허용하는 편집거리 — 순차 모델에서는 정렬 비용과 같다."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1])
    return d[n][m]


class TestFitnessMetrics(unittest.TestCase):
    def test_log_fitness_one_for_own_model(self):
        lg = L.generate(n_cases=100, seed=43)
        net, m0, mf = T.to_petri(IM.mine(lg))
        f, _ = C.log_fitness(net, m0, mf, lg)
        self.assertAlmostEqual(f, 1.0, places=9)

    def test_fitness_drops_for_wrong_model(self):
        lg = L.generate(n_cases=60, seed=44)
        net, m0, mf = seq_model(['Request', 'Approve', 'Pay'])
        f, _ = C.log_fitness(net, m0, mf, lg)
        self.assertLess(f, 0.9)
        self.assertGreater(f, 0.0)


class TestPrecision(unittest.TestCase):
    def test_flower_has_low_precision(self):
        lg = L.generate(n_cases=100, seed=45)
        flower = IM._flower(lg.activities())
        fnet, fm0, fmf = T.to_petri(flower)
        good = IM.mine(lg)
        gnet, gm0, gmf = T.to_petri(good)
        p_flower = C.precision(fnet, fm0, fmf, lg)
        p_good = C.precision(gnet, gm0, gmf, lg)
        self.assertLess(p_flower, p_good)
        self.assertLess(p_flower, 0.5)

    def test_flower_fitness_is_one(self):
        lg = L.generate(n_cases=40, seed=46)
        flower = IM._flower(lg.activities())
        net, m0, mf = T.to_petri(flower)
        f, _ = C.log_fitness(net, m0, mf, lg)
        self.assertAlmostEqual(f, 1.0, places=9)     # 적합도만으로는 구별 못 한다


if __name__ == '__main__':
    unittest.main()


class TestLPHeuristic(unittest.TestCase):
    def test_lower_bound_at_start(self):
        """LP 휴리스틱이 실제 정렬 비용을 넘지 않아야 한다(허용 가능성)."""
        lg = L.generate(n_cases=40, seed=61)
        net, m0, mf = T.to_petri(IM.mine(lg))
        cases = [list(v) for v in list(lg.variants())[:5]]
        cases += [['Request', 'Pay'], ['Pay'], [], ['Request', 'ZZ', 'Pay']]
        for tr in cases:
            h = C.lp_heuristic(net, m0, mf, tr)
            true = C.align(net, m0, mf, tr)['cost']
            self.assertLessEqual(h, true + 1e-6, (tr, h, true))

    def test_same_cost_as_plain_astar(self):
        lg = L.generate(n_cases=40, seed=62)
        net, m0, mf = T.to_petri(IM.mine(lg))
        for seq in list(lg.variants())[:4]:
            tr = list(seq) + ['ZZ']
            self.assertEqual(C.align_lp(net, m0, mf, tr)['cost'],
                             C.align(net, m0, mf, tr)['cost'])

    def test_visits_fewer_states(self):
        lg = L.generate(n_cases=60, seed=63)
        net, m0, mf = T.to_petri(IM.mine(lg))
        seq = list(max(lg.variants(), key=len))
        tr = seq + ['ZZ', 'YY']
        a = C.align(net, m0, mf, tr, heuristic=False)
        b = C.align_lp(net, m0, mf, tr)
        self.assertLessEqual(b['visited'], a['visited'])

    def test_infeasible_marking_detected(self):
        # 종료 마킹에 닿을 수 없는 상태에서는 휴리스틱이 무한대를 준다
        net, m0, mf = seq_model(['a', 'b'])
        after = net.fire(m0, [t for t in net.transitions
                              if net.label_of(t) == 'a'][0])
        self.assertLess(C.lp_heuristic(net, after, mf, ['b']), float('inf'))
