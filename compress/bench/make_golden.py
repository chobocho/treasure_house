# -*- coding: utf-8 -*-
"""골든 벡터를 만든다 — 다섯 언어가 같은 바이트를 냈는지 재는 자.

    python3 bench/make_golden.py            # 다시 만든다
    python3 bench/make_golden.py --check    # 만들지 않고 대조만

파이썬 참조 구현이 코퍼스 파일마다 낸 출력의 SHA-256 과 크기를
golden/<알고리즘>/<파일>.sha256 · .size 에 적는다. 나머지 네 언어는
이 값과 한 글자도 다르면 안 된다.

**골든을 다시 만드는 것은 "지금까지의 출력이 틀렸다" 는 선언이다.**
왜 바뀌어야 하는지 커밋 메시지에 적지 않고 돌리지 말 것. 시험이나
골든을 고쳐 통과시키는 것은 이 프로젝트에서 가장 하면 안 되는 일이다.
"""
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'src', 'py'))

from compresslib import registry                   # noqa: E402

CORPUS = os.path.join(BASE, 'corpus')
GOLDEN = os.path.join(BASE, 'golden')
# 코퍼스 디렉터리에서 시험 자료가 아닌 것들
SKIP = {'gen_corpus.py', 'MANIFEST.txt', 'README.md', '.gitkeep'}


def corpus_files():
    return sorted(f for f in os.listdir(CORPUS) if f not in SKIP)


def run(check):
    names = corpus_files()
    bad = 0
    rows = []
    for algo in registry.ORDER:
        outdir = os.path.join(GOLDEN, algo)
        if not check:
            os.makedirs(outdir, exist_ok=True)
        for name in names:
            data = io.open(os.path.join(CORPUS, name), 'rb').read()
            out = registry.encode(algo, data)
            # 만들자마자 되풀어 본다. 골든에 한 번 잘못 들어가면
            # 나머지 네 언어가 그 틀린 값을 좇게 된다.
            if registry.decode(algo, out) != data:
                sys.exit('%s/%s 왕복 실패 — 골든을 만들 수 없다'
                         % (algo, name))
            digest = hashlib.sha256(out).hexdigest()
            rows.append((algo, name, len(data), len(out)))
            for ext, text in (('sha256', digest + '\n'),
                              ('size', '%d\n' % len(out))):
                path = os.path.join(outdir, '%s.%s' % (name, ext))
                if check:
                    if not os.path.exists(path):
                        print('  없음 %s/%s.%s' % (algo, name, ext))
                        bad += 1
                    elif io.open(path, encoding='utf-8').read() != text:
                        print('  다름 %s/%s.%s' % (algo, name, ext))
                        bad += 1
                else:
                    io.open(path, 'w', encoding='utf-8',
                            newline='\n').write(text)
    return rows, bad


def main(argv):
    check = '--check' in argv
    rows, bad = run(check)
    print('알고리즘 %d개 × 파일 %d개 = 골든 %d쌍'
          % (len(registry.ORDER), len(corpus_files()), len(rows)))
    if check:
        print('대조 결과 어긋남 %d건' % bad)
        return 1 if bad else 0
    # 비율 표 — 사람이 눈으로 이상한 자리를 찾기 위한 것이다
    print('%-12s %10s %10s %7s' % ('알고리즘', '원본', '결과', '비율'))
    for algo in registry.ORDER:
        tot_in = sum(r[2] for r in rows if r[0] == algo)
        tot_out = sum(r[3] for r in rows if r[0] == algo)
        print('%-12s %10d %10d %6.1f%%'
              % (algo, tot_in, tot_out, 100.0 * tot_out / tot_in))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
