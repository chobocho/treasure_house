// 세이브와 CRC — SPEC §11.
//
// 전부 빅 엔디언이다. 바이트 순서를 손으로 나눠 쓰면 어느 언어에서든 같다.
// DataView 나 Buffer.writeUInt32BE 를 쓰면 더 짧아지지만, 파이썬·루아 판과
// 코드가 갈라져 '같은 형식인가'를 눈으로 확인할 수 없게 된다.
// xor 도 마찬가지 이유로 JS 의 ^ 대신 fixed 의 산술 xor 를 쓴다.
import { xor8, xor16 } from './fixed';

export const CRC_POLY = 0x1021;
export const CRC_INIT = 0xffff;

/** CRC-16/CCITT-FALSE 표. 다항식 나눗셈을 바이트 단위로 미리 접어 둔 것이다. */
function makeTable(): number[] {
  const tbl: number[] = [];
  for (let i = 0; i < 256; i++) {
    let c = i * 256;
    for (let k = 0; k < 8; k++) {
      const hi = c >= 32768;
      c = (c * 2) % 65536;
      if (hi) c = xor16(c, CRC_POLY);
    }
    tbl.push(c);
  }
  return tbl;
}

export const CRC_TBL: number[] = makeTable();

/** 표 구동 CRC. 한 바이트에 xor 두 번과 표 조회 한 번.
 *  (c*256) mod 65536 은 하위 바이트가 0 이므로 상위 바이트만 8비트 xor 하면 된다. */
export function crc16(data: Uint8Array | number[]): number {
  let c = CRC_INIT;
  for (let i = 0; i < data.length; i++) {
    const b = data[i] as number;
    const t = CRC_TBL[xor8(Math.floor(c / 256), b)] as number;
    c = xor8(c % 256, Math.floor(t / 256)) * 256 + (t % 256);
  }
  return c;
}

// ---------------------------------------------------------------- 정수 인코딩
export function i32ToU32(v: number): number {
  return v - 4294967296 * Math.floor(v / 4294967296);
}

export function u32ToI32(v: number): number {
  return v >= 2147483648 ? v - 4294967296 : v;
}

function u8(out: number[], v: number): void {
  out.push(v % 256);
}

function u16(out: number[], v: number): void {
  out.push(Math.floor(v / 256) % 256);
  out.push(v % 256);
}

function u32(out: number[], v0: number): void {
  const v = i32ToU32(v0);
  out.push(Math.floor(v / 16777216));
  out.push(Math.floor(v / 65536) % 256);
  out.push(Math.floor(v / 256) % 256);
  out.push(v % 256);
}

export class Reader {
  d: Uint8Array;
  i = 0;

  constructor(d: Uint8Array) {
    this.d = d;
  }

  u8(): number {
    const v = this.d[this.i] as number;
    this.i += 1;
    return v;
  }

  u16(): number {
    return this.u8() * 256 + this.u8();
  }

  u32(): number {
    return this.u16() * 65536 + this.u16();
  }

  i32(): number {
    return u32ToI32(this.u32());
  }
}

export const MAGIC: number[] = [0x49, 0x53, 0x4f, 0x31]; // 'ISO1'

// game 모듈을 import 하면 순환이 되므로, 세이브가 필요로 하는 모양만 적어 둔다.
// TS 의 구조적 타이핑이라 Game 클래스는 아무 선언 없이 이 형을 만족한다.
export interface SaveEntity {
  kind: number; fx: number; fy: number; h: number; hp: number; maxhp: number;
  lv: number; xp: number; atk: number; dfn: number; armor: number;
  dirn: number; alive: number;
}

export interface SaveGame {
  tickN: number;
  rng: { s: number };
  camX: number;
  camY: number;
  ents: SaveEntity[];
  fog: { bits: Uint8Array; recount(): void };
}

/** 게임 상태를 바이트열로. 끝에 CRC 2바이트가 붙는다. */
export function packState(g: SaveGame): Uint8Array {
  const out: number[] = MAGIC.slice();
  u32(out, g.tickN);
  u32(out, g.rng.s);
  u32(out, i32ToU32(g.camX));
  u32(out, i32ToU32(g.camY));
  u16(out, g.ents.length);
  for (const e of g.ents) {
    u8(out, e.kind);
    u32(out, i32ToU32(e.fx));
    u32(out, i32ToU32(e.fy));
    u8(out, e.h);
    u16(out, e.hp);
    u16(out, e.maxhp);
    u8(out, e.lv);
    u32(out, e.xp);
    u8(out, e.atk);
    u8(out, e.dfn);
    u8(out, e.armor);
    u8(out, e.dirn);
    u8(out, e.alive);
  }
  // 안개는 타일 4개에 1바이트. 2비트씩 접어 넣는다.
  const bits = g.fog.bits;
  const n = bits.length;
  u16(out, Math.floor((n + 3) / 4));
  let i = 0;
  while (i < n) {
    let b = 0;
    let p = 1;
    for (let k = 0; k < 4; k++) {
      const v = i + k < n ? (bits[i + k] as number) : 0;
      b += (v % 4) * p;
      p *= 4;
    }
    out.push(b);
    i += 4;
  }
  u16(out, crc16(out));
  return Uint8Array.from(out);
}

/** 세이브를 게임에 되돌린다. CRC 가 맞지 않으면 Error. */
export function unpackState(data: Uint8Array, g: SaveGame): SaveGame {
  for (let i = 0; i < 4; i++) {
    if (data[i] !== MAGIC[i]) throw new Error('세이브 매직이 다르다');
  }
  const want = (data[data.length - 2] as number) * 256 + (data[data.length - 1] as number);
  if (crc16(data.subarray(0, data.length - 2)) !== want) {
    throw new Error('세이브가 손상됐다 (CRC 불일치)');
  }
  const r = new Reader(data);
  r.i = 4;
  g.tickN = r.u32();
  g.rng.s = r.u32();
  g.camX = r.i32();
  g.camY = r.i32();
  const cnt = r.u16();
  if (cnt !== g.ents.length) {
    throw new Error('엔티티 수가 ' + g.ents.length + ' 여야 하는데 ' + cnt);
  }
  for (const e of g.ents) {
    e.kind = r.u8();
    e.fx = r.i32();
    e.fy = r.i32();
    e.h = r.u8();
    e.hp = r.u16();
    e.maxhp = r.u16();
    e.lv = r.u8();
    e.xp = r.u32();
    e.atk = r.u8();
    e.dfn = r.u8();
    e.armor = r.u8();
    e.dirn = r.u8();
    e.alive = r.u8();
  }
  const nb = r.u16();
  const bits = g.fog.bits;
  const n = bits.length;
  for (let j = 0; j < nb; j++) {
    const b = r.u8();
    let p = 1;
    for (let k = 0; k < 4; k++) {
      const i = j * 4 + k;
      if (i < n) bits[i] = Math.floor(b / p) % 4;
      p *= 4;
    }
  }
  // 비트만 되돌리고 누적 개수를 그대로 두면, 되돌린 뒤의 트레이스가
  // 복원된 상태의 함수가 아니게 된다. 개수는 비트에서 다시 센다.
  g.fog.recount();
  return g;
}
