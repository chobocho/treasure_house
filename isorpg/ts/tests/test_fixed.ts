// 고정소수점 모듈 — 경계값과 오차 상계를 실제로 확인한다.
import * as H from './harness';
import * as F from '../src/fixed';

/** 테스트 전용 난수. 파이썬 쪽은 (1103515245*rs+12345) % 2^31 을 그냥 쓰지만
 *  1103515245 * 2^31 ~ 2^61 이라 배정밀도로는 곱이 깨진다. 엔진의 LCG 와
 *  똑같이 상·하위 16비트로 쪼개면 중간값이 2^47 아래로 내려온다. */
function lcg31(s: number): number {
  const sh = Math.floor(s / 65536);
  const sl = s - sh * 65536;
  const lo = 1103515245 * sl + 12345;
  const hi = 1103515245 * sh;
  return F.fmod(F.fmod(hi, 32768) * 65536 + lo, 2147483648);
}

export function run(): number {
  H.title('fixed');

  // ---- floordiv / fmod : 음수에서도 내림인가
  const DIVC: number[][] = [
    [7, 2, 3, 1], [-7, 2, -4, 1], [0, 3, 0, 0], [-1, 65536, -1, 65535],
    [-65536, 65536, -1, 0], [-65537, 65536, -2, 65535],
  ];
  for (const row of DIVC) {
    const a = row[0] as number;
    const b = row[1] as number;
    H.check('floordiv(' + a + ',' + b + ')', F.floordiv(a, b), row[2] as number);
    H.check('fmod(' + a + ',' + b + ')', F.fmod(a, b), row[3] as number);
  }

  // ---- fp 변환
  H.check('fp(3)', F.fp(3), 196608);
  H.check('fp_floor(-1)', F.fpFloor(-1), -1);
  H.check('fp_round(32767)', F.fpRound(32767), 0);
  H.check('fp_round(32768)', F.fpRound(32768), 1);
  H.check('fp_frac(-1)', F.fpFrac(-1), 65535);

  // ---- fp_mul : 분할 곱이 진짜 곱과 같은가 (전수는 못 하니 경계 + 무작위)
  const CASES: Array<[number, number]> = [
    [0, 0], [1, 1], [65536, 65536], [-65536, 65536], [65535, 65535],
    [-1, 1], [1, -1], [-1, -1], [1073741824, 3], [-1073741824, 3],
    [46341, 46341], [13107, 46341], [2147483647, 5], [-2147483648, 5],
  ];
  let rs = 12345;
  for (let i = 0; i < 4000; i++) {
    rs = lcg31(rs);
    const a = (rs % 134217728) - 67108864;
    rs = lcg31(rs);
    const b = (rs % 134217728) - 67108864;
    CASES.push([a, b]);
  }
  let bad = 0;
  for (const [a, b] of CASES) {
    // |a|,|b| < 2^27 이라 a*b < 2^54... 는 아니고 2^53 미만이라 참값을 그대로 쓸 수 있다
    if (F.fpMul(a, b) !== Math.floor((a * b) / 65536)) bad += 1;
  }
  H.check('fp_mul == floor(a*b/65536) (' + CASES.length + '개)', bad, 0);
  H.note('중간값 상계 확인: |a|<2^31, |b|<2^37 에서 분할 곱의 항이 2^53 미만');

  // ---- fp_div
  bad = 0;
  for (const [a, b] of CASES) {
    const aa = a < 0 ? -a : a;
    if (b !== 0 && aa < 134217728 && F.fpDiv(a, b) !== Math.floor((a * 65536) / b)) bad += 1;
  }
  H.check('fp_div == floor(a*65536/b)', bad, 0);

  // ---- isqrt : 0, 1, 완전제곱수 앞뒤, 큰 값
  const NS: number[] = [];
  for (let n = 0; n < 2000; n++) NS.push(n);
  NS.push(65535, 65536, 65537, 1000000, 4294967295, 8796093022207);
  bad = 0;
  for (const n of NS) {
    const r = F.isqrt(n);
    if (!(r * r <= n && n < (r + 1) * (r + 1))) bad += 1;
  }
  H.check('isqrt 불변식 r^2 <= n < (r+1)^2', bad, 0);
  H.check('isqrt(0)', F.isqrt(0), 0);
  H.check('fp_sqrt(fp(1))', F.fpSqrt(65536), 65536);
  H.check('fp_sqrt(fp(2))', F.fpSqrt(131072), 92681);

  // ---- CORDIC : 참값과의 오차 상계 (테스트에서만 부동소수점을 쓴다)
  let mx = 0;
  for (let a = 0; a < 256; a++) {
    const tc = Math.round(65536 * Math.cos((2 * Math.PI * a) / 256));
    const ts = Math.round(65536 * Math.sin((2 * Math.PI * a) / 256));
    mx = Math.max(mx, Math.abs((F.COS[a] as number) - tc), Math.abs((F.SIN[a] as number) - ts));
  }
  H.checkTrue('CORDIC 표 오차 <= 1 (실측 ' + mx + ')', mx <= 1);
  H.check('SIN[0]', F.SIN[0], 0);
  H.check('COS[0]', F.COS[0], 65536);
  H.check('SIN[32] == COS[32] == 46341', [F.SIN[32], F.COS[32]], [46341, 46341]);
  H.check('SIN[64]', F.SIN[64], 65536);
  let mx2 = 0;
  for (let a = 0; a < 256; a++) {
    const s = F.SIN[a] as number;
    const c = F.COS[a] as number;
    const e = Math.abs(F.fpMul(s, s) + F.fpMul(c, c) - 65536);
    if (e > mx2) mx2 = e;
  }
  H.checkTrue('sin^2+cos^2 오차 <= 2/65536 (실측 ' + mx2 + ')', mx2 <= 2);

  // ---- 팔각 거리 오차
  let lo = 1000000000;
  let hi = -1000000000;
  for (let a = 0; a < 256; a++) {
    const dx = F.floordiv(1000 * (F.COS[a] as number), 65536);
    const dy = F.floordiv(1000 * (F.SIN[a] as number), 65536);
    const ex = F.isqrt(dx * dx + dy * dy);
    if (ex) {
      const e = F.floordiv((F.octDist(dx, dy) - ex) * 1000000, ex);
      if (e < lo) lo = e;
      if (e > hi) hi = e;
    }
  }
  H.note('팔각 거리 상대오차 ' + lo + ' ~ ' + hi + ' ppm');
  H.checkTrue('팔각 거리 오차가 ±5% 안', -50000 < lo && hi < 50000);
  H.check('oct_dist(3,4)', F.octDist(3, 4), 5);
  H.check('oct_dist(0,0)', F.octDist(0, 0), 0);

  // ---- xor16 : 표 없이 만든 배타적 논리합이 진짜 xor 인가
  bad = 0;
  let pairs = 0;
  for (let a = 0; a < 65536; a += 251) {
    for (let b = 0; b < 65536; b += 257) {
      pairs += 1;
      // a, b 가 16비트라 여기서는 JS 의 ^ 를 참값으로 써도 안전하다
      if (F.xor16(a, b) !== (a ^ b)) bad += 1;
    }
  }
  H.check('xor16 == ^ (표본 ' + pairs + '쌍)', bad, 0);

  return H.done();
}
