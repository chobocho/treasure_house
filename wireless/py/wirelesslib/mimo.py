# -*- coding: utf-8 -*-
"""mimo — 안테나를 여럿 두면 무엇이 좋아지는가.

   세 가지가 좋아지고, 셋은 서로 다른 것이다. 헷갈리면 이 장으로
   돌아오면 된다.

     · **다이버시티** — 같은 것을 여러 길로 보낸다. 다 같이 죽을 확률이
       작아지므로 BER 곡선의 기울기가 가팔라진다. 알라무티는 송신
       안테나 둘로 채널을 몰라도 차수 2 를 얻는다.
     · **다중화** — 서로 다른 것을 동시에 보낸다. 용량이 min(N_t,N_r)
       배로 는다. 특잇값 하나가 한 줄기다.
     · **배열 이득** — 여러 소자를 한 방향으로 모은다. 조향 방향에서
       전력이 N 배가 된다. 위상만 맞추면 되므로 가장 값싼 이득이다.

   massive MIMO 가 하는 일은 셋째를 극단으로 밀면서 **채널 경화** 를
   덤으로 얻는 것이다 — 안테나가 많아지면 순간 이득의 출렁임이
   1/N 로 줄어, 페이딩이 사실상 사라진다.
"""
import cmath
import math
import random


# ── 알라무티 ──────────────────────────────────────────────────────


def alamouti_channel(s, h):
    """두 심볼을 두 시각·두 안테나로 보내 한 안테나로 받는다.

        시각 1: (s₁, s₂)      시각 2: (−s₂*, s₁*)

    수신은 y₁ = h₁s₁ + h₂s₂, y₂ = −h₁s₂* + h₂s₁* 다. 두 식이 직교해서,
    채널만 알면 나눗셈 없이 두 심볼이 분리된다 — 행렬을 뒤집지 않는다는
    것이 알라무티의 값어치다.
    """
    s1, s2 = s
    h1, h2 = h
    return [h1 * s1 + h2 * s2,
            -h1 * s2.conjugate() + h2 * s1.conjugate()]


def alamouti_decode(y, h):
    """두 줄짜리 결합식. 결과는 |h₁|²+|h₂|² 배로 커진 원래 심볼이다."""
    y1, y2 = y
    h1, h2 = h
    g = abs(h1) ** 2 + abs(h2) ** 2
    if g == 0:
        raise ValueError('채널이 0 이다')
    s1 = (h1.conjugate() * y1 + h2 * y2.conjugate()) / g
    s2 = (h2.conjugate() * y1 - h1 * y2.conjugate()) / g
    return [s1, s2]


def _bpsk_ber_run(ebn0_db, frames, seed, alamouti):
    rnd = random.Random(seed)
    ebn0 = 10.0 ** (ebn0_db / 10.0)
    sd = math.sqrt(1.0 / (2.0 * ebn0))
    bad = 0
    total = 0
    for _ in range(frames):
        if alamouti:
            # 송신 전력을 안테나 둘에 나눠야 공평한 비교가 된다
            h = [complex(rnd.gauss(0, math.sqrt(0.5)),
                         rnd.gauss(0, math.sqrt(0.5)))
                 for _ in range(2)]
            b = [rnd.getrandbits(1), rnd.getrandbits(1)]
            s = [complex(1 - 2 * v, 0) / math.sqrt(2.0) for v in b]
            y = alamouti_channel(s, h)
            y = [v + complex(rnd.gauss(0, sd), rnd.gauss(0, sd))
                 for v in y]
            got = alamouti_decode(y, h)
            for i in (0, 1):
                total += 1
                if (0 if got[i].real > 0 else 1) != b[i]:
                    bad += 1
        else:
            h = complex(rnd.gauss(0, math.sqrt(0.5)),
                        rnd.gauss(0, math.sqrt(0.5)))
            b = rnd.getrandbits(1)
            s = complex(1 - 2 * b, 0)
            y = h * s + complex(rnd.gauss(0, sd), rnd.gauss(0, sd))
            z = y * h.conjugate()
            total += 1
            if (0 if z.real > 0 else 1) != b:
                bad += 1
    return bad / float(total)


def alamouti_ber(ebn0_db, frames, seed=1):
    """알라무티 2×1 의 BER. 높은 SNR 에서 SNR⁻² 로 떨어진다."""
    return _bpsk_ber_run(ebn0_db, frames, seed, True)


def siso_rayleigh_ber(ebn0_db, frames, seed=1):
    """비교용 1×1 레일리 BER. SNR⁻¹ 로만 떨어진다."""
    return _bpsk_ber_run(ebn0_db, frames, seed, False)


# ── 선형 검출 ─────────────────────────────────────────────────────


def apply_channel(h, x):
    """y = H·x."""
    return [sum(h[i][j] * x[j] for j in range(len(x)))
            for i in range(len(h))]


def _solve(a, b):
    """복소 정사각 연립방정식을 부분 피벗 가우스 소거로 푼다."""
    n = len(a)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]
    for k in range(n):
        piv = max(range(k, n), key=lambda i: abs(m[i][k]))
        if abs(m[piv][k]) < 1e-12:
            raise ValueError('행렬이 특이하다 — 역행렬이 없다')
        m[k], m[piv] = m[piv], m[k]
        for i in range(k + 1, n):
            f = m[i][k] / m[k][k]
            for j in range(k, n + 1):
                m[i][j] -= f * m[k][j]
    x = [0j] * n
    for i in range(n - 1, -1, -1):
        s = m[i][n] - sum(m[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / m[i][i]
    return x


def _hermitian_gram(h):
    """HᴴH — 검출기와 특잇값이 함께 쓴다."""
    nt = len(h[0])
    nr = len(h)
    return [[sum(h[k][i].conjugate() * h[k][j] for k in range(nr))
             for j in range(nt)] for i in range(nt)]


def zf_detect(h, y):
    """영 강제 검출. (HᴴH)⁻¹Hᴴy — 간섭을 완전히 지운다.

    대신 잡음도 같이 키운다. 채널이 나쁜 방향(특잇값이 작은 쪽)에서는
    1/σ 배로 커지므로, 낮은 SNR 에서는 MMSE 가 낫다.
    """
    g = _hermitian_gram(h)
    nr = len(h)
    rhs = [sum(h[k][i].conjugate() * y[k] for k in range(nr))
           for i in range(len(h[0]))]
    return _solve(g, rhs)


def mmse_detect(h, y, n0):
    """MMSE 검출. (HᴴH + N₀I)⁻¹Hᴴy.

    간섭을 다 지우지 않는 대신 잡음을 덜 키운다. N₀ → 0 이면 ZF 와
    같아진다 — 시험이 그 극한을 확인한다.
    """
    g = _hermitian_gram(h)
    for i in range(len(g)):
        g[i][i] += n0
    nr = len(h)
    rhs = [sum(h[k][i].conjugate() * y[k] for k in range(nr))
           for i in range(len(h[0]))]
    return _solve(g, rhs)


def detect_mse(snr_db, trials, seed=1, kind='zf', n=2):
    """검출 오차의 평균 제곱. 낮은 SNR 에서 MMSE 가 작아야 한다."""
    rnd = random.Random(seed)
    n0 = 10.0 ** (-snr_db / 10.0)
    sd = math.sqrt(n0 / 2.0)
    acc = 0.0
    cnt = 0
    for _ in range(trials):
        h = [[complex(rnd.gauss(0, math.sqrt(0.5)),
                      rnd.gauss(0, math.sqrt(0.5)))
              for _ in range(n)] for _ in range(n)]
        x = [complex(1 - 2 * rnd.getrandbits(1), 0) for _ in range(n)]
        y = [v + complex(rnd.gauss(0, sd), rnd.gauss(0, sd))
             for v in apply_channel(h, x)]
        try:
            est = (zf_detect(h, y) if kind == 'zf'
                   else mmse_detect(h, y, n0))
        except ValueError:
            continue
        for a, b in zip(x, est):
            acc += abs(a - b) ** 2
            cnt += 1
    return acc / max(cnt, 1)


# ── 특잇값 ────────────────────────────────────────────────────────


def _jacobi_eigvals(a, sweeps=60, tol=1e-14):
    """실 대칭 행렬의 고윳값 — 순환 야코비. 시간 O(n³·sweeps)."""
    n = len(a)
    m = [list(row) for row in a]
    for _ in range(sweeps):
        off = math.sqrt(sum(m[i][j] ** 2 for i in range(n)
                            for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(m[p][q]) < tol:
                    continue
                theta = (m[q][q] - m[p][p]) / (2.0 * m[p][q])
                t = ((1.0 if theta >= 0 else -1.0)
                     / (abs(theta) + math.sqrt(theta * theta + 1.0)))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = m[k][p], m[k][q]
                    m[k][p] = c * akp - s * akq
                    m[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = m[p][k], m[q][k]
                    m[p][k] = c * apk - s * aqk
                    m[q][k] = s * apk + c * aqk
    return sorted((m[i][i] for i in range(n)), reverse=True)


def singular_values(h):
    """H 의 특잇값 (큰 것부터). numpy 없이 구한다.

    에르미트 행렬 A = X + iY 의 고윳값은 실 대칭 행렬 [[X,−Y],[Y,X]] 의
    고윳값과 같고 각각 두 번씩 나온다. 그래서 복소 야코비를 짜는 대신
    실수 야코비 하나로 끝낸다 — 짧고 틀릴 데가 적다.
    """
    g = _hermitian_gram(h)
    n = len(g)
    big = [[0.0] * (2 * n) for _ in range(2 * n)]
    for i in range(n):
        for j in range(n):
            x, y = g[i][j].real, g[i][j].imag
            big[i][j] = x
            big[i + n][j + n] = x
            big[i][j + n] = -y
            big[i + n][j] = y
    ev = _jacobi_eigvals(big)
    every_other = [ev[2 * i] for i in range(n)]
    return [math.sqrt(max(0.0, v)) for v in every_other]


def capacity_from_sv(sv, nt, snr_db):
    """특잇값으로 센 용량 — Σ log₂(1 + ρ/N_t · σᵢ²).

    log₂det 공식과 같은 값이어야 한다. 같다는 것이 곧 "MIMO 채널은
    서로 간섭하지 않는 평행 채널 min(N_t,N_r) 개와 같다" 는 말이다.
    """
    rho = 10.0 ** (snr_db / 10.0) / nt
    return sum(math.log2(1.0 + rho * s * s) for s in sv)


# ── 균일 선형 배열 ────────────────────────────────────────────────


def array_factor(n, d_lambda, theta, steer=0.0):
    """N 소자 균일 선형 배열의 배열 인자.

        AF(θ) = Σ_{k=0}^{N−1} e^{jk(2πd·sinθ − 2πd·sinθ₀)}

    조향 방향(θ=θ₀)에서 모든 항의 위상이 같아져 크기가 정확히 N 이 된다.
    그것이 배열 이득의 전부다 — 새 에너지를 만드는 것이 아니라
    한 방향으로 모으는 것이다.
    """
    psi = 2.0 * math.pi * d_lambda * (math.sin(theta)
                                      - math.sin(steer))
    return sum(cmath.exp(1j * k * psi) for k in range(n))


def array_gain_db(n):
    """조향 방향의 배열 이득 — 10·log₁₀ N."""
    if n < 1:
        raise ValueError('소자 수는 1 이상이어야 한다')
    return 10.0 * math.log10(n)


def count_nulls(n, d_lambda, steer=0.0):
    """주엽 둘레에서 배열 인자가 0 이 되는 자리의 수.

    널은 위상차 ψ 가 2πk/N (k = 1…N−1) 일 때 생긴다. 그것을 각도로
    옮기면 sinθ = sinθ₀ ± k/(N·d) 이고, |sinθ| ≤ 1 인 것만 실제
    각도로 나타난다. 표본을 훑어 최소를 찾는 대신 닫힌 식으로 세는
    까닭: 표본 사이에 널이 놓이면 그냥 놓친다.

    반파장 간격이면 −90°~90° 안에 정확히 N−1 개가 보인다. 널의 수와
    자리가 곧 '간섭을 어디로 버릴 수 있는가' 다.
    """
    if n < 2:
        return 0
    cnt = 0
    for k in range(1, n):
        for sign in (1, -1):
            s = math.sin(steer) + sign * k / (n * d_lambda)
            if -1.0 <= s <= 1.0:
                cnt += 1
    return min(cnt, n - 1)


def beamwidth_rad(n, d_lambda):
    """주엽의 널 대 널 폭 [rad] — 대략 2λ/(N·d).

    배열이 크면 빔이 좁아진다.
    """
    if n < 2:
        raise ValueError('소자가 둘 이상이어야 빔이 생긴다')
    return 2.0 / (n * d_lambda)


def has_grating_lobe(d_lambda):
    """간격이 반파장을 넘으면 주엽과 똑같은 격자엽이 생긴다.

    그래서 배열 간격의 상한이 λ/2 다. 넓게 두면 개구가 커져 빔이
    좁아지지만, 엉뚱한 방향으로도 똑같이 세게 쏘게 된다.
    """
    return d_lambda > 0.5


# ── 채널 경화 ─────────────────────────────────────────────────────


def _hardening_samples(n, trials, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(trials):
        s = 0.0
        for _k in range(n):
            s += (rnd.gauss(0, math.sqrt(0.5)) ** 2
                  + rnd.gauss(0, math.sqrt(0.5)) ** 2)
        out.append(s / n)
    return out


def hardening_mean(n, trials, seed=1):
    v = _hardening_samples(n, trials, seed)
    return sum(v) / len(v)


def hardening_variance(n, trials, seed=1):
    """‖h‖²/N 의 분산. 1/N 로 준다 — 이것이 채널 경화다.

    안테나가 많아지면 순간 이득이 평균에 붙어 버려서, 페이딩을 쫓는
    일(빠른 전력 제어·재전송)이 덜 중요해진다. massive MIMO 가
    스케줄링을 단순하게 만든 까닭이 여기 있다.
    """
    v = _hardening_samples(n, trials, seed)
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / len(v)
