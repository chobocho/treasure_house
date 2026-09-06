-- 화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).

local H = require('tests.harness')
local C = require('rts.const')
local RS = require('rts.raster')
local RD = require('rts.render')
local SIM = require('rts.sim')
local S = require('rts.spatial')
local T = require('rts.tmap')

H.title('render')

local floor = math.floor
local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local PAL = RS.build_palette()
local LIGHT = RS.build_light(PAL)

local function start_sim()
    local m = T.load_text(H.golden('map_start.txt'))
    local s = SIM.new(m, 1, 2)
    s:setup_start()
    return s
end

-- ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
local m = T.load_text(H.golden('map_start.txt'))
local v = RD.newview()
H.check('처음 카메라는 (0,0)', lst(v.cam_x, v.cam_y), lst(0, 0))
v:move(m, -100, -100)
H.check('왼쪽 위로 넘어가지 않는다', lst(v.cam_x, v.cam_y), lst(0, 0))
v:move(m, 10000, 10000)
H.check('오른쪽 아래 한계는 맵 - 뷰포트', lst(v.cam_x, v.cam_y),
        lst(C.MAP_W * C.TILE - C.VIEW_W, C.MAP_H * C.TILE - C.VIEW_H))
H.check('그 값은 768', v.cam_x, 768)
local v2 = RD.newview()
v2:center_on(m, 32, 32)
H.check('가운데 정렬', lst(v2.cam_x, v2.cam_y),
        lst(32 * 16 - floor(C.VIEW_W / 2), 32 * 16 - floor(C.VIEW_H / 2)))
v2:center_on(m, 0, 0)
H.check('가장자리에서는 클램프', lst(v2.cam_x, v2.cam_y), lst(0, 0))
H.check('카메라는 정수 픽셀', v2.cam_x == floor(v2.cam_x), true)

local v3 = RD.newview()
v3.cam_x, v3.cam_y = 100, 50
H.check('첫 타일과 오프셋', lst(v3:first_tile()), lst(6, 3, 4, 2))
H.check('그릴 타일 수는 17열', RD.TILES_X, floor(C.VIEW_W / C.TILE) + 1)
H.check('가장자리 스크롤 — 왼쪽 8px 안', lst(RD.edge_scroll(3, 100)),
        lst(-RD.EDGE_SPEED, 0))
H.check('오른쪽', lst(RD.edge_scroll(C.VIEW_W - 2, 100)), lst(RD.EDGE_SPEED, 0))
H.check('위', lst(RD.edge_scroll(100, 2)), lst(0, -RD.EDGE_SPEED))
H.check('가운데는 안 움직인다', lst(RD.edge_scroll(100, 100)), lst(0, 0))
H.check('패널 위에서는 안 움직인다', lst(RD.edge_scroll(300, 100)), lst(0, 0))

-- ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
local s = start_sim()
local order = RD.y_order(s.w)
local keys = {n = order.n}
for k = 0, order.n - 1 do keys[k] = RD.sort_key(s.w, order[k]) end
local function key_lt(p, q)
    for k = 0, 2 do
        if p[k] ~= q[k] then return p[k] < q[k] end
    end
    return false
end
local sorted_keys = {}
for k = 0, keys.n - 1 do sorted_keys[k + 1] = keys[k] end
table.sort(sorted_keys, key_lt)
local sk0 = {n = keys.n}
for k = 0, keys.n - 1 do sk0[k] = sorted_keys[k + 1] end
H.check('발밑 y · x · 핸들 순', keys, sk0)
local nalive = 0
for i = 1, C.MAX_ENT - 1 do
    if s.w.alive[i] ~= 0 then nalive = nalive + 1 end
end
H.check('살아 있는 것만', order.n, nalive)
local byorder = {}
for k = 0, order.n - 1 do byorder[k + 1] = order[k] end
table.sort(byorder, function(p, q)
    return key_lt(RD.sort_key(s.w, p), RD.sort_key(s.w, q))
end)
local bo0 = {n = order.n}
for k = 0, order.n - 1 do bo0[k] = byorder[k + 1] end
H.check('삽입 정렬이 표준 정렬과 같은 답을 낸다', order, bo0)
local seenk, nseen = {}, 0
for k = 0, keys.n - 1 do
    local kk = keys[k][0] .. ',' .. keys[k][1] .. ',' .. keys[k][2]
    if not seenk[kk] then seenk[kk] = true; nseen = nseen + 1 end
end
H.check('키는 전순서 — 같은 키가 둘일 수 없다', nseen, keys.n)

-- ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
H.check('64 맵을 64 픽셀에 — 한 타일이 한 픽셀', RD.minimap_nearest(m, 10, 20),
        m.terrain[20 * m.w + 10])
H.check('축소 코드도 있다 (128 맵을 대비)', RD.minimap_nearest(m, 0, 0),
        m.terrain[0])
local maj = RD.minimap_majority(m, 5, 5)
H.check_true('다수결도 같은 크기에서는 같은 답',
             maj == RD.minimap_nearest(m, 5, 5))
H.check('미니맵 클릭의 역변환', lst(RD.minimap_to_tile(32, 48)), lst(32, 48))
local vv = RD.newview()
local mtx, mty = RD.minimap_to_tile(32, 32)
vv:center_on(m, mtx, mty)
H.check('클릭한 타일이 뷰포트 중앙에 온다',
        lst(vv.cam_x + floor(C.VIEW_W / 2), vv.cam_y + floor(C.VIEW_H / 2)),
        lst(32 * 16, 32 * 16))

-- ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
local fb = RS.newframe()
RD.draw(fb.fb, s, RD.newview(), 0, PAL, LIGHT, 0, {n = 0}, '')
local nzero = 0
for i = 0, fb.fb.n - 1 do
    if fb.fb[i] == 0 then nzero = nzero + 1 end
end
H.check('프레임버퍼를 다 채운다', nzero < 320 * 200, true)
local mxp = 0
for x = C.PANEL_X, 319 do
    if fb.fb[10 * 320 + x] > mxp then mxp = fb.fb[10 * 320 + x] end
end
H.check('패널 영역에도 그린다', mxp > 0, true)
local mxb = 0
for x = 0, 255 do
    local vch = fb.fb[(C.BAR_Y + 10) * 320 + x]
    if vch > mxb then mxb = vch end
end
H.check('하단 바에도 그린다', mxb > 0, true)

local fb2 = RS.newframe()
RD.draw(fb2.fb, s, RD.newview(), 0, PAL, LIGHT, 0, {n = 0}, '')
H.check('같은 상태면 같은 그림', fb.fb, fb2.fb)
local ppm = RS.to_ppm(fb.fb, PAL)
H.check('PPM 192,015바이트', #ppm, 192015)

-- ── 안개 ────────────────────────────────────────────────────────────────────
local view = RD.newview()
view:center_on(m, 8, 8)                      -- 0번 기지
local litf = RS.newframe()
RD.draw(litf.fb, s, view, 0, PAL, LIGHT, 0, {n = 0}, '')
local darkf = RS.newframe()
RD.draw(darkf.fb, s, view, 0, PAL, LIGHT, 1, {n = 0}, '')  -- 1번 시야로 같은 곳
local function count_zero(a, lim)
    local c = 0
    for i = 0, lim - 1 do
        if a[i] == 0 then c = c + 1 end
    end
    return c
end
H.check_true('남의 시야로 보면 어둡다',
             count_zero(darkf.fb, C.VIEW_H * 320)
             > count_zero(litf.fb, C.VIEW_H * 320))
H.check('미탐험은 완전한 검정', darkf.fb[10 * 320 + 10], 0)

local enemy_visible = RD.visible_entities(s, 1)
local mine_seen = {n = 0}
for k = 0, enemy_visible.n - 1 do
    if s.w.owner[enemy_visible[k]] == 0 then
        mine_seen[mine_seen.n] = enemy_visible[k]
        mine_seen.n = mine_seen.n + 1
    end
end
H.check('1번 플레이어는 0번 유닛을 못 본다', mine_seen, {n = 0})
local own = RD.visible_entities(s, 0)
H.check_true('제 유닛은 본다', own.n > 0)
H.note('명암표는 어둡게 만들 뿐이라 유닛 숨기기는 2단계에서 걸러야 한다')

-- ── 선택 표시와 체력바 ──────────────────────────────────────────────────────
local hq
for i = 1, C.MAX_ENT - 1 do
    if s.w.alive[i] ~= 0 and s.w.owner[i] == 0 and s.w.kind[i] == C.HQ then
        hq = i
        break
    end
end
local fb3 = RS.newframe()
RD.draw(fb3.fb, s, view, 0, PAL, LIGHT, 0, lst(s.w:handle(hq)), '')
H.check_true('선택하면 그림이 달라진다', not H.deep_eq(fb3.fb, litf.fb))
s.w.hp[hq] = floor(C.HP[C.HQ] / 2)
local fb4 = RS.newframe()
RD.draw(fb4.fb, s, view, 0, PAL, LIGHT, 0, lst(s.w:handle(hq)), '')
H.check_true('체력이 줄면 체력바도 달라진다', not H.deep_eq(fb4.fb, fb3.fb))

-- ── 하단 바 ─────────────────────────────────────────────────────────────────
local fb5 = RS.newframe()
RD.draw(fb5.fb, s, view, 0, PAL, LIGHT, 0, {n = 0}, 'BASE UNDER ATTACK')
local bar_same = true
for i = C.BAR_Y * 320, 320 * 200 - 1 do
    if fb5.fb[i] ~= fb.fb[i] then bar_same = false; break end
end
H.check_true('메시지를 쓰면 하단 바가 달라진다', not bar_same)
H.check('자릿수는 고정 폭', RD.credits_text(50), '   50')
H.check('큰 수도 다섯 자리', RD.credits_text(12345), '12345')
H.check('넘치면 잘라 붙인다', RD.credits_text(1234567), '99999')

-- ── 팔레트 사이클은 그림을 바꾸지 않는다 (팔레트만 바뀐다) ──────────────────
local fb6 = RS.newframe()
local fb7 = RS.newframe()
RD.draw(fb6.fb, s, view, 0, PAL, LIGHT, 0, {n = 0}, '')
RD.draw(fb7.fb, s, view, 3, PAL, LIGHT, 0, {n = 0}, '')
H.check('사이클 위상은 프레임버퍼를 바꾸지 않는다', fb7.fb, fb6.fb)
H.note('물 애니메이션은 팔레트만 돌린다 — 그래서 공짜다')

return H.done()
