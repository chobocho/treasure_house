// 캐노니컬 허프만 — SPEC §5.
//
// 트리를 만들지 않는다. 최적 길이 벡터는 하나가 아니어서(1,1,1,1 은 두
// 벌이 다 최적) 트리를 만들면 우선순위 큐의 동점 처리가 어느 쪽을
// 고를지 정하는데, 그 처리는 언어마다 다르다. package–merge 의 정렬 키
// (무게, 종류, 순번) 가 동점 처리 전부이고, 그 키 덕분에 결과가 빈도
// 벡터만의 함수가 된다.
import { Bytes, concat, fail } from './common';
import { MsbReader, MsbWriter } from './bitio';
import * as varint from './varint';

export const MAX_LENGTH = 15;
export const ALPHABET = 256;
export const TABLE_BYTES = ALPHABET / 2;

interface Coin {
  weight: number;
  // 0 = 기호 동전, 1 = 꾸러미. 무게가 같으면 기호 동전이 앞선다.
  kind: number;
  rank: number;
  syms: number[];
}

function coinLess(a: Coin, b: Coin): number {
  if (a.weight !== b.weight) return a.weight - b.weight;
  if (a.kind !== b.kind) return a.kind - b.kind;
  return a.rank - b.rank;
}

export function codeLengths(freqs: number[],
                            limit = MAX_LENGTH): number[] {
  const used: Array<[number, number]> = [];
  for (let s = 0; s < freqs.length; s++) {
    if (freqs[s] > 0) used.push([freqs[s], s]);
  }
  used.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
  const lengths = new Array<number>(freqs.length).fill(0);
  const m = used.length;
  if (m === 0) return lengths;
  if (m === 1) {
    lengths[used[0][1]] = 1;
    return lengths;
  }
  if (limit < 31 && m > 2 ** limit) {
    fail(`기호 ${m}개는 길이 ${limit} 로 못 담는다`);
  }
  const coins: Coin[] = used.map(([f, s], j) => ({
    weight: f,
    kind: 0,
    rank: j,
    syms: [s],
  }));
  let level = coins.slice();
  for (let round = 0; round < limit - 1; round++) {
    const packed: Coin[] = [];
    for (let i = 0; i + 1 < level.length; i += 2) {
      packed.push({
        weight: level[i].weight + level[i + 1].weight,
        kind: 1,
        rank: packed.length,
        syms: level[i].syms.concat(level[i + 1].syms),
      });
    }
    level = packed.concat(coins);
    level.sort(coinLess);
  }
  const take = Math.min(2 * m - 2, level.length);
  for (let i = 0; i < take; i++) {
    for (const s of level[i].syms) lengths[s] += 1;
  }
  return lengths;
}

export function canonicalCodes(lengths: number[]): number[] {
  const blCount = new Array<number>(MAX_LENGTH + 1).fill(0);
  for (const l of lengths) {
    if (l > 0) {
      if (l > MAX_LENGTH) fail(`부호 길이 ${l} 는 상한을 넘는다`);
      blCount[l] += 1;
    }
  }
  const nextCode = new Array<number>(MAX_LENGTH + 2).fill(0);
  let code = 0;
  for (let bits = 1; bits <= MAX_LENGTH; bits++) {
    code = (code + blCount[bits - 1]) * 2;
    nextCode[bits] = code;
  }
  const codes = new Array<number>(lengths.length).fill(0);
  for (let s = 0; s < lengths.length; s++) {
    const l = lengths[s];
    if (l === 0) continue;
    if (nextCode[l] >= 2 ** l) fail(`부호표가 넘친다 — 길이 ${l}`);
    codes[s] = nextCode[l]++;
  }
  return codes;
}

// 크래프트 합이 1 인지. 예외는 **기호 하나짜리 표** — 길이 1 하나라 늘
// 합이 1/2 이고, zeros_64k 처럼 한 바이트만 있는 파일에서 반드시
// 나온다.
export function checkComplete(lengths: number[]): void {
  let total = 0;
  let used = 0;
  let only = 0;
  for (const l of lengths) {
    if (l > 0) {
      total += 2 ** (MAX_LENGTH - l);
      used++;
      only = l;
    }
  }
  const full = 2 ** MAX_LENGTH;
  if (total > full) fail('부호표가 넘친다 (크래프트 합 > 1)');
  if (total < full && !(used === 1 && only === 1)) {
    fail('부호표가 모자란다 (크래프트 합 < 1)');
  }
}

export interface BitSource {
  readBit(): number;
}

// 캐노니컬 복호기 — 트리를 안 만든다. 길이별 첫 부호와 첫 자리만 있으면
// 비트를 하나씩 받아 가며 판정할 수 있다.
export class Decoder {
  private symbols: number[] = [];
  private count = new Array<number>(MAX_LENGTH + 1).fill(0);
  private firstCode = new Array<number>(MAX_LENGTH + 2).fill(0);
  private firstIndex = new Array<number>(MAX_LENGTH + 2).fill(0);

  constructor(lengths: number[]) {
    const pairs: Array<[number, number]> = [];
    for (let s = 0; s < lengths.length; s++) {
      if (lengths[s] > 0) pairs.push([lengths[s], s]);
    }
    pairs.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
    for (const [l, s] of pairs) {
      this.symbols.push(s);
      this.count[l] += 1;
    }
    let code = 0;
    let index = 0;
    for (let l = 1; l <= MAX_LENGTH; l++) {
      code = (code + this.count[l - 1]) * 2;
      this.firstCode[l] = code;
      this.firstIndex[l] = index;
      index += this.count[l];
    }
  }

  read(r: BitSource): number {
    let code = 0;
    for (let l = 1; l <= MAX_LENGTH; l++) {
      code = code * 2 + r.readBit();
      const off = code - this.firstCode[l];
      if (this.count[l] > 0 && off < this.count[l]) {
        return this.symbols[this.firstIndex[l] + off];
      }
    }
    return fail('부호표에 없는 비트열');
  }
}

export function nibble(table: Bytes, sym: number): number {
  const b = table[sym >> 1];
  return (sym & 1) === 1 ? b & 0x0f : b >> 4;
}

export function packTable(lengths: number[]): Bytes {
  const table = new Uint8Array(TABLE_BYTES);
  for (let s = 0; s < ALPHABET; s++) {
    const v = lengths[s] & 0x0f;
    if ((s & 1) === 1) table[s >> 1] |= v;
    else table[s >> 1] |= v << 4;
  }
  return table;
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  const freqs = new Array<number>(ALPHABET).fill(0);
  for (const b of src) freqs[b] += 1;
  const lengths = codeLengths(freqs);
  const codes = canonicalCodes(lengths);
  const w = new MsbWriter();
  for (const b of src) w.writeBits(codes[b], lengths[b]);
  w.flush();
  return concat(
    [varint.put(src.length), packTable(lengths), w.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  if (src.length < pos + TABLE_BYTES) fail('부호 길이 표가 잘렸다');
  const table = src.subarray(pos, pos + TABLE_BYTES);
  const lengths = new Array<number>(ALPHABET);
  for (let s = 0; s < ALPHABET; s++) lengths[s] = nibble(table, s);
  checkComplete(lengths);
  const dec = new Decoder(lengths);
  const r = new MsbReader(src, pos + TABLE_BYTES);
  const out = new Uint8Array(n);
  for (let i = 0; i < n; i++) out[i] = dec.read(r);
  return out;
}
