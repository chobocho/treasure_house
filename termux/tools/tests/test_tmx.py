# -*- coding: utf-8 -*-
"""tmx.sh 시험 — 호스트 Termux 로 가는 유일한 문 (PLAN.md §2.1).

두 가지를 본다.
  1. 거부 목록(§0.7·§0.8)의 명령은 **실행되지 않고** 99 로 끝난다.
     "실행되지 않았다" 는 같은 줄 뒤에 붙인 touch 가 표지 파일을
     만들지 못했다는 것으로 확인한다 — 종료 코드만 보면 거부한 척하고
     실행해 버린 경우를 못 잡는다.
  2. 허용된 명령은 돌고, 마지막 줄에 `## tmx: side=… cwd=… exit=N`
     이 붙으며, tmx.sh 의 종료 코드가 명령의 종료 코드와 같다.

호스트를 건드리는 명령은 이 시험에서 하나도 실제로 돌리지 않는다.
허용 쪽 시험은 echo·false·env·pwd 뿐이다.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TMX = os.path.join(os.path.dirname(HERE), 'tmx.sh')
PREFIX = '/data/data/com.termux/files/usr'
HAVE_TERMUX = os.access(os.path.join(PREFIX, 'bin', 'bash'), os.X_OK)


def tmx(*args, env=None):
    r = subprocess.run(['sh', TMX] + list(args), capture_output=True,
                       text=True, timeout=60, env=env)
    return r.returncode, r.stdout, r.stderr


# 거부되어야 하는 명령들. 각 줄 = (명령, 무엇을 막는가)
DENIED = [
    ('termux-reset', '환경 초기화'),
    ('termux-restore backup.tar', '백업 덮어쓰기'),
    ('termux-change-repo', '미러 바꾸기'),
    ("sed -i 's/a/b/' $PREFIX/etc/apt/sources.list",
     'sources.list 편집'),
    ('echo x > $PREFIX/etc/apt/sources.list.d/x.list',
     'sources.list.d 쓰기'),
    ('pkg upgrade', '전체 업그레이드'),
    ('pkg up', 'pkg 의 업그레이드 줄임말'),
    ('apt upgrade -y', '전체 업그레이드'),
    ('apt-get dist-upgrade', '배포판 업그레이드'),
    ('apt full-upgrade', '전체 업그레이드'),
    ('apt remove nano', '패키지 제거'),
    ('apt-get purge nano', '패키지 제거'),
    ('apt autoremove', '자동 제거'),
    ('pkg uninstall nano', '패키지 제거'),
    ('dpkg -r nano', '패키지 제거'),
    ('dpkg --purge nano', '패키지 제거'),
    ('rm -rf $PREFIX/lib', '$PREFIX 지우기'),
    ('rm -r /data/data/com.termux/files/home/x', '$HOME 지우기'),
    ('rm -fr ~/x', '$HOME 지우기'),
    ('echo x > ~/.termux/termux.properties', '~/.termux 쓰기'),
    ('touch /data/data/com.termux/files/home/.termux/x',
     '~/.termux 쓰기'),
    ('termux-wifi-enable false', 'Wi-Fi 끄기'),
    ('termux-telephony-call 0', '전화 걸기'),
    ('termux-sms-send -n 0 hi', '문자 보내기'),
    ('termux-sms-list', '문자 읽기(개인정보)'),
    ('termux-call-log', '통화 기록(개인정보)'),
    ('termux-contact-list', '연락처(개인정보)'),
    ('termux-location', '위치(개인정보)'),
    ('termux-camera-photo x.jpg', '카메라(개인정보)'),
    ('termux-microphone-record -f x', '마이크(개인정보)'),
    ('termux-notification-list', '알림 읽기(개인정보)'),
    ('termux-fingerprint', '지문'),
    ('termux-keystore list', '키 저장소'),
    ('termux-nfc', 'NFC'),
    ('termux-usb -l', 'USB'),
    ('termux-telephony-deviceinfo', '전화 기기 정보(개인정보)'),
    ('termux-wallpaper -f x.jpg', '배경화면 바꾸기'),
    ('termux-brightness 10', '밝기 바꾸기'),
    ('termux-volume music 3', '음량 바꾸기'),
    ('termux-torch on', '손전등 켜기'),
    ('termux-setup-storage', '권한 창을 띄운다'),
    ('termux-dialog', '대화형'),
    ('am start -a android.intent.action.VIEW', '앱 띄우기'),
    ('termux-am broadcast -a x', '브로드캐스트'),
    ('termux-open x.html', '다른 앱 띄우기'),
    ('termux-open-url https://example.invalid', '브라우저 띄우기'),
    ('pkg install nano', '허락 없는 설치'),
    ('apt install -y nano', '허락 없는 설치'),
    ('echo ok; termux-reset', '줄 뒤쪽에 숨은 명령'),
    ('true && pkg upgrade', '&& 뒤에 숨은 명령'),
]


class DenyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mark = os.path.join(self.tmp, 'ran')

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_each_denied_exits_99_without_running(self):
        for cmd, why in DENIED:
            with self.subTest(cmd=cmd, why=why):
                # 거부 목록 검사는 쪽(side)과 상관없이 먼저 돈다.
                # proot 쪽으로 보내 시험이 호스트에 닿을 길을
                # 아예 없앤다.
                code, out, err = tmx('--proot', '--', cmd + '; touch '
                                     + self.mark)
                self.assertEqual(code, 99, (cmd, out, err))
                self.assertFalse(os.path.exists(self.mark), cmd)
                self.assertIn('거부', err)

    def test_dry_run_reports_verdict_only(self):
        code, out, _ = tmx('--dry-run', '--', 'termux-reset')
        self.assertEqual(code, 99)
        code, out, _ = tmx('--dry-run', '--', 'echo hi')
        self.assertEqual(code, 0)
        self.assertIn('허용', out)

    # ── 거부 목록이 너무 넓으면 캡처를 못 뜬다 — 허용돼야 하는 것 ─────
    def test_read_only_neighbours_are_allowed(self):
        ok = ['cat $PREFIX/etc/apt/sources.list',
              'ls ~/.termux/',
              'termux-battery-status',
              'termux-volume',
              'termux-torch --help',
              'apt-cache policy',
              'dpkg -l',
              'pkg list-installed',
              'rm -rf ' + '/data/data/com.termux/files/home/github/'
              'treasure_house/termux/scratch/x',
              'rm -f /data/data/com.termux/files/home/github/'
              'treasure_house/termux/scratch/y',
              'apt remove -y treasure-hello',
              'dpkg -r treasure-hello']
        for cmd in ok:
            with self.subTest(cmd=cmd):
                code, out, _ = tmx('--dry-run', '--', cmd)
                self.assertEqual(code, 0, (cmd, out))

    def test_install_needs_explicit_flag(self):
        code, _, _ = tmx('--dry-run', '--allow-install', '--',
                         'pkg install -y cronie')
        self.assertEqual(code, 0)

    def test_no_command_is_usage_error(self):
        code, _, err = tmx('--proot')
        self.assertEqual(code, 2)
        self.assertIn('사용법', err)


class RunTest(unittest.TestCase):
    def test_proot_side_trailer_and_exit(self):
        code, out, _ = tmx('--proot', '--', 'echo hi')
        self.assertEqual(code, 0)
        lines = out.rstrip('\n').split('\n')
        self.assertEqual(lines[0], 'hi')
        self.assertRegex(lines[-1],
                         r'^## tmx: side=proot cwd=\S+ exit=0$')

    def test_exit_code_passes_through(self):
        code, out, _ = tmx('--proot', '--', 'exit 3')
        self.assertEqual(code, 3)
        self.assertTrue(out.rstrip().endswith('exit=3'))

    def test_timeout_is_124(self):
        code, out, _ = tmx('--proot', '--timeout', '1', '--', 'sleep 5')
        self.assertEqual(code, 124)
        self.assertTrue(out.rstrip().endswith('exit=124'))

    def test_cwd_option(self):
        d = tempfile.mkdtemp()
        try:
            code, out, _ = tmx('--proot', '--cwd', d, '--', 'pwd')
            self.assertEqual(out.split('\n')[0], d)
            self.assertIn('cwd=%s ' % d, out)
        finally:
            shutil.rmtree(d)

    def test_proot_ld_vars_are_not_leaked(self):
        env = dict(os.environ, LD_PRELOAD='/nope.so',
                   LD_LIBRARY_PATH='/x')
        code, out, _ = tmx('--proot', '--', 'env', env=env)
        self.assertNotIn('LD_PRELOAD=', out)
        self.assertNotIn('LD_LIBRARY_PATH=', out)

    @unittest.skipUnless(HAVE_TERMUX, 'Termux 접두사가 없다')
    def test_termux_side_environment(self):
        code, out, _ = tmx('--', 'echo "$PREFIX|$HOME|$TMPDIR|$LANG";'
                           ' echo "$PATH"; echo "${BASH_VERSION%%.*}"')
        self.assertEqual(code, 0)
        rows = out.split('\n')
        home = '/data/data/com.termux/files/home'
        self.assertEqual(rows[0], '%s|%s|%s/tmp|en_US.UTF-8'
                         % (PREFIX, home, PREFIX))
        self.assertEqual(rows[1], PREFIX + '/bin')
        self.assertRegex(out.rstrip().split('\n')[-1],
                         r'^## tmx: side=termux cwd=\S+ exit=0$')

    @unittest.skipUnless(HAVE_TERMUX, 'Termux 접두사가 없다')
    def test_termux_side_runs_bionic_bash(self):
        # proot 의 /bin/bash 가 아니라 Termux 의 bash 인가.
        # bash -c 는 마지막 명령을 exec 로 바꿔 치운다 — readlink 를
        # 그냥 부르면 $$ 가 readlink 자신(coreutils)이 된다. 명령
        # 치환 안에서 불러 bash 가 살아 있을 때 잰다.
        code, out, _ = tmx('--', 'x=$(readlink /proc/$$/exe);'
                           ' echo "$x"')
        self.assertEqual(out.split('\n')[0], PREFIX + '/bin/bash')


if __name__ == '__main__':
    unittest.main()
