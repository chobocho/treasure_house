// 경로 — 허용성·일관성·모서리 자르기·A* == 다익스트라.
import * as H from './harness';
import * as M from '../src/gamemap';
import * as P from '../src/path';

export function run(): number {
  H.title('path');

  const m = M.genMap();

  // ---- 방향표
  H.check('방향 8개', [P.DIRX.length, P.DIRY.length], [8, 8]);
  H.check('대각 표시', P.DIAG, [false, true, false, true, false, true, false, true]);
  H.check('걸음 기본값', P.STEP_BASE, [10, 14, 10, 14, 10, 14, 10, 14]);

  // ---- 옥타일 골든
  H.check('h((0,0),(0,0))', P.octile(0, 0, 0, 0), 0);
  H.check('h((0,0),(1,0))', P.octile(0, 0, 1, 0), 8);
  H.check('h((0,0),(1,1))', P.octile(0, 0, 1, 1), 11);
  H.check('h((0,0),(47,47))', P.octile(0, 0, 47, 47), 517);
  H.note('내림을 두 번 하는 흔한 형태는 같은 자리에서 526 을 낸다 — 허용성이 깨진 값');

  // ---- 허용성: 다익스트라 실제 비용 >= h
  const sx = 24;
  const sy = 34;
  const dist = P.dijkstra(m, sx, sy);
  let bad = 0;
  for (let y = 0; y < 48; y++) {
    for (let x = 0; x < 48; x++) {
      const d = dist[y * 48 + x] as number;
      if (d === P.UNREACHED) continue;
      if (P.octile(sx, sy, x, y) > d) bad += 1;
    }
  }
  H.check('허용성 위반 (실제 비용 < h)', bad, 0);

  // ---- 일관성: 모든 간선에서 h(a)-h(n) <= cost
  const gx0 = 24;
  const gy0 = 20;
  bad = 0;
  for (let y = 0; y < 48; y++) {
    for (let x = 0; x < 48; x++) {
      if (!P.passable(m, x, y)) continue;
      for (let d = 0; d < 8; d++) {
        if (!P.stepOk(m, x, y, d)) continue;
        const nx = x + (P.DIRX[d] as number);
        const ny = y + (P.DIRY[d] as number);
        if (P.octile(x, y, gx0, gy0) - P.octile(nx, ny, gx0, gy0) > P.stepCost(m, nx, ny, d)) {
          bad += 1;
        }
      }
    }
  }
  H.check('일관성 위반 간선', bad, 0);

  // ---- 모서리 자르기 금지
  let cut = 0;
  for (let y = 1; y < 47; y++) {
    for (let x = 1; x < 47; x++) {
      for (const d of [1, 3, 5, 7]) {
        if (P.stepOk(m, x, y, d)) {
          if (!(P.passable(m, x + (P.DIRX[d] as number), y)
            && P.passable(m, x, y + (P.DIRY[d] as number)))) cut += 1;
        }
      }
    }
  }
  H.check('막힌 모서리를 대각으로 통과한 사례', cut, 0);

  // ---- 오르막 제한
  bad = 0;
  for (let y = 0; y < 47; y++) {
    for (let x = 0; x < 47; x++) {
      for (let d = 0; d < 8; d++) {
        const nx = x + (P.DIRX[d] as number);
        const ny = y + (P.DIRY[d] as number);
        if (!m.inside(nx, ny) || !P.stepOk(m, x, y, d)) continue;
        if (Math.abs(M.heightOf(m.at(nx, ny)) - M.heightOf(m.at(x, y))) > P.CLIMB_MAX) bad += 1;
      }
    }
  }
  H.check('오르막 제한 위반', bad, 0);

  // ---- A* 가 다익스트라와 같은 비용을 내는가
  const targets: Array<[number, number]> = [
    [24, 20], [20, 20], [29, 29], [24, 44], [18, 24], [26, 26], [2, 2],
  ];
  let same = 0;
  let miss = 0;
  for (const [gx, gy] of targets) {
    const got = P.astar(m, sx, sy, gx, gy);
    const want = dist[gy * 48 + gx] as number;
    if (want === P.UNREACHED) {
      miss += 1;
      H.check('A* 도 못 감 (' + gx + ',' + gy + ')', got.path, null);
      continue;
    }
    H.check('A* 비용 == 다익스트라 (' + gx + ',' + gy + ')', got.cost, want);
    same += 1;
  }
  H.note('도달 가능 ' + same + '개 / 도달 불가 ' + miss + '개');

  // ---- 경로가 실제로 이어지는가
  const res = P.astar(m, sx, sy, 24, 20);
  const pathOut = res.path as Array<[number, number]>;
  H.check('경로 시작', pathOut[0], [sx, sy]);
  H.check('경로 끝', pathOut[pathOut.length - 1], [24, 20]);
  bad = 0;
  let tot = 0;
  for (let i = 0; i < pathOut.length - 1; i++) {
    const a = pathOut[i] as [number, number];
    const b = pathOut[i + 1] as [number, number];
    let dd = -1;
    for (let d = 0; d < 8; d++) {
      if (P.DIRX[d] === b[0] - a[0] && P.DIRY[d] === b[1] - a[1]) { dd = d; break; }
    }
    if (dd < 0 || !P.stepOk(m, a[0], a[1], dd)) bad += 1;
    else tot += P.stepCost(m, b[0], b[1], dd);
  }
  H.check('경로 각 걸음이 합법', bad, 0);
  H.check('걸음 비용 합 == A* 비용', tot, res.cost);
  let reach = 0;
  for (let i = 0; i < dist.length; i++) if (dist[i] !== P.UNREACHED) reach += 1;
  H.note('A* 확장 노드 ' + res.expanded + '개 (다익스트라 전체 ' + reach + '칸)');
  H.checkTrue('A* 가 다익스트라보다 적게 본다', res.expanded < reach);

  // ---- 양동이 큐 경계
  let mxc = 0;
  for (let y = 0; y < 48; y++) {
    for (let x = 0; x < 48; x++) {
      if (!P.passable(m, x, y)) continue;
      for (let d = 0; d < 8; d++) {
        const c = P.stepCost(m, x, y, d);
        if (c > mxc) mxc = c;
      }
    }
  }
  H.checkTrue('최대 간선 비용 < BUCKET_N', mxc < P.BUCKET_N);

  return H.done();
}
