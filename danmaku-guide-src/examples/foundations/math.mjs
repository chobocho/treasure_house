import { pathToFileURL } from 'node:url';
import { dsin, dcos, direction, overlaps, FixedStep, Rng } from './core.mjs';

// 슬라이드의 수치 예시는 손으로 계산하지 않고 이 파일을 실제로 실행한 출력만 싣는다.
const n = (value, digits = 6) => Number(value.toFixed(digits));

// dsin 내부의 사분면 접기와 같은 규칙을 따로 보여 주기 위한 계산이다.
function fold(turn) {
  let t = turn - Math.floor(turn);
  if (t > .75) t -= 1;
  else if (t > .25) t = .5 - t;
  return n(t, 4);
}

export const topics = {
  // #region math-vectors
  vectors() {
    const [ux, uy] = direction(3, 4);
    const [dx, dy] = direction(1, -1);
    return [
      `|(3, 4)| = √(3² + 4²) = ${Math.sqrt(3 * 3 + 4 * 4)}`,
      `정규화 (3, 4) → (${n(ux)}, ${n(uy)}), 길이 ${n(Math.hypot(ux, uy))}`,
      `대각선 (1, −1) × 4 그대로 → 길이 ${n(Math.hypot(4, 4))}`,
      `대각선 정규화 뒤 × 4 → (${n(dx * 4)}, ${n(dy * 4)}), 길이 ${n(Math.hypot(dx * 4, dy * 4))}`,
      `영벡터 정규화 → (${direction(0, 0).join(', ')})`
    ];
  },
  // #endregion
  // #region math-angles
  angles() {
    const rows = [0, .1, .25, .4, .9, 1.25].map((t) =>
      `회전수 ${t} = ${n(t * 2 * Math.PI, 4)}rad, 접은 값 ${fold(t)}, dsin ${n(dsin(t))}`);
    let worst = 0;
    for (let i = -360; i <= 720; i++) worst = Math.max(worst, Math.abs(dsin(i / 360) - Math.sin(i / 360 * 2 * Math.PI)));
    rows.push(`−1~2바퀴 1081점에서 Math.sin과의 최대 오차 ${worst.toExponential(2)}`);
    return rows;
  },
  // #endregion
  // #region math-rotation
  rotation() {
    const turn = .025, c = dcos(turn), s = dsin(turn);
    const x = 0, y = 1;
    const rx = x * c - y * s, ry = x * s + y * c;
    return [
      `Δ = ${turn}바퀴 = ${n(turn * 360, 1)}°, cos Δ = ${n(c)}, sin Δ = ${n(s)}`,
      `(0, 1) 회전 → (${n(rx)}, ${n(ry)}), 길이 ${n(Math.hypot(rx, ry))}`
    ];
  },
  // #endregion
  // #region math-patterns
  patterns() {
    const ring = Array.from({ length: 8 }, (_, i) => i / 8);
    const fan = Array.from({ length: 7 }, (_, i) => n((i - 3) * .025, 4));
    const gap = Math.min(.025, .5 / 64);
    return [
      `링 8발 회전수: ${ring.join(', ')}`,
      `부채꼴 7발 각도 차이: ${fan.join(', ')}`,
      `부채꼴 64발 간격 = min(0.025, 0.5/64) = ${gap}, 전체 폭 ${n(63 * gap, 4)}`,
      `예전 나선: 60 × 0.007 = ${n(60 * .007, 4)}, 1/8 대칭 뒤 보이는 회전 ${n((60 * .007) % (1 / 8), 4)}`,
      `지금 나선: 6 × 0.007 = ${n(6 * .007, 4)}바퀴씩`,
      ...[0, 60, 120, 180].map((t) => `파동 중심 틱 ${t}: ${n(.25 + dsin(t / 180) * .12, 4)}`)
    ];
  },
  // #endregion
  // #region math-loop
  loop() {
    const second = new FixedStep();
    let steps30 = 0;
    for (let i = 0; i < 30; i++) second.advance(1 / 30, () => steps30++);
    const clock = new FixedStep();
    let steps = 0;
    const alphas = [0, 1, 2].map(() => n(clock.advance(1 / 40, () => steps++), 4));
    return [
      `30Hz로 1초 렌더 → 논리 스텝 ${steps30}번`,
      `40Hz 렌더 세 번 → 논리 스텝 ${steps}번, 남은 비율 α = ${alphas.join(', ')}`,
      `보간 예: 100 + (110 − 100) × ${alphas[0]} = ${n(100 + 10 * alphas[0], 4)}`
    ];
  },
  // #endregion
  // #region math-collision
  collision() {
    const hit = (6.5) ** 2, graze = 20 ** 2;
    return [
      `적탄 (245, 564): dx² + dy² = ${5 * 5 + 4 * 4}, (2.5 + 4)² = ${hit} → 피격 ${overlaps(240, 560, 2.5, 245, 564, 4)}`,
      `적탄 (250, 570): ${10 * 10 + 10 * 10} > ${hit} → 피격 ${overlaps(240, 560, 2.5, 250, 570, 4)}`,
      `같은 적탄: ${10 * 10 + 10 * 10} ≤ (16 + 4)² = ${graze} → 그레이즈 ${overlaps(240, 560, 16, 250, 570, 4)}`
    ];
  },
  // #endregion
  // #region math-random
  random() {
    const rng = new Rng(1);
    const first = [rng.next(), rng.next(), rng.next()];
    const r = new Rng(0x2F6E2B1).next();
    const full = 2 ** 32, buckets = 416;
    return [
      `시드 1: ${first.join(', ')}`,
      `시드 0은 고정점: ${new Rng(0).next()}`,
      `게임 시드 첫 값 ${r} → 적 x = 32 + ${r} mod 416 = ${32 + r % 416}`,
      `2³² = 416 × ${Math.floor(full / buckets)} + ${full % buckets}`,
      `32비트 값이 고르게 나온다면 나머지 0~${full % buckets - 1}는 ${Math.floor(full / buckets) + 1}번, 나머지 ${full % buckets}~415는 ${Math.floor(full / buckets)}번`
    ];
  }
  // #endregion
};

// #region math-cli
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const topic = process.argv[2];
  if (!Object.hasOwn(topics, topic)) throw new Error('주제는 ' + Object.keys(topics).join(', ') + ' 중 하나');
  console.log(topics[topic]().join('\n'));
}
// #endregion
