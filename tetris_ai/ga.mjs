// ga.mjs — 가중치 8개를 유전 알고리즘으로 찾는다.
//
// 우리가 최적화하려는 함수는 이렇게 생겼다:
//   f(w) = "가중치 w 로 AI가 400조각을 두면 몇 줄을 지우는가"
// 미분할 수 없고(조각 하나 놓는 순간 argmax 가 튄다), 노이즈가 있고(시드마다 다르다),
// 한 번 평가하는 데 40 ms 가 든다. 경사하강법이 손댈 수 없는 모양이다.
// 반면 GA 는 f 를 "넣으면 숫자가 나오는 검은 상자"로만 다룬다. 그래서 맞는다.
//
//   node ga.mjs                 기본 설정으로 학습 → weights.json, ga_log.json
//   node ga.mjs --pop 16 --gen 10
import { loadCore, setWeights, V } from './core.mjs';
import { writeFileSync } from 'node:fs';
import { mulberry32, gauss, DIM, normalize, randomGenome, tournament, crossover, mutate }
  from './ga_core.mjs';
export { mulberry32, gauss, DIM, normalize, randomGenome, tournament, crossover, mutate };

// ── 적합도 ───────────────────────────────────────────────────────────
// 같은 가중치라도 조각 순서에 따라 결과가 흔들린다. 그래서 시드 여러 개의 평균을 쓴다.
// 시드를 매 세대 바꾸면 "운 좋은 세대"가 살아남아 그래프가 요동친다 — 고정한다.
export function makeFitness(core, seeds, maxPieces, every = 0) {
  const cache = new Map();
  return function fitness(g) {
    const key = g.map(v => v.toFixed(5)).join(',');
    const hit = cache.get(key);
    if (hit) return hit;
    setWeights(core, g);
    let lines = 0, attack = 0, placed = 0;
    for (const s of seeds) {
      lines  += core.e.ai_play_hard(s >>> 0, maxPieces, every);
      attack += core.e.ai_play_attack();
      placed += core.e.ai_play_placed();
    }
    const n = seeds.length;
    const r = { lines: lines / n, attack: attack / n, placed: placed / n };
    cache.set(key, r);
    return r;
  };
}

// ── 진화 루프 ────────────────────────────────────────────────────────
// 한 세대에서 벌어지는 일은 네 줄로 요약된다.
//   1) 전원을 평가한다
//   2) 상위 elite 명은 그대로 다음 세대로 복사한다 (최고 기록이 사라지지 않게)
//   3) 나머지는 토너먼트로 부모 둘을 뽑아 교차 + 변이로 만든다
//   4) 반복
export async function evolve(opts = {}) {
  const {
    pop: POP = 32, gen: GEN = 30, elite = 2, k = 3,
    sigma = 0.2, mutP = 0.2, alpha = 0.5,
    seeds = [1, 2, 3], maxPieces = 400, rngSeed = 20260827,
    objective = 'attack', every = 0,
    core, onGen = null,
  } = opts;

  const c = core ?? await loadCore(1);
  const rnd = mulberry32(rngSeed);
  const fitness = makeFitness(c, seeds, maxPieces, every);

  let popArr = Array.from({ length: POP }, () => randomGenome(rnd));
  const log = [];
  let best = null, bestFit = -1;

  for (let g = 1; g <= GEN; g++) {
    const t0 = Date.now();
    const evals = popArr.map(fitness);
    const fits  = evals.map(x => x[objective]);      // 'attack' 또는 'lines'

    const order = fits.map((f, i) => [f, i]).sort((a, b) => b[0] - a[0]);
    const gBestI = order[0][1];
    if (fits[gBestI] > bestFit) { bestFit = fits[gBestI]; best = popArr[gBestI].slice(); }

    const mean = fits.reduce((s, x) => s + x, 0) / fits.length;
    const rec = {
      gen: g,
      best: +fits[gBestI].toFixed(1),
      mean: +mean.toFixed(1),
      worst: +order[order.length - 1][0].toFixed(1),
      lines: +evals[gBestI].lines.toFixed(1),
      attack: +evals[gBestI].attack.toFixed(1),
      placed: +evals[gBestI].placed.toFixed(0),
      ms: 0,
      weights: popArr[gBestI].map(v => +v.toFixed(4)),
    };

    // 다음 세대 만들기
    const next = order.slice(0, elite).map(([, i]) => popArr[i].slice());
    while (next.length < POP) {
      const a = tournament(popArr, fits, k, rnd);
      const b = tournament(popArr, fits, k, rnd);
      next.push(mutate(crossover(a, b, rnd, alpha), rnd, sigma, mutP));
    }
    popArr = next;

    rec.ms = Date.now() - t0;
    log.push(rec);
    if (onGen) await onGen(rec);
  }
  return { best, bestFit, log };
}

// ── CLI ──────────────────────────────────────────────────────────────
function argInt(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? parseInt(process.argv[i + 1], 10) : dflt;
}
const FEATNAME = ['줄수', '높이합', '구멍', '요철', '우물', '행전이', '열전이', '착지높이'];

if (import.meta.url === `file://${process.argv[1]}`) {
  const POP = argInt('pop', 32), GEN = argInt('gen', 50), MAXP = argInt('pieces', 400);
  const OBJ = process.argv.includes('--lines') ? 'lines' : 'attack';
  const core = await loadCore(1);
  console.log(`GA 시작 — 개체 ${POP}, 세대 ${GEN}, 조각 상한 ${MAXP}, 목표 ${OBJ}, 시드 [1,2,3]`);
  console.log('세대 | 최고    평균    최저   | 지운줄 | 놓은수 | 소요');
  console.log('-----+------------------------+--------+--------+------');

  const snapshots = {};
  const { best, bestFit, log } = await evolve({
    pop: POP, gen: GEN, maxPieces: MAXP, objective: OBJ, core,
    onGen: (r) => {
      if (r.gen === 1 || r.gen === 5 || r.gen === 15) snapshots[r.gen] = r.weights;
      if (r.gen === 1) snapshots.g1 = r.weights;
      console.log(`${String(r.gen).padStart(4)} | ${String(r.best).padStart(6)}  ` +
                  `${String(r.mean).padStart(6)}  ${String(r.worst).padStart(6)} | ` +
                  `${String(r.lines).padStart(6)} | ${String(r.placed).padStart(6)} | ` +
                  `${(r.ms / 1000).toFixed(1)}s`);
    },
  });

  console.log('\n최종 가중치');
  best.forEach((v, i) => console.log(`  ${FEATNAME[i].padEnd(6)} ${v >= 0 ? ' ' : ''}${v.toFixed(4)}`));
  console.log(`\n적합도(${OBJ === 'attack' ? '평균 보낸 줄' : '평균 지운 줄'}) ${bestFit.toFixed(1)}`);

  // 난이도 프리셋 = 학습 도중의 스냅숏. "덜 배운 AI" 가 곧 약한 상대다.
  const out = {
    best: best.map(v => +v.toFixed(6)),
    fitness: +bestFit.toFixed(1),
    objective: OBJ,
    gen: GEN, pop: POP, maxPieces: MAXP, seedsUsed: [1, 2, 3],
    features: ['F_LINES', 'F_AGG', 'F_HOLES', 'F_BUMP', 'F_WELLS', 'F_ROWT', 'F_COLT', 'F_LAND'],
    levels: {
      easy:   snapshots[1]  ?? log[0].weights,
      normal: snapshots[5]  ?? log[Math.min(4, log.length - 1)].weights,
      hard:   snapshots[15] ?? log[Math.min(14, log.length - 1)].weights,
      max:    best.map(v => +v.toFixed(6)),
    },
  };
  writeFileSync(new URL('./weights.json', import.meta.url), JSON.stringify(out, null, 2) + '\n');
  writeFileSync(new URL('./ga_log.json', import.meta.url), JSON.stringify(log, null, 1) + '\n');
  console.log('\nweights.json, ga_log.json 저장 완료');
}
