# -*- coding: utf-8 -*-
"""카메라 — SPEC §4. 정수 픽셀 스크롤과 데드존 추적."""
from .proj import HW, MAP_H, MAP_W, MAXH, SCR_H, SCR_W, TZ

DEADZONE_X = 48
DEADZONE_Y = 24

# 맵 전체가 차지하는 월드 픽셀 범위. 마름모 배치라 가로가 세로의 두 배다.
WORLD_X0 = -HW * (MAP_H - 1) - HW
WORLD_X1 = HW * (MAP_W - 1) + HW
WORLD_Y0 = -MAXH * TZ
WORLD_Y1 = 8 * (MAP_W + MAP_H - 2) + 16


def clamp_cam(cx, cy):
    lo_x, hi_x = WORLD_X0, WORLD_X1 - SCR_W
    lo_y, hi_y = WORLD_Y0, WORLD_Y1 - SCR_H
    if cx < lo_x:
        cx = lo_x
    if cx > hi_x:
        cx = hi_x
    if cy < lo_y:
        cy = lo_y
    if cy > hi_y:
        cy = hi_y
    return (cx, cy)


def follow(cx, cy, tgt_x, tgt_y):
    """대상이 데드존을 벗어난 만큼만 카메라를 민다.

       매 프레임 중앙에 붙여 두면 걸을 때마다 화면이 흔들린다.
       도스 RPG 들이 가운데에 네모난 여유를 둔 이유가 그것이다.
    """
    dx = tgt_x - cx - SCR_W // 2
    dy = tgt_y - cy - SCR_H // 2
    if dx > DEADZONE_X:
        cx += dx - DEADZONE_X
    elif dx < -DEADZONE_X:
        cx += dx + DEADZONE_X
    if dy > DEADZONE_Y:
        cy += dy - DEADZONE_Y
    elif dy < -DEADZONE_Y:
        cy += dy + DEADZONE_Y
    return clamp_cam(cx, cy)
