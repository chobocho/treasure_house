# -*- coding: utf-8 -*-
"""elf.py 시험 — 실행 파일이 누구를 부르는지 읽는 일.

5부가 "Termux 의 bash 는 /system/bin/linker64 를 부르고, 우분투의
bash 는 /lib/ld-linux-aarch64.so.1 을 부른다" 를 보여 줄 때 쓰는
도구다. 그래서 두 가지를 본다.
  1. 시험 안에서 바이트로 지은 ELF — 값을 우리가 정했으니 답이
     정해져 있다(64·32비트, 리틀·빅 엔디언, 정적 파일, 망가진 파일).
  2. gcc 로 만든 진짜 실행 파일 — readelf 의 답과 같아야 한다.
바이너리 조각은 커밋하지 않는다. 필요한 것은 시험이 그때 짓는다.
"""
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import elf                                         # noqa: E402

PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
DT_NULL, DT_NEEDED, DT_STRTAB, DT_STRSZ = 0, 1, 5, 10
DT_SONAME, DT_RPATH, DT_RUNPATH = 14, 15, 29


def build(bits=64, little=True, machine=183, etype=3, interp=None,
          needed=(), runpath=None, rpath=None, soname=None):
    """ELF 한 벌을 바이트로 짓는다. 파일 전체를 가상 주소 0 에
    싣는 PT_LOAD 하나를 두어 주소 = 파일 위치가 되게 한다."""
    e = '<' if little else '>'
    ehsize, phsize = (64, 56) if bits == 64 else (52, 32)
    strs, offs = b'\0', {}

    def s(x):
        nonlocal strs
        if x not in offs:
            offs[x] = len(strs)
            strs += x.encode() + b'\0'
        return offs[x]
    dyn = [(DT_NEEDED, s(n)) for n in needed]
    if runpath:
        dyn.append((DT_RUNPATH, s(runpath)))
    if rpath:
        dyn.append((DT_RPATH, s(rpath)))
    if soname:
        dyn.append((DT_SONAME, s(soname)))
    has_dyn = bool(dyn)
    nph = 1 + (1 if interp else 0) + (1 if has_dyn else 0)
    at = ehsize + nph * phsize
    interp_b = (interp.encode() + b'\0') if interp else b''
    interp_off = at
    at += len(interp_b)
    str_off = at
    at += len(strs)
    at += (-at) % 8
    dyn_off = at
    dyn += [(DT_STRTAB, str_off), (DT_STRSZ, len(strs)), (DT_NULL, 0)]
    word = 'Q' if bits == 64 else 'I'
    sword = 'q' if bits == 64 else 'i'
    dyn_b = b''.join(struct.pack(e + sword + word, t, v)
                     for t, v in dyn)
    if not has_dyn:
        dyn_b = b''
    total = dyn_off + len(dyn_b)

    def ph(typ, off, size):
        if bits == 64:
            return struct.pack(e + 'IIQQQQQQ', typ, 4, off, off, off,
                               size, size, 8)
        return struct.pack(e + 'IIIIIIII', typ, off, off, off, size,
                           size, 4, 4)
    phs = ph(PT_LOAD, 0, total)
    if interp:
        phs += ph(PT_INTERP, interp_off, len(interp_b))
    if has_dyn:
        phs += ph(PT_DYNAMIC, dyn_off, len(dyn_b))
    ident = (b'\x7fELF' + bytes([2 if bits == 64 else 1,
                                  1 if little else 2, 1])
             + b'\0' * 9)
    if bits == 64:
        hdr = ident + struct.pack(e + 'HHIQQQIHHHHHH', etype, machine,
                                  1, 0, ehsize, 0, 0, ehsize, phsize,
                                  nph, 64, 0, 0)
    else:
        hdr = ident + struct.pack(e + 'HHIIIIIHHHHHH', etype, machine,
                                  1, 0, ehsize, 0, 0, ehsize, phsize,
                                  nph, 40, 0, 0)
    body = hdr + phs + interp_b + strs
    body += b'\0' * (dyn_off - len(body))
    return body + dyn_b


class SyntheticTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def put(self, data):
        p = os.path.join(self.d, 'x')
        open(p, 'wb').write(data)
        return p

    def test_bionic_like_64(self):
        info = elf.read(self.put(build(
            interp='/system/bin/linker64',
            needed=['libandroid-support.so', 'libc.so'],
            runpath='/data/data/com.termux/files/usr/lib')))
        self.assertEqual(info['class'], 'ELF64')
        self.assertEqual(info['endian'], 'LSB')
        self.assertEqual(info['machine'], 'AArch64')
        self.assertEqual(info['type'], 'DYN')
        self.assertEqual(info['interp'], '/system/bin/linker64')
        self.assertEqual(info['needed'],
                         ['libandroid-support.so', 'libc.so'])
        self.assertEqual(info['runpath'],
                         '/data/data/com.termux/files/usr/lib')
        self.assertIsNone(info['rpath'])

    def test_arm32(self):
        info = elf.read(self.put(build(bits=32, machine=40,
                                       interp='/system/bin/linker',
                                       needed=['libc.so'])))
        self.assertEqual(info['class'], 'ELF32')
        self.assertEqual(info['machine'], 'ARM')
        self.assertEqual(info['interp'], '/system/bin/linker')
        self.assertEqual(info['needed'], ['libc.so'])

    def test_big_endian(self):
        info = elf.read(self.put(build(little=False, machine=21,
                                       needed=['libc.so.6'],
                                       rpath='$ORIGIN')))
        self.assertEqual(info['endian'], 'MSB')
        self.assertEqual(info['needed'], ['libc.so.6'])
        self.assertEqual(info['rpath'], '$ORIGIN')

    def test_shared_library_soname(self):
        info = elf.read(self.put(build(needed=['libc.so'],
                                       soname='libfoo.so')))
        self.assertEqual(info['soname'], 'libfoo.so')
        self.assertIsNone(info['interp'])

    def test_static_exec(self):
        info = elf.read(self.put(build(etype=2)))
        self.assertEqual(info['type'], 'EXEC')
        self.assertIsNone(info['interp'])
        self.assertEqual(info['needed'], [])

    def test_not_elf(self):
        with self.assertRaises(ValueError):
            elf.read(self.put(b'#!/bin/sh\necho hi\n'))

    def test_truncated(self):
        data = build(interp='/system/bin/linker64', needed=['libc.so'])
        with self.assertRaises(ValueError):
            elf.read(self.put(data[:40]))

    def test_empty_file(self):
        with self.assertRaises(ValueError):
            elf.read(self.put(b''))

    def test_report_fits_72(self):
        info = elf.read(self.put(build(
            interp='/system/bin/linker64',
            needed=['libc.so'] * 3,
            runpath='/data/data/com.termux/files/usr/lib')))
        text = elf.report('/data/data/com.termux/files/usr/bin/bash',
                          info)
        self.assertTrue(all(len(l) <= 72 for l in text.split('\n')))
        self.assertIn('interp: /system/bin/linker64', text)


@unittest.skipUnless(shutil.which('gcc') and shutil.which('readelf'),
                     'gcc·readelf 가 없다')
class RealTest(unittest.TestCase):
    def test_matches_readelf(self):
        d = tempfile.mkdtemp()
        try:
            c = os.path.join(d, 'h.c')
            b = os.path.join(d, 'h')
            open(c, 'w').write('#include <stdio.h>\n#include <math.h>\n'
                               'int main(int n,char**v){'
                               'printf("%f\\n",sqrt(n));return 0;}\n')
            subprocess.run(['gcc', c, '-o', b, '-lm',
                            '-Wl,-rpath,/opt/x'], check=True)
            out = subprocess.run(['readelf', '-d', '-l', b],
                                 capture_output=True, text=True).stdout
            info = elf.read(b)
            want = sorted(l.split('[')[1].split(']')[0]
                          for l in out.split('\n') if '(NEEDED)' in l)
            self.assertEqual(sorted(info['needed']), want)
            interp = out.split('interpreter: ')[1].split(']')[0]
            self.assertEqual(info['interp'], interp)
            self.assertEqual(info['runpath'] or info['rpath'], '/opt/x')
        finally:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
