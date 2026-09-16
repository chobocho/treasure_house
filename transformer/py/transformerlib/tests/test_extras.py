# -*- coding: utf-8 -*-
"""extras 의 증인 시험 (PLAN.md §3.1 표 12행).

  · 온라인 소프트맥스: 타일 크기가 무엇이든 한 번에 계산한 어텐션
    출력과 ≤ 1e-12.
  · GQA 에서 그룹 수 = 헤드 수이면 MHA 와 정확히 같다.
  · LoRA: B = 0 이면 출력이 그대로다. **계획서는 "그때 기울기가 A 에
    닿는다" 고 적었지만 거짓이다** — ∂ℓ/∂A = xᵀ·g·Bᵀ 이고 B = 0 이면
    정확히 0 이다. 참인 성질은 "B 가 먼저 기울기를 받고, B 가 한 번
    움직이면 A 도 받는다" 이다. 시험은 그것을 본다.
  · MLM: 가린 자리 비율과 80/10/10, 손실은 가린 자리에서만.
"""
import math
import unittest

from transformerlib import attention as A
from transformerlib import extras as X
from transformerlib import model as M
from transformerlib import tensor as T
from transformerlib.rng import Rng
from transformerlib.tests.test_tensor import check, rand


class TestOnlineSoftmax(unittest.TestCase):
    def test_equals_direct_for_any_tile(self):
        r = Rng(1)
        n, dv = 37, 5
        xs = [r.normal() * 4 for _ in range(n)]
        vs = [[r.normal() for _ in range(dv)] for _ in range(n)]
        p = [0.0] * n
        from transformerlib import ops
        ops._softmax_row(xs, 0, n, p)
        want = [math.fsum(p[j] * vs[j][c] for j in range(n))
                for c in range(dv)]
        for tile in (1, 2, 5, 16, 37, 100):
            got = X.online_attention_row(xs, vs, tile)
            err = max(abs(a - b) for a, b in zip(got, want))
            self.assertLess(err, 1e-12, 'tile=%d %.2e' % (tile, err))

    def test_logsumexp(self):
        xs = [1000.0, 999.0, -5.0, 3.0]
        want = 1000.0 + math.log(1 + math.exp(-1) + math.exp(-1005)
                                 + math.exp(-997))
        for tile in (1, 3, 4):
            self.assertAlmostEqual(X.online_logsumexp(xs, tile), want,
                                   places=12)

    def test_tiled_attention_matches_sdpa(self):
        q, k = rand((1, 6, 4), 2), rand((1, 6, 4), 3)
        v = rand((1, 6, 4), 4)
        want = A.scaled_dot_product(q, k, v, causal=True)[0].data
        for tile in (1, 2, 4):
            got = X.tiled_attention(q, k, v, tile)
            self.assertLess(max(abs(a - b) for a, b in zip(got, want)),
                            1e-12)


class TestGqa(unittest.TestCase):
    def test_groups_equal_heads_is_mha(self):
        d, h = 8, 4
        W = rand((d, 3 * d), 5)
        b = rand((3 * d,), 6)
        Wo, bo = rand((d, d), 7), rand((d,), 8)
        x = rand((2, 5, d), 9)
        mha = A.multi_head_attention(x, W, b, Wo, bo, heads=h)[0]
        Wq, Wkv = X.split_qkv(W, d)
        bq, bkv = T.Tensor(b.data[:d], (d,)), T.Tensor(b.data[d:],
                                                        (2 * d,))
        gqa = X.grouped_query_attention(x, Wq, bq, Wkv, bkv, Wo, bo,
                                        heads=h, groups=h)
        self.assertEqual(gqa.data, mha.data)

    def test_mqa_shape_and_backward(self):
        d, h, g = 8, 4, 1
        dk = d // h
        args = [rand((1, 3, d), 10), rand((d, d), 11), rand((d,), 12),
                rand((d, 2 * g * dk), 13), rand((2 * g * dk,), 14),
                rand((d, d), 15), rand((d,), 16)]
        f = lambda *a: X.grouped_query_attention(*a, heads=h, groups=g)
        self.assertEqual(f(*args).shape, (1, 3, d))
        check(self, f, args)

    def test_kv_cache_size(self):
        cfg = M.Config(V=10, T=1024, d=768, L=12, h=12, d_ff=3072)
        mha = X.kv_cache_floats(cfg, 1024, groups=12)
        self.assertEqual(mha, 2 * 12 * 1024 * 768)
        self.assertEqual(X.kv_cache_floats(cfg, 1024, groups=1),
                         mha // 12)

    def test_rejects_bad_groups(self):
        with self.assertRaises(ValueError):
            X.grouped_query_attention(rand((1, 2, 8), 1), None, None,
                                      None, None, None, None,
                                      heads=4, groups=3)


class TestLora(unittest.TestCase):
    def setUp(self):
        self.x = rand((3, 6), 20)
        self.W, self.b = rand((6, 5), 21), rand((5,), 22)
        self.Am = rand((6, 2), 23)
        self.Bm = T.zeros((2, 5), requires_grad=True)

    def test_zero_B_leaves_output_unchanged(self):
        base = T.add(T.matmul(self.x, self.W), self.b).data
        got = X.lora_linear(self.x, self.W, self.b, self.Am, self.Bm,
                            alpha=4, r=2).data
        self.assertEqual(got, base)

    def test_zero_B_gets_gradient_but_A_does_not(self):
        y = X.lora_linear(self.x, self.W, self.b, self.Am, self.Bm,
                          4, 2)
        T.sum(T.mul(y, rand((3, 5), 24))).backward()
        self.assertTrue(any(g != 0.0 for g in self.Bm.grad))
        self.assertEqual(self.Am.grad, [0.0] * 12)

    def test_after_B_moves_A_gets_gradient(self):
        self.Bm.data[:] = [0.01 * (k + 1) for k in range(10)]
        f = lambda A_, B_: X.lora_linear(self.x, self.W, self.b, A_, B_,
                                         4, 2)
        check(self, f, [self.Am, self.Bm])
        self.assertTrue(any(g != 0.0 for g in self.Am.grad))

    def test_merge_equals_adapter(self):
        self.Bm.data[:] = [0.1 * (k - 4) for k in range(10)]
        y = X.lora_linear(self.x, self.W, self.b, self.Am, self.Bm,
                          4, 2)
        W2 = X.lora_merge(self.W, self.Am, self.Bm, 4, 2)
        y2 = T.add(T.matmul(self.x, W2), self.b)
        err = max(abs(a - b) for a, b in zip(y.data, y2.data))
        self.assertLess(err, 1e-12)

    def test_parameter_saving(self):
        self.assertEqual(X.lora_params(768, 768, 8), 2 * 768 * 8)


class TestMlm(unittest.TestCase):
    def test_mask_statistics(self):
        ids = [5] * 20000
        inp, pos = X.mlm_mask(ids, Rng(1), vocab=50, mask_id=49)
        self.assertLess(abs(len(pos) / 20000 - 0.15), 0.01)
        masked = sum(1 for i in pos if inp[i] == 49)
        same = sum(1 for i in pos if inp[i] == 5)
        self.assertLess(abs(masked / len(pos) - 0.8), 0.02)
        self.assertLess(abs(same / len(pos) - 0.1), 0.02)
        outside = [i for i in range(20000) if i not in set(pos)]
        self.assertTrue(all(inp[i] == 5 for i in outside))

    def test_encoder_sees_the_future(self):
        cfg = M.Config(V=7, T=4, d=4, L=1, h=2, d_ff=8)
        p = M.init_params(cfg, 3)
        a, _ = M.forward(p, cfg, [[1, 2, 3, 4]], causal=False)
        b, _ = M.forward(p, cfg, [[1, 2, 3, 6]], causal=False)
        self.assertNotEqual(a.data[:7], b.data[:7])

    def test_loss_only_on_masked_positions(self):
        cfg = M.Config(V=9, T=5, d=8, L=1, h=2, d_ff=16)
        p = M.init_params(cfg, 4)
        ids = [1, 2, 3, 4, 5]
        loss, inp, pos = X.mlm_loss(p, cfg, ids, Rng(7), mask_id=8,
                                    p_mask=0.5)
        logits, _ = M.forward(p, cfg, [inp], causal=False)
        from transformerlib import ops
        rows = [logits.data[i * 9:(i + 1) * 9] for i in pos]
        want = ops.cross_entropy(T.Tensor([v for r in rows for v in r],
                                          (len(pos), 9)),
                                 [ids[i] for i in pos]).data[0]
        self.assertAlmostEqual(loss.data[0], want, places=14)


if __name__ == '__main__':
    unittest.main()
