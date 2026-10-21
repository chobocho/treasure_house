#include "game.hpp"
// #region lv6-stage-add
bool Game::addStage(double at, unsigned int kind, unsigned int pattern) {
  if (stageCount == 4096 || !__builtin_isfinite(at) || at < 0 || __builtin_floor(at) != at ||
      kind > 1 || pattern > 3 || (kind == 1 && pattern != 0)) return false;
  if (stageCount > 0 && at < stage[stageCount - 1].frame) return false;
  stage[stageCount++] = {at, kind, pattern};
  return true;
}
// #endregion
// #region lv6-stage-step
void Game::runStage() {
  while (stageCursor < stageCount) {
    const StageEvent& event = stage[stageCursor];
    if (event.frame > frame) break;
    ++stageCursor;
    if (event.kind == 0) spawnEnemy(event.pattern);
    else stageBossPending = true;
  }
  if (stageBossPending) {
    spawnBoss();
    if (bossSpawned) stageBossPending = false;
  }
}
// #endregion
// #region lv6-emit
bool Game::emit(unsigned int kind, double x, double y) {
  if (eventCount == 64) return false;
  events[eventCount++] = {x, y, kind};
  return true;
}
// #endregion
// #region lv6-graze
void Game::graze() {
  if (invulnerable > 0 || lives == 0) return;
  for (unsigned int i = 0; i < bullets.count; ++i) {
    Body& b = bullets.data[i];
    if (b.kind != 1 || b.mark != 0) continue;
    if (overlaps(x, y, 16, b.x, b.y, b.radius) && !overlaps(x, y, 2.5, b.x, b.y, b.radius)) {
      b.mark = 1; ++grazeCount; score += 10;
      emit(4, b.x, b.y);
    }
  }
}
// #endregion
// #region lv6-bomb
void Game::bomb(unsigned int bits) {
  const bool pressed = (bits & 64) && !(previousInput & 64);
  previousInput = bits;
  if (!pressed || bombs == 0 || lives == 0) return;
  --bombs;
  score += clearEnemyBullets() * 5;
  if (invulnerable < 180) invulnerable = 180;
  emit(5, x, y);
  for (unsigned int n = enemies.count; n > 0; --n) {
    const unsigned int i = n - 1;
    enemies.data[i].hp -= 30;
    if (enemies.data[i].hp <= 0) defeatEnemy(i);
  }
}
// #endregion
// #region lv6-items
void Game::moveItems() {
  for (unsigned int n = items.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Body& item = items.data[i];
    item.x += item.vx; item.y += item.vy;
    if (item.y > 672) items.erase(i);
    else if (overlaps(x, y, 12, item.x, item.y, item.radius)) {
      if (power < 3) ++power;
      score += 50; emit(6, item.x, item.y); items.erase(i);
    }
  }
}
// #endregion
// #region lv6-boss-spawn
int Game::findBoss() const {
  for (unsigned int n = enemies.count; n > 0; --n) {
    if (enemies.data[n - 1].kind == 1) return static_cast<int>(n - 1);
  }
  return -1;
}
bool Game::spawnBoss() {
  if (bossSpawned) return false;
  if (!enemies.add(240, 100, 0, 0, 28, 1, 180)) return false;
  bossSpawned = true; phase = 1; phaseTime = 0;
  return true;
}
// #endregion
// #region lv6-clear
unsigned int Game::clearEnemyBullets() {
  unsigned int removed = 0;
  for (unsigned int n = bullets.count; n > 0; --n) {
    if (bullets.data[n - 1].kind == 1) { bullets.erase(n - 1); ++removed; }
  }
  return removed;
}
// #endregion
void Game::updateBoss(unsigned int i) {
  Body& boss = enemies.data[i];
  // #region lv6-boss-move
  const double oldX = boss.x;
  ++boss.age;
  boss.x = 240 + 140 * dsin(boss.age / 240.0);
  boss.vx = boss.x - oldX;
  // #endregion
  // #region lv6-transition
  ++phaseTime;
  if (phase < 3 && (phaseTime >= 300 || boss.hp <= 180.0 - phase * 60)) {
    ++phase; phaseTime = 0;
    emit(7, boss.x, boss.y);
    clearEnemyBullets();
  }
  // #endregion
  // #region lv6-boss-fire
  const unsigned int interval = phase == 1 ? 45 : phase == 2 ? 32 : 4;
  if (phaseTime % interval == 0) {
    const double x = boss.x, y = boss.y + 24;
    if (phase == 1) ring(x, y, 12, 2, frame * .001);
    else if (phase == 2) aimedFan(x, y, 7, 3);
    else {
      // 나선은 4스텝마다 세 팔을 이어 쏘고 파동은 그중 20스텝마다 겹쳐 쏜다.
      spiral(x, y, 3, 2.5, frame);
      if (phaseTime % 20 == 0) wave(x, y, 6, 3, frame);
    }
  }
  // #endregion
}
// #region lv6-defeat
void Game::defeatEnemy(unsigned int i) {
  if (enemies.data[i].kind == 1) {
    score += 1000; phase = 4; clearPending = true;
    emit(8, enemies.data[i].x, enemies.data[i].y);
  } else {
    score += 100; ++killCount;
    emit(3, enemies.data[i].x, enemies.data[i].y);
    if (killCount % 3 == 0) items.add(enemies.data[i].x, enemies.data[i].y, 0, 1.5, 6);
  }
  enemies.erase(i);
}
// #endregion
// #region lv6-dsin
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
// #region lv6-ring
void Game::ring(double x, double y, unsigned int count, double speed, double turn) {
  for (unsigned int i = 0; i < count; ++i) {
    const double angle = turn + static_cast<double>(i) / count;
    bullets.add(x, y, dcos(angle) * speed, dsin(angle) * speed, 4, 1);
  }
}
// #endregion
// #region lv6-fan
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
// #region lv6-spiral-wave
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
// #region lv6-dispatch
bool Game::firePattern(double x, double y, unsigned int mode, unsigned int count, double speed) {
  if (mode == 0) ring(x, y, count, speed);
  else if (mode == 1) aimedFan(x, y, count, speed);
  else if (mode == 2) spiral(x, y, count, speed, frame);
  else if (mode == 3) wave(x, y, count, speed, frame);
  else return false;
  return true;
}
// #endregion
// #region lv6-collision
bool overlaps(double ax, double ay, double ar, double bx, double by, double br) {
  const double dx = ax - bx, dy = ay - by, radius = ar + br;
  return dx * dx + dy * dy <= radius * radius;
}
// #endregion
// #region lv6-enemy-spawn
bool Game::spawnEnemy(unsigned int pattern) {
  const double position = 32 + rng.next() % 416;
  if (!enemies.add(position, -16, 0, 1.2, 12, 0, 3)) return false;
  enemies.data[enemies.count - 1].mark = pattern == 4 ? (frame / 90) % 4 : pattern;
  return true;
}
// #endregion
// #region lv6-enemy-step
void Game::moveEnemies() {
  for (unsigned int n = enemies.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Body& e = enemies.data[i];
    if (e.kind == 1) { updateBoss(i); continue; }
    e.x += e.vx; e.y += e.vy; ++e.age;
    if (e.y > 672) { enemies.erase(i); continue; }
    // 나선은 링 전체를 가끔 쏘면 회전이 링 대칭에 상쇄되므로 두 팔을 6스텝마다 이어 쏜다.
    const bool stream = e.mark == 2;
    if (e.age % (stream ? 6 : 60) == 0) firePattern(e.x, e.y + 12, e.mark, stream ? 2 : 8);
  }
}
// #endregion
// #region lv6-hurt
bool Game::hurt() {
  if (invulnerable > 0 || lives == 0) return false;
  emit(2, x, y);
  --lives; invulnerable = 120;
  x = previousX = 240; y = previousY = 560;
  return true;
}
// #endregion
// #region lv6-player-hit
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
        if (e.hp <= 0) defeatEnemy(ei);
        break;
      }
    }
  }
}
// #endregion
// #region lv6-enemy-hit
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
    if (overlaps(x, y, 2.5, e.x, e.y, e.radius) && hurt()) {
      if (e.kind != 1) enemies.erase(i);
    }
  }
}
// #endregion
// #region lv6-move
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

// #region lv6-shoot
void Game::shoot(unsigned int bits) {
  if (cooldown > 0) --cooldown;
  if ((bits & 16) && cooldown == 0) {
    for (unsigned int i = 0; i < power; ++i) {
      const double shotX = x + (static_cast<double>(i) - (power - 1) / 2.0) * 8;
      if (bullets.add(shotX, y - 14, 0, -8)) emit(1, shotX, y - 14);
    }
    cooldown = 8;
  }
}
// #endregion

// #region lv6-bullets
void Game::moveBullets() {
  for (unsigned int n = bullets.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Body& b = bullets.data[i];
    b.x += b.vx; b.y += b.vy; ++b.age;
    if (b.x < -32 || b.x > 512 || b.y < -32 || b.y > 672) bullets.erase(i);
  }
}
// #endregion

// #region lv6-step
bool Game::step(unsigned int bits) {
  if (bits > 511) return false;
  eventCount = 0;
  if (invulnerable > 0) --invulnerable;
  move(bits);
  shoot(bits);
  runStage();
  bomb(bits);
  moveEnemies();
  moveBullets();
  playerBulletHits();
  if (clearPending) { clearEnemyBullets(); clearPending = false; }
  enemyBulletHits();
  enemyBodyHits();
  graze();
  moveItems();
  ++frame;
  return true;
}
// #endregion

// #region lv6-checksum
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
// #region lv6-abi
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
DM_API(dm_phase) unsigned int dm_phase() { return game.phase; }
// #endregion
// #region lv6-stage-abi
DM_API(dm_stage_add) unsigned int dm_stage_add(double frame, unsigned int kind, unsigned int pattern) {
  return game.addStage(frame, kind, pattern);
}
// #endregion
// #region lv6-reward-abi
DM_API(dm_power) unsigned int dm_power() { return game.power; }
DM_API(dm_bombs) unsigned int dm_bombs() { return game.bombs; }
DM_API(dm_graze) unsigned int dm_graze() { return game.grazeCount; }
DM_API(dm_items) unsigned int dm_items() { return game.items.count; }
DM_API(dm_event_count) unsigned int dm_event_count() { return game.eventCount; }
DM_API(dm_events) const Event* dm_events() { return game.events; }
DM_API(dm_event_stride) unsigned int dm_event_stride() { return sizeof(Event); }
// #endregion

// #region lv6-boss-hud
DM_API(dm_boss_hp) double dm_boss_hp() {
  const int index = game.findBoss();
  return index >= 0 ? game.enemies.data[index].hp : 0;
}
DM_API(dm_boss_x) double dm_boss_x() {
  const int index = game.findBoss();
  return index >= 0 ? game.enemies.data[index].x : -100;
}
// #endregion

// #region lv6-render-buffer
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

// #region lv6-render-enemies
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
// #region lv6-render-items
alignas(8) static double itemPositions[64 * 2];
DM_API(dm_item_positions) const double* dm_item_positions() {
  for (unsigned int i = 0; i < game.items.count; ++i) {
    itemPositions[i * 2] = game.items.data[i].x;
    itemPositions[i * 2 + 1] = game.items.data[i].y;
  }
  return itemPositions;
}
// #endregion
