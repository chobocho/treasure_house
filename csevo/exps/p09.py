# -*- coding: utf-8 -*-
"""9부 앞 조각 — C# 8.0 개관(런타임 결합)과 nullable 참조 형식의 증거.
예제는 ex/09/ 아래의 ov*·nrt*·nn* 이다. (패턴·인덱스·비동기 스트림은
p09b, 기본 인터페이스 메서드와 작은 기능들은 p09c 가 같은 ex/09 에 다른
이름으로 쓴다)

nullable 경고는 경고일 뿐이라 종료 코드가 0 이다 — 경고가 증거인 예제는
EXPECT_WARN 을 두고 그대로(expect=0) 캡처한다."""
import os
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

CSC = 'dotnet /usr/lib/dotnet/sdk/10.0.112/Roslyn/bincore/csc.dll'

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovruntime', 'ovtnew',
    # 2장 — 켜기와 문맥
    'nrtgate', 'nrtproj', 'nrtctx', 'nrtrestore', 'nrtpragma',
    # 2장 — 같은 형식, 메타데이터
    'nrtsame', 'nrtmeta', 'nrtembed',
    # 2장 — 흐름 분석과 경고
    'nrtflow', 'nrtassign', 'nrtreturn', 'nrtctor', 'nrtchecks',
    'nrtlearn', 'nrtvar', 'nrtconv', 'nrtlinq', 'nrttostring',
    'nrtctorfix', 'nrtinfer', 'nrtnever', 'nrtasync',
    # 2장 — ! 와 제네릭
    'nrtbangidiom', 'nrtgeneric', 'nrttq', 'nrtclassq',
    'nnbasic', 'nnwarn', 'nnmeta', 'nncoalesce', 'nnoverride',
    'nndefault9',
    # 2장 — 특성과 BCL
    'nnattrs', 'nnallow', 'nnmaybe', 'nnwhen', 'nnifnn', 'nnnoreturn',
    'nnattrbody', 'nrtbcl', 'nrtbclcount', 'nnmember9',
    # 2장 — 옮기기와 그 뒤
    'nrtoverride', 'nrtmigrate', 'nrtguard',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['ovversion', 'nrtbangbang']

# 처리기 없는 예외로 끝나는 예제 — 경고 없이(또는 경고와 함께) 터진다
ABORTS = [
    'nrtwhy', 'nrtoblivious', 'nrtfool', 'nrtlambda', 'nrtarray',
    'nrtstruct', 'nrtbang',
]

# C# 7.3 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED73 = ['ovgates', 'nrtgate', 'nnbasic', 'nncoalesce', 'nnoverride']

# 뒤 버전 기능 — 한 단계 아래(8.0)로 내리면 거절
LATER = ['ovtnew', 'nnmember9']

# C# 8.0 에서 제약 없는 T? 는 CS8627 — 그 줄은 200칸을 넘어 캡처로 싣지
# 못한다. 그래서 거절만 확인하고 저장하지 않는다(덱은 그렇게 밝힌다)
TQ_REFUSED = ['nrttq', 'nndefault9']

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전, 종료 코드)
DEFINES = [
    ('nrtsame', 'BAD', None, 1), ('nrtsame', 'DUP', None, 1),
    ('nrtbangidiom', 'BAD', None, 1), ('nnallow', 'BAD', None, ABORT),
    ('nnifnn', 'BAD', None, 0),
]


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
        ctx.cs('ex/09/' + d)
    for d in FAIL:
        ctx.cs('ex/09/' + d, expect=1)
    for d in ABORTS:
        ctx.cs('ex/09/' + d, expect=ABORT)
    for d in GATED73:
        ctx.cs('ex/09/' + d, v='7.3', expect=1)
    for d in LATER:
        ctx.cs('ex/09/' + d, v='8.0', expect=1)
    for d, sym, v, code in DEFINES:
        ctx.cs('ex/09/' + d, v=v, flags='-define:' + sym,
               tag=sym.lower(), expect=code)

    for d in TQ_REFUSED:
        code, text = csver.execute(os.path.join(csver.BASE, 'ex/09', d),
                                   'csrun', v='8.0', name='p09-check-' + d)
        if code != 1 or 'error CS8627' not in text:
            raise RuntimeError('[p09] %s 는 C# 8.0 에서 CS8627 이어야 한다\n%s'
                               % (d, text))

    # 컴파일러가 아는 언어 버전 목록과 '#error version'
    ctx.cs('ex/09/ovversion', cmd=CSC + ' -langversion:?', tag='list')
    ctx.cs('ex/09/ovversion', v='7.3', expect=1)

    # 프로젝트 단위 -nullable: 네 값과 C# 7.3 에서의 거절
    ctx.cs('ex/09/nrtproj', v='7.3', expect=1)
    for val in ('disable', 'warnings', 'annotations'):
        ctx.cs('ex/09/nrtproj', flags='-nullable:' + val, tag=val)
    # #nullable restore 는 프로젝트 값으로 돌아간다
    ctx.cs('ex/09/nrtrestore', flags='-nullable:enable', tag='enable')
    # #pragma warning disable nullable 은 안 먹고, 명령 줄은 먹는다
    ctx.cs('ex/09/nrtpragma', flags='-nowarn:nullable', tag='nowarn')
    ctx.cs('ex/09/nrtpragma', flags='-warnaserror:nullable', tag='wae',
           expect=1)
    ctx.cs('ex/09/nrtpragma', v='14.0')
    # 제약 없는 T 의 default — 8.0 과 9.0 의 경고가 다르다 (나)
    ctx.cs('ex/09/nrtgeneric', v='9.0')
