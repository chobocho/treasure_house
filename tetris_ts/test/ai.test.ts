// ai.test.ts — AI 층의 단위 테스트 + C++ wasm AI 파리티.
//
// 여기서 가장 무서운 실패 모드는 "거의 맞는 것"이다. float32 마지막 비트 하나가
// 달라 argmax 가 다른 후보를 고르면, 단위 테스트는 전부 통과하는데 400조각을
// 두고 나면 완전히 다른 판이 된다. 그래서 실전 판 56개를 통째로 대조한다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { Tetris, ST, STATE, W, H, SPAWN_X, GARBAGE } from '../src/core.js';
import { paintBoard } from '../src/trace.js';
import { Ai, F, features, scoreOf, DEFAULT_WEIGHTS, FEATURE_NAMES } from '../src/ai.js';
import {
  runPlanTrace, runPlayTrace, runEvalTrace, aiBoards, WEIGHT_SETS,
  type AiTarget, type PlanCase, type PlayCase, type EvalCase,
} from '../src/trace_ai.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const GOLDEN = join(HERE, '..', '..', 'test', 'golden', 'ai_traces.json');

/** Tetris + Ai 한 쌍을 AiTarget 으로 감싼다. */
class TsAiTarget implements AiTarget {
  readonly g = new Tetris(1);
  readonly ai = new Ai(this.g);
  init(seed: number): void { this.g.init(seed); }
  paint(rows: readonly string[]): void { paintBoard(this.g.board, rows); }
  setPiece(piece: number): void { this.g.setPiece(piece); }
  setWeights(w: readonly number[]): void { this.ai.setWeights(w); }
  plan(): number { return this.ai.plan(); }
  apply(packed: number): void { this.ai.apply(packed); }
  evalHere(): number { return this.ai.evalHere(); }
  features(): Float32Array { return this.ai.lastFeat; }
  play(seed: number, maxPieces: number, every: number): number {
    return this.ai.play(seed, maxPieces, every);
  }
  playAttack(): number { return this.ai.playAttack; }
  playPlaced(): number { return this.ai.playPlaced; }
  board(): Uint8Array { return this.g.board; }
  stats(): Int32Array { return this.g.stats; }
}

/** 특징 벡터를 손으로 읽기 쉬운 객체로 — 실패 메시지에 쓴다. */
function featObj(f: readonly number[] | Float32Array): Record<string, number> {
  const o: Record<string, number> = {};
  FEATURE_NAMES.forEach((n, i) => { o[n] = f[i] as number; });
  return o;
}

// ── 1. 특징 함수 ──────────────────────────────────────────────────────
test('빈 판의 특징은 전부 0 (열 전이만 0)', () => {
  const b = new Uint8Array(H * W);
  const f = new Float32Array(F.COUNT);
  features(b, 0, 0, f);
  assert.equal(f[F.AGG], 0);
  assert.equal(f[F.HOLES], 0);
  assert.equal(f[F.BUMP], 0);
  assert.equal(f[F.WELLS], 0);
  // 빈 줄은 왼쪽 벽→빈칸 전이 1 + 오른쪽 벽 전이 1 = 2, 24줄이면 48
  assert.equal(f[F.ROWT], 2 * H);
  // 빈 열은 천장부터 바닥까지 전부 비어 있으니 바닥에서 1번만 전이 → 10
  assert.equal(f[F.COLT], W);
});

test('구멍 세기: 블록 아래의 빈칸만 구멍이다', () => {
  const g = new Tetris(1);
  paintBoard(g.board, [
    '#.........',
    '..........',
    '#.........',
  ]);
  const f = new Float32Array(F.COUNT);
  features(g.board, 0, 0, f);
  // 0열: 맨 위 블록 아래로 빈칸 1개(가운데 줄) → 구멍 1
  assert.equal(f[F.HOLES], 1, JSON.stringify(featObj(f)));
  assert.equal(f[F.AGG], 3, '0열 높이 3');
});

test('울퉁불퉁함(BUMP)은 이웃 열 높이차의 합', () => {
  const g = new Tetris(1);
  paintBoard(g.board, ['#.#.#.#.#.']);
  const f = new Float32Array(F.COUNT);
  features(g.board, 0, 0, f);
  // 높이가 1,0,1,0,... 이므로 이웃 차이 1 이 9번
  assert.equal(f[F.BUMP], 9, JSON.stringify(featObj(f)));
});

test('우물(WELLS) 비용은 깊이 d 에 대해 1+2+…+d', () => {
  const g = new Tetris(1);
  // 가운데 한 칸만 3 깊이로 파인 판
  paintBoard(g.board, ['###.######', '###.######', '###.######']);
  const f = new Float32Array(F.COUNT);
  features(g.board, 0, 0, f);
  assert.equal(f[F.WELLS], 6, `깊이 3 → 1+2+3 = 6 (${JSON.stringify(featObj(f))})`);
});

test('score 는 f32 로 접힌다 — 이걸 빼면 argmax 가 갈린다', () => {
  const w = new Float32Array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]);
  const f = new Float32Array([1, 2, 3, 4, 5, 6, 7, 8]);
  const got = scoreOf(w, f);
  // 같은 계산을 float64 로 하면 값이 다르다 — 다르지 않으면 fround 가 죽은 코드다
  let f64 = 0;
  for (let i = 0; i < 8; i++) f64 += (w[i] as number) * (f[i] as number);
  assert.notEqual(got, f64, 'f32 접기가 실제로 값을 바꿔야 한다');
  assert.equal(got, Math.fround(got), '결과는 f32 로 표현 가능한 수여야 한다');
});

// ── 2. 탐색 ───────────────────────────────────────────────────────────
test('packed 인코딩: (hold<<8) | (rot<<4) | (x+3)', () => {
  const g = new Tetris(1);
  const ai = new Ai(g);
  const p = ai.plan();
  assert.ok(p >= 0, '빈 판에서는 반드시 둘 곳이 있다');
  const x = (p & 15) - 3;
  const rot = (p >> 4) & 3;
  const hold = (p >> 8) & 1;
  assert.ok(x >= -3 && x < W, `x 범위 ${x}`);
  assert.ok(rot >= 0 && rot < 4);
  assert.ok(hold === 0 || hold === 1);
});

test('게임오버 판에서는 -1', () => {
  const g = new Tetris(1);
  const ai = new Ai(g);
  g.stats[ST.STATE] = STATE.OVER;
  assert.equal(ai.plan(), -1);
});

test('구멍을 싫어하도록 가중치를 주면 구멍을 안 만든다', () => {
  // 구멍 하나만 극단적으로 벌점 → I 를 눕혀 평평하게 놓아야 한다
  const g = new Tetris(1);
  const ai = new Ai(g, [0, 0, -1000, 0, 0, 0, 0, 0]);
  g.setPiece(0); // I
  ai.step();
  const f = new Float32Array(F.COUNT);
  features(g.board, 0, 0, f);
  assert.equal(f[F.HOLES], 0, `구멍을 만들면 안 된다 (${JSON.stringify(featObj(f))})`);
});

test('AI 는 진행 중인 판을 탐색으로 더럽히지 않는다', () => {
  const g = new Tetris(1);
  const ai = new Ai(g);
  const before = Uint8Array.from(g.board);
  const st = Int32Array.from(g.stats);
  ai.plan(); // 탐색만 하고 두지는 않는다
  assert.deepEqual(Array.from(g.board), Array.from(before), '보드가 그대로여야 한다');
  assert.deepEqual(Array.from(g.stats), Array.from(st), 'stats 도 그대로여야 한다');
});

test('apply 는 규칙을 우회하지 않는다 — 하드드롭 점수가 붙는다', () => {
  const g = new Tetris(1);
  const ai = new Ai(g);
  const before = g.stats[ST.SCORE] as number;
  const p = ai.plan();
  ai.apply(p);
  assert.ok((g.stats[ST.SCORE] as number) > before, '낙하 점수가 들어와야 한다');
  // 홀드를 쓰면 스폰이 한 번 더 일어난다(홀드 교체 + 락 후 스폰) — 규칙대로 do_hold 를
  // 거쳤다는 증거이므로 그 경우까지 세어 준다.
  const usedHold = (p >> 8) & 1;
  assert.equal(g.stats[ST.PIECES], 2 + usedHold, `조각 수 (홀드 사용 ${usedHold})`);
});

test('도달할 수 없는 자리는 후보에서 빠진다', () => {
  // 오른쪽 x=6..9 가 스폰 높이까지 막힌 판. 스폰 자리(x=4,5)는 비워 둬야 한다 —
  // 스폰까지 막으면 setPiece 가 곧장 게임오버로 만들어 이 테스트가 무의미해진다.
  const g = new Tetris(1);
  const ai = new Ai(g, [0, 0, 0, 0, 0, 0, 0, 1000]); // 높이 보상 → 최대한 높이 두려 함
  paintBoard(g.board, Array.from({ length: 20 }, () => '......####'));
  g.setPiece(3); // O — 스폰 시 x=4,5 를 차지한다
  assert.equal(g.stats[ST.STATE], STATE.PLAY, '스폰은 막히지 않아야 한다');
  const p = ai.plan();
  assert.ok(p >= 0, '왼쪽에는 둘 곳이 있다');
  const x = (p & 15) - 3;
  // 벽 위(높은 착지)가 훨씬 매력적이지만 스폰 줄을 따라 미끄러져 갈 수 없으므로 포기해야 한다
  assert.ok(x <= SPAWN_X, `막힌 오른쪽으로는 갈 수 없다 (고른 x=${x})`);
});

// ── 3. 한 판 두기 ─────────────────────────────────────────────────────
test('학습된 가중치로 400조각을 두면 100줄 이상 지운다', () => {
  const g = new Tetris(1);
  const ai = new Ai(g, DEFAULT_WEIGHTS);
  const lines = ai.play(1, 400, 0);
  assert.ok(lines >= 100, `${lines}줄 — 학습된 AI 라면 이 정도는 나와야 한다`);
  assert.equal(ai.playPlaced, 400, '400조각을 다 놓기 전에 죽으면 안 된다');
});

test('every > 0 이면 가비지가 새서 더 어렵다', () => {
  const easy = new Ai(new Tetris(1), DEFAULT_WEIGHTS);
  const hard = new Ai(new Tetris(1), DEFAULT_WEIGHTS);
  easy.play(3, 400, 0);
  hard.play(3, 400, 8);
  assert.ok(
    (hard.game.stats[ST.GARBAGE_RECV] as number) > 0,
    '가비지가 실제로 올라와야 한다',
  );
  assert.equal(easy.game.stats[ST.GARBAGE_RECV], 0);
});

test('나쁜 가중치는 빨리 죽는다 (적합도가 실제로 구별된다)', () => {
  const good = new Ai(new Tetris(1), DEFAULT_WEIGHTS);
  const bad = new Ai(new Tetris(1), [1, 1, 1, 1, 1, 1, 1, 1]);
  good.play(1, 400, 0);
  bad.play(1, 400, 0);
  assert.ok(
    bad.playPlaced < good.playPlaced,
    `나쁜 가중치 ${bad.playPlaced}조각 vs 좋은 가중치 ${good.playPlaced}조각`,
  );
});

// ── 4. C++ wasm AI 파리티 ─────────────────────────────────────────────
interface AiGolden {
  v: number;
  boards: number;
  weightSets: number;
  evalCases: EvalCase[];
  plan: PlanCase[];
  play: PlayCase[];
}

const golden: AiGolden | null = existsSync(GOLDEN)
  ? (JSON.parse(readFileSync(GOLDEN, 'utf8')) as AiGolden)
  : null;

function requireGolden(): AiGolden {
  if (!golden) throw new Error(`${GOLDEN} 이 없다 — 먼저 \`make golden\` 을 돌려라`);
  return golden;
}

test('AI 골든 파일이 있어야 한다 (make golden)', () => {
  const gd = requireGolden();
  assert.equal(gd.weightSets, WEIGHT_SETS.length);
  assert.equal(gd.boards, aiBoards().length);
});

test('파리티: 평가 트레이스 — 특징 8개와 f32 점수가 동일', () => {
  const gd = requireGolden();
  const got = runEvalTrace(new TsAiTarget(), aiBoards());
  assert.equal(got.length, gd.evalCases.length);
  for (let i = 0; i < got.length; i++) {
    const mine = got[i]!, want = gd.evalCases[i]!;
    assert.deepEqual(
      mine.feat, want.feat,
      `판 ${mine.b} 의 특징이 다르다\n  got  ${JSON.stringify(featObj(mine.feat))}\n  want ${JSON.stringify(featObj(want.feat))}`,
    );
    assert.equal(mine.score, want.score, `판 ${mine.b} · 가중치 ${mine.wi} 의 점수`);
  }
});

test('파리티: 탐색 트레이스 — 고른 수(packed)까지 동일', () => {
  const gd = requireGolden();
  const got = runPlanTrace(new TsAiTarget(), aiBoards());
  assert.equal(got.cases.length, gd.plan.length);
  for (let i = 0; i < got.cases.length; i++) {
    const mine = got.cases[i]!, want = gd.plan[i]!;
    const label = `판 ${mine.b} · 조각 ${mine.p} · 가중치 ${mine.wi}`;
    assert.equal(
      mine.packed, want.packed,
      `${label} 에서 다른 수를 골랐다 (got ${mine.packed}, want ${want.packed})`,
    );
    assert.deepEqual(mine.feat, want.feat, `${label} 의 특징 벡터`);
    assert.deepEqual(mine.after, want.after, `${label} 을 둔 뒤의 상태`);
  }
  // 표본 건전성: -1 경로와 홀드 경로를 실제로 밟았는가
  assert.ok(got.cases.some((c) => c.packed < 0), '둘 수 없는 판을 한 번은 밟아야 한다');
  assert.ok(got.cases.some((c) => c.packed >= 0 && ((c.packed >> 8) & 1) === 1), '홀드 경로');
});

test('파리티: 실전 트레이스 — 400조각 56판의 누적 결과가 동일', () => {
  const gd = requireGolden();
  const got = runPlayTrace(new TsAiTarget());
  assert.equal(got.cases.length, gd.play.length);
  for (let i = 0; i < got.cases.length; i++) {
    const mine = got.cases[i]!, want = gd.play[i]!;
    assert.deepEqual(
      mine.r, want.r,
      `가중치 ${mine.wi} · 시드 ${mine.seed} · every ${mine.every} 의 결과가 다르다\n` +
      `  [줄, 공격, 조각, 점수, 레벨, 상태, 해시]\n  got  ${JSON.stringify(mine.r)}\n  want ${JSON.stringify(want.r)}`,
    );
  }
});

test('가비지 칸도 특징 계산에서 "찬 칸"으로 센다', () => {
  const g = new Tetris(1);
  g.garbage(3, 4);
  const f = new Float32Array(F.COUNT);
  features(g.board, 0, 0, f);
  assert.equal(g.board[(H - 1) * W] , GARBAGE);
  assert.equal(f[F.AGG], 3 * (W - 1), '구멍 난 열 하나를 뺀 9열이 높이 3');
  assert.equal(f[F.HOLES], 0, '구멍 열은 위가 뚫려 있으니 구멍이 아니다');
});
