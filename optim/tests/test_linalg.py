# -*- coding: utf-8 -*-
"""linalg 모듈 테스트 — 구현보다 먼저 쓴다(RED).

   경계값을 특히 본다: 1×1, 특이행렬, 영벡터, 피벗이 0인 행렬,
   조건수가 큰 힐베르트 행렬.
"""
import math
import unittest

from py import linalg as la


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


class TestVector(unittest.TestCase):
    def test_basic_ops(self):
        x, y = [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]
        self.assertEqual(la.vadd(x, y), [5.0, 7.0, 9.0])
        self.assertEqual(la.vsub(y, x), [3.0, 3.0, 3.0])
        self.assertEqual(la.vscale(2.0, x), [2.0, 4.0, 6.0])
        self.assertEqual(la.dot(x, y), 32.0)

    def test_axpy(self):
        self.assertEqual(la.axpy(2.0, [1.0, 1.0], [3.0, 4.0]), [5.0, 6.0])

    def test_norms(self):
        v = [3.0, -4.0]
        self.assertTrue(close(la.norm(v), 5.0))
        self.assertTrue(close(la.norm1(v), 7.0))
        self.assertTrue(close(la.norminf(v), 4.0))
        self.assertEqual(la.norm([]), 0.0)          # 빈 벡터 경계

    def test_norm_no_overflow(self):
        # 스케일링 없이 제곱하면 1e200 에서 넘친다 — 넘치지 않아야 한다.
        v = [1e200, 1e200]
        self.assertTrue(math.isfinite(la.norm(v)))
        self.assertTrue(close(la.norm(v), math.sqrt(2.0) * 1e200, 1e-12))

    def test_dim_mismatch(self):
        with self.assertRaises(ValueError):
            la.dot([1.0], [1.0, 2.0])


class TestMatrix(unittest.TestCase):
    def test_matvec_matmul(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(la.matvec(A, [1.0, 1.0]), [3.0, 7.0])
        self.assertEqual(la.matmul(A, la.identity(2)), A)
        self.assertEqual(la.transpose(A), [[1.0, 3.0], [2.0, 4.0]])

    def test_identity_zeros(self):
        self.assertEqual(la.identity(1), [[1.0]])
        self.assertEqual(la.zeros(2, 3), [[0.0] * 3, [0.0] * 2 and [0.0] * 3])

    def test_matmul_shape_error(self):
        with self.assertRaises(ValueError):
            la.matmul([[1.0, 2.0]], [[1.0, 2.0]])


class TestLU(unittest.TestCase):
    def test_solve_2x2(self):
        A = [[2.0, 1.0], [1.0, 3.0]]
        b = [3.0, 5.0]
        x = la.solve(A, b)
        self.assertTrue(close(x[0], 0.8) and close(x[1], 1.4))

    def test_needs_pivot(self):
        # (1,1) 성분이 0 이라 피벗팅 없이는 0 으로 나눈다.
        A = [[0.0, 1.0], [1.0, 0.0]]
        x = la.solve(A, [2.0, 3.0])
        self.assertTrue(close(x[0], 3.0) and close(x[1], 2.0))

    def test_1x1(self):
        self.assertTrue(close(la.solve([[4.0]], [8.0])[0], 2.0))

    def test_singular_raises(self):
        with self.assertRaises(la.SingularMatrix):
            la.solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_det_inv(self):
        A = [[4.0, 7.0], [2.0, 6.0]]
        self.assertTrue(close(la.det(A), 10.0))
        Ai = la.inv(A)
        I = la.matmul(A, Ai)
        self.assertTrue(close(I[0][0], 1.0) and abs(I[0][1]) < 1e-12)

    def test_hilbert_residual(self):
        # 조건수가 큰 힐베르트 5×5 라도 잔차는 작아야 한다.
        n = 5
        A = [[1.0 / (i + j + 1) for j in range(n)] for i in range(n)]
        xt = [1.0] * n
        b = la.matvec(A, xt)
        x = la.solve(A, b)
        r = la.vsub(la.matvec(A, x), b)
        self.assertLess(la.norm(r), 1e-12)


class TestCholesky(unittest.TestCase):
    def test_spd(self):
        A = [[4.0, 2.0], [2.0, 3.0]]
        L = la.cholesky(A)
        self.assertTrue(close(L[0][0], 2.0))
        self.assertTrue(close(la.matmul(L, la.transpose(L))[1][1], 3.0))
        x = la.chol_solve(L, [2.0, 1.0])
        self.assertLess(la.norm(la.vsub(la.matvec(A, x), [2.0, 1.0])), 1e-12)

    def test_not_pos_def(self):
        with self.assertRaises(la.NotPositiveDefinite):
            la.cholesky([[1.0, 2.0], [2.0, 1.0]])

    def test_is_pos_def(self):
        self.assertTrue(la.is_pos_def([[2.0, 0.0], [0.0, 3.0]]))
        self.assertFalse(la.is_pos_def([[0.0, 1.0], [1.0, 0.0]]))


class TestQR(unittest.TestCase):
    def test_qr_reconstruct(self):
        A = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        Q, R = la.qr(A)
        QR = la.matmul(Q, R)
        for i in range(3):
            for j in range(2):
                self.assertTrue(close(QR[i][j], A[i][j], 1e-12))
        # Q 의 열은 정규직교
        QtQ = la.matmul(la.transpose(Q), Q)
        self.assertTrue(close(QtQ[0][0], 1.0) and abs(QtQ[0][1]) < 1e-12)
        # R 은 상삼각
        self.assertLess(abs(R[1][0]), 1e-12)

    def test_least_squares(self):
        # y = 2x + 1 위의 점 3개 + 잡음 없음 → 정확히 복원
        A = [[1.0, 1.0], [1.0, 2.0], [1.0, 3.0]]
        b = [3.0, 5.0, 7.0]
        x = la.lstsq(A, b)
        self.assertTrue(close(x[0], 1.0, 1e-10) and close(x[1], 2.0, 1e-10))


class TestEigen(unittest.TestCase):
    def test_symmetric_2x2(self):
        A = [[2.0, 1.0], [1.0, 2.0]]
        vals, vecs = la.eigh(A)
        self.assertTrue(close(vals[0], 1.0, 1e-10))
        self.assertTrue(close(vals[1], 3.0, 1e-10))
        # A v = λ v
        for k in range(2):
            v = [vecs[i][k] for i in range(2)]
            self.assertLess(la.norm(la.vsub(la.matvec(A, v), la.vscale(vals[k], v))), 1e-9)

    def test_diagonal(self):
        vals, _ = la.eigh([[5.0, 0.0], [0.0, -2.0]])
        self.assertTrue(close(vals[0], -2.0) and close(vals[1], 5.0))

    def test_1x1(self):
        vals, vecs = la.eigh([[7.0]])
        self.assertTrue(close(vals[0], 7.0))
        self.assertTrue(close(abs(vecs[0][0]), 1.0))


class TestSVD(unittest.TestCase):
    def test_reconstruct(self):
        A = [[3.0, 0.0], [0.0, -2.0], [1.0, 1.0]]
        U, s, V = la.svd(A)
        self.assertTrue(all(s[i] >= s[i + 1] for i in range(len(s) - 1)))
        # U diag(s) V^T == A
        R = la.matmul(la.matmul(U, la.diag(s)), la.transpose(V))
        for i in range(3):
            for j in range(2):
                self.assertTrue(close(R[i][j], A[i][j], 1e-9))

    def test_cond(self):
        self.assertTrue(close(la.cond([[2.0, 0.0], [0.0, 1.0]]), 2.0, 1e-10))


if __name__ == '__main__':
    unittest.main()
