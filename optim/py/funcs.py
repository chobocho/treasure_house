# -*- coding: utf-8 -*-
"""시험함수 모음 — 교재 전체가 공유하는 벤치마크.

   알고리즘을 비교하려면 상대가 같아야 한다. 여기 있는 문제들은 전부
   해석적 f, ∇f, ∇²f 를 갖고 있고, tests/test_numdiff.py 가 매번 수치미분과
   대조해 그 식이 맞다는 것을 확인한다. 그래서 뒤에서 어떤 알고리즘이 실패하면
   그것은 알고리즘의 성질이지 도함수 오타가 아니다.

   각 문제는 왜 그것이 어려운지도 함께 적어 둔다 — 벤치마크는 성격을 알아야 쓸모가 있다.
"""
import math
import random

# math.fsum 대신 이것을 쓴다 — 실수에는 fsum(정확한 합)을, 자동미분의
# 이중수·그래프 마디에는 보통의 덧셈을 적용해 준다(py/autodiff.py 참고).
# 덕분에 같은 시험함수를 해석적 미분·수치미분·자동미분 셋 모두에 쓸 수 있다.
from py.autodiff import fsum


class Problem(object):
    """최적화 문제 하나. hess 가 None 이면 2차 정보를 제공하지 않는 문제다."""

    name = 'problem'
    x0 = None
    argmin = None          # 알려진 전역 최소점(있으면)
    fmin = None            # 그때의 함수값

    def f(self, x):
        raise NotImplementedError

    def grad(self, x):
        raise NotImplementedError

    hess = None

    @property
    def n(self):
        return len(self.x0)


class Quadratic(Problem):
    """f(x) = ½xᵀQx − cᵀx.  Q 가 대칭 양의 정부호면 유일한 최소점은 Qx = c 의 해.

       모든 매끄러운 함수는 최소점 근방에서 이 모양이다(테일러 2차 근사).
       그래서 알고리즘의 '점근적' 성질은 여기서 먼저 드러난다.
       조건수 κ(Q) 를 키우면 계곡이 길고 좁아져 경사하강이 지그재그를 친다.
    """

    def __init__(self, Q, c=None, name=None):
        self.Q = [[float(v) for v in row] for row in Q]
        self.c = [0.0] * len(Q) if c is None else [float(v) for v in c]
        self.x0 = [0.0] * len(Q)
        self.name = name or 'quadratic(%d)' % len(Q)

    def f(self, x):
        n = len(x)
        q = fsum(x[i] * self.Q[i][j] * x[j] for i in range(n) for j in range(n))
        return 0.5 * q - fsum(self.c[i] * x[i] for i in range(n))

    def grad(self, x):
        n = len(x)
        return [fsum(self.Q[i][j] * x[j] for j in range(n)) - self.c[i] for i in range(n)]

    def hess(self, x):
        return [row[:] for row in self.Q]

    @staticmethod
    def ill_conditioned(n, kappa):
        """조건수가 정확히 kappa 인 대각 이차형식 — 수렴률 실험용."""
        Q = [[0.0] * n for _ in range(n)]
        for i in range(n):
            # 고윳값을 1 과 kappa 사이에 로그 간격으로 배치
            t = 0.0 if n == 1 else i / float(n - 1)
            Q[i][i] = kappa ** t
        return Quadratic(Q, name='ill(κ=%g)' % kappa)


class Rosenbrock(Problem):
    """바나나 골짜기.  f = Σ [100(x_{i+1} − x_i²)² + (1 − x_i)²],  최소 f(1,…,1)=0.

       왜 어려운가: 골짜기 바닥이 포물선 x₂ = x₁² 을 따라 휘어 있다. 기울기는
       골짜기를 가로지르는 방향으로는 크고 따라가는 방향으로는 거의 0 이라,
       1차 방법은 바닥에서 종종걸음을 친다. 최소점에서 헤세의 조건수는 약 2508.
    """

    def __init__(self, n=2):
        self.nn = n
        # 관례적인 출발점 (−1.2, 1, −1.2, 1, …). 홀수 자리를 −1.2 로 번갈아 두는 것이
        # 표준이다. (−1.2, 1, 1, 1, …) 처럼 뒤를 전부 1 로 채우면 n ≥ 4 에서
        # f ≈ 3.99 의 국소 최소로 빨려 들어가 알고리즘 비교가 왜곡된다.
        self.x0 = [(-1.2 if i % 2 == 0 else 1.0) for i in range(n)] if n >= 2 else [-1.2]
        self.argmin = [1.0] * n
        self.fmin = 0.0
        self.name = 'rosenbrock(%d)' % n

    def f(self, x):
        return fsum(100.0 * (x[i + 1] - x[i] ** 2) ** 2 + (1.0 - x[i]) ** 2
                         for i in range(len(x) - 1))

    def grad(self, x):
        n = len(x)
        g = [0.0] * n
        for i in range(n - 1):
            t = x[i + 1] - x[i] ** 2
            g[i] += -400.0 * x[i] * t - 2.0 * (1.0 - x[i])
            g[i + 1] += 200.0 * t
        return g

    def hess(self, x):
        n = len(x)
        H = [[0.0] * n for _ in range(n)]
        for i in range(n - 1):
            t = x[i + 1] - x[i] ** 2
            H[i][i] += -400.0 * t + 800.0 * x[i] ** 2 + 2.0
            H[i][i + 1] += -400.0 * x[i]
            H[i + 1][i] += -400.0 * x[i]
            H[i + 1][i + 1] += 200.0
        return H


class Himmelblau(Problem):
    """f = (x²+y−11)² + (x+y²−7)².  전역 최소가 네 개(값은 모두 0).

       "최소점이 하나가 아니다"를 보여 주는 표본. 시작점에 따라 다른 답으로 간다 —
       비볼록 문제에서 '수렴했다'가 '옳은 답'을 뜻하지 않는다는 것을 눈으로 확인한다.
    """

    name = 'himmelblau'
    x0 = [0.0, 0.0]
    fmin = 0.0
    argmin = [3.0, 2.0]
    ALL_MIN = [(3.0, 2.0), (-2.805118, 3.131312),
               (-3.779310, -3.283186), (3.584428, -1.848126)]

    def f(self, x):
        a = x[0] ** 2 + x[1] - 11.0
        b = x[0] + x[1] ** 2 - 7.0
        return a * a + b * b

    def grad(self, x):
        a = x[0] ** 2 + x[1] - 11.0
        b = x[0] + x[1] ** 2 - 7.0
        return [4.0 * x[0] * a + 2.0 * b, 2.0 * a + 4.0 * x[1] * b]

    def hess(self, x):
        a = x[0] ** 2 + x[1] - 11.0
        b = x[0] + x[1] ** 2 - 7.0
        return [[12.0 * x[0] ** 2 + 4.0 * x[1] - 42.0, 4.0 * x[0] + 4.0 * x[1]],
                [4.0 * x[0] + 4.0 * x[1], 4.0 * x[0] + 12.0 * x[1] ** 2 - 26.0]]


class Beale(Problem):
    """f = (1.5−x+xy)² + (2.25−x+xy²)² + (2.625−x+xy³)².  최소 f(3, 0.5)=0.

       평평한 고원이 넓어서 기울기가 오래 거의 0 이다. 스텝 크기를 고정한
       경사하강이 '수렴한 것처럼 보이지만 멈춰 있는' 상태를 만든다.
    """

    name = 'beale'
    x0 = [1.0, 1.0]
    argmin = [3.0, 0.5]
    fmin = 0.0
    _K = (1.5, 2.25, 2.625)

    def _r(self, x):
        return [self._K[i] - x[0] + x[0] * x[1] ** (i + 1) for i in range(3)]

    def f(self, x):
        return fsum(r * r for r in self._r(x))

    def grad(self, x):
        r = self._r(x)
        gx = fsum(2.0 * r[i] * (-1.0 + x[1] ** (i + 1)) for i in range(3))
        gy = fsum(2.0 * r[i] * (x[0] * (i + 1) * x[1] ** i) for i in range(3))
        return [gx, gy]

    def hess(self, x):
        r = self._r(x)
        hxx = hxy = hyy = 0.0
        for i in range(3):
            p = i + 1
            drx = -1.0 + x[1] ** p
            dry = x[0] * p * x[1] ** (p - 1)
            d2xy = p * x[1] ** (p - 1)
            d2yy = x[0] * p * (p - 1) * (x[1] ** (p - 2) if p >= 2 else 0.0)
            hxx += 2.0 * drx * drx
            hxy += 2.0 * (drx * dry + r[i] * d2xy)
            hyy += 2.0 * (dry * dry + r[i] * d2yy)
        return [[hxx, hxy], [hxy, hyy]]


class LogisticRegression(Problem):
    """ℓ2 정칙화 로지스틱 회귀 —  f(w) = (1/N)Σ log(1+e^{−yᵢ wᵀxᵢ}) + (λ/2)‖w‖².

       이 교재에서 '진짜 문제'의 역할을 한다. 볼록이고 매끄럽고 미분이 닫힌 꼴이며,
       λ>0 이면 강볼록이라 수렴률 정리들을 그대로 적용해 확인할 수 있다.
       ∇²f = (1/N) Xᵀ S X + λI,  S = diag(σ(1−σ)) 이므로 항상 양의 반정부호다.
    """

    name = 'logistic'

    def __init__(self, X, y, lam=1e-2):
        self.X = X                      # N×d
        self.y = [1.0 if v > 0 else -1.0 for v in y]
        self.lam = float(lam)
        self.x0 = [0.0] * len(X[0])

    @classmethod
    def toy(cls, seed=0, n=60, d=3, lam=1e-2):
        """선형 분리에 가까운 인공 자료. 시드를 고정해 매 실행이 같도록 한다."""
        rng = random.Random(seed)
        w_true = [1.0, -2.0, 0.5][:d] + [0.3] * max(0, d - 3)
        X, y = [], []
        for _ in range(n):
            xi = [rng.gauss(0.0, 1.0) for _ in range(d)]
            z = fsum(a * b for a, b in zip(w_true, xi))
            p = 1.0 / (1.0 + math.exp(-z))
            y.append(1.0 if rng.random() < p else -1.0)
            X.append(xi)
        return cls(X, y, lam)

    @staticmethod
    def _logexp(z):
        """log(1+e^{−z}) 를 넘침 없이. z 가 크게 음수면 −z 가 지배한다."""
        if z >= 0.0:
            return math.log1p(math.exp(-z))
        return -z + math.log1p(math.exp(z))

    def f(self, w):
        n = len(self.X)
        s = fsum(self._logexp(self.y[i] * fsum(a * b for a, b in zip(w, self.X[i])))
                      for i in range(n))
        return s / n + 0.5 * self.lam * fsum(v * v for v in w)

    def grad(self, w):
        n, d = len(self.X), len(w)
        g = [self.lam * v for v in w]
        for i in range(n):
            z = self.y[i] * fsum(a * b for a, b in zip(w, self.X[i]))
            # −σ(−z) = −1/(1+e^{z}) — 넘침을 피해 부호로 갈라 쓴다
            s = -1.0 / (1.0 + math.exp(z)) if z > -700 else -1.0
            c = s * self.y[i] / n
            xi = self.X[i]
            for j in range(d):
                g[j] += c * xi[j]
        return g

    def hess(self, w):
        n, d = len(self.X), len(w)
        H = [[self.lam if i == j else 0.0 for j in range(d)] for i in range(d)]
        for i in range(n):
            z = self.y[i] * fsum(a * b for a, b in zip(w, self.X[i]))
            sig = 1.0 / (1.0 + math.exp(-z)) if z > -700 else 0.0
            c = sig * (1.0 - sig) / n
            xi = self.X[i]
            for a in range(d):
                if xi[a] == 0.0:
                    continue
                for b in range(d):
                    H[a][b] += c * xi[a] * xi[b]
        return H


ALL = {
    'rosenbrock2': lambda: Rosenbrock(2),
    'rosenbrock5': lambda: Rosenbrock(5),
    'himmelblau': Himmelblau,
    'beale': Beale,
    'logistic': lambda: LogisticRegression.toy(seed=7, n=200, d=4),
    'ill100': lambda: Quadratic.ill_conditioned(10, 100.0),
}
