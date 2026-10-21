#include "game.hpp"
#include <cassert>
#include <iostream>
#include <cmath>
static Game game;
int main(int argc, char**) {
  game.init(49734321);
  if (argc > 1) {
    unsigned int count, kind, pattern;
    double at;
    if (!(std::cin >> count) || count > 4096) return 4;
    for (unsigned int i = 0; i < count; ++i) {
      if (!(std::cin >> at >> kind >> pattern) || !game.addStage(at, kind, pattern)) return 4;
    }
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
  game.init(1); game.frame = game.time = 210; game.spawnEnemy();
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
  game.bullets.add(250, 560, 0, 0, 4, 1);
  game.graze(); game.graze();
  assert(game.grazeCount == 1 && game.score == 10 && game.bullets.data[0].mark == 1);
  game.init(1); game.bullets.add(240, 560, 0, 0, 4, 1); game.graze();
  assert(game.grazeCount == 0);
  game.init(1); game.invulnerable = 1;
  game.bullets.add(250, 560, 0, 0, 4, 1); game.graze(); assert(game.grazeCount == 0);
  game.init(1);
  for (unsigned int i = 0; i < 64; ++i) assert(game.emit(1, 0, 0));
  assert(!game.emit(1, 0, 0));
  game.bullets.add(250, 560, 0, 0, 4, 1); game.graze();
  assert(game.score == 10 && game.eventCount == 64);
  game.init(1); game.spawnBoss();
  game.enemies.add(20, 20, 0, 0, 12, 0, 3);
  game.bullets.add(0, 0, 0, 0, 4, 1); game.bullets.add(0, 0, 0, 0, 4, 1);
  game.bullets.add(0, 0, 0, 0); game.bomb(64);
  assert(game.bombs == 2 && game.invulnerable == 180 && game.score == 110);
  assert(game.enemies.count == 1 && game.enemies.data[0].hp == 150 && game.bullets.count == 1);
  game.bomb(64); assert(game.bombs == 2);
  game.bomb(0); game.bomb(64); assert(game.bombs == 1);
  game.init(1); game.lives = 0; game.bomb(64); assert(game.bombs == 3);
  game.init(1);
  for (unsigned int i = 0; i < 3; ++i) {
    game.enemies.add(240, 560, 0, 0); game.defeatEnemy(0);
  }
  assert(game.items.count == 1 && game.killCount == 3);
  game.moveItems(); assert(game.power == 2 && game.score == 350 && game.items.count == 0);
  game.items.add(240, 560, 0, 0, 6); game.moveItems();
  game.items.add(240, 560, 0, 0, 6); game.moveItems(); assert(game.power == 3);
  game.cooldown = 0; game.bullets.count = 0; game.eventCount = 0; game.shoot(16);
  assert(game.bullets.count == 3 && game.eventCount == 3);
  assert(game.bullets.data[0].x == 232 && game.bullets.data[2].x == 248);
  game.items.add(0, 673, 0, 0); game.moveItems(); assert(game.items.count == 0);
  game.step(0); assert(game.eventCount == 0);
  game.init(1); assert(game.power == 1 && game.bombs == 3 && game.grazeCount == 0);
  for (unsigned int i = 0; i < 1000; ++i) game.step(0);
  assert(game.enemies.count == 0 && !game.bossSpawned);
  game.init(1);
  assert(!game.addStage(-1, 0, 0) && !game.addStage(0.5, 0, 0));
  assert(!game.addStage(0, 2, 0) && !game.addStage(0, 0, 4));
  assert(!game.addStage(0, 1, 1));
  assert(game.addStage(0, 0, 2) && game.addStage(0, 0, 3));
  assert(game.addStage(2, 0, 1) && !game.addStage(1, 0, 0));
  game.runStage();
  assert(game.enemies.count == 2 && game.stageCursor == 2);
  assert(game.enemies.data[0].mark == 2 && game.enemies.data[1].mark == 3);
  game.runStage(); assert(game.enemies.count == 2);
  game.frame = game.time = 2; game.runStage(); assert(game.enemies.count == 3);
  game.init(1);
  for (unsigned int i = 0; i < 128; ++i) game.enemies.add(0, 0, 0, 0);
  game.addStage(0, 1, 0); game.runStage();
  assert(game.stageBossPending && !game.bossSpawned);
  game.enemies.erase(0); game.runStage();
  assert(game.bossSpawned && !game.stageBossPending);
  game.init(1); game.addStage(0, 1, 0); game.addStage(0, 1, 0); game.runStage();
  assert(game.enemies.count == 1 && !game.stageBossPending);
  game.init(1);
  for (unsigned int i = 0; i < 4096; ++i) assert(game.addStage(i, 0, 0));
  assert(!game.addStage(4096, 0, 0));
  game.init(1); game.status = 0;
  game.step(0); assert(game.frame == 1 && game.time == 0 && game.status == 0);
  game.addStage(0, 0, 1); game.highScore = 999;
  game.step(128); assert(game.frame == 1 && game.time == 1 && game.enemies.count == 1);
  assert(game.status == 1 && game.highScore == 999 && game.stageCount == 1);
  game.step(128); assert(game.time == 2);
  game.step(256); assert(game.paused && game.time == 2);
  game.step(256); assert(game.paused && game.time == 2);
  game.step(0); game.step(256); assert(!game.paused && game.time == 3);
  game.init(1); game.lives = 0; game.step(0); assert(game.status == 2);
  game.init(1); game.phase = 4; game.score = 1000; game.step(0);
  assert(game.status == 3 && game.highScore == 1000);
  game.step(128); assert(game.status == 1 && game.time == 1 && game.highScore == 1000);
  game.init(1); const auto battleState = game.rng.state;
  game.emit(5, 240, 560); game.updateEffects();
  assert(game.particles.count == 24 && game.rng.state == battleState);
  game.eventCount = 0;
  for (unsigned int i = 0; i < 30; ++i) game.updateEffects();
  assert(game.particles.count == 0);
  for (unsigned int i = 0; i < 2048; ++i) game.particles.add(0, 0, 0, 0);
  game.emit(5, 0, 0); game.spawnEffects();
  assert(game.particles.count == 2048 && game.rng.state == battleState);
}
