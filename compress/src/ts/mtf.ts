// move-to-front — SPEC §4.
//
// 앞으로 **옮기는** 것이지 바꿔치는 것이 아니다. 바꿔치기도
// 자기들끼리는 왕복이 되므로, 골든 벡터가 없으면 갈라진 줄도 모른다.
import { Bytes, concat, fail } from './common';
import * as varint from './varint';

export const ALPHABET = 256;

function identity(): Uint8Array {
  const t = new Uint8Array(ALPHABET);
  for (let i = 0; i < ALPHABET; i++) t[i] = i;
  return t;
}

export function transform(src: Bytes): Bytes {
  const table = identity();
  const out = new Uint8Array(src.length);
  for (let p = 0; p < src.length; p++) {
    const b = src[p];
    let i = 0;
    while (table[i] !== b) i++;
    out[p] = i;
    for (let k = i; k > 0; k--) table[k] = table[k - 1];
    table[0] = b;
  }
  return out;
}

export function inverse(src: Bytes): Bytes {
  const table = identity();
  const out = new Uint8Array(src.length);
  for (let p = 0; p < src.length; p++) {
    const idx = src[p];
    const b = table[idx];
    out[p] = b;
    for (let k = idx; k > 0; k--) table[k] = table[k - 1];
    table[0] = b;
  }
  return out;
}

export function encode(src: Bytes): Bytes {
  return concat([varint.put(src.length), transform(src)]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (src.length - pos !== n) {
    fail(`몸통 길이가 헤더와 다르다: ${src.length - pos} != ${n}`);
  }
  return inverse(src.subarray(pos));
}
