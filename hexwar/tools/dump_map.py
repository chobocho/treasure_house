# -*- coding: utf-8 -*-
"""시나리오를 사람이 읽을 수 있게 덤프한다 — 덱에 싣기 위한 출력."""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, 'py'))

from hexwar import hexcoord as H                       # noqa: E402
from hexwar import los, scenario                       # noqa: E402
from hexwar.hexmap import MAP_H, MAP_W, T_CHAR, TERRAIN_MASK   # noqa: E402
from hexwar.units import K_CHAR                        # noqa: E402

OUT = []


def say(s=''):
    OUT.append(s)
    print(s)


def main():
    m, pool, obj = scenario.load()
    say('지형 (%d×%d = %d칸, %d바이트)' % (MAP_W, MAP_H, MAP_W * MAP_H, MAP_W * MAP_H))
    objset = set(m.axial_idx(q, r) for (q, r) in obj)
    occ = {}
    for u in pool.iter_alive():
        occ[m.axial_idx(u.q, u.r)] = (K_CHAR[u.kind], u.side)
    for row in range(MAP_H):
        line = []
        for col in range(MAP_W):
            i = row * MAP_W + col
            if i in occ:
                ch, side = occ[i]
                line.append(ch.lower() if side else ch)
            elif i in objset:
                line.append('*')
            else:
                line.append(T_CHAR[m.cells[i] & TERRAIN_MASK])
        say('%2d %s' % (row, ' '.join(line) if False else ''.join(line)))
    say()
    say('. 평지  f 숲  h 언덕  M 산  C 도시  ~ 강  s 늪  # 바다  * 목표')
    say('대문자 유닛 = 청군, 소문자 = 적군 (I 보병 T 전차 A 포병 R 정찰)')
    say()

    say('셀 바이트 예시')
    say('  col row  글자  바이트  지형 고도 도로')
    for (col, row) in ((0, 0), (7, 2), (14, 5), (2, 9), (21, 12), (0, 17)):
        c = m.cells[row * MAP_W + col]
        say('  %3d %3d   %s    0x%02X   %4d %4d %4d'
            % (col, row, T_CHAR[c & TERRAIN_MASK], c,
               c & 0x0F, (c >> 4) & 7, (c >> 7) & 1))
    say()

    los.update_fog(m, pool, 0)
    vis = sum(1 for f in m.fog if f == 2)
    say('청군 시야 초기값: 보이는 칸 %d / %d' % (vis, MAP_W * MAP_H))
    say()
    say('안개 (0 미탐색 · 1 탐색됨 · 2 보임)')
    for line in m.fog_text().split('\n'):
        say('   ' + line)

    io.open(os.path.join(BASE, 'out', 'map_dump.txt'), 'w',
            encoding='utf-8').write('\n'.join(OUT) + '\n')


if __name__ == '__main__':
    main()
