# -*- coding: utf-8 -*-
"""compresslib 명령줄 도구 — 다섯 언어가 똑같은 사용법을 갖는다.

    python3 cli/py/main.py <알고리즘> enc|dec <입력> <출력>
    python3 cli/py/main.py list

다섯 언어에 같은 도구를 두는 이유는 하나다. 파서티 검사가 "파이썬이 만든
파일을 자바가 푸는" 식으로 25가지 조합을 돌리는데, 그러려면 바깥에서
똑같이 부를 수 있어야 한다. 라이브러리끼리 부르면 그 검사를 못 한다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'src', 'py'))

from compresslib import registry                   # noqa: E402

USAGE = ('사용법: main.py <알고리즘> enc|dec <입력> <출력>\n'
         '        main.py batch <작업파일>\n'
         '        main.py list')


def run_one(algo, mode, src_path, dst_path):
    """한 건. 실패하면 사람이 읽을 문장을 돌려준다."""
    if algo not in registry.MODULES:
        return '모르는 알고리즘: %s' % algo
    if mode not in ('enc', 'dec'):
        return 'enc 또는 dec 이어야 한다: %s' % mode
    with open(src_path, 'rb') as f:
        data = f.read()
    try:
        out = (registry.encode(algo, data) if mode == 'enc'
               else registry.decode(algo, data))
    except ValueError as e:
        return '%s %s 실패: %s' % (algo, mode, e)
    with open(dst_path, 'wb') as f:
        f.write(out)
    return None


def batch(job_path):
    """작업 목록을 한 프로세스에서 전부 처리한다.

    파서티 검사는 (알고리즘 × 파일 × 언어) 조합이 수천 건이라, 건마다
    프로세스를 띄우면 JVM 하나만으로도 몇 분이 간다. 그래서 다섯 언어
    모두 batch 를 갖는다. 한 줄에 한 건:
    "<알고리즘> enc|dec <입력> <출력>".
    결과도 한 줄에 하나씩 OK 또는 FAIL <사유> 로 찍는다.
    """
    with open(job_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 4:
                print('FAIL 칸이 4개가 아니다')
                continue
            err = run_one(*parts)
            print('FAIL ' + err if err else 'OK')
    return 0


def main(argv):
    if len(argv) == 1 and argv[0] == 'list':
        print('\n'.join(registry.ORDER))
        return 0
    if len(argv) == 2 and argv[0] == 'batch':
        return batch(argv[1])
    if len(argv) != 4:
        sys.stderr.write(USAGE + '\n')
        return 2
    err = run_one(*argv)
    if err:
        sys.stderr.write(err + '\n')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
