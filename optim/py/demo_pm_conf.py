# -*- coding: utf-8 -*-
"""11부 데모 — 적합도: 토큰 재생 vs 정렬, 그리고 네 가지 품질 축."""
from py import fmt
from py.pm import conformance as C
from py.pm import inductive as IM
from py.pm import log as L
from py.pm import tree as T

SHORT = {'Request': 'Req', 'Approve': 'App', 'Reject': 'Rej', 'Order': 'Ord',
         'Check': 'Chk', 'Receive': 'Rec', 'Pay': 'Pay'}


def s(a):
    return SHORT.get(a, a) if a else '»'


def trace_model(log):
    """로그의 변형만 정확히 허용하는 모델 — 정밀도 1, 일반화 0 의 극단."""
    seqs = sorted(log.variants())
    return T.Node(T.XOR, children=[
        T.Node(T.SEQ, children=[T.act(a) for a in seq]) for seq in seqs])


def demo_replay_vs_align():
    print('■ 1. 같은 편차, 두 가지 측정 — 토큰 재생과 정렬')
    net, m0, mf = T.to_petri(T.Node(T.SEQ, children=[T.act(a) for a in
                                                     ['a', 'b', 'c', 'd']]))
    cases = [(['a', 'b', 'c', 'd'], '완벽'),
             (['a', 'c', 'd'], 'b 가 빠짐'),
             (['a', 'b', 'x', 'c', 'd'], '모르는 활동 x 가 끼어듦'),
             (['a', 'c', 'b', 'd'], 'b 와 c 의 순서가 바뀜'),
             (['a', 'b'], '중간에 끊김'),
             (['d', 'c', 'b', 'a'], '완전히 거꾸로')]
    rows = [['자취', '설명', '토큰재생 적합도', '정렬 비용', '정렬 적합도',
             '로그 이동', '모델 이동']]
    for tr, note in cases:
        r = C.token_replay(net, m0, mf, tr)
        f, a = C.alignment_fitness(net, m0, mf, tr)
        rows.append([' '.join(tr), note, '%.4f' % r['fitness'], '%d' % a['cost'],
                     '%.4f' % f, '%d' % a['log_moves'], '%d' % a['model_moves']])
    print(fmt.table(rows, align='llrrrrr'))
    print('  모델은 a → b → c → d 다. 정렬 비용은 "몇 번의 어긋남이 있었는가"를')
    print('  정확히 센다: 빠진 사건은 모델 이동 1, 끼어든 사건은 로그 이동 1.')
    print('  토큰 재생은 값싸지만 편차의 종류를 구별하지 못한다.\n')


def demo_moves():
    print('■ 2. 정렬이 실제로 무엇을 짝지었는가')
    net, m0, mf = T.to_petri(T.Node(T.SEQ, children=[T.act(a) for a in
                                                     ['a', 'b', 'c', 'd']]))
    tr = ['a', 'x', 'c', 'b', 'd']
    a = C.align(net, m0, mf, tr)
    rows = [['단계', '로그 쪽', '모델 쪽', '이동 종류', '비용']]
    for i, (kind, lab, t) in enumerate(a['moves']):
        if kind == C.SYNC_MOVE:
            rows.append(['%d' % (i + 1), s(lab), s(net.label_of(t)), '동기', '0'])
        elif kind == C.LOG_MOVE:
            rows.append(['%d' % (i + 1), s(lab), '»', '로그 이동', '1'])
        else:
            lbl = net.label_of(t)
            rows.append(['%d' % (i + 1), '»', s(lbl) if lbl else 'τ',
                         '모델 이동' + ('(τ)' if lbl is None else ''),
                         '0' if lbl is None else '1'])
    print(fmt.table(rows, align='rlllr'))
    print('  총 비용 %d, 탐색한 상태 %d개.' % (a['cost'], a['visited']))
    print('  » 는 "그쪽에는 대응하는 것이 없다"는 표시다. 이 표가 곧 "어디가 어떻게')
    print('  어긋났는가"에 대한 답이고, 감사·규정 준수 보고서의 원자료가 된다.\n')


def demo_quality():
    print('■ 3. 네 가지 품질 축 — 하나만 보면 속는다')
    lg = L.generate(n_cases=300, seed=51)
    models = [
        ('인덕티브 마이너', IM.mine(lg)),
        ('플라워 (무엇이든 허용)', IM._flower(lg.activities())),
        ('자취 모델 (로그 그대로)', trace_model(lg)),
        ('틀린 모델 (Req→App→Pay)',
         T.Node(T.SEQ, children=[T.act(a) for a in ['Request', 'Approve', 'Pay']])),
    ]
    rows = [['모델', '적합도', '정밀도', '단순성', '모델 크기', '한 줄 평']]
    for name, tree in models:
        net, m0, mf = T.to_petri(tree)
        f, _ = C.log_fitness(net, m0, mf, lg)
        p = C.precision(net, m0, mf, lg)
        simp = C.simplicity(net)
        if f < 0.95:
            note = '적합도가 낮다 — 로그를 설명하지 못한다'
        elif p < 0.4:
            note = '과소적합 — 다 허용한다'
        elif tree.size() > 50:
            note = '과적합 — 로그를 통째로 외웠다'
        else:
            note = '균형'
        rows.append([name, '%.4f' % f, '%.4f' % p, '%.4f' % simp,
                     '%d' % tree.size(), note])
    print(fmt.table(rows, align='lrrrrl'))
    print('  플라워 모델은 적합도가 1 인데 정밀도가 바닥이다 — 아무것도 설명하지 않는다.')
    print('  자취 모델은 정밀도가 높지만 크기가 폭발하고 새 케이스를 전부 위반으로 본다.')
    print('  인덕티브 마이너의 모델만 두 축을 함께 지킨다. 하나의 수로 모델을 평가할 수')
    print('  없다는 것이 이 표의 요점이다.\n')


def demo_astar():
    print('■ 4. 정렬은 최단경로 문제다 — 휴리스틱이 탐색을 줄인다')
    lg = L.generate(n_cases=200, seed=52)
    net, m0, mf = T.to_petri(IM.mine(lg))
    rows = [['자취 (약칭)', '길이', '비용', '다익스트라', 'A* (단순 h)', 'A* (LP h)',
             'LP 절감']]
    variants = sorted(lg.variants(), key=len)
    picks = [variants[0], variants[len(variants) // 2], variants[-1]]
    for seq in picks:
        tr = list(seq) + ['ZZ', 'YY']            # 모델에 없는 활동을 덧붙인다
        d = C.align(net, m0, mf, tr, heuristic=False)
        a = C.align(net, m0, mf, tr, heuristic=True)
        b = C.align_lp(net, m0, mf, tr)
        assert d['cost'] == a['cost'] == b['cost']
        rows.append([' '.join(s(x) for x in tr[:8]) + ('…' if len(tr) > 8 else ''),
                     '%d' % len(tr), '%d' % a['cost'],
                     '%d' % d['visited'], '%d' % a['visited'], '%d' % b['visited'],
                     '%.1f%%' % (100.0 * (1 - b['visited'] / float(d['visited'])))])
    print(fmt.table(rows, align='lrrrrrr'))
    print('  세 방법의 비용은 언제나 같다 — 두 휴리스틱 모두 허용 가능하므로')
    print('  최적성이 보존된다. 달라지는 것은 탐색한 상태 수뿐이다.')
    print()
    print('  단순 휴리스틱은 "모델에 아예 없는 활동의 개수"다.')
    print('  LP 휴리스틱은 마킹 방정식의 선형계획 완화를 매 상태에서 푼다:')
    print('    min  sum r_a + sum_{보이는 t} y_t - 2 sum s_a')
    print('    s.t. m + N y = m_f,  s_a <= r_a,  s_a <= sum_{label(t)=a} y_t,  y, s >= 0')
    print('  정수 제약을 풀어 준 완화의 최적값이므로 진짜 비용보다 클 수 없다 —')
    print('  7부에서 분지한정의 하한을 얻던 논리 그대로다.')
    print('  대가는 명확하다: 상태마다 LP 를 한 번 푼다. 상태 수는 줄지만 한 상태가 비싸다.')


def main():
    demo_replay_vs_align()
    demo_moves()
    demo_quality()
    demo_astar()


if __name__ == '__main__':
    main()
