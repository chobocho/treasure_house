# -*- coding: utf-8 -*-
"""exp/ 시험 — 같은 C 소스를 두 libc 로 짓고, 성질을 확인한다.

C 실험은 두 번 컴파일한다(PLAN.md §9 결정 10).
  glibc  — proot 의 gcc   → scratch/build/glibc/
  bionic — Termux 의 clang(tools/tmx.sh 경유) → scratch/build/bionic/
플래그는 둘 다 -std=c99 -Wall -Wextra -Werror -D_DEFAULT_SOURCE.

**여기서 도는 bionic 바이너리도 proot 의 ptrace 아래다.** 그래서
시험은 proot 안에서도 참인 성질만 단언한다(파일시스템이 우분투의
것으로 보이는 일 따위는 단언하지 않는다). 네이티브에서만 참인 것은
tools/native_facts.sh 가 사용자의 손으로 뜬다.
"""
import io
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BASE = os.path.dirname(EXP)
sys.path.insert(0, os.path.join(BASE, 'py'))
import elf                                         # noqa: E402

TMX = os.path.join(BASE, 'tools', 'tmx.sh')
BUILD = os.path.join(BASE, 'scratch', 'build')
PREFIX = '/data/data/com.termux/files/usr'
HOME_T = '/data/data/com.termux/files/home'
HAVE_TERMUX = os.access(os.path.join(PREFIX, 'bin', 'clang'), os.X_OK)
CFLAGS = ['-std=c99', '-Wall', '-Wextra', '-Werror',
          '-D_DEFAULT_SOURCE']
C_FILES = ['hello', 'passwd', 'paths', 'bind_port', 'syscall_loop']


def build(side, name):
    """두 컴파일러 중 하나로 exp/<name>.c 를 짓는다. 경고도 실패다."""
    out = os.path.join(BUILD, side, name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    src = os.path.join(EXP, name + '.c')
    if side == 'glibc':
        subprocess.run(['gcc'] + CFLAGS + [src, '-o', out], check=True,
                       capture_output=True)
    else:
        cmd = 'clang %s %s -o %s' % (' '.join(CFLAGS), src, out)
        r = subprocess.run(['sh', TMX, '--', cmd], capture_output=True,
                           text=True)
        if r.returncode != 0:
            raise AssertionError('clang 실패: ' + r.stdout + r.stderr)
    return out


def run(side, name, *args):
    """짓고 돌린다. bionic 은 tmx.sh 로(Termux 의 환경에서) 돌린다."""
    exe = build(side, name)
    if side == 'glibc':
        r = subprocess.run([exe] + list(args), capture_output=True,
                           text=True)
        return r.returncode, r.stdout
    r = subprocess.run(['sh', TMX, '--', ' '.join([exe] + list(args))],
                       capture_output=True, text=True)
    out = r.stdout.rsplit('## tmx:', 1)[0]
    return r.returncode, out


SIDES = ['glibc'] + (['bionic'] if HAVE_TERMUX else [])


class BuildScriptTest(unittest.TestCase):
    def test_builds_all_five_with_gcc(self):
        d = tempfile.mkdtemp()
        try:
            r = subprocess.run(['sh', os.path.join(EXP, 'build.sh'),
                                'gcc', d], cwd=BASE,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(os.listdir(d)), sorted(C_FILES))
            self.assertEqual(len(r.stdout.strip().split('\n')), 5)
        finally:
            shutil.rmtree(d)

    def test_compiler_error_stops(self):
        r = subprocess.run(['sh', os.path.join(EXP, 'build.sh'),
                            'false', tempfile.gettempdir()], cwd=BASE,
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


class HelloTest(unittest.TestCase):
    def test_same_greeting_different_libc(self):
        outs = {s: run(s, 'hello')[1].split('\n') for s in SIDES}
        self.assertEqual(outs['glibc'][0], 'hello, termux')
        self.assertEqual(outs['glibc'][1], 'libc: glibc')
        if 'bionic' in outs:
            self.assertEqual(outs['bionic'][0], outs['glibc'][0])
            self.assertEqual(outs['bionic'][1], 'libc: bionic')
            self.assertTrue(
                outs['bionic'][2].startswith('android api:'))

    def test_interpreters_differ(self):
        g = elf.read(build('glibc', 'hello'))
        self.assertTrue(g['interp'].startswith('/lib/ld-linux'))
        if HAVE_TERMUX:
            b = elf.read(build('bionic', 'hello'))
            self.assertEqual(b['interp'], '/system/bin/linker64')


class PasswdTest(unittest.TestCase):
    def test_glibc_reads_etc_passwd(self):
        _rc, out = run('glibc', 'passwd', '0', '10123')
        self.assertIn('uid 0: name=root', out)
        self.assertIn('uid 10123: (없음)', out)

    @unittest.skipUnless(HAVE_TERMUX, 'Termux 가 없다')
    def test_bionic_synthesizes_app_names_and_termux_home(self):
        # 앱 uid 는 bionic 이 u0_aNNN 으로 이름을 지어내고, 집과 셸은
        # termux-packages 의 ndk-patches pwd.h 가 Termux 경로로 바꾼다.
        _rc, out = run('bionic', 'passwd', '10123', '2000')
        self.assertIn('uid 10123: name=u0_a123 dir=%s' % HOME_T, out)
        self.assertIn('uid 2000: name=shell', out)

    def test_default_is_own_uid(self):
        _rc, out = run('glibc', 'passwd')
        self.assertTrue(out.startswith('uid %d:' % os.getuid()))


class PathsTest(unittest.TestCase):
    def test_answers(self):
        for s in SIDES:
            _rc, out = run(s, 'paths', '/nonexistent', '/bin/sh',
                           '/proc/self')
            self.assertIn('/nonexistent: 없음 ENOENT', out)
            self.assertIn('/bin/sh: 있음 실행 가능', out)
            self.assertIn('/proc/self: 있음', out)


class BindTest(unittest.TestCase):
    def test_free_range_is_one_line(self):
        for s in SIDES:
            _rc, out = run(s, 'bind_port', '--scan', '40100', '40105')
            self.assertEqual(out.strip(), '40100-40105: ok')

    def test_port_in_use(self):
        held = socket.socket()
        held.bind(('127.0.0.1', 0))
        held.listen(1)
        port = held.getsockname()[1]
        try:
            for s in SIDES:
                _rc, out = run(s, 'bind_port', str(port))
                self.assertEqual(out.strip(),
                                 '%d: EADDRINUSE' % port)
        finally:
            held.close()


class SyscallLoopTest(unittest.TestCase):
    def test_count(self):
        for s in SIDES:
            rc, out = run(s, 'syscall_loop', '1000')
            self.assertEqual(rc, 0)
            self.assertEqual(out.strip(), 'getpid 1000번')

    def test_bad_argument(self):
        rc, _out = run('glibc', 'syscall_loop', 'x')
        self.assertEqual(rc, 2)

    def test_getcwd_mode(self):
        # proot 의 seccomp 목록에 있는 호출(getcwd)과 없는 호출
        # (getpid)을 나란히 재려고 둘째 인자로 고른다(9부)
        for s in SIDES:
            rc, out = run(s, 'syscall_loop', '1000', 'getcwd')
            self.assertEqual(rc, 0)
            self.assertEqual(out.strip(), 'getcwd 1000번')

    def test_explicit_getpid_mode(self):
        rc, out = run('glibc', 'syscall_loop', '5', 'getpid')
        self.assertEqual((rc, out.strip()), (0, 'getpid 5번'))

    def test_zero_and_unknown_mode(self):
        rc, out = run('glibc', 'syscall_loop', '0', 'getcwd')
        self.assertEqual((rc, out.strip()), (0, 'getcwd 0번'))
        rc, _out = run('glibc', 'syscall_loop', '10', 'open')
        self.assertEqual(rc, 2)
        rc, _out = run('glibc', 'syscall_loop', '10', 'getcwd', 'x')
        self.assertEqual(rc, 2)


class TimeitTest(unittest.TestCase):
    def test_median(self):
        sys.path.insert(0, EXP)
        import timeit_exp
        self.assertEqual(timeit_exp.median([5, 1, 3]), 3)
        self.assertEqual(timeit_exp.median([4, 1, 3, 2]), 2.5)

    def test_runs_three_times(self):
        r = subprocess.run([sys.executable,
                            os.path.join(EXP, 'timeit_exp.py'), '-n',
                            '3', '--', 'true'], capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0)
        self.assertRegex(r.stdout, r'^runs=3 median_ms=\d+\.\d{3}\n$')


class ForkLoopTest(unittest.TestCase):
    def test_count(self):
        r = subprocess.run(['sh', os.path.join(EXP, 'fork_loop.sh'),
                            '20'], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), 'true 를 20번 실행했다')


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def fake(self, name, body):
        p = os.path.join(self.d, name)
        io.open(p, 'w').write('#!/bin/sh\n%s\n' % body)
        os.chmod(p, stat.S_IRWXU)

    def sh(self, script, *args):
        env = dict(os.environ, PATH=self.d + ':' + os.environ['PATH'])
        return subprocess.run(['sh', os.path.join(EXP, script)]
                              + list(args), capture_output=True,
                              text=True, env=env)

    def test_pkg_diff_fills_placeholders(self):
        src = os.path.join(self.d, 'pkg.in')
        inst = os.path.join(self.d, 'pkg')
        io.open(src, 'w').write('#!/bin/bash\nP=@TERMUX_PREFIX@\n'
                                'A=@TERMUX_APP_PACKAGE@\n'
                                'C=@TERMUX_CACHE_DIR@\n'
                                'V=@PACKAGE_VERSION@\n')
        io.open(inst, 'w').write('#!/bin/bash\nP=/pre\nA=com.termux\n'
                                 'C=/data/data/com.termux/cache\n'
                                 'V=9.9\n')
        env = dict(os.environ, PREFIX='/pre')
        r = subprocess.run(['sh', os.path.join(EXP, 'pkg_diff.sh'),
                            src, inst, '9.9'], capture_output=True,
                           text=True, env=env)
        self.assertEqual(r.stdout.strip().split('\n')[-1],
                         'diff 종료 0')

    def test_pkg_diff_shows_difference(self):
        src = os.path.join(self.d, 'pkg.in')
        inst = os.path.join(self.d, 'pkg')
        io.open(src, 'w').write('#!/bin/bash\n')
        io.open(inst, 'w').write('#!/pre/bin/bash\n')
        env = dict(os.environ, PREFIX='/pre')
        r = subprocess.run(['sh', os.path.join(EXP, 'pkg_diff.sh'),
                            src, inst, '1'], capture_output=True,
                           text=True, env=env)
        self.assertIn('> #!/pre/bin/bash', r.stdout)
        self.assertIn('diff 종료 1', r.stdout)

    def test_signals_137(self):
        r = self.sh('signals.sh')
        self.assertIn('종료 상태 137 = 128 + 9(SIGKILL)', r.stdout)

    def test_api_call_reads_method_from_installed_script(self):
        # 설치된 termux-battery-status 는 termux-api 에 메서드 이름
        # 하나를 넘길 뿐이다. api_call.sh 는 그 이름을 스크립트에서
        # 읽어 termux-api 를 직접 부른다 — 이름을 손으로 적지 않는다.
        self.fake('termux-battery-status',
                  '/x/libexec/termux-api BatteryStatus')
        api = os.path.join(self.d, 'api')
        io.open(api, 'w').write('#!/bin/sh\necho "called: $*"\n')
        os.chmod(api, stat.S_IRWXU)
        env = dict(os.environ, PATH=self.d + ':' + os.environ['PATH'],
                   TERMUX_API=api)
        r = subprocess.run(['sh', os.path.join(EXP, 'api_call.sh')],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('메서드 이름: BatteryStatus', r.stdout)
        self.assertIn('called: BatteryStatus', r.stdout)

    def test_wakelock_unlocks_even_on_failure(self):
        log = os.path.join(self.d, 'log')
        self.fake('termux-wake-lock', 'echo lock >> %s' % log)
        self.fake('termux-wake-unlock', 'echo unlock >> %s' % log)
        r = self.sh('wakelock.sh', 'false')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(io.open(log).read(), 'lock\nunlock\n')
        self.assertIn('termux-wake-lock 종료 코드 0', r.stdout)

    def test_shebang_runner_reports_each_script(self):
        r = self.sh('shebang/run.sh')
        lines = [l for l in r.stdout.split('\n') if l]
        self.assertEqual([l.split(':')[0] for l in lines],
                         ['bin_sh.sh', 'env_sh.sh', 'prefix_sh.sh'])
        for l in lines:
            self.assertRegex(l, r'^\S+: 종료 \d+ · ')


class MissingLibTest(unittest.TestCase):
    # 실험 12 — 공유 라이브러리를 지운 뒤 실행하면 링커가 무엇이라
    # 하는가(15부). bionic 은 "CANNOT LINK EXECUTABLE", glibc 는
    # "error while loading shared libraries".
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_it(self, cc, d):
        script = os.path.join(EXP, 'missing_lib.sh')
        return subprocess.run(['sh', script, cc, d],
                              capture_output=True, text=True)

    def test_glibc_message(self):
        r = self.run_it('gcc', self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], '있을 때: gone 이 불렸다')
        self.assertIn('libgone.so', lines[1])
        self.assertIn('error while loading shared libraries', lines[1])
        self.assertRegex(lines[2], r'^종료 \d+$')
        self.assertNotEqual(lines[2], '종료 0')
        # 지운 뒤 디렉터리에는 실행 파일만 남는다
        self.assertEqual(sorted(os.listdir(self.d)), ['use_gone'])

    @unittest.skipUnless(HAVE_TERMUX, 'Termux clang 이 없다')
    def test_bionic_message(self):
        d = os.path.join(BASE, 'scratch', 'missing_t')
        shutil.rmtree(d, ignore_errors=True)
        rel = os.path.relpath(d, BASE)
        r = subprocess.run(['sh', TMX, '--', 'sh exp/missing_lib.sh '
                            'clang ' + rel], capture_output=True,
                           text=True)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], '있을 때: gone 이 불렸다')
        self.assertIn('CANNOT LINK EXECUTABLE', lines[1])
        self.assertIn('libgone.so', lines[1])
        shutil.rmtree(d, ignore_errors=True)

    def test_usage(self):
        r = subprocess.run(['sh', os.path.join(EXP, 'missing_lib.sh')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless(shutil.which('curl'), 'curl 이 없다')
class ServeOnceTest(unittest.TestCase):
    # 실험 11 — 127.0.0.1 에 웹 서버를 띄워 한 번 묻고 끈다(11부)
    def setUp(self):
        self.d = tempfile.mkdtemp()
        io.open(os.path.join(self.d, 'a.txt'), 'w').write('x' * 37)

    def tearDown(self):
        shutil.rmtree(self.d)

    def free_port(self):
        import socket
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def serve(self, *args):
        return subprocess.run(['sh', os.path.join(EXP, 'serve_once.sh')]
                              + list(args), capture_output=True,
                              text=True, timeout=60)

    def test_status_and_size(self):
        port = self.free_port()
        r = self.serve(str(port), self.d, 'a.txt')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, '200 37\n')
        # 끈 뒤에는 그 포트가 비어 있다 — 다시 bind 할 수 있다
        import socket
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
        s.close()

    def test_missing_file_is_404(self):
        r = self.serve(str(self.free_port()), self.d, 'none.txt')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith('404 '), r.stdout)

    def test_usage(self):
        self.assertEqual(self.serve().returncode, 2)
        self.assertEqual(self.serve('80').returncode, 2)


@unittest.skipUnless(shutil.which('dpkg-deb'), 'dpkg-deb 가 없다')
class MkdebTest(unittest.TestCase):
    def test_build(self):
        sys.path.insert(0, os.path.join(BASE, 'py'))
        import deb
        d = tempfile.mkdtemp()
        try:
            r = subprocess.run(['sh', os.path.join(EXP, 'mkdeb',
                                                   'build.sh'), d],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            info = deb.read(os.path.join(d,
                                         'treasure-hello_1.0_all.deb'))
            self.assertEqual(info['control']['Package'],
                             'treasure-hello')
            self.assertIn(PREFIX + '/bin/treasure-hello', info['files'])
        finally:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
