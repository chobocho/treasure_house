# -*- coding: utf-8 -*-
"""scrub.py 시험 — 캡처에서 개인정보를 지우고, 남은 것을 잡는다.

모든 값은 **지어낸 것**이다. 진짜 전화번호·MAC·주소는 이 파일에도
없다. 예시 IP 는 문서용 대역(RFC 5737: 192.0.2.0/24·198.51.100.0/24·
203.0.113.0/24)이 아니라 일부러 '공인처럼 보이는' 값을 쓴다 —
문서용 대역을 봐주는 규칙이 없으므로 결과는 같다.

두 갈래다.
  fix()      — 바꿔도 뜻이 안 변하는 것(SSID·BSSID·공인 IP·집 경로)을
               자리표시로 바꾼다. run_all.py 가 캡처를 쓰기 직전에
               부른다.
  problems() — 바꾸면 안 되는 것, 또는 fix 가 놓친 것이 남았는지 본다.
               하나라도 있으면 make scrub 이 실패한다.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import scrub                                       # noqa: E402

HOME = '/data/data/com.termux/files/home'
REPO = HOME + '/github/treasure_house/termux'


def kinds(text):
    return sorted(set(k for _n, k, _s in scrub.problems(text)))


class FixTest(unittest.TestCase):
    def test_ssid_json(self):
        got, n = scrub.fix('{"ssid": "MyHomeNet_5G", "rssi": -50}')
        self.assertEqual(got, '{"ssid": "<ssid>", "rssi": -50}')
        self.assertEqual(n, 1)

    def test_bssid_json(self):
        got, _ = scrub.fix('"bssid": "a4:b1:c2:d3:e4:f5",')
        self.assertEqual(got, '"bssid": "<bssid>",')

    def test_public_ipv4_in_json_and_inet(self):
        got, _ = scrub.fix('"ip": "121.130.7.42"\ninet 121.130.7.42/24')
        self.assertEqual(got, '"ip": "<ip>"\ninet <ip>/24')

    def test_private_and_loopback_kept(self):
        t = 'inet 127.0.0.1 10.0.0.5 192.168.1.20 172.20.0.3 0.0.0.0'
        self.assertEqual(scrub.fix(t)[0], t)

    def test_ipv6_global_replaced_loopback_kept(self):
        got, _ = scrub.fix('inet6 2001:4860:1a2b::7 ::1')
        self.assertEqual(got, 'inet6 <ip> ::1')

    def test_link_local_ipv6_replaced(self):
        # fe80 주소의 뒤 64비트는 MAC 에서 만들어지기도 한다
        got, _ = scrub.fix('inet6 fe80::a6b1:c2ff:fed3:e4f5')
        self.assertEqual(got, 'inet6 <ip>')

    def test_home_path_outside_repo(self):
        got, _ = scrub.fix('cwd=%s/secret/plans.txt' % HOME)
        self.assertEqual(got, 'cwd=<home>/…')

    def test_repo_path_kept(self):
        t = 'cwd=%s/scratch' % REPO
        self.assertEqual(scrub.fix(t)[0], t)

    def test_proot_root_path_outside_repo(self):
        got, _ = scrub.fix('/root/Downloads/x.pdf')
        self.assertEqual(got, '<home>/…')
        t = '/root/github/treasure_house/termux/out'
        self.assertEqual(scrub.fix(t)[0], t)

    def test_root_inside_a_word_is_not_a_path(self):
        # "main/x11/root/TUR" 의 /root 는 경로가 아니다 (실제 오탐)
        t = '저장소 계층(main/x11/root/TUR/glibc)'
        self.assertEqual(scrub.fix(t)[0], t)
        self.assertEqual(kinds(t), [])

    def test_bare_home_kept(self):
        t = 'HOME=%s\n' % HOME
        self.assertEqual(scrub.fix(t)[0], t)

    def test_shared_storage_file(self):
        got, _ = scrub.fix('/storage/emulated/0/DCIM/IMG_1.jpg')
        self.assertEqual(got, '/storage/emulated/0/<…>')
        t = 'ls /storage/emulated/0 /sdcard'
        self.assertEqual(scrub.fix(t)[0], t)

    def test_fix_is_idempotent(self):
        once, _ = scrub.fix('"ssid": "x" inet 8.8.4.4')
        twice, n = scrub.fix(once)
        self.assertEqual(once, twice)
        self.assertEqual(n, 0)

    def test_empty(self):
        self.assertEqual(scrub.fix(''), ('', 0))
        self.assertEqual(scrub.problems(''), [])


class ProblemTest(unittest.TestCase):
    def test_korean_mobile_number(self):
        self.assertEqual(kinds('call 010-1234-5678'), ['phone'])
        self.assertEqual(kinds('01012345678'), ['phone'])

    def test_international_number(self):
        self.assertEqual(kinds('+82 10 1234 5678'), ['phone'])

    def test_imei_like(self):
        self.assertEqual(kinds('imei 356938035643809'), ['imei'])

    def test_serial(self):
        self.assertEqual(kinds('ro.serialno=R5CT11AB2CD'), ['serial'])
        self.assertEqual(kinds('serial: <redacted>'), [])

    def test_mac(self):
        self.assertEqual(kinds('ether a4:b1:c2:d3:e4:f5'), ['mac'])

    def test_android_placeholder_mac_ok(self):
        self.assertEqual(kinds('02:00:00:00:00:00 00:00:00:00:00:00'),
                         [])

    def test_gps(self):
        self.assertEqual(kinds('37.566535, 126.977969'), ['gps'])
        self.assertEqual(kinds('"latitude": 37.5665'), ['gps'])

    def test_email(self):
        self.assertEqual(kinds('mail kim.minsu@example-corp.kr'),
                         ['email'])

    def test_public_email_allowlist(self):
        self.assertEqual(kinds('x@users.noreply.github.com'), [])

    def test_leftover_public_ip(self):
        self.assertEqual(kinds('connect to 121.130.7.42'), ['ip'])

    def test_unfixed_ssid(self):
        self.assertEqual(kinds('"ssid": "Cafe"'), ['ssid'])

    def test_unfixed_home_path(self):
        self.assertEqual(kinds('%s/notes.txt' % HOME), ['home'])

    def test_login_name_by_hash(self):
        # 이름 자체는 소스에 두지 않는다 — 해시로만 안다.
        word = 'zzqtestname'
        scrub.NAME_HASHES.add(scrub.name_hash(word))
        try:
            self.assertEqual(kinds('by ZzqTestName today'), ['name'])
        finally:
            scrub.NAME_HASHES.discard(scrub.name_hash(word))

    def test_fixed_text_has_no_problems(self):
        raw = ('{"ssid": "Home", "bssid": "a4:b1:c2:d3:e4:f5", '
               '"ip": "121.130.7.42"}\n%s/x/y' % HOME)
        self.assertEqual(scrub.problems(scrub.fix(raw)[0]), [])

    def test_versions_and_times_are_not_hits(self):
        t = ('bash 5.3.15 · 12:34:56 · 2026-09-18 · sha 1a2b3c4d '
             '· size 1234567 · port 8022 · python 3.14.4')
        self.assertEqual(kinds(t), [])

    def test_report_masks_value(self):
        hits = scrub.problems('call 010-1234-5678')
        self.assertNotIn('1234-5678', hits[0][2])


class CliTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def run_cli(self, *args):
        return subprocess.run([sys.executable,
                               os.path.join(os.path.dirname(HERE),
                                            'scrub.py')] + list(args),
                              capture_output=True, text=True)

    def test_check_clean_dir(self):
        io.open(os.path.join(self.d, 'a.txt'), 'w').write('ok\n')
        r = self.run_cli('--check', self.d)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_check_dirty_dir_fails_without_echoing_secret(self):
        io.open(os.path.join(self.d, 'a.txt'), 'w').write(
            'x\ncall 010-1234-5678\n')
        r = self.run_cli('--check', self.d)
        self.assertEqual(r.returncode, 1)
        self.assertIn('a.txt:2', r.stdout)
        self.assertNotIn('1234-5678', r.stdout)

    def test_fix_in_place(self):
        p = os.path.join(self.d, 'w.json')
        io.open(p, 'w').write('{"ssid": "Home"}\n')
        r = self.run_cli('--fix', p)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(io.open(p).read(), '{"ssid": "<ssid>"}\n')

    def test_missing_path_is_error(self):
        r = self.run_cli('--check', os.path.join(self.d, 'nope'))
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()
