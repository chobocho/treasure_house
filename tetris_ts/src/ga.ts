// ga.ts — 유전 알고리즘. 난수·유전자·선택·교차·변이, 그리고 진화 루프.
//
// 우리가 최적화하려는 함수는 이렇게 생겼다:
//   f(w) = "가중치 w 로 AI가 400조각을 두면 상대에게 몇 줄을 보내는가"
// 미분할 수 없고(조각 하나 놓는 순간 argmax 가 튄다), 노이즈가 있고(시드마다 다르다),
// 한 번 평가하는 데 수십 ms 가 든다. 경사하강법이 손댈 수 없는 모양이다.
// 반면 GA 는 f 를 "넣으면 숫자가 나오는 검은 상자"로만 다룬다. 그래서 맞는다.
//
// 이 파일은 파일 시스템도 DOM 도 건드리지 않는다. 그래서 Node 트레이너(train.ts)와
// 브라우저 라이브 학습이 이 파일 하나를 그대로 나눠 쓴다.

import { Tetris } from './core.js';
import { Ai, F } from './ai.js';

/** 유전자 = 실수 8개 (특징 가중치). */
export type Genome = number[];
export const DIM = F.COUNT;

// ── 결정론적 난수 ────────────────────────────────────────────────────
/** mulberry32. Math.random() 을 쓰면 "덱에 실린 로그"를 재현할 수 없다 — 씨앗을 고정한다. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function (): number {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 박스-뮐러: 균등난수 두 개 → 표준정규분포 하나. */
export function gauss(rnd: () => number): number {
  const u = Math.max(rnd(), 1e-12), v = rnd();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ── 유전자 ───────────────────────────────────────────────────────────
/** 길이를 1로 고정한다.
 *  w 와 2w 는 argmax 가 완전히 같다 — 크기는 정보가 아니라 잡음이다.
 *  정규화하지 않으면 개체들이 "방향은 같은데 길이만 다른" 복제로 채워진다. */
export function normalize(g: readonly number[]): Genome {
  let n = 0;
  for (const v of g) n += v * v;
  n = Math.sqrt(n) || 1;
  return g.map((v) => v / n);
}

export function randomGenome(rnd: () => number): Genome {
  return normalize(Array.from({ length: DIM }, () => gauss(rnd)));
}

// ── 선택·교차·변이 ───────────────────────────────────────────────────
/** 토너먼트 선택: 무작위 k 명을 뽑아 그중 1등을 부모로 쓴다.
 *  순위 전체를 훑는 룰렛 선택과 달리 적합도 스케일에 둔감하고, k 로 압력을 조절한다. */
export function tournament(
  pop: readonly Genome[], fits: readonly number[], k: number, rnd: () => number,
): Genome {
  let best = (rnd() * pop.length) | 0;
  for (let i = 1; i < k; i++) {
    const c = (rnd() * pop.length) | 0;
    if ((fits[c] as number) > (fits[best] as number)) best = c;
  }
  return pop[best] as Genome;
}

/** 혼합 교차(BLX-α): 두 부모 사이 구간을 α 만큼 바깥으로 넓혀 그 안에서 뽑는다.
 *  성분을 그대로 골라 오는 균등 교차와 달리 "부모 사이의 새 값"을 만들 수 있다. */
export function crossover(a: Genome, b: Genome, rnd: () => number, alpha = 0.5): Genome {
  const c = new Array<number>(DIM);
  for (let i = 0; i < DIM; i++) {
    const ai = a[i] as number, bi = b[i] as number;
    const lo = Math.min(ai, bi), hi = Math.max(ai, bi), d = hi - lo;
    c[i] = lo - alpha * d + rnd() * (d * (1 + 2 * alpha));
  }
  return normalize(c);
}

/** 변이: 각 성분을 확률 p 로 정규분포만큼 흔든다. 국소최적에서 빠져나오는 유일한 통로다. */
export function mutate(g: Genome, rnd: () => number, sigma = 0.2, p = 0.2): Genome {
  const c = g.slice();
  // 조건이 참일 때만 gauss 를 부른다 — 미리 뽑아 두면 난수 소비 순서가 달라져
  // 같은 시드로도 다른 학습 곡선이 나온다.
  for (let i = 0; i < DIM; i++) {
    if (rnd() < p) c[i] = (c[i] as number) + gauss(rnd) * sigma;
  }
  return normalize(c);
}

// ── 적합도 ───────────────────────────────────────────────────────────
export interface Fitness {
  lines: number;
  attack: number;
  placed: number;
}

export type FitnessFn = (g: Genome) => Fitness;

/**
 * 적합도 함수를 만든다.
 *
 * 같은 가중치라도 조각 순서에 따라 결과가 흔들린다. 그래서 시드 여러 개의 평균을 쓴다.
 * 시드를 매 세대 바꾸면 "운 좋은 세대"가 살아남아 그래프가 요동친다 — 고정한다.
 *
 * 캐시가 중요하다: 엘리트는 세대마다 그대로 살아남아 같은 유전자가 반복 평가된다.
 * 캐시 하나로 세대당 평가 횟수가 눈에 띄게 준다.
 */
export function makeFitness(
  ai: Ai, seeds: readonly number[], maxPieces: number, every = 0,
): FitnessFn {
  const cache = new Map<string, Fitness>();
  return function fitness(g: Genome): Fitness {
    const key = g.map((v) => v.toFixed(5)).join(',');
    const hit = cache.get(key);
    if (hit) return hit;
    ai.setWeights(g);
    let lines = 0, attack = 0, placed = 0;
    for (const s of seeds) {
      lines += ai.play(s >>> 0, maxPieces, every);
      attack += ai.playAttack;
      placed += ai.playPlaced;
    }
    const n = seeds.length;
    const r: Fitness = { lines: lines / n, attack: attack / n, placed: placed / n };
    cache.set(key, r);
    return r;
  };
}

// ── 진화 루프 ────────────────────────────────────────────────────────
export interface GenRecord {
  gen: number;
  best: number;
  mean: number;
  worst: number;
  lines: number;
  attack: number;
  placed: number;
  ms: number;
  weights: number[];
}

export interface EvolveOptions {
  pop?: number;
  gen?: number;
  elite?: number;
  k?: number;
  sigma?: number;
  mutP?: number;
  alpha?: number;
  seeds?: readonly number[];
  maxPieces?: number;
  rngSeed?: number;
  objective?: 'attack' | 'lines';
  every?: number;
  ai?: Ai;
  onGen?: ((r: GenRecord) => void) | null;
}

export interface EvolveResult {
  best: Genome;
  bestFit: number;
  log: GenRecord[];
}

/**
 * 한 세대에서 벌어지는 일은 네 줄로 요약된다.
 *   1) 전원을 평가한다
 *   2) 상위 elite 명은 그대로 다음 세대로 복사한다 (최고 기록이 사라지지 않게)
 *   3) 나머지는 토너먼트로 부모 둘을 뽑아 교차 + 변이로 만든다
 *   4) 반복
 */
export function evolve(opts: EvolveOptions = {}): EvolveResult {
  const {
    pop: POP = 32, gen: GEN = 30, elite = 2, k = 3,
    sigma = 0.2, mutP = 0.2, alpha = 0.5,
    seeds = [1, 2, 3], maxPieces = 400, rngSeed = 20260827,
    objective = 'attack', every = 0,
    ai = new Ai(new Tetris(1)), onGen = null,
  } = opts;

  const rnd = mulberry32(rngSeed);
  const fitness = makeFitness(ai, seeds, maxPieces, every);

  let popArr: Genome[] = Array.from({ length: POP }, () => randomGenome(rnd));
  const log: GenRecord[] = [];
  let best: Genome | null = null;
  let bestFit = -1;

  for (let g = 1; g <= GEN; g++) {
    const t0 = Date.now();
    const evals = popArr.map(fitness);
    const fits = evals.map((x) => x[objective]);

    const order = fits
      .map((f, i) => [f, i] as [number, number])
      .sort((a, b) => b[0] - a[0]);
    const gBestI = (order[0] as [number, number])[1];
    if ((fits[gBestI] as number) > bestFit) {
      bestFit = fits[gBestI] as number;
      best = (popArr[gBestI] as Genome).slice();
    }

    const mean = fits.reduce((s, x) => s + x, 0) / fits.length;
    const rec: GenRecord = {
      gen: g,
      best: +(fits[gBestI] as number).toFixed(1),
      mean: +mean.toFixed(1),
      worst: +(order[order.length - 1] as [number, number])[0].toFixed(1),
      lines: +(evals[gBestI] as Fitness).lines.toFixed(1),
      attack: +(evals[gBestI] as Fitness).attack.toFixed(1),
      placed: +(evals[gBestI] as Fitness).placed.toFixed(0),
      ms: 0,
      weights: (popArr[gBestI] as Genome).map((v) => +v.toFixed(4)),
    };

    // 다음 세대 만들기
    const next: Genome[] = order.slice(0, elite).map(([, i]) => (popArr[i] as Genome).slice());
    while (next.length < POP) {
      const a = tournament(popArr, fits, k, rnd);
      const b = tournament(popArr, fits, k, rnd);
      next.push(mutate(crossover(a, b, rnd, alpha), rnd, sigma, mutP));
    }
    popArr = next;

    rec.ms = Date.now() - t0;
    log.push(rec);
    if (onGen) onGen(rec);
  }
  return { best: best ?? randomGenome(rnd), bestFit, log };
}
