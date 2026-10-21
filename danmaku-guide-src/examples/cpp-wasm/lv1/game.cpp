#include "game.hpp"
// #region lv1-move
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

// #region lv1-shoot
void Game::shoot(unsigned int bits) {
  if (cooldown > 0) --cooldown;
  if ((bits & 16) && cooldown == 0) {
    bullets.add(x, y - 14, 0, -8);
    cooldown = 8;
  }
}
// #endregion

// #region lv1-bullets
void Game::moveBullets() {
  for (unsigned int n = bullets.count; n > 0; --n) {
    const unsigned int i = n - 1;
    Bullet& b = bullets.data[i];
    b.x += b.vx; b.y += b.vy; ++b.age;
    if (b.x < -32 || b.x > 512 || b.y < -32 || b.y > 672) bullets.erase(i);
  }
}
// #endregion

// #region lv1-step
bool Game::step(unsigned int bits) {
  if (bits > 511) return false;
  move(bits);
  shoot(bits);
  moveBullets();
  ++frame;
  return true;
}
// #endregion

// #region lv1-checksum
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
// #region lv1-abi
DM_API(dm_abi_version) unsigned int dm_abi_version() { return 1; }
DM_API(dm_init) void dm_init(unsigned int seed) { game.init(seed); }
DM_API(dm_step) unsigned int dm_step(unsigned int bits) { return game.step(bits); }
DM_API(dm_frame) unsigned int dm_frame() { return game.frame; }
DM_API(dm_count) unsigned int dm_count() { return game.bullets.count; }
DM_API(dm_checksum) unsigned int dm_checksum() { return game.checksum(); }
DM_API(dm_player_x) double dm_player_x() { return game.x; }
DM_API(dm_player_y) double dm_player_y() { return game.y; }
// #endregion

// #region lv1-render-buffer
alignas(8) static double renderPositions[Pool::CAPACITY * 2];
DM_API(dm_positions) const double* dm_positions() {
  for (unsigned int i = 0; i < game.bullets.count; ++i) {
    renderPositions[i * 2] = game.bullets.data[i].x;
    renderPositions[i * 2 + 1] = game.bullets.data[i].y;
  }
  return renderPositions;
}
DM_API(dm_capacity) unsigned int dm_capacity() { return Pool::CAPACITY; }
DM_API(dm_stride) unsigned int dm_stride() { return 16; }
// #endregion
