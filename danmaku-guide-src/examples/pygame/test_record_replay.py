import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def recorder():
    path = HERE / 'record_replay.py'
    if not path.exists():
        raise AssertionError('자동 조종 기록기가 있어야 합니다')
    spec = importlib.util.spec_from_file_location('record_replay', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordReplayTests(unittest.TestCase):
    def test_candidates_are_distinct_moves_with_and_without_focus(self):
        r = recorder()
        m = r.load(7)
        moves = r.candidates(m)
        self.assertEqual(len(moves), 17)
        self.assertEqual(len(set(moves)), 17)
        self.assertIn(0, moves)
        self.assertNotIn(m.FOCUS, moves)

    def test_evaluate_penalizes_a_hit_and_prefers_escape(self):
        r = recorder()
        m = r.load(7)
        g = m.Game()
        # 정지하면 곧바로 맞는 적탄 하나를 플레이어 바로 위에 둔다.
        g.bullets.add(g.player_x, g.player_y - 20, 0.0, 2.5, radius=4.0, kind=1)
        stay = r.evaluate(g, 0)
        escape = r.evaluate(g, m.LEFT)
        self.assertLess(stay, -1e5)
        self.assertGreater(escape, -1e5)
        self.assertEqual(g.lives, 3)  # 평가는 복사본만 진행한다

    def test_final_phase_keeps_the_boss_alive(self):
        r = recorder()
        m = r.load(7)
        g = m.Game()
        index = g.spawn_boss()
        self.assertTrue(r.wants_shot(g))
        g.phase, g.enemies.hp[index] = 3, 40.0
        self.assertFalse(r.wants_shot(g))
        g.enemies.hp[index] = 41.0
        self.assertTrue(r.wants_shot(g))


if __name__ == '__main__':
    unittest.main()
