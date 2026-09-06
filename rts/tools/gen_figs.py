# -*- coding: utf-8 -*-
"""덱에 인라인으로 들어갈 도해를 만든다 — deck/figs/*.svg (SPEC 참고, 8단계).

   도해는 **손으로 그리지 않는다.** 엔진과 골든에서 숫자를 읽어 그린다.
   그래야 명세가 바뀌면 그림도 같이 바뀌고, "그림만 옛날 값"이 되는 일이 없다.

   쓰는 CSS 클래스는 deck/base/head.html 의 `svg.diag` 규칙뿐이다:
     .tl(타일) .tl.on .tl.hot .tl.dim .tl.cool .tl.none .gd(격자) .lbl .ax(강조)
   색을 직접 쓰지 않는 이유는 덱의 명암 테마가 바뀌어도 도해가 따라가게 하려는 것.

   실행:  python3 tools/gen_figs.py           (deck/figs/*.svg 를 덮어쓴다)
          sh tools/check_figs.sh /tmp/figs    (눈으로 확인)
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, 'deck', 'figs')
sys.path.insert(0, os.path.join(BASE, 'py'))

from rts import circle as CI      # noqa: E402
from rts import const as C        # noqa: E402
from rts import fixed as F        # noqa: E402
from rts import flow as FL        # noqa: E402
from rts import main as MAIN      # noqa: E402
from rts import tmap as T         # noqa: E402


# ── 아주 작은 SVG 조립기 ────────────────────────────────────────────────────
class Svg(object):
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.parts = ['<svg class="diag" viewBox="0 0 %d %d" role="img">' % (w, h),
                      '<title>%s</title>' % esc(title)]

    def rect(self, x, y, w, h, cls='tl', extra=''):
        self.parts.append('<rect class="%s" x="%g" y="%g" width="%g" height="%g"%s/>'
                          % (cls, x, y, w, h, extra))

    def line(self, x1, y1, x2, y2, cls='gd'):
        self.parts.append('<line class="%s" x1="%g" y1="%g" x2="%g" y2="%g"/>'
                          % (cls, x1, y1, x2, y2))

    def path(self, d, cls='ax'):
        self.parts.append('<path class="%s" d="%s"/>' % (cls, d))

    def text(self, x, y, s, cls=None, anchor='middle'):
        c = ' class="%s"' % cls if cls else ''
        self.parts.append('<text%s x="%g" y="%g" text-anchor="%s">%s</text>'
                          % (c, x, y, anchor, esc(s)))

    def circle(self, x, y, r, cls='tl'):
        self.parts.append('<circle class="%s" cx="%g" cy="%g" r="%g"/>'
                          % (cls, x, y, r))

    def save(self, name):
        self.parts.append('</svg>')
        p = os.path.join(FIGS, name)
        io.open(p, 'w', encoding='utf-8').write('\n'.join(self.parts) + '\n')
        return name


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def arrow(sv, x, y, d, r=9):
    """방향 번호 d 로 화살표 하나. 8방향 표는 §2.7."""
    dx, dy = F.DX[d] * r, F.DY[d] * r
    sv.path('M%g %g L%g %g' % (x - dx * .5, y - dy * .5, x + dx * .5, y + dy * .5))
    ax, ay = x + dx * .5, y + dy * .5
    # 화살촉은 진행 방향에서 좌우로 135도 꺾은 두 선
    for s in (3, -3):
        px = ax - dx * .35 + dy * .18 * (s / 3.0)
        py = ay - dy * .35 - dx * .18 * (s / 3.0)
        sv.path('M%g %g L%g %g' % (ax, ay, px, py))


# ── 4부: 오토타일 ───────────────────────────────────────────────────────────
def fig_autotile_classes():
    """256 마스크가 47 클래스로 접히는 것을 실제 타일 그림으로 보인다."""
    cls = sorted(set(T.canon(m) for m in range(256)))
    cols, cell, pad = 12, 46, 8
    rows = (len(cls) + cols - 1) // cols
    sv = Svg(cols * cell + 2 * pad, rows * cell + 2 * pad + 16,
             '오토타일 47 클래스 — 8이웃 마스크를 정규화한 결과')
    for k, m in enumerate(cls):
        cx = pad + (k % cols) * cell
        cy = pad + (k // cols) * cell + 12
        for d in range(8):
            x = cx + 12 + F.DX[d] * 11
            y = cy + 12 + F.DY[d] * 11
            sv.rect(x - 5, y - 5, 10, 10,
                    'tl on' if F.bit(m, d) else 'tl dim')
        sv.rect(cx + 7, cy + 7, 10, 10, 'tl hot')
        sv.text(cx + 12, cy + 40, '%d' % k, 'lbl')
    sv.text(pad, 12, '가운데가 자기 칸 · 이웃 8칸이 같은 지형이면 밝게 · 아래는 클래스 번호',
            'lbl', 'start')
    return sv.save('autotile_classes.svg')


def fig_autotile_corner():
    """정리 4.1 — 모서리 비트는 양옆 변이 둘 다 있을 때만 살아남는다."""
    sv = Svg(560, 190, '모서리 비트 정규화 규칙 (정리 4.1)')
    cases = [(F.setbit(0, 1), '북동 모서리만'),
             (F.setbit(F.setbit(0, 1), 0), '모서리 + 북'),
             (F.setbit(F.setbit(F.setbit(0, 1), 0), 2), '모서리 + 북 + 동')]
    for k, (m, label) in enumerate(cases):
        ox = 24 + k * 180
        for d in range(8):
            x = ox + 46 + F.DX[d] * 26
            y = 66 + F.DY[d] * 26
            sv.rect(x - 12, y - 12, 24, 24, 'tl on' if F.bit(m, d) else 'tl dim')
        sv.rect(ox + 34, 54, 24, 24, 'tl hot')
        sv.text(ox + 46, 122, label, 'lbl')
        cm = T.canon(m)
        sv.text(ox + 46, 140, '마스크 %d → 정규화 %d' % (m, cm), 'lbl')
        sv.text(ox + 46, 158,
                '모서리 %s' % ('살아남는다' if F.bit(cm, 1) else '지워진다'), 'lbl')
    sv.text(24, 22, '모서리(북동)는 양옆 변(북·동)이 둘 다 있어야 그림이 이어진다',
            None, 'start')
    return sv.save('autotile_corner.svg')


# ── 6부: 원 마스크 ──────────────────────────────────────────────────────────
def fig_circle_spans():
    """행 span 으로 그린 디스크와, 고전 미드포인트 외곽선의 반례(r=2 의 (2,1))."""
    r = 6
    cell = 15
    n = 2 * r + 1
    sv = Svg(n * cell + 260, n * cell + 40, '원 마스크 — 행 span 과 미드포인트 외곽선')
    sp = CI.spans(r)
    out = CI.midpoint_outline(r)
    for j in range(-r, r + 1):
        w = sp[j if j >= 0 else -j]
        for i in range(-r, r + 1):
            x = 20 + (i + r) * cell
            y = 24 + (j + r) * cell
            inside = abs(i) <= w
            cls = 'tl on' if inside else 'tl dim'
            if (i, j) in out:
                cls = 'tl hot' if inside else 'tl cool'
            sv.rect(x, y, cell - 2, cell - 2, cls)
        sv.text(20 + n * cell + 8, 24 + (j + r) * cell + 10,
                'span %d' % w, 'lbl', 'start')
    sv.text(20, 16, 'r=%d · 안에 드는 칸 %d개 (가우스 원 문제 N(r))'
            % (r, CI.count(r)), None, 'start')
    bx = 20 + n * cell + 90
    sv.text(bx, 24 + n * cell - 8,
            '주황: 외곽선이 찍은 칸 중 원 안', 'lbl', 'start')
    sv.text(bx, 24 + n * cell + 6,
            '파랑: 외곽선이 찍었으나 원 밖', 'lbl', 'start')
    return sv.save('circle_spans.svg')


def fig_circle_counterexample():
    """r=2 에서 미드포인트 외곽선이 (2,1) 을 찍는다 — 2²+1²=5 > 4."""
    r, cell = 2, 40
    n = 2 * r + 1
    sv = Svg(n * cell + 300, n * cell + 46,
             '미드포인트 외곽선의 반례 — r=2 에서 (2,1)')
    out = CI.midpoint_outline(r)
    sp = CI.spans(r)
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            x = 20 + (i + r) * cell
            y = 30 + (j + r) * cell
            inside = abs(i) <= sp[j if j >= 0 else -j]
            cls = 'tl on' if inside else 'tl dim'
            if (i, j) in out and not inside:
                cls = 'tl cool'
            sv.rect(x, y, cell - 3, cell - 3, cls)
            sv.text(x + cell // 2 - 2, y + cell // 2 + 2,
                    '%d' % (i * i + j * j), 'lbl')
    tx = 20 + n * cell + 16
    sv.text(tx, 46, '칸 안의 숫자는 i² + j²', 'lbl', 'start')
    sv.text(tx, 66, 'r² = 4 이므로 5 는 원 밖이다', 'lbl', 'start')
    sv.text(tx, 86, '그런데 외곽선 알고리즘은 (2,1) 을 찍는다', 'lbl', 'start')
    sv.text(tx, 106, '시야 마스크로 쓰면 칸 수가', 'lbl', 'start')
    sv.text(tx, 122, '가우스 원 문제의 값과 어긋난다', 'lbl', 'start')
    sv.text(tx, 146, '그래서 이 엔진은 행 span 을 쓴다 (§6.2)', 'lbl', 'start')
    return sv.save('circle_counterexample.svg')


# ── 13부: 흐름장 ────────────────────────────────────────────────────────────
def fig_flow_field():
    """골든 9절의 적분장과 경사장을 그대로 그린다."""
    m = MAIN.flowmap()
    integ = FL.integration(m, 0, [(4, 4)])
    fl = FL.flow_dirs(m, 0, integ)
    cell = 34
    sv = Svg(m.w * cell + 40, m.h * cell + 60,
             '적분장과 경사장 — 목표 (4,4), 골든 9절 그대로')
    for y in range(m.h):
        for x in range(m.w):
            i = y * m.w + x
            px, py = 20 + x * cell, 30 + y * cell
            if not m.passable_terrain(x, y, 0):
                sv.rect(px, py, cell - 2, cell - 2, 'tl dim')
                continue
            v = integ[i]
            sv.rect(px, py, cell - 2, cell - 2,
                    'tl none' if v >= FL.INF else ('tl hot' if v == 0 else 'tl on'))
            if v < FL.INF:
                sv.text(px + cell / 2 - 1, py + 13, '%d' % v, 'lbl')
                if fl[i] != FL.STOP:
                    arrow(sv, px + cell / 2 - 1, py + cell - 12, fl[i], 14)
    sv.text(20, 20, '숫자는 목표까지의 비용(10 직선 · 14 대각) · 화살표는 경사장',
            None, 'start')
    return sv.save('flow_field.svg')


def fig_clearance():
    """클리어런스 — 좌상단 기준 정사각형 여유 (정리 11.1)."""
    m = MAIN.flowmap()
    cl = FL.clearance(m, 0)
    cell = 30
    sv = Svg(m.w * cell + 300, m.h * cell + 46, '클리어런스 (정리 11.1)')
    for y in range(m.h):
        for x in range(m.w):
            v = cl[y * m.w + x]
            px, py = 20 + x * cell, 30 + y * cell
            sv.rect(px, py, cell - 2, cell - 2, 'tl dim' if v == 0 else 'tl on')
            sv.text(px + cell / 2 - 1, py + cell / 2 + 4, '%d' % v, 'lbl')
    tx = 20 + m.w * cell + 16
    sv.text(tx, 44, 'clear[x][y] = 그 칸을 좌상단으로 하는', 'lbl', 'start')
    sv.text(tx, 60, '모두 통행 가능한 정사각형의 최대 변', 'lbl', 'start')
    sv.text(tx, 84, '= 1 + min(오른쪽, 아래, 오른쪽아래)', 'lbl', 'start')
    sv.text(tx, 108, '오른쪽 아래에서 한 번 훑으면 끝 — O(맵)', 'lbl', 'start')
    sv.text(tx, 132, '크기 s 유닛은 clear >= s 인 칸만 지난다', 'lbl', 'start')
    return sv.save('clearance.svg')


# ── 14부: 예약 불변식 ───────────────────────────────────────────────────────
def fig_reservation():
    """불변식 R — 걸음 도중에는 두 칸을 쥔다."""
    cell, y0 = 54, 60
    sv = Svg(660, 250, '타일 예약 불변식 R — 두 칸을 쥐는 구간')
    steps = [('걸음 전', [0], []),
             ('걸음 시작', [0, 1], [1]),
             ('진행 중', [0, 1], []),
             ('도착', [1], [])]
    for k, (label, held, new) in enumerate(steps):
        ox = 24 + k * 158
        sv.text(ox + cell, 34, label, 'lbl')
        for t in (0, 1):
            cls = 'tl on' if t in held else 'tl'
            if t in new:
                cls = 'tl hot'
            sv.rect(ox + t * (cell + 6), y0, cell, cell, cls)
            sv.text(ox + t * (cell + 6) + cell / 2, y0 + cell / 2 + 4,
                    'a' if t == 0 else 'b', 'lbl')
        if k < 3:
            prog = [0, 0.15, 0.7, 1.0][k]
            sv.circle(ox + prog * (cell + 6) + cell / 2, y0 + cell + 26, 9, 'tl hot')
        else:
            sv.circle(ox + (cell + 6) + cell / 2, y0 + cell + 26, 9, 'tl hot')
        sv.text(ox + cell, y0 + cell + 56,
                ['resv[a]=나', 'resv[b]=나 (두 칸)', 'prog < 1', 'resv[a]=0'][k],
                'lbl')
    sv.text(24, 20, '한 칸만 쥐면 두 유닛이 서로의 칸으로 동시에 들어가 겹친다',
            None, 'start')
    sv.text(24, 232,
            '주황 칸이 이번 걸음에 새로 쥔 칸 · 아래 원이 유닛의 실제 위치', 'lbl',
            'start')
    return sv.save('reservation.svg')


# ── 16부: 포물선 ────────────────────────────────────────────────────────────
def fig_parabola():
    """정리 15.2 — 이산 적분의 착탄 오차는 G·T/2 다."""
    from rts import combat as CB
    T_ = 12
    G = CB.G
    y0 = 0
    vy0 = -F.fp_mul(G, F.fp_div(F.fp(T_), F.fp(2)))
    ys, vy = [], vy0
    y = y0
    for k in range(T_ + 1):
        ys.append(y)
        vy += G
        y += vy
    lo, hi = min(ys), max(ys)
    sv = Svg(620, 260, '포물선 투사체 — 이산 적분과 착탄 오차 (정리 15.2)')
    sx, sy = 40, 40
    w, h = 480, 160

    def px(k):
        return sx + w * k // T_

    def py(v):
        return sy + h * (v - lo) // (hi - lo if hi > lo else 1)

    sv.line(sx, py(y0), sx + w, py(y0))
    d = 'M%g %g' % (px(0), py(ys[0]))
    for k in range(1, len(ys)):
        d += ' L%g %g' % (px(k), py(ys[k]))
    sv.path(d)
    for k in range(0, len(ys)):
        sv.circle(px(k), py(ys[k]), 3, 'tl hot')
    sv.text(sx, 24, '수평 등속 · 수직은 매 틱 vy += G (G = %d, 0.025 px/틱²)' % G,
            None, 'start')
    sv.text(sx - 4, py(y0) - 6, '발사 높이', 'lbl', 'start')
    sv.text(px(T_) + 6, py(ys[-1]) + 4,
            '착탄 = y1 + G·T/2 (%d/65536 px)' % (G * T_ // 2), 'lbl', 'start')
    sv.text(sx, 236,
            '이산과 연속의 차이는 G·T/2 이며 T=12 에서 화면 0.15px — '
            '보정하지 않기로 한 결정이다', 'lbl', 'start')
    return sv.save('parabola.svg')


# ── 19부: 락스텝 타임라인 ───────────────────────────────────────────────────
def fig_lockstep():
    """명령의 실행 틱은 보낼 때 정해진다. 지터는 도착만 늦춘다."""
    sv = Svg(720, 230, '락스텝 타임라인 — 실행 틱은 보낼 때 정해진다')
    x0, dx = 118, 52
    for k in range(11):
        x = x0 + k * dx
        sv.line(x, 40, x, 176)
        sv.text(x, 32, 't+%d' % k, 'lbl')
    for row, (name, jit) in enumerate((('플레이어 0', 0), ('플레이어 1', 2))):
        y = 70 + row * 56
        sv.text(12, y + 4, name, 'lbl', 'start')
        sv.rect(x0 - 10, y - 14, 20, 20, 'tl hot')          # 보낸 틱
        sv.rect(x0 + (2 + jit) * dx - 10, y - 14, 20, 20, 'tl cool')   # 도착
        sv.rect(x0 + 2 * dx - 10, y + 14, 20, 20, 'tl on')  # 실행
        arrow(sv, x0 + dx, y - 4, 2, 26)
    sv.text(x0 - 10, 200, '주황 = 보냄', 'lbl', 'start')
    sv.text(x0 + 130, 200, '파랑 = 도착(지터 0~2틱)', 'lbl', 'start')
    sv.text(x0 + 330, 200, '노랑 = 실행 (항상 t+2)', 'lbl', 'start')
    sv.text(24, 220,
            '늦게 도착하면 그 틱을 기다릴 뿐이다 — 앞당겨 실행하는 경로는 없다',
            'lbl', 'start')
    return sv.save('lockstep_timeline.svg')


# ── 6부: 거리 척도의 오차 ───────────────────────────────────────────────────
def fig_metrics_error():
    """정수 척도가 유클리드에서 얼마나 벗어나는가 — 천분율 막대."""
    pairs = MAIN.PAIRS_M
    sv = Svg(700, 300, '거리 척도의 오차 — 유클리드 대비 천분율')
    x0, y0, bw, h = 70, 40, 36, 180
    mid = y0 + h // 2
    sv.line(x0 - 10, mid, x0 + len(pairs) * bw + 10, mid)
    worst = 0
    for k, (dx, dy) in enumerate(pairs):
        eu = F.isqrt((dx * dx + dy * dy) * 1000000)
        e83 = F.d83(dx, dy) * 1000000 // eu - 1000
        eab = F.dab(dx, dy) * 1000000 // eu - 1000
        worst = max(worst, abs(e83), abs(eab))
        for j, (v, cls) in enumerate(((e83, 'tl on'), (eab, 'tl hot'))):
            bh = v * (h // 2) // 120
            x = x0 + k * bw + j * 15
            sv.rect(x, mid if bh >= 0 else mid + bh, 12, abs(bh) if bh else 1, cls)
    sv.text(x0, 24, 'd83(왼쪽·노랑)과 α-max β-min(오른쪽·주황) · '
            '위가 과대평가', None, 'start')
    sv.text(x0, mid + h // 2 + 34,
            '최악 오차 %d/1000 · 눈금 한 칸 = 120/1000' % worst, 'lbl', 'start')
    sv.text(x0, mid + h // 2 + 52,
            '옥타일은 유클리드 근사가 아니므로 여기 넣지 않는다 — '
            '8방향 격자의 참 길이다', 'lbl', 'start')
    for k, (dx, dy) in enumerate(pairs):
        sv.text(x0 + k * bw + 14, mid + h // 2 + 16, '%d,%d' % (dx, dy), 'lbl')
    return sv.save('metrics_error.svg')


# ── 13부: HPA* 클러스터 ─────────────────────────────────────────────────────
def fig_hpa_clusters():
    """클러스터 경계와 입구 — 추상 그래프가 왜 작아지는가."""
    from rts import hpa as HP
    m = T.TMap.load_text(io.open(os.path.join(BASE, 'golden', 'map_1.txt'),
                                 encoding='utf-8').read())
    cell = 13
    sv = Svg(m.w * cell + 300, m.h * cell + 40, 'HPA* 클러스터와 입구')
    for y in range(m.h):
        for x in range(m.w):
            sv.rect(20 + x * cell, 26 + y * cell, cell - 1, cell - 1,
                    'tl' if m.passable_terrain(x, y, 0) else 'tl dim')
    for c in range(0, m.w + 1, C.CLUSTER):
        sv.line(20 + c * cell - 1, 26, 20 + c * cell - 1, 26 + m.h * cell, 'ax')
    for c in range(0, m.h + 1, C.CLUSTER):
        sv.line(20, 26 + c * cell - 1, 20 + m.w * cell, 26 + c * cell - 1, 'ax')
    ent = HP.entrances(m, 0)
    for (a, b) in ent:
        for (x, y) in (a, b):
            sv.rect(20 + x * cell, 26 + y * cell, cell - 1, cell - 1, 'tl hot')
    tx = 20 + m.w * cell + 16
    sv.text(tx, 44, '맵 %dx%d = %d칸' % (m.w, m.h, m.w * m.h), 'lbl', 'start')
    sv.text(tx, 62, '클러스터 한 변 %d → %d개' % (C.CLUSTER,
                                                 (m.w // C.CLUSTER) ** 2),
            'lbl', 'start')
    sv.text(tx, 80, '입구(전이) %d개 — 주황' % len(ent), 'lbl', 'start')
    sv.text(tx, 104, '추상 그래프의 노드는 입구뿐이다.', 'lbl', 'start')
    sv.text(tx, 120, '칸 %d개 대신 노드 %d개를 훑는다.'
            % (m.w * m.h, len(ent) * 2), 'lbl', 'start')
    sv.text(tx, 144, 'HPA* 는 최적이 아니다 — 실측 1.000~1.321배', 'lbl', 'start')
    return sv.save('hpa_clusters.svg')


# ── 13부: JPS 가지치기 ──────────────────────────────────────────────────────
def fig_jps_prune():
    """강제 이웃 — 막힌 칸이 있어야 대각 이웃을 살려 둔다."""
    sv = Svg(620, 250, 'JPS 가지치기 — 강제 이웃 규칙')
    cell = 40
    for k, (blocked, label) in enumerate(((False, '막힌 칸이 없으면'),
                                          (True, '위가 막혀 있으면'))):
        ox = 40 + k * 300
        for gy in range(3):
            for gx in range(4):
                cls = 'tl'
                if blocked and gx == 2 and gy == 0:
                    cls = 'tl dim'
                sv.rect(ox + gx * cell, 60 + gy * cell, cell - 2, cell - 2, cls)
        sv.circle(ox + cell + cell / 2 - 1, 60 + cell + cell / 2 - 1, 10, 'tl hot')
        arrow(sv, ox + cell / 2, 60 + cell + cell / 2 - 1, 2, 26)
        if blocked:
            sv.rect(ox + 3 * cell, 60, cell - 2, cell - 2, 'tl hot')
            sv.text(ox + 3 * cell + cell / 2, 60 + cell / 2 + 4, '강제', 'lbl')
        sv.text(ox + 2 * cell, 40, label, 'lbl')
        sv.text(ox + 2 * cell, 60 + 3 * cell + 22,
                '이웃을 전부 버린다' if not blocked else '대각 하나를 살린다',
                'lbl')
    sv.text(40, 24, '동쪽으로 들어온 유닛은 동쪽만 보면 된다 — '
            '그 규칙이 깨지는 자리가 강제 이웃이다', None, 'start')
    sv.text(40, 236, '점프는 강제 이웃이나 목표를 만날 때까지 한 방향으로 달린다.',
            'lbl', 'start')
    return sv.save('jps_prune.svg')


# ── 16부: 피해 분포 ─────────────────────────────────────────────────────────
def fig_damage_dist():
    """피해는 최대치의 50~100 % 균등 — 기대값과 실제 도수."""
    from rts import combat as CB
    from rts import rng as R
    basic, pierce, armour = 12, 8, 3
    mx = CB.max_damage(basic, pierce, armour)
    lo = CB.damage_lo(mx)
    r = R.LCG(12345)
    hist = {}
    n = 4000
    for _k in range(n):
        v = CB.roll_damage(r, basic, pierce, armour)
        hist[v] = hist.get(v, 0) + 1
    sv = Svg(660, 280, '피해 분포 — 기본 %d · 관통 %d · 방어 %d' % (basic, pierce, armour))
    x0, y0, h = 60, 40, 170
    top = max(hist.values())
    bw = 520 // (mx - lo + 1)
    for k, v in enumerate(range(lo, mx + 1)):
        c = hist.get(v, 0)
        bh = c * h // top
        sv.rect(x0 + k * bw, y0 + h - bh, bw - 4, bh, 'tl on')
        sv.text(x0 + k * bw + bw / 2 - 2, y0 + h + 14, '%d' % v, 'lbl')
    e = CB.expect100(basic, pierce, armour)
    ex = x0 + (e / 100.0 - lo) * bw + bw / 2
    sv.line(ex, y0 - 6, ex, y0 + h + 4, 'ax')
    sv.text(ex, y0 - 12, 'E = %d.%02d' % (e // 100, e % 100), 'lbl')
    sv.text(x0, 24, 'mx = 기본 − 방어 + 관통 = %d · lo = ceil(mx/2) = %d · '
            '%d회 시뮬' % (mx, lo, n), None, 'start')
    sv.text(x0, y0 + h + 40,
            '홀수 mx 에서만 E = 0.75·mx + 0.25 다 — 올림이 한 칸 올리기 때문이다.',
            'lbl', 'start')
    sv.text(x0, y0 + h + 58,
            '명세 초안은 이것을 짝수라고 적고 있었고, 시험이 잡았다.', 'lbl', 'start')
    return sv.save('damage_dist.svg')


# ── 17부: 기술 트리 ─────────────────────────────────────────────────────────
def fig_tech_tree():
    """DAG 와 위상 정렬 — 선행이 둘인 노드는 공장뿐이다."""
    from rts import econ as E
    sv = Svg(640, 300, '기술 트리 DAG — 위상 정렬이 실제로 필요한 자리')
    pos = {C.HQ: (90, 60), C.HARV: (300, 40), C.REF: (300, 90),
           C.BARR: (300, 150), C.POW: (90, 220), C.INF: (500, 110),
           C.ARCHER: (500, 150), C.TOWER: (500, 190), C.FACT: (300, 220),
           C.TANK: (500, 240), C.MORTAR: (500, 275)}
    for k, (x, y) in pos.items():
        for pre in C.PREREQ[k]:
            if pre in pos:
                px, py = pos[pre]
                sv.line(px + 46, py + 10, x - 4, y + 10, 'ax')
    for k, (x, y) in pos.items():
        cls = 'tl hot' if k == C.FACT else ('tl on' if C.IS_BUILDING[k] else 'tl')
        sv.rect(x, y, 46, 22, cls)
        sv.text(x + 23, y + 15, C.NAME[k], 'lbl')
    order = E.topo_order()
    sv.text(20, 22, '주황 = 선행이 둘인 유일한 노드(공장) — '
            '그래서 위상 정렬을 넣었다', None, 'start')
    sv.text(20, 290, '칸 위상 정렬 순서: ' +
            ' '.join(C.NAME[k] for k in order if C.NAME[k]), 'lbl', 'start')
    return sv.save('tech_tree.svg')


# ── 15부: 안개 세 평면 ──────────────────────────────────────────────────────
def fig_fog_planes():
    """explored · count · 4단계 — 왜 칸당 1바이트인가."""
    from rts import fog as FG
    W = 16
    fg = FG.Fog(W, W, 1)
    for (x, y), r in (((4, 5), 3), ((9, 7), 4)):
        fg.add_sight(0, x, y, r)
    fg.remove_sight(0, 4, 5, 3)
    fg.add_sight(0, 5, 5, 3)
    cell = 15
    sv = Svg(3 * (W * cell + 24) + 20, W * cell + 60, '안개의 세 평면')
    titles = ['explored (0/1)', 'count (참조 카운트)', 'level (0~3 렌더 단계)']
    for pane in range(3):
        ox = 20 + pane * (W * cell + 24)
        sv.text(ox + W * cell / 2, 22, titles[pane], 'lbl')
        for y in range(W):
            for x in range(W):
                i = y * W + x
                if pane == 0:
                    v = fg.explored[0][i]
                    cls = 'tl on' if v else 'tl dim'
                elif pane == 1:
                    v = fg.count[0][i]
                    cls = ['tl dim', 'tl on', 'tl hot'][min(v, 2)]
                else:
                    v = fg.level(0, x, y)
                    cls = ['tl dim', 'tl', 'tl cool', 'tl on'][v]
                sv.rect(ox + x * cell, 30 + y * cell, cell - 1, cell - 1, cls)
    sv.text(20, W * cell + 48,
            '참조 카운트는 비트로 담을 수 없다. explored 만 비트로 접어 봐야 '
            '4096바이트를 아낄 뿐이다.', 'lbl', 'start')
    return sv.save('fog_planes.svg')


# ── 16부: 란체스터 ──────────────────────────────────────────────────────────
def fig_lanchester():
    """제곱 법칙 — 정수 이산 시뮬과 폐형해를 나란히."""
    import math
    a0, b0, al, be = 50, 40, 1311, 1311      # 골든 11절의 여섯째 줄
    a, b = F.fp(a0), F.fp(b0)
    ha, hb = [a], [b]
    while a >= F.FP_ONE and b >= F.FP_ONE and len(ha) < 200:
        da, db = F.fp_mul(be, b), F.fp_mul(al, a)
        a = max(0, a - da)
        b = max(0, b - db)
        ha.append(a)
        hb.append(b)
    n = len(ha) - 1
    sv = Svg(660, 300, '란체스터 제곱 법칙 — 50 대 40')
    x0, y0, w, h = 60, 40, 480, 190
    top = F.fp(a0)

    def px(k):
        return x0 + w * k // max(n, 1)

    def py(v):
        return y0 + h - h * v // top

    for series, cls in ((ha, 'ax'), (hb, 'gd')):
        d = 'M%g %g' % (px(0), py(series[0]))
        for k in range(1, len(series)):
            d += ' L%g %g' % (px(k), py(series[k]))
        sv.path(d, cls)
    # 폐형해 (실수 — 도구는 실수를 써도 된다)
    alf, bef = al / 65536.0, be / 65536.0
    inv = alf * a0 * a0 - bef * b0 * b0
    tstar = (1.0 / (2 * math.sqrt(alf * bef))) * math.log(
        (math.sqrt(alf) * a0 + math.sqrt(bef) * b0)
        / (math.sqrt(alf) * a0 - math.sqrt(bef) * b0))
    sv.line(px(0), py(F.fp(int(math.sqrt(inv / alf)))),
            px(n), py(F.fp(int(math.sqrt(inv / alf)))))
    sv.text(px(n) + 6, py(F.fp(int(math.sqrt(inv / alf)))) + 4,
            '√(αA₀²−βB₀²)/α = %.1f' % math.sqrt(inv / alf), 'lbl', 'start')
    sv.text(x0, 24, '굵은 선 A(50기) · 가는 선 B(40기) · α = β · 가로는 틱',
            None, 'start')
    sv.text(x0, y0 + h + 26,
            '이산 시뮬은 %d틱에 B 를 0 으로 만들었고 폐형해는 %.1f틱을 준다 — '
            '부대가 작을수록 이산성이 지배한다' % (n, tstar), 'lbl', 'start')
    sv.text(x0, y0 + h + 44,
            'α·A² − β·B² 는 불변이다(정리 15.3). 그래서 수가 2배면 전투력이 4배다.',
            'lbl', 'start')
    for k in range(0, n + 1, max(1, n // 8)):
        sv.text(px(k), y0 + h + 12, '%d' % k, 'lbl')
    return sv.save('lanchester.svg')


# ── 17부: 수입률 ────────────────────────────────────────────────────────────
def fig_income_rate():
    """정리 16.1 — 왕복 거리가 늘면 수입은 이렇게 준다."""
    from rts import econ as E
    v = C.SPEED[C.HARV] // C.TILE
    xs = list(range(0, 33))
    ys = [E.income10000(d, v) for d in xs]
    sv = Svg(660, 300, '채집 수입률 — 정리 16.1')
    x0, y0, w, h = 60, 40, 480, 190
    top = ys[0]

    def px(k):
        return x0 + w * k // xs[-1]

    def py(val):
        return y0 + h - h * val // top

    d = 'M%g %g' % (px(0), py(ys[0]))
    for k in range(1, len(ys)):
        d += ' L%g %g' % (px(xs[k]), py(ys[k]))
    sv.path(d)
    for k in (0, 4, 8, 16, 32):
        sv.circle(px(k), py(ys[k]), 4, 'tl hot')
        sv.text(px(k), py(ys[k]) - 10, '%d.%02d' % (ys[k] // 10000,
                                                    ys[k] % 10000 // 100), 'lbl')
        sv.text(px(k), y0 + h + 14, '%d' % k, 'lbl')
    sv.text(x0, 24, '가로: 왕복 타일 · 세로: 크레딧/틱 (채집기 속도 1.2 px/틱)',
            None, 'start')
    sv.text(x0, y0 + h + 38,
            'rate = 적재 / (2·d/v + 적재/채굴속도 + 반납틱) — '
            '분모의 세 항이 왕복·채굴·반납이다', 'lbl', 'start')
    sv.text(x0, y0 + h + 56,
            'd = 0 이어도 100/(20+12) = 3.125 를 넘지 못한다. '
            '정제소를 광맥에 붙여도 상한이 있다.', 'lbl', 'start')
    sv.text(x0, y0 + h + 74,
            '1200틱 시나리오의 실측은 3333/10000 — 차이는 채집기끼리의 길막이다.',
            'lbl', 'start')
    return sv.save('income_rate.svg')


# ── 22부: PIT 분주값 오차 ───────────────────────────────────────────────────
def fig_pit_divisor():
    """정수 분주값이 만드는 음정 오차 — 센트."""
    import math
    from rts import speaker as SK
    sv = Svg(700, 280, 'PIT 분주값의 음정 오차 (센트)')
    x0, y0, h = 50, 40, 170
    mid = y0 + h // 2
    bw = 600 // len(SK.NOTE_HZ)
    worst, worst_note = 0.0, ''
    for k, f in enumerate(SK.NOTE_HZ):
        act = SK.actual100(f) / 100.0
        cents = 1200 * math.log(act / f) / math.log(2)
        if abs(cents) > abs(worst):
            worst, worst_note = cents, SK.NOTE_NAME[k]
        bh = int(cents * (h // 2) / 6.0)
        sv.rect(x0 + k * bw, mid if bh >= 0 else mid + bh, bw - 3,
                abs(bh) if bh else 1, 'tl hot' if cents < 0 else 'tl on')
        if k % 2 == 0:
            sv.text(x0 + k * bw + bw / 2, mid + h // 2 + 16,
                    SK.NOTE_NAME[k], 'lbl')
    sv.line(x0 - 8, mid, x0 + len(SK.NOTE_HZ) * bw + 8, mid)
    sv.text(x0, 24, '분주값 = round(1193182 / f) 이므로 실제 음은 목표에서 조금 벗어난다',
            None, 'start')
    sv.text(x0, mid + h // 2 + 40,
            '최악 %s %+.1f센트 — 사람이 겨우 구별하는 한계가 5센트 근처다'
            % (worst_note, worst), 'lbl', 'start')
    sv.text(x0, mid + h // 2 + 58,
            '센트는 로그가 필요해 엔진이 아니라 도구가 계산한다. '
            '엔진은 분주값과 몫·나머지만 낸다.', 'lbl', 'start')
    sv.text(x0, mid + h // 2 + 76, '눈금 한 칸 = 6센트', 'lbl', 'start')
    return sv.save('pit_divisor.svg')


# ── 5부: 미니맵 축소 ────────────────────────────────────────────────────────
def fig_minimap_scale():
    """최근접과 다수결 — 128 맵을 64 픽셀에 넣을 때 갈리는 지점."""
    from rts import render as RD
    m = T.TMap.load_text(io.open(os.path.join(BASE, 'golden', 'map_start.txt'),
                                 encoding='utf-8').read())
    cell = 5
    sv = Svg(2 * (C.MINI_W * cell + 30) + 240, C.MINI_H * cell + 70,
             '미니맵 축소 — 최근접 대 다수결')
    for pane, fn in enumerate((RD.minimap_nearest, RD.minimap_majority)):
        ox = 20 + pane * (C.MINI_W * cell + 30)
        sv.text(ox + C.MINI_W * cell / 2, 22,
                ['최근접(한 점만 본다)', '다수결(블록 전체를 센다)'][pane], 'lbl')
        for sy in range(C.MINI_H):
            for sx in range(C.MINI_W):
                t = fn(m, sx, sy)
                cls = {T.WATER: 'tl cool', T.ROCK: 'tl dim', T.ORE: 'tl hot',
                       T.HILL: 'tl dim'}.get(t, 'tl on')
                sv.rect(ox + sx * cell, 30 + sy * cell, cell, cell, cls)
    tx = 20 + 2 * (C.MINI_W * cell + 30)
    sv.text(tx, 46, '이 맵은 64×64 이고 미니맵도 64×64 다.', 'lbl', 'start')
    sv.text(tx, 62, '한 타일이 한 픽셀이므로 두 방식이 같다.', 'lbl', 'start')
    sv.text(tx, 86, '맵이 128 이 되면 갈린다 — 최근접은', 'lbl', 'start')
    sv.text(tx, 102, '가느다란 길을 통째로 놓치고,', 'lbl', 'start')
    sv.text(tx, 118, '다수결은 놓치지 않는 대신 네 배 느리다.', 'lbl', 'start')
    sv.text(tx, 142, '축소 코드를 미리 갖춰 두는 이유다.', 'lbl', 'start')
    return sv.save('minimap_scale.svg')


# ── 8부: 5방향으로 8방향 ────────────────────────────────────────────────────
def fig_sprite_mirror():
    """그린 것은 다섯 방향뿐 — 나머지 셋은 좌우 반전이다."""
    sv = Svg(660, 250, '5장으로 8방향 — 좌우 반전')
    r = 74
    cx, cy = 200, 130
    for d in range(8):
        x = cx + F.DX[d] * r
        y = cy + F.DY[d] * r
        drawn = d <= 4
        sv.rect(x - 20, y - 20, 40, 40, 'tl on' if drawn else 'tl cool')
        sv.text(x, y - 2, F.DNAME[d], 'lbl')
        sv.text(x, y + 12, '그림 %d' % (d if drawn else 8 - d), 'lbl')
    sv.circle(cx, cy, 14, 'tl hot')
    sv.text(cx, cy + 4, '유닛', 'lbl')
    tx = 360
    sv.text(tx, 44, '노랑 = 실제로 그린 다섯 장 (N NE E SE S)', 'lbl', 'start')
    sv.text(tx, 62, '파랑 = 반전으로 얻는 세 장 (SW W NW)', 'lbl', 'start')
    sv.text(tx, 90, '메모리와 아티스트 시간을 동시에 아끼는', 'lbl', 'start')
    sv.text(tx, 106, '도스 시절의 표준 요령이다.', 'lbl', 'start')
    sv.text(tx, 134, '반전은 블릿 안에서 런의 순서와', 'lbl', 'start')
    sv.text(tx, 150, '런 안의 픽셀 순서를 뒤집어 처리한다 —', 'lbl', 'start')
    sv.text(tx, 166, '별도의 스프라이트를 만들지 않는다.', 'lbl', 'start')
    sv.text(tx, 194, '상자 안에서 뒤집으므로 기준점이 1px 옮겨진다.', 'lbl', 'start')
    sv.text(tx, 210, '세 언어가 같은 자리에 그리는 것이 그보다 중요하다.',
            'lbl', 'start')
    return sv.save('sprite_mirror.svg')


# ── 19부: 상태 해시 바이트열 ────────────────────────────────────────────────
def fig_hash_bytes():
    """해시에 무엇이 어떤 순서로 들어가는가 (§18.4)."""
    sv = Svg(660, 300, '상태 해시의 바이트열 — 순서가 명세다')
    rows = [('틱', 4), ('rng 상태', 4), ('플레이어×4: 크레딧', 4),
            ('  인구 사용', 2), ('  인구 상한', 2), ('엔티티 i: alive', 1),
            ('  owner kind tx ty', 4), ('  hp', 2), ('  dir state', 2),
            ('  px py', 8), ('  target load', 4), ('  prog', 4),
            ('  from_t to_t', 4), ('  cool timer', 4),
            ('투사체: 개수 + 항목들', 2), ('생산 큐', 1), ('광맥 잔량', 4),
            ('map_hash', 4)]
    y = 44
    for name, nbytes in rows:
        hot = name.strip().startswith('cool')
        sv.rect(300, y - 11, min(nbytes * 22, 200), 15,
                'tl hot' if hot else 'tl on')
        sv.text(296, y, name, 'lbl', 'end')
        sv.text(300 + min(nbytes * 22, 200) + 8, y, '%d바이트' % nbytes,
                'lbl', 'start')
        y += 14
    sv.text(20, 24, 'FNV-1a 32비트에 이 순서로 흘려 넣는다', None, 'start')
    sv.text(20, y + 8,
            '주황: cool·timer 를 빠뜨리면 재장전이 한 틱 어긋나도 해시가 같다.',
            'lbl', 'start')
    sv.text(20, y + 24,
            '그러면 디싱크가 첫 발이 어긋난 다음 틱에야 잡힌다.', 'lbl', 'start')
    return sv.save('hash_bytes.svg')


def main():
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    made = [fig_autotile_classes(), fig_autotile_corner(), fig_circle_spans(),
            fig_circle_counterexample(), fig_metrics_error(), fig_hpa_clusters(),
            fig_jps_prune(), fig_flow_field(), fig_clearance(),
            fig_reservation(), fig_damage_dist(), fig_tech_tree(),
            fig_fog_planes(), fig_parabola(), fig_lanchester(),
            fig_income_rate(), fig_pit_divisor(), fig_minimap_scale(),
            fig_sprite_mirror(), fig_hash_bytes(), fig_lockstep()]
    for n in made:
        print('  deck/figs/%s' % n)
    print('도해 %d장' % len(made))


main()
