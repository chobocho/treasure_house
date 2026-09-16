# -*- coding: utf-8 -*-
"""데모가 캡처를 남기는 공통 틀.

   덱의 <!--OUT file=… sec=N--> 지시자가 절 하나를 통째로 잘라 싣는다.
   그래서 절 표지를 '== N. 제목 ==' 꼴로 못 박아 둔다 — 파일이 길어져도
   인용한 자리가 밀리지 않는다.
"""
import io
import os

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), 'out')


def write(name, sections):
    """sections 는 [(제목, 본문), …]. out/<name>.txt 로 적는다."""
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    parts = []
    for i, (title, body) in enumerate(sections, 1):
        parts.append('== %d. %s ==' % (i, title))
        parts.append(body.rstrip('\n'))
        parts.append('')
    text = '\n'.join(parts).rstrip('\n') + '\n'
    p = os.path.join(OUT, name)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(text)
    return p
