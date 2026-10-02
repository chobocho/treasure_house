# -*- coding: utf-8 -*-
"""9부 가운데 조각 — C# 8.0 의 패턴의 확장(3장), 인덱스와 범위(4장),
비동기 스트림과 using(5장)의 증거.
예제는 ex/09/ 아래의 pat*·sw*·idx*·rng*·as*·use* 이다.
(nullable 참조 형식은 p09, 기본 인터페이스 메서드와 작은 기능들은 p09c 가
같은 ex/09 에 다른 이름으로 쓴다)"""
import re
import subprocess

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 3장 — switch 식
    'swbasic', 'swstmt', 'swtype', 'swenum', 'swwhen',
    # 3장 — 속성·위치·튜플·재귀 패턴
    'patprop', 'patnull', 'patnest', 'patext10', 'pattype',
    'patpos', 'patituple', 'patnames', 'pattuple', 'pattupleval',
    'patrec', 'patvar', 'patnullptr', 'patbyte',
    'patdag', 'patdecon', 'patil', 'patrel9', 'patlist11', 'patrt',
    # 4장 — 인덱스와 범위
    'idxbasic', 'idxtype', 'idxzero', 'rngbasic', 'rngtype', 'rngprec',
    'rngcopy', 'rngstring', 'idxpattern', 'rngpattern', 'idxlist',
    'idxlinq', 'rngerr', 'idxrt', 'idxinit13',
    # 5장 — 비동기 스트림과 using
    'asbasic', 'asvstask', 'asmanual', 'aspattern', 'ascancel',
    'asfinally', 'asconfig', 'assm', 'aslinq', 'asyncusing', 'auboth',
    'usedecl', 'usescope', 'usenull', 'usedisposal', 'usedispforeach',
    'asrt',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'patorder', 'idxwhere', 'aserrors', 'usebad', 'usegoto',
]

# #if BAD 줄을 켜면 컴파일러가 거절한다(또는 경고한다) — (예제, 종료 코드)
BAD = [
    ('swstmt', 1), ('swtype', 1), ('patnames', 1),
    ('patvar', 1), ('patbyte', 1), ('rngprec', 1),
    ('usedisposal', 1),
]

# C# 7.3 으로 내리면 거절되는 것 — 언어 버전 짝 (가). 3장의 표가 이
# 캡처들에서 컴파일러가 댄 기능 이름을 뽑는다: (예제, 표에 적을 꼴)
GATED73 = [
    ('swbasic', 'switch 식(상수와 _ 만)'),
    ('patprop', '속성 패턴'),
    ('patnull', '{ } 패턴'),
    ('patpos', '위치 패턴'),
    ('pattuple', '튜플 패턴(switch 식)'),
    ('pattupleval', '튜플 리터럴을 고르는 switch 식·문'),
    ('patrec', '재귀 패턴'),
    ('patvar', 'var (x, y) 패턴'),
    ('patnullptr', '포인터의 null 패턴'),
]

# 4장·5장의 언어 버전 짝 — C# 7.3 으로 내린다
GATED73B = [
    'idxbasic', 'rngbasic', 'idxpattern', 'rngpattern',
    'asbasic', 'aspattern', 'asyncusing', 'usedecl', 'usedisposal',
    'usedispforeach',
]

# 뒤 버전 기능 — 한 단계 아래로 내리면 거절 (예제, 아래 버전)
LATER = [
    ('patext10', '9.0'), ('patrel9', '8.0'), ('patlist11', '10.0'),
    ('idxinit13', '12.0'),
]

# 같은 소스를 두 언어 버전으로 — 버전에 묶인 동작인가 (예제, 버전, flags)
BOTH = [
    ('patbyte', '9.0', None), ('patbyte', '9.0', '-define:BAD'),
]


class Retry(object):
    """스왑이 찬 날에는 csc 하나가 60초를 넘기기도 한다(2026-10-01 두 번).
    시간 초과만 두 번까지 다시 돌린다 — 출력이 다른 것은 다시 돌리지
    않는다(기대한 종료 코드가 아니면 run_all 이 그대로 멈춘다)."""

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
    """C# 7.3 거절 캡처 → 표의 줄. 한 캡처에 기능 이름이 여럿일 수 있다.
    O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error (CS\d+): Feature '([^']+)'", text):
            if m.group(2) not in names:
                names.append(m.group(2))
        codes = sorted(set(re.findall(r'error (CS\d+)', text)))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/09/' + ex, ' · '.join(names),
                     ' '.join(codes), str(count)))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/09/' + d)
    # 빠뜨린 갈래 — 경고를 내고 컴파일되지만, 돌리면 예외로 죽는다
    ctx.cs('ex/09/swexh', expect=-6)
    for d in FAIL:
        ctx.cs('ex/09/' + d, expect=1)
    for d, code in BAD:
        ctx.cs('ex/09/' + d, flags='-define:BAD', tag='bad', expect=code)
    found = []
    for d, title in GATED73:
        found.append((d, title, ctx.cs('ex/09/' + d, v='7.3', expect=1)))
    for d in GATED73B:
        ctx.cs('ex/09/' + d, v='7.3', expect=1)
    for d, v in LATER:
        ctx.cs('ex/09/' + d, v=v, expect=1)
    for d, v, fl in BOTH:
        ctx.cs('ex/09/' + d, v=v, flags=fl,
               tag='bad' if fl else None, expect=1 if fl else 0)
    # [EnumeratorCancellation] 을 빼면 — 경고 CS8425 의 문장은 300칸이
    # 넘어 캡처의 200칸 한도에 걸린다. 경고는 끄고 동작만 뜬다
    ctx.cs('ex/09/ascancel', flags='-define:BAD -nowarn:8425', tag='bad')
    # 컴파일러가 범위 연산에 부르는 메서드 — 4장에서 쓴다
    ctx.cs('ex/09/patil', cmd='csrun -- Slice', tag='slice')

    ctx.table('p09b_gates73',
              ['패턴의 꼴', '예제', '컴파일러가 댄 기능 이름', '오류 번호',
               '오류 수'],
              gate_rows(found),
              caption='3장의 예제를 -langversion:7.3 으로 컴파일한 캡처에서 '
                      '뽑은 표')
