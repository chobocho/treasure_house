# -*- coding: utf-8 -*-
"""소스 파일을 슬라이드 크기 조각으로 자른다.

   '전문 게재'를 사람 손으로 하면 반드시 어딘가 빠진다. 그래서 자르는 일을
   기계에 맡기고, 커버리지 검사로 한 줄도 빠지지 않았음을 증명한다.

   자르는 자리는 아무 데나가 아니라 '최상위 정의가 시작되는 줄'이다.
   함수 한가운데서 끊긴 코드는 읽히지 않는다.
"""
import re

# 언어별 '여기서 새 덩어리가 시작된다'는 신호
BREAK = {
    'py': re.compile(r'^(def |class |@|#\s*-{4,}|[A-Z_]+ = |[A-Za-z_]+ = )'),
    'lua': re.compile(r'^(function |local function |local [A-Za-z_]+ = |-- )'),
    'ts': re.compile(r'^(export |function |class |interface |const |type |import |// )'),
}


def split(text, lang, maxlines=46, minlines=16):
    """(시작줄, 끝줄) 목록을 1-베이스 포함 범위로 돌려준다."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    n = len(lines)
    pat = BREAK.get(lang, BREAK['py'])

    # 자를 수 있는 자리: 최상위(들여쓰기 0) 정의가 시작하는 줄
    cuts = set()
    for i, ln in enumerate(lines):
        if ln and not ln[0].isspace() and pat.match(ln):
            cuts.add(i)
        elif ln.strip() == '' and i + 1 < n and lines[i + 1][:1] not in (' ', '\t', ''):
            cuts.add(i + 1)

    out = []
    start = 0
    while start < n:
        end = min(start + maxlines, n)
        if end < n:
            # maxlines 안쪽에서 가장 뒤에 있는 자를 자리를 찾는다
            best = -1
            for c in range(end, start + minlines, -1):
                if c in cuts:
                    best = c
                    break
            if best > 0:
                end = best
        out.append((start + 1, end))
        start = end
    return out


def label_for(lines, a, b, lang):
    """조각의 제목 — 그 구간에서 처음 나오는 최상위 이름."""
    pats = {
        'py': re.compile(r'^(?:def|class)\s+([A-Za-z_][\w]*)'),
        'lua': re.compile(r'^(?:local\s+)?function\s+([\w.:]+)|^local\s+([A-Za-z_][\w]*)\s*='),
        'ts': re.compile(r'^export\s+(?:function|class|const|interface|type)\s+([A-Za-z_][\w]*)'
                         r'|^(?:function|class|interface)\s+([A-Za-z_][\w]*)'),
    }
    pat = pats.get(lang, pats['py'])
    names = []
    for ln in lines[a - 1:b]:
        m = pat.match(ln)
        if m:
            names.append(next(g for g in m.groups() if g))
        if len(names) >= 2:
            break
    if not names:
        return '머리말' if a == 1 else '이어서'
    return ' · '.join(names)
