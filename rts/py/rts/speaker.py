# -*- coding: utf-8 -*-
"""PC 스피커 — 분주값·음표표·사각파 (SPEC §21).

   PIT 은 사각파만 낼 수 있었다. 음량 조절이 없었고 듀티비도 고정이라,
   도스 게임의 스피커 음악은 전부 같은 음색이다. 여기서 하는 일은 그 제약을
   그대로 흉내내는 것뿐이다.

   소리를 재생하지 않는다 — 헤드리스 환경이고, 바이트가 같으면 소리도 같다.
"""

from . import const as C
from . import fixed as F

SAMPLE_RATE = 22050
AMP_LO, AMP_HI, AMP_MID = 0x40, 0xC0, 0x80

# §21.2 A4 = 440 Hz 12평균율을 **정수 Hz 로 반올림해 박아 둔다.**
# 세 언어가 같은 표를 갖는 것이 실수 연산을 맞추는 것보다 싸고 확실하다.
NOTE_NAME = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4',
             'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5',
             'G#5', 'A5', 'A#5', 'B5']
NOTE_HZ = [262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494,
           523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 932, 988]


# ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
def divisor(f):
    """반올림 나눗셈. PIT_HZ 자체가 반올림값이라는 것을 22부가 따로 따진다."""
    if f <= 0:
        return 0
    d = F.floordiv(C.PIT_HZ + F.floordiv(f, 2), f)
    return 1 if d < 1 else d


def actual(f):
    """실제로 나는 주파수를 **정수 나눗셈의 몫과 나머지**로 낸다.

       센트 오차는 로그가 필요하므로 엔진이 아니라 tools/gen_prim.py 가 낸다.
    """
    d = divisor(f)
    if d == 0:
        return (0, 0)
    return (C.PIT_HZ // d, C.PIT_HZ % d)


def actual100(f):
    d = divisor(f)
    return 0 if d == 0 else C.PIT_HZ * 100 // d


# ── SPEC §21.3 사각파 합성 ──────────────────────────────────────────────────
def half_period(f):
    q = actual(f)[0]
    if q <= 0:
        return 0
    return F.floordiv(SAMPLE_RATE, 2 * q)


def square(f, n):
    """8비트 부호 없는 모노 PCM n 샘플. f <= 0 이면 무음(쉼표)."""
    if n <= 0:
        return b''
    if f <= 0:
        return bytes(bytearray([AMP_MID] * n))
    half = half_period(f)
    if half <= 0:
        return bytes(bytearray([AMP_MID] * n))
    out = bytearray()
    for k in range(n):
        out.append(AMP_LO if F.floordiv(k, half) % 2 == 0 else AMP_HI)
    return bytes(out)


def _le(out, v, n):
    for _k in range(n):
        out.append(v % 256)
        v //= 256


def wav(pcm):
    """44바이트 헤더 + PCM. 전체 바이트의 FNV-1a 를 골든으로 둔다."""
    out = bytearray()
    out += b'RIFF'
    _le(out, 36 + len(pcm), 4)
    out += b'WAVE'
    out += b'fmt '
    _le(out, 16, 4)                    # fmt 청크 길이
    _le(out, 1, 2)                     # PCM
    _le(out, 1, 2)                     # 모노
    _le(out, SAMPLE_RATE, 4)
    _le(out, SAMPLE_RATE, 4)           # 바이트/초 = 레이트 × 1채널 × 1바이트
    _le(out, 1, 2)                     # 블록 정렬
    _le(out, 8, 2)                     # 비트/샘플
    out += b'data'
    _le(out, len(pcm), 4)
    out += bytearray(pcm)
    return bytes(out)


def tune(notes):
    """(주파수, 샘플 수) 목록을 이어 붙여 WAV 로."""
    pcm = bytearray()
    for (f, n) in notes:
        pcm += bytearray(square(f, n))
    return wav(bytes(pcm))
