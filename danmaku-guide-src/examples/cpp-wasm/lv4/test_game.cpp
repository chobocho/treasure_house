#include "game.hpp"
#include <cassert>
#include <iostream>
#include <cmath>
static Game game;
int main(int argc, char**) {
  game.init(49734321);
  if (argc > 1) {
    unsigned int bits;
    while (std::cin >> bits) {
      if (!game.step(bits)) return 2;
      if (game.frame == 60 || game.frame == 600 || game.frame == 1800) {
        std::cout << game.frame << ' ' << game.bullets.count << ' ' << game.enemies.count
          << ' ' << game.score << ' ' << game.lives << ' ' << game.phase << ' ' << game.checksum() << '\n';
      }
    }
    return game.frame == 1800 ? 0 : 3;
  }
  assert(overlaps(0, 0, 2, 5, 0, 3));
  assert(!overlaps(0, 0, 2, 5.01, 0, 3));
  assert(overlaps(-2, -2, 1, -2, -2, 1));
  assert(!game.step(512) && game.frame == 0);
  Rng zero; assert(zero.next() == 0);
  Rng expected; expected.state = game.seed;
  const double expectedX = 32 + expected.next() % 416;
  assert(game.spawnEnemy() && game.enemies.data[0].x == expectedX);
  game.init(1);
  for (unsigned int i = 0; i < 128; ++i) game.spawnEnemy();
  const unsigned int state = game.rng.state;
  assert(!game.spawnEnemy() && game.rng.state != state);
  game.init(1);
  game.enemies.add(100, 100, 0, 0, 12, 0, 1);
  game.bullets.add(100, 100, 0, 0);
  game.bullets.add(100, 100, 0, 0);
  game.playerBulletHits();
  assert(game.score == 100 && game.enemies.count == 0 && game.bullets.count == 1);
  game.init(1);
  game.bullets.add(240, 560, 0, 0, 4, 1);
  game.bullets.add(240, 560, 0, 0, 4, 1);
  game.enemyBulletHits();
  assert(game.lives == 2 && game.invulnerable == 120 && game.bullets.count == 1);
  game.enemyBulletHits(); assert(game.lives == 2);
  game.invulnerable = 1; game.step(0);
  assert(game.lives == 1 && game.invulnerable == 120);
  game.invulnerable = 0; game.lives = 0;
  assert(!game.hurt() && game.lives == 0);
  game.init(1);
  game.enemies.add(240, 560, 0, 0, 12);
  game.enemyBodyHits();
  assert(game.lives == 2 && game.enemies.count == 0);
  game.init(1);
  game.bullets.add(240, 560, 0, 0, 4, 0);
  game.enemyBulletHits(); assert(game.lives == 3);
  game.enemies.add(240, 560, 0, 0, 12, 0, 3);
  game.bullets.data[0].kind = 1;
  game.playerBulletHits(); assert(game.enemies.data[0].hp == 3);
  game.init(1);
  game.enemies.add(100, 0, 0, 1.2, 12, 0, 3);
  game.enemies.data[0].age = 59; game.moveEnemies();
  assert(game.bullets.count == 8 && game.bullets.data[0].kind == 1);
  assert(game.bullets.data[0].y == 13.2);
  game.init(1);
  assert(game.lives == 3 && game.invulnerable == 0 && game.score == 0);
  assert(std::abs(dsin(.25) - 1) < 1e-8);
  assert(std::abs(dsin(-.25) + 1) < 1e-8);
  assert(std::abs(dsin(1.25) - dsin(.25)) < 1e-15);
  assert(std::abs(dcos(0) - dsin(.25)) < 1e-15);
  game.ring(100, 100, 4, 2);
  assert(game.bullets.count == 4);
  assert(std::abs(game.bullets.data[0].vx - 2) < 1e-8);
  assert(game.bullets.data[0].vy == 0);
  assert(std::abs(game.bullets.data[1].vy - 2) < 1e-8);
  game.init(1); game.aimedFan(240, 560, 3, 2);
  assert(std::abs(game.bullets.data[1].vx) < 1e-15);
  assert(std::abs(game.bullets.data[1].vy - 2) < 1e-8);
  for (unsigned int mode = 0; mode < 4; ++mode) {
    game.init(1); game.frame = 120;
    assert(game.firePattern(100, 100, mode, 8, 2.5));
    assert(game.bullets.count == 8);
    for (unsigned int i = 0; i < 8; ++i) {
      const auto& b = game.bullets.data[i];
      assert(std::isfinite(b.vx) && std::isfinite(b.vy));
      assert(std::abs(std::sqrt(b.vx * b.vx + b.vy * b.vy) - 2.5) < 1e-7);
    }
  }
  game.init(1); assert(!game.firePattern(0, 0, 4));
  game.ring(0, 0, 0, 1); assert(game.bullets.count == 0);
  for (unsigned int i = 0; i < 4095; ++i) game.bullets.add(0, 0, 0, 0);
  game.ring(100, 100, 8, 2); assert(game.bullets.count == 4096);
  game.init(1); game.frame = 210; game.spawnEnemy();
  assert(game.enemies.data[0].mark == 2);
  game.init(1);
  for (unsigned int i = 0; i < 128; ++i) game.enemies.add(0, 0, 0, 0);
  assert(!game.spawnBoss() && !game.bossSpawned);
  game.enemies.erase(0); assert(game.spawnBoss());
  assert(!game.spawnBoss() && game.phase == 1);
  const int boss = game.findBoss(); assert(boss >= 0);
  game.enemies.erase(0); assert(game.findBoss() == 0);
  game.init(1); game.spawnBoss();
  game.bullets.add(0, 0, 0, 0, 4, 1);
  game.bullets.add(0, 0, 0, 0);
  game.phaseTime = 299; game.updateBoss(0);
  assert(game.phase == 2 && game.phaseTime == 0);
  assert(game.bullets.count == 8); // 아군탄1 + 진입 조준탄7
  game.enemies.data[0].hp = 1; game.updateBoss(0);
  assert(game.phase == 3 && game.phaseTime == 0);
  assert(game.bullets.count == 10); // 아군탄1 + 나선3 + 파동6
  game.phaseTime = 300; game.updateBoss(0); assert(game.phase == 3);
  game.init(1); game.spawnBoss(); game.enemies.data[0].hp = 1;
  game.updateBoss(0); assert(game.phase == 2); // 한 호출에서 한 단계
  game.init(1); game.spawnBoss();
  game.x = 240; game.y = 100; game.enemyBodyHits();
  assert(game.lives == 2 && game.findBoss() == 0);
  game.init(1); game.spawnBoss(); game.enemies.data[0].hp = 1;
  game.bullets.add(240, 100, 0, 0);
  game.bullets.add(240, 560, 0, 0, 4, 1);
  game.playerBulletHits();
  assert(game.phase == 4 && game.score == 1000 && game.clearPending);
  assert(game.bullets.count == 1 && game.findBoss() == -1);
  assert(game.clearEnemyBullets() == 1 && game.bullets.count == 0);
  game.init(1); assert(!game.bossSpawned && !game.clearPending && game.phaseTime == 0);
}
