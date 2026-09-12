# -*- coding: utf-8 -*-
"""속도와 비율 재기 — 덱의 숫자는 전부 여기서 나온다.

    python3 bench/run_bench.py            # 전부
    python3 bench/run_bench.py --quick    # 빠른 모듈만 (cm·ppm 제외)

**비율과 속도를 한 파일에 섞지 않는다.** 비율은 두 번 재도 같지만
속도는 그렇지 않기 때문이다. 같은 파일에 두면 그 파일 전체가 재현
불가가 되고, 그러면 "이 캡처는 두 번 떠서 같아야 한다" 는 규칙을
비율에까지 적용할 수 없게 된다.

  out/bench_ratio.txt   골든 크기에서 바로 만든다 — 아무것도 안 돌린다
  out/bench_speed.txt   진짜로 재는 것. 두 번 떠도 같지 않다
  out/bench_lang.txt    언어별 합계 — 이것도 시간이라 같지 않다
  out/manifest.json     out/ 의 모든 캡처와 코퍼스의 SHA-256

비율을 골든에서 가져오는 것이 요점이다. 골든은 이미 다섯 언어가 같은
바이트를 낸다는 것이 증명된 크기다. 여기서 다시 부호화해 재면 그 숫자가
골든과 어긋날 여지가 생긴다 — 어긋나면 어느 쪽이 맞는지 알 수 없다.
"""
import io
import json
import os
import subprocess
import sys
import time

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

# 속도는 이 파일 하나로 잰다. 코퍼스 전부로 재면 cm 하나가 다섯 언어
# × 세 번에 한 시간을 먹는다. 영어 산문은 이 책의 모든 모델이 뭔가
# 할 말이 있는 입력이라 모듈 사이의 차이가 가장 잘 드러난다.
SPEED_FILE = 'english.txt'
SPEED_ROUNDS = 3            # 가장 빠른 회차를 쓴다 (§8)
MAX_REPS = 1024             # 되풀이 상한 — 빠른 모듈이 여기 걸린다

# 느린 모듈. --quick 에서 뺀다.
SLOW = {'cm', 'ppm'}


def corpus_files():
    return sorted(f for f in os.listdir(CORPUS) if f not in SKIP)


def available():
    return [(name, cmd) for name, probe, cmd in LANGS
            if os.path.exists(probe)]


def cells(text):
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1
               for c in text)


def pad(text, width, right=False):
    fill = ' ' * max(0, width - cells(text))
    return (fill + text) if right else (text + fill)


# 표 머리에 쓸 짧은 이름. boundary_32768 과 32769 는 앞 9글자가
# 같아서 그냥 자르면 두 칸이 똑같아진다 — 뒤를 남긴다.
def short(name):
    stem = name.split('.')[0]
    if stem.startswith('boundary_'):
        return 'b' + stem[9:]
    return stem.replace('_', '')[:8]


def golden_size(algo, name):
    p = os.path.join(GOLDEN, algo, '%s.size' % name)
    if not os.path.exists(p):
        return None
    return int(io.open(p, encoding='utf-8').read().strip())


def write(path, lines):
    io.open(path, 'w', encoding='utf-8', newline='\n').write(
        '\n'.join(lines) + '\n')


def ratio_report():
    """골든 크기만으로 만드는 비율표. 아무것도 돌리지 않는다."""
    names = corpus_files()
    raw = {n: os.path.getsize(os.path.join(CORPUS, n)) for n in names}
    total_raw = sum(raw.values())

    lines = ['== 압축비 — 골든 벡터의 크기 그대로 ==',
             '다섯 언어가 같은 바이트를 낸다는 것은 파서티가 봤다.',
             '여기서는 그 크기를 읽기만 한다 (out/parity_*.txt).',
             '']
    head = pad('모듈', 12) + pad('원본', 10, True)
    head += pad('결과', 11, True)
    head += pad('비율', 8, True) + pad('영어 산문', 10, True)
    lines.append(head)
    rows = []
    for algo in registry.ORDER:
        sizes = {n: golden_size(algo, n) for n in names}
        if any(v is None for v in sizes.values()):
            continue
        total = sum(sizes.values())
        # 대표 숫자는 영어 산문으로 잡는다. 전체 비율은 코퍼스에
        # 섞인 0 채움과 난수에 끌려다녀 모듈끼리 비교가 안 된다.
        eng = sizes['english.txt'] / float(raw['english.txt'])
        rows.append((total / float(total_raw), algo, total, eng))
    for ratio, algo, total, eng in sorted(rows):
        lines.append(pad(algo, 12) + pad('%d' % total_raw, 10, True)
                     + pad('%d' % total, 11, True)
                     + pad('%.1f%%' % (ratio * 100), 8, True)
                     + pad('%.1f%%' % (eng * 100), 10, True))
    lines.append('')
    lines.append('코퍼스 %d개 파일 · 원본 %d 바이트'
                 % (len(names), total_raw))

    lines.append('')
    lines.append('== 파일별 비율 (%) ==')
    cols = [n for n in names if raw[n] >= 4096]
    lines.append(pad('모듈', 12)
                 + ''.join(pad(short(n), 9, True) for n in cols))
    for _r, algo, _t, _e in sorted(rows):
        row = pad(algo, 12)
        for n in cols:
            s = golden_size(algo, n)
            row += pad('%.1f' % (100.0 * s / raw[n]), 9, True)
        lines.append(row)
    return lines


def time_one(cmd, jobs, work):
    """작업 목록을 한 프로세스로 돌리고 걸린 시간(초)을 돌려준다."""
    job_path = os.path.join(work, 'jobs.txt')
    write(job_path, ['%s %s %s %s' % j for j in jobs])
    start = time.time()
    proc = subprocess.run(cmd + [job_path], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, cwd=BASE)
    took = time.time() - start
    if proc.returncode != 0:
        raise RuntimeError('%s 가 실패했다: %s'
                           % (cmd[0], proc.stderr.decode(
                               'utf-8', 'replace')[:200]))
    return took


def measure(cmd, jobs, startup, work, bytes_once):
    """같은 작업을 잴 만해질 때까지 되풀이해 KB/s 를 낸다.

    한 번만 재면 C++ 의 61 KB 부호화는 1밀리초도 안 걸려서, 프로세스
    시작 값을 빼고 나면 남는 것이 시계의 분해능뿐이다. 실제로 처음
    재 봤을 때 다섯 모듈이 나란히 같은 숫자를 냈다 — 그게 clamp 값
    이었다. 그래서 0.25초를 넘길 때까지 작업을 늘린다.
    """
    reps = 1
    while True:
        t = min(time_one(cmd, jobs * reps, work)
                for _ in range(SPEED_ROUNDS)) - startup
        if t >= 0.25 or reps >= MAX_REPS:
            return bytes_once * reps / 1024.0 / max(t, 1e-4)
        reps *= 4


def speed_report(algos, langs, work):
    """모듈 × 언어의 처리량. 프로세스 시작 값도 함께 적는다."""
    src = os.path.join(CORPUS, SPEED_FILE)
    raw = os.path.getsize(src)
    lines = ['== 속도 — %s (%d 바이트) ==' % (SPEED_FILE, raw),
             '잴 만해질 때까지 되풀이하고, 그 묶음을 %d번 돌려'
             % SPEED_ROUNDS,
             '가장 빠른 회차를 쓴다. 단위는 KB/s.',
             '**이 캡처는 두 번 떠도 같지 않다** — 시간이기 때문이다.',
             '프로세스 시작(빈 작업)을 따로 재서 빼 두었다.',
             '']

    # 빈 작업 한 줄로 프로세스 시작 값을 잰다. JVM 은 이것이 크다.
    startup = {}
    enc0 = os.path.join(work, 'zero.bin')
    io.open(enc0, 'wb').write(b'')
    for name, cmd in langs:
        jobs = [('bitio', 'enc', enc0, os.path.join(work, 'z.out'))]
        startup[name] = min(time_one(cmd, jobs, work)
                            for _ in range(SPEED_ROUNDS))
    lines.append(pad('프로세스 시작', 14)
                 + ''.join(pad('%.0fms' % (startup[n] * 1000), 9, True)
                           for n, _c in langs))
    lines.append('')

    lines.append(pad('모듈', 12) + pad('', 2)
                 + ''.join(pad(n, 9, True) for n, _c in langs))
    for algo in algos:
        enc = os.path.join(work, '%s.enc' % algo)
        dec = os.path.join(work, '%s.dec' % algo)
        row_e = pad(algo, 12) + pad('부호', 2)
        row_d = pad('', 12) + pad('복호', 2)
        for name, cmd in langs:
            v = measure(cmd, [(algo, 'enc', src, enc)], startup[name],
                        work, raw)
            row_e += pad('%.0f' % v, 9, True)
            v = measure(cmd, [(algo, 'dec', enc, dec)], startup[name],
                        work, raw)
            row_d += pad('%.0f' % v, 9, True)
        lines.append(row_e)
        lines.append(row_d)
    return lines


def lang_report(algos, langs, work):
    """언어별 합계 — 한 프로세스가 모든 모듈을 부호화한 시간."""
    src = os.path.join(CORPUS, SPEED_FILE)
    raw = os.path.getsize(src)
    lines = ['== 언어별 합계 — %s 를 모듈 %d개로 ==' % (SPEED_FILE,
                                                     len(algos)),
             '한 프로세스가 부호화를 모두 한 처리량. 재현 불가.',
             '']
    lines.append(pad('언어', 10) + pad('KB/s', 10, True)
                 + pad('파이썬 대비', 12, True))
    base = None
    for name, cmd in langs:
        jobs = [(a, 'enc', src, os.path.join(work, '%s.%s' % (a, name)))
                for a in algos]
        startup = 0.0
        v = measure(cmd, jobs, startup, work, raw * len(algos))
        if base is None:
            base = v
        lines.append(pad(name, 10) + pad('%.0f' % v, 10, True)
                     + pad('%.1f배' % (v / base), 12, True))
    return lines


def tool_versions():
    """캡처가 어느 도구에서 나왔는지. 숫자가 달라지면 여기부터 본다."""
    out = {}
    probes = [('python', [sys.executable, '--version']),
              ('g++', ['g++', '--version']),
              ('go', ['go', 'version']),
              ('node', ['node', '--version']),
              ('java', ['java', '-version'])]
    for name, cmd in probes:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            first = p.stdout.decode('utf-8', 'replace').split('\n')[0]
            out[name] = first.strip()
        except OSError:
            out[name] = None
    return out


def manifest():
    """out/ 과 코퍼스의 지문. 덱에 실린 캡처가 어느 실행의 것인지."""
    import hashlib

    def sha(path):
        return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()

    captures = {}
    for n in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, n)
        if os.path.isfile(p) and not n.startswith('.') \
                and n != 'manifest.json':
            captures[n] = {'sha256': sha(p),
                           'bytes': os.path.getsize(p)}
    corpus = {n: {'sha256': sha(os.path.join(CORPUS, n)),
                  'bytes': os.path.getsize(os.path.join(CORPUS, n))}
              for n in corpus_files()}
    golden = 0
    for a in sorted(os.listdir(GOLDEN)):
        d = os.path.join(GOLDEN, a)
        if not os.path.isdir(d):
            continue
        golden += sum(1 for f in os.listdir(d)
                      if f.endswith('.sha256'))
    return {
        'modules': registry.ALL,
        'encoding_modules': registry.ORDER,
        'decode_only': registry.DECODE_ONLY,
        'golden_vectors': golden,
        'corpus': corpus,
        'captures': captures,
        'tools': tool_versions(),
        # 시각은 일부러 안 넣는다. 넣으면 manifest 가 두 번 떠서
        # 같을 수 없고, 그러면 재현 검사에서 뺄 수밖에 없다.
    }


def main(argv):
    quick = '--quick' in argv
    langs = available()
    if not langs:
        print('지은 언어가 없다 — make build 먼저')
        return 1
    algos = [a for a in registry.ORDER if not (quick and a in SLOW)]
    os.makedirs(OUT, exist_ok=True)
    work = os.path.join(BUILD, 'bench')
    os.makedirs(work, exist_ok=True)

    write(os.path.join(OUT, 'bench_ratio.txt'), ratio_report())
    print('  out/bench_ratio.txt — 모듈 %d개' % len(registry.ORDER))

    write(os.path.join(OUT, 'bench_speed.txt'),
          speed_report(algos, langs, work))
    print('  out/bench_speed.txt — 모듈 %d개 × 언어 %d개'
          % (len(algos), len(langs)))

    write(os.path.join(OUT, 'bench_lang.txt'),
          lang_report(algos, langs, work))
    print('  out/bench_lang.txt — 언어 %d개' % len(langs))

    io.open(os.path.join(OUT, 'manifest.json'), 'w',
            encoding='utf-8', newline='\n').write(
        json.dumps(manifest(), ensure_ascii=False, indent=2,
                   sort_keys=True) + '\n')
    print('  out/manifest.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
