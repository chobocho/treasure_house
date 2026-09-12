# -*- coding: utf-8 -*-
"""엔트로피를 실제로 재 본다 — 1부의 모든 숫자가 여기서 나온다.

    python3 bench/entropy.py            # out/entropy.txt
    python3 bench/entropy.py english.txt  # 한 파일만 화면에

왜 도구를 따로 두나: 1부는 "줄일 수 있는 여지" 를 말하는 부인데, 그
여지는 파일마다 다르고 **몇 차 문맥으로 보느냐에 따라 또 다르다.**
설명만 하면 독자가 확인할 길이 없다. 그래서 재는 쪽을 코드로 둔다.

차수의 뜻은 이렇다.
  0차  앞을 안 본다. 바이트 빈도만
  1차  바로 앞 한 바이트를 보고
  2차  앞 두 바이트를 보고

차수를 올리면 값이 내려간다. 그런데 **끝없이 내려가지는 않는다** —
문맥이 늘면 셀 표본이 줄어서, 어느 지점부터는 '외운 것' 이지 '안 것'
이 아니게 된다. 그 경계가 11부 PPM 의 출발점이다.
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
CORPUS = os.path.join(BASE, 'corpus')
GOLDEN = os.path.join(BASE, 'golden')
OUT = os.path.join(BASE, 'out')
SKIP = {'gen_corpus.py', 'MANIFEST.txt', 'README.md', '.gitkeep'}


def cells(text):
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1
               for c in text)


def pad(text, width, right=False):
    fill = ' ' * max(0, width - cells(text))
    return (fill + text) if right else (text + fill)


def entropy0(data):
    """바이트 하나에 든 정보량 (비트). 앞을 안 본다."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    total = float(len(data))
    out = 0.0
    for c in counts:
        if c:
            p = c / total
            out -= p * math.log(p, 2)
    return out


def entropy_n(data, order):
    """앞 order 바이트를 문맥으로 본 조건부 엔트로피 (비트/바이트).

    문맥마다 따로 세고, 그 문맥이 나온 횟수로 가중 평균한다. 앞쪽
    order 바이트는 문맥이 모자라 세지 않는다 — 전체에 견주면 무시할
    수 있는 수이고, 억지로 채우면 없는 정보를 넣는 꼴이 된다.
    """
    if len(data) <= order:
        return 0.0
    table = {}
    for i in range(order, len(data)):
        ctx = bytes(data[i - order:i])
        row = table.get(ctx)
        if row is None:
            row = table[ctx] = [0] * 257    # 마지막 칸은 그 문맥의 합
        row[data[i]] += 1
        row[256] += 1
    total = float(len(data) - order)
    out = 0.0
    for row in table.values():
        n = float(row[256])
        for c in row[:256]:
            if c:
                out -= (n / total) * (c / n) * math.log(c / n, 2)
    return out


def corpus_files():
    return sorted(f for f in os.listdir(CORPUS) if f not in SKIP)


def golden_size(algo, name):
    p = os.path.join(GOLDEN, algo, '%s.size' % name)
    if not os.path.exists(p):
        return None
    return int(io.open(p, encoding='utf-8').read().strip())


def report():
    names = corpus_files()
    lines = ['== 차수별 엔트로피 (비트/바이트) ==',
             '0차는 바이트 빈도만, 1·2차는 앞 바이트를 문맥으로 본다.',
             '오른쪽 두 칸은 그 엔트로피가 말하는 최소 크기(바이트).',
             '']
    lines.append(pad('파일', 22) + pad('크기', 9, True)
                 + pad('0차', 7, True) + pad('1차', 7, True)
                 + pad('2차', 7, True) + pad('0차 최소', 10, True)
                 + pad('2차 최소', 10, True))
    for n in names:
        data = io.open(os.path.join(CORPUS, n), 'rb').read()
        if len(data) > 262144:
            # 1 MiB 파일의 2차 표는 이 기계에서 너무 크다. 앞 256 KiB
            # 만 본다 — 그 사실을 숨기지 말고 이름 옆에 적는다.
            data = data[:262144]
            label = n + ' (앞 256K)'
        else:
            label = n
        h0 = entropy0(data)
        h1 = entropy_n(data, 1)
        h2 = entropy_n(data, 2)
        lines.append(pad(label, 22) + pad('%d' % len(data), 9, True)
                     + pad('%.2f' % h0, 7, True)
                     + pad('%.2f' % h1, 7, True)
                     + pad('%.2f' % h2, 7, True)
                     + pad('%d' % int(len(data) * h0 / 8), 10, True)
                     + pad('%d' % int(len(data) * h2 / 8), 10, True))

    lines.append('')
    lines.append('== 0차 한계와 실제 결과 ==')
    lines.append('허프만은 0차 모델이다. 그 한계에 얼마나 붙었나.')
    lines.append('')
    lines.append(pad('파일', 20) + pad('원본', 9, True)
                 + pad('0차 한계', 10, True) + pad('huffman', 10, True)
                 + pad('차이', 8, True) + pad('deflate', 10, True))
    for n in names:
        raw = os.path.getsize(os.path.join(CORPUS, n))
        if raw < 1024:
            continue
        data = io.open(os.path.join(CORPUS, n), 'rb').read()
        limit = int(raw * entropy0(data) / 8)
        huff = golden_size('huffman', n)
        defl = golden_size('deflate', n)
        if huff is None or defl is None:
            continue
        lines.append(pad(n, 20) + pad('%d' % raw, 9, True)
                     + pad('%d' % limit, 10, True)
                     + pad('%d' % huff, 10, True)
                     + pad('+%d' % (huff - limit), 8, True)
                     + pad('%d' % defl, 10, True))
    lines.append('')
    lines.append('deflate 가 0차 한계보다 작은 것은 규칙을 어긴 것이')
    lines.append('아니다. 그 한계는 0차 모델의 한계일 뿐이고,')
    lines.append('deflate 는 LZ77 로 되풀이를 먼저 지워 모델을 바꾼다.')
    return lines


def main(argv):
    if argv:
        for n in argv:
            data = io.open(os.path.join(CORPUS, n), 'rb').read()
            print('%s  0차 %.4f  1차 %.4f  2차 %.4f'
                  % (n, entropy0(data), entropy_n(data, 1),
                     entropy_n(data, 2)))
        return 0
    os.makedirs(OUT, exist_ok=True)
    text = '\n'.join(report()) + '\n'
    io.open(os.path.join(OUT, 'entropy.txt'), 'w',
            encoding='utf-8', newline='\n').write(text)
    print('  out/entropy.txt — 코퍼스 %d개' % len(corpus_files()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
