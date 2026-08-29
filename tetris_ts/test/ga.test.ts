// ga.test.ts — GA 층의 단위 테스트 + 부 2 JS 구현과의 파리티.
//
// GA 의 버그는 조용하다. 난수를 한 번 더 소비하거나 정규화를 한 곳에서 빠뜨려도
// 학습은 "그럭저럭" 돌아가고, 다만 덱에 실을 학습 곡선이 재현되지 않는다.
// 그래서 순수 함수를 호출 순서까지 고정해 대조하고, 진화 루프도 통째로 대조한다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { Tetris } from '../src/core.js';
import { Ai } from '../src/ai.js';
import {
  mulberry32, gauss, normalize, randomGenome, tournament, crossover, mutate,
  makeFitness, evolve, LiveGa, DIM, type Genome, type GenRecord,
} from '../src/ga.js';
import {
  runGaOpsTrace, EVOLVE_CHECK, EVOLVE_CHECK_HARD, type GaOpsTrace,
} from '../src/trace_ga.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const GOLDEN = join(HERE, '..', '..', 'test', 'golden', 'ga_traces.json');

const TS_OPS = {
  mulberry32, gauss, normalize, randomGenome, tournament, crossover, mutate,
};

function len(g: readonly number[]): number {
  return Math.sqrt(g.reduce((s, v) => s + v * v, 0));
}

// ── 1. 난수 ───────────────────────────────────────────────────────────
test('mulberry32 는 [0,1) 범위의 결정론적 수열', () => {
  const a = mulberry32(42), b = mulberry32(42);
  for (let i = 0; i < 100; i++) {
    const v = a();
    assert.ok(v >= 0 && v < 1, `범위 밖: ${v}`);
    assert.equal(v, b(), '같은 시드는 같은 수열');
  }
  assert.notEqual(mulberry32(42)(), mulberry32(43)(), '다른 시드는 다른 수열');
});

test('gauss 는 평균 0 · 표준편차 1 근처', () => {
  const r = mulberry32(7);
  const n = 20000;
  let sum = 0, sq = 0;
  for (let i = 0; i < n; i++) { const v = gauss(r); sum += v; sq += v * v; }
  const mean = sum / n;
  const sd = Math.sqrt(sq / n - mean * mean);
  assert.ok(Math.abs(mean) < 0.05, `평균 ${mean}`);
  assert.ok(Math.abs(sd - 1) < 0.05, `표준편차 ${sd}`);
});

// ── 2. 유전자 ─────────────────────────────────────────────────────────
test('normalize 는 길이를 1로 만든다', () => {
  assert.ok(Math.abs(len(normalize([3, 4, 0, 0, 0, 0, 0, 0])) - 1) < 1e-12);
  assert.ok(Math.abs(len(normalize([-1, -1, -1, -1, -1, -1, -1, -1])) - 1) < 1e-12);
});

test('normalize 는 0벡터에서 죽지 않는다 (0으로 나누기 방어)', () => {
  const z = normalize([0, 0, 0, 0, 0, 0, 0, 0]);
  assert.equal(z.length, DIM);
  assert.ok(z.every((v) => v === 0), `0벡터는 0벡터로: ${z}`);
  assert.ok(z.every(Number.isFinite), 'NaN/Infinity 가 나오면 안 된다');
});

test('randomGenome 은 길이 8, 노름 1', () => {
  const r = mulberry32(1);
  for (let i = 0; i < 50; i++) {
    const g = randomGenome(r);
    assert.equal(g.length, DIM);
    assert.ok(Math.abs(len(g) - 1) < 1e-12);
  }
});

// ── 3. 선택·교차·변이 ─────────────────────────────────────────────────
test('토너먼트는 적합도가 높은 쪽으로 치우친다', () => {
  const pop: Genome[] = Array.from({ length: 8 }, (_, i) => [i, 0, 0, 0, 0, 0, 0, 0]);
  const fits = pop.map((_, i) => i); // 인덱스가 곧 적합도
  const r = mulberry32(3);
  let sum = 0;
  const N = 4000;
  for (let i = 0; i < N; i++) sum += (tournament(pop, fits, 3, r) as Genome)[0] as number;
  const avg = sum / N;
  assert.ok(avg > 3.5, `k=3 토너먼트의 평균 적합도 ${avg} — 무작위(3.5)보다 커야 한다`);
  assert.ok(avg < 7, `1등만 뽑히면 다양성이 죽는다 (평균 ${avg})`);
});

test('k=1 토너먼트는 그냥 무작위 선택', () => {
  const pop: Genome[] = Array.from({ length: 8 }, (_, i) => [i, 0, 0, 0, 0, 0, 0, 0]);
  const fits = pop.map((_, i) => i);
  const r = mulberry32(9);
  let sum = 0;
  const N = 8000;
  for (let i = 0; i < N; i++) sum += (tournament(pop, fits, 1, r) as Genome)[0] as number;
  assert.ok(Math.abs(sum / N - 3.5) < 0.25, `평균 ${sum / N} 은 3.5 근처여야 한다`);
});

test('BLX-α 교차 결과는 정규화되고, 부모 구간 바깥도 나올 수 있다', () => {
  const a: Genome = normalize([1, 0, 0, 0, 0, 0, 0, 0]);
  const b: Genome = normalize([0, 1, 0, 0, 0, 0, 0, 0]);
  const r = mulberry32(11);
  let outside = 0;
  for (let i = 0; i < 200; i++) {
    const c = crossover(a, b, r, 0.5);
    assert.ok(Math.abs(len(c) - 1) < 1e-12, '교차 결과도 노름 1');
    // 정규화 전 구간은 [-0.5, 1.5] 였으므로 성분 부호가 뒤집힌 것도 나온다
    if ((c[0] as number) < 0 || (c[1] as number) < 0) outside++;
  }
  assert.ok(outside > 0, 'α 확장이 실제로 부모 바깥 값을 만들어야 한다');
});

test('변이는 확률 p 에 비례해 유전자를 바꾼다', () => {
  const g: Genome = normalize([1, 1, 1, 1, 1, 1, 1, 1]);
  const r = mulberry32(5);
  // p=0 이어도 normalize 를 한 번 더 거친다. 부동소수점에서 정규화는 완전한 멱등이
  // 아니라서(1/√8 을 다시 정규화하면 마지막 비트가 흔들린다) 근사로 비교한다.
  const same = mutate(g, r, 0.2, 0);
  same.forEach((v, i) => assert.ok(Math.abs(v - (g[i] as number)) < 1e-15, `p=0 이면 그대로: ${v}`));
  const changed = mutate(g, mulberry32(5), 0.2, 1);
  assert.ok(changed.some((v, i) => v !== (g[i] as number)), 'p=1 이면 전부 흔들린다');
  assert.ok(Math.abs(len(changed) - 1) < 1e-12, '변이 결과도 노름 1');
});

// ── 4. 적합도 ─────────────────────────────────────────────────────────
test('적합도는 캐시된다 — 같은 유전자를 두 번 평가하지 않는다', () => {
  const ai = new Ai(new Tetris(1));
  let calls = 0;
  const orig = ai.play.bind(ai);
  ai.play = (s: number, m: number, e: number): number => { calls++; return orig(s, m, e); };
  const fit = makeFitness(ai, [1, 2], 60, 0);
  const g = randomGenome(mulberry32(1));
  const a = fit(g);
  const after = calls;
  const b = fit(g.slice()); // 값이 같은 다른 배열
  assert.equal(calls, after, '캐시 적중이면 play 를 다시 부르면 안 된다');
  assert.deepEqual(a, b);
  assert.equal(after, 2, '시드 2개 = 판 2번');
});

test('좋은 유전자가 나쁜 유전자보다 적합도가 높다', () => {
  const fit = makeFitness(new Ai(new Tetris(1)), [1, 2], 200, 0);
  const good = fit(normalize([0.07328, 0.064795, -0.477997, 0.210324, -0.008971, -0.391833, -0.504655, -0.556259]));
  const bad = fit(normalize([1, 1, 1, 1, 1, 1, 1, 1]));
  assert.ok(good.lines > bad.lines, `${good.lines} vs ${bad.lines}`);
  assert.ok(good.placed > bad.placed, `놓은 조각 ${good.placed} vs ${bad.placed}`);
});

// ── 5. 진화 루프 ──────────────────────────────────────────────────────
test('진화는 세대를 거치며 최고 적합도가 단조 증가한다 (엘리트 보존)', () => {
  const { log, bestFit } = evolve({
    pop: 10, gen: 5, maxPieces: 100, seeds: [1], rngSeed: 99, ai: new Ai(new Tetris(1)),
  });
  assert.equal(log.length, 5);
  let running = -Infinity;
  for (const r of log) {
    running = Math.max(running, r.best);
    assert.ok(r.best >= r.mean - 1e-9, `세대 ${r.gen}: 최고 ${r.best} < 평균 ${r.mean}`);
    assert.ok(r.mean >= r.worst - 1e-9, `세대 ${r.gen}: 평균 ${r.mean} < 최저 ${r.worst}`);
  }
  assert.equal(bestFit, running, '반환된 최고 적합도는 로그 전체의 최고와 같아야 한다');
  // 엘리트 2명이 그대로 넘어가므로 다음 세대의 최고는 이전 이상이어야 한다
  for (let i = 1; i < log.length; i++) {
    assert.ok(
      (log[i] as GenRecord).best >= (log[i - 1] as GenRecord).best - 1e-9,
      `세대 ${i + 1} 의 최고가 떨어졌다: ${(log[i - 1] as GenRecord).best} → ${(log[i] as GenRecord).best}`,
    );
  }
});

test('같은 rngSeed 는 같은 학습 곡선을 낸다', () => {
  const cfg = { pop: 8, gen: 3, maxPieces: 80, seeds: [1], rngSeed: 777 };
  const a = evolve({ ...cfg, ai: new Ai(new Tetris(1)) });
  const b = evolve({ ...cfg, ai: new Ai(new Tetris(1)) });
  assert.deepEqual(a.log.map((r) => r.weights), b.log.map((r) => r.weights));
  assert.equal(a.bestFit, b.bestFit);
});

// ── 6. 부 2 JS 구현과의 파리티 ────────────────────────────────────────
interface EvolveGolden {
  best: number[];
  bestFit: number;
  log: Omit<GenRecord, 'ms'>[];
}
interface GaGolden {
  v: number;
  ops: GaOpsTrace;
  evolve: { easy: EvolveGolden; hard: EvolveGolden };
}

const golden: GaGolden | null = existsSync(GOLDEN)
  ? (JSON.parse(readFileSync(GOLDEN, 'utf8')) as GaGolden)
  : null;

function requireGolden(): GaGolden {
  if (!golden) throw new Error(`${GOLDEN} 이 없다 — 먼저 \`make golden\` 을 돌려라`);
  return golden;
}

test('GA 골든 파일이 있어야 한다 (make golden)', () => {
  const gd = requireGolden();
  assert.ok(gd.ops.rnd.length > 0);
});

test('파리티: 순수 함수 — 난수 소비 순서까지 부 2 의 JS 와 동일', () => {
  const gd = requireGolden();
  const got = runGaOpsTrace(TS_OPS);
  for (const key of Object.keys(gd.ops) as (keyof GaOpsTrace)[]) {
    assert.deepEqual(got[key], gd.ops[key], `${key} 가 다르다`);
  }
});

test('파리티: 진화 루프 — 세대별 로그가 통째로 동일', () => {
  const gd = requireGolden();
  for (const [name, cfg] of [['easy', EVOLVE_CHECK], ['hard', EVOLVE_CHECK_HARD]] as const) {
    const want = gd.evolve[name];
    const got = evolve({ ...cfg, ai: new Ai(new Tetris(1)) });
    assert.equal(got.log.length, want.log.length, `${name}: 세대 수`);
    for (let i = 0; i < got.log.length; i++) {
      const { ms: _ms, ...mine } = got.log[i] as GenRecord;
      assert.deepEqual(mine, want.log[i], `${name}: 세대 ${i + 1} 의 로그가 다르다`);
    }
    assert.deepEqual(got.best, want.best, `${name}: 최종 가중치`);
    assert.equal(got.bestFit, want.bestFit, `${name}: 최고 적합도`);
  }
});

// ── 7. 학습 산출물이 실측인지 ─────────────────────────────────────────
//
// 덱의 학습 곡선은 ga_log.json 을 그대로 그린다. 그러니 그 파일이 "정말 이 코드가
// 낸 숫자인지"를 테스트가 확인해야 한다. 손으로 고친 로그는 여기서 걸린다.
interface WeightsFile {
  best: number[];
  fitness: number;
  objective: 'attack' | 'lines';
  gen: number;
  pop: number;
  maxPieces: number;
  seedsUsed: number[];
  features: string[];
  levels: Record<string, number[]>;
}

const ROOT = join(HERE, '..', '..');
const WEIGHTS = join(ROOT, 'weights.json');
const GA_LOG = join(ROOT, 'ga_log.json');

test('weights.json 의 적합도는 다시 돌려도 그대로 나온다', () => {
  assert.ok(existsSync(WEIGHTS), 'weights.json 이 없다 — `make train` 을 돌려라');
  const w = JSON.parse(readFileSync(WEIGHTS, 'utf8')) as WeightsFile;
  assert.equal(w.features.length, DIM);
  assert.equal(w.best.length, DIM);

  const fit = makeFitness(new Ai(new Tetris(1)), w.seedsUsed, w.maxPieces, 0);
  const got = fit(w.best);
  assert.equal(
    +got[w.objective].toFixed(1), w.fitness,
    `기록된 적합도 ${w.fitness} 를 재현하지 못했다 (실측 ${got[w.objective].toFixed(1)})`,
  );
});

test('ga_log.json 은 기록된 세대 수만큼 있고 마지막이 최고와 일치한다', () => {
  assert.ok(existsSync(GA_LOG), 'ga_log.json 이 없다 — `make train` 을 돌려라');
  const w = JSON.parse(readFileSync(WEIGHTS, 'utf8')) as WeightsFile;
  const log = JSON.parse(readFileSync(GA_LOG, 'utf8')) as GenRecord[];
  assert.equal(log.length, w.gen, '로그 세대 수가 weights.json 의 gen 과 달라야 할 이유가 없다');
  const best = Math.max(...log.map((r) => r.best));
  assert.equal(best, w.fitness, '로그의 최고 적합도와 weights.json 의 fitness');
  assert.ok(log.every((r) => r.weights.length === DIM), '세대마다 가중치 8개');
  assert.ok(log.every((r) => r.ms >= 0), '소요 시간이 기록돼 있어야 한다');
});

test('난이도 프리셋은 학습 순서대로 강해진다 (easy < normal < hard < max)', () => {
  const w = JSON.parse(readFileSync(WEIGHTS, 'utf8')) as WeightsFile;
  // "세다"의 기준은 **공격량**이다. GA 가 최적화한 목표가 그것이기 때문이다.
  // 생존 조각 수로 재면 easy 가 max 를 이기는 일이 벌어진다 — max 는 테트리스를
  // 노리느라 판을 높이 쌓아서 가끔 죽고, easy 는 얌전히 싱글만 지우며 오래 버틴다.
  // 오래 버티는 것과 상대를 이기는 것은 다른 문제다.
  const attackOf = (g: number[]): number => {
    let atk = 0;
    for (const s of w.seedsUsed) {
      const ai = new Ai(new Tetris(1), g);
      ai.play(s, w.maxPieces, 0);
      atk += ai.playAttack;
    }
    return atk / w.seedsUsed.length;
  };
  const easy = attackOf(w.levels.easy as number[]);
  const normal = attackOf(w.levels.normal as number[]);
  const hard = attackOf(w.levels.hard as number[]);
  const max = attackOf(w.levels.max as number[]);
  const line = `easy ${easy.toFixed(1)} / normal ${normal.toFixed(1)} / hard ${hard.toFixed(1)} / max ${max.toFixed(1)}`;
  assert.ok(normal > easy, `normal 이 easy 보다 세야 한다 — ${line}`);
  assert.ok(hard > normal, `hard 가 normal 보다 세야 한다 — ${line}`);
  assert.ok(max > hard, `max 가 hard 보다 세야 한다 — ${line}`);
  assert.equal(+max.toFixed(1), w.fitness, `max 프리셋의 공격량이 곧 기록된 적합도 — ${line}`);
});

// ── 5. 브라우저 라이브 학습 ───────────────────────────────────────────
// 라이브 학습은 프레임을 쪼개 쓰는 것 말고는 트레이너와 완전히 같아야 한다.
// 다르면 덱 안의 데모가 "비슷하지만 다른 것"을 보여 주는 셈이 된다.
const LIVE_CFG = { pop: 8, gen: 3, maxPieces: 60, seeds: [1], rngSeed: 991, elite: 2 } as const;

test('라이브 학습은 트레이너(evolve)와 같은 곡선을 낸다', () => {
  const want = evolve({ ...LIVE_CFG, ai: new Ai(new Tetris(1)) }).log;
  const live = new LiveGa({ ...LIVE_CFG, ai: new Ai(new Tetris(1)) });
  while (live.log.length < LIVE_CFG.gen) live.step();
  assert.equal(live.log.length, want.length);
  for (let i = 0; i < want.length; i++) {
    const a = { ...(live.log[i] as GenRecord), ms: 0 };
    const b = { ...(want[i] as GenRecord), ms: 0 }; // 소요 시간만 다르다
    assert.deepEqual(a, b, `${i + 1}세대의 기록이 다르다`);
  }
});

test('예산을 잘게 쪼개도 결과가 같다 (한 프레임에 한 개체씩)', () => {
  const want = evolve({ ...LIVE_CFG, ai: new Ai(new Tetris(1)) });
  const live = new LiveGa({ ...LIVE_CFG, ai: new Ai(new Tetris(1)) });
  let guard = 0;
  while (live.log.length < LIVE_CFG.gen && guard++ < 1000) live.step(0); // 예산 0 = 최소 한 개체
  assert.equal(live.log.length, LIVE_CFG.gen, '세대가 끝나지 않았다');
  assert.deepEqual(live.best, want.best, '최고 유전자가 다르다');
  assert.equal(live.bestFit, want.bestFit);
});

test('진행률은 0에서 1 사이를 오간다', () => {
  const live = new LiveGa({ ...LIVE_CFG, ai: new Ai(new Tetris(1)) });
  assert.equal(live.progress, 0);
  live.step(0);
  assert.ok(live.progress > 0 && live.progress < 1, `중간 진행률이 이상하다 (${live.progress})`);
  while (live.log.length < 1) live.step(0);
  assert.equal(live.gen, 2, '한 세대가 끝나면 다음 세대로 넘어간다');
  assert.equal(live.progress, 0, '새 세대는 0에서 시작한다');
});
