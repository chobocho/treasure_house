# -*- coding: utf-8 -*-
"""14부 가운데 조각 — C# 13 의 ref struct 확장(4장: allows ref struct ·
ref struct 인터페이스 · 반복기와 async 의 ref·unsafe)과 partial 속성·
인덱서(5장)의 증거. 예제는 ex/14/ 아래의 ar*·ri*·ru*·pp* 이다. (params
컬렉션·Lock 은 p14, 오버로드 우선순위·작은 기능들·field 는 p14c 가 같은
ex/14 에 다른 이름으로 쓴다)"""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 4장 — allows ref struct
    'arbasic', 'arlimit', 'arescape', 'arsyntax', 'arnew', 'armeta',
    'arfunc', 'arnatural', 'arruntime',
    # 4장 — ref struct 인터페이스
    'ribasic', 'riconv', 'rialloc', 'riequ', 'ridim', 'riusing', 'ripref',
    'riunscoped', 'riruntime',
    # 4장 — 반복기와 async 의 ref·unsafe
    'rubasic', 'ruacross', 'rutrap', 'ruparam', 'ruforeach', 'rulower',
    'ruunsafe', 'ruasync', 'rumod', 'rubreak', 'ruawait', 'rulock',
    # 5장 — partial 속성과 인덱서
    'ppbasic', 'ppgen', 'ppbad', 'ppmatch', 'ppattr', 'ppregex', 'ppiface',
    'ppfield',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = []

# C# 12.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED12 = [
    'arbasic', 'arfunc', 'ribasic', 'riusing', 'ripref', 'rubasic',
    'ruunsafe', 'rumod', 'ruforeach', 'ppbasic', 'ppiface',
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 기호, 종료 코드)
OTHER = [
    ('arnatural', '12.0', None, 0),   # 자연 형식은 언어 버전에 안 묶였다
    ('arnatural', '10.0', None, 0),
    ('ruold', '12.0', None, 0),       # 반복기의 Span 지역 변수는 전부터
    ('ruold', '12.0', 'REF', 1),
    ('ruold', '12.0', 'ASYNC', 1),
    ('ruasync', '7.3', None, 0),      # async 의 unsafe 블록은 전부터
    ('rubreak', '12.0', 'OLD', 0),    # 깨지는 변경 — 12.0 에선 된다
    ('rubreak', '13.0', 'OLD', 1),
    ('ruawait', '12.0', None, 1),     # 반대쪽 — 12.0 에선 await 불가
    ('ruparam', '14.0', 'ITER', 1),   # C# 14 에서도
    ('ppiface', '14.0', None, 0),
    ('ppfield', '13.0', None, 1),     # field 는 C# 14
    ('ppbad', '14.0', 'HALF', 0),
]

# -define 으로 켜는 갈래 — (예제, 기호, 종료 코드)
DEFINES = [
    ('arbasic', 'BAD', 1),
    ('arlimit', 'FIELD', 1),
    ('arlimit', 'BOX', 1),
    ('arlimit', 'ARRAY', 1),
    ('arlimit', 'LAMBDA', 1),
    ('arlimit', 'LIST', 1),
    ('arlimit', 'TOSTR', 1),
    ('arescape', 'BAD', 1),
    ('arsyntax', 'LAST', 1),
    ('arsyntax', 'CLASS', 1),
    ('arsyntax', 'INHERIT', 1),
    ('armeta', 'BAD', 1),
    ('riconv', 'CONV', 1),
    ('riconv', 'CAST', 1),
    ('riconv', 'PAT', 0),            # 경고만 — 프로그램은 돈다
    ('ridim', 'MISSING', 1),
    ('ridim', 'SEALED', 1),
    ('riusing', 'BAD', 1),
    ('riunscoped', 'BAD', 1),
    ('riunscoped', 'BAD2', 1),
    ('ruacross', 'SPAN', 1),
    ('ruacross', 'REF', 1),
    ('ruacross', 'YIELD', 1),
    ('rutrap', 'BAD', 1),
    ('ruparam', 'ASYNC', 1),
    ('ruparam', 'ITER', 1),
    ('ruparam', 'UNUSED', 0),        # 쓰지 않는 Span 매개변수는 된다
    ('ruunsafe', 'YIELD', 1),
    ('ruunsafe', 'ADDR', 1),
    ('ruasync', 'AWAIT', 1),
    ('ruasync', 'ADDR', 0),          # 기본 경고 수준에선 조용하다
    ('rumod', 'BODY', 1),
    ('rulock', 'LOCK', 1),
    ('ppbad', 'MISSING', 1),
    ('ppbad', 'ONLYIMPL', 1),
    ('ppbad', 'BOTHAUTO', 1),
    ('ppbad', 'TWOIMPL', 1),
    ('ppbad', 'HALF', 1),
    ('ppmatch', 'ACC', 1),
    ('ppmatch', 'INIT', 1),
    ('ppmatch', 'NAME', 0),          # 경고만
    ('ppregex', 'BAD', 1),
]

# 컴파일러 플래그를 더해 돌리는 것 — (예제, 플래그, 꼬리표, 종료 코드).
# csrun 은 -optimize 없이 컴파일한다(디버그 IL)
FLAGS = [
    ('rulower', '-optimize+', 'opt', 0),
    ('ruasync', '-define:ADDR -warn:8', 'addr8', 0),
    ('rulock', '-warn:9999', 'w9999', 0),
    ('ppdoc', '-doc:bin/doc.xml', 'doc', 0),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = [
    # 명시적 구현은 ref struct 의 멤버로 보이지 않는다
    ('riconv', None, 'DIRECT', 1, ['error CS1061']),
]

# 장마다 거절을 모은 표 — (예제, 찾는 열쇠, 무엇을 했나).
# 캡처에서 첫 진단의 번호와 문장을 뽑는다
DIAG4 = [
    ('arbasic', 'v12', 'C# 12.0 에서 where T : allows ref struct'),
    ('arbasic', 'bad', '반제약 없는 T 에 Span<int>'),
    ('arlimit', 'field', '클래스의 필드가 T'),
    ('arlimit', 'box', 'object o = t'),
    ('arlimit', 'array', 'new T[1]'),
    ('arlimit', 'lambda', '람다가 t 를 포착'),
    ('arlimit', 'list', 'new List<T>()'),
    ('arlimit', 'tostr', 't.ToString()'),
    ('arescape', 'bad', '스택을 가리킬 수 있는 t 를 반환'),
    ('arsyntax', 'last', 'allows 뒤에 다른 제약'),
    ('arsyntax', 'class', 'class 와 allows ref struct'),
    ('arsyntax', 'inherit', 'where S : T 의 S 에 Span<int>'),
    ('armeta', 'bad', 'Span<Span<int>>'),
    ('ribasic', 'v12', 'C# 12.0 에서 ref struct : 인터페이스'),
    ('riconv', 'conv', 'ref struct 를 인터페이스 변수에'),
    ('riconv', 'cast', '(IName)t 캐스트'),
    ('riconv', 'pat', 't is IName (경고)'),
    ('ridim', 'missing', '기본 구현 멤버를 구현하지 않음'),
    ('ridim', 'sealed', 'T 로 sealed 인터페이스 멤버 호출'),
    ('riusing', 'bad', 'IDisposable 아닌 T 를 using'),
    ('riunscoped', 'bad', '[UnscopedRef] 속성의 ref 를 반환'),
    ('riunscoped', 'bad2', '구현 쪽에만 [UnscopedRef]'),
    ('rubasic', 'v12', 'C# 12.0 에서 async 의 Span 지역 변수'),
    ('ruacross', 'span', 'await 뒤에 Span 을 씀'),
    ('ruacross', 'ref', 'await 뒤에 ref 지역 변수를 씀'),
    ('rutrap', 'bad', 'Span 을 foreach 하며 yield'),
    ('ruparam', 'async', 'async 메서드의 ReadOnlySpan 매개변수'),
    ('ruparam', 'iter', '반복기의 Span 매개변수를 씀'),
    ('ruunsafe', 'yield', 'unsafe 블록 안의 yield return'),
    ('ruunsafe', 'addr', '반복기에서 &지역 변수'),
    ('ruasync', 'await', 'unsafe 블록 안의 await'),
    ('ruasync', 'addr8', 'async 에서 &지역 변수 (-warn:8)'),
    ('rumod', 'body', 'unsafe 반복기의 몸체에서 포인터'),
    ('rubreak', 'old13.0', 'unsafe 클래스 반복기의 지역 함수'),
    ('ruawait', '12.0', 'C# 12.0 에서 같은 자리의 await'),
    ('rulock', 'lock', 'Lock 의 lock 안에서 yield'),
]
DIAG5 = [
    ('ppbasic', 'v12', 'C# 12.0 에서 partial 속성'),
    ('ppbad', 'missing', '구현 조각이 없음'),
    ('ppbad', 'onlyimpl', '정의 조각이 없음'),
    ('ppbad', 'bothauto', '두 조각 모두 자동 속성 꼴'),
    ('ppbad', 'twoimpl', '구현 조각이 둘'),
    ('ppbad', 'half', 'C# 13.0 에서 접근자 하나만 몸체'),
    ('ppmatch', 'acc', 'private set 과 set'),
    ('ppmatch', 'init', 'init 과 set'),
    ('ppmatch', 'name', '인덱서 매개변수 이름이 다름'),
    ('ppregex', 'bad', '생성기 없이 [GeneratedRegex] 속성'),
    ('ppfield', '13.0', 'C# 13.0 에서 field 와 초기화자'),
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
            raise RuntimeError('[p14b] %s 에 진단 줄이 없다' % ex)
        msg = m.group(2)
        if len(msg) > 60:      # 낱말 경계에서 자른다('C# 1…' 같은 꼬리 없이)
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, 'ex/14/' + ex, m.group(1), msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/14/' + d)
    for d in FAIL:
        ctx.cs('ex/14/' + d, expect=1)
    found = {}
    for d in GATED12:
        found[(d, 'v12')] = ctx.cs('ex/14/' + d, v='12.0', expect=1)
    for d, v, sym, code in OTHER:
        flags = '-define:' + sym if sym else None
        tag = sym.lower() if sym else None
        found[(d, (tag or '') + v)] = ctx.cs('ex/14/' + d, v=v, flags=flags,
                                              tag=tag, expect=code)
    for d, sym, code in DEFINES:
        found[(d, sym.lower())] = ctx.cs('ex/14/' + d, flags='-define:' + sym,
                                         tag=sym.lower(), expect=code)
    for d, fl, tag, code in FLAGS:
        found[(d, tag)] = ctx.cs('ex/14/' + d, flags=fl, tag=tag,
                                 expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/14/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p14b-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p14b] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    ctx.table('p14b_diag4', head, diag_rows(DIAG4, found),
              caption='4장의 거절 캡처에서 뽑은 표')
    ctx.table('p14b_diag5', head, diag_rows(DIAG5, found),
              caption='5장의 거절 캡처에서 뽑은 표')
