# -*- coding: utf-8 -*-
"""10부 가운데 조각 — C# 9.0 의 최상위 문(3장), 패턴 3(4장),
nint·함수 포인터·SkipLocalsInit(5장)의 증거.
예제는 ex/10/ 아래의 top*·pat*·nint*·fp*·sli* 이다.
(레코드와 init 은 p10, 다듬기·모듈 초기화자는 p10c 가 같은 ex/10 에
다른 이름으로 쓴다)"""
import re
import subprocess

# 3장 — 그대로 돌아가는 예제(csproj 의 LangVersion 으로)
RUN3 = [
    'tophello', 'topentry', 'topsig', 'topargs', 'toplocfn', 'toporder',
    'topscope', 'toppartial', 'topglobal10', 'topns',
]

# 4장 — 그대로 돌아가는 예제
RUN4 = [
    'patrel', 'patreltype', 'patandor', 'patparen', 'patnotnull',
    'patnotprec', 'pattype', 'patbreak', 'patvars', 'patnarrow', 'patexh',
    'patsubsume', 'patdag', 'patlater', 'patrelenum', 'patwhen8',
]

# 5장 — 그대로 돌아가는 예제
RUN5 = [
    'nintbasic', 'ninttype', 'nintptr', 'nintconst', 'nintchecked',
    'nintdyn', 'nintover', 'fpbasic', 'fpil', 'fpalloc', 'fpconv', 'fpbad',
    'fpreflect', 'slibasic', 'sliscope', 'sligarbage', 'perfrt',
    'nintlater11',
]

# 4장 — C# 8.0 으로 내린 거절. 표가 캡처에서 컴파일러가 댄 기능 이름을
# 뽑는다: (예제, 표에 적을 꼴)
GATED4 = [
    ('patrel', '< 0 => … (관계 패턴만)'),
    ('patnotnull', 'is not null'),
    ('pattype', 'int => … · long or short'),
    ('patandor', '>= \'a\' and <= \'z\' or …'),
    ('patparen', 'not (0 or > -5) · (… and …) or (…)'),
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'toptwo', 'topusing',
]

# #if 기호를 켜서 돌린다 — (예제, -define 기호, tag, 기대 종료 코드)
DEFINE = [
    ('topsig', 'RET', 'ret', 3),
    ('topsig', 'AWAIT', 'await', 0),
    ('topsig', 'AWAIT;RET', 'both', 3),
    ('topargs', 'BAD', 'bad', 1),
    ('topret', 'BAD', 'bad', 1),
    ('toplocfn', 'BAD', 'bad', 1),
    ('toporder', 'BAD', 'bad', 1),
    ('topscope', 'BAD', 'bad', 1),
    ('toppartial', 'BAD', 'bad', 1),
    ('patreltype', 'NAN', 'nan', 1),
    ('patreltype', 'VAR', 'var', 1),
    ('patbreak', 'NOT', 'not', 0),
    ('patbreak', 'OR', 'or', 0),
    ('patbreak', 'AND', 'and', 0),
    ('patrelenum', 'BAD', 'bad', 1),
    ('patvars', 'BAD', 'bad', 1),
    ('patexh', 'BAD', 'bad', -6),
    ('patexh', 'GAP', 'gap', 0),
    ('patsubsume', 'DUP', 'dup', 1),
    ('patsubsume', 'NEVER', 'never', 1),
    ('patsubsume', 'REDUNDANT', 'redundant', 0),
    ('nintconst', 'BAD', 'bad', 1),
    ('nintover', 'OVER', 'over', 1),
    ('nintover', 'ENUM', 'enum', 1),
    ('fpbasic', 'CMP', 'cmp', 0),
    ('fpconv', 'CALL', 'call', 1),
    ('fpconv', 'MIX', 'mix', 1),
    ('fpbad', 'BAD', 'bad', 1),
    ('sliscope', 'MOD', 'mod', 0),
]

# 한 단계 아래 언어 버전으로 내리면 거절 — (예제, 아래 버전)
GATED = [
    ('tophello', '8.0'), ('topglobal10', '9.0'), ('patlater', '10.0'),
    ('nintbasic', '8.0'), ('fpbasic', '8.0'), ('nintlater11', '10.0'),
]

# 같은 소스를 다른 언어 버전으로 — 언어 버전에 묶였는가 (예제, 버전)
OTHERV = [
    ('ninttype', '11.0'), ('nintptr', '8.0'), ('nintptr', '11.0'),
    ('fpalloc', '11.0'), ('slibasic', '8.0'), ('slibasic', '7.3'),
]


def gate_rows(found):
    """C# 8.0 거절 캡처 → 표의 줄. 한 캡처에 기능 이름이 여럿일 수 있다.
    O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error (CS\d+): Feature '([^']+)'", text):
            if m.group(2) not in names:
                names.append(m.group(2))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/10/' + ex, ' · '.join(names), str(count)))
    return rows


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

    def table(self, *args, **kw):
        return self.ctx.table(*args, **kw)


def run(ctx):
    ctx = Retry(ctx)
    ex = lambda d: 'ex/10/' + d
    # ---- 3장 최상위 문
    for d in RUN3:
        ctx.cs(ex(d))
    for d in FAIL:
        ctx.cs(ex(d), expect=1)
    for d, sym, tag, code in DEFINE:
        ctx.cs(ex(d), flags='-define:' + sym, tag=tag, expect=code)
    for d, v in GATED:
        ctx.cs(ex(d), v=v, expect=1)
    ctx.cs(ex('topargs'), cmd='csrun -- red green', tag='args')
    ctx.cs(ex('topret'), expect=2)
    ctx.cs(ex('topret'), cmd='csrun -- x', tag='arg')
    # Main 이 따로 있으면 경고 CS7022, -main: 으로 고르면 그 Main
    ctx.cs(ex('topmain'))
    ctx.cs(ex('topmain'), flags='-main:App', tag='mainsw')
    # C# 10 의 파일 범위 네임스페이스는 최상위 문 뒤에 올 수 없다
    ctx.cs(ex('topns'), v='10.0', flags='-define:FILESCOPED', tag='fs',
           expect=1)
    # 처리하지 않은 예외 — 종료 코드 -6(SIGABRT)
    ctx.cs(ex('toptrace'), expect=-6)
    # ---- 4장 패턴 3
    for d in RUN4:
        ctx.cs(ex(d))
    found = []
    for d, title in GATED4:
        found.append((d, title, ctx.cs(ex(d), v='8.0', expect=1)))
    # not 을 형식 이름으로 쓰던 코드 — 8.0 으로 내려도 새 파서가 읽는다
    ctx.cs(ex('patbreak'), v='8.0', flags='-define:NOT', tag='not',
           expect=1)
    # 제안서가 오류로 하자던 겹친 or — 경고 웨이브를 다 켜도 조용한가
    ctx.cs(ex('patsubsume'), v='14.0', flags='-define:REDUNDANT -warn:9999',
           tag='redundant', expect=0)
    ctx.cs(ex('patnotprec'), v='14.0', flags='-warn:9999', tag='w',
           expect=0)
    ctx.table('p10b_gates8',
              ['패턴의 꼴', '예제', '컴파일러가 댄 기능 이름', '오류 수'],
              gate_rows(found),
              caption='4장의 예제를 -langversion:8.0 으로 컴파일한 캡처에서 '
                      '뽑은 표')
    # ---- 5장 nint · 함수 포인터 · SkipLocalsInit
    for d in RUN5:
        ctx.cs(ex(d))
    for d, v in OTHERV:
        ctx.cs(ex(d), v=v)
    # 최적화한 IL — 디버그 빌드의 nop·br.s 없이
    ctx.cs(ex('fpil'), flags='-optimize+', tag='opt')
    # AllowUnsafeBlocks 를 끄면 [SkipLocalsInit] 은 CS0227
    ctx.cs(ex('slibasic'), flags='-unsafe-', tag='unsafe', expect=1)
