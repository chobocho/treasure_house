# -*- coding: utf-8 -*-
"""3부 — 12노드 그래프를 손으로 역전파하고 차분과 견준다."""
from demo import report
from transformerlib import fmt, scalar


def names(out, leaves):
    """scalar.example_graph 문서의 이름(x1‥x3, n4‥n12)을 붙인다.
    구조를 거슬러 올라가며 찾는다 — n12 = relu(n11), n11 = n8 + n10 …"""
    n12 = out
    n11 = n12.prev[0]
    n8, n10 = n11.prev
    n6, n7 = n8.prev
    n5 = n6.prev[0]
    n4 = n5.prev[0]
    n9 = n10.prev[0]
    nm = {id(leaves[0]): 'x1', id(leaves[1]): 'x2', id(leaves[2]): 'x3'}
    for k, v in (('n4', n4), ('n5', n5), ('n6', n6), ('n7', n7),
                 ('n8', n8), ('n9', n9), ('n10', n10), ('n11', n11),
                 ('n12', n12)):
        nm[id(v)] = k
    order = sorted(scalar.topo_order(out),
                   key=lambda v: int(nm[id(v)][1:]))
    return order, nm


def sec_forward():
    out, leaves = scalar.example_graph()
    order, nm = names(out, leaves)
    rows = [['노드', '연산', '입력', '값']]
    for v in order:
        ins = ', '.join(nm[id(p)] for p in v.prev) or '-'
        rows.append([nm[id(v)], v.op or '입력', ins, '%.6f' % v.data])
    return fmt.table(rows, align='llll')


def sec_backward():
    out, leaves = scalar.example_graph()
    out.backward()
    order, nm = names(out, leaves)
    rows = [['노드', '∂출력/∂노드']]
    for v in reversed(order):
        rows.append([nm[id(v)], '%.6f' % v.grad])
    return (fmt.table(rows, align='lr')
            + '\n\n출력에서 1 로 시작해 위상정렬의 역순으로 내려간다.')


def sec_check():
    out, leaves = scalar.example_graph()
    out.backward()
    xs = [v.data for v in leaves]
    rows = [['입력', '역전파', '중심 차분 h=1e-6', '상대 오차']]
    for i, (name, v) in enumerate(zip(('x1', 'x2', 'x3'), leaves)):
        h = 1e-6
        up, dn = list(xs), list(xs)
        up[i] += h
        dn[i] -= h
        fd = (scalar.example_graph(*up)[0].data
              - scalar.example_graph(*dn)[0].data) / (2 * h)
        rel = abs(v.grad - fd) / max(abs(v.grad), abs(fd))
        rows.append([name, '%.9f' % v.grad, '%.9f' % fd, '%.1e' % rel])
    return fmt.table(rows, align='lrrr')


def sec_reuse():
    x = scalar.Value(3.0)
    y = x * x
    y.backward()
    return ('y = x·x, x = 3 에서 역전파한 dy/dx = %.1f\n'
            '(x 가 두 번 쓰였으니 두 길의 기울기 3 + 3 을 더한다)'
            % x.grad)


def main():
    return report.write('py_scalar.txt', [
        ('순전파 — 12개 노드', sec_forward()),
        ('역전파 — 노드마다 기울기', sec_backward()),
        ('차분으로 검증', sec_check()),
        ('두 번 쓴 노드는 기울기를 더한다', sec_reuse()),
    ])


if __name__ == '__main__':
    print(main())
