// 팩 (SPEC.md §13) — 객체 여럿을 한 파일에, 비슷한 것은 델타로.
//
// 느슨한 객체는 파일 하나에 객체 하나지만, 팩은 객체들을 이어 붙이고
// 비슷한 객체는 "바탕에서 여기를 복사, 여기에 이것을 끼움" 이라는
// 델타로 적는다. 색인(.idx)은 이름 → 팩 안 자리의 표다. 팩 끝
// 20바이트는 팩 전체의 SHA-1 이고, 그것이 곧 파일 이름이다.
//
// 가변 길이 수는 << 대신 곱셈으로 쌓는다 — JS 의 << 는 32비트에서
// 부호가 뒤집혀, 2 GiB 넘는 크기·자리를 잘못 읽는다.
import { crc32 } from 'node:zlib';
import { GitError } from './errors';
import * as objects from './objects';
import { sha1 } from './sha1';
import * as zlib from './zlib';

const TYPE_NAMES: Record<number, string> = { 1: 'commit', 2: 'tree',
  3: 'blob', 4: 'tag' };
const TYPE_CODES: Record<string, number> = { commit: 1, tree: 2,
  blob: 3, tag: 4 };
export const OFS_DELTA = 6;
export const REF_DELTA = 7;

// 팩 항목 하나를 되살린 것. packedType 은 팩에 적힌 형식(6·7 은
// 델타), type·body 는 되살린 객체, depth·base 는 델타 사슬.
export class PackEntry {
  end = 0;
  crc = 0;
  packedType = 0;
  delta: Buffer | null = null;
  baseOffset: number | null = null;
  base: string | null = null;
  type = '';
  body: Buffer | null = null;
  oid = '';
  depth = 0;

  constructor(readonly offset: number) {}
}

// 7비트씩 작은 쪽부터(델타 머리의 크기). → [값, 다음 자리].
function varintLe(data: Buffer, pos: number): [number, number] {
  let [val, scale] = [0, 1];
  for (;;) {
    const b = data[pos++];
    val += (b & 0x7f) * scale;
    scale *= 128;
    if (!(b & 0x80)) return [val, pos];
  }
}

// 항목 머리 → [형식, 크기, 다음 자리]. 첫 바이트의 낮은 4비트가
// 크기의 시작이고, 이어지는 바이트는 7비트씩 위로 붙는다.
function entryHeader(data: Buffer, pos: number):
  [number, number, number] {
  let b = data[pos++];
  const typ = (b >> 4) & 7;
  let [size, scale] = [b & 15, 16];
  while (b & 0x80) {
    b = data[pos++];
    size += (b & 0x7f) * scale;
    scale *= 128;
  }
  return [typ, size, pos];
}

// OFS_DELTA 의 거리 — 큰 쪽부터, 이어지는 바이트마다 +1.
function ofs(data: Buffer, pos: number): [number, number] {
  let b = data[pos++];
  let n = b & 0x7f;
  while (b & 0x80) {
    b = data[pos++];
    n = (n + 1) * 128 + (b & 0x7f);
  }
  return [n, pos];
}

// 델타를 바탕에 적용한다(SPEC.md §13.1). O(결과 길이).
export function applyDelta(base: Buffer, delta: Buffer): Buffer {
  let [size, pos] = varintLe(delta, 0);
  if (size !== base.length) {
    throw new GitError('fatal: mygit: delta base size mismatch');
  }
  let want: number;
  [want, pos] = varintLe(delta, pos);
  const out: Buffer[] = [];
  while (pos < delta.length) {
    const op = delta[pos++];
    if (op & 0x80) {                           // 복사
      let [off, n] = [0, 0];
      for (let k = 0; k < 4; k++) {
        if (op & (1 << k)) off += delta[pos++] * 256 ** k;
      }
      for (let k = 0; k < 3; k++) {
        if (op & (0x10 << k)) n += delta[pos++] * 256 ** k;
      }
      n ||= 0x10000;
      if (off + n > base.length) {
        throw new GitError('fatal: mygit: delta copy out of range');
      }
      out.push(base.subarray(off, off + n));
    } else if (op) {                           // 끼움
      out.push(delta.subarray(pos, pos + op));
      pos += op;
    } else {
      throw new GitError('fatal: mygit: delta opcode 0 is reserved');
    }
  }
  const body = Buffer.concat(out);
  if (body.length !== want) {
    throw new GitError('fatal: mygit: delta result size mismatch');
  }
  return body;
}

// 팩 바이트 → PackEntry 들, 자리 차례. external(이름) 은 팩 밖의
// REF_DELTA 바탕을 [형식, 몸] 으로 준다(없으면 오류).
//
// 앞에서부터 읽으며 zlib 스트림이 먹은 바이트 수로 다음 항목을 찾고,
// 델타는 바탕을 먼저 되살린 뒤 적용한다. O(팩 크기 + 되살린 크기).
export function readPack(data: Buffer,
  external?: (oid: string) => [string, Buffer]): PackEntry[] {
  if (data.length < 32 || data.toString('latin1', 0, 4) !== 'PACK') {
    throw new GitError('fatal: mygit: not a pack file');
  }
  if (!sha1(data.subarray(0, -20)).equals(data.subarray(-20))) {
    throw new GitError('fatal: mygit: pack checksum mismatch');
  }
  const ver = data.readUInt32BE(4);
  if (ver !== 2 && ver !== 3) {
    throw new GitError(`fatal: mygit: pack version ${ver}`);
  }
  const ents: PackEntry[] = [];
  let pos = 12;
  for (let k = data.readUInt32BE(8); k > 0; k--) {
    const e = new PackEntry(pos);
    let size: number;
    [e.packedType, size, pos] = entryHeader(data, pos);
    if (e.packedType === OFS_DELTA) {
      let n: number;
      [n, pos] = ofs(data, pos);
      e.baseOffset = e.offset - n;
    } else if (e.packedType === REF_DELTA) {
      e.base = data.toString('hex', pos, pos + 20);
      pos += 20;
    } else if (!(e.packedType in TYPE_NAMES)) {
      throw new GitError('fatal: mygit: bad pack entry type ' +
        e.packedType);
    }
    const [raw, used] = zlib.decompressPrefix(data, pos);
    if (raw.length !== size) {
      throw new GitError('fatal: mygit: pack entry size mismatch');
    }
    pos += used;
    e.end = pos;
    e.crc = crc32(data.subarray(e.offset, pos));
    if (e.packedType in TYPE_NAMES) {
      [e.type, e.body] = [TYPE_NAMES[e.packedType], raw];
    } else {
      e.delta = raw;
    }
    ents.push(e);
  }
  if (pos !== data.length - 20) {
    throw new GitError('fatal: mygit: pack has trailing garbage');
  }
  resolveDeltas(ents, external);
  return ents;
}

// 델타 사슬을 풀어 형식·몸·이름·깊이를 채운다. 바탕이 아직 안 풀린
// 델타는 다음 바퀴로 미룬다 — 한 바퀴에 하나도 못 풀면 멈춘다.
function resolveDeltas(ents: PackEntry[],
  external?: (oid: string) => [string, Buffer]): void {
  const byOff = new Map(ents.map((e) => [e.offset, e]));
  const byOid = new Map<string, PackEntry>();
  for (const e of ents) {
    if (e.body === null) continue;
    e.oid = objects.hashObject(e.type, e.body);
    byOid.set(e.oid, e);
  }
  let pending = ents.filter((e) => e.body === null);
  while (pending.length) {
    const left: PackEntry[] = [];
    for (const e of pending) {
      let b: PackEntry | undefined;
      if (e.baseOffset !== null) {
        b = byOff.get(e.baseOffset);
        if (b === undefined) {
          throw new GitError('fatal: mygit: bad OFS_DELTA base');
        }
      } else {
        b = byOid.get(e.base!);
        if (b === undefined && external !== undefined) {
          const [t, body] = external(e.base!);
          [e.type, e.body] = [t, applyDelta(body, e.delta!)];
          e.depth = 1;
          e.oid = objects.hashObject(e.type, e.body);
          byOid.set(e.oid, e);
          continue;
        }
      }
      if (b?.body == null) {
        left.push(e);
        continue;
      }
      [e.type, e.body] = [b.type, applyDelta(b.body, e.delta!)];
      [e.depth, e.base] = [b.depth + 1, b.oid];
      e.oid = objects.hashObject(e.type, e.body);
      byOid.set(e.oid, e);
    }
    if (left.length === pending.length) {
      throw new GitError('fatal: mygit: unresolved delta base');
    }
    pending = left;
  }
}

export interface Idx {
  entries: [oid: string, offset: number, crc: number][];
  packSum: Buffer;
}

// 색인 판 2 → { entries: [이름, 자리, crc], packSum: 20바이트 }.
export function readIdx(data: Buffer): Idx {
  if (!data.subarray(0, 8).equals(Buffer.from('ff744f6300000002',
    'hex'))) {
    throw new GitError('fatal: mygit: not a version 2 pack index');
  }
  if (!sha1(data.subarray(0, -20)).equals(data.subarray(-20))) {
    throw new GitError('fatal: mygit: pack index checksum mismatch');
  }
  const n = data.readUInt32BE(8 + 255 * 4);
  let p = 8 + 256 * 4;
  const oids = Array.from({ length: n },
    (_, k) => data.toString('hex', p + 20 * k, p + 20 * k + 20));
  p += 20 * n;
  const crcs = Array.from({ length: n },
    (_, k) => data.readUInt32BE(p + 4 * k));
  p += 4 * n;
  const offs = Array.from({ length: n }, (_, k) => {
    const v = data.readUInt32BE(p + 4 * k);
    if (!(v & 0x80000000)) return v;
    // 2 GiB 넘는 자리의 표 — 8바이트
    const big = p + 4 * n + 8 * (v & 0x7fffffff);
    return Number(data.readBigUInt64BE(big));
  });
  return { entries: oids.map((o, k) => [o, offs[k], crcs[k]]),
    packSum: data.subarray(-40, -20) };
}

const u32 = (v: number) => {
  const b = Buffer.alloc(4);
  b.writeUInt32BE(v);
  return b;
};

// PackEntry 들 → 색인 판 2 바이트(SPEC.md §13.2).
//
// 이름 차례로 정렬한 fanout·이름·CRC·자리, 팩 체크섬, 그 앞 전부의
// SHA-1. 같은 팩이면 git 의 .idx 와 바이트까지 같다.
export function writeIdx(entries: PackEntry[], packSum: Buffer):
  Buffer {
  const ents = [...entries].sort((a, b) =>
    a.oid < b.oid ? -1 : a.oid > b.oid ? 1 : 0);
  const fan = new Array<number>(256).fill(0);
  for (const e of ents) fan[parseInt(e.oid.slice(0, 2), 16)]++;
  for (let k = 1; k < 256; k++) fan[k] += fan[k - 1];
  const big = ents.filter((e) => e.offset >= 0x80000000)
    .map((e) => e.offset);
  const small = ents.map((e) => e.offset >= 0x80000000
    ? (0x80000000 | big.indexOf(e.offset)) >>> 0 : e.offset);
  const body = Buffer.concat([Buffer.from('ff744f6300000002', 'hex'),
    ...fan.map(u32), ...ents.map((e) => Buffer.from(e.oid, 'hex')),
    ...ents.map((e) => u32(e.crc)), ...small.map(u32),
    ...big.map((o) => {
      const b = Buffer.alloc(8);
      b.writeBigUInt64BE(BigInt(o));
      return b;
    }), packSum]);
  return Buffer.concat([body, sha1(body)]);
}

function varintOut(n: number): number[] {
  const out: number[] = [];
  for (;;) {
    const b = n % 128;
    n = Math.floor(n / 128);
    out.push(b | (n ? 0x80 : 0));
    if (!n) return out;
  }
}

// 복사 명령 — 0 이 아닌 바이트만 쓴다. 길이 0x10000 은 길이 바이트
// 없이.
function copyOp(off: number, n: number): number[] {
  let op = 0x80;
  const tail: number[] = [];
  for (let k = 0; k < 4; k++) {
    const byte = Math.floor(off / 256 ** k) % 256;
    if (byte) {
      op |= 1 << k;
      tail.push(byte);
    }
  }
  if (n !== 0x10000) {
    for (let k = 0; k < 3; k++) {
      const byte = (n >> (8 * k)) & 0xff;
      if (byte) {
        op |= 0x10 << k;
        tail.push(byte);
      }
    }
  }
  return [op, ...tail];
}

const BLOCK = 16;

// 바탕 → 결과의 델타(SPEC.md §13.3). 다섯 언어가 같은 바이트를 낸다.
//
// 바탕을 16바이트 칸으로 잘라 "칸 내용 → 처음 나온 자리" 표를 만들고,
// 결과를 앞에서부터 훑으며 표에 있는 칸이면 앞으로 늘일 수 있는 만큼
// 복사, 없으면 한 바이트씩 끼울 것에 모은다. 표의 열쇠는 16바이트를
// latin1 로 푼 문자열이다(Map 은 Buffer 를 내용으로 견주지 않는다).
// git 의 델타 찾기(rolling hash 와 바탕 뒤로 늘이기)보다 단순하고,
// 그래서 보통 더 길다. O(결과 길이 × 복사 길이) 최악.
export function makeDelta(base: Buffer, target: Buffer): Buffer {
  const table = new Map<string, number>();
  for (let off = 0; off + BLOCK <= base.length; off += BLOCK) {
    const key = base.toString('latin1', off, off + BLOCK);
    if (!table.has(key)) table.set(key, off);
  }
  const out = [...varintOut(base.length), ...varintOut(target.length)];
  let pend: number[] = [];
  const flush = (): void => {
    for (let k = 0; k < pend.length; k += 127) {
      const chunk = pend.slice(k, k + 127);
      out.push(chunk.length, ...chunk);
    }
    pend = [];
  };
  for (let i = 0; i < target.length;) {
    const o = i + BLOCK <= target.length
      ? table.get(target.toString('latin1', i, i + BLOCK)) : undefined;
    if (o === undefined) {
      pend.push(target[i++]);
      if (pend.length === 127) flush();
      continue;
    }
    let n = BLOCK;
    while (o + n < base.length && i + n < target.length &&
      base[o + n] === target[i + n]) n++;
    flush();
    for (let k = 0; k < n; k += 0x10000) {
      out.push(...copyOp(o + k, Math.min(0x10000, n - k)));
    }
    i += n;
  }
  flush();
  return Buffer.from(out);
}

function entryHead(typ: number, size: number): number[] {
  let b = (typ << 4) | (size & 15);
  size = Math.floor(size / 16);
  const out: number[] = [];
  while (size) {
    out.push(b | 0x80);
    b = size % 128;
    size = Math.floor(size / 128);
  }
  out.push(b);
  return out;
}

// OFS_DELTA 거리 — 큰 쪽부터, 이어지는 바이트마다 1 을 뺀다.
function ofsOut(n: number): number[] {
  const out = [n % 128];
  n = Math.floor(n / 128);
  while (n) {
    n -= 1;
    out.unshift(0x80 | (n % 128));
    n = Math.floor(n / 128);
  }
  return out;
}

// 팩에 넣을 것 하나 — [형식, 몸, 델타 바탕의 목록 번호 또는 null]
export type PackItem = [type: string, body: Buffer,
  base: number | null];

// PackItem 들 → [팩 바이트, PackEntry 들]. 바탕은 목록에서 앞에
// 있어야 한다(OFS_DELTA 는 뒤로만 가리킨다).
export function writePack(items: PackItem[]): [Buffer, PackEntry[]] {
  const head = Buffer.alloc(12);
  head.write('PACK', 'latin1');
  head.writeUInt32BE(2, 4);
  head.writeUInt32BE(items.length, 8);
  const parts = [head];
  let size = head.length;
  const ents: PackEntry[] = [];
  for (const [type, body, base] of items) {
    const e = new PackEntry(size);
    [e.type, e.body] = [type, body];
    e.oid = objects.hashObject(type, body);
    let raw = body;
    let hdr: number[];
    if (base === null) {
      e.packedType = TYPE_CODES[type];
      hdr = entryHead(e.packedType, raw.length);
    } else {
      const b = ents[base];
      raw = e.delta = makeDelta(b.body!, body);
      [e.packedType, e.base, e.depth] = [OFS_DELTA, b.oid, b.depth + 1];
      hdr = [...entryHead(OFS_DELTA, raw.length),
        ...ofsOut(e.offset - b.offset)];
    }
    const rec = Buffer.concat([Buffer.from(hdr), zlib.compress(raw)]);
    parts.push(rec);
    size += rec.length;
    e.end = size;
    e.crc = crc32(rec);
    ents.push(e);
  }
  const data = Buffer.concat(parts);
  return [Buffer.concat([data, sha1(data)]), ents];
}

// git verify-pack -v 와 바이트까지 같은 줄들(SPEC.md §13.3).
export function verifyLines(entries: PackEntry[], packPath: string):
  string[] {
  const ents = [...entries].sort((a, b) => a.offset - b.offset);
  const hist = new Map<number, number>();
  const rows = ents.map((e, k) => {
    const sizeIn = (ents[k + 1]?.offset ?? e.end) - e.offset;
    // 크기는 팩에 적힌 크기 — 델타면 델타의 크기다(git 과 같다)
    const size = (e.delta ?? e.body)!.length;
    let row = `${e.oid} ${e.type.padEnd(6)} ${size} ${sizeIn} ` +
      `${e.offset}`;
    if (e.depth) row += ` ${e.depth} ${e.base}`;
    hist.set(e.depth, (hist.get(e.depth) ?? 0) + 1);
    return row;
  });
  const plural = (n: number) => `${n} object${n === 1 ? '' : 's'}`;
  rows.push('non delta: ' + plural(hist.get(0) ?? 0));
  hist.delete(0);
  for (const d of [...hist.keys()].sort((a, b) => a - b)) {
    rows.push(`chain length = ${d}: ${plural(hist.get(d)!)}`);
  }
  rows.push(`${packPath}: ok`);
  return rows;
}
