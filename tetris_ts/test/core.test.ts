// core.test.ts — TS 코어의 단위 테스트 + C++ wasm 골든 트레이스 대조.
//
// 이 파일의 절반은 "규칙이 맞는가"(단위 테스트), 나머지 절반은 "부 1·2 의 wasm 과
// 한 글자도 다르지 않은가"(파리티)다. 뒤쪽이 훨씬 강하다 — 사람이 생각해 낸 경우만
// 검사하는 게 아니라 1500스텝 × 6시드의 모든 중간 상태를 대조하기 때문이다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  Tetris, ACT, ST, STATE, W, H, HIDDEN, SPAWN_X, SHAPES, GARBAGE,
  attackFor, boardHash, dumpBoard, GRAVITY_MS, LOCK_MS,
} from '../src/core.js';
import {
  runTrace, runPlacementTrace, runComboTrace, paintBoard, TRACE_SEEDS, TRACE_STEPS,
  statsHash, COMBO_SCENARIOS,
  type ComboTarget, type TraceResult, type PlacementCase, type ComboStep,
} from '../src/trace.js';

const HERE = dirname(fileURLToPath(import.meta.url));
// dist/test/ 에서 실행되므로 두 단계 위가 프로젝트 루트다.
const GOLDEN = join(HERE, '..', '..', 'test', 'golden', 'core_traces.json');

/** Tetris 인스턴스를 트레이스 러너가 요구하는 인터페이스로 감싼다. */
class TsTarget implements ComboTarget {
  readonly g = new Tetris(1);
  init(seed: number): void { this.g.init(seed); }
  press(act: number): void { this.g.press(act); }
  release(act: number): void { this.g.release(act); }
  update(dtMs: number): void { this.g.update(dtMs); }
  queueGarbage(n: number): void { this.g.queueGarbage(n); }
  paint(rows: readonly string[]): void { paintBoard(this.g.board, rows); }
  setPiece(piece: number): void { this.g.setPiece(piece); }
  board(): Uint8Array { return this.g.board; }
  stats(): Int32Array { return this.g.stats; }
}

// ── 1. 기본 불변식 ────────────────────────────────────────────────────
test('초기 상태: 레벨 1, 콤보 -1, 홀드 없음, 진행 중', () => {
  const g = new Tetris(1);
  assert.equal(g.stats[ST.LEVEL], 1);
  assert.equal(g.stats[ST.COMBO], -1);
  assert.equal(g.stats[ST.HOLD], -1);
  assert.equal(g.stats[ST.STATE], STATE.PLAY);
  assert.equal(g.stats[ST.SCORE], 0);
  assert.equal(g.stats[ST.PIECES], 1); // 첫 조각이 이미 스폰되어 있다
  assert.equal(g.stats[ST.GRAVITY], GRAVITY_MS[1]);
  assert.equal(g.curX, SPAWN_X);
  assert.equal(g.curY, HIDDEN);
});

test('시드 0 은 기본 시드로 대체된다 (0 이면 xorshift 가 영원히 0)', () => {
  const a = new Tetris(0);
  const b = new Tetris(0x9e3779b9);
  assert.equal(boardHash(a.board), boardHash(b.board));
  const pa: number[] = [], pb: number[] = [];
  for (let i = 0; i < 30; i++) { a.press(ACT.HARD); pa.push(a.curPiece); }
  for (let i = 0; i < 30; i++) { b.press(ACT.HARD); pb.push(b.curPiece); }
  assert.deepEqual(pa, pb);
});

test('7-bag: 연속한 7조각은 항상 7종을 한 번씩', () => {
  const g = new Tetris(42);
  const seq: number[] = [g.curPiece];
  // 죽으면 press 가 무시되어 같은 조각이 반복 기록된다 — 살아 있는 동안만 모은다.
  // 대신 판을 매번 비워서 300조각까지 뽑는다(봉지 경계를 40번 넘긴다).
  for (let i = 0; i < 300; i++) {
    g.press(ACT.HARD);
    g.board.fill(0);
    assert.equal(g.stats[ST.STATE], STATE.PLAY);
    seq.push(g.curPiece);
  }
  for (let i = 0; i + 7 <= seq.length; i += 7) {
    const bag = new Set(seq.slice(i, i + 7));
    assert.equal(bag.size, 7, `${i}번째 봉지가 7종이 아니다: ${seq.slice(i, i + 7)}`);
  }
});

test('조각 모양표: 각 조각의 각 회전은 정확히 4칸', () => {
  for (let p = 0; p < 7; p++) {
    for (let r = 0; r < 4; r++) {
      let n = 0;
      const m = SHAPES[p]![r]!;
      for (let i = 0; i < 16; i++) if (m & (1 << i)) n++;
      assert.equal(n, 4, `조각 ${p} 회전 ${r} 의 칸 수`);
    }
  }
});

test('O 조각은 회전해도 모양이 같다', () => {
  for (let r = 1; r < 4; r++) assert.equal(SHAPES[3]![r], SHAPES[3]![0]);
});

// ── 2. 충돌·이동 ──────────────────────────────────────────────────────
test('좌우 벽 밖은 충돌, 천장 위는 충돌 아님', () => {
  const g = new Tetris(1);
  g.setPiece(1); // J
  assert.equal(g.collide(1, 0, -1, HIDDEN), true);
  assert.equal(g.collide(1, 0, W - 1, HIDDEN), true);
  assert.equal(g.collide(1, 0, 0, -HIDDEN), false); // 숨은 줄 위쪽
});

test('하드드롭은 바닥까지 내려가 굳는다 — 1칸당 2점', () => {
  const g = new Tetris(1);
  g.setPiece(3); // O — 항상 2x2, 계산이 명확하다
  const before = g.stats[ST.SCORE]!;
  g.press(ACT.HARD);
  // O 는 spawn_y=4, 셀은 y+1..y+2 (0x0066). 바닥(H-1)까지 → 낙하 거리 = H-1-2-4 = 17...
  // 정확한 수치보다 "점수가 낙하 거리 × 2 로 증가"가 규칙이므로 짝수·양수만 확인한다.
  const gained = g.stats[ST.SCORE]! - before;
  assert.ok(gained > 0 && gained % 2 === 0, `하드드롭 점수 ${gained}`);
  // 바닥 두 줄에 O 가 남아 있어야 한다
  const rows = dumpBoard(g.board).split('\n');
  assert.match(rows[19]!, /4/);
  assert.match(rows[18]!, /4/);
});

// ── 3. 줄 지우기·점수 ─────────────────────────────────────────────────
/** 왼쪽 1칸 우물이 n 줄 있는 판 — I 를 세워 꽂으면 정확히 n 줄이 지워진다.
 *  맨 아래에 "절대 안 지워지는 줄"을 한 줄 깔아 두는 게 요령이다.
 *  이게 없으면 우물을 메우는 순간 판이 텅 비어 **퍼펙트 클리어 보너스**가 붙어서,
 *  싱글/더블/테트리스 점수를 재려던 테스트가 엉뚱한 수를 보게 된다. */
function wellBoard(n: number): string[] {
  const rows: string[] = [];
  for (let i = 0; i < n; i++) rows.push('.#########');
  rows.push('#########.'); // 바닥 받침 — x=9 가 비어 있어 절대 안 찬다
  return rows;
}

function dropIVertical(g: Tetris): void {
  g.setPiece(0); // I
  g.press(ACT.CW); // 세로로 (rot1 = 0x2222, x offset 1)
  for (let i = 0; i < 6; i++) g.press(ACT.LEFT);
  g.press(ACT.HARD);
}

test('테트리스(4줄)는 800×레벨', () => {
  const g = new Tetris(1);
  paintBoard(g.board, wellBoard(4));
  dropIVertical(g);
  assert.equal(g.stats[ST.CLEAR], 4);
  assert.equal(g.stats[ST.GAIN], 800 * 1 + 50 * 0 * 1); // 콤보 0 → 보너스 0
  assert.equal(g.stats[ST.B2B], 1);
  assert.equal(g.stats[ST.LINES], 4);
});

test('싱글 100 · 더블 300 · 트리플 500 (레벨 1)', () => {
  for (const [n, want] of [[1, 100], [2, 300], [3, 500]] as const) {
    const g = new Tetris(1);
    paintBoard(g.board, wellBoard(n));
    dropIVertical(g);
    assert.equal(g.stats[ST.CLEAR], n, `${n}줄 지움`);
    assert.equal(g.stats[ST.GAIN], want, `${n}줄 점수`);
    assert.equal(g.stats[ST.B2B], 0, `${n}줄은 어려운 클리어가 아니다`);
  }
});

test('Back-to-Back 테트리스는 ×1.5', () => {
  const g = new Tetris(1);
  paintBoard(g.board, wellBoard(4));
  dropIVertical(g);
  assert.equal(g.stats[ST.B2B], 1);
  // 두 번째 테트리스: 800×1.5 = 1200, 콤보 1 보너스 50 → 1250
  paintBoard(g.board, wellBoard(4));
  dropIVertical(g);
  assert.equal(g.stats[ST.CLEAR], 4);
  assert.equal(g.stats[ST.GAIN], 1200 + 50 * 1 * 1);
});

test('줄을 못 지우면 콤보가 -1 로 끊긴다', () => {
  const g = new Tetris(1);
  paintBoard(g.board, wellBoard(1));
  dropIVertical(g);
  assert.equal(g.stats[ST.COMBO], 0);
  g.setPiece(3);
  g.press(ACT.HARD);
  assert.equal(g.stats[ST.COMBO], -1);
});

test('레벨은 10줄마다 오르고 20 에서 멈춘다', () => {
  const g = new Tetris(1);
  for (let k = 0; k < 60; k++) {
    paintBoard(g.board, wellBoard(4));
    dropIVertical(g);
  }
  assert.equal(g.stats[ST.LEVEL], 20);
  assert.equal(g.stats[ST.GRAVITY], GRAVITY_MS[20]);
});

test('퍼펙트 클리어 보너스 1000×레벨', () => {
  // 두 줄의 오른쪽 2칸만 비워 두고 O 를 꽂으면 두 줄이 동시에 차서 판이 텅 빈다.
  const g = new Tetris(1);
  paintBoard(g.board, ['########..', '########..']);
  g.setPiece(3); // O — 2x2
  for (let i = 0; i < 8; i++) g.press(ACT.RIGHT); // 벽에 막힐 때까지
  g.press(ACT.HARD);
  assert.equal(g.stats[ST.CLEAR], 2);
  assert.equal(g.stats[ST.PERFECT], 1);
  assert.equal(g.stats[ST.GAIN], 300 + 1000); // 더블 300 + 퍼펙트 1000, 콤보 0
  assert.equal(boardHash(g.board), boardHash(new Uint8Array(H * W)), '판이 완전히 비어야 한다');
  // 퍼펙트는 공격 +10 이 붙는다 — 대전에서 가장 큰 한 방
  assert.equal(g.stats[ST.ATTACK], 1 + 10);
});

// ── 4. 대전 규칙 ──────────────────────────────────────────────────────
test('공격 표: 싱글 0, 더블 1, 트리플 2, 테트리스 4', () => {
  assert.equal(attackFor(1, 0, 0, 0, false), 0);
  assert.equal(attackFor(2, 0, 0, 0, false), 1);
  assert.equal(attackFor(3, 0, 0, 0, false), 2);
  assert.equal(attackFor(4, 0, 0, 0, false), 4);
});

test('공격 표: T스핀·미니·B2B·콤보·퍼펙트', () => {
  assert.equal(attackFor(1, 2, 0, 0, false), 2); // T스핀 싱글
  assert.equal(attackFor(2, 2, 0, 0, false), 4); // T스핀 더블
  assert.equal(attackFor(3, 2, 0, 0, false), 6); // T스핀 트리플
  assert.equal(attackFor(1, 1, 0, 0, false), 0); // 미니 싱글
  assert.equal(attackFor(2, 1, 0, 0, false), 1); // 미니 더블
  assert.equal(attackFor(4, 0, 1, 0, false), 5); // 테트리스 + B2B
  assert.equal(attackFor(2, 0, 0, 5, false), 1 + 2); // 콤보 5 보너스 2
  assert.equal(attackFor(2, 0, 0, 99, false), 1 + 5); // 콤보는 12 에서 상한
  assert.equal(attackFor(2, 0, 0, 0, true), 1 + 10); // 퍼펙트 +10
  assert.equal(attackFor(0, 0, 1, 9, true), 0); // 못 지우면 무조건 0
});

test('가비지: 대기 → 줄 못 지운 락에서 솟아오름', () => {
  const g = new Tetris(1);
  g.queueGarbage(3);
  assert.equal(g.stats[ST.PENDING], 3);
  g.setPiece(3);
  g.press(ACT.HARD); // 줄을 못 지운다 → 3줄 솟아오른다
  assert.equal(g.stats[ST.GARBAGE_RECV], 3);
  assert.equal(g.stats[ST.PENDING], 0);
  const rows = dumpBoard(g.board).split('\n');
  for (let i = 17; i <= 19; i++) {
    assert.equal((rows[i]!.match(/#/g) ?? []).length, W - 1, `${i}번 줄은 구멍 1개짜리 가비지`);
  }
});

test('가비지 상한: 한 락에 최대 8줄만', () => {
  const g = new Tetris(1);
  g.queueGarbage(20);
  g.setPiece(3);
  g.press(ACT.HARD);
  assert.equal(g.stats[ST.GARBAGE_RECV], 8);
  assert.equal(g.stats[ST.PENDING], 12);
});

test('상쇄: 내 공격이 먼저 내 대기줄을 지운다', () => {
  const g = new Tetris(1);
  paintBoard(g.board, wellBoard(4));
  g.queueGarbage(3);
  dropIVertical(g); // 테트리스 → 공격 4
  assert.equal(g.stats[ST.PENDING], 0); // 3줄 상쇄
  assert.equal(g.stats[ST.ATTACK], 1); // 남은 1줄만 상대에게
  assert.equal(g.stats[ST.GARBAGE_RECV], 0); // 솟아오르지 않았다
});

test('가비지 n줄은 같은 구멍을 공유한다(클린 가비지)', () => {
  const g = new Tetris(1);
  g.garbage(5, 3);
  const rows = dumpBoard(g.board).split('\n');
  for (let i = 15; i <= 19; i++) assert.equal(rows[i]!, '###.######'.replace(/#/g, '#'));
  for (let i = 15; i <= 19; i++) assert.equal(rows[i]![3], '.');
});

// ── 5. 홀드 ───────────────────────────────────────────────────────────
test('홀드는 조각당 1회', () => {
  const g = new Tetris(7);
  const first = g.curPiece;
  g.press(ACT.HOLD);
  assert.equal(g.stats[ST.HOLD], first);
  const second = g.curPiece;
  g.press(ACT.HOLD); // 무시되어야 한다
  assert.equal(g.curPiece, second);
  assert.equal(g.stats[ST.HOLD], first);
});

test('두 번째 홀드는 스왑', () => {
  const g = new Tetris(7);
  const a = g.curPiece;
  g.press(ACT.HOLD);
  const b = g.curPiece;
  g.press(ACT.HARD);
  g.press(ACT.HOLD);
  assert.equal(g.curPiece, a);
  assert.equal(g.stats[ST.HOLD], g.holdPiece);
  assert.notEqual(b, undefined);
});

// ── 6. 타이밍 ─────────────────────────────────────────────────────────
test('락 유예 500ms 가 지나야 굳는다', () => {
  const g = new Tetris(1);
  g.setPiece(3);
  // update 는 dt 를 100ms 로 자른다(탭 전환 방어). 그래서 큰 dt 를 한 번 주는 게 아니라
  // 100ms 씩 여러 번 줘야 시간이 실제로 흐른다 — 이 클램프를 잊으면 테스트가 거짓말을 한다.
  while (!g.collide(g.curPiece, g.curRot, g.curX, g.curY + 1)) g.update(100);
  const pieces = g.stats[ST.PIECES]!;
  // 착지시킨 그 호출에서 이미 유예가 100ms 쌓였다. 300ms 를 더해 400ms.
  for (let i = 0; i < 3; i++) g.update(100);
  assert.equal(g.stats[ST.PIECES], pieces, `400ms 에서는 아직 굳으면 안 된다 (LOCK_MS=${LOCK_MS})`);
  g.update(100); // 500ms
  assert.equal(g.stats[ST.PIECES], pieces + 1, '이제 굳어야 한다');
});

test('일시정지 중에는 시간이 흐르지 않는다', () => {
  const g = new Tetris(1);
  g.press(ACT.PAUSE);
  assert.equal(g.stats[ST.STATE], STATE.PAUSE);
  const e = g.stats[ST.ELAPSED]!;
  g.update(500);
  assert.equal(g.stats[ST.ELAPSED], e);
  g.press(ACT.PAUSE);
  assert.equal(g.stats[ST.STATE], STATE.PLAY);
});

test('dt 는 100ms 로 잘린다 (탭 전환 방어)', () => {
  const g = new Tetris(1);
  g.update(5000);
  assert.equal(g.stats[ST.ELAPSED], 100);
});

// ── 7. 해시 도구 자체의 건전성 ────────────────────────────────────────
test('boardHash 는 다른 판을 구별한다', () => {
  const a = new Uint8Array(H * W);
  const b = new Uint8Array(H * W);
  assert.equal(boardHash(a), boardHash(b));
  b[0] = 1;
  assert.notEqual(boardHash(a), boardHash(b));
  const c = new Uint8Array(H * W);
  c[H * W - 1] = 1;
  assert.notEqual(boardHash(b), boardHash(c));
  assert.notEqual(boardHash(a), 0);
});

test('statsHash 는 필드 하나만 달라도 바뀐다', () => {
  const a = new Int32Array(ST.COUNT);
  const b = new Int32Array(ST.COUNT);
  assert.equal(statsHash(a), statsHash(b));
  b[ST.COMBO] = -1;
  assert.notEqual(statsHash(a), statsHash(b));
});

// ── 8. C++ wasm 파리티 ────────────────────────────────────────────────
interface GoldenFile {
  v: number;
  steps: number;
  traces: TraceResult[];
  placement: PlacementCase[];
  combo: ComboStep[];
}

const golden: GoldenFile | null = existsSync(GOLDEN)
  ? (JSON.parse(readFileSync(GOLDEN, 'utf8')) as GoldenFile)
  : null;

/** 골든 파일이 없으면 파리티 테스트는 "통과"가 아니라 실패해야 한다.
 *  없는 정답지를 조용히 건너뛰는 순간 이 프로젝트의 검증 전략 전체가 무너진다. */
function requireGolden(): GoldenFile {
  if (!golden) throw new Error(`${GOLDEN} 이 없다 — 먼저 \`make golden\` 을 돌려라`);
  return golden;
}

test('골든 트레이스 파일이 있어야 한다 (make golden)', () => {
  const gd = requireGolden();
  assert.equal(gd.steps, TRACE_STEPS);
  assert.equal(gd.traces.length, TRACE_SEEDS.length);
});

for (const seed of TRACE_SEEDS) {
  test(`파리티: 시드 ${seed >>> 0} — 1500스텝 전 구간이 wasm 과 동일`, () => {
    const gd = requireGolden();
    const want = gd.traces.find((t) => t.seed === seed);
    assert.ok(want, `시드 ${seed} 의 골든 트레이스가 없다`);
    const got = runTrace(new TsTarget(), seed, TRACE_STEPS);

    assert.equal(got.restarts, want!.restarts, '게임오버 재시작 횟수');
    for (let i = 0; i < TRACE_STEPS; i++) {
      if (got.bh[i] !== want!.bh[i] || got.sh[i] !== want!.sh[i]) {
        // 어긋난 첫 스텝의 직전 스냅샷을 붙여서 어디가 틀렸는지 바로 보이게 한다
        const snap = want!.snaps.filter((s) => s.i <= i).pop();
        assert.fail(
          `시드 ${seed >>> 0} 스텝 ${i} 에서 갈라짐\n` +
          `  보드 해시 got=${got.bh[i]} want=${want!.bh[i]}\n` +
          `  상태 해시 got=${got.sh[i]} want=${want!.sh[i]}\n` +
          `  직전 골든 스냅샷(스텝 ${snap?.i}): ${JSON.stringify(snap?.stats)}`,
        );
      }
    }
    for (const s of want!.snaps) {
      const mine = got.snaps.find((x) => x.i === s.i);
      assert.deepEqual(mine?.stats, s.stats, `스텝 ${s.i} 의 stats 전체`);
    }
  });
}

test('파리티: 배치 트레이스 1960경우 — 킥·T스핀·점수까지 동일', () => {
  const gd = requireGolden();
  const got = runPlacementTrace(new TsTarget());
  assert.equal(got.cases.length, gd.placement.length);
  for (let i = 0; i < got.cases.length; i++) {
    const mine = got.cases[i]!, want = gd.placement[i]!;
    assert.equal(mine.b, want.b);
    assert.equal(mine.p, want.p);
    assert.equal(mine.w, want.w);
    assert.deepEqual(
      mine.r, want.r,
      `판 ${mine.b} · 조각 ${mine.p} · 단어 ${mine.w} 의 결과가 다르다`,
    );
  }
  // 이 트레이스가 실제로 흥미로운 경우를 밟았는지 — 통과했는데 아무 일도 없었으면 무의미하다
  assert.ok(got.cases.some((c) => c.r[3]! > 0), 'T스핀이 한 번도 안 나왔다면 표본이 부실하다');
  assert.ok(got.cases.filter((c) => c.r[2]! > 0).length > 20, '줄 지우기 표본이 너무 적다');
});

test('파리티: 연쇄 트레이스 — 콤보·B2B·레벨업·상쇄까지 동일', () => {
  const gd = requireGolden();
  const got = runComboTrace(new TsTarget());
  assert.equal(got.steps.length, gd.combo.length);
  for (let i = 0; i < got.steps.length; i++) {
    const mine = got.steps[i]!, want = gd.combo[i]!;
    const label = `${COMBO_SCENARIOS[mine.s]!.name} 라운드 ${mine.i}`;
    assert.equal(mine.s, want.s);
    assert.equal(mine.i, want.i);
    assert.deepEqual(mine.r, want.r, `${label} 의 결과가 다르다`);
  }
});

test('연쇄 트레이스가 실제로 연쇄를 밟는지 (표본 건전성)', () => {
  const gd = requireGolden();
  const combos = gd.combo.map((c) => c.r[5]!);
  const levels = gd.combo.map((c) => c.r[7]!);
  const b2b = gd.combo.filter((c) => c.r[6] === 1).length;
  const tspins = gd.combo.filter((c) => c.r[4]! > 0).length;
  const risen = gd.combo.filter((c) => c.r[10]! > 0).length;
  assert.ok(Math.max(...combos) >= 5, `콤보가 5 이상 올라가야 한다 (최대 ${Math.max(...combos)})`);
  assert.ok(Math.max(...levels) >= 2, `레벨업을 밟아야 한다 (최대 ${Math.max(...levels)})`);
  assert.ok(b2b >= 10, `B2B 가 붙은 라운드가 충분해야 한다 (${b2b}회)`);
  assert.ok(tspins >= 5, `T스핀 연쇄를 밟아야 한다 (${tspins}회)`);
  assert.ok(risen > 0, '대기 가비지가 남는 라운드가 있어야 한다');
});

test('가비지 색 인덱스는 조각 색과 겹치지 않는다', () => {
  assert.ok(GARBAGE > 7);
});
