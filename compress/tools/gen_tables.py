# -*- coding: utf-8 -*-
"""손으로 적을 수밖에 없는 표를 만들고, 다섯 언어에 같은 값이 있는지 본다.

    python3 tools/gen_tables.py            # 각 언어에 넣을 모양을 찍는다
    python3 tools/gen_tables.py --check    # 다섯 소스에 그대로 있는지 검사

이 덱의 상수는 거의 전부 식에서 나온다 — DEFLATE 의 길이표도, CRC 표도,
tANS 의 걸음도. 유도할 식이 없는 표는 다섯 가지뿐이다.

  SQUASH      로지스틱 함수를 정수로 옮긴 33개 (SPEC §18.6)
  DCT         8x8 코사인 행렬 64개, 2^13 배 (§19.2)
  JPEGQ       JPEG 표준 휘도 양자화표 64개 (§19.4)
  ADPCMSTEP   IMA ADPCM 걸음표 89개 (§19.6)
  ADPCMINDEX  IMA ADPCM 지표표 16개 (§19.6)

숫자를 다섯 언어에 손으로 옮기면 어딘가는 틀리고, 틀린 자리는 그 값이
실제로 쓰이는 입력을 만나기 전까지 안 보인다. DCT 와 코사인은 실수
계산이라 프로그램이 직접 구하면 반올림이 기계마다 달라지기까지 한다.
그래서 여기서 한 번 만들고, --check 로 다섯 곳이 같은지 기계가 본다.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)

# SPEC §18.6. 로지스틱 함수 squash 를 128 간격으로 뜬 값이다.
SQUASH = [1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
          1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024, 4050,
          4068, 4079, 4085, 4089, 4092, 4093, 4094]

# 8x8 정수 DCT 의 코사인 행렬, 2^13 배 (SPEC §19.2). 코사인을 프로그램이
# 직접 계산하면 실수가 코덱 경로에 들어오고, 반올림이 기계마다 달라진다.
DCT_SCALE = 13
DCT = [2896, 2896, 2896, 2896, 2896, 2896, 2896, 2896, 4017, 3406, 2276, 799, -799, -2276, -3406, -4017, 3784, 1567, -1567, -3784, -3784, -1567, 1567, 3784, 3406, -799, -4017, -2276, 2276, 4017, 799, -3406, 2896, -2896, -2896, 2896, 2896, -2896, -2896, 2896, 2276, -4017, 799, 3406, -3406, -799, 4017, -2276, 1567, -3784, 3784, -1567, -1567, 3784, -3784, 1567, 799, -2276, 3406, -4017, 4017, -3406, 2276, -799]

# JPEG 표준 휘도 양자화표 (SPEC §19.4). 사람 눈이 높은 주파수에 둔하다는
# 실험에서 나온 값이라 식이 없다.
JPEG_QUANT = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]

# IMA ADPCM 의 걸음표 89개와 지표표 16개 (SPEC §19.6).
ADPCM_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]
ADPCM_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]

# 표식 → (상수 목록, 그 표가 있어야 하는 파일들)
TABLES = {
    'SQUASH': (SQUASH, ['src/py/compresslib/cm.py', 'src/cpp/cm.h',
                        'src/go/cm.go', 'src/ts/cm.ts',
                        'src/java/compresslib/Cm.java']),
    'DCT': (DCT, ['src/py/compresslib/lossy.py', 'src/cpp/lossy.h',
                  'src/go/lossy.go', 'src/ts/lossy.ts',
                  'src/java/compresslib/Lossy.java']),
    'JPEGQ': (JPEG_QUANT, ['src/py/compresslib/lossy.py',
                           'src/cpp/lossy.h', 'src/go/lossy.go',
                           'src/ts/lossy.ts',
                           'src/java/compresslib/Lossy.java']),
    'ADPCMSTEP': (ADPCM_STEP, ['src/py/compresslib/lossy.py',
                               'src/cpp/lossy.h', 'src/go/lossy.go',
                               'src/ts/lossy.ts',
                               'src/java/compresslib/Lossy.java']),
    'ADPCMINDEX': (ADPCM_INDEX, ['src/py/compresslib/lossy.py',
                                 'src/cpp/lossy.h', 'src/go/lossy.go',
                                 'src/ts/lossy.ts',
                                 'src/java/compresslib/Lossy.java']),
}

NUMBERS = re.compile(r'-?\d+')


def wrapped(prefix, indent, width=68, values=None):
    """숫자를 이어 적되 폴더블 폭 안에서 접는다."""
    values = SQUASH if values is None else values
    lines = []
    cur = indent
    for i, v in enumerate(values):
        piece = '%d,' % v if i + 1 < len(values) else '%d' % v
        if len(cur) + len(piece) + 1 > width and cur.strip():
            lines.append(cur.rstrip())
            cur = indent
        cur += piece + ' '
    lines.append(cur.rstrip())
    return prefix + '\n'.join(lines)


def found_in(path, name, want):
    """표식 사이에서 want 가 **이어진 조각으로** 들어 있는지 본다.

    구간의 숫자를 전부 긁어 비교하면 안 된다 — 표식 줄의 절 번호(§18.6)도,
    C++·Go 의 배열 크기 선언(33)도 숫자이기 때문이다. 언어마다 그 잡음이
    달라서, "어딘가에 이 서른셋이 이 순서로 있다" 를 묻는 편이 맞다.
    """
    text = io.open(os.path.join(BASE, path), encoding='utf-8').read()
    m = re.search(r'%s-TABLE-BEGIN(.*?)%s-TABLE-END' % (name, name),
                  text, re.S)
    if not m:
        return None
    nums = [int(x) for x in NUMBERS.findall(m.group(1))]
    k = len(want)
    for i in range(len(nums) - k + 1):
        if nums[i:i + k] == want:
            return want
    return nums


def main(argv):
    if '--check' in argv:
        bad = 0
        checked = 0
        for name, (want, paths) in sorted(TABLES.items()):
            for path in paths:
                if not os.path.exists(os.path.join(BASE, path)):
                    continue
                checked += 1
                got = found_in(path, name, want)
                if got is None:
                    print('  %s 표식을 못 찾았다: %s' % (name, path))
                    bad += 1
                elif got != want:
                    print('  %s 표가 다르다: %s' % (name, path))
                    bad += 1
        print('손으로 적은 표 %d자리 — 어긋남 %d건' % (checked, bad))
        return 1 if bad else 0
    for name, (want, _paths) in sorted(TABLES.items()):
        print('== %s (%d개) ==' % (name, len(want)))
        print(wrapped('', '    ', values=want))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
