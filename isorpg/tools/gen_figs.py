# -*- coding: utf-8 -*-
"""덱에 들어갈 인라인 SVG 도해 생성기.

   마름모 격자를 손으로 좌표 찍어 그리면 반드시 어긋난다. 그래서 배치 규칙을
   코드로 쓴다 — 도해와 엔진이 같은 공식을 쓰므로 그림이 거짓말을 할 수 없다.
   실제로 py/isorpg/proj.py 를 import 해서 좌표를 얻는다.

   확인: sh tools/check_figs.sh <디렉터리>   (rsvg-convert 로 PNG 렌더)
   실행: python3 tools/gen_figs.py
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS = os.path.join(BASE, 'deck', 'figs')
sys.path.insert(0, os.path.join(BASE, 'py'))
from isorpg import proj as PR                                  # noqa: E402
from isorpg import sortdag as SD                               # noqa: E402


# ------------------------------------------------------------------ 기본 도구
def poly(pts, cls='tl', extra=''):
    d = ' '.join('%.2f,%.2f' % p for p in pts)
    return '<polygon class="%s" points="%s"%s/>' % (cls, d, extra)


def dia(cx, cy, hw=16.0, hh=8.0, cls='tl'):
    """마름모 하나. 엔진의 TW/TH 비율(2:1)을 그대로 쓴다."""
    return poly([(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)], cls)


def txt(x, y, s, cls=None, anchor='middle', size=None):
    c = ' class="%s"' % cls if cls else ''
    z = ' font-size="%s"' % size if size else ''
    return ('<text x="%.1f" y="%.1f" text-anchor="%s"%s%s>%s</text>'
            % (x, y, anchor, c, z, s))


def line(x1, y1, x2, y2, cls='gd', extra=''):
    return ('<path class="%s" d="M %.2f %.2f L %.2f %.2f"%s/>'
            % (cls, x1, y1, x2, y2, extra))


def arrow(x1, y1, x2, y2, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ''
    return ('<path class="ax" d="M %.1f %.1f L %.1f %.1f"%s marker-end="url(#ah)"/>'
            % (x1, y1, x2, y2, d))


def rect(x, y, w, h, fill='none', stroke='#8a5a2b', sw=1.2, extra=''):
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
            'stroke="%s" stroke-width="%s"%s/>' % (x, y, w, h, fill, stroke, sw, extra))


DEFS = ('<defs><marker id="ah" markerWidth="9" markerHeight="9" refX="7.5" refY="3"'
        ' orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="#b04a2a"/></marker></defs>')


def svg(name, w, h, body, title):
    doc = ('<svg class="diag" viewBox="0 0 %d %d" role="img" aria-label="%s">\n'
           '<title>%s</title>\n%s\n%s\n</svg>\n'
           % (w, h, title, title, DEFS, '\n'.join(body)))
    io.open(os.path.join(FIGS, name), 'w', encoding='utf-8').write(doc)
    return name


# ------------------------------------------------------------------ 1. 기저와 투영
def fig_basis():
    S = 3.0                                     # 화면 확대 배율
    OX, OY = 250.0, 66.0
    b = []
    for ty in range(4):
        for tx in range(4):
            sx, sy = PR.tile_to_screen(tx, ty, 0)
            cls = 'tl on' if (tx, ty) in ((1, 0), (0, 1)) else 'tl'
            b.append(dia(OX + sx * S, OY + (sy + PR.HH) * S, 16 * S, 8 * S, cls))
            b.append(txt(OX + sx * S, OY + (sy + PR.HH) * S + 4,
                         '%d,%d' % (tx, ty), 'lbl'))
    b.append(arrow(OX, OY, OX + 16 * S, OY + 8 * S))
    b.append(arrow(OX, OY, OX - 16 * S, OY + 8 * S))
    b.append(txt(OX + 16 * S + 44, OY + 8 * S + 16, 'e_x = (16, 8)'))
    b.append(txt(OX - 16 * S - 44, OY + 8 * S + 16, 'e_y = (-16, 8)'))
    b.append(txt(OX, OY - 16, '타일 (0,0) 의 꼭대기 꼭짓점'))
    b.append(txt(250, 268, 'M = [[16, -16], [8, 8]]      det M = 256 = 2^8'))
    b.append(txt(250, 286, '행렬식이 2의 거듭제곱이라 역행렬 성분이 전부 '
                           '2의 거듭제곱 배수가 된다', 'lbl'))
    return svg('fig_basis.svg', 500, 300, b, '2:1 다이메트릭 기저 벡터')


# ------------------------------------------------------------------ 2. 마름모와 L1 공
def fig_diamond():
    S = 9.0
    OX, OY = 250.0, 100.0
    b = []
    b.append(rect(OX - 16 * S, OY - 8 * S, 32 * S, 16 * S, 'none', '#c9bda4', 1))
    b.append(dia(OX, OY, 16 * S, 8 * S, 'tl on'))
    b.append(line(OX - 16 * S, OY, OX + 16 * S, OY))
    b.append(line(OX, OY - 8 * S, OX, OY + 8 * S))
    b.append(txt(OX, OY - 8 * S - 8, 'v = -8'))
    b.append(txt(OX, OY + 8 * S + 16, 'v = +8'))
    b.append(txt(OX - 16 * S - 26, OY + 4, 'u = -16'))
    b.append(txt(OX + 16 * S + 26, OY + 4, 'u = +16'))
    b.append(txt(OX, OY + 5, '|u| + 2|v| ≤ 16'))
    b.append(txt(250, 250, '마름모 = L1 단위공을 u축으로 두 배 늘인 것.'
                           '  넓이 = 32×16/2 = 256픽셀'))
    return svg('fig_diamond.svg', 500, 270, b, '마름모는 L1 단위공이다')


# ------------------------------------------------------------------ 3. 모서리 마스크
def fig_mask():
    S = 13.0
    OX, OY = 60.0, 40.0
    COL = {0: '#e6dcc6', 1: '#f4d98a', 2: '#b9cbdc', 3: '#e8a37a'}
    b = []
    for oy in range(16):
        run_start = 0
        for ox in range(33):
            cur = PR.PICK_MASK[oy * 32 + ox] if ox < 32 else -1
            prev = PR.PICK_MASK[oy * 32 + run_start]
            if ox == 32 or cur != prev:
                b.append(rect(OX + run_start * S, OY + oy * S,
                              (ox - run_start) * S, S, COL[prev], 'none', 0))
                run_start = ox
    b.append(rect(OX, OY, 32 * S, 16 * S, 'none', '#8a5a2b', 1.4))
    # 두 경계선: ox + 2oy = 32, 2oy - ox = 0
    b.append(line(OX + 32 * S, OY, OX, OY + 16 * S, 'ax'))
    b.append(line(OX, OY, OX + 32 * S, OY + 16 * S, 'ax'))
    for k, (lx, ly, name) in enumerate((
            (16, 3, 'A=0 B=-1'), (4, 8, 'A=0 B=0'),
            (28, 8, 'A=1 B=-1'), (16, 13, 'A=1 B=0'))):
        b.append(txt(OX + lx * S, OY + ly * S + 4, name, 'lbl'))
    b.append(txt(OX + 16 * S, OY + 16 * S + 24,
                 '32×16 사각형 하나가 두 직선으로 넷으로 갈린다 — '
                 '이것이 도스식 모서리 마스크다'))
    b.append(txt(OX + 16 * S, OY + 16 * S + 42,
                 'ox + 2·oy = 32  (기울기 -1/2)      2·oy - ox = 0  (기울기 +1/2)',
                 'lbl'))
    return svg('fig_mask.svg', 520, 300, b, '32x16 모서리 마스크의 네 영역')


# ------------------------------------------------------------------ 4. 화가 알고리즘
def fig_paint():
    S = 3.4
    OX, OY = 250.0, 40.0
    b = []
    order = []
    for ty in range(4):
        for tx in range(4):
            order.append((tx + ty, tx, ty))
    order.sort()
    for k, (_d, tx, ty) in enumerate(order):
        sx, sy = PR.tile_to_screen(tx, ty, 0)
        cls = 'tl on' if k < 6 else ('tl' if k < 12 else 'tl dim')
        b.append(dia(OX + sx * S, OY + (sy + PR.HH) * S, 16 * S, 8 * S, cls))
        b.append(txt(OX + sx * S, OY + (sy + PR.HH) * S + 4, str(k + 1), 'lbl'))
    b.append(txt(250, 235, 'd = tx + ty 오름차순, 같으면 tx 오름차순'))
    b.append(txt(250, 253, 'A 가 B 를 가리려면 A.tx ≥ B.tx 이고 A.ty ≥ B.ty — '
                           '그러면 반드시 d 가 더 크다', 'lbl'))
    return svg('fig_paint.svg', 500, 270, b, '바닥 타일의 화가 순서')


# ------------------------------------------------------------------ 5. 상자 3-순환
def _box3d(x0, y0, z0, x1, y1, z1, S, OX, OY, cls):
    """상자 하나를 윗면 + 두 옆면으로. 높이가 보이지 않으면 z 조건이 설명되지 않는다."""
    def pt(x, y, z):
        sx, sy = PR.tile_to_screen(x, y, z)
        return (OX + sx * S, OY + sy * S)
    top = [pt(x0, y0, z1), pt(x1, y0, z1), pt(x1, y1, z1), pt(x0, y1, z1)]
    left = [pt(x0, y0, z1), pt(x0, y1, z1), pt(x0, y1, z0), pt(x0, y0, z0)]
    right = [pt(x0, y1, z1), pt(x1, y1, z1), pt(x1, y1, z0), pt(x0, y1, z0)]
    out = [poly(left, cls, ' fill-opacity="0.55"'),
           poly(right, cls, ' fill-opacity="0.75"'),
           poly(top, cls, ' fill-opacity="1.0"')]
    cx = sum(p[0] for p in top) / 4.0
    cy = sum(p[1] for p in top) / 4.0
    return out, (cx, cy)


def fig_cycle():
    S = 2.6
    OX, OY = 232.0, 58.0
    rows = [l.split() for l in
            io.open(os.path.join(BASE, 'golden', 'sortcase.txt'),
                    encoding='utf-8').read().strip().split('\n')]
    items = None
    i = 1
    while i < len(rows):
        n = int(rows[i][3])
        if rows[i][1] == '6':
            items = [tuple(int(v) for v in rows[i + 1 + k]) for k in range(n)]
            break
        i += 1 + n
    b = []
    for ty in range(1, 8):
        for tx in range(1, 8):
            sx, sy = PR.tile_to_screen(tx, ty, 0)
            b.append(dia(OX + sx * S, OY + (sy + PR.HH) * S, 16 * S, 8 * S, 'tl dim'))
    cls = ('tl on', 'tl hot', 'tl cool')
    cen = [None, None, None]
    # 뒤에 있는 것부터 그린다 — 이 그림 자체가 화가 알고리즘이다
    for k in sorted(range(3), key=lambda i: items[i][1] + items[i][2]):
        _id, x0, y0, z0, x1, y1, z1 = items[k]
        parts, c = _box3d(x0, y0, z0, x1, y1, z1, S, OX, OY, cls[k])
        b.extend(parts)
        cen[k] = c
    for k, (cx, cy) in enumerate(cen):
        b.append(txt(cx, cy + 5, chr(65 + k), None, 'middle', 15))
    for a2, c2, lab in ((0, 1, 'y'), (1, 2, 'z'), (2, 0, 'x')):
        x1, y1 = cen[a2]
        x2, y2 = cen[c2]
        b.append(arrow(x1 + (x2 - x1) * 0.22, y1 + (y2 - y1) * 0.22 - 14,
                       x1 + (x2 - x1) * 0.80, y1 + (y2 - y1) * 0.80 - 14))
        b.append(txt((x1 + x2) / 2, (y1 + y2) / 2 - 20, lab, 'lbl', 'middle', 13))
    b.append(txt(250, 322, 'A→B 는 y 조건, B→C 는 z 조건, C→A 는 x 조건'))
    b.append(txt(250, 340, '정확히 한 방향씩만 성립해 순환이 닫힌다 — '
                           '위상정렬이 멈추는 지점이다', 'lbl'))
    return svg('fig_cycle.svg', 500, 352, b, '상자 세 개가 만드는 3-순환')


# ------------------------------------------------------------------ 6. 브레젠험 오차항
def fig_bres():
    S = 26.0
    OX, OY = 60.0, 40.0
    pts = []
    x0, y0, x1, y1 = 0, 0, 9, 4
    dx = x1 - x0
    dy = -(y1 - y0)
    err = dx + dy
    x, y = x0, y0
    while True:
        pts.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += 1
        if e2 <= dx:
            err += dx
            y += 1
    b = []
    for gy in range(6):
        for gx in range(11):
            b.append(rect(OX + gx * S, OY + gy * S, S, S, 'none', '#d6cdb8', .8))
    for gx, gy in pts:
        b.append(rect(OX + gx * S, OY + gy * S, S, S, '#f4d98a', '#8a5a2b', 1.2))
    b.append(line(OX + 0.5 * S, OY + 0.5 * S, OX + (x1 + .5) * S, OY + (y1 + .5) * S,
                  'ax'))
    b.append(txt(OX + 5.5 * S, OY + 6.6 * S,
                 '(0,0) → (9,4).  기울기 4/9 를 err = dx + dy 하나로 들고 다닌다'))
    b.append(txt(OX + 5.5 * S, OY + 7.3 * S,
                 'e2 = 2·err 가 dy 이상이면 x 를, dx 이하면 y 를 한 칸 — '
                 '나눗셈도 실수도 없다', 'lbl'))
    return svg('fig_bres.svg', 520, 250, b, '브레젠험 직선의 오차항')


# ------------------------------------------------------------------ 7. 다이아몬드-스퀘어
def fig_ds():
    S = 46.0
    b = []
    OLD = '#8a5a2b'
    NEW = '#b04a2a'
    panels = (
        ('① 네 귀퉁이', [(0, 0), (4, 0), (0, 4), (4, 4)], []),
        ('② 다이아몬드', [(0, 0), (4, 0), (0, 4), (4, 4)], [(2, 2)]),
        ('③ 스퀘어', [(0, 0), (4, 0), (0, 4), (4, 4), (2, 2)],
         [(2, 0), (0, 2), (4, 2), (2, 4)]),
        ('④ 반복', [(gx, gy) for gy in range(5) for gx in range(5)
                    if gx % 2 == 0 and gy % 2 == 0],
         [(gx, gy) for gy in range(5) for gx in range(5)
          if gx % 2 == 1 or gy % 2 == 1]),
    )
    for panel, (title, old, new) in enumerate(panels):
        OX = 30.0 + panel * 122.0
        OY = 52.0

        def at(gx, gy):
            return (OX + gx * S / 2, OY + gy * S / 2)

        for gy in range(5):
            for gx in range(5):
                b.append(rect(OX + gx * S / 2, OY + gy * S / 2, S / 2, S / 2,
                              'none', '#e0d6c2', .7))
        # 새로 채우는 점이 어느 이웃의 평균인지 — 대표로 하나만 잇는다
        if panel == 1:
            for gx, gy in ((0, 0), (4, 0), (0, 4), (4, 4)):
                x1, y1 = at(gx, gy)
                x2, y2 = at(2, 2)
                b.append(line(x1, y1, x2, y2, 'ax'))
        if panel == 2:
            for ddx, ddy in ((-2, 0), (2, 0), (0, 2)):
                x1, y1 = at(2 + ddx, 0 + ddy)
                x2, y2 = at(2, 0)
                b.append(line(x1, y1, x2, y2, 'ax'))
        for gx, gy in old:
            x, y = at(gx, gy)
            b.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (x, y, OLD))
        for gx, gy in new:
            x, y = at(gx, gy)
            b.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (x, y, NEW))
        b.append(txt(OX + S, OY - 18, title))
    b.append(txt(250, 178, '주황이 이번 단계에서 새로 채우는 점.'
                           ' ③ 은 대표로 한 점의 이웃만 표시했다', 'lbl'))
    b.append(txt(250, 198, '한 단계마다 흔들림 폭에 58%를 곱한다 — '
                           '그 비가 곧 지형의 거칠기다'))
    return svg('fig_ds.svg', 500, 214, b, '다이아몬드-스퀘어 네 단계')


# ------------------------------------------------------------------ 8. 큐브 구성
def _cube(cx, cy, S, cls='tl', op=1.0):
    """큐브 하나 — 윗면 마름모 + 아래로 8픽셀 이어지는 두 옆면."""
    hw, hh, tz = 16 * S, 8 * S, 8 * S
    top = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
    left = [(cx - hw, cy), (cx, cy + hh), (cx, cy + hh + tz), (cx - hw, cy + tz)]
    right = [(cx, cy + hh), (cx + hw, cy), (cx + hw, cy + tz), (cx, cy + hh + tz)]
    return [poly(left, cls, ' fill-opacity="%.2f"' % (op * 0.55)),
            poly(right, cls, ' fill-opacity="%.2f"' % (op * 0.75)),
            poly(top, cls, ' fill-opacity="%.2f"' % op)]


def fig_cube():
    S = 3.2
    b = []
    # 왼쪽: 큐브 한 장의 구성
    OX, OY = 130.0, 90.0
    b.extend(_cube(OX, OY, S))
    b.append(txt(OX, OY + 3, '윗면 32×16', 'lbl'))
    b.append(txt(OX - 16 * S - 6, OY + 8 * S + 14, '왼쪽 면', 'lbl', 'end'))
    b.append(txt(OX + 16 * S + 6, OY + 8 * S + 14, '오른쪽 면', 'lbl', 'start'))
    b.append(txt(OX, OY - 8 * S - 14, '큐브 스프라이트 32×24'))
    # 오른쪽: 높이 3 기둥
    OX2, OY2 = 370.0, 112.0
    for k in range(1, 4):
        sx, sy = PR.tile_to_screen(0, 0, k)
        b.extend(_cube(OX2, OY2 + (sy + 8) * S, S, 'tl on' if k == 3 else 'tl'))
        b.append(txt(OX2 + 16 * S + 8, OY2 + (sy + 8) * S + 4, 'k=%d' % k,
                     'lbl', 'start'))
    b.append(txt(OX2, OY2 - 76, '높이 3 인 기둥'))
    b.append(txt(250, 222, '큐브를 k = 1..h 순서로, 아래부터 올린다.'))
    b.append(txt(250, 240, '마지막에 올린 윗면이 맨 위에 남고 옆면은 8h 픽셀만큼 '
                           '이어 붙는다 — 스프라이트 한 장으로 어떤 높이든 만든다', 'lbl'))
    return svg('fig_cube.svg', 500, 256, b, '큐브 스프라이트로 기둥 쌓기')


# ------------------------------------------------------------------ 9. 옥타일
def fig_octile():
    S = 30.0
    OX, OY = 70.0, 40.0
    b = []
    for gy in range(6):
        for gx in range(9):
            b.append(rect(OX + gx * S, OY + gy * S, S, S, 'none', '#d6cdb8', .8))
    path = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3)]
    for k, (gx, gy) in enumerate(path):
        b.append(rect(OX + gx * S, OY + gy * S, S, S,
                      '#e8a37a' if k < 4 else '#f4d98a', '#8a5a2b', 1.2))
        b.append(txt(OX + (gx + .5) * S, OY + (gy + .6) * S,
                     '11' if 0 < k < 4 else ('8' if k else '·'), 'lbl'))
    b.append(txt(OX + 4.5 * S, OY + 6.6 * S,
                 'dx=8, dy=3.  대각 3번 + 직진 5번 = 11·3 + 8·5 = 73'))
    b.append(txt(OX + 4.5 * S, OY + 7.3 * S,
                 'h = 8·max(dx,dy) + 3·min(dx,dy) — 나눗셈이 없어 내림이 끼지 않는다',
                 'lbl'))
    return svg('fig_octile.svg', 520, 250, b, '옥타일 휴리스틱')


# ------------------------------------------------------------------ 10. 가시 범위
def fig_viewport():
    S = 0.26
    OX, OY = 250.0, 20.0
    CX, CY = 60, 250                    # 카메라 위치 (월드 픽셀)
    r = PR.visible_range(CX, CY, CX + 320, CY + 200)
    b = []
    STEP = 3
    for ty in range(0, 48, STEP):
        for tx in range(0, 48, STEP):
            sx, sy = PR.tile_to_screen(tx, ty, 0)
            on = r[0] <= tx <= r[2] and r[1] <= ty <= r[3]
            b.append(dia(OX + sx * S, OY + (sy + PR.HH) * S,
                         16 * S * STEP, 8 * S * STEP, 'tl on' if on else 'tl dim'))
    b.append(rect(OX + CX * S, OY + CY * S, 320 * S, 200 * S, 'none', '#b04a2a', 2.2))
    b.append(txt(OX + (CX + 160) * S, OY + (CY + 100) * S + 4, '화면 320×200'))
    b.append(txt(250, 240, '뷰포트 네 모서리를 역투영해 tx, ty 의 최대·최소를 얻는다'))
    b.append(txt(250, 258, 'a = px + 2py 는 선형이라 직사각형 위에서 꼭짓점에서만 '
                           '최대·최소가 난다 (정리 3.3)', 'lbl'))
    b.append(txt(250, 276, '여백 160픽셀은 최대 높이 15단계(120)와 가장 큰 '
                           '스프라이트(32)를 더한 값이다', 'lbl'))
    return svg('fig_viewport.svg', 500, 290, b, '뷰포트에서 가시 타일 범위 구하기')


def main():
    made = [fig_basis(), fig_diamond(), fig_mask(), fig_paint(), fig_cycle(),
            fig_bres(), fig_ds(), fig_cube(), fig_octile(), fig_viewport()]
    for n in made:
        print('deck/figs/%s  %d바이트'
              % (n, os.path.getsize(os.path.join(FIGS, n))))


if __name__ == '__main__':
    main()
