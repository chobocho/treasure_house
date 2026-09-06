-- 트레이스·해시·리플레이·락스텝 부명령 (SPEC §18.3, §19, §20, §24).

local H = require('tests.harness')
local MAIN = require('rts.main')

H.title('trace')

local N = 40

--- 마지막 빈 줄을 뺀 줄 목록 (파이썬의 split('\n')[:-1]).
local function lines_nolast(s)
    local a = H.lines(s)
    a.n = a.n - 1
    a[a.n] = nil
    return a
end

local tr = lines_nolast(MAIN.cmd_trace(N))
H.check('틱마다 한 줄', tr.n, N)
H.check('첫 줄의 틱', tr[0]:sub(1, 6), '{"t":1')
H.check('마지막 줄의 틱',
        tr[tr.n - 1]:sub(1, #string.format('{"t":%d,', N))
        == string.format('{"t":%d,', N), true)
local missing = {n = 0}
for _, k in ipairs({'"t":', '"h":', '"cr":', '"su":', '"sc":', '"n":', '"ev":'}) do
    if not tr[0]:find(k, 1, true) then
        missing[missing.n] = k
        missing.n = missing.n + 1
    end
end
H.check('키 순서가 명세대로', missing, {n = 0})
H.check('공백이 없다', tr[0]:find(' ', 1, true) ~= nil, false)
local nlower = 0
for k = 0, tr.n - 1 do
    local h = tr[k]:match('"h":"(%x+)"')
    if h:upper() ~= h then nlower = nlower + 1 end
end
H.check('해시는 8자리 대문자 16진', nlower, 0)
H.check('두 번 돌려도 같다', lines_nolast(MAIN.cmd_trace(N)), tr)

local hs = lines_nolast(MAIN.cmd_hashes(N))
H.check('해시 줄 수', hs.n, N)
H.check('형식은 "틱 해시"', H.split(hs[0])[0], '1')
local h1, h2 = {n = N}, {n = N}
local uniq, nuniq = {}, 0
for k = 0, N - 1 do
    h1[k] = H.split(hs[k])[1]
    h2[k] = tr[k]:match('"h":"(%x+)"')
    if not uniq[hs[k]] then uniq[hs[k]] = true; nuniq = nuniq + 1 end
end
H.check('트레이스의 해시와 같다', h1, h2)
H.check_true('해시가 변한다', nuniq == N)

local out = MAIN.cmd_lockstep(60)
H.check_true('락스텝 60틱 일치', out:find('락스텝 60틱 일치', 1, true) ~= nil)
H.check_true('float_bug 실험 결과가 한 줄 나온다',
             out:find('float_bug:', 1, true) ~= nil)
local ol = H.lines(H.strip(out))
H.note('%s', ol[ol.n - 2])

-- 골든 옆의 out/ 에 잠깐 쓴다. Makefile 이 이미 만들어 두지만 없을 수도 있다.
local base = '../out/'
local probe = io.open(base .. '.probe', 'wb')
if probe == nil then
    os.execute('mkdir -p ../out')
    probe = io.open(base .. '.probe', 'wb')
end
if probe then probe:close(); os.remove(base .. '.probe') end
local path = base .. 'test_replay_lua.bin'
local msg = MAIN.cmd_replay(path, 60)
H.check_true('리플레이 재생이 일치한다', H.strip(msg):sub(-#'일치') == '일치')
local f = assert(io.open(path, 'rb'))
local blob = f:read('*a')
f:close()
H.check_true(string.format('리플레이는 작다 (%s)', H.strip(msg)), #blob < 4096)
H.check('상태는 저장하지 않는다 — 파일에 머리 넷 글자', blob:sub(1, 4), 'RTSR')
os.remove(path)

return H.done()
