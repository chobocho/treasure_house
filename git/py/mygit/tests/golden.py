# -*- coding: utf-8 -*-
"""시험 도우미 — golden/ 을 읽고 재료를 바이트로 만든다.

golden/ 은 진짜 git 이 만든 기준 바이트다(SPEC.md §16.2). 시험은 git 을
부르지 않고 이 파일들만 읽는다. 재료 문법은 SPEC.md §2.1·§16.4 이고,
tools/make_golden.py 의 make() 와 같은 규칙이다.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GIT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GOLDEN = os.path.join(GIT, 'golden')


def path(*parts):
    return os.path.join(GOLDEN, *parts)


def read(*parts):
    with open(path(*parts), 'rb') as f:
        return f.read()


def tsv(*parts):
    """주석(#)과 머리 줄을 뺀 행들. 각 행은 칸 이름 → 값."""
    rows, head = [], None
    for line in read(*parts).decode('utf-8').split('\n'):
        if not line or line.startswith('#'):
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
        else:
            rows.append(dict(zip(head, cols)))
    return rows


def unescape(s):
    """text: 재료의 이스케이프 — \\n \\t \\\\ \\" \\xHH."""
    out, i, raw = bytearray(), 0, s.encode('utf-8')
    while i < len(raw):
        c = raw[i:i + 1]
        if c == b'\\' and i + 1 < len(raw):
            n = raw[i + 1:i + 2]
            if n == b'x':
                out.append(int(raw[i + 2:i + 4], 16))
                i += 4
                continue
            out += {b'n': b'\n', b't': b'\t'}.get(n, n)
            i += 2
            continue
        out += c
        i += 1
    return bytes(out)


def make(recipe):
    """재료 한 줄 → 바이트 (SPEC.md §2.1). O(결과 길이)."""
    kind, _, arg = recipe.partition(':')
    if kind == 'empty':
        return b''
    if kind == 'text':
        return unescape(arg)
    if kind == 'repeat':
        byte, n = arg.split(':')
        return bytes([int(byte, 16)]) * int(n)
    if kind == 'counter':
        return bytes(i % 251 for i in range(int(arg)))
    if kind == 'seq':
        a, b = (int(x) for x in arg.split(':'))
        return b''.join(b'%d\n' % i for i in range(a, b + 1))
    if kind == 'golden':
        return read(arg)
    raise ValueError('모르는 재료: %s' % recipe)


def assert_git_error(case, fn, *args):
    """fn(*args) 가 **진짜** GitError 를 던지는가.

    껍데기(not_implemented)도 GitError 를 던지므로 그냥 assertRaises 로
    보면 구현 전에 이미 통과한다 — 거짓 초록이다. 코드 99 는 "아직 안
    짰다" 라서 여기서 떨어뜨린다. 던져진 오류를 돌려준다.
    """
    from mygit import GitError
    with case.assertRaises(GitError) as cm:
        fn(*args)
    case.assertNotEqual(cm.exception.code, 99, 'not implemented')
    return cm.exception
