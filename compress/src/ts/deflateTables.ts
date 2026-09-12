// DEFLATE 의 표들 — SPEC §10.3 (RFC 1951).
//
// 길이 부호 284 는 227..257 까지만 적을 수 있고, **길이 258 은 늘 285**
// 다. 284 + 여분 31 로도 258 이 되지만 진짜 부호기는 아무도 그러지
// 않는다.
import { fail } from './common';

export const MIN_MATCH = 3;
export const MAX_MATCH = 258;
export const MAX_DIST = 32768;
export const END_OF_BLOCK = 256;
export const LITLEN_SYMBOLS = 286;
export const DIST_SYMBOLS = 30;
export const CL_SYMBOLS = 19;
export const CL_MAX_LENGTH = 7;
export const CL_REPEAT = 16;
export const CL_ZERO_SHORT = 17;
export const CL_ZERO_LONG = 18;

export const LENGTH_EXTRA = [
  0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2,
  2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0,
];
export const LENGTH_BASE = [
  3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23,
  27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258,
];
export const DIST_EXTRA = [
  0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6,
  6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13,
];
export const DIST_BASE = [
  1, 2, 3, 4, 5, 7, 9, 13, 17, 25,
  33, 49, 65, 97, 129, 193, 257, 385, 513, 769,
  1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577,
];

// 자주 0 이 되는 것을 뒤로 몰아 HCLEN 으로 꼬리를 자를 수 있게 한 순서.
export const CL_ORDER = [
  16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15,
];

export const LENGTH_CODE = (() => {
  const t = new Int32Array(MAX_MATCH + 1);
  for (let code = 0; code < LENGTH_BASE.length; code++) {
    const base = LENGTH_BASE[code];
    let top = base + 2 ** LENGTH_EXTRA[code] - 1;
    if (base === MAX_MATCH) top = MAX_MATCH;
    for (let ln = base; ln <= top && ln <= MAX_MATCH; ln++) {
      t[ln] = 257 + code;
    }
  }
  t[MAX_MATCH] = 285; // 284 가 아니라 285 로 못 박는다
  return t;
})();

export function distCode(dist: number): number {
  for (let code = DIST_SYMBOLS - 1; code >= 0; code--) {
    if (dist >= DIST_BASE[code]) return code;
  }
  return fail(`거리가 1보다 작다: ${dist}`);
}

export const FIXED_LITLEN = (() => {
  const l = new Array<number>(288).fill(8);
  for (let s = 144; s < 256; s++) l[s] = 9;
  for (let s = 256; s < 280; s++) l[s] = 7;
  return l;
})();

export const FIXED_DIST = new Array<number>(32).fill(5);
