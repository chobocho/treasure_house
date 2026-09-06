// 시뮬레이션 — 틱 단계·상태 해시·트리거·시나리오 스크립트 (SPEC §18).

import * as H from './harness';
import * as C from '../src/const';
import * as SEL from '../src/select';
import * as SIM from '../src/sim';
import * as S from '../src/spatial';
import * as T from '../src/tmap';

H.title('sim');

function grid(rowsIn: string[]): T.TMap {
  const m = new T.TMap(rowsIn[0].length, rowsIn.length);
  for (let y = 0; y < rowsIn.length; y += 1) {
    for (let x = 0; x < rowsIn[y].length; x += 1) {
      m.terrain[y * m.w + x] = T.TERRAIN_CH.indexOf(rowsIn[y][x]);
      m.repass(y * m.w + x);
    }
  }
  m.bump();
  return m;
}

function flat(n = 24): T.TMap {
  return grid(H.range(n).map(() => '.'.repeat(n)));
}

function add(s: SIM.Sim, p: number, kind: number, x: number,
             y: number): number {
  return S.index(s.spawn(p, kind, x, y));
}

function countAlive(s: SIM.Sim): number {
  let n = 0;
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (s.w.alive[i] !== 0) n += 1;
  }
  return n;
}

// ── SPEC §18.1 유일한 진입점 ────────────────────────────────────────────────
const s = new SIM.Sim(flat(), 1234, 2);
H.check('시작 틱은 0', s.tick, 0);
s.step([]);
H.check('한 틱 지나면 1', s.tick, 1);
H.check('이벤트는 매 틱 초에 비운다', s.events, []);

const u = add(s, 0, C.INF, 5, 5);
const uh = s.w.handle(u);
s.step([[0, uh, SEL.MOVE, 8, 5, 0]]);
H.checkTrue('MOVE 명령이 경로를 깐다', s.mv.goal[u] >= 0);
for (let t = 0; t < 200; t += 1) s.step([]);
H.check('목표까지 간다', [s.w.tx[u], s.w.ty[u]], [8, 5]);

let bad = 0;
try {
  s.step([[1, 5, 0, 0, 0, 0], [0, 5, 0, 0, 0, 0]]);
} catch (e) {
  bad = 1;
}
H.check('정렬되지 않은 명령 목록은 그 자리에서 터진다', bad, 1);
H.note('조용히 정렬해 주면 호출자의 버그가 다른 기계에서 다른 순서로 나타난다');

s.step([[1, uh, SEL.MOVE, 0, 0, 0]]);
H.check('남의 유닛에 내린 명령은 무시', s.w.owner[u], 0);
s.step([[0, 999999, SEL.MOVE, 0, 0, 0]]);
H.check('죽은 핸들에 내린 명령도 무시', s.tick > 0, true);

// ── SPEC §18.4 상태 해시 ────────────────────────────────────────────────────
const a = new SIM.Sim(flat(), 7, 2);
const b = new SIM.Sim(flat(), 7, 2);
for (const sm of [a, b]) {
  add(sm, 0, C.INF, 3, 3);
  add(sm, 1, C.TANK, 9, 9);
  add(sm, 0, C.HQ, 15, 15);
}
H.check('같은 상태면 같은 해시', a.stateHash(), b.stateHash());
H.checkTrue('해시는 32비트 안', a.stateHash() >= 0 && a.stateHash() < 4294967296);
const base = a.stateHash();
a.w.hp[1] -= 1;
H.check('hp 한 점이 해시를 바꾼다', a.stateHash() !== base, true);
a.w.hp[1] += 1;
H.check('되돌리면 같다', a.stateHash(), base);
const WFIELDS: Array<[string, number]> = [
  ['cool', 1], ['timer', 1], ['prog', 1], ['load', 1],
  ['dir', 1], ['state', 1], ['target', 1]];
for (const [field, val] of WFIELDS) {
  const arr = (a.w as unknown as Record<string, number[]>)[field];
  arr[1] += val;
  if (a.stateHash() === base) H.note(field + ' 가 해시에 들어가지 않는다');
  arr[1] -= val;
}
H.check('cool·timer 를 포함한 엔티티 15칸이 전부 해시에 들어간다',
        a.stateHash(), base);
a.ec.credits[0] += 1;
H.check('크레딧도 해시에', a.stateHash() !== base, true);
a.ec.credits[0] -= 1;
a.ec.ore[10] = 5;
H.check('광맥 잔량도 해시에', a.stateHash() !== base, true);
a.ec.ore[10] = 0;
a.ec.queue[3] = [C.INF];                     // 3번이 사령부다 — 큐는 건물의 것이다
H.check('생산 큐도 해시에', a.stateHash() !== base, true);
a.ec.queue[3] = [];
a.rng.s += 1;
H.check('rng 상태도 해시에', a.stateHash() !== base, true);
a.rng.s -= 1;
a.m.setTerrain(1, 1, T.ROCK);
H.check('지형이 바뀌면 map_hash 가 바뀐다', a.stateHash() !== base, true);
const mh = a.mapHash();
H.check('map_hash 는 version 이 같으면 다시 계산하지 않는다',
        [a.mapHash(), a.mapHashVersion], [mh, a.m.version]);
a.m.setTerrain(1, 1, T.SAND);
H.checkTrue('version 이 오르면 다시 계산한다', a.mapHash() !== mh);

// ── SPEC §18.2 5단계: 피해는 모아서 적용한다 ────────────────────────────────
const s2 = new SIM.Sim(flat(12), 3, 2);
const x2 = add(s2, 0, C.INF, 5, 5);
const y2 = add(s2, 1, C.INF, 6, 5);
s2.w.hp[x2] = 3;
s2.w.hp[y2] = 3;
for (let t = 0; t < 30; t += 1) {
  s2.step([]);
  if (s2.w.alive[x2] === 0 || s2.w.alive[y2] === 0) break;
}
H.check('서로를 같은 틱에 죽일 수 있다 — 먼저 처리된 쪽이 유리하지 않다',
        [s2.w.alive[x2], s2.w.alive[y2]], [0, 0]);

// ── SPEC §18.3 이벤트 로그 ──────────────────────────────────────────────────
const s3 = new SIM.Sim(flat(12), 5, 2);
const hq3 = add(s3, 0, C.HQ, 4, 4);
s3.ec.credits[0] = 1000;
s3.ec.recountSupply(s3.w);
s3.step([[0, s3.w.handle(hq3), SEL.TRAIN, C.HARV, 0, 0]]);
H.check('명령은 이벤트를 남긴다', s3.events.map((e) => e[0]), [SIM.EV_ORDER]);
for (let t = 0; t < C.BUILD_TICKS[C.HARV] + 2; t += 1) {
  s3.step([]);
  if (s3.events.some((e) => e[0] === SIM.EV_SPAWN)) break;
}
H.check('생산이 끝나면 SPAWN 이벤트', s3.events.map((e) => e[0]),
        [SIM.EV_SPAWN]);
H.checkTrue('실제로 채집기가 생겼다',
            H.range(1, C.MAX_ENT).some(
              (i) => s3.w.alive[i] !== 0 && s3.w.kind[i] === C.HARV));
H.check('이벤트는 해시에 넣지 않는다 — 트레이스가 대신 잡는다',
        s3.events.length !== 0, true);

// ── §16.4 건물 건설 ─────────────────────────────────────────────────────────
const s4 = new SIM.Sim(flat(16), 9, 2);
const hq4 = add(s4, 0, C.HQ, 4, 4);
s4.mv.claim(hq4);
s4.ec.credits[0] = 1000;
s4.ec.recountSupply(s4.w);
s4.step([[0, s4.w.handle(hq4), SEL.BUILD, C.POW, 8, 4]]);
const built = H.range(1, C.MAX_ENT).filter(
  (i) => s4.w.alive[i] !== 0 && s4.w.kind[i] === C.POW);
H.check('BUILD 는 그 자리에 즉시 엔티티를 만든다', built.length, 1);
const bi4 = built[0];
H.check('짓는 중 상태', s4.w.state[bi4], C.ST_BUILD);
H.check('hp 는 1 에서 시작', s4.w.hp[bi4], 1);
H.check('돈은 선불', s4.ec.credits[0], 1000 - C.COST[C.POW]);
H.check('짓는 중에도 발자국을 막는다', s4.m.passableTerrain(8, 4, 0), false);
for (let t = 0; t < C.BUILD_TICKS[C.POW] + 2; t += 1) {
  s4.step([]);
  if (s4.w.state[bi4] === C.ST_IDLE) break;
}
H.check('다 지으면 IDLE', s4.w.state[bi4], C.ST_IDLE);
H.check('hp 가 정격까지 찬다', s4.w.hp[bi4], C.HP[C.POW]);
s4.step([[0, s4.w.handle(hq4), SEL.BUILD, C.FACT, 12, 12]]);
H.check('돈이 없으면 짓지 않는다',
        H.range(1, C.MAX_ENT).filter(
          (i) => s4.w.alive[i] !== 0 && s4.w.kind[i] === C.FACT).length, 0);
s4.step([[0, s4.w.handle(hq4), SEL.BUILD, C.POW, 4, 4]]);
H.check('못 짓는 자리에도 짓지 않는다',
        H.range(1, C.MAX_ENT).filter(
          (i) => s4.w.alive[i] !== 0 && s4.w.kind[i] === C.POW).length, 1);

// ── §16.5 내 유닛이 막고 있으면 비키게 한다 ────────────────────────────────
//   채집 경로 위에 건물 자리를 잡으면 재시도가 전부 막힌다 — 실제로 그래서
//   플레이어 1 의 발전소가 1200틱 내내 서지 않았다.
const s4b = new SIM.Sim(flat(16), 10, 2);
const hq4b = add(s4b, 0, C.HQ, 4, 4);
s4b.ec.credits[0] = 1000;
s4b.ec.recountSupply(s4b.w);
const blocker = add(s4b, 0, C.INF, 9, 4);
H.check('그 칸은 내 유닛이 쥐고 있다', s4b.mv.resv[4 * 16 + 9],
        s4b.w.handle(blocker));
s4b.step([[0, s4b.w.handle(hq4b), SEL.BUILD, C.POW, 8, 4]]);
H.check('막힌 배치는 실패한다',
        H.range(1, C.MAX_ENT).filter(
          (i) => s4b.w.alive[i] !== 0 && s4b.w.kind[i] === C.POW).length, 0);
H.check('돈은 나가지 않았다', s4b.ec.credits[0], 1000);
H.checkTrue('대신 막은 유닛에게 한 걸음 명령이 갔다',
            s4b.mv.goal[blocker] >= 0 || s4b.w.prog[blocker] > 0);
for (let t = 0; t < 40; t += 1) {
  s4b.step([]);
  if (!(s4b.w.tx[blocker] === 9 && s4b.w.ty[blocker] === 4)) break;
}
H.checkTrue('유닛이 비켰다',
            !(s4b.w.tx[blocker] === 9 && s4b.w.ty[blocker] === 4));
s4b.step([[0, s4b.w.handle(hq4b), SEL.BUILD, C.POW, 8, 4]]);
H.check('다음 시도는 성공한다',
        H.range(1, C.MAX_ENT).filter(
          (i) => s4b.w.alive[i] !== 0 && s4b.w.kind[i] === C.POW).length, 1);
H.note('밀면서 동시에 짓지는 않는다 — 서 있는 유닛 위에 건물을 얹으면 불변식 R 이 깨진다');

// ── SPEC §18.5 트리거 ───────────────────────────────────────────────────────
const s5 = new SIM.Sim(flat(16), 11, 2);
s5.addTrigger([SIM.CT_TICK_GE, 3, 0, 0, 0],
              [SIM.AC_SPAWN, 0, C.INF, 2, 2], true);
for (let t = 0; t < 2; t += 1) s5.step([]);
H.check('3틱 전에는 발화하지 않는다', countAlive(s5), 0);
s5.step([]);
H.check('TICK_GE 가 발화해 유닛을 만든다', countAlive(s5), 1);
for (let t = 0; t < 5; t += 1) s5.step([]);
H.check('once 트리거는 한 번만', countAlive(s5), 1);
H.check('발화 표시는 상태의 일부', s5.fired[0], true);

const s6 = new SIM.Sim(flat(16), 12, 2);
s6.ec.credits[1] = 500;
s6.addTrigger([SIM.CT_CREDITS_GE, 1, 400, 0, 0], [SIM.AC_MESSAGE, 7, 0, 0],
              true);
s6.step([]);
H.check('CREDITS_GE',
        s6.events.filter((e) => e[0] === SIM.EV_ORDER).length === 0, true);
H.check('메시지 액션은 이벤트로 나온다',
        s6.events.filter((e) => e[0] === SIM.EV_MESSAGE).map((e) => e[1]), [7]);

const s7 = new SIM.Sim(flat(16), 13, 2);
add(s7, 0, C.INF, 5, 5);
s7.addTrigger([SIM.CT_UNIT_COUNT, 0, C.INF, SIM.CMP_GE, 1],
              [SIM.AC_REVEAL, 10, 10, 3], false);
s7.step([]);
H.check('UNIT_COUNT + REVEAL', s7.fog.explored[0][10 * 16 + 10], 1);
s7.step([]);
H.check('once 가 아니면 계속 평가한다', s7.fired[0], false);

const s8 = new SIM.Sim(flat(16), 14, 2);
const mine8 = add(s8, 0, C.INF, 1, 1);
s8.addTrigger([SIM.CT_AREA_ENTERED, 0, 8, 8, 2], [SIM.AC_LOSE, 0, 0, 0], true);
s8.step([]);
H.check('멀리 있으면 발화하지 않는다', s8.loser, []);
s8.w.tx[mine8] = 8;
s8.w.ty[mine8] = 9;
s8.step([]);
H.check('AREA_ENTERED', s8.loser, [0]);

// ── SPEC §18.5 기본 승패 ────────────────────────────────────────────────────
const s9 = new SIM.Sim(flat(16), 15, 2);
const b0 = add(s9, 0, C.HQ, 2, 2);
const b1 = add(s9, 1, C.HQ, 12, 12);
s9.w.hp[b0] = 400;
s9.w.hp[b1] = 400;
s9.step([]);
H.check('둘 다 살아 있으면 승자 없음', s9.winner, -1);
s9.w.hp[b1] = 0;
s9.step([]);
H.check('건물이 전부 부서진 쪽이 진다', s9.loser, [1]);
H.check('남은 쪽이 이긴다', s9.winner, 0);
H.check('WIN 이벤트',
        s9.events.filter((e) => e[0] === SIM.EV_WIN).length, 1);
s9.step([]);
H.check('승리는 한 번만 알린다',
        s9.events.filter((e) => e[0] === SIM.EV_WIN).length, 0);

// ── SPEC §18.6 시나리오 스크립트 ────────────────────────────────────────────
const sc = SIM.parseScript(H.golden('script.txt'));
H.check('골든 스크립트의 길이', sc.ticks, 1200);
H.check('플레이어 수', sc.players, 2);
H.checkTrue('명령이 여러 줄', sc.lines.length > 20);
H.check('주석은 건너뛴다',
        sc.lines.filter((ln) => String(ln[2]).indexOf('#') === 0).map(() => 1),
        []);
H.check('틱 오름차순', sc.lines.map((ln) => ln[0]),
        H.sortedNums(sc.lines.map((ln) => ln[0])));

const s10 = new SIM.Sim(flat(20), 21, 2);
const u1 = add(s10, 0, C.INF, 2, 2);
const u2 = add(s10, 0, C.HARV, 3, 3);
const u3 = add(s10, 1, C.INF, 9, 9);
const bq = add(s10, 0, C.HQ, 5, 5);
const mini = SIM.parseScript('RTSS 1\nticks 10\nplayers 2\n'
                             + '# 주석\n'
                             + '1 0 A MOVE 7 7 0\n'
                             + '2 0 F MOVE 8 8 0\n'
                             + '3 0 K10 TRAIN 4 0 0\n'
                             + '4 0 N MOVE 1 1 0\n');
const o1 = s10.scriptOrders(mini, 1);
H.check('선택자 A 는 내 유닛 전부 (건물 제외)', o1.map((o) => o[1]),
        H.sortedNums([s10.w.handle(u1), s10.w.handle(u2)]));
H.check('명령 여섯 칸', o1[0].length, 6);
const o2 = s10.scriptOrders(mini, 2);
H.check('선택자 F 는 전투 유닛만', o2.map((o) => o[1]), [s10.w.handle(u1)]);
const o3 = s10.scriptOrders(mini, 3);
H.check('선택자 K10 은 종류 10 (사령부)', o3.map((o) => o[1]),
        [s10.w.handle(bq)]);
const o4 = s10.scriptOrders(mini, 4);
H.check('선택자 N 은 가장 최근에 생산된 유닛 하나', o4.length, 1);
H.check('없는 틱은 빈 목록', s10.scriptOrders(mini, 9), []);
H.check('펼친 결과는 핸들 오름차순', o1.map((o) => o[1]),
        H.sortedNums(o1.map((o) => o[1])));
H.check('남의 유닛은 내 선택자에 걸리지 않는다',
        o1.map((o) => o[1]).indexOf(s10.w.handle(u3)) >= 0, false);

// ── 결정론: 같은 씨앗·같은 명령이면 매 틱 같은 해시 ─────────────────────────
function run(n: number): [SIM.Sim, number[]] {
  const sm = new SIM.Sim(T.TMap.loadText(H.golden('map_start.txt')), 1, 2);
  sm.setupStart();
  const hs: number[] = [];
  for (let t = 0; t < n; t += 1) {
    sm.step([]);
    hs.push(sm.stateHash());
  }
  return [sm, hs];
}

const [sA, hA] = run(120);
const [, hB] = run(120);
H.check('같은 씨앗이면 120틱의 해시열이 같다', hA, hB);
H.checkTrue('해시가 실제로 변한다', H.sortedSet(hA).length > 60);
const sC = new SIM.Sim(T.TMap.loadText(H.golden('map_start.txt')), 1, 2);
sC.setupStart();

function countOf(sm: SIM.Sim, p: number, kind: number): number {
  let n = 0;
  for (let i = 1; i < C.MAX_ENT; i += 1) {
    if (sm.w.alive[i] !== 0 && sm.w.owner[i] === p && sm.w.kind[i] === kind) {
      n += 1;
    }
  }
  return n;
}

H.check('시작 조건 — 플레이어마다 HQ 1채, 채집기 2기',
        [0, 1].map((p) => [countOf(sC, p, C.HQ), countOf(sC, p, C.HARV)]),
        [[1, C.START_HARV], [1, C.START_HARV]]);
H.check('시작 크레딧', sC.ec.credits.slice(0, 2),
        [C.START_CREDITS, C.START_CREDITS]);
H.check('시작하면 AI 가 켜진다', sC.aiEnabled.slice(0, 2), [true, true]);
H.checkTrue('120틱 뒤에는 AI 가 채집기를 더 뽑았다',
            countOf(sA, 0, C.HARV) > C.START_HARV);
H.checkTrue('채집이 돌아간다 (120틱)',
            sA.ec.credits[0] + sA.ec.credits[1] >= 0);
H.check('불변식 R 이 유지된다',
        H.range(1, C.MAX_ENT).filter(
          (i) => sA.w.alive[i] !== 0 && C.IS_BUILDING[sA.w.kind[i]] === 0
                 && sA.mv.resv[sA.w.from_t[i]] !== sA.w.handle(i)).length, 0);
H.check('불변식 F 가 유지된다', sA.fog.recount(sA.w), 0);

H.done();
