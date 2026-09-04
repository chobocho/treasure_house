# -*- coding: utf-8 -*-
"""휴리스틱 마이너 — 빈도를 보고 잡음을 견딘다.

   알파 알고리즘은 "한 번이라도 a 다음에 b 가 왔는가"만 본다. 그래서 기록 오류
   하나가 모델 전체를 바꾼다. 휴리스틱 마이너는 <얼마나 자주>를 본다.

       의존도  dep(a, b) = (|a>b| − |b>a|) / (|a>b| + |b>a| + 1)

   이 값은 −1 과 1 사이이고, a 다음에 b 가 압도적으로 자주 오면 1 에 가깝다.
   +1 이 분모에 있는 것은 관측이 적을 때 자신 없어 하도록 만드는 장치다
   (a>b 가 1회, b>a 가 0회면 dep = 0.5 로 중간값이 된다).

   문턱을 넘는 간선만 남기면 잡음이 걸러진 <의존 그래프>가 나온다. 페트리넷이
   아니라 그래프라서 실행 의미론이 약하지만, 실무의 첫 탐색에는 이쪽이 훨씬 낫다.
"""


def dependency(log):
    """{(a, b): 의존도}. 값이 클수록 a → b 라는 인과가 확실하다."""
    dfg = log.dfg()
    acts = sorted(log.activities())
    out = {}
    for a in acts:
        for b in acts:
            ab = dfg.get((a, b), 0)
            ba = dfg.get((b, a), 0)
            if a == b:
                out[(a, b)] = ab / float(ab + 1)          # 자기 루프는 따로 센다
            elif ab + ba > 0:
                out[(a, b)] = (ab - ba) / float(ab + ba + 1)
    return out


def dependency_graph(log, dep_threshold=0.9, freq_threshold=1,
                     all_tasks_connected=True):
    """문턱을 넘는 간선만 남긴 의존 그래프.

       all_tasks_connected 이면, 문턱 때문에 고립된 활동이 생기지 않도록
       각 활동의 가장 강한 간선 하나는 반드시 남긴다 — 실무 구현의 관례다.
    """
    dfg = log.dfg()
    dep = dependency(log)
    acts = sorted(log.activities())
    edges = {}
    for (a, b), d in dep.items():
        if d >= dep_threshold and dfg.get((a, b), 0) >= freq_threshold:
            edges[(a, b)] = {'dep': d, 'freq': dfg.get((a, b), 0)}
    if all_tasks_connected:
        for a in acts:
            outs = [(b, dep.get((a, b), -2)) for b in acts if (a, b) in dfg]
            if outs and not any((a, b) in edges for b in acts):
                b = max(outs, key=lambda t: t[1])[0]
                edges[(a, b)] = {'dep': dep.get((a, b), 0.0),
                                 'freq': dfg[(a, b)], 'kept': 'best-out'}
            ins = [(b, dep.get((b, a), -2)) for b in acts if (b, a) in dfg]
            if ins and not any((b, a) in edges for b in acts):
                b = max(ins, key=lambda t: t[1])[0]
                edges[(b, a)] = {'dep': dep.get((b, a), 0.0),
                                 'freq': dfg[(b, a)], 'kept': 'best-in'}
    return edges


def graph_stats(log, edges):
    dfg = log.dfg()
    total = sum(dfg.values())
    kept = sum(v['freq'] for v in edges.values())
    return {'edges_all': len(dfg), 'edges_kept': len(edges),
            'freq_all': total, 'freq_kept': kept,
            'coverage': kept / float(total) if total else 0.0}
