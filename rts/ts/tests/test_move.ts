// 이동·예약·대형 (SPEC §13).
//
//    핵심은 불변식 R 이다 — 어떤 타일도 두 엔티티에게 동시에 예약되지 않는다.
//    무작위 시나리오를 오래 돌려 매 틱 확인한다.

import * as H from './harness';
import * as C from '../src/const';
import * as F from '../src/fixed';
import * as M from '../src/move';
import { LCG } from '../src/rng';
import * as S from '../src/spatial';
import * as T from '../src/tmap';

H.title('move');

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

function worldOf(m: T.TMap): S.World {
  return new S.World(m.w, m.h);
}

// ── SPEC §13.1 걸음 진행량 ──────────────────────────────────────────────────
const sp = C.SPEED[C.INF];
const st = M.stepAmount(sp, 0);            // 북 = 직선
const di = M.stepAmount(sp, 1);            // 북동 = 대각
H.check('직선 진행량 = fpdiv(speed, fp(TILE))', st, F.fpDiv(sp, F.fp(C.TILE)));
H.check('대각 진행량 = 직선 × FP_DIAG', di, F.fpMul(st, F.FP_DIAG));
H.check('대각/직선 = 1/√2 (만분율)', F.floordiv(di * 10000, st), 7070);
H.note('보정을 빼면 대각이 √2 = 1.414배 빨라진다 — 41% 빠른 지그재그 버그');
H.check('네 직선 방향의 진행량이 같다',
        [0, 2, 4, 6].map((d) => M.stepAmount(sp, d)), [st, st, st, st]);
H.check('네 대각 방향의 진행량이 같다',
        [1, 3, 5, 7].map((d) => M.stepAmount(sp, d)), [di, di, di, di]);
H.check('속도 0 이면 진행량 0', M.stepAmount(0, 0), 0);

// ── 정리 13.1 — 화면상 픽셀 속도가 방향과 무관한가 ──────────────────────────
// 유닛 한 기를 목표까지 걷게 하고 걸린 틱 수를 돌려준다.
function walk(rowsIn: string[], sx: number, sy: number, gx: number, gy: number,
              kind = C.INF): number {
  const m = grid(rowsIn);
  const w = worldOf(m);
  const mv = new M.Movement(w, m);
  const h = w.spawn(0, kind, sx, sy);
  const i = S.index(h);
  mv.claim(i);
  mv.order(i, gx, gy);
  let t = 0;
  while (!(w.tx[i] === gx && w.ty[i] === gy) && t < 2000) {
    mv.step();
    t += 1;
  }
  return t;
}

const tStr = walk(H.range(3).map(() => '..........'), 0, 1, 8, 1);
const tDia = walk(H.range(10).map(() => '..........'), 0, 0, 8, 8);
// 픽셀 거리: 직선 8타일 = 128px, 대각 8타일 = 128*√2 = 181.02px
const rTicks = F.floordiv(tDia * 1000, tStr);
H.checkTrue('대각 8칸의 틱수/직선 8칸의 틱수 ≈ √2 (' + rTicks + '/1000)',
            Math.abs(rTicks - 1414) <= 60);
H.note('틱은 정수라 걸음마다 최대 1틱이 남는다 — 그 오차가 위의 여유폭이다');

// ── SPEC §13.1 화면 위치는 파생값 ───────────────────────────────────────────
let m = grid(['....', '....', '....', '....']);
let w = worldOf(m);
let mv = new M.Movement(w, m);
let h = w.spawn(0, C.INF, 1, 1);
let i = S.index(h);
mv.claim(i);
H.check('서 있으면 타일 좌표 그대로', M.posOf(w, m, i),
        [F.fp(1 * C.TILE), F.fp(1 * C.TILE)]);
w.to_t[i] = 1 * m.w + 2;
w.prog[i] = F.FP_HALF;
H.check('동쪽으로 절반 왔으면 x 는 한 타일의 절반',
        M.posOf(w, m, i), [F.fp(16) + F.fp(8), F.fp(16)]);
w.prog[i] = F.FP_ONE;
H.check('진행률 1 이면 도착 타일 위', M.posOf(w, m, i), [F.fp(32), F.fp(16)]);
w.to_t[i] = w.from_t[i];
w.prog[i] = 0;

// ── SPEC §13.2 예약 불변식 ──────────────────────────────────────────────────
H.check('생성 시 자기 칸을 예약한다', mv.resv[1 * m.w + 1], h);
H.check('예약이 남의 것이면 실패', mv.reserve(1 * m.w + 1, h + 256), false);
H.check('제 예약을 다시 잡는 것은 성공', mv.reserve(1 * m.w + 1, h), true);
H.check('빈 칸 예약은 성공', mv.reserve(0, h), true);
mv.release(0, h);
H.check('반납하면 0', mv.resv[0], 0);
mv.release(0, h);
H.check('두 번 반납해도 조용하다', mv.resv[0], 0);

const bh = w.spawn(1, C.HQ, 2, 2);
mv.claim(S.index(bh));
H.check('건물은 발자국 9칸을 전부 예약한다',
        [0, 1].map((dy) => [0, 1].map((dx) => mv.resv[(2 + dy) * m.w + (2 + dx)]))
          .reduce((p, c) => p.concat(c), []),
        [bh, bh, bh, bh]);
H.note('3x3 이지만 맵이 4x4 라 오른쪽·아래 한 줄은 맵 밖이다');

// ── 걸음 중에는 두 칸을 쥔다 ────────────────────────────────────────────────
m = grid(['.....', '.....', '.....']);
w = worldOf(m);
mv = new M.Movement(w, m);
h = w.spawn(0, C.INF, 0, 1);
i = S.index(h);
mv.claim(i);
mv.order(i, 4, 1);
mv.step();
H.check('걸음을 시작하면 두 칸', mv.resv.filter((v) => v === h).length, 2);
H.check('진행 중 tx 는 아직 출발 타일', [w.tx[i], w.ty[i]], [0, 1]);
while (w.prog[i] !== 0) mv.step();
H.check('걸음이 끝나면 다시 한 칸', mv.resv.filter((v) => v === h).length, 1);
H.check('타일이 넘어갔다', [w.tx[i], w.ty[i]], [1, 1]);
H.check('넘은 사실이 crossed 에 남는다 — sim 7단계의 시야 갱신이 이것만 본다',
        mv.crossed, [[i, 1 * m.w + 0, 1 * m.w + 1]]);
mv.step();
H.check('crossed 는 매 틱 비운다', mv.crossed, []);

// ── 무작위 시나리오에서 불변식 R 을 매 틱 확인 ──────────────────────────────
const ROWS = [
  '................',
  '..####....####..',
  '..#..#....#..#..',
  '..####....####..',
  '................',
  '....########....',
  '................',
  '..####....####..',
  '..#..#....#..#..',
  '..####....####..',
  '................',
  '................',
];
m = grid(ROWS);
w = worldOf(m);
mv = new M.Movement(w, m);
const rand = new LCG(7);
const free: number[] = [];
for (let j = 0; j < m.w * m.h; j += 1) {
  if (m.passableTerrain(j % m.w, Math.floor(j / m.w), 0)) free.push(j);
}
const units: number[] = [];
for (let k = 0; k < 24; k += 1) {
  let j = 0;
  for (;;) {
    j = free[rand.roll(free.length)];
    if (mv.resv[j] === 0) break;
  }
  const hh = w.spawn(rand.roll(2), k % 2 !== 0 ? C.INF : C.TANK,
                     j % m.w, Math.floor(j / m.w));
  mv.claim(S.index(hh));
  units.push(S.index(hh));
}
const startPos = new Map<number, [number, number]>();
for (const u of units) startPos.set(u, [w.tx[u], w.ty[u]]);
let viol = 0;
let overlap = 0;
let selfown = 0;
for (let tick = 0; tick < 600; tick += 1) {
  if (tick % 50 === 0) {
    for (const u of units) {
      const j = free[rand.roll(free.length)];
      mv.order(u, j % m.w, Math.floor(j / m.w));
    }
  }
  mv.step();
  const seen = new Map<number, number>();
  for (const u of units) {
    for (const tile of [w.from_t[u], w.to_t[u]]) {
      const hh = w.handle(u);
      if (mv.resv[tile] !== hh) selfown += 1;
      if (seen.has(tile) && seen.get(tile) !== u) viol += 1;
      seen.set(tile, u);
    }
  }
  const occ = units.map((u) => w.ty[u] * m.w + w.tx[u]);
  if (new Set(occ).size !== occ.length) overlap += 1;
}
H.check('불변식 R — 600틱 동안 한 칸을 둘이 예약한 적', viol, 0);
H.check('제가 선 칸은 늘 제 예약이다', selfown, 0);
H.check('두 유닛이 같은 타일에 선 적', overlap, 0);
H.checkTrue('24기 중 20기 이상이 실제로 자리를 옮겼다',
            units.filter((u) => {
              const sp0 = startPos.get(u) as [number, number];
              return w.tx[u] !== sp0[0] || w.ty[u] !== sp0[1];
            }).length >= 20);
H.check('예약 수 == 서 있는 칸 + 걷는 중인 칸',
        mv.resv.filter((v) => v !== 0).length,
        units.length + units.filter((u) => w.prog[u] > 0).length);

// ── SPEC §13.3 막힘과 교착 ──────────────────────────────────────────────────
m = grid(['#####', '.....', '#####']);       // 폭 1 통로
w = worldOf(m);
mv = new M.Movement(w, m);
let ha = w.spawn(0, C.INF, 0, 1);
let hb = w.spawn(1, C.INF, 4, 1);            // 다른 플레이어 — 밀어내지 않는다
let ia = S.index(ha);
let ib = S.index(hb);
mv.claim(ia);
mv.claim(ib);
mv.order(ia, 4, 1);
mv.order(ib, 0, 1);
let rep = 0;
let give = 0;
for (let t = 0; t < 400; t += 1) {
  mv.step();
  if (mv.blocked[ia] === M.REPATH_TICKS) rep += 1;
  if (mv.goal[ia] < 0 && give === 0) give = t;
}
H.checkTrue('좁은 통로에서 마주 오면 ' + give + '틱에 포기한다 (교착 해소)',
            give > 0);
H.checkTrue('포기 전에 재탐색을 시도한다', rep > 0);
H.check('포기하면 경로도 비운다', mv.path[ia], []);
H.note('이것은 해결이 아니라 포기다 — 협상 기반 재배치는 이 엔진 밖이다');

// ── 밀어내기: 정지한 아군은 비켜 준다 ───────────────────────────────────────
m = grid(['.....', '.....', '.....']);
w = worldOf(m);
mv = new M.Movement(w, m);
ha = w.spawn(0, C.INF, 0, 1);
hb = w.spawn(0, C.INF, 1, 1);                // 같은 플레이어, 정지 상태
ia = S.index(ha);
ib = S.index(hb);
mv.claim(ia);
mv.claim(ib);
mv.order(ia, 4, 1);
H.check('진행 방향(E)의 반대 W 부터 시계로 훑는다 — W 는 밀 유닛이 쥐었으니 NW(7)',
        M.pushDir(mv, ib, 2), 7);
for (let t = 0; t < 60; t += 1) {
  mv.step();
  if (!(w.tx[ib] === 1 && w.ty[ib] === 1)) break;
}
H.checkTrue('정지한 아군은 밀려난다', !(w.tx[ib] === 1 && w.ty[ib] === 1));
H.check('밀려간 칸은 NW', [w.tx[ib], w.ty[ib]], [0, 0]);
H.note('훑는 순서 = 반대 방향에서 시계 방향 — 세 언어가 같은 칸을 골라야 한다');

// ── SPEC §13.4 도착 반경 ────────────────────────────────────────────────────
m = grid(['.....', '.....', '.....']);
w = worldOf(m);
mv = new M.Movement(w, m);
hb = w.spawn(0, C.INF, 4, 1);
ha = w.spawn(0, C.INF, 0, 1);
ia = S.index(ha);
ib = S.index(hb);
mv.claim(ib);
mv.claim(ia);
mv.order(ia, 4, 1);                          // 목표 칸은 이미 점유되어 있다
let tArr = 0;
for (tArr = 0; tArr < 300; tArr += 1) {
  mv.step();
  if (mv.goal[ia] < 0) break;
}
H.checkTrue('목표가 점유되어 있어도 ' + M.ARRIVE_R + '타일 안이면 도착으로 친다',
            F.dinf(w.tx[ia] - 4, w.ty[ia] - 1) <= M.ARRIVE_R);
H.check('도착하면 경로를 비운다', mv.path[ia], []);
H.checkTrue('영원히 두드리지 않는다', tArr < 299);

// ── SPEC §13.5 rot8 ─────────────────────────────────────────────────────────
H.check('rot8(0) 은 항등', M.rot8(0, 3, 1), [3, 1]);
H.check('rot8(2) = (-oy, ox)', M.rot8(2, 3, 1), [-1, 3]);
H.check('rot8(4) = (-ox, -oy)', M.rot8(4, 3, 1), [-3, -1]);
H.check('rot8(6) = (oy, -ox)', M.rot8(6, 3, 1), [1, -3]);
H.check('rot8(1) = 이웃 둘의 평균 (내림)', M.rot8(1, 3, 1),
        [F.floordiv(3 + -1, 2), F.floordiv(1 + 3, 2)]);
H.check('rot8(7) = 0 과 6 의 평균', M.rot8(7, 3, 1),
        [F.floordiv(3 + 1, 2), F.floordiv(1 + -3, 2)]);
H.check('원점은 어떤 회전에도 원점',
        H.range(8).map((d) => M.rot8(d, 0, 0)), H.range(8).map(() => [0, 0]));

// ── SPEC §13.5 대형 ─────────────────────────────────────────────────────────
m = grid(H.range(16).map(() => '.'.repeat(16)));
const boxf = M.formation(9, M.BOX, 0, 8, 8, m, 0);
H.check('n=9 BOX 는 3×3, 슬롯 9개', boxf.length, 9);
H.check('BOX 첫 줄은 목표의 x-1..x+1', boxf.slice(0, 3),
        [[7, 8], [8, 8], [9, 8]]);
H.check('BOX 둘째 줄은 한 칸 아래', boxf.slice(3, 6),
        [[7, 9], [8, 9], [9, 9]]);
H.check('n=1 이면 목표 한 칸', M.formation(1, M.BOX, 0, 8, 8, m, 0), [[8, 8]]);
H.check('n=0 이면 빈 목록', M.formation(0, M.BOX, 0, 8, 8, m, 0), []);
H.check('n=5 BOX 의 한 변은 3',
        H.sortedSet(M.formation(5, M.BOX, 0, 8, 8, m, 0).map((p) => p[0])).length,
        3);
const line = M.formation(4, M.LINE, 0, 8, 8, m, 0);
H.check('LINE 은 한 줄', H.sortedSet(line.map((p) => p[1])), [8]);
H.check('LINE 은 가운데 정렬', line, [[7, 8], [8, 8], [9, 8], [10, 8]]);
const col = M.formation(3, M.COLUMN, 0, 8, 8, m, 0);
H.check('COLUMN 은 진행 방향으로 한 줄', col, [[8, 8], [8, 9], [8, 10]]);
H.check('COLUMN 을 동쪽(2)으로 돌리면 x 로 늘어선다',
        M.formation(3, M.COLUMN, 2, 8, 8, m, 0), [[8, 8], [7, 8], [6, 8]]);
const edge = M.formation(9, M.BOX, 0, 0, 0, m, 0);
H.checkTrue('맵 밖 슬롯은 목표 타일로 접는다',
            edge.filter((p) => p[0] === 0 && p[1] === 0).length > 1);
const blocked = grid(H.range(5).map(() => '.'.repeat(5)));
blocked.setTerrain(4, 2, T.ROCK);
H.check('막힌 슬롯은 목표 타일로 접는다',
        M.formation(3, M.LINE, 0, 3, 2, blocked, 0),
        [[2, 2], [3, 2], [3, 2]]);

// ── 경계 조건 ───────────────────────────────────────────────────────────────
m = grid(['..#..', '..#..', '..#..']);
w = worldOf(m);
mv = new M.Movement(w, m);
h = w.spawn(0, C.INF, 0, 1);
i = S.index(h);
mv.claim(i);
H.check('닿을 수 없는 목표는 §8.6 의 대체 목표로 바뀐다', mv.order(i, 4, 1), true);
H.checkTrue('대체 목표는 벽 앞이다', mv.goal[i] % m.w <= 1);
H.check('이미 서 있는 칸으로의 명령은 즉시 도착', mv.order(i, 0, 1), true);
H.check('그 경우 경로는 비어 있다', mv.path[i], []);
H.check('맵 밖 명령은 거부', mv.order(i, -1, 1), false);
mv.order(i, 1, 1);
mv.stop(i);
H.check('STOP 은 아직 시작하지 않은 걸음의 예약만 반납한다',
        mv.resv.filter((v) => v === h).length, 1);
H.check('STOP 은 경로와 목표를 비운다', [mv.path[i], mv.goal[i]], [[], -1]);
mv.order(i, 1, 1);
mv.step();
mv.stop(i);
H.checkTrue('걸음 도중의 STOP 은 두 칸을 쥔 채로 걸음을 마친다',
            mv.resv.filter((v) => v === h).length === 2);
while (w.prog[i] !== 0) mv.step();
H.check('마친 뒤에는 한 칸', mv.resv.filter((v) => v === h).length, 1);
H.check('그리고 멈춰 있다', mv.path[i], []);

H.done();
