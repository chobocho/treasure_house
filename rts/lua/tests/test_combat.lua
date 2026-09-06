-- 전투 — 피해 공식·표적 선택·투사체·스플래시·란체스터 (SPEC §15).

local H = require('tests.harness')
local CB = require('rts.combat')
local C = require('rts.const')
local F = require('rts.fixed')
local R = require('rts.rng')
local S = require('rts.spatial')

H.title('combat')

local floor = math.floor
local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local g = H.lines(H.golden('prim.txt'))

-- ── 골든 11절 피해표 ────────────────────────────────────────────────────────
local i = H.index_of(g, '== 11. 전투 ==') + 2
local bad = 0
local rows = 0
while H.strip(g[i]) ~= '' and g[i]:sub(1, #'란체스터') ~= '란체스터' do
    local v = H.ints(g[i])
    local basic, pierce, armour = v[0], v[1], v[2]
    local wmx, wlo, wn, we, wsim = v[3], v[4], v[5], v[6], v[7]
    local mx = CB.max_damage(basic, pierce, armour)
    local lo = CB.damage_lo(mx)
    local r = R.new(12345)
    local tot = 0
    for _ = 1, 1000 do
        tot = tot + CB.roll_damage(r, basic, pierce, armour)
    end
    local got = arr(mx, lo, mx - lo + 1, CB.expect100(basic, pierce, armour),
                    F.floordiv(tot * 100, 1000))
    local wnt = arr(wmx, wlo, wn, we, wsim)
    if not H.deep_eq(got, wnt) then
        bad = bad + 1
        H.note('%d/%d/%d 기대 %s 실제 %s', basic, pierce, armour,
               H.repr(wnt), H.repr(got))
    end
    rows = rows + 1
    i = i + 1
end
H.check(string.format('골든 11절 피해표 %d줄', rows), bad, 0)

-- ── 골든 11절 란체스터 ──────────────────────────────────────────────────────
i = H.index_of(g, '란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)') + 1
bad = 0
rows = 0
while i < g.n and g[i]:sub(1, 1) == ' ' do
    local v = H.ints(g[i])
    local t, a, b = CB.lanchester_sim(v[0], v[1], v[2], v[3])
    local got = arr(t, a, b)
    local wnt = arr(v[4], v[5], v[6])
    if not H.deep_eq(got, wnt) then
        bad = bad + 1
        H.note('%d vs %d 기대 %s 실제 %s', v[0], v[1], H.repr(wnt), H.repr(got))
    end
    rows = rows + 1
    i = i + 1
end
H.check(string.format('골든 11절 란체스터 %d줄', rows), bad, 0)

-- ── SPEC §15.2 피해 공식의 경계 ─────────────────────────────────────────────
H.check('최대 피해 = 기본 − 방어 + 관통', CB.max_damage(12, 8, 3), 17)
H.check('방어가 커도 최소 1 (이 덱의 규칙)', CB.max_damage(2, 0, 99), 1)
H.check('음수가 되어도 1', CB.max_damage(0, 0, 5), 1)
H.check('lo = ceil(mx/2)',
        arr(CB.damage_lo(1), CB.damage_lo(2), CB.damage_lo(3),
            CB.damage_lo(4), CB.damage_lo(9), CB.damage_lo(10)),
        arr(1, 1, 2, 2, 5, 5))
H.check('mx=1 이면 피해는 늘 1', CB.damage_lo(1), 1)
local r = R.new(1)
local vals = {n = 0}
local vmin, vmax, vsum = 999, -999, 0
local seenv = {}
for _ = 1, 2000 do
    local v = CB.roll_damage(r, 6, 3, 2)
    vals[vals.n] = v
    vals.n = vals.n + 1
    if v < vmin then vmin = v end
    if v > vmax then vmax = v end
    vsum = vsum + v
    seenv[v] = true
end
H.check('피해는 lo..mx 범위 안', arr(vmin, vmax), arr(4, 7))
local uniq = {n = 0}
for v = 0, 20 do
    if seenv[v] then uniq[uniq.n] = v; uniq.n = uniq.n + 1 end
end
H.check('네 값이 모두 나온다', uniq, arr(4, 5, 6, 7))
H.check('E[dmg]*100 = (lo+mx)*50', CB.expect100(6, 3, 2), 550)
local diff = F.floordiv(vsum * 100, vals.n) - 550
if diff < 0 then diff = -diff end
H.check_true('시뮬 평균이 기대값의 2% 안', diff <= 11)

-- ── 정리 15.1 — 기대값이 0.75·mx 근처인가 ───────────────────────────────────
local even, odd = 0, 0
for mx = 1, 39 do
    local e = (CB.damage_lo(mx) + mx) * 50
    if mx % 2 == 0 and e ~= 75 * mx then even = even + 1 end
    if mx % 2 == 1 and e ~= 75 * mx + 25 then odd = odd + 1 end
end
H.check('짝수 mx 에서 E = 0.75·mx (정리 15.1)', even, 0)
H.check('홀수 mx 에서 E = 0.75·mx + 0.25 — 올림이 한 칸 올린다', odd, 0)
H.note('SPEC 초안은 이 둘을 뒤집어 적고 있었다 — 이 시험이 잡았다')

-- ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
local w = S.new(32, 32)
local me = S.index(w:spawn(0, C.ARCHER, 10, 10))     -- 사거리 4
local near = S.index(w:spawn(1, C.INF, 12, 10))      -- 거리 2
local far = S.index(w:spawn(1, C.INF, 20, 10))       -- 거리 10
local tie_a = S.index(w:spawn(1, C.INF, 10, 13))     -- 거리 3
local tie_b = S.index(w:spawn(1, C.INF, 13, 10))     -- 거리 3
local mate = S.index(w:spawn(0, C.INF, 11, 10))      -- 아군
for _, k in ipairs({me, near, far, tie_a, tie_b, mate}) do
    w.hp[k] = C.HP[w.kind[k]]
end

H.check('사거리는 체비셰프', CB.in_range(w, me, near), true)
H.check('사거리 밖', CB.in_range(w, me, far), false)
H.check('대각 3칸도 사거리 4 안', CB.in_range(w, me, tie_a), true)
local t, appr = CB.pick_target(w, me, 0, false)
H.check('가장 가까운 적을 고른다', t, w:handle(near))
H.check('접근할 필요는 없다', appr, false)
H.check('아군은 고르지 않는다', t ~= w:handle(mate), true)

w.target[me] = w:handle(tie_a)
t = CB.pick_target(w, me, 0, false)
H.check('현재 표적이 살아 있고 사거리 안이면 그대로 (규칙 1)', t, w:handle(tie_a))
w.hp[tie_a] = 0
w:kill(w:handle(tie_a))
t = CB.pick_target(w, me, 0, false)
H.check('표적이 죽으면 다시 고른다', t, w:handle(near))

w.target[me] = 0
t = CB.pick_target(w, me, w:handle(tie_b), false)
H.check('나를 때린 적이 사거리 안이면 그것 (규칙 2)', t, w:handle(tie_b))
t = CB.pick_target(w, me, w:handle(far), false)
H.check('나를 때린 적이 사거리 밖이면 규칙 3 으로', t, w:handle(near))

-- 동점 — 핸들 오름차순
local w2 = S.new(32, 32)
local a = S.index(w2:spawn(0, C.ARCHER, 10, 10))
local e1 = S.index(w2:spawn(1, C.INF, 12, 10))
local e2 = S.index(w2:spawn(1, C.INF, 8, 10))
for _, k in ipairs({a, e1, e2}) do w2.hp[k] = C.HP[w2.kind[k]] end
H.check('d83 동점이면 핸들 오름차순', (CB.pick_target(w2, a, 0, false)),
        w2:handle(e1))
H.check_true('핸들이 작은 쪽이 먼저다', w2:handle(e1) < w2:handle(e2))

-- 규칙 4 — ATTACK_MOVE 만 사거리+2 를 훑는다
local w3 = S.new(32, 32)
a = S.index(w3:spawn(0, C.INF, 10, 10))              -- 사거리 1
local e = S.index(w3:spawn(1, C.INF, 13, 10))        -- 거리 3 = 사거리+2
for _, k in ipairs({a, e}) do w3.hp[k] = C.HP[w3.kind[k]] end
H.check('보통은 사거리 밖이면 표적 없음', arr(CB.pick_target(w3, a, 0, false)),
        arr(0, false))
H.check('ATTACK_MOVE 는 사거리+2 안을 훑고 접근한다',
        arr(CB.pick_target(w3, a, 0, true)), arr(w3:handle(e), true))
w3.tx[e] = 14
H.check('사거리+3 은 ATTACK_MOVE 도 못 본다',
        arr(CB.pick_target(w3, a, 0, true)), arr(0, false))
H.check('채집기는 공격하지 않는다',
        arr(CB.pick_target(w3, S.index(w3:spawn(0, C.HARV, 13, 10)), 0, true)),
        arr(0, false))

-- ── SPEC §15.3 직선 투사체 ──────────────────────────────────────────────────
local pj = CB.newprojectiles(32)
H.check('처음에는 비어 있다', pj:n(), 0)
local ok = pj:launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(80), F.fp(16),
                     CB.ARROW_SPEED, 999, 7)
H.check('발사 성공', ok, true)
H.check('한 발', pj:n(), 1)
H.check('수평 발사면 vy 는 0', pj.vy[0], 0)
H.check('vx 는 화살 속도 그대로', pj.vx[0], CB.ARROW_SPEED)
H.check('ttl = 거리/속도 + 2', pj.ttl[0],
        F.floordiv(F.fp(64), CB.ARROW_SPEED) + 2)
local hits = {n = 0}
for _ = 1, 40 do
    local hs = pj:step()
    for k = 0, hs.n - 1 do
        hits[hits.n] = hs[k]
        hits.n = hits.n + 1
    end
    if pj:n() == 0 then break end
end
H.check('언젠가 반드시 명중 또는 소멸한다', hits.n, 1)
H.check('명중 정보는 (목표 핸들, 피해, 목표 타일)',
        arr(hits[0][1], hits[0][2]), arr(999, 7))
H.check('명중 타일은 목표 타일', hits[0][3], 1 * 32 + 5)
H.check('명중하면 목록에서 사라진다', pj:n(), 0)

H.check('같은 칸이면 발사하지 않고 즉시 명중',
        pj:launch(CB.STRAIGHT, F.fp(16), F.fp(16), F.fp(16), F.fp(16),
                  CB.ARROW_SPEED, 1, 5), false)
H.check('그래도 목록은 비어 있다', pj:n(), 0)

-- 속도 벡터의 크기가 speed 인가 (대각 발사)
local pj2 = CB.newprojectiles(32)
pj2:launch(CB.STRAIGHT, 0, 0, F.fp(60), F.fp(80), CB.ARROW_SPEED, 1, 1)
local mag = F.fp_sqrt(F.fp_mul(pj2.vx[0], pj2.vx[0])
                      + F.fp_mul(pj2.vy[0], pj2.vy[0]))
local md = mag - CB.ARROW_SPEED
if md < 0 then md = -md end
H.check_true('|v| == speed (오차 1% 안)', md <= floor(CB.ARROW_SPEED / 100))
H.note('발사 시점의 위치로 날아간다 — 빠른 유닛은 화살을 피할 수 있다')

-- ── SPEC §15.4 포물선 투사체와 정리 15.2 ────────────────────────────────────
local pj3 = CB.newprojectiles(64)
local x0, y0, x1, y1 = F.fp(16), F.fp(200), F.fp(16 + 96), F.fp(200)
pj3:launch(CB.ARC, x0, y0, x1, y1, 0, 55, 20)
local TT = pj3.ttl[0]
H.check('비행 시간 T = max(6, d/24)', TT, (6 > floor(96 / 24)) and 6 or floor(96 / 24))
local ymin = nil
hits = {n = 0}
while pj3:n() > 0 do
    if ymin == nil or pj3.y[0] < ymin then ymin = pj3.y[0] end
    local hs = pj3:step()
    for k = 0, hs.n - 1 do
        hits[hits.n] = hs[k]
        hits.n = hits.n + 1
    end
end
H.check('T틱 뒤에 명중한다', hits.n, 1)
H.check_true('가는 동안 위로 올라갔다 내려온다', ymin < y0)
local land = hits[0][4]
H.check('착탄점의 오차는 정리 15.2 의 G·T/2', land - y1, floor(CB.G * TT / 2))
H.note('보정하지 않기로 한 결정이다 — 0.15px 는 타일 판정에 영향이 없다')
H.check('수평은 등속', pj3:n(), 0)

-- ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
H.check('링 0 은 그대로', CB.splash_damage(20, 0), 20)
H.check('링 1 은 절반', CB.splash_damage(20, 1), 10)
H.check('링 2 는 1/4', CB.splash_damage(20, 2), 5)
H.check('링 3 이상은 0',
        arr(CB.splash_damage(20, 3), CB.splash_damage(20, 4),
            CB.splash_damage(20, 9)), arr(0, 0, 0))
H.check('홀수는 내림', arr(CB.splash_damage(7, 1), CB.splash_damage(7, 2)),
        arr(3, 1))
H.check('피해 1 도 링 1 에서는 0', CB.splash_damage(1, 1), 0)

local w4 = S.new(16, 16)
local mine = S.index(w4:spawn(0, C.INF, 5, 5))
local foe = S.index(w4:spawn(1, C.INF, 6, 5))
local away = S.index(w4:spawn(1, C.INF, 9, 5))
for _, k in ipairs({mine, foe, away}) do w4.hp[k] = 40 end
local sp = CB.splash_hits(w4, 5, 5, 20)
local spd = {}
local sph = {}
for k = 0, sp.n - 1 do
    spd[sp[k][1]] = sp[k][2]
    sph[#sph + 1] = sp[k][1]
end
H.check('명중 칸의 유닛은 전액', spd[w4:handle(mine)], 20)
H.check('링 1 은 절반 — 아군도 맞는다', spd[w4:handle(foe)], 10)
H.check('링 3 밖은 목록에 없다', spd[w4:handle(away)] ~= nil, false)
local sph_sorted = {}
for k = 1, #sph do sph_sorted[k] = sph[k] end
table.sort(sph_sorted)
H.check('스플래시 목록은 핸들 오름차순', sph, sph_sorted)
H.note('아군 오사는 AI 의 제약이다 — 17부에서 박격포 사격 규칙에 쓰인다')

-- ── 란체스터의 경계 ─────────────────────────────────────────────────────────
H.check('한쪽이 0 이면 즉시 끝', (CB.lanchester_sim(0, 10, 6554, 6554)), 0)
H.check('둘 다 0', arr(CB.lanchester_sim(0, 0, 6554, 6554)), arr(0, 0, 0))
H.check('전투력이 0 이면 10000틱 상한에서 멈춘다',
        (CB.lanchester_sim(10, 10, 0, 0)), 10000)
local lt, la, lb = CB.lanchester_sim(20, 10, 6554, 6554)
H.check_true('수가 2배면 손실 없이 가깝게 이긴다 (제곱 법칙)', la >= 16 and lb == 0)
H.note('α·A² − β·B² 가 불변이므로 400−100 = 300 → √300 ≈ 17.3 이 이론값이다')

return H.done()
