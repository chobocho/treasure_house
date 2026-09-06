# -*- coding: utf-8 -*-
"""쿼터뷰 투영과 역투영 — SPEC §3.

   이 파일이 덱 전체의 심장이다. 타일 하나가 화면 어디에 놓이는지,
   그리고 마우스가 짚은 픽셀이 어느 타일인지. 두 방향 모두 정수만 쓴다.
"""
from . import fixed as F

TW = 32                 # 마름모 가로 지름
TH = 16                 # 마름모 세로 지름
TZ = 8                  # 높이 한 단계
SCR_W = 320
SCR_H = 200
MAP_W = 48
MAP_H = 48
MAXH = 15

HW = TW // 2            # 16
HH = TH // 2            # 8


def tile_to_screen(tx, ty, h):
    """타일 -> 마름모 꼭대기 꼭짓점의 월드 픽셀.

       기저 e_x = (16, 8), e_y = (-16, 8). 행렬식 256 = 2^8 이라
       역행렬 성분이 전부 2의 거듭제곱 배수가 된다 — 그것이 2:1 을 고른 이유다.
    """
    return (HW * (tx - ty), HH * (tx + ty) - h * TZ)


def world_to_screen(fx, fy, h):
    """16.16 타일 좌표 -> 월드 픽셀. 엔티티가 타일 사이에 있을 때 쓴다."""
    return (F.floordiv((fx - fy) * HW, F.FP_ONE),
            F.floordiv((fx + fy) * HH, F.FP_ONE) - h * TZ)


def screen_to_tile(px, py):
    """대수적 역. 나눗셈 두 번이면 끝난다. (정리 3.2)

       a = px + 2py, b = 2py - px 로 좌표를 갈아타면 마름모가
       변 32짜리 정사각형이 되고, 그러면 내림 나눗셈이 곧 답이다.
    """
    return (F.floordiv(px + 2 * py, 32), F.floordiv(2 * py - px, 32))


def screen_to_tile_slow(px, py):
    """마름모 정의(|u| + 2|v| <= 16)로 직접 찾는다 — 빠른 식을 검산하는 용도.

       경계 픽셀은 여러 마름모에 걸치므로, floor 규칙과 같은 것을 고르려면
       a = px+2py 와 b = 2py-px 가 큰 쪽을 택해야 한다.
    """
    gx, gy = screen_to_tile(px, py)
    best = None
    for tx in range(gx - 2, gx + 3):
        for ty in range(gy - 2, gy + 3):
            cx = HW * (tx - ty)
            cy = HH * (tx + ty) + HH
            u = px - cx
            v = py - cy
            if (u if u >= 0 else -u) + 2 * (v if v >= 0 else -v) <= HW:
                if best is None or (tx + ty, tx) > (best[0] + best[1], best[0]):
                    best = (tx, ty)
    return best


def _build_mask():
    """32x16 모서리 마스크. 값은 2*A + (B+1) 로 0..3 네 가지뿐이다. (SPEC §3.4)

       도스 게임이 이 표를 파일로 들고 다닌 이유는 나눗셈이 느려서였다.
       여기서는 표가 왜 네 값뿐인지를 보이려고 만든다.
    """
    m = [0] * (TW * TH)
    for oy in range(TH):
        for ox in range(TW):
            a = F.floordiv(ox + 2 * oy, 32)
            b = F.floordiv(2 * oy - ox, 32)
            m[oy * TW + ox] = 2 * a + (b + 1)
    return m


PICK_MASK = _build_mask()


def pick_mask(px, py):
    """도스식 역투영 — 나눗셈 두 번(사각형 찾기)과 표 조회 한 번."""
    rc = F.floordiv(px, TW)
    rr = F.floordiv(py, TH)
    ox = px - TW * rc
    oy = py - TH * rr
    m = PICK_MASK[oy * TW + ox]
    return (rc + rr + F.floordiv(m, 2), rr - rc + F.fmod(m, 2) - 1)


MARGIN_X = HW
# 세로 여백: 마름모 반, 최대 높이 15단계, 그리고 가장 큰 스프라이트(나무 32px)
MARGIN_Y = HH + MAXH * TZ + 32


def visible_range(x0, y0, x1, y1):
    """뷰포트에 걸치는 타일 범위. 네 모서리만 역투영하면 된다. (정리 3.3)

       a = px + 2py 는 선형이라 직사각형 위에서 최대·최소를 꼭짓점에서 취한다.
       계수가 둘 다 양수이므로 a 의 최소는 좌상, 최대는 우하에서 난다.
    """
    ax0 = x0 - MARGIN_X
    ax1 = x1 + MARGIN_X
    ay0 = y0 - MARGIN_Y
    ay1 = y1 + MARGIN_Y
    tx0 = F.floordiv(ax0 + 2 * ay0, 32)
    tx1 = F.floordiv(ax1 + 2 * ay1, 32)
    ty0 = F.floordiv(2 * ay0 - ax1, 32)
    ty1 = F.floordiv(2 * ay1 - ax0, 32)
    if tx0 < 0:
        tx0 = 0
    if ty0 < 0:
        ty0 = 0
    if tx1 > MAP_W - 1:
        tx1 = MAP_W - 1
    if ty1 > MAP_H - 1:
        ty1 = MAP_H - 1
    return (tx0, ty0, tx1, ty1)
