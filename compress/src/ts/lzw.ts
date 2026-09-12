// LZ78 계열 — SPEC §7.
//
// **복호기는 부호기보다 항목 하나 뒤처진다.** 그래서 폭을 늘리는 조건이
// 부호기는 nextFree, 복호기는 nextFree+1 이다. 이 한 칸을 틀리면 사전
// 254번째 항목쯤부터 어긋난다 — 작은 시험은 전부 통과한다.
import { ByteBuf, Bytes, concat, fail } from './common';
import { MsbReader, MsbWriter } from './bitio';
import * as varint from './varint';

export const CLEAR = 256;
export const EOF = 257;
export const FIRST_FREE = 258;
export const MIN_WIDTH = 9;
export const MAX_WIDTH = 12;
export const DICT_CAP = 1 << MAX_WIDTH;

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const w = new MsbWriter();
  // 열쇠는 (앞 부호 << 8) | 다음 바이트 — 트라이를 Map 하나로 눌러 담은
  // 것.
  let table = new Map<number, number>();
  let nextFree = FIRST_FREE;
  let width = MIN_WIDTH;
  let cur = -1;
  for (const k of src) {
    if (cur < 0) {
      cur = k;
      continue;
    }
    const key = cur * 256 + k;
    const found = table.get(key);
    if (found !== undefined) {
      cur = found;
      continue;
    }
    w.writeBits(cur, width);
    if (nextFree === DICT_CAP) {
      w.writeBits(CLEAR, width);
      table = new Map<number, number>();
      nextFree = FIRST_FREE;
      width = MIN_WIDTH;
    } else {
      table.set(key, nextFree++);
      // 폭 검사는 항목을 넣은 뒤에 — 다음 부호부터 넓어진다.
      if (nextFree === 1 << width && width < MAX_WIDTH) width++;
    }
    cur = k;
  }
  if (cur >= 0) w.writeBits(cur, width);
  w.writeBits(EOF, width);
  w.flush();
  return concat([varint.put(src.length), w.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  const r = new MsbReader(src, pos);
  const out = new ByteBuf();
  const table = new Array<Uint8Array>(DICT_CAP);
  let nextFree = FIRST_FREE;
  let width = MIN_WIDTH;
  let prev: Uint8Array | null = null;
  for (;;) {
    const code = r.readBits(width);
    if (code === EOF) break;
    if (code === CLEAR) {
      nextFree = FIRST_FREE;
      width = MIN_WIDTH;
      prev = null;
      continue;
    }
    let entry: Uint8Array;
    if (prev === null) {
      if (code >= CLEAR) fail(`첫 부호가 리터럴이 아니다: ${code}`);
      entry = Uint8Array.of(code);
    } else if (code < 256) {
      entry = Uint8Array.of(code);
    } else if (code < nextFree) {
      entry = table[code];
    } else if (code === nextFree) {
      // KwKwK — 부호기가 방금 만든 항목이다. 늘 prev + prev[0] 이다.
      entry = concat([prev, Uint8Array.of(prev[0])]);
    } else {
      return fail(`아직 없는 부호: ${code}`);
    }
    out.extend(entry);
    if (out.size > n) fail('푼 길이가 헤더를 넘었다');
    if (prev !== null) {
      table[nextFree++] = concat([prev, Uint8Array.of(entry[0])]);
      // 복호기는 한 칸 뒤처져 있다. +1 이 그 보정이다.
      if (nextFree + 1 === 1 << width && width < MAX_WIDTH) width++;
    }
    prev = entry;
  }
  if (out.size !== n) {
    fail(`푼 길이가 헤더와 다르다: ${out.size} != ${n}`);
  }
  return out.bytes();
}
