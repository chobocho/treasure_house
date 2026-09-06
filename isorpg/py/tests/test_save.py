# -*- coding: utf-8 -*-
"""저장 — CRC 검증값, 왕복, 손상 검출."""
from __future__ import print_function

import harness as H
from isorpg import game as G
from isorpg import save as S

H.title('save')

H.check('crc16 빈 입력', S.crc16(b''), 0xFFFF)
H.check('crc16 "123456789"', S.crc16(b'123456789'), 0x29B1)
H.check('crc16 "A"', S.crc16(b'A'), 0xB915)
H.check('crc16 0x00..0F', S.crc16(bytes(range(16))), 0x3B37)
H.check('표 크기', len(S.CRC_TBL), 256)
H.check('표 앞 4개', list(S.CRC_TBL[:4]), [0, 4129, 8258, 12387])

# 한 비트만 바꿔도 값이 바뀌는가
base = S.crc16(b'ISORPG-SAVE')
diff = 0
for i in range(11):
    for b in range(8):
        d = bytearray(b'ISORPG-SAVE')
        d[i] ^= (1 << b)
        if S.crc16(bytes(d)) != base:
            diff += 1
H.check('1비트 변화 88가지 모두 다른 CRC', diff, 88)

# ---- 상태 왕복
g = G.Game()
for _ in range(30):
    g.tick()
blob = S.pack_state(g)
H.check('매직', blob[:4], b'ISO1')
H.check_true('CRC 가 뒤에 붙는다', S.crc16(blob[:-2]) == (blob[-2] << 8) | blob[-1])

g2 = G.Game()
S.unpack_state(blob, g2)
H.check('왕복 후 다시 저장한 바이트가 같다', S.pack_state(g2), blob)
H.check('틱', g2.tick_n, g.tick_n)
H.check('난수 상태', g2.rng.s, g.rng.s)
H.check('플레이어 좌표', (g2.ents[0].fx, g2.ents[0].fy), (g.ents[0].fx, g.ents[0].fy))
H.check('안개', bytes(g2.fog.bits), bytes(g.fog.bits))

# ---- 복원한 뒤 이어서 돌리면 같은 결과인가
for _ in range(20):
    g.tick()
    g2.tick()
H.check('복원 후 20틱 진행 결과가 같다', S.pack_state(g2), S.pack_state(g))

# ---- 손상 검출
bad = bytearray(blob)
bad[10] ^= 0xFF
g3 = G.Game()
try:
    S.unpack_state(bytes(bad), g3)
    H.check('손상된 세이브를 거부', 'no error', 'ValueError')
except ValueError:
    H.check('손상된 세이브를 거부', 'ValueError', 'ValueError')

# ---- 음수 좌표 (i32 2의 보수)
H.check('u32 왕복 -1', S.i32_to_u32(-1), 4294967295)
H.check('u32 왕복 -65536', S.u32_to_i32(S.i32_to_u32(-65536)), -65536)
H.check('u32 왕복 최대', S.u32_to_i32(S.i32_to_u32(2147483647)), 2147483647)
H.check('u32 왕복 최소', S.u32_to_i32(S.i32_to_u32(-2147483648)), -2147483648)

H.done()
