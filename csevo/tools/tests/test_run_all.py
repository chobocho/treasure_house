# -*- coding: utf-8 -*-
"""run_all.py 의 시험 — 캡처 이름·첫 줄·기대 종료 코드·이름 겹침·묶음 지우기.

dotnet 을 돌리지 않는다: csver.execute 를 가짜로 바꿔 끼운다.
(goevo/tools/tests/test_run_all.py 를 C# 에 맞춰 옮긴 것.)

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

CSPROJ = ('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n'
          '    <OutputType>Exe</OutputType>\n'
          '    <TargetFramework>net10.0</TargetFramework>\n'
          '    <LangVersion>9.0</LangVersion>\n'
          '  </PropertyGroup>\n</Project>\n')
ERR = ("Program.cs(1,1): error CS8400: Feature 'records' is not available "
       "in C# 8.0. Please use language version 9.0 or greater.\n")


class Fake(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='runall-')
        self.saved = (run_all.OUT, run_all.BASE, run_all.csver.execute)
        run_all.OUT = os.path.join(self.root, 'out')
        run_all.BASE = self.root
        os.makedirs(run_all.OUT)
        ex = os.path.join(self.root, 'ex', '10', 'rec')
        os.makedirs(ex)
        with io.open(os.path.join(ex, 'ex.csproj'), 'w') as f:
            f.write(CSPROJ)
        self.calls = []

        def fake(src, cmd, v=None, flags=None, env=None, name=None):
            self.calls.append((cmd, v, flags, env, name))
            if v == '8.0':
                return 1, ERR
            return 0, 'P { X = 1 }'
        run_all.csver.execute = fake
        run_all.Ctx.taken = set()
        self.ctx = run_all.Ctx('p10')

    def tearDown(self):
        run_all.OUT, run_all.BASE, run_all.csver.execute = self.saved
        shutil.rmtree(self.root)

    def read(self, name):
        with io.open(os.path.join(run_all.OUT, name), encoding='utf-8') as f:
            return f.read()

    def test_default_version_from_csproj_is_written_out(self):
        # 캡처 첫 줄은 언제나 언어 버전을 밝힌다 — csproj 의 값이라도
        self.ctx.cs('ex/10/rec')
        self.assertEqual(self.read('10-rec__cs9.0.txt'),
                         '$ csrun -langversion:9.0\nP { X = 1 }\n')
        self.assertEqual(self.calls[0][1], '9.0')

    def test_lang_downgrade_expected_failure(self):
        self.ctx.cs('ex/10/rec', v='8.0', expect=1)
        self.assertEqual(self.read('10-rec__cs8.0.txt'),
                         '$ csrun -langversion:8.0\n' + ERR + '[exit 1]\n')

    def test_unexpected_exit_stops(self):
        with self.assertRaises(RuntimeError):
            self.ctx.cs('ex/10/rec', v='8.0')          # 기대는 0 인데 1

    def test_env_and_flags_in_first_line_and_name(self):
        self.ctx.cs('ex/10/rec', env='DOTNET_TieredPGO=0',
                    flags='-nullable:enable', tag='nrt')
        self.assertTrue(self.read('10-rec__cs9.0-env-dotnet_tieredpgo-0-nrt.txt')
                        .startswith('$ DOTNET_TieredPGO=0 csrun '
                                    '-langversion:9.0 -nullable:enable\n'))
        self.assertEqual(self.calls[0][2:4],
                         ('-nullable:enable', 'DOTNET_TieredPGO=0'))

    def test_name_collision_stops(self):
        self.ctx.cs('ex/10/rec')
        with self.assertRaises(RuntimeError):
            self.ctx.cs('ex/10/rec', cmd='csrun -- x')    # tag 없이 같은 이름

    def test_batch_files_recorded_and_cleared(self):
        self.ctx.cs('ex/10/rec')
        run_all.save_batches({'p10': sorted(self.ctx.written)})
        with io.open(os.path.join(run_all.OUT, 'batches.json')) as f:
            self.assertEqual(json.load(f), {'p10': ['10-rec__cs9.0.txt']})
        run_all.clear_batch('p10')
        self.assertFalse(os.path.exists(
            os.path.join(run_all.OUT, '10-rec__cs9.0.txt')))


class ConcurrentBatches(Fake):
    """서브에이전트 둘이 각자 --only 로 돌리면 batches.json 을 같이 고친다.
    한쪽이 시작할 때 읽은 사본으로 끝에 덮어쓰면 다른 쪽 항목이 사라졌다
    (2026-10-01, p04 가 p04b 의 항목을 지웠다)."""

    def test_only_run_keeps_key_written_meanwhile(self):
        exps = os.path.join(self.root, 'exps')
        os.makedirs(exps)
        with io.open(os.path.join(exps, 'ORDER'), 'w') as f:
            f.write('pA\npB\n')
        open(os.path.join(exps, 'pA.py'), 'w').close()
        run_all.save_batches({'pA': ['old.txt']})

        class Mod(object):
            @staticmethod
            def run(ctx):
                # 이 묶음이 도는 사이 다른 프로세스가 pB 를 적는다
                run_all.save_batches({'pA': ['old.txt'], 'pB': ['b.txt']})
                ctx.cs('ex/10/rec')
        saved = (run_all.HERE, run_all.importlib.import_module)
        run_all.HERE = self.root
        run_all.importlib.import_module = lambda name: Mod
        try:
            run_all.run('pA')
        finally:
            run_all.HERE, run_all.importlib.import_module = saved
        with io.open(os.path.join(run_all.OUT, 'batches.json')) as f:
            self.assertEqual(json.load(f), {'pA': ['10-rec__cs9.0.txt'],
                                            'pB': ['b.txt']})


class VanishingCapture(unittest.TestCase):
    """다른 묶음이 제 캡처를 지우는 사이에 listdir 와 open 이 끼면
    FileNotFoundError 로 manifest 를 못 쓰고 끝났다(2026-10-02 p10b·p10c)."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='runall-gone-')
        self.saved = (run_all.OUT, os.listdir)
        run_all.OUT = self.root
        with io.open(os.path.join(self.root, 'a.txt'), 'w') as f:
            f.write('ok\n')
        real = os.listdir

        def listdir_with_ghost(path):
            # 목록에는 있었는데 열기 전에 지워진 캡처
            return real(path) + ['gone.txt', 'gone.html']
        os.listdir = listdir_with_ghost

    def tearDown(self):
        run_all.OUT, os.listdir = self.saved
        shutil.rmtree(self.root)

    def test_width_problems_skips_vanished(self):
        self.assertEqual(run_all.width_problems(), [])

    def test_manifest_skips_vanished(self):
        self.assertEqual(sorted(run_all.manifest()), ['a.txt'])


class FullRunGuard(unittest.TestCase):
    def test_bare_run_refuses(self):
        # 인자 없이 돌리면 모든 묶음의 캡처를 먼저 지운다 — goevo 에서
        # 서브에이전트가 그렇게 돌려 캡처가 사라졌다. 전체는 --all 로만.
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
