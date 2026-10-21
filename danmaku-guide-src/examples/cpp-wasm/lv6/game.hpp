#pragma once
static_assert(sizeof(unsigned int) == 4);
// #region lv6-rng
struct Rng {
  unsigned int state = 0;
  unsigned int next() {
    unsigned int x = state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return state = x;
  }
};
// #endregion
// #region lv6-pool
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
struct Event { double x, y; unsigned int kind; };
struct StageEvent { double frame; unsigned int kind, pattern; };
// #region lv6-state
struct Game {
  unsigned int frame = 0, cooldown = 0, seed = 0;
  unsigned int score = 0, lives = 3, phase = 0, invulnerable = 0;
  double x = 240, y = 560, previousX = 240, previousY = 560;
  Pool<4096> bullets;
  Pool<128> enemies;
  Rng rng;
  bool bossSpawned = false, clearPending = false;
  unsigned int phaseTime = 0;
  // #region lv6-stage-state
  StageEvent stage[4096];
  unsigned int stageCount = 0, stageCursor = 0;
  bool stageBossPending = false;
  bool addStage(double frame, unsigned int kind, unsigned int pattern);
  void runStage();
  // #endregion
  // #region lv6-rewards
  Pool<64> items;
  unsigned int power = 1, bombs = 3, grazeCount = 0, killCount = 0, previousInput = 0;
  Event events[64];
  unsigned int eventCount = 0;
  bool emit(unsigned int kind, double x, double y);
  void graze();
  void bomb(unsigned int bits);
  void moveItems();
  // #endregion
  void init(unsigned int value) {
    frame = cooldown = score = phase = invulnerable = 0;
    lives = 3; seed = rng.state = value;
    x = previousX = 240; y = previousY = 560;
    bullets.count = enemies.count = 0;
    bossSpawned = clearPending = false; phaseTime = 0;
    items.count = eventCount = grazeCount = killCount = previousInput = 0;
    power = 1; bombs = 3;
    stageCount = stageCursor = 0; stageBossPending = false;
  }
  void move(unsigned int bits);
  void shoot(unsigned int bits);
  void moveBullets();
  bool spawnEnemy(unsigned int pattern = 4);
  void ring(double x, double y, unsigned int count, double speed, double turn = 0);
  void aimedFan(double x, double y, unsigned int count, double speed);
  void spiral(double x, double y, unsigned int count, double speed, unsigned int tick);
  void wave(double x, double y, unsigned int count, double speed, unsigned int tick);
  bool firePattern(double x, double y, unsigned int mode, unsigned int count = 8, double speed = 2.5);
  void moveEnemies();
  int findBoss() const;
  bool spawnBoss();
  unsigned int clearEnemyBullets();
  void updateBoss(unsigned int i);
  void defeatEnemy(unsigned int i);
  bool hurt();
  void playerBulletHits();
  void enemyBulletHits();
  void enemyBodyHits();
  bool step(unsigned int bits);
  unsigned int checksum() const;
};
bool overlaps(double ax, double ay, double ar, double bx, double by, double br);
double dsin(double turn);
double dcos(double turn);
// #endregion
