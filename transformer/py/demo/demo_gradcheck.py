# -*- coding: utf-8 -*-
"""3·4부 — 연산마다 역전파를 중심 차분과 견준 표.

tensor·ops·attention 의 모든 연산을 같은 방법으로 잰다:
출력에 고정된 난수 가중치 w 를 곱해 더한 Σ w·f(x) 의 기울기를
역전파와 차분으로 구해, 벡터 크기에 견준 상대 오차를 적는다.
"""
from demo import report
from transformerlib import attention as A
from transformerlib import fmt, ops, posenc
from transformerlib import tensor as T
from transformerlib.rng import Rng


def rand(shape, seed, lo=-1.0, hi=1.0):
    r = Rng(seed)
    return T.Tensor([lo + (hi - lo) * r.uniform()
                     for _ in range(T.numel(shape))], shape,
                    requires_grad=True)


def worst(f, inputs, seed=7):
    for x in inputs:
        x.grad = None
    out = f(*inputs)
    w = rand(out.shape, seed)
    w.requires_grad = False
    T.sum(T.mul(out, w)).backward()
    errs = []
    for x in inputs:
        num = T.finite_difference(
            lambda: T.sum(T.mul(f(*inputs), w)).data[0], x)
        errs.append(T.rel_error(x.grad, num))
    return max(errs)


CASES = [
    ('add (퍼짐 (4,3)+(3,))', T.add, [((4, 3), 1), ((3,), 2)]),
    ('mul', T.mul, [((2, 3), 3), ((2, 3), 4)]),
    ('div', T.div, [((2, 3), 5), ((2, 3), 6, 0.5, 2.0)]),
    ('pow 3', lambda x: T.pow(x, 3), [((2, 3), 7)]),
    ('exp', T.exp, [((2, 3), 8)]),
    ('log', T.log, [((2, 3), 9, 0.5, 2.0)]),
    ('tanh', T.tanh, [((2, 3), 10)]),
    ('matmul (3,4)@(4,2)', T.matmul, [((3, 4), 11), ((4, 2), 12)]),
    ('matmul 배치', T.matmul, [((2, 3, 4), 13), ((4, 5), 14)]),
    ('transpose', lambda x: T.transpose(x, 0, 1), [((3, 4), 15)]),
    ('sum axis 1', lambda x: T.sum(x, 1), [((3, 4), 16)]),
    ('softmax', ops.softmax, [((2, 5), 17, -3, 3)]),
    ('log_softmax', ops.log_softmax, [((2, 5), 18, -3, 3)]),
    ('cross_entropy', lambda z: ops.cross_entropy(z, [1, 4]),
     [((2, 5), 19, -2, 2)]),
    ('layernorm', ops.layernorm, [((3, 5), 20, -2, 2),
                                  ((5,), 21, 0.5, 1.5), ((5,), 22)]),
    ('gelu', ops.gelu, [((2, 6), 23, -3, 3)]),
    ('causal_softmax', ops.causal_softmax, [((2, 4, 4), 24, -2, 2)]),
    ('rope', posenc.rope, [((1, 2, 3, 4), 25)]),
    ('scaled_dot_product',
     lambda q, k, v: A.scaled_dot_product(q, k, v)[0],
     [((1, 3, 4), 26), ((1, 3, 4), 27), ((1, 3, 4), 28)]),
]


def sec_table():
    rows = [['연산', '입력 수', '최대 상대 오차']]
    for name, f, specs in CASES:
        inputs = [rand(*s) for s in specs]
        rows.append([name, str(len(inputs)), '%.1e' % worst(f, inputs)])
    return (fmt.table(rows, align='lrr')
            + '\n\n차분 h = 1e-6, 오차 = max|역전파 − 차분| /'
            + ' max(크기).')


def main():
    return report.write('py_gradcheck.txt', [
        ('연산마다 역전파 대 중심 차분', sec_table()),
    ])


if __name__ == '__main__':
    print(main())
