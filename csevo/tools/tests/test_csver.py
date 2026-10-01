# -*- coding: utf-8 -*-
"""tools/csver.py 의 시험 — csproj 읽기, 명령 줄, 정규화, 검사 캐시 열쇠.

dotnet 을 돌리는 시험은 두지 않는다(느리고 메모리를 먹는다). 진짜로
돌리는 것은 make examples-check 와 run_all.py 다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import csver   # noqa: E402

CSPROJ = ('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n'
          '    <OutputType>Exe</OutputType>\n'
          '    <TargetFramework>net10.0</TargetFramework>\n'
          '    <LangVersion>8.0</LangVersion>\n'
          '    <Nullable>enable</Nullable>\n'
          '    <ImplicitUsings>disable</ImplicitUsings>\n'
          '  </PropertyGroup>\n</Project>\n')


class Csproj(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix='csver-')
        with io.open(os.path.join(self.d, 'ex.csproj'), 'w') as f:
            f.write(CSPROJ)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_props(self):
        p = csver.csproj_props(self.d)
        self.assertEqual(p['LangVersion'], '8.0')
        self.assertEqual(p['Nullable'], 'enable')
        self.assertEqual(csver.lang_version(self.d), '8.0')

    def test_missing_langversion_is_an_error(self):
        # 예제마다 언어 버전을 못 박는다 — 기본값(latest)에 기대면 SDK 를
        # 올리는 날 캡처가 조용히 바뀐다
        with io.open(os.path.join(self.d, 'ex.csproj'), 'w') as f:
            f.write(CSPROJ.replace('    <LangVersion>8.0</LangVersion>\n',
                                   ''))
        with self.assertRaises(ValueError):
            csver.lang_version(self.d)


class Argv(unittest.TestCase):
    def test_csrun_gets_version_then_flags_then_rest(self):
        env, argv = csver.build_argv('csrun -- 3 4', v='7.3',
                                     flags='-unsafe', env='A=1')
        self.assertEqual(env, {'A': '1'})
        self.assertEqual(argv, [csver.CSRUN, '-langversion:7.3', '-unsafe',
                                '--', '3', '4'])

    def test_other_commands_untouched(self):
        env, argv = csver.build_argv('dotnet --version', v='14.0',
                                     flags='-unsafe')
        self.assertEqual(argv, ['dotnet', '--version'])

    def test_shell_features_refused(self):
        with self.assertRaises(ValueError):
            csver.build_argv('csrun | head')


class Normalise(unittest.TestCase):
    def test_work_and_scratch_paths(self):
        t = csver.normalise('at P.M() in /s/work/x/Program.cs:line 3\n'
                            '/s/home/.dotnet\n', '/s/work/x', '/s')
        self.assertEqual(t, 'at P.M() in /work/Program.cs:line 3\n'
                            '/scratch/home/.dotnet\n')

    def test_long_hex_addresses_masked_short_kept(self):
        t = csver.normalise('ptr 0x00007FFF5A3C1D20 flag 0xFF\n', '/w', '/s')
        self.assertEqual(t, 'ptr 0x… flag 0xFF\n')

    def test_crlf(self):
        self.assertEqual(csver.normalise('a\r\nb\r\n', '/w', '/s'), 'a\nb\n')


class CheckKey(unittest.TestCase):
    def test_key_changes_with_source_and_flags(self):
        d = tempfile.mkdtemp(prefix='csver-')
        try:
            with io.open(os.path.join(d, 'Program.cs'), 'w') as f:
                f.write('class P {}\n')
            with io.open(os.path.join(d, 'ex.csproj'), 'w') as f:
                f.write(CSPROJ)
            k1 = csver.check_key(d)
            self.assertEqual(k1, csver.check_key(d))
            with io.open(os.path.join(d, 'Program.cs'), 'a') as f:
                f.write('// x\n')
            self.assertNotEqual(k1, csver.check_key(d))
        finally:
            shutil.rmtree(d)


class RunsThroughTheLock(unittest.TestCase):
    # _run 은 시험에서 한 번도 안 돌았다 — 그 안의 줄이 깨져(주석이 접혀
    # 맨 낱말이 코드 줄로 떨어짐) run_all 이 NameError 로 멈춘 일이 있다.
    # dotnet 대신 true 를 돌려 잠금·서브프로세스 길만 지난다.
    def test_run_trivial_command(self):
        p = csver._run(['true'], tempfile.gettempdir(),
                       {'PATH': os.environ.get('PATH', '')})
        self.assertEqual(p.returncode, 0)


if __name__ == '__main__':
    unittest.main()
