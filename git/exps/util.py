# -*- coding: utf-8 -*-
"""실험들이 같이 쓰는 도우미."""
import re


def tick(r, n):
    """작성·커밋 시각을 고정 시각 + n 분으로. 커밋 이름이 사건마다
    달라지고, log 의 차례가 날짜로 정해지게 한다."""
    r.env['GIT_AUTHOR_DATE'] = r.env['GIT_COMMITTER_DATE'] = \
        '%d +0900' % (1700000000 + 60 * n)


def commit(r, n, msg, files):
    """files = {경로: 내용} 을 쓰고 add·commit 한다(캡처 없이)."""
    tick(r, n)
    for path, text in files.items():
        r.write(path, text)
    r.sh('git add -A && git commit -q -m "%s"' % msg)


# ls-files --debug 의 stat 칸 가운데 이 기계에서만 뜻이 있는 것
_STAT = re.compile(r'(ctime|dev|ino|uid|gid): *\d+(:\d+)?')


def unstat(text):
    """ctime·dev·ino·uid·gid 를 <…> 로. 캡션에 적는 정규화."""
    return _STAT.sub(lambda m: '%s: <%s>' % (m.group(1), m.group(1)),
                     text)
