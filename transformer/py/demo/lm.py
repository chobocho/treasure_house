# -*- coding: utf-8 -*-
"""8·10부 — 한국어·영어 언어 모델을 C 로 학습하고 글을 뽑는다.

모양은 한국어와 영어가 같다(바이트 BPE 어휘 512). 다른 것은 말뭉치뿐이라
두 곡선과 두 퍼플렉시티를 나란히 놓을 수 있다. 샘플이 "한국어처럼
읽히는가" 는 사람의 판단이다 — 덱은 샘플을 그대로 싣고 판단은 독자에게
맡긴다.
"""
import math
import os

from demo import crun, report

# 스텝 수는 한 번의 학습이 3분 안에 끝나도록 이 기계에서 재어 정했다
# (PLAN.md §0.7). 기록은 deck/budget.txt 아래에도 남긴다.
SPEC = dict(T=48, d=64, L=3, h=4, B=16, steps=640, lr=5e-3, warmup=50,
            seed=1, log=20, eval=160, eval_batches=8)

LANGS = {
    'ko': dict(vocab='ckpt/tok/ko512', prompts=['김 첨지는', '나는 '],
               title='한국어 — 위키문헌 공유저작물 34편'),
    'en': dict(vocab='ckpt/tok/en512', prompts=['ROMEO:\n', 'The '],
               title='영어 — tinyshakespeare 앞부분'),
}


def sample_text(ckpt, vocab, prompt, n, temp, top_k, top_p, seed):
    args = ['sample', ckpt, vocab, '--prompt', prompt, '--n', n,
            '--temp', temp, '--seed', seed]
    if top_k:
        args += ['--top-k', top_k]
    if top_p:
        args += ['--top-p', top_p]
    out = crun.tfs(*args)
    return out.split('\n', 1)[1].rstrip('\n')      # 첫 줄(ids)은 뺀다


def run(lang):
    info = LANGS[lang]
    spec = dict(SPEC, vocab=info['vocab'])
    ckpt = os.path.join('ckpt', 'c_%s.ckpt' % lang)
    tr, va = crun.split_text(lang, lang)
    head, steps, evals = crun.train(spec, ckpt, tr, va)

    rows = ['스텝   검증 손실   퍼플렉시티 exp(손실)']
    for step, loss in evals:
        rows.append('%5s   %.4f      %8.2f' % (step, float(loss),
                                             math.exp(float(loss))))
    samples = []
    p0 = info['prompts'][0]
    for temp in ('0', '0.5', '0.8', '1.0'):
        samples.append('-- 온도 %s · top-k 40 --\n%s'
                       % (temp, sample_text(ckpt, info['vocab'], p0, 60,
                                            temp, 40, None, 7)))
    samples.append('-- 온도 1.0 · top-p 0.9 --\n%s'
                   % sample_text(ckpt, info['vocab'], p0, 60, '1.0',
                                 None, '0.9', 7))
    other = sample_text(ckpt, info['vocab'], info['prompts'][1], 80,
                        '0.8', 40, None, 11)
    report.write('curve_c_%s.txt' % lang,
                 [('학습 곡선 (스텝 손실 학습률 노름)',
                   crun.curve_text(steps)),
                  ('검증 손실 (스텝 손실)',
                   '\n'.join('%s %s' % e for e in evals))])
    return report.write('c_%s.txt' % lang, [
        (info['title'], head + '\n\n' + crun.pick(steps, 100)),
        ('검증 손실과 퍼플렉시티', '\n'.join(rows)),
        ('같은 프롬프트, 거르개만 바꿔서', '\n\n'.join(samples)),
        ('다른 프롬프트 · 온도 0.8 · top-k 40', other),
    ])
