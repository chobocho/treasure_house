# -*- coding: utf-8 -*-
"""5부 — 바이트 BPE 가 한국어와 영어에서 어휘를 어떻게 쓰나."""
import io
import os

from demo import report
from transformerlib import fmt
from transformerlib import tokenizer as tk

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CORPUS = os.path.join(BASE, 'corpus')


def read_group(sub):
    d = os.path.join(CORPUS, sub)
    return ''.join(io.open(os.path.join(d, n), encoding='utf-8',
                           newline='').read()
                   for n in sorted(os.listdir(d)))


def shown(b):
    """토큰 바이트열을 사람이 읽을 꼴로. 깨진 UTF-8 은 16진."""
    try:
        s = b.decode('utf-8')
    except UnicodeDecodeError:
        return '<' + b.hex(' ') + '>'
    return s.replace(' ', '␣').replace('\n', '↵')


def sec_pretokenize():
    text = '김 첨지는 80전을 벌고 "운수 좋은 날"이라고  했다.\n'
    chunks = tk.pretokenize(text)
    return ('입력: ' + text.replace('\n', '↵') + '\n조각 '
            + str(len(chunks)) + '개: '
            + ' | '.join(shown(c.encode('utf-8')) for c in chunks))


def sec_first_merges(ko, en):
    rows = [['순위', '한국어 병합이 만든 토큰',
             '영어 병합이 만든 토큰']]
    for r in range(20):
        rows.append([str(r), shown(ko[0][256 + r]),
                     shown(en[0][256 + r])])
    return (fmt.table(rows, align='rll')
            + '\n\n<…> 는 UTF-8 글자의 일부만 담은 토큰이다. 한글'
            + ' 음절은'
            + ' 3바이트라\n처음 병합들은 음절의 앞 두 바이트를 묶는다.')


def sec_vocab_sizes(ko_text, en_text):
    rows = [['어휘 크기', '한국어 바이트/토큰', '영어 바이트/토큰']]
    kb, eb = len(ko_text.encode('utf-8')), len(en_text.encode('utf-8'))
    for V in (256, 384, 512, 1024):
        k = tk.Tokenizer(*tk.train_bpe(ko_text, V)).encode(ko_text)
        e = tk.Tokenizer(*tk.train_bpe(en_text, V)).encode(en_text)
        rows.append([str(V), '%.3f' % (float(kb) / len(k)),
                     '%.3f' % (float(eb) / len(e))])
    return (fmt.table(rows, align='rrr')
            + '\n\n같은 어휘 크기에서 한국어 토큰 하나가 담는 바이트가'
            + ' 더 많지만,'
            + '\n한글 음절이 3바이트라 음절로 따지면 영어 글자보다 적게'
            + ' 담는다.')


def sec_syllables(ko_text, ko):
    toks = tk.Tokenizer(*ko).encode(ko_text)
    syl = sum(1 for c in ko_text if 0xAC00 <= ord(c) <= 0xD7A3)
    whole = 0
    for t in set(toks):
        s = ko[0][t]
        try:
            u = s.decode('utf-8')
            whole += any(0xAC00 <= ord(c) <= 0xD7A3 for c in u)
        except UnicodeDecodeError:
            pass
    return ('한국어 말뭉치: 한글 음절 {:,}개 · BPE-512 토큰 {:,}개\n'
            '어휘 512개 가운데 온전한 음절을 하나 이상 담은 토큰: {}개'
            .format(syl, len(toks), whole))


def sec_round_trip(ko):
    """접힌 화면(108칸)에 맞게 id 는 10개, 토큰은 6개씩 줄을 나눈다."""
    t = tk.Tokenizer(*ko)
    text = '밑바닥부터 만드는 트랜스포머'
    ids = t.encode(text)
    lines = ['입력: %s (%d바이트)' % (text, len(text.encode('utf-8')))]
    for k in range(0, len(ids), 10):
        lines.append(('id: ' if k == 0 else '    ')
                     + ' '.join('%3d' % i for i in ids[k:k + 10]))
    toks = [shown(t.vocab[i]) for i in ids]
    for k in range(0, len(toks), 6):
        lines.append(('토큰: ' if k == 0 else '      ')
                     + ' | '.join(toks[k:k + 6]))
    lines.append('토큰 %d개 · 되돌리기: %s' % (len(ids), t.decode(ids)))
    return '\n'.join(lines)


def main():
    ko_text, en_text = read_group('ko'), read_group('en')
    ko = tk.load(os.path.join(BASE, 'ckpt', 'tok', 'ko512'))
    en = tk.load(os.path.join(BASE, 'ckpt', 'tok', 'en512'))
    return report.write('tokenizer.txt', [
        ('사전 토크나이저가 자른 조각', sec_pretokenize()),
        ('처음 배운 병합 스무 개', sec_first_merges(ko, en)),
        ('어휘 크기와 압축률', sec_vocab_sizes(ko_text, en_text)),
        ('음절과 토큰', sec_syllables(ko_text, ko)),
        ('인코드와 디코드', sec_round_trip(ko)),
    ])


if __name__ == '__main__':
    print(main())
