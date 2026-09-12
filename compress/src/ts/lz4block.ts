// LZ4 — SPEC §14.
//
// LZ77 인데 **엔트로피 부호가 아예 없다.** 리터럴과 일치를 바이트로
// 그냥 적는다. DEFLATE 보다 덜 줄고 몇 배 빨리 풀린다.
//
// 꼬리 규칙 둘: 마지막 5바이트는 반드시 리터럴, 일치는 끝에서 12바이트
// 안쪽에서 시작 금지. 지키지 않으면 진짜 lz4 가 거절한다.
import { ByteBuf, Bytes, concat, fail } from './common';
import * as varint from './varint';

export const MIN_MATCH = 4;
export const LAST_LITERALS = 5;
export const MF_LIMIT = 12;
export const HASH_LOG = 12;
export const HASH_SIZE = 1 << HASH_LOG;
export const HASH_MUL = 2654435761;
export const MAX_OFFSET = 65535;

export function putLsic(out: ByteBuf, v: number): void {
  let left = v;
  while (left >= 255) {
    out.push(255);
    left -= 255;
  }
  out.push(left);
}

// 고리를 묶는 것은 입력 자신이다 — 이어짐 바이트가 남은 것보다 많을 수
// 없다. 고정 상한은 솔깃하고 틀린다 (SPEC §14.3).
export function getLsic(src: Bytes, pos: number): [number, number] {
  let total = 0;
  let at = pos;
  while (at < src.length) {
    const b = src[at++];
    total += b;
    if (b !== 255) {
      if (total > varint.MAX_LENGTH) fail('LSIC 값이 너무 크다');
      return [total, at];
    }
  }
  return fail('LSIC 가 잘렸다');
}

function hash4(s: Bytes, i: number): number {
  const v = (s[i] | (s[i + 1] << 8) | (s[i + 2] << 16) |
             (s[i + 3] << 24)) >>> 0;
  // **Math.imul 이어야 한다.** v * HASH_MUL 은 최대 1.1e19 로 2^53 을
  // 훌쩍 넘어 배정도가 정밀도를 잃는다. 한국어 UTF-8 처럼 맨 위 비트가
  // 켜진 바이트가 많은 입력에서만 해시가 어긋나 파서티가 깨졌다.
  // imul 은 32비트 곱의 아래 32비트를 정확히 준다 (SPEC §0.5).
  return Math.imul(v, HASH_MUL) >>> (32 - HASH_LOG);
}

function same4(s: Bytes, a: number, b: number): boolean {
  return s[a] === s[b] && s[a + 1] === s[b + 1] &&
         s[a + 2] === s[b + 2] && s[a + 3] === s[b + 3];
}

// 시퀀스 하나. hasMatch 가 거짓이면 마지막(리터럴만) 시퀀스다.
function emit(out: ByteBuf, src: Bytes, from: number, to: number,
              hasMatch: boolean, offset: number, length: number): void {
  const litLen = to - from;
  const tokenLit = Math.min(litLen, 15);
  if (!hasMatch) {
    out.push(tokenLit << 4);
    if (litLen >= 15) putLsic(out, litLen - 15);
    out.extend(src, from, to);
    return;
  }
  const mlCode = length - MIN_MATCH;
  const tokenMl = Math.min(mlCode, 15);
  out.push((tokenLit << 4) | tokenMl);
  if (litLen >= 15) putLsic(out, litLen - 15);
  out.extend(src, from, to);
  out.push(offset & 0xff);
  out.push(offset >> 8);
  if (mlCode >= 15) putLsic(out, mlCode - 15);
}

export function compressBlock(src: Bytes): Bytes {
  const n = src.length;
  const out = new ByteBuf();
  if (n < MF_LIMIT + 1) {
    emit(out, src, 0, n, false, 0, 0);
    return out.bytes();
  }
  const table = new Int32Array(HASH_SIZE).fill(-1);
  let ip = 0;
  let anchor = 0;
  while (ip <= n - MF_LIMIT) {
    const h = hash4(src, ip);
    const ref = table[h];
    table[h] = ip;
    if (ref >= 0 && ip - ref <= MAX_OFFSET && same4(src, ref, ip)) {
      let ml = MIN_MATCH;
      const limit = n - LAST_LITERALS;
      while (ip + ml < limit && src[ref + ml] === src[ip + ml]) ml++;
      emit(out, src, anchor, ip, true, ip - ref, ml);
      ip += ml;
      anchor = ip;
    } else {
      ip++;
    }
  }
  emit(out, src, anchor, n, false, 0, 0);
  return out.bytes();
}

export function decompressBlock(block: Bytes, check: boolean,
                                want: number): Bytes {
  const out = new ByteBuf();
  let pos = 0;
  const n = block.length;
  while (pos < n) {
    const token = block[pos++];
    let litLen = token >> 4;
    if (litLen === 15) {
      const [extra, next] = getLsic(block, pos);
      litLen += extra;
      pos = next;
    }
    if (pos + litLen > n) fail('리터럴이 잘렸다');
    out.extend(block, pos, pos + litLen);
    pos += litLen;
    if (pos === n) break;          // 마지막 시퀀스는 리터럴뿐이다
    if (pos + 2 > n) fail('거리가 잘렸다');
    const offset = block[pos] | (block[pos + 1] << 8);
    pos += 2;
    let length = token & 15;
    if (length === 15) {
      const [extra, next] = getLsic(block, pos);
      length += extra;
      pos = next;
    }
    length += MIN_MATCH;
    if (offset === 0) fail('거리 0 은 없다');
    if (offset > out.size) fail(`거리 ${offset} 가 낸 것보다 멀다`);
    const start = out.size - offset;
    // 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
    for (let j = 0; j < length; j++) out.push(out.at(start + j));
  }
  if (check && out.size !== want) fail('푼 길이가 헤더와 다르다');
  return out.bytes();
}

export function encode(src: Bytes): Bytes {
  if (src.length === 0) return varint.put(0);
  return concat([varint.put(src.length), compressBlock(src)]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  if (n === 0) {
    if (pos !== src.length) fail('빈 입력인데 뒤에 바이트가 있다');
    return new Uint8Array(0);
  }
  return decompressBlock(src.subarray(pos), true, n);
}

// 진짜 lz4 명령이 쓰는 프레임을 푼다 (§14.6). 쓰지는 않는다.
// 내용 검사합(xxHash)은 건너뛴다 — 이유는 명세에 적어 뒀다.
export function frameDecode(src: Bytes): Bytes {
  if (src.length < 7 || src[0] !== 0x04 || src[1] !== 0x22 ||
      src[2] !== 0x4d || src[3] !== 0x18) {
    fail('lz4 프레임 매직이 아니다');
  }
  const flg = src[4];
  if (flg >> 6 !== 1) fail(`모르는 프레임 판: ${flg >> 6}`);
  const blockChecksum = (flg & 0x10) !== 0;
  const contentSize = (flg & 0x08) !== 0;
  const contentChecksum = (flg & 0x04) !== 0;
  const dictId = (flg & 0x01) !== 0;
  let pos = 6;
  if (contentSize) pos += 8;
  if (dictId) pos += 4;
  pos += 1;                        // 머리 검사 바이트(HC)
  const parts: Bytes[] = [];
  for (;;) {
    if (pos + 4 > src.length) fail('블록 크기가 잘렸다');
    let size = (src[pos] + src[pos + 1] * 256 + src[pos + 2] * 65536 +
                src[pos + 3] * 16777216);
    pos += 4;
    if (size === 0) break;
    const stored = size >= 0x80000000;
    if (stored) size -= 0x80000000;
    if (pos + size > src.length) fail('블록이 잘렸다');
    const chunk = src.subarray(pos, pos + size);
    pos += size;
    if (blockChecksum) pos += 4;
    parts.push(stored ? chunk : decompressBlock(chunk, false, 0));
  }
  if (contentChecksum) pos += 4;
  return concat(parts);
}
