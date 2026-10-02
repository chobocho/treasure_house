# -*- coding: utf-8 -*-
"""8부 앞 조각 — C# 7.0 의 큰 기능: 튜플·분해·버리기, 패턴 매칭,
out 변수, 지역 함수의 증거. 예제는 ex/08/ 아래에 있다.
(ref·throw 식·식 본문·리터럴·C# 7.1 은 p08b, C# 7.2·7.3 은 p08c 가
같은 ex/08 에 다른 이름으로 쓴다)"""
import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관과 같이 온 런타임
    'tupgates5', 'tupbefore', 'tupruntime',
    # 2장 — 튜플
    'tupgate', 'tupvsclass', 'tupnames', 'tupnameattr', 'tupmutable',
    'tupequals', 'tupdict', 'tupconv', 'tupwarn', 'tupobject',
    'tupgeneric', 'tupbig', 'tupswap', 'tupasync', 'tuplinq',
    # 2장 — 분해와 버리기
    'tupdecon', 'tupdeconuser', 'tupdeconext', 'tupdeconorder',
    'tupdeconnest', 'tupdeconmix', 'discgate', 'disckinds', 'discident',
    # 3장 — 패턴 매칭
    'patgate', 'patasis', 'patconst', 'patnullop', 'patvar',
    'patnullable', 'patswitch', 'patdefault', 'patnull', 'patwhen',
    'patscope', 'patdisamb', 'pattry', 'patlater8', 'patlater9',
    'patlater11',
    # 4장 — out 변수와 지역 함수
    'outvgate', 'outvscope', 'outvoverload', 'outvinit73',
    'locfngate', 'locfncapture', 'locfnclosure', 'locfndelegate',
    'locfnname', 'locfniter', 'locfnasync', 'locfnlambda',
    'locfnstatic8', 'locfnattr9',
    # 덧붙인 것 — 대상 형식·식 트리·필터·C# 8·9
    'tupnull', 'patcatch', 'disclambda9', 'locfnshadow8',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'tupreserved', 'tupoverload', 'tupdeconbad', 'discbad',
    'patcompat', 'patorder', 'patmulti', 'patscopebad', 'patgeneric',
    'locfndefassign', 'tupiface', 'tupexpr',
]

# 처리기 없는 예외로 끝나는 예제 — 스택 트레이스가 증거다
ABORTS = [
]

# #if BAD 줄을 켜면 컴파일러가 거절한다 — (예제, 종료 코드)
BAD = [
    ('tupvsclass', 1), ('tupmutable', 1), ('tupequals', 1),
    ('tupasync', 1), ('tuplinq', 1), ('discident', 1),
    ('patnullable', 1), ('outvoverload', 1), ('locfnlambda', 1),
    ('locfnstatic8', 1), ('tupnull', 1),
]

# C# 6 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED6 = [
    'tupgates5', 'tupgate', 'tupdecon', 'discgate', 'patgate',
    'patswitch', 'outvgate', 'locfngate',
]

# 뒤 버전 기능 — 한 단계 아래로 내리면 거절 (예제, 아래 버전)
LATER = [
    ('tupdeconmix', '9.0'), ('patlater8', '7.3'), ('patlater9', '8.0'),
    ('patlater11', '10.0'), ('outvinit73', '7.2'),
    ('locfnstatic8', '7.3'), ('locfnattr9', '8.0'),
    ('disclambda9', '8.0'), ('locfnshadow8', '7.3'),
]


class Retry(object):
    """스왑이 찬 날에는 csc 하나가 60초를 넘기기도 한다(2026-10-01 두 번).
    시간 초과만 두 번까지 다시 돌린다 — 출력이 다른 것은 다시 돌리지
    않는다(기대한 종료 코드가 아니면 run_all 이 그대로 멈춘다)."""

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
        ctx.cs('ex/08/' + d)
    for d in FAIL:
        ctx.cs('ex/08/' + d, expect=1)
    for d in ABORTS:
        ctx.cs('ex/08/' + d, expect=ABORT)
    for d in GATED6:
        ctx.cs('ex/08/' + d, v='6', expect=1)
    for d, code in BAD:
        ctx.cs('ex/08/' + d, flags='-define:BAD', tag='bad', expect=code)
    for d, v in LATER:
        ctx.cs('ex/08/' + d, v=v, expect=1)

    # 형식 매개변수에 패턴 — C# 7.0 은 거절(위 FAIL), C# 7.1 은 돈다
    ctx.cs('ex/08/patgeneric', v='7.1')
    # 섞은 분해 — C# 7.0 으로 내려도 '10.0 을 쓰라'
    ctx.cs('ex/08/tupdeconmix', v='7.0', expect=1)
    # 식 트리 안의 튜플·패턴·out var — C# 14 로 올려도 거절
    ctx.cs('ex/08/tupexpr', v='14.0', expect=1)
