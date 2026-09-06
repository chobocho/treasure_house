-- 락스텝 네트워크 — 명령만 보낸다 (SPEC §19).
--
--    유닛 200기의 상태는 매 틱 수 KB 다. 명령은 대개 0개이고, 있어도 한 줄이면
--    20바이트다. 28.8 kbps 모뎀에서 전자는 불가능하고 후자는 여유롭다. 대신
--    **모든 기계가 같은 계산을 해야 한다**는 대가를 치른다 — 이 저장소의 골든
--    해시 전부가 그 대가를 갚는 일이다.
--
--    지터가 있어도 결과는 같다. 명령의 **실행 틱은 보낼 때 정해지고**, 늦게
--    도착하면 그 틱을 기다릴 뿐이다. 늦게 도착한 명령을 앞당겨 실행하는 경로는
--    존재하지 않는다 — 그런 경로가 하나라도 있으면 락스텝은 그 자리에서 끝난다.

local C = require('rts.const')
local R = require('rts.rng')

local M = {}

local Net = {}
Net.__index = Net
M.Net = Net

function M.new(n_players, latency, jitter_seed, jitter_max)
    local self = setmetatable({}, Net)
    self.n = n_players
    self.latency = latency or C.ORDER_DELAY
    self.jitter_max = jitter_max or 0
    -- 지터는 **전용 RNG** 로 만든다. 시뮬레이션 RNG(§3.3)를 쓰면 네트워크
    -- 사정이 게임 내용을 바꾸고, 그것이야말로 디싱크의 정의다.
    self.rng = R.new(jitter_seed or 0)
    self.box = {}                 -- 실행 틱 → 명령 목록
    self.sealed = {}              -- 실행 틱 → {플레이어: 도착 틱}
    self.delay = {}               -- '보낸 틱,플레이어' → 도착 틱
    self.stalls = 0               -- 실행 틱보다 늦게 닿은 턴의 수
    return self
end
Net.new = M.new

--- 실행 틱은 지터와 무관하다.
function Net:exec_of(tick, player)
    return tick + self.latency
end

function Net:arrive_of(tick, player)
    local key = tick .. ',' .. player
    if self.delay[key] == nil then
        local j = 0
        if self.jitter_max ~= 0 then
            j = self.rng:roll(self.jitter_max + 1)
        end
        self.delay[key] = tick + self.latency + j
        if j > 0 then
            self.stalls = self.stalls + 1
        end
    end
    return self.delay[key]
end

function Net:send(tick, player, order)
    self:arrive_of(tick, player)
    local et = self:exec_of(tick, player)
    if self.box[et] == nil then
        self.box[et] = {n = 0}
    end
    local b = self.box[et]
    b[b.n] = order
    b.n = b.n + 1
    return et
end

--- 빈 턴도 보낸다. 그래야 상대가 영원히 기다리지 않는다.
function Net:flush(tick, player)
    local et = self:exec_of(tick, player)
    if self.sealed[et] == nil then
        self.sealed[et] = {n = 0}
    end
    local d = self.sealed[et]
    if d[player] == nil then
        d.n = d.n + 1
    end
    d[player] = self:arrive_of(tick, player)
    return et
end

--- 그 실행 틱의 몫이 **전원** 도착했는가. wall 은 지금 시각(틱)이다.
function Net:ready(exec_tick, wall)
    local d = self.sealed[exec_tick]
    if d == nil or d.n ~= self.n then
        return false
    end
    if wall == nil then
        return true
    end
    -- 플레이어 번호 오름차순으로 본다 — 파이썬의 sorted(d) 와 같은 순서다.
    for p = 0, C.MAX_PLAYER - 1 do
        if d[p] ~= nil and d[p] > wall then
            return false
        end
    end
    return true
end

--- 그 틱의 명령을 §18.1 의 키로 정렬해 돌려준다. 한 번만 준다.
function Net:take(exec_tick)
    local out = self.box[exec_tick]
    self.box[exec_tick] = nil
    if out == nil then
        return {n = 0}
    end
    local tmp = {}
    for k = 0, out.n - 1 do tmp[k + 1] = out[k] end
    table.sort(tmp, function(a, b)
        local n = a.n < b.n and a.n or b.n
        for k = 0, n - 1 do
            if a[k] ~= b[k] then return a[k] < b[k] end
        end
        return a.n < b.n
    end)
    for k = 0, out.n - 1 do out[k] = tmp[k + 1] end
    return out
end

return M
