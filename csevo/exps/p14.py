# -*- coding: utf-8 -*-
"""14부 앞 조각 — C# 13 개관(게이트 아홉 · .NET 9 · 같이 온 형식 ·
경고 웨이브 9 가 없음 · .NET 9 의 깨지는 변경), params 컬렉션, Lock 객체의
증거. 예제는 ex/14/ 아래의 ov*·pm*·cb*·lk*·v13* 이다(p14b·p14c 는 같은
ex/14 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 12.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다
(둘이면 실행마다 순서가 바뀔 수 있어서). 선언에서 난 오류는 몸체의
오류를 가리고, \\e 의 거절(어휘 분석 단계)은 나머지를 모두 가린다."""
import subprocess

EX = 'ex/14/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion(13.0)으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovgates2', 'ovruntime', 'ovbcl', 'ovwave', 'ovinline',
    # 2장 — params 컬렉션
    'pmbasic', 'pmiface', 'pmconcrete', 'cbparams', 'pminfer',
    'pmforms', 'pmover', 'pmbcl', 'pmbcllist', 'pmmeta', 'pmscoped',
    'pmovr', 'pmlambda', 'pmdyn', 'pmexpr', 'pmorder', 'pmbetter',
    'pmempty', 'pmtie', 'pmerr', 'pmasync', 'pmreq',
    # 3장 — Lock 객체
    'lkbasic', 'lkscope', 'lkobj', 'lkgen', 'lkasync', 'lkthreads',
]

# C# 12.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED12 = ['ovgates', 'ovgates2', 'pmbasic', 'pmlambda', 'lkbasic']

# 다른 버전으로 — (예제, 언어 버전, 종료 코드)
OTHER = [('pminfer', '14.0', 0), ('pmbcl', '12.0', 0),
         ('pmbetter', '12.0', 0), ('lkscope', '12.0', 0)]

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전 또는 None, 종료 코드)
DEFINES = [
    ('ovgates', 'NOESC', '12.0', 1),
    ('ovinline', 'BAD', None, 1), ('ovinline', 'BAD', '12.0', 1),
    ('pmscoped', 'ESCAPE', None, 1), ('pmovr', 'BAD', None, 1),
    ('pmdyn', 'BAD', None, 1), ('pmexpr', 'BAD', None, 1),
    ('pmbetter', 'ELEM', None, 0), ('pmbetter', 'ELEM', '12.0', 1),
    ('pmempty', 'EMPTY', None, 1), ('pmempty', 'EMPTY', '12.0', 0),
    ('pmtie', 'NONE', None, 1),
    ('pmerr', 'INT', None, 1), ('pmerr', 'NOADD', None, 1),
    ('pmerr', 'DICT', None, 1), ('pmerr', 'DEFAULT', None, 1),
    ('pmasync', 'SPAN', None, 1), ('pmreq', 'BAD', None, 1),
    ('lkasync', 'AWAIT', None, 1), ('lkasync', 'USING', None, 1),
    ('lkasync', 'USING', '12.0', 1),
]

# 경고 수준을 올린 캡처 — (예제, 수준, 언어 버전 또는 None)
WAVE = [('ovwave', 9, None), ('ovwave', 10, None), ('ovwave', 10, '12.0')]

# 프로그램 인자로 메서드 이름을 주는 IL 캡처 — (꼬리표, 메서드들)
IL = [('pm', 'ArrayVars SpanConsts SpanVars SpanNone EnumVars'),
      ('lk', 'LockLock LockObject')]


class Retry(object):
    """스왑이 찬 날에는 csc 하나가 60초를 넘기기도 한다. 시간 초과만 두
    번까지 다시 돌린다 — 출력이 다른 것은 다시 돌리지 않는다."""

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
        ctx.cs(EX + d)
    for d in GATED12:
        ctx.cs(EX + d, v='12.0', expect=1)
    for d, v, code in OTHER:
        ctx.cs(EX + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        ctx.cs(EX + d, v=v, flags='-define:' + sym, tag=sym.lower(),
               expect=code)
    for d, lvl, v in WAVE:
        ctx.cs(EX + d, v=v, flags='-warn:%d' % lvl, tag='w%d' % lvl)
    for tag, methods in IL:
        ctx.cs(EX + 'v13il', cmd='csrun -- ' + methods, tag=tag)
    # 할당 측정 — 최적화하고 계층 컴파일을 끈 것, 그리고 이 덱의 기본
    ctx.cs(EX + 'pmalloc', flags='-optimize+',
           env='DOTNET_TieredCompilation=0', tag='opt')
    ctx.cs(EX + 'pmalloc')
