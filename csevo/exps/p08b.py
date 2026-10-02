# -*- coding: utf-8 -*-
"""8부 가운데 조각 — C# 7.0 의 나머지(ref 지역 변수와 반환, throw 식,
식 본문의 확장, 숫자 리터럴, 작업 같은 형식)와 C# 7.1 의 증거.
예제는 ex/08/ 아래의 ref*·thr*·eb*·lit*·task*·v71* 이다.
(튜플·패턴·out 변수·지역 함수는 p08, C# 7.2·7.3 은 p08c 가 같은
ex/08 에 다른 이름으로 쓴다)"""
import re
import subprocess

# 그대로 돌아가는 예제 — csproj 의 LangVersion 으로
RUN = [
    # 5장 — ref 지역 변수와 ref 반환
    'refgate', 'refcopy', 'refbig', 'refmax', 'refmeta', 'refindexer',
    'refalias', 'refcovar',
    'refnull', 'refbcl', 'reflater13',
    # 5장 — throw 식
    'thrgate', 'thrbefore', 'thrlazy', 'thrflow', 'thrlambda',
    'thrswitch8',
    # 5장 — 식 본문의 확장
    'ebgate', 'ebctor', 'ebil',
    # 5장 — 숫자 리터럴
    'litgate', 'litweird', 'littype',
    # 5장 — 작업 같은 형식
    'taskattr', 'taskown', 'taskover', 'tasklater10',
    # 6장 — C# 7.1
    'v71default', 'v71defcond', 'v71defover', 'v71defnull',
    'v71tupnames', 'v71tuprules', 'v71tupbreak', 'v71genpat',
    'v71genold', 'v71refpack', 'v71tupdecon', 'v71mainboth',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = [
    'refbadlocal', 'refstructfld', 'refinit', 'refwhere', 'refro',
    'refvirt', 'thrbad', 'thrparse', 'thrtree', 'ebbad', 'litbad',
    'v71ver', 'v71defbad', 'v71defnarrow', 'v71mainvoid',
]

# #if BAD 줄을 켜면 컴파일러가 거절한다 — (예제, 종료 코드)
BAD = [
    ('refbig', 1), ('refmax', 1), ('taskover', 1), ('refmeta', 1),
    ('refindexer', 1), ('refalias', 1),
    ('thrflow', 1), ('littype', 1),
    ('v71defover', 1), ('v71tuprules', 1), ('v71genpat', 1),
]

# C# 6 으로 내리면 거절되는 것 — 언어 버전 짝 (가). 5장 끝의 표가
# 이 캡처들에서 기능 이름을 뽑는다: (예제, 표에 적을 기능)
GATED6 = [
    ('refgate', 'ref 반환·ref 지역 변수'),
    ('thrgate', 'throw 식'),
    ('ebgate', '생성자·종료자·접근자의 식 본문'),
    ('litgate', '이진 리터럴·자릿수 구분자'),
]

# C# 7.0 으로 내리면 거절되는 것 — 7.1 의 언어 버전 짝 (가)
GATED70 = [
    'v71default', 'v71tupnames', 'v71tuprules', 'v71tupbreak',
    'v71genpat', 'v71mainvoid', 'v71maintask', 'v71tupdecon',
]

# 뒤 버전 기능 — 한 단계 아래로 내리면 거절 (예제, 아래 버전)
LATER = [
    ('reflater13', '12.0'), ('reflater13', '7.0'), ('thrswitch8', '7.3'),
    ('tasklater10', '9.0'),
]

# 게이트가 없는 기능 — 낮은 버전으로도 컴파일되고 돈다 (예제, 버전)
UNGATED = [
    ('taskattr', '5'), ('taskown', '5'),
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
    """C# 6 거절 캡처 → 표의 줄. 한 캡처에 기능 이름이 여럿일 수 있다
    (리터럴 예제는 둘). O(캡처 길이)."""
    rows = []
    for ex, title, text in found:
        names = []
        for m in re.finditer(r"error (CS\d+): Feature '([^']+)'", text):
            if m.group(2) not in names:
                names.append(m.group(2))
        codes = sorted(set(re.findall(r'error (CS\d+)', text)))
        count = len(re.findall(r'\berror CS', text))
        rows.append((title, 'ex/08/' + ex, ' · '.join(names),
                     ' '.join(codes), str(count)))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs('ex/08/' + d)
    for d in FAIL:
        ctx.cs('ex/08/' + d, expect=1)
    for d, code in BAD:
        ctx.cs('ex/08/' + d, flags='-define:BAD', tag='bad', expect=code)
    found = []
    for d, title in GATED6:
        found.append((d, title, ctx.cs('ex/08/' + d, v='6', expect=1)))
    for d in GATED70:
        ctx.cs('ex/08/' + d, v='7.0', expect=1)
    for d, v in LATER:
        ctx.cs('ex/08/' + d, v=v, expect=1)
    for d, v in UNGATED:
        ctx.cs('ex/08/' + d, v=v)

    # 디버그 빌드와 최적화 빌드의 IL — 식 본문과 블록 본문
    ctx.cs('ex/08/ebil', flags='-optimize+', tag='opt')
    # 람다 하나뿐인 throw 식 — C# 10 의 자연 형식도 못 정한다
    ctx.cs('ex/08/thrlambda', v='10.0', flags='-define:BAD', tag='bad',
           expect=1)

    # 6장 — 언어 버전 고르기: 이름마다 컴파일러가 실제로 고른 버전
    for v in ('latest', 'default', 'latestmajor', 'preview', '7'):
        ctx.cs('ex/08/v71ver', v=v, expect=1)
    ctx.cs('ex/08/v71ver', v='07', expect=1)          # 앞자리 0 은 거절
    ctx.cs('ex/08/v71langq', flags='-langversion:?', tag='list')
    # default 리터럴의 좁혀진 자리 — 언어 버전과 상관없다
    ctx.cs('ex/08/v71defnarrow', v='14.0', expect=1)
    # ?: 안의 default — C# 9 의 대상 형식 조건식에서도 같은가
    ctx.cs('ex/08/v71defcond', v='9.0')
    # default 와 C# 8 의 nullable 참조 형식
    ctx.cs('ex/08/v71defnull', v='8.0', flags='-nullable:enable',
           tag='nrt')
    # 열린 형식에 null 상수 패턴 — C# 8 에서야 된다
    ctx.cs('ex/08/v71genpat', v='8.0', flags='-define:BAD', tag='bad')
    # async 없이 Task<int> 를 돌려주는 Main — 종료 코드 3
    ctx.cs('ex/08/v71maintask', expect=3)
    # 옛 Main 과 async Main 이 함께 — 경고 수준 5 에서야 경고
    ctx.cs('ex/08/v71mainboth', flags='-warn:5', tag='warn5')
    # 참조 어셈블리는 실행용으로 불러올 수 없다
    ctx.cs('ex/08/v71refload', flags='-refout:bin/ref.dll',
           tag='refout')
    # 참조 어셈블리 — -refout 으로 bin/ref.dll 을 함께 낸다
    ctx.cs('ex/08/v71refasm', flags='-refout:bin/ref.dll', tag='refout')

    ctx.table('p08b_gates6',
              ['기능', '예제', '컴파일러가 댄 기능 이름', '오류 번호',
               '오류 수'],
              gate_rows(found),
              caption='5장의 게이트 여섯 — 같은 예제를 -langversion:6 '
                      '으로 컴파일한 캡처에서 뽑은 표')
