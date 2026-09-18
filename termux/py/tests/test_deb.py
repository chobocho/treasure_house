# -*- coding: utf-8 -*-
"""deb.py 시험 — .deb 한 개를 손으로 열어 보는 일.

6부의 실습은 ".deb 는 ar 묶음 안의 tar 두 개" 라는 사실에서 시작한다.
그래서 시험은 .deb 를 두 번 짓는다 — 한 번은 파이썬의 tarfile 과 손으로
쓴 ar 머리로(압축 없음·gz·xz), 한 번은 진짜 dpkg-deb --build 로.
두 쪽 모두 같은 control 과 파일 목록이 나와야 한다.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import deb                                         # noqa: E402

CONTROL = ('Package: treasure-hello\nVersion: 1.0\n'
           'Architecture: all\nMaintainer: nobody <x@example.com>\n'
           'Description: 인사 한 줄\n 두 번째 줄은 들여쓴다.\n')


def tar_bytes(files, mode):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w' + mode) as t:
        for name, data in files:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name.endswith('hello') else 0o644
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def ar(members):
    """ar 묶음. 머리 60바이트, 몸통은 짝수 길이로 맞춘다."""
    out = b'!<arch>\n'
    for name, data in members:
        head = ('%-16s%-12d%-6d%-6d%-8s%-10d`\n'
                % (name, 0, 0, 0, '100644', len(data))).encode()
        out += head + data + (b'\n' if len(data) % 2 else b'')
    return out


def build(comp=''):
    ext = {'': '', ':gz': '.gz', ':xz': '.xz'}[comp]
    ctl = tar_bytes([('./control', CONTROL.encode())], comp)
    data = tar_bytes([('./data/data/com.termux/files/usr/bin/hello',
                       b'#!/bin/sh\necho hi\n'),
                      ('./data/data/com.termux/files/usr/share/doc/'
                       'treasure-hello/README', b'r\n')], comp)
    return ar([('debian-binary', b'2.0\n'),
               ('control.tar' + ext, ctl), ('data.tar' + ext, data)])


class DebTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def put(self, data, name='x.deb'):
        p = os.path.join(self.d, name)
        open(p, 'wb').write(data)
        return p

    def check(self, p):
        info = deb.read(p)
        self.assertEqual(info['format'], '2.0')
        self.assertEqual(info['control']['Package'], 'treasure-hello')
        self.assertEqual(info['control']['Version'], '1.0')
        self.assertEqual(info['control']['Description'],
                         '인사 한 줄\n두 번째 줄은 들여쓴다.')
        self.assertIn('/data/data/com.termux/files/usr/bin/hello',
                      info['files'])
        return info

    def test_plain_gz_xz(self):
        for comp, ext in (('', ''), (':gz', '.gz'), (':xz', '.xz')):
            with self.subTest(comp=comp):
                info = self.check(self.put(build(comp)))
                self.assertEqual([m[0] for m in info['members']],
                                 ['debian-binary', 'control.tar' + ext,
                                  'data.tar' + ext])

    def test_member_sizes(self):
        info = deb.read(self.put(build(':gz')))
        self.assertEqual(info['members'][0], ('debian-binary', 4))

    def test_not_ar(self):
        with self.assertRaises(ValueError):
            deb.read(self.put(b'PK\x03\x04 not a deb'))

    def test_missing_control(self):
        with self.assertRaises(ValueError):
            deb.read(self.put(ar([('debian-binary', b'2.0\n')])))

    def test_zstd_is_named_not_crashed(self):
        data = ar([('debian-binary', b'2.0\n'),
                   ('control.tar.zst', b'\x28\xb5\x2f\xfd'),
                   ('data.tar.zst', b'\x28\xb5\x2f\xfd')])
        with self.assertRaises(ValueError) as cm:
            deb.read(self.put(data))
        self.assertIn('zst', str(cm.exception))

    def test_parse_control_continuation_and_dot(self):
        c = deb.parse_control('A: 1\nB: x\n y\n .\n z\n')
        self.assertEqual(c, {'A': '1', 'B': 'x\ny\n\nz'})

    def test_clip_counts_korean_double(self):
        self.assertEqual(deb.clip('가나다라', 5), '가나')
        self.assertEqual(deb.clip('abc', 5), 'abc')

    def test_report_fits_72(self):
        info = deb.read(self.put(build(':xz')))
        text = deb.report('x.deb', info)
        self.assertTrue(all(len(l) <= 72 for l in text.split('\n')))
        self.assertIn('Package: treasure-hello', text)


@unittest.skipUnless(shutil.which('dpkg-deb'), 'dpkg-deb 가 없다')
class RealDebTest(unittest.TestCase):
    def test_matches_dpkg_deb(self):
        d = tempfile.mkdtemp()
        try:
            root = os.path.join(d, 'pkg')
            os.makedirs(os.path.join(root, 'DEBIAN'))
            os.makedirs(os.path.join(root, 'usr', 'bin'))
            open(os.path.join(root, 'DEBIAN', 'control'), 'w').write(
                'Package: treasure-hello\nVersion: 1.0\n'
                'Architecture: all\nMaintainer: n <x@example.com>\n'
                'Description: hi\n')
            p = os.path.join(root, 'usr', 'bin', 'hello')
            open(p, 'w').write('#!/bin/sh\necho hi\n')
            os.chmod(p, 0o755)
            out = os.path.join(d, 'x.deb')
            subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz',
                            '--build', root, out], check=True,
                           capture_output=True)
            info = deb.read(out)
            want = subprocess.run(['dpkg-deb', '-c', out],
                                  capture_output=True,
                                  text=True).stdout.split('\n')
            names = sorted(l.split()[-1].lstrip('.') for l in want
                           if l.strip() and not l.startswith('d'))
            self.assertEqual(sorted(info['files']), names)
            self.assertEqual(info['control']['Package'],
                             'treasure-hello')
        finally:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
