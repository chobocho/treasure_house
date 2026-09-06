-- PC 스피커 — 분주값·음표표·사각파 (SPEC §21).
--
--    PIT 은 사각파만 낼 수 있었다. 음량 조절이 없었고 듀티비도 고정이라, 도스
--    게임의 스피커 음악은 전부 같은 음색이다. 여기서 하는 일은 그 제약을 그대로
--    흉내내는 것뿐이다.
--
--    소리를 재생하지 않는다 — 헤드리스 환경이고, 바이트가 같으면 소리도 같다.

local C = require('rts.const')
local F = require('rts.fixed')

local M = {}
local floor = math.floor

M.SAMPLE_RATE = 22050
M.AMP_LO, M.AMP_HI, M.AMP_MID = 64, 192, 128
local SAMPLE_RATE, AMP_LO, AMP_HI, AMP_MID = 22050, 64, 192, 128

-- §21.2 A4 = 440 Hz 12평균율을 **정수 Hz 로 반올림해 박아 둔다.**
-- 세 언어가 같은 표를 갖는 것이 실수 연산을 맞추는 것보다 싸고 확실하다.
M.NOTE_NAME = {[0] = 'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4',
               'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5',
               'G5', 'G#5', 'A5', 'A#5', 'B5', n = 24}
M.NOTE_HZ = {[0] = 262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494,
             523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 932, 988, n = 24}

-- ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────

--- 반올림 나눗셈. PIT_HZ 자체가 반올림값이라는 것을 22부가 따로 따진다.
function M.divisor(f)
    if f <= 0 then
        return 0
    end
    local d = F.floordiv(C.PIT_HZ + F.floordiv(f, 2), f)
    return d < 1 and 1 or d
end

--- 실제로 나는 주파수를 **정수 나눗셈의 몫과 나머지**로 낸다.
--- 센트 오차는 로그가 필요하므로 엔진이 아니라 tools/gen_prim.py 가 낸다.
function M.actual(f)
    local d = M.divisor(f)
    if d == 0 then
        return 0, 0
    end
    return F.floordiv(C.PIT_HZ, d), F.fmod(C.PIT_HZ, d)
end

function M.actual100(f)
    local d = M.divisor(f)
    if d == 0 then return 0 end
    return F.floordiv(C.PIT_HZ * 100, d)
end

-- ── SPEC §21.3 사각파 합성 ──────────────────────────────────────────────────
function M.half_period(f)
    local q = M.actual(f)
    if q <= 0 then
        return 0
    end
    return F.floordiv(SAMPLE_RATE, 2 * q)
end

--- 8비트 부호 없는 모노 PCM n 샘플의 바이트 문자열. f <= 0 이면 무음(쉼표).
function M.square(f, n)
    if n <= 0 then
        return ''
    end
    if f <= 0 then
        return string.rep(string.char(AMP_MID), n)
    end
    local half = M.half_period(f)
    if half <= 0 then
        return string.rep(string.char(AMP_MID), n)
    end
    local lo, hi = string.char(AMP_LO), string.char(AMP_HI)
    local out = {}
    for k = 0, n - 1 do
        out[k + 1] = (F.floordiv(k, half) % 2 == 0) and lo or hi
    end
    return table.concat(out)
end

local function le(out, v, n)
    for _ = 1, n do
        out[#out + 1] = string.char(v % 256)
        v = floor(v / 256)
    end
end

--- 44바이트 헤더 + PCM. 전체 바이트의 FNV-1a 를 골든으로 둔다.
function M.wav(pcm)
    local out = {}
    out[#out + 1] = 'RIFF'
    le(out, 36 + #pcm, 4)
    out[#out + 1] = 'WAVE'
    out[#out + 1] = 'fmt '
    le(out, 16, 4)                     -- fmt 청크 길이
    le(out, 1, 2)                      -- PCM
    le(out, 1, 2)                      -- 모노
    le(out, SAMPLE_RATE, 4)
    le(out, SAMPLE_RATE, 4)            -- 바이트/초 = 레이트 × 1채널 × 1바이트
    le(out, 1, 2)                      -- 블록 정렬
    le(out, 8, 2)                      -- 비트/샘플
    out[#out + 1] = 'data'
    le(out, #pcm, 4)
    out[#out + 1] = pcm
    return table.concat(out)
end

--- (주파수, 샘플 수) 목록을 이어 붙여 WAV 로.
function M.tune(notes)
    local pcm = {}
    for k = 0, notes.n - 1 do
        pcm[#pcm + 1] = M.square(notes[k][1], notes[k][2])
    end
    return M.wav(table.concat(pcm))
end

return M
