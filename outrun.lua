-- ============================================================================
--  OUTRUN-LÖVE  —  유사 3D(pseudo-3D) 아웃런 스타일 2D 레이싱 게임
--  LÖVE 11.x (love2d.org) 용 완전 동작 단일 파일 소스
--
--  실행:  love .        (이 파일이 main.lua 라는 이름으로 폴더에 있어야 함)
--         또는  love outrun.lua 가 아니라, 폴더째  love <폴더>  로 실행합니다.
--  조작:  ← → 방향키 = 좌우,  ↑ = 가속,  ↓ = 브레이크,  Space = 시점 리셋
--         R = 재시작,  Esc = 종료
--
--  렌더링 원리는 세그먼트 기반 유사 3D 투영입니다. 자세한 수학 모델은
--  동봉된 슬라이드(러브2D_아웃런_레이싱_게임.html)를 참고하세요.
-- ============================================================================

local W, H            -- 화면 크기 (love.load 에서 설정)

-- ─── 튜닝 상수 ──────────────────────────────────────────────────────────────
local ROAD_W          = 2000        -- 도로 절반 폭(월드 단위)
local SEG_LEN         = 200         -- 세그먼트 하나의 z 길이
local RUMBLE_LEN      = 3           -- 럼블/차선 색이 바뀌는 세그먼트 수
local LANES           = 3           -- 차선 수
local FOV             = 100         -- 시야각(도)
local CAM_HEIGHT      = 1000        -- 카메라(눈) 높이
local DRAW_DIST       = 300         -- 앞으로 그릴 세그먼트 수
local FOG_DENSITY     = 5           -- 안개 세기
local MAX_SPEED       = SEG_LEN * 60 -- 초당 최고 속도(세그먼트 60개/초)
local ACCEL           = MAX_SPEED / 5
local BRAKE           = -MAX_SPEED
local DECEL           = -MAX_SPEED / 5
local OFFROAD_DECEL   = -MAX_SPEED / 2
local OFFROAD_LIMIT   = MAX_SPEED / 4
local CENTRIFUGAL     = 0.3         -- 원심력 계수
local CAM_DEPTH                     -- 1/tan(fov/2), love.load 에서 계산

-- ─── 색 팔레트 (라이트/다크 교대) ──────────────────────────────────────────
local function rgb(r,g,b) return {r/255, g/255, b/255} end
local COLORS = {
  LIGHT = { road=rgb(105,105,105), grass=rgb(16,170,79),  rumble=rgb(255,255,255), lane=rgb(255,255,255) },
  DARK  = { road=rgb( 96, 96, 96), grass=rgb(12,150,70),  rumble=rgb(187, 25, 55) },
  START = { road=rgb(255,255,255), grass=rgb(16,170,79),  rumble=rgb(255,255,255) },
  FINISH= { road=rgb( 40, 40, 40), grass=rgb(16,170,79),  rumble=rgb( 40, 40, 40) },
}
local SKY_TOP = rgb(0x18,0x0a,0x3a)   -- 밤보라
local SKY_BOT = rgb(0xff,0x5a,0x8c)   -- 노을 핑크

-- ─── 게임 상태 ─────────────────────────────────────────────────────────────
local segments = {}
local trackLength = 0
local position = 0     -- 카메라의 z 위치(월드)
local playerX = 0      -- 도로중앙 기준 가로 위치(-1..1 이 도로폭)
local speed = 0
local cars = {}        -- 교통 차량
local sprites = {}      -- (도로변 오브젝트는 세그먼트에 부착)
local hud = { lap=1, time=0, best=nil }
local keys = {}

-- ─── 세그먼트 색 조회 ──────────────────────────────────────────────────────
local function findSegment(z)
  return segments[math.floor(z/SEG_LEN) % #segments + 1]
end

-- ─── 원근 투영: 월드 좌표 → 화면 좌표 ─────────────────────────────────────
-- p.world = {x,y,z}, cameraX/Y/Z 는 카메라 위치
local function project(p, camX, camY, camZ)
  p.camera.x = (p.world.x or 0) - camX
  p.camera.y = (p.world.y or 0) - camY
  p.camera.z = (p.world.z or 0) - camZ
  p.screen.scale = CAM_DEPTH / p.camera.z
  p.screen.x = math.floor((W/2) + (p.screen.scale * p.camera.x * W/2))
  p.screen.y = math.floor((H/2) - (p.screen.scale * p.camera.y * H/2))
  p.screen.w = math.floor(p.screen.scale * ROAD_W * W/2)
end

-- ─── 트랙 만들기 ───────────────────────────────────────────────────────────
local function lastY() return (#segments==0) and 0 or segments[#segments].p2.world.y end

local function addSegment(curve, y)
  local n = #segments
  local prevY = lastY()
  segments[n+1] = {
    index = n,
    p1 = { world={y=prevY, z=n*SEG_LEN}, camera={}, screen={} },
    p2 = { world={y=y,     z=(n+1)*SEG_LEN}, camera={}, screen={} },
    curve = curve,
    sprites = {}, cars = {},
    color = (math.floor(n/RUMBLE_LEN)%2==1) and COLORS.DARK or COLORS.LIGHT,
  }
end

local function easeIn(a,b,p)  return a + (b-a)*p*p end
local function easeInOut(a,b,p) return a + (b-a)*(-math.cos(p*math.pi)/2 + 0.5) end

local function addRoad(enter, hold, leave, curve, y)
  local startY = lastY()
  local endY   = startY + (y or 0) * SEG_LEN
  local total  = enter + hold + leave
  for i=0,enter-1 do addSegment(easeIn(0,curve,i/enter),      easeInOut(startY,endY,i/total)) end
  for i=0,hold-1  do addSegment(curve,                        easeInOut(startY,endY,(enter+i)/total)) end
  for i=0,leave-1 do addSegment(easeInOut(curve,0,i/leave),   easeInOut(startY,endY,(enter+hold+i)/total)) end
end

local ROAD = { LENGTH={NONE=0,SHORT=25,MEDIUM=50,LONG=100},
               CURVE ={NONE=0,EASY=2,MEDIUM=4,HARD=6},
               HILL  ={NONE=0,LOW=20,MEDIUM=40,HIGH=60} }

local function buildTrack()
  segments = {}
  addRoad(50,50,50, 0, 0)                                   -- 출발 직선
  addRoad(30,30,30, ROAD.CURVE.EASY,   ROAD.HILL.LOW)
  addRoad(40,40,40, ROAD.CURVE.MEDIUM, -ROAD.HILL.MEDIUM)
  addRoad(30,30,30, -ROAD.CURVE.EASY,  ROAD.HILL.MEDIUM)
  addRoad(40,40,40, -ROAD.CURVE.HARD,   0)
  addRoad(20,20,20, 0,                 ROAD.HILL.HIGH)
  addRoad(40,40,40, ROAD.CURVE.MEDIUM, -ROAD.HILL.LOW)
  addRoad(30,30,30, ROAD.CURVE.EASY,   0)
  addRoad(50,50,50, 0,                 0)                   -- 도착 직선
  -- 출발/도착 색 표시
  segments[1].color = COLORS.START
  segments[2].color = COLORS.START
  for i=#segments-2,#segments do segments[i].color = COLORS.FINISH end
  trackLength = #segments * SEG_LEN

  -- 도로변 스프라이트(나무·야자수)를 좌우로 배치
  for i=20,#segments,5 do
    local side = (i%2==0) and -1 or 1
    local off  = 1.4 + (i%3)*0.6
    segments[i].sprites[#segments[i].sprites+1] = { offset = side*off, kind = (i%4==0) and 'palm' or 'tree' }
  end

  -- 교통 차량 배치
  cars = {}
  for i=1,20 do
    local seg = math.random(20, #segments-20)
    cars[i] = { offset = (math.random()*2-1)*0.7, z = seg*SEG_LEN,
                speed = MAX_SPEED*(0.25+math.random()*0.35),
                color = rgb(math.random(80,255),math.random(80,255),math.random(80,255)) }
    segments[seg].cars[#segments[seg].cars+1] = cars[i]
  end
end

-- ─── 폴리곤·직사각형 헬퍼 ──────────────────────────────────────────────────
local function quad(x1,y1,x2,y2,x3,y3,x4,y4,col)
  love.graphics.setColor(col)
  love.graphics.polygon('fill', x1,y1, x2,y2, x3,y3, x4,y4)
end

local function fog(d, density)      -- d: 0(가까움)~1(멈)
  return math.exp(-density * d * d)
end
local function mix(a,b,t)           -- 두 색 보간
  return { a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t, a[3]+(b[3]-a[3])*t }
end

-- ─── 세그먼트 하나 렌더 ────────────────────────────────────────────────────
local function renderSegment(seg, fogAmt)
  local c = seg.color
  local p1,p2 = seg.p1.screen, seg.p2.screen
  local grass = fogAmt < 1 and mix(SKY_BOT, c.grass, fogAmt) or c.grass
  -- 잔디(전체 폭)
  quad(0,p1.y, W,p1.y, W,p2.y, 0,p2.y, grass)
  -- 럼블
  local r1,r2 = p1.w/6, p2.w/6
  quad(p1.x-p1.w-r1,p1.y, p1.x-p1.w,p1.y, p2.x-p2.w,p2.y, p2.x-p2.w-r2,p2.y, mix(SKY_BOT,c.rumble,fogAmt))
  quad(p1.x+p1.w+r1,p1.y, p1.x+p1.w,p1.y, p2.x+p2.w,p2.y, p2.x+p2.w+r2,p2.y, mix(SKY_BOT,c.rumble,fogAmt))
  -- 도로
  quad(p1.x-p1.w,p1.y, p1.x+p1.w,p1.y, p2.x+p2.w,p2.y, p2.x-p2.w,p2.y, mix(SKY_BOT,c.road,fogAmt))
  -- 차선(라이트 색 세그먼트에만)
  if c.lane then
    local lw1 = p1.w/40*2/LANES*0 + p1.w*0.02
    local lw2 = p2.w*0.02
    for l=1,LANES-1 do
      local lx1 = p1.x - p1.w + (p1.w*2)*(l/LANES)
      local lx2 = p2.x - p2.w + (p2.w*2)*(l/LANES)
      quad(lx1-lw1,p1.y, lx1+lw1,p1.y, lx2+lw2,p2.y, lx2-lw2,p2.y, mix(SKY_BOT,c.lane,fogAmt))
    end
  end
end

-- ─── 도로변 스프라이트/차량(빌보드) 렌더 ──────────────────────────────────
local function drawTree(cx, baseY, scale, fogAmt)
  local h = scale*260
  if h < 2 then return end
  local trunkW = math.max(2, h*0.12)
  love.graphics.setColor(mix(SKY_BOT, rgb(70,45,30), fogAmt))
  love.graphics.rectangle('fill', cx-trunkW/2, baseY-h*0.35, trunkW, h*0.35)
  love.graphics.setColor(mix(SKY_BOT, rgb(18,120,60), fogAmt))
  love.graphics.polygon('fill', cx,baseY-h, cx-h*0.35,baseY-h*0.30, cx+h*0.35,baseY-h*0.30)
end
local function drawPalm(cx, baseY, scale, fogAmt)
  local h = scale*320
  if h<2 then return end
  love.graphics.setColor(mix(SKY_BOT, rgb(60,40,26), fogAmt))
  love.graphics.setLineWidth(math.max(2,h*0.05))
  love.graphics.line(cx, baseY, cx-h*0.08, baseY-h)
  love.graphics.setColor(mix(SKY_BOT, rgb(30,140,70), fogAmt))
  local tx,ty = cx-h*0.08, baseY-h
  for a=-2,2 do love.graphics.line(tx,ty, tx+a*h*0.14, ty+math.abs(a)*h*0.10 - h*0.06) end
end
local function drawCar(cx, baseY, scale, col, fogAmt)
  local w = scale*ROAD_W*W/2 * 0.00110
  local wpx = math.max(4, scale*260)
  local hpx = wpx*0.6
  love.graphics.setColor(mix(SKY_BOT, col, fogAmt))
  love.graphics.rectangle('fill', cx-wpx/2, baseY-hpx, wpx, hpx, wpx*0.12)
  love.graphics.setColor(mix(SKY_BOT, rgb(20,20,25), fogAmt))
  love.graphics.rectangle('fill', cx-wpx*0.35, baseY-hpx*0.85, wpx*0.7, hpx*0.4)
  love.graphics.setColor(mix(SKY_BOT, rgb(255,40,40), fogAmt))
  love.graphics.rectangle('fill', cx-wpx*0.42, baseY-hpx*0.18, wpx*0.14, hpx*0.14)
  love.graphics.rectangle('fill', cx+wpx*0.28, baseY-hpx*0.18, wpx*0.14, hpx*0.14)
end

-- ─── 배경(하늘·노을·산) ───────────────────────────────────────────────────
local skyMesh
local function drawBackground(baseCurve)
  -- 하늘 그라디언트
  local steps=40
  for i=0,steps-1 do
    local t=i/steps
    love.graphics.setColor(mix(SKY_TOP,SKY_BOT,t))
    love.graphics.rectangle('fill', 0, H*0.62*t, W, H*0.62/steps+1)
  end
  -- 태양
  love.graphics.setColor(1,0.78,0.30)
  love.graphics.circle('fill', W/2 - baseCurve*W*0.15, H*0.42, H*0.16)
  -- 먼 산 실루엣(패럴랙스)
  love.graphics.setColor(0.36,0.13,0.30)
  local off = -baseCurve*W*0.25
  love.graphics.polygon('fill', 0,H*0.6, off+W*0.2,H*0.42, off+W*0.4,H*0.58,
                        off+W*0.6,H*0.40, off+W*0.85,H*0.56, W,H*0.46, W,H*0.62, 0,H*0.62)
end

-- ─── 메인 렌더 ─────────────────────────────────────────────────────────────
local function render()
  local baseSeg = findSegment(position)
  local basePercent = (position % SEG_LEN)/SEG_LEN
  local camH = CAM_HEIGHT + baseSeg.p1.world.y
    + (baseSeg.p2.world.y - baseSeg.p1.world.y)*basePercent
  local maxy = H
  local x, dx = 0, -(baseSeg.curve * basePercent)

  drawBackground(baseSeg.curve)

  -- 앞쪽 세그먼트: 뒤에서 앞으로 투영·그리기
  for n=0,DRAW_DIST-1 do
    local seg = segments[(baseSeg.index + n) % #segments + 1]
    local looped = seg.index < baseSeg.index
    local camZ = position - (looped and trackLength or 0)
    local fogAmt = fog(n/DRAW_DIST, FOG_DENSITY)

    project(seg.p1, playerX*ROAD_W - x,      camH, camZ)
    project(seg.p2, playerX*ROAD_W - x - dx, camH, camZ)
    x  = x + dx
    dx = dx + seg.curve

    if seg.p1.camera.z <= CAM_DEPTH        -- 카메라 뒤
       or seg.p2.screen.y >= seg.p1.screen.y  -- 뒤집힘
       or seg.p2.screen.y >= maxy then       -- 이미 가려짐
      -- skip
    else
      renderSegment(seg, fogAmt)
      maxy = seg.p2.screen.y
    end
    seg._fog = fogAmt
    seg._drawn = not (seg.p1.camera.z <= CAM_DEPTH)
  end

  -- 스프라이트·차량: 앞에서 뒤로(painter) 그려 원근 겹침 처리
  for n=DRAW_DIST-1,0,-1 do
    local seg = segments[(baseSeg.index + n) % #segments + 1]
    if seg._drawn then
      for _,sp in ipairs(seg.sprites) do
        local sc = seg.p1.screen.scale
        local sx = seg.p1.screen.x + sc*sp.offset*ROAD_W*W/2
        local by = seg.p1.screen.y
        if sp.kind=='palm' then drawPalm(sx,by,sc,seg._fog) else drawTree(sx,by,sc,seg._fog) end
      end
      for _,car in ipairs(seg.cars) do
        local sc = seg.p1.screen.scale
        local sx = seg.p1.screen.x + sc*car.offset*ROAD_W*W/2
        drawCar(sx, seg.p1.screen.y, sc, car.color, seg._fog)
      end
    end
  end
end

-- ─── 플레이어 차 그리기(화면 하단 고정) ────────────────────────────────────
local function drawPlayer()
  local cx, by = W/2 + playerX*W*0.12, H*0.92
  local bounce = (speed>0) and math.sin(position*0.02)*2 or 0
  by = by + bounce
  local w = H*0.20
  love.graphics.setColor(rgb(230,30,40))
  love.graphics.rectangle('fill', cx-w/2, by-w*0.55, w, w*0.55, w*0.10)
  love.graphics.setColor(rgb(20,20,28))
  love.graphics.rectangle('fill', cx-w*0.30, by-w*0.50, w*0.60, w*0.28)
  love.graphics.setColor(rgb(15,15,18))
  love.graphics.rectangle('fill', cx-w*0.55, by-w*0.20, w*0.16, w*0.22, 3)
  love.graphics.rectangle('fill', cx+w*0.39, by-w*0.20, w*0.16, w*0.22, 3)
end

-- ─── HUD ───────────────────────────────────────────────────────────────────
local function drawHUD()
  love.graphics.setColor(1,1,1)
  local kmh = math.floor(speed/MAX_SPEED*300)
  love.graphics.print(('SPEED  %3d km/h'):format(kmh), 16, 14)
  love.graphics.print(('LAP    %d'):format(hud.lap), 16, 34)
  love.graphics.print(('TIME   %5.1f'):format(hud.time), 16, 54)
  if hud.best then love.graphics.print(('BEST   %5.1f'):format(hud.best), 16, 74) end
  -- 속도 게이지
  local gw=W-32
  love.graphics.setColor(0.2,0.2,0.25); love.graphics.rectangle('fill',16,H-24,gw,10)
  love.graphics.setColor(1,0.5,0.2);    love.graphics.rectangle('fill',16,H-24,gw*(speed/MAX_SPEED),10)
end

-- ============================================================================
--  LÖVE 콜백
-- ============================================================================
function love.load()
  love.window.setMode(900, 540, {resizable=true, minwidth=320, minheight=240})
  love.graphics.setDefaultFilter('nearest','nearest')
  W,H = love.graphics.getDimensions()
  CAM_DEPTH = 1 / math.tan((FOV/2)*math.pi/180)
  math.randomseed(os.time())
  buildTrack()
  position, playerX, speed = 0,0,0
  hud = {lap=1, time=0, best=nil}
end

function love.resize(w,h) W,H = w,h end

function love.keypressed(k)
  if k=='escape' then love.event.quit() end
  if k=='r' then love.load() end
  if k=='space' then playerX = 0 end
end

function love.update(dt)
  dt = math.min(dt, 1/30)
  local seg = findSegment(position + CAM_DEPTH)   -- 살짝 앞을 봄
  local speedPct = speed/MAX_SPEED
  hud.time = hud.time + dt

  -- 입력
  keys.left  = love.keyboard.isDown('left')
  keys.right = love.keyboard.isDown('right')
  keys.up    = love.keyboard.isDown('up')
  keys.down  = love.keyboard.isDown('down')

  if keys.up then speed = speed + ACCEL*dt
  elseif keys.down then speed = speed + BRAKE*dt
  else speed = speed + DECEL*dt end

  -- 조향(속도에 비례)
  local dx = dt * 2 * speedPct
  if keys.left  then playerX = playerX - dx end
  if keys.right then playerX = playerX + dx end
  -- 원심력: 곡선에서 바깥으로 밀림
  playerX = playerX - (dx * speedPct * seg.curve * CENTRIFUGAL)

  -- 오프로드 감속
  if (playerX < -1 or playerX > 1) and speed > OFFROAD_LIMIT then
    speed = speed + OFFROAD_DECEL*dt
  end

  playerX = math.max(-2, math.min(2, playerX))
  speed   = math.max(0, math.min(speed, MAX_SPEED))

  -- 교통 차량과 충돌
  local pseg = findSegment(position)
  for _,car in ipairs(pseg.cars) do
    if speed > car.speed then
      if math.abs(playerX - car.offset) < 0.5 then
        speed = car.speed * 0.5
      end
    end
  end

  -- 전진 + 랩
  position = position + speed*dt
  while position >= trackLength do
    position = position - trackLength
    hud.lap = hud.lap + 1
    if not hud.best or hud.time < hud.best then hud.best = hud.time end
    hud.time = 0
  end
  while position < 0 do position = position + trackLength end
end

function love.draw()
  render()
  drawPlayer()
  drawHUD()
end
