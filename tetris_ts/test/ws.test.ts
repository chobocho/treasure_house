// ws.test.ts — 직접 쓴 RFC 6455 구현과 허브·서버 테스트.
//
// 두 층으로 나눠 본다.
//   1) 프레임 파서·인코더 — 순수 함수라 구석까지 몰 수 있다. TCP 가 프레임을
//      어떻게 쪼개 놓든 같은 결과가 나와야 한다는 게 핵심이다.
//   2) 진짜 서버 — 포트를 열고 Node 의 표준 WebSocket 클라이언트로 붙는다.
//      "우리 구현끼리만 말이 통하는" 자기만족을 막으려면 남의 클라이언트가 필요하다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

import {
  FrameParser, encodeFrame, acceptKey, OP, WS_GUID, MAX_MESSAGE, WsProtocolError,
} from '../src/net/ws.js';
import { Hub, safeJoin, createServer, CODE_LEN } from '../src/net/server.js';
import { PROTOCOL_VERSION, mergeCfg } from '../src/net/protocol.js';

const enc = new TextEncoder();
const dec = new TextDecoder();

/** 클라이언트가 보내는 것처럼 마스킹된 프레임을 만든다. */
function clientFrame(op: number, payload: Uint8Array, key = [0x37, 0xfa, 0x21, 0x3d]): Uint8Array {
  const len = payload.length;
  const ext = len >= 65536 ? 8 : len >= 126 ? 2 : 0;
  const out = new Uint8Array(2 + ext + 4 + len);
  out[0] = 0x80 | op;
  out[1] = 0x80 | (ext === 8 ? 127 : ext === 2 ? 126 : len);
  let off = 2;
  if (ext === 2) { out[2] = (len >> 8) & 0xff; out[3] = len & 0xff; off = 4; }
  else if (ext === 8) {
    out[6] = (len >>> 24) & 0xff; out[7] = (len >>> 16) & 0xff;
    out[8] = (len >>> 8) & 0xff; out[9] = len & 0xff;
    off = 10;
  }
  for (let i = 0; i < 4; i++) out[off + i] = key[i] as number;
  off += 4;
  for (let i = 0; i < len; i++) out[off + i] = (payload[i] as number) ^ (key[i & 3] as number);
  return out;
}

// ── 1. 핸드셰이크 ─────────────────────────────────────────────────────
test('Sec-WebSocket-Accept 는 RFC 6455 의 예제와 일치한다', () => {
  // RFC 6455 §1.3 의 예제: 키 dGhlIHNhbXBsZSBub25jZQ== → s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
  assert.equal(acceptKey('dGhlIHNhbXBsZSBub25jZQ=='), 's3pPLMBiTxaQ9kYGzzhZRbK+xOo=');
});

test('GUID 는 규격이 못박은 그 문자열', () => {
  assert.equal(WS_GUID, '258EAFA5-E914-47DA-95CA-C5AB0DC85B11');
  const manual = createHash('sha1').update('x' + WS_GUID).digest('base64');
  assert.equal(acceptKey('x'), manual);
});

// ── 2. 프레임 파서 ────────────────────────────────────────────────────
test('짧은 텍스트 프레임 하나', () => {
  const p = new FrameParser();
  const frames = p.push(clientFrame(OP.TEXT, enc.encode('Hello')));
  assert.equal(frames.length, 1);
  assert.equal(frames[0]!.op, OP.TEXT);
  assert.equal(frames[0]!.fin, true);
  assert.equal(dec.decode(frames[0]!.payload), 'Hello');
});

test('마스킹을 풀어야 원문이 나온다', () => {
  // RFC 6455 §5.7 의 예제: 마스킹된 "Hello"
  const raw = Uint8Array.from([0x81, 0x85, 0x37, 0xfa, 0x21, 0x3d, 0x7f, 0x9f, 0x4d, 0x51, 0x58]);
  const frames = new FrameParser().push(raw);
  assert.equal(dec.decode(frames[0]!.payload), 'Hello');
});

test('TCP 가 어떻게 쪼개도 같은 결과 — 1바이트씩 흘려 넣기', () => {
  const whole = clientFrame(OP.TEXT, enc.encode('조각나도 괜찮은가?'));
  const p = new FrameParser();
  const got: string[] = [];
  for (let i = 0; i < whole.length; i++) {
    for (const f of p.push(whole.subarray(i, i + 1))) got.push(dec.decode(f.payload));
  }
  assert.deepEqual(got, ['조각나도 괜찮은가?']);
});

test('한 번에 프레임 세 개가 와도 세 개로 나온다', () => {
  const a = clientFrame(OP.TEXT, enc.encode('하나'));
  const b = clientFrame(OP.TEXT, enc.encode('둘'));
  const c = clientFrame(OP.PING, new Uint8Array(0));
  const all = new Uint8Array(a.length + b.length + c.length);
  all.set(a, 0); all.set(b, a.length); all.set(c, a.length + b.length);
  const frames = new FrameParser().push(all);
  assert.equal(frames.length, 3);
  assert.deepEqual(frames.map((f) => f.op), [OP.TEXT, OP.TEXT, OP.PING]);
});

test('길이 126 이상은 2바이트 확장 길이를 쓴다', () => {
  const payload = enc.encode('x'.repeat(300));
  const frames = new FrameParser().push(clientFrame(OP.TEXT, payload));
  assert.equal(frames[0]!.payload.length, 300);
});

test('길이 65536 이상은 8바이트 확장 길이를 쓴다', () => {
  const payload = new Uint8Array(70000).fill(65);
  const frames = new FrameParser().push(clientFrame(OP.BIN, payload));
  assert.equal(frames[0]!.payload.length, 70000);
});

test('RSV 비트가 켜져 있으면 프로토콜 오류', () => {
  const f = clientFrame(OP.TEXT, enc.encode('x'));
  f[0] = (f[0] as number) | 0x40; // RSV1
  assert.throws(() => new FrameParser().push(f), WsProtocolError);
});

test('제어 프레임은 125바이트를 넘을 수 없다', () => {
  const f = clientFrame(OP.PING, new Uint8Array(200));
  assert.throws(() => new FrameParser().push(f), /제어 프레임/);
});

test('제어 프레임은 조각날 수 없다', () => {
  const f = clientFrame(OP.PING, new Uint8Array(4));
  f[0] = (f[0] as number) & 0x7f; // FIN 끄기
  assert.throws(() => new FrameParser().push(f), /조각날 수 없다/);
});

test('상한을 넘는 길이 헤더는 거부한다 (메모리 고갈 방어)', () => {
  const f = new Uint8Array(14);
  f[0] = 0x82; // BIN
  f[1] = 0x80 | 127;
  // 상위 4바이트를 0 으로 두고 하위에 큰 수를 넣는다
  f[6] = 0xff; f[7] = 0xff; f[8] = 0xff; f[9] = 0xff;
  assert.throws(() => new FrameParser().push(f), /너무 크다/);
  assert.ok(MAX_MESSAGE < 0xffffffff);
});

// ── 3. 인코더 ─────────────────────────────────────────────────────────
test('서버가 보내는 프레임은 마스킹하지 않는다', () => {
  const f = encodeFrame(OP.TEXT, enc.encode('hi'));
  assert.equal(f[0], 0x81);
  assert.equal((f[1] as number) & 0x80, 0, '마스크 비트가 꺼져 있어야 한다');
  assert.equal((f[1] as number) & 0x7f, 2);
});

test('인코더와 파서가 왕복한다 — 경계 길이 전부', () => {
  for (const n of [0, 1, 125, 126, 127, 65535, 65536, 65537]) {
    const payload = new Uint8Array(n);
    for (let i = 0; i < n; i++) payload[i] = (i * 7) & 0xff;
    // 서버가 보낸 프레임(비마스킹)을 그대로 파서에 넣어 본다
    const frames = new FrameParser().push(encodeFrame(OP.BIN, payload));
    assert.equal(frames.length, 1, `길이 ${n}`);
    assert.deepEqual(Array.from(frames[0]!.payload), Array.from(payload), `길이 ${n}`);
  }
});

test('마스킹해서 보낸 것도 왕복한다 (봇 클라이언트 경로)', () => {
  const payload = enc.encode('클라이언트가 보내는 프레임');
  const frames = new FrameParser().push(encodeFrame(OP.TEXT, payload, true));
  assert.equal(dec.decode(frames[0]!.payload), '클라이언트가 보내는 프레임');
});

// ── 4. 허브 ───────────────────────────────────────────────────────────
test('hello 없이는 아무것도 못 한다 (err hello)', () => {
  const h = new Hub(1);
  const pid = h.connect();
  assert.deepEqual(h.handle(pid, { t: 'create' }, 0), [{ to: pid, m: { t: 'err', code: 'hello' } }]);
  // ping 도 인사 뒤에야 받는다 — Go·파이썬 허브의 분기 순서가 그렇다
  assert.deepEqual(h.handle(pid, { t: 'ping', c: 1 }, 0), [{ to: pid, m: { t: 'err', code: 'hello' } }]);
});

test('hello 는 hi 로, create/join 은 joined 로 답한다 (규격서와 다른 실제 동작)', () => {
  const h = new Hub(1);
  const pid = h.connect();
  assert.deepEqual(
    h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION, name: '가' }, 0),
    [{ to: pid, m: { t: 'hi', pid, v: PROTOCOL_VERSION } }],
  );
  const j = h.handle(pid, { t: 'create' }, 0)[0]!.m;
  assert.equal(j.t, 'joined');
});

test('이미 방에 있으면 create/join 이 inroom 으로 거절된다', () => {
  const h = new Hub(1);
  const pid = h.connect();
  h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  h.handle(pid, { t: 'create' }, 0);
  assert.deepEqual(h.handle(pid, { t: 'create' }, 0), [{ to: pid, m: { t: 'err', code: 'inroom' } }]);
  assert.deepEqual(h.handle(pid, { t: 'join', room: 'ABCD' }, 0), [{ to: pid, m: { t: 'err', code: 'inroom' } }]);
});

test('cfg 의 0 은 "안 적었다"로 본다 (Go·파이썬의 mergeCfg 규칙)', () => {
  const h = new Hub(1);
  const pid = h.connect();
  h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  const j = h.handle(pid, { t: 'create', cfg: { max: 0, delay: 0, target: 'ko' } }, 0)[0]!.m;
  assert.equal(j.t, 'joined');
  if (j.t !== 'joined') return;
  assert.equal(j.cfg.max, 8, '0 은 기본값 유지');
  assert.equal(j.cfg.delay, 900);
  assert.equal(j.cfg.target, 'ko', '적은 건 반영');
  assert.equal(mergeCfg({ max: 99 }).max, 8, '8석을 넘길 수 없다');
});

test('프로토콜 버전이 다르면 err ver', () => {
  const h = new Hub(1);
  const pid = h.connect();
  assert.deepEqual(
    h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION + 1 }, 0),
    [{ to: pid, m: { t: 'err', code: 'ver' } }],
  );
});

test('create 는 방 코드를 주고 join 은 그 코드로 들어간다', () => {
  const h = new Hub(1);
  const a = h.connect();
  h.handle(a, { t: 'hello', v: PROTOCOL_VERSION, name: '가' }, 0);
  const hi = h.handle(a, { t: 'create', cfg: { max: 4 } }, 0);
  const m = hi[0]!.m;
  assert.equal(m.t, 'joined');
  if (m.t !== 'joined') return;
  assert.equal(m.code.length, CODE_LEN);
  assert.equal(m.cfg.max, 4);

  const b = h.connect();
  h.handle(b, { t: 'hello', v: PROTOCOL_VERSION, name: '나' }, 0);
  const joined = h.handle(b, { t: 'join', room: m.code }, 0);
  assert.equal(joined[0]!.m.t, 'joined');
});

test('없는 방 코드는 nosuch', () => {
  const h = new Hub(1);
  const pid = h.connect();
  h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  assert.deepEqual(
    h.handle(pid, { t: 'join', room: 'ZZZZ' }, 0),
    [{ to: pid, m: { t: 'err', code: 'nosuch' } }],
  );
});

test('방 코드는 헷갈리는 글자(0 O 1 I L)를 쓰지 않는다', () => {
  const h = new Hub(99);
  for (let k = 0; k < 300; k++) {
    const c = h.newCode();
    assert.ok(!/[01OIL]/.test(c), `코드에 헷갈리는 글자: ${c}`);
    h.rooms.set(c, null as never); // 다음 뽑기가 이 코드를 피하도록
  }
});

test('브로드캐스트는 그 방 사람들에게만 간다', () => {
  const h = new Hub(7);
  const a = h.connect(), b = h.connect(), c = h.connect();
  for (const p of [a, b, c]) h.handle(p, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  const hi = h.handle(a, { t: 'create', cfg: { max: 4 } }, 0)[0]!.m;
  if (hi.t !== 'joined') return assert.fail('joined 가 아니다');
  h.handle(b, { t: 'join', room: hi.code }, 0);
  // c 는 다른 방
  h.handle(c, { t: 'create' }, 0);

  const outs = h.handle(a, { t: 'seat', i: -1, kind: 'human', name: '가' }, 0);
  const targets = new Set(outs.map((o) => o.to));
  assert.deepEqual([...targets].sort(), [a, b], `${[...targets]}`);
});

test('마지막 사람이 나가면 방이 치워진다', () => {
  const h = new Hub(3);
  const a = h.connect();
  h.handle(a, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  const hi = h.handle(a, { t: 'create' }, 0)[0]!.m;
  if (hi.t !== 'joined') return assert.fail('joined 가 아니다');
  assert.equal(h.rooms.size, 1);
  h.disconnect(a, 0);
  assert.equal(h.rooms.size, 0, '빈 방이 남으면 코드가 영원히 쌓인다');
});

test('방에 안 들어간 채로 좌석을 요청하면 nosuch', () => {
  const h = new Hub(1);
  const pid = h.connect();
  h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  assert.deepEqual(
    h.handle(pid, { t: 'seat', i: -1, kind: 'human' }, 0),
    [{ to: pid, m: { t: 'err', code: 'nosuch' } }],
  );
});

test('인사한 뒤의 ping 은 pong 을 받는다 (지연 측정용)', () => {
  const h = new Hub(1);
  const pid = h.connect();
  h.handle(pid, { t: 'hello', v: PROTOCOL_VERSION }, 0);
  assert.deepEqual(h.handle(pid, { t: 'ping', c: 42 }, 0), [{ to: pid, m: { t: 'pong', c: 42 } }]);
});

// ── 5. 정적 파일 경로 ─────────────────────────────────────────────────
test('safeJoin 은 web/ 밖으로 나가지 못한다', () => {
  const root = '/srv/web';
  assert.equal(safeJoin(root, '/'), '/srv/web/index.html');
  assert.equal(safeJoin(root, '/app.js'), '/srv/web/app.js');
  assert.equal(safeJoin(root, '/js/../app.js'), '/srv/web/app.js');
  for (const evil of ['/../../etc/passwd', '/..%2f..%2fetc/passwd', '/a/../../../etc/passwd']) {
    const got = safeJoin(root, evil);
    assert.ok(got === null || got.startsWith(root + '/'), `${evil} → ${got}`);
  }
});

test('safeJoin 은 널 바이트를 거부한다', () => {
  assert.equal(safeJoin('/srv/web', '/a%00b.html'), null);
});

// ── 6. 진짜 소켓으로 왕복 ─────────────────────────────────────────────
//
// 여기서부터는 우리 파서를 안 쓴다. Node 24 의 표준 WebSocket 클라이언트가
// 우리 서버에 붙는다 — 남의 구현이 우리 핸드셰이크와 프레이밍을 인정하는지가 요점이다.
test('표준 WebSocket 클라이언트가 붙어서 대화한다', async () => {
  const srv = createServer({ quiet: true, seed: 5, webRoot: '/nonexistent' });
  const port = await srv.listen(0);
  try {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws`);
    const msgs: Record<string, unknown>[] = [];
    const gotMsg = (): Promise<Record<string, unknown>> =>
      new Promise((resolve) => {
        ws.addEventListener('message', (e) => {
          const m = JSON.parse(String((e as MessageEvent).data)) as Record<string, unknown>;
          msgs.push(m);
          resolve(m);
        }, { once: true });
      });

    await new Promise<void>((resolve, reject) => {
      ws.addEventListener('open', () => resolve(), { once: true });
      ws.addEventListener('error', () => reject(new Error('연결 실패')), { once: true });
    });

    ws.send(JSON.stringify({ t: 'hello', v: PROTOCOL_VERSION, name: '보라' }));
    assert.deepEqual(await gotMsg(), { t: 'hi', pid: 1, v: PROTOCOL_VERSION });

    ws.send(JSON.stringify({ t: 'ping', c: 7 }));
    assert.deepEqual(await gotMsg(), { t: 'pong', c: 7 });

    ws.send(JSON.stringify({ t: 'create', cfg: { max: 2 } }));
    const hi = await gotMsg();
    assert.equal(hi.t, 'joined');
    assert.equal(String(hi.code).length, CODE_LEN);

    ws.send(JSON.stringify({ t: 'seat', i: -1, kind: 'human', name: '보라' }));
    const room = await gotMsg();
    assert.equal(room.t, 'room');

    // 긴 메시지(확장 길이 경로)도 왕복하는지 — 이름을 길게 준다
    ws.send(JSON.stringify({ t: 'seat', i: 1, kind: 'ai', name: '봇'.repeat(200), lv: 'max' }));
    const room2 = await gotMsg();
    assert.equal(room2.t, 'room');
    const seats = room2.seats as { name: string }[];
    assert.equal(seats.length, 2);
    assert.equal(seats[1]!.name.length, 200);

    ws.close();
  } finally {
    await srv.close();
  }
});

test('/ws 가 아닌 업그레이드 요청은 거절한다', async () => {
  const srv = createServer({ quiet: true, webRoot: '/nonexistent' });
  const port = await srv.listen(0);
  try {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/nope`);
    const closed = await new Promise<boolean>((resolve) => {
      ws.addEventListener('error', () => resolve(true), { once: true });
      ws.addEventListener('open', () => resolve(false), { once: true });
    });
    assert.equal(closed, true, '엉뚱한 경로로는 연결되면 안 된다');
  } finally {
    await srv.close();
  }
});

test('두 클라이언트가 같은 방에서 서로의 로비 갱신을 본다', async () => {
  const srv = createServer({ quiet: true, seed: 11, webRoot: '/nonexistent' });
  const port = await srv.listen(0);
  const open = async (): Promise<WebSocket> => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws`);
    await new Promise<void>((res, rej) => {
      ws.addEventListener('open', () => res(), { once: true });
      ws.addEventListener('error', () => rej(new Error('연결 실패')), { once: true });
    });
    return ws;
  };
  const next = (ws: WebSocket): Promise<Record<string, unknown>> =>
    new Promise((resolve) => {
      ws.addEventListener('message', (e) => {
        resolve(JSON.parse(String((e as MessageEvent).data)) as Record<string, unknown>);
      }, { once: true });
    });

  try {
    const a = await open();
    a.send(JSON.stringify({ t: 'hello', v: PROTOCOL_VERSION, name: 'A' }));
    assert.equal((await next(a)).t, 'hi');
    a.send(JSON.stringify({ t: 'create', cfg: { max: 4 } }));
    const joined = await next(a);
    assert.equal(joined.t, 'joined');
    const code = String(joined.code);

    const b = await open();
    b.send(JSON.stringify({ t: 'hello', v: PROTOCOL_VERSION, name: 'B' }));
    assert.equal((await next(b)).t, 'hi');
    const bJoined = next(b);
    b.send(JSON.stringify({ t: 'join', room: code }));
    assert.equal((await bJoined).t, 'joined');

    // A 가 앉으면 B 도 room 갱신을 받아야 한다
    const bRoom = next(b);
    a.send(JSON.stringify({ t: 'seat', i: -1, kind: 'human', name: 'A' }));
    const got = await bRoom;
    assert.equal(got.t, 'room');
    assert.equal((got.seats as unknown[]).length, 1);

    a.close();
    b.close();
  } finally {
    await srv.close();
  }
});
