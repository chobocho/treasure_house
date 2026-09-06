// 화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).

import * as H from './harness';
import * as C from '../src/const';
import * as RS from '../src/raster';
import * as RD from '../src/render';
import * as SIM from '../src/sim';
import * as T from '../src/tmap';

H.title('render');

const PAL = RS.buildPalette();
const LIGHT = RS.buildLight(PAL);

function startSim(): SIM.Sim {
  const m0 = T.TMap.loadText(H.golden('map_start.txt'));
  const s0 = new SIM.Sim(m0, 1, 2);
  s0.setupStart();
  return s0;
}

// ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
const m = T.TMap.loadText(H.golden('map_start.txt'));
const v = new RD.View();
H.check('처음 카메라는 (0,0)', [v.camX, v.camY], [0, 0]);
v.move(m, -100, -100);
H.check('왼쪽 위로 넘어가지 않는다', [v.camX, v.camY], [0, 0]);
v.move(m, 10000, 10000);
H.check('오른쪽 아래 한계는 맵 - 뷰포트', [v.camX, v.camY],
        [C.MAP_W * C.TILE - C.VIEW_W, C.MAP_H * C.TILE - C.VIEW_H]);
H.check('그 값은 768', v.camX, 768);
const v2 = new RD.View();
v2.centerOn(m, 32, 32);
H.check('가운데 정렬', [v2.camX, v2.camY],
        [32 * 16 - Math.floor(C.VIEW_W / 2), 32 * 16 - Math.floor(C.VIEW_H / 2)]);
v2.centerOn(m, 0, 0);
H.check('가장자리에서는 클램프', [v2.camX, v2.camY], [0, 0]);
H.check('카메라는 정수 픽셀', Number.isInteger(v2.camX), true);

const v3 = new RD.View();
v3.camX = 100;
v3.camY = 50;
H.check('첫 타일과 오프셋', v3.firstTile(), [6, 3, 4, 2]);
H.check('그릴 타일 수는 17열', RD.TILES_X, Math.floor(C.VIEW_W / C.TILE) + 1);
H.check('가장자리 스크롤 — 왼쪽 8px 안', RD.edgeScroll(3, 100),
        [-RD.EDGE_SPEED, 0]);
H.check('오른쪽', RD.edgeScroll(C.VIEW_W - 2, 100), [RD.EDGE_SPEED, 0]);
H.check('위', RD.edgeScroll(100, 2), [0, -RD.EDGE_SPEED]);
H.check('가운데는 안 움직인다', RD.edgeScroll(100, 100), [0, 0]);
H.check('패널 위에서는 안 움직인다', RD.edgeScroll(300, 100), [0, 0]);

// ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
const s = startSim();
const order = RD.yOrder(s.w);
const keys = order.map((i) => RD.sortKey(s.w, i));
H.check('발밑 y · x · 핸들 순', keys, H.sortedTuples(keys));
let aliveN = 0;
for (let i = 1; i < C.MAX_ENT; i += 1) {
  if (s.w.alive[i] !== 0) aliveN += 1;
}
H.check('살아 있는 것만', order.length, aliveN);
const std = order.slice();
std.sort((a, b) => H.cmpArr(RD.sortKey(s.w, a), RD.sortKey(s.w, b)));
H.check('삽입 정렬이 표준 정렬과 같은 답을 낸다', order, std);
H.check('키는 전순서 — 같은 키가 둘일 수 없다',
        new Set(keys.map((k) => k.join(','))).size, keys.length);

// ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
H.check('64 맵을 64 픽셀에 — 한 타일이 한 픽셀', RD.minimapNearest(m, 10, 20),
        m.terrain[20 * m.w + 10]);
H.check('축소 코드도 있다 (128 맵을 대비)', RD.minimapNearest(m, 0, 0),
        m.terrain[0]);
const maj = RD.minimapMajority(m, 5, 5);
H.checkTrue('다수결도 같은 크기에서는 같은 답',
            maj === RD.minimapNearest(m, 5, 5));
H.check('미니맵 클릭의 역변환', RD.minimapToTile(32, 48), [32, 48]);
const vv = new RD.View();
const [mtx, mty] = RD.minimapToTile(32, 32);
vv.centerOn(m, mtx, mty);
H.check('클릭한 타일이 뷰포트 중앙에 온다',
        [vv.camX + Math.floor(C.VIEW_W / 2), vv.camY + Math.floor(C.VIEW_H / 2)],
        [32 * 16, 32 * 16]);

// ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
const fb = new RS.Frame();
RD.draw(fb.fb, s, new RD.View(), 0, PAL, LIGHT, 0, [], '');
H.check('프레임버퍼를 다 채운다',
        fb.fb.filter((val) => val === 0).length < 320 * 200, true);
H.check('패널 영역에도 그린다',
        H.maxOf(fb.fb.slice(10 * 320 + C.PANEL_X, 10 * 320 + 320)) > 0, true);
H.check('하단 바에도 그린다',
        H.maxOf(fb.fb.slice((C.BAR_Y + 10) * 320,
                            (C.BAR_Y + 10) * 320 + 256)) > 0, true);

const fb2 = new RS.Frame();
RD.draw(fb2.fb, s, new RD.View(), 0, PAL, LIGHT, 0, [], '');
H.check('같은 상태면 같은 그림', fb.fb, fb2.fb);
const ppm = RS.toPpm(fb.fb, PAL);
H.check('PPM 192,015바이트', ppm.length, 192015);

// ── 안개 ────────────────────────────────────────────────────────────────────
const view = new RD.View();
view.centerOn(m, 8, 8);                      // 0번 기지
const lit = new RS.Frame();
RD.draw(lit.fb, s, view, 0, PAL, LIGHT, 0, [], '');
const dark = new RS.Frame();
RD.draw(dark.fb, s, view, 0, PAL, LIGHT, 1, [], '');   // 1번 시야로 같은 곳
H.checkTrue('남의 시야로 보면 어둡다',
            dark.fb.slice(0, C.VIEW_H * 320).filter((val) => val === 0).length
            > lit.fb.slice(0, C.VIEW_H * 320).filter((val) => val === 0).length);
H.check('미탐험은 완전한 검정', dark.fb[10 * 320 + 10], 0);

const enemyVisible = RD.visibleEntities(s, 1);
H.check('1번 플레이어는 0번 유닛을 못 본다',
        enemyVisible.filter((i) => s.w.owner[i] === 0), []);
const own = RD.visibleEntities(s, 0);
H.checkTrue('제 유닛은 본다', own.length > 0);
H.note('명암표는 어둡게 만들 뿐이라 유닛 숨기기는 2단계에서 걸러야 한다');

// ── 선택 표시와 체력바 ──────────────────────────────────────────────────────
const hq = H.range(1, C.MAX_ENT).filter(
  (i) => s.w.alive[i] !== 0 && s.w.owner[i] === 0 && s.w.kind[i] === C.HQ)[0];
const fb3 = new RS.Frame();
RD.draw(fb3.fb, s, view, 0, PAL, LIGHT, 0, [s.w.handle(hq)], '');
H.checkTrue('선택하면 그림이 달라진다', !H.deepEq(fb3.fb, lit.fb));
s.w.hp[hq] = Math.floor(C.HP[C.HQ] / 2);
const fb4 = new RS.Frame();
RD.draw(fb4.fb, s, view, 0, PAL, LIGHT, 0, [s.w.handle(hq)], '');
H.checkTrue('체력이 줄면 체력바도 달라진다', !H.deepEq(fb4.fb, fb3.fb));

// ── 하단 바 ─────────────────────────────────────────────────────────────────
const fb5 = new RS.Frame();
RD.draw(fb5.fb, s, view, 0, PAL, LIGHT, 0, [], 'BASE UNDER ATTACK');
H.checkTrue('메시지를 쓰면 하단 바가 달라진다',
            !H.deepEq(fb5.fb.slice(C.BAR_Y), fb.fb.slice(C.BAR_Y)));
H.check('자릿수는 고정 폭', RD.creditsText(50), '   50');
H.check('큰 수도 다섯 자리', RD.creditsText(12345), '12345');
H.check('넘치면 잘라 붙인다', RD.creditsText(1234567), '99999');

// ── 팔레트 사이클은 그림을 바꾸지 않는다 (팔레트만 바뀐다) ──────────────────
const fb6 = new RS.Frame();
const fb7 = new RS.Frame();
RD.draw(fb6.fb, s, view, 0, PAL, LIGHT, 0, [], '');
RD.draw(fb7.fb, s, view, 3, PAL, LIGHT, 0, [], '');
H.check('사이클 위상은 프레임버퍼를 바꾸지 않는다', fb7.fb, fb6.fb);
H.note('물 애니메이션은 팔레트만 돌린다 — 그래서 공짜다');

H.done();
