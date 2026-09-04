# -*- coding: utf-8 -*-
"""10부 데모 — 인덕티브 마이너와 휴리스틱 마이너."""
from py import fmt
from py.pm import heuristic as H
from py.pm import inductive as IM
from py.pm import log as L
from py.pm import petri
from py.pm import tree as T


def demo_rediscovery():
    print('■ 1. 생성 모델을 되찾는가 — 인덕티브 마이너')
    lg = L.generate(n_cases=500, seed=21, noise=0.0)
    t = IM.mine(lg)
    print('  생성 규칙(우리가 로그를 만든 방법):')
    print('    Request → Approve, 반려되면 Reject 뒤 다시 Request')
    print('    그 다음 Order (때때로 Check 와 병렬), 그 다음 Receive → Pay')
    print()
    print('  발견된 프로세스 트리:')
    print('    %s' % repr(t))
    print()
    net, m0, mf = T.to_petri(t)
    s = net.summary()
    rows = [['항목', '값']]
    rows.append(['트리 노드 수', '%d' % t.size()])
    rows.append(['페트리넷 장소', '%d' % s['places']])
    rows.append(['페트리넷 전이', '%d (보이지 않는 전이 %d)' % (s['transitions'], s['silent'])])
    ok = all(petri.replay_trace(net, m0, mf, list(v), max_silent=14)[0]
             for v in lg.variants())
    rows.append(['로그의 모든 변형이 재생되는가', '예' if ok else '아니오'])
    print(fmt.table(rows, align='lr'))
    print('  구조가 정확히 일치한다: 순차 → 안에 루프(Request-Approve / Reject)와')
    print('  병렬(∧) 안의 선택(×(Check, τ)) 이 들어 있다. 보이지 않는 전이 τ 가')
    print('  "Check 를 건너뛴다"를 표현한다 — 알파 알고리즘이 하지 못하던 일이다.\n')


def demo_noise_robustness():
    print('■ 2. 잡음이 있으면 — 그리고 걸러내면')
    lg = L.generate(n_cases=400, seed=14, noise=0.4)
    rows = [['최소 변형 빈도', '남은 케이스', '남은 변형', '발견된 모델', '구조가 있는가']]
    for mc in (1, 3, 8, 20, 40):
        sub = lg.filter_variants(mc)
        t = IM.mine(lg, min_count=mc)
        flower = (t.op == T.LOOP and len(t.children) == 2
                  and t.children[0].op == T.TAU and t.children[1].op == T.XOR
                  and all(c.op == T.ACT for c in t.children[1].children))
        rows.append(['%d' % mc, '%d' % len(sub), '%d' % len(sub.variants()),
                     repr(t)[:44] + ('…' if len(repr(t)) > 44 else ''),
                     '아니오 (플라워)' if flower else '예'])
    print(fmt.table(rows, align='rrrll'))
    print('  잡음이 심하면 인덕티브 마이너는 "플라워 모델"로 물러선다 — 무엇이든')
    print('  허용하는 모델이다. 적합도는 1 이지만 아무것도 설명하지 못한다.')
    print('  희귀 변형을 걸러내면 구조가 되살아난다. 무엇을 걸러낼지가 실무의 판단이다.\n')


def demo_dependency():
    print('■ 3. 휴리스틱 마이너의 의존도 — 빈도로 잡음을 이긴다')
    lg = L.generate(n_cases=500, seed=31, noise=0.35)
    dep = H.dependency(lg)
    dfg = lg.dfg()
    items = sorted(dfg.items(), key=lambda kv: -kv[1])
    rows = [['a → b', '|a>b|', '|b>a|', '의존도 dep(a,b)', '해석']]
    for (a, b), c in items[:14]:
        d = dep.get((a, b), 0.0)
        back = dfg.get((b, a), 0)
        if d > 0.9:
            note = '강한 인과'
        elif d > 0.5:
            note = '인과로 볼 만함'
        elif abs(d) < 0.3:
            note = '병렬 또는 잡음'
        else:
            note = '약함'
        rows.append(['%s → %s' % (a, b), '%d' % c, '%d' % back, '%+.4f' % d, note])
    print(fmt.table(rows, align='lrrrl'))
    print('  Order 와 Check 처럼 양방향 빈도가 비슷하면 의존도가 0 근처가 된다 —')
    print('  병렬의 표지다. 반대로 한쪽만 크면 1 에 가까워진다.')
    print('  분모의 +1 은 관측이 적을 때 확신하지 않게 만드는 장치다:')
    print('  1회만 본 관계의 의존도는 1/(1+0+1) = 0.5 로 중간값이다.\n')


def demo_threshold():
    print('■ 4. 문턱을 올리면 그래프가 정리된다')
    lg = L.generate(n_cases=500, seed=31, noise=0.35)
    rows = [['의존도 문턱', '빈도 문턱', '남은 간선', '전체 간선', '빈도 커버리지']]
    for dt, ft in ((0.0, 1), (0.5, 1), (0.9, 1), (0.9, 10), (0.95, 30)):
        g = H.dependency_graph(lg, dep_threshold=dt, freq_threshold=ft,
                               all_tasks_connected=False)
        st = H.graph_stats(lg, g)
        rows.append(['%.2f' % dt, '%d' % ft, '%d' % st['edges_kept'],
                     '%d' % st['edges_all'], '%.1f%%' % (100 * st['coverage'])])
    print(fmt.table(rows, align='rrrrr'))
    print('  간선 수는 크게 줄지만 빈도 커버리지는 훨씬 덜 준다 — 잘려 나가는 것이')
    print('  대부분 "드문" 간선이라는 뜻이다. 이것이 잡음 필터링이 통하는 이유다.')
    print('  다만 병렬 쌍(Order ‖ Check)도 의존도가 0 근처라 함께 잘린다 —')
    print('  완전한 휴리스틱 마이너가 AND-분기를 따로 판정해야 하는 이유다.')


def main():
    demo_rediscovery()
    demo_noise_robustness()
    demo_dependency()
    demo_threshold()


if __name__ == '__main__':
    main()
