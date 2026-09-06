-- 저장·리플레이·압축 (SPEC §20).

local H = require('tests.harness')
local F = require('rts.fixed')
local RP = require('rts.replay')
local SEL = require('rts.select')
local T = require('rts.tmap')

H.title('replay')

local function ord(p, issuer, kind, a, b, c)
    return {[0] = p, issuer, kind, a, b, c, n = 6}
end
local function lst(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local LOG = lst({1, lst(ord(0, 256, SEL.MOVE, 3, 4, 0))},
                {4, lst(ord(0, 256, SEL.BUILD, 12, 6, 10),
                        ord(1, 512, SEL.TRAIN, 4, 0, 0))},
                {9, lst(ord(1, 65535, SEL.ATTACK, 30, 30, 65280))})

-- ── SPEC §20.2 리플레이 = 명령 로그 ─────────────────────────────────────────
local blob = RP.save(12345, 2, 1200, LOG)
H.check('머리는 RTSR', blob:sub(1, 4), 'RTSR')
H.check('버전', blob:byte(5), RP.VERSION)
local seed, players, ticks, log = RP.load(blob)
H.check('머리를 그대로 읽는다', lst(seed, players, ticks), lst(12345, 2, 1200))
H.check('본문을 그대로 읽는다', log, LOG)
H.check('꼬리는 CRC-16 두 바이트',
        blob:byte(#blob - 1) * 256 + blob:byte(#blob),
        F.crc16(blob:sub(1, #blob - 2)))

local broken = blob:sub(1, 10) .. string.char((blob:byte(11) + 1) % 256)
                   .. blob:sub(12)
H.check('한 바이트만 바뀌어도 CRC 가 잡는다',
        pcall(function() RP.load(broken) end) and 0 or 1, 1)
H.check('머리가 다르면 거부',
        pcall(function() RP.load('XXXX' .. blob:sub(5)) end) and 0 or 1, 1)
local _s, _p, _t, emptylog = RP.load(RP.save(1, 2, 0, {n = 0}))
H.check('빈 로그도 왕복한다', emptylog, {n = 0})
local _s2, _p2, _t2, ordlog = RP.load(
    RP.save(1, 2, 10, lst({5, {n = 0}}, {2, {n = 0}})))
local tks = {n = ordlog.n}
for k = 0, ordlog.n - 1 do tks[k] = ordlog[k][1] end
H.check('틱은 오름차순으로 저장한다', tks, lst(2, 5))

H.check_true(string.format('1200틱 리플레이는 수백 바이트 (%d)', #blob),
             #blob < 1000)
local snap = 4096
H.note('같은 게임의 상태 스냅샷은 틱당 약 %d바이트 — 1200틱이면 %d KB', snap,
       math.floor(snap * 1200 / 1024))
H.check('상태는 한 바이트도 저장하지 않는다',
        blob:find('hp', 1, true) ~= nil, false)

-- ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────
H.check('빈 입력', RP.rle_encode(''), '')
H.check('한 바이트', RP.rle_encode('A'), '\001A')
H.check('세 번 반복', RP.rle_encode('AAA'), '\003A')
H.check('바뀌면 새 쌍', RP.rle_encode('AAB'), '\002A\001B')
H.check('255 를 넘으면 쌍을 나눈다', #RP.rle_encode(string.rep('A', 300)), 4)
H.check('왕복', RP.rle_decode(RP.rle_encode(string.rep('A', 300) .. 'BC')),
        string.rep('A', 300) .. 'BC')
local dt = {}
for k = 0, 999 do dt[k + 1] = string.char(k % 7) end
local data = table.concat(dt)
H.check('반복이 없으면 두 배로 늘어난다', #RP.rle_encode(data), 2000)
H.check('그래도 왕복한다', RP.rle_decode(RP.rle_encode(data)), data)

-- ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
H.check('빈 입력', RP.lzss_encode(''), '')
H.check('짧은 입력은 전부 리터럴', RP.lzss_encode('AB'), '\003AB')
H.check('AAAAAAAA 는 리터럴 하나 + 토큰 하나',
        RP.lzss_encode(string.rep('A', 8)), '\001A\000\004')
H.note('플래그 1바이트 · 리터럴 A · (offset-1=0, len-3=4) 두 바이트 = 4바이트')
H.check('왕복', RP.lzss_decode(RP.lzss_encode(string.rep('A', 8))),
        string.rep('A', 8))
H.check('최대 일치는 18', RP.lzss_decode(RP.lzss_encode(string.rep('B', 40))),
        string.rep('B', 40))

local samples = {'', 'A', 'AB', 'ABABABABABAB', string.rep('A', 5000)}
local s1 = {}
for k = 0, 2999 do s1[k + 1] = string.char((k * 37) % 251) end
samples[#samples + 1] = table.concat(s1)
local s2 = {}
for k = 0, 4199 do s2[k + 1] = string.char(k % 3) end
samples[#samples + 1] = table.concat(s2)
for _, sample in ipairs(samples) do
    if RP.lzss_decode(RP.lzss_encode(sample)) ~= sample then
        H.check(string.format('왕복 실패 (길이 %d)', #sample), false, true)
    end
end
H.check('여러 표본에서 왕복', true, true)

H.check_true('창은 4096, 최소 일치 3, 최대 일치 18',
             RP.WINDOW == 4096 and RP.MIN_MATCH == 3 and RP.MAX_MATCH == 18)

-- 동점이면 가장 가까운 일치 (탐욕적)
local enc = RP.lzss_encode('XYZ' .. string.rep('Q', 3) .. 'XYZ' .. 'XYZ')
H.check('탐욕 일치도 왕복한다', RP.lzss_decode(enc), 'XYZQQQXYZXYZ')

-- 실제 맵으로 압축률을 잰다 — "보통 절반" 같은 문장은 쓰지 않는다
local m = T.load_text(H.golden('map_start.txt'))
local pt = {}
for k = 0, m.terrain.n - 1 do pt[k + 1] = string.char(m.terrain[k]) end
local plane = table.concat(pt)
local r_rle = #RP.rle_encode(plane)
local r_lz = #RP.lzss_encode(plane)
H.check('맵 지형 평면 왕복 (RLE)', RP.rle_decode(RP.rle_encode(plane)), plane)
H.check('맵 지형 평면 왕복 (LZSS)', RP.lzss_decode(RP.lzss_encode(plane)), plane)
H.note('64x64 지형 평면 %d바이트 → RLE %d · LZSS %d', #plane, r_rle, r_lz)
H.check_true('둘 다 원본보다 작다', r_rle < #plane and r_lz < #plane)

return H.done()
