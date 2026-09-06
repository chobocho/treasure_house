-- 난수 — 볼랜드 계열 LCG 하나 (SPEC §3).
--
--    짧은 파일이지만 세 언어를 건너는 지점이 둘 있다.
--      · 22695477 * s 는 최대 2^56 이라 53비트 가수에 담기지 않는다 → 분할 곱
--      · 나머지만 쓰면 모듈로 편향이 생긴다 → 기각 표본추출
--
--    시뮬레이션은 이 인스턴스를 **정확히 하나** 갖는다(SPEC §3.3). 렌더나 UI 가
--    난수를 뽑는 순간 두 기계의 수열이 갈리고, 그 뒤로 모든 것이 어긋난다.

local M = {}

local floor = math.floor

local A = 22695477
local M32 = 4294967296
M.A = A
M.M32 = M32

--- 상태는 32비트 부호 없는 정수 하나다.
local LCG = {}
LCG.__index = LCG
M.LCG = LCG

function M.new(seed)
    return setmetatable({s = seed % M32, rejects = 0}, LCG)
end
LCG.new = M.new

-- ── SPEC §3.1 ───────────────────────────────────────────────────────────────

--- 상태를 한 번 굴리고 상위 15비트(비트 30..16)를 돌려준다.
--
--    하위 비트는 주기가 짧다 — 최하위 비트는 0,1,0,1 을 반복한다. 그래서
--    rand() 가 돌려주는 것도 상위 비트다.
function LCG:next15()
    local s = self.s
    local sh = floor(s / 65536)
    local sl = s % 65536
    local lo = A * sl                    -- < 2^41
    local hi = (A * sh) % 65536          -- < 2^16
    self.s = (lo + hi * 65536 + 1) % M32
    return floor(self.s / 65536) % 32768
end

-- ── SPEC §3.2 ───────────────────────────────────────────────────────────────

--- 0 <= 결과 < n 인 균등 난수. 기각 루프도 결정론적이다.
function LCG:roll(n)
    if n <= 1 then
        return 0
    end
    local limit = 32768 - 32768 % n
    while true do
        local r = self:next15()
        if r < limit then
            return r % n
        end
        self.rejects = self.rejects + 1
    end
end

function LCG:save()
    return self.s
end

function LCG:load(s)
    self.s = s % M32
end

return M
