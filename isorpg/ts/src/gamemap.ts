// 지형 맵 — SPEC §5. 한 칸 1바이트, 다이아몬드-스퀘어 생성, RLE 저장.
//
// 파이썬 쪽이 모듈 이름을 map 이 아니라 gamemap 으로 둔 것은 내장 map 과
// 겹치지 않게 하려는 것이다. 타입스크립트에서는 같은 이유로 클래스 이름도
// Map 이 아니라 GameMap 이다 — ES2015 의 전역 Map 을 모듈 안에서 가려 버리면
// 나중에 진짜 Map 이 필요해졌을 때 조용히 엉뚱한 것을 쓰게 된다.
import { Rng } from './rng';

export const MAP_W = 48;
export const MAP_H = 48;
export const MAXH = 15;

// 지형 id — 셀 바이트의 하위 4비트
export const T_DEEP = 0;
export const T_WATER = 1;
export const T_SAND = 2;
export const T_GRASS = 3;
export const T_DIRT = 4;
export const T_ROCK = 5;
export const T_FOREST = 6;
export const T_MOUNTAIN = 7;
export const T_ROAD = 8;
export const T_FLOOR = 9;
export const T_WALL = 10;
export const T_BRIDGE = 11;
export const T_SNOW = 12;
export const T_SWAMP = 13;
export const T_LAVA = 14;
export const T_VOID = 15;

// (이름, 이동비용 0=불가, 시야차단)
export const TERRAIN: Array<[string, number, boolean]> = [
  ['DEEP', 0, false], ['WATER', 0, false], ['SAND', 12, false],
  ['GRASS', 10, false], ['DIRT', 10, false], ['ROCK', 14, false],
  ['FOREST', 16, true], ['MOUNTAIN', 0, true], ['ROAD', 8, false],
  ['FLOOR', 10, false], ['WALL', 0, true], ['BRIDGE', 10, false],
  ['SNOW', 13, false], ['SWAMP', 20, false], ['LAVA', 0, false],
  ['VOID', 0, true],
];
export const MOVE: number[] = TERRAIN.map((t) => t[1]);
export const OPAQUE: boolean[] = TERRAIN.map((t) => t[2]);
export const MIN_MOVE: number = MOVE.filter((v) => v > 0).reduce((a, b) => (a < b ? a : b));

export function makeCell(t: number, h: number): number {
  return t + h * 16;
}

export function terrainOf(cell: number): number {
  return cell % 16;
}

export function heightOf(cell: number): number {
  return Math.floor(cell / 16);
}

export class GameMap {
  w: number;
  h: number;
  cells: Uint8Array;

  constructor(w: number, h: number, cells?: Uint8Array) {
    this.w = w;
    this.h = h;
    // Uint8Array 는 범위를 벗어난 대입을 조용히 감싼다. 셀은 make_cell 로만
    // 만들고(0..255 보장) 그 밖의 경로로는 쓰지 않는 것이 유일한 방어다.
    this.cells = cells !== undefined ? cells : new Uint8Array(w * h);
  }

  inside(x: number, y: number): boolean {
    return x >= 0 && x < this.w && y >= 0 && y < this.h;
  }

  at(x: number, y: number): number {
    return this.cells[y * this.w + x] as number;
  }

  put(x: number, y: number, cell: number): void {
    this.cells[y * this.w + x] = cell;
  }

  terrain(x: number, y: number): number {
    return (this.cells[y * this.w + x] as number) % 16;
  }

  height(x: number, y: number): number {
    return Math.floor((this.cells[y * this.w + x] as number) / 16);
  }
}

// ---------------------------------------------------------------- 다이아몬드-스퀘어
export const DS_N = 64;
export const DS_SEED = 1;
export const DS_CORNER: number[] = [520, 300, 700, 420];
export const DS_SCALE = 560;
export const DS_ROUGH_NUM = 58;
export const DS_ROUGH_DEN = 100;
export const DS_OFF = Math.floor((DS_N + 1 - MAP_W) / 2); // 65x65 에서 가운데 48x48

/** 프랙탈 중점 변위. 반복 순서가 난수 소비 순서를 정하므로 명세의 일부다.
 *
 *  O(n^2) 시간, O(n^2) 공간. 격자는 (2^k + 1) 이어야 한다.
 *  값이 ±수천 수준이라 Int16Array 로도 되지만, 중간에 clamp 전 값이
 *  범위를 넘을 수 있어 감싸기 사고가 나기 쉽다. 평범한 number[][] 로 둔다. */
export function genHeight(
  n: number, corners: number[], scale0: number, seed: number,
  roughNum: number = DS_ROUGH_NUM, roughDen: number = DS_ROUGH_DEN,
): number[][] {
  const size = n + 1;
  const h: number[][] = [];
  for (let i = 0; i < size; i++) h.push(new Array<number>(size).fill(0));
  (h[0] as number[])[0] = corners[0] as number;
  (h[0] as number[])[n] = corners[1] as number;
  (h[n] as number[])[0] = corners[2] as number;
  (h[n] as number[])[n] = corners[3] as number;
  const r = new Rng(seed);
  let step = n;
  let scale = scale0;
  const jitter = (): number => {
    const span = 2 * scale + 1;
    const v = r.next();
    return v - span * Math.floor(v / span) - scale;
  };
  while (step > 1) {
    const half = Math.floor(step / 2);
    // 다이아몬드: 정사각형 네 꼭짓점의 평균 + 흔들림
    for (let y = half; y < size; y += step) {
      for (let x = half; x < size; x += step) {
        const s = ((h[y - half] as number[])[x - half] as number)
          + ((h[y - half] as number[])[x + half] as number)
          + ((h[y + half] as number[])[x - half] as number)
          + ((h[y + half] as number[])[x + half] as number);
        (h[y] as number[])[x] = Math.floor(s / 4) + jitter();
      }
    }
    // 스퀘어: 마름모 네 꼭짓점(격자 밖은 뺀다)의 평균 + 흔들림.
    // 행 간격은 half, 열 간격은 step 이고 홀짝 행마다 시작 열이 어긋난다 —
    // 그래야 아직 값이 없는 변의 중점만 정확히 한 번씩 채운다.
    for (let y = 0; y < size; y += half) {
      const xs = Math.floor(y / half) % 2 === 0 ? half : 0;
      for (let x = xs; x < size; x += step) {
        let s = 0;
        let cnt = 0;
        if (x - half >= 0) { s += (h[y] as number[])[x - half] as number; cnt += 1; }
        if (x + half < size) { s += (h[y] as number[])[x + half] as number; cnt += 1; }
        if (y - half >= 0) { s += (h[y - half] as number[])[x] as number; cnt += 1; }
        if (y + half < size) { s += (h[y + half] as number[])[x] as number; cnt += 1; }
        (h[y] as number[])[x] = Math.floor(s / cnt) + jitter();
      }
    }
    step = half;
    scale = Math.floor((scale * roughNum) / roughDen);
  }
  for (const row of h) {
    for (let i = 0; i < size; i++) {
      const v = row[i] as number;
      row[i] = v < 0 ? 0 : v > 1023 ? 1023 : v;
    }
  }
  return h;
}

export const DS_BLUR = 2;

/** 3x3 상자 흐리기. 프랙탈 그대로는 타일 눈금에서 잡음처럼 보인다.
 *
 *  O(9 * n^2) 시간. 가장자리는 격자 안의 이웃만 평균한다.
 *  RLE 가 실제로 압축되게 만드는 유일한 장치이기도 하다. */
export function smooth(h0: number[][]): number[][] {
  const n = h0.length;
  let h = h0;
  for (let pass = 0; pass < DS_BLUR; pass++) {
    const g: number[][] = [];
    for (let i = 0; i < n; i++) g.push(new Array<number>(n).fill(0));
    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        let s = 0;
        let c = 0;
        for (let dy = -1; dy <= 1; dy++) {
          const yy = y + dy;
          if (yy < 0 || yy >= n) continue;
          const row = h[yy] as number[];
          for (let dx = -1; dx <= 1; dx++) {
            const xx = x + dx;
            if (xx >= 0 && xx < n) { s += row[xx] as number; c += 1; }
          }
        }
        (g[y] as number[])[x] = Math.floor(s / c);
      }
    }
    h = g;
  }
  return h;
}

/** 높이값 -> 지형. 문턱은 SPEC §5.5 가 정한다. */
export function terrainOfValue(v: number): number {
  if (v < 100) return T_DEEP;
  if (v < 205) return T_WATER;
  if (v < 240) return T_SAND;
  if (v < 460) return T_GRASS;
  if (v < 630) return T_FOREST;
  if (v < 800) return T_ROCK;
  return T_MOUNTAIN;
}

export function heightOfValue(v: number): number {
  if (v < 205) return 0;
  const hh = Math.floor((v - 205) / 90);
  return hh > 12 ? 12 : hh;
}

export const TOWN_X0 = 18;
export const TOWN_Y0 = 18;
export const TOWN_X1 = 30;
export const TOWN_Y1 = 30;
export const TOWN_MID = 24;
export const TOWN_H = 2;
export const TOWN_WALL_H = 4; // 성벽은 바닥보다 두 단계 높다 — 그래야 옆면이 보인다

/** 마을을 찍는다. 순서가 중요하다 — 벽을 먼저 두르고 문을 나중에 뚫는다. */
export function stampTown(m: GameMap): void {
  for (let ty = TOWN_Y0; ty < TOWN_Y1; ty++) {
    for (let tx = TOWN_X0; tx < TOWN_X1; tx++) {
      if (tx === TOWN_X0 || tx === TOWN_X1 - 1 || ty === TOWN_Y0 || ty === TOWN_Y1 - 1) {
        m.put(tx, ty, makeCell(T_WALL, TOWN_WALL_H));
        continue;
      }
      const t = tx === TOWN_MID || ty === TOWN_MID ? T_ROAD : T_FLOOR;
      m.put(tx, ty, makeCell(t, TOWN_H));
    }
  }
  const gates: Array<[number, number]> = [
    [TOWN_MID, TOWN_Y0], [TOWN_MID, TOWN_Y1 - 1],
    [TOWN_X0, TOWN_MID], [TOWN_X1 - 1, TOWN_MID],
  ];
  for (const [tx, ty] of gates) m.put(tx, ty, makeCell(T_ROAD, TOWN_H));
  for (let ty = 0; ty < TOWN_Y0; ty++) m.put(TOWN_MID, ty, makeCell(T_ROAD, TOWN_H));
  for (let ty = TOWN_Y1; ty < MAP_H; ty++) m.put(TOWN_MID, ty, makeCell(T_ROAD, TOWN_H));
}

/** 맵 한 장. 같은 씨앗이면 언제나 같은 맵이다. */
export function genMap(): GameMap {
  const hg = smooth(genHeight(DS_N, DS_CORNER, DS_SCALE, DS_SEED));
  const m = new GameMap(MAP_W, MAP_H);
  for (let ty = 0; ty < MAP_H; ty++) {
    const row = hg[ty + DS_OFF] as number[];
    for (let tx = 0; tx < MAP_W; tx++) {
      const v = row[tx + DS_OFF] as number;
      m.put(tx, ty, makeCell(terrainOfValue(v), heightOfValue(v)));
    }
  }
  stampTown(m);
  return m;
}

// ---------------------------------------------------------------- RLE
/** 행 우선으로 훑어 같은 값을 묶는다. 런 하나는 최대 255칸. */
export function saveRle(m: GameMap): string {
  const runs: string[] = [];
  let i = 0;
  const n = m.cells.length;
  while (i < n) {
    const v = m.cells[i] as number;
    let j = i;
    while (j < n && m.cells[j] === v && j - i < 255) j += 1;
    runs.push(String(j - i) + ':' + String(v));
    i = j;
  }
  const lines: string[] = ['ISORPG-MAP 1 ' + m.w + ' ' + m.h];
  for (let k = 0; k < runs.length; k += 16) lines.push(runs.slice(k, k + 16).join(' '));
  return lines.join('\n') + '\n';
}

export function loadRle(text: string): GameMap {
  const lines = text.trim().split('\n');
  const head = (lines[0] as string).split(/\s+/);
  if (head[0] !== 'ISORPG-MAP') throw new Error('맵 매직이 다르다: ' + head[0]);
  const w = parseInt(head[2] as string, 10);
  const h = parseInt(head[3] as string, 10);
  const cells: number[] = [];
  for (let li = 1; li < lines.length; li++) {
    const toks = (lines[li] as string).split(/\s+/).filter((s) => s.length > 0);
    for (const run of toks) {
      const parts = run.split(':');
      const c = parseInt(parts[0] as string, 10);
      const v = parseInt(parts[1] as string, 10);
      for (let k = 0; k < c; k++) cells.push(v);
    }
  }
  if (cells.length !== w * h) {
    throw new Error('칸 수가 ' + w * h + ' 여야 하는데 ' + cells.length);
  }
  return new GameMap(w, h, Uint8Array.from(cells));
}
