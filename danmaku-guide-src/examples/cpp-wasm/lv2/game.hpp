#pragma once
static_assert(sizeof(unsigned int) == 4);
// #region lv2-rng
struct Rng {
  unsigned int state = 0;
  unsigned int next() {
    unsigned int x = state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return state = x;
  }
};
// #endregion
// #region lv2-pool
struct Body {
  double x, y, vx, vy, radius, hp;
  unsigned int kind, age, mark;
};
template<unsigned int N> struct Pool {
  static constexpr unsigned int CAPACITY = N;
  Body data[N];
  unsigned int count = 0;
  bool add(double x, double y, double vx, double vy,
           double radius = 3, unsigned int kind = 0, double hp = 1) {
    if (count >= N) return false;
    data[count++] = {x, y, vx, vy, radius, hp, kind, 0, 0};
    return true;
  }
  bool erase(unsigned int i) {
    if (i >= count || i >= N || count > N) return false;
    const Body& last = data[--count];
    data[i].x = last.x; data[i].y = last.y;
    data[i].vx = last.vx; data[i].vy = last.vy;
    data[i].radius = last.radius; data[i].hp = last.hp;
    data[i].kind = last.kind; data[i].age = last.age; data[i].mark = last.mark;
    return true;
  }
};
// #endregion
// #region lv2-state
struct Game {
  unsigned int frame = 0, cooldown = 0, seed = 0;
  unsigned int score = 0, lives = 3, phase = 0, invulnerable = 0;
  double x = 240, y = 560, previousX = 240, previousY = 560;
  Pool<4096> bullets;
  Pool<128> enemies;
  Rng rng;
  void init(unsigned int value) {
    frame = cooldown = score = phase = invulnerable = 0;
    lives = 3; seed = rng.state = value;
    x = previousX = 240; y = previousY = 560;
    bullets.count = enemies.count = 0;
  }
  void move(unsigned int bits);
  void shoot(unsigned int bits);
  void moveBullets();
  bool spawnEnemy();
  void moveEnemies();
  bool hurt();
  void playerBulletHits();
  void enemyBulletHits();
  void enemyBodyHits();
  bool step(unsigned int bits);
  unsigned int checksum() const;
};
bool overlaps(double ax, double ay, double ar, double bx, double by, double br);
// #endregion
