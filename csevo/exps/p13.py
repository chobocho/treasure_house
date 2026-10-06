# -*- coding: utf-8 -*-
"""13부 앞 조각 — C# 12 개관(게이트 여덟 · .NET 8 · 같이 온 형식 ·
경고 웨이브 8 · .NET 8 의 깨지는 변경 둘), 기본 생성자, 모든 형식의
using 별칭의 증거. 예제는 ex/13/ 아래의 ov*·pc*·ps*·al* 이다(p13b·
p13c 는 같은 ex/13 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 11.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다
(둘이면 실행마다 순서가 바뀔 수 있어서). 선언에서 난 오류는 몸체의
오류를 가리므로 거절 시연은 기능 하나씩이다."""
import os
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/13/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion(12.0)으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovgates2', 'ovruntime', 'ovwave8', 'ovdynref',
    'ovasyncusing',
    # 2장 — 기본 생성자
    'pcbasic', 'pcscope', 'pcrecord', 'pccapture', 'pcfields',
    'pcorder',
    'pcdouble', 'pcmutable', 'pcchain', 'pcnoctor',
    'pcbase', 'pcshadow', 'pclookup', 'pcdi', 'pcvalid', 'pclambda',
    'pcref', 'pcattr', 'pcpartial', 'pcunread', 'pcsemi', 'pcvs',
    'psbasic', 'psreadonly', 'psref', 'psthis',
    # 3장 — 형식 별칭
    'albasic', 'altuple', 'alkinds', 'alunsafe', 'alnull', 'algeneric',
    'alglobal', 'aldynamic', 'alscope', 'alext',
    # 뒤 버전 — C# 14 의 csproj
    'pcpartial14',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['alnoflag']

# C# 11.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED11 = ['ovgates', 'ovgates2', 'pcbasic', 'psbasic', 'albasic']

# 다른 버전으로 — (예제, 언어 버전, 종료 코드)
OTHER = [('ovasyncusing', '11.0', 0), ('ovasyncusing', '8.0', 0),
         ('pcsemi', '11.0', 1),
         ('aldynamic', '11.0', 0), ('aldynamic', '4', 0),
         ('aldynamic', '3', 1),
         ('pcpartial14', '12.0', 1), ('alext', '14.0', 1)]

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전 또는 None, 종료 코드)
DEFINES = [
    ('ovdynref', 'BAD', None, 1), ('ovdynref', 'BAD', '11.0', 1),
    ('ovdynref', 'BAD', '7.3', 1),
    ('pcscope', 'CTOR', None, 1), ('pcchain', 'BAD', None, 1),
    ('pcnoctor', 'BAD', None, 1), ('pcref', 'CAP', None, 1),
    ('pcattr', 'FIELD', None, 0), ('pcpartial', 'BAD', None, 1),
    ('pcunread', 'UNREAD', None, 0),
    ('psreadonly', 'BAD', None, 1), ('psreadonly', 'BAD2', None, 1),
    ('psref', 'BAD', None, 1),
    ('altuple', 'OVER', None, 1), ('alunsafe', 'NOUNSAFE', None, 1),
    ('alnull', 'BAD', None, 1), ('algeneric', 'OPEN', None, 1),
    ('algeneric', 'UNBOUND', None, 1), ('alscope', 'SHORT', None, 1),
    ('alglobal', 'CHAIN', None, 1),
]

# 그 밖의 컴파일러 옵션을 붙인 캡처 — (예제, 옵션, 꼬리표, 종료 코드)
FLAGS = []

# 경고 수준을 올린 캡처 — (예제, 수준, 언어 버전 또는 None)
WAVE = [('ovwave8', 8, None), ('ovwave8', 8, '11.0'),
        ('ovwave8', 7, None)]

# 한 줄이 200칸을 넘어 캡처로 못 싣는 거절 — (예제, 기호, 오류 번호)
LONGLINE = []

# 경고 한 줄이 200칸을 넘는 EXPECT_WARN 예제 — (예제, 경고 번호).
# 캡처는 -nowarn 으로 그 경고만 끄고 돌린 것이고, 실험이 그냥 컴파일한
# 출력에 그 경고가 있고 종료 코드가 0 인지 따로 확인한다
LONGWARN = [('pcdoublebase', 'CS9107')]


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
    for d in RUN:
        ctx.cs(EX + d)
    for d in FAIL:
        ctx.cs(EX + d, expect=1)
    for d in GATED11:
        ctx.cs(EX + d, v='11.0', expect=1)
    for d, v, code in OTHER:
        ctx.cs(EX + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        ctx.cs(EX + d, v=v, flags='-define:' + sym, tag=sym.lower(),
               expect=code)
    for d, flags, tag, code in FLAGS:
        ctx.cs(EX + d, flags=flags, tag=tag, expect=code)
    for d, lvl, v in WAVE:
        ctx.cs(EX + d, v=v, flags='-warn:%d' % lvl, tag='w%d' % lvl)
    for d, warn in LONGWARN:
        ctx.cs(EX + d, flags='-nowarn:' + warn[2:], tag='nowarn')
        code, text = csver.execute(os.path.join(csver.BASE, EX + d),
                                   'csrun', name='p13-check-' + d)
        if code != 0 or 'warning ' + warn not in text:
            raise RuntimeError('[p13] %s 는 경고 %s 를 내고 돌아야 '
                               '한다\n%s' % (d, warn, text))
    for d, sym, err in LONGLINE:
        code, text = csver.execute(os.path.join(csver.BASE, EX + d),
                                   'csrun', flags='-define:' + sym,
                                   name='p13-check-' + d)
        if code != 1 or 'error ' + err not in text:
            raise RuntimeError('[p13] %s(-define:%s) 는 %s 이어야 '
                               '한다\n%s' % (d, sym, err, text))
