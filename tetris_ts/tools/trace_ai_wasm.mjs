// trace_ai_wasm.mjs — C++ wasm 의 AI 층(ai.cpp)에서 정답지를 뽑는다.
//
//   node tools/trace_ai_wasm.mjs        → test/golden/ai_traces.json
//
// 코어 정답지(trace_wasm.mjs)와 같은 규칙: 시나리오는 src/trace_ai.ts 에만 있고
// 이 도구는 wasm 어댑터만 제공한다. dist/ 가 먼저 빌드되어 있어야 한다.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { paintBoard } from '../dist/src/trace.js';
import {
  runPlanTrace, runPlayTrace, runEvalTrace, aiBoards, WEIGHT_SETS, AI_BOARD_COUNT,
} from '../dist/src/trace_ai.js';
import { ST, H, W } from '../dist/src/core.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const WASM = join(ROOT, '..', 'tetris_ai', 'tetris_ai.wasm');

const module = await WebAssembly.compile(readFileSync(WASM));

async function makeTarget() {
  const inst = await WebAssembly.instantiate(module, {});
  const e = inst.exports;
  const buf = e.memory.buffer;
  if (e.ai_feature_count() !== 8) throw new Error('특징 개수가 8이 아니다');
  const board = new Uint8Array(buf, e.ts_board(), H * W);
  const stats = new Int32Array(buf, e.ts_stats(), ST.COUNT);
  const weights = new Float32Array(buf, e.ai_weights_ptr(), 8);
  const feats = new Float32Array(buf, e.ai_features_ptr(), 8);
  return {
    init: (seed) => e.ts_init(seed >>> 0),
    paint: (rows) => paintBoard(board, rows),
    setPiece: (p) => e.ts_set_piece(p),
    setWeights: (w) => weights.set(w),
    plan: () => e.ai_plan(),
    apply: (packed) => e.ai_apply(packed),
    evalHere: () => e.ai_eval_here(),
    features: () => feats,
    play: (seed, maxPieces, every) => e.ai_play_hard(seed >>> 0, maxPieces, every),
    playAttack: () => e.ai_play_attack(),
    playPlaced: () => e.ai_play_placed(),
    board: () => board,
    stats: () => stats,
  };
}

const boards = aiBoards();

const evalCases = runEvalTrace(await makeTarget(), boards);
console.log(`평가 트레이스: ${evalCases.length}경우`);

const plan = runPlanTrace(await makeTarget(), boards);
const noMove = plan.cases.filter((c) => c.packed < 0).length;
const usedHold = plan.cases.filter((c) => c.packed >= 0 && (c.packed >> 8) & 1).length;
console.log(`탐색 트레이스: ${plan.cases.length}경우, 둘 수 없음 ${noMove}, 홀드 사용 ${usedHold}`);

const play = runPlayTrace(await makeTarget());
const best = play.cases.reduce((a, c) => (c.r[0] > a.r[0] ? c : a));
console.log(
  `실전 트레이스: ${play.cases.length}판, 최고 ${best.r[0]}줄 ` +
  `(가중치 ${best.wi} · 시드 ${best.seed} · every ${best.every}, 공격 ${best.r[1]}, 조각 ${best.r[2]})`,
);

const out = {
  v: 1,
  note: 'C++ wasm AI(ai.cpp)에서 뽑은 골든 트레이스. TS 의 ai.ts 가 이걸 그대로 재현해야 한다.',
  source: 'tetris_ai/tetris_ai.wasm',
  weightSets: WEIGHT_SETS.length,
  boards: boards.length,
  evalCases,
  plan: plan.cases,
  play: play.cases,
};
mkdirSync(join(ROOT, 'test', 'golden'), { recursive: true });
const path = join(ROOT, 'test', 'golden', 'ai_traces.json');
writeFileSync(path, JSON.stringify(out), 'utf8');
console.log(`\n기록: ${path} (${(JSON.stringify(out).length / 1024).toFixed(0)} KB)`);
