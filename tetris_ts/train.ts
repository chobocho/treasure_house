// train.ts — GA 트레이너. 실제로 학습을 돌려 weights.json 과 ga_log.json 을 남긴다.
//
//   node dist/train.js                    기본값(개체 32, 세대 50, 조각 400)
//   node dist/train.js --pop 16 --gen 10
//   node dist/train.js --lines            목표를 "지운 줄"로 (기본은 "보낸 줄")
//
// 덱의 학습 곡선은 **여기서 나온 로그**를 그린다. 지어낸 숫자를 쓰지 않는다.
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { Tetris } from './src/core.js';
import { Ai, FEATURE_NAMES } from './src/ai.js';
import { evolve, type GenRecord } from './src/ga.js';

const HERE = dirname(fileURLToPath(import.meta.url));
// dist/train.js 에서 실행되므로 한 단계 위가 프로젝트 루트다.
const ROOT = join(HERE, '..');

function argInt(name: string, dflt: number): number {
  const i = process.argv.indexOf('--' + name);
  if (i < 0) return dflt;
  const v = parseInt(process.argv[i + 1] as string, 10);
  return Number.isFinite(v) ? v : dflt;
}

const FEATNAME = ['줄수', '높이합', '구멍', '요철', '우물', '행전이', '열전이', '착지높이'];

const POP = argInt('pop', 32);
const GEN = argInt('gen', 50);
const MAXP = argInt('pieces', 400);
const EVERY = argInt('every', 0);
const OBJ: 'attack' | 'lines' = process.argv.includes('--lines') ? 'lines' : 'attack';
const SEEDS = [1, 2, 3];

console.log(
  `GA 시작 — 개체 ${POP}, 세대 ${GEN}, 조각 상한 ${MAXP}, ` +
  `목표 ${OBJ}, 시드 [${SEEDS}]${EVERY > 0 ? `, 가비지 1/${EVERY}조각` : ''}`,
);
console.log('세대 | 최고    평균    최저   | 지운줄 | 놓은수 | 소요');
console.log('-----+------------------------+--------+--------+------');

// 난이도 프리셋으로 쓸 중간 스냅숏. "덜 배운 AI" 가 곧 약한 상대다.
const snapshots = new Map<number, number[]>();

const { best, bestFit, log } = evolve({
  pop: POP, gen: GEN, maxPieces: MAXP, objective: OBJ, every: EVERY, seeds: SEEDS,
  ai: new Ai(new Tetris(1)),
  onGen: (r: GenRecord) => {
    if (r.gen === 1 || r.gen === 5 || r.gen === 15) snapshots.set(r.gen, r.weights);
    console.log(
      `${String(r.gen).padStart(4)} | ${String(r.best).padStart(6)}  ` +
      `${String(r.mean).padStart(6)}  ${String(r.worst).padStart(6)} | ` +
      `${String(r.lines).padStart(6)} | ${String(r.placed).padStart(6)} | ` +
      `${(r.ms / 1000).toFixed(1)}s`,
    );
  },
});

console.log('\n최종 가중치');
best.forEach((v, i) => {
  console.log(`  ${(FEATNAME[i] as string).padEnd(6)} ${v >= 0 ? ' ' : ''}${v.toFixed(4)}`);
});
console.log(`\n적합도(${OBJ === 'attack' ? '평균 보낸 줄' : '평균 지운 줄'}) ${bestFit.toFixed(1)}`);

const at = (g: number, fallback: number): number[] =>
  snapshots.get(g) ?? ((log[Math.min(fallback, log.length - 1)] as GenRecord).weights);

const out = {
  best: best.map((v) => +v.toFixed(6)),
  fitness: +bestFit.toFixed(1),
  objective: OBJ,
  gen: GEN, pop: POP, maxPieces: MAXP, seedsUsed: SEEDS,
  features: FEATURE_NAMES,
  levels: {
    easy: at(1, 0),
    normal: at(5, 4),
    hard: at(15, 14),
    max: best.map((v) => +v.toFixed(6)),
  },
};
writeFileSync(join(ROOT, 'weights.json'), JSON.stringify(out, null, 2) + '\n', 'utf8');
writeFileSync(join(ROOT, 'ga_log.json'), JSON.stringify(log, null, 1) + '\n', 'utf8');
console.log('\nweights.json, ga_log.json 저장 완료');
