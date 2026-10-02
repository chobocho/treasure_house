# -*- coding: utf-8 -*-
"""5부 — C# 4.0 의 증거: dynamic · 명명·선택 인수 · 제네릭 변성 · COM 과
그 밖의 것. 예제는 ex/05/ 아래에 있다."""
import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관과 같이 온 런타임
    'fourgates', 'dlrasm', 'bclasm', 'refasm',
    # 2장 — dynamic
    'dyngate', 'dynname', 'dynbind', 'dynsame', 'dynattr', 'dynerr',
    'dynmulti', 'dynstatic', 'dynops', 'dynchecked', 'dynconv',
    'dyncompound', 'dynleak', 'dynlambda', 'dynvoid', 'dyninacc',
    'dynexpando', 'dynnotify', 'dynobj', 'dynobjinvoke', 'dynobjreal',
    'dyncallsite', 'dynreflect', 'dynstruct', 'dynrefarg', 'dyncheck',
    'dynpattern', 'dynnullable', 'dyngenattr', 'dyninfer', 'dynnull',
    'dyncache', 'dynevent',
    # 3장 — 명명·선택 인수
    'optgate', 'namedgate', 'optbefore', 'optafter', 'optvalues',
    'optorder', 'optil', 'optmeta', 'optattr', 'optoverload', 'optparams',
    'optvirtual', 'optiface', 'namedswap', 'optwarn', 'optdelegate',
    'namedattr', 'namednontrail', 'optlambda', 'optexprtree', 'nameddyn',
    'callerdyn', 'optdefault', 'optstruct',
    # 4장 — 제네릭 변성
    'vargate', 'varco', 'varcontra', 'varnested', 'varvalue', 'vardelegate',
    'vararray', 'varbcl', 'varis', 'varreturn', 'varext', 'varinfer',
    # 5장 — COM 과 그 밖의 것
    'comref', 'nopiaattr',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'dynsig', 'dynwhere', 'dynstaticrecv',
    'namedbreak',
    'varunsafe', 'varunsafein', 'varwhere',
]

# 처리기 없는 예외로 끝나는 예제 — 스택 트레이스가 증거다
ABORTS = [
    'dynerr2', 'dynindex', 'varcombine',
]

# -define:BAD 로 켜는 틀린 줄 — 같은 파일의 거절(또는 경고)
BAD = [
    ('dynleak', 1), ('dynlambda', 1), ('dynrefarg', 1), ('dyncheck', 1),
    ('dynpattern', 1), ('dyngenattr', 1), ('dynvoid', 1),
    ('dyninfer', 1),
    ('optvalues', 1), ('optoverload', 1), ('optdelegate', 1),
    ('namednontrail', 1), ('optexprtree', 1),
    ('varvalue', 1), ('comref', 1), ('optstruct', 1),
    ('dynnullable', ABORT),
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
        ctx.cs('ex/05/' + d)
    for d in FAIL:
        ctx.cs('ex/05/' + d, expect=1)
    for d in ABORTS:
        ctx.cs('ex/05/' + d, expect=ABORT)
    for d, code in BAD:
        ctx.cs('ex/05/' + d, flags='-define:BAD', tag='bad', expect=code)

    # 언어 버전 짝 (가) — C# 3 으로 내리면
    ctx.cs('ex/05/fourgates', v='3', expect=1)   # 선언의 두 게이트만 보인다
    ctx.cs('ex/05/dyngate', v='3', expect=1)     # dynamic 은 그냥 이름
    ctx.cs('ex/05/dynname', v='3')               # 내 클래스 dynamic 은 C# 3 도
    # dynamic 을 쓰면 참조 어셈블리가 는다
    ctx.cs('ex/05/refasm', flags='-define:DYN', tag='dyn')
    ctx.cs('ex/05/optgate', v='3', expect=1)     # optional parameter
    ctx.cs('ex/05/namedgate', v='3', expect=1)   # named argument
    ctx.cs('ex/05/namedattr', v='3', expect=1)   # 특성의 명명 인수도
    ctx.cs('ex/05/vargate', v='3', expect=1)     # type variance
    # 게이트가 없는 쪽 — C# 3 으로도 컴파일된다
    ctx.cs('ex/05/optattr', v='3')               # [Optional] 을 생략해 부르기
    ctx.cs('ex/05/comref', v='3')                # COM 메서드의 ref 생략
    ctx.cs('ex/05/varinfer', v='3')              # 변성을 쓰는 형식 유추
    # 컴파일러 옵션 -link(NoPIA)는 지금도 있다 — 없는 파일을 주면
    ctx.cs('ex/05/nopiaattr', flags='-link:missing.dll', tag='link',
           expect=1)
    # 뒤 버전 — 한 단계 아래로 내리면
    ctx.cs('ex/05/dynpattern', v='6', expect=1)  # pattern matching (C# 7)
    ctx.cs('ex/05/namednontrail', v='7.1', expect=1)  # non-trailing (7.2)
    ctx.cs('ex/05/optlambda', v='11.0', expect=1)     # lambda optional (12)
    ctx.cs('ex/05/optexprtree', v='13.0', expect=1)   # expression trees (14)
    ctx.cs('ex/05/varreturn', v='8.0', expect=1)      # covariant returns (9)
    ctx.cs('ex/05/optdefault', v='7.0', expect=1)     # default literal (7.1)
