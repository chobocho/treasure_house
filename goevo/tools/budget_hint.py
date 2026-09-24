# -*- coding: utf-8 -*-
"""budget_hint.py — 부 예산을 릴리스마다 나눈다 (make budget-hint, PLAN.md §4).

    python3 tools/budget_hint.py

릴리스 하나에 기능 장을 몇 장 줄지를 기억으로 정하면, 기억에 크게 남은
릴리스가 부풀고 조용한 릴리스가 굶는다. 그래서 그 릴리스 노트의 길이
(docs/relnotes/go1.N.txt 의 바이트)에 비례해 나누고, 최신 세 릴리스
(1.25–1.27)는 두 배로 센다.

부 예산에서 먼저 뺀다: 부 표지와 머리말 2장, 릴리스마다 장 표지·개관
장·퀴즈 3장. 남은 것을 비례로 나누고 끝수는 큰 나머지 차례로 준다
(같은 입력이면 늘 같은 답). O(릴리스 수 log 릴리스 수).
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PER_PART, PER_RELEASE = 2, 3
PARTS = {3: ['1.1', '1.2', '1.3', '1.4'],
         4: ['1.5', '1.6', '1.7', '1.8', '1.9', '1.10'],
         5: ['1.11', '1.12', '1.13', '1.14', '1.15', '1.16', '1.17'],
         6: ['1.18', '1.19', '1.20'],
         7: ['1.21', '1.22', '1.23', '1.24'],
         8: ['1.25', '1.26', '1.27']}
WEIGHTS = {'1.25': 2, '1.26': 2, '1.27': 2}


def split(budget, lengths, weights=None):
    """[(버전, 노트 길이)] → [(버전, 기능 장 수)] (입력 차례 그대로)."""
    weights = weights or {}
    left = budget - PER_PART - PER_RELEASE * len(lengths)
    w = [(v, n * weights.get(v, 1)) for v, n in lengths]
    total = float(sum(x for _, x in w)) or 1.0
    exact = [(v, left * x / total) for v, x in w]
    base = dict((v, int(e)) for v, e in exact)
    rest = left - sum(base.values())
    order = sorted(exact, key=lambda ve: (-(ve[1] - int(ve[1])), ve[0]))
    for v, _ in order[:rest]:
        base[v] += 1
    return [(v, base[v]) for v, _ in lengths]


def main():
    budget = {}
    with io.open(os.path.join(BASE, 'deck', 'budget.txt'),
                 encoding='utf-8') as f:
        for line in f:
            line = line.split('#')[0].split()
            if len(line) == 2:
                budget[int(line[0])] = int(line[1])
    for part, vs in sorted(PARTS.items()):
        lens = [(v, os.path.getsize(os.path.join(
            BASE, 'docs', 'relnotes', 'go%s.txt' % v))) for v in vs]
        got = split(budget[part], lens, WEIGHTS)
        print('%d부 (예산 %d): %s' % (part, budget[part], ' · '.join(
            '%s %d장' % (v, n) for v, n in got)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
