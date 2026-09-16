# -*- coding: utf-8 -*-
"""optim 의 증인 시험 (PLAN.md §3.1 표 9행, SPEC.md §6).

  · Adam 편향 보정: 첫 스텝의 갱신은 lr·sign(g) 다. 보정이 없으면
    lr·(1−β1)/√(1−β2) · sign(g) 로 작아진다.
  · AdamW: 기울기가 0 이어도 θ 는 스텝마다 정확히 (1 − lr·wd) 배.
    감쇠는 기울기와 무관하다 — Adam + L2 와 다른 점.
  · 학습률 일정: 0·워밍업 끝·가운데·끝 값을 박는다.
"""
import math
import unittest

from transformerlib import optim as O
from transformerlib import tensor as T


def param(values, grads, name='h0.W1'):
    t = T.Tensor(values, (len(values),), requires_grad=True)
    t.grad = list(grads)
    return {name: t}


class TestAdam(unittest.TestCase):
    def test_first_step_is_lr_times_sign(self):
        p = param([1.0, -2.0, 0.5, 3.0], [0.3, -0.1, 7.0, -250.0], 'b')
        opt = O.AdamW(p, wd=0.1)
        opt.step(p, lr=0.01)
        got = [a - b
               for a, b in zip(p['b'].data, [1.0, -2.0, 0.5, 3.0])]
        for g, dg in zip([0.3, -0.1, 7.0, -250.0], got):
            self.assertLess(abs(dg + 0.01 * math.copysign(1, g)), 1e-9)

    def test_without_bias_correction_first_step_is_smaller(self):
        p = param([0.0], [0.5], 'b')
        O.AdamW(p, wd=0.0, bias_correction=False).step(p, lr=1.0)
        want = -(1 - 0.9) / math.sqrt(1 - 0.95)
        self.assertAlmostEqual(p['b'].data[0], want, places=6)

    def test_matches_formula_over_three_steps(self):
        grads = [[0.2], [-0.4], [0.1]]
        p = param([1.0], grads[0], 'b')
        opt = O.AdamW(p, wd=0.0)
        m = v = 0.0
        theta = 1.0
        for t, g in enumerate(grads, 1):
            p['b'].grad = list(g)
            opt.step(p, lr=0.1)
            m = 0.9 * m + 0.1 * g[0]
            v = 0.95 * v + 0.05 * g[0] ** 2
            mh, vh = m / (1 - 0.9 ** t), v / (1 - 0.95 ** t)
            theta -= 0.1 * mh / (math.sqrt(vh) + 1e-8)
            self.assertAlmostEqual(p['b'].data[0], theta, places=14)
        self.assertEqual(opt.t, 3)


class TestAdamW(unittest.TestCase):
    def test_decay_independent_of_gradient(self):
        p = param([2.0, -4.0], [0.0, 0.0], 'h0.W1')
        opt = O.AdamW(p, wd=0.1)
        for _ in range(5):
            p['h0.W1'].grad = [0.0, 0.0]
            opt.step(p, lr=0.5)
        f = (1 - 0.5 * 0.1) ** 5
        self.assertAlmostEqual(p['h0.W1'].data[0], 2.0 * f, places=14)
        self.assertAlmostEqual(p['h0.W1'].data[1], -4.0 * f, places=14)

    def test_only_matrices_decay(self):
        for name, want in (('wte', True), ('wpe', True),
                           ('h3.Wqkv', True),
                           ('h0.Wo', True), ('h1.W1', True),
                           ('h1.W2', True), ('h0.bqkv', False),
                           ('h0.ln1_g', False), ('lnf_b', False)):
            self.assertEqual(O.decays(name), want, name)
        p = param([2.0], [0.0], 'h0.ln1_g')
        O.AdamW(p, wd=0.1).step(p, lr=0.5)
        self.assertEqual(p['h0.ln1_g'].data, [2.0])


class TestClip(unittest.TestCase):
    def test_clips_to_one(self):
        p = param([0.0, 0.0], [3.0, 4.0])
        n = O.clip_grad_norm(p, 1.0)
        self.assertEqual(n, 5.0)
        g = p['h0.W1'].grad
        self.assertAlmostEqual(g[0], 3.0 / (5.0 + 1e-6), places=15)
        self.assertLessEqual(math.hypot(*g), 1.0)

    def test_small_gradient_untouched(self):
        p = param([0.0, 0.0], [0.3, 0.4])
        self.assertAlmostEqual(O.clip_grad_norm(p, 1.0), 0.5, places=15)
        self.assertEqual(p['h0.W1'].grad, [0.3, 0.4])

    def test_norm_over_all_parameters(self):
        p = param([0.0], [1.0], 'a')
        p.update(param([0.0], [2.0], 'b'))
        p.update(param([0.0], [2.0], 'c'))
        self.assertEqual(O.clip_grad_norm(p, 10.0), 3.0)


class TestSchedule(unittest.TestCase):
    def test_pinned_values(self):
        f = lambda t: O.lr_schedule(t, 1e-3, 1e-4, 100, 1100)
        self.assertAlmostEqual(f(1), 1e-5, places=18)
        self.assertEqual(f(100), 1e-3)
        self.assertAlmostEqual(f(600), 5.5e-4, places=15)
        self.assertAlmostEqual(f(1100), 1e-4, places=15)

    def test_warmup_rises_then_cosine_falls(self):
        xs = [O.lr_schedule(t, 1.0, 0.0, 10, 50) for t in range(1, 51)]
        self.assertTrue(all(a < b for a, b in zip(xs[:9], xs[1:10])))
        self.assertTrue(all(a >= b for a, b in zip(xs[9:], xs[10:])))

    def test_vaswani_schedule(self):
        """논문 식 (3): d^{−½}·min(t^{−½}, t·w^{−1.5}). 꼭짓점 t = w."""
        f = lambda t: O.noam(t, 512, 4000)
        self.assertAlmostEqual(f(4000), 512 ** -0.5 * 4000 ** -0.5,
                               places=15)
        self.assertLess(f(3999), f(4000))
        self.assertLess(f(4001), f(4000))


class TestSgdMomentum(unittest.TestCase):
    def quad(self, opt_step, steps=60):
        """f(x) = ½·(10x² + y²) 의 골짜기."""
        p = param([1.0, 1.0], [0.0, 0.0], 'a')
        for _ in range(steps):
            x, y = p['a'].data
            p['a'].grad = [10 * x, y]
            opt_step(p)
        x, y = p['a'].data
        return 0.5 * (10 * x * x + y * y)

    def test_sgd_descends(self):
        self.assertLess(self.quad(lambda p: O.sgd_step(p, 0.05)), 0.01)

    def test_momentum_beats_sgd_in_the_valley(self):
        """학습률이 작으면 완만한 y 방향이 SGD 로는 0.99ⁿ 으로만 준다.
        모멘텀은 두 방향 모두 |r| = √β ≈ 0.949 로 준다."""
        sgd = self.quad(lambda p: O.sgd_step(p, 0.01))
        mom = O.Momentum(beta=0.9)
        self.assertLess(self.quad(lambda p: mom.step(p, 0.01)), sgd / 5)


if __name__ == '__main__':
    unittest.main()
