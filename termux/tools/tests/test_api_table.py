# -*- coding: utf-8 -*-
"""api_table.py 시험 — termux-* 명령 색인을 캡처에서 만든다.

data/api_cmds.tsv 의 '주인 패키지' 와 'termux-api 를 부르나' 칸은
손으로 적지 않는다(PLAN.md §3.3 dpkg_stats). 캡처 두 개(dpkg -S 목록,
termux-api 를 부르는 스크립트 이름)를 읽어 표를 만든다.
개인정보 등급은 PLAN.md §0.8 의 목록(정책)이다.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import api_table                                   # noqa: E402

P = '/data/data/com.termux/files/usr/bin/'
DPKG = ('== 3. x ==\n$ dpkg -S …\n'
        'termux-api: %stermux-battery-status\n'
        'termux-api: %stermux-sms-list\n'
        'termux-tools: %stermux-info\n'
        'proot: %stermux-chroot\n'
        '## tmx: side=termux cwd=/x exit=0\n' % (P, P, P, P))
CALLS = ('== 4. 그 이름들 ==\n$ grep …\ntermux-battery-status\n'
         'termux-sms-list\n## tmx: side=termux cwd=/x exit=0\n')


class ApiTableTest(unittest.TestCase):
    def setUp(self):
        self.rows = api_table.build(DPKG, CALLS,
                                    native={'termux-battery-status'},
                                    proot={'termux-info'})

    def test_owner_from_dpkg(self):
        got = {r['command']: r['owner-package'] for r in self.rows}
        self.assertEqual(got['termux-info'], 'termux-tools')
        self.assertEqual(got['termux-chroot'], 'proot')

    def test_needs_app_from_calls(self):
        got = {r['command']: r['needs-app'] for r in self.rows}
        self.assertEqual(got['termux-battery-status'], 'yes')
        self.assertEqual(got['termux-info'], 'no')

    def test_privacy_policy(self):
        got = {r['command']: r['privacy'] for r in self.rows}
        self.assertEqual(got['termux-sms-list'], 'sensitive')
        self.assertEqual(got['termux-battery-status'], 'safe')

    def test_run_in_deck(self):
        got = {r['command']: r['run-in-deck'] for r in self.rows}
        self.assertEqual(got['termux-sms-list'], 'never')
        self.assertEqual(got['termux-battery-status'], 'native')
        self.assertEqual(got['termux-info'], 'proot')
        self.assertEqual(got['termux-chroot'], '-')

    def test_sorted_and_complete(self):
        self.assertEqual([r['command'] for r in self.rows],
                         ['termux-battery-status', 'termux-chroot',
                          'termux-info', 'termux-sms-list'])

    def test_tsv_header_first(self):
        text = api_table.to_tsv(self.rows)
        self.assertTrue(text.split('\n')[2].startswith('command\t'))

    def test_empty_capture(self):
        self.assertEqual(api_table.build('', '', native=set(),
                                         proot=set()), [])


if __name__ == '__main__':
    unittest.main()
