# -*- coding: utf-8 -*-
"""vec3 — 3차원 벡터와 3×3 행렬 (SPEC §1.4).

벡터는 원소 셋짜리 리스트, 행렬은 행 셋의 리스트다. 클래스를 만들지
않은 까닭: 자바스크립트 판의 배열과 모양이 같아야 골든 벡터를 그대로
주고받는다.
"""
import math


def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def scale(a, k):
    return [a[0] * k, a[1] * k, a[2] * k]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def norm(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    n = norm(a)
    return [a[0] / n, a[1] / n, a[2] / n]


def dist(a, b):
    return norm(sub(a, b))


# ---------------------------------------------------------- 3×3 행렬
def eye3():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def from_cols(a, b, c):
    """열 벡터 셋 → 행렬."""
    return [[a[0], b[0], c[0]], [a[1], b[1], c[1]], [a[2], b[2], c[2]]]


def transpose(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def matvec(m, v):
    return [dot(m[0], v), dot(m[1], v), dot(m[2], v)]


def matmul(a, b):
    bt = transpose(b)
    return [[dot(a[i], bt[j]) for j in range(3)] for i in range(3)]


def det3(m):
    """첫 행으로 전개 (7부의 3×3 행렬식)."""
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def inv3(m):
    """여인수 행렬 / 행렬식. 행렬식이 0 이면 ZeroDivisionError."""
    d = det3(m)
    c = [[m[(j + 1) % 3][(i + 1) % 3] * m[(j + 2) % 3][(i + 2) % 3]
          - m[(j + 1) % 3][(i + 2) % 3] * m[(j + 2) % 3][(i + 1) % 3]
          for j in range(3)] for i in range(3)]
    return [[c[i][j] / d for j in range(3)] for i in range(3)]


# ENU(동·북·위) → NED(북·동·아래). (1,1,0)/√2 축으로 π 회전이다.
ENU_TO_NED = [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]]
