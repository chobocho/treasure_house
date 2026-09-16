# -*- coding: utf-8 -*-
"""dsp — 이 책이 쓰는 신호 처리의 바닥.

   여기 있는 것은 넷이다.

     · DFT 와 그 빠른 판(radix-2 FFT) — OFDM 이 곧 IFFT/FFT 다
     · 선형 컨볼루션 — 채널도, 정합 필터도, 부호기도 컨볼루션이다
     · 펄스 성형(상승 코사인과 그 제곱근) — 나이퀴스트 조건의 실물
     · 표본율 바꾸기와 주기도(periodogram)

   numpy 가 없는 기계다. 그래서 복소수 리스트로 직접 짠다. 느리지만
   이 책의 시뮬레이션 크기(N ≤ 4096)에서는 충분하다.
"""
import cmath
import math

# 이 파일의 모든 신호는 '복소수 리스트' 다. 실수 신호도 complex 로 올려
# 다룬다 — 기저대역 등가 표현에서는 어차피 복소수이고, 형을 하나로 두면
# 함수마다 분기가 사라진다.


def is_pow2(n):
    return n > 0 and (n & (n - 1)) == 0


def next_pow2(n):
    """n 이상인 가장 작은 2의 거듭제곱. O(log n)."""
    p = 1
    while p < n:
        p *= 2
    return p


def dft(x):
    """정의 그대로의 DFT. O(N²).

    빠르지 않다. 여기 있는 이유는 하나 — FFT 가 맞는지 견주기 위해서다.
    시험(tests/test_dsp.py)이 둘을 1e-9 안에서 맞대어 본다.
    """
    n = len(x)
    out = []
    for k in range(n):
        s = 0j
        for i, v in enumerate(x):
            s += v * cmath.exp(-2j * math.pi * k * i / n)
        out.append(s)
    return out


def idft(X):
    """정의 그대로의 역 DFT. O(N²).

    길이가 2의 거듭제곱이 아닐 때 쓴다 — LTE 의 SC-FDMA 는 DFT 크기가
    2^a·3^b·5^c 라 72·180 같은 값이 나온다. 이 책에서 그런 크기를
    다루는 곳은 SC-FDMA 하나뿐이라 느린 쪽으로 충분하다.
    """
    n = len(X)
    out = []
    for i in range(n):
        s = 0j
        for k, v in enumerate(X):
            s += v * cmath.exp(2j * math.pi * k * i / n)
        out.append(s / n)
    return out


def any_dft(x):
    """길이에 상관없이 DFT. 2의 거듭제곱이면 FFT 로 간다."""
    return fft(x) if is_pow2(len(x)) else dft(x)


def any_idft(X):
    """any_dft 의 역."""
    return ifft(X) if is_pow2(len(X)) else idft(X)


def fft(x):
    """radix-2 쿨리-튜키 FFT (제자리 반복형).

    시간 O(N log N), 여분 공간 O(N).

    되부름 대신 반복으로 짠 이유: 파이썬의 되부름은 깊이 제한이 있고
    프레임 비용이 커서, N=4096 에서 눈에 띄게 느려진다.
    """
    n = len(x)
    if n == 0:
        return []
    if not is_pow2(n):
        raise ValueError('FFT 길이는 2의 거듭제곱이어야 한다: %d' % n)
    a = [complex(v) for v in x]

    # 1) 비트 뒤집기 순서로 자리를 바꾼다
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    # 2) 나비 연산 — 길이 2 부터 두 배씩
    size = 2
    while size <= n:
        ang = -2j * math.pi / size
        step = cmath.exp(ang)
        half = size // 2
        for start in range(0, n, size):
            w = 1 + 0j
            for k in range(half):
                u = a[start + k]
                t = w * a[start + k + half]
                a[start + k] = u + t
                a[start + k + half] = u - t
                w *= step
        size *= 2
    return a


def ifft(X):
    """역 FFT. conj → FFT → conj → 1/N 이라는 흔한 요령을 쓴다."""
    n = len(X)
    if n == 0:
        return []
    y = fft([v.conjugate() for v in X])
    return [v.conjugate() / n for v in y]


def conv(a, b):
    """선형 컨볼루션. 길이 len(a)+len(b)-1. O(len(a)·len(b)).

    FFT 로 하면 더 빠르지만, 이 책에서 컨볼루션을 쓰는 자리(필터 탭,
    부호기, 짧은 다중경로)는 한쪽이 짧아서 직접 도는 쪽이 오히려 빠르고
    무엇보다 읽기 쉽다. 큰 것이 필요하면 fft 를 직접 부르면 된다.
    """
    if not a or not b:
        return []
    out = [0 * (a[0] * b[0])] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        if av == 0:
            continue
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


def _sinc(t):
    """정규화 sinc — sin(πt)/(πt), t=0 에서 1."""
    if t == 0:
        return 1.0
    return math.sin(math.pi * t) / (math.pi * t)


def rc(beta, sps, span):
    """상승 코사인 펄스. 꼭대기가 1 이고 심볼 순간마다 0 이다.

    h(t) = sinc(t/T) · cos(πβt/T) / (1 − (2βt/T)²)

    sps 는 심볼당 표본 수, span 은 몇 심볼 길이로 자를지다. 탭 수는
    span·sps + 1 이라 한가운데가 정확히 t=0 이 된다 — 짝수 길이로 두면
    "심볼 순간" 이 표본 사이에 놓여 나이퀴스트 검사를 못 한다.

    에너지를 1 로 맞추지 않는다. 이 함수는 '나이퀴스트 조건이 이렇게
    생겼다' 를 보여 주는 쪽이고, 실제로 쓰는 것은 rrc 다.
    """
    n = span * sps
    out = []
    for i in range(n + 1):
        t = (i - n / 2.0) / sps
        den = 1.0 - (2.0 * beta * t) ** 2
        if beta > 0 and abs(den) < 1e-12:
            # t = ±T/(2β) 의 0/0 — 로피탈로 구한 극한값
            out.append(math.pi / 4.0 * _sinc(1.0 / (2.0 * beta)))
        else:
            out.append(_sinc(t) * math.cos(math.pi * beta * t) / den)
    return out


def rrc(beta, sps, span):
    """상승 코사인의 제곱근(RRC). 에너지를 1 로 맞춰 돌려준다.

    송신기와 수신기가 이것을 하나씩 쓰면 둘을 이은 것이 상승 코사인이
    된다 — 그래서 ISI 가 0 이면서 동시에 정합 필터다. 이 책의 모든
    단일 반송파 링크가 이 쌍을 쓴다.

    t=0 과 t=±T/(4β) 에서 식이 0/0 이 되므로 극한값을 따로 넣는다.
    """
    n = span * sps
    out = []
    for i in range(n + 1):
        t = (i - n / 2.0) / sps
        if t == 0:
            v = 1.0 + beta * (4.0 / math.pi - 1.0)
        elif beta > 0 and abs(abs(t) - 1.0 / (4.0 * beta)) < 1e-12:
            v = (beta / math.sqrt(2.0)) * (
                (1.0 + 2.0 / math.pi) * math.sin(math.pi / (4.0 * beta))
                + (1.0 - 2.0 / math.pi)
                * math.cos(math.pi / (4.0 * beta)))
        else:
            num = (math.sin(math.pi * t * (1.0 - beta))
                   + 4.0 * beta * t
                   * math.cos(math.pi * t * (1.0 + beta)))
            den = math.pi * t * (1.0 - (4.0 * beta * t) ** 2)
            v = num / den
        out.append(v)
    e = math.sqrt(sum(v * v for v in out))
    return [v / e for v in out]


def upsample(x, n):
    """표본 사이에 0 을 n−1 개씩 넣는다.

    심볼을 성형 필터에 먹이는 방법이 바로 이것이다.
    """
    if n < 1:
        raise ValueError('배율은 1 이상이어야 한다: %d' % n)
    out = []
    zero = 0 * x[0] if x else 0
    for v in x:
        out.append(v)
        out.extend([zero] * (n - 1))
    return out


def downsample(x, n, phase=0):
    """n 개마다 하나씩 고른다.

    심볼 순간에서 표본을 고르는 일이 곧 이것이다.
    """
    if n < 1:
        raise ValueError('배율은 1 이상이어야 한다: %d' % n)
    return x[phase::n]


def periodogram(x, nfft=None):
    """주기도 — |X[k]|² / N². 합에 N 을 곱하면 시간 영역 에너지가 된다.

    창(window)을 걸지 않은 날것이다. 이 책에서 주기도를 쓰는 자리는
    'OFDM 스펙트럼이 이렇게 생겼다'·'PAPR 을 재기 전에 신호를 본다'
    정도라, 창을 걸면 오히려 설명이 늘어난다.
    """
    n = nfft or next_pow2(len(x))
    a = [complex(v) for v in x] + [0j] * (n - len(x))
    X = fft(a)
    return [abs(v) ** 2 / (n * n) for v in X]
