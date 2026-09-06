# -*- coding: utf-8 -*-
"""세이브와 CRC — SPEC §11.

   전부 빅 엔디언이다. 리틀 엔디언을 쓰면 언어마다 바이트 순서 함수가 달라
   같은 세이브를 만들었는지 확인하기가 번거로워진다. 손으로 시프트하면 어디서든 같다.
"""
from .fixed import xor8, xor16

CRC_POLY = 0x1021
CRC_INIT = 0xFFFF


def _make_table():
    """CRC-16/CCITT-FALSE 표. 다항식 나눗셈을 바이트 단위로 미리 접어 둔 것이다.

       GF(2) 위의 다항식 나눗셈이라 뺄셈이 곧 xor 다. 자리 올림이 없어서
       하드웨어에서도 시프트 레지스터 하나면 끝난다 — 그게 CRC 가 퍼진 이유다.
    """
    tbl = []
    for i in range(256):
        c = i * 256
        for _ in range(8):
            hi = c >= 32768
            c = (c * 2) % 65536
            if hi:
                c = xor16(c, CRC_POLY)
        tbl.append(c)
    return tbl


CRC_TBL = _make_table()


def crc16(data):
    """표 구동 CRC. 한 바이트에 xor 두 번과 표 조회 한 번.

       (c*256) mod 65536 은 하위 바이트가 0 이므로 16비트 xor 가 필요 없다 —
       상위 바이트만 8비트로 xor 하면 된다. 그래서 xor16 대신 xor8 을 쓴다.
    """
    c = CRC_INIT
    for b in data:
        t = CRC_TBL[xor8(c // 256, b)]
        c = xor8(c % 256, t // 256) * 256 + t % 256
    return c


# ---------------------------------------------------------------- 정수 인코딩
def i32_to_u32(v):
    return v % 4294967296


def u32_to_i32(v):
    return v - 4294967296 if v >= 2147483648 else v


def _u8(out, v):
    out.append(v % 256)


def _u16(out, v):
    out.append((v // 256) % 256)
    out.append(v % 256)


def _u32(out, v):
    v = v % 4294967296
    out.append(v // 16777216)
    out.append((v // 65536) % 256)
    out.append((v // 256) % 256)
    out.append(v % 256)


class Reader(object):
    __slots__ = ('d', 'i')

    def __init__(self, d):
        self.d = d
        self.i = 0

    def u8(self):
        v = self.d[self.i]
        self.i += 1
        return v

    def u16(self):
        return self.u8() * 256 + self.u8()

    def u32(self):
        return self.u16() * 65536 + self.u16()

    def i32(self):
        return u32_to_i32(self.u32())


MAGIC = b'ISO1'


def pack_state(g):
    """게임 상태를 바이트열로. 끝에 CRC 2바이트가 붙는다."""
    out = bytearray(MAGIC)
    _u32(out, g.tick_n)
    _u32(out, g.rng.s)
    _u32(out, i32_to_u32(g.cam_x))
    _u32(out, i32_to_u32(g.cam_y))
    _u16(out, len(g.ents))
    for e in g.ents:
        _u8(out, e.kind)
        _u32(out, i32_to_u32(e.fx))
        _u32(out, i32_to_u32(e.fy))
        _u8(out, e.h)
        _u16(out, e.hp)
        _u16(out, e.maxhp)
        _u8(out, e.lv)
        _u32(out, e.xp)
        _u8(out, e.atk)
        _u8(out, e.dfn)
        _u8(out, e.armor)
        _u8(out, e.dirn)
        _u8(out, e.alive)
    # 안개는 타일 4개에 1바이트. 2비트씩 접어 넣는다.
    bits = g.fog.bits
    n = len(bits)
    _u16(out, (n + 3) // 4)
    i = 0
    while i < n:
        b = 0
        for k in range(4):
            v = bits[i + k] if i + k < n else 0
            b += (v % 4) * (1 << (2 * k))
        out.append(b)
        i += 4
    _u16(out, crc16(bytes(out)))
    return bytes(out)


def unpack_state(data, g):
    """세이브를 게임에 되돌린다. CRC 가 맞지 않으면 ValueError."""
    if data[:4] != MAGIC:
        raise ValueError('세이브 매직이 다르다')
    want = data[-2] * 256 + data[-1]
    if crc16(data[:-2]) != want:
        raise ValueError('세이브가 손상됐다 (CRC 불일치)')
    r = Reader(data)
    r.i = 4
    g.tick_n = r.u32()
    g.rng.s = r.u32()
    g.cam_x = r.i32()
    g.cam_y = r.i32()
    cnt = r.u16()
    if cnt != len(g.ents):
        raise ValueError('엔티티 수가 %d 여야 하는데 %d' % (len(g.ents), cnt))
    for e in g.ents:
        e.kind = r.u8()
        e.fx = r.i32()
        e.fy = r.i32()
        e.h = r.u8()
        e.hp = r.u16()
        e.maxhp = r.u16()
        e.lv = r.u8()
        e.xp = r.u32()
        e.atk = r.u8()
        e.dfn = r.u8()
        e.armor = r.u8()
        e.dirn = r.u8()
        e.alive = r.u8()
    nb = r.u16()
    bits = g.fog.bits
    n = len(bits)
    for j in range(nb):
        b = r.u8()
        for k in range(4):
            i = j * 4 + k
            if i < n:
                bits[i] = (b // (1 << (2 * k))) % 4
    # 비트만 되돌리고 누적 개수를 그대로 두면, 되돌린 뒤의 트레이스가
    # 복원된 상태의 함수가 아니게 된다. 개수는 비트에서 다시 센다.
    g.fog.recount()
    return g
