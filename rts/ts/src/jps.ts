// 점프 포인트 탐색 — Harabor & Grastien 2011 (SPEC §10).
//
//    격자의 대칭 경로를 가지치기해 A* 가 여는 노드 수를 줄인다. 비용은 A* 와
//    **정확히 같다**. 그 등가성을 정리로 옮겨 적는 대신 전수 검사로 증명한다
//    (tests/test_jps.ts).
//
//    여기 있는 가지치기 규칙은 **코너 컷을 허용하는 격자**의 것이다. 금지하면
//    강제 이웃 조건이 통째로 달라진다 — 그것이 SPEC §8.1 에서 코너 컷을
//    허용하기로 한 첫 번째 이유다.

import * as F from './fixed';
import * as P from './path';
import { TMap } from './tmap';

// (x,y) 에 방향 (dx,dy) 로 들어왔을 때 강제 이웃이 있는가 (SPEC §10.1).
export function forced(m: TMap, x: number, y: number, dx: number, dy: number,
                       kind: number): boolean {
  const ok = (u: number, v: number): boolean => m.passableTerrain(u, v, kind);
  if (dx !== 0 && dy !== 0) {
    return (!ok(x - dx, y) && ok(x - dx, y + dy))
      || (!ok(x, y - dy) && ok(x + dx, y - dy));
  }
  if (dx !== 0) {
    for (const s of [-1, 1]) {
      if (!ok(x, y + s) && ok(x + dx, y + s)) return true;
    }
    return false;
  }
  for (const s of [-1, 1]) {
    if (!ok(x + s, y) && ok(x + s, y + dy)) return true;
  }
  return false;
}

// 방향 (dx,dy) 로 계속 나아가다 점프점을 만나면 그 칸을 돌려준다.
// 대각 점프가 먼저 두 성분 방향을 재귀로 훑는 것이 핵심이다. 그 방향에서
// 점프점이 나오면 지금 서 있는 대각 칸 자체가 점프점이 된다.
export function jump(m: TMap, x: number, y: number, dx: number, dy: number,
                     t: [number, number],
                     kind: number): [number, number] | null {
  const u = x + dx;
  const v = y + dy;
  if (!m.passableTerrain(u, v, kind)) return null;
  if (u === t[0] && v === t[1]) return [u, v];
  if (forced(m, u, v, dx, dy, kind)) return [u, v];
  if (dx !== 0 && dy !== 0) {
    if (jump(m, u, v, dx, 0, t, kind) !== null
        || jump(m, u, v, 0, dy, t, kind) !== null) return [u, v];
  }
  return jump(m, u, v, dx, dy, t, kind);
}

// 부모에서 온 방향에 따라 살아남는 이웃 방향들 (SPEC §10.1).
export function prune(m: TMap, x: number, y: number,
                      parent: [number, number] | null,
                      kind: number): Array<[number, number]> {
  const ok = (u: number, v: number): boolean => m.passableTerrain(u, v, kind);
  if (parent === null) {
    const out: Array<[number, number]> = [];
    for (let d = 0; d < 8; d += 1) {
      if (ok(x + F.DX[d], y + F.DY[d])) out.push([F.DX[d], F.DY[d]]);
    }
    return out;
  }
  const px = parent[0];
  const py = parent[1];
  const dx = (x - px > 0 ? 1 : 0) - (x - px < 0 ? 1 : 0);
  const dy = (y - py > 0 ? 1 : 0) - (y - py < 0 ? 1 : 0);
  const out: Array<[number, number]> = [];
  if (dx !== 0 && dy !== 0) {
    if (ok(x + dx, y)) out.push([dx, 0]);
    if (ok(x, y + dy)) out.push([0, dy]);
    if (ok(x + dx, y + dy)) out.push([dx, dy]);
    if (!ok(x - dx, y) && ok(x - dx, y + dy)) out.push([-dx, dy]);
    if (!ok(x, y - dy) && ok(x + dx, y - dy)) out.push([dx, -dy]);
  } else if (dx !== 0) {
    if (ok(x + dx, y)) out.push([dx, 0]);
    for (const s of [-1, 1]) {
      if (!ok(x, y + s) && ok(x + dx, y + s)) out.push([dx, s]);
    }
  } else {
    if (ok(x, y + dy)) out.push([0, dy]);
    for (const s of [-1, 1]) {
      if (!ok(x + s, y) && ok(x + s, y + dy)) out.push([s, dy]);
    }
  }
  return out;
}

// (비용, 점프점 목록, 연 노드 수). A* 와 같은 비교자·같은 힙을 쓴다.
export function search(m: TMap, kind: number, s: [number, number],
                       t: [number, number]): [number, number[], number] {
  const w = m.w;
  if (!(m.passableTerrain(s[0], s[1], kind)
        && m.passableTerrain(t[0], t[1], kind))) return [-1, [], 0];
  const si = s[1] * w + s[0];
  const ti = t[1] * w + t[0];
  const dist = new Map<number, number>();
  dist.set(si, 0);
  const parent = new Map<number, [number, number] | null>();
  parent.set(si, null);
  const closed = new Set<number>();
  const heap = new P.Heap();
  const h0 = P.hOct(s[0], s[1], t[0], t[1]);
  heap.push(h0, h0, si);
  let expanded = 0;
  while (heap.length > 0) {
    const p = heap.pop()[2];
    if (closed.has(p)) continue;
    closed.add(p);
    expanded += 1;
    const x = F.fmod(p, w);
    const y = F.floordiv(p, w);
    if (p === ti) {
      const out = [p];
      for (;;) {
        const q = parent.get(out[out.length - 1]) as [number, number] | null;
        if (q === null) break;
        out.push(q[1] * w + q[0]);
      }
      out.reverse();
      return [dist.get(p) as number, out, expanded];
    }
    const par = parent.get(p) as [number, number] | null;
    const dp = dist.get(p) as number;
    for (const [dx, dy] of prune(m, x, y, par, kind)) {
      const n = jump(m, x, y, dx, dy, t, kind);
      if (n === null) continue;
      const steps = Math.max(Math.abs(n[0] - x), Math.abs(n[1] - y));
      const nd = dp + steps * ((dx !== 0 && dy !== 0) ? F.D_DIAG : F.D_STRAIGHT);
      const j = n[1] * w + n[0];
      const old = dist.has(j) ? (dist.get(j) as number) : P.INF;
      if (nd < old) {
        dist.set(j, nd);
        parent.set(j, [x, y]);
        const hn = P.hOct(n[0], n[1], t[0], t[1]);
        heap.push(nd + hn, hn, j);
      }
    }
  }
  return [-1, [], expanded];
}
