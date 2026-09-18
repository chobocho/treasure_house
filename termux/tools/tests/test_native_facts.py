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
    # 측정(timeit)은 시험에서 돌리지 않는다 — 인자만 되받아 적는다
    'python3': 'echo "python3 $*"',
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
        # 실험 빌드는 없는 곳을 가리킨다 — 진짜 바이너리를 돌리지 않게
        env = dict(os.environ, PATH=self.d + ':' + os.environ['PATH'],
                   NATIVE_BUILD=os.path.join(self.d, 'nobuild'))
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

    def test_experiment_sections(self):
        # 5단계의 bionic 실험을 네이티브에서 돌리는 절. 빌드가 없으면
        # 없다고 적고 넘어간다 — 조용히 빠지지 않는다.
        self.run_it()
        text = io.open(self.out).read()
        for h in ('bind_port --scan 1 1100', 'paths',
                  'shebang/run.sh (termux-exec 켬)',
                  'shebang/run.sh (LD_PRELOAD 뺌)',
                  "grep ' /storage/emulated ' /proc/mounts",
                  'echo "$LD_PRELOAD"',
                  'timeit_exp.py -n 3 -- sh exp/fork_loop.sh 100',
                  'timeit_exp.py -n 3 -- syscall_loop 200000 getcwd'):
            self.assertIn(h, text)

    def test_api_sections_are_read_only_and_bounded(self):
        # proot 에서는 Termux:API 가 답하지 않는다(6단계). 읽기만 하는
        # 명령을 20초 제한으로 네이티브에서 뜬다. 화면에 흔적을 남기는
        # 명령(토스트·진동·알림)과 개인정보 명령은 넣지 않는다.
        self.run_it()
        text = io.open(self.out).read()
        for h in ('termux-battery-status', 'termux-sensor -l',
                  'termux-camera-info', 'termux-wifi-connectioninfo'):
            self.assertIn('timeout 20 ' + h, text)
        src = io.open(SCRIPT).read()
        for bad in ('termux-toast', 'termux-vibrate',
                    'termux-notification', 'termux-location',
                    'termux-sms', 'termux-clipboard'):
            self.assertNotIn(bad, src)

    def test_missing_build_is_reported(self):
        env = dict(os.environ, PATH=self.d + ':' + os.environ['PATH'],
                   NATIVE_BUILD=os.path.join(self.d, 'nope'))
        subprocess.run(['sh', SCRIPT, self.out], env=env,
                       capture_output=True, text=True)
        self.assertIn('(빌드 없음', io.open(self.out).read())

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
        r = subprocess.run(['sh', SCRIPT], capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
