// trace_ai.ts — AI 층(ai.ts)이 C++ ai.cpp/wasm 과 같은 수를 고르는지 재는 자.
//
// 코어 파리티(trace.ts)와 같은 구조다: 시나리오와 실행 루프를 여기 한 번만 쓰고,
// wasm 과 TS 는 AiTarget 어댑터만 제공한다.
//
// AI 파리티는 코어 파리티보다 까다롭다. 평가 점수가 float32 라, 마지막 비트 하나만
// 달라도 argmax 가 다른 후보를 고르고 그때부터 판이 통째로 갈라지기 때문이다.
// 그래서 "고른 수(packed)"를 보드마다 직접 대조하고, 그다음에 400조각짜리 실전 판을
// 통째로 돌려 누적 결과까지 맞춰 본다.

import { W, ST, boardHash } from './core.js';
import { scriptRng } from './trace.js';

/** AI 를 붙인 코어 하나를 조작하는 인터페이스. */
export interface AiTarget {
  init(seed: number): void;
  paint(rows: readonly string[]): void;
  setPiece(piece: number): void;
  setWeights(w: readonly number[]): void;
  /** 1수 탐색 결과 (packed). -1 이면 둘 수 없음. */
  plan(): number;
  apply(packed: number): void;
  /** 지금 판을 그대로 평가한 점수 (f32) */
  evalHere(): number;
  /** 마지막으로 계산된 특징 벡터 8개 */
  features(): Float32Array;
  /** 한 판을 끝까지 둔다. 반환은 지운 줄 수. */
  play(seed: number, maxPieces: number, every: number): number;
  playAttack(): number;
  playPlaced(): number;
  board(): Uint8Array;
  stats(): Int32Array;
}

/**
 * 대조에 쓰는 가중치 묶음.
 *
 * 앞의 넷은 부 2 의 GA 가 실제로 뽑아 낸 난이도별 가중치다(tetris_ai/weights.json).
 * 뒤의 셋은 손으로 만든 극단값 — 전부 0, 전부 양수, 부호가 뒤집힌 것.
 * 극단값이 중요하다: 부호가 뒤집히면 AI 가 일부러 판을 높이 쌓아서
 * "블록아웃 직전"과 "둘 수 있는 수가 없음(-1)" 경로를 밟는다.
 */
export const WEIGHT_SETS: readonly (readonly number[])[] = [
  [0.07328, 0.064795, -0.477997, 0.210324, -0.008971, -0.391833, -0.504655, -0.556259], // max
  [-0.3458, -0.1764, -0.7118, 0.2672, -0.3872, -0.1953, -0.2603, -0.1243], // normal
  [-0.0367, -0.5056, 0.4788, -0.0219, -0.4999, -0.4376, -0.195, -0.184], // easy
  [-0.031, 0.0583, -0.6088, 0.2292, -0.1135, -0.378, -0.3072, -0.5678], // hard
  [0, 0, 0, 0, 0, 0, 0, 0], // 전부 0 — 첫 후보가 그대로 최선이 된다(동점 처리 확인)
  [1, 1, 1, 1, 1, 1, 1, 1], // 전부 양수 — 최악의 수를 고른다
  [0.5, -0.25, 0.125, -0.0625, 0.03125, -0.015625, 0.0078125, -0.00390625], // 2의 거듭제곱
];

/**
 * 대조용 무작위 판 생성.
 *
 * 열마다 높이를 뽑고, 그 아래를 7칸에 1칸꼴로 비워 구멍을 낸다.
 * 구멍이 있어야 F_HOLES · F_COLT · F_WELLS 가 0 이 아닌 값을 갖는다 —
 * 평평한 판만 쓰면 특징 8개 중 절반이 늘 0 이라 대조가 헐거워진다.
 * 높이 상한은 14 로 잡았다. 더 높이면 스폰이 막혀 대부분의 판이 -1 로 끝난다.
 */
export function randomBoards(count: number, seed = 0x7f4a7c15): string[][] {
  const r = scriptRng(seed);
  const out: string[][] = [];
  for (let i = 0; i < count; i++) {
    const h = new Array<number>(W);
    for (let x = 0; x < W; x++) h[x] = r() % 15;
    const rows: string[] = [];
    for (let y = 0; y < 20; y++) {
      let s = '';
      const depth = 20 - y; // 바닥에서 센 높이 (바닥줄 = 1)
      for (let x = 0; x < W; x++) {
        const filled = depth <= (h[x] as number) && r() % 7 !== 0;
        s += filled ? '#' : '.';
      }
      rows.push(s);
    }
    out.push(rows);
  }
  return out;
}

export interface PlanCase {
  /** 판 · 조각 · 가중치 인덱스 */
  b: number;
  p: number;
  wi: number;
  /** AI 가 고른 수 (packed) */
  packed: number;
  /** 고른 수의 특징 벡터 8개 */
  feat: number[];
  /** 그 수를 둔 뒤의 보드 해시와 주요 stats */
  after: number[];
}

export interface PlanResult {
  cases: PlanCase[];
}

/** 판을 심고 조각을 지정한 뒤 "AI 가 무엇을 고르는가"를 전수로 대조한다. */
export function runPlanTrace(t: AiTarget, boards: string[][], seed = 0x4d2): PlanResult {
  const cases: PlanCase[] = [];
  for (let b = 0; b < boards.length; b++) {
    for (let p = 0; p < 7; p++) {
      for (let wi = 0; wi < WEIGHT_SETS.length; wi++) {
        t.init(seed);
        t.setWeights(WEIGHT_SETS[wi] as readonly number[]);
        t.paint(boards[b] as string[]);
        t.setPiece(p);
        const packed = t.plan();
        const feat = Array.from(t.features());
        t.apply(packed);
        const s = t.stats();
        cases.push({
          b, p, wi, packed, feat,
          after: [
            boardHash(t.board()),
            s[ST.SCORE] as number, s[ST.LINES] as number,
            s[ST.STATE] as number, s[ST.ATTACK] as number,
          ],
        });
      }
    }
  }
  return { cases };
}

export interface PlayCase {
  wi: number;
  seed: number;
  maxPieces: number;
  every: number;
  /** [지운줄, 공격, 놓은조각, 점수, 레벨, 상태, 보드해시] */
  r: number[];
}

export interface PlayResult {
  cases: PlayCase[];
}

export const PLAY_SEEDS: readonly number[] = [1, 2, 3, 777];

/**
 * 실전 판 대조 — 400조각을 끝까지 둔 뒤의 누적 결과를 맞춰 본다.
 *
 * every > 0 은 "비가 새는 배" 모드다. GA 의 적합도 함수가 실제로 쓰는 설정이라
 * 여기서 맞춰 두지 않으면 3부(학습)에서 두 구현의 적합도가 갈린다.
 */
export function runPlayTrace(t: AiTarget, maxPieces = 400): PlayResult {
  const cases: PlayCase[] = [];
  for (let wi = 0; wi < WEIGHT_SETS.length; wi++) {
    t.setWeights(WEIGHT_SETS[wi] as readonly number[]);
    for (const seed of PLAY_SEEDS) {
      for (const every of [0, 12]) {
        const lines = t.play(seed, maxPieces, every);
        const s = t.stats();
        cases.push({
          wi, seed, maxPieces, every,
          r: [
            lines, t.playAttack(), t.playPlaced(),
            s[ST.SCORE] as number, s[ST.LEVEL] as number, s[ST.STATE] as number,
            boardHash(t.board()),
          ],
        });
      }
    }
  }
  return { cases };
}

/** 특징 함수만 따로 대조 — 판만 심고 ai_eval_here 를 부른다.
 *  탐색을 거치지 않으므로, 갈라졌을 때 "특징이 틀렸나 탐색이 틀렸나"를 가른다. */
export interface EvalCase {
  b: number;
  wi: number;
  score: number;
  feat: number[];
}

export function runEvalTrace(t: AiTarget, boards: string[][], seed = 0x4d2): EvalCase[] {
  const out: EvalCase[] = [];
  for (let b = 0; b < boards.length; b++) {
    for (let wi = 0; wi < WEIGHT_SETS.length; wi++) {
      t.init(seed);
      t.setWeights(WEIGHT_SETS[wi] as readonly number[]);
      t.paint(boards[b] as string[]);
      out.push({ b, wi, score: t.evalHere(), feat: Array.from(t.features()) });
    }
  }
  return out;
}

/** 무작위 판 개수 — 도구와 테스트가 같은 수를 써야 하므로 여기서 고정한다. */
export const AI_BOARD_COUNT = 24;

const rep = (row: string, n: number): string[] => Array.from({ length: n }, () => row);

/**
 * 무작위 판이 절대 만들어 주지 않는 경계 판들.
 *
 * 특히 "스폰이 막힌 판"이 중요하다. 무작위 판 24개에서는 plan() 이 -1 을 반환하는
 * 경우가 한 번도 안 나왔다. 아무도 안 밟는 분기는 검증된 적이 없는 분기다.
 */
export const AI_EXTRA_BOARDS: readonly string[][] = [
  [], // 빈 판 — 모든 후보가 유효, F_HOLES 등이 0
  rep('#########.', 20), // 스폰까지 꽉 참 → setPiece 가 곧장 게임오버, plan() = -1
  rep('#########.', 16), // 거의 다 참 — 후보가 몇 개 안 남는다
  ['..........', '..........', ...rep('.........#', 18)], // 오른쪽 벽만 높은 판
  rep('.....#####', 19), // 절반만 높은 판 — 도달 불가 자리가 많이 생긴다
];

/** 대조에 쓰는 판 전체 = 무작위 + 경계. */
export function aiBoards(): string[][] {
  return [...randomBoards(AI_BOARD_COUNT), ...AI_EXTRA_BOARDS.map((b) => [...b])];
}
