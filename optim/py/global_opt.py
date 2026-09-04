# -*- coding: utf-8 -*-
"""비평활·전역 최적화 — 기울기가 없거나, 최소점이 여럿일 때.

   지금까지의 방법들은 두 가지를 가정했다: 기울기를 계산할 수 있고, 국소해면
   충분하다는 것. 그 가정이 깨지는 자리가 있다.

     · 목적함수가 블랙박스다 (시뮬레이션·실험·하이퍼파라미터)
     · 미분이 존재하지 않는다 (‖·‖₁, max, 이산 성분)
     · 최소점이 여럿이고 전역해가 필요하다

   여기서 다루는 방법들은 보장이 약하다. 열경사법만 수렴률이 증명되고, 나머지는
   "잘 되더라" 수준의 보장뿐이다. 그 한계를 숨기지 않고 실측으로 보인다.
"""
import math
import random

from py import linalg as la


class Result(object):
    def __init__(self, x, fx, nit=0, nfev=0, history=None, msg=''):
        self.x = x
        self.fx = fx
        self.nit = nit
        self.nfev = nfev
        self.history = history or []
        self.msg = msg

    def __repr__(self):
        return '<Global f=%.6g nfev=%d>' % (self.fx, self.nfev)


# ---------------------------------------------------------------- 열경사법

def subgradient(f, subg, x0, step, iters=1000, keep_history=False):
    """열경사법:  x ← x − α_k g,  g ∈ ∂f(x).

       경사하강처럼 보이지만 결정적으로 다른 점이 있다: <열경사는 하강 방향이
       아닐 수 있다>. 그래서 f(x_k) 가 단조 감소하지 않으며, 라인서치를 쓸 수도 없다
       (어느 방향이 좋은지 국소 정보만으로는 모른다).

       그래서 '지금까지의 최선'을 따로 들고 다닌다. 수렴률은 볼록·립시츠 가정에서
       O(1/√k) — 경사하강의 O(1/k) 보다 느리고, 이것이 비평활의 대가다.
    """
    x = [float(v) for v in x0]
    best_x, best_f = list(x), f(x)
    hist = []
    for k in range(iters):
        g = subg(x)
        x = la.axpy(-step(k), g, x)
        fv = f(x)
        if fv < best_f:
            best_f, best_x = fv, list(x)
        if keep_history:
            hist.append({'k': k, 'f': fv, 'best': best_f, 'step': step(k)})
    return Result(best_x, best_f, iters, iters, hist)


# ---------------------------------------------------------------- Nelder–Mead

def nelder_mead(f, x0, step0=0.5, maxiter=2000, tol=1e-12,
                alpha=1.0, gamma=2.0, rho=0.5, sigma=0.5, keep_history=False):
    """Nelder–Mead 단체법 — 기울기를 전혀 쓰지 않는다.

       n+1 개의 점(단체)을 두고, 가장 나쁜 점을 나머지의 무게중심 너머로 <반사>한다.
       잘 되면 더 멀리(확장), 안 되면 덜 멀리(수축), 그래도 안 되면 전체를 줄인다.

       장점: 도함수가 필요 없고 구현이 짧다. 잡음이 있는 목적함수에도 쓸 수 있다.
       한계: 수렴 보장이 없다(McKinnon 의 반례). 차원이 10 을 넘으면 급격히 나빠진다.
             그래도 저차원 블랙박스에서는 여전히 널리 쓰인다.
    """
    n = len(x0)
    simplex = [list(x0)]
    for i in range(n):
        p = list(x0)
        p[i] += step0 if p[i] == 0 else step0 * abs(p[i])
        simplex.append(p)
    fv = [f(p) for p in simplex]
    nfev = n + 1
    hist = []
    for it in range(maxiter):
        order = sorted(range(n + 1), key=lambda i: fv[i])
        simplex = [simplex[i] for i in order]
        fv = [fv[i] for i in order]
        size = max(la.norm(la.vsub(simplex[i], simplex[0])) for i in range(1, n + 1))
        if keep_history:
            hist.append({'k': it, 'f': fv[0], 'size': size})
        if size < tol:
            break
        cen = [math.fsum(simplex[i][j] for i in range(n)) / n for j in range(n)]
        xr = la.axpy(alpha, la.vsub(cen, simplex[n]), cen)
        fr = f(xr); nfev += 1
        if fv[0] <= fr < fv[n - 1]:
            simplex[n], fv[n] = xr, fr
            continue
        if fr < fv[0]:                                   # 확장
            xe = la.axpy(gamma, la.vsub(xr, cen), cen)
            fe = f(xe); nfev += 1
            simplex[n], fv[n] = (xe, fe) if fe < fr else (xr, fr)
            continue
        xc = la.axpy(rho, la.vsub(simplex[n], cen), cen)  # 수축
        fc = f(xc); nfev += 1
        if fc < fv[n]:
            simplex[n], fv[n] = xc, fc
            continue
        for i in range(1, n + 1):                        # 축소
            simplex[i] = la.axpy(sigma, la.vsub(simplex[i], simplex[0]), simplex[0])
            fv[i] = f(simplex[i]); nfev += 1
    k = min(range(n + 1), key=lambda i: fv[i])
    return Result(simplex[k], fv[k], it + 1, nfev, hist)


# ---------------------------------------------------------------- 담금질

def simulated_annealing(f, x0, lo, hi, iters=10000, t0=1.0, seed=0,
                        scale=0.1, keep_history=False):
    """담금질 — 나쁜 이동도 확률 exp(−Δ/T) 로 받아들인다.

       온도 T 가 높으면 거의 무작위로 떠돌고(탐색), 낮으면 탐욕에 가까워진다(활용).
       T 를 천천히 낮추면 국소 최소에서 빠져나올 기회를 주면서 결국 좋은 곳에 머문다.

       이론: T_k ≥ c/log(k) 로 아주 느리게 식히면 전역해로의 확률 수렴이 증명된다.
       실제로 그 일정은 너무 느려 쓸 수 없고, 기하급수 냉각을 쓴다 — 그러면 보장은
       사라진다. 이 방법의 정직한 성격이다.

       scale 은 제안 분포의 폭(구간 길이 대비)이다. 이것이 크면 온도와 무관하게
       분지 사이를 건너뛰므로 온도의 효과가 보이지 않는다. 제안 분포와 냉각 일정을
       함께 봐야 담금질을 이해한 것이다.
    """
    rng = random.Random(seed)
    x = [float(v) for v in x0]
    fx = f(x)
    best_x, best_f = list(x), fx
    step_sd = [(hi[i] - lo[i]) * scale for i in range(len(x))]
    hist = []
    for k in range(iters):
        T = max(t0 * (1.0 - k / float(iters)) ** 2, 1e-12)
        cand = [min(hi[i], max(lo[i], x[i] + rng.gauss(0, step_sd[i])))
                for i in range(len(x))]
        fc = f(cand)
        d = fc - fx
        if d <= 0 or rng.random() < math.exp(-d / T):
            x, fx = cand, fc
            if fx < best_f:
                best_f, best_x = fx, list(x)
        if keep_history:
            hist.append({'k': k, 'f': fx, 'T': T, 'best': best_f})
    return Result(best_x, best_f, iters, iters, hist)


# ---------------------------------------------------------------- 유전 알고리즘

def genetic(f, lo, hi, pop=40, gens=60, seed=0, elite=2, mut=0.2,
            keep_history=False):
    """유전 알고리즘 — 개체군을 두고 선택·교차·변이를 반복한다.

       엘리트 보존(가장 좋은 몇 개를 그대로 다음 세대로) 덕분에 최선값이 단조
       감소한다. 그 외의 보장은 없다.

       담금질과의 차이: 담금질은 <한 점>이 온도에 따라 떠돌고, 유전 알고리즘은
       <여러 점>이 정보를 교환한다. 목적함수가 비싸면 개체군을 유지하는 비용이 크다.
    """
    n = len(lo)
    rng = random.Random(seed)
    P = [[rng.uniform(lo[i], hi[i]) for i in range(n)] for _ in range(pop)]
    F = [f(p) for p in P]
    nfev = pop
    hist = []
    for g in range(gens):
        order = sorted(range(pop), key=lambda i: F[i])
        P = [P[i] for i in order]
        F = [F[i] for i in order]
        if keep_history:
            hist.append({'gen': g, 'best': F[0],
                         'mean': math.fsum(F) / pop,
                         'spread': max(la.norm(la.vsub(P[i], P[0]))
                                       for i in range(pop))})
        newP = [list(P[i]) for i in range(elite)]
        while len(newP) < pop:
            # 토너먼트 선택 — 무작위 둘 중 나은 쪽
            a = min(rng.randrange(pop), rng.randrange(pop))
            b = min(rng.randrange(pop), rng.randrange(pop))
            t = rng.random()
            child = [t * P[a][i] + (1 - t) * P[b][i] for i in range(n)]   # 혼합 교차
            for i in range(n):
                if rng.random() < mut:
                    child[i] += rng.gauss(0, (hi[i] - lo[i]) * 0.1)
                child[i] = min(hi[i], max(lo[i], child[i]))
            newP.append(child)
        P = newP
        F = [f(p) for p in P]
        nfev += pop - elite
    k = min(range(pop), key=lambda i: F[i])
    return Result(P[k], F[k], gens, nfev, hist)


# ---------------------------------------------------------------- 베이지안 최적화

class GP(object):
    """가우스 과정 회귀 (RBF 커널).

       함수 자체에 확률분포를 두고, 관측한 자료로 그 분포를 갱신한다. 예측은
       평균(어디가 좋아 보이는가)과 표준편차(어디를 아직 모르는가)를 함께 준다.
       그 둘을 결합해 다음 관측점을 고르는 것이 베이지안 최적화다.

       비용: 관측 N 개에 대해 촐레스키 O(N³). 그래서 <함수 평가가 아주 비쌀 때>만
       쓴다 — 하이퍼파라미터 튜닝, 실험 설계, 시뮬레이션 최적화가 전형적이다.
    """

    def __init__(self, X, y, length=1.0, sigma=1.0, noise=1e-6):
        self.X = [list(p) for p in X]
        self.length = length
        self.sigma = sigma
        self.noise = noise
        self.ymean = math.fsum(y) / len(y) if y else 0.0
        self.y = [v - self.ymean for v in y]
        n = len(X)
        K = la.zeros(n, n)
        for i in range(n):
            for j in range(n):
                K[i][j] = self.k(self.X[i], self.X[j])
            K[i][i] += noise
        self.L = la.cholesky(K)
        self.alpha = la.chol_solve(self.L, self.y)

    def k(self, a, b):
        d2 = math.fsum((a[i] - b[i]) ** 2 for i in range(len(a)))
        return self.sigma ** 2 * math.exp(-0.5 * d2 / (self.length ** 2))

    def predict(self, x):
        """사후 평균과 표준편차."""
        ks = [self.k(x, p) for p in self.X]
        mean = la.dot(ks, self.alpha) + self.ymean
        v = la.chol_solve(self.L, ks)
        var = self.k(x, x) - la.dot(ks, v)
        return mean, math.sqrt(max(var, 0.0))


def _norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def expected_improvement(gp, x, best, xi=0.01):
    """기대 개선량 EI(x) = E[max(best − f(x), 0)].

       닫힌 꼴:  EI = (best − μ − ξ)Φ(z) + σφ(z),  z = (best − μ − ξ)/σ.
       평균이 낮은 곳(활용)과 분산이 큰 곳(탐색)을 <하나의 수>로 저울질한다.
       ξ 는 탐색 쪽으로 살짝 기울이는 여유값이다.
    """
    mu, sd = gp.predict(x)
    if sd < 1e-12:
        return 0.0
    imp = best - mu - xi
    z = imp / sd
    return max(0.0, imp * _norm_cdf(z) + sd * _norm_pdf(z))


def bayes_opt(f, lo, hi, iters=25, init=4, seed=0, length=None, cand=400,
              keep_history=False):
    """베이지안 최적화 — 대리 모형(GP)을 세우고 EI 가 가장 큰 점을 다음에 평가한다.

       함수 평가 한 번이 비싼 상황을 가정한다. 그래서 '다음에 어디를 볼 것인가'를
       고르는 데 계산을 아끼지 않는다(여기서는 무작위 후보 cand 개 중 EI 최대).
    """
    n = len(lo)
    rng = random.Random(seed)
    if length is None:
        length = 0.2 * max(hi[i] - lo[i] for i in range(n))
    X = [[rng.uniform(lo[i], hi[i]) for i in range(n)] for _ in range(init)]
    Y = [f(p) for p in X]
    hist = []
    for t in range(iters):
        gp = GP(X, Y, length=length, sigma=max(1e-6, _spread(Y)), noise=1e-8)
        best = min(Y)
        cands = [[rng.uniform(lo[i], hi[i]) for i in range(n)] for _ in range(cand)]
        scores = [expected_improvement(gp, c, best) for c in cands]
        j = max(range(cand), key=lambda i: scores[i])
        X.append(cands[j])
        Y.append(f(cands[j]))
        if keep_history:
            hist.append({'t': t, 'best': min(Y), 'ei': scores[j],
                         'x': list(cands[j])})
    k = min(range(len(Y)), key=lambda i: Y[i])
    return Result(X[k], Y[k], iters, len(Y), hist)


def _spread(y):
    m = math.fsum(y) / len(y)
    return math.sqrt(math.fsum((v - m) ** 2 for v in y) / max(1, len(y) - 1))


def multistart(method, f, lo, hi, starts=10, seed=0, **kw):
    """여러 출발점에서 국소 최적화를 돌리고 가장 좋은 것을 고른다.

       비볼록 문제의 가장 단순하고 가장 견고한 전략이다. 국소 방법이 빠르면
       (뉴턴·BFGS) 이 조합이 전문화된 전역 기법보다 나은 경우가 많다.
    """
    rng = random.Random(seed)
    best = None
    nfev = 0
    for _ in range(starts):
        x0 = [rng.uniform(lo[i], hi[i]) for i in range(len(lo))]
        r = method(f, x0, **kw)
        nfev += r.nfev
        if best is None or r.fx < best.fx:
            best = r
    return Result(best.x, best.fx, starts, nfev)
