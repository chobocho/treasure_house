# -*- coding: utf-8 -*-
"""turbo — LTE 의 병렬 연접 부호와 BCJR 반복 복호.

   1993년에 터보 부호가 나오기 전까지, 섀넌 한계에서 2~3 dB 안쪽은
   닿을 수 없는 곳이었다. 여기 있는 것은 그 0.5 dB 를 만든 두 생각이다.

     1. **되먹임 조직 부호(RSC)를 둘, 사이에 인터리버.** 한쪽 부호기가
        약하게 보호한 자리를 다른 쪽은 전혀 다른 순서로 본다.
     2. **연판정을 주고받는 반복 복호.** 복호기 둘이 서로에게 "나는
        이 비트가 0 쪽인 것 같다" 는 정도를 넘겨 주고, 넘겨받은 쪽은
        자기가 이미 아는 부분을 빼고(외재 정보) 다시 센다.

   구성 부호는 3GPP TS 36.212 §5.1.3.2 의 8상태 부호다.

       g₀(D) = 1 + D² + D³ (되먹임),  g₁(D) = 1 + D + D³

   인터리버는 같은 절의 QPP — Π(i) = (f₁·i + f₂·i²) mod K.
   덧셈과 곱셈만으로 자리를 계산하므로 표를 들고 다닐 필요가 없고,
   병렬 복호기가 충돌 없이 메모리를 나눠 쓸 수 있다.
"""
import math
import random

# 상태는 (s1, s2, s3) 를 (s1<<2)|(s2<<1)|s3 로 담은 0~7 이다.
NSTATE = 8


def _step(state, u):
    """RSC 한 걸음. (다음 상태, 패리티) 를 돌려준다."""
    s1 = (state >> 2) & 1
    s2 = (state >> 1) & 1
    s3 = state & 1
    a = u ^ s2 ^ s3          # 되먹임 g₀ = 1 + D² + D³
    p = a ^ s1 ^ s3          # 앞먹임 g₁ = 1 + D + D³
    return ((a << 2) | (s1 << 1) | s2), p


# (상태, 입력) → (다음 상태, 패리티) 를 미리 펴 둔다.
TRELLIS = [[_step(s, u) for u in (0, 1)] for s in range(NSTATE)]


def rsc_encode(bits):
    """(계통 비트, 패리티, 꼬리 6비트).

    꼬리는 되먹임 값을 그대로 입력에 넣어 상태를 0 으로 되돌린 것이다.
    비되먹임 부호처럼 0 을 넣으면 안 된다 — 되먹임 때문에 0 을 넣어도
    상태가 0 으로 가지 않는다. 터보 부호를 처음 짤 때 가장 흔히
    물리는 자리다.
    """
    st = 0
    par = []
    for u in bits:
        ns, p = TRELLIS[st][u & 1]
        par.append(p)
        st = ns
    tail = []
    for _ in range(3):
        s2 = (st >> 1) & 1
        s3 = st & 1
        u = s2 ^ s3          # 이렇게 넣어야 되먹임 a 가 0 이 된다
        ns, p = TRELLIS[st][u]
        tail.extend([u, p])
        st = ns
    return list(bits), par, tail


def rsc_final_state(bits, tail):
    """꼬리까지 넣고 난 뒤의 상태.

    0 이어야 끝맺음이 제대로 된 것이다.
    """
    st = 0
    for u in bits:
        st = TRELLIS[st][u & 1][0]
    for i in range(0, len(tail), 2):
        st = TRELLIS[st][tail[i] & 1][0]
    return st


# ── QPP 인터리버 ──────────────────────────────────────────────────


def qpp(k, f1, f2):
    """Π(i) = (f₁·i + f₂·i²) mod K. 순열이 아니면 예외.

    순열 조건을 이론으로 따지는 대신 실제로 전단사인지 세어 본다 —
    O(K) 면 되고, 틀린 매개변수를 조용히 넘기지 않는다.
    """
    perm = [(f1 * i + f2 * i * i) % k for i in range(k)]
    if len(set(perm)) != k:
        raise ValueError('QPP 가 순열이 아니다: K=%d f1=%d f2=%d'
                         % (k, f1, f2))
    return perm


def apply_perm(x, perm):
    """y[i] = x[Π(i)]."""
    return [x[p] for p in perm]


def undo_perm(y, perm):
    out = [None] * len(y)
    for i, p in enumerate(perm):
        out[p] = y[i]
    return out


# ── 부호기 ────────────────────────────────────────────────────────


def encode(bits, f1, f2):
    """LTE 터보 부호기. 길이는 정확히 3K + 12 다.

    차례는 [계통 K] [패리티1 K] [패리티2 K] [꼬리1 6] [꼬리2 6] 이다.
    실물 LTE 는 여기에 레이트 매칭(9번 모듈 harq)이 붙어 차례가
    다시 섞이지만, 부호 자체를 보여 주는 데는 이 차례가 읽기 좋다.
    """
    k = len(bits)
    perm = qpp(k, f1, f2)
    sysb, p1, t1 = rsc_encode(bits)
    _s2, p2, t2 = rsc_encode(apply_perm(bits, perm))
    return sysb + p1 + p2 + t1 + t2


# ── BCJR ──────────────────────────────────────────────────────────

NEG = -1e30


def _maxstar(a, b, maxlog):
    """log(e^a + e^b). maxlog 면 max 로 갈음한다.

    보정항 log(1+e^{−|a−b|}) 이 있고 없고의 차이가 곧 log-MAP 과
    max-log-MAP 의 차이다. 0.2~0.5 dB 쯤 된다 — 실물 복호기는
    이 보정을 표로 어림하거나 그냥 버린다.
    """
    if maxlog:
        return a if a > b else b
    if a > b:
        return a + math.log1p(math.exp(b - a))
    return b + math.log1p(math.exp(a - b))


def bcjr(la, lsys, lpar, maxlog=False):
    """한 구성 부호의 BCJR. 사후 LLR 목록을 돌려준다.

    la 는 앞 단계 복호기가 넘겨준 사전 정보(외재 정보)다. 길이는
    lsys·lpar 과 같아야 하고, 꼬리 구간에서는 0 이다 — 꼬리 비트에
    대해서는 상대 복호기가 아무 말도 해 줄 수 없기 때문이다.

    시간 O(T·8), 공간 O(T·8).
    """
    t = len(lsys)
    alpha = [[NEG] * NSTATE for _ in range(t + 1)]
    beta = [[NEG] * NSTATE for _ in range(t + 1)]
    alpha[0][0] = 0.0
    beta[t][0] = 0.0                     # 끝맺음한 부호라 끝은 0 상태다

    def gamma(i, s, u):
        ns, p = TRELLIS[s][u]
        gu = 1.0 - 2.0 * u
        gp = 1.0 - 2.0 * p
        return 0.5 * gu * (la[i] + lsys[i]) + 0.5 * gp * lpar[i]

    for i in range(t):
        for s in range(NSTATE):
            if alpha[i][s] <= NEG:
                continue
            for u in (0, 1):
                ns = TRELLIS[s][u][0]
                v = alpha[i][s] + gamma(i, s, u)
                alpha[i + 1][ns] = _maxstar(alpha[i + 1][ns], v, maxlog)
    for i in range(t - 1, -1, -1):
        for s in range(NSTATE):
            acc = NEG
            for u in (0, 1):
                ns = TRELLIS[s][u][0]
                if beta[i + 1][ns] <= NEG:
                    continue
                acc = _maxstar(acc, beta[i + 1][ns] + gamma(i, s, u),
                               maxlog)
            beta[i][s] = acc

    out = []
    for i in range(t):
        n0 = n1 = NEG
        for s in range(NSTATE):
            if alpha[i][s] <= NEG:
                continue
            for u in (0, 1):
                ns = TRELLIS[s][u][0]
                if beta[i + 1][ns] <= NEG:
                    continue
                v = alpha[i][s] + gamma(i, s, u) + beta[i + 1][ns]
                if u:
                    n1 = _maxstar(n1, v, maxlog)
                else:
                    n0 = _maxstar(n0, v, maxlog)
        out.append(n0 - n1)
    return out


# ── 반복 복호 ─────────────────────────────────────────────────────


def _channel_llr(bits, ebn0_db, k, rnd):
    """BPSK·AWGN 을 지나온 채널 LLR. 양수면 0 쪽이 그럴듯하다는 뜻.

    Eb 는 **정보 비트당** 에너지다. 부호율이 R 이면 심볼당 에너지는
    R 배가 된다 — 이 한 줄을 빠뜨리면 터보 부호가 실제보다 3~5 dB
    좋아 보인다.
    """
    n = len(bits)
    rate = float(k) / n
    esn0 = 10.0 ** ((ebn0_db + 10.0 * math.log10(rate)) / 10.0)
    sigma2 = 1.0 / (2.0 * esn0)
    sd = math.sqrt(sigma2)
    out = []
    for b in bits:
        x = 1.0 - 2.0 * b                # 0 → +1, 1 → −1
        y = x + rnd.gauss(0.0, sd)
        out.append(2.0 * y / sigma2)
    return out


def _decode_llr(llr, k, perm, iters, maxlog):
    """반복마다의 경판정 목록.

    반복이 얼마나 벌어 주는지를 재려면 중간 결과가 있어야 한다.
    """
    zero = [0.0] * 3
    ls = llr[:k]
    lp1 = llr[k:2 * k]
    lp2 = llr[2 * k:3 * k]
    t1 = llr[3 * k:3 * k + 6]
    t2 = llr[3 * k + 6:3 * k + 12]
    # 꼬리 구간의 계통·패리티 LLR 을 갈라 놓는다
    ts1 = [t1[0], t1[2], t1[4]]
    tp1 = [t1[1], t1[3], t1[5]]
    ts2 = [t2[0], t2[2], t2[4]]
    tp2 = [t2[1], t2[3], t2[5]]

    ls1 = ls + ts1
    lpa1 = lp1 + tp1
    lsi = apply_perm(ls, perm) + ts2
    lpa2 = lp2 + tp2

    ext = [0.0] * k
    outs = []
    for _ in range(iters):
        la1 = ext + list(zero)
        l1 = bcjr(la1, ls1, lpa1, maxlog)
        e1 = [l1[i] - la1[i] - ls1[i] for i in range(k)]

        la2 = apply_perm(e1, perm) + list(zero)
        l2 = bcjr(la2, lsi, lpa2, maxlog)
        e2 = [l2[i] - la2[i] - lsi[i] for i in range(k)]
        ext = undo_perm(e2, perm)

        total = undo_perm([l2[i] for i in range(k)], perm)
        outs.append([0 if v > 0 else 1 for v in total])
    return outs


def decode(bits, f1, f2, ebn0_db, iters, seed=1, maxlog=False):
    """부호화 → 잡음 → 반복 복호까지 한 번에.

    복호된 메시지를 돌려준다.
    """
    k = len(bits)
    perm = qpp(k, f1, f2)
    y = encode(bits, f1, f2)
    rnd = random.Random(seed)
    llr = _channel_llr(y, ebn0_db, k, rnd)
    return _decode_llr(llr, k, perm, iters, maxlog)[-1]


def ber_vs_iters(ebn0_db, iters, frames, k, f1, f2, seed=1,
                 maxlog=False):
    """반복 횟수마다의 BER. 목록의 i번째가 (i+1)회 반복한 결과다.

    이 목록이 단조 감소하지 않으면 무언가 잘못된 것이다 — 외재 정보의
    부호를 뒤집었거나, 사전 정보를 빼지 않고 되돌려 주고 있거나.
    """
    rnd = random.Random(seed)
    perm = qpp(k, f1, f2)
    err = [0] * iters
    for _ in range(frames):
        msg = [rnd.getrandbits(1) for _ in range(k)]
        y = encode(msg, f1, f2)
        llr = _channel_llr(y, ebn0_db, k, rnd)
        for i, got in enumerate(_decode_llr(llr, k, perm, iters,
                                            maxlog)):
            err[i] += sum(1 for a, b in zip(msg, got) if a != b)
    return [e / float(frames * k) for e in err]
