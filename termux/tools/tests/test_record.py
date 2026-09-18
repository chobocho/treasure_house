# -*- coding: utf-8 -*-
"""record.sh 시험 — stable 캡처만 세 번 같아야 한다.

가짜 run_all.py 를 끼운 임시 디렉터리에서 돌린다. 가짜는 부를
때마다 stable 파일 하나는 같게, snapshot 파일 하나는 다르게 쓴다.
record.sh --check 는 snapshot 을 대조에서 빼야 통과하고, stable 이
흔들리면 실패해야 한다.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'record.sh')

FAKE = '''import io, os, time
n = int(io.open('count').read()) if os.path.exists('count') else 0
io.open('count', 'w').write(str(n + 1))
io.open('out/a.txt', 'w').write('same\\n')
io.open('out/snap.txt', 'w').write('# snapshot 2026-09-18\\n%d\\n' % n)
io.open('out/b.txt', 'w').write('%s\\n' % (n if os.environ.get('FLAKY')
                                           else 'fixed'))
'''
MAN = {'a.txt': {'kind': 'stable', 'side': 'termux'},
       'b.txt': {'kind': 'stable', 'side': 'termux'},
       'snap.txt': {'kind': 'snapshot', 'side': 'termux',
                    'date': '2026-09-18'}}


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, 'out'))
        io.open(os.path.join(self.d, 'run_all.py'), 'w').write(FAKE)
        io.open(os.path.join(self.d, 'out', 'manifest.json'),
                'w').write(json.dumps(MAN))
        subprocess.run([sys.executable, 'run_all.py'], cwd=self.d,
                       check=True)

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_it(self, flaky=False):
        env = dict(os.environ, RECORD_BASE=self.d, PY=sys.executable)
        if flaky:
            env['FLAKY'] = '1'
        return subprocess.run(['sh', SCRIPT, '--check'], env=env,
                              capture_output=True, text=True)

    def test_snapshot_changes_are_ignored(self):
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('stable 캡처 2개가 3회차까지 같다', r.stdout)

    def test_flaky_stable_fails_and_names_file(self):
        r = self.run_it(flaky=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn('out/b.txt', r.stdout)

    def test_runs_three_times_in_total(self):
        self.run_it()
        # setUp 에서 한 번 + record.sh 가 두 번 더
        self.assertEqual(io.open(os.path.join(self.d, 'count')).read(),
                         '3')


if __name__ == '__main__':
    unittest.main()
