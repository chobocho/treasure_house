-- 상수표와 유닛·건물표 (SPEC §0, §25).
--
--    파이썬 쪽과 마찬가지로 이 시험만 SPEC.md 를 **직접 읽어** 표와 코드를
--    대조한다. 손으로 옮겨 적은 숫자는 반드시 언젠가 한 자리가 틀리고, 그 한
--    자리는 1200틱 뒤 해시 불일치로만 드러난다.

local H = require('tests.harness')
local C = require('rts.const')

H.title('const')

local SPEC = H.lines(H.root_file('SPEC.md'))

--- 지정한 절 제목 뒤 첫 마크다운 표의 데이터 행을 셀 목록으로 돌려준다.
local function table_rows(header_line)
    local i = H.index_of(SPEC, header_line)
    while SPEC[i]:sub(1, 1) ~= '|' do i = i + 1 end
    i = i + 2                               -- 머리글과 구분선을 건너뛴다
    local out = {n = 0}
    while i < SPEC.n and SPEC[i]:sub(1, 1) == '|' do
        local line = SPEC[i]:gsub('^|', ''):gsub('|$', '')
        local cells = {n = 0}
        local start = 1
        while true do
            local p = line:find('|', start, true)
            local cell
            if p then cell = line:sub(start, p - 1) else cell = line:sub(start) end
            cells[cells.n] = H.strip(cell)
            cells.n = cells.n + 1
            if not p then break end
            start = p + 1
        end
        out[out.n] = cells
        out.n = out.n + 1
        i = i + 1
    end
    return out
end

local function num(s)
    s = s:gsub('%(.*$', '')
    s = H.strip(s):gsub('`', '')
    if s == '—' or s == '-' or s == '' then
        return 0
    end
    return tonumber(s)                      -- '0x1021' 도 그대로 읽힌다
end

-- ── §0 상수표 ───────────────────────────────────────────────────────────────
local bad = 0
local n = 0
for r = 0, table_rows('## 0. 상수').n - 1 do
    local cells = table_rows('## 0. 상수')[r]
    local name = cells[0]:gsub('`', ''):gsub('\\', '')
    if C[name] == nil then
        H.note('%s 가 const 에 없다', name)
        bad = bad + 1
    else
        n = n + 1
        if C[name] ~= num(cells[1]) then
            H.note('%s 기대 %s 실제 %s', name, cells[1], H.repr(C[name]))
            bad = bad + 1
        end
    end
end
H.check(string.format('§0 상수 %d개가 표와 같다', n), bad, 0)

-- ── §25.1 유닛표 ────────────────────────────────────────────────────────────
local COLS = {'HP', 'BASIC', 'PIERCE', 'ARMOUR', 'RANGE', 'RELOAD',
              'SPEED', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP'}
bad = 0
local kinds = {n = 0}
local urows = table_rows('### 25.1 유닛')
for r = 0, urows.n - 1 do
    local cells = urows[r]
    local k = tonumber(cells[0])
    kinds[kinds.n] = k
    kinds.n = kinds.n + 1
    local short = cells[1]:match('`([^`]*)`')
    if C[short] ~= k then
        H.note('%s 번호 기대 %d 실제 %s', short, k, H.repr(C[short]))
        bad = bad + 1
    end
    for j = 1, #COLS do
        local got = C[COLS[j]][k]
        if got ~= num(cells[1 + j]) then
            H.note('%s.%s 기대 %s 실제 %s', short, COLS[j], cells[1 + j],
                   H.repr(got))
            bad = bad + 1
        end
    end
    if C.NAME[k] ~= H.strip((cells[1]:gsub('`.*$', ''))) then bad = bad + 1 end
    if C.FOOT[k] ~= 1 or C.IS_BUILDING[k] ~= 0 then bad = bad + 1 end
end
H.check(string.format('§25.1 유닛 %d종 × %d칸', kinds.n, #COLS + 3), bad, 0)
H.check('유닛 번호는 0..4', kinds, {[0] = 0, 1, 2, 3, 4, n = 5})

-- ── §25.2 건물표 ────────────────────────────────────────────────────────────
local BCOLS = {'HP', 'ARMOUR', 'SIGHT', 'COST', 'BUILD_TICKS', 'POP'}
bad = 0
local bkinds = {n = 0}
local brows = table_rows('### 25.2 건물')
for r = 0, brows.n - 1 do
    local cells = brows[r]
    local k = tonumber(cells[0])
    bkinds[bkinds.n] = k
    bkinds.n = bkinds.n + 1
    local short = cells[1]:match('`([^`]*)`')
    if C[short] ~= k then bad = bad + 1 end
    if C.FOOT[k] ~= tonumber(cells[2]:match('^(%d+)')) then
        H.note('%s 발자국 기대 %s 실제 %d', short, cells[2], C.FOOT[k])
        bad = bad + 1
    end
    for j = 1, #BCOLS do
        if C[BCOLS[j]][k] ~= num(cells[2 + j]) then
            H.note('%s.%s 기대 %s 실제 %s', short, BCOLS[j], cells[2 + j],
                   H.repr(C[BCOLS[j]][k]))
            bad = bad + 1
        end
    end
    if C.IS_BUILDING[k] ~= 1 then bad = bad + 1 end
end
H.check(string.format('§25.2 건물 %d종 × %d칸', bkinds.n, #BCOLS + 2), bad, 0)
H.check('건물 번호는 10..15', bkinds, {[0] = 10, 11, 12, 13, 14, 15, n = 6})

-- 방어탑의 공격 수치는 비고 칸에만 있다 — 거기서도 읽어 온다
local tower
for r = 0, brows.n - 1 do
    if brows[r][0] == '15' then tower = brows[r][9] end
end
local vals = {n = 0}
for d in tower:gmatch('%d+') do
    vals[vals.n] = tonumber(d)
    vals.n = vals.n + 1
end
H.check('방어탑 기본·관통·사거리·재장전',
        {[0] = C.BASIC[C.TOWER], C.PIERCE[C.TOWER],
         C.RANGE[C.TOWER], C.RELOAD[C.TOWER], n = 4}, vals)

-- ── 표의 내부 정합성 ────────────────────────────────────────────────────────
local t = {n = 0}
for k = 5, 9 do t[t.n] = C.HP[k]; t.n = t.n + 1 end
H.check('빈 번호 5..9 는 전부 0', t, {[0] = 0, 0, 0, 0, 0, n = 5})

local lens, want16 = {n = 0}, {n = 0}
local ALLCOLS = {}
for j = 1, #COLS do ALLCOLS[#ALLCOLS + 1] = COLS[j] end
ALLCOLS[#ALLCOLS + 1] = 'FOOT'
ALLCOLS[#ALLCOLS + 1] = 'NAME'
for j = 1, #ALLCOLS do
    lens[lens.n] = C[ALLCOLS[j]].n; lens.n = lens.n + 1
    want16[want16.n] = 16; want16.n = want16.n + 1
end
H.check('표 길이는 16', lens, want16)

local noatk = {n = 0}
for k = 0, 15 do
    if C.IS_BUILDING[k] == 0 and C.HP[k] ~= 0 and C.BASIC[k] == 0 then
        noatk[noatk.n] = k; noatk.n = noatk.n + 1
    end
end
H.check('공격하지 않는 것은 채집기뿐', noatk, {[0] = C.HARV, n = 1})

local all_ok = true
for k = 0, 15 do
    if C.RANGE[k] == 0 and C.HP[k] ~= 0 and C.BASIC[k] ~= 0 then all_ok = false end
end
H.check_true('사거리가 0 인 유닛은 공격력도 0', all_ok)
all_ok = true
for k = 0, 15 do
    if C.SIGHT[k] > C.SIGHT_MAX then all_ok = false end
end
H.check_true('모든 유닛의 시야는 SIGHT_MAX 이하', all_ok)

-- 이동 종류는 §25.1 아래 문단에만 있다 — 표가 아니라 산문이라 여기에 옮겨 적는다
local veh = {n = 0}
for k = 0, 15 do
    if C.MOVE_KIND[k] == 1 then veh[veh.n] = k; veh.n = veh.n + 1 end
end
H.check('차량은 전차와 채집기뿐 (SPEC §25.1)', veh,
        {[0] = C.TANK, C.HARV, n = 2})
local bmk = {n = 0}
for k = 10, 15 do bmk[bmk.n] = C.MOVE_KIND[k]; bmk.n = bmk.n + 1 end
H.check('건물의 이동 종류는 0', bmk, {[0] = 0, 0, 0, 0, 0, 0, n = 6})

-- ── §25.3 기술 트리 ─────────────────────────────────────────────────────────
H.check('HQ 는 선행 조건이 없다', C.PREREQ[C.HQ], {n = 0})
local multi = {n = 0}
for k = 0, 15 do
    if C.PREREQ[k].n > 1 then multi[multi.n] = k; multi.n = multi.n + 1 end
end
H.check('공장만 선행 조건이 둘', multi, {[0] = C.FACT, n = 1})
H.check('공장의 선행은 발전소와 병영 (번호 오름차순)', C.PREREQ[C.FACT],
        {[0] = C.BARR, C.POW, n = 2})
H.check('전차·박격포는 공장에서',
        {[0] = C.PREREQ[C.TANK], C.PREREQ[C.MORTAR], n = 2},
        {[0] = {[0] = C.FACT, n = 1}, {[0] = C.FACT, n = 1}, n = 2})
bad = 0
for k = 0, 15 do
    for j = 0, C.PREREQ[k].n - 1 do
        if C.IS_BUILDING[C.PREREQ[k][j]] ~= 1 then bad = bad + 1 end
    end
end
H.check('선행 조건은 전부 건물', bad, 0)

--- DAG 확인 — 순환이 있으면 위상 정렬이 멈춘다 (§16.6).
local function has_cycle()
    local seen = {}
    for k = 0, 15 do seen[k] = 0 end
    local visit
    visit = function(k)
        if seen[k] == 1 then return true end
        if seen[k] == 2 then return false end
        seen[k] = 1
        for j = 0, C.PREREQ[k].n - 1 do
            if visit(C.PREREQ[k][j]) then return true end
        end
        seen[k] = 2
        return false
    end
    for k = 0, 15 do
        if visit(k) then return true end
    end
    return false
end
H.check('기술 트리는 순환이 없다', has_cycle(), false)

-- ── §17.1 FSM 상태 번호표 ───────────────────────────────────────────────────
bad = 0
local names = {n = 0}
local frows = table_rows('### 17.1 유닛 FSM')
for r = 0, frows.n - 1 do
    local name = frows[r][1]:gsub('`', '')
    names[names.n] = name
    names.n = names.n + 1
    if C[name] ~= tonumber(frows[r][0]) then
        H.note('%s 기대 %s 실제 %s', name, frows[r][0], H.repr(C[name]))
        bad = bad + 1
    end
end
H.check(string.format('§17.1 상태 번호 %d개', names.n), bad, 0)
local nums = {}
for r = 0, names.n - 1 do nums[#nums + 1] = C[names[r]] end
table.sort(nums)
local sorted = {n = names.n}
for r = 0, names.n - 1 do sorted[r] = nums[r + 1] end
local want10 = {n = 10}
for r = 0, 9 do want10[r] = r end
H.check('상태 번호는 0..9 로 겹치지 않는다', sorted, want10)

-- ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
H.check('시작 크레딧 1000', C.START_CREDITS, 1000)
H.check('시작 채집기 2기', C.START_HARV, 2)
H.check('시나리오 길이 1200틱', C.SCENARIO_TICKS, 1200)

return H.done()
