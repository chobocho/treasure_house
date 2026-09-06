// 흐름장·클리어런스·브러시파이어 (SPEC §11).
//
//    A* 는 "한 유닛이 한 목표로" 가는 도구다. 무리 40기가 같은 깃발로 몰려갈 때
//    A* 를 40번 부르는 것은 같은 답을 40번 계산하는 것이다. 적분장은 반대로
//    목표에서 한 번 거꾸로 퍼뜨려 두고, 유닛은 자기 칸의 방향 하나만 읽는다.
//
//    여기의 모든 장은 **지형만** 본다. 점유 비트를 넣으면 유닛이 움직일 때마다
//    장을 다시 깔아야 하고, 그러면 애초에 장을 쓰는 이유가 없어진다.

import * as F from './fixed';
import { TMap } from './tmap';

export const INF = 65535;            // SPEC §11.1 — 세 언어가 같은 수를 찍어야 한다
export const NB = F.D_DIAG + 1;      // 양동이 15개 (§8.4 와 같은 이유)
export const STOP = 255;

// 다중 시작점 다익스트라. seeds 는 (칸번호, 초기비용) 목록.
// O(칸수 × 8) 시간, O(칸수) 공간. 간선 비용이 10 과 14 둘뿐이라
// 원형 양동이 15개로 힙 없이 돈다 — 정리 8.3 이 그대로 적용된다.
function dial(m: TMap, kind: number,
              seeds: Array<[number, number]>): number[] {
  const w = m.w;
  const h = m.h;
  const dist = new Array<number>(w * h).fill(INF);
  const buckets: number[][] = [];
  for (let k = 0; k < NB; k += 1) buckets.push([]);
  let pending = 0;
  let lo = INF;
  for (const [i, c] of seeds) {
    if (c < dist[i]) {
      dist[i] = c;
      buckets[F.fmod(c, NB)].push(i);
      pending += 1;
      if (c < lo) lo = c;
    }
  }
  if (pending === 0) return dist;
  let cur = lo;
  while (pending > 0) {
    let b = buckets[F.fmod(cur, NB)];
    while (b.length === 0) {
      cur += 1;
      b = buckets[F.fmod(cur, NB)];
    }
    const p = b.pop() as number;
    pending -= 1;
    if (dist[p] !== cur) continue;   // 낡은 항목 — 감소키는 만들지 않는다
    const x = F.fmod(p, w);
    const y = F.floordiv(p, w);
    for (let d = 0; d < 8; d += 1) {
      const u = x + F.DX[d];
      const v = y + F.DY[d];
      if (!m.passableTerrain(u, v, kind)) continue;  // 통행 가능 칸으로만
      const nd = cur + F.DCOST[d];
      const j = v * w + u;
      if (nd < dist[j]) {
        dist[j] = nd;
        buckets[F.fmod(nd, NB)].push(j);
        pending += 1;
      }
    }
  }
  return dist;
}

// ── SPEC §11.1 적분장 ───────────────────────────────────────────────────────
// 목표 집합에서 거꾸로 퍼뜨린 비용장. 도달 불가는 INF.
// 막힌 목표는 무시한다(§11.1). 닿을 수 없는 칸을 0 으로 심으면 장 전체가
// 그쪽으로 기울고, 그것은 §8.6 의 대체 목표가 맡을 몫이다.
export function integration(m: TMap, kind: number,
                            goals: Array<[number, number]>): number[] {
  const seeds: Array<[number, number]> = [];
  for (const [x, y] of goals) {
    if (m.passableTerrain(x, y, kind)) seeds.push([y * m.w + x, 0]);
  }
  return dial(m, kind, seeds);
}

// ── SPEC §11.2 경사장 ───────────────────────────────────────────────────────
// 각 칸에서 갈 방향. 후보가 없으면 255(정지).
// 동점은 **방향 번호가 작은 쪽**이다. 언어별 min 구현에 맡기면 대칭 맵에서
// 무리가 좌우로 갈리고, 그 갈림은 PPM 바이트 비교에서 바로 잡힌다.
export function flowDirs(m: TMap, kind: number, integ: number[]): number[] {
  const w = m.w;
  const h = m.h;
  const out = new Array<number>(w * h).fill(STOP);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const i = y * w + x;
      if (integ[i] >= INF || !m.passableTerrain(x, y, kind)) continue;
      let best = INF;
      let bd = STOP;
      for (let d = 0; d < 8; d += 1) {
        const u = x + F.DX[d];
        const v = y + F.DY[d];
        if (!m.passableTerrain(u, v, kind)) continue;
        const c = integ[v * w + u];
        if (c < best) {              // 등호를 빼면 작은 d 가 이긴다
          best = c;
          bd = d;
        }
      }
      out[i] = bd;
    }
  }
  return out;
}

// ── SPEC §11.3 클리어런스 ───────────────────────────────────────────────────
// clear[i] = (x,y) 를 좌상단으로 하는 통행 가능 정사각형의 최대 변 (정리 11.1).
// O(칸수) 시간, O(칸수) 공간 — 오른쪽 아래에서 한 번만 훑는다.
// 맵 밖은 0 이므로 오른쪽·아래 가장자리의 자유 칸은 1 이 된다.
export function clearance(m: TMap, kind: number): number[] {
  const w = m.w;
  const h = m.h;
  const c = new Array<number>(w * h).fill(0);
  for (let y = h - 1; y >= 0; y -= 1) {
    for (let x = w - 1; x >= 0; x -= 1) {
      if (!m.passableTerrain(x, y, kind)) continue;
      if (x + 1 >= w || y + 1 >= h) {
        c[y * w + x] = 1;
      } else {
        const r = c[y * w + x + 1];
        const d = c[(y + 1) * w + x];
        const q = c[(y + 1) * w + x + 1];
        c[y * w + x] = 1 + Math.min(r, d, q);
      }
    }
  }
  return c;
}

// 크기 size 인 유닛이 (x,y) 를 좌상단으로 설 수 있는가.
export function sizePassable(clear: number[], m: TMap, x: number, y: number,
                             size: number): boolean {
  if (!m.inMap(x, y)) return false;
  return clear[y * m.w + x] >= size;
}

// ── SPEC §11.4 브러시파이어 ─────────────────────────────────────────────────
// 가장 가까운 막힌 칸까지의 옥타일 비용. 막힌 칸은 0.
// 맵 밖도 막힌 칸이다(§4.2 의 terrain_at 규약). 그래서 가장자리 자유 칸은
// 10 이고, AI 는 맵 끝에 건물을 붙이지 않는다(§17.4).
export function brushfire(m: TMap, kind: number): number[] {
  const w = m.w;
  const h = m.h;
  const seeds: Array<[number, number]> = [];
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      if (!m.passableTerrain(x, y, kind)) {
        seeds.push([y * w + x, 0]);
        continue;
      }
      let best = INF;
      for (let d = 0; d < 8; d += 1) {   // 맵 밖 이웃은 비용 0 짜리 시작점이다
        if (!m.inMap(x + F.DX[d], y + F.DY[d])) {
          if (F.DCOST[d] < best) best = F.DCOST[d];
        }
      }
      if (best < INF) seeds.push([y * w + x, best]);
    }
  }
  return dial(m, kind, seeds);
}
