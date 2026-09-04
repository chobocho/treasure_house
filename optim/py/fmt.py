# -*- coding: utf-8 -*-
"""데모 출력용 표 도우미.

   덱에 실리는 실행 출력은 고정폭 글꼴로 보인다. 한글은 두 칸을 차지하므로
   len() 으로 자리를 맞추면 한글이 섞인 표가 어긋난다. 여기서 한 번만 제대로
   맞춰 두고 모든 데모가 이것을 쓴다.
"""
import unicodedata


def wlen(s):
    """터미널 표시 폭.

       · East Asian Wide/Fullwidth(한글·한자·전각) 는 두 칸.
       · 결합 문자(x̂ 의 ̂ 처럼 앞 글자에 얹히는 것)는 0 칸 — 이걸 1 로 세면
         수식 기호가 들어간 머리글의 표가 한 칸씩 밀린다.
    """
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w


def pad(s, w):
    """왼쪽 정렬. 넘치면 자르지 않는다 — 숫자를 잘라 거짓말하는 것보다 어긋나는 게 낫다."""
    return s + ' ' * max(0, w - wlen(s))


def rpad(s, w):
    return ' ' * max(0, w - wlen(s)) + s


def table(rows, align=None, sep='  ', rule='-'):
    """첫 행을 머리로 보고 구분선을 넣은 표를 만든다.

       align: 열마다 'l'(왼쪽) 또는 'r'(오른쪽). 없으면 전부 왼쪽.

       구분선을 ASCII 하이픈으로 긋는 이유: U+2500(─) 같은 괘선 문자는 유니코드
       동아시아 폭이 '모호(Ambiguous)'라서, 한글 글꼴로 대체 렌더링되면 두 칸을
       차지해 표가 통째로 어긋난다. 폴드7에서 실제로 겪는 문제다.
    """
    if not rows:
        return ''
    ncol = max(len(r) for r in rows)
    rows = [list(r) + [''] * (ncol - len(r)) for r in rows]
    align = (align or 'l' * ncol).ljust(ncol, 'l')
    w = [max(wlen(r[j]) for r in rows) for j in range(ncol)]
    out = []
    for i, r in enumerate(rows):
        cells = [(rpad if align[j] == 'r' else pad)(r[j], w[j]) for j in range(ncol)]
        out.append(sep.join(cells).rstrip())
        if i == 0:
            out.append(sep.join(rule * w[j] for j in range(ncol)))
    width = max(wlen(x) for x in out)
    return '\n'.join(pad(x, width) for x in out)


def num(v, d=6):
    """보기 좋은 수 — 아주 크거나 작으면 지수, 아니면 소수."""
    if v != v:
        return 'nan'
    a = abs(v)
    if a != 0 and (a < 1e-4 or a >= 1e6):
        return '%.*e' % (d - 3, v)
    return '%.*f' % (d, v)
