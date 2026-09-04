# -*- coding: utf-8 -*-
"""덱에 들어갈 인라인 SVG 도해 생성기.

   육각 격자 도해를 손으로 좌표 찍어 그리면 반드시 어긋난다. 그래서 배치
   규칙(SPEC §4.1)을 코드로 써서 그린다 — 도해와 엔진이 같은 공식을 쓰므로
   그림이 거짓말을 할 수 없다.

   확인: sh tools/check_figs.sh <디렉터리>  (rsvg-convert 로 PNG 렌더)
"""
import io
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, 'deck', 'figs')
SQRT3 = math.sqrt(3.0)

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
DIR_NAMES = ('E', 'NE', 'NW', 'W', 'SW', 'SE')


# ------------------------------------------------------------------ 기본 도구
def hexpoints(cx, cy, r, pointy=True):
    pts = []
    for i in range(6):
        ang = math.radians(60 * i - (90 if pointy else 0))
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def axial_xy(q, r, R, ox, oy):
    """축좌표 → 화면 좌표(뾰족머리). 엔진의 배치 규칙과 같은 식이다."""
    return (ox + SQRT3 * R * (q + r / 2.0), oy + 1.5 * R * r)


def poly(pts, cls='hx', extra=''):
    d = ' '.join('%.2f,%.2f' % p for p in pts)
    return '<polygon class="%s" points="%s"%s/>' % (cls, d, extra)


def hexat(cx, cy, r, cls='hx', pointy=True):
    return poly(hexpoints(cx, cy, r, pointy), cls)


def txt(x, y, s, cls=None, anchor='middle', size=None):
    c = ' class="%s"' % cls if cls else ''
    z = ' font-size="%s"' % size if size else ''
    return ('<text x="%.1f" y="%.1f" text-anchor="%s"%s%s>%s</text>'
            % (x, y, anchor, c, z, s))


def arrow(x1, y1, x2, y2, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ''
    return '<path class="ax" d="M %.1f %.1f L %.1f %.1f"%s marker-end="url(#ah)"/>' % (
        x1, y1, x2, y2, d)


def rect(x, y, w, h, fill='none', stroke='#4a6b34', sw=1.2, extra=''):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
            'stroke="%s" stroke-width="%s"%s/>' % (x, y, w, h, fill, stroke, sw, extra))


DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#b04a2a"/></marker></defs>')


def svg(w, h, body, title=''):
    return ('<svg class="diag" viewBox="0 0 %d %d" role="img" aria-label="%s">'
            '<title>%s</title>%s\n%s\n</svg>' % (w, h, title, title, DEFS, body))


def write(name, content):
    io.open(os.path.join(FIGS, name), 'w', encoding='utf-8').write(content + '\n')


# ------------------------------------------------------------ 1. 사각 vs 육각
def fig_sqhex():
    b = []
    ox, oy, s = 24, 48, 36
    for r in range(3):
        for c in range(3):
            x, y = ox + c * s, oy + r * s
            b.append(rect(x, y, s, s, '#f4d98a' if (r, c) == (1, 1) else '#dfe6cd'))
            if (r, c) != (1, 1):
                b.append(txt(x + s / 2, y + s / 2 + 4,
                             '1.41' if (r != 1 and c != 1) else '1', 'lbl'))
    b.append(txt(ox + 1.5 * s, 24, '사각 격자 · 8이웃'))
    b.append(txt(ox + 1.5 * s, oy + 3 * s + 22, '대각선이 1.41배 멀다', 'lbl'))

    cx, cy, R = 300, 108, 28
    b.append(hexat(cx, cy, R, 'hx on'))
    for i in range(6):
        nx, ny = cx + SQRT3 * R * math.cos(math.radians(60 * i)), \
                 cy + SQRT3 * R * math.sin(math.radians(60 * i))
        b.append(hexat(nx, ny, R))
        b.append(txt(nx, ny + 4, '1', 'lbl'))
    b.append(txt(cx, 24, '육각 격자 · 6이웃'))
    b.append(txt(cx, oy + 3 * s + 22, '여섯 방향 모두 거리 1', 'lbl'))
    return svg(400, 200, '\n'.join(b), '사각 격자와 육각 격자의 이웃 비교')


# ------------------------------------------------------------- 2. 오프셋 배치
def fig_offsets():
    b = []
    r = 21
    for row in range(4):
        for col in range(4):
            cx = 44 + col * SQRT3 * r + (row & 1) * (SQRT3 * r / 2)
            cy = 58 + row * 1.5 * r
            b.append(hexat(cx, cy, r))
            b.append(txt(cx, cy + 3, '%d,%d' % (col, row), 'lbl', size=8))
    b.append(txt(110, 24, 'odd-r · 뾰족머리 · 행이 어긋난다'))
    for col in range(4):
        for row in range(4):
            cx = 285 + col * 1.5 * r
            cy = 58 + row * SQRT3 * r + (col & 1) * (SQRT3 * r / 2)
            b.append(hexat(cx, cy, r, 'hx', pointy=False))
            b.append(txt(cx, cy + 3, '%d,%d' % (col, row), 'lbl', size=8))
    b.append(txt(332, 24, 'odd-q · 납작머리 · 열이 어긋난다'))
    b.append(txt(210, 200, '이 문서의 엔진은 왼쪽(odd-r)을 쓴다', 'lbl'))
    return svg(420, 212, '\n'.join(b), '두 가지 오프셋 배치')


# ------------------------------------------------------------------ 3. 축좌표
def fig_axial():
    b = []
    R, ox, oy = 30, 200, 140
    for r in range(-2, 3):
        for q in range(-2, 3):
            if abs(q) + abs(r) + abs(q + r) > 4:
                continue
            cx, cy = axial_xy(q, r, R, ox, oy)
            b.append(hexat(cx, cy, R, 'hx on' if (q, r) == (0, 0) else 'hx'))
            b.append(txt(cx, cy + 4, '%d,%d' % (q, r), 'lbl', size=10))
    b.append(txt(200, 22, '축좌표 (q, r) — 반경 2 안의 19칸'))
    ex, ey = axial_xy(1, 0, R, ox, oy)
    sx, sy = axial_xy(0, 1, R, ox, oy)
    b.append(arrow(ox, oy, ex - 10, ey))
    b.append(txt((ox + ex) / 2, ey - 8, '+q', 'lbl'))
    b.append(arrow(ox, oy, sx - 6, sy - 8))
    b.append(txt((ox + sx) / 2 - 14, (oy + sy) / 2 + 4, '+r', 'lbl', 'end'))
    b.append(txt(200, 272, '+r 축은 아래가 아니라 남동쪽을 향한다 — 여기서 헷갈리면 전부 어긋난다', 'lbl'))
    return svg(400, 286, '\n'.join(b), '축좌표계')


# ------------------------------------------------------------------ 4. 큐브 좌표
def fig_cube():
    b = []
    R, ox, oy = 34, 200, 126
    for (q, r) in ((0, 0),) + tuple((q, r) for q, r in
                                    ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))):
        cx, cy = axial_xy(q, r, R, ox, oy)
        b.append(hexat(cx, cy, R, 'hx on' if (q, r) == (0, 0) else 'hx'))
        b.append(txt(cx, cy - 1, '%d,%d,%d' % (q, -q - r, r), 'lbl', size=9))
        b.append(txt(cx, cy + 11, 'x  y  z', 'lbl', size=7))
    b.append(txt(200, 22, '큐브 좌표 — 언제나 x + y + z = 0'))
    b.append(txt(200, 246, '한 칸 움직이면 두 성분이 ±1, 나머지 하나는 그대로다', 'lbl'))
    return svg(400, 258, '\n'.join(b), '큐브 좌표계')


# --------------------------------------------------------------- 5. 헥스 기하
def fig_hexgeom():
    S, ox, oy = 4.2, 120, 34
    pts = [(16, 0), (32, 8), (32, 24), (16, 32), (0, 24), (0, 8)]
    d = ' '.join('%.1f,%.1f' % (ox + x * S, oy + y * S) for x, y in pts)
    b = ['<polygon class="hx" points="%s"/>' % d]
    for (x, y) in pts:
        px, py = ox + x * S, oy + y * S
        b.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#b04a2a"/>' % (px, py))
        if x == 0:
            b.append(txt(px - 8, py + 4, '(%d,%d)' % (x, y), 'lbl', 'end', 9))
        elif x == 32:
            b.append(txt(px + 8, py + 4, '(%d,%d)' % (x, y), 'lbl', 'start', 9))
        else:
            b.append(txt(px, py - 8 if y == 0 else py + 16, '(%d,%d)' % (x, y), 'lbl', size=9))
    b.append('<path class="ax" d="M %.1f %.1f L %.1f %.1f"/>'
             % (ox, oy + 32 * S + 26, ox + 32 * S, oy + 32 * S + 26))
    b.append(txt(ox + 16 * S, oy + 32 * S + 42, '너비 32', 'lbl'))
    b.append('<path class="ax" d="M %.1f %.1f L %.1f %.1f"/>' % (ox - 56, oy, ox - 56, oy + 32 * S))
    b.append(txt(ox - 62, oy + 16 * S, '높이 32', 'lbl', 'end'))
    b.append('<path class="ax" d="M %.1f %.1f L %.1f %.1f" stroke-dasharray="4 3"/>'
             % (ox + 32 * S + 44, oy, ox + 32 * S + 44, oy + 24 * S))
    b.append(txt(ox + 32 * S + 52, oy + 12 * S, '행 간격 24', 'lbl', 'start'))
    b.append(txt(200, 18, '기울기 8/16 = 1/2 — 곱셈 없이 시프트로 변을 그린다', 'lbl'))
    return svg(400, 220, '\n'.join(b), '32x32 늘린 육각형의 꼭짓점')


# ------------------------------------------------------------ 6. 벽돌 + 마스크
def fig_brick():
    S, ox, oy = 3.4, 118, 100
    b = []
    shape = [(16, 0), (32, 8), (32, 24), (16, 32), (0, 24), (0, 8)]
    for (bx, by, lab, cls) in ((-16, -24, 'NW 이웃', 'hx dim'), (16, -24, 'NE 이웃', 'hx dim'),
                               (0, 0, '자기 칸', 'hx on')):
        d = ' '.join('%.1f,%.1f' % (ox + (x + bx) * S, oy + (y + by) * S) for x, y in shape)
        b.append('<polygon class="%s" points="%s"/>' % (cls, d))
        b.append(txt(ox + (16 + bx) * S, oy + (7 + by) * S, lab, 'lbl', size=9))
    b.append(rect(ox, oy, 32 * S, 24 * S, 'none', '#b04a2a', 2, ' stroke-dasharray="5 4"'))
    b.append(txt(ox + 4 * S, oy + 5 * S, '1', None, 'middle', 13))
    b.append(txt(ox + 28 * S, oy + 5 * S, '2', None, 'middle', 13))
    b.append(txt(ox + 16 * S, oy + 15 * S, '0', None, 'middle', 13))
    b.append(txt(ox + 16 * S, oy + 32 * S + 26,
                 '벽돌 32 × 24 — 나눗셈 두 번으로 여기까지 오고,', 'lbl'))
    b.append(txt(ox + 16 * S, oy + 32 * S + 42,
                 '벽돌 안의 소속은 마스크 표를 한 번 읽어 정한다', 'lbl'))
    b.append(txt(200, 20, '위쪽 8줄만 애매하다 — 나머지 16줄은 무조건 자기 칸', 'lbl'))
    return svg(400, 260, '\n'.join(b), '벽돌과 마스크로 하는 픽킹')


# ----------------------------------------------------------------- 7. 마스크 표
def fig_mask():
    b = []
    px = 9.0
    ox, oy = 60, 40
    for oyi in range(24):
        for oxi in range(32):
            if oyi < 8 and oxi < 16 - 2 * oyi:
                col, lab = '#e8a37a', '1'
            elif oyi < 8 and oxi >= 16 + 2 * oyi:
                col, lab = '#8fb0d4', '2'
            else:
                col, lab = '#dfe6cd', '0'
            b.append(rect(ox + oxi * px, oy + oyi * px, px, px, col, '#ffffff', 0.4))
            if oyi in (0, 4, 12) and oxi in (2, 16, 30):
                b.append(txt(ox + oxi * px + px / 2, oy + oyi * px + px - 2, lab, None, 'middle', 7))
    b.append(txt(ox + 16 * px, 24, '768바이트 — 값 1은 NW, 2는 NE, 0은 자기 칸', 'lbl'))
    b.append(txt(ox + 16 * px, oy + 24 * px + 18,
                 '위 8줄만 색이 갈린다. 아래 16줄이 전부 0이라 RLE 로는 거의 공짜다', 'lbl'))
    return svg(400, 300, '\n'.join(b), '픽킹 마스크 표 32x24')


# ------------------------------------------------------------------ 8. 셀 바이트
def fig_cell():
    b = []
    x0, y, w = 34, 44, 40
    bits = [('7', '도로', '#e8a37a'), ('6', '고', '#f4d98a'), ('5', '도', '#f4d98a'),
            ('4', '', '#f4d98a'), ('3', '지', '#cfe0c0'), ('2', '형', '#cfe0c0'),
            ('1', '', '#cfe0c0'), ('0', '', '#cfe0c0')]
    for i, (n, lab, col) in enumerate(bits):
        x = x0 + i * w
        b.append(rect(x, y, w, 44, col))
        b.append(txt(x + w / 2, y - 8, 'b%s' % n, 'lbl'))
        if lab:
            b.append(txt(x + w / 2, y + 27, lab, None, 'middle', 13))
    for (a, c, lab) in ((0, 1, '1비트'), (1, 4, '3비트 · 고도 0–7'), (4, 8, '4비트 · 지형 0–15')):
        b.append('<path class="ax" d="M %d %d L %d %d"/>'
                 % (x0 + a * w, y + 58, x0 + c * w, y + 58))
        b.append(txt(x0 + (a + c) * w / 2, y + 74, lab, 'lbl'))
    b.append(txt(x0 + 4 * w, 22, '한 칸 = 한 바이트 — 메모리를 한 번 읽어 세 정보를 얻는다', 'lbl'))
    return svg(400, 140, '\n'.join(b), '맵 셀 바이트의 비트 배치')


# ------------------------------------------------------------------ 9. 화면 배치
def fig_layout():
    S, ox, oy = 1.1, 46, 34
    b = [rect(ox, oy, 320 * S, 200 * S, '#101010')]
    for (x, y, w, h, col, lab) in ((0, 0, 256, 168, '#3f5a2e', '맵 뷰포트 256×168'),
                                   (256, 0, 64, 200, '#5a5a4a', '패널 64×200'),
                                   (0, 168, 256, 32, '#2e3a4a', '메시지 256×32')):
        b.append(rect(ox + x * S, oy + y * S, w * S, h * S, col, '#eef0e4', 1))
        b.append('<text x="%.1f" y="%.1f" text-anchor="middle" fill="#eef0e4" '
                 'font-size="11">%s</text>'
                 % (ox + (x + w / 2) * S, oy + (y + h / 2) * S + 4, lab))
    b.append(txt(ox + 160 * S, 22, '320 × 200 · 64,000바이트 = 세그먼트 하나', 'lbl'))
    b.append(txt(ox + 160 * S, oy + 200 * S + 20,
                 '맵은 왼쪽 위 한 구석만 쓴다 — 클리핑 사각형이 이 값이다', 'lbl'))
    return svg(440, 285, '\n'.join(b), '화면 영역 배치')


# ----------------------------------------------------------------- 10. 상태 기계
def fig_fsm():
    nodes = {'IDLE': (78, 56), 'SELECTED': (230, 56), 'TARGETING': (382, 56),
             'DIALOG': (230, 170), 'GAMEOVER': (382, 170)}
    edges = [('IDLE', 'SELECTED', '아군 클릭 ⇄ ESC', 'up'),
             ('SELECTED', 'TARGETING', 'T ⇄ ESC', 'up'),
             ('SELECTED', 'DIALOG', 'E ⇄ ESC/NO', 'right'),
             ('TARGETING', 'GAMEOVER', '마지막 적 격파', 'right'),
             ('DIALOG', 'GAMEOVER', '승패 확정', 'up')]
    b = []
    for (a, c, lab, where) in edges:
        (x1, y1), (x2, y2) = nodes[a], nodes[c]
        b.append('<path class="ax" d="M %d %d L %d %d" opacity=".5"/>' % (x1, y1, x2, y2))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if where == 'up':
            b.append(txt(mx, my - 8, lab, 'lbl', size=9))
        else:
            b.append(txt(mx + 8, my + 3, lab, 'lbl', 'start', 9))
    for (n, (x, y)) in nodes.items():
        b.append(rect(x - 52, y - 15, 104, 30, '#dfe6cd', '#4a6b34', 1.4, ' rx="6"'))
        b.append(txt(x, y + 4, n, None, 'middle', 11))
    b.append(txt(230, 24, '같은 클릭이 상태에 따라 선택·이동·공격이 된다', 'lbl'))
    return svg(460, 210, '\n'.join(b), 'UI 상태 기계')


# -------------------------------------------------------------------- 11. 링
def fig_ring():
    b = []
    R, ox, oy = 26, 200, 132
    order = {}
    q, r = DIRS[4][0] * 2, DIRS[4][1] * 2
    k = 0
    for d in range(6):
        for _ in range(2):
            order[(q, r)] = k
            k += 1
            q += DIRS[d][0]
            r += DIRS[d][1]
    for rr in range(-2, 3):
        for qq in range(-2, 3):
            if abs(qq) + abs(rr) + abs(qq + rr) > 4:
                continue
            cx, cy = axial_xy(qq, rr, R, ox, oy)
            dist = (abs(qq) + abs(rr) + abs(qq + rr)) // 2
            cls = 'hx on' if (qq, rr) in order else ('hx hot' if dist == 0 else 'hx dim')
            b.append(hexat(cx, cy, R, cls))
            if (qq, rr) in order:
                b.append(txt(cx, cy + 4, str(order[(qq, rr)]), None, 'middle', 11))
    b.append(txt(200, 22, 'ring(중심, 2) — SW 로 2칸 간 자리에서 시작해 여섯 방향으로 2칸씩', 'lbl'))
    b.append(txt(200, 252, '거리 판정 없이 걷기만 한다 · 개수는 정확히 6n', 'lbl'))
    return svg(400, 264, '\n'.join(b), '링 순회 순서')


# ------------------------------------------------------------------- 12. 라인
def fig_line():
    import sys
    sys.path.insert(0, os.path.join(BASE, 'py'))
    from hexwar import hexcoord as H
    b = []
    R, ox, oy = 24, 90, 70
    pts = set(H.line(0, 0, 4, 2))
    for rr in range(-1, 4):
        for qq in range(-1, 6):
            cx, cy = axial_xy(qq, rr, R, ox, oy)
            if cx < 20 or cx > 380 or cy < 30 or cy > 210:
                continue
            cls = 'hx on' if (qq, rr) in pts else 'hx'
            if (qq, rr) in ((0, 0), (4, 2)):
                cls = 'hx hot'
            b.append(hexat(cx, cy, R, cls))
    ax, ay = axial_xy(0, 0, R, ox, oy)
    bx, by = axial_xy(4, 2, R, ox, oy)
    b.append('<path class="ax" d="M %.1f %.1f L %.1f %.1f" opacity=".8"/>' % (ax, ay, bx, by))
    b.append(txt(200, 22, 'line((0,0) → (4,2)) — 엔진이 실제로 돌려주는 칸들', 'lbl'))
    b.append(txt(200, 236, '보간은 1/1024 단위 정수로 하고, 넛지가 모서리 동점을 한쪽으로 민다', 'lbl'))
    return svg(400, 248, '\n'.join(b), '헥스 라인')


# ---------------------------------------------------------------- 13. 고도 시야
def fig_los():
    b = []
    x0, y0, w = 26, 170, 50
    heights = [1, 1, 3, 2, 1, 1, 2]
    for i, h in enumerate(heights):
        b.append(rect(x0 + i * w, y0 - h * 22, w, h * 22,
                      '#cfe0c0' if i not in (0, 6) else '#dfe6cd'))
        b.append(txt(x0 + i * w + w / 2, y0 + 16, 'h=%d' % h, 'lbl', size=9))
    ex = x0 + w / 2
    ey = y0 - heights[0] * 22 - 12
    tx = x0 + 6 * w + w / 2
    ty = y0 - heights[6] * 22
    b.append('<path class="ax" d="M %.1f %.1f L %.1f %.1f" stroke-dasharray="4 3"/>'
             % (ex, ey, tx, ty))
    b.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#b04a2a"/>' % (ex, ey))
    b.append(txt(ex, ey - 10, '눈높이 = 고도 + 1', 'lbl'))
    b.append(txt(tx, ty - 10, '목표', 'lbl'))
    b.append(txt(x0 + 2 * w + w / 2, y0 - 3 * 22 - 10, '여기서 막힌다', 'lbl'))
    b.append(txt(200, 24, '중간 칸이 눈–목표 직선 위로 솟으면 시야가 끊긴다', 'lbl'))
    b.append(txt(200, 214, 'H(m)·N > H(a)·(N−i) + H(b)·i — 양변에 N 을 곱해 정수로 판정', 'lbl'))
    return svg(400, 226, '\n'.join(b), '고도에 따른 시야 판정')


# ------------------------------------------------------------- 14. 양동이 큐
def fig_dial():
    b = []
    x0, y0, w, h = 34, 60, 44, 34
    for c in range(8):
        b.append(rect(x0 + c * w, y0, w, h, '#dfe6cd'))
        b.append(txt(x0 + c * w + w / 2, y0 - 8, str(c), 'lbl'))
    for (c, n) in ((0, 1), (1, 2), (2, 3), (3, 2), (4, 4), (6, 1)):
        for k in range(n):
            b.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#4a6b34"/>'
                     % (x0 + c * w + 10 + k * 8, y0 + h / 2))
    b.append(txt(x0 + 4 * w, 26, '남은 비용별 양동이 — 비용이 1..6 이라 힙이 필요 없다', 'lbl'))
    b.append(arrow(x0, y0 + h + 22, x0 + 8 * w, y0 + h + 22))
    b.append(txt(x0 + 4 * w, y0 + h + 40, '0번부터 차례로 비우면 그 순서가 곧 최단 순서다', 'lbl'))
    b.append(txt(x0 + 4 * w, y0 + h + 58, 'O(V + E + maxMP) · 비교 함수도 로그도 없다', 'lbl'))
    return svg(400, 190, '\n'.join(b), 'Dial 양동이 큐')


# ------------------------------------------------------------------ 15. ZOC
def fig_zoc():
    b = []
    R, ox, oy = 27, 200, 130
    zoc = set()
    for d in range(6):
        zoc.add((DIRS[d][0], DIRS[d][1]))
    for rr in range(-2, 3):
        for qq in range(-2, 3):
            if abs(qq) + abs(rr) + abs(qq + rr) > 4:
                continue
            cx, cy = axial_xy(qq, rr, R, ox, oy)
            if (qq, rr) == (0, 0):
                cls = 'hx hot'
            elif (qq, rr) in zoc:
                cls = 'hx on'
            else:
                cls = 'hx'
            b.append(hexat(cx, cy, R, cls))
    b.append(txt(ox, oy + 4, '적', None, 'middle', 12))
    b.append(txt(200, 22, '적 유닛에 인접한 여섯 칸이 통제 지역(ZOC)', 'lbl'))
    b.append(txt(200, 254, '들어갈 수는 있지만, 들어간 순간 남은 이동력이 0이 된다', 'lbl'))
    return svg(400, 266, '\n'.join(b), '통제 지역')


# ------------------------------------------------------------------- 16. RLE
def fig_rle():
    b = []
    x0, y0, px = 40, 56, 15
    row = [0] * 6 + [16] * 9 + [20] * 3 + [16] * 4
    for i, v in enumerate(row):
        col = {0: '#101010', 16: '#8fb08f', 20: '#4a6b34'}[v]
        b.append(rect(x0 + i * px, y0, px, px, col, '#ffffff', 0.5))
    b.append(txt(x0 + len(row) * px / 2, y0 - 10, '원본 22바이트', 'lbl'))
    pairs = [(6, 0), (9, 16), (3, 20), (4, 16)]
    x = x0
    for (c, v) in pairs:
        wpx = c * px
        col = {0: '#101010', 16: '#8fb08f', 20: '#4a6b34'}[v]
        b.append(rect(x, y0 + 52, wpx, px, col, '#ffffff', 0.5))
        b.append(txt(x + wpx / 2, y0 + 52 + px + 14, '%d,%d' % (c, v), 'lbl', size=9))
        x += wpx
    b.append(txt(x0 + len(row) * px / 2, y0 + 44, 'RLE 4쌍 = 8바이트', 'lbl'))
    b.append(txt(200, 150,
                 '픽셀마다 색을 흔들면(점묘) 쌍이 폭발한다 — 넓은 색면으로 그리는 이유', 'lbl'))
    b.append(txt(200, 168, '실측: 점묘 70.6% → 4픽셀 색면 46.6%', 'lbl'))
    return svg(400, 182, '\n'.join(b), 'RLE 인코딩')


# ------------------------------------------------------------ 17. 더티 사각형
def fig_dirty():
    b = [rect(30, 40, 220, 150, '#101010')]
    for (x, y, w, h, lab) in ((60, 60, 44, 44, '커서 이동'), (150, 100, 44, 44, '유닛 이동'),
                              (90, 130, 44, 44, '')):
        b.append(rect(x, y, w, h, '#3f5a2e', '#f4d98a', 1.6))
        if lab:
            b.append(txt(x + w / 2, y - 6, lab, 'lbl', size=9))
    b.append(txt(140, 206, '바뀐 사각형만 다시 그린다', 'lbl'))
    b.append(rect(280, 40, 100, 150, '#101010'))
    b.append(rect(280, 40, 100, 150, '#3f5a2e', '#f4d98a', 1.6))
    b.append(txt(330, 206, '전체 갱신 64,000바이트', 'lbl'))
    b.append(txt(140, 26, '3개 × 44×44 = 5,808바이트', 'lbl'))
    b.append(txt(330, 26, '11배 차이', 'lbl'))
    return svg(400, 220, '\n'.join(b), '더티 사각형과 전체 갱신')


# ------------------------------------------------------------- 18. SoA vs AoS
def fig_soa():
    b = []
    x0, y0, cw, ch = 34, 56, 26, 24
    b.append(txt(x0, 34, '구조체 배열(AoS) — 한 칸의 모든 필드가 붙어 있다', 'lbl', 'start'))
    for i in range(3):
        for j, (lab, col) in enumerate((('지형', '#cfe0c0'), ('안개', '#f4d98a'),
                                        ('점유', '#e8a37a'), ('예약', '#dcdcd0'))):
            x = x0 + (i * 4 + j) * cw
            b.append(rect(x, y0, cw, ch, col))
            b.append(txt(x + cw / 2, y0 + 16, lab[0], None, 'middle', 9))
    b.append(txt(x0, y0 + 44, '경로 탐색은 지형만 읽는데 캐시 라인의 3/4 가 낭비된다', 'lbl', 'start'))

    y1 = y0 + 76
    b.append(txt(x0, y1 - 10, '평행 배열(SoA) — 같은 필드끼리 모은다', 'lbl', 'start'))
    for j, (lab, col) in enumerate((('지형', '#cfe0c0'), ('안개', '#f4d98a'), ('점유', '#e8a37a'))):
        for i in range(6):
            x = x0 + i * cw
            b.append(rect(x, y1 + 6 + j * (ch + 4), cw, ch, col))
        b.append(txt(x0 + 6 * cw + 10, y1 + 6 + j * (ch + 4) + 16, lab, 'lbl', 'start', 9))
    b.append(txt(x0, y1 + 6 + 3 * (ch + 4) + 18,
                 '지형 배열만 훑으면 캐시 라인이 전부 쓸모 있는 데이터다', 'lbl', 'start'))
    return svg(400, 250, '\n'.join(b), 'AoS 와 SoA 배치 비교')


# -------------------------------------------------------------- 19. 위젯 트리
def fig_widget():
    nodes = [('root 320×200', 200, 34, 0), ('mapview', 70, 92, 1), ('log', 160, 92, 1),
             ('panel', 260, 92, 1), ('dialog', 350, 92, 1),
             ('minimap', 210, 150, 2), ('end', 268, 150, 2), ('undo', 316, 150, 2),
             ('yes', 364, 150, 2), ('no', 404, 150, 2)]
    b = []
    for (lab, x, y, depth) in nodes:
        if depth == 1:
            b.append('<path class="ax" d="M 200 48 L %d %d" opacity=".4"/>' % (x, y - 12))
        if depth == 2:
            px = 260 if lab in ('minimap', 'end', 'undo') else 350
            b.append('<path class="ax" d="M %d 106 L %d %d" opacity=".4"/>' % (px, x, y - 12))
    for (lab, x, y, depth) in nodes:
        w = 22 + 7 * len(lab)
        b.append(rect(x - w / 2, y - 12, w, 24, '#dfe6cd', '#4a6b34', 1.2, ' rx="5"'))
        b.append(txt(x, y + 4, lab, None, 'middle', 9))
    b.append(txt(200, 190, '그리기는 위에서 아래로 · 히트 테스트는 아래에서 위로', 'lbl'))
    b.append(txt(200, 206, '이 한 문장이 모달 대화상자가 밑을 가리는 이유 전부다', 'lbl'))
    return svg(440, 220, '\n'.join(b), '위젯 트리')


# -------------------------------------------------------------- 20. 그리기 순서
def fig_paint():
    b = []
    R, ox, oy = 30, 130, 70
    for row in range(3):
        for col in range(3):
            cx = ox + col * SQRT3 * R + (row & 1) * (SQRT3 * R / 2)
            cy = oy + row * 1.5 * R
            b.append(hexat(cx, cy, R, 'hx' if row else 'hx dim'))
            b.append(txt(cx, cy + 4, str(row * 3 + col + 1), 'lbl'))
    b.append(txt(200, 24, '위 행부터 그리면 아래 행이 자연스럽게 8픽셀을 덮는다', 'lbl'))
    b.append(txt(200, 200, '헥스 높이 32 · 행 간격 24 → 세로로 8픽셀이 겹친다', 'lbl'))
    b.append(arrow(340, 60, 340, 130))
    b.append(txt(352, 98, '그리는 순서', 'lbl', 'start'))
    return svg(400, 214, '\n'.join(b), '화가 알고리즘 그리기 순서')


FIGS_ALL = [
    ('fig_sqhex.svg', fig_sqhex), ('fig_offsets.svg', fig_offsets),
    ('fig_axial.svg', fig_axial), ('fig_cube.svg', fig_cube),
    ('fig_hexgeom.svg', fig_hexgeom), ('fig_brick.svg', fig_brick),
    ('fig_mask.svg', fig_mask), ('fig_cell.svg', fig_cell),
    ('fig_layout.svg', fig_layout), ('fig_fsm.svg', fig_fsm),
    ('fig_ring.svg', fig_ring), ('fig_line.svg', fig_line),
    ('fig_los.svg', fig_los), ('fig_dial.svg', fig_dial),
    ('fig_zoc.svg', fig_zoc), ('fig_rle.svg', fig_rle),
    ('fig_dirty.svg', fig_dirty), ('fig_soa.svg', fig_soa),
    ('fig_widget.svg', fig_widget), ('fig_paint.svg', fig_paint),
]


def main():
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    for name, fn in FIGS_ALL:
        write(name, fn())
    print('도해 %d개 생성 → deck/figs/' % len(FIGS_ALL))


if __name__ == '__main__':
    main()
