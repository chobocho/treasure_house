// Adler-32 과 CRC-32 — SPEC §10.8.
//
// 표는 다항식에서 만든다. 숫자 256개를 다섯 언어에 옮겨 적으면 틀린다.
// 결과는 >>> 0 으로 부호 없는 32비트로 되돌린다 — 안 하면 음수가
// 나온다.
import { Bytes } from './common';

export const ADLER_MOD = 65521;
// b 가 32비트를 넘기 전에 나눠야 하는 폭 (zlib 의 NMAX)
export const ADLER_NMAX = 5552;
export const CRC_POLY = 0xedb88320;

export function adler32(data: Bytes): number {
  let a = 1;
  let b = 0;
  for (let i = 0; i < data.length; i += ADLER_NMAX) {
    const end = Math.min(data.length, i + ADLER_NMAX);
    for (let j = i; j < end; j++) {
      a += data[j];
      b += a;
    }
    a %= ADLER_MOD;
    b %= ADLER_MOD;
  }
  return (b * 65536 + a) >>> 0;
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) {
      c = (c & 1) !== 0 ? (c >>> 1) ^ CRC_POLY : c >>> 1;
    }
    t[i] = c >>> 0;
  }
  return t;
})();

export function crc32(data: Bytes): number {
  let c = 0xffffffff;
  for (const b of data) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
