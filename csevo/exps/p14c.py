# -*- coding: utf-8 -*-
"""14부 마지막 조각 — C# 13 의 오버로드 해석 우선순위(6장), 작은 기능들
(7장 — \\e · 메서드 그룹의 자연 형식 · 개체 초기화자의 ^ 인덱스),
field 키워드 미리 보기(8장), 정리(9장)의 증거. 예제는 ex/14/ 아래의
or*·es*·mg*·ii*·fk*·w13* 이다(p14·p14b 는 같은 ex/14 에 다른 이름으로
쓴다).

게이트가 있는 기능은 C# 12.0 으로 내린 거절을 옆에 둔다. #if 기호를 켠
캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에 진단 하나를 노린다.
\\e 의 거절은 어휘 분석 단계라 같은 파일의 다른 거절을 가린다 — 그래서
\\e 시연은 제 파일에만 둔다."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/14/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion(13.0)으로
RUN = [
    # 6장 — 오버로드 해석 우선순위
    'orbasic', 'orderive', 'orext', 'orcall', 'orneg', 'orlang',
    'orwhere', 'oriface', 'orbcl',
    # 7장 — 작은 기능들
    'esbasic', 'eshex', 'eswhere', 'esold',
    'mgnatural', 'mgnest', 'mggeneric', 'mgcons', 'mgbreak',
    'iibasic', 'iiorder', 'iirange',
    # 8장 — field 키워드(fkbasic 은 C# 14.0 프로젝트)
    'fkbasic', 'fkbody', 'fkshadow', 'fklocal',
    # 9장 — 정리: 같은 프로그램을 C# 12 와 C# 13 으로, 버전마다의 거절 번호
    'w13old', 'w13new', 'w13codes',
]

# 처리하지 않은 예외로 끝나는 것 — (예제, 종료 코드)
CRASH = [('iitrap', -6)]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = ['orambig']

# C# 12.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED12 = ['orbasic', 'orneg', 'esbasic', 'eswhere', 'iibasic', 'iirange']

# 언어 버전에 묶인 동작(게이트 없음) — C# 12.0 에서 다른 결과 (나)
KEYED12 = ['mgnatural', 'mgnest', 'mggeneric', 'mgcons', 'mgbreak']

# 다른 버전으로 — (예제, 언어 버전, 기호 또는 None, 종료 코드)
OTHER = [
    ('orlang', '12.0', None, 0),     # 메타데이터의 특성은 조용히 무시
    ('orcall', '14.0', 'DEL1', 1),
    ('esold', '12.0', 'CS13', 1),    # #if 를 켜면 C# 12 가 거절
    ('esold', '13.0', 'CS13', 0),
    # field 는 C# 13 의 미리 보기 — 13.0 은 거절, preview 는 받는다
    ('fkbasic', '13.0', None, 1), ('fkbasic', '12.0', None, 1),
    ('fkbasic', 'preview', None, 0),
    ('iirange', '14.0', None, 0),    # 초기화자의 Slice 인수는 14.0 도 같다
    ('fkbody', '13.0', None, 1),     # 13.0 의 field 는 그냥 이름 — CS0103
    ('w13new', '12.0', None, 1),     # \e 의 거절이 나머지를 가린다
]

# '이 기능은 C# N 에 없다' 의 번호가 버전마다 다르다 — C# 14 기능 하나를
# 여러 언어 버전으로 컴파일해 첫 오류의 번호를 표로 모은다
CODES = ['6', '7', '7.1', '7.2', '7.3', '8.0', '9.0', '10.0', '11.0',
         '12.0', '13.0']

# 컴파일러 플래그를 더한 캡처 — (예제, 언어 버전, 플래그, 꼬리표, 종료 코드).
# CS9258 경고 줄은 200칸을 넘어 캡처에 싣지 못하므로 끄고 싣는다 —
# 경고가 실제로 나는지는 LONGLINE 이 따로 확인한다
FLAGS = [
    ('fkshadow', '14.0', '-nowarn:9258', 'nowarn', 0),
    ('fklocal', '14.0', '-nowarn:9258,219', 'nowarn', 1),
]

# 오류·경고 줄이 200칸을 넘어 캡처로 싣지 못하는 것 — 종료 코드와 번호만
# (예제, 언어 버전, 기호, 종료 코드, 출력에 있어야 할 것들)
LONGLINE = [
    ('fkshadow', '14.0', None, 0,
     ['warning CS9258', "In language version 14.0, the 'field' keyword"
      " binds to a synthesized backing field", '0 7 7']),
    ('fklocal', '14.0', None, 1, ['error CS9273', 'warning CS9258']),
]

# #if 줄을 켠 캡처 — (예제, 기호, 종료 코드)
DEFINES = [
    ('orbasic', 'NOPRI', 0), ('orambig', 'PRI', 0), ('orneg', 'NOPRI', 0),
    ('orcall', 'DEL1', 1), ('orcall', 'DEL3', 0),
    ('orwhere', 'OVR', 1), ('orwhere', 'PROP', 1), ('orwhere', 'ACC', 1),
    ('orwhere', 'CONV', 1), ('orwhere', 'FIN', 1), ('orwhere', 'CCTOR', 1),
    ('orwhere', 'LAMBDA', 1), ('orwhere', 'LOCAL', 1),
    ('eswhere', 'UPPER', 1), ('mggeneric', 'NOEXT', 1),
    ('mgbreak', 'BAD', 1), ('iitrap', 'DICT', 1),
]

# 장마다 거절을 모은 표 — (예제, 꼬리표, 무엇을 했나)
DIAG6 = [
    ('orbasic', 'v12', 'C# 12.0 에서 [OverloadResolutionPriority(1)]'),
    ('orambig', 'v13', '변환 둘을 가진 값을 params 오버로드 둘에'),
    ('orcall', 'del1', 'Action<int> 에 우선순위가 밀어낸 M1(int)'),
    ('orwhere', 'ovr', 'override 메서드에'),
    ('orwhere', 'prop', '인덱서가 아닌 속성에'),
    ('orwhere', 'acc', '인덱서의 get 접근자에'),
    ('orwhere', 'conv', '변환 연산자에'),
    ('orwhere', 'fin', '종료자에'),
    ('orwhere', 'cctor', '정적 생성자에'),
    ('orwhere', 'lambda', '람다에'),
    ('orwhere', 'local', '지역 함수에'),
]
DIAG7 = [
    ('esbasic', 'v12', "C# 12.0 에서 '\\e'"),
    ('esold', 'cs1312.0', 'C# 12.0 에서 #if CS13 을 켜면'),
    ('eswhere', 'upper', "대문자 '\\E'"),
    ('mgnatural', 'v12', 'C# 12.0 — 인스턴스 M(int)·확장 M(string)'),
    ('mgnest', 'v12', 'C# 12.0 — 안쪽·바깥 범위의 확장 메서드'),
    ('mggeneric', 'v12', 'C# 12.0 — 형식 인수 없는 제네릭 M<T>'),
    ('mggeneric', 'noext', 'C# 13.0 — 확장 메서드를 빼면'),
    ('mgcons', 'v12', 'C# 12.0 — 제약을 못 맞추는 M<string>'),
    ('mgbreak', 'v12', 'C# 12.0 — params 가 다른 두 M'),
    ('mgbreak', 'bad', '문서의 Test1 — 순서에 따라 달랐던 추론'),
    ('iibasic', 'v12', 'C# 12.0 에서 [^1] = 0'),
    ('iirange', 'v12', 'C# 12.0 에서 Slice 로 낮추는 [1..3]'),
    ('iitrap', 'dict', 'Dictionary<int, string> 에 [^1]'),
]
DIAG8 = [
    ('fkbasic', '12.0', 'C# 12.0 에서 field'),
    ('fkbasic', '13.0', 'C# 13.0 에서 field'),
    ('fklocal', 'nowarn', 'C# 14.0 — 접근자 안의 지역 변수 field'),
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
        m = (re.search(r'error (CS\d+): (.*)', text)
             or re.search(r'warning (CS\d+): (.*)', text))
        if not m:
            raise RuntimeError('[p14c] %s 에 진단 줄이 없다' % ex)
        msg = m.group(2)
        if len(msg) > 60:      # 낱말 경계에서 자른다
            msg = msg[:60].rsplit(' ', 1)[0] + ' …'
        rows.append((what, EX + ex, m.group(1), msg))
    return rows


def run(ctx):
    ctx = Retry(ctx)
    found = {}
    for d in RUN:
        ctx.cs(EX + d)
    for d in FAIL:
        found[(d, 'v13')] = ctx.cs(EX + d, expect=1)
    for d, code in CRASH:
        ctx.cs(EX + d, expect=code)
    for d in GATED12 + KEYED12:
        found[(d, 'v12')] = ctx.cs(EX + d, v='12.0', expect=1)
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
    for d, v, sym, want, needles in LONGLINE:
        src = os.path.join(csver.BASE, EX + d)
        flags = '-define:' + sym if sym else None
        code, text = csver.execute(src, 'csrun', v=v, flags=flags,
                                   name='p14c-check-%s-%s' % (d, v))
        if code != want or any(x not in text for x in needles):
            raise RuntimeError('[p14c] %s(-langversion:%s %s) 는 종료 %d·%s'
                               ' 이어야 한다\n%s'
                               % (d, v, flags, want, ' / '.join(needles),
                                  text))
    rows = []
    for v in CODES:
        text = ctx.cs(EX + 'w13codes', v=v, expect=1)
        m = re.search(r'error (CS\d+): Feature (.*) is not available in'
                      r' (C# [\d.]+)\.', text)
        if not m:
            raise RuntimeError('[p14c] w13codes C# %s 의 거절이 없다' % v)
        rows.append(('-langversion:' + v, m.group(1), m.group(2),
                     m.group(3)))
    ctx.table('p14c_codes', ['언어 버전', '진단', '기능', '문장의 버전'],
              rows, caption='같은 C# 14 기능(?.=)을 버전마다 컴파일한 첫 오류')
    head = ['무엇을', '예제', '진단', '컴파일러의 문장(앞부분)']
    for name, spec, cap in (
            ('p14c_diag6', DIAG6, '6장의 거절 캡처에서 뽑은 표'),
            ('p14c_diag7', DIAG7, '7장의 거절 캡처에서 뽑은 표'),
            ('p14c_diag8', DIAG8, '8장의 거절·경고 캡처에서 뽑은 표')):
        if spec:
            ctx.table(name, head, diag_rows(spec, found), caption=cap)
