# -*- coding: utf-8 -*-
"""10부 앞 조각 — C# 9.0 개관(.NET 5, 경고 웨이브 5)과 레코드·init·with 의 증거.
예제는 ex/10/ 아래의 ov*·rec*·with*·init* 이다. (최상위 문·패턴·성능은
p10b, 다듬기·코드 생성기 지원은 p10c 가 같은 ex/10 에 다른 이름으로 쓴다)

레코드 선언은 C# 8.0 에서 '레코드' 로 읽히지 않는다 — 'records' 거절은
with 식에서만 나온다(withgate). 그래서 recgate 의 8.0 캡처에는 다른
오류들이 찍힌다. 슬라이드는 그것을 그대로 보인다."""
import subprocess

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovruntime', 'ovwave',
    # 2장 — 레코드 선언
    'recgate', 'recambig', 'recpos', 'recnominal', 'recmembers', 'rechand',
    # 2장 — 값 동등성
    'receq', 'receqnan', 'receqarr', 'recfields', 'receqcustom', 'recasym',
    'reccontract', 'recspoof', 'recinherit', 'recabstract',
    # 2장 — 출력·분해·생성자
    'recstr', 'recprint', 'reccycle', 'recsealed10', 'recdecon',
    'recownprop', 'recctor', 'recattr', 'reccopy', 'recmut', 'recvs',
    # 2장 — with
    'withbasic', 'withlower', 'withshallow', 'withdeep', 'recvalid',
    'withnull',
    'withstruct10',
    # 2장 — init
    'initgate', 'initwhere', 'initro', 'initvirt', 'initiface',
    'initstruct', 'initidx', 'initmodreq', 'initpoly', 'initdefault',
    # 2장 — 뒤 버전
    'initrequired11', 'recstruct10', 'recprimary12',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['withgate', 'recforbid', 'rechidden', 'withbad', 'initnot',
        'initrestrict']

# 처리기 없는 예외로 끝나는 예제
ABORTS = []

# C# 8.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED8 = ['ovgates', 'recgate', 'recnominal', 'withgate', 'initgate']

# 8.0 에서도 컴파일되지만 뜻이 달라지는 것 — (나)
SAME8 = ['recambig']

# 뒤 버전 기능 — (예제, 한 단계 아래 버전)
LATER = [('recstruct10', '9.0'), ('withstruct10', '9.0'),
         ('recsealed10', '9.0'), ('initrequired11', '10.0'),
         ('recprimary12', '11.0')]

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전, 종료 코드)
DEFINES = [
    ('recsealed10', 'C9', '10.0', 0),
    ('recownprop', 'BAD', '9.0', 0),
    ('recctor', 'BAD', '9.0', 1),
    ('recvs', 'BAD', '9.0', 1),
    ('withbad', 'STMT', '9.0', 1),
    ('initro', 'BAD', '9.0', 1),
    ('initvirt', 'BAD', '9.0', 1),
    ('initiface', 'BAD', '9.0', 1),
    ('initstruct', 'BAD', '9.0', 1),
    ('initidx', 'BAD', '9.0', 1),
    ('initrequired11', 'BAD', '11.0', 1),
]

# 경고 웨이브 5 — 경고 수준으로만 켜진다(언어 버전과 무관)
WAVE = [('ovwave', None), ('ovwave', '7.3')]


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
        ctx.cs('ex/10/' + d)
    for d in FAIL:
        ctx.cs('ex/10/' + d, expect=1)
    for d in ABORTS:
        ctx.cs('ex/10/' + d, expect=ABORT)
    for d in GATED8:
        ctx.cs('ex/10/' + d, v='8.0', expect=1)
    for d in SAME8:
        ctx.cs('ex/10/' + d, v='8.0')
    for d, v in LATER:
        ctx.cs('ex/10/' + d, v=v, expect=1)
    for d, sym, v, code in DEFINES:
        ctx.cs('ex/10/' + d, v=v, flags='-define:' + sym,
               tag=sym.lower(), expect=code)
    for d, v in WAVE:
        ctx.cs('ex/10/' + d, v=v, flags='-warn:5', tag='w5')

