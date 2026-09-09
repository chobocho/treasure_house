#!/usr/bin/env python3
"""인용 범위(lines=A-B)가 소스의 경계와 맞는지 검사한다.

    python3 deck/check_slices.py            # 조각 전부
    python3 deck/check_slices.py 03_ad.html # 하나만

왜 필요한가: 조립기는 "그 줄이 파일에 있는가"(커버리지·역검증)만 본다.
소스를 고쳐 줄이 밀리면 lines=A-B 는 그대로인데 내용이 밀린다 —
함수의 머리 주석이 앞 장에 붙고, 다음 장은 `}` 로 시작한다.
2차 리뷰에서 그런 자리가 40곳 넘게 나왔다(대부분 rewrap 뒤의 밀림).
사람 눈으로는 못 잡는 종류라 규칙으로 옮겼다.

규칙(전부 오류):
  E1  끝 줄이 파일 길이를 넘는다 — 빈 인용이 화면에 실린다
  E2  시작 줄이 `}` 하나뿐이다 — 앞 함수의 꼬리
  E3  시작 줄이 주석인데 그 앞 줄도 주석이다 — 주석 블록 중간에서 시작
  E4  끝 줄이 주석인데 다음 줄이 주석·선언이다 — 머리 주석이 잘린 채 끝남
  E5  시작 줄이 빈 줄이다
  E6  앞 줄이 `\\` 로 끝난다 / 끝 줄이 `\\` 로 끝난다 — 쉘 명령이 반으로
  E7  시작 줄이 `)`·`]`·`}` 로만 된 닫힘이다 (파이썬·YAML·JSON)
  E8  시작 줄이 들여쓰기돼 있는데 앞 줄이 빈 줄이 아니다 — 블록 한가운데
  E9  끝 줄이 `{` 로 끝난다 — 블록을 연 채 끝남
      (JSON 은 E8 대신 "앞 줄이 : 로 끝남" 을 본다. 같은 파일을 A-1 에서
      끝난 인용에 바로 이어 붙이면 E8 은 봐준다 — 앞머리/뒷부분 나누기)

의도한 이어 붙이기("앞머리/뒷부분")는 빈 줄이나 문장 경계에서 자르면
규칙에 걸리지 않는다. 캡처(OUT)는 E1 만 본다 — 출력에는 경계가 없다.
O(줄 수) 시간, 파일마다 한 번 읽는다.
"""
import os
import re
import sys

DECK = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DECK)
SECTIONS = os.path.join(DECK, 'sections')

DIRECTIVE = re.compile(r'<!--(CODE|OUT)\s+file=(\S+)(?:\s+lines=(\d+)-(\d+))?')
COMMENT = {'.go': '//', '.sh': '#', '.py': '#', '.yaml': '#', '.yml': '#',
           '.ldif': '#', 'Makefile': '#'}
DECL = re.compile(r'^(func|type|const|var|def|class|[A-Za-z_][\w-]*\s*:)\b')

_cache = {}


def read_lines(path):
    if path not in _cache:
        with open(path, encoding='utf-8') as f:
            _cache[path] = f.read().split('\n')
    return _cache[path]


def check(kind, rel, a, b, where, chained=False):
    path = os.path.join(BASE, 'out' if kind == 'OUT' else '', rel)
    if not os.path.exists(path):
        return ['%s: 파일이 없다 %s' % (where, rel)]
    lines = read_lines(path)
    n = len(lines) - (1 if lines and lines[-1] == '' else 0)
    errs = []
    if b > n:
        errs.append('%s: E1 %s lines=%d-%d — 파일은 %d줄뿐이다' % (where, rel, a, b, n))
        return errs
    if kind == 'OUT':
        return errs
    ext = os.path.splitext(rel)[1] or os.path.basename(rel)
    cm = COMMENT.get(ext)
    first, last = lines[a - 1], lines[b - 1]
    prev = lines[a - 2] if a >= 2 else ''
    nxt = lines[b] if b < n else ''

    def is_comment(s):
        return cm is not None and s.strip().startswith(cm)

    tag = '%s: %s lines=%d-%d' % (where, rel, a, b)
    if first.strip() == '}':
        errs.append(tag + ' — E2 `}` 로 시작한다 (앞 함수의 꼬리)')
    elif first.strip() in (')', ']', '},', '],', ')', '}'):
        errs.append(tag + ' — E7 닫힘 괄호로 시작한다')
    elif not first.strip():
        errs.append(tag + ' — E5 빈 줄로 시작한다')
    elif is_comment(first) and is_comment(prev):
        errs.append(tag + ' — E3 주석 블록 중간에서 시작한다 (%d행부터가 한 덩어리)' % (a - 1))
    elif ext == '.json':
        if prev.rstrip().endswith(':'):
            errs.append(tag + ' — E8 키와 값 사이에서 시작한다 (%d행이 앞 줄)' % (a - 1))
    elif (first[:1] in ('\t', ' ') and prev.strip() and ext != '.yaml'
          and not chained and not is_comment(first)):
        # 주석 줄에서 시작하는 발췌는 일부러 자른 자리다 — 봐준다
        errs.append(tag + ' — E8 블록 한가운데서 시작한다 (%d행이 앞 줄)' % (a - 1))
    if last.rstrip().endswith('{'):
        errs.append(tag + ' — E9 블록을 연 채 끝난다')
    if is_comment(last) and (is_comment(nxt) or DECL.match(nxt.strip())):
        errs.append(tag + ' — E4 머리 주석이 잘린 채 끝난다 (%d행이 그 선언)' % (b + 1))
    if ext == '.sh':
        if prev.rstrip().endswith('\\'):
            errs.append(tag + ' — E6 앞 줄이 \\ 로 이어지는 명령 중간에서 시작한다')
        if last.rstrip().endswith('\\'):
            errs.append(tag + ' — E6 \\ 로 이어지는 명령 중간에서 끝난다')
    return errs


def main():
    names = sys.argv[1:] or sorted(os.listdir(SECTIONS))
    errs, total = [], 0
    for name in names:
        if not name.endswith('.html'):
            continue
        p = os.path.join(SECTIONS, name)
        ends = {}  # 파일 → 이 조각에서 인용한 끝 줄들 (이어 붙이기 판정)
        for i, line in enumerate(read_lines(p), 1):
            m = DIRECTIVE.search(line)
            if not m or not m.group(3):
                continue
            total += 1
            a = int(m.group(3))
            # "앞머리 / 뒷부분" 처럼 같은 파일을 바로 이어 인용하면 블록
            # 한가운데서 시작해도 된다 — 읽는 사람에게는 한 덩어리다.
            chained = (a - 1) in ends.setdefault(m.group(2), set())
            errs += check(m.group(1), m.group(2), a, int(m.group(4)),
                          '%s:%d' % (name, i), chained)
            ends[m.group(2)].add(int(m.group(4)))
    for e in errs:
        print('  ✗ ' + e)
    print('인용 범위 %d개 — 어긋남 %d건' % (total, len(errs)))
    sys.exit(1 if errs else 0)


if __name__ == '__main__':
    main()
