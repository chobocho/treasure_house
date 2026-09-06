// 경로 탐색 I — BFS·다익스트라·A* 와 그 성질 (SPEC §8).

import * as H from './harness';
import * as F from '../src/fixed';
import * as P from '../src/path';
import * as T from '../src/tmap';

H.title('path');

const MAPS = H.range(1, 7).map((i) => T.TMap.loadText(H.golden('map_' + i + '.txt')));

// ---- 골든 7절과 전수 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 7. 경로 탐색 ==') + 2;
let bad = 0;
let n = 0;
while (rows[i].trim() !== '' && rows[i].indexOf('다익스트라') !== 0) {
  const v = H.ints(rows[i].replace(/\(/g, ' ').replace(/\)/g, ' ')
    .replace(/,/g, ' ').replace(/->/g, ' '));
  const [mi, sx, sy, tx, ty, wb, wd, wa, wx] = v;
  const m = MAPS[mi - 1];
  const gb = P.bfs(m, 0, [sx, sy], [tx, ty]);
  let gd = P.dijkstra(m, 0, [sy * m.w + sx], ty * m.w + tx)[ty * m.w + tx];
  gd = gd >= P.INF ? -1 : gd;
  const [ga, , gx] = P.astar(m, 0, [sx, sy], [tx, ty]);
  if (!H.deepEq([gb, gd, ga, gx], [wb, wd, wa, wx])) {
    bad += 1;
    H.note('맵' + mi + ' (' + sx + ',' + sy + ')->(' + tx + ',' + ty + ') 기대 '
           + JSON.stringify([wb, wd, wa, wx]) + ' 실제 '
           + JSON.stringify([gb, gd, ga, gx]));
  }
  n += 1;
  i += 1;
}
H.check('골든 7절 ' + n + '줄 (BFS·다익스트라·A*·연 노드 수)', bad, 0);

// ---- 다익스트라와 A* 의 비용은 언제나 같아야 한다 (정리 8.1)
bad = 0;
for (const m of MAPS) {
  for (const [s, t] of m.pairs) {
    const d = P.dijkstra(m, 0, [s[1] * m.w + s[0]],
                         t[1] * m.w + t[0])[t[1] * m.w + t[0]];
    const a = P.astar(m, 0, s, t)[0];
    if ((d < P.INF ? d : -1) !== a) bad += 1;
  }
}
H.check('다익스트라 == A*', bad, 0);

// ---- 휴리스틱의 허용성: h(n) <= 실제 최적 비용 (전수)
const m0 = MAPS[0];
bad = 0;
let checked = 0;
const src: [number, number] = [16, 16];
const dist = P.dijkstra(m0, 0, [src[1] * m0.w + src[0]]);
for (let j = 0; j < m0.w * m0.h; j += 1) {
  if (dist[j] >= P.INF) continue;
  const x = j % m0.w;
  const y = Math.floor(j / m0.w);
  if (P.hOct(src[0], src[1], x, y) > dist[j]) bad += 1;
  checked += 1;
}
H.check('허용성: h <= g* (' + checked + '칸 전수)', bad, 0);

// ---- 일관성: h(n) <= c(n,n') + h(n') (전수)
bad = 0;
const tg: [number, number] = [30, 30];
for (let y = 1; y <= 30; y += 1) {
  for (let x = 1; x <= 30; x += 1) {
    for (const [d, u, v] of P.neighbours(m0, x, y, 0)) {
      if (P.hOct(x, y, tg[0], tg[1])
          > F.DCOST[d] + P.hOct(u, v, tg[0], tg[1])) bad += 1;
    }
  }
}
H.check("일관성: h(n) <= c + h(n')", bad, 0);
H.note('일관적이므로 닫힌 노드를 다시 열지 않는다 — 재개방 코드가 아예 없다');

// ---- 경로가 실제로 이어져 있고 비용이 맞는가
bad = 0;
for (const m of MAPS) {
  for (const [s, t] of m.pairs) {
    const [cost, tiles] = P.astar(m, 0, s, t);
    if (cost < 0) continue;
    let total = 0;
    for (let k = 0; k < tiles.length - 1; k += 1) {
      const ax = tiles[k] % m.w;
      const ay = Math.floor(tiles[k] / m.w);
      const bx = tiles[k + 1] % m.w;
      const by = Math.floor(tiles[k + 1] / m.w);
      const dx = bx - ax;
      const dy = by - ay;
      if (Math.max(Math.abs(dx), Math.abs(dy)) !== 1) bad += 1;
      total += (dx !== 0 && dy !== 0) ? F.D_DIAG : F.D_STRAIGHT;
    }
    if (total !== cost) bad += 1;
  }
}
H.check('경로가 한 칸씩 이어지고 비용 합이 같다', bad, 0);

// ---- 양동이 큐 (정리 8.3): 15개면 충분한가
H.check('양동이 개수', P.NB, 15);
H.check('최대 간선 비용', F.D_DIAG, 14);
H.checkTrue('양동이 개수 > 최대 간선 비용', P.NB > F.D_DIAG);

// ---- 코너 컷 허용 (SPEC §8.1)
const m2 = new T.TMap(3, 3);
for (let y = 0; y < 3; y += 1) {
  for (let x = 0; x < 3; x += 1) m2.setTerrain(x, y, T.DIRT);
}
m2.setTerrain(1, 0, T.ROCK);
m2.setTerrain(0, 1, T.ROCK);
H.check('바위 두 개 사이 대각을 지나간다', P.astar(m2, 0, [0, 0], [1, 1])[0], 14);
H.note('이것은 선택이다 — 금지하면 JPS 의 가지치기 규칙이 통째로 달라진다');

// ---- 도달 불가 목표 (SPEC §8.6)
const m5 = MAPS[4];
H.check('섬 안쪽은 닿지 않는다', P.astar(m5, 0, [1, 1], [25, 25])[0], -1);
const alt = P.closestReachable(m5, 0, [1, 1], [25, 25]);
H.checkTrue('대체 목표를 찾는다 (' + (alt === null ? 'None' : alt.join(', '))
            + ')', alt !== null);
H.check('대체 목표는 같은 성분',
        m5.labels(0)[(alt as [number, number])[1] * m5.w
                     + (alt as [number, number])[0]],
        m5.labels(0)[1 * m5.w + 1]);
const [fcost] = P.find(m5, 0, [1, 1], [25, 25]);
H.checkTrue('find 는 대체 목표까지의 경로를 준다', fcost > 0);

// ---- 경로 캐시 (SPEC §8.7)
const cache = new P.Cache();
const m1 = MAPS[0];
P.find(m1, 0, [1, 1], [30, 30], cache);
P.find(m1, 0, [1, 1], [30, 30], cache);
H.check('두 번째는 적중', cache.hits, 1);
H.check('첫 번째는 실패', cache.misses, 1);
m1.setTerrain(15, 15, T.ROCK);
P.find(m1, 0, [1, 1], [30, 30], cache);
H.check('지형이 바뀌면 통째로 비운다', cache.hits, 1);
m1.setTerrain(15, 15, T.DIRT);

H.done();
