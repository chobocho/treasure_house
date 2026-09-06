// 난수 — 주기·분할 곱·모듈로 편향 (SPEC §3).

import * as H from './harness';
import { LCG } from '../src/rng';

H.title('rng');

// ---- 골든 4절과 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 4. LCG ==') + 2;
let g = new LCG(1);
let bad = 0;
for (let k = 0; k < 10; k += 1) {
  const p = H.fields(rows[i + k]);
  const v = g.next15();
  if (g.s !== parseInt(p[1], 10) || v !== parseInt(p[2], 10)) {
    bad += 1;
    H.note((k + 1) + '번째: 기대 상태 ' + p[1] + ' next15 ' + p[2]
           + ' / 실제 ' + g.s + ' ' + v);
  }
}
H.check('LCG 첫 10회가 골든과 같다', bad, 0);

// ---- 분할 곱이 직접 곱과 같은가
//      파이썬은 큰 정수를 그대로 곱해 확인하지만 JS 는 2^53 을 넘으므로
//      여기서도 32비트 곱을 두 조각으로 나눠 대조군을 만든다.
function mul32(s: number): number {
  const A = 22695477;
  const hi = Math.floor(s / 65536);
  const lo = s % 65536;
  return (A * lo + ((A * hi) % 65536) * 65536 + 1) % 4294967296;
}
g = new LCG(12345);
bad = 0;
let direct = 12345;
for (let k = 0; k < 20000; k += 1) {
  g.next15();
  direct = mul32(direct);
  if (g.s !== direct) {
    bad += 1;
    break;
  }
}
H.check('분할 곱 == (22695477*s+1) mod 2^32 (2만회)', bad, 0);

// ---- 중간값이 2^53 을 넘지 않는가
let worst = 0;
g = new LCG(1);
for (let k = 0; k < 5000; k += 1) {
  const s = g.s;
  worst = Math.max(worst, 22695477 * (s % 65536),
                   22695477 * Math.floor(s / 65536));
  g.next15();
}
H.checkTrue('분할 항의 최대 ' + worst + ' < 2^53', worst < Math.pow(2, 53));

// ---- Hull–Dobell 세 조건 (SPEC 정리 3.2)
const A = 22695477;
const c = 1;
H.check('gcd(c, m) == 1', c === 1 ? 1 : 0, 1);
H.check('m 의 소인수 2 가 a-1 을 나눈다', (A - 1) % 2, 0);
H.check('4 | m 이므로 4 | a-1', (A - 1) % 4, 0);

// ---- 하위 비트의 짧은 주기: 상태의 하위 k비트는 주기 2^k
bad = 0;
for (const k of [1, 2, 3, 8]) {
  g = new LCG(1);
  const seen: number[] = [];
  const period = Math.pow(2, k);
  for (let t = 0; t < period * 3; t += 1) {
    g.next15();
    seen.push(g.s % period);
  }
  if (!H.deepEq(seen.slice(0, period), seen.slice(period, period * 2))) bad += 1;
}
H.check('상태 하위 k비트의 주기가 2^k', bad, 0);
H.note('그래서 next15 는 상위 15비트(비트 30..16)만 쓴다');

// ---- roll: 범위와 편향
g = new LCG(2026);
bad = 0;
for (let k = 0; k < 20000; k += 1) {
  const v = g.roll(7);
  if (!(v >= 0 && v < 7)) bad += 1;
}
H.check('roll(7) 범위', bad, 0);
H.check('roll(0)', new LCG(1).roll(0), 0);
H.check('roll(1)', new LCG(1).roll(1), 0);

i = rows.indexOf('== 4. LCG ==');
const P20 = 'roll(6) x20: ';
const line20 = rows.slice(i, i + 30).filter((l) => l.indexOf(P20) === 0)[0];
const want20 = H.ints(line20.slice(P20.length));
g = new LCG(2026);
const got20: number[] = [];
for (let k = 0; k < 20; k += 1) got20.push(g.roll(6));
H.check('roll(6) 20회가 골든과 같다', got20, want20);
const P6K = 'roll(6) x6000 도수: ';
const line6k = rows.slice(i, i + 30).filter((l) => l.indexOf(P6K) === 0)[0];
const want6k = H.ints(line6k.slice(P6K.length));
g = new LCG(2026);
const hist = [0, 0, 0, 0, 0, 0];
for (let k = 0; k < 6000; k += 1) hist[g.roll(6)] += 1;
H.check('roll(6) 6000회 도수가 골든과 같다', hist, want6k);
H.note('기각 ' + g.rejects + '회 — 기대 시도 횟수는 2 미만이어야 한다');
H.checkTrue('기각 횟수가 표본의 절반 미만', g.rejects < 3000);

// ---- 편향 실험: 기각 없이 나머지만 쓰면 어떻게 되는가
g = new LCG(7);
const biased = [0, 0, 0];
const nSamples = 32768 * 4;
for (let k = 0; k < nSamples; k += 1) biased[g.next15() % 3] += 1;
H.note('나머지만 쓴 roll(3) 도수 [' + biased.join(', ')
       + '] (32768 이 3으로 나뉘지 않는다)');
H.checkTrue('세 도수가 완전히 같지는 않다', H.sortedSet(biased).length > 1);

// ---- 상태 저장·복원
g = new LCG(99);
for (let k = 0; k < 50; k += 1) g.next15();
const saved = g.save();
const a: number[] = [];
for (let k = 0; k < 10; k += 1) a.push(g.next15());
g.load(saved);
const b: number[] = [];
for (let k = 0; k < 10; k += 1) b.push(g.next15());
H.check('save/load 후 같은 수열', a, b);

H.done();
