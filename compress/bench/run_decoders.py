# -*- coding: utf-8 -*-
"""복호기만 있는 모듈의 검사 — 다섯 언어가 **진짜 도구가 만든 파일** 을
같게 푸는가 (PLAN.md §0.4, SPEC §15·§16).

    python3 bench/run_decoders.py            # 있는 언어로 전부
    python3 bench/run_decoders.py bzip2dec   # 모듈만 골라서

골든 벡터가 없는 모듈이다. 부호기를 안 만들었으니 "우리가 만든 바이트가
같은가" 를 물을 수 없다. 대신 더 센 것을 묻는다 — 우리가 만들지 않은
파일, 즉 bzip2·xz 가 만든 진짜 파일을 다섯 언어가 전부 **원본과 같은
SHA-256 으로** 푸는가.

파서티 검사와 같은 이유로 batch 를 쓴다 — 언어마다 프로세스 한 번.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'src', 'py'))

sys.path.insert(0, HERE)
from run_parity import (available, corpus_files,      # noqa: E402
                        pad, run_batch)

CORPUS = os.path.join(BASE, 'corpus')
OUT = os.path.join(BASE, 'out')

# 모듈 → (진짜 도구를 부르는 방법, 설정 이름들)
TOOLS = {
    'bzip2dec': ('bzip2', [('-1', ['-1']), ('-9', ['-9'])]),
    # xz 의 --format=lzma 가 LZMA1 "alone" 형식이다 (SPEC §16.1)
    'lzmadec': ('xz', [('-1', ['--format=lzma', '-1']),
                       ('-9', ['--format=lzma', '-9'])]),
}


def make_inputs(algo, workdir):
    """진짜 도구로 시험 파일을 만든다. (이름, 경로, 원본 경로) 목록."""
    cmd, settings = TOOLS[algo]
    made = []
    for name in corpus_files():
        src_path = os.path.join(CORPUS, name)
        data = io.open(src_path, 'rb').read()
        for label, args in settings:
            raw = subprocess.run([cmd] + args + ['-c'], input=data,
                                 stdout=subprocess.PIPE,
                                 check=True).stdout
            dst = os.path.join(workdir, '%s.%s.in' % (name, label))
            io.open(dst, 'wb').write(raw)
            made.append(('%s %s' % (name, label), dst, src_path))
    return made


def sha(path):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()


def check_algo(algo, langs, work):
    inputs = make_inputs(algo, work)
    lines = ['== 1. 진짜 도구가 만든 파일을 다섯이 같게 푸는가 (%s) =='
             % algo,
             '입력은 우리가 만들지 않았다. 골든 벡터보다 센 시험이다.',
             pad('파일 · 설정', 26)
             + ''.join(pad(n, 7, True) for n, _c in langs)]
    fails = 0
    out_dir = os.path.join(work, 'out')
    os.makedirs(out_dir, exist_ok=True)
    got = {}
    for lang, cmd in langs:
        jobs = []
        for _label, path, _orig in inputs:
            name = '%s.%s' % (os.path.basename(path), lang)
            jobs.append((algo, 'dec', path,
                         os.path.join(out_dir, name)))
        results = run_batch(cmd, jobs, work)
        got[lang] = list(zip(results, jobs))
    for i, (label, _path, orig) in enumerate(inputs):
        want = sha(orig)
        row = pad(label, 26)
        for lang, _cmd in langs:
            res, job = got[lang][i]
            if res != 'OK':
                mark, fails = 'ERR', fails + 1
            elif sha(job[3]) != want:
                mark, fails = 'DIFF', fails + 1
            else:
                mark = 'OK'
            row += pad(mark, 7, True)
        lines.append(row)
    lines.append('')
    return '\n'.join(lines) + '\n', fails


def main(argv):
    langs = available()
    algos = [a for a in argv if not a.startswith('-')] or sorted(TOOLS)
    print('언어 %s · 모듈 %d개'
          % (', '.join(n for n, _c in langs), len(algos)))
    total = 0
    for algo in algos:
        work = tempfile.mkdtemp(prefix='dec_%s_' % algo)
        try:
            text, fails = check_algo(algo, langs, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        io.open(os.path.join(OUT, 'decoders_%s.txt' % algo), 'w',
                encoding='utf-8', newline='\n').write(text)
        total += fails
        print('  %-12s 실패 %d건' % (algo, fails))
    print('전체 실패 %d건' % total)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
