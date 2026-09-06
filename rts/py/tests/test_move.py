# -*- coding: utf-8 -*-
"""이동·예약·대형 (SPEC §13).

   핵심은 불변식 R 이다 — 어떤 타일도 두 엔티티에게 동시에 예약되지 않는다.
   무작위 시나리오를 오래 돌려 매 틱 확인한다.
"""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import fixed as F
from rts import move as M
from rts import rng as R
from rts import spatial as S
from rts import tmap as T

H.title('move')


def grid(rows):
    m = T.TMap(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            m.terrain[y * m.w + x] = T.ROCK if ch == '#' else T.DIRT
            m._repass(y * m.w + x)
    m._bump()
    return m


def world_of(m):
    return S.World(m.w, m.h)


# ── SPEC §13.1 걸음 진행량 ──────────────────────────────────────────────────
sp = C.SPEED[C.INF]
st = M.step_amount(sp, 0)                  # 북 = 직선
di = M.step_amount(sp, 1)                  # 북동 = 대각
H.check('직선 진행량 = fpdiv(speed, fp(TILE))', st, F.fp_div(sp, F.fp(C.TILE)))
H.check('대각 진행량 = 직선 × FP_DIAG', di, F.fp_mul(st, F.FP_DIAG))
H.check('대각/직선 = 1/√2 (만분율)', di * 10000 // st, 7070)
H.note('보정을 빼면 대각이 √2 = 1.414배 빨라진다 — 41% 빠른 지그재그 버그')
H.check('네 직선 방향의 진행량이 같다',
        [M.step_amount(sp, d) for d in (0, 2, 4, 6)], [st] * 4)
H.check('네 대각 방향의 진행량이 같다',
        [M.step_amount(sp, d) for d in (1, 3, 5, 7)], [di] * 4)
H.check('속도 0 이면 진행량 0', M.step_amount(0, 0), 0)

# ── 정리 13.1 — 화면상 픽셀 속도가 방향과 무관한가 ──────────────────────────
def walk(rows, sx, sy, gx, gy, kind=C.INF):
    """유닛 한 기를 목표까지 걷게 하고 (틱수, 이동 픽셀거리*1000) 를 돌려준다."""
    m = grid(rows)
    w = world_of(m)
    mv = M.Movement(w, m)
    h = w.spawn(0, kind, sx, sy)
    mv.claim(S.index(h))
    mv.order(S.index(h), gx, gy)
    i = S.index(h)
    t = 0
    while (w.tx[i], w.ty[i]) != (gx, gy) and t < 2000:
        mv.step()
        t += 1
    return t, i, w, mv


t_str, _i, _w, _mv = walk(['..........'] * 3, 0, 1, 8, 1)
t_dia, _i, _w, _mv = walk(['..........'] * 10, 0, 0, 8, 8)
# 픽셀 거리: 직선 8타일 = 128px, 대각 8타일 = 128*√2 = 181.02px
r_ticks = t_dia * 1000 // t_str
r_dist = 1414
H.check_true('대각 8칸의 틱수/직선 8칸의 틱수 ≈ √2 (%d/1000)' % r_ticks,
             abs(r_ticks - r_dist) <= 60)
H.note('틱은 정수라 걸음마다 최대 1틱이 남는다 — 그 오차가 위의 여유폭이다')

# ── SPEC §13.1 화면 위치는 파생값 ───────────────────────────────────────────
m = grid(['....', '....', '....', '....'])
w = world_of(m)
mv = M.Movement(w, m)
h = w.spawn(0, C.INF, 1, 1)
i = S.index(h)
mv.claim(i)
H.check('서 있으면 타일 좌표 그대로', M.pos_of(w, m, i),
        (F.fp(1 * C.TILE), F.fp(1 * C.TILE)))
w.to_t[i] = 1 * m.w + 2
w.prog[i] = F.FP_HALF
H.check('동쪽으로 절반 왔으면 x 는 한 타일의 절반',
        M.pos_of(w, m, i), (F.fp(16) + F.fp(8), F.fp(16)))
w.prog[i] = F.FP_ONE
H.check('진행률 1 이면 도착 타일 위', M.pos_of(w, m, i), (F.fp(32), F.fp(16)))
w.to_t[i] = w.from_t[i]
w.prog[i] = 0

# ── SPEC §13.2 예약 불변식 ──────────────────────────────────────────────────
H.check('생성 시 자기 칸을 예약한다', mv.resv[1 * m.w + 1], h)
H.check('예약이 남의 것이면 실패', mv.reserve(1 * m.w + 1, h + 256), False)
H.check('제 예약을 다시 잡는 것은 성공', mv.reserve(1 * m.w + 1, h), True)
H.check('빈 칸 예약은 성공', mv.reserve(0, h), True)
mv.release(0, h)
H.check('반납하면 0', mv.resv[0], 0)
mv.release(0, h)
H.check('두 번 반납해도 조용하다', mv.resv[0], 0)

bh = w.spawn(1, C.HQ, 2, 2)
mv.claim(S.index(bh))
H.check('건물은 발자국 9칸을 전부 예약한다',
        [mv.resv[(2 + dy) * m.w + (2 + dx)] for dy in range(2) for dx in range(2)],
        [bh] * 4)
H.note('3x3 이지만 맵이 4x4 라 오른쪽·아래 한 줄은 맵 밖이다')

# ── 걸음 중에는 두 칸을 쥔다 ────────────────────────────────────────────────
m = grid(['.....', '.....', '.....'])
w = world_of(m)
mv = M.Movement(w, m)
h = w.spawn(0, C.INF, 0, 1)
i = S.index(h)
mv.claim(i)
mv.order(i, 4, 1)
mv.step()
H.check('걸음을 시작하면 두 칸', len([1 for v in mv.resv if v == h]), 2)
H.check('진행 중 tx 는 아직 출발 타일', (w.tx[i], w.ty[i]), (0, 1))
while w.prog[i] != 0:
    mv.step()
H.check('걸음이 끝나면 다시 한 칸', len([1 for v in mv.resv if v == h]), 1)
H.check('타일이 넘어갔다', (w.tx[i], w.ty[i]), (1, 1))
H.check('넘은 사실이 crossed 에 남는다 — sim 7단계의 시야 갱신이 이것만 본다',
        mv.crossed, [(i, 1 * m.w + 0, 1 * m.w + 1)])
mv.step()
H.check('crossed 는 매 틱 비운다', mv.crossed, [])

# ── 무작위 시나리오에서 불변식 R 을 매 틱 확인 ──────────────────────────────
ROWS = [
    '................',
    '..####....####..',
    '..#..#....#..#..',
    '..####....####..',
    '................',
    '....########....',
    '................',
    '..####....####..',
    '..#..#....#..#..',
    '..####....####..',
    '................',
    '................',
]
m = grid(ROWS)
w = world_of(m)
mv = M.Movement(w, m)
rand = R.LCG(7)
free = [j for j in range(m.w * m.h)
        if m.passable_terrain(j % m.w, j // m.w, 0)]
units = []
for k in range(24):
    while True:
        j = free[rand.roll(len(free))]
        if mv.resv[j] == 0:
            break
    hh = w.spawn(rand.roll(2), C.INF if k % 2 else C.TANK, j % m.w, j // m.w)
    mv.claim(S.index(hh))
    units.append(S.index(hh))
start_pos = dict((i, (w.tx[i], w.ty[i])) for i in units)
viol = 0
overlap = 0
selfown = 0
moved = 0
for tick in range(600):
    if tick % 50 == 0:
        for i in units:
            j = free[rand.roll(len(free))]
            mv.order(i, j % m.w, j // m.w)
    mv.step()
    seen = {}
    for i in units:
        for tile in (w.from_t[i], w.to_t[i]):
            hh = w.handle(i)
            if mv.resv[tile] != hh:
                selfown += 1
            if tile in seen and seen[tile] != i:
                viol += 1
            seen[tile] = i
    occ = [w.ty[i] * m.w + w.tx[i] for i in units]
    if len(set(occ)) != len(occ):
        overlap += 1
H.check('불변식 R — 600틱 동안 한 칸을 둘이 예약한 적', viol, 0)
H.check('제가 선 칸은 늘 제 예약이다', selfown, 0)
H.check('두 유닛이 같은 타일에 선 적', overlap, 0)
H.check_true('24기 중 20기 이상이 실제로 자리를 옮겼다',
             sum(1 for i in units
                 if (w.tx[i], w.ty[i]) != start_pos[i]) >= 20)
H.check('예약 수 == 서 있는 칸 + 걷는 중인 칸',
        len([1 for v in mv.resv if v != 0]),
        len(units) + len([1 for i in units if w.prog[i] > 0]))

# ── SPEC §13.3 막힘과 교착 ──────────────────────────────────────────────────
m = grid(['#####', '.....', '#####'])       # 폭 1 통로
w = world_of(m)
mv = M.Movement(w, m)
ha = w.spawn(0, C.INF, 0, 1)
hb = w.spawn(1, C.INF, 4, 1)                # 다른 플레이어 — 밀어내지 않는다
ia, ib = S.index(ha), S.index(hb)
mv.claim(ia)
mv.claim(ib)
mv.order(ia, 4, 1)
mv.order(ib, 0, 1)
rep = give = 0
for t in range(400):
    mv.step()
    if mv.blocked[ia] == M.REPATH_TICKS:
        rep += 1
    if mv.goal[ia] < 0 and give == 0:
        give = t
H.check_true('좁은 통로에서 마주 오면 %d틱에 포기한다 (교착 해소)' % give, give > 0)
H.check_true('포기 전에 재탐색을 시도한다', rep > 0)
H.check('포기하면 경로도 비운다', mv.path[ia], [])
H.note('이것은 해결이 아니라 포기다 — 협상 기반 재배치는 이 엔진 밖이다')

# ── 밀어내기: 정지한 아군은 비켜 준다 ───────────────────────────────────────
m = grid(['.....', '.....', '.....'])
w = world_of(m)
mv = M.Movement(w, m)
ha = w.spawn(0, C.INF, 0, 1)
hb = w.spawn(0, C.INF, 1, 1)                # 같은 플레이어, 정지 상태
ia, ib = S.index(ha), S.index(hb)
mv.claim(ia)
mv.claim(ib)
mv.order(ia, 4, 1)
H.check('진행 방향(E)의 반대 W 부터 시계로 훑는다 — W 는 밀 유닛이 쥐었으니 NW(7)',
        M.push_dir(mv, ib, 2), 7)
for t in range(60):
    mv.step()
    if (w.tx[ib], w.ty[ib]) != (1, 1):
        break
H.check_true('정지한 아군은 밀려난다', (w.tx[ib], w.ty[ib]) != (1, 1))
H.check('밀려간 칸은 NW', (w.tx[ib], w.ty[ib]), (0, 0))
H.note('훑는 순서 = 반대 방향에서 시계 방향 — 세 언어가 같은 칸을 골라야 한다')

# ── SPEC §13.4 도착 반경 ────────────────────────────────────────────────────
m = grid(['.....', '.....', '.....'])
w = world_of(m)
mv = M.Movement(w, m)
hb = w.spawn(0, C.INF, 4, 1)
ha = w.spawn(0, C.INF, 0, 1)
ia, ib = S.index(ha), S.index(hb)
mv.claim(ib)
mv.claim(ia)
mv.order(ia, 4, 1)                          # 목표 칸은 이미 점유되어 있다
for t in range(300):
    mv.step()
    if mv.goal[ia] < 0:
        break
H.check_true('목표가 점유되어 있어도 %d타일 안이면 도착으로 친다' % M.ARRIVE_R,
             F.dinf(w.tx[ia] - 4, w.ty[ia] - 1) <= M.ARRIVE_R)
H.check('도착하면 경로를 비운다', mv.path[ia], [])
H.check_true('영원히 두드리지 않는다', t < 299)

# ── SPEC §13.5 rot8 ─────────────────────────────────────────────────────────
H.check('rot8(0) 은 항등', M.rot8(0, 3, 1), (3, 1))
H.check('rot8(2) = (-oy, ox)', M.rot8(2, 3, 1), (-1, 3))
H.check('rot8(4) = (-ox, -oy)', M.rot8(4, 3, 1), (-3, -1))
H.check('rot8(6) = (oy, -ox)', M.rot8(6, 3, 1), (1, -3))
H.check('rot8(1) = 이웃 둘의 평균 (내림)', M.rot8(1, 3, 1),
        ((3 + -1) // 2, (1 + 3) // 2))
H.check('rot8(7) = 0 과 6 의 평균', M.rot8(7, 3, 1),
        ((3 + 1) // 2, (1 + -3) // 2))
H.check('원점은 어떤 회전에도 원점',
        [M.rot8(d, 0, 0) for d in range(8)], [(0, 0)] * 8)

# ── SPEC §13.5 대형 ─────────────────────────────────────────────────────────
m = grid(['.' * 16] * 16)
box = M.formation(9, M.BOX, 0, 8, 8, m, 0)
H.check('n=9 BOX 는 3×3, 슬롯 9개', len(box), 9)
H.check('BOX 첫 줄은 목표의 x-1..x+1', box[:3], [(7, 8), (8, 8), (9, 8)])
H.check('BOX 둘째 줄은 한 칸 아래', box[3:6], [(7, 9), (8, 9), (9, 9)])
H.check('n=1 이면 목표 한 칸', M.formation(1, M.BOX, 0, 8, 8, m, 0), [(8, 8)])
H.check('n=0 이면 빈 목록', M.formation(0, M.BOX, 0, 8, 8, m, 0), [])
H.check('n=5 BOX 의 한 변은 3', len(set(x for x, _y in
                                        M.formation(5, M.BOX, 0, 8, 8, m, 0))), 3)
line = M.formation(4, M.LINE, 0, 8, 8, m, 0)
H.check('LINE 은 한 줄', sorted(set(y for _x, y in line)), [8])
H.check('LINE 은 가운데 정렬', line, [(7, 8), (8, 8), (9, 8), (10, 8)])
col = M.formation(3, M.COLUMN, 0, 8, 8, m, 0)
H.check('COLUMN 은 진행 방향으로 한 줄', col, [(8, 8), (8, 9), (8, 10)])
H.check('COLUMN 을 동쪽(2)으로 돌리면 x 로 늘어선다',
        M.formation(3, M.COLUMN, 2, 8, 8, m, 0), [(8, 8), (7, 8), (6, 8)])
edge = M.formation(9, M.BOX, 0, 0, 0, m, 0)
H.check_true('맵 밖 슬롯은 목표 타일로 접는다', edge.count((0, 0)) > 1)
blocked = grid(['.' * 5] * 5)
blocked.set_terrain(4, 2, T.ROCK)
H.check('막힌 슬롯은 목표 타일로 접는다',
        M.formation(3, M.LINE, 0, 3, 2, blocked, 0), [(2, 2), (3, 2), (3, 2)])

# ── 경계 조건 ───────────────────────────────────────────────────────────────
m = grid(['..#..', '..#..', '..#..'])
w = world_of(m)
mv = M.Movement(w, m)
h = w.spawn(0, C.INF, 0, 1)
i = S.index(h)
mv.claim(i)
H.check('닿을 수 없는 목표는 §8.6 의 대체 목표로 바뀐다',
        mv.order(i, 4, 1), True)
H.check_true('대체 목표는 벽 앞이다', mv.goal[i] % m.w <= 1)
H.check('이미 서 있는 칸으로의 명령은 즉시 도착', mv.order(i, 0, 1), True)
H.check('그 경우 경로는 비어 있다', mv.path[i], [])
H.check('맵 밖 명령은 거부', mv.order(i, -1, 1), False)
mv.order(i, 1, 1)
mv.stop(i)
H.check('STOP 은 아직 시작하지 않은 걸음의 예약만 반납한다',
        len([1 for v in mv.resv if v == h]), 1)
H.check('STOP 은 경로와 목표를 비운다', [mv.path[i], mv.goal[i]], [[], -1])
mv.order(i, 1, 1)
mv.step()
mv.stop(i)
H.check_true('걸음 도중의 STOP 은 두 칸을 쥔 채로 걸음을 마친다',
             len([1 for v in mv.resv if v == h]) == 2)
while w.prog[i] != 0:
    mv.step()
H.check('마친 뒤에는 한 칸', len([1 for v in mv.resv if v == h]), 1)
H.check('그리고 멈춰 있다', mv.path[i], [])

H.done()
