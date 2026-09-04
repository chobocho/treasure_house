# -*- coding: utf-8 -*-
"""확률적·대규모 최적화 — 기울기를 흘끗 보고도 최적화할 수 있는가.

   자료가 N 개면 전체 기울기 한 번에 N 번의 계산이 든다. N 이 10^7 이면
   한 걸음이 이미 비싸다. 그런데 목적함수가 합의 꼴이면

       f(x) = (1/N) Σ fᵢ(x)   ⟹   E[∇fᵢ(x)] = ∇f(x)

   즉 표본 하나의 기울기가 <전체 기울기의 불편추정량>이다. 방향은 맞고 잡음만
   섞여 있으니, 잡음을 견디는 방식으로 걸으면 된다. 그것이 SGD 다.

   대가는 명확하다. 잡음이 있는 한 <고정 보폭으로는 최적해에 도달하지 못하고>
   그 주변의 공 안을 맴돈다. 보폭을 줄이거나(1/k), 분산을 줄이거나(SVRG),
   미니배치로 평균을 내야 한다. 이 파일은 그 셋을 모두 구현하고 실측한다.
"""
import math
import random

from py import convex as cx
from py import linalg as la
from py import unconstrained as uc


class Result(object):
    def __init__(self, x, fx=None, nit=0, history=None, msg=''):
        self.x = x
        self.fx = fx
        self.nit = nit
        self.history = history or []
        self.msg = msg

    def __repr__(self):
        return '<Stoch nit=%d f=%s>' % (self.nit, self.fx)


# ---------------------------------------------------------------- 유한합 문제

class LeastSquaresBatch(object):
    """f(x) = (1/2N) Σ (aᵢᵀx − bᵢ)²  — 표본 단위로 기울기를 뽑을 수 있는 최소제곱.

       확률적 방법을 시험하려면 '표본 하나'라는 개념이 필요하다. 이 클래스는
       전체 기울기(grad)와 부분 기울기(grad_sample)를 모두 제공해, 둘의 관계를
       테스트가 직접 확인할 수 있게 한다.
    """

    def __init__(self, X, y, lam=0.0):
        self.X = X
        self.y = y
        self.n = len(X)
        self.d = len(X[0])
        self.lam = lam

    def f(self, x):
        s = math.fsum((la.dot(self.X[i], x) - self.y[i]) ** 2 for i in range(self.n))
        return 0.5 * s / self.n + 0.5 * self.lam * la.dot(x, x)

    def grad(self, x):
        g = [self.lam * v for v in x]
        for i in range(self.n):
            r = (la.dot(self.X[i], x) - self.y[i]) / self.n
            g = la.axpy(r, self.X[i], g)
        return g

    def grad_sample(self, x, idx):
        """지정한 표본들만으로 만든 기울기 추정. idx 가 전체이면 grad 와 같다."""
        g = [self.lam * v for v in x]
        for i in idx:
            r = (la.dot(self.X[i], x) - self.y[i]) / len(idx)
            g = la.axpy(r, self.X[i], g)
        return g

    def exact_solution(self):
        """정규방정식으로 구한 정확한 최소점 — 실험의 기준점."""
        d = self.d
        A = la.zeros(d, d)
        b = [0.0] * d
        for i in range(self.n):
            xi = self.X[i]
            for a in range(d):
                b[a] += xi[a] * self.y[i] / self.n
                for c in range(d):
                    A[a][c] += xi[a] * xi[c] / self.n
        for a in range(d):
            A[a][a] += self.lam
        return la.solve(A, b)


# ---------------------------------------------------------------- SGD 계열

def sgd(problem, x0, step, epochs=100, batch=1, seed=0, keep_history=False):
    """확률적 경사하강. step 은 반복 횟수를 받아 보폭을 돌려주는 함수다.

       한 에폭 = 자료를 한 번 훑는 것. 표본 순서를 매 에폭 섞는다(shuffling) —
       같은 순서를 반복하면 편향이 생길 수 있기 때문이다.
    """
    rng = random.Random(seed)
    x = [float(v) for v in x0]
    n = problem.n
    hist = []
    k = 0
    for ep in range(epochs):
        order = list(range(n))
        rng.shuffle(order)
        for s in range(0, n, batch):
            idx = order[s:s + batch]
            g = problem.grad_sample(x, idx)
            x = la.axpy(-step(k), g, x)
            k += 1
        if keep_history:
            hist.append({'epoch': ep, 'f': problem.f(x), 'step': step(k)})
    return Result(x, problem.f(x), k, hist)


def svrg(problem, x0, step, epochs=20, seed=0, keep_history=False):
    """SVRG — 분산 감소.

       주기마다 전체 기울기 ∇f(x̃) 를 한 번 계산해 두고, 안쪽 반복에서

           g = ∇fᵢ(x) − ∇fᵢ(x̃) + ∇f(x̃)

       를 쓴다. 기댓값은 여전히 ∇f(x) 이지만(불편), x 가 x̃ 에 가까울수록 앞의
       두 항이 상쇄되어 <분산이 0 으로 줄어든다>. 그래서 고정 보폭으로도
       선형 수렴한다 — SGD 가 못 하는 일이다.
    """
    rng = random.Random(seed)
    x = [float(v) for v in x0]
    n = problem.n
    hist = []
    for ep in range(epochs):
        snapshot = list(x)
        full = problem.grad(snapshot)
        for _ in range(n):
            i = rng.randrange(n)
            gi = problem.grad_sample(x, [i])
            gs = problem.grad_sample(snapshot, [i])
            g = la.vadd(la.vsub(gi, gs), full)
            x = la.axpy(-step, g, x)
        if keep_history:
            hist.append({'epoch': ep, 'f': problem.f(x)})
    return Result(x, problem.f(x), epochs * n, hist)


# ---------------------------------------------------------------- 모멘텀·가속

def momentum(problem, x0, step, beta=0.9, iters=1000, tol=1e-10, keep_history=False):
    """무거운 공(heavy ball):  v ← βv − α∇f,  x ← x + v.

       왜 빠른가: 진동하는 방향은 부호가 매번 바뀌어 v 에서 상쇄되고, 일관된
       방향은 누적된다. 이차함수에서 최적 β 를 쓰면 수렴 인자가 (κ−1)/(κ+1) 에서
       (√κ−1)/(√κ+1) 로 개선된다 — 3부 정리 13.3 의 켤레기울기와 같은 차수다.
    """
    x = [float(v) for v in x0]
    v = [0.0] * len(x)
    hist = []
    for k in range(iters):
        g = problem.grad(x)
        if la.norm(g) <= tol:
            break
        v = la.axpy(-step, g, la.vscale(beta, v))
        x = la.vadd(x, v)
        if keep_history:
            hist.append({'k': k, 'f': problem.f(x), 'gnorm': la.norm(g)})
    return Result(x, problem.f(x), k + 1, hist)


def accelerated(problem, x0, L, iters=1000, tol=1e-12, keep_history=False):
    """네스테로프 가속 경사법.

           y_k = x_k + ((k−1)/(k+2))(x_k − x_{k−1})
           x_{k+1} = y_k − (1/L)∇f(y_k)

       기울기를 <현재 점이 아니라 앞질러 간 점>에서 잰다. 볼록·L-평활 문제에서
       f(x_k) − f⋆ = O(1/k²) 로, 경사하강의 O(1/k) 보다 한 차수 빠르다.
       이 속도는 1차 방법의 <이론적 하한>이기도 하다(Nesterov).
    """
    x = [float(v) for v in x0]
    x_prev = list(x)
    hist = []
    for k in range(iters):
        beta = (k - 1.0) / (k + 2.0) if k > 0 else 0.0
        y = la.axpy(beta, la.vsub(x, x_prev), x)
        g = problem.grad(y)
        x_prev = x
        x = la.axpy(-1.0 / L, g, y)
        if keep_history:
            hist.append({'k': k, 'f': problem.f(x), 'gnorm': la.norm(g)})
        if la.norm(g) <= tol:
            break
    return Result(x, problem.f(x), k + 1, hist)


def count_iters(problem, x0, method='gd', tol=1e-8, maxiter=20000, step=None,
                beta=0.9):
    """같은 문제에서 방법별 반복 수를 센다 — 비교 실험용."""
    if method == 'gd':
        H = problem.hess(x0)
        vals, _ = la.eigh(H)
        a = step or 2.0 / (vals[0] + vals[-1])
        x = [float(v) for v in x0]
        for k in range(maxiter):
            g = problem.grad(x)
            if la.norm(g) <= tol:
                return k
            x = la.axpy(-a, g, x)
        return maxiter
    if method == 'momentum':
        H = problem.hess(x0)
        vals, _ = la.eigh(H)
        L, mu = vals[-1], vals[0]
        # 이차함수에서의 최적 모멘텀 계수 (Polyak)
        b = ((math.sqrt(L) - math.sqrt(mu)) / (math.sqrt(L) + math.sqrt(mu))) ** 2
        a = (2.0 / (math.sqrt(L) + math.sqrt(mu))) ** 2
        x = [float(v) for v in x0]
        v = [0.0] * len(x)
        for k in range(maxiter):
            g = problem.grad(x)
            if la.norm(g) <= tol:
                return k
            v = la.axpy(-a, g, la.vscale(b, v))
            x = la.vadd(x, v)
        return maxiter
    raise ValueError('모르는 방법: %s' % method)


# ---------------------------------------------------------------- 적응 보폭

def adagrad_full(problem, x0, step=1.0, iters=1000, eps=1e-8, keep_history=False):
    """AdaGrad (전체 기울기 버전) — 좌표마다 지금까지의 기울기 제곱합으로 나눈다.

       자주 크게 움직인 좌표는 보폭이 줄고, 드물게 움직인 좌표는 큰 보폭을 유지한다.
       스케일이 제각각인 문제(희소 특징이 대표적)에서 강하다.
       단점: 분모가 단조 증가하므로 보폭이 <영원히 줄어든다> — RMSProp 이 이것을
       지수이동평균으로 바꿔 고쳤다.
    """
    x = [float(v) for v in x0]
    acc = [0.0] * len(x)
    hist = []
    for k in range(iters):
        g = problem.grad(x)
        for i in range(len(x)):
            acc[i] += g[i] * g[i]
            x[i] -= step * g[i] / (math.sqrt(acc[i]) + eps)
        if keep_history:
            hist.append({'k': k, 'f': problem.f(x), 'gnorm': la.norm(g)})
    return Result(x, problem.f(x), iters, hist)


def adam(problem, x0, step=0.01, epochs=100, batch=1, beta1=0.9, beta2=0.999,
         eps=1e-8, seed=0, bias_correct=True, keep_history=False):
    """Adam — 모멘텀(1차 적률)과 RMSProp(2차 적률)의 결합.

           m ← β₁m + (1−β₁)g,      v ← β₂v + (1−β₂)g²
           m̂ = m/(1−β₁ᵏ),          v̂ = v/(1−β₂ᵏ)     ← 편향 보정
           x ← x − α m̂ / (√v̂ + ε)

       편향 보정이 필요한 이유: m, v 를 0 에서 시작하므로 초기 몇 걸음의 추정치가
       0 쪽으로 크게 치우친다. (1−βᵏ) 로 나누면 그 치우침이 정확히 상쇄된다.
    """
    rng = random.Random(seed)
    x = [float(v) for v in x0]
    m = [0.0] * len(x)
    v = [0.0] * len(x)
    n = problem.n
    hist = []
    k = 0
    for ep in range(epochs):
        order = list(range(n))
        rng.shuffle(order)
        for s in range(0, n, batch):
            k += 1
            g = problem.grad_sample(x, order[s:s + batch])
            for i in range(len(x)):
                m[i] = beta1 * m[i] + (1 - beta1) * g[i]
                v[i] = beta2 * v[i] + (1 - beta2) * g[i] * g[i]
                mh = m[i] / (1 - beta1 ** k) if bias_correct else m[i]
                vh = v[i] / (1 - beta2 ** k) if bias_correct else v[i]
                x[i] -= step * mh / (math.sqrt(vh) + eps)
        if keep_history:
            hist.append({'epoch': ep, 'f': problem.f(x)})
    return Result(x, problem.f(x), k, hist)


# ---------------------------------------------------------------- 근접경사

def _lasso_obj(X, y, x, lam):
    r = [la.dot(X[i], x) - y[i] for i in range(len(X))]
    return 0.5 * math.fsum(v * v for v in r) + lam * math.fsum(abs(v) for v in x)


def _lasso_L(X):
    """∇(½‖Xx−y‖²) 의 립시츠 상수 = λ_max(XᵀX)."""
    XtX = la.matmul(la.transpose(X), X)
    vals, _ = la.eigh(XtX)
    return vals[-1]


def ista(X, y, lam, iters=1000, keep_history=False):
    """ISTA — 근접경사법으로 라쏘를 푼다.

           x ← prox_{(λ/L)‖·‖₁}( x − (1/L)∇g(x) ),   g(x) = ½‖Xx−y‖²

       매끄러운 부분에는 경사 한 걸음, 비평활 부분에는 prox 한 번. 2부 정의 7.12
       에서 본 근접연산자가 여기서 연성 문턱이 된다 — 그래서 계수가 정확히 0 이 된다.
       수렴률은 O(1/k) 다.
    """
    L = _lasso_L(X)
    x = [0.0] * len(X[0])
    hist = []
    for k in range(iters):
        r = [la.dot(X[i], x) - y[i] for i in range(len(X))]
        g = la.matvec(la.transpose(X), r)
        x = cx.soft_threshold(la.axpy(-1.0 / L, g, x), lam / L)
        if keep_history:
            hist.append(_lasso_obj(X, y, x, lam))
    return Result(x, _lasso_obj(X, y, x, lam), iters, hist)


def fista(X, y, lam, iters=1000, keep_history=False):
    """FISTA — ISTA 에 네스테로프 가속을 얹은 것. 수렴률 O(1/k²).

       구조는 accelerated() 와 같다: 앞질러 간 점 y 에서 기울기를 재고 prox 를 건다.
       비평활 항이 있어도 가속이 그대로 작동한다는 것이 이 방법의 요점이다.
    """
    L = _lasso_L(X)
    x = [0.0] * len(X[0])
    z = list(x)
    t = 1.0
    hist = []
    for k in range(iters):
        r = [la.dot(X[i], z) - y[i] for i in range(len(X))]
        g = la.matvec(la.transpose(X), r)
        x_new = cx.soft_threshold(la.axpy(-1.0 / L, g, z), lam / L)
        t_new = 0.5 * (1.0 + math.sqrt(1.0 + 4.0 * t * t))
        z = la.axpy((t - 1.0) / t_new, la.vsub(x_new, x), x_new)
        x, t = x_new, t_new
        if keep_history:
            hist.append(_lasso_obj(X, y, x, lam))
    return Result(x, _lasso_obj(X, y, x, lam), iters, hist)


def lasso_coordinate(X, y, lam, iters=200, tol=1e-14):
    """좌표하강 — 한 번에 좌표 하나만 정확히 최적화한다.

       라쏘의 한 좌표 부분문제는 닫힌 해(연성 문턱)를 가진다. 좌표별로 최적화하면
       ‖·‖₁ 이 좌표마다 분리되므로 <비평활인데도> 좌표하강이 최적해로 수렴한다.
       (일반적인 비평활 함수에서는 좌표하강이 엉뚱한 점에 갇힐 수 있다.)
    """
    n, d = len(X), len(X[0])
    x = [0.0] * d
    col2 = [math.fsum(X[i][j] ** 2 for i in range(n)) for j in range(d)]
    r = [la.dot(X[i], x) - y[i] for i in range(n)]
    for _ in range(iters):
        delta = 0.0
        for j in range(d):
            if col2[j] == 0.0:
                continue
            rho = math.fsum(X[i][j] * (r[i] - X[i][j] * x[j]) for i in range(n))
            new = cx.soft_threshold([-rho], lam)[0] / col2[j]
            if new != x[j]:
                diff = new - x[j]
                for i in range(n):
                    r[i] += X[i][j] * diff
                delta = max(delta, abs(diff))
                x[j] = new
        if delta < tol:
            break
    return Result(x, _lasso_obj(X, y, x, lam))


def lasso_admm(X, y, lam, rho=1.0, iters=500):
    """ADMM 으로 라쏘를 푼다.

       min ½‖Xx−y‖² + λ‖z‖₁  s.t.  x − z = 0  으로 쪼갠 뒤 증강 라그랑주(5부 22장)를
       x 와 z 에 <번갈아> 적용한다.

           x ← (XᵀX + ρI)⁻¹ (Xᵀy + ρ(z − u))     ← 선형계 한 번 (미리 분해해 둔다)
           z ← prox_{λ/ρ}(x + u)                  ← 연성 문턱
           u ← u + x − z                          ← 승수 갱신

       두 부분문제가 각각 쉬운 것이 요점이다. 큰 문제를 <쉬운 조각으로 분해>하는
       일반적인 틀이며, 분산 학습에서 널리 쓰인다.
    """
    d = len(X[0])
    XtX = la.matmul(la.transpose(X), X)
    for i in range(d):
        XtX[i][i] += rho
    Xty = la.matvec(la.transpose(X), y)
    fac = la.lu_factor(XtX)
    x = [0.0] * d
    z = [0.0] * d
    u = [0.0] * d
    for _ in range(iters):
        rhs = la.vadd(Xty, la.vscale(rho, la.vsub(z, u)))
        x = la.lu_solve(fac, rhs)
        z = cx.soft_threshold(la.vadd(x, u), lam / rho)
        u = la.vadd(u, la.vsub(x, z))
    return Result(z, _lasso_obj(X, y, z, lam))
