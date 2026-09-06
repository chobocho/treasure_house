// 경로 탐색 — BFS·다익스트라(양동이 큐)·A*(이진 힙) (SPEC §8).
//
//    코너 컷은 **허용한다**. 대각 이동은 도착 칸만 본다. 선택이며, 그 이유와
//    대가는 SPEC §8.1 에 적어 두었다 — 요약하면 JPS 의 가지치기 규칙이
//    코너 컷 격자 위에서 정의되어 있기 때문이다.
//
//    경로 탐색은 점유 비트를 보지 않는다(SPEC §4.3). 움직이는 유닛 때문에
//    경로가 매 틱 흔들리면 무리 이동이 통째로 무너진다.

import * as F from './fixed';
import { TMap } from './tmap';

export const INF = 1073741824;              // 1 << 30 — 시프트는 쓰지 않는다
export const NB = F.D_DIAG + 1;             // 양동이 15개 — 최대 간선 비용보다 커야 한다

// 옥타일 휴리스틱 = 10*max + 4*min. 허용적이고 일관적이다 (정리 8.1/8.2).
export function hOct(ax: number, ay: number, bx: number, by: number): number {
  return F.doct(ax - bx, ay - by);
}

// (방향, u, v) — 코너 컷 허용이므로 도착 칸만 검사한다.
export function neighbours(m: TMap, x: number, y: number,
                           kind: number): Array<[number, number, number]> {
  const out: Array<[number, number, number]> = [];
  for (let d = 0; d < 8; d += 1) {
    const u = x + F.DX[d];
    const v = y + F.DY[d];
    if (m.passableTerrain(u, v, kind)) out.push([d, u, v]);
  }
  return out;
}

// ── BFS ─────────────────────────────────────────────────────────────────────
// 걸음 수(가중치 없음). 대각도 한 걸음이다.
export function bfs(m: TMap, kind: number, s: [number, number],
                    t: [number, number]): number {
  if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind))) return -1;
  const w = m.w;
  const seen = new Array<number>(w * m.h).fill(-1);
  const si = s[1] * w + s[0];
  seen[si] = 0;
  const q: number[] = [si];
  let head = 0;
  while (head < q.length) {
    const p = q[head];
    head += 1;
    const x = F.fmod(p, w);
    const y = F.floordiv(p, w);
    if (x === t[0] && y === t[1]) return seen[p];
    for (let d = 0; d < 8; d += 1) {
      const u = x + F.DX[d];
      const v = y + F.DY[d];
      if (!m.passableTerrain(u, v, kind)) continue;
      const j = v * w + u;
      if (seen[j] < 0) {
        seen[j] = seen[p] + 1;
        q.push(j);
      }
    }
  }
  return -1;
}

// ── SPEC §8.4 다익스트라 (Dial 양동이 큐) ───────────────────────────────────
// 모든 칸까지의 비용 배열. 간선 비용이 10 과 14 뿐이라 힙이 필요 없다.
// 정리 8.3 이 보장한다 — 처리 중인 거리 cur 와 새 거리 nd 는 항상
// cur <= nd < cur + 15 이므로 원형 양동이 15개면 충돌하지 않는다.
export function dijkstra(m: TMap, kind: number, starts: number[],
                         goal?: number): number[] {
  const w = m.w;
  const h = m.h;
  const dist = new Array<number>(w * h).fill(INF);
  const buckets: number[][] = [];
  for (let k = 0; k < NB; k += 1) buckets.push([]);
  let pending = 0;
  for (const s of starts) {
    if (dist[s] > 0) {
      dist[s] = 0;
      buckets[0].push(s);
      pending += 1;
    }
  }
  let cur = 0;
  while (pending > 0) {
    let b = buckets[F.fmod(cur, NB)];
    while (b.length === 0) {
      cur += 1;
      b = buckets[F.fmod(cur, NB)];
    }
    const p = b.pop() as number;
    pending -= 1;
    if (dist[p] !== cur) continue;    // 낡은 항목 — 감소키를 구현하지 않는다
    if (goal !== undefined && p === goal) return dist;
    const x = F.fmod(p, w);
    const y = F.floordiv(p, w);
    for (let d = 0; d < 8; d += 1) {
      const u = x + F.DX[d];
      const v = y + F.DY[d];
      if (!m.passableTerrain(u, v, kind)) continue;
      const j = v * w + u;
      const nd = cur + F.DCOST[d];
      if (nd < dist[j]) {
        dist[j] = nd;
        buckets[F.fmod(nd, NB)].push(j);
        pending += 1;
      }
    }
  }
  return dist;
}

// ── SPEC §8.5 A* (손으로 쓴 이진 힙) ────────────────────────────────────────
// (f, h, idx) 사전식 최소 힙.
//
//   파이썬 heapq · 루아 table.sort · 자바스크립트 Array.sort 는 서로 다른
//   순서를 낼 수 있다. 비교자가 전순서이기만 하면 손으로 쓴 힙이 세 언어에서
//   같은 순서로 뽑는다 — 그래서 손으로 쓴다.
export class Heap {
  a: Array<[number, number, number]>;

  constructor() {
    this.a = [];
  }

  get length(): number {
    return this.a.length;
  }

  private static less(x: [number, number, number],
                      y: [number, number, number]): boolean {
    if (x[0] !== y[0]) return x[0] < y[0];
    if (x[1] !== y[1]) return x[1] < y[1];
    return x[2] < y[2];
  }

  private static le(x: [number, number, number],
                    y: [number, number, number]): boolean {
    return !Heap.less(y, x);
  }

  push(f: number, hh: number, idx: number): void {
    const a = this.a;
    a.push([f, hh, idx]);
    let i = a.length - 1;
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (Heap.le(a[p], a[i])) break;
      const tmp = a[p];
      a[p] = a[i];
      a[i] = tmp;
      i = p;
    }
  }

  pop(): [number, number, number] {
    const a = this.a;
    const top = a[0];
    const last = a.pop() as [number, number, number];
    if (a.length > 0) {
      a[0] = last;
      let i = 0;
      const n = a.length;
      for (;;) {
        const l = 2 * i + 1;
        const r = 2 * i + 2;
        let s = i;
        if (l < n && Heap.less(a[l], a[s])) s = l;
        if (r < n && Heap.less(a[r], a[s])) s = r;
        if (s === i) break;
        const tmp = a[s];
        a[s] = a[i];
        a[i] = tmp;
        i = s;
      }
    }
    return top;
  }
}

// (비용, 경로 타일 목록, 연 노드 수). 도달 불가면 (-1, [], n).
export function astar(m: TMap, kind: number, s: [number, number],
                      t: [number, number]): [number, number[], number] {
  const w = m.w;
  if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind))) return [-1, [], 0];
  const si = s[1] * w + s[0];
  const ti = t[1] * w + t[0];
  const dist = new Map<number, number>();
  dist.set(si, 0);
  const prev = new Map<number, number>();
  const closed = new Set<number>();
  const heap = new Heap();
  const h0 = hOct(s[0], s[1], t[0], t[1]);
  heap.push(h0, h0, si);
  let expanded = 0;
  while (heap.length > 0) {
    const p = heap.pop()[2];
    if (closed.has(p)) continue;
    closed.add(p);                      // 일관적이므로 재개방하지 않는다
    expanded += 1;
    if (p === ti) {
      const out = [p];
      while (out[out.length - 1] !== si) {
        out.push(prev.get(out[out.length - 1]) as number);
      }
      out.reverse();
      return [dist.get(p) as number, out, expanded];
    }
    const x = F.fmod(p, w);
    const y = F.floordiv(p, w);
    const dp = dist.get(p) as number;
    for (let d = 0; d < 8; d += 1) {
      const u = x + F.DX[d];
      const v = y + F.DY[d];
      if (!m.passableTerrain(u, v, kind)) continue;
      const j = v * w + u;
      const nd = dp + F.DCOST[d];
      const old = dist.has(j) ? (dist.get(j) as number) : INF;
      if (nd < old) {
        dist.set(j, nd);
        prev.set(j, p);
        const hn = hOct(u, v, t[0], t[1]);
        heap.push(nd + hn, hn, j);
      }
    }
  }
  return [-1, [], expanded];
}

// ── SPEC §8.6 도달 불가 목표 ────────────────────────────────────────────────
// 목표가 다른 성분이면 같은 성분에서 목표에 가장 가까운 칸으로 바꾼다.
// 이 한 줄이 없으면 '섬 건너편 클릭' 한 번이 A* 에게 맵 전체를 펴게 한다.
export function closestReachable(m: TMap, kind: number, s: [number, number],
                                 t: [number, number]): [number, number] | null {
  const lab = m.labels(kind);
  const si = s[1] * m.w + s[0];
  const ti = t[1] * m.w + t[0];
  if (lab[si] < 0) return null;
  if (lab[ti] === lab[si]) return t;
  let best: [number, number] | null = null;
  let bd = INF;
  let bi = INF;
  for (let i = 0; i < m.w * m.h; i += 1) {
    if (lab[i] !== lab[si]) continue;
    const x = F.fmod(i, m.w);
    const y = F.floordiv(i, m.w);
    const d = F.d83(x - t[0], y - t[1]);
    if (d < bd || (d === bd && i < bi)) {
      best = [x, y];
      bd = d;
      bi = i;
    }
  }
  return best;
}

// ── SPEC §8.7 경로 캐시 ─────────────────────────────────────────────────────
// 64칸 LRU. 지형이 바뀌면 통째로 비운다 — 낡은 경로는 곧 디싱크다.
// LRU 순서는 상태가 아니다(해시에 넣지 않는다). 캐시는 같은 답을 더 빨리
// 줄 뿐이고, 다른 답을 주면 그것은 버그다.
export class Cache {
  static LIMIT = 64;
  mapVersion: number;
  data: Map<number, [number, number[]]>;
  order: number[];
  hits: number;
  misses: number;

  constructor() {
    this.mapVersion = -1;
    this.data = new Map<number, [number, number[]]>();
    this.order = [];
    this.hits = 0;
    this.misses = 0;
  }

  get(m: TMap, key: number): [number, number[]] | null {
    if (m.version !== this.mapVersion) {
      this.mapVersion = m.version;
      this.data = new Map<number, [number, number[]]>();
      this.order = [];
    }
    const hit = this.data.get(key);
    if (hit !== undefined) {
      this.hits += 1;
      this.order.splice(this.order.indexOf(key), 1);
      this.order.push(key);
      return hit;
    }
    this.misses += 1;
    return null;
  }

  put(key: number, value: [number, number[]]): void {
    if (this.data.has(key)) {
      this.order.splice(this.order.indexOf(key), 1);
    } else if (this.order.length >= Cache.LIMIT) {
      this.data.delete(this.order.shift() as number);
    }
    this.data.set(key, value);
    this.order.push(key);
  }
}

// 캐시를 거치는 표준 경로 질의. 목표가 닿지 않으면 대체 목표로 바꾼다.
export function find(m: TMap, kind: number, s: [number, number],
                     t: [number, number],
                     cache?: Cache | null): [number, number[]] {
  const goal = closestReachable(m, kind, s, t);
  if (goal === null) return [-1, []];
  const key = ((s[1] * m.w + s[0]) * 4096 + (goal[1] * m.w + goal[0])) * 2 + kind;
  if (cache !== undefined && cache !== null) {
    const hit = cache.get(m, key);
    if (hit !== null) return hit;
  }
  const [cost, tiles] = astar(m, kind, s, goal);
  if (cache !== undefined && cache !== null) cache.put(key, [cost, tiles]);
  return [cost, tiles];
}
