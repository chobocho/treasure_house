/* ============================================================
   16부의 타입스크립트 엔진을 브라우저에서 그대로 돌리기 위한 묶음.

   이 파일의 코드는 ts/src/*.ts 를 tsc 가 옮긴 것이고, 손으로 고친 곳이 없다.
   그래서 이 문서 안에서 걸어 다니는 캐릭터의 좌표는 golden/trace.jsonl 을
   만든 것과 같은 코드가 계산한 값이다.

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
    // 이 구분을 빠뜨리면 game.ts 가 경로 스텁을 경로탐색 모듈로 착각한다.
    var builtin = raw.charAt(0) !== '.';
    if (builtin && n === 'path') {
      // 경로 계산은 모듈을 불러올 때 바로 돈다(raster.ts 의 ROOT 상수).
      // 값을 쓰지는 않으므로 문자열만 이어 준다.
      var join = function () { return Array.prototype.join.call(arguments, '/'); };
      return { join: join, resolve: join, dirname: function (q) { return String(q); } };
    }
    if (builtin && n === 'fs') {
      // 브라우저에는 파일이 없다. 조용히 넘어가지 않고 터지게 둔다.
      return { readFileSync: function () {
        throw new Error('브라우저에서는 파일을 읽을 수 없다 — parsePalette / parseSprites / runScriptText 를 쓸 것');
      }, writeFileSync: function () { throw new Error('브라우저에서는 파일을 쓸 수 없다'); } };
    }
    if (__cache[n]) return __cache[n];
    var f = __mods[n] || __mods['web/' + n];
    if (!f) throw new Error('모듈 없음: ' + name);
    var m = { exports: {} };
    __cache[n] = m.exports;
    f(m.exports, __req, m);
    __cache[n] = m.exports;
    return m.exports;
  }
  __def('fixed', function (exports, require, module) {
"use strict";
// 16.16 고정소수점 — SPEC §2.
//
// 타입스크립트의 정수는 배정밀도 부동소수점(가수 53비트) 위에 얹혀 있다.
// `>>`, `<<`, `&`, `|`, `^` 는 피연산자를 32비트 정수로 잘라 버리므로
// 16.16 값(최대 2^37)이나 2^32 LCG 상태에 쓰면 소리 없이 값이 망가진다.
// 그래서 이 모듈은 시프트를 한 번도 쓰지 않고 `Math.floor` 와 곱셈·나눗셈만 쓴다.
// 파이썬·루아 구현과 코드가 한 줄씩 대응하도록 일부러 한 줄짜리 함수도 남겨 뒀다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.NIB_XOR = exports.SIN = exports.COS = exports.K_INV = exports.ATAN_BRAD = exports.GUARD = exports.N_ITER = exports.OCT_B = exports.OCT_A = exports.FP_ONE = exports.FP_BITS = void 0;
exports.floordiv = floordiv;
exports.fmod = fmod;
exports.pow2 = pow2;
exports.ashr = ashr;
exports.fp = fp;
exports.fpFloor = fpFloor;
exports.fpRound = fpRound;
exports.fpFrac = fpFrac;
exports.fpMul = fpMul;
exports.fpMulr = fpMulr;
exports.fpDiv = fpDiv;
exports.isqrt = isqrt;
exports.fpSqrt = fpSqrt;
exports.octDist = octDist;
exports.cordic = cordic;
exports.xor8 = xor8;
exports.xor16 = xor16;
exports.FP_BITS = 16;
exports.FP_ONE = 65536;
/** b > 0 일 때 -무한대 방향 내림. JS 의 `/` 는 실수 나눗셈이라 floor 가 필요하다. */
function floordiv(a, b) {
    return Math.floor(a / b);
}
/** 항상 0 <= 결과 < b. JS 의 `%` 는 피제수 부호를 따라가므로 그대로 쓸 수 없다. */
function fmod(a, b) {
    return a - b * Math.floor(a / b);
}
// 2의 거듭제곱 표. `1 << i` 로 만들 수도 있지만 i 가 31을 넘는 순간
// 조용히 틀리는 코드가 되므로, 시프트를 아예 쓰지 않는 쪽으로 통일한다.
const POW2 = (() => {
    const t = [];
    let v = 1;
    for (let i = 0; i < 54; i++) {
        t.push(v);
        v *= 2;
    }
    return t;
})();
function pow2(k) {
    return POW2[k];
}
/** 산술 우시프트 = 2^k 로 내림 나눗셈. 음수에서도 내림이다. */
function ashr(a, k) {
    return Math.floor(a / pow2(k));
}
function fp(n) {
    return n * exports.FP_ONE;
}
function fpFloor(x) {
    return Math.floor(x / exports.FP_ONE);
}
function fpRound(x) {
    return Math.floor((x + exports.FP_ONE / 2) / exports.FP_ONE);
}
function fpFrac(x) {
    return fmod(x, exports.FP_ONE);
}
/** floor(a*b / 65536). a 를 상·하위 16비트로 쪼개 중간값을 2^53 아래로 묶는다.
 *
 *  a*b 를 그대로 곱하면 2^62 까지 커져 배정밀도 가수를 넘고, 넘는 순간
 *  예외도 경고도 없이 하위 비트가 사라진다. 그것이 이 함수가 존재하는 이유다.
 *  |a| < 2^31, |b| < 2^37 이면 |ah*b| < 2^52, |al*b| < 2^53. (정리 2.1) */
function fpMul(a, b) {
    const ah = Math.floor(a / exports.FP_ONE);
    const al = a - ah * exports.FP_ONE; // 0 <= al < 65536
    return ah * b + Math.floor((al * b) / exports.FP_ONE);
}
/** 반올림 곱. 광원 감쇠처럼 한쪽으로 쏠리면 곤란한 곳에만 쓴다. */
function fpMulr(a, b) {
    const ah = Math.floor(a / exports.FP_ONE);
    const al = a - ah * exports.FP_ONE;
    return ah * b + Math.floor((al * b + exports.FP_ONE / 2) / exports.FP_ONE);
}
/** floor(a*65536 / b). |a| < 2^37 이면 a*65536 이 2^53 미만이다. */
function fpDiv(a, b) {
    return Math.floor((a * exports.FP_ONE) / b);
}
/** floor(sqrt(n)). 뉴턴 반복 — 단조 감소라 반드시 멈춘다. (정리 2.2)
 *
 *  `Math.sqrt` 를 쓰지 않는다. 반올림 방향이 명세에 없고, 2^43 근처에서
 *  floor(Math.sqrt(n)) 이 참값보다 1 크게 나오는 입력이 실제로 있기 때문이다.
 *  나눗셈만 쓰는 이 형태는 세 언어가 글자 그대로 같다. */
function isqrt(n) {
    if (n < 2)
        return n;
    let x = n;
    let y = Math.floor((x + 1) / 2);
    while (y < x) {
        x = y;
        y = Math.floor((x + Math.floor(n / x)) / 2);
    }
    return x;
}
function fpSqrt(x) {
    return isqrt(x * exports.FP_ONE);
}
// 알파 맥스 플러스 베타 민 — 최소최대오차 최적 계수를 1024배 해 반올림한 것.
exports.OCT_A = 983;
exports.OCT_B = 407;
/** sqrt(dx^2+dy^2) 의 정수 근사. 곱셈 두 번과 나눗셈 한 번. */
function octDist(dx, dy) {
    const ax = dx >= 0 ? dx : -dx;
    const ay = dy >= 0 ? dy : -dy;
    const hi = ax > ay ? ax : ay;
    const lo = ax > ay ? ay : ax;
    return Math.floor((exports.OCT_A * hi + exports.OCT_B * lo) / 1024);
}
// ---------------------------------------------------------------- CORDIC (SPEC §2.6)
exports.N_ITER = 20;
exports.GUARD = 8;
exports.ATAN_BRAD = [
    2097152, 1238021, 654136, 332050, 166669, 83416, 41718, 20860,
    10430, 5215, 2608, 1304, 652, 326, 163, 81, 41, 20, 10, 5,
];
exports.K_INV = 10188014;
/** 16.16 brad 각도 -> [cos, sin] 16.16.
 *
 *  안쪽에서 가드 8비트를 들고 다니다 끝에서 반올림해 버린다.
 *  `y / 2^i` 를 `y >> i` 로 쓰고 싶어지는 자리인데, x·y 가 가드 때문에
 *  최대 2^24 를 넘나들어 32비트 안에는 들어가지만 음수 시프트 규칙이
 *  파이썬의 내림과 어긋난다. 그래서 여기서도 Math.floor 로 통일한다. */
function cordic(theta) {
    let t = fmod(theta, 256 * exports.FP_ONE);
    const quad = Math.floor(t / (64 * exports.FP_ONE));
    t -= quad * 64 * exports.FP_ONE;
    let x = exports.K_INV;
    let y = 0;
    let z = t;
    for (let i = 0; i < exports.N_ITER; i++) {
        const d = z >= 0 ? 1 : -1;
        const p = pow2(i);
        const nx = x - d * Math.floor(y / p);
        const ny = y + d * Math.floor(x / p);
        z -= d * exports.ATAN_BRAD[i];
        x = nx;
        y = ny;
    }
    x = Math.floor((x + 128) / 256);
    y = Math.floor((y + 128) / 256);
    if (quad === 0)
        return [x, y];
    if (quad === 1)
        return [-y, x];
    if (quad === 2)
        return [-x, -y];
    return [y, -x];
}
function buildTrig() {
    const c = new Array(256).fill(0);
    const s = new Array(256).fill(0);
    for (let a = 0; a < 256; a++) {
        const cs = cordic(a * exports.FP_ONE);
        c[a] = cs[0];
        s[a] = cs[1];
    }
    return [c, s];
}
const _trig = buildTrig();
exports.COS = _trig[0];
exports.SIN = _trig[1];
function nibTable() {
    const t = new Array(256).fill(0);
    for (let a = 0; a < 16; a++) {
        for (let b = 0; b < 16; b++) {
            let r = 0;
            let p = 1;
            let x = a;
            let y = b;
            for (let k = 0; k < 4; k++) {
                if (x % 2 !== y % 2)
                    r += p;
                x = Math.floor(x / 2);
                y = Math.floor(y / 2);
                p *= 2;
            }
            t[a * 16 + b] = r;
        }
    }
    return t;
}
exports.NIB_XOR = nibTable();
/** 8비트 배타적 논리합. 니블 표 두 번이면 끝난다.
 *
 *  JS 에는 `^` 가 있고 8비트라면 안전하지만, 루아 5.1 판과 코드를 같게 두려고
 *  세 언어 모두 이 산술 형태를 쓴다. 어느 언어에서 읽어도 같은 함수임이 자명해진다. */
function xor8(a, b) {
    return (exports.NIB_XOR[Math.floor(a / 16) * 16 + Math.floor(b / 16)] * 16 +
        exports.NIB_XOR[(a % 16) * 16 + (b % 16)]);
}
/** 표 없이 만든 16비트 배타적 논리합. 한 비트씩 16번 — O(16). */
function xor16(a, b) {
    let r = 0;
    let p = 1;
    let x = a;
    let y = b;
    for (let i = 0; i < 16; i++) {
        if (x % 2 !== y % 2)
            r += p;
        x = Math.floor(x / 2);
        y = Math.floor(y / 2);
        p *= 2;
    }
    return r;
}
  });
  __def('proj', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MARGIN_Y = exports.MARGIN_X = exports.PICK_MASK = exports.HH = exports.HW = exports.MAXH = exports.MAP_H = exports.MAP_W = exports.SCR_H = exports.SCR_W = exports.TZ = exports.TH = exports.TW = void 0;
exports.tileToScreen = tileToScreen;
exports.worldToScreen = worldToScreen;
exports.screenToTile = screenToTile;
exports.screenToTileSlow = screenToTileSlow;
exports.pickMask = pickMask;
exports.visibleRange = visibleRange;
// 쿼터뷰 투영과 역투영 — SPEC §3.
//
// 두 방향 모두 정수만 쓴다. 화면 좌표는 최대 ±768 이라 32비트에 넉넉히 들어가지만,
// 여기서도 `>>` 대신 Math.floor 를 쓴다. `-17 >> 5` 는 -1 이고 `Math.floor(-17/32)`
// 도 -1 이라 우연히 같지만, 나눗수가 2의 거듭제곱이 아닌 자리(§3.4 의 /2, %2)까지
// 섞이면 규칙이 둘이 되어 버린다. 규칙은 하나여야 읽는 사람이 안 틀린다.
const F = require("./fixed");
exports.TW = 32; // 마름모 가로 지름
exports.TH = 16; // 마름모 세로 지름
exports.TZ = 8; // 높이 한 단계
exports.SCR_W = 320;
exports.SCR_H = 200;
exports.MAP_W = 48;
exports.MAP_H = 48;
exports.MAXH = 15;
exports.HW = exports.TW / 2; // 16
exports.HH = exports.TH / 2; // 8
/** 타일 -> 마름모 꼭대기 꼭짓점의 월드 픽셀.
 *
 *  기저 e_x = (16, 8), e_y = (-16, 8). 행렬식 256 = 2^8 이라
 *  역행렬 성분이 전부 2의 거듭제곱 배수가 된다 — 그것이 2:1 을 고른 이유다. */
function tileToScreen(tx, ty, h) {
    return [exports.HW * (tx - ty), exports.HH * (tx + ty) - h * exports.TZ];
}
/** 16.16 타일 좌표 -> 월드 픽셀. 엔티티가 타일 사이에 있을 때 쓴다. */
function worldToScreen(fx, fy, h) {
    return [
        F.floordiv((fx - fy) * exports.HW, F.FP_ONE),
        F.floordiv((fx + fy) * exports.HH, F.FP_ONE) - h * exports.TZ,
    ];
}
/** 대수적 역. 나눗셈 두 번이면 끝난다. (정리 3.2) */
function screenToTile(px, py) {
    return [F.floordiv(px + 2 * py, 32), F.floordiv(2 * py - px, 32)];
}
/** 마름모 정의(|u| + 2|v| <= 16)로 직접 찾는다 — 빠른 식을 검산하는 용도.
 *
 *  경계 픽셀은 여러 마름모에 걸치므로, floor 규칙과 같은 것을 고르려면
 *  a = px+2py 와 b = 2py-px 가 큰 쪽을 택해야 한다. 파이썬은 튜플 비교
 *  하나로 끝나지만 JS 에는 튜플 순서 비교가 없어 손으로 편다. */
function screenToTileSlow(px, py) {
    const g = screenToTile(px, py);
    let bx = 0;
    let by = 0;
    let have = false;
    for (let tx = g[0] - 2; tx <= g[0] + 2; tx++) {
        for (let ty = g[1] - 2; ty <= g[1] + 2; ty++) {
            const cx = exports.HW * (tx - ty);
            const cy = exports.HH * (tx + ty) + exports.HH;
            const u = px - cx;
            const v = py - cy;
            if ((u >= 0 ? u : -u) + 2 * (v >= 0 ? v : -v) <= exports.HW) {
                if (!have || tx + ty > bx + by || (tx + ty === bx + by && tx > bx)) {
                    bx = tx;
                    by = ty;
                    have = true;
                }
            }
        }
    }
    return [bx, by];
}
/** 32x16 모서리 마스크. 값은 2*A + (B+1) 로 0..3 네 가지뿐이다. (SPEC §3.4) */
function buildMask() {
    const m = new Array(exports.TW * exports.TH).fill(0);
    for (let oy = 0; oy < exports.TH; oy++) {
        for (let ox = 0; ox < exports.TW; ox++) {
            const a = F.floordiv(ox + 2 * oy, 32);
            const b = F.floordiv(2 * oy - ox, 32);
            m[oy * exports.TW + ox] = 2 * a + (b + 1);
        }
    }
    return m;
}
exports.PICK_MASK = buildMask();
/** 도스식 역투영 — 나눗셈 두 번(사각형 찾기)과 표 조회 한 번. */
function pickMask(px, py) {
    const rc = F.floordiv(px, exports.TW);
    const rr = F.floordiv(py, exports.TH);
    const ox = px - exports.TW * rc;
    const oy = py - exports.TH * rr;
    const m = exports.PICK_MASK[oy * exports.TW + ox];
    return [rc + rr + F.floordiv(m, 2), rr - rc + F.fmod(m, 2) - 1];
}
exports.MARGIN_X = exports.HW;
// 세로 여백: 마름모 반, 최대 높이 15단계, 그리고 가장 큰 스프라이트(나무 32px)
exports.MARGIN_Y = exports.HH + exports.MAXH * exports.TZ + 32;
/** 뷰포트에 걸치는 타일 범위. 네 모서리만 역투영하면 된다. (정리 3.3) */
function visibleRange(x0, y0, x1, y1) {
    const ax0 = x0 - exports.MARGIN_X;
    const ax1 = x1 + exports.MARGIN_X;
    const ay0 = y0 - exports.MARGIN_Y;
    const ay1 = y1 + exports.MARGIN_Y;
    let tx0 = F.floordiv(ax0 + 2 * ay0, 32);
    let tx1 = F.floordiv(ax1 + 2 * ay1, 32);
    let ty0 = F.floordiv(2 * ay0 - ax1, 32);
    let ty1 = F.floordiv(2 * ay1 - ax0, 32);
    if (tx0 < 0)
        tx0 = 0;
    if (ty0 < 0)
        ty0 = 0;
    if (tx1 > exports.MAP_W - 1)
        tx1 = exports.MAP_W - 1;
    if (ty1 > exports.MAP_H - 1)
        ty1 = exports.MAP_H - 1;
    return [tx0, ty0, tx1, ty1];
}
  });
  __def('rng', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Rng = exports.LCG_M = exports.LCG_C = exports.LCG_A = void 0;
// 난수 — SPEC §5.2. 볼랜드 계열 LCG.
//
// 상태가 2^32 미만이라 `s >>> 16` 이나 `s & 0xffff` 로 쓰고 싶어지는 자리인데,
// 곱한 뒤의 중간값(22695477 * 65535 ~ 2^41)이 32비트를 훌쩍 넘는다.
// `*` 는 배정밀도로 계산되지만 그 결과를 비트 연산에 넣는 순간 하위 32비트만 남는다.
// 그래서 상·하위 16비트로 쪼개 나눗셈과 곱셈만으로 처리한다. (정리 5.1)
exports.LCG_A = 22695477;
exports.LCG_C = 1;
exports.LCG_M = 4294967296; // 2^32
class Rng {
    constructor(seed) {
        this.s = seed - exports.LCG_M * Math.floor(seed / exports.LCG_M);
    }
    /** 상태를 한 걸음 굴리고 15비트 난수를 돌려준다 (0..32767).
     *
     *  하위 비트는 주기가 짧다 — 최하위 비트는 0,1 을 번갈 뿐이다.
     *  그래서 도스 시절 rand() 도 비트 30..16 을 꺼내 썼다. */
    next() {
        const s = this.s;
        const sh = Math.floor(s / 65536);
        const sl = s - sh * 65536;
        const lo = exports.LCG_A * sl + exports.LCG_C; // < 2^41
        const hi = exports.LCG_A * sh; // < 2^41
        const t = (hi - 65536 * Math.floor(hi / 65536)) * 65536 + lo;
        this.s = t - exports.LCG_M * Math.floor(t / exports.LCG_M);
        const u = Math.floor(this.s / 65536);
        return u - 32768 * Math.floor(u / 32768);
    }
    below(n) {
        const v = this.next();
        return v - n * Math.floor(v / n);
    }
    roll(n, m) {
        let t = 0;
        for (let i = 0; i < n; i++) {
            const v = this.next();
            t += v - m * Math.floor(v / m) + 1;
        }
        return t;
    }
}
exports.Rng = Rng;
  });
  __def('camera', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WORLD_Y1 = exports.WORLD_Y0 = exports.WORLD_X1 = exports.WORLD_X0 = exports.DEADZONE_Y = exports.DEADZONE_X = void 0;
exports.clampCam = clampCam;
exports.follow = follow;
// 카메라 — SPEC §4. 정수 픽셀 스크롤과 데드존 추적.
const proj_1 = require("./proj");
exports.DEADZONE_X = 48;
exports.DEADZONE_Y = 24;
// 맵 전체가 차지하는 월드 픽셀 범위. 마름모 배치라 가로가 세로의 두 배다.
exports.WORLD_X0 = -proj_1.HW * (proj_1.MAP_H - 1) - proj_1.HW;
exports.WORLD_X1 = proj_1.HW * (proj_1.MAP_W - 1) + proj_1.HW;
exports.WORLD_Y0 = -proj_1.MAXH * proj_1.TZ;
exports.WORLD_Y1 = 8 * (proj_1.MAP_W + proj_1.MAP_H - 2) + 16;
function clampCam(cx, cy) {
    const loX = exports.WORLD_X0;
    const hiX = exports.WORLD_X1 - proj_1.SCR_W;
    const loY = exports.WORLD_Y0;
    const hiY = exports.WORLD_Y1 - proj_1.SCR_H;
    let x = cx;
    let y = cy;
    if (x < loX)
        x = loX;
    if (x > hiX)
        x = hiX;
    if (y < loY)
        y = loY;
    if (y > hiY)
        y = hiY;
    return [x, y];
}
/** 대상이 데드존을 벗어난 만큼만 카메라를 민다.
 *
 *  매 프레임 중앙에 붙여 두면 걸을 때마다 화면이 흔들린다.
 *  도스 RPG 들이 가운데에 네모난 여유를 둔 이유가 그것이다. */
function follow(cx, cy, tgtX, tgtY) {
    let x = cx;
    let y = cy;
    const dx = tgtX - x - proj_1.SCR_W / 2;
    const dy = tgtY - y - proj_1.SCR_H / 2;
    if (dx > exports.DEADZONE_X)
        x += dx - exports.DEADZONE_X;
    else if (dx < -exports.DEADZONE_X)
        x += dx + exports.DEADZONE_X;
    if (dy > exports.DEADZONE_Y)
        y += dy - exports.DEADZONE_Y;
    else if (dy < -exports.DEADZONE_Y)
        y += dy + exports.DEADZONE_Y;
    return clampCam(x, y);
}
  });
  __def('gamemap', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TOWN_WALL_H = exports.TOWN_H = exports.TOWN_MID = exports.TOWN_Y1 = exports.TOWN_X1 = exports.TOWN_Y0 = exports.TOWN_X0 = exports.DS_BLUR = exports.DS_OFF = exports.DS_ROUGH_DEN = exports.DS_ROUGH_NUM = exports.DS_SCALE = exports.DS_CORNER = exports.DS_SEED = exports.DS_N = exports.GameMap = exports.MIN_MOVE = exports.OPAQUE = exports.MOVE = exports.TERRAIN = exports.T_VOID = exports.T_LAVA = exports.T_SWAMP = exports.T_SNOW = exports.T_BRIDGE = exports.T_WALL = exports.T_FLOOR = exports.T_ROAD = exports.T_MOUNTAIN = exports.T_FOREST = exports.T_ROCK = exports.T_DIRT = exports.T_GRASS = exports.T_SAND = exports.T_WATER = exports.T_DEEP = exports.MAXH = exports.MAP_H = exports.MAP_W = void 0;
exports.makeCell = makeCell;
exports.terrainOf = terrainOf;
exports.heightOf = heightOf;
exports.genHeight = genHeight;
exports.smooth = smooth;
exports.terrainOfValue = terrainOfValue;
exports.heightOfValue = heightOfValue;
exports.stampTown = stampTown;
exports.genMap = genMap;
exports.saveRle = saveRle;
exports.loadRle = loadRle;
// 지형 맵 — SPEC §5. 한 칸 1바이트, 다이아몬드-스퀘어 생성, RLE 저장.
//
// 파이썬 쪽이 모듈 이름을 map 이 아니라 gamemap 으로 둔 것은 내장 map 과
// 겹치지 않게 하려는 것이다. 타입스크립트에서는 같은 이유로 클래스 이름도
// Map 이 아니라 GameMap 이다 — ES2015 의 전역 Map 을 모듈 안에서 가려 버리면
// 나중에 진짜 Map 이 필요해졌을 때 조용히 엉뚱한 것을 쓰게 된다.
const rng_1 = require("./rng");
exports.MAP_W = 48;
exports.MAP_H = 48;
exports.MAXH = 15;
// 지형 id — 셀 바이트의 하위 4비트
exports.T_DEEP = 0;
exports.T_WATER = 1;
exports.T_SAND = 2;
exports.T_GRASS = 3;
exports.T_DIRT = 4;
exports.T_ROCK = 5;
exports.T_FOREST = 6;
exports.T_MOUNTAIN = 7;
exports.T_ROAD = 8;
exports.T_FLOOR = 9;
exports.T_WALL = 10;
exports.T_BRIDGE = 11;
exports.T_SNOW = 12;
exports.T_SWAMP = 13;
exports.T_LAVA = 14;
exports.T_VOID = 15;
// (이름, 이동비용 0=불가, 시야차단)
exports.TERRAIN = [
    ['DEEP', 0, false], ['WATER', 0, false], ['SAND', 12, false],
    ['GRASS', 10, false], ['DIRT', 10, false], ['ROCK', 14, false],
    ['FOREST', 16, true], ['MOUNTAIN', 0, true], ['ROAD', 8, false],
    ['FLOOR', 10, false], ['WALL', 0, true], ['BRIDGE', 10, false],
    ['SNOW', 13, false], ['SWAMP', 20, false], ['LAVA', 0, false],
    ['VOID', 0, true],
];
exports.MOVE = exports.TERRAIN.map((t) => t[1]);
exports.OPAQUE = exports.TERRAIN.map((t) => t[2]);
exports.MIN_MOVE = exports.MOVE.filter((v) => v > 0).reduce((a, b) => (a < b ? a : b));
function makeCell(t, h) {
    return t + h * 16;
}
function terrainOf(cell) {
    return cell % 16;
}
function heightOf(cell) {
    return Math.floor(cell / 16);
}
class GameMap {
    constructor(w, h, cells) {
        this.w = w;
        this.h = h;
        // Uint8Array 는 범위를 벗어난 대입을 조용히 감싼다. 셀은 make_cell 로만
        // 만들고(0..255 보장) 그 밖의 경로로는 쓰지 않는 것이 유일한 방어다.
        this.cells = cells !== undefined ? cells : new Uint8Array(w * h);
    }
    inside(x, y) {
        return x >= 0 && x < this.w && y >= 0 && y < this.h;
    }
    at(x, y) {
        return this.cells[y * this.w + x];
    }
    put(x, y, cell) {
        this.cells[y * this.w + x] = cell;
    }
    terrain(x, y) {
        return this.cells[y * this.w + x] % 16;
    }
    height(x, y) {
        return Math.floor(this.cells[y * this.w + x] / 16);
    }
}
exports.GameMap = GameMap;
// ---------------------------------------------------------------- 다이아몬드-스퀘어
exports.DS_N = 64;
exports.DS_SEED = 1;
exports.DS_CORNER = [520, 300, 700, 420];
exports.DS_SCALE = 560;
exports.DS_ROUGH_NUM = 58;
exports.DS_ROUGH_DEN = 100;
exports.DS_OFF = Math.floor((exports.DS_N + 1 - exports.MAP_W) / 2); // 65x65 에서 가운데 48x48
/** 프랙탈 중점 변위. 반복 순서가 난수 소비 순서를 정하므로 명세의 일부다.
 *
 *  O(n^2) 시간, O(n^2) 공간. 격자는 (2^k + 1) 이어야 한다.
 *  값이 ±수천 수준이라 Int16Array 로도 되지만, 중간에 clamp 전 값이
 *  범위를 넘을 수 있어 감싸기 사고가 나기 쉽다. 평범한 number[][] 로 둔다. */
function genHeight(n, corners, scale0, seed, roughNum = exports.DS_ROUGH_NUM, roughDen = exports.DS_ROUGH_DEN) {
    const size = n + 1;
    const h = [];
    for (let i = 0; i < size; i++)
        h.push(new Array(size).fill(0));
    h[0][0] = corners[0];
    h[0][n] = corners[1];
    h[n][0] = corners[2];
    h[n][n] = corners[3];
    const r = new rng_1.Rng(seed);
    let step = n;
    let scale = scale0;
    const jitter = () => {
        const span = 2 * scale + 1;
        const v = r.next();
        return v - span * Math.floor(v / span) - scale;
    };
    while (step > 1) {
        const half = Math.floor(step / 2);
        // 다이아몬드: 정사각형 네 꼭짓점의 평균 + 흔들림
        for (let y = half; y < size; y += step) {
            for (let x = half; x < size; x += step) {
                const s = h[y - half][x - half]
                    + h[y - half][x + half]
                    + h[y + half][x - half]
                    + h[y + half][x + half];
                h[y][x] = Math.floor(s / 4) + jitter();
            }
        }
        // 스퀘어: 마름모 네 꼭짓점(격자 밖은 뺀다)의 평균 + 흔들림.
        // 행 간격은 half, 열 간격은 step 이고 홀짝 행마다 시작 열이 어긋난다 —
        // 그래야 아직 값이 없는 변의 중점만 정확히 한 번씩 채운다.
        for (let y = 0; y < size; y += half) {
            const xs = Math.floor(y / half) % 2 === 0 ? half : 0;
            for (let x = xs; x < size; x += step) {
                let s = 0;
                let cnt = 0;
                if (x - half >= 0) {
                    s += h[y][x - half];
                    cnt += 1;
                }
                if (x + half < size) {
                    s += h[y][x + half];
                    cnt += 1;
                }
                if (y - half >= 0) {
                    s += h[y - half][x];
                    cnt += 1;
                }
                if (y + half < size) {
                    s += h[y + half][x];
                    cnt += 1;
                }
                h[y][x] = Math.floor(s / cnt) + jitter();
            }
        }
        step = half;
        scale = Math.floor((scale * roughNum) / roughDen);
    }
    for (const row of h) {
        for (let i = 0; i < size; i++) {
            const v = row[i];
            row[i] = v < 0 ? 0 : v > 1023 ? 1023 : v;
        }
    }
    return h;
}
exports.DS_BLUR = 2;
/** 3x3 상자 흐리기. 프랙탈 그대로는 타일 눈금에서 잡음처럼 보인다.
 *
 *  O(9 * n^2) 시간. 가장자리는 격자 안의 이웃만 평균한다.
 *  RLE 가 실제로 압축되게 만드는 유일한 장치이기도 하다. */
function smooth(h0) {
    const n = h0.length;
    let h = h0;
    for (let pass = 0; pass < exports.DS_BLUR; pass++) {
        const g = [];
        for (let i = 0; i < n; i++)
            g.push(new Array(n).fill(0));
        for (let y = 0; y < n; y++) {
            for (let x = 0; x < n; x++) {
                let s = 0;
                let c = 0;
                for (let dy = -1; dy <= 1; dy++) {
                    const yy = y + dy;
                    if (yy < 0 || yy >= n)
                        continue;
                    const row = h[yy];
                    for (let dx = -1; dx <= 1; dx++) {
                        const xx = x + dx;
                        if (xx >= 0 && xx < n) {
                            s += row[xx];
                            c += 1;
                        }
                    }
                }
                g[y][x] = Math.floor(s / c);
            }
        }
        h = g;
    }
    return h;
}
/** 높이값 -> 지형. 문턱은 SPEC §5.5 가 정한다. */
function terrainOfValue(v) {
    if (v < 100)
        return exports.T_DEEP;
    if (v < 205)
        return exports.T_WATER;
    if (v < 240)
        return exports.T_SAND;
    if (v < 460)
        return exports.T_GRASS;
    if (v < 630)
        return exports.T_FOREST;
    if (v < 800)
        return exports.T_ROCK;
    return exports.T_MOUNTAIN;
}
function heightOfValue(v) {
    if (v < 205)
        return 0;
    const hh = Math.floor((v - 205) / 90);
    return hh > 12 ? 12 : hh;
}
exports.TOWN_X0 = 18;
exports.TOWN_Y0 = 18;
exports.TOWN_X1 = 30;
exports.TOWN_Y1 = 30;
exports.TOWN_MID = 24;
exports.TOWN_H = 2;
exports.TOWN_WALL_H = 4; // 성벽은 바닥보다 두 단계 높다 — 그래야 옆면이 보인다
/** 마을을 찍는다. 순서가 중요하다 — 벽을 먼저 두르고 문을 나중에 뚫는다. */
function stampTown(m) {
    for (let ty = exports.TOWN_Y0; ty < exports.TOWN_Y1; ty++) {
        for (let tx = exports.TOWN_X0; tx < exports.TOWN_X1; tx++) {
            if (tx === exports.TOWN_X0 || tx === exports.TOWN_X1 - 1 || ty === exports.TOWN_Y0 || ty === exports.TOWN_Y1 - 1) {
                m.put(tx, ty, makeCell(exports.T_WALL, exports.TOWN_WALL_H));
                continue;
            }
            const t = tx === exports.TOWN_MID || ty === exports.TOWN_MID ? exports.T_ROAD : exports.T_FLOOR;
            m.put(tx, ty, makeCell(t, exports.TOWN_H));
        }
    }
    const gates = [
        [exports.TOWN_MID, exports.TOWN_Y0], [exports.TOWN_MID, exports.TOWN_Y1 - 1],
        [exports.TOWN_X0, exports.TOWN_MID], [exports.TOWN_X1 - 1, exports.TOWN_MID],
    ];
    for (const [tx, ty] of gates)
        m.put(tx, ty, makeCell(exports.T_ROAD, exports.TOWN_H));
    for (let ty = 0; ty < exports.TOWN_Y0; ty++)
        m.put(exports.TOWN_MID, ty, makeCell(exports.T_ROAD, exports.TOWN_H));
    for (let ty = exports.TOWN_Y1; ty < exports.MAP_H; ty++)
        m.put(exports.TOWN_MID, ty, makeCell(exports.T_ROAD, exports.TOWN_H));
}
/** 맵 한 장. 같은 씨앗이면 언제나 같은 맵이다. */
function genMap() {
    const hg = smooth(genHeight(exports.DS_N, exports.DS_CORNER, exports.DS_SCALE, exports.DS_SEED));
    const m = new GameMap(exports.MAP_W, exports.MAP_H);
    for (let ty = 0; ty < exports.MAP_H; ty++) {
        const row = hg[ty + exports.DS_OFF];
        for (let tx = 0; tx < exports.MAP_W; tx++) {
            const v = row[tx + exports.DS_OFF];
            m.put(tx, ty, makeCell(terrainOfValue(v), heightOfValue(v)));
        }
    }
    stampTown(m);
    return m;
}
// ---------------------------------------------------------------- RLE
/** 행 우선으로 훑어 같은 값을 묶는다. 런 하나는 최대 255칸. */
function saveRle(m) {
    const runs = [];
    let i = 0;
    const n = m.cells.length;
    while (i < n) {
        const v = m.cells[i];
        let j = i;
        while (j < n && m.cells[j] === v && j - i < 255)
            j += 1;
        runs.push(String(j - i) + ':' + String(v));
        i = j;
    }
    const lines = ['ISORPG-MAP 1 ' + m.w + ' ' + m.h];
    for (let k = 0; k < runs.length; k += 16)
        lines.push(runs.slice(k, k + 16).join(' '));
    return lines.join('\n') + '\n';
}
function loadRle(text) {
    const lines = text.trim().split('\n');
    const head = lines[0].split(/\s+/);
    if (head[0] !== 'ISORPG-MAP')
        throw new Error('맵 매직이 다르다: ' + head[0]);
    const w = parseInt(head[2], 10);
    const h = parseInt(head[3], 10);
    const cells = [];
    for (let li = 1; li < lines.length; li++) {
        const toks = lines[li].split(/\s+/).filter((s) => s.length > 0);
        for (const run of toks) {
            const parts = run.split(':');
            const c = parseInt(parts[0], 10);
            const v = parseInt(parts[1], 10);
            for (let k = 0; k < c; k++)
                cells.push(v);
        }
    }
    if (cells.length !== w * h) {
        throw new Error('칸 수가 ' + w * h + ' 여야 하는데 ' + cells.length);
    }
    return new GameMap(w, h, Uint8Array.from(cells));
}
  });
  __def('sortdag', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.I_Z1 = exports.I_Y1 = exports.I_X1 = exports.I_Z0 = exports.I_Y0 = exports.I_X0 = exports.I_ID = void 0;
exports.boxBbox = boxBbox;
exports.bboxOverlap = bboxOverlap;
exports.behind = behind;
exports.depthKey = depthKey;
exports.topoSort = topoSort;
// 그리기 순서 — SPEC §6. 화가 알고리즘을 DAG 로 푼다.
//
// 파이썬은 heapq 에 (depth_key 튜플, 인덱스) 를 그대로 넣는다. JS 에는 튜플
// 비교도 표준 힙도 없으므로 이진 힙을 직접 만든다. 다만 depth_key 의 마지막
// 성분이 id 라 키가 전부 서로 다르고, 그래서 어떤 힙 구현을 써도 방출 순서가
// 같다 — 세 언어가 각자의 힙을 써도 되는 이유이자, 이 포트가 성립하는 근거다.
const proj_1 = require("./proj");
exports.I_ID = 0;
exports.I_X0 = 1;
exports.I_Y0 = 2;
exports.I_Z0 = 3;
exports.I_X1 = 4;
exports.I_Y1 = 5;
exports.I_Z1 = 6;
/** 상자의 화면 경계상자 [minx, miny, maxx, maxy]. 여덟 꼭짓점을 다 투영한다 —
 *  네 값만 골라 쓰면 왜 그 값인지가 코드에서 사라진다. 상자 하나에 여덟 번은 싸다. */
function boxBbox(b) {
    let minx = 1073741824;
    let miny = 1073741824;
    let maxx = -1073741824;
    let maxy = -1073741824;
    const xs = [b[exports.I_X0], b[exports.I_X1]];
    const ys = [b[exports.I_Y0], b[exports.I_Y1]];
    const zs = [b[exports.I_Z0], b[exports.I_Z1]];
    for (const x of xs) {
        for (const y of ys) {
            for (const z of zs) {
                const sx = proj_1.HW * (x - y);
                const sy = proj_1.HH * (x + y) - z * proj_1.TZ;
                if (sx < minx)
                    minx = sx;
                if (sx > maxx)
                    maxx = sx;
                if (sy < miny)
                    miny = sy;
                if (sy > maxy)
                    maxy = sy;
            }
        }
    }
    return [minx, miny, maxx, maxy];
}
function bboxOverlap(a, b) {
    return !(a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1]);
}
/** a 를 b 보다 먼저 그려야 하는가. 셋 중 하나만 성립해도 참이다.
 *  이 느슨함이 화면에서는 대개 옳지만 반대칭이 아니어서 순환을 만든다. */
function behind(a, b) {
    return a[exports.I_X1] <= b[exports.I_X0]
        || a[exports.I_Y1] <= b[exports.I_Y0]
        || a[exports.I_Z1] <= b[exports.I_Z0];
}
/** 동점을 가르는 기준 [x0+y0, z0, id]. id 가 마지막에 들어가 완전히 결정적이다. */
function depthKey(b) {
    return [b[exports.I_X0] + b[exports.I_Y0], b[exports.I_Z0], b[exports.I_ID]];
}
function keyLess(a, b) {
    if (a[0] !== b[0])
        return a[0] < b[0];
    if (a[1] !== b[1])
        return a[1] < b[1];
    return a[2] < b[2];
}
/** depth_key 오름차순 이진 힙. 원소는 [키, 노드 인덱스].
 *  키가 서로 다르므로 인덱스까지 비교할 일은 실제로 생기지 않지만,
 *  전순서를 완성해 두는 편이 나중에 상자를 늘렸을 때 사고를 막는다. */
class KeyHeap {
    constructor() {
        this.ks = [];
        this.vs = [];
    }
    get size() {
        return this.vs.length;
    }
    less(i, j) {
        const a = this.ks[i];
        const b = this.ks[j];
        if (keyLess(a, b))
            return true;
        if (keyLess(b, a))
            return false;
        return this.vs[i] < this.vs[j];
    }
    swap(i, j) {
        const tk = this.ks[i];
        this.ks[i] = this.ks[j];
        this.ks[j] = tk;
        const tv = this.vs[i];
        this.vs[i] = this.vs[j];
        this.vs[j] = tv;
    }
    push(k, v) {
        this.ks.push(k);
        this.vs.push(v);
        let i = this.vs.length - 1;
        while (i > 0) {
            const p = Math.floor((i - 1) / 2);
            if (!this.less(i, p))
                break;
            this.swap(i, p);
            i = p;
        }
    }
    pop() {
        const top = this.vs[0];
        const last = this.vs.length - 1;
        this.swap(0, last);
        this.ks.pop();
        this.vs.pop();
        let i = 0;
        const n = this.vs.length;
        for (;;) {
            const l = 2 * i + 1;
            const r = l + 1;
            let m = i;
            if (l < n && this.less(l, m))
                m = l;
            if (r < n && this.less(r, m))
                m = r;
            if (m === i)
                break;
            this.swap(i, m);
            i = m;
        }
        return top;
    }
}
/** 칸 알고리즘. 순환이 남으면 depth_key 가 가장 작은 것을 강제로 뽑는다.
 *  반환: [id 순서, 순환을 자른 횟수] */
function topoSort(items) {
    const n = items.length;
    const bb = items.map(boxBbox);
    const adj = [];
    for (let i = 0; i < n; i++)
        adj.push([]);
    const indeg = new Array(n).fill(0);
    // 화면 x 로 훑는 쓸어내기. 모든 쌍을 보면 O(n^2) 인데, 한 화면에 상자가
    // 600개쯤 되면 18만 번이다. x 구간이 겹치는 것끼리만 보면 그 4분의 1로 준다.
    const idx = [];
    for (let i = 0; i < n; i++)
        idx.push(i);
    idx.sort((a, b) => {
        const d = bb[a][0] - bb[b][0];
        return d !== 0 ? d : a - b;
    });
    for (let a = 0; a < n; a++) {
        const i = idx[a];
        const bi = bb[i];
        const ii = items[i];
        const ri = bi[2];
        for (let b = a + 1; b < n; b++) {
            const j = idx[b];
            const bj = bb[j];
            if (bj[0] >= ri)
                break; // 이후는 전부 오른쪽 — 더 볼 필요가 없다
            if (bi[3] <= bj[1] || bj[3] <= bi[1])
                continue;
            const jj = items[j];
            const aij = behind(ii, jj);
            const aji = behind(jj, ii);
            // 양쪽 다 참이면 순서가 무의미하다 — 간선을 걸지 않는다 (보조정리 6.2)
            if (aij && !aji) {
                adj[i].push(j);
                indeg[j] = indeg[j] + 1;
            }
            else if (aji && !aij) {
                adj[j].push(i);
                indeg[i] = indeg[i] + 1;
            }
        }
    }
    const heap = new KeyHeap();
    for (let i = 0; i < n; i++) {
        if (indeg[i] === 0)
            heap.push(depthKey(items[i]), i);
    }
    const done = new Array(n).fill(false);
    const order = [];
    let breaks = 0;
    let left = n;
    while (left > 0) {
        let pick = -1;
        if (heap.size > 0) {
            pick = heap.pop();
            if (done[pick])
                continue;
        }
        else {
            // 순환이다. 남은 것 중 가장 뒤에 있어야 할 것을 강제로 방출한다.
            breaks += 1;
            let best = null;
            for (let i = 0; i < n; i++) {
                if (done[i])
                    continue;
                const k = depthKey(items[i]);
                if (best === null || keyLess(k, best)) {
                    best = k;
                    pick = i;
                }
            }
            for (let i = 0; i < n; i++) {
                if (done[i])
                    continue;
                const lst = adj[i];
                const at = lst.indexOf(pick);
                if (at >= 0) {
                    lst.splice(at, 1);
                    indeg[pick] = indeg[pick] - 1;
                }
            }
        }
        done[pick] = true;
        left -= 1;
        order.push(items[pick][exports.I_ID]);
        for (const j of adj[pick]) {
            indeg[j] = indeg[j] - 1;
            if (indeg[j] === 0 && !done[j])
                heap.push(depthKey(items[j]), j);
        }
        adj[pick] = [];
    }
    return [order, breaks];
}
  });
  __def('raster', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dirty = exports.Frame = exports.Sprite = exports.GOLDEN = exports.ROOT = exports.WATER_HI = exports.WATER_LO = exports.DAC_MAX = exports.LIGHT_LEVELS = exports.PAL_SIZE = exports.SCR_H = exports.SCR_W = void 0;
exports.parsePalette = parsePalette;
exports.loadPalette = loadPalette;
exports.buildLight = buildLight;
exports.parseSprites = parseSprites;
exports.loadSprites = loadSprites;
exports.getLight = getLight;
exports.setLight = setLight;
exports.cyclePalette = cyclePalette;
exports.expand6 = expand6;
exports.toPpm = toPpm;
// 래스터 — SPEC §7. 320x200 8비트 인덱스 프레임버퍼.
//
// 모드 13h 를 그대로 흉내 낸다. 프레임버퍼는 Uint8Array 다 — 파이썬의 bytearray,
// 루아의 1-기반 정수 테이블과 같은 자리다. 다만 Uint8Array 는 범위를 벗어난
// 대입을 예외 없이 256으로 접어 버리므로, 넣는 값이 팔레트 인덱스(0..255)임을
// 넣기 전에 보장해야 한다. 감싸기는 버그를 숨기지 없애지 않는다.
const fs = require("fs");
const path = require("path");
exports.SCR_W = 320;
exports.SCR_H = 200;
exports.PAL_SIZE = 256;
exports.LIGHT_LEVELS = 16;
exports.DAC_MAX = 63;
exports.WATER_LO = 16;
exports.WATER_HI = 31;
// dist/src -> dist -> ts -> isorpg. node dist/src/main.js 를 ts/ 에서 돌리든
// 다른 데서 돌리든 같은 곳을 가리켜야 하므로 cwd 가 아니라 __dirname 을 쓴다.
exports.ROOT = path.resolve(__dirname, '..', '..', '..');
exports.GOLDEN = path.join(exports.ROOT, 'golden');
/** golden/palette.txt 의 내용을 판다. 파일 읽기와 나눠 둔 것은 브라우저 때문이다 —
 *  덱 안에서 도는 미니 RPG 는 같은 문자열을 소스에 박아 넣고 이 함수만 부른다. */
function parsePalette(raw) {
    const text = raw.trim().split('\n');
    const head = text[0].split(/\s+/);
    if (head[0] !== 'ISORPG-PAL')
        throw new Error('팔레트 매직이 다르다: ' + head[0]);
    const pal = [];
    for (let i = 1; i < text.length; i++) {
        const q = text[i].split(/\s+/);
        pal.push([
            parseInt(q[1], 10),
            parseInt(q[2], 10),
            parseInt(q[3], 10),
        ]);
    }
    if (pal.length !== exports.PAL_SIZE)
        throw new Error('팔레트가 ' + pal.length + '색');
    return pal;
}
/** golden/palette.txt -> [r,g,b] 256개. 값은 6비트 DAC (0..63). */
function loadPalette(p) {
    return parsePalette(fs.readFileSync(p ?? path.join(exports.GOLDEN, 'palette.txt'), 'utf8'));
}
/** 명암표 16 x 256. LIGHT[l*256 + c] = 색 c 를 l/15 로 어둡게 한 것에 가장 가까운 색.
 *
 *  16 * 256 * 256 = 1,048,576 번의 거리 계산 — 시작할 때 한 번뿐이다.
 *  동점이면 인덱스가 작은 쪽을 고른다(`d < bd` 이므로 먼저 본 것이 이긴다).
 *  `<=` 로 바꾸면 파이썬과 다른 표가 나오고 렌더 파리티가 그 자리에서 깨진다. */
function buildLight(pal) {
    const tbl = new Array(exports.LIGHT_LEVELS * exports.PAL_SIZE).fill(0);
    for (let l = 0; l < exports.LIGHT_LEVELS; l++) {
        for (let c = 0; c < exports.PAL_SIZE; c++) {
            const src = pal[c];
            const tr = Math.floor((src[0] * l) / (exports.LIGHT_LEVELS - 1));
            const tg = Math.floor((src[1] * l) / (exports.LIGHT_LEVELS - 1));
            const tb = Math.floor((src[2] * l) / (exports.LIGHT_LEVELS - 1));
            let best = 0;
            let bd = 1073741824;
            for (let k = 0; k < exports.PAL_SIZE; k++) {
                const q = pal[k];
                const dr = q[0] - tr;
                const dg = q[1] - tg;
                const db = q[2] - tb;
                const d = dr * dr + dg * dg + db * db;
                if (d < bd) {
                    bd = d;
                    best = k;
                    if (d === 0)
                        break;
                }
            }
            tbl[l * exports.PAL_SIZE + c] = best;
        }
    }
    return tbl;
}
class Sprite {
    constructor(name, w, h, ox, oy, rows) {
        this.name = name;
        this.w = w;
        this.h = h;
        this.ox = ox;
        this.oy = oy;
        this.rows = rows;
    }
}
exports.Sprite = Sprite;
/** golden/tiles.rle 의 내용을 판다. 색 0 은 투명. */
function parseSprites(raw) {
    const lines = raw.replace(/\n+$/, '').split('\n');
    const head = lines[0].split(/\s+/);
    if (head[0] !== 'ISORPG-TILES')
        throw new Error('스프라이트 매직이 다르다: ' + head[0]);
    const out = [];
    let i = 1;
    while (i < lines.length) {
        const q = lines[i].split(/\s+/);
        const name = q[2];
        const w = parseInt(q[3], 10);
        const h = parseInt(q[4], 10);
        const ox = parseInt(q[5], 10);
        const oy = parseInt(q[6], 10);
        i += 1;
        const rows = [];
        for (let k = 0; k < h; k++) {
            const runs = [];
            let total = 0;
            for (const tok of lines[i + k].split(/\s+/)) {
                const ab = tok.split(':');
                const a = parseInt(ab[0], 10);
                const b = parseInt(ab[1], 10);
                runs.push([a, b]);
                total += a;
            }
            if (total !== w) {
                throw new Error(name + ' 의 ' + k + '행 런 합이 ' + total + ' (폭 ' + w + ')');
            }
            rows.push(runs);
        }
        i += h;
        out.push(new Sprite(name, w, h, ox, oy, rows));
    }
    const want = parseInt(head[2], 10);
    if (out.length !== want) {
        throw new Error('스프라이트 개수가 ' + want + ' 여야 하는데 ' + out.length);
    }
    return out;
}
/** golden/tiles.rle 을 읽는다. */
function loadSprites(p) {
    return parseSprites(fs.readFileSync(p ?? path.join(exports.GOLDEN, 'tiles.rle'), 'utf8'));
}
let _lightCache = null;
/** 기본 명암표. 만드는 데 시간이 걸리므로 한 번만 만들어 둔다. */
function getLight() {
    if (_lightCache === null)
        _lightCache = buildLight(loadPalette());
    return _lightCache;
}
/** 명암표를 밖에서 넣는다. 브라우저에는 파일이 없어 팔레트를 읽을 수 없기 때문이다. */
function setLight(tbl) {
    _lightCache = tbl;
}
/** 프레임버퍼 하나. Uint8Array 가 곧 모드 13h 의 A000 세그먼트다. */
class Frame {
    constructor(light) {
        this.fb = new Uint8Array(exports.SCR_W * exports.SCR_H);
        this.light = light ?? getLight();
    }
    clear(c = 0) {
        this.fb.fill(c);
    }
    px(x, y) {
        return this.fb[y * exports.SCR_W + x];
    }
    /** 런 단위로 자르며 그린다. 픽셀마다 조건을 걸지 않는 것이 도스식이다.
     *
     *  세로는 행 통째로 건너뛰고, 가로는 런 하나를 [a,b) 로 잘라 채운다.
     *  Uint8Array.fill(v, a, b) 이 그 자리를 그대로 옮긴 것이라 루프보다 빠르다. */
    blitRle(spr, x, y, level = 15) {
        const light = this.light;
        const fb = this.fb;
        const top = y - spr.oy;
        const left = x - spr.ox;
        const rows = spr.rows;
        for (let r = 0; r < spr.h; r++) {
            const py = top + r;
            if (py < 0 || py >= exports.SCR_H)
                continue;
            const base = py * exports.SCR_W;
            let px = left;
            for (const run of rows[r]) {
                const count = run[0];
                const color = run[1];
                if (color) {
                    const a = px > 0 ? px : 0;
                    let b = px + count;
                    if (b > exports.SCR_W)
                        b = exports.SCR_W;
                    if (a < b) {
                        const v = light[level * exports.PAL_SIZE + color];
                        fb.fill(v, base + a, base + b);
                    }
                }
                px += count;
                if (px >= exports.SCR_W)
                    break;
            }
        }
    }
}
exports.Frame = Frame;
/** 더티 렉트 — 바뀐 곳만 다시 올리기 위한 사각형 목록. */
class Dirty {
    constructor() {
        this.rects = [];
    }
    add(x0, y0, w0, h0) {
        let x = x0;
        let y = y0;
        let w = w0;
        let h = h0;
        if (x < 0) {
            w += x;
            x = 0;
        }
        if (y < 0) {
            h += y;
            y = 0;
        }
        if (x + w > exports.SCR_W)
            w = exports.SCR_W - x;
        if (y + h > exports.SCR_H)
            h = exports.SCR_H - y;
        if (w > 0 && h > 0)
            this.rects.push([x, y, w, h]);
    }
    /** 겹치거나 맞닿은 사각형을 합친다. 낭비가 1.5배를 넘으면 그냥 둔다.
     *  마지막 정렬은 (y, x) 오름차순 — 동점에도 순서가 흔들리지 않도록
     *  w, h 까지 비교에 넣는다. JS 의 sort 는 안정 정렬이지만 기대지 않는다. */
    merge() {
        let changed = true;
        while (changed) {
            changed = false;
            const out = [];
            const used = new Array(this.rects.length).fill(false);
            for (let i = 0; i < this.rects.length; i++) {
                if (used[i])
                    continue;
                const ri = this.rects[i];
                let x = ri[0];
                let y = ri[1];
                let w = ri[2];
                let h = ri[3];
                for (let j = i + 1; j < this.rects.length; j++) {
                    if (used[j])
                        continue;
                    const rj = this.rects[j];
                    const x2 = rj[0];
                    const y2 = rj[1];
                    const w2 = rj[2];
                    const h2 = rj[3];
                    if (x + w < x2 || x2 + w2 < x || y + h < y2 || y2 + h2 < y)
                        continue;
                    const nx = x < x2 ? x : x2;
                    const ny = y < y2 ? y : y2;
                    const nr = x + w > x2 + w2 ? x + w : x2 + w2;
                    const nb = y + h > y2 + h2 ? y + h : y2 + h2;
                    if ((nr - nx) * (nb - ny) * 2 <= (w * h + w2 * h2) * 3) {
                        x = nx;
                        y = ny;
                        w = nr - nx;
                        h = nb - ny;
                        used[j] = true;
                        changed = true;
                    }
                }
                used[i] = true;
                out.push([x, y, w, h]);
            }
            this.rects = out;
        }
        this.rects.sort((a, b) => (a[1] - b[1]) || (a[0] - b[0]) || (a[2] - b[2]) || (a[3] - b[3]));
        return this.rects;
    }
}
exports.Dirty = Dirty;
/** 물 램프 구간만 왼쪽으로 n 칸 돌린다. 프레임버퍼는 건드리지 않는다. */
function cyclePalette(pal, n) {
    const span = exports.WATER_HI - exports.WATER_LO + 1;
    const k = n - span * Math.floor(n / span);
    const out = pal.slice();
    for (let i = 0; i < span; i++) {
        out[exports.WATER_LO + i] = pal[exports.WATER_LO + ((i + k) % span)];
    }
    return out;
}
/** 6비트 DAC -> 8비트. v*4 + v/16 이라 0 -> 0, 63 -> 255 가 정확히 맞는다. */
function expand6(v) {
    return v * 4 + Math.floor(v / 16);
}
/** P6 PPM. 머리말 15바이트 + 192,000바이트 = 192,015바이트. */
function toPpm(fb, pal) {
    const lut = new Uint8Array(exports.PAL_SIZE * 3);
    for (let i = 0; i < exports.PAL_SIZE; i++) {
        const c = pal[i];
        lut[i * 3] = expand6(c[0]);
        lut[i * 3 + 1] = expand6(c[1]);
        lut[i * 3 + 2] = expand6(c[2]);
    }
    const header = 'P6\n320 200\n255\n';
    const out = new Uint8Array(header.length + exports.SCR_W * exports.SCR_H * 3);
    for (let i = 0; i < header.length; i++)
        out[i] = header.charCodeAt(i);
    let j = header.length;
    for (let i = 0; i < exports.SCR_W * exports.SCR_H; i++) {
        const c = fb[i] * 3;
        out[j] = lut[c];
        out[j + 1] = lut[c + 1];
        out[j + 2] = lut[c + 2];
        j += 3;
    }
    return out;
}
  });
  __def('path', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Bucket = exports.DIAG_MIN = exports.STRAIGHT_MIN = exports.UNREACHED = exports.BUCKET_N = exports.MIN_MOVE = exports.CLIMB_MAX = exports.DIR_NAME = exports.STEP_BASE = exports.DIAG = exports.DIRY = exports.DIRX = void 0;
exports.passable = passable;
exports.stepOk = stepOk;
exports.stepCost = stepCost;
exports.octile = octile;
exports.dijkstra = dijkstra;
exports.astar = astar;
// 경로 탐색 — SPEC §8. 8방향 격자, 다익스트라(양동이 큐), A*(옥타일).
//
// 파이썬은 '아직 값이 없음'을 None 으로 적는다. TS 에서 (number | null)[] 로 옮기면
// 안쪽 루프마다 널 검사가 생겨 형이 바뀌고 느려지므로, -1 을 미도달 표식으로 쓰고
// Int32Array 에 담는다. 비용은 최대 몇천이라 int32 안에 넉넉히 들어간다.
const M = require("./gamemap");
//                       E  SE  S  SW  W  NW  N  NE
exports.DIRX = [1, 1, 0, -1, -1, -1, 0, 1];
exports.DIRY = [0, 1, 1, 1, 0, -1, -1, -1];
exports.DIAG = [false, true, false, true, false, true, false, true];
exports.STEP_BASE = [10, 14, 10, 14, 10, 14, 10, 14];
exports.DIR_NAME = ['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE'];
exports.CLIMB_MAX = 1;
exports.MIN_MOVE = M.MIN_MOVE; // 8 (ROAD)
exports.BUCKET_N = 64; // 최대 간선 비용 floordiv(14*20,10)=28 보다 크면 된다
/** 미도달 표식. 파이썬의 None 자리다. */
exports.UNREACHED = -1;
function passable(m, x, y) {
    return m.inside(x, y) && M.MOVE[m.terrain(x, y)] > 0;
}
/** (x,y) 에서 방향 d 로 한 칸 갈 수 있는가.
 *
 *  마지막 조건이 '모서리 자르기 금지'다. 벽 두 장이 만나는 모서리를
 *  대각선으로 스쳐 지나가면 캐릭터가 벽을 뚫은 것처럼 보인다. */
function stepOk(m, x, y, d) {
    const nx = x + exports.DIRX[d];
    const ny = y + exports.DIRY[d];
    if (!passable(m, nx, ny))
        return false;
    const dh = m.height(nx, ny) - m.height(x, y);
    if (dh > exports.CLIMB_MAX || dh < -exports.CLIMB_MAX)
        return false;
    if (exports.DIAG[d]) {
        if (!passable(m, nx, y) || !passable(m, x, ny))
            return false;
    }
    return true;
}
/** 도착 칸의 지형으로 값을 매긴다. 떠나는 칸이 아니라. */
function stepCost(m, nx, ny, d) {
    return Math.floor((exports.STEP_BASE[d] * M.MOVE[m.terrain(nx, ny)]) / 10);
}
exports.STRAIGHT_MIN = Math.floor((10 * exports.MIN_MOVE) / 10); // 8
exports.DIAG_MIN = Math.floor((14 * exports.MIN_MOVE) / 10); // 11
/** 가장 싼 지형만 밟았을 때의 정확한 8방향 최단거리. (정리 8.1, 8.2)
 *
 *  흔히 쓰는 floordiv((10*(dx+dy) - 6*min) * 8, 10) 형태는 쓰지 않는다.
 *  내림이 두 번 들어가 (47,47) 에서 526 을 내놓는데 실제 최소 비용은 517 이다. */
function octile(ax, ay, bx, by) {
    let dx = ax - bx;
    if (dx < 0)
        dx = -dx;
    let dy = ay - by;
    if (dy < 0)
        dy = -dy;
    const hi = dx < dy ? dy : dx;
    const lo = dx < dy ? dx : dy;
    return exports.STRAIGHT_MIN * hi + (exports.DIAG_MIN - exports.STRAIGHT_MIN) * lo;
}
/** 원형 양동이 큐. 간선 비용이 [0, BUCKET_N) 이면 이진 힙과 같은 순서를 준다. (정리 8.3)
 *
 *  비지 않은 첫 양동이의 **마지막** 원소를 꺼낸다 — 스택 방식이라 동점 처리가
 *  결정적이다. 파이썬의 list.pop() 과 JS 의 Array.pop() 이 같은 동작이라 그대로 옮았다. */
class Bucket {
    constructor() {
        this.b = [];
        this.cur = 0;
        this.n = 0;
        for (let i = 0; i < exports.BUCKET_N; i++)
            this.b.push([]);
    }
    push(key, node) {
        this.b[key % exports.BUCKET_N].push([key, node]);
        this.n += 1;
    }
    popMin() {
        if (this.n === 0)
            return null;
        for (let i = 0; i < exports.BUCKET_N; i++) {
            const q = this.b[this.cur];
            if (q.length > 0) {
                this.n -= 1;
                return q.pop();
            }
            this.cur = (this.cur + 1) % exports.BUCKET_N;
        }
        return null;
    }
}
exports.Bucket = Bucket;
/** 시작점에서 모든 칸까지의 최소 비용. 못 가는 칸은 UNREACHED(-1). */
function dijkstra(m, sx, sy) {
    const w = m.w;
    const dist = new Int32Array(w * m.h).fill(exports.UNREACHED);
    if (!passable(m, sx, sy))
        return dist;
    dist[sy * w + sx] = 0;
    const q = new Bucket();
    q.push(0, sy * w + sx);
    for (;;) {
        const it = q.popMin();
        if (it === null)
            break;
        const g = it[0];
        const idx = it[1];
        const cur = dist[idx];
        if (cur !== exports.UNREACHED && g > cur)
            continue;
        const x = idx % w;
        const y = Math.floor(idx / w);
        for (let d = 0; d < 8; d++) {
            if (!stepOk(m, x, y, d))
                continue;
            const nx = x + exports.DIRX[d];
            const ny = y + exports.DIRY[d];
            const ng = g + stepCost(m, nx, ny, d);
            const ni = ny * w + nx;
            const dn = dist[ni];
            if (dn === exports.UNREACHED || ng < dn) {
                dist[ni] = ng;
                q.push(ng, ni);
            }
        }
    }
    return dist;
}
/** f = g + h 를 같은 양동이 큐에 넣는다. h 가 일관적이므로 f 는 경로를 따라
 *  단조 증가하고 한 걸음에 최대 28 늘어난다 — 활성 폭이 BUCKET_N 미만이다. */
function astar(m, sx, sy, gx, gy) {
    const w = m.w;
    if (!passable(m, sx, sy) || !passable(m, gx, gy)) {
        return { path: null, cost: exports.UNREACHED, expanded: 0 };
    }
    const gcost = new Int32Array(w * m.h).fill(exports.UNREACHED);
    const prev = new Int32Array(w * m.h).fill(-1);
    const closed = new Uint8Array(w * m.h);
    const si = sy * w + sx;
    const gi = gy * w + gx;
    gcost[si] = 0;
    const q = new Bucket();
    q.push(octile(sx, sy, gx, gy), si);
    let expanded = 0;
    for (;;) {
        const it = q.popMin();
        if (it === null)
            return { path: null, cost: exports.UNREACHED, expanded };
        const idx = it[1];
        if (closed[idx])
            continue;
        closed[idx] = 1;
        expanded += 1;
        if (idx === gi)
            break;
        const x = idx % w;
        const y = Math.floor(idx / w);
        const g = gcost[idx];
        for (let d = 0; d < 8; d++) {
            if (!stepOk(m, x, y, d))
                continue;
            const nx = x + exports.DIRX[d];
            const ny = y + exports.DIRY[d];
            const ni = ny * w + nx;
            if (closed[ni])
                continue;
            const ng = g + stepCost(m, nx, ny, d);
            const cn = gcost[ni];
            if (cn === exports.UNREACHED || ng < cn) {
                gcost[ni] = ng;
                prev[ni] = idx;
                q.push(ng + octile(nx, ny, gx, gy), ni);
            }
        }
    }
    const pathOut = [];
    let i = gi;
    while (i !== -1) {
        pathOut.push([i % w, Math.floor(i / w)]);
        i = prev[i];
    }
    pathOut.reverse();
    return { path: pathOut, cost: gcost[gi], expanded };
}
  });
  __def('los', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Fog = exports.SIGHT_R = exports.EYE = void 0;
exports.line = line;
exports.visible = visible;
// 시야·안개·조명 — SPEC §9.
//
// 브레젠험 직선 하나로 셋을 다 만든다. 시야는 그 선 위에 막는 것이 있는지,
// 안개는 본 적 있는지, 조명은 얼마나 먼지.
const M = require("./gamemap");
const fixed_1 = require("./fixed");
exports.EYE = 2;
exports.SIGHT_R = 9;
/** 브레젠험 정수 직선. 양 끝을 포함한다.
 *
 *  err 는 '이상적 직선에서 벗어난 양'을 2*dx 배로 확대해 정수로 들고 다니는 값이다.
 *  길이는 항상 max(|dx|,|dy|) + 1 이고, 걸음마다 x 나 y 가 정확히 1씩 움직인다. */
function line(x0, y0, x1, y1) {
    let dx = x1 - x0;
    if (dx < 0)
        dx = -dx;
    let dy = y1 - y0;
    if (dy < 0)
        dy = -dy;
    dy = -dy;
    const sx = x0 < x1 ? 1 : -1;
    const sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    let x = x0;
    let y = y0;
    const out = [];
    for (;;) {
        out.push([x, y]);
        if (x === x1 && y === y1)
            return out;
        const e2 = 2 * err;
        if (e2 >= dy) {
            err += dy;
            x += sx;
        }
        if (e2 <= dx) {
            err += dx;
            y += sy;
        }
    }
}
/** (sx,sy) 에서 (gx,gy) 가 보이는가. 중간 칸만 검사한다.
 *
 *  높이 규칙은 단순하다 — 양 끝보다 EYE-1 단계 넘게 솟은 칸이 있으면 막힌다.
 *  진짜 3D 광선을 쏘지 않는 이유는 도스 게임도 그러지 않았기 때문이다. */
function visible(m, sx, sy, gx, gy) {
    if (sx === gx && sy === gy)
        return true;
    if (!m.inside(gx, gy))
        return false;
    const hs = m.height(sx, sy);
    const hg = m.height(gx, gy);
    const top = (hs > hg ? hs : hg) + exports.EYE - 1;
    const pts = line(sx, sy, gx, gy);
    for (let i = 1; i < pts.length - 1; i++) {
        const p = pts[i];
        const x = p[0];
        const y = p[1];
        if (!m.inside(x, y))
            return false;
        if (M.OPAQUE[m.terrain(x, y)])
            return false;
        if (m.height(x, y) > top)
            return false;
    }
    return true;
}
/** 타일마다 2비트. bit0 = 본 적 있다, bit1 = 지금 보인다.
 *  값이 0..3 뿐이라 Uint8Array 로 충분하고, 세이브도 이 배열을 그대로 접는다. */
class Fog {
    constructor(w, h) {
        this.nSeen = 0;
        this.nVis = 0;
        this.w = w;
        this.h = h;
        this.bits = new Uint8Array(w * h);
    }
    isSeen(x, y) {
        return this.bits[y * this.w + x] % 2 === 1;
    }
    isVisible(x, y) {
        return Math.floor(this.bits[y * this.w + x] / 2) % 2 === 1;
    }
    countSeen() {
        return this.nSeen;
    }
    countVisible() {
        return this.nVis;
    }
    /** 비트에서 누적 개수를 다시 센다. 세이브를 되돌린 직후에 부른다.
     *
     *  개수는 세이브에 넣지 않는다 — 비트에서 유도되는 값이라 넣으면 같은 사실이
     *  두 곳에 적히고, 둘이 어긋나면 어느 쪽이 옳은지 알 수 없다. */
    recount() {
        let seen = 0;
        let vis = 0;
        const bits = this.bits;
        for (let i = 0; i < bits.length; i++) {
            const v = bits[i];
            if (v % 2 === 1)
                seen++;
            if (Math.floor(v / 2) % 2 === 1)
                vis++;
        }
        this.nSeen = seen;
        this.nVis = vis;
    }
    /** 지금 보이는 칸을 다시 세운다. 기억(bit0)은 지우지 않는다. */
    update(m, px, py) {
        const bits = this.bits;
        const w = this.w;
        for (let i = 0; i < bits.length; i++)
            bits[i] = bits[i] % 2;
        let x0 = px - exports.SIGHT_R;
        let x1 = px + exports.SIGHT_R;
        let y0 = py - exports.SIGHT_R;
        let y1 = py + exports.SIGHT_R;
        if (x0 < 0)
            x0 = 0;
        if (y0 < 0)
            y0 = 0;
        if (x1 > w - 1)
            x1 = w - 1;
        if (y1 > this.h - 1)
            y1 = this.h - 1;
        let seen = this.nSeen;
        let vis = 0;
        const rr = exports.SIGHT_R * exports.SIGHT_R;
        for (let y = y0; y <= y1; y++) {
            const dy = y - py;
            const row = y * w;
            for (let x = x0; x <= x1; x++) {
                const dx = x - px;
                // 정사각형이 아니라 원 안만 본다 — 사각형 모서리는 반경 밖이다
                if (dx * dx + dy * dy > rr)
                    continue;
                if (visible(m, px, py, x, y)) {
                    if (bits[row + x] === 0)
                        seen += 1;
                    bits[row + x] = 3; // 지금 보이면 본 적도 있는 것이다
                    vis += 1;
                }
            }
        }
        this.nSeen = seen;
        this.nVis = vis;
    }
    /** 조명 단계 0..15. 지금 보이면 거리에 따라, 기억만 있으면 4, 아니면 0. */
    lightOf(x, y, px, py) {
        const v = this.bits[y * this.w + x];
        if (Math.floor(v / 2) % 2) {
            const d = (0, fixed_1.octDist)((x - px) * 256, (y - py) * 256);
            const l = 15 - Math.floor((8 * d) / (exports.SIGHT_R * 256));
            if (l < 7)
                return 7;
            if (l > 15)
                return 15;
            return l;
        }
        if (v % 2)
            return 4;
        return 0;
    }
}
exports.Fog = Fog;
  });
  __def('dice', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.dist = dist;
exports.roll = roll;
exports.toHit = toHit;
exports.pHit = pHit;
exports.attack = attack;
exports.xpToNext = xpToNext;
/** n개의 m면 주사위 합 분포. dist(n,m)[s] = 합이 s 인 경우의 수. O(n^2 * m). */
function dist(n, m) {
    let c = [1];
    for (let k = 0; k < n; k++) {
        const c2 = new Array(c.length + m).fill(0);
        for (let s = 0; s < c.length; s++) {
            const v = c[s];
            if (v) {
                for (let f = 1; f <= m; f++)
                    c2[s + f] = c2[s + f] + v;
            }
        }
        c = c2;
    }
    return c;
}
/** 실제 굴림. 난수 소비 순서가 명세의 일부다. */
function roll(r, n, m) {
    let t = 0;
    for (let i = 0; i < n; i++) {
        const v = r.next();
        t += (v - m * Math.floor(v / m)) + 1;
    }
    return t;
}
/** 1d20 이 이 값 이상이면 명중. */
function toHit(atk, dfn) {
    return 11 + dfn - atk;
}
/** 20면 중 명중하는 눈의 수. 1은 언제나 실패, 20은 언제나 성공. */
function pHit(atk, dfn) {
    const v = 21 - toHit(atk, dfn);
    if (v < 1)
        return 1;
    if (v > 19)
        return 19;
    return v;
}
/** 난수는 명중 굴림 한 번, 그리고 명중했을 때만 피해 굴림 dn번을 쓴다.
 *  빗나갔을 때 피해 굴림을 건너뛰는 것까지 명세다 — 안 그러면 난수 흐름이 갈린다. */
function attack(r, atk, dfn, dn, dm, dbonus, armor) {
    const v = r.next();
    const d20 = (v - 20 * Math.floor(v / 20)) + 1;
    if (d20 === 1)
        return { hit: false, dmg: 0, d20 };
    if (d20 !== 20 && d20 < toHit(atk, dfn))
        return { hit: false, dmg: 0, d20 };
    let dmg = roll(r, dn, dm) + dbonus - armor;
    if (dmg < 1)
        dmg = 1;
    return { hit: true, dmg, d20 };
}
/** 다음 레벨까지 필요한 경험치. 2차식이라 후반이 완만하게 무거워진다. */
function xpToNext(lv) {
    return 20 * lv * lv + 30 * lv;
}
  });
  __def('save', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MAGIC = exports.Reader = exports.CRC_TBL = exports.CRC_INIT = exports.CRC_POLY = void 0;
exports.crc16 = crc16;
exports.i32ToU32 = i32ToU32;
exports.u32ToI32 = u32ToI32;
exports.packState = packState;
exports.unpackState = unpackState;
// 세이브와 CRC — SPEC §11.
//
// 전부 빅 엔디언이다. 바이트 순서를 손으로 나눠 쓰면 어느 언어에서든 같다.
// DataView 나 Buffer.writeUInt32BE 를 쓰면 더 짧아지지만, 파이썬·루아 판과
// 코드가 갈라져 '같은 형식인가'를 눈으로 확인할 수 없게 된다.
// xor 도 마찬가지 이유로 JS 의 ^ 대신 fixed 의 산술 xor 를 쓴다.
const fixed_1 = require("./fixed");
exports.CRC_POLY = 0x1021;
exports.CRC_INIT = 0xffff;
/** CRC-16/CCITT-FALSE 표. 다항식 나눗셈을 바이트 단위로 미리 접어 둔 것이다. */
function makeTable() {
    const tbl = [];
    for (let i = 0; i < 256; i++) {
        let c = i * 256;
        for (let k = 0; k < 8; k++) {
            const hi = c >= 32768;
            c = (c * 2) % 65536;
            if (hi)
                c = (0, fixed_1.xor16)(c, exports.CRC_POLY);
        }
        tbl.push(c);
    }
    return tbl;
}
exports.CRC_TBL = makeTable();
/** 표 구동 CRC. 한 바이트에 xor 두 번과 표 조회 한 번.
 *  (c*256) mod 65536 은 하위 바이트가 0 이므로 상위 바이트만 8비트 xor 하면 된다. */
function crc16(data) {
    let c = exports.CRC_INIT;
    for (let i = 0; i < data.length; i++) {
        const b = data[i];
        const t = exports.CRC_TBL[(0, fixed_1.xor8)(Math.floor(c / 256), b)];
        c = (0, fixed_1.xor8)(c % 256, Math.floor(t / 256)) * 256 + (t % 256);
    }
    return c;
}
// ---------------------------------------------------------------- 정수 인코딩
function i32ToU32(v) {
    return v - 4294967296 * Math.floor(v / 4294967296);
}
function u32ToI32(v) {
    return v >= 2147483648 ? v - 4294967296 : v;
}
function u8(out, v) {
    out.push(v % 256);
}
function u16(out, v) {
    out.push(Math.floor(v / 256) % 256);
    out.push(v % 256);
}
function u32(out, v0) {
    const v = i32ToU32(v0);
    out.push(Math.floor(v / 16777216));
    out.push(Math.floor(v / 65536) % 256);
    out.push(Math.floor(v / 256) % 256);
    out.push(v % 256);
}
class Reader {
    constructor(d) {
        this.i = 0;
        this.d = d;
    }
    u8() {
        const v = this.d[this.i];
        this.i += 1;
        return v;
    }
    u16() {
        return this.u8() * 256 + this.u8();
    }
    u32() {
        return this.u16() * 65536 + this.u16();
    }
    i32() {
        return u32ToI32(this.u32());
    }
}
exports.Reader = Reader;
exports.MAGIC = [0x49, 0x53, 0x4f, 0x31]; // 'ISO1'
/** 게임 상태를 바이트열로. 끝에 CRC 2바이트가 붙는다. */
function packState(g) {
    const out = exports.MAGIC.slice();
    u32(out, g.tickN);
    u32(out, g.rng.s);
    u32(out, i32ToU32(g.camX));
    u32(out, i32ToU32(g.camY));
    u16(out, g.ents.length);
    for (const e of g.ents) {
        u8(out, e.kind);
        u32(out, i32ToU32(e.fx));
        u32(out, i32ToU32(e.fy));
        u8(out, e.h);
        u16(out, e.hp);
        u16(out, e.maxhp);
        u8(out, e.lv);
        u32(out, e.xp);
        u8(out, e.atk);
        u8(out, e.dfn);
        u8(out, e.armor);
        u8(out, e.dirn);
        u8(out, e.alive);
    }
    // 안개는 타일 4개에 1바이트. 2비트씩 접어 넣는다.
    const bits = g.fog.bits;
    const n = bits.length;
    u16(out, Math.floor((n + 3) / 4));
    let i = 0;
    while (i < n) {
        let b = 0;
        let p = 1;
        for (let k = 0; k < 4; k++) {
            const v = i + k < n ? bits[i + k] : 0;
            b += (v % 4) * p;
            p *= 4;
        }
        out.push(b);
        i += 4;
    }
    u16(out, crc16(out));
    return Uint8Array.from(out);
}
/** 세이브를 게임에 되돌린다. CRC 가 맞지 않으면 Error. */
function unpackState(data, g) {
    for (let i = 0; i < 4; i++) {
        if (data[i] !== exports.MAGIC[i])
            throw new Error('세이브 매직이 다르다');
    }
    const want = data[data.length - 2] * 256 + data[data.length - 1];
    if (crc16(data.subarray(0, data.length - 2)) !== want) {
        throw new Error('세이브가 손상됐다 (CRC 불일치)');
    }
    const r = new Reader(data);
    r.i = 4;
    g.tickN = r.u32();
    g.rng.s = r.u32();
    g.camX = r.i32();
    g.camY = r.i32();
    const cnt = r.u16();
    if (cnt !== g.ents.length) {
        throw new Error('엔티티 수가 ' + g.ents.length + ' 여야 하는데 ' + cnt);
    }
    for (const e of g.ents) {
        e.kind = r.u8();
        e.fx = r.i32();
        e.fy = r.i32();
        e.h = r.u8();
        e.hp = r.u16();
        e.maxhp = r.u16();
        e.lv = r.u8();
        e.xp = r.u32();
        e.atk = r.u8();
        e.dfn = r.u8();
        e.armor = r.u8();
        e.dirn = r.u8();
        e.alive = r.u8();
    }
    const nb = r.u16();
    const bits = g.fog.bits;
    const n = bits.length;
    for (let j = 0; j < nb; j++) {
        const b = r.u8();
        let p = 1;
        for (let k = 0; k < 4; k++) {
            const i = j * 4 + k;
            if (i < n)
                bits[i] = Math.floor(b / p) % 4;
            p *= 4;
        }
    }
    // 비트만 되돌리고 누적 개수를 그대로 두면, 되돌린 뒤의 트레이스가
    // 복원된 상태의 함수가 아니게 된다. 개수는 비트에서 다시 센다.
    g.fog.recount();
    return g;
}
  });
  __def('game', function (exports, require, module) {
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Game = exports.PLACE_NPC = exports.PLACE_CHEST = exports.PLACE_MON = exports.Entity = exports.SPRDIR = exports.K_NPC = exports.K_CHEST = exports.K_MON = exports.K_PLAYER = exports.GAME_SEED = exports.PATH_EVERY = exports.ATTACK_EVERY = exports.AGGRO_R = exports.DIAG_FACTOR = exports.MON_SPEED = exports.SPEED = exports.GOLDEN = exports.ROOT = void 0;
exports.runScriptTrace = runScriptTrace;
// 게임 상태와 틱 — SPEC §12.
//
// 한 틱은 PIT 기본 분주(18.2065 Hz) 한 번이다. 고정 타임스텝이라
// 프레임을 몇 장 그리든 결과가 같다 — 세 언어의 트레이스를 바이트로 견줄 수 있는 이유다.
const fs = require("fs");
const path = require("path");
const CAM = require("./camera");
const DICE = require("./dice");
const M = require("./gamemap");
const LOS = require("./los");
const P = require("./path");
const PR = require("./proj");
const RA = require("./raster");
const SV = require("./save");
const SD = require("./sortdag");
const fixed_1 = require("./fixed");
const rng_1 = require("./rng");
exports.ROOT = path.resolve(__dirname, '..', '..', '..');
exports.GOLDEN = path.join(exports.ROOT, 'golden');
exports.SPEED = 13107; // 한 틱에 0.2타일
exports.MON_SPEED = 9830; // 몬스터는 조금 느리다 (0.15타일)
exports.DIAG_FACTOR = 46341; // round(65536 / sqrt(2))
exports.AGGRO_R = 7;
exports.ATTACK_EVERY = 12;
exports.PATH_EVERY = 8;
exports.GAME_SEED = 20260906;
exports.K_PLAYER = 0;
exports.K_MON = 1;
exports.K_CHEST = 2;
exports.K_NPC = 3;
// 8방향 -> 스프라이트 4방향. 화면에서 오른쪽아래/왼쪽아래/오른쪽위/왼쪽위 넷이면 족하다.
exports.SPRDIR = [0, 0, 1, 1, 3, 3, 2, 2];
class Entity {
    constructor(eid, kind, tx, ty) {
        this.h = 0;
        this.hp = 1;
        this.maxhp = 1;
        this.lv = 1;
        this.xp = 0;
        this.atk = 0;
        this.dfn = 0;
        this.armor = 0;
        this.dirn = 2;
        this.alive = 1;
        this.anim = 0;
        this.cool = 0;
        this.path = null;
        this.eid = eid;
        this.kind = kind;
        this.fx = tx * fixed_1.FP_ONE + fixed_1.FP_ONE / 2; // 타일 중앙
        this.fy = ty * fixed_1.FP_ONE + fixed_1.FP_ONE / 2;
    }
    tile() {
        return [(0, fixed_1.fpFloor)(this.fx), (0, fixed_1.fpFloor)(this.fy)];
    }
}
exports.Entity = Entity;
exports.PLACE_MON = [
    [20, 20], [28, 21], [21, 28], [27, 27], [24, 14], [24, 40],
];
exports.PLACE_CHEST = [[22, 22], [26, 26], [24, 20]];
exports.PLACE_NPC = [[23, 25], [25, 23]];
class Game {
    constructor() {
        this.tickN = 0;
        this.cycleBreaks = 0;
        this.palPhase = 0;
        this.slot = null;
        this.inDir = -1;
        this.inAct = 0;
        this.inAtk = 0;
        this.ents = [];
        this.camX = 0;
        this.camY = 0;
        this.frame = null;
        this.spr = null;
        this.map = M.genMap();
        this.rng = new rng_1.Rng(exports.GAME_SEED);
        this.fog = new LOS.Fog(M.MAP_W, M.MAP_H);
        this.buildEntities();
        const p0 = this.ents[0];
        const [px, py] = PR.worldToScreen(p0.fx, p0.fy, p0.h);
        const c = CAM.clampCam(px - PR.SCR_W / 2, py - PR.SCR_H / 2);
        this.camX = c[0];
        this.camY = c[1];
        const t0 = p0.tile();
        this.fog.update(this.map, t0[0], t0[1]);
    }
    // ------------------------------------------------------------ 초기 배치
    buildEntities() {
        const p = new Entity(0, exports.K_PLAYER, 24, 34);
        p.hp = 60;
        p.maxhp = 60;
        p.atk = 4;
        p.dfn = 3;
        p.armor = 2;
        this.ents.push(p);
        exports.PLACE_MON.forEach((pos, k) => {
            const e = new Entity(k + 1, exports.K_MON, pos[0], pos[1]);
            e.hp = 8 + k;
            e.maxhp = 8 + k;
            e.atk = 1;
            e.dfn = 0;
            e.armor = 0;
            this.ents.push(e);
        });
        for (const pos of exports.PLACE_CHEST) {
            this.ents.push(new Entity(this.ents.length, exports.K_CHEST, pos[0], pos[1]));
        }
        for (const pos of exports.PLACE_NPC) {
            this.ents.push(new Entity(this.ents.length, exports.K_NPC, pos[0], pos[1]));
        }
        for (const e of this.ents) {
            const t = e.tile();
            e.h = this.map.height(t[0], t[1]);
        }
    }
    // ------------------------------------------------------------ 이동
    canStand(e, fx, fy) {
        const tx = (0, fixed_1.fpFloor)(fx);
        const ty = (0, fixed_1.fpFloor)(fy);
        if (!P.passable(this.map, tx, ty))
            return false;
        const dh = this.map.height(tx, ty) - e.h;
        return -P.CLIMB_MAX <= dh && dh <= P.CLIMB_MAX;
    }
    /** 방향 d 로 한 틱만큼. 막히면 축을 하나씩 떼어 미끄러진다.
     *
     *  도스 RPG 의 조작감은 이 '미끄러짐'에서 온다. 벽에 비스듬히 부딪혔을 때
     *  딱 멈추면 답답하고, 벽을 타고 흐르면 자연스럽다. */
    moveEntity(e, d, speed) {
        let dx = P.DIRX[d] * speed;
        let dy = P.DIRY[d] * speed;
        if (P.DIAG[d]) {
            dx = (0, fixed_1.fpMul)(dx, exports.DIAG_FACTOR);
            dy = (0, fixed_1.fpMul)(dy, exports.DIAG_FACTOR);
        }
        const nfx = e.fx + dx;
        const nfy = e.fy + dy;
        let moved = false;
        if (this.canStand(e, nfx, nfy)) {
            e.fx = nfx;
            e.fy = nfy;
            moved = true;
        }
        else if (dx && this.canStand(e, nfx, e.fy)) {
            e.fx = nfx;
            moved = true;
        }
        else if (dy && this.canStand(e, e.fx, nfy)) {
            e.fy = nfy;
            moved = true;
        }
        e.dirn = d;
        const t = e.tile();
        e.h = this.map.height(t[0], t[1]);
        if (moved)
            e.anim += 1;
        return moved;
    }
    // ------------------------------------------------------------ 전투
    adjacent(a, b) {
        const ta = a.tile();
        const tb = b.tile();
        const dx = ta[0] - tb[0];
        const dy = ta[1] - tb[1];
        return dx >= -1 && dx <= 1 && dy >= -1 && dy <= 1;
    }
    levelUp(a) {
        while (a.xp >= DICE.xpToNext(a.lv)) {
            a.xp -= DICE.xpToNext(a.lv);
            a.lv += 1;
            const v = this.rng.next();
            a.maxhp += 4 + (v - 5 * Math.floor(v / 5));
            a.hp = a.maxhp;
            a.atk += 1;
            if (a.lv % 2 === 0)
                a.dfn += 1;
        }
    }
    doAttack(a, b) {
        const res = DICE.attack(this.rng, a.atk, b.dfn, 1, 6, a.atk, b.armor);
        if (!res.hit)
            return false;
        b.hp -= res.dmg;
        if (b.hp <= 0) {
            b.hp = 0;
            b.alive = 0;
            if (a.kind === exports.K_PLAYER) {
                a.xp += 20 + 5 * b.maxhp;
                this.levelUp(a);
            }
        }
        return true;
    }
    // ------------------------------------------------------------ 한 틱
    /** SPEC §12.2 의 순서를 그대로. 순서가 곧 명세다. */
    tick() {
        const p = this.ents[0];
        // 1~2. 입력과 플레이어 이동
        if (this.inDir >= 0)
            this.moveEntity(p, this.inDir, exports.SPEED);
        // 3. 몬스터
        const pt = p.tile();
        const ptx = pt[0];
        const pty = pt[1];
        for (const e of this.ents) {
            if (e.kind !== exports.K_MON || !e.alive)
                continue;
            const et = e.tile();
            const etx = et[0];
            const ety = et[1];
            const dx = etx - ptx;
            const dy = ety - pty;
            const near = dx >= -exports.AGGRO_R && dx <= exports.AGGRO_R && dy >= -exports.AGGRO_R && dy <= exports.AGGRO_R;
            if (!(near && LOS.visible(this.map, etx, ety, ptx, pty))) {
                e.path = null;
                continue;
            }
            if (this.adjacent(e, p)) {
                if (e.cool <= 0) {
                    this.doAttack(e, p);
                    e.cool = exports.ATTACK_EVERY;
                }
                else {
                    e.cool -= 1;
                }
                continue;
            }
            if (e.cool > 0)
                e.cool -= 1;
            if (e.path === null || this.tickN % exports.PATH_EVERY === 0) {
                e.path = P.astar(this.map, etx, ety, ptx, pty).path;
            }
            if (e.path !== null && e.path.length > 1) {
                const nxt = e.path[1];
                const nx = nxt[0];
                const ny = nxt[1];
                let d = -1;
                for (let k = 0; k < 8; k++) {
                    if (P.DIRX[k] === nx - etx && P.DIRY[k] === ny - ety) {
                        d = k;
                        break;
                    }
                }
                if (d >= 0) {
                    this.moveEntity(e, d, exports.MON_SPEED);
                    const nt = e.tile();
                    if (nt[0] === nx && nt[1] === ny)
                        e.path = e.path.slice(1);
                }
            }
        }
        // 4. 플레이어 명령
        if (this.inAtk) {
            for (const e of this.ents) {
                if (e.kind === exports.K_MON && e.alive && this.adjacent(p, e)) {
                    this.doAttack(p, e);
                    break;
                }
            }
        }
        if (this.inAct) {
            for (const e of this.ents) {
                if (e.kind === exports.K_CHEST && e.alive && this.adjacent(p, e)) {
                    e.alive = 0;
                    p.xp += 30;
                    this.levelUp(p);
                    break;
                }
            }
        }
        // 5. 안개와 조명
        this.fog.update(this.map, ptx, pty);
        // 6. 카메라
        const s = PR.worldToScreen(p.fx, p.fy, p.h);
        const c = CAM.follow(this.camX, this.camY, s[0], s[1]);
        this.camX = c[0];
        this.camY = c[1];
        // 7. 틱
        this.tickN += 1;
        this.palPhase = Math.floor(this.tickN / 4);
    }
    // ------------------------------------------------------------ 트레이스
    traceLine() {
        const p = this.ents[0];
        let mon = 0;
        for (const e of this.ents)
            if (e.kind === exports.K_MON && e.alive)
                mon += 1;
        // 세이브 끝에 붙은 CRC 를 그대로 읽는다. 세이브 전체를 다시 crc16 하면
        // 언제나 0이 나온다 — CCITT-FALSE 의 성질이라 값으로는 쓸모가 없다.
        const blob = SV.packState(this);
        const crc = blob[blob.length - 2] * 256 + blob[blob.length - 1];
        return '{"t":' + this.tickN + ',"px":' + p.fx + ',"py":' + p.fy + ',"ph":' + p.h
            + ',"hp":' + p.hp + ',"lv":' + p.lv + ',"xp":' + p.xp
            + ',"rng":' + this.rng.s + ',"cam":[' + this.camX + ',' + this.camY + ']'
            + ',"seen":' + this.fog.countSeen() + ',"vis":' + this.fog.countVisible()
            + ',"mon":' + mon + ',"crc":' + crc + '}';
    }
    /** 골든 시나리오를 돌린다. emit 이 있으면 매 틱 한 줄씩 넘긴다.
     *
     *  limit 을 주면 그만큼 '진행한 틱' 뒤에 멈춘다. tick_n 이 아니라
     *  실제로 돌린 횟수다 — load 가 시계를 되돌리기 때문이다. */
    runScript(scriptPath, emit, limit) {
        return this.runScriptText(fs.readFileSync(scriptPath ?? path.join(exports.GOLDEN, 'script.txt'), 'utf8'), emit, limit);
    }
    /** 시나리오 문자열을 그대로 돌린다. 파일 읽기와 나눠 둔 것은 브라우저 때문이다. */
    runScriptText(text, emit, limit) {
        let done = 0;
        for (const raw of text.split('\n')) {
            const line = raw.trim();
            if (!line || line.startsWith('#'))
                continue;
            const q = line.split(/\s+/);
            const cmd = q[0];
            if (cmd === 'mark') {
                if (emit)
                    emit('{"mark":"' + q[1] + '","t":' + this.tickN + '}');
                continue;
            }
            if (cmd === 'save') {
                this.slot = SV.packState(this);
                continue;
            }
            if (cmd === 'load') {
                if (this.slot !== null)
                    SV.unpackState(this.slot, this);
                continue;
            }
            let n;
            if (cmd === 'hold') {
                const d = P.DIR_NAME.indexOf(q[1]);
                n = parseInt(q[2], 10);
                this.inDir = d;
                this.inAct = 0;
                this.inAtk = 0;
            }
            else if (cmd === 'wait') {
                n = parseInt(q[1], 10);
                this.inDir = -1;
                this.inAct = 0;
                this.inAtk = 0;
            }
            else if (cmd === 'act') {
                n = 1;
                this.inDir = -1;
                this.inAct = 1;
                this.inAtk = 0;
            }
            else if (cmd === 'atk') {
                n = 1;
                this.inDir = -1;
                this.inAct = 0;
                this.inAtk = 1;
            }
            else {
                throw new Error('모르는 명령: ' + cmd);
            }
            for (let k = 0; k < n; k++) {
                this.tick();
                done += 1;
                if (emit)
                    emit(this.traceLine());
                if (limit !== undefined && limit !== null && done >= limit) {
                    this.inDir = -1;
                    this.inAct = 0;
                    this.inAtk = 0;
                    return this;
                }
            }
        }
        this.inDir = -1;
        this.inAct = 0;
        this.inAtk = 0;
        return this;
    }
    // ------------------------------------------------------------ 렌더
    /** 스프라이트를 밖에서 넣는다. 브라우저에는 파일이 없기 때문이다. */
    setSprites(list) {
        this.spr = list;
    }
    sprites() {
        if (this.spr === null)
            this.spr = RA.loadSprites();
        return this.spr;
    }
    /** 정렬에 넣을 상자들. 지형 기둥과 물체를 한 통에 넣는다.
     *
     *  지형을 빼고 물체끼리만 정렬하면 절벽 뒤에 선 캐릭터가 절벽 위로 뜬다. */
    boxes() {
        const m = this.map;
        const [tx0, ty0, tx1, ty1] = PR.visibleRange(this.camX, this.camY, this.camX + PR.SCR_W, this.camY + PR.SCR_H);
        const boxes = [];
        const kinds = [];
        for (let ty = ty0; ty <= ty1; ty++) {
            for (let tx = tx0; tx <= tx1; tx++) {
                const h = m.height(tx, ty);
                boxes.push([boxes.length, tx, ty, 0, tx + 1, ty + 1, h + 1]);
                kinds.push({ t: 'tile', tx, ty });
            }
        }
        for (const e of this.ents) {
            if (!e.alive && e.kind === exports.K_MON)
                continue;
            const t = e.tile();
            const tx = t[0];
            const ty = t[1];
            if (!(tx0 <= tx && tx <= tx1 && ty0 <= ty && ty <= ty1))
                continue;
            boxes.push([boxes.length, tx, ty, e.h, tx + 1, ty + 1, e.h + 3]);
            kinds.push({ t: 'ent', e });
        }
        // 장식: 숲에는 나무, 바위 지형에는 바위. 배치는 좌표만으로 정해 결정적이다.
        for (let ty = ty0; ty <= ty1; ty++) {
            for (let tx = tx0; tx <= tx1; tx++) {
                const t = m.terrain(tx, ty);
                const h = m.height(tx, ty);
                if (t === M.T_FOREST && (tx * 7 + ty * 13) % 5 === 0) {
                    boxes.push([boxes.length, tx, ty, h, tx + 1, ty + 1, h + 4]);
                    kinds.push({ t: 'spr', sid: 46, tx, ty, h });
                }
                else if (t === M.T_ROCK && (tx * 11 + ty * 5) % 7 === 0) {
                    boxes.push([boxes.length, tx, ty, h, tx + 1, ty + 1, h + 2]);
                    kinds.push({ t: 'spr', sid: 47, tx, ty, h });
                }
            }
        }
        return [boxes, kinds];
    }
    /** 한 프레임. 정렬 결과대로 지형 기둥과 물체를 차례로 올린다. */
    render() {
        const spr = this.sprites();
        if (this.frame === null)
            this.frame = new RA.Frame();
        const f = this.frame;
        f.clear(0);
        const m = this.map;
        const [boxes, kinds] = this.boxes();
        const [order, breaks] = SD.topoSort(boxes);
        this.cycleBreaks += breaks;
        const pt = this.ents[0].tile();
        const ptx = pt[0];
        const pty = pt[1];
        for (const bid of order) {
            const kind = kinds[bid];
            if (kind.t === 'tile') {
                const tx = kind.tx;
                const ty = kind.ty;
                const lv = this.fog.lightOf(tx, ty, ptx, pty);
                if (lv === 0)
                    continue;
                const t = m.terrain(tx, ty);
                const h = m.height(tx, ty);
                if (h === 0) {
                    const s = PR.tileToScreen(tx, ty, 0);
                    f.blitRle(spr[t], s[0] - this.camX, s[1] - this.camY, lv);
                }
                else {
                    for (let k = 1; k <= h; k++) {
                        const s = PR.tileToScreen(tx, ty, k);
                        f.blitRle(spr[16 + t], s[0] - this.camX, s[1] - this.camY, lv);
                    }
                }
            }
            else if (kind.t === 'ent') {
                const e = kind.e;
                const t = e.tile();
                const lv = this.fog.lightOf(t[0], t[1], ptx, pty);
                if (lv === 0)
                    continue;
                const s = PR.worldToScreen(e.fx, e.fy, e.h);
                const sy = s[1] + PR.HH;
                let sid;
                if (e.kind === exports.K_PLAYER) {
                    sid = 32 + exports.SPRDIR[e.dirn] * 2 + (Math.floor(e.anim / 4) % 2);
                }
                else if (e.kind === exports.K_MON) {
                    sid = 40 + ((Math.floor(this.tickN / 6) + e.eid) % 2);
                }
                else if (e.kind === exports.K_CHEST) {
                    sid = e.alive ? 42 : 43;
                }
                else {
                    sid = 44 + (e.eid % 2);
                }
                f.blitRle(spr[sid], s[0] - this.camX, sy - this.camY, lv);
            }
            else {
                const lv = this.fog.lightOf(kind.tx, kind.ty, ptx, pty);
                if (lv === 0)
                    continue;
                const s = PR.tileToScreen(kind.tx, kind.ty, kind.h);
                f.blitRle(spr[kind.sid], s[0] - this.camX, s[1] + PR.HH - this.camY, lv);
            }
        }
        return f.fb;
    }
    renderPpm() {
        const pal = RA.cyclePalette(RA.loadPalette(), this.palPhase);
        return RA.toPpm(this.render(), pal);
    }
}
exports.Game = Game;
function runScriptTrace(scriptPath) {
    const g = new Game();
    const out = [];
    g.runScript(scriptPath ?? null, (l) => out.push(l));
    return out.join('\n') + '\n';
}
  });
  __def('web/data', function (exports, require, module) {
"use strict";
// 이 파일은 tools/gen_webdata.py 가 만든다. 손으로 고치지 말 것.
// 골든 데이터를 브라우저용으로 박아 넣은 것이고, 내용은 golden/ 과 같다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.SCRIPT_TXT = exports.TILES_RLE = exports.PALETTE_TXT = void 0;
/** golden/palette.txt (3128바이트) */
exports.PALETTE_TXT = `ISORPG-PAL 1 256
0 0 0 0
1 0 0 42
2 0 42 0
3 0 42 42
4 42 0 0
5 42 0 42
6 42 21 0
7 42 42 42
8 21 21 21
9 21 21 63
10 21 63 21
11 21 63 63
12 63 21 21
13 63 21 63
14 63 63 21
15 63 63 63
16 0 2 14
17 1 5 17
18 2 7 21
19 4 10 24
20 5 12 27
21 6 15 30
22 7 17 34
23 8 20 37
24 10 22 40
25 11 25 43
26 12 27 47
27 13 30 50
28 14 32 53
29 16 35 56
30 17 37 60
31 18 40 63
32 22 16 6
33 25 19 8
34 27 22 10
35 30 24 12
36 33 27 13
37 36 30 15
38 38 33 17
39 41 36 19
40 44 38 21
41 47 41 23
42 49 44 25
43 52 47 27
44 55 50 28
45 58 52 30
46 60 55 32
47 63 58 34
48 4 14 4
49 6 17 6
50 8 20 7
51 10 23 9
52 12 26 10
53 14 29 12
54 16 32 14
55 18 35 15
56 20 39 17
57 22 42 18
58 24 45 20
59 26 48 22
60 28 51 23
61 30 54 25
62 32 57 26
63 34 60 28
64 14 9 4
65 16 11 5
66 19 13 6
67 21 14 8
68 23 16 9
69 25 18 10
70 28 20 11
71 30 22 12
72 32 23 14
73 34 25 15
74 37 27 16
75 39 29 17
76 41 31 18
77 43 32 20
78 46 34 21
79 48 36 22
80 10 10 12
81 13 13 15
82 16 16 18
83 18 18 21
84 21 21 24
85 24 24 27
86 27 27 30
87 30 30 33
88 32 32 35
89 35 35 38
90 38 38 41
91 41 41 44
92 44 44 47
93 46 46 50
94 49 49 53
95 52 52 56
96 2 9 3
97 3 11 4
98 4 14 5
99 6 16 6
100 7 18 7
101 8 21 8
102 9 23 9
103 10 25 10
104 12 28 11
105 13 30 12
106 14 32 13
107 15 35 14
108 16 37 15
109 18 39 16
110 19 42 17
111 20 44 18
112 21 14 6
113 23 16 7
114 26 18 9
115 28 20 10
116 31 22 11
117 33 24 12
118 36 26 14
119 38 28 15
120 41 31 16
121 43 33 17
122 46 35 19
123 48 37 20
124 51 39 21
125 53 41 22
126 56 43 24
127 58 45 25
128 10 10 13
129 12 12 16
130 15 15 18
131 17 17 21
132 19 19 23
133 21 21 26
134 24 24 29
135 26 26 31
136 28 28 34
137 30 30 36
138 33 33 39
139 35 35 42
140 37 37 44
141 39 39 47
142 42 42 49
143 44 44 52
144 15 13 11
145 17 15 13
146 20 18 15
147 22 20 17
148 25 22 19
149 27 25 21
150 30 27 23
151 32 29 25
152 35 32 28
153 37 34 30
154 40 36 32
155 42 39 34
156 45 41 36
157 47 43 38
158 50 46 40
159 52 48 42
160 12 7 2
161 14 8 3
162 16 10 3
163 18 11 4
164 21 13 5
165 23 14 5
166 25 15 6
167 27 17 7
168 29 18 7
169 31 20 8
170 33 21 9
171 35 22 9
172 38 24 10
173 40 25 11
174 42 27 11
175 44 28 12
176 24 26 32
177 26 28 34
178 29 31 36
179 31 33 38
180 34 36 40
181 36 38 42
182 38 40 44
183 41 43 46
184 43 45 49
185 46 48 51
186 48 50 53
187 50 52 55
188 53 55 57
189 55 57 59
190 58 60 61
191 60 62 63
192 6 10 6
193 7 12 7
194 9 14 8
195 10 16 10
196 11 17 11
197 13 19 12
198 14 21 13
199 15 23 14
200 17 25 16
201 18 27 17
202 19 29 18
203 21 31 19
204 22 32 20
205 23 34 22
206 25 36 23
207 26 38 24
208 20 2 0
209 23 5 1
210 26 8 1
211 29 10 2
212 31 13 2
213 34 16 3
214 37 19 3
215 40 22 4
216 43 24 4
217 46 27 5
218 49 30 5
219 52 33 6
220 54 36 6
221 57 38 7
222 60 41 7
223 63 44 8
224 18 10 6
225 21 12 8
226 24 15 10
227 27 17 12
228 30 20 14
229 33 22 16
230 36 24 18
231 39 27 20
232 42 29 22
233 45 32 24
234 48 34 26
235 51 36 28
236 54 39 30
237 57 41 32
238 60 44 34
239 63 46 36
240 10 2 6
241 13 3 7
242 16 4 9
243 20 6 10
244 23 7 12
245 26 8 13
246 29 9 15
247 32 10 16
248 36 12 18
249 39 13 19
250 42 14 21
251 45 15 22
252 48 16 24
253 52 18 25
254 55 19 27
255 58 20 28
`;
/** golden/tiles.rle (49788바이트) */
exports.TILES_RLE = `ISORPG-TILES 1 48
SPRITE 0 tile_0 32 16 16 0
16:0 1:27 15:0
14:0 1:24 1:25 1:22 1:25 1:24 13:0
12:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 11:0
10:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 9:0
8:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 7:0
6:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 5:0
4:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 3:0
2:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 1:0
1:0 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:20
3:0 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 2:0
5:0 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:20 4:0
7:0 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 6:0
9:0 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:20 8:0
11:0 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 10:0
13:0 1:20 1:25 1:22 1:25 1:22 1:25 1:20 12:0
15:0 1:23 1:22 1:23 14:0
SPRITE 1 tile_1 32 16 16 0
16:0 1:30 15:0
14:0 1:27 1:28 1:25 1:28 1:27 13:0
12:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 11:0
10:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 9:0
8:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 7:0
6:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 5:0
4:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 3:0
2:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 1:0
1:0 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:23
3:0 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 2:0
5:0 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:23 4:0
7:0 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 6:0
9:0 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:23 8:0
11:0 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 10:0
13:0 1:23 1:28 1:25 1:28 1:25 1:28 1:23 12:0
15:0 1:26 1:25 1:26 14:0
SPRITE 2 tile_2 32 16 16 0
16:0 1:46 15:0
14:0 1:43 2:41 1:44 1:43 13:0
12:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 11:0
10:0 1:43 1:44 3:41 1:44 3:41 1:44 2:41 1:43 9:0
8:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 7:0
6:0 1:43 2:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 1:43 5:0
4:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 3:0
2:0 1:43 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 2:41 1:43 1:0
1:0 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:39
3:0 1:39 1:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:42 2:0
5:0 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:39 4:0
7:0 1:42 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 1:41 1:39 6:0
9:0 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:39 8:0
11:0 1:39 1:41 1:44 3:41 1:44 3:41 1:42 10:0
13:0 1:39 1:44 1:41 1:44 1:41 1:44 1:39 12:0
15:0 1:42 1:41 1:39 14:0
SPRITE 3 tile_3 32 16 16 0
16:0 1:61 15:0
14:0 1:57 2:55 1:59 1:57 13:0
12:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 11:0
10:0 1:57 11:55 1:57 9:0
8:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 7:0
6:0 1:57 2:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 1:57 5:0
4:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 3:0
2:0 1:57 27:55 1:57 1:0
1:0 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:53
3:0 1:53 1:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:57 2:0
5:0 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:53 4:0
7:0 1:53 17:55 1:53 6:0
9:0 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:53 8:0
11:0 1:53 1:55 1:59 3:55 1:59 3:55 1:57 10:0
13:0 1:53 1:59 1:55 1:59 1:55 1:59 1:53 12:0
15:0 1:53 1:55 1:53 14:0
SPRITE 4 tile_4 32 16 16 0
16:0 1:76 15:0
14:0 1:73 2:71 1:74 1:73 13:0
12:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 11:0
10:0 1:73 1:74 3:71 1:74 3:71 1:74 2:71 1:73 9:0
8:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 7:0
6:0 1:73 2:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 1:73 5:0
4:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 3:0
2:0 1:73 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 2:71 1:73 1:0
1:0 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:69
3:0 1:69 1:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:72 2:0
5:0 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:69 4:0
7:0 1:72 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 1:71 1:69 6:0
9:0 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:69 8:0
11:0 1:69 1:71 1:74 3:71 1:74 3:71 1:72 10:0
13:0 1:69 1:74 1:71 1:74 1:71 1:74 1:69 12:0
15:0 1:72 1:71 1:69 14:0
SPRITE 5 tile_5 32 16 16 0
16:0 1:92 15:0
14:0 1:89 1:90 1:87 1:90 1:89 13:0
12:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 11:0
10:0 1:89 1:90 3:87 1:90 3:87 1:90 2:87 1:89 9:0
8:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 7:0
6:0 1:89 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:89 5:0
4:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 3:0
2:0 1:89 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 2:87 1:89 1:0
1:0 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:85
3:0 1:88 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:88 2:0
5:0 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:85 4:0
7:0 1:88 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 1:87 1:85 6:0
9:0 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:85 8:0
11:0 1:88 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:88 10:0
13:0 1:85 1:90 1:87 1:90 1:87 1:90 1:85 12:0
15:0 1:88 1:87 1:85 14:0
SPRITE 6 tile_6 32 16 16 0
16:0 1:107 15:0
14:0 1:103 1:105 1:101 1:105 1:103 13:0
12:0 1:107 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:107 11:0
10:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 9:0
8:0 1:107 2:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 1:107 7:0
6:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 5:0
4:0 1:107 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:107 3:0
2:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 1:0
1:0 1:103 1:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:99
3:0 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 2:0
5:0 1:99 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:99 4:0
7:0 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 6:0
9:0 1:103 1:105 1:101 3:105 1:101 3:105 1:101 3:105 1:99 8:0
11:0 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 10:0
13:0 1:99 1:105 1:101 1:105 1:101 1:105 1:99 12:0
15:0 1:103 1:101 1:103 14:0
SPRITE 7 tile_7 32 16 16 0
16:0 1:95 15:0
14:0 1:92 2:90 1:94 1:92 13:0
12:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 11:0
10:0 1:92 11:90 1:92 9:0
8:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 7:0
6:0 1:92 2:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 1:92 5:0
4:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 3:0
2:0 1:92 27:90 1:92 1:0
1:0 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:88
3:0 1:88 1:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:92 2:0
5:0 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:88 4:0
7:0 1:88 17:90 1:88 6:0
9:0 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:88 8:0
11:0 1:88 1:90 1:94 3:90 1:94 3:90 1:92 10:0
13:0 1:88 1:94 1:90 1:94 1:90 1:94 1:88 12:0
15:0 1:88 1:90 1:88 14:0
SPRITE 8 tile_8 32 16 16 0
16:0 1:125 15:0
14:0 1:122 3:120 1:122 13:0
12:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 11:0
10:0 1:122 11:120 1:122 9:0
8:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 7:0
6:0 1:122 19:120 1:122 5:0
4:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 3:0
2:0 1:122 27:120 1:122 1:0
1:0 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:118
3:0 1:118 25:120 1:118 2:0
5:0 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:118 4:0
7:0 1:118 17:120 1:118 6:0
9:0 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:118 8:0
11:0 1:118 9:120 1:118 10:0
13:0 1:118 1:123 1:120 1:123 1:120 1:123 1:118 12:0
15:0 1:118 1:120 1:118 14:0
SPRITE 9 tile_9 32 16 16 0
16:0 1:142 15:0
14:0 1:139 3:137 1:139 13:0
12:0 1:139 1:137 1:140 3:137 1:140 1:137 1:139 11:0
10:0 1:139 11:137 1:139 9:0
8:0 1:142 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:142 7:0
6:0 1:139 19:137 1:139 5:0
4:0 1:139 1:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 1:137 1:139 3:0
2:0 1:139 27:137 1:139 1:0
1:0 1:135 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:135
3:0 1:135 25:137 1:135 2:0
5:0 1:135 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 1:135 4:0
7:0 1:135 17:137 1:135 6:0
9:0 1:135 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:135 8:0
11:0 1:135 9:137 1:135 10:0
13:0 1:135 1:140 3:137 1:140 1:135 12:0
15:0 1:135 1:137 1:135 14:0
SPRITE 10 tile_10 32 16 16 0
16:0 1:158 15:0
14:0 1:154 3:152 1:154 13:0
12:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 11:0
10:0 1:154 11:152 1:154 9:0
8:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 7:0
6:0 1:154 19:152 1:154 5:0
4:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 3:0
2:0 1:154 27:152 1:154 1:0
1:0 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:150
3:0 1:150 25:152 1:150 2:0
5:0 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:150 4:0
7:0 1:150 17:152 1:150 6:0
9:0 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:150 8:0
11:0 1:150 9:152 1:150 10:0
13:0 1:150 1:156 1:152 1:156 1:152 1:156 1:150 12:0
15:0 1:150 1:152 1:150 14:0
SPRITE 11 tile_11 32 16 16 0
16:0 1:174 15:0
14:0 1:170 1:172 1:168 1:172 1:170 13:0
12:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 11:0
10:0 1:170 1:172 3:168 1:172 3:168 1:172 2:168 1:170 9:0
8:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 7:0
6:0 1:170 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:170 5:0
4:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 3:0
2:0 1:170 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 2:168 1:170 1:0
1:0 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:166
3:0 1:170 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:170 2:0
5:0 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:166 4:0
7:0 1:170 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 1:168 1:166 6:0
9:0 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:166 8:0
11:0 1:170 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:170 10:0
13:0 1:166 1:172 1:168 1:172 1:168 1:172 1:166 12:0
15:0 1:170 1:168 1:166 14:0
SPRITE 12 tile_12 32 16 16 0
16:0 1:191 15:0
14:0 1:189 3:187 1:189 13:0
12:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 11:0
10:0 1:189 11:187 1:189 9:0
8:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 7:0
6:0 1:189 19:187 1:189 5:0
4:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 3:0
2:0 1:189 27:187 1:189 1:0
1:0 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:185
3:0 1:185 25:187 1:185 2:0
5:0 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:185 4:0
7:0 1:185 17:187 1:185 6:0
9:0 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:185 8:0
11:0 1:185 9:187 1:185 10:0
13:0 1:185 1:191 1:187 1:191 1:187 1:191 1:185 12:0
15:0 1:185 1:187 1:185 14:0
SPRITE 13 tile_13 32 16 16 0
16:0 1:202 15:0
14:0 1:199 1:200 1:197 1:200 1:199 13:0
12:0 1:202 1:197 3:200 1:197 2:200 1:202 11:0
10:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 9:0
8:0 1:202 2:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 1:202 7:0
6:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 5:0
4:0 1:202 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 2:200 1:202 3:0
2:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 1:0
1:0 1:198 1:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:195
3:0 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 2:0
5:0 1:195 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 1:200 1:198 4:0
7:0 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 6:0
9:0 1:198 1:200 1:197 3:200 1:197 3:200 1:197 3:200 1:195 8:0
11:0 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 10:0
13:0 1:195 3:200 1:197 1:200 1:198 12:0
15:0 1:198 1:197 1:198 14:0
SPRITE 14 tile_14 32 16 16 0
16:0 1:223 15:0
14:0 1:217 1:222 1:215 1:222 1:217 13:0
12:0 1:223 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:223 11:0
10:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 9:0
8:0 1:223 2:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 1:223 7:0
6:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 5:0
4:0 1:223 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:223 3:0
2:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 1:0
1:0 1:220 1:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:213
3:0 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 2:0
5:0 1:213 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:213 4:0
7:0 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 6:0
9:0 1:220 1:222 1:215 3:222 1:215 3:222 1:215 3:222 1:213 8:0
11:0 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 10:0
13:0 1:213 1:222 1:215 1:222 1:215 1:222 1:213 12:0
15:0 1:220 1:215 1:220 14:0
SPRITE 15 tile_15 32 16 16 0
16:0 1:86 15:0
14:0 1:84 3:82 1:84 13:0
12:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 11:0
10:0 1:84 11:82 1:84 9:0
8:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 7:0
6:0 1:84 19:82 1:84 5:0
4:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 3:0
2:0 1:84 27:82 1:84 1:0
1:0 1:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:80
3:0 1:80 25:82 1:80 2:0
5:0 1:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:80 4:0
7:0 1:80 17:82 1:80 6:0
9:0 1:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:80 8:0
11:0 1:80 9:82 1:80 10:0
13:0 1:80 1:84 1:82 1:84 1:82 1:84 1:80 12:0
15:0 1:80 1:82 1:80 14:0
SPRITE 16 cube_0 32 24 16 0
16:0 1:27 15:0
14:0 1:24 1:25 1:22 1:25 1:24 13:0
12:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 11:0
10:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 9:0
8:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 7:0
6:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 5:0
4:0 1:27 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:27 3:0
2:0 1:24 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:24 1:0
1:0 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:20
1:0 2:18 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 2:20
1:0 4:18 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 5:20
1:0 6:18 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 6:20
1:0 8:18 1:20 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 9:20
1:0 10:18 1:23 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:25 1:22 1:23 10:20
1:0 12:18 1:20 1:25 1:22 1:25 1:22 1:25 13:20
1:0 14:18 1:23 1:22 1:23 14:20
1:0 2:17 13:18 14:20 2:19
3:0 2:17 11:18 12:20 2:19 2:0
5:0 2:17 9:18 10:20 2:19 4:0
7:0 2:17 7:18 8:20 2:19 6:0
9:0 2:17 5:18 6:20 2:19 8:0
11:0 2:17 3:18 4:20 2:19 10:0
13:0 2:17 1:18 2:20 2:19 12:0
15:0 1:17 2:19 14:0
SPRITE 17 cube_1 32 24 16 0
16:0 1:30 15:0
14:0 1:27 1:28 1:25 1:28 1:27 13:0
12:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 11:0
10:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 9:0
8:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 7:0
6:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 5:0
4:0 1:30 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:30 3:0
2:0 1:27 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:27 1:0
1:0 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:23
1:0 2:21 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 2:23
1:0 4:21 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 5:23
1:0 6:21 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 6:23
1:0 8:21 1:23 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 9:23
1:0 10:21 1:26 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:28 1:25 1:26 10:23
1:0 12:21 1:23 1:28 1:25 1:28 1:25 1:28 13:23
1:0 14:21 1:26 1:25 1:26 14:23
1:0 2:20 13:21 14:23 2:22
3:0 2:20 11:21 12:23 2:22 2:0
5:0 2:20 9:21 10:23 2:22 4:0
7:0 2:20 7:21 8:23 2:22 6:0
9:0 2:20 5:21 6:23 2:22 8:0
11:0 2:20 3:21 4:23 2:22 10:0
13:0 2:20 1:21 2:23 2:22 12:0
15:0 1:20 2:22 14:0
SPRITE 18 cube_2 32 24 16 0
16:0 1:46 15:0
14:0 1:43 2:41 1:44 1:43 13:0
12:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 11:0
10:0 1:43 1:44 3:41 1:44 3:41 1:44 2:41 1:43 9:0
8:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 7:0
6:0 1:43 2:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 1:43 5:0
4:0 1:46 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:46 3:0
2:0 1:43 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 2:41 1:43 1:0
1:0 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:39
1:0 2:37 1:39 1:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:42 2:39
1:0 4:37 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 5:39
1:0 6:37 1:42 3:41 1:44 3:41 1:44 3:41 1:44 3:41 1:44 1:41 7:39
1:0 8:37 1:39 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 1:41 1:44 9:39
1:0 10:37 1:39 1:41 1:44 3:41 1:44 3:41 1:42 10:39
1:0 12:37 1:39 1:44 1:41 1:44 1:41 1:44 13:39
1:0 14:37 1:42 1:41 15:39
1:0 2:36 13:37 14:39 2:38
3:0 2:36 11:37 12:39 2:38 2:0
5:0 2:36 9:37 10:39 2:38 4:0
7:0 2:36 7:37 8:39 2:38 6:0
9:0 2:36 5:37 6:39 2:38 8:0
11:0 2:36 3:37 4:39 2:38 10:0
13:0 2:36 1:37 2:39 2:38 12:0
15:0 1:36 2:38 14:0
SPRITE 19 cube_3 32 24 16 0
16:0 1:61 15:0
14:0 1:57 2:55 1:59 1:57 13:0
12:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 11:0
10:0 1:57 11:55 1:57 9:0
8:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 7:0
6:0 1:57 2:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 1:57 5:0
4:0 1:61 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:61 3:0
2:0 1:57 27:55 1:57 1:0
1:0 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:53
1:0 2:51 1:53 1:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:59 3:55 1:57 2:53
1:0 4:51 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 5:53
1:0 6:51 1:53 17:55 7:53
1:0 8:51 1:53 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 1:55 1:59 9:53
1:0 10:51 1:53 1:55 1:59 3:55 1:59 3:55 1:57 10:53
1:0 12:51 1:53 1:59 1:55 1:59 1:55 1:59 13:53
1:0 14:51 1:53 1:55 15:53
1:0 2:50 13:51 14:53 2:52
3:0 2:50 11:51 12:53 2:52 2:0
5:0 2:50 9:51 10:53 2:52 4:0
7:0 2:50 7:51 8:53 2:52 6:0
9:0 2:50 5:51 6:53 2:52 8:0
11:0 2:50 3:51 4:53 2:52 10:0
13:0 2:50 1:51 2:53 2:52 12:0
15:0 1:50 2:52 14:0
SPRITE 20 cube_4 32 24 16 0
16:0 1:76 15:0
14:0 1:73 2:71 1:74 1:73 13:0
12:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 11:0
10:0 1:73 1:74 3:71 1:74 3:71 1:74 2:71 1:73 9:0
8:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 7:0
6:0 1:73 2:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 1:73 5:0
4:0 1:76 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:76 3:0
2:0 1:73 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 2:71 1:73 1:0
1:0 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:69
1:0 2:67 1:69 1:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:72 2:69
1:0 4:67 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 5:69
1:0 6:67 1:72 3:71 1:74 3:71 1:74 3:71 1:74 3:71 1:74 1:71 7:69
1:0 8:67 1:69 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 1:71 1:74 9:69
1:0 10:67 1:69 1:71 1:74 3:71 1:74 3:71 1:72 10:69
1:0 12:67 1:69 1:74 1:71 1:74 1:71 1:74 13:69
1:0 14:67 1:72 1:71 15:69
1:0 2:66 13:67 14:69 2:68
3:0 2:66 11:67 12:69 2:68 2:0
5:0 2:66 9:67 10:69 2:68 4:0
7:0 2:66 7:67 8:69 2:68 6:0
9:0 2:66 5:67 6:69 2:68 8:0
11:0 2:66 3:67 4:69 2:68 10:0
13:0 2:66 1:67 2:69 2:68 12:0
15:0 1:66 2:68 14:0
SPRITE 21 cube_5 32 24 16 0
16:0 1:92 15:0
14:0 1:89 1:90 1:87 1:90 1:89 13:0
12:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 11:0
10:0 1:89 1:90 3:87 1:90 3:87 1:90 2:87 1:89 9:0
8:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 7:0
6:0 1:89 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:89 5:0
4:0 1:92 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:92 3:0
2:0 1:89 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 2:87 1:89 1:0
1:0 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:85
1:0 2:83 1:88 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:88 2:85
1:0 4:83 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 5:85
1:0 6:83 1:88 3:87 1:90 3:87 1:90 3:87 1:90 3:87 1:90 1:87 7:85
1:0 8:83 1:85 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 9:85
1:0 10:83 1:88 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:90 1:87 1:88 10:85
1:0 12:83 1:85 1:90 1:87 1:90 1:87 1:90 13:85
1:0 14:83 1:88 1:87 15:85
1:0 2:82 13:83 14:85 2:84
3:0 2:82 11:83 12:85 2:84 2:0
5:0 2:82 9:83 10:85 2:84 4:0
7:0 2:82 7:83 8:85 2:84 6:0
9:0 2:82 5:83 6:85 2:84 8:0
11:0 2:82 3:83 4:85 2:84 10:0
13:0 2:82 1:83 2:85 2:84 12:0
15:0 1:82 2:84 14:0
SPRITE 22 cube_6 32 24 16 0
16:0 1:107 15:0
14:0 1:103 1:105 1:101 1:105 1:103 13:0
12:0 1:107 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:107 11:0
10:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 9:0
8:0 1:107 2:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 1:107 7:0
6:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 5:0
4:0 1:107 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:107 3:0
2:0 1:103 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:103 1:0
1:0 1:103 1:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:101 3:105 1:99
1:0 2:97 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 2:99
1:0 4:97 1:99 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 5:99
1:0 6:97 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 6:99
1:0 8:97 1:103 1:105 1:101 3:105 1:101 3:105 1:101 3:105 9:99
1:0 10:97 1:103 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:105 1:101 1:103 10:99
1:0 12:97 1:99 1:105 1:101 1:105 1:101 1:105 13:99
1:0 14:97 1:103 1:101 1:103 14:99
1:0 2:96 13:97 14:99 2:98
3:0 2:96 11:97 12:99 2:98 2:0
5:0 2:96 9:97 10:99 2:98 4:0
7:0 2:96 7:97 8:99 2:98 6:0
9:0 2:96 5:97 6:99 2:98 8:0
11:0 2:96 3:97 4:99 2:98 10:0
13:0 2:96 1:97 2:99 2:98 12:0
15:0 1:96 2:98 14:0
SPRITE 23 cube_7 32 24 16 0
16:0 1:95 15:0
14:0 1:92 2:90 1:94 1:92 13:0
12:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 11:0
10:0 1:92 11:90 1:92 9:0
8:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 7:0
6:0 1:92 2:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 1:92 5:0
4:0 1:95 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:95 3:0
2:0 1:92 27:90 1:92 1:0
1:0 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:88
1:0 2:86 1:88 1:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:94 3:90 1:92 2:88
1:0 4:86 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 5:88
1:0 6:86 1:88 17:90 7:88
1:0 8:86 1:88 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 1:90 1:94 9:88
1:0 10:86 1:88 1:90 1:94 3:90 1:94 3:90 1:92 10:88
1:0 12:86 1:88 1:94 1:90 1:94 1:90 1:94 13:88
1:0 14:86 1:88 1:90 15:88
1:0 2:85 13:86 14:88 2:87
3:0 2:85 11:86 12:88 2:87 2:0
5:0 2:85 9:86 10:88 2:87 4:0
7:0 2:85 7:86 8:88 2:87 6:0
9:0 2:85 5:86 6:88 2:87 8:0
11:0 2:85 3:86 4:88 2:87 10:0
13:0 2:85 1:86 2:88 2:87 12:0
15:0 1:85 2:87 14:0
SPRITE 24 cube_8 32 24 16 0
16:0 1:125 15:0
14:0 1:122 3:120 1:122 13:0
12:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 11:0
10:0 1:122 11:120 1:122 9:0
8:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 7:0
6:0 1:122 19:120 1:122 5:0
4:0 1:125 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:125 3:0
2:0 1:122 27:120 1:122 1:0
1:0 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:118
1:0 2:116 1:118 25:120 3:118
1:0 4:116 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 5:118
1:0 6:116 1:118 17:120 7:118
1:0 8:116 1:118 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 1:120 1:123 9:118
1:0 10:116 1:118 9:120 11:118
1:0 12:116 1:118 1:123 1:120 1:123 1:120 1:123 13:118
1:0 14:116 1:118 1:120 15:118
1:0 2:115 13:116 14:118 2:117
3:0 2:115 11:116 12:118 2:117 2:0
5:0 2:115 9:116 10:118 2:117 4:0
7:0 2:115 7:116 8:118 2:117 6:0
9:0 2:115 5:116 6:118 2:117 8:0
11:0 2:115 3:116 4:118 2:117 10:0
13:0 2:115 1:116 2:118 2:117 12:0
15:0 1:115 2:117 14:0
SPRITE 25 cube_9 32 24 16 0
16:0 1:142 15:0
14:0 1:139 3:137 1:139 13:0
12:0 1:139 1:137 1:140 3:137 1:140 1:137 1:139 11:0
10:0 1:139 11:137 1:139 9:0
8:0 1:142 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:142 7:0
6:0 1:139 19:137 1:139 5:0
4:0 1:139 1:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 1:137 1:139 3:0
2:0 1:139 27:137 1:139 1:0
1:0 1:135 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:135
1:0 2:133 1:135 25:137 3:135
1:0 4:133 1:135 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 3:137 1:140 5:135
1:0 6:133 1:135 17:137 7:135
1:0 8:133 1:135 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 1:137 1:140 9:135
1:0 10:133 1:135 9:137 11:135
1:0 12:133 1:135 1:140 3:137 1:140 13:135
1:0 14:133 1:135 1:137 15:135
1:0 2:132 13:133 14:135 2:134
3:0 2:132 11:133 12:135 2:134 2:0
5:0 2:132 9:133 10:135 2:134 4:0
7:0 2:132 7:133 8:135 2:134 6:0
9:0 2:132 5:133 6:135 2:134 8:0
11:0 2:132 3:133 4:135 2:134 10:0
13:0 2:132 1:133 2:135 2:134 12:0
15:0 1:132 2:134 14:0
SPRITE 26 cube_10 32 24 16 0
16:0 1:158 15:0
14:0 1:154 3:152 1:154 13:0
12:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 11:0
10:0 1:154 11:152 1:154 9:0
8:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 7:0
6:0 1:154 19:152 1:154 5:0
4:0 1:158 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:158 3:0
2:0 1:154 27:152 1:154 1:0
1:0 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:150
1:0 2:148 1:150 25:152 3:150
1:0 4:148 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 5:150
1:0 6:148 1:150 17:152 7:150
1:0 8:148 1:150 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 1:152 1:156 9:150
1:0 10:148 1:150 9:152 11:150
1:0 12:148 1:150 1:156 1:152 1:156 1:152 1:156 13:150
1:0 14:148 1:150 1:152 15:150
1:0 2:147 13:148 14:150 2:149
3:0 2:147 11:148 12:150 2:149 2:0
5:0 2:147 9:148 10:150 2:149 4:0
7:0 2:147 7:148 8:150 2:149 6:0
9:0 2:147 5:148 6:150 2:149 8:0
11:0 2:147 3:148 4:150 2:149 10:0
13:0 2:147 1:148 2:150 2:149 12:0
15:0 1:147 2:149 14:0
SPRITE 27 cube_11 32 24 16 0
16:0 1:174 15:0
14:0 1:170 1:172 1:168 1:172 1:170 13:0
12:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 11:0
10:0 1:170 1:172 3:168 1:172 3:168 1:172 2:168 1:170 9:0
8:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 7:0
6:0 1:170 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:170 5:0
4:0 1:174 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:174 3:0
2:0 1:170 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 2:168 1:170 1:0
1:0 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:166
1:0 2:164 1:170 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:170 2:166
1:0 4:164 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 5:166
1:0 6:164 1:170 3:168 1:172 3:168 1:172 3:168 1:172 3:168 1:172 1:168 7:166
1:0 8:164 1:166 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 9:166
1:0 10:164 1:170 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:172 1:168 1:170 10:166
1:0 12:164 1:166 1:172 1:168 1:172 1:168 1:172 13:166
1:0 14:164 1:170 1:168 15:166
1:0 2:163 13:164 14:166 2:165
3:0 2:163 11:164 12:166 2:165 2:0
5:0 2:163 9:164 10:166 2:165 4:0
7:0 2:163 7:164 8:166 2:165 6:0
9:0 2:163 5:164 6:166 2:165 8:0
11:0 2:163 3:164 4:166 2:165 10:0
13:0 2:163 1:164 2:166 2:165 12:0
15:0 1:163 2:165 14:0
SPRITE 28 cube_12 32 24 16 0
16:0 1:191 15:0
14:0 1:189 3:187 1:189 13:0
12:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 11:0
10:0 1:189 11:187 1:189 9:0
8:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 7:0
6:0 1:189 19:187 1:189 5:0
4:0 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 3:0
2:0 1:189 27:187 1:189 1:0
1:0 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:185
1:0 2:183 1:185 25:187 3:185
1:0 4:183 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 5:185
1:0 6:183 1:185 17:187 7:185
1:0 8:183 1:185 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 1:187 1:191 9:185
1:0 10:183 1:185 9:187 11:185
1:0 12:183 1:185 1:191 1:187 1:191 1:187 1:191 13:185
1:0 14:183 1:185 1:187 15:185
1:0 2:182 13:183 14:185 2:184
3:0 2:182 11:183 12:185 2:184 2:0
5:0 2:182 9:183 10:185 2:184 4:0
7:0 2:182 7:183 8:185 2:184 6:0
9:0 2:182 5:183 6:185 2:184 8:0
11:0 2:182 3:183 4:185 2:184 10:0
13:0 2:182 1:183 2:185 2:184 12:0
15:0 1:182 2:184 14:0
SPRITE 29 cube_13 32 24 16 0
16:0 1:202 15:0
14:0 1:199 1:200 1:197 1:200 1:199 13:0
12:0 1:202 1:197 3:200 1:197 2:200 1:202 11:0
10:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 9:0
8:0 1:202 2:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 1:202 7:0
6:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 5:0
4:0 1:202 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 2:200 1:202 3:0
2:0 1:199 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:199 1:0
1:0 1:198 1:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:195
1:0 2:193 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 2:195
1:0 4:193 1:195 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 3:200 1:197 1:200 1:198 4:195
1:0 6:193 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 6:195
1:0 8:193 1:198 1:200 1:197 3:200 1:197 3:200 1:197 3:200 9:195
1:0 10:193 1:198 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:200 1:197 1:198 10:195
1:0 12:193 1:195 3:200 1:197 1:200 1:198 12:195
1:0 14:193 1:198 1:197 1:198 14:195
1:0 2:192 13:193 14:195 2:194
3:0 2:192 11:193 12:195 2:194 2:0
5:0 2:192 9:193 10:195 2:194 4:0
7:0 2:192 7:193 8:195 2:194 6:0
9:0 2:192 5:193 6:195 2:194 8:0
11:0 2:192 3:193 4:195 2:194 10:0
13:0 2:192 1:193 2:195 2:194 12:0
15:0 1:192 2:194 14:0
SPRITE 30 cube_14 32 24 16 0
16:0 1:223 15:0
14:0 1:217 1:222 1:215 1:222 1:217 13:0
12:0 1:223 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:223 11:0
10:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 9:0
8:0 1:223 2:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 1:223 7:0
6:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 5:0
4:0 1:223 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:223 3:0
2:0 1:217 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:217 1:0
1:0 1:220 1:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:215 3:222 1:213
1:0 2:211 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 2:213
1:0 4:211 1:213 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 5:213
1:0 6:211 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 6:213
1:0 8:211 1:220 1:222 1:215 3:222 1:215 3:222 1:215 3:222 9:213
1:0 10:211 1:220 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:222 1:215 1:220 10:213
1:0 12:211 1:213 1:222 1:215 1:222 1:215 1:222 13:213
1:0 14:211 1:220 1:215 1:220 14:213
1:0 2:210 13:211 14:213 2:212
3:0 2:210 11:211 12:213 2:212 2:0
5:0 2:210 9:211 10:213 2:212 4:0
7:0 2:210 7:211 8:213 2:212 6:0
9:0 2:210 5:211 6:213 2:212 8:0
11:0 2:210 3:211 4:213 2:212 10:0
13:0 2:210 1:211 2:213 2:212 12:0
15:0 1:210 2:212 14:0
SPRITE 31 cube_15 32 24 16 0
16:0 1:86 15:0
14:0 1:84 3:82 1:84 13:0
12:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 11:0
10:0 1:84 11:82 1:84 9:0
8:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 7:0
6:0 1:84 19:82 1:84 5:0
4:0 1:86 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:86 3:0
2:0 1:84 27:82 1:84 1:0
1:0 1:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:80
1:0 3:80 25:82 3:80
1:0 5:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 5:80
1:0 7:80 17:82 7:80
1:0 9:80 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 1:82 1:84 9:80
1:0 11:80 9:82 11:80
1:0 13:80 1:84 1:82 1:84 1:82 1:84 13:80
1:0 15:80 1:82 15:80
1:0 31:80
3:0 27:80 2:0
5:0 23:80 4:0
7:0 19:80 6:0
9:0 15:80 8:0
11:0 11:80 10:0
13:0 7:80 12:0
15:0 3:80 14:0
SPRITE 32 hero_0_0 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 2:235 1:81 2:235 1:81 3:235 3:0
4:0 8:235 4:0
5:0 2:235 2:92 2:235 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 1:235 9:249 2:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
4:0 8:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 33 hero_0_1 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 2:235 1:81 2:235 1:81 3:235 3:0
4:0 8:235 4:0
5:0 2:235 2:92 2:235 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 1:235 9:249 2:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
3:0 4:244 2:0 4:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 3:164 4:0 3:164 3:0
3:0 3:164 4:0 3:164 3:0
SPRITE 34 hero_1_0 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 1:66 6:235 1:66 4:0
3:0 3:235 1:81 2:235 1:81 2:235 4:0
4:0 8:235 4:0
5:0 2:235 2:92 2:235 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 2:235 9:249 1:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
4:0 8:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 35 hero_1_1 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 1:66 6:235 1:66 4:0
3:0 3:235 1:81 2:235 1:81 2:235 4:0
4:0 8:235 4:0
5:0 2:235 2:92 2:235 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 2:235 9:249 1:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
3:0 4:244 2:0 4:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 3:164 4:0 3:164 3:0
3:0 3:164 4:0 3:164 3:0
SPRITE 36 hero_2_0 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
5:0 6:66 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 2:235 9:249 1:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
4:0 8:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 37 hero_2_1 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
5:0 6:66 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 2:235 9:249 1:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
3:0 4:244 2:0 4:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 3:164 4:0 3:164 3:0
3:0 3:164 4:0 3:164 3:0
SPRITE 38 hero_3_0 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
5:0 6:66 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 1:235 9:249 2:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
4:0 8:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 2:244 4:0 2:244 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 39 hero_3_1 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
5:0 6:66 5:0
6:0 4:235 6:0
3:0 10:249 3:0
2:0 12:249 2:0
2:0 1:235 10:249 1:235 2:0
2:0 1:235 9:249 2:235 2:0
3:0 10:249 3:0
3:0 10:249 3:0
3:0 10:244 3:0
3:0 4:244 2:0 4:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 2:244 6:0 2:244 3:0
3:0 3:164 4:0 3:164 3:0
3:0 3:164 4:0 3:164 3:0
SPRITE 40 mon_0 16 18 8 17
16:0
3:0 2:88 6:0 2:88 3:0
3:0 3:88 4:0 3:88 3:0
4:0 8:88 4:0
3:0 10:88 3:0
2:0 2:88 1:220 6:88 1:220 2:88 2:0
2:0 12:88 2:0
2:0 3:88 6:92 3:88 2:0
3:0 10:88 3:0
2:0 12:88 2:0
2:0 12:88 2:0
2:0 12:88 2:0
3:0 10:88 3:0
4:0 8:88 4:0
4:0 2:88 4:0 2:88 4:0
4:0 2:88 4:0 2:88 4:0
3:0 3:88 4:0 3:88 3:0
3:0 3:88 4:0 3:88 3:0
SPRITE 41 mon_1 16 18 8 17
16:0
3:0 2:88 6:0 2:88 3:0
3:0 3:88 4:0 3:88 3:0
4:0 8:88 4:0
3:0 10:88 3:0
2:0 2:88 1:220 6:88 1:220 2:88 2:0
2:0 12:88 2:0
2:0 3:88 6:92 3:88 2:0
3:0 10:88 3:0
2:0 12:88 2:0
2:0 12:88 2:0
2:0 12:88 2:0
2:0 5:88 2:0 5:88 2:0
3:0 4:88 2:0 4:88 3:0
3:0 2:88 6:0 2:88 3:0
3:0 2:88 6:0 2:88 3:0
2:0 3:88 6:0 3:88 2:0
2:0 3:88 6:0 3:88 2:0
SPRITE 42 chest_0 16 14 8 11
16:0
2:0 12:167 2:0
1:0 1:167 12:171 1:167 1:0
1:0 1:167 1:171 10:92 1:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 14:167 1:0
1:0 1:167 4:171 4:46 4:171 1:167 1:0
1:0 1:167 4:171 1:46 2:92 1:46 4:171 1:167 1:0
1:0 1:167 4:171 4:46 4:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 14:167 1:0
2:0 12:167 2:0
16:0
SPRITE 43 chest_1 16 14 8 11
2:0 12:167 2:0
1:0 1:167 12:171 1:167 1:0
1:0 1:167 1:171 10:92 1:171 1:167 1:0
1:0 14:167 1:0
16:0
2:0 12:46 2:0
1:0 1:167 12:46 1:167 1:0
1:0 1:167 1:171 10:46 1:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 1:167 12:171 1:167 1:0
1:0 14:167 1:0
2:0 12:167 2:0
16:0
SPRITE 44 npc_0 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 1:66 6:235 1:66 4:0
4:0 2:235 1:81 2:235 1:81 3:235 3:0
4:0 8:235 4:0
5:0 2:235 2:92 2:235 5:0
6:0 4:235 6:0
3:0 10:46 3:0
2:0 12:46 2:0
2:0 1:235 10:46 1:235 2:0
2:0 1:235 9:46 2:235 2:0
3:0 10:46 3:0
3:0 10:46 3:0
3:0 10:167 3:0
4:0 8:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 45 npc_1 16 22 8 21
16:0
5:0 6:66 5:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
4:0 8:66 4:0
5:0 6:66 5:0
6:0 4:235 6:0
3:0 10:46 3:0
2:0 12:46 2:0
2:0 1:235 10:46 1:235 2:0
2:0 1:235 9:46 2:235 2:0
3:0 10:46 3:0
3:0 10:46 3:0
3:0 10:167 3:0
4:0 8:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 2:167 4:0 2:167 4:0
4:0 3:164 2:0 3:164 4:0
4:0 3:164 2:0 3:164 4:0
SPRITE 46 tree 20 18 10 17
8:0 4:105 8:0
6:0 8:105 6:0
5:0 10:105 5:0
4:0 12:105 4:0
3:0 14:105 3:0
3:0 14:105 3:0
2:0 16:105 2:0
2:0 16:105 2:0
2:0 16:105 2:0
3:0 14:105 3:0
4:0 12:105 4:0
5:0 10:105 5:0
6:0 8:105 6:0
8:0 4:167 8:0
8:0 4:167 8:0
8:0 4:167 8:0
7:0 6:167 7:0
7:0 6:167 7:0
SPRITE 47 rock 18 8 9 7
6:0 6:88 6:0
4:0 2:88 6:92 2:88 4:0
3:0 1:88 10:92 1:88 3:0
2:0 1:88 12:92 1:88 2:0
2:0 1:88 12:92 1:88 2:0
1:0 2:88 12:92 2:88 1:0
1:0 3:88 10:92 3:88 1:0
2:0 14:88 2:0
`;
/** golden/script.txt (615바이트) */
exports.SCRIPT_TXT = `# 시나리오 — 남쪽 길에서 마을로 들어가 상자 셋을 열고 몬스터와 싸운 뒤 저장/복원한다.
# 방향 이름은 SPEC 8.1 의 8방향 표를 따른다 (E SE S SW W NW N NE).
mark start
hold N 25
mark south_gate
hold N 20
mark town_center
wait 8
atk
wait 4
atk
wait 4
atk
wait 4
atk
wait 4
atk
wait 4
atk
wait 4
mark after_fight
hold E 10
act
wait 3
mark chest_east
hold NW 15
hold W 10
act
wait 3
mark chest_west
hold NE 16
act
wait 3
mark chest_north
save
hold SE 20
hold S 8
mark wandered
load
mark restored
hold W 6
atk
wait 4
atk
wait 4
mark last_fight
hold S 20
hold SE 12
mark end
`;
  });
  __def('web/canvas', function (exports, require, module) {
"use strict";
// 캔버스 프런트엔드 — 8비트 인덱스 버퍼를 팔레트로 풀어 화면에 올린다.
//
// 엔진은 320x200 짜리 팔레트 인덱스 배열만 만든다. 여기서 하는 일은
// 모드 13h 시절 VGA DAC 가 하던 일과 정확히 같다 — 인덱스를 RGB 로 바꾸는 것.
// 그래서 이 파일에는 게임 로직이 한 줄도 없다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.CanvasView = void 0;
const raster_1 = require("../raster");
/** 팔레트를 RGBA 룩업으로 미리 펴 둔다. 픽셀마다 세 번 조회하는 것보다 싸다. */
function paletteLut(pal) {
    const lut = new Uint8ClampedArray(raster_1.PAL_SIZE * 4);
    for (let i = 0; i < raster_1.PAL_SIZE; i++) {
        const c = pal[i];
        lut[i * 4] = (0, raster_1.expand6)(c[0]);
        lut[i * 4 + 1] = (0, raster_1.expand6)(c[1]);
        lut[i * 4 + 2] = (0, raster_1.expand6)(c[2]);
        lut[i * 4 + 3] = 255;
    }
    return lut;
}
class CanvasView {
    constructor(pal, scale) {
        this.phase = -1;
        this.basePal = pal;
        this.lut = paletteLut(pal);
        const cv = document.createElement('canvas');
        cv.width = raster_1.SCR_W;
        cv.height = raster_1.SCR_H;
        // 확대는 CSS 로 한다. 캔버스를 크게 잡고 그리면 픽셀마다 비용이 배로 든다.
        cv.style.width = String(raster_1.SCR_W * scale) + 'px';
        cv.style.height = String(raster_1.SCR_H * scale) + 'px';
        cv.style.imageRendering = 'pixelated';
        cv.style.display = 'block';
        cv.style.maxWidth = '100%';
        this.canvas = cv;
        const c = cv.getContext('2d');
        if (!c)
            throw new Error('2d 컨텍스트를 못 얻었다');
        this.ctx = c;
        this.img = this.ctx.createImageData(raster_1.SCR_W, raster_1.SCR_H);
        this.buf = this.img.data;
    }
    /** 화면 폭에 맞춰 CSS 크기를 다시 잡는다. 정수 배율만 쓴다 — 그래야 픽셀이 안 뭉갠다. */
    fit(availWidth) {
        let s = Math.floor(availWidth / raster_1.SCR_W);
        if (s < 1)
            s = 1;
        if (s > 4)
            s = 4;
        this.canvas.style.width = String(raster_1.SCR_W * s) + 'px';
        this.canvas.style.height = String(raster_1.SCR_H * s) + 'px';
    }
    /** 팔레트 사이클링 위상이 바뀌었을 때만 룩업을 다시 만든다. */
    setPhase(phase) {
        if (phase === this.phase)
            return;
        this.phase = phase;
        this.lut = paletteLut((0, raster_1.cyclePalette)(this.basePal, phase));
    }
    draw(fb) {
        const buf = this.buf;
        const lut = this.lut;
        const n = raster_1.SCR_W * raster_1.SCR_H;
        for (let i = 0; i < n; i++) {
            const c = fb[i] * 4;
            const j = i * 4;
            buf[j] = lut[c];
            buf[j + 1] = lut[c + 1];
            buf[j + 2] = lut[c + 2];
            buf[j + 3] = 255;
        }
        this.ctx.putImageData(this.img, 0, 0);
    }
}
exports.CanvasView = CanvasView;
  });
  __def('web/minirpg', function (exports, require, module) {
"use strict";
// 덱 안에서 도는 미니 RPG — 14~16부에 실린 그 엔진 그대로다.
//
// 다시 만든 것이 아니다. `dist/src/*.js` 를 그대로 묶어 넣었고, 이 파일은
// 파일 대신 문자열에서 골든 데이터를 넣어 주고 캔버스에 올리는 일만 한다.
// 그래서 여기서 걸어 다니는 캐릭터의 좌표는 `golden/trace.jsonl` 의 좌표와
// 같은 코드가 계산한 값이다.
Object.defineProperty(exports, "__esModule", { value: true });
exports.boot = boot;
const game_1 = require("../game");
const RA = require("../raster");
const canvas_1 = require("./canvas");
const data_1 = require("./data");
const TICK_US = 54925;
// 화면 방향키 -> 타일 방향. 6부에서 다룬 45도 어긋남을 여기서 흡수한다.
// 위 화살표를 누르면 화면에서 위로 가야 하는데, 타일 축으로는 NW 다.
const KEY_DIR = {
    ArrowUp: 5, ArrowRight: 7, ArrowDown: 1, ArrowLeft: 3,
    w: 5, d: 7, s: 1, a: 3,
    q: 6, e: 0, z: 4, c: 2,
};
function el(tag, cls) {
    const e = document.createElement(tag);
    if (cls)
        e.className = cls;
    return e;
}
function boot(host, api) {
    const out = host.querySelector('.out');
    if (!out)
        return;
    const pal = RA.parsePalette(data_1.PALETTE_TXT);
    RA.setLight(RA.buildLight(pal));
    const view = new canvas_1.CanvasView(pal, 2);
    const g = new game_1.Game();
    g.setSprites(RA.parseSprites(data_1.TILES_RLE));
    const wrap = el('div');
    wrap.appendChild(view.canvas);
    const hud = el('div', 'lbl');
    hud.style.marginTop = '6px';
    wrap.appendChild(hud);
    out.innerHTML = '';
    out.appendChild(wrap);
    let held = -1;
    let act = 0;
    let atk = 0;
    let acc = 0;
    let last = 0;
    let running = true;
    function status() {
        const p = g.ents[0];
        if (!p)
            return;
        const mon = g.ents.filter((e) => e.kind === 1 && e.alive).length;
        const chest = g.ents.filter((e) => e.kind === 2 && e.alive).length;
        hud.textContent =
            '틱 ' + String(g.tickN) + '   체력 ' + String(p.hp) + '/' + String(p.maxhp) +
                '   레벨 ' + String(p.lv) + '   경험치 ' + String(p.xp) +
                '   남은 몬스터 ' + String(mon) + '   안 연 상자 ' + String(chest) +
                '   본 칸 ' + String(g.fog.countSeen());
    }
    function step(now) {
        if (!running)
            return;
        if (last === 0)
            last = now;
        let dt = (now - last) * 1000;
        last = now;
        // 탭을 오래 놔뒀다 돌아오면 dt 가 몇 초씩 된다. 한 번에 다섯 틱까지만 따라잡는다.
        if (dt > TICK_US * 5)
            dt = TICK_US * 5;
        acc += dt;
        let did = false;
        while (acc >= TICK_US) {
            acc -= TICK_US;
            g.inDir = held;
            g.inAct = act;
            g.inAtk = atk;
            act = 0;
            atk = 0;
            g.tick();
            did = true;
        }
        if (did) {
            view.setPhase(g.palPhase);
            view.draw(g.render());
            status();
        }
        requestAnimationFrame(step);
    }
    function onKey(e, down) {
        const d = KEY_DIR[e.key];
        if (d !== undefined) {
            // 방향키를 먹지 않으면 덱이 슬라이드를 넘겨 버린다.
            e.preventDefault();
            held = down ? d : (held === d ? -1 : held);
            return;
        }
        if (!down)
            return;
        if (e.key === ' ') {
            e.preventDefault();
            atk = 1;
        }
        else if (e.key === 'Enter' || e.key === 'f') {
            e.preventDefault();
            act = 1;
        }
    }
    // 캔버스가 포커스를 받아야 방향키가 여기로 온다.
    view.canvas.tabIndex = 0;
    view.canvas.style.outline = 'none';
    view.canvas.addEventListener('keydown', (e) => onKey(e, true));
    view.canvas.addEventListener('keyup', (e) => onKey(e, false));
    view.canvas.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        view.canvas.focus();
        // 터치에서는 캔버스를 눌러 방향을 준다 — 누른 지점이 가운데서 어느 쪽인지로.
        const r = view.canvas.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2);
        const dy = e.clientY - (r.top + r.height / 2);
        if (Math.abs(dx) < r.width * 0.12 && Math.abs(dy) < r.height * 0.12) {
            atk = 1;
            act = 1;
            return;
        }
        // 화면 방향을 타일 방향으로 되돌린다. 4부의 역투영과 같은 식이다.
        const a = dx + 2 * dy;
        const b = 2 * dy - dx;
        if (Math.abs(a) > Math.abs(b) * 2)
            held = a > 0 ? 0 : 4;
        else if (Math.abs(b) > Math.abs(a) * 2)
            held = b > 0 ? 2 : 6;
        else if (a > 0 && b > 0)
            held = 1;
        else if (a > 0)
            held = 7;
        else if (b > 0)
            held = 3;
        else
            held = 5;
    });
    view.canvas.addEventListener('pointerup', () => { held = -1; });
    view.canvas.addEventListener('pointerleave', () => { held = -1; });
    const btnStop = host.querySelector('[data-stop]');
    if (btnStop) {
        btnStop.addEventListener('click', () => {
            running = !running;
            btnStop.textContent = running ? '멈춤' : '계속';
            if (running) {
                last = 0;
                requestAnimationFrame(step);
            }
        });
    }
    const btnAuto = host.querySelector('[data-auto]');
    if (btnAuto) {
        btnAuto.addEventListener('click', () => {
            // 골든 시나리오 222틱을 그대로 재생한다. 트레이스와 같은 길을 걷는다.
            running = false;
            const g2 = new game_1.Game();
            g2.setSprites(g.sprites());
            let i = 0;
            const frames = [];
            g2.runScriptText(data_1.SCRIPT_TXT, () => {
                if (i % 3 === 0)
                    frames.push(g2.render().slice());
                i++;
            });
            let k = 0;
            const play = () => {
                if (k >= frames.length) {
                    running = true;
                    last = 0;
                    requestAnimationFrame(step);
                    return;
                }
                view.setPhase(Math.floor(k / 2));
                view.draw(frames[k]);
                k++;
                setTimeout(play, 40);
            };
            play();
        });
    }
    window.addEventListener('resize', () => view.fit(host.clientWidth || 320));
    view.fit(host.clientWidth || 320);
    api.w(host, '', 'dim');
    out.innerHTML = '';
    out.appendChild(wrap);
    view.draw(g.render());
    status();
    requestAnimationFrame(step);
}
  });

  root.__isorpg = { require: __req };
  // 덱의 데모 틀에 미니 RPG 를 등록한다. 등록만 하고 실행은 슬라이드가 열릴 때 한다 —
  // 1MB 짜리 문서에서 안 보는 데모까지 도는 것은 낭비다.
  if (root.__demo) {
    root.__demo('mini-rpg', function (host, api) {
      __req('web/minirpg').boot(host, api);
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);
