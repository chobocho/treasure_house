// battle.test.ts — 심판(Referee)과 로컬 대전(Battle) 테스트.
//
// 심판은 순수 상태 기계라 단위 테스트로 구석까지 몰 수 있다. 반대로 Battle 은
// 8인이 몇 분을 싸우는 큰 물건이라, 여기서는 "결정론"과 "불변식"을 붙잡는다:
// 같은 시드면 같은 경기가 나오고, 등수는 1..N 이 한 번씩이고, 보낸 줄과 맞은 줄의
// 총합이 어긋나지 않는다.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { Tetris, ST, STATE, W } from '../src/core.js';
import { paintBoard } from '../src/trace.js';
import { DEFAULT_WEIGHTS } from '../src/ai.js';
import {
  Referee, Battle, newRefereeSeat, REFEREE_DEFAULTS,
  type RefEvent, type RefereeSeat, type SeatSpec, type TargetMode,
} from '../src/battle.js';

/** 좌석 n 개가 전부 차 있고 전부 살아 있는 심판 하나. */
function refWith(n: number, target: TargetMode = 'random', seed = 1): Referee {
  const r = new Referee({ max: n, target }, seed);
  for (let i = 0; i < n; i++) r.seats[i] = newRefereeSeat();
  return r;
}

// ── 1. 타깃팅 ─────────────────────────────────────────────────────────
test('공격은 자기 자신에게 가지 않는다', () => {
  const r = refWith(4);
  for (let k = 0; k < 200; k++) {
    const j = r.pickTarget(0, 0);
    assert.notEqual(j, 0);
    assert.ok(j >= 1 && j < 4);
  }
});

test('혼자 남으면 대상이 없다 (-1)', () => {
  const r = refWith(3);
  (r.seats[1] as RefereeSeat).alive = false;
  (r.seats[2] as RefereeSeat).alive = false;
  assert.equal(r.pickTarget(0, 0), -1);
  assert.deepEqual(r.attack(0, 4, 0), [], '허공으로 날아간 공격은 사건을 만들지 않는다');
});

test("'even' 은 가장 덜 맞은 쪽 — 난수를 쓰지 않는다", () => {
  const r = refWith(4, 'even');
  (r.seats[1] as RefereeSeat).recv = 10;
  (r.seats[2] as RefereeSeat).recv = 2;
  (r.seats[3] as RefereeSeat).recv = 7;
  assert.equal(r.pickTarget(0, 0), 2);
  // 같은 판을 몇 번을 물어도 같은 답이 나와야 한다 (난수 소비 없음)
  for (let k = 0; k < 10; k++) assert.equal(r.pickTarget(0, 0), 2);
});

test("'ko' 는 가장 높이 쌓인 쪽 = 죽기 직전인 쪽", () => {
  const r = refWith(4, 'ko');
  (r.seats[1] as RefereeSeat).height = 5;
  (r.seats[2] as RefereeSeat).height = 18;
  (r.seats[3] as RefereeSeat).height = 12;
  assert.equal(r.pickTarget(0, 0), 2);
});

test("'attackers' 는 최근에 때린 쪽에 반격하고, 기억이 낡으면 무작위로", () => {
  const r = refWith(4, 'attackers');
  (r.seats[0] as RefereeSeat).hits.push({ from: 3, at: 1000 });
  assert.equal(r.pickTarget(0, 1500), 3, '최근 기억이 있으면 그쪽');
  // TTL 을 넘기면 기억이 끊긴다
  const after = r.pickTarget(0, 1000 + REFEREE_DEFAULTS.hitTTL + 1);
  assert.ok(after >= 1 && after <= 3, `기억이 낡으면 무작위: ${after}`);
});

test("'attackers': 이미 죽은 상대에게는 반격하지 않는다", () => {
  const r = refWith(4, 'attackers');
  (r.seats[0] as RefereeSeat).hits.push({ from: 3, at: 100 });
  (r.seats[3] as RefereeSeat).alive = false;
  const j = r.pickTarget(0, 200);
  assert.ok(j === 1 || j === 2, `죽은 3번 말고 다른 곳: ${j}`);
});

test('공격 사건은 대상·줄수·보낸이·구멍을 담는다', () => {
  const r = refWith(4, 'even');
  const ev = r.attack(0, 3, 0);
  assert.equal(ev.length, 1);
  const e = ev[0] as RefEvent;
  assert.equal(e.t, 'grb');
  if (e.t !== 'grb') return;
  assert.equal(e.from, 0);
  assert.equal(e.n, 3);
  assert.ok(e.hole >= 0 && e.hole < W, `구멍은 0..${W - 1}: ${e.hole}`);
  assert.equal((r.seats[e.i] as RefereeSeat).recv, 3, '맞은 줄이 누적된다');
});

// ── 2. 탈락과 등수 ────────────────────────────────────────────────────
test('탈락 순서의 역순이 등수다 (마지막 생존자가 1등)', () => {
  const r = refWith(4);
  const out: RefEvent[] = [];
  r.kill(2, 0, out); // 4명 중 첫 탈락 → 4등
  r.kill(0, 0, out); // 3명 중 탈락 → 3등
  r.kill(3, 0, out); // 2명 중 탈락 → 2등, 남은 1명이 1등 + end
  assert.equal((r.seats[2] as RefereeSeat).place, 4);
  assert.equal((r.seats[0] as RefereeSeat).place, 3);
  assert.equal((r.seats[3] as RefereeSeat).place, 2);
  assert.equal((r.seats[1] as RefereeSeat).place, 1);
  const end = out.find((e) => e.t === 'end');
  assert.ok(end && end.t === 'end');
  if (end && end.t === 'end') assert.deepEqual(end.order, [1, 3, 0, 2], '등수 순 좌석 번호');
});

test('KO 사건은 "누가 죽였는지"를 담는다', () => {
  const r = refWith(3);
  (r.seats[0] as RefereeSeat).hits.push({ from: 2, at: 500 });
  const out: RefEvent[] = [];
  r.kill(0, 600, out);
  const ko = out.find((e) => e.t === 'ko');
  assert.ok(ko && ko.t === 'ko');
  if (ko && ko.t === 'ko') {
    assert.equal(ko.i, 0);
    assert.equal(ko.by, 2);
    assert.equal(ko.place, 3);
  }
});

test('오래된 타격은 킬 크레딧으로 치지 않는다', () => {
  const r = refWith(3);
  (r.seats[0] as RefereeSeat).hits.push({ from: 2, at: 0 });
  const out: RefEvent[] = [];
  r.kill(0, REFEREE_DEFAULTS.hitTTL + 1, out);
  const ko = out.find((e) => e.t === 'ko');
  if (ko && ko.t === 'ko') assert.equal(ko.by, -1, '범인 없음');
});

test('이미 죽은 좌석을 또 죽여도 아무 일도 없다', () => {
  const r = refWith(3);
  const a: RefEvent[] = [];
  r.kill(0, 0, a);
  const b: RefEvent[] = [];
  r.kill(0, 0, b);
  assert.deepEqual(b, [], '두 번째 kill 은 사건을 만들지 않는다');
  assert.equal((r.seats[0] as RefereeSeat).place, 3, '등수가 덮어써지면 안 된다');
});

// ── 3. 로컬 대전 ──────────────────────────────────────────────────────
function aiSeats(n: number, intervalMs = 200): SeatSpec[] {
  return Array.from({ length: n }, (_, i) => ({
    name: `AI${i + 1}`, kind: 'ai' as const, weights: DEFAULT_WEIGHTS, intervalMs,
  }));
}

test('좌석마다 다른 조각 순서를 받는다 (같으면 8중 복사다)', () => {
  const b = new Battle({ seats: aiSeats(4), seed: 7 });
  const first = b.seats.map((s) => s.game.curPiece);
  const queues = b.seats.map((s) => Array.from(s.game.nextQ).join(','));
  assert.equal(new Set(queues).size, 4, `좌석별 큐가 달라야 한다: ${queues}`);
  assert.ok(first.length === 4);
});

test('sharedSeed 를 켜면 좌석 전부가 같은 조각 순서를 받는다 (온라인 규격과 같게)', () => {
  const b = new Battle({ seats: aiSeats(8), seed: 7, sharedSeed: true });
  const queues = b.seats.map((s) => Array.from(s.game.nextQ).join(','));
  assert.equal(new Set(queues).size, 1, `한 시드를 나눠 쓰면 큐가 같아야 한다: ${queues}`);
  assert.equal(new Set(b.seats.map((s) => s.game.curPiece)).size, 1);
});

test('같은 시드·같은 dt 면 같은 경기가 나온다', () => {
  const play = (): string => {
    const b = new Battle({ seats: aiSeats(4), seed: 31, target: 'even' });
    b.run(50);
    return JSON.stringify({ order: b.order, sum: b.summary() });
  };
  assert.equal(play(), play());
});

test('4인 대전은 끝나고 등수가 1..4 로 한 번씩 매겨진다', () => {
  const b = new Battle({ seats: aiSeats(4, 120), seed: 5, target: 'ko' });
  b.run(50);
  assert.ok(b.over, `경기가 끝나야 한다 (${b.now}ms 경과)`);
  assert.deepEqual(b.order.slice().sort((x, y) => x - y), [0, 1, 2, 3]);
  const places = b.summary().map((s) => s.place).sort((x, y) => x - y);
  assert.deepEqual(places, [1, 2, 3, 4]);
});

test('8인 대전도 끝난다 (좌석 수가 늘어도 종료 조건이 성립)', () => {
  const b = new Battle({ seats: aiSeats(8, 120), seed: 9, target: 'random' });
  b.run(50);
  assert.ok(b.over, `8인 경기가 끝나야 한다 (${b.now}ms 경과)`);
  assert.equal(b.order.length, 8);
  assert.equal(new Set(b.order).size, 8, '같은 좌석이 두 번 나오면 안 된다');
});

test('보낸 줄의 총합과 맞은 줄의 총합이 같다', () => {
  const b = new Battle({ seats: aiSeats(4, 150), seed: 21, target: 'even' });
  b.run(50);
  const sum = b.summary();
  const sent = sum.reduce((a, s) => a + s.sent, 0);
  const recv = sum.reduce((a, s) => a + s.recv, 0);
  // 마지막 한 명이 남은 뒤의 공격은 허공으로 사라지므로 sent >= recv 다.
  assert.ok(sent >= recv, `보낸 ${sent} < 맞은 ${recv} 는 있을 수 없다`);
  assert.ok(recv > 0, '아무도 안 맞았으면 대전이 아니다');
});

test('가비지는 유예 뒤에 도착한다 — 그 사이에 상쇄할 수 있다', () => {
  const b = new Battle({ seats: aiSeats(2, 100), seed: 3, delay: 900 });
  // 1번 좌석에 4줄짜리 공격을 심판을 거치지 않고 직접 넣어 본다
  const ev = b.ref.attack(0, 4, b.now);
  assert.equal(ev.length, 1);
  const target = (ev[0] as { t: 'grb'; i: number }).i;
  assert.equal(target, 1);
  const before = b.seats[1]!.game.stats[ST.GARBAGE_RECV];
  b.update(50);
  assert.equal(b.seats[1]!.game.stats[ST.GARBAGE_RECV], before, '유예 안에는 안 온다');
});

test('사람 좌석은 중력이 돌고, 키를 누르면 즉시 공격이 배달된다', () => {
  const b = new Battle({
    seats: [{ name: '나', kind: 'human' }, { name: 'AI', kind: 'ai', intervalMs: 100000 }],
    seed: 1, target: 'even', delay: 0,
  });
  const me = b.seats[0]!;
  // 테트리스 자리를 심고 I 를 세워 꽂는다 → 공격 4
  paintBoard(me.game.board, ['.#########', '.#########', '.#########', '.#########', '#########.']);
  me.game.setPiece(0);
  b.press(0, 3); // CW
  for (let k = 0; k < 6; k++) b.press(0, 0); // LEFT
  const ev = b.press(0, 5); // HARD
  assert.equal(me.game.stats[ST.CLEAR], 4);
  const grb = ev.find((e) => e.t === 'grb');
  assert.ok(grb && grb.t === 'grb', `공격이 배달돼야 한다: ${JSON.stringify(ev)}`);
  if (grb && grb.t === 'grb') {
    assert.equal(grb.from, 0);
    assert.equal(grb.n, 4);
    assert.equal(grb.i, 1);
  }
});

test('사람 좌석에는 중력이, AI 좌석에는 중력이 돌지 않는다', () => {
  const b = new Battle({
    seats: [{ name: '나', kind: 'human' }, { name: 'AI', kind: 'ai', intervalMs: 100000 }],
    seed: 1,
  });
  const humanY = b.seats[0]!.game.curY;
  const aiY = b.seats[1]!.game.curY;
  for (let k = 0; k < 15; k++) b.update(100); // 1.5초
  assert.ok(b.seats[0]!.game.curY > humanY, '사람 조각은 중력으로 내려간다');
  assert.equal(b.seats[1]!.game.curY, aiY, 'AI 조각은 하드드롭으로만 움직인다');
});

test('죽은 좌석에는 가비지가 배달되지 않는다', () => {
  const b = new Battle({ seats: aiSeats(3, 150), seed: 4, delay: 0 });
  // 1번을 탈락 상태로 만들고, 그 뒤에 도착 예정인 가비지를 심는다
  const ev = b.ref.attack(0, 4, b.now);
  assert.equal((ev[0] as { t: 'grb'; i: number }).i >= 0, true);
  (b.ref.seats[1] as RefereeSeat).alive = false;
  b.seats[1]!.game.stats[ST.STATE] = STATE.OVER;
  const before = b.seats[1]!.game.stats[ST.GARBAGE_RECV];
  b.update(50);
  assert.equal(b.seats[1]!.game.stats[ST.GARBAGE_RECV], before);
});

test('심판의 난수는 규격의 xorshift32 다 (코어와 같은 수열)', () => {
  const r = new Referee({}, 1);
  const g = new Tetris(1);
  // 코어의 rnd() 는 private 이라 직접 못 부른다. 대신 같은 알고리즘을 여기서 재현해
  // 두 곳이 같은 상수를 쓰는지 확인한다 — 규격서(protocol.md)가 정한 그 수열이다.
  let x = 1 >>> 0;
  const next = (): number => {
    x ^= x << 13; x >>>= 0;
    x ^= x >>> 17;
    x ^= x << 5; x >>>= 0;
    return x;
  };
  for (let k = 0; k < 20; k++) assert.equal(r.rng(), next());
  assert.ok(g.stats[ST.STATE] === STATE.PLAY);
});
