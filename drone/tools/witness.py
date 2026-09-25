# -*- coding: utf-8 -*-
"""witness.py — 정리 하나의 증인 시험만 돌려 결과를 찍는다.

    python3 tools/witness.py T14

data/theorems.tsv 의 witness-test 칸(py/tests/test_pid.py::이름)을
읽어 그 시험 하나만 돌린다. 덱의 <!--WITNESS id=T14--> 는 이 도구의
캡처(out/w_T14.txt)를 증명 장에 붙인다 — "이 식을 숫자로도 확인했다"
를 정리마다 따로 보이기 위해서다. 시간은 찍지 않는다.
"""
import importlib
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(BASE, 'deck'))
import cites  # noqa: E402


def find(tid):
    for r in cites.rows(BASE, 'theorems.tsv'):
        if r.get('id') == tid:
            return r
    return None


def load_case(path, name):
    """'py/tests/test_pid.py' 와 시험 이름 → TestCase 하나."""
    root = os.path.join(BASE, path.split('/')[0])     # py 또는 ex
    if root not in sys.path:
        sys.path.insert(0, root)
    # py/tests 와 ex/tests 가 둘 다 'tests' 라서 이름으로 import 하면
    # 먼저 불린 쪽이 남는다 — 파일 경로로 직접 싣는다.
    full = os.path.join(BASE, path)
    stem = 'w_' + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(stem, full)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for obj in vars(mod).values():
        if (isinstance(obj, type) and issubclass(obj, unittest.TestCase)
                and name in vars(obj)):
            return obj(name)
    raise LookupError('%s 에 %s 가 없다' % (path, name))


def main(argv):
    if len(argv) != 1:
        print('사용법: witness.py 정리id')
        return 2
    row = find(argv[0])
    w = (row or {}).get('witness-test', '')
    if not row or '::' not in w:
        print('정리 %s 에 증인 시험이 없다' % argv[0])
        return 2
    path, name = w.split('::', 1)
    case = load_case(path, name)
    res = unittest.TestResult()
    unittest.TestSuite([case]).run(res)
    ok = res.wasSuccessful()
    print('정리 %s · 증인 %s' % (row['id'], w))
    label = '%s.%s.%s' % (os.path.splitext(os.path.basename(path))[0],
                          type(case).__name__, name)
    print('%-5s %s' % ('ok' if ok else 'FAIL', label))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
