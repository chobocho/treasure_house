// trace_wasm.mjs — 부 1·2 에서 만든 C++ wasm 코어를 "정답지"로 삼아 골든 트레이스를 뽑는다.
//
//   node tools/trace_wasm.mjs           → test/golden/core_traces.json
//
// 이 도구는 TS 코어를 **전혀 부르지 않는다**. 시나리오 생성기(src/trace.ts)만 공유한다.
// 그래야 "두 구현이 같은 길을 걸었는데 도착지가 같은가"를 물을 수 있다.
//
// 주의: dist/ 가 먼저 빌드되어 있어야 한다 (`make build`). Makefile 이 순서를 강제한다.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  runTrace, TRACE_SEEDS, TRACE_STEPS, runPlacementTrace, runComboTrace, paintBoard,
} from '../dist/src/trace.js';
import { ST, H, W } from '../dist/src/core.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const WASM = join(ROOT, '..', 'tetris_ai', 'tetris_ai.wasm');

const module = await WebAssembly.compile(readFileSync(WASM));

// wasm 인스턴스 하나를 TraceTarget 모양으로 감싼다.
// 선형 메모리는 자라지 않으므로 뷰를 한 번만 만들어 재사용한다.
async function makeTarget() {
  const inst = await WebAssembly.instantiate(module, {});
  const e = inst.exports;
  const buf = e.memory.buffer;
  const dims = e.ts_dims(), rows = e.ts_rows();
  const w = dims >>> 16, h = rows >>> 16;
  if (w !== W || h !== H) throw new Error(`판 크기 불일치: wasm ${w}x${h}, TS ${W}x${H}`);
  const board = new Uint8Array(buf, e.ts_board(), h * w);
  const stats = new Int32Array(buf, e.ts_stats(), ST.COUNT);
  return {
    init: (seed) => e.ts_init(seed >>> 0),
    press: (act) => e.ts_press(act),
    release: (act) => e.ts_release(act),
    update: (dt) => e.ts_update(dt),
    queueGarbage: (n) => e.ts_queue_garbage(n),
    paint: (rows) => paintBoard(board, rows),
    setPiece: (p) => e.ts_set_piece(p),
    board: () => board,
    stats: () => stats,
  };
}

const traces = [];
for (const seed of TRACE_SEEDS) {
  const t = await makeTarget();          // 시드마다 새 인스턴스 — 상태 누수 차단
  const r = runTrace(t, seed, TRACE_STEPS);
  traces.push(r);
  const last = r.snaps[r.snaps.length - 1].stats;
  console.log(
    `seed ${seed >>> 0}: ${r.steps}스텝, 재시작 ${r.restarts}회, ` +
    `조각 ${last[ST.PIECES]}, 줄 ${last[ST.LINES]}, 점수 ${last[ST.SCORE]}`,
  );
}

// 배치 트레이스 — 킥 표와 T스핀 판정을 전수로 대조한다.
const placement = runPlacementTrace(await makeTarget());
const tspins = placement.cases.filter((c) => c.r[3] > 0).length;
const cleared = placement.cases.filter((c) => c.r[2] > 0).length;
console.log(`\n배치 트레이스: ${placement.cases.length}경우, 줄 지움 ${cleared}, T스핀 ${tspins}`);

// 연쇄 트레이스 — 콤보·B2B·레벨업·상쇄
const combo = runComboTrace(await makeTarget());
const maxCombo = Math.max(...combo.steps.map((c) => c.r[5]));
const maxLevel = Math.max(...combo.steps.map((c) => c.r[7]));
const b2bHits = combo.steps.filter((c) => c.r[6] === 1).length;
console.log(`연쇄 트레이스: ${combo.steps.length}라운드, 최대콤보 ${maxCombo}, 최대레벨 ${maxLevel}, B2B ${b2bHits}회`);

const out = {
  v: 1,
  note: 'C++ wasm 코어(tetris_ai.wasm)에서 뽑은 골든 트레이스. TS 코어가 이걸 그대로 재현해야 한다.',
  source: 'tetris_ai/tetris_ai.wasm',
  steps: TRACE_STEPS,
  traces,
  placement: placement.cases,
  combo: combo.steps,
};
mkdirSync(join(ROOT, 'test', 'golden'), { recursive: true });
const path = join(ROOT, 'test', 'golden', 'core_traces.json');
writeFileSync(path, JSON.stringify(out), 'utf8');
console.log(`\n기록: ${path} (${(JSON.stringify(out).length / 1024).toFixed(0)} KB)`);
