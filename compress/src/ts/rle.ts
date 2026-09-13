// 런 길이 부호 — SPEC §3.
//
// 정한 값 셋이 출력 바이트를 바꾼다: 문턱 3, 런 상한 128, 리터럴 상한
// 128. 리터럴 묶음을 min(j+r, i+128) 로 자르는 것이 특히 중요하다 — 안
// 자르면 129바이트 묶음이 나오는데, 제어 바이트에 안 들어가는 길이라 못
// 푼다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export const RUN_MIN = 3;
export const RUN_MAX = 128;
export const LIT_MAX = 128;
export const RESERVED = 128;

function runAt(src: Bytes, i: number, limit: number): number {
  const b = src[i];
  let j = i + 1;
  const end = Math.min(src.length, i + limit);
  while (j < end && src[j] === b) j++;
  return j - i;
}

export function pack(src: Bytes): Bytes {
  const out = new ByteBuf();
  let i = 0;
  const n = src.length;
  while (i < n) {
    const run = runAt(src, i, RUN_MAX);
    if (run >= RUN_MIN) {
      out.push(257 - run);
      out.push(src[i]);
      i += run;
      continue;
    }
    let j = i;
    while (j < n && j - i < LIT_MAX) {
      const r = runAt(src, j, RUN_MAX);
      if (r >= RUN_MIN) break;
      j = Math.min(j + r, i + LIT_MAX);
    }
    out.push(j - i - 1);
    out.extend(src, i, j);
    i = j;
  }
  return out.bytes();
}

export function unpack(src: Bytes, pos: number,
                       want: number): [Bytes, number] {
  const out = new ByteBuf();
  const n = src.length;
  while (out.size < want) {
    if (pos >= n) fail('PackBits 가 잘렸다');
    const c = src[pos++];
    if (c === RESERVED) fail('제어 128 은 쓰지 않는다');
    if (c < RESERVED) {
      const k = c + 1;
      if (pos + k > n) fail('리터럴 묶음이 잘렸다');
      out.extend(src, pos, pos + k);
      pos += k;
    } else {
      const k = 257 - c;
      if (pos >= n) fail('런 묶음이 잘렸다');
      for (let j = 0; j < k; j++) out.push(src[pos]);
      pos++;
    }
  }
  if (out.size !== want) fail('푼 길이가 헤더와 다르다');
  return [out.bytes(), pos];
}

export function encode(src: Bytes): Bytes {
  return concat([varint.put(src.length), pack(src)]);
}

export function decode(src: Bytes): Bytes {
  const [n, at] = varint.getLength(src, 0);
  const [out, pos] = unpack(src, at, n);
  if (pos !== src.length) fail('뒤에 남은 바이트가 있다');
  return out;
}

// 0런 부호 (SPEC §3.2) — bzip2 의 RUNA/RUNB. bzip2dec(§15)이 쓴다.
export const RUN_A = 0;
export const RUN_B = 1;

export function zeroRunEncode(syms: number[]): number[] {
  const out: number[] = [];
  let i = 0;
  const n = syms.length;
  while (i < n) {
    if (syms[i] !== 0) {
      out.push(syms[i] + 1);
      i++;
      continue;
    }
    let j = i;
    while (j < n && syms[j] === 0) j++;
    let length = j - i + 1;
    while (length > 1) {
      out.push(length % 2 === 1 ? RUN_B : RUN_A);
      length = Math.floor(length / 2);
    }
    i = j;
  }
  return out;
}

export function zeroRunDecode(syms: number[]): number[] {
  const out: number[] = [];
  let i = 0;
  const n = syms.length;
  while (i < n) {
    if (syms[i] > 1) {
      out.push(syms[i] - 1);
      i++;
      continue;
    }
    let run = 0;
    let weight = 1;
    while (i < n && syms[i] <= 1) {
      run += (syms[i] + 1) * weight;
      weight *= 2;
      i++;
    }
    for (let j = 0; j < run; j++) out.push(0);
  }
  return out;
}
