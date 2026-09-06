// 흐름장·클리어런스·브러시파이어 (SPEC §11).
//
//    골든 9절과 대조하고, 정리 11.1 은 완전 탐색으로 직접 확인한다.

import * as H from './harness';
import * as F from '../src/fixed';
import * as FL from '../src/flow';
import * as P from '../src/path';
import * as T from '../src/tmap';
import { padLeft } from '../src/fmt';

H.title('flow');

// tools/gen_prim.py 의 FLOWMAP 과 **글자 단위로 같아야 한다**.
const FLOWMAP = [
  '............',
  '.##########.',
  '.#........#.',
  '.#.######.#.',
  '.#.#....#.#.',
  '.#.#.##.#.#.',
  '.#.#.##.#.#.',
  '.#.#....#.#.',
  '.#.######.#.',
  '.#........#.',
  '.##########.',
  '............',
];

function grid(rowsIn: string[]): T.TMap {
  const m = new T.TMap(rowsIn[0].length, rowsIn.length);
  for (let y = 0; y < rowsIn.length; y += 1) {
    for (let x = 0; x < rowsIn[y].length; x += 1) {
      m.terrain[y * m.w + x] = rowsIn[y][x] === '#' ? T.ROCK : T.DIRT;
      m.repass(y * m.w + x);
    }
  }
  m.bump();
  return m;
}

function rowsOf(field: number[], m: T.TMap, width: number): string[] {
  const out: string[] = [];
  for (let y = 0; y < m.h; y += 1) {
    const cells: string[] = [];
    for (let x = 0; x < m.w; x += 1) cells.push(padLeft(field[y * m.w + x], width));
    out.push('  ' + cells.join(' '));
  }
  return out;
}

const FM = grid(FLOWMAP);

// ── 골든 9절 세 표와 한 줄씩 대조 ───────────────────────────────────────────
const g = H.golden('prim.txt').split('\n');
const i9 = g.indexOf('== 9. 흐름장과 클리어런스 ==');
const integ = FL.integration(FM, 0, [[4, 4]]);
const fl = FL.flowDirs(FM, 0, integ);
const cl = FL.clearance(FM, 0);
const want = g.slice(i9 + 2, i9 + 2 + 12)
  .concat(g.slice(i9 + 15, i9 + 15 + 12))
  .concat(g.slice(i9 + 28, i9 + 28 + 12));
const got = rowsOf(integ, FM, 5).concat(rowsOf(fl, FM, 3))
  .concat(rowsOf(cl, FM, 2));
let bad = 0;
for (let k = 0; k < 36; k += 1) {
  if (got[k] !== want[k]) {
    bad += 1;
    if (bad < 4) {
      H.note(k + '행 기대 ' + JSON.stringify(want[k]));
      H.note('     실제 ' + JSON.stringify(got[k]));
    }
  }
}
H.check('골든 9절 36줄 (적분장·경사장·클리어런스)', bad, 0);

// ── 적분장 = 목표에서 거꾸로 돌린 다익스트라 ────────────────────────────────
const dd = P.dijkstra(FM, 0, [4 * FM.w + 4]);
bad = 0;
for (let j = 0; j < FM.w * FM.h; j += 1) {
  let wv = dd[j] >= FL.INF ? FL.INF : dd[j];
  if (!FM.passableTerrain(j % FM.w, Math.floor(j / FM.w), 0)) wv = FL.INF;
  if (integ[j] !== wv) bad += 1;
}
H.check('적분장 == path.dijkstra (INF 는 65535 로 자름)', bad, 0);

// ── 다중 목표는 목표별 장의 최솟값이다 ──────────────────────────────────────
const fa = FL.integration(FM, 0, [[2, 2]]);
const fb = FL.integration(FM, 0, [[9, 9]]);
const fab = FL.integration(FM, 0, [[2, 2], [9, 9]]);
H.check('다중 목표 == 목표별 최솟값', fab,
        H.range(FM.w * FM.h).map((j) => Math.min(fa[j], fb[j])));

// ── 경계 조건 ───────────────────────────────────────────────────────────────
H.check('목표가 없으면 전부 INF',
        H.sortedSet(FL.integration(FM, 0, [])), [FL.INF]);
H.check('막힌 목표는 무시한다 (SPEC §11.1)',
        FL.integration(FM, 0, [[1, 1]]), FL.integration(FM, 0, []));
H.check('막힌 목표 + 성한 목표 = 성한 목표만',
        FL.integration(FM, 0, [[1, 1], [4, 4]]), integ);
const one = grid(['.']);
H.check('1x1 맵', FL.integration(one, 0, [[0, 0]]), [0]);
H.check('1x1 맵의 경사장', FL.flowDirs(one, 0, [0]), [255]);
H.check('1x1 맵의 클리어런스', FL.clearance(one, 0), [1]);
const solid = grid(['##', '##']);
H.check('전부 막힌 맵의 클리어런스', FL.clearance(solid, 0), [0, 0, 0, 0]);
H.check('전부 막힌 맵의 브러시파이어', FL.brushfire(solid, 0), [0, 0, 0, 0]);

// ── 경사장: 막힌 칸과 INF 칸은 255, 나머지는 내리막이다 ─────────────────────
bad = 0;
let stops = 0;
for (let j = 0; j < FM.w * FM.h; j += 1) {
  const x = j % FM.w;
  const y = Math.floor(j / FM.w);
  if (integ[j] === FL.INF) {
    if (fl[j] !== 255) bad += 1;
    continue;
  }
  if (fl[j] === 255) {
    stops += 1;
    continue;
  }
  const u = x + F.DX[fl[j]];
  const v = y + F.DY[fl[j]];
  if (integ[j] === 0) continue;      // 목표 칸은 예외 — 오르막을 가리킨다
  if (!FM.passableTerrain(u, v, 0) || integ[v * FM.w + u] >= integ[j]) bad += 1;
}
H.check('INF·막힌 칸의 경사는 255', bad, 0);
H.check('정지 칸은 없다 (모든 도달 가능 칸에 후보가 있다)', stops, 0);

// ── 경사장 동점 규칙: 대칭 맵에서 항상 작은 방향 번호 ───────────────────────
const open3 = grid(['...', '...', '...']);
const of3 = FL.flowDirs(open3, 0, FL.integration(open3, 0, [[1, 1]]));
H.check('(0,0) 은 목표를 향한 대각 3(SE)', of3[0], 3);
H.check('목표 칸도 255 가 아니다 — 가장 싼 이웃(오르막)을 가리킨다', of3[4], 0);
const tie = FL.flowDirs(open3, 0, FL.integration(open3, 0, [[0, 0], [2, 0]]));
H.check('동점이면 작은 방향 번호 — (1,1) 은 1(NE), 7(NW) 이 아니다', tie[4], 1);

// ── 정리 11.1 을 완전 탐색으로 확인 ─────────────────────────────────────────
function maxSquare(m: T.TMap, kind: number, x: number, y: number): number {
  let k = 0;
  for (;;) {
    const s = k + 1;
    if (x + s > m.w || y + s > m.h) return k;
    for (let v = y; v < y + s; v += 1) {
      for (let u = x; u < x + s; u += 1) {
        if (!m.passableTerrain(u, v, kind)) return k;
      }
    }
    k = s;
  }
}

const MAPS = [FM].concat(
  H.range(1, 7).map((k) => T.TMap.loadText(H.golden('map_' + k + '.txt'))));
bad = 0;
let cells = 0;
for (const m of MAPS) {
  const c = FL.clearance(m, 0);
  for (let y = 0; y < m.h; y += 1) {
    for (let x = 0; x < m.w; x += 1) {
      cells += 1;
      if (c[y * m.w + x] !== maxSquare(m, 0, x, y)) bad += 1;
    }
  }
}
H.check('정리 11.1 — ' + cells + '칸에서 clear == 최대 정사각 변', bad, 0);

// ── 크기 s 유닛의 통행 판정 ─────────────────────────────────────────────────
const M1 = MAPS[1];
const c1 = FL.clearance(M1, 0);
let passCount = 0;
for (let j = 0; j < M1.w * M1.h; j += 1) {
  if (M1.passableTerrain(j % M1.w, Math.floor(j / M1.w), 0)) passCount += 1;
}
H.checkTrue('크기 1 통행 칸 수 == 지형 통행 칸 수',
            c1.filter((v) => v >= 1).length === passCount);
H.checkTrue('크기 2 통행 칸은 크기 1 통행 칸의 부분집합',
            c1.filter((v) => v >= 2).every((v) => v >= 1));
H.check('size_passable 는 clear >= s 와 같다',
        H.range(20).map((j) => FL.sizePassable(c1, M1, j % M1.w,
                                               Math.floor(j / M1.w), 2)),
        H.range(20).map((j) => c1[j] >= 2));
H.check('맵 밖은 어떤 크기로도 통행 불가',
        FL.sizePassable(c1, M1, -1, 0, 1), false);

// ── 브러시파이어: 벨만-포드로 다시 풀어 비교 ────────────────────────────────
// 같은 답을 아주 느리게 구하는 참조 구현 — 완화가 멈출 때까지 돈다.
function brushfireRef(m: T.TMap, kind: number): number[] {
  const n = m.w * m.h;
  const dist = new Array<number>(n).fill(FL.INF);
  for (let y = 0; y < m.h; y += 1) {
    for (let x = 0; x < m.w; x += 1) {
      if (!m.passableTerrain(x, y, kind)) {
        dist[y * m.w + x] = 0;
      } else {
        for (let d = 0; d < 8; d += 1) {
          if (!m.inMap(x + F.DX[d], y + F.DY[d])) {
            dist[y * m.w + x] = Math.min(dist[y * m.w + x], F.DCOST[d]);
          }
        }
      }
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (let y = 0; y < m.h; y += 1) {
      for (let x = 0; x < m.w; x += 1) {
        if (!m.passableTerrain(x, y, kind)) continue;
        const j = y * m.w + x;
        for (let d = 0; d < 8; d += 1) {
          const u = x + F.DX[d];
          const v = y + F.DY[d];
          if (!m.inMap(u, v)) continue;
          const nd = dist[v * m.w + u] + F.DCOST[d];
          if (nd < dist[j]) {
            dist[j] = nd;
            changed = true;
          }
        }
      }
    }
  }
  return dist;
}

bad = 0;
for (const m of MAPS.slice(0, 4)) {
  if (!H.deepEq(FL.brushfire(m, 0), brushfireRef(m, 0))) bad += 1;
}
H.check('브러시파이어 == 참조 구현 (맵 4장)', bad, 0);

const fire = FL.brushfire(FM, 0);
H.check('막힌 칸의 fire 는 0', fire[1 * FM.w + 1], 0);
H.check('가장자리 자유 칸의 fire 는 10 (맵 밖 = 막힌 칸)', fire[0], 10);
H.checkTrue('바위 덩어리 반대편으로 0 이 새지 않는다',
            fire[0 * FM.w + 6] > 0 && fire[2 * FM.w + 5] > 0);

// ── 한 번 계산하면 유닛 수와 무관하다 (§11.1 의 손익분기) ───────────────────
const free: number[] = [];
for (let j = 0; j < FM.w * FM.h; j += 1) {
  if (FM.passableTerrain(j % FM.w, Math.floor(j / FM.w), 0)) free.push(j);
}
bad = 0;
for (const j of free.slice(0, 40)) {
  const s: [number, number] = [j % FM.w, Math.floor(j / FM.w)];
  if (integ[j] >= FL.INF) continue;
  if (P.astar(FM, 0, s, [4, 4])[0] !== integ[j]) bad += 1;
}
H.check('적분장 값 == 그 칸에서 목표까지의 A* 비용 ('
        + free.slice(0, 40).length + '칸)', bad, 0);

H.done();
