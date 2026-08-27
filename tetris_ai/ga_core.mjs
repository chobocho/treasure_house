// ga_core.mjs — 유전 알고리즘의 순수한 부분(난수·유전자·선택·교차·변이).
// wasm 도 파일 시스템도 건드리지 않는다. 그래서 Node 트레이너와 브라우저 라이브
// 학습이 이 파일 하나를 그대로 나눠 쓴다 — 덱에 인라인할 때는 각 줄 앞의
// `export ` 만 기계적으로 떼어 낸다(같은 함수 본문이라는 뜻이다).

// ── 결정론적 난수 ────────────────────────────────────────────────────
// Math.random() 을 쓰면 "덱에 실린 로그"를 재현할 수 없다. 씨앗을 고정한다.
export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
// 박스-뮐러: 균등난수 두 개 → 표준정규분포 하나
export function gauss(rnd) {
  const u = Math.max(rnd(), 1e-12), v = rnd();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ── 유전자 ───────────────────────────────────────────────────────────
// 유전자 = 실수 8개. 단, 길이는 1로 고정한다.
// w 와 2w 는 argmax 가 완전히 같다 — 크기는 정보가 아니라 잡음이다.
// 정규화하지 않으면 개체들이 "방향은 같은데 길이만 다른" 복제로 채워진다.
export const DIM = 8;
export function normalize(g) {
  let n = 0;
  for (const v of g) n += v * v;
  n = Math.sqrt(n) || 1;
  return g.map(v => v / n);
}
export function randomGenome(rnd) {
  return normalize(Array.from({ length: DIM }, () => gauss(rnd)));
}

// ── 선택·교차·변이 ───────────────────────────────────────────────────
// 토너먼트 선택: 무작위 k 명을 뽑아 그중 1등을 부모로 쓴다.
// 순위 전체를 훑는 룰렛 선택과 달리 적합도 스케일에 둔감하고, k 로 압력을 조절한다.
export function tournament(pop, fits, k, rnd) {
  let best = (rnd() * pop.length) | 0;
  for (let i = 1; i < k; i++) {
    const c = (rnd() * pop.length) | 0;
    if (fits[c] > fits[best]) best = c;
  }
  return pop[best];
}
// 혼합 교차(BLX-α): 두 부모 사이 구간을 α 만큼 바깥으로 넓혀 그 안에서 뽑는다.
// 성분을 그대로 골라 오는 균등 교차와 달리 "부모 사이의 새 값"을 만들 수 있다.
export function crossover(a, b, rnd, alpha = 0.5) {
  const c = new Array(DIM);
  for (let i = 0; i < DIM; i++) {
    const lo = Math.min(a[i], b[i]), hi = Math.max(a[i], b[i]), d = hi - lo;
    c[i] = lo - alpha * d + rnd() * (d * (1 + 2 * alpha));
  }
  return normalize(c);
}
// 변이: 각 성분을 확률 p 로 정규분포만큼 흔든다. 국소최적에서 빠져나오는 유일한 통로다.
export function mutate(g, rnd, sigma = 0.2, p = 0.2) {
  const c = g.slice();
  for (let i = 0; i < DIM; i++) if (rnd() < p) c[i] += gauss(rnd) * sigma;
  return normalize(c);
}
