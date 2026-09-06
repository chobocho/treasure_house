# -*- coding: utf-8 -*-
"""AI — 영향 지도·안개 존중·건물 배치·빌드 오더·정찰 (SPEC §17)."""
from __future__ import print_function

import harness as H
from rts import ai as A
from rts import const as C
from rts import econ as E
from rts import fixed as F
from rts import flow as FL
from rts import fog as FG
from rts import move as M
from rts import select as SEL
from rts import spatial as S
from rts import tmap as T

H.title('ai')


def grid(rows):
    m = T.TMap(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            m.terrain[y * m.w + x] = T.TERRAIN_CH.index(ch)
            m._repass(y * m.w + x)
    m._bump()
    return m


def spawn(w, p, kind, x, y):
    i = S.index(w.spawn(p, kind, x, y))
    w.hp[i] = C.HP[kind]
    return i


# ── SPEC §17.2 전력 ─────────────────────────────────────────────────────────
m = grid(['.' * 16] * 16)
w = S.World(16, 16)
inf = spawn(w, 0, C.INF, 8, 8)
H.check('전력 = 기본 + 관통 + hp/4',
        A.strength(w, inf), C.BASIC[C.INF] + C.PIERCE[C.INF] + C.HP[C.INF] // 4)
w.hp[inf] = 4
H.check('hp 가 줄면 전력도 준다', A.strength(w, inf),
        C.BASIC[C.INF] + C.PIERCE[C.INF] + 1)
w.hp[inf] = C.HP[C.INF]
H.check('채집기의 전력은 hp 뿐', A.strength(w, spawn(w, 0, C.HARV, 1, 1)),
        C.HP[C.HARV] // 4)

# ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────
w2 = S.World(16, 16)
fg = FG.Fog(16, 16)
a = spawn(w2, 0, C.INF, 8, 8)
fg.add_sight(0, 8, 8, C.SIGHT[C.INF])
inf0 = A.influence(w2, fg, 0, m)
c = 8 * 16 + 8
H.check('내 유닛 자리가 가장 크다', inf0[c], max(inf0))
H.check_true('정수 내림 때문에 총합이 준다 — 그 감쇠가 곧 거리 감쇠다',
             sum(inf0) < A.strength(w2, a))
H.check('먼 구석은 0', inf0[0], 0)
H.check('보병 한 기의 영향은 3회 확산 만에 이웃에서 사라진다', inf0[c - 1], 0)
H.note('영향 지도가 보는 것은 한 기가 아니라 밀집이다 — 이것도 감쇠의 결과다')

wt = S.World(16, 16)
ft = FG.Fog(16, 16)
tank = spawn(wt, 0, C.TANK, 8, 8)
ft.add_sight(0, 8, 8, C.SIGHT[C.TANK])
inft = A.influence(wt, ft, 0, m)
H.check_true('전차 한 기(전력 %d)는 이웃까지 번진다' % A.strength(wt, tank),
             inft[c - 1] > 0)
H.check_true('멀수록 작다', inft[c - 1] > inft[c - 3])

b = spawn(w2, 1, C.TANK, 9, 8)
fg2 = FG.Fog(16, 16)
fg2.add_sight(0, 8, 8, C.SIGHT[C.INF])
inf1 = A.influence(w2, fg2, 0, m)
H.check_true('보이는 적은 음수로 들어간다', inf1[8 * 16 + 9] < inf0[8 * 16 + 9])
fg3 = FG.Fog(16, 16)                       # 아무것도 안 보이는 안개
inf2 = A.influence(w2, fg3, 0, m)
H.check('안개 속의 적은 seed 에 들어가지 않는다 (§17.3) — 적이 없을 때와 같다',
        inf2, inf0)
H.check_true('보일 때와는 다르다', inf2[8 * 16 + 9] > inf1[8 * 16 + 9])
thr = A.threat(w2, fg2, 0, m)
H.check_true('위협도는 적만으로 계산한다', thr[8 * 16 + 9] > 0)
H.check('내 유닛은 위협이 아니다', min(thr), 0)

# ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────
gh = A.Memory(16, 16)
gh.update(w2, fg2, 0)
H.check('보이는 적은 유령으로 남는다', gh.ttl[8 * 16 + 9], A.GHOST_TICKS)
H.check_true('적 기지가 알려지지 않았다', not gh.enemy_base_known(w2, fg2, 0))
for _t in range(A.GHOST_TICKS - 1):
    gh.update(w2, fg3, 0)
H.check('안 보이면 매 틱 준다', gh.ttl[8 * 16 + 9], 1)
gh.update(w2, fg3, 0)
H.check('30틱이면 잊는다', gh.ttl[8 * 16 + 9], 0)
H.check('그 자리가 유령 목록에서도 빠진다', gh.ghosts(), [])
hqe = spawn(w2, 1, C.HQ, 2, 2)
fg4 = FG.Fog(16, 16)
fg4.add_sight(0, 2, 2, 4)
gh.update(w2, fg4, 0)
H.check_true('적 건물을 보면 기지가 알려진다', gh.enemy_base_known(w2, fg4, 0))
H.check('알려진 기지 위치', gh.enemy_base(w2, fg4, 0), (2, 2))
H.note('이 제약이 없으면 AI 가 전지적이 되고, 그건 게임이 아니다')

# ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────
m5 = grid(['.' * 20] * 10 + ['.' * 16 + '****'] + ['.' * 20] * 9)
w5 = S.World(20, 20)
mv5 = M.Movement(w5, m5)
ec5 = E.Econ(m5)
hq = spawn(w5, 0, C.HQ, 5, 5)
mv5.claim(hq)
fg5 = FG.Fog(20, 20)
fg5.add_sight(0, 5, 5, C.SIGHT[C.HQ])
fire = FL.brushfire(m5, 0)
thr5 = A.threat(w5, fg5, 0, m5)
spot = A.best_placement(w5, m5, mv5, ec5, fire, thr5, 0, C.POW, (5, 5))
H.check_true('발전소 자리를 찾았다', spot is not None)
H.check('찾은 자리는 실제로 지을 수 있다',
        ec5.placeable(w5, m5, mv5, C.POW, spot[0], spot[1], 0), True)


def brute(kind):
    """같은 점수를 아주 느리게 계산하는 참조 구현 (SPEC §17.4)."""
    best, bs, bi = None, None, None
    ore = ec5.nearest_ore(m5, 5, 5)
    for y in range(20):
        for x in range(20):
            if F.dinf(x - 5, y - 5) > A.PLACE_R:
                continue
            if not ec5.placeable(w5, m5, mv5, kind, x, y, 0):
                continue
            i = y * 20 + x
            sc = 100 - 3 * F.d83(x - 5, y - 5) + 2 * fire[i] - thr5[i]
            if kind == C.REF and ore >= 0:
                sc += 40 - 8 * F.d83(ore % 20 - x, ore // 20 - y)
            if bs is None or sc > bs or (sc == bs and i < bi):
                best, bs, bi = (x, y), sc, i
    return best


H.check('발전소 자리는 참조 구현과 같다', spot, brute(C.POW))
ref_spot = A.best_placement(w5, m5, mv5, ec5, fire, thr5, 0, C.REF, (5, 5))
H.check('정제소 자리도 같다', ref_spot, brute(C.REF))
H.check_true('정제소는 광맥 쪽으로 끌린다', ref_spot[0] > spot[0])
H.check('기지 반경 밖에서는 못 찾는다',
        A.best_placement(w5, m5, mv5, ec5, fire, thr5, 3, C.POW, (60, 60)),
        None)
H.note('점수의 fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다')

# ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
m6 = grid(['.' * 24] * 12 + ['.' * 20 + '****'] + ['.' * 24] * 11)
w6 = S.World(24, 24)
mv6 = M.Movement(w6, m6)
ec6 = E.Econ(m6)
fg6 = FG.Fog(24, 24)
gh6 = A.Memory(24, 24)
hq6 = spawn(w6, 0, C.HQ, 4, 4)
mv6.claim(hq6)
ec6.recount_supply(w6)
ec6.credits[0] = 1000
act = A.build_order(w6, ec6, gh6, 0)
H.check('채집기가 4기 미만이면 채집기', act, ('TRAIN', C.HARV, hq6))
for _k in range(4):
    spawn(w6, 0, C.HARV, 8, 8)
ec6.recount_supply(w6)
H.check('채집기가 차면 정제소', A.build_order(w6, ec6, gh6, 0)[:2],
        ('BUILD', C.REF))
ec6.credits[0] = 100
H.check('돈이 없으면 다음 줄로 내려간다', A.build_order(w6, ec6, gh6, 0),
        ('DEFEND',))
H.note('군대가 없고 병영도 없고 돈도 없으면 남는 것은 방어뿐이다')
ec6.credits[0] = 1000
spawn(w6, 0, C.REF, 9, 4)
H.check('정제소가 서면 병영', A.build_order(w6, ec6, gh6, 0)[:2],
        ('BUILD', C.BARR))
barr = spawn(w6, 0, C.BARR, 4, 9)
H.check('병영이 서면 보병', A.build_order(w6, ec6, gh6, 0),
        ('TRAIN', C.INF, barr))
for _k in range(6):
    spawn(w6, 0, C.INF, 6, 6)
ec6.recount_supply(w6)
H.check('군대가 6 이면, 적 기지를 모르면 방어', A.build_order(w6, ec6, gh6, 0),
        ('DEFEND',))
efoe = spawn(w6, 1, C.HQ, 20, 20)
fg6.add_sight(0, 20, 20, 4)
gh6.update(w6, fg6, 0)
H.check('적 기지를 알면 전군 공격', A.build_order(w6, ec6, gh6, 0),
        ('ATTACK', 20, 20))
H.check('여섯 줄이 전부다', len(A.RULES), 6)

# ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────
m7 = grid(['.' * 16] * 16)
w7 = S.World(16, 16)
mv7 = M.Movement(w7, m7)
ords = SEL.Orders()
me = spawn(w7, 0, C.ARCHER, 2, 2)          # 사거리 4
mv7.claim(me)
w7.state[me] = C.ST_IDLE
A.unit_tick(w7, me, m7, mv7, ords)
H.check('적이 없으면 IDLE 그대로', w7.state[me], C.ST_IDLE)
foe = spawn(w7, 1, C.INF, 4, 2)
mv7.claim(foe)
A.unit_tick(w7, me, m7, mv7, ords)
H.check('사거리 안에 적이 있으면 ATTACK', w7.state[me], C.ST_ATTACK)
H.check('표적이 잡힌다', w7.target[me], w7.handle(foe))
w7.tx[foe] = 2 + C.RANGE[C.ARCHER] + A.CHASE_R
A.unit_tick(w7, me, m7, mv7, ords)
H.check('사거리 + 추격 %d타일 안이면 쫓아간다' % A.CHASE_R,
        w7.state[me], C.ST_MOVE)
w7.tx[foe] += 1
w7.state[me] = C.ST_ATTACK
A.unit_tick(w7, me, m7, mv7, ords)
H.check('한 칸만 더 멀어도 포기하고 IDLE', w7.state[me], C.ST_IDLE)
w7.kill(w7.handle(foe))
w7.state[me] = C.ST_ATTACK
w7.target[me] = 0
A.unit_tick(w7, me, m7, mv7, ords)
H.check('표적이 죽으면 IDLE', w7.state[me], C.ST_IDLE)

hv = spawn(w7, 0, C.HARV, 3, 3)
mv7.claim(hv)
w7.hp[hv] = C.HP[C.HARV] // 5              # 25% 아래
spawn(w7, 0, C.REF, 1, 1)
A.unit_tick(w7, hv, m7, mv7, ords)
H.check('hp 25%% 아래인 채집기는 도망친다', w7.state[hv], C.ST_FLEE)
w7.hp[hv] = C.HP[C.HARV]
A.unit_tick(w7, hv, m7, mv7, ords)
H.check('회복하면 다시 캔다', w7.state[hv], C.ST_SEEK)

# ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────
m8 = grid(['.' * 16] * 16)
fg8 = FG.Fog(16, 16)
tg = A.scout_targets(m8, fg8, 0)
H.check('16x16 이면 클러스터 4개', len(tg), 4)
H.check('클러스터 중심, 번호 오름차순', tg, [(4, 4), (12, 4), (4, 12), (12, 12)])
fg8.add_sight(0, 2, 2, 1)                  # 클러스터 0 안에만 드는 작은 원
H.check('탐험한 클러스터는 빠진다', A.scout_targets(m8, fg8, 0), tg[1:])
fg9 = FG.Fog(16, 16)
for _i in range(16 * 16):
    fg9.explored[0][_i] = 1
H.check('전부 탐험하면 빈 목록', A.scout_targets(m8, fg9, 0), [])
H.note('정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다')

H.done()
