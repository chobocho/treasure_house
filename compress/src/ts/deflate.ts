// DEFLATE 부호기 — SPEC §10.
//
// RFC 가 부호기에 맡긴 선택을 전부 못 박은 것이 이 파일이다. 블록
// 65535, 값을 정확히 세어 가장 작은 것, 같으면 stored → fixed →
// dynamic. 값을 어림하면 언어마다 반올림이 달라져 블록 종류가 갈린다.
import { Bytes } from './common';
import { LsbWriter } from './bitio';
import { canonicalCodes, codeLengths, MAX_LENGTH } from './huffman';
import { inflateRaw } from './inflate';
import * as T from './deflateTables';

export const BLOCK_SIZE = 65535;
export const HASH_BITS = 15;
export const HASH_SIZE = 1 << HASH_BITS;
export const CHAIN_LIMIT = 128;
const NIL = -1;

export interface Token {
  isMatch: boolean;
  literal: number;
  length: number;
  dist: number;
}

interface ClItem {
  sym: number;
  value: number;
  nbits: number;
}

function hash3(s: Bytes, i: number): number {
  return ((s[i] << 10) ^ (s[i + 1] << 5) ^ s[i + 2]) & (HASH_SIZE - 1);
}

export function parse(src: Bytes): Token[] {
  const n = src.length;
  const head = new Int32Array(HASH_SIZE).fill(NIL);
  const prev = new Int32Array(Math.max(n, 1)).fill(NIL);
  const tokens: Token[] = [];

  const insert = (p: number): void => {
    if (p + T.MIN_MATCH <= n) {
      const h = hash3(src, p);
      prev[p] = head[h];
      head[h] = p;
    }
  };
  const find = (p: number): [number, number] => {
    if (p + T.MIN_MATCH > n) return [0, 0];
    let bestLen = 0;
    let bestDist = 0;
    const limit = Math.min(T.MAX_MATCH, n - p);
    let cand = head[hash3(src, p)];
    let probes = 0;
    while (cand !== NIL && probes < CHAIN_LIMIT) {
      const dist = p - cand;
      if (dist > T.MAX_DIST) break;
      let ln = 0;
      while (ln < limit && src[cand + ln] === src[p + ln]) ln++;
      if (ln > bestLen) {
        bestLen = ln;
        bestDist = dist;
        if (ln === limit) break;
      }
      cand = prev[cand];
      probes++;
    }
    return [bestLen, bestDist];
  };

  let i = 0;
  while (i < n) {
    const [ln, dist] = find(i);
    insert(i);
    if (ln >= T.MIN_MATCH) {
      const nxtLen = i + 1 < n ? find(i + 1)[0] : 0;
      if (nxtLen > ln) {
        // 게으른 일치 — 한 칸 뒤에서 더 긴 것이 있으면 이번은 버린다
        tokens.push(
          { isMatch: false, literal: src[i], length: 0, dist: 0 });
        i++;
        continue;
      }
      for (let k = 1; k < ln; k++) insert(i + k);
      tokens.push({ isMatch: true, literal: 0, length: ln, dist });
      i += ln;
    } else {
      tokens.push(
        { isMatch: false, literal: src[i], length: 0, dist: 0 });
      i++;
    }
  }
  return tokens;
}

interface Block {
  tokA: number;
  tokB: number;
  inA: number;
  inB: number;
}

export function splitBlocks(tokens: Token[]): Block[] {
  const blocks: Block[] = [];
  let tokStart = 0;
  let inStart = 0;
  let cur = 0;
  for (let k = 0; k < tokens.length; k++) {
    cur += tokens[k].isMatch ? tokens[k].length : 1;
    if (cur >= BLOCK_SIZE) {
      blocks.push({ tokA: tokStart, tokB: k + 1, inA: inStart,
                    inB: inStart + cur });
      tokStart = k + 1;
      inStart += cur;
      cur = 0;
    }
  }
  if (cur > 0 || blocks.length === 0) {
    blocks.push({ tokA: tokStart, tokB: tokens.length, inA: inStart,
                  inB: inStart + cur });
  }
  return blocks;
}

function freqsOf(tokens: Token[], a: number, b: number):
    [number[], number[], number] {
  const lit = new Array<number>(T.LITLEN_SYMBOLS).fill(0);
  const dst = new Array<number>(T.DIST_SYMBOLS).fill(0);
  let extra = 0;
  for (let k = a; k < b; k++) {
    const t = tokens[k];
    if (t.isMatch) {
      const code = T.LENGTH_CODE[t.length];
      lit[code] += 1;
      extra += T.LENGTH_EXTRA[code - 257];
      const dc = T.distCode(t.dist);
      dst[dc] += 1;
      extra += T.DIST_EXTRA[dc];
    } else {
      lit[t.literal] += 1;
    }
  }
  lit[T.END_OF_BLOCK] += 1;
  return [lit, dst, extra];
}

function bodyBits(lit: number[], dst: number[], extra: number,
                  litLen: number[], dstLen: number[]): number {
  let bits = extra;
  for (let s = 0; s < lit.length; s++) {
    if (lit[s]) bits += lit[s] * litLen[s];
  }
  for (let s = 0; s < dst.length; s++) {
    if (dst[s]) bits += dst[s] * dstLen[s];
  }
  return bits;
}

// 부호 길이 배열 → (기호, 여분 값, 여분 비트). 왼쪽부터 탐욕.
export function clEncode(lengths: number[]): ClItem[] {
  const out: ClItem[] = [];
  let i = 0;
  const n = lengths.length;
  while (i < n) {
    const cur = lengths[i];
    let run = 1;
    while (i + run < n && lengths[i + run] === cur) run++;
    if (cur === 0) {
      while (run >= 3) {
        let k: number;
        if (run >= 11) {
          k = Math.min(run, 138);
          out.push({ sym: T.CL_ZERO_LONG, value: k - 11, nbits: 7 });
        } else {
          k = Math.min(run, 10);
          out.push({ sym: T.CL_ZERO_SHORT, value: k - 3, nbits: 3 });
        }
        run -= k;
        i += k;
      }
      for (let j = 0; j < run; j++) {
        out.push({ sym: 0, value: 0, nbits: 0 });
        i++;
      }
    } else {
      out.push({ sym: cur, value: 0, nbits: 0 });
      i++;
      run--;
      while (run >= 3) {
        const k = Math.min(run, 6);
        out.push({ sym: T.CL_REPEAT, value: k - 3, nbits: 2 });
        run -= k;
        i += k;
      }
      for (let j = 0; j < run; j++) {
        out.push({ sym: cur, value: 0, nbits: 0 });
        i++;
      }
    }
  }
  return out;
}

function lastUsed(lengths: number[]): number {
  for (let s = lengths.length; s > 0; s--) if (lengths[s - 1]) return s;
  return 0;
}

class DynamicPlan {
  litLen: number[];
  dstLen: number[];
  clLen: number[];
  items: ClItem[];
  hlit: number;
  hdist: number;
  hclen: number;
  bits: number;

  constructor(litFreq: number[], dstFreq: number[], extra: number) {
    this.litLen = codeLengths(litFreq, MAX_LENGTH);
    this.dstLen = codeLengths(dstFreq, MAX_LENGTH);
    if (!this.dstLen.some((l) => l > 0)) {
      // 일치가 하나도 없는 블록. 거리 부호를 안 보낼 수는 없으므로
      // 하나를 길이 1 로 보낸다 — 쓰이지 않는 부호다 (§10.5).
      this.dstLen[0] = 1;
    }
    this.hlit = Math.max(257, lastUsed(this.litLen));
    this.hdist = Math.max(1, lastUsed(this.dstLen));
    this.items = clEncode(
      this.litLen.slice(0, this.hlit)
        .concat(this.dstLen.slice(0, this.hdist)),
    );
    const clFreq = new Array<number>(T.CL_SYMBOLS).fill(0);
    for (const it of this.items) clFreq[it.sym] += 1;
    this.clLen = codeLengths(clFreq, T.CL_MAX_LENGTH);
    this.hclen = T.CL_SYMBOLS;
    while (this.hclen > 4 &&
           this.clLen[T.CL_ORDER[this.hclen - 1]] === 0) {
      this.hclen--;
    }
    let header = 5 + 5 + 4 + 3 * this.hclen;
    for (const it of this.items) {
      header += this.clLen[it.sym] + it.nbits;
    }
    this.bits = 3 + header +
      bodyBits(litFreq, dstFreq, extra, this.litLen, this.dstLen);
  }
}

function writeBody(w: LsbWriter, tokens: Token[], a: number, b: number,
                   litLen: number[], litCode: number[],
                   dstLen: number[], dstCode: number[]): void {
  for (let k = a; k < b; k++) {
    const t = tokens[k];
    if (t.isMatch) {
      const code = T.LENGTH_CODE[t.length];
      w.writeCode(litCode[code], litLen[code]);
      const idx = code - 257;
      if (T.LENGTH_EXTRA[idx]) {
        w.writeBits(t.length - T.LENGTH_BASE[idx], T.LENGTH_EXTRA[idx]);
      }
      const dc = T.distCode(t.dist);
      w.writeCode(dstCode[dc], dstLen[dc]);
      if (T.DIST_EXTRA[dc]) {
        w.writeBits(t.dist - T.DIST_BASE[dc], T.DIST_EXTRA[dc]);
      }
    } else {
      w.writeCode(litCode[t.literal], litLen[t.literal]);
    }
  }
  w.writeCode(litCode[T.END_OF_BLOCK], litLen[T.END_OF_BLOCK]);
}

export function deflateRaw(src: Bytes): Bytes {
  const w = new LsbWriter();
  if (src.length === 0) {
    // 마지막 고정 블록 하나, 안에는 블록 끝 기호뿐. 두 바이트 03 00.
    w.writeBits(1, 1);
    w.writeBits(1, 2);
    w.writeCode(0, 7);
    w.flush();
    return w.bytes();
  }
  const tokens = parse(src);
  const blocks = splitBlocks(tokens);
  const fixedCode = canonicalCodes(T.FIXED_LITLEN);
  const fixedDcode = canonicalCodes(T.FIXED_DIST);
  for (let k = 0; k < blocks.length; k++) {
    const blk = blocks[k];
    const final = k === blocks.length - 1 ? 1 : 0;
    const [litFreq, dstFreq, extra] =
      freqsOf(tokens, blk.tokA, blk.tokB);
    const rawLen = blk.inB - blk.inA;
    // stored 의 값은 지금 비트 자리에 달려 있다 — 정렬 때문이다.
    const pad = (8 - ((w.bitPos() + 3) % 8)) % 8;
    const costStored = 3 + pad + 32 + 8 * rawLen;
    const costFixed = 3 +
      bodyBits(litFreq, dstFreq, extra, T.FIXED_LITLEN, T.FIXED_DIST);
    const plan = new DynamicPlan(litFreq, dstFreq, extra);
    if (costStored <= costFixed && costStored <= plan.bits) {
      w.writeBits(final, 1);
      w.writeBits(0, 2);
      w.align();
      w.writeBits(rawLen, 16);
      w.writeBits(rawLen ^ 0xffff, 16);
      for (let j = blk.inA; j < blk.inB; j++) w.writeBits(src[j], 8);
      continue;
    }
    w.writeBits(final, 1);
    if (costFixed <= plan.bits) {
      w.writeBits(1, 2);
      writeBody(w, tokens, blk.tokA, blk.tokB, T.FIXED_LITLEN,
                fixedCode, T.FIXED_DIST, fixedDcode);
      continue;
    }
    w.writeBits(2, 2);
    w.writeBits(plan.hlit - 257, 5);
    w.writeBits(plan.hdist - 1, 5);
    w.writeBits(plan.hclen - 4, 4);
    for (let i = 0; i < plan.hclen; i++) {
      w.writeBits(plan.clLen[T.CL_ORDER[i]], 3);
    }
    const clCode = canonicalCodes(plan.clLen);
    for (const it of plan.items) {
      w.writeCode(clCode[it.sym], plan.clLen[it.sym]);
      if (it.nbits) w.writeBits(it.value, it.nbits);
    }
    writeBody(w, tokens, blk.tokA, blk.tokB, plan.litLen,
              canonicalCodes(plan.litLen), plan.dstLen,
              canonicalCodes(plan.dstLen));
  }
  w.flush();
  return w.bytes();
}

// 골든 코덱. 다른 모듈과 달리 varint 헤더가 없다 — 남의 형식이라 우리가
// 얹을 자리가 없고, 원본 길이는 스트림 자신이 알고 있다.
export function encode(src: Bytes): Bytes {
  return deflateRaw(src);
}

export function decode(src: Bytes): Bytes {
  return inflateRaw(src);
}
