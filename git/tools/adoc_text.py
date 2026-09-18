# -*- coding: utf-8 -*-
"""adoc_text.py — git 의 .adoc 문서를 "§ 제목 줄 + 본문" 글로 바꾼다.

    python3 tools/adoc_text.py < x.adoc > x.txt

deck/check_claims.py 는 <!--CITE key=… sec=…--> 의 절 제목이 받아 둔
문서에 진짜 있는지를 `^§<TAB>제목$` 한 줄로 찾는다(SPEC 이 아니라
PLAN.md §1 의 약속). git 의 문서는 제목을 두 가지로 적는다 —
`== 제목`(아스키독 ATX 꼴)과, 제목 줄 바로 아래 같은 길이의
`====`·`----`·`~~~~`·`^^^^` 밑줄(setext 꼴). 둘 다 같은 꼴로 바꾸고
나머지 줄은 한 글자도 건드리지 않는다. O(줄 수).
"""
import re
import sys

ATX = re.compile(r'^(=+)\s+(.*?)\s*$')
UNDER = re.compile(r'^([=\-~^+])\1{2,}\s*$')


def convert(text):
    lines = text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        m = ATX.match(ln)
        if m:
            out.append('§\t' + m.group(2))
            i += 1
            continue
        # 밑줄 꼴: 제목 길이와 밑줄 길이가 같아야 한다(±1 은 봐준다 —
        # git 문서에 한 글자 어긋난 밑줄이 몇 군데 있다).
        if (ln.strip() and UNDER.match(nxt)
                and abs(len(nxt.rstrip()) - len(ln.rstrip())) <= 1):
            out.append('§\t' + ln.strip())
            i += 2
            continue
        out.append(ln)
        i += 1
    return '\n'.join(out)


if __name__ == '__main__':
    sys.stdout.write(convert(sys.stdin.read()))
