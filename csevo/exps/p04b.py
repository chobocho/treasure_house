# -*- coding: utf-8 -*-
"""4부 뒤 조각 — C# 3.0 의 쿼리 식·LINQ to Objects·식 트리·C# 3.0 정리의
증거."""

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 6장 — 쿼리 식
    'qescapefail', 'qnopattern', 'qrangescope', 'qnoselect', 'qjoinorder',
    'qjoineq', 'qjoinkeyfail', 'qassign',
    # 8장 — 식 트리가 될 수 없는 람다
    'etcannot', 'etlater', 'etoverload',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — 쿼리 식
    'qbefore', 'qgate', 'qkeywords', 'qescape', 'qdesugar', 'qpattern',
    'qtrace', 'qdegenerate', 'qinstwins', 'qmaybe', 'qorderby',
    'qorderbyfail', 'qlet', 'qletcount', 'qfromfrom', 'qselectnest',
    'qgroup', 'qgroupkey', 'qinto', 'qjoin', 'qjoinkey', 'qgroupjoin',
    'qcast', 'qmix', 'qcompose', 'qoutvar',
    # 7장 — LINQ to Objects 와 늦은 실행
    'lqmethods', 'lqmywhere', 'lqdeferred', 'lqimmediate', 'lqorderbuffer',
    'lqgroupbuffer', 'lqjoinbuffer', 'lqmulti', 'lqcapture',
    'lqsourcechange', 'lqforcapture', 'lqstable', 'lqdistinct', 'lqsetops',
    'lqaggregate', 'lqsum', 'lqempty', 'lqfirst', 'lqargnull', 'lqmutate',
    'lqinfinite', 'lqoftype', 'lqcastnum', 'lqtodict', 'lqselectmany',
    'lqsources', 'lqtostring',
    # 8장 — 식 트리
    'etcodedata', 'etnodes', 'etwalk', 'etilscan', 'etbyhand', 'etruntime',
    'etcompile', 'etnewobj', 'etequal', 'etconvert', 'etanon', 'etblock',
    'etoptional', 'etnatural', 'etclosure', 'etopaque', 'etparam',
    'etvisitor', 'etsql', 'etqueryable', 'etfuncvar',
    # 9장 — C# 3.0 정리
    'smc2', 'smc3', 'smc3m', 'smc3tree',
]


def run(ctx):
    for d in RUN:
        ctx.cs('ex/04/' + d)
    for d in FAIL:
        ctx.cs('ex/04/' + d, expect=1)
    # 늦게 돈 람다 안의 0 으로 나누기 — 잡지 않은 예외의 트레이스가 증거
    ctx.cs('ex/04/lqdeferexc', expect=ABORT)

    # 언어 버전 짝 (가) — 한 단계 내리면 컴파일러가 거절한다
    ctx.cs('ex/04/qgate', v='2', expect=1)           # query expression
    ctx.cs('ex/04/qoutvar', v='7.2', expect=1)       # out var in a query
    ctx.cs('ex/04/etoptional', v='13.0', expect=1)   # optional args in trees
    ctx.cs('ex/04/etnatural', v='9.0', expect=1)     # natural lambda type
    ctx.cs('ex/04/smc3', v='2', expect=1)            # 9장 — C# 3 을 C# 2 로

    # 게이트가 없는 쪽 — 쿼리의 낱말을 이름으로 쓴 C# 1 코드는 C# 14 에서도
    ctx.cs('ex/04/qkeywords', v='14.0')
