// 지형 맵 — 한 칸 두 바이트, 오토타일, 연결 성분, RLE (SPEC §4).
//
//    맵은 두 평면으로 나뉜다. 한 배열에 비트로 우겨 넣지 않는다.
//      terrain[i]  지형 종류
//      pass[i]     통행 비트 — 지형에서 파생되지만 건물이 서면 달라지므로 별도 상태다
//
//    비트마스크는 전부 산술로 다룬다(SPEC §1.1). 오토타일 마스크는 8비트뿐이라
//    JS 의 & 로도 잘릴 일이 없어 보이지만, 규칙을 한 군데서만 어기면 반드시
//    다른 곳에서 샌다.

import * as F from './fixed';

// ── SPEC §4.1 지형표 ────────────────────────────────────────────────────────
export const SAND = 0;
export const ROCK = 1;
export const WATER = 2;
export const DIRT = 3;
export const ORE = 4;
export const HILL = 5;
export const RUBBLE = 6;
export const ROAD = 7;

export const TERRAIN_CH = '.#~,*^;=';
export const TERRAIN_NAME = ['모래', '바위', '물', '흙', '광맥', '언덕',
                             '잔해', '도로'];
export const MINI_COLOR = [216, 220, 232, 214, 240, 218, 222, 226];

// 보병 통행 · 차량 통행 · 건설 가능
export const FOOT_OK = [1, 0, 0, 1, 1, 1, 1, 1];
export const VEHICLE_OK = [1, 0, 0, 1, 1, 0, 1, 1];   // 차량은 언덕에 못 오른다
export const BUILD_OK = [1, 0, 0, 1, 0, 0, 1, 1];

export const FOOT_BIT = 0;
export const VEH_BIT = 1;
export const BUILD_BIT = 2;
export const OCC_BIT = 3;

// ── SPEC §4.4 오토타일 ──────────────────────────────────────────────────────
// (모서리 방향, 양옆 변 방향 둘). 방향 번호는 fixed.DX/DY 와 같다.
const CORNERS: Array<[number, number, number]> = [
  [1, 0, 2], [3, 4, 2], [5, 4, 6], [7, 0, 6]];

// 모서리 비트는 양옆 변이 둘 다 있을 때만 살린다 (SPEC 정리 4.1).
export function canon(m: number): number {
  let r = m;
  for (const [c, a, b] of CORNERS) {
    if (!(F.bit(m, a) === 1 && F.bit(m, b) === 1)) r = F.clrbit(r, c);
  }
  return r;
}

const CLASSES: number[] = (() => {
  const seen = new Set<number>();
  for (let m = 0; m < 256; m += 1) seen.add(canon(m));
  const out = Array.from(seen);
  out.sort((a, b) => a - b);
  return out;
})();

const CLASS_INDEX = new Map<number, number>();
for (let i = 0; i < CLASSES.length; i += 1) CLASS_INDEX.set(CLASSES[i], i);

export const CLASS_COUNT = CLASSES.length;

export function classes(): number[] {
  return CLASSES.slice();
}

// 정규화된 마스크 → 0..46 그림 번호.
export function canonIndex(cm: number): number {
  return CLASS_INDEX.get(cm) as number;
}

// 4모서리(마칭 스퀘어) 16케이스. v = [좌상, 우상, 우하, 좌하] 의 0/1.
export function cornerMask(v: number[]): number {
  return v[0] + 2 * v[1] + 4 * v[2] + 8 * v[3];
}

export class TMap {
  w: number;
  h: number;
  terrain: number[];
  pass_: number[];
  version: number;
  starts: Array<[number, number]>;
  pairs: Array<[[number, number], [number, number]]>;
  private labelCache: Map<number, number[]>;

  constructor(w: number, h: number) {
    this.w = w;
    this.h = h;
    this.terrain = new Array<number>(w * h).fill(SAND);
    this.pass_ = new Array<number>(w * h).fill(0);
    this.version = 0;
    this.starts = [];
    this.pairs = [];
    this.labelCache = new Map<number, number[]>();
    for (let i = 0; i < w * h; i += 1) this.repass(i);
  }

  // ── SPEC §4.2 좌표 ───────────────────────────────────────────────────────
  idx(x: number, y: number): number {
    return y * this.w + x;
  }

  inMap(x: number, y: number): boolean {
    return x >= 0 && x < this.w && y >= 0 && y < this.h;
  }

  // 맵 밖은 ROCK 이다 — 호출자가 경계 검사를 하지 않아도 되고, 오토타일 마스크가
  // 가장자리에서 자연스럽게 닫힌다.
  terrainAt(x: number, y: number): number {
    if (!this.inMap(x, y)) return ROCK;
    return this.terrain[y * this.w + x];
  }

  // ── SPEC §4.3 통행 비트 ──────────────────────────────────────────────────
  repass(i: number): void {
    const t = this.terrain[i];
    const occ = F.bit(this.pass_[i], OCC_BIT);
    this.pass_[i] = FOOT_OK[t] + 2 * VEHICLE_OK[t] + 4 * BUILD_OK[t] + 8 * occ;
  }

  setTerrain(x: number, y: number, t: number): void {
    const i = y * this.w + x;
    if (this.terrain[i] === t) return;
    this.terrain[i] = t;
    this.repass(i);
    this.bump();
  }

  occupy(x: number, y: number, on: boolean): void {
    const i = y * this.w + x;
    this.pass_[i] = on ? F.setbit(this.pass_[i], OCC_BIT)
                       : F.clrbit(this.pass_[i], OCC_BIT);
  }

  // 건물이 선 칸 — 통행 비트를 내리고 점유 비트를 세운다 (SPEC §4.3).
  // 유닛과 달리 건물은 비키지 않는다. 예약(§13.2)만으로 막으면 유닛이 건물을
  // 향해 24틱을 두드리다 포기하므로, 경로 그래프에서 아예 뺀다.
  // `version` 이 오르니 경로 캐시와 연결 성분이 함께 무효가 된다.
  setBuilding(x: number, y: number, on: boolean): void {
    const i = y * this.w + x;
    if (on) {
      this.pass_[i] = 8;                       // 점유 비트만 남긴다
    } else {
      this.repass(i);
      this.pass_[i] = F.clrbit(this.pass_[i], OCC_BIT);
    }
    this.bump();
  }

  walkable(x: number, y: number, kind: number): boolean {
    if (!this.inMap(x, y)) return false;
    const p = this.pass_[y * this.w + x];
    return F.bit(p, kind) === 1 && F.bit(p, OCC_BIT) === 0;
  }

  // 점유를 보지 않는 통행 판정 — 경로 탐색은 이것을 쓴다(SPEC §4.3).
  passableTerrain(x: number, y: number, kind: number): boolean {
    if (!this.inMap(x, y)) return false;
    return F.bit(this.pass_[y * this.w + x], kind) === 1;
  }

  buildable(x: number, y: number): boolean {
    if (!this.inMap(x, y)) return false;
    const p = this.pass_[y * this.w + x];
    return F.bit(p, BUILD_BIT) === 1 && F.bit(p, OCC_BIT) === 0;
  }

  bump(): void {
    this.version += 1;
    this.labelCache = new Map<number, number[]>();
  }

  // ── SPEC §4.4 이웃 마스크 ────────────────────────────────────────────────
  mask(x: number, y: number): number {
    const t = this.terrainAt(x, y);
    let m = 0;
    for (let d = 0; d < 8; d += 1) {
      if (this.terrainAt(x + F.DX[d], y + F.DY[d]) === t) m = F.setbit(m, d);
    }
    return m;
  }

  tileIndex(x: number, y: number): number {
    return canonIndex(canon(this.mask(x, y)));
  }

  // ── SPEC §4.6 연결 성분 (유니온–파인드) ──────────────────────────────────
  // 통행 가능 칸을 8방향으로 묶은 대표 원소 배열. 막힌 칸은 -1.
  // 지형이 바뀌면 통째로 다시 계산한다. 증분 삭제가 되는 유니온–파인드는
  // 복잡하고, 4096칸 재계산은 측정상 1 ms 미만이다.
  labels(kind: number): number[] {
    const hit = this.labelCache.get(kind);
    if (hit !== undefined) return hit;
    const n = this.w * this.h;
    const parent = new Array<number>(n);
    for (let i = 0; i < n; i += 1) parent[i] = i;

    const find = (a0: number): number => {
      let root = a0;
      while (parent[root] !== root) root = parent[root];
      let a = a0;
      while (parent[a] !== root) {              // 경로 압축
        const nxt = parent[a];
        parent[a] = root;
        a = nxt;
      }
      return root;
    };

    for (let y = 0; y < this.h; y += 1) {
      for (let x = 0; x < this.w; x += 1) {
        if (!this.passableTerrain(x, y, kind)) continue;
        let a = find(y * this.w + x);
        for (let d = 0; d < 8; d += 1) {
          const u = x + F.DX[d];
          const v = y + F.DY[d];
          if (this.passableTerrain(u, v, kind)) {
            const b = find(v * this.w + u);
            if (a !== b) {
              parent[b] = a;
              a = find(a);
            }
          }
        }
      }
    }
    const out = new Array<number>(n).fill(-1);
    for (let y = 0; y < this.h; y += 1) {
      for (let x = 0; x < this.w; x += 1) {
        if (this.passableTerrain(x, y, kind)) {
          out[y * this.w + x] = find(y * this.w + x);
        }
      }
    }
    this.labelCache.set(kind, out);
    return out;
  }

  // ── SPEC §4.7 RLE ────────────────────────────────────────────────────────
  saveRle(): number[] {
    const body: number[] = [];
    for (const ch of 'RTSM') body.push(ch.charCodeAt(0));
    body.push(1);
    body.push(this.w);
    body.push(this.h);
    for (const plane of [this.terrain, this.pass_]) {
      let run = 0;
      let val = -1;
      for (const v of plane) {
        if (v === val && run < 255) {
          run += 1;
        } else {
          if (run !== 0) {
            body.push(run);
            body.push(val);
          }
          run = 1;
          val = v;
        }
      }
      if (run !== 0) {
        body.push(run);
        body.push(val);
      }
    }
    const c = F.crc16(body);
    body.push(F.floordiv(c, 256));
    body.push(F.fmod(c, 256));
    return body;
  }

  static loadRle(blob: ArrayLike<number>): TMap {
    const b: number[] = [];
    for (let i = 0; i < blob.length; i += 1) b.push(blob[i]);
    if (String.fromCharCode(b[0], b[1], b[2], b[3]) !== 'RTSM') {
      throw new Error('맵 파일이 아니다');
    }
    const want = b[b.length - 2] * 256 + b[b.length - 1];
    if (F.crc16(b.slice(0, b.length - 2)) !== want) {
      throw new Error('CRC 불일치 — 맵이 깨졌다');
    }
    const w = b[5];
    const h = b[6];
    const m = new TMap(w, h);
    let pos = 7;
    for (const plane of [m.terrain, m.pass_]) {
      let i = 0;
      while (i < w * h) {
        const run = b[pos];
        const val = b[pos + 1];
        pos += 2;
        for (let k = 0; k < run; k += 1) {
          plane[i] = val;
          i += 1;
        }
      }
    }
    m.bump();
    return m;
  }

  // ── 골든 맵 텍스트 (시험용) ──────────────────────────────────────────────
  // golden/map_*.txt 를 읽는다. '.'/'#' 격자와 지형 문자 격자 둘 다.
  static loadText(text: string): TMap {
    const lines = text.split('\n');
    let w = 0;
    let h = 0;
    let m: TMap | null = null;
    let i = 0;
    while (i < lines.length) {
      const ln = lines[i];
      if (ln.indexOf('size ') === 0) {
        const v = ln.slice(5).trim().split(/\s+/).map((s) => parseInt(s, 10));
        w = v[0];
        h = v[1];
      } else if (ln === 'map' || ln === 'terrain') {
        m = new TMap(w, h);
        for (let y = 0; y < h; y += 1) {
          const row = lines[i + 1 + y];
          for (let x = 0; x < w; x += 1) {
            const ch = row[x];
            if (ln === 'map') m.terrain[y * w + x] = ch === '#' ? ROCK : DIRT;
            else m.terrain[y * w + x] = TERRAIN_CH.indexOf(ch);
            m.repass(y * w + x);
          }
        }
        i += h;
      } else if (ln.indexOf('pairs ') === 0) {
        const cnt = parseInt(ln.slice(6), 10);
        for (let k = 0; k < cnt; k += 1) {
          const v = lines[i + 1 + k].trim().split(/\s+/)
            .map((s) => parseInt(s, 10));
          (m as TMap).pairs.push([[v[0], v[1]], [v[2], v[3]]]);
        }
        i += cnt;
      } else if (ln.indexOf('start ') === 0) {
        const cnt = parseInt(ln.slice(6), 10);
        for (let k = 0; k < cnt; k += 1) {
          const v = lines[i + 1 + k].trim().split(/\s+/)
            .map((s) => parseInt(s, 10));
          (m as TMap).starts.push([v[0], v[1]]);
        }
        i += cnt;
      }
      i += 1;
    }
    (m as TMap).bump();
    return m as TMap;
  }
}
