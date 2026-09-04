# -*- coding: utf-8 -*-
"""화면 좌표 → 헥스 — SPEC §4.

   도스 게임의 마우스 처리에서 제일 자주 틀리는 곳이다. 육각형은 사각형과
   달리 나눗셈만으로 칸이 나오지 않는다. 정공법은 역행렬을 곱하고 큐브
   반올림을 하는 것인데, 8086 에는 FPU 가 없어 이 경로가 너무 비쌌다.

   그래서 실제로 쓰인 방법이 '벽돌 + 마스크'다. 화면을 32x24 벽돌로 자르면
   나눗셈 두 번으로 벽돌이 정해지고, 벽돌 안에서 어느 헥스인지는 768바이트
   표를 한 번 읽어 정한다. 곱셈도 분기도 없다.
"""

from .hexmap import MAP_W, MAP_H

HEX_W = 32        # 헥스 바운딩 박스 너비
HEX_H = 32        # 높이 — 정육각형이 아니다(§4.2). 기울기를 1/2 로 맞추려는 의도.
ROW_STEP = 24     # 행 간격 = HEX_H * 3/4
ODD_SHIFT = 16    # 홀수 행은 오른쪽으로 반 칸

def build_mask():
    """SPEC §4.3 의 768바이트 마스크. 도스 게임은 이 표를 데이터 파일이나
       오브젝트 파일에 그대로 넣고 다녔다 — 여기서는 규칙에서 만들되,
       만들어진 표가 golden/pick_mask.txt 와 같은지 테스트가 확인한다.

       위 8줄만 애매하다. 벽돌 안에서 왼쪽 위 삼각형은 북서 이웃, 오른쪽 위
       삼각형은 북동 이웃, 나머지는 전부 자기 칸이다.
    """
    m = bytearray(ROW_STEP * HEX_W)
    for oy in range(ROW_STEP):
        for ox in range(HEX_W):
            if oy < 8 and ox < 16 - 2 * oy:
                v = 1
            elif oy < 8 and ox >= 16 + 2 * oy:
                v = 2
            else:
                v = 0
            m[oy * HEX_W + ox] = v
    return m


PICK_MASK = build_mask()


def hex_origin(col, row):
    """헥스 (col,row) 바운딩 박스의 맵 좌표 왼쪽 위 모서리."""
    return (col * HEX_W + (row & 1) * ODD_SHIFT, row * ROW_STEP)


def floor_div(a, b):
    """음수에서도 내림. 카메라가 맵 밖으로 나가면 좌표가 음수가 된다."""
    return a // b          # 파이썬의 // 는 이미 내림이다


def nw_neighbor(col, row):
    """odd-r 오프셋의 북서 이웃 — 행 홀짝에 따라 열이 달라진다."""
    return (col - 1 + (row & 1), row - 1)


def ne_neighbor(col, row):
    return (col + (row & 1), row - 1)


def pick(mx, my, camx, camy, w=MAP_W, h=MAP_H):
    """화면 (mx,my) 아래의 헥스 (col,row). 맵 밖이면 None. O(1)."""
    yy = my + camy
    by = floor_div(yy, ROW_STEP)
    oy = yy - by * ROW_STEP
    xx = mx + camx - (by & 1) * ODD_SHIFT
    bx = floor_div(xx, HEX_W)
    ox = xx - bx * HEX_W

    v = PICK_MASK[oy * HEX_W + ox]
    if v == 0:
        col, row = bx, by
    elif v == 1:
        col, row = nw_neighbor(bx, by)
    else:
        col, row = ne_neighbor(bx, by)

    if 0 <= col < w and 0 <= row < h:
        return (col, row)
    return None


def hex_center(col, row):
    """헥스 중심의 맵 좌표 — 스프라이트가 아니라 선·화살표를 그릴 때 쓴다."""
    x, y = hex_origin(col, row)
    return (x + HEX_W // 2, y + HEX_H // 2)
