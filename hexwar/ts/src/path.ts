// 이동 범위와 경로 — SPEC §6

import * as H from './hexcoord';
import { HexMap, NEIGHBOR_DELTA, T_MOVE, TERRAIN_MASK } from './hexmap';
import { NO_UNIT, Unit, UnitPool } from './units';

export const UNREACHED = 0x7fffffff;
export const MIN_COST = 1;

// 이웃 조회용 스크래치 버퍼. 한 번만 만들어 돌려 쓴다 — 이 루프에서
// 배열을 새로 할당하면 GC 가 프레임을 먹는다.
const NBD = new Int32Array(6);
const NBI = new Int32Array(6);

export function zocMask(m: HexMap, pool: UnitPool, side: number): Uint8Array {
  const mask = new Uint8Array(m.n);
  for (const uid of pool.aliveIds()) {
    const u = pool.get(uid)!;
    if (u.side === side) continue;
    const i = m.axialIdx(u.q, u.r);
    if (i < 0) continue;
    const k = m.neighborsWithDir(i, NBD, NBI);
    for (let j = 0; j < k; j++) mask[NBI[j]!] = 1;
  }
  return mask;
}

export function stepCost(m: HexMap, _pool: UnitPool, _side: number,
                         frm: number, to: number): number {
  const c = m.cells[to]!;
  const mv = T_MOVE[c & TERRAIN_MASK]!;
  if (mv < 0) return -1;
  if (m.occupant[to]! !== NO_UNIT) return -1;
  if ((m.cells[frm]! & 0x80) !== 0 && (c & 0x80) !== 0) return 1;
  return mv;
}

export class Reach {
  constructor(readonly cost: Map<number, number>,
              readonly came: Map<number, number>,
              readonly list: number[]) {}

  has(i: number): boolean { return this.cost.has(i); }
}

// Dial 의 양동이 큐 — O(V + E + maxMP)
export function reachable(m: HexMap, pool: UnitPool, unit: Unit): Reach {
  const start = m.axialIdx(unit.q, unit.r);
  const budget = unit.mp;
  if (start < 0) return new Reach(new Map(), new Map(), []);
  if (budget <= 0) {
    return new Reach(new Map([[start, 0]]), new Map([[start, -1]]), [start]);
  }

  const best = new Int32Array(m.n).fill(UNREACHED);
  const came = new Int32Array(m.n).fill(-1);
  best[start] = 0;
  const zoc = zocMask(m, pool, unit.side);
  const buckets: number[][] = [];
  for (let c = 0; c <= budget; c++) buckets.push([]);
  buckets[0]!.push(start);

  for (let c = 0; c <= budget; c++) {
    const b = buckets[c]!;
    for (let bi = 0; bi < b.length; bi++) {
      const cur = b[bi]!;
      if (best[cur]! !== c) continue;            // 더 싼 길로 이미 갱신됨
      if (cur !== start && zoc[cur] === 1) continue;   // ZOC 에 들어가면 끝
      const k = m.neighborsWithDir(cur, NBD, NBI);
      for (let j = 0; j < k; j++) {
        const ni = NBI[j]!;
        const sc = stepCost(m, pool, unit.side, cur, ni);
        if (sc < 0) continue;
        const nc = c + sc;
        if (nc <= budget && nc < best[ni]!) {
          best[ni] = nc;
          came[ni] = NBD[j]!;
          buckets[nc]!.push(ni);
        }
      }
    }
  }

  const cost = new Map<number, number>();
  const came2 = new Map<number, number>();
  const list: number[] = [];
  for (let i = 0; i < m.n; i++) {
    if (best[i]! !== UNREACHED) {
      cost.set(i, best[i]!);
      came2.set(i, came[i]!);
      list.push(i);
    }
  }
  return new Reach(cost, came2, list);
}

export function tracePath(m: HexMap, reach: Reach, target: number): number[] {
  if (!reach.has(target)) return [];
  const path = [target];
  let cur = target;
  for (;;) {
    const d = reach.came.get(cur)!;
    if (d < 0) break;
    const row = Math.floor(cur / m.w);
    let col = cur - row * m.w;
    const back = NEIGHBOR_DELTA[row & 1]![(d + 3) % 6]!;
    col += back[0];
    cur = (row + back[1]) * m.w + col;
    path.push(cur);
  }
  path.reverse();
  return path;
}

// A* — 이진 힙. 동점은 삽입 순번으로 깨서 세 언어의 답이 갈리지 않게 한다.
interface HeapNode { f: number; ord: number; idx: number; }

function heapPush(h: HeapNode[], node: HeapNode): void {
  h.push(node);
  let i = h.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    const a = h[i]!, b = h[p]!;
    if (a.f < b.f || (a.f === b.f && a.ord < b.ord)) {
      h[i] = b; h[p] = a; i = p;
    } else break;
  }
}

function heapPop(h: HeapNode[]): HeapNode {
  const top = h[0]!;
  const last = h.pop()!;
  if (h.length > 0) {
    h[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = 2 * i + 2;
      let s = i;
      if (l < h.length && (h[l]!.f < h[s]!.f || (h[l]!.f === h[s]!.f && h[l]!.ord < h[s]!.ord))) s = l;
      if (r < h.length && (h[r]!.f < h[s]!.f || (h[r]!.f === h[s]!.f && h[r]!.ord < h[s]!.ord))) s = r;
      if (s === i) break;
      const t = h[i]!; h[i] = h[s]!; h[s] = t; i = s;
    }
  }
  return top;
}

export function astar(m: HexMap, pool: UnitPool, side: number,
                      start: number, goal: number): number[] {
  if (start === goal) return [start];
  const [gq, gr] = m.idxAxial(goal);
  const g = new Int32Array(m.n).fill(UNREACHED);
  const came = new Int32Array(m.n).fill(-1);
  g[start] = 0;
  let order = 0;
  const [sq, sr] = m.idxAxial(start);
  const heap: HeapNode[] = [];
  heapPush(heap, { f: H.distance(sq, sr, gq, gr) * MIN_COST, ord: 0, idx: start });
  const closed = new Uint8Array(m.n);

  while (heap.length > 0) {
    const cur = heapPop(heap).idx;
    if (closed[cur] === 1) continue;
    closed[cur] = 1;
    if (cur === goal) break;
    const k = m.neighborsWithDir(cur, NBD, NBI);
    for (let j = 0; j < k; j++) {
      const ni = NBI[j]!;
      if (closed[ni] === 1) continue;
      const sc = stepCost(m, pool, side, cur, ni);
      if (sc < 0) continue;
      const ng = g[cur]! + sc;
      if (ng < g[ni]!) {
        g[ni] = ng;
        came[ni] = cur;
        const [nq, nr] = m.idxAxial(ni);
        order++;
        heapPush(heap, { f: ng + H.distance(nq, nr, gq, gr) * MIN_COST, ord: order, idx: ni });
      }
    }
  }

  if (g[goal]! === UNREACHED) return [];
  const out = [goal];
  while (out[out.length - 1]! !== start) out.push(came[out[out.length - 1]!]!);
  out.reverse();
  return out;
}
