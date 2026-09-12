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
from compresslib import lz4block                   # noqa: E402

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


# ------------------------------------------------------- xxHash-32 lz4
# 프레임의 **머리 검사 바이트** 하나 때문에 필요하다. 우리는 프레임을
# 읽기만 하므로(§14.6) 라이브러리에는 xxHash 가 없다. 그런데 진짜 lz4 -d
# 가 우리 블록을 풀게 하려면 프레임으로 감싸야 하고, 감싸려면 머리 검사
# 바이트를 맞춰야 한다. 그래서 **상호운용 스크립트에만** 둔다.
XXH_P1 = 2654435761
XXH_P2 = 2246822519
XXH_P3 = 3266489917
XXH_P4 = 668265263
XXH_P5 = 374761393
M32 = 0xFFFFFFFF


def rotl32(x, r):
    return ((x << r) | (x >> (32 - r))) & M32


def _u32le(data, i):
    return int.from_bytes(data[i:i + 4], 'little')


def _xxh_round(acc, lane):
    acc = (acc + lane * XXH_P2) & M32
    return (rotl32(acc, 13) * XXH_P1) & M32


def xxh32(data, seed=0):
    n = len(data)
    i = 0
    if n >= 16:
        v1 = (seed + XXH_P1 + XXH_P2) & M32
        v2 = (seed + XXH_P2) & M32
        v3 = seed & M32
        v4 = (seed - XXH_P1) & M32
        while n - i >= 16:
            v1 = _xxh_round(v1, _u32le(data, i))
            v2 = _xxh_round(v2, _u32le(data, i + 4))
            v3 = _xxh_round(v3, _u32le(data, i + 8))
            v4 = _xxh_round(v4, _u32le(data, i + 12))
            i += 16
        h = (rotl32(v1, 1) + rotl32(v2, 7) + rotl32(v3, 12)
             + rotl32(v4, 18)) & M32
    else:
        h = (seed + XXH_P5) & M32
    h = (h + n) & M32
    while n - i >= 4:
        h = (h + _u32le(data, i) * XXH_P3) & M32
        h = (rotl32(h, 17) * XXH_P4) & M32
        i += 4
    while i < n:
        h = (h + data[i] * XXH_P5) & M32
        h = (rotl32(h, 11) * XXH_P1) & M32
        i += 1
    h ^= h >> 15
    h = (h * XXH_P2) & M32
    h ^= h >> 13
    h = (h * XXH_P3) & M32
    h ^= h >> 16
    return h


def lz4_frame_wrap(block):
    """우리 블록 하나를 lz4 프레임으로 감싼다. 검사합은 안 붙인다.

    FLG 0x60 = 판 01 · 블록 독립 · 검사합 없음, BD 0x70 = 최대 4 MiB.
    코퍼스에서 가장 큰 파일이 1 MiB 라 한 블록에 들어간다.
    """
    desc = bytes([0x60, 0x70])
    hc = (xxh32(desc) >> 8) & 0xFF
    head = b'\x04\x22\x4d\x18' + desc + bytes([hc])
    return (head + len(block).to_bytes(4, 'little') + block
            + b'\x00\x00\x00\x00')


def lz4_cli(data, *args):
    return subprocess.run(['lz4', '-c'] + list(args), input=data,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, check=True).stdout


def unlz4_cli(data):
    return subprocess.run(['lz4', '-d', '-c'], input=data,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, check=True).stdout


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

    lz = lz4_report()
    io.open(os.path.join(OUT, 'interop_lz4.txt'), 'w',
            encoding='utf-8', newline='\n').write(lz.text())
    print(lz.text())
    print('실패 %d건' % (r.fails + lz.fails))
    return 1 if (r.fails + lz.fails) else 0


def lz4_report():
    """LZ4 상호운용. 프레임을 쓰는 코드는 여기에만 있다 (SPEC §14.6)."""
    r = Report()

    r.section('우리 블록을 프레임으로 감싸 → 진짜 lz4 -d 가 푼다')
    r.row(pad('파일', 20) + ' ' + pad('우리 블록', 11, True)
          + ' ' + pad('프레임', 10, True) + '  결과')
    for name in FILES:
        src = read(name)
        block = lz4block.compress_block(src)
        frame = lz4_frame_wrap(block)
        ok = unlz4_cli(frame) == src
        r.row('%-20s %11d %10d  %s'
              % (name, len(block), len(frame), r.check(ok, name)))
    r.blank()

    r.section('진짜 lz4 (-1 · -9 · --no-frame-crc) → 우리가 푼다')
    r.row('기본 프레임에는 내용 xxHash 가 붙는다. 우리 독해기는 그')
    r.row('4바이트를 건너뛴다 — 검사는 안 하고 읽기는 한다 (§14.6).')
    r.row(pad('파일', 20) + ' ' + pad('설정', 16) + ' '
          + pad('프레임', 10, True) + '  결과')
    for name in FILES:
        src = read(name)
        settings = (('-1', ('-1',)), ('-9', ('-9',)),
                    ('--no-frame-crc', ('-9', '--no-frame-crc')))
        for label, args in settings:
            frame = lz4_cli(src, *args)
            ok = lz4block.frame_decode(frame) == src
            r.row('%-20s %-16s %10d  %s'
                  % (name, label, len(frame), r.check(ok, name)))
    r.blank()

    r.section('우리 프레임과 lz4 -9 프레임의 크기')
    r.row('우리 부호기는 해시 한 칸짜리 "빠른 모드" 다. lz4 -9 는')
    r.row('사슬을 끝까지 뒤진다 — 같은 형식이지만 하는 일이 다르다.')
    r.row('둘 다 프레임으로 재서 머릿값까지 같은 조건으로 견준다.')
    r.row(pad('파일', 20) + ' ' + pad('원본', 10, True) + ' '
          + pad('우리', 10, True) + ' ' + pad('lz4 -9', 10, True)
          + ' ' + pad('차이', 9, True))
    for name in FILES:
        src = read(name)
        ours = len(lz4_frame_wrap(lz4block.compress_block(src)))
        theirs = len(lz4_cli(src, '-9', '--no-frame-crc'))
        diff = 100.0 * (ours - theirs) / max(1, theirs)
        r.row('%-20s %10d %10d %10d %+8.1f%%'
              % (name, len(src), ours, theirs, diff))
    return r


if __name__ == '__main__':
    sys.exit(main())
