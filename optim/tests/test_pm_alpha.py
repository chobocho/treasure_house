# -*- coding: utf-8 -*-
"""알파 알고리즘과 페트리넷 — 알려진 모델을 되찾는가."""
import unittest

from py.pm import alpha as A
from py.pm import log as L
from py.pm import petri


class TestPetriNet(unittest.TestCase):
    def _seq_net(self):
        n = petri.PetriNet()
        for p in ('i', 'p1', 'o'):
            n.add_place(p)
        n.add_transition('a')
        n.add_transition('b')
        n.add_arc('i', 'a'); n.add_arc('a', 'p1')
        n.add_arc('p1', 'b'); n.add_arc('b', 'o')
        return n

    def test_enabled_and_fire(self):
        n = self._seq_net()
        m = {'i': 1}
        self.assertEqual(n.enabled(m), ['a'])
        m = n.fire(m, 'a')
        self.assertEqual(m, {'p1': 1})
        self.assertEqual(n.enabled(m), ['b'])
        m = n.fire(m, 'b')
        self.assertEqual(m, {'o': 1})

    def test_fire_disabled_raises(self):
        n = self._seq_net()
        with self.assertRaises(ValueError):
            n.fire({'i': 1}, 'b')

    def test_replay_accepts_and_rejects(self):
        n = self._seq_net()
        ok, _ = petri.replay_trace(n, {'i': 1}, {'o': 1}, ['a', 'b'])
        self.assertTrue(ok)
        bad, _ = petri.replay_trace(n, {'i': 1}, {'o': 1}, ['b', 'a'])
        self.assertFalse(bad)

    def test_parallel_net(self):
        # i → t_split → (p1, p2) → a, b → (p3, p4) → t_join → o
        n = petri.PetriNet()
        for p in ('i', 'p1', 'p2', 'p3', 'p4', 'o'):
            n.add_place(p)
        n.add_transition('split', None)      # 보이지 않는 전이
        n.add_transition('a'); n.add_transition('b')
        n.add_transition('join', None)
        n.add_arc('i', 'split'); n.add_arc('split', 'p1'); n.add_arc('split', 'p2')
        n.add_arc('p1', 'a'); n.add_arc('a', 'p3')
        n.add_arc('p2', 'b'); n.add_arc('b', 'p4')
        n.add_arc('p3', 'join'); n.add_arc('p4', 'join'); n.add_arc('join', 'o')
        for seq in (['a', 'b'], ['b', 'a']):
            ok, _ = petri.replay_trace(n, {'i': 1}, {'o': 1}, seq)
            self.assertTrue(ok, seq)
        ok, _ = petri.replay_trace(n, {'i': 1}, {'o': 1}, ['a'])
        self.assertFalse(ok)


class TestFootprint(unittest.TestCase):
    def test_sequence(self):
        lg = L.EventLog.from_variants({('a', 'b', 'c'): 5})
        acts, rel = A.footprint(lg)
        self.assertEqual(acts, ['a', 'b', 'c'])
        self.assertEqual(rel[('a', 'b')], '→')
        self.assertEqual(rel[('b', 'a')], '←')
        self.assertEqual(rel[('a', 'c')], '#')

    def test_parallel(self):
        lg = L.EventLog.from_variants({('a', 'b', 'c', 'd'): 3,
                                       ('a', 'c', 'b', 'd'): 3})
        _, rel = A.footprint(lg)
        self.assertEqual(rel[('b', 'c')], '‖')
        self.assertEqual(rel[('c', 'b')], '‖')

    def test_choice(self):
        lg = L.EventLog.from_variants({('a', 'b', 'd'): 3, ('a', 'c', 'd'): 3})
        _, rel = A.footprint(lg)
        self.assertEqual(rel[('b', 'c')], '#')


class TestAlpha(unittest.TestCase):
    def test_sequence_model(self):
        lg = L.EventLog.from_variants({('a', 'b', 'c'): 10})
        net, m0, mf = A.alpha(lg)
        ok, _ = petri.replay_trace(net, m0, mf, ['a', 'b', 'c'])
        self.assertTrue(ok)
        bad, _ = petri.replay_trace(net, m0, mf, ['a', 'c', 'b'])
        self.assertFalse(bad)

    def test_choice_model(self):
        lg = L.EventLog.from_variants({('a', 'b', 'd'): 5, ('a', 'c', 'd'): 5})
        net, m0, mf = A.alpha(lg)
        for seq in (('a', 'b', 'd'), ('a', 'c', 'd')):
            ok, _ = petri.replay_trace(net, m0, mf, list(seq))
            self.assertTrue(ok, seq)
        bad, _ = petri.replay_trace(net, m0, mf, ['a', 'b', 'c', 'd'])
        self.assertFalse(bad)

    def test_parallel_model(self):
        lg = L.EventLog.from_variants({('a', 'b', 'c', 'd'): 5,
                                       ('a', 'c', 'b', 'd'): 5})
        net, m0, mf = A.alpha(lg)
        for seq in (('a', 'b', 'c', 'd'), ('a', 'c', 'b', 'd')):
            ok, _ = petri.replay_trace(net, m0, mf, list(seq))
            self.assertTrue(ok, seq)

    def test_rediscovers_all_log_traces(self):
        lg = L.EventLog.from_variants({
            ('a', 'b', 'c', 'e'): 4, ('a', 'c', 'b', 'e'): 4, ('a', 'd', 'e'): 4})
        net, m0, mf = A.alpha(lg)
        for seq in lg.variants():
            ok, _ = petri.replay_trace(net, m0, mf, list(seq))
            self.assertTrue(ok, seq)

    def test_short_loop_limitation(self):
        # 알파 알고리즘의 알려진 한계: 길이 2 루프(a b a b)를 병렬로 오인한다
        lg = L.EventLog.from_variants({('a', 'b', 'a', 'b', 'c'): 5,
                                       ('a', 'b', 'c'): 5})
        _, rel = A.footprint(lg)
        self.assertEqual(rel[('a', 'b')], '‖')     # 인과가 아니라 병렬로 보인다
        self.assertEqual(rel[('b', 'a')], '‖')


if __name__ == '__main__':
    unittest.main()
