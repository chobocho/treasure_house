# -*- coding: utf-8 -*-
"""testcap_run.py — testcap.py 가 하위 프로세스에서 부르는 시험 실행기.

시험 이름을 정한 차례(이름 순)로 돌리고, 시험마다 한 줄씩 찍는다:

    ok    test_quat.Product.test_identity
    FAIL  test_quat.Product.test_norm  AssertionError: 0.9 != 1.0
    ERROR test_quat.Product.test_inv   NotImplementedError: 구현 전

끝에 '시험 N개 · 통과 P · 실패 F · 오류 E' 한 줄. 시간은 찍지 않는다.
실패 메시지는 첫 줄만, 108칸에서 자른다(캡처 폭 규칙, PLAN.md §0.9).
"""
import unittest

WIDTH = 108


def _walk(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from _walk(t)
        else:
            yield t


def main(modname):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(modname)
    tests = sorted(_walk(suite), key=lambda t: t.id())
    n = ok = fail = err = 0
    lines = []
    for t in tests:
        res = unittest.TestResult()
        t.run(res)
        n += 1
        name = t.id().split('.', 1)[1]
        if res.failures:
            fail += 1
            row = 'FAIL  %s  %s' % (name, _exc(res.failures[0][1]))
        elif res.errors:
            err += 1
            row = 'ERROR %s  %s' % (name, _exc(res.errors[0][1]))
        elif res.skipped:
            row = 'skip  %s' % name
            ok += 1
        else:
            ok += 1
            row = 'ok    %s' % name
        lines.append(row[:WIDTH])
    print('\n'.join(lines))
    print('시험 %d개 · 통과 %d · 실패 %d · 오류 %d'
          % (n, ok, fail, err))
    return 1 if (fail or err) else 0


def _exc(text):
    """TestResult 가 남긴 트레이스백 글에서 예외 줄(의 첫 줄)만.

    마지막 '  File …' 줄 뒤의 들여쓴 코드 줄을 건너뛴 첫 줄이 예외다.
    assertEqual 의 여러 줄 메시지는 그 첫 줄만 남는다."""
    rows = text.rstrip().split('\n')
    last = max((i for i, r in enumerate(rows)
                if r.startswith('  File ')), default=-1)
    for r in rows[last + 1:]:
        if r and not r.startswith(' '):
            return r.strip()
    return rows[-1].strip() if rows else ''
