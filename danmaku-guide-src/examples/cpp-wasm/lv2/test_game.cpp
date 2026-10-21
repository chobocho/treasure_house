#include "game.hpp"
#include <cassert>
#include <iostream>
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
  assert(game.bullets.count == 1 && game.bullets.data[0].kind == 1);
  assert(game.bullets.data[0].y == 13.2);
  game.init(1);
  assert(game.lives == 3 && game.invulnerable == 0 && game.score == 0);
}
