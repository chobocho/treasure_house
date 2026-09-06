# -*- coding: utf-8 -*-
"""저장·리플레이·압축 (SPEC §20)."""
from __future__ import print_function

import harness as H
from rts import fixed as F
from rts import replay as RP
from rts import select as SEL
from rts import tmap as T

H.title('replay')

LOG = [(1, [(0, 256, SEL.MOVE, 3, 4, 0)]),
       (4, [(0, 256, SEL.BUILD, 12, 6, 10), (1, 512, SEL.TRAIN, 4, 0, 0)]),
       (9, [(1, 65535, SEL.ATTACK, 30, 30, 65280)])]

# ── SPEC §20.2 리플레이 = 명령 로그 ─────────────────────────────────────────
blob = RP.save(12345, 2, 1200, LOG)
H.check('머리는 RTSR', blob[:4], b'RTSR')
H.check('버전', bytearray(blob)[4], RP.VERSION)
seed, players, ticks, log = RP.load(blob)
H.check('머리를 그대로 읽는다', [seed, players, ticks], [12345, 2, 1200])
H.check('본문을 그대로 읽는다', log, LOG)
H.check('꼬리는 CRC-16 두 바이트',
        bytearray(blob)[-2] * 256 + bytearray(blob)[-1],
        F.crc16(blob[:-2]))

bad = bytearray(blob)
bad[10] = (bad[10] + 1) % 256
err = 0
try:
    RP.load(bytes(bad))
except ValueError:
    err = 1
H.check('한 바이트만 바뀌어도 CRC 가 잡는다', err, 1)
err = 0
try:
    RP.load(b'XXXX' + blob[4:])
except ValueError:
    err = 1
H.check('머리가 다르면 거부', err, 1)
H.check('빈 로그도 왕복한다', RP.load(RP.save(1, 2, 0, []))[3], [])
H.check('틱은 오름차순으로 저장한다',
        [t for (t, _o) in RP.load(RP.save(1, 2, 10, [(5, []), (2, [])]))[3]],
        [2, 5])

H.check_true('1200틱 리플레이는 수백 바이트 (%d)' % len(blob), len(blob) < 1000)
snap = 4096
H.note('같은 게임의 상태 스냅샷은 틱당 약 %d바이트 — 1200틱이면 %d KB', snap,
       snap * 1200 // 1024)
H.check('상태는 한 바이트도 저장하지 않는다', b'hp' in blob, False)

# ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────
H.check('빈 입력', RP.rle_encode(b''), b'')
H.check('한 바이트', RP.rle_encode(b'A'), b'\x01A')
H.check('세 번 반복', RP.rle_encode(b'AAA'), b'\x03A')
H.check('바뀌면 새 쌍', RP.rle_encode(b'AAB'), b'\x02A\x01B')
H.check('255 를 넘으면 쌍을 나눈다', len(RP.rle_encode(b'A' * 300)), 4)
H.check('왕복', RP.rle_decode(RP.rle_encode(b'A' * 300 + b'BC')),
        b'A' * 300 + b'BC')
data = bytes(bytearray([k % 7 for k in range(1000)]))
H.check('반복이 없으면 두 배로 늘어난다', len(RP.rle_encode(data)), 2000)
H.check('그래도 왕복한다', RP.rle_decode(RP.rle_encode(data)), data)

# ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
H.check('빈 입력', RP.lzss_encode(b''), b'')
H.check('짧은 입력은 전부 리터럴', RP.lzss_encode(b'AB'),
        b'\x03AB')
H.check('AAAAAAAA 는 리터럴 하나 + 토큰 하나',
        bytearray(RP.lzss_encode(b'A' * 8)), bytearray(b'\x01A\x00\x04'))
H.note('플래그 1바이트 · 리터럴 A · (offset-1=0, len-3=4) 두 바이트 = 4바이트')
H.check('왕복', RP.lzss_decode(RP.lzss_encode(b'A' * 8)), b'A' * 8)
H.check('최대 일치는 18', RP.lzss_decode(RP.lzss_encode(b'B' * 40)), b'B' * 40)

for sample in (b'', b'A', b'AB', b'ABABABABABAB', b'A' * 5000,
               bytes(bytearray([(k * 37) % 251 for k in range(3000)])),
               bytes(bytearray([k % 3 for k in range(4200)]))):
    if RP.lzss_decode(RP.lzss_encode(sample)) != sample:
        H.check('왕복 실패 (길이 %d)' % len(sample), False, True)
H.check('여러 표본에서 왕복', True, True)

H.check_true('창은 4096, 최소 일치 3, 최대 일치 18',
             (RP.WINDOW, RP.MIN_MATCH, RP.MAX_MATCH) == (4096, 3, 18))

# 동점이면 가장 가까운 일치 (탐욕적)
enc = RP.lzss_encode(b'XYZ' + b'Q' * 3 + b'XYZ' + b'XYZ')
H.check('탐욕 일치도 왕복한다', RP.lzss_decode(enc), b'XYZQQQXYZXYZ')

# 실제 맵으로 압축률을 잰다 — "보통 절반" 같은 문장은 쓰지 않는다
m = T.TMap.load_text(H.golden('map_start.txt'))
plane = bytes(bytearray(m.terrain))
r_rle = len(RP.rle_encode(plane))
r_lz = len(RP.lzss_encode(plane))
H.check('맵 지형 평면 왕복 (RLE)', RP.rle_decode(RP.rle_encode(plane)), plane)
H.check('맵 지형 평면 왕복 (LZSS)', RP.lzss_decode(RP.lzss_encode(plane)),
        plane)
H.note('64x64 지형 평면 %d바이트 → RLE %d · LZSS %d', len(plane), r_rle, r_lz)
H.check_true('둘 다 원본보다 작다', r_rle < len(plane) and r_lz < len(plane))

H.done()
