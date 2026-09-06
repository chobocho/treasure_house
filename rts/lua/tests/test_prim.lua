-- `main prim` 이 골든을 바이트 단위로 재현하는가 (SPEC §24).
--
--    이 한 시험이 엔진 전체와 **독립 참조 구현**(tools/gen_prim.py)의 대조다.
--    앞선 시험들이 모듈을 따로 확인했다면, 이것은 열넷 절을 한꺼번에 맞춘다.

local H = require('tests.harness')
local MAIN = require('rts.main')

H.title('prim')

local prim = MAIN.cmd_prim()
local got = H.lines(prim)
local want = H.lines(H.golden('prim.txt'))

H.check('줄 수', got.n, want.n)
local bad = 0
local first = -1
local lim = got.n < want.n and got.n or want.n
for k = 0, lim - 1 do
    if got[k] ~= want[k] then
        bad = bad + 1
        if first < 0 then
            first = k
            H.note('%d행 기대 %s', k + 1, H.repr(want[k]))
            H.note('     실제 %s', H.repr(got[k]))
        end
    end
end
H.check(string.format('%d행 전부 일치', want.n), bad, 0)

local secs = {n = 0}
for k = 0, want.n - 1 do
    if want[k]:sub(1, 3) == '== ' then
        secs[secs.n] = want[k]
        secs.n = secs.n + 1
    end
end
H.check('절 구분은 14개', secs.n, 14)
local badend = {n = 0}
for k = 0, secs.n - 1 do
    if secs[k]:sub(-3) ~= ' ==' then
        badend[badend.n] = secs[k]
        badend.n = badend.n + 1
    end
end
H.check('절 표시 형식', badend, {n = 0})
H.check('덱 지시자가 자를 수 있는 형태', secs[0], '== 1. 거리 척도 ==')
H.check('출력은 줄바꿈으로 끝난다', prim:sub(-1), '\n')

-- 절 하나만 바뀌어도 잡히는가 — 시험 자체의 민감도 확인
local uniq = {}
local nuniq = 0
for k = 0, secs.n - 1 do
    if not uniq[secs[k]] then uniq[secs[k]] = true; nuniq = nuniq + 1 end
end
H.check_true('절마다 내용이 다르다', nuniq == 14)

return H.done()
