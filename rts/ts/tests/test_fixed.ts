// 고정소수점·거리·방향 — 경계값과 오차 상계를 실제로 확인한다 (SPEC §1, §2).

import * as H from './harness';
import * as F from '../src/fixed';
import * as C from '../src/const';

H.title('fixed');

// ---- floordiv / fmod : 음수에서도 내림인가
for (const [a, b, q, r] of [[7, 2, 3, 1], [-7, 2, -4, 1], [0, 3, 0, 0],
                            [-1, 65536, -1, 65535], [-65536, 65536, -1, 0],
                            [-65537, 65536, -2, 65535]]) {
  H.check('floordiv(' + a + ',' + b + ')', F.floordiv(a, b), q);
  H.check('fmod(' + a + ',' + b + ')', F.fmod(a, b), r);
}

// ---- 비트 연산의 산술 대체 (SPEC §1.1)
for (const [v, k, want] of [[0, 0, 0], [1, 0, 1], [2, 0, 0], [2, 1, 1],
                            [255, 7, 1], [128, 7, 1]]) {
  H.check('bit(' + v + ',' + k + ')', F.bit(v, k), want);
}
H.check('setbit(0,3)', F.setbit(0, 3), 8);
H.check('setbit(8,3)', F.setbit(8, 3), 8);
H.check('clrbit(9,3)', F.clrbit(9, 3), 1);
H.check('clrbit(1,3)', F.clrbit(1, 3), 1);
let bad = 0;
for (let a = 0; a < 256; a += 1) {
  for (let b = 0; b < 256; b += 7) {
    // 대조군만 비트 연산자를 쓴다 — 엔진 코드에는 한 개도 없다.
    /* eslint-disable no-bitwise */
    if (F.xor8(a, b) !== (a ^ b)) bad += 1;
    /* eslint-enable no-bitwise */
  }
}
H.check('xor8 == ^ (전수 근사)', bad, 0);
H.check('xor_low8(0x12345678, 0xFF)', F.xorLow8(0x12345678, 0xFF), 0x12345687);

// ---- fp 변환
H.check('fp(3)', F.fp(3), 196608);
H.check('fp_floor(-1)', F.fpFloor(-1), -1);
H.check('fp_round(32767)', F.fpRound(32767), 0);
H.check('fp_round(32768)', F.fpRound(32768), 1);
H.check('fp_frac(-1)', F.fpFrac(-1), 65535);
H.check('FP_DIAG', F.FP_DIAG, 46341);
H.check('FP_SQRT2M1', F.FP_SQRT2M1, 27146);

// ---- fp_mul : 분할 곱이 진짜 곱과 같은가
const CASES: Array<[number, number]> = [
  [0, 0], [1, 1], [65536, 65536], [-65536, 65536], [65535, 65535],
  [-1, 1], [1, -1], [-1, -1], [Math.pow(2, 30), 3], [-Math.pow(2, 30), 3],
  [46341, 46341], [13107, 46341], [2147483647, 5], [-2147483648, 5]];
let rs = 12345;
for (let k = 0; k < 4000; k += 1) {
  rs = H.lcg31(rs);
  const a = rs % Math.pow(2, 27) - Math.pow(2, 26);
  rs = H.lcg31(rs);
  const b = rs % Math.pow(2, 27) - Math.pow(2, 26);
  CASES.push([a, b]);
}
bad = 0;
let big = 0;
for (const [a, b] of CASES) {
  if (F.fpMul(a, b) !== F.floordiv(a * b, 65536)) bad += 1;
  const ah = F.floordiv(a, 65536);
  const al = F.fmod(a, 65536);
  big = Math.max(big, Math.abs(ah * b), Math.abs(al * b));
}
H.check('fp_mul == floor(a*b/65536) (' + CASES.length + '개)', bad, 0);
H.checkTrue('분할 곱 중간값 < 2^53 (최대 ' + big + ')', big < Math.pow(2, 53));

// ---- fp_div
bad = 0;
for (const [a, b] of CASES) {
  if (b !== 0 && Math.abs(a) < Math.pow(2, 27)
      && F.fpDiv(a, b) !== F.floordiv(a * 65536, b)) bad += 1;
}
H.check('fp_div == floor(a*65536/b)', bad, 0);
try {
  F.fpDiv(1, 0);
  H.check('fp_div(1,0) 은 터져야 한다', 'no raise', 'raise');
} catch (e) {
  H.check('fp_div(1,0) 은 터져야 한다', 'raise', 'raise');
}

// ---- isqrt
bad = 0;
const SQNS = H.range(0, 2000).concat([65535, 65536, 65537, 1000000,
                                      Math.pow(2, 31) - 1, Math.pow(2, 40)]);
for (const n of SQNS) {
  const r = F.isqrt(n);
  if (!(r * r <= n && n < (r + 1) * (r + 1))) bad += 1;
}
H.check('isqrt 는 floor(sqrt(n))', bad, 0);
H.check('fp_sqrt(fp(4))', F.fpSqrt(F.fp(4)), F.fp(2));

// ---- 거리 척도 (SPEC §2.6) — 골든 1절과 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 1. 거리 척도 ==') + 2;
bad = 0;
let n = 0;
while (rows[i].trim() !== '' && rows[i].indexOf('eu3') !== 0) {
  const v = H.ints(rows[i]);
  const dx = v[0];
  const dy = v[1];
  const got = [F.d1(dx, dy), F.dinf(dx, dy), F.d83(dx, dy), F.dab(dx, dy),
               F.doct(dx, dy)];
  if (!H.deepEq(got, v.slice(2, 7))) {
    bad += 1;
    H.note(dx + ',' + dy + ' 기대 ' + JSON.stringify(v.slice(2, 7))
           + ' 실제 ' + JSON.stringify(got));
  }
  n += 1;
  i += 1;
}
H.check('거리 척도 ' + n + '줄이 골든과 같다', bad, 0);
H.check('dab(1,0) 은 0 이 아니다', F.dab(1, 0), 1);
H.check('dinf 는 8방향 걸음 수', F.dinf(-7, 3), 7);

// ---- atan8 (SPEC §2.7)
i = rows.indexOf('== 3. 8방향 판별 ==') + 2;
bad = 0;
n = 0;
while (i < rows.length && rows[i].trim() !== '') {
  const p = H.fields(rows[i]);
  const dx = parseInt(p[0], 10);
  const dy = parseInt(p[1], 10);
  const want = parseInt(p[5], 10);
  if (F.atan8(dx, dy) !== want) {
    bad += 1;
    H.note('atan8(' + dx + ',' + dy + ') 기대 ' + want
           + ' 실제 ' + F.atan8(dx, dy));
  }
  n += 1;
  i += 1;
}
H.check('atan8 ' + n + '줄이 골든과 같다', bad, 0);
H.check('atan8(0,0) 은 E', F.atan8(0, 0), 2);
bad = 0;
for (let d = 0; d < 8; d += 1) {
  if (F.atan8(F.DX[d] * 9, F.DY[d] * 9) !== d) bad += 1;
}
H.check('여덟 방향의 대표 벡터가 자기 번호로 돌아온다', bad, 0);
H.note('경계각 tan22.5 ~ 5/12: (12,5)는 대각, (12,4)는 직각 방향');

// ── 골든 13절 CRC·FNV (SPEC §20.1, §18.4) ───────────────────────────────────
// 골든이 파이썬 %r 로 적었으므로 인자는 작은따옴표에 싸여 있다. eval 대신
// 따옴표를 벗겨 읽는다 — 들어 있는 문자열이 전부 단순 ASCII 라 그것으로 충분하다.
const g13 = H.golden('prim.txt').split('\n');
let i13 = g13.indexOf('== 13. CRC 와 FNV ==') + 1;
let bad13 = 0;
let n13 = 0;
while (i13 < g13.length && g13[i13].trim() !== '') {
  const parts = H.fields(g13[i13]);
  const fn = parts[0];
  const hx = parts[parts.length - 1];
  // 파이썬 rsplit(None, 2)[0] — 뒤에서 공백 두 번까지만 자른다.
  const rest = g13[i13].slice(fn.length);
  const arg = rest.replace(/\s+\S+\s*$/, '').replace(/\s+\S+\s*$/, '').trim();
  let data: number[];
  if (arg === 'bytes(0..15)') data = H.range(16);
  else data = F.ascii(arg.slice(1, arg.length - 1));
  const got = fn === 'crc16' ? F.crc16(data) : F.fnv1a(data);
  if (got !== parseInt(hx, 16)) {
    bad13 += 1;
    H.note(fn + ' ' + arg + ' 기대 ' + hx + ' 실제 ' + got);
  }
  n13 += 1;
  i13 += 1;
}
H.check('골든 13절 ' + n13 + '줄 (crc16·fnv1a)', bad13, 0);
H.check('FNV 오프셋과 소수', [F.FNV_OFFSET, F.FNV_PRIME],
        [2166136261, 16777619]);
H.check('빈 입력의 fnv1a 는 오프셋 그대로', F.fnv1a([]), F.FNV_OFFSET);
H.check('한 바이트 차이가 해시를 바꾼다',
        F.fnv1a([0]) !== F.fnv1a([1]), true);
let mxh = 0;
for (let k = 0; k < 256; k += 1) mxh = Math.max(mxh, F.fnv1a([k]));
H.check('32비트를 넘지 않는다', mxh < 4294967296, true);

// ── fixed 와 const 에 두 번 적힌 값은 서로 같아야 한다 (SPEC §0) ────────────
H.check('fixed 와 const 의 §0 값이 일치',
        [F.FP_BITS, F.FP_ONE, F.FP_HALF, F.FP_DIAG, F.FP_SQRT2M1,
         F.D_STRAIGHT, F.D_DIAG],
        [C.FP_BITS, C.FP_ONE, C.FP_HALF, C.FP_DIAG, C.FP_SQRT2M1,
         C.D_STRAIGHT, C.D_DIAG]);

H.done();
