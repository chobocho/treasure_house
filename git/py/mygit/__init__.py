# -*- coding: utf-8 -*-
"""mygit — 만들면서 배우는 Git 의 Python 구현 (git/SPEC.md).

다섯 언어 가운데 이야기의 앞장을 선다(PLAN.md §0.10). 표준 라이브러리만
쓰고, SHA-1 은 손으로 짠다(SPEC.md §2). 모든 모듈은 SPEC 의 절을
따르고, 시험은 진짜 git 이 만든 golden/ 과 견준다.

STEP 은 지금까지 만든 부록 A 의 단계다. 장면 시험(tests/test_scenes.py)
은 자기 단계가 오기 전에는 "N단계에서 켜진다" 는 이유로 건너뛴다 —
12단계를 마치면 건너뛰는 시험이 하나도 없어야 한다.
"""

STEP = 12


class GitError(Exception):
    """SPEC.md §15 — 모든 모듈이 던지는 오류 한 가지.

    메시지(표준 오류에 쓸 첫 줄들)와 종료 코드를 함께 갖는다. 출력은
    cli 만 한다 — 다른 모듈은 이것을 던질 뿐이다.
    """

    def __init__(self, message, code=128):
        Exception.__init__(self, message)
        self.message = message
        self.code = code


def not_implemented():
    """아직 없는 함수의 껍데기. 시험이 "모듈이 없다" 가 아니라
    "아직 안 짰다" 로 실패하게 한다(SPEC.md §16.3)."""
    raise GitError('not implemented', 99)
