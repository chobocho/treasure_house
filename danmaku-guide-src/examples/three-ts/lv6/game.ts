// #region constants
export const WIDTH = 480, HEIGHT = 640, SEED = 0x2f6e2b1;
export const LEFT = 1, RIGHT = 2, UP = 4, DOWN = 8;
export const SHOOT = 16, FOCUS = 32, BOMB = 64, START = 128, PAUSE = 256;
export const PLAYER_SPEED = 4, FOCUS_SPEED = 1.6, PLAYER_RADIUS = 2.5, GRAZE_RADIUS = 16;
export const SHOT_PERIOD = 8, SHOT_SPEED = 8;
const floatFields = ['x', 'y', 'vx', 'vy', 'radius', 'hp'] as const;
const intFields = ['kind', 'age', 'mark'] as const;
const fields = [...floatFields, ...intFields] as const;
// #endregion

// #region dsin
// 접기와 Horner 연산 순서를 모든 트랙에서 유지한다. 시간 O(1), 추가 공간 O(1).
export function dsin(turn: number): number {
  // #region angle-fold
  let t = turn - Math.floor(turn);
  if (t > .75) t -= 1;
  else if (t > .25) t = .5 - t;
  // #endregion
  const x = t * 6.283185307179586, z = x * x;
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
export function dcos(turn: number): number { return dsin(turn + .25); }
// #endregion

// #region rng
export class Rng {
  state: number;
  constructor(seed: number) { this.state = seed >>> 0; }
  next(): number {
    let x = this.state;
    x = (x ^ (x << 13)) >>> 0;
    x = (x ^ (x >>> 17)) >>> 0;
    x = (x ^ (x << 5)) >>> 0;
    this.state = x;
    return x;
  }
}
// #endregion

// #region collision
export function overlaps(ax: number, ay: number, ar: number, bx: number, by: number, br: number): boolean {
  const dx = ax - bx, dy = ay - by, radius = ar + br;
  return dx * dx + dy * dy <= radius * radius;
}
// #endregion

export class Pool {
  // #region pool-init
  count = 0;
  x!: Float64Array; y!: Float64Array; vx!: Float64Array; vy!: Float64Array;
  radius!: Float64Array; hp!: Float64Array;
  kind!: Int32Array; age!: Int32Array; mark!: Int32Array;
  constructor(readonly capacity: number) {
    if (!Number.isInteger(capacity) || capacity < 0) throw new Error('잘못된 풀 용량');
    for (const name of floatFields) this[name] = new Float64Array(capacity);
    for (const name of intFields) this[name] = new Int32Array(capacity);
  }
  // #endregion

  // #region pool-add
  add(x: number, y: number, vx: number, vy: number, radius = 3, kind = 0, hp = 1): number {
    if (this.count === this.capacity) return -1;
    const i = this.count++;
    this.x[i] = x; this.y[i] = y;
    this.vx[i] = vx; this.vy[i] = vy;
    this.radius[i] = radius; this.hp[i] = hp;
    this.kind[i] = kind; this.age[i] = 0; this.mark[i] = 0;
    return i;
  }
  // #endregion

  // #region pool-erase
  // 순서 대신 고정 비용을 선택한다. 시간 O(1), 추가 공간 O(1).
  erase(i: number): boolean {
    if (!Number.isInteger(i) || i < 0 || i >= this.count) return false;
    const last = --this.count;
    for (const name of fields) this[name][i] = this[name][last];
    return true;
  }
  // #endregion
}

// #region stage-validate
export type StageEvent = readonly [number, 'enemy' | 'boss', number];
// 로딩 시에만 검증하고 불변 값으로 복사한다. 시간 O(n), 저장 공간 O(n).
export function validateStage(data: unknown): readonly StageEvent[] {
  if (!Array.isArray(data) || data.length > 4096) throw new Error('잘못된 스테이지 배열');
  const result: StageEvent[] = [];
  let previous = -1;
  for (const event of data) {
    if (!event || typeof event !== 'object' || Array.isArray(event)) throw new Error('잘못된 이벤트');
    const e = event as Record<string, unknown>, frame = e.frame, kind = e.kind;
    if (typeof frame !== 'number' || !Number.isInteger(frame) || frame < 0 || frame < previous) throw new Error('잘못된 시간');
    if (kind !== 'enemy' && kind !== 'boss') throw new Error('잘못된 종류');
    const keys = Object.keys(e), expected = kind === 'enemy' ? ['frame', 'kind', 'pattern'] : ['frame', 'kind'];
    if (keys.length !== expected.length || !expected.every((key) => keys.includes(key))) throw new Error('잘못된 필드');
    const pattern = kind === 'enemy' ? e.pattern : 0;
    if (typeof pattern !== 'number' || !Number.isInteger(pattern) || pattern < 0 || pattern > 3) throw new Error('잘못된 패턴');
    result.push(Object.freeze([frame, kind, pattern] as const));
    previous = frame;
  }
  return Object.freeze(result);
}
// #endregion

export class Game {
  // #region state-init
  frame = 0;
  playerX = 240; playerY = 560;
  previousX = 240; previousY = 560;
  cooldown = 0;
  bullets = new Pool(4096);
  enemies = new Pool(128);
  score = 0; lives = 3; phase = 0;
  readonly seed: number;
  rng: Rng;
  invulnerable = 0;
  bossSpawned = false;
  phaseTime = 0;
  clearPending = false;
  constructor(seed = SEED, stage: unknown = []) {
    this.seed = seed >>> 0; this.rng = new Rng(this.seed);
    this.stage = validateStage(stage);
  }
  // #endregion

  // #region rewards-init
  items = new Pool(64);
  power = 1; bombs = 3; grazeCount = 0; killCount = 0;
  previousInput = 0;
  eventKind = new Int32Array(64);
  eventX = new Float64Array(64); eventY = new Float64Array(64);
  eventCount = 0;
  // #endregion

  // #region stage-init
  readonly stage: readonly StageEvent[];
  stageCursor = 0;
  stageBossPending = false;
  // #endregion

  // #region player-move
  movePlayer(bits: number): void {
    this.previousX = this.playerX; this.previousY = this.playerY;
    const dx = Number(Boolean(bits & RIGHT)) - Number(Boolean(bits & LEFT));
    const dy = Number(Boolean(bits & DOWN)) - Number(Boolean(bits & UP));
    const speed = bits & FOCUS ? FOCUS_SPEED : PLAYER_SPEED;
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length > 0) {
      this.playerX += dx * (speed / length);
      this.playerY += dy * (speed / length);
    }
    this.playerX = Math.max(12, Math.min(468, this.playerX));
    this.playerY = Math.max(12, Math.min(628, this.playerY));
  }
  // #endregion

  // #region player-shoot
  shoot(bits: number): void {
    if (this.cooldown > 0) this.cooldown--;
    if ((bits & SHOOT) && this.cooldown === 0) {
      for (let i = 0; i < this.power; i++) {
        const x = this.playerX + (i - (this.power - 1) / 2) * 8;
        if (this.bullets.add(x, this.playerY - 14, 0, -SHOT_SPEED) >= 0) this.emit(1, x, this.playerY - 14);
      }
      this.cooldown = SHOT_PERIOD;
    }
  }
  // #endregion

  // #region bullet-step
  // 역순 삭제로 이동 중복을 막는다. 시간 O(n), 추가 공간 O(1).
  moveBullets(): void {
    const p = this.bullets;
    for (let i = p.count - 1; i >= 0; i--) {
      p.x[i] += p.vx[i]; p.y[i] += p.vy[i]; p.age[i]++;
      if (p.x[i] < -32 || p.x[i] > WIDTH + 32 || p.y[i] < -32 || p.y[i] > HEIGHT + 32) p.erase(i);
    }
  }
  // #endregion

  // #region ring
  // 탄수 n에 대해 시간 O(n), 추가 공간 O(1).
  ring(x: number, y: number, count: number, speed: number, turn = 0): void {
    for (let i = 0; i < count; i++) {
      const angle = turn + i / count;
      this.bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, 4, 1);
    }
  }
  // #endregion

  // 역각 없이 방향 벡터를 회전한다. 시간 O(n), 추가 공간 O(1).
  // #region aimed-fan
  aimedFan(x: number, y: number, count: number, speed: number): void {
    // #region aim-vector
    const dx = this.playerX - x, dy = this.playerY - y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const ux = length > 0 ? dx / length : 0, uy = length > 0 ? dy / length : 1;
    // #endregion
    for (let i = 0; i < count; i++) {
      // #region fan-velocity
      const angle = (i - (count - 1) / 2) * .025;
      const c = dcos(angle), s = dsin(angle);
      const vx = (ux * c - uy * s) * speed, vy = (ux * s + uy * c) * speed;
      this.bullets.add(x, y, vx, vy, 4, 1);
      // #endregion
    }
  }
  // #endregion

  // #region spiral
  spiral(x: number, y: number, count: number, speed: number, tick: number): void {
    this.ring(x, y, count, speed, tick * .007);
  }
  // #endregion

  // 위상은 논리 시간에만 두고 인덱스는 부채꼴 간격으로 펼친다. 인덱스를 위상에 더하면
  // 한 번에 사인 한 주기를 모두 찍어 전체가 흔들리지 않고 대칭인 두 탄환이 겹친다. 시간 O(n), 추가 공간 O(1).
  // #region wave
  wave(x: number, y: number, count: number, speed: number, tick: number): void {
    for (let i = 0; i < count; i++) {
      const angle = .25 + dsin(tick / 180) * .12 + (i - (count - 1) / 2) * .025;
      this.bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, 4, 1);
    }
  }
  // #endregion

  // #region pattern-dispatch
  firePattern(x: number, y: number, mode: number, count = 8, speed = 2.5, tick = this.frame): void {
    if (mode === 0) this.ring(x, y, count, speed);
    else if (mode === 1) this.aimedFan(x, y, count, speed);
    else if (mode === 2) this.spiral(x, y, count, speed, tick);
    else if (mode === 3) this.wave(x, y, count, speed, tick);
    else throw new Error('패턴 번호는 0부터 3까지입니다');
  }
  // #endregion

  // #region boss-find
  // 교환 삭제로 인덱스가 바뀌므로 종류로 다시 찾는다. 시간 O(e), 추가 공간 O(1).
  findBoss(): number {
    for (let i = this.enemies.count - 1; i >= 0; i--) if (this.enemies.kind[i] === 1) return i;
    return -1;
  }
  // #endregion

  // #region boss-spawn
  spawnBoss(): number {
    if (this.bossSpawned) return -1;
    const index = this.enemies.add(240, 100, 0, 0, 28, 1, 180);
    if (index >= 0) { this.bossSpawned = true; this.phase = 1; this.phaseTime = 0; }
    return index;
  }
  // #endregion

  // #region clear-enemy-bullets
  // 탄환 순회가 진행 중이지 않을 때 호출한다. 시간 O(b), 추가 공간 O(1).
  clearEnemyBullets(): number {
    let removed = 0;
    for (let i = this.bullets.count - 1; i >= 0; i--) {
      if (this.bullets.kind[i] === 1) { this.bullets.erase(i); removed++; }
    }
    return removed;
  }
  // #endregion

  // #region boss-step
  updateBoss(i: number): void {
    const p = this.enemies;
    // #region boss-move
    const oldX = p.x[i];
    p.age[i]++;
    p.x[i] = 240 + 140 * dsin(p.age[i] / 240);
    p.vx[i] = p.x[i] - oldX;
    // #endregion
    // #region boss-transition
    this.phaseTime++;
    if (this.phase < 3 && (this.phaseTime >= 300 || p.hp[i] <= 180 - this.phase * 60)) {
      this.phase++; this.phaseTime = 0;
      this.emit(7, p.x[i], p.y[i]);
      this.clearEnemyBullets();
    }
    // #endregion
    // #region boss-fire
    const interval = this.phase === 1 ? 45 : this.phase === 2 ? 32 : 4;
    if (this.phaseTime % interval === 0) {
      const x = p.x[i], y = p.y[i] + 24;
      if (this.phase === 1) this.ring(x, y, 12, 2, this.frame * .001);
      else if (this.phase === 2) this.aimedFan(x, y, 7, 3);
      else {
        // 나선은 4스텝마다 세 팔을 이어 쏘고 파동은 그중 20스텝마다 겹쳐 쏜다.
        this.spiral(x, y, 3, 2.5, this.frame);
        if (this.phaseTime % 20 === 0) this.wave(x, y, 6, 3, this.frame);
      }
    }
    // #endregion
  }
  // #endregion

  // #region enemy-defeat
  defeatEnemy(i: number): void {
    if (this.enemies.kind[i] === 1) {
      this.score += 1000;
      this.phase = 4;
      this.clearPending = true;
      this.emit(8, this.enemies.x[i], this.enemies.y[i]);
    } else {
      this.score += 100; this.killCount++;
      this.emit(3, this.enemies.x[i], this.enemies.y[i]);
      if (this.killCount % 3 === 0) this.items.add(this.enemies.x[i], this.enemies.y[i], 0, 1.5, 6);
    }
    this.enemies.erase(i);
  }
  // #endregion

  // #region enemy-spawn
  spawnEnemy(pattern = Math.floor(this.frame / 90) % 4): number {
    const x = 32 + this.rng.next() % 416;
    const index = this.enemies.add(x, -16, 0, 1.2, 12, 0, 3);
    if (index >= 0) this.enemies.mark[index] = pattern;
    return index;
  }
  // #endregion

  // #region enemy-step
  moveEnemies(): void {
    const p = this.enemies;
    for (let i = p.count - 1; i >= 0; i--) {
      if (p.kind[i] === 1) { this.updateBoss(i); continue; }
      p.x[i] += p.vx[i]; p.y[i] += p.vy[i]; p.age[i]++;
      if (p.y[i] > HEIGHT + 32) { p.erase(i); continue; }
      // 나선은 링 전체를 가끔 쏘면 회전이 링 대칭에 상쇄되므로 두 팔을 6스텝마다 이어 쏜다.
      const stream = p.mark[i] === 2;
      if (p.age[i] % (stream ? 6 : 60) === 0) this.firePattern(p.x[i], p.y[i] + 12, p.mark[i], stream ? 2 : 8);
    }
  }
  // #endregion

  // #region player-hurt
  hurt(): boolean {
    if (this.invulnerable > 0 || this.lives <= 0) return false;
    this.emit(2, this.playerX, this.playerY);
    this.lives--;
    this.invulnerable = 120;
    this.playerX = 240; this.playerY = 560;
    this.previousX = this.playerX; this.previousY = this.playerY;
    return true;
  }
  // #endregion

  // #region player-bullet-hit
  // 총알 b개와 적 e개를 비교한다. 시간 O(b*e), 추가 공간 O(1).
  playerBulletHits(): void {
    const b = this.bullets, e = this.enemies;
    for (let bi = b.count - 1; bi >= 0; bi--) {
      if (b.kind[bi] !== 0) continue;
      for (let ei = e.count - 1; ei >= 0; ei--) {
        if (overlaps(b.x[bi], b.y[bi], b.radius[bi], e.x[ei], e.y[ei], e.radius[ei])) {
          e.hp[ei]--;
          b.erase(bi);
          if (e.hp[ei] <= 0) this.defeatEnemy(ei);
          break;
        }
      }
    }
  }
  // #endregion

  // #region enemy-bullet-hit
  enemyBulletHits(): void {
    const p = this.bullets;
    for (let i = p.count - 1; i >= 0; i--) {
      if (p.kind[i] === 1 && overlaps(this.playerX, this.playerY, PLAYER_RADIUS,
          p.x[i], p.y[i], p.radius[i]) && this.hurt()) p.erase(i);
    }
  }
  // #endregion

  // #region enemy-body-hit
  enemyBodyHits(): void {
    const p = this.enemies;
    for (let i = p.count - 1; i >= 0; i--) {
      if (overlaps(this.playerX, this.playerY, PLAYER_RADIUS, p.x[i], p.y[i], p.radius[i]) && this.hurt()) {
        if (p.kind[i] !== 1) p.erase(i);
      }
    }
  }
  // #endregion

  // #region event-emit
  // 알림 포화가 게임 계산을 막지 않는다. 시간 O(1), 추가 공간 O(1).
  emit(kind: number, x: number, y: number): boolean {
    if (this.eventCount === 64) return false;
    const i = this.eventCount++;
    this.eventKind[i] = kind; this.eventX[i] = x; this.eventY[i] = y;
    return true;
  }
  // #endregion

  // #region graze
  // 탄환 표식을 교환 삭제와 함께 이동한다. 시간 O(b), 추가 공간 O(1).
  graze(): void {
    if (this.invulnerable > 0 || this.lives <= 0) return;
    const p = this.bullets;
    for (let i = 0; i < p.count; i++) {
      if (p.kind[i] !== 1 || p.mark[i] !== 0) continue;
      const x = p.x[i], y = p.y[i], r = p.radius[i];
      if (overlaps(this.playerX, this.playerY, GRAZE_RADIUS, x, y, r) &&
          !overlaps(this.playerX, this.playerY, PLAYER_RADIUS, x, y, r)) {
        p.mark[i] = 1;
        this.grazeCount++; this.score += 10;
        this.emit(4, x, y);
      }
    }
  }
  // #endregion

  // #region bomb
  // 적탄 순회 전에 광역 피해를 확정한다. 시간 O(b+e), 추가 공간 O(1).
  bomb(bits: number): void {
    const pressed = (bits & BOMB) && !(this.previousInput & BOMB);
    this.previousInput = bits;
    if (!pressed || this.bombs <= 0 || this.lives <= 0) return;
    this.bombs--;
    this.score += this.clearEnemyBullets() * 5;
    this.invulnerable = Math.max(this.invulnerable, 180);
    this.emit(5, this.playerX, this.playerY);
    for (let i = this.enemies.count - 1; i >= 0; i--) {
      this.enemies.hp[i] -= 30;
      if (this.enemies.hp[i] <= 0) this.defeatEnemy(i);
    }
  }
  // #endregion

  // #region item-step
  // 역순으로 수집과 삭제를 처리한다. 시간 O(i), 추가 공간 O(1).
  moveItems(): void {
    const p = this.items;
    for (let i = p.count - 1; i >= 0; i--) {
      p.x[i] += p.vx[i]; p.y[i] += p.vy[i];
      if (p.y[i] > HEIGHT + 32) p.erase(i);
      else if (overlaps(this.playerX, this.playerY, 12, p.x[i], p.y[i], p.radius[i])) {
        this.power = Math.min(3, this.power + 1); this.score += 50;
        this.emit(6, p.x[i], p.y[i]); p.erase(i);
      }
    }
  }
  // #endregion

  // #region stage-step
  // 이벤트당 한 번만 방문한다. 전체 처리 시간 O(n), 추가 공간 O(1).
  runStage(): void {
    while (this.stageCursor < this.stage.length) {
      const [frame, kind, pattern] = this.stage[this.stageCursor];
      if (frame > this.frame) break;
      this.stageCursor++;
      if (kind === 'enemy') this.spawnEnemy(pattern);
      else this.stageBossPending = true;
    }
    if (this.stageBossPending) {
      this.spawnBoss();
      if (this.bossSpawned) this.stageBossPending = false;
    }
  }
  // #endregion

  // #region game-step
  step(bits: number): void {
    if (!Number.isInteger(bits) || bits < 0 || bits > 511) throw new Error('잘못된 입력 비트');
    this.eventCount = 0;
    if (this.invulnerable > 0) this.invulnerable--;
    this.movePlayer(bits);
    this.shoot(bits);
    this.runStage();
    this.bomb(bits);
    this.moveEnemies();
    this.moveBullets();
    this.playerBulletHits();
    // #region deferred-clear
    if (this.clearPending) { this.clearEnemyBullets(); this.clearPending = false; }
    // #endregion
    this.enemyBulletHits();
    this.enemyBodyHits();
    this.graze();
    this.moveItems();
    this.frame++;
  }
  // #endregion

  // #region snapshot
  // 양자화와 내림 순서를 포트에서 유지한다. 시간 O(b), 추가 공간 O(1).
  snapshot() {
    let checksum = 0;
    for (let i = 0; i < this.bullets.count; i++) {
      checksum = (checksum + Math.floor(this.bullets.x[i] * 16) * 31 + Math.floor(this.bullets.y[i] * 16)) >>> 0;
    }
    return { frame: this.frame, bullets: this.bullets.count, enemies: this.enemies.count,
      score: this.score, lives: this.lives, phase: this.phase, checksum };
  }
  // #endregion
}
