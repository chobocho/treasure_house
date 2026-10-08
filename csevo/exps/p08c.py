# -*- coding: utf-8 -*-
"""8부 뒤 조각 — C# 7.2(in·ref readonly·readonly struct·ref struct 와
Span·ref 조건식·ref 확장 메서드·private protected·0x_)와 C# 7.3(튜플
==·ref 재할당·ref for·stackalloc 초기화자·새 제약·[field:]·식 변수·
오버로드 후보·fixed 패턴·움직이는 고정 버퍼), 그리고 8부 정리의 증거.
예제는 ex/08/ 아래의 inp*·ro*·rs*·span*·v72*·v73* 이다."""
import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 7장 — in 매개변수
    'inpbasic', 'inpcopy', 'inpalias', 'inpover', 'inpmeta',
    # 7장 — ref readonly, readonly struct
    'rorefret', 'rostruct', 'rostructcopy',
    # 7장 — ref struct 와 Span
    'rsbasic', 'rsiface13', 'rsmeta', 'spanrt', 'spanslice', 'spanstack',
    # 7장 — ref 조건식·ref 확장·private protected·0x_
    'v72refcond', 'v72refext', 'v72pp', 'v72lead',
    # 8장 — C# 7.3
    'v73tupeq', 'v73tupeqorder', 'v73tupeqwarn', 'v73reref', 'v73reffor',
    'v73stackinit', 'v73enumdel', 'v73unmanaged', 'v73unmgen', 'v73unmmeta',
    'v73fieldattr', 'v73exprvar', 'v73overload', 'v73fixed', 'v73fixbuf',
    'v73pathmap', 'v73rt',
    # 9장 — 정리
    'v73sum6', 'v73sum73', 'v73to8',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'inpwrite', 'inplimit', 'inpasync', 'rorefbad', 'rostructbad',
    'roasref', 'rsheap', 'rsfield', 'rscapture', 'rsasync', 'spanescape',
    'v72refextbad', 'v72break', 'v73enumkw', 'v73unmbad',
]

# 처리기 없는 예외로 끝나는 예제 — 스택 트레이스가 증거다
ABORTS = [
]

# #if BAD 줄을 켜면 컴파일러가 거절한다 — (예제, 종료 코드)
BAD = [
    ('spanstack', 1), ('v72refext', 1), ('v72pp', 1), ('v72lead', 1),
    ('v73reref', 1), ('v73reffor', 1), ('v73enumdel', 1),
    ('v73exprvar', 1), ('v73fixbuf', 1),
]

# 한 단계 아래 버전으로 내리면 거절되는 것 — 언어 버전 짝 (가)
# (예제, 아래 버전)
GATED = [
    ('inpbasic', '7.1'), ('rorefret', '7.1'), ('rostruct', '7.1'),
    ('rsbasic', '7.1'), ('spanstack', '7.1'), ('v72refcond', '7.1'),
    ('v72refext', '7.1'), ('v72pp', '7.1'), ('v72lead', '7.1'),
    ('rsiface13', '12.0'), ('rsiface13', '7.2'),
    ('v73tupeq', '7.2'), ('v73reref', '7.2'), ('v73reffor', '7.2'),
    ('v73stackinit', '7.2'), ('v73enumdel', '7.2'), ('v73unmanaged', '7.2'),
    ('v73unmgen', '7.3'), ('v73exprvar', '7.2'), ('v73overload', '7.2'),
    ('v73fixed', '7.2'), ('v73fixbuf', '7.2'),
    ('v73sum73', '6'), ('v73to8', '7.3'),
]

# 같은 소스를 다른 버전으로 — 거절이 아니라 같은 답인지 보는 것 (나)
SAME = [
    ('inpover', '7.3'), ('spanslice', '7.1'), ('v73fieldattr', '7.2'),
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
    for d, code in BAD:
        ctx.cs('ex/08/' + d, flags='-define:BAD', tag='bad', expect=code)
    for d, v in GATED:
        ctx.cs('ex/08/' + d, v=v, expect=1)
    for d, v in SAME:
        ctx.cs('ex/08/' + d, v=v)

    # .NET 10 의 Unsafe.AsRef(in …) 는 C# 12 의 ref readonly 매개변수 — 12 면 된다
    ctx.cs('ex/08/roasref', v='12.0')
    # 7.1 컴파일러가 받던 default ?? 1 — 지금의 컴파일러는 7.1 에서도 거절
    ctx.cs('ex/08/v72break', v='7.1', expect=1)
    # async 를 람다·반복기와 한 파일에 두면 CS1988 하나만 남는다
    ctx.cs('ex/08/inplimit', flags='-define:ASYNC', tag='async', expect=1)
    # 중첩 stackalloc 은 C# 8 — 8.0 에서 되고 7.3 에서 거절
    ctx.cs('ex/08/v73stackinit', v='8.0', flags='-define:NEST', tag='nest')
    ctx.cs('ex/08/v73stackinit', flags='-define:NEST', tag='nest', expect=1)
    # 제네릭 구조체 P<int> 는 C# 8.0 에서 unmanaged — 거절이 둘로 준다
    ctx.cs('ex/08/v73unmbad', v='8.0', expect=1)
