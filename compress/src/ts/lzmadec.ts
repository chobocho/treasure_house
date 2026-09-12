// LZMA1 복호기 — SPEC §16.
//
// §8 의 레인지 코더를 LZMA 것으로 쓴 이유가 이 파일이다. 같은 코더에
// LZMA 의 문맥 모델만 얹으면 진짜 xz 가 만든 파일이 풀린다.
//
// 읽는 것은 LZMA1 "alone" 형식이다. .xz 컨테이너는 다른 틀이고 12부에서
// 말로만 다룬다 — "LZMA 를 푼다" 와 ".xz 를 푼다" 는 다른 주장이다.
import { ByteBuf, Bytes, fail } from './common';
import { Decoder, PROB_INIT } from './rangecoder';

export const NUM_STATES = 12;
export const NUM_POS_BITS_MAX = 4;
export const NUM_LEN_TO_POS_STATES = 4;
export const NUM_ALIGN_BITS = 4;
export const END_POS_MODEL_INDEX = 14;
export const NUM_FULL_DISTANCES = 1 << (END_POS_MODEL_INDEX >> 1);
export const MATCH_MIN_LEN = 2;
export const UNKNOWN_SIZE = 2 ** 64 - 1;
export const END_MARKER = 0xffffffff;
export const MAX_OUTPUT = 2 ** 32;

function probs(n: number): Uint16Array {
  return new Uint16Array(n).fill(PROB_INIT);
}

// 위에서부터 내려가는 이진 트리. 결과는 numBits 짜리 값.
function bitTree(dec: Decoder, p: Uint16Array, offset: number,
                 numBits: number): number {
  let m = 1;
  for (let i = 0; i < numBits; i++) {
    m = m * 2 + dec.decodeBit(p, offset + m);
  }
  return m - 2 ** numBits;
}

// 같은 트리인데 비트를 **거꾸로** 모은다 — 거리의 아래 비트가 이렇다.
function bitTreeReverse(dec: Decoder, p: Uint16Array, offset: number,
                        numBits: number): number {
  let m = 1;
  let sym = 0;
  for (let i = 0; i < numBits; i++) {
    const bit = dec.decodeBit(p, offset + m);
    m = m * 2 + bit;
    sym |= bit << i;
  }
  return sym >>> 0;
}

// 길이 복호기. 2..273 을 세 구간(8+8+256)으로 나눠 적는다.
class LengthCoder {
  choice = probs(2);
  low: Uint16Array;
  mid: Uint16Array;
  high = probs(256);

  constructor(posStates: number) {
    this.low = probs(posStates * 8);
    this.mid = probs(posStates * 8);
  }

  decode(dec: Decoder, posState: number): number {
    if (dec.decodeBit(this.choice, 0) === 0) {
      return bitTree(dec, this.low, posState * 8, 3);
    }
    if (dec.decodeBit(this.choice, 1) === 0) {
      return 8 + bitTree(dec, this.mid, posState * 8, 3);
    }
    return 16 + bitTree(dec, this.high, 0, 8);
  }
}

export interface Header {
  lc: number;
  lp: number;
  pb: number;
  dictSize: number;
  size: number;
  pos: number;
}

export function parseHeader(src: Bytes): Header {
  if (src.length < 13) fail('LZMA 머리가 너무 짧다');
  const prop = src[0];
  if (prop >= 9 * 5 * 5) fail(`속성 바이트가 범위를 넘는다: ${prop}`);
  const lc = prop % 9;
  const rest = Math.floor(prop / 9);
  const lp = rest % 5;
  const pb = Math.floor(rest / 5);
  let dictSize = 0;
  for (let i = 0; i < 4; i++) dictSize += src[1 + i] * 2 ** (8 * i);
  let size = 0;
  for (let i = 0; i < 8; i++) size += src[5 + i] * 2 ** (8 * i);
  if (size !== UNKNOWN_SIZE && size > MAX_OUTPUT) {
    fail('원본 길이가 너무 크다');
  }
  return { lc, lp, pb, dictSize, size, pos: 13 };
}

export function decode(src: Bytes): Bytes {
  const h = parseHeader(src);
  const dec = new Decoder(src, h.pos);
  const posStates = 1 << h.pb;
  const posMask = posStates - 1;
  const lpMask = (1 << h.lp) - 1;

  const isMatch = probs(NUM_STATES << NUM_POS_BITS_MAX);
  const isRep = probs(NUM_STATES);
  const isRepG0 = probs(NUM_STATES);
  const isRepG1 = probs(NUM_STATES);
  const isRepG2 = probs(NUM_STATES);
  const isRep0Long = probs(NUM_STATES << NUM_POS_BITS_MAX);
  const posSlot = probs(NUM_LEN_TO_POS_STATES * 64);
  const specPos = probs(NUM_FULL_DISTANCES - END_POS_MODEL_INDEX + 1);
  const alignProbs = probs(1 << NUM_ALIGN_BITS);
  const literal = probs(0x300 * 2 ** (h.lc + h.lp));
  const lenCoder = new LengthCoder(posStates);
  const repLenCoder = new LengthCoder(posStates);

  const out = new ByteBuf();
  let state = 0;
  let rep0 = 0;
  let rep1 = 0;
  let rep2 = 0;
  let rep3 = 0;

  while (h.size === UNKNOWN_SIZE || out.size < h.size) {
    const posState = out.size & posMask;
    const midx = (state << NUM_POS_BITS_MAX) + posState;
    let length: number;
    if (dec.decodeBit(isMatch, midx) === 0) {
      const prev = out.size > 0 ? out.at(out.size - 1) : 0;
      const litState = ((out.size & lpMask) << h.lc)
        + (prev >> (8 - h.lc));
      const base = 0x300 * litState;
      let symbol = 1;
      if (state >= 7) {
        // 일치 뒤의 리터럴 — 앞 일치의 같은 자리 바이트에 견준다
        if (rep0 + 1 > out.size) fail('거리가 지금까지 낸 것보다 멀다');
        let matchByte = out.at(out.size - rep0 - 1);
        while (symbol < 0x100) {
          const matchBit = (matchByte >> 7) & 1;
          matchByte = (matchByte << 1) & 0xff;
          const bit = dec.decodeBit(
            literal, base + ((1 + matchBit) << 8) + symbol);
          symbol = (symbol << 1) | bit;
          if (matchBit !== bit) break;
        }
      }
      while (symbol < 0x100) {
        symbol = (symbol << 1) | dec.decodeBit(literal, base + symbol);
      }
      out.push(symbol & 0xff);
      state = state < 4 ? 0 : (state < 10 ? state - 3 : state - 6);
      continue;
    }

    if (dec.decodeBit(isRep, state) !== 0) {
      // 지난 거리 넷 가운데 하나를 다시 쓴다 (§16.4)
      if (out.size === 0) fail('첫 기호가 되풀이 일치다');
      if (dec.decodeBit(isRepG0, state) === 0) {
        if (dec.decodeBit(isRep0Long, midx) === 0) {
          state = state < 7 ? 9 : 11;
          if (rep0 + 1 > out.size) fail('거리가 낸 것보다 멀다');
          out.push(out.at(out.size - rep0 - 1));
          continue;
        }
      } else {
        let dist: number;
        if (dec.decodeBit(isRepG1, state) === 0) {
          dist = rep1;
        } else {
          if (dec.decodeBit(isRepG2, state) === 0) {
            dist = rep2;
          } else {
            dist = rep3;
            rep3 = rep2;
          }
          rep2 = rep1;
        }
        rep1 = rep0;
        rep0 = dist;
      }
      length = repLenCoder.decode(dec, posState) + MATCH_MIN_LEN;
      state = state < 7 ? 8 : 11;
    } else {
      rep3 = rep2;
      rep2 = rep1;
      rep1 = rep0;
      length = lenCoder.decode(dec, posState) + MATCH_MIN_LEN;
      state = state < 7 ? 7 : 10;
      const slotState = Math.min(length - MATCH_MIN_LEN,
                                 NUM_LEN_TO_POS_STATES - 1);
      const slot = bitTree(dec, posSlot, slotState * 64, 6);
      if (slot < 4) {
        rep0 = slot;
      } else {
        const direct = (slot >> 1) - 1;
        rep0 = (2 | (slot & 1)) * 2 ** direct;
        if (slot < END_POS_MODEL_INDEX) {
          rep0 += bitTreeReverse(dec, specPos, rep0 - slot, direct);
        } else {
          rep0 += dec.decodeDirectBits(direct - NUM_ALIGN_BITS) *
                  2 ** NUM_ALIGN_BITS;
          rep0 += bitTreeReverse(dec, alignProbs, 0, NUM_ALIGN_BITS);
        }
        if (rep0 === END_MARKER) break;
      }
    }

    // 거리 검사는 한 곳에서만 한다 — 새 일치든 되풀이 일치든 같다.
    if (rep0 >= out.size) fail('거리가 지금까지 낸 것보다 멀다');
    const start = out.size - rep0 - 1;
    // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
    for (let j = 0; j < length; j++) out.push(out.at(start + j));
    if (out.size > MAX_OUTPUT) fail('푼 길이가 상한을 넘는다');
  }

  if (h.size !== UNKNOWN_SIZE && out.size !== h.size) {
    fail(`푼 길이가 머리와 다르다: ${out.size} != ${h.size}`);
  }
  return out.bytes();
}
