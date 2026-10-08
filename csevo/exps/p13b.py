# -*- coding: utf-8 -*-
"""13부 가운데 조각 — C# 12 의 컬렉션 식(4장)과 람다의 기본값·params(5장)의
증거. 예제는 ex/13/ 아래의 ce*·cb*·sp*·ld*·lp* 이다. (기본 생성자·형식
별칭은 p13, ref readonly·인라인 배열은 p13c 가 같은 ex/13 에 다른 이름으로
쓴다)

오류 줄이 200칸을 넘는 거절은 캡처로 싣지 못한다 — LONGLINE 이 종료
코드와 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 4장 — 컬렉션 식
    'cebefore', 'cebasic', 'cetargets', 'ceronly', 'ceempty', 'cenotype',
    'ceinfer', 'cenested',
    'cespread', 'ceorder', 'cerange', 'cecond',
    'cbbasic', 'cbimm', 'cbrules', 'cbiface',
    'cecinit', 'cestr', 'ceactions', 'cecap', 'ceaddrange', 'cedict',
    'ceover', 'ceover2', 'cealloc', 'celower', 'cespan', 'ceescape',
    'ceuse', 'cerev', 'ceruntime', 'celater',
    # 5장 — 람다의 기본값과 params
    'ldbasic', 'ldtype', 'ldnamed', 'ldmgroup', 'ldbreak', 'ldwarn',
    'ldvalues', 'ldimplicit', 'lddpv', 'ldframe',
    'lpbasic', 'lpmeta', 'lpmix', 'ldlater',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = []

# C# 11.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED11 = [
    ('cebasic', '컬렉션 식'),
    ('ldbasic', '람다의 기본값'),
    ('lpbasic', '람다의 params 배열'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 기호, 종료 코드)
OTHER = [
    ('cenotype', '13.0', 'SUM', 0),   # C# 13 의 더 나은 변환 규칙
    ('cecond', '14.0', 'BAD', 1),     # C# 14 에서도 CS0173
    ('ceover', '13.0', 'BAD2', 0),    # C# 13 이 모호함을 푼다
    ('celater', '12.0', None, 1),     # params 컬렉션은 C# 13
    # 메서드 그룹의 기본값·params 는 언어 버전이 아니라 컴파일러에 묶였다
    ('ldmgroup', '10.0', None, 0),
    ('ldbreak', '10.0', 'BAD', 1),
    ('ldlater', '13.0', None, 1),     # 형식 없는 out 은 C# 14
]

# 프로그램 인자로 갈래를 고르는 것 — (예제, 인자, 꼬리표, 종료 코드)
ARGS = []

# -define 으로 켜는 갈래 — (예제, 기호, 종료 코드)
DEFINES = [
    ('cenotype', 'BAD', 1),
    ('cenotype', 'BAD2', 1),
    ('cenotype', 'BAD3', 1),
    ('cenotype', 'SUM', 1),
    ('ceinfer', 'BAD', 1),
    ('cenested', 'BAD', 1),
    ('cespread', 'BAD', 1),
    ('cerange', 'BAD', 1),
    ('cecond', 'BAD', 1),
    ('cbrules', 'BAD', 1),
    ('cbrules', 'BAD2', 1),
    ('cecinit', 'BAD', 1),
    ('ceactions', 'BAD', 1),
    ('cedict', 'BAD', 1),
    ('ceover', 'BAD', 1),
    ('ceover', 'BAD2', 1),
    ('ceover2', 'BAD', 1),
    ('ceuse', 'BAD', 1),
    ('ceuse', 'BAD2', 1),
    ('ceescape', 'BAD', 1),
    ('ldtype', 'BAD', 1),
    ('ldnamed', 'BAD', 1),
    ('ldbreak', 'BAD', 1),
    ('ldbreak', 'BAD2', 1),
    ('ldwarn', 'WARN1', 0),          # 경고만 — 프로그램은 돈다
    ('ldwarn', 'WARN2', 0),
    ('ldwarn', 'WARN3', 0),
    ('ldvalues', 'BAD', 1),
    ('ldvalues', 'BAD2', 1),
    ('ldvalues', 'BAD3', 1),
    ('ldimplicit', 'BAD', 1),
    ('ldimplicit', 'BAD2', 1),
    ('lpmeta', 'BAD', 1),
    ('lpmix', 'BAD', 1),
    ('lpmix', 'BAD2', 1),
    ('ldlater', 'BAD', 1),
]

# 컴파일러 플래그(와 환경)를 더해 돌리는 것 — (예제, 플래그, 환경,
# 꼬리표, 종료 코드). csrun 은 -optimize 없이 컴파일한다(디버그 IL)
FLAGS = [
    ('cealloc', '-optimize+', None, 'opt', 0),
    ('cespan', '-optimize+', None, 'opt', 0),
    ('cespan', '-optimize+', 'DOTNET_TieredCompilation=0', 'opt', 0),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = [
    # FrozenDictionary 의 빌더는 C# 12 규칙에 맞지 않아 Add 를 찾는다
    ('cedict', None, 'FZ', 1, ['error CS0144', 'error CS1061']),
    ('cedict', '14.0', 'FZ', 1, ['error CS0144', 'error CS1061']),
    # string 에는 인수 없는 생성자도 Add 도 없다
    ('cestr', None, 'BAD', 1, ['error CS1729', 'error CS1061']),
]

# 장마다 거절을 모은 표 — (예제, 기호 또는 'v11', 무엇을 했나).
# 캡처에서 첫 진단의 번호와 문장을 뽑는다
DIAG4 = [
    ('cebasic', 'v11', 'C# 11.0 에서 int[] a = [1, 2, 3]'),
    ('cenotype', 'bad', 'var x = [1, 2, 3]'),
    ('cenotype', 'bad2', '[1, 2, 3].Length'),
    ('cenotype', 'bad3', '[1, 2, 3].Sum() — 확장 메서드'),
    ('cenotype', 'sum', 'Enumerable.Sum([1, 2, 3])'),
    ('ceinfer', 'bad', 'AsArray([]) — 원소 없는 추론'),
    ('cenested', 'bad', 'int[,] 에 [[1, 2], [3, 4]]'),
    ('cespread', 'bad', '[.. 42] — 열거할 수 없는 것'),
    ('cerange', 'bad', 'Range[] 에 [..2]'),
    ('cecond', 'bad', '.. v ? ["-v"] : []'),
    ('cbrules', 'bad', '빌더 메서드 이름이 틀림'),
    ('cbrules', 'bad2', '빌더가 int[] 를 받음'),
    ('cecinit', 'bad', 'Add 만 있고 IEnumerable 이 없음'),
    ('cedict', 'bad', 'Dictionary 에 [new("a", 1)]'),
    ('ceactions', 'bad', 'IEnumerable 형식에 [_ => { }]'),
    ('ceover2', 'bad', 'ReadOnlySpan 과 List 오버로드'),
    ('ceuse', 'bad', 'foreach (int x in [4, 5])'),
    ('ceuse', 'bad2', '매개변수 기본값 = []'),
    ('ceescape', 'bad', '[x, y] 를 ReadOnlySpan 으로 반환'),
]
DIAG5 = [
    ('ldbasic', 'v11', 'C# 11.0 에서 (int x = 1) => …'),
    ('lpbasic', 'v11', 'C# 11.0 에서 (params int[] xs) => …'),
    ('ldtype', 'bad', '기본값이 다른 람다끼리 대입'),
    ('ldnamed', 'bad', '람다의 매개변수 이름으로 명명 인수'),
    ('ldbreak', 'bad', 'var 로 받은 메서드 그룹을 Action 에'),
    ('ldwarn', 'warn1', '기본값 없는 대리자에 기본값 람다'),
    ('ldwarn', 'warn2', '기본값이 다른 대리자에 기본값 람다'),
    ('ldwarn', 'warn3', 'params 없는 대리자에 params 람다'),
    ('ldvalues', 'bad', '상수가 아닌 기본값'),
    ('ldvalues', 'bad2', 'ref 매개변수의 기본값'),
    ('ldvalues', 'bad3', '기본값 뒤에 필수 매개변수'),
    ('ldimplicit', 'bad', '형식 없는 매개변수의 기본값'),
    ('ldimplicit', 'bad2', '익명 메서드(delegate)의 기본값'),
    ('lpmeta', 'bad', 'params 람다를 Func<int[], int> 에'),
    ('lpmix', 'bad', 'params 매개변수의 기본값'),
    ('lpmix', 'bad2', 'params 뒤에 매개변수'),
    ('ldlater', 'bad', 'C# 14 에서도 (params xs) => …'),
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
    """거절 캡처 → 표의 줄(무엇을 했나, 예제, 진단 번호, 문장의 앞부분).
    O(캡처 길이)."""
    rows = []
    for ex, key, what in spec:
        text = found[(ex, key)]
        m = re.search(r'(?:error|warning) (CS\d+): (.*)', text)
        if not m:
            raise RuntimeError('[p13b] %s 에 진단 줄이 없다' % ex)
        msg = m.group(2)
        if len(msg) > 60:      # 낱말 경계에서 자른다('C# 1…' 같은 꼬리 없이)
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, 'ex/13/' + ex, m.group(1), msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/13/' + d)
    for d in FAIL:
        ctx.cs('ex/13/' + d, expect=1)
    found = {}
    for d, title in GATED11:
        found[(d, 'v11')] = ctx.cs('ex/13/' + d, v='11.0', expect=1)
    for d, v, sym, code in OTHER:
        flags = '-define:' + sym if sym else None
        tag = sym.lower() if sym else None
        found[(d, (tag or '') + v)] = ctx.cs('ex/13/' + d, v=v, flags=flags,
                                              tag=tag, expect=code)
    for d, arg, tag, code in ARGS:
        ctx.cs('ex/13/' + d, cmd='csrun -- ' + arg, tag=tag, expect=code)
    for d, sym, code in DEFINES:
        found[(d, sym.lower())] = ctx.cs('ex/13/' + d, flags='-define:' + sym,
                                         tag=sym.lower(), expect=code)
    for d, fl, env, tag, code in FLAGS:
        ctx.cs('ex/13/' + d, flags=fl, env=env, tag=tag, expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/13/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p13b-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p13b] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    if DIAG4:
        ctx.table('p13b_diag4', head, diag_rows(DIAG4, found),
                  caption='4장의 거절 캡처에서 뽑은 표')
    if DIAG5:
        ctx.table('p13b_diag5', head, diag_rows(DIAG5, found),
                  caption='5장의 거절 캡처에서 뽑은 표')
