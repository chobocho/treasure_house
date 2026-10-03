# -*- coding: utf-8 -*-
"""12부 앞 조각 — C# 11 개관과 메서드 그룹 캐시, 문자열(원시 문자열 ·
UTF-8 · 구멍 안의 줄바꿈 · 스팬 패턴), 제네릭 특성과 nameof 의 증거.
예제는 ex/12/ 아래의 ov*·mg*·rw*·u8*·nl*·sp*·ga*·nm* 이다(p12b·p12c 는
같은 ex/12 에 다른 이름으로 쓴다).

게이트가 있는 기능은 C# 10.0 으로 내린 거절을 옆에 둔다. 메서드 그룹
캐시와 nameof 범위는 거절이 아니라 '같은 소스, 다른 결과' 라 두 버전을
모두 돌린다. #if 기호를 켠 캡처는 같은 파일의 '틀린 꼴' 이고, 기호 하나에
오류 하나다(오류 둘의 순서가 실행마다 바뀔 수 있어서)."""
import os
import re
import subprocess

import csver   # run_all.py 가 tools/ 를 sys.path 에 넣어 둔다

EX = 'ex/12/'

# 그대로 돌아가는 예제 — csproj 의 LangVersion(11.0)으로
RUN = [
    # 1장 — 개관 · 메서드 그룹 캐시 · 경고 웨이브 7
    'ovgates', 'ovruntime', 'ovwave7', 'mgcache', 'mgscope', 'mgcount',
    # 2장 — 원시 문자열
    'rwbasic', 'rwdedent', 'rwends', 'rwquotes', 'rwnewline', 'rwregex',
    'rwconst', 'rwinterp', 'rwformat', 'rwmixed', 'rwjson', 'rwu8',
    # 2장 — UTF-8 · 구멍 안의 줄바꿈 · 스팬 패턴
    'u8basic', 'u8type', 'u8data', 'u8surr', 'u8overload', 'u8async',
    'u8static', 'u8pattern', 'u8json',
    'nlswitch', 'nlquery', 'nlverbatim',
    'spbasic', 'sprules', 'spsubsume', 'spparse',
    # 3장 — 제네릭 특성과 nameof
    'gabasic', 'gaconstraint', 'gahistory', 'gareflect', 'garules',
    'gamulti', 'gactor',
    'nmscope', 'nmold', 'nmshadow', 'nmnull', 'nmcaller',
]

# 고의로 깨진 예제(EXPECT_FAIL) — 컴파일러의 거절이 증거다
FAIL = []

# C# 10.0 으로 내리면 거절되는 것 — 언어 버전 짝 (가)
GATED10 = ['ovgates', 'rwbasic', 'u8basic', 'nlswitch', 'nlquery',
           'spbasic', 'gabasic', 'gahistory']

# 같은 소스를 C# 10.0 으로도 돌린다 — 거절이 아니라 결과가 다르다 (나)
SAME10 = ['mgcache', 'mgscope', 'mgcount', 'nmscope', 'nmshadow',
          'nmcaller']

# 다른 버전으로 — (예제, 언어 버전, 종료 코드)
OTHER = [('nlverbatim', '10.0', 0), ('nlverbatim', '6', 0),
         ('nmold', '6', 0), ('nmold', '5', 1),
         ('gahistory', '2', 1), ('gahistory', '8.0', 1)]

# #if 줄을 켠 캡처 — (예제, 기호, 언어 버전 또는 None, 종료 코드)
DEFINES = [
    ('ovwave7', 'REQ', None, 1), ('ovwave7', 'REQ', '10.0', 0),
    ('rwquotes', 'SAME', None, 1),
    ('rwinterp', 'FOUR', None, 1), ('rwinterp', 'ONE', None, 1),
    ('rwinterp', 'CLOSE', None, 1), ('rwinterp', 'START', None, 1),
    ('u8surr', 'LONE', None, 1), ('u8surr', 'TWOHIGH', None, 1),
    ('u8overload', 'CAST', None, 1),
    ('u8async', 'LOCAL', None, 1), ('u8async', 'LOCAL', '12.0', 1),
    ('u8async', 'LOCAL', '13.0', 0), ('u8async', 'CROSS', '13.0', 1),
    ('nlquery', 'TEXT', None, 1),
    ('sprules', 'NULL', None, 1), ('sprules', 'STRNULL', None, 1),
    ('sprules', 'GENERIC', None, 1), ('sprules', 'TYPED', None, 1),
    ('gamulti', 'TWO', None, 1), ('gactor', 'DEC', None, 1),
    ('rwu8', 'INTERP', None, 1),
    ('u8pattern', 'IS', None, 1), ('u8pattern', 'SWITCH', None, 1),
    ('nmnull', 'NULLARG', None, 0), ('nmnull', 'STALE', None, 0),
]

# 제네릭 특성의 형식 인수로 못 오는 것 — (기호, 무엇)
GAERR = [
    ('OPEN', '둘러싼 형식의 형식 매개변수 T2'),
    ('NESTED', 'T2 를 품은 생성 형식 List<T2>'),
    ('DYN', 'dynamic'),
    ('NULLABLE', 'nullable 참조 형식 string?'),
    ('TUPLE', '이름 붙은 튜플 (int X, int Y)'),
]

# 한 줄이 200칸을 넘어 캡처로 못 싣는 거절 — (예제, 기호, 오류 번호).
# 실험이 종료 코드와 번호만 확인하고 슬라이드는 그렇다고 밝힌다
LONGLINE = [('gaconstraint', 'BAD', 'CS0311')]

# u8 리터럴을 둘 수 없는 자리 — (기호, 자리). 첫 오류 번호를 표로 싣는다
U8ERR = [
    ('STR', 'string 변수'),
    ('ARR', 'byte[] 변수'),
    ('SPAN', 'Span<byte> 변수'),
    ('BOX', 'object 변수(박싱)'),
    ('CONST', 'const 지역 상수'),
    ('DEFAULT', '선택적 매개변수의 기본값'),
    ('NOSUFFIX', '접미사 없는 "ok" → ReadOnlySpan<byte>'),
]

# 원시 문자열의 오류 규칙 — (기호, 규칙). 캡처에서 첫 오류 번호와 오류 수를
# 뽑아 표로 싣는다. 규칙의 말은 제안서의 문장을 줄인 것이다
RAWERR = [
    ('OPEN', '여러 줄 꼴인데 여는 따옴표 줄에 내용이 있다'),
    ('CLOSE', '닫는 따옴표가 내용 줄 끝에 붙었다'),
    ('EMPTY', '여는 줄과 닫는 줄 사이에 내용 줄이 없다'),
    ('SIX', '따옴표 여섯 개 — 빈 문자열이 아니라 여섯 따옴표로 여는 리터럴'),
    ('QUOTES', '내용에 구분자보다 긴 따옴표 연속이 있다'),
    ('UNDER', '내용 줄이 닫는 줄보다 덜 들여 썼다'),
    ('TAB', '들여쓰기 공백의 종류(탭 · 스페이스)가 닫는 줄과 다르다'),
]

# 경고 수준을 올린 캡처 — (예제, 언어 버전 또는 None)
WAVE = [('ovwave7', None), ('ovwave7', '10.0')]


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


def run(ctx):
    ctx = Retry(ctx)
    for d in RUN:
        ctx.cs(EX + d)
    for d in FAIL:
        ctx.cs(EX + d, expect=1)
    for d in GATED10:
        ctx.cs(EX + d, v='10.0', expect=1)
    for d in SAME10:
        ctx.cs(EX + d, v='10.0')
    for d, v, code in OTHER:
        ctx.cs(EX + d, v=v, expect=code)
    for d, sym, v, code in DEFINES:
        ctx.cs(EX + d, v=v, flags='-define:' + sym, tag=sym.lower(),
               expect=code)
    for d, v in WAVE:
        ctx.cs(EX + d, v=v, flags='-warn:7', tag='w7')
    errtable(ctx, 'p12_rawerr', 'rwerr', RAWERR, '규칙')
    errtable(ctx, 'p12_u8err', 'u8type', U8ERR, '자리')
    errtable(ctx, 'p12_gaerr', 'garules', GAERR, '형식 인수')
    for d, sym, err in LONGLINE:
        code, text = csver.execute(os.path.join(csver.BASE, EX + d),
                                   'csrun', flags='-define:' + sym,
                                   name='p12-check-' + d)
        if code != 1 or 'error ' + err not in text:
            raise RuntimeError('[p12] %s(-define:%s) 는 %s 이어야 한다\n%s'
                               % (d, sym, err, text))


def errtable(ctx, name, ex, cases, what):
    """기호마다 컴파일한 캡처에서 첫 오류 번호와 오류 수를 뽑아 표로."""
    rows = []
    for sym, rule in cases:
        text = ctx.cs(EX + ex, flags='-define:' + sym, tag=sym.lower(),
                      expect=1)
        errs = re.findall(r'error (CS\d+)', text)
        rows.append([sym, rule, errs[0], str(len(errs))])
    ctx.table(name, ['기호', what, '첫 오류', '오류 수'], rows,
              caption='ex/12/%s 를 -define:기호 로 컴파일한 캡처에서 '
                      '뽑은 표' % ex)

