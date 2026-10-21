import importlib.util
from pathlib import Path
import unittest
from test_snapshots import load_game


class Lv4Tests(unittest.TestCase):
    def test_spawn_and_no_duplicate(self):
        game = load_game(4)
        g = game.Game()
        g.frame = 600
        g.step(0)
        self.assertTrue(g.boss_spawned)
        self.assertEqual(g.phase, 1)
        self.assertGreaterEqual(g.find_boss(), 0)
        self.assertEqual(g.spawn_boss(), -1)

    def test_capacity_retry(self):
        game = load_game(4)
        g = game.Game()
        for _ in range(128):
            g.enemies.add(10, 10, 0, 0)
        g.frame = 600
        g.step(0)
        self.assertFalse(g.boss_spawned)
        g.enemies.erase(0)
        g.step(0)
        self.assertTrue(g.boss_spawned)
        self.assertEqual(g.enemies.count, 128)

    def test_timer_and_hp_phase_boundaries(self):
        game = load_game(4)
        g = game.Game()
        index = g.spawn_boss()
        g.bullets.add(50, 50, 0, 0, kind=1)
        g.phase_time = 299
        g.step(0)
        self.assertEqual((g.phase, g.phase_time), (2, 0))
        self.assertFalse(any(g.bullets.x[i] == 50 for i in range(g.bullets.count)))
        g.enemies.hp[index] = 60
        g.step(0)
        self.assertEqual(g.phase, 3)
        g = game.Game()
        index = g.spawn_boss()
        g.enemies.hp[index] = 120
        g.step(0)
        self.assertEqual(g.phase, 2)

    def test_boss_death_deferred_clear_and_score(self):
        game = load_game(4)
        g = game.Game()
        index = g.spawn_boss()
        g.enemies.hp[index] = 1
        g.bullets.add(240, 100, 0, 0)
        g.bullets.add(300, 300, 0, 0, kind=1)
        g.bullets.add(0, 0, 0, 0)
        g.step(0)
        self.assertEqual((g.phase, g.score, g.enemies.count), (4, 1000, 0))
        self.assertEqual(g.bullets.count, 1)
        self.assertEqual(g.bullets.kind[0], 0)
        self.assertFalse(g.clear_pending)

    def test_boss_body_survives_player_contact(self):
        game = load_game(4)
        g = game.Game()
        g.spawn_boss()
        g.player_x, g.player_y = 240, 100
        g.step(0)
        self.assertEqual(g.lives, 2)
        self.assertGreaterEqual(g.find_boss(), 0)

    def test_phase_attack_counts(self):
        game = load_game(4)
        g = game.Game()
        g.spawn_boss()
        for phase, elapsed, count in [(1, 44, 12), (2, 31, 7), (3, 19, 9), (3, 3, 3), (3, 4, 0)]:
            g.phase, g.phase_time, g.bullets.count = phase, elapsed, 0
            g.step(0)
            self.assertEqual(g.bullets.count, count)

    def test_health_bar_pixels(self):
        import pygame
        load_game(4)
        file = Path(__file__).parent / 'lv4/render.py'
        self.assertTrue(file.exists())
        spec = importlib.util.spec_from_file_location('boss_renderer', file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pygame.display.init()
        pygame.font.init()
        try:
            screen = pygame.display.set_mode((480, 640))
            g = load_game(4).Game()
            index = g.spawn_boss()
            g.enemies.hp[index] = 90
            module.Renderer(screen).draw(g, 1.0)
            self.assertEqual(tuple(screen.get_at((20, 62)))[:3], (255, 100, 120))
            self.assertEqual(tuple(screen.get_at((460, 62)))[:3], (30, 40, 60))
        finally:
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
