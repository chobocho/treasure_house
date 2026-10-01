# -*- coding: utf-8 -*-
"""md_text.py — 공식 마크다운 문서를 인용할 수 있는 텍스트로 바꾼다.

    python3 tools/md_text.py 파일.md > 파일.txt

goevo 의 html_text.py 자리다(PLAN.md §1). C# 의 역사 문서는 거의 전부
마크다운이다 — dotnet/docs 의 whats-new, csharplang 의 버전 기록과 제안,
Roslyn 의 기능 상태·호환성 문서. 규칙은 셋뿐이다.

  · 제목(ATX '#…' 와 setext '===' · '---' 밑줄)은 '§<TAB>제목' 한 줄이
    된다. <!--CITE sec=…--> 는 이 줄과 글자까지 같아야 한다(deck/cites.py).
    제목 글자에서는 마크다운 표시(`코드`, [글](주소), *강조*, \\# 이스케이프,
    {#앵커}, HTML 태그)를 걷어 낸다 — "## The `field` keyword" 는
    "The field keyword" 로 인용한다.
  · 울타리 코드 블록(``` · ~~~) 안은 글자 그대로 둔다. 그 안의 '#' 줄
    (#nullable, #:sdk, 셸 주석)은 제목이 아니다.
  · 맨 앞의 YAML 머리말(--- … ---)은 그대로 둔다. 닫는 '---' 를 앞줄의
    setext 밑줄로 읽으면 'ms.custom: …' 가 제목이 된다.

나머지 줄은 손대지 않는다(끝 공백만 뗀다). 시간·공간 O(문서 길이).
"""
import re
import sys

ATX = re.compile(r'^ {0,3}(#{1,6})\s+(.*?)\s*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')
SETEXT = re.compile(r'^ {0,3}(=+|-+)\s*$')


def clean(s):
    """제목 글자에서 마크다운 표시를 걷어 낸다. O(글자 수)."""
    s = re.sub(r'\s+#+\s*$', '', s)                    # 닫는 '##'
    s = re.sub(r'\s*\{#[^}]*\}\s*$', '', s)            # {#앵커}
    s = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', s)   # [글](주소)
    s = re.sub(r'<[^>]+>', '', s)                      # HTML 태그
    s = s.replace('`', '')
    s = re.sub(r'(\*\*|__)(.+?)\1', r'\2', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'\1', s)
    s = re.sub(r'\\([\\`*_{}\[\]()#+\-.!<>|])', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def _front_matter_end(lines):
    """맨 앞이 '---' 이면 닫는 '---' 의 줄 번호, 아니면 -1."""
    if not lines or lines[0].strip() != '---':
        return -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            return i
    return -1


def convert(text):
    lines = text.lstrip('\ufeff').replace('\r\n', '\n').split('\n')
    out = []
    fm = _front_matter_end(lines)
    fence = None                       # 열린 울타리의 표시(``` 또는 ~~~)
    for i, line in enumerate(lines):
        line = line.rstrip()
        if i <= fm:
            out.append(line)
            continue
        m = FENCE.match(line)
        if fence:
            out.append(line)
            if m and m.group(1)[0] == fence[0] and \
                    len(m.group(1)) >= len(fence) and \
                    not line.strip()[len(m.group(1)):].strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            out.append(line)
            continue
        h = ATX.match(line)
        if h:
            out.append('§\t' + clean(h.group(2)))
            continue
        # setext 밑줄 — 앞줄이 보통 문단 글이어야 한다(빈 줄·목록·표·
        # 이미 제목인 줄·머리말 다음 줄은 아니다)
        if SETEXT.match(line) and out and i - 1 > fm:
            prev = out[-1]
            if prev.strip() and not prev.startswith('§\t') and \
                    not re.match(r'^\s*([-*+]|\d+[.)]|\|)', prev):
                out[-1] = '§\t' + clean(prev)
                continue
        out.append(line)
    return '\n'.join(out).rstrip('\n') + '\n'


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as f:
        sys.stdout.write(convert(f.read()))
