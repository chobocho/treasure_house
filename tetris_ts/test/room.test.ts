// room.test.ts — 골든 벡터로 TS room 엔진을 검증한다.
//
// 부 3 의 JS(test_room.mjs)·Go(server_test.go)·파이썬(test_server.py) 하니스와
// 하는 일이 똑같다: 같은 JSON 을 읽어 같은 순서로 밀어 넣고, 나온 출력을
// **순서까지** 그대로 비교한다. TS 는 이 표를 재현하는 네 번째 구현이다.
//
// 벡터 파일은 복사하지 않고 tetris_net/protocol_vectors.json 을 그대로 읽는다.
// 복사본을 두면 언젠가 한쪽만 고쳐지고, 그때부터 "네 구현이 같다"는 말이 거짓이 된다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { Room, DEFAULTS } from '../src/net/room.js';
import {
  snapshot, unsnapshot, packState, heightOf, rleEncode, rleDecode,
  toBase64, fromBase64, S, PROTOCOL_VERSION,
  type ClientMsg, type Outbound, type RoomCfg,
} from '../src/net/protocol.js';
import { Tetris, ST, W, VIS, GARBAGE } from '../src/core.js';
import { Ai } from '../src/ai.js';
import { paintBoard } from '../src/trace.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const VECTORS = join(HERE, '..', '..', '..', 'tetris_net', 'protocol_vectors.json');

interface VecStep {
  pid: number;
  at: number;
  m: ClientMsg;
  out: Outbound[];
}
interface VecCase {
  name: string;
  why: string;
  cfg: Partial<RoomCfg>;
  seed: number;
  setup: { pid: number; at: number; m: ClientMsg }[];
  steps: VecStep[];
}
interface VectorFile {
  v: number;
  note: string;
  cases: VecCase[];
}

const VEC = JSON.parse(readFileSync(VECTORS, 'utf8')) as VectorFile;

test('골든 벡터 파일을 읽었고 프로토콜 버전이 맞다', () => {
  assert.equal(VEC.v, PROTOCOL_VERSION);
  assert.ok(VEC.cases.length >= 10, `사례 ${VEC.cases.length}개`);
});

// ── 1. 골든 벡터 재현 ─────────────────────────────────────────────────
for (const c of VEC.cases) {
  test(`벡터: ${c.name} — ${c.why}`, () => {
    const room = new Room(c.cfg, c.seed);
    for (const s of c.setup) room.handle(s.pid, s.m, s.at | 0);
    c.steps.forEach((s, k) => {
      const got = room.handle(s.pid, s.m, s.at | 0);
      assert.deepEqual(
        got, s.out,
        `${c.name} #${k + 1} (${s.m.t})\n  기대: ${JSON.stringify(s.out)}\n  실제: ${JSON.stringify(got)}`,
      );
    });
  });
}

// ── 2. 벡터가 다루지 않는 것 ──────────────────────────────────────────
test('난수열은 규격의 xorshift32 그대로다', () => {
  const r = new Room({ max: 2 }, 1);
  const got = [r.rng(), r.rng(), r.rng(), r.rng(), r.rng()];
  assert.deepEqual(got, [270369, 67634689, 2647435461, 307599695, 2398689233]);
});

test('좌석 8석 · PC 4대 — 요구사항 그대로의 최대 구성', () => {
  const r = new Room({ max: 8, perPeer: 2 }, 1);
  for (let pid = 1; pid <= 4; pid++) {
    r.handle(pid, { t: 'seat', i: -1, kind: 'human', name: `P${pid}a` }, 0);
    r.handle(pid, { t: 'seat', i: -1, kind: 'ai', name: `P${pid}b`, lv: 'hard' }, 0);
    r.handle(pid, { t: 'ready', v: true }, 0);
  }
  const outs = r.handle(1, { t: 'start' }, 0);
  const m = (outs[0] as Outbound).m;
  assert.equal(m.t, 'start');
  if (m.t !== 'start') return;
  assert.equal(m.seats.length, 8);
  assert.deepEqual(m.seats.map((s) => s.pid), [1, 1, 2, 2, 3, 3, 4, 4]);
  // 대전이 시작된 뒤의 9번째 좌석 요청은 'seat' 이 아니라 'phase' 로 거절된다
  const nine = r.handle(5, { t: 'seat', i: -1, kind: 'human', name: 'X' }, 0);
  assert.deepEqual(nine, [{ to: 5, m: { t: 'err', code: 'phase' } }]);
});

test('PC 당 좌석 수 상한을 넘으면 full', () => {
  const r = new Room({ max: 8, perPeer: 2 }, 1);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'a' }, 0);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'b' }, 0);
  const third = r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'c' }, 0);
  assert.deepEqual(third, [{ to: 1, m: { t: 'err', code: 'full' } }]);
});

test('방장은 가장 작은 pid 이고, 나가면 다음 사람에게 넘어간다', () => {
  const r = new Room({ max: 4 }, 1);
  r.handle(3, { t: 'seat', i: -1, kind: 'human', name: 'c' }, 0);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'a' }, 0);
  assert.equal(r.host(), 1);
  const out = r.handle(1, { t: 'bye' }, 0);
  const m = (out[0] as Outbound).m;
  assert.equal(m.t, 'room');
  if (m.t === 'room') assert.equal(m.host, 3, '1번이 나갔으니 3번이 방장');
});

test('사람 좌석이 준비 안 되면 start 가 거절된다 (AI 는 기다리지 않는다)', () => {
  const r = new Room({ max: 4 }, 1);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'a' }, 0);
  r.handle(1, { t: 'seat', i: -1, kind: 'ai', name: 'bot', lv: 'max' }, 0);
  assert.deepEqual(r.handle(1, { t: 'start' }, 0), [{ to: 1, m: { t: 'err', code: 'ready' } }]);
  r.handle(1, { t: 'ready', v: true }, 0);
  const ok = r.handle(1, { t: 'start' }, 0);
  assert.equal((ok[0] as Outbound).m.t, 'start');
});

test('빈 방은 start 할 수 없다', () => {
  const r = new Room({ max: 4 }, 1);
  r.handle(1, { t: 'ready', v: true }, 0); // peers 에만 들어간다
  assert.deepEqual(r.handle(1, { t: 'start' }, 0), [{ to: 1, m: { t: 'err', code: 'seat' } }]);
});

test('방장이 아니면 start 가 거절된다', () => {
  const r = new Room({ max: 4 }, 1);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'a' }, 0);
  r.handle(2, { t: 'seat', i: -1, kind: 'human', name: 'b' }, 0);
  r.handle(1, { t: 'ready', v: true }, 0);
  r.handle(2, { t: 'ready', v: true }, 0);
  assert.deepEqual(r.handle(2, { t: 'start' }, 0), [{ to: 2, m: { t: 'err', code: 'host' } }]);
});

test('모르는 메시지는 조용히 무시한다', () => {
  const r = new Room({ max: 2 }, 1);
  assert.deepEqual(r.handle(1, { t: 'nope' } as unknown as ClientMsg, 0), []);
});

test('bye 는 peers 에 다시 넣지 않는다 (안 그러면 방장이 안 바뀐다)', () => {
  const r = new Room({ max: 2 }, 1);
  r.handle(1, { t: 'seat', i: -1, kind: 'human', name: 'a' }, 0);
  r.handle(1, { t: 'bye' }, 0);
  assert.equal(r.peers.has(1), false);
  assert.deepEqual(r.handle(1, { t: 'bye' }, 0), [], '두 번째 bye 는 아무 일도 없다');
});

// ── 3. 인코딩 ─────────────────────────────────────────────────────────
test('base64 왕복 — 길이 0~200 전부', () => {
  for (let n = 0; n <= 200; n++) {
    const b = new Uint8Array(n);
    for (let i = 0; i < n; i++) b[i] = (i * 37 + n) & 0xff;
    const back = fromBase64(toBase64(b));
    assert.deepEqual(Array.from(back), Array.from(b), `길이 ${n}`);
  }
});

test('base64 는 표준 문자표와 패딩을 쓴다', () => {
  assert.equal(toBase64(Uint8Array.from([0])), 'AA==');
  assert.equal(toBase64(Uint8Array.from([0, 0])), 'AAA=');
  assert.equal(toBase64(Uint8Array.from([0, 0, 0])), 'AAAA');
  assert.equal(toBase64(Uint8Array.from([255, 255, 255])), '////');
  assert.equal(toBase64(Uint8Array.from([251, 255, 191])), '+/+/');
});

test('base64 는 Node 의 Buffer 구현과 같은 결과를 낸다', () => {
  for (let n = 0; n < 64; n++) {
    const b = new Uint8Array(n);
    for (let i = 0; i < n; i++) b[i] = (i * 91 + 7) & 0xff;
    assert.equal(toBase64(b), Buffer.from(b).toString('base64'), `길이 ${n}`);
  }
});

test('RLE: 빈 판은 13바이트 (200 = 16×12 + 8)', () => {
  const cells = new Uint8Array(VIS * W);
  const raw = rleEncode(cells);
  assert.equal(raw.length, 13);
  assert.equal(toBase64(raw).length, 20, '빈 판의 스냅샷은 base64 20자');
});

test('RLE 런 길이는 16 에서 끊긴다 (4비트)', () => {
  const cells = new Uint8Array(40).fill(3);
  const raw = rleEncode(cells);
  assert.equal(raw.length, 3, '16+16+8');
  assert.equal(raw[0], (15 << 4) | 3);
  assert.equal(raw[2], (7 << 4) | 3);
});

test('RLE 왕복 — 무작위 판 200개', () => {
  let s = 12345 >>> 0;
  const rnd = (): number => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s; };
  const out = new Uint8Array(VIS * W);
  for (let k = 0; k < 200; k++) {
    const cells = new Uint8Array(VIS * W);
    for (let i = 0; i < cells.length; i++) cells[i] = rnd() % 9; // 0..8
    const n = rleDecode(rleEncode(cells), out);
    assert.equal(n, cells.length);
    assert.deepEqual(Array.from(out), Array.from(cells), `${k}번째 판`);
  }
});

test('실전 스냅샷 크기 — 규격 §6 의 "100바이트 이하"는 사실이 아니다', () => {
  // 규격서는 "꽉 찬 판도 100바이트를 넘지 않는다"고 적었지만, AI 가 실제로 둔 판
  // 2000개를 재 보면 평균 70바이트, 최악 118바이트다. 200칸이 전부 다른 색으로
  // 번갈아 나오면 이론적 최악은 200바이트(런 길이 1이 200번)다.
  // 규격서의 수치가 아니라 **잰 값**을 테스트에 적는다.
  const g = new Tetris(1);
  const ai = new Ai(g);
  let worst = 0, sum = 0, n = 0;
  for (const seed of [1, 2, 3]) {
    ai.game.init(seed);
    for (let k = 0; k < 400 && (g.stats[ST.STATE] as number) === 0; k++) {
      ai.step();
      const bytes = rleEncode(cellsOf(g)).length;
      worst = Math.max(worst, bytes);
      sum += bytes; n++;
    }
  }
  assert.ok(n > 1000, `표본이 ${n}개뿐이면 의미가 없다`);
  assert.ok(sum / n < 90, `평균 ${(sum / n).toFixed(1)}바이트`);
  assert.ok(worst <= 130, `실전 최악 ${worst}바이트`);
  assert.ok(worst > 100, `규격의 "100바이트 이하"가 실제로 깨진다는 것도 확인 (${worst})`);

  // 이론적 최악: 런이 전부 길이 1
  const alt = new Uint8Array(VIS * W);
  for (let i = 0; i < alt.length; i++) alt[i] = i % 2 ? 1 : 2;
  assert.equal(rleEncode(alt).length, VIS * W, '교대 무늬는 압축이 전혀 안 된다');
});

/** 스냅샷이 보는 것과 같은 칸 배열 (굳은 블록 + 현재 조각). */
function cellsOf(g: Tetris): Uint8Array {
  const cells = new Uint8Array(VIS * W);
  cells.set(g.cells);
  for (let i = 0; i < cells.length; i++) {
    const o = g.overlay[i] as number;
    if (o >= 1 && o <= 7) cells[i] = o;
  }
  return cells;
}

// ── 4. 스냅샷과 상태 배열 ─────────────────────────────────────────────
test('스냅샷은 굳은 블록과 현재 조각을 같이 담는다', () => {
  const g = new Tetris(1);
  paintBoard(g.board, ['##########'.replace('#', '.')]); // 바닥에 한 줄(x=0 만 빔)
  g.setPiece(3); // O
  const b = snapshot(g);
  const out = new Uint8Array(VIS * W);
  assert.equal(unsnapshot(b, out), VIS * W);
  // 바닥 줄에 가비지가, 위쪽에 현재 조각(색 4)이 보여야 한다
  assert.equal(out[(VIS - 1) * W + 1], GARBAGE);
  assert.ok(Array.from(out).includes(4), '현재 조각이 스냅샷에 있어야 한다');
});

test('상태 배열은 12칸이고 규격의 자리에 규격의 값이 있다', () => {
  const g = new Tetris(1);
  g.garbage(3, 4);
  const s = packState(g);
  assert.equal(s.length, S.COUNT);
  assert.equal(s[S.STATE], g.stats[ST.STATE]);
  assert.equal(s[S.SCORE], g.stats[ST.SCORE]);
  assert.equal(s[S.LINES], g.stats[ST.LINES]);
  assert.equal(s[S.PIECES], g.stats[ST.PIECES]);
  assert.equal(s[S.HEIGHT], 3, '3줄 솟았으니 높이 3');
  assert.equal(s[S.PENDING], g.stats[ST.PENDING]);
  assert.equal(s[S.HOLD], -1);
});

test('heightOf 는 가장 높은 열의 높이 — ko 타깃팅이 읽는 값', () => {
  const g = new Tetris(1);
  assert.equal(heightOf(g), 0, '빈 판은 0');
  paintBoard(g.board, ['.........#', '..........', '#.........']);
  assert.equal(heightOf(g), 3, '가장 높은 열이 3줄');
});

test('기본 설정은 규격 §2 의 표와 같다', () => {
  assert.equal(DEFAULTS.max, 8);
  assert.equal(DEFAULTS.perPeer, 2);
  assert.equal(DEFAULTS.target, 'random');
  assert.equal(DEFAULTS.delay, 900);
  assert.equal(DEFAULTS.cap, 8);
  assert.equal(DEFAULTS.hitTTL, 8000);
});
