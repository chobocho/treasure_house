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
 * 한 세대를 **조각내어** 돌릴 수 있는 진화 루프.
 *
 * 한 세대에서 벌어지는 일은 네 줄로 요약된다.
 *   1) 전원을 평가한다
 *   2) 상위 elite 명은 그대로 다음 세대로 복사한다 (최고 기록이 사라지지 않게)
 *   3) 나머지는 토너먼트로 부모 둘을 뽑아 교차 + 변이로 만든다
 *   4) 반복
 *
 * 문제는 1)이 오래 걸린다는 것이다. 개체 32명을 한 번에 평가하면 몇 초가 걸리고,
 * 브라우저에서 그러면 화면이 그동안 얼어붙는다. 그래서 "예산(ms)만큼만 평가하고
 * 돌아오는" 모양으로 짰다. 트레이너(evolve)는 예산 없이 이걸 돌리는 얇은 껍데기다.
 * 두 경로가 같은 코드를 쓰므로 덱 안의 라이브 학습과 `make train` 의 곡선은
 * 갈라질 수 없다 — 테스트가 두 로그를 통째로 비교한다.
 */
export class LiveGa {
  pop: Genome[];
  readonly log: GenRecord[] = [];
  best: Genome | null = null;
  bestFit = -1;
  /** 지금 진행 중인 세대 번호 (1부터) */
  gen = 1;
  /** 이번 세대에서 평가를 마친 개체 수 */
  idx = 0;

  private evals: Fitness[] = [];
  private readonly rnd: () => number;
  private readonly fit: FitnessFn;
  private readonly POP: number;
  private readonly elite: number;
  private readonly k: number;
  private readonly sigma: number;
  private readonly mutP: number;
  private readonly alpha: number;
  private readonly objective: 'attack' | 'lines';
  private readonly onGen: ((r: GenRecord) => void) | null;
  private spentMs = 0;

  constructor(opts: EvolveOptions = {}) {
    const {
      pop: POP = 32, elite = 2, k = 3, sigma = 0.2, mutP = 0.2, alpha = 0.5,
      seeds = [1, 2, 3], maxPieces = 400, rngSeed = 20260827,
      objective = 'attack', every = 0,
      ai = new Ai(new Tetris(1)), onGen = null,
    } = opts;
    this.POP = POP; this.elite = elite; this.k = k;
    this.sigma = sigma; this.mutP = mutP; this.alpha = alpha;
    this.objective = objective; this.onGen = onGen;
    this.rnd = mulberry32(rngSeed);
    this.fit = makeFitness(ai, seeds, maxPieces, every);
    this.pop = Array.from({ length: POP }, () => randomGenome(this.rnd));
  }

  /** 이번 세대의 진행률 (0~1). 세대가 넘어가면 다시 0. */
  get progress(): number {
    return this.idx / this.pop.length;
  }

  /**
   * 예산 안에서 개체를 평가한다.
   *
   * 개체 하나는 **반드시** 평가한다. 예산이 0이라고 아무것도 안 하면 호출자가
   * 무한히 불러도 진도가 안 나간다 — 프레임마다 부르는 쪽에서 가장 흔한 사고다.
   *
   * @returns 이번 호출로 한 세대가 끝났으면 true
   */
  step(budgetMs = Infinity, now: () => number = Date.now): boolean {
    const t0 = now();
    do {
      this.evals[this.idx] = this.fit(this.pop[this.idx] as Genome);
      this.idx++;
    } while (this.idx < this.pop.length && now() - t0 < budgetMs);
    this.spentMs += now() - t0;
    if (this.idx < this.pop.length) return false;
    this.closeGen();
    return true;
  }

  /** 세대 마무리 — 기록을 남기고 다음 개체군을 낳는다. */
  private closeGen(): void {
    const fits = this.evals.map((x) => x[this.objective]);
    const order = fits
      .map((f, i) => [f, i] as [number, number])
      .sort((a, b) => b[0] - a[0]);
    const gBestI = (order[0] as [number, number])[1];
    if ((fits[gBestI] as number) > this.bestFit) {
      this.bestFit = fits[gBestI] as number;
      this.best = (this.pop[gBestI] as Genome).slice();
    }

    const mean = fits.reduce((s, x) => s + x, 0) / fits.length;
    const rec: GenRecord = {
      gen: this.gen,
      best: +(fits[gBestI] as number).toFixed(1),
      mean: +mean.toFixed(1),
      worst: +(order[order.length - 1] as [number, number])[0].toFixed(1),
      lines: +(this.evals[gBestI] as Fitness).lines.toFixed(1),
      attack: +(this.evals[gBestI] as Fitness).attack.toFixed(1),
      placed: +(this.evals[gBestI] as Fitness).placed.toFixed(0),
      ms: this.spentMs,
      weights: (this.pop[gBestI] as Genome).map((v) => +v.toFixed(4)),
    };

    // 다음 세대 만들기 — 난수 소비 순서가 곧 재현성이다. 엘리트 복사에는 난수를
    // 쓰지 않고, 자식 하나마다 토너먼트 2회 + 교차 + 변이 순서로만 쓴다.
    const next: Genome[] = order.slice(0, this.elite).map(([, i]) => (this.pop[i] as Genome).slice());
    while (next.length < this.POP) {
      const a = tournament(this.pop, fits, this.k, this.rnd);
      const b = tournament(this.pop, fits, this.k, this.rnd);
      next.push(mutate(crossover(a, b, this.rnd, this.alpha), this.rnd, this.sigma, this.mutP));
    }
    this.pop = next;
    this.evals = [];
    this.idx = 0;
    this.spentMs = 0;
    this.gen++;
    this.log.push(rec);
    if (this.onGen) this.onGen(rec);
  }
}

/** 트레이너용 — 끝까지 돌린다. 브라우저와 같은 코드를 쓰되 예산을 두지 않을 뿐이다. */
export function evolve(opts: EvolveOptions = {}): EvolveResult {
  const GEN = opts.gen ?? 30;
  const ga = new LiveGa(opts);
  while (ga.log.length < GEN) ga.step();
  return { best: ga.best ?? (ga.pop[0] as Genome), bestFit: ga.bestFit, log: ga.log };
}
