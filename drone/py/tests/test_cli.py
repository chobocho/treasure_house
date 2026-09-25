# -*- coding: utf-8 -*-
"""cli 시험 — python3 -m droneshow 의 하위 명령 (SPEC §9.6)."""
import contextlib
import io
import json
import os
import tempfile
import unittest

from droneshow import cli

SPEC = {'fps': 25, 'profile': {'kind': 'trapezoid', 'ramp': 0.25},
        'scenes': [
            {'name': 'grid', 'shape': 'grid', 'n': 6, 'd': 3.0,
             'z0': 10.0, 'hold': 1.0, 'rgb': [255, 255, 255]},
            {'name': 'hi', 'shape': 'text', 's': 'HI', 'd': 3.0,
             'z0': 10.0, 'hold': 1.0, 'rgb': [255, 0, 64]}]}


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(list(args))
    return code, out.getvalue()


class Cli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='cli-')
        self.spec = os.path.join(self.dir, 'spec.json')
        with open(self.spec, 'w', encoding='utf-8') as f:
            json.dump(dict(SPEC, scenes=[SPEC['scenes'][0],
                                         dict(SPEC['scenes'][0],
                                              name='circle',
                                              shape='circle')]), f)
        self.show = os.path.join(self.dir, 'show.json')

    def test_plan_then_info(self):
        code, out = run('plan', self.spec, '-o', self.show)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(self.show))
        code, out = run('info', self.show)
        self.assertEqual(code, 0)
        self.assertIn('드론 6대', out)
        self.assertIn('최소 간격', out)

    def test_text_scene_needs_matching_count(self):
        with open(self.spec, 'w', encoding='utf-8') as f:
            json.dump(SPEC, f)
        code, out = run('plan', self.spec, '-o', self.show)
        self.assertEqual(code, 2)
        self.assertIn('점의 수', out)

    def test_csv(self):
        run('plan', self.spec, '-o', self.show)
        code, _out = run('csv', self.show, self.dir)
        self.assertEqual(code, 0)
        rows = open(os.path.join(self.dir, 'drone_0.csv'),
                    encoding='utf-8').read().split('\n')
        self.assertTrue(rows[0].startswith('Time [msec]'))

    def test_svg(self):
        run('plan', self.spec, '-o', self.show)
        code, out = run('svg', self.show, '0', '--view', 'top')
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith('<svg class="show"'))

    def test_fly_kinematic_and_physics(self):
        run('plan', self.spec, '-o', self.show)
        code, out = run('fly', self.show, '--mode', 'kinematic')
        self.assertIn('kinematic', out)
        code, out = run('fly', self.show, '--mode', 'physics',
                        '--ids', '0,1')
        self.assertEqual(code, 0)
        self.assertIn('최대 오차', out)


if __name__ == '__main__':
    unittest.main()
