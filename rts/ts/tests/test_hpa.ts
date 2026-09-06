// 계층 경로 탐색 — 최적이 아니라는 것을 숫자로 남긴다 (SPEC §9).

import * as H from './harness';
import * as A from '../src/hpa';
import * as P from '../src/path';
import * as T from '../src/tmap';

H.title('hpa');

const MAPS = H.range(1, 7).map((i) => T.TMap.loadText(H.golden('map_' + i + '.txt')));

// ---- 골든 8절의 HPA* 열과 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 8. HPA* 와 JPS ==') + 2;
let bad = 0;
let n = 0;
const ratios: number[] = [];
while (rows[i].trim() !== '' && rows[i].indexOf('JPS 비용') !== 0) {
  const v = H.ints(rows[i].replace(/\(/g, ' ').replace(/\)/g, ' ')
    .replace(/,/g, ' ').replace(/->/g, ' '));
  const [mi, sx, sy, tx, ty, , , , wh, wr] = v;
  const m = MAPS[mi - 1];
  const [c] = A.search(m, 0, [sx, sy], [tx, ty]);
  if (c !== wh) {
    bad += 1;
    H.note('맵' + mi + ' (' + sx + ',' + sy + ')->(' + tx + ',' + ty + ') 기대 '
           + wh + ' 실제 ' + c);
  }
  if (wr > 0) ratios.push(wr);
  n += 1;
  i += 1;
}
H.check('골든 8절 ' + n + '줄의 HPA* 비용', bad, 0);
H.note('최적 대비 ' + H.minOf(ratios) + '~' + H.maxOf(ratios) + ' 천분율 (평균 '
       + Math.floor(H.sum(ratios) / ratios.length)
       + ') — 논문의 "1%" 를 옮겨 적지 않는다');

// ---- HPA* 는 최적 이상이다 (아래로 내려갈 수는 없다)
bad = 0;
for (const m of MAPS) {
  for (const [s, t] of m.pairs) {
    const a = P.astar(m, 0, s, t)[0];
    const [c] = A.search(m, 0, s, t);
    if (a > 0 && c > 0 && c < a) {
      bad += 1;
      H.note('HPA* 가 A* 보다 싸다?! ' + JSON.stringify(s) + ' '
             + JSON.stringify(t) + ' ' + c + ' < ' + a);
    }
  }
}
H.check('HPA* 비용 >= A* 비용', bad, 0);

// ---- 클러스터와 전이
const m1 = MAPS[0];
H.check('클러스터 한 변', A.CLUSTER, 8);
H.check('32x32 맵의 클러스터 수',
        Math.floor(m1.w / 8) * Math.floor(m1.h / 8), 16);
H.check('cluster_of(0,0)', A.clusterOf(0, 0), [0, 0]);
H.check('cluster_of(8,8)', A.clusterOf(8, 8), [1, 1]);
const ents = A.entrances(m1, 0);
H.checkTrue('빈 들판에도 전이가 있다 (' + ents.length + '개)', ents.length > 0);
H.checkTrue('전이는 이웃한 두 칸을 잇는다',
            ents.every(([a, b]) => Math.abs(a[0] - b[0])
                                   + Math.abs(a[1] - b[1]) === 1));

// ---- 구간 길이에 따른 전이 개수 (SPEC §9.2)
const id = (v: number): number => v;
H.check('길이 1 구간은 전이 1개', A.place([5], id).length, 1);
H.check('길이 5 구간은 전이 1개', A.place([1, 2, 3, 4, 5], id).length, 1);
H.check('길이 5 구간의 위치는 가운데', A.place([1, 2, 3, 4, 5], id), [3]);
H.check('길이 6 구간은 양 끝 2개', A.place([1, 2, 3, 4, 5, 6], id), [1, 6]);
H.check('빈 구간은 전이 없음', A.place([], id), []);

// ---- 정련 (SPEC §9.4)
const m3 = MAPS[3];
const [s3, t3] = m3.pairs[0];
const [, nodes] = A.search(m3, 0, s3, t3);
const tiles = A.refine(m3, 0, nodes);
H.checkTrue('정련 결과가 출발에서 시작한다',
            tiles[0] === s3[1] * m3.w + s3[0]);
H.checkTrue('정련 결과가 도착에서 끝난다',
            tiles[tiles.length - 1] === t3[1] * m3.w + t3[0]);

// ---- 추상 그래프는 맵 버전마다 다시 짓는다
const a1 = A.abstract(m1, 0);
const a2 = A.abstract(m1, 0);
H.check('같은 버전이면 같은 그래프 객체', a1 === a2, true);
m1.setTerrain(4, 4, T.ROCK);
const a3 = A.abstract(m1, 0);
H.check('버전이 바뀌면 다시 짓는다', a3 === a1, false);
m1.setTerrain(4, 4, T.DIRT);

H.done();
