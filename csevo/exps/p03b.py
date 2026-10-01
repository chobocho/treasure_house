# -*- coding: utf-8 -*-
"""3부 뒤 조각 — C# 2.0 의 익명 메서드·대리자·partial·static class·접근자·
작은 게이트들의 증거."""

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 별칭 Con 을 붙여 참조할 어셈블리 — extern alias 예제가 쓴다
CON = ('-r:Con=/usr/lib/dotnet/packs/Microsoft.NETCore.App.Ref/10.0.12/'
       'ref/net10.0/System.Console.dll')

# 오류가 여러 형식·파일에 흩어진 예제 — 병렬 컴파일에서는 진단의 차례가 실행마다
# 바뀌었다(staticbad 를 여섯 번 돌려 네 가지 차례). -parallel- 로 한 줄로 세운다
SEQ = '-parallel-'
PAR = ['partialbad', 'partialgeneric', 'staticbad', 'accbad', 'fixedbad',
       'capturebad']

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 5장 — 익명 메서드와 대리자
    'anonoutbad', 'anonambig', 'anonsig', 'anonbreak', 'anontype',
    'capturebad', 'anonyield', 'anonrecbad', 'mgambig', 'mgvalue',
    'mgvarbad', 'anonstaticbad',
    # 6장 — partial·static class·접근자·별칭
    'partialdup', 'partialbad', 'partialgeneric',
    'staticbad', 'staticuse', 'staticext', 'accbad', 'acclookup',
    'accoverride', 'globalbad', 'externalias',
    # 7장 — 그 밖의 C# 2.0
    'fixedbad',
]

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 5장
    'anonc1', 'anon', 'anonforms', 'anonreturn', 'closure', 'closureshare',
    'closureclass', 'closuretarget', 'closuredesugar', 'closurenest',
    'loopinst', 'forcapture', 'forfix', 'lifetime', 'scopeshare',
    'capturevalue', 'structthis', 'anongeneric', 'anoniter', 'anonrec', 'unsub',
    'delegeq', 'reentry', 'mgroup', 'mginfer', 'mgtarget', 'mgoverload',
    'mgvariance', 'mgevents', 'mgvarout', 'mgcache', 'anonbcl', 'anonsort',
    'foreachmod', 'anoninfer', 'anonlambda', 'anononly', 'anonstatic',
    'anonasync',
    # 6장
    'partial', 'partialmerge', 'partialorder', 'partialns', 'partialkinds',
    'partialattrs', 'partialident', 'partialmethod', 'partialprop',
    'staticc1', 'staticcls', 'staticmeta', 'usingstatic', 'accc1',
    'accessor', 'accindexer', 'accinterface', 'autoprop', 'initsetter',
    'globalns', 'aliasq',
    # 7장
    'pragmawarn', 'pragma', 'pragmascope', 'pragmafile', 'pragmachecksum',
    'fixedwhy', 'fixedbuf', 'fixedoverrun', 'fixed73', 'inlinearr',
    'wrapcode',
]


def run(ctx):
    for d in RUN:
        ctx.cs('ex/03/' + d)
    for d in FAIL:
        ctx.cs('ex/03/' + d, flags=SEQ if d in PAR else None, expect=1)
    # 익명 메서드 안에서 터진 예외 — 스택 트레이스의 생성된 이름이 증거
    ctx.cs('ex/03/anontrace', expect=ABORT)

    # 언어 버전 짝 (가) — C# 1 로 내리면 컴파일러가 거절한다
    ctx.cs('ex/03/anon', v='1', expect=1)          # anonymous methods
    ctx.cs('ex/03/partial', v='1', flags=SEQ, expect=1)       # partial types
    ctx.cs('ex/03/staticcls', v='1', expect=1)     # static classes
    ctx.cs('ex/03/accessor', v='1', expect=1)      # access modifiers on properties
    ctx.cs('ex/03/globalns', v='1', expect=1)      # namespace alias qualifier
    ctx.cs('ex/03/externalias', flags=CON, tag='ref')            # 별칭이 있으면 돈다
    ctx.cs('ex/03/externalias', v='1', flags=CON, tag='ref', expect=1)  # extern alias
    ctx.cs('ex/03/pragma', v='1', expect=1)        # #pragma
    ctx.cs('ex/03/fixedbuf', v='1', expect=1)      # fixed size buffers

    # 게이트가 없는 것 — 버전 기록은 C# 2.0 으로 적지만 C# 1 로도 컴파일된다
    ctx.cs('ex/03/mgroup', v='1')                  # 메서드 그룹 변환
    ctx.cs('ex/03/mgvariance', v='1')              # 메서드 그룹의 공변·반공변
    ctx.cs('ex/03/partialident', v='14.0')         # partial 은 문맥 키워드

    # 경고를 오류로 — #pragma 로 끈 경고는 오류도 되지 않는다
    ctx.cs('ex/03/pragmawarn', flags='-warnaserror', tag='wae', expect=1)
    ctx.cs('ex/03/pragma', flags='-warnaserror', tag='wae')

    # 지금도 같은 것
    ctx.cs('ex/03/forcapture', v='14.0')           # for 변수는 하나뿐
    ctx.cs('ex/03/anontype', v='14.0', expect=1)   # 오늘의 진단은 CS8917

    # 버전에 묶인 동작 (나) — C# 11 부터 메서드 그룹 변환의 대리자를 캐시한다
    ctx.cs('ex/03/mgcache', v='10.0')
    ctx.cs('ex/03/mgcache', v='11.0')

    # 뒤 버전과의 맞물림
    ctx.cs('ex/03/anonlambda', v='2', expect=1)    # lambda expression (C# 3)
    ctx.cs('ex/03/mgvarout', v='3', expect=1)      # type variance (C# 4)
    ctx.cs('ex/03/anonasync', v='4', expect=1)     # async function (C# 5)
    ctx.cs('ex/03/anonstatic', v='8.0', expect=1)  # static anonymous function (C# 9)
    ctx.cs('ex/03/partialmethod', v='2', flags=SEQ, expect=1) # partial method (C# 3)
    ctx.cs('ex/03/partialprop', v='13.0', flags=SEQ, expect=1)  # partial 생성자 (C# 14)
    ctx.cs('ex/03/usingstatic', v='5', expect=1)   # using static (C# 6)
    ctx.cs('ex/03/autoprop', v='2', expect=1)      # 자동 속성 (C# 3)
    ctx.cs('ex/03/initsetter', v='8.0', expect=1)  # init (C# 9)
    ctx.cs('ex/03/fixed73', v='7.2', expect=1)     # indexing movable fixed buffers
    ctx.cs('ex/03/inlinearr', v='11.0', expect=1)  # inline arrays (C# 12)
