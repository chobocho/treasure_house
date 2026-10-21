import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_snapshots import load_game


def adapter(name):
    path = Path(__file__).parent / 'lv7' / (name + '.py')
    if not path.exists():
        raise AssertionError('Lv7 어댑터 파일이 있어야 합니다')
    spec = importlib.util.spec_from_file_location('lv7_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Lv7Tests(unittest.TestCase):
    def test_title_start_pause_resume(self):
        m = load_game(7)
        g = m.Game(start=False)
        g.step(m.RIGHT | m.SHOOT)
        self.assertEqual((g.status, g.player_x, g.bullets.count, g.time), (0, 240, 0, 0))
        g.step(m.START | m.RIGHT)
        self.assertEqual((g.status, g.player_x, g.time), (1, 244, 1))
        g.step(m.PAUSE | m.RIGHT)
        self.assertTrue(g.paused)
        self.assertEqual((g.player_x, g.time), (244, 1))
        g.step(m.PAUSE)
        self.assertTrue(g.paused)
        g.step(0)
        g.step(m.PAUSE | m.RIGHT)
        self.assertEqual((g.paused, g.player_x, g.time), (False, 248, 2))

    def test_game_over_freezes_gameplay_and_restart_keeps_best(self):
        m = load_game(7)
        g = m.Game()
        g.score, g.lives = 1234, 1
        g.bullets.add(240, 560, 0, 0, radius=4, kind=1)
        g.step(0)
        self.assertEqual((g.status, g.lives, g.high_score), (2, 0, 1234))
        old = (g.time, g.player_x, g.bullets.count, g.score)
        g.step(m.RIGHT | m.SHOOT)
        self.assertEqual((g.time, g.player_x, g.bullets.count, g.score), old)
        g.step(m.START)
        self.assertEqual((g.status, g.lives, g.score, g.high_score), (1, 3, 0, 1234))

    def test_clear_state(self):
        g = load_game(7).Game()
        i = g.spawn_boss()
        g.enemies.hp[i] = 1
        g.bullets.add(240, 100, 0, 0)
        g.step(0)
        self.assertEqual((g.status, g.phase, g.high_score), (3, 4, 1000))

    def test_effect_rng_does_not_change_game_rng(self):
        m = load_game(7)
        g = m.Game()
        state = g.rng.state
        g.emit(3, 100, 100)
        g.update_effects()
        self.assertGreater(g.particles.count, 0)
        self.assertEqual(g.rng.state, state)
        for _ in range(31):
            g.event_count = 0
            g.update_effects()
        self.assertEqual(g.particles.count, 0)
        self.assertEqual(g.particles.capacity, 2048)

    def test_particle_capacity(self):
        g = load_game(7).Game()
        for _ in range(2048):
            g.particles.add(0, 0, 0, 0, hp=30)
        g.emit(5, 100, 100)
        g.update_effects()
        self.assertEqual(g.particles.count, 2048)

    def test_synth_audio_and_unavailable_device(self):
        import pygame
        audio = adapter('audio')
        samples = audio.tone(440, .1)
        self.assertEqual(len(samples), 2205)
        self.assertEqual(samples.typecode, 'h')
        self.assertGreater(max(samples), 0)
        self.assertLessEqual(max(abs(x) for x in samples), 32767)
        with patch.object(pygame.mixer, 'init', side_effect=pygame.error('없는 장치')):
            sound = audio.Audio()
            self.assertFalse(sound.enabled)
            sound.consume(load_game(7).Game())
            sound.close()
        sound = audio.Audio()
        self.assertTrue(sound.enabled)
        g = load_game(7).Game()
        g.emit(5, 0, 0)
        sound.consume(g)
        sound.close()

    def test_persistence_valid_corrupt_missing_and_range(self):
        module = adapter('storage')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'best.json'
            self.assertEqual(module.load_best(path), 0)
            self.assertTrue(module.save_best(path, 1234))
            self.assertEqual(module.load_best(path), 1234)
            for text in ['no json', '{"best":true}', '{"best":-1}', '{"best":1.5}', '{"best":9007199254740992}']:
                path.write_text(text)
                self.assertEqual(module.load_best(path), 0)
            for value in [-1, True, 1.5, 9007199254740992]:
                self.assertFalse(module.save_best(path, value))
            self.assertFalse(module.save_best(Path(directory)/'missing'/'best.json', 1))

    def test_overlay_and_particle_pixels(self):
        import pygame
        render = adapter('render')
        pygame.display.init()
        pygame.font.init()
        try:
            screen = pygame.display.set_mode((480, 640))
            g = load_game(7).Game(start=False)
            renderer = render.Renderer(screen)
            renderer.draw(g, 1)
            self.assertNotEqual(tuple(screen.get_at((80, 280)))[:3], (8, 21, 35))
            g.status = 1
            g.particles.add(100, 200, 0, 0, radius=2, hp=30, kind=3)
            renderer.draw(g, 1)
            self.assertEqual(tuple(screen.get_at((100, 200)))[:3], (255, 190, 90))
        finally:
            pygame.quit()
