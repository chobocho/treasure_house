# -*- coding: utf-8 -*-
"""sample 의 증인 시험 (PLAN.md §3.1 표 11행, SPEC.md §7).

  · KV 캐시로 한 토큰씩 늘린 로짓 = 전체를 다시 계산한 로짓 (≤ 1e-9),
    세 위치 방식 모두.
  · top-p 는 누적합이 처음 p 이상이 되는 가장 짧은 앞부분이다.
  · 온도 → 0 은 greedy 와 같다. top-k = 1 도 greedy 다.
  · 뽑힌 빈도가 확률을 따른다.
"""
import math
import unittest

from transformerlib import model as M
from transformerlib import sample as S
from transformerlib.rng import Rng


def cfg_of(pos):
    return M.Config(V=13, T=6, d=8, L=2, h=2, d_ff=16, pos=pos)


class TestKvCache(unittest.TestCase):
    def test_cached_logits_equal_full_recompute(self):
        for pos in ('learned', 'sin', 'rope'):
            cfg = cfg_of(pos)
            params = M.init_params(cfg, 3)
            # 초기값 그대로면 로짓이 너무 평평해 차이가 안 보인다
            for t in params.values():
                t.data[:] = [v * 30 for v in t.data]
            ids = [3, 7, 1, 12, 0, 5]
            cache = S.KVCache(cfg)
            for n in range(1, len(ids) + 1):
                row = S.forward_cached(params, cfg, ids[n - 1], cache)
                full, _ = M.forward(params, cfg, [ids[:n]])
                want = full.data[(n - 1) * cfg.V:n * cfg.V]
                err = max(abs(a - b) for a, b in zip(row, want))
                self.assertLess(err, 1e-9,
                                '%s n=%d %.2e' % (pos, n, err))

    def test_cache_refuses_to_overflow(self):
        cfg = cfg_of('learned')
        params = M.init_params(cfg, 1)
        cache = S.KVCache(cfg)
        for t in range(6):
            S.forward_cached(params, cfg, t, cache)
        with self.assertRaises(ValueError):
            S.forward_cached(params, cfg, 1, cache)


class TestFilters(unittest.TestCase):
    def test_top_p_smallest_prefix(self):
        logits = [math.log(p) for p in (0.1, 0.4, 0.3, 0.2)]
        kept = S.filtered(logits, 1.0, None, 0.7)
        self.assertEqual([i for i, _ in kept], [1, 2])
        kept = S.filtered(logits, 1.0, None, 0.71)
        self.assertEqual([i for i, _ in kept], [1, 2, 3])
        self.assertAlmostEqual(sum(p for _, p in kept), 1.0, places=14)

    def test_top_k_then_top_p_renormalised(self):
        logits = [math.log(p) for p in (0.1, 0.4, 0.3, 0.2)]
        # top-k 2 뒤의 확률은 4/7, 3/7 — p 0.5 는 첫 칸에서 채워진다
        kept = S.filtered(logits, 1.0, 2, 0.5)
        self.assertEqual([i for i, _ in kept], [1])

    def test_ties_break_by_smaller_id(self):
        kept = S.filtered([0.0, 1.0, 1.0, 0.0], 1.0, 2, None)
        self.assertEqual([i for i, _ in kept], [1, 2])
        self.assertEqual(S.sample_next([0.0, 1.0, 1.0], 0.0, None, None,
                                       Rng(1)), 1)

    def test_temperature_zero_and_near_zero_are_greedy(self):
        r = Rng(4)
        for trial in range(200):
            logits = [r.normal() for _ in range(10)]
            best = max(range(10), key=lambda k: (logits[k], -k))
            self.assertEqual(S.sample_next(logits, 0.0, None, None, r),
                             best)
            self.assertEqual(S.sample_next(logits, 1e-4, None, None, r),
                             best)
            self.assertEqual(S.sample_next(logits, 1.0, 1, None, r),
                             best)

    def test_frequencies_follow_probabilities(self):
        probs = [0.5, 0.3, 0.15, 0.05]
        logits = [math.log(p) for p in probs]
        r = Rng(9)
        n = 20000
        count = [0] * 4
        for _ in range(n):
            count[S.sample_next(logits, 1.0, None, None, r)] += 1
        for c, p in zip(count, probs):
            sd = math.sqrt(p * (1 - p) / n)
            self.assertLess(abs(c / n - p), 4 * sd)

    def test_high_temperature_flattens(self):
        logits = [2.0, 0.0, -2.0]
        hot = S.filtered(logits, 10.0, None, None)
        cold = S.filtered(logits, 0.5, None, None)
        self.assertLess(hot[0][1], cold[0][1])


class TestGenerate(unittest.TestCase):
    def test_cache_and_recompute_generate_the_same(self):
        cfg = cfg_of('learned')
        params = M.init_params(cfg, 5)
        for t in params.values():
            t.data[:] = [v * 30 for v in t.data]
        a = S.generate(params, cfg, [1, 2], 9, 0.8, 5, 0.9, seed=7,
                       use_cache=True)
        b = S.generate(params, cfg, [1, 2], 9, 0.8, 5, 0.9, seed=7,
                       use_cache=False)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 11)

    def test_context_refill_rule(self):
        """T=6 을 넘기면 뒤쪽 3토큰만 남기고 다시 채운다(SPEC §7)."""
        self.assertEqual(S.window([1, 2, 3, 4, 5, 6], 6), [4, 5, 6])
        self.assertEqual(S.window([1, 2, 3], 6), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
