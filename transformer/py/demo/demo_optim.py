# -*- coding: utf-8 -*-
"""8부 — Adam 편향 보정, AdamW 감쇠, 학습률 일정."""
import math

from demo import report
from transformerlib import fmt
from transformerlib import optim as O
from transformerlib import tensor as T


def one(value, grad, name='b'):
    t = T.Tensor([value], (1,), requires_grad=True)
    t.grad = [grad]
    return {name: t}


def sec_first_step():
    rows = [['기울기 g', '보정한 첫 갱신', '보정 없는 첫 갱신',
             'lr·sign(g)']]
    for g in (1e-4, 0.3, -2.0, 250.0):
        a, b = one(0.0, g), one(0.0, g)
        O.AdamW(a, wd=0.0).step(a, lr=0.01)
        O.AdamW(b, wd=0.0, bias_correction=False).step(b, lr=0.01)
        rows.append(['%g' % g, '%+.6f' % a['b'].data[0],
                     '%+.6f' % b['b'].data[0],
                     '%+.6f' % (-0.01 * math.copysign(1, g))])
    return (fmt.table(rows, align='rrrr')
            + '\n\nβ1 0.9 · β2 0.95 · lr 0.01. 보정하면 첫 갱신 크기가'
            + ' g 와'
            + '\n무관하게 lr 이다. 보정이 없으면 (1−β1)/√(1−β2) ≈ 0.447'
            + ' 배.')


def sec_decay():
    rows = [['스텝', 'AdamW θ (g = 0)', '(1 − lr·wd)^t', 'Adam+L2 θ']]
    a = one(2.0, 0.0, 'h0.W1')
    opt = O.AdamW(a, wd=0.1)
    b = one(2.0, 0.0, 'h0.W1')
    opt2 = O.AdamW(b, wd=0.0)
    for t in range(1, 6):
        a['h0.W1'].grad = [0.0]
        opt.step(a, lr=0.5)
        b['h0.W1'].grad = [0.1 * b['h0.W1'].data[0]]   # L2 를 g 에 섞음
        opt2.step(b, lr=0.5)
        rows.append([str(t), '%.6f' % a['h0.W1'].data[0],
                     '%.6f' % (2.0 * (1 - 0.05) ** t),
                     '%.6f' % b['h0.W1'].data[0]])
    return (fmt.table(rows, align='rrrr')
            + '\n\nAdamW 는 기울기와 따로 θ 를 줄인다. L2 를 기울기에'
            + ' 섞으면'
            + '\n√v̂ 로 나뉘어 크기와 무관한 lr 만큼씩 움직인다 —'
            + ' 감쇠가 아니다.')


def sec_schedule():
    rows = [['스텝 t', '워밍업+코사인', '논문 식 (3) d=512 w=4000']]
    for t in (1, 50, 100, 500, 1000, 4000, 8000, 20000):
        rows.append([str(t),
                     '%.3e' % O.lr_schedule(t, 1e-3, 1e-4, 100, 20000),
                     '%.3e' % O.noam(t, 512, 4000)])
    return (fmt.table(rows, align='rrr')
            + '\n\n가운데 열: lr_max 1e-3, lr_min 1e-4, 워밍업 100,'
            + ' 전체 20000.')


def sec_clip():
    rows = [['기울기', '노름', '자른 뒤', '자른 뒤 노름']]
    for g in ([0.3, 0.4], [3.0, 4.0], [30.0, -40.0]):
        p = {'a': T.Tensor([0.0, 0.0], (2,), requires_grad=True)}
        p['a'].grad = list(g)
        n = O.clip_grad_norm(p, 1.0)
        c = p['a'].grad
        rows.append(['%g, %g' % tuple(g), '%.3f' % n,
                     '%.6f, %.6f' % tuple(c), '%.6f' % math.hypot(*c)])
    return (fmt.table(rows, align='rrrr')
            + '\n\n노름이 1 을 넘으면 방향은 두고 길이만 1/(n + 1e-6)'
            + ' 배.')


def main():
    return report.write('optim.txt', [
        ('Adam 의 첫 스텝 — 편향 보정', sec_first_step()),
        ('AdamW 의 감쇠는 기울기와 따로', sec_decay()),
        ('학습률 일정', sec_schedule()),
        ('기울기 자르기', sec_clip()),
    ])


if __name__ == '__main__':
    print(main())
