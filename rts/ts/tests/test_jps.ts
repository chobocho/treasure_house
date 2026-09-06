// 점프 포인트 탐색 — A* 와 비용이 같은가를 전수로 확인한다 (SPEC §10).

import * as H from './harness';
import * as J from '../src/jps';
import * as P from '../src/path';
import { LCG } from '../src/rng';
import * as T from '../src/tmap';

H.title('jps');

const MAPS = H.range(1, 7).map((i) => T.TMap.loadText(H.golden('map_' + i + '.txt')));

// ---- 골든 8절의 JPS 열과 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 8. HPA* 와 JPS ==') + 2;
let bad = 0;
let n = 0;
while (rows[i].trim() !== '' && rows[i].indexOf('JPS 비용') !== 0) {
  const v = H.ints(rows[i].replace(/\(/g, ' ').replace(/\)/g, ' ')
    .replace(/,/g, ' ').replace(/->/g, ' '));
  const [mi, sx, sy, tx, ty, , wj, wjx] = v;
  const m = MAPS[mi - 1];
  const [c, , ex] = J.search(m, 0, [sx, sy], [tx, ty]);
  if (!H.deepEq([c, ex], [wj, wjx])) {
    bad += 1;
    H.note('맵' + mi + ' (' + sx + ',' + sy + ')->(' + tx + ',' + ty + ') 기대 '
           + JSON.stringify([wj, wjx]) + ' 실제 ' + JSON.stringify([c, ex]));
  }
  n += 1;
  i += 1;
}
H.check('골든 8절 ' + n + '줄의 JPS 비용·연 노드 수', bad, 0);

// ---- 전수 검사: 정리 10.1 을 옮겨 적는 대신 직접 확인한다
bad = 0;
let total = 0;
for (let mi = 0; mi < MAPS.length; mi += 1) {
  const m = MAPS[mi];
  const free: number[] = [];
  for (let j = 0; j < m.w * m.h; j += 1) {
    if (m.passableTerrain(j % m.w, Math.floor(j / m.w), 0)) free.push(j);
  }
  const rand = new LCG(1000 + mi);
  for (let k = 0; k < 120; k += 1) {
    const a = free[rand.roll(free.length)];
    const b = free[rand.roll(free.length)];
    const s: [number, number] = [a % m.w, Math.floor(a / m.w)];
    const t: [number, number] = [b % m.w, Math.floor(b / m.w)];
    const ca = P.astar(m, 0, s, t)[0];
    const cj = J.search(m, 0, s, t)[0];
    total += 1;
    if (ca !== cj) {
      bad += 1;
      if (bad < 4) {
        H.note('맵' + (mi + 1) + ' (' + s[0] + ',' + s[1] + ')->('
               + t[0] + ',' + t[1] + ') A*=' + ca + ' JPS=' + cj);
      }
    }
  }
}
H.check('무작위 ' + total + '쌍에서 JPS 비용 == A* 비용', bad, 0);

// ---- 경로가 실제로 이어지는가 (점프점 사이는 직선이어야 한다)
bad = 0;
for (const m of MAPS) {
  for (const [s, t] of m.pairs) {
    const [cost, tiles] = J.search(m, 0, s, t);
    if (cost < 0) continue;
    for (let k = 0; k < tiles.length - 1; k += 1) {
      const ax = tiles[k] % m.w;
      const ay = Math.floor(tiles[k] / m.w);
      const bx = tiles[k + 1] % m.w;
      const by = Math.floor(tiles[k + 1] / m.w);
      const dx = bx - ax;
      const dy = by - ay;
      if (dx !== 0 && dy !== 0 && Math.abs(dx) !== Math.abs(dy)) bad += 1;
      if (dx === 0 && dy === 0) bad += 1;
    }
  }
}
H.check('점프점 사이가 직선 또는 45도', bad, 0);

// ---- JPS 가 여는 노드 수는 A* 이하인가
let worse = 0;
let same = 0;
for (const m of MAPS) {
  for (const [s, t] of m.pairs) {
    const ax = P.astar(m, 0, s, t)[2];
    const jx = J.search(m, 0, s, t)[2];
    if (jx > ax) worse += 1;
    else if (jx === ax) same += 1;
  }
}
H.check('JPS 의 연 노드 수가 A* 보다 많은 경우', worse, 0);
H.note('연 노드 수가 같은 경우 ' + same
       + '건 — 줄어드는 것은 연 노드지 훑는 칸이 아니다');

// ---- 강제 이웃 규칙 (SPEC §10.1)
const m2 = new T.TMap(5, 5);
for (let y = 0; y < 5; y += 1) {
  for (let x = 0; x < 5; x += 1) m2.setTerrain(x, y, T.DIRT);
}
m2.setTerrain(2, 1, T.ROCK);
H.checkTrue('(2,2) 로 동쪽으로 들어오면 (3,1) 이 강제 이웃',
            J.forced(m2, 2, 2, 1, 0, 0));
m2.setTerrain(2, 1, T.DIRT);
H.checkTrue('막힌 칸이 없으면 강제 이웃도 없다',
            !J.forced(m2, 2, 2, 1, 0, 0));

H.done();
