// 버로우즈–휠러 변환 — SPEC §9.
//
// 배가 늘리기 정렬. 키를 rank[i]*(m+1) + rank[i+k] 로 눌러 담는데, **첫
// 회의 rank 를 바이트 값 그대로 쓰면 안 된다** — 곱수 m+1 이 255 보다
// 작아져 자리가 겹친다. 0..(서로 다른 값 수-1) 로 먼저 압축한다. 같은
// 회전이 여럿이면 순서는 시작 위치 오름차순 — 안정 정렬이 필요하고,
// ECMAScript 2019 부터 Array.prototype.sort 는 안정으로 보장된다.
//
// 키가 최대 (m+1)^2 = 2^32 쯤이라 배정도로 정확하다. Int32Array 에
// 담으면 넘친다 — Float64Array 를 쓰는 이유다.
import { Bytes, concat, fail } from './common';
import * as varint from './varint';

export const BLOCK = 1 << 16;
export const ALPHABET = 256;

export function transformBlock(block: Bytes): [Bytes, number] {
  const m = block.length;
  if (m === 0) return [new Uint8Array(0), 0];
  const order = new Int32Array(ALPHABET).fill(-1);
  for (const c of block) order[c] = 1;
  let next = 0;
  for (let i = 0; i < ALPHABET; i++) {
    if (order[i] > 0) order[i] = next++;
  }
  let rank = new Float64Array(m);
  for (let i = 0; i < m; i++) rank[i] = order[block[i]];
  let sa = Array.from({ length: m }, (_v, i) => i);
  const keys = new Float64Array(m);
  const newRank = new Float64Array(m);
  const mul = m + 1;
  for (let k = 1; ; k *= 2) {
    for (let i = 0; i < m; i++) {
      keys[i] = rank[i] * mul + rank[(i + k) % m];
    }
    sa.sort((a, b) => keys[a] - keys[b]);
    let r = 0;
    newRank[sa[0]] = 0;
    for (let j = 1; j < m; j++) {
      if (keys[sa[j]] !== keys[sa[j - 1]]) r++;
      newRank[sa[j]] = r;
    }
    rank = Float64Array.from(newRank);
    if (r === m - 1 || k >= m) break;
  }
  const l = new Uint8Array(m);
  let primary = 0;
  for (let j = 0; j < m; j++) {
    const i = sa[j];
    l[j] = block[(i + m - 1) % m];
    if (i === 0) primary = j;
  }
  return [l, primary];
}

export function inverseBlock(l: Bytes, primary: number): Bytes {
  const m = l.length;
  if (m === 0) return new Uint8Array(0);
  if (primary < 0 || primary >= m) {
    fail(`primary 가 범위 밖이다: ${primary}`);
  }
  const count = new Int32Array(ALPHABET);
  const first = new Int32Array(ALPHABET);
  const occ = new Int32Array(ALPHABET);
  for (const c of l) count[c] += 1;
  let total = 0;
  for (let c = 0; c < ALPHABET; c++) {
    first[c] = total;
    total += count[c];
  }
  // nxt 는 LF 의 역치환이다. LF 로 걸으면 원문이 거꾸로 나오고,
  // nxt 로 걸으면 바로 나온다.
  const nxt = new Int32Array(m);
  for (let i = 0; i < m; i++) {
    const c = l[i];
    nxt[first[c] + occ[c]] = i;
    occ[c] += 1;
  }
  const out = new Uint8Array(m);
  let i = primary;
  for (let step = 0; step < m; step++) {
    i = nxt[i];
    out[step] = l[i];
  }
  return out;
}

export function encode(src: Bytes): Bytes {
  const parts: Bytes[] = [varint.put(src.length)];
  for (let off = 0; off < src.length; off += BLOCK) {
    const end = Math.min(off + BLOCK, src.length);
    const [l, primary] = transformBlock(src.subarray(off, end));
    parts.push(
      Uint8Array.of(
        primary & 0xff,
        (primary >> 8) & 0xff,
        (primary >> 16) & 0xff,
        (primary >>> 24) & 0xff,
      ),
    );
    parts.push(l);
  }
  return concat(parts);
}

export function decode(src: Bytes): Bytes {
  const [n, start] = varint.getLength(src, 0);
  let pos = start;
  const parts: Bytes[] = [];
  let left = n;
  while (left > 0) {
    const m = Math.min(BLOCK, left);
    if (pos + 4 + m > src.length) fail('블록이 잘렸다');
    const primary =
      src[pos] + src[pos + 1] * 256 + src[pos + 2] * 65536 +
      src[pos + 3] * 16777216;
    pos += 4;
    parts.push(inverseBlock(src.subarray(pos, pos + m), primary));
    pos += m;
    left -= m;
  }
  if (pos !== src.length) fail('뒤에 남은 바이트가 있다');
  return concat(parts);
}
