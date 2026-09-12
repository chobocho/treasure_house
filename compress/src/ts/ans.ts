// ANS — 비대칭 수 체계 — SPEC §13.
//
// rANS 는 **스택** 이다. 부호기가 입력을 뒤에서부터 밀어 넣고 복호기가
// 앞에서부터 꺼낸다.
//
// 상태 x 는 (x / f) * TOTAL 에서 2^31 에 닿는다. TS 의 비트 연산자는
// 부호 있는 32비트라 거기서 음수가 된다 — x << 8 대신 x * 256 % 2^32,
// x >> 12 대신 Math.floor(x / 4096) 를 쓴다 (SPEC §0.5).
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export const TOTAL_BITS = 12;
export const TOTAL = 1 << TOTAL_BITS;
export const L = 2 ** 23;
export const ALPHABET = 256;
// tANS 의 퍼뜨리기 걸음 (zstd 의 값). 홀수라서 2의 거듭제곱 칸을
// 빠짐없이 한 번씩 돈다.
export const SPREAD_STEP = (TOTAL >> 1) + (TOTAL >> 3) + 3;
const U32 = 0x100000000;

// 빈도를 합이 정확히 TOTAL 이 되게 고친다 (SPEC §13.3).
// 남으면 가장 큰 기호에 한꺼번에, 모자라면 가장 큰 데서 되풀이해 뺀다.
// 동점이면 번호가 작은 쪽.
export function normalise(counts: number[]): number[] {
  let total = 0;
  for (const c of counts) total += c;
  const f = new Array<number>(ALPHABET).fill(0);
  if (total === 0) return f;
  for (let s = 0; s < ALPHABET; s++) {
    if (counts[s] > 0) {
      f[s] = Math.max(1, Math.floor((counts[s] * TOTAL) / total));
    }
  }
  let sum = 0;
  for (const v of f) sum += v;
  let d = TOTAL - sum;
  while (d !== 0) {
    let best = 0;
    for (let s = 1; s < ALPHABET; s++) {
      if (f[s] > f[best]) best = s;
    }
    if (d > 0) {
      f[best] += d;
      d = 0;
    } else {
      const take = Math.min(-d, f[best] - 1);
      if (take === 0) fail('빈도를 TOTAL 에 못 맞춘다');
      f[best] -= take;
      d += take;
    }
  }
  return f;
}

export function cumulative(f: number[]): number[] {
  const cum = new Array<number>(ALPHABET).fill(0);
  let total = 0;
  for (let s = 0; s < ALPHABET; s++) {
    cum[s] = total;
    total += f[s];
  }
  return cum;
}

export function slotSymbols(f: number[], cum: number[]): Uint8Array {
  const slots = new Uint8Array(TOTAL);
  for (let s = 0; s < ALPHABET; s++) {
    for (let i = cum[s]; i < cum[s] + f[s]; i++) slots[i] = s;
  }
  return slots;
}

// tANS 의 상태표 (SPEC §13.6). 골든에는 안 들어가고 12부가 쓴다.
export function tansTable(f: number[]): Uint8Array {
  const table = new Uint8Array(TOTAL);
  let pos = 0;
  for (let s = 0; s < ALPHABET; s++) {
    for (let i = 0; i < f[s]; i++) {
      table[pos] = s;
      pos = (pos + SPREAD_STEP) & (TOTAL - 1);
    }
  }
  return table;
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const counts = new Array<number>(ALPHABET).fill(0);
  for (const b of src) counts[b] += 1;
  const f = normalise(counts);
  const cum = cumulative(f);

  const body: number[] = [];
  let x = L;
  // 뒤에서부터 민다. rANS 는 스택이고, 마지막에 넣은 것이 먼저 나온다.
  for (let i = src.length - 1; i >= 0; i--) {
    const s = src[i];
    const fs = f[s];
    const xmax = Math.floor(L / TOTAL) * 256 * fs;
    while (x >= xmax) {
      body.push(x % 256);
      x = Math.floor(x / 256);
    }
    x = Math.floor(x / fs) * TOTAL + (x % fs) + cum[s];
  }
  for (let i = 0; i < 4; i++) {
    body.push(Math.floor(x / 2 ** (8 * i)) % 256);
  }
  body.reverse();

  const head = new ByteBuf();
  head.extend(varint.put(src.length));
  for (let s = 0; s < ALPHABET; s++) head.extend(varint.put(f[s]));
  return concat([head.bytes(), Uint8Array.from(body)]);
}

export function decode(src: Bytes): Bytes {
  let [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  const f = new Array<number>(ALPHABET).fill(0);
  let sum = 0;
  for (let s = 0; s < ALPHABET; s++) {
    const [v, next] = varint.get(src, pos);
    pos = next;
    if (v > TOTAL) fail('빈도가 TOTAL 을 넘는다');
    f[s] = v;
    sum += v;
  }
  if (sum !== TOTAL) fail(`빈도의 합이 ${TOTAL} 이 아니다`);
  const cum = cumulative(f);
  const slots = slotSymbols(f, cum);

  if (src.length - pos < 4) fail('rANS 스트림이 너무 짧다');
  let x = 0;
  for (let i = 0; i < 4; i++) x = (x * 256 + src[pos + i]) % U32;
  let at = pos + 4;
  const out = new Uint8Array(n);
  for (let k = 0; k < n; k++) {
    const slot = x % TOTAL;
    const s = slots[slot];
    out[k] = s;
    x = f[s] * Math.floor(x / TOTAL) + slot - cum[s];
    while (x < L) {
      if (at >= src.length) fail('rANS 스트림이 모자란다');
      x = x * 256 + src[at++];
    }
  }
  if (at !== src.length) fail('뒤에 남은 바이트가 있다');
  return out;
}
