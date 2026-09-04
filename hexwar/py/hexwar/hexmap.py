# -*- coding: utf-8 -*-
"""맵 자료구조 — SPEC §2.

   도스 게임의 맵은 거의 예외 없이 '한 칸 = 한 바이트'였다. 64KB 세그먼트
   하나에 맵이 통째로 들어가야 세그먼트 레지스터를 갈아 끼우지 않고 인덱싱할
   수 있었기 때문이다. 24x18 = 432바이트짜리 이 맵은 그 관례를 그대로 따른다.

   지형·고도·도로를 한 바이트에 욱여넣는 것은 메모리 절약이 아니라 '한 번의
   메모리 읽기로 세 정보를 다 얻기' 위해서다. 8086 의 메모리 접근은 레지스터
   연산의 열 배가 넘게 비쌌다. 시프트와 마스크는 공짜에 가깝다.
"""

from . import hexcoord as H

MAP_W = 24
MAP_H = 18
MAP_N = MAP_W * MAP_H

# ---- 셀 바이트 (SPEC §2.2) --------------------------------------------------
#   비트 7   도로
#   비트 6-4 고도 0..7
#   비트 3-0 지형 0..15
TERRAIN_MASK = 0x0F
ELEV_SHIFT, ELEV_MASK = 4, 0x07
ROAD_BIT = 0x80


def pack_cell(terrain, elev, road):
    return ((road & 1) << 7) | ((elev & ELEV_MASK) << ELEV_SHIFT) | (terrain & TERRAIN_MASK)


def cell_terrain(c):
    return c & TERRAIN_MASK


def cell_elev(c):
    return (c >> ELEV_SHIFT) & ELEV_MASK


def cell_road(c):
    return (c >> 7) & 1


# ---- 지형표 (SPEC §2.3) -----------------------------------------------------
CLEAR, FOREST, HILL, MOUNTAIN, CITY, RIVER, SWAMP, SEA = range(8)

#            key         이름     이동  방어  시야차단  시야높이  글자
TERRAIN = (
    ('CLEAR',    '평지',   2, 0, 0, 0, '.'),
    ('FOREST',   '숲',     4, 2, 1, 1, 'f'),
    ('HILL',     '언덕',   4, 1, 0, 1, 'h'),
    ('MOUNTAIN', '산',     6, 3, 1, 2, 'M'),
    ('CITY',     '도시',   2, 4, 1, 1, 'C'),
    ('RIVER',    '강',     6, 1, 0, 0, '~'),
    ('SWAMP',    '늪',     6, 0, 0, 0, 's'),
    ('SEA',      '바다',  -1, 0, 0, 0, '#'),
)
T_MOVE = tuple(t[2] for t in TERRAIN)
T_DEF = tuple(t[3] for t in TERRAIN)
T_BLOCK = tuple(t[4] for t in TERRAIN)
T_LOSH = tuple(t[5] for t in TERRAIN)
T_CHAR = tuple(t[6] for t in TERRAIN)
CHAR_TO_TERRAIN = dict((t[6], i) for i, t in enumerate(TERRAIN))

# 안개 상태 (SPEC §9.3)
FOG_HIDDEN, FOG_EXPLORED, FOG_VISIBLE = 0, 1, 2


class HexMap(object):
    """세 개의 평행 배열(SoA). 구조체 배열(AoS)과의 차이는 덱 5부에서 잰다.

       셀 바이트는 렌더링·경로 계산이 매 프레임 훑고, 안개는 턴마다 한 번,
       점유는 이동할 때만 바뀐다. 접근 빈도가 다른 것을 한 구조체에 묶으면
       캐시 라인이 쓸데없는 필드로 채워진다 — 그래서 따로 둔다.
    """

    __slots__ = ('w', 'h', 'cells', 'fog', 'occupant')

    def __init__(self, w=MAP_W, h=MAP_H):
        self.w = w
        self.h = h
        n = w * h
        self.cells = bytearray(n)
        self.fog = bytearray(n)              # 청군 시점 하나만 둔다
        self.occupant = [-1] * n

    # -- 인덱싱 -------------------------------------------------------------
    def idx(self, col, row):
        return row * self.w + col

    def in_bounds(self, col, row):
        return 0 <= col < self.w and 0 <= row < self.h

    def axial_in_bounds(self, q, r):
        col, row = H.axial_to_oddr(q, r)
        return self.in_bounds(col, row)

    def axial_idx(self, q, r):
        """축좌표 → 저장 인덱스. 맵 밖이면 -1."""
        col, row = H.axial_to_oddr(q, r)
        if 0 <= col < self.w and 0 <= row < self.h:
            return row * self.w + col
        return -1

    def idx_axial(self, i):
        row, col = divmod(i, self.w)
        return H.oddr_to_axial(col, row)

    # -- 셀 접근 ------------------------------------------------------------
    def terrain_at(self, i):
        return self.cells[i] & TERRAIN_MASK

    def elev_at(self, i):
        return (self.cells[i] >> ELEV_SHIFT) & ELEV_MASK

    def road_at(self, i):
        return (self.cells[i] >> 7) & 1

    def set_cell(self, col, row, terrain, elev=0, road=0):
        self.cells[row * self.w + col] = pack_cell(terrain, elev, road)

    def passable(self, i):
        return T_MOVE[self.cells[i] & TERRAIN_MASK] >= 0

    # -- 이웃 ---------------------------------------------------------------
    def neighbors_idx(self, i):
        """저장 인덱스 기준 이웃 목록(맵 밖 제외). 경로 탐색의 안쪽 루프다.

           매번 축좌표로 바꿨다 돌아오는 대신, 행 홀짝별 델타 표를 미리
           만들어 두면 덧셈 한 번으로 끝난다 — 아래 NEIGHBOR_DELTA 참고.
        """
        row, col = divmod(i, self.w)
        out = []
        for dcol, drow in NEIGHBOR_DELTA[row & 1]:
            c, r = col + dcol, row + drow
            if 0 <= c < self.w and 0 <= r < self.h:
                out.append(r * self.w + c)
        return out

    def neighbors_with_dir(self, i):
        """(방향 인덱스, 이웃 인덱스) 쌍. 경로에 '어디서 왔는지'를 남기려면
           이웃과 방향을 같이 알아야 한다 — 나중에 역추적할 때 뺄셈이 없다."""
        row, col = divmod(i, self.w)
        out = []
        deltas = NEIGHBOR_DELTA[row & 1]
        for d in range(6):
            dcol, drow = deltas[d]
            c, r = col + dcol, row + drow
            if 0 <= c < self.w and 0 <= r < self.h:
                out.append((d, r * self.w + c))
        return out

    # -- 텍스트 입출력 ------------------------------------------------------
    def to_text(self):
        """지형 글자 + 고도 숫자 두 줄씩. 세이브가 아니라 눈으로 볼 용도."""
        lines = []
        for row in range(self.h):
            base = row * self.w
            lines.append(''.join(T_CHAR[self.cells[base + c] & TERRAIN_MASK]
                                 for c in range(self.w)))
            lines.append(''.join(str((self.cells[base + c] >> ELEV_SHIFT) & ELEV_MASK)
                                 for c in range(self.w)))
        return '\n'.join(lines)

    def fog_text(self):
        return '\n'.join(''.join(str(self.fog[row * self.w + c]) for c in range(self.w))
                         for row in range(self.h))


# odd-r 이웃 델타 — [행이 짝수일 때][방향], 방향 순서는 SPEC §1.5 와 같다.
# 이 표가 있으면 이웃 찾기가 '표 읽기 + 덧셈' 이 된다.
NEIGHBOR_DELTA = (
    ((1, 0), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)),    # 짝수 행
    ((1, 0), (1, -1), (0, -1), (-1, 0), (0, 1), (1, 1)),      # 홀수 행
)
