# -*- coding: utf-8 -*-
"""codes — 오류를 막는 부호들. 이 책의 3부가 통째로 이 모듈이다.

   담긴 것은 넷이다.

     · **CRC** — 고치지는 못하고 깨졌는지만 안다. 그런데 무선에서는
       그 '안다' 가 곧 재전송(HARQ)의 방아쇠라 값이 크다.
     · **블록 부호** — 해밍(7,4). 최소 거리가 곧 정정 능력이라는 것을
       가장 작은 예로 보여 준다.
     · **컨볼루션 부호와 비터비** — 2G·3G 의 음성과 제어가 전부 이것
       위에 있었다. GSM(K=5)·IS-95(K=9)·LTE(K=7 꼬리물기)를 담았다.
     · **인터리버** — 부호는 흩어진 오류에 강하고 연집 오류에 약하다.
       그 간극을 메우는 것이 인터리버다.

   부호기는 자기 복호기와만 짝이 맞아도 왕복이 되기 때문에, 시험은
   왕복이 아니라 **거리** 를 본다. 거리를 전수로 세고, 그 거리에서
   보장되는 오류를 하나도 빠짐없이 고치는지 확인한다.
"""

# ── CRC ───────────────────────────────────────────────────────────
#
# 생성 다항식은 3GPP TS 38.212 §5.1(NR)·TS 36.212 §5.1.1(LTE)·
# TS 45.003(GSM)의 것이다. 값은 최고차항(항상 1)을 뺀 나머지 계수다.
CRC_POLYS = {
    # D³ + D + 1 — GSM 음성 Ia 등급 3비트 패리티
    'gsm_crc3': (3, 0b011),
    # D⁶ + D⁵ + 1 — NR 의 짧은 제어 정보
    'crc6': (6, 0x21),
    # D⁸ + D⁷ + D⁴ + D³ + D + 1 — LTE
    'crc8': (8, 0x9B),
    # D¹¹ + D¹⁰ + D⁹ + D⁵ + 1 — NR
    'crc11': (11, 0x621),
    # D¹⁶ + D¹² + D⁵ + 1 — LTE·NR (CRC-CCITT 와 같은 다항식)
    'crc16': (16, 0x1021),
    # D²⁴+D²³+D¹⁸+D¹⁷+D¹⁴+D¹¹+D¹⁰+D⁷+D⁶+D⁵+D⁴+D³+D+1
    'crc24a': (24, 0x864CFB),
    # D²⁴ + D²³ + D⁶ + D⁵ + D + 1
    'crc24b': (24, 0x800063),
    # D²⁴+D²³+D²¹+D²⁰+D¹⁷+D¹⁵+D¹³+D¹²+D⁸+D⁴+D²+D+1
    'crc24c': (24, 0xB2B117),
}


def crc_len(name):
    if name not in CRC_POLYS:
        raise ValueError('모르는 CRC: %s' % name)
    return CRC_POLYS[name][0]


def crc(bits, name):
    """시프트 레지스터로 구한 CRC. 초기값 0, 최종 반전 없음(3GPP 방식).

    구하는 값은 메시지 다항식에 D^L 을 곱해 생성 다항식으로 나눈
    나머지다. 시간 O(n).
    """
    if name not in CRC_POLYS:
        raise ValueError('모르는 CRC: %s' % name)
    length, poly = CRC_POLYS[name]
    mask = (1 << length) - 1
    reg = 0
    for b in bits:
        top = ((reg >> (length - 1)) & 1) ^ (b & 1)
        reg = (reg << 1) & mask
        if top:
            reg ^= poly
    return [(reg >> (length - 1 - i)) & 1 for i in range(length)]


def crc_polydiv(bits, name):
    """같은 값을 다항식 긴 나눗셈으로 — **다른 길로** 구한 검산용.

    시프트 레지스터 판이 틀려도 자기 자신과는 늘 짝이 맞는다. 정의
    그대로 나눠 보는 이쪽과 맞대어야 "맞다" 고 말할 수 있다.
    시간 O(n·L).
    """
    if name not in CRC_POLYS:
        raise ValueError('모르는 CRC: %s' % name)
    length, poly = CRC_POLYS[name]
    gen = [1] + [(poly >> (length - 1 - i)) & 1 for i in range(length)]
    work = [b & 1 for b in bits] + [0] * length
    for i in range(len(work) - length):
        if work[i]:
            for j, g in enumerate(gen):
                work[i + j] ^= g
    return work[-length:]


def crc_append(bits, name):
    """메시지 뒤에 CRC 를 붙인다.

    이렇게 하면 전체가 생성 다항식으로 나누어떨어진다.
    """
    return list(bits) + crc(bits, name)


def crc_check(bits, name):
    """CRC 가 붙은 말이 성한지. 나머지가 0 이면 성하다고 본다."""
    return crc(bits, name) == [0] * crc_len(name)


# ── 해밍(7,4) ─────────────────────────────────────────────────────
#
# 부호어는 [d0 d1 d2 d3 p0 p1 p2] 다.
#   p0 = d0⊕d1⊕d2 · p1 = d1⊕d2⊕d3 · p2 = d0⊕d1⊕d3
# 검사 행렬의 일곱 열이 서로 다른 0 아닌 3비트 값이라, 증후군이 곧
# 틀린 자리의 이름이 된다. 최소 거리 3 — 한 자리를 고친다.
_H_COLS = [0b101, 0b111, 0b110, 0b011, 0b100, 0b010, 0b001]
_SYND = {v: i for i, v in enumerate(_H_COLS)}


def hamming74_encode(bits):
    if len(bits) != 4:
        raise ValueError('해밍(7,4)의 메시지는 4비트다: %d' % len(bits))
    d0, d1, d2, d3 = (b & 1 for b in bits)
    return [d0, d1, d2, d3,
            d0 ^ d1 ^ d2, d1 ^ d2 ^ d3, d0 ^ d1 ^ d3]


def hamming74_decode(bits):
    """(메시지, 고친 자리) — 고친 데가 없으면 자리는 −1."""
    if len(bits) != 7:
        raise ValueError('해밍(7,4)의 부호어는 7비트다: %d' % len(bits))
    c = [b & 1 for b in bits]
    s = 0
    for i, col in enumerate(_H_COLS):
        if c[i]:
            s ^= col
    fixed = -1
    if s:
        fixed = _SYND[s]
        c[fixed] ^= 1
    return c[:4], fixed


# ── 컨볼루션 부호 ─────────────────────────────────────────────────


def _parity(v):
    return bin(v).count('1') & 1


class ConvCode(object):
    """비되먹임 컨볼루션 부호기와 비터비 복호기.

    상태는 '최근 K−1 개의 입력 비트' 다. 생성 다항식의 최상위 비트가
    지금 들어온 비트에 붙는다 — 예를 들어 K=5 에서 0o23 = 10011 은
    1 + D³ + D⁴ 를 뜻한다.

    비터비의 시간은 O(단계 수 · 2^(K−1) · 2), 공간도 같다(역추적표).
    """

    def __init__(self, k, polys, name=''):
        self.k = k
        self.n = len(polys)
        self.polys = list(polys)
        self.name = name
        self.nstate = 1 << (k - 1)
        self.mask = self.nstate - 1
        # 상태·입력마다 (다음 상태, 출력 비트들) 을 미리 펴 둔다.
        self.next = [[0] * 2 for _ in range(self.nstate)]
        self.out = [[None] * 2 for _ in range(self.nstate)]
        for st in range(self.nstate):
            for u in (0, 1):
                reg = (u << (k - 1)) | st
                self.next[st][u] = reg >> 1
                self.out[st][u] = tuple(_parity(reg & p) for p in polys)

    # ---- 부호기 ----

    def encode(self, bits, tail=True, tailbiting=False):
        """비트열을 부호화한다.

        tail=True 면 끝에 0 을 K−1 개 붙여 상태 0 으로 되돌린다.
        tailbiting=True 면 꼬리 비트 없이, 시작 상태를 메시지의 마지막
        K−1 비트로 맞춘다 — LTE 의 제어 채널이 쓰는 방식이다.
        길이가 짧은 말에서 꼬리 비트의 낭비를 없애려는 것이다.
        """
        bits = [b & 1 for b in bits]
        if tailbiting:
            if len(bits) < self.k - 1:
                raise ValueError('꼬리물기는 메시지가 K−1 비트 이상'
                                 ' 이어야 한다')
            st = 0
            for i in range(self.k - 1):
                st |= bits[len(bits) - 1 - i] << (self.k - 2 - i)
            seq = bits
        else:
            st = 0
            seq = bits + ([0] * (self.k - 1) if tail else [])
        out = []
        for u in seq:
            out.extend(self.out[st][u])
            st = self.next[st][u]
        return out

    # ---- 복호기 ----

    def _viterbi(self, metric, steps, start=None, end=None):
        """공통 몸통.

        metric(step, state, u) 가 그 가지의 비용을 준다.
        """
        inf = float('inf')
        if start is None:
            cost = [0.0] * self.nstate
        else:
            cost = [inf] * self.nstate
            cost[start] = 0.0
        back = []
        for t in range(steps):
            nxt = [inf] * self.nstate
            bt = [(-1, 0)] * self.nstate
            for st in range(self.nstate):
                if cost[st] == inf:
                    continue
                for u in (0, 1):
                    c = cost[st] + metric(t, st, u)
                    ns = self.next[st][u]
                    if c < nxt[ns]:
                        nxt[ns] = c
                        bt[ns] = (st, u)
            cost = nxt
            back.append(bt)
        if end is None:
            last = min(range(self.nstate), key=lambda s: cost[s])
        else:
            last = end
        if cost[last] == inf:
            raise ValueError('복호할 수 있는 경로가 없다')
        msg = []
        st = last
        for t in range(steps - 1, -1, -1):
            prev, u = back[t][st]
            msg.append(u)
            st = prev
        msg.reverse()
        return msg, cost[last]

    def _check_len(self, y):
        if len(y) % self.n:
            raise ValueError('받은 길이가 %d 의 배수가 아니다: %d'
                             % (self.n, len(y)))
        return len(y) // self.n

    def viterbi_hard(self, y):
        """경판정 비터비. 가지 비용은 해밍 거리다.

        꼬리 비트로 끝맺은(terminated) 부호라고 보고, 마지막 K−1 개를
        떼어 낸 메시지를 돌려준다.
        """
        steps = self._check_len(y)
        y = [b & 1 for b in y]

        def metric(t, st, u):
            o = self.out[st][u]
            base = t * self.n
            return sum(1 for i in range(self.n) if o[i] != y[base + i])

        msg, _c = self._viterbi(metric, steps, start=0, end=0)
        return msg[:steps - (self.k - 1)]

    def viterbi_soft(self, llr):
        """연판정 비터비. LLR 이 양수면 0 쪽이 더 그럴듯하다는 뜻이다.

        0 을 고르면 −LLR, 1 을 고르면 +LLR 을 더하고 합을 최소화한다.
        경판정보다 이론상 약 2 dB 를 번다 — 시험이 같은 잡음에서
        연판정이 더 적게 틀리는지 확인한다.
        """
        steps = self._check_len(llr)

        def metric(t, st, u):
            o = self.out[st][u]
            base = t * self.n
            s = 0.0
            for i in range(self.n):
                s += llr[base + i] if o[i] else -llr[base + i]
            return s

        msg, _c = self._viterbi(metric, steps, start=0, end=0)
        return msg[:steps - (self.k - 1)]

    def viterbi_tailbiting(self, y):
        """꼬리물기 복호 — 시작 상태를 모르니 전부 해 보고 고른다.

        시작과 끝 상태가 같은 경로 가운데 비용이 가장 작은 것을 고른다.
        시간이 2^(K−1) 배 든다. 실물 수신기는 '원형 비터비' 로 이것을
        어림하지만, 여기서는 정확한 쪽을 택했다 — 이 책이 보여 주려는
        것은 속도가 아니라 뜻이다.
        """
        steps = self._check_len(y)
        y = [b & 1 for b in y]

        def metric(t, st, u):
            o = self.out[st][u]
            base = t * self.n
            return sum(1 for i in range(self.n) if o[i] != y[base + i])

        best, bestc = None, float('inf')
        for s0 in range(self.nstate):
            try:
                msg, c = self._viterbi(metric, steps, start=s0, end=s0)
            except ValueError:
                continue
            if c < bestc:
                best, bestc = msg, c
        if best is None:
            raise ValueError('꼬리물기 경로를 못 찾았다')
        return best

    # ---- 거리 ----

    def min_distance(self, nmsg):
        """길이 nmsg 인 말을 꼬리 비트로 끝맺었을 때의 최소 거리.

        전수로 센다 — 2^nmsg 개의 부호어를 만들어 0 이 아닌 것 가운데
        가장 가벼운 무게를 찾는다(선형 부호라 이것이 곧 최소 거리다).
        nmsg 가 커지면 자유 거리로 수렴한다. nmsg ≤ 14 에서만 쓸 것.
        """
        if nmsg > 14:
            raise ValueError('전수로 세기에 너무 크다: %d' % nmsg)
        best = None
        for v in range(1, 1 << nmsg):
            msg = [(v >> (nmsg - 1 - i)) & 1 for i in range(nmsg)]
            w = sum(self.encode(msg, tail=True))
            if best is None or w < best:
                best = w
        return best


# 3GPP TS 45.003 §4.1.3 — GSM 의 rate 1/2, K=5 (1+D³+D⁴, 1+D+D³+D⁴)
GSM_CONV = ConvCode(5, [0o23, 0o33], 'GSM K=5 r=1/2')
# TIA/EIA IS-95 순방향 — rate 1/2, K=9
IS95_CONV = ConvCode(9, [0o753, 0o561], 'IS-95 K=9 r=1/2')
# 3GPP TS 36.212 §5.1.3.1 — LTE 꼬리물기 rate 1/3, K=7
LTE_CONV = ConvCode(7, [0o133, 0o171, 0o165], 'LTE K=7 r=1/3')


# ── 인터리버 ──────────────────────────────────────────────────────


def block_interleave(x, rows, cols):
    """행으로 쓰고 열로 읽는다 — 가장 단순하고 가장 많이 쓰인 인터리버.

    연집 오류가 복호기 앞에서 rows 칸씩 벌어져 흩어진다. 대신 지연이
    한 블록만큼 늘어난다. 이 맞바꿈이 인터리버 설계의 전부다.
    """
    if len(x) != rows * cols:
        raise ValueError('길이가 %d×%d 와 다르다: %d'
                         % (rows, cols, len(x)))
    return [x[r * cols + c] for c in range(cols) for r in range(rows)]


def block_deinterleave(x, rows, cols):
    """block_interleave 의 역."""
    if len(x) != rows * cols:
        raise ValueError('길이가 %d×%d 와 다르다: %d'
                         % (rows, cols, len(x)))
    out = [None] * (rows * cols)
    i = 0
    for c in range(cols):
        for r in range(rows):
            out[r * cols + c] = x[i]
            i += 1
    return out
