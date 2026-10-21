import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent
EXPECTED_LEVELS = [1, 2, 3, 4, 5, 6, 7]


def load_game(level):
    file = HERE / f'lv{level}/game.py'
    if not file.exists():
        raise AssertionError(f'Lv{level}의 독립 게임 모듈이 있어야 한다')
    spec = importlib.util.spec_from_file_location(f'pygame_game_{level}', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SnapshotTests(unittest.TestCase):
    def test_golden_cannot_be_overwritten(self):
        file = SRC / 'spec/golden/lv1.json'
        self.assertTrue(file.exists())
        original = file.read_bytes()
        result = subprocess.run([sys.executable, str(HERE / 'generate_golden.py'), '1'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(file.read_bytes(), original)

    def test_invalid_input_bits(self):
        game = load_game(1).Game()
        for bits in [-1, 512, None, 1.5, 'shoot']:
            with self.assertRaises(ValueError):
                game.step(bits)

    def test_shared_constants(self):
        constants = json.loads((SRC / 'spec/constants.json').read_text(encoding='utf-8'))
        for level in EXPECTED_LEVELS:
            game = load_game(level)
            self.assertEqual((game.WIDTH, game.HEIGHT), (480, 640))
            self.assertEqual(game.SEED, constants['seed'])
            self.assertEqual(game.PLAYER_SPEED, constants['player']['speed'])
            self.assertEqual(game.FOCUS_SPEED, constants['player']['focusSpeed'])
            self.assertEqual(game.PLAYER_RADIUS, constants['player']['hitRadius'])
            self.assertEqual(game.GRAZE_RADIUS, constants['player']['grazeRadius'])
            self.assertEqual(game.Game().bullets.capacity, constants['pools']['bullets'])

    def test_move_focus_diagonal_and_opposites(self):
        for level in EXPECTED_LEVELS:
            game = load_game(level)
            g = game.Game()
            g.step(game.RIGHT)
            self.assertEqual(g.player_x, 244)
            g.step(game.LEFT | game.RIGHT)
            self.assertEqual(g.player_x, 244)
            g.step(game.RIGHT | game.FOCUS)
            self.assertAlmostEqual(g.player_x, 245.6)
            x, y = g.player_x, g.player_y
            g.step(game.UP | game.LEFT)
            self.assertAlmostEqual(math.hypot(g.player_x - x, g.player_y - y), 4)
            x, y = g.player_x, g.player_y
            g.step(0)
            self.assertEqual((g.player_x, g.player_y), (x, y))

    def test_player_boundaries(self):
        for level in [1]:
            game = load_game(level)
            g = game.Game()
            for _ in range(200):
                g.step(game.UP | game.LEFT)
            self.assertEqual((g.player_x, g.player_y), (12, 12))
            for _ in range(300):
                g.step(game.DOWN | game.RIGHT)
            self.assertEqual((g.player_x, g.player_y), (468, 628))

    def test_shot_cooldown_and_recycling(self):
        for level in [1]:
            game = load_game(level)
            g = game.Game()
            g.step(game.SHOOT)
            self.assertEqual(g.bullets.count, 1)
            self.assertEqual(g.bullets.vy[0], -8)
            self.assertEqual(g.bullets.y[0], 538)
            for _ in range(7):
                g.step(game.SHOOT)
            self.assertEqual(g.bullets.count, 1)
            g.step(game.SHOOT)
            self.assertEqual(g.bullets.count, 2)
            identity = id(g.bullets.x)
            for _ in range(300):
                g.step(0)
            self.assertEqual(g.bullets.count, 0)
            self.assertEqual(id(g.bullets.x), identity)

    def test_pool_capacity_and_all_fields(self):
        game = load_game(1)
        self.assertEqual(game.Pool(0).add(0, 0, 0, 0), -1)
        pool = game.Pool(1)
        self.assertEqual(pool.add(1, 2, 3, 4, radius=5, kind=1, hp=9), 0)
        self.assertEqual(pool.add(0, 0, 0, 0), -1)
        self.assertTrue(pool.erase(0))
        self.assertFalse(pool.erase(0))
        self.assertFalse(pool.erase(-1))
        pool = game.Pool(2)
        pool.add(0, 0, 0, 0)
        pool.add(1, 2, 3, 4, radius=5, kind=1, hp=9)
        pool.mark[1] = 7
        pool.erase(0)
        self.assertEqual([pool.x[0], pool.y[0], pool.vx[0], pool.vy[0], pool.radius[0], pool.kind[0], pool.hp[0], pool.mark[0]], [1, 2, 3, 4, 5, 1, 9, 7])
        with self.assertRaises(ValueError):
            game.Pool(-1)

    def test_golden_checkpoints(self):
        for level in EXPECTED_LEVELS:
            with self.subTest(level=level):
                path = SRC / f'spec/golden/lv{level}.json'
                self.assertTrue(path.exists(), '기준 기록은 pygame의 실제 실행에서 생성해야 한다')
                golden = json.loads(path.read_text(encoding='utf-8'))
                game = load_game(level)
                stage_path = HERE / f'lv{level}/stage.json'
                options = {'stage': json.loads(stage_path.read_text(encoding='utf-8'))} if stage_path.exists() else {}
                g = game.Game(golden['seed'], **options)
                cursor, bits, actual = 0, 0, []
                for frame in range(1800):
                    if cursor < len(golden['inputs']) and frame == golden['inputs'][cursor]['frame']:
                        bits = golden['inputs'][cursor]['bits']
                        cursor += 1
                    g.step(bits)
                    if g.frame in [60, 600, 1800]:
                        actual.append(g.snapshot())
                self.assertEqual(actual, golden['checkpoints'])

    def test_headless_commands_and_render(self):
        for level in EXPECTED_LEVELS:
            main = HERE / f'lv{level}/main.py'
            self.assertTrue(main.exists())
            result = subprocess.run([sys.executable, str(main), '--headless', '--frames', '1800'], check=True, text=True, capture_output=True)
            data = json.loads(result.stdout)
            self.assertEqual(data['checkpoints'][-1]['frame'], 1800)
            result = subprocess.run(['bash', str(HERE / 'commands.sh'), f'lv{level}', '--frames', '2'], cwd=SRC, check=True, text=True, capture_output=True)
            self.assertTrue(json.loads(result.stdout)['notBlank'])

    def test_snapshot_folder_is_standalone(self):
        for level in EXPECTED_LEVELS:
            with tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'game'
                self.assertTrue((HERE / f'lv{level}').exists())
                shutil.copytree(HERE / f'lv{level}', target)
                result = subprocess.run([sys.executable, str(target / 'main.py'), '--frames', '2'], cwd=temp, check=True, capture_output=True, text=True)
                self.assertTrue(json.loads(result.stdout)['notBlank'])

    def test_player_bullet_is_drawn_at_logic_position(self):
        import pygame
        for level in EXPECTED_LEVELS:
            spec = importlib.util.spec_from_file_location(f'pygame_render_{level}', HERE / f'lv{level}/render.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            pygame.display.init()
            pygame.font.init()
            try:
                screen = pygame.display.set_mode((480, 640))
                game = load_game(level)
                g = game.Game()
                g.step(game.SHOOT)
                module.Renderer(screen).draw(g, 1.0)
                x, y = round(g.bullets.x[0]), round(g.bullets.y[0])
                self.assertEqual(tuple(screen.get_at((x, y)))[:3], (100, 220, 255))
            finally:
                pygame.quit()


if __name__ == '__main__':
    unittest.main()
