-- 주사위와 전투 — SPEC §10.
--
--   분포는 합성곱으로 정확히 센다. 몬테카를로가 아니라 경우의 수다.
--
-- 배열 규약: dist(n,m) 이 돌려주는 배열은 1-기반이라 '합이 s 인 경우의 수'가
--   c[s + 1] 에 들어간다. 파이썬의 c[s] 와 자리가 하나 어긋나는 유일한 지점이니
--   합계·기대값을 셀 때 항상 (i-1) 을 합으로 쓴다.

local M = {}

-- n개의 m면 주사위 합 분포. O(n^2 * m) 시간. 총합은 정확히 m^n 이어야 한다.
function M.dist(n, m)
  local c = {1}                                   -- 0면 주사위: 합 0 이 1가지
  for _ = 1, n do
    local len = #c
    local c2 = {}
    for i = 1, len + m do c2[i] = 0 end
    for s = 0, len - 1 do
      local v = c[s + 1]
      if v ~= 0 then
        for f = 1, m do
          c2[s + f + 1] = c2[s + f + 1] + v
        end
      end
    end
    c = c2
  end
  return c
end

-- 실제 굴림. 난수 소비 순서가 명세의 일부다.
function M.roll(r, n, m)
  local t = 0
  for _ = 1, n do
    local v = r:next()
    t = t + (v - m * math.floor(v / m)) + 1
  end
  return t
end

-- 1d20 이 이 값 이상이면 명중.
function M.to_hit(atk, dfn)
  return 11 + dfn - atk
end

-- 20면 중 명중하는 눈의 수. 1은 언제나 실패, 20은 언제나 성공.
function M.p_hit(atk, dfn)
  local v = 21 - M.to_hit(atk, dfn)
  if v < 1 then return 1 end
  if v > 19 then return 19 end
  return v
end

-- (명중 여부, 피해, 굴림). 빗나가면 피해 0.
-- 빗나갔을 때 피해 굴림을 건너뛰는 것까지 명세다 — 안 그러면 난수 흐름이 갈린다.
function M.attack(r, atk, dfn, dn, dm, dbonus, armor)
  local v = r:next()
  local d20 = (v - 20 * math.floor(v / 20)) + 1
  if d20 == 1 then return false, 0, d20 end
  if d20 ~= 20 and d20 < M.to_hit(atk, dfn) then return false, 0, d20 end
  local dmg = M.roll(r, dn, dm) + dbonus - armor
  if dmg < 1 then dmg = 1 end
  return true, dmg, d20
end

-- 다음 레벨까지 필요한 경험치. 2차식이라 후반이 완만하게 무거워진다.
function M.xp_to_next(lv)
  return 20 * lv * lv + 30 * lv
end

return M
