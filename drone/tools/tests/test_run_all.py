# -*- coding: utf-8 -*-
"""run_all 시험 — 캡처 이름·종료 코드·시간 지우기·표·manifest."""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BASE)
import run_all  # noqa: E402


class Fixture(unittest.TestCase):
    def setUp(self):
        self.saved = run_all.OUT
        run_all.OUT = tempfile.mkdtemp(prefix='out-')
        run_all.Ctx.taken = set()

    def tearDown(self):
        shutil.rmtree(run_all.OUT)
        run_all.OUT = self.saved

    def read(self, name):
        return io.open(os.path.join(run_all.OUT, name),
                       encoding='utf-8').read()


class Capture(Fixture):
    def test_command_line_first(self):
        c = run_all.Ctx('t')
        c.py('hello', '-c', 'print("안녕")')
        self.assertEqual(self.read('hello.txt'),
                         '$ python3 -c \'print("안녕")\'\n안녕\n')

    def test_duplicate_name_stops(self):
        c = run_all.Ctx('t')
        c.text('a', 'x')
        with self.assertRaises(RuntimeError):
            c.text('a', 'y')
        with self.assertRaises(RuntimeError):
            run_all.Ctx('u').text('a', 'z')     # 다른 묶음이라도

    def test_unexpected_exit_stops(self):
        c = run_all.Ctx('t')
        with self.assertRaises(RuntimeError):
            c.py('boom', '-c', 'import sys; sys.exit(3)')

    def test_expected_failure_is_recorded(self):
        c = run_all.Ctx('t')
        c.py('boom', '-c', 'import sys; sys.exit(3)', expect=3)
        self.assertTrue(self.read('boom.txt').endswith('[exit 3]\n'))

    def test_timing_stripped(self):
        c = run_all.Ctx('t')
        c.py('tm', '-c', 'print("✔ a (2.5ms)"); print("ℹ duration_ms 9")',
             strip_timing=True)
        self.assertNotIn('ms', self.read('tm.txt').split('\n', 1)[1])


class Tables(Fixture):
    def test_table_html(self):
        c = run_all.Ctx('t')
        c.table('x', ['이름', '값'], [['a<b', 1.5]], caption='캡션',
                num=(1,))
        t = self.read('tbl_x.html')
        self.assertIn('<caption>캡션</caption>', t)
        self.assertIn('<th class="num">값</th>', t)
        self.assertIn('<td>a&lt;b</td><td class="num">1.5</td>', t)


class Manifest(Fixture):
    def test_manifest_skips_bookkeeping(self):
        c = run_all.Ctx('t')
        c.text('a', 'x')
        run_all.save_batches({'t': ['a.txt']})
        self.assertEqual(sorted(run_all.manifest()), ['a.txt'])

    def test_clear_batch(self):
        c = run_all.Ctx('t')
        c.text('a', 'x')
        run_all.save_batches({'t': ['a.txt']})
        run_all.clear_batch('t')
        self.assertFalse(os.path.exists(os.path.join(run_all.OUT,
                                                     'a.txt')))

    def test_width_problem(self):
        run_all.Ctx('t').text('w', 'x' * 201)
        self.assertEqual(len(run_all.width_problems()), 1)


if __name__ == '__main__':
    unittest.main()
