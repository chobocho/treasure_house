# -*- coding: utf-8 -*-
"""chunks.py — 소스 파일을 슬라이드 한 장에 들어갈 크기로 자르는 자리를 찾아 준다.

덱 작성용 보조 도구다(덱에는 실리지 않는다). 함수/블록 경계를 우선으로 삼고,
없으면 빈 줄에서 자른다. 출력은 그대로 <!--CODE lines=A-B--> 에 넣으면 된다.

    python3 deck/chunks.py net.cpp 38
"""
import io, os, re, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 자르기 좋은 자리 — 여기서 끊으면 슬라이드가 문장 중간에서 잘리지 않는다.
TOP = re.compile(r'^(?:[A-Za-z_#/].*|\}|\)|-{2,}|\s*$)')
HARD = re.compile(r'^(?:EXPORT\(|static |func |def |class |type |const |var |import |'
                  r'#include|// ──|# ──|async def |\.PHONY|[a-zA-Z_][\w./$()-]*:)')

def chunks(path, limit=38):
    lines = io.open(os.path.join(SRC, path), encoding='utf-8').read().split('\n')
    n = len(lines)
    if lines and lines[-1] == '':
        n -= 1
    out, start = [], 1
    while start <= n:
        end = min(start + limit - 1, n)
        if end < n:
            # 뒤에서부터 좋은 경계를 찾는다. 최소 절반은 채운다.
            best = None
            for i in range(end, start + limit // 2, -1):
                if HARD.match(lines[i]):        # 다음 줄이 새 블록의 시작
                    best = i
                    break
            if best is None:
                for i in range(end, start + limit // 2, -1):
                    if lines[i - 1].strip() == '':
                        best = i - 1
                        break
            if best:
                end = best
        out.append((start, end))
        start = end + 1
    return out, n

if __name__ == '__main__':
    files = sys.argv[1:2] or []
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 38
    for f in files:
        cs, n = chunks(f, limit)
        print('%s — 총 %d줄, %d조각' % (f, n, len(cs)))
        for a, b in cs:
            print('  <!--CODE file=%s lines=%d-%d cap="">  (%d줄)' % (f, a, b, b - a + 1))
