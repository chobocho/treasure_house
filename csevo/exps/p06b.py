# -*- coding: utf-8 -*-
"""6부 뒤 조각 — 호출자 정보 특성 · foreach 변수 포착 · 그 밖의 C# 5 ·
비동기의 그 뒤 · C# 5.0 정리의 증거.

C# 5 의 게이트는 async 하나뿐이다(0부). 호출자 정보 특성과 foreach 의
변화는 -langversion 으로 옛 동작이 돌아오지 않는다 — 그래서 'C# 4 로
내려도 같다' 는 캡처를 함께 남겨, 옛 동작은 풀어 쓴 코드로 보였다고
슬라이드가 밝힐 근거로 삼는다. 이 묶음은 두 번 돌려 바이트까지 같은
것만 쓴다."""

import subprocess

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 6장 — 호출자 정보 특성
    'callerbad',
    # 7장 — foreach 변수 포착
    'feref',
    # 9장 — 비동기의 그 뒤
    'afrefbad',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — 호출자 정보 특성
    'callerinfo', 'callerold', 'callerconst', 'callerpath', 'callerinpc',
    'callerinpcold', 'callerwrap', 'callermembers', 'callerctor',
    'callerlambda', 'callerdyn', 'callerover', 'callerrt', 'callerargexpr',
    'callerattr', 'callerlines', 'callerlater',
    # 7장 — foreach 변수 포착
    'fegate', 'fedesugar', 'fefor', 'feclosure', 'felinq', 'felater',
    'feasync',
    # 8장 — 그 밖의 C# 5
    'asyncinfer', 'asyncbetter',
    # 9장 — 비동기의 그 뒤 (예제마다 그 기능이 들어온 버전으로)
    'afcatch', 'afmain', 'afbuilder', 'afstream', 'afstreamsm', 'afbreak',
    'afcancel', 'afext', 'afusing', 'afref', 'afcawait',
    # 10장 — 정리: 같은 프로그램을 C# 4 와 C# 5 로
    'wrapc4', 'wrapc5',
]


class Retry(object):
    """ctx 를 감싸 csrun 의 60초 시간 초과만 두 번까지 다시 돌린다
    (p06 의 것과 같다 — 다른 묶음과 함께 돌면 스왑이 차서 느려진다)."""

    def __init__(self, ctx):
        self.ctx = ctx

    def cs(self, *a, **k):
        for _ in range(2):
            try:
                return self.ctx.cs(*a, **k)
            except subprocess.TimeoutExpired:
                pass
        return self.ctx.cs(*a, **k)


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/06/' + d)
    for d in FAIL:
        ctx.cs('ex/06/' + d, expect=1)

    # 6장 — 호출자 정보는 게이트가 없다: C# 4 로 내려도 채워진다(꼴 (나) 불가)
    ctx.cs('ex/06/callerinfo', v='4')
    # 선택적 매개변수 자체는 C# 4 의 게이트 — C# 3 으로 내리면 거절
    ctx.cs('ex/06/callerinfo', v='3', expect=1)
    # CallerArgumentExpression(C# 10)도 게이트가 없다 — C# 5 로 내려도 돈다
    ctx.cs('ex/06/callerargexpr', v='5')

    # 7장 — foreach 의 변화는 게이트가 없다: C# 4·3 으로 내려도 1 2 3
    ctx.cs('ex/06/fegate', v='4')
    ctx.cs('ex/06/fegate', v='3')
    # 클로저 객체의 수는 최적화 빌드에서도 같은가
    ctx.cs('ex/06/feclosure', flags='-optimize+', tag='opt')
    # ref 반복 변수(C# 7.3)의 게이트, 그리고 C# 14 에서도 포착 불가
    ctx.cs('ex/06/felater', v='7.2', expect=1)
    ctx.cs('ex/06/feref', v='14.0', expect=1)

    # 8장 — async 람다는 C# 5 의 것: C# 4 로 내리면 람다마다 거절
    ctx.cs('ex/06/asyncinfer', v='4', expect=1)

    # 9장 — 뒤 버전의 비동기 기능: 한 버전 아래에서 거절
    ctx.cs('ex/06/afcatch', v='5', expect=1)        # catch·finally 의 await
    ctx.cs('ex/06/afmain', v='7.0', expect=1)       # async Main
    # async Task<int> Main 의 반환값이 종료 코드가 된다 — 인자 둘이면 2
    ctx.cs('ex/06/afmain', cmd='csrun -- a b', tag='args', expect=2)
    ctx.cs('ex/06/afbuilder', v='9.0', expect=1)    # 메서드의 빌더
    ctx.cs('ex/06/afstream', v='7.3', expect=1)     # async streams
    ctx.cs('ex/06/afext', v='8.0', expect=1)        # 확장 GetAsyncEnumerator
    ctx.cs('ex/06/afusing', v='7.3', expect=1)      # await using
    ctx.cs('ex/06/afref', v='12.0', expect=1)       # async 안의 ref 지역
    ctx.cs('ex/06/afrefbad', v='14.0', expect=1)    # await 를 건너면 C# 14 도

    # 10장 — C# 5 판을 C# 4 로 내리면 async 만 거절된다
    ctx.cs('ex/06/wrapc5', v='4', expect=1)
