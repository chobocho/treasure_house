#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱에 실을 그림(SVG)을 만든다. 손으로 그리지 않는다.

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

왜 그림도 코드로 만드는가: 곡선을 손으로 그리면 그 곡선이 무엇인지
아무도 확인할 수 없다. 여기서 만드는 곡선은 전부 py/wirelesslib 의
함수를 실제로 불러 얻은 값이고, 구조도는 규격의 숫자에서 나온다.
소스가 바뀌면 그림이 따라 바뀐다.

만든 뒤에는 **눈으로 본다**. `make figs-png` 가 rsvg-convert 로
.svgrender/ 에 PNG 를 뽑는다. 압축 덱은 이 단계에서 28장 중 8장을
고쳤다 — 글자가 겹치거나 축이 잘리는 것은 기계가 못 잡는다.
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIGS = os.path.join(HERE, 'figs')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'py'))

import svgkit as sk                                    # noqa: E402
from svgkit import Axes, Fig                           # noqa: E402
from wirelesslib import (cellular, channel, info, mimo,  # noqa: E402
                         modem, ofdm, orbit, spread, tdma)

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


# ── 2부: 변조와 오류율 ────────────────────────────────────────────


@fig('ber_curves')
def ber_curves():
    f = Fig(230, title='변조별 BER 곡선')
    ax = Axes(f, 40, 14, 196, 170, (0, 26), (1e-6, 0.5),
              ylog=True)
    ax.frame()
    ax.grid(xs=(5, 10, 15, 20, 25),
            ys=(1e-5, 1e-4, 1e-3, 1e-2, 1e-1))
    # BPSK 와 QPSK 는 BER 이 **정확히 같다.** 그대로 그리면 한 곡선이
    # 다른 곡선에 완전히 가려지므로, BPSK 를 파선으로 둔다.
    names = [('bpsk', 'cvd'), ('qpsk', 'cv2'), ('8psk', 'cv3'),
             ('16qam', 'cv4'), ('64qam', 'cv5'), ('256qam', 'cv6')]
    for name, cls in names:
        pts = []
        for i in range(53):
            e = i * 0.5
            v = modem.ber_theory(name, e)
            if v < 1e-7:
                break
            pts.append((e, max(v, 1e-6)))
        ax.curve(pts, cls)
    ax.xticks((0, 5, 10, 15, 20, 25), '%d', 'Eb/N0 [dB]')
    ax.yticks((1e-6, 1e-4, 1e-2, 0.5), '%.0e', 'BER')
    sk.legend(f, 246, 26, [(n, c) for n, c in names])
    f.text(246, 108, 'BPSK 와 QPSK 는', 'cap', 'start')
    f.text(246, 118, 'BER 이 같다', 'cap', 'start')
    return f


@fig('constellations')
def constellations():
    f = Fig(190, title='성상도 — QPSK·16QAM·64QAM')
    import random
    rnd = random.Random(20260916)
    for k, (name, x0) in enumerate((('qpsk', 8), ('16qam', 118),
                                    ('64qam', 228))):
        c = modem.constellation(name)
        cx, cy, r = x0 + 52, 92, 44
        f.rect(x0, 48, 104, 104, 'frame')
        f.line(cx, 48, cx, 152, 'grid')
        f.line(x0, cy, x0 + 104, cy, 'grid')
        y = modem.awgn(modem.modulate(
            [rnd.getrandbits(1) for _ in range(c.k * 60)], c),
            18.0, rnd)
        for v in y:
            f.circle(cx + v.real * r, cy - v.imag * r, 1.0, 'dotn')
        for p in c.points:
            f.circle(cx + p.real * r, cy - p.imag * r, 1.6, 'dot')
        f.text(cx, 40, name, 'key')
        f.text(cx, 168, '%d bit/심볼' % c.k, 'cap')
    f.text(170, 182, '회색 점은 Es/N0 = 18 dB 잡음이 얹힌 수신 표본',
           'cap')
    return f


@fig('mi_vs_capacity')
def mi_vs_capacity():
    f = Fig(220, title='성상도의 상호정보와 섀넌 용량')
    # 섀넌 선은 파선으로 — QPSK 의 청록과 실선끼리는 구별이 안 됐다.
    # y 상한은 30 dB 의 용량(9.97)이 들어오게 10 으로.
    ax = Axes(f, 34, 14, 200, 160, (-5, 30), (0, 10))
    ax.frame()
    ax.grid(xs=(0, 10, 20, 30), ys=(2, 4, 6, 8))
    ax.curve([(s, info.capacity_awgn(s))
              for s in range(-5, 31)], 'cvd')
    for name, cls in (('qpsk', 'cv2'), ('16qam', 'cv4'),
                      ('64qam', 'cv5'), ('256qam', 'cv6')):
        ax.curve([(s, info.constellation_mi(name, float(s), 900,
                                            seed=7))
                  for s in range(-5, 31, 1)], cls)
    ax.xticks((-5, 0, 10, 20, 30), '%d', 'SNR [dB]')
    ax.yticks((0, 2, 4, 6, 8, 10), '%d', 'bit/s/Hz')
    sk.legend(f, 244, 26, [('섀넌', 'cvd'), ('QPSK', 'cv2'),
                           ('16QAM', 'cv4'), ('64QAM', 'cv5'),
                           ('256QAM', 'cv6')])
    f.text(170, 208, '유한 성상도는 k 비트에서 포화한다', 'cap')
    return f


@fig('shannon_limit')
def shannon_limit():
    # 축 제목(y0+h+25=189)과 그림 설명이 같은 줄에 겹쳤다 — 설명은
    # 그 아래(210)로, 곡선은 틀 아래로 새지 않게 y 하한(0.1)부터.
    f = Fig(224, title='스펙트럼 효율과 Eb/N0 한계')
    ax = Axes(f, 40, 14, 262, 150, (-2, 20), (0.1, 10),
              ylog=True)
    ax.frame()
    ax.grid(xs=(0, 5, 10, 15), ys=(0.1, 1, 10))
    pts = []
    e = 0.1
    while e <= 10.0:
        pts.append((info.ebn0_min_db(e), e))
        e *= 1.08
    ax.curve(pts, 'cv')
    x, _y = ax.at(modem.shannon_limit_db(), 0.1)
    f.line(x, 14, x, 164, 'cvd')
    f.text(x + 3, 26, '−1.59 dB', 'key', 'start')
    ax.xticks((0, 5, 10, 15, 20), '%d', 'Eb/N0 [dB]')
    ax.yticks((0.1, 1, 10), '%g', '효율 [bit/s/Hz]')
    f.text(170, 210, '왼쪽은 어떤 부호로도 닿을 수 없는 영역이다',
           'cap')
    return f


# ── 2부: 채널 ─────────────────────────────────────────────────────


@fig('rayleigh_cdf')
def rayleigh_cdf():
    f = Fig(215, title='레일리 포락선의 분포')
    ax = Axes(f, 38, 14, 210, 155, (0, 2.5), (0, 1))
    ax.frame()
    ax.grid(xs=(0.5, 1.0, 1.5, 2.0), ys=(0.25, 0.5, 0.75))
    h = channel.rayleigh(20000, seed=20260916)
    mags = sorted(abs(v) for v in h)
    emp = []
    for i in range(0, len(mags), 200):
        emp.append((mags[i], i / float(len(mags))))
    ax.curve([(r / 40.0, 1 - math.exp(-(r / 40.0) ** 2))
              for r in range(101)], 'cv')
    ax.dots(emp, 1.2, 'dot2')
    ax.xticks((0, 0.5, 1.0, 1.5, 2.0, 2.5), '%.1f', '|h| (실효값 1)')
    ax.yticks((0, 0.5, 1.0), '%.1f', 'CDF')
    sk.legend(f, 256, 40, [('이론', 'cv')])
    f.text(256, 54, '점: 표본 2만 개', 'tick', 'start')
    return f


@fig('doppler_spectrum')
def doppler_spectrum():
    f = Fig(224, title='클라크 도플러 스펙트럼')
    ax = Axes(f, 38, 14, 262, 150, (-1.05, 1.05), (0, 4))
    ax.frame()
    pts = []
    for i in range(1, 400):
        x = -1.0 + 2.0 * i / 400.0
        # 가장자리에서 발산한다 — y 상한(4)에서 자른다. 틀 위로 새면
        # 제목을 덮는다.
        pts.append((x, min(4.0, 1.0 / math.sqrt(max(1e-6, 1 - x * x)))))
    ax.curve(pts, 'cv')
    ax.xticks((-1, -0.5, 0, 0.5, 1), '%.1f', 'f / f_D')
    ax.yticks((0, 1, 2, 3, 4), '%d', 'S(f)')
    f.text(170, 210,
           '가장자리(±f_D)에서 솟는다 — 옆에서 오는 파가 가장 많다',
           'cap')
    return f


@fig('pathloss_models')
def pathloss_models():
    f = Fig(220, title='경로손실 모형 비교')
    ax = Axes(f, 38, 14, 168, 155, (1, 20), (80, 190),
              xlog=True)
    ax.frame()
    ax.grid(xs=(1, 2, 5, 10, 20), ys=(100, 120, 140, 160, 180))
    ds = [1 + i * 0.2 for i in range(96)]
    ax.curve([(d, channel.fspl_db(d * 1000.0, 2.0e9)) for d in ds],
             'cv1')
    ax.curve([(d, channel.hata_db(900.0, 30.0, 1.5, d)) for d in ds],
             'cv2')
    ax.curve([(d, channel.hata_db(900.0, 30.0, 1.5, d, 'suburban'))
              for d in ds], 'cv3')
    ax.curve([(d, channel.cost231_db(1800.0, 30.0, 1.5, d))
              for d in ds], 'cv4')
    ax.curve([(d, channel.tr38901_db('uma', d * 1000.0, 2.0, True))
              for d in ds], 'cv5')
    ax.xticks((1, 2, 5, 10, 20), '%g', '거리 [km]')
    ax.yticks((80, 120, 160, 190), '%d', '손실 [dB]')
    sk.legend(f, 214, 36, [('자유공간 2 GHz', 'cv1'),
                           ('하타 도심 900', 'cv2'),
                           ('하타 교외 900', 'cv3'),
                           ('COST-231 1800', 'cv4'),
                           ('38.901 UMa LOS', 'cv5')])
    return f


# ── 3부: 부호 ─────────────────────────────────────────────────────


@fig('viterbi_trellis')
def viterbi_trellis():
    f = Fig(210, title='비터비 격자 (K=3 예시)')
    states = 4
    steps = 5
    x0, y0, dx, dy = 40, 34, 55, 38
    names = ['00', '01', '10', '11']
    for s in range(states):
        f.text(x0 - 10, y0 + s * dy + 4, names[s], 'tick', 'end')
    for t in range(steps):
        for s in range(states):
            x = x0 + t * dx
            y = y0 + s * dy
            f.circle(x, y, 3.2, 'dot' if (t, s) in
                     ((0, 0), (1, 2), (2, 1), (3, 2), (4, 1))
                     else 'dotn')
    for t in range(steps - 1):
        for s in range(states):
            for u in (0, 1):
                ns = ((s << 1) | u) & 3
                x1, y1 = x0 + t * dx, y0 + s * dy
                x2, y2 = x0 + (t + 1) * dx, y0 + ns * dy
                hot = ((t, s), (t + 1, ns)) in (
                    (((0, 0)), ((1, 2))), (((1, 2)), ((2, 1))),
                    (((2, 1)), ((3, 2))), (((3, 2)), ((4, 1))))
                f.line(x1 + 4, y1, x2 - 4, y2,
                       'tie hot' if hot else 'tie')
    f.text(x0 - 26, y0 - 14, '상태', 'key', 'start')
    f.text(170, 200, '굵은 선이 살아남은 경로 — 비용이 가장 작은 길',
           'cap')
    f.text(170, 190, '단계마다 상태로 들어오는 두 길 중 하나만 남긴다',
           'cap')
    return f


@fig('tanner_graph')
def tanner_graph():
    f = Fig(210, title='LDPC 탄너 그래프')
    vs = 8
    cs = 4
    vx0, cx0 = 30, 30
    dv = (280.0 / (vs - 1))
    dc = (280.0 / (cs - 1))
    edges = [(0, 0), (0, 3), (0, 5), (1, 1), (1, 3), (1, 6),
             (2, 0), (2, 2), (2, 7), (3, 4), (3, 5), (3, 6)]
    for c, v in edges:
        f.line(cx0 + c * dc, 52, vx0 + v * dv, 148, 'tie')
    for c in range(cs):
        f.rect(cx0 + c * dc - 9, 42, 18, 18, 'cell b')
        f.text(cx0 + c * dc, 55, '+', 'key')
    for v in range(vs):
        f.circle(vx0 + v * dv, 156, 7, 'cell a')
        f.text(vx0 + v * dv, 159, str(v), 'tick')
    f.text(14, 34, '검사 노드 (패리티 식)', 'key', 'start')
    f.text(14, 182, '변수 노드 (부호어 비트)', 'key', 'start')
    f.text(170, 200, '선이 드문드문한 것이 "저밀도" 라는 이름의 뜻이다',
           'cap')
    return f


@fig('turbo_encoder')
def turbo_encoder():
    f = Fig(200, title='터보 부호기의 구조')
    # 왼쪽 여백 14, 오른쪽 여백 326 을 넘지 않게 그린다
    f.text(16, 32, '정보 비트', 'key', 'start')
    f.line(16, 40, 250, 40, 'tie hot')
    f.text(326, 36, '→ 계통', 'key', 'end')
    f.rect(60, 62, 104, 26, 'cell a')
    f.text(112, 79, 'RSC 부호기 1', 'tick')
    f.line(112, 40, 112, 62, 'tie')
    f.line(164, 75, 300, 75, 'tie')
    f.text(326, 71, '→ 패리티1', 'key', 'end')
    f.rect(60, 104, 104, 26, 'cell c')
    f.text(112, 121, 'QPP 인터리버', 'tick')
    f.line(40, 40, 40, 117, 'tie')
    f.line(40, 117, 60, 117, 'tie')
    f.rect(60, 146, 104, 26, 'cell a')
    f.text(112, 163, 'RSC 부호기 2', 'tick')
    f.line(112, 130, 112, 146, 'tie')
    f.line(164, 159, 300, 159, 'tie')
    f.text(326, 155, '→ 패리티2', 'key', 'end')
    f.text(232, 100, '부호율 1/3', 'cap')
    f.text(232, 112, '(꼬리 12비트 별도)', 'cap')
    f.text(170, 192,
           '같은 정보를 전혀 다른 차례로 두 번 보호한다 —'
           ' 그것이 전부다', 'cap')
    return f


@fig('polar_butterfly')
def polar_butterfly():
    f = Fig(210, title='폴라 변환의 나비 연산 (N=8)')
    n = 8
    x0, dx = 40, 80
    y0, dy = 26, 22
    for i in range(n):
        f.text(x0 - 10, y0 + i * dy + 3, 'u%d' % i, 'tick', 'end')
        f.text(x0 + 3 * dx + 10, y0 + i * dy + 3, 'x%d' % i, 'tick',
               'start')
        f.line(x0, y0 + i * dy, x0 + 3 * dx, y0 + i * dy, 'ax')
    step = 1
    for stage in range(3):
        xs = x0 + stage * dx + dx / 2.0
        for i in range(n):
            if (i // step) % 2 == 0:
                j = i + step
                f.line(xs, y0 + i * dy, xs, y0 + j * dy, 'tie hot')
                f.circle(xs, y0 + i * dy, 2.4, 'dot2')
                f.circle(xs, y0 + j * dy, 2.4, 'dot2')
        step *= 2
    f.text(170, 200, '같은 나비를 log₂N 단계 되풀이하면 F⊗ⁿ 이 된다',
           'cap')
    return f


# ── 4부: 셀룰러 ───────────────────────────────────────────────────


def _hex(f, cx, cy, r, cls, label=''):
    pts = []
    for k in range(6):
        a = math.radians(60 * k - 30)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    f.poly(pts, cls)
    if label:
        f.text(cx, cy + 3, label, 'tick')


@fig('hex_reuse')
def hex_reuse():
    f = Fig(240, title='육각 재사용 패턴 N=7')
    r = 22
    dx = r * math.sqrt(3)
    dy = r * 1.5
    letters = 'ABCDEFG'
    cls = ['cell a', 'cell b', 'cell c', 'cell d', 'cell e',
           'cell f', 'cell']
    for row in range(-3, 4):
        for col in range(-4, 5):
            cx = 170 + col * dx + (row % 2) * dx / 2.0
            cy = 112 + row * dy
            if not (14 < cx < 326 and 24 < cy < 200):
                continue
            # i=2, j=1 이면 N = 4+2+1 = 7 이다
            k = (col + 2 * row) % 7
            _hex(f, cx, cy, r, cls[k], letters[k])
    f.text(170, 222, 'N = i²+ij+j² = 2²+2·1+1² = 7 · 같은 글자끼리'
                     ' D = √(3N)·R 만큼 떨어져 있다', 'cap')
    return f


@fig('sir_vs_cluster')
def sir_vs_cluster():
    f = Fig(215, title='클러스터 크기와 SIR')
    ax = Axes(f, 38, 14, 202, 150, (0, 22), (0, 30))
    ax.frame()
    ax.grid(ys=(6, 12, 18, 24))
    ns = cellular.cluster_sizes(4)[:10]          # 1 … 21, 축 끝까지
    for gamma, cls in ((2.5, 'cv1'), (3.0, 'cv2'), (3.5, 'cv3'),
                       (4.0, 'cv4')):
        ax.curve([(n, cellular.sir_db(n, gamma)) for n in ns], cls)
        ax.dots([(n, cellular.sir_db(n, gamma)) for n in ns], 1.4)
    x1, y1 = ax.at(0, 18)
    x2, _y = ax.at(22, 18)
    f.line(x1, y1, x2, y1, 'cvd')
    # 왼쪽 위에 둔다 — 오른쪽은 γ=3 곡선이 지나가 글자와 겹친다
    f.text(x1 + 4, y1 - 4, 'AMPS 18 dB', 'key', 'start')
    # 3·4 와 12·13 은 눈금이 겹쳐 읽히지 않았다 — 자주 쓰는 값만 적는다
    ax.xticks((1, 4, 7, 12, 19, 21), '%d', '클러스터 크기 N')
    ax.yticks((0, 10, 20, 30), '%d', 'SIR [dB]')
    sk.legend(f, 250, 30, [('γ=2.5', 'cv1'), ('γ=3', 'cv2'),
                           ('γ=3.5', 'cv3'), ('γ=4', 'cv4')])
    return f


@fig('erlang_b')
def erlang_b():
    f = Fig(215, title='얼랑 B 곡선')
    ax = Axes(f, 40, 14, 202, 150, (0, 40), (1e-3, 1),
              ylog=True)
    ax.frame()
    ax.grid(ys=(1e-2, 1e-1))
    for n, cls in ((5, 'cv1'), (10, 'cv2'), (20, 'cv3'),
                   (30, 'cv4'), (50, 'cv5')):
        pts = [(a * 0.5, max(cellular.erlang_b(a * 0.5, n), 1e-3))
               for a in range(1, 81)]
        ax.curve(pts, cls)
    x1, y1 = ax.at(0, 0.02)
    x2, _ = ax.at(40, 0.02)
    f.line(x1, y1, x2, y1, 'cvd')
    f.text(x2 - 2, y1 - 4, '차단률 2 %', 'key', 'end')
    ax.xticks((0, 10, 20, 30, 40), '%d', '부하 A [얼랑]')
    ax.yticks((1e-3, 1e-2, 1e-1, 1), '%.0e', '차단 확률')
    sk.legend(f, 250, 30, [('N=5', 'cv1'), ('N=10', 'cv2'),
                           ('N=20', 'cv3'), ('N=30', 'cv4'),
                           ('N=50', 'cv5')])
    return f



# ── 6부: GSM ──────────────────────────────────────────────────────


@fig('gsm_frame')
def gsm_frame():
    f = Fig(250, title='GSM 의 시간 구조')
    f.text(16, 24, '① TDMA 프레임 = 8 슬롯 = 60/13 ms ≈ 4.615 ms',
           'key', 'start')
    x0, w = 16, 310
    for i in range(8):
        f.rect(x0 + i * w / 8.0, 32, w / 8.0 - 1, 22,
               'cell a' if i == 2 else 'cell')
        f.text(x0 + (i + 0.5) * w / 8.0, 46, str(i), 'tick')
    f.text(16, 74, '② 슬롯 하나 = 156.25 비트 ≈ 576.9 μs (정상 버스트)',
           'key', 'start')
    fields = tdma.burst_fields('normal')
    total = float(sum(v for _n, v in fields))
    x = 16.0
    for name, v in fields:
        ww = 310.0 * float(v) / total
        cls = {'데이터1': 'cell a', '데이터2': 'cell a',
               '훈련열': 'cell b', '가드': 'cell f'}.get(name, 'cell')
        f.rect(x, 82, max(ww - 0.8, 0.8), 22, cls)
        if ww > 26:
            f.text(x + ww / 2.0, 96, str(v), 'tick')
        x += ww
    f.text(16, 118, '꼬리3 · 데이터57 · S1 · 훈련열26 · S1 ·'
                    ' 데이터57 · 꼬리3 · 가드 8.25', 'cap', 'start')
    f.text(16, 142, '③ 26 멀티프레임(트래픽) = 120 ms 정확히',
           'key', 'start')
    for i in range(26):
        cls = 'cell b' if i == 12 else ('cell f' if i == 25
                                        else 'cell a')
        f.rect(16 + i * 12, 150, 11, 18, cls)
    f.text(16, 182, 'T·T·…·(12=SACCH)·…·(25=쉼)', 'cap', 'start')
    f.text(16, 206, '④ 슈퍼프레임 26×51 = 6.12 s ·'
                    ' 하이퍼프레임 2048 슈퍼프레임', 'key', 'start')
    f.text(16, 222, '   = 2,715,648 프레임 = 3시간 28분 53.76초',
           'cap', 'start')
    f.text(16, 236, '   A5 의 프레임 번호가 한 바퀴 도는 주기다',
           'cap', 'start')
    return f


@fig('gmsk_spectrum')
def gmsk_spectrum():
    f = Fig(228, title='GMSK 와 MSK 의 스펙트럼')
    ax = Axes(f, 40, 14, 200, 150, (0, 2.0), (-70, 5))
    ax.frame()
    ax.grid(xs=(0.5, 1.0, 1.5), ys=(-60, -40, -20, 0))
    import random
    from wirelesslib import dsp
    for bt, cls in ((None, 'cvd'), (0.5, 'cv3'), (0.3, 'cv5')):
        rnd = random.Random(20260916)
        bits = [rnd.getrandbits(1) for _ in range(1024)]
        x = tdma.gmsk_modulate(bits, bt, 8)
        n = dsp.next_pow2(len(x))
        p = dsp.periodogram(x, n)
        peak = max(p)
        pts = []
        # 축 끝(2.0)까지 그린다(k < n/4). 바닥은 y 하한 −70 dB 에
        # 붙인다 — 더 내려가면 곡선이 틀 밖으로 새어 눈금을 덮는다.
        for k in range(1, n // 4):
            fr = k * 8.0 / n
            if fr > 2.0:
                break
            pts.append((fr, 10 * math.log10(max(p[k] / peak, 1e-7))))
        ax.curve(pts, cls)
    ax.xticks((0, 0.5, 1.0, 1.5, 2.0), '%.1f', '주파수 / 비트율')
    ax.yticks((-70, -50, -30, -10, 5), '%d', '[dB]')
    sk.legend(f, 250, 34, [('MSK', 'cvd'), ('BT=0.5', 'cv3'),
                           ('BT=0.3', 'cv5')])
    f.text(170, 214,
           'BT 를 낮추면 이웃 채널이 조용해진다 — 대신 ISI 가 는다',
           'cap')
    return f


# ── 7·9부: 확산 ───────────────────────────────────────────────────


@fig('ovsf_tree')
def ovsf_tree():
    f = Fig(220, title='OVSF 부호 나무')
    levels = [(1, 26), (2, 66), (4, 106), (8, 146)]
    for sf, y in levels:
        f.text(14, y + 4, 'SF=%d' % sf, 'key', 'start')
        for k in range(sf):
            x = 60 + (k + 0.5) * 264.0 / sf
            used = (sf == 4 and k == 1)
            anc = (sf == 2 and k == 0) or (sf == 1 and k == 0)
            blocked = (sf == 8 and k in (2, 3)) or anc
            cls = 'cell b' if used else ('cell f' if blocked
                                         else 'cell a')
            f.circle(x, y, min(9.0, 120.0 / sf), cls)
            if sf <= 4:
                f.text(x, y + 3, str(k), 'tick')
    for sf, y in levels[:-1]:
        ny = dict(levels)[sf * 2]
        for k in range(sf):
            x = 60 + (k + 0.5) * 264.0 / sf
            for c in (2 * k, 2 * k + 1):
                nx = 60 + (c + 0.5) * 264.0 / (sf * 2)
                f.line(x, y + 8, nx, ny - 8, 'tie')
    f.text(170, 182, '분홍: 쓰는 부호 · 회색: 그 때문에 못 쓰는 부호',
           'cap')
    f.text(170, 196, '조상과 자손을 함께 쓸 수 없다 —', 'cap')
    f.text(170, 208, '긴 부호의 앞머리가 짧은 부호와 같아지기 때문이다',
           'cap')
    return f


@fig('is95_forward')
def is95_forward():
    f = Fig(215, title='IS-95 순방향 링크')
    rows = [('파일럿', 'W0', '위상 기준·셀 탐색', 'cell b'),
            ('동기', 'W32', '시각과 롱코드 상태', 'cell c'),
            ('페이징', 'W1~W7', '착신 호출·시스템 정보', 'cell d'),
            ('트래픽', 'W8~W63', '통화 (최대 55개)', 'cell a')]
    for i, (name, w, what, cls) in enumerate(rows):
        y = 30 + i * 30
        f.rect(16, y, 62, 22, cls)
        f.text(47, y + 15, name, 'tick')
        f.rect(84, y, 52, 22, 'cell')
        f.text(110, y + 15, w, 'tick')
        f.text(144, y + 15, what, 'cap', 'start')
    f.line(140, 156, 240, 156, 'tie')
    f.rect(120, 152, 100, 22, 'cell e')
    f.text(170, 167, '합산 → 숏 PN 스크램블', 'tick')
    for i in range(4):
        f.line(78, 41 + i * 30, 120, 158, 'tie')
    f.line(220, 163, 300, 163, 'tie hot')
    f.text(326, 159, '→ 안테나', 'key', 'end')
    f.text(170, 196, '1.2288 Mcps · 왈시 64 · 처리 이득 21 dB', 'cap')
    f.text(170, 208,
           '기지국이 한꺼번에 내보내므로 왈시가 완벽히 직교한다',
           'cap')
    return f


@fig('rake_receiver')
def rake_receiver():
    f = Fig(210, title='RAKE 수신기')
    f.text(16, 24, '수신 신호', 'key', 'start')
    f.line(16, 34, 300, 34, 'tie')
    for i, (d, g) in enumerate(((0, '0 칩'), (1, '3 칩'),
                                (2, '7 칩'))):
        y = 56 + i * 40
        f.rect(46, y, 56, 24, 'cell f')
        f.text(74, y + 16, '지연 %s' % g, 'tick')
        f.rect(114, y, 62, 24, 'cell a')
        f.text(145, y + 16, '역확산', 'tick')
        f.rect(188, y, 62, 24, 'cell c')
        f.text(219, y + 16, '가중 h*', 'tick')
        f.line(74, 34, 74, y, 'tie')
        f.line(102, y + 12, 114, y + 12, 'tie')
        f.line(176, y + 12, 188, y + 12, 'tie')
        f.line(250, y + 12, 276, y + 12, 'tie')
        f.line(276, y + 12, 276, 108, 'tie')
    f.circle(276, 108, 10, 'cell e')
    f.text(276, 112, '+', 'key')
    f.line(286, 108, 310, 108, 'tie hot')
    f.text(326, 104, '판정', 'key', 'end')
    f.text(170, 190, '갈래마다 따로 받아 위상을 맞춰 더한다 —', 'cap')
    f.text(170, 202,
           '다중경로가 잡음이 아니라 다이버시티가 된다', 'cap')
    return f


# ── 10·11부: OFDM 과 자원 그리드 ──────────────────────────────────


@fig('ofdm_subcarriers')
def ofdm_subcarriers():
    f = Fig(228, title='OFDM 부반송파의 직교')
    ax = Axes(f, 30, 20, 280, 120, (-3.5, 3.5), (-0.35, 1.1))
    ax.frame()
    for k in range(-3, 4):
        pts = []
        for i in range(281):
            x = -3.5 + 7.0 * i / 280.0
            t = math.pi * (x - k)
            v = 1.0 if abs(t) < 1e-9 else math.sin(t) / t
            pts.append((x, v))
        ax.curve(pts, 'cv%d' % (abs(k) + 1) if k else 'cv')
        xx, yy = ax.at(k, 1.0)
        f.circle(xx, yy, 2.2, 'dot2')
    ax.xticks((-3, -2, -1, 0, 1, 2, 3), '%d', '부반송파 번호')
    f.text(170, 186,
           '한 부반송파의 꼭대기에서 나머지는 전부 정확히 0 이다',
           'cap')
    f.text(170, 200, '그것이 "직교" 이고, 간격이 1/T 여야 성립한다',
           'cap')
    f.text(170, 214, '주파수가 ε 만큼 어긋나면 이 0 이 깨진다(ICI)',
           'cap')
    return f


@fig('ofdm_cp')
def ofdm_cp():
    f = Fig(190, title='순환 전치가 하는 일')
    f.text(16, 22, '① 보낼 심볼 (FFT 길이 N)', 'key', 'start')
    f.rect(96, 30, 200, 24, 'cell a')
    f.text(196, 46, 'IFFT 출력 N 표본', 'tick')
    f.rect(246, 30, 50, 24, 'cell b')
    f.text(271, 46, '끝 부분', 'tick')
    f.text(16, 84, '② 끝을 잘라 앞에 붙인다', 'key', 'start')
    f.rect(46, 92, 50, 24, 'cell b')
    f.text(71, 108, 'CP', 'tick')
    f.rect(96, 92, 200, 24, 'cell a')
    f.text(196, 108, 'N 표본', 'tick')
    f.line(271, 54, 271, 74, 'tie hot')
    f.line(271, 74, 71, 74, 'tie hot')
    f.line(71, 74, 71, 92, 'tie hot')
    f.text(16, 140, '③ 다중경로가 CP 안에서 끝나면', 'key', 'start')
    f.text(16, 156, '   채널과의 컨볼루션이 순환 컨볼루션이 되어,',
           'cap', 'start')
    f.text(16, 170, '   주파수 영역에서 곱셈 하나로 바뀐다', 'cap',
           'start')
    f.text(16, 184, '   → 부반송파마다 복소수 하나로 등화 끝', 'cap',
           'start')
    return f


@fig('papr_ccdf')
def papr_ccdf():
    f = Fig(215, title='PAPR 의 CCDF')
    ax = Axes(f, 40, 14, 200, 150, (2, 13), (1e-3, 1), ylog=True)
    ax.frame()
    ax.grid(xs=(4, 6, 8, 10, 12), ys=(1e-2, 1e-1))
    levels = [2 + i * 0.25 for i in range(45)]
    for nfft, sc, cls in ((64, False, 'cv1'), (256, False, 'cv3'),
                          (1024, False, 'cv5'), (256, True, 'cv2')):
        vals = ofdm.papr_ccdf(nfft, levels, 400, seed=7, scfdma=sc)
        pts = [(lv, max(v, 1e-3)) for lv, v in zip(levels, vals)
               if v > 0]
        ax.curve(pts, cls)
    ax.xticks((2, 4, 6, 8, 10, 12), '%d', 'PAPR 문턱 [dB]')
    ax.yticks((1e-3, 1e-2, 1e-1, 1), '%.0e', 'P(PAPR > 문턱)')
    sk.legend(f, 250, 30, [('OFDM 64', 'cv1'), ('OFDM 256', 'cv3'),
                           ('OFDM 1024', 'cv5'),
                           ('SC-FDMA 256', 'cv2')])
    f.text(170, 200,
           'SC-FDMA 곡선이 왼쪽에 있다 — 그만큼 증폭기가 싸진다',
           'cap')
    return f


@fig('resource_grid')
def resource_grid():
    # 10부(LTE)에서만 쓴다. LTE 의 슬롯은 7 심볼·0.5 ms 이고 14 심볼은
    # 서브프레임이다 — NR 식 '슬롯 14 심볼' 로 적으면 옆 표와 어긋난다.
    f = Fig(230, title='LTE 자원 그리드')
    f.text(16, 22, '서브프레임 1 ms × PRB 쌍 = 12 부반송파 × 14 심볼',
           'key', 'start')
    x0, y0 = 40, 32
    cw, ch = 19.0, 11.0
    for k in range(12):
        for l in range(14):
            cls = 'cell'
            if l in (2, 11) and k % 3 == 0:
                cls = 'cell b'          # 기준신호
            elif l < 2:
                cls = 'cell d'          # 제어 영역
            f.rect(x0 + l * cw, y0 + k * ch, cw - 0.8, ch - 0.8, cls)
    f.text(30, y0 + 6 * ch, '부반송파', 'axname', 'middle',
           ' transform="rotate(-90 30 %.1f)"' % (y0 + 6 * ch))
    f.text(x0 + 7 * cw, y0 + 12 * ch + 14, 'OFDM 심볼 →', 'axname')
    f.text(16, 206, '주황: 제어 영역 · 분홍: 기준신호 · 흰: 데이터',
           'cap', 'start')
    f.text(16, 220, '슬롯은 7 심볼(0.5 ms). 이 한 칸이 180 kHz × 1 ms',
           'cap', 'start')
    return f


@fig('nr_numerology')
def nr_numerology():
    f = Fig(215, title='NR 뉴머롤로지 — 같은 1 ms 를 어떻게 쪼개나')
    f.text(16, 22, '서브프레임 1 ms 는 μ 와 무관하게 고정이다',
           'key', 'start')
    x0, w = 40, 240          # 오른쪽 '120 kHz' 가 viewBox 340 안에 들게
    for i, mu in enumerate((0, 1, 2, 3)):
        y = 34 + i * 38
        n = ofdm.slots_per_subframe(mu)
        f.text(34, y + 14, 'μ=%d' % mu, 'key', 'end')
        for k in range(n):
            f.rect(x0 + k * w / n, y, w / n - 1.2, 22,
                   'cell a' if k % 2 == 0 else 'cell c')
        f.text(x0 + w + 2, y + 14,
               '%d kHz' % ofdm.scs_khz(mu), 'tick', 'start')
    f.text(16, 196, '부반송파 간격이 두 배가 되면 슬롯이 반이 된다',
           'cap', 'start')
    f.text(16, 208,
           '(15·2^μ kHz ↔ 1/2^μ ms) — 지연과 부담의 맞바꿈이다',
           'cap', 'start')
    return f


# ── 12부: 위성 ────────────────────────────────────────────────────


@fig('orbit_shells')
def orbit_shells():
    f = Fig(240, title='궤도 고도와 편도 지연')
    # 고리 넷이 viewBox 왼쪽·아래로 새고 범례를 가로질렀다 — 가장 큰
    # 고리(r+9+3·11=64)가 x 26~154, y 54~182 안에 들도록 잡는다.
    cx, cy, r = 90, 118, 22
    f.circle(cx, cy, r, 'cell a')
    f.text(cx, cy + 4, '지구', 'tick')
    shells = [(550.0, '저궤도 550 km', 'cv2'),
              (1200.0, '저궤도 1200 km', 'cv3'),
              (20200.0, 'MEO 20,200 km', 'cv4'),
              (35786.0, 'GEO 35,786 km', 'cv5')]
    for i, (h, name, cls) in enumerate(shells):
        rr = r + 9 + i * 11
        f.circle(cx, cy, rr, cls)
        d = orbit.one_way_delay_ms(h, 90.0)
        f.text(160, 44 + i * 22, '%s — 천정 편도 %.2f ms'
               % (name, d), 'tick', 'start')
        f.line(150, 40 + i * 22, 156, 40 + i * 22, cls)
    f.text(170, 200, '고도가 곧 지연이다. 정지궤도는 왕복 238 ms 라',
           'cap')
    f.text(170, 212, 'HARQ 타이머와 RTT 를 그대로 쓸 수 없다.', 'cap')
    f.text(170, 228, '저궤도는 편도 2~4 ms 로 지상망과 비슷해진다.',
           'cap')
    return f


@fig('ntn_geometry')
def ntn_geometry():
    f = Fig(235, title='NTN 기하 — 앙각이 지연을 정한다')
    # 지구는 아래쪽 띠로, 위성은 오른쪽 위로 부채꼴로 펼친다.
    # **각도는 보기 쉽게 과장했다** — 실제 중심각은 15도 안쪽이다.
    gx, gy = 48, 150
    f.raw('<path d="M 14 174 Q 170 150 326 174 L 326 190 L 14 190 Z"'
          ' class="cell a"/>')
    f.circle(gx, gy + 8, 3.2, 'dot')
    f.text(gx, gy + 26, '지상국', 'tick')
    h = 550.0
    rows = [(90.0, 88, 'cv2'), (40.0, 52, 'cv3'), (10.0, 18, 'cv5')]
    for i, (el, deg, cls) in enumerate(rows):
        a_ = math.radians(deg)
        sx = gx + 150 * math.cos(a_)
        sy = gy + 8 - 118 * math.sin(a_)
        f.line(gx, gy + 8, sx, sy, cls)
        f.circle(sx, sy, 3.4, 'dot2')
        yy = 30 + i * 16
        f.text(204, yy, '앙각 %.0f° · %.0f km · %.2f ms'
               % (el, orbit.slant_range_km(h, el),
                  orbit.one_way_delay_ms(h, el)), 'tick', 'start')
        f.line(190, yy - 3, 200, yy - 3, cls)
    f.text(170, 208,
           '같은 위성이라도 앙각이 낮으면 거리가 두 배가 된다.',
           'cap')
    f.text(170, 220,
           '빔 안에서 왕복 지연이 ms 단위로 벌어지므로', 'cap')
    f.text(170, 232, 'Rel-17 NTN 은 공통 TA 를 따로 둔다.'
                     ' (각도는 과장해 그렸다)', 'cap')
    return f


# ── 14부: 세대 ────────────────────────────────────────────────────


@fig('generation_ribbon')
def generation_ribbon():
    """세대가 겹쳐 사는 모습 — 띠를 세대마다 한 줄씩 겹쳐 그린다.

    첫 상용 연도만 잇대어 그리면 '다음 세대가 오면 앞 세대가 꺼진다'
    는 그림이 된다 — 옆 문장이 부정하는 바로 그것이다. 여기서는 띠가
    겹치게 그리고, 끝난 해가 출처로 확인된 1G(AMPS 2008-02, 5부)만
    닫는다. 나머지는 2026 까지 열어 둔다. 행 수는 timeline.tsv 에서
    센다.
    """
    f = Fig(226, title='세대 연표 — 겹쳐 사는 띠')
    x0, x1 = 24, 316
    lo, hi = 1975, 2032
    now = 2026

    def fx(v):
        return x0 + (v - lo) / float(hi - lo) * (x1 - x0)

    ytop = 30
    f.line(x0, ytop, x1, ytop, 'ax')
    for yr in (1980, 1990, 2000, 2010, 2020, 2030):
        f.line(fx(yr), ytop - 4, fx(yr), ytop, 'ax')
        f.text(fx(yr), ytop - 8, str(yr), 'tick')
    # (첫 상용, 끝난 해 또는 None, 이름)
    spans = [(1979, 2008, '1G'), (1991, None, '2G'), (2001, None, '3G'),
             (2009, None, '4G'), (2019, None, '5G')]
    for i, (a, b, name) in enumerate(spans):
        y = ytop + 6 + i * 15
        end = b if b else now
        f.rect(fx(a), y, fx(end) - fx(a) - 1, 11, 'cell ' + 'abcde'[i])
        f.text(fx(a) + 4, y + 9, name, 'key', 'start')
        if b:
            f.text(fx(b) + 3, y + 9, '%d 종료' % b, 'tick', 'start')
        else:
            f.text(fx(end) + 3, y + 9, '→', 'tick', 'start')
    marks = [(1979, 'NTT 자동차전화'), (1991, 'GSM 상용'),
             (1996, '한국 CDMA'), (2001, 'FOMA'),
             (2009, 'LTE 상용'), (2019, '한국 5G')]
    ybase = ytop + 6 + 5 * 15 + 4
    for i, (yr, what) in enumerate(marks):
        yy = ybase + 12 + i * 13
        f.circle(fx(yr), yy - 4, 2.2, 'dot2')
        f.text(fx(yr) + 5, yy, '%d %s' % (yr, what), 'tick', 'start')
    rows = 0
    with io.open(os.path.join(BASE, 'data', 'timeline.tsv'),
                 encoding='utf-8') as fh:
        for k, line in enumerate(fh):
            if k and line.strip() and not line.startswith('#'):
                rows += 1
    f.text(170, 218, '연도는 data/timeline.tsv 에서 온다 — %d행,'
                     ' 행마다 출처가 있다' % rows, 'cap')
    return f


@fig('architecture_evolution')
def architecture_evolution():
    f = Fig(268, title='망 구조의 진화')
    rows = [('GSM', ['MS', 'BTS', 'BSC', 'MSC', 'HLR'], 'a'),
            ('UMTS', ['UE', 'NodeB', 'RNC', 'SGSN', 'GGSN'], 'b'),
            ('LTE', ['UE', 'eNB', 'MME', 'SGW', 'PGW'], 'c'),
            ('5G', ['UE', 'gNB', 'AMF', 'SMF', 'UPF'], 'd')]
    for i, (name, boxes, cls) in enumerate(rows):
        y = 34 + i * 52
        f.text(16, y + 16, name, 'key', 'start')
        for k, b in enumerate(boxes):
            x = 54 + k * 55
            f.rect(x, y, 48, 26, 'cell ' + cls)
            f.text(x + 24, y + 17, b, 'tick')
            if k:
                f.line(x - 7, y + 13, x, y + 13, 'tie')
    f.text(170, 240, 'GSM 은 BSC 가 무선을 모두 쥐었고, LTE 는 그 층을',
           'cap')
    f.text(170, 252,
           '없애 eNB 로 평탄하게 만들었다. 5G 는 제어와 사용자',
           'cap')
    f.text(170, 264, '평면을 아예 갈랐다(AMF/SMF 대 UPF).', 'cap')
    return f


@fig('mimo_array_pattern')
def mimo_array_pattern():
    f = Fig(220, title='균일 선형 배열의 빔 (d = λ/2)')
    ax = Axes(f, 34, 14, 274, 150, (-90, 90), (-30, 3))
    ax.frame()
    ax.grid(xs=(-60, -30, 0, 30, 60), ys=(-20, -10, 0))
    for n, cls in ((2, 'cv1'), (4, 'cv3'), (8, 'cv4'), (16, 'cv5')):
        pts = []
        for i in range(721):
            deg = -90 + 180.0 * i / 720.0
            v = abs(mimo.array_factor(n, 0.5, math.radians(deg), 0.0))
            # 바닥은 y 하한 −30 dB — 널이 그 아래로 내려가면 곡선이
            # 틀 밖으로 새어 눈금과 설명 글자를 덮는다
            pts.append((deg, 20 * math.log10(max(v / n, 10 ** -1.5))))
        ax.curve(pts, cls)
    ax.xticks((-90, -45, 0, 45, 90), '%d', '각도 [도]')
    ax.yticks((-30, -20, -10, 0), '%d', '정규화 [dB]')
    sk.legend(f, 250, 30, [('N=2', 'cv1'), ('N=4', 'cv3'),
                           ('N=8', 'cv4'), ('N=16', 'cv5')])
    f.text(170, 206, '소자가 늘면 주엽이 좁아지고 널이 많아진다', 'cap')
    return f


@fig('alamouti_slope')
def alamouti_slope():
    f = Fig(215, title='다이버시티 차수 = BER 곡선의 기울기')
    ax = Axes(f, 40, 14, 200, 150, (5, 22), (1e-4, 0.2), ylog=True)
    ax.frame()
    ax.grid(ys=(1e-3, 1e-2, 1e-1))
    a = [(e, mimo.siso_rayleigh_ber(float(e), 20000, seed=5))
         for e in range(5, 23, 3)]
    b = [(e, max(mimo.alamouti_ber(float(e), 4000, seed=3), 1e-4))
         for e in range(5, 23, 3)]
    ax.curve(a, 'cv1')
    ax.dots(a, 1.6, 'dot')
    ax.curve(b, 'cv5')
    ax.dots(b, 1.6, 'dot2')
    ax.xticks((5, 10, 15, 20), '%d', 'Eb/N0 [dB]')
    ax.yticks((1e-4, 1e-3, 1e-2, 1e-1), '%.0e', 'BER')
    sk.legend(f, 250, 34, [('1×1 레일리', 'cv1'),
                           ('알라무티 2×1', 'cv5')])
    # 기울기는 그린 점에서 잰다(log10 BER / (dB/10)). 이론값 −1·−2 로
    # 반올림해 적으면 옆 슬라이드의 '반올림하지 않는다' 와 어긋난다.
    def slope(pts):
        return ((math.log10(pts[-1][1]) - math.log10(pts[0][1]))
                / ((pts[-1][0] - pts[0][0]) / 10.0))
    f.text(170, 200,
           '점에서 잰 기울기 %.2f → %.2f (이론 −1 → −2) — 차수 2'
           % (slope(a), slope(b)),
           'cap')
    return f


def render_all():
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    made = {}
    for name in sorted(FIGURES):
        made[name + '.svg'] = FIGURES[name]().render() + '\n'
    return made


def main(argv):
    made = render_all()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(FIGS, name)
            cur = (io.open(p, encoding='utf-8').read()
                   if os.path.exists(p) else '')
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 소스와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    wide = []
    for name, text in sorted(made.items()):
        io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                newline='\n').write(text)
        import re
        m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ', text)
        if m and float(m.group(1)) > 360:
            wide.append(name)
    for name in wide:
        print('  ✗ %s: viewBox 가 너무 넓다' % name)
    print('그림 %d장 → deck/figs/' % len(made))
    return 1 if wide else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
