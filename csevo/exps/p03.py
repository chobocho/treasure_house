# -*- coding: utf-8 -*-
"""3부 앞 조각 — C# 2.0 의 제네릭·nullable 값 형식·반복기의 증거."""

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['listbad', 'inferfail', 'noconstraint', 'constraintbad',
        'constraintorder', 'nullt', 'eqt', 'astrap', 'invfail',
        'sigconstraint', 'addt', 'intnull', 'nullconv', 'boolif',
        'nullasbad', 'nullnested', 'nullablet2', 'yieldtype', 'yieldcatch', 'yieldrules']

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관과 같이 온 런타임
    'allfour', 'runtime', 'runtimebcl',
    # 2장 — 제네릭
    'c1generic', 'listint', 'boxing', 'stack', 'arity', 'nested',
    'openclosed', 'inherit', 'genmethod', 'inferok', 'constraints',
    'constraintkinds', 'newt', 'defaultop', 'defaultt', 'eqfix', 'asfix',
    'defaultstruct', 'icomp', 'sortfail', 'multiiface', 'gendelegate', 'staticper', 'cache',
    'reified', 'collections', 'invariant', 'varuse', 'vardecl', 'overload',
    'shadowt',
    # 3장 — nullable 값 형식
    'magic', 'nullable', 'nullstruct', 'nulldefault', 'hasvalue',
    'coalesce', 'coalesce1', 'lifted', 'liftdesugar',
    'liftuser', 'liftcmp', 'boolq', 'nullsort', 'nullkey', 'nullbox', 'nullas', 'nullgettype',
    'nullablet', 'stringq',
    # 4장 — 반복기
    'handenum', 'yield', 'yieldbreak', 'yieldident', 'lazy', 'statemachine',
    'sameobj', 'current', 'iterexception', 'argcheck', 'argfix', 'finally',
    'iterusing', 'foreachcast', 'getenum', 'iterprop', 'multienum', 'itermutate', 'fib',
    'pipeline', 'recursive', 'itercs13',
]


def run(ctx):
    for d in RUN:
        ctx.cs('ex/03/' + d)
    for d in FAIL:
        ctx.cs('ex/03/' + d, expect=1)
    # 처리되지 않은 예외로 끝나는 C# 1 예제 — 이 기계에서 종료 코드는 -6(SIGABRT)
    ctx.cs('ex/03/arraylist', expect=-6)

    # 언어 버전 짝 (가) — C# 1 로 내리면 컴파일러가 거절한다
    ctx.cs('ex/03/allfour', v='1', expect=1)       # 구문 단계의 거절만 보인다
    ctx.cs('ex/03/allfour', v='ISO-2', tag='iso')  # 옛 이름 ISO-2 도 같은 뜻
    ctx.cs('ex/03/listint', v='1', expect=1)       # generics
    ctx.cs('ex/03/defaultop', v='1', expect=1)     # default operator
    ctx.cs('ex/03/nullable', v='1', expect=1)      # nullable types
    ctx.cs('ex/03/yield', v='1', expect=1)         # iterators

    # 게이트가 없는 것 — C# 1 로도 컴파일된다
    ctx.cs('ex/03/yieldident', v='14.0')           # yield 는 문맥 키워드

    # 뒤 버전과의 맞물림
    ctx.cs('ex/03/vardecl', v='2', expect=1)       # 변성 선언은 C# 4
    ctx.cs('ex/03/stringq', v='2', expect=1)       # string? 은 C# 8
    ctx.cs('ex/03/yieldcatch', v='14.0', expect=1) # 지금도 거절
    ctx.cs('ex/03/sigconstraint', v='14.0', expect=1)
    ctx.cs('ex/03/itercs13', v='12.0', expect=1)   # ref 지역 변수는 C# 13
