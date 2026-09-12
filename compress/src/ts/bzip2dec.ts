// bzip2 복호기 — SPEC §15.
//
// bzip2 가 쓰는 조각은 이미 다 있다. BWT·MTF·0런·캐노니컬 허프만.
// bzip2 가 더한 것은 **조립** 이라, 부호기는 안 만든다 — 진짜 bzip2 가
// 만든 파일을 푸는 편이 훨씬 센 주장이다.
//
// 가장 잘 속는 자리는 CRC 다. bzip2 의 CRC-32 는 gzip 것과 다항식은
// 같아도 **반사가 없다.** gzip 표를 그대로 쓰면 빈 입력만 맞는다
// (§15.6).
import { ByteBuf, Bytes, fail } from './common';
import { inverseBlock } from './bwt';
import { Decoder, checkComplete } from './huffman';

export const BLOCK_MAGIC = 0x314159265359;
export const END_MAGIC = 0x177245385090;
export const MAX_GROUPS = 6;
export const GROUP_SIZE = 50;
export const MAX_CODE_LEN = 20;
// RUNA 는 0, RUNB 는 1 이다. 여기서는 "RUNB 이하" 만 보면 되므로
// RUN_B 하나로 판정한다 (SPEC §15.3).
const RUN_B = 1;

// 반사 없는 CRC-32/BZIP2 표. 다항식 0x04C11DB7 을 위에서부터 민다.
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = (i << 24) >>> 0;
    for (let k = 0; k < 8; k++) {
      c = (c & 0x80000000) !== 0 ? (((c << 1) >>> 0) ^ 0x04c11db7) >>> 0
                                 : (c << 1) >>> 0;
    }
    t[i] = c;
  }
  return t;
})();

export function crc32Bzip2(data: Bytes): number {
  let c = 0xffffffff;
  for (const b of data) {
    c = (CRC_TABLE[((c >>> 24) ^ b) & 0xff] ^ ((c << 8) >>> 0)) >>> 0;
  }
  return (c ^ 0xffffffff) >>> 0;
}

// MSB 먼저. bzip2 는 48비트 매직을 읽어야 해서 넓은 읽기가 필요하다.
// 48비트는 2^53 아래라 배정도로 정확하다 — 곱셈으로 이어 붙인다.
export class BitReader {
  private pos: number;
  private buf = 0;
  private n = 0;

  constructor(private src: Bytes, pos: number) {
    this.pos = pos;
  }

  readBit(): number {
    if (this.n === 0) {
      if (this.pos >= this.src.length) fail('bzip2 스트림이 바닥났다');
      this.buf = this.src[this.pos++];
      this.n = 8;
    }
    this.n--;
    return (this.buf >> this.n) & 1;
  }

  readBits(count: number): number {
    let v = 0;
    for (let i = 0; i < count; i++) v = v * 2 + this.readBit();
    return v;
  }
}

// 같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다 (§15.5).
export function rle1Decode(src: Bytes): Bytes {
  const out = new ByteBuf();
  let i = 0;
  const n = src.length;
  while (i < n) {
    const b = src[i];
    let run = 1;
    while (run < 4 && i + run < n && src[i + run] === b) run++;
    for (let k = 0; k < run; k++) out.push(b);
    i += run;
    if (run === 4) {
      if (i >= n) fail('RLE1 의 개수 바이트가 없다');
      for (let k = 0; k < src[i]; k++) out.push(b);
      i++;
    }
  }
  return out.bytes();
}

function readSymbolMap(r: BitReader): number[] {
  const used: number[] = [];
  const groups = r.readBits(16);
  for (let g = 0; g < 16; g++) {
    if ((groups & (1 << (15 - g))) !== 0) {
      const bits = r.readBits(16);
      for (let k = 0; k < 16; k++) {
        if ((bits & (1 << (15 - k))) !== 0) used.push(g * 16 + k);
      }
    }
  }
  if (used.length === 0) fail('기호 지도가 비었다');
  return used;
}

// 단항으로 적힌 MTF 선택자. 값이 곧 "몇 번째 표" 다.
function readSelectors(r: BitReader, nGroups: number,
                       nSelectors: number): number[] {
  const mtf = Array.from({ length: nGroups }, (_v, i) => i);
  const out: number[] = [];
  for (let i = 0; i < nSelectors; i++) {
    let j = 0;
    while (r.readBit() !== 0) {
      if (++j >= nGroups) fail('선택자가 표 개수를 넘는다');
    }
    const v = mtf[j];
    mtf.splice(j, 1);
    mtf.unshift(v);
    out.push(v);
  }
  return out;
}

function readTables(r: BitReader, nGroups: number,
                    alphaSize: number): Decoder[] {
  const tables: Decoder[] = [];
  for (let g = 0; g < nGroups; g++) {
    let length = r.readBits(5);
    const lengths: number[] = [];
    for (let s = 0; s < alphaSize; s++) {
      for (;;) {
        if (length < 1 || length > MAX_CODE_LEN) {
          fail(`부호 길이가 범위를 벗어났다: ${length}`);
        }
        if (r.readBit() === 0) break;
        length += r.readBit() !== 0 ? -1 : 1;
      }
      lengths.push(length);
    }
    checkComplete(lengths, MAX_CODE_LEN);
    tables.push(new Decoder(lengths, MAX_CODE_LEN));
  }
  return tables;
}

// 허프만 → MTF 지표 열. RUNA/RUNB 는 여기서 0 의 런으로 편다.
function readBlockSymbols(r: BitReader, tables: Decoder[],
                          selectors: number[], alphaSize: number,
                          limit: number): number[] {
  const eob = alphaSize - 1;
  const out: number[] = [];
  let group = 0;
  let left = 0;
  let dec: Decoder | null = null;
  let run = 0;
  let weight = 1;
  for (;;) {
    if (left === 0) {
      if (group >= selectors.length) fail('선택자가 모자란다');
      dec = tables[selectors[group]];
      group++;
      left = GROUP_SIZE;
    }
    left--;
    const sym = (dec as Decoder).read(r);
    if (sym <= RUN_B) {
      run += (sym + 1) * weight;
      weight *= 2;
      if (run > limit) fail('0 런이 블록 크기를 넘는다');
      continue;
    }
    if (run > 0) {
      for (let k = 0; k < run; k++) out.push(0);
      run = 0;
      weight = 1;
    }
    if (sym === eob) return out;
    out.push(sym - 1);
    if (out.length > limit) fail('블록이 상한을 넘는다');
  }
}

// 쓰인 값들만 놓고 MTF 를 되돌린다 — 기호 지도가 여기서 값을 한다.
function inverseMtf(indices: number[], used: number[]): Bytes {
  const table = used.slice();
  const out = new Uint8Array(indices.length);
  for (let k = 0; k < indices.length; k++) {
    const i = indices[k];
    if (i >= table.length) fail('MTF 지표가 알파벳을 넘는다');
    const v = table[i];
    out[k] = v;
    if (i !== 0) {
      table.splice(i, 1);
      table.unshift(v);
    }
  }
  return out;
}

export function decode(src: Bytes): Bytes {
  if (src.length < 4 || src[0] !== 0x42 || src[1] !== 0x5a ||
      src[2] !== 0x68) {
    fail('bzip2 매직이 아니다');
  }
  const level = src[3] - 0x30;
  if (level < 1 || level > 9) fail('블록 크기 등급이 1~9 가 아니다');
  const limit = level * 100000;
  const r = new BitReader(src, 4);
  const out = new ByteBuf();
  let combined = 0;
  for (;;) {
    const magic = r.readBits(48);
    if (magic === END_MAGIC) {
      const want = r.readBits(32);
      if (want !== combined) fail('합친 CRC 가 다르다');
      return out.bytes();
    }
    if (magic !== BLOCK_MAGIC) fail('블록 매직이 아니다');
    const blockCrc = r.readBits(32);
    if (r.readBit() !== 0) fail('무작위화된 블록은 지원하지 않는다');
    const origPtr = r.readBits(24);
    const used = readSymbolMap(r);
    const alphaSize = used.length + 2;
    const nGroups = r.readBits(3);
    if (nGroups < 2 || nGroups > MAX_GROUPS) {
      fail('표 개수가 2~6 이 아니다');
    }
    const nSelectors = r.readBits(15);
    const selectors = readSelectors(r, nGroups, nSelectors);
    const tables = readTables(r, nGroups, alphaSize);
    const indices =
      readBlockSymbols(r, tables, selectors, alphaSize, limit);
    const lColumn = inverseMtf(indices, used);
    if (origPtr >= lColumn.length) fail('origPtr 가 블록 밖이다');
    const block = rle1Decode(inverseBlock(lColumn, origPtr));
    if (crc32Bzip2(block) !== blockCrc) fail('블록 CRC 가 다르다');
    combined = (((combined << 1) >>> 0) | (combined >>> 31)) >>> 0;
    combined = (combined ^ blockCrc) >>> 0;
    out.extend(block);
  }
}
