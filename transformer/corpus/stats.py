# -*- coding: utf-8 -*-
"""말뭉치 통계 — 바이트·글자·음절을 세어 out/corpus_stats.txt 로.

    python3 corpus/stats.py

5부(토크나이저)의 첫 질문에 숫자로 답하려고 있다. "한글 한 글자는
몇 바이트인가" 는 외울 일이 아니라 세어 볼 일이다. 한글 음절
(U+AC00‥U+D7A3)은 UTF-8 로 늘 3바이트이고, 영어 글자는 1바이트다.
그 차이가 바이트 BPE 의 어휘를 어디에 쓰게 하는지가 5부의 이야기다.
시간 O(말뭉치 바이트 수).
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'py'))
from transformerlib import fmt                       # noqa: E402

OUT = os.path.join(BASE, 'out', 'corpus_stats.txt')


def is_syllable(c):
    return 0xAC00 <= ord(c) <= 0xD7A3


def count(path):
    """(바이트, 글자, 한글 음절, 줄) — 줄바꿈도 글자로 센다."""
    raw = io.open(path, 'rb').read()
    text = raw.decode('utf-8')
    return (len(raw), len(text), sum(1 for c in text if is_syllable(c)),
            text.count('\n'))


def files(sub):
    d = os.path.join(HERE, sub)
    return sorted(os.path.join(sub, n) for n in os.listdir(d)
                  if n.endswith('.txt'))


def utf8_lengths(text):
    """UTF-8 바이트 길이별 글자 수 {1: …, 2: …, 3: …, 4: …}."""
    hist = {1: 0, 2: 0, 3: 0, 4: 0}
    for c in text:
        hist[len(c.encode('utf-8'))] += 1
    return hist


def report():
    out = []
    groups = [('ko', '한국어 (위키문헌)'),
              ('en', '영어 (tinyshakespeare)'),
              ('tasks', '합성 과제')]
    out.append('== 1. 묶음별 크기 ==')
    rows = [['묶음', '파일', '바이트', '글자', '한글 음절',
             '바이트/글자']]
    total = [0, 0, 0]
    for sub, label in groups:
        n = b = c = s = 0
        for f in files(sub):
            fb, fc, fs, _ = count(os.path.join(HERE, f))
            n, b, c, s = n + 1, b + fb, c + fc, s + fs
        total = [total[0] + n, total[1] + b, total[2] + c]
        rows.append([label, str(n), '{:,}'.format(b), '{:,}'.format(c),
                     '{:,}'.format(s), '%.3f' % (float(b) / c)])
    rows.append(['합계', str(total[0]), '{:,}'.format(total[1]),
                 '{:,}'.format(total[2]), '', ''])
    out.append(fmt.table(rows, align='lrrrrr'))
    out.append('')

    out.append('== 2. UTF-8 바이트 길이별 글자 수 ==')
    rows = [['묶음', '1바이트', '2바이트', '3바이트', '4바이트']]
    for sub, label in groups[:2]:
        h = {1: 0, 2: 0, 3: 0, 4: 0}
        for f in files(sub):
            t = io.open(os.path.join(HERE, f), encoding='utf-8').read()
            for k, v in utf8_lengths(t).items():
                h[k] += v
        rows.append([label] + ['{:,}'.format(h[k])
                               for k in (1, 2, 3, 4)])
    out.append(fmt.table(rows, align='lrrrr'))
    out.append('')

    out.append('== 3. 한국어 작품별 ==')
    rows = [['파일', '바이트', '음절', '줄']]
    for f in files('ko'):
        fb, _, fs, fl = count(os.path.join(HERE, f))
        rows.append([f[3:-4], '{:,}'.format(fb), '{:,}'.format(fs),
                     str(fl)])
    out.append(fmt.table(rows, align='lrrr'))
    out.append('')

    out.append('== 4. 음절 하나를 바이트로 ==')
    for word in ('가', '한', '글', '힣', 'A'):
        bs = word.encode('utf-8')
        hexes = ' '.join('%02X' % x for x in bs)
        out.append('%s  U+%04X  %s' % (word, ord(word), hexes))
    return '\n'.join(out) + '\n'


def main():
    text = report()
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
