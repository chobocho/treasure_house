# -*- coding: utf-8 -*-
"""13부 마지막 조각 — C# 12 의 ref readonly 매개변수(6장), 인라인 배열(7장),
작은 기능들(8장 — 인스턴스 멤버 nameof·[Experimental]·인터셉터), 정리(9장)의
증거. 예제는 ex/13/ 아래의 rr*·ia*·nm*·ex*·ic*·w12* 이다. (기본 생성자·형식
별칭은 p13, 컬렉션 식·람다는 p13b 가 같은 ex/13 에 다른 이름으로 쓴다)

오류 줄이 200칸을 넘는 거절은 캡처로 싣지 못한다 — LONGLINE 이 종료
코드와 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 6장 — ref readonly 매개변수
    'rrbefore', 'rrbasic', 'rrcall', 'rrmeta', 'rrmigrate', 'rrold',
    'rrbcl', 'rrbreak', 'rrover', 'rrdeleg', 'rrdecl',
    # 7장 — 인라인 배열
    'iafixed', 'iabasic', 'ialayout', 'iaindex', 'iaspan', 'ialower',
    'iaforeach', 'iarules', 'ianot', 'iabcl',
    # 8장 — 작은 기능들
    'nmbasic', 'nmattr', 'nmold', 'nmlimits',
    'exbasic', 'exopts', 'exbcl',
    # 9장 — 정리: 같은 프로그램을 C# 11 과 C# 12 로
    'w12old', 'w12new',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    # 인터셉터는 -features:InterceptorsNamespaces=Gen 없이는 거절된다
    'icbasic',
]

# C# 11.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED11 = [
    ('rrbasic', 'ref readonly 매개변수'),
    ('iabasic', '인라인 배열'),
    ('nmbasic', '인스턴스 멤버 nameof'),
    ('nmattr', '특성 인수 안의 인스턴스 멤버 nameof'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 기호, 종료 코드)
OTHER = [
    ('rrbreak', '11.0', None, 0),     # C# 11 은 확장 메서드 E 를 고른다
    ('rrbreak', '11.0', 'BAD', 0),    # C# 11 은 모호하지 않다
    ('rrover', '14.0', 'BAD', 1),     # C# 14 에서도 모호하다
    # [InlineArray] 의 검사는 언어 버전에 묶이지 않는다
    ('iarules', '11.0', 'R1', 1),
    ('iarules', '11.0', 'R4', 1),
    # 인스턴스 멤버 nameof 의 거절은 C# 6 에서도 같은 기능 이름이다
    ('nmold', '6', 'BAD', 1),
    ('nmold', '11.0', None, 0),
    # [Experimental] 은 언어 버전이 아니라 컴파일러가 본다
    ('exbasic', '11.0', 'USE', 1),
    ('exbasic', '7.3', 'USE', 1),
    # 9장 — C# 12 판을 C# 11.0 으로 내리면 선언의 두 기능만 보인다
    ('w12new', '11.0', None, 1),
]

# -define 으로 켜는 갈래 — (예제, 기호, 종료 코드)
DEFINES = [
    ('rrbasic', 'W1', 0),             # 경고만 — 프로그램은 돈다
    ('rrbasic', 'W2', 0),
    ('rrbasic', 'W3', 0),
    ('rrcall', 'A1', 0),
    ('rrcall', 'A2', 1),
    ('rrcall', 'A3', 1),
    ('rrcall', 'A4', 1),
    ('rrcall', 'A5', 1),
    ('rrmigrate', 'V2', 0),
    ('rrold', 'BAD', 1),
    ('rrold', 'BAD2', 1),
    ('rrbreak', 'BAD', 1),
    ('rrover', 'BAD', 1),
    ('rrover', 'BAD3', 1),
    ('rrdeleg', 'BAD', 1),
    ('rrdeleg', 'BAD2', 1),
    ('rrdecl', 'BAD', 1),
    ('rrdecl', 'W1', 0),
    ('rrdecl', 'BAD2', 1),
    ('rrdecl', 'BAD3', 1),
    ('iafixed', 'BAD', 1),
    ('iafixed', 'BAD2', 1),
    ('iaindex', 'BAD', 1),
    ('iaindex', 'BAD2', 1),
    ('iaspan', 'BAD', 1),
    ('iaspan', 'BAD2', 1),
    ('iaforeach', 'BAD', 1),
    ('iarules', 'R1', 1),
    ('iarules', 'R2', 1),
    ('iarules', 'R3', 1),
    ('iarules', 'R4', 1),
    ('iarules', 'R5', 1),
    ('ianot', 'BAD', 1),
    ('ianot', 'BAD2', 1),
    ('ianot', 'BAD3', 1),
    ('nmlimits', 'BAD', 1),
    ('nmlimits', 'BAD2', 1),
    ('nmlimits', 'BAD3', 1),
    ('exbasic', 'USE', 1),
    ('exopts', 'U1', 1),
    ('exopts', 'U2', 1),
    ('exopts', 'U3', 1),
    ('exopts', 'BAD', 1),
]

# 컴파일러 플래그를 더해 돌리는 것 — (예제, 언어 버전, 플래그, 꼬리표,
# 종료 코드)
FLAGS = [
    ('exbasic', None, '-define:USE -nowarn:MY001', 'nowarn', 0),
    ('icbasic', None, '-features:InterceptorsNamespaces=Gen', 'ns', 0),
    ('icbasic', '7.3', '-features:InterceptorsNamespaces=Gen', 'ns', 0),
    ('icbasic', None, '-features:InterceptorsPreviewNamespaces=Gen',
     'preview', 1),
    ('icbasic', None, '-features:InterceptorsNamespaces=Gen'
     ' -define:BADCOL', 'badcol', 1),
    ('icbasic', None, '-features:InterceptorsNamespaces=Gen'
     ' -define:BADPATH', 'badpath', 1),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = [
    # 인라인 배열에는 Length 멤버가 없다 — CS1061 줄이 243칸
    ('ianot', None, 'BAD4', 1, ['error CS1061', "'Length'"]),
]

# 장마다 거절·경고를 모은 표 — (예제, 기호 또는 'v11', 무엇을 했나).
# 캡처에서 첫 진단의 번호와 문장을 뽑는다
DIAG6 = [
    ('rrbasic', 'v11', 'C# 11.0 에서 ref readonly 매개변수'),
    ('rrbasic', 'w1', 'ref readonly 에 수식어 없는 변수'),
    ('rrbasic', 'w2', 'ref readonly 에 값(x + 0)'),
    ('rrbasic', 'w3', 'ref readonly 에 in 없는 readonly 필드'),
    ('rrcall', 'a1', 'in 매개변수에 ref 인수'),
    ('rrcall', 'a2', 'ref readonly 에 out 인수'),
    ('rrcall', 'a3', 'ref 매개변수에 in 인수'),
    ('rrcall', 'a4', 'ref readonly 에 in 5'),
    ('rrcall', 'a5', 'ref readonly 에 ref 로 readonly 필드'),
    ('rrold', 'bad', 'C# 11.0 에서 .NET 10 의 ref readonly 에 in'),
    ('rrbreak', 'bad', 'ref·in 오버로드 둘에 ref 인수'),
    ('rrover', 'bad', 'in·ref readonly 오버로드 둘에 ref 인수'),
    ('rrover', 'bad3', 'in·ref readonly 오버로드 둘에 수식어 없이'),
    ('rrdeleg', 'bad', 'in 대리자에 ref 람다'),
    ('rrdeleg', 'bad2', 'ref readonly 대리자에 ref 메서드'),
    ('rrdecl', 'bad', '연산자의 ref readonly 매개변수'),
    ('rrdecl', 'w1', 'ref readonly 매개변수의 기본값'),
    ('rrdecl', 'bad2', '[RequiresLocation] 을 손으로'),
    ('rrdecl', 'bad3', 'ref readonly 매개변수에 대입'),
]
DIAG7 = [
    ('iabasic', 'v11', 'C# 11.0 에서 buffer[i]'),
    ('iafixed', 'bad', '고정 크기 버퍼에 string 원소'),
    ('iafixed', 'bad2', '고정 크기 버퍼를 Span 으로'),
    ('iaindex', 'bad', '상수 인덱스 b[8] (길이 8)'),
    ('iaindex', 'bad2', '상수 범위 b[6..9]'),
    ('iaspan', 'bad', 'static readonly 필드를 Span 으로'),
    ('iaspan', 'bad2', '메서드가 돌려준 값을 ReadOnlySpan 으로'),
    ('iaforeach', 'bad', '값 위의 foreach (ref …)'),
    ('iarules', 'r1', '인스턴스 필드 둘'),
    ('iarules', 'r2', '길이 0'),
    ('iarules', 'r3', 'StructLayout(Explicit)'),
    ('iarules', 'r4', 'record struct'),
    ('iarules', 'r5', 'class'),
    ('ianot', 'bad', '컬렉션 식의 대상'),
    ('ianot', 'bad2', '목록 패턴'),
    ('ianot', 'bad3', '객체 초기화자의 [0] = 1'),
]
DIAG8 = [
    ('nmbasic', 'v11', 'C# 11.0 에서 정적 문맥의 nameof(Name.ToUpper)'),
    ('nmattr', 'v11', 'C# 11.0 에서 특성 인수의 nameof'),
    ('nmold', 'bad6', 'C# 6 에서 nameof(Name.Length)'),
    ('nmlimits', 'bad', 'nameof(Name.Length.ToString())'),
    ('nmlimits', 'bad2', '정적 메서드의 nameof(this.Name)'),
    ('nmlimits', 'bad3', 'nameof(Tags[0].Length)'),
    ('exbasic', 'use', '[Experimental("MY001")] 메서드 호출'),
    ('exopts', 'u1', 'UrlFormat 을 준 실험 API'),
    ('exopts', 'u2', 'Message 를 준 실험 API'),
    ('exopts', 'u3', '실험 형식 Wrapper 를 부름'),
    ('exopts', 'bad', '진단 ID "MY 005"'),
    ('icbasic', 'v12', '-features 없이 인터셉터'),
    ('icbasic', 'preview', 'InterceptorsPreviewNamespaces=Gen'),
    ('icbasic', 'badcol', '위치가 메서드 이름이 아님'),
    ('icbasic', 'badpath', '없는 파일 Prog.cs'),
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
        # 오류가 있으면 오류를(앞의 경고에 가리지 않게), 없으면 경고를
        m = (re.search(r'error (CS\d+|[A-Z]+\d+): (.*)', text)
             or re.search(r'warning (CS\d+): (.*)', text))
        if not m:
            raise RuntimeError('[p13c] %s 에 진단 줄이 없다' % ex)
        msg = m.group(2)
        if len(msg) > 60:      # 낱말 경계에서 자른다('C# 1…' 같은 꼬리 없이)
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, 'ex/13/' + ex, m.group(1), msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    found = {}
    for d in RUN:
        ctx.cs('ex/13/' + d)
    for d in FAIL:
        found[(d, 'v12')] = ctx.cs('ex/13/' + d, expect=1)
    for d, title in GATED11:
        found[(d, 'v11')] = ctx.cs('ex/13/' + d, v='11.0', expect=1)
    for d, v, sym, code in OTHER:
        flags = '-define:' + sym if sym else None
        tag = sym.lower() if sym else None
        found[(d, (tag or '') + v)] = ctx.cs('ex/13/' + d, v=v, flags=flags,
                                              tag=tag, expect=code)
    for d, sym, code in DEFINES:
        found[(d, sym.lower())] = ctx.cs('ex/13/' + d, flags='-define:' + sym,
                                         tag=sym.lower(), expect=code)
    for d, v, fl, tag, code in FLAGS:
        found[(d, tag)] = ctx.cs('ex/13/' + d, v=v, flags=fl, tag=tag,
                                 expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/13/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p13c-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p13c] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    for name, spec, cap in (('p13c_diag6', DIAG6, '6장의 거절·경고 캡처에서 뽑은 표'),
                            ('p13c_diag7', DIAG7, '7장의 거절 캡처에서 뽑은 표'),
                            ('p13c_diag8', DIAG8, '8장의 거절 캡처에서 뽑은 표')):
        if spec:
            ctx.table(name, head, diag_rows(spec, found), caption=cap)
