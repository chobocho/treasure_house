# -*- coding: utf-8 -*-
"""12부 마지막 조각 — C# 11 의 목록 패턴(6장), required 와 구조체
기본값(7장), ref 필드와 scoped(8장), file 형식과 12부 정리(9장)의 증거.
예제는 ex/12/ 아래의 lp*·rq*·ad*·rf*·sc*·fl*·v11* 이다. (문자열·제네릭
특성은 p12, 제네릭 수학·연산자는 p12b 가 같은 ex/12 에 다른 이름으로 쓴다)

오류 줄이 200칸을 넘는 거절은 캡처로 싣지 못한다 — LONGLINE 이 종료
코드와 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — 목록 패턴
    'lpwhy', 'lpbasic', 'lpslice', 'lptypes', 'lpslicem', 'lplower',
    'lpnested', 'lpexhaust', 'lpsubsume', 'lpneg', 'lpcopy', 'lplater12',
    # 7장 — required 와 구조체 기본값
    'rqwhy', 'rqbasic', 'rqsets', 'rqnew', 'rqrules', 'rqinherit',
    'rqmeta', 'rqnull', 'rqattr',
    'adbasic', 'adlower', 'adwarn',
    # 8장 — ref 필드와 scoped
    'rfruntime', 'rfbasic', 'rfspan', 'rfrules', 'rfnull', 'rfreturn',
    'scbasic', 'sclocal', 'scout', 'scunscoped', 'scbreak',
    'rfmeta', 'rfsafety',
    # 9장 — file 형식과 12부 정리
    'flbasic', 'flmeta', 'flsig', 'flnames', 'v11old', 'v11new',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = []

# C# 10.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED10 = [
    ('lpbasic', '목록 패턴'),
    ('rqbasic', 'required 멤버'),
    ('adbasic', '구조체 필드의 자동 기본값'),
    ('adwarn', '읽기 전에 대입하지 않은 필드 — 10.0 의 오류'),
    ('rfbasic', 'ref 필드'),
    ('scbasic', 'scoped 매개변수 — 게이트 이름은 ref fields'),
    ('flbasic', 'file 형식'),
    ('v11new', '9장의 프로그램 전체 — 선언의 거절만'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 종료 코드)
OTHER = [
    ('lpneg', '10.0', 0),        # 음수 아님 가정은 언어 버전을 보지 않는다
    ('lplater12', '11.0', 1),    # 컬렉션 식만 거절 — 패턴은 C# 11
    # ref 안전 규칙은 언어 버전이 아니라 대상 런타임(corlib 의 플래그)에 묶였다
    ('rfruntime', '10.0', 0),
    ('scout', '10.0', 0),
    ('scout', '7.3', 0),
    ('rfsafety', '10.0', 0),
    ('rfsafety', '7.3', 0),
    ('rfsafety', '1', 0),
]

# 예약어가 된 형식 이름 — C# 10.0 에서는 그대로 컴파일된다
OTHER += [('flnames', '10.0', 0)]

# 프로그램 인자로 갈래를 고르는 것 — (예제, 인자, 꼬리표, 종료 코드)
ARGS = []

# -define 으로 켜는 갈래 — (예제, 기호, 언어 버전, 종료 코드).
# 처리되지 않은 예외는 SIGABRT — 종료 코드는 134 또는 -6
DEFINES = [
    ('lptypes', 'BAD', None, 1),
    ('lptypes', 'BAD2', None, 1),
    ('lpexhaust', 'BAD', None, (134, -6)),
    ('lpexhaust', 'BAD2', None, (134, -6)),
    ('lpsubsume', 'BAD', None, 1),
    ('lpneg', 'BAD', None, 1),
    ('lpneg', 'BAD2', None, 0),
    ('lpneg', 'BAD', '10.0', 1),
    ('rqbasic', 'BAD', None, 1),
    ('rqsets', 'BAD', None, 1),
    ('rqsets', 'BAD2', None, 1),
    ('rqnew', 'BAD', None, 1),
    ('rqnew', 'BAD2', None, 1),
] + [('rqrules', 'BAD%d' % i, None, 1) for i in range(1, 9)] + [
    ('rqinherit', 'BAD', None, 1),
    ('rqinherit', 'BAD2', None, 1),
    ('rqnull', 'OLD', None, 0),
    ('rqnull', 'BAD', None, 0),
    ('rqattr', 'BAD', None, 1),
] + [('rfrules', 'BAD%d' % i, None, 1) for i in range(1, 6)] + [
    ('rfrules', 'BAD5', '14.0', 1),   # ref struct 를 가리키는 ref 필드는 아직
    ('rfreturn', 'BAD', None, 1),
    ('rfreturn', 'BAD2', None, 1),
    ('scbasic', 'BAD', None, 1),
    ('scbasic', 'BAD2', None, 1),
    ('sclocal', 'BAD', None, 1),
    ('sclocal', 'BAD2', None, 1),
    ('scout', 'BAD', None, 1),
    ('scout', 'BAD', '10.0', 1),
    ('scout', 'BAD', '7.3', 1),
    ('scunscoped', 'BAD', None, 1),
    ('scunscoped', 'BAD2', None, 1),
    ('scbreak', 'DOC', None, 0),      # 문서의 CS8350 이 지금은 나지 않는다
    ('scbreak', 'BAD2', None, 1),
    ('scbreak', 'BAD3', None, 1),
] + [('flsig', 'BAD%d' % i, None, 1) for i in range(1, 5)] + [
    ('flnames', 'FILE', None, 1),
    ('flnames', 'SCOPED', None, 1),
    ('flnames', 'REQ', None, 1),
    ('flnames', 'SCOPED', '10.0', 0),
]

# 컴파일러 플래그를 더해 돌리는 것 — (예제, 플래그, 꼬리표, 종료 코드)
FLAGS = [
    ('rqsets', '-nullable:enable', 'nullable', 0),
    # 꺼져 있는 경고(CS9018–CS9022)를 전역 분석기 설정으로 켠다
    ('adwarn', '-analyzerconfig:warn.txt', 'on', 0),
    ('adwarn', '-warn:9999', 'w9999', 0),      # 경고 웨이브로는 안 켜진다
    ('adwarn', '-warnaserror+:CS9022', 'err', 1),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = []


# 7장의 거절 표 — (예제, 기호, 무엇을 했나). 캡처의 첫 오류 줄에서 뽑는다
DIAG7 = [
    ('rqbasic', 'bad', '초기화자에서 required 하나를 빠뜨림'),
    ('rqsets', 'bad2', 'new Person() — 초기화자 없음'),
    ('rqsets', 'bad', '[SetsRequiredMembers] 생성자로 잇는데 특성 없음'),
    ('rqnew', 'bad', 'new() 제약의 형식 인수'),
    ('rqrules', 'bad1', 'required readonly 필드'),
    ('rqrules', 'bad2', 'set·init 없는 속성'),
    ('rqrules', 'bad3', 'internal set'),
    ('rqrules', 'bad4', '형식보다 덜 보이는 protected 필드'),
    ('rqrules', 'bad5', 'static 속성'),
    ('rqrules', 'bad6', '인덱서'),
    ('rqrules', 'bad7', '인터페이스 멤버'),
    ('rqrules', 'bad8', 'new 로 가린 멤버'),
    ('rqinherit', 'bad', 'override 에서 required 를 뺌'),
    ('rqattr', 'bad', '특성의 이름 붙은 인수에서 빠뜨림'),
]

DIAG8 = [
    ('rfrules', 'bad1', 'ref readonly 필드에 값을 씀'),
    ('rfrules', 'bad2', 'readonly ref 필드를 다시 가리킴'),
    ('rfrules', 'bad3', '보통 struct 의 ref 필드'),
    ('rfrules', 'bad4', 'readonly ref struct 의 ref 필드'),
    ('rfrules', 'bad5', 'ref struct 를 가리키는 ref 필드'),
    ('rfreturn', 'bad', '보통 필드를 ref 로 반환'),
    ('rfreturn', 'bad2', '지역 변수를 가리키는 ref 필드를 반환'),
    ('scbasic', 'bad', '지역 변수를 잡을 수 있는 메서드의 결과를 반환'),
    ('scbasic', 'bad2', 'scoped 매개변수를 Span 에 담아 반환'),
    ('sclocal', 'bad', 'scoped 지역 변수를 반환'),
    ('sclocal', 'bad2', '반환할 수 있는 Span 에 stackalloc'),
    ('scout', 'bad', 'out 매개변수를 ref 로 반환'),
    ('scunscoped', 'bad', '구조체 필드를 ref 로 반환'),
    ('scunscoped', 'bad2', '임시 값의 [UnscopedRef] 멤버를 반환'),
    ('scbreak', 'bad2', '숨은 in 기본 인수를 받은 결과를 반환'),
    ('scbreak', 'bad3', 'ref struct 메서드가 ref 매개변수를 필드에'),
]

DIAG9 = [
    ('flsig', 'bad1', 'file 형식을 공개 메서드의 반환 형식에'),
    ('flsig', 'bad2', '중첩 형식에 file'),
    ('flsig', 'bad3', 'public file record'),
    ('flsig', 'bad4', 'global using static 의 file 형식'),
    ('flnames', 'file', 'class file'),
    ('flnames', 'scoped', 'class scoped'),
    ('flnames', 'req', 'class required'),
]

DIAG_RE = re.compile(r'\((\d+),(\d+)\): (?:error|warning) (CS\d+): (.*)')


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


def short(msg, n=60):
    """낱말 경계에서 자른다('C# 1…' 같은 꼬리 없이)."""
    return msg if len(msg) <= n else msg[:n].rsplit(' ', 1)[0] + ' …'


def diag_rows(spec, found):
    """거절 캡처 → 표의 줄(무엇을 했나, 예제, 오류 번호, 문장의 앞부분).
    O(캡처 길이)."""
    rows = []
    for ex, key, what in spec:
        m = re.search(r'error (CS\d+): (.*)', found[(ex, key)])
        if not m:
            raise RuntimeError('[p12c] %s 에 오류 줄이 없다' % ex)
        rows.append((what, 'ex/12/' + ex, m.group(1), short(m.group(2))))
    return rows


def pair_rows(old, new):
    """같은 소스의 두 캡처에서 진단을 차례대로 맞댄다 — 위치가 다르면
    표가 거짓이 되므로 멈춘다. O(줄 수)."""
    a = DIAG_RE.findall(old)
    b = [d for d in DIAG_RE.findall(new) if d[2] != 'CS0649']
    if len(a) != len(b) or any(x[:2] != y[:2] for x, y in zip(a, b)):
        raise RuntimeError('[p12c] adwarn 의 두 캡처가 맞지 않는다')
    return [('%s행 %s열' % x[:2], x[2], y[2], short(y[3], 56))
            for x, y in zip(a, b)]


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
        found[(d, tag)] = ctx.cs('ex/12/' + d, flags=fl, tag=tag,
                                 expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/12/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p12c-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p12c] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))

    head = ['무엇을', '예제', '오류', '컴파일러의 문장(앞부분)']
    ctx.table('p12c_diag7', head, diag_rows(DIAG7, found),
              caption='7장의 required 거절 캡처에서 뽑은 표')
    ctx.table('p12c_diag8', head, diag_rows(DIAG8, found),
              caption='8장의 ref 안전 거절 캡처에서 뽑은 표')
    ctx.table('p12c_diag9', head, diag_rows(DIAG9, found),
              caption='9장의 file 형식 거절 캡처에서 뽑은 표')
    ctx.table('p12c_adpairs',
              ['위치', 'C# 10.0 의 오류', 'C# 11 의 숨은 경고', '경고 문장(앞부분)'],
              pair_rows(found[('adwarn', 'v10')], found[('adwarn', 'on')]),
              caption='ex/12/adwarn 을 -langversion:10.0 으로, 그리고 11.0 에서 '
                      '-analyzerconfig:warn.txt 로 컴파일한 두 캡처를 줄마다 맞댄 표')
