# -*- coding: utf-8 -*-
"""작업 트리 (SPEC.md §8). 지금은 경로 따옴표만 — 6단계에서 자란다."""

# \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
_SHORT = {7: 'a', 8: 'b', 9: 't', 10: 'n', 11: 'v', 12: 'f', 13: 'r',
          34: '"', 92: '\\'}


def quote_path(path, space=False):
    """경로 바이트 → git 이 사람에게 찍는 꼴 (core.quotePath=true).

    제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
    전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space=True 는
    status 의 규칙 — 공백만 있어도 감싼다(공백 자체는 그대로).
    한글은 UTF-8 여섯 바이트가 \\355\\225… 로 찍힌다. O(경로 길이).
    """
    need = space and 32 in path
    body = []
    for b in path:
        if b in _SHORT:
            body.append('\\' + _SHORT[b])
            need = True
        elif b < 32 or b >= 127:
            body.append('\\%03o' % b)
            need = True
        else:
            body.append(chr(b))
    s = ''.join(body)
    return '"%s"' % s if need else s
