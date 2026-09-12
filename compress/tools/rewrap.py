# -*- coding: utf-8 -*-
"""rewrap.py — 소스의 한국어 주석 문단을 폴더블 폭에 맞춰 다시 접는다.

덱에 실릴 코드는 <pre> 안에서 72칸을 넘으면 안 된다(tools/width.py 참고).
한국어 주석은 한 글자가 두 칸이라 눈으로는 짧아 보여도 쉽게 넘는다.
손으로 접으면 반드시 어딘가에서 한 글자씩 밀리므로 기계에 맡긴다.

**건드리는 것만 건드린다.** 다음 조건을 모두 만족하는 '순수 주석 문단' 만:
  · 줄 전체가 주석이다 (코드 뒤에 붙은 꼬리 주석은 손대지 않는다)
  · 같은 들여쓰기 · 같은 접두사(// 또는 #)가 이어진다
  · 문단 안에 구분선(──), 목록 기호, 예제 명령(탭·4칸 들여쓴 줄),
    표 모양(여러 칸 띄어쓰기)이 없다
그 외에는 손대지 않고 width.py 가 잡아 사람이 고치게 둔다.

    python3 tools/rewrap.py web/01_hello/main.go        # 제자리에서 고친다
    python3 tools/rewrap.py --dry web/**/*.go           # 바꿀 것만 보여 준다
"""
import io
import os
import re
import sys
import unicodedata

MAX = 72
TABSTOP = 4          # 덱 CSS 의 tab-size 와 같아야 한다

# 자바독(  * …)도 다룬다. 자바는 이 덱에서 주석이 가장 긴 언어인데,
# javadoc 은 한 줄이 ' * ' 로 시작해 //·# 규칙에 안 걸렸다.
_PREFIX = re.compile(r'^([ \t]*)(//|#|\*)( ?)(.*)$')
# 이 문단은 접지 않는다는 신호들
# 자바독 문단 첫 줄(<p>)과 태그(@param 따위)는 접지 않는다 — 접으면
# 문단 구분이 사라진다. 목록 기호로 쓰인 '*' 도 여전히 건너뛴다.
_KEEP = re.compile(r'──|^\s*[-·]\s|^\s*\d+[.)]\s|^\s{2,}\S|\t|  +\S'
                   r'|^@\w|^<pre>|^</pre>')


def cells(s):
    n = 0
    for ch in s:
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def wrap(words, prefix, limit):
    """어절 목록을 limit 칸 안으로 접는다.

    칸 수 기준이라 한글이 섞여도 맞다. 들여쓰기가 탭이면 반드시 펼쳐서
    재야 한다 — 탭 하나를 한 칸으로 세면 함수 안쪽 주석이 매번 세 칸씩
    모자라게 나온다.
    """
    lines, cur = [], ''
    for wd in words:
        cand = wd if not cur else cur + ' ' + wd
        if cells((prefix + cand).expandtabs(TABSTOP)) > limit and cur:
            lines.append(prefix + cur)
            cur = wd
        else:
            cur = cand
    if cur:
        lines.append(prefix + cur)
    return lines


def blocks(lines):
    """(시작, 끝, 접두사) — 이어진 순수 주석 줄 덩어리."""
    out, i, n = [], 0, len(lines)
    while i < n:
        m = _PREFIX.match(lines[i])
        if not m:
            i += 1
            continue
        indent, mark, _sp, body = m.groups()
        # ' */' 는 주석을 **닫는** 줄이다. 문단으로 보면 '/' 라는 낱말로
        # 빨려 들어가 닫는 표시가 사라진다 — 자바 파일 스물한 개를
        # 한꺼번에 깨뜨리고 나서 알았다.
        if mark == '*' and body.startswith('/'):
            i += 1
            continue
        pre = indent + mark + ' '
        j = i
        while j < n:
            mj = _PREFIX.match(lines[j])
            if not mj or mj.group(1) != indent or mj.group(2) != mark:
                break
            if mark == '*' and mj.group(4).startswith('/'):
                break
            j += 1
        out.append((i, j, pre))
        i = j
    return out


def paragraphs(chunk, bodies):
    """빈 주석 줄(//)을 경계로 문단을 나눈다.

    경계를 넘어 이어 붙이면 뜻이 뭉개진다 — 빈 줄은 글쓴이가 일부러 둔
    쉼표다. 그래서 덩어리 전체를 포기하는 대신 문단마다 따로 접는다.
    """
    out, start = [], 0
    for i, body in enumerate(bodies + ['']):
        if i == len(bodies) or not body.strip():
            if i > start:
                out.append((start, i))
            start = i + 1
    return out


def rewrap_text(text):
    lines = text.split('\n')
    changed = 0
    for a, b, pre in reversed(blocks(lines)):
        chunk = lines[a:b]
        bodies = [_PREFIX.match(l).group(4) for l in chunk]
        # 뒤에서부터 고쳐야 앞 문단의 줄 번호가 밀리지 않는다
        for ps, pe in reversed(paragraphs(chunk, bodies)):
            part = chunk[ps:pe]
            pb = bodies[ps:pe]
            if any(_KEEP.search(x) for x in pb):
                continue
            if all(cells(l.expandtabs(4)) <= MAX for l in part):
                continue
            words = ' '.join(x.strip() for x in pb).split()
            new = wrap(words, pre, MAX)
            if new != part:
                lines[a + ps:a + pe] = new
                changed += 1
    return '\n'.join(lines), changed


def main(argv):
    dry = '--dry' in argv
    paths = [p for p in argv if not p.startswith('--')]
    if not paths:
        sys.stderr.write(__doc__)
        return 2
    total = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        src = io.open(p, encoding='utf-8').read()
        new, n = rewrap_text(src)
        if n:
            total += n
            print('  %s — 문단 %d개 다시 접음' % (p, n))
            if not dry:
                io.open(p, 'w', encoding='utf-8', newline='\n').write(new)
    print('총 %d개 문단%s' % (total, ' (미적용)' if dry else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
