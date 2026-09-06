-- 선택과 명령 — 픽킹·상자 선택·컨트롤 그룹·명령 큐 (SPEC §12).

local H = require('tests.harness')
local C = require('rts.const')
local E = require('rts.econ')
local SEL = require('rts.select')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('select')

local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
local function cam(x, y) return {[0] = x, [1] = y, n = 2} end

local function grid(rows)
    local m = T.new(#rows[1], #rows)
    for y = 0, #rows - 1 do
        local row = rows[y + 1]
        for x = 0, m.w - 1 do
            local ch = row:sub(x + 1, x + 1)
            m.terrain[y * m.w + x] = T.TERRAIN_CH:find(ch, 1, true) - 1
            m:_repass(y * m.w + x)
        end
    end
    m:_bump()
    return m
end

-- ── SPEC §12.1 뷰포트와 좌표 ────────────────────────────────────────────────
H.check('뷰포트 안', SEL.in_view(0, 0), true)
H.check('뷰포트 오른쪽 끝', SEL.in_view(C.VIEW_W - 1, C.VIEW_H - 1), true)
H.check('패널은 뷰포트가 아니다', SEL.in_view(C.VIEW_W, 10), false)
H.check('하단 바도 아니다', SEL.in_view(10, C.VIEW_H), false)
H.check('음수도 아니다', SEL.in_view(-1, 0), false)
H.check('카메라를 더해 월드 좌표로',
        arr(SEL.screen_to_world(cam(32, 48), 10, 20)), arr(42, 68))
H.check('카메라 0 이면 그대로',
        arr(SEL.screen_to_world(cam(0, 0), 5, 7)), arr(5, 7))

-- ── SPEC §12.1 픽킹 ─────────────────────────────────────────────────────────
local w = S.new(32, 32)
local a = S.index(w:spawn(0, C.INF, 2, 2))    -- 월드 (32,32)-(48,48)
local b = S.index(w:spawn(0, C.INF, 2, 3))    -- 아래쪽 — 앞에 그려진다
for _, k in ipairs({a, b}) do w.hp[k] = 40 end
H.check('빈 곳을 찍으면 0', SEL.pick(w, cam(0, 0), 200, 100), 0)
H.check('유닛 위를 찍으면 그 핸들', SEL.pick(w, cam(0, 0), 36, 36), w:handle(a))
H.check('아래쪽 유닛', SEL.pick(w, cam(0, 0), 36, 52), w:handle(b))
H.check('카메라가 움직이면 화면 좌표도 움직인다',
        SEL.pick(w, cam(32, 32), 4, 4), w:handle(a))
H.check('뷰포트 밖은 픽킹하지 않는다', SEL.pick(w, cam(0, 0), 300, 36), 0)

local over = S.index(w:spawn(0, C.TANK, 2, 3))   -- b 와 같은 칸, 핸들이 더 크다
w.hp[over] = 90
H.check('겹치면 y 내림차순 → 동점이면 핸들 내림차순 (뒤에 만든 것이 위)',
        SEL.pick(w, cam(0, 0), 36, 52), w:handle(over))
H.check('y 가 큰 쪽이 먼저다', SEL.pick(w, cam(0, 0), 36, 36), w:handle(a))

--- 가운데 8×8 만 불투명한 가짜 알파 마스크.
local function mask(kind, d, lx, ly)
    return lx >= 4 and lx < 12 and ly >= 4 and ly < 12
end

H.check('마스크를 통과해야 잡힌다', SEL.pick(w, cam(0, 0), 40, 40, mask),
        w:handle(a))
H.check('AABB 안이어도 마스크 밖이면 지나친다',
        SEL.pick(w, cam(0, 0), 33, 33, mask), 0)
H.note('AABB 만으로 끝내지 않는 이유는 유닛이 사각형이 아니기 때문이다')

-- ── SPEC §12.2 상자 선택 ────────────────────────────────────────────────────
local w2 = S.new(32, 32)
local mine = {}
for k = 0, 2 do mine[k] = S.index(w2:spawn(0, C.INF, 2 + k, 2)) end
local foe = S.index(w2:spawn(1, C.INF, 3, 2))
local bld = S.index(w2:spawn(0, C.HQ, 2, 4))
for _, k in ipairs({mine[0], mine[1], mine[2], foe, bld}) do w2.hp[k] = 100 end
local sel = SEL.box_select(w2, 0, cam(0, 0), 30, 30, 90, 60)
H.check('내 유닛만 (남의 유닛과 건물은 빠진다)', sel,
        arr(w2:handle(mine[0]), w2:handle(mine[1]), w2:handle(mine[2])))
local sorted_sel = {}
for k = 0, sel.n - 1 do sorted_sel[k + 1] = sel[k] end
table.sort(sorted_sel)
local sel_sorted0 = {n = sel.n}
for k = 0, sel.n - 1 do sel_sorted0[k] = sorted_sel[k + 1] end
H.check('핸들 오름차순', sel, sel_sorted0)
H.check('상자가 비면 빈 목록',
        SEL.box_select(w2, 0, cam(0, 0), 300, 300, 310, 310), {n = 0})
H.check('내 유닛이 하나도 없으면 내 건물을 고른다',
        SEL.box_select(w2, 0, cam(0, 0), 30, 60, 90, 100), arr(w2:handle(bld)))
H.check('남의 것만 있으면 빈 목록',
        SEL.box_select(w2, 1, cam(0, 0), 30, 60, 90, 100), {n = 0})
H.check('한 점 드래그도 AABB 교차로 다룬다',
        SEL.box_select(w2, 0, cam(0, 0), 36, 36, 36, 36),
        arr(w2:handle(mine[0])))
H.check('좌표가 뒤집혀 들어와도 정규화한다',
        SEL.box_select(w2, 0, cam(0, 0), 90, 60, 30, 30),
        arr(w2:handle(mine[0]), w2:handle(mine[1]), w2:handle(mine[2])))

local w3 = S.new(32, 32)
for k = 0, 39 do
    local i = S.index(w3:spawn(0, C.INF, k % 16, math.floor(k / 16)))
    w3.hp[i] = 40
end
local big = SEL.box_select(w3, 0, cam(0, 0), 0, 0, 255, 175)
H.check('한 번에 32기 상한 (이 덱의 규칙)', big.n, SEL.SELECT_MAX)
local allh = {}
for i = 1, C.MAX_ENT - 1 do
    if w3.alive[i] ~= 0 then allh[#allh + 1] = w3:handle(i) end
end
table.sort(allh)
local want32 = {n = SEL.SELECT_MAX}
for k = 0, SEL.SELECT_MAX - 1 do want32[k] = allh[k + 1] end
H.check('상한을 넘으면 핸들이 작은 쪽부터', big, want32)

-- ── SPEC §12.3 컨트롤 그룹 ──────────────────────────────────────────────────
local gr = SEL.newgroups()
gr:set(3, sel)
H.check('저장한 그대로 불러온다', gr:recall(w2, 3), sel)
H.check('빈 그룹', gr:recall(w2, 7), {n = 0})
w2:kill(sel[0])
local rest = {n = sel.n - 1}
for k = 1, sel.n - 1 do rest[k - 1] = sel[k] end
H.check('죽은 유닛은 valid 에서 걸러진다', gr:recall(w2, 3), rest)
H.check('그룹은 0..9', gr.g.n, 10)
gr:set(3, {n = 0})
H.check('빈 선택을 저장하면 그룹도 빈다', gr:recall(w2, 3), {n = 0})

-- ── SPEC §12.4 명령 큐 ──────────────────────────────────────────────────────
local q = SEL.neworders()
local i = mine[1]
q:push(i, arr(SEL.MOVE, 5, 5, 0), false)
H.check('기본 클릭은 큐를 비우고 하나', q.q[i], {[0] = arr(SEL.MOVE, 5, 5, 0), n = 1})
q:push(i, arr(SEL.MOVE, 6, 6, 0), true)
H.check('시프트 클릭은 뒤에 붙인다', q.q[i].n, 2)
q:push(i, arr(SEL.MOVE, 7, 7, 0), false)
H.check('시프트가 없으면 다시 하나', q.q[i], {[0] = arr(SEL.MOVE, 7, 7, 0), n = 1})
for k = 0, 19 do
    q:push(i, arr(SEL.MOVE, k, 0, 0), true)
end
H.check('큐 상한은 8', q.q[i].n, SEL.ORDER_MAX)
H.check('상한을 넘으면 뒤를 버린다', q.q[i][0], arr(SEL.MOVE, 7, 7, 0))
H.check('꺼내면 앞에서', q:pop(i), arr(SEL.MOVE, 7, 7, 0))
H.check('꺼낸 만큼 준다', q.q[i].n, SEL.ORDER_MAX - 1)
q:push(i, arr(SEL.STOP, 0, 0, 0), true)
H.check('STOP 은 큐를 비운다', q.q[i], {n = 0})
H.check('빈 큐에서 꺼내면 None', q:pop(i), nil)
local kinds = {SEL.MOVE, SEL.ATTACK, SEL.ATTACK_MOVE, SEL.HARVEST,
               SEL.BUILD, SEL.STOP, SEL.HOLD, SEL.TRAIN}
table.sort(kinds)
local kinds0 = {n = 8}
for k = 0, 7 do kinds0[k] = kinds[k + 1] end
H.check('명령 종류는 여덟 — TRAIN 만 건물에게 내린다', kinds0,
        arr(0, 1, 2, 3, 4, 5, 6, 7))

-- ── SPEC §12.4 우클릭 문맥 규칙 ─────────────────────────────────────────────
local m = grid({'.....', '..*..', '.....', '.....', '.....'})
local w4 = S.new(5, 5)
local ec = E.new(m)
local me = S.index(w4:spawn(0, C.INF, 0, 0))
local enemy = S.index(w4:spawn(1, C.INF, 4, 4))
local ref = S.index(w4:spawn(0, C.REF, 3, 0))
local barr = S.index(w4:spawn(0, C.BARR, 0, 3))
for _, k in ipairs({me, enemy, ref, barr}) do w4.hp[k] = 100 end
H.check('적이면 ATTACK',
        SEL.context_order(w4, ec, m, 0, 4, 4, w4:handle(enemy)), SEL.ATTACK)
H.check('자원이면 HARVEST', SEL.context_order(w4, ec, m, 0, 2, 1, 0), SEL.HARVEST)
H.check('내 정제소면 HARVEST (반납)',
        SEL.context_order(w4, ec, m, 0, 3, 0, w4:handle(ref)), SEL.HARVEST)
H.check('내 병영이면 그냥 MOVE',
        SEL.context_order(w4, ec, m, 0, 0, 3, w4:handle(barr)), SEL.MOVE)
H.check('빈 땅이면 MOVE', SEL.context_order(w4, ec, m, 0, 1, 1, 0), SEL.MOVE)
H.check('내 유닛이면 MOVE',
        SEL.context_order(w4, ec, m, 0, 0, 0, w4:handle(me)), SEL.MOVE)
H.check('죽은 핸들은 없는 것으로 친다',
        SEL.context_order(w4, ec, m, 0, 4, 4, 999999), SEL.MOVE)
ec:mine(m, 1 * 5 + 2, 9999)
H.check('다 캔 광맥은 MOVE', SEL.context_order(w4, ec, m, 0, 2, 1, 0), SEL.MOVE)

-- ── SPEC §12.5 명령은 틱 경계에서만 ─────────────────────────────────────────
H.check('명령 지연은 상수다', C.ORDER_DELAY, 2)
H.note('UI 가 sim 의 상태를 직접 건드리는 경로는 존재하지 않는다 — 락스텝의 전제다')

return H.done()
