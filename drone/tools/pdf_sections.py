# -*- coding: utf-8 -*-
"""pdf_sections.py — pdftotext 의 출력에서 절 제목을 찾아 '§' 줄로.

    python3 tools/pdf_sections.py 글.txt > 글.sec.txt
    python3 tools/pdf_sections.py --columns 글.txt    # 1 또는 2

tools/pdf_text.sh 가 부른다(PLAN.md §3.1). PDF 에는 제목 표시가
없으므로 모양으로 짐작한다. 논문·보고서에 흔한 셋만 본다.

  · 번호 제목   '3.4  Magnetic distortion compensation'
                → '§<TAB>3.4 Magnetic distortion compensation'
  · 로마 숫자   'II. QUADROTOR DYNAMICS MODEL', 대문자 한 줄
                'REFERENCES', 알파벳 부록 'A. Properties of the Hat Map'
  · 이름난 단어 'Abstract', 'Contents', 'References' …

오탐을 막는 규칙(한 번씩 실제로 걸렸던 것):
  · 목차 줄('3.1 … . . . .  6')과 쪽 번호로 끝나는 줄은 제목이 아니다.
  · 번호 뒤 글이 여덟 낱말을 넘거나 쉼표가 있거나 마침표로 끝나면
    문장이다('1. This is a system of four identical rotors and
    propellers'). 'vs.' 같은 가운데 마침표는 된다.
  · 세 글자 낱말이 없으면 식의 부스러기다('1 T T', '2 Ω d').
  · 첫 번호가 20 을 넘으면 그림의 눈금이다('50   Kalman').
  · 작은 대문자는 pdftotext 가 'R EFERENCES' 로 뗀다 — 붙인다.
  · 대문자 제목이 두 줄로 꺾이면 이어 붙인다.
  · 같은 대문자 줄이 세 번 넘게 나오면 쪽 머리글이다.

두 단 논문은 -layout 로 뽑으면 두 단이 한 줄에 섞인다. --columns 가
'가운데에 세 칸 넘는 빈칸이 있는 줄' 이 40 % 를 넘으면 2 를 내고,
pdf_text.sh 는 그때 읽기 차례(-layout 없이)로 다시 뽑는다.
시간 O(줄 수).
"""
import re
import sys

NAMED = {'abstract', 'contents', 'references', 'acknowledgements',
         'acknowledgments', 'appendix', 'bibliography', 'conclusion',
         'conclusions', 'introduction'}
NUM = re.compile(r'^(\d{1,2}(?:\.\d{1,2})*)\.?\s+(\S.*)$')
ROMAN = re.compile(r'^([IVX]{1,5}|[A-H])\.\s+(\S.*)$')
CAPS = re.compile(r'^[A-Z][A-Z0-9 ,:&()\-]*$')
TOC = re.compile(r'(\s\.){3}|\s{2,}\d+$')


def columns(text):
    """레이아웃 글이 두 단이면 2, 아니면 1."""
    ls = [l.strip() for l in text.split('\n') if l.strip()]
    if not ls:
        return 1
    wide = sum(1 for l in ls if re.search(r'\S {3,}\S', l))
    return 2 if wide > 0.4 * len(ls) else 1


def _smallcaps(s):
    # 'R EFERENCES' → 'REFERENCES', 'A PPENDIX' → 'APPENDIX'
    return re.sub(r'\b([A-Z]) (?=[A-Z]{2,}\b)', r'\1', s)


def _word(s):
    # 식의 부스러기('1 T T', '2 Ω d')를 거른다 — 세 글자 낱말이 있어야
    return re.search(r'[A-Za-z]{3}', s) is not None


def _caps(s):
    return (CAPS.match(s) is not None and len(s) <= 60 and _word(s)
            and not re.search(r'\s{3,}', s))


def _short_title(s):
    # 'vs.' 같은 줄임은 되고, 마침표로 끝나면 문장이다
    words = s.split()
    return (len(words) <= 8 and not re.search(r'[,;]|\.$', s)
            and not re.search(r'\s{3,}', s) and s[0].isupper()
            and _word(s))


def heading(line):
    """줄 하나 → (제목, 대문자인가) 또는 None."""
    s = line.strip()
    if not s or TOC.search(line.rstrip()):
        return None
    s = _smallcaps(s)
    if s.lower() in NAMED and (s[0].isupper()):
        return s, s.isupper()
    m = ROMAN.match(s)
    if m:
        num, title = m.group(1), m.group(2)
        letter = len(num) == 1 and num in 'ABCDEFGH'
        if _caps(title) or (letter and _short_title(title)):
            flat = re.sub(r'\s+', ' ', title)
            return '%s. %s' % (num, flat), _caps(title)
        return None
    m = NUM.match(s)
    if m:
        first = int(m.group(1).split('.')[0])
        title = re.sub(r'\s+', ' ', m.group(2))
        if first <= 20 and _short_title(m.group(2)):
            return '%s %s' % (m.group(1), title), False
        return None
    if _caps(s):
        return s, True
    return None


def sections(text):
    """pdftotext 출력 → 제목 줄을 '§<TAB>제목' 으로 바꾼 글."""
    text = text.replace('\f', '\n')
    src = text.split('\n')
    count = {}
    for l in src:
        h = heading(l)
        if h and h[1]:
            count[h[0]] = count.get(h[0], 0) + 1
    out, last_caps = [], False
    for l in src:
        h = heading(l)
        if h and h[1] and count.get(h[0], 0) > 3:
            h = None                       # 쪽 머리글
        if h is None:
            out.append(l.rstrip())
            if l.strip():
                last_caps = False
            continue
        title, caps = h
        roman = ROMAN.match(title) is not None
        if caps and last_caps and not roman and out:
            out[-1] += ' ' + title         # 두 줄로 꺾인 대문자 제목
            continue
        out.append('§\t' + title)
        last_caps = caps
    return '\n'.join(out).rstrip('\n') + '\n'


if __name__ == '__main__':
    args = sys.argv[1:]
    want_cols = '--columns' in args
    args = [a for a in args if a != '--columns']
    with open(args[0], encoding='utf-8', errors='replace') as f:
        src = f.read()
    if want_cols:
        print(columns(src))
    else:
        sys.stdout.write(sections(src))
