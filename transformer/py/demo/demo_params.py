# -*- coding: utf-8 -*-
"""7부 — 파라미터 수와 FLOPs 를 식으로 세고, 계측과 견준다."""
from demo import report
from transformerlib import fmt
from transformerlib import model as M
from transformerlib import tensor as T

GPT2 = [('GPT-2 small', 768, 12, 12), ('GPT-2 medium', 1024, 24, 16),
        ('GPT-2 large', 1280, 36, 20), ('GPT-2 XL', 1600, 48, 25)]


def sec_gpt2_small():
    c = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
    d = c.d
    blk = 12 * d * d + 13 * d
    rows = [['부분', '식', '개수']]
    rows.append(['토큰 임베딩 wte', 'V·d', '{:,}'.format(c.V * d)])
    rows.append(['위치 임베딩 wpe', 'T·d', '{:,}'.format(c.T * d)])
    rows.append(['블록 하나', '12d² + 13d', '{:,}'.format(blk)])
    rows.append(['블록 12개', 'L·(12d² + 13d)',
                 '{:,}'.format(12 * blk)])
    rows.append(['마지막 LN', '2d', '{:,}'.format(2 * d)])
    rows.append(['합계', '', '{:,}'.format(M.count_params(c))])
    return (fmt.table(rows, align='llr')
            + '\n\n출력 사영은 wte 와 묶여 있어 따로 세지 않는다.')


def sec_block():
    d = 768
    rows = [['블록 안', '모양', '개수']]
    for name, shape, n in (('ln1 g·b', '2 × [d]', 2 * d),
                           ('Wqkv', '[d, 3d]', 3 * d * d),
                           ('bqkv', '[3d]', 3 * d),
                           ('Wo · bo', '[d, d] · [d]', d * d + d),
                           ('ln2 g·b', '2 × [d]', 2 * d),
                           ('W1 · b1', '[d, 4d] · [4d]',
                            4 * d * d + 4 * d),
                           ('W2 · b2', '[4d, d] · [d]', 4 * d * d + d)):
        rows.append([name, shape, '{:,}'.format(n)])
    rows.append(['합', '12d² + 13d',
                 '{:,}'.format(12 * d * d + 13 * d)])
    return fmt.table(rows, align='llr')


def sec_family():
    rows = [['모델', 'd', 'L', 'h', '식으로 센 수', '백만']]
    for name, d, L, h in GPT2:
        c = M.Config(V=50257, T=1024, d=d, L=L, h=h, d_ff=4 * d)
        n = M.count_params(c)
        rows.append([name, str(d), str(L), str(h), '{:,}'.format(n),
                     '%.1f' % (n / 1e6)])
    return (fmt.table(rows, align='lrrrrr')
            + '\n\nd·L·h 는 data/models.tsv(OpenAI hparams) 의 값이다.')


def sec_bert():
    n = M.bert_params(V=30522, T=512, d=768, L=12)
    return ('BERT-base (V 30522, T 512, d 768, L 12,'
            ' 문장 종류 2, 풀러 포함)\n= {:,}'.format(n))


def sec_mults():
    c = M.Config(V=9, T=5, d=8, L=2, h=2, d_ff=16)
    p = M.init_params(c, 3)
    T.MULTS[0] = 0
    M.forward(p, c, [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]])
    rows = [['', '곱셈 수']]
    rows.append(['식 matmul_mults × 배치 2', '{:,}'.format(
        2 * M.matmul_mults(c, 5))])
    rows.append(['순전파를 계측한 수', '{:,}'.format(T.MULTS[0])])
    return (fmt.table(rows, align='lr')
            + '\n\n설정 V=9 T=5 d=8 L=2 h=2 d_ff=16, 길이 5 두 줄.')


def sec_six_n():
    rows = [['모델', 'n', 'N', '토큰당 학습 FLOPs', '÷ 6N']]
    for name, d, L, h in GPT2[:2]:
        c = M.Config(V=50257, T=1024, d=d, L=L, h=h, d_ff=4 * d)
        N = M.count_params(c)
        for n in (128, 1024):
            f = M.train_flops_per_token(c, n)
            rows.append([name, str(n), '{:,}'.format(N),
                         '{:,.0f}'.format(f), '%.3f' % (f / (6 * N))])
    return (fmt.table(rows, align='lrrrr')
            + '\n\n6N 은 "파라미터 하나에 곱셈 한 번" 이라는 어림이다.'
            + ' 실제로는'
            + '\n어텐션 점수의 곱셈(n²·d)이 더해지고, 위치 임베딩과 LN'
            + ' 은'
            + '\n행렬곱을 하지 않는다. 그래서 문맥이 길수록 1 보다'
            + ' 커진다.')


def main():
    return report.write('params.txt', [
        ('GPT-2 small 을 한 자리까지', sec_gpt2_small()),
        ('블록 하나의 속', sec_block()),
        ('GPT-2 네 크기', sec_family()),
        ('BERT-base', sec_bert()),
        ('곱셈 수 — 식과 계측', sec_mults()),
        ('학습 FLOPs 와 6N', sec_six_n()),
    ])


if __name__ == '__main__':
    print(main())
