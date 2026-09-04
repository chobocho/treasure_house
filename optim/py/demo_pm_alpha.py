# -*- coding: utf-8 -*-
"""10부 데모 — 알파 알고리즘: 풋프린트에서 페트리넷으로, 그리고 그 한계."""
from py import fmt
from py.pm import alpha as A
from py.pm import log as L
from py.pm import petri


def demo_footprint():
    print('■ 1. 풋프린트 행렬 — 네 가지 관계로 로그를 요약한다')
    lg = L.EventLog.from_variants({('a', 'b', 'c', 'd'): 5,
                                   ('a', 'c', 'b', 'd'): 5,
                                   ('a', 'e', 'd'): 4})
    acts, rel = A.footprint(lg)
    rows = [[''] + acts]
    for a in acts:
        rows.append([a] + [rel[(a, b)] for b in acts])
    print(fmt.table(rows, align='l' + 'c' * len(acts)))
    print('  기호: → 인과,  ← 역인과,  ‖ 병렬,  # 무관/배타')
    print('  b 와 c 가 ‖ 인 것은 두 순서가 모두 관측됐기 때문이고,')
    print('  b 와 e 가 # 인 것은 한 번도 이웃한 적이 없기 때문이다 — 배타적 선택의 흔적이다.\n')


def demo_construct():
    print('■ 2. 알파 알고리즘이 만든 페트리넷')
    lg = L.EventLog.from_variants({('a', 'b', 'c', 'd'): 5,
                                   ('a', 'c', 'b', 'd'): 5,
                                   ('a', 'e', 'd'): 4})
    net, m0, mf = A.alpha(lg)
    s = net.summary()
    print('  장소 %d개, 전이 %d개, 호 %d개' % (s['places'], s['transitions'], s['arcs']))
    rows = [['장소', '들어오는 전이', '나가는 전이', '뜻']]
    for p in sorted(net.places):
        ins = sorted(t for t in net.transitions if p in net.outs.get(t, {}))
        outs = sorted(t for t in net.transitions if p in net.ins.get(t, {}))
        if p == 'i':
            note = '시작 장소'
        elif p == 'o':
            note = '종료 장소'
        elif len(outs) > 1:
            note = '선택 (두 전이가 토큰 하나를 다툰다)'
        elif len(ins) > 1:
            note = '합류'
        else:
            note = '순차 연결'
        rows.append([p, ', '.join(ins) or '-', ', '.join(outs) or '-', note])
    print(fmt.table(rows))
    rows = [['자취', '이 모델로 재생되는가', '판정']]
    for seq in [('a', 'b', 'c', 'd'), ('a', 'c', 'b', 'd'), ('a', 'e', 'd'),
                ('a', 'b', 'd'), ('a', 'b', 'e', 'd'), ('a', 'd')]:
        ok, _ = petri.replay_trace(net, m0, mf, list(seq))
        seen = seq in lg.variants()
        rows.append([' '.join(seq), '예' if ok else '아니오',
                     '로그에 있음' if seen else ('일반화 — 로그엔 없지만 허용'
                                                 if ok else '허용 안 함')])
    print(fmt.table(rows, align='llc'))
    print('  로그에 있는 세 자취가 모두 재생된다. 로그에 없는 자취를 어디까지 허용하는지가')
    print('  11부의 "일반화"와 "정밀도" 논의로 이어진다.\n')


def demo_limits():
    print('■ 3. 알파 알고리즘의 한계 세 가지')

    print('  (1) 길이 2 루프를 병렬로 오인한다')
    lg = L.EventLog.from_variants({('a', 'b', 'a', 'b', 'c'): 5, ('a', 'b', 'c'): 5})
    _, rel = A.footprint(lg)
    print('      a>b 도 있고 b>a 도 있으므로 관계는 %s — 실제로는 루프인데 병렬로 읽힌다.'
          % rel[('a', 'b')])

    print('  (2) 잡음 한 건이 모델을 바꾼다')
    clean = L.EventLog.from_variants({('a', 'b', 'c'): 100})
    dirty = L.EventLog.from_variants({('a', 'b', 'c'): 100, ('a', 'c', 'b'): 1})
    _, r1 = A.footprint(clean)
    _, r2 = A.footprint(dirty)
    print('      깨끗한 로그: b 와 c 의 관계 = %s' % r1[('b', 'c')])
    print('      1%% 잡음:      b 와 c 의 관계 = %s   <- 인과가 병렬로 뒤집힌다' % r2[('b', 'c')])

    print('  (3) 보이지 않는 활동(기록되지 않은 단계)을 표현하지 못한다')
    print('      선택적 단계 Check 를 건너뛴 자취와 수행한 자취가 섞이면,')
    print('      알파는 그것을 "선택"으로 적을 장소를 만들 수 없다 — τ 전이가 필요한데')
    print('      알파의 구성에는 τ 가 없기 때문이다.')
    print()
    print('  이 셋 때문에 실무에서 알파 알고리즘을 그대로 쓰지 않는다. 그러나')
    print('  "직접후행 관계만으로 인과·병렬·선택을 구별할 수 있다"는 통찰은 그대로 남아,')
    print('  뒤의 모든 알고리즘이 그 위에 서 있다.')


def main():
    demo_footprint()
    demo_construct()
    demo_limits()


if __name__ == '__main__':
    main()
