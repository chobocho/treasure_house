# -*- coding: utf-8 -*-
"""tools/gover.py 의 시험 (PLAN.md §3.3, §0.10).

go 를 실제로 돌리는 시험은 하나뿐이다(맨 끝, 몇 초) — 나머지는 정규화·
작업 사본·명령 해석처럼 순수한 부분이다.

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

import gover  # noqa: E402


class Normalise(unittest.TestCase):
    def n(self, text, work='/s/work/07-x__go1.22'):
        return gover.normalise(text, work=work, scratch='/s')

    def test_other_work_copy_from_cache(self):
        # go fix -diff 의 출력은 GOCACHE 에서 나온다. 다른 작업 사본에서 만든
        # 캐시가 쓰이면 그 사본의 경로가 머리 줄에 남는다 — 그것도 /work 로.
        self.assertEqual(self.n('--- /s/work/try-p08-x/main.go (old)\n'),
                         '--- /work/main.go (old)\n')
        self.assertEqual(self.n('/s/work/08-y__go1.26/a.go:1\n'),
                         '/work/a.go:1\n')

    def test_work_and_scratch_paths(self):
        self.assertEqual(self.n('/s/work/07-x__go1.22/main.go:3:2: x\n'),
                         '/work/main.go:3:2: x\n')
        self.assertEqual(self.n('cache /s/gocache/ab\n'),
                         'cache /scratch/gocache/ab\n')

    def test_goroot(self):
        self.assertEqual(self.n(gover.GOROOT + '/src/runtime/panic.go:9\n'),
                         '$GOROOT/src/runtime/panic.go:9\n')

    def test_goroutine_id(self):
        self.assertEqual(self.n('goroutine 7 [running]:\n'),
                         'goroutine N [running]:\n')

    def test_addresses(self):
        self.assertEqual(self.n('main.f(0xc000012345, 0x3)\n'
                                '\t/work/main.go:8 +0x1c\n'),
                         'main.f(0xc…, 0x3)\n\t/work/main.go:8 +0x…\n')
        self.assertEqual(self.n('pc=0x4a1b2c sp=0x7fff fp=0x1\n'),
                         'pc=0x… sp=0x… fp=0x…\n')

    def test_small_hex_values_kept(self):
        # 프로그램이 찍은 값(0x3, 0xff)은 증거다 — 지우면 안 된다
        self.assertEqual(self.n('v=0xff\n'), 'v=0xff\n')

    def test_temp_build_dirs(self):
        self.assertEqual(self.n('/tmp/go-build123456/b001/exe/x\n'),
                         '/tmp/go-buildN/b001/exe/x\n')

    def test_benchmark_masks_time_and_iterations_keeps_allocs(self):
        got = self.n('BenchmarkSum-8   \t 1000000\t      1043 ns/op\t'
                     '      24 B/op\t       1 allocs/op\n')
        # 이름 꼬리(GOMAXPROCS)도 가린다 — test_benchmark_gomaxprocs_suffix
        self.assertEqual(got, 'BenchmarkSum-N   \t…\t… ns/op\t'
                              '      24 B/op\t       1 allocs/op\n')

    def test_benchmark_gomaxprocs_suffix(self):
        # 이 기기는 켜진 코어 수가 때마다 달라 -4 와 -8 이 번갈아 나왔다
        self.assertEqual(self.n('BenchmarkSum-8   \t…\t… ns/op\n'),
                         'BenchmarkSum-N   \t…\t… ns/op\n')
        self.assertEqual(self.n('BenchmarkA/sub-4 \t…\n'),
                         'BenchmarkA/sub-N \t…\n')

    def test_subtest_durations_indented(self):
        # 하위 시험 줄은 들여쓰기가 있다 — 이것도 가린다
        self.assertEqual(self.n('    --- PASS: TestA/b (0.00s)\n'),
                         '    --- PASS: TestA/b (…s)\n')

    def test_test_durations(self):
        self.assertEqual(self.n('--- PASS: TestA (0.00s)\n'
                                'ok  \tex/07/x\t0.012s\n'
                                'FAIL\tex/07/y\t1.5s\n'),
                         '--- PASS: TestA (…s)\n'
                         'ok  \tex/07/x\t…s\n'
                         'FAIL\tex/07/y\t…s\n')


class Command(unittest.TestCase):
    def test_leading_env_assignments(self):
        env, argv = gover.split_cmd('GOTOOLCHAIN=go1.26.0 go version')
        self.assertEqual(env, {'GOTOOLCHAIN': 'go1.26.0'})
        self.assertEqual(argv, ['go', 'version'])

    def test_lowercase_env_names(self):
        # http_proxy 처럼 소문자 이름의 환경 변수도 있다
        env, argv = gover.split_cmd('HTTP_PROXY=a http_proxy=b go run .')
        self.assertEqual(env, {'HTTP_PROXY': 'a', 'http_proxy': 'b'})
        self.assertEqual(argv, ['go', 'run', '.'])

    def test_quoted_args(self):
        env, argv = gover.split_cmd("go build -gcflags='-m -l' .")
        self.assertEqual(env, {})
        self.assertEqual(argv, ['go', 'build', '-gcflags=-m -l', '.'])

    def test_no_shell_features(self):
        for bad in ('go run . | head', 'go build && ls', 'go run . > x'):
            with self.assertRaises(ValueError):
                gover.split_cmd(bad)


class WorkCopy(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='gover-')
        self.src = os.path.join(self.root, 'ex', '07', 'x')
        os.makedirs(self.src)
        with io.open(os.path.join(self.src, 'go.mod'), 'w') as f:
            f.write('module ex/07/x\n\ngo 1.22\n')
        with io.open(os.path.join(self.src, 'main.go'), 'w') as f:
            f.write('package main\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_go_line_read(self):
        self.assertEqual(gover.mod_version(self.src), '1.22')

    def test_copy_rewrites_go_line_only_in_copy(self):
        dst = os.path.join(self.root, 'work', 'c')
        gover.prepare(self.src, dst, lang='1.21')
        with io.open(os.path.join(dst, 'go.mod')) as f:
            self.assertIn('\ngo 1.21\n', f.read())
        with io.open(os.path.join(self.src, 'go.mod')) as f:
            self.assertIn('\ngo 1.22\n', f.read())     # ex/ 는 그대로
        self.assertTrue(os.path.exists(os.path.join(dst, 'main.go')))

    def test_copy_replaces_old_copy(self):
        dst = os.path.join(self.root, 'work', 'c')
        os.makedirs(dst)
        with io.open(os.path.join(dst, 'stale.go'), 'w') as f:
            f.write('x')
        gover.prepare(self.src, dst)
        self.assertFalse(os.path.exists(os.path.join(dst, 'stale.go')))


class RealGo(unittest.TestCase):
    """진짜 go 로 한 번 — 언어 버전을 내리면 컴파일러가 거절하는가."""

    def test_lang_directive_is_enforced(self):
        root = tempfile.mkdtemp(prefix='gover-go-')
        try:
            src = os.path.join(root, 'ex', '07', 'r')
            os.makedirs(src)
            with io.open(os.path.join(src, 'go.mod'), 'w') as f:
                f.write('module ex/07/r\n\ngo 1.22\n')
            with io.open(os.path.join(src, 'main.go'), 'w') as f:
                f.write('package main\n\nimport "fmt"\n\nfunc main() {\n'
                        '\tfor i := range 3 {\n\t\tfmt.Print(i)\n\t}\n}\n')
            code, text = gover.execute(src, 'go run .', lang='1.21',
                                       scratch=os.path.join(root, 's'))
            self.assertEqual(code, 1)
            self.assertIn('requires go1.22 or later', text)
            # 컴파일 오류의 위치는 작업 디렉터리 기준 상대 경로로 나온다
            self.assertIn('./main.go:6:17: cannot range over 3', text)
            self.assertNotIn(root, text)
            code, text = gover.execute(src, 'go run .',
                                       scratch=os.path.join(root, 's'))
            self.assertEqual((code, text), (0, '012'))
        finally:
            shutil.rmtree(root)


if __name__ == '__main__':
    unittest.main()
