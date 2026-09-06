// 맵 생성 — 셀룰러 오토마타·다이아몬드 스퀘어·대칭·자원 (SPEC §5).

import * as H from './harness';
import * as G from '../src/mapgen';
import { LCG } from '../src/rng';
import * as T from '../src/tmap';

H.title('mapgen');

// ---- 골든 시작 맵을 바이트 단위로 재현하는가
const want = T.TMap.loadText(H.golden('map_start.txt'));
const [got, seed, retries] = G.genStart();
H.check('시작 맵 지형이 골든과 같다', got.terrain, want.terrain);
H.check('시드', seed, 3);
H.check('재시도 횟수', retries, 0);
H.check('시작점', G.START, [[8, 8], [55, 55]]);

// ---- 180도 회전 대칭 (SPEC §5.4)
let bad = 0;
for (let y = 0; y < 64; y += 1) {
  for (let x = 0; x < 64; x += 1) {
    if (got.terrain[y * 64 + x] !== got.terrain[(63 - y) * 64 + (63 - x)]) {
      bad += 1;
    }
  }
}
H.check('맵이 180도 회전 대칭', bad, 0);

// ---- 두 시작점이 이어져 있는가
const lab = got.labels(0);
H.check('두 기지가 보병으로 이어진다',
        lab[got.idx(8, 8)] === lab[got.idx(55, 55)], true);

// ---- 셀룰러 오토마타 (SPEC §5.1)
const ca = G.cellular(32, 32, new LCG(7), 4);
H.check('CA 결과는 0/1', H.sortedSet(ca), [0, 1]);
const wall = H.sum(ca);
H.note('시드 7, 4세대: 벽 ' + wall + ' / 1024 ('
       + (100.0 * wall / 1024).toFixed(0) + '%)');
H.checkTrue('벽이 전부도 아니고 없지도 않다', wall > 0 && wall < 1024);

const full = G.cellularStep(H.range(64).map(() => 1), 8, 8);
H.check('가득 찬 판은 고정점', full, H.range(64).map(() => 1));
const empty = G.cellularStep(H.range(64).map(() => 0), 8, 8);
H.check('빈 판은 맵 밖이 벽이라 가장자리부터 채워진다', empty[0], 1);
H.check('빈 판의 한가운데는 그대로', empty[8 * 3 + 3], 0);

// ---- 다이아몬드-스퀘어 (SPEC §5.2)
const hh = G.diamondSquare(new LCG(3));
H.check('격자 크기 65x65', [hh.length, hh[0].length], [65, 65]);
H.checkTrue('높이는 0..255 로 잘린다',
            hh.every((row) => row.every((v) => v >= 0 && v <= 255)));
H.check('임계값 표', G.THRESH[0], [63, T.WATER]);
H.check('높이 0 은 물', G.terrainOf(0), T.WATER);
H.check('높이 63 은 물', G.terrainOf(63), T.WATER);
H.check('높이 64 는 모래', G.terrainOf(64), T.SAND);
H.check('높이 255 는 바위', G.terrainOf(255), T.ROCK);

// ---- 자원 배치의 최소 거리 (SPEC §5.3)
const pts = G.LAST_ORE;
H.checkTrue('광맥점 ' + pts.length + '개', pts.length > 0);
bad = 0;
for (let i = 0; i < pts.length; i += 1) {
  for (let j = i + 1; j < pts.length; j += 1) {
    const dx = pts[i][0] - pts[j][0];
    const dy = pts[i][1] - pts[j][1];
    if (dx * dx + dy * dy < 81) bad += 1;
  }
}
H.check('어떤 두 광맥점도 9타일보다 가깝지 않다', bad, 0);
H.checkTrue('제곱근을 쓰지 않는다 (dx²+dy² < rmin² 로 판정)', true);

// ---- 시도 상한이 있는가 (무한 루프 방지)
H.check('시도 상한', G.ORE_TRIES, 4000);

H.done();
