// 정수 부호 — SPEC §2.
//
// varint 만 바이트 단위이고 감마·델타·라이스는 비트 스트림(MSB
// 먼저)에서 돈다. 단항은 **1 을 q개 쓰고 0 으로 닫는다** — 반대 약속도
// 문헌에 흔한데, 섞어 쓰면 작은 값은 그대로 왕복돼서 골든 벡터 전에는
// 안 보인다.
//
// zigzag 만 BigInt 다. 64비트 부호 있는 정수를 다루는데 TS 의 수로는
// 2^53 까지만 정확하고, 무엇보다 산술 시프트가 32비트에서 끊긴다.
import { Bytes, concat, fail } from './common';
import { MsbReader, MsbWriter } from './bitio';
import * as varint from './varint';

// 단항 상한 (SPEC §2.5). 손상된 파일이 무한 루프가 되지 않게 하되,
// k=0 인 라이스(= 순수 단항)가 쓸모 있을 만큼은 크게.
export const MAX_UNARY = 4096;

export function zigzag(n: bigint): bigint {
  return BigInt.asUintN(64, (n << 1n) ^ (n >> 63n));
}

export function unzigzag(u: bigint): bigint {
  return BigInt.asIntN(64, (u >> 1n) ^ -(u & 1n));
}

export function bitLength(v: number): number {
  let n = 0;
  let x = v;
  while (x >= 1) {
    n++;
    x = Math.floor(x / 2);
  }
  return n;
}

export function putGamma(w: MsbWriter, v: number): void {
  if (v < 1) fail(`gamma 는 1 이상만: ${v}`);
  const n = bitLength(v);
  w.writeBits(0, n - 1);
  w.writeBits(v, n);
}

export function getGamma(r: MsbReader): number {
  let n = 1;
  while (r.readBit() === 0) {
    if (++n > 64) fail('gamma 의 길이 부분이 64비트를 넘는다');
  }
  return 2 ** (n - 1) + r.readBits(n - 1);
}

export function putDelta(w: MsbWriter, v: number): void {
  if (v < 1) fail(`delta 는 1 이상만: ${v}`);
  const n = bitLength(v);
  putGamma(w, n);
  w.writeBits(v, n - 1);
}

export function getDelta(r: MsbReader): number {
  const n = getGamma(r);
  if (n > 64) fail('delta 의 길이 부분이 64비트를 넘는다');
  return 2 ** (n - 1) + r.readBits(n - 1);
}

export function putRice(w: MsbWriter, v: number, k: number): void {
  const q = Math.floor(v / 2 ** k);
  if (q > MAX_UNARY) fail(`rice 의 몫이 ${q} — k 를 잘못 골랐다`);
  for (let i = 0; i < q; i++) w.writeBit(1);
  w.writeBit(0);
  if (k > 0) w.writeBits(v % 2 ** k, k);
}

export function getRice(r: MsbReader, k: number): number {
  let q = 0;
  while (r.readBit() === 1) {
    if (++q > MAX_UNARY) fail(`rice 의 단항이 ${MAX_UNARY} 를 넘는다`);
  }
  return q * 2 ** k + (k > 0 ? r.readBits(k) : 0);
}

// 골든 코덱 (SPEC §2.6) — 바이트마다 gamma(b+1).
export function encode(src: Bytes): Bytes {
  const w = new MsbWriter();
  for (const b of src) putGamma(w, b + 1);
  w.flush();
  return concat([varint.put(src.length), w.bytes()]);
}

export function decode(src: Bytes): Bytes {
  const [n, pos] = varint.getLength(src, 0);
  const r = new MsbReader(src, pos);
  const out = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    const v = getGamma(r) - 1;
    if (v < 0 || v > 255) fail(`바이트 범위를 벗어난 값: ${v}`);
    out[i] = v;
  }
  return out;
}
