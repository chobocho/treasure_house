# -*- coding: utf-8 -*-
"""순수 파이썬 선형대수 — 최적화 알고리즘이 딛고 설 바닥.

   왜 numpy 를 쓰지 않는가:
     · 이 교재의 목표는 "행렬 연산을 호출할 줄 안다"가 아니라 "왜 그렇게 푸는가"다.
       LU 의 피벗팅, 촐레스키가 실패하는 순간, QR 이 정규방정식보다 안정한 이유는
       구현을 열어 봐야 보인다.
     · 표준 라이브러리만 쓰면 어떤 파이썬에서도 그대로 돌아간다.

   표현:  벡터 = float 의 list,  행렬 = 행(list)들의 list.
   행렬은 A[i][j] — i 행, j 열. 모든 함수는 입력을 바꾸지 않는다(순수 함수).
"""
import math

__all__ = [
    'SingularMatrix', 'NotPositiveDefinite',
    'vadd', 'vsub', 'vscale', 'axpy', 'dot', 'norm', 'norm1', 'norminf', 'vzeros',
    'zeros', 'identity', 'diag', 'transpose', 'matvec', 'matmul', 'outer',
    'madd', 'msub', 'mscale', 'frobenius', 'copy_mat',
    'lu_factor', 'lu_solve', 'solve', 'det', 'inv',
    'cholesky', 'chol_solve', 'is_pos_def', 'is_symmetric',
    'qr', 'lstsq', 'eigh', 'svd', 'cond',
]


class SingularMatrix(Exception):
    """정칙이 아니어서 유일해가 없다 — 피벗이 사실상 0."""


class NotPositiveDefinite(Exception):
    """양의 정부호가 아니다 — 촐레스키 분해 중 음수의 제곱근을 만났다."""


# ---------------------------------------------------------------- 벡터

def _same(x, y):
    if len(x) != len(y):
        raise ValueError('길이가 다르다: %d vs %d' % (len(x), len(y)))


def vadd(x, y):
    _same(x, y)
    return [a + b for a, b in zip(x, y)]


def vsub(x, y):
    _same(x, y)
    return [a - b for a, b in zip(x, y)]


def vscale(c, x):
    return [c * a for a in x]


def axpy(a, x, y):
    """y + a·x — 최적화 루프에서 가장 자주 쓰는 한 줄(스텝 갱신)."""
    _same(x, y)
    return [a * xi + yi for xi, yi in zip(x, y)]


def dot(x, y):
    _same(x, y)
    return math.fsum(a * b for a, b in zip(x, y))   # fsum: 누적 반올림 오차를 없앤다


def norm(x):
    """유클리드 노름. 제곱을 먼저 하면 1e200 에서 넘치므로 최대 성분으로 스케일한다.

       O(n) 시간, O(1) 추가 공간.
    """
    if not x:
        return 0.0
    s = max(abs(a) for a in x)
    if s == 0.0:
        return 0.0
    return s * math.sqrt(math.fsum((a / s) ** 2 for a in x))


def norm1(x):
    return math.fsum(abs(a) for a in x)


def norminf(x):
    return max((abs(a) for a in x), default=0.0)


def vzeros(n):
    return [0.0] * n


# ---------------------------------------------------------------- 행렬

def zeros(m, n):
    return [[0.0] * n for _ in range(m)]


def identity(n):
    I = zeros(n, n)
    for i in range(n):
        I[i][i] = 1.0
    return I


def diag(v):
    """벡터를 대각행렬로."""
    n = len(v)
    D = zeros(n, n)
    for i in range(n):
        D[i][i] = float(v[i])
    return D


def copy_mat(A):
    return [row[:] for row in A]


def transpose(A):
    return [list(col) for col in zip(*A)]


def matvec(A, x):
    if A and len(A[0]) != len(x):
        raise ValueError('모양이 안 맞는다: %d열 × %d' % (len(A[0]), len(x)))
    return [math.fsum(a * b for a, b in zip(row, x)) for row in A]


def matmul(A, B):
    """O(m·n·p) 시간. 안쪽 루프에서 B 의 열을 매번 훑지 않도록 B 를 전치해 둔다."""
    if A and B and len(A[0]) != len(B):
        raise ValueError('모양이 안 맞는다: %d열 × %d행' % (len(A[0]), len(B)))
    Bt = transpose(B)
    return [[math.fsum(a * b for a, b in zip(row, col)) for col in Bt] for row in A]


def outer(x, y):
    return [[xi * yj for yj in y] for xi in x]


def madd(A, B):
    return [[a + b for a, b in zip(ra, rb)] for ra, rb in zip(A, B)]


def msub(A, B):
    return [[a - b for a, b in zip(ra, rb)] for ra, rb in zip(A, B)]


def mscale(c, A):
    return [[c * a for a in row] for row in A]


def frobenius(A):
    return math.sqrt(math.fsum(a * a for row in A for a in row))


def is_symmetric(A, tol=1e-12):
    n = len(A)
    return all(abs(A[i][j] - A[j][i]) <= tol * max(1.0, abs(A[i][j]))
               for i in range(n) for j in range(i + 1, n))


# ---------------------------------------------------------------- LU 분해

def lu_factor(A):
    """부분 피벗팅 LU 분해.  PA = LU 를 한 배열에 겹쳐 담는다.

       왜 피벗팅이 필요한가: [[0,1],[1,0]] 은 정칙인데도 (1,1) 성분이 0 이라
       그대로 소거하면 0 으로 나눈다. 크기가 가장 큰 행을 위로 올리면 그 사고가
       사라지고, 증배 계수 |l| ≤ 1 이 보장돼 오차 증폭도 억제된다.

       O(n³/3) 시간, O(n²) 공간.  반환: (LU, piv, sign)
    """
    n = len(A)
    LU = copy_mat([[float(v) for v in row] for row in A])
    piv = list(range(n))
    sign = 1.0
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(LU[i][k]))
        if abs(LU[p][k]) < 1e-300:
            raise SingularMatrix('%d번째 피벗이 0' % k)
        if p != k:
            LU[k], LU[p] = LU[p], LU[k]
            piv[k], piv[p] = piv[p], piv[k]
            sign = -sign
        pivot = LU[k][k]
        for i in range(k + 1, n):
            f = LU[i][k] / pivot
            LU[i][k] = f                      # L 의 증배 계수를 그 자리에 저장
            if f != 0.0:
                row_i, row_k = LU[i], LU[k]
                for j in range(k + 1, n):
                    row_i[j] -= f * row_k[j]
    return LU, piv, sign


def lu_solve(fac, b):
    """LU 분해 결과로 Ax=b 를 푼다. 전진대입 후 후진대입, O(n²)."""
    LU, piv, _ = fac
    n = len(LU)
    if len(b) != n:
        raise ValueError('우변 길이가 %d 이어야 한다' % n)
    y = [float(b[piv[i]]) for i in range(n)]
    for i in range(1, n):                     # 전진대입 (L 의 대각은 1)
        y[i] -= math.fsum(LU[i][j] * y[j] for j in range(i))
    x = y
    for i in range(n - 1, -1, -1):            # 후진대입
        x[i] = (x[i] - math.fsum(LU[i][j] * x[j] for j in range(i + 1, n))) / LU[i][i]
    return x


def solve(A, b):
    """정사각 연립방정식 한 번 풀기. 같은 A 를 여러 번 쓸 거면 lu_factor 를 재사용하라."""
    return lu_solve(lu_factor(A), b)


def det(A):
    """행렬식 = 피벗들의 곱 × 행 교환 부호. 여인수 전개(O(n!))를 쓰면 안 되는 이유다."""
    try:
        LU, _, sign = lu_factor(A)
    except SingularMatrix:
        return 0.0
    d = sign
    for i in range(len(LU)):
        d *= LU[i][i]
    return d


def inv(A):
    """역행렬. 실무에서는 거의 필요 없다 — Ax=b 는 solve 로 푸는 게 더 빠르고 안정하다."""
    n = len(A)
    fac = lu_factor(A)
    cols = [lu_solve(fac, [1.0 if i == k else 0.0 for i in range(n)]) for k in range(n)]
    return transpose(cols)


# ---------------------------------------------------------------- 촐레스키

def cholesky(A):
    """A = L Lᵀ (L 은 하삼각, 대각 > 0).  O(n³/6) — LU 의 절반.

       최적화에서 이것이 중요한 이유: 뉴턴 방향을 구할 때 헤세 행렬에 촐레스키를
       시도해 보면 "양의 정부호인가"라는 2차 최적성 조건을 공짜로 검사하게 된다.
       실패하는 지점이 곧 하강 방향이 보장되지 않는 지점이다.
    """
    n = len(A)
    L = zeros(n, n)
    for i in range(n):
        for j in range(i + 1):
            s = math.fsum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                d = A[i][i] - s
                if d <= 0.0:
                    raise NotPositiveDefinite('대각 %d 에서 %r ≤ 0' % (i, d))
                L[i][j] = math.sqrt(d)
            else:
                L[i][j] = (A[i][j] - s) / L[j][j]
    return L


def chol_solve(L, b):
    """L Lᵀ x = b — 전진대입 후 후진대입."""
    n = len(L)
    y = [0.0] * n
    for i in range(n):
        y[i] = (b[i] - math.fsum(L[i][k] * y[k] for k in range(i))) / L[i][i]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - math.fsum(L[k][i] * x[k] for k in range(i + 1, n))) / L[i][i]
    return x


def is_pos_def(A):
    if not is_symmetric(A):
        return False
    try:
        cholesky(A)
        return True
    except NotPositiveDefinite:
        return False


# ---------------------------------------------------------------- QR (하우스홀더)

def qr(A):
    """하우스홀더 반사로 A = QR.  Q 는 m×m 직교, R 은 m×n 상삼각.  O(2mn² − 2n³/3).

       그람–슈미트 대신 반사를 쓰는 이유: 그람–슈미트는 열이 거의 평행할 때
       직교성을 잃는다(수치적으로 무너진다). 반사는 매 단계가 직교변환이라
       오차가 증폭되지 않는다.
    """
    m, n = len(A), len(A[0])
    R = [[float(v) for v in row] for row in A]
    Q = identity(m)
    for k in range(min(n, m - 1)):
        x = [R[i][k] for i in range(k, m)]
        nx = norm(x)
        if nx < 1e-300:
            continue
        # 부호를 x[0] 와 같게 잡아야 v 가 0 에 가까워지는 상쇄를 피한다.
        alpha = -nx if x[0] >= 0 else nx
        v = x[:]
        v[0] -= alpha
        nv = norm(v)
        if nv < 1e-300:
            continue
        v = [vi / nv for vi in v]
        # R ← (I − 2vvᵀ) R,  Q ← Q (I − 2vvᵀ)   — 행렬곱이 아니라 랭크-1 갱신
        for j in range(k, n):
            s = 2.0 * math.fsum(v[i - k] * R[i][j] for i in range(k, m))
            for i in range(k, m):
                R[i][j] -= s * v[i - k]
        for i in range(m):
            s = 2.0 * math.fsum(Q[i][j] * v[j - k] for j in range(k, m))
            for j in range(k, m):
                Q[i][j] -= s * v[j - k]
    for i in range(m):                        # 상삼각 아래를 정확히 0 으로
        for j in range(min(i, n)):
            R[i][j] = 0.0
    return Q, R


def lstsq(A, b):
    """최소제곱 min‖Ax−b‖₂ 를 QR 로 푼다.

       정규방정식 AᵀA x = Aᵀb 은 조건수를 제곱해 버린다(κ(AᵀA)=κ(A)²).
       QR 은 κ(A) 만큼만 잃는다 — 4부에서 수치실험으로 확인한다.
    """
    m, n = len(A), len(A[0])
    Q, R = qr(A)
    qb = matvec(transpose(Q), b)
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        if abs(R[i][i]) < 1e-300:
            raise SingularMatrix('열이 일차종속이다(랭크 부족)')
        x[i] = (qb[i] - math.fsum(R[i][j] * x[j] for j in range(i + 1, n))) / R[i][i]
    return x


# ---------------------------------------------------------------- 고윳값 (야코비)

def eigh(A, tol=1e-13, sweeps=100):
    """대칭행렬의 고윳값·고유벡터 — 순환 야코비 회전.

       비대각 성분 하나를 회전으로 0 으로 만드는 일을 반복한다. 그때마다
       비대각 제곱합이 반드시 줄어들기 때문에 수렴이 보장된다(2부에서 증명).
       O(n³) 정도, 대칭행렬에 대해 매우 정확하다.

       반환: (오름차순 고윳값 리스트, 고유벡터 행렬 V) — V 의 k번째 '열'이 k번째 고유벡터.
    """
    n = len(A)
    D = [[float(v) for v in row] for row in A]
    V = identity(n)
    for _ in range(sweeps):
        off = math.sqrt(math.fsum(D[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off <= tol * max(1.0, frobenius(D)):
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(D[p][q]) < 1e-300:
                    continue
                theta = (D[q][q] - D[p][p]) / (2.0 * D[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    dkp, dkq = D[k][p], D[k][q]
                    D[k][p] = c * dkp - s * dkq
                    D[k][q] = s * dkp + c * dkq
                for k in range(n):
                    dpk, dqk = D[p][k], D[q][k]
                    D[p][k] = c * dpk - s * dqk
                    D[q][k] = s * dpk + c * dqk
                for k in range(n):
                    vkp, vkq = V[k][p], V[k][q]
                    V[k][p] = c * vkp - s * vkq
                    V[k][q] = s * vkp + c * vkq
    vals = [D[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda i: vals[i])
    return [vals[i] for i in order], [[V[r][i] for i in order] for r in range(n)]


# ---------------------------------------------------------------- SVD (한쪽 야코비)

def svd(A, tol=1e-14, sweeps=60):
    """A = U diag(s) Vᵀ,  s 는 내림차순.  한쪽(one-sided) 야코비.

       A 의 열끼리 직교가 될 때까지 2×2 회전을 돌린다. 끝나면 열의 길이가
       특잇값, 정규화한 열이 U 의 열, 누적한 회전이 V 다.
       AᵀA 를 만들어 고윳값을 구하는 방법보다 정확하다 — 제곱하면서 잃는
       유효숫자가 없기 때문이다.
    """
    m, n = len(A), len(A[0])
    if m < n:                                  # 가로로 긴 행렬은 전치해서 풀고 되돌린다
        U, s, V = svd(transpose(A), tol, sweeps)
        return V, s, U
    B = transpose([[float(v) for v in row] for row in A])   # B[j] = A 의 j번째 열
    V = identity(n)
    for _ in range(sweeps):
        done = True
        for p in range(n - 1):
            for q in range(p + 1, n):
                app = math.fsum(v * v for v in B[p])
                aqq = math.fsum(v * v for v in B[q])
                apq = math.fsum(a * b for a, b in zip(B[p], B[q]))
                if abs(apq) <= tol * math.sqrt(app * aqq) or apq == 0.0:
                    continue
                done = False
                theta = (aqq - app) / (2.0 * apq)
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s_ = t * c
                for i in range(m):
                    bp, bq = B[p][i], B[q][i]
                    B[p][i] = c * bp - s_ * bq
                    B[q][i] = s_ * bp + c * bq
                for i in range(n):
                    vp, vq = V[i][p], V[i][q]
                    V[i][p] = c * vp - s_ * vq
                    V[i][q] = s_ * vp + c * vq
        if done:
            break
    sing = [norm(col) for col in B]
    order = sorted(range(n), key=lambda j: -sing[j])
    s = [sing[j] for j in order]
    U = zeros(m, n)
    for k, j in enumerate(order):
        if s[k] > 1e-300:
            for i in range(m):
                U[i][k] = B[j][i] / s[k]
    Vo = [[V[i][j] for j in order] for i in range(n)]
    return U, s, Vo


def cond(A):
    """2-노름 조건수 σ_max/σ_min. 이 수가 10^k 이면 유효숫자 k 자리를 잃는다."""
    s = svd(A)[1]
    if not s or s[-1] <= 1e-300:
        return float('inf')
    return s[0] / s[-1]
