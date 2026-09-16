# -*- coding: utf-8 -*-
"""spread — 확산 부호. 2G CDMA·3G WCDMA·4G/5G 기준신호의 재료다.

   담긴 것은 넷이다.

     · **왈시·OVSF** — 완전히 직교한다. 대신 같은 시각에 맞춰야만
       직교하고, 조상·자손끼리는 쓸 수 없다. IS-95 순방향과 WCDMA
       하향이 이것으로 사용자를 가른다.
     · **m-수열** — 한 주기에 1 이 0 보다 딱 하나 많고, 자기상관이
       두 값(N, −1)뿐이다. 그래서 '언제인지' 를 찾는 데 쓴다.
     · **골드 부호** — m-수열 둘을 어긋나게 XOR 한 것. 상호상관이
       세 값뿐이라 여러 기지국이 같은 대역을 함께 쓸 수 있다.
     · **Zadoff-Chu** — 진폭이 늘 1 이고 순환 자기상관이 0 이다.
       LTE·NR 의 PSS·PRACH·SRS 가 전부 이것이다.

   **탭을 기억으로 적으면 안 되는 자리다.** 되먹임 다항식이 원시가
   아니면 주기가 확 짧아지는데, 수열을 눈으로 봐서는 모른다. 그래서
   is_primitive() 를 두고, IS-95 숏 PN·롱코드·WCDMA 스크램블링의 탭을
   그것으로 검산한다. 2⁴²−1 은 돌려서 셀 수 없으니 대수로 확인한다.
"""
import cmath
import math


# ── 왈시·아다마르 ─────────────────────────────────────────────────


def hadamard(n):
    """실베스터 방식 아다마르 행렬. H₁=[1], H₂ₙ=[[H,H],[H,−H]].

    행끼리 직교하고 각 행의 에너지가 N 이다. 시간·공간 O(N²).
    """
    if n < 1 or (n & (n - 1)):
        raise ValueError('아다마르 크기는 2의 거듭제곱이어야 한다: %d'
                         % n)
    h = [[1]]
    while len(h) < n:
        m = len(h)
        nh = [[0] * (2 * m) for _ in range(2 * m)]
        for i in range(m):
            for j in range(m):
                v = h[i][j]
                nh[i][j] = v
                nh[i][j + m] = v
                nh[i + m][j] = v
                nh[i + m][j + m] = -v
        h = nh
    return h


def walsh(n, k):
    """N 칩짜리 왈시 부호 k번. IS-95 순방향의 채널 구분이 이것이다."""
    return hadamard(n)[k]


def ovsf(sf, k):
    """OVSF 부호. C(2n,2k)=[c,c], C(2n,2k+1)=[c,−c] 로 자란다.

    확산율이 달라도 서로 직교할 수 있다는 것이 '직교 가변 확산율' 의
    뜻이다. 다만 조상을 쓰면 그 밑의 자손을 전부 못 쓴다 — 긴 부호의
    앞머리가 짧은 부호와 똑같아지기 때문이다.
    """
    if sf < 1 or (sf & (sf - 1)):
        raise ValueError('확산율은 2의 거듭제곱이어야 한다: %d' % sf)
    if not 0 <= k < sf:
        raise ValueError('부호 번호가 범위를 벗어났다: %d/%d' % (k, sf))
    c = [1]
    n = 1
    while n < sf:
        bit = (k >> (int(math.log2(sf // n)) - 1)) & 1
        c = c + ([-v for v in c] if bit else list(c))
        n *= 2
    return c


def is_ancestor(sf1, k1, sf2, k2):
    """(sf1,k1) 이 (sf2,k2) 의 조상인가. 조상이면 둘을 함께 못 쓴다."""
    if sf1 >= sf2:
        return False
    steps = int(math.log2(sf2 // sf1))
    return (k2 >> steps) == k1


# ── GF(2) 다항식 ──────────────────────────────────────────────────


def _polymulmod(a, b, f, m):
    """GF(2)[x] 곱셈 뒤 f 로 나눈 나머지. 시간 O(m²)."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> m & 1:
            a ^= f
    return r


def _polypowmod(base, e, f, m):
    r = 1
    base %= (1 << m)
    while e:
        if e & 1:
            r = _polymulmod(r, base, f, m)
        base = _polymulmod(base, base, f, m)
        e >>= 1
    return r


def _factorize(n):
    """작은 수의 소인수 집합. 2^42−1 까지는 시험 나눗셈으로 충분하다."""
    out = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            out.add(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out.add(n)
    return out


def is_primitive(poly, m):
    """f(x) 가 GF(2) 위의 원시 다항식인가 — 곧 주기가 2^m−1 인가.

    x 의 곱셈 차수가 정확히 2^m−1 인지를 본다. x^(2^m−1) ≡ 1 이면서
    2^m−1 의 어떤 진약수에서도 1 이 되지 않으면 원시다. f 가 기약이
    아니면 그런 원소가 아예 없으므로 이 검사 하나로 충분하다.

    돌려 보는 것이 아니라 대수로 푸는 까닭: 2⁴²−1 번 돌리는 일은
    이 기계에서 끝나지 않는다. 시간 O(log(2^m) · m²).
    """
    if not (poly >> m) & 1 or not poly & 1:
        return False
    order = (1 << m) - 1
    if _polypowmod(2, order, poly, m) != 1:
        return False
    for p in _factorize(order):
        if _polypowmod(2, order // p, poly, m) == 1:
            return False
    return True


# ── LFSR 과 m-수열 ────────────────────────────────────────────────
#
# 탭은 전부 규격에서 온 것이고, is_primitive() 로 검산한다.
# IS-95 숏 PN — TIA/EIA/IS-95 §7.1.3.1.11
IS95_PN_I = (1 << 15) | (1 << 13) | (1 << 9) | (1 << 8) | (1 << 7) \
    | (1 << 5) | 1
IS95_PN_Q = (1 << 15) | (1 << 12) | (1 << 11) | (1 << 10) | (1 << 6) \
    | (1 << 5) | (1 << 4) | (1 << 3) | 1
# IS-95 롱코드 — 주기 2⁴²−1
IS95_LONG = ((1 << 42) | (1 << 35) | (1 << 33) | (1 << 31) | (1 << 27)
             | (1 << 26) | (1 << 25) | (1 << 22) | (1 << 21) | (1 << 19)
             | (1 << 18) | (1 << 17) | (1 << 16) | (1 << 10) | (1 << 7)
             | (1 << 6) | (1 << 5) | (1 << 3) | (1 << 2) | (1 << 1) | 1)
# WCDMA 하향 스크램블링 골드 부호의 두 생성기 — 3GPP TS 25.213 §5.2.2
WCDMA_X = (1 << 18) | (1 << 7) | 1
WCDMA_Y = (1 << 18) | (1 << 10) | (1 << 7) | (1 << 5) | 1


def lfsr_step(state, poly, m):
    """피보나치 LFSR 한 걸음. (내보낸 비트, 새 상태)."""
    out = state & 1
    fb = bin(state & (poly & ((1 << m) - 1))).count('1') & 1
    return out, (state >> 1) | (fb << (m - 1))


def m_sequence(poly, m, seed=1):
    """한 주기(2^m−1)만큼의 비트열."""
    st = seed & ((1 << m) - 1)
    if st == 0:
        raise ValueError('씨앗이 0 이면 LFSR 은 영원히 0 이다')
    out = []
    for _ in range((1 << m) - 1):
        b, st = lfsr_step(st, poly, m)
        out.append(b)
    return out


def lfsr_period(poly, m, seed=1):
    """실제로 돌려서 잰 주기. m 이 20 을 넘으면 쓰지 말 것."""
    start = seed & ((1 << m) - 1)
    st = start
    n = 0
    while True:
        _b, st = lfsr_step(st, poly, m)
        n += 1
        if st == start:
            return n
        if n > (1 << m):
            raise RuntimeError('주기를 못 찾았다 — 탭이 잘못됐다')


def bipolar(bits):
    """0 → +1, 1 → −1. 상관을 재려면 이 꼴이어야 한다."""
    return [1 - 2 * b for b in bits]


# ── 골드 부호 ─────────────────────────────────────────────────────


def gold(p1, p2, m, shift):
    """선호쌍 m-수열 둘을 어긋나게 XOR 한 부호."""
    a = m_sequence(p1, m)
    b = m_sequence(p2, m)
    n = len(a)
    return [a[i] ^ b[(i + shift) % n] for i in range(n)]


def gold_family(p1, p2, m):
    """골드 집합 — 두 m-수열과 N 개의 어긋난 XOR, 모두 N+2 개."""
    n = (1 << m) - 1
    fam = [m_sequence(p1, m), m_sequence(p2, m)]
    fam += [gold(p1, p2, m, k) for k in range(n)]
    return fam


# ── Zadoff-Chu ────────────────────────────────────────────────────


def zadoff_chu(n, u):
    """Zadoff-Chu 수열. 진폭이 늘 1 이고 순환 자기상관이 0 이다.

        홀수 N: x_u[k] = e^{−jπ u k(k+1)/N}
        짝수 N: x_u[k] = e^{−jπ u k²/N}

    이 두 성질 때문에 LTE·NR 이 동기와 임의접속에 이것을 쓴다.
    진폭이 고르면 증폭기를 최대로 밀 수 있고(PAPR 이 낮다), 자기상관이
    뾰족하면 도착 시각을 정확히 짚을 수 있다. u 는 N 과 서로소여야 한다.
    """
    if n < 1:
        raise ValueError('길이는 1 이상이어야 한다')
    if math.gcd(n, u) != 1:
        raise ValueError('근 u 는 N 과 서로소여야 한다: N=%d u=%d'
                         % (n, u))
    out = []
    for k in range(n):
        if n % 2:
            ph = -math.pi * u * k * (k + 1) / n
        else:
            ph = -math.pi * u * k * k / n
        out.append(cmath.exp(1j * ph))
    return out


def processing_gain_db(sf):
    """확산 이득 — 10·log₁₀(확산율).

    IS-95 순방향은 1.2288 Mcps 에 9.6 kbps 이므로 확산율 128,
    곧 21 dB 다.
    이 21 dB 가 '잡음보다 낮은 신호를 받아 낸다' 는 말의 실체다.
    """
    if sf <= 0:
        raise ValueError('확산율은 양수여야 한다')
    return 10.0 * math.log10(sf)
