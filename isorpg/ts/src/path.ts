// 경로 탐색 — SPEC §8. 8방향 격자, 다익스트라(양동이 큐), A*(옥타일).
//
// 파이썬은 '아직 값이 없음'을 None 으로 적는다. TS 에서 (number | null)[] 로 옮기면
// 안쪽 루프마다 널 검사가 생겨 형이 바뀌고 느려지므로, -1 을 미도달 표식으로 쓰고
// Int32Array 에 담는다. 비용은 최대 몇천이라 int32 안에 넉넉히 들어간다.
import * as M from './gamemap';
import type { GameMap } from './gamemap';

//                       E  SE  S  SW  W  NW  N  NE
export const DIRX: number[] = [1, 1, 0, -1, -1, -1, 0, 1];
export const DIRY: number[] = [0, 1, 1, 1, 0, -1, -1, -1];
export const DIAG: boolean[] = [false, true, false, true, false, true, false, true];
export const STEP_BASE: number[] = [10, 14, 10, 14, 10, 14, 10, 14];
export const DIR_NAME: string[] = ['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE'];
export const CLIMB_MAX = 1;
export const MIN_MOVE = M.MIN_MOVE; // 8 (ROAD)
export const BUCKET_N = 64; // 최대 간선 비용 floordiv(14*20,10)=28 보다 크면 된다

/** 미도달 표식. 파이썬의 None 자리다. */
export const UNREACHED = -1;

export function passable(m: GameMap, x: number, y: number): boolean {
  return m.inside(x, y) && (M.MOVE[m.terrain(x, y)] as number) > 0;
}

/** (x,y) 에서 방향 d 로 한 칸 갈 수 있는가.
 *
 *  마지막 조건이 '모서리 자르기 금지'다. 벽 두 장이 만나는 모서리를
 *  대각선으로 스쳐 지나가면 캐릭터가 벽을 뚫은 것처럼 보인다. */
export function stepOk(m: GameMap, x: number, y: number, d: number): boolean {
  const nx = x + (DIRX[d] as number);
  const ny = y + (DIRY[d] as number);
  if (!passable(m, nx, ny)) return false;
  const dh = m.height(nx, ny) - m.height(x, y);
  if (dh > CLIMB_MAX || dh < -CLIMB_MAX) return false;
  if (DIAG[d]) {
    if (!passable(m, nx, y) || !passable(m, x, ny)) return false;
  }
  return true;
}

/** 도착 칸의 지형으로 값을 매긴다. 떠나는 칸이 아니라. */
export function stepCost(m: GameMap, nx: number, ny: number, d: number): number {
  return Math.floor(((STEP_BASE[d] as number) * (M.MOVE[m.terrain(nx, ny)] as number)) / 10);
}

export const STRAIGHT_MIN = Math.floor((10 * MIN_MOVE) / 10); // 8
export const DIAG_MIN = Math.floor((14 * MIN_MOVE) / 10); // 11

/** 가장 싼 지형만 밟았을 때의 정확한 8방향 최단거리. (정리 8.1, 8.2)
 *
 *  흔히 쓰는 floordiv((10*(dx+dy) - 6*min) * 8, 10) 형태는 쓰지 않는다.
 *  내림이 두 번 들어가 (47,47) 에서 526 을 내놓는데 실제 최소 비용은 517 이다. */
export function octile(ax: number, ay: number, bx: number, by: number): number {
  let dx = ax - bx;
  if (dx < 0) dx = -dx;
  let dy = ay - by;
  if (dy < 0) dy = -dy;
  const hi = dx < dy ? dy : dx;
  const lo = dx < dy ? dx : dy;
  return STRAIGHT_MIN * hi + (DIAG_MIN - STRAIGHT_MIN) * lo;
}

/** 원형 양동이 큐. 간선 비용이 [0, BUCKET_N) 이면 이진 힙과 같은 순서를 준다. (정리 8.3)
 *
 *  비지 않은 첫 양동이의 **마지막** 원소를 꺼낸다 — 스택 방식이라 동점 처리가
 *  결정적이다. 파이썬의 list.pop() 과 JS 의 Array.pop() 이 같은 동작이라 그대로 옮았다. */
export class Bucket {
  private b: Array<Array<[number, number]>> = [];
  private cur = 0;
  private n = 0;

  constructor() {
    for (let i = 0; i < BUCKET_N; i++) this.b.push([]);
  }

  push(key: number, node: number): void {
    (this.b[key % BUCKET_N] as Array<[number, number]>).push([key, node]);
    this.n += 1;
  }

  popMin(): [number, number] | null {
    if (this.n === 0) return null;
    for (let i = 0; i < BUCKET_N; i++) {
      const q = this.b[this.cur] as Array<[number, number]>;
      if (q.length > 0) {
        this.n -= 1;
        return q.pop() as [number, number];
      }
      this.cur = (this.cur + 1) % BUCKET_N;
    }
    return null;
  }
}

/** 시작점에서 모든 칸까지의 최소 비용. 못 가는 칸은 UNREACHED(-1). */
export function dijkstra(m: GameMap, sx: number, sy: number): Int32Array {
  const w = m.w;
  const dist = new Int32Array(w * m.h).fill(UNREACHED);
  if (!passable(m, sx, sy)) return dist;
  dist[sy * w + sx] = 0;
  const q = new Bucket();
  q.push(0, sy * w + sx);
  for (;;) {
    const it = q.popMin();
    if (it === null) break;
    const g = it[0];
    const idx = it[1];
    const cur = dist[idx] as number;
    if (cur !== UNREACHED && g > cur) continue;
    const x = idx % w;
    const y = Math.floor(idx / w);
    for (let d = 0; d < 8; d++) {
      if (!stepOk(m, x, y, d)) continue;
      const nx = x + (DIRX[d] as number);
      const ny = y + (DIRY[d] as number);
      const ng = g + stepCost(m, nx, ny, d);
      const ni = ny * w + nx;
      const dn = dist[ni] as number;
      if (dn === UNREACHED || ng < dn) {
        dist[ni] = ng;
        q.push(ng, ni);
      }
    }
  }
  return dist;
}

export interface AstarResult {
  path: Array<[number, number]> | null;
  cost: number;          // 못 가면 UNREACHED
  expanded: number;
}

/** f = g + h 를 같은 양동이 큐에 넣는다. h 가 일관적이므로 f 는 경로를 따라
 *  단조 증가하고 한 걸음에 최대 28 늘어난다 — 활성 폭이 BUCKET_N 미만이다. */
export function astar(
  m: GameMap, sx: number, sy: number, gx: number, gy: number,
): AstarResult {
  const w = m.w;
  if (!passable(m, sx, sy) || !passable(m, gx, gy)) {
    return { path: null, cost: UNREACHED, expanded: 0 };
  }
  const gcost = new Int32Array(w * m.h).fill(UNREACHED);
  const prev = new Int32Array(w * m.h).fill(-1);
  const closed = new Uint8Array(w * m.h);
  const si = sy * w + sx;
  const gi = gy * w + gx;
  gcost[si] = 0;
  const q = new Bucket();
  q.push(octile(sx, sy, gx, gy), si);
  let expanded = 0;
  for (;;) {
    const it = q.popMin();
    if (it === null) return { path: null, cost: UNREACHED, expanded };
    const idx = it[1];
    if (closed[idx]) continue;
    closed[idx] = 1;
    expanded += 1;
    if (idx === gi) break;
    const x = idx % w;
    const y = Math.floor(idx / w);
    const g = gcost[idx] as number;
    for (let d = 0; d < 8; d++) {
      if (!stepOk(m, x, y, d)) continue;
      const nx = x + (DIRX[d] as number);
      const ny = y + (DIRY[d] as number);
      const ni = ny * w + nx;
      if (closed[ni]) continue;
      const ng = g + stepCost(m, nx, ny, d);
      const cn = gcost[ni] as number;
      if (cn === UNREACHED || ng < cn) {
        gcost[ni] = ng;
        prev[ni] = idx;
        q.push(ng + octile(nx, ny, gx, gy), ni);
      }
    }
  }
  const pathOut: Array<[number, number]> = [];
  let i = gi;
  while (i !== -1) {
    pathOut.push([i % w, Math.floor(i / w)]);
    i = prev[i] as number;
  }
  pathOut.reverse();
  return { path: pathOut, cost: gcost[gi] as number, expanded };
}
