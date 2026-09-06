-- 상수표와 유닛·건물표 — SPEC §0, §25.
--
--    이 파일은 다른 모듈을 하나도 참조하지 않고, 함수도 (표를 만드는 것 말고는)
--    없다. 숫자만 있다. 같은 상수를 두 군데 적으면 한 쪽만 고치는 날이 오고,
--    그날 세 언어가 갈린다. 그래서 `fixed` 에 있는 FP_* 와 D_* 를 여기서 다시
--    읽어 오는 편이 옳아 보이지만 그렇게 하지 않았다 — `fixed` 는 의존이 없어야
--    세 언어에서 가장 먼저 포팅된다. 두 곳에 있는 값은 test_const 와 test_fixed
--    가 서로 대조한다.

local M = {}

-- ── §0 화면과 맵 ────────────────────────────────────────────────────────────
M.SCR_W = 320
M.SCR_H = 200
M.TILE = 16
M.MAP_W = 64
M.MAP_H = 64
M.VIEW_X = 0
M.VIEW_Y = 0
M.VIEW_W = 256                    -- 16타일
M.VIEW_H = 176                    -- 11타일 — 176 + 24 = 200 이 정확히 화면 높이다
M.PANEL_X = 256
M.PANEL_W = 64
M.MINI_X = 256
M.MINI_Y = 0
M.MINI_W = 64
M.MINI_H = 64
M.BAR_Y = 176
M.BAR_H = 24

-- ── §0 고정소수점 (fixed 와 같은 값이어야 한다) ─────────────────────────────
M.FP_BITS = 16
M.FP_ONE = 65536
M.FP_HALF = 32768
M.FP_DIAG = 46341
M.FP_SQRT2M1 = 27146

-- ── §0 하드웨어와 시간 ──────────────────────────────────────────────────────
M.PAL_SIZE = 256
M.DAC_MAX = 63
M.TICK_US = 54925                 -- 18.2065 Hz. 실제 54,925.4 µs — 오차 0.0007 %
M.PIT_HZ = 1193182

-- ── §0 시뮬레이션 ───────────────────────────────────────────────────────────
M.ORDER_DELAY = 2
M.MAX_ENT = 256
M.GEN_MOD = 256
M.MAX_PLAYER = 4
M.SIGHT_MAX = 8
M.CLUSTER = 8
M.BUCKET = 8
M.D_STRAIGHT = 10
M.D_DIAG = 14

-- ── §0 해시와 CRC ───────────────────────────────────────────────────────────
M.FNV_OFFSET = 2166136261
M.FNV_PRIME = 16777619
M.CRC_POLY = 4129                 -- 0x1021
M.CRC_INIT = 65535                -- 0xFFFF

-- ── §25 종류 번호 ───────────────────────────────────────────────────────────
-- 유닛 0..4, 건물 10..15. 5..9 를 비워 둔 것은 "유닛인가"를 번호 하나로
-- 판별하려는 유혹을 막기 위해서다 — 판별은 IS_BUILDING 표가 한다.
M.INF, M.ARCHER, M.TANK, M.MORTAR, M.HARV = 0, 1, 2, 3, 4
M.HQ, M.REF, M.BARR, M.FACT, M.POW, M.TOWER = 10, 11, 12, 13, 14, 15

local INF, ARCHER, TANK, MORTAR, HARV = 0, 1, 2, 3, 4
local HQ, REF, BARR, FACT, POW, TOWER = 10, 11, 12, 13, 14, 15

M.KIND_COUNT = 16
local KIND_COUNT = 16

--- {종류, 값} 쌍을 길이 16 의 0-기반 배열로. 세 언어가 같은 모양을 갖도록
--- 딕셔너리가 아니라 배열로 둔다 — 순회 순서가 언어마다 다르면 안 되기 때문이다.
local function tab(pairs_)
    local t = {n = KIND_COUNT}
    for k = 0, KIND_COUNT - 1 do t[k] = 0 end
    for i = 1, #pairs_ do
        t[pairs_[i][1]] = pairs_[i][2]
    end
    return t
end

M.NAME = {n = KIND_COUNT}
for k = 0, KIND_COUNT - 1 do M.NAME[k] = '' end
for _, p in ipairs({{INF, '보병'}, {ARCHER, '사수'}, {TANK, '전차'},
                    {MORTAR, '박격포'}, {HARV, '채집기'}, {HQ, '사령부'},
                    {REF, '정제소'}, {BARR, '병영'}, {FACT, '공장'},
                    {POW, '발전소'}, {TOWER, '방어탑'}}) do
    M.NAME[p[1]] = p[2]
end

M.HP = tab({{INF, 40}, {ARCHER, 30}, {TANK, 90}, {MORTAR, 35}, {HARV, 60},
            {HQ, 400}, {REF, 250}, {BARR, 200}, {FACT, 300}, {POW, 150},
            {TOWER, 120}})
M.BASIC = tab({{INF, 6}, {ARCHER, 4}, {TANK, 12}, {MORTAR, 10}, {TOWER, 8}})
M.PIERCE = tab({{INF, 3}, {ARCHER, 6}, {TANK, 8}, {MORTAR, 12}, {TOWER, 6}})
M.ARMOUR = tab({{INF, 1}, {ARCHER, 0}, {TANK, 4}, {MORTAR, 0}, {HARV, 3},
                {HQ, 3}, {REF, 5}, {BARR, 4}, {FACT, 5}, {POW, 3}, {TOWER, 5}})
M.RANGE = tab({{INF, 1}, {ARCHER, 4}, {TANK, 3}, {MORTAR, 6}, {TOWER, 5}})
M.RELOAD = tab({{INF, 12}, {ARCHER, 16}, {TANK, 24}, {MORTAR, 40}, {TOWER, 20}})
-- 16.16 px/틱. 1.5 px/틱 = 0.094 타일/틱 — 47타일 대각선에 500틱이 든다.
M.SPEED = tab({{INF, 98304}, {ARCHER, 91750}, {TANK, 131072},
               {MORTAR, 65536}, {HARV, 78643}})
M.SIGHT = tab({{INF, 4}, {ARCHER, 5}, {TANK, 5}, {MORTAR, 4}, {HARV, 3},
               {HQ, 6}, {REF, 4}, {BARR, 4}, {FACT, 4}, {POW, 3}, {TOWER, 6}})
M.COST = tab({{INF, 100}, {ARCHER, 140}, {TANK, 300}, {MORTAR, 260},
              {HARV, 150}, {REF, 300}, {BARR, 400}, {FACT, 600}, {POW, 200},
              {TOWER, 250}})
M.BUILD_TICKS = tab({{INF, 60}, {ARCHER, 80}, {TANK, 150}, {MORTAR, 140},
                     {HARV, 90}, {REF, 180}, {BARR, 200}, {FACT, 300},
                     {POW, 120}, {TOWER, 120}})
-- 유닛은 인구 소비, 건물은 인구 제공 — 어느 쪽인지는 IS_BUILDING 이 정한다.
M.POP = tab({{INF, 1}, {ARCHER, 1}, {TANK, 2}, {MORTAR, 2}, {HARV, 1},
             {HQ, 10}, {POW, 10}})
M.FOOT = tab({{INF, 1}, {ARCHER, 1}, {TANK, 1}, {MORTAR, 1}, {HARV, 1},
              {HQ, 3}, {REF, 2}, {BARR, 2}, {FACT, 3}, {POW, 2}, {TOWER, 1}})
M.IS_BUILDING = tab({{HQ, 1}, {REF, 1}, {BARR, 1}, {FACT, 1}, {POW, 1},
                     {TOWER, 1}})
-- §4.3 통행 비트 번호와 같은 값이다: 0 = 보병, 1 = 차량. 차량은 언덕에 못 오른다.
M.MOVE_KIND = tab({{TANK, 1}, {HARV, 1}})

-- ── §17.1 FSM 상태 번호 ─────────────────────────────────────────────────────
-- 전투 유닛과 채집기가 state 바이트 하나를 나눠 쓴다. 겹치면 상태 해시가
-- 같은 값을 두 뜻으로 읽게 되므로 번호는 여기 한 곳에서만 정한다.
M.ST_IDLE, M.ST_MOVE, M.ST_ATTACK, M.ST_FLEE = 0, 1, 2, 3
M.ST_SEEK, M.ST_TO_ORE, M.ST_MINE = 4, 5, 6
M.ST_TO_BASE, M.ST_UNLOAD, M.ST_BUILD = 7, 8, 9

-- ── §25.3 기술 트리 (DAG) ───────────────────────────────────────────────────
-- 선행 목록은 **번호 오름차순**으로 적는다. 위상 정렬의 타이브레이크가 세 언어에서
-- 같아야 하기 때문이다. FACT 만 선행이 둘이고, 그래서 위상 정렬이 실제로 필요하다.
M.PREREQ = {n = KIND_COUNT}
for k = 0, KIND_COUNT - 1 do M.PREREQ[k] = {n = 0} end
local function prereq(k, list)
    local t = {n = #list}
    for i = 1, #list do t[i - 1] = list[i] end
    M.PREREQ[k] = t
end
prereq(HARV, {HQ})
prereq(REF, {HQ})
prereq(BARR, {HQ})
prereq(INF, {BARR})
prereq(ARCHER, {BARR})
prereq(TOWER, {BARR})
prereq(FACT, {BARR, POW})
prereq(TANK, {FACT})
prereq(MORTAR, {FACT})

-- ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
M.START_CREDITS = 1000
M.START_HARV = 2
M.SCENARIO_TICKS = 1200

return M
