// 그리기 순서 — SPEC §6. 화가 알고리즘을 DAG 로 푼다.
//
// 파이썬은 heapq 에 (depth_key 튜플, 인덱스) 를 그대로 넣는다. JS 에는 튜플
// 비교도 표준 힙도 없으므로 이진 힙을 직접 만든다. 다만 depth_key 의 마지막
// 성분이 id 라 키가 전부 서로 다르고, 그래서 어떤 힙 구현을 써도 방출 순서가
// 같다 — 세 언어가 각자의 힙을 써도 되는 이유이자, 이 포트가 성립하는 근거다.
import { HH, HW, TZ } from './proj';

// 상자 = [id, x0, y0, z0, x1, y1, z1]. 전부 반개구간 [a, b).
export type Box = number[];

export const I_ID = 0;
export const I_X0 = 1;
export const I_Y0 = 2;
export const I_Z0 = 3;
export const I_X1 = 4;
export const I_Y1 = 5;
export const I_Z1 = 6;

export type BBox = [number, number, number, number];

/** 상자의 화면 경계상자 [minx, miny, maxx, maxy]. 여덟 꼭짓점을 다 투영한다 —
 *  네 값만 골라 쓰면 왜 그 값인지가 코드에서 사라진다. 상자 하나에 여덟 번은 싸다. */
export function boxBbox(b: Box): BBox {
  let minx = 1073741824;
  let miny = 1073741824;
  let maxx = -1073741824;
  let maxy = -1073741824;
  const xs = [b[I_X0] as number, b[I_X1] as number];
  const ys = [b[I_Y0] as number, b[I_Y1] as number];
  const zs = [b[I_Z0] as number, b[I_Z1] as number];
  for (const x of xs) {
    for (const y of ys) {
      for (const z of zs) {
        const sx = HW * (x - y);
        const sy = HH * (x + y) - z * TZ;
        if (sx < minx) minx = sx;
        if (sx > maxx) maxx = sx;
        if (sy < miny) miny = sy;
        if (sy > maxy) maxy = sy;
      }
    }
  }
  return [minx, miny, maxx, maxy];
}

export function bboxOverlap(a: BBox, b: BBox): boolean {
  return !(a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1]);
}

/** a 를 b 보다 먼저 그려야 하는가. 셋 중 하나만 성립해도 참이다.
 *  이 느슨함이 화면에서는 대개 옳지만 반대칭이 아니어서 순환을 만든다. */
export function behind(a: Box, b: Box): boolean {
  return (a[I_X1] as number) <= (b[I_X0] as number)
    || (a[I_Y1] as number) <= (b[I_Y0] as number)
    || (a[I_Z1] as number) <= (b[I_Z0] as number);
}

/** 동점을 가르는 기준 [x0+y0, z0, id]. id 가 마지막에 들어가 완전히 결정적이다. */
export function depthKey(b: Box): [number, number, number] {
  return [(b[I_X0] as number) + (b[I_Y0] as number), b[I_Z0] as number, b[I_ID] as number];
}

function keyLess(a: [number, number, number], b: [number, number, number]): boolean {
  if (a[0] !== b[0]) return a[0] < b[0];
  if (a[1] !== b[1]) return a[1] < b[1];
  return a[2] < b[2];
}

/** depth_key 오름차순 이진 힙. 원소는 [키, 노드 인덱스].
 *  키가 서로 다르므로 인덱스까지 비교할 일은 실제로 생기지 않지만,
 *  전순서를 완성해 두는 편이 나중에 상자를 늘렸을 때 사고를 막는다. */
class KeyHeap {
  private ks: Array<[number, number, number]> = [];
  private vs: number[] = [];

  get size(): number {
    return this.vs.length;
  }

  private less(i: number, j: number): boolean {
    const a = this.ks[i] as [number, number, number];
    const b = this.ks[j] as [number, number, number];
    if (keyLess(a, b)) return true;
    if (keyLess(b, a)) return false;
    return (this.vs[i] as number) < (this.vs[j] as number);
  }

  private swap(i: number, j: number): void {
    const tk = this.ks[i] as [number, number, number];
    this.ks[i] = this.ks[j] as [number, number, number];
    this.ks[j] = tk;
    const tv = this.vs[i] as number;
    this.vs[i] = this.vs[j] as number;
    this.vs[j] = tv;
  }

  push(k: [number, number, number], v: number): void {
    this.ks.push(k);
    this.vs.push(v);
    let i = this.vs.length - 1;
    while (i > 0) {
      const p = Math.floor((i - 1) / 2);
      if (!this.less(i, p)) break;
      this.swap(i, p);
      i = p;
    }
  }

  pop(): number {
    const top = this.vs[0] as number;
    const last = this.vs.length - 1;
    this.swap(0, last);
    this.ks.pop();
    this.vs.pop();
    let i = 0;
    const n = this.vs.length;
    for (;;) {
      const l = 2 * i + 1;
      const r = l + 1;
      let m = i;
      if (l < n && this.less(l, m)) m = l;
      if (r < n && this.less(r, m)) m = r;
      if (m === i) break;
      this.swap(i, m);
      i = m;
    }
    return top;
  }
}

/** 칸 알고리즘. 순환이 남으면 depth_key 가 가장 작은 것을 강제로 뽑는다.
 *  반환: [id 순서, 순환을 자른 횟수] */
export function topoSort(items: Box[]): [number[], number] {
  const n = items.length;
  const bb: BBox[] = items.map(boxBbox);
  const adj: number[][] = [];
  for (let i = 0; i < n; i++) adj.push([]);
  const indeg: number[] = new Array<number>(n).fill(0);
  // 화면 x 로 훑는 쓸어내기. 모든 쌍을 보면 O(n^2) 인데, 한 화면에 상자가
  // 2,100개쯤 되면 220만 번이다. x 구간이 겹치는 것끼리만 보면 10만 번으로,
  // 22분의 1로 준다.
  const idx: number[] = [];
  for (let i = 0; i < n; i++) idx.push(i);
  idx.sort((a, b) => {
    const d = (bb[a] as BBox)[0] - (bb[b] as BBox)[0];
    return d !== 0 ? d : a - b;
  });
  for (let a = 0; a < n; a++) {
    const i = idx[a] as number;
    const bi = bb[i] as BBox;
    const ii = items[i] as Box;
    const ri = bi[2];
    for (let b = a + 1; b < n; b++) {
      const j = idx[b] as number;
      const bj = bb[j] as BBox;
      if (bj[0] >= ri) break; // 이후는 전부 오른쪽 — 더 볼 필요가 없다
      if (bi[3] <= bj[1] || bj[3] <= bi[1]) continue;
      const jj = items[j] as Box;
      const aij = behind(ii, jj);
      const aji = behind(jj, ii);
      // 양쪽 다 참이면 순서가 무의미하다 — 간선을 걸지 않는다 (보조정리 6.2)
      if (aij && !aji) {
        (adj[i] as number[]).push(j);
        indeg[j] = (indeg[j] as number) + 1;
      } else if (aji && !aij) {
        (adj[j] as number[]).push(i);
        indeg[i] = (indeg[i] as number) + 1;
      }
    }
  }
  const heap = new KeyHeap();
  for (let i = 0; i < n; i++) {
    if (indeg[i] === 0) heap.push(depthKey(items[i] as Box), i);
  }
  const done: boolean[] = new Array<boolean>(n).fill(false);
  const order: number[] = [];
  let breaks = 0;
  let left = n;
  while (left > 0) {
    let pick = -1;
    if (heap.size > 0) {
      pick = heap.pop();
      if (done[pick]) continue;
    } else {
      // 순환이다. 남은 것 중 가장 뒤에 있어야 할 것을 강제로 방출한다.
      breaks += 1;
      let best: [number, number, number] | null = null;
      for (let i = 0; i < n; i++) {
        if (done[i]) continue;
        const k = depthKey(items[i] as Box);
        if (best === null || keyLess(k, best)) {
          best = k;
          pick = i;
        }
      }
      for (let i = 0; i < n; i++) {
        if (done[i]) continue;
        const lst = adj[i] as number[];
        const at = lst.indexOf(pick);
        if (at >= 0) {
          lst.splice(at, 1);
          indeg[pick] = (indeg[pick] as number) - 1;
        }
      }
    }
    done[pick] = true;
    left -= 1;
    order.push((items[pick] as Box)[I_ID] as number);
    for (const j of adj[pick] as number[]) {
      indeg[j] = (indeg[j] as number) - 1;
      if (indeg[j] === 0 && !done[j]) heap.push(depthKey(items[j] as Box), j);
    }
    adj[pick] = [];
  }
  return [order, breaks];
}
