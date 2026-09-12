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
         '        main.py list')


def main(argv):
    if len(argv) == 1 and argv[0] == 'list':
        print('\n'.join(registry.ORDER))
        return 0
    if len(argv) != 4:
        sys.stderr.write(USAGE + '\n')
        return 2
    algo, mode, src_path, dst_path = argv
    if algo not in registry.MODULES:
        sys.stderr.write('모르는 알고리즘: %s\n' % algo)
        return 2
    if mode not in ('enc', 'dec'):
        sys.stderr.write('enc 또는 dec 이어야 한다: %s\n' % mode)
        return 2
    with open(src_path, 'rb') as f:
        data = f.read()
    try:
        out = (registry.encode(algo, data) if mode == 'enc'
               else registry.decode(algo, data))
    except ValueError as e:
        sys.stderr.write('%s %s 실패: %s\n' % (algo, mode, e))
        return 1
    with open(dst_path, 'wb') as f:
        f.write(out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
