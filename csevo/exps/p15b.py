# -*- coding: utf-8 -*-
"""15부 가운데 조각 — C# 14 의 field 키워드(3장), 암묵적 Span 변환(4장),
null 조건 대입(5장)의 증거. 예제는 ex/15/ 아래의 fk*·sp*·na* 이다(p15·
p15c 는 같은 ex/15 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 13.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다.
200칸을 넘는 진단 줄(CS9258·CS9264 등)은 캡처에 싣지 못하므로, 경고를
끈 캡처를 싣고 경고 자체는 LONGLINE 이 따로 확인한 뒤 문장 전체를 표
(tbl_p15b_long)로 옮긴다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/15/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 3장 — field 키워드
    'fkbasic', 'fkmeta', 'fkforms', 'fkinit', 'fkctor', 'fkinitacc',
    'fknull', 'fknullset', 'fkattr', 'fkwhere', 'fkcapture', 'fkstatic',
    'fkstruct', 'fkwarn', 'fkover', 'fkhand', 'fkbreak',
    # 4장 — 암묵적 Span 변환
    'spbasic', 'spconv', 'spcov', 'spinfer', 'spover', 'spcast',
    'spcovarr', 'spambig', 'sprev', 'splookup', 'spudc', 'spcompose',
    'spetree', 'spmgroup', 'spalloc', 'spbcl', 'spblog',
    # 5장 — null 조건 대입
    'nabasic', 'naindex', 'nacompound', 'natype', 'nachain', 'naevent',
    'nanot',
]

# 처리하지 않은 예외로 끝나는 것 — (예제, 종료 코드)
CRASH = []

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['spspan']

# C# 13.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED13 = ['fkbasic', 'spinfer', 'spcov', 'nabasic']

# 다른 버전으로 — (예제, 언어 버전, 기호 또는 None, 종료 코드)
OTHER = [
    ('fknullset', '13.0', None, 1),   # body-only 접근자 — CS0103
    ('fkwhere', '13.0', None, 0),     # 키워드가 아닌 자리 — 13.0 도 같다
    # 4장 — 같은 소스가 C# 13.0 에서는 다른 판을 고르거나 통과한다
    ('spconv', '13.0', None, 0),      # 넷은 사용자 정의 연산자로 통과
    ('spconv', '13.0', 'COV', 1),
    ('spover', '13.0', None, 0),
    ('spover', '13.0', 'AMBIG', 1),
    ('spcast', '13.0', None, 0),
    ('spcast', '13.0', 'OLD', 0),
    ('spcovarr', '13.0', None, 0),
    ('spambig', '13.0', 'OLD', 0),
    ('sprev', '13.0', None, 0),
    ('splookup', '13.0', None, 0),
    ('spudc', '13.0', None, 0),
    ('spcompose', '13.0', 'STR', 1),
    ('spetree', '13.0', None, 0),
    ('spmgroup', '13.0', None, 0),
    ('spalloc', '13.0', None, 0),
    ('spspan', '13.0', None, 0),      # C# 13 은 받고 실행에서 던진다
    ('spblog', '13.0', None, 0),      # 블로그의 After 는 C# 13 도 받는다
]

# #if 줄을 켠 캡처 — (예제, 기호, 종료 코드)
DEFINES = [
    ('fkctor', 'BAD', 1),
    ('fkinitacc', 'BAD', 1),
    ('fknullset', 'PARTIAL', 0),
    ('fkcapture', 'NAMEOF', 1),
    ('fkcapture', 'STATIC', 1),
    ('fkstatic', 'IFACE', 1),
    ('fkstruct', 'P2', 1),
    ('fkstruct', 'P4', 1),
    ('fkwarn', 'SETONLY', 1),
    ('fkover', 'HALF', 1),
    ('fkhand', 'RESET', 1),
    ('fkhand', 'REF', 1),
    # 4장
    ('spconv', 'COV', 0),
    ('spover', 'AMBIG', 0),
    ('spinfer', 'MIXED', 1),
    ('spcast', 'OLD', 1),
    ('spcovarr', 'RO', 0),
    ('spambig', 'OLD', 1),
    ('sprev', 'VAR', 1),
    ('spcompose', 'STR', 0),
    ('spspan', 'CAST', 0),
    # 5장
    ('nacompound', 'INC', 1),
    ('nacompound', 'PREDEC', 1),
    ('natype', 'GENERIC', 1),
    ('naevent', 'ASSIGN', 1),
    ('nanot', 'STRUCT', 1),
    ('nanot', 'NULLABLE', 1),
    ('nanot', 'REF', 1),
    ('nanot', 'DECON', 1),
]

# 컴파일러 플래그를 더한 캡처 — (예제, 언어 버전, 플래그, 꼬리표, 종료 코드)
FLAGS = [
    ('fknull', '14.0', '-define:STRICT -nowarn:9264', 'strict', 0),
    ('fknull', '14.0', '-define:EMPTYSET -nowarn:9264', 'emptyset', 0),
    ('fkcapture', '14.0', '-define:LAMBDA -nowarn:9258', 'lambda', 1),
    ('fkbreak', '14.0', '-nowarn:9258', 'nowarn', 0),
    ('fkbreak', '14.0', '-define:FIX', 'fix', 0),
    ('fkattr', '13.0', '-nowarn:0657', 'nowarn', 1),
]

# IL 의 호출 — (언어 버전, 플래그, 메서드들, 꼬리표). 도구는 14부의 것
IL = [
    ('14.0', None, 'Str Arr Spn Has Rev', 'il'),
    ('13.0', None, 'Str Arr Spn Has Rev', 'il'),
    ('14.0', '-define:COV', 'Up ArrUp', 'cov'),
]

# 200칸을 넘는 진단 — 종료 코드와 들어 있어야 할 것을 확인하고, 진단
# 줄의 번호와 문장을 표로 옮긴다.
# (예제, 언어 버전, 플래그, 종료 코드, 있어야 할 것들, 표에 쓸 무엇)
LONGLINE = [
    ('fknull', '14.0', '-define:STRICT', 0,
     ['warning CS9264', '6'], '-define:STRICT — get => field 인 Strict'),
    ('fkattr', '14.0', '-define:BAD', 0,
     ['warning CS0657', 'lazy cache'],
     '-define:BAD — field 를 쓰지 않는 속성에 [field: …]'),
    ('fkattr', '13.0', None, 1,
     ['error CS9260', 'warning CS0657'], 'C# 13.0 — fkattr 그대로'),
    ('spbasic', '13.0', None, 1,
     ['error CS1929'], 'C# 13.0 — 배열·Span 을 확장 메서드의 받는 쪽으로'),
    ('fkcapture', '14.0', '-define:LAMBDA', 1,
     ['error CS9273', 'warning CS9258', 'error CS0019'],
     '-define:LAMBDA — 접근자 안 람다의 매개변수 field'),
    ('fkbreak', '14.0', None, 0,
     ['warning CS9258', 'warning CS0649', '5 0'],
     'C# 14.0 — field 라는 멤버를 읽고 쓰던 접근자'),
]

# 장마다 거절을 모은 표 — (예제, 꼬리표, 무엇을 했나)
DIAG3 = [
    ('fkbasic', 'v13', 'C# 13.0 에서 get; 과 set => field 를 섞음'),
    ('fknullset', '13.0', 'C# 13.0 에서 몸체만 있는 접근자의 field'),
    ('fkctor', 'bad', 'setter 없는 P1 => field 에 바깥에서 대입'),
    ('fkinitacc', 'bad', 'init 접근자 속성에 바깥에서 대입'),
    ('fkcapture', 'nameof', 'nameof(field)'),
    ('fkcapture', 'lambda', '접근자 안 람다의 매개변수 field'),
    ('fkcapture', 'static', '인스턴스 속성의 static 람다가 field'),
    ('fkstatic', 'iface', '인터페이스의 인스턴스 속성이 field'),
    ('fkstruct', 'p2', 'readonly 속성의 field ??= …'),
    ('fkstruct', 'p4', 'readonly 속성의 set 이 field 에 대입'),
    ('fkwarn', 'setonly', '{ set; } — get 없는 자동 속성'),
    ('fkover', 'half', 'override 가 get 만 field 로'),
    ('fkhand', 'reset', '메서드 안의 field'),
    ('fkhand', 'ref', 'ref 를 돌려주는 속성의 ref field'),
]
DIAG4 = [
    ('spinfer', 'v13', 'C# 13.0 — 배열에서 ReadOnlySpan<T> 의 T 유추'),
    ('spcov', 'v13', 'C# 13.0 — Span<string> 을 ReadOnlySpan<object> 로'),
    ('spconv', 'cov13.0', 'C# 13.0 — ReadOnlySpan<string> 을 <object> 로'),
    ('spover', 'ambig13.0', 'C# 13.0 — IEnumerable<int> 판과 스팬 판'),
    ('spcompose', 'str13.0', 'C# 13.0 — string → 사용자 정의 변환'),
    ('spinfer', 'mixed', 'Span<T> 와 T 에서 서로 다른 T'),
    ('spcast', 'old', 'MemoryMarshal.Cast(배열) 를 Span 에 담음'),
    ('spambig', 'old', '배열 판과 스팬 판이 같이 맞는 호출'),
    ('sprev', 'var', 'var 에 void 인 Rev() 의 결과'),
    ('spspan', 'fail', 'string[] 를 Span<object> 에 암묵적으로'),
]
DIAG5 = [
    ('nabasic', 'v13', 'C# 13.0 에서 ?. 의 왼쪽 대입'),
    ('nacompound', 'inc', 'on?.Hits++'),
    ('nacompound', 'predec', '--on?.Hits'),
    ('natype', 'generic', '제약 없는 T 의 대입식 값을 씀'),
    ('naevent', 'assign', '이벤트에 ?. = 대입'),
    ('nanot', 'struct', 'null 이 될 수 없는 구조체 p?.X ='),
    ('nanot', 'nullable', 'Nullable 구조체 q?.X ='),
    ('nanot', 'ref', 'ref c?.V'),
    ('nanot', 'decon', '분해 대입의 왼쪽 c?.V'),
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
            raise RuntimeError('[p15b] %s(%s) 에 진단 줄이 없다' % (ex, key))
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
    for d, code in CRASH:
        ctx.cs(EX + d, expect=code)
    for d in GATED13:
        found[(d, 'v13')] = ctx.cs(EX + d, v='13.0', expect=1)
    for d, v, sym, code in OTHER:
        flags = '-define:' + sym if sym else None
        tag = sym.lower() if sym else None
        found[(d, (tag or '') + v)] = ctx.cs(EX + d, v=v, flags=flags,
                                              tag=tag, expect=code)
    for d, sym, code in DEFINES:
        found[(d, sym.lower())] = ctx.cs(EX + d, flags='-define:' + sym,
                                         tag=sym.lower(), expect=code)
    for d, v, fl, tag, code in FLAGS:
        found[(d, tag)] = ctx.cs(EX + d, v=v, flags=fl, tag=tag, expect=code)
    for v, fl, methods, tag in IL:
        ctx.cs(EX + 'spil', cmd='csrun -- ' + methods, v=v, flags=fl,
               tag=tag)
    long_rows = []
    for d, v, fl, want, needles, what in LONGLINE:
        src = os.path.join(csver.BASE, EX + d)
        code, text = execute(src, v, fl, 'p15b-check-%s-%s' % (d, v))
        if code != want or any(x not in text for x in needles):
            raise RuntimeError('[p15b] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, fl, want, ' / '.join(needles), text))
        seen = set()
        for m in re.finditer(r'(error|warning) (CS\d+): (.*)', text):
            if m.group(2) in seen:
                continue
            seen.add(m.group(2))
            long_rows.append((what, EX + d, m.group(1) + ' ' + m.group(2),
                              m.group(3)))
    ctx.table('p15b_long', ['무엇을', '예제', '진단', '컴파일러의 문장 전체'],
              long_rows, caption='200칸이 넘어 캡처에 싣지 못한 진단 — '
              '실험 묶음이 돌려 뽑은 문장')
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    for name, spec, cap in (
            ('p15b_diag3', DIAG3, '3장의 거절·경고 캡처에서 뽑은 표'),
            ('p15b_diag4', DIAG4, '4장의 거절·경고 캡처에서 뽑은 표'),
            ('p15b_diag5', DIAG5, '5장의 거절·경고 캡처에서 뽑은 표')):
        if spec:
            ctx.table(name, head, diag_rows(spec, found), caption=cap)
