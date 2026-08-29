// trace_ga_js.mjs — 부 2 의 JS GA(ga_core.mjs / ga.mjs)에서 정답지를 뽑는다.
//
//   node tools/trace_ga_js.mjs          → test/golden/ga_traces.json
//
// GA 는 부 2 에서도 JS 였다(wasm 은 평가만 했다). 그러니 정답지는 그 JS 파일이다.
// 시나리오는 src/trace_ga.ts 에만 있고 이 도구는 어댑터만 제공한다.
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { runGaOpsTrace, EVOLVE_CHECK, EVOLVE_CHECK_HARD } from '../dist/src/trace_ga.js';
import {
  mulberry32, gauss, normalize, randomGenome, tournament, crossover, mutate,
} from '../../tetris_ai/ga_core.mjs';
import { evolve } from '../../tetris_ai/ga.mjs';
import { loadCore } from '../../tetris_ai/core.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const ops = runGaOpsTrace({
  mulberry32, gauss, normalize, randomGenome, tournament, crossover, mutate,
});
console.log(
  `순수 함수 트레이스: 난수 ${ops.rnd.length}, 정규분포 ${ops.gauss.length}, ` +
  `유전자 ${ops.genomes.length}, 토너먼트 ${ops.tournament.length}, ` +
  `교차 ${ops.crossover.length}, 변이 ${ops.mutate.length}`,
);

// 진화 루프 — 부 2 의 evolve 를 wasm 코어 위에서 그대로 돌린다.
async function runEvolve(cfg) {
  const core = await loadCore(1);
  const { best, bestFit, log } = await evolve({ ...cfg, core });
  // ms 는 기계마다 다르다 — 대조에서 빼려고 여기서 지운다.
  return { best, bestFit, log: log.map(({ ms, ...rest }) => rest) };
}

const easy = await runEvolve(EVOLVE_CHECK);
const hard = await runEvolve(EVOLVE_CHECK_HARD);
console.log(
  `진화 루프: 기본 ${easy.log.length}세대 최고 ${easy.bestFit.toFixed(1)}, ` +
  `가비지 모드 ${hard.log.length}세대 최고 ${hard.bestFit.toFixed(1)}`,
);

const out = {
  v: 1,
  note: '부 2 의 JS GA(ga_core.mjs / ga.mjs)에서 뽑은 골든 트레이스. TS 의 ga.ts 가 이걸 그대로 재현해야 한다.',
  source: 'tetris_ai/ga_core.mjs, tetris_ai/ga.mjs',
  ops,
  evolve: { easy, hard },
};
mkdirSync(join(ROOT, 'test', 'golden'), { recursive: true });
const path = join(ROOT, 'test', 'golden', 'ga_traces.json');
writeFileSync(path, JSON.stringify(out), 'utf8');
console.log(`\n기록: ${path} (${(JSON.stringify(out).length / 1024).toFixed(0)} KB)`);
