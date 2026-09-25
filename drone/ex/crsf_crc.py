# -*- coding: utf-8 -*-
"""CRSF 틀 하나를 싸고 푼다 — 동기 바이트·길이·유형·내용·CRC8 (6부).

TBS CRSF 규격: 틀은 64바이트 이하, 길이 칸은 유형부터 CRC 까지의
바이트 수(2–62), CRC 는 유형과 내용만 덮는다. 다항식
x⁷+x⁶+x⁴+x²+1(0xD5). 규격은 256칸 표로 계산하지만 여기서는 표 없이
비트마다 나눈다 — 시험이 규격 표의 첫 줄·끝 줄과 대조한다.
시간 O(8 · 바이트 수).
"""
SYNC = 0xC8
RC_CHANNELS = 0x16


def crc8(data, crc=0):
    """MSB 먼저, 다항식 0xD5. 바이트마다 여덟 번 나눈다."""
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0xD5) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def frame(kind, payload):
    """[동기, 길이, 유형, 내용…, CRC8]."""
    body = bytes([kind]) + bytes(payload)
    return bytes([SYNC, len(body) + 1]) + body + bytes([crc8(body)])


def check(f):
    """(유형, 내용) — 길이나 CRC 가 틀리면 ValueError."""
    n = f[1]
    if not 2 <= n <= 62 or len(f) < n + 2:
        raise ValueError('길이 칸이 범위 밖')
    body = f[2:1 + n]
    if crc8(body) != f[1 + n]:
        raise ValueError('CRC8 불일치')
    return body[0], bytes(body[1:])


def us_to_ticks(us):
    """규격의 US_TO_TICKS — C 의 정수 나눗셈(0 쪽으로 버림)."""
    return int((us - 1500) * 8 / 5) + 992


def ticks_to_us(t):
    """규격의 TICKS_TO_US."""
    return int((t - 992) * 5 / 8) + 1500


def frame_time_us(nbytes, baud):
    """8N1 — 바이트마다 시작·정지 비트를 더해 10비트."""
    return nbytes * 10 / baud * 1e6


if __name__ == '__main__':
    sticks = [us_to_ticks(u) for u in (1500, 1500, 1000, 1500)]
    print('스틱 1500/1500/1000/1500 µs → 틱', sticks)
    f = frame(RC_CHANNELS, bytes(range(22)))
    print('틀', len(f), '바이트:', f.hex(' '))
    print('풀기:', check(f)[0] == RC_CHANNELS, 'CRC8 = 0x%02X' % f[-1])
    print('416666 보에서 %.1f µs' % frame_time_us(len(f), 416666))
