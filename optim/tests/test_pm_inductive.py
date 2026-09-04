# -*- coding: utf-8 -*-
"""인덕티브 마이너 — 알려진 구조를 되찾고, 만든 모델이 건전한가."""
import unittest

from py.pm import inductive as IM
from py.pm import log as L
from py.pm import petri
from py.pm import tree as T


def _is_flower(node):
    """루프 하나 안에 모든 활동이 선택으로 들어 있는 모델인가."""
    if node.op != T.LOOP or len(node.children) != 2:
        return False
    body, redo = node.children
    if body.op != T.TAU or redo.op != T.XOR:
        return False
    return all(c.op == T.ACT for c in redo.children)


def replays(node, seq):
    net, m0, mf = T.to_petri(node)
    ok, _ = petri.replay_trace(net, m0, mf, list(seq), max_silent=12)
    return ok


class TestCuts(unittest.TestCase):
    def test_sequence(self):
        t = IM.discover([('a', 'b', 'c')] * 5)
        self.assertEqual(t.op, T.SEQ)
        self.assertTrue(replays(t, ('a', 'b', 'c')))
        self.assertFalse(replays(t, ('a', 'c', 'b')))

    def test_choice(self):
        t = IM.discover([('a', 'b', 'd')] * 5 + [('a', 'c', 'd')] * 5)
        self.assertTrue(replays(t, ('a', 'b', 'd')))
        self.assertTrue(replays(t, ('a', 'c', 'd')))
        self.assertFalse(replays(t, ('a', 'b', 'c', 'd')))

    def test_parallel(self):
        t = IM.discover([('a', 'b', 'c', 'd')] * 5 + [('a', 'c', 'b', 'd')] * 5)
        self.assertTrue(replays(t, ('a', 'b', 'c', 'd')))
        self.assertTrue(replays(t, ('a', 'c', 'b', 'd')))

    def test_loop(self):
        traces = [('a', 'b')] * 5 + [('a', 'c', 'a', 'b')] * 3 + \
                 [('a', 'c', 'a', 'c', 'a', 'b')] * 2
        t = IM.discover(traces)
        for seq in set(traces):
            self.assertTrue(replays(t, seq), seq)

    def test_single_activity(self):
        self.assertEqual(IM.discover([('a',)] * 3).op, T.ACT)


class TestSoundness(unittest.TestCase):
    def test_all_log_traces_replay(self):
        lg = L.generate(n_cases=200, seed=11)
        t = IM.mine(lg)
        for seq in lg.variants():
            self.assertTrue(replays(t, seq), seq)

    def test_tree_covers_all_activities(self):
        lg = L.generate(n_cases=100, seed=12)
        t = IM.mine(lg)
        self.assertEqual(t.activities(), lg.activities())

    def test_petri_net_is_wellformed(self):
        lg = L.generate(n_cases=100, seed=13)
        net, m0, mf = T.to_petri(IM.mine(lg))
        s = net.summary()
        self.assertGreater(s['places'], 0)
        self.assertGreater(s['transitions'], 0)
        self.assertEqual(len(m0), 1)
        self.assertEqual(len(mf), 1)

    def test_noise_filtering_recovers_structure(self):
        # 잡음이 심하면 인덕티브 마이너가 플라워 모델로 물러선다(무엇이든 허용).
        # 희귀 변형을 걸러내면 진짜 구조가 다시 드러난다 — 모델이 <작아지는> 것이
        # 아니라 <구조가 생기는> 것이 요점이다.
        lg = L.generate(n_cases=400, seed=14, noise=0.4)
        raw = IM.mine(lg, min_count=1)
        filt = IM.mine(lg, min_count=20)
        self.assertTrue(_is_flower(raw), repr(raw))
        self.assertFalse(_is_flower(filt), repr(filt))
        self.assertEqual(filt.op, T.SEQ)


class TestFlowerFallback(unittest.TestCase):
    def test_flower_accepts_everything(self):
        t = IM._flower({'a', 'b', 'c'})
        for seq in (('a',), ('c', 'b', 'a'), ('a', 'a', 'b'), ()):
            self.assertTrue(replays(t, seq), seq)


if __name__ == '__main__':
    unittest.main()


class TestRediscovery(unittest.TestCase):
    def test_recovers_generating_model(self):
        """합성 로그의 생성 모델을 구조까지 정확히 되찾는지 — 이 부의 핵심 주장."""
        lg = L.generate(n_cases=500, seed=21, noise=0.0)
        t = IM.mine(lg)
        # →( ↺(→(Request, Approve), Reject), ∧(×(Check, τ), Order), Receive, Pay )
        self.assertEqual(t.op, T.SEQ)
        self.assertEqual(len(t.children), 4)
        loop, par, recv, pay = t.children
        self.assertEqual(loop.op, T.LOOP)
        self.assertEqual(loop.children[0].op, T.SEQ)
        self.assertEqual([c.label for c in loop.children[0].children],
                         ['Request', 'Approve'])
        self.assertEqual(loop.children[1].label, 'Reject')
        self.assertEqual(par.op, T.AND)
        self.assertEqual(recv.label, 'Receive')
        self.assertEqual(pay.label, 'Pay')
        # 선택적 Check: ×(Check, τ)
        opt = [c for c in par.children if c.op == T.XOR]
        self.assertEqual(len(opt), 1)
        self.assertEqual({c.op for c in opt[0].children}, {T.ACT, T.TAU})
