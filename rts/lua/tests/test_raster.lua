-- 래스터 — 팔레트·명암표·스프라이트·블릿·폰트·PPM (SPEC §22).

local H = require('tests.harness')
local C = require('rts.const')
local F = require('rts.fixed')
local RS = require('rts.raster')

H.title('raster')

local floor = math.floor
local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end
local function tolist(t)
    local out = {n = #t}
    for k = 1, #t do out[k - 1] = t[k] end
    return out
end

-- ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
local pal = RS.build_palette()
local glines = H.lines(H.golden('palette.txt'))
local bad = 0
local n = 0
for k = 0, glines.n - 1 do
    local ln = glines[k]
    if ln ~= '' and ln:sub(1, 1) ~= '#' then
        local p = H.split(ln)
        if p[0] ~= 'light' and p[0] ~= 'palette' then
            local i, r, gg, b = tonumber(p[0]), tonumber(p[1]), tonumber(p[2]),
                                tonumber(p[3])
            if not H.deep_eq(tolist(pal[i]), lst(r, gg, b)) then
                bad = bad + 1
                if bad < 4 then
                    H.note('%d 기대 %s 실제 %s', i, H.repr(lst(r, gg, b)),
                           H.repr(tolist(pal[i])))
                end
            end
            n = n + 1
        end
    end
end
H.check(string.format('골든 팔레트 %d색', n), bad, 0)
H.check('256색', pal.n, 256)
local mx, mn = 0, 999
for c = 0, 255 do
    for j = 1, 3 do
        if pal[c][j] > mx then mx = pal[c][j] end
        if pal[c][j] < mn then mn = pal[c][j] end
    end
end
H.check('성분은 0..63 (VGA DAC 6비트)', mx <= 63 and mn >= 0, true)
H.check('0번은 검정', tolist(pal[0]), lst(0, 0, 0))
H.check('회색 16단계의 끝', {[0] = tolist(pal[16]), tolist(pal[31]), n = 2},
        {[0] = lst(0, 0, 0), lst(63, 63, 63), n = 2})
H.check('플레이어 기준은 160', RS.PLAYER_BASE, 160)
local diffs = {n = 3}
for p = 0, 2 do
    diffs[p] = not H.deep_eq(pal[160 + p * 8], pal[160 + (p + 1) * 8])
end
H.check('플레이어 램프는 넷 × 8단계', diffs, lst(true, true, true))

local flat = {}
for c = 0, 255 do
    flat[#flat + 1] = string.char(pal[c][1], pal[c][2], pal[c][3])
end
local want
for k = 0, glines.n - 1 do
    if glines[k]:sub(1, 8) == 'palette ' then
        want = H.split(glines[k])[1]
    end
end
H.check('팔레트 전체 해시',
        string.format('0x%08X', F.fnv1a(table.concat(flat))), want)

local light = RS.build_light(pal)
H.check('명암 단계는 넷', light.n, 4)
local ident = {n = 0}
for c = 0, 255 do
    if light[3][c] ~= c and not H.deep_eq(pal[light[3][c]], pal[c]) then
        ident[ident.n] = c
        ident.n = ident.n + 1
    end
end
H.check('3단계는 원색 그대로 (같은 색이 둘이면 인덱스가 작은 쪽)', ident, {n = 0})
local same_all = true
for c = 0, 255 do
    if light[3][c] ~= c then same_all = false end
end
H.check_true('중복 색이 있어 항등은 아니다', not same_all)
H.check('0단계는 전부 검정 계열', light[0][100], 0)
bad = 0
for k = 0, glines.n - 1 do
    if glines[k]:sub(1, 6) == 'light ' then
        local p = H.split(glines[k])
        local l = tonumber(p[1])
        local bytes = {}
        for c = 0, 255 do bytes[c + 1] = string.char(light[l][c]) end
        if string.format('0x%08X', F.fnv1a(table.concat(bytes))) ~= p[2] then
            bad = bad + 1
        end
    end
end
H.check('명암표 네 단계의 해시', bad, 0)
H.note('256×256×4 = 262,144회 비교를 시작할 때 한 번 한다')

-- ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
H.check('expand(63) = 255', RS.expand(63), 255)
H.check('expand(0) = 0', RS.expand(0), 0)
local mono = true
for v = 0, 62 do
    if not (RS.expand(v) < RS.expand(v + 1)) then mono = false end
end
H.check('expand 는 단조', mono, true)
H.check('expand 는 v*4 + v//16',
        lst(RS.expand(1), RS.expand(16), RS.expand(32), RS.expand(47)),
        lst(4, 65, 130, 190))

local fb = RS.newframe()
H.check('프레임버퍼는 320x200 1차원', fb.fb.n, 320 * 200)
local fmx = 0
for i = 0, fb.fb.n - 1 do if fb.fb[i] > fmx then fmx = fb.fb[i] end end
H.check('처음에는 전부 0', fmx, 0)
fb.fb[0] = 63
local ppm = RS.to_ppm(fb.fb, pal)
H.check('PPM 은 192,015바이트', #ppm, 15 + 320 * 200 * 3)
H.check('머리', ppm:sub(1, 15), 'P6\n320 200\n255\n')
H.check('첫 픽셀은 팔레트 63번을 편 값',
        lst(ppm:byte(16), ppm:byte(17), ppm:byte(18)),
        lst(RS.expand(pal[63][1]), RS.expand(pal[63][2]),
            RS.expand(pal[63][3])))

-- ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
local slines = H.lines(H.golden('sprites.txt'))
bad = 0
local ns = 0
for k = 0, slines.n - 1 do
    local ln = slines[k]
    if ln ~= '' and ln:sub(1, 1) ~= '#' then
        local p = H.split(ln)
        local name = p[0]
        local spr = RS.SPRITES[name]
        local got = lst(spr.w, spr.h, spr.ox, spr.oy, #spr.data,
                        string.format('0x%08X', F.fnv1a(spr.data)))
        local wnt = lst(tonumber(p[1]), tonumber(p[2]), tonumber(p[3]),
                        tonumber(p[4]), tonumber(p[5]), p[6])
        if not H.deep_eq(got, wnt) then
            bad = bad + 1
            if bad < 4 then
                H.note('%s 기대 %s 실제 %s', name, H.repr(wnt), H.repr(got))
            end
        end
        ns = ns + 1
    end
end
H.check(string.format('골든 스프라이트 %d장', ns), bad, 0)
local nspr = 0
for _ in pairs(RS.SPRITES) do nspr = nspr + 1 end
H.check('유닛 25 + 건물 6', nspr, 31)
H.check('유닛 기준점은 발밑',
        lst(RS.SPRITES['INF_0'].ox, RS.SPRITES['INF_0'].oy), lst(8, 14))
H.check('사령부는 3x3 타일',
        lst(RS.SPRITES['HQ'].w, RS.SPRITES['HQ'].h), lst(48, 48))

local px = RS.SPRITES['INF_0']:pixels()
H.check('풀면 w*h 픽셀', px.n, 16 * 16)
H.check('0 은 투명 — 모서리는 비어 있다', px[0], 0)
H.check('몸통은 플레이어 색', px[9 * 16 + 8], RS.PLAYER_BASE + 3)

-- ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
local function count_pos(a)
    local c = 0
    for i = 0, a.n - 1 do if a[i] > 0 then c = c + 1 end end
    return c
end
local function maxof(a)
    local v = 0
    for i = 0, a.n - 1 do if a[i] > v then v = a[i] end end
    return v
end

local fb2 = RS.newframe()
RS.blit(fb2.fb, RS.SPRITES['INF_0'], 100, 100)
H.check_true('그려졌다', maxof(fb2.fb) > 0)
local drawn = count_pos(fb2.fb)
H.check('투명 픽셀은 건드리지 않는다', drawn, count_pos(px))

local fb3 = RS.newframe()
RS.blit(fb3.fb, RS.SPRITES['INF_0'], -100, 100)
H.check('완전히 화면 밖이면 한 픽셀도 안 쓴다', maxof(fb3.fb), 0)
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 400, 100)
H.check('오른쪽 밖도', maxof(fb3.fb), 0)
RS.blit(fb3.fb, RS.SPRITES['INF_0'], 100, -100)
H.check('위쪽 밖도', maxof(fb3.fb), 0)

local fb4 = RS.newframe()
RS.blit(fb4.fb, RS.SPRITES['INF_0'], 4, 100)     -- x0 = -4 — 네 칸이 화면 밖
local part = count_pos(fb4.fb)
H.check_true('걸치면 걸친 만큼만 그린다', part > 0 and part < drawn)
local leak = {n = 0}
for y = 0, 199 do
    for x = 12, 319 do
        if fb4.fb[y * 320 + x] > 0 then
            leak[leak.n] = 1
            leak.n = leak.n + 1
        end
    end
end
H.check('왼쪽 밖으로 새지 않는다', leak, {n = 0})

-- ── SPEC §22.5 플레이어 색 리맵 ─────────────────────────────────────────────
local fb5 = RS.newframe()
RS.blit(fb5.fb, RS.SPRITES['INF_0'], 100, 100, 2)
H.check('owner * 8 을 더한다', fb5.fb[(100 + 9 - 14) * 320 + (100 + 8 - 8)],
        RS.PLAYER_BASE + 16 + 3)
local has_shadow = false
for i = 0, fb5.fb.n - 1 do
    if fb5.fb[i] == RS.SHADOW then has_shadow = true; break end
end
H.check('그림자는 리맵하지 않는다', has_shadow, true)
H.note('색을 여덟 벌 그리지 않는다 — 도스 시절의 표준 요령이다')

-- ── SPEC §22.7 좌우 반전 ────────────────────────────────────────────────────
local fa = RS.newframe()
local fbb = RS.newframe()
RS.blit(fa.fb, RS.SPRITES['INF_1'], 100, 100)
RS.blit(fbb.fb, RS.SPRITES['INF_1'], 100, 100, 0, true)
local row_a, row_b, row_rev = {n = 16}, {n = 16}, {n = 16}
for k = 0, 15 do
    row_a[k] = fa.fb[(100 - 14 + 5) * 320 + 100 - 8 + k]
    row_b[k] = fbb.fb[(100 - 14 + 5) * 320 + 100 - 8 + k]
end
for k = 0, 15 do row_rev[k] = row_a[15 - k] end
H.check('반전은 각 줄을 뒤집는다', row_b, row_rev)
H.check('그리는 것은 5방향, 나머지 셋은 반전', RS.DRAWN_DIRS, 5)

-- ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
local p0 = RS.build_palette()
local p1 = RS.cycle_water(RS.build_palette(), 1)
local ch1, ch2 = {n = 0}, {n = 0}
for k = 0, 255 do
    if not H.deep_eq(p0[k], p1[k]) then
        ch1[ch1.n] = k
        ch1.n = ch1.n + 1
    end
end
for k = 232, 239 do
    if not H.deep_eq(p0[k], p1[k]) then
        ch2[ch2.n] = k
        ch2.n = ch2.n + 1
    end
end
H.check('물 색만 돈다', ch1, ch2)
H.check('한 칸 돈다', p1[232], p0[233])
H.check('끝은 처음으로', p1[239], p0[232])
H.check('8칸이면 제자리', RS.cycle_water(RS.build_palette(), 8), p0)
local zerofb = {n = 320 * 200}
for i = 0, 320 * 200 - 1 do zerofb[i] = 0 end
H.check('프레임버퍼는 건드리지 않는다 — 공짜 애니메이션', RS.newframe().fb, zerofb)

-- ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
local flines = H.lines(H.golden('font.txt'))
local fhex
for k = 0, flines.n - 1 do
    if flines[k] ~= '' and flines[k]:sub(1, 1) ~= '#' then
        fhex = flines[k]
        break
    end
end
H.check('폰트는 760바이트 (95자 × 8)', RS.FONT.n, 760)
local hx = {}
for k = 0, RS.FONT.n - 1 do hx[k + 1] = string.format('%02x', RS.FONT[k]) end
H.check('골든 폰트와 같다', table.concat(hx), fhex)
local fb6 = RS.newframe()
RS.text(fb6.fb, 'A', 0, 0, 15)
local rows = {}
for y = 0, 6 do
    local a = {}
    for x = 0, 5 do
        a[#a + 1] = (fb6.fb[y * 320 + x] ~= 0) and '#' or '.'
    end
    rows[y] = table.concat(a)
end
H.check('A 의 첫 줄', rows[0], '.###..')
H.check('A 의 넷째 줄', rows[3], '#####.')
RS.text(RS.newframe().fb, 'a', 0, 0, 15)
H.check('소문자는 빈 글자다 — 도스 UI 가 대문자만 쓴 이유와 같다', true, true)
local fb7 = RS.newframe()
RS.text(fb7.fb, 'AB', 0, 0, 15)
H.check('글자 간격은 6px', fb7.fb[0 * 320 + 6], 15)
RS.text(fb7.fb, 'ZZZZ', 318, 0, 15)
H.check('화면 밖 글자는 잘린다', true, true)

-- ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
local d = RS.newdirty()
H.check('처음에는 비어 있다', d:rects(), {n = 0})
d:add(10, 10, 4, 4)
H.check('하나', d:rects().n, 1)
for k = 0, 7 do d:add(k * 10, 0, 4, 4) end
H.check('8개를 넘으면 전체를 다시 그린다', d:rects(),
        {[0] = lst(0, 0, C.SCR_W, C.SCR_H), n = 1})
d:clear()
H.check('비우면 다시 처음', d:rects(), {n = 0})
H.note('합치는 비용이 이득을 넘는 지점은 out/bench.txt 6절에서 실측한다')

return H.done()
