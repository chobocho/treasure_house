# -*- coding: utf-8 -*-
"""PC 스피커 — 분주값·음표표·사각파 (SPEC §21)."""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import fixed as F
from rts import speaker as SP

H.title('speaker')

g = H.golden('prim.txt').split('\n')

# ── 골든 14절 분주값 표 ─────────────────────────────────────────────────────
i = g.index('== 14. PIT 분주값 ==') + 2
bad = 0
n = 0
while i < len(g) and g[i].strip():
    name, f, div, act, diff = g[i].split()
    f, div, act, diff = int(f), int(div), int(act), int(diff)
    got = [SP.NOTE_NAME[n], SP.NOTE_HZ[n], SP.divisor(f), SP.actual100(f)]
    if got != [name, f, div, act]:
        bad += 1
        H.note('%s 기대 %s 실제 %s', name, [name, f, div, act], got)
    if act - f * 100 != diff:
        bad += 1
    n += 1
    i += 1
H.check('골든 14절 %d음' % n, bad, 0)
H.check('24음 (C4..B5)', n, 24)
H.check('A4 는 440 Hz', SP.NOTE_HZ[SP.NOTE_NAME.index('A4')], 440)
H.check('C4 는 262 Hz (261.63 반올림)', SP.NOTE_HZ[0], 262)

# ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
H.check('분주값은 반올림 나눗셈', SP.divisor(440),
        F.floordiv(C.PIT_HZ + 220, 440))
H.check('1 Hz 는 분주값이 PIT 클럭 그대로', SP.divisor(1), C.PIT_HZ)
H.check('분주값은 1 아래로 내려가지 않는다', SP.divisor(10000000), 1)
H.check('실제 주파수는 몫과 나머지로만 낸다', SP.actual(440),
        (C.PIT_HZ // SP.divisor(440), C.PIT_HZ % SP.divisor(440)))
H.check_true('440 Hz 의 실제 값은 439.96 Hz', SP.actual100(440) == 43996)
H.note('센트 오차는 로그가 필요해 엔진이 아니라 gen_prim 이 낸다')
H.check('PIT_HZ 는 반올림값 — 정확한 값은 14.31818MHz/12 = 1193181.8181…',
        C.PIT_HZ, 1193182)

# ── SPEC §21.3 사각파 ───────────────────────────────────────────────────────
H.check('샘플레이트', SP.SAMPLE_RATE, 22050)
half = SP.half_period(440)
H.check('반주기 = 22050 / (2 · 실제주파수)', half,
        F.floordiv(SP.SAMPLE_RATE, 2 * SP.actual(440)[0]))
pcm = SP.square(440, 100)
H.check('요청한 만큼 샘플이 나온다', len(pcm), 100)
H.check('진폭은 두 값뿐 (듀티비 고정 — 음량 조절이 없었다)',
        sorted(set(bytearray(pcm))), [0x40, 0xC0])
H.check('첫 반주기는 같은 값', len(set(bytearray(pcm)[:half])), 1)
H.check('반주기 뒤에 뒤집힌다',
        bytearray(pcm)[0] != bytearray(pcm)[half], True)
H.check('쉼표는 무음 (0x80)', sorted(set(bytearray(SP.square(0, 50)))), [0x80])
H.check('길이 0 이면 빈 소리', SP.square(440, 0), b'')

# ── WAV ─────────────────────────────────────────────────────────────────────
wav = SP.wav(pcm)
H.check('헤더는 44바이트', len(wav), 44 + len(pcm))
H.check('RIFF/WAVE', [wav[:4], wav[8:12]], [b'RIFF', b'WAVE'])
H.check('fmt 청크', wav[12:16], b'fmt ')
H.check('data 청크', wav[36:40], b'data')
b = bytearray(wav)
H.check('PCM · 모노 · 8비트', [b[20], b[22], b[34]], [1, 1, 8])
H.check('샘플레이트가 머리에 들어간다',
        b[24] + b[25] * 256 + b[26] * 65536 + b[27] * 16777216, SP.SAMPLE_RATE)
H.check('RIFF 크기 = 전체 - 8',
        b[4] + b[5] * 256 + b[6] * 65536 + b[7] * 16777216, len(wav) - 8)

tune = SP.tune([(SP.NOTE_HZ[0], 20), (0, 5), (SP.NOTE_HZ[12], 20)])
H.check('연속 연주는 이어 붙인 것', len(tune), 44 + 45)
H.check_true('바이트 해시가 결정론적 (%08X)' % F.fnv1a(tune),
             F.fnv1a(tune) == F.fnv1a(SP.tune([(SP.NOTE_HZ[0], 20), (0, 5),
                                               (SP.NOTE_HZ[12], 20)])))
H.note('소리를 재생하지 않는다 — 헤드리스이고, 바이트가 같으면 소리도 같다')

H.done()
