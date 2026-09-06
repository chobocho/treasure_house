-- CLI — 세 언어가 같은 부명령을 갖는다 (SPEC §24).
--
--    `prim` 의 출력은 `golden/prim.txt` 와 **바이트 단위로 같아야 한다.** 절 구분
--    `== N. 제목 ==` 은 명세이며, 덱의 `<!--OUT sec=N-->` 지시자가 이 표시로 절을
--    잘라 온다.
--
--    여기에 박힌 시험 입력들(거리 쌍·제곱근 인자·피해 조합…)은 tools/gen_prim.py
--    의 것과 **같아야 한다.** 두 곳에 적히는 유일한 자료이며, 둘이 어긋나면
--    `cmp` 가 그 자리에서 잡는다 — 그래서 굳이 한 곳으로 합치지 않았다.
--    합치면 "둘 다 같은 실수를 했다"는 사고를 막을 수 없다.

package.path = './?.lua;' .. package.path

local AI = require('rts.ai')
local CI = require('rts.circle')
local CB = require('rts.combat')
local C = require('rts.const')
local E = require('rts.econ')
local F = require('rts.fixed')
local FL = require('rts.flow')
local FG = require('rts.fog')
local HP = require('rts.hpa')
local JP = require('rts.jps')
local P = require('rts.path')
local RS = require('rts.raster')
local RD = require('rts.render')
local RP = require('rts.replay')
local R = require('rts.rng')
local SIM = require('rts.sim')
local SK = require('rts.speaker')
local T = require('rts.tmap')

local M = {}
local floor = math.floor
local fmt = string.format

-- 골든 디렉터리 — lua/ 에서 실행하므로 한 칸 위다. 실행 위치가 달라져도
-- 찾아지도록 후보를 훑는다.
local GOLDEN_CANDIDATES = {'../golden/', 'golden/', '../../golden/'}
local golden_dir = nil

local function golden(name)
    if golden_dir == nil then
        for _, d in ipairs(GOLDEN_CANDIDATES) do
            local f = io.open(d .. 'prim.txt', 'rb')
            if f then f:close(); golden_dir = d; break end
        end
        assert(golden_dir, 'golden 디렉터리를 찾지 못했다')
    end
    local f = assert(io.open(golden_dir .. name, 'rb'))
    local s = f:read('*a')
    f:close()
    return s
end
M.golden = golden

local function pt(x, y) return {[0] = x, [1] = y, n = 2} end
local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local PAIRS_M = lst(pt(1, 0), pt(0, 1), pt(1, 1), pt(2, 1), pt(3, 1), pt(3, 2),
                    pt(4, 3), pt(5, 5), pt(8, 3), pt(10, 0), pt(10, 10),
                    pt(-7, 4), pt(-6, -6), pt(0, -9), pt(12, -5), pt(-3, 11))
local SQ_N = lst(0, 1, 2, 3, 15, 16, 17, 99, 100, 65535, 65536, 1000000,
                 2147483647)
local ANG_V = lst(pt(12, 5), pt(12, -5), pt(12, 6), pt(5, 12), pt(12, 4),
                  pt(-12, 5), pt(-5, -12), pt(0, 0), pt(1, 0), pt(0, -1),
                  pt(7, 3), pt(3, 7), pt(-9, -4), pt(4, -9), pt(100, 41),
                  pt(100, 42))
local DMG_CASE = lst({6, 3, 0}, {6, 3, 2}, {6, 3, 5}, {6, 3, 9}, {9, 1, 0},
                     {9, 1, 4}, {12, 8, 3}, {12, 8, 11}, {4, 0, 0}, {4, 0, 3},
                     {20, 12, 6}, {2, 2, 4})
local LAN_CASE = lst({10, 10, 6554, 6554}, {20, 10, 6554, 6554},
                     {10, 20, 6554, 6554}, {30, 20, 3277, 6554},
                     {5, 5, 13107, 13107}, {50, 40, 1311, 1311},
                     {12, 8, 6554, 9830}, {100, 100, 655, 655})
local ECON_CASE = lst({0, 6554}, {4, 6554}, {8, 6554}, {16, 6554},
                      {8, 13107}, {8, 3277})
local FOG_UNITS = lst({10, 10, 3}, {12, 11, 5}, {30, 30, 8})
local FLOWMAP = {
    '............',
    '.##########.',
    '.#........#.',
    '.#.######.#.',
    '.#.#....#.#.',
    '.#.#.##.#.#.',
    '.#.#.##.#.#.',
    '.#.#....#.#.',
    '.#.######.#.',
    '.#........#.',
    '.##########.',
    '............',
}

local function maps()
    local ms = {n = 6}
    for i = 1, 6 do
        ms[i - 1] = T.load_text(golden('map_' .. i .. '.txt'))
    end
    return ms
end

local function flowmap()
    local m = T.new(#FLOWMAP[1], #FLOWMAP)
    for y = 0, #FLOWMAP - 1 do
        local row = FLOWMAP[y + 1]
        for x = 0, m.w - 1 do
            local ch = row:sub(x + 1, x + 1)
            m.terrain[y * m.w + x] = (ch == '#') and T.ROCK or T.DIRT
            m:_repass(y * m.w + x)
        end
    end
    m:_bump()
    return m
end

-- 출력 줄 모으기
local function push(o, s)
    o.n = o.n + 1
    o[o.n] = s
end

local function join(t, sep)
    local a = {}
    for k = 1, #t do a[k] = t[k] end
    return table.concat(a, sep)
end

-- ── prim 의 절들 ────────────────────────────────────────────────────────────
local function sec1(o)
    push(o, '== 1. 거리 척도 ==')
    push(o, '  dx   dy     d1  dinf   d83   dab   doct     eu3  d83pm  dabpm'
            .. ' doctpm')
    for k = 0, PAIRS_M.n - 1 do
        local dx, dy = PAIRS_M[k][0], PAIRS_M[k][1]
        local eu = F.isqrt((dx * dx + dy * dy) * 1000000)
        push(o, fmt('%4d %4d %6d %5d %5d %5d %6d %7d %6d %6d %6d',
                    dx, dy, F.d1(dx, dy), F.dinf(dx, dy), F.d83(dx, dy),
                    F.dab(dx, dy), F.doct(dx, dy), eu,
                    F.floordiv(F.d83(dx, dy) * 1000000, eu) - 1000,
                    F.floordiv(F.dab(dx, dy) * 1000000, eu) - 1000,
                    F.floordiv(F.doct(dx, dy) * 100000, eu) - 1000))
    end
    push(o, 'eu3 = floor(sqrt(dx^2+dy^2) * 1000)')
    push(o, 'd83pm dabpm = 유클리드 대비 천분율 편차')
    push(o, 'doctpm = 유클리드*10 대비. 옥타일은 유클리드 근사가 아니므로'
            .. ' 참고값이며,')
    push(o, '참 옥타일과의 비교는 out/analysis.txt 2절에 있다.')
end

local function sec2(o)
    push(o, '== 2. 정수 제곱근 ==')
    push(o, '          n     isqrt          isqrt^2      (isqrt+1)^2')
    for k = 0, SQ_N.n - 1 do
        local n = SQ_N[k]
        local r = F.isqrt(n)
        push(o, fmt('%11d %9d %16d %16d', n, r, r * r, (r + 1) * (r + 1)))
    end
end

local function sec3(o)
    push(o, '== 3. 8방향 판별 ==')
    push(o, '  dx   dy  12*mn  5*mx  대각  방향  이름')
    for k = 0, ANG_V.n - 1 do
        local dx, dy = ANG_V[k][0], ANG_V[k][1]
        local ax = dx < 0 and -dx or dx
        local ay = dy < 0 and -dy or dy
        local mx = ax > ay and ax or ay
        local mn = ax < ay and ax or ay
        local d = F.atan8(dx, dy)
        push(o, fmt('%4d %4d %6d %5d %5d %5d  %s', dx, dy, 12 * mn, 5 * mx,
                    (12 * mn > 5 * mx) and 1 or 0, d, F.DNAME[d]))
    end
end

local function sec4(o)
    push(o, '== 4. LCG ==')
    local r = R.new(1)
    push(o, '  i           상태   next15')
    for i = 0, 9 do
        local v = r:next15()
        push(o, fmt('%3d %14d %8d', i + 1, r.s, v))
    end
    push(o, '하위 비트의 짧은 주기 — 상태의 최하위 1·2비트')
    local r2 = R.new(1)
    local b1, b2 = {}, {}
    for _ = 1, 16 do
        r2:next15()
        b1[#b1 + 1] = tostring(r2.s % 2)
        b2[#b2 + 1] = tostring(r2.s % 4)
    end
    push(o, '  bit0: ' .. join(b1, ' '))
    push(o, '  bit10: ' .. join(b2, ' '))
    local r3 = R.new(2026)
    local a = {}
    for _ = 1, 20 do a[#a + 1] = tostring(r3:roll(6)) end
    push(o, 'roll(6) x20: ' .. join(a, ' '))
    push(o, fmt('기각 횟수 %d', r3.rejects))
    local r4 = R.new(2026)
    local hist = {}
    for k = 1, 6 do hist[k] = 0 end
    for _ = 1, 6000 do
        local v = r4:roll(6)
        hist[v + 1] = hist[v + 1] + 1
    end
    local hs = {}
    for k = 1, 6 do hs[k] = tostring(hist[k]) end
    push(o, 'roll(6) x6000 도수: ' .. join(hs, ' '))
    push(o, fmt('기각 횟수 %d', r4.rejects))
end

local function sec5(o)
    push(o, '== 5. 오토타일 ==')
    push(o, fmt('클래스 %d개', T.CLASS_COUNT))
    push(o, '정규화 인덱스 (마스크 0..255, 16개씩)')
    for row = 0, 15 do
        local a = {}
        for c = 0, 15 do
            a[#a + 1] = fmt('%3d', T.canon_index(T.canon(row * 16 + c)))
        end
        push(o, '  ' .. join(a, ' '))
    end
    push(o, '클래스별 마스크 개수')
    local cls = T.CLASSES
    local row = 1
    while row <= #cls do
        local a = {}
        local last = row + 7
        if last > #cls then last = #cls end
        for i = row, last do
            local cnt = 0
            for k = 0, 255 do
                if T.canon(k) == cls[i] then cnt = cnt + 1 end
            end
            a[#a + 1] = fmt('%3d:%-3d', cls[i], cnt)
        end
        push(o, '  ' .. join(a, ' '))
        row = row + 8
    end
end

local function sec6(o)
    push(o, '== 6. 원 마스크 ==')
    push(o, ' r    개수  span')
    for r = 1, 8 do
        local sp = CI.spans(r)
        local a = {}
        for k = 0, sp.n - 1 do a[#a + 1] = tostring(sp[k]) end
        push(o, fmt('%2d %7d  %s', r, CI.count(r), join(a, ' ')))
    end
end

local function sec7(o, ms)
    push(o, '== 7. 경로 탐색 ==')
    push(o, '맵 출발      도착      BFS걸음  다익스트라   A*비용  A*연노드')
    for i = 0, ms.n - 1 do
        local m = ms[i]
        for k = 0, m.pairs.n - 1 do
            local s, t = m.pairs[k][0], m.pairs[k][1]
            local b = P.bfs(m, 0, s, t)
            local dj = P.dijkstra(m, 0, lst(s[1] * m.w + s[0]),
                                  t[1] * m.w + t[0])[t[1] * m.w + t[0]]
            if dj >= P.INF then dj = -1 end
            local a, _tiles, ex = P.astar(m, 0, s, t)
            push(o, fmt('%2d (%2d,%2d) -> (%2d,%2d) %8d %11d %8d %9d',
                        i + 1, s[0], s[1], t[0], t[1], b, dj, a, ex))
        end
    end
    push(o, '다익스트라와 A* 의 비용은 모든 줄에서 같아야 한다 (정리 8.1)')
end

local function sec8(o, ms)
    push(o, '== 8. HPA* 와 JPS ==')
    push(o, '맵 출발      도착        A*   JPS  JPS연노드   HPA*  HPA*/A*(pm)')
    for i = 0, ms.n - 1 do
        local m = ms[i]
        for k = 0, m.pairs.n - 1 do
            local s, t = m.pairs[k][0], m.pairs[k][1]
            local a = P.astar(m, 0, s, t)
            local j, _tiles, jx = JP.search(m, 0, s, t)
            local hp = HP.search(m, 0, s, t)
            local ratio = -1
            if a > 0 and hp > 0 then
                ratio = F.floordiv(hp * 1000, a)
            end
            push(o, fmt('%2d (%2d,%2d) -> (%2d,%2d) %6d %5d %10d %6d %12d',
                        i + 1, s[0], s[1], t[0], t[1], a, j, jx, hp, ratio))
        end
    end
    push(o, 'JPS 비용은 모든 줄에서 A* 와 같아야 한다 (정리 10.1)')
end

local function sec9(o)
    push(o, '== 9. 흐름장과 클리어런스 ==')
    local m = flowmap()
    local integ = FL.integration(m, 0, lst(pt(4, 4)))
    local fl = FL.flow_dirs(m, 0, integ)
    local cl = FL.clearance(m, 0)
    push(o, '목표 (4,4) · 적분장')
    for y = 0, m.h - 1 do
        local a = {}
        for x = 0, m.w - 1 do a[#a + 1] = fmt('%5d', integ[y * m.w + x]) end
        push(o, '  ' .. join(a, ' '))
    end
    push(o, '경사장 (방향 번호, 255=정지)')
    for y = 0, m.h - 1 do
        local a = {}
        for x = 0, m.w - 1 do a[#a + 1] = fmt('%3d', fl[y * m.w + x]) end
        push(o, '  ' .. join(a, ' '))
    end
    push(o, '클리어런스 (좌상단 기준 정사각 여유)')
    for y = 0, m.h - 1 do
        local a = {}
        for x = 0, m.w - 1 do a[#a + 1] = fmt('%2d', cl[y * m.w + x]) end
        push(o, '  ' .. join(a, ' '))
    end
end

local function sec10(o)
    push(o, '== 10. 안개 참조 카운트 ==')
    local function report(tag, us, count)
        local fg = FG.new(64, 64, 1)
        for k = 0, count - 1 do
            fg:add_sight(0, us[k][1], us[k][2], us[k][3])
        end
        local cnt = fg.count[0]
        local tot, vis, mx = 0, 0, 0
        for i = 0, cnt.n - 1 do
            tot = tot + cnt[i]
            if cnt[i] > 0 then vis = vis + 1 end
            if cnt[i] > mx then mx = cnt[i] end
        end
        local hist = {}
        for k = 0, mx do hist[k] = 0 end
        for i = 0, cnt.n - 1 do
            if cnt[i] ~= 0 then hist[cnt[i]] = hist[cnt[i]] + 1 end
        end
        push(o, fmt('%s 가시 칸 %d · 카운트 합 %d · 최대 %d', tag, vis, tot, mx))
        local a = {}
        for k = 1, mx do a[#a + 1] = fmt('%d:%d', k, hist[k]) end
        push(o, '  도수: ' .. join(a, ' '))
    end
    report('초기', FOG_UNITS, 3)
    local moved = lst({11, 10, 3}, FOG_UNITS[1], FOG_UNITS[2])
    report('1번 유닛 (10,10)->(11,10)', moved, 3)
    report('3번 유닛 사망', moved, 2)
    local fg = FG.new(64, 64, 1)
    local s = 0
    for i = 0, fg.count[0].n - 1 do s = s + fg.count[0][i] end
    push(o, fmt('전원 제거 후 카운트 합 %d', s))
end

local function sec11(o)
    push(o, '== 11. 전투 ==')
    push(o, '기본 관통 방어    mx    lo    n   E*100  모의평균*100')
    for k = 0, DMG_CASE.n - 1 do
        local basic, pierce, armour = DMG_CASE[k][1], DMG_CASE[k][2],
                                      DMG_CASE[k][3]
        local mx = CB.max_damage(basic, pierce, armour)
        local lo = CB.damage_lo(mx)
        local r = R.new(12345)
        local tot = 0
        for _ = 1, 1000 do
            tot = tot + CB.roll_damage(r, basic, pierce, armour)
        end
        push(o, fmt('%4d %4d %4d %5d %5d %4d %7d %13d',
                    basic, pierce, armour, mx, lo, mx - lo + 1,
                    CB.expect100(basic, pierce, armour),
                    F.floordiv(tot * 100, 1000)))
    end
    push(o, '란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)')
    for k = 0, LAN_CASE.n - 1 do
        local a0, b0, al, be = LAN_CASE[k][1], LAN_CASE[k][2],
                               LAN_CASE[k][3], LAN_CASE[k][4]
        local t, a, b = CB.lanchester_sim(a0, b0, al, be)
        push(o, fmt('%4d %4d %6d %6d %8d %8d %8d', a0, b0, al, be, t, a, b))
    end
end

local function sec12(o)
    push(o, '== 12. 경제 ==')
    push(o, '왕복타일 속도(fp)   총틱   수입*10000')
    for k = 0, ECON_CASE.n - 1 do
        local d, v = ECON_CASE[k][1], ECON_CASE[k][2]
        push(o, fmt('%8d %10d %6d %12d', d, v, E.round_trip_ticks(d, v),
                    E.income10000(d, v)))
    end
    push(o, fmt('적재 %d · 틱당 채굴 %d · 반납 %d틱',
                E.LOAD_MAX, E.MINE_PER_TICK, E.UNLOAD_TICKS))
end

local function sec13(o)
    push(o, '== 13. CRC 와 FNV ==')
    -- 파이썬의 %r 은 ASCII 문자열을 작은따옴표로 감싼다 — 그 글자 그대로 낸다.
    for _, s in ipairs({'123456789', '', 'A', 'RTSM', 'the quick brown fox'}) do
        push(o, fmt('crc16 %-20s %6d 0x%04X', "'" .. s .. "'",
                    F.crc16(s), F.crc16(s)))
    end
    for _, s in ipairs({'', 'a', 'foobar', 'RTSM'}) do
        push(o, fmt('fnv1a %-20s %12d 0x%08X', "'" .. s .. "'",
                    F.fnv1a(s), F.fnv1a(s)))
    end
    local b = {n = 16}
    for k = 0, 15 do b[k] = k end
    push(o, fmt('fnv1a bytes(0..15) %12d 0x%08X', F.fnv1a(b), F.fnv1a(b)))
end

local function sec14(o)
    push(o, '== 14. PIT 분주값 ==')
    push(o, '음   목표Hz  분주값   실제Hz*100   차이*100')
    for k = 0, SK.NOTE_NAME.n - 1 do
        local f = SK.NOTE_HZ[k]
        local div = SK.divisor(f)
        local act = SK.actual100(f)
        push(o, fmt('%-4s %6d %7d %12d %10d', SK.NOTE_NAME[k], f, div, act,
                    act - f * 100))
    end
end

function M.cmd_prim()
    local ms = maps()
    local o = {n = 0}
    sec1(o); push(o, '')
    sec2(o); push(o, '')
    sec3(o); push(o, '')
    sec4(o); push(o, '')
    sec5(o); push(o, '')
    sec6(o); push(o, '')
    sec7(o, ms); push(o, '')
    sec8(o, ms); push(o, '')
    sec9(o); push(o, '')
    sec10(o); push(o, '')
    sec11(o); push(o, '')
    sec12(o); push(o, '')
    sec13(o); push(o, '')
    sec14(o)
    local a = {}
    for k = 1, o.n do a[k] = o[k] end
    return table.concat(a, '\n') .. '\n'
end

-- ── 시나리오 ────────────────────────────────────────────────────────────────
local function scenario(ticks, float_bug)
    local m = T.load_text(golden('map_start.txt'))
    local sc = SIM.parse_script(golden('script.txt'))
    local s = SIM.new(m, 1, sc.players, float_bug)
    s:setup_start(false)                 -- §18.6 — 스크립트가 몬다
    return s, sc, (ticks == nil) and sc.ticks or ticks
end
M.scenario = scenario

--- §17.5 의 러시 타이밍을 재는 별도 실행. 스크립트 없이 AI 끼리 붙인다.
local function ai_game(ticks, seed, seven)
    local m = T.load_text(golden('map_start.txt'))
    local s = SIM.new(m, seed or 1, 2)
    s:setup_start(true)
    if seven then
        s.ai_rules = AI.RULES7
    end
    return s, ticks
end

local function ev_json(e)
    local v = {}
    for k = 0, 3 do
        v[k] = (k < e.n) and e[k] or 0
    end
    return fmt('[%d,%d,%d,%d]', v[0], v[1], v[2], v[3])
end

--- §18.3 — 키 순서와 공백까지 명세다. JSON 직렬화기를 믿지 않는다.
function M.cmd_trace(ticks)
    local s, sc, n = scenario(ticks)
    local out = {}
    for t = 1, n do
        local h = s:step(s:script_orders(sc, t))
        local alive = 0
        for i = 1, C.MAX_ENT - 1 do
            if s.w.alive[i] ~= 0 then alive = alive + 1 end
        end
        local cr, su, scp = {}, {}, {}
        for p = 0, sc.players - 1 do
            cr[#cr + 1] = tostring(s.ec.credits[p])
            su[#su + 1] = tostring(s.ec.supply_used[p])
            scp[#scp + 1] = tostring(s.ec.supply_cap[p])
        end
        local ev = {}
        for k = 0, s.events.n - 1 do ev[#ev + 1] = ev_json(s.events[k]) end
        out[#out + 1] = fmt(
            '{"t":%d,"h":"%08X","cr":[%s],"su":[%s],"sc":[%s],"n":%d,"ev":[%s]}',
            t, h, join(cr, ','), join(su, ','), join(scp, ','), alive,
            join(ev, ','))
    end
    return table.concat(out, '\n') .. '\n'
end

function M.cmd_aigame(ticks, seven)
    local s, n = ai_game(ticks or 1200, 1, seven)
    local out = {}
    for t = 1, n do
        local h = s:step({n = 0})
        local alive = 0
        for i = 1, C.MAX_ENT - 1 do
            if s.w.alive[i] ~= 0 then alive = alive + 1 end
        end
        local ev = {}
        for k = 0, s.events.n - 1 do ev[#ev + 1] = ev_json(s.events[k]) end
        out[#out + 1] = fmt(
            '{"t":%d,"h":"%08X","cr":[%d,%d],"su":[%d,%d],"sc":[%d,%d],'
            .. '"n":%d,"ev":[%s]}',
            t, h, s.ec.credits[0], s.ec.credits[1],
            s.ec.supply_used[0], s.ec.supply_used[1],
            s.ec.supply_cap[0], s.ec.supply_cap[1], alive, join(ev, ','))
    end
    return table.concat(out, '\n') .. '\n'
end

function M.cmd_hashes(ticks)
    local s, sc, n = scenario(ticks)
    local out = {}
    for t = 1, n do
        out[#out + 1] = fmt('%d %08X', t, s:step(s:script_orders(sc, t)))
    end
    return table.concat(out, '\n') .. '\n'
end

function M.cmd_render(path, tick)
    tick = tick or 1
    local s, sc = scenario()
    for t = 1, tick do
        s:step(s:script_orders(sc, t))
    end
    local pal = RS.build_palette()
    local light = RS.build_light(pal)
    local view = RD.newview()
    view:center_on(s.m, s.m.starts[0][0], s.m.starts[0][1])
    local fb = RS.newframe()
    RD.draw(fb.fb, s, view, 0, pal, light, 0, {n = 0}, fmt('TICK %d', tick))
    local f = assert(io.open(path, 'wb'))
    f:write(RS.to_ppm(fb.fb, pal))
    f:close()
    return fmt('%s — 틱 %d\n', path, tick)
end

--- §19.3·§19.4 — 두 시뮬 대조와 부동소수점 주입 실험.
function M.cmd_lockstep(ticks)
    ticks = ticks or 300
    local out = {}
    local a, sc = scenario(ticks)
    local b, sc2 = scenario(ticks)
    local same = true
    for t = 1, ticks do
        local ha = a:step(a:script_orders(sc, t))
        local hb = b:step(b:script_orders(sc2, t))
        if ha ~= hb then
            same = false
            out[#out + 1] = fmt('%d틱에서 갈렸다 %08X vs %08X', t, ha, hb)
            break
        end
    end
    if same then
        out[#out + 1] = fmt('락스텝 %d틱 일치', ticks)
    end
    local c, sc3 = scenario(ticks)
    local d, sc4 = scenario(ticks, true)
    local first_hash, first_tile = -1, -1
    for t = 1, ticks do
        local hc = c:step(c:script_orders(sc3, t))
        local hd = d:step(d:script_orders(sc4, t))
        if first_hash < 0 and hc ~= hd then
            first_hash = t
        end
        if first_tile < 0 then
            local diff = false
            for i = 1, C.MAX_ENT - 1 do
                if c.w.alive[i] ~= d.w.alive[i] or c.w.tx[i] ~= d.w.tx[i]
                   or c.w.ty[i] ~= d.w.ty[i] then
                    diff = true
                    break
                end
            end
            if diff then first_tile = t end
        end
    end
    out[#out + 1] = fmt('float_bug: 해시가 갈린 틱 %d · 타일 좌표가 갈린 틱 %d',
                        first_hash, first_tile)
    out[#out + 1] = fmt('타일이 -1 이면 %d틱 동안 화면에서는 같아 보였다는 뜻이다',
                        ticks)
    return table.concat(out, '\n') .. '\n'
end

--- §20.2 — **상태는 한 바이트도 저장하지 않는다.** 명령이 없는 틱은 아예 적지
--- 않고, 재생은 머리의 총 틱 수만큼 돌면서 해당 틱에만 명령을 먹인다.
function M.cmd_replay(path, ticks)
    local s, sc, n = scenario(ticks)
    local log = {n = 0}
    for t = 1, n do
        local orders = s:script_orders(sc, t)
        if orders.n > 0 then
            log[log.n] = {t, orders}
            log.n = log.n + 1
        end
        s:step(orders)
    end
    local blob = RP.save(1, sc.players, n, log)
    local f = assert(io.open(path, 'wb'))
    f:write(blob)
    f:close()
    local seed, players, tk, log2 = RP.load(blob)
    local s2 = SIM.new(T.load_text(golden('map_start.txt')), seed, players)
    s2:setup_start(false)                -- 원본과 같은 조건이어야 한다
    local at = {}
    local nord = 0
    for k = 0, log2.n - 1 do
        at[log2[k][1]] = log2[k][2]
        nord = nord + log2[k][2].n
    end
    for t = 1, tk do
        s2:step(at[t] or {n = 0})
    end
    local same = s2:state_hash() == s:state_hash()
    return fmt('리플레이 %d바이트 · %d틱 · 명령 %d줄 · 재생 해시 %08X %s\n',
               #blob, tk, nord, s2:state_hash(), same and '일치' or '불일치')
end

function M.cmd_bench()
    local out = {}
    local ms = maps()
    local t0 = os.clock()
    for _ = 1, 20 do
        for i = 0, ms.n - 1 do
            local m = ms[i]
            for k = 0, m.pairs.n - 1 do
                P.astar(m, 0, m.pairs[k][0], m.pairs[k][1])
            end
        end
    end
    out[#out + 1] = fmt('1. A* %d회 %.3f초', 20 * 6 * 4, os.clock() - t0)
    t0 = os.clock()
    for _ = 1, 20 do
        for i = 0, ms.n - 1 do
            local m = ms[i]
            for k = 0, m.pairs.n - 1 do
                JP.search(m, 0, m.pairs[k][0], m.pairs[k][1])
            end
        end
    end
    out[#out + 1] = fmt('2. JPS %d회 %.3f초', 20 * 6 * 4, os.clock() - t0)
    local m = T.load_text(golden('map_start.txt'))
    t0 = os.clock()
    for _ = 1, 5 do
        FL.integration(m, 0, lst(pt(32, 32)))
    end
    out[#out + 1] = fmt('3. 흐름장 5회 %.3f초', os.clock() - t0)
    t0 = os.clock()
    local s, sc = scenario(200)
    for t = 1, 200 do
        s:step(s:script_orders(sc, t))
    end
    out[#out + 1] = fmt('4. 시뮬 200틱 %.3f초', os.clock() - t0)
    local pal = RS.build_palette()
    t0 = os.clock()
    RS.build_light(pal)
    out[#out + 1] = fmt('5. 명암표 1회 %.3f초', os.clock() - t0)
    local fb = RS.newframe()
    local light = RS.build_light(pal)
    t0 = os.clock()
    for _ = 1, 10 do
        RD.draw(fb.fb, s, RD.newview(), 0, pal, light, 0, {n = 0}, '')
    end
    out[#out + 1] = fmt('6. 렌더 10프레임 %.3f초', os.clock() - t0)
    return table.concat(out, '\n') .. '\n'
end

function M.cmd_speaker(path)
    local notes = {n = 4}
    local idx = {0, 4, 7, 12}
    for k = 1, 4 do notes[k - 1] = {SK.NOTE_HZ[idx[k]], 2200} end
    local blob = SK.tune(notes)
    local f = assert(io.open(path, 'wb'))
    f:write(blob)
    f:close()
    return fmt('%s — %d바이트 · FNV %08X\n', path, #blob, F.fnv1a(blob))
end

function M.main(argv)
    if argv[1] == nil then
        io.write('부명령: prim trace hashes aigame render lockstep'
                 .. ' replay bench speaker\n')
        return 1
    end
    local cmd = argv[1]
    local n1 = argv[2] and tonumber(argv[2]) or nil
    if cmd == 'prim' then
        io.write(M.cmd_prim())
    elseif cmd == 'trace' then
        io.write(M.cmd_trace(n1))
    elseif cmd == 'aigame' then
        io.write(M.cmd_aigame(n1 or 1200, false))
    elseif cmd == 'aigame7' then
        io.write(M.cmd_aigame(n1 or 1200, true))
    elseif cmd == 'hashes' then
        io.write(M.cmd_hashes(n1))
    elseif cmd == 'render' then
        io.write(M.cmd_render(argv[2], argv[3] and tonumber(argv[3]) or 1))
    elseif cmd == 'lockstep' then
        io.write(M.cmd_lockstep(n1 or 300))
    elseif cmd == 'replay' then
        io.write(M.cmd_replay(argv[2], argv[3] and tonumber(argv[3]) or nil))
    elseif cmd == 'bench' then
        io.write(M.cmd_bench())
    elseif cmd == 'speaker' then
        io.write(M.cmd_speaker(argv[2]))
    else
        io.write(fmt('모르는 부명령: %s\n', cmd))
        return 1
    end
    return 0
end

-- 스크립트로 직접 실행할 때만 main 을 돈다 (require 로 불러도 안전하게).
if arg ~= nil and arg[0] ~= nil and arg[0]:match('main%.lua$') then
    os.exit(M.main(arg))
end

return M
