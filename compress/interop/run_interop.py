# -*- coding: utf-8 -*-
"""상호운용 확인 — 진짜 도구와 주고받아 보고 out/ 에 남긴다.

    python3 interop/run_interop.py          (= make interop)

왜 이게 가장 강한 증거인가: 우리끼리의 왕복은 "내가 쓴 것을 내가 읽는다"
일 뿐이다. 부호기와 복호기가 같은 오해를 하고 있으면 영원히 안 드러난다.
**진짜 gzip 이 우리 파일을 풀고, 우리가 진짜 gzip 파일을 푸는 것** 만이
형식을 제대로 구현했다는 증거다.

이 단계에서 보는 것은 DEFLATE 계열뿐이다(PLAN §5 5단계).
bzip2·xz·lz4 는 그 모듈이 생기는 7단계에서 붙인다.

캡처는 재현되어야 한다(§8). 그래서
  · gzip 은 -n 을 준다 — 안 주면 머리에 수정 시각이 들어가 매번 달라진다
  · 시간·경로·판본 문자열은 적지 않는다
  · 숫자는 크기와 SHA-256 뿐이다
"""
import hashlib
import io
import os
import subprocess
import sys
import unicodedata
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'src', 'py'))

from compresslib import containers, deflate        # noqa: E402

CORPUS = os.path.join(BASE, 'corpus')
OUT = os.path.join(BASE, 'out')
FILES = ['empty.bin', 'one.bin', 'abab_4k.txt', 'alphabet.bin',
         'runs.bin', 'zeros_64k.bin', 'random_64k.bin',
         'boundary_32768.bin', 'boundary_32769.bin',
         'korean_utf8.txt', 'english.txt', 'source.go', 'mixed_1m.bin']


def cells(text):
    """화면 칸 수. 한글은 두 칸이다."""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1
               for c in text)


def pad(text, width, right=False):
    """칸 수로 맞춰 채운다.

    %-20s 로 채우면 글자 수로 세기 때문에 한글이 든 칸만 밀린다.
    고정폭 글꼴에서 한글은 정확히 두 칸이므로 표가 어긋나 보인다.
    캡처는 덱에 <pre> 로 그대로 실리니 여기서 맞춰 둬야 한다.
    """
    fill = ' ' * max(0, width - cells(text))
    return (fill + text) if right else (text + fill)


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def read(name):
    return io.open(os.path.join(CORPUS, name), 'rb').read()


def gzip_cli(data, level):
    """진짜 gzip 으로 압축. -n 이 없으면 머리에 시각이 들어가
    매번 다른 바이트가 나온다 — 재현이 깨진다."""
    return subprocess.run(['gzip', '-n', '-%d' % level, '-c'],
                          input=data, stdout=subprocess.PIPE,
                          check=True).stdout


def gunzip_cli(data):
    return subprocess.run(['gzip', '-d', '-c'], input=data,
                          stdout=subprocess.PIPE, check=True).stdout


class Report:
    """절 단위로 모은다. 덱은 <!--OUT sec=N--> 으로 한 절을 인용한다."""

    def __init__(self):
        self.lines = []
        self.n = 0
        self.fails = 0

    def section(self, title):
        self.n += 1
        self.lines.append('== %d. %s ==' % (self.n, title))

    def row(self, *cols):
        self.lines.append(' '.join(cols))

    def check(self, ok, label):
        if not ok:
            self.fails += 1
        return 'OK ' if ok else 'FAIL'

    def blank(self):
        self.lines.append('')

    def text(self):
        return '\n'.join(self.lines) + '\n'


def main():
    r = Report()

    r.section('우리 raw deflate → 진짜 zlib 이 푼다')
    r.row(pad('파일', 20) + ' ' + pad('원본', 10, True)
          + ' ' + pad('우리', 10, True) + ' ' + pad('비율', 7, True)
          + '  결과')
    for name in FILES:
        src = read(name)
        raw = deflate.deflate_raw(src)
        ok = zlib.decompress(raw, -15) == src
        ratio = 100.0 * len(raw) / len(src) if src else 0.0
        r.row('%-20s %10d %10d %6.1f%%  %s'
              % (name, len(src), len(raw), ratio, r.check(ok, name)))
    r.blank()

    r.section('진짜 zlib(레벨 0~9) → 우리 inflate 가 푼다')
    r.row(pad('파일', 20) + ' ' + pad('레벨', 6, True)
          + ' ' + pad('zlib', 10, True) + '  결과')
    for name in FILES:
        src = read(name)
        for level in (0, 1, 6, 9):
            co = zlib.compressobj(level, zlib.DEFLATED, -15)
            raw = co.compress(src) + co.flush()
            ok = deflate.inflate_raw(raw) == src
            r.row('%-20s %6d %10d  %s'
                  % (name, level, len(raw), r.check(ok, name)))
    r.blank()

    r.section('우리 gzip → 진짜 gzip 명령이 푼다')
    r.row(pad('파일', 20) + ' ' + pad('우리 .gz', 10, True)
          + ' ' + pad('SHA-256', 17, True) + '  결과')
    for name in FILES:
        src = read(name)
        gz = containers.gzip_compress(src)
        ok = gunzip_cli(gz) == src
        r.row('%-20s %10d %17s  %s'
              % (name, len(gz), sha(gz), r.check(ok, name)))
    r.blank()

    r.section('진짜 gzip -n -1/-6/-9 → 우리가 푼다')
    r.row(pad('파일', 20) + ' ' + pad('레벨', 6, True)
          + ' ' + pad('gzip', 10, True) + '  결과')
    for name in FILES:
        src = read(name)
        for level in (1, 6, 9):
            gz = gzip_cli(src, level)
            ok = containers.gzip_decompress(gz) == src
            r.row('%-20s %6d %10d  %s'
                  % (name, level, len(gz), r.check(ok, name)))
    r.blank()

    r.section('우리 것과 gzip -9 의 크기 차이')
    r.row('바이트가 같아지지는 않는다. 우리 부호기는 zlib 보다 단순한')
    r.row('선택을 하기 때문이다. 견줄 것은 크기뿐이다.')
    r.row(pad('파일', 20) + ' ' + pad('우리', 10, True)
          + ' ' + pad('gzip -9', 10, True) + ' ' + pad('차이', 9, True))
    for name in FILES:
        src = read(name)
        ours = len(containers.gzip_compress(src))
        theirs = len(gzip_cli(src, 9))
        diff = 100.0 * (ours - theirs) / theirs
        r.row('%-20s %10d %10d %+8.2f%%' % (name, ours, theirs, diff))
    r.blank()

    r.section('우리 zlib 컨테이너 ↔ 파이썬 zlib')
    r.row(pad('파일', 20) + ' ' + pad('우리', 10, True)
          + ' ' + pad('그쪽→', 7, True) + ' ' + pad('←우리', 7, True))
    for name in FILES:
        src = read(name)
        ours = containers.zlib_compress(src)
        a = r.check(zlib.decompress(ours) == src, name)
        theirs = containers.zlib_decompress(zlib.compress(src, 9))
        b = r.check(theirs == src, name)
        r.row('%-20s %10d %7s %7s' % (name, len(ours), a, b))

    text = r.text()
    io.open(os.path.join(OUT, 'interop_deflate.txt'), 'w',
            encoding='utf-8', newline='\n').write(text)
    print(text)
    print('실패 %d건' % r.fails)
    return 1 if r.fails else 0


if __name__ == '__main__':
    sys.exit(main())
