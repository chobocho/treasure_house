// 계층 경로 탐색 — HPA* 2수준 (SPEC §9, Botea–Müller–Schaeffer 2004).
//
//    **HPA* 는 최적이 아니다.** 원 논문이 보고하는 "최적 대비 1 % 안팎"은
//    그 논문의 맵과 클러스터 크기에서 나온 값이다. 이 엔진의 값은 골든 맵에서
//    직접 재어 out/*_prim.txt 8절에 남기고, 덱은 그 숫자만 쓴다.
//
//    노드는 (x,y) 튜플 대신 `x * 4096 + y` 정수 하나로 담는다. 그래야 노드
//    정렬이 파이썬의 튜플 사전식 정렬과 **정확히 같은 순서**가 되고, 문자열
//    키를 쓸 때 생기는 사전 순회 순서 문제도 아예 생기지 않는다.

import * as F from './fixed';
import * as P from './path';
import { TMap } from './tmap';

export const CLUSTER = 8;

export function nk(x: number, y: number): number {
  return x * 4096 + y;
}

export function nkx(k: number): number {
  return F.floordiv(k, 4096);
}

export function nky(k: number): number {
  return F.fmod(k, 4096);
}

export function clusterOf(x: number, y: number): [number, number] {
  return [F.floordiv(x, CLUSTER), F.floordiv(y, CLUSTER)];
}

function ck(x: number, y: number): number {
  return F.floordiv(x, CLUSTER) * 4096 + F.floordiv(y, CLUSTER);
}

// 한 클러스터 안에서만 도는 A*. 8×8 이므로 최악 64칸이다.
export function intra(m: TMap, kind: number, a: number, b: number): number {
  const ax = nkx(a);
  const ay = nky(a);
  const bx = nkx(b);
  const by = nky(b);
  const cx = F.floordiv(ax, CLUSTER);
  const cy = F.floordiv(ay, CLUSTER);
  const loX = cx * CLUSTER;
  const loY = cy * CLUSTER;
  const hiX = loX + CLUSTER - 1;
  const hiY = loY + CLUSTER - 1;
  const dist = new Map<number, number>();
  dist.set(a, 0);
  const heap = new P.Heap();
  heap.push(P.hOct(ax, ay, bx, by), 0, 0);
  const nodes: number[] = [a];
  const closed = new Set<number>();
  while (heap.length > 0) {
    const k = heap.pop()[2];
    const p = nodes[k];
    if (closed.has(p)) continue;
    closed.add(p);
    if (p === b) return dist.get(p) as number;
    const px = nkx(p);
    const py = nky(p);
    const dp = dist.get(p) as number;
    for (const [d, u, v] of P.neighbours(m, px, py, kind)) {
      if (!(u >= loX && u <= hiX && v >= loY && v <= hiY)) continue;
      const key = nk(u, v);
      const nd = dp + F.DCOST[d];
      const old = dist.has(key) ? (dist.get(key) as number) : P.INF;
      if (nd < old) {
        dist.set(key, nd);
        nodes.push(key);
        heap.push(nd + P.hOct(u, v, bx, by), 0, nodes.length - 1);
      }
    }
  }
  return -1;
}

// SPEC §9.2 — 짧은 구간은 가운데 하나, 긴 구간은 양 끝 둘.
export function place<T>(run: number[], mk: (v: number) => T): T[] {
  if (run.length === 0) return [];
  if (run.length <= 5) return [mk(run[F.floordiv(run.length - 1, 2)])];
  return [mk(run[0]), mk(run[run.length - 1])];
}

export type Edge = [[number, number], [number, number]];

// 클러스터 경계에서 양쪽이 모두 통행 가능한 연속 구간을 찾아 전이를 만든다.
export function entrances(m: TMap, kind: number): Edge[] {
  let edges: Edge[] = [];
  const cw = F.floordiv(m.w, CLUSTER);
  const chh = F.floordiv(m.h, CLUSTER);
  for (let cy = 0; cy < chh; cy += 1) {
    for (let cx = 0; cx < cw; cx += 1) {
      if (cx + 1 < cw) {
        const x = cx * CLUSTER + CLUSTER - 1;
        const mkH = (yy: number): Edge => [[x, yy], [x + 1, yy]];
        let run: number[] = [];
        for (let y = cy * CLUSTER; y < cy * CLUSTER + CLUSTER; y += 1) {
          if (m.passableTerrain(x, y, kind)
              && m.passableTerrain(x + 1, y, kind)) {
            run.push(y);
          } else {
            edges = edges.concat(place(run, mkH));
            run = [];
          }
        }
        edges = edges.concat(place(run, mkH));
      }
      if (cy + 1 < chh) {
        const y = cy * CLUSTER + CLUSTER - 1;
        const mkV = (xx: number): Edge => [[xx, y], [xx, y + 1]];
        let run: number[] = [];
        for (let x = cx * CLUSTER; x < cx * CLUSTER + CLUSTER; x += 1) {
          if (m.passableTerrain(x, y, kind)
              && m.passableTerrain(x, y + 1, kind)) {
            run.push(x);
          } else {
            edges = edges.concat(place(run, mkV));
            run = [];
          }
        }
        edges = edges.concat(place(run, mkV));
      }
    }
  }
  return edges;
}

// 추상 그래프. 맵 버전이 바뀌면 다시 짓는다.
//
//   인접 목록의 순서는 (1) entrances 가 만든 전이 간선, (2) 같은 클러스터 안
//   노드 쌍의 정렬 순서로 **완전히 결정된다.** 한 노드는 정확히 한 클러스터에만
//   속하므로 클러스터를 어떤 순서로 훑든 결과가 같다 — 파이썬의 집합·사전
//   순회 순서에 기대는 자리가 여기에는 없다.
export class Abstract {
  version: number;
  kind: number;
  graph: Map<number, Array<[number, number]>>;
  byCluster: Map<number, number[]>;

  constructor(m: TMap, kind: number) {
    this.version = m.version;
    this.kind = kind;
    this.graph = new Map<number, Array<[number, number]>>();
    this.byCluster = new Map<number, number[]>();
    const nodes = new Set<number>();
    const addEdge = (a: number, b: number, c: number): void => {
      let lst = this.graph.get(a);
      if (lst === undefined) {
        lst = [];
        this.graph.set(a, lst);
      }
      lst.push([b, c]);
    };
    for (const [a, b] of entrances(m, kind)) {
      const ka = nk(a[0], a[1]);
      const kb = nk(b[0], b[1]);
      nodes.add(ka);
      nodes.add(kb);
      addEdge(ka, kb, F.D_STRAIGHT);
      addEdge(kb, ka, F.D_STRAIGHT);
    }
    for (const n of nodes) {
      const c = ck(nkx(n), nky(n));
      let lst = this.byCluster.get(c);
      if (lst === undefined) {
        lst = [];
        this.byCluster.set(c, lst);
      }
      lst.push(n);
    }
    for (const c of Array.from(this.byCluster.keys())) {
      const ns = (this.byCluster.get(c) as number[]).slice();
      ns.sort((a, b) => a - b);
      this.byCluster.set(c, ns);
      for (let i = 0; i < ns.length; i += 1) {
        for (let j = i + 1; j < ns.length; j += 1) {
          const c1 = intra(m, kind, ns[i], ns[j]);
          if (c1 >= 0) {
            addEdge(ns[i], ns[j], c1);
            addEdge(ns[j], ns[i], c1);
          }
        }
      }
    }
  }
}

const cacheByMap = new WeakMap<TMap, Map<number, Abstract>>();

export function abstract(m: TMap, kind: number): Abstract {
  let per = cacheByMap.get(m);
  if (per === undefined) {
    per = new Map<number, Abstract>();
    cacheByMap.set(m, per);
  }
  let a = per.get(kind);
  if (a === undefined || a.version !== m.version) {
    a = new Abstract(m, kind);
    per.set(kind, a);
  }
  return a;
}

// 추상 그래프 위의 A*. 정련 경로의 비용은 추상 비용과 같다.
export function search(m: TMap, kind: number, s: [number, number],
                       t: [number, number]): [number, number[]] {
  if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind))) return [-1, []];
  const ab = abstract(m, kind);
  const graph = new Map<number, Array<[number, number]>>();
  for (const [k, v] of ab.graph) graph.set(k, v.slice());
  const addEdge = (a: number, b: number, c: number): void => {
    let lst = graph.get(a);
    if (lst === undefined) {
      lst = [];
      graph.set(a, lst);
    }
    lst.push([b, c]);
  };
  const sk = nk(s[0], s[1]);
  const tk = nk(t[0], t[1]);
  for (const temp of [sk, tk]) {           // 임시 노드 삽입 (질의가 끝나면 버린다)
    const near = ab.byCluster.get(ck(nkx(temp), nky(temp)));
    for (const n of (near === undefined ? [] : near)) {
      const c1 = intra(m, kind, temp, n);
      if (c1 >= 0) {
        addEdge(temp, n, c1);
        addEdge(n, temp, c1);
      }
    }
  }
  if (ck(s[0], s[1]) === ck(t[0], t[1])) {
    const c1 = intra(m, kind, sk, tk);
    if (c1 >= 0) addEdge(sk, tk, c1);
  }

  const dist = new Map<number, number>();
  dist.set(sk, 0);
  const prev = new Map<number, number>();
  const closed = new Set<number>();
  const heap = new P.Heap();
  const nodes: number[] = [sk];
  heap.push(P.hOct(s[0], s[1], t[0], t[1]), 0, 0);
  while (heap.length > 0) {
    const k = heap.pop()[2];
    const p = nodes[k];
    if (closed.has(p)) continue;
    closed.add(p);
    if (p === tk) {
      const out = [p];
      while (prev.has(out[out.length - 1])) {
        out.push(prev.get(out[out.length - 1]) as number);
      }
      out.reverse();
      return [dist.get(p) as number, out];
    }
    const dp = dist.get(p) as number;
    const adj = graph.get(p);
    for (const [n, c1] of (adj === undefined ? [] : adj)) {
      const nd = dp + c1;
      const old = dist.has(n) ? (dist.get(n) as number) : P.INF;
      if (nd < old) {
        dist.set(n, nd);
        prev.set(n, p);
        nodes.push(n);
        heap.push(nd + P.hOct(nkx(n), nky(n), t[0], t[1]), 0, nodes.length - 1);
      }
    }
  }
  return [-1, []];
}

// 추상 경로의 인접 노드 쌍을 클러스터 안 A* 로 실제 타일 열로 편다.
export function refine(m: TMap, kind: number, absnodes: number[]): number[] {
  let out: number[] = [];
  for (let i = 0; i < absnodes.length - 1; i += 1) {
    const a = absnodes[i];
    const b = absnodes[i + 1];
    const ax = nkx(a);
    const ay = nky(a);
    const bx = nkx(b);
    const by = nky(b);
    let tiles: number[];
    if (ck(ax, ay) === ck(bx, by)) {
      tiles = P.astar(m, kind, [ax, ay], [bx, by])[1];
    } else {
      tiles = [ay * m.w + ax, by * m.w + bx];
    }
    if (out.length > 0 && tiles.length > 0
        && out[out.length - 1] === tiles[0]) {
      tiles = tiles.slice(1);
    }
    out = out.concat(tiles);
  }
  return out;
}
