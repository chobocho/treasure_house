-- love.graphics 스텁 — 그리는 대신 그리기 호출을 받아 적는다.
--
--   이 기계에는 OpenGL 이 없어 love.graphics 가 아예 뜨지 않는다. 그래서 LÖVE
--   프런트엔드의 스크린샷은 영영 찍을 수 없다. 없는 증거를 있는 척하지 않는 대신,
--   차선을 고른다 — "프런트엔드가 어떤 호출을 어떤 인자로, 어떤 순서로 내는가"와
--   "그때 텍스처에 올라가는 바이트가 엔진 프레임버퍼와 같은가"를 검사한다.
--   그림이 화면에 뿌려지는 마지막 한 걸음만 증명하지 못하고, 그 앞은 전부 확인된다.
--
--   luajit 만으로 돌아간다. love 전역을 이 표로 갈아 끼운 뒤 love/main.lua 를
--   불러들이면, main.lua 는 자기가 LÖVE 안에서 도는 줄 알고 평소대로 그린다.
--   쓰는 쪽은 tests/test_love_draw.lua 다.
--
--   루아 5.1 문법만 쓴다.

local floor = math.floor

local M = {}

-- ---------------------------------------------------------------- ImageData
--
--   LÖVE 의 ImageData 는 두 가지로 만들어진다.
--     · newImageData(w, h)                     -> 빈 것. setPixel 로 채운다.
--     · newImageData(w, h, 'rgba8', <바이트열>) -> 통째로. 11.0 에서 들어왔다.
--   두 길이 같은 픽셀을 냈는지 견주려면 표현을 하나로 모아야 한다.
--   그래서 rgba_bytes() 가 어느 쪽이든 256,000바이트 문자열을 돌려준다.
local ImageData = {}
ImageData.__index = ImageData

function ImageData:getWidth() return self.w end
function ImageData:getHeight() return self.h end
function ImageData:getFormat() return self.format end

function ImageData:setPixel(x, y, r, g, b, a)
  if x < 0 or y < 0 or x >= self.w or y >= self.h then
    error('setPixel 범위 밖: ' .. tostring(x) .. ',' .. tostring(y))
  end
  self.px[y * self.w + x + 1] = {r, g, b, a}
  self.set_count = self.set_count + 1
end

function ImageData:getPixel(x, y)
  local p = self.px[y * self.w + x + 1]
  if p then return p[1], p[2], p[3], p[4] end
  if self.data then
    local o = (y * self.w + x) * 4
    return string.byte(self.data, o + 1) / 255, string.byte(self.data, o + 2) / 255,
           string.byte(self.data, o + 3) / 255, string.byte(self.data, o + 4) / 255
  end
  return 0, 0, 0, 0
end

-- 0..1 실수 -> 0..255 바이트. LÖVE 가 내부에서 하는 반올림과 같은 규칙으로 맞춘다.
local function to_byte(v)
  if v == nil then return 0 end
  local n = floor(v * 255 + 0.5)
  if n < 0 then n = 0 elseif n > 255 then n = 255 end
  return n
end

function ImageData:rgba_bytes()
  if self.data then return self.data end
  local parts = {}
  local n = self.w * self.h
  for i = 1, n do
    local p = self.px[i]
    if p then
      parts[i] = string.char(to_byte(p[1]), to_byte(p[2]), to_byte(p[3]), to_byte(p[4]))
    else
      parts[i] = string.char(0, 0, 0, 0)
    end
  end
  return table.concat(parts)
end

-- ---------------------------------------------------------------- Image
local Image = {}
Image.__index = Image

function Image:getWidth() return self.w end
function Image:getHeight() return self.h end

-- ---------------------------------------------------------------- 레코더
--
--   opts.width / opts.height   창 크기 (love.graphics.getDimensions 가 돌려줄 값)
--   opts.source_base           love.filesystem.getSourceBaseDirectory 의 반환값
--                              (nil 이면 main.lua 가 부트스트랩을 건너뛴다)
--   opts.keys                  눌린 것으로 칠 키 이름 집합 {up = true, ...}
function M.new(opts)
  opts = opts or {}
  local rec = {
    calls = {},
    width = opts.width or 960,
    height = opts.height or 600,
    source_base = opts.source_base,
    keys = opts.keys or {},
    files = {},
    quit_code = nil,
    time = 0,
  }

  -- 호출 하나를 적는다. 인자는 그대로 담는다 — 값까지 검사해야 증거가 되기 때문이다.
  -- 조회 계열(getDimensions 등)도 빼지 않는다. 빼면 "그 프레임에 이것 말고는
  -- 아무것도 부르지 않았다"는 주장을 할 수 없다.
  --
  -- 다만 ImageData:setPixel 만은 목록에 남기지 않는다. 프레임 하나에 64,000개가
  -- 쌓여 나머지 호출이 파묻히기 때문이다. 대신 ImageData 자신이 set_count 로 센다.
  local function log(name, ...)
    local n = select('#', ...)
    local a = {}
    for i = 1, n do a[i] = (select(i, ...)) end
    a.n = n
    rec.calls[#rec.calls + 1] = {name = name, args = a}
    return rec.calls[#rec.calls]
  end
  rec.log = log

  function rec.reset()
    rec.calls = {}
  end

  -- 이름만 뽑는다. 순서 검사는 이 목록으로 한다.
  function rec.names()
    local out = {}
    for i = 1, #rec.calls do out[i] = rec.calls[i].name end
    return out
  end

  local function new_imagedata(w, h, format, data)
    local id = setmetatable({w = w, h = h, format = format or 'rgba8',
                             data = data, px = {}, set_count = 0}, ImageData)
    if data ~= nil and #data ~= w * h * 4 then
      error(string.format('rgba8 데이터가 %d바이트 (기대 %d)', #data, w * h * 4))
    end
    -- 반환값도 기록에 남긴다. "방금 만든 그 ImageData 가 그대로 텍스처에 올라갔는가"를
    -- 확인하려면 호출 인자만으로는 부족하다.
    log('love.image.newImageData', w, h, format, data).ret = id
    return id
  end

  local image = {
    newImageData = new_imagedata,
  }

  local graphics = {}

  function graphics.newImage(id)
    local img = setmetatable({w = id:getWidth(), h = id:getHeight(), source = id}, Image)
    log('love.graphics.newImage', id).ret = img
    -- 메서드는 인스턴스마다 걸어 준다. 레코더를 닫아 두면 여러 개를 만들어도 섞이지 않는다.
    function img:replacePixels(nid)
      self.source = nid
      log('Image:replacePixels', self, nid)
    end
    function img:setFilter(a, b)
      log('Image:setFilter', a, b)
    end
    return img
  end

  function graphics.draw(drawable, x, y, r, sx, sy)
    log('love.graphics.draw', drawable, x, y, r, sx, sy)
  end

  function graphics.getDimensions()
    log('love.graphics.getDimensions')
    return rec.width, rec.height
  end

  function graphics.getWidth() log('love.graphics.getWidth'); return rec.width end
  function graphics.getHeight() log('love.graphics.getHeight'); return rec.height end

  function graphics.setDefaultFilter(a, b) log('love.graphics.setDefaultFilter', a, b) end
  function graphics.setBackgroundColor(r, g, b) log('love.graphics.setBackgroundColor', r, g, b) end
  function graphics.setColor(r, g, b, a) log('love.graphics.setColor', r, g, b, a) end
  function graphics.clear(r, g, b, a) log('love.graphics.clear', r, g, b, a) end
  function graphics.present() log('love.graphics.present') end
  function graphics.isActive() return true end

  local keyboard = {}
  function keyboard.isDown(k) return rec.keys[k] == true end

  local filesystem = {}
  function filesystem.getSourceBaseDirectory() return rec.source_base end
  function filesystem.write(name, s) rec.files[name] = s; log('love.filesystem.write', name, #s); return true end
  function filesystem.read(name) return rec.files[name] end

  local event = {}
  function event.quit(code) rec.quit_code = code; log('love.event.quit', code) end

  local timer = {}
  function timer.getTime() return rec.time end
  function timer.step() return 0 end

  rec.love = {
    _version = '11.5',
    _version_major = 11,
    _version_minor = 5,
    graphics = graphics,
    image = image,
    keyboard = keyboard,
    filesystem = filesystem,
    event = event,
    timer = timer,
  }
  return rec
end

M.ImageData = ImageData
M.Image = Image
M.to_byte = to_byte

return M
