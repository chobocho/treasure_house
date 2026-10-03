# -*- coding: utf-8 -*-
"""11부 뒤 조각 — C# 10 의 보간 문자열 처리기(4장), 람다와 패턴(5장),
작은 기능들(6장), 정리(7장)의 증거. 예제는 ex/11/ 아래의 ih*·ci*·la*·pp*·
dc*·da*·ab*·ca*·ln*·np*·v10* 이다. (record struct·구조체·global using 은
p11 이 같은 ex/11 에 다른 이름으로 쓴다)

오류 줄이 200칸을 넘는 거절(CS8950 · CS8947 …)은 캡처로 싣지 못한다 —
LONGLINE 이 종료 코드와 오류 번호만 확인한다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 4장 — 보간 문자열 처리기 · 상수 보간 문자열
    'ihtrace', 'ihbool', 'ihorder', 'ihafter', 'ihover', 'ihassert',
    'ihcreate', 'ihasync', 'ihruntime', 'ihlocal', 'ihindex', 'ciconst',
    # 5장 — 람다와 확장 속성 패턴
    'lanatural', 'laobj', 'lasynth', 'lainfer', 'laret', 'laattr',
    'labreak', 'lamini', 'laruntime', 'lalater', 'lacond',
    'ppbasic', 'ppeval', 'ppbad',
    # 6장 — 작은 기능들
    'dcmix', 'dcorder', 'dacases', 'abcustom', 'caexpr', 'caruntime', 'lnspan',
    'npimpl', 'v10null',
    # 7장 — 같은 프로그램, C# 9.0 과 C# 10
    'v10old', 'v10new',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = []

# C# 9.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가). 7장의 표가 이
# 캡처들에서 컴파일러가 댄 기능 이름과 오류 번호를 뽑는다
GATED9 = [
    ('ihtrace', '보간 문자열 처리기'),
    ('ciconst', '상수 보간 문자열'),
    ('lanatural', '람다·메서드 그룹의 자연 형식'),
    ('laobj', 'Delegate·object·Expression 으로의 변환'),
    ('lainfer', '자연 형식으로 하는 형식 유추'),
    ('laret', '람다의 반환 형식'),
    ('laattr', '람다의 특성'),
    ('ppbasic', '확장 속성 패턴'),
    ('dcmix', '선언과 대입을 섞은 분해'),
    ('abcustom', '메서드에 단 비동기 빌더'),
    ('npimpl', '공개 아닌 인터페이스 멤버의 암시적 구현'),
]

# 다른 버전으로도 돌려 보는 것 — (예제, 언어 버전, 종료 코드).
# 거절이 아니라 출력이 달라지는 것 — 언어 버전에 묶인 동작 (나)
OTHER = [
    ('ihover', '9.0', 0),        # 9.0 에서는 모두 string 오버로드로
    ('ihassert', '9.0', 0),      # 9.0 에서는 구멍이 언제나 평가된다
    ('labreak', '9.0', 0),       # 9.0 에서는 확장 메서드·기반 클래스로
    ('lalater', '10.0', 1),      # C# 12 의 기본값·params 람다
    ('dacases', '9.0', 0),       # 확정 대입의 개선은 언어 버전을 보지 않는다
    ('dacases', '7.3', 0),
    ('caexpr', '9.0', 0),        # CallerArgumentExpression 도 게이트가 없다
    ('lnspan', '9.0', 0),        # #line 범위 꼴도 게이트가 없다
    ('v10new', '9.0', 1),        # 선언 단계의 거절만 보인다
]

# -define 으로 켜는 갈래 — (예제, 기호, 언어 버전, 종료 코드)
DEFINES = [
    ('ihafter', 'BAD', None, 1),
    ('ihasync', 'AWAIT', None, 1),
    ('ihindex', 'BAD', None, 1),
    ('ciconst', 'BAD', None, 1),
    ('lanatural', 'BAD', None, 1),
    ('laobj', 'WARN', None, 0),
    ('lainfer', 'BAD', None, 1),
    ('lainfer', 'BAD', '14.0', 1),     # ?: 는 C# 14 에서도 CS0173
    ('laret', 'BAD', None, 1),
    ('laattr', 'BAD', None, 1),
    ('labreak', 'AMBIG', None, 1),
    ('labreak', 'AMBIG', '9.0', 0),
    ('lalater', 'BAD', None, 1),
    ('lacond', 'DEBUG', None, 0),
    ('lacond', 'LAMBDA', None, 1),
    ('ppbad', 'BAD', None, 1),
    ('ppbad', 'CALL', None, 1),
    ('dcmix', 'BAD', None, 1),
    ('dacases', 'BAD', None, 1),
    ('abcustom', 'BAD', None, 1),
    ('caexpr', 'ODD', None, 0),
    ('lnspan', 'WARN', None, 0),
    ('npimpl', 'INTERNAL', None, 1),
    ('v10null', 'OLD', None, 1),
    ('v10null', 'OLD', '8.0', 1),   # 문서는 'C# 10.0 부터' 라고 적는다
]

# 환경 변수를 주고 돌리는 것 — (예제, 환경, 종료 코드)
ENVS = [
    # 계층 컴파일(tier 0)이 섞이면 할당량이 실행마다 흔들릴 수 있다
    ('ihsb', 'DOTNET_TieredCompilation=0', 0),
]

# 오류 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# 확인한다(슬라이드는 그렇게 밝힌다).
# (예제, 언어 버전, 기호, 종료 코드, 진단 번호들)
LONGLINE = [
    ('ihafter', None, 'LATE', 1, ['error CS8950']),
    ('ihafter', None, 'WARN', 0, ['warning CS8947']),
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


def gate_rows(found):
    """C# 9.0 캡처 → 표의 줄. 'Feature' 꼴이 아닌 거절은 이름 칸에
    '(전용 문장 …)' 을 적는다. O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error CS\d+: Feature '([^']*)'", text):
            name = m.group(1) or '(빈 이름)'
            if name not in names:
                names.append(name)
        other = re.findall(r'error (CS\d+): (?!Feature)', text)
        if other:
            names.append('(전용 문장 %s)' % ' '.join(sorted(set(other))))
        codes = sorted(set(re.findall(r'error (CS\d+)', text)))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/11/' + ex, ' · '.join(names),
                     ' '.join(codes), str(count)))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/11/' + d)
    for d in FAIL:
        ctx.cs('ex/11/' + d, expect=1)
    found = []
    for d, title in GATED9:
        found.append((d, title, ctx.cs('ex/11/' + d, v='9.0', expect=1)))
    for d, v, code in OTHER:
        ctx.cs('ex/11/' + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        ctx.cs('ex/11/' + d, v=v, flags='-define:' + sym,
               tag=sym.lower(), expect=code)
    for d, env, code in ENVS:
        ctx.cs('ex/11/' + d, env=env, expect=code)
    for d, v, sym, want, diags in LONGLINE:
        src = os.path.join(csver.BASE, 'ex/11/' + d)
        v = v or csver.lang_version(src)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p11b-check-%s-%s' % (d, sym))
        if code != want or any(x not in text for x in diags):
            raise RuntimeError('[p11b] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' '.join(diags), text))
    ctx.table('p11b_gates9',
              ['기능', '예제', '컴파일러가 댄 이름', '오류 번호', '오류 수'],
              gate_rows(found),
              caption='4장–6장의 예제를 -langversion:9.0 으로 컴파일한 '
                      '캡처에서 뽑은 표')
