# -*- coding: utf-8 -*-
"""8부 — 순수 파이썬으로 작은 모델을 실제로 학습한다.

c/ 가 몇 분에 끝내는 일을 파이썬은 모델을 아주 작게 해야 겨우 한다.
그래도 손실이 내려가는 것을 눈으로 보는 것이 이 장의 요점이다 —
같은 train.step 이 C 에서는 그대로 train.c 의 tfs_train_step 이다.
"""
import io
import os

from demo import report
from transformerlib import fmt
from transformerlib import model as M
from transformerlib import tokenizer as tk
from transformerlib import train as TR

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def run():
    path = os.path.join(BASE, 'corpus', 'tasks', 'add_train.txt')
    text = io.open(path, encoding='utf-8').read()[:13 * 2000]
    vocab, merges = tk.load(os.path.join(BASE, 'ckpt', 'tok', 'add'))
    ids = tk.Tokenizer(vocab, merges).encode(text)
    cfg = M.Config(V=len(vocab), T=13, d=16, L=1, h=2, d_ff=64)
    log = []
    TR.train(cfg, ids, steps=120, B=4, lr_max=1e-2, warmup=10, seed=1,
             newline=vocab.index(b'\n'),
             on_step=lambda t, l, lr, n: log.append((t, l, lr, n)))
    return cfg, log


def sec_loss(cfg, log):
    rows = [['스텝', '손실', '학습률', '기울기 노름']]
    for t, l, lr, n in log:
        if t == 1 or t % 10 == 0:
            rows.append([str(t), '%.4f' % l, '%.2e' % lr, '%.3f' % n])
    head = '%r · 파라미터 %d개 · 배치 4' % (cfg, M.count_params(cfg))
    return head + '\n\n' + fmt.table(rows, align='rrrr')


def main():
    cfg, log = run()
    return report.write('py_tiny.txt', [
        ('순수 파이썬 학습 — 덧셈 과제', sec_loss(cfg, log)),
    ])


if __name__ == '__main__':
    print(main())
