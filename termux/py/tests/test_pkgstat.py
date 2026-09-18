# -*- coding: utf-8 -*-
"""pkgstat.py 시험 — dpkg 의 status 파일에서 숫자를 세는 일.

6부의 "이 기기에 패키지가 몇 개, 크기는 어떻게 퍼져 있나" 표는 이
도구가 $PREFIX/var/lib/dpkg/status 에서 센다. 합성 status 는 실제
파일의 꼴(Essential·Conffiles 이어지는 줄·지워졌지만 설정만 남은 것)을
본떴다.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import pkgstat                                     # noqa: E402

STATUS = """Package: apt
Essential: yes
Status: install ok installed
Installed-Size: 4008
Maintainer: @termux
Architecture: aarch64
Version: 2.8.1-2
Conffiles:
 /data/data/com.termux/files/usr/etc/apt/sources.list bb43
Description: Front-end for the dpkg package manager

Package: autoconf
Status: install ok installed
Installed-Size: 3680
Maintainer: @termux
Architecture: all
Version: 2.73

Package: tiny
Status: install ok installed
Installed-Size: 12
Maintainer: someone
Architecture: aarch64
Version: 1

Package: gone
Status: deinstall ok config-files
Installed-Size: 999999
Architecture: aarch64
Version: 0.1

Package: nosize
Status: install ok installed
Architecture: aarch64
Version: 3
"""


class PkgStatTest(unittest.TestCase):
    def setUp(self):
        self.all = pkgstat.parse_status(STATUS)
        self.inst = pkgstat.installed(self.all)

    def test_paragraphs(self):
        self.assertEqual([p['Package'] for p in self.all],
                         ['apt', 'autoconf', 'tiny', 'gone', 'nosize'])
        self.assertIn('sources.list',
                      self.all[0]['Conffiles'])

    def test_only_installed(self):
        self.assertEqual([p['Package'] for p in self.inst],
                         ['apt', 'autoconf', 'tiny', 'nosize'])

    def test_summary(self):
        s = pkgstat.summary(self.inst)
        self.assertEqual(s['count'], 4)
        self.assertEqual(s['total_kib'], 4008 + 3680 + 12)
        self.assertEqual(s['essential'], 1)
        self.assertEqual(s['arch'], {'aarch64': 3, 'all': 1})
        self.assertEqual(s['no_size'], 1)
        self.assertEqual(s['top'][0], ('apt', 4008))
        self.assertEqual(s['maintainer_termux'], 2)

    def test_histogram(self):
        h = pkgstat.histogram([12, 3680, 4008, 150000],
                              [100, 1024, 10240, 102400])
        self.assertEqual(h, [('100 KiB 미만', 1), ('100 KiB–1 MiB', 0),
                             ('1–10 MiB', 2), ('10–100 MiB', 0),
                             ('100 MiB 이상', 1)])

    def test_empty(self):
        self.assertEqual(pkgstat.parse_status(''), [])
        s = pkgstat.summary([])
        self.assertEqual(s['count'], 0)
        self.assertEqual(s['top'], [])

    def test_report_fits_72(self):
        text = pkgstat.report(pkgstat.summary(self.inst))
        self.assertTrue(all(len(l) <= 72 for l in text.split('\n')))
        self.assertIn('설치된 패키지 4개', text)


if __name__ == '__main__':
    unittest.main()
