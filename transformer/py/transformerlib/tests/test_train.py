# -*- coding: utf-8 -*-
"""train 의 증인 시험 (PLAN.md §3.1 표 10행, SPEC.md §4·§6).

  · 작은 모델이 배치 하나를 300 스텝 안에 손실 < 0.05 로 외운다 —
    순전파·역전파·옵티마이저가 한 줄로 이어져 있다는 가장 싼 증거.
  · 체크포인트: 쓰고 읽고 다시 쓰면 바이트까지 같다. SPEC §4.1 의
    풀어 본 예(66 파라미터)는 정확히 296바이트이고 머리말이 맞다.
  · 배치 시작 위치는 SPEC §6.1 그대로.
"""
import io
import os
import struct
import tempfile
import unittest

from transformerlib import model as M
from transformerlib import train as TR
from transformerlib.rng import Rng


class TestBatches(unittest.TestCase):
    def test_all_starts(self):
        self.assertEqual(TR.batch_starts(list(range(10)), 4),
                         [0, 1, 2, 3, 4, 5])

    def test_aligned_starts_follow_newlines(self):
        toks = [5, 5, 0, 5, 5, 5, 0, 5, 5, 0, 5, 5]   # 0 이 줄바꿈
        self.assertEqual(TR.batch_starts(toks, 3, newline=0), [0, 3, 7])

    def test_batch_uses_spec_rng_order(self):
        toks = list(range(100, 130))
        starts = TR.batch_starts(toks, 4)
        x, y = TR.get_batch(toks, starts, 3, 4, Rng(8))
        r = Rng(8)
        for b in range(3):
            s = starts[r.randint(len(starts))]
            self.assertEqual(x[b], toks[s:s + 4])
            self.assertEqual(y[b], toks[s + 1:s + 5])

    def test_too_short_corpus(self):
        with self.assertRaises(ValueError):
            TR.batch_starts([1, 2, 3], 3)


class TestLearning(unittest.TestCase):
    def test_overfits_one_batch(self):
        cfg = M.Config(V=11, T=8, d=16, L=1, h=2, d_ff=32)
        params = M.init_params(cfg, 1)
        r = Rng(2)
        x = [[r.randint(11) for _ in range(8)] for _ in range(2)]
        y = [[r.randint(11) for _ in range(8)] for _ in range(2)]
        opt = TR.make_optimizer(params)
        loss = None
        for t in range(1, 301):
            loss = TR.step(params, cfg, opt, x, y, lr=3e-2)[0]
            if loss < 0.05:
                break
        self.assertLess(loss, 0.05)
        self.assertLessEqual(t, 300)

    def test_train_is_deterministic(self):
        cfg = M.Config(V=6, T=4, d=8, L=1, h=2, d_ff=16)
        toks = [i % 6 for i in range(60)]
        a = TR.train(cfg, toks, steps=5, B=2, lr_max=1e-2, warmup=2,
                     seed=3)
        b = TR.train(cfg, toks, steps=5, B=2, lr_max=1e-2, warmup=2,
                     seed=3)
        self.assertEqual(a[1], b[1])
        self.assertEqual(a[0]['wte'].data, b[0]['wte'].data)
        self.assertEqual([row[0] for row in a[1]], [1, 2, 3, 4, 5])

    def test_eval_loss_uses_fixed_windows(self):
        cfg = M.Config(V=6, T=4, d=8, L=1, h=2, d_ff=16)
        p = M.init_params(cfg, 4)
        toks = [i % 6 for i in range(30)]
        self.assertEqual(TR.eval_loss(p, cfg, toks, 2),
                         TR.eval_loss(p, cfg, toks, 2))


class TestCheckpoint(unittest.TestCase):
    def test_spec_worked_example_bytes(self):
        cfg = M.Config(V=2, T=2, d=2, L=1, h=1, d_ff=4)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.ckpt')
            TR.save_ckpt(p, cfg, M.init_params(cfg, 0))
            raw = io.open(p, 'rb').read()
        self.assertEqual(len(raw), 296)
        self.assertEqual(raw[:4], b'TFS1')
        self.assertEqual(struct.unpack('<7i', raw[4:32]),
                         (2, 2, 2, 1, 1, 4, 1))
        # ln1_g 는 바이트 64 부터, 값 1.0
        self.assertEqual(struct.unpack('<2f', raw[64:72]), (1.0, 1.0))

    def test_round_trip_is_byte_identical(self):
        for pos in ('learned', 'sin', 'rope'):
            cfg = M.Config(V=9, T=5, d=8, L=2, h=2, d_ff=16, pos=pos)
            with tempfile.TemporaryDirectory() as d:
                a, b = os.path.join(d, 'a'), os.path.join(d, 'b')
                TR.save_ckpt(a, cfg, M.init_params(cfg, 5))
                cfg2, params2 = TR.load_ckpt(a)
                TR.save_ckpt(b, cfg2, params2)
                self.assertEqual(io.open(a, 'rb').read(),
                                 io.open(b, 'rb').read(), pos)
                self.assertEqual(repr(cfg2), repr(cfg))

    def test_bad_magic(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x')
            io.open(p, 'wb').write(b'NOPE' + b'\0' * 28)
            with self.assertRaises(ValueError):
                TR.load_ckpt(p)

    def test_optimizer_state_round_trip(self):
        cfg = M.Config(V=5, T=3, d=4, L=1, h=2, d_ff=8)
        params = M.init_params(cfg, 6)
        opt = TR.make_optimizer(params)
        TR.step(params, cfg, opt, [[1, 2, 3]], [[2, 3, 4]], lr=1e-2)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'o.opt')
            TR.save_opt(p, opt, cfg)
            opt2 = TR.make_optimizer(params)
            TR.load_opt(p, opt2, cfg)
            self.assertEqual(opt2.t, 1)
            q = os.path.join(d, 'p.opt')
            TR.save_opt(q, opt2, cfg)
            self.assertEqual(io.open(p, 'rb').read(),
                             io.open(q, 'rb').read())


class TestAccuracy(unittest.TestCase):
    def test_greedy_accuracy_counts_exact_answers(self):
        cfg = M.Config(V=4, T=6, d=8, L=1, h=2, d_ff=16)
        p = M.init_params(cfg, 7)
        acc, rows = TR.task_accuracy(p, cfg, [[0, 1, 2, 3, 3]], 3)
        self.assertIn(acc, (0.0, 1.0))
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0][1]), 2)     # 정답 길이만큼 만든다


if __name__ == '__main__':
    unittest.main()
