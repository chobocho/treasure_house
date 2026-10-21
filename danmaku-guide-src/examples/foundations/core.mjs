// #region turns
export function wrapTurn(turn) {
  return turn - Math.floor(turn);
}
// #endregion

// #region dsin
export function dsin(turn) {
  // #region angle-fold
  let t = wrapTurn(turn);
  if (t > .75) t -= 1;
  else if (t > .25) t = .5 - t;
  // #endregion
  const x = t * 6.283185307179586;
  const z = x * x;
  // 언어 사이의 반올림 차이를 줄이기 위해 곱셈과 덧셈의 순서를 고정한다.
  // #region horner
  let p = 1 / 6227020800;
  p = -1 / 39916800 + z * p;
  p = 1 / 362880 + z * p;
  p = -1 / 5040 + z * p;
  p = 1 / 120 + z * p;
  p = -1 / 6 + z * p;
  return x * (1 + z * p);
  // #endregion
}
// #endregion

// #region dcos
export function dcos(turn) {
  return dsin(turn + .25);
}
// #endregion

// #region direction
export function direction(dx, dy) {
  const length = Math.sqrt(dx * dx + dy * dy);
  return length === 0 ? [0, 0] : [dx / length, dy / length];
}
// #endregion

// #region collision
export function overlaps(ax, ay, ar, bx, by, br) {
  const dx = ax - bx, dy = ay - by;
  const radius = ar + br;
  return dx * dx + dy * dy <= radius * radius;
}
// #endregion

export class Pool {
  // #region pool-init
  constructor(capacity) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new Error('풀 용량은 음이 아닌 정수여야 한다');
    this.capacity = capacity;
    this.count = 0;
    this.x = new Float64Array(capacity);
    this.y = new Float64Array(capacity);
    this.vx = new Float64Array(capacity);
    this.vy = new Float64Array(capacity);
  }
  // #endregion
  // #region pool-add
  add(x, y, vx, vy) {
    if (this.count === this.capacity) return -1;
    const i = this.count++;
    this.x[i] = x; this.y[i] = y;
    this.vx[i] = vx; this.vy[i] = vy;
    return i;
  }
  // #endregion
  // #region pool-erase
  erase(i) {
    if (!Number.isInteger(i) || i < 0 || i >= this.count) return false;
    const last = --this.count;
    this.x[i] = this.x[last]; this.y[i] = this.y[last];
    this.vx[i] = this.vx[last]; this.vy[i] = this.vy[last];
    return true;
  }
  // #endregion
}

// #region pool-step
// 역순으로 지우면 마지막에서 가져온 요소를 같은 스텝에 다시 갱신하지 않는다. 시간 O(n), 추가 공간 O(1).
export function stepPool(pool, width, height) {
  for (let i = pool.count - 1; i >= 0; i--) {
    pool.x[i] += pool.vx[i]; pool.y[i] += pool.vy[i];
    if (pool.x[i] < -32 || pool.x[i] > width + 32 || pool.y[i] < -32 || pool.y[i] > height + 32) pool.erase(i);
  }
}
// #endregion

// #region pattern-periods
// 나선은 링 전체를 가끔 쏘면 회전이 링 대칭에 상쇄되어 링과 구별되지 않는다.
// 그래서 나선만 짧은 주기로 이어 쏘고 나머지는 한 번에 한 묶음씩 쏜다.
export const PATTERN_PERIODS = { ring: 48, fan: 48, spiral: 4, wave: 48 };
// #endregion

// #region pattern
// 발사 중 임시 배열을 만들지 않는다. 탄환 수 n에 대해 시간 O(n), 추가 공간 O(1).
export function emitPattern(pool, mode, count, speed, x, y, tick, targetX, targetY) {
  // #region aim-vector
  const dx = targetX - x, dy = targetY - y;
  const length = Math.sqrt(dx * dx + dy * dy);
  const ux = length > 0 ? dx / length : 0;
  const uy = length > 0 ? dy / length : 1;
  // #endregion
  // 탄수가 많아도 부채꼴 전체가 반 바퀴를 넘어 겹치지 않도록 간격을 줄인다.
  const fanGap = Math.min(.025, .5 / count);
  for (let i = 0; i < count; i++) {
    // #region pattern-angle
    let turn = i / count;
    if (mode === 'spiral') turn += tick * .007;
    // 파동의 위상은 시간에만 두어 부채꼴 전체가 좌우로 흔들리게 한다.
    if (mode === 'wave') turn = .25 + dsin(tick / 180) * .12 + (i - (count - 1) / 2) * .025;
    if (mode === 'fan') turn = (i - (count - 1) / 2) * fanGap;
    // #endregion
    // #region pattern-velocity
    const c = dcos(turn), s = dsin(turn);
    const vx = mode === 'fan' ? ux * c - uy * s : c;
    const vy = mode === 'fan' ? ux * s + uy * c : s;
    pool.add(x, y, vx * speed, vy * speed);
    // #endregion
  }
}
// #endregion

export class FixedStep {
  constructor() { this.accumulator = 0; this.frame = 0; }
  // #region fixed-step
  advance(seconds, step) {
    if (!Number.isFinite(seconds) || seconds < 0) throw new Error('유효하지 않은 시간 간격');
    const dt = 1 / 60;
    this.accumulator += Math.min(seconds, .25);
    while (this.accumulator + 1e-12 >= dt) {
      step(this.frame++);
      this.accumulator = Math.max(0, this.accumulator - dt);
    }
    return this.accumulator / dt;
  }
  // #endregion
}

export class Rng {
  constructor(seed) { this.state = seed >>> 0; }
  // #region rng
  next() {
    let x = this.state;
    x = (x ^ (x << 13)) >>> 0;
    x = (x ^ (x >>> 17)) >>> 0;
    x = (x ^ (x << 5)) >>> 0;
    this.state = x;
    return x;
  }
  // #endregion
}

// #region checksum
// 언어마다 다른 음수 나머지를 피하려고 더할 때마다 무부호로 되돌린다. 시간 O(n), 추가 공간 O(1).
export function checksum(pool) {
  let sum = 0;
  for (let i = 0; i < pool.count; i++) sum = (sum + Math.floor(pool.x[i] * 16) * 31 + Math.floor(pool.y[i] * 16)) >>> 0;
  return sum;
}
// #endregion
