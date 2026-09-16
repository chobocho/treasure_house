# -*- coding: utf-8 -*-
"""tdma — GSM 의 시간축과 GMSK.

   GSM 의 시간 구조는 어림수가 하나도 없다. 변조율 1625/6 kbit/s 하나를
   놓으면 나머지가 전부 유리수로 따라 나온다.

       비트 길이   48/13 μs   ≈ 3.692 μs
       슬롯        156.25 비트 = 15/26 ms ≈ 576.9 μs
       프레임      8슬롯      = 60/13 ms  ≈ 4.615 ms
       26 멀티프레임 = 120 ms **정확히** (13 이 딱 나눠떨어진다)
       51 멀티프레임 = 3060/13 ms ≈ 235.4 ms
       슈퍼프레임  = 26×51 = 1326 프레임 = 6.12 s
       하이퍼프레임 = 2048 슈퍼프레임 = 2,715,648 프레임
                    = 3시간 28분 53.76초

   마지막 값이 왜 중요한가: A5 암호가 프레임 번호를 초기 벡터로 쓰므로,
   같은 키를 쓰는 한 이 주기가 곧 열쇠 흐름이 되풀이되는 주기다.

   그래서 이 파일은 실수(float) 대신 **분수** 로 셈한다. 4.615 ms 로
   적어 놓고 26을 곱하면 120 ms 가 안 나온다.

   뒤쪽 절반은 GMSK 다. 포락선이 일정해 증폭기를 포화시켜 쓸 수 있고
   (배터리와 값), 가우스 필터로 위상을 부드럽게 만들어 이웃 채널로
   새는 전력을 줄였다. 그 대가가 ISI 이고, BT=0.3 이 그 맞바꿈의 답이다.
"""
import cmath
import math
import random

from fractions import Fraction

from wirelesslib import dsp

C = 299792458.0

# 3GPP TS 45.001·45.002 — 시간축의 뿌리
RATE_KBPS = Fraction(1625, 6)
BIT_US = Fraction(1000) / RATE_KBPS          # 48/13 μs
SLOT_BITS = Fraction(625, 4)                 # 156.25 비트
SLOT_MS = SLOT_BITS * BIT_US / 1000          # 15/26 ms
FRAME_MS = 8 * SLOT_MS                       # 60/13 ms
SUPERFRAME_FRAMES = 26 * 51                  # 1326
HYPERFRAME_FRAMES = 2048 * SUPERFRAME_FRAMES  # 2,715,648


def multiframe_ms(n):
    """n 프레임짜리 멀티프레임의 길이 [ms]. 26 이면 정확히 120 이다."""
    return n * FRAME_MS


def superframe_ms():
    return multiframe_ms(SUPERFRAME_FRAMES)


def hyperframe_seconds():
    return HYPERFRAME_FRAMES * FRAME_MS / 1000


def hyperframe_hms():
    """(시, 분, 초). 초는 소수점까지 남긴다."""
    total = hyperframe_seconds()
    h = int(total // 3600)
    m = int((total - h * 3600) // 60)
    s = float(total - h * 3600 - m * 60)
    return h, m, s


def next_fn(fn):
    """다음 프레임 번호. 하이퍼프레임 끝에서 0 으로 돌아간다."""
    return (fn + 1) % HYPERFRAME_FRAMES


# ── 버스트 ────────────────────────────────────────────────────────
#
# TS 45.002 §5.2 — 다섯 종류 모두 156.25 비트다. 가드 구간의 길이가
# 그 버스트가 무엇을 모르는 채로 보내는지를 말해 준다.
_BURSTS = {
    'normal': [('꼬리1', 3), ('데이터1', 57), ('스틸링1', 1),
               ('훈련열', 26), ('스틸링2', 1), ('데이터2', 57),
               ('꼬리2', 3), ('가드', Fraction(33, 4))],
    # 주파수 보정 버스트 — 142비트를 전부 0 으로 채워 순수 정현파를 낸다
    'frequency': [('꼬리1', 3), ('고정비트', 142), ('꼬리2', 3),
                  ('가드', Fraction(33, 4))],
    'sync': [('꼬리1', 3), ('데이터1', 39), ('확장훈련열', 64),
             ('데이터2', 39), ('꼬리2', 3), ('가드', Fraction(33, 4))],
    'dummy': [('꼬리1', 3), ('혼합비트', 142), ('꼬리2', 3),
              ('가드', Fraction(33, 4))],
    # 임의접속 버스트 — 거리를 모르니 가드를 68.25 비트나 둔다
    'access': [('확장꼬리', 8), ('동기열', 41), ('데이터', 36),
               ('꼬리', 3), ('가드', Fraction(273, 4))],
}
BURSTS = tuple(sorted(_BURSTS))


def burst_fields(kind):
    """버스트의 칸 목록 [(이름, 비트 수), …]. 합은 언제나 156.25 다."""
    if kind not in _BURSTS:
        raise ValueError('모르는 버스트: %s' % kind)
    return list(_BURSTS[kind])


# ── 타이밍 어드밴스 ───────────────────────────────────────────────


def ta_distance_m(ta):
    """타이밍 어드밴스 한 걸음이 나타내는 거리.

    한 걸음은 비트 하나의 **왕복** 이다. 빛이 3.692 μs 동안 가는 거리의
    절반이니 약 553 m 다. TA 는 6비트(0~63)라 최대 34.9 km —
    그래서 GSM 셀 반지름의 한계가 35 km 다. 이 한계는 전력이 아니라
    시간축이 만든 것이다.
    """
    if not 0 <= ta <= 63:
        raise ValueError('TA 는 0~63 이다: %s' % ta)
    return C * float(BIT_US) * 1e-6 * ta / 2.0


def ta_from_distance(d):
    """거리에 맞는 가장 큰 TA. 35 km 를 넘으면 예외."""
    if d < 0:
        raise ValueError('거리는 음수일 수 없다')
    step = ta_distance_m(1)
    ta = int(d // step)
    if ta > 63:
        raise ValueError('GSM 셀 반지름 한계(약 35 km)를 넘는다: %g m'
                         % d)
    return ta


# ── GMSK ──────────────────────────────────────────────────────────


def msk_phase(bits, sps=8):
    """MSK 의 위상 궤적. 비트마다 정확히 ±π/2 를 움직인다.

    MSK 는 변조 지수 0.5 인 연속 위상 FSK 다. 위상이 꺾이지 않고
    이어지므로 스펙트럼이 좁고, 크기가 일정해 증폭기를 포화시켜 쓸 수
    있다. 여기서 한 걸음 더 나아가 위상 변화까지 부드럽게 만든 것이
    GMSK 다.
    """
    ph = [0.0]
    for b in bits:
        d = (math.pi / 2) * (1 if b else -1) / sps
        for _ in range(sps):
            ph.append(ph[-1] + d)
    return ph


def gaussian_pulse(bt, sps=8, span=4):
    """가우스 필터의 임펄스 응답. 넓이를 1 로 맞춰 돌려준다.

    BT 는 3 dB 대역폭과 비트 주기의 곱이다. 작을수록 스펙트럼이 좁아
    이웃 채널을 덜 건드리지만, 시간 영역에서 길어져 ISI 가 는다.
    GSM 은 BT=0.3 을 골랐다 — 세 비트쯤에 걸치는 길이다.
    """
    if bt <= 0:
        raise ValueError('BT 는 양수여야 한다')
    # σ = √(ln2) / (2π·BT) [비트 주기 단위] 이므로
    # h(t) ∝ exp(−t² / 2σ²) = exp(−2π²·BT²·t² / ln2) 다.
    k = 2.0 * (math.pi ** 2) * bt * bt / math.log(2.0)
    n = span * sps
    out = []
    for i in range(n + 1):
        t = (i - n / 2.0) / sps
        out.append(math.exp(-k * t * t))
    s = sum(out)
    return [v / s for v in out]


def pulse_width(g):
    """실효 폭 — 넓이로 가중한 표준편차. BT 비교에 쓴다."""
    n = len(g)
    mid = (n - 1) / 2.0
    m2 = sum(v * (i - mid) ** 2 for i, v in enumerate(g))
    return math.sqrt(m2 / sum(g))


def gmsk_modulate(bits, bt=0.3, sps=8, span=4):
    """GMSK 변조. 가우스 필터를 지난 뒤 위상을 쌓는다.

    bt 가 None 이면 필터를 걸지 않은 MSK 다. 어느 쪽이든 결과의 크기는
    언제나 1 이다 — 일정 포락선이라는 말의 실체이고, 그래서 값싼
    비선형 증폭기를 쓸 수 있다.
    """
    nrz = [1.0 if b else -1.0 for b in bits]
    up = dsp.upsample(nrz, sps)
    if bt is None:
        shaped = up
    else:
        shaped = dsp.conv(up, gaussian_pulse(bt, sps, span))
    ph = 0.0
    out = []
    for v in shaped:
        ph += (math.pi / 2) * v / sps
        out.append(cmath.exp(1j * ph))
    return out


def out_of_band_db(bt, seed=1, nbits=512, sps=8, edge=0.75):
    """대역 밖으로 새는 전력의 비율 [dB]. 작을수록 이웃 채널에 착하다.

    기준 대역은 비트율의 edge 배다. 그 밖으로 나간 전력을 전체로 나눈다.
    GMSK(BT=0.3)가 MSK 보다 확실히 작아야 한다 — GSM 이 200 kHz 간격에
    270.833 kbit/s 를 밀어 넣을 수 있었던 근거다.
    """
    rnd = random.Random(seed)
    bits = [rnd.getrandbits(1) for _ in range(nbits)]
    x = gmsk_modulate(bits, bt, sps)
    n = dsp.next_pow2(len(x))
    p = dsp.periodogram(x, n)
    total = sum(p)
    # 표본율은 비트율의 sps 배다. 정규화 주파수 edge/sps 안쪽이 대역 안.
    k = int(n * edge / (2.0 * sps))
    inband = sum(p[:k + 1]) + sum(p[n - k:])
    return 10.0 * math.log10(max(total - inband, 1e-30) / total)
