# -*- coding: utf-8 -*-
"""7부 뒤 조각 — 식 본문 멤버 · 자동 속성 · using static · 예외 필터 ·
인덱스 초기화자 · C# 6.0 정리의 증거. 예제는 ex/07/ 아래에 있다.

C# 6 의 게이트는 기능 하나에 예제 하나씩 C# 5 로 내려 거절을 받는다.
선언의 오류가 몸체의 검사를 가리기 때문이다(7부 1장). 이 묶음은 두 번
돌려 바이트까지 같은 것만 쓴다."""

import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 5장 — 식 본문 멤버
    'ebmethod', 'ebprop', 'ebindexer', 'ebops', 'ebvoid', 'ebnot6',
    'ebil', 'ebtrap', 'ebnew', 'ebvsfield', 'ebthrow', 'ebasync',
    'ebnullc', 'eblambda', 'ebref', 'ebiface',
    # 6장 — 자동 속성
    'autoinit', 'autoorder', 'autothis', 'roauto', 'roctor', 'rofield',
    'roreflect', 'structauto', 'structinit', 'immut', 'immutrec',
    'immutinit', 'autofield', 'autovirt', 'roreadonly', 'rochain',
    'autoattr', 'required',
    # 7장 — using static 과 그 밖의 작은 기능
    'usstatic', 'usstring', 'usext', 'usenum', 'usconf', 'usglobal',
    'fltgate', 'fltorder', 'fltlog', 'fltthrow', 'fltmulti',
    'dictgate', 'dictlower', 'dictmix', 'extadd', 'overload', 'enumbase',
    'catchwhen', 'dictonce', 'usgeneric', 'fltstack', 'dictlist',
    'fltpattern', 'ushide',
    # 8장 — C# 6.0 정리
    'wrapc5', 'wrapc6', 'wrapdev',          # wrapbreak 은 BAD 로만
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
]

# C# 6 의 게이트 — C# 5 로 내리면 거절
GATE5 = [
    'ebmethod', 'ebprop', 'ebindexer', 'ebops',
    'autoinit', 'roauto',
    'usstatic', 'fltgate', 'dictgate',
]

# -define:<기호> 로 켜는 틀린 줄 — (예제, 기호, 종료 코드)
BAD = [
    ('ebprop', 'BAD', 1), ('ebvoid', 'BAD', 1), ('ebvoid', 'BAD2', 1),
    ('ebasync', 'BAD', 1),
    ('autothis', 'BAD', 1), ('roctor', 'BAD', 1), ('roctor', 'BAD2', 1),
    ('immutinit', 'BAD', 1),
    ('usstring', 'BAD', 1), ('usext', 'BAD', 1), ('usconf', 'BAD', 1),
    ('fltmulti', 'BAD', 1), ('dictmix', 'BAD', 1),
    ('roreadonly', 'BAD', 1), ('required', 'BAD', 1), ('usenum', 'BAD', 1),
    ('ushide', 'BAD', 1),
    ('wrapdev', 'BAD', 1),
    ('wrapbreak', 'BAD', 0),    # 경고 CS0472 만 — lock (t) 는 거절되지 않는다
    ('wrapbreak', 'BAD2', 1),
]

# 뒤 버전의 기능 — 한 단계 아래로 내리면 거절 (예제, 버전)
LATER = [
    ('ebnot6', '6'), ('ebthrow', '6'),
    ('structinit', '9.0'), ('structinit', '6'), ('immutinit', '8.0'),
    ('autofield', '13.0'), ('usglobal', '9.0'),
    ('ebref', '6'), ('ebiface', '7.3'), ('roreadonly', '7.1'),
    ('required', '10.0'), ('wrapc6', '5'), ('fltpattern', '6'),
]


class Retry(object):
    """ctx 를 감싸 csrun 의 60초 시간 초과만 두 번까지 다시 돌린다
    (p05 의 것과 같다 — 스왑이 찬 날에는 csc 하나가 60초를 넘기기도
    한다). 출력이 다른 것은 다시 돌리지 않는다."""

    def __init__(self, ctx):
        self.ctx = ctx

    def cs(self, *args, **kw):
        for attempt in range(3):
            try:
                return self.ctx.cs(*args, **kw)
            except subprocess.TimeoutExpired:
                if attempt == 2:
                    raise


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/07/' + d)
    for d in FAIL:
        ctx.cs('ex/07/' + d, expect=1)
    for d in GATE5:
        ctx.cs('ex/07/' + d, v='5', expect=1)
    for d, sym, code in BAD:
        ctx.cs('ex/07/' + d, flags='-define:' + sym, tag=sym.lower(),
               expect=code)
    for d, v in LATER:
        ctx.cs('ex/07/' + d, v=v, expect=1)

    # 5장 — 디버그 빌드와 최적화 빌드의 IL
    ctx.cs('ex/07/ebil', flags='-optimize+', tag='opt')

    # 6장 — 구조체 생성자의 완화는 게이트가 없다: C# 5·3 으로 내려도 돈다
    ctx.cs('ex/07/structauto', v='5')
    ctx.cs('ex/07/structauto', v='3')

    # 7장 — 게이트가 없는 C# 6 의 변화: 내려도 같은 출력(꼴 (나) 불가)
    ctx.cs('ex/07/extadd', v='3')      # 확장 Add — 확장 메서드 자체가 C# 3
    ctx.cs('ex/07/overload', v='5')    # 메서드 그룹의 오버로드 해석
    ctx.cs('ex/07/enumbase', v='5')    # System.Byte 기반 형식 · 빈 params 배열

    # 6장 — 숨은 필드의 특성은 7.2 에서 거절이 아니라 경고(그래도 붙는다)
    ctx.cs('ex/07/autoattr', v='7.2')
