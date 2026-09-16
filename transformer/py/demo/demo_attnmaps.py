# -*- coding: utf-8 -*-
"""6부 — 학습된 어텐션 지도. C 가 학습한 체크포인트를 파이썬이 읽어
같은 순전파로 가중치를 꺼낸다(두 구현이 같은 체크포인트를 읽는다는
약속, SPEC §4 가 여기서 쓸모를 보인다).

그림(deck/gen_figs.py)은 이 캡처의 행렬을 읽어 그린다. 사람이 읽을
표로는 헤드마다 "각 질의가 가장 많이 본 키" 를 적는다.
"""
import os

from demo import report
from transformerlib import model as M
from transformerlib import tokenizer as tk
from transformerlib import train as TR

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

CASES = [
    ('add', 'c_add.ckpt', 'add', '042+915=7590'),
    ('sort', 'c_sort.ckpt', 'sort', 'qwerty>eqrtwy'),
    ('ko', 'c_ko.ckpt', 'ko512', '김 첨지는 오래간만에 돈을 벌었다.'),
]


def shown(tok, i):
    s = tok.vocab[i].decode('utf-8', 'replace')
    return s.replace(' ', '␣').replace('\n', '↵') or '?'


def maps(name, ckpt, vocab, text):
    cfg, params = TR.load_ckpt(os.path.join(BASE, 'ckpt', ckpt))
    prefix = os.path.join(BASE, 'ckpt', 'tok', vocab)
    tok = tk.Tokenizer(*tk.load(prefix))
    ids = tok.encode(text)[:cfg.T]
    out = []
    M.forward(params, cfg, [ids], attn_out=out)
    labels = [shown(tok, i) for i in ids]
    lines = ['토큰 %d개: %s' % (len(ids), ' '.join(labels))]
    n = len(ids)
    for l, w in enumerate(out):
        for h in range(cfg.h):
            lines.append('블록 %d 헤드 %d' % (l, h))
            for i in range(n):
                row = w.data[(h * n + i) * n:(h * n + i + 1) * n]
                lines.append(' '.join('%.3f' % v for v in row))
    best = []
    last = out[-1]
    for h in range(cfg.h):
        top = []
        for i in range(n):
            row = last.data[(h * n + i) * n:(h * n + i + 1) * n]
            j = max(range(n), key=lambda k: (row[k], -k))
            top.append('%s→%s' % (labels[i], labels[j]))
        best.append('헤드 %d: %s' % (h, ' '.join(top)))
    return '\n'.join(lines), '\n'.join(best)


def main():
    sections = []
    for name, ckpt, vocab, text in CASES:
        full, best = maps(name, ckpt, vocab, text)
        sections.append(('%s — 마지막 블록, 질의마다 가장 많이 본 키'
                         % name, best))
        sections.append(('%s — 가중치 행렬 전부' % name, full))
    return report.write('attnmaps.txt', sections)


if __name__ == '__main__':
    print(main())
