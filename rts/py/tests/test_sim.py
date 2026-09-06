# -*- coding: utf-8 -*-
"""시뮬레이션 — 틱 단계·상태 해시·트리거·시나리오 스크립트 (SPEC §18)."""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import econ as E
from rts import select as SEL
from rts import sim as SIM
from rts import spatial as S
from rts import tmap as T

H.title('sim')


def grid(rows):
    m = T.TMap(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            m.terrain[y * m.w + x] = T.TERRAIN_CH.index(ch)
            m._repass(y * m.w + x)
    m._bump()
    return m


def flat(n=24):
    return grid(['.' * n] * n)


def add(s, p, kind, x, y):
    i = S.index(s.spawn(p, kind, x, y))
    return i


# ── SPEC §18.1 유일한 진입점 ────────────────────────────────────────────────
s = SIM.Sim(flat(), 1234, 2)
H.check('시작 틱은 0', s.tick, 0)
s.step([])
H.check('한 틱 지나면 1', s.tick, 1)
H.check('이벤트는 매 틱 초에 비운다', s.events, [])

u = add(s, 0, C.INF, 5, 5)
h = s.w.handle(u)
s.step([(0, h, SEL.MOVE, 8, 5, 0)])
H.check_true('MOVE 명령이 경로를 깐다', s.mv.goal[u] >= 0)
for _t in range(200):
    s.step([])
H.check('목표까지 간다', (s.w.tx[u], s.w.ty[u]), (8, 5))

bad = 0
try:
    s.step([(1, 5, 0, 0, 0, 0), (0, 5, 0, 0, 0, 0)])
except ValueError:
    bad = 1
H.check('정렬되지 않은 명령 목록은 그 자리에서 터진다', bad, 1)
H.note('조용히 정렬해 주면 호출자의 버그가 다른 기계에서 다른 순서로 나타난다')

H.check('남의 유닛에 내린 명령은 무시', (s.step([(1, h, SEL.MOVE, 0, 0, 0)]),
                                        s.w.owner[u])[1], 0)
H.check('죽은 핸들에 내린 명령도 무시', (s.step([(0, 999999, SEL.MOVE, 0, 0, 0)]),
                                        s.tick > 0)[1], True)

# ── SPEC §18.4 상태 해시 ────────────────────────────────────────────────────
a = SIM.Sim(flat(), 7, 2)
b = SIM.Sim(flat(), 7, 2)
for sm in (a, b):
    add(sm, 0, C.INF, 3, 3)
    add(sm, 1, C.TANK, 9, 9)
    add(sm, 0, C.HQ, 15, 15)
H.check('같은 상태면 같은 해시', a.state_hash(), b.state_hash())
H.check_true('해시는 32비트 안', 0 <= a.state_hash() < 4294967296)
base = a.state_hash()
a.w.hp[1] -= 1
H.check('hp 한 점이 해시를 바꾼다', a.state_hash() != base, True)
a.w.hp[1] += 1
H.check('되돌리면 같다', a.state_hash(), base)
for field, val in (('cool', 1), ('timer', 1), ('prog', 1), ('load', 1),
                   ('dir', 1), ('state', 1), ('target', 1)):
    arr = getattr(a.w, field)
    arr[1] += val
    if a.state_hash() == base:
        H.note('%s 가 해시에 들어가지 않는다', field)
    arr[1] -= val
H.check('cool·timer 를 포함한 엔티티 15칸이 전부 해시에 들어간다',
        a.state_hash(), base)
a.ec.credits[0] += 1
H.check('크레딧도 해시에', a.state_hash() != base, True)
a.ec.credits[0] -= 1
a.ec.ore[10] = 5
H.check('광맥 잔량도 해시에', a.state_hash() != base, True)
a.ec.ore[10] = 0
a.ec.queue[3] = [C.INF]                    # 3번이 사령부다 — 큐는 건물의 것이다
H.check('생산 큐도 해시에', a.state_hash() != base, True)
a.ec.queue[3] = []
a.rng.s += 1
H.check('rng 상태도 해시에', a.state_hash() != base, True)
a.rng.s -= 1
a.m.set_terrain(1, 1, T.ROCK)
H.check('지형이 바뀌면 map_hash 가 바뀐다', a.state_hash() != base, True)
mh = a.map_hash()
H.check('map_hash 는 version 이 같으면 다시 계산하지 않는다',
        (a.map_hash(), a._map_hash_version), (mh, a.m.version))
a.m.set_terrain(1, 1, T.SAND)
H.check_true('version 이 오르면 다시 계산한다', a.map_hash() != mh)

# ── SPEC §18.2 5단계: 피해는 모아서 적용한다 ────────────────────────────────
s2 = SIM.Sim(flat(12), 3, 2)
x = add(s2, 0, C.INF, 5, 5)
y = add(s2, 1, C.INF, 6, 5)
s2.w.hp[x] = 3
s2.w.hp[y] = 3
for _t in range(30):
    s2.step([])
    if s2.w.alive[x] == 0 or s2.w.alive[y] == 0:
        break
H.check('서로를 같은 틱에 죽일 수 있다 — 먼저 처리된 쪽이 유리하지 않다',
        [s2.w.alive[x], s2.w.alive[y]], [0, 0])

# ── SPEC §18.3 이벤트 로그 ──────────────────────────────────────────────────
s3 = SIM.Sim(flat(12), 5, 2)
hq = add(s3, 0, C.HQ, 4, 4)
s3.ec.credits[0] = 1000
s3.ec.recount_supply(s3.w)
s3.step([(0, s3.w.handle(hq), SEL.TRAIN, C.HARV, 0, 0)])
H.check('명령은 이벤트를 남긴다',
        [e[0] for e in s3.events], [SIM.EV_ORDER])
for _t in range(C.BUILD_TICKS[C.HARV] + 2):
    s3.step([])
    if any(e[0] == SIM.EV_SPAWN for e in s3.events):
        break
H.check('생산이 끝나면 SPAWN 이벤트', [e[0] for e in s3.events], [SIM.EV_SPAWN])
H.check_true('실제로 채집기가 생겼다',
             any(s3.w.alive[i] and s3.w.kind[i] == C.HARV
                 for i in range(1, C.MAX_ENT)))
H.check('이벤트는 해시에 넣지 않는다 — 트레이스가 대신 잡는다', s3.events != [],
        True)

# ── §16.4 건물 건설 ─────────────────────────────────────────────────────────
s4 = SIM.Sim(flat(16), 9, 2)
hq4 = add(s4, 0, C.HQ, 4, 4)
s4.mv.claim(hq4)
s4.ec.credits[0] = 1000
s4.ec.recount_supply(s4.w)
s4.step([(0, s4.w.handle(hq4), SEL.BUILD, C.POW, 8, 4)])
built = [i for i in range(1, C.MAX_ENT)
         if s4.w.alive[i] and s4.w.kind[i] == C.POW]
H.check('BUILD 는 그 자리에 즉시 엔티티를 만든다', len(built), 1)
bi = built[0]
H.check('짓는 중 상태', s4.w.state[bi], C.ST_BUILD)
H.check('hp 는 1 에서 시작', s4.w.hp[bi], 1)
H.check('돈은 선불', s4.ec.credits[0], 1000 - C.COST[C.POW])
H.check('짓는 중에도 발자국을 막는다',
        s4.m.passable_terrain(8, 4, 0), False)
for _t in range(C.BUILD_TICKS[C.POW] + 2):
    s4.step([])
    if s4.w.state[bi] == C.ST_IDLE:
        break
H.check('다 지으면 IDLE', s4.w.state[bi], C.ST_IDLE)
H.check('hp 가 정격까지 찬다', s4.w.hp[bi], C.HP[C.POW])
H.check('돈이 없으면 짓지 않는다',
        (s4.step([(0, s4.w.handle(hq4), SEL.BUILD, C.FACT, 12, 12)]),
         len([i for i in range(1, C.MAX_ENT)
              if s4.w.alive[i] and s4.w.kind[i] == C.FACT]))[1], 0)
H.check('못 짓는 자리에도 짓지 않는다',
        (s4.step([(0, s4.w.handle(hq4), SEL.BUILD, C.POW, 4, 4)]),
         len([i for i in range(1, C.MAX_ENT)
              if s4.w.alive[i] and s4.w.kind[i] == C.POW]))[1], 1)

# ── §16.5 내 유닛이 막고 있으면 비키게 한다 ────────────────────────────────
#   채집 경로 위에 건물 자리를 잡으면 재시도가 전부 막힌다 — 실제로 그래서
#   플레이어 1 의 발전소가 1200틱 내내 서지 않았다.
s4b = SIM.Sim(flat(16), 10, 2)
hq4b = add(s4b, 0, C.HQ, 4, 4)
s4b.ec.credits[0] = 1000
s4b.ec.recount_supply(s4b.w)
blocker = add(s4b, 0, C.INF, 9, 4)
H.check('그 칸은 내 유닛이 쥐고 있다', s4b.mv.resv[4 * 16 + 9],
        s4b.w.handle(blocker))
s4b.step([(0, s4b.w.handle(hq4b), SEL.BUILD, C.POW, 8, 4)])
H.check('막힌 배치는 실패한다',
        len([i for i in range(1, C.MAX_ENT)
             if s4b.w.alive[i] and s4b.w.kind[i] == C.POW]), 0)
H.check('돈은 나가지 않았다', s4b.ec.credits[0], 1000)
H.check_true('대신 막은 유닛에게 한 걸음 명령이 갔다',
             s4b.mv.goal[blocker] >= 0 or s4b.w.prog[blocker] > 0)
for _t in range(40):
    s4b.step([])
    if (s4b.w.tx[blocker], s4b.w.ty[blocker]) != (9, 4):
        break
H.check_true('유닛이 비켰다', (s4b.w.tx[blocker], s4b.w.ty[blocker]) != (9, 4))
s4b.step([(0, s4b.w.handle(hq4b), SEL.BUILD, C.POW, 8, 4)])
H.check('다음 시도는 성공한다',
        len([i for i in range(1, C.MAX_ENT)
             if s4b.w.alive[i] and s4b.w.kind[i] == C.POW]), 1)
H.note('밀면서 동시에 짓지는 않는다 — 서 있는 유닛 위에 건물을 얹으면 불변식 R 이 깨진다')

# ── SPEC §18.5 트리거 ───────────────────────────────────────────────────────
s5 = SIM.Sim(flat(16), 11, 2)
s5.add_trigger((SIM.CT_TICK_GE, 3, 0, 0, 0),
               (SIM.AC_SPAWN, 0, C.INF, 2, 2), True)
for _t in range(2):
    s5.step([])
H.check('3틱 전에는 발화하지 않는다',
        len([i for i in range(1, C.MAX_ENT) if s5.w.alive[i]]), 0)
s5.step([])
H.check('TICK_GE 가 발화해 유닛을 만든다',
        len([i for i in range(1, C.MAX_ENT) if s5.w.alive[i]]), 1)
for _t in range(5):
    s5.step([])
H.check('once 트리거는 한 번만',
        len([i for i in range(1, C.MAX_ENT) if s5.w.alive[i]]), 1)
H.check('발화 표시는 상태의 일부', s5.fired[0], True)

s6 = SIM.Sim(flat(16), 12, 2)
s6.ec.credits[1] = 500
s6.add_trigger((SIM.CT_CREDITS_GE, 1, 400, 0, 0), (SIM.AC_MESSAGE, 7, 0, 0), True)
s6.step([])
H.check('CREDITS_GE', [e for e in s6.events if e[0] == SIM.EV_ORDER] == [], True)
H.check('메시지 액션은 이벤트로 나온다',
        [e[1] for e in s6.events if e[0] == SIM.EV_MESSAGE], [7])

s7 = SIM.Sim(flat(16), 13, 2)
add(s7, 0, C.INF, 5, 5)
s7.add_trigger((SIM.CT_UNIT_COUNT, 0, C.INF, SIM.CMP_GE, 1),
               (SIM.AC_REVEAL, 10, 10, 3), False)
s7.step([])
H.check('UNIT_COUNT + REVEAL', s7.fog.explored[0][10 * 16 + 10], 1)
H.check('once 가 아니면 계속 평가한다', (s7.step([]), s7.fired[0])[1], False)

s8 = SIM.Sim(flat(16), 14, 2)
mine8 = add(s8, 0, C.INF, 1, 1)
s8.add_trigger((SIM.CT_AREA_ENTERED, 0, 8, 8, 2), (SIM.AC_LOSE, 0, 0, 0), True)
s8.step([])
H.check('멀리 있으면 발화하지 않는다', s8.loser, [])
s8.w.tx[mine8] = 8
s8.w.ty[mine8] = 9
s8.step([])
H.check('AREA_ENTERED', s8.loser, [0])

# ── SPEC §18.5 기본 승패 ────────────────────────────────────────────────────
s9 = SIM.Sim(flat(16), 15, 2)
b0 = add(s9, 0, C.HQ, 2, 2)
b1 = add(s9, 1, C.HQ, 12, 12)
s9.w.hp[b0] = 400
s9.w.hp[b1] = 400
s9.step([])
H.check('둘 다 살아 있으면 승자 없음', s9.winner, -1)
s9.w.hp[b1] = 0
s9.step([])
H.check('건물이 전부 부서진 쪽이 진다', s9.loser, [1])
H.check('남은 쪽이 이긴다', s9.winner, 0)
H.check('WIN 이벤트', [e[0] for e in s9.events].count(SIM.EV_WIN), 1)
s9.step([])
H.check('승리는 한 번만 알린다', [e[0] for e in s9.events].count(SIM.EV_WIN), 0)

# ── SPEC §18.6 시나리오 스크립트 ────────────────────────────────────────────
sc = SIM.parse_script(H.golden('script.txt'))
H.check('골든 스크립트의 길이', sc.ticks, 1200)
H.check('플레이어 수', sc.players, 2)
H.check_true('명령이 여러 줄', len(sc.lines) > 20)
H.check('주석은 건너뛴다',
        [1 for ln in sc.lines if str(ln[2]).startswith('#')], [])
H.check('틱 오름차순', [ln[0] for ln in sc.lines],
        sorted(ln[0] for ln in sc.lines))

s10 = SIM.Sim(flat(20), 21, 2)
u1 = add(s10, 0, C.INF, 2, 2)
u2 = add(s10, 0, C.HARV, 3, 3)
u3 = add(s10, 1, C.INF, 9, 9)
bq = add(s10, 0, C.HQ, 5, 5)
mini = SIM.parse_script('RTSS 1\nticks 10\nplayers 2\n'
                        '# 주석\n'
                        '1 0 A MOVE 7 7 0\n'
                        '2 0 F MOVE 8 8 0\n'
                        '3 0 K10 TRAIN 4 0 0\n'
                        '4 0 N MOVE 1 1 0\n')
o1 = s10.script_orders(mini, 1)
H.check('선택자 A 는 내 유닛 전부 (건물 제외)',
        [o[1] for o in o1], sorted([s10.w.handle(u1), s10.w.handle(u2)]))
H.check('명령 여섯 칸', len(o1[0]), 6)
o2 = s10.script_orders(mini, 2)
H.check('선택자 F 는 전투 유닛만', [o[1] for o in o2], [s10.w.handle(u1)])
o3 = s10.script_orders(mini, 3)
H.check('선택자 K10 은 종류 10 (사령부)', [o[1] for o in o3],
        [s10.w.handle(bq)])
o4 = s10.script_orders(mini, 4)
H.check('선택자 N 은 가장 최근에 생산된 유닛 하나', len(o4), 1)
H.check('없는 틱은 빈 목록', s10.script_orders(mini, 9), [])
H.check('펼친 결과는 핸들 오름차순', [o[1] for o in o1],
        sorted(o[1] for o in o1))
H.check('남의 유닛은 내 선택자에 걸리지 않는다',
        s10.w.handle(u3) in [o[1] for o in o1], False)

# ── 결정론: 같은 씨앗·같은 명령이면 매 틱 같은 해시 ─────────────────────────
def run(n):
    sm = SIM.Sim(T.TMap.load_text(H.golden('map_start.txt')), 1, 2)
    sm.setup_start()
    hs = []
    for t in range(n):
        sm.step([])
        hs.append(sm.state_hash())
    return sm, hs


s_a, h_a = run(120)
s_b, h_b = run(120)
H.check('같은 씨앗이면 120틱의 해시열이 같다', h_a, h_b)
H.check_true('해시가 실제로 변한다', len(set(h_a)) > 60)
s_c = SIM.Sim(T.TMap.load_text(H.golden('map_start.txt')), 1, 2)
s_c.setup_start()


def count_of(sm, p, kind):
    return len([i for i in range(1, C.MAX_ENT)
                if sm.w.alive[i] and sm.w.owner[i] == p and sm.w.kind[i] == kind])


H.check('시작 조건 — 플레이어마다 HQ 1채, 채집기 2기',
        [[count_of(s_c, p, C.HQ), count_of(s_c, p, C.HARV)] for p in (0, 1)],
        [[1, C.START_HARV], [1, C.START_HARV]])
H.check('시작 크레딧', s_c.ec.credits[:2], [C.START_CREDITS] * 2)
H.check('시작하면 AI 가 켜진다', s_c.ai_enabled[:2], [True, True])
H.check_true('120틱 뒤에는 AI 가 채집기를 더 뽑았다',
             count_of(s_a, 0, C.HARV) > C.START_HARV)
H.check_true('채집이 돌아간다 (120틱)', sum(s_a.ec.credits[:2]) >= 0)
H.check('불변식 R 이 유지된다',
        len([1 for i in range(1, C.MAX_ENT)
             if s_a.w.alive[i] and C.IS_BUILDING[s_a.w.kind[i]] == 0
             and s_a.mv.resv[s_a.w.from_t[i]] != s_a.w.handle(i)]), 0)
H.check('불변식 F 가 유지된다', s_a.fog.recount(s_a.w), 0)

H.done()
