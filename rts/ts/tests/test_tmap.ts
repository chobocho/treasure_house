// 지형 맵 — 오토타일·통행·연결 성분·RLE (SPEC §4).

import * as H from './harness';
import * as F from '../src/fixed';
import * as T from '../src/tmap';

H.title('tmap');

const m = new T.TMap(8, 8);

// ---- 좌표와 경계 (SPEC §4.2)
H.check('idx(3,2)', m.idx(3, 2), 2 * 8 + 3);
H.check('in_map(0,0)', m.inMap(0, 0), true);
H.check('in_map(-1,0)', m.inMap(-1, 0), false);
H.check('맵 밖은 ROCK', m.terrainAt(-1, 0), T.ROCK);
H.check('맵 밖은 ROCK (오른쪽)', m.terrainAt(8, 0), T.ROCK);

// ---- 통행 비트 (SPEC §4.3)
m.setTerrain(1, 1, T.DIRT);
m.setTerrain(2, 1, T.WATER);
m.setTerrain(3, 1, T.HILL);
m.setTerrain(4, 1, T.ORE);
H.check('흙은 보병 통행', m.walkable(1, 1, 0), true);
H.check('흙은 차량 통행', m.walkable(1, 1, 1), true);
H.check('물은 통행 불가', m.walkable(2, 1, 0), false);
H.check('언덕은 보병만', m.walkable(3, 1, 0), true);
H.check('언덕은 차량 불가', m.walkable(3, 1, 1), false);
H.check('광맥은 통행 가능', m.walkable(4, 1, 0), true);
H.check('광맥은 건설 불가', m.buildable(4, 1), false);
H.check('흙은 건설 가능', m.buildable(1, 1), true);
m.occupy(1, 1, true);
H.check('점유되면 통행 불가', m.walkable(1, 1, 0), false);
H.check('점유는 경로 탐색이 보지 않는 비트', T.OCC_BIT, 3);
m.occupy(1, 1, false);
H.check('점유 해제', m.walkable(1, 1, 0), true);

// ---- 오토타일 정규화 (SPEC §4.4) — 골든 5절과 대조
const rows = H.golden('prim.txt').split('\n');
let i = rows.indexOf('== 5. 오토타일 ==');
H.check('클래스 개수', T.CLASS_COUNT,
        parseInt(H.fields(rows[i + 1])[1].replace(/개$/, ''), 10));
let bad = 0;
for (let r = 0; r < 16; r += 1) {
  const want = H.ints(rows[i + 3 + r]);
  const got = H.range(16).map((c) => T.canonIndex(T.canon(r * 16 + c)));
  if (!H.deepEq(want, got)) {
    bad += 1;
    H.note('행 ' + r + ' 기대 ' + JSON.stringify(want)
           + ' 실제 ' + JSON.stringify(got));
  }
}
H.check('256개 마스크의 정규화 인덱스가 골든과 같다', bad, 0);

// 방향 비트 — `1 << k` 대신 값을 그대로 적는다 (SPEC §1.1)
const N = 1;
const NE = 2;
const E = 4;
const W = 64;
H.check('모서리는 양옆이 있어야 산다', T.canon(NE), 0);
H.check('N+E 가 있으면 NE 가 산다', T.canon(N + E + NE), N + E + NE);
H.check('N 만 없으면 NE 는 죽는다', T.canon(E + NE), E);
H.check('canon 은 멱등', T.canon(T.canon(255)), T.canon(255));

// ---- 이웃 마스크
const m2 = new T.TMap(5, 5);
for (let y = 0; y < 5; y += 1) {
  for (let x = 0; x < 5; x += 1) m2.setTerrain(x, y, T.SAND);
}
m2.setTerrain(2, 2, T.DIRT);
H.check('혼자 있는 칸의 마스크는 0', m2.mask(2, 2), 0);
m2.setTerrain(2, 1, T.DIRT);
H.check('북쪽만 같으면 마스크는 N', m2.mask(2, 2), N);
H.check('가장자리 칸은 맵 밖을 ROCK 으로 본다',
        F.bit(m2.mask(0, 0), 6) * W, 0);

// ---- 4모서리 마스크 (SPEC §4.5)
H.check('corner_mask 는 0..15', T.cornerMask([0, 0, 0, 0]), 0);
H.check('corner_mask 전부', T.cornerMask([1, 1, 1, 1]), 15);
H.check('corner_mask 좌상단만', T.cornerMask([1, 0, 0, 0]), 1);

// ---- 연결 성분 (SPEC §4.6)
const m3 = new T.TMap(8, 8);
for (let y = 0; y < 8; y += 1) {
  for (let x = 0; x < 8; x += 1) m3.setTerrain(x, y, T.WATER);
}
for (const [x, y] of [[1, 1], [2, 1], [1, 2], [5, 5], [6, 5]]) {
  m3.setTerrain(x, y, T.DIRT);
}
const lab = m3.labels(0);
H.check('두 덩어리는 다른 라벨',
        lab[m3.idx(1, 1)] !== lab[m3.idx(5, 5)], true);
H.check('같은 덩어리는 같은 라벨', lab[m3.idx(1, 1)], lab[m3.idx(2, 1)]);
H.check('대각으로도 이어진다', lab[m3.idx(1, 1)], lab[m3.idx(1, 2)]);
H.check('물은 라벨 -1', lab[m3.idx(0, 0)], -1);
const v0 = m3.version;
m3.setTerrain(3, 3, T.DIRT);
H.checkTrue('지형을 고치면 버전이 오른다', m3.version > v0);
H.check('라벨은 다시 계산된다', m3.labels(0)[m3.idx(3, 3)] >= 0, true);

// ---- 차량용 라벨은 언덕에서 끊긴다
const m4 = new T.TMap(5, 1);
for (let x = 0; x < 5; x += 1) m4.setTerrain(x, 0, T.DIRT);
m4.setTerrain(2, 0, T.HILL);
H.check('보병은 이어진다', m4.labels(0)[0], m4.labels(0)[4]);
H.check('차량은 끊긴다', m4.labels(1)[0] !== m4.labels(1)[4], true);

// ---- RLE 왕복 (SPEC §4.7)
const m5 = new T.TMap(64, 64);
let r = 1;
for (let y = 0; y < 64; y += 1) {
  for (let x = 0; x < 64; x += 1) {
    r = H.lcg31(r);
    m5.setTerrain(x, y, r % 8);
  }
}
const blob = m5.saveRle();
const m6 = T.TMap.loadRle(blob);
H.check('RLE 왕복: 지형', m6.terrain, m5.terrain);
H.check('RLE 왕복: 통행', m6.pass_, m5.pass_);
H.check('헤더', blob.slice(0, 4), F.ascii('RTSM'));
H.checkTrue('CRC 가 붙어 있다 (' + blob.length + '바이트)', blob.length > 6);
const broken = blob.slice();
broken[10] = (broken[10] + 1) % 256;
try {
  T.TMap.loadRle(broken);
  H.check('CRC 가 깨지면 터져야 한다', 'no raise', 'raise');
} catch (e) {
  H.check('CRC 가 깨지면 터져야 한다', 'raise', 'raise');
}

// ---- 골든 맵 읽기
const g = T.TMap.loadText(H.golden('map_1.txt'));
H.check('map_1 크기', [g.w, g.h], [32, 32]);
H.check('가장자리는 막혀 있다', g.walkable(0, 0, 0), false);
H.check('안쪽은 통행 가능', g.walkable(1, 1, 0), true);
H.check('시험 쌍 4개', g.pairs.length, 4);
const gs = T.TMap.loadText(H.golden('map_start.txt'));
H.check('시작 맵 크기', [gs.w, gs.h], [64, 64]);
H.check('시작점 2개', gs.starts, [[8, 8], [55, 55]]);
H.check('시작점 주변은 흙', gs.terrainAt(8, 8), T.DIRT);

// ── SPEC §4.3 건물이 선 칸 ──────────────────────────────────────────────────
const bm = new T.TMap(4, 4);
for (let y = 0; y < 4; y += 1) {
  for (let x = 0; x < 4; x += 1) bm.setTerrain(x, y, T.DIRT);
}
const bv = bm.version;
bm.setBuilding(1, 1, true);
H.check('건물 칸은 보병·차량 통행 불가',
        [bm.passableTerrain(1, 1, 0), bm.passableTerrain(1, 1, 1)],
        [false, false]);
H.check('건물 칸은 건설도 불가', bm.buildable(1, 1), false);
H.checkTrue('건물은 version 을 올린다 — 경로 캐시가 무효가 된다',
            bm.version > bv);
bm.setBuilding(1, 1, false);
H.check('철거하면 통행이 돌아온다', bm.passableTerrain(1, 1, 0), true);
H.check('철거하면 점유 비트도 내려간다', bm.buildable(1, 1), true);
bm.setBuilding(2, 2, true);
bm.setTerrain(2, 2, T.RUBBLE);
H.check('잔해로 바꾸는 것만으로 통행이 복구된다 (§4.3)',
        bm.passableTerrain(2, 2, 0), true);

H.done();
