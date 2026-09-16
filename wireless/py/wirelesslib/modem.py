# -*- coding: utf-8 -*-
"""modem — 성상도·변조·AWGN·복조, 그리고 오류율.

   이 책에서 가장 자주 되부르는 모듈이다. 2부의 BER 곡선도, 6부의 GMSK
   비교도, 10·11부의 MCS 표도 결국 여기서 나온 숫자를 쓴다.

   세 가지 약속을 지킨다.

     1. 모든 성상도는 **평균 에너지가 1** 이다. 그래야 Es/N0 와 Eb/N0 가
        표기 그대로 뜻을 갖는다.
     2. 모든 라벨은 **그레이 사상** 이다 — 가장 가까운 이웃끼리 비트가
        하나만 다르다. 시험이 이것을 성상도마다 확인한다.
     3. 비트 차례는 **MSB 먼저** 다. k비트 묶음의 첫 비트가 라벨의
        최상위 비트가 된다. 부호기·복호기와 맞물릴 때 이 약속이 흔들리면
        LLR 부호가 통째로 뒤집힌다.
"""
import math
import random

# ── Q 함수 ────────────────────────────────────────────────────────


def qfunc(x):
    """Q(x) = 1/√(2π) ∫_x^∞ e^{−t²/2} dt = ½ erfc(x/√2).

    math.erfc 가 표준 라이브러리에 있다. 급수를 손으로 짜지 않는 이유는
    erfc 가 꼬리(x > 5)에서도 상대 정확도를 지키기 때문이다 — 직접 짠
    급수는 거기서 자릿수를 잃는다.
    """
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def db2lin(db):
    return 10.0 ** (db / 10.0)


def lin2db(v):
    return 10.0 * math.log10(v)


def shannon_limit_db():
    """부호가 있어도 넘을 수 없는 Eb/N0 의 바닥 — 10·log₁₀(ln 2) dB.

    대역폭을 무한히 넓혀 스펙트럼 효율을 0 으로 보내면 섀넌 용량식이
    Eb/N0 → ln 2 로 수렴한다. 2부에서 유도한다.
    """
    return lin2db(math.log(2.0))


# ── 성상도 ────────────────────────────────────────────────────────


def _gray(i):
    """이진수 i 를 그레이 부호로. 이웃한 i 끼리 비트가 하나만 다르다."""
    return i ^ (i >> 1)


def _ungray(g, k):
    """그레이 부호를 되돌린다 — _gray 의 역함수.

    자리(position)에 붙는 라벨이 _gray(자리) 여야 이웃한 자리끼리 비트가
    하나만 다르다. 그러니 라벨에서 자리를 찾으려면 이 역함수가 필요하다.

    **_gray 를 역함수 대신 쓰면 안 된다.** 두 비트짜리(16QAM·QPSK)에서는
    _gray 가 우연히 자기 역함수라서 맞아 보이지만, 세 비트부터는
    어긋난다. 실제로 그렇게 짰다가 64QAM 의 BER 이 이론보다 14 %
    높게 나왔다.
    """
    b = g
    sh = 1
    while sh < k:
        b ^= b >> sh
        sh <<= 1
    return b


class Constellation(object):
    """points[b] 는 비트 라벨이 정수 b 인 점이다.

    라벨을 첨자로 쓰면 변조가 그냥 색인 참조가 된다 — 사상표를 따로
    들고 다니다 어긋나는 사고가 아예 생기지 않는다.
    """

    def __init__(self, name, k, points):
        self.name = name
        self.k = k
        self.m = 1 << k
        self.points = points
        self.labels = list(range(self.m))
        assert len(points) == self.m

    def __repr__(self):
        return '<Constellation %s k=%d>' % (self.name, self.k)


def _psk_points(k):
    """M-PSK — 라벨을 그레이로 풀어 각도 자리를 정한다."""
    m = 1 << k
    out = [0j] * m
    for label in range(m):
        pos = _ungray(label, k)
        ang = 2.0 * math.pi * pos / m
        out[label] = complex(math.cos(ang), math.sin(ang))
    return out


def _qam_points(k):
    """사각 M-QAM — 앞 절반 비트가 I, 뒤 절반이 Q.

    각 축은 그레이 PAM 이다. 평균 에너지를 1 로 맞추는 배율은
    √(3/(2(M−1))) 인데, 그 까닭은 ±1,±3,…,±(L−1) 의 평균 제곱이
    (L²−1)/3 이고 두 축이 있어 2(M−1)/3 이 되기 때문이다.
    """
    if k % 2:
        raise ValueError('사각 QAM 은 짝수 비트만 된다: k=%d' % k)
    half = k // 2
    side = 1 << half
    m = 1 << k
    scale = math.sqrt(3.0 / (2.0 * (m - 1)))

    def level(h):
        return 2 * _ungray(h, half) - (side - 1)

    out = [0j] * m
    for label in range(m):
        hi = label >> half            # 앞 절반 비트 → I
        lo = label & (side - 1)       # 뒤 절반 비트 → Q
        out[label] = complex(level(hi), level(lo)) * scale
    return out


def _normalise(points):
    e = math.sqrt(sum(abs(p) ** 2 for p in points) / len(points))
    return [p / e for p in points]


_CACHE = {}


def constellation(name):
    """이름으로 성상도를 얻는다.

    'bpsk' · 'qpsk' · '8psk' · '16qam' · '64qam' … '1024qam'.
    """
    name = name.lower()
    if name in _CACHE:
        return _CACHE[name]
    if name == 'bpsk':
        c = Constellation('bpsk', 1, [1 + 0j, -1 + 0j])
    elif name == 'qpsk':
        # QPSK 는 직교한 BPSK 둘이다. I 와 Q 에 비트를 하나씩 싣는다.
        s = 1.0 / math.sqrt(2.0)
        c = Constellation('qpsk', 2, [complex(s, s), complex(s, -s),
                                      complex(-s, s), complex(-s, -s)])
    elif name.endswith('psk'):
        m = int(name[:-3])
        k = m.bit_length() - 1
        if (1 << k) != m or k < 1:
            raise ValueError('PSK 크기는 2의 거듭제곱이어야 한다: %s'
                             % name)
        c = Constellation(name, k, _normalise(_psk_points(k)))
    elif name.endswith('qam'):
        m = int(name[:-3])
        k = m.bit_length() - 1
        if (1 << k) != m or k < 2 or k % 2:
            raise ValueError('사각 QAM 만 다룬다: %s' % name)
        c = Constellation(name, k, _normalise(_qam_points(k)))
    else:
        raise ValueError('모르는 성상도: %s' % name)
    _CACHE[name] = c
    return c


# ── 변조·복조 ─────────────────────────────────────────────────────


def modulate(bits, c):
    """비트열 → 심볼열. k 비트씩 묶어 MSB 먼저 라벨을 만든다."""
    if len(bits) % c.k:
        raise ValueError('비트 수가 %d 의 배수가 아니다: %d'
                         % (c.k, len(bits)))
    out = []
    for i in range(0, len(bits), c.k):
        label = 0
        for b in bits[i:i + c.k]:
            label = (label << 1) | (b & 1)
        out.append(c.points[label])
    return out


def _label_bits(label, k):
    return [(label >> (k - 1 - j)) & 1 for j in range(k)]


def demap_hard(y, c):
    """가장 가까운 점을 고른다 — AWGN 에서는 이것이 최우 판정이다."""
    out = []
    for v in y:
        best, bi = None, 0
        for label, p in enumerate(c.points):
            d = (v.real - p.real) ** 2 + (v.imag - p.imag) ** 2
            if best is None or d < best:
                best, bi = d, label
        out.extend(_label_bits(bi, c.k))
    return out


def demap_llr(y, c, n0, maxlog=False):
    """비트마다 로그 우도비. 양수면 0 쪽이 더 그럴듯하다는 뜻이다.

    LLR(b) = ln [ Σ_{s: b=0} e^{−|y−s|²/N₀} ] − ln [ Σ_{s: b=1} … ]

    maxlog 를 켜면 합을 가장 큰 항 하나로 갈음한다(최소 거리 차). 3부의
    LDPC·터보 복호기가 실제로 쓰는 근사이고, 높은 SNR 에서는 거의 같다.
    시험이 그 '거의' 를 숫자로 확인한다.

    지수가 밑넘침하지 않도록 각 비트마다 최소 거리를 먼저 빼 둔다 —
    빼지 않으면 N₀ 가 작을 때 양쪽 합이 모두 0 이 되어 log(0) 이 된다.
    """
    masks = [1 << (c.k - 1 - j) for j in range(c.k)]
    out = []
    for v in y:
        d = [((v.real - p.real) ** 2 + (v.imag - p.imag) ** 2) / n0
             for p in c.points]
        for j, mask in enumerate(masks):
            d0 = [d[t] for t in range(c.m) if not (t & mask)]
            d1 = [d[t] for t in range(c.m) if (t & mask)]
            if maxlog:
                out.append(min(d1) - min(d0))
            else:
                m0, m1 = min(d0), min(d1)
                s0 = sum(math.exp(m0 - x) for x in d0)
                s1 = sum(math.exp(m1 - x) for x in d1)
                out.append((m1 - m0) + math.log(s0) - math.log(s1))
    return out


def awgn(syms, snr_db, rnd):
    """Es/N0 [dB] 를 주면 그만큼의 복소 백색 가우스 잡음을 더한다.

    복소 잡음의 전력은 두 축에 반씩 나뉜다 — 축마다 분산 N₀/2 다.
    이 반쪽을 빠뜨리는 것이 이 바닥에서 가장 흔한 3 dB 오류다.
    """
    if not syms:
        return []
    es = sum(abs(s) ** 2 for s in syms) / len(syms)
    n0 = es / db2lin(snr_db)
    sd = math.sqrt(n0 / 2.0)
    return [s + complex(rnd.gauss(0.0, sd), rnd.gauss(0.0, sd))
            for s in syms]


# ── 오류율 ────────────────────────────────────────────────────────


def ber_sim(name, ebn0_db, nbits, seed=1):
    """몬테카를로 BER. 같은 씨앗이면 언제나 같은 값이 나온다."""
    c = constellation(name)
    nsym = nbits // c.k
    if nsym < 1:
        raise ValueError('비트가 너무 적다')
    rnd = random.Random(seed)
    esn0 = ebn0_db + lin2db(c.k)
    bits = [rnd.getrandbits(1) for _ in range(nsym * c.k)]
    y = awgn(modulate(bits, c), esn0, rnd)
    got = demap_hard(y, c)
    err = sum(1 for a, b in zip(bits, got) if a != b)
    return err / float(len(bits))


def ser_sim(name, esn0_db, nsym, seed=1):
    """몬테카를로 SER — 심볼 단위 오류율."""
    c = constellation(name)
    rnd = random.Random(seed)
    labels = [rnd.randrange(c.m) for _ in range(nsym)]
    syms = [c.points[v] for v in labels]
    y = awgn(syms, esn0_db, rnd)
    err = 0
    for v, want in zip(y, labels):
        best, bi = None, 0
        for label, p in enumerate(c.points):
            d = (v.real - p.real) ** 2 + (v.imag - p.imag) ** 2
            if best is None or d < best:
                best, bi = d, label
        if bi != want:
            err += 1
    return err / float(nsym)


def ber_theory(name, ebn0_db):
    """닫힌 식(또는 표준 근사식)의 BER.

    · BPSK·QPSK : Q(√(2 Eb/N₀)) — 근사가 아니라 정확한 값이다
    · 사각 M-QAM: (4/k)(1 − 1/√M) · Q(√(3k/(M−1) · Eb/N₀)) — **근사식**.
      가장 가까운 이웃만 센 것이라 낮은 SNR 에서 조금 크게 나온다.
    · M-PSK    : SER 근사식을 k 로 나눈 것 — 그레이 사상을 가정한다
    """
    c = constellation(name)
    g = db2lin(ebn0_db)
    if c.name in ('bpsk', 'qpsk'):
        return qfunc(math.sqrt(2.0 * g))
    if c.name.endswith('qam'):
        return ((4.0 / c.k) * (1.0 - 1.0 / math.sqrt(c.m))
                * qfunc(math.sqrt(3.0 * c.k * g / (c.m - 1))))
    return ser_theory_mpsk(c.m, ebn0_db + lin2db(c.k)) / c.k


def ser_theory_mpsk(m, esn0_db):
    """M-PSK 의 SER 근사 — 2·Q(√(2 Es/N₀) · sin(π/M)).

    가장 가까운 두 이웃만 센 합집합 한계다. M ≥ 4 이고 SNR 이 웬만하면
    참값과 몇 %  안에서 맞는다. M=2 는 이 식이 두 배로 세므로 따로 둔다.
    """
    g = db2lin(esn0_db)
    if m == 2:
        return qfunc(math.sqrt(2.0 * g))
    return 2.0 * qfunc(math.sqrt(2.0 * g) * math.sin(math.pi / m))
