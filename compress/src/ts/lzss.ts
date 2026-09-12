// LZ77 계열 — SPEC §6.
//
// 사슬 배열을 **절대 위치로** 잡는다. zlib 은 창 크기 배열에 감아
// 넣어서 pos-32768 자리를 pos 가 덮어쓰고, 그래서 실효 최대 거리가
// 32506 이다. 후보 교체 비교는 > 다. >= 로 쓰면 같은 길이에서 먼 쪽을
// 골라, 정상 복호되는 **다른** 파일이 나온다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export const WINDOW = 32768;
export const MIN_MATCH = 3;
export const MAX_MATCH = 258;
export const HASH_BITS = 15;
export const HASH_SIZE = 1 << HASH_BITS;
export const CHAIN_LIMIT = 32;
const NIL = -1;

export interface Token {
  isMatch: boolean;
  literal: number;
  length: number;
  dist: number;
}

export function hash3(s: Bytes, i: number): number {
  return ((s[i] << 10) ^ (s[i + 1] << 5) ^ s[i + 2]) & (HASH_SIZE - 1);
}

export function findTokens(src: Bytes): Token[] {
  const n = src.length;
  const head = new Int32Array(HASH_SIZE).fill(NIL);
  const prev = new Int32Array(Math.max(n, 1)).fill(NIL);
  const tokens: Token[] = [];
  let i = 0;
  while (i < n) {
    let bestLen = 0;
    let bestDist = 0;
    if (i + MIN_MATCH <= n) {
      const limit = Math.min(MAX_MATCH, n - i);
      let cand = head[hash3(src, i)];
      let probes = 0;
      while (cand !== NIL && probes < CHAIN_LIMIT) {
        const dist = i - cand;
        if (dist > WINDOW) break;
        let ln = 0;
        while (ln < limit && src[cand + ln] === src[i + ln]) ln++;
        if (ln > bestLen) {
          bestLen = ln;
          bestDist = dist;
          if (ln === limit) break;
        }
        cand = prev[cand];
        probes++;
      }
    }
    if (bestLen >= MIN_MATCH) {
      for (let k = 0; k < bestLen; k++) {
        const p = i + k;
        if (p + MIN_MATCH <= n) {
          const h = hash3(src, p);
          prev[p] = head[h];
          head[h] = p;
        }
      }
      tokens.push(
        { isMatch: true, literal: 0, length: bestLen, dist: bestDist });
      i += bestLen;
    } else {
      if (i + MIN_MATCH <= n) {
        const h = hash3(src, i);
        prev[i] = head[h];
        head[h] = i;
      }
      tokens.push(
        { isMatch: false, literal: src[i], length: 0, dist: 0 });
      i++;
    }
  }
  return tokens;
}

export function encode(src: Bytes): Bytes {
  const tokens = findTokens(src);
  const out = new ByteBuf();
  for (let base = 0; base < tokens.length; base += 8) {
    const end = Math.min(base + 8, tokens.length);
    let flag = 0;
    for (let k = base; k < end; k++) {
      if (tokens[k].isMatch) flag |= 1 << (7 - (k - base));
    }
    out.push(flag);
    for (let k = base; k < end; k++) {
      const t = tokens[k];
      if (t.isMatch) {
        const d = t.dist - 1;
        out.push(t.length - MIN_MATCH);
        out.push(d & 0xff);
        out.push(d >> 8);
      } else {
        out.push(t.literal);
      }
    }
  }
  return concat([varint.put(src.length), out.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, start] = varint.getLength(src, 0);
  let pos = start;
  const end = src.length;
  const out = new ByteBuf();
  while (out.size < n) {
    if (pos >= end) fail('플래그 바이트가 없다');
    const flag = src[pos++];
    for (let k = 0; k < 8 && out.size < n; k++) {
      if (flag & (1 << (7 - k))) {
        if (pos + 3 > end) fail('일치 토큰이 잘렸다');
        const ln = src[pos] + MIN_MATCH;
        const dist = (src[pos + 1] | (src[pos + 2] << 8)) + 1;
        pos += 3;
        if (dist > out.size) fail(`거리 ${dist} 가 낸 것보다 멀다`);
        const at = out.size - dist;
        // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다 —
        // 한 번에 복사하면 틀린다.
        for (let j = 0; j < ln; j++) out.push(out.at(at + j));
      } else {
        if (pos >= end) fail('리터럴이 잘렸다');
        out.push(src[pos++]);
      }
    }
  }
  if (out.size !== n) fail('푼 길이가 헤더와 다르다');
  if (pos !== end) fail('뒤에 남은 바이트가 있다');
  return out.bytes();
}
