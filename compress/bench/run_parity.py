# -*- coding: utf-8 -*-
"""파서티 검사 — 다섯 언어가 같은 바이트를 내고 서로의 것을 푸는가.

    python3 bench/run_parity.py                # 있는 언어로 전부
    python3 bench/run_parity.py huffman lzss   # 모듈만 골라서

두 가지를 본다.

  1. **골든 대조** — 언어마다 코퍼스 파일 전부를 부호화해 SHA-256 이
     golden/ 과 같은지. 이게 "바이트가 같다" 의 증명이다.
  2. **5×5 교차 복호** — 각 언어가 만든 파일을 다섯 언어가 모두 푼다.
     1이 통과하면 파일이 어차피 같으므로 논리적으로는 따라오지만,
     복호기에만 있는 버그(예: 쓰지 않는 분기)는 여기서만 잡힌다.

교차 복호는 코퍼스 일부에서만 돈다. 전부 돌리면 (10 모듈 × 13 파일 ×
25 조합) 이라 3,250건이고, 그만큼의 일을 더 해도 새로 잡히는 것이 없다.
대신 경계를 밟는 파일(빈 것·1바이트·런·알파벳 전부·창 경계)을 고른다.

언어마다 프로세스를 한 번만 띄운다. 건마다 띄우면 JVM 하나로 몇 분이
간다 — 그래서 다섯 언어의 명령줄 도구가 모두 batch 를 갖는다.
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

from compresslib import registry                   # noqa: E402

CORPUS = os.path.join(BASE, 'corpus')
GOLDEN = os.path.join(BASE, 'golden')
OUT = os.path.join(BASE, 'out')
BUILD = os.path.join(BASE, 'build')
SKIP = {'gen_corpus.py', 'MANIFEST.txt', 'README.md', '.gitkeep'}

PYCLI = os.path.join(BASE, 'cli', 'py', 'main.py')
TSCLI = os.path.join(BUILD, 'ts', 'cli', 'ts', 'main.js')

# 언어 → (그 언어가 준비됐는지 보는 경로, batch 를 부르는 명령)
LANGS = [
    ('py', PYCLI, [sys.executable, PYCLI, 'batch']),
    ('cpp', os.path.join(BUILD, 'cppcli'),
     [os.path.join(BUILD, 'cppcli'), 'batch']),
    ('go', os.path.join(BUILD, 'gocli'),
     [os.path.join(BUILD, 'gocli'), 'batch']),
    ('java', os.path.join(BUILD, 'java', 'compresslib', 'Main.class'),
     ['sh', os.path.join(BASE, 'tools', 'flock_java.sh'), 'java', '-cp',
      os.path.join(BUILD, 'java'), 'compresslib.Main', 'batch']),
    ('ts', TSCLI, ['node', TSCLI, 'batch']),
]

# 교차 복호에 쓰는 파일. 경계를 밟는 것만 고른다.
CROSS_FILES = ['empty.bin', 'one.bin', 'abab_4k.txt', 'runs.bin',
               'alphabet.bin', 'boundary_32768.bin', 'korean_utf8.txt']


def corpus_files():
    return sorted(f for f in os.listdir(CORPUS) if f not in SKIP)


def available():
    return [(name, cmd) for name, probe, cmd in LANGS
            if os.path.exists(probe)]


def run_batch(cmd, jobs, workdir):
    """작업 목록을 한 프로세스로 돌리고 줄마다의 결과를 돌려준다."""
    job_path = os.path.join(workdir, 'jobs.txt')
    io.open(job_path, 'w', encoding='utf-8', newline='\n').write(
        '\n'.join('%s %s %s %s' % j for j in jobs) + '\n')
    proc = subprocess.run(cmd + [job_path], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, cwd=BASE)
    lines = proc.stdout.decode('utf-8', 'replace').split('\n')
    lines = [l.strip() for l in lines if l.strip()]
    if len(lines) != len(jobs):
        raise RuntimeError('%s 가 %d줄이 아니라 %d줄을 냈다: %s'
                           % (cmd[0], len(jobs), len(lines),
                              proc.stderr.decode('utf-8',
                                                 'replace')[:200]))
    return lines


def sha(path):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()


def golden_sha(algo, name):
    p = os.path.join(GOLDEN, algo, '%s.sha256' % name)
    return io.open(p, encoding='utf-8').read().strip()


def cells(text):
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1
               for c in text)


def pad(text, width, right=False):
    fill = ' ' * max(0, width - cells(text))
    return (fill + text) if right else (text + fill)


def check_algo(algo, langs, work):
    """한 모듈을 검사하고 (보고서 글, 실패 수) 를 돌려준다."""
    names = corpus_files()
    lines = ['== 1. 부호기 출력이 골든과 같은가 (%s) ==' % algo,
             pad('파일', 20)
             + ''.join(pad(n, 7, True) for n, _c in langs)]
    fails = 0
    enc_dir = os.path.join(work, 'enc')
    os.makedirs(enc_dir, exist_ok=True)
    made = {}
    for lang, cmd in langs:
        jobs = [(algo, 'enc', 'corpus/%s' % n,
                 os.path.join(enc_dir, '%s.%s' % (n, lang)))
                for n in names]
        results = run_batch(cmd, jobs, work)
        made[lang] = {n: (r, j[3])
                      for n, r, j in zip(names, results, jobs)}
    for name in names:
        want = golden_sha(algo, name)
        row = pad(name, 20)
        for lang, _cmd in langs:
            res, path = made[lang][name]
            if res != 'OK':
                mark, fails = 'ERR', fails + 1
            elif sha(path) != want:
                mark, fails = 'DIFF', fails + 1
            else:
                mark = 'OK'
            row += pad(mark, 7, True)
        lines.append(row)
    lines.append('')

    lines.append('== 2. 5×5 교차 복호 (%s) ==' % algo)
    lines.append('만든 쪽 아래로, 푼 쪽 옆으로.')
    lines.append('파일 %d개가 전부 원본과 같아야 한다.'
                 % len(CROSS_FILES))
    lines.append(pad('만든 쪽', 10)
                 + ''.join(pad(n, 7, True) for n, _c in langs))
    dec_dir = os.path.join(work, 'dec')
    os.makedirs(dec_dir, exist_ok=True)
    for maker, _mc in langs:
        row = pad(maker, 10)
        for reader, cmd in langs:
            jobs = []
            for name in CROSS_FILES:
                src = made[maker][name][1]
                jobs.append((algo, 'dec', src,
                             os.path.join(dec_dir, '%s.%s.%s'
                                          % (name, maker, reader))))
            results = run_batch(cmd, jobs, work)
            bad = 0
            for name, res, job in zip(CROSS_FILES, results, jobs):
                orig = os.path.join(CORPUS, name)
                if res != 'OK' or sha(job[3]) != sha(orig):
                    bad += 1
            fails += bad
            row += pad('OK' if not bad else '%d건' % bad, 7, True)
        lines.append(row)
    lines.append('')
    return '\n'.join(lines) + '\n', fails


def main(argv):
    langs = available()
    algos = [a for a in argv if not a.startswith('-')] or registry.ORDER
    print('언어 %s · 모듈 %d개'
          % (', '.join(n for n, _c in langs), len(algos)))
    if len(langs) < 2:
        print('  (언어가 하나뿐이라 교차 검사는 아직 뜻이 없다)')
    total = 0
    for algo in algos:
        work = tempfile.mkdtemp(prefix='parity_%s_' % algo)
        try:
            text, fails = check_algo(algo, langs, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        io.open(os.path.join(OUT, 'parity_%s.txt' % algo), 'w',
                encoding='utf-8', newline='\n').write(text)
        total += fails
        print('  %-12s 실패 %d건' % (algo, fails))
    print('전체 실패 %d건' % total)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
