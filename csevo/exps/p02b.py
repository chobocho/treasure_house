# -*- coding: utf-8 -*-
"""2부 뒤 조각 — C# 1.0 의 멤버·상속·대리자·이벤트·예외·문장, 그리고 C# 1.2.
예제는 전부 -langversion:1 로 컴파일한다(그것이 C# 1 문법이라는 증거다).
Roslyn 에는 1.2 라는 언어 버전이 없어서 C# 1.2 의 변화도 1 로 컴파일한다.

-parallel- 은 진단이 둘 이상의 형식에서 나오는 거절 예제에만 붙인다.
csc 는 기본으로 형식들을 나란히 컴파일해서, 형식이 다른 진단끼리는 찍히는
순서가 실행마다 바뀐다(2026-10-01 에 sealedfail 을 여섯 번 돌려 두 가지
순서를 봤다). -parallel- 이면 소스 순서로 고정된다.

종료 코드: 처리하지 않은 예외는 SIGABRT 라 -6, 컴파일 거절은 1."""

BOOM = -6       # 처리하지 않은 예외 — 런타임이 abort 한다
REFUSED = 1     # 컴파일러의 거절
SEQ = '-parallel-'  # 진단 순서를 소스 순서로 고정


def run(ctx):
    # 4장 — 클래스와 상속
    ctx.cs('ex/02/virt')
    ctx.cs('ex/02/hidenew')
    ctx.cs('ex/02/hidewarn')                        # EXPECT_WARN: CS0108 · CS0114
    ctx.cs('ex/02/overridefail', expect=REFUSED)
    ctx.cs('ex/02/sealedfail', flags=SEQ, expect=REFUSED)
    ctx.cs('ex/02/abstract')
    ctx.cs('ex/02/abstractfail', flags=SEQ, expect=REFUSED)
    ctx.cs('ex/02/abstractnew', expect=REFUSED)
    ctx.cs('ex/02/basecall')
    ctx.cs('ex/02/ctorchain')
    ctx.cs('ex/02/ctorvirt')
    ctx.cs('ex/02/defctor', flags=SEQ, expect=REFUSED)
    ctx.cs('ex/02/cctor')
    ctx.cs('ex/02/cctorfail')
    ctx.cs('ex/02/access')
    ctx.cs('ex/02/protfail', expect=REFUSED)
    ctx.cs('ex/02/nested')
    ctx.cs('ex/02/objover')
    ctx.cs('ex/02/eqhash', flags=SEQ)               # EXPECT_WARN: CS0659 · CS0660 · CS0661
    ctx.cs('ex/02/finalizer')
    ctx.cs('ex/02/finalfail', flags=SEQ, expect=REFUSED)

    # 5장 — 인터페이스·속성·인덱서
    ctx.cs('ex/02/iface')
    ctx.cs('ex/02/ifacefail', flags=SEQ, expect=REFUSED)
    ctx.cs('ex/02/explicit')
    ctx.cs('ex/02/explicitfail')
    ctx.cs('ex/02/explicitmod', expect=REFUSED)
    ctx.cs('ex/02/reimpl')
    ctx.cs('ex/02/ifacecast', expect=BOOM)
    ctx.cs('ex/02/ifacesealed', expect=REFUSED)
    ctx.cs('ex/02/prop')
    ctx.cs('ex/02/propir')
    ctx.cs('ex/02/propname', expect=REFUSED)
    ctx.cs('ex/02/propref', expect=REFUSED)
    ctx.cs('ex/02/indexer')
    ctx.cs('ex/02/indexername')
    ctx.cs('ex/02/staticmem')
    ctx.cs('ex/02/staticfail', expect=REFUSED)

    # 6장 — 대리자와 이벤트
    ctx.cs('ex/02/delegate')
    ctx.cs('ex/02/delclass')
    ctx.cs('ex/02/delbegin')
    ctx.cs('ex/02/multicast')
    ctx.cs('ex/02/mcreturn')
    ctx.cs('ex/02/mcexcept')
    ctx.cs('ex/02/delremove')
    ctx.cs('ex/02/delnull', expect=BOOM)
    ctx.cs('ex/02/event')
    ctx.cs('ex/02/eventfail', expect=REFUSED)
    ctx.cs('ex/02/eventfield')
    ctx.cs('ex/02/eventacc')
    ctx.cs('ex/02/eventargs')
    ctx.cs('ex/02/eventimmut')

    # 7장 — 예외와 자원
    ctx.cs('ex/02/trycatch')
    ctx.cs('ex/02/catchorder', expect=REFUSED)
    ctx.cs('ex/02/rethrow')
    ctx.cs('ex/02/finallyret')
    ctx.cs('ex/02/finallyfail', expect=REFUSED)
    ctx.cs('ex/02/finallyexc')
    ctx.cs('ex/02/throwfail', expect=REFUSED)
    ctx.cs('ex/02/excwrap')
    ctx.cs('ex/02/nothrows', expect=BOOM)
    ctx.cs('ex/02/throwsfail', expect=REFUSED)
    ctx.cs('ex/02/usingstmt')
    ctx.cs('ex/02/usinglower')
    ctx.cs('ex/02/usingfail', expect=REFUSED)
    ctx.cs('ex/02/lockstmt')
    ctx.cs('ex/02/lockfail', expect=REFUSED)

    # 8장 — 문장과 그 밖의 C# 1
    ctx.cs('ex/02/foreachex')
    ctx.cs('ex/02/fereadonly', expect=REFUSED)
    ctx.cs('ex/02/foreachpat')
    ctx.cs('ex/02/fecast', expect=BOOM)
    ctx.cs('ex/02/gotocase')
    ctx.cs('ex/02/attr')
    ctx.cs('ex/02/attrfail', flags=SEQ, expect=REFUSED)
    ctx.cs('ex/02/modattr')                         # EXPECT_WARN: CS1645
    ctx.cs('ex/02/modattr', v='2')                  # C# 2 부터는 경고도 없다
    ctx.cs('ex/02/conditional')
    ctx.cs('ex/02/conditional', flags='-define:TRACE_ON', tag='trace')
    ctx.cs('ex/02/preproc')
    ctx.cs('ex/02/preproc', flags='-define:NIGHTLY', tag='nightly')
    ctx.cs('ex/02/warnerr')                         # EXPECT_WARN: CS1030
    ctx.cs('ex/02/warnerr', flags='-define:SHIP', tag='ship',
           expect=REFUSED)
    ctx.cs('ex/02/linedir')                         # EXPECT_WARN: CS0168 둘
    ctx.cs('ex/02/xmldoc')
    ctx.cs('ex/02/xmldoc', flags='-doc:bin/doc.xml', tag='doc')
    ctx.cs('ex/02/unsafeptr')
    ctx.cs('ex/02/unsafeptr', flags='-unsafe-', tag='nounsafe',
           expect=REFUSED)
    ctx.cs('ex/02/stackalloc')
    ctx.cs('ex/02/fixedstr')                        # csproj 가 7.3
    ctx.cs('ex/02/fixedstr', v='1', expect=REFUSED)
    ctx.cs('ex/02/nsalias')
    ctx.cs('ex/02/pinvoke')
    ctx.cs('ex/02/mainsig', expect=REFUSED)
    ctx.cs('ex/02/mainsig', flags='-main:Check', cmd='csrun -- one two',
           tag='check')
    ctx.cs('ex/02/mainsig', flags='-main:Check', cmd='csrun -- one',
           tag='check1', expect=2)

    # 9장 — C# 1.2
    ctx.cs('ex/02/fedispose')
    ctx.cs('ex/02/fedispose', v='1.2', expect=REFUSED)  # 1.2 라는 언어 버전은 없다
    ctx.cs('ex/02/fedesugar')
    ctx.cs('ex/02/fepattern')
    ctx.cs('ex/02/feyield')                         # csproj 가 2 — 반복기
    ctx.cs('ex/02/feyield', v='1', expect=REFUSED)
    ctx.cs('ex/02/feruntime')
