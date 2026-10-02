# -*- coding: utf-8 -*-
"""7부 앞 조각 — C# 6.0 의 Roslyn·문자열 보간·nameof·null 조건 연산자의 증거.
(식 본문·자동 속성·using static·예외 필터·인덱스 초기화자·정리는 p07b)

Roslyn 예제 셋(roslyncsc·roslynapi·roslyncomp)은 SDK 의 컴파일러
어셈블리를 경로로 읽는다 — 이 기계의 SDK 10.0.112 자리다. 출력에는
그 경로를 찍지 않는다."""

import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'nameofbad', 'nameofshadow',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관과 Roslyn
    'boiler5', 'boiler6', 'gates12', 'roslyncsc', 'roslynapi',
    'roslyncomp', 'determ', 'runtime',
    # 2장 — 문자열 보간
    'interpgate', 'interpfmterr', 'interpfmt', 'interpescape',
    'interpcond', 'interpculture', 'interpformattable',
    'interpiformattable', 'interpoverload', 'interplower', 'interpil',
    'interpawait', 'interpnull', 'interptimespan', 'interpforget',
    'interpet', 'interpevalorder',
    # 2장 — 뒤 버전(각자의 LangVersion)
    'interpverb8', 'interpconst10', 'interphandler10', 'interpskip10',
    'interpmanual10', 'interpnewline11', 'interpraw11',
    # 3장 — nameof
    'nameofgate', 'nameofkinds', 'nameofnoeval', 'nameofconst',
    'nameofrename', 'nameofinpc', 'nameofgeneric', 'nameofident',
    'nameofattr11', 'nameofinst12', 'nameofunbound14',
    # 4장 — null 조건 연산자
    'ncgate', 'ncindex', 'ncchain', 'nclift', 'nccoalesce', 'nconce',
    'ncevent', 'ncvoid', 'ncvaluetype', 'ncgeneric', 'ncuserop',
    'ncawait', 'ncdynamic', 'ncet', 'ncassign14', 'ncnrt8',
]

# #if BAD 줄을 켜면 컴파일러가 거절한다 — (예제, 종료 코드)
BAD = [
    ('interpcond', 1), ('interpoverload', 1), ('interptimespan', 1),
    ('nccoalesce', 1), ('ncvoid', 1), ('ncvaluetype', 1),
    ('ncgeneric', 1), ('ncet', 1), ('ncassign14', 1),
]

# 뒤 버전 기능 — 한 단계 아래로 내리면 거절 (예제, 아래 버전)
LATER = [
    ('interpverb8', '7.3'), ('interpconst10', '9.0'),
    ('interphandler10', '9.0'), ('interpskip10', '9.0'),
    ('interpnewline11', '10.0'), ('interpraw11', '10.0'),
    ('nameofinst12', '11.0'), ('nameofunbound14', '13.0'),
    ('nameofshadow', '10.0'), ('ncassign14', '13.0'),
]

# C# 5 로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED5 = [
    'boiler6', 'gates12', 'interpgate', 'nameofgate', 'ncgate',
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
        ctx.cs('ex/07/' + d)
    for d in FAIL:
        ctx.cs('ex/07/' + d, expect=1)
    for d in GATED5:
        ctx.cs('ex/07/' + d, v='5', expect=1)
    for d, code in BAD:
        ctx.cs('ex/07/' + d, flags='-define:BAD', tag='bad', expect=code)
    for d, v in LATER:
        ctx.cs('ex/07/' + d, v=v, expect=1)

    # 결정적 컴파일 — 다른 작업 디렉터리에서 한 번 더, 기호 하나를 더해 한 번
    ctx.cs('ex/07/determ', tag='again')
    ctx.cs('ex/07/determ', flags='-define:X', tag='defx')

    # 번역은 언어 버전을 따지지 않는다 — C# 10 으로 컴파일해도 같은가 (나)
    ctx.cs('ex/07/interplower', v='10.0')
    ctx.cs('ex/07/interpil', v='10.0')
    # 식 트리 안의 보간 — C# 14 에서도 string.Format
    ctx.cs('ex/07/interpet', v='14.0')

    # nameof(int) 은 구문 오류 — 켜면 다른 오류를 가린다
    ctx.cs('ex/07/nameofbad', flags='-define:INT', tag='int', expect=1)
    # C# 11 의 nameof 범위 — 게이트가 없어 C# 10 으로도 컴파일된다
    ctx.cs('ex/07/nameofattr11', v='10.0')
    # 가림(shadowing) — 문서는 C# 11 부터라지만 C# 6 에서도 매개변수가 가린다
    ctx.cs('ex/07/nameofshadow', v='6', expect=1)
    # C# 6 의 ?. 는 대입의 왼쪽이 될 수 없다
    ctx.cs('ex/07/ncassign14', v='6', expect=1)
