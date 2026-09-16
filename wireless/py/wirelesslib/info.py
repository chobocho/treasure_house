# -*- coding: utf-8 -*-
"""info — 용량. 이 책 전체의 잣대가 여기서 나온다.

   "이 규격은 잘 만든 것인가" 라는 물음은 결국 "섀넌 한계에서 얼마나
   떨어져 있는가" 로 바뀐다. 그래서 세대를 다루는 모든 장이 이 모듈을
   되부른다.

   담긴 것:

     · AWGN 용량과 −1.59 dB 의 벽
     · 레일리 채널의 에르고딕 용량(닫힌 식 + 몬테카를로)과 중단 용량
     · 평행 채널의 물채우기
     · MIMO 용량 log₂ det(I + ρ/N_t · H Hᴴ)
     · 성상도가 실제로 실어 나를 수 있는 양(상호정보)

   마지막 것이 중요하다. 섀넌 용량은 입력이 가우스일 때의 값이라,
   16QAM 으로는 아무리 좋은 부호를 써도 4 비트를 넘길 수 없다.
   이 '성상도 한계' 가 왜 세대마다 변조 차수를 올렸는지를 설명한다.
"""
import math
import random

EULER = 0.5772156649015329


def db2lin(db):
    return 10.0 ** (db / 10.0)


def lin2db(v):
    return 10.0 * math.log10(v)


# ── 지수적분 ──────────────────────────────────────────────────────


def e1(x, tol=1e-15, itmax=200):
    """지수적분 E₁(x) = ∫₁^∞ e^{−xt}/t dt (x > 0).

    레일리 에르고딕 용량의 닫힌 식에 이 함수가 들어간다. 표준
    라이브러리에 없어서 직접 짠다 — 작은 x 는 급수로, 큰 x 는
    연분수로 푼다(Numerical Recipes 의 expint 와 같은 갈래).

    두 갈래를 쓰는 까닭: 급수는 x 가 커지면 항이 번갈아 커졌다
    작아지며 자릿수를 다 잃고, 연분수는 x 가 작으면 안 모인다.
    """
    if x <= 0:
        raise ValueError('E₁ 은 x > 0 에서만 정의된다: %g' % x)
    if x <= 1.0:
        s = -EULER - math.log(x)
        term = 1.0
        for k in range(1, itmax):
            term *= -x / k
            d = -term / k
            s += d
            if abs(d) < tol * abs(s):
                break
        return s
    # 연분수 — 수정 렌츠 알고리즘
    tiny = 1e-300
    b = x + 1.0
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, itmax):
        a = -i * i
        b += 2.0
        d = 1.0 / (a * d + b)
        c = b + a / c
        delta = c * d
        h *= delta
        if abs(delta - 1.0) < tol:
            break
    return h * math.exp(-x)


# ── AWGN ──────────────────────────────────────────────────────────


def capacity_awgn(snr_db):
    """섀넌–하틀리. C = log₂(1 + ρ) [bit/s/Hz]."""
    return math.log2(1.0 + db2lin(snr_db))


def ebn0_min_db(eff):
    """스펙트럼 효율 η 를 내려면 최소한 얼마의 Eb/N0 가 필요한가.

        Eb/N0 = (2^η − 1) / η

    η → 0 으로 보내면 ln 2, 곧 −1.59 dB 로 간다. 이것이 부호를 아무리
    잘 만들어도 못 넘는 바닥이다.
    """
    if eff <= 0:
        raise ValueError('효율은 양수여야 한다')
    return lin2db((2.0 ** eff - 1.0) / eff)


# ── 레일리 ────────────────────────────────────────────────────────


def capacity_rayleigh_ergodic(snr_db):
    """레일리 채널의 에르고딕 용량 — 닫힌 식.

        C = log₂e · e^{1/ρ} · E₁(1/ρ)

    평균 SNR 이 같아도 AWGN 보다 반드시 작다. log 가 오목 함수라
    젠센 부등식이 그렇게 만든다 — 페이딩은 평균적으로 손해다.
    이 사실이 다이버시티가 필요한 이유의 절반이다.
    """
    rho = db2lin(snr_db)
    z = 1.0 / rho
    return math.log2(math.e) * math.exp(z) * e1(z)


def capacity_rayleigh_mc(snr_db, n, seed=1):
    """같은 값을 표본 평균으로. |h|² 는 평균 1 인 지수분포다."""
    rnd = random.Random(seed)
    rho = db2lin(snr_db)
    s = 0.0
    for _ in range(n):
        s += math.log2(1.0 + rho * rnd.expovariate(1.0))
    return s / n


def capacity_rayleigh_outage(snr_db, eps):
    """중단 용량 — 시간의 ε 만큼은 못 받아도 좋다고 할 때의 속도.

    |h|² 가 평균 1 인 지수분포이므로 하위 ε 분위수는 −ln(1−ε) 다.
    지연에 민감한 서비스가 보는 것은 에르고딕 용량이 아니라 이 값이다.
    """
    if not 0.0 < eps < 1.0:
        raise ValueError('ε 는 0 과 1 사이여야 한다')
    return math.log2(1.0 + db2lin(snr_db) * (-math.log(1.0 - eps)))


# ── 평행 채널과 물채우기 ──────────────────────────────────────────


def waterfill(gains, total):
    """평행 채널에 전력을 어떻게 나눌 것인가.

        p_i = max(0, μ − 1/g_i),  Σ p_i = P

    좋은 채널에 더 주고 나쁜 채널은 아예 끈다. '물을 부으면 골짜기가
    먼저 찬다' 는 그림이 그대로 식이다. 1/g 를 오름차순으로 훑으며
    켜진 채널의 집합을 늘려 가면 되므로 O(n log n).
    """
    if total < 0:
        raise ValueError('전력은 음수일 수 없다')
    idx = sorted(range(len(gains)), key=lambda i: -gains[i])
    inv = [1.0 / gains[i] for i in idx]
    best_k, level = 0, 0.0
    acc = 0.0
    for k in range(1, len(inv) + 1):
        acc += inv[k - 1]
        mu = (total + acc) / k
        if mu > inv[k - 1]:
            best_k, level = k, mu
        else:
            break
    out = [0.0] * len(gains)
    for j in range(best_k):
        out[idx[j]] = level - inv[j]
    return out


def capacity_parallel(gains, powers):
    """평행 채널의 합 용량 — Σ log₂(1 + g_i p_i)."""
    return sum(math.log2(1.0 + g * p) for g, p in zip(gains, powers))


# ── 작은 복소 선형대수 ────────────────────────────────────────────


def _logdet(a):
    """부분 피벗 LU 로 log|det|. a 는 정사각 복소 행렬(리스트의 리스트).

    numpy 가 없으니 직접 짠다. 이 책에서 쓰는 크기는 최대 8×8 이라
    O(n³) 로 충분하다.
    """
    n = len(a)
    m = [row[:] for row in a]
    s = 0.0
    for k in range(n):
        piv = max(range(k, n), key=lambda i: abs(m[i][k]))
        if abs(m[piv][k]) < 1e-300:
            return float('-inf')
        if piv != k:
            m[k], m[piv] = m[piv], m[k]
        s += math.log(abs(m[k][k]))
        for i in range(k + 1, n):
            f = m[i][k] / m[k][k]
            if f == 0:
                continue
            for j in range(k, n):
                m[i][j] -= f * m[k][j]
    return s


def mimo_capacity(h, snr_db):
    """MIMO 용량. C = log₂ det(I + ρ/N_t · H Hᴴ).

    송신기가 채널을 모르면 전력을 안테나에 고르게 나눌 수밖에 없다 —
    ρ/N_t 가 그 뜻이다. 높은 SNR 에서 이 값은 min(N_t, N_r) 개의
    평행 채널처럼 늘어난다. 그 min 이 곧 다중화 이득이다.

    h 는 N_r × N_t 행렬이다(행이 수신, 열이 송신).
    """
    nr = len(h)
    nt = len(h[0])
    rho = db2lin(snr_db) / nt
    a = [[(1.0 + 0j if i == j else 0j) for j in range(nr)]
         for i in range(nr)]
    for i in range(nr):
        for j in range(nr):
            s = 0j
            for t in range(nt):
                s += h[i][t] * h[j][t].conjugate()
            a[i][j] += rho * s
    return _logdet(a) / math.log(2.0)


def mimo_capacity_mc(nt, nr, snr_db, trials, seed=1):
    """i.i.d. 레일리 채널에서 MIMO 용량의 표본 평균."""
    rnd = random.Random(seed)
    s = 0.0
    sd = math.sqrt(0.5)
    for _ in range(trials):
        h = [[complex(rnd.gauss(0.0, sd), rnd.gauss(0.0, sd))
              for _ in range(nt)] for _ in range(nr)]
        s += mimo_capacity(h, snr_db)
    return s / trials


# ── 성상도의 상호정보 ─────────────────────────────────────────────


def constellation_mi(name, snr_db, n, seed=1):
    """유한 성상도가 AWGN 에서 실어 나를 수 있는 비트 수 [bit/심볼].

        I(X;Y) = k − E[ log₂ Σ_j exp( −(|y−s_j|² − |y−s_x|²)/N₀ ) ]

    높은 SNR 에서 k 로 포화한다 — 16QAM 은 4 비트를 넘길 수 없다.
    이 포화점이 세대마다 변조 차수를 올린 이유이자, MCS 표가 왜
    계단처럼 생겼는지의 답이다.

    같은 SNR 에서 이 값은 섀넌 용량보다 작거나 같다(가우스 입력이
    최적이므로). 몬테카를로 추정이라 표본이 적으면 ±0.03 쯤 흔들려
    용량을 살짝 넘어 보일 수 있다 — 시험은 그 오차 안에서 확인한다.
    """
    # 순환 참조를 피하려고 여기서 늦게 부른다
    from wirelesslib import modem
    c = modem.constellation(name)
    rnd = random.Random(seed)
    n0 = 1.0 / db2lin(snr_db)
    sd = math.sqrt(n0 / 2.0)
    acc = 0.0
    for _ in range(n):
        x = rnd.randrange(c.m)
        noise = complex(rnd.gauss(0.0, sd), rnd.gauss(0.0, sd))
        y = c.points[x] + noise
        dx = abs(y - c.points[x]) ** 2
        s = 0.0
        for p in c.points:
            s += math.exp(-(abs(y - p) ** 2 - dx) / n0)
        acc += math.log2(s)
    return c.k - acc / n
