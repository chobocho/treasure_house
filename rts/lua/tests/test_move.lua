-- 이동·예약·대형 (SPEC §13).
--
--    핵심은 불변식 R 이다 — 어떤 타일도 두 엔티티에게 동시에 예약되지 않는다.
--    무작위 시나리오를 오래 돌려 매 틱 확인한다.

local H = require('tests.harness')
local C = require('rts.const')
local F = require('rts.fixed')
local MV = require('rts.move')
local R = require('rts.rng')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('move')

local floor = math.floor

local function grid(rows)
    local m = T.new(#rows[1], #rows)
    for y = 0, #rows - 1 do
        local row = rows[y + 1]
        for x = 0, m.w - 1 do
            local ch = row:sub(x + 1, x + 1)
            m.terrain[y * m.w + x] = (ch == '#') and T.ROCK or T.DIRT
            m:_repass(y * m.w + x)
        end
    end
    m:_bump()
    return m
end

local function rep(s, k)
    local t = {}
    for i = 1, k do t[i] = s end
    return t
end

local function world_of(m) return S.new(m.w, m.h) end
local function pair(a, b) return {[0] = a, [1] = b, n = 2} end
local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

-- ── SPEC §13.1 걸음 진행량 ──────────────────────────────────────────────────
local sp = C.SPEED[C.INF]
local st = MV.step_amount(sp, 0)             -- 북 = 직선
local di = MV.step_amount(sp, 1)             -- 북동 = 대각
H.check('직선 진행량 = fpdiv(speed, fp(TILE))', st, F.fp_div(sp, F.fp(C.TILE)))
H.check('대각 진행량 = 직선 × FP_DIAG', di, F.fp_mul(st, F.FP_DIAG))
H.check('대각/직선 = 1/√2 (만분율)', F.floordiv(di * 10000, st), 7070)
H.note('보정을 빼면 대각이 √2 = 1.414배 빨라진다 — 41% 빠른 지그재그 버그')
H.check('네 직선 방향의 진행량이 같다',
        arr(MV.step_amount(sp, 0), MV.step_amount(sp, 2),
            MV.step_amount(sp, 4), MV.step_amount(sp, 6)),
        arr(st, st, st, st))
H.check('네 대각 방향의 진행량이 같다',
        arr(MV.step_amount(sp, 1), MV.step_amount(sp, 3),
            MV.step_amount(sp, 5), MV.step_amount(sp, 7)),
        arr(di, di, di, di))
H.check('속도 0 이면 진행량 0', MV.step_amount(0, 0), 0)

-- ── 정리 13.1 — 화면상 픽셀 속도가 방향과 무관한가 ──────────────────────────

--- 유닛 한 기를 목표까지 걷게 하고 (틱수, …) 를 돌려준다.
local function walk(rows, sx, sy, gx, gy, kind)
    kind = kind or C.INF
    local m = grid(rows)
    local w = world_of(m)
    local mv = MV.new(w, m)
    local h = w:spawn(0, kind, sx, sy)
    local i = S.index(h)
    mv:claim(i)
    mv:order(i, gx, gy)
    local t = 0
    while not (w.tx[i] == gx and w.ty[i] == gy) and t < 2000 do
        mv:step()
        t = t + 1
    end
    return t, i, w, mv
end

local t_str = walk(rep('..........', 3), 0, 1, 8, 1)
local t_dia = walk(rep('..........', 10), 0, 0, 8, 8)
-- 픽셀 거리: 직선 8타일 = 128px, 대각 8타일 = 128*√2 = 181.02px
local r_ticks = F.floordiv(t_dia * 1000, t_str)
local diff = r_ticks - 1414; if diff < 0 then diff = -diff end
H.check_true(string.format(
    '대각 8칸의 틱수/직선 8칸의 틱수 ≈ √2 (%d/1000)', r_ticks), diff <= 60)
H.note('틱은 정수라 걸음마다 최대 1틱이 남는다 — 그 오차가 위의 여유폭이다')

-- ── SPEC §13.1 화면 위치는 파생값 ───────────────────────────────────────────
local m = grid({'....', '....', '....', '....'})
local w = world_of(m)
local mv = MV.new(w, m)
local h = w:spawn(0, C.INF, 1, 1)
local i = S.index(h)
mv:claim(i)
H.check('서 있으면 타일 좌표 그대로', pair(MV.pos_of(w, m, i)),
        pair(F.fp(1 * C.TILE), F.fp(1 * C.TILE)))
w.to_t[i] = 1 * m.w + 2
w.prog[i] = F.FP_HALF
H.check('동쪽으로 절반 왔으면 x 는 한 타일의 절반',
        pair(MV.pos_of(w, m, i)), pair(F.fp(16) + F.fp(8), F.fp(16)))
w.prog[i] = F.FP_ONE
H.check('진행률 1 이면 도착 타일 위', pair(MV.pos_of(w, m, i)),
        pair(F.fp(32), F.fp(16)))
w.to_t[i] = w.from_t[i]
w.prog[i] = 0

-- ── SPEC §13.2 예약 불변식 ──────────────────────────────────────────────────
H.check('생성 시 자기 칸을 예약한다', mv.resv[1 * m.w + 1], h)
H.check('예약이 남의 것이면 실패', mv:reserve(1 * m.w + 1, h + 256), false)
H.check('제 예약을 다시 잡는 것은 성공', mv:reserve(1 * m.w + 1, h), true)
H.check('빈 칸 예약은 성공', mv:reserve(0, h), true)
mv:release(0, h)
H.check('반납하면 0', mv.resv[0], 0)
mv:release(0, h)
H.check('두 번 반납해도 조용하다', mv.resv[0], 0)

local bh = w:spawn(1, C.HQ, 2, 2)
mv:claim(S.index(bh))
H.check('건물은 발자국 9칸을 전부 예약한다',
        arr(mv.resv[2 * m.w + 2], mv.resv[2 * m.w + 3],
            mv.resv[3 * m.w + 2], mv.resv[3 * m.w + 3]),
        arr(bh, bh, bh, bh))
H.note('3x3 이지만 맵이 4x4 라 오른쪽·아래 한 줄은 맵 밖이다')

-- ── 걸음 중에는 두 칸을 쥔다 ────────────────────────────────────────────────
local function count_resv(mv_, h_)
    local c = 0
    for k = 0, mv_.resv.n - 1 do
        if mv_.resv[k] == h_ then c = c + 1 end
    end
    return c
end

m = grid({'.....', '.....', '.....'})
w = world_of(m)
mv = MV.new(w, m)
h = w:spawn(0, C.INF, 0, 1)
i = S.index(h)
mv:claim(i)
mv:order(i, 4, 1)
mv:step()
H.check('걸음을 시작하면 두 칸', count_resv(mv, h), 2)
H.check('진행 중 tx 는 아직 출발 타일', pair(w.tx[i], w.ty[i]), pair(0, 1))
while w.prog[i] ~= 0 do mv:step() end
H.check('걸음이 끝나면 다시 한 칸', count_resv(mv, h), 1)
H.check('타일이 넘어갔다', pair(w.tx[i], w.ty[i]), pair(1, 1))
H.check('넘은 사실이 crossed 에 남는다 — sim 7단계의 시야 갱신이 이것만 본다',
        mv.crossed, {[0] = {i, 1 * m.w + 0, 1 * m.w + 1}, n = 1})
mv:step()
H.check('crossed 는 매 틱 비운다', mv.crossed, {n = 0})

-- ── 무작위 시나리오에서 불변식 R 을 매 틱 확인 ──────────────────────────────
local ROWS = {
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
}
m = grid(ROWS)
w = world_of(m)
mv = MV.new(w, m)
local rand = R.new(7)
local free = {n = 0}
for j = 0, m.w * m.h - 1 do
    if m:passable_terrain(j % m.w, floor(j / m.w), 0) then
        free[free.n] = j
        free.n = free.n + 1
    end
end
local units = {n = 0}
for k = 0, 23 do
    local j
    while true do
        j = free[rand:roll(free.n)]
        if mv.resv[j] == 0 then break end
    end
    local kind = (k % 2 == 1) and C.INF or C.TANK
    local hh = w:spawn(rand:roll(2), kind, j % m.w, floor(j / m.w))
    mv:claim(S.index(hh))
    units[units.n] = S.index(hh)
    units.n = units.n + 1
end
local start_pos = {}
for k = 0, units.n - 1 do
    local u = units[k]
    start_pos[u] = {w.tx[u], w.ty[u]}
end
local viol, overlap, selfown = 0, 0, 0
for tick = 0, 599 do
    if tick % 50 == 0 then
        for k = 0, units.n - 1 do
            local j = free[rand:roll(free.n)]
            mv:order(units[k], j % m.w, floor(j / m.w))
        end
    end
    mv:step()
    local seen = {}
    for k = 0, units.n - 1 do
        local u = units[k]
        local hh = w:handle(u)
        for _, tile in ipairs({w.from_t[u], w.to_t[u]}) do
            if mv.resv[tile] ~= hh then selfown = selfown + 1 end
            if seen[tile] ~= nil and seen[tile] ~= u then viol = viol + 1 end
            seen[tile] = u
        end
    end
    local occ = {}
    local dup = false
    for k = 0, units.n - 1 do
        local u = units[k]
        local tile = w.ty[u] * m.w + w.tx[u]
        if occ[tile] then dup = true end
        occ[tile] = true
    end
    if dup then overlap = overlap + 1 end
end
H.check('불변식 R — 600틱 동안 한 칸을 둘이 예약한 적', viol, 0)
H.check('제가 선 칸은 늘 제 예약이다', selfown, 0)
H.check('두 유닛이 같은 타일에 선 적', overlap, 0)
local movedn = 0
for k = 0, units.n - 1 do
    local u = units[k]
    if w.tx[u] ~= start_pos[u][1] or w.ty[u] ~= start_pos[u][2] then
        movedn = movedn + 1
    end
end
H.check_true('24기 중 20기 이상이 실제로 자리를 옮겼다', movedn >= 20)
local nresv, nwalk = 0, 0
for k = 0, mv.resv.n - 1 do
    if mv.resv[k] ~= 0 then nresv = nresv + 1 end
end
for k = 0, units.n - 1 do
    if w.prog[units[k]] > 0 then nwalk = nwalk + 1 end
end
H.check('예약 수 == 서 있는 칸 + 걷는 중인 칸', nresv, units.n + nwalk)

-- ── SPEC §13.3 막힘과 교착 ──────────────────────────────────────────────────
m = grid({'#####', '.....', '#####'})        -- 폭 1 통로
w = world_of(m)
mv = MV.new(w, m)
local ha = w:spawn(0, C.INF, 0, 1)
local hb = w:spawn(1, C.INF, 4, 1)           -- 다른 플레이어 — 밀어내지 않는다
local ia, ib = S.index(ha), S.index(hb)
mv:claim(ia)
mv:claim(ib)
mv:order(ia, 4, 1)
mv:order(ib, 0, 1)
local repn, give = 0, 0
for t = 0, 399 do
    mv:step()
    if mv.blocked[ia] == MV.REPATH_TICKS then repn = repn + 1 end
    if mv.goal[ia] < 0 and give == 0 then give = t end
end
H.check_true(string.format('좁은 통로에서 마주 오면 %d틱에 포기한다 (교착 해소)',
                           give), give > 0)
H.check_true('포기 전에 재탐색을 시도한다', repn > 0)
H.check('포기하면 경로도 비운다', mv.path[ia], {n = 0})
H.note('이것은 해결이 아니라 포기다 — 협상 기반 재배치는 이 엔진 밖이다')

-- ── 밀어내기: 정지한 아군은 비켜 준다 ───────────────────────────────────────
m = grid({'.....', '.....', '.....'})
w = world_of(m)
mv = MV.new(w, m)
ha = w:spawn(0, C.INF, 0, 1)
hb = w:spawn(0, C.INF, 1, 1)                 -- 같은 플레이어, 정지 상태
ia, ib = S.index(ha), S.index(hb)
mv:claim(ia)
mv:claim(ib)
mv:order(ia, 4, 1)
H.check('진행 방향(E)의 반대 W 부터 시계로 훑는다 — W 는 밀 유닛이 쥐었으니 NW(7)',
        MV.push_dir(mv, ib, 2), 7)
for _ = 0, 59 do
    mv:step()
    if not (w.tx[ib] == 1 and w.ty[ib] == 1) then break end
end
H.check_true('정지한 아군은 밀려난다', not (w.tx[ib] == 1 and w.ty[ib] == 1))
H.check('밀려간 칸은 NW', pair(w.tx[ib], w.ty[ib]), pair(0, 0))
H.note('훑는 순서 = 반대 방향에서 시계 방향 — 세 언어가 같은 칸을 골라야 한다')

-- ── SPEC §13.4 도착 반경 ────────────────────────────────────────────────────
m = grid({'.....', '.....', '.....'})
w = world_of(m)
mv = MV.new(w, m)
hb = w:spawn(0, C.INF, 4, 1)
ha = w:spawn(0, C.INF, 0, 1)
ia, ib = S.index(ha), S.index(hb)
mv:claim(ib)
mv:claim(ia)
mv:order(ia, 4, 1)                           -- 목표 칸은 이미 점유되어 있다
local tlast = 0
for t = 0, 299 do
    tlast = t
    mv:step()
    if mv.goal[ia] < 0 then break end
end
H.check_true(string.format('목표가 점유되어 있어도 %d타일 안이면 도착으로 친다',
                           MV.ARRIVE_R),
             F.dinf(w.tx[ia] - 4, w.ty[ia] - 1) <= MV.ARRIVE_R)
H.check('도착하면 경로를 비운다', mv.path[ia], {n = 0})
H.check_true('영원히 두드리지 않는다', tlast < 299)

-- ── SPEC §13.5 rot8 ─────────────────────────────────────────────────────────
H.check('rot8(0) 은 항등', pair(MV.rot8(0, 3, 1)), pair(3, 1))
H.check('rot8(2) = (-oy, ox)', pair(MV.rot8(2, 3, 1)), pair(-1, 3))
H.check('rot8(4) = (-ox, -oy)', pair(MV.rot8(4, 3, 1)), pair(-3, -1))
H.check('rot8(6) = (oy, -ox)', pair(MV.rot8(6, 3, 1)), pair(1, -3))
H.check('rot8(1) = 이웃 둘의 평균 (내림)', pair(MV.rot8(1, 3, 1)),
        pair(F.floordiv(3 + -1, 2), F.floordiv(1 + 3, 2)))
H.check('rot8(7) = 0 과 6 의 평균', pair(MV.rot8(7, 3, 1)),
        pair(F.floordiv(3 + 1, 2), F.floordiv(1 + -3, 2)))
local origins = {n = 8}
local zeros8 = {n = 8}
for d = 0, 7 do
    origins[d] = pair(MV.rot8(d, 0, 0))
    zeros8[d] = pair(0, 0)
end
H.check('원점은 어떤 회전에도 원점', origins, zeros8)

-- ── SPEC §13.5 대형 ─────────────────────────────────────────────────────────
m = grid(rep(string.rep('.', 16), 16))
local box = MV.formation(9, MV.BOX, 0, 8, 8, m, 0)
H.check('n=9 BOX 는 3×3, 슬롯 9개', box.n, 9)
H.check('BOX 첫 줄은 목표의 x-1..x+1', arr(box[0], box[1], box[2]),
        arr(pair(7, 8), pair(8, 8), pair(9, 8)))
H.check('BOX 둘째 줄은 한 칸 아래', arr(box[3], box[4], box[5]),
        arr(pair(7, 9), pair(8, 9), pair(9, 9)))
H.check('n=1 이면 목표 한 칸', MV.formation(1, MV.BOX, 0, 8, 8, m, 0),
        arr(pair(8, 8)))
H.check('n=0 이면 빈 목록', MV.formation(0, MV.BOX, 0, 8, 8, m, 0), {n = 0})
local f5 = MV.formation(5, MV.BOX, 0, 8, 8, m, 0)
local xs = {}
local nxs = 0
for k = 0, f5.n - 1 do
    if not xs[f5[k][0]] then xs[f5[k][0]] = true; nxs = nxs + 1 end
end
H.check('n=5 BOX 의 한 변은 3', nxs, 3)
local line = MV.formation(4, MV.LINE, 0, 8, 8, m, 0)
local ys = {}
local nys = 0
for k = 0, line.n - 1 do
    if not ys[line[k][1]] then ys[line[k][1]] = true; nys = nys + 1 end
end
H.check('LINE 은 한 줄', arr(nys, line[0][1]), arr(1, 8))
H.check('LINE 은 가운데 정렬', line,
        arr(pair(7, 8), pair(8, 8), pair(9, 8), pair(10, 8)))
local col = MV.formation(3, MV.COLUMN, 0, 8, 8, m, 0)
H.check('COLUMN 은 진행 방향으로 한 줄', col,
        arr(pair(8, 8), pair(8, 9), pair(8, 10)))
H.check('COLUMN 을 동쪽(2)으로 돌리면 x 로 늘어선다',
        MV.formation(3, MV.COLUMN, 2, 8, 8, m, 0),
        arr(pair(8, 8), pair(7, 8), pair(6, 8)))
local edge = MV.formation(9, MV.BOX, 0, 0, 0, m, 0)
local cnt00 = 0
for k = 0, edge.n - 1 do
    if edge[k][0] == 0 and edge[k][1] == 0 then cnt00 = cnt00 + 1 end
end
H.check_true('맵 밖 슬롯은 목표 타일로 접는다', cnt00 > 1)
local blocked = grid(rep('.....', 5))
blocked:set_terrain(4, 2, T.ROCK)
H.check('막힌 슬롯은 목표 타일로 접는다',
        MV.formation(3, MV.LINE, 0, 3, 2, blocked, 0),
        arr(pair(2, 2), pair(3, 2), pair(3, 2)))

-- ── 경계 조건 ───────────────────────────────────────────────────────────────
m = grid({'..#..', '..#..', '..#..'})
w = world_of(m)
mv = MV.new(w, m)
h = w:spawn(0, C.INF, 0, 1)
i = S.index(h)
mv:claim(i)
H.check('닿을 수 없는 목표는 §8.6 의 대체 목표로 바뀐다', mv:order(i, 4, 1), true)
H.check_true('대체 목표는 벽 앞이다', mv.goal[i] % m.w <= 1)
H.check('이미 서 있는 칸으로의 명령은 즉시 도착', mv:order(i, 0, 1), true)
H.check('그 경우 경로는 비어 있다', mv.path[i], {n = 0})
H.check('맵 밖 명령은 거부', mv:order(i, -1, 1), false)
mv:order(i, 1, 1)
mv:stop(i)
H.check('STOP 은 아직 시작하지 않은 걸음의 예약만 반납한다', count_resv(mv, h), 1)
H.check('STOP 은 경로와 목표를 비운다',
        {[0] = mv.path[i], [1] = mv.goal[i], n = 2},
        {[0] = {n = 0}, [1] = -1, n = 2})
mv:order(i, 1, 1)
mv:step()
mv:stop(i)
H.check_true('걸음 도중의 STOP 은 두 칸을 쥔 채로 걸음을 마친다',
             count_resv(mv, h) == 2)
while w.prog[i] ~= 0 do mv:step() end
H.check('마친 뒤에는 한 칸', count_resv(mv, h), 1)
H.check('그리고 멈춰 있다', mv.path[i], {n = 0})

return H.done()
