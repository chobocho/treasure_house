# -*- coding: utf-8 -*-
"""4부 앞 조각 — C# 3.0 의 아홉 조각 가운데 var·익명 형식·초기화자·자동 속성·
partial 메서드·람다·확장 메서드의 증거. (쿼리 식·식 트리는 p04b)"""

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 2장 — var 와 익명 형식
    'varstatic', 'varrules', 'varclass', 'varfield',
    'anonreadonly', 'anonnull', 'implarrayfail',
    # 3장 — 초기화자·자동 속성·partial 메서드
    'objinitdup', 'objinitstruct', 'collinitienum',
    'partialrules', 'partialdelegate',
    # 4장 — 람다
    'lambdaarity', 'lambdaambig', 'lambdareturn', 'lambdadeltypes',
    'lambdarecfail', 'lambdastaticfail',
    # 5장 — 확장 메서드
    'extattr', 'extrules', 'extambig', 'extconv', 'extprivate',
    'extdelegatefail',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장
    'eight', 'average', 'funcasm',
    # 2장
    'vargate', 'varlocals', 'varliteral', 'varident', 'varforeach', 'varneed',
    'varnew',
    'anongate', 'anonprops', 'anonequals', 'anonsame', 'anonprojection',
    'anoncast', 'anonarray', 'anonwith',
    'implarraygate', 'implarraybest',
    # 3장
    'objinitgate', 'objinitorder', 'objinitatomic', 'objinitself',
    'objinitctor', 'objinitnested',
    'collinitgate', 'collinitadd', 'collinitdict', 'collinitext',
    'collinitnested', 'dictinit',
    'autopropgate', 'autopropfield', 'autoprop6', 'autopropstruct',
    'autoprop14', 'partialargs', 'partial9',
    # 4장
    'lambdagate', 'lambdaforms', 'lambdavsanon', 'lambdainfer',
    'lambdanatural', 'lambdaclosure', 'lambdaloop', 'lambdaoverload',
    'lambdaintdiv', 'lambdacache', 'lambdathis', 'lambdaevent', 'lambdarec',
    'lambdacompose', 'lamteaser', 'lambdashadow', 'lambdastatic', 'lambdamod',
    # 5장
    'extgate', 'extstatic', 'extinstance', 'extusing', 'extnear',
    'extiface', 'extgeneric', 'extnull', 'extchain', 'extenum', 'extvalue',
    'extref', 'extdelegate', 'extdim', 'extgetenum', 'extmember',
]


def run(ctx):
    for d in RUN:
        ctx.cs('ex/04/' + d)
    for d in FAIL:
        ctx.cs('ex/04/' + d, expect=1)
    # dynamic 수신자의 확장 호출 — 컴파일은 되고 런타임 바인더가 멈춘다
    ctx.cs('ex/04/extdynamic', expect=ABORT)

    # 언어 버전 짝 (가) — C# 2 로 내리면 컴파일러가 거절한다
    ctx.cs('ex/04/eight', v='2', expect=1)          # 여덟 게이트가 한꺼번에
    ctx.cs('ex/04/vargate', v='2', expect=1)        # implicitly typed local variable
    ctx.cs('ex/04/anongate', v='2', expect=1)       # anonymous types
    ctx.cs('ex/04/implarraygate', v='2', expect=1)  # implicitly typed array
    ctx.cs('ex/04/objinitgate', v='2', expect=1)    # object initializer
    ctx.cs('ex/04/collinitgate', v='2', expect=1)   # collection initializer
    ctx.cs('ex/04/autopropgate', v='2', expect=1)   # auto-implemented properties
    ctx.cs('ex/04/partialargs', v='2', expect=1)    # partial method
    ctx.cs('ex/04/lambdagate', v='2', expect=1)     # lambda expression
    ctx.cs('ex/04/extgate', v='2', expect=1)        # extension method

    # 부르는 쪽에는 게이트가 없다 — list.Average() 는 C# 2 로도 컴파일된다
    ctx.cs('ex/04/average', v='2')

    # 구현이 있을 때의 partial 메서드 — 인자가 평가된다
    ctx.cs('ex/04/partialargs', flags='-define:IMPL', tag='impl')
    # using 을 빼면 Tools 의 Shout 는 후보에서 빠지고 전역의 Fallback 이 불린다
    ctx.cs('ex/04/extusing', flags='-define:NOUSING', tag='nousing')

    # 지금의 진단 — C# 14 로 올려도 var 규칙은 그대로(일부는 자연 형식으로 바뀜)
    ctx.cs('ex/04/varrules', v='14.0', expect=1)
    # 버전에 묶인 동작 (나) — 람다 대리자 캐시는 언어 버전과 무관한가
    ctx.cs('ex/04/lambdacache', v='14.0')

    # 뒤 버전과의 맞물림 — 한 단계 아래로 내리면 거절
    ctx.cs('ex/04/varnew', v='8.0', expect=1)       # target-typed new (C# 9)
    ctx.cs('ex/04/anonwith', v='9.0', expect=1)     # with on anonymous types (C# 10)
    ctx.cs('ex/04/dictinit', v='5', expect=1)       # dictionary initializer (C# 6)
    ctx.cs('ex/04/autoprop6', v='3', expect=1)      # auto-property initializer (C# 6)
    ctx.cs('ex/04/autopropstruct', v='3', expect=1)  # struct auto-default (C# 11)
    ctx.cs('ex/04/autoprop14', v='13.0', expect=1)  # field keyword (C# 14)
    ctx.cs('ex/04/partial9', v='8.0', expect=1)     # extended partial methods (C# 9)
    ctx.cs('ex/04/lambdanatural', v='9.0', expect=1)  # lambda natural type (C# 10)
    ctx.cs('ex/04/lambdashadow', v='7.3', expect=1)   # name shadowing (C# 8)
    ctx.cs('ex/04/lambdastatic', v='8.0', expect=1)   # static lambda (C# 9)
    ctx.cs('ex/04/lambdamod', v='13.0', expect=1)     # simple lambda modifiers (C# 14)
    ctx.cs('ex/04/extref', v='7.1', expect=1)       # ref extension methods (C# 7.2)
    ctx.cs('ex/04/extdim', v='7.3', expect=1)       # default interface methods (C# 8)
    ctx.cs('ex/04/extgetenum', v='8.0', expect=1)   # extension GetEnumerator (C# 9)
    ctx.cs('ex/04/extmember', v='13.0', expect=1)   # extension blocks (C# 14)
