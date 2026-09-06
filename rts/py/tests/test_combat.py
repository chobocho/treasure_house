# -*- coding: utf-8 -*-
"""전투 — 피해 공식·표적 선택·투사체·스플래시·란체스터 (SPEC §15)."""
from __future__ import print_function

import harness as H
from rts import combat as CB
from rts import const as C
from rts import fixed as F
from rts import rng as R
from rts import spatial as S

H.title('combat')

g = H.golden('prim.txt').split('\n')

# ── 골든 11절 피해표 ────────────────────────────────────────────────────────
i = g.index('== 11. 전투 ==') + 2
bad = 0
rows = 0
while g[i].strip() and not g[i].startswith('란체스터'):
    basic, pierce, armour, wmx, wlo, wn, we, wsim = [int(v) for v in g[i].split()]
    mx = CB.max_damage(basic, pierce, armour)
    lo = CB.damage_lo(mx)
    r = R.LCG(12345)
    tot = sum(CB.roll_damage(r, basic, pierce, armour) for _ in range(1000))
    got = [mx, lo, mx - lo + 1, CB.expect100(basic, pierce, armour),
           tot * 100 // 1000]
    if got != [wmx, wlo, wn, we, wsim]:
        bad += 1
        H.note('%d/%d/%d 기대 %s 실제 %s', basic, pierce, armour,
               [wmx, wlo, wn, we, wsim], got)
    rows += 1
    i += 1
H.check('골든 11절 피해표 %d줄' % rows, bad, 0)

# ── 골든 11절 란체스터 ──────────────────────────────────────────────────────
i = g.index('란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)') + 1
bad = 0
rows = 0
while i < len(g) and g[i].startswith(' '):
    a0, b0, al, be, wt, wa, wb = [int(v) for v in g[i].split()]
    if list(CB.lanchester_sim(a0, b0, al, be)) != [wt, wa, wb]:
        bad += 1
        H.note('%d vs %d 기대 %s 실제 %s', a0, b0, [wt, wa, wb],
               list(CB.lanchester_sim(a0, b0, al, be)))
    rows += 1
    i += 1
H.check('골든 11절 란체스터 %d줄' % rows, bad, 0)

# ── SPEC §15.2 피해 공식의 경계 ─────────────────────────────────────────────
H.check('최대 피해 = 기본 − 방어 + 관통', CB.max_damage(12, 8, 3), 17)
H.check('방어가 커도 최소 1 (이 덱의 규칙)', CB.max_damage(2, 0, 99), 1)
H.check('음수가 되어도 1', CB.max_damage(0, 0, 5), 1)
H.check('lo = ceil(mx/2)', [CB.damage_lo(k) for k in (1, 2, 3, 4, 9, 10)],
        [1, 1, 2, 2, 5, 5])
H.check('mx=1 이면 피해는 늘 1', CB.damage_lo(1), 1)
r = R.LCG(1)
vals = [CB.roll_damage(r, 6, 3, 2) for _ in range(2000)]
H.check('피해는 lo..mx 범위 안', [min(vals), max(vals)], [4, 7])
H.check('네 값이 모두 나온다', sorted(set(vals)), [4, 5, 6, 7])
H.check('E[dmg]*100 = (lo+mx)*50', CB.expect100(6, 3, 2), 550)
H.check_true('시뮬 평균이 기대값의 2% 안',
             abs(sum(vals) * 100 // len(vals) - 550) <= 11)

# ── 정리 15.1 — 기대값이 0.75·mx 근처인가 ───────────────────────────────────
even = odd = 0
for mx in range(1, 40):
    e = (CB.damage_lo(mx) + mx) * 50
    if mx % 2 == 0 and e != 75 * mx:
        even += 1
    if mx % 2 == 1 and e != 75 * mx + 25:
        odd += 1
H.check('짝수 mx 에서 E = 0.75·mx (정리 15.1)', even, 0)
H.check('홀수 mx 에서 E = 0.75·mx + 0.25 — 올림이 한 칸 올린다', odd, 0)
H.note('SPEC 초안은 이 둘을 뒤집어 적고 있었다 — 이 시험이 잡았다')

# ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
w = S.World(32, 32)
me = S.index(w.spawn(0, C.ARCHER, 10, 10))          # 사거리 4
near = S.index(w.spawn(1, C.INF, 12, 10))           # 거리 2
far = S.index(w.spawn(1, C.INF, 20, 10))            # 거리 10
tie_a = S.index(w.spawn(1, C.INF, 10, 13))          # 거리 3
tie_b = S.index(w.spawn(1, C.INF, 13, 10))          # 거리 3
mate = S.index(w.spawn(0, C.INF, 11, 10))           # 아군
for k in (me, near, far, tie_a, tie_b, mate):
    w.hp[k] = C.HP[w.kind[k]]

H.check('사거리는 체비셰프', CB.in_range(w, me, near), True)
H.check('사거리 밖', CB.in_range(w, me, far), False)
H.check('대각 3칸도 사거리 4 안', CB.in_range(w, me, tie_a), True)
t, appr = CB.pick_target(w, me, 0, False)
H.check('가장 가까운 적을 고른다', t, w.handle(near))
H.check('접근할 필요는 없다', appr, False)
H.check('아군은 고르지 않는다', t != w.handle(mate), True)

w.target[me] = w.handle(tie_a)
t, _a = CB.pick_target(w, me, 0, False)
H.check('현재 표적이 살아 있고 사거리 안이면 그대로 (규칙 1)',
        t, w.handle(tie_a))
w.hp[tie_a] = 0
w.kill(w.handle(tie_a))
t, _a = CB.pick_target(w, me, 0, False)
H.check('표적이 죽으면 다시 고른다', t, w.handle(near))

w.target[me] = 0
t, _a = CB.pick_target(w, me, w.handle(tie_b), False)
H.check('나를 때린 적이 사거리 안이면 그것 (규칙 2)', t, w.handle(tie_b))
t, _a = CB.pick_target(w, me, w.handle(far), False)
H.check('나를 때린 적이 사거리 밖이면 규칙 3 으로', t, w.handle(near))

# 동점 — 핸들 오름차순
w2 = S.World(32, 32)
a = S.index(w2.spawn(0, C.ARCHER, 10, 10))
e1 = S.index(w2.spawn(1, C.INF, 12, 10))
e2 = S.index(w2.spawn(1, C.INF, 8, 10))
for k in (a, e1, e2):
    w2.hp[k] = C.HP[w2.kind[k]]
H.check('d83 동점이면 핸들 오름차순', CB.pick_target(w2, a, 0, False)[0],
        w2.handle(e1))
H.check_true('핸들이 작은 쪽이 먼저다', w2.handle(e1) < w2.handle(e2))

# 규칙 4 — ATTACK_MOVE 만 사거리+2 를 훑는다
w3 = S.World(32, 32)
a = S.index(w3.spawn(0, C.INF, 10, 10))             # 사거리 1
e = S.index(w3.spawn(1, C.INF, 13, 10))             # 거리 3 = 사거리+2
for k in (a, e):
    w3.hp[k] = C.HP[w3.kind[k]]
H.check('보통은 사거리 밖이면 표적 없음', CB.pick_target(w3, a, 0, False),
        (0, False))
H.check('ATTACK_MOVE 는 사거리+2 안을 훑고 접근한다',
        CB.pick_target(w3, a, 0, True), (w3.handle(e), True))
w3.tx[e] = 14
H.check('사거리+3 은 ATTACK_MOVE 도 못 본다',
        CB.pick_target(w3, a, 0, True), (0, False))
H.check('채집기는 공격하지 않는다',
        CB.pick_target(w3, S.index(w3.spawn(0, C.HARV, 13, 10)), 0, True),
        (0, False))

# ── SPEC §15.3 직선 투사체 ──────────────────────────────────────────────────
pj = CB.Projectiles(32)
H.check('처음에는 비어 있다', pj.n(), 0)
ok = pj.launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(80), F.fp(16),
               CB.ARROW_SPEED, 999, 7)
H.check('발사 성공', ok, True)
H.check('한 발', pj.n(), 1)
H.check('수평 발사면 vy 는 0', pj.vy[0], 0)
H.check('vx 는 화살 속도 그대로', pj.vx[0], CB.ARROW_SPEED)
H.check('ttl = 거리/속도 + 2', pj.ttl[0], F.floordiv(F.fp(64), CB.ARROW_SPEED) + 2)
hits = []
for _t in range(40):
    hits += pj.step()
    if not pj.n():
        break
H.check('언젠가 반드시 명중 또는 소멸한다', len(hits), 1)
H.check('명중 정보는 (목표 핸들, 피해, 목표 타일)', hits[0][:2], (999, 7))
H.check('명중 타일은 목표 타일', hits[0][2], 1 * 32 + 5)
H.check('명중하면 목록에서 사라진다', pj.n(), 0)

H.check('같은 칸이면 발사하지 않고 즉시 명중',
        pj.launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(16), F.fp(16),
                  CB.ARROW_SPEED, 1, 5), False)
H.check('그래도 목록은 비어 있다', pj.n(), 0)

# 속도 벡터의 크기가 speed 인가 (대각 발사)
pj2 = CB.Projectiles(32)
pj2.launch(CB.STRAIGHT, 0, 0, F.fp(60), F.fp(80), CB.ARROW_SPEED, 1, 1)
mag = F.fp_sqrt(F.fp_mul(pj2.vx[0], pj2.vx[0]) + F.fp_mul(pj2.vy[0], pj2.vy[0]))
H.check_true('|v| == speed (오차 1% 안)',
             abs(mag - CB.ARROW_SPEED) <= CB.ARROW_SPEED // 100)
H.note('발사 시점의 위치로 날아간다 — 빠른 유닛은 화살을 피할 수 있다')

# ── SPEC §15.4 포물선 투사체와 정리 15.2 ────────────────────────────────────
pj3 = CB.Projectiles(64)
x0, y0, x1, y1 = F.fp(16), F.fp(200), F.fp(16 + 96), F.fp(200)
pj3.launch(CB.ARC, x0, y0, x1, y1, 0, 55, 20)
T = pj3.ttl[0]
H.check('비행 시간 T = max(6, d/24)', T, max(6, 96 // 24))
ys = []
hits = []
while pj3.n():
    ys.append(pj3.y[0])
    hits += pj3.step()
H.check('T틱 뒤에 명중한다', len(hits), 1)
H.check_true('가는 동안 위로 올라갔다 내려온다', min(ys) < y0)
land = hits[0][3]
H.check('착탄점의 오차는 정리 15.2 의 G·T/2', land - y1, CB.G * T // 2)
H.note('보정하지 않기로 한 결정이다 — 0.15px 는 타일 판정에 영향이 없다')
H.check('수평은 등속', pj3.n(), 0)

# ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
H.check('링 0 은 그대로', CB.splash_damage(20, 0), 20)
H.check('링 1 은 절반', CB.splash_damage(20, 1), 10)
H.check('링 2 는 1/4', CB.splash_damage(20, 2), 5)
H.check('링 3 이상은 0', [CB.splash_damage(20, k) for k in (3, 4, 9)], [0, 0, 0])
H.check('홀수는 내림', [CB.splash_damage(7, 1), CB.splash_damage(7, 2)], [3, 1])
H.check('피해 1 도 링 1 에서는 0', CB.splash_damage(1, 1), 0)

w4 = S.World(16, 16)
mine = S.index(w4.spawn(0, C.INF, 5, 5))
foe = S.index(w4.spawn(1, C.INF, 6, 5))
away = S.index(w4.spawn(1, C.INF, 9, 5))
for k in (mine, foe, away):
    w4.hp[k] = 40
sp = CB.splash_hits(w4, 5, 5, 20)
H.check('명중 칸의 유닛은 전액', dict(sp)[w4.handle(mine)], 20)
H.check('링 1 은 절반 — 아군도 맞는다', dict(sp)[w4.handle(foe)], 10)
H.check('링 3 밖은 목록에 없다', w4.handle(away) in dict(sp), False)
H.check('스플래시 목록은 핸들 오름차순',
        [h for h, _d in sp], sorted(h for h, _d in sp))
H.note('아군 오사는 AI 의 제약이다 — 17부에서 박격포 사격 규칙에 쓰인다')

# ── 란체스터의 경계 ─────────────────────────────────────────────────────────
H.check('한쪽이 0 이면 즉시 끝', CB.lanchester_sim(0, 10, 6554, 6554)[0], 0)
H.check('둘 다 0', CB.lanchester_sim(0, 0, 6554, 6554), (0, 0, 0))
H.check('전투력이 0 이면 10000틱 상한에서 멈춘다',
        CB.lanchester_sim(10, 10, 0, 0)[0], 10000)
t, a, b = CB.lanchester_sim(20, 10, 6554, 6554)
H.check_true('수가 2배면 손실 없이 가깝게 이긴다 (제곱 법칙)', a >= 16 and b == 0)
H.note('α·A² − β·B² 가 불변이므로 400−100 = 300 → √300 ≈ 17.3 이 이론값이다')

H.done()
