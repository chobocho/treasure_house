-- 원 마스크 — 정의와 증분 계산이 같은 집합인가 (SPEC §6).

local H = require('tests.harness')
local C = require('rts.circle')

H.title('circle')

-- ---- 전수 비교: r = 1..64 에서 정의와 span 계산이 같은 집합인가
local bad = 0
for r = 1, 64 do
    local want = {}
    local nwant = 0
    for y = -r, r do
        for x = -r, r do
            if x * x + y * y <= r * r then
                want[x .. ',' .. y] = true
                nwant = nwant + 1
            end
        end
    end
    local got = C.offsets(r)
    local same = (got.n == nwant)
    if same then
        for k = 0, got.n - 1 do
            if not want[got[k][0] .. ',' .. got[k][1]] then same = false; break end
        end
    end
    if not same then
        bad = bad + 1
        H.note('r=%d: 정의와 span 계산이 어긋난다 (기대 %d개 실제 %d개)',
               r, nwant, got.n)
    end
end
H.check('r=1..64 에서 disc_spans == {x²+y² <= r²}', bad, 0)

-- ---- 가우스 원 문제의 개수 (SPEC 정리 6.1)
local counts = {n = 8}
for r = 1, 8 do counts[r - 1] = C.offsets(r).n end
H.check('N(r), r=1..8', counts,
        {[0] = 5, 13, 29, 49, 81, 113, 149, 197, n = 8})

-- ---- 골든 6절과 대조
local rows = H.lines(H.golden('prim.txt'))
local i = H.index_of(rows, '== 6. 원 마스크 ==') + 2
bad = 0
for r = 1, 8 do
    local p = H.split(rows[i + r - 1])
    if tonumber(p[1]) ~= C.offsets(r).n then bad = bad + 1 end
    local want = {n = p.n - 2}
    for k = 2, p.n - 1 do want[k - 2] = tonumber(p[k]) end
    if not H.deep_eq(want, C.spans(r)) then
        bad = bad + 1
        H.note('r=%d span 기대 %s 실제 %s', r, H.repr(want), H.repr(C.spans(r)))
    end
end
H.check('개수·span 이 골든과 같다', bad, 0)

-- ---- 순회 순서가 고정인가 (SPEC §6.3)
local o = C.offsets(3)
H.check('첫 원소', o[0], {[0] = 0, [1] = -3, n = 2})
H.check('마지막 원소', o[o.n - 1], {[0] = 0, [1] = 3, n = 2})
local ordered = true
for k = 0, o.n - 2 do
    local a, b = o[k], o[k + 1]
    if not (a[1] < b[1] or (a[1] == b[1] and a[0] <= b[0])) then ordered = false end
end
H.check_true('dy 오름차순, 같은 dy 안에서 dx 오름차순', ordered)

-- ---- 곱셈을 쓰지 않는가 (span 계산은 덧셈만)
H.check('spans(8)', C.spans(8), {[0] = 8, 7, 7, 7, 6, 6, 5, 3, 0, n = 9})
H.check('in_disc(3,3,5)', C.in_disc(3, 3, 5), true)
H.check('in_disc(4,4,5)', C.in_disc(4, 4, 5), false)

-- ---- 고전 미드포인트 외곽선은 원 밖의 점을 찍는다 (SPEC §6.2)
local out = C.midpoint_outline(2)
H.check_true('r=2 외곽선에 (2,1) 이 있다', out['2,1'])
H.check_true('그런데 (2,1) 은 원 밖이다', 2 * 2 + 1 * 1 > 2 * 2)
H.note('그래서 시야 마스크에 외곽선 알고리즘을 쓰면 개수가 가우스 값과 어긋난다')

-- ---- 캐시가 같은 객체를 돌려주되 내용이 바뀌지 않는가
H.check('offsets 는 매번 같은 목록', C.offsets(5), C.offsets(5))

return H.done()
