# -*- coding: utf-8 -*-
"""linalg — 작은 정사각 행렬의 가우스 소거 (7부의 소거법 그대로).

믹서의 계수(T10), 행렬식(T9), 최소 스냅의 8N×8N 연립방정식(T27)이
쓴다. N ≤ 12 라 행렬은 96×96 이 가장 크다 — O(n³) 소거로 충분하다.
"""


def _copy(a):
    return [[float(x) for x in row] for row in a]


def solve(a, b):
    """A x = b. 부분 피벗팅(각 열에서 절댓값이 가장 큰 행을 피벗으로).

    피벗을 고르지 않으면 첫 피벗이 0 인 행렬에서 멈추고, 0 에 가까운
    피벗으로 나누면 반올림 오차가 커진다. O(n³) 시간, O(n²) 공간."""
    m = _copy(a)
    x = [float(v) for v in b]
    n = len(m)
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-14:
            raise ValueError('특이 행렬 — 해가 하나로 정해지지 않는다')
        m[col], m[piv] = m[piv], m[col]
        x[col], x[piv] = x[piv], x[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            if f:
                for k in range(col, n):
                    m[r][k] -= f * m[col][k]
                x[r] -= f * x[col]
    for r in range(n - 1, -1, -1):
        s = x[r] - sum(m[r][k] * x[k] for k in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def rank(a, tol=1e-10):
    """행 사다리꼴로 줄여 피벗 개수를 센다. 직사각 행렬도 된다."""
    m = _copy(a)
    rows, cols = len(m), len(m[0]) if m else 0
    r = 0
    for col in range(cols):
        if r == rows:
            break
        piv = max(range(r, rows), key=lambda i: abs(m[i][col]))
        if abs(m[piv][col]) < tol:
            continue
        m[r], m[piv] = m[piv], m[r]
        for i in range(r + 1, rows):
            f = m[i][col] / m[r][col]
            for k in range(col, cols):
                m[i][k] -= f * m[r][k]
        r += 1
    return r


def det(a):
    """소거하며 피벗을 곱한다. 행을 바꿀 때마다 부호가 뒤집힌다."""
    m = _copy(a)
    n, d = len(m), 1.0
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if m[piv][col] == 0.0:
            return 0.0
        if piv != col:
            m[col], m[piv] = m[piv], m[col]
            d = -d
        d *= m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            for k in range(col, n):
                m[r][k] -= f * m[col][k]
    return d
