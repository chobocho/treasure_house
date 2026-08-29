// test/bot.test.ts — 봇 클라이언트 실측 대전.
//
// 여기서만은 가짜가 하나도 없다. 진짜 TCP 소켓, 우리가 쓴 RFC 6455 서버,
// Node 표준 WebSocket 클라이언트, 그리고 룸 엔진을 그대로 통과한 경기 한 판이다.
// 단위 테스트가 조각마다 옳다고 말해도, 조각들이 서로 말이 통하는지는 이렇게만 안다.
//
// 시계만 speed 로 당긴다(규칙은 그대로). 실시간으로 8인전을 돌리면 테스트가 1분을 넘는다.

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { runMatch, type MatchResult } from '../bot_client.js';

/** 한 판은 비싸다 — 처음 부르는 테스트가 돌리고 나머지는 그 결과를 나눠 본다. */
let cached: Promise<MatchResult> | null = null;
function match(): Promise<MatchResult> {
  cached ??= runMatch({ quiet: true, tickMs: 20, speed: 0.08, target: 'ko' });
  return cached;
}

test('봇 4대·8석이 진짜 웹소켓으로 붙어 경기를 끝낸다', async () => {
  const r = await match();
  assert.equal(r.seats.length, 8, 'PC 4대 × 2석 = 8석이 앉아야 한다');
  assert.deepEqual(r.order.slice().sort((a, b) => a - b), [0, 1, 2, 3, 4, 5, 6, 7]);
  assert.equal(new Set(r.order).size, 8, '같은 좌석이 두 번 등수를 받으면 안 된다');
});

test('가비지가 서버를 거쳐 실제로 오간다', async () => {
  const r = await match();
  const sent = r.seats.reduce((a, s) => a + s.sent, 0);
  const recv = r.seats.reduce((a, s) => a + s.recv, 0);
  assert.ok(recv > 0, `공격이 한 줄도 배달되지 않았다 (보냄 ${sent})`);
  // 보낸 쪽이 혼자 남았거나 대상이 이미 죽었으면 서버가 버린다 — 그래서 recv ≤ sent.
  assert.ok(recv <= sent, `배달된 줄(${recv})이 보낸 줄(${sent})보다 많을 수 없다`);
});

test('경기 통계가 헛돌지 않는다 — 줄을 지운 좌석이 있다', async () => {
  const r = await match();
  assert.ok(r.seats.some((s) => s.lines > 0), '아무도 줄을 못 지웠으면 AI 가 죽어 있는 것이다');
  assert.ok(r.ms > 0);
});

test('PC 2대 × 1석 = 1:1 도 같은 코드로 끝난다 (좌석 수는 손잡이일 뿐)', async () => {
  const r = await runMatch({ quiet: true, tickMs: 20, speed: 0.08, pcs: 2, perPc: 1, target: 'ko' });
  assert.equal(r.seats.length, 2);
  assert.deepEqual(r.order.slice().sort((a, b) => a - b), [0, 1]);
});

test('실측 트래픽이 집계된다 — 덱에 싣는 KB/s 는 잰 값이어야 한다', async () => {
  const r = await match();
  // 지금 없는 필드다. 있어야 덱의 "PC 한 대당 몇 KB/s" 표를 지어내지 않을 수 있다.
  const net = (r as { net?: { up: number; down: number; msgUp: number; msgDown: number } }).net;
  assert.ok(net, '트래픽 집계(net)가 없다');
  assert.ok(net.up > 0 && net.down > 0, `주고받은 바이트가 0이다 (${JSON.stringify(net)})`);
  // 상태 갱신은 초당 10회씩 여덟 좌석이 브로드캐스트된다 — 받는 쪽이 훨씬 많다.
  assert.ok(net.msgDown > net.msgUp, `받은 메시지(${net.msgDown})가 보낸 것(${net.msgUp})보다 많아야 한다`);
});

test('공격 횟수와 배달 횟수가 맞는다', async () => {
  const r = await match();
  const c = r as unknown as { atk?: number; grb?: number };
  assert.equal(typeof c.atk, 'number', '공격 집계(atk)가 없다');
  assert.equal(typeof c.grb, 'number', '배달 집계(grb)가 없다');
  assert.ok((c.atk as number) > 0, '공격이 한 번도 없었다');
  // 대상이 없으면(혼자 남음) 서버가 버리므로 배달 ≤ 공격.
  assert.ok((c.grb as number) > 0 && (c.grb as number) <= (c.atk as number), `배달 ${c.grb} / 공격 ${c.atk}`);
});

test('탈락 기록이 하나도 빠지지 않는다 (끝나자마자 끊으면 마지막 KO 를 놓친다)', async () => {
  const r = await match();
  const kos = (r as unknown as { kos?: { i: number; place: number; by: number }[] }).kos;
  assert.ok(kos, '탈락 기록(kos)이 없다');
  assert.equal(kos.length, 7, `8석이면 탈락은 7번이다 (받은 건 ${kos.length}번)`);
  // 탈락은 꼴찌부터 나온다 — 8등, 7등, … 2등.
  assert.deepEqual(kos.map((k) => k.place), [8, 7, 6, 5, 4, 3, 2]);
  assert.equal(kos[kos.length - 1]!.place, 2, '마지막 탈락자가 2등이다');
  assert.ok(!kos.some((k) => k.i === r.order[0]), '우승자는 탈락 기록에 없어야 한다');
});
