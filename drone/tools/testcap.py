# -*- coding: utf-8 -*-
"""testcap.py — 시험 한 모듈을 돌려 '시간 없는' 결과를 찍는다.

    python3 tools/testcap.py green quat     # 지금 구현으로
    python3 tools/testcap.py red quat       # 몸통을 비운 판으로

왜 따로 있나: unittest 는 끝에 "Ran 5 tests in 0.003s" 를 찍는다.
그 시간은 돌릴 때마다 달라서, 캡처를 세 번 떠 같은지 보는 규칙
(PLAN.md §0.10)을 통과할 수 없다. 여기서는 시험 이름과 결과, 실패의
첫 줄만 찍는다.

RED 는 어떻게 되살리나: 14부는 모듈마다 "시험을 먼저 쓰고 빨간불을
봤다" 를 캡처로 보인다. 그 빨간불을 한 번 찍고 버리면 다시 만들 수
없다. 그래서 대상 모듈의 소스를 ast 로 읽어 **함수·메서드의 몸통만
`raise NotImplementedError` 로 바꾼 판**을 scratch/red/ 에 만들고
그 위에서 시험을 돌린다. 이름과 서명은 그대로라 import 는 되고,
시험은 '구현이 없어서' 실패한다 — 컴파일 오류로 빨간 것이 아니다.
상수(모듈 수준 대입)는 그대로 둔다. O(소스 크기 + 시험 시간).
"""
import ast
import io
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PY = os.path.join(BASE, 'py')


def stub_source(src):
    """함수·메서드 몸통을 전부 NotImplementedError 로 바꾼 소스."""
    tree = ast.parse(src)

    class Gut(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            doc = ast.get_docstring(node)
            body = [ast.Expr(ast.Constant(doc))] if doc else []
            body.append(ast.parse(
                "raise NotImplementedError('구현 전')").body[0])
            node.body = body
            return node

    tree = Gut().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'


class _Result(unittest.TextTestResult):
    pass


def run(mode, module, stream):
    """mode 'red'|'green', module 'quat' → 실패 수. 출력은 stream 에."""
    root = PY
    if mode == 'red':
        root = os.path.join(BASE, 'scratch', 'red')
        if os.path.isdir(root):
            shutil.rmtree(root)
        shutil.copytree(PY, root, ignore=shutil.ignore_patterns(
            '__pycache__'))
        p = os.path.join(root, 'droneshow', module + '.py')
        with io.open(p, encoding='utf-8') as f:
            src = f.read()
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(stub_source(src))
    code = ('import sys, unittest\n'
            'sys.path.insert(0, %r)\n'
            'from testcap_run import main\n'
            'sys.exit(main(%r))\n' % (root, 'tests.test_' + module))
    env = dict(os.environ, PYTHONPATH=HERE, PYTHONHASHSEED='0',
               PYTHONDONTWRITEBYTECODE='1')
    r = subprocess.run([sys.executable, '-c', code], cwd=root, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stream.write(r.stdout.decode('utf-8'))
    return r.returncode


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('red', 'green'):
        sys.exit('사용법: testcap.py red|green 모듈')
    sys.exit(1 if run(sys.argv[1], sys.argv[2], sys.stdout) else 0)
