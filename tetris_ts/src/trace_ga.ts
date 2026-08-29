// trace_ga.ts — GA 층이 부 2 의 JS 구현(ga_core.mjs / ga.mjs)과 같은 수열을 내는지 재는 자.
//
// 코어·AI 는 wasm 이 정답지였지만 GA 는 원래부터 JS 다(부 2 에서 wasm 은 평가만 하고
// 진화 루프는 JS 가 돌렸다). 그래서 여기서는 **그 JS 파일들이 정답지**다.
//
// 순수 함수 하나가 난수를 한 번 더 소비하기만 해도 그 뒤의 모든 세대가 갈라진다.
// 그래서 (1) 순수 함수를 호출 순서까지 고정해 대조하고, (2) 진화 루프를 작게
// 한 판 돌려 세대별 로그를 통째로 대조한다.

/** GA 의 순수 함수 묶음. TS 판과 JS 판이 각각 이 모양으로 제공된다. */
export interface GaOps {
  mulberry32(seed: number): () => number;
  gauss(rnd: () => number): number;
  normalize(g: number[]): number[];
  randomGenome(rnd: () => number): number[];
  tournament(pop: number[][], fits: number[], k: number, rnd: () => number): number[];
  crossover(a: number[], b: number[], rnd: () => number, alpha: number): number[];
  mutate(g: number[], rnd: () => number, sigma: number, p: number): number[];
}

export interface GaOpsTrace {
  rnd: number[];
  gauss: number[];
  normalize: number[][];
  genomes: number[][];
  tournament: number[][];
  crossover: number[][];
  mutate: number[][];
}

/** 정규화가 손댈 만한 입력들 — 0벡터(길이 0 방어), 음수, 아주 큰 값, 아주 작은 값. */
const NORM_INPUTS: readonly number[][] = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 0, 0, 0],
  [-1, -2, -3, -4, -5, -6, -7, -8],
  [1e-8, 1e-8, 1e-8, 1e-8, 1e-8, 1e-8, 1e-8, 1e-8],
  [1e8, -1e8, 0, 0, 0, 0, 0, 0],
  [0.5, -0.25, 0.125, -0.0625, 0.03125, -0.015625, 0.0078125, -0.00390625],
];

/**
 * 순수 함수들을 정해진 순서로 두들긴다.
 *
 * 난수 스트림 하나를 처음부터 끝까지 공유하는 게 요점이다. 함수마다 새 난수를
 * 만들어 쓰면 "난수를 몇 번 소비하는가"의 차이를 못 잡는다 — 그런데 진화 루프가
 * 갈라지는 원인의 대부분이 바로 그것이다.
 */
export function runGaOpsTrace(ops: GaOps): GaOpsTrace {
  const out: GaOpsTrace = {
    rnd: [], gauss: [], normalize: [], genomes: [],
    tournament: [], crossover: [], mutate: [],
  };

  // 1) 난수기 자체
  const r0 = ops.mulberry32(20260827);
  for (let i = 0; i < 32; i++) out.rnd.push(r0());
  const r1 = ops.mulberry32(0); // 시드 0 경계
  for (let i = 0; i < 8; i++) out.rnd.push(r1());

  // 2) 정규분포
  const r2 = ops.mulberry32(12345);
  for (let i = 0; i < 32; i++) out.gauss.push(ops.gauss(r2));

  // 3) 정규화 (난수 없음)
  for (const g of NORM_INPUTS) out.normalize.push(ops.normalize(g.slice()));

  // 4) 이하는 난수 스트림 하나를 끝까지 공유한다
  const r = ops.mulberry32(0x5eed);
  const pop: number[][] = [];
  for (let i = 0; i < 12; i++) {
    const g = ops.randomGenome(r);
    pop.push(g);
    out.genomes.push(g);
  }
  const fits = pop.map((_, i) => (i * 37) % 11); // 동점이 섞이도록 일부러 겹치는 값

  for (let i = 0; i < 16; i++) out.tournament.push(ops.tournament(pop, fits, 3, r));
  for (let i = 0; i < 16; i++) {
    out.crossover.push(ops.crossover(pop[i % 12] as number[], pop[(i + 5) % 12] as number[], r, 0.5));
  }
  for (let i = 0; i < 16; i++) {
    out.mutate.push(ops.mutate(pop[i % 12] as number[], r, 0.2, 0.2));
  }
  return out;
}

/** 진화 루프 대조에 쓰는 설정. 작게 잡아야 정답지 생성이 몇 초에 끝난다. */
export const EVOLVE_CHECK = {
  pop: 12,
  gen: 6,
  maxPieces: 120,
  seeds: [1, 2] as readonly number[],
  rngSeed: 20260827,
  objective: 'attack' as const,
  every: 0,
};

/** 가비지가 새는 모드까지 한 번 더 — GA 가 실제로 쓰는 설정이다. */
export const EVOLVE_CHECK_HARD = { ...EVOLVE_CHECK, every: 10, rngSeed: 4242 };
