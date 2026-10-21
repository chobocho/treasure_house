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
  constructor(seed = SEED) { this.seed = seed >>> 0; this.rng = new Rng(this.seed); }
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
      this.bullets.add(this.playerX, this.playerY - 14, 0, -SHOT_SPEED);
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

  // #region enemy-spawn
  spawnEnemy(): number {
    const x = 32 + this.rng.next() % 416;
    return this.enemies.add(x, -16, 0, 1.2, 12, 0, 3);
  }
  // #endregion

  // #region enemy-step
  moveEnemies(): void {
    const p = this.enemies;
    for (let i = p.count - 1; i >= 0; i--) {
      p.x[i] += p.vx[i]; p.y[i] += p.vy[i]; p.age[i]++;
      if (p.y[i] > HEIGHT + 32) { p.erase(i); continue; }
      if (p.age[i] % 60 === 0) this.bullets.add(p.x[i], p.y[i] + 12, 0, 2.5, 4, 1);
    }
  }
  // #endregion

  // #region player-hurt
  hurt(): boolean {
    if (this.invulnerable > 0 || this.lives <= 0) return false;
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
          if (e.hp[ei] <= 0) { this.score += 100; e.erase(ei); }
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
      if (overlaps(this.playerX, this.playerY, PLAYER_RADIUS, p.x[i], p.y[i], p.radius[i]) && this.hurt()) p.erase(i);
    }
  }
  // #endregion

  // #region game-step
  step(bits: number): void {
    if (!Number.isInteger(bits) || bits < 0 || bits > 511) throw new Error('잘못된 입력 비트');
    if (this.invulnerable > 0) this.invulnerable--;
    this.movePlayer(bits);
    this.shoot(bits);
    if (this.frame % 90 === 30) this.spawnEnemy();
    this.moveEnemies();
    this.moveBullets();
    this.playerBulletHits();
    this.enemyBulletHits();
    this.enemyBodyHits();
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
