# -*- coding: utf-8 -*-
"""model 의 증인 시험 (PLAN.md §3.1 표 8행).

  · GPT-2 small 설정의 파라미터 수 = 124,439,808 (SPEC §3.4) — 텐서를
    만들지 않고 식으로. 작은 설정에서는 식 = 실제로 만든 텐서 칸 수.
  · BERT-base 는 같은 식의 변형으로 109,482,240.
  · 행렬곱 곱셈 수 식 = 순전파가 실제로 한 곱셈 수(계측), 그리고
    학습 FLOPs ≈ 6N 이 GPT-2 small 에서 몇 % 어긋나는지.
  · 초기화 직후 손실 ≈ ln V.
  · 모델 전체의 역전파가 차분과 맞다.
  · 미래 토큰은 과거 로짓을 못 바꾼다.
"""
import math
import unittest

from transformerlib import model as M
from transformerlib import tensor as T

TINY = M.Config(V=7, T=4, d=4, L=1, h=2, d_ff=8)


class TestCounting(unittest.TestCase):
    def test_gpt2_small(self):
        cfg = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
        self.assertEqual(M.count_params(cfg), 124439808)

    def test_bert_base(self):
        self.assertEqual(M.bert_params(V=30522, T=512, d=768, L=12),
                         109482240)

    def test_formula_equals_built_tensors(self):
        for pos in ('learned', 'sin', 'rope'):
            cfg = M.Config(V=11, T=6, d=8, L=2, h=2, d_ff=32, pos=pos)
            params = M.init_params(cfg, 1)
            n = sum(len(p.data) for p in params.values())
            self.assertEqual(n, M.count_params(cfg), pos)

    def test_block_is_12d2_plus_13d(self):
        for d in (4, 64, 768):
            cfg = M.Config(V=1, T=1, d=d, L=1, h=1, d_ff=4 * d,
                           pos='sin')
            self.assertEqual(M.count_params(cfg) - d - 2 * d,
                             12 * d * d + 13 * d)

    def test_matmul_count_matches_instrumented_forward(self):
        cfg = M.Config(V=9, T=5, d=8, L=2, h=2, d_ff=16)
        params = M.init_params(cfg, 3)
        T.MULTS[0] = 0
        M.forward(params, cfg, [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]])
        self.assertEqual(T.MULTS[0], 2 * M.matmul_mults(cfg, 5))

    def test_six_n_rule_on_gpt2_small(self):
        cfg = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
        ratio = M.train_flops_per_token(cfg, 1024) / (
            6 * M.count_params(cfg))
        self.assertGreater(ratio, 1.0)
        self.assertLess(ratio, 1.2)


class TestInit(unittest.TestCase):
    def test_order_matches_spec_checkpoint(self):
        names = M.param_names(M.Config(V=2, T=2, d=2, L=1, h=1, d_ff=4))
        self.assertEqual(names, [
            'wte', 'wpe', 'h0.ln1_g', 'h0.ln1_b', 'h0.Wqkv', 'h0.bqkv',
            'h0.Wo', 'h0.bo', 'h0.ln2_g', 'h0.ln2_b', 'h0.W1', 'h0.b1',
            'h0.W2', 'h0.b2', 'lnf_g', 'lnf_b'])

    def test_spec_worked_example_has_66_params(self):
        self.assertEqual(M.count_params(
            M.Config(V=2, T=2, d=2, L=1, h=1, d_ff=4)), 66)

    def test_init_values_follow_spec(self):
        from transformerlib.rng import Rng
        cfg = M.Config(V=3, T=2, d=2, L=2, h=1, d_ff=8)
        p = M.init_params(cfg, 5)
        r = Rng(5)
        want_wte = [r.normal() * 0.02 for _ in range(6)]
        self.assertEqual(p['wte'].data, want_wte)
        self.assertEqual(p['h0.ln1_g'].data, [1.0, 1.0])
        self.assertEqual(p['h1.bqkv'].data, [0.0] * 6)
        # Wo 는 0.02/√(2L) — wpe(4)·Wqkv(12) 다음 차례로 뽑힌다
        for _ in range(4 + 12):
            r.normal()
        want_wo = [r.normal() * 0.02 / math.sqrt(4) for _ in range(4)]
        self.assertEqual(p['h0.Wo'].data, want_wo)

    def test_rejects_bad_config(self):
        with self.assertRaises(ValueError):
            M.Config(V=5, T=4, d=6, L=1, h=4, d_ff=8)
        with self.assertRaises(ValueError):
            M.Config(V=5, T=4, d=4, L=1, h=2, d_ff=8, pos='abs')


class TestForward(unittest.TestCase):
    def test_initial_loss_is_near_log_vocab(self):
        cfg = M.Config(V=50, T=8, d=16, L=1, h=2, d_ff=32)
        p = M.init_params(cfg, 7)
        ids = [[(i * 7 + b) % 50 for i in range(8)] for b in range(2)]
        tg = [[(i * 3 + b) % 50 for i in range(8)] for b in range(2)]
        _, loss = M.forward(p, cfg, ids, tg)
        self.assertLess(abs(loss.data[0] - math.log(50)), 0.05)

    def test_shapes_and_positions(self):
        for pos in ('learned', 'sin', 'rope'):
            cfg = M.Config(V=7, T=4, d=4, L=2, h=2, d_ff=8, pos=pos)
            logits, _ = M.forward(M.init_params(cfg, 1), cfg,
                                  [[1, 2, 3]])
            self.assertEqual(logits.shape, (1, 3, 7), pos)

    def test_too_long_sequence(self):
        with self.assertRaises(ValueError):
            M.forward(M.init_params(TINY, 1), TINY, [[1, 2, 3, 4, 5]])

    def test_future_cannot_change_past_logits(self):
        p = M.init_params(TINY, 2)
        a, _ = M.forward(p, TINY, [[1, 2, 3, 4]])
        b, _ = M.forward(p, TINY, [[1, 2, 3, 6]])
        self.assertEqual(a.data[:21], b.data[:21])
        self.assertNotEqual(a.data[21:], b.data[21:])

    def test_attention_maps_are_returned(self):
        p = M.init_params(TINY, 2)
        maps = []
        M.forward(p, TINY, [[1, 2, 3]], attn_out=maps)
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0].shape, (1, 2, 3, 3))


class TestGradient(unittest.TestCase):
    def test_every_parameter_matches_finite_difference(self):
        for pos in ('learned', 'rope'):
            cfg = M.Config(V=5, T=3, d=4, L=1, h=2, d_ff=8, pos=pos)
            params = M.init_params(cfg, 11)
            # 0.02 초기화 그대로는 기울기가 작아 차분이 반올림 잡음에
            # 묻힌다. 값을 키우되 ×20 은 너무 뾰족해 차분의 절단 오차가
            # h² 에 비례해 1e-5 를 넘었다(h 를 1/10 로 줄이면 오차가
            # 1/100 — 역전파가 아니라 차분 탓). ×5 에서 5.6e-10 이다.
            for t in params.values():
                t.data[:] = [v * 5 + 0.1 for v in t.data]
            ids, tg = [[1, 4, 2]], [[4, 2, 0]]
            _, loss = M.forward(params, cfg, ids, tg)
            loss.backward()
            for name, t in params.items():
                f = lambda: M.forward(params, cfg, ids, tg)[1].data[0]
                err = T.rel_error(t.grad, T.finite_difference(f, t))
                self.assertLess(err, 1e-5,
                                '%s %s %.2e' % (pos, name, err))


if __name__ == '__main__':
    unittest.main()
