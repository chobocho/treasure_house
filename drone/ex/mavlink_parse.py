# -*- coding: utf-8 -*-
"""HEARTBEAT 한 통을 우리 손으로 싸고 다시 푼다 (MAVLink 2, 6부).

체크섬은 CRC-16/MCRF4XX(x25). 메시지 정의에서 CRC_EXTRA 를 계산해
체크섬 끝에 한 바이트 더 섞는다 — 보내는 쪽과 받는 쪽의 정의가
다르면 체크섬이 어긋난다.
"""
import struct

MAGIC = 0xFD
# 전송 순서: 큰 형부터, 같은 크기는 XML 정의 순서 (uint8_t_mavlink_
# version 은 생성기가 uint8_t 로 읽는다)
FIELDS = [('uint32_t', 'custom_mode'), ('uint8_t', 'type'),
          ('uint8_t', 'autopilot'), ('uint8_t', 'base_mode'),
          ('uint8_t', 'system_status'), ('uint8_t', 'mavlink_version')]


def x25(data, crc=0xFFFF):
    """checksum.h 의 crc_accumulate 를 바이트마다."""
    for b in data:
        tmp = b ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3)
               ^ (tmp >> 4)) & 0xFFFF
    return crc


def crc_extra(name, fields):
    """메시지 이름과 필드(형·이름)를 전송 순서로 x25 에 넣어 한
    바이트로."""
    crc = x25((name + ' ').encode())
    for typ, field in fields:
        crc = x25((typ + ' ').encode(), crc)
        crc = x25((field + ' ').encode(), crc)
    return (crc & 0xFF) ^ (crc >> 8)


EXTRA = crc_extra('HEARTBEAT', FIELDS)


def pack(seq, sysid, compid, fields):
    """HEARTBEAT(메시지 id 0) 한 통. 끝의 0 바이트는 잘라 보낸다."""
    body = struct.pack('<IBBBBB', *fields)
    while len(body) > 1 and body[-1] == 0:
        body = body[:-1]
    head = struct.pack('<BBBBBB', len(body), 0, 0, seq, sysid, compid)
    head += (0).to_bytes(3, 'little')                 # msgid = 0
    crc = x25(head + body + bytes([EXTRA]))
    return bytes([MAGIC]) + head + body + struct.pack('<H', crc)


def unpack(frame):
    """(seq, sysid, compid, 필드 여섯) — 체크섬이 틀리면 ValueError."""
    n = frame[1]
    body = frame[10:10 + n]
    want = struct.unpack('<H', frame[10 + n:12 + n])[0]
    if x25(frame[1:10 + n] + bytes([EXTRA])) != want:
        raise ValueError('체크섬 불일치')
    # 잘린 0 을 되살린다
    body = body + bytes(9 - len(body))
    return frame[4], frame[5], frame[6], struct.unpack('<IBBBBB', body)


if __name__ == '__main__':
    print('CRC_EXTRA(HEARTBEAT) =', EXTRA)
    f = pack(7, 1, 1, (0, 2, 12, 0x81, 4, 3))
    print('패킷', len(f), '바이트:', f.hex(' '))
    print('풀기:', unpack(f))
    bad = bytearray(f)
    bad[12] ^= 0x01                                   # 한 비트 뒤집기
    try:
        unpack(bytes(bad))
    except ValueError as e:
        print('한 비트 뒤집은 패킷:', e)
