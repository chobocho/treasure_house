# -*- coding: utf-8 -*-
"""anon.py 시험 — 네이티브 캡처의 기기 식별값을 가짜로 바꾼다.

scrub.py 가 개인정보(SSID·IP·집 경로)를 맡는다면 anon.py 는 그
밖의 "이 폰" 을 가리키는 값 — 모델 번호, 커널 빌드 문자열, 배터리
수치, 센서 칩 이름, 카메라 사양, 미러, 갱신 대기 패키지 — 을 맡는다.
공개 저장소에 올리기 전에 사용자가 정한 것(2026-09-19).
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import anon                                        # noqa: E402

UNAME = ('Linux localhost 6.12.58-android16-6-pdeadbe0-abogkiG99'
         '9NXXU1AAA1-4k #1 SMP PREEMPT Tue Mar  3 12:34:56 UTC '
         '2026 aarch64 Android')


def sec(n, title, body, rc=0):
    return '== %d. %s ==\n%s\n(종료 %d)\n' % (n, title, body, rc)


def body_of(text, word):
    """제목에 word 가 든 절의 본문(JSON)."""
    for part in ('\n' + text).split('\n== ')[1:]:
        head, _, rest = part.partition(' ==\n')
        if word in head:
            return json.loads(rest.rsplit('\n(종료', 1)[0])
    raise KeyError(word)


class AnonTest(unittest.TestCase):
    def test_uname_keeps_release_line_only(self):
        # GKI 판(6.12.58-android16)은 덱이 인용한다. 그 뒤의 빌드
        # 해시·펌웨어 번호·빌드 시각이 이 기기를 가리킨다
        out = anon.native(sec(6, 'uname -a', UNAME))
        self.assertIn('6.12.58-android16-6-', out)
        self.assertNotIn('pdeadbe0', out)
        self.assertNotIn('G999', out)
        self.assertNotIn('Mar  3 12:34:56', out)
        self.assertIn('aarch64 Android', out)

    def test_model(self):
        out = anon.native('Device model:\nSM-G999N\n')
        self.assertEqual(out, 'Device model:\n%s\n' % anon.MODEL)
        self.assertNotEqual(anon.MODEL, 'SM-G999N')

    def test_pid(self):
        out = anon.native('TERMUX_APP__PID=4321\n')
        self.assertNotIn('4321', out)

    def test_battery_numbers_fake_keys_kept(self):
        real = {'present': True, 'plugged': 'PLUGGED_AC',
                'status': 'CHARGING', 'temperature': 33.3,
                'voltage': 3900, 'current': 123789,
                'percentage': 77, 'charge_counter': 1111111}
        text = sec(21, 'timeout 20 termux-battery-status',
                   json.dumps(real, indent=2))
        got = body_of(anon.native(text), 'battery')
        self.assertEqual(list(got), list(real))   # 칸과 차례는 그대로
        self.assertEqual(got['status'], 'CHARGING')
        for k in ('temperature', 'voltage', 'current', 'percentage',
                  'charge_counter'):
            self.assertNotEqual(got[k], real[k], k)

    def test_sensor_names_count_kept(self):
        real = {'sensors': ['chipA_0 Accelerometer', 'chipB Pressure',
                            'x']}
        text = sec(22, 'timeout 20 termux-sensor -l',
                   json.dumps(real, indent=2))
        got = body_of(anon.native(text), 'sensor')['sensors']
        self.assertEqual(len(got), 3)             # 덱이 개수를 인용
        self.assertNotIn('chipA', ' '.join(got))

    def test_camera_facing_kept_specs_fake(self):
        cam = {'id': '0', 'facing': 'back',
               'jpeg_output_sizes': [{'width': 4096, 'height': 3072},
                                     {'width': 640, 'height': 480}],
               'focal_lengths': [6.25],
               'physical_size': {'width': 8.8, 'height': 6.6},
               'capabilities': ['raw']}
        text = sec(23, 'timeout 20 termux-camera-info',
                   json.dumps([cam, dict(cam, id='1', facing='front')],
                              indent=2))
        got = body_of(anon.native(text), 'camera')
        self.assertEqual([c['facing'] for c in got], ['back', 'front'])
        dump = json.dumps(got)
        for real in ('4096', '3072', '6.25', '8.8'):
            self.assertNotIn(real, dump)

    def test_mirror_and_updatable(self):
        text = ('deb https://mirror.example.org/termux/apt/'
                'termux-main stable main\n'
                'Updatable packages:\n'
                'vim/stable 1.2.3789 aarch64 [upgradable from: 1.2]\n'
                'code-server/tur 7.890.1 aarch64 [upgradable from: 7]\n'
                'termux-tools version:\n1.45.0\n')
        out = anon.native(text)
        self.assertNotIn('example.org', out)
        self.assertIn(anon.MIRROR, out)
        self.assertNotIn('code-server', out)
        self.assertIn('termux-tools version:\n1.45.0\n', out)

    def test_idempotent_and_untouched(self):
        text = sec(6, 'uname -a', UNAME) + 'Android version:\n17\n'
        once = anon.native(text)
        self.assertEqual(anon.native(once), once)
        self.assertIn('Android version:\n17\n', once)

    def test_bad_json_left_alone(self):
        # 20초에 끊겨 본문이 빈 절(tts-engines)도 있다
        text = sec(21, 'timeout 20 termux-battery-status', '', 124)
        self.assertEqual(anon.native(text), text)


class IdsTest(unittest.TestCase):
    # 앱 번호 789(시험용). 범주는 c(789 & 255)=c21, c(256 + 3)=c259
    ENV = ('groups=0(root),1077(external_storage),3003(inet),'
           '20789(u0_a789_cache),50789(all_a789)\n'
           'aid_u0_a789:x:10789:10789:Termux:/:/sbin/nologin\n'
           'Uid:\t10789\t10789\nTERMUX__UID=10789\n'
           'u:r:untrusted_app_27:s0:c21,c259,c512,c768\n')

    def test_app_id_faked_consistently(self):
        out = anon.ids(self.ENV)
        self.assertNotIn('789', out)
        self.assertNotIn('c21,c259', out)
        n = anon.APP_ID
        for want in ('20%d(u0_a%d_cache)' % (n, n), '50%d(all_a%d)'
                     % (n, n), 'aid_u0_a%d:x:10%d:10%d' % (n, n, n),
                     'Uid:\t10%d\t10%d' % (n, n),
                     'TERMUX__UID=10%d' % n,
                     's0:c%d,c%d,c512,c768' % (n & 255,
                                               256 + (n >> 8))):
            self.assertIn(want, out)
        # 시스템 그룹 번호는 그대로
        self.assertIn('1077(external_storage),3003(inet)', out)
        self.assertEqual(anon.ids(out), out)

    def test_two_apps_idempotent(self):
        # 앱 이름이 둘이면 작은 번호부터 가짜 번호를 차례로 받는다.
        # 두 번째 호출이 둘을 하나로 뭉개면 안 된다
        text = 'u0_a231 10231 x u0_a789 10789 all_a789\n'
        n = anon.APP_ID
        want = ('u0_a%d 10%d x u0_a%d 10%d all_a%d\n'
                % (n, n, n + 1, n + 1, n + 1))
        once = anon.ids(text)
        self.assertEqual(once, want)
        self.assertEqual(anon.ids(once), once)

    def test_real_id_equal_to_fake_does_not_chain(self):
        # 진짜 번호가 우연히 가짜 번호와 같아도 한 번에 바꾼다 —
        # 차례로 바꾸면 100→123 뒤에 123→124 가 앞의 것까지 삼킨다
        n = anon.APP_ID
        text = 'u0_a100 10100 u0_a%d 10%d\n' % (n, n)
        self.assertEqual(anon.ids(text), 'u0_a%d 10%d u0_a%d 10%d\n'
                         % (n, n, n + 1, n + 1))

    def test_no_app_name_untouched(self):
        # 앱 이름이 없는 파일에서는 번호를 짐작하지 않는다
        text = 'Uid:\t10789\nwidth 789\n'
        self.assertEqual(anon.ids(text), text)

    def test_mirror_host_everywhere(self):
        text = (' 500 https://mirror.real.edu/termux/apt/termux-main '
                'stable/main aarch64 Packages\n'
                '     origin mirror.real.edu\n'
                'deb https://tur.kcubeterm.com tur-packages tur\n')
        out = anon.ids(text)
        self.assertNotIn('real.edu', out)
        self.assertIn('origin mirror.example.com\n', out)
        # 공개 저장소는 그대로
        self.assertIn('tur.kcubeterm.com', out)

    def test_native_does_ids_too(self):
        self.assertNotIn('789', anon.native(self.ENV))


if __name__ == '__main__':
    unittest.main()
