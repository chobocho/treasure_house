/* ============================================================
   28부의 타입스크립트 엔진을 브라우저에서 그대로 돌리기 위한 묶음.

   이 파일의 코드는 ts/src/*.ts 를 tsc 가 옮긴 것이고, 손으로 고친 곳이 없다.
   그래서 이 문서 안에서 움직이는 유닛의 좌표는 golden/trace.jsonl 을 만든 것과
   같은 코드가 계산한 값이다. tools/check_web.js 가 매번 그것을 대조한다.

   tools/bundle_web.py 가 만든다. 손으로 고치지 말 것.
   ============================================================ */
(function (root) {
  'use strict';
  var __mods = {};
  var __cache = {};
  function __def(name, fn) { __mods[name] = fn; }
  function __req(name) {
    var raw = String(name);
    // './fixed' 나 '../raster' 같은 상대 경로를 이름으로 되돌린다.
    var n = raw.replace(/^(\.\.?\/)+/, '').replace(/\.js$/, '');
    // 점으로 시작하지 않으면 노드 내장 모듈이다. 엔진에도 path 라는 모듈이 있어서
    // 이 구분을 빠뜨리면 경로탐색 모듈이 경로 스텁으로 가려진다.
    var builtin = raw.charAt(0) !== '.';
    if (builtin && n === 'path') {
      // join 만 진짜로 만든다. resolve 와 dirname 은 브라우저에서 쓸 일이 없고,
      // 그럴듯한 값을 돌려주면 나중에 누가 쓸 때 조용히 틀린 경로가 흘러다닌다.
      var join = function () { return Array.prototype.join.call(arguments, '/'); };
      var nope = function (what) {
        return function () { throw new Error('브라우저에서는 path.' + what + ' 를 쓸 수 없다'); };
      };
      return { join: join, resolve: join, dirname: nope('dirname'),
               basename: nope('basename'), relative: nope('relative') };
    }
    if (builtin && n === 'fs') {
      // 브라우저에는 파일이 없다. 조용히 빈 값을 돌려주면 맵이 비고 시나리오가
      // 사라진 채로 게임이 도는데, 그 화면은 "그럴듯해" 보인다. 그래서 터뜨린다.
      return { readFileSync: function () {
        throw new Error('브라우저에서는 파일을 읽을 수 없다 — web/data.ts 의 문자열을 쓸 것');
      }, writeFileSync: function () { throw new Error('브라우저에서는 파일을 쓸 수 없다'); } };
    }
    if (__cache[n]) return __cache[n];
    var f = __mods[n] || __mods['web/' + n];
    if (!f) throw new Error('모듈 없음: ' + name);
    var m = { exports: {} };
    // 순환 참조를 위해 평가 전에 미리 넣는다. 대신 평가가 터지면 반드시 걷어낸다 —
    // 안 그러면 다음 require 가 반쯤 만들어진 exports 를 조용히 돌려준다.
    __cache[n] = m.exports;
    try {
      // tsc 가 낸 코드에 __dirname 이 남아 있을 수 있다(경로 상수). 브라우저에는
      // 그런 전역이 없으므로 여기서 넣어 준다. 값은 쓰이지 않는다.
      f(m.exports, __req, m, '/');
    } catch (e) {
      delete __cache[n];
      throw e;
    }
    __cache[n] = m.exports;
    return m.exports;
  }
  __def('fmt', function (exports, require, module, __dirname) {
"use strict";
// 문자열 서식 — 파이썬 `%` 연산자를 바이트 단위로 흉내낸다 (SPEC §24).
//
//    자바스크립트에는 printf 가 없다. `golden/prim.txt` 는 294줄의 정렬된 표이고
//    빈칸 하나만 어긋나도 `cmp` 가 떨어진다. 그래서 필요한 서식만 최소로 만들고
//    쓰는 쪽에서 폭을 명시한다 — 서식 문자열을 파싱하는 범용 구현은 만들지 않는다.
//    범용 구현은 어디가 틀렸는지 찾기가 더 어렵다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.padLeft = padLeft;
exports.padRight = padRight;
exports.hex8 = hex8;
exports.hex4 = hex4;
exports.hex2 = hex2;
exports.fixed3 = fixed3;
exports.pyRepr = pyRepr;
// '%Nd' — 오른쪽 정렬. 음수 부호도 문자열 길이에 포함된다(파이썬과 같다).
function padLeft(v, w) {
    const s = typeof v === 'number' ? String(v) : v;
    return s.length >= w ? s : ' '.repeat(w - s.length) + s;
}
// '%-Ns' — 왼쪽 정렬.
function padRight(v, w) {
    const s = typeof v === 'number' ? String(v) : v;
    return s.length >= w ? s : s + ' '.repeat(w - s.length);
}
function hexOf(v, w, upper) {
    let s = Math.trunc(v).toString(16);
    if (upper)
        s = s.toUpperCase();
    return s.length >= w ? s : '0'.repeat(w - s.length) + s;
}
function hex8(v) {
    return hexOf(v, 8, true);
}
function hex4(v) {
    return hexOf(v, 4, true);
}
function hex2(v) {
    return hexOf(v, 2, false);
}
// '%.3f' — 벤치마크의 초 단위에만 쓴다(골든 비교 대상이 아니다).
function fixed3(v) {
    return v.toFixed(3);
}
// 파이썬 `repr` 흉내. prim 13절이 ASCII 문자열에 `%r` 을 쓰므로
// '123456789' 처럼 따옴표가 붙은 형태가 그대로 골든에 들어 있다.
function pyRepr(v) {
    if (v === null || v === undefined)
        return 'None';
    if (typeof v === 'boolean')
        return v ? 'True' : 'False';
    if (typeof v === 'number') {
        if (Number.isInteger(v))
            return String(v);
        return String(v);
    }
    if (typeof v === 'string') {
        const q = (v.indexOf("'") >= 0 && v.indexOf('"') < 0) ? '"' : "'";
        let out = '';
        for (const ch of v) {
            if (ch === '\\')
                out += '\\\\';
            else if (ch === q)
                out += '\\' + ch;
            else if (ch === '\n')
                out += '\\n';
            else if (ch === '\t')
                out += '\\t';
            else
                out += ch;
        }
        return q + out + q;
    }
    if (Array.isArray(v)) {
        return '[' + v.map((e) => pyRepr(e)).join(', ') + ']';
    }
    return String(v);
}
  });
  __def('const', function (exports, require, module, __dirname) {
"use strict";
// 상수표와 유닛·건물표 — SPEC §0, §25.
//
//    이 파일은 다른 모듈을 하나도 참조하지 않고, 함수도 (표를 만드는 것 말고는)
//    없다. 숫자만 있다. 같은 상수를 두 군데 적으면 한 쪽만 고치는 날이 오고,
//    그날 세 언어가 갈린다. 그래서 `fixed` 에 있는 FP_* 와 D_* 를 여기에 **다시**
//    적어 두었지만, 그 둘이 같은지는 test_fixed 가 대조한다. `fixed` 는 의존이
//    없어야 가장 먼저 포팅되므로 여기를 참조하지 않는다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.TOWER = exports.POW = exports.FACT = exports.BARR = exports.REF = exports.HQ = exports.HARV = exports.MORTAR = exports.TANK = exports.ARCHER = exports.INF = exports.CRC_INIT = exports.CRC_POLY = exports.FNV_PRIME = exports.FNV_OFFSET = exports.D_DIAG = exports.D_STRAIGHT = exports.BUCKET = exports.CLUSTER = exports.SIGHT_MAX = exports.MAX_PLAYER = exports.GEN_MOD = exports.MAX_ENT = exports.ORDER_DELAY = exports.PIT_HZ = exports.TICK_US = exports.DAC_MAX = exports.PAL_SIZE = exports.FP_SQRT2M1 = exports.FP_DIAG = exports.FP_HALF = exports.FP_ONE = exports.FP_BITS = exports.BAR_H = exports.BAR_Y = exports.MINI_H = exports.MINI_W = exports.MINI_Y = exports.MINI_X = exports.PANEL_W = exports.PANEL_X = exports.VIEW_H = exports.VIEW_W = exports.VIEW_Y = exports.VIEW_X = exports.MAP_H = exports.MAP_W = exports.TILE = exports.SCR_H = exports.SCR_W = void 0;
exports.SCENARIO_TICKS = exports.START_HARV = exports.START_CREDITS = exports.PREREQ = exports.ST_BUILD = exports.ST_UNLOAD = exports.ST_TO_BASE = exports.ST_MINE = exports.ST_TO_ORE = exports.ST_SEEK = exports.ST_FLEE = exports.ST_ATTACK = exports.ST_MOVE = exports.ST_IDLE = exports.MOVE_KIND = exports.IS_BUILDING = exports.FOOT = exports.POP = exports.BUILD_TICKS = exports.COST = exports.SIGHT = exports.SPEED = exports.RELOAD = exports.RANGE = exports.ARMOUR = exports.PIERCE = exports.BASIC = exports.HP = exports.NAME = exports.KIND_COUNT = void 0;
// ── §0 화면과 맵 ────────────────────────────────────────────────────────────
exports.SCR_W = 320;
exports.SCR_H = 200;
exports.TILE = 16;
exports.MAP_W = 64;
exports.MAP_H = 64;
exports.VIEW_X = 0;
exports.VIEW_Y = 0;
exports.VIEW_W = 256; // 16타일
exports.VIEW_H = 176; // 11타일 — 176 + 24 = 200 이 화면 높이다
exports.PANEL_X = 256;
exports.PANEL_W = 64;
exports.MINI_X = 256;
exports.MINI_Y = 0;
exports.MINI_W = 64;
exports.MINI_H = 64;
exports.BAR_Y = 176;
exports.BAR_H = 24;
// ── §0 고정소수점 (fixed 와 같은 값이어야 한다) ─────────────────────────────
exports.FP_BITS = 16;
exports.FP_ONE = 65536;
exports.FP_HALF = 32768;
exports.FP_DIAG = 46341;
exports.FP_SQRT2M1 = 27146;
// ── §0 하드웨어와 시간 ──────────────────────────────────────────────────────
exports.PAL_SIZE = 256;
exports.DAC_MAX = 63;
exports.TICK_US = 54925; // 18.2065 Hz. 실제 54,925.4 µs
exports.PIT_HZ = 1193182;
// ── §0 시뮬레이션 ───────────────────────────────────────────────────────────
exports.ORDER_DELAY = 2;
exports.MAX_ENT = 256;
exports.GEN_MOD = 256;
exports.MAX_PLAYER = 4;
exports.SIGHT_MAX = 8;
exports.CLUSTER = 8;
exports.BUCKET = 8;
exports.D_STRAIGHT = 10;
exports.D_DIAG = 14;
// ── §0 해시와 CRC ───────────────────────────────────────────────────────────
exports.FNV_OFFSET = 2166136261;
exports.FNV_PRIME = 16777619;
exports.CRC_POLY = 0x1021;
exports.CRC_INIT = 0xFFFF;
// ── §25 종류 번호 ───────────────────────────────────────────────────────────
// 유닛 0..4, 건물 10..15. 5..9 를 비워 둔 것은 "유닛인가"를 번호 하나로
// 판별하려는 유혹을 막기 위해서다 — 판별은 IS_BUILDING 표가 한다.
exports.INF = 0;
exports.ARCHER = 1;
exports.TANK = 2;
exports.MORTAR = 3;
exports.HARV = 4;
exports.HQ = 10;
exports.REF = 11;
exports.BARR = 12;
exports.FACT = 13;
exports.POW = 14;
exports.TOWER = 15;
exports.KIND_COUNT = 16;
// {종류: 값} 을 길이 16 배열로. 언어가 달라도 같은 모양을 갖도록 배열로 둔다.
function tab(pairs) {
    const t = [];
    for (let k = 0; k < exports.KIND_COUNT; k += 1)
        t.push(0);
    for (const [k, v] of pairs)
        t[k] = v;
    return t;
}
exports.NAME = ['', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', ''];
for (const [k, n] of [[exports.INF, '보병'], [exports.ARCHER, '사수'], [exports.TANK, '전차'],
    [exports.MORTAR, '박격포'], [exports.HARV, '채집기'], [exports.HQ, '사령부'],
    [exports.REF, '정제소'], [exports.BARR, '병영'], [exports.FACT, '공장'],
    [exports.POW, '발전소'], [exports.TOWER, '방어탑']]) {
    exports.NAME[k] = n;
}
exports.HP = tab([[exports.INF, 40], [exports.ARCHER, 30], [exports.TANK, 90], [exports.MORTAR, 35],
    [exports.HARV, 60], [exports.HQ, 400], [exports.REF, 250], [exports.BARR, 200],
    [exports.FACT, 300], [exports.POW, 150], [exports.TOWER, 120]]);
exports.BASIC = tab([[exports.INF, 6], [exports.ARCHER, 4], [exports.TANK, 12], [exports.MORTAR, 10],
    [exports.TOWER, 8]]);
exports.PIERCE = tab([[exports.INF, 3], [exports.ARCHER, 6], [exports.TANK, 8], [exports.MORTAR, 12],
    [exports.TOWER, 6]]);
exports.ARMOUR = tab([[exports.INF, 1], [exports.ARCHER, 0], [exports.TANK, 4], [exports.MORTAR, 0],
    [exports.HARV, 3], [exports.HQ, 3], [exports.REF, 5], [exports.BARR, 4], [exports.FACT, 5],
    [exports.POW, 3], [exports.TOWER, 5]]);
exports.RANGE = tab([[exports.INF, 1], [exports.ARCHER, 4], [exports.TANK, 3], [exports.MORTAR, 6],
    [exports.TOWER, 5]]);
exports.RELOAD = tab([[exports.INF, 12], [exports.ARCHER, 16], [exports.TANK, 24], [exports.MORTAR, 40],
    [exports.TOWER, 20]]);
// 16.16 px/틱. 1.5 px/틱 = 0.094 타일/틱 — 47타일 대각선에 752틱이 든다(대각 보정 포함, §25.4).
exports.SPEED = tab([[exports.INF, 98304], [exports.ARCHER, 91750], [exports.TANK, 131072],
    [exports.MORTAR, 65536], [exports.HARV, 78643]]);
exports.SIGHT = tab([[exports.INF, 4], [exports.ARCHER, 5], [exports.TANK, 5], [exports.MORTAR, 4],
    [exports.HARV, 3], [exports.HQ, 6], [exports.REF, 4], [exports.BARR, 4], [exports.FACT, 4],
    [exports.POW, 3], [exports.TOWER, 6]]);
exports.COST = tab([[exports.INF, 100], [exports.ARCHER, 140], [exports.TANK, 300], [exports.MORTAR, 260],
    [exports.HARV, 150], [exports.REF, 300], [exports.BARR, 400], [exports.FACT, 600],
    [exports.POW, 200], [exports.TOWER, 250]]);
exports.BUILD_TICKS = tab([[exports.INF, 60], [exports.ARCHER, 80], [exports.TANK, 150],
    [exports.MORTAR, 140], [exports.HARV, 90], [exports.REF, 180],
    [exports.BARR, 200], [exports.FACT, 300], [exports.POW, 120],
    [exports.TOWER, 120]]);
// 유닛은 인구 소비, 건물은 인구 제공 — 어느 쪽인지는 IS_BUILDING 이 정한다.
exports.POP = tab([[exports.INF, 1], [exports.ARCHER, 1], [exports.TANK, 2], [exports.MORTAR, 2],
    [exports.HARV, 1], [exports.HQ, 10], [exports.POW, 10]]);
exports.FOOT = tab([[exports.INF, 1], [exports.ARCHER, 1], [exports.TANK, 1], [exports.MORTAR, 1],
    [exports.HARV, 1], [exports.HQ, 3], [exports.REF, 2], [exports.BARR, 2], [exports.FACT, 3],
    [exports.POW, 2], [exports.TOWER, 1]]);
exports.IS_BUILDING = tab([[exports.HQ, 1], [exports.REF, 1], [exports.BARR, 1], [exports.FACT, 1],
    [exports.POW, 1], [exports.TOWER, 1]]);
// §4.3 통행 비트 번호와 같은 값이다: 0 = 보병, 1 = 차량. 차량은 언덕에 못 오른다.
exports.MOVE_KIND = tab([[exports.TANK, 1], [exports.HARV, 1]]);
// ── §17.1 FSM 상태 번호 ─────────────────────────────────────────────────────
// 전투 유닛과 채집기가 state 바이트 하나를 나눠 쓴다. 겹치면 상태 해시가
// 같은 값을 두 뜻으로 읽게 되므로 번호는 여기 한 곳에서만 정한다.
exports.ST_IDLE = 0;
exports.ST_MOVE = 1;
exports.ST_ATTACK = 2;
exports.ST_FLEE = 3;
exports.ST_SEEK = 4;
exports.ST_TO_ORE = 5;
exports.ST_MINE = 6;
exports.ST_TO_BASE = 7;
exports.ST_UNLOAD = 8;
exports.ST_BUILD = 9;
// ── §25.3 기술 트리 (DAG) ───────────────────────────────────────────────────
// 선행 목록은 **번호 오름차순**으로 적는다. 위상 정렬의 타이브레이크가 세 언어에서
// 같아야 하기 때문이다. FACT 만 선행이 둘이고, 그래서 위상 정렬이 실제로 필요하다.
exports.PREREQ = [];
for (let k = 0; k < exports.KIND_COUNT; k += 1)
    exports.PREREQ.push([]);
exports.PREREQ[exports.HARV] = [exports.HQ];
exports.PREREQ[exports.REF] = [exports.HQ];
exports.PREREQ[exports.BARR] = [exports.HQ];
exports.PREREQ[exports.INF] = [exports.BARR];
exports.PREREQ[exports.ARCHER] = [exports.BARR];
exports.PREREQ[exports.TOWER] = [exports.BARR];
exports.PREREQ[exports.FACT] = [exports.BARR, exports.POW];
exports.PREREQ[exports.TANK] = [exports.FACT];
exports.PREREQ[exports.MORTAR] = [exports.FACT];
// ── §25.4 시작 조건 ─────────────────────────────────────────────────────────
exports.START_CREDITS = 1000;
exports.START_HARV = 2;
exports.SCENARIO_TICKS = 1200;
  });
  __def('fixed', function (exports, require, module, __dirname) {
"use strict";
// 16.16 고정소수점 · 정수 기하 · 거리 척도 — SPEC §1, §2.
//
//    파이썬 원본을 그대로 옮긴다. 파이썬만 생각하면 한 줄이면 끝나는 함수들이
//    이렇게 쪼개져 있는 이유는 자바스크립트 때문이다. JS 의 정수는 배정밀도
//    부동소수점(가수 53비트)에 얹혀 있고 `>>` `&` `|` `^` 는 32비트로 잘린다.
//    그래서 이 모듈은
//      · 시프트를 쓰지 않고 (floordiv 로만)
//      · 곱셈 중간값이 2^53 을 넘지 않게 쪼개서
//      · 비트 연산자 대신 산술로
//    계산한다. 이 파일 전체에 비트 연산자가 한 개도 없다는 것이 규약이다.
//
//    이 파일은 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.FNV_PRIME = exports.FNV_OFFSET = exports.DCOST = exports.DNAME = exports.DY = exports.DX = exports.D_DIAG = exports.D_STRAIGHT = exports.FP_SQRT2M1 = exports.FP_DIAG = exports.FP_HALF = exports.FP_ONE = exports.FP_BITS = void 0;
exports.pow2 = pow2;
exports.floordiv = floordiv;
exports.fmod = fmod;
exports.ashr = ashr;
exports.ashl = ashl;
exports.bit = bit;
exports.setbit = setbit;
exports.clrbit = clrbit;
exports.xor8 = xor8;
exports.xorLow8 = xorLow8;
exports.fp = fp;
exports.fpFloor = fpFloor;
exports.fpRound = fpRound;
exports.fpFrac = fpFrac;
exports.fpMul = fpMul;
exports.fpDiv = fpDiv;
exports.isqrt = isqrt;
exports.fpSqrt = fpSqrt;
exports.d1 = d1;
exports.dinf = dinf;
exports.d83 = d83;
exports.doct = doct;
exports.dab = dab;
exports.atan8 = atan8;
exports.xor16 = xor16;
exports.fnv1aStep = fnv1aStep;
exports.fnv1a = fnv1a;
exports.crc16 = crc16;
exports.ascii = ascii;
exports.FP_BITS = 16;
exports.FP_ONE = 65536;
exports.FP_HALF = 32768;
exports.FP_DIAG = 46341; // 1/√2 의 16.16 반올림 (46340.950…)
exports.FP_SQRT2M1 = 27146; // √2−1 의 16.16 반올림 (27145.951…)
exports.D_STRAIGHT = 10;
exports.D_DIAG = 14;
// SPEC §2.7 — 화면 좌표이므로 y 는 아래로 증가한다.
exports.DX = [0, 1, 1, 1, 0, -1, -1, -1];
exports.DY = [-1, -1, 0, 1, 1, 1, 0, -1];
exports.DNAME = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
exports.DCOST = [exports.D_STRAIGHT, exports.D_DIAG, exports.D_STRAIGHT, exports.D_DIAG,
    exports.D_STRAIGHT, exports.D_DIAG, exports.D_STRAIGHT, exports.D_DIAG];
// 2의 거듭제곱 표 — `1 << k` 를 쓰지 않기 위한 것이다. k 가 31 을 넘어도
// 안전해야 하므로 (fnv 는 2^32 를 다룬다) 표로 미리 굳혀 둔다.
const POW2 = [];
for (let k = 0; k <= 53; k += 1)
    POW2.push(Math.pow(2, k));
function pow2(k) {
    return POW2[k];
}
// ── SPEC §1 정수 연산 규약 ──────────────────────────────────────────────────
// 파이썬의 // 와 % 를 **알고리즘까지** 그대로 옮긴다. Math.floor(a/b) 로 줄이면
// 나눗셈이 한 번 반올림된 뒤 내림이 되어 2^53 근처에서 한 칸씩 어긋난다.
function floordiv(a, b) {
    let mod = a % b; // JS 의 % 는 절단 나머지 — 정확하다
    let div = (a - mod) / b; // a - mod 는 b 의 배수라 나눗셈이 정확하다
    if (mod !== 0 && (b < 0) !== (mod < 0)) {
        mod += b;
        div -= 1;
    }
    const fl = Math.floor(div);
    return (div - fl > 0.5) ? fl + 1 : fl; // CPython float_floor_div 와 같은 보정
}
function fmod(a, b) {
    let mod = a % b;
    if (mod !== 0 && (b < 0) !== (mod < 0))
        mod += b;
    return mod;
}
function ashr(a, k) {
    return floordiv(a, POW2[k]);
}
function ashl(a, k) {
    return a * POW2[k];
}
// ── SPEC §1.1 비트 연산의 산술 대체 ─────────────────────────────────────────
function bit(v, k) {
    return fmod(floordiv(v, POW2[k]), 2);
}
function setbit(v, k) {
    return v + (1 - bit(v, k)) * POW2[k];
}
function clrbit(v, k) {
    return v - bit(v, k) * POW2[k];
}
// 바이트 두 개의 XOR — 여덟 번 도는 것이 전부다.
// JS 의 ^ 는 32비트로 잘리므로 여기서는 쓰지 않는다(SPEC §1.1). 한 곳에서만
// 규칙을 어겨도 반드시 다른 곳에서 샌다.
function xor8(x, y) {
    let r = 0;
    let p = 1;
    let a = x;
    let b = y;
    for (let k = 0; k < 8; k += 1) {
        if ((a % 2) !== (b % 2))
            r += p;
        a = floordiv(a, 2);
        b = floordiv(b, 2);
        p *= 2;
    }
    return r;
}
// 32비트 값의 하위 8비트에만 XOR — FNV-1a(SPEC §18.4)가 쓴다.
function xorLow8(h, b) {
    return h - fmod(h, 256) + xor8(fmod(h, 256), b);
}
// ── SPEC §2.1 변환 ──────────────────────────────────────────────────────────
function fp(n) {
    return n * exports.FP_ONE;
}
function fpFloor(x) {
    return floordiv(x, exports.FP_ONE);
}
function fpRound(x) {
    return floordiv(x + exports.FP_HALF, exports.FP_ONE);
}
function fpFrac(x) {
    return fmod(x, exports.FP_ONE);
}
// ── SPEC §2.3 곱셈 (분할 곱) ────────────────────────────────────────────────
// floor(a*b / 65536). a 를 상·하위로 쪼개 중간값을 2^53 아래로 붙든다.
// a = ah·2^16 + al 이므로 a·b/2^16 = ah·b + al·b/2^16 이고, 첫 항이 정수라
// 바닥함수 밖으로 나온다 (SPEC 정리 2.1). 쪼개지 않으면 a·b 가 2^53 을 넘는다.
function fpMul(a, b) {
    const ah = floordiv(a, exports.FP_ONE);
    const al = fmod(a, exports.FP_ONE);
    return ah * b + floordiv(al * b, exports.FP_ONE);
}
function fpDiv(a, b) {
    if (b === 0)
        throw new Error('fp_div: b == 0'); // 호출자의 버그다
    return floordiv(a * exports.FP_ONE, b);
}
// ── SPEC §2.5 정수 제곱근 ───────────────────────────────────────────────────
// 뉴턴 반복. 초기값과 종료 조건까지 명세다 — 세 언어가 같은 횟수를 돈다.
function isqrt(n) {
    if (n < 2)
        return n;
    let x = n;
    let y = floordiv(x + 1, 2);
    while (y < x) {
        x = y;
        y = floordiv(x + floordiv(n, x), 2);
    }
    return x;
}
function fpSqrt(x) {
    return isqrt(x * exports.FP_ONE); // x < 2^31 이므로 x*65536 < 2^47 — 안전하다
}
// ── SPEC §2.6 거리 척도 ─────────────────────────────────────────────────────
function mxmn(dx, dy) {
    const ax = dx >= 0 ? dx : -dx;
    const ay = dy >= 0 ? dy : -dy;
    return ax >= ay ? [ax, ay] : [ay, ax];
}
// L1 (맨해튼) — 4방향 이동의 정확한 걸음 수.
function d1(dx, dy) {
    return (dx >= 0 ? dx : -dx) + (dy >= 0 ? dy : -dy);
}
// L∞ (체비셰프) — 8방향 이동의 정확한 걸음 수. 사거리 판정은 전부 이것.
function dinf(dx, dy) {
    return mxmn(dx, dy)[0];
}
// 옥타일 8분의 3 근사. √2−1 = 0.41421 을 3/8 로 바꾼 도스식 값.
function d83(dx, dy) {
    const [mx, mn] = mxmn(dx, dy);
    return mx + floordiv(3 * mn, 8);
}
// 경로 비용 단위의 옥타일 거리. 직선 10, 대각 14 — A* 휴리스틱이 이것이다.
function doct(dx, dy) {
    const [mx, mn] = mxmn(dx, dy);
    return exports.D_STRAIGHT * mx + (exports.D_DIAG - exports.D_STRAIGHT) * mn;
}
// alpha-max-beta-min. 마지막 반올림(+32768)이 없으면 dab(1,0) = 0 이 된다.
// 거리 1 이 0 으로 나오면 사거리 판정과 타깃 선택이 통째로 무너진다.
// 골든 벡터를 처음 만들 때 오차 −100 % 로 드러난 자리다(SPEC §2.6).
function dab(dx, dy) {
    const [mx, mn] = mxmn(dx, dy);
    return floordiv(62943 * mx + 26072 * mn + exports.FP_HALF, exports.FP_ONE);
}
// ── SPEC §2.7 8방향 판별 ────────────────────────────────────────────────────
// 비교만으로 8방향을 고른다. 나눗셈도 삼각함수도 없다.
// 경계는 22.5°이고 tan 22.5° = √2−1 = 0.414214 다. 5/12 = 0.416667 로 바꾸면
// 경계각이 22.62° — 0.12° 넓어질 뿐이다. √2−1 의 연분수 수렴분수가
// 1/2, 2/5, 5/12, 12/29 … (펠 수의 비)이므로 5/12 는 우연이 아니다.
function atan8(dx, dy) {
    if (dx === 0 && dy === 0)
        return 2; // 규약: 정지 상태는 E 를 본다
    const ax = dx >= 0 ? dx : -dx;
    const ay = dy >= 0 ? dy : -dy;
    const mx = ax >= ay ? ax : ay;
    const mn = ax >= ay ? ay : ax;
    const diag = 12 * mn > 5 * mx;
    if (ax >= ay) { // 동서가 주축
        if (dx > 0) {
            if (diag)
                return dy < 0 ? 1 : 3;
            return 2;
        }
        if (diag)
            return dy < 0 ? 7 : 5;
        return 6;
    }
    if (dy < 0) { // 남북이 주축
        if (diag)
            return dx > 0 ? 1 : 7;
        return 0;
    }
    if (diag)
        return dx > 0 ? 3 : 5;
    return 4;
}
// ── SPEC §20.1 CRC-16/CCITT-FALSE ───────────────────────────────────────────
// 여기 있는 이유: tmap(맵 파일)과 replay(리플레이 꼬리)가 둘 다 쓰는데,
// fixed 는 아무것도 참조하지 않으므로 순환이 생기지 않는다.
function xor16(a, b) {
    return xor8(floordiv(a, 256), floordiv(b, 256)) * 256
        + xor8(fmod(a, 256), fmod(b, 256));
}
// ── SPEC §18.4 FNV-1a 32비트 ────────────────────────────────────────────────
exports.FNV_OFFSET = 2166136261;
exports.FNV_PRIME = 16777619;
// 바이트 하나. XOR 은 하위 8비트만 바뀌므로 xor8 로 끝나고,
// 곱셈은 분할한다 — hl * 16777619 < 2^40 이라 53비트 가수에 담긴다.
function fnv1aStep(h, b) {
    const x = xorLow8(h, b);
    const hh = floordiv(x, 65536);
    const hl = fmod(x, 65536);
    return fmod(hl * exports.FNV_PRIME + fmod(hh * exports.FNV_PRIME, 65536) * 65536, 4294967296);
}
function fnv1a(data) {
    let h = exports.FNV_OFFSET;
    for (let i = 0; i < data.length; i += 1)
        h = fnv1aStep(h, data[i]);
    return h;
}
// poly 0x1021, init 0xFFFF, 반사 없음. crc16(b'123456789') == 0x29B1.
// `c >= 32768` 이 "최상위 비트가 1"과 같다. 이것이 GF(2) 위의 다항식
// 나눗셈이며, 곱셈 2 가 다항식의 x 곱이다.
function crc16(data) {
    let c = 65535;
    for (let i = 0; i < data.length; i += 1) {
        c = xor16(c, data[i] * 256);
        for (let k = 0; k < 8; k += 1) {
            if (c >= 32768)
                c = xor16(fmod(c * 2, 65536), 0x1021);
            else
                c = fmod(c * 2, 65536);
        }
    }
    return c;
}
// ASCII 문자열을 바이트 배열로 — 골든과 시험이 자주 쓴다.
function ascii(s) {
    const out = [];
    for (let i = 0; i < s.length; i += 1)
        out.push(s.charCodeAt(i));
    return out;
}
  });
  __def('rng', function (exports, require, module, __dirname) {
"use strict";
// 난수 — 볼랜드 계열 LCG 하나 (SPEC §3).
//
//    짧은 파일이지만 언어를 건너는 지점이 둘 있다.
//      · 22695477 * s 는 최대 2^56 이라 53비트 가수에 담기지 않는다 → 분할 곱
//      · 나머지만 쓰면 모듈로 편향이 생긴다 → 기각 표본추출
//
//    시뮬레이션은 이 인스턴스를 **정확히 하나** 갖는다(SPEC §3.3). 렌더나 UI 가
//    난수를 뽑는 순간 두 기계의 수열이 갈리고, 그 뒤로 모든 것이 어긋난다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.LCG = exports.M32 = exports.A = void 0;
const fixed_1 = require("./fixed");
exports.A = 22695477;
exports.M32 = 4294967296;
class LCG {
    constructor(seed) {
        this.s = (0, fixed_1.fmod)(seed, exports.M32);
        this.rejects = 0;
    }
    // ── SPEC §3.1 ────────────────────────────────────────────────────────────
    // 상태를 한 번 굴리고 상위 15비트(비트 30..16)를 돌려준다.
    // 하위 비트는 주기가 짧다 — 최하위 비트는 0,1,0,1 을 반복한다.
    next15() {
        const s = this.s;
        const sh = (0, fixed_1.floordiv)(s, 65536);
        const sl = (0, fixed_1.fmod)(s, 65536);
        const lo = exports.A * sl; // < 2^41
        const hi = (0, fixed_1.fmod)(exports.A * sh, 65536); // < 2^16
        this.s = (0, fixed_1.fmod)(lo + hi * 65536 + 1, exports.M32);
        return (0, fixed_1.fmod)((0, fixed_1.floordiv)(this.s, 65536), 32768);
    }
    // ── SPEC §3.2 ────────────────────────────────────────────────────────────
    // 0 <= 결과 < n 인 균등 난수. 기각 루프도 결정론적이다.
    roll(n) {
        if (n <= 1)
            return 0;
        const limit = 32768 - (0, fixed_1.fmod)(32768, n);
        for (;;) {
            const r = this.next15();
            if (r < limit)
                return (0, fixed_1.fmod)(r, n);
            this.rejects += 1;
        }
    }
    save() {
        return this.s;
    }
    load(s) {
        this.s = (0, fixed_1.fmod)(s, exports.M32);
    }
}
exports.LCG = LCG;
  });
  __def('tmap', function (exports, require, module, __dirname) {
"use strict";
// 지형 맵 — 한 칸 두 바이트, 오토타일, 연결 성분, RLE (SPEC §4).
//
//    맵은 두 평면으로 나뉜다. 한 배열에 비트로 우겨 넣지 않는다.
//      terrain[i]  지형 종류
//      pass[i]     통행 비트 — 지형에서 파생되지만 건물이 서면 달라지므로 별도 상태다
//
//    비트마스크는 전부 산술로 다룬다(SPEC §1.1). 오토타일 마스크는 8비트뿐이라
//    JS 의 & 로도 잘릴 일이 없어 보이지만, 규칙을 한 군데서만 어기면 반드시
//    다른 곳에서 샌다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.TMap = exports.CLASS_COUNT = exports.OCC_BIT = exports.BUILD_BIT = exports.VEH_BIT = exports.FOOT_BIT = exports.BUILD_OK = exports.VEHICLE_OK = exports.FOOT_OK = exports.MINI_COLOR = exports.TERRAIN_NAME = exports.TERRAIN_CH = exports.ROAD = exports.RUBBLE = exports.HILL = exports.ORE = exports.DIRT = exports.WATER = exports.ROCK = exports.SAND = void 0;
exports.canon = canon;
exports.classes = classes;
exports.canonIndex = canonIndex;
exports.cornerMask = cornerMask;
const F = require("./fixed");
// ── SPEC §4.1 지형표 ────────────────────────────────────────────────────────
exports.SAND = 0;
exports.ROCK = 1;
exports.WATER = 2;
exports.DIRT = 3;
exports.ORE = 4;
exports.HILL = 5;
exports.RUBBLE = 6;
exports.ROAD = 7;
exports.TERRAIN_CH = '.#~,*^;=';
exports.TERRAIN_NAME = ['모래', '바위', '물', '흙', '광맥', '언덕',
    '잔해', '도로'];
exports.MINI_COLOR = [216, 220, 232, 214, 240, 218, 222, 226];
// 보병 통행 · 차량 통행 · 건설 가능
exports.FOOT_OK = [1, 0, 0, 1, 1, 1, 1, 1];
exports.VEHICLE_OK = [1, 0, 0, 1, 1, 0, 1, 1]; // 차량은 언덕에 못 오른다
exports.BUILD_OK = [1, 0, 0, 1, 0, 0, 1, 1];
exports.FOOT_BIT = 0;
exports.VEH_BIT = 1;
exports.BUILD_BIT = 2;
exports.OCC_BIT = 3;
// ── SPEC §4.4 오토타일 ──────────────────────────────────────────────────────
// (모서리 방향, 양옆 변 방향 둘). 방향 번호는 fixed.DX/DY 와 같다.
const CORNERS = [
    [1, 0, 2], [3, 4, 2], [5, 4, 6], [7, 0, 6]
];
// 모서리 비트는 양옆 변이 둘 다 있을 때만 살린다 (SPEC 정리 4.1).
function canon(m) {
    let r = m;
    for (const [c, a, b] of CORNERS) {
        if (!(F.bit(m, a) === 1 && F.bit(m, b) === 1))
            r = F.clrbit(r, c);
    }
    return r;
}
const CLASSES = (() => {
    const seen = new Set();
    for (let m = 0; m < 256; m += 1)
        seen.add(canon(m));
    const out = Array.from(seen);
    out.sort((a, b) => a - b);
    return out;
})();
const CLASS_INDEX = new Map();
for (let i = 0; i < CLASSES.length; i += 1)
    CLASS_INDEX.set(CLASSES[i], i);
exports.CLASS_COUNT = CLASSES.length;
function classes() {
    return CLASSES.slice();
}
// 정규화된 마스크 → 0..46 그림 번호.
function canonIndex(cm) {
    return CLASS_INDEX.get(cm);
}
// 4모서리(마칭 스퀘어) 16케이스. v = [좌상, 우상, 우하, 좌하] 의 0/1.
function cornerMask(v) {
    return v[0] + 2 * v[1] + 4 * v[2] + 8 * v[3];
}
class TMap {
    constructor(w, h) {
        this.w = w;
        this.h = h;
        this.terrain = new Array(w * h).fill(exports.SAND);
        this.pass_ = new Array(w * h).fill(0);
        this.version = 0;
        this.starts = [];
        this.pairs = [];
        this.labelCache = new Map();
        for (let i = 0; i < w * h; i += 1)
            this.repass(i);
    }
    // ── SPEC §4.2 좌표 ───────────────────────────────────────────────────────
    idx(x, y) {
        return y * this.w + x;
    }
    inMap(x, y) {
        return x >= 0 && x < this.w && y >= 0 && y < this.h;
    }
    // 맵 밖은 ROCK 이다 — 호출자가 경계 검사를 하지 않아도 되고, 오토타일 마스크가
    // 가장자리에서 자연스럽게 닫힌다.
    terrainAt(x, y) {
        if (!this.inMap(x, y))
            return exports.ROCK;
        return this.terrain[y * this.w + x];
    }
    // ── SPEC §4.3 통행 비트 ──────────────────────────────────────────────────
    repass(i) {
        const t = this.terrain[i];
        const occ = F.bit(this.pass_[i], exports.OCC_BIT);
        this.pass_[i] = exports.FOOT_OK[t] + 2 * exports.VEHICLE_OK[t] + 4 * exports.BUILD_OK[t] + 8 * occ;
    }
    setTerrain(x, y, t) {
        const i = y * this.w + x;
        if (this.terrain[i] === t)
            return;
        this.terrain[i] = t;
        this.repass(i);
        this.bump();
    }
    occupy(x, y, on) {
        const i = y * this.w + x;
        this.pass_[i] = on ? F.setbit(this.pass_[i], exports.OCC_BIT)
            : F.clrbit(this.pass_[i], exports.OCC_BIT);
    }
    // 건물이 선 칸 — 통행 비트를 내리고 점유 비트를 세운다 (SPEC §4.3).
    // 유닛과 달리 건물은 비키지 않는다. 예약(§13.2)만으로 막으면 유닛이 건물을
    // 향해 24틱을 두드리다 포기하므로, 경로 그래프에서 아예 뺀다.
    // `version` 이 오르니 경로 캐시와 연결 성분이 함께 무효가 된다.
    setBuilding(x, y, on) {
        const i = y * this.w + x;
        if (on) {
            this.pass_[i] = 8; // 점유 비트만 남긴다
        }
        else {
            this.repass(i);
            this.pass_[i] = F.clrbit(this.pass_[i], exports.OCC_BIT);
        }
        this.bump();
    }
    walkable(x, y, kind) {
        if (!this.inMap(x, y))
            return false;
        const p = this.pass_[y * this.w + x];
        return F.bit(p, kind) === 1 && F.bit(p, exports.OCC_BIT) === 0;
    }
    // 점유를 보지 않는 통행 판정 — 경로 탐색은 이것을 쓴다(SPEC §4.3).
    passableTerrain(x, y, kind) {
        if (!this.inMap(x, y))
            return false;
        return F.bit(this.pass_[y * this.w + x], kind) === 1;
    }
    buildable(x, y) {
        if (!this.inMap(x, y))
            return false;
        const p = this.pass_[y * this.w + x];
        return F.bit(p, exports.BUILD_BIT) === 1 && F.bit(p, exports.OCC_BIT) === 0;
    }
    bump() {
        this.version += 1;
        this.labelCache = new Map();
    }
    // ── SPEC §4.4 이웃 마스크 ────────────────────────────────────────────────
    mask(x, y) {
        const t = this.terrainAt(x, y);
        let m = 0;
        for (let d = 0; d < 8; d += 1) {
            if (this.terrainAt(x + F.DX[d], y + F.DY[d]) === t)
                m = F.setbit(m, d);
        }
        return m;
    }
    tileIndex(x, y) {
        return canonIndex(canon(this.mask(x, y)));
    }
    // ── SPEC §4.6 연결 성분 (유니온–파인드) ──────────────────────────────────
    // 통행 가능 칸을 8방향으로 묶은 대표 원소 배열. 막힌 칸은 -1.
    // 지형이 바뀌면 통째로 다시 계산한다. 증분 삭제가 되는 유니온–파인드는
    // 복잡하고, 4096칸 재계산은 측정상 1 ms 미만이다.
    labels(kind) {
        const hit = this.labelCache.get(kind);
        if (hit !== undefined)
            return hit;
        const n = this.w * this.h;
        const parent = new Array(n);
        for (let i = 0; i < n; i += 1)
            parent[i] = i;
        const find = (a0) => {
            let root = a0;
            while (parent[root] !== root)
                root = parent[root];
            let a = a0;
            while (parent[a] !== root) { // 경로 압축
                const nxt = parent[a];
                parent[a] = root;
                a = nxt;
            }
            return root;
        };
        for (let y = 0; y < this.h; y += 1) {
            for (let x = 0; x < this.w; x += 1) {
                if (!this.passableTerrain(x, y, kind))
                    continue;
                let a = find(y * this.w + x);
                for (let d = 0; d < 8; d += 1) {
                    const u = x + F.DX[d];
                    const v = y + F.DY[d];
                    if (this.passableTerrain(u, v, kind)) {
                        const b = find(v * this.w + u);
                        if (a !== b) {
                            parent[b] = a;
                            a = find(a);
                        }
                    }
                }
            }
        }
        const out = new Array(n).fill(-1);
        for (let y = 0; y < this.h; y += 1) {
            for (let x = 0; x < this.w; x += 1) {
                if (this.passableTerrain(x, y, kind)) {
                    out[y * this.w + x] = find(y * this.w + x);
                }
            }
        }
        this.labelCache.set(kind, out);
        return out;
    }
    // ── SPEC §4.7 RLE ────────────────────────────────────────────────────────
    saveRle() {
        const body = [];
        for (const ch of 'RTSM')
            body.push(ch.charCodeAt(0));
        body.push(1);
        body.push(this.w);
        body.push(this.h);
        for (const plane of [this.terrain, this.pass_]) {
            let run = 0;
            let val = -1;
            for (const v of plane) {
                if (v === val && run < 255) {
                    run += 1;
                }
                else {
                    if (run !== 0) {
                        body.push(run);
                        body.push(val);
                    }
                    run = 1;
                    val = v;
                }
            }
            if (run !== 0) {
                body.push(run);
                body.push(val);
            }
        }
        const c = F.crc16(body);
        body.push(F.floordiv(c, 256));
        body.push(F.fmod(c, 256));
        return body;
    }
    static loadRle(blob) {
        const b = [];
        for (let i = 0; i < blob.length; i += 1)
            b.push(blob[i]);
        if (String.fromCharCode(b[0], b[1], b[2], b[3]) !== 'RTSM') {
            throw new Error('맵 파일이 아니다');
        }
        const want = b[b.length - 2] * 256 + b[b.length - 1];
        if (F.crc16(b.slice(0, b.length - 2)) !== want) {
            throw new Error('CRC 불일치 — 맵이 깨졌다');
        }
        const w = b[5];
        const h = b[6];
        const m = new TMap(w, h);
        let pos = 7;
        for (const plane of [m.terrain, m.pass_]) {
            let i = 0;
            while (i < w * h) {
                const run = b[pos];
                const val = b[pos + 1];
                pos += 2;
                for (let k = 0; k < run; k += 1) {
                    plane[i] = val;
                    i += 1;
                }
            }
        }
        m.bump();
        return m;
    }
    // ── 골든 맵 텍스트 (시험용) ──────────────────────────────────────────────
    // golden/map_*.txt 를 읽는다. '.'/'#' 격자와 지형 문자 격자 둘 다.
    static loadText(text) {
        const lines = text.split('\n');
        let w = 0;
        let h = 0;
        let m = null;
        let i = 0;
        while (i < lines.length) {
            const ln = lines[i];
            if (ln.indexOf('size ') === 0) {
                const v = ln.slice(5).trim().split(/\s+/).map((s) => parseInt(s, 10));
                w = v[0];
                h = v[1];
            }
            else if (ln === 'map' || ln === 'terrain') {
                m = new TMap(w, h);
                for (let y = 0; y < h; y += 1) {
                    const row = lines[i + 1 + y];
                    for (let x = 0; x < w; x += 1) {
                        const ch = row[x];
                        if (ln === 'map')
                            m.terrain[y * w + x] = ch === '#' ? exports.ROCK : exports.DIRT;
                        else
                            m.terrain[y * w + x] = exports.TERRAIN_CH.indexOf(ch);
                        m.repass(y * w + x);
                    }
                }
                i += h;
            }
            else if (ln.indexOf('pairs ') === 0) {
                const cnt = parseInt(ln.slice(6), 10);
                for (let k = 0; k < cnt; k += 1) {
                    const v = lines[i + 1 + k].trim().split(/\s+/)
                        .map((s) => parseInt(s, 10));
                    m.pairs.push([[v[0], v[1]], [v[2], v[3]]]);
                }
                i += cnt;
            }
            else if (ln.indexOf('start ') === 0) {
                const cnt = parseInt(ln.slice(6), 10);
                for (let k = 0; k < cnt; k += 1) {
                    const v = lines[i + 1 + k].trim().split(/\s+/)
                        .map((s) => parseInt(s, 10));
                    m.starts.push([v[0], v[1]]);
                }
                i += cnt;
            }
            i += 1;
        }
        m.bump();
        return m;
    }
}
exports.TMap = TMap;
  });
  __def('mapgen', function (exports, require, module, __dirname) {
"use strict";
// 맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·포아송 자원·대칭 (SPEC §5).
//
//    생성기는 게임이 시작하기 전에 한 번만 돈다. 그래서 시뮬레이션 RNG 와
//    **다른 인스턴스**를 쓴다(SPEC §3.3). 여기서 뽑은 난수가 시뮬 수열에
//    끼어들면 두 기계가 같은 맵을 놓고도 다른 게임을 하게 된다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.LAST_ORE = exports.THRESH = exports.ORE_RMIN = exports.ORE_COUNT = exports.ORE_TRIES = exports.START = exports.MH = exports.MW = void 0;
exports.terrainOf = terrainOf;
exports.cellularStep = cellularStep;
exports.cellular = cellular;
exports.diamondSquare = diamondSquare;
exports.placeOre = placeOre;
exports.symmetrize = symmetrize;
exports.clearBase = clearBase;
exports.genStart = genStart;
const rng_1 = require("./rng");
const T = require("./tmap");
exports.MW = 64;
exports.MH = 64;
exports.START = [[8, 8], [55, 55]];
exports.ORE_TRIES = 4000;
exports.ORE_COUNT = 12;
exports.ORE_RMIN = 9;
// 높이 → 지형 (SPEC §5.2). 위에서부터 처음 걸리는 것.
exports.THRESH = [
    [63, T.WATER], [95, T.SAND], [175, T.DIRT], [207, T.HILL], [255, T.ROCK]
];
// 마지막 생성의 광맥 중심점 — 시험·덱용
exports.LAST_ORE = [];
function terrainOf(v) {
    for (const [lim, t] of exports.THRESH) {
        if (v <= lim)
            return t;
    }
    return T.ROCK;
}
function clamp(v) {
    return v < 0 ? 0 : (v > 255 ? 255 : v);
}
// ── SPEC §5.1 셀룰러 오토마타 ───────────────────────────────────────────────
// B5678/S45678 한 세대. 맵 밖은 벽으로 센다.
// 살아 있는 벽은 이웃 벽이 4 이상이면 남고, 빈 칸은 5 이상이면 벽이 된다.
// 2세대면 덩어리가 덜 뭉치고 6세대면 좁은 통로가 전부 막힌다 —
// 4세대가 통로와 개활지가 함께 남는 자리다.
function cellularStep(cur, w, h) {
    const nxt = new Array(w * h).fill(0);
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            let n = 0;
            for (const dy of [-1, 0, 1]) {
                for (const dx of [-1, 0, 1]) {
                    if (dx === 0 && dy === 0)
                        continue;
                    const u = x + dx;
                    const v = y + dy;
                    n += (u >= 0 && u < w && v >= 0 && v < h) ? cur[v * w + u] : 1;
                }
            }
            if (cur[y * w + x] === 1)
                nxt[y * w + x] = n >= 4 ? 1 : 0;
            else
                nxt[y * w + x] = n >= 5 ? 1 : 0;
        }
    }
    return nxt;
}
function cellular(w, h, rand, gens = 4, fill = 45) {
    let cur = [];
    for (let i = 0; i < w * h; i += 1)
        cur.push(rand.roll(100) < fill ? 1 : 0);
    for (let k = 0; k < gens; k += 1)
        cur = cellularStep(cur, w, h);
    return cur;
}
// ── SPEC §5.2 다이아몬드-스퀘어 ─────────────────────────────────────────────
// (2^6)+1 = 65 칸 격자. 평균은 반올림이 아니라 내림이다 — 명세다.
function diamondSquare(rand) {
    const n = 65;
    const h = [];
    for (let y = 0; y < n; y += 1)
        h.push(new Array(n).fill(0));
    for (const [x, y] of [[0, 0], [0, 64], [64, 0], [64, 64]]) {
        h[y][x] = rand.roll(256);
    }
    let step = 64;
    while (step > 1) {
        const half = Math.floor(step / 2);
        const amp = Math.floor(step * 255 / 128);
        for (let y = 0; y < n - 1; y += step) {
            for (let x = 0; x < n - 1; x += step) {
                const a = Math.floor((h[y][x] + h[y][x + step]
                    + h[y + step][x] + h[y + step][x + step]) / 4);
                h[y + half][x + half] = clamp(a + rand.roll(2 * amp + 1) - amp);
            }
        }
        let row = 0;
        for (let y = 0; y < n; y += half) {
            const start = row % 2 === 0 ? half : 0;
            for (let x = start; x < n; x += step) {
                let t = 0;
                let c = 0;
                for (const [dx, dy] of [[-half, 0], [half, 0], [0, -half], [0, half]]) {
                    const u = x + dx;
                    const v = y + dy;
                    if (u >= 0 && u < n && v >= 0 && v < n) {
                        t += h[v][u];
                        c += 1;
                    }
                }
                h[y][x] = clamp(Math.floor(t / c) + rand.roll(2 * amp + 1) - amp);
            }
            row += 1;
        }
        step = half;
    }
    return h;
}
// ── SPEC §5.3 정수 포아송 디스크 ────────────────────────────────────────────
// 앞쪽 절반에만 놓고 대칭 복사한다. 시도 상한이 반드시 있어야 한다 —
// 상한 없는 재시도는 디싱크보다 나쁘다(맵 생성이 영원히 끝나지 않는다).
function placeOre(m, rand, n = exports.ORE_COUNT, rmin = exports.ORE_RMIN) {
    const pts = [];
    let tries = 0;
    while (pts.length < n && tries < exports.ORE_TRIES) {
        tries += 1;
        const x = rand.roll(exports.MW);
        const y = rand.roll(Math.floor(exports.MH / 2));
        const t = m.terrain[y * exports.MW + x];
        if (t !== T.DIRT && t !== T.SAND)
            continue;
        let ok = true;
        for (const [px, py] of pts) {
            if ((x - px) * (x - px) + (y - py) * (y - py) < rmin * rmin) {
                ok = false;
                break;
            }
        }
        if (ok)
            pts.push([x, y]);
    }
    for (const [px, py] of pts) {
        for (let dy = -2; dy <= 2; dy += 1) {
            for (let dx = -2; dx <= 2; dx += 1) {
                if (dx * dx + dy * dy > 4)
                    continue;
                const u = px + dx;
                const v = py + dy;
                if (u >= 0 && u < exports.MW && v >= 0 && v < exports.MH) {
                    const t = m.terrain[v * exports.MW + u];
                    if (t === T.DIRT || t === T.SAND) {
                        m.terrain[v * exports.MW + u] = T.ORE;
                        m.terrain[(exports.MH - 1 - v) * exports.MW + (exports.MW - 1 - u)] = T.ORE;
                    }
                }
            }
        }
    }
    return [pts, tries];
}
// ── SPEC §5.4 대칭과 시작 지점 ──────────────────────────────────────────────
// 180도 회전 대칭. 앞쪽 절반이 원본이다.
function symmetrize(m) {
    for (let y = 0; y < exports.MH; y += 1) {
        for (let x = 0; x < exports.MW; x += 1) {
            if (y * exports.MW + x < exports.MW * exports.MH / 2) {
                m.terrain[(exports.MH - 1 - y) * exports.MW + (exports.MW - 1 - x)] = m.terrain[y * exports.MW + x];
            }
        }
    }
}
// 시작 지점 5×5 를 흙으로 — 사령부 3×3 이 반드시 들어가야 한다.
function clearBase(m) {
    for (const [bx, by] of exports.START) {
        for (let dy = -2; dy <= 2; dy += 1) {
            for (let dx = -2; dx <= 2; dx += 1) {
                const u = bx + dx;
                const v = by + dy;
                if (u >= 0 && u < exports.MW && v >= 0 && v < exports.MH)
                    m.terrain[v * exports.MW + u] = T.DIRT;
            }
        }
    }
}
// 시드를 1씩 올리며 두 시작점이 이어질 때까지 다시 만든다.
// 재시도가 필요하다는 것 자체가 명세의 일부다 — 다이아몬드-스퀘어는
// 가끔 두 기지 사이를 물로 끊어 놓는다.
function genStart(seed0 = 3) {
    let seed = seed0;
    let retries = 0;
    for (;;) {
        const rand = new rng_1.LCG(seed);
        const m = new T.TMap(exports.MW, exports.MH);
        const h = diamondSquare(rand);
        for (let y = 0; y < exports.MH; y += 1) {
            for (let x = 0; x < exports.MW; x += 1)
                m.terrain[y * exports.MW + x] = terrainOf(h[y][x]);
        }
        symmetrize(m);
        const [pts] = placeOre(m, rand);
        clearBase(m);
        for (let i = 0; i < exports.MW * exports.MH; i += 1)
            m.repass(i);
        m.bump();
        m.starts = exports.START.map((p) => [p[0], p[1]]);
        const lab = m.labels(0);
        const a = lab[m.idx(exports.START[0][0], exports.START[0][1])];
        const b = lab[m.idx(exports.START[1][0], exports.START[1][1])];
        if (a === b && a >= 0) {
            exports.LAST_ORE = pts;
            return [m, seed, retries];
        }
        seed += 1;
        retries += 1;
    }
}
  });
  __def('circle', function (exports, require, module, __dirname) {
"use strict";
// 원 마스크 — 시야·스플래시·자원 스탬프가 전부 이것을 쓴다 (SPEC §6).
//
//    고전 미드포인트 원 알고리즘은 여기에 쓰지 않는다. 그것은 *외곽선*을 그리는
//    알고리즘이라 참원에 가장 가까운 점을 고르고, 그 점이 원 안이라는 보장이 없다.
//    r=2 에서 (2,1) 을 찍는데 2²+1² = 5 > 4 다. 시야 마스크로 쓰면 격자점 개수가
//    가우스 원 문제의 값과 어긋난다 — 골든을 처음 만들 때 그 검사가 잡았다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.spans = spans;
exports.offsets = offsets;
exports.count = count;
exports.inDisc = inDisc;
exports.midpointOutline = midpointOutline;
const spanCache = new Map();
const offCache = new Map();
// span[j] = 행 j 에서 원 안에 드는 최대 |i|. 덧셈과 뺄셈만 쓴다.
// 불변식은 t = r² − j² − x² >= 0 이고 x 가 그 조건을 만족하는 최대값이다.
// x 는 결코 늘지 않으므로 전체 비용이 O(r) 이다 (SPEC 정리 6.2).
function spans(r) {
    const hit = spanCache.get(r);
    if (hit !== undefined)
        return hit;
    const out = new Array(r + 1).fill(0);
    out[0] = r;
    let x = r;
    let t = 0;
    for (let j = 1; j <= r; j += 1) {
        t -= 2 * (j - 1) + 1;
        while (t < 0) {
            t += 2 * x - 1;
            x -= 1;
        }
        out[j] = x;
    }
    spanCache.set(r, out);
    return out;
}
// (dx, dy) 목록. dy 오름차순, 같은 dy 안에서 dx 오름차순으로 **고정**한다.
// 순서가 다르면 참조 카운트 결과는 같지만 이벤트 로그의 순서가 달라지고,
// 그 차이가 상태 해시를 가른다(SPEC §6.3).
function offsets(r) {
    const hit = offCache.get(r);
    if (hit !== undefined)
        return hit;
    const sp = spans(r);
    const out = [];
    for (let j = -r; j <= r; j += 1) {
        const w = sp[j >= 0 ? j : -j];
        for (let i = -w; i <= w; i += 1)
            out.push([i, j]);
    }
    offCache.set(r, out);
    return out;
}
function count(r) {
    return offsets(r).length;
}
function inDisc(dx, dy, r) {
    return dx * dx + dy * dy <= r * r;
}
// 고전 미드포인트 '외곽선' — 엔진은 쓰지 않는다. 6부의 대조용으로만 있다.
function midpointOutline(r) {
    const seen = new Set();
    const pts = [];
    let x = r;
    let y = 0;
    let d = 1 - r;
    const add = (a, b) => {
        const key = a + ',' + b;
        if (!seen.has(key)) {
            seen.add(key);
            pts.push([a, b]);
        }
    };
    while (y <= x) {
        add(x, y);
        add(y, x);
        add(-x, y);
        add(-y, x);
        add(x, -y);
        add(y, -x);
        add(-x, -y);
        add(-y, -x);
        y += 1;
        if (d < 0) {
            d += 2 * y + 1;
        }
        else {
            x -= 1;
            d += 2 * (y - x) + 1;
        }
    }
    return pts;
}
  });
  __def('spatial', function (exports, require, module, __dirname) {
"use strict";
// 엔티티와 공간 분할 — SoA·세대 핸들·균일 격자 버킷 (SPEC §7).
//
//    엔티티를 구조체의 배열이 아니라 배열의 구조체로 담는다. 성능도 이유지만
//    더 큰 이유는 **직렬화 순서가 배열 순서로 자동으로 고정**된다는 것이다.
//    상태 해시(SPEC §18.4)가 언어별 필드 순서에 영향을 받지 않는다.
//    그래서 여기서는 객체 배열도, 타입 배열도 쓰지 않는다 — px·py 는 16.16
//    이라 Int32Array 로도 넘칠 수 있고, §19.4 의 주입 버그에서는 실수가 된다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.World = exports.BUCKET = exports.GEN_MOD = exports.MAX_ENT = void 0;
exports.index = index;
exports.generation = generation;
const F = require("./fixed");
exports.MAX_ENT = 256;
exports.GEN_MOD = 256;
exports.BUCKET = 8;
function index(h) {
    return F.floordiv(h, 256);
}
function generation(h) {
    return F.fmod(h, 256);
}
function zeros(n) {
    return new Array(n).fill(0);
}
// 엔티티 배열과 버킷. 시뮬레이션 규칙은 여기 없다 — 담는 그릇일 뿐이다.
class World {
    constructor(w, h) {
        this.w = w;
        this.h = h;
        this.bw = Math.floor((w + exports.BUCKET - 1) / exports.BUCKET);
        this.bh = Math.floor((h + exports.BUCKET - 1) / exports.BUCKET);
        const n = exports.MAX_ENT;
        this.alive = zeros(n);
        this.gen = zeros(n);
        this.owner = zeros(n);
        this.kind = zeros(n);
        this.tx = zeros(n);
        this.ty = zeros(n);
        this.px = zeros(n);
        this.py = zeros(n);
        this.hp = zeros(n);
        this.dir = zeros(n);
        this.state = zeros(n);
        this.target = zeros(n);
        this.load = zeros(n);
        this.prog = zeros(n);
        this.from_t = zeros(n);
        this.to_t = zeros(n);
        this.cool = zeros(n);
        this.timer = zeros(n);
        this.buckets = [];
        for (let i = 0; i < this.bw * this.bh; i += 1)
            this.buckets.push([]);
    }
    // ── SPEC §7.2 핸들 ───────────────────────────────────────────────────────
    handle(i) {
        return i * 256 + this.gen[i];
    }
    valid(h) {
        if (h === 0)
            return false;
        const i = index(h);
        return i > 0 && i < exports.MAX_ENT && this.alive[i] === 1
            && generation(h) === this.gen[i];
    }
    bucketOf(tx, ty) {
        return F.floordiv(ty, exports.BUCKET) * this.bw + F.floordiv(tx, exports.BUCKET);
    }
    // ── 생성·소멸 ────────────────────────────────────────────────────────────
    // 슬롯 0 은 절대 쓰지 않는다 — 핸들 0 이 "없음"을 뜻해야 하기 때문이다.
    spawn(owner, kind, tx, ty) {
        for (let i = 1; i < exports.MAX_ENT; i += 1) {
            if (this.alive[i] === 0) {
                this.alive[i] = 1;
                this.owner[i] = owner;
                this.kind[i] = kind;
                this.tx[i] = tx;
                this.ty[i] = ty;
                this.px[i] = F.fp(tx * 16);
                this.py[i] = F.fp(ty * 16);
                this.dir[i] = 4;
                this.state[i] = 0;
                this.target[i] = 0;
                this.load[i] = 0;
                this.prog[i] = 0;
                this.from_t[i] = ty * this.w + tx;
                this.to_t[i] = ty * this.w + tx;
                this.cool[i] = 0;
                this.timer[i] = 0;
                this.bucketAdd(i);
                return this.handle(i);
            }
        }
        return 0; // 상한 초과 — 조용히 실패한다
    }
    kill(h) {
        if (!this.valid(h))
            return false;
        const i = index(h);
        this.bucketDel(i);
        this.alive[i] = 0;
        this.gen[i] = F.fmod(this.gen[i] + 1, exports.GEN_MOD);
        return true;
    }
    // ── SPEC §7.3 버킷 ───────────────────────────────────────────────────────
    bucketAdd(i) {
        const b = this.buckets[this.bucketOf(this.tx[i], this.ty[i])];
        let k = 0;
        while (k < b.length && b[k] < i)
            k += 1; // 오름차순 유지 — 결정론을 위해서다
        b.splice(k, 0, i);
    }
    bucketDel(i) {
        const b = this.buckets[this.bucketOf(this.tx[i], this.ty[i])];
        const k = b.indexOf(i);
        if (k >= 0)
            b.splice(k, 1);
    }
    // 타일을 넘을 때만 부른다. 픽셀 이동마다 부르는 것이 아니다.
    moveTile(i, tx, ty) {
        if (this.bucketOf(this.tx[i], this.ty[i]) !== this.bucketOf(tx, ty)) {
            this.bucketDel(i);
            this.tx[i] = tx;
            this.ty[i] = ty;
            this.bucketAdd(i);
        }
        else {
            this.tx[i] = tx;
            this.ty[i] = ty;
        }
    }
    // 반경 r(체비셰프) 안의 엔티티 인덱스. 오름차순으로 돌려준다.
    query(tx, ty, r) {
        const out = [];
        const x0 = F.floordiv(Math.max(0, tx - r), exports.BUCKET);
        const x1 = F.floordiv(Math.min(this.w - 1, tx + r), exports.BUCKET);
        const y0 = F.floordiv(Math.max(0, ty - r), exports.BUCKET);
        const y1 = F.floordiv(Math.min(this.h - 1, ty + r), exports.BUCKET);
        for (let by = y0; by <= y1; by += 1) {
            for (let bx = x0; bx <= x1; bx += 1) {
                for (const i of this.buckets[by * this.bw + bx]) {
                    if (F.dinf(this.tx[i] - tx, this.ty[i] - ty) <= r)
                        out.push(i);
                }
            }
        }
        out.sort((a, b) => a - b);
        return out;
    }
}
exports.World = World;
  });
  __def('select', function (exports, require, module, __dirname) {
"use strict";
// 선택과 명령 — 픽킹·상자 선택·컨트롤 그룹·명령 큐 (SPEC §12).
//
//    이 모듈은 **상태를 바꾸지 않는다.** 명령을 만들어 큐에 넣을 뿐이고,
//    그 큐는 net(§19)의 지연 큐를 거쳐 ORDER_DELAY 틱 뒤에 sim.step 의 인자로
//    들어간다. UI 코드가 sim 의 상태를 직접 건드리는 경로는 존재하지 않는다 —
//    이 규율 하나가 락스텝을 가능하게 한다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Orders = exports.Groups = exports.PICK_R = exports.SELECT_MAX = exports.ORDER_MAX = exports.TRAIN = exports.HOLD = exports.STOP = exports.BUILD = exports.HARVEST = exports.ATTACK_MOVE = exports.ATTACK = exports.MOVE = void 0;
exports.inView = inView;
exports.screenToWorld = screenToWorld;
exports.pick = pick;
exports.boxSelect = boxSelect;
exports.contextOrder = contextOrder;
const C = require("./const");
const E = require("./econ");
const F = require("./fixed");
const S = require("./spatial");
// TRAIN 만 유닛이 아니라 건물에게 내리는 명령이다 — UI·AI·스크립트가 모두
// 같은 자료형으로 sim.step 에 들어와야 락스텝이 성립한다(§12.4).
exports.MOVE = 0;
exports.ATTACK = 1;
exports.ATTACK_MOVE = 2;
exports.HARVEST = 3;
exports.BUILD = 4;
exports.STOP = 5;
exports.HOLD = 6;
exports.TRAIN = 7;
exports.ORDER_MAX = 8; // §12.4 유닛당 명령 큐 상한
exports.SELECT_MAX = 32; // §12.2 한 번에 고를 수 있는 유닛 수
exports.PICK_R = 2; // §12.1 버킷 질의 반경 (타일)
// 전장 뷰포트 안인가. 밖이면 패널·미니맵 처리로 넘어간다.
function inView(sx, sy) {
    return sx >= C.VIEW_X && sx < C.VIEW_X + C.VIEW_W
        && sy >= C.VIEW_Y && sy < C.VIEW_Y + C.VIEW_H;
}
function screenToWorld(cam, sx, sy) {
    return [sx - C.VIEW_X + cam[0], sy - C.VIEW_Y + cam[1]];
}
// 엔티티의 월드 픽셀 AABB. px·py 는 이동 중에도 정확하다(§13.1).
function box(w, i) {
    const size = C.TILE * C.FOOT[w.kind[i]];
    const x0 = F.fpFloor(w.px[i]);
    const y0 = F.fpFloor(w.py[i]);
    return [x0, y0, x0 + size, y0 + size];
}
// ── SPEC §12.1 픽킹 ─────────────────────────────────────────────────────────
// 한 점이 가리키는 엔티티 핸들. 없으면 0.
// 앞에 그려진 것이 먼저 잡혀야 하므로 y 내림차순, 동점이면 핸들 내림차순으로
// 훑는다 — §23.3 의 그리기 순서를 거꾸로 도는 것이다.
// `mask(kind, dir, lx, ly)` 는 스프라이트 알파 마스크다. AABB 만으로 끝내지
// 않는 이유는 유닛이 사각형이 아니기 때문이다.
function pick(w, cam, sx, sy, mask) {
    if (!inView(sx, sy))
        return 0;
    const [wx, wy] = screenToWorld(cam, sx, sy);
    const cands = w.query(F.floordiv(wx, C.TILE), F.floordiv(wy, C.TILE), exports.PICK_R);
    const order = cands.slice();
    order.sort((a, b) => {
        if (w.py[a] !== w.py[b])
            return w.py[b] - w.py[a];
        return w.handle(b) - w.handle(a);
    });
    for (const i of order) {
        const [x0, y0, x1, y1] = box(w, i);
        if (!(x0 <= wx && wx < x1 && y0 <= wy && wy < y1))
            continue;
        if (mask !== undefined && !mask(w.kind[i], w.dir[i], wx - x0, wy - y0)) {
            continue;
        }
        return w.handle(i);
    }
    return 0;
}
// ── SPEC §12.2 상자 선택 ────────────────────────────────────────────────────
// 드래그 상자와 겹치는 **내** 엔티티. 유닛이 하나라도 있으면 건물은 뺀다.
// 정렬이 핸들 오름차순인 것은 눈에 보이지 않지만 중요하다 —
// 선택 목록의 순서가 대형 슬롯 배정(§13.5)을 그대로 결정한다.
function boxSelect(w, p, cam, x0in, y0in, x1in, y1in) {
    let x0 = x0in;
    let y0 = y0in;
    let x1 = x1in;
    let y1 = y1in;
    if (x1 < x0) {
        const t = x0;
        x0 = x1;
        x1 = t;
    }
    if (y1 < y0) {
        const t = y0;
        y0 = y1;
        y1 = t;
    }
    const [ax0, ay0] = screenToWorld(cam, x0, y0);
    const [ax1, ay1] = screenToWorld(cam, x1, y1);
    const units = [];
    const builds = [];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0 || w.owner[i] !== p)
            continue;
        const [bx0, by0, bx1, by1] = box(w, i);
        if (bx1 - 1 < ax0 || ax1 < bx0 || by1 - 1 < ay0 || ay1 < by0)
            continue;
        if (C.IS_BUILDING[w.kind[i]] !== 0)
            builds.push(w.handle(i));
        else
            units.push(w.handle(i));
    }
    const out = units.length > 0 ? units : builds;
    out.sort((a, b) => a - b);
    return out.slice(0, exports.SELECT_MAX);
}
// ── SPEC §12.3 컨트롤 그룹 ──────────────────────────────────────────────────
// 저장되는 것은 **핸들**이다. 죽은 유닛은 valid(§7.2)가 자동으로 거른다.
class Groups {
    constructor() {
        this.g = [];
        for (let k = 0; k < 10; k += 1)
            this.g.push([]);
    }
    set(k, sel) {
        this.g[k] = sel.slice();
    }
    recall(w, k) {
        return this.g[k].filter((h) => w.valid(h));
    }
}
exports.Groups = Groups;
// ── SPEC §12.4 명령 큐 ──────────────────────────────────────────────────────
// 유닛당 큐 하나. 기본 클릭은 비우고 하나, 시프트 클릭은 뒤에 붙인다.
class Orders {
    constructor() {
        this.q = [];
        for (let i = 0; i < C.MAX_ENT; i += 1)
            this.q.push([]);
    }
    push(i, order, shift) {
        if (order[0] === exports.STOP) {
            this.q[i] = []; // STOP 은 큐를 비우고 끝이다
            return;
        }
        if (!shift)
            this.q[i] = [];
        if (this.q[i].length < exports.ORDER_MAX)
            this.q[i].push(order);
    }
    pop(i) {
        if (this.q[i].length === 0)
            return null;
        const head = this.q[i][0];
        this.q[i] = this.q[i].slice(1);
        return head;
    }
    clear(i) {
        this.q[i] = [];
    }
}
exports.Orders = Orders;
// 우클릭의 문맥 규칙. 판정 순서가 명세다 — 적 정제소는 반납이 아니라 공격이다.
function contextOrder(w, ec, m, p, tx, ty, h) {
    if (w.valid(h)) {
        const j = S.index(h);
        if (w.owner[j] !== p)
            return exports.ATTACK;
        if (E.DEPOT.indexOf(w.kind[j]) >= 0)
            return exports.HARVEST;
        return exports.MOVE;
    }
    if (m.inMap(tx, ty) && ec.ore[ty * m.w + tx] > 0)
        return exports.HARVEST;
    return exports.MOVE;
}
  });
  __def('path', function (exports, require, module, __dirname) {
"use strict";
// 경로 탐색 — BFS·다익스트라(양동이 큐)·A*(이진 힙) (SPEC §8).
//
//    코너 컷은 **허용한다**. 대각 이동은 도착 칸만 본다. 선택이며, 그 이유와
//    대가는 SPEC §8.1 에 적어 두었다 — 요약하면 JPS 의 가지치기 규칙이
//    코너 컷 격자 위에서 정의되어 있기 때문이다.
//
//    경로 탐색은 점유 비트를 보지 않는다(SPEC §4.3). 움직이는 유닛 때문에
//    경로가 매 틱 흔들리면 무리 이동이 통째로 무너진다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Cache = exports.Heap = exports.NB = exports.INF = void 0;
exports.hOct = hOct;
exports.neighbours = neighbours;
exports.bfs = bfs;
exports.dijkstra = dijkstra;
exports.astar = astar;
exports.closestReachable = closestReachable;
exports.find = find;
const F = require("./fixed");
exports.INF = 1073741824; // 1 << 30 — 시프트는 쓰지 않는다
exports.NB = F.D_DIAG + 1; // 양동이 15개 — 최대 간선 비용보다 커야 한다
// 옥타일 휴리스틱 = 10*max + 4*min. 허용적이고 일관적이다 (정리 8.1/8.2).
function hOct(ax, ay, bx, by) {
    return F.doct(ax - bx, ay - by);
}
// (방향, u, v) — 코너 컷 허용이므로 도착 칸만 검사한다.
function neighbours(m, x, y, kind) {
    const out = [];
    for (let d = 0; d < 8; d += 1) {
        const u = x + F.DX[d];
        const v = y + F.DY[d];
        if (m.passableTerrain(u, v, kind))
            out.push([d, u, v]);
    }
    return out;
}
// ── BFS ─────────────────────────────────────────────────────────────────────
// 걸음 수(가중치 없음). 대각도 한 걸음이다.
function bfs(m, kind, s, t) {
    if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind)))
        return -1;
    const w = m.w;
    const seen = new Array(w * m.h).fill(-1);
    const si = s[1] * w + s[0];
    seen[si] = 0;
    const q = [si];
    let head = 0;
    while (head < q.length) {
        const p = q[head];
        head += 1;
        const x = F.fmod(p, w);
        const y = F.floordiv(p, w);
        if (x === t[0] && y === t[1])
            return seen[p];
        for (let d = 0; d < 8; d += 1) {
            const u = x + F.DX[d];
            const v = y + F.DY[d];
            if (!m.passableTerrain(u, v, kind))
                continue;
            const j = v * w + u;
            if (seen[j] < 0) {
                seen[j] = seen[p] + 1;
                q.push(j);
            }
        }
    }
    return -1;
}
// ── SPEC §8.4 다익스트라 (Dial 양동이 큐) ───────────────────────────────────
// 모든 칸까지의 비용 배열. 간선 비용이 10 과 14 뿐이라 힙이 필요 없다.
// 정리 8.3 이 보장한다 — 처리 중인 거리 cur 와 새 거리 nd 는 항상
// cur <= nd < cur + 15 이므로 원형 양동이 15개면 충돌하지 않는다.
function dijkstra(m, kind, starts, goal) {
    const w = m.w;
    const h = m.h;
    const dist = new Array(w * h).fill(exports.INF);
    const buckets = [];
    for (let k = 0; k < exports.NB; k += 1)
        buckets.push([]);
    let pending = 0;
    for (const s of starts) {
        if (dist[s] > 0) {
            dist[s] = 0;
            buckets[0].push(s);
            pending += 1;
        }
    }
    let cur = 0;
    while (pending > 0) {
        let b = buckets[F.fmod(cur, exports.NB)];
        while (b.length === 0) {
            cur += 1;
            b = buckets[F.fmod(cur, exports.NB)];
        }
        const p = b.pop();
        pending -= 1;
        if (dist[p] !== cur)
            continue; // 낡은 항목 — 감소키를 구현하지 않는다
        if (goal !== undefined && p === goal)
            return dist;
        const x = F.fmod(p, w);
        const y = F.floordiv(p, w);
        for (let d = 0; d < 8; d += 1) {
            const u = x + F.DX[d];
            const v = y + F.DY[d];
            if (!m.passableTerrain(u, v, kind))
                continue;
            const j = v * w + u;
            const nd = cur + F.DCOST[d];
            if (nd < dist[j]) {
                dist[j] = nd;
                buckets[F.fmod(nd, exports.NB)].push(j);
                pending += 1;
            }
        }
    }
    return dist;
}
// ── SPEC §8.5 A* (손으로 쓴 이진 힙) ────────────────────────────────────────
// (f, h, idx) 사전식 최소 힙.
//
//   파이썬 heapq · 루아 table.sort · 자바스크립트 Array.sort 는 서로 다른
//   순서를 낼 수 있다. 비교자가 전순서이기만 하면 손으로 쓴 힙이 세 언어에서
//   같은 순서로 뽑는다 — 그래서 손으로 쓴다.
class Heap {
    constructor() {
        this.a = [];
    }
    get length() {
        return this.a.length;
    }
    static less(x, y) {
        if (x[0] !== y[0])
            return x[0] < y[0];
        if (x[1] !== y[1])
            return x[1] < y[1];
        return x[2] < y[2];
    }
    static le(x, y) {
        return !Heap.less(y, x);
    }
    push(f, hh, idx) {
        const a = this.a;
        a.push([f, hh, idx]);
        let i = a.length - 1;
        while (i > 0) {
            const p = Math.floor((i - 1) / 2);
            if (Heap.le(a[p], a[i]))
                break;
            const tmp = a[p];
            a[p] = a[i];
            a[i] = tmp;
            i = p;
        }
    }
    pop() {
        const a = this.a;
        const top = a[0];
        const last = a.pop();
        if (a.length > 0) {
            a[0] = last;
            let i = 0;
            const n = a.length;
            for (;;) {
                const l = 2 * i + 1;
                const r = 2 * i + 2;
                let s = i;
                if (l < n && Heap.less(a[l], a[s]))
                    s = l;
                if (r < n && Heap.less(a[r], a[s]))
                    s = r;
                if (s === i)
                    break;
                const tmp = a[s];
                a[s] = a[i];
                a[i] = tmp;
                i = s;
            }
        }
        return top;
    }
}
exports.Heap = Heap;
// (비용, 경로 타일 목록, 연 노드 수). 도달 불가면 (-1, [], n).
function astar(m, kind, s, t) {
    const w = m.w;
    if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind)))
        return [-1, [], 0];
    const si = s[1] * w + s[0];
    const ti = t[1] * w + t[0];
    const dist = new Map();
    dist.set(si, 0);
    const prev = new Map();
    const closed = new Set();
    const heap = new Heap();
    const h0 = hOct(s[0], s[1], t[0], t[1]);
    heap.push(h0, h0, si);
    let expanded = 0;
    while (heap.length > 0) {
        const p = heap.pop()[2];
        if (closed.has(p))
            continue;
        closed.add(p); // 일관적이므로 재개방하지 않는다
        expanded += 1;
        if (p === ti) {
            const out = [p];
            while (out[out.length - 1] !== si) {
                out.push(prev.get(out[out.length - 1]));
            }
            out.reverse();
            return [dist.get(p), out, expanded];
        }
        const x = F.fmod(p, w);
        const y = F.floordiv(p, w);
        const dp = dist.get(p);
        for (let d = 0; d < 8; d += 1) {
            const u = x + F.DX[d];
            const v = y + F.DY[d];
            if (!m.passableTerrain(u, v, kind))
                continue;
            const j = v * w + u;
            const nd = dp + F.DCOST[d];
            const old = dist.has(j) ? dist.get(j) : exports.INF;
            if (nd < old) {
                dist.set(j, nd);
                prev.set(j, p);
                const hn = hOct(u, v, t[0], t[1]);
                heap.push(nd + hn, hn, j);
            }
        }
    }
    return [-1, [], expanded];
}
// ── SPEC §8.6 도달 불가 목표 ────────────────────────────────────────────────
// 목표가 다른 성분이면 같은 성분에서 목표에 가장 가까운 칸으로 바꾼다.
// 이 한 줄이 없으면 '섬 건너편 클릭' 한 번이 A* 에게 맵 전체를 펴게 한다.
function closestReachable(m, kind, s, t) {
    const lab = m.labels(kind);
    const si = s[1] * m.w + s[0];
    const ti = t[1] * m.w + t[0];
    if (lab[si] < 0)
        return null;
    if (lab[ti] === lab[si])
        return t;
    let best = null;
    let bd = exports.INF;
    let bi = exports.INF;
    for (let i = 0; i < m.w * m.h; i += 1) {
        if (lab[i] !== lab[si])
            continue;
        const x = F.fmod(i, m.w);
        const y = F.floordiv(i, m.w);
        const d = F.d83(x - t[0], y - t[1]);
        if (d < bd || (d === bd && i < bi)) {
            best = [x, y];
            bd = d;
            bi = i;
        }
    }
    return best;
}
// ── SPEC §8.7 경로 캐시 ─────────────────────────────────────────────────────
// 64칸 LRU. 지형이 바뀌면 통째로 비운다 — 낡은 경로는 곧 디싱크다.
// LRU 순서는 상태가 아니다(해시에 넣지 않는다). 캐시는 같은 답을 더 빨리
// 줄 뿐이고, 다른 답을 주면 그것은 버그다.
class Cache {
    constructor() {
        this.mapVersion = -1;
        this.data = new Map();
        this.order = [];
        this.hits = 0;
        this.misses = 0;
    }
    get(m, key) {
        if (m.version !== this.mapVersion) {
            this.mapVersion = m.version;
            this.data = new Map();
            this.order = [];
        }
        const hit = this.data.get(key);
        if (hit !== undefined) {
            this.hits += 1;
            this.order.splice(this.order.indexOf(key), 1);
            this.order.push(key);
            return hit;
        }
        this.misses += 1;
        return null;
    }
    put(key, value) {
        if (this.data.has(key)) {
            this.order.splice(this.order.indexOf(key), 1);
        }
        else if (this.order.length >= Cache.LIMIT) {
            this.data.delete(this.order.shift());
        }
        this.data.set(key, value);
        this.order.push(key);
    }
}
exports.Cache = Cache;
Cache.LIMIT = 64;
// 캐시를 거치는 표준 경로 질의. 목표가 닿지 않으면 대체 목표로 바꾼다.
function find(m, kind, s, t, cache) {
    const goal = closestReachable(m, kind, s, t);
    if (goal === null)
        return [-1, []];
    const key = ((s[1] * m.w + s[0]) * 4096 + (goal[1] * m.w + goal[0])) * 2 + kind;
    if (cache !== undefined && cache !== null) {
        const hit = cache.get(m, key);
        if (hit !== null)
            return hit;
    }
    const [cost, tiles] = astar(m, kind, s, goal);
    if (cache !== undefined && cache !== null)
        cache.put(key, [cost, tiles]);
    return [cost, tiles];
}
  });
  __def('hpa', function (exports, require, module, __dirname) {
"use strict";
// 계층 경로 탐색 — HPA* 2수준 (SPEC §9, Botea–Müller–Schaeffer 2004).
//
//    **HPA* 는 최적이 아니다.** 원 논문이 보고하는 "최적 대비 1 % 안팎"은
//    그 논문의 맵과 클러스터 크기에서 나온 값이다. 이 엔진의 값은 골든 맵에서
//    직접 재어 out/*_prim.txt 8절에 남기고, 덱은 그 숫자만 쓴다.
//
//    노드는 (x,y) 튜플 대신 `x * 4096 + y` 정수 하나로 담는다. 그래야 노드
//    정렬이 파이썬의 튜플 사전식 정렬과 **정확히 같은 순서**가 되고, 문자열
//    키를 쓸 때 생기는 사전 순회 순서 문제도 아예 생기지 않는다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Abstract = exports.CLUSTER = void 0;
exports.nk = nk;
exports.nkx = nkx;
exports.nky = nky;
exports.clusterOf = clusterOf;
exports.intra = intra;
exports.place = place;
exports.entrances = entrances;
exports.abstract = abstract;
exports.search = search;
exports.refine = refine;
const F = require("./fixed");
const P = require("./path");
exports.CLUSTER = 8;
function nk(x, y) {
    return x * 4096 + y;
}
function nkx(k) {
    return F.floordiv(k, 4096);
}
function nky(k) {
    return F.fmod(k, 4096);
}
function clusterOf(x, y) {
    return [F.floordiv(x, exports.CLUSTER), F.floordiv(y, exports.CLUSTER)];
}
function ck(x, y) {
    return F.floordiv(x, exports.CLUSTER) * 4096 + F.floordiv(y, exports.CLUSTER);
}
// 한 클러스터 안에서만 도는 A*. 8×8 이므로 최악 64칸이다.
function intra(m, kind, a, b) {
    const ax = nkx(a);
    const ay = nky(a);
    const bx = nkx(b);
    const by = nky(b);
    const cx = F.floordiv(ax, exports.CLUSTER);
    const cy = F.floordiv(ay, exports.CLUSTER);
    const loX = cx * exports.CLUSTER;
    const loY = cy * exports.CLUSTER;
    const hiX = loX + exports.CLUSTER - 1;
    const hiY = loY + exports.CLUSTER - 1;
    const dist = new Map();
    dist.set(a, 0);
    const heap = new P.Heap();
    heap.push(P.hOct(ax, ay, bx, by), 0, 0);
    const nodes = [a];
    const closed = new Set();
    while (heap.length > 0) {
        const k = heap.pop()[2];
        const p = nodes[k];
        if (closed.has(p))
            continue;
        closed.add(p);
        if (p === b)
            return dist.get(p);
        const px = nkx(p);
        const py = nky(p);
        const dp = dist.get(p);
        for (const [d, u, v] of P.neighbours(m, px, py, kind)) {
            if (!(u >= loX && u <= hiX && v >= loY && v <= hiY))
                continue;
            const key = nk(u, v);
            const nd = dp + F.DCOST[d];
            const old = dist.has(key) ? dist.get(key) : P.INF;
            if (nd < old) {
                dist.set(key, nd);
                nodes.push(key);
                heap.push(nd + P.hOct(u, v, bx, by), 0, nodes.length - 1);
            }
        }
    }
    return -1;
}
// SPEC §9.2 — 짧은 구간은 가운데 하나, 긴 구간은 양 끝 둘.
function place(run, mk) {
    if (run.length === 0)
        return [];
    if (run.length <= 5)
        return [mk(run[F.floordiv(run.length - 1, 2)])];
    return [mk(run[0]), mk(run[run.length - 1])];
}
// 클러스터 경계에서 양쪽이 모두 통행 가능한 연속 구간을 찾아 전이를 만든다.
function entrances(m, kind) {
    let edges = [];
    const cw = F.floordiv(m.w, exports.CLUSTER);
    const chh = F.floordiv(m.h, exports.CLUSTER);
    for (let cy = 0; cy < chh; cy += 1) {
        for (let cx = 0; cx < cw; cx += 1) {
            if (cx + 1 < cw) {
                const x = cx * exports.CLUSTER + exports.CLUSTER - 1;
                const mkH = (yy) => [[x, yy], [x + 1, yy]];
                let run = [];
                for (let y = cy * exports.CLUSTER; y < cy * exports.CLUSTER + exports.CLUSTER; y += 1) {
                    if (m.passableTerrain(x, y, kind)
                        && m.passableTerrain(x + 1, y, kind)) {
                        run.push(y);
                    }
                    else {
                        edges = edges.concat(place(run, mkH));
                        run = [];
                    }
                }
                edges = edges.concat(place(run, mkH));
            }
            if (cy + 1 < chh) {
                const y = cy * exports.CLUSTER + exports.CLUSTER - 1;
                const mkV = (xx) => [[xx, y], [xx, y + 1]];
                let run = [];
                for (let x = cx * exports.CLUSTER; x < cx * exports.CLUSTER + exports.CLUSTER; x += 1) {
                    if (m.passableTerrain(x, y, kind)
                        && m.passableTerrain(x, y + 1, kind)) {
                        run.push(x);
                    }
                    else {
                        edges = edges.concat(place(run, mkV));
                        run = [];
                    }
                }
                edges = edges.concat(place(run, mkV));
            }
        }
    }
    return edges;
}
// 추상 그래프. 맵 버전이 바뀌면 다시 짓는다.
//
//   인접 목록의 순서는 (1) entrances 가 만든 전이 간선, (2) 같은 클러스터 안
//   노드 쌍의 정렬 순서로 **완전히 결정된다.** 한 노드는 정확히 한 클러스터에만
//   속하므로 클러스터를 어떤 순서로 훑든 결과가 같다 — 파이썬의 집합·사전
//   순회 순서에 기대는 자리가 여기에는 없다.
class Abstract {
    constructor(m, kind) {
        this.version = m.version;
        this.kind = kind;
        this.graph = new Map();
        this.byCluster = new Map();
        const nodes = new Set();
        const addEdge = (a, b, c) => {
            let lst = this.graph.get(a);
            if (lst === undefined) {
                lst = [];
                this.graph.set(a, lst);
            }
            lst.push([b, c]);
        };
        for (const [a, b] of entrances(m, kind)) {
            const ka = nk(a[0], a[1]);
            const kb = nk(b[0], b[1]);
            nodes.add(ka);
            nodes.add(kb);
            addEdge(ka, kb, F.D_STRAIGHT);
            addEdge(kb, ka, F.D_STRAIGHT);
        }
        for (const n of nodes) {
            const c = ck(nkx(n), nky(n));
            let lst = this.byCluster.get(c);
            if (lst === undefined) {
                lst = [];
                this.byCluster.set(c, lst);
            }
            lst.push(n);
        }
        for (const c of Array.from(this.byCluster.keys())) {
            const ns = this.byCluster.get(c).slice();
            ns.sort((a, b) => a - b);
            this.byCluster.set(c, ns);
            for (let i = 0; i < ns.length; i += 1) {
                for (let j = i + 1; j < ns.length; j += 1) {
                    const c1 = intra(m, kind, ns[i], ns[j]);
                    if (c1 >= 0) {
                        addEdge(ns[i], ns[j], c1);
                        addEdge(ns[j], ns[i], c1);
                    }
                }
            }
        }
    }
}
exports.Abstract = Abstract;
const cacheByMap = new WeakMap();
function abstract(m, kind) {
    let per = cacheByMap.get(m);
    if (per === undefined) {
        per = new Map();
        cacheByMap.set(m, per);
    }
    let a = per.get(kind);
    if (a === undefined || a.version !== m.version) {
        a = new Abstract(m, kind);
        per.set(kind, a);
    }
    return a;
}
// 추상 그래프 위의 A*. 정련 경로의 비용은 추상 비용과 같다.
function search(m, kind, s, t) {
    if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind)))
        return [-1, []];
    const ab = abstract(m, kind);
    const graph = new Map();
    for (const [k, v] of ab.graph)
        graph.set(k, v.slice());
    const addEdge = (a, b, c) => {
        let lst = graph.get(a);
        if (lst === undefined) {
            lst = [];
            graph.set(a, lst);
        }
        lst.push([b, c]);
    };
    const sk = nk(s[0], s[1]);
    const tk = nk(t[0], t[1]);
    for (const temp of [sk, tk]) { // 임시 노드 삽입 (질의가 끝나면 버린다)
        const near = ab.byCluster.get(ck(nkx(temp), nky(temp)));
        for (const n of (near === undefined ? [] : near)) {
            const c1 = intra(m, kind, temp, n);
            if (c1 >= 0) {
                addEdge(temp, n, c1);
                addEdge(n, temp, c1);
            }
        }
    }
    if (ck(s[0], s[1]) === ck(t[0], t[1])) {
        const c1 = intra(m, kind, sk, tk);
        if (c1 >= 0)
            addEdge(sk, tk, c1);
    }
    const dist = new Map();
    dist.set(sk, 0);
    const prev = new Map();
    const closed = new Set();
    const heap = new P.Heap();
    const nodes = [sk];
    heap.push(P.hOct(s[0], s[1], t[0], t[1]), 0, 0);
    while (heap.length > 0) {
        const k = heap.pop()[2];
        const p = nodes[k];
        if (closed.has(p))
            continue;
        closed.add(p);
        if (p === tk) {
            const out = [p];
            while (prev.has(out[out.length - 1])) {
                out.push(prev.get(out[out.length - 1]));
            }
            out.reverse();
            return [dist.get(p), out];
        }
        const dp = dist.get(p);
        const adj = graph.get(p);
        for (const [n, c1] of (adj === undefined ? [] : adj)) {
            const nd = dp + c1;
            const old = dist.has(n) ? dist.get(n) : P.INF;
            if (nd < old) {
                dist.set(n, nd);
                prev.set(n, p);
                nodes.push(n);
                heap.push(nd + P.hOct(nkx(n), nky(n), t[0], t[1]), 0, nodes.length - 1);
            }
        }
    }
    return [-1, []];
}
// 추상 경로의 인접 노드 쌍을 클러스터 안 A* 로 실제 타일 열로 편다.
function refine(m, kind, absnodes) {
    let out = [];
    for (let i = 0; i < absnodes.length - 1; i += 1) {
        const a = absnodes[i];
        const b = absnodes[i + 1];
        const ax = nkx(a);
        const ay = nky(a);
        const bx = nkx(b);
        const by = nky(b);
        let tiles;
        if (ck(ax, ay) === ck(bx, by)) {
            tiles = P.astar(m, kind, [ax, ay], [bx, by])[1];
        }
        else {
            tiles = [ay * m.w + ax, by * m.w + bx];
        }
        if (out.length > 0 && tiles.length > 0
            && out[out.length - 1] === tiles[0]) {
            tiles = tiles.slice(1);
        }
        out = out.concat(tiles);
    }
    return out;
}
  });
  __def('jps', function (exports, require, module, __dirname) {
"use strict";
// 점프 포인트 탐색 — Harabor & Grastien 2011 (SPEC §10).
//
//    격자의 대칭 경로를 가지치기해 A* 가 여는 노드 수를 줄인다. 비용은 A* 와
//    **정확히 같다**. 그 등가성을 정리로 옮겨 적는 대신 전수 검사로 증명한다
//    (tests/test_jps.ts).
//
//    여기 있는 가지치기 규칙은 **코너 컷을 허용하는 격자**의 것이다. 금지하면
//    강제 이웃 조건이 통째로 달라진다 — 그것이 SPEC §8.1 에서 코너 컷을
//    허용하기로 한 첫 번째 이유다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.forced = forced;
exports.jump = jump;
exports.prune = prune;
exports.search = search;
const F = require("./fixed");
const P = require("./path");
// (x,y) 에 방향 (dx,dy) 로 들어왔을 때 강제 이웃이 있는가 (SPEC §10.1).
function forced(m, x, y, dx, dy, kind) {
    const ok = (u, v) => m.passableTerrain(u, v, kind);
    if (dx !== 0 && dy !== 0) {
        return (!ok(x - dx, y) && ok(x - dx, y + dy))
            || (!ok(x, y - dy) && ok(x + dx, y - dy));
    }
    if (dx !== 0) {
        for (const s of [-1, 1]) {
            if (!ok(x, y + s) && ok(x + dx, y + s))
                return true;
        }
        return false;
    }
    for (const s of [-1, 1]) {
        if (!ok(x + s, y) && ok(x + s, y + dy))
            return true;
    }
    return false;
}
// 방향 (dx,dy) 로 계속 나아가다 점프점을 만나면 그 칸을 돌려준다.
// 대각 점프가 먼저 두 성분 방향을 재귀로 훑는 것이 핵심이다. 그 방향에서
// 점프점이 나오면 지금 서 있는 대각 칸 자체가 점프점이 된다.
function jump(m, x, y, dx, dy, t, kind) {
    const u = x + dx;
    const v = y + dy;
    if (!m.passableTerrain(u, v, kind))
        return null;
    if (u === t[0] && v === t[1])
        return [u, v];
    if (forced(m, u, v, dx, dy, kind))
        return [u, v];
    if (dx !== 0 && dy !== 0) {
        if (jump(m, u, v, dx, 0, t, kind) !== null
            || jump(m, u, v, 0, dy, t, kind) !== null)
            return [u, v];
    }
    return jump(m, u, v, dx, dy, t, kind);
}
// 부모에서 온 방향에 따라 살아남는 이웃 방향들 (SPEC §10.1).
function prune(m, x, y, parent, kind) {
    const ok = (u, v) => m.passableTerrain(u, v, kind);
    if (parent === null) {
        const out = [];
        for (let d = 0; d < 8; d += 1) {
            if (ok(x + F.DX[d], y + F.DY[d]))
                out.push([F.DX[d], F.DY[d]]);
        }
        return out;
    }
    const px = parent[0];
    const py = parent[1];
    const dx = (x - px > 0 ? 1 : 0) - (x - px < 0 ? 1 : 0);
    const dy = (y - py > 0 ? 1 : 0) - (y - py < 0 ? 1 : 0);
    const out = [];
    if (dx !== 0 && dy !== 0) {
        if (ok(x + dx, y))
            out.push([dx, 0]);
        if (ok(x, y + dy))
            out.push([0, dy]);
        if (ok(x + dx, y + dy))
            out.push([dx, dy]);
        if (!ok(x - dx, y) && ok(x - dx, y + dy))
            out.push([-dx, dy]);
        if (!ok(x, y - dy) && ok(x + dx, y - dy))
            out.push([dx, -dy]);
    }
    else if (dx !== 0) {
        if (ok(x + dx, y))
            out.push([dx, 0]);
        for (const s of [-1, 1]) {
            if (!ok(x, y + s) && ok(x + dx, y + s))
                out.push([dx, s]);
        }
    }
    else {
        if (ok(x, y + dy))
            out.push([0, dy]);
        for (const s of [-1, 1]) {
            if (!ok(x + s, y) && ok(x + s, y + dy))
                out.push([s, dy]);
        }
    }
    return out;
}
// (비용, 점프점 목록, 연 노드 수). A* 와 같은 비교자·같은 힙을 쓴다.
function search(m, kind, s, t) {
    const w = m.w;
    if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind)))
        return [-1, [], 0];
    const si = s[1] * w + s[0];
    const ti = t[1] * w + t[0];
    const dist = new Map();
    dist.set(si, 0);
    const parent = new Map();
    parent.set(si, null);
    const closed = new Set();
    const heap = new P.Heap();
    const h0 = P.hOct(s[0], s[1], t[0], t[1]);
    heap.push(h0, h0, si);
    let expanded = 0;
    while (heap.length > 0) {
        const p = heap.pop()[2];
        if (closed.has(p))
            continue;
        closed.add(p);
        expanded += 1;
        const x = F.fmod(p, w);
        const y = F.floordiv(p, w);
        if (p === ti) {
            const out = [p];
            for (;;) {
                const q = parent.get(out[out.length - 1]);
                if (q === null)
                    break;
                out.push(q[1] * w + q[0]);
            }
            out.reverse();
            return [dist.get(p), out, expanded];
        }
        const par = parent.get(p);
        const dp = dist.get(p);
        for (const [dx, dy] of prune(m, x, y, par, kind)) {
            const n = jump(m, x, y, dx, dy, t, kind);
            if (n === null)
                continue;
            const steps = Math.max(Math.abs(n[0] - x), Math.abs(n[1] - y));
            const nd = dp + steps * ((dx !== 0 && dy !== 0) ? F.D_DIAG : F.D_STRAIGHT);
            const j = n[1] * w + n[0];
            const old = dist.has(j) ? dist.get(j) : P.INF;
            if (nd < old) {
                dist.set(j, nd);
                parent.set(j, [x, y]);
                const hn = P.hOct(n[0], n[1], t[0], t[1]);
                heap.push(nd + hn, hn, j);
            }
        }
    }
    return [-1, [], expanded];
}
  });
  __def('flow', function (exports, require, module, __dirname) {
"use strict";
// 흐름장·클리어런스·브러시파이어 (SPEC §11).
//
//    A* 는 "한 유닛이 한 목표로" 가는 도구다. 무리 40기가 같은 깃발로 몰려갈 때
//    A* 를 40번 부르는 것은 같은 답을 40번 계산하는 것이다. 적분장은 반대로
//    목표에서 한 번 거꾸로 퍼뜨려 두고, 유닛은 자기 칸의 방향 하나만 읽는다.
//
//    여기의 모든 장은 **지형만** 본다. 점유 비트를 넣으면 유닛이 움직일 때마다
//    장을 다시 깔아야 하고, 그러면 애초에 장을 쓰는 이유가 없어진다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.STOP = exports.NB = exports.INF = void 0;
exports.integration = integration;
exports.flowDirs = flowDirs;
exports.clearance = clearance;
exports.sizePassable = sizePassable;
exports.brushfire = brushfire;
const F = require("./fixed");
exports.INF = 65535; // SPEC §11.1 — 세 언어가 같은 수를 찍어야 한다
exports.NB = F.D_DIAG + 1; // 양동이 15개 (§8.4 와 같은 이유)
exports.STOP = 255;
// 다중 시작점 다익스트라. seeds 는 (칸번호, 초기비용) 목록.
// O(칸수 × 8) 시간, O(칸수) 공간. 간선 비용이 10 과 14 둘뿐이라
// 원형 양동이 15개로 힙 없이 돈다 — 정리 8.3 이 그대로 적용된다.
function dial(m, kind, seeds) {
    const w = m.w;
    const h = m.h;
    const dist = new Array(w * h).fill(exports.INF);
    const buckets = [];
    for (let k = 0; k < exports.NB; k += 1)
        buckets.push([]);
    let pending = 0;
    let lo = exports.INF;
    for (const [i, c] of seeds) {
        if (c < dist[i]) {
            dist[i] = c;
            buckets[F.fmod(c, exports.NB)].push(i);
            pending += 1;
            if (c < lo)
                lo = c;
        }
    }
    if (pending === 0)
        return dist;
    let cur = lo;
    while (pending > 0) {
        let b = buckets[F.fmod(cur, exports.NB)];
        while (b.length === 0) {
            cur += 1;
            b = buckets[F.fmod(cur, exports.NB)];
        }
        const p = b.pop();
        pending -= 1;
        if (dist[p] !== cur)
            continue; // 낡은 항목 — 감소키는 만들지 않는다
        const x = F.fmod(p, w);
        const y = F.floordiv(p, w);
        for (let d = 0; d < 8; d += 1) {
            const u = x + F.DX[d];
            const v = y + F.DY[d];
            if (!m.passableTerrain(u, v, kind))
                continue; // 통행 가능 칸으로만
            const nd = cur + F.DCOST[d];
            const j = v * w + u;
            if (nd < dist[j]) {
                dist[j] = nd;
                buckets[F.fmod(nd, exports.NB)].push(j);
                pending += 1;
            }
        }
    }
    return dist;
}
// ── SPEC §11.1 적분장 ───────────────────────────────────────────────────────
// 목표 집합에서 거꾸로 퍼뜨린 비용장. 도달 불가는 INF.
// 막힌 목표는 무시한다(§11.1). 닿을 수 없는 칸을 0 으로 심으면 장 전체가
// 그쪽으로 기울고, 그것은 §8.6 의 대체 목표가 맡을 몫이다.
function integration(m, kind, goals) {
    const seeds = [];
    for (const [x, y] of goals) {
        if (m.passableTerrain(x, y, kind))
            seeds.push([y * m.w + x, 0]);
    }
    return dial(m, kind, seeds);
}
// ── SPEC §11.2 경사장 ───────────────────────────────────────────────────────
// 각 칸에서 갈 방향. 후보가 없으면 255(정지).
// 동점은 **방향 번호가 작은 쪽**이다. 언어별 min 구현에 맡기면 대칭 맵에서
// 무리가 좌우로 갈리고, 그 갈림은 PPM 바이트 비교에서 바로 잡힌다.
function flowDirs(m, kind, integ) {
    const w = m.w;
    const h = m.h;
    const out = new Array(w * h).fill(exports.STOP);
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            const i = y * w + x;
            if (integ[i] >= exports.INF || !m.passableTerrain(x, y, kind))
                continue;
            let best = exports.INF;
            let bd = exports.STOP;
            for (let d = 0; d < 8; d += 1) {
                const u = x + F.DX[d];
                const v = y + F.DY[d];
                if (!m.passableTerrain(u, v, kind))
                    continue;
                const c = integ[v * w + u];
                if (c < best) { // 등호를 빼면 작은 d 가 이긴다
                    best = c;
                    bd = d;
                }
            }
            out[i] = bd;
        }
    }
    return out;
}
// ── SPEC §11.3 클리어런스 ───────────────────────────────────────────────────
// clear[i] = (x,y) 를 좌상단으로 하는 통행 가능 정사각형의 최대 변 (정리 11.1).
// O(칸수) 시간, O(칸수) 공간 — 오른쪽 아래에서 한 번만 훑는다.
// 맵 밖은 0 이므로 오른쪽·아래 가장자리의 자유 칸은 1 이 된다.
function clearance(m, kind) {
    const w = m.w;
    const h = m.h;
    const c = new Array(w * h).fill(0);
    for (let y = h - 1; y >= 0; y -= 1) {
        for (let x = w - 1; x >= 0; x -= 1) {
            if (!m.passableTerrain(x, y, kind))
                continue;
            if (x + 1 >= w || y + 1 >= h) {
                c[y * w + x] = 1;
            }
            else {
                const r = c[y * w + x + 1];
                const d = c[(y + 1) * w + x];
                const q = c[(y + 1) * w + x + 1];
                c[y * w + x] = 1 + Math.min(r, d, q);
            }
        }
    }
    return c;
}
// 크기 size 인 유닛이 (x,y) 를 좌상단으로 설 수 있는가.
function sizePassable(clear, m, x, y, size) {
    if (!m.inMap(x, y))
        return false;
    return clear[y * m.w + x] >= size;
}
// ── SPEC §11.4 브러시파이어 ─────────────────────────────────────────────────
// 가장 가까운 막힌 칸까지의 옥타일 비용. 막힌 칸은 0.
// 맵 밖도 막힌 칸이다(§4.2 의 terrain_at 규약). 그래서 가장자리 자유 칸은
// 10 이고, AI 는 맵 끝에 건물을 붙이지 않는다(§17.4).
function brushfire(m, kind) {
    const w = m.w;
    const h = m.h;
    const seeds = [];
    for (let y = 0; y < h; y += 1) {
        for (let x = 0; x < w; x += 1) {
            if (!m.passableTerrain(x, y, kind)) {
                seeds.push([y * w + x, 0]);
                continue;
            }
            let best = exports.INF;
            for (let d = 0; d < 8; d += 1) { // 맵 밖 이웃은 비용 0 짜리 시작점이다
                if (!m.inMap(x + F.DX[d], y + F.DY[d])) {
                    if (F.DCOST[d] < best)
                        best = F.DCOST[d];
                }
            }
            if (best < exports.INF)
                seeds.push([y * w + x, best]);
        }
    }
    return dial(m, kind, seeds);
}
  });
  __def('move', function (exports, require, module, __dirname) {
"use strict";
// 이동·예약·밀어내기·대형 — SPEC §13.
//
//    이 모듈의 전부는 불변식 R 하나다: **어떤 타일도 두 엔티티에게 동시에
//    예약되지 않는다.** 걸음을 시작할 때 도착 칸을 먼저 쥐고, 걸음이 끝나야
//    출발 칸을 놓는다. 두 칸을 쥐는 구간이 있어야 두 유닛이 서로의 칸으로
//    동시에 들어가는 사고가 없다.
//
//    교착은 완전히 사라지지 않는다. 좁은 통로에서 마주 오는 두 무리는 24틱 뒤
//    명령을 포기하는 것으로 풀린다 — 해결이 아니라 포기다(§13.3).
Object.defineProperty(exports, "__esModule", { value: true });
exports.Movement = exports.STOP_DIR = exports.BOX = exports.COLUMN = exports.LINE = exports.GIVEUP_TICKS = exports.REPATH_TICKS = exports.ARRIVE_R = void 0;
exports.stepAmount = stepAmount;
exports.posOf = posOf;
exports.rot8 = rot8;
exports.formation = formation;
exports.pushDir = pushDir;
const C = require("./const");
const F = require("./fixed");
const P = require("./path");
const S = require("./spatial");
exports.ARRIVE_R = 2; // §13.4 도착 반경 (타일, 체비셰프)
exports.REPATH_TICKS = 8; // §13.3 이만큼 막히면 경로를 다시 찾는다
exports.GIVEUP_TICKS = 24; // §13.3 이만큼 막히면 명령을 포기한다
exports.LINE = 0; // §13.5 대형
exports.COLUMN = 1;
exports.BOX = 2;
exports.STOP_DIR = 255;
// ── SPEC §13.1 타일 사이 보간 ───────────────────────────────────────────────
const SQRT2 = Math.sqrt(2.0); // §19.4 의 주입 버그에서만 쓴다
// 방향 d 로 한 틱에 늘어나는 진행률 (16.16).
//
//   대각 보정을 빼면 유닛이 대각으로 √2 = 41 % 빨라진다. 도스 시절에도
//   이 버그를 그대로 둔 게임이 있었고, 그래서 플레이어들이 지그재그로 움직였다.
//
//   `floatBug` 는 §19.4 의 **일부러 넣은** 디싱크다. 1/√2 는 이진 소수로
//   끝나지 않으므로 진행률이 정수가 아니게 되고, 그 누적 차이가 px·py 를 통해
//   상태 해시에 바로 나타난다. **엔진의 다른 어느 곳도 실수를 쓰지 않는다.**
function stepAmount(speed, d, floatBug = false) {
    const st = F.fpDiv(speed, F.fp(C.TILE));
    if (F.DCOST[d] === F.D_DIAG) {
        if (floatBug)
            return st / SQRT2;
        return F.fpMul(st, F.FP_DIAG);
    }
    return st;
}
// 화면 위치는 상태가 아니라 from_t·to_t·prog 의 파생값이다 (§13.1).
function posOf(w, m, i) {
    const fx = F.fmod(w.from_t[i], m.w);
    const fy = F.floordiv(w.from_t[i], m.w);
    const tx = F.fmod(w.to_t[i], m.w);
    const ty = F.floordiv(w.to_t[i], m.w);
    const px = F.fp(fx * C.TILE) + F.fpMul(F.fp((tx - fx) * C.TILE), w.prog[i]);
    const py = F.fp(fy * C.TILE) + F.fpMul(F.fp((ty - fy) * C.TILE), w.prog[i]);
    return [px, py];
}
// ── SPEC §13.5 회전과 대형 ──────────────────────────────────────────────────
// 이동 방향 d 로 오프셋을 돌린다. 행렬이 아니라 8방향 표다.
// 45° 회전은 정수 격자를 보존하지 않으므로 대각은 이웃한 두 직교 방향의
// 결과를 더해 2로 내림 나눗셈한다 — 근사이며, 그렇다고 적어 둔다.
function rot8(d, ox, oy) {
    if (d === 0)
        return [ox, oy];
    if (d === 2)
        return [-oy, ox];
    if (d === 4)
        return [-ox, -oy];
    if (d === 6)
        return [oy, -ox];
    const [ax, ay] = rot8(d - 1, ox, oy);
    const [bx, by] = rot8(F.fmod(d + 1, 8), ox, oy);
    return [F.floordiv(ax + bx, 2), F.floordiv(ay + by, 2)];
}
// 목표 주위 n 개의 슬롯 타일. 슬롯 순서 = 핸들 오름차순으로 나눠 준다.
// 맵 밖이거나 통행 불가인 슬롯은 목표 타일 자체로 접는다. 슬롯을 다시
// 찾아 주지는 않는다 — 반쯤 성공하는 재배치가 교착보다 나쁜 그림을 만든다.
function formation(n, shape, d, gx, gy, m, kind) {
    const out = [];
    if (n <= 0)
        return out;
    const side = F.isqrt(n - 1) + 1; // ceil(sqrt(n)) — §2.5 정수 제곱근
    for (let k = 0; k < n; k += 1) {
        let ox = 0;
        let oy = 0;
        if (shape === exports.LINE) {
            ox = k - F.floordiv(n - 1, 2);
            oy = 0;
        }
        else if (shape === exports.COLUMN) {
            ox = 0;
            oy = k;
        }
        else {
            ox = F.fmod(k, side) - F.floordiv(side - 1, 2);
            oy = F.floordiv(k, side);
        }
        const [rx, ry] = rot8(d, ox, oy);
        let x = gx + rx;
        let y = gy + ry;
        if (!m.passableTerrain(x, y, kind)) {
            x = gx;
            y = gy;
        }
        out.push([x, y]);
    }
    return out;
}
// ── SPEC §13.3 밀어내기 ─────────────────────────────────────────────────────
// i 를 어느 방향으로 비키게 할지. 없으면 255.
// 훑는 순서는 미는 쪽 진행 방향의 **반대에서 시작해 시계 방향**이다.
// 순서를 명세로 고정하지 않으면 세 언어가 다른 칸을 고르고, 그 차이는
// 한 틱 뒤 위치 차이가 되어 그대로 디싱크다.
function pushDir(mv, i, fromDir) {
    const w = mv.w;
    const m = mv.m;
    const kind = C.MOVE_KIND[w.kind[i]];
    for (let k = 0; k < 8; k += 1) {
        const d = F.fmod(fromDir + 4 + k, 8);
        const u = w.tx[i] + F.DX[d];
        const v = w.ty[i] + F.DY[d];
        if (!m.passableTerrain(u, v, kind))
            continue;
        if (mv.resv[v * m.w + u] !== 0)
            continue;
        return d;
    }
    return exports.STOP_DIR;
}
// 예약판과 유닛별 경로. sim 이 하나만 들고 있는다 (§18.2 4단계).
class Movement {
    constructor(world, tmap, floatBug = false) {
        this.w = world;
        this.m = tmap;
        this.floatBug = floatBug;
        this.resv = new Array(tmap.w * tmap.h).fill(0);
        this.blocked = new Array(C.MAX_ENT).fill(0);
        this.path = [];
        for (let i = 0; i < C.MAX_ENT; i += 1)
            this.path.push([]);
        this.goal = new Array(C.MAX_ENT).fill(-1);
        this.cache = new P.Cache();
        this.crossed = [];
    }
    // ── SPEC §13.2 예약 ──────────────────────────────────────────────────────
    reserve(tile, h) {
        const cur = this.resv[tile];
        if (cur !== 0 && cur !== h)
            return false;
        this.resv[tile] = h;
        return true;
    }
    release(tile, h) {
        if (this.resv[tile] !== h)
            return false;
        this.resv[tile] = 0;
        return true;
    }
    // 엔티티가 선 칸을 예약한다. 건물은 발자국 전체를 영구히 쥔다.
    claim(i) {
        const w = this.w;
        const m = this.m;
        const h = w.handle(i);
        const f = C.FOOT[w.kind[i]];
        let ok = true;
        for (let dy = 0; dy < f; dy += 1) {
            for (let dx = 0; dx < f; dx += 1) {
                const x = w.tx[i] + dx;
                const y = w.ty[i] + dy;
                if (!m.inMap(x, y))
                    continue;
                if (!this.reserve(y * m.w + x, h))
                    ok = false;
                if (C.IS_BUILDING[w.kind[i]] !== 0)
                    m.setBuilding(x, y, true);
                else
                    m.occupy(x, y, true);
            }
        }
        return ok;
    }
    // 사망·철거. 건물은 잔해를 남기므로 통행이 지형에서 복구된다(§4.3).
    unclaim(i) {
        const w = this.w;
        const m = this.m;
        const h = w.handle(i);
        const f = C.FOOT[w.kind[i]];
        for (let dy = 0; dy < f; dy += 1) {
            for (let dx = 0; dx < f; dx += 1) {
                const x = w.tx[i] + dx;
                const y = w.ty[i] + dy;
                if (!m.inMap(x, y))
                    continue;
                this.release(y * m.w + x, h);
                if (C.IS_BUILDING[w.kind[i]] !== 0)
                    m.setBuilding(x, y, false);
                else
                    m.occupy(x, y, false);
            }
        }
        this.release(w.to_t[i], h);
        this.path[i] = [];
        this.goal[i] = -1;
        this.blocked[i] = 0;
    }
    // ── 명령 ─────────────────────────────────────────────────────────────────
    // 목표 타일로 가는 경로를 깐다. 닿을 수 없으면 §8.6 의 대체 목표로.
    order(i, gx, gy) {
        if (!this.m.inMap(gx, gy))
            return false;
        this.blocked[i] = 0;
        return this.plan(i, gx, gy);
    }
    // 경로만 다시 깐다 — blocked 카운터는 건드리지 않는다(§13.3 재탐색).
    plan(i, gx, gy) {
        const w = this.w;
        const m = this.m;
        const kind = C.MOVE_KIND[w.kind[i]];
        const s = [w.tx[i], w.ty[i]];
        const goal = P.closestReachable(m, kind, s, [gx, gy]);
        if (goal === null) {
            this.path[i] = [];
            this.goal[i] = -1;
            return false;
        }
        const [, tiles] = P.find(m, kind, s, goal, this.cache);
        this.path[i] = tiles.slice(1);
        this.goal[i] = this.path[i].length > 0 ? goal[1] * m.w + goal[0] : -1;
        return true;
    }
    // §12.4 STOP — 아직 시작하지 않은 걸음의 예약만 반납한다(§13.2).
    stop(i) {
        const w = this.w;
        this.path[i] = [];
        this.goal[i] = -1;
        this.blocked[i] = 0;
        if (w.prog[i] === 0 && w.to_t[i] !== w.from_t[i]) {
            this.release(w.to_t[i], w.handle(i));
            w.to_t[i] = w.from_t[i];
        }
    }
    // ── SPEC §18.2 4단계: 핸들 오름차순으로 한 틱 ────────────────────────────
    step() {
        const w = this.w;
        this.crossed = [];
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 1 && C.IS_BUILDING[w.kind[i]] === 0)
                this.stepOne(i);
        }
    }
    stepOne(i) {
        const w = this.w;
        const m = this.m;
        const h = w.handle(i);
        if (w.prog[i] > 0) { // 걸음 도중 — 끝까지 마친다
            w.prog[i] += stepAmount(C.SPEED[w.kind[i]], w.dir[i], this.floatBug);
            if (w.prog[i] >= F.FP_ONE)
                this.finishStep(i, h);
            const [px, py] = posOf(w, m, i);
            w.px[i] = px;
            w.py[i] = py;
            return;
        }
        if (this.path[i].length === 0)
            return;
        if (this.arrived(i, h))
            return;
        const nxt = this.path[i][0];
        const d = F.atan8(F.fmod(nxt, m.w) - w.tx[i], F.floordiv(nxt, m.w) - w.ty[i]);
        if (!this.reserve(nxt, h)) {
            this.onBlocked(i, d);
            return;
        }
        this.blocked[i] = 0;
        w.dir[i] = d;
        w.to_t[i] = nxt;
        w.prog[i] = stepAmount(C.SPEED[w.kind[i]], d, this.floatBug);
        if (w.prog[i] >= F.FP_ONE)
            this.finishStep(i, h); // 아주 빠른 유닛
        const [px, py] = posOf(w, m, i);
        w.px[i] = px;
        w.py[i] = py;
    }
    finishStep(i, h) {
        const w = this.w;
        const m = this.m;
        const old = w.from_t[i];
        this.release(old, h);
        m.occupy(F.fmod(old, m.w), F.floordiv(old, m.w), false);
        w.from_t[i] = w.to_t[i];
        w.prog[i] = 0;
        const nx = F.fmod(w.to_t[i], m.w);
        const ny = F.floordiv(w.to_t[i], m.w);
        w.moveTile(i, nx, ny);
        m.occupy(nx, ny, true);
        this.crossed.push([i, old, w.to_t[i]]);
        if (this.path[i].length > 0 && this.path[i][0] === w.to_t[i]) {
            this.path[i] = this.path[i].slice(1);
        }
        if (this.path[i].length === 0)
            this.goal[i] = -1;
    }
    // §13.4 목표 칸이 남의 것이고 ARRIVE_R 안이면 도착으로 친다.
    // 이것이 없으면 무리의 마지막 한 기가 영원히 목표 칸을 두드린다.
    arrived(i, h) {
        const w = this.w;
        const m = this.m;
        const g = this.goal[i];
        if (g < 0)
            return false;
        const taken = this.resv[g];
        if (taken === 0 || taken === h)
            return false;
        if (F.dinf(F.fmod(g, m.w) - w.tx[i], F.floordiv(g, m.w) - w.ty[i]) > exports.ARRIVE_R)
            return false;
        this.path[i] = [];
        this.goal[i] = -1;
        this.blocked[i] = 0;
        return true;
    }
    // §13.3 막힘 — 8틱이면 재탐색, 24틱이면 포기.
    onBlocked(i, d) {
        const w = this.w;
        const m = this.m;
        this.blocked[i] += 1;
        const nxt = this.path[i][0];
        const other = this.resv[nxt];
        if (w.valid(other)) {
            const j = S.index(other);
            if (w.owner[j] === w.owner[i] && w.prog[j] === 0
                && this.path[j].length === 0 && C.IS_BUILDING[w.kind[j]] === 0) {
                const pd = pushDir(this, j, d); // 정지한 아군은 비켜 준다
                if (pd !== exports.STOP_DIR) {
                    this.path[j] = [(w.ty[j] + F.DY[pd]) * m.w + w.tx[j] + F.DX[pd]];
                    this.goal[j] = this.path[j][0];
                }
            }
        }
        if (this.blocked[i] >= exports.GIVEUP_TICKS) {
            this.path[i] = [];
            this.goal[i] = -1;
            this.blocked[i] = 0;
        }
        else if (this.blocked[i] === exports.REPATH_TICKS && this.goal[i] >= 0) {
            const g = this.goal[i];
            this.plan(i, F.fmod(g, m.w), F.floordiv(g, m.w));
        }
    }
}
exports.Movement = Movement;
  });
  __def('fog', function (exports, require, module, __dirname) {
"use strict";
// 시야와 안개 — 참조 카운트 세 평면 (SPEC §14).
//
//    안개는 **그리기 단계에서만** 쓰인다. 시뮬레이션은 안개를 무시한다 —
//    안개를 시뮬레이션의 일부로 만들면 플레이어마다 상태가 갈리고, 그러면
//    락스텝의 전제가 무너진다(§14.5).
//
//    칸당 1바이트를 쓴다. 비트 플레인이 8배 작지만 참조 카운트는 비트로 담을 수
//    없다. 비트 플레인은 저장·전송용 `packBits` 로만 남겼다(§14.2).
Object.defineProperty(exports, "__esModule", { value: true });
exports.Fog = void 0;
const CI = require("./circle");
const C = require("./const");
const F = require("./fixed");
// 플레이어마다 explored·count 두 평면. visible 은 count > 0 의 별칭이다.
class Fog {
    constructor(w, h, players = C.MAX_PLAYER) {
        this.w = w;
        this.h = h;
        this.count = [];
        this.explored = [];
        for (let p = 0; p < players; p += 1) {
            this.count.push(new Array(w * h).fill(0));
            this.explored.push(new Array(w * h).fill(0));
        }
    }
    visible(p, i) {
        return this.count[p][i] > 0;
    }
    // ── SPEC §14.3 증분 갱신 ─────────────────────────────────────────────────
    // O(r²) — 원 안의 칸마다 카운트 +1 과 탐험 표시.
    addSight(p, tx, ty, r) {
        const cnt = this.count[p];
        const exp = this.explored[p];
        for (const [dx, dy] of CI.offsets(r)) {
            const x = tx + dx;
            const y = ty + dy;
            if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
                const i = y * this.w + x;
                cnt[i] += 1;
                exp[i] = 1;
            }
        }
    }
    // 카운트 −1. 0 아래로는 내려가지 않는다 — 내려간다면 그것은 버그다.
    removeSight(p, tx, ty, r) {
        const cnt = this.count[p];
        for (const [dx, dy] of CI.offsets(r)) {
            const x = tx + dx;
            const y = ty + dy;
            if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
                const i = y * this.w + x;
                if (cnt[i] > 0)
                    cnt[i] -= 1;
            }
        }
    }
    // 타일을 넘을 때 — **빼기가 먼저다**(§14.3).
    moveSight(p, ox, oy, nx, ny, r) {
        this.removeSight(p, ox, oy, r);
        this.addSight(p, nx, ny, r);
    }
    // 불변식 F 를 전수로 검증하고 **어긋난 칸 수만** 돌려준다.
    // 고치지 않는 이유는 하나다. 증분 갱신이 새면 그것은 버그이고,
    // 조용히 고쳐 버리면 그 버그는 영원히 드러나지 않는다.
    recount(world) {
        const want = [];
        for (let p = 0; p < this.count.length; p += 1) {
            want.push(new Array(this.w * this.h).fill(0));
        }
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (world.alive[i] === 0)
                continue;
            const r = C.SIGHT[world.kind[i]];
            const p = world.owner[i];
            if (p >= want.length)
                continue;
            for (const [dx, dy] of CI.offsets(r)) { // 건물의 시야 중심은 좌상단이다
                const x = world.tx[i] + dx;
                const y = world.ty[i] + dy;
                if (x >= 0 && x < this.w && y >= 0 && y < this.h) {
                    want[p][y * this.w + x] += 1;
                }
            }
        }
        let bad = 0;
        for (let p = 0; p < this.count.length; p += 1) {
            for (let i = 0; i < this.w * this.h; i += 1) {
                if (this.count[p][i] !== want[p][i])
                    bad += 1;
            }
        }
        return bad;
    }
    // ── SPEC §14.4 4단계 렌더 ────────────────────────────────────────────────
    // 0 미탐험 · 1 탐험 · 2 경계 · 3 가시.
    // 2단계는 순전히 눈을 위한 것이다. 1과 3만 있으면 안개 경계가 계단처럼 보인다.
    level(p, x, y) {
        if (!(x >= 0 && x < this.w && y >= 0 && y < this.h))
            return 0;
        const i = y * this.w + x;
        if (this.count[p][i] > 0)
            return 3;
        if (this.explored[p][i] === 0)
            return 0;
        for (const dy of [-1, 0, 1]) {
            for (const dx of [-1, 0, 1]) {
                const u = x + dx;
                const v = y + dy;
                if (u >= 0 && u < this.w && v >= 0 && v < this.h
                    && this.count[p][v * this.w + u] > 0)
                    return 2;
            }
        }
        return 1;
    }
    // ── SPEC §14.2 비트 플레인 (저장·전송용) ─────────────────────────────────
    // 탐험 평면 8칸을 1바이트로. 칸 i 는 바이트 i//8 의 2^(i%8) 자리다.
    // 비트 연산자를 쓰지 않는다(§1.1) — 곱셈과 덧셈이면 충분하다.
    packBits(p) {
        const n = this.w * this.h;
        const out = new Array(Math.floor((n + 7) / 8)).fill(0);
        const exp = this.explored[p];
        for (let i = 0; i < n; i += 1) {
            if (exp[i] !== 0)
                out[F.floordiv(i, 8)] += F.pow2(F.fmod(i, 8));
        }
        return out;
    }
    unpackBits(p, data) {
        const n = this.w * this.h;
        const exp = this.explored[p];
        for (let i = 0; i < n; i += 1) {
            exp[i] = F.fmod(F.floordiv(data[F.floordiv(i, 8)], F.pow2(F.fmod(i, 8))), 2);
        }
    }
}
exports.Fog = Fog;
  });
  __def('combat', function (exports, require, module, __dirname) {
"use strict";
// 전투 — 피해·표적·투사체·스플래시·란체스터 (SPEC §15).
//
//    피해 공식은 워크래프트 II 의 공식 문서를 따랐다(§15.2). 다만 "50 %에서
//    100 % 사이"의 **반올림 방향**은 블리자드 문서에 없고 팬 사이트의 역산이
//    출처다. 하한 1(방어가 아무리 높아도 피해 1)은 이 덱의 규칙이다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Projectiles = exports.SPLASH_RINGS = exports.ARC_DIV = exports.ARC_MIN_TICKS = exports.ARROW_SPEED = exports.G = exports.ARC = exports.STRAIGHT = void 0;
exports.maxDamage = maxDamage;
exports.damageLo = damageLo;
exports.rollDamage = rollDamage;
exports.expect100 = expect100;
exports.inRange = inRange;
exports.pickTarget = pickTarget;
exports.splashDamage = splashDamage;
exports.splashHits = splashHits;
exports.lanchesterSim = lanchesterSim;
const C = require("./const");
const F = require("./fixed");
exports.STRAIGHT = 0;
exports.ARC = 1;
exports.G = 1638; // 0.025 px/틱², 16.16
exports.ARROW_SPEED = F.fp(4); // 화살·총알 4 px/틱 (§15.3)
exports.ARC_MIN_TICKS = 6;
exports.ARC_DIV = 24;
exports.SPLASH_RINGS = 3;
// ── SPEC §15.2 피해 공식 ────────────────────────────────────────────────────
// 최대 피해 = 기본 − 방어 + 관통, 하한 1.
// 하한이 없으면 방어력이 높은 유닛은 **절대 죽지 않는다**. 이 하한은
// 블리자드 문서에 없는 이 덱의 규칙이다.
function maxDamage(basic, pierce, armour) {
    const mx = basic - armour + pierce;
    return mx < 1 ? 1 : mx;
}
// 최대치의 50 %, 올림. 올림이라는 부분은 2차 출처다(§15.2).
function damageLo(mx) {
    return F.floordiv(mx + 1, 2);
}
function rollDamage(rng, basic, pierce, armour) {
    const mx = maxDamage(basic, pierce, armour);
    const lo = damageLo(mx);
    return lo + rng.roll(mx - lo + 1);
}
// E[dmg] × 100 (정리 15.1). 정수만 쓰려고 100배로 둔다.
function expect100(basic, pierce, armour) {
    const mx = maxDamage(basic, pierce, armour);
    return (damageLo(mx) + mx) * 50;
}
// ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
// 체비셰프 거리 — 8방향 격자에서 '몇 걸음 안'과 정확히 같다.
function inRange(w, i, j) {
    return F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]) <= C.RANGE[w.kind[i]];
}
function isEnemy(w, i, j) {
    return w.alive[j] === 1 && w.owner[j] !== w.owner[i] && w.hp[j] > 0;
}
// 사거리 안 적 중 d83 최소, 동점이면 핸들 오름차순.
// 동점 규칙이 명세인 이유는 대칭 맵에서 동점이 흔하기 때문이다.
// 두 기계가 다른 표적을 고르면 그 틱부터 상태가 갈린다.
function nearest(w, i, reach) {
    let best = 0;
    let bd = -1;
    for (let j = 1; j < C.MAX_ENT; j += 1) {
        if (!isEnemy(w, i, j))
            continue;
        const d = F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]);
        if (d > reach)
            continue;
        const s = F.d83(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]);
        if (bd < 0 || s < bd) { // 핸들 오름차순으로 훑으므로
            bd = s; // 등호를 빼면 작은 핸들이 이긴다
            best = w.handle(j);
        }
    }
    return best;
}
// (표적 핸들, 접근이 필요한가). 규칙 순서는 §15.1 그대로다.
function pickTarget(w, i, lastHitter, attackMove) {
    if (C.BASIC[w.kind[i]] === 0)
        return [0, false]; // 채집기·비무장 건물
    const reach = C.RANGE[w.kind[i]];
    const cur = w.target[i];
    if (w.valid(cur)) {
        const j = F.floordiv(cur, 256);
        if (isEnemy(w, i, j) && inRange(w, i, j))
            return [cur, false]; // 1) 표적 유지
    }
    if (w.valid(lastHitter)) {
        const j = F.floordiv(lastHitter, 256);
        if (isEnemy(w, i, j) && inRange(w, i, j))
            return [lastHitter, false]; // 2)
    }
    let h = nearest(w, i, reach); // 3) 가장 가까운 적
    if (h !== 0)
        return [h, false];
    if (attackMove) { // 4) ATTACK_MOVE 만 두 칸 더 본다
        h = nearest(w, i, reach + 2);
        if (h !== 0)
            return [h, true];
    }
    return [0, false];
}
// ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
// 링 단위 감쇠 — 0링 전액, 1링 1/2, 2링 1/4, 그 밖은 0. 나눗셈은 내림.
function splashDamage(dmg, ring) {
    if (ring >= exports.SPLASH_RINGS)
        return 0;
    return F.floordiv(dmg, F.pow2(ring));
}
// (핸들, 피해) 목록, 핸들 오름차순. **아군도 맞는다**.
// 같은 유닛이 두 링에 걸치는 일은 없다 — 대표 타일 하나로 판정하기 때문이다.
function splashHits(w, tx, ty, dmg) {
    const out = [];
    for (let j = 1; j < C.MAX_ENT; j += 1) {
        if (w.alive[j] === 0 || w.hp[j] <= 0)
            continue;
        const ring = F.dinf(w.tx[j] - tx, w.ty[j] - ty);
        const d = splashDamage(dmg, ring);
        if (d > 0)
            out.push([w.handle(j), d]);
    }
    return out;
}
// ── SPEC §15.3·15.4 투사체 ──────────────────────────────────────────────────
// SoA 로 담는다 — 상태 해시(§18.4)가 배열 순서로 자동 고정되기 때문이다.
class Projectiles {
    constructor(mapW) {
        this.mapW = mapW;
        this.x = [];
        this.y = [];
        this.vx = [];
        this.vy = [];
        this.ttl = [];
        this.target = [];
        this.dmg = [];
        this.kind = [];
        this.dest = [];
    }
    n() {
        return this.x.length;
    }
    tile(x, y) {
        return F.floordiv(F.fpFloor(y), C.TILE) * this.mapW
            + F.floordiv(F.fpFloor(x), C.TILE);
    }
    // 좌표는 전부 16.16 픽셀. 같은 칸이면 발사하지 않는다(즉시 명중).
    // **표적을 쫓지 않는다.** 발사 시점의 위치로 날아가므로 빠른 유닛은
    // 화살을 피할 수 있다 — 이것도 이 덱의 규칙이다.
    launch(kind, x0, y0, x1, y1, speed, target, dmg) {
        const dx = F.fpFloor(x1) - F.fpFloor(x0);
        const dy = F.fpFloor(y1) - F.fpFloor(y0);
        const d = F.isqrt(dx * dx + dy * dy);
        if (d === 0)
            return false;
        let vx = 0;
        let vy = 0;
        let ttl = 0;
        if (kind === exports.ARC) {
            let t = exports.ARC_MIN_TICKS;
            if (F.floordiv(d, exports.ARC_DIV) > t)
                t = F.floordiv(d, exports.ARC_DIV);
            vx = F.fpDiv(x1 - x0, F.fp(t));
            vy = F.fpDiv(y1 - y0, F.fp(t))
                - F.fpMul(exports.G, F.fpDiv(F.fp(t), F.fp(2)));
            ttl = t;
        }
        else {
            vx = F.fpMul(F.fpDiv(F.fp(dx), F.fp(d)), speed);
            vy = F.fpMul(F.fpDiv(F.fp(dy), F.fp(d)), speed);
            ttl = F.floordiv(F.fp(d), speed) + 2;
        }
        this.x.push(x0);
        this.y.push(y0);
        this.vx.push(vx);
        this.vy.push(vy);
        this.ttl.push(ttl);
        this.target.push(target);
        this.dmg.push(dmg);
        this.kind.push(kind);
        this.dest.push(this.tile(x1, y1));
        return true;
    }
    // 한 틱. 명중한 것을 (핸들, 피해, 착탄 타일, 착탄 y, 종류) 로 돌려주고 지운다.
    // 마지막 칸이 종류인 이유는 sim 이 포물선 명중에만 스플래시(§15.5)를
    // 적용해야 하기 때문이다.
    step() {
        const hits = [];
        const keep = [];
        for (let k = 0; k < this.x.length; k += 1) {
            if (this.kind[k] === exports.ARC)
                this.vy[k] += exports.G; // 수직은 중력만
            this.x[k] += this.vx[k];
            this.y[k] += this.vy[k];
            this.ttl[k] -= 1;
            if (this.tile(this.x[k], this.y[k]) === this.dest[k] || this.ttl[k] <= 0) {
                hits.push([this.target[k], this.dmg[k], this.dest[k], this.y[k],
                    this.kind[k]]);
            }
            else {
                keep.push(k);
            }
        }
        if (keep.length !== this.x.length) {
            this.x = keep.map((k) => this.x[k]);
            this.y = keep.map((k) => this.y[k]);
            this.vx = keep.map((k) => this.vx[k]);
            this.vy = keep.map((k) => this.vy[k]);
            this.ttl = keep.map((k) => this.ttl[k]);
            this.target = keep.map((k) => this.target[k]);
            this.dmg = keep.map((k) => this.dmg[k]);
            this.kind = keep.map((k) => this.kind[k]);
            this.dest = keep.map((k) => this.dest[k]);
        }
        return hits;
    }
}
exports.Projectiles = Projectiles;
// ── SPEC §15.6 란체스터 ─────────────────────────────────────────────────────
// 정수 이산 시뮬. 폐형해(정리 15.4)는 엔진이 아니라 gen_prim 이 계산한다.
// 종료 조건이 `>= FP_ONE` 인 것이 중요하다. `> 0` 으로 두면 A 가 0.5 인
// 상태에서 감소량이 내림으로 0 이 되어 영원히 돌지 않는다.
function lanchesterSim(a0, b0, alpha, beta) {
    let a = F.fp(a0);
    let b = F.fp(b0);
    let t = 0;
    while (a >= F.FP_ONE && b >= F.FP_ONE && t < 10000) {
        const da = F.fpMul(beta, b);
        const db = F.fpMul(alpha, a);
        a -= da;
        b -= db;
        if (a < 0)
            a = 0;
        if (b < 0)
            b = 0;
        t += 1;
    }
    return [t, F.fpFloor(a), F.fpFloor(b)];
}
  });
  __def('econ', function (exports, require, module, __dirname) {
"use strict";
// 경제 — 자원·채집기 FSM·생산 큐·기술 트리·인구 (SPEC §16).
//
//    생산은 **선불**이다. 큐에 넣는 순간 크레딧이 빠진다. 후불로 두면 "완성
//    시점에 돈이 없는" 상태가 생기고, 그 처리 규칙이 언어마다 미묘하게 갈릴
//    여지가 생긴다 — 결정론을 위해 게임 디자인을 고른 자리다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Econ = exports.DEPOT = exports.H_IDLE = exports.H_UNLOAD = exports.H_TO_BASE = exports.H_MINE = exports.H_TO_ORE = exports.H_SEEK = exports.TOUCH_R = exports.BASE_R = exports.SUPPLY_MAX = exports.QUEUE_MAX = exports.UNLOAD_TICKS = exports.MINE_PER_TICK = exports.LOAD_MAX = exports.ORE_PER_TILE = void 0;
exports.roundTripTicks = roundTripTicks;
exports.income10000 = income10000;
exports.topoOrder = topoOrder;
const C = require("./const");
const F = require("./fixed");
const T = require("./tmap");
exports.ORE_PER_TILE = 500;
exports.LOAD_MAX = 100;
exports.MINE_PER_TICK = 5;
exports.UNLOAD_TICKS = 12;
exports.QUEUE_MAX = 5;
exports.SUPPLY_MAX = 100;
exports.BASE_R = 4; // §16.5 기지 반경 (체비셰프, 건물 원점 기준)
exports.TOUCH_R = 1; // 채집기가 "닿았다"고 보는 거리
// §16.2 채집기 FSM 상태 — 번호는 const 가 소유한다(§17.1 의 표).
exports.H_SEEK = C.ST_SEEK;
exports.H_TO_ORE = C.ST_TO_ORE;
exports.H_MINE = C.ST_MINE;
exports.H_TO_BASE = C.ST_TO_BASE;
exports.H_UNLOAD = C.ST_UNLOAD;
exports.H_IDLE = C.ST_IDLE;
exports.DEPOT = [C.HQ, C.REF]; // 자원 반납처 (§25.2)
// ── SPEC §16.3 수입률 (정리 16.1) ───────────────────────────────────────────
// 왕복 d 타일, 속도 v(16.16 타일/틱)인 채집기 한 기의 주기 (틱).
// 세 항은 왕복 이동·채굴·반납이다. d 가 0 이어도 20 + 12 = 32틱이 든다 —
// **정제소를 광맥에 붙여도 상한이 있다.**
function roundTripTicks(d, v) {
    return F.floordiv(F.fp(2 * d), v)
        + F.floordiv(exports.LOAD_MAX, exports.MINE_PER_TICK) + exports.UNLOAD_TICKS;
}
// 크레딧/틱 × 10000. 나눗셈 한 번으로 끝내려고 정수 배율을 쓴다.
function income10000(d, v) {
    return F.floordiv(exports.LOAD_MAX * 10000, roundTripTicks(d, v));
}
// ── SPEC §16.6 기술 트리 = DAG (정리 16.2) ──────────────────────────────────
// 칸(Kahn) 위상 정렬. 진입차수 0 은 **번호 오름차순**으로 꺼낸다.
// 순환이 있으면 null 을 돌려준다 — 조용히 넘어가지 않는다. 기술 트리는
// 데이터이고, 데이터가 잘못되면 터지는 편이 낫다.
function topoOrder(extra) {
    const pre = [];
    for (let k = 0; k < C.KIND_COUNT; k += 1)
        pre.push(C.PREREQ[k].slice());
    for (const [k, p] of (extra === undefined ? [] : extra)) {
        pre[k] = pre[k].concat([p]);
    }
    const indeg = pre.map((v) => v.length);
    const out = [];
    const done = new Array(C.KIND_COUNT).fill(0);
    for (;;) {
        let pick = -1;
        for (let k = 0; k < C.KIND_COUNT; k += 1) { // 오름차순 선형 탐색 — 16개다
            if (done[k] === 0 && indeg[k] === 0) {
                pick = k;
                break;
            }
        }
        if (pick < 0)
            break;
        done[pick] = 1;
        out.push(pick);
        for (let k = 0; k < C.KIND_COUNT; k += 1) {
            if (done[k] === 0 && pre[k].indexOf(pick) >= 0)
                indeg[k] -= 1;
        }
    }
    if (out.length !== C.KIND_COUNT)
        return null; // 남은 노드가 있으면 순환이다
    return out;
}
// 플레이어별 크레딧·인구, 타일별 광맥, 건물별 생산 큐.
class Econ {
    constructor(m) {
        this.ore = new Array(m.w * m.h).fill(0);
        for (let i = 0; i < m.w * m.h; i += 1) {
            if (m.terrain[i] === T.ORE)
                this.ore[i] = exports.ORE_PER_TILE;
        }
        this.credits = new Array(C.MAX_PLAYER).fill(0);
        this.supplyUsed = new Array(C.MAX_PLAYER).fill(0);
        this.supplyCap = new Array(C.MAX_PLAYER).fill(0);
        this.queue = [];
        for (let i = 0; i < C.MAX_ENT; i += 1)
            this.queue.push([]);
        this.progress = new Array(C.MAX_ENT).fill(0);
        this.oreTarget = new Array(C.MAX_ENT).fill(-1);
    }
    // ── SPEC §16.1 자원 ──────────────────────────────────────────────────────
    // **도달 가능한** 광맥 중 d83 최소, 동점이면 타일 번호 오름차순. 없으면 −1.
    // 도달 가능 판정을 빼면 채집기가 바위 건너편 광맥을 잡고 §8.6 의 대체
    // 목표가 제자리를 돌려주어 영원히 선다(SPEC §16.2).
    nearestOre(m, x, y, kind = 0) {
        const lab = m.labels(kind);
        const here = m.inMap(x, y) ? lab[y * m.w + x] : -1;
        let best = -1;
        let bd = -1;
        for (let i = 0; i < m.w * m.h; i += 1) {
            if (this.ore[i] <= 0)
                continue;
            if (here >= 0 && lab[i] !== here)
                continue; // 다른 성분 — 걸어서 못 간다
            const d = F.d83(F.fmod(i, m.w) - x, F.floordiv(i, m.w) - y);
            if (bd < 0 || d < bd) {
                bd = d;
                best = i;
            }
        }
        return best;
    }
    // 캔 양을 돌려준다. 다 캐면 그 칸은 모래가 되고 지형 version 이 오른다.
    mine(m, tile, amount) {
        let got = this.ore[tile];
        if (got > amount)
            got = amount;
        this.ore[tile] -= got;
        if (this.ore[tile] <= 0 && m.terrain[tile] === T.ORE) {
            m.setTerrain(F.fmod(tile, m.w), F.floordiv(tile, m.w), T.SAND);
        }
        return got;
    }
    // ── SPEC §16.4 생산 큐 ───────────────────────────────────────────────────
    enqueue(w, bi, kind) {
        const p = w.owner[bi];
        if (this.queue[bi].length >= exports.QUEUE_MAX)
            return false;
        if (!this.canBuild(w, p, kind))
            return false;
        if (this.credits[p] < C.COST[kind])
            return false;
        if (C.IS_BUILDING[kind] === 0) {
            if (this.supplyUsed[p] + this.reserved(w, p) + C.POP[kind]
                > this.supplyCap[p])
                return false; // 큐에 든 것도 인구를 먹는다
        }
        this.credits[p] -= C.COST[kind]; // 선불
        this.queue[bi].push(kind);
        return true;
    }
    // 큐에 들어 있는 유닛이 예약한 인구. 이것을 빼면 상한이 헐거워진다.
    reserved(w, p) {
        let n = 0;
        for (let bi = 1; bi < C.MAX_ENT; bi += 1) {
            if (w.alive[bi] === 0 || w.owner[bi] !== p)
                continue;
            for (const kind of this.queue[bi]) {
                if (C.IS_BUILDING[kind] === 0)
                    n += C.POP[kind];
            }
        }
        return n;
    }
    // 환불은 100 %. 이 덱의 규칙이며, 부분 환불은 반올림 규칙을 하나 더 만든다.
    cancel(w, bi, k) {
        if (k < 0 || k >= this.queue[bi].length)
            return 0;
        const kind = this.queue[bi][k];
        this.queue[bi] = this.queue[bi].slice(0, k)
            .concat(this.queue[bi].slice(k + 1));
        if (k === 0)
            this.progress[bi] = 0;
        this.credits[w.owner[bi]] += C.COST[kind];
        return C.COST[kind];
    }
    // 한 틱. 완성된 (건물 인덱스, 종류) 목록을 인덱스 오름차순으로.
    stepProduction(w) {
        const done = [];
        for (let bi = 1; bi < C.MAX_ENT; bi += 1) {
            if (w.alive[bi] === 0 || this.queue[bi].length === 0)
                continue;
            const kind = this.queue[bi][0];
            this.progress[bi] += 1;
            if (this.progress[bi] >= C.BUILD_TICKS[kind]) {
                this.progress[bi] = 0;
                this.queue[bi] = this.queue[bi].slice(1);
                done.push([bi, kind]);
            }
        }
        return done;
    }
    // 선행이 **완성된 채 살아 있는지** 본다. 병영이 부서지면 보병을 못 뽑는다.
    canBuild(w, p, kind) {
        for (const need of C.PREREQ[kind]) {
            let found = false;
            for (let j = 1; j < C.MAX_ENT; j += 1) {
                if (w.alive[j] === 1 && w.owner[j] === p && w.kind[j] === need
                    && w.hp[j] > 0) {
                    found = true;
                    break;
                }
            }
            if (!found)
                return false;
        }
        return true;
    }
    // ── SPEC §16.5 배치 판정 ─────────────────────────────────────────────────
    // 발자국 전체가 건설 가능 지형이고 비어 있고, 기지에서 4타일 안.
    placeable(w, m, mv, kind, x, y, p) {
        const f = C.FOOT[kind];
        for (let dy = 0; dy < f; dy += 1) {
            for (let dx = 0; dx < f; dx += 1) {
                const u = x + dx;
                const v = y + dy;
                if (!m.inMap(u, v))
                    return false;
                const i = v * m.w + u;
                if (F.bit(m.pass_[i], T.BUILD_BIT) !== 1)
                    return false;
                if (mv.resv[i] !== 0)
                    return false;
            }
        }
        let near = false;
        let anyOwn = false;
        for (let j = 1; j < C.MAX_ENT; j += 1) {
            if (w.alive[j] === 1 && w.owner[j] === p
                && C.IS_BUILDING[w.kind[j]] === 1) {
                anyOwn = true;
                if (F.dinf(w.tx[j] - x, w.ty[j] - y) <= exports.BASE_R) {
                    near = true;
                    break;
                }
            }
        }
        return near || !anyOwn; // 첫 건물은 면제
    }
    // ── SPEC §16.7 인구 ──────────────────────────────────────────────────────
    // 유닛은 먹고 건물은 준다. 상한 100. 매 틱 전수로 세도 256칸이다.
    recountSupply(w) {
        for (let p = 0; p < C.MAX_PLAYER; p += 1) {
            this.supplyUsed[p] = 0;
            this.supplyCap[p] = 0;
        }
        for (let j = 1; j < C.MAX_ENT; j += 1) {
            if (w.alive[j] === 0 || w.hp[j] <= 0)
                continue;
            const p = w.owner[j];
            if (p >= C.MAX_PLAYER)
                continue;
            if (C.IS_BUILDING[w.kind[j]] !== 0)
                this.supplyCap[p] += C.POP[w.kind[j]];
            else
                this.supplyUsed[p] += C.POP[w.kind[j]];
        }
        for (let p = 0; p < C.MAX_PLAYER; p += 1) {
            if (this.supplyCap[p] > exports.SUPPLY_MAX)
                this.supplyCap[p] = exports.SUPPLY_MAX;
        }
    }
    // ── SPEC §16.2 채집기 FSM ────────────────────────────────────────────────
    // 건물 발자국의 어느 칸에라도 한 칸 안으로 붙었는가.
    touching(w, i, bi) {
        const f = C.FOOT[w.kind[bi]];
        let dx = 0;
        if (w.tx[i] < w.tx[bi])
            dx = w.tx[bi] - w.tx[i];
        else if (w.tx[i] > w.tx[bi] + f - 1)
            dx = w.tx[i] - (w.tx[bi] + f - 1);
        let dy = 0;
        if (w.ty[i] < w.ty[bi])
            dy = w.ty[bi] - w.ty[i];
        else if (w.ty[i] > w.ty[bi] + f - 1)
            dy = w.ty[i] - (w.ty[bi] + f - 1);
        return F.dinf(dx, dy) <= exports.TOUCH_R;
    }
    nearestDepot(w, i) {
        let best = 0;
        let bd = -1;
        for (let j = 1; j < C.MAX_ENT; j += 1) {
            if (w.alive[j] === 0 || w.owner[j] !== w.owner[i]
                || exports.DEPOT.indexOf(w.kind[j]) < 0 || w.hp[j] <= 0)
                continue;
            const d = F.d83(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i]);
            if (bd < 0 || d < bd) {
                bd = d;
                best = w.handle(j);
            }
        }
        return best;
    }
    // 건물 발자국을 둘러싼 고리에서 채집기가 붙을 칸 (SPEC §16.2).
    // 건물 원점으로 그냥 명령하면 §8.6 의 대체 목표가 "건물 반대편"이나
    // 심지어 "지금 서 있는 칸"을 고를 수 있다 — d83 동점에서 타일 번호가
    // 작은 쪽이 이기기 때문이다. 그러면 채집기가 적재를 든 채 굳는다.
    dock(w, m, mv, i, bi) {
        const kind = C.MOVE_KIND[w.kind[i]];
        const f = C.FOOT[w.kind[bi]];
        let best = null;
        for (const ignoreResv of [false, true]) {
            let bd = -1;
            let bt = -1;
            for (let dy = -1; dy <= f; dy += 1) {
                for (let dx = -1; dx <= f; dx += 1) {
                    if (dx >= 0 && dx < f && dy >= 0 && dy < f)
                        continue; // 발자국 내부
                    const x = w.tx[bi] + dx;
                    const y = w.ty[bi] + dy;
                    if (!m.passableTerrain(x, y, kind))
                        continue;
                    const t = y * m.w + x;
                    if (!ignoreResv && mv.resv[t] !== 0 && mv.resv[t] !== w.handle(i)) {
                        continue;
                    }
                    const d = F.d83(x - w.tx[i], y - w.ty[i]);
                    if (bd < 0 || d < bd || (d === bd && t < bt)) {
                        best = [x, y];
                        bd = d;
                        bt = t;
                    }
                }
            }
            if (best !== null)
                return best;
        }
        return null;
    }
    // 이동이 포기된 상태 — §13.3 이 24틱 만에 명령을 버렸다는 뜻이다.
    stuck(w, mv, i) {
        return mv.goal[i] < 0 && mv.path[i].length === 0 && w.prog[i] === 0;
    }
    // 채집기 한 기의 한 틱. sim 의 3단계에서 핸들 오름차순으로 부른다.
    harvestTick(w, i, m, mv) {
        const st = w.state[i];
        const p = w.owner[i];
        if (st === exports.H_SEEK) {
            const tile = this.nearestOre(m, w.tx[i], w.ty[i], C.MOVE_KIND[w.kind[i]]);
            if (tile < 0) {
                w.state[i] = exports.H_IDLE; // 캘 것이 없으면 멈춘다
                return;
            }
            this.oreTarget[i] = tile;
            mv.order(i, F.fmod(tile, m.w), F.floordiv(tile, m.w));
            w.state[i] = exports.H_TO_ORE;
            return;
        }
        if (st === exports.H_TO_ORE) {
            const t = this.oreTarget[i];
            if (t < 0 || this.ore[t] <= 0) {
                w.state[i] = exports.H_SEEK;
                return;
            }
            if (F.dinf(F.fmod(t, m.w) - w.tx[i], F.floordiv(t, m.w) - w.ty[i]) <= exports.TOUCH_R) {
                w.state[i] = exports.H_MINE;
            }
            else if (this.stuck(w, mv, i)) {
                mv.order(i, F.fmod(t, m.w), F.floordiv(t, m.w)); // 길막에 포기했으면
            }
            return;
        }
        if (st === exports.H_MINE) {
            const room = exports.LOAD_MAX - w.load[i];
            const wantAmt = exports.MINE_PER_TICK < room ? exports.MINE_PER_TICK : room;
            const got = this.mine(m, this.oreTarget[i], wantAmt);
            w.load[i] += got;
            if (w.load[i] >= exports.LOAD_MAX) {
                const h = this.nearestDepot(w, i);
                if (h === 0)
                    return; // 반납처가 없으면 실어 둔 채 기다린다
                w.target[i] = h;
                const bi = F.floordiv(h, 256);
                const d = this.dock(w, m, mv, i, bi);
                if (d !== null)
                    mv.order(i, d[0], d[1]);
                w.state[i] = exports.H_TO_BASE;
            }
            else if (got === 0) {
                w.state[i] = exports.H_SEEK; // 칸이 말랐다
            }
            return;
        }
        if (st === exports.H_TO_BASE) {
            const h = w.target[i];
            if (!w.valid(h)) {
                w.state[i] = w.load[i] < exports.LOAD_MAX ? exports.H_MINE : exports.H_TO_BASE;
                w.target[i] = this.nearestDepot(w, i);
                if (w.target[i] === 0)
                    w.state[i] = exports.H_SEEK;
                return;
            }
            const bi = F.floordiv(h, 256);
            if (this.touching(w, i, bi)) {
                w.state[i] = exports.H_UNLOAD;
                w.timer[i] = exports.UNLOAD_TICKS;
            }
            else if (this.stuck(w, mv, i)) {
                const d = this.dock(w, m, mv, i, bi);
                if (d !== null)
                    mv.order(i, d[0], d[1]);
            }
            return;
        }
        if (st === exports.H_UNLOAD) {
            w.timer[i] -= 1;
            if (w.timer[i] <= 0) {
                this.credits[p] += w.load[i];
                w.load[i] = 0;
                w.state[i] = exports.H_SEEK;
            }
        }
    }
}
exports.Econ = Econ;
  });
  __def('ai', function (exports, require, module, __dirname) {
"use strict";
// AI — 영향 지도·유령 기억·건물 배치·빌드 오더·정찰 (SPEC §17).
//
//    AI 는 **시뮬레이션의 일부**다. sim.step 안에서 돌고 명령을 자기 큐에 바로
//    넣는다. 네트워크 지연을 거치지 않아도 되는 이유는 모든 기계가 같은 AI 를
//    같은 틱에 돌리기 때문이다 — 결정론이 통신을 대신한다.
//
//    AI 는 안개를 존중한다(§17.3). 이 제약이 없으면 AI 가 전지적이 되고,
//    그건 게임이 아니다. 대신 마지막으로 본 위치를 30틱 기억해서 정찰에
//    값어치를 만든다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.RULES7 = exports.RULES = exports.Memory = exports.HARV_MIN = exports.ARMY_MIN = exports.FLEE_DEN = exports.FLEE_NUM = exports.SPREAD = exports.CHASE_R = exports.PLACE_R = exports.GHOST_TICKS = void 0;
exports.strength = strength;
exports.influence = influence;
exports.threat = threat;
exports.placeScore = placeScore;
exports.bestPlacement = bestPlacement;
exports.producer = producer;
exports.buildOrder = buildOrder;
exports.unitTick = unitTick;
exports.scoutTargets = scoutTargets;
const CB = require("./combat");
const C = require("./const");
const E = require("./econ");
const F = require("./fixed");
const SEL = require("./select");
const S = require("./spatial");
exports.GHOST_TICKS = 30; // §17.3 마지막으로 본 위치를 기억하는 틱
exports.PLACE_R = 12; // §17.4 건물 후보 반경 (타일)
exports.CHASE_R = 3; // §17.1 추격은 사거리 + 이만큼까지
exports.SPREAD = 3; // §17.2 확산 반복 횟수
exports.FLEE_NUM = 1; // §17.1 hp 가 1/4 아래면 도망
exports.FLEE_DEN = 4;
exports.ARMY_MIN = 6; // §17.5 이만큼 모이면 나간다
exports.HARV_MIN = 4;
// ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────
// 전력 = 기본 + 관통 + hp/4. 이 덱의 규칙이다.
function strength(w, i) {
    return C.BASIC[w.kind[i]] + C.PIERCE[w.kind[i]] + F.floordiv(w.hp[i], 4);
}
// 3회 확산. 가중치 4 + 8 = 12 로 나눈다.
// 정수 나눗셈의 내림 때문에 매 반복 조금씩 줄어드는데, 그 감쇠가 곧
// "멀수록 영향이 적다"이다. 별도의 감쇠 계수를 두지 않는 이유가 이것이다.
function spread(m, seed) {
    let cur = seed;
    for (let k = 0; k < exports.SPREAD; k += 1) {
        const nxt = new Array(m.w * m.h).fill(0);
        for (let y = 0; y < m.h; y += 1) {
            for (let x = 0; x < m.w; x += 1) {
                let acc = 4 * cur[y * m.w + x];
                for (let d = 0; d < 8; d += 1) {
                    const u = x + F.DX[d];
                    const v = y + F.DY[d];
                    if (u >= 0 && u < m.w && v >= 0 && v < m.h)
                        acc += cur[v * m.w + u];
                }
                nxt[y * m.w + x] = F.floordiv(acc, 12);
            }
        }
        cur = nxt;
    }
    return cur;
}
function seeds(w, fog, p, m, enemyOnly) {
    const seed = new Array(m.w * m.h).fill(0);
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0 || w.hp[i] <= 0)
            continue;
        const t = w.ty[i] * m.w + w.tx[i];
        if (w.owner[i] === p) {
            if (!enemyOnly)
                seed[t] += strength(w, i);
        }
        else if (fog.visible(p, t)) { // 보이는 적만 (§17.3)
            seed[t] += enemyOnly ? strength(w, i) : -strength(w, i);
        }
    }
    return seed;
}
function influence(w, fog, p, m) {
    return spread(m, seeds(w, fog, p, m, false));
}
function threat(w, fog, p, m) {
    return spread(m, seeds(w, fog, p, m, true));
}
// ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────
// 적을 마지막으로 본 자리를 30틱 기억한다. 건물 자리는 잊지 않는다 —
// 건물은 움직이지 않으므로 한 번 본 것을 잊는 편이 오히려 거짓말이다.
class Memory {
    constructor(w, h) {
        this.w = w;
        this.h = h;
        this.ttl = new Array(w * h).fill(0);
        this.baseTile = -1;
    }
    update(world, fog, p) {
        for (let i = 0; i < this.ttl.length; i += 1) {
            if (this.ttl[i] > 0)
                this.ttl[i] -= 1;
        }
        for (let j = 1; j < C.MAX_ENT; j += 1) {
            if (world.alive[j] === 0 || world.owner[j] === p || world.hp[j] <= 0) {
                continue;
            }
            const t = world.ty[j] * this.w + world.tx[j];
            if (!fog.visible(p, t))
                continue;
            this.ttl[t] = exports.GHOST_TICKS;
            if (C.IS_BUILDING[world.kind[j]] !== 0) {
                if (this.baseTile < 0 || t < this.baseTile)
                    this.baseTile = t;
            }
        }
    }
    ghosts() {
        const out = [];
        for (let i = 0; i < this.ttl.length; i += 1) {
            if (this.ttl[i] > 0)
                out.push(i);
        }
        return out;
    }
    enemyBaseKnown() {
        return this.baseTile >= 0;
    }
    enemyBase() {
        if (this.baseTile < 0)
            return null;
        return [F.fmod(this.baseTile, this.w), F.floordiv(this.baseTile, this.w)];
    }
}
exports.Memory = Memory;
// ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────
// 점수 — fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다.
function placeScore(m, fire, thr, kind, x, y, cx, cy, ore) {
    const i = y * m.w + x;
    let sc = 100 - 3 * F.d83(x - cx, y - cy) + 2 * fire[i] - thr[i];
    if (kind === C.REF && ore >= 0) {
        sc += 40 - 8 * F.d83(F.fmod(ore, m.w) - x, F.floordiv(ore, m.w) - y);
    }
    return sc;
}
// 기지 중심 반경 12 안에서 점수 최대, 동점이면 타일 번호 최소.
function bestPlacement(w, m, mv, ec, fire, thr, p, kind, centre) {
    const cx = centre[0];
    const cy = centre[1];
    const ore = kind === C.REF ? ec.nearestOre(m, cx, cy) : -1;
    let best = null;
    let bs = 0;
    let bi = 0;
    let has = false;
    for (let y = cy - exports.PLACE_R; y <= cy + exports.PLACE_R; y += 1) {
        for (let x = cx - exports.PLACE_R; x <= cx + exports.PLACE_R; x += 1) {
            if (!m.inMap(x, y))
                continue;
            if (F.dinf(x - cx, y - cy) > exports.PLACE_R)
                continue;
            if (!ec.placeable(w, m, mv, kind, x, y, p))
                continue;
            const i = y * m.w + x;
            const sc = placeScore(m, fire, thr, kind, x, y, cx, cy, ore);
            if (!has || sc > bs || (sc === bs && i < bi)) {
                best = [x, y];
                bs = sc;
                bi = i;
                has = true;
            }
        }
    }
    return best;
}
// ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
function countKind(w, p, kind) {
    let n = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 1 && w.owner[i] === p && w.kind[i] === kind
            && w.hp[i] > 0)
            n += 1;
    }
    return n;
}
function armyCount(w, p) {
    let n = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 1 && w.owner[i] === p && w.hp[i] > 0
            && C.IS_BUILDING[w.kind[i]] === 0 && C.BASIC[w.kind[i]] > 0)
            n += 1;
    }
    return n;
}
// 그 유닛을 뽑을 수 있는 내 건물 중 인덱스가 가장 작은 것. 없으면 -1.
function producer(w, ec, p, kind) {
    if (C.PREREQ[kind].length === 0)
        return -1;
    const need = C.PREREQ[kind][0];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 1 && w.owner[i] === p && w.kind[i] === need
            && w.hp[i] > 0 && ec.queue[i].length < E.QUEUE_MAX)
            return i;
    }
    return -1;
}
function canTrain(w, ec, p, kind) {
    const bi = producer(w, ec, p, kind);
    if (bi < 0 || !ec.canBuild(w, p, kind))
        return -1;
    if (ec.credits[p] < C.COST[kind])
        return -1;
    if (ec.supplyUsed[p] + C.POP[kind] > ec.supplyCap[p])
        return -1;
    return bi;
}
function canBuildRule(w, ec, p, kind, credits) {
    if (ec.credits[p] < credits || !ec.canBuild(w, p, kind))
        return false;
    return true;
}
const ruleHarvester = (w, ec, _mem, p) => {
    if (countKind(w, p, C.HARV) >= exports.HARV_MIN)
        return null;
    const bi = canTrain(w, ec, p, C.HARV);
    return bi >= 0 ? ['TRAIN', C.HARV, bi] : null;
};
const ruleRefinery = (w, ec, _mem, p) => {
    if (countKind(w, p, C.REF) > 0)
        return null;
    return canBuildRule(w, ec, p, C.REF, 300) ? ['BUILD', C.REF] : null;
};
const ruleBarracks = (w, ec, _mem, p) => {
    if (countKind(w, p, C.BARR) > 0)
        return null;
    return canBuildRule(w, ec, p, C.BARR, 400) ? ['BUILD', C.BARR] : null;
};
const ruleInfantry = (w, ec, _mem, p) => {
    if (armyCount(w, p) >= exports.ARMY_MIN)
        return null;
    const bi = canTrain(w, ec, p, C.INF);
    return bi >= 0 ? ['TRAIN', C.INF, bi] : null;
};
const ruleAttack = (w, _ec, mem, p) => {
    if (armyCount(w, p) < exports.ARMY_MIN || !mem.enemyBaseKnown())
        return null;
    const b = mem.enemyBase();
    return ['ATTACK', b[0], b[1]];
};
const ruleDefend = () => ['DEFEND'];
// 일곱째 줄 — 실험용이다(§17.5). 여섯 줄짜리 AI 는 인구 10 에서 멈춘다.
const rulePower = (w, ec, _mem, p) => {
    if (ec.supplyCap[p] - ec.supplyUsed[p] >= 2)
        return null;
    if (ec.supplyCap[p] >= E.SUPPLY_MAX)
        return null;
    return canBuildRule(w, ec, p, C.POW, 200) ? ['BUILD', C.POW] : null;
};
// 여섯 줄이 AI 전부다. 위에서부터 훑어 처음으로 조건을 만족하는 하나를 실행한다.
exports.RULES = [ruleHarvester, ruleRefinery, ruleBarracks,
    ruleInfantry, ruleAttack, ruleDefend];
// 발전소 한 줄을 더한 판. 18부가 두 실행을 나란히 놓는다.
exports.RULES7 = [ruleHarvester, ruleRefinery, ruleBarracks,
    rulePower, ruleInfantry, ruleAttack, ruleDefend];
function buildOrder(w, ec, mem, p, rules) {
    for (const rule of (rules === undefined || rules === null ? exports.RULES : rules)) {
        const act = rule(w, ec, mem, p);
        if (act !== null)
            return act;
    }
    return ['DEFEND'];
}
// ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────
// 한 유닛의 상태 전이. 평가 순서가 곧 우선순위다.
// 세 번째 인자(맵)는 쓰이지 않지만 파이썬 원본과 같은 자리에 남겨 둔다 —
// 세 언어의 호출부가 같은 모양이어야 sim 의 2단계를 눈으로 대조할 수 있다.
function unitTick(w, i, _m, mv, orders) {
    const kind = w.kind[i];
    if (C.IS_BUILDING[kind] !== 0)
        return;
    if (kind === C.HARV) {
        if (w.hp[i] * exports.FLEE_DEN < C.HP[kind] * exports.FLEE_NUM) { // hp 25 % 아래
            let h = 0;
            for (let j = 1; j < C.MAX_ENT; j += 1) {
                if (w.alive[j] === 1 && w.owner[j] === w.owner[i]
                    && E.DEPOT.indexOf(w.kind[j]) >= 0 && w.hp[j] > 0) {
                    h = j;
                    break;
                }
            }
            w.state[i] = C.ST_FLEE;
            if (h !== 0)
                mv.order(i, w.tx[h], w.ty[h]);
            return;
        }
        if (w.state[i] === C.ST_FLEE)
            w.state[i] = C.ST_SEEK; // 회복하면 하던 일로
        return;
    }
    const [tgt, approach] = CB.pickTarget(w, i, 0, w.state[i] === C.ST_MOVE);
    if (tgt !== 0 && !approach) {
        w.target[i] = tgt;
        w.state[i] = C.ST_ATTACK;
        return;
    }
    if (w.state[i] === C.ST_ATTACK || w.state[i] === C.ST_MOVE) {
        const cur = w.target[i];
        if (w.valid(cur)) {
            const j = S.index(cur);
            const d = F.dinf(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i]);
            if (d <= C.RANGE[kind] + exports.CHASE_R) {
                w.state[i] = C.ST_MOVE; // 추격
                mv.order(i, w.tx[j], w.ty[j]);
                orders.push(i, [SEL.ATTACK_MOVE, w.tx[j], w.ty[j], cur], false);
                return;
            }
        }
        w.target[i] = 0;
        w.state[i] = C.ST_IDLE;
        return;
    }
    if (tgt !== 0) {
        w.target[i] = tgt;
        w.state[i] = C.ST_MOVE;
        return;
    }
    if (mv.path[i].length === 0 && mv.goal[i] < 0)
        w.state[i] = C.ST_IDLE;
}
// ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────
// 미탐험 클러스터의 중심, **클러스터 번호 오름차순**.
// 정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다 —
// 목록이 결정론적이어야 그 이어받기가 세 언어에서 같다.
function scoutTargets(m, fog, p) {
    const out = [];
    const cw = Math.floor((m.w + C.CLUSTER - 1) / C.CLUSTER);
    const chh = Math.floor((m.h + C.CLUSTER - 1) / C.CLUSTER);
    for (let cy = 0; cy < chh; cy += 1) {
        for (let cx = 0; cx < cw; cx += 1) {
            let seen = false;
            for (let y = cy * C.CLUSTER; y < Math.min(m.h, (cy + 1) * C.CLUSTER); y += 1) {
                for (let x = cx * C.CLUSTER; x < Math.min(m.w, (cx + 1) * C.CLUSTER); x += 1) {
                    if (fog.explored[p][y * m.w + x] !== 0) {
                        seen = true;
                        break;
                    }
                }
                if (seen)
                    break;
            }
            if (!seen) {
                out.push([cx * C.CLUSTER + Math.floor(C.CLUSTER / 2),
                    cy * C.CLUSTER + Math.floor(C.CLUSTER / 2)]);
            }
        }
    }
    return out;
}
  });
  __def('sim', function (exports, require, module, __dirname) {
"use strict";
// 시뮬레이션 — 유일한 진입점 (SPEC §18).
//
//    **상태를 바꾸는 함수는 `step` 하나뿐이다.** 렌더는 읽기만 하고, UI 는 명령을
//    만들 뿐이며, AI 조차 같은 자료형의 명령으로 말한다. 이 규율이 19부(락스텝)와
//    20부(리플레이)의 전제 전부다.
//
//    틱의 아홉 단계 순서는 명세다. 바꾸면 골든이 통째로 틀어진다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sim = exports.Script = exports.CMD = exports.AI_PERIOD = exports.CMP_EQ = exports.CMP_LE = exports.CMP_GE = exports.AC_REVEAL = exports.AC_LOSE = exports.AC_WIN = exports.AC_MESSAGE = exports.AC_SPAWN = exports.CT_CREDITS_GE = exports.CT_AREA_ENTERED = exports.CT_BUILDING_DESTROYED = exports.CT_UNIT_COUNT = exports.CT_TICK_GE = exports.EV_MESSAGE = exports.EV_WIN = exports.EV_ORDER = exports.EV_UNLOAD = exports.EV_MINE = exports.EV_BUILD_DONE = exports.EV_HIT = exports.EV_DIE = exports.EV_SPAWN = void 0;
exports.parseScript = parseScript;
const AI = require("./ai");
const CB = require("./combat");
const C = require("./const");
const E = require("./econ");
const F = require("./fixed");
const FL = require("./flow");
const fog_1 = require("./fog");
const M = require("./move");
const rng_1 = require("./rng");
const SEL = require("./select");
const S = require("./spatial");
const T = require("./tmap");
// ── §18.3 이벤트 종류 ───────────────────────────────────────────────────────
exports.EV_SPAWN = 0;
exports.EV_DIE = 1;
exports.EV_HIT = 2;
exports.EV_BUILD_DONE = 3;
exports.EV_MINE = 4;
exports.EV_UNLOAD = 5;
exports.EV_ORDER = 6;
exports.EV_WIN = 7;
exports.EV_MESSAGE = 8;
// ── §18.5 트리거 ────────────────────────────────────────────────────────────
exports.CT_TICK_GE = 0;
exports.CT_UNIT_COUNT = 1;
exports.CT_BUILDING_DESTROYED = 2;
exports.CT_AREA_ENTERED = 3;
exports.CT_CREDITS_GE = 4;
exports.AC_SPAWN = 0;
exports.AC_MESSAGE = 1;
exports.AC_WIN = 2;
exports.AC_LOSE = 3;
exports.AC_REVEAL = 4;
exports.CMP_GE = 0;
exports.CMP_LE = 1;
exports.CMP_EQ = 2;
exports.AI_PERIOD = 15; // §17.5 빌드 오더 평가 주기
exports.CMD = {
    MOVE: SEL.MOVE, AMOVE: SEL.ATTACK_MOVE, ATTACK: SEL.ATTACK,
    HARVEST: SEL.HARVEST, STOP: SEL.STOP, HOLD: SEL.HOLD,
    BUILD: SEL.BUILD, TRAIN: SEL.TRAIN,
};
// 트리거 인자는 길이가 들쭉날쭉하다 — 없는 칸은 0 으로 읽는다.
function at(t, k) {
    return k < t.length ? t[k] : 0;
}
class Script {
    constructor() {
        this.ticks = 0;
        this.players = 0;
        this.lines = [];
    }
}
exports.Script = Script;
// §18.6 시나리오 스크립트. `#` 로 시작하는 줄은 주석이다.
function parseScript(text) {
    const sc = new Script();
    for (const raw of text.split('\n')) {
        const ln = raw.trim();
        if (ln === '' || ln.indexOf('#') === 0 || ln.indexOf('RTSS') === 0)
            continue;
        if (ln.indexOf('ticks ') === 0) {
            sc.ticks = parseInt(ln.split(/\s+/)[1], 10);
            continue;
        }
        if (ln.indexOf('players ') === 0) {
            sc.players = parseInt(ln.split(/\s+/)[1], 10);
            continue;
        }
        const p = ln.split(/\s+/);
        sc.lines.push([parseInt(p[0], 10), parseInt(p[1], 10), p[2], p[3],
            parseInt(p[4], 10), parseInt(p[5], 10), parseInt(p[6], 10)]);
    }
    return sc;
}
// FNV-1a 를 흘려 넣는다 — 바이트열을 통째로 만들지 않는 편이 메모리와 시간이
// 덜 든다 (SPEC §18.4).
class Hash {
    constructor() {
        this.h = F.FNV_OFFSET;
    }
    // Math.trunc 를 한 번 거치는 이유는 §19.4 의 주입 버그 때문이다. 그때만
    // prog·px·py 가 실수가 되고, 해시는 그 잘린 값을 그대로 본다.
    b1(v) {
        this.h = F.fnv1aStep(this.h, F.fmod(Math.trunc(v), 256));
    }
    b2(v) {
        const x = F.fmod(Math.trunc(v), 65536); // 음수는 2의 보수로 접는다
        this.b1(F.floordiv(x, 256));
        this.b1(F.fmod(x, 256));
    }
    b4(v) {
        const x = F.fmod(Math.trunc(v), 4294967296);
        this.b2(F.floordiv(x, 65536));
        this.b2(F.fmod(x, 65536));
    }
}
class Sim {
    constructor(m, seed, players = 2, floatBug = false) {
        this.m = m;
        this.players = players;
        this.w = new S.World(m.w, m.h);
        this.fog = new fog_1.Fog(m.w, m.h);
        this.ec = new E.Econ(m);
        this.mv = new M.Movement(this.w, m, floatBug);
        this.pj = new CB.Projectiles(m.w);
        this.rng = new rng_1.LCG(seed);
        this.orders = new SEL.Orders();
        this.mem = [];
        for (let p = 0; p < C.MAX_PLAYER; p += 1) {
            this.mem.push(new AI.Memory(m.w, m.h));
        }
        this.aiEnabled = new Array(C.MAX_PLAYER).fill(false);
        this.aiRules = null; // null 이면 §17.5 의 여섯 줄
        this.tick = 0;
        this.events = [];
        this.triggers = [];
        this.fired = [];
        this.winner = -1;
        this.loser = [];
        this.lastHit = new Array(C.MAX_ENT).fill(0);
        this.lastSpawn = new Array(C.MAX_PLAYER).fill(0);
        this.sightAt = new Array(C.MAX_ENT).fill(-1); // 안개가 아는 위치
        this.hadBuilding = new Array(C.MAX_PLAYER).fill(false);
        this.mapHashValue = 0;
        this.mapHashVersion = -1;
        this.fireField = null;
        this.fireVersion = -1;
    }
    // ── 생성·소멸 ────────────────────────────────────────────────────────────
    spawn(p, kind, x, y) {
        const h = this.w.spawn(p, kind, x, y);
        if (h === 0)
            return 0;
        const i = S.index(h);
        this.w.hp[i] = C.HP[kind]; // 태어나는 것은 정격 hp 로
        this.mv.claim(i);
        this.fog.addSight(p, x, y, C.SIGHT[kind]);
        this.sightAt[i] = y * this.m.w + x;
        if (C.IS_BUILDING[kind] !== 0)
            this.hadBuilding[p] = true;
        else
            this.lastSpawn[p] = h;
        if (kind === C.HARV)
            this.w.state[i] = C.ST_SEEK;
        return h;
    }
    // §25.4 시작 조건. 골든 시나리오는 스크립트가 몰므로 AI 를 끈다 —
    // 한 지갑을 둘이 쓰면 서로의 건설을 굶긴다(§18.6).
    setupStart(ai = true) {
        const n = Math.min(this.players, this.m.starts.length);
        for (let p = 0; p < n; p += 1) {
            const sx = this.m.starts[p][0];
            const sy = this.m.starts[p][1];
            this.spawn(p, C.HQ, sx - 1, sy - 1);
            for (let k = 0; k < C.START_HARV; k += 1) {
                let x = sx + 2;
                let y = sy + 1 + k;
                if (!this.m.passableTerrain(x, y, C.MOVE_KIND[C.HARV])) {
                    x = sx;
                    y = sy + 2 + k;
                }
                this.spawn(p, C.HARV, x, y);
            }
            this.ec.credits[p] = C.START_CREDITS;
            this.aiEnabled[p] = ai;
        }
        this.ec.recountSupply(this.w);
    }
    addTrigger(cond, act, once) {
        this.triggers.push([cond, act, once]);
        this.fired.push(false);
    }
    // ── SPEC §18.2 틱의 아홉 단계 ────────────────────────────────────────────
    step(orders) {
        this.events = [];
        this.tick += 1;
        this.checkSorted(orders);
        for (const o of orders)
            this.applyOrder(o); // 1. 명령 적용
        this.phaseAi(); // 2. AI
        this.phaseEcon(); // 3. 생산·경제
        this.mv.step(); // 4. 이동
        this.phaseCombat(); // 5. 전투
        this.phaseDeath(); // 6. 사망
        this.phaseSight(); // 7. 시야
        this.phaseTriggers(); // 8. 트리거·승패
        return this.stateHash(); // 9. 상태 해시
    }
    checkSorted(orders) {
        for (let k = 1; k < orders.length; k += 1) {
            if (cmpOrder(orders[k - 1], orders[k]) > 0) {
                throw new Error('명령 목록이 정렬되어 있지 않다 (SPEC §18.1)');
            }
        }
    }
    // ── 1단계 ────────────────────────────────────────────────────────────────
    applyOrder(o) {
        const p = o[0];
        const issuer = o[1];
        const kind = o[2];
        const a = o[3];
        const b = o[4];
        const c = o[5];
        if (!this.w.valid(issuer))
            return;
        const i = S.index(issuer);
        const w = this.w;
        if (w.owner[i] !== p)
            return; // 남의 유닛에 내린 명령은 무시
        if (kind === SEL.MOVE || kind === SEL.ATTACK_MOVE) {
            if (this.mv.order(i, a, b)) {
                w.state[i] = C.ST_MOVE;
                w.target[i] = 0;
            }
        }
        else if (kind === SEL.ATTACK) {
            w.target[i] = c;
            w.state[i] = C.ST_ATTACK;
            if (w.valid(c)) {
                const j = S.index(c);
                this.mv.order(i, w.tx[j], w.ty[j]);
            }
        }
        else if (kind === SEL.HARVEST) {
            if (w.kind[i] === C.HARV)
                w.state[i] = C.ST_SEEK;
        }
        else if (kind === SEL.STOP) {
            this.mv.stop(i);
            this.orders.clear(i);
            w.state[i] = C.ST_IDLE;
        }
        else if (kind === SEL.HOLD) {
            this.mv.stop(i);
            w.state[i] = C.ST_IDLE;
        }
        else if (kind === SEL.TRAIN) {
            this.ec.enqueue(w, i, a);
        }
        else if (kind === SEL.BUILD) {
            this.doBuild(p, a, b, c);
        }
        this.events.push([exports.EV_ORDER, p, issuer, kind]);
    }
    // §16.4 — 통과하면 그 자리에 즉시 엔티티가 생기고 짓기 시작한다.
    doBuild(p, kind, x, y) {
        if (C.IS_BUILDING[kind] === 0)
            return false;
        if (!this.ec.canBuild(this.w, p, kind))
            return false;
        if (this.ec.credits[p] < C.COST[kind])
            return false;
        if (!this.ec.placeable(this.w, this.m, this.mv, kind, x, y, p)) {
            this.shove(p, kind, x, y); // §16.5 — 내 유닛이면 비키게 한다
            return false;
        }
        this.ec.credits[p] -= C.COST[kind]; // 선불
        const h = this.spawn(p, kind, x, y);
        if (h === 0) {
            this.ec.credits[p] += C.COST[kind];
            return false;
        }
        const i = S.index(h);
        this.w.state[i] = C.ST_BUILD;
        this.w.hp[i] = 1;
        this.w.timer[i] = C.BUILD_TICKS[kind];
        return true;
    }
    // 발자국을 막은 내 유닛들에게 바깥으로 한 걸음 명령을 준다 (§16.5).
    // 밀면서 동시에 짓지는 않는다 — 아직 그 칸에 선 유닛 위에 건물을
    // 얹으면 불변식 R 이 깨진다. 다음 재시도에서 자리가 빈다.
    shove(p, kind, x, y) {
        const w = this.w;
        const m = this.m;
        const f = C.FOOT[kind];
        const cx = x + Math.floor(f / 2);
        const cy = y + Math.floor(f / 2);
        for (let dy = 0; dy < f; dy += 1) {
            for (let dx = 0; dx < f; dx += 1) {
                const u = x + dx;
                const v = y + dy;
                if (!m.inMap(u, v))
                    continue;
                const h = this.mv.resv[v * m.w + u];
                if (!w.valid(h))
                    continue;
                const j = S.index(h);
                if (w.owner[j] !== p || C.IS_BUILDING[w.kind[j]] !== 0)
                    continue;
                const out = F.atan8(w.tx[j] - cx, w.ty[j] - cy);
                const pd = M.pushDir(this.mv, j, F.fmod(out + 4, 8));
                if (pd !== M.STOP_DIR) {
                    const t = (w.ty[j] + F.DY[pd]) * m.w + w.tx[j] + F.DX[pd];
                    this.mv.path[j] = [t];
                    this.mv.goal[j] = t;
                }
            }
        }
    }
    // ── 2단계 AI ─────────────────────────────────────────────────────────────
    phaseAi() {
        for (let p = 0; p < this.players; p += 1) {
            if (!this.aiEnabled[p])
                continue;
            this.mem[p].update(this.w, this.fog, p);
            if (F.fmod(this.tick, exports.AI_PERIOD) === 0)
                this.aiDecide(p);
            for (let i = 1; i < C.MAX_ENT; i += 1) {
                if (this.w.alive[i] === 1 && this.w.owner[i] === p
                    && C.IS_BUILDING[this.w.kind[i]] === 0) {
                    AI.unitTick(this.w, i, this.m, this.mv, this.orders);
                }
            }
        }
    }
    brushfire() {
        if (this.fireVersion !== this.m.version) {
            this.fireField = FL.brushfire(this.m, 0);
            this.fireVersion = this.m.version;
        }
        return this.fireField;
    }
    aiDecide(p) {
        const act = AI.buildOrder(this.w, this.ec, this.mem[p], p, this.aiRules);
        if (act[0] === 'TRAIN') {
            this.ec.enqueue(this.w, act[2], act[1]);
        }
        else if (act[0] === 'BUILD') {
            const centre = this.baseOf(p);
            if (centre === null)
                return;
            const thr = AI.threat(this.w, this.fog, p, this.m);
            const spot = AI.bestPlacement(this.w, this.m, this.mv, this.ec, this.brushfire(), thr, p, act[1], centre);
            if (spot !== null)
                this.doBuild(p, act[1], spot[0], spot[1]);
        }
        else if (act[0] === 'ATTACK') {
            for (const i of this.army(p)) {
                this.mv.order(i, act[1], act[2]);
                this.w.state[i] = C.ST_MOVE;
            }
        }
        else { // DEFEND (+ §17.6 정찰)
            const centre = this.baseOf(p);
            if (centre === null)
                return;
            const army = this.army(p);
            const spots = AI.scoutTargets(this.m, this.fog, p);
            for (let k = 0; k < army.length; k += 1) {
                const i = army[k];
                if (this.w.state[i] !== C.ST_IDLE || this.mv.path[i].length > 0)
                    continue;
                if (k === 0 && spots.length > 0) {
                    // 첫 유닛 하나만 정찰. 이것이 없으면 적 기지를 영영 모르고
                    // 빌드 오더의 다섯째 줄(전군 공격)이 발화하지 않는다.
                    this.mv.order(i, spots[0][0], spots[0][1]);
                    this.w.state[i] = C.ST_MOVE;
                }
                else {
                    this.mv.order(i, centre[0], centre[1]);
                }
            }
        }
    }
    baseOf(p) {
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (this.w.alive[i] === 1 && this.w.owner[i] === p
                && C.IS_BUILDING[this.w.kind[i]] === 1) {
                return [this.w.tx[i], this.w.ty[i]];
            }
        }
        return null;
    }
    army(p) {
        const out = [];
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (this.w.alive[i] === 1 && this.w.owner[i] === p
                && C.IS_BUILDING[this.w.kind[i]] === 0
                && C.BASIC[this.w.kind[i]] > 0)
                out.push(i);
        }
        return out;
    }
    // ── 3단계 생산·경제 ──────────────────────────────────────────────────────
    phaseEcon() {
        const w = this.w;
        for (let i = 1; i < C.MAX_ENT; i += 1) { // 건설 진행
            if (w.alive[i] === 1 && C.IS_BUILDING[w.kind[i]] !== 0
                && w.state[i] === C.ST_BUILD) {
                const total = C.BUILD_TICKS[w.kind[i]];
                let done = total - w.timer[i];
                if (done < 0)
                    done = 0;
                w.hp[i] = 1 + F.floordiv(done * (C.HP[w.kind[i]] - 1), total);
                w.timer[i] -= 1;
                if (w.timer[i] <= 0) {
                    w.timer[i] = 0;
                    w.hp[i] = C.HP[w.kind[i]];
                    w.state[i] = C.ST_IDLE;
                    this.events.push([exports.EV_BUILD_DONE, w.owner[i], w.handle(i), w.kind[i]]);
                }
            }
        }
        for (const [bi, kind] of this.ec.stepProduction(w)) {
            const spot = this.freeNear(bi, kind);
            if (spot === null)
                continue;
            const h = this.spawn(w.owner[bi], kind, spot[0], spot[1]);
            if (h !== 0)
                this.events.push([exports.EV_SPAWN, w.owner[bi], h, kind]);
        }
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 1 && w.kind[i] === C.HARV) {
                const before = this.ec.credits[w.owner[i]];
                this.ec.harvestTick(w, i, this.m, this.mv);
                if (this.ec.credits[w.owner[i]] > before) {
                    this.events.push([exports.EV_UNLOAD, w.owner[i], w.handle(i),
                        this.ec.credits[w.owner[i]] - before]);
                }
            }
        }
        this.ec.recountSupply(w);
    }
    // 건물 둘레에서 빈 칸 하나. y 오름차순, 같은 y 안에서 x 오름차순.
    freeNear(bi, kind) {
        const w = this.w;
        const m = this.m;
        const mk = C.MOVE_KIND[kind];
        const f = C.FOOT[w.kind[bi]];
        for (let r = 1; r < 4; r += 1) {
            for (let y = w.ty[bi] - r; y < w.ty[bi] + f + r; y += 1) {
                for (let x = w.tx[bi] - r; x < w.tx[bi] + f + r; x += 1) {
                    if (!m.passableTerrain(x, y, mk))
                        continue;
                    if (this.mv.resv[y * m.w + x] !== 0)
                        continue;
                    return [x, y];
                }
            }
        }
        return null;
    }
    // ── 5단계 전투 ───────────────────────────────────────────────────────────
    phaseCombat() {
        const w = this.w;
        const m = this.m;
        const pending = [];
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 0 || w.hp[i] <= 0)
                continue;
            const kind = w.kind[i];
            if (C.BASIC[kind] === 0)
                continue;
            if (w.cool[i] > 0) {
                w.cool[i] -= 1;
                continue;
            }
            const [tgt, approach] = CB.pickTarget(w, i, this.lastHit[i], w.state[i] === C.ST_MOVE);
            if (tgt === 0 || approach)
                continue;
            const j = S.index(tgt);
            w.target[i] = tgt;
            const dmg = CB.rollDamage(this.rng, C.BASIC[kind], C.PIERCE[kind], C.ARMOUR[w.kind[j]]);
            w.cool[i] = C.RELOAD[kind];
            if (kind === C.ARCHER || kind === C.MORTAR) {
                const pk = kind === C.MORTAR ? CB.ARC : CB.STRAIGHT;
                const sp = kind === C.MORTAR ? 0 : CB.ARROW_SPEED;
                if (!this.pj.launch(pk, w.px[i], w.py[i], w.px[j], w.py[j], sp, tgt, dmg)) {
                    pending.push([tgt, w.handle(i), dmg]);
                }
            }
            else {
                pending.push([tgt, w.handle(i), dmg]);
            }
        }
        for (const [tgt, dmg, dest, , pkind] of this.pj.step()) {
            if (pkind === CB.ARC) { // 포물선만 스플래시 (아군도 맞는다)
                for (const [hh, dd] of CB.splashHits(w, F.fmod(dest, m.w), F.floordiv(dest, m.w), dmg)) {
                    pending.push([hh, 0, dd]);
                }
            }
            else if (w.valid(tgt)) {
                pending.push([tgt, 0, dmg]);
            }
        }
        pending.sort(cmpTriple);
        for (const [tgt, src, dmg] of pending) { // **피해는 여기서 한꺼번에**
            if (!w.valid(tgt))
                continue;
            const j = S.index(tgt);
            w.hp[j] -= dmg;
            if (src !== 0)
                this.lastHit[j] = src;
            this.events.push([exports.EV_HIT, tgt, src, dmg]);
        }
    }
    // ── 6단계 사망 ───────────────────────────────────────────────────────────
    phaseDeath() {
        const w = this.w;
        const m = this.m;
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 0 || w.hp[i] > 0)
                continue;
            this.events.push([exports.EV_DIE, w.owner[i], w.handle(i), w.kind[i]]);
            const t = this.sightAt[i]; // 안개가 아는 위치에서 반납한다
            if (t >= 0) {
                this.fog.removeSight(w.owner[i], F.fmod(t, m.w), F.floordiv(t, m.w), C.SIGHT[w.kind[i]]);
                this.sightAt[i] = -1;
            }
            const f = C.FOOT[w.kind[i]];
            const building = C.IS_BUILDING[w.kind[i]] === 1;
            const cells = [];
            for (let dy = 0; dy < f; dy += 1) {
                for (let dx = 0; dx < f; dx += 1)
                    cells.push([w.tx[i] + dx, w.ty[i] + dy]);
            }
            this.mv.unclaim(i);
            if (building) {
                for (const [x, y] of cells) { // 잔해를 남긴다
                    if (m.inMap(x, y))
                        m.setTerrain(x, y, T.RUBBLE);
                }
            }
            w.kill(w.handle(i));
        }
    }
    // ── 7단계 시야 ───────────────────────────────────────────────────────────
    phaseSight() {
        const w = this.w;
        const m = this.m;
        for (const [i, , nw] of this.mv.crossed) {
            if (w.alive[i] === 0)
                continue; // 6단계에서 이미 반납했다
            const r = C.SIGHT[w.kind[i]];
            const src = this.sightAt[i];
            if (src >= 0) {
                this.fog.removeSight(w.owner[i], F.fmod(src, m.w), F.floordiv(src, m.w), r);
            }
            this.fog.addSight(w.owner[i], F.fmod(nw, m.w), F.floordiv(nw, m.w), r);
            this.sightAt[i] = nw;
        }
    }
    // ── 8단계 트리거·승패 ────────────────────────────────────────────────────
    phaseTriggers() {
        for (let k = 0; k < this.triggers.length; k += 1) {
            const [cond, act, once] = this.triggers[k];
            if (once && this.fired[k])
                continue;
            if (this.cond(cond)) {
                this.act(act);
                if (once)
                    this.fired[k] = true;
            }
        }
        this.checkVictory();
    }
    cond(t) {
        const w = this.w;
        const kind = t[0];
        if (kind === exports.CT_TICK_GE)
            return this.tick >= at(t, 1);
        if (kind === exports.CT_UNIT_COUNT) {
            const p = at(t, 1);
            const uk = at(t, 2);
            const cmp = at(t, 3);
            const n = at(t, 4);
            let cnt = 0;
            for (let i = 1; i < C.MAX_ENT; i += 1) {
                if (w.alive[i] !== 0 && w.owner[i] === p && w.kind[i] === uk)
                    cnt += 1;
            }
            if (cmp === exports.CMP_GE)
                return cnt >= n;
            if (cmp === exports.CMP_LE)
                return cnt <= n;
            return cnt === n;
        }
        if (kind === exports.CT_BUILDING_DESTROYED)
            return !this.hasBuilding(at(t, 1));
        if (kind === exports.CT_AREA_ENTERED) {
            const p = at(t, 1);
            const x = at(t, 2);
            const y = at(t, 3);
            const r = at(t, 4);
            for (let i = 1; i < C.MAX_ENT; i += 1) {
                if (w.alive[i] !== 0 && w.owner[i] === p
                    && C.IS_BUILDING[w.kind[i]] === 0
                    && F.dinf(w.tx[i] - x, w.ty[i] - y) <= r)
                    return true;
            }
            return false;
        }
        if (kind === exports.CT_CREDITS_GE)
            return this.ec.credits[at(t, 1)] >= at(t, 2);
        return false;
    }
    act(t) {
        const kind = t[0];
        if (kind === exports.AC_SPAWN) {
            const h = this.spawn(at(t, 1), at(t, 2), at(t, 3), at(t, 4));
            if (h !== 0)
                this.events.push([exports.EV_SPAWN, at(t, 1), h, at(t, 2)]);
        }
        else if (kind === exports.AC_MESSAGE) {
            this.events.push([exports.EV_MESSAGE, at(t, 1)]);
        }
        else if (kind === exports.AC_WIN) {
            this.declare(at(t, 1));
        }
        else if (kind === exports.AC_LOSE) {
            const p = at(t, 1);
            if (this.loser.indexOf(p) < 0)
                this.loser.push(p);
        }
        else if (kind === exports.AC_REVEAL) {
            const x = at(t, 1);
            const y = at(t, 2);
            const r = at(t, 3);
            this.fog.addSight(0, x, y, r);
            this.fog.removeSight(0, x, y, r); // 탐험만 남기고 시야는 돌려준다
        }
    }
    hasBuilding(p) {
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (this.w.alive[i] === 1 && this.w.owner[i] === p
                && C.IS_BUILDING[this.w.kind[i]] === 1)
                return true;
        }
        return false;
    }
    declare(p) {
        if (this.winner < 0) {
            this.winner = p;
            this.events.push([exports.EV_WIN, p]);
        }
    }
    // 건물이 전부 파괴되면 패배. 남은 플레이어가 하나면 승리.
    checkVictory() {
        if (this.winner >= 0)
            return;
        const alive = [];
        for (let p = 0; p < this.players; p += 1) {
            if (this.hasBuilding(p))
                alive.push(p);
            else if (this.hadBuilding[p] && this.loser.indexOf(p) < 0) {
                this.loser.push(p);
            }
        }
        if (alive.length === 1 && this.loser.length > 0)
            this.declare(alive[0]);
    }
    // ── SPEC §18.4 상태 해시 ─────────────────────────────────────────────────
    // 지형이 바뀔 때만 다시 계산한다. 캐시지만 상태의 순수 함수다.
    mapHash() {
        if (this.mapHashVersion !== this.m.version) {
            const hh = new Hash();
            for (const v of this.m.terrain)
                hh.b1(v);
            for (const v of this.m.pass_)
                hh.b1(v);
            this.mapHashValue = hh.h;
            this.mapHashVersion = this.m.version;
        }
        return this.mapHashValue;
    }
    stateHash() {
        const w = this.w;
        const hh = new Hash();
        hh.b4(this.tick);
        hh.b4(this.rng.s);
        for (let p = 0; p < C.MAX_PLAYER; p += 1) {
            hh.b4(this.ec.credits[p]);
            hh.b2(this.ec.supplyUsed[p]);
            hh.b2(this.ec.supplyCap[p]);
        }
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            hh.b1(w.alive[i]);
            if (w.alive[i] === 0)
                continue;
            hh.b1(w.owner[i]);
            hh.b1(w.kind[i]);
            hh.b1(w.tx[i]);
            hh.b1(w.ty[i]);
            hh.b2(w.hp[i]);
            hh.b1(w.dir[i]);
            hh.b1(w.state[i]);
            hh.b4(w.px[i]);
            hh.b4(w.py[i]);
            hh.b2(w.target[i]);
            hh.b2(w.load[i]);
            hh.b4(w.prog[i]);
            hh.b2(w.from_t[i]);
            hh.b2(w.to_t[i]);
            hh.b2(w.cool[i]);
            hh.b2(w.timer[i]);
        }
        hh.b2(this.pj.n());
        for (let k = 0; k < this.pj.n(); k += 1) {
            hh.b4(this.pj.x[k]);
            hh.b4(this.pj.y[k]);
            hh.b4(this.pj.vx[k]);
            hh.b4(this.pj.vy[k]);
            hh.b2(this.pj.target[k]);
            hh.b2(this.pj.dmg[k]);
        }
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 0 || C.IS_BUILDING[w.kind[i]] === 0)
                continue;
            hh.b1(this.ec.queue[i].length);
            for (const k of this.ec.queue[i])
                hh.b1(k);
            hh.b2(this.ec.progress[i]);
        }
        const ores = [];
        for (let i = 0; i < this.ec.ore.length; i += 1) {
            if (this.ec.ore[i] > 0)
                ores.push(i);
        }
        hh.b2(ores.length);
        for (const i of ores) {
            hh.b2(i);
            hh.b2(this.ec.ore[i]);
        }
        hh.b4(this.mapHash());
        return hh.h;
    }
    // ── SPEC §18.6 선택자 ────────────────────────────────────────────────────
    select(p, sel) {
        const w = this.w;
        const out = [];
        if (sel === 'N') {
            const h = this.lastSpawn[p];
            return w.valid(h) ? [h] : [];
        }
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 0 || w.owner[i] !== p)
                continue;
            const k = w.kind[i];
            if (sel === 'A') {
                if (C.IS_BUILDING[k] === 0)
                    out.push(w.handle(i));
            }
            else if (sel === 'F') {
                if (C.IS_BUILDING[k] === 0 && C.BASIC[k] > 0)
                    out.push(w.handle(i));
            }
            else if (sel.indexOf('K') === 0) {
                if (k === parseInt(sel.slice(1), 10))
                    out.push(w.handle(i));
            }
        }
        out.sort((a, b) => a - b);
        return out;
    }
    // 스크립트도 사람과 똑같은 경로를 지난다 — 뒷문을 내지 않는다.
    scriptOrders(script, tick) {
        const out = [];
        for (const [t, p, sel, cmd, a, b, c] of script.lines) {
            if (t !== tick)
                continue;
            for (const h of this.select(p, sel))
                out.push([p, h, exports.CMD[cmd], a, b, c]);
        }
        out.sort(cmpOrder);
        return out;
    }
}
exports.Sim = Sim;
// 튜플 사전식 비교 — 파이썬 list.sort() 의 기본 순서와 같다.
function cmpOrder(a, b) {
    for (let i = 0; i < a.length && i < b.length; i += 1) {
        if (a[i] !== b[i])
            return a[i] < b[i] ? -1 : 1;
    }
    return a.length - b.length;
}
function cmpTriple(a, b) {
    if (a[0] !== b[0])
        return a[0] < b[0] ? -1 : 1;
    if (a[1] !== b[1])
        return a[1] < b[1] ? -1 : 1;
    if (a[2] !== b[2])
        return a[2] < b[2] ? -1 : 1;
    return 0;
}
  });
  __def('net', function (exports, require, module, __dirname) {
"use strict";
// 락스텝 네트워크 — 명령만 보낸다 (SPEC §19).
//
//    유닛 200기의 상태는 매 틱 수 KB 다. 명령은 대개 0개이고, 있어도 한 줄이면
//    20바이트다. 28.8 kbps 모뎀에서 전자는 불가능하고 후자는 여유롭다. 대신
//    **모든 기계가 같은 계산을 해야 한다**는 대가를 치른다.
//
//    지터가 있어도 결과는 같다. 명령의 **실행 틱은 보낼 때 정해지고**, 늦게
//    도착하면 그 틱을 기다릴 뿐이다. 늦게 도착한 명령을 앞당겨 실행하는 경로는
//    존재하지 않는다 — 그런 경로가 하나라도 있으면 락스텝은 그 자리에서 끝난다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Net = void 0;
const C = require("./const");
const rng_1 = require("./rng");
function cmpOrder(a, b) {
    for (let i = 0; i < a.length && i < b.length; i += 1) {
        if (a[i] !== b[i])
            return a[i] < b[i] ? -1 : 1;
    }
    return a.length - b.length;
}
class Net {
    constructor(nPlayers, latency = C.ORDER_DELAY, jitterSeed = 0, jitterMax = 0) {
        this.n = nPlayers;
        this.latency = latency;
        this.jitterMax = jitterMax;
        // 지터는 **전용 RNG** 로 만든다. 시뮬레이션 RNG(§3.3)를 쓰면 네트워크
        // 사정이 게임 내용을 바꾸고, 그것이야말로 디싱크의 정의다.
        this.rng = new rng_1.LCG(jitterSeed);
        this.box = new Map();
        this.sealed = new Map();
        this.delay = new Map();
        this.stalls = 0;
    }
    // 실행 틱은 지터와 무관하다.
    execOf(tick, _player) {
        return tick + this.latency;
    }
    arriveOf(tick, player) {
        const key = tick * 16 + player;
        if (!this.delay.has(key)) {
            const j = this.jitterMax !== 0 ? this.rng.roll(this.jitterMax + 1) : 0;
            this.delay.set(key, tick + this.latency + j);
            if (j > 0)
                this.stalls += 1;
        }
        return this.delay.get(key);
    }
    send(tick, player, order) {
        this.arriveOf(tick, player);
        const et = this.execOf(tick, player);
        let lst = this.box.get(et);
        if (lst === undefined) {
            lst = [];
            this.box.set(et, lst);
        }
        lst.push(order);
        return et;
    }
    // 빈 턴도 보낸다. 그래야 상대가 영원히 기다리지 않는다.
    flush(tick, player) {
        const et = this.execOf(tick, player);
        let d = this.sealed.get(et);
        if (d === undefined) {
            d = new Map();
            this.sealed.set(et, d);
        }
        d.set(player, this.arriveOf(tick, player));
        return et;
    }
    // 그 실행 틱의 몫이 **전원** 도착했는가. wall 은 지금 시각(틱)이다.
    ready(execTick, wall) {
        const d = this.sealed.get(execTick);
        if (d === undefined || d.size !== this.n)
            return false;
        if (wall === undefined || wall === null)
            return true;
        const keys = Array.from(d.keys());
        keys.sort((a, b) => a - b);
        for (const p of keys) {
            if (d.get(p) > wall)
                return false;
        }
        return true;
    }
    // 그 틱의 명령을 §18.1 의 키로 정렬해 돌려준다. 한 번만 준다.
    take(execTick) {
        const out = this.box.get(execTick);
        this.box.delete(execTick);
        if (out === undefined)
            return [];
        out.sort(cmpOrder);
        return out;
    }
}
exports.Net = Net;
  });
  __def('replay', function (exports, require, module, __dirname) {
"use strict";
// 저장·리플레이·압축 (SPEC §20).
//
//    리플레이는 **명령 로그**다. 상태는 한 바이트도 저장하지 않는다. 재생한다는
//    것은 같은 시드로 시뮬을 새로 만들어 같은 명령을 같은 틱에 먹이는 것이고,
//    결과가 같다는 증명은 `hashes.txt` 와의 대조가 대신한다.
//
//    비트 연산자는 쓰지 않는다(§1.1). LZSS 의 토큰도 곱셈과 나눗셈으로 접는다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.MAX_MATCH = exports.MIN_MATCH = exports.WINDOW = exports.VERSION = exports.MAGIC = void 0;
exports.save = save;
exports.load = load;
exports.rleEncode = rleEncode;
exports.rleDecode = rleDecode;
exports.lzssEncode = lzssEncode;
exports.lzssDecode = lzssDecode;
const F = require("./fixed");
exports.MAGIC = 'RTSR';
exports.VERSION = 1;
exports.WINDOW = 4096;
exports.MIN_MATCH = 3;
exports.MAX_MATCH = 18;
function b2(out, v0) {
    const v = F.fmod(v0, 65536);
    out.push(F.floordiv(v, 256));
    out.push(F.fmod(v, 256));
}
function b4(out, v0) {
    const v = F.fmod(v0, 4294967296);
    b2(out, F.floordiv(v, 65536));
    b2(out, F.fmod(v, 65536));
}
function r2(b, i) {
    return [b[i] * 256 + b[i + 1], i + 2];
}
function r4(b, i0) {
    const [hi, i1] = r2(b, i0);
    const [lo, i2] = r2(b, i1);
    return [hi * 65536 + lo, i2];
}
// 로그 항목 정렬 — 파이썬 sorted(log) 와 같은 순서(틱, 그다음 명령 목록).
function cmpLog(a, b) {
    if (a[0] !== b[0])
        return a[0] < b[0] ? -1 : 1;
    const n = Math.min(a[1].length, b[1].length);
    for (let i = 0; i < n; i += 1) {
        const x = a[1][i];
        const y = b[1][i];
        for (let k = 0; k < x.length && k < y.length; k += 1) {
            if (x[k] !== y[k])
                return x[k] < y[k] ? -1 : 1;
        }
    }
    return a[1].length - b[1].length;
}
// ── SPEC §20.2 ──────────────────────────────────────────────────────────────
// log 는 (틱, 명령 목록). 명령은 §18.1 의 여섯 칸이다.
function save(seed, players, ticks, log) {
    const out = [];
    for (const ch of exports.MAGIC)
        out.push(ch.charCodeAt(0));
    out.push(exports.VERSION);
    b4(out, seed);
    out.push(players);
    b4(out, ticks);
    b2(out, log.length);
    const sorted = log.slice();
    sorted.sort(cmpLog);
    for (const [t, orders] of sorted) {
        b4(out, t);
        out.push(orders.length);
        for (const o of orders) {
            out.push(o[0]); // 플레이어
            out.push(o[2]); // 종류
            b2(out, o[1]); // 발령자 핸들
            out.push(o[3]);
            out.push(o[4]);
            b2(out, o[5]);
        }
    }
    const crc = F.crc16(out);
    b2(out, crc);
    return out;
}
function load(blob) {
    const b = [];
    for (let i = 0; i < blob.length; i += 1)
        b.push(blob[i]);
    if (String.fromCharCode(b[0], b[1], b[2], b[3]) !== exports.MAGIC) {
        throw new Error('리플레이 파일이 아니다');
    }
    const want = b[b.length - 2] * 256 + b[b.length - 1];
    if (F.crc16(b.slice(0, b.length - 2)) !== want) {
        throw new Error('CRC 불일치 — 리플레이가 깨졌다');
    }
    let i = 5;
    let seed = 0;
    [seed, i] = r4(b, i);
    const players = b[i];
    i += 1;
    let ticks = 0;
    [ticks, i] = r4(b, i);
    let n = 0;
    [n, i] = r2(b, i);
    const log = [];
    for (let k = 0; k < n; k += 1) {
        let t = 0;
        [t, i] = r4(b, i);
        const cnt = b[i];
        i += 1;
        const orders = [];
        for (let j = 0; j < cnt; j += 1) {
            const p = b[i];
            const kind = b[i + 1];
            const [issuer, i2] = r2(b, i + 2);
            const a = b[i2];
            const bb = b[i2 + 1];
            let c = 0;
            [c, i] = r2(b, i2 + 2);
            orders.push([p, issuer, kind, a, bb, c]);
        }
        log.push([t, orders]);
    }
    return [seed, players, ticks, log];
}
// ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────
// (개수, 값) 쌍. 개수는 1..255 — 넘으면 쌍을 나눈다.
function rleEncode(data) {
    const out = [];
    let i = 0;
    while (i < data.length) {
        const v = data[i];
        let run = 1;
        while (i + run < data.length && data[i + run] === v && run < 255)
            run += 1;
        out.push(run);
        out.push(v);
        i += run;
    }
    return out;
}
function rleDecode(data) {
    const out = [];
    let i = 0;
    while (i < data.length) {
        for (let k = 0; k < data[i]; k += 1)
            out.push(data[i + 1]);
        i += 2;
    }
    return out;
}
// ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
// 가장 긴 일치, 동점이면 가장 가까운 것. 탐욕적이다 — 최적 파싱은 안 한다.
// O(창 × 최대일치) = 4096 × 18. 20부는 이 단순함의 대가를 실측으로 보인다.
function match(b, pos) {
    let bestLen = 0;
    let bestOff = 0;
    let start = pos - exports.WINDOW;
    if (start < 0)
        start = 0;
    let limit = b.length - pos;
    if (limit > exports.MAX_MATCH)
        limit = exports.MAX_MATCH;
    for (let j = pos - 1; j >= start; j -= 1) { // 가까운 쪽부터 훑는다
        let k = 0;
        while (k < limit && b[j + k] === b[pos + k])
            k += 1; // 겹치는 일치도 허용
        if (k > bestLen) {
            bestLen = k;
            bestOff = pos - j;
            if (bestLen === limit)
                break;
        }
    }
    return [bestLen, bestOff];
}
function lzssEncode(data) {
    const b = [];
    for (let i = 0; i < data.length; i += 1)
        b.push(data[i]);
    const out = [];
    let pos = 0;
    while (pos < b.length) {
        let flag = 0;
        const chunk = [];
        let bit = 1;
        let used = 0;
        while (used < 8 && pos < b.length) {
            const [ln, off] = match(b, pos);
            if (ln >= exports.MIN_MATCH) {
                const o = off - 1; // 1..4096 → 0..4095
                chunk.push(F.floordiv(o, 16));
                chunk.push(F.fmod(o, 16) * 16 + (ln - exports.MIN_MATCH));
                pos += ln;
            }
            else {
                flag += bit; // 비트 1 = 리터럴
                chunk.push(b[pos]);
                pos += 1;
            }
            bit *= 2;
            used += 1;
        }
        out.push(flag);
        for (const v of chunk)
            out.push(v);
    }
    return out;
}
function lzssDecode(data) {
    const b = [];
    for (let i = 0; i < data.length; i += 1)
        b.push(data[i]);
    const out = [];
    let i = 0;
    while (i < b.length) {
        let flag = b[i];
        i += 1;
        for (let k = 0; k < 8; k += 1) {
            if (i >= b.length)
                break;
            if (F.fmod(flag, 2) === 1) {
                out.push(b[i]);
                i += 1;
            }
            else {
                const o = b[i] * 16 + F.floordiv(b[i + 1], 16);
                const ln = F.fmod(b[i + 1], 16) + exports.MIN_MATCH;
                i += 2;
                const src = out.length - (o + 1);
                for (let j = 0; j < ln; j += 1)
                    out.push(out[src + j]); // 겹침 허용
            }
            flag = F.floordiv(flag, 2);
        }
    }
    return out;
}
  });
  __def('speaker', function (exports, require, module, __dirname) {
"use strict";
// PC 스피커 — 분주값·음표표·사각파 (SPEC §21).
//
//    PIT 은 사각파만 낼 수 있었다. 음량 조절이 없었고 듀티비도 고정이라,
//    도스 게임의 스피커 음악은 전부 같은 음색이다. 여기서 하는 일은 그 제약을
//    그대로 흉내내는 것뿐이다. 소리를 재생하지 않는다 — 헤드리스 환경이고,
//    바이트가 같으면 소리도 같다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.NOTE_HZ = exports.NOTE_NAME = exports.AMP_MID = exports.AMP_HI = exports.AMP_LO = exports.SAMPLE_RATE = void 0;
exports.divisor = divisor;
exports.actual = actual;
exports.actual100 = actual100;
exports.halfPeriod = halfPeriod;
exports.square = square;
exports.wav = wav;
exports.tune = tune;
const C = require("./const");
const F = require("./fixed");
exports.SAMPLE_RATE = 22050;
exports.AMP_LO = 0x40;
exports.AMP_HI = 0xC0;
exports.AMP_MID = 0x80;
// §21.2 A4 = 440 Hz 12평균율을 **정수 Hz 로 반올림해 박아 둔다.**
// 세 언어가 같은 표를 갖는 것이 실수 연산을 맞추는 것보다 싸고 확실하다.
exports.NOTE_NAME = ['C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4',
    'G#4', 'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5',
    'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5'];
exports.NOTE_HZ = [262, 277, 294, 311, 330, 349, 370, 392, 415, 440,
    466, 494, 523, 554, 587, 622, 659, 698, 740, 784,
    831, 880, 932, 988];
// ── SPEC §21.1 분주값 ───────────────────────────────────────────────────────
// 반올림 나눗셈. PIT_HZ 자체가 반올림값이라는 것을 22부가 따로 따진다.
function divisor(f) {
    if (f <= 0)
        return 0;
    const d = F.floordiv(C.PIT_HZ + F.floordiv(f, 2), f);
    return d < 1 ? 1 : d;
}
// 실제로 나는 주파수를 **정수 나눗셈의 몫과 나머지**로 낸다.
// 센트 오차는 로그가 필요하므로 엔진이 아니라 tools/gen_prim.py 가 낸다.
function actual(f) {
    const d = divisor(f);
    if (d === 0)
        return [0, 0];
    return [F.floordiv(C.PIT_HZ, d), F.fmod(C.PIT_HZ, d)];
}
function actual100(f) {
    const d = divisor(f);
    return d === 0 ? 0 : F.floordiv(C.PIT_HZ * 100, d);
}
// ── SPEC §21.3 사각파 합성 ──────────────────────────────────────────────────
function halfPeriod(f) {
    const q = actual(f)[0];
    if (q <= 0)
        return 0;
    return F.floordiv(exports.SAMPLE_RATE, 2 * q);
}
// 8비트 부호 없는 모노 PCM n 샘플. f <= 0 이면 무음(쉼표).
function square(f, n) {
    if (n <= 0)
        return [];
    if (f <= 0)
        return new Array(n).fill(exports.AMP_MID);
    const half = halfPeriod(f);
    if (half <= 0)
        return new Array(n).fill(exports.AMP_MID);
    const out = [];
    for (let k = 0; k < n; k += 1) {
        out.push(F.fmod(F.floordiv(k, half), 2) === 0 ? exports.AMP_LO : exports.AMP_HI);
    }
    return out;
}
function le(out, v0, n) {
    let v = v0;
    for (let k = 0; k < n; k += 1) {
        out.push(F.fmod(v, 256));
        v = F.floordiv(v, 256);
    }
}
// 44바이트 헤더 + PCM. 전체 바이트의 FNV-1a 를 골든으로 둔다.
function wav(pcm) {
    const out = [];
    const push = (s) => {
        for (const ch of s)
            out.push(ch.charCodeAt(0));
    };
    push('RIFF');
    le(out, 36 + pcm.length, 4);
    push('WAVE');
    push('fmt ');
    le(out, 16, 4); // fmt 청크 길이
    le(out, 1, 2); // PCM
    le(out, 1, 2); // 모노
    le(out, exports.SAMPLE_RATE, 4);
    le(out, exports.SAMPLE_RATE, 4); // 바이트/초 = 레이트 × 1채널 × 1바이트
    le(out, 1, 2); // 블록 정렬
    le(out, 8, 2); // 비트/샘플
    push('data');
    le(out, pcm.length, 4);
    for (let i = 0; i < pcm.length; i += 1)
        out.push(pcm[i]);
    return out;
}
// (주파수, 샘플 수) 목록을 이어 붙여 WAV 로.
function tune(notes) {
    const pcm = [];
    for (const [f, n] of notes) {
        for (const v of square(f, n))
            pcm.push(v);
    }
    return wav(pcm);
}
  });
  __def('raster', function (exports, require, module, __dirname) {
"use strict";
// 래스터 — 프레임버퍼·팔레트·스프라이트·블릿·폰트·PPM (SPEC §22).
//
//    세 언어 모두 프레임버퍼가 **1차원 정수 배열**이다. 이것이 세 구현을 바이트
//    단위로 비교 가능하게 만드는 유일한 이유다. 프런트엔드는 이 배열에 팔레트로
//    색을 입혀 화면에 올릴 뿐이고, `make parity` 는 192,015바이트짜리 PPM 을
//    `cmp` 한다.
//
//    팔레트와 스프라이트는 정수식으로 만든다(§22.2·§22.3). 표를 세 언어에 옮겨
//    적는 대신 같은 식을 세 번 쓰고, 결과를 골든과 대조한다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dirty = exports.Frame = exports.SPRITES = exports.Sprite = exports.FONT_FIRST = exports.FONT_ADV = exports.FONT_H = exports.FONT_W = exports.FONT = exports.UI = exports.TERRAIN_RAMP = exports.PLAYER_RAMP = exports.EGA = exports.BLD_NAME = exports.UNIT_NAME = exports.UNIT_M = exports.UNIT_R = exports.DRAWN_DIRS = exports.WATER_N = exports.WATER_BASE = exports.SHADOW = exports.PLAYER_SHADES = exports.PLAYER_BASE = void 0;
exports.ramp = ramp;
exports.buildPalette = buildPalette;
exports.buildLight = buildLight;
exports.cycleWater = cycleWater;
exports.unitSprite = unitSprite;
exports.buildingSprite = buildingSprite;
exports.spriteFor = spriteFor;
exports.blit = blit;
exports.text = text;
exports.expand = expand;
exports.toPpm = toPpm;
const CI = require("./circle");
const C = require("./const");
const F = require("./fixed");
exports.PLAYER_BASE = 160;
exports.PLAYER_SHADES = 8;
exports.SHADOW = 251;
exports.WATER_BASE = 232;
exports.WATER_N = 8;
exports.DRAWN_DIRS = 5; // §22.7 그린 방향 수 (나머지 셋은 좌우 반전)
exports.UNIT_R = [5, 4, 6, 5, 5];
exports.UNIT_M = [3, 3, 4, 3, 3];
exports.UNIT_NAME = ['INF', 'ARCHER', 'TANK', 'MORTAR', 'HARV'];
exports.BLD_NAME = [
    [C.HQ, 'HQ'], [C.REF, 'REF'], [C.BARR, 'BARR'],
    [C.FACT, 'FACT'], [C.POW, 'POW'], [C.TOWER, 'TOWER']
];
exports.EGA = [
    [0, 0, 42], [0, 42, 0], [0, 42, 42], [42, 0, 0], [42, 0, 42],
    [42, 21, 0], [42, 42, 42], [21, 21, 21], [21, 21, 63], [21, 63, 21],
    [21, 63, 63], [63, 21, 21], [63, 21, 63], [63, 63, 21], [63, 63, 63]
];
exports.PLAYER_RAMP = [
    [[16, 4, 4], [63, 26, 26]], [[4, 8, 20], [26, 38, 63]],
    [[4, 18, 6], [26, 56, 26]], [[20, 16, 4], [63, 58, 20]]
];
exports.TERRAIN_RAMP = [
    [[24, 14, 6], [46, 34, 18]], [[44, 40, 26], [18, 18, 20]],
    [[20, 20, 22], [40, 40, 42]], [[6, 10, 30], [22, 34, 54]],
    [[40, 32, 4], [63, 58, 26]], [[0, 0, 0], [30, 30, 30]]
];
exports.UI = [
    [0, 0, 0], [10, 10, 12], [20, 20, 24], [30, 30, 34], [42, 42, 46],
    [52, 52, 56], [63, 63, 63], [63, 52, 20], [52, 20, 20], [20, 52, 20],
    [20, 20, 52], [40, 40, 10], [30, 8, 8], [8, 30, 8], [8, 8, 30],
    [32, 32, 32]
];
const FONT_HEX = '000000000000000008080808080008000000000000000000143e14143e14000000000000'
    + '000000003234081026060000000000000000000000000000000000000408101010080400'
    + '100804040408100000000000000000000008083e0808000000000000181810000000003e'
    + '00000000000000000018180002020408102020001c22262a32221c000818080808081c00'
    + '1c22020408103e003c02021c02023c00040c14243e0404003e203c0202221c000c10203c'
    + '22221c003e020408101010001c22221c22221c001c22221e020418000018180018180000'
    + '00000000000000000000000000000000000000000000000000000000000000001c220204'
    + '0800080000000000000000001c22223e222222003c22223c22223c001c22202020221c00'
    + '3c22222222223c003e20203c20203e003e20203c202020001c22202e22221c002222223e'
    + '222222001c08080808081c000e0404040424180022242830282422002020202020203e00'
    + '22362a2a2222220022322a2a262222001c22222222221c003c22223c202020001c222222'
    + '2a241a003c22223c282422001e20201c02023c003e080808080808002222222222221c00'
    + '22222222221408002222222a2a362200222214081422220022221408080808003e020408'
    + '10203e000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '000000000000000000000000000000000000000000000000000000000000000000000000'
    + '00000000';
exports.FONT = (() => {
    const out = [];
    for (let k = 0; k < FONT_HEX.length / 2; k += 1) {
        out.push(parseInt(FONT_HEX.slice(k * 2, k * 2 + 2), 16));
    }
    return out;
})();
exports.FONT_W = 6;
exports.FONT_H = 8;
exports.FONT_ADV = 6;
exports.FONT_FIRST = 32;
// ── SPEC §22.2 팔레트 ───────────────────────────────────────────────────────
// 두 끝색 사이의 정수 보간. 나눗셈은 내림이다.
function ramp(c0, c1, i) {
    return [c0[0] + F.floordiv((c1[0] - c0[0]) * i, 7),
        c0[1] + F.floordiv((c1[1] - c0[1]) * i, 7),
        c0[2] + F.floordiv((c1[2] - c0[2]) * i, 7)];
}
function buildPalette() {
    const pal = [];
    for (let i = 0; i < 256; i += 1)
        pal.push([0, 0, 0]);
    for (let k = 0; k < 15; k += 1)
        pal[1 + k] = exports.EGA[k];
    for (let i = 0; i < 16; i += 1) {
        const g = F.floordiv(i * 63, 15);
        pal[16 + i] = [g, g, g];
    }
    for (let p = 0; p < 4; p += 1) {
        const [c0, c1] = exports.PLAYER_RAMP[p];
        for (let i = 0; i < exports.PLAYER_SHADES; i += 1) {
            pal[exports.PLAYER_BASE + p * exports.PLAYER_SHADES + i] = ramp(c0, c1, i);
        }
    }
    for (let i = 0; i < 16; i += 1)
        pal[192 + i] = exports.UI[i];
    for (let r = 0; r < 6; r += 1) {
        const [c0, c1] = exports.TERRAIN_RAMP[r];
        for (let i = 0; i < 8; i += 1)
            pal[208 + r * 8 + i] = ramp(c0, c1, i);
    }
    return pal;
}
// 명암 단계 l 에서 색 c 에 가장 가까운 항목. 동점이면 인덱스 최소.
// 256 × 256 × 4 = 262,144회 비교이며 **시작할 때 한 번**이다. 안개(§14.4)가
// 이 표를 쓴다 — 안개 때문에 색 계산을 하지 않으려고 표로 미리 굳힌다.
function buildLight(pal) {
    const out = [];
    for (let l = 0; l < 4; l += 1) {
        const row = new Array(256).fill(0);
        for (let c = 0; c < 256; c += 1) {
            const wr = F.floordiv(pal[c][0] * l, 3);
            const wg = F.floordiv(pal[c][1] * l, 3);
            const wb = F.floordiv(pal[c][2] * l, 3);
            let best = 0;
            let bd = -1;
            for (let j = 0; j < 256; j += 1) {
                const dr = pal[j][0] - wr;
                const dg = pal[j][1] - wg;
                const db = pal[j][2] - wb;
                const d = dr * dr + dg * dg + db * db;
                if (bd < 0 || d < bd) {
                    bd = d;
                    best = j;
                }
            }
            row[c] = best;
        }
        out.push(row);
    }
    return out;
}
// ── SPEC §22.6 팔레트 사이클링 ──────────────────────────────────────────────
// 물 색 8칸을 한 칸씩 돌린다. **프레임버퍼는 건드리지 않는다** —
// 팔레트 모드의 가장 큰 장점이었던 공짜 애니메이션이다.
function cycleWater(pal, phase) {
    const out = pal.slice();
    for (let i = 0; i < exports.WATER_N; i += 1) {
        out[exports.WATER_BASE + i] = pal[exports.WATER_BASE + F.fmod(i + phase, exports.WATER_N)];
    }
    return out;
}
// ── SPEC §22.3 스프라이트 ───────────────────────────────────────────────────
class Sprite {
    constructor(w, h, ox, oy, data) {
        this.w = w;
        this.h = h;
        this.ox = ox;
        this.oy = oy;
        this.data = data;
    }
    pixels() {
        const out = [];
        const d = this.data;
        let i = 0;
        while (i < d.length) {
            for (let k = 0; k < d[i]; k += 1)
                out.push(d[i + 1]);
            i += 2;
        }
        return out;
    }
}
exports.Sprite = Sprite;
function rle(px) {
    const out = [];
    let i = 0;
    while (i < px.length) {
        const v = px[i];
        let run = 1;
        while (i + run < px.length && px[i + run] === v && run < 255)
            run += 1;
        out.push(run);
        out.push(v);
        i += run;
    }
    return out;
}
// §6.2 의 행 span 으로 원을 채운다 — 곱셈도 제곱근도 쓰지 않는다.
function disc(px, w, cx, cy, r, colour, onlyBelow = false, onlyEmpty = false) {
    const sp = CI.spans(r);
    const h = Math.floor(px.length / w);
    for (let dy = -r; dy <= r; dy += 1) {
        if (onlyBelow && dy < 0)
            continue;
        const wdt = sp[dy >= 0 ? dy : -dy];
        const y = cy + dy;
        for (let dx = -wdt; dx <= wdt; dx += 1) {
            const x = cx + dx;
            if (x >= 0 && x < w && y >= 0 && y < h) {
                if (onlyEmpty && px[y * w + x] !== 0)
                    continue;
                px[y * w + x] = colour;
            }
        }
    }
}
function unitSprite(k, d) {
    const w = C.TILE;
    const h = C.TILE;
    const px = new Array(w * h).fill(0);
    const r = exports.UNIT_R[k];
    disc(px, w, 8, 9, r, exports.PLAYER_BASE + 1); // 테두리
    disc(px, w, 8, 9, r - 1, exports.PLAYER_BASE + 3); // 속
    disc(px, w, 8, 14, 3, exports.SHADOW, true, true); // 그림자 (아래 절반, 빈 곳만)
    const mx = 8 + F.DX[d] * exports.UNIT_M[k];
    const my = 9 + F.DY[d] * exports.UNIT_M[k];
    for (let y = my; y < my + 2; y += 1) {
        for (let x = mx; x < mx + 2; x += 1) {
            if (x >= 0 && x < w && y >= 0 && y < h)
                px[y * w + x] = exports.PLAYER_BASE + 6;
        }
    }
    return new Sprite(w, h, 8, 14, rle(px));
}
function buildingSprite(foot) {
    const w = C.TILE * foot;
    const h = C.TILE * foot;
    const px = new Array(w * h).fill(0);
    for (let y = 4; y < h - 2; y += 1) {
        for (let x = 2; x < w - 2; x += 1) {
            const edge = (x === 2 || x === w - 3 || y === 4 || y === h - 3);
            px[y * w + x] = exports.PLAYER_BASE + (edge ? 5 : 2);
        }
    }
    for (let y = 4; y < 7; y += 1) {
        for (let x = 2; x < w - 2; x += 1)
            px[y * w + x] = exports.PLAYER_BASE + 6; // 지붕
    }
    for (let y = h - 6; y < h - 2; y += 1) {
        for (let x = Math.floor(w / 2) - 2; x < Math.floor(w / 2) + 2; x += 1) {
            px[y * w + x] = exports.PLAYER_BASE; // 문
        }
    }
    return new Sprite(w, h, Math.floor(w / 2), h - 2, rle(px));
}
exports.SPRITES = (() => {
    const out = {};
    for (let k = 0; k < 5; k += 1) {
        for (let d = 0; d < exports.DRAWN_DIRS; d += 1) {
            out[exports.UNIT_NAME[k] + '_' + d] = unitSprite(k, d);
        }
    }
    for (const [kind, name] of exports.BLD_NAME)
        out[name] = buildingSprite(C.FOOT[kind]);
    return out;
})();
// §22.7 — 그린 것은 5방향뿐이다. (스프라이트, 반전 여부).
function spriteFor(kind, d) {
    if (C.IS_BUILDING[kind] !== 0) {
        for (const [k, name] of exports.BLD_NAME) {
            if (k === kind)
                return [exports.SPRITES[name], false];
        }
        return [null, false];
    }
    if (d <= 4)
        return [exports.SPRITES[exports.UNIT_NAME[kind] + '_' + d], false];
    return [exports.SPRITES[exports.UNIT_NAME[kind] + '_' + (8 - d)], true];
}
// ── SPEC §22.1 프레임버퍼 ───────────────────────────────────────────────────
class Frame {
    constructor(w = C.SCR_W, h = C.SCR_H) {
        this.w = w;
        this.h = h;
        this.fb = new Array(w * h).fill(0);
    }
    clear(v = 0) {
        for (let i = 0; i < this.fb.length; i += 1)
            this.fb[i] = v;
    }
    rect(x, y, w, h, v) {
        for (let j = Math.max(0, y); j < Math.min(this.h, y + h); j += 1) {
            const row = j * this.w;
            for (let i = Math.max(0, x); i < Math.min(this.w, x + w); i += 1) {
                this.fb[row + i] = v;
            }
        }
    }
}
exports.Frame = Frame;
// ── SPEC §22.4 클리핑 블릿 ──────────────────────────────────────────────────
// 런 단위로 자른다 — 픽셀마다 경계를 검사하지 않는다 (정리 22.1).
// 완전히 화면 밖이면 런을 하나도 훑지 않고 돌아간다.
function blit(fb, spr, x, y, owner = 0, flip = false, light = null, level = 3) {
    // 반전해도 상자 자체는 그대로 두고 상자 **안에서** 뒤집는다. 기준점은
    // (w - 1 - 2*ox) 픽셀만큼 옮겨지는데(폭 16·ox 8 이면 1px), 세 언어가
    // 같은 자리에 그리는 것이 그 1px 보다 중요하다.
    const x0 = x - spr.ox;
    const y0 = y - spr.oy;
    if (x0 + spr.w <= 0 || x0 >= C.SCR_W || y0 + spr.h <= 0 || y0 >= C.SCR_H) {
        return;
    }
    const add = owner * exports.PLAYER_SHADES;
    const d = spr.data;
    let i = 0;
    let pos = 0;
    while (i < d.length) {
        const run = d[i];
        const val = d[i + 1];
        i += 2;
        if (val === 0) { // 컬러키 — 통째로 건너뛴다
            pos += run;
            continue;
        }
        let colour = (val >= exports.PLAYER_BASE && val < exports.PLAYER_BASE + exports.PLAYER_SHADES)
            ? val + add : val;
        if (light !== null && level < 3)
            colour = light[level][colour];
        let p = pos;
        const end = pos + run;
        while (p < end) {
            const sy = F.floordiv(p, spr.w);
            const sx = F.fmod(p, spr.w);
            let n = end - p;
            if (n > spr.w - sx)
                n = spr.w - sx; // 이 줄에 걸치는 만큼만
            const fy = y0 + sy;
            if (fy >= 0 && fy < C.SCR_H) {
                const fx = flip ? x0 + (spr.w - 1 - (sx + n - 1)) : x0 + sx;
                const a = fx > 0 ? fx : 0;
                let b = fx + n;
                if (b > C.SCR_W)
                    b = C.SCR_W;
                const row = fy * C.SCR_W;
                for (let q = a; q < b; q += 1)
                    fb[row + q] = colour;
            }
            p += n;
        }
        pos = end;
    }
}
// ── SPEC §22.8 폰트 ─────────────────────────────────────────────────────────
// 6×8 칸에 5×7 획. 소문자는 빈 글자다(§22.8).
function text(fb, s, x0, y, colour) {
    let x = x0;
    for (const ch of s) {
        const code = ch.charCodeAt(0);
        if (code >= exports.FONT_FIRST && code < exports.FONT_FIRST + 95) {
            const base = (code - exports.FONT_FIRST) * exports.FONT_H;
            for (let j = 0; j < exports.FONT_H; j += 1) {
                const v = exports.FONT[base + j];
                const fy = y + j;
                if (!(fy >= 0 && fy < C.SCR_H))
                    continue;
                for (let k = 0; k < exports.FONT_W; k += 1) {
                    if (F.fmod(F.floordiv(v, F.pow2(5 - k)), 2) === 1) {
                        const fx = x + k;
                        if (fx >= 0 && fx < C.SCR_W)
                            fb[fy * C.SCR_W + fx] = colour;
                    }
                }
            }
        }
        x += exports.FONT_ADV;
    }
}
// ── SPEC §22.9 더티 렉트 ────────────────────────────────────────────────────
// 8개를 넘으면 전체를 다시 그린다 — 합치는 비용이 이득을 넘는 지점이다.
class Dirty {
    constructor() {
        this.r = [];
    }
    add(x, y, w, h) {
        this.r.push([x, y, w, h]);
    }
    rects() {
        if (this.r.length > Dirty.MAX)
            return [[0, 0, C.SCR_W, C.SCR_H]];
        return this.r.slice();
    }
    clear() {
        this.r = [];
    }
}
exports.Dirty = Dirty;
Dirty.MAX = 8;
// ── SPEC §22.10 PPM ─────────────────────────────────────────────────────────
// 0…63 을 0…255 로. v*255/63 이 아니라 곱셈·나눗셈 하나씩이다.
function expand(v) {
    return v * 4 + F.floordiv(v, 16);
}
function toPpm(fb, pal) {
    const out = [];
    const head = 'P6\n' + C.SCR_W + ' ' + C.SCR_H + '\n255\n';
    for (const ch of head)
        out.push(ch.charCodeAt(0));
    const lut = [];
    for (const c of pal) {
        lut.push(expand(c[0]));
        lut.push(expand(c[1]));
        lut.push(expand(c[2]));
    }
    for (const v of fb) {
        const j = v * 3;
        out.push(lut[j]);
        out.push(lut[j + 1]);
        out.push(lut[j + 2]);
    }
    return out;
}
  });
  __def('render', function (exports, require, module, __dirname) {
"use strict";
// 화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).
//
//    렌더는 **상태를 읽기만 한다.** sim 을 건드리는 줄이 하나라도 생기면
//    락스텝이 끝난다(§18.1). 팔레트 사이클 위상도 인자로만 받는다.
//
//    지형 타일은 그림이 아니라 색이다(§23.1). 아티스트가 없으므로 한 칸을
//    MINI_COLOR 로 채우고, 오토타일 마스크가 가리키는 "나와 다른 지형" 쪽
//    가장자리 1px 만 어둡게 긋는다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.View = exports.UI_SELECT = exports.UI_HP_BAD = exports.UI_HP_GOOD = exports.UI_TEXT = exports.UI_LIGHT = exports.UI_MID = exports.UI_DARK = exports.MAX_CAM_Y = exports.MAX_CAM_X = exports.EDGE_MARGIN = exports.EDGE_SPEED = exports.TILES_Y = exports.TILES_X = void 0;
exports.edgeScroll = edgeScroll;
exports.sortKey = sortKey;
exports.yOrder = yOrder;
exports.minimapNearest = minimapNearest;
exports.minimapMajority = minimapMajority;
exports.minimapToTile = minimapToTile;
exports.visibleEntities = visibleEntities;
exports.creditsText = creditsText;
exports.draw = draw;
const C = require("./const");
const F = require("./fixed");
const RS = require("./raster");
const S = require("./spatial");
const T = require("./tmap");
exports.TILES_X = Math.floor(C.VIEW_W / C.TILE) + 1;
exports.TILES_Y = Math.floor(C.VIEW_H / C.TILE) + 1;
exports.EDGE_SPEED = 4;
exports.EDGE_MARGIN = 8;
exports.MAX_CAM_X = C.MAP_W * C.TILE - C.VIEW_W;
exports.MAX_CAM_Y = C.MAP_H * C.TILE - C.VIEW_H;
exports.UI_DARK = 193;
exports.UI_MID = 195;
exports.UI_LIGHT = 197;
exports.UI_TEXT = 198;
exports.UI_HP_GOOD = 201;
exports.UI_HP_BAD = 200;
exports.UI_SELECT = 199;
// ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
// 카메라는 **정수 픽셀**이다. 서브픽셀 스크롤은 도스 시절 흔치 않았고,
// 정수로 두면 타일 그리기가 오프셋 하나로 끝난다.
class View {
    constructor(camX = 0, camY = 0) {
        this.camX = camX;
        this.camY = camY;
    }
    clampTo(m) {
        const mx = m.w * C.TILE - C.VIEW_W;
        const my = m.h * C.TILE - C.VIEW_H;
        if (this.camX < 0)
            this.camX = 0;
        if (this.camY < 0)
            this.camY = 0;
        if (this.camX > mx)
            this.camX = mx;
        if (this.camY > my)
            this.camY = my;
    }
    move(m, dx, dy) {
        this.camX += dx;
        this.camY += dy;
        this.clampTo(m);
    }
    centerOn(m, tx, ty) {
        this.camX = tx * C.TILE - Math.floor(C.VIEW_W / 2);
        this.camY = ty * C.TILE - Math.floor(C.VIEW_H / 2);
        this.clampTo(m);
    }
    // (첫 타일 x, 첫 타일 y, 픽셀 오프셋 x, 오프셋 y).
    firstTile() {
        return [F.floordiv(this.camX, C.TILE), F.floordiv(this.camY, C.TILE),
            F.fmod(this.camX, C.TILE), F.fmod(this.camY, C.TILE)];
    }
}
exports.View = View;
// 마우스가 뷰포트 가장자리 8px 안이면 그 방향으로 4px/틱.
function edgeScroll(mx, my) {
    if (!(mx >= 0 && mx < C.VIEW_W && my >= 0 && my < C.VIEW_H))
        return [0, 0];
    let dx = 0;
    let dy = 0;
    if (mx < exports.EDGE_MARGIN)
        dx = -exports.EDGE_SPEED;
    else if (mx >= C.VIEW_W - exports.EDGE_MARGIN)
        dx = exports.EDGE_SPEED;
    if (my < exports.EDGE_MARGIN)
        dy = -exports.EDGE_SPEED;
    else if (my >= C.VIEW_H - exports.EDGE_MARGIN)
        dy = exports.EDGE_SPEED;
    return [dx, dy];
}
// ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
// 발밑 y · x · 핸들. 키가 전순서라 안정 정렬 여부에 의존하지 않는다.
function sortKey(w, i) {
    const foot = C.FOOT[w.kind[i]];
    return [F.fpFloor(w.py[i]) + foot * C.TILE, F.fpFloor(w.px[i]), w.handle(i)];
}
function keyGt(a, b) {
    if (a[0] !== b[0])
        return a[0] > b[0];
    if (a[1] !== b[1])
        return a[1] > b[1];
    return a[2] > b[2];
}
// 삽입 정렬. 프레임 사이에 목록이 거의 정렬되어 있어 거의 O(n) 이다.
function yOrder(w) {
    const out = [];
    for (let i = 1; i < C.MAX_ENT; i += 1) {
        if (w.alive[i] === 0)
            continue;
        const k = sortKey(w, i);
        let j = out.length;
        while (j > 0 && keyGt(sortKey(w, out[j - 1]), k))
            j -= 1;
        out.splice(j, 0, i);
    }
    return out;
}
// ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
function minimapNearest(m, sx, sy) {
    return m.terrain[F.floordiv(sy * m.h, C.MINI_H) * m.w
        + F.floordiv(sx * m.w, C.MINI_W)];
}
// 블록에서 가장 많이 나온 지형, 동점이면 지형 번호 최소. 128 맵을 대비한다.
function minimapMajority(m, sx, sy) {
    const x0 = F.floordiv(sx * m.w, C.MINI_W);
    let x1 = F.floordiv((sx + 1) * m.w, C.MINI_W);
    const y0 = F.floordiv(sy * m.h, C.MINI_H);
    let y1 = F.floordiv((sy + 1) * m.h, C.MINI_H);
    if (x1 <= x0)
        x1 = x0 + 1;
    if (y1 <= y0)
        y1 = y0 + 1;
    const cnt = new Array(8).fill(0);
    for (let y = y0; y < Math.min(y1, m.h); y += 1) {
        for (let x = x0; x < Math.min(x1, m.w); x += 1) {
            cnt[m.terrain[y * m.w + x]] += 1;
        }
    }
    let best = 0;
    let bn = -1;
    for (let t = 0; t < 8; t += 1) {
        if (cnt[t] > bn) {
            bn = cnt[t];
            best = t;
        }
    }
    return best;
}
function minimapToTile(sx, sy) {
    return [F.floordiv(sx * C.MAP_W, C.MINI_W), F.floordiv(sy * C.MAP_H, C.MINI_H)];
}
// ── 안개가 가리는 것 ────────────────────────────────────────────────────────
// §23.1 — **유닛 숨기기는 명암표가 못 한다.** 보이는 칸의 것만 그린다.
function visibleEntities(sim, p) {
    const out = [];
    for (const i of yOrder(sim.w)) {
        const t = sim.w.ty[i] * sim.m.w + sim.w.tx[i];
        if (sim.fog.visible(p, t))
            out.push(i);
    }
    return out;
}
// 자릿수 고정 — 숫자가 흔들리면 더티 렉트가 커진다.
function creditsText(v0) {
    let v = v0;
    if (v > 99999)
        v = 99999;
    const s = String(v);
    return ' '.repeat(5 - s.length) + s;
}
// ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
function fill(fb, x, y, w, h, v) {
    for (let j = Math.max(0, y); j < Math.min(C.VIEW_H, y + h); j += 1) {
        const row = j * C.SCR_W;
        for (let i = Math.max(0, x); i < Math.min(C.VIEW_W, x + w); i += 1) {
            fb[row + i] = v;
        }
    }
}
function drawTerrain(fb, sim, view, light, p) {
    const m = sim.m;
    const [tx0, ty0, ox, oy] = view.firstTile();
    for (let ty = ty0; ty < Math.min(m.h, ty0 + exports.TILES_Y); ty += 1) {
        for (let tx = tx0; tx < Math.min(m.w, tx0 + exports.TILES_X); tx += 1) {
            const px = (tx - tx0) * C.TILE - ox;
            const py = (ty - ty0) * C.TILE - oy;
            const level = sim.fog.level(p, tx, ty);
            if (level === 0) {
                fill(fb, px, py, C.TILE, C.TILE, 0);
                continue;
            }
            const t = m.terrain[ty * m.w + tx];
            let base = T.MINI_COLOR[t];
            let edge = F.fmod(base, 8) >= 2 ? base - 2 : base + 1;
            if (level < 3) {
                base = light[level][base];
                edge = light[level][edge];
            }
            fill(fb, px, py, C.TILE, C.TILE, base);
            const mask = m.mask(tx, ty); // §4.4 — 다른 지형 쪽만 긋는다
            if (F.bit(mask, 0) === 0)
                fill(fb, px, py, C.TILE, 1, edge);
            if (F.bit(mask, 4) === 0)
                fill(fb, px, py + C.TILE - 1, C.TILE, 1, edge);
            if (F.bit(mask, 6) === 0)
                fill(fb, px, py, 1, C.TILE, edge);
            if (F.bit(mask, 2) === 0)
                fill(fb, px + C.TILE - 1, py, 1, C.TILE, edge);
        }
    }
}
// 체력바와 선택 표시. 뷰포트 안에서만 그린다.
function bars(fb, w, i, x0, y0, spr, selected) {
    const hp = w.hp[i];
    const full = C.HP[w.kind[i]];
    if (full <= 0)
        return;
    const wdt = spr.w - 2;
    const fillN = F.floordiv(wdt * hp, full);
    const y = y0 - 2;
    if (y >= 0 && y < C.VIEW_H) {
        for (let k = 0; k < wdt; k += 1) {
            const x = x0 + 1 + k;
            if (x >= 0 && x < C.VIEW_W) {
                fb[y * C.SCR_W + x] = k < fillN ? exports.UI_HP_GOOD : exports.UI_HP_BAD;
            }
        }
    }
    if (selected) {
        for (let k = 0; k < spr.w; k += 1) {
            const x = x0 + k;
            for (const yy of [y0, y0 + spr.h - 1]) {
                if (x >= 0 && x < C.VIEW_W && yy >= 0 && yy < C.VIEW_H) {
                    fb[yy * C.SCR_W + x] = exports.UI_SELECT;
                }
            }
        }
    }
}
function drawEntities(fb, sim, view, _light, p, selection) {
    const w = sim.w;
    const sel = new Set(selection);
    for (const i of visibleEntities(sim, p)) {
        const [spr, flip] = RS.spriteFor(w.kind[i], w.dir[i]);
        if (spr === null)
            continue;
        const sx = F.fpFloor(w.px[i]) - view.camX;
        const sy = F.fpFloor(w.py[i]) - view.camY;
        const anchorX = sx + F.floordiv(C.TILE * C.FOOT[w.kind[i]], 2);
        const anchorY = sy + C.TILE * C.FOOT[w.kind[i]] - 2;
        RS.blit(fb, spr, anchorX, anchorY, w.owner[i], flip);
        bars(fb, w, i, anchorX - spr.ox, anchorY - spr.oy, spr, sel.has(w.handle(i)));
    }
}
function drawProjectiles(fb, sim, view) {
    for (let k = 0; k < sim.pj.n(); k += 1) {
        const x = F.fpFloor(sim.pj.x[k]) - view.camX;
        const y = F.fpFloor(sim.pj.y[k]) - view.camY;
        if (x >= 0 && x < C.VIEW_W && y >= 0 && y < C.VIEW_H) {
            fb[y * C.SCR_W + x] = exports.UI_TEXT;
        }
    }
}
function drawPanel(fb, sim, p, selection) {
    const m = sim.m;
    for (let y = 0; y < C.SCR_H; y += 1) {
        const row = y * C.SCR_W;
        for (let x = C.PANEL_X; x < C.SCR_W; x += 1)
            fb[row + x] = exports.UI_DARK;
    }
    for (let sy = 0; sy < C.MINI_H; sy += 1) { // 미니맵 — 한 타일이 한 픽셀
        const row = (C.MINI_Y + sy) * C.SCR_W;
        for (let sx = 0; sx < C.MINI_W; sx += 1) {
            const [tx, ty] = minimapToTile(sx, sy);
            const level = sim.fog.level(p, tx, ty);
            if (level === 0)
                fb[row + C.MINI_X + sx] = 0;
            else
                fb[row + C.MINI_X + sx] = T.MINI_COLOR[minimapNearest(m, sx, sy)];
        }
    }
    for (let i = 1; i < C.MAX_ENT; i += 1) { // 미니맵 위의 유닛
        if (sim.w.alive[i] === 0)
            continue;
        const t = sim.w.ty[i] * m.w + sim.w.tx[i];
        if (!sim.fog.visible(p, t))
            continue;
        const sx = F.floordiv(sim.w.tx[i] * C.MINI_W, m.w);
        const sy = F.floordiv(sim.w.ty[i] * C.MINI_H, m.h);
        fb[(C.MINI_Y + sy) * C.SCR_W + C.MINI_X + sx] =
            RS.PLAYER_BASE + sim.w.owner[i] * 8 + 5;
    }
    RS.text(fb, 'SEL', C.PANEL_X + 2, C.MINI_H + 4, exports.UI_TEXT);
    if (selection.length > 0) {
        const h = selection[0];
        if (sim.w.valid(h)) {
            const j = S.index(h);
            RS.text(fb, C.NAME[sim.w.kind[j]].slice(0, 1).toUpperCase()
                + String(sim.w.kind[j]), C.PANEL_X + 2, C.MINI_H + 14, exports.UI_TEXT);
            RS.text(fb, creditsText(sim.w.hp[j]), C.PANEL_X + 2, C.MINI_H + 24, exports.UI_HP_GOOD);
        }
    }
}
function drawBottom(fb, sim, p, message) {
    for (let y = C.BAR_Y; y < C.SCR_H; y += 1) {
        const row = y * C.SCR_W;
        for (let x = 0; x < C.PANEL_X; x += 1)
            fb[row + x] = exports.UI_MID;
    }
    RS.text(fb, 'CREDITS' + creditsText(sim.ec.credits[p]), 4, C.BAR_Y + 2, exports.UI_TEXT);
    RS.text(fb, 'POP' + creditsText(sim.ec.supplyUsed[p]) + '/'
        + creditsText(sim.ec.supplyCap[p]), 4, C.BAR_Y + 12, exports.UI_TEXT);
    if (message !== '') {
        RS.text(fb, message.slice(0, 24), 130, C.BAR_Y + 12, exports.UI_LIGHT);
    }
}
// §23.1 의 여덟 층을 순서대로. 팔레트 위상은 그림을 바꾸지 않는다.
function draw(fb, sim, view, _phase, _pal, light, p, selection, message) {
    drawTerrain(fb, sim, view, light, p);
    drawEntities(fb, sim, view, light, p, selection);
    drawProjectiles(fb, sim, view);
    drawPanel(fb, sim, p, selection);
    drawBottom(fb, sim, p, message);
}
  });
  __def('web/data', function (exports, require, module, __dirname) {
"use strict";
// 골든 데이터 — **생성물이다. 손으로 고치지 말 것.**
//
// tools/gen_webdata.py 가 golden/ 에서 만든다. 브라우저에는 fs 가 없으므로
// 엔진이 파일에서 읽던 것(시작 맵·시나리오 스크립트·경로탐색 시험 맵)을
// 문자열로 들고 있는다. 팔레트와 스프라이트는 여기 없다 — raster.buildPalette()
// 와 raster.SPRITES 가 절차적으로 만들기 때문이다(§22.2·§22.7).
Object.defineProperty(exports, "__esModule", { value: true });
exports.MAPS_TXT = exports.SCRIPT_TXT = exports.MAP_START_TXT = void 0;
// golden/map_start.txt — 64x64 · 2인 시작 위치. 시나리오와
// 미니 RTS 데모가 같은 맵을 쓴다.
exports.MAP_START_TXT = [
    "RTSMAP 1",
    "name 시작 맵",
    "size 64 64",
    "terrain",
    "~~~~~~~~~~~................,,,,,,,,,,,,,,,,,,,,,,,^,,,**^,,,,^^^",
    "~~~~~~~~~~................,,,,,,,,,,,,,,,,,,,,,,,,,,,***^^,,^^^,",
    "~~~~~~~~~~~...............,,,,,,,,,,,,,,,,,,,,,,,,,,,,*^^^^^^,,^",
    "~~~~~~~~~~~..........*....,,,,,,,,,,,,,,,,,,,,*,,,,,,^^^^^^^^^,,",
    "~~~~~~~~~~~*........***..,,,,,,,,,,,,,,,,,,,,***,,,,,^^^^^^,,,^^",
    "~~~~~~~~~~***......*****.,,,,,,,,,,,,,,,,,,,*****,,,^^^^^^^^^^,,",
    "~~~~~~,,,,,***.,,...***..,,,,,,,,,,,^,^,,,,,,***,,,^^^^^^^^^^^^^",
    "~~~~~~,,,,,**..,,,,,.*..,,,,,,,,,,,,^,,^,,,,,,*,,,,^^^^^^^^^^^^^",
    "~~~~~~,,,,,*..,,,,,,,..,,,,,,,,,,,,,^,,^^,,,,,,,^,^^^^^^^^^^^^^^",
    "~~~~..,,,,,...,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^^^^",
    "......,,,,,.,.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^^^^",
    "............,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^^^^^",
    "............,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^#####^###",
    ",,,,.,.....,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,*,,,^^^^^^#########",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,***,,,^^^^##########",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,*,,,,,,*****,,^^^^##########",
    ",,,,,,,,,,,,,,*,,,,,,,,,,,,,,,,,,,,***,,,,,,***,,,^^^^##########",
    ",,,,,,,,,,,,,***,,,,,,,,,*,,,,,,,,*****,,,,,,*,,,^^^^^##########",
    ",*,,,,,,,,,,*****,,,,,,,***,,,,,,,,***,,,,,,,,,,,,^^^^^#########",
    "***,,,,,,,,,,***,,,,,,,*****,,,,,,,,*,,,,,,,,,,,,,^^^^##^#######",
    "****,,,,,,,,,,*,,,,,,,,,***,,,,,,,,,,,,,,,,,,,,,^,^^^^^^^#######",
    "***,,,,,,,,,,,,,,,,,,,,,,*,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^#######",
    ",*,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^######",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^######",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^######",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^^#####",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,.,,,,,,,,,,,,,,,,,,,,^^^^^^^^^^^######",
    ",,,,,,,,,,,,,,,,,,,,,,,,,,.*,..,,,,,,,,,*,,,,^^^^^^^^^^^########",
    ",,,,,,,,,,,,,,,,,,,,,,,,,.***.....,,,,,***,,,^^^^^^^^^^^^^^#####",
    ",,,,,,,,,*,,,,,,,,,,,,,,,*****......,,*****,^^^^^^^^^^^^########",
    ",,,,,,,,***,,,,,,,,,,,,,..***........,,***,,^^^^^^^^^^^#########",
    ",,,,,,,*****,,,,,,,,,,.....*~~.......,,,*,,,,^^^^^^^^^^#########",
    "#########^^^^^^^^^^,,,,*,,,.......~~*.....,,,,,,,,,,*****,,,,,,,",
    "#########^^^^^^^^^^^,,***,,........***..,,,,,,,,,,,,,***,,,,,,,,",
    "########^^^^^^^^^^^^,*****,,......*****,,,,,,,,,,,,,,,*,,,,,,,,,",
    "#####^^^^^^^^^^^^^^,,,***,,,,,.....***.,,,,,,,,,,,,,,,,,,,,,,,,,",
    "########^^^^^^^^^^^,,,,*,,,,,,,,,..,*.,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "######^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,.,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "#####^^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "######^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "######^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "######^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,*,",
    "#######^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,*,,,,,,,,,,,,,,,,,,,,,,***",
    "#######^^^^^^^,^,,,,,,,,,,,,,,,,,,,,,***,,,,,,,,,*,,,,,,,,,,****",
    "#######^##^^^^,,,,,,,,,,,,,*,,,,,,,,*****,,,,,,,***,,,,,,,,,,***",
    "#########^^^^^,,,,,,,,,,,,***,,,,,,,,***,,,,,,,*****,,,,,,,,,,*,",
    "##########^^^^^,,,*,,,,,,*****,,,,,,,,*,,,,,,,,,***,,,,,,,,,,,,,",
    "##########^^^^,,,***,,,,,,***,,,,,,,,,,,,,,,,,,,,*,,,,,,,,,,,,,,",
    "##########^^^^,,*****,,,,,,*,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "##########^^^^,,,***,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
    "#########^^^^^^,,,*,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,.....,.,,,,",
    "###^#####^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,............",
    "^^^^^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,............",
    "^^^^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,.,.,,,,,......",
    "^^^^^^^^^^^^^^,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,...,,,,,..~~~~",
    "^^^^^^^^^^^^^^,^,,,,,,,^^,,^,,,,,,,,,,,,,..,,,,,,,..*,,,,,~~~~~~",
    "^^^^^^^^^^^^^,,,,*,,,,,,^,,^,,,,,,,,,,,,..*.,,,,,..**,,,,,~~~~~~",
    "^^^^^^^^^^^^^,,,***,,,,,,^,^,,,,,,,,,,,..***...,,.***,,,,,~~~~~~",
    ",,^^^^^^^^^^,,,*****,,,,,,,,,,,,,,,,,,,.*****......***~~~~~~~~~~",
    "^^,,,^^^^^^,,,,,***,,,,,,,,,,,,,,,,,,,,..***........*~~~~~~~~~~~",
    ",,^^^^^^^^^,,,,,,*,,,,,,,,,,,,,,,,,,,,....*..........~~~~~~~~~~~",
    "^,,^^^^^^*,,,,,,,,,,,,,,,,,,,,,,,,,,,,...............~~~~~~~~~~~",
    ",^^^,,^^***,,,,,,,,,,,,,,,,,,,,,,,,,,,................~~~~~~~~~~",
    "^^^,,,,^**,,,^,,,,,,,,,,,,,,,,,,,,,,,................~~~~~~~~~~~",
    "start 2",
    "8 8",
    "55 55",
    "seed 3",
    "retries 0",
    "ore 12 55",
    "",
].join('\n');
// golden/script.txt — §18.6 시나리오. 트레이스를 만드는 입력이다.
exports.SCRIPT_TXT = [
    "RTSS 1",
    "ticks 1200",
    "players 2",
    "# 틱 플레이어 선택자 명령 a b c   (SPEC §18.6)",
    "1 0 K4 HARVEST 0 0 0",
    "4 0 K10 BUILD 12 5 9",
    "8 0 K10 BUILD 11 8 10",
    "12 0 K10 TRAIN 4 0 0",
    "29 0 K10 BUILD 12 5 9",
    "33 0 K10 BUILD 11 8 10",
    "46 1 K4 HARVEST 0 0 0",
    "49 1 K10 BUILD 12 57 53",
    "53 1 K10 BUILD 11 54 52",
    "54 0 K10 BUILD 12 5 9",
    "57 1 K10 TRAIN 4 0 0",
    "58 0 K10 BUILD 11 8 10",
    "74 1 K10 BUILD 12 57 53",
    "78 1 K10 BUILD 11 54 52",
    "79 0 K10 BUILD 12 5 9",
    "83 0 K10 BUILD 11 8 10",
    "99 1 K10 BUILD 12 57 53",
    "103 1 K10 BUILD 11 54 52",
    "104 0 K10 BUILD 12 5 9",
    "108 0 K10 BUILD 11 8 10",
    "110 0 N HARVEST 0 0 0",
    "115 0 K10 TRAIN 4 0 0",
    "124 1 K10 BUILD 12 57 53",
    "128 1 K10 BUILD 11 54 52",
    "149 1 K10 BUILD 12 57 53",
    "153 1 K10 BUILD 11 54 52",
    "155 1 N HARVEST 0 0 0",
    "160 1 K10 TRAIN 4 0 0",
    "215 0 K12 TRAIN 1 0 0",
    "215 0 N HARVEST 0 0 0",
    "220 0 K10 BUILD 14 11 9",
    "245 0 K10 BUILD 14 11 9",
    "260 1 K12 TRAIN 1 0 0",
    "260 1 N HARVEST 0 0 0",
    "265 1 K10 BUILD 14 51 53",
    "270 0 K10 BUILD 14 11 9",
    "280 0 K12 TRAIN 0 0 0",
    "290 1 K10 BUILD 14 51 53",
    "295 0 K10 BUILD 14 11 9",
    "315 1 K10 BUILD 14 51 53",
    "320 0 K10 BUILD 14 11 9",
    "325 1 K12 TRAIN 0 0 0",
    "340 1 K10 BUILD 14 51 53",
    "345 0 K12 TRAIN 0 0 0",
    "365 1 K10 BUILD 14 51 53",
    "390 1 K12 TRAIN 0 0 0",
    "410 0 K12 TRAIN 1 0 0",
    "455 1 K12 TRAIN 1 0 0",
    "475 0 K12 TRAIN 0 0 0",
    "480 0 F MOVE 14 14 0",
    "520 0 K10 BUILD 13 11 11",
    "520 1 K12 TRAIN 0 0 0",
    "525 1 F MOVE 49 49 0",
    "540 0 F AMOVE 55 55 0",
    "540 0 K12 TRAIN 0 0 0",
    "545 0 K10 BUILD 13 11 11",
    "565 1 K10 BUILD 13 50 50",
    "570 0 K10 BUILD 13 11 11",
    "585 1 F AMOVE 8 8 0",
    "585 1 K12 TRAIN 0 0 0",
    "590 1 K10 BUILD 13 50 50",
    "595 0 K10 BUILD 13 11 11",
    "605 0 K12 TRAIN 1 0 0",
    "615 1 K10 BUILD 13 50 50",
    "620 0 K10 BUILD 13 11 11",
    "640 1 K10 BUILD 13 50 50",
    "650 1 K12 TRAIN 1 0 0",
    "665 1 K10 BUILD 13 50 50",
    "670 0 K12 TRAIN 0 0 0",
    "715 1 K12 TRAIN 0 0 0",
    "900 0 F AMOVE 55 55 0",
    "900 0 K13 TRAIN 2 0 0",
    "945 1 F AMOVE 8 8 0",
    "945 1 K13 TRAIN 2 0 0",
    "",
].join('\n');
// golden/map_1..6.txt — §8 경로탐색 시험 맵 여섯. 각 맵의 pairs 는
// prim.txt 가 쓰는 것과 같은 출발·도착 쌍이다.
exports.MAPS_TXT = [
    [
        "RTSMAP 1",
        "name 빈 들판",
        "size 32 32",
        "map",
        "################################",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "################################",
        "pairs 4",
        "19 14 23 18",
        "6 15 4 25",
        "12 26 25 9",
        "14 21 15 24",
        "",
    ].join('\n'),
    [
        "RTSMAP 1",
        "name 벽과 문",
        "size 32 32",
        "map",
        "################################",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#..............................#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "#...............#..............#",
        "################################",
        "pairs 4",
        "1 29 27 23",
        "13 15 6 15",
        "3 22 24 16",
        "1 11 25 20",
        "",
    ].join('\n'),
    [
        "RTSMAP 1",
        "name 빗살 미로",
        "size 32 32",
        "map",
        "################################",
        "#.......#.......#.......#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#...#...#...#...#...#......#",
        "#...#.......#.......#..........#",
        "################################",
        "pairs 4",
        "28 30 13 1",
        "11 6 6 29",
        "15 2 11 30",
        "25 27 19 24",
        "",
    ].join('\n'),
    [
        "RTSMAP 1",
        "name 방과 문",
        "size 32 32",
        "map",
        "################################",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#..............................#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#####.##########.##########.####",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#..............................#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#####.##########.##########.####",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#..............................#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "#.........#..........#.........#",
        "################################",
        "pairs 4",
        "8 3 27 13",
        "1 12 28 22",
        "28 11 17 3",
        "16 14 28 5",
        "",
    ].join('\n'),
    [
        "RTSMAP 1",
        "name 닿을 수 없는 섬",
        "size 32 32",
        "map",
        "################################",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#.....................########.#",
        "#.....................#......#.#",
        "#.....................#......#.#",
        "#.....................#......#.#",
        "#.....................#......#.#",
        "#.....................#......#.#",
        "#.....................#......#.#",
        "#.....................########.#",
        "#..............................#",
        "################################",
        "pairs 4",
        "1 1 25 25",
        "28 6 27 30",
        "21 13 27 14",
        "17 23 18 22",
        "",
    ].join('\n'),
    [
        "RTSMAP 1",
        "name 동굴",
        "size 32 32",
        "map",
        "################################",
        "##........#########..#####.....#",
        "#..........##...##......#......#",
        "#..............................#",
        "#......#......................##",
        "#.....##......................##",
        "#.............................##",
        "##.............................#",
        "##.....................#.......#",
        "##.....................#.......#",
        "##.............................#",
        "###............................#",
        "###............................#",
        "###...........................##",
        "##..................###...######",
        "#...................###...######",
        "#..................###....######",
        "##................###.......####",
        "#####.............###........###",
        "######........................##",
        "######.........................#",
        "######.......###...............#",
        "#..###.......###...............#",
        "#...#.........###..............#",
        "#.............###..............#",
        "#............####..............#",
        "#.........#######..............#",
        "#.........#######......##......#",
        "#.........########....##########",
        "#........##########..###########",
        "##......########################",
        "################################",
        "pairs 4",
        "12 16 7 14",
        "30 1 13 17",
        "11 24 25 5",
        "7 6 25 5",
        "",
    ].join('\n'),
];
  });
  __def('web/canvas', function (exports, require, module, __dirname) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Screen = exports.H = exports.W = void 0;
exports.paletteLut = paletteLut;
// 320×200 인덱스 프레임버퍼를 캔버스에 올린다 — 그리기는 하지 않는다.
//
// 엔진의 render.draw() 는 팔레트 번호 하나가 든 320×200 배열을 채운다. 브라우저는
// 그 배열을 화면에 못 올리므로 여기서 RGBA 로 편다. 그 이상은 하지 않는다.
// 선 하나라도 여기서 그리기 시작하면 "화면에 보이는 것 = 엔진이 그린 것" 이라는
// 이 덱의 유일한 주장이 무너진다.
//
// 팔레트 값은 0…63 (VGA DAC) 이므로 raster.expand() 로 0…255 로 편다. 세 언어의
// PPM 출력이 쓰는 것과 같은 함수다 — 브라우저 화면과 out/frame_*.ppm 이 같은 색이다.
const C = require("../const");
const RS = require("../raster");
exports.W = C.SCR_W;
exports.H = C.SCR_H;
// 팔레트 → RGBA 룩업 1024바이트. 색 하나당 네 칸(R,G,B,A)이다.
function paletteLut(pal) {
    const lut = new Uint8ClampedArray(256 * 4);
    for (let i = 0; i < 256; i += 1) {
        const c = i < pal.length ? pal[i] : [0, 0, 0];
        lut[i * 4] = RS.expand(c[0]);
        lut[i * 4 + 1] = RS.expand(c[1]);
        lut[i * 4 + 2] = RS.expand(c[2]);
        lut[i * 4 + 3] = 255;
    }
    return lut;
}
// 320×200 을 정수배로 키워 보여 준다. 확대는 캔버스가 하고(보간 끔),
// 우리는 등배 ImageData 하나만 유지한다 — 프레임마다 새로 만들지 않는다.
class Screen {
    constructor(scale = 2, w = exports.W, h = exports.H) {
        this.w = w;
        this.h = h;
        this.canvas = document.createElement('canvas');
        this.canvas.width = w * scale;
        this.canvas.height = h * scale;
        this.canvas.style.width = '100%';
        this.canvas.style.maxWidth = w * scale + 'px';
        this.canvas.style.display = 'block';
        this.canvas.style.imageRendering = 'pixelated';
        this.canvas.style.background = '#000';
        this.canvas.style.borderRadius = '6px';
        this.canvas.style.touchAction = 'none';
        this.ctx = this.canvas.getContext('2d');
        this.back = document.createElement('canvas');
        this.back.width = w;
        this.back.height = h;
        this.bctx = this.back.getContext('2d');
        this.img = this.bctx.createImageData(w, h);
        this.lut = paletteLut(RS.buildPalette());
    }
    // 물 색 순환(§22.3)처럼 팔레트만 바뀌는 경우를 위해 따로 둔다.
    setPalette(pal) {
        this.lut = paletteLut(pal);
    }
    // 인덱스 배열 → 화면. 할당이 없다 — 애니메이션 루프 안에서 매 프레임 불린다.
    paint(fb) {
        const d = this.img.data;
        const lut = this.lut;
        const n = this.w * this.h;
        for (let i = 0; i < n; i += 1) {
            const s = fb[i] * 4;
            const t = i * 4;
            d[t] = lut[s];
            d[t + 1] = lut[s + 1];
            d[t + 2] = lut[s + 2];
            d[t + 3] = 255;
        }
        this.bctx.putImageData(this.img, 0, 0);
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.drawImage(this.back, 0, 0, this.canvas.width, this.canvas.height);
    }
    // 마우스 이벤트 → 320×200 좌표. CSS 로 늘어난 만큼 되돌린다.
    // 화면 밖이면 붙잡지 않고 그대로 돌려준다 — 판정은 부르는 쪽(select.inView)이 한다.
    eventPos(e) {
        const r = this.canvas.getBoundingClientRect();
        const sx = r.width > 0 ? this.w / r.width : 1;
        const sy = r.height > 0 ? this.h / r.height : 1;
        return [Math.floor((e.clientX - r.left) * sx),
            Math.floor((e.clientY - r.top) * sy)];
    }
}
exports.Screen = Screen;
  });
  __def('web/minirts', function (exports, require, module, __dirname) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MiniRts = void 0;
exports.boot = boot;
// 미니 RTS — 덱 안에서 실제로 해 볼 수 있는 판.
//
// 이 파일에는 규칙이 없다. 규칙은 전부 sim.Sim 안에 있고, 여기는 사람의 손짓을
// **명령 여섯 칸**(§18.1)으로 바꿔 sim.step() 에 넣는 껍데기다. 상태를 직접
// 건드리는 줄이 하나라도 생기면 이 판은 골든 트레이스를 만든 그 엔진이 아니게 된다 —
// 그래서 여기에는 w.hp[i] = … 같은 대입이 없다. 있으면 그것이 버그다.
//
// 그리기도 마찬가지다. render.draw() 가 320×200 인덱스 배열을 채우고, canvas.ts 가
// 그것을 편다. 이 파일이 캔버스에 긋는 선은 없다.
const C = require("../const");
const RS = require("../raster");
const RD = require("../render");
const SEL = require("../select");
const SIM = require("../sim");
const S = require("../spatial");
const T = require("../tmap");
const canvas_1 = require("./canvas");
const data_1 = require("./data");
const ME = 0; // 사람이 잡는 진영
const FOE = 1;
// 지을 수 있는 것과 뽑을 수 있는 것. 순서가 단추 순서다.
const BUILDS = [C.REF, C.BARR, C.POW, C.FACT, C.TOWER];
const TRAINS = [C.HARV, C.INF, C.ARCHER, C.TANK, C.MORTAR];
// 유닛 종류 → 그것을 뽑는 건물. §25.3 의 선행과는 다른 표다 —
// 선행은 "지을 수 있는가", 이것은 "누가 큐를 갖는가".
const TRAINER = [];
for (let k = 0; k < C.KIND_COUNT; k += 1)
    TRAINER.push(-1);
TRAINER[C.HARV] = C.HQ;
TRAINER[C.INF] = C.BARR;
TRAINER[C.ARCHER] = C.BARR;
TRAINER[C.TANK] = C.FACT;
TRAINER[C.MORTAR] = C.FACT;
// §18.1 의 사전식 순서. sim.step 이 정렬을 검사하고 어긋나면 던진다.
function cmpOrder(a, b) {
    for (let i = 0; i < a.length && i < b.length; i += 1) {
        if (a[i] !== b[i])
            return a[i] < b[i] ? -1 : 1;
    }
    return a.length - b.length;
}
function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls !== undefined)
        e.className = cls;
    if (text !== undefined)
        e.textContent = text;
    return e;
}
class MiniRts {
    constructor(host, api) {
        const m = T.TMap.loadText(data_1.MAP_START_TXT);
        this.sim = new SIM.Sim(m, 1, 2);
        this.sim.setupStart(true); // 두 진영 모두 AI 로 세우고
        this.sim.aiEnabled[ME] = false; // 내 쪽만 손으로 잡는다
        this.view = new RD.View();
        this.view.centerOn(m, m.starts[ME][0], m.starts[ME][1]);
        this.pal = RS.buildPalette();
        this.light = RS.buildLight(this.pal);
        this.fb = new Array(C.SCR_W * C.SCR_H).fill(0);
        this.screen = new canvas_1.Screen(2);
        this.pending = [];
        this.sel = [];
        this.buildKind = -1;
        this.drag = null;
        this.mouse = [0, 0];
        this.message = '';
        this.running = true;
        this.acc = 0;
        this.last = 0;
        this.raf = 0;
        this.phase = 0;
        const out = api.out(host) || host;
        out.innerHTML = '';
        const wrap = el('div');
        wrap.style.display = 'flex';
        wrap.style.flexDirection = 'column';
        wrap.style.gap = '6px';
        wrap.appendChild(this.screen.canvas);
        this.bar = el('div', 'row');
        this.status = el('div');
        this.status.style.fontSize = '.8rem';
        this.status.style.lineHeight = '1.5';
        wrap.appendChild(this.bar);
        wrap.appendChild(this.status);
        out.appendChild(wrap);
        this.buildBar();
        this.wire();
        this.draw();
        this.tickLoop = this.tickLoop.bind(this);
        this.raf = requestAnimationFrame(this.tickLoop);
    }
    // ── 단추 ──────────────────────────────────────────────────────────────────
    buildBar() {
        const mk = (label, fn) => {
            const b = el('button', 'sec', label);
            b.addEventListener('click', (e) => { e.preventDefault(); fn(); });
            this.bar.appendChild(b);
        };
        for (const k of BUILDS) {
            mk('건설 ' + C.NAME[k] + ' ' + C.COST[k], () => {
                this.buildKind = this.buildKind === k ? -1 : k;
                this.say(this.buildKind < 0 ? '건설 취소'
                    : C.NAME[k] + ' — 놓을 자리를 누르세요');
            });
        }
        for (const k of TRAINS) {
            mk('생산 ' + C.NAME[k] + ' ' + C.COST[k], () => this.train(k));
        }
        mk('정지', () => this.orderSelection(SEL.STOP, 0, 0, 0));
        mk('일시정지', () => {
            this.running = !this.running;
            this.say(this.running ? '진행' : '멈춤');
        });
    }
    // ── 명령 ──────────────────────────────────────────────────────────────────
    // 모든 상태 변화가 지나는 유일한 문. §12.5 — UI 는 시뮬을 직접 만지지 않는다.
    push(o) {
        this.pending.push(o);
    }
    orderSelection(kind, a, b, c) {
        for (const h of this.sel) {
            if (this.sim.w.valid(h))
                this.push([ME, h, kind, a, b, c]);
        }
    }
    // 내 건물 중 조건에 맞는 첫 핸들. 없으면 0.
    myBuilding(kind) {
        const w = this.sim.w;
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 1 && w.owner[i] === ME && w.kind[i] === kind
                && w.hp[i] > 0)
                return w.handle(i);
        }
        return 0;
    }
    train(kind) {
        const need = TRAINER[kind];
        // 고른 것 중에 생산 건물이 있으면 그것이 뽑는다. 없으면 아무 것이나 찾는다.
        let issuer = 0;
        for (const h of this.sel) {
            if (this.sim.w.valid(h)
                && this.sim.w.kind[S.index(h)] === need) {
                issuer = h;
                break;
            }
        }
        if (issuer === 0)
            issuer = this.myBuilding(need);
        if (issuer === 0) {
            this.say(C.NAME[need] + ' 이(가) 없습니다');
            return;
        }
        if (!this.sim.ec.canBuild(this.sim.w, ME, kind)) {
            this.say(C.NAME[kind] + ' 은(는) 선행이 모자랍니다');
            return;
        }
        this.push([ME, issuer, SEL.TRAIN, kind, 0, 0]);
        this.say(C.NAME[kind] + ' 을(를) 큐에 넣었습니다');
    }
    place(tx, ty) {
        const k = this.buildKind;
        const issuer = this.myBuilding(C.HQ) || this.myBuilding(C.BARR);
        if (issuer === 0) {
            this.say('명령을 낼 건물이 없습니다');
            return;
        }
        this.push([ME, issuer, SEL.BUILD, k, tx, ty]);
        this.buildKind = -1;
        this.say(C.NAME[k] + ' 건설 명령');
    }
    // ── 입력 ──────────────────────────────────────────────────────────────────
    wire() {
        const cv = this.screen.canvas;
        cv.addEventListener('contextmenu', (e) => e.preventDefault());
        cv.addEventListener('mousedown', (e) => this.onDown(e));
        cv.addEventListener('mousemove', (e) => this.onMove(e));
        cv.addEventListener('mouseup', (e) => this.onUp(e));
        cv.addEventListener('mouseleave', () => { this.drag = null; });
        cv.tabIndex = 0;
        cv.addEventListener('keydown', (e) => this.onKey(e));
    }
    onKey(e) {
        const step = 16;
        let dx = 0;
        let dy = 0;
        if (e.key === 'ArrowLeft')
            dx = -step;
        else if (e.key === 'ArrowRight')
            dx = step;
        else if (e.key === 'ArrowUp')
            dy = -step;
        else if (e.key === 'ArrowDown')
            dy = step;
        else if (e.key === 'Escape') {
            this.buildKind = -1;
            this.sel = [];
        }
        else
            return;
        // 덱이 슬라이드를 넘겨 버리면 판이 사라진다.
        e.preventDefault();
        if (dx !== 0 || dy !== 0)
            this.view.move(this.sim.m, dx, dy);
        this.draw();
    }
    onDown(e) {
        const [sx, sy] = this.screen.eventPos(e);
        this.mouse = [sx, sy];
        this.screen.canvas.focus();
        if (e.button === 2) {
            this.context(sx, sy);
            return;
        }
        if (sx >= C.MINI_X && sy < C.MINI_H) { // 미니맵 클릭 — 카메라만
            const [tx, ty] = RD.minimapToTile(sx - C.MINI_X, sy - C.MINI_Y);
            this.view.centerOn(this.sim.m, tx, ty);
            this.draw();
            return;
        }
        if (!SEL.inView(sx, sy))
            return;
        if (this.buildKind >= 0) {
            const cam = [this.view.camX, this.view.camY];
            const [wx, wy] = SEL.screenToWorld(cam, sx, sy);
            this.place(Math.floor(wx / C.TILE), Math.floor(wy / C.TILE));
            return;
        }
        this.drag = [sx, sy];
    }
    onMove(e) {
        const [sx, sy] = this.screen.eventPos(e);
        this.mouse = [sx, sy];
    }
    onUp(e) {
        if (e.button === 2 || this.drag === null)
            return;
        const [sx, sy] = this.screen.eventPos(e);
        const [ax, ay] = this.drag;
        this.drag = null;
        const cam = [this.view.camX, this.view.camY];
        if (Math.abs(sx - ax) < 3 && Math.abs(sy - ay) < 3) {
            const h = SEL.pick(this.sim.w, cam, sx, sy);
            // 남의 것을 집으면 고르지 않는다 — 정보는 화면이 이미 보여 준다.
            this.sel = (h !== 0 && this.sim.w.owner[S.index(h)] === ME) ? [h] : [];
        }
        else {
            this.sel = SEL.boxSelect(this.sim.w, ME, cam, ax, ay, sx, sy);
        }
        this.say(this.sel.length === 0 ? '선택 없음'
            : this.sel.length + '기 선택');
        this.draw();
    }
    // 우클릭 한 번의 뜻은 select.contextOrder 가 정한다 — 여기서 다시 정하지 않는다.
    context(sx, sy) {
        if (!SEL.inView(sx, sy) || this.sel.length === 0)
            return;
        const cam = [this.view.camX, this.view.camY];
        const [wx, wy] = SEL.screenToWorld(cam, sx, sy);
        const tx = Math.floor(wx / C.TILE);
        const ty = Math.floor(wy / C.TILE);
        const h = SEL.pick(this.sim.w, cam, sx, sy);
        const kind = SEL.contextOrder(this.sim.w, this.sim.ec, this.sim.m, ME, tx, ty, h);
        for (const s of this.sel) {
            if (!this.sim.w.valid(s))
                continue;
            if (kind === SEL.ATTACK)
                this.push([ME, s, kind, 0, 0, h]);
            else
                this.push([ME, s, kind, tx, ty, 0]);
        }
        const names = ['이동', '공격', '공격이동', '채집', '건설', '정지', '대기',
            '생산'];
        this.say('우클릭 → ' + names[kind]);
    }
    // ── 루프 ──────────────────────────────────────────────────────────────────
    // 18.2065 Hz(§3.2). 프레임이 밀려도 한 번에 세 틱까지만 따라잡는다 —
    // 탭을 다시 열었을 때 몇 백 틱을 몰아 도는 것을 막는다.
    tickLoop(now) {
        this.raf = requestAnimationFrame(this.tickLoop);
        if (this.last === 0)
            this.last = now;
        const dt = now - this.last;
        this.last = now;
        if (!this.running || this.sim.winner >= 0)
            return;
        if (this.screen.canvas.offsetParent === null)
            return; // 안 보이는 슬라이드
        this.acc += dt;
        const per = C.TICK_US / 1000;
        let n = 0;
        while (this.acc >= per && n < 3) {
            this.acc -= per;
            n += 1;
            this.stepOnce();
        }
        if (n > 0)
            this.draw();
    }
    stepOnce() {
        const [dx, dy] = RD.edgeScroll(this.mouse[0], this.mouse[1]);
        if (dx !== 0 || dy !== 0)
            this.view.move(this.sim.m, dx, dy);
        const orders = this.pending;
        this.pending = [];
        orders.sort(cmpOrder);
        this.sim.step(orders);
        this.sel = this.sel.filter((h) => this.sim.w.valid(h));
        this.phase = (this.phase + 1) % RS.WATER_N;
    }
    say(s) {
        this.message = s;
    }
    // 화면 = 엔진이 그린 것. 여기서 더 그리는 것은 없다.
    draw() {
        this.screen.setPalette(RS.cycleWater(this.pal, this.phase));
        RD.draw(this.fb, this.sim, this.view, this.phase, this.pal, this.light, ME, this.sel, this.message);
        this.screen.paint(this.fb);
        this.status.textContent = this.statusText();
    }
    statusText() {
        const ec = this.sim.ec;
        const mine = this.count(ME);
        const foe = this.count(FOE);
        let head = '틱 ' + this.sim.tick + ' · 크레딧 ' + ec.credits[ME]
            + ' · 인구 ' + ec.supplyUsed[ME] + '/' + ec.supplyCap[ME]
            + ' · 내 것 ' + mine + '기 · 적 ' + foe + '기';
        if (this.sim.winner === ME)
            head = '★ 승리 — ' + head;
        else if (this.sim.winner >= 0)
            head = '패배 — ' + head;
        return head + '\n왼쪽 끌기로 선택 · 오른쪽 클릭이 문맥 명령(이동·공격·채집)'
            + ' · 화살표로 스크롤 · 적 건물을 전부 부수면 이깁니다';
    }
    count(p) {
        const w = this.sim.w;
        let n = 0;
        for (let i = 1; i < C.MAX_ENT; i += 1) {
            if (w.alive[i] === 1 && w.owner[i] === p)
                n += 1;
        }
        return n;
    }
    stop() {
        if (this.raf !== 0)
            cancelAnimationFrame(this.raf);
        this.raf = 0;
    }
}
exports.MiniRts = MiniRts;
// 데모 틀이 부르는 자리. 한 슬라이드에 하나만 만든다.
function boot(host, api) {
    return new MiniRts(host, api);
}
  });

  // names 는 검사 도구용이다 — tools/check_web.js 가 27개를 전부 평가해 보고
  // 브라우저에서만 터지는 최상위 코드(__dirname·process)가 없는지 확인한다.
  root.__rts = { require: __req, names: Object.keys(__mods) };
  // 덱의 데모 틀에 미니 RTS 를 등록한다. 등록만 하고 실행은 슬라이드가 열릴 때 한다 —
  // 1MB 짜리 문서에서 안 보는 판까지 도는 것은 낭비다.
  if (root.__demo) {
    root.__demo('mini-rts', function (host, api) {
      __req('web/minirts').boot(host, api);
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);
