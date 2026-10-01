# -*- coding: utf-8 -*-
"""6부 앞 조각 — C# 5.0 의 async/await 의 증거.
(호출자 정보 특성·foreach 변수 포착·C# 5.0 정리는 p06b)

비동기 예제의 출력은 실행마다 같아야 한다. 그래서 예제는 스레드 번호·
시각을 찍지 않고, 차례는 await 나 TaskCompletionSource 나 한 스레드짜리
동기화 문맥이 정한다. 이 묶음은 두 번 돌려 바이트까지 같은 것만 쓴다."""

import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 3장 — 문법과 의미
    'rettypebad', 'returnbad', 'awaitname', 'awaitoutside', 'awaitlock',
    'asyncref', 'lambdanested', 'awaitplaces', 'awaitvoid',
    # 4장 — 컴파일러가 만드는 것
    'awaitbad',
    # 5장 — 함정
    'asyncabstract',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관
    'gate', 'awaitident', 'runtime', 'compdeps',
    # 2장 — 왜 async 인가: 같은 프로그램 다섯 가지
    'stylesync', 'styleapm', 'styleeap', 'styletpl', 'styleawait',
    'styleexc',
    # 3장 — 문법과 의미
    'rettypes', 'valuetask', 'noawait', 'split', 'syncfirst', 'completed',
    'yield', 'awaitexpr', 'excawait', 'excwait', 'exccancel',
    'asyncvoidctx', 'cs4014', 'catchfinally', 'asynclambda', 'asyncmain',
    'seqconc',
    # 4장 — 컴파일러가 만드는 것
    'smtype', 'smfields', 'builder', 'smhand', 'awaitable', 'critical',
    'extawait', 'awaitdyn', 'syncctx', 'configawait', 'deadlock',
    'deadlockfix', 'smawaiters',
    # 5장 — 함정
    'trapnowarn', 'traplambda', 'trapoverload', 'trapsync', 'traplazyarg',
    'trapstartnew', 'trapwhenall', 'trapwhenany', 'whenallorder',
    'trapcancel', 'trapcanceldelay', 'asyncimpl', 'awaitnull',
    'threadstatic',
    # 더한 것 — 1장·3장
    'taskstatus', 'awaittry', 'awaitusing', 'tcswrap', 'awaitshort',
    'smbuilders', 'lambdasm', 'asynclocal',
]


class Retry(object):
    """ctx 를 감싸 csrun 의 60초 시간 초과만 두 번까지 다시 돌린다.
    다른 서브에이전트와 함께 돌 때 스왑이 차서 컴파일 하나가 20–60초로
    늘어났다(2026-10-01). 출력이 다르면 다시 돌리지 않는다 — 그것은
    두 번 돌려 비교하는 검사가 잡는다."""

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

    # 언어 버전 짝 (가) — C# 4 로 내리면 컴파일러가 거절한다
    ctx.cs('ex/06/gate', v='4', expect=1)           # async function
    ctx.cs('ex/06/awaitident', v='4', expect=1)     # await 이름은 되고 async 만

    # async void 의 예외 — 스레드 풀에서 다시 던져져 프로세스가 끝난다
    ctx.cs('ex/06/asyncvoid', expect=ABORT)
    # 처리하지 않은 예외가 async 메서드 두 겹을 건너 Main 까지
    ctx.cs('ex/06/asyncstack', expect=ABORT)

    # C# 5 의 제약 — catch·finally 의 await 는 C# 6 에서 풀렸다
    ctx.cs('ex/06/catchfinally', v='5', expect=1)
    # lock 안의 await 는 C# 14 에서도 거절
    ctx.cs('ex/06/awaitlock', v='14.0', expect=1)
    # ref·out 매개변수, unsafe·식 트리 안의 await 도 C# 14 에서 그대로
    ctx.cs('ex/06/asyncref', v='14.0', expect=1)
    ctx.cs('ex/06/awaitplaces', v='14.0', expect=1)
    # 몸체 없는 멤버의 async — C# 14 에서는 CS1994 만 남는가
    ctx.cs('ex/06/asyncabstract', v='14.0', expect=1)
    # 뒤 버전과의 맞물림 — async Main 은 C# 7.1
    ctx.cs('ex/06/asyncmain', v='7.0', expect=1)

    # 디버그 빌드(csrun 의 기본)와 최적화 빌드 — 상태 기계가 class 냐 struct 냐
    ctx.cs('ex/06/smtype', flags='-optimize+', tag='opt')
    ctx.cs('ex/06/smfields', flags='-optimize+', tag='opt')
