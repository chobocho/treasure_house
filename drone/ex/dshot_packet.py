# -*- coding: utf-8 -*-
"""DShot 한 프레임 — 16비트 = 값 11 + 텔레메트리 요청 1 + 체크섬 4.

Betaflight src/main/drivers/dshot.c 의 prepareDshotPacket 과 같은
틀을 파이썬으로 옮겼다(4부 4장). 값 48–2047 이 스로틀이고 그 아래는
명령이다(dshot.h 의 DSHOT_MIN_THROTTLE·DSHOT_MAX_THROTTLE).
"""
import itertools

MIN_THROTTLE = 48
MAX_THROTTLE = 2047


def packet(value, telemetry=False, inverted=False):
    """값 → 16비트 프레임. 체크섬은 앞 12비트의 니블 셋을 XOR.

    inverted 는 양방향 DShot 에서 체크섬을 뒤집는 것(원본의 ~csum)."""
    if not 0 <= value <= 2047:
        raise ValueError('값은 11비트(0–2047)')
    p = (value << 1) | (1 if telemetry else 0)
    csum, data = 0, p
    for _ in range(3):
        csum ^= data          # 니블 단위로 XOR
        data >>= 4
    if inverted:
        csum = ~csum
    return (p << 4) | (csum & 0xF)


def check(frame, inverted=False):
    """받은 쪽의 검사 — 앞 12비트로 체크섬을 다시 만들어 비교."""
    p = frame >> 4
    want = packet(p >> 1, bool(p & 1), inverted)
    return frame == want


def unpack(frame):
    p = frame >> 4
    return p >> 1, bool(p & 1)


def flips_caught(frame, k):
    """비트 k 개를 뒤집는 모든 경우 가운데 체크섬이 잡는 수 → (잡음,
    전체). 16비트에서 고르므로 C(16, k) 가지."""
    got = total = 0
    for bits in itertools.combinations(range(16), k):
        bad = frame
        for b in bits:
            bad ^= 1 << b
        total += 1
        got += not check(bad)
    return got, total


def frame_us(kbit):
    """DShot<kbit> 한 프레임이 선 위에 머무는 시간[µs] = 16비트 ÷
    초당 비트."""
    return 16 / (kbit * 1000.0) * 1e6


if __name__ == '__main__':
    for v, t in ((0, False), (48, False), (1046, False), (1046, True),
                 (2047, False)):
        f = packet(v, t)
        print('값 %4d 텔레메트리 %d → %s  0x%04X'
              % (v, t, format(f, '016b'), f))
    f = packet(1046)
    for k in (1, 2):
        print('비트 %d개 뒤집기: %d / %d 가지를 잡음'
              % ((k,) + flips_caught(f, k)))
    for kb in (150, 300, 600):
        print('DShot%-4d 한 프레임 %6.2f µs' % (kb, frame_us(kb)))
