# -*- coding: utf-8 -*-
"""소스 파일을 슬라이드 한 장 크기의 조각으로 자른다.

   '전문 게재'를 사람 손으로 하면 반드시 어딘가 빠지거나 겹친다. 그래서 자르는
   일을 기계에 맡기고, 조립기의 커버리지 검사로 "한 줄도 빠지지 않았음" 을
   증명한다. 자르는 자리는 아무 데나가 아니라 '최상위 정의가 시작되는 줄' 이다 —
   함수 한가운데서 끊긴 코드는 읽히지 않는다.

   rts/deck/chunks.py 에서 물려받아 이 덱이 쓰는 언어(Go·YAML·JSON·shell·LDIF)를
   더했다. 시간·공간 모두 O(파일 줄 수).
"""
import re

# 언어별 '여기서 새 덩어리가 시작된다' 는 신호
BREAK = {
    'go': re.compile(r'^(package |import |func |type |var |const |// ─|//go:)'),
    'py': re.compile(r'^(def |class |@|#\s*-{4,}|[A-Z_]+ = |[A-Za-z_]+ = )'),
    'sh': re.compile(r'^([A-Za-z_][\w]*\(\)|[A-Za-z_][\w]*=|#\s|set -|echo |exec )'),
    'make': re.compile(r'^([A-Za-z_][\w.%-]*:|\.PHONY|#\s|[A-Z_]+\s*[:?+]?=)'),
    # YAML 은 문서 구분선과 최상위 키가 자연스러운 경계다
    'yaml': re.compile(r'^(---|[A-Za-z_][\w.-]*:|#\s)'),
    # JSON 은 들여쓰기 2칸의 키가 realm 파일에서 사실상 '절' 노릇을 한다
    'json': re.compile(r'^ {0,2}"[^"]+"\s*:'),
    # LDIF 는 빈 줄로 엔트리가 갈린다. dn: 이 곧 새 엔트리다.
    'ldif': re.compile(r'^(dn:|#\s)'),
}


def split(text, lang, maxlines=42, minlines=14):
    """(시작줄, 끝줄) 목록을 1-베이스 포함 범위로 돌려준다.

    maxlines 를 45가 아니라 42로 둔 것은 여유다 — 조립기의 오버플로 검사가
    한 <pre> 45줄에서 걸리는데, 라벨과 캡션이 같은 화면을 쓰기 때문이다.
    """
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    n = len(lines)
    pat = BREAK.get(lang, BREAK['py'])

    # 자를 수 있는 자리: 최상위(들여쓰기 0) 정의가 시작하는 줄,
    # 그리고 빈 줄 다음에 최상위 줄이 오는 자리.
    cuts = set()
    for i, ln in enumerate(lines):
        if ln and not ln[0].isspace() and pat.match(ln):
            cuts.add(i)
        elif ln.strip() == '' and i + 1 < n and lines[i + 1][:1] not in (' ', '\t', ''):
            cuts.add(i + 1)
    if lang in ('yaml', 'json', 'ldif'):
        # 들여쓴 최상위 키(JSON)·문서 구분(YAML)·빈 줄(LDIF)도 경계로 인정한다
        for i, ln in enumerate(lines):
            if pat.match(ln):
                cuts.add(i)

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
    """조각의 제목 — 그 구간에서 처음 나오는 최상위 이름 한두 개."""
    pats = {
        'go': re.compile(r'^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)'
                         r'|^type\s+([A-Za-z_]\w*)'
                         r'|^(?:var|const)\s+\(?\s*([A-Za-z_]\w*)?'),
        'py': re.compile(r'^(?:def|class)\s+([A-Za-z_]\w*)'),
        'sh': re.compile(r'^([A-Za-z_]\w*)\(\)'),
        'make': re.compile(r'^([A-Za-z_][\w.%-]*):'),
        'yaml': re.compile(r'^kind:\s*(\S+)|^([A-Za-z_][\w.-]*):'),
        'json': re.compile(r'^ {0,2}"([^"]+)"\s*:'),
        'ldif': re.compile(r'^dn:\s*(\S+)'),
    }
    pat = pats.get(lang, pats['py'])
    names = []
    for ln in lines[a - 1:b]:
        m = pat.match(ln)
        if m:
            g = next((x for x in m.groups() if x), None)
            if g:
                names.append(g)
        if len(names) >= 2:
            break
    if not names:
        return '머리말' if a == 1 else '이어서'
    return ' · '.join(names)
