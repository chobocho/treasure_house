// 맵 자료구조 — SPEC §2
//
// 여기서 타입드 어레이가 처음 나온다. Uint8Array 는 자바스크립트에서
// '진짜 바이트 배열'에 가장 가까운 것이고, 도스의 한 칸 = 한 바이트 모델을
// 그대로 옮길 수 있다. 일반 배열(Array<number>)을 쓰면 값마다 태그가 붙어
// 메모리가 8배가 되고, 무엇보다 값이 0..255 라는 보장이 사라진다.

import * as H from './hexcoord';

export const MAP_W = 24;
export const MAP_H = 18;
export const MAP_N = MAP_W * MAP_H;

export const TERRAIN_MASK = 0x0f;
export const ELEV_SHIFT = 4;
export const ELEV_MASK = 0x07;
export const ROAD_BIT = 0x80;

export function packCell(terrain: number, elev: number, road: number): number {
  return ((road & 1) << 7) | ((elev & ELEV_MASK) << ELEV_SHIFT) | (terrain & TERRAIN_MASK);
}

export function cellTerrain(c: number): number { return c & TERRAIN_MASK; }
export function cellElev(c: number): number { return (c >> ELEV_SHIFT) & ELEV_MASK; }
export function cellRoad(c: number): number { return (c >> 7) & 1; }

export const CLEAR = 0, FOREST = 1, HILL = 2, MOUNTAIN = 3;
export const CITY = 4, RIVER = 5, SWAMP = 6, SEA = 7;

interface TerrainDef {
  key: string; name: string; move: number; def: number;
  block: number; losh: number; ch: string;
}

export const TERRAIN: ReadonlyArray<TerrainDef> = [
  { key: 'CLEAR', name: '평지', move: 2, def: 0, block: 0, losh: 0, ch: '.' },
  { key: 'FOREST', name: '숲', move: 4, def: 2, block: 1, losh: 1, ch: 'f' },
  { key: 'HILL', name: '언덕', move: 4, def: 1, block: 0, losh: 1, ch: 'h' },
  { key: 'MOUNTAIN', name: '산', move: 6, def: 3, block: 1, losh: 2, ch: 'M' },
  { key: 'CITY', name: '도시', move: 2, def: 4, block: 1, losh: 1, ch: 'C' },
  { key: 'RIVER', name: '강', move: 6, def: 1, block: 0, losh: 0, ch: '~' },
  { key: 'SWAMP', name: '늪', move: 6, def: 0, block: 0, losh: 0, ch: 's' },
  { key: 'SEA', name: '바다', move: -1, def: 0, block: 0, losh: 0, ch: '#' },
];

export const T_MOVE = TERRAIN.map((t) => t.move);
export const T_DEF = TERRAIN.map((t) => t.def);
export const T_BLOCK = TERRAIN.map((t) => t.block);
export const T_LOSH = TERRAIN.map((t) => t.losh);
export const T_CHAR = TERRAIN.map((t) => t.ch);
export const CHAR_TO_TERRAIN = new Map<string, number>(TERRAIN.map((t, i) => [t.ch, i]));

export const FOG_HIDDEN = 0, FOG_EXPLORED = 1, FOG_VISIBLE = 2;

// odd-r 이웃 델타 — [행 홀짝][방향 0..5]
export const NEIGHBOR_DELTA: ReadonlyArray<ReadonlyArray<readonly [number, number]>> = [
  [[1, 0], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]],
  [[1, 0], [1, -1], [0, -1], [-1, 0], [0, 1], [1, 1]],
];

export class HexMap {
  readonly w: number;
  readonly h: number;
  readonly n: number;
  readonly cells: Uint8Array;
  readonly fog: Uint8Array;
  readonly occupant: Int16Array;

  constructor(w: number = MAP_W, h: number = MAP_H) {
    this.w = w;
    this.h = h;
    this.n = w * h;
    this.cells = new Uint8Array(this.n);
    this.fog = new Uint8Array(this.n);
    this.occupant = new Int16Array(this.n).fill(-1);
  }

  idx(col: number, row: number): number { return row * this.w + col; }

  inBounds(col: number, row: number): boolean {
    return col >= 0 && col < this.w && row >= 0 && row < this.h;
  }

  axialIdx(q: number, r: number): number {
    const [col, row] = H.axialToOddr(q, r);
    if (col >= 0 && col < this.w && row >= 0 && row < this.h) return row * this.w + col;
    return -1;
  }

  idxAxial(i: number): [number, number] {
    const row = Math.floor(i / this.w);
    return H.oddrToAxial(i - row * this.w, row);
  }

  terrainAt(i: number): number { return this.cells[i]! & TERRAIN_MASK; }
  elevAt(i: number): number { return (this.cells[i]! >> ELEV_SHIFT) & ELEV_MASK; }
  roadAt(i: number): number { return (this.cells[i]! >> 7) & 1; }

  setCell(col: number, row: number, terrain: number, elev = 0, road = 0): void {
    this.cells[row * this.w + col] = packCell(terrain, elev, road);
  }

  passable(i: number): boolean {
    return T_MOVE[this.cells[i]! & TERRAIN_MASK]! >= 0;
  }

  // (방향, 이웃 인덱스) 쌍. 배열을 매번 새로 만들지 않도록 호출자가 준 버퍼에
  // 채워 넣는다 — 경로 탐색의 가장 뜨거운 루프라 할당을 없애는 값어치가 있다.
  neighborsWithDir(i: number, outDir: Int32Array, outIdx: Int32Array): number {
    const row = Math.floor(i / this.w);
    const col = i - row * this.w;
    const deltas = NEIGHBOR_DELTA[row & 1]!;
    let k = 0;
    for (let d = 0; d < 6; d++) {
      const c = col + deltas[d]![0];
      const r = row + deltas[d]![1];
      if (c >= 0 && c < this.w && r >= 0 && r < this.h) {
        outDir[k] = d;
        outIdx[k] = r * this.w + c;
        k++;
      }
    }
    return k;
  }

  toText(): string {
    const lines: string[] = [];
    for (let row = 0; row < this.h; row++) {
      let a = '', b = '';
      for (let col = 0; col < this.w; col++) {
        const c = this.cells[row * this.w + col]!;
        a += T_CHAR[c & TERRAIN_MASK]!;
        b += String((c >> ELEV_SHIFT) & ELEV_MASK);
      }
      lines.push(a, b);
    }
    return lines.join('\n');
  }

  fogText(): string {
    const lines: string[] = [];
    for (let row = 0; row < this.h; row++) {
      let a = '';
      for (let col = 0; col < this.w; col++) a += String(this.fog[row * this.w + col]!);
      lines.push(a);
    }
    return lines.join('\n');
  }
}
