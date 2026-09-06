-- 저장 — CRC 검증값, 왕복, 손상 검출.

local H = require("tests.harness")
local G = require("isorpg.game")
local S = require("isorpg.save")
local F = require("isorpg.fixed")

H.title('save')

H.check('crc16 빈 입력', S.crc16(''), 0xFFFF)
H.check('crc16 "123456789"', S.crc16('123456789'), 0x29B1)
H.check('crc16 "A"', S.crc16('A'), 0xB915)
local b16 = {}
for i = 0, 15 do b16[i + 1] = i end
H.check('crc16 0x00..0F', S.crc16(b16), 0x3B37)
H.check('표 크기', #S.CRC_TBL, 256)
H.check('표 앞 4개',
        {S.CRC_TBL[1], S.CRC_TBL[2], S.CRC_TBL[3], S.CRC_TBL[4]},
        {0, 4129, 8258, 12387})

-- 한 비트만 바꿔도 값이 바뀌는가.
-- 루아 5.1 에는 ^= 가 없으니 fixed 의 산술 xor 를 쓴다.
local base = S.crc16('ISORPG-SAVE')
local diff = 0
for i = 1, 11 do
  for b = 0, 7 do
    local d = {}
    for k = 1, 11 do d[k] = ('ISORPG-SAVE'):byte(k) end
    d[i] = F.xor8(d[i], 2 ^ b)
    if S.crc16(d) ~= base then diff = diff + 1 end
  end
end
H.check('1비트 변화 88가지 모두 다른 CRC', diff, 88)

-- ---- 상태 왕복
local g = G.new_game()
for _ = 1, 30 do g:tick() end
local blob = S.pack_state(g)
H.check('매직', {blob[1], blob[2], blob[3], blob[4]}, {73, 83, 79, 49})
local head = {}
for i = 1, #blob - 2 do head[i] = blob[i] end
H.check_true('CRC 가 뒤에 붙는다',
             S.crc16(head) == blob[#blob - 1] * 256 + blob[#blob])

local g2 = G.new_game()
S.unpack_state(blob, g2)
H.check('왕복 후 다시 저장한 바이트가 같다', S.pack_state(g2), blob)
H.check('틱', g2.tick_n, g.tick_n)
H.check('난수 상태', g2.rng.s, g.rng.s)
H.check('플레이어 좌표', {g2.ents[1].fx, g2.ents[1].fy},
        {g.ents[1].fx, g.ents[1].fy})
H.check('안개', g2.fog.bits, g.fog.bits)

-- ---- 복원한 뒤 이어서 돌리면 같은 결과인가
for _ = 1, 20 do
  g:tick()
  g2:tick()
end
H.check('복원 후 20틱 진행 결과가 같다', S.pack_state(g2), S.pack_state(g))

-- ---- 손상 검출
local bad = {}
for i = 1, #blob do bad[i] = blob[i] end
bad[11] = F.xor8(bad[11], 0xFF)
local g3 = G.new_game()
local ok = pcall(function() S.unpack_state(bad, g3) end)
H.check('손상된 세이브를 거부', ok and 'no error' or 'error', 'error')

-- ---- 음수 좌표 (i32 2의 보수)
H.check('u32 왕복 -1', S.i32_to_u32(-1), 4294967295)
H.check('u32 왕복 -65536', S.u32_to_i32(S.i32_to_u32(-65536)), -65536)
H.check('u32 왕복 최대', S.u32_to_i32(S.i32_to_u32(2147483647)), 2147483647)
H.check('u32 왕복 최소', S.u32_to_i32(S.i32_to_u32(-2147483648)), -2147483648)

H.done()
