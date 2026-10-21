import unittest
import importlib.util
from pathlib import Path
from test_snapshots import load_game


class Lv2Tests(unittest.TestCase):
    def test_enemy_and_enemy_bullet_pixels(self):
        import pygame
        file = Path(__file__).parent / 'lv2/render.py'
        self.assertTrue(file.exists())
        spec = importlib.util.spec_from_file_location('render_lv2_types', file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pygame.display.init()
        pygame.font.init()
        try:
            screen = pygame.display.set_mode((480, 640))
            g = load_game(2).Game()
            g.enemies.add(100, 100, 0, 0)
            g.bullets.add(300, 300, 0, 0, radius=4, kind=1)
            module.Renderer(screen).draw(g, 1.0)
            region = pygame.image.tobytes(screen.subsurface((84, 84, 32, 32)), 'RGB')
            self.assertNotEqual(region, bytes((8, 21, 35)) * (32 * 32))
            color = screen.get_at((300, 300))
            self.assertGreater(color.r, 150)
            self.assertLess(color.g, 150)
        finally:
            pygame.quit()

    def test_rng_sequence_and_collision_edges(self):
        game = load_game(2)
        rng = game.Rng(1)
        self.assertEqual([rng.next(), rng.next(), rng.next()], [270369, 67634689, 2647435461])
        self.assertTrue(game.overlaps(0, 0, 2, 5, 0, 3))
        self.assertFalse(game.overlaps(0, 0, 2, 5.001, 0, 3))

    def test_spawn_and_enemy_shot(self):
        game = load_game(2)
        g = game.Game()
        for _ in range(31):
            g.step(0)
        self.assertEqual(g.enemies.count, 1)
        self.assertGreaterEqual(g.enemies.x[0], 32)
        self.assertLessEqual(g.enemies.x[0], 447)
        g.enemies.age[0] = 59
        g.step(0)
        self.assertTrue(any(g.bullets.kind[i] == 1 for i in range(g.bullets.count)))

    def test_one_enemy_scores_once(self):
        game = load_game(2)
        g = game.Game()
        g.enemies.add(240, 100, 0, 0, radius=12, hp=1)
        g.bullets.add(240, 100, 0, 0)
        g.bullets.add(240, 100, 0, 0)
        g.step(0)
        self.assertEqual(g.score, 100)
        self.assertEqual(g.enemies.count, 0)
        self.assertEqual(g.bullets.count, 1)

    def test_enemy_bullet_and_invulnerability_boundary(self):
        game = load_game(2)
        g = game.Game()
        for _ in range(2):
            g.bullets.add(g.player_x, g.player_y, 0, 0, radius=4, kind=1)
        g.step(0)
        self.assertEqual(g.lives, 2)
        self.assertEqual(g.invulnerable, 120)
        g.step(0)
        self.assertEqual(g.lives, 2)
        g.invulnerable = 1
        g.step(0)
        self.assertEqual(g.lives, 1)

    def test_body_collision_and_lives_floor(self):
        game = load_game(2)
        g = game.Game()
        g.enemies.add(240, 560, 0, 0, radius=12)
        g.step(0)
        self.assertEqual((g.lives, g.score, g.enemies.count), (2, 0, 0))
        g.lives, g.invulnerable = 0, 0
        g.bullets.add(240, 560, 0, 0, radius=4, kind=1)
        g.step(0)
        self.assertEqual(g.lives, 0)

    def test_enemy_capacity_and_no_friendly_fire(self):
        game = load_game(2)
        g = game.Game()
        for i in range(128):
            g.enemies.add(100, 100, 0, 0, hp=3)
        self.assertEqual(g.spawn_enemy(), -1)
        g.bullets.add(100, 100, 0, 0, radius=4, kind=1)
        g.step(0)
        self.assertEqual(g.enemies.count, 128)
        self.assertEqual(g.enemies.hp[0], 3)


if __name__ == '__main__':
    unittest.main()
