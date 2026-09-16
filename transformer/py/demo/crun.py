# -*- coding: utf-8 -*-
"""C 기록 실행의 공통 틀 — c/tfs 를 불러 출력을 절로 나눠 싣는다.

학습의 모양(폭·층·스텝·배치)은 여기 각 데모의 SPEC 사전에만 적는다.
덱의 산문은 이 숫자를 손으로 옮기지 않고, 캡처 첫 줄(tfs train 이
찍는 설정 줄)을 인용한다(PLAN.md §9 결정 4).

학습은 스레드 4개로 돈다(스레드 수와 무관하게 같은 가중치가 나온다 —
C 시험이 확인한다). 걸린 시간은 어디에도 적지 않는다.
"""
import io
import os
import re
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TFS = os.path.join(BASE, 'c', 'tfs')
BUILD = os.path.join(BASE, '.build')
THREADS = 4


def tfs(*args):
    """tfs 를 저장소 뿌리에서 돌리고 표준 출력을 돌려준다."""
    r = subprocess.run([TFS] + [str(a) for a in args], cwd=BASE,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)
    return r.stdout.decode('utf-8', 'replace')


def split_text(sub, name, fraction=0.95):
    """corpus/<sub> 전체를 이어 붙여 앞 95% 를 학습, 뒤를 검증으로.
    줄 경계에서 자르고 .build/ 에 둔다(말뭉치에서 늘 같게 만든다)."""
    d = os.path.join(BASE, 'corpus', sub)
    text = ''.join(io.open(os.path.join(d, n), encoding='utf-8',
                           newline='').read()
                   for n in sorted(os.listdir(d)))
    cut = text.rfind('\n', 0, int(len(text) * fraction)) + 1
    out = os.path.join(BUILD, name)
    if not os.path.isdir(out):
        os.makedirs(out)
    for part, body in (('train', text[:cut]), ('valid', text[cut:])):
        io.open(os.path.join(out, part + '.txt'), 'w', encoding='utf-8',
                newline='').write(body)
    return (os.path.join('.build', name, 'train.txt'),
            os.path.join('.build', name, 'valid.txt'))


STEP = re.compile(r'^스텝\s+(\d+)\s+손실 ([\d.]+)\s+학습률 (\S+)\s+'
                  r'노름 ([\d.]+)')
EVAL = re.compile(r'^스텝\s+(\d+)\s+검증 손실 ([\d.]+)')


def train(spec, ckpt, train_file, valid_file=None):
    """학습하고 (설정 줄, 기록 줄 목록, 검증 줄 목록) 을 돌려준다."""
    args = ['train', '--vocab', spec['vocab'], '--train', train_file,
            '--T', spec['T'], '--d', spec['d'], '--L', spec['L'],
            '--h', spec['h'], '--steps', spec['steps'],
            '--batch', spec['B'], '--lr', spec['lr'],
            '--warmup', spec['warmup'], '--seed', spec['seed'],
            '--threads', THREADS, '--out', ckpt, '--log', spec['log']]
    if spec.get('aligned'):
        args.append('--aligned')
    if valid_file:
        args += ['--valid', valid_file, '--eval', spec['eval'],
                 '--eval-batches', spec.get('eval_batches', 8)]
    lines = tfs(*args).rstrip('\n').split('\n')
    head = lines[0]
    steps = [STEP.match(l).groups() for l in lines if STEP.match(l)]
    evals = [EVAL.match(l).groups() for l in lines if EVAL.match(l)]
    return head, steps, evals


def curve_text(steps):
    """그림용 전체 곡선. 한 줄에 '스텝 손실 학습률 노름'."""
    return '\n'.join(' '.join(row) for row in steps)


def pick(steps, every):
    """기록 줄 가운데 첫 줄·every 배수·끝 줄만 — 캡처가 45줄 안에."""
    last = steps[-1][0]
    rows = [r for r in steps
            if r[0] == '1' or int(r[0]) % every == 0 or r[0] == last]
    return '\n'.join('스텝 %5s  손실 %s  학습률 %s  노름 %s' % r
                     for r in rows)
