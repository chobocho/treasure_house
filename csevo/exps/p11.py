# -*- coding: utf-8 -*-
"""11부 앞 조각 — C# 10 개관, 구조체와 record struct, global using 과 파일
범위 네임스페이스의 증거. 예제는 ex/11/ 아래의 ov*·iu*·rs*·st*·wi*·gu*·ns*
이다(p11b 는 같은 ex/11 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 9.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이다 — 고의로 깨진 줄을 따로 파일로 떼지
않고 한 슬라이드에 둘을 함께 보이기 위해서다."""
import subprocess

EX = 'ex/11/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion(10.0)으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovruntime', 'iusdk', 'ovwave6',
    # 2장 — record struct
    'rsgate', 'rsmembers', 'rseq', 'rsnan', 'rsbox', 'rshash', 'rsprint',
    'rstuple', 'rsreadonly', 'rsinitprop', 'rsfield', 'rssealed',
    'rswarn', 'rsctor', 'rstrap', 'rsnominal', 'rsarray',
    # 2장 — 구조체의 생성자와 초기화자
    'stctor', 'stdefault', 'stinit', 'stoptional', 'stthis', 'strecord',
    'stgeneric', 'stparam', 'stro',
    # 2장 — with
    'wistruct', 'wiref', 'wiorder', 'wiro', 'wianon', 'wigeneric',
    'wituple', 'winested',
    # 3장 — global using · 파일 범위 네임스페이스
    'gubasic', 'guall', 'guscope', 'guambig', 'guext', 'guhide',
    'nsbasic', 'nsrules', 'nsusing', 'nsil', 'nsnested', 'nsglobal',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['ovpreview', 'rslimits', 'rsref', 'stnoctor', 'stassign',
        'stpublic', 'guorder', 'guinns']

# C# 9.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED9 = ['ovgates', 'rsgate', 'rsfield', 'rssealed', 'stctor', 'stinit',
          'wistruct', 'wianon', 'wituple', 'gubasic', 'nsbasic']

# 뒤 버전에서 — (예제, 언어 버전, 종료 코드)
LATER = [('ovpreview', '11.0', 0), ('stassign', '11.0', 0),
         ('stpublic', '14.0', 1)]

# #if 줄을 켠 캡처 — (예제, 기호, 종료 코드)
DEFINES = [
    ('rseq', 'BAD', 1), ('rsreadonly', 'BAD', 1), ('rsinitprop', 'BAD', 1),
    ('rssealed', 'BAD', 1), ('rswarn', 'BAD', 1), ('rsctor', 'BAD', 1),
    ('rstrap', 'BAD', 1),
    ('strecord', 'R1', 1), ('strecord', 'R5', 1), ('stparam', 'BAD', 1),
    ('wiro', 'BAD', 1), ('wianon', 'BAD', 1), ('wigeneric', 'BAD', 1),
    ('winested', 'BAD', 1),
    ('guscope', 'BAD', 1), ('guscope', 'BAD2', 1),
    ('guambig', 'BAD', 1), ('guext', 'BAD', 1),
    ('nsrules', 'TYPEFIRST', 1), ('nsrules', 'TWICE', 1),
    ('nsrules', 'MIX', 1), ('nsusing', 'BEFORE', 0), ('nsil', 'FS', 0),
    ('nsglobal', 'BAD', 1),
]

# 경고 웨이브 6 — 경고 수준으로 켠다. 9.0 으로 내려도 같은지 본다
WAVE = [('ovwave6', None), ('ovwave6', '9.0')]


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
    for d in FAIL:
        ctx.cs(EX + d, expect=1)
    for d in GATED9:
        ctx.cs(EX + d, v='9.0', expect=1)
    for d, v, code in LATER:
        ctx.cs(EX + d, v=v, expect=code)
    for d, sym, code in DEFINES:
        ctx.cs(EX + d, flags='-define:' + sym, tag=sym.lower(), expect=code)
    for d, v in WAVE:
        ctx.cs(EX + d, v=v, flags='-warn:6', tag='w6')
