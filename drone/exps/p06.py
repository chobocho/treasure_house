# -*- coding: utf-8 -*-
"""6부 — 통신과 소프트웨어. 패킷·CRC·링크 모델·울타리·기록의 수.

'모델' 이라고 적힌 표(자유 공간 손실, 도약, 미션 올리기 손실)는 이
덱이 세운 장난감이고, 거기 넣은 감도·출력 값은 슬라이드가 CITE 로
단 문서의 값이다. 비행은 우리 6자유도 시뮬레이터(sim·cascade)이고
울타리 판정·멈춤 동작은 이 파일의 장난감이지 PX4·ArduPilot 코드가
아니다. 씨앗은 모두 고정한다.
"""
import math
import os
import struct
import sys
from itertools import combinations

from droneshow import cascade, params, rng
from droneshow import quadrotor as QR
from droneshow import quat as Q

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'ex'))
import crsf_crc as CR  # noqa: E402
import geofence as GF  # noqa: E402
import mavlink_parse as MP  # noqa: E402
import rf_link as RF  # noqa: E402
import ulog_mini as U  # noqa: E402

DEG = 180.0 / math.pi
HB = (0, 2, 12, 0x81, 4, 3)      # quad · PX4 · 무장+사용자 모드 · ACTIVE


# ------------------------------------------------ MAVLink 패킷 해부
def mav_bytes(ctx):
    """HEARTBEAT 한 통의 바이트를 칸마다."""
    f = MP.pack(7, 1, 1, HB)
    spans = [(0, 1, 'magic', '패킷 시작(MAVLink 2)'),
             (1, 2, 'len', '페이로드 길이'),
             (2, 3, 'incompat_flags', '0 = 서명 없음'),
             (3, 4, 'compat_flags', ''),
             (4, 5, 'seq', '보낸 차례 7'),
             (5, 6, 'sysid', '시스템 1'),
             (6, 7, 'compid', '구성 요소 1'),
             (7, 10, 'msgid', '24비트 리틀 엔디언 = 0'),
             (10, 14, 'custom_mode', 'uint32 = 0'),
             (14, 15, 'type', '2'),
             (15, 16, 'autopilot', '12'),
             (16, 17, 'base_mode', '0x81 = 128 + 1'),
             (17, 18, 'system_status', '4'),
             (18, 19, 'mavlink_version', '3'),
             (19, 21, 'checksum', 'x25, 낮은 바이트 먼저')]
    rows = [['%d' % a if b == a + 1 else '%d–%d' % (a, b - 1), name,
             f[a:b].hex(' '), why] for a, b, name, why in spans]
    ctx.table('p06_mav_bytes', ['바이트', '칸', '값(16진)', '뜻'], rows)


def mav_trunc(ctx):
    """끝의 0 바이트 자르기 — 필드 값에 따라 len 이 달라진다."""
    cases = [HB, (0, 2, 12, 0, 0, 0), (5, 0, 0, 0, 0, 0), (0,) * 6]
    rows = []
    for c in cases:
        f = MP.pack(0, 1, 1, c)
        rows.append([' '.join('%d' % x for x in c), '%d' % f[1],
                     '%d' % len(f), '%s' % (MP.unpack(f)[3] == c)])
    ctx.table('p06_mav_trunc', ['필드 여섯(전송 순서)', 'len',
                                '패킷 바이트', '되살림'], rows,
              num=(1, 2))


def mav_extra_mismatch(ctx):
    """받는 쪽 CRC_EXTRA 가 다르면 — 같은 바이트도 버려진다."""
    f = MP.pack(7, 1, 1, HB)
    n = f[1]
    want = struct.unpack('<H', f[10 + n:12 + n])[0]
    lines = ['# exps/p06.py mav_extra_mismatch — 같은 패킷, 다른 정의',
             '보낸 쪽 CRC_EXTRA %d, 실린 체크섬 0x%04X' % (MP.EXTRA, want)]
    xml_order = [MP.FIELDS[i] for i in (1, 2, 3, 0, 4, 5)]
    for label, extra in (('같은 정의', MP.EXTRA),
                         ('XML 순서로 잘못 정렬',
                          MP.crc_extra('HEARTBEAT', xml_order))):
        got = MP.x25(f[1:10 + n] + bytes([extra]))
        lines.append('%-18s CRC_EXTRA %3d → 0x%04X %s'
                     % (label, extra, got,
                        '받음' if got == want else '버림(체크섬 불일치)'))
    ctx.text('p06_mav_mismatch', '\n'.join(lines))


# ------------------------------------------------ CRC 의 선형성
def x25_zero(data):
    """초깃값 0 의 x25 — 오류 패턴이 체크섬에 주는 몫(선형 부분)."""
    return MP.x25(data, 0)


def crc_linear(ctx):
    """체크섬 차이는 오류 패턴에만 달렸다 — 메시지와 무관."""
    r = rng.Rng(6)
    lines = ['# exps/p06.py crc_linear — 18바이트 메시지 셋, 씨앗 6']
    msgs = [bytes(r.next() & 0xFF for _ in range(18)) for _ in range(3)]
    a, b, c = msgs
    abc = bytes(x ^ y ^ z for x, y, z in zip(a, b, c))
    lhs = MP.x25(a) ^ MP.x25(b) ^ MP.x25(c)
    lines.append('x25(a)^x25(b)^x25(c) = 0x%04X' % lhs)
    lines.append('x25(a^b^c)           = 0x%04X' % MP.x25(abc))
    for pos in (0, 77, 143):
        e = bytearray(18)
        e[pos // 8] = 1 << (pos % 8)
        diffs = set()
        for m in msgs:
            bad = bytes(x ^ y for x, y in zip(m, e))
            diffs.add(MP.x25(m) ^ MP.x25(bad))
        lines.append('비트 %3d 뒤집기: 체크섬 차이 %s, 초깃값 0 의 '
                     'x25(e) = 0x%04X'
                     % (pos, ' '.join('0x%04X' % d for d in diffs),
                        x25_zero(bytes(e))))
    ctx.text('p06_crc_linear', '\n'.join(lines))


def div_bits(data, crc=0xFFFF, poly=0x8408):
    """비트마다 나누기 — 낮은 비트 먼저(반사형) 다항식 0x8408.

    0x8408 을 거꾸로 읽으면 0x1021 = x¹⁶+x¹²+x⁵+1 (x¹⁶ 은 암묵)."""
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ poly if crc & 1 else crc >> 1
    return crc


def crc_poly(ctx):
    """checksum.h 의 바이트 공식(x25)이 곧 0x8408 나눗셈임을 잰다."""
    r = rng.Rng(16)
    same = 0
    for _ in range(1000):
        m = bytes(r.next() & 0xFF for _ in range(1 + r.next() % 40))
        same += MP.x25(m) == div_bits(m)
    rev = int('{:016b}'.format(0x8408)[::-1], 2)
    terms = [16] + [k for k in range(15, -1, -1) if rev >> k & 1]
    ctx.text('p06_crc_poly', '\n'.join([
        '# exps/p06.py crc_poly — 무작위 메시지 1000개(1–40바이트)',
        'x25 == 비트마다 0x8408 로 나눈 나머지: %d/1000' % same,
        '0x8408 을 거꾸로 = 0x%04X → 항: %s (%d개)'
        % (rev, ' + '.join('x^%d' % k if k else '1' for k in terms),
           len(terms))]))


def syndromes(nbytes, lin, crc_bits):
    """비트 자리마다 '그 비트만 뒤집혔을 때 체크섬 비교가 틀어지는
    양'. 데이터 비트는 선형 부분 lin(e), 체크섬 칸의 비트는 그 자리."""
    out = []
    for i in range(8 * nbytes):
        e = bytearray(nbytes)
        e[i // 8] = 1 << (i % 8)
        out.append(lin(bytes(e)))
    return out + [1 << j for j in range(crc_bits)]


def weight_counts(s, kmax):
    """무게 k 오류 가운데 못 잡는(신드롬 XOR 이 0 인) 수, k = 1…kmax.

    무게 1·2·3 은 모두 세고, 무게 4 는 쌍의 XOR 이 같은 두 쌍으로 센다
    (모든 신드롬이 서로 다르면 한 네 벌을 세 번 센다). O(n²)."""
    n = len(s)
    out = [(1, n, sum(1 for x in s if x == 0))]
    pair = {}
    for i, j in combinations(range(n), 2):
        v = s[i] ^ s[j]
        pair[v] = pair.get(v, 0) + 1
    out.append((2, n * (n - 1) // 2, pair.get(0, 0)))
    if kmax >= 3:
        where = {}
        for k, x in enumerate(s):
            where.setdefault(x, []).append(k)
        c3 = 0
        for i, j in combinations(range(n), 2):
            c3 += sum(1 for k in where.get(s[i] ^ s[j], ()) if k > j)
        out.append((3, math.comb(n, 3), c3))
    if kmax >= 4 and len(set(s)) == n:
        c4 = sum(m * (m - 1) // 2 for v, m in pair.items() if v) // 3
        out.append((4, math.comb(n, 4), c4))
    return out


def crc_weights(ctx):
    """L28 의 수 — MAVLink(16비트)와 CRSF(8비트)의 무게별 놓침."""
    mav = syndromes(18, lambda e: x25_zero(e + b'\x00'), 16)
    crsf = syndromes(23, lambda e: CR.crc8(e, 0), 8)
    rows = []
    for name, s, k in (('MAVLink HEARTBEAT (CRC-16)', mav, 4),
                       ('CRSF RC 틀 (CRC-8)', crsf, 4)):
        for w, total, miss in weight_counts(s, k):
            rows.append([name, '%d' % len(s), '%d' % w, '%d' % total,
                         '%d' % miss, '%.2e' % (miss / total)])
    ctx.table('p06_crc_weights', ['패킷', '덮인 비트', '뒤집힌 비트',
                                  '경우 수', '못 잡음', '비율'], rows,
              num=(1, 2, 3, 4, 5))


def crc_bursts(ctx):
    """연속 오류(첫·끝 비트가 뒤집힌 길이 b 의 창) — 그레이 부호로
    한 걸음에 XOR 하나. O(자리 수 · 2^(b−2))."""
    s = syndromes(18, lambda e: x25_zero(e + b'\x00'), 16)
    n, edge = len(s), 8 * 18          # edge: 체크섬 칸이 시작하는 비트
    rows = []
    for b in (2, 8, 12, 16, 17):
        total, miss, cross = 0, 0, 0
        for p in range(n - b + 1):
            ends = s[p] ^ s[p + b - 1]
            mid = s[p + 1:p + b - 1]
            acc, prev, m = ends, 0, 0
            for g in range(1 << (b - 2)):
                gray = g ^ (g >> 1)
                if g:
                    acc ^= mid[(gray ^ prev).bit_length() - 1]
                prev = gray
                total += 1
                m += acc == 0
            miss += m
            if p < edge <= p + b - 1:     # 데이터와 체크섬에 걸친 창
                cross += m
        rows.append(['%d' % b, '%d' % total, '%d' % miss, '%d' % cross,
                     '%d' % (miss - cross)])
    ctx.table('p06_crc_bursts', ['연속 길이 b', '경우 수', '못 잡음',
                                 '그중 경계에 걸친 창', '걸치지 않은 창'],
              rows, num=(0, 1, 2, 3, 4))


# ------------------------------------------------ RC 링크 모델
def rf_bands(ctx):
    rows = []
    for f in (915e6, 2.44e9, 5.8e9):
        lam = RF.wavelength(f)
        rows.append(['%.0f' % (f / 1e6), '%.3f' % lam,
                     '%.1f' % (lam / 4 * 100),
                     '%.2f' % (lam / RF.wavelength(2.44e9)),
                     '%.1f' % RF.fspl_db(1000.0, f)])
    ctx.table('p06_bands', ['주파수 MHz', '파장 m', 'λ/4 cm',
                            '2.44 GHz 파장의 배', '1 km 자유 공간 손실 dB'],
              rows, num=(0, 1, 2, 3, 4))


# (이름, 주파수, 송신 mW, 감도 dBm) — 감도·출력은 슬라이드가 CITE 로
# 단 문서 값(ExpressLRS 신호 상태 표, ArduPilot SiK 문서)
LINKS = [('ELRS 2.4 GHz 500Hz', 2.44e9, 100, -105),
         ('ELRS 2.4 GHz 250Hz', 2.44e9, 100, -108),
         ('ELRS 2.4 GHz 50Hz', 2.44e9, 100, -115),
         ('ELRS 900 MHz 25Hz', 915e6, 100, -123),
         ('SiK 915 MHz', 915e6, 100, -121)]


def rf_budget(ctx):
    """자유 공간 손실만 있는 세상의 거리 — 윗한계."""
    rows = []
    for name, f, mw, sens in LINKS:
        cells = [name, '%.0f' % RF.dbm(mw), '%d' % sens]
        for g in (0.0, 2.0):
            b = RF.budget(RF.dbm(mw), g, g, sens)
            cells.append('%.1f' % (RF.range_m(b, f) / 1000))
        rows.append(cells)
    ctx.table('p06_budget', ['링크', '송신 dBm', '감도 dBm',
                             '거리 km (0 dBi)', '거리 km (2 dBi 둘)'],
              rows, num=(1, 2, 3, 4))
    ctx.text('p06_power', '# exps/p06.py rf_budget — 출력을 두 배로\n'
             '+%.2f dB → 자유 공간 거리 ×%.3f'
             % (RF.dbm(2.0), 10 ** (RF.dbm(2.0) / 20)))


def rf_hop(ctx):
    """방해 채널 k 개: 고정 채널과 도약의 손실, 두 링크의 부딪힘."""
    n = 40
    seq = RF.hops(b'treasure', n, 50)
    rows = []
    for k in (0, 4, 8, 20):
        blocked = set(range(10, 10 + k))
        rows.append(['%d' % k, '%d' % n, '%.3f' % RF.lost(seq, blocked),
                     '%.3f' % (k / n), '0 또는 1'])
    ctx.table('p06_hop_block', ['막힌 채널', '전체 채널',
                                '도약 손실(잰 값)', 'k/N',
                                '고정 채널 손실'], rows,
              num=(0, 1, 2, 3))
    rows = []
    for m in (10, 20, 40, 80):
        a = RF.hops(b'pilot-a', m, 400)
        b = RF.hops(b'pilot-b', m, 400)
        rows.append(['%d' % m, '%.4f' % RF.collide(a, b),
                     '%.4f' % (1 / m)])
    ctx.table('p06_hop_collide', ['채널 N', '두 링크가 겹친 칸(잰 값)',
                                  '1/N'], rows, num=(0, 1, 2))


# ExpressLRS 텔레메트리 대역폭 표(elrs-telem)의 250 Hz 줄 — 문서 값
ELRS_TELEM = [('1:128', 39, 39), ('1:16', 312, 547), ('1:2', 2500, 4922)]


def telem_fit(ctx):
    """1 Hz HEARTBEAT(21바이트) 가 대역의 몇 %를 먹나 — 모델."""
    bits = 8 * len(MP.pack(0, 1, 1, HB))
    rows = []
    for ratio, plain, burst in ELRS_TELEM:
        rows.append([ratio, '%d' % plain, '%d' % burst, '%d' % bits,
                     '%.0f' % (100 * bits / plain),
                     '%.0f' % (100 * bits / burst)])
    ctx.table('p06_telem_fit', ['텔레메트리 비율(250 Hz)', 'bps',
                                'bps(버스트)', 'HEARTBEAT 1 Hz 비트',
                                '차지 %', '차지 %(버스트)'], rows,
              num=(1, 2, 3, 4, 5))


def crsf_timing(ctx):
    rows = []
    for baud in (115200, 416666, 921600):
        us = CR.frame_time_us(26, baud)
        rows.append(['%d' % baud, '%.1f' % us, '%.0f' % (1e6 / us)])
    ctx.table('p06_crsf_time', ['보(baud)', '26바이트 틀 µs',
                                '틀을 잇대면 초당'], rows,
              num=(0, 1, 2))


# ------------------------------------------------ 미션 올리기 모델
def mission_upload(ctx):
    """항목마다 REQUEST→ITEM 한 번이 한 시도, 둘 다 손실률 p.
    시도는 처음 1번 + 다시 5번(문서의 권고 최대). 모델."""
    n_items, trials, tries = 20, 2000, 6
    rows = []
    for p in (0.0, 0.05, 0.2, 0.4):
        r = rng.Rng(60 + int(p * 100))
        fail = sent = 0
        for _ in range(trials):
            for _ in range(n_items):
                for t in range(tries):
                    sent += 1
                    if r.uniform() >= p:           # REQUEST 도착
                        sent += 1
                        if r.uniform() >= p:       # ITEM 도착
                            break
                else:
                    fail += 1
                    break
        q = (1 - p) ** 2
        want = 1 - (1 - (1 - q) ** tries) ** n_items
        rows.append(['%.2f' % p, '%.2f' % (sent / trials),
                     '%.4f' % (fail / trials), '%.4f' % want])
    ctx.table('p06_mission', ['손실률 p', '평균 메시지 수(20항목)',
                              '실패율(잰 값)', '실패율(식)'], rows,
              num=(0, 1, 2, 3))


# ------------------------------------------------ 울타리와 기록
def fly_to_fence(p, v, radius=10.0, check_hz=25, log=None):
    """+x 로 v m/s 로 날다가 울타리 판정(check_hz)이 밖을 보면 그
    자리에 멈춰 선다(Hold 흉내). → (넘어선 거리 최대, 판정 시각)."""
    ctl = cascade.Controller(p)
    s = QR.hover_state(p, [0.0, 0.0, 10.0])
    dt = 1.0 / cascade.PHYS_HZ
    every = cascade.PHYS_HZ // check_hz
    hold, t_hit, worst = None, None, 0.0
    ok = lambda q: GF.in_cylinder(q, (0, 0, 0), radius, 50.0)  # noqa
    for k in range(round((radius / v + 5.0) / dt)):
        t = k * dt
        if hold is None and k % every == 0 and not ok(s[0:3]):
            hold, t_hit = list(s[0:3]), t
            if log:
                log.text('4', int(t * 1e6), 'fence breach: hold')
        ref = ({'p': [v * t, 0.0, 10.0], 'v': [v, 0.0, 0.0]}
               if hold is None else {'p': hold})
        cmd = ctl.update(k, s, ref)
        s = QR.step(ctl.p, s, cmd, dt, (0.0, 0.0, 0.0))
        worst = max(worst, math.hypot(s[0], s[1]) - radius)
        if log and (k + 1) % 10 == 0:
            log.data('pos', [int((k + 1) * dt * 1e6), s[0], s[1], s[2],
                             ref['p'][0]])
    return worst, t_hit


def fence(ctx):
    p = params.load()
    a_tilt = p['g'] * math.tan(math.radians(p['tilt_max_deg']))
    rows = []
    for v in (1.0, 2.0, 3.0, 4.0, 5.0):
        worst, t_hit = fly_to_fence(p, v)
        rows.append(['%.0f' % v, '%.2f' % t_hit, '%.3f' % worst,
                     '%.3f' % GF.stop_distance(v, p['amax']),
                     '%.3f' % GF.stop_distance(v, a_tilt)])
    ctx.table('p06_fence', ['속도 m/s', '판정 시각 s', '넘어선 거리 m',
                            'v²/2a (a=amax 2.0)',
                            'v²/2a (a=g·tan35°)'], rows,
              num=(0, 1, 2, 3, 4))


def pyulog_check(ctx):
    """공식 파서 pyulog 로 우리 ULog 를 읽는다. pyulog 는 numpy 가
    필요해, numpy·pyulog 가 있는 파이썬을 찾아 그것으로 돌린다."""
    import shutil
    import subprocess
    for py in [shutil.which('python3'), shutil.which('python'),
               '/data/data/com.termux/files/usr/bin/python3']:
        if py and subprocess.run([py, '-c', 'import pyulog'],
                                 capture_output=True).returncode == 0:
            ctx.cmd('p06_pyulog', [py, 'tools/pyulog_check.py'])
            return
    raise RuntimeError('pyulog 를 부를 수 있는 파이썬이 없다 '
                       '(pip install pyulog — numpy 필요)')


def ulog_fence(ctx):
    """5 m/s 울타리 비행을 ULog 로 쓰고 다시 읽어 되짚는다."""
    p = params.load()
    w = U.Writer(0)
    w.info('sys_name', 'droneshow')
    w.format('pos', [('uint64_t', 'timestamp'), ('float', 'x'),
                     ('float', 'y'), ('float', 'z'), ('float', 'x_sp')])
    w.subscribe('pos')
    worst, t_hit = fly_to_fence(p, 5.0, log=w)
    b = w.bytes()
    log = U.read(b)
    rows = log['data']['pos']
    far = max(rows, key=lambda r: math.hypot(r['x'], r['y']))
    ev = log['text'][0]
    lines = ['# exps/p06.py ulog_fence — 5 m/s 로 반지름 10 m 울타리에',
             '파일 %d 바이트, 머리 %s' % (len(b), b[:8].hex(' ')),
             '형식: %s' % ' '.join('%s %s;' % f
                                  for f in log['formats']['pos']),
             'pos 기록 %d 줄(50 Hz), 글 %d 줄'
             % (len(rows), len(log['text'])),
             '글: 수준 %s, %.2f s, "%s"' % (ev[0], ev[1] / 1e6, ev[2]),
             '가장 먼 점: %.2f s 에 x = %.3f m (울타리 밖 %.3f m)'
             % (far['timestamp'] / 1e6, far['x'],
                math.hypot(far['x'], far['y']) - 10.0),
             '시뮬레이터가 직접 잰 값: %.3f m (50 Hz 기록 사이의 최대 '
             '포함)' % worst]
    ctx.text('p06_ulog', '\n'.join(lines))


def motor_loss(ctx):
    """t = 2 s 에 모터 1 의 추력이 e 배로 — 원하는 자세 대 실제 자세.

    ArduPilot 로그 진단 문서의 '기계 고장' 모양(원하는 롤·피치와 실제가
    갑자기 벌어짐)을 우리 시뮬레이터로 만든다."""
    p = params.load()
    dt = 1.0 / cascade.PHYS_HZ
    rows = []
    for e in (1.0, 0.8, 0.5, 0.0):
        ctl = cascade.Controller(p)
        s = QR.hover_state(p, [0.0, 0.0, 10.0])
        worst, t_div, z_min = 0.0, None, 10.0
        for k in range(round(4.0 / dt)):
            t = k * dt
            cmd = list(ctl.update(k, s, {'p': [0.0, 0.0, 10.0]}))
            if t >= 2.0:
                cmd[0] *= math.sqrt(e)       # 추력 ∝ Ω² 이므로 √e
            s = QR.step(ctl.p, s, cmd, dt, (0.0, 0.0, 0.0))
            qe = Q.mul(Q.conj(ctl.q_d), s[6:10])
            ang = Q.to_axis_angle(Q.canonical(qe))[1] * DEG
            worst = max(worst, ang)
            if t_div is None and ang > 10.0:
                t_div = t
            z_min = min(z_min, s[2])
        rows.append(['%.1f' % e, '%.2f' % worst,
                     '-' if t_div is None else '%.3f' % (t_div - 2.0),
                     '%.2f' % z_min])
    ctx.table('p06_motor', ['모터 1 추력 배율', '자세 오차 최대 °',
                            '10° 넘은 때(고장 뒤 s)', '가장 낮은 z m'],
              rows, num=(0, 1, 2, 3))


def run(ctx):
    ctx.py('p06_mavlink', 'ex/mavlink_parse.py')
    ctx.py('p06_mavxml', 'ex/mavlink_xml.py')
    ctx.py('p06_crsf', 'ex/crsf_crc.py')
    ctx.py('p06_rf', 'ex/rf_link.py')
    ctx.py('p06_geofence', 'ex/geofence.py')
    ctx.py('p06_ulogdemo', 'ex/ulog_mini.py')
    pyulog_check(ctx)
    mav_bytes(ctx)
    mav_trunc(ctx)
    mav_extra_mismatch(ctx)
    crc_linear(ctx)
    crc_poly(ctx)
    crc_weights(ctx)
    crc_bursts(ctx)
    rf_bands(ctx)
    rf_budget(ctx)
    rf_hop(ctx)
    crsf_timing(ctx)
    telem_fit(ctx)
    mission_upload(ctx)
    fence(ctx)
    ulog_fence(ctx)
    motor_loss(ctx)
