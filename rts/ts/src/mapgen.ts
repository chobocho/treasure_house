// 맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·포아송 자원·대칭 (SPEC §5).
//
//    생성기는 게임이 시작하기 전에 한 번만 돈다. 그래서 시뮬레이션 RNG 와
//    **다른 인스턴스**를 쓴다(SPEC §3.3). 여기서 뽑은 난수가 시뮬 수열에
//    끼어들면 두 기계가 같은 맵을 놓고도 다른 게임을 하게 된다.

import { LCG } from './rng';
import * as T from './tmap';

export const MW = 64;
export const MH = 64;
export const START: Array<[number, number]> = [[8, 8], [55, 55]];
export const ORE_TRIES = 4000;
export const ORE_COUNT = 12;
export const ORE_RMIN = 9;

// 높이 → 지형 (SPEC §5.2). 위에서부터 처음 걸리는 것.
export const THRESH: Array<[number, number]> = [
  [63, T.WATER], [95, T.SAND], [175, T.DIRT], [207, T.HILL], [255, T.ROCK]];

// 마지막 생성의 광맥 중심점 — 시험·덱용
export let LAST_ORE: Array<[number, number]> = [];

export function terrainOf(v: number): number {
  for (const [lim, t] of THRESH) {
    if (v <= lim) return t;
  }
  return T.ROCK;
}

function clamp(v: number): number {
  return v < 0 ? 0 : (v > 255 ? 255 : v);
}

// ── SPEC §5.1 셀룰러 오토마타 ───────────────────────────────────────────────
// B5678/S45678 한 세대. 맵 밖은 벽으로 센다.
// 살아 있는 벽은 이웃 벽이 4 이상이면 남고, 빈 칸은 5 이상이면 벽이 된다.
// 2세대면 덩어리가 덜 뭉치고 6세대면 좁은 통로가 전부 막힌다 —
// 4세대가 통로와 개활지가 함께 남는 자리다.
export function cellularStep(cur: number[], w: number, h: number): number[] {
  const nxt = new Array<number>(w * h).fill(0);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      let n = 0;
      for (const dy of [-1, 0, 1]) {
        for (const dx of [-1, 0, 1]) {
          if (dx === 0 && dy === 0) continue;
          const u = x + dx;
          const v = y + dy;
          n += (u >= 0 && u < w && v >= 0 && v < h) ? cur[v * w + u] : 1;
        }
      }
      if (cur[y * w + x] === 1) nxt[y * w + x] = n >= 4 ? 1 : 0;
      else nxt[y * w + x] = n >= 5 ? 1 : 0;
    }
  }
  return nxt;
}

export function cellular(w: number, h: number, rand: LCG,
                         gens = 4, fill = 45): number[] {
  let cur: number[] = [];
  for (let i = 0; i < w * h; i += 1) cur.push(rand.roll(100) < fill ? 1 : 0);
  for (let k = 0; k < gens; k += 1) cur = cellularStep(cur, w, h);
  return cur;
}

// ── SPEC §5.2 다이아몬드-스퀘어 ─────────────────────────────────────────────
// (2^6)+1 = 65 칸 격자. 평균은 반올림이 아니라 내림이다 — 명세다.
export function diamondSquare(rand: LCG): number[][] {
  const n = 65;
  const h: number[][] = [];
  for (let y = 0; y < n; y += 1) h.push(new Array<number>(n).fill(0));
  for (const [x, y] of [[0, 0], [0, 64], [64, 0], [64, 64]]) {
    h[y][x] = rand.roll(256);
  }
  let step = 64;
  while (step > 1) {
    const half = Math.floor(step / 2);
    const amp = Math.floor(step * 255 / 128);
    for (let y = 0; y < n - 1; y += step) {
      for (let x = 0; x < n - 1; x += step) {
        const a = Math.floor((h[y][x] + h[y][x + step]
                              + h[y + step][x] + h[y + step][x + step]) / 4);
        h[y + half][x + half] = clamp(a + rand.roll(2 * amp + 1) - amp);
      }
    }
    let row = 0;
    for (let y = 0; y < n; y += half) {
      const start = row % 2 === 0 ? half : 0;
      for (let x = start; x < n; x += step) {
        let t = 0;
        let c = 0;
        for (const [dx, dy] of [[-half, 0], [half, 0], [0, -half], [0, half]]) {
          const u = x + dx;
          const v = y + dy;
          if (u >= 0 && u < n && v >= 0 && v < n) {
            t += h[v][u];
            c += 1;
          }
        }
        h[y][x] = clamp(Math.floor(t / c) + rand.roll(2 * amp + 1) - amp);
      }
      row += 1;
    }
    step = half;
  }
  return h;
}

// ── SPEC §5.3 정수 포아송 디스크 ────────────────────────────────────────────
// 앞쪽 절반에만 놓고 대칭 복사한다. 시도 상한이 반드시 있어야 한다 —
// 상한 없는 재시도는 디싱크보다 나쁘다(맵 생성이 영원히 끝나지 않는다).
export function placeOre(m: T.TMap, rand: LCG, n = ORE_COUNT,
                         rmin = ORE_RMIN): [Array<[number, number]>, number] {
  const pts: Array<[number, number]> = [];
  let tries = 0;
  while (pts.length < n && tries < ORE_TRIES) {
    tries += 1;
    const x = rand.roll(MW);
    const y = rand.roll(Math.floor(MH / 2));
    const t = m.terrain[y * MW + x];
    if (t !== T.DIRT && t !== T.SAND) continue;
    let ok = true;
    for (const [px, py] of pts) {
      if ((x - px) * (x - px) + (y - py) * (y - py) < rmin * rmin) {
        ok = false;
        break;
      }
    }
    if (ok) pts.push([x, y]);
  }
  for (const [px, py] of pts) {
    for (let dy = -2; dy <= 2; dy += 1) {
      for (let dx = -2; dx <= 2; dx += 1) {
        if (dx * dx + dy * dy > 4) continue;
        const u = px + dx;
        const v = py + dy;
        if (u >= 0 && u < MW && v >= 0 && v < MH) {
          const t = m.terrain[v * MW + u];
          if (t === T.DIRT || t === T.SAND) {
            m.terrain[v * MW + u] = T.ORE;
            m.terrain[(MH - 1 - v) * MW + (MW - 1 - u)] = T.ORE;
          }
        }
      }
    }
  }
  return [pts, tries];
}

// ── SPEC §5.4 대칭과 시작 지점 ──────────────────────────────────────────────
// 180도 회전 대칭. 앞쪽 절반이 원본이다.
export function symmetrize(m: T.TMap): void {
  for (let y = 0; y < MH; y += 1) {
    for (let x = 0; x < MW; x += 1) {
      if (y * MW + x < MW * MH / 2) {
        m.terrain[(MH - 1 - y) * MW + (MW - 1 - x)] = m.terrain[y * MW + x];
      }
    }
  }
}

// 시작 지점 5×5 를 흙으로 — 사령부 3×3 이 반드시 들어가야 한다.
export function clearBase(m: T.TMap): void {
  for (const [bx, by] of START) {
    for (let dy = -2; dy <= 2; dy += 1) {
      for (let dx = -2; dx <= 2; dx += 1) {
        const u = bx + dx;
        const v = by + dy;
        if (u >= 0 && u < MW && v >= 0 && v < MH) m.terrain[v * MW + u] = T.DIRT;
      }
    }
  }
}

// 시드를 1씩 올리며 두 시작점이 이어질 때까지 다시 만든다.
// 재시도가 필요하다는 것 자체가 명세의 일부다 — 다이아몬드-스퀘어는
// 가끔 두 기지 사이를 물로 끊어 놓는다.
export function genStart(seed0 = 3): [T.TMap, number, number] {
  let seed = seed0;
  let retries = 0;
  for (;;) {
    const rand = new LCG(seed);
    const m = new T.TMap(MW, MH);
    const h = diamondSquare(rand);
    for (let y = 0; y < MH; y += 1) {
      for (let x = 0; x < MW; x += 1) m.terrain[y * MW + x] = terrainOf(h[y][x]);
    }
    symmetrize(m);
    const [pts] = placeOre(m, rand);
    clearBase(m);
    for (let i = 0; i < MW * MH; i += 1) m.repass(i);
    m.bump();
    m.starts = START.map((p) => [p[0], p[1]] as [number, number]);
    const lab = m.labels(0);
    const a = lab[m.idx(START[0][0], START[0][1])];
    const b = lab[m.idx(START[1][0], START[1][1])];
    if (a === b && a >= 0) {
      LAST_ORE = pts;
      return [m, seed, retries];
    }
    seed += 1;
    retries += 1;
  }
}
