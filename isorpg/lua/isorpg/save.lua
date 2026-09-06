-- 세이브와 CRC — SPEC §11.
--
--   전부 빅 엔디언이다. 손으로 나눠 쓰면 어느 언어에서든 같은 바이트가 나온다.
--   루아 5.1 에는 string.pack 도, 비트 연산도, 바이트 배열도 없다.
--   그래서 세이브는 '0..255 숫자가 든 1-기반 배열'이고, xor 는 fixed 의 산술 xor 다.
--
-- 배열 규약: CRC_TBL 은 [i + 1] 로 읽는다(i = 0..255). 세이브 바이트열도 1-기반이라
--   파이썬의 data[-2], data[-1] 은 data[#data-1], data[#data] 이 된다.

local F = require("isorpg.fixed")

local floor = math.floor
local xor8, xor16 = F.xor8, F.xor16

local M = {}

M.CRC_POLY = 0x1021
M.CRC_INIT = 0xFFFF

-- CRC-16/CCITT-FALSE 표. GF(2) 위의 다항식 나눗셈이라 뺄셈이 곧 xor 다.
local CRC_TBL = {}
for i = 0, 255 do
  local c = i * 256
  for _ = 1, 8 do
    local hi = c >= 32768
    c = c * 2
    c = c - 65536 * floor(c / 65536)
    if hi then c = xor16(c, 0x1021) end
  end
  CRC_TBL[i + 1] = c
end
M.CRC_TBL = CRC_TBL

-- 표 구동 CRC. 문자열이든 바이트 배열이든 받는다 —
-- 루아에는 bytes 타입이 없어서 테스트는 문자열을, 세이브는 배열을 넘긴다.
-- (c*256) mod 65536 은 하위 바이트가 0 이라 8비트 xor 만으로 충분하다.
function M.crc16(data)
  local c = 0xFFFF
  local n, get
  if type(data) == 'string' then
    n = #data
    get = string.byte
  else
    n = #data
    get = function(d, i) return d[i] end
  end
  for i = 1, n do
    local ch = floor(c / 256)
    local t = CRC_TBL[xor8(ch, get(data, i)) + 1]
    c = xor8(c - ch * 256, floor(t / 256)) * 256 + (t - 256 * floor(t / 256))
  end
  return c
end

-- ---------------------------------------------------------------- 정수 인코딩
function M.i32_to_u32(v)
  return v - 4294967296 * floor(v / 4294967296)
end

function M.u32_to_i32(v)
  if v >= 2147483648 then return v - 4294967296 end
  return v
end

local function u8(out, v)
  out[#out + 1] = v - 256 * floor(v / 256)
end

local function u16(out, v)
  local h = floor(v / 256)
  out[#out + 1] = h - 256 * floor(h / 256)
  out[#out + 1] = v - 256 * floor(v / 256)
end

local function u32(out, v)
  v = v - 4294967296 * floor(v / 4294967296)
  out[#out + 1] = floor(v / 16777216)
  local a = floor(v / 65536)
  out[#out + 1] = a - 256 * floor(a / 256)
  local b = floor(v / 256)
  out[#out + 1] = b - 256 * floor(b / 256)
  out[#out + 1] = v - 256 * floor(v / 256)
end

M.u8, M.u16, M.u32 = u8, u16, u32

local Reader = {}
Reader.__index = Reader
M.Reader = Reader

function M.new_reader(d)
  return setmetatable({d = d, i = 1}, Reader)
end

function Reader:u8()
  local v = self.d[self.i]
  self.i = self.i + 1
  return v
end

function Reader:u16()
  return self:u8() * 256 + self:u8()
end

function Reader:u32()
  return self:u16() * 65536 + self:u16()
end

function Reader:i32()
  return M.u32_to_i32(self:u32())
end

M.MAGIC = {73, 83, 79, 49}          -- 'ISO1'

-- 게임 상태를 바이트 배열로. 끝에 CRC 2바이트가 붙는다.
function M.pack_state(g)
  local out = {73, 83, 79, 49}
  u32(out, g.tick_n)
  u32(out, g.rng.s)
  u32(out, M.i32_to_u32(g.cam_x))
  u32(out, M.i32_to_u32(g.cam_y))
  u16(out, #g.ents)
  for k = 1, #g.ents do
    local e = g.ents[k]
    u8(out, e.kind)
    u32(out, M.i32_to_u32(e.fx))
    u32(out, M.i32_to_u32(e.fy))
    u8(out, e.h)
    u16(out, e.hp)
    u16(out, e.maxhp)
    u8(out, e.lv)
    u32(out, e.xp)
    u8(out, e.atk)
    u8(out, e.dfn)
    u8(out, e.armor)
    u8(out, e.dirn)
    u8(out, e.alive)
  end
  -- 안개는 타일 4개에 1바이트. 2비트씩 접어 넣는다.
  local bits = g.fog.bits
  local n = g.fog.w * g.fog.h
  u16(out, floor((n + 3) / 4))
  local i = 0
  while i < n do
    local b = 0
    local p = 1
    for k = 0, 3 do
      local v = (i + k < n) and bits[i + k + 1] or 0
      b = b + (v - 4 * floor(v / 4)) * p
      p = p * 4
    end
    out[#out + 1] = b
    i = i + 4
  end
  u16(out, M.crc16(out))
  return out
end

-- 세이브를 게임에 되돌린다. CRC 가 맞지 않으면 오류다.
function M.unpack_state(data, g)
  for i = 1, 4 do
    if data[i] ~= M.MAGIC[i] then error('세이브 매직이 다르다') end
  end
  local want = data[#data - 1] * 256 + data[#data]
  local head = {}
  for i = 1, #data - 2 do head[i] = data[i] end
  if M.crc16(head) ~= want then
    error('세이브가 손상됐다 (CRC 불일치)')
  end
  local r = M.new_reader(data)
  r.i = 5
  g.tick_n = r:u32()
  g.rng.s = r:u32()
  g.cam_x = r:i32()
  g.cam_y = r:i32()
  local cnt = r:u16()
  if cnt ~= #g.ents then
    error(string.format('엔티티 수가 %d 여야 하는데 %d', #g.ents, cnt))
  end
  for k = 1, #g.ents do
    local e = g.ents[k]
    e.kind = r:u8()
    e.fx = r:i32()
    e.fy = r:i32()
    e.h = r:u8()
    e.hp = r:u16()
    e.maxhp = r:u16()
    e.lv = r:u8()
    e.xp = r:u32()
    e.atk = r:u8()
    e.dfn = r:u8()
    e.armor = r:u8()
    e.dirn = r:u8()
    e.alive = r:u8()
  end
  local nb = r:u16()
  local bits = g.fog.bits
  local n = g.fog.w * g.fog.h
  for j = 0, nb - 1 do
    local b = r:u8()
    local p = 1
    for k = 0, 3 do
      local i = j * 4 + k
      if i < n then
        local q = floor(b / p)
        bits[i + 1] = q - 4 * floor(q / 4)
      end
      p = p * 4
    end
  end
  -- 비트만 되돌리고 누적 개수를 그대로 두면, 되돌린 뒤의 트레이스가
  -- 복원된 상태의 함수가 아니게 된다. 개수는 비트에서 다시 센다.
  g.fog:recount()
  return g
end

return M
