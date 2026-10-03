# -*- coding: utf-8 -*-
"""12부 가운데 조각 — C# 11 의 제네릭 수학(4장)과 연산자·정수(5장)의 증거.
예제는 ex/12/ 아래의 gm*·sa*·ck*·ur*·sh*·ni* 이다. (문자열·제네릭 특성은
p12, 목록 패턴·required·ref 필드는 p12c 가 같은 ex/12 에 다른 이름으로 쓴다)

오류 줄이 200칸을 넘는 거절은 캡처로 싣지 못한다 — LONGLINE 이 종료
코드와 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 4장 — 제네릭 수학
    'gmbefore', 'gmsum', 'samonoid', 'saself', 'sacall', 'sakinds',
    'savirtual', 'satypearg', 'sarules', 'sainherit', 'sail',
    'saruntime', 'safactory',
    'gmifaces', 'gmhier', 'gmcreate', 'gmaddop', 'gmbase', 'gmfloat',
    'gmconst', 'gmchecked', 'gmparse', 'gmpat', 'gmmod', 'gmvec',
    'gmfamily',
    # 5장 — 연산자와 정수
    'ckbasic', 'ckpair', 'ckconv', 'ckbody', 'ckmeta', 'ckdyn', 'ckint128',
    'urbasic', 'urbefore', 'uruser', 'urlimits',
    'shrelax', 'shcout', 'shgeneric',
    'nialias', 'nichecked', 'niambig', 'nidyn',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['gmold']

# C# 10.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED10 = [
    ('gmsum', '형식 매개변수의 static abstract 멤버 호출'),
    ('samonoid', 'static abstract 멤버 선언'),
    ('savirtual', 'static virtual 멤버 선언'),
    ('sarules', 'static sealed 멤버 선언'),
    ('ckbasic', 'checked 사용자 정의 연산자'),
    ('urbasic', '부호 없는 오른쪽 시프트'),
    ('shrelax', '시프트 연산자의 둘째 피연산자'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 종료 코드)
OTHER = [
    ('gmold', '14.0', 1),        # 제약이 없으면 C# 14 에서도 CS0019
    # 숫자형 IntPtr 는 언어 버전이 아니라 런타임(.NET 7+)에 묶여 있다
    ('nialias', '9.0', 0),
    ('nialias', '10.0', 0),
    ('nichecked', '8.0', 0),
    ('nidyn', '9.0', 0),
]

# 프로그램 인자로 갈래를 고르는 것 — (예제, 인자, 꼬리표, 종료 코드)
ARGS = [
    ('sail', 'box', 'box', 0),
]

# -define 으로 켜는 갈래 — (예제, 기호, 언어 버전, 종료 코드)
DEFINES = [
    ('saself', 'BAD', None, 1),
    ('sacall', 'BAD', None, 1),
    ('sacall', 'BAD2', None, 1),
    ('sakinds', 'BAD', None, 1),
    ('savirtual', 'BAD', None, 1),
    ('satypearg', 'BAD', None, 1),
    ('sarules', 'CLASS', None, 1),
    ('sarules', 'AMBIG', None, 1),
    ('sainherit', 'BAD', None, 1),
    ('gmconst', 'BAD', None, 1),
    ('gmconst', 'BAD2', None, 1),
    ('gmparse', 'BAD', None, 1),
    ('ckpair', 'BAD', None, 1),
    ('ckconv', 'BAD', None, 1),
    ('uruser', 'BAD', None, 1),
    ('urlimits', 'TREE', None, 1),
    ('urlimits', 'DYN', None, 1),
    ('shcout', 'BAD', None, 1),
    ('niambig', 'BAD', None, 1),
    ('niambig', 'BAD', '8.0', 1),   # 거절도 언어 버전을 보지 않는다
]

# 컴파일러 플래그를 더해 돌리는 것 — (예제, 플래그, 꼬리표, 종료 코드).
# -checked+ 는 csproj 의 <CheckForOverflowUnderflow>true 와 같다.
# 처리되지 않은 예외는 SIGABRT — 종료 코드는 134 또는 -6
FLAGS = [
    ('ckbasic', '-checked+', 'checked', (134, -6)),
    ('ckbody', '-checked+', 'checked', (134, -6)),
]

# 환경 변수를 주고 돌리는 것 — (예제, 환경, 종료 코드)
ENVS = []

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = [
    ('gmfloat', None, 'BAD', 1, ['error CS0315']),   # int 에는 Sqrt 가 없다
    ('gmpat', None, 'BAD', 1, ['error CS9060']),     # t is 1
]


# 장마다 거절을 모은 표 — (예제, 기호 또는 'v10', 무엇을 했나).
# 캡처에서 첫 오류의 번호와 문장을 뽑는다
DIAG4 = [
    ('samonoid', 'v10', 'C# 10.0 에서 static abstract 선언'),
    ('gmsum', 'v10', 'C# 10.0 에서 T.AdditiveIdentity 호출'),
    ('saself', 'bad', '연산자 피연산자가 제약 없는 T'),
    ('sacall', 'bad', '인터페이스 이름으로 직접 호출'),
    ('sacall', 'bad2', '명시적 구현을 구현 형식으로 호출'),
    ('sakinds', 'bad', 'static abstract 필드'),
    ('savirtual', 'bad', '기본 구현을 구현 형식으로 호출'),
    ('satypearg', 'bad', '구현 없는 인터페이스를 형식 인수로'),
    ('sarules', 'class', '클래스의 static abstract'),
    ('sarules', 'ambig', '두 인터페이스의 같은 이름'),
    ('sainherit', 'bad', '파생 클래스를 TSelf 로'),
    ('gmconst', 'bad', 'x / 2 — int 상수'),
    ('gmconst', 'bad2', '(T)2 — 캐스트'),
    ('gmparse', 'bad', 'T.Parse(s) — 인수 하나'),
]
DIAG5 = [
    ('ckbasic', 'v10', 'C# 10.0 에서 operator checked +'),
    ('ckpair', 'bad', '짝 없는 checked 연산자'),
    ('ckconv', 'bad', 'implicit 변환에 checked'),
    ('urbasic', 'v10', 'C# 10.0 에서 >>>'),
    ('uruser', 'bad', 'op_UnsignedRightShift 를 이름으로 호출'),
    ('urlimits', 'tree', '식 트리 안의 >>>'),
    ('urlimits', 'dyn', 'dynamic 에 >>>'),
    ('shrelax', 'v10', 'C# 10.0 에서 둘째 피연산자가 int 아닌 <<'),
    ('shcout', 'bad', '첫 피연산자가 다른 형식인 <<'),
    ('niambig', 'bad', 'UIntPtr + int'),
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


def diag_rows(spec, found):
    """거절 캡처 → 표의 줄(무엇을 했나, 예제, 오류 번호, 문장의 앞부분).
    O(캡처 길이)."""
    rows = []
    for ex, key, what in spec:
        text = found[(ex, key)]
        m = re.search(r'error (CS\d+): (.*)', text)
        if not m:
            raise RuntimeError('[p12b] %s 에 오류 줄이 없다' % ex)
        msg = m.group(2)
        if len(msg) > 60:      # 낱말 경계에서 자른다('C# 1…' 같은 꼬리 없이)
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, 'ex/12/' + ex, m.group(1), msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/12/' + d)
    for d in FAIL:
        ctx.cs('ex/12/' + d, expect=1)
    found = {}
    for d, title in GATED10:
        found[(d, 'v10')] = ctx.cs('ex/12/' + d, v='10.0', expect=1)
    for d, v, code in OTHER:
        ctx.cs('ex/12/' + d, v=v, expect=code)
    for d, arg, tag, code in ARGS:
        ctx.cs('ex/12/' + d, cmd='csrun -- ' + arg, tag=tag, expect=code)
    for d, sym, v, code in DEFINES:
        key = (d, sym.lower()) if v is None else (d, sym.lower() + v)
        found[key] = ctx.cs('ex/12/' + d, v=v, flags='-define:' + sym,
                            tag=sym.lower(), expect=code)
    for d, fl, tag, code in FLAGS:
        ctx.cs('ex/12/' + d, flags=fl, tag=tag, expect=code)
    for d, env, code in ENVS:
        ctx.cs('ex/12/' + d, env=env, expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/12/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p12b-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p12b] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))
    head = ['무엇을', '예제', '오류', '컴파일러의 문장(앞부분)']
    ctx.table('p12b_diag4', head, diag_rows(DIAG4, found),
              caption='4장의 거절 캡처에서 뽑은 표')
    ctx.table('p12b_diag5', head, diag_rows(DIAG5, found),
              caption='5장의 거절 캡처에서 뽑은 표')
