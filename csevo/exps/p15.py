# -*- coding: utf-8 -*-
"""15부 앞 조각 — C# 14 개관(게이트 아홉 · .NET 10 · 같이 온 형식 ·
경고 웨이브 10 · .NET 10 의 깨지는 변경)과 확장 멤버(확장 블록 · 확장 속성 ·
정적 확장 멤버 · 확장 연산자)의 증거. 예제는 ex/15/ 아래의 ov*·xm* 이다
(p15b·p15c 는 같은 ex/15 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 13.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다
(둘이면 실행마다 순서가 바뀔 수 있어서). 200칸을 넘는 진단 줄(CS1061·
CS9286)은 캡처에 싣지 못하므로 LONGLINE 이 따로 돌려 확인하고, 문장
전체를 표(tbl_p15_long)로 옮긴다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/15/'
CSC = 'dotnet /usr/lib/dotnet/sdk/10.0.112/Roslyn/bincore/csc.dll'

# 처리기 없이 끝나는 예외의 종료 코드 — 이 기계에서는 -6(SIGABRT)
ABORT = -6

# 그대로 돌아가는 예제 — csproj 의 LangVersion(14.0)으로
RUN = [
    # 1장 — 개관
    'ovgates', 'ovgates2', 'ovnomsg', 'ovruntime', 'ovbcl', 'ovwave',
    'ovbrkenum', 'ovbrkfix', 'ovbrkuref',
    # 2장 — 확장 멤버
    'xmbasic', 'xmsame', 'xmport', 'xmmeta', 'xmskel', 'xmprop',
    'xmstate', 'xmvalue', 'xmref', 'xmienum', 'xmgeneric', 'xmuse',
    'xmstatic', 'xmstmeta', 'xmresolve', 'xmscope', 'xmambig', 'xmdup',
    'xmusing', 'xmiface', 'xmop', 'xmopcomp', 'xmoprules', 'xmexpr',
    'xmkw', 'xmindexer', 'xmreal', 'xmgroup', 'xmscoping', 'xmcontainer',
    'xmnull', 'xmorp', 'xmlinq', 'xmlogic', 'xmenum', 'xmasync',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 말이 증거다
FAIL = ['ovnet10']

# C# 13.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED13 = ['ovgates', 'ovgates2', 'ovnomsg', 'xmbasic', 'xmparse']

# 다른 버전으로 — (예제, 언어 버전, 종료 코드)
OTHER = [
    ('xmparse', '14.0', 0),           # 이 예제의 csproj 도 14.0 — 짝을 맞춘다
    ('xmkw', '13.0', 0),              # @extension 은 두 버전 모두 된다
    ('ovbrkenum', '7.3', 0),          # 컴파일러의 수정 — 언어 버전과 무관
    ('ovbrkuref', '7.3', 0),          # net10 참조로는 옛 ref 규칙이 아니다
]

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전 또는 None, 종료 코드)
DEFINES = [
    # 1장
    ('ovbrkfix', 'OBS', None, 0), ('ovbrkfix', 'OBS', '13.0', 0),
    ('ovbrkfix', 'PTR', None, 1), ('ovbrkfix', 'PTR', '13.0', 1),
    # 2장 — 블록과 메타데이터
    ('xmparse', 'GEN', '13.0', 1), ('xmparse', 'EMPTY', '13.0', 1),
    ('xmport', 'NEW', None, 0),
    # 2장 — 속성과 수신자
    ('xmstate', 'AUTO', None, 1), ('xmstate', 'FIELD', None, 1),
    ('xmstate', 'KW', None, 1), ('xmstate', 'INIT', None, 1),
    ('xmref', 'CLASS', None, 1), ('xmref', 'GENERIC', None, 1),
    ('xmref', 'RVALUE', None, 1),
    ('xmgeneric', 'INFER', None, 1),
    ('xmscoping', 'STATIC', None, 1), ('xmscoping', 'REUSE', None, 1),
    ('xmscoping', 'TPARAM', None, 1),
    ('xmcontainer', 'NONSTATIC', None, 1), ('xmcontainer', 'GENERIC', None, 1),
    ('xmcontainer', 'NESTED', None, 1), ('xmcontainer', 'VIRTUAL', None, 1),
    ('xmnull', 'WARN', None, ABORT),
    ('xmuse', 'NAMEOF', None, 1), ('xmuse', 'DYN', None, ABORT),
    # 2장 — 정적 멤버와 해석 규칙
    ('xmstatic', 'INST', None, 1), ('xmstatic', 'VAR', None, 1),
    ('xmambig', 'A1', None, 1), ('xmambig', 'A2', None, 1),
    ('xmdup', 'DUP1', None, 1), ('xmdup', 'DUP2', None, 1),
    ('xmusing', 'BAD', None, 1),
    ('xmorp', 'NOORP', None, 0),
    # 2장 — 연산자
    ('xmop', 'STR', None, 1),
    ('xmopcomp', 'VALUE', None, 1), ('xmopcomp', 'SB', None, 1),
    ('xmoprules', 'UNRELATED', None, 1), ('xmoprules', 'CONV', None, 1),
    ('xmoprules', 'INST', None, 1), ('xmoprules', 'PAIR', None, 1),
    ('xmexpr', 'PROP', None, 1),
    # 2장 — 키워드와 C# 14 에 없는 것
    ('xmkw', 'CTOR', None, 1), ('xmkw', 'CTOR', '13.0', 0),
    ('xmkw', 'RET', None, 1), ('xmkw', 'RET', '13.0', 0),
    ('xmkw', 'NAME', None, 1), ('xmkw', 'NAME', '13.0', 0),
    ('xmindexer', 'INDEXER', None, 1),
    ('xmindexer', 'INDEXER', 'preview', 1),
    ('xmindexer', 'EVENT', None, 1), ('xmindexer', 'CTOR', None, 1),
]

# 경고 수준을 올린 캡처 — (예제, 수준, 언어 버전 또는 None, 종료 코드)
WAVE = [('ovwave', 10, None, 0), ('ovwave', 10, '11.0', 0),
        ('ovwave', 10, '10.0', 1)]

# 200칸을 넘는 진단 — 종료 코드와 들어 있어야 할 것을 확인하고, 진단
# 줄의 번호와 문장을 표로 옮긴다.
# (예제, 언어 버전, 플래그, 종료 코드, 있어야 할 것들, 표에 쓸 무엇)
LONGLINE = [
    ('xmgeneric', '14.0', '-define:ONE', 1, ['error CS1061', "'To'"],
     '-define:ONE — 300.To<long>(): 메서드의 R 만 적음'),
    ('xmgeneric', '14.0', '-define:STR', 1, ['error CS9286', "'IsZero'"],
     '-define:STR — 제약(INumber)을 못 맞춘 수신자 string'),
    ('xmambig', '14.0', '-define:A3', 1, ['error CS9286', "'P'"],
     '-define:A3 — 두 클래스의 같은 확장 속성 x.P'),
    ('xmiface', '14.0', '-define:DIM', 1, ['error CS1061', "'Kind'"],
     '-define:DIM — 기본 구현 멤버 Kind 를 클래스 변수로'),
]

# 2장의 거절을 모은 표 (1) — 블록 · 수신자 · 속성. (예제, 꼬리표, 무엇을 했나)
DIAG2A = [
    ('xmbasic', 'v13', 'C# 13.0 에서 멤버가 든 확장 블록'),
    ('xmparse', 'gen13.0', 'C# 13.0 에서 제네릭 확장 블록'),
    ('xmstate', 'auto', '자동 속성 { get; set; }'),
    ('xmstate', 'field', '필드'),
    ('xmstate', 'kw', 'field 키워드를 쓴 속성'),
    ('xmstate', 'init', 'init 접근자'),
    ('xmref', 'class', '참조 형식(string)에 ref 수신자'),
    ('xmref', 'generic', '제약 없는 T 에 ref 수신자'),
    ('xmref', 'rvalue', 'ref 수신자에 값(new Big())'),
    ('xmgeneric', 'infer', '블록의 T 를 아무 데서도 안 씀'),
    ('xmscoping', 'static', '정적 멤버에서 수신자 ts 를 씀'),
    ('xmscoping', 'reuse', '멤버의 매개변수 이름이 ts'),
    ('xmscoping', 'tparam', '멤버의 형식 매개변수 이름이 T'),
    ('xmcontainer', 'nonstatic', 'static 이 아닌 클래스 안의 블록'),
    ('xmcontainer', 'generic', '제네릭 정적 클래스 안의 블록'),
    ('xmcontainer', 'nested', '중첩된 정적 클래스 안의 블록'),
    ('xmcontainer', 'virtual', '블록 멤버에 virtual'),
    ('xmuse', 'nameof', 'nameof(none.IsBlank)'),
]

# 2장의 거절을 모은 표 (2) — 정적 멤버 · 해석 · 연산자 · 키워드
DIAG2B = [
    ('xmstatic', 'inst', '이름 없는 수신자 블록의 인스턴스 멤버'),
    ('xmstatic', 'var', '정적 확장 멤버를 인스턴스로'),
    ('xmambig', 'a1', '두 클래스의 같은 정적 확장 M()'),
    ('xmambig', 'a2', '두 클래스의 같은 확장 메서드 x.M2()'),
    ('xmdup', 'dup1', 'this 꼴과 블록에 같은 First()'),
    ('xmdup', 'dup2', '두 블록에 같은 이름 Last'),
    ('xmusing', 'bad', 'using static 으로 인스턴스 확장을 Who(5)'),
    ('xmop', 'str', '제약을 못 맞춘 string[] * string'),
    ('xmopcomp', 'value', '값 형식 수신자(ref 없음)의 -='),
    ('xmopcomp', 'sb', 'StringBuilder += "b"'),
    ('xmoprules', 'unrelated', '확장 형식이 없는 int * int'),
    ('xmoprules', 'conv', '변환 연산자 implicit operator'),
    ('xmoprules', 'inst', 'static 없는 operator +'),
    ('xmoprules', 'pair', '== 만 있고 != 없음'),
    ('xmexpr', 'prop', '식 트리 안의 확장 속성'),
    ('xmkw', 'name', '형식 매개변수 이름 extension'),
    ('xmindexer', 'indexer', '확장 인덱서 this[Index]'),
    ('xmindexer', 'event', '확장 이벤트'),
    ('xmindexer', 'ctor', '확장 블록 안의 생성자'),
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

    def table(self, *args, **kw):
        return self.ctx.table(*args, **kw)


def execute(src, v, flags, name):
    """캡처로 남기지 않는 실행 — 시간 초과만 두 번까지 다시."""
    for attempt in range(3):
        try:
            return csver.execute(src, 'csrun', v=v, flags=flags, name=name)
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise


def first_diag(text):
    """첫 오류(없으면 첫 경고)의 (번호, 문장)."""
    m = (re.search(r'error (CS\d+): (.*)', text)
         or re.search(r'warning (CS\d+): (.*)', text))
    return m.groups() if m else None


def diag_rows(spec, found):
    """거절 캡처 → 표의 줄(무엇을 했나, 예제, 진단 번호, 문장의 앞부분).
    O(캡처 길이)."""
    rows = []
    for ex, key, what in spec:
        got = first_diag(found[(ex, key)])
        if not got:
            raise RuntimeError('[p15] %s(%s) 에 진단 줄이 없다' % (ex, key))
        code, msg = got
        if len(msg) > 60:      # 낱말 경계에서 자른다
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, EX + ex, code, msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    found = {}
    for d in RUN:
        found[(d, 'run')] = ctx.cs(EX + d)
    for d in FAIL:
        found[(d, 'fail')] = ctx.cs(EX + d, expect=1)
    ctx.cs(EX + 'ovnet10', cmd=CSC + ' -langversion:?', tag='list')
    for d in GATED13:
        found[(d, 'v13')] = ctx.cs(EX + d, v='13.0', expect=1)
    for d, v, code in OTHER:
        found[(d, v)] = ctx.cs(EX + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        key = sym.lower() + (v or '')
        found[(d, key)] = ctx.cs(EX + d, v=v, flags='-define:' + sym,
                                 tag=sym.lower(), expect=code)
    for d, lvl, v, code in WAVE:
        ctx.cs(EX + d, v=v, flags='-warn:%d' % lvl, tag='w%d' % lvl,
               expect=code)
    long_rows = []
    for d, v, fl, want, needles, what in LONGLINE:
        src = os.path.join(csver.BASE, EX + d)
        code, text = execute(src, v, fl, 'p15-check-%s-%s' % (d, fl[-3:]))
        if code != want or any(x not in text for x in needles):
            raise RuntimeError('[p15] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, fl, want, ' / '.join(needles), text))
        for m in re.finditer(r'(error|warning) (CS\d+): (.*)', text):
            long_rows.append((what, EX + d, m.group(1) + ' ' + m.group(2),
                              m.group(3)))
    ctx.table('p15_long', ['무엇을', '예제', '진단', '컴파일러의 문장 전체'],
              long_rows, caption='200칸이 넘어 캡처에 싣지 못한 진단 — '
              '실험 묶음이 돌려 뽑은 문장')
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    ctx.table('p15_diag2a', head, diag_rows(DIAG2A, found),
              caption='2장의 거절 캡처에서 뽑은 표 (1)')
    ctx.table('p15_diag2b', head, diag_rows(DIAG2B, found),
              caption='2장의 거절 캡처에서 뽑은 표 (2)')
