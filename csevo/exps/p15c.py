# -*- coding: utf-8 -*-
"""15부 마지막 조각 — C# 14 의 partial 이벤트와 생성자(6장), 사용자 정의
복합 대입(7장), 작은 기능들(8장 — nameof 의 열린 제네릭 · 람다 매개변수
한정자 · 식 트리의 선택·명명 인수 · #: 지시문), 정리(9장)의 증거.
예제는 ex/15/ 아래의 pe*·ca*·nm*·lm*·et*·dr*·w14* 이다(p15·p15b 는 같은
ex/15 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 13.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다.

pecrash 는 캡처로 싣지 못한다 — SDK 10.0.112 의 csc 가 스택 넘침으로
죽으며 16MB 가 넘는 스택 트레이스를 찍는다. CRASHCHECK 가 종료 코드와
되풀이되는 프레임을 확인하고, 그 프레임들을 표(tbl_p15c_crash)로 옮긴다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/15/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — partial 이벤트와 생성자
    'pebasic', 'pegen', 'peinit', 'peevent', 'pebad', 'pesig', 'pemeta',
    'peiface',
    # 7장 — 사용자 정의 복합 대입
    'cawhy', 'cabasic', 'caalloc', 'cavar', 'cafall', 'canull', 'caincr',
    'cacheck', 'cameta', 'cavirt', 'cabcl', 'carules', 'cadyn', 'caonce',
    # 8장 — 작은 기능들(nmold 는 C# 13.0 프로젝트)
    'nmbasic', 'nmold', 'nmnot', 'lmbasic', 'lmref', 'lmbad', 'lmbreak',
    'lmover', 'etbasic', 'etorder', 'etwhy', 'etdefault',
    # 9장 — 정리(w14old 는 C# 13.0 프로젝트)
    'w14old', 'w14new', 'w14next',
]

# 처리하지 않은 예외로 끝나는 것 — (예제, 종료 코드)
CRASH = []

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다.
# pecrash 는 여기 없다(캡처할 수 없는 컴파일러 충돌 — CRASHCHECK)
FAIL = ['pebreak', 'drbasic', 'drrules', 'drshebang']

# C# 13.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED13 = ['pebasic', 'peiface', 'cabasic', 'nmbasic', 'lmbasic', 'lmref',
           'etbasic', 'w14new']

# 다른 버전으로 — (예제, 언어 버전, 기호 또는 None, 종료 코드)
OTHER = [
    ('pebreak', '13.0', None, 0),     # C# 13 에서는 partial 을 돌려주는 메서드
    ('cawhy', '13.0', None, 0),       # 정적 + 만 — C# 13 도 같은 출력
    # 8장
    ('nmold', '14.0', 'CS14', 0), ('nmold', '13.0', 'CS14', 1),
    ('lmbreak', '13.0', 'DEF', 0),    # 13.0 에서 scoped 는 형식 이름
    ('etorder', '13.0', None, 1),
    ('etwhy', '13.0', None, 1),
    # 9장 — 이 컴파일러에는 C# 15 가 없다
    ('w14next', 'preview', 'UNION', 1),
    ('w14next', '15', None, 1),
]

# #if 줄을 켠 캡처 — (예제, 기호, 종료 코드)
DEFINES = [
    ('peinit', 'BAD', 1), ('peinit', 'NOTHIS', 1),
    ('peevent', 'VALUE', 1), ('peevent', 'ADDONLY', 1),
    ('peevent', 'TWICE', 1),
    ('pebad', 'NOIMPL', 1), ('pebad', 'NODEF', 1),
    ('pebad', 'ABSTRACT', 1), ('pebad', 'NOTPARTIAL', 1),
    ('pesig', 'NAMES', 0), ('pesig', 'DEFAULT', 0), ('pesig', 'ACCESS', 1),
    ('pebreak', 'FIX', 0),
    ('pecrash', 'FIX', 0),
    # 7장
    ('cavar', 'NOSTATIC', 1), ('cacheck', 'NOPAIR', 1),
    ('carules', 'STATIC', 1), ('carules', 'RETURN', 1), ('carules', 'TWO', 1),
    ('carules', 'NONPUBLIC', 1), ('carules', 'NOTVAR', 1),
    ('cadyn', 'NOSTATIC', 0),
    ('caonce', 'INPARAM', 1), ('caonce', 'READONLY', 1),
    # 8장
    ('nmold', 'OBJ', 1), ('nmold', 'ABS', 1),
    ('nmnot', 'NESTED', 1), ('nmnot', 'PARTIAL', 1), ('nmnot', 'ARRAY', 1),
    ('nmnot', 'OUTSIDE', 1),
    ('lmref', 'NOSCOPED', 1),
    ('lmbad', 'PARAMS', 1), ('lmbad', 'MIXED', 1), ('lmbad', 'NOPARENS', 1),
    ('lmbad', 'DEFAULT', 1),
    ('lmbreak', 'VAR', 0), ('lmbreak', 'DEF', 1), ('lmbreak', 'FIX', 0),
    ('lmover', 'AMBIG', 1),
    ('etbasic', 'SKIP', 1), ('etorder', 'SWAP', 1),
    # 9장
    ('w14next', 'WITH', 1), ('w14next', 'LABEL', 1), ('w14next', 'UNION', 1),
]

FBP = '-features:FileBasedProgram'

# 컴파일러 플래그를 더한 캡처 — (예제, 언어 버전, 플래그, 꼬리표, 종료 코드)
FLAGS = [
    ('cacheck', '14.0', '-checked+', 'checked', -6),   # 첫 += 부터 checked
    # 8장 — #: 지시문은 csc 의 기능 플래그가 있어야 받는다
    ('drbasic', '14.0', FBP, 'fbp', 0),
    ('drbasic', '13.0', FBP, 'fbp', 0),
    ('drbasic', '1', FBP, 'fbp', 0),
    ('drrules', '14.0', FBP, 'fbp', 0),
    ('drrules', '14.0', FBP + ' -define:IFFIRST', 'iffirst', 1),
    ('drrules', '14.0', FBP + ' -define:AFTER', 'after', 1),
    ('drshebang', '14.0', FBP, 'fbp', 1),
]

# 200칸을 넘는 진단 — 종료 코드와 들어 있어야 할 것을 확인하고, 진단
# 줄의 번호와 문장을 표(tbl_p15c_long)로 옮긴다.
# (예제, 언어 버전, 플래그, 종료 코드, 있어야 할 것들, 표에 쓸 무엇)
LONGLINE = [
    ('pebad', '14.0', '-define:STATIC', 1,
     ['error CS0267', 'an instance constructor name'],
     '-define:STATIC — static partial 생성자'),
]

# 컴파일러가 스택 넘침으로 죽는 것 — (예제, 언어 버전, 플래그, 꼬리표).
# 출력은 싣지 않고 종료 코드 134 와 되풀이 고리의 프레임을 확인한다
CRASHCHECK = [
    ('pecrash', '14.0', None, 'C# 14.0'),
    ('pecrash', '13.0', None, 'C# 13.0'),
]
# 되풀이 고리에 있어야 할 프레임 — 고리를 도는 차례로
CYCLE = [
    'SourceMemberContainerTypeSymbol.MergePartialMembers',
    'MemberSignatureComparer.HaveSameParameterTypes',
    'SynthesizedEventAccessorValueParameterSymbol',
    'SourceEventSymbol.get_IsWindowsRuntimeEvent',
    'TypeSymbol.FindImplementationForInterfaceMemberInNonInterface'
    'WithDiagnostics',
    'TypeSymbol.MakeExplicitInterfaceImplementationMap',
    'SourceMemberContainerTypeSymbol.GetMembersUnordered',
]

# 장마다 거절을 모은 표 — (예제, 꼬리표, 무엇을 했나)
DIAG6 = [
    ('pebasic', 'v13', 'C# 13.0 에서 partial 생성자·이벤트'),
    ('peiface', 'v13', 'C# 13.0 에서 인터페이스의 partial 이벤트'),
    ('peinit', 'bad', '정의 조각에 : base(…)'),
    ('peinit', 'nothis', '기본 생성자가 있는 형식의 partial 생성자에 : this 없음'),
    ('peevent', 'value', 'partial 이벤트를 값으로 Opened?.Invoke()'),
    ('peevent', 'addonly', '구현 조각에 add 만'),
    ('peevent', 'twice', '접근자 없는 꼴을 두 번'),
    ('pebad', 'noimpl', '구현 조각이 없다'),
    ('pebad', 'nodef', '정의 조각이 없다'),
    ('pebad', 'abstract', 'abstract partial 이벤트'),
    ('pebad', 'notpartial', 'partial 이 아닌 클래스 안에'),
    ('pesig', 'names', '두 조각의 매개변수 이름이 다르다'),
    ('pesig', 'default', '구현 조각에 기본값'),
    ('pesig', 'access', '두 조각의 접근성이 다르다'),
    ('pebreak', 'fail', 'C# 14.0 — partial 을 돌려주는 메서드 Make()'),
]
DIAG7 = [
    ('cabasic', 'v13', 'C# 13.0 에서 인스턴스 operator +='),
    ('cavar', 'nostatic', '정적 + 없이 속성에 +='),
    ('cacheck', 'nopair', '보통 판 없는 operator checked -='),
    ('carules', 'static', 'static void operator *='),
    ('carules', 'return', 'void 가 아닌 operator /='),
    ('carules', 'two', '매개변수 둘인 operator %='),
    ('carules', 'nonpublic', 'public 이 아닌 operator &='),
    ('carules', 'notvar', '변수가 아닌 new P() += 1'),
    ('caonce', 'inparam', 'in 매개변수에 readonly operator -='),
    ('caonce', 'readonly', 'static readonly 필드에 +='),
]
DIAG8 = [
    ('nmbasic', 'v13', 'C# 13.0 에서 nameof(List<>)'),
    ('nmold', 'obj', 'C# 13.0 — 제약을 못 맞추는 Registry<object>'),
    ('nmold', 'abs', 'C# 13.0 — 추상 형식 Registry<Shape>'),
    ('nmnot', 'nested', 'nameof(List<List<>>)'),
    ('nmnot', 'partial', 'nameof(Dictionary<int,>)'),
    ('nmnot', 'array', 'nameof(List<>[])'),
    ('nmnot', 'outside', 'nameof 밖의 List<>.Empty'),
    ('lmbasic', 'v13', 'C# 13.0 에서 (text, out result) =>'),
    ('lmref', 'v13', 'C# 13.0 에서 (scoped s) =>'),
    ('lmref', 'noscoped', 'scoped 매개변수 대리자에 (s) =>'),
    ('lmbad', 'params', '(params xs) =>'),
    ('lmbad', 'mixed', '(ref int x, y) =>'),
    ('lmbad', 'noparens', 'ref x => (괄호 없이)'),
    ('lmbad', 'default', '(ref x, y = 1) =>'),
    ('lmbreak', 'def', 'C# 14.0 — (scoped s = default) =>'),
    ('lmover', 'ambig', 'scoped 만 다른 두 대리자에 (scoped s) =>'),
]
DIAG8B = [
    ('etbasic', 'v13', 'C# 13.0 — 식 트리 안의 선택 인수'),
    ('etorder', '13.0', 'C# 13.0 — 식 트리 안의 명명 인수'),
    ('etbasic', 'skip', '선택 인수를 건너뛴 명명 인수'),
    ('etorder', 'swap', '순서를 바꾼 명명 인수'),
    ('drbasic', 'fail', '기능 플래그 없이 #:'),
    ('drshebang', 'fbp', '첫 줄이 아닌 #!'),
    ('drrules', 'iffirst', '#if 뒤의 #:'),
    ('drrules', 'after', '첫 토큰 뒤의 #:'),
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
            raise RuntimeError('[p15c] %s(%s) 에 진단 줄이 없다' % (ex, key))
        code, msg = got
        if len(msg) > 60:      # 낱말 경계에서 자른다
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, EX + ex, code, msg))
    return rows


def crash_rows():
    """컴파일러 충돌을 확인하고 표의 줄을 만든다. 스택 트레이스는 실행마다
    꼴이 다르다(프레임을 다 찍거나 'Repeated N times:' 로 접는다) — 그래서
    줄 수는 싣지 않고, 고리의 프레임이 있는지만 본다. O(출력 길이)."""
    rows = []
    for d, v, fl, what in CRASHCHECK:
        src = os.path.join(csver.BASE, EX + d)
        code, text = execute(src, v, fl, 'p15c-check-%s-%s' % (d, v))
        if code != 134 or not text.startswith('Stack overflow.'):
            raise RuntimeError('[p15c] %s(-langversion:%s) 는 종료 134·'
                               'Stack overflow 여야 한다 — 종료 %d\n%s'
                               % (d, v, code, text[:2000]))
        missing = [f for f in CYCLE if f not in text]
        if missing:
            raise RuntimeError('[p15c] %s 의 스택에 %s 가 없다'
                               % (d, ', '.join(missing)))
        if 'error CS' in text:
            raise RuntimeError('[p15c] %s 가 진단을 찍었다' % d)
        rows.append((what, EX + d, 'exit %d' % code, 'Stack overflow.'))
    for i, f in enumerate(CYCLE):
        rows.append(('', '고리 %d' % (i + 1), '프레임', f))
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
    long_rows = []
    for d, v, fl, want, needles, what in LONGLINE:
        src = os.path.join(csver.BASE, EX + d)
        code, text = execute(src, v, fl, 'p15c-check-%s-%s' % (d, v))
        if code != want or any(x not in text for x in needles):
            raise RuntimeError('[p15c] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, fl, want, ' / '.join(needles), text))
        seen = set()
        for m in re.finditer(r'(error|warning) (CS\d+): (.*)', text):
            if m.group(2) in seen:
                continue
            seen.add(m.group(2))
            long_rows.append((what, EX + d, m.group(1) + ' ' + m.group(2),
                              m.group(3)))
    # 지원하는 언어 버전 목록 — 컴파일만 하고 실행은 건너뛴다
    ctx.cs(EX + 'w14next', flags='-langversion:?', tag='list',
           env='CSRUN_COMPILE_ONLY=1')
    ctx.table('p15c_long', ['무엇을', '예제', '진단', '컴파일러의 문장 전체'],
              long_rows, caption='200칸이 넘어 캡처에 싣지 못한 진단 — '
              '실험 묶음이 돌려 뽑은 문장')
    ctx.table('p15c_crash', ['무엇을', '예제', '결과', '스택 트레이스'],
              crash_rows(),
              caption='SDK 10.0.112 의 csc — 인터페이스 이벤트와 같은 이름의 '
              'partial 이벤트')
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    for name, spec, cap in (
            ('p15c_diag6', DIAG6, '6장의 거절·경고 캡처에서 뽑은 표'),
            ('p15c_diag7', DIAG7, '7장의 거절·경고 캡처에서 뽑은 표'),
            ('p15c_diag8', DIAG8, '8장(nameof·람다)의 거절 캡처에서 뽑은 표'),
            ('p15c_diag8b', DIAG8B,
             '8장(식 트리·지시문)의 거절 캡처에서 뽑은 표')):
        if spec:
            ctx.table(name, head, diag_rows(spec, found), caption=cap)
