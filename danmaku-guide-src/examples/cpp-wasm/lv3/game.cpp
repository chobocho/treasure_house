#include "game.hpp"
// #region lv3-dsin
double dsin(double turn) {
  double t = turn - __builtin_floor(turn);
  if (t > .75) t -= 1;
  else if (t > .25) t = .5 - t;
  const double x = t * 6.283185307179586, z = x * x;
  double p = 1.0 / 6227020800;
  p = -1.0 / 39916800 + z * p;
  p = 1.0 / 362880 + z * p;
  p = -1.0 / 5040 + z * p;
  p = 1.0 / 120 + z * p;
  p = -1.0 / 6 + z * p;
  return x * (1 + z * p);
}
double dcos(double turn) { return dsin(turn + .25); }
// #endregion
// #region lv3-ring
void Game::ring(double x, double y, unsigned int count, double speed, double turn) {
  for (unsigned int i = 0; i < count; ++i) {
    const double angle = turn + static_cast<double>(i) / count;
    bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, 4, 1);
  }
}
// #endregion
// #region lv3-fan
void Game::aimedFan(double x, double y, unsigned int count, double speed) {
  const double dx = this->x - x, dy = this->y - y;
  const double length = __builtin_sqrt(dx * dx + dy * dy);
  const double ux = length > 0 ? dx / length : 0, uy = length > 0 ? dy / length : 1;
  for (unsigned int i = 0; i < count; ++i) {
    const double angle = (static_cast<double>(i) - (count - 1) / 2.0) * .025;
    const double c = dcos(angle), s = dsin(angle);
    const double vx = (ux * c - uy * s) * speed, vy = (ux * s + uy * c) * speed;
    bullets.add(x, y, vx, vy, 4, 1);
  }
}
// #endregion
// #region lv3-spiral-wave
void Game::spiral(double x, double y, unsigned int count, double speed, unsigned int tick) {
  ring(x, y, count, speed, tick * .007);
}
void Game::wave(double x, double y, unsigned int count, double speed, unsigned int tick) {
  for (unsigned int i = 0; i < count; ++i) {
    const double angle = .25 + dsin(tick / 180.0) * .12 + (static_cast<double>(i) - (static_cast<double>(count) - 1) / 2) * .025;
    bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, 4, 1);
  }
}
// #endregion
// #region lv3-dispatch
bool Game::firePattern(double x, double y, unsigned int mode, unsigned int count, double speed) {
  if (mode == 0) ring(x, y, count, speed);
  else if (mode == 1) aimedFan(x, y, count, speed);
  else if (mode == 2) spiral(x, y, count, speed, frame);
  else if (mode == 3) wave(x, y, count, speed, frame);
  else return false;
  return true;
}
// #endregion
// #region lv3-collision
bool overlaps(double ax, double ay, double ar, double bx, double by, double br) {
  const double dx = ax - bx, dy = ay - by, radius = ar + br;
  return dx * dx + dy * dy <= radius * radius;
}
// #endregion
// #region lv3-enemy-spawn
bool Game::spawnEnemy() {
  const double position = 32 + rng.next() % 416;
  if (!enemies.add(position, -16, 0, 1.2, 12, 0, 3)) return false;
  enemies.data[enemies.count - 1].mark = (frame / 90) % 4;
  return true;
}
// #endregion
// #region lv3-enemy-step
void Game::moveEnemies() {
  for (unsigned int n = enemies.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Body& e = enemies.data[i];
    e.x += e.vx; e.y += e.vy; ++e.age;
    if (e.y > 672) { enemies.erase(i); continue; }
    // 나선은 링 전체를 가끔 쏘면 회전이 링 대칭에 상쇄되므로 두 팔을 6스텝마다 이어 쏜다.
    const bool stream = e.mark == 2;
    if (e.age % (stream ? 6 : 60) == 0) firePattern(e.x, e.y + 12, e.mark, stream ? 2 : 8);
  }
}
// #endregion
// #region lv3-hurt
bool Game::hurt() {
  if (invulnerable > 0 || lives == 0) return false;
  --lives; invulnerable = 120;
  x = previousX = 240; y = previousY = 560;
  return true;
}
// #endregion
// #region lv3-player-hit
void Game::playerBulletHits() {
  for (unsigned int bn = bullets.count; bn > 0; --bn) {
    const unsigned int bi = bn - 1;
    const Body& b = bullets.data[bi];
    if (b.kind != 0) continue;
    for (unsigned int en = enemies.count; en > 0; --en) {
      const unsigned int ei = en - 1;
      Body& e = enemies.data[ei];
      if (overlaps(b.x, b.y, b.radius, e.x, e.y, e.radius)) {
        --e.hp;
        bullets.erase(bi);
        if (e.hp <= 0) { score += 100; enemies.erase(ei); }
        break;
      }
    }
  }
}
// #endregion
// #region lv3-enemy-hit
void Game::enemyBulletHits() {
  for (unsigned int n = bullets.count; n > 0; --n) {
    const unsigned int i = n - 1;
    const Body& b = bullets.data[i];
    if (b.kind == 1 && overlaps(x, y, 2.5, b.x, b.y, b.radius) && hurt()) bullets.erase(i);
  }
}
void Game::enemyBodyHits() {
  for (unsigned int n = enemies.count; n > 0; --n) {
    const unsigned int i = n - 1;
    const Body& e = enemies.data[i];
    if (overlaps(x, y, 2.5, e.x, e.y, e.radius) && hurt()) enemies.erase(i);
  }
}
// #endregion
// #region lv3-move
void Game::move(unsigned int bits) {
  previousX = x; previousY = y;
  const int dx = static_cast<int>(!!(bits & 2)) - static_cast<int>(!!(bits & 1));
  const int dy = static_cast<int>(!!(bits & 8)) - static_cast<int>(!!(bits & 4));
  const double speed = bits & 32 ? 1.6 : 4.0;
  const double length = __builtin_sqrt(static_cast<double>(dx * dx + dy * dy));
  if (length > 0) {
    x += dx * (speed / length);
    y += dy * (speed / length);
  }
  if (x < 12) x = 12;
  if (x > 468) x = 468;
  if (y < 12) y = 12;
  if (y > 628) y = 628;
}
// #endregion

// #region lv3-shoot
void Game::shoot(unsigned int bits) {
  if (cooldown > 0) --cooldown;
  if ((bits & 16) && cooldown == 0) {
    bullets.add(x, y - 14, 0, -8);
    cooldown = 8;
  }
}
// #endregion

// #region lv3-bullets
void Game::moveBullets() {
  for (unsigned int n = bullets.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Body& b = bullets.data[i];
    b.x += b.vx; b.y += b.vy; ++b.age;
    if (b.x < -32 || b.x > 512 || b.y < -32 || b.y > 672) bullets.erase(i);
  }
}
// #endregion

// #region lv3-step
bool Game::step(unsigned int bits) {
  if (bits > 511) return false;
  if (invulnerable > 0) --invulnerable;
  move(bits);
  shoot(bits);
  if (frame % 90 == 30) spawnEnemy();
  moveEnemies();
  moveBullets();
  playerBulletHits();
  enemyBulletHits();
  enemyBodyHits();
  ++frame;
  return true;
}
// #endregion

// #region lv3-checksum
unsigned int Game::checksum() const {
  unsigned int result = 0;
  for (unsigned int i = 0; i < bullets.count; ++i) {
    const auto qx = static_cast<long long>(__builtin_floor(bullets.data[i].x * 16));
    const auto qy = static_cast<long long>(__builtin_floor(bullets.data[i].y * 16));
    result += static_cast<unsigned int>(qx * 31 + qy);
  }
  return result;
}
// #endregion

#if defined(__wasm__)
#define DM_API(name) extern "C" __attribute__((export_name(#name), used))
#else
#define DM_API(name) extern "C"
#endif
static Game game;
// #region lv3-abi
DM_API(dm_abi_version) unsigned int dm_abi_version() { return 1; }
DM_API(dm_init) void dm_init(unsigned int seed) { game.init(seed); }
DM_API(dm_step) unsigned int dm_step(unsigned int bits) { return game.step(bits); }
DM_API(dm_frame) unsigned int dm_frame() { return game.frame; }
DM_API(dm_count) unsigned int dm_count() { return game.bullets.count; }
DM_API(dm_checksum) unsigned int dm_checksum() { return game.checksum(); }
DM_API(dm_player_x) double dm_player_x() { return game.x; }
DM_API(dm_player_y) double dm_player_y() { return game.y; }
DM_API(dm_enemies) unsigned int dm_enemies() { return game.enemies.count; }
DM_API(dm_score) unsigned int dm_score() { return game.score; }
DM_API(dm_lives) unsigned int dm_lives() { return game.lives; }
DM_API(dm_invulnerable) unsigned int dm_invulnerable() { return game.invulnerable; }
// #endregion

// #region lv3-render-buffer
alignas(8) static double renderPositions[4096 * 2];
DM_API(dm_positions) const double* dm_positions() {
  for (unsigned int i = 0; i < game.bullets.count; ++i) {
    renderPositions[i * 2] = game.bullets.data[i].x;
    renderPositions[i * 2 + 1] = game.bullets.data[i].y;
  }
  return renderPositions;
}
DM_API(dm_capacity) unsigned int dm_capacity() { return 4096; }
DM_API(dm_stride) unsigned int dm_stride() { return 16; }
// #endregion

// #region lv3-render-enemies
alignas(8) static double enemyPositions[128 * 2];
static unsigned int bulletKinds[4096];
DM_API(dm_enemy_positions) const double* dm_enemy_positions() {
  for (unsigned int i = 0; i < game.enemies.count; ++i) {
    enemyPositions[i * 2] = game.enemies.data[i].x;
    enemyPositions[i * 2 + 1] = game.enemies.data[i].y;
  }
  return enemyPositions;
}
DM_API(dm_kinds) const unsigned int* dm_kinds() {
  for (unsigned int i = 0; i < game.bullets.count; ++i) bulletKinds[i] = game.bullets.data[i].kind;
  return bulletKinds;
}
// #endregion
