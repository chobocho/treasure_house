# -*- coding: utf-8 -*-
"""자원 배치 — 프로세스 개선을 최적화 문제로 적는다.

   12부의 마지막 단계다. 병목을 찾았다면 다음 질문은 "그래서 무엇을 바꿀 것인가"이고,
   그 답은 언제나 <제약 아래에서 무언가를 최소화하는 문제>로 적힌다.

   여기서는 두 가지를 다룬다.
     1. 활동-자원 배치      → 할당 문제 (헝가리안, 7부)
     2. 용량 증설 예산 배분  → 정수계획 (분지한정, 7부)
"""
import math

from py import milp
from py.pm import perf


def cost_matrix(log, activities=None, resources=None, default=None):
    """자원 r 이 활동 a 를 한 번 처리하는 평균 시간. 관측이 없으면 default.

       실제 로그에서 그대로 뽑아내는 것이 요점이다 — 추정치를 가정하지 않는다.
    """
    acc = {}
    for t in log:
        for e in t:
            if e.resource is None or 'duration' not in e.attrs:
                continue
            k = (e.activity, e.resource)
            d = acc.setdefault(k, [])
            d.append(float(e.attrs['duration']))
    acts = sorted(activities or {a for (a, _) in acc})
    res = sorted(resources or {r for (_, r) in acc})
    allv = [v for vs in acc.values() for v in vs]
    fallback = default if default is not None else (
        math.fsum(allv) / len(allv) if allv else 1.0)
    M = []
    for a in acts:
        row = []
        for r in res:
            vs = acc.get((a, r))
            row.append(math.fsum(vs) / len(vs) if vs else fallback)
        M.append(row)
    return acts, res, M


def assign_resources(log, activities=None, resources=None, scale=1000):
    """활동마다 자원 하나를 배정해 총 처리시간을 최소화한다 (할당 문제).

       헝가리안 알고리즘은 정수 비용을 받으므로 실수 시간을 scale 배해 반올림한다.
       그 반올림 오차가 최적성을 해치지 않을 만큼 scale 을 크게 잡는다.
    """
    acts, res, M = cost_matrix(log, activities, resources)
    n = max(len(acts), len(res))
    big = max(max(row) for row in M) * scale * 10 if M else 1
    C = [[int(round(M[i][j] * scale)) if i < len(acts) and j < len(res) else big
          for j in range(n)] for i in range(n)]
    _, assign = milp.hungarian(C)
    out, total = [], 0.0
    for i, a in enumerate(acts):
        j = assign[i]
        if j < len(res):
            out.append((a, res[j], M[i][j]))
            total += M[i][j]
    # 헝가리안이 돌려준 비용에는 채워 넣은 가짜 행의 값이 섞여 있으므로,
    # 실제 배정된 쌍만 다시 더한다. (가짜 행의 비용은 어느 열을 가져가든 같아서
    # 최적 배정 자체는 영향을 받지 않는다.)
    return out, total


def capacity_plan(log, budget, unit_cost=None, gain=None):
    """예산 안에서 어느 활동의 용량을 늘릴 것인가 (0/1 배낭 = 정수계획).

       각 활동에 담당자를 한 명 더 붙이면 그 활동의 대기시간이 절반이 된다고 하자.
       그러면 절감되는 총 대기시간이 <가치>, 인건비가 <무게>, 예산이 <용량>이다.
       7부의 배낭 문제 그대로다.

       gain[a] 를 주면 그 값을 절감량으로 쓰고, 없으면 총 대기시간의 절반으로 둔다.
    """
    bt = perf.bottlenecks(log)
    acts = [r['activity'] for r in bt]
    values, weights = [], []
    for r in bt:
        g = (gain or {}).get(r['activity'], 0.5 * r['total_waiting'])
        w = (unit_cost or {}).get(r['activity'], 1)
        values.append(int(round(g)))
        weights.append(int(w))
    best, pick = milp.knapsack_dp(values, weights, int(budget))
    return {'chosen': [acts[i] for i in pick], 'saved': best,
            'spent': sum(weights[i] for i in pick),
            'candidates': list(zip(acts, values, weights))}
