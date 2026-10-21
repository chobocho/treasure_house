import unittest
from test_snapshots import load_game


class Lv5Tests(unittest.TestCase):
    def game(self):
        return load_game(5).Game()

    def test_graze_once_and_hit_excluded(self):
        g = self.game()
        g.bullets.add(255, 560, 0, 0, radius=4, kind=1)
        g.graze()
        g.graze()
        self.assertEqual((g.score, g.graze_count), (10, 1))
        g.bullets.add(240, 560, 0, 0, radius=4, kind=1)
        g.graze()
        self.assertEqual(g.graze_count, 1)
        g.invulnerable = 1
        g.bullets.add(225, 560, 0, 0, radius=4, kind=1)
        g.graze()
        self.assertEqual(g.graze_count, 1)

    def test_bomb_edge_and_ownership(self):
        g = self.game()
        g.bullets.add(0, 0, 0, 0)
        g.bullets.add(10, 10, 0, 0, kind=1)
        g.step(64)
        self.assertEqual((g.bombs, g.score, g.bullets.count), (2, 5, 1))
        self.assertEqual(g.invulnerable, 180)
        g.step(64)
        self.assertEqual(g.bombs, 2)
        g.step(0)
        g.step(64)
        self.assertEqual(g.bombs, 1)
        g.bombs = 0
        g.step(0)
        g.step(64)
        self.assertEqual(g.bombs, 0)

    def test_bomb_damage_and_drop_every_third(self):
        g = self.game()
        boss = g.spawn_boss()
        for x in [50, 100, 150]:
            g.enemies.add(x, 200, 0, 0, hp=3)
        g.step(64)
        self.assertEqual(g.enemies.hp[g.find_boss()], 150)
        self.assertEqual((g.score, g.kill_count, g.items.count), (300, 3, 1))
        self.assertEqual(g.items.y[0], 201.5)

    def test_pickup_power_cap_and_multishot(self):
        g = self.game()
        for expected in [2, 3, 3]:
            g.items.add(240, 558.5, 0, 1.5, radius=6)
            g.move_items()
            self.assertEqual(g.power, expected)
        self.assertEqual(g.score, 150)
        g.shoot(16)
        self.assertEqual(g.bullets.count, 3)
        self.assertEqual(list(g.bullets.x[:3]), [232, 240, 248])
        g.shoot(16)
        self.assertEqual(g.bullets.count, 3)

    def test_item_cull_and_full_pool(self):
        g = self.game()
        g.items.add(0, 672, 0, 1.5)
        g.move_items()
        self.assertEqual(g.items.count, 0)
        for _ in range(64):
            g.items.add(0, 0, 0, 0)
        self.assertEqual(g.items.add(0, 0, 0, 0), -1)

    def test_event_capacity_reset_and_state_independent(self):
        g = self.game()
        for _ in range(70):
            g.emit(4, 10, 20)
        self.assertEqual(g.event_count, 64)
        g.bullets.add(255, 560, 0, 0, radius=4, kind=1)
        g.graze()
        self.assertEqual(g.score, 10)
        self.assertEqual(g.event_count, 64)
        g.step(0)
        self.assertEqual(g.event_count, 0)

    def test_dead_player_cannot_bomb_or_graze(self):
        g = self.game()
        g.lives = 0
        g.bullets.add(255, 560, 0, 0, radius=4, kind=1)
        g.step(64)
        self.assertEqual((g.bombs, g.score), (3, 0))

    def test_item_and_graze_pixels(self):
        import importlib.util
        from pathlib import Path
        import pygame
        g = self.game()
        path = Path(__file__).parent / 'lv5/render.py'
        spec = importlib.util.spec_from_file_location('rewards_renderer', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pygame.display.init()
        pygame.font.init()
        try:
            screen = pygame.display.set_mode((480, 640))
            g.items.add(100, 200, 0, 0, radius=6)
            g.previous_input = 32
            module.Renderer(screen).draw(g, 1)
            self.assertEqual(tuple(screen.get_at((100, 200)))[:3], (255, 210, 80))
            self.assertEqual(tuple(screen.get_at((256, 560)))[:3], (80, 150, 180))
        finally:
            pygame.quit()
