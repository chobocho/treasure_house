# -*- coding: utf-8 -*-
"""polar — 채널 극화와 폴라 부호. 5G NR 의 제어 채널이 쓰는 부호다.

   2008년에 아르칸이 보인 것은 이렇다. 같은 채널 둘을 특별한 방법으로
   묶으면, 한쪽은 더 좋아지고 다른 쪽은 더 나빠진다. 그런데 **둘의 용량
   합은 변하지 않는다.** 이것을 되풀이하면 채널들이 '거의 완벽한 것' 과
   '거의 쓸모없는 것' 으로 갈라진다(극화). 좋은 자리에만 정보를 싣고
   나쁜 자리는 0 으로 얼리면(동결) 용량에 닿는다.

   용량 보존이 이 이야기의 전부이므로, 시험도 거기부터 확인한다.

   변환은 비트 역순을 쓰지 않는 쪽(x = u·F^{⊗n})으로 통일했다 —
   3GPP TS 38.212 §5.3.1 도 역순 치환 없이 정의한다.

   복호는 셋을 담았다.
     · SC     — 앞에서부터 하나씩 정한다. 한 번 틀리면 뒤가 다 무너진다
     · SCL    — 후보 경로를 L 개 들고 간다. 그 약점을 덜어 준다
     · CA-SCL — 목록 가운데 CRC 가 맞는 것을 고른다. NR 이 쓰는 방식
"""
import math
import random


def _check_pow2(n):
    if n < 1 or (n & (n - 1)):
        raise ValueError('N 은 2의 거듭제곱이어야 한다: %d' % n)


# ── 극화 ──────────────────────────────────────────────────────────


def capacities(n, i0):
    """N 개로 쪼갠 채널의 용량 (BEC 기준). 합은 언제나 N·I(W) 다.

        I⁻ = I²,   I⁺ = 2I − I²

    나쁜 쪽(I²)이 먼저, 좋은 쪽이 나중에 온다. 두 값을 더하면 2I 이므로
    단계마다 합이 보존되고, 끝까지 가면 N·I 가 된다. 시험이 이 항등식을
    소수점 아래 아홉 자리까지 확인한다.
    """
    _check_pow2(n)
    cur = [float(i0)]
    while len(cur) < n:
        nxt = []
        for v in cur:
            nxt.append(v * v)
            nxt.append(2.0 * v - v * v)
        cur = nxt
    return cur


def bhattacharyya(n, z0):
    """바타차리야 파라미터의 재귀. Z⁻ = 2Z − Z², Z⁺ = Z².

    Z 는 '두 입력을 헷갈릴 만한 정도' 라, 작을수록 좋은 채널이다.
    BEC 에서는 Z 가 곧 소실 확률이고 I = 1 − Z 다 — 시험이 그 관계를
    확인한다. 부호 설계(어느 자리를 얼릴지)는 이 값의 순서로 정한다.
    """
    _check_pow2(n)
    cur = [float(z0)]
    while len(cur) < n:
        nxt = []
        for v in cur:
            nxt.append(2.0 * v - v * v)
            nxt.append(v * v)
        cur = nxt
    return cur


# ── 변환 ──────────────────────────────────────────────────────────


def kronecker_generator(n):
    """F^{⊗n} 을 실제로 만들어 돌려준다 — 나비 연산을 검산하려고 둔다.

    F = [[1,0],[1,1]] 의 n 차 크로네커 거듭제곱이다. 크기가 N×N 이라
    N ≤ 256 에서만 쓸 것. 시간·공간 O(N²).
    """
    _check_pow2(n)
    g = [[1]]
    while len(g) < n:
        m = len(g)
        ng = [[0] * (2 * m) for _ in range(2 * m)]
        for i in range(m):
            for j in range(m):
                ng[i][j] = g[i][j]
                ng[i + m][j] = g[i][j]
                ng[i + m][j + m] = g[i][j]
        g = ng
    return g


def transform(u):
    """x = u·F^{⊗n} 을 나비 연산으로. 시간 O(N log N), 제자리.

    F 가 GF(2) 에서 자기 자신의 역이라 이 변환은 대합(involution)이다 —
    두 번 걸면 제자리로 돌아온다. 시험이 그것을 확인한다.
    """
    x = [b & 1 for b in u]
    n = len(x)
    _check_pow2(n)
    step = 1
    while step < n:
        for i in range(0, n, 2 * step):
            for j in range(i, i + step):
                x[j] ^= x[j + step]
        step *= 2
    return x


# ── 부호 설계 ─────────────────────────────────────────────────────


def frozen_set(n, k, design):
    """얼릴 자리의 집합. Z 가 큰(나쁜) 자리부터 N−K 개를 고른다.

    design 은 설계 소실 확률이다. 실물 NR 은 이것 대신 미리 계산된
    신뢰도 순서표(TS 38.212 표 5.3.1.2-1)를 쓴다 — 부호율과 무관하게
    한 벌이면 되도록 만든 표다. 여기서는 원리대로 그때그때 센다.
    """
    _check_pow2(n)
    if not 0 < k <= n:
        raise ValueError('K 는 1 이상 N 이하여야 한다: %d/%d' % (k, n))
    z = bhattacharyya(n, design)
    order = sorted(range(n), key=lambda i: -z[i])
    return frozenset(order[:n - k])


def encode(msg, n, frozen):
    """정보 비트를 얼지 않은 자리에 차례로 놓고 변환한다."""
    k = n - len(frozen)
    if len(msg) != k:
        raise ValueError('메시지는 %d 비트다: %d' % (k, len(msg)))
    u = [0] * n
    it = iter(msg)
    for i in range(n):
        if i not in frozen:
            u[i] = next(it) & 1
    return transform(u)


# ── 복호 ──────────────────────────────────────────────────────────


def _f(a, b):
    """상위 비트 쪽 LLR — 정확한 식으로.

    f(a,b) = 2·atanh(tanh(a/2)·tanh(b/2)) 인데, 그대로 쓰면 큰 인수에서
    자릿수를 잃는다. 아래 꼴은 같은 값이면서 넘침이 없다.
    """
    s = -1.0 if (a < 0) != (b < 0) else 1.0
    m = min(abs(a), abs(b))
    corr = (math.log1p(math.exp(-abs(a + b)))
            - math.log1p(math.exp(-abs(a - b))))
    return s * m + corr


def _g(a, b, u):
    """하위 비트 쪽 LLR. 위에서 정한 비트 u 가 부호를 정한다."""
    return b + a if u == 0 else b - a


def _sc(llr, frozen, offset, uhat):
    """SC 복호의 되부름 — 돌려주는 것은 그 부분나무의 x 영역 비트다."""
    n = len(llr)
    if n == 1:
        u = 0 if offset in frozen else (0 if llr[0] > 0 else 1)
        uhat[offset] = u
        return [u]
    h = n // 2
    a, b = llr[:h], llr[h:]
    lf = [_f(a[j], b[j]) for j in range(h)]
    x1 = _sc(lf, frozen, offset, uhat)
    lg = [_g(a[j], b[j], x1[j]) for j in range(h)]
    x2 = _sc(lg, frozen, offset + h, uhat)
    return [x1[j] ^ x2[j] for j in range(h)] + x2


def sc_decode(llr, n, frozen):
    """연속 소거(SC) 복호. 시간 O(N log N).

    앞에서부터 한 비트씩 정하고, 정한 것을 뒤 계산에 그대로 쓴다.
    그래서 한 번 틀리면 그 뒤가 줄줄이 무너진다 — SCL 이 있는 이유다.
    """
    if len(llr) != n:
        raise ValueError('LLR 길이가 N 과 다르다')
    uhat = [0] * n
    _sc(list(llr), frozen, 0, uhat)
    return [uhat[i] for i in range(n) if i not in frozen]


def _bit_llr(llr, u, i):
    """이미 정한 비트 u[0:i] 를 두고 i번 비트의 LLR 을 구한다.

    읽기 쉬운 쪽을 골랐다. 실물 SCL 은 중간 계산을 나무에 쌓아 두고
    다시 쓰지만, 여기서는 매번 되짚어 계산한다 — 비트마다 O(N log N),
    한 프레임 O(N² log N). 이 책이 다루는 N ≤ 128 에서는 충분하다.
    """
    n = len(llr)
    if n == 1:
        return llr[0]
    h = n // 2
    a, b = llr[:h], llr[h:]
    if i < h:
        lf = [_f(a[j], b[j]) for j in range(h)]
        return _bit_llr(lf, u[:i], i)
    x1 = transform(u[:h])
    lg = [_g(a[j], b[j], x1[j]) for j in range(h)]
    return _bit_llr(lg, u[h:i], i - h)


def scl_decode(llr, n, frozen, listsize, crc_name=None):
    """목록 복호(SCL). 후보 경로를 L 개까지 들고 끝까지 간다.

    경로 값(path metric)은 '지금까지의 선택이 얼마나 억지스러웠나' 다.
    LLR 이 가리키는 쪽을 고르면 0 에 가깝고, 거스르면 |LLR| 만큼
    쌓인다. 끝에서 값이 가장 작은 경로를 고른다.

    crc_name 을 주면 CRC 가 맞는 경로 가운데서 고른다. NR 이 이렇게
    한다 — 목록 안에 정답이 있는데도 값이 가장 작은 것이 정답이
    아닌 일이 잦기 때문이다.
    """
    if len(llr) != n:
        raise ValueError('LLR 길이가 N 과 다르다')
    llr = list(llr)
    paths = [([], 0.0)]                    # (u 비트들, 경로 값)
    for i in range(n):
        nxt = []
        for u, pm in paths:
            v = _bit_llr(llr, u, i)
            if i in frozen:
                pen = 0.0 if v > 0 else abs(v)
                nxt.append((u + [0], pm + pen))
            else:
                for bit in (0, 1):
                    agree = (v > 0) == (bit == 0)
                    pen = 0.0 if agree else abs(v)
                    nxt.append((u + [bit], pm + pen))
        nxt.sort(key=lambda t: t[1])
        paths = nxt[:listsize]
    infos = [[u[j] for j in range(n) if j not in frozen]
             for u, _pm in paths]
    if crc_name:
        from wirelesslib import codes
        for info in infos:
            if codes.crc_check(info, crc_name):
                return info
    return infos[0]


# ── 성능 재기 ─────────────────────────────────────────────────────


def bler(n, k, ebn0_db, frames, listsize=1, seed=1, crc_name=None):
    """블록 오류율. crc_name 을 주면 그만큼 정보 비트가 줄어든다.

    부호율은 K/N 이다(CRC 를 붙이면 실제 정보는 K−L 비트지만, 잡음을
    맞추는 데 쓰는 부호율은 전송하는 비트로 센다).
    """
    from wirelesslib import codes
    fz = frozen_set(n, k, 0.5)
    rnd = random.Random(seed)
    rate = float(k) / n
    esn0 = 10.0 ** ((ebn0_db + 10.0 * math.log10(rate)) / 10.0)
    sigma2 = 1.0 / (2.0 * esn0)
    sd = math.sqrt(sigma2)
    bad = 0
    for _ in range(frames):
        if crc_name:
            body = [rnd.getrandbits(1)
                    for _ in range(k - codes.crc_len(crc_name))]
            msg = codes.crc_append(body, crc_name)
        else:
            msg = [rnd.getrandbits(1) for _ in range(k)]
        x = encode(msg, n, fz)
        y = [2.0 * ((1.0 - 2.0 * b) + rnd.gauss(0.0, sd)) / sigma2
             for b in x]
        if listsize <= 1:
            got = sc_decode(y, n, fz)
        else:
            got = scl_decode(y, n, fz, listsize, crc_name)
        if got != msg:
            bad += 1
    return bad / float(frames)
