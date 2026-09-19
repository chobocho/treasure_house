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
                'voltage': 3900, 'current': 123456,
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
                'vim/stable 9.2.1100 aarch64 [upgradable from: 9.2]\n'
                'code-server/tur 4.137.0 aarch64 [upgradable from: 4]\n'
                'termux-tools version:\n1.45.0\n')
        out = anon.native(text)
        self.assertNotIn('example.org', out)
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


if __name__ == '__main__':
    unittest.main()
