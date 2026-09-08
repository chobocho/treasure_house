#!/usr/bin/env python3
"""주소 하나를 사람이 읽게 펼친다.

    showurl.py 'http://…/auth?response_type=code&client_id=…'

물음표 앞뒤를 나누고, & 로 이어 붙은 칸을 한 줄에 하나씩 적는다.
값은 퍼센트 부호를 풀어 준다 — 실제로 오간 글자를 봐야 하기 때문이다.

주소는 한 줄로 200칸이 넘는 일이 흔한데, 그러면 좁은 화면에서 잘려
정작 봐야 할 칸이 안 보인다. 덱에 싣는 것은 이렇게 펼친 모습이다.
"""
import sys
import urllib.parse

# 토큰처럼 아주 긴 값은 가운데를 줄인다. 무엇이 실렸는지만 보면 된다.
MAXVAL = 56


def show(url):
    head, _, query = url.partition('?')
    print(head)
    if not query:
        return
    for n, part in enumerate(query.split('&')):
        key, _, raw = part.partition('=')
        val = urllib.parse.unquote_plus(raw)
        if len(val) > MAXVAL:
            val = '%s…(%d자 줄임)…%s' % (
                val[:20], len(val) - 40, val[-20:])
        print('  %s %-22s = %s' % ('?' if n == 0 else '&', key, val))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    show(sys.argv[1].strip())
