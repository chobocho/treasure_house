-- 원 마스크 — 시야·스플래시·자원 스탬프가 전부 이것을 쓴다 (SPEC §6).
--
--    고전 미드포인트 원 알고리즘은 여기에 쓰지 않는다. 그것은 *외곽선*을 그리는
--    알고리즘이라 참원에 가장 가까운 점을 고르고, 그 점이 원 안이라는 보장이 없다.
--    r=2 에서 (2,1) 을 찍는데 2²+1² = 5 > 4 다. 시야 마스크로 쓰면 격자점 개수가
--    가우스 원 문제의 값과 어긋난다 — 골든을 처음 만들 때 그 검사가 잡았다.

local M = {}

local span_cache = {}
local off_cache = {}

--- span[j] = 행 j 에서 원 안에 드는 최대 |i|. 덧셈과 뺄셈만 쓴다.
--
--    불변식은 t = r² − j² − x² >= 0 이고 x 가 그 조건을 만족하는 최대값이다.
--    x 는 결코 늘지 않으므로 전체 비용이 O(r) 이다 (SPEC 정리 6.2).
function M.spans(r)
    local c = span_cache[r]
    if c then return c end
    local out = {n = r + 1}
    for j = 0, r do out[j] = 0 end
    out[0] = r
    local x, t = r, 0
    for j = 1, r do
        t = t - (2 * (j - 1) + 1)
        while t < 0 do
            t = t + 2 * x - 1
            x = x - 1
        end
        out[j] = x
    end
    span_cache[r] = out
    return out
end

--- (dx, dy) 목록. dy 오름차순, 같은 dy 안에서 dx 오름차순으로 **고정**한다.
--
--    순서가 다르면 참조 카운트 결과는 같지만 이벤트 로그의 순서가 달라지고,
--    그 차이가 상태 해시를 가른다(SPEC §6.3).
--
--    한 점은 {[0]=dx, [1]=dy} 인 2원소 배열이다 — 세 언어가 같은 모양을 갖도록
--    사전이 아니라 배열로 둔다.
function M.offsets(r)
    local c = off_cache[r]
    if c then return c end
    local sp = M.spans(r)
    local out = {n = 0}
    for j = -r, r do
        local w = sp[j >= 0 and j or -j]
        for i = -w, w do
            out[out.n] = {[0] = i, [1] = j, n = 2}
            out.n = out.n + 1
        end
    end
    off_cache[r] = out
    return out
end

function M.count(r)
    return M.offsets(r).n
end

function M.in_disc(dx, dy, r)
    return dx * dx + dy * dy <= r * r
end

--- 고전 미드포인트 '외곽선' — 엔진은 쓰지 않는다. 6부의 대조용으로만 있다.
--- 집합은 'x,y' 키의 테이블로 돌려준다 (루아에는 튜플 집합이 없다).
function M.midpoint_outline(r)
    local pts = {}
    local x, y, d = r, 0, 1 - r
    while y <= x do
        local cand = {{x, y}, {y, x}, {-x, y}, {-y, x},
                      {x, -y}, {y, -x}, {-x, -y}, {-y, -x}}
        for _, p in ipairs(cand) do
            pts[p[1] .. ',' .. p[2]] = true
        end
        y = y + 1
        if d < 0 then
            d = d + 2 * y + 1
        else
            x = x - 1
            d = d + 2 * (y - x) + 1
        end
    end
    return pts
end

return M
