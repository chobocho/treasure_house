#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이 덱의 도해 — data/·out/ 에서만 그린다 (PLAN.md §3.6).

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

점 하나, 곡선 하나가 모두 data/*.tsv 의 한 행이거나 out/fig_*.tsv
(exps/pf.py 가 시뮬레이터로 계산한 것)의 한 행이다. 그림이 가정하는
것(예: 연표가 1849 에서 시작한다)은 need() 로 적어 두고, 자료가 바뀌어
가정이 깨지면 그림을 만들지 않는다. 자료가 없는 개념도(프레임 기하,
블록도)는 "개념도" 라고 캡션에 밝힌다.

viewBox 폭은 340(svgkit.W). 글자는 svgkit 의 클래스로만 적는다.
goevo/deck/gen_figs.py 의 틀(FIGURES·need·--check)을 물려받았다.
"""
import datetime
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data')
OUT = os.path.join(BASE, 'out')
FIGS = os.path.join(HERE, 'figs')
sys.path.insert(0, HERE)
from svgkit import Axes, Fig, legend                    # noqa: E402

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


def need(cond, what):
    """그림의 가정이 자료와 맞는지. 어긋나면 그림을 만들지 않는다."""
    if not cond:
        raise SystemExit('gen_figs: 자료가 그림의 가정과 다르다 — ' + what)


def _read_tsv(path):
    rows, head = [], None
    with io.open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            cols = line.split('\t')
            if head is None:
                head = cols
            else:
                rows.append(dict(zip(head, cols)))
    return rows


def tsv(name):
    """data/<name> — '#' 줄을 건너뛰고 머리줄을 열쇠로 한 dict 들."""
    return _read_tsv(os.path.join(DATA, name))


def out_tsv(name):
    """out/fig_<name>.tsv — 값은 전부 float 로."""
    rows = _read_tsv(os.path.join(OUT, 'fig_%s.tsv' % name))
    return [{k: float(v) for k, v in r.items()} for r in rows]


def year_frac(date):
    """'1849-07-15' · '2012-09' · '1935' → 연도 + 그해의 몇 분의 몇."""
    parts = [int(x) for x in date.split('-')] + [1, 1]
    y, m, d = parts[0], parts[1], parts[2]
    start = datetime.date(y, 1, 1)
    days = (datetime.date(y + 1, 1, 1) - start).days
    return y + (datetime.date(y, m, d) - start).days / float(days)


# ── 1. 연표 ────────────────────────────────────────────────────────────

# 갈래 차례 = head.html 의 --g1…--g8 차례 (색이 덱 전체에서 같은 뜻)
KINDS = [('military', '군용'), ('hobby', 'RC 취미'),
         ('multirotor', '멀티로터·FC'), ('consumer', '소비자'),
         ('racing', '레이싱'), ('delivery', '배송·산업'),
         ('show', '드론쇼'), ('law', '규제')]
# 가로축은 두 토막 — 1849–1999 는 왼쪽 30 %, 2000–2026 은 오른쪽 70 %.
# 행의 대부분이 2000 년 뒤라 한 눈금으로 그리면 오른쪽 끝에 뭉친다.
TL_X0, TL_BRK, TL_X1 = 78, 150, 330
TL_Y0, TL_END = 1849, 2027


def tl_x(y):
    if y < 2000:
        return TL_X0 + (y - TL_Y0) / (2000 - TL_Y0) * (TL_BRK - TL_X0)
    return TL_BRK + (y - 2000) / (TL_END - 2000) * (TL_X1 - TL_BRK)


def timeline_fig(title, window=None):
    rows = tsv('timeline.tsv')
    need(len(rows) >= 220, '연표가 220행 이상')
    need(min(year_frac(r['date']) for r in rows) >= TL_Y0, '1849 이후')
    need(max(year_frac(r['date']) for r in rows) < TL_END, '2026 까지')
    need(set(r['kind'] for r in rows) <= set(k for k, _ in KINDS),
         '갈래가 여덟 가지 안')
    lane, top = 17, 24
    f = Fig(h=top + lane * len(KINDS) + 44, title=title)
    bottom = top + lane * len(KINDS)
    if window:
        a, b = tl_x(window[0]), tl_x(window[1])
        f.rect(a, top - 4, b - a, bottom - top + 4, 'cell a')
    for i, (kind, name) in enumerate(KINDS):
        y = top + lane * i + lane / 2
        f.line(TL_X0, y, TL_X1, y, 'grid')
        n = 0
        for r in rows:
            if r['kind'] == kind:
                f.circle(tl_x(year_frac(r['date'])), y, 2.0,
                         'dotg%d' % (i + 1))
                n += 1
        f.text(TL_X0 - 4, y + 3, '%s %d' % (name, n), 'tick', 'end')
    f.line(TL_X0, bottom, TL_X1, bottom, 'ax')
    for y in (1850, 1900, 1950, 2000, 2010, 2020):
        x = tl_x(y)
        f.line(x, bottom, x, bottom + 3, 'ax')
        f.text(x, bottom + 12, '%d' % y, 'tick')
    # 눈금이 바뀌는 자리 — 물결 대신 두 줄 빗금
    for dx in (-2, 2):
        f.line(TL_BRK + dx - 2, bottom + 4, TL_BRK + dx + 2, bottom - 4,
               'ax')
    f.text(170, bottom + 26, '점 하나 = data/timeline.tsv 한 행 (%d행)'
           % len(rows), 'cap')
    f.text(170, bottom + 38, '2000 년에서 눈금이 바뀐다 — 왼쪽 150년, '
           '오른쪽 27년', 'cap')
    return f


@fig('timeline')
def timeline():
    return timeline_fig('드론 연표 1849–2026, 갈래별')


@fig('timeline_p2')
def timeline_p2():
    """2부(역사 I)의 창 — 멀티로터 부활 전까지."""
    return timeline_fig('2부가 다루는 창: 1849–2004', (1849, 2005))


@fig('timeline_p3')
def timeline_p3():
    """3부(역사 II)의 창 — MEMS·리포 전환점부터 지금까지."""
    return timeline_fig('3부가 다루는 창: 2005–2026', (2005, 2026.8))


# ── 2. 드론쇼 규모 ──────────────────────────────────────────────────────

RECORD_CLS = {'Guinness': 'dot', 'claimed': 'dot2', 'none': 'dotn'}


@fig('show_sizes')
def show_sizes():
    """쇼마다 점 하나 — 세로는 대수(로그), 모양은 기록의 종류."""
    rows = tsv('shows.tsv')
    need(len(rows) >= 60, '쇼 기록이 60행 이상')
    need(set(r['record'] for r in rows) <= set(RECORD_CLS),
         'record 는 Guinness·claimed·none 중 하나')
    ns = [int(r['drone-count']) for r in rows]
    need(min(ns) >= 10 and max(ns) < 100000, '대수가 10~100000 사이')
    ys = [year_frac(r['date']) for r in rows]
    need(min(ys) >= 2012 and max(ys) < 2027, '2012–2026 의 쇼')
    f = Fig(h=236, title='드론쇼 한 편에 뜬 대수')
    ax = Axes(f, 40, 14, 288, 160, (2012, 2027), (10, 100000), ylog=True)
    ax.grid(xs=range(2012, 2027, 2), ys=(100, 1000, 10000))
    ax.frame()
    ax.xticks(range(2012, 2027, 2), '%d', '')
    ax.yticks((10, 100, 1000, 10000, 100000), '%d', '')
    # 기네스 행의 최고 기록을 이어 '기록의 사다리' 를 그린다
    best, lad = 0, []
    for y, n, r in sorted(zip(ys, ns, [r['record'] for r in rows])):
        if r == 'Guinness' and n > best:
            best = n
            lad.append((y, n))
    ax.curve(lad, 'cvd')
    for y, n, r in zip(ys, ns, rows):
        x, yy = ax.at(y, n)
        f.circle(x, yy, 2.2, RECORD_CLS[r['record']])
    cnt = {k: sum(1 for r in rows if r['record'] == k) for k in RECORD_CLS}
    f.circle(44, 200, 2.2, 'dot')
    f.text(50, 203, '기네스 인증 %d' % cnt['Guinness'], 'cap', 'start')
    f.circle(134, 200, 2.2, 'dot2')
    f.text(140, 203, '주최측 주장 %d' % cnt['claimed'], 'cap', 'start')
    f.circle(224, 200, 2.2, 'dotn')
    f.text(230, 203, '기록 아님 %d' % cnt['none'], 'cap', 'start')
    f.text(184, 218, '점선 = 기네스 기록의 사다리 · 세로는 로그 눈금',
           'cap')
    f.text(184, 230, '출처: data/shows.tsv (%d행)' % len(rows), 'cap')
    return f


# ── 3. 프레임 기하 (개념도) ─────────────────────────────────────────────

def rotor(f, x, y, ccw, r=9.0):
    """위에서 본 로터 하나 — 원과 도는 방향 화살 촉."""
    f.circle(x, y, r, 'ring')
    # 원 꼭대기에 촉을 달아 방향을 보인다: 반시계면 왼쪽을 향한다
    s = -1 if ccw else 1
    f.poly([(x + s * 3.5, y - r), (x - s * 1.5, y - r - 3),
            (x - s * 1.5, y - r + 3)], 'ah')


def arm_frame(f, cx, cy, angles, spins, arm=22.0, coax=False):
    for a, ccw in zip(angles, spins):
        t = math.radians(a)
        x, y = cx + arm * math.sin(t), cy - arm * math.cos(t)
        f.line(cx, cy, x, y, 'edge')
        rotor(f, x, y, ccw, 7.0)
        if coax:
            f.circle(x, y, 4.0, 'ring')
    f.rect(cx - 4, cy - 4, 8, 8, 'box g3')


@fig('frames')
def frames():
    """+, X, H, 6·8축, 동축 — 위에서 본 모양과 로터가 도는 방향.

    X 는 SPEC §4.1 의 번호(1 앞왼쪽, 반시계부터 번갈아)를 따른다."""
    f = Fig(h=236, title='멀티로터 프레임 기하(위에서 본 개념도)')
    f.text(170, 12, '위쪽 = 기체 앞(x) · 촉 = 로터가 도는 방향', 'cap')
    alt4 = [True, False, True, False]
    cells = [
        ('+ 4축', [0, 90, 180, 270], [True, False, True, False], False),
        ('X 4축', [315, 225, 135, 45], alt4, False),
        ('6축(헥사)', [0, 60, 120, 180, 240, 300],
         [True, False] * 3, False),
        ('8축(옥타)', [22.5 + 45 * k for k in range(8)],
         [True, False] * 4, False),
        ('동축 X8', [315, 225, 135, 45], alt4, True),
    ]
    for i, (name, ang, spin, coax) in enumerate(cells):
        cx = 58 + (i % 3) * 112
        cy = 60 + (i // 3) * 92
        # 8축은 팔을 늘려야 이웃 로터끼리 겹치지 않는다
        arm_frame(f, cx, cy, ang, spin, arm=28.0 if len(ang) == 8 else 22.0,
                  coax=coax)
        f.text(cx, cy + 44, name, 'lbl')
    # H 프레임 — 팔이 몸통 옆으로 나란하다
    cx, cy = 58 + 2 * 112, 60 + 92
    f.rect(cx - 5, cy - 22, 10, 44, 'box g3')
    for (dx, dy), ccw in zip(((-24, -20), (-24, 20), (24, 20), (24, -20)),
                             alt4):
        f.line(cx, cy + dy, cx + dx, cy + dy, 'edge')
        rotor(f, cx + dx, cy + dy, ccw, 7.0)
    f.text(cx, cy + 44, 'H 4축', 'lbl')
    f.text(170, 226, '동축: 위·아래 로터가 반대로 돈다(아래는 작은 원)',
           'cap')
    return f


# ── 4. 시뮬레이터 곡선 (out/fig_*.tsv) ─────────────────────────────────

@fig('step')
def step():
    """T14 — ζ 0.2·0.707·1 의 계단 응답 (kp = 4)."""
    rows = out_tsv('step')
    keys = ['zeta=0.2', 'zeta=0.707', 'zeta=1']
    need(set(keys) <= set(rows[0]), 'ζ 세 열')
    need(abs(rows[-1]['t'] - 6.0) < 1e-9, '6초까지')
    top = max(r['zeta=0.2'] for r in rows)
    need(1.4 < top < 1.6, 'ζ 0.2 의 최고점이 1.4~1.6 (공식 1.527)')
    f = Fig(h=210, title='2차 계의 계단 응답, kp = 4')
    ax = Axes(f, 34, 14, 292, 150, (0, 6), (0, 1.6))
    ax.grid(xs=range(0, 7), ys=(0.5, 1.0, 1.5))
    ax.frame()
    ax.xticks(range(0, 7), '%d', '시간 t [s]')
    ax.yticks((0, 0.5, 1.0, 1.5), '%.1f', '')
    for k, cls in zip(keys, ('cv5', 'cv', 'cv2')):
        ax.curve([(r['t'], r[k]) for r in rows], cls)
    legend(f, 240, 128, [('ζ = 0.2', 'cv5'), ('ζ = 0.707', 'cv'),
                         ('ζ = 1', 'cv2')])
    f.text(180, 206, '출처: out/fig_step.tsv (exps/pf.py, RK4 1 ms)', 'cap')
    return f


@fig('cascade_step')
def cascade_step():
    """전체 모형 — x 목표를 1 m 옮겼을 때 x(t) 와 기울기."""
    rows = out_tsv('cascade')
    need(abs(rows[-1]['t'] - 5.0) < 1e-9, '5초까지')
    need(abs(rows[-1]['x'] - 1.0) < 0.02, '5초 뒤 목표 근처')
    tmax = max(r['tilt_deg'] for r in rows)
    need(5 < tmax < 30, '기울기 최고 5°~30°')
    f = Fig(h=264, title='캐스케이드 제어: x 를 1 m 옮기기')
    ax = Axes(f, 34, 14, 292, 90, (0, 5), (0, 1.2))
    ax.grid(ys=(0.5, 1.0))
    ax.frame()
    ax.yticks((0, 0.5, 1.0), '%.1f', 'x [m]')
    ax.curve([(r['t'], r['x']) for r in rows], 'cv')
    ax2 = Axes(f, 34, 124, 292, 80, (0, 5), (0, 25))
    ax2.grid(ys=(10, 20))
    ax2.frame()
    ax2.xticks(range(0, 6), '%d', '시간 t [s]')
    ax2.yticks((0, 10, 20), '%d', '기울기 [°]')
    ax2.curve([(r['t'], r['tilt_deg']) for r in rows], 'cv5')
    f.text(180, 246, '먼저 기울고(아래) 그다음 움직인다(위)', 'cap')
    f.text(180, 258, '0.6 s 의 0 = 반대로 기울어 제동하는 순간 · '
           'out/fig_cascade.tsv', 'cap')
    return f


@fig('comp')
def comp():
    """T23 — 자이로 적분은 표류, 가속도계는 떨림, 상보 필터는 둘 다 덜."""
    rows = out_tsv('comp')
    need(abs(rows[-1]['t'] - 10.0) < 1e-9, '10초까지')
    drift = rows[-1]['gyro_int'] - rows[-1]['truth']
    need(0.3 < drift < 0.7, '자이로 적분의 표류가 0.3~0.7 rad (바이어스 0.05)')
    f = Fig(h=214, title='자세 한 축: 참값과 세 가지 추정')
    ax = Axes(f, 34, 14, 292, 150, (0, 10), (-0.6, 0.9))
    ax.grid(ys=(-0.3, 0, 0.3, 0.6))
    ax.frame()
    ax.xticks(range(0, 11, 2), '%d', '시간 t [s]')
    ax.yticks((-0.3, 0, 0.3, 0.6), '%.1f', '각 [rad]')
    ax.dots([(r['t'], r['acc']) for r in rows[::2]], 0.9, 'dotn')
    ax.curve([(r['t'], r['gyro_int']) for r in rows], 'cv5')
    ax.curve([(r['t'], r['truth']) for r in rows], 'cvd')
    ax.curve([(r['t'], r['comp']) for r in rows], 'cv')
    legend(f, 44, 26, [('자이로 적분', 'cv5'), ('상보 α 0.98', 'cv'),
                       ('참값', 'cvd')])
    f.text(180, 210, '회색 점 = 가속도계 각 · out/fig_comp.tsv', 'cap')
    return f


@fig('snap')
def snap():
    """10 m 를 같은 시간에 — 사다리꼴 속도와 최소 스냅."""
    rows = out_tsv('snap')
    big_t = rows[-1]['t']
    need(abs(rows[-1]['trap_x'] - 10) < 1e-6 and
         abs(rows[-1]['snap_x'] - 10) < 1e-6, '둘 다 10 m 에서 멈춘다')
    vmax = max(r['snap_v'] for r in rows)
    need(4 < vmax < 6, '최소 스냅의 최고 속도 4~6 m/s')
    f = Fig(h=250, title='10 m 이동: 사다리꼴 대 최소 스냅')
    ax = Axes(f, 34, 14, 292, 90, (0, big_t), (0, 10.5))
    ax.grid(ys=(5, 10))
    ax.frame()
    ax.yticks((0, 5, 10), '%d', 'x [m]')
    ax.curve([(r['t'], r['trap_x']) for r in rows], 'cv5')
    ax.curve([(r['t'], r['snap_x']) for r in rows], 'cv')
    ax2 = Axes(f, 34, 124, 292, 80, (0, big_t), (0, 6))
    ax2.grid(ys=(2, 4))
    ax2.frame()
    ax2.xticks(range(0, int(big_t) + 1), '%d', '시간 t [s]')
    ax2.yticks((0, 2, 4, 6), '%d', 'v [m/s]')
    ax2.curve([(r['t'], r['trap_v']) for r in rows], 'cv5')
    ax2.curve([(r['t'], r['snap_v']) for r in rows], 'cv')
    legend(f, 44, 30, [('사다리꼴 v 4, a 2', 'cv5'), ('최소 스냅', 'cv')])
    f.text(180, 246, '같은 %.1f s — 최소 스냅은 꺾임이 없는 대신 최고 속도가 '
           '높다' % big_t, 'cap')
    return f


# ── 5. 블록도·기하 (개념도) ─────────────────────────────────────────────

def box(f, x, y, w, h, text, cls='box'):
    f.rect(x, y, w, h, cls)
    f.text(x + w / 2, y + h / 2 + 3.5, text, 'lbl')


def arrow(f, x1, y1, x2, y2, cls='edge'):
    f.line(x1, y1, x2, y2, cls)
    a = math.atan2(y2 - y1, x2 - x1)
    pts = [(x2, y2)]
    for s in (-1, 1):
        pts.append((x2 - 6 * math.cos(a) + s * 3 * math.sin(a),
                    y2 - 6 * math.sin(a) - s * 3 * math.cos(a)))
    f.poly(pts, 'ah' + (' hot' if 'hot' in cls else ''))


@fig('cascade_block')
def cascade_block():
    """위치 → 속도 → 자세 → 각속도 → 믹서 → 모터 (SPEC §5, PX4 구조와 같다)."""
    f = Fig(h=228, title='캐스케이드 제어기 블록도(개념도)')
    stages = [('위치 P', 'g1', '50 Hz'), ('속도 PID', 'g1', '50 Hz'),
              ('자세 P(사원수)', 'g3', '250 Hz'),
              ('각속도 PID', 'g3', '250 Hz'), ('믹서 M⁻¹', 'g5', ''),
              ('모터 4개', 'g6', '')]
    w, h = 96, 26
    xs = (20, 122, 224)
    for i, (name, g, hz) in enumerate(stages):
        row, col = divmod(i, 3)
        if row:
            col = 2 - col                   # 둘째 줄은 오른쪽에서 왼쪽으로
        x, y = xs[col], 40 + row * 80
        box(f, x, y, w - 8, h, name, 'box ' + g)
        if hz:
            f.text(x + (w - 8) / 2 + (12 if row else 0), y - 5, hz, 'tick')
        if i < 5:
            if i == 2:
                # 아래 상자의 주파수 글자와 겹치지 않게 왼쪽으로 비켜 내린다
                arrow(f, x + 16, y + h, x + 16, y + 80)
            elif row == 0:
                arrow(f, x + w - 8, y + h / 2, x + w + 2, y + h / 2)
            else:
                arrow(f, x, y + h / 2, x - 14, y + h / 2)
    # 되먹임 — 상태 추정이 네 고리 모두에 값을 댄다
    box(f, 20, 172, 300, 22, '상태 추정(자이로·가속도계·GNSS·기압계)',
        'box g2')
    for x in (64, 166, 268):
        arrow(f, x, 172, x, 148, 'edge dim')
    f.text(170, 24, '바깥 고리 = 느리게(50 Hz), 안쪽 고리 = 빠르게(250 Hz)',
           'cap')
    f.text(170, 212, '안쪽 고리가 바깥보다 몇 배 빨라야 한다(T17) · '
           '구조는 PX4 와 같다', 'cap')
    return f


@fig('assign_cross')
def assign_cross():
    """T30 반례의 두 쌍 — 교차점 X 에서 u·w = 0.9 (exps/p10 counter 와 같은 수)."""
    c = 0.9
    u, w = (1.0, 0.0), (c, math.sqrt(1 - c * c))
    a1, b1 = (-u[0], -u[1]), (10 * u[0], 10 * u[1])
    a2, b2 = (-10 * w[0], -10 * w[1]), (w[0], w[1])
    d = lambda p, q: math.hypot(p[0] - q[0], p[1] - q[1])
    keep2 = d(a1, b1) ** 2 + d(a2, b2) ** 2
    swap2 = d(a1, b2) ** 2 + d(a2, b1) ** 2
    need(keep2 < swap2, '제곱 합은 교차하는 쪽이 작다')
    need(d(a1, b2) + d(a2, b1) < d(a1, b1) + d(a2, b2),
         '그냥 거리 합은 안 교차하는 쪽이 작다')
    f = Fig(h=160, title='제곱 거리 최적이 교차하는 예')
    # 가로·세로 눈금을 같게(1 m = 300/21 px) 해야 각도가 바로 보인다
    ax = Axes(f, 20, 12, 300, 100, (-10.5, 10.5), (-5.0, 2.0))
    ax.frame()
    for (p, q), cls in (((a1, b1), 'edge hot'), ((a2, b2), 'edge hot'),
                        ((a1, b2), 'edge dim'), ((a2, b1), 'edge dim')):
        x1, y1 = ax.at(*p)
        x2, y2 = ax.at(*q)
        arrow(f, x1, y1, x2, y2, cls)
    for p, name in ((a1, 'a₁'), (a2, 'a₂'), (b1, 'b₁'), (b2, 'b₂')):
        x, y = ax.at(*p)
        f.circle(x, y, 2.6, 'dot')
        f.text(x, y - 6 if p[1] >= 0 else y + 13, name, 'tick')
    f.text(170, 136, '굵은 선 = 제곱 합 %.2f (교차) · 점선 = %.2f'
           % (keep2, swap2), 'cap')
    f.text(170, 150, '그래도 두 기체의 거리는 δ/√2 아래로 안 내려간다(T31)',
           'cap')
    return f


# ── 6. 개념도 — 추진·힘·쇼 현장 ────────────────────────────────────────

@fig('stream_tube')
def stream_tube():
    """T1 — 모멘텀 이론의 흐름관. 멀리 위 0, 원판 v_i, 멀리 아래 2v_i."""
    f = Fig(h=236, title='로터를 지나는 흐름관(모멘텀 이론 개념도)')
    cx = 130
    # 흐름관의 가장자리 — 위는 넓고 아래로 갈수록 좁아진다.
    # 연속 방정식: 넓이 × 속도 가 일정 → 멀리 아래의 넓이는 원판의 ½,
    # 반지름은 1/√2 배.
    r_disk = 50.0
    for side in (-1, 1):
        pts = []
        for y in range(22, 205, 6):
            if y <= 96:
                w = 1.0 + 0.9 * ((96 - y) / 74.0) ** 1.6
            else:
                w = 1 / math.sqrt(2) + (1 - 1 / math.sqrt(2)) * math.exp(
                    -(y - 96) / 22.0)
            pts.append((cx + side * r_disk * w, y))
        f.path(pts, 'cv')
    f.rect(cx - r_disk, 93, 2 * r_disk, 6, 'box g3')
    f.text(240, 99, '로터 원판 A', 'lbl', 'start')
    for y, v, lines in ((34, 0, ('멀리 위: 속도 0',)),
                        (80, 1, ('원판 위: vᵢ',)),
                        (130, 1, ('원판 아래: vᵢ', '(압력만 뛴다)')),
                        (180, 2, ('멀리 아래: 2vᵢ', '넓이 A/2'))):
        if v:
            arrow(f, cx, y - 6 * v, cx, y + 6 * v, 'edge hot')
        for k, line in enumerate(lines):
            f.text(240, y + 3 + 10 * k, line, 'tick', 'start')
    f.text(170, 218, '추력 T = 2ρA vᵢ² · 필요 동력 P = T vᵢ = T^(3/2)/√(2ρA)',
           'cap')
    f.text(170, 230, '화살 길이 = 흐름 속도(개념) · 공식은 4부 T1', 'cap')
    return f


@fig('freebody')
def freebody():
    """8부 — 쿼드로터에 걸리는 힘과 토크(옆에서 본 개념도)."""
    f = Fig(h=210, title='쿼드로터의 자유물체도(옆에서 본 개념도)')
    cx, cy = 170, 110
    f.line(cx - 90, cy, cx + 90, cy, 'edge')
    f.rect(cx - 14, cy - 8, 28, 16, 'box g3')
    for dx, name in ((-80, 'T₂ = kT·Ω₂²'), (80, 'T₁ = kT·Ω₁²')):
        f.rect(cx + dx - 18, cy - 4, 36, 3, 'box g5')
        arrow(f, cx + dx, cy - 6, cx + dx, cy - 56, 'edge hot')
        f.text(cx + dx, cy - 62, name, 'tick')
    arrow(f, cx, cy + 10, cx, cy + 62, 'edge')
    f.text(cx + 6, cy + 58, 'mg (무게)', 'tick', 'start')
    # 몸 좌표축 — z_B 는 로터 추력의 방향
    arrow(f, cx, cy, cx + 34, cy, 'edge dim')
    f.text(cx + 36, cy + 11, 'x_B', 'tick', 'start')
    arrow(f, cx, cy, cx, cy - 34, 'edge dim')
    f.text(cx + 5, cy - 28, 'z_B', 'tick', 'start')
    f.text(170, 22, '추력은 모두 z_B 방향 — 옆으로 가려면 몸을 기울인다',
           'cap')
    f.text(170, 190, '토크: 좌우 추력 차 × 팔 길이 = 굴림·키놀이, '
           '반토크 kQ·Ω² 의 합 = 요', 'cap')
    f.text(170, 202, '8부 T8(뉴턴-오일러)·T9(믹서)의 그림', 'cap')
    return f


@fig('showday')
def showday():
    """11부 — 쇼 당일 현장의 구성(개념도). 선 = 정보가 흐르는 길."""
    f = Fig(h=224, title='드론쇼 현장의 구성(개념도)')
    box(f, 12, 30, 92, 26, 'GNSS 위성', 'box g8')
    box(f, 12, 90, 92, 26, 'RTK 기준국', 'box g2')
    box(f, 124, 90, 92, 26, '지상국(GCS)', 'box g3')
    box(f, 236, 60, 92, 26, '쇼 파일', 'box g4')
    box(f, 236, 120, 92, 26, '안전 파일럿', 'box g5')
    box(f, 124, 160, 92, 26, '기체 N대', 'box g7')
    box(f, 12, 160, 92, 26, '지오펜스', 'box off')
    arrow(f, 58, 56, 58, 88)
    arrow(f, 104, 103, 122, 103)
    arrow(f, 236, 73, 218, 96)
    arrow(f, 170, 116, 170, 158, 'edge hot')
    arrow(f, 236, 133, 218, 170, 'edge hot')
    arrow(f, 104, 173, 122, 173, 'edge dim')
    f.text(176, 140, '보정값 + 명령', 'tick', 'start')
    f.text(282, 160, '정지·귀환 스위치', 'tick')
    f.text(170, 206, '기준국이 GNSS 오차를 재어 보내면(RTK) 기체 위치가 '
           'cm 급이 된다', 'cap')
    f.text(170, 218, '굵은 선 = 현장 무선 링크 · 11부에서 차례로 풀어 본다',
           'cap')
    return f


# (관할, 조문, 행 안에 있어야 할 말, 아래 끝 kg, 위 끝 kg, 칸 이름)
WEIGHT_BANDS = [
    ('KR', '제306조', '250 g 이하', 0.1, 0.25, '제외'),
    ('KR', '제306조', '4종 무인동력비행장치: 최대이륙중량 250 g 초과 2 kg',
     0.25, 2, '4종'),
    ('KR', '제306조', '3종 무인동력비행장치: 최대이륙중량 2 kg 초과 7 kg',
     2, 7, '3종'),
    ('KR', '제306조', '2종 무인동력비행장치: 최대이륙중량 7 kg 초과 25 kg',
     7, 25, '2종'),
    ('KR', '제306조', '1종 무인동력비행장치: 최대이륙중량 25 kg 초과',
     25, 150, '1종'),
    ('US', '§107.110', '0.55 lb 이하', 0.1, 0.249, '범주1'),
    ('US', '§107.3', '55 lb 미만', 0.249, 24.9, 'Part 107 small UAS'),
    ('EU', 'PART 1', '250 g 미만', 0.1, 0.25, 'C0'),
    ('EU', 'PART 2', '900 g 미만', 0.25, 0.9, 'C1'),
    ('EU', 'PART 3', '4 kg 미만', 0.9, 4, 'C2'),
    ('EU', 'PART 4', '25 kg 미만', 4, 25, 'C3·C4'),
]


@fig('weight_classes')
def weight_classes():
    """1부 — 무게로 나눈 등급, 한국·미국·EU (data/law.tsv 의 조문)."""
    rows = tsv('law.tsv')
    for jur, art, text, _lo, _hi, _name in WEIGHT_BANDS:
        need(any(r['jurisdiction'] == jur and r['article'] == art
                 and text in r['requirement(ko)'] for r in rows),
             '%s %s 에 "%s"' % (jur, art, text))
    f = Fig(h=210, title='무게로 나눈 등급 — 한국·미국·EU')
    ax = Axes(f, 40, 20, 290, 120, (0.1, 200), (0, 3), xlog=True)
    ax.grid(xs=(0.25, 2, 25, 150))
    ax.xticks((0.1, 0.25, 1, 2, 7, 25, 150), '%g', '최대이륙중량 [kg] (로그 눈금)')
    lane = {'KR': 2, 'US': 1, 'EU': 0}
    colors = {'KR': 'g3', 'US': 'g6', 'EU': 'g4'}
    for jur, _art, _t, lo, hi, name in WEIGHT_BANDS:
        x0, y0 = ax.at(lo, lane[jur] + 0.9)
        x1, y1 = ax.at(hi, lane[jur] + 0.1)
        f.rect(x0 + 0.6, y0, x1 - x0 - 1.2, y1 - y0, 'box ' + colors[jur])
        if x1 - x0 > 22:
            f.text((x0 + x1) / 2, (y0 + y1) / 2 + 3, name, 'tick')
    for jur, k in lane.items():
        f.text(36, ax.at(1, k + 0.5)[1] + 3, jur, 'key', 'end')
    f.text(185, 180, '칸 하나 = data/law.tsv 의 조문 한 줄 · KR 제외 = '
           '조종자 증명 대상 밖', 'cap')
    f.text(185, 192, 'US 범주1 = 사람 위 비행 · EU C0–C4 = 기체 클래스 · '
           '빈 곳은 다른 절차', 'cap')
    f.text(185, 204, 'KR 1종의 위 끝 150 kg 은 연료를 뺀 자체중량', 'cap')
    return f


def render_all():
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
            cur = ''
            if os.path.exists(p):
                with io.open(p, encoding='utf-8') as f:
                    cur = f.read()
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 자료와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    os.makedirs(FIGS, exist_ok=True)
    for name, text in sorted(made.items()):
        with io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                     newline='\n') as f:
            f.write(text)
    print('그림 %d장 → deck/figs/' % len(made))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
