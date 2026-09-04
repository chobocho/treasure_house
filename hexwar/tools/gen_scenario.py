# -*- coding: utf-8 -*-
"""시나리오 텍스트 생성기 — 지형 지도는 손으로 그리고, 고도·도로는 규칙으로 만든다.
   결과는 golden/scenario.txt 로 고정되며 세 언어가 모두 이 파일을 읽는다."""
import io, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 24, 18

TERRAIN = [
    "....ffff......hh........",
    "...ffff.......hh...ff...",
    "..ff...C......hhh..ff...",
    "..ff....~.....hh........",
    ".......~~......h........",
    "......~~.....MMM........",
    ".....~~......MMM..ff....",
    "....~~........h...ff....",
    "...~~.....ss..h.........",
    "..~~......ss............",
    "..~.......ss.....hh.....",
    "..~..ff.........hhh.....",
    "..~..ff..........hh..C..",
    "..~~.............h......",
    "...~~...........f.......",
    "####~~..........ff......",
    "#####~~.................",
    "######~~................",
]

# 고도: 언덕 1, 산 3, 도시·숲 0. 산줄기 가장자리는 2로 낮춰 능선을 만든다.
ELEV_BY_CHAR = {'.': 0, 'f': 0, 'h': 1, 'M': 3, 'C': 0, '~': 0, 's': 0, '#': 0}
# 산 덩어리의 바깥 테두리는 2 — 시야 계산에 능선이 생긴다
SOFT = {(5, 13), (5, 15), (7, 13), (7, 15)}

# 도로: 9행을 가로지르는 간선 + 도시 두 곳으로 갈라지는 지선
ROAD_CELLS = set()
for c in range(0, W):
    ROAD_CELLS.add((9, c))
for r in range(3, 10):          # 북쪽 도시(7,2)로 올라가는 지선
    ROAD_CELLS.add((r, 7))
ROAD_CELLS.add((2, 7))
for r in range(10, 13):         # 남쪽 도시(21,12)로 내려가는 지선
    ROAD_CELLS.add((r, 21))
for c in range(17, 22):
    ROAD_CELLS.add((12, c))

UNITS = [
    # side kind col row      (kind: 0 보병 1 전차 2 포병 3 정찰)
    (0, 0, 2, 9), (0, 0, 3, 10), (0, 1, 1, 9), (0, 1, 2, 11),
    (0, 2, 0, 10), (0, 3, 4, 8),
    (1, 0, 20, 8), (1, 0, 19, 9), (1, 1, 21, 9), (1, 1, 22, 10),
    (1, 2, 23, 9), (1, 3, 18, 7),
]
OBJECTIVES = [(7, 2), (21, 12)]


def main():
    assert len(TERRAIN) == H, len(TERRAIN)
    for i, row in enumerate(TERRAIN):
        assert len(row) == W, (i, len(row))

    elev = []
    for r in range(H):
        line = []
        for c in range(W):
            e = ELEV_BY_CHAR[TERRAIN[r][c]]
            if (r, c) in SOFT:
                e = 2
            line.append(str(e))
        elev.append(''.join(line))

    road = []
    for r in range(H):
        road.append(''.join('R' if (r, c) in ROAD_CELLS and TERRAIN[r][c] != '#' else '.'
                            for c in range(W)))

    out = [';; HexWar 시나리오 1 — 개활지의 교차로',
           ';; 지형: . 평지  f 숲  h 언덕  M 산  C 도시  ~ 강  s 늪  # 바다',
           '[terrain]']
    out += TERRAIN
    out.append('[elev]')
    out += elev
    out.append('[road]')
    out += road
    out.append('[units]')
    out += ['%d %d %d %d' % u for u in UNITS]
    out.append('[objectives]')
    out += ['%d %d' % o for o in OBJECTIVES]

    p = os.path.join(BASE, 'golden', 'scenario.txt')
    io.open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('wrote %s — %d줄' % (p, len(out)))


if __name__ == '__main__':
    main()
