import math
import unittest
from test_snapshots import load_game


class Lv3Tests(unittest.TestCase):
    def test_quarter_wave_boundaries_and_accuracy(self):
        game = load_game(3)
        for i in range(-360, 721):
            turn = i / 360
            self.assertLess(abs(game.dsin(turn) - math.sin(turn * math.pi * 2)), 1e-8)
            self.assertLess(abs(game.dcos(turn) - math.cos(turn * math.pi * 2)), 1e-8)

    def test_all_patterns_keep_speed_and_count(self):
        game = load_game(3)
        for mode in range(4):
            g = game.Game()
            g.fire_pattern(240, 100, mode, count=9, speed=2.5)
            self.assertEqual(g.bullets.count, 9)
            for i in range(9):
                self.assertAlmostEqual(math.hypot(g.bullets.vx[i], g.bullets.vy[i]), 2.5, places=7)
                self.assertEqual(g.bullets.kind[i], 1)

    def test_aimed_fan_symmetry_and_zero_vector(self):
        game = load_game(3)
        g = game.Game()
        g.fire_pattern(240, 100, 1, count=5)
        self.assertAlmostEqual(g.bullets.vx[2], 0)
        self.assertAlmostEqual(g.bullets.vx[0], -g.bullets.vx[4])
        self.assertGreater(g.bullets.vy[2], 0)
        g.bullets.count = 0
        g.fire_pattern(g.player_x, g.player_y, 1, count=1)
        self.assertTrue(math.isfinite(g.bullets.vy[0]))

    def test_spiral_wave_time_and_capacity_edges(self):
        game = load_game(3)
        g = game.Game()
        g.fire_pattern(0, 0, 0, count=0)
        self.assertEqual(g.bullets.count, 0)
        g.fire_pattern(0, 0, 0, count=1)
        self.assertGreater(g.bullets.vx[0], 0)
        g.bullets.count = 0
        g.frame = 10
        g.fire_pattern(0, 0, 2, count=1)
        self.assertGreater(g.bullets.vy[0], 0)
        g.bullets.count = g.bullets.capacity
        g.fire_pattern(0, 0, 3)
        self.assertEqual(g.bullets.count, 4096)
        with self.assertRaises(ValueError):
            g.fire_pattern(0, 0, 99)

    def test_wave_sways_without_overlapping_pairs(self):
        game = load_game(3)

        def turns(tick):
            g = game.Game()
            g.fire_pattern(240, 100, 3, count=6, tick=tick)
            return [math.atan2(g.bullets.vy[i], g.bullets.vx[i]) / (2 * math.pi) for i in range(6)]

        first, quarter = turns(0), turns(45)
        # 한 번의 발사 안에서는 부채꼴 간격으로 펼쳐져 같은 방향의 쌍이 생기지 않는다.
        for a, b in zip(first, first[1:]):
            self.assertAlmostEqual(b - a, .025, places=6)
        # 사분의 일 주기 뒤에는 부채꼴 전체가 진폭만큼 옆으로 옮겨 간다.
        for a, b in zip(first, quarter):
            self.assertAlmostEqual(b - a, .12, places=6)

    def test_spiral_enemy_streams_two_rotating_arms(self):
        game = load_game(3)
        g = game.Game()
        spiral = g.enemies.add(240, 100, 0.0, 0.0, radius=12.0, kind=0, hp=3.0)
        g.enemies.mark[spiral] = 2
        shots = []
        for frame in range(1, 61):
            g.frame = frame
            before = g.bullets.count
            g.move_enemies()
            if g.bullets.count > before:
                shots.append((frame, g.bullets.count - before,
                              math.atan2(g.bullets.vy[before], g.bullets.vx[before]) / (2 * math.pi)))
        self.assertEqual([s[0] for s in shots], list(range(6, 61, 6)))
        self.assertTrue(all(s[1] == 2 for s in shots))
        # 발사마다 시작 방향이 6스텝 × 0.007 회전수씩 돌아 소용돌이 궤적을 만든다.
        for (_, _, a), (_, _, b) in zip(shots, shots[1:]):
            self.assertAlmostEqual((b - a) % 1, .042, places=6)
        ring = game.Game()
        other = ring.enemies.add(240, 100, 0.0, 0.0, radius=12.0, kind=0, hp=3.0)
        ring.enemies.mark[other] = 0
        for frame in range(1, 61):
            ring.frame = frame
            ring.move_enemies()
        self.assertEqual(ring.bullets.count, 8)

    def test_spawn_patterns_cycle_without_extra_rng(self):
        game = load_game(3)
        reference = game.Rng(game.SEED)
        g = game.Game()
        for i in range(4):
            g.frame = 30 + i * 90
            index = g.spawn_enemy()
            self.assertEqual(g.enemies.mark[index], i)
            self.assertEqual(g.enemies.x[index], 32 + reference.next() % 416)


if __name__ == '__main__':
    unittest.main()
