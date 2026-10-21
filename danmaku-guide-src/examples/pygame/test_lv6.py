import unittest
from test_snapshots import load_game


class Lv6Tests(unittest.TestCase):
    def module(self):
        return load_game(6)

    def test_empty_stage_has_no_implicit_spawns(self):
        g = self.module().Game(stage=[])
        for _ in range(700):
            g.step(0)
        self.assertEqual((g.enemies.count, g.stage_cursor, g.phase), (0, 0, 0))

    def test_same_frame_order_and_once(self):
        data = [{'frame': 0, 'kind': 'enemy', 'pattern': 3},
                {'frame': 0, 'kind': 'enemy', 'pattern': 1},
                {'frame': 1, 'kind': 'boss'}]
        g = self.module().Game(stage=data)
        g.step(0)
        self.assertEqual((g.enemies.count, g.stage_cursor), (2, 2))
        self.assertEqual(list(g.enemies.mark[:2]), [3, 1])
        g.step(0)
        self.assertEqual((g.enemies.count, g.stage_cursor, g.phase), (3, 3, 1))
        g.step(0)
        self.assertEqual(g.enemies.count, 3)

    def test_validation_boundaries(self):
        validate = self.module().validate_stage
        self.assertEqual(validate([]), ())
        invalid = [None, {}, [None], [{'frame': -1, 'kind': 'boss'}],
                   [{'frame': True, 'kind': 'boss'}], [{'frame': 1.5, 'kind': 'boss'}],
                   [{'frame': 1, 'kind': 'boss'}, {'frame': 0, 'kind': 'boss'}],
                   [{'frame': 0, 'kind': 'unknown'}],
                   [{'frame': 0, 'kind': 'enemy', 'pattern': -1}],
                   [{'frame': 0, 'kind': 'enemy', 'pattern': 4}],
                   [{'frame': 0, 'kind': 'enemy', 'pattern': True}],
                   [{'frame': 0, 'kind': 'enemy'}],
                   [{'frame': 0, 'kind': 'boss', 'extra': 1}],
                   [{'frame': 0, 'kind': 'boss'}] * 4097]
        for data in invalid:
            with self.subTest(data=str(data)[:100]):
                with self.assertRaises(ValueError):
                    validate(data)
        self.assertEqual(len(validate([{'frame': 0, 'kind': 'boss'}] * 4096)), 4096)

    def test_data_is_copied(self):
        data = [{'frame': 1, 'kind': 'enemy', 'pattern': 2}]
        g = self.module().Game(stage=data)
        data[0]['frame'] = 999
        data.clear()
        g.step(0)
        g.step(0)
        self.assertEqual(g.enemies.count, 1)
        self.assertIsInstance(g.stage, tuple)

    def test_boss_retry_and_duplicates(self):
        g = self.module().Game(stage=[{'frame': 0, 'kind': 'boss'}, {'frame': 1, 'kind': 'boss'}])
        for _ in range(128):
            g.enemies.add(0, 0, 0, 0)
        g.step(0)
        self.assertTrue(g.stage_boss_pending)
        g.enemies.erase(0)
        g.step(0)
        self.assertTrue(g.boss_spawned)
        self.assertFalse(g.stage_boss_pending)
        self.assertEqual(sum(g.enemies.kind[i] == 1 for i in range(g.enemies.count)), 1)

    def test_full_enemy_pool_still_consumes_rng_and_event(self):
        module = self.module()
        g = module.Game(stage=[{'frame': 0, 'kind': 'enemy', 'pattern': 0}])
        for _ in range(128):
            g.enemies.add(0, 0, 0, 0)
        expected = module.Rng(g.seed).next()
        g.step(0)
        self.assertEqual((g.rng.state, g.stage_cursor, g.enemies.count), (expected, 1, 128))
