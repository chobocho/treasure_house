#pragma once
// #region lv1-pool
struct Bullet {
  double x, y, vx, vy;
  unsigned int age;
};
struct Pool {
  static constexpr unsigned int CAPACITY = 4096;
  Bullet data[CAPACITY];
  unsigned int count = 0;
  bool add(double x, double y, double vx, double vy) {
    if (count == CAPACITY) return false;
    data[count++] = {x, y, vx, vy, 0};
    return true;
  }
  bool erase(unsigned int i) {
    if (i >= count || i >= CAPACITY || count > CAPACITY) return false;
    const Bullet& last = data[--count];
    data[i].x = last.x; data[i].y = last.y;
    data[i].vx = last.vx; data[i].vy = last.vy;
    data[i].age = last.age;
    return true;
  }
};
// #endregion

// #region lv1-state
struct Game {
  unsigned int frame = 0, cooldown = 0, seed = 0;
  double x = 240, y = 560, previousX = 240, previousY = 560;
  Pool bullets;
  void init(unsigned int value) {
    frame = 0; cooldown = 0; seed = value;
    x = previousX = 240; y = previousY = 560;
    bullets.count = 0;
  }
  void move(unsigned int bits);
  void shoot(unsigned int bits);
  void moveBullets();
  bool step(unsigned int bits);
  unsigned int checksum() const;
};
// #endregion
