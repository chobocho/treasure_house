# -*- coding: utf-8 -*-
"""8부 — 합성 과제를 C 로 학습하고 시험 줄의 정답률을 잰다.

과제마다 모델 모양은 같다. 줄 길이만큼의 문맥(T)으로 줄 머리에 맞춰
자르므로(aligned) 창 하나에 문제가 정확히 하나 든다.
"""
import os

from demo import crun, report

# d = 48 로는 덧셈이 손실 고원(≈1.59)에서 벗어나는 스텝이 1,000 에서
# 3,000 넘게까지 들쭉날쭉해, 같은 설정도 스텝 수에 따라 정답률이
# 100 % 와 7 % 로 갈렸다. d = 64 도 2,200 스텝 설정에서는 뒤집은
# 덧셈이 고원에 남았다 — 스텝 수를 3,000 으로 두었다(PLAN.md 7단계).
SHAPE = dict(d=64, L=2, h=4, B=32, lr=6e-3, warmup=150, seed=1, log=50,
             aligned=True)

TASKS = {
    'add': dict(vocab='ckpt/tok/add', T=13, steps=3000, sep='=',
                title='세 자리 덧셈 — 답을 뒤집어 적는다'),
    'addplain': dict(vocab='ckpt/tok/add', T=13, steps=3000, sep='=',
                     title='세 자리 덧셈 — 답을 그대로 적는다'),
    'sort': dict(vocab='ckpt/tok/sort', T=14, steps=2000, sep='>',
                 title='글자 여섯 개 정렬'),
    'reverse': dict(vocab='ckpt/tok/reverse', T=14, steps=2000, sep='<',
                    title='글자 여섯 개 뒤집기'),
    'parity': dict(vocab='ckpt/tok/parity', T=19, steps=1600, sep='=',
                   title='열여섯 비트의 홀짝'),
}


def run(name):
    spec = dict(SHAPE, **TASKS[name])
    ckpt = os.path.join('ckpt', 'c_%s.ckpt' % name)
    train_file = os.path.join('corpus', 'tasks', '%s_train.txt' % name)
    test_file = os.path.join('corpus', 'tasks', '%s_test.txt' % name)
    head, steps, _ = crun.train(spec, ckpt, train_file)
    test = crun.tfs('accuracy', ckpt, spec['vocab'], test_file,
                    '--sep', spec['sep'], '--show', 8)
    seen = crun.tfs('accuracy', ckpt, spec['vocab'], train_file,
                    '--sep', spec['sep'], '--show', 0, '--limit', 1000)
    report.write('curve_c_%s.txt' % name,
                 [('학습 곡선 (스텝 손실 학습률 노름)',
                   crun.curve_text(steps))])
    return report.write('c_%s.txt' % name, [
        (spec['title'], head + '\n\n' + crun.pick(steps, 500)),
        ('시험 줄 1000개 — 학습에 없던 문제', test),
        ('학습 줄 앞 1000개', seen),
    ])
