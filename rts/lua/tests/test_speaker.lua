-- PC 스피커 — 분주값·음표표·사각파 (SPEC §21).

local H = require('tests.harness')
local C = require('rts.const')
local F = require('rts.fixed')
local SP = require('rts.speaker')

H.title('speaker')

local function arr(...)
    local t = {n = select('#', ...)}
    for k = 1, t.n do t[k - 1] = select(k, ...) end
    return t
end

local g = H.lines(H.golden('prim.txt'))

-- ── 골든 14절 분주값 표 ─────────────────────────────────────────────────────
local i = H.index_of(g, '== 14. PIT 분주값 ==') + 2
local bad = 0
local n = 0
while i < g.n and H.strip(g[i]) ~= '' do
    local p = H.split(g[i])
    local name = p[0]
    local f, div, act, diff = tonumber(p[1]), tonumber(p[2]), tonumber(p[3]),
                              tonumber(p[4])
    local got = arr(SP.NOTE_NAME[n], SP.NOTE_HZ[n], SP.divisor(f),
                    SP.actual100(f))
    local wnt = arr(name, f, div, act)
    if not H.deep_eq(got, wnt) then
        bad = bad + 1
        H.note('%s 기대 %s 실제 %s', name, H.repr(wnt), H.repr(got))
    end
    if act - f * 100 ~= diff then bad = bad + 1 end
    n = n + 1
    i = i + 1
end
H.check(string.format('골든 14절 %d음', n), bad, 0)
H.check('24음 (C4..B5)', n, 24)
H.check('A4 는 440 Hz', SP.NOTE_HZ[H.index_of(SP.NOTE_NAME, 'A4')], 440)
H.check('C4 는 262 Hz (261.63 반올림)', SP.NOTE_HZ[0], 262)

-- ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
H.check('분주값은 반올림 나눗셈', SP.divisor(440), F.floordiv(C.PIT_HZ + 220, 440))
H.check('1 Hz 는 분주값이 PIT 클럭 그대로', SP.divisor(1), C.PIT_HZ)
H.check('분주값은 1 아래로 내려가지 않는다', SP.divisor(10000000), 1)
H.check('실제 주파수는 몫과 나머지로만 낸다', arr(SP.actual(440)),
        arr(F.floordiv(C.PIT_HZ, SP.divisor(440)),
            F.fmod(C.PIT_HZ, SP.divisor(440))))
H.check_true('440 Hz 의 실제 값은 439.96 Hz', SP.actual100(440) == 43996)
H.note('센트 오차는 로그가 필요해 엔진이 아니라 gen_prim 이 낸다')
H.check('PIT_HZ 는 반올림값 — 정확한 값은 14.31818MHz/12 = 1193181.8181…',
        C.PIT_HZ, 1193182)

-- ── SPEC §21.3 사각파 ───────────────────────────────────────────────────────
H.check('샘플레이트', SP.SAMPLE_RATE, 22050)
local half = SP.half_period(440)
local q440 = SP.actual(440)
H.check('반주기 = 22050 / (2 · 실제주파수)', half,
        F.floordiv(SP.SAMPLE_RATE, 2 * q440))
local pcm = SP.square(440, 100)
H.check('요청한 만큼 샘플이 나온다', #pcm, 100)
local function byteset(s)
    local seen = {}
    local out = {n = 0}
    for k = 1, #s do seen[s:byte(k)] = true end
    for v = 0, 255 do
        if seen[v] then out[out.n] = v; out.n = out.n + 1 end
    end
    return out
end
H.check('진폭은 두 값뿐 (듀티비 고정 — 음량 조절이 없었다)', byteset(pcm),
        arr(64, 192))
H.check('첫 반주기는 같은 값', byteset(pcm:sub(1, half)).n, 1)
H.check('반주기 뒤에 뒤집힌다', pcm:byte(1) ~= pcm:byte(half + 1), true)
H.check('쉼표는 무음 (0x80)', byteset(SP.square(0, 50)), arr(128))
H.check('길이 0 이면 빈 소리', SP.square(440, 0), '')

-- ── WAV ─────────────────────────────────────────────────────────────────────
local wav = SP.wav(pcm)
H.check('헤더는 44바이트', #wav, 44 + #pcm)
H.check('RIFF/WAVE', arr(wav:sub(1, 4), wav:sub(9, 12)), arr('RIFF', 'WAVE'))
H.check('fmt 청크', wav:sub(13, 16), 'fmt ')
H.check('data 청크', wav:sub(37, 40), 'data')
H.check('PCM · 모노 · 8비트',
        arr(wav:byte(21), wav:byte(23), wav:byte(35)), arr(1, 1, 8))
H.check('샘플레이트가 머리에 들어간다',
        wav:byte(25) + wav:byte(26) * 256 + wav:byte(27) * 65536
        + wav:byte(28) * 16777216, SP.SAMPLE_RATE)
H.check('RIFF 크기 = 전체 - 8',
        wav:byte(5) + wav:byte(6) * 256 + wav:byte(7) * 65536
        + wav:byte(8) * 16777216, #wav - 8)

local function notes()
    return {[0] = {SP.NOTE_HZ[0], 20}, {0, 5}, {SP.NOTE_HZ[12], 20}, n = 3}
end
local tune = SP.tune(notes())
H.check('연속 연주는 이어 붙인 것', #tune, 44 + 45)
H.check_true(string.format('바이트 해시가 결정론적 (%08X)', F.fnv1a(tune)),
             F.fnv1a(tune) == F.fnv1a(SP.tune(notes())))
H.note('소리를 재생하지 않는다 — 헤드리스이고, 바이트가 같으면 소리도 같다')

return H.done()
