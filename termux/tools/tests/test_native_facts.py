# -*- coding: utf-8 -*-
"""native_facts.sh 시험 — 사용자가 네이티브 Termux 에서 한 번 돌리는 것.

proot 안에서는 getprop 이 막히고 id·uname 이 proot 의 값이다
(PLAN.md 진행 기록 2단계). 그래서 이 스크립트만은 사용자가 직접
돌린다. 시험은 가짜 명령(getprop·settings·termux-info)을 PATH 앞에
세워, 절 머리와 순서, 그리고 읽기 전용 명령만 부른다는 것을 본다.
"""
import io
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'native_facts.sh')

FAKES = {
    'getprop': 'echo "prop:$1"',
    'settings': 'echo "settings:$*"',
    'termux-info': 'echo "info-line"',
}


class NativeFactsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for name, body in FAKES.items():
            p = os.path.join(self.d, name)
            io.open(p, 'w').write('#!/bin/sh\n%s\n' % body)
            os.chmod(p, stat.S_IRWXU)
        self.out = os.path.join(self.d, 'device.txt')

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_it(self):
        env = dict(os.environ, PATH=self.d + ':' + os.environ['PATH'])
        return subprocess.run(['sh', SCRIPT, self.out], env=env,
                              capture_output=True, text=True)

    def test_sections_in_order(self):
        r = self.run_it()
        self.assertEqual(r.returncode, 0, r.stderr)
        text = io.open(self.out).read()
        heads = re.findall(r'^== \d+\. (.*) ==$', text, re.M)
        self.assertEqual(heads[:4], [
            'getprop ro.build.version.release',
            'getprop ro.build.version.sdk',
            'settings get global settings_enable_monitor_phantom_procs',
            'getprop ro.product.cpu.abi'])
        self.assertIn('prop:ro.build.version.sdk', text)
        self.assertIn('info-line', text)
        self.assertIn('== ', text)

    def test_identity_sections_present(self):
        self.run_it()
        text = io.open(self.out).read()
        for h in ('id', 'uname -a', 'TracerPid'):
            self.assertIn(h, text)

    def test_first_line_names_the_side(self):
        self.run_it()
        first = io.open(self.out).readline()
        self.assertTrue(first.startswith('# native_facts '), first)

    def test_only_read_only_commands(self):
        src = io.open(SCRIPT).read()
        body = '\n'.join(l for l in src.split('\n')
                         if not l.lstrip().startswith('#'))
        for bad in ('settings put', 'setprop', 'pkg ', 'apt ', 'rm ',
                    'am ', 'termux-reset'):
            self.assertNotIn(bad, body)

    def test_missing_argument(self):
        r = subprocess.run(['sh', SCRIPT], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
