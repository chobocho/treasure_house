# -*- coding: utf-8 -*-
"""ofdm — 직교 주파수 분할 다중화와 NR 뉴머롤로지.

   OFDM 의 약속은 하나다. **부반송파끼리 서로 간섭하지 않는다.**
   그 근거는 적분 한 줄이다 — 유용 심볼 구간 T 안에서 두 복소 정현파는

       ∫₀^T e^{j2π(k−l)t/T} dt = 0  (k ≠ l)

   이므로, 부반송파 간격이 정확히 1/T 이면 서로 직교한다. 그래서
   IFFT 한 번이 곧 변조기다.

   그런데 이 약속은 공짜가 아니라 **조건부** 다.

     · 다중경로가 심볼 경계를 넘으면 직교가 깨진다 → 순환 전치(CP).
       CP 가 지연 확산보다 길면 채널이 한 탭 곱셈으로 줄어든다.
     · 주파수가 어긋나면 직교가 깨진다 → 부반송파 사이 간섭(ICI).
       작은 오차 ε 에 대해 ICI 전력은 대략 (πε)²/3 이다.
     · 여러 정현파가 우연히 겹치면 첨두가 치솟는다 → PAPR.
       그래서 LTE 상향은 DFT 를 한 번 더 도는 SC-FDMA 를 쓴다.

   뒤쪽 절반은 NR 뉴머롤로지의 산술이다. SCS = 15·2^μ kHz 하나로
   슬롯 길이·심볼 길이·PRB 폭이 전부 따라 나온다.
"""
import cmath
import math
import random

from wirelesslib import dsp


# ── 변·복조 ───────────────────────────────────────────────────────


def modulate(syms, nfft, ncp):
    """부반송파 심볼 → 시간 표본. IFFT 뒤에 꼬리를 앞에 붙인다.

    CP 는 심볼의 **끝** 을 잘라 앞에 붙인 것이다. 그래야 채널과의
    선형 컨볼루션이 순환 컨볼루션과 같아지고, 주파수 영역에서 곱셈
    하나로 바뀐다. 0 을 채우면 안 되는 이유가 이것이다.
    """
    if len(syms) != nfft:
        raise ValueError('심볼 수가 FFT 크기와 다르다')
    t = dsp.ifft(list(syms))
    return t[nfft - ncp:] + t


def demodulate(x, nfft, ncp):
    """CP 를 떼고 FFT. modulate 의 정확한 역이다."""
    if len(x) != nfft + ncp:
        raise ValueError('표본 수가 맞지 않는다')
    return dsp.fft(x[ncp:])


def cp_overhead(nfft, ncp):
    """CP 가 잡아먹는 비율. NR 정상 CP 는 약 7 % 다."""
    return float(ncp) / (nfft + ncp)


def multipath_error(nfft, ncp, taps):
    """다중경로를 지나 한 탭 등화까지 한 뒤 남는 오차의 최댓값.

    CP 가 가장 긴 지연보다 길면 이 값이 0 이 된다 — 다중경로가
    부반송파마다 복소수 하나의 곱셈으로 줄어든다는 뜻이다.
    CP 가 짧으면 심볼 간 간섭이 남아 0 이 아니게 된다.
    """
    rnd = random.Random(20260916)
    syms = [complex(1 - 2 * rnd.getrandbits(1),
                    1 - 2 * rnd.getrandbits(1)) for _ in range(nfft)]
    x = modulate(syms, nfft, ncp)
    # 앞 심볼의 꼬리가 넘어오는 것까지 보려면 두 심볼을 이어 보낸다
    prev = modulate([complex(1 - 2 * rnd.getrandbits(1),
                             1 - 2 * rnd.getrandbits(1))
                     for _ in range(nfft)], nfft, ncp)
    stream = prev + x
    h = [0j] * (max(d for d, _a in taps) + 1)
    for d, a in taps:
        h[d] = complex(a, 0.0)
    y = dsp.conv(stream, h)
    seg = y[len(prev):len(prev) + nfft + ncp]
    got = demodulate(seg, nfft, ncp)
    hf = dsp.fft(h + [0j] * (nfft - len(h)))
    worst = 0.0
    for k in range(nfft):
        eq = got[k] / hf[k]
        worst = max(worst, abs(eq - syms[k]))
    return worst


def ici_power(nfft, eps):
    """부반송파 하나가 받는 간섭 전력. eps 는 부반송파 간격 대비 오차.

    반송파 주파수가 ε 만큼 어긋나면 직교 적분이 0 이 되지 않는다.
    남는 양을 전부 더한 것이 ICI 다. 작은 ε 에서 (πε)²/3 에 가깝다 —
    시험이 그 근사와 맞대어 본다.

    이 값이 뉴머롤로지 선택의 뿌리다. 고속 이동이나 높은 반송파에서
    도플러가 커지면, 부반송파 간격을 넓혀 ε 를 줄이는 수밖에 없다.
    """
    if eps == 0:
        return 0.0
    sig = 0.0
    inter = 0.0
    for k in range(nfft):
        # 부반송파 k 가 관심 부반송파 0 에 남기는 몫
        d = k + eps
        if abs(d) < 1e-12:
            a = 1.0
        else:
            a = abs(math.sin(math.pi * d) / (nfft * math.sin(
                math.pi * d / nfft)))
        if k == 0:
            sig = a * a
        else:
            inter += a * a
    return inter / sig


# ── PAPR ──────────────────────────────────────────────────────────


def papr_db(x):
    """첨두 대 평균 전력비 [dB].

    증폭기를 얼마나 물려 놓아야 하는지가 이 값으로 정해진다.
    """
    if not x:
        raise ValueError('빈 신호')
    peak = max(abs(v) ** 2 for v in x)
    mean = sum(abs(v) ** 2 for v in x) / len(x)
    return 10.0 * math.log10(peak / mean)


def _random_qpsk(n, rnd):
    s = 1.0 / math.sqrt(2.0)
    return [complex(s * (1 - 2 * rnd.getrandbits(1)),
                    s * (1 - 2 * rnd.getrandbits(1)))
            for _ in range(n)]


def _one_symbol(nfft, rnd, scfdma, m=None):
    if not scfdma:
        return dsp.ifft(_random_qpsk(nfft, rnd))
    m = m or nfft // 4
    d = dsp.any_dft(_random_qpsk(m, rnd))
    grid = [0j] * nfft
    for i in range(m):
        grid[i] = d[i]
    return dsp.ifft(grid)


def mean_papr_db(nfft, trials, seed=1, scfdma=False):
    """여러 심볼의 PAPR 평균. 부반송파가 많을수록 커진다."""
    rnd = random.Random(seed)
    tot = 0.0
    for _ in range(trials):
        tot += papr_db(_one_symbol(nfft, rnd, scfdma))
    return tot / trials


def papr_ccdf(nfft, levels, trials, seed=1, scfdma=False):
    """PAPR 이 각 문턱을 넘을 확률 — 증폭기 설계가 보는 곡선."""
    rnd = random.Random(seed)
    vals = [papr_db(_one_symbol(nfft, rnd, scfdma))
            for _ in range(trials)]
    return [sum(1 for v in vals if v > lv) / float(trials)
            for lv in levels]


# ── SC-FDMA ───────────────────────────────────────────────────────


def scfdma_modulate(syms, nfft, ncp, offset):
    """DFT 확산 OFDM. 심볼을 먼저 DFT 로 펴서 부반송파에 얹는다.

    한 심볼이 배정된 모든 부반송파에 퍼지므로 시간 파형이 단일 반송파에
    가까워진다 — 그래서 PAPR 이 낮다. 단말의 전력 증폭기가 값싸고
    배터리가 오래 가는 대가로, 주파수 배정이 연속이어야 한다는 제약이
    붙는다. LTE 상향이 이 맞바꿈을 택했다.
    """
    m = len(syms)
    if m < 1 or m > nfft:
        raise ValueError('DFT 크기는 1 이상 FFT 크기 이하여야 한다')
    # LTE 의 DFT 크기는 2^a·3^b·5^c 다(12의 배수, 곧 PRB 단위).
    # 2의 거듭제곱이 아니어도 돌아야 하므로 any_dft 를 쓴다.
    d = dsp.any_dft(list(syms))
    grid = [0j] * nfft
    for i in range(m):
        grid[(offset + i) % nfft] = d[i]
    return modulate(grid, nfft, ncp)


def scfdma_demodulate(x, nfft, ncp, offset, m):
    grid = demodulate(x, nfft, ncp)
    d = [grid[(offset + i) % nfft] for i in range(m)]
    return dsp.any_idft(d)


# ── NR 뉴머롤로지 ─────────────────────────────────────────────────
#
# 3GPP TS 38.211 §4.2·§4.3 — μ 하나로 나머지가 전부 정해진다.
MAX_MU = 6


def _check_mu(mu):
    if not 0 <= mu <= MAX_MU:
        raise ValueError('μ 는 0~%d 다: %s' % (MAX_MU, mu))


def scs_khz(mu):
    """부반송파 간격 = 15 · 2^μ kHz."""
    _check_mu(mu)
    return 15 * (1 << mu)


def slot_ms(mu):
    """슬롯 길이 = 1 ms / 2^μ.

    서브프레임(1 ms)과 프레임(10 ms)은 μ 와 무관하게 고정이고, 그 안에
    들어가는 슬롯의 수만 2^μ 배로 는다. LTE 와 시간축을 맞춰 두려는
    설계다 — 그래서 NR 과 LTE 가 같은 대역에서 공존할 수 있다.
    """
    _check_mu(mu)
    return 1.0 / (1 << mu)


def slots_per_subframe(mu):
    _check_mu(mu)
    return 1 << mu


def symbols_per_slot(cp='normal'):
    """정상 CP 는 14 심볼, 확장 CP 는 12 심볼."""
    if cp == 'normal':
        return 14
    if cp == 'extended':
        return 12
    raise ValueError('CP 는 normal 이나 extended 다: %s' % cp)


def extended_cp_allowed(mu):
    """확장 CP 는 μ=2(60 kHz)에서만 쓴다 — TS 38.211 표 4.3.2-1."""
    _check_mu(mu)
    return mu == 2


def useful_symbol_us(mu):
    """유용 심볼 길이 [μs] = 1 / SCS. 직교 조건이 곧 이 관계다."""
    return 1000.0 / scs_khz(mu)


def prb_khz(mu):
    """자원 블록의 폭 — 부반송파 12개. LTE(μ=0)에서 180 kHz 다."""
    return 12.0 * scs_khz(mu)


def re_per_prb(cp='normal'):
    """한 슬롯·한 PRB 안의 자원 요소 수."""
    return 12 * symbols_per_slot(cp)
