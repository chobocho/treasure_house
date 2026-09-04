# -*- coding: utf-8 -*-
"""시나리오 로더 — golden/scenario.txt 를 읽어 맵과 유닛을 만든다.

   도스 게임의 시나리오 파일도 대개 이런 모양이었다. 바이너리가 아니라
   텍스트인 것은 이 교재의 편의이고, 대신 '한 글자 = 한 헥스' 라는
   원본의 성질은 그대로 지킨다.
"""

import io
import os

from . import hexcoord as H
from .hexmap import HexMap, CHAR_TO_TERRAIN, MAP_W, MAP_H
from .units import UnitPool

GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'golden')


def parse(text):
    """[terrain] [elev] [road] [units] [objectives] 다섯 블록을 나눈다."""
    blocks = {}
    cur = None
    for raw in text.split('\n'):
        line = raw.rstrip('\r')
        if not line or line.startswith(';'):
            continue
        if line.startswith('[') and line.endswith(']'):
            cur = line[1:-1]
            blocks[cur] = []
            continue
        if cur is None:
            raise ValueError('블록 밖의 줄: %r' % line)
        blocks[cur].append(line)
    return blocks


def load(path=None):
    """(맵, 유닛풀, 목표헥스목록) 을 돌려준다."""
    path = path or os.path.join(GOLDEN, 'scenario.txt')
    blocks = parse(io.open(path, encoding='utf-8').read())

    terr = blocks['terrain']
    elev = blocks['elev']
    road = blocks['road']
    if not (len(terr) == len(elev) == len(road) == MAP_H):
        raise ValueError('맵 높이가 %d 이 아니다' % MAP_H)

    m = HexMap(MAP_W, MAP_H)
    for row in range(MAP_H):
        if not (len(terr[row]) == len(elev[row]) == len(road[row]) == MAP_W):
            raise ValueError('%d행의 너비가 %d 이 아니다' % (row, MAP_W))
        for col in range(MAP_W):
            t = CHAR_TO_TERRAIN[terr[row][col]]
            e = int(elev[row][col])
            rd = 1 if road[row][col] == 'R' else 0
            m.set_cell(col, row, t, e, rd)

    pool = UnitPool()
    for line in blocks['units']:
        side, kind, col, row = (int(x) for x in line.split())
        q, r = H.oddr_to_axial(col, row)
        uid = pool.spawn(side, kind, q, r)
        m.occupant[m.idx(col, row)] = uid

    objectives = []
    for line in blocks['objectives']:
        col, row = (int(x) for x in line.split())
        objectives.append(H.oddr_to_axial(col, row))

    return m, pool, objectives
