// net.test.ts — 브라우저 쪽 네트워크 층(클라이언트·루프백·경기 진행).
//
// 여기서 도는 허브·룸은 서버가 쓰는 그 클래스 그대로다. 바뀌는 건 전송 계층뿐이라,
// 이 테스트가 통과하면 "덱 데모와 진짜 서버가 같은 코드를 지난다"는 말이 사실이 된다.

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { NetClient } from '../src/net/client.js';
import { LoopbackHub } from '../src/net/loopback.js';
import { Match } from '../src/net/match.js';
import { unsnapshot } from '../src/net/protocol.js';
import { W, VIS, ST } from '../src/core.js';
import { App } from '../src/app.js';

/** 루프백은 onOpen 을 다음 틱에 부른다 — 그 틱을 흘려 준다. */
const tick = (): Promise<void> => new Promise((r) => { setTimeout(r, 0); });

interface Peer { c: NetClient; m: Match }

/** PC 여러 대를 붙이고 좌석을 잡게 한다. */
async function room(pcs: number, perPc: number, cfg: Record<string, unknown> = {}): Promise<{
  hub: LoopbackHub; peers: Peer[];
}> {
  const hub = new LoopbackHub(0xc0ffee);
  const peers: Peer[] = [];
  for (let k = 0; k < pcs; k++) {
    const c = new NetClient(hub.connect(), `PC${k + 1}`);
    const m = new Match(c, { intervalMs: 20, stMs: 50, delay: 0, defer: (fn): void => { fn(); } });
    c.on('joined', () => {
      for (let s = 0; s < perPc; s++) c.takeSeat(-1, 'ai', `${k + 1}-${s + 1}`, 'max');
      c.setReady(true);
    });
    // 핸들러가 받는 건 ServerMsg 유니온이다. t 로 좁히면 캐스팅이 필요 없다.
    c.on('start', (msg) => { if (msg.t === 'start') m.begin(msg.seed, msg.seats); });
    c.on('grb', (msg) => { if (msg.t === 'grb') m.garbage(msg.i, msg.n); });
    peers.push({ c, m });
    await tick();                       // hello → hi
    if (k === 0) c.create({ max: pcs * perPc, perPeer: perPc, target: 'random', ...cfg });
    else c.join((peers[0] as Peer).c.code);
    await tick();
  }
  return { hub, peers };
}

test('루프백으로 붙으면 hi 와 joined 가 온다', async () => {
  const { peers } = await room(1, 1);
  const c = (peers[0] as Peer).c;
  assert.ok(c.pid > 0, 'pid 를 못 받았다');
  assert.match(c.code, /^[A-Z2-9]{4}$/, `방 코드가 이상하다: ${c.code}`);
  assert.equal(c.cfg?.max, 1);
});

test('PC 4대가 8석을 나눠 잡는다', async () => {
  const { peers } = await room(4, 2);
  const host = (peers[0] as Peer).c;
  assert.equal(host.seats.length, 8, '여덟 자리가 다 차야 한다');
  assert.equal(new Set(host.seats.map((s) => s.pid)).size, 4, 'PC 는 넷이다');
  assert.equal(host.mine().length, 2, '내 좌석은 둘');
});

test('start 는 전원에게 같은 시드로 간다', async () => {
  const { peers } = await room(2, 2);
  (peers[0] as Peer).c.start();
  const seeds = peers.map((p) => p.c.seed);
  assert.ok(seeds[0] as number, '시드가 0이면 안 된다');
  assert.equal(new Set(seeds).size, 1, `시드가 갈렸다: ${seeds}`);
  assert.equal((peers[1] as Peer).m.seats.length, 2, '두 번째 PC 도 판을 세웠어야 한다');
});

test('공격이 서버를 거쳐 상대에게 배달된다', async () => {
  const { peers } = await room(2, 1);
  const [a, b] = peers as [Peer, Peer];
  let delivered = 0;
  b.c.on('grb', (m) => { if (m.t === 'grb') delivered += m.n; });
  a.c.start();
  // 한쪽이 줄을 지울 때까지 돌린다
  for (let i = 0; i < 4000 && delivered === 0; i++) {
    for (const p of peers) p.m.update(20);
  }
  assert.ok(delivered > 0, '가비지가 한 줄도 배달되지 않았다');
  const seat = b.m.seats[0];
  assert.ok((seat?.recv ?? 0) > 0, '받은 쪽이 맞은 줄을 세지 않았다');
});

test('스냅샷으로 남의 판이 그대로 온다', async () => {
  const { peers } = await room(2, 1);
  const [a, b] = peers as [Peer, Peer];
  let got: string | null = null;
  let fromSeat = -1;
  b.c.on('st', (m) => {
    if (m.t !== 'st') return;
    got = m.b;
    fromSeat = m.i;
  });
  a.c.start();
  for (let i = 0; i < 60 && got === null; i++) a.m.update(20);
  assert.ok(got !== null, '상태 메시지가 안 왔다');
  const out = new Uint8Array(VIS * W);
  assert.equal(unsnapshot(got as unknown as string, out), VIS * W);
  const mine = a.m.seat(fromSeat);
  assert.ok(mine, '보낸 좌석을 못 찾았다');
  // 내가 보낸 판과 남이 푼 판이 한 칸도 다르지 않아야 한다(현재 조각 포함).
  const src = new Uint8Array(VIS * W);
  src.set(mine.game.cells);
  for (let k = 0; k < src.length; k++) {
    const ov = mine.game.overlay[k] as number;
    if (ov >= 1 && ov <= 7) src[k] = ov;
  }
  assert.deepEqual(Array.from(out), Array.from(src), '스냅샷이 원판과 다르다');
});

test('경기가 끝나면 end 로 등수가 온다', async () => {
  const { peers } = await room(2, 1);
  const [a, b] = peers as [Peer, Peer];
  let order: number[] | null = null;
  a.c.on('end', (m) => { if (m.t === 'end') order = m.order; });
  a.c.start();
  for (let i = 0; i < 20000 && order === null; i++) {
    for (const p of peers) p.m.update(50);
  }
  assert.ok(order !== null, '경기가 안 끝났다');
  assert.deepEqual((order as unknown as number[]).slice().sort(), [0, 1]);
  assert.equal(b.c.order?.length, 2, '진 쪽도 등수를 받아야 한다');
  // 죽은 좌석은 더 이상 조각을 두지 않는다
  const dead = [...a.m.seats, ...b.m.seats].filter((s) => !s.alive);
  assert.ok(dead.length >= 1);
  const before = dead.map((s) => s.game.stats[ST.PIECES] as number);
  for (const p of peers) p.m.update(100);
  assert.deepEqual(dead.map((s) => s.game.stats[ST.PIECES] as number), before);
});

// ── 진짜 페이지(app.ts) — 전송 계층만 루프백으로 바꿔 시험한다 ─────────
/** app.ts 가 DOM 에 요구하는 만큼만 흉내 내는 스텁. */
function stubHost(): { host: Record<string, unknown>; texts: () => string } {
  const ctx = new Proxy({}, { get: () => (): void => {}, set: () => true }) as Record<string, unknown>;
  const doc: Record<string, unknown> = {};
  const make = (): Record<string, unknown> => {
    const kids: Record<string, unknown>[] = [];
    const node: Record<string, unknown> = {
      style: { cssText: '' }, textContent: '', width: 0, height: 0, children: kids,
      ownerDocument: doc,
      appendChild: (c: Record<string, unknown>) => { kids.push(c); return c; },
      addEventListener: () => {},
      getContext: () => ctx,
      getBoundingClientRect: () => ({ width: 720 }),
    };
    return node;
  };
  doc.createElement = (): Record<string, unknown> => make();
  const host = make();
  const walk = (n: Record<string, unknown>): string =>
    String(n.textContent ?? '') + ((n.children as Record<string, unknown>[]) ?? []).map(walk).join(' ');
  return { host, texts: (): string => walk(host) };
}

test('app 은 전송 계층만 바꿔 끼우면 그대로 돈다', async () => {
  const hub = new LoopbackHub(0xbeef);
  const { host, texts } = stubHost();
  const c = clockOf();
  const app = new App(host as unknown as HTMLElement, {
    transport: () => hub.connect(), name: '나',
    raf: c.raf, caf: c.caf, now: c.now, maxWidth: 400,
  });
  await tick();                                  // hello → hi
  app.client.create({ max: 2, perPeer: 2 });
  await tick();
  assert.match(app.client.code, /^[A-Z2-9]{4}$/, '방을 못 만들었다');
  assert.match(texts(), /방 .* 에 들어왔다/, '로비 안내가 없다');

  app.client.takeSeat(-1, 'ai', '보라', 'max');
  app.client.takeSeat(-1, 'ai', '다온', 'max');
  await tick();
  assert.equal(app.client.seats.length, 2);

  app.client.start();
  await tick();
  assert.equal(app.match.seats.length, 2, '내 좌석 둘이 서야 한다');
  for (let i = 0; i < 30; i++) c.tick(50);
  const placed = app.match.seats.reduce((a, s) => a + (s.game.stats[ST.PIECES] as number), 0);
  assert.ok(placed > 2, `조각이 놓여야 한다 (${placed})`);
  app.stop();
});

/** 손으로 돌리는 프레임 시계 — view 테스트의 것과 같은 물건이다. */
function clockOf(): { raf: (cb: (t: number) => void) => number; caf: (h: number) => void;
                      now: () => number; tick: (ms: number) => void } {
  let t = 0, next = 1;
  const q = new Map<number, (t: number) => void>();
  return {
    raf(cb) { const h = next++; q.set(h, cb); return h; },
    caf(h) { q.delete(h); },
    now: () => t,
    tick(ms) { t += ms; const due = [...q.entries()]; q.clear(); for (const [, cb] of due) cb(t); },
  };
}
