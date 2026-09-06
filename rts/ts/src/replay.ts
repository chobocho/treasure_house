// 저장·리플레이·압축 (SPEC §20).
//
//    리플레이는 **명령 로그**다. 상태는 한 바이트도 저장하지 않는다. 재생한다는
//    것은 같은 시드로 시뮬을 새로 만들어 같은 명령을 같은 틱에 먹이는 것이고,
//    결과가 같다는 증명은 `hashes.txt` 와의 대조가 대신한다.
//
//    비트 연산자는 쓰지 않는다(§1.1). LZSS 의 토큰도 곱셈과 나눗셈으로 접는다.

import * as F from './fixed';

export const MAGIC = 'RTSR';
export const VERSION = 1;
export const WINDOW = 4096;
export const MIN_MATCH = 3;
export const MAX_MATCH = 18;

export type Order = number[];
export type LogEntry = [number, Order[]];

function b2(out: number[], v0: number): void {
  const v = F.fmod(v0, 65536);
  out.push(F.floordiv(v, 256));
  out.push(F.fmod(v, 256));
}

function b4(out: number[], v0: number): void {
  const v = F.fmod(v0, 4294967296);
  b2(out, F.floordiv(v, 65536));
  b2(out, F.fmod(v, 65536));
}

function r2(b: number[], i: number): [number, number] {
  return [b[i] * 256 + b[i + 1], i + 2];
}

function r4(b: number[], i0: number): [number, number] {
  const [hi, i1] = r2(b, i0);
  const [lo, i2] = r2(b, i1);
  return [hi * 65536 + lo, i2];
}

// 로그 항목 정렬 — 파이썬 sorted(log) 와 같은 순서(틱, 그다음 명령 목록).
function cmpLog(a: LogEntry, b: LogEntry): number {
  if (a[0] !== b[0]) return a[0] < b[0] ? -1 : 1;
  const n = Math.min(a[1].length, b[1].length);
  for (let i = 0; i < n; i += 1) {
    const x = a[1][i];
    const y = b[1][i];
    for (let k = 0; k < x.length && k < y.length; k += 1) {
      if (x[k] !== y[k]) return x[k] < y[k] ? -1 : 1;
    }
  }
  return a[1].length - b[1].length;
}

// ── SPEC §20.2 ──────────────────────────────────────────────────────────────
// log 는 (틱, 명령 목록). 명령은 §18.1 의 여섯 칸이다.
export function save(seed: number, players: number, ticks: number,
                     log: LogEntry[]): number[] {
  const out: number[] = [];
  for (const ch of MAGIC) out.push(ch.charCodeAt(0));
  out.push(VERSION);
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
      out.push(o[0]);                        // 플레이어
      out.push(o[2]);                        // 종류
      b2(out, o[1]);                         // 발령자 핸들
      out.push(o[3]);
      out.push(o[4]);
      b2(out, o[5]);
    }
  }
  const crc = F.crc16(out);
  b2(out, crc);
  return out;
}

export function load(blob: ArrayLike<number>): [number, number, number, LogEntry[]] {
  const b: number[] = [];
  for (let i = 0; i < blob.length; i += 1) b.push(blob[i]);
  if (String.fromCharCode(b[0], b[1], b[2], b[3]) !== MAGIC) {
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
  const log: LogEntry[] = [];
  for (let k = 0; k < n; k += 1) {
    let t = 0;
    [t, i] = r4(b, i);
    const cnt = b[i];
    i += 1;
    const orders: Order[] = [];
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
export function rleEncode(data: ArrayLike<number>): number[] {
  const out: number[] = [];
  let i = 0;
  while (i < data.length) {
    const v = data[i];
    let run = 1;
    while (i + run < data.length && data[i + run] === v && run < 255) run += 1;
    out.push(run);
    out.push(v);
    i += run;
  }
  return out;
}

export function rleDecode(data: ArrayLike<number>): number[] {
  const out: number[] = [];
  let i = 0;
  while (i < data.length) {
    for (let k = 0; k < data[i]; k += 1) out.push(data[i + 1]);
    i += 2;
  }
  return out;
}

// ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
// 가장 긴 일치, 동점이면 가장 가까운 것. 탐욕적이다 — 최적 파싱은 안 한다.
// O(창 × 최대일치) = 4096 × 18. 20부는 이 단순함의 대가를 실측으로 보인다.
function match(b: number[], pos: number): [number, number] {
  let bestLen = 0;
  let bestOff = 0;
  let start = pos - WINDOW;
  if (start < 0) start = 0;
  let limit = b.length - pos;
  if (limit > MAX_MATCH) limit = MAX_MATCH;
  for (let j = pos - 1; j >= start; j -= 1) {   // 가까운 쪽부터 훑는다
    let k = 0;
    while (k < limit && b[j + k] === b[pos + k]) k += 1;  // 겹치는 일치도 허용
    if (k > bestLen) {
      bestLen = k;
      bestOff = pos - j;
      if (bestLen === limit) break;
    }
  }
  return [bestLen, bestOff];
}

export function lzssEncode(data: ArrayLike<number>): number[] {
  const b: number[] = [];
  for (let i = 0; i < data.length; i += 1) b.push(data[i]);
  const out: number[] = [];
  let pos = 0;
  while (pos < b.length) {
    let flag = 0;
    const chunk: number[] = [];
    let bit = 1;
    let used = 0;
    while (used < 8 && pos < b.length) {
      const [ln, off] = match(b, pos);
      if (ln >= MIN_MATCH) {
        const o = off - 1;                    // 1..4096 → 0..4095
        chunk.push(F.floordiv(o, 16));
        chunk.push(F.fmod(o, 16) * 16 + (ln - MIN_MATCH));
        pos += ln;
      } else {
        flag += bit;                          // 비트 1 = 리터럴
        chunk.push(b[pos]);
        pos += 1;
      }
      bit *= 2;
      used += 1;
    }
    out.push(flag);
    for (const v of chunk) out.push(v);
  }
  return out;
}

export function lzssDecode(data: ArrayLike<number>): number[] {
  const b: number[] = [];
  for (let i = 0; i < data.length; i += 1) b.push(data[i]);
  const out: number[] = [];
  let i = 0;
  while (i < b.length) {
    let flag = b[i];
    i += 1;
    for (let k = 0; k < 8; k += 1) {
      if (i >= b.length) break;
      if (F.fmod(flag, 2) === 1) {
        out.push(b[i]);
        i += 1;
      } else {
        const o = b[i] * 16 + F.floordiv(b[i + 1], 16);
        const ln = F.fmod(b[i + 1], 16) + MIN_MATCH;
        i += 2;
        const src = out.length - (o + 1);
        for (let j = 0; j < ln; j += 1) out.push(out[src + j]);  // 겹침 허용
      }
      flag = F.floordiv(flag, 2);
    }
  }
  return out;
}
