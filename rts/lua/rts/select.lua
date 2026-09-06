-- 선택과 명령 — 픽킹·상자 선택·컨트롤 그룹·명령 큐 (SPEC §12).
--
--    이 모듈은 **상태를 바꾸지 않는다.** 명령을 만들어 큐에 넣을 뿐이고, 그 큐는
--    net(§19)의 지연 큐를 거쳐 ORDER_DELAY 틱 뒤에 sim.step 의 인자로 들어간다.
--    UI 코드가 sim 의 상태를 직접 건드리는 경로는 존재하지 않는다 — 이 규율
--    하나가 락스텝을 가능하게 한다.

local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local S = require('rts.spatial')

local M = {}

-- TRAIN 만 유닛이 아니라 건물에게 내리는 명령이다 — UI·AI·스크립트가 모두 같은
-- 자료형으로 sim.step 에 들어와야 락스텝이 성립한다(§12.4).
M.MOVE, M.ATTACK, M.ATTACK_MOVE, M.HARVEST = 0, 1, 2, 3
M.BUILD, M.STOP, M.HOLD, M.TRAIN = 4, 5, 6, 7
local STOP = 5

M.ORDER_MAX = 8                  -- §12.4 유닛당 명령 큐 상한
M.SELECT_MAX = 32                -- §12.2 한 번에 고를 수 있는 유닛 수
M.PICK_R = 2                     -- §12.1 버킷 질의 반경 (타일)
local ORDER_MAX, SELECT_MAX, PICK_R = 8, 32, 2

--- 전장 뷰포트 안인가. 밖이면 패널·미니맵 처리로 넘어간다.
function M.in_view(sx, sy)
    return sx >= C.VIEW_X and sx < C.VIEW_X + C.VIEW_W
           and sy >= C.VIEW_Y and sy < C.VIEW_Y + C.VIEW_H
end

--- cam 은 {[0]=x, [1]=y} 다.
function M.screen_to_world(cam, sx, sy)
    return sx - C.VIEW_X + cam[0], sy - C.VIEW_Y + cam[1]
end

--- 엔티티의 월드 픽셀 AABB. px·py 는 이동 중에도 정확하다(§13.1).
local function box(w, i)
    local size = C.TILE * C.FOOT[w.kind[i]]
    local x0 = F.fp_floor(w.px[i])
    local y0 = F.fp_floor(w.py[i])
    return x0, y0, x0 + size, y0 + size
end
M._box = box

-- ── SPEC §12.1 픽킹 ─────────────────────────────────────────────────────────

--- 한 점이 가리키는 엔티티 핸들. 없으면 0.
--
--    앞에 그려진 것이 먼저 잡혀야 하므로 y 내림차순, 동점이면 핸들 내림차순으로
--    훑는다 — §23.3 의 그리기 순서를 거꾸로 도는 것이다. `mask(kind, dir, lx, ly)`
--    는 스프라이트 알파 마스크다. AABB 만으로 끝내지 않는 이유는 유닛이
--    사각형이 아니기 때문이다.
function M.pick(w, cam, sx, sy, mask)
    if not M.in_view(sx, sy) then
        return 0
    end
    local wx, wy = M.screen_to_world(cam, sx, sy)
    local cands = w:query(F.floordiv(wx, C.TILE), F.floordiv(wy, C.TILE), PICK_R)
    local order = {}
    for k = 0, cands.n - 1 do order[k + 1] = cands[k] end
    table.sort(order, function(i, j)
        if w.py[i] ~= w.py[j] then return w.py[i] > w.py[j] end
        return w:handle(i) > w:handle(j)
    end)
    for k = 1, #order do
        local i = order[k]
        local x0, y0, x1, y1 = box(w, i)
        if wx >= x0 and wx < x1 and wy >= y0 and wy < y1 then
            if mask == nil or mask(w.kind[i], w.dir[i], wx - x0, wy - y0) then
                return w:handle(i)
            end
        end
    end
    return 0
end

-- ── SPEC §12.2 상자 선택 ────────────────────────────────────────────────────

--- 드래그 상자와 겹치는 **내** 엔티티. 유닛이 하나라도 있으면 건물은 뺀다.
--
--    정렬이 핸들 오름차순인 것은 눈에 보이지 않지만 중요하다 — 선택 목록의
--    순서가 대형 슬롯 배정(§13.5)을 그대로 결정한다.
function M.box_select(w, p, cam, x0, y0, x1, y1)
    if x1 < x0 then x0, x1 = x1, x0 end
    if y1 < y0 then y0, y1 = y1, y0 end
    local ax0, ay0 = M.screen_to_world(cam, x0, y0)
    local ax1, ay1 = M.screen_to_world(cam, x1, y1)
    local units, builds = {}, {}
    for i = 1, C.MAX_ENT - 1 do
        if w.alive[i] ~= 0 and w.owner[i] == p then
            local bx0, by0, bx1, by1 = box(w, i)
            if not (bx1 - 1 < ax0 or ax1 < bx0 or by1 - 1 < ay0 or ay1 < by0) then
                if C.IS_BUILDING[w.kind[i]] ~= 0 then
                    builds[#builds + 1] = w:handle(i)
                else
                    units[#units + 1] = w:handle(i)
                end
            end
        end
    end
    local src = (#units > 0) and units or builds
    table.sort(src)
    local out = {n = 0}
    for k = 1, #src do
        if out.n >= SELECT_MAX then break end
        out[out.n] = src[k]
        out.n = out.n + 1
    end
    return out
end

-- ── SPEC §12.3 컨트롤 그룹 ──────────────────────────────────────────────────

--- 저장되는 것은 **핸들**이다. 죽은 유닛은 valid(§7.2)가 자동으로 거른다.
local Groups = {}
Groups.__index = Groups
M.Groups = Groups

function M.newgroups()
    local self = setmetatable({g = {n = 10}}, Groups)
    for k = 0, 9 do self.g[k] = {n = 0} end
    return self
end
Groups.new = M.newgroups

function Groups:set(k, sel)
    local t = {n = sel.n}
    for j = 0, sel.n - 1 do t[j] = sel[j] end
    self.g[k] = t
end

function Groups:recall(w, k)
    local out = {n = 0}
    local g = self.g[k]
    for j = 0, g.n - 1 do
        if w:valid(g[j]) then
            out[out.n] = g[j]
            out.n = out.n + 1
        end
    end
    return out
end

-- ── SPEC §12.4 명령 큐 ──────────────────────────────────────────────────────

--- 유닛당 큐 하나. 기본 클릭은 비우고 하나, 시프트 클릭은 뒤에 붙인다.
local Orders = {}
Orders.__index = Orders
M.Orders = Orders

function M.neworders()
    local self = setmetatable({q = {n = C.MAX_ENT}}, Orders)
    for i = 0, C.MAX_ENT - 1 do self.q[i] = {n = 0} end
    return self
end
Orders.new = M.neworders

function Orders:push(i, order, shift)
    if order[0] == STOP then
        self.q[i] = {n = 0}                    -- STOP 은 큐를 비우고 끝이다
        return
    end
    if not shift then
        self.q[i] = {n = 0}
    end
    if self.q[i].n < ORDER_MAX then
        self.q[i][self.q[i].n] = order
        self.q[i].n = self.q[i].n + 1
    end
end

function Orders:pop(i)
    local q = self.q[i]
    if q.n == 0 then
        return nil
    end
    local head = q[0]
    local nq = {n = q.n - 1}
    for j = 1, q.n - 1 do nq[j - 1] = q[j] end
    self.q[i] = nq
    return head
end

function Orders:clear(i)
    self.q[i] = {n = 0}
end

--- 우클릭의 문맥 규칙. 판정 순서가 명세다 — 적 정제소는 반납이 아니라 공격이다.
function M.context_order(w, ec, m, p, tx, ty, h)
    if w:valid(h) then
        local j = S.index(h)
        if w.owner[j] ~= p then
            return M.ATTACK
        end
        if E.is_depot(w.kind[j]) then
            return M.HARVEST
        end
        return M.MOVE
    end
    if m:in_map(tx, ty) and ec.ore[ty * m.w + tx] > 0 then
        return M.HARVEST
    end
    return M.MOVE
end

return M
