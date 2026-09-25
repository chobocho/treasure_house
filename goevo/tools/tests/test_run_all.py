# -*- coding: utf-8 -*-
"""run_all.py 의 시험 — 캡처 이름·첫 줄·기대 종료 코드·이름 겹침·묶음 지우기.

go 를 돌리지 않는다: gover.execute 를 가짜로 바꿔 끼운다.

    python3 -m unittest discover -s tools/tests
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BASE)

import run_all  # noqa: E402


class Fake(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='runall-')
        self.saved = (run_all.OUT, run_all.BASE, run_all.gover.execute)
        run_all.OUT = os.path.join(self.root, 'out')
        run_all.BASE = self.root
        os.makedirs(run_all.OUT)
        ex = os.path.join(self.root, 'ex', '07', 'r')
        os.makedirs(ex)
        with io.open(os.path.join(ex, 'go.mod'), 'w') as f:
            f.write('module ex/07/r\n\ngo 1.22\n')
        self.calls = []

        def fake(src, cmd, lang=None, godebug=None, exp=None, name=None):
            self.calls.append((cmd, lang, godebug, exp, name))
            if lang == '1.21':
                return 1, './main.go:6:17: requires go1.22 or later\n'
            return 0, '012'
        run_all.gover.execute = fake
        run_all.Ctx.taken = set()          # 한 번의 run_all 과 같은 출발점
        self.ctx = run_all.Ctx('b7')

    def tearDown(self):
        run_all.OUT, run_all.BASE, run_all.gover.execute = self.saved
        shutil.rmtree(self.root)

    def read(self, name):
        with io.open(os.path.join(run_all.OUT, name), encoding='utf-8') as f:
            return f.read()

    def test_default_version_from_go_mod(self):
        self.ctx.go('ex/07/r')
        self.assertEqual(self.read('07-r__go1.22.txt'), '$ go run .\n012\n')

    def test_lang_downgrade_expected_failure(self):
        self.ctx.go('ex/07/r', v='1.21', expect=1)
        self.assertEqual(self.read('07-r__go1.21.txt'),
                         '$ go run .\n./main.go:6:17: requires go1.22 or '
                         'later\n[exit 1]\n')
        self.assertEqual(self.calls[0][1], '1.21')

    def test_unexpected_exit_stops(self):
        with self.assertRaises(RuntimeError):
            self.ctx.go('ex/07/r', v='1.21')          # 기대는 0 인데 1

    def test_godebug_in_first_line_and_name(self):
        self.ctx.go('ex/07/r', godebug='x=1', cmd='go test -v', tag='test')
        self.assertTrue(self.read('07-r__go1.22-godebug-x-1-test.txt')
                        .startswith('$ GODEBUG=x=1 go test -v\n'))

    def test_name_collision_stops(self):
        self.ctx.go('ex/07/r')
        with self.assertRaises(RuntimeError):
            self.ctx.go('ex/07/r', cmd='go vet .')    # tag 없이 같은 이름

    def test_batch_files_recorded_and_cleared(self):
        self.ctx.go('ex/07/r')
        run_all.save_batches({'b7': sorted(self.ctx.written)})
        with io.open(os.path.join(run_all.OUT, 'batches.json')) as f:
            self.assertEqual(json.load(f), {'b7': ['07-r__go1.22.txt']})
        run_all.clear_batch('b7')
        self.assertFalse(os.path.exists(
            os.path.join(run_all.OUT, '07-r__go1.22.txt')))


class FullRunGuard(unittest.TestCase):
    def test_bare_run_refuses(self):
        # 인자 없이 돌리면 모든 묶음의 캡처를 먼저 지운다 — 2026-09-24 에
        # 누군가 그렇게 돌려 02~09부 캡처가 사라졌다. 전체는 --all 로만.
        # 가드가 없더라도 이 시험이 진짜 실험을 돌리면 안 된다(RED 단계에서
        # 실제로 전체 실행이 한 번 돌았다) — run 을 가짜로 바꿔 끼운다.
        saved = run_all.run

        def fake_run(only):
            raise AssertionError('가드 없이 실험을 돌리려 했다')
        run_all.run = fake_run
        try:
            with self.assertRaises(SystemExit):
                run_all.main([])
        finally:
            run_all.run = saved


if __name__ == '__main__':
    unittest.main()
