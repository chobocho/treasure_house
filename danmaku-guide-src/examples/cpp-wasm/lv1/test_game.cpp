#include "game.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
static Game game;
int main(int argc, char**) {
  if (argc > 1) {
    unsigned int bits;
    game.init(49734321);
    while (std::cin >> bits) {
      if (!game.step(bits)) return 2;
      if (game.frame == 60 || game.frame == 600 || game.frame == 1800) {
        std::cout << game.frame << ' ' << game.bullets.count << ' ' << game.checksum() << '\n';
      }
    }
    return game.frame == 1800 ? 0 : 3;
  }
  game.init(49734321);
  assert(!game.step(512) && game.frame == 0);
  game.step(1 | 2 | 4 | 8);
  assert(game.x == 240 && game.y == 560);
  game.init(1); game.step(2 | 4);
  assert(std::abs(game.x - 240 - 4 / std::sqrt(2.0)) < 1e-12);
  game.init(1); game.step(2 | 32);
  assert(game.x == 241.6);
  for (int i = 0; i < 1000; ++i) game.step(2 | 8);
  assert(game.x == 468 && game.y == 628);
  game.init(1); game.step(16);
  assert(game.bullets.count == 1 && game.bullets.data[0].y == 538);
  for (int i = 0; i < 7; ++i) game.step(16);
  assert(game.bullets.count == 1);
  game.step(16); assert(game.bullets.count == 2);
  game.init(1);
  for (unsigned int i = 0; i < Pool::CAPACITY; ++i) assert(game.bullets.add(i, 0, 0, 0));
  assert(!game.bullets.add(0, 0, 0, 0));
  game.bullets.data[Pool::CAPACITY - 1].age = 77;
  assert(game.bullets.erase(0) && game.bullets.data[0].age == 77);
  assert(!game.bullets.erase(Pool::CAPACITY));
  game.init(1);
  game.bullets.add(0, -32, 0, 0);
  game.bullets.add(10, -33, 0, 0);
  game.bullets.add(20, 0, 0, -1);
  game.moveBullets();
  assert(game.bullets.count == 2 && game.bullets.data[1].y == -1);
  game.init(1); game.bullets.add(-0.01, -0.01, 0, 0);
  assert(game.checksum() == 4294967264u);
  game.init(1); assert(game.bullets.count == 0 && game.frame == 0);
}
