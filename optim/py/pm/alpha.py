# -*- coding: utf-8 -*-
"""알파 알고리즘 — 이벤트 로그에서 페트리넷을 뽑아내는 첫 방법.

   아이디어 하나로 요약된다: 로그에서 관찰되는 <직접후행 관계>만 보면 활동 사이의
   인과·선택·병렬을 구별할 수 있다.

       a > b   : 어딘가에서 a 바로 다음에 b 가 왔다
       a → b   : a > b 이고 b > a 는 아니다        (인과)
       a ‖ b   : a > b 이고 b > a 다               (병렬)
       a # b   : 둘 다 아니다                      (배타·무관)

   이 네 관계를 표로 적은 것이 <풋프린트 행렬>이고, 알파 알고리즘은 그 표만 보고
   페트리넷을 만든다. 한계도 분명하다 — 짧은 루프, 보이지 않는 전이, 잡음에 약하다.
   그래서 11부에서 더 견고한 방법(인덕티브 마이너)으로 넘어간다.
"""
import itertools

from py.pm import petri


def footprint(log):
    """풋프린트 행렬을 만든다. 반환: (활동 목록, {(a,b): 관계 문자})."""
    acts = sorted(log.activities())
    dfg = log.dfg()
    rel = {}
    for a in acts:
        for b in acts:
            ab = (a, b) in dfg
            ba = (b, a) in dfg
            if ab and not ba:
                rel[(a, b)] = '→'
            elif ba and not ab:
                rel[(a, b)] = '←'
            elif ab and ba:
                rel[(a, b)] = '‖'
            else:
                rel[(a, b)] = '#'
    return acts, rel


def _causal(rel, A, B):
    return all(rel[(a, b)] == '→' for a in A for b in B)


def _independent(rel, S):
    """S 안의 서로 다른 두 활동이 모두 # 관계인가 (동시에 일어날 수 없는 선택지)."""
    return all(rel[(a, b)] == '#' for a in S for b in S if a != b)


def alpha(log, max_set=3):
    """알파 알고리즘.  반환: (PetriNet, 초기 마킹, 최종 마킹)

       단계
         1. 활동 집합 T, 시작 활동 T_I, 종료 활동 T_O 를 구한다
         2. 조건을 만족하는 (A, B) 쌍을 모두 찾는다:
            A 안은 서로 #, B 안은 서로 #, 그리고 모든 a∈A, b∈B 에서 a→b
         3. 극대인 쌍만 남긴다 (다른 쌍에 포함되지 않는 것)
         4. 쌍마다 장소를 하나 만들고 A 에서 들어오고 B 로 나가는 호를 놓는다
         5. 시작 장소 i, 종료 장소 o 를 붙인다

       max_set 은 A, B 의 최대 크기다. 원 알고리즘은 제한이 없지만 부분집합이
       2^|T| 개라, 교재 예제 규모에서는 3 이면 충분하고 훨씬 빠르다.
    """
    acts, rel = footprint(log)
    starts = set(log.start_activities())
    ends = set(log.end_activities())

    # 2. 후보 쌍 생성
    subsets = []
    for k in range(1, max_set + 1):
        for S in itertools.combinations(acts, k):
            if _independent(rel, S):
                subsets.append(frozenset(S))
    pairs = []
    for A in subsets:
        for B in subsets:
            if _causal(rel, A, B):
                pairs.append((A, B))

    # 3. 극대 쌍만 남긴다
    maximal = []
    for (A, B) in pairs:
        dominated = False
        for (C, D) in pairs:
            if (A, B) != (C, D) and A <= C and B <= D:
                dominated = True
                break
        if not dominated:
            maximal.append((A, B))

    # 4~5. 페트리넷 구성
    net = petri.PetriNet(name='alpha')
    for a in acts:
        net.add_transition(a, a)
    src = net.add_place('i')
    snk = net.add_place('o')
    for idx, (A, B) in enumerate(sorted(maximal, key=lambda p: (sorted(p[0]), sorted(p[1])))):
        p = net.add_place('p(%s|%s)' % (','.join(sorted(A)), ','.join(sorted(B))))
        for a in sorted(A):
            net.add_arc(a, p)
        for b in sorted(B):
            net.add_arc(p, b)
    for a in sorted(starts):
        net.add_arc(src, a)
    for a in sorted(ends):
        net.add_arc(a, snk)
    return net, {'i': 1}, {'o': 1}
