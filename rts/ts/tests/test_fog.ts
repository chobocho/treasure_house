// 시야와 안개 — 참조 카운트와 4단계 렌더 (SPEC §14).

import * as H from './harness';
import * as CI from '../src/circle';
import * as C from '../src/const';
import * as FG from '../src/fog';
import { LCG } from '../src/rng';
import * as S from '../src/spatial';

H.title('fog');

const W = 64;
const HT = 64;

// 골든 10절과 같은 형식의 통계 — 가시 칸·합·최대·도수.
function report(fg: FG.Fog, p: number): [number, number, number, number[]] {
  const cnt = fg.count[p];
  const vis = cnt.filter((v) => v > 0).length;
  const tot = H.sum(cnt);
  const mx = cnt.length > 0 ? H.maxOf(cnt) : 0;
  const hist = new Array<number>(Math.max(3, mx + 1)).fill(0);
  for (const v of cnt) {
    if (v !== 0) hist[v] += 1;
  }
  return [vis, tot, mx, hist];
}

// ── 골든 10절 ───────────────────────────────────────────────────────────────
const fg = new FG.Fog(W, HT);
const UNITS: Array<[[number, number], number]> = [
  [[10, 10], 3], [[12, 11], 5], [[30, 30], 8]];
for (const [[x, y], r] of UNITS) fg.addSight(0, x, y, r);
let [vis, tot, mx, hist] = report(fg, 0);
H.check('초기 가시 칸·합·최대', [vis, tot, mx], [279, 307, 2]);
H.check('초기 도수 1·2', [hist[1], hist[2]], [251, 28]);

fg.removeSight(0, 10, 10, 3);
fg.addSight(0, 11, 10, 3);
[vis, tot, mx, hist] = report(fg, 0);
H.check('1번 유닛 이동 뒤', [vis, tot, mx, hist[1], hist[2]],
        [278, 307, 2, 249, 29]);

fg.removeSight(0, 30, 30, 8);
[vis, tot, mx, hist] = report(fg, 0);
H.check('3번 유닛 사망 뒤', [vis, tot, mx, hist[1], hist[2]],
        [81, 110, 2, 52, 29]);

fg.removeSight(0, 11, 10, 3);
fg.removeSight(0, 12, 11, 5);
H.check('전원 제거 후 카운트 합', H.sum(fg.count[0]), 0);
H.checkTrue('그래도 탐험 표시는 남는다', H.sum(fg.explored[0]) > 0);
H.note('증분 갱신이 정확히 0 으로 돌아온다 — 이것이 불변식 F 의 최소 조건이다');

// ── 평면은 플레이어마다 따로다 ──────────────────────────────────────────────
H.check('다른 플레이어의 카운트는 그대로 0', H.sum(fg.count[1]), 0);
H.check('다른 플레이어는 탐험도 0', H.sum(fg.explored[1]), 0);
H.check('플레이어 수는 MAX_PLAYER', fg.count.length, C.MAX_PLAYER);

// ── 가장자리 잘림 ───────────────────────────────────────────────────────────
const fg2 = new FG.Fog(W, HT);
fg2.addSight(0, 0, 0, 3);
H.check('(0,0) 반경 3 은 원의 1/4 만 맵 안', H.sum(fg2.count[0]),
        CI.offsets(3).filter(([dx, dy]) => dx >= 0 && dx < W
                                           && dy >= 0 && dy < HT).length);
H.check('맵 밖은 세지 않는다', H.maxOf(fg2.count[0]), 1);
fg2.removeSight(0, 0, 0, 3);
H.check('잘린 원도 정확히 0 으로 돌아온다', H.sum(fg2.count[0]), 0);
fg2.addSight(0, 5, 5, 0);
H.check('반경 0 은 자기 칸 하나', H.sum(fg2.count[0]), 1);
fg2.removeSight(0, 5, 5, 0);
H.check('카운트는 음수가 되지 않는다', H.minOf(fg2.count[0]), 0);
fg2.removeSight(0, 5, 5, 0);
H.check('없는 시야를 또 빼도 0 이다', H.minOf(fg2.count[0]), 0);

// ── 불변식 F — 무작위 이동 중 매 틱 전수 검증 ───────────────────────────────
const w = new S.World(W, HT);
const fg3 = new FG.Fog(W, HT);
const rand = new LCG(31);
const ents: number[] = [];
for (let k = 0; k < 12; k += 1) {
  const kind = [C.INF, C.ARCHER, C.TANK, C.HARV][k % 4];
  const x = 4 + rand.roll(56);
  const y = 4 + rand.roll(56);
  const i = S.index(w.spawn(k % 2, kind, x, y));
  fg3.addSight(w.owner[i], x, y, C.SIGHT[kind]);
  ents.push(i);
}
w.spawn(0, C.HQ, 20, 20);
fg3.addSight(0, 20, 20, C.SIGHT[C.HQ]);
let bad = 0;
const DXS = [0, 1, 1, 1, 0, -1, -1, -1];
const DYS = [-1, -1, 0, 1, 1, 1, 0, -1];
for (let t = 0; t < 120; t += 1) {
  for (const i of ents) {
    const d = rand.roll(8);
    const nx = Math.min(W - 1, Math.max(0, w.tx[i] + DXS[d]));
    const ny = Math.min(HT - 1, Math.max(0, w.ty[i] + DYS[d]));
    if (nx === w.tx[i] && ny === w.ty[i]) continue;
    const r = C.SIGHT[w.kind[i]];
    fg3.removeSight(w.owner[i], w.tx[i], w.ty[i], r);     // 먼저 빼고
    w.moveTile(i, nx, ny);
    fg3.addSight(w.owner[i], nx, ny, r);                  // 나중에 더한다
  }
  bad += fg3.recount(w);
}
H.check('불변식 F — 120틱 × 4플레이어 전수 재계산 불일치', bad, 0);

const dead = ents[0];
fg3.removeSight(w.owner[dead], w.tx[dead], w.ty[dead], C.SIGHT[w.kind[dead]]);
w.kill(w.handle(dead));
H.check('죽으면 remove 만 한다 — 그 뒤에도 불변식 F', fg3.recount(w), 0);

// 일부러 어긋뜨리면 recount 가 잡아내는가
fg3.count[0][7 * W + 7] += 1;
H.check('어긋난 칸을 recount 가 센다', fg3.recount(w), 1);
fg3.count[0][7 * W + 7] -= 1;
H.check('되돌리면 다시 0', fg3.recount(w), 0);
H.note('recount 는 고치지 않고 세기만 한다 — 고치면 버그가 조용히 묻힌다');

// ── SPEC §14.4 4단계 ────────────────────────────────────────────────────────
const fg4 = new FG.Fog(16, 16);
H.check('아무것도 안 봤으면 0(미탐험)', fg4.level(0, 8, 8), 0);
fg4.addSight(0, 8, 8, 3);
H.check('보고 있으면 3(가시)', fg4.level(0, 8, 8), 3);
H.check('원 밖은 아직 0', fg4.level(0, 8, 15), 0);
fg4.removeSight(0, 8, 8, 3);
H.check('시야가 빠지면 1(탐험됨)', fg4.level(0, 8, 8), 1);
fg4.addSight(0, 8, 8, 1);
H.check('가시 칸에 인접한 탐험 칸은 2(경계)', fg4.level(0, 10, 8), 2);
H.check('가시 칸에서 두 칸 떨어진 탐험 칸은 1', fg4.level(0, 11, 8), 1);
H.check('가시 칸 자신은 3', fg4.level(0, 8, 9), 3);
H.check('맵 밖은 0', fg4.level(0, -1, 0), 0);
const lv: number[] = [];
for (let y = 0; y < 16; y += 1) {
  for (let x = 0; x < 16; x += 1) lv.push(fg4.level(0, x, y));
}
H.check('단계는 0..3 뿐', H.sortedSet(lv), [0, 1, 2, 3]);

// ── SPEC §14.2 비트 플레인 (저장·전송용) ────────────────────────────────────
const packed = fg4.packBits(0);
H.check('16×16 = 256칸이 32바이트로 접힌다', packed.length, 32);
H.checkTrue('바이트 범위', packed.every((v) => v >= 0 && v <= 255));
const fg5 = new FG.Fog(16, 16);
fg5.unpackBits(0, packed);
H.check('풀면 원래 탐험 평면', fg5.explored[0], fg4.explored[0]);
H.check('한 칸도 안 본 평면은 전부 0', new FG.Fog(8, 8).packBits(0),
        H.range(8).map(() => 0));
const full = new FG.Fog(8, 8);
for (let k = 0; k < 64; k += 1) full.explored[0][k] = 1;
H.check('전부 본 평면은 전부 255', full.packBits(0), H.range(8).map(() => 255));
const odd = new FG.Fog(4, 3);                // 12칸 — 8의 배수가 아니다
odd.explored[0][11] = 1;
H.check('8의 배수가 아니면 마지막 바이트를 0으로 채운다', odd.packBits(0).length, 2);
H.check('마지막 칸은 마지막 바이트의 3번 비트', odd.packBits(0), [0, 8]);

H.done();
