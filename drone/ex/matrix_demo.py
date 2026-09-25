# -*- coding: utf-8 -*-
"""행렬 계산 한 판 — 7부 2장 (droneshow.vec3, droneshow.linalg).

곱의 결합, 행렬식 = 삼중곱, 소거로 풀기(피벗이 0 일 때 줄 바꾸기),
계수, 직교 행렬, ENU → NED 가 반사가 아니라 회전이라는 것.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import linalg, mixer, params  # noqa: E402
from droneshow import vec3 as V  # noqa: E402

A = [[2.0, 0.0, 1.0], [1.0, 3.0, 0.0], [0.0, 1.0, 4.0]]
B = [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
x = [1.0, -1.0, 2.0]

if __name__ == '__main__':
    print('(AB)x =', V.matvec(V.matmul(A, B), x))
    print('A(Bx) =', V.matvec(A, V.matvec(B, x)))
    cols = [[A[r][k] for r in range(3)] for k in range(3)]
    print('det A =', V.det3(A), ' 삼중곱 =',
          V.dot(cols[0], V.cross(cols[1], cols[2])))
    print('det B =', V.det3(B), ' (두 축을 맞바꾼 거울)')
    print('A y = (4, 4, 9) 의 해 y =', linalg.solve(A, [4.0, 4.0, 9.0]))
    print('첫 피벗이 0: [[0,1],[1,1]] z = (2,3) → z =',
          linalg.solve([[0.0, 1.0], [1.0, 1.0]], [2.0, 3.0]))
    print('계수: [[1,2],[2,4]] →', linalg.rank([[1, 2], [2, 4]]),
          ' 추력→힘·토크 사상 →',
          linalg.rank(mixer.wrench_map(params.load())))
    N = V.ENU_TO_NED
    print('ENU→NED: det =', V.det3(N), ' NᵀN = I:',
          V.matmul(V.transpose(N), N) == V.eye3())
